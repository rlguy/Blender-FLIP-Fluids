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

from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils


def _draw_geometry_attributes_menu(self, context):
    obj = vcu.get_active_object(context)
    sprops = obj.flip_fluid.domain.surface
    show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

    #
    # Geometry Attributes
    #
    box = self.layout.box()
    row = box.row(align=True)
    row.alert = not sprops.enable_surface_mesh_generation
    row.prop(sprops, "geometry_attributes_expanded",
        icon="TRIA_DOWN" if sprops.geometry_attributes_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Surface Attributes:")

    if sprops.geometry_attributes_expanded:
        prefs = vcu.get_addon_preferences()
        if not prefs.is_developer_tools_enabled():
            warn_box = box.box()
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

        if not vcu.is_blender_293():
            column = box.column(align=True)
            column.enabled = False
            column.label(text="Geometry attribute features for the fluid surface are only available in", icon='ERROR')
            column.label(text="Blender 2.93 or later. Blender 3.1 or later recommended.", icon='ERROR')
            return

        #
        # Velocity Attributes
        #
        subbox = box.box()
        row = subbox.row(align=True)
        row.prop(sprops, "velocity_attributes_expanded",
            icon="TRIA_DOWN" if sprops.velocity_attributes_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Velocity Based Attributes:")

        if sprops.velocity_attributes_expanded:
            column = subbox.column(align=True)
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
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_velocity_vector_attribute", text="Velocity")
            row.prop(sprops, "enable_speed_attribute", text="Speed")
            row.prop(sprops, "enable_vorticity_vector_attribute", text="Vorticity")
        
        #
        # Color Attributes
        #
        subbox = box.box()
        row = subbox.row(align=True)
        row.prop(sprops, "color_attributes_expanded",
            icon="TRIA_DOWN" if sprops.color_attributes_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Color and Mixing Attributes:")

        if sprops.color_attributes_expanded:
            column = subbox.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.prop(sprops, "enable_color_attribute", text="Color Attributes")
            if sprops.show_smoothing_radius_in_ui:
                column_right.prop(sprops, "color_attribute_radius", text="Smoothing", slider=True)

            column = subbox.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.enabled = sprops.enable_color_attribute
            column_left.prop(sprops, "enable_color_attribute_mixing", text="Enable Mixing")
            column_right.enabled = sprops.enable_color_attribute and sprops.enable_color_attribute_mixing
            column_right.prop(sprops, "color_attribute_mixing_rate", text="Mix Rate", slider=True)
            column_right.prop(sprops, "color_attribute_mixing_radius", text="Mix Radius", slider=True)

            column = subbox.column(align=True)
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
                        column.operator("flip_fluid_operators.open_preferences", text="Open Preferences", icon="PREFERENCES")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_color_attribute", text="Color")
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.enabled = sprops.enable_color_attribute
            row.prop(sprops, "enable_color_attribute_mixing", text="Mixing")

        #
        # Other Attributes
        #
        subbox = box.box()
        row = subbox.row(align=True)
        row.prop(sprops, "other_attributes_expanded",
            icon="TRIA_DOWN" if sprops.other_attributes_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Other Attributes:")

        if sprops.other_attributes_expanded:
            column = subbox.column(align=True)
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
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_age_attribute", text="Age")
            row.prop(sprops, "enable_lifetime_attribute", text="Life")
            row.prop(sprops, "enable_whitewater_proximity_attribute", text="WW Prox.")
            row.prop(sprops, "enable_source_id_attribute", text="Source ID")

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

    
class FLIPFLUID_PT_DomainTypeFluidSurfacePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Surface"
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
        sprops = obj.flip_fluid.domain.surface
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Surface and Meshing Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Surface-Settings"
            column.operator(
                "wm.url_open", 
                text="How do I make my surface smoother?", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Surface-Settings#mesh-smoothing"
            column.operator(
                "wm.url_open", 
                text="Mesh banding against curved obstacles", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#mesh-banding-artifacts-against-curved-obstacles"

        column = self.layout.column(align=True)
        column.prop(sprops, "enable_surface_mesh_generation")

        box = self.layout.box()
        row = box.row(align=True)
        row.alert = not sprops.enable_surface_mesh_generation
        row.prop(sprops, "surface_mesh_expanded",
            icon="TRIA_DOWN" if sprops.surface_mesh_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Surface Mesh:")

        if not sprops.surface_mesh_expanded:
            info_text = "Subdivisions " + str(sprops.subdivisions) + "  /  "
            info_text += "Scale " + "{:.2f}".format(sprops.particle_scale)
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            if sprops.particle_scale < 0.999:
                row.alert = True
            row.label(text=info_text)

        if sprops.surface_mesh_expanded:
            column = box.column(align=True)
            column.prop(sprops, "subdivisions")
            row = column.row(align=True)
            if sprops.particle_scale < 0.999:
                row.alert = True
            row.prop(sprops, "particle_scale")

        object_collection = vcu.get_scene_collection()
        if vcu.is_blender_28():
            search_group = "all_objects"
        else:
            search_group = "objects"

        box = self.layout.box()
        row = box.row(align=True)
        row.alert = not sprops.enable_surface_mesh_generation
        row.prop(sprops, "meshing_volume_expanded",
            icon="TRIA_DOWN" if sprops.meshing_volume_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Meshing Volume:")

        if not sprops.meshing_volume_expanded:
            info_text = ""
            if sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_DOMAIN":
                info_text = "Domain Volume"
            elif sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_OBJECT":
                info_text = "Object Volume"
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=info_text)

        if sprops.meshing_volume_expanded:
            row = box.row(align=True)
            row.prop(sprops, "meshing_volume_mode", expand=True)
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_right.enabled = sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_OBJECT"
            column_right.prop_search(sprops, "meshing_volume_object", object_collection, search_group, text="Object")
            column_right.prop(sprops, "export_animated_meshing_volume_object")

        box = self.layout.box()
        row = box.row(align=True)
        row.alert = not sprops.enable_surface_mesh_generation
        row.prop(sprops, "meshing_against_boundary_expanded",
            icon="TRIA_DOWN" if sprops.meshing_against_boundary_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Meshing Against Boundary:")

        if not sprops.meshing_against_boundary_expanded:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "remove_mesh_near_domain", text="Remove")

        if sprops.meshing_against_boundary_expanded:
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column()
            column_left.prop(sprops, "remove_mesh_near_domain")
            column_right = split.column()
            column_right.enabled = sprops.remove_mesh_near_domain
            column_right.prop(sprops, "remove_mesh_near_domain_distance")

        box = self.layout.box()
        row = box.row(align=True)
        row.alert = not sprops.enable_surface_mesh_generation
        row.prop(sprops, "meshing_against_obstacles_expanded",
            icon="TRIA_DOWN" if sprops.meshing_against_obstacles_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Meshing Against Obstacles:")

        if not sprops.meshing_against_obstacles_expanded:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(sprops, "enable_meshing_offset", text="Enable  ")

        if sprops.meshing_against_obstacles_expanded:
            column = box.column(align=True)
            column.prop(sprops, "enable_meshing_offset")
            row = box.row(align=True)
            row.enabled = sprops.enable_meshing_offset
            row.prop(sprops, "obstacle_meshing_mode", expand=True)

            if show_documentation:
                column = box.column(align=True)
                column.operator(
                    "wm.url_open", 
                    text="Which meshing offset mode to use?", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Surface-Settings#which-offset-mode-to-use"

        # Removed surface smoothing options. These are better set
        # using a Blender smooth modifier.
        """
        box = self.layout.box()
        box.label(text="Smoothing:")
        row = box.row(align=True)
        row.prop(sprops, "smoothing_value")
        row.prop(sprops, "smoothing_iterations")
        """

        # Motion Blur is no longer supported
        #column = self.layout.column(align=True)
        #column.separator()
        #column.prop(sprops, "generate_motion_blur_data")

        _draw_geometry_attributes_menu(self, context)

        self.layout.separator()
        column = self.layout.column(align=True)
        column.operator("flip_fluid_operators.helper_delete_surface_objects", icon="X")


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidSurfacePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidSurfacePanel)
