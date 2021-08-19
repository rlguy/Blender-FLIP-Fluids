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

import bpy, os, re

from ..filesystem import filesystem_protection_layer as fpl
from ..utils import version_compatibility_utils as vcu

from bpy.props import (
        StringProperty,
        )


class FlipFluidFreeCache(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.free_cache"
    bl_label = "Free Cache"
    bl_description = "Delete Simulation Cache Files"


    def clear_cache(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        clear_export = dprops.cache.clear_cache_directory_export
        clear_logs = dprops.cache.clear_cache_directory_logs

        fpl.clear_cache_directory(cache_directory, 
            clear_export=clear_export, 
            clear_logs=clear_logs, 
            remove_directory=True
            )


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        cache_path = dprops.cache.get_cache_abspath()
        if not os.path.isdir(cache_path):
            self.report({"ERROR"}, "Current cache directory does not exist")
            return {'CANCELLED'}

        self.clear_cache(context)
        self.report({"INFO"}, "Successfully cleared cache directory '" + cache_path  + "'.")

        dprops.stats.refresh_stats()
        dprops.bake.check_autosave()
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidFreeUnheldCacheFiles(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.free_unheld_cache_files"
    bl_label = "Free Unheld Cache Files"
    bl_description = "Delete Unheld Simulation Cache Files"


    def delete_unheld_cache_directory(self, directory, extension):
        if not os.path.isdir(directory):
            return

        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        rprops = dprops.render
        hold_frame = rprops.hold_frame_number
        
        for f in os.listdir(directory):
            if f.endswith(extension):
                startidx = -(len(extension) + 6)
                endidx = startidx + 6
                numstr = f[startidx:endidx]
                if not numstr.isdigit():
                    continue

                frameno = int(numstr)
                if frameno == hold_frame:
                    continue

                filepath = os.path.join(directory, f)
                fpl.delete_file(filepath)


    def clear_unheld_cache_files(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_dir = dprops.cache.get_cache_abspath()

        bakefiles_dir = os.path.join(cache_dir, "bakefiles")
        self.delete_unheld_cache_directory(bakefiles_dir, ".bbox")
        self.delete_unheld_cache_directory(bakefiles_dir, ".bobj")
        self.delete_unheld_cache_directory(bakefiles_dir, ".wwp")
        self.delete_unheld_cache_directory(bakefiles_dir, ".fpd")
        self.delete_unheld_cache_directory(bakefiles_dir, ".ffd")


    def count_directory_bytes(self, dirpath):
        byte_count = 0
        for dirpath, dirnames, filenames in os.walk(dirpath):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                byte_count += os.path.getsize(fp)
        return byte_count


    def update_cache_bytes(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        bakefiles_directory = os.path.join(cache_directory, "bakefiles")
        dprops.stats.cache_bytes.set(self.count_directory_bytes(bakefiles_directory))


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        cache_path = dprops.cache.get_cache_abspath()
        if not os.path.isdir(cache_path):
            self.report({"ERROR"}, "Current cache directory does not exist")
            return {'CANCELLED'}

        self.clear_unheld_cache_files(context)
        self.report({"INFO"}, "Successfully cleared unheld cache files")

        self.update_cache_bytes(context)

        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)



class FlipFluidMoveCache(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.move_cache"
    bl_label = "Move Cache"
    bl_description = "Move Simulation Cache Files"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        src_dir = dprops.cache.get_cache_abspath()
        dst_dir = dprops.cache.get_abspath(dprops.cache.move_cache_directory)

        try:
            if not os.path.exists(src_dir):
                os.makedirs(src_dir)
        except Exception as e:
            self.report({"ERROR"}, "Error creating cache directory: " + str(e))
            return {'CANCELLED'}

        try:
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
        except Exception as e:
            self.report({"ERROR"}, "Error creating destination directory: " + str(e))
            return {'CANCELLED'}

        if not os.access(dst_dir, os.W_OK):
            self.report({"ERROR"}, "Unable to write to destination directory")
            return {'CANCELLED'}

        try:
            shutil.move(src_dir, dst_dir)
        except Exception as e:
            self.report({"ERROR"}, "Error moving cache directory: " + str(e))
            return {'CANCELLED'}

        base_dir = os.path.basename(src_dir)
        new_cache_path = os.path.join(dst_dir, base_dir)
        self.report({"INFO"}, "Successfully moved '" + src_dir  + "' to '" + new_cache_path + "'.")

        dprops.cache.cache_directory = new_cache_path
        dprops.stats.refresh_stats()

        return {'FINISHED'}


class FlipFluidRenameCache(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.rename_cache"
    bl_label = "Rename Cache"
    bl_description = "Rename Simulation Cache Directory"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        src_dir = dprops.cache.get_cache_abspath()
        parent_dir = os.path.dirname(src_dir)
        rename_dir = dprops.cache.rename_cache_directory
        new_cache_path = os.path.join(parent_dir, rename_dir)

        try:
            if not os.path.exists(src_dir):
                os.makedirs(src_dir)
        except Exception as e:
            self.report({"ERROR"}, "Error creating cache directory: " + str(e))
            return {'CANCELLED'}
            
        if os.path.exists(new_cache_path):
            self.report({"ERROR"}, "Renamed cache directory already exists")
            return {'CANCELLED'}
        if not os.access(os.path.dirname(new_cache_path), os.W_OK):
            dst_dir = os.path.dirname(new_cache_path)
            self.report({"ERROR"}, "Unable to write to destination directory: " + dst_dir)
            return {'CANCELLED'}

        try:
            os.rename(src_dir, new_cache_path)
        except Exception as e:
            self.report({"ERROR"}, "Error renaming cache directory: " + str(e))
            return {'CANCELLED'}

        self.report({"INFO"}, "Successfully renamed '" + src_dir  + "' to '" + new_cache_path + "'.")

        is_relative = dprops.cache.cache_directory.startswith("//")
        dprops.cache.cache_directory = new_cache_path
        if is_relative:
            bpy.ops.flip_fluid_operators.relative_cache_directory("INVOKE_DEFAULT")

        dprops.stats.refresh_stats()

        return {'FINISHED'}


class FlipFluidCopyCache(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.copy_cache"
    bl_label = "Copy Cache"
    bl_description = "Copy Simulation Cache Directory"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        src_dir = dprops.cache.get_cache_abspath()
        dst_dir = dprops.cache.get_abspath(dprops.cache.copy_cache_directory)

        try:
            if not os.path.exists(src_dir):
                os.makedirs(src_dir)
        except Exception as e:
            self.report({"ERROR"}, "Error creating cache directory: " + str(e))
            return {'CANCELLED'}

        try:
            shutil.copytree(src_dir, dst_dir)
        except Exception as e:
            self.report({"ERROR"}, "Error copying cache directory: " + str(e))
            return {'CANCELLED'}

        self.report({"INFO"}, "Successfully copied '" + src_dir  + "' to '" + dst_dir + "'.")

        return {'FINISHED'}


class FlipFluidRelativeCacheDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.relative_cache_directory"
    bl_label = "Make Relative"
    bl_description = "Convert to a filepath relative to the Blend file"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        blend_filepath = bpy.path.abspath("//")
        if not blend_filepath:
            self.report({"ERROR"}, "Cannot make path relative to unsaved Blend file")
            return {'CANCELLED'}

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        cache_directory = dprops.cache.get_cache_abspath()

        try:
            relpath = os.path.relpath(cache_directory, blend_filepath)
        except ValueError:
            self.report({"ERROR"}, "Relative path requires Blend file and cache directory to be on the same drive")
            return {'CANCELLED'}

        relprefix = "//"
        dprops.cache.cache_directory = relprefix + relpath

        return {'FINISHED'}


class FlipFluidAbsoluteCacheDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.absolute_cache_directory"
    bl_label = "Make Absolute"
    bl_description = "Convert to an absolute filepath location"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        dprops.cache.cache_directory = dprops.cache.get_cache_abspath()
        return {'FINISHED'}


class FlipFluidMatchFilenameCacheDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.match_filename_cache_directory"
    bl_label = "Match Filename"
    bl_description = ("Set the cache directory name to correspond to the .blend filename." +
        " Note: this will not rename an existing cache directory")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        blend_filepath = bpy.path.abspath("//")
        if not blend_filepath:
            self.report({"ERROR"}, "The Blend file must be saved to use this operator")
            return {'CANCELLED'}

        cache_directory = dprops.cache.cache_directory
        relprefix = "//"
        is_relative = cache_directory.startswith(relprefix)

        abspath = dprops.cache.get_cache_abspath()
        parent_path = os.path.dirname(abspath)

        new_directory_name = os.path.basename(bpy.data.filepath)
        new_directory_name = os.path.splitext(new_directory_name)[0]
        new_directory_name += "_flip_fluid_cache"

        dprops.cache.cache_directory = os.path.join(parent_path, new_directory_name)
        if is_relative:
            bpy.ops.flip_fluid_operators.relative_cache_directory()

        return {'FINISHED'}


class FlipFluidIncreaseDecreaseCacheDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.increment_decrease_cache_directory"
    bl_label = "Increase/Decrease Cache Directory"
    bl_description = ("Increase or decrease a numbered suffix on the cache directory." + 
        " Note: this will not rename an existing cache directory")

    increment_mode = StringProperty(default="INCREASE")
    exec(vcu.convert_attribute_to_28("increment_mode"))


    @classmethod
    def poll(cls, context):
        return True


    def get_trailing_number(self, s):
        m = re.search(r'\d+$', s)
        return int(m.group()) if m else None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        cache_directory = dprops.cache.cache_directory
        relprefix = "//"
        is_relative = cache_directory.startswith(relprefix)

        abspath = dprops.cache.get_cache_abspath()
        parent_path = os.path.dirname(abspath)
        basename = os.path.basename(abspath)

        suffix_number = self.get_trailing_number(basename)
        if suffix_number:
            basename = basename[:-len(str(suffix_number))]

        if self.increment_mode == 'INCREASE':
            if not suffix_number:
                suffix_number = 0
            suffix_number += 1
            new_basename = basename + str(suffix_number)
        else:
            if not suffix_number:
                return {'FINISHED'}
            if suffix_number <= 1:
                suffix_string = ""
            else:
                suffix_string = str(suffix_number - 1)
            new_basename = basename + suffix_string

        dprops.cache.cache_directory = os.path.join(parent_path, new_basename)
        if is_relative:
            bpy.ops.flip_fluid_operators.relative_cache_directory()

        return {'FINISHED'}


class FlipFluidRelativeLinkedGeometryDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.relative_linked_geometry_directory"
    bl_label = "Make Relative"
    bl_description = "Convert to a filepath relative to the Blend file"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        blend_filepath = bpy.path.abspath("//")
        if not blend_filepath:
            self.report({"ERROR"}, "Cannot make path relative to unsaved Blend file")
            return {'CANCELLED'}

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        linked_directory = dprops.cache.get_linked_geometry_abspath()
        if not linked_directory:
            self.report({"ERROR"}, "Linked geometry directory is not set. Set to an existing cache directory and try again.")
            return {'CANCELLED'}

        try:
            relpath = os.path.relpath(linked_directory, blend_filepath)
        except ValueError:
            self.report({"ERROR"}, "Relative path requires Blend file and cache directory to be on the same drive")
            return {'CANCELLED'}

        relprefix = "//"
        dprops.cache.linked_geometry_directory = relprefix + relpath

        return {'FINISHED'}


class FlipFluidAbsoluteLinkedGeometryDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.absolute_linked_geometry_directory"
    bl_label = "Make Absolute"
    bl_description = "Convert to an absolute filepath location"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        linked_directory = dprops.cache.get_linked_geometry_abspath()
        if not linked_directory:
            self.report({"ERROR"}, "Linked geometry directory is not set. Set to an existing cache directory and try again.")
            return {'CANCELLED'}

        dprops.cache.linked_geometry_directory = linked_directory
        return {'FINISHED'}


class FlipFluidClearLinkedGeometryDirectory(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.clear_linked_geometry_directory"
    bl_label = "Clear"
    bl_description = "Clear the linked geometry directory field. No files will be deleted"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        dprops.cache.linked_geometry_directory = ""
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidFreeCache)
    bpy.utils.register_class(FlipFluidFreeUnheldCacheFiles)

    # The move, rename, and copy cache operations should not be performed
    # in Blender and are removed from the UI. There is a potential for Blender 
    # to crash, which could lead to loss of data. It is best to perform these 
    # operations through the OS filesystem which is cabable of handling failures.
    """
    bpy.utils.register_class(FlipFluidMoveCache)
    bpy.utils.register_class(FlipFluidRenameCache)
    bpy.utils.register_class(FlipFluidCopyCache)
    """

    bpy.utils.register_class(FlipFluidRelativeCacheDirectory)
    bpy.utils.register_class(FlipFluidAbsoluteCacheDirectory)
    bpy.utils.register_class(FlipFluidMatchFilenameCacheDirectory)
    bpy.utils.register_class(FlipFluidIncreaseDecreaseCacheDirectory)
    bpy.utils.register_class(FlipFluidRelativeLinkedGeometryDirectory)
    bpy.utils.register_class(FlipFluidAbsoluteLinkedGeometryDirectory)
    bpy.utils.register_class(FlipFluidClearLinkedGeometryDirectory)


def unregister():
    bpy.utils.unregister_class(FlipFluidFreeCache)
    bpy.utils.unregister_class(FlipFluidFreeUnheldCacheFiles)

    """
    bpy.utils.unregister_class(FlipFluidMoveCache)
    bpy.utils.unregister_class(FlipFluidRenameCache)
    bpy.utils.unregister_class(FlipFluidCopyCache)
    """

    bpy.utils.unregister_class(FlipFluidRelativeCacheDirectory)
    bpy.utils.unregister_class(FlipFluidAbsoluteCacheDirectory)
    bpy.utils.unregister_class(FlipFluidMatchFilenameCacheDirectory)
    bpy.utils.unregister_class(FlipFluidIncreaseDecreaseCacheDirectory)
    bpy.utils.unregister_class(FlipFluidRelativeLinkedGeometryDirectory)
    bpy.utils.unregister_class(FlipFluidAbsoluteLinkedGeometryDirectory)
    bpy.utils.unregister_class(FlipFluidClearLinkedGeometryDirectory)
