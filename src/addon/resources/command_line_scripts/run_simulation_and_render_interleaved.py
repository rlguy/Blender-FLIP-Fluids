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

import bpy, sys, os, threading, time, subprocess, pathlib
from collections import namedtuple

argv = sys.argv
argv = argv[argv.index("--") + 1:]
num_render_instances_option = int(argv[0])
use_overwrite_option = int(argv[1])

_NUM_RENDER_INSTANCES = num_render_instances_option
_USE_OVERWRITE = bool(use_overwrite_option)
_RENDER_THREADS = []
_IS_SIMULATION_FINISHED = False

RenderCommandInfo = namedtuple('RenderCommandInfo', ['blendfile', 'frame'])


def get_max_bakefile_frame(bakefiles_directory):
        bakefiles = os.listdir(bakefiles_directory)
        max_frameno = -1
        for f in bakefiles:
            base = f.split(".")[0]
            if not base.startswith("finished"):
                # a file named in the form finished######.txt is created
                # to signal that all cache files for the frame have been generated.
                continue

            try:
                frameno = int(base[-6:])
                max_frameno = max(frameno, max_frameno)
            except:
                # In the case that there is a bakefile without a number
                pass
        return max_frameno


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


def get_render_command_list_single_blend():
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    frame_step = bpy.context.scene.frame_step
    skip_rendered_frames = not _USE_OVERWRITE

    render_command_list = []
    for frameno in range(frame_start, frame_end + 1, frame_step):
        image_filepath = bpy.context.scene.render.frame_path(frame=frameno)
        if skip_rendered_frames and os.path.isfile(image_filepath):
            continue

        command = RenderCommandInfo(blendfile=bpy.data.filepath, frame=frameno)
        render_command_list.append(command)

    return render_command_list


def get_render_command_list_render_passes():
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    frame_step = bpy.context.scene.frame_step
    skip_rendered_frames = not _USE_OVERWRITE
    render_passes_info = get_render_passes_info()
    _, _, image_file_extension = get_render_output_info()

    render_command_list = []
    for frameno in range(frame_start, frame_end + 1, frame_step):
        for pass_info in render_passes_info:
            blend_filepath = pass_info['blend_filepath']

            if skip_rendered_frames:                    
                render_file_prefix = pass_info['pass_file_prefix']
                rendered_files = pass_info['rendered_files']
                rendered_filename = render_file_prefix + str(frameno).zfill(4) + image_file_extension
                if not rendered_filename in rendered_files:
                    command = RenderCommandInfo(blendfile=blend_filepath, frame=frameno)
                    render_command_list.append(command)
            else:
                command = RenderCommandInfo(blendfile=blend_filepath, frame=frameno)
                render_command_list.append(command)

    return render_command_list


def _render_thread(command):
    subprocess_command = [bpy.app.binary_path, "-b", command.blendfile, "-f", str(command.frame)] 
    subprocess.call(subprocess_command, shell=False)  


def _render_sequence_thread(command, frame_start, frame_end):
    subprocess_command = [bpy.app.binary_path, "-b", command.blendfile, "-s", str(frame_start), "-e", str(frame_end), "-a"] 
    subprocess.call(subprocess_command, shell=False)  


def render_loop(render_command_list):
    global _NUM_RENDER_INSTANCES
    global _RENDER_THREADS
    global _IS_SIMULATION_FINISHED

    _RENDER_THREADS = [None] * _NUM_RENDER_INSTANCES

    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    frame_step = bpy.context.scene.frame_step

    hprops = bpy.context.scene.flip_fluid_helper
    render_single_blend_file = not hprops.render_passes
    render_single_threaded = _NUM_RENDER_INSTANCES == 1
    is_render_sequence_optimization_available = render_single_blend_file and render_single_threaded and frame_step == 1

    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    cache_directory = dprops.cache.get_cache_abspath()
    bakefiles_directory = os.path.join(cache_directory, "bakefiles")

    baked_frames = []
    render_command_queue = []

    updates_per_second = 60
    while True:
        if not os.path.isdir(bakefiles_directory):
            continue

        # Update render command queue
        max_frameno = get_max_bakefile_frame(bakefiles_directory)
        if max_frameno < 0:
            continue

        if max_frameno not in baked_frames:
            if baked_frames:
                next_frame = baked_frames[-1] + 1
            else:
                next_frame = frame_start

            for i in range(next_frame, max_frameno + 1):
                baked_frames.append(i)

        new_commands = [command for command in render_command_list if command.frame <= max_frameno]
        render_command_queue += new_commands
        remaining_commands = [command for command in render_command_list if command.frame > max_frameno]
        render_command_list = remaining_commands

        # Launch render worker thread
        if render_command_queue:
            available_thread_id = -1
            is_thread_available = False
            for i in range(len(_RENDER_THREADS)):
                if _RENDER_THREADS[i] is None or not _RENDER_THREADS[i].is_alive():
                    available_thread_id = i
                    is_thread_available = True
                    break

            if is_thread_available:
                if is_render_sequence_optimization_available:
                    # Render a continuous frame sequence instead of shutting down Blender between frames
                    sequence_start = render_command_queue[0].frame
                    sequence_end = sequence_start
                    for i in range(1, len(render_command_queue)):
                        next_frame = render_command_queue[i].frame
                        if next_frame == sequence_end + 1:
                            sequence_end = next_frame
                        else:
                            break

                    next_command = render_command_queue.pop(0)
                    render_command_queue = [command for command in render_command_queue if command.frame > sequence_end]

                    _RENDER_THREADS[available_thread_id] = threading.Thread(target=_render_sequence_thread, args=(next_command, sequence_start, sequence_end,))
                    _RENDER_THREADS[available_thread_id].start()
                else:
                    next_command = render_command_queue.pop(0)
                    _RENDER_THREADS[available_thread_id] = threading.Thread(target=_render_thread, args=(next_command,))
                    _RENDER_THREADS[available_thread_id].start()

        # Check if render finished
        if _IS_SIMULATION_FINISHED:
            last_frameno = baked_frames[-1]
            if last_frameno == frame_end:
                is_threads_running = False
                for thread in _RENDER_THREADS:
                    if thread is not None and thread.is_alive():
                        is_threads_running = True
                        break
                if not is_threads_running:
                    return

        time.sleep(1.0/updates_per_second)


hprops = bpy.context.scene.flip_fluid_helper
if hprops.render_passes:
    render_command_list = get_render_command_list_render_passes()
else:
    render_command_list = get_render_command_list_single_blend()

render_loop_thread = threading.Thread(target=render_loop, args=(render_command_list,))
render_loop_thread.start()

bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()
_IS_SIMULATION_FINISHED = True

render_loop_thread.join()
