# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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

import bpy, os, string

from ..utils import version_compatibility_utils as vcu


class FlipFluidSupportPrintSystemInfo(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.print_system_info"
    bl_label = "Print System & Blend Info"
    bl_description = "Print system and Blend file info if saved into the file (requires domain)"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.debug.print_system_and_blend_info()
        return {'FINISHED'}


class FlipFluidSupportStandardizeBlendFile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.standardize_blend_file"
    bl_label = "Standardize Blend File"
    bl_description = "Set cache/render location relative, set simulation viewport to visible, set simulation viewport mesh display to final (requires domain)"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        print()
        
        original_cache_directory = dprops.cache.get_cache_abspath()
        bpy.ops.flip_fluid_operators.relative_cache_directory()
        bpy.ops.flip_fluid_operators.match_filename_cache_directory()
        new_cache_directory = dprops.cache.get_cache_abspath()
        if new_cache_directory != original_cache_directory:
            info_msg = "Changed cache directory <" + original_cache_directory + "> -> <" + new_cache_directory + ">"
            self.report({'INFO'}, info_msg)

        original_render_output = context.scene.render.filepath
        bpy.ops.flip_fluid_operators.relative_to_blend_render_output()
        new_render_output = context.scene.render.filepath
        if new_render_output != original_render_output:
            info_msg = "Changed render output <" + original_render_output + "> -> <" + new_render_output + ">"
            self.report({'INFO'}, info_msg)

        if not context.scene.flip_fluid.show_viewport:
            context.scene.flip_fluid.show_viewport = True
            self.report({'INFO'}, "Enabled simulation display in viewport")

        if not dprops.render.viewport_display == 'DISPLAY_FINAL':
            dprops.render.viewport_display = 'DISPLAY_FINAL'
            self.report({'INFO'}, "Set surface viewport display to Final")

        if not dprops.render.whitewater_viewport_display == 'DISPLAY_FINAL':
            dprops.render.whitewater_viewport_display = 'DISPLAY_FINAL'
            self.report({'INFO'}, "Set whitewater viewport display to Final")

        bpy.ops.wm.save_as_mainfile()

        return {'FINISHED'}


class FlipFluidSupportDisplayOverlayStats(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.display_overlay_stats"
    bl_label = "Display Overlay Stats"
    bl_description = "Enable overlays and show geometry overlay stats in the 3D viewports"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_overlays = True
                        space.overlay.show_stats = True

        return {'FINISHED'}


class FlipFluidSupportSelectSimulationObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.select_simulation_objects"
    bl_label = "Select All Simulation Objects"
    bl_description = "Select all objects related to the simulation. Notes: may not select all dependencies of a simulation object. Will not select hidden objects"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        for obj in bpy.data.objects:
            obj.select_set(False)

        for obj in bpy.data.objects:
            if not obj.flip_fluid.is_active:
                continue

            obj.select_set(True)

            if obj.flip_fluid.is_fluid():
                target = obj.flip_fluid.fluid.get_target_object()
                if target is not None:
                    target.select_set(True)

            if obj.flip_fluid.is_inflow():
                target = obj.flip_fluid.inflow.get_target_object()
                if target is not None:
                    target.select_set(True)

            if obj.flip_fluid.is_domain():
                meshing_volume = obj.flip_fluid.domain.surface.get_meshing_volume_object()
                if meshing_volume is not None:
                    meshing_volume.select_set(True)

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            mesh_cache_props = [
                dprops.mesh_cache.surface,
                dprops.mesh_cache.particles,
                dprops.mesh_cache.foam,
                dprops.mesh_cache.bubble,
                dprops.mesh_cache.spray,
                dprops.mesh_cache.dust,
                dprops.mesh_cache.obstacle,
            ]

            whitewater_cache_props = [
                dprops.mesh_cache.foam,
                dprops.mesh_cache.bubble,
                dprops.mesh_cache.spray,
                dprops.mesh_cache.dust,
            ]

            for obj_props in mesh_cache_props:
                obj = obj_props.get_cache_object()
                if obj is not None:
                    obj.select_set(True)

        domain_obj = context.scene.flip_fluid.get_domain_object()
        if domain_obj is not None:
            vcu.set_active_object(domain_obj)
        elif len(bpy.context.selected_objects) > 0:
            vcu.set_active_object(bpy.context.selected_objects[0])

        return {'FINISHED'}


class FlipFluidSupportSelectHiddenSimulationObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.select_hidden_simulation_objects"
    bl_label = "Show and Select Hidden Simulation Objects"
    bl_description = "Show and select all objects related to the simulation that are currently hidden. Notes: may not select all dependencies of a simulation object"


    @classmethod
    def poll(cls, context):
        return True


    def update_selection(self, obj):
        if obj.hide_viewport or obj.hide_get():
            obj.hide_viewport = False
            obj.hide_set(False)
            obj.select_set(True)


    def execute(self, context):
        for obj in bpy.data.objects:
            obj.select_set(False)

        for obj in bpy.data.objects:
            if not obj.flip_fluid.is_active:
                continue

            self.update_selection(obj)

            if obj.flip_fluid.is_fluid():
                target = obj.flip_fluid.fluid.get_target_object()
                if target is not None:
                    self.update_selection(target)

            if obj.flip_fluid.is_inflow():
                target = obj.flip_fluid.inflow.get_target_object()
                if target is not None:
                    self.update_selection(target)

            if obj.flip_fluid.is_domain():
                meshing_volume = obj.flip_fluid.domain.surface.get_meshing_volume_object()
                if meshing_volume is not None:
                    self.update_selection(meshing_volume)

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            mesh_cache_props = [
                dprops.mesh_cache.surface,
                dprops.mesh_cache.foam,
                dprops.mesh_cache.bubble,
                dprops.mesh_cache.spray,
                dprops.mesh_cache.dust,
                dprops.mesh_cache.obstacle,
            ]

            for obj_props in mesh_cache_props:
                obj = obj_props.get_cache_object()
                if obj is not None:
                    self.update_selection(obj)

        domain_obj = context.scene.flip_fluid.get_domain_object()
        if domain_obj is not None:
            vcu.set_active_object(domain_obj)
        elif len(bpy.context.selected_objects) > 0:
            vcu.set_active_object(bpy.context.selected_objects[0])

        return {'FINISHED'}


class FlipFluidSupportPrintHiddenSimulationObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.print_hidden_simulation_objects"
    bl_label = "Print Hidden Simulation Objects"
    bl_description = "Print objects related to the simulation that are currently hidden to the system console. Notes: may not select all dependencies of a simulation object"


    @classmethod
    def poll(cls, context):
        return True


    def update_print(self, obj):
        if obj.hide_viewport or obj.hide_get():
            print(obj)


    def execute(self, context):
        print()
        print("*** Hidden Simulation Objects ***")
        for obj in bpy.data.objects:
            if not obj.flip_fluid.is_active:
                continue

            self.update_print(obj)

            if obj.flip_fluid.is_fluid():
                target = obj.flip_fluid.fluid.get_target_object()
                if target is not None:
                    self.update_print(target)

            if obj.flip_fluid.is_inflow():
                target = obj.flip_fluid.inflow.get_target_object()
                if target is not None:
                    self.update_print(target)

            if obj.flip_fluid.is_domain():
                meshing_volume = obj.flip_fluid.domain.surface.get_meshing_volume_object()
                if meshing_volume is not None:
                    self.update_print(meshing_volume)

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            mesh_cache_props = [
                dprops.mesh_cache.surface,
                dprops.mesh_cache.foam,
                dprops.mesh_cache.bubble,
                dprops.mesh_cache.spray,
                dprops.mesh_cache.dust,
                dprops.mesh_cache.obstacle,
            ]

            for obj_props in mesh_cache_props:
                obj = obj_props.get_cache_object()
                if obj is not None:
                    self.update_print(obj)

        domain_obj = context.scene.flip_fluid.get_domain_object()
        if domain_obj is not None:
            vcu.set_active_object(domain_obj)
        elif len(bpy.context.selected_objects) > 0:
            vcu.set_active_object(bpy.context.selected_objects[0])

        return {'FINISHED'}


class FlipFluidSupportPrintInverseObstacles(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.print_inverse_obstacles"
    bl_label = "Print Inverse Obstacles"
    bl_description = "Print all obstacles with the 'Inverse' option enabled to the system console."


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        print()
        print("*** Inverse Obstacle Objects ***")
        obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()
        for obj in obstacle_objects:
            if not obj.flip_fluid.is_active:
                continue

            if obj.flip_fluid.obstacle.is_inversed:
                is_hidden = obj.hide_viewport or obj.hide_get()
                print(obj, "<hidden: " + str(is_hidden) + ">")

        return {'FINISHED'}


class FlipFluidSupportSelectInverseObstacles(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.select_inverse_obstacles"
    bl_label = "Select Inverse Obstacles"
    bl_description = "Select all obstacles with the 'Inverse' option enabled. Will not select hidden objects"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        for obj in bpy.data.objects:
            obj.select_set(False)

        obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()
        for obj in obstacle_objects:
            if not obj.flip_fluid.is_active:
                continue

            if obj.flip_fluid.obstacle.is_inversed:
                obj.select_set(True)

        if len(bpy.context.selected_objects) > 0:
            vcu.set_active_object(bpy.context.selected_objects[0])

        return {'FINISHED'}


class FlipFluidSupportInvertSelection(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.invert_selection"
    bl_label = "Invert Selection"
    bl_description = "Inverts selection of currently selected objects"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        bpy.ops.object.select_all(action='INVERT')
        return {'FINISHED'}


class FlipFluidSupportIncrementAndSaveFile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.increment_and_save_file"
    bl_label = "Increment Version and Save Blend File"
    bl_description = "Increment Blend filename version and save file"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        filepath = bpy.data.filepath
        basename = os.path.basename(filepath)
        extension = os.path.splitext(basename)[-1]
        filename = basename[:-len(extension)]
        base_filename = filename.rstrip(string.digits)
        parent_path = os.path.dirname(filepath)

        for i in range(1, 999):
            num_str = str(i).zfill(3)
            new_path = os.path.join(parent_path, base_filename + num_str + extension)
            if os.path.isfile(new_path):
                continue

            bpy.ops.wm.save_as_mainfile(filepath=new_path)
            break

        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidSupportPrintSystemInfo)
    bpy.utils.register_class(FlipFluidSupportStandardizeBlendFile)
    bpy.utils.register_class(FlipFluidSupportDisplayOverlayStats)
    bpy.utils.register_class(FlipFluidSupportSelectSimulationObjects)
    bpy.utils.register_class(FlipFluidSupportSelectHiddenSimulationObjects)
    bpy.utils.register_class(FlipFluidSupportPrintHiddenSimulationObjects)
    bpy.utils.register_class(FlipFluidSupportSelectInverseObstacles)
    bpy.utils.register_class(FlipFluidSupportPrintInverseObstacles)
    bpy.utils.register_class(FlipFluidSupportInvertSelection)
    bpy.utils.register_class(FlipFluidSupportIncrementAndSaveFile)


def unregister():
    bpy.utils.unregister_class(FlipFluidSupportPrintSystemInfo)
    bpy.utils.unregister_class(FlipFluidSupportStandardizeBlendFile)
    bpy.utils.unregister_class(FlipFluidSupportDisplayOverlayStats)
    bpy.utils.unregister_class(FlipFluidSupportSelectSimulationObjects)
    bpy.utils.unregister_class(FlipFluidSupportSelectHiddenSimulationObjects)
    bpy.utils.unregister_class(FlipFluidSupportPrintHiddenSimulationObjects)
    bpy.utils.unregister_class(FlipFluidSupportSelectInverseObstacles)
    bpy.utils.unregister_class(FlipFluidSupportPrintInverseObstacles)
    bpy.utils.unregister_class(FlipFluidSupportInvertSelection)
    bpy.utils.unregister_class(FlipFluidSupportIncrementAndSaveFile)
