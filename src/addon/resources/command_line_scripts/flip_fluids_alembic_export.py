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

import bpy, ctypes, os, json, platform, traceback


def get_flip_fluids_alembic_exporter_lib_filepath():
    executable_name = ""

    system = platform.system()
    if system == "Windows":
        lib_name = "libffalembicengine.dll"
    elif system == "Darwin":
        lib_name = "libffalembicengine.dylib"
    elif system == "Linux":
        lib_name = "libffalembicengine.so"

    lib_path = os.path.dirname(os.path.realpath(__file__))
    lib_path = os.path.dirname(os.path.dirname(lib_path))
    lib_path = os.path.join(lib_path, "ffengine", "lib", lib_name)
    if not os.path.isfile(lib_path):
        return None, "Missing Alembic export engine library  <" + lib_path + ">"
    return lib_path, None


def get_export_frame_range():
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    hprops = bpy.context.scene.flip_fluid_helper
    if hprops.alembic_frame_range_mode == 'FRAME_RANGE_CUSTOM':
        frame_start = hprops.alembic_frame_range_custom.value_min
        frame_end = hprops.alembic_frame_range_custom.value_max
    return frame_start, frame_end


def flip_fluids_alembic_export():
    hprops = bpy.context.scene.flip_fluid_helper
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()

    input_cache_directory = dprops.cache.get_cache_abspath()
    output_alembic_filepath = hprops.alembic_output_filepath
    frame_start, frame_end = get_export_frame_range()

    export_config = {}
    export_config['cache_directory'] = input_cache_directory
    export_config['alembic_filepath'] = output_alembic_filepath
    export_config['frame_start'] = frame_start
    export_config['frame_end'] = frame_end

    json_string = json.dumps(export_config, indent=4)
    b_json_string = json_string.encode('utf-8')

    exporter_library_filepath, error_message = get_flip_fluids_alembic_exporter_lib_filepath()
    if error_message is not None:
        print("\n***ERROR: Unabled to Begin Alembic Export***")
        print("Reason: " + error_message)
        print("Contact the developers if you think that this is an error.")
        return

    exporter_library = None
    exporter_library_error = None
    try:
        exporter_library = ctypes.cdll.LoadLibrary(exporter_library_filepath)
    except Exception as e:
        exporter_library_error = str(e.__class__.__name__) + " - " + str(e)

    if exporter_library is None:
        errmsg = "Unable to load Alembic export engine library: <" + exporter_library_filepath + ">\n"
        if exporter_library_error is not None:
            errmsg += "Reason: " + exporter_library_error

        print("\n***ERROR: Unabled to Begin Alembic Export***")
        print(errmsg)
        print("Contact the developers if you think that this is an error.")
        return

    exporter_library.alembic_io_flip_fluids_cache_to_alembic.argtypes = [ctypes.c_char_p]
    exporter_library.alembic_io_flip_fluids_cache_to_alembic(b_json_string)

    print("Alembic export of cache <" + input_cache_directory + "> has been written to: <" + output_alembic_filepath + ">")


flip_fluids_alembic_export()