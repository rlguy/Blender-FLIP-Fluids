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

import bpy, os, shutil
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import global_vars

class DomainCacheProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        temp_directory = bpy.context.user_preferences.filepaths.temporary_directory
        default_cache_directory = os.path.join(temp_directory, "untitled_flip_fluid_cache")
        cls.cache_directory = StringProperty(
                name="",
                description="Simulation files will be saved to this directory",
                default=default_cache_directory, 
                subtype='DIR_PATH',
                update=lambda self, context: self._update_cache_directory(context),
                )
        cls.default_cache_directory = StringProperty(
                default=default_cache_directory, 
                subtype='DIR_PATH',
                )
        cls.move_cache_directory = StringProperty(
                name="",
                description="Cache directory will be moved to this location",
                default=temp_directory, 
                subtype='DIR_PATH',
                )
        cls.rename_cache_directory = StringProperty(
                name="",
                description="Cache directory will be renamed to this value",
                default="untitled_flip_fluid_cache",
                )
        cls.copy_cache_directory = StringProperty(
                name="",
                description="Cache directory contents will be copied to this location",
                default=default_cache_directory, 
                subtype='DIR_PATH',
                )
        cls.clear_cache_directory_logs = BoolProperty(
                name="Clear log files",
                description="Also delete log files when freeing cache directory",
                default=False,
                )
        cls.logfile_name = StringProperty(
                default=os.path.join(temp_directory, "flip_fluid_log.txt"), 
                subtype='FILE_NAME',
                )

        cls.is_cache_directory_set = BoolProperty(default=False)


    @classmethod
    def unregister(cls):
        pass


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


    def mark_cache_directory_set(self):
        self.is_cache_directory_set = True


    def load_pre(self):
        self._delete_unsaved_cache_directory()


    def load_post(self):
        self._check_cache_directory()


    def save_post(self):
        self._check_cache_directory()
        

    def _update_cache_directory(self, context):
        self.is_cache_directory_set = True
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        dprops.stats.refresh_stats()
        dprops.bake.check_autosave()
        global_vars.CACHE_DIRECTORY = self.get_cache_abspath()


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


    def _delete_unsaved_cache_directory(self):
        base = os.path.basename(bpy.data.filepath)
        save_file = os.path.splitext(base)[0]
        if not base or not save_file:
            cache_directory = self.get_cache_abspath()
            if os.path.exists(cache_directory):
                shutil.rmtree(cache_directory, True)



def register():
    bpy.utils.register_class(DomainCacheProperties)


def unregister():
    bpy.utils.unregister_class(DomainCacheProperties)