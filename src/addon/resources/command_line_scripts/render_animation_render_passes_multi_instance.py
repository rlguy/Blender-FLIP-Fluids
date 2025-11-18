# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy, sys, os, pathlib, threading, time, subprocess, queue

argv = sys.argv
argv = argv[argv.index("--") + 1:]
num_render_instances_option = int(argv[0])
use_overwrite_option = int(argv[1])

_NUM_RENDER_INSTANCES = num_render_instances_option
_USE_OVERWRITE = bool(use_overwrite_option)
_RENDER_THREADS = []


def _render_thread(command_info):
    blend_filepath = command_info['blend_filepath']
    frameno = command_info['frameno']
    command = [bpy.app.binary_path, "-b", blend_filepath, "-f", str(frameno)] 
    subprocess.call(command, shell=False)


def render_loop(command_list):
    global _NUM_RENDER_INSTANCES
    global _RENDER_THREADS
    global _IS_SIMULATION_FINISHED

    _RENDER_THREADS = [None] * _NUM_RENDER_INSTANCES

    render_command_queue = queue.Queue()
    for command_text in command_list:
        render_command_queue.put(command_text)

    updates_per_second = 60
    while True:
        if not render_command_queue.empty():
            available_thread_id = -1
            is_thread_available = False
            for i in range(len(_RENDER_THREADS)):
                if _RENDER_THREADS[i] is None or not _RENDER_THREADS[i].is_alive():
                    available_thread_id = i
                    is_thread_available = True
                    break

            if is_thread_available:
                command_info = render_command_queue.get()
                _RENDER_THREADS[available_thread_id] = threading.Thread(target=_render_thread, args=(command_info,))
                _RENDER_THREADS[available_thread_id].start()

        if render_command_queue.empty():
            is_threads_running = False
            for thread in _RENDER_THREADS:
                if thread is not None and thread.is_alive():
                    is_threads_running = True
                    break
            if not is_threads_running:
                return

        time.sleep(1.0/updates_per_second)


def get_render_output_info():
    full_path = bpy.path.abspath(bpy.context.scene.render.filepath)
    directory_path = full_path

    file_prefix = os.path.basename(directory_path)
    if file_prefix:
       directory_path = os.path.dirname(directory_path)

    file_format_to_suffix = {
        "BMP"                 : ".bmp",
        "IRIS"                : ".rgb",
        "PNG"                 : ".png",
        "JPEG"                : ".jpg",
        "JPEG2000"            : ".jp2",
        "TARGA"               : ".tga",
        "TARGA_RAW"           : ".tga",
        "CINEON"              : ".cin",
        "DPX"                 : ".dpx",
        "OPEN_EXR_MULTILAYER" : ".exr",
        "OPEN_EXR"            : ".exr",
        "HDR"                 : ".hdr",
        "TIFF"                : ".tif",
        "WEBP"                : ".webp",
        "AVI_JPEG"            : ".avi",
        "AVI_RAW"             : ".avi",
        "FFMPEG"              : ".mp4"
    }

    file_format = bpy.context.scene.render.image_settings.file_format
    file_suffix = file_format_to_suffix[file_format]

    return directory_path, file_prefix, file_suffix


def get_render_passes_info():
    # Pass-Suffix-Liste mit den zugehoerigen Listen
    hprops = bpy.context.scene.flip_fluid_helper
    pass_suffixes = [
        ("BG_elements_only", hprops.render_passes_elements_only, hprops.render_passes_bg_elementslist),
        ("REF_elements_only", hprops.render_passes_elements_only, hprops.render_passes_ref_elementslist),
        ("objects_only", hprops.render_passes_objects_only, None),
        ("fluidparticles_only", hprops.render_passes_fluidparticles_only, None),
        ("fluid_only", hprops.render_passes_fluid_only, None),
        ("fluid_shadows_only", hprops.render_passes_fluid_shadows_only, None),
        ("reflr_only", hprops.render_passes_reflr_only, None),
        ("bubblesanddust_only", hprops.render_passes_bubblesanddust_only, None),
        ("foamandspray_only", hprops.render_passes_foamandspray_only, None),
        ("FG_elements_only", hprops.render_passes_elements_only, hprops.render_passes_fg_elementslist),
    ]

    # Entferne leere Listen-Suffixe
    filtered_suffixes = [
        suffix for suffix, is_active, elements_list in pass_suffixes
        if is_active and (elements_list is None or len(elements_list) > 0)
    ]

    blend_file_directory = os.path.dirname(bpy.data.filepath)
    base_file_name = pathlib.Path(bpy.path.basename(bpy.data.filepath)).stem

    info_dict_items = []
    for idx, suffix in enumerate(filtered_suffixes):
        pass_index = idx + 1

        render_pass_blend_filename = f"{pass_index}_{base_file_name}_{suffix}.blend"
        blend_filepath = os.path.join(blend_file_directory, render_pass_blend_filename)

        original_output_folder = bpy.path.abspath(bpy.context.scene.render.filepath)
        output_folder = os.path.dirname(original_output_folder)
        render_output_subfolder = f"{pass_index}_{suffix}"
        render_output_directory = os.path.join(output_folder, render_output_subfolder)
        output_filename = os.path.basename(original_output_folder)
        pass_file_prefix = f"{pass_index}_{output_filename}_{suffix}"

        rendered_files = os.listdir(render_output_directory)

        info = {}
        info['pass_index'] = pass_index
        info['blend_filepath'] = blend_filepath
        info['pass_file_prefix'] = pass_file_prefix
        info['rendered_files'] = rendered_files
        info_dict_items.append(info)

    return info_dict_items


hprops = bpy.context.scene.flip_fluid_helper
render_passes_info = get_render_passes_info()
_, _, image_file_extension = get_render_output_info()
skip_rendered_frames = not _USE_OVERWRITE
frame_start = bpy.context.scene.frame_start
frame_end = bpy.context.scene.frame_end
frame_step = bpy.context.scene.frame_step
skipped_frame_filepaths = []
rendered_frame_filepaths = []

render_command_queue = []
for frameno in range(frame_start, frame_end + 1, frame_step):
    for pass_info in render_passes_info:
        blend_filepath = pass_info['blend_filepath']

        if skip_rendered_frames:                    
            render_file_prefix = pass_info['pass_file_prefix']
            rendered_files = pass_info['rendered_files']
            rendered_filename = render_file_prefix + str(frameno).zfill(4) + image_file_extension
            if not rendered_filename in rendered_files:
                command_info = {}
                command_info['blend_filepath'] = blend_filepath
                command_info['frameno'] = frameno
                render_command_queue.append(command_info)
        else:
            command_info = {}
            command_info['blend_filepath'] = blend_filepath
            command_info['frameno'] = frameno
            render_command_queue.append(command_info)

render_loop(render_command_queue)

print("\n***Multi Instance Render Complete***\n")
