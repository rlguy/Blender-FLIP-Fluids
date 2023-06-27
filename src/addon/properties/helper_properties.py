# Blender FLIP Fluids Add-on
# Copyright (C) 2022 Ryan L. Guy
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

import bpy
from bpy.props import (
        IntProperty,
        FloatProperty,
        StringProperty,
        BoolProperty,
        PointerProperty,
        EnumProperty
        )

from . import preset_properties
from .. import types
from ..utils import version_compatibility_utils as vcu

DISABLE_FRAME_CHANGE_POST_HANDLER = False


class FlipFluidHelperProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    enable_auto_frame_load = BoolProperty(
            name="Auto-Load Baked Frames",
            description="Automatically load frames as they finish baking",
            default=False,
            update=lambda self, context: self._update_enable_auto_frame_load_cmd(context),
            ); exec(conv("enable_auto_frame_load"))
    enable_auto_frame_load_cmd = BoolProperty(
            name="Sync With CMD Bake",
            description="Automatically load frames as they finish baking when running a command"
                " line bake. Note: this feature may decrease Blender performance and responsiveness"
                " when a CMD bake is not running. If this is an issue, it is recommended to disable"
                " this option when a CMD bake is not running",
            default=False,
            update=lambda self, context: self._update_enable_auto_frame_load_cmd(context),
            ); exec(conv("enable_auto_frame_load_cmd"))
    playback_frame_offset = IntProperty(
            name="Frame Offset",
            description="Frame offset for simulation playback",
            default=0,
            options={'HIDDEN'},
            ); exec(conv("playback_frame_offset"))

    cmd_launch_render_after_bake = BoolProperty(
            name="Render After Bake",
            description="After the command line bake process is finished, begin rendering animation",
            default=False,
            ); exec(conv("cmd_launch_render_after_bake"))
    cmd_launch_render_mode = EnumProperty(
            name="CMD Render Mode",
            description="Frame range to use for baking the simulation",
            items=types.cmd_render_mode,
            default='CMD_RENDER_MODE_NORMAL',
            options={'HIDDEN'},
            ); exec(conv("cmd_launch_render_mode"))
    cmd_open_image_after_render = BoolProperty(
            name="Open Image After Render",
            description="After the command line render process is finished, open the image in your default OS image program",
            default=True,
            ); exec(conv("cmd_open_image_after_render"))
    cmd_close_window_after_render = BoolProperty(
            name="Close CMD Window After Render",
            description="After the command line render process is finished, open the image in your default OS image program",
            default=False,
            ); exec(conv("cmd_close_window_after_render"))

    unsaved_blend_file_tooltip = BoolProperty(
            name="Unsaved Blend File Tooltip", 
            description="This is currently an unsaved .blend file. We recommend saving your file before baking a"
                " simulation so you do not accidentally lose your simulation progress or settings", 
            default=True,
            ); exec(conv("unsaved_blend_file_tooltip"))

    flip_fluids_remesh_skip_hide_render_objects = BoolProperty(
            name="Skip Hidden Render Objects",
            description="Skip remeshing objects in the collection that are hidden from render (outliner camera icon)",
            default=False,
            ); exec(conv("flip_fluids_remesh_skip_hide_render_objects"))
    flip_fluids_remesh_apply_object_modifiers = BoolProperty(
            name="Apply Object Modifiers",
            description="Automatically apply modifiers to objects in collection. If disabled, objects with modifiers will"
                " need to have modifiers applied manually or excluded from the viewport (disable outliner monitor icon)"
                " before proceeding with the remesh process. Modifiers may not be applied in the intended order and objects"
                " with complex modifier dependencies may need to be applied manually for accuracy",
            default=True,
            ); exec(conv("flip_fluids_remesh_apply_object_modifiers"))
    flip_fluids_remesh_convert_objects_to_mesh = BoolProperty(
            name="Convert Objects to Mesh",
            description="Automatically convert non-mesh type objects in the collection to a mesh type if applicable. If an object cannot"
                " be converted to a mesh (empties, armatures, etc), the object will be skipped from the remeshing process."
                " If disabled, non-mesh type objects will need to be manually converted to a mesh or excluded from the viewport"
                " (disable outliner monitor icon) before proceeding with the remesh process",
            default=True,
            ); exec(conv("flip_fluids_remesh_convert_objects_to_mesh"))
    update_object_speed_data_on_frame_change = BoolProperty(
            name="Update on frame change",
            description="Update the object speed measurement for the active object after changing a frame. Not recommended"
            " to leave this option enabled when not in use as this could slow down Blender when measuring complex or high poly geometry",
            default=False,
            ); exec(conv("update_object_speed_data_on_frame_change"))
    measure_object_speed_units_mode = EnumProperty(
            name="Measurement Units",
            description="Display speed in metric or imperial units",
            items=types.measurement_units_mode,
            default='MEASUREMENT_UNITS_MODE_METRIC',
            options={'HIDDEN'},
            ); exec(conv("measure_object_speed_units_mode"))

    is_auto_frame_load_cmd_operator_running = BoolProperty(default=False); exec(conv("is_auto_frame_load_cmd_operator_running"))

    # Used in Helper Operators > FlipFluidMeasureObjectSpeed operator
    is_translation_data_available = BoolProperty(default=False); exec(conv("is_translation_data_available"))
    min_vertex_translation = FloatProperty(default=0.0); exec(conv("min_vertex_translation"))
    max_vertex_translation = FloatProperty(default=0.0); exec(conv("max_vertex_translation"))
    avg_vertex_translation = FloatProperty(default=0.0); exec(conv("avg_vertex_translation"))
    center_translation = FloatProperty(default=0.0); exec(conv("center_translation"))
    translation_data_object_name = StringProperty(default="Name Not Available"); exec(conv("translation_data_object_name"))
    translation_data_object_vertices = IntProperty(default=-1); exec(conv("translation_data_object_vertices"))
    translation_data_object_frame = IntProperty(default=-1); exec(conv("translation_data_object_frame"))
    translation_data_object_compute_time = IntProperty(default=-1); exec(conv("translation_data_object_compute_time"))

    prepare_geometry_tools_expanded = BoolProperty(default=False); exec(conv("prepare_geometry_tools_expanded"))
    bake_simulation_expanded = BoolProperty(default=True); exec(conv("bake_simulation_expanded"))
    add_remove_objects_expanded = BoolProperty(default=True); exec(conv("add_remove_objects_expanded"))
    outliner_organization_expanded = BoolProperty(default=False); exec(conv("outliner_organization_expanded"))
    quick_select_expanded = BoolProperty(default=False); exec(conv("quick_select_expanded"))
    command_line_tools_expanded = BoolProperty(default=True); exec(conv("command_line_tools_expanded"))
    geometry_node_tools_expanded = BoolProperty(default=False); exec(conv("geometry_node_tools_expanded"))
    object_speed_measurement_tools_expanded = BoolProperty(default=False); exec(conv("object_speed_measurement_tools_expanded"))
    beginner_tools_expanded = BoolProperty(default=False); exec(conv("beginner_tools_expanded"))

    quick_viewport_display_expanded = BoolProperty(default=True); exec(conv("quick_viewport_display_expanded"))
    simulation_playback_expanded = BoolProperty(default=False); exec(conv("simulation_playback_expanded"))
    render_tools_expanded = BoolProperty(default=False); exec(conv("render_tools_expanded"))


    @classmethod
    def register(cls):
        bpy.types.Scene.flip_fluid_helper = PointerProperty(
                name="Flip Fluid Helper Properties",
                description="",
                type=cls,
                )


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.flip_fluid_helper


    def load_post(self):
        self.is_auto_frame_load_cmd_operator_running = False
        if self.is_auto_frame_load_cmd_enabled():
            bpy.ops.flip_fluid_operators.auto_load_baked_frames_cmd('INVOKE_DEFAULT')

    def frame_change_post(self, scene, depsgraph=None):
        if self.update_object_speed_data_on_frame_change:
            try:
                if bpy.ops.flip_fluid_operators.measure_object_speed.poll():
                    print("Measure Object Speed: Update on frame change option is enabled.")
                    bpy.ops.flip_fluid_operators.measure_object_speed('INVOKE_DEFAULT')
                else:
                    bpy.ops.flip_fluid_operators.clear_measure_object_speed('INVOKE_DEFAULT')
            except:
                pass


    def get_addon_preferences(self):
        return vcu.get_addon_preferences()


    def frame_complete_callback(self):
        prefs = self.get_addon_preferences()
        if prefs.enable_helper and self.enable_auto_frame_load:
            bpy.ops.flip_fluid_operators.helper_load_last_frame()


    def is_auto_frame_load_cmd_enabled(self):
        return self.enable_auto_frame_load and self.enable_auto_frame_load_cmd


    def _update_enable_auto_frame_load_cmd(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        is_auto_load_cmd_enabled = self.is_auto_frame_load_cmd_enabled()
        if is_auto_load_cmd_enabled and not self.is_auto_frame_load_cmd_operator_running:
            bpy.ops.flip_fluid_operators.auto_load_baked_frames_cmd('INVOKE_DEFAULT')


def load_post():
    bpy.context.scene.flip_fluid_helper.load_post()


def frame_change_post(scene, depsgraph=None):
    global DISABLE_FRAME_CHANGE_POST_HANDLER
    if DISABLE_FRAME_CHANGE_POST_HANDLER:
        return
    bpy.context.scene.flip_fluid_helper.frame_change_post(scene, depsgraph)


def register():
    bpy.utils.register_class(FlipFluidHelperProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperProperties)
