# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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


def _draw_geometry_attributes_menu(self, context):
    obj = vcu.get_active_object(context)
    pprops = obj.flip_fluid.domain.particles
    sprops = obj.flip_fluid.domain.surface
    show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui
    
    #
    # Geometry Attributes
    #
    box = self.layout.box()
    row = box.row(align=True)
    row.prop(pprops, "geometry_attributes_expanded",
        icon="TRIA_DOWN" if pprops.geometry_attributes_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Fluid Particle Attributes:")

    if pprops.geometry_attributes_expanded:
        if not vcu.is_blender_31():
            column = box.column(align=True)
            column.enabled = False
            column.label(text="Geometry attribute features for fluid particles are only available in", icon='ERROR')
            column.label(text="Blender 3.1 or later", icon='ERROR')
            return

        #
        # Velocity Attributes
        #
        subbox = box.box()
        row = subbox.row(align=True)
        row.prop(pprops, "velocity_attributes_expanded",
            icon="TRIA_DOWN" if pprops.velocity_attributes_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Velocity Based Attributes:")

        if pprops.velocity_attributes_expanded:
            column = subbox.column(align=True)
            column.prop(pprops, "enable_fluid_particle_velocity_vector_attribute", text="Velocity Attributes")
            column.prop(pprops, "enable_fluid_particle_speed_attribute", text="Speed Attributes")
            column.prop(pprops, "enable_fluid_particle_vorticity_vector_attribute", text="Vorticity Attributes")
            column.operator("flip_fluid_operators.helper_initialize_motion_blur")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_velocity_vector_attribute", text="Velocity")
            row.prop(pprops, "enable_fluid_particle_speed_attribute", text="Speed")
            row.prop(pprops, "enable_fluid_particle_vorticity_vector_attribute", text="Vorticity")

        #
        # Color Attributes
        #
        subbox = box.box()
        row = subbox.row(align=True)
        row.prop(pprops, "color_attributes_expanded",
            icon="TRIA_DOWN" if pprops.color_attributes_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Color and Mixing Attributes:")

        if pprops.color_attributes_expanded:
            column = subbox.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.prop(pprops, "enable_fluid_particle_color_attribute", text="Color Attributes")

            column = subbox.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.enabled = pprops.enable_fluid_particle_color_attribute
            column_left.prop(sprops, "enable_color_attribute_mixing", text="Enable Mixing")
            column_right.enabled = pprops.enable_fluid_particle_color_attribute and sprops.enable_color_attribute_mixing
            column_right.prop(sprops, "color_attribute_mixing_rate", text="Mix Rate", slider=True)
            column_right.prop(sprops, "color_attribute_mixing_radius", text="Mix Radius", slider=True)

            column = subbox.column(align=True)
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
                        column.operator("flip_fluid_operators.open_preferences", text="Open Preferences", icon="PREFERENCES")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_color_attribute", text="Color")
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.enabled = pprops.enable_fluid_particle_color_attribute
            row.prop(sprops, "enable_color_attribute_mixing", text="Mixing")
        
        #
        # Other Attributes
        #
        subbox = box.box()
        row = subbox.row(align=True)
        row.prop(pprops, "other_attributes_expanded",
            icon="TRIA_DOWN" if pprops.other_attributes_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Other Attributes:")

        if pprops.other_attributes_expanded:
            column = subbox.column(align=True)
            column.prop(pprops, "enable_fluid_particle_age_attribute", text="Age Attributes")
            row = column.row(align=True)
            row.prop(pprops, "enable_fluid_particle_lifetime_attribute", text="Lifetime Attributes")
            row.prop(sprops, "lifetime_attribute_death_time")
            column.prop(pprops, "enable_fluid_particle_whitewater_proximity_attribute", text="Whitewater Proximity Attributes")
            column.prop(pprops, "enable_fluid_particle_source_id_attribute", text="Source ID Attributes")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_age_attribute", text="Age")
            row.prop(pprops, "enable_fluid_particle_lifetime_attribute", text="Life")
            row.prop(pprops, "enable_fluid_particle_whitewater_proximity_attribute", text="WW Prox.")
            row.prop(pprops, "enable_fluid_particle_source_id_attribute", text="Source ID")

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Domain Attributes Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Attributes-and-Data-Settings"
            column.operator(
                "wm.url_open", 
                text="Attributes and Motion Blur Example Scenes", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions#attribute-and-motion-blur-examples"

    
class FLIPFLUID_PT_DomainTypeFluidParticlesPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Particles"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if vcu.get_addon_preferences(context).enable_tabbed_domain_settings:
            return False
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN" and not is_addon_disabled


    def draw(self, context):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        pprops = obj.flip_fluid.domain.particles
        sprops = obj.flip_fluid.domain.surface
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        prefs = vcu.get_addon_preferences()
        if not prefs.is_developer_tools_enabled():
            warn_box = self.layout.box()
            warn_column = warn_box.column(align=True)
            warn_column.enabled = True
            warn_column.label(text="     This feature is affected by a current bug in Blender.", icon='ERROR')
            warn_column.label(text="     The Developer Tools option must be enabled in preferences")
            warn_column.label(text="     to use this feature.")
            warn_column.separator()
            warn_column.prop(prefs, "enable_developer_tools", text="Enable Developer Tools in Preferences")
            warn_column.separator()
            warn_column.operator(
                "wm.url_open", 
                text="Important Info and Limitations", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preferences-Menu-Settings#developer-tools"
            return

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(pprops, "fluid_particles_expanded",
            icon="TRIA_DOWN" if pprops.fluid_particles_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Fluid Particle Export:")

        if not pprops.fluid_particles_expanded:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(pprops, "enable_fluid_particle_output")

        if pprops.fluid_particles_expanded:
            column = box.column(align=True)
            column.prop(pprops, "enable_fluid_particle_output")
            subbox = column.box()
            subbox.enabled = pprops.enable_fluid_particle_output
            subcolumn = subbox.column(align=True)
            subcolumn.prop(pprops, "fluid_particle_output_amount", slider=True)
            subcolumn.prop(pprops, "enable_fluid_particle_surface_output")
            subcolumn.prop(pprops, "enable_fluid_particle_boundary_output")
            subcolumn.prop(pprops, "enable_fluid_particle_interior_output")

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(pprops, "fluid_particle_generation_expanded",
            icon="TRIA_DOWN" if pprops.fluid_particle_generation_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Fluid Particle Generation:")

        aprops = dprops.advanced
        if not pprops.fluid_particle_generation_expanded:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(aprops, "jitter_surface_particles")

        if pprops.fluid_particle_generation_expanded:
            column = box.column()
            row = column.row(align=True)
            row.prop(aprops, "particle_jitter_factor", slider=True)
            row.prop(aprops, "jitter_surface_particles")

        box = self.layout.box()
        row = box.row(align=True)
        row.enabled = pprops.enable_fluid_particle_output
        row.prop(pprops, "fluid_particle_display_settings_expanded",
            icon="TRIA_DOWN" if pprops.fluid_particle_display_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Fluid Particle Display and Render Settings:")

        if pprops.fluid_particle_display_settings_expanded:
            bl_fluid_particles_mesh_cache = dprops.mesh_cache.particles.get_cache_object()
            point_cloud_detected = helper_operators.is_geometry_node_point_cloud_detected(bl_fluid_particles_mesh_cache)

            column = box.column(align=True)
            column.label(text="More display settings can be found in the FLIP Fluid Display Settings panel")

            subbox = box.box()
            subbox.enabled = pprops.enable_fluid_particle_output
            column = subbox.column(align=True)
            column.label(text="Particle Object Settings:")

            if point_cloud_detected:
                column.label(text="Point cloud geometry nodes setup detected", icon="INFO")
                column.label(text="More settings can be found in the fluid particles object geometry nodes modifier", icon="INFO")
                column.separator()

                bl_mod = domain_display_ui.get_motion_blur_geometry_node_modifier(bl_fluid_particles_mesh_cache)
                row = column.row(align=True)
                row.alignment = 'LEFT'
                row.label(text="Fluid Particles:")
                domain_display_ui.draw_whitewater_motion_blur_geometry_node_properties(row, bl_mod)
            else:
                column.label(text="FLIP Fluids Geometry Nodes Modifier not found on fluid particles object.", icon="INFO")
                column.label(text="Fluid particle settings will be unavailable in this menu.", icon="INFO")

        _draw_geometry_attributes_menu(self, context)

        self.layout.separator()
        column = self.layout.column(align=True)
        column.operator("flip_fluid_operators.helper_delete_particle_objects", icon="X")


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidParticlesPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidParticlesPanel)
