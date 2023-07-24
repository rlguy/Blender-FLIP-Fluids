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

import bpy, os, shutil, json, zipfile, urllib.request, sys, textwrap, platform, random, traceback
from bpy_extras.io_utils import ImportHelper

from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        CollectionProperty,
        )

from ..presets import preset_library
from ..pyfluid import gpu_utils
from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils
from ..utils import audio_utils
from ..utils import api_workaround_utils as api_utils
from ..filesystem import filesystem_protection_layer as fpl


def _get_addon_directory():
    this_filepath = os.path.dirname(os.path.realpath(__file__))
    addon_directory = os.path.dirname(this_filepath)
    return addon_directory


class FLIPFluidPreferencesExportUserData(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preferences_export_user_data"
    bl_label = "Export User Settings"
    bl_description = ("Creates a backup of your user settings and presets as a" +
        " .zip file. All user data will be lost after uninstalling the addon.")

    filepath = StringProperty(subtype="FILE_PATH")
    exec(vcu.convert_attribute_to_28("filepath"))


    @classmethod
    def poll(cls, context):
        return True


    def get_user_settings_info(self):
        user_info = [
            {
                "id":         "system_presets", 
                "archive":    "system_presets.zip", 
                "extract_to": "presets/preset_library/sys"
            },
            {
                "id":         "user_presets", 
                "archive":    "user_presets.zip", 
                "extract_to": "presets/preset_library/usr"
            },
        ]

        addon_path = _get_addon_directory()
        for i in range(len(user_info) - 1, -1, -1):
            d = user_info[i]
            item_path = os.path.join(addon_path, d["extract_to"])
            item_path = os.path.normpath(item_path)
            if not os.path.exists(item_path):
                user_info.pop(i)

        return user_info


    def get_temp_directory(self):
        temp_dir = os.path.join(os.path.dirname(self.filepath), "temp_export_user_settings")
        if os.path.exists(temp_dir):
            for i in range(0, 1000000):
                new_path = temp_dir + str(i)
                if not os.path.exists(new_path):
                    temp_dir = new_path
                    break
        return temp_dir


    def create_archive(self):
        pass

        # Deprecated function - do not uncomment until updating to use filesystem_protection_layer
        """
        temp_dir = self.get_temp_directory()
        if not os.path.exists(temp_dir):
            try:
                os.makedirs(temp_dir)
            except Exception as e:
                return str(e)

        user_info = self.get_user_settings_info()

        user_info_str = json.dumps(user_info, sort_keys=True, indent=4)
        user_info_filepath = os.path.join(temp_dir, "user_settings.info")
        with open(user_info_filepath, 'w', encoding='utf-8') as f:
            f.write(user_info_str)

        addon_path = _get_addon_directory()
        for d in user_info:
            archive_name = d["archive"][:-4]
            archive_path = os.path.join(temp_dir, archive_name)
            item_path = os.path.join(addon_path, d["extract_to"])
            item_path = os.path.normpath(item_path)
            try:
                shutil.make_archive(archive_path, 'zip', item_path)
            except Exception as e:
                return str(e)

        try:
            archive_path = self.filepath[:-4]
            shutil.make_archive(archive_path, 'zip', temp_dir)
        except Exception as e:
            return str(e)

        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            return str(e)
        """


    def execute(self, context):
        if os.path.isdir(self.filepath):
            errmsg = "Error: file path is already a directory"
            desc = "Path: <" + self.filepath + ">"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=desc,
                    popup_width=400
                    )
            return {'CANCELLED'}

        if not self.filepath.endswith(".zip"):
            self.filepath += ".zip"

        error = self.create_archive()
        if error:
            errmsg = "Error: unable to export user settings"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        self.report({'INFO'}, "Successfully exported user settings to: <" + self.filepath + ">")
        return {'FINISHED'}


    def invoke(self, context, event):
        default_directory = vcu.get_blender_preferences_temporary_directory()
        if bpy.data.is_saved:
            default_directory = os.path.dirname(bpy.data.filepath)
        self.filepath = os.path.join(default_directory, "flip_fluid_user_settings.zip")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class FLIPFluidPreferencesImportUserData(bpy.types.Operator, ImportHelper):
    bl_idname = "flip_fluid_operators.preferences_import_user_data"
    bl_label = "Import User Settings"
    bl_description = "Load user settings and presets from a previous installation"

    filename_ext = "*.zip"
    filter_glob = StringProperty(
            default="*.zip",
            options={'HIDDEN'},
            maxlen=255,
            )
    exec(vcu.convert_attribute_to_28("filter_glob"))



    def get_temp_directory(self):
        temp_dir = os.path.join(os.path.dirname(self.filepath), "temp_import_user_settings")
        if os.path.exists(temp_dir):
            for i in range(0, 1000000):
                new_path = temp_dir + str(i)
                if not os.path.exists(new_path):
                    temp_dir = new_path
                    break
        return temp_dir


    def import_user_data(self):
        pass

        # Deprecated function - do not uncomment until updating to use filesystem_protection_layer
        """
        temp_dir = self.get_temp_directory()
        try:
            zfile = zipfile.ZipFile(self.filepath, "r")
            zfile.extractall(temp_dir)
            zfile.close()
        except Exception as e:
            return str(e)

        info_filepath = os.path.join(temp_dir, "user_settings.info")
        if not os.path.exists(info_filepath):
            return "Unable to find user settings. This is not a valid user settings file."

        with open(info_filepath, 'rb') as user_info_file:
            user_info = json.loads(user_info_file.read().decode("utf-8"))

        addon_dir = _get_addon_directory()
        for p in user_info:
            archive_filepath = os.path.join(temp_dir, p['archive'])
            archive_dest = os.path.normpath(os.path.join(addon_dir, p['extract_to']))
            try:
                zfile = zipfile.ZipFile(archive_filepath, "r")
                zfile.extractall(archive_dest)
                zfile.close()
            except Exception as e:
                return str(e)

        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            return str(e)
        """


    def execute(self, context):
        error = self.import_user_data()
        if error:
            errmsg = "Error: unable to import user settings"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        preset_library.initialize()
        self.report({'INFO'}, "Successfully imported user settings: <" + self.filepath + ">")
        return {'FINISHED'}


class FLIPFluidInstallMixboxPlugin(bpy.types.Operator, ImportHelper):
    bl_idname = "flip_fluid_operators.install_mixbox_plugin"
    bl_label = "Install Mixbox"
    bl_description = ("Select and install the Mixbox plugin file. The Mixbox plugin adds physically" +
                      " accurate pigment mixing technology for simulating mixed and blended" +
                      " color simulations. The Mixbox plugin file can be found in the FLIP" +
                      " Fluids addon downloads")

    filename_ext = "*.plugin"
    filter_glob = StringProperty(
            default="*.plugin",
            options={'HIDDEN'},
            maxlen=255,
            )
    exec(vcu.convert_attribute_to_28("filter_glob"))


    @classmethod
    def poll(cls, context):
        return not installation_utils.is_mixbox_installation_complete()


    def tag_redraw(self, context):
        try:
            # Depending on window, area may be None
            context.area.tag_redraw()
        except:
            pass


    def clear_error_message(self, context):
        preferences = vcu.get_addon_preferences()
        preferences.is_mixbox_installation_error = False
        preferences.mixbox_installation_error_message = ""
        self.tag_redraw(context)


    def report_error_message(self, context, error_message, error_type={'ERROR_INVALID_INPUT'}):
        self.report(error_type, error_message)
        print(error_message)
        preferences = vcu.get_addon_preferences()
        preferences.is_mixbox_installation_error = True
        preferences.mixbox_installation_error_message = error_message
        self.tag_redraw(context)


    def execute(self, context):
        installation_utils.update_mixbox_installation_status()
        self.clear_error_message(context)

        if not os.path.exists(self.filepath):
            self.report_error_message(context, "Error: File does not exist. Select the Mixbox.plugin file.")
            return {'CANCELLED'}

        if not os.path.isfile(self.filepath):
            self.report_error_message(context, "Error: No file selected. Select the Mixbox.plugin file.")
            return {'CANCELLED'}

        try:
            expected_lut_filename = "mixbox_lut_data.bin"
            expected_lut_filesize = 4070220
            with zipfile.ZipFile(self.filepath, 'r') as zip:
                if not expected_lut_filename in zip.namelist():
                    self.report_error_message(context, "Error: Invalid plugin contents. File may be corrupted.")
                    return {'CANCELLED'}

                for f in zip.infolist():
                    if f.filename == expected_lut_filename and f.file_size != expected_lut_filesize:
                        self.report_error_message(context, "Error: Invalid plugin data. File may be corrupted.")
                        return {'CANCELLED'}

                dst_path = os.path.join(_get_addon_directory(), "third_party", "mixbox")
                zip.extractall(path=dst_path)

        except zipfile.BadZipFile as e:
            self.report_error_message(context, "Error: Invalid plugin installation file.")
            return {'CANCELLED'}
        except Exception as e:
            self.report_error_message(context, "Unknown Error Encountered: " + str(e))
            return {'CANCELLED'}

        installation_utils.update_mixbox_installation_status()
        success_message = "The Mixbox plugin has been installed successfully."
        self.report({'INFO'}, success_message)
        print(success_message)
        self.clear_error_message(context)
        return {'FINISHED'}


class FLIPFluidUninstallMixboxPlugin(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.uninstall_mixbox_plugin"
    bl_label = "Uninstall Mixbox"
    bl_description = ("Uninstall the Mixbox plugin")


    def execute(self, context):
        installation_utils.update_mixbox_installation_status()

        mixbox_base_directory = os.path.join(_get_addon_directory(), "third_party", "mixbox")
        mixbox_src_directory = os.path.join(mixbox_base_directory, "src")

        fpl.delete_files_in_directory(mixbox_base_directory, [".bin", ".txt"], remove_directory=False)
        fpl.delete_files_in_directory(mixbox_src_directory, [".h", ".cpp", ".png", ".md"], remove_directory=True)

        installation_utils.update_mixbox_installation_status()
        success_message = "The Mixbox plugin has been uninstalled successfully."
        self.report({'INFO'}, success_message)
        print(success_message)
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FLIPFluidInstallPresetLibrary(bpy.types.Operator, ImportHelper):
    bl_idname = "flip_fluid_operators.install_preset_library"
    bl_label = "Install Preset Scenes Library"
    bl_description = ("Select and install the Preset Scenes zip file into Blender's Asset Browser." + 
                      " The Preset Scenes file can be found in the FLIP Fluids addon downloads")

    filename_ext = "*.zip"
    filter_glob = StringProperty(
            default="*.zip",
            options={'HIDDEN'},
            maxlen=255,
            )
    exec(vcu.convert_attribute_to_28("filter_glob"))


    @classmethod
    def poll(cls, context):
        #return not installation_utils.is_mixbox_installation_complete()
        return True


    def tag_redraw(self, context):
        try:
            # Depending on window, area may be None
            context.area.tag_redraw()
        except:
            pass


    def clear_error_message(self, context):
        preferences = vcu.get_addon_preferences()
        preferences.is_preset_library_installation_error = False
        preferences.preset_library_installation_error_message = ""
        self.tag_redraw(context)


    def report_error_message(self, context, error_message, error_type={'ERROR_INVALID_INPUT'}):
        self.report(error_type, error_message)
        print(error_message)
        preferences = vcu.get_addon_preferences()
        preferences.is_preset_library_installation_error = True
        preferences.preset_library_installation_error_message = error_message
        self.tag_redraw(context)


    def is_path_equal(self, p1, p2):
        return os.path.normpath(p1) == os.path.normpath(p2)


    def execute(self, context):

        installation_utils.update_preset_library_installation_status()
        self.clear_error_message(context)

        preferences = vcu.get_addon_preferences()
        install_location = preferences.preset_library_install_location

        if not install_location:
            self.report_error_message(context, "Error: No install location selected. Select an install location above.")
            return {'CANCELLED'}

        if not os.path.exists(self.filepath):
            self.report_error_message(context, "Error: File does not exist. Select the Preset Scenes zip file.")
            return {'CANCELLED'}

        if not os.path.isfile(self.filepath):
            self.report_error_message(context, "Error: No file selected. Select the Preset Scenes zip file.")
            return {'CANCELLED'}

        if os.path.isfile(install_location):
            self.report_error_message(context, "Error: Invalid install location. Selected install location is an existing file. Select a valid install directory above.")
            return {'CANCELLED'}

        if not os.path.isdir(install_location):
            try:
                os.makedirs(install_location, exist_ok=True)
            except:
                self.report_error_message(context, "Error: Access denied. Unable to write files to install location: <" + install_location + ">")
                return {'CANCELLED'}

        # Test creating a directory
        test_directory_name = "temp_directory" + str(random.randint(0, 1000000))
        test_directory = os.path.join(install_location, test_directory_name)
        if not os.path.isdir(test_directory):
            try:
                os.mkdir(test_directory)
            except:
                self.report_error_message(context, "Error: Access denied. Unable to write files to install location: <" + install_location + ">")
                return {'CANCELLED'}
            try:
                os.rmdir(test_directory)
            except:
                self.report_error_message(context, "Error: Access denied. Unable to write files to install location: <" + install_location + ">")
                return {'CANCELLED'}
        else:
            self.report_error_message(context, "Error: Unknown Error. This should not happen. Try again or contact the developers.")
            return {'CANCELLED'}

        # Validate Preset Scenes zip file
        lib_version_str = ""
        try:
            expected_metadata_filepath = "FLIP_Fluids_Addon_Presets/.metadata/version.json"
            with zipfile.ZipFile(self.filepath, 'r') as zip:
                if not expected_metadata_filepath in zip.namelist():
                    self.report_error_message(context, "Error: Invalid Preset Scenes zip file contents. File may be corrupted.")
                    return {'CANCELLED'}

                with zip.open(expected_metadata_filepath) as version_json:
                    try:
                        version_data = json.loads(version_json.read())
                        version = version_data["version"]
                        lib_version_str = "v" + str(version[0]) + "." + str(version[1]) + "." + str(version[2])
                    except Exception as e:
                        self.report_error_message(context, "Error: Invalid Preset Metadata <Error: " + str(e) + ">. Contact the developers.")
                        return {'CANCELLED'}
                    
                zip.extractall(path=install_location)

        except zipfile.BadZipFile as e:
            self.report_error_message(context, "Error: Invalid Preset Scenes zip file. File may be corrupted.")
            return {'CANCELLED'}
        except Exception as e:
            self.report_error_message(context, "Unknown Error Encountered: " + str(e))
            return {'CANCELLED'}

        preset_library_name = "FLIP Fluids Addon Presets " + lib_version_str
        preset_library_directory = os.path.join(install_location, "FLIP_Fluids_Addon_Presets")

        bl_preferences = bpy.context.preferences
        bl_filepaths = bl_preferences.filepaths
        is_library_path_in_asset_browser = False
        for lib_entry in bl_filepaths.asset_libraries:
            if self.is_path_equal(lib_entry.path, preset_library_directory):
                is_library_path_in_asset_browser = True
                break

        if not is_library_path_in_asset_browser:
            bpy.ops.preferences.asset_library_add(directory=preset_library_directory)

        for lib_entry in bl_filepaths.asset_libraries:
            if self.is_path_equal(lib_entry.path, preset_library_directory):
                lib_entry.name = preset_library_name

        installation_utils.update_preset_library_installation_status()
        success_message = "The Preset Scenes Library has been installed successfully into the Blender Asset Browser."
        self.report({'INFO'}, success_message)
        self.clear_error_message(context)

        return {'FINISHED'}


class FLIPFluidSelectPresetLibraryFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.select_preset_library_folder"
    bl_label = "Install Preset Folder"
    bl_description = ("Select an existing Preset Library installation folder and add it to the Blender Asset Browser")

    directory = bpy.props.StringProperty(name="Directory", options={"HIDDEN"})
    exec(vcu.convert_attribute_to_28("directory"))

    filter_folder = bpy.props.BoolProperty(default=True, options={"HIDDEN"})
    exec(vcu.convert_attribute_to_28("filter_folder"))


    @classmethod
    def poll(cls, context):
        #return not installation_utils.is_mixbox_installation_complete()
        return True


    def tag_redraw(self, context):
        try:
            # Depending on window, area may be None
            context.area.tag_redraw()
        except:
            pass


    def clear_error_message(self, context):
        preferences = vcu.get_addon_preferences()
        preferences.is_preset_library_installation_error = False
        preferences.preset_library_installation_error_message = ""
        self.tag_redraw(context)


    def report_error_message(self, context, error_message, error_type={'ERROR_INVALID_INPUT'}):
        self.report(error_type, error_message)
        print(error_message)
        preferences = vcu.get_addon_preferences()
        preferences.is_preset_library_installation_error = True
        preferences.preset_library_installation_error_message = error_message
        self.tag_redraw(context)


    def is_path_equal(self, p1, p2):
        return os.path.normpath(p1) == os.path.normpath(p2)


    def is_valid_metadata_file(self, filepath):
        try:
            with open(filepath, 'r') as json_file:
                metadata = json.loads(json_file.read())
                if "name" in metadata.keys() and metadata["name"] == "FLIP Fluids Addon Presets":
                    return True, metadata
            return False, None
        except:
            return False, None


    def execute(self, context):

        installation_utils.update_preset_library_installation_status()
        self.clear_error_message(context)

        install_directory = self.directory
        if not os.path.exists(install_directory):
            self.report_error_message(context, "Error: Error: Selected folder does not exist <" + install_directory + ">")
            return {'CANCELLED'}

        if not os.path.isdir(install_directory):
            self.report_error_message(context, "Error: Selected folder is not a directory <" + install_directory + ">")
            return {'CANCELLED'}

        if not os.listdir(install_directory):
            self.report_error_message(context, "Error: Selected folder is empty <" + install_directory + ">")
            return {'CANCELLED'}

        found_installations = []

        # Check if current directory is a valid preset library folder
        expected_metadata_filepath = os.path.join(install_directory, ".metadata/version.json")
        if os.path.isfile(expected_metadata_filepath):
            is_valid, metadata = self.is_valid_metadata_file(expected_metadata_filepath)
            if is_valid:
                metadata["install_path"] = install_directory
                found_installations.append(metadata)

        # check if subdirectories are valid preset library folders
        if not found_installations:
            subdirs = [os.path.join(install_directory, d) for d in os.listdir(install_directory) if os.path.isdir(os.path.join(install_directory, d))]
            for path in subdirs:
                expected_metadata_filepath = os.path.join(path, ".metadata/version.json")
                if os.path.isfile(expected_metadata_filepath):
                    is_valid, metadata = self.is_valid_metadata_file(expected_metadata_filepath)
                    if is_valid:
                        metadata["install_path"] = path
                        found_installations.append(metadata)

        if not found_installations:
            self.report_error_message(context, "Error: No valid preset libraries found in selected folder or subfolders <" + install_directory + ">")
            return {'CANCELLED'}

        bl_preferences = bpy.context.preferences
        bl_filepaths = bl_preferences.filepaths
        for metadata in found_installations:
            is_library_path_in_asset_browser = False
            preset_library_directory = metadata["install_path"]
            for lib_entry in bl_filepaths.asset_libraries:
                if self.is_path_equal(lib_entry.path, preset_library_directory):
                    is_library_path_in_asset_browser = True
                    break

            if not is_library_path_in_asset_browser:
                bpy.ops.preferences.asset_library_add(directory=preset_library_directory)

            for lib_entry in bl_filepaths.asset_libraries:
                if self.is_path_equal(lib_entry.path, preset_library_directory):
                    version = metadata["version"]
                    lib_version_str = "v" + str(version[0]) + "." + str(version[1]) + "." + str(version[2])
                    preset_library_name = "FLIP Fluids Addon Presets " + lib_version_str
                    lib_entry.name = preset_library_name

        installation_utils.update_preset_library_installation_status()
        success_message = "The Preset Scenes Library has been installed successfully into the Blender Asset Browser."
        print(success_message)
        self.report({'INFO'}, success_message)
        self.clear_error_message(context)
        self.tag_redraw(context)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class FLIPFluidPresetLibraryCopyInstallLocation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_library_copy_install_location"
    bl_label = "Copy Install Location"
    bl_description = ("Copy the preset library location to the Install Location field and" + 
                      " system clipboard. The install location is the parent directory of the path listed below")

    install_location = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("install_location"))

    def execute(self, context):
        preferences = vcu.get_addon_preferences()
        preferences.preset_library_install_location = self.install_location
        bpy.context.window_manager.clipboard = self.install_location
        return {'FINISHED'}


class FLIPFluidUninstallPresetLibrary(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.uninstall_preset_library"
    bl_label = "Uninstall Preset Library"
    bl_description = ("Uninstall the preset library. The preset library will be removed from" +
                      " the Blender Asset Browser and the files deleted from your system")

    install_info_json_string = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("install_info_json_string"))


    def tag_redraw(self, context):
        try:
            # Depending on window, area may be None
            context.area.tag_redraw()
        except:
            pass


    def is_path_equal(self, p1, p2):
        return os.path.normpath(p1) == os.path.normpath(p2)


    def execute(self, context):
        installation_utils.update_preset_library_installation_status()

        install_info = json.loads(self.install_info_json_string)
        library_path = install_info["path"]
        blend_filenames = install_info["metadata"]["blend_files"]
        other_filenames = [
            "blender_assets.cats.txt",
            "blender_assets.cats.txt~",
            "README.txt",
            ".metadata/version.json",
            "releasenotes.txt"
        ]

        library_filenames = blend_filenames + other_filenames
        for name in library_filenames:
            filepath = os.path.join(library_path, name)
            if os.path.isfile(filepath):
                fpl.delete_file(filepath, error_ok=True)

        directories = [
            os.path.join(library_path, ".metadata"),
            library_path
        ]
        for d in directories:
            fpl.delete_files_in_directory(d, [], remove_directory=True)

        bl_preferences = bpy.context.preferences
        bl_filepaths = bl_preferences.filepaths
        
        library_index = -1
        for idx, lib_entry in enumerate(bl_filepaths.asset_libraries):
            if self.is_path_equal(lib_entry.path, library_path):
                library_index = idx
                break

        if library_index >= 0:
            bpy.ops.preferences.asset_library_remove(index=library_index)

        installation_utils.update_preset_library_installation_status()
        success_message = "The Preset Library <" + install_info["name"] + "> has been uninstalled successfully."
        self.report({'INFO'}, success_message)
        self.tag_redraw(context)

        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FLIPFluidPreferencesFindGPUDevices(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preferences_find_gpu_devices"
    bl_label = "Find GPU Devices"
    bl_description = "Search for GPU compute devices"

    def execute(self, context):
        preferences = vcu.get_addon_preferences()

        devices = gpu_utils.find_gpu_devices()
        preferences.gpu_devices.clear()
        max_score = -1
        max_name = ""
        for d in devices:
            new_device = preferences.gpu_devices.add()
            new_device.name = d['name']
            new_device.description = d['description']
            new_device.score = d['score']

            if new_device.score > max_score:
                max_score = new_device.score
                max_name = new_device.name

        preferences.selected_gpu_device = max_name
        preferences.is_gpu_devices_initialized = True

        self.report({'INFO'}, "Found " + str(len(devices)) + " GPU compute device(s).")
        return {'FINISHED'}


class VersionDataTextEntry(bpy.types.PropertyGroup):
    text = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("text"))


class FlipFluidCheckForUpdates(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.check_for_updates"
    bl_label = "Check for Updates"
    bl_description = ("Check for version updates. Note: this will not automatically" + 
        " install new versions of the addon. Version updates can be found in your" + 
        " Blender Market account downloads")

    version_data_url = StringProperty(default="http://rlguy.com/blender_flip_fluids/version_data/versions.json")
    exec(vcu.convert_attribute_to_28("version_data_url"))

    error = BoolProperty(default=False)
    exec(vcu.convert_attribute_to_28("error"))

    error_message = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("error_message"))

    version_text = CollectionProperty(type=VersionDataTextEntry)
    exec(vcu.convert_attribute_to_28("version_text"))

    window_width = IntProperty(default=1280)
    exec(vcu.convert_attribute_to_28("window_width"))


    def initialize_ui_text(self, text):
        self.version_text.clear()
        
        module = sys.modules[installation_utils.get_module_name()]
        current_version = module.bl_info.get('version', (-1, -1, -1))

        version_data_json = json.loads(text)
        version_data = []
        for k,v in version_data_json.items():
            version = k.split('.')
            version_tuple = (int(version[0]), int(version[1]), int(version[2]))
            if version_tuple >= current_version:
                version_data.append({'version': version_tuple, 'data': v})

        version_data_sorted = sorted(version_data, key=lambda k: k['version'], reverse=True)
        if len(version_data) <= 1:
            entry = self.version_text.add()
            entry.text = "You are currently using the most recent version of the FLIP Fluids addon!"
        else:
            entry = self.version_text.add()
            entry.text = "A new version of the FLIP Fluids addon is available!"
            entry = self.version_text.add()
            entry.text = "You may download the update from your Blender Market account downloads."
        entry = self.version_text.add()

        for ve in version_data_sorted:
            version_string = str(ve['version'][0]) + "." + str(ve['version'][1]) + "." + str(ve['version'][2])
            entry = self.version_text.add()
            entry.text = "Version " + version_string
            for change_text in ve['data']:
                text_list = textwrap.wrap(change_text, width=120)
                for i,text_line in enumerate(text_list):
                    if i == 0:
                        indent = 6
                    else:
                        indent = 10
                    entry = self.version_text.add()
                    entry.text = " "*indent + text_line
            self.version_text.add()


    def draw(self, context):
        column = self.layout.column(align=True)

        if self.error:
            column.label(text="Error checking for updates:", icon="ERROR")
            column.separator()
            column.label(text=self.error_message)
            return

        for text_entry in self.version_text:
            column.label(text=text_entry.text)


    def execute(self, context):
        return {'FINISHED'}


    def invoke(self, context, event):
        self.error = False
        try:
            response = urllib.request.urlopen(self.version_data_url)
        except urllib.error.HTTPError:
            self.error = True
            self.error_message = "Unable to find version data file. Please contact the developers."
        except urllib.error.URLError:
            self.error = True
            self.error_message = "No network connection found. Please check your internet connection."

        if self.error:
            return context.window_manager.invoke_props_dialog(self, width=self.window_width)

        data = response.read()
        text = data.decode('utf-8')
        self.initialize_ui_text(text)
        return context.window_manager.invoke_props_dialog(self, width=self.window_width)


def get_gpu_string():
    gpu_string = ""
    if not bpy.app.background:
        try:
            import gpu
            gpu_string = gpu.platform.renderer_get() + " " + gpu.platform.vendor_get() + " " + gpu.platform.version_get()
        except:
            pass
    return gpu_string


def get_system_info_dict():
    def prepr(v):
        r = repr(v)
        vt = type(v)
        if vt is bytes:
            r = r[2:-1]
        elif vt is list or vt is tuple:
            r = r[1:-1]
        return r

    bl_info = sys.modules[installation_utils.get_module_name()].bl_info

    blender_version = ("%s, %s, %s %s, %s" % (
            bpy.app.version_string,
            prepr(bpy.app.build_branch),
            prepr(bpy.app.build_commit_date),
            prepr(bpy.app.build_commit_time),
            prepr(bpy.app.build_hash),
            ))

    gpu_string = "Unknown (fill in)"
    if not bpy.app.background:
        try:
            import gpu
            gpu_string = gpu.platform.renderer_get() + " " + gpu.platform.vendor_get() + " " + gpu.platform.version_get()
        except Exception as e:
            print(traceback.format_exc())
            print(e)

    cpu_string = "Unknown (fill in)"
    try:
        from ..third_party import cpuinfo
        cpu_string = cpuinfo.cpu.info[0]['ProcessorNameString']
    except KeyError:
        if platform.system() == "Darwin":
            # Apple Silicon systems may not contain the ProcessorNameString
            try:
                cpu_string = cpuinfo.cpu.info['arch'].decode("utf-8")
            except Exception as e:
                print(traceback.format_exc())
                print(e)

        if platform.system() == "Linux":
            try:
                cpu_string = cpuinfo.cpu.info[0]['model name']
            except:
                # May not be able to retrieve processor on some Linux distributions
                # Currently unknown how to solve this issue. Processor will be marked
                # as 'Unknown' in this case
                pass
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    threads_string = "Unknown"
    try:
        original_threads_mode = bpy.context.scene.render.threads_mode
        bpy.context.scene.render.threads_mode = 'AUTO'
        num_threads = bpy.context.scene.render.threads
        bpy.context.scene.render.threads_mode = original_threads_mode
        threads_string = str(num_threads)
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    addon_path_string = _get_addon_directory()

    cache_path_string = "N/A"
    cache_path_exists_string = "N/A"
    log_files_string = "N/A"
    try:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            cache_path_string = dprops.cache.get_cache_abspath()
            cache_path_exists = os.path.isdir(cache_path_string)
            cache_path_exists_string = str(cache_path_exists)
            if cache_path_exists:
                logs_directory = os.path.join(cache_path_string, "logs")
                if os.path.isdir(logs_directory):
                    log_files = [f for f in os.listdir(logs_directory) if os.path.isfile(os.path.join(logs_directory, f))]
                    log_files_string = str(len(log_files))
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    default_addons = [
            "Pose Library",
            "BioVision Motion Capture (BVH) format",
            "FBX format",
            "STL format",
            "Scalable Vector Graphics (SVG) 1.1 format",
            "Stanford PLY format",
            "UV Layout",
            "Wavefront OBJ format (legacy)",
            "glTF 2.0 format",
            "Cycles Render Engine",
            "Web3D X3D/VRML2 format"
            ]

    addons_string = ""
    try:
        for mod_name in bpy.context.preferences.addons.keys():
            mod = sys.modules[mod_name]
            addon_name = mod.bl_info.get("name")
            if addon_name not in default_addons:
                addons_string += addon_name + ", "
        addons_string = addons_string.removesuffix(", ")
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        addons_string = "Unknown"

    developer_tools_string = "Uknown"
    try:
        preferences = vcu.get_addon_preferences()
        developer_tools_string = "Enabled" if preferences.enable_developer_tools else "Disabled"
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    mixbox_installed_string = "Unknown"
    try:
        is_mixbox_installed = installation_utils.is_mixbox_installation_complete()
        mixbox_installed_string = "Installed" if is_mixbox_installed else "Not Installed"
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    features_string = "N/A"
    try:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            features_string = ""
            if dprops.whitewater.enable_whitewater_simulation:
                features_string += "Whitewater, "
            if dprops.world.enable_viscosity:
                if dprops.surface.enable_viscosity_attribute:
                    features_string += "Variable Viscosity, "
                else:
                    features_string += "Constant Viscosity, "
            if dprops.world.enable_surface_tension:
                features_string += "Surface Tension, "
            if dprops.world.enable_sheet_seeding:
                features_string += "Sheeting, "
            features_string = features_string.removesuffix(", ")
        if not features_string:
            features_string = "Default"
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        features_string = "Unknown"

    attributes_string = "N/A"
    try:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            d = api_utils.get_enabled_features_affected_by_T88811()
            if d is not None:
                if d["attributes"]["surface"] or d["attributes"]["whitewater"] or d["viscosity"]:
                    attributes_string = ""
                    for att in d["attributes"]["surface"]:
                        attributes_string += "Surface " + att + ", "
                    if d["viscosity"]:
                        attributes_string += "Surface Viscosity, "
                    for att in d["attributes"]["whitewater"]:
                        attributes_string += "Whitewater " + att + ", "
                    attributes_string = attributes_string.removesuffix(", ")
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    lock_interface_string = "Unknown"
    try:
        lock_interface_string = "Enabled" if bpy.context.scene.render.use_lock_interface else "Disabled"
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    persistent_data_string = "Disabled"
    try:
        persistent_data_string = "Enabled" if api_utils.is_persistent_data_issue_relevant() else "Disabled"
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    blender_binary_string = "Unknown"
    try:
        blender_binary_string  = bpy.app.binary_path
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    viewport_modes_string = "N/A"
    try:
        shading_modes = []
        for area in bpy.data.screens[3].areas: 
            if area.type == 'VIEW_3D':
               for space in area.spaces: 
                   if space.type == 'VIEW_3D':
                      shading_modes.append(space.shading.type)
        if shading_modes:
            viewport_modes_string = ""
            for mode in shading_modes:
                viewport_modes_string += mode + ", "
        viewport_modes_string = viewport_modes_string.removesuffix(", ")
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        viewport_modes_string = "Unknown"

    domains_string = "N/A"
    domain_count = 0
    obstacle_count = 0
    fluid_count = 0
    inflow_count = 0
    outflow_count = 0
    force_field_count = 0
    animated_obstacle_count = 0
    animated_fluid_count = 0
    animated_inflow_count = 0
    animated_outflow_count = 0
    animated_force_field_count = 0
    skip_export_obstacle_count = 0
    skip_export_fluid_count = 0
    skip_export_inflow_count = 0
    skip_export_outflow_count = 0
    skip_export_force_field_count = 0
    obstacles_string = "Unknown"
    fluids_string = "Unknown"
    inflows_string = "Unknown"
    outflows_string = "Unknown"
    force_fields_string = "Unknown"
    animated_obstacles_string = "Unknown"
    animated_fluids_string = "Unknown"
    animated_inflows_string = "Unknown"
    animated_outflows_string = "Unknown"
    animated_force_fields_string = "Unknown"
    skip_export_obstacles_string = "Unknown"
    skip_export_fluids_string = "Unknown"
    skip_export_inflows_string = "Unknown"
    skip_export_outflows_string = "Unknown"
    skip_export_force_fields_string = "Unknown"
    flip_objects_string = "Unknown"
    found_domains = []
    try:
        for scene in bpy.data.scenes:
            for obj in scene.objects:
                if obj.flip_fluid.is_domain():
                    domain_count += 1
                    found_domains.append(obj.name + " <scene: " + scene.name + ">")

                if obj.flip_fluid.is_obstacle():
                    obstacle_count += 1
                    if obj.flip_fluid.obstacle.export_animated_mesh:
                        animated_obstacle_count += 1
                    if obj.flip_fluid.obstacle.skip_reexport:
                        skip_export_obstacle_count += 1
                if obj.flip_fluid.is_fluid():
                    fluid_count += 1
                    if obj.flip_fluid.fluid.export_animated_mesh:
                        animated_fluid_count += 1
                    if obj.flip_fluid.fluid.skip_reexport:
                        skip_export_fluid_count += 1
                if obj.flip_fluid.is_inflow():
                    inflow_count += 1
                    if obj.flip_fluid.inflow.export_animated_mesh:
                        animated_inflow_count += 1
                    if obj.flip_fluid.inflow.skip_reexport:
                        skip_export_inflow_count += 1
                if obj.flip_fluid.is_outflow():
                    outflow_count += 1
                    if obj.flip_fluid.outflow.export_animated_mesh:
                        animated_outflow_count += 1
                    if obj.flip_fluid.outflow.skip_reexport:
                        skip_export_outflow_count += 1
                if obj.flip_fluid.is_force_field():
                    force_field_count += 1
                    if obj.flip_fluid.force_field.export_animated_mesh:
                        skip_export_force_field_count += 1
                    if obj.flip_fluid.force_field.skip_reexport:
                        skip_export_force_field_count += 1
        if found_domains:
            domains_string = ""
            for d in found_domains:
                domains_string += d + ", "
            domains_string = domains_string.removesuffix(", ")

        animated_obstacles_string = " <Export Animated: " + str(animated_obstacle_count) + "> "
        animated_fluids_string = " <Export Animated: " + str(animated_fluid_count) + "> "
        animated_inflows_string = " <Export Animated: " + str(animated_inflow_count) + "> "
        animated_outflows_string = " <Export Animated: " + str(animated_outflow_count) + "> "
        animated_force_fields_string = " <Export Animated: " + str(animated_force_field_count) + "> "
        skip_export_obstacles_string = "<Skip Re-export: " + str(skip_export_obstacle_count) + ">"
        skip_export_fluids_string = "<Skip Re-export: " + str(skip_export_fluid_count) + ">"
        skip_export_inflows_string = "<Skip Re-export: " + str(skip_export_inflow_count) + ">"
        skip_export_outflows_string = "<Skip Re-export: " + str(skip_export_outflow_count) + ">"
        skip_export_force_fields_string = "<Skip Re-export: " + str(skip_export_force_field_count) + ">"

        obstacles_string = "0"
        fluids_string = "0"
        inflows_string = "0"
        outflows_string = "0"
        force_fields_string = "0"

        if obstacle_count:
            obstacles_string = str(obstacle_count) + animated_obstacles_string + skip_export_obstacles_string
        if fluid_count:
            fluids_string = str(fluid_count) + animated_fluids_string + skip_export_fluids_string
        if inflow_count:
            inflows_string = str(inflow_count) + animated_inflows_string + skip_export_inflows_string
        if outflow_count:
            outflows_string = str(outflow_count) + animated_outflows_string + skip_export_outflows_string
        if force_field_count:
            force_fields_string = str(force_field_count) + animated_force_fields_string + skip_export_force_fields_string
        flip_objects_string = str(domain_count + obstacle_count + fluid_count + inflow_count + outflow_count + force_field_count)
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    objects_string = "Unknown"
    try:
        objects_string = str(len(bpy.data.objects))
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    renderer_string = "Unknown"
    cycles_device_string = "N/A"
    try:
        renderer_string = bpy.context.scene.render.engine
        if renderer_string == 'CYCLES':
            cycles_device_string = bpy.context.scene.cycles.device
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    simulation_visibility_string = "N/A"
    surface_visibility_string = "N/A"
    whitewater_visibility_string = "N/A"
    try:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            sim_viewport = "Enabled" if bpy.context.scene.flip_fluid.show_viewport else "Disabled"
            sim_render = "Enabled" if bpy.context.scene.flip_fluid.show_render else "Disabled"
            simulation_visibility_string = "<Viewport: " + sim_viewport + "> <Render: " + sim_render + ">"

            surface_object = dprops.mesh_cache.surface.get_cache_object()
            if surface_object is not None:
                surface_viewport = dprops.render.viewport_display
                surface_render = dprops.render.render_display
                surface_visibility_string = "<Viewport: " + surface_viewport + "> <Render: " + surface_render + ">"

            whitewater_objects = [
                    dprops.mesh_cache.foam.get_cache_object(),
                    dprops.mesh_cache.bubble.get_cache_object(),
                    dprops.mesh_cache.spray.get_cache_object(),
                    dprops.mesh_cache.dust.get_cache_object()
                    ]
            if not all(obj is None for obj in whitewater_objects):
                whitewater_viewport = str(dprops.render.whitewater_viewport_display)
                whitewater_render = str(dprops.render.whitewater_render_display)
                whitewater_visibility_string = "<Viewport: " + whitewater_viewport + "> <Render: " + whitewater_render + ">"
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    d = {}
    d['blender_version'] = blender_version
    d['addon_version'] = bl_info.get('description', "Missing Version Label")
    d['operating_system'] = platform.platform()
    d['cpu'] = cpu_string
    d['threads'] = threads_string
    d['gpu'] = gpu_string
    d['ram'] = "Unknown (fill in)"

    d['addon_path'] = addon_path_string
    d['blender_binary'] = blender_binary_string
    d['renderer'] = renderer_string
    d['cycles_device'] = cycles_device_string
    d['viewport_modes'] = viewport_modes_string
    d['objects'] = objects_string
    d['flip_objects'] = flip_objects_string
    d['domains'] = domains_string
    d['obstacles'] = obstacles_string
    d['fluids'] = fluids_string
    d['inflows'] = inflows_string
    d['outflows'] = outflows_string
    d['force_fields'] = force_fields_string
    d['cache_path'] = cache_path_string
    d['cache_exists'] = cache_path_exists_string
    d['cache_logs'] = log_files_string
    d['simulation_visibility'] = simulation_visibility_string
    d['surface_visibility'] = surface_visibility_string
    d['whitewater_visibility'] = whitewater_visibility_string
    d['features'] = features_string
    d['attributes'] = attributes_string
    d['lock_interface'] = lock_interface_string
    d['persistent_data'] = persistent_data_string
    d['developer_tools'] = developer_tools_string
    d['mixbox'] = mixbox_installed_string
    d['addons'] = addons_string
    return d


class FlipFluidReportBugPrefill(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.report_bug_prefill"
    bl_label = "Report a Bug (GitHub)"
    bl_description = ("Start a bug report on the FLIP Fluids addon issue tracker." + 
                      " This operator will automatically" + 
                      " pre-fill the report with your system and Blend file information." + 
                      " Not all information may be found depending on system." + 
                      " A GitHub account is required.")


    def execute(self, context):
        return {'FINISHED'}


    def invoke(self, context, event):
        sys_info = get_system_info_dict()
        
        user_info = ""
        user_info += "#### System and Blend File Information\n\n"
        user_info += "**Blender Version:** " + sys_info['blender_version'] + "\n"
        user_info += "**Addon Version:** " + sys_info['addon_version'] + "\n"
        user_info += "**OS:** " + sys_info['operating_system'] + "\n"
        user_info += "**GPU:** " + sys_info['gpu'] + "\n"
        user_info += "**CPU:** " + sys_info['cpu'] + "\n"
        user_info += "**CPU Threads:** " + sys_info['threads'] + "\n"
        user_info += "**RAM:** " + sys_info['ram'] + "\n\n"

        user_info += "**Blender Binary:** " + sys_info['blender_binary'] + "\n"
        user_info += "**Addon Path:** " + sys_info['addon_path'] + "\n"
        user_info += "**Renderer:** " + sys_info['renderer'] + "\n"
        user_info += "**Cycles Device:** " + sys_info['cycles_device'] + "\n"
        user_info += "**Viewport Modes:** " + sys_info['viewport_modes'] + "\n"
        user_info += "**Objects:** " + sys_info['objects'] + "\n"
        user_info += "**FLIP Objects:** " + sys_info['flip_objects'] + "\n"
        user_info += "**FLIP Domains:** " + sys_info['domains'] + "\n"
        user_info += "**Obstacle Objects:** " + sys_info['obstacles'] + "\n"
        user_info += "**Fluid Objects:** " + sys_info['fluids'] + "\n"
        user_info += "**Inflow Objects:** " + sys_info['inflows'] + "\n"
        user_info += "**Outflow Objects:** " + sys_info['outflows'] + "\n"
        user_info += "**Force Objects:** " + sys_info['force_fields'] + "\n"
        user_info += "**Cache Path:** " + sys_info['cache_path'] + "\n"
        user_info += "**Cache Exists:** " + sys_info['cache_exists'] + "\n"
        user_info += "**Cache Logs:** " + sys_info['cache_logs'] + "\n"
        user_info += "**Simulation Visibility:** " + sys_info['simulation_visibility'] + "\n"
        user_info += "**Surface Visibility:** " + sys_info['surface_visibility'] + "\n"
        user_info += "**Whitewater Visibility:** " + sys_info['whitewater_visibility'] + "\n"
        user_info += "**Enabled Features:** " + sys_info['features'] + "\n"
        user_info += "**Enabled Attributes:** " + sys_info['attributes'] + "\n"
        user_info += "**Lock Interface:** " + sys_info['lock_interface'] + "\n"
        user_info += "**Cycles Persistent Data:** " + sys_info['persistent_data'] + "\n"
        user_info += "**Developer Tools:** " + sys_info['developer_tools'] + "\n"
        user_info += "**Mixbox Plugin:** " + sys_info['mixbox'] + "\n"
        user_info += "**Enabled Addons:** " + sys_info['addons'] + "\n\n"
        user_info += "#### Describe the bug\n\n"
        user_info += "Provide a clear and concise description of what the actual bug/issue is that you are experiencing.\n\n"
        user_info += "#### To Reproduce\n\n"
        user_info += "Provide descriptive instructions for how to reproduce the issue or how to use your .blend file.\n\n"
        user_info += "#### Expected Behaviour\n\n"
        user_info += "A description of what you expected to happen.\n\n"
        user_info += "#### Actual Behaviour\n\n"
        user_info += "A description of what actually happened.\n\n"
        user_info += "#### Screenshots\n\n"
        user_info += "If applicable, add screenshots to help explain your problem.\n\n"

        user_info = user_info.replace(" ", "%20")
        user_info = user_info.replace("\n", "%0A")
        user_info = user_info.replace("#", "%23")

        base_url = "https://github.com/rlguy/Blender-FLIP-Fluids/issues/new?body="
        full_url = base_url + user_info
        bpy.ops.wm.url_open(url=full_url)

        return {'FINISHED'}


def get_system_info_string():
    sys_info = get_system_info_dict()
        
    user_info = ""
    user_info += "Blender Version: " + sys_info['blender_version'] + "\n"
    user_info += "Addon Version: " + sys_info['addon_version'] + "\n"
    user_info += "OS: " + sys_info['operating_system'] + "\n"
    user_info += "GPU: " + sys_info['gpu'] + "\n"
    user_info += "CPU: " + sys_info['cpu'] + "\n"
    user_info += "CPU Threads: " + sys_info['threads'] + "\n"
    user_info += "RAM: " + sys_info['ram'] + "\n\n"

    user_info += "Blender Binary: " + sys_info['blender_binary'] + "\n"
    user_info += "Addon Path: " + sys_info['addon_path'] + "\n"
    user_info += "Renderer: " + sys_info['renderer'] + "\n"
    user_info += "Cycles Device: " + sys_info['cycles_device'] + "\n"
    user_info += "Viewport Modes: " + sys_info['viewport_modes'] + "\n"
    user_info += "Objects: " + sys_info['objects'] + "\n"
    user_info += "FLIP Objects: " + sys_info['flip_objects'] + "\n"
    user_info += "FLIP Domains: " + sys_info['domains'] + "\n"
    user_info += "Obstacle Objects: " + sys_info['obstacles'] + "\n"
    user_info += "Fluid Objects: " + sys_info['fluids'] + "\n"
    user_info += "Inflow Objects: " + sys_info['inflows'] + "\n"
    user_info += "Outflow Objects: " + sys_info['outflows'] + "\n"
    user_info += "Force Field Objects: " + sys_info['force_fields'] + "\n"
    user_info += "Cache Path: " + sys_info['cache_path'] + "\n"
    user_info += "Cache Exists: " + sys_info['cache_exists'] + "\n"
    user_info += "Cache Logs: " + sys_info['cache_logs'] + "\n"
    user_info += "Simulation Visibility: " + sys_info['simulation_visibility'] + "\n"
    user_info += "Surface Visibility: " + sys_info['surface_visibility'] + "\n"
    user_info += "Whitewater Visibility: " + sys_info['whitewater_visibility'] + "\n"
    user_info += "Enabled Features: " + sys_info['features'] + "\n"
    user_info += "Enabled Attributes: " + sys_info['attributes'] + "\n"
    user_info += "Lock Interface: " + sys_info['lock_interface'] + "\n"
    user_info += "Cycles Persistent Data: " + sys_info['persistent_data'] + "\n"
    user_info += "Developer Tools: " + sys_info['developer_tools'] + "\n"
    user_info += "Mixbox Plugin: " + sys_info['mixbox'] + "\n"
    user_info += "Enabled Addons: " + sys_info['addons']
    return user_info


class FlipFluidCopySystemInfo(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.copy_system_info"
    bl_label = "Copy System & Blend Info"
    bl_description = ("Copy your system and Blend file info to the clipboard." + 
                      " Paste this info into messages to us sent through the" + 
                      " marketplace, support@flipfluids.com, or elsewhere." + 
                      " Not all information may be found depending on system")


    def execute(self, context):
        return {'FINISHED'}


    def invoke(self, context, event):
        user_info = get_system_info_string()
        bpy.context.window_manager.clipboard = user_info

        print("*** Copied system and Blend file info to clipboard: ***")
        print(user_info)

        return {'FINISHED'}


class FlipFluidOpenPreferences(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.open_preferences"
    bl_label = "FLIP Fluids Preferences"
    bl_description = ("Open the FLIP Fluids addon preferences menu")


    def execute(self, context):
        return {'FINISHED'}


    def invoke(self, context, event):
        bpy.ops.preferences.addon_show(module=installation_utils.get_module_name())
        return {'FINISHED'}


class FlipFluidTestBakeAlarm(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.test_bake_alarm"
    bl_label = "Test Alarm"
    bl_description = ("Test and play the alarm sound")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        json_filepath = os.path.join(audio_utils.get_sounds_directory(), "alarm", "sound_data.json")
        audio_utils.play_sound(json_filepath)
        return {'FINISHED'}


class FLIPFLUIDS_MT_help_menu(bpy.types.Menu):
    bl_label = "FLIP Fluids"
    bl_idname = "FLIPFLUIDS_MT_help_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.report_bug_prefill", icon="URL")
        self.layout.operator("flip_fluid_operators.copy_system_info", icon="COPYDOWN")

        if vcu.is_blender_28():
            self.layout.operator("flip_fluid_operators.open_preferences", icon="PREFERENCES")


def draw_flip_fluids_help_menu(self, context):
    self.layout.separator()
    self.layout.menu(FLIPFLUIDS_MT_help_menu.bl_idname)


def register():
    bpy.utils.register_class(FLIPFluidPreferencesExportUserData)
    bpy.utils.register_class(FLIPFluidPreferencesImportUserData)
    bpy.utils.register_class(FLIPFluidPreferencesFindGPUDevices)

    bpy.utils.register_class(FLIPFluidInstallMixboxPlugin)
    bpy.utils.register_class(FLIPFluidUninstallMixboxPlugin)

    bpy.utils.register_class(FLIPFluidInstallPresetLibrary)
    bpy.utils.register_class(FLIPFluidSelectPresetLibraryFolder)
    bpy.utils.register_class(FLIPFluidPresetLibraryCopyInstallLocation)
    bpy.utils.register_class(FLIPFluidUninstallPresetLibrary)

    bpy.utils.register_class(VersionDataTextEntry)
    bpy.utils.register_class(FlipFluidCheckForUpdates)

    bpy.utils.register_class(FlipFluidReportBugPrefill)
    bpy.utils.register_class(FlipFluidCopySystemInfo)
    bpy.utils.register_class(FlipFluidOpenPreferences)

    bpy.utils.register_class(FlipFluidTestBakeAlarm)

    bpy.utils.register_class(FLIPFLUIDS_MT_help_menu)

    try:
        # Blender 2.8+
        bpy.types.TOPBAR_MT_help.append(draw_flip_fluids_help_menu)
    except:
        pass

    try:
        # Blender 2.79
        bpy.types.INFO_MT_help.append(draw_flip_fluids_help_menu)
    except:
        pass


def unregister():
    bpy.utils.unregister_class(FLIPFluidPreferencesExportUserData)
    bpy.utils.unregister_class(FLIPFluidPreferencesImportUserData)
    bpy.utils.unregister_class(FLIPFluidPreferencesFindGPUDevices)

    bpy.utils.unregister_class(FLIPFluidInstallMixboxPlugin)
    bpy.utils.unregister_class(FLIPFluidUninstallMixboxPlugin)

    bpy.utils.unregister_class(FLIPFluidInstallPresetLibrary)
    bpy.utils.unregister_class(FLIPFluidSelectPresetLibraryFolder)
    bpy.utils.unregister_class(FLIPFluidPresetLibraryCopyInstallLocation)
    bpy.utils.unregister_class(FLIPFluidUninstallPresetLibrary)

    bpy.utils.unregister_class(VersionDataTextEntry)
    bpy.utils.unregister_class(FlipFluidCheckForUpdates)

    bpy.utils.unregister_class(FlipFluidReportBugPrefill)
    bpy.utils.unregister_class(FlipFluidCopySystemInfo)
    bpy.utils.unregister_class(FlipFluidOpenPreferences)

    bpy.utils.unregister_class(FlipFluidTestBakeAlarm)

    bpy.utils.unregister_class(FLIPFLUIDS_MT_help_menu)
    
    try:
        # Blender 2.8+
        bpy.types.TOPBAR_MT_help.remove(draw_flip_fluids_help_menu)
    except:
        pass

    try:
        # Blender 2.79
        bpy.types.INFO_MT_help.remove(draw_flip_fluids_help_menu)
    except:
        pass
