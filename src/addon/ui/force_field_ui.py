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
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        column = self.layout.column()
        column.prop(force_field_props, "force_field_type", text="Mode")

        if obj.type == 'CURVE' and force_field_props.force_field_type != 'FORCE_FIELD_TYPE_CURVE':
            column = self.layout.column()
            column.label(text="Curve objects can only be set as a Curve Guide Force Field")
            return

        if obj.type == 'EMPTY' and force_field_props.force_field_type != 'FORCE_FIELD_TYPE_POINT':
            column = self.layout.column()
            column.label(text="Empty objects can only be set as a Point Force Field")
            return

        if obj.type == 'MESH' and force_field_props.force_field_type == 'FORCE_FIELD_TYPE_CURVE':
            column = self.layout.column()
            column.label(text="Mesh objects cannot be used as a Curve Guide Force Field")
            column.label(text="Curve Guide Force Fields only support Curve objects")
            return

        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_VORTEX':
            column = self.layout.column()
            column.label(text="Vortex force is not yet available")
            column.label(text="Feature implementation in progress")
            return
        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_TURBULENCE':
            column = self.layout.column()
            column.label(text="Turbulence guided force is not yet available")
            column.label(text="Feature implementation in progress")
            return
        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_PROGRAMMABLE':
            column = self.layout.column()
            column.label(text="Programmable guided force is not yet available")
            column.label(text="Feature implementation in progress")
            return
        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_OTHER':
            column = self.layout.column()
            column.label(text="More force field modes are in development")
            column.label(text="Try out our experimental builds for the latest features!")
            column.operator(
                "wm.url_open", 
                text="Experimental Builds", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Experimental-Builds"
            return

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Force Field Object Settings", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Force-Field-Object-Settings"
            column.operator(
                "wm.url_open", 
                text="Force Field Example Scenes", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions#force-field-examples"

        column = self.layout.column()
        column.prop(force_field_props, "is_enabled")

        strength_text = "Strength"
        if force_field_props.force_field_type == 'FORCE_FIELD_TYPE_CURVE':
            strength_text = "Attraction Strength"

        box = self.layout.box()
        box.label(text="Field Strength and Falloff:")
        column = box.column(align=True)
        column.prop(force_field_props, "strength", text=strength_text)

        if force_field_props.force_field_type == 'FORCE_FIELD_TYPE_CURVE':
            column.prop(force_field_props, "flow_strength")
            column.prop(force_field_props, "spin_strength")
            row = column.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(force_field_props, "enable_endcaps")

        column = box.column(align=True)
        if force_field_props.force_field_type == 'FORCE_FIELD_TYPE_POINT':
            split = column.split()
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.prop(force_field_props, "falloff_power")
            column_right.enabled=False

            # Todo: implement point shapes
            #column_right.prop(force_field_props, "falloff_shape", text="Shape")
        else:
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

        eps = 1e-12
        power = force_field_props.falloff_power
        distance = eps
        if force_field_props.enable_min_distance:
            distance = max(force_field_props.min_max_distance.value_min, eps)
        denominator = math.pow(distance, force_field_props.falloff_power)

        if denominator == 0.0:
            max_strength_str = "infinite"
        else:
            strength = abs(force_field_props.strength)
            max_strength = strength * (1.0 / denominator)
            limit_factor = force_field_props.maximum_force_limit_factor
            max_strength = min(max_strength, limit_factor * strength)
            max_strength_str = self._format_strength_value(max_strength)
            
        column.separator()
        column.separator()
        column.prop(force_field_props, "maximum_force_limit_factor")

        split = column.split()
        column = split.column()
        row = column.row()
        row.alignment = 'LEFT'
        row.prop(force_field_props, "maximum_strength_tooltip", icon="QUESTION", emboss=False, text="")
        row.label(text="Max Force:")
        column = split.column()
        row = column.row()
        row.label(text=max_strength_str)

        self.layout.separator()
        box = self.layout.box()
        box.label(text="Antigravity")
        column = box.column(align=True)

        if force_field_props.force_field_type == 'FORCE_FIELD_TYPE_POINT':
            column.prop(force_field_props, "gravity_scale_point", slider=True)
            column.prop(force_field_props, "gravity_scale_width_point", text="Width", slider=True)
        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_SURFACE':
            column.prop(force_field_props, "gravity_scale_surface", slider=True)
            column.prop(force_field_props, "gravity_scale_width_surface", text="Width", slider=True)
        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_VOLUME':
            column.prop(force_field_props, "gravity_scale_volume", slider=True)
            column.prop(force_field_props, "gravity_scale_width_volume", text="Width", slider=True)
        elif force_field_props.force_field_type == 'FORCE_FIELD_TYPE_CURVE':
            column.prop(force_field_props, "gravity_scale_curve", slider=True)
            column.prop(force_field_props, "gravity_scale_width_curve", text="Width", slider=True)
        
        box = self.layout.box()
        box.label(text="Mesh Data Export:")
        column = box.column(align=True)
        column.prop(force_field_props, "export_animated_mesh")
        if show_advanced:
            column.prop(force_field_props, "skip_reexport")
            column.separator()
            column = box.column(align=True)
            column.enabled = force_field_props.skip_reexport
            column.prop(force_field_props, "force_reexport_on_next_bake", toggle=True)


    def _format_strength_value(self, s):
        if s > 10:
            return '{0:.1f}'.format(s)
        if s > 1:
            return '{0:.2f}'.format(s)
        return '{0:.3f}'.format(s)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_ForceFieldTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_ForceFieldTypePanel)
