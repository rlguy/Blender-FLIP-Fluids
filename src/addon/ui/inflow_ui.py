# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
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
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == 'TYPE_INFLOW' and not is_addon_disabled


    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        inflow_props = obj_props.inflow
        dprops = context.scene.flip_fluid.get_domain_properties()

        show_disabled_in_viewport_warning = True
        if show_disabled_in_viewport_warning and obj.hide_viewport:
            box = self.layout.box()
            box.alert = True
            column = box.column(align=True)
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.prop(inflow_props, "disabled_in_viewport_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="Object is currently disabled in the viewport")
            row.label(text="", icon="RESTRICT_VIEW_ON")
            column.label(text="This object will not be included within the simulation")

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        column = self.layout.column()
        column.prop(inflow_props, "is_enabled")
        column.prop(inflow_props, "substep_emissions")
        column.prop(inflow_props, "priority", text="Priority Level")

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
            search_group = "all_objects"
                
            column_right = split.column(align=True)
            column_right.label(text="Target Object:")
            column_right.prop_search(inflow_props, "target_object", target_collection, search_group, text="")

            target_object = inflow_props.get_target_object()
            if target_object is not None:
                is_target_domain = target_object.flip_fluid.is_domain()
                target_props = target_object.flip_fluid.get_property_group()
                if target_props is not None and not is_target_domain:
                    column_right.prop(target_props, "export_animated_mesh", text="Export Animated Target")
                else:
                    column_right.prop(inflow_props, "export_animated_target")
            else:
                column_right.prop(inflow_props, "export_animated_target")

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

        if vcu.get_addon_preferences().is_extra_features_enabled():
            box = self.layout.box()
            box.label(text="Geometry Attributes:")
            column = box.column(align=True)
            
            is_color_attribute_enabled = dprops is not None and (dprops.surface.enable_color_attribute or 
                                                                 dprops.particles.enable_fluid_particle_color_attribute)
            show_color = dprops is not None and is_color_attribute_enabled
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.enabled = show_color
            column_left.prop(inflow_props, "color")
            column_right = split.column(align=True)
            column_right.label(text="")
            row = column_right.row(align=True)
            row.alignment = 'LEFT'
            if dprops is not None and not show_color:
                row.operator("flip_fluid_operators.enable_color_attribute_tooltip", 
                             text="Enable Color Attribute", icon="PLUS", emboss=False)
            if dprops is None:
                row.label(text="Domain required for this option")
            column.separator()

            show_viscosity = dprops is not None and dprops.world.enable_viscosity and dprops.surface.enable_viscosity_attribute
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.enabled = show_viscosity
            column_left.prop(inflow_props, "viscosity")
            column_right = split.column(align=True)
            row = column_right.row(align=True)
            row.alignment = 'LEFT'
            if dprops is not None and not show_viscosity:
                row.operator("flip_fluid_operators.enable_viscosity_attribute_tooltip", 
                             text="Enable Viscosity Attribute", icon="PLUS", emboss=False)
            if dprops is None:
                row.label(text="Domain required for this option")
            column.separator()

            show_density = dprops is not None and dprops.world.enable_density_attribute
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.enabled = show_density
            column_left.prop(inflow_props, "density")
            column_right = split.column(align=True)
            row = column_right.row(align=True)
            row.alignment = 'LEFT'
            if dprops is not None and not show_density:
                row.operator("flip_fluid_operators.enable_density_attribute_tooltip", 
                             text="Enable Density Attribute", icon="PLUS", emboss=False)
            if dprops is None:
                row.label(text="Domain required for this option")
            column.separator()

            is_lifetime_attribute_enabled = dprops is not None and (dprops.surface.enable_lifetime_attribute or 
                                                                    dprops.particles.enable_fluid_particle_lifetime_attribute)
            show_lifetime = dprops is not None and is_lifetime_attribute_enabled
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.enabled = show_lifetime
            column_left.prop(inflow_props, "lifetime")
            column_right = split.column(align=True)
            row = column_right.row(align=True)
            row.alignment = 'LEFT'
            if dprops is not None and not show_lifetime:
                row.operator("flip_fluid_operators.enable_lifetime_attribute_tooltip", 
                             text="Enable Lifetime Attribute", icon="PLUS", emboss=False)
            elif dprops is not None:
                row.alignment = 'EXPAND'
                row.prop(inflow_props, "lifetime_variance", text="Variance")
            if dprops is None:
                row.label(text="Domain required for this option")
            column.separator()

            is_source_id_attribute_enabled = dprops is not None and (dprops.surface.enable_source_id_attribute or 
                                                                     dprops.particles.enable_fluid_particle_source_id_attribute)
            show_source_id = dprops is not None and is_source_id_attribute_enabled
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.enabled = show_source_id
            column_left.prop(inflow_props, "source_id")
            column_right = split.column(align=True)
            row = column_right.row(align=True)
            row.alignment = 'LEFT'
            if dprops is not None and not show_source_id:
                row.operator("flip_fluid_operators.enable_source_id_attribute_tooltip", 
                             text="Enable Source ID Attribute", icon="PLUS", emboss=False)
            if dprops is None:
                row.label(text="Domain required for this option")
            column.separator()

        box = self.layout.box()
        box.label(text="Mesh Data Export:")
        column = box.column(align=True)
        
        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.prop(inflow_props, "export_animated_mesh")

        is_child_object = obj.parent is not None
        is_hint_enabled = not vcu.get_addon_preferences().dismiss_export_animated_mesh_parented_relation_hint
        if is_hint_enabled and not inflow_props.export_animated_mesh and is_child_object:
            row.prop(context.scene.flip_fluid_helper, "export_animated_mesh_parent_tooltip", 
                    icon="QUESTION", emboss=False, text=""
                    )
            row.label(text="←Hint: export option may be required")
        
        column.prop(inflow_props, "skip_reexport")
        column.separator()
        column = box.column(align=True)
        column.enabled = inflow_props.skip_reexport
        column.prop(inflow_props, "force_reexport_on_next_bake", toggle=True)

        column = self.layout.column(align=True)
        column.separator()
        column.operator("flip_fluid_operators.copy_setting_to_selected", icon='COPYDOWN')
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_InflowTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_InflowTypePanel)
