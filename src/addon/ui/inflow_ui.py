# Blender FLIP Fluid Add-on
# Copyright (C) 2019 Ryan L. Guy
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
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        column = self.layout.column()
        column.prop(obj_props, "object_type")

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
        else:
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
            row = column.row(align=True)
            row.prop(inflow_props, "inflow_mesh_type", expand=True)
            column = box.column(align=True)
            column.prop(inflow_props, "constrain_fluid_velocity")

        column = self.layout.column()
        column.separator()
        split = column.split()
        column_left = split.column()
        column_left.prop(inflow_props, "export_animated_mesh")
        column_right = split.column()

        if show_advanced:
            column_right.enabled = inflow_props.export_animated_mesh
            column_right.prop(inflow_props, "skip_animated_mesh_reexport")
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_InflowTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_InflowTypePanel)
