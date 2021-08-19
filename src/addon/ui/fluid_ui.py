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

import bpy

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_FluidTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"


    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == 'TYPE_FLUID'


    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        fluid_props = obj_props.fluid
        dprops = context.scene.flip_fluid.get_domain_properties()
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        column = self.layout.column()
        column.prop(obj_props, "object_type")
        column.separator()

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Fluid Object Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Fluid-Object-Settings"
            column.operator(
                "wm.url_open", 
                text="Fluid objects must have manifold/watertight geometry", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Manifold-Meshes"

        if show_advanced:
            column.label(text="Trigger:")
            row = column.row(align= True)
            row.prop(fluid_props, "frame_offset_type", text = "")
            if fluid_props.frame_offset_type == 'OFFSET_TYPE_FRAME':
                row.prop(fluid_props, "frame_offset")
            elif fluid_props.frame_offset_type == 'OFFSET_TYPE_TIMELINE':
                row.prop(fluid_props, "timeline_offset")
            self.layout.separator()

        box = self.layout.box()
        box.label(text="Fluid Velocity Mode:")
        row = box.row(align=True)
        row.prop(fluid_props, "fluid_velocity_mode", expand=True)

        if fluid_props.fluid_velocity_mode == 'FLUID_VELOCITY_MANUAL':
            column = box.column(align=True)
            column.label(text="Fluid Velocity:")
            row = column.row(align=True)
            row.prop(fluid_props, "initial_velocity", text="")
            row = column.row(align=True)
            row.label(text="")
        elif fluid_props.fluid_velocity_mode == 'FLUID_VELOCITY_AXIS':
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.label(text="Fluid Speed:")
            column_left.prop(fluid_props, "initial_speed")
                
            column_right = split.column(align=True)
            column_right.label(text="Local Axis:")
            row = column_right.row(align=True)
            row.prop_enum(fluid_props, "fluid_axis_mode", 'LOCAL_AXIS_POS_X')
            row.prop_enum(fluid_props, "fluid_axis_mode", 'LOCAL_AXIS_POS_Y')
            row.prop_enum(fluid_props, "fluid_axis_mode", 'LOCAL_AXIS_POS_Z')
            row = column_right.row(align=True)
            row.prop_enum(fluid_props, "fluid_axis_mode", 'LOCAL_AXIS_NEG_X')
            row.prop_enum(fluid_props, "fluid_axis_mode", 'LOCAL_AXIS_NEG_Y')
            row.prop_enum(fluid_props, "fluid_axis_mode", 'LOCAL_AXIS_NEG_Z')

        elif fluid_props.fluid_velocity_mode == 'FLUID_VELOCITY_TARGET':
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.label(text="Fluid Speed:")
            column_left.prop(fluid_props, "initial_speed")

            target_collection = vcu.get_scene_collection()
            if vcu.is_blender_28():
                search_group = "all_objects"
            else:
                search_group = "objects"

            column_right = split.column(align=True)
            column_right.label(text="Target Object:")
            column_right.prop_search(fluid_props, "target_object", target_collection, search_group, text="")
            column_right.prop(fluid_props, "export_animated_target")

        if show_advanced:
            box.separator()
            column = box.column(align=True)
            split = vcu.ui_split(column, factor=0.66)
            column = split.column()
            column.prop(fluid_props, "append_object_velocity")
            column = split.column()
            column.enabled = fluid_props.append_object_velocity
            column.prop(fluid_props, "append_object_velocity_influence")


        if vcu.get_addon_preferences().enable_developer_tools:
            box = self.layout.box()
            box.label(text="Geometry Attributes:")
            column = box.column(align=True)
            if vcu.is_blender_293():
                show_color = dprops is not None and dprops.surface.enable_color_attribute
                column.enabled = show_color
                column.prop(fluid_props, "color")

                column.separator()
                show_source_id = dprops is not None and dprops.surface.enable_source_id_attribute
                column.enabled = show_source_id
                column.prop(fluid_props, "source_id")
            else:
                column.enabled = False
                column.label(text="Geometry attribute features are only available in", icon='ERROR')
                column.label(text="Blender 2.93 or later", icon='ERROR')

        if show_advanced:
            box = self.layout.box()
            box.label(text="Mesh Data Export:")
            column = box.column(align=True)
            column.prop(fluid_props, "export_animated_mesh")
            column.prop(fluid_props, "skip_reexport")
            column.separator()
            column = box.column(align=True)
            column.enabled = fluid_props.skip_reexport
            column.prop(fluid_props, "force_reexport_on_next_bake", toggle=True)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_FluidTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_FluidTypePanel)
