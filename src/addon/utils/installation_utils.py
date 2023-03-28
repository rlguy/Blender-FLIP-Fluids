# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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

import bpy, os, sys, json

from . import version_compatibility_utils as vcu

IS_INSTALLATION_UTILS_INITIALIZED = False
IS_INSTALLATION_COMPLETE = False
IS_STABLE_BUILD = True

IS_MIXBOX_SUPPORTED = False
IS_MIXBOX_INSTALLATION_COMPLETE = False
MIXBOX_BOOST_FACTOR = 1.2

IS_PRESET_LIBRARY_INSTALLATION_COMPLETE = False
PRESET_LIBRARY_INSTALLATIONS = []

IS_ADDON_ACTIVE = False


def is_installation_complete():
    global IS_INSTALLATION_UTILS_INITIALIZED
    global IS_INSTALLATION_COMPLETE

    if IS_INSTALLATION_UTILS_INITIALIZED:
        return IS_INSTALLATION_COMPLETE

    script_dir = os.path.dirname(os.path.realpath(__file__))
    addon_dir = os.path.dirname(script_dir)
    install_file = os.path.join(addon_dir, "resources", "installation_data", "installation_complete")

    if os.path.exists(install_file):
        IS_INSTALLATION_COMPLETE = True
    else:
        IS_INSTALLATION_COMPLETE = False

    IS_INSTALLATION_UTILS_INITIALIZED = True

    return IS_INSTALLATION_COMPLETE


def complete_installation():
    global IS_INSTALLATION_UTILS_INITIALIZED
    global IS_INSTALLATION_COMPLETE

    script_dir = os.path.dirname(os.path.realpath(__file__))
    addon_dir = os.path.dirname(script_dir)
    install_file = os.path.join(addon_dir, "resources", "installation_data", "installation_complete")

    if not os.path.exists(install_file):
        with open(install_file, 'w') as f:
            f.write("1")

    IS_INSTALLATION_COMPLETE = True
    IS_INSTALLATION_UTILS_INITIALIZED = True


def get_module_name():
    from ..properties import preferences_properties
    prefs = preferences_properties.get_addon_preferences()

    module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    module_name = os.path.basename(os.path.normpath(module_dir))
    if prefs.enable_addon_directory_renaming:
        return module_name
    else:
        hardcoded_name = "flip_fluids_addon"
        if module_name != hardcoded_name:
            errmsg = "Installation Error Detected"
            errdesc = "The FLIP Fluids addon directory located at <" + module_dir + "> must be named 'flip_fluids_addon'. Please rename this directory, restart Blender, and re-enable the addon."
            bpy.ops.flip_fluid_operators.display_error(
                'INVOKE_DEFAULT',
                error_message=errmsg,
                error_description=errdesc,
                popup_width=600
                )
        return hardcoded_name


def get_enabled_flip_fluids_addon_installations():
    import addon_utils
    bl_prefs = vcu.get_blender_preferences()

    name_prefix = "FLIP Fluids"
    description_prefix = "A FLIP Fluid Simulation Tool for Blender"
    flip_fluids_installations = []
    for mod_name in bl_prefs.addons.keys():
        try:
            module = sys.modules[mod_name]
            name = module.bl_info.get('name', "")
            description = module.bl_info.get('description', "")
            if name.startswith(name_prefix) and description.startswith(description_prefix):
                d = {}
                d['module_name'] = mod_name
                d['addon_name'] = name
                flip_fluids_installations.append(d)
        except:
            pass

    return flip_fluids_installations


def is_experimental_build():
    global IS_STABLE_BUILD
    return not IS_STABLE_BUILD


def is_addon_active():
    global IS_ADDON_ACTIVE
    return IS_ADDON_ACTIVE


def tag_addon_active():
    global IS_ADDON_ACTIVE
    IS_ADDON_ACTIVE = True


def tag_addon_inactive():
    global IS_ADDON_ACTIVE
    IS_ADDON_ACTIVE = False


def update_mixbox_installation_status():
    global IS_MIXBOX_INSTALLATION_COMPLETE
    if not is_mixbox_supported():
        IS_MIXBOX_INSTALLATION_COMPLETE = False
        return

    lut_filename = "mixbox_lut_data.bin"
    addon_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    mixbox_lut_filepath = os.path.join(addon_directory, "third_party", "mixbox", lut_filename)
    IS_MIXBOX_INSTALLATION_COMPLETE = os.path.isfile(mixbox_lut_filepath)
    return IS_MIXBOX_INSTALLATION_COMPLETE


def is_mixbox_supported():
    global IS_MIXBOX_SUPPORTED
    return IS_MIXBOX_SUPPORTED


def is_mixbox_installation_complete():
    global IS_MIXBOX_INSTALLATION_COMPLETE
    return IS_MIXBOX_INSTALLATION_COMPLETE


def get_mixbox_boost_factor():
    global MIXBOX_BOOST_FACTOR
    return MIXBOX_BOOST_FACTOR


def update_preset_library_installation_status():
    global IS_PRESET_LIBRARY_INSTALLATION_COMPLETE
    global PRESET_LIBRARY_INSTALLATIONS

    IS_PRESET_LIBRARY_INSTALLATION_COMPLETE = False
    PRESET_LIBRARY_INSTALLATIONS = []

    if not vcu.is_blender_33():
        # Asset library is only available in Blender 3.3 or later
        return

    bl_preferences = bpy.context.preferences
    bl_filepaths = bl_preferences.filepaths
    for lib_entry in bl_filepaths.asset_libraries:
        entry_name = lib_entry.name
        entry_path = lib_entry.path
        expected_metadata_filepath = os.path.join(entry_path, ".metadata", "version.json")
        if not os.path.isfile(expected_metadata_filepath):
            continue

        try:
            with open(expected_metadata_filepath, 'r') as version_file:
                version_data = json.loads(version_file.read())
                d = {}
                d["name"] = entry_name
                d["path"] = entry_path
                d["install_path"] = os.path.dirname(entry_path)
                d["metadata"] = version_data
                PRESET_LIBRARY_INSTALLATIONS.append(d)
                IS_PRESET_LIBRARY_INSTALLATION_COMPLETE = True
        except Exception as e:
            print("FLIP Fluids: Error verifying preset library install. <" + lib_entry.name + " : " + entry_path + ">" + "<" + str(e) + ">")

    return IS_PRESET_LIBRARY_INSTALLATION_COMPLETE


def is_preset_library_installation_complete():
    global IS_PRESET_LIBRARY_INSTALLATION_COMPLETE
    return IS_PRESET_LIBRARY_INSTALLATION_COMPLETE


def get_preset_library_installations():
    global PRESET_LIBRARY_INSTALLATIONS
    return PRESET_LIBRARY_INSTALLATIONS


def is_turbo_tools_addon_enabled():
    # Used for command line tools to launch Turbo Tools Render processes
    #     https://blendermarket.com/products/turbo-tools-v3---turbo-render-turbo-comp-temporal-stabilizer
    return "Turbo Tools" in vcu.get_blender_preferences().addons


def __load_post_update_is_addon_active():
    tag_addon_inactive()
    if bpy.context.scene.flip_fluid.is_domain_object_set():
        tag_addon_active()
        return
    if bpy.context.scene.flip_fluid.get_simulation_objects():
        tag_addon_active()
        return


def load_post():
    complete_installation()
    update_mixbox_installation_status()
    __load_post_update_is_addon_active()


def scene_update_post(scene):
    if is_addon_active():
        return

    # FLIP Fluid objects appended from another scene will not tag the addon as active
    # This workaround is to quickly check whether the active object is a FLIP Fluid object
    # and in this case, tag the addon as active
    try:
        active_object = vcu.get_active_object()
    except AttributeError as e:
        # Context may not have an active object available, such as when exporting to Alembic.
        # In this case, ignore and return.
        return

    if active_object is not None and active_object.flip_fluid.is_active:
        tag_addon_active()
