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

from ..operators import helper_operators
from ..ui import domain_display_ui
from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils


def _draw_fluid_particle_display_settings(self, context):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    domain_display_ui.draw_fluid_particle_display_settings(self, context, dprops.particles)


def _draw_geometry_attributes_menu(self, context):
    obj = vcu.get_active_object(context)
    pprops = obj.flip_fluid.domain.particles
    sprops = obj.flip_fluid.domain.surface
    
    #
    # Geometry Attributes
    #
    #
    box = self.layout.box()
    header, body = box.panel("fluid_particle_geometry_attributes", default_closed=True)

    row = header.row(align=True)
    row.label(text="Fluid Particle Attributes:")
    if body:
        #
        # Velocity Attributes
        #
        box = body.box()
        header_velocity, body_velocity = box.panel("fluid_particle_velocity_attributes", default_closed=True)

        row_velocity = header_velocity.row(align=True)
        row_velocity.label(text="Velocity Based Attributes:")
        if body_velocity:
            column = body_velocity.column(align=True)
            column.prop(pprops, "enable_fluid_particle_velocity_vector_attribute", text="Velocity Attributes")
            column.prop(pprops, "enable_fluid_particle_speed_attribute", text="Speed Attributes")
            column.prop(pprops, "enable_fluid_particle_vorticity_vector_attribute", text="Vorticity Attributes")
            column.operator("flip_fluid_operators.helper_initialize_motion_blur")
        else:
            row = row_velocity.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_velocity_vector_attribute", text="Velocity")
            row.prop(pprops, "enable_fluid_particle_speed_attribute", text="Speed")
            row.prop(pprops, "enable_fluid_particle_vorticity_vector_attribute", text="Vorticity")

        #
        # Color Attributes
        #
        box = body.box()
        header_color, body_color = box.panel("fluid_particle_color_attributes", default_closed=True)

        row_color = header_color.row(align=True)
        row_color.label(text="Color and Mixing Attributes:")
        if body_color:
            column = body_color.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.prop(pprops, "enable_fluid_particle_color_attribute", text="Color Attributes")

            column = body_color.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.enabled = pprops.enable_fluid_particle_color_attribute
            column_left.prop(sprops, "enable_color_attribute_mixing", text="Enable Mixing")
            column_right.enabled = pprops.enable_fluid_particle_color_attribute and sprops.enable_color_attribute_mixing
            column_right.prop(sprops, "color_attribute_mixing_rate", text="Mix Rate", slider=True)

            column = body_color.column(align=True)
            column.enabled = pprops.enable_fluid_particle_color_attribute and sprops.enable_color_attribute_mixing
            column.label(text="Mixing Mode:")
            row = column.row(align=True)
            row.enabled = pprops.enable_fluid_particle_color_attribute
            row.prop(sprops, "color_attribute_mixing_mode", expand=True)

            if sprops.color_attribute_mixing_mode == 'COLOR_MIXING_MODE_MIXBOX':
                if not installation_utils.is_mixbox_supported():
                    column.label(text="Mixbox feature is not supported", icon="ERROR")
                    column.label(text="in this version of the FLIP Fluids Addon", icon="ERROR")

                if installation_utils.is_mixbox_supported():
                    if installation_utils.is_mixbox_installation_complete():
                        column.label(text="Mixbox Plugin Status: Installed", icon="CHECKMARK")
                    else:
                        column.label(text="Install the Mixbox plugin in the", icon="INFO")
                        column.label(text="FLIP Fluids Addon preferences", icon="INFO")
                        column.operator(
                                "flip_fluid_operators.open_preferences", 
                                text="Open Preferences", icon="PREFERENCES"
                                ).view_mode = 'PREFERENCES_MENU_VIEW_MIXBOX'
        else:
            row = row_color.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_color_attribute", text="Color")
            row = row_color.row(align=True)
            row.alignment = 'RIGHT'
            row.enabled = pprops.enable_fluid_particle_color_attribute
            row.prop(sprops, "enable_color_attribute_mixing", text="Mixing")
        
        #
        # Other Attributes
        #
        box = body.box()
        header_other, body_other = box.panel("fluid_particle_other_attributes", default_closed=True)

        row_other = header_other.row(align=True)
        row_other.label(text="Other Attributes:")
        if body_other:
            column = body_other.column(align=True)
            column.prop(pprops, "enable_fluid_particle_age_attribute", text="Age Attributes")
            row = column.row(align=True)
            row.prop(pprops, "enable_fluid_particle_lifetime_attribute", text="Lifetime Attributes")
            row.prop(sprops, "lifetime_attribute_death_time")
            column.prop(pprops, "enable_fluid_particle_whitewater_proximity_attribute", text="Whitewater Proximity Attributes")
            column.prop(pprops, "enable_fluid_particle_source_id_attribute", text="Source ID Attributes")
            row = column.row(align=True)
            row.prop(pprops, "enable_fluid_particle_uid_attribute", text="UID Attributes")
            row.prop(pprops, "enable_fluid_particle_uid_attribute_reuse", text="Reuse UIDs")
        else:
            row = row_other.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_age_attribute", text="Age")
            row.prop(pprops, "enable_fluid_particle_lifetime_attribute", text="Life")
            row.prop(pprops, "enable_fluid_particle_whitewater_proximity_attribute", text="WW Prox.")
            row.prop(pprops, "enable_fluid_particle_source_id_attribute", text="Source ID")
            row.prop(pprops, "enable_fluid_particle_uid_attribute", text="UID")

    
class FLIPFLUID_PT_DomainTypeFluidParticlesPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Particles"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if vcu.get_addon_preferences(context).enable_tabbed_domain_settings_view:
            return False
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN" and not is_addon_disabled


    def draw(self, context):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        pprops = obj.flip_fluid.domain.particles
        sprops = obj.flip_fluid.domain.surface
        aprops = dprops.advanced

        #
        # Fluid Particle Export Panel
        #
        box = self.layout.box()
        header, body = box.panel("fluid_particles", default_closed=False)

        row = header.row(align=True)
        row.label(text="Fluid Particle Export:")
        if body:
            column = body.column(align=True)
            column.prop(pprops, "enable_fluid_particle_output")
            subbox = column.box()
            subbox.enabled = pprops.enable_fluid_particle_output
            subcolumn = subbox.column(align=True)
            subcolumn.prop(pprops, "fluid_particle_output_amount", slider=True)
            subcolumn.prop(pprops, "enable_fluid_particle_surface_output")
            subcolumn.prop(pprops, "enable_fluid_particle_boundary_output")
            subcolumn.prop(pprops, "enable_fluid_particle_interior_output")
            subcolumn.separator()
            subcolumn.prop(pprops, "fluid_particle_source_id_blacklist", text="Skip Particles With Source ID Value")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_output")

        #
        # Fluid Particle Generation Panel
        #
        box = self.layout.box()
        header, body = box.panel("fluid_particle_generation", default_closed=True)

        row = header.row(align=True)
        row.label(text="Fluid Particle Generation:")
        if body:
            column = body.column()
            row = column.row(align=True)
            row.prop(aprops, "particle_jitter_factor", slider=True)
            row.prop(aprops, "jitter_surface_particles")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(aprops, "jitter_surface_particles")

        _draw_fluid_particle_display_settings(self, context)
        _draw_geometry_attributes_menu(self, context)

        self.layout.separator()
        column = self.layout.column(align=True)
        column.operator("flip_fluid_operators.helper_delete_particle_objects", icon="X")


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidParticlesPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidParticlesPanel)
