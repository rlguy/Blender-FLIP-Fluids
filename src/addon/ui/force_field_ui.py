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

import bpy, math

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_ForceFieldTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"

    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_FORCE_FIELD"

    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        force_field_props = obj_props.force_field
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        column = self.layout.column()
        column.prop(force_field_props, "force_field_type", text="Mode")

        column = self.layout.column()
        column.prop(force_field_props, "is_enabled")

        box = self.layout.box()
        box.label(text="Field Strength and Falloff:")
        column = box.column()
        column.prop(force_field_props, "strength")

        column = box.column(align=True)
        column.prop(force_field_props, "falloff_power")

        split = column.split()
        col = split.column()
        row = col.row(align=True)
        row.prop(force_field_props, "enable_min_distance", text="")
        sub = row.row(align=True)
        sub.active = force_field_props.enable_min_distance
        sub.prop(force_field_props.min_max_distance, "value_min")

        col = split.column()
        row = col.row(align=True)
        row.prop(force_field_props, "enable_max_distance", text="")
        sub = row.row(align=True)
        sub.active = force_field_props.enable_max_distance
        sub.prop(force_field_props.min_max_distance, "value_max")

        power = force_field_props.falloff_power
        distance = 0
        if force_field_props.enable_min_distance:
            distance = force_field_props.min_max_distance.value_min
        denominator = math.pow(distance, force_field_props.falloff_power)

        if denominator == 0.0:
            max_strength_str = "infinite"
        else:
            max_strength = force_field_props.strength * (1.0 / denominator)
            max_strength_str = self._format_strength_value(max_strength)
            
        column.separator()
        split = column.split()
        column = split.column()
        row = column.row()
        row.alignment = 'LEFT'
        row.prop(force_field_props, "maximum_strength_tooltip", icon="QUESTION", emboss=False, text="")
        row.label(text="Max Field Strength:")
        column = split.column()
        row = column.row()
        row.label(text=max_strength_str)
        
        column = self.layout.column()
        column.separator()
        split = column.split()
        column_left = split.column()
        column_left.prop(force_field_props, "export_animated_mesh")
        column_right = split.column()

        if show_advanced:
            column_right.enabled = force_field_props.export_animated_mesh
            column_right.prop(force_field_props, "skip_animated_mesh_reexport")


    def _format_strength_value(self, s):
        if s > 10:
            return '{0:.0f}'.format(s)
        if s > 1:
            return '{0:.1f}'.format(s)
        return '{0:.2f}'.format(s)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_ForceFieldTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_ForceFieldTypePanel)
