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

import bpy, os, shutil
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import exit_handler
from ..utils import version_compatibility_utils as vcu

class DomainCacheProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    temp_directory = vcu.get_blender_preferences_temporary_directory()
    default_cache_directory_str = os.path.join(temp_directory, "untitled_flip_fluid_cache")
    
    cache_directory = StringProperty(
            name="",
            description="Simulation files will be saved to this directory."
                " It is recommended to save your .blend file before beginning a simulation",
            default=default_cache_directory_str, 
            subtype='DIR_PATH',
            update=lambda self, context: self._update_cache_directory(context),
            ); exec(conv("cache_directory"))
    default_cache_directory = StringProperty(
            default=default_cache_directory_str, 
            subtype='DIR_PATH',
            ); exec(conv("default_cache_directory"))
    move_cache_directory = StringProperty(
            name="",
            description="Cache directory will be moved to this location",
            default=temp_directory, 
            subtype='DIR_PATH',
            ); exec(conv("move_cache_directory"))
    rename_cache_directory = StringProperty(
            name="",
            description="Cache directory will be renamed to this value",
            default="untitled_flip_fluid_cache",
            ); exec(conv("rename_cache_directory"))
    copy_cache_directory = StringProperty(
            name="",
            description="Cache directory contents will be copied to this location",
            default=default_cache_directory_str, 
            subtype='DIR_PATH',
            ); exec(conv("copy_cache_directory"))
    clear_cache_directory_logs = BoolProperty(
            name="Clear log files",
            description="Also delete log files when freeing cache directory",
            default=False,
            ); exec(conv("clear_cache_directory_logs"))
    clear_cache_directory_export = BoolProperty(
            name="Clear export files",
            description="Also delete exported settings and objects when freeing cache directory",
            default=False,
            ); exec(conv("clear_cache_directory_export"))
    logfile_name = StringProperty(
            default=os.path.join(temp_directory, "flip_fluid_log.txt"), 
            subtype='FILE_NAME',
            ); exec(conv("logfile_name"))
    linked_geometry_directory = StringProperty(
            name="",
            description="select an existing cache directory. Link exported geometry data from another cache directory."
                " Use if you want to re-use exported geometry that is located in another cache. Useful if you have a"
                " lot of geometry in your scene that you do not want to re-export",
            default="", 
            subtype='DIR_PATH',
            ); exec(conv("linked_geometry_directory"))

    is_cache_directory_set = BoolProperty(default=False); exec(conv("is_cache_directory_set"))


    def register_preset_properties(self, registry, path):
        pass


    def initialize(self):
        self._check_cache_directory()
        

    def get_abspath(self, path_prop):
        relprefix = "//"
        if path_prop.startswith(relprefix):
            path_prop = path_prop[len(relprefix):]
            blend_directory = os.path.dirname(bpy.data.filepath)
            path = os.path.join(blend_directory, path_prop)
            return os.path.normpath(path)
        return os.path.normpath(path_prop)


    def get_cache_abspath(self):
        return self.get_abspath(self.cache_directory)


    def get_linked_geometry_abspath(self):
        if not self.linked_geometry_directory:
            return None
        return self.get_abspath(self.linked_geometry_directory)


    def is_linked_geometry_directory(self):
        linked_geometry_directory = self.get_linked_geometry_abspath()
        if linked_geometry_directory is None:
            return False

        if not os.path.isdir(linked_geometry_directory):
            return False

        linked_export_directory = os.path.join(linked_geometry_directory, "export")
        if os.path.isdir(linked_export_directory):
            return True
        else:
            incorrect_filepath_test = os.path.join(linked_geometry_directory, database_filename)
            if os.path.isfile(incorrect_filepath_test):
                return True
            else:
                return False


    def get_geometry_database_abspath(self, export_directory=None, database_filename=None):
        if export_directory is None:
            export_directory = os.path.join(self.get_cache_abspath(), "export")
        if database_filename is None:
            database_filename = "export_data.sqlite3"

        default_filepath = os.path.join(export_directory, database_filename)

        linked_geometry_directory = self.get_linked_geometry_abspath()
        if linked_geometry_directory is None:
            return default_filepath

        if not os.path.isdir(linked_geometry_directory):
            return default_filepath

        linked_export_directory = os.path.join(linked_geometry_directory, "export")
        if os.path.isdir(linked_export_directory):
            return os.path.join(linked_export_directory, database_filename)
        else:
            incorrect_filepath_test = os.path.join(linked_geometry_directory, database_filename)
            if os.path.isfile(incorrect_filepath_test):
                return incorrect_filepath_test
            else:
                return default_filepath


    def mark_cache_directory_set(self):
        self.is_cache_directory_set = True


    def load_post(self):
        self._check_cache_directory()


    def save_post(self):
        self._check_cache_directory()
        

    def _update_cache_directory(self, context):
        self.is_cache_directory_set = True
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        relprefix = "//"
        if self.cache_directory == "" or self.cache_directory == relprefix:
            # Don't want the user to set an empty path
            if bpy.data.filepath:
                base = os.path.basename(bpy.data.filepath)
                save_file = os.path.splitext(base)[0]
                cache_folder_parent = os.path.dirname(bpy.data.filepath)

                cache_folder = save_file + "_flip_fluid_cache"
                cache_path = os.path.join(cache_folder_parent, cache_folder)
                relpath = os.path.relpath(cache_path, cache_folder_parent)

                default_cache_directory_str = relprefix + relpath
            else:
                temp_directory = vcu.get_blender_preferences_temporary_directory()
                default_cache_directory_str = os.path.join(temp_directory, "untitled_flip_fluid_cache")
            self["cache_directory"] = default_cache_directory_str

        dprops.stats.refresh_stats()
        dprops.bake.check_autosave()
        exit_handler.set_cache_directory(self.get_cache_abspath())


    def _check_cache_directory(self):
        if self.is_cache_directory_set:
            return

        base = os.path.basename(bpy.data.filepath)
        save_file = os.path.splitext(base)[0]
        if not base or not save_file:
            directory = self.default_cache_directory
            if os.path.exists(directory):
                for i in range(1, 1000):
                    test_directory = directory + str(i)
                    if not os.path.exists(test_directory):
                        directory = test_directory
                        break
            self.cache_directory = directory
            self.is_cache_directory_set = False
            return

        cache_folder_parent = os.path.dirname(bpy.data.filepath)
        cache_folder = save_file + "_flip_fluid_cache"
        cache_path = os.path.join(cache_folder_parent, cache_folder)
        relpath = os.path.relpath(cache_path, cache_folder_parent)

        relprefix = "//"
        self.cache_directory = relprefix + relpath
        self.is_cache_directory_set = True


def register():
    bpy.utils.register_class(DomainCacheProperties)


def unregister():
    bpy.utils.unregister_class(DomainCacheProperties)