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


class FLIPFLUID_PT_DomainTypeWhitewaterPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Whitewater"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        wprops = dprops.whitewater
        is_whitewater_enabled = wprops.enable_whitewater_simulation
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui
        show_advanced_whitewater = (wprops.whitewater_ui_mode == 'WHITEWATER_UI_MODE_ADVANCED') and show_advanced
        highlight_advanced = wprops.highlight_advanced_settings and show_advanced

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Whitewater Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Whitewater-Settings"
            column.operator(
                "wm.url_open", 
                text="Simulation not generating enough whitewater", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#simulation-not-generating-enough-whitewater-foambubblespray"
            column.operator(
                "wm.url_open", 
                text="Whitewater particles are rendered too large", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#whitewater-particles-are-too-largesmall-when-rendered"
            column.operator(
                "wm.url_open", 
                text="Whitewater particles are not rendered in preview render", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#whitewater-particles-are-not-rendered-when-viewport-shading-is-set-to-rendered"
            column.operator(
                "wm.url_open", 
                text="Whitewater particles are not exported to Alembic", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Alembic-Export-Support#rendering-alembic-whitewater-on-a-render-farm"
            column.operator(
                "wm.url_open", 
                text="Whitewater rendering tips", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Whitewater-Settings#whitewater-rendering-tips"


        column = self.layout.column(align=True)
        column.prop(wprops, "enable_whitewater_simulation")
        column.separator()

        if show_advanced:
            box = self.layout.box()
            box.label(text="Settings View Mode:")
            column = box.column(align=True)
            row = column.row()
            row.prop(wprops, "whitewater_ui_mode", expand=True)

            split = column.split()
            split.column()
            column_right = split.column()
            column_right.enabled = show_advanced_whitewater
            column_right.prop(wprops, "highlight_advanced_settings")

        box = self.layout.box()
        box.label(text="Whitewater Simulation Particles:")
        column = box.column(align=True)
        column.enabled = is_whitewater_enabled

        row = column.row()
        row.prop(wprops, "enable_foam")
        row.prop(wprops, "enable_bubbles")
        row.prop(wprops, "enable_spray")
        row.prop(wprops, "enable_dust")

        if show_advanced_whitewater:
            # Whitewater motion blur rendering is currently too resource intensive
            # for Blender Cycles
            """
            column = self.layout.column(align=True)
            column.label(text="Rendering:")
            column.enabled = is_whitewater_enabled
            column.prop(wprops, "generate_whitewater_motion_blur_data")
            """

        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        row = box.row(align=True)
        row.prop(wprops, "emitter_settings_expanded",
            icon="TRIA_DOWN" if wprops.emitter_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Emitter Settings:")

        if wprops.emitter_settings_expanded:
            column = box.column(align=True)

            if show_advanced:
                column.prop(wprops, "enable_whitewater_emission")

            if show_advanced_whitewater:
                column = box.column(align=True)
                column.alert = highlight_advanced
                column.prop(wprops, "whitewater_emitter_generation_rate")

            column = box.column(align=True)
            column.prop(wprops, "wavecrest_emission_rate")
            column.prop(wprops, "turbulence_emission_rate")
            column = column.column(align=True)
            column.enabled = wprops.enable_dust
            column.prop(wprops, "dust_emission_rate")

            column = box.column(align=True)
            column.prop(wprops, "spray_emission_speed", slider=True)

            if show_advanced_whitewater:
                column = box.column(align=True)
                row = column.row(align=True)
                row.prop(wprops.min_max_whitewater_energy_speed, "value_min")
                row.prop(wprops.min_max_whitewater_energy_speed, "value_max")

                row = column.row(align=True)
                row.alert = highlight_advanced
                row.prop(wprops.min_max_whitewater_wavecrest_curvature, "value_min")
                row.prop(wprops.min_max_whitewater_wavecrest_curvature, "value_max")

                row = column.row(align=True)
                row.alert = highlight_advanced
                row.prop(wprops.min_max_whitewater_turbulence, "value_min")
                row.prop(wprops.min_max_whitewater_turbulence, "value_max")
            else:
                column = box.column()
                row = column.row(align=True)
                row.prop(wprops.min_max_whitewater_energy_speed, "value_min")
                row.prop(wprops.min_max_whitewater_energy_speed, "value_max")

            column = box.column(align=True)
            column.prop(wprops, "max_whitewater_particles")

            if show_advanced_whitewater:
                column = box.column(align=True)
                column.alert = highlight_advanced
                column.prop(wprops, "enable_whitewater_emission_near_boundary")

            column = box.column(align=True)
            column.enabled = wprops.enable_dust
            column.prop(wprops, "enable_dust_emission_near_boundary", text="Enable dust emission near domain floor")

        if show_advanced:
            box = self.layout.box()
            box.enabled = is_whitewater_enabled
            row = box.row(align=True)
            row.prop(wprops, "particle_settings_expanded",
                icon="TRIA_DOWN" if wprops.particle_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Particle Settings:")

            if wprops.particle_settings_expanded:

                column = box.column()
                column.label(text="Foam:")

                row = column.row()
                row.prop(wprops, "foam_advection_strength", text="Advection Strength", slider=True)

                if show_advanced_whitewater:
                    row = column.row()
                    row.alert = highlight_advanced
                    row.prop(wprops, "foam_layer_depth", text="Depth", slider=True)

                    row = column.row()
                    row.alert = highlight_advanced
                    row.prop(wprops, "foam_layer_offset", text="Offset", slider=True)

                # Preserve foam settings removed from UI - do not currently work as expected
                """
                if show_advanced:
                    column = box.column()
                    column.prop(wprops, "preserve_foam")

                if show_advanced_whitewater:
                    column = column.column(align=True)
                    column.enabled = wprops.preserve_foam
                    column.alert = highlight_advanced
                    column.prop(wprops, "foam_preservation_rate")
                    row = column.row(align=True)
                    row.prop(wprops.min_max_foam_density, "value_min")
                    row.prop(wprops.min_max_foam_density, "value_max")
                """

                if show_advanced:
                    column = box.column(align=True)
                    column.label(text="Bubble:")
                    column.prop(wprops, "bubble_drag_coefficient", text="Drag Coefficient", slider=True)
                    column.prop(wprops, "bubble_bouyancy_coefficient", text="Buoyancy Coefficient")

                    column = box.column(align=True)
                    column.label(text="Spray:")
                    column.prop(wprops, "spray_drag_coefficient", text="Drag Coefficient", slider=True)

                    column = box.column(align=True)
                    column.enabled = wprops.enable_dust
                    column.label(text="Dust:")
                    column.prop(wprops, "dust_drag_coefficient", text="Drag Coefficient", slider=True)
                    column.prop(wprops, "dust_bouyancy_coefficient", text="Buoyancy Coefficient")

                    column = box.column(align=True)
                    split = column.split()
                    column = split.column(align=True)
                    column.label(text="Lifespan:")
                    column.prop(wprops.min_max_whitewater_lifespan, "value_min", text="Min")
                    column.prop(wprops.min_max_whitewater_lifespan, "value_max", text="Max")
                    column.prop(wprops, "whitewater_lifespan_variance", text="Variance")

                    column = split.column(align=True)
                    column.label(text="Lifespan Modifiers:")
                    column.prop(wprops, "foam_lifespan_modifier", text="Foam")
                    column.prop(wprops, "bubble_lifespan_modifier", text="Bubble")
                    column.prop(wprops, "spray_lifespan_modifier", text="Spray")
                    column = column.column(align=True)
                    column.enabled = wprops.enable_dust
                    column.prop(wprops, "dust_lifespan_modifier", text="Dust")

        if show_advanced_whitewater:
            box = self.layout.box()
            box.alert = highlight_advanced
            row = box.row(align=True)
            row.prop(wprops, "boundary_behaviour_settings_expanded",
                icon="TRIA_DOWN" if wprops.boundary_behaviour_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Behaviour At Boundary:")

            if wprops.boundary_behaviour_settings_expanded:
                column = box.column()
                row = box.row()
                column = row.column(align=True)
                column.label(text="Foam:")
                column.prop(wprops, "foam_boundary_behaviour", text="")
                if wprops.foam_boundary_behaviour != 'BEHAVIOUR_COLLIDE':
                    r = column.row(align=True)
                    r.prop(wprops, "foam_boundary_active", index=0, text="X –")
                    r.prop(wprops, "foam_boundary_active", index=1, text="X+")
                    r = column.row(align=True)
                    r.prop(wprops, "foam_boundary_active", index=2, text="Y –")
                    r.prop(wprops, "foam_boundary_active", index=3, text="Y+")
                    r = column.row(align=True)
                    r.prop(wprops, "foam_boundary_active", index=4, text="Z –")
                    r.prop(wprops, "foam_boundary_active", index=5, text="Z+")

                column = row.column(align=True)
                column.label(text="Bubble:")
                column.prop(wprops, "bubble_boundary_behaviour", text="")
                if wprops.bubble_boundary_behaviour != 'BEHAVIOUR_COLLIDE':
                    r = column.row(align=True)
                    r.prop(wprops, "bubble_boundary_active", index=0, text="X –")
                    r.prop(wprops, "bubble_boundary_active", index=1, text="X+")
                    r = column.row(align=True)
                    r.prop(wprops, "bubble_boundary_active", index=2, text="Y –")
                    r.prop(wprops, "bubble_boundary_active", index=3, text="Y+")
                    r = column.row(align=True)
                    r.prop(wprops, "bubble_boundary_active", index=4, text="Z –")
                    r.prop(wprops, "bubble_boundary_active", index=5, text="Z+")

                column = row.column(align=True)
                column.label(text="Spray:")
                column.prop(wprops, "spray_boundary_behaviour", text="")
                if wprops.spray_boundary_behaviour != 'BEHAVIOUR_COLLIDE':
                    r = column.row(align=True)
                    r.prop(wprops, "spray_boundary_active", index=0, text="X –")
                    r.prop(wprops, "spray_boundary_active", index=1, text="X+")
                    r = column.row(align=True)
                    r.prop(wprops, "spray_boundary_active", index=2, text="Y –")
                    r.prop(wprops, "spray_boundary_active", index=3, text="Y+")
                    r = column.row(align=True)
                    r.prop(wprops, "spray_boundary_active", index=4, text="Z –")
                    r.prop(wprops, "spray_boundary_active", index=5, text="Z+")

        if show_advanced:
            box = self.layout.box()
            box.enabled = is_whitewater_enabled
            row = box.row(align=True)
            row.prop(wprops, "obstacle_settings_expanded",
                icon="TRIA_DOWN" if wprops.obstacle_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Obstacle Settings:")

            if wprops.obstacle_settings_expanded:
                column = box.column(align=True)

                # The following properties are probably set at reasonable values and
                # are not needed by the user
                """
                column.prop(wprops, "obstacle_influence_base_level", text="Base Level")
                column.prop(wprops, "obstacle_influence_decay_rate", text="Decay Rate")
                """

                obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()
                indent_str = 5 * " "
                column.label(text="Obstacle Object Influence:")
                if len(obstacle_objects) == 0:
                    column.label(text=indent_str + "No obstacle objects found...")
                else:
                    split = vcu.ui_split(column, factor=0.25, align=True)
                    column_left = split.column(align=True)
                    column_right = split.column(align=True)
                    for ob in obstacle_objects:
                        pgroup = ob.flip_fluid.get_property_group()
                        column_left.label(text=ob.name, icon="OBJECT_DATA")
                        row = column_right.row()
                        row.alignment = 'RIGHT'
                        row.prop(pgroup, "whitewater_influence", text="influence")
                        row.prop(pgroup, "dust_emission_strength", text="dust emission")

        self.draw_whitewater_display_settings(context)


    def draw_whitewater_display_settings(self, context):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        rprops = dprops.render
        wprops = dprops.whitewater
        is_whitewater_enabled = dprops.whitewater.enable_whitewater_simulation
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        master_box = self.layout.box()
        column = master_box.column()

        row = column.row(align=True)
        row.enabled = is_whitewater_enabled
        row.prop(wprops, "whitewater_display_settings_expanded",
            icon="TRIA_DOWN" if wprops.whitewater_display_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Particle Display and Render Settings:")

        if not wprops.whitewater_display_settings_expanded:
            return

        column.label(text="More settings found in FLIP Fluid Display Settings panel")

        if not show_advanced:
            box = master_box.box()
            box.enabled = is_whitewater_enabled
            box.label(text="Particle Object Settings:")
            row = box.row(align=True)
            row.prop(rprops, "whitewater_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_whitewater_in_render")
            return

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        column.label(text="Particle Object Settings Mode:")
        row = column.row()
        row.prop(rprops, "whitewater_particle_object_settings_mode", expand=True)
        column = box.column()

        box_column = box.column()
        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            column = box_column.column()
            column.label(text="Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "whitewater_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.whitewater_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop_search(rprops, "whitewater_particle_object", 
                            bpy.data, "objects", text="")
            row = column.row()
            row.prop(rprops, "whitewater_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_whitewater_in_render", text="Hide particles in viewport")
        else:
            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Foam Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "foam_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.foam_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop_search(rprops, "foam_particle_object", 
                            bpy.data, "objects", text="")
            row = column.row()
            row.prop(rprops, "foam_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_foam_in_render", text="Hide particles in viewport")

            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Bubble Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "bubble_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.bubble_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop_search(rprops, "bubble_particle_object", 
                            bpy.data, "objects", text="")
            row = column.row()
            row.prop(rprops, "bubble_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_bubble_in_render", text="Hide particles in viewport")

            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Spray Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "spray_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.spray_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop_search(rprops, "spray_particle_object", 
                            bpy.data, "objects", text="")
            row = column.row()
            row.prop(rprops, "spray_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_spray_in_render", text="Hide particles in viewport")

            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Dust Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "dust_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.dust_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop_search(rprops, "dust_particle_object", 
                            bpy.data, "objects", text="")
            row = column.row()
            row.prop(rprops, "dust_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_dust_in_render", text="Hide particles in viewport")
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeWhitewaterPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeWhitewaterPanel)
