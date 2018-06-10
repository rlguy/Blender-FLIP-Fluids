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

import bpy


class FlipFluidInflowTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"

    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == 'TYPE_INFLOW'


    def draw(self, context):
        obj = context.scene.objects.active
        obj_props = context.scene.objects.active.flip_fluid
        inflow_props = obj_props.inflow

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        column = self.layout.column()
        column.prop(inflow_props, "is_enabled")
        column.prop(inflow_props, "substep_emissions")
        column.separator()

        box = self.layout.box()
        box.label("Inflow Velocity Mode:")
        row = box.row(align=True)
        row.prop(inflow_props, "inflow_velocity_mode", expand=True)

        if inflow_props.inflow_velocity_mode == 'INFLOW_VELOCITY_MANUAL':
            column = box.column(align=True)
            column.label("Inflow Velocity:")
            row = column.row(align=True)
            row.prop(inflow_props, "inflow_velocity", text="")
        else:
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.label("Inflow Speed:")
            column_left.prop(inflow_props, "inflow_speed")

            column_right = split.column(align=True)
            column_right.label("Target Object:")
            column_right.prop_search(inflow_props, "target_object", context.scene, "objects")
            column_right.prop(inflow_props, "export_animated_target")

        box.separator()
        column = box.column(align=True)
        split = column.split(percentage=0.60)
        column = split.column()
        column.prop(inflow_props, "append_object_velocity")
        column = split.column(align=True)
        column.enabled = inflow_props.append_object_velocity
        column.prop(inflow_props, "append_object_velocity_influence")
        row = column.row(align=True)
        row.prop(inflow_props, "inflow_mesh_type", expand=True)

        column = self.layout.column()
        column.separator()
        column.prop(inflow_props, "export_animated_mesh")
    

def register():
    bpy.utils.register_class(FlipFluidInflowTypePanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidInflowTypePanel)
