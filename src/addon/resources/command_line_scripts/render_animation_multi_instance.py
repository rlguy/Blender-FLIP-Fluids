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

import bpy, sys, os, threading, time, subprocess, queue

argv = sys.argv
argv = argv[argv.index("--") + 1:]
num_render_instances_option = int(argv[0])
use_overwrite_option = int(argv[1])

_NUM_RENDER_INSTANCES = num_render_instances_option
_USE_OVERWRITE = bool(use_overwrite_option)
_RENDER_THREADS = []


def _render_thread(settings, frameno):
    command = [settings["blender_binary_path"], "-b", settings["blend_filepath"], "-f", str(frameno)] 
    subprocess.call(command, shell=False)


def render_loop(settings):
    global _NUM_RENDER_INSTANCES
    global _RENDER_THREADS
    global _IS_SIMULATION_FINISHED

    _RENDER_THREADS = [None] * _NUM_RENDER_INSTANCES

    render_frame_queue = queue.Queue()
    for frameno in settings["frameno_list"]:
        render_frame_queue.put(frameno)

    updates_per_second = 60
    while True:
        if not render_frame_queue.empty():
            available_thread_id = -1
            is_thread_available = False
            for i in range(len(_RENDER_THREADS)):
                if _RENDER_THREADS[i] is None or not _RENDER_THREADS[i].is_alive():
                    available_thread_id = i
                    is_thread_available = True
                    break

            if is_thread_available:
                frameno = render_frame_queue.get()
                _RENDER_THREADS[available_thread_id] = threading.Thread(target=_render_thread, args=(settings, frameno))
                _RENDER_THREADS[available_thread_id].start()

        if render_frame_queue.empty():
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


hprops = bpy.context.scene.flip_fluid_helper
directory_path, file_prefix, file_suffix = get_render_output_info()
frame_start = bpy.context.scene.frame_start
frame_end = bpy.context.scene.frame_end
frame_step = bpy.context.scene.frame_step
skipped_frame_filepaths = []
rendered_frame_filepaths = []

frameno_list = list(range(frame_start, frame_end + 1, frame_step))
if not _USE_OVERWRITE:
    filtered_frameno_list = []
    filename_list = os.listdir(directory_path)
    for frameno in frameno_list:
        frame_filename = file_prefix + str(frameno).zfill(4) + file_suffix
        frame_filepath = os.path.join(directory_path, frame_filename)
        if frame_filename not in filename_list:
            filtered_frameno_list.append(frameno)
            rendered_frame_filepaths.append(frame_filepath)
        else:
            skipped_frame_filepaths.append(frame_filepath)
            print("Frame exists, skipping frame <" + frame_filepath + ">")
    frameno_list = filtered_frameno_list
else:
    for frameno in frameno_list:
        frame_filename = file_prefix + str(frameno).zfill(4) + file_suffix
        frame_filepath = os.path.join(directory_path, frame_filename)
        rendered_frame_filepaths.append(frame_filepath)

settings = {}
settings["blender_binary_path"] = bpy.app.binary_path
settings["blend_filepath"] = bpy.data.filepath
settings["frame_start"] = bpy.context.scene.frame_start
settings["frame_end"] = bpy.context.scene.frame_end
settings["frame_step"] = bpy.context.scene.frame_step
settings["use_overwrite"] = _USE_OVERWRITE
settings["frameno_list"] = frameno_list

render_loop(settings)

print("\n***Multi Instance Render Complete***\n")

print("Blend Files: " + settings["blend_filepath"] + "\n")

print("Skipped Existing Frames: ")
if skipped_frame_filepaths:
    for f in skipped_frame_filepaths:
        print("\t" + f)
else:
    print("\tNo frames skipped")

print()

print("Rendered Frames: ")
if rendered_frame_filepaths:
    for f in rendered_frame_filepaths:
        print("\t" + f)
else:
    print("\tNo frames rendered")
