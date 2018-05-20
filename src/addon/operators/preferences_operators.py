# Blender FLIP Fluid Add-on
# Copyright (C) 2018 Ryan L. Guy
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

import bpy, os, shutil, json, zipfile
from bpy_extras.io_utils import ImportHelper

from bpy.props import (
        StringProperty,
        )

from ..presets import preset_library

from ..pyfluid import gpu_utils


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
        temp_dir = self.get_temp_directory()
        if not os.path.exists(temp_dir):
            try:
                os.makedirs(temp_dir)
            except Exception as e:
                return str(e)

        user_info = self.get_user_settings_info()

        user_info_str = json.dumps(user_info, sort_keys=True, indent=4)
        user_info_filepath = os.path.join(temp_dir, "user_settings.info")
        with open(user_info_filepath, 'w') as f:
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
        default_directory = context.user_preferences.filepaths.temporary_directory
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


class FLIPFluidPreferencesFindGPUDevices(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preferences_find_gpu_devices"
    bl_label = "Find GPU Devices"
    bl_description = "Search for GPU compute devices"

    def execute(self, context):
        id_name = __name__.split(".")[0]
        preferences = bpy.context.user_preferences.addons[id_name].preferences

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


def register():
    bpy.utils.register_class(FLIPFluidPreferencesExportUserData)
    bpy.utils.register_class(FLIPFluidPreferencesImportUserData)
    bpy.utils.register_class(FLIPFluidPreferencesFindGPUDevices)


def unregister():
    bpy.utils.unregister_class(FLIPFluidPreferencesExportUserData)
    bpy.utils.unregister_class(FLIPFluidPreferencesImportUserData)
    bpy.utils.unregister_class(FLIPFluidPreferencesFindGPUDevices)
