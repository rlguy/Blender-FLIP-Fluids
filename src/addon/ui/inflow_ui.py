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


class FLIPFLUID_PT_InflowTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"

    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == 'TYPE_INFLOW'


    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        inflow_props = obj_props.inflow
        dprops = context.scene.flip_fluid.get_domain_properties()
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Inflow Object Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Inflow-Object-Settings"
            column.operator(
                "wm.url_open", 
                text="How to use the Constrain Fluid Velocity option", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Inflow-Constrain-Fluid-Velocity-Additional-Notes"
            column.operator(
                "wm.url_open", 
                text="Inflow stops emitting fluid when submerged", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#inflow-will-not-fill-up-a-tank-when-submerged"
            column.operator(
                "wm.url_open", 
                text="Small inflow does not emit fluid", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#small-inflow-not-emitting-fluid-low-resolution-simulation"
            column.operator(
                "wm.url_open", 
                text="Inflow objects must have manifold/watertight geometry", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Manifold-Meshes"



        column = self.layout.column()
        column.prop(inflow_props, "is_enabled")

        if show_advanced:
            column.prop(inflow_props, "substep_emissions")

        column.separator()
        box = self.layout.box()
        box.label(text="Inflow Velocity Mode:")
        row = box.row(align=True)
        row.prop(inflow_props, "inflow_velocity_mode", expand=True)

        if inflow_props.inflow_velocity_mode == 'INFLOW_VELOCITY_MANUAL':
            column = box.column(align=True)
            column.label(text="Inflow Velocity:")
            row = column.row(align=True)
            row.prop(inflow_props, "inflow_velocity", text="")
            row = column.row(align=True)
            row.label(text="")
        elif inflow_props.inflow_velocity_mode == 'INFLOW_VELOCITY_AXIS':
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.label(text="Inflow Speed:")
            column_left.prop(inflow_props, "inflow_speed")
                
            column_right = split.column(align=True)
            column_right.label(text="Local Axis:")
            row = column_right.row(align=True)
            row.prop_enum(inflow_props, "inflow_axis_mode", 'LOCAL_AXIS_POS_X')
            row.prop_enum(inflow_props, "inflow_axis_mode", 'LOCAL_AXIS_POS_Y')
            row.prop_enum(inflow_props, "inflow_axis_mode", 'LOCAL_AXIS_POS_Z')
            row = column_right.row(align=True)
            row.prop_enum(inflow_props, "inflow_axis_mode", 'LOCAL_AXIS_NEG_X')
            row.prop_enum(inflow_props, "inflow_axis_mode", 'LOCAL_AXIS_NEG_Y')
            row.prop_enum(inflow_props, "inflow_axis_mode", 'LOCAL_AXIS_NEG_Z')
        elif inflow_props.inflow_velocity_mode == 'INFLOW_VELOCITY_TARGET':
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.label(text="Inflow Speed:")
            column_left.prop(inflow_props, "inflow_speed")

            target_collection = vcu.get_scene_collection()
            if vcu.is_blender_28():
                search_group = "all_objects"
            else:
                search_group = "objects"
                
            column_right = split.column(align=True)
            column_right.label(text="Target Object:")
            column_right.prop_search(inflow_props, "target_object", target_collection, search_group, text="")
            column_right.prop(inflow_props, "export_animated_target")

        if show_advanced:
            box.separator()
            column = box.column(align=True)
            split = vcu.ui_split(column, factor=0.60)
            column = split.column()
            column.prop(inflow_props, "append_object_velocity")
            column = split.column(align=True)
            column.enabled = inflow_props.append_object_velocity
            column.prop(inflow_props, "append_object_velocity_influence")
            column = box.column(align=True)
            column.prop(inflow_props, "constrain_fluid_velocity")

        if vcu.get_addon_preferences().enable_developer_tools:
            box = self.layout.box()
            box.label(text="Geometry Attributes:")
            column = box.column(align=True)
            if vcu.is_blender_293():
                show_color = dprops is not None and dprops.surface.enable_color_attribute
                column.enabled = show_color
                column.prop(inflow_props, "color")

                column.separator()
                show_source_id = dprops is not None and dprops.surface.enable_source_id_attribute
                column.enabled = show_source_id
                column.prop(inflow_props, "source_id")
            else:
                column.enabled = False
                column.label(text="Geometry attribute features are only available in", icon='ERROR')
                column.label(text="Blender 2.93 or later", icon='ERROR')

        box = self.layout.box()
        box.label(text="Mesh Data Export:")
        column = box.column(align=True)
        column.prop(inflow_props, "export_animated_mesh")
        if show_advanced:
            column.prop(inflow_props, "skip_reexport")
            column.separator()
            column = box.column(align=True)
            column.enabled = inflow_props.skip_reexport
            column.prop(inflow_props, "force_reexport_on_next_bake", toggle=True)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_InflowTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_InflowTypePanel)
