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

from ..ui import domain_display_ui
from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils


def _draw_fluid_surface_display_settings(self, context):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    domain_display_ui.draw_surface_display_settings(self, context, dprops.surface)


def _draw_geometry_attributes_menu(self, context):
    obj = vcu.get_active_object(context)
    sprops = obj.flip_fluid.domain.surface
    rprops = obj.flip_fluid.domain.render
    is_surface_mesh_generation_enabled = sprops.enable_surface_mesh_generation

    #
    # Geometry Attributes
    #
    is_preview_mode_enabled = rprops.viewport_display == 'DISPLAY_PREVIEW'
    is_attributes_enabled = (
            sprops.enable_velocity_vector_attribute or
            sprops.enable_speed_attribute or
            sprops.enable_vorticity_vector_attribute or
            sprops.enable_color_attribute or
            sprops.enable_age_attribute or
            sprops.enable_lifetime_attribute or
            sprops.enable_whitewater_proximity_attribute or
            sprops.enable_source_id_attribute or
            sprops.enable_viscosity_attribute
            )

    box = self.layout.box()
    header, body = box.panel("geometry_attributes", default_closed=True)

    row = header.row(align=True)
    row.alert = not is_surface_mesh_generation_enabled
    row.label(text="Surface Attributes:")
    if body:
        if is_preview_mode_enabled and is_attributes_enabled:
            row = body.row(align=True)
            row.alert = True
            row.alignment = 'LEFT'
            row.prop(sprops, "preview_mode_attributes_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="Warning: Surface attributes will not be loaded in mesh Preview Mode")

        #
        # Velocity Attributes
        #
        box = body.box()
        header_velocity, body_velocity = box.panel("velocity_attributes", default_closed=True)

        row_velocity = header_velocity.row(align=True)
        row_velocity.alert = not is_surface_mesh_generation_enabled
        row_velocity.label(text="Velocity Based Attributes:")
        if body_velocity:
            column = body_velocity.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_right.enabled = sprops.enable_velocity_vector_attribute or sprops.enable_speed_attribute or sprops.enable_vorticity_vector_attribute
            column_left.prop(sprops, "enable_velocity_vector_attribute", text="Velocity Attributes")
            
            # This option should always be on. Hiding option from UI, and always enabling this in the simulator.
            #column_right.prop(sprops, "enable_velocity_vector_attribute_against_obstacles", text="Generate Against Obstacles")
            
            column.prop(sprops, "enable_speed_attribute", text="Speed Attributes")
            column.prop(sprops, "enable_vorticity_vector_attribute", text="Vorticity Attributes")
            column.separator()
            column.operator("flip_fluid_operators.helper_initialize_motion_blur")
        else:
            row = row_velocity.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_velocity_vector_attribute", text="Velocity")
            row.prop(sprops, "enable_speed_attribute", text="Speed")
            row.prop(sprops, "enable_vorticity_vector_attribute", text="Vorticity")
        
        #
        # Color Attributes
        #
        box = body.box()
        header_color, body_color = box.panel("color_attributes", default_closed=True)

        row_color = header_color.row(align=True)
        row_color.alert = not is_surface_mesh_generation_enabled
        row_color.label(text="Color and Mixing Attributes:")
        if body_color:
            column = body_color.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.prop(sprops, "enable_color_attribute", text="Color Attributes")
            if sprops.show_smoothing_radius_in_ui:
                column_right.prop(sprops, "color_attribute_radius", text="Smoothing", slider=True)

            column = body_color.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.enabled = sprops.enable_color_attribute
            column_left.prop(sprops, "enable_color_attribute_mixing", text="Enable Mixing")
            column_right.enabled = sprops.enable_color_attribute and sprops.enable_color_attribute_mixing
            column_right.prop(sprops, "color_attribute_mixing_rate", text="Mix Rate", slider=True)

            column = body_color.column(align=True)
            column.enabled = sprops.enable_color_attribute and sprops.enable_color_attribute_mixing
            column.label(text="Mixing Mode:")
            row = column.row(align=True)
            row.enabled = sprops.enable_color_attribute
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
            row.prop(sprops, "enable_color_attribute", text="Color")
            row = row_color.row(align=True)
            row.alignment = 'RIGHT'
            row.enabled = sprops.enable_color_attribute
            row.prop(sprops, "enable_color_attribute_mixing", text="Mixing")

        #
        # Other Attributes
        #
        box = body.box()
        header_other, body_other = box.panel("other_attributes", default_closed=True)

        row_other = header_other.row(align=True)
        row_other.alert = not is_surface_mesh_generation_enabled
        row_other.label(text="Other Attributes:")
        if body_other:
            column = body_other.column(align=True)
            row = column.row(align=True)
            row.prop(sprops, "enable_age_attribute", text="Age Attributes")
            if sprops.show_smoothing_radius_in_ui:
                row.prop(sprops, "age_attribute_radius", text="Smoothing", slider=True)
            else:
                row.label(text="")
            row = column.row(align=True)
            row.prop(sprops, "enable_lifetime_attribute", text="Lifetime Attributes")
            row.prop(sprops, "lifetime_attribute_death_time")
            if sprops.show_smoothing_radius_in_ui:
                row.prop(sprops, "lifetime_attribute_radius", text="Smoothing", slider=True)
            row = column.row(align=True)
            row.prop(sprops, "enable_whitewater_proximity_attribute", text="Whitewater Proximity Attributes")
            if sprops.show_smoothing_radius_in_ui:
                row.prop(sprops, "whitewater_proximity_attribute_radius", text="Smoothing", slider=True)
            column.prop(sprops, "enable_source_id_attribute", text="Source ID Attributes")
        else:
            row = row_other.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_age_attribute", text="Age")
            row.prop(sprops, "enable_lifetime_attribute", text="Life")
            row.prop(sprops, "enable_whitewater_proximity_attribute", text="WW Prox.")
            row.prop(sprops, "enable_source_id_attribute", text="Source ID")

    
class FLIPFLUID_PT_DomainTypeFluidSurfacePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Surface"
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
        sprops = obj.flip_fluid.domain.surface
        is_surface_mesh_generation_enabled = sprops.enable_surface_mesh_generation
        
        column = self.layout.column(align=True)
        column.prop(sprops, "enable_surface_mesh_generation")

        #
        # Surface Mesh Panel
        #
        box = self.layout.box()
        header, body = box.panel("surface_mesh", default_closed=False)

        row = header.row(align=True)
        row.alert = not is_surface_mesh_generation_enabled
        row.label(text="Surface Mesh:")
        if body:
            column = body.column(align=True)
            column.prop(sprops, "subdivisions")
            row = column.row(align=True)
            if sprops.particle_scale < 0.999:
                row.alert = True
            row.prop(sprops, "particle_scale")
        else:
            info_text = "Subdivisions " + str(sprops.subdivisions) + "  /  "
            info_text += "Scale " + "{:.2f}".format(sprops.particle_scale)
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            if sprops.particle_scale < 0.999:
                row.alert = True
            row.label(text=info_text)

        #
        # Meshing Volume Panel
        #
        box = self.layout.box()
        header, body = box.panel("meshing_volume", default_closed=True)

        row = header.row(align=True)
        row.alert = not is_surface_mesh_generation_enabled
        row.label(text="Meshing Volume:")
        if body:
            row = body.row(align=True)
            row.prop(sprops, "meshing_volume_mode", expand=True)
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_right.enabled = sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_OBJECT"
            column_right.prop_search(sprops, "meshing_volume_object", vcu.get_scene_collection(), "all_objects", text="Object")
            column_right.prop(sprops, "export_animated_meshing_volume_object")
        else:
            info_text = ""
            if sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_DOMAIN":
                info_text = "Domain Volume"
            elif sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_OBJECT":
                info_text = "Object Volume"
                if sprops.meshing_volume_object is not None:
                    info_text += ": <" + sprops.meshing_volume_object.name + ">"
                else:
                    info_text += ": None"
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=info_text)

        #
        # Meshing Volume Panel
        #
        box = self.layout.box()
        header, body = box.panel("meshing_against_boundary", default_closed=True)

        row = header.row(align=True)
        row.alert = not is_surface_mesh_generation_enabled
        row.label(text="Meshing Against Boundary:")
        if body:
            column = body.column(align=True)
            column.prop(sprops, "remove_mesh_near_domain")

            column = body.column(align=True)
            column.enabled = sprops.remove_mesh_near_domain
            row = column.row(align=True)
            row.prop(sprops, "remove_mesh_near_domain_sides", index=0, text="X –")
            row.prop(sprops, "remove_mesh_near_domain_sides", index=1, text="X+")
            row = column.row(align=True)
            row.prop(sprops, "remove_mesh_near_domain_sides", index=2, text="Y –")
            row.prop(sprops, "remove_mesh_near_domain_sides", index=3, text="Y+")
            row = column.row(align=True)
            row.prop(sprops, "remove_mesh_near_domain_sides", index=4, text="Z –")
            row.prop(sprops, "remove_mesh_near_domain_sides", index=5, text="Z+")
            column.prop(sprops, "remove_mesh_near_domain_distance")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "remove_mesh_near_domain", text="Remove")

        #
        # Meshing Against Obstacle Panel
        #
        box = self.layout.box()
        header, body = box.panel("meshing_against_obstacles", default_closed=True)

        row = header.row(align=True)
        row.alert = not is_surface_mesh_generation_enabled
        row.label(text="Meshing Against Obstacles:")
        if body:
            column = body.column(align=True)
            column.prop(sprops, "enable_meshing_offset")
            row = body.row(align=True)
            row.enabled = sprops.enable_meshing_offset
            row.prop(sprops, "obstacle_meshing_mode", expand=True)
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_meshing_offset", text="Enable  ")

        _draw_fluid_surface_display_settings(self, context)
        _draw_geometry_attributes_menu(self, context)

        self.layout.separator()
        column = self.layout.column(align=True)
        column.operator("flip_fluid_operators.helper_delete_surface_objects", icon="X")


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidSurfacePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidSurfacePanel)
