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
from . import domain_display_ui
from ..utils import version_compatibility_utils as vcu


def _draw_whitewater_display_settings(self, context):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    domain_display_ui.draw_whitewater_display_settings(self, context, dprops.whitewater)


def _draw_geometry_attributes_menu(self, context):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    wprops = dprops.whitewater
    prefs = vcu.get_addon_preferences()

    #
    # Whitewater Attributes Panel
    #
    box = self.layout.box()
    header, body = box.panel("whitewater_geometry_attributes", default_closed=True)

    row = header.row(align=True)
    row.label(text="Whitewater Attribute:")
    if body:
        column = body.column(align=True)
        column.prop(wprops, "enable_velocity_vector_attribute")
        column.prop(wprops, "enable_id_attribute")
        column.prop(wprops, "enable_lifetime_attribute")
        column.separator()
        column.operator("flip_fluid_operators.helper_initialize_motion_blur")
    else:
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(wprops, "enable_velocity_vector_attribute", text="Velocity")
        row.prop(wprops, "enable_id_attribute", text="ID")
        row.prop(wprops, "enable_lifetime_attribute", text="Lifetime")


class FLIPFLUID_PT_DomainTypeWhitewaterPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Whitewater"
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
        wprops = dprops.whitewater
        is_whitewater_enabled = wprops.enable_whitewater_simulation
        show_advanced_whitewater = (wprops.whitewater_ui_mode == 'WHITEWATER_UI_MODE_ADVANCED')
        highlight_advanced = wprops.highlight_advanced_settings

        column = self.layout.column(align=True)
        column.prop(wprops, "enable_whitewater_simulation")
        column.separator()

        #
        # Settings View Mode Panel
        #
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        header, body = box.panel("whitewater_settings_view_mode", default_closed=True)

        row = header.row(align=True)
        row.label(text="Settings View Mode:")
        if body:
            column = body.column(align=True)
            row = column.row()
            row.prop(wprops, "whitewater_ui_mode", expand=True)

            split = column.split()
            split.column()
            column_right = split.column()
            column_right.enabled = show_advanced_whitewater
            column_right.prop(wprops, "highlight_advanced_settings")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(wprops, "whitewater_ui_mode", expand=True)

        #
        # Whitewater Particle Types Panel
        #
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        header, body = box.panel("whitewater_simulation_particles", default_closed=True)

        row = header.row(align=True)
        row.label(text="Whitewater Particle Types:")
        if body:
            column = body.column(align=True)
            column.enabled = is_whitewater_enabled

            row = column.row()
            row.prop(wprops, "enable_foam")
            row.prop(wprops, "enable_bubbles")
            row.prop(wprops, "enable_spray")
            row.prop(wprops, "enable_dust")
        else:
            info_text = ""
            enabled_particles = []
            if wprops.enable_foam:
                enabled_particles.append("Foam")
            if wprops.enable_bubbles:
                enabled_particles.append("Bubble")
            if wprops.enable_spray:
                enabled_particles.append("Spray")
            if wprops.enable_dust:
                enabled_particles.append("Dust")

            if enabled_particles:
                for ptype in enabled_particles:
                    info_text += ptype + "/"
                info_text = info_text.rstrip("/")
            else:
                info_text = "None"

            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=info_text)

        #
        # Emitter Settings Panel
        #
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        header, body = box.panel("whitewater_emitter_settings", default_closed=False)

        row = header.row(align=True)
        row.label(text="Emitter Settings:")
        if body:
            column = body.column(align=True)
            column.prop(wprops, "enable_whitewater_emission")

            if show_advanced_whitewater:
                column = body.column(align=True)
                column.alert = highlight_advanced
                column.prop(wprops, "whitewater_emitter_generation_rate")

            column = body.column(align=True)
            column.prop(wprops, "wavecrest_emission_rate")
            column.prop(wprops, "turbulence_emission_rate")
            column = column.column(align=True)
            column.enabled = wprops.enable_dust
            column.prop(wprops, "dust_emission_rate")

            column = body.column(align=True)
            column.prop(wprops, "spray_emission_speed", slider=True)

            if show_advanced_whitewater:
                column = body.column(align=True)
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
                column = body.column()
                row = column.row(align=True)
                row.prop(wprops.min_max_whitewater_energy_speed, "value_min")
                row.prop(wprops.min_max_whitewater_energy_speed, "value_max")

            column = body.column(align=True)
            column.prop(wprops, "max_whitewater_particles")

            if show_advanced_whitewater:
                column = body.column(align=True)
                column.alert = highlight_advanced
                column.prop(wprops, "enable_whitewater_emission_near_boundary")

            column = body.column(align=True)
            column.enabled = wprops.enable_dust
            column.prop(wprops, "enable_dust_emission_near_boundary", text="Enable Dust Emission Near Domain Floor")

        #
        # Particle Behavior Settings Panel
        #
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        header, body = box.panel("whitewater_particle_behavior_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Particle Behavior Settings:")
        if body:
            column = body.column()
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

            column = body.column(align=True)
            column.label(text="Bubble:")
            column.prop(wprops, "bubble_drag_coefficient", text="Drag Coefficient", slider=True)
            column.prop(wprops, "bubble_bouyancy_coefficient", text="Buoyancy Coefficient")

            column = body.column(align=True)
            column.label(text="Spray:")
            column.prop(wprops, "spray_drag_coefficient", text="Drag Coefficient", slider=True)

            column = body.column(align=True)
            column.enabled = wprops.enable_dust
            column.label(text="Dust:")
            column.prop(wprops, "dust_drag_coefficient", text="Drag Coefficient", slider=True)
            column.prop(wprops, "dust_bouyancy_coefficient", text="Buoyancy Coefficient")

            column = body.column(align=True)
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

        #
        # Domain Boundary Collisions Panel
        #
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        header, body = box.panel("whitewater_boundary_behaviour_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Domain Boundary Collisions:")
        if body:
            column = body.column()
            row = column.row(align=True)
            row.prop(wprops, "whitewater_boundary_collisions_mode", expand=True)

            if wprops.whitewater_boundary_collisions_mode == 'BOUNDARY_COLLISIONS_MODE_INHERIT':
                sprops = dprops.simulation
                column = box.column()
                column.enabled = False
                row = column.row(align=True)
                row.alignment = 'LEFT'
                row.prop(sprops, "fluid_boundary_collisions", index=0, text="X –")
                row.prop(sprops, "fluid_boundary_collisions", index=1, text="X+")
                row = column.row(align=True)
                row.alignment = 'LEFT'
                row.prop(sprops, "fluid_boundary_collisions", index=2, text="Y –")
                row.prop(sprops, "fluid_boundary_collisions", index=3, text="Y+")
                row = column.row(align=True)
                row.alignment = 'LEFT'
                row.prop(sprops, "fluid_boundary_collisions", index=4, text="Z –")
                row.prop(sprops, "fluid_boundary_collisions", index=5, text="Z+")
            else:
                split = column.split(align=True)
                column1 = split.column(align=True)
                column2 = split.column(align=True)
                column3 = split.column(align=True)
                column4 = split.column(align=True)

                column1.label(text="Foam:")
                row = column1.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "foam_boundary_collisions", index=0, text="X –")
                row.prop(wprops, "foam_boundary_collisions", index=1, text="X+")
                row = column1.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "foam_boundary_collisions", index=2, text="Y –")
                row.prop(wprops, "foam_boundary_collisions", index=3, text="Y+")
                row = column1.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "foam_boundary_collisions", index=4, text="Z –")
                row.prop(wprops, "foam_boundary_collisions", index=5, text="Z+")

                column2.label(text="Bubble:")
                row = column2.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "bubble_boundary_collisions", index=0, text="X –")
                row.prop(wprops, "bubble_boundary_collisions", index=1, text="X+")
                row = column2.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "bubble_boundary_collisions", index=2, text="Y –")
                row.prop(wprops, "bubble_boundary_collisions", index=3, text="Y+")
                row = column2.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "bubble_boundary_collisions", index=4, text="Z –")
                row.prop(wprops, "bubble_boundary_collisions", index=5, text="Z+")

                column3.label(text="Spray:")
                row = column3.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "spray_boundary_collisions", index=0, text="X –")
                row.prop(wprops, "spray_boundary_collisions", index=1, text="X+")
                row = column3.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "spray_boundary_collisions", index=2, text="Y –")
                row.prop(wprops, "spray_boundary_collisions", index=3, text="Y+")
                row = column3.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "spray_boundary_collisions", index=4, text="Z –")
                row.prop(wprops, "spray_boundary_collisions", index=5, text="Z+")

                column4.label(text="Dust:")
                row = column4.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "dust_boundary_collisions", index=0, text="X –")
                row.prop(wprops, "dust_boundary_collisions", index=1, text="X+")
                row = column4.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "dust_boundary_collisions", index=2, text="Y –")
                row.prop(wprops, "dust_boundary_collisions", index=3, text="Y+")
                row = column4.row(align=True)
                row.alignment = 'LEFT'
                row.prop(wprops, "dust_boundary_collisions", index=4, text="Z –")
                row.prop(wprops, "dust_boundary_collisions", index=5, text="Z+")
        else:
            info_text = ""
            if wprops.whitewater_boundary_collisions_mode == 'BOUNDARY_COLLISIONS_MODE_INHERIT':
                info_text = "Inherit"
            elif wprops.whitewater_boundary_collisions_mode == 'BOUNDARY_COLLISIONS_MODE_CUSTOM':
                info_text = "Custom"

            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=info_text)

        #
        # Obstacle Influence Settings Panel
        #
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        header, body = box.panel("whitewater_obstacle_influence_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Obstacle Influence Settings:")
        if body:
            column = body.column(align=True)

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

        _draw_whitewater_display_settings(self, context)
        _draw_geometry_attributes_menu(self, context)

        self.layout.separator()
        column = self.layout.column(align=True)
        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", icon="X").whitewater_type = 'TYPE_ALL'
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeWhitewaterPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeWhitewaterPanel)
