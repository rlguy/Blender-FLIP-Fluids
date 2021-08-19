# Blender FLIP Fluids Add-on
# Copyright (C) 2021 Ryan L. Guy
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

import bpy, os, shutil, json, zipfile, urllib.request, sys, textwrap
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
        " Blender Market account downloads.")

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
        
        module = sys.modules["flip_fluids_addon"]
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


def register():
    bpy.utils.register_class(FLIPFluidPreferencesExportUserData)
    bpy.utils.register_class(FLIPFluidPreferencesImportUserData)
    bpy.utils.register_class(FLIPFluidPreferencesFindGPUDevices)

    bpy.utils.register_class(VersionDataTextEntry)
    bpy.utils.register_class(FlipFluidCheckForUpdates)


def unregister():
    bpy.utils.unregister_class(FLIPFluidPreferencesExportUserData)
    bpy.utils.unregister_class(FLIPFluidPreferencesImportUserData)
    bpy.utils.unregister_class(FLIPFluidPreferencesFindGPUDevices)

    bpy.utils.unregister_class(VersionDataTextEntry)
    bpy.utils.unregister_class(FlipFluidCheckForUpdates)
