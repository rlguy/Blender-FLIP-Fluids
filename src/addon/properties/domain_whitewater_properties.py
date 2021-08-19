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

import bpy, os
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        EnumProperty,
        FloatProperty,
        IntProperty
        )

from .custom_properties import (
        NewMinMaxIntProperty,
        NewMinMaxFloatProperty
        )
from .. import types
from ..utils import version_compatibility_utils as vcu


class DomainWhitewaterProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    whitewater_ui_mode = EnumProperty(
            name="Whitewater UI Mode",
            description="Whitewater UI mode",
            items=types.whitewater_ui_modes,
            default='WHITEWATER_UI_MODE_BASIC',
            ); exec(conv("whitewater_ui_mode"))
    highlight_advanced_settings = BoolProperty(
            name="Highlight Advanced Settings",
            description="Highlight advanced parameters in red",
            default=False,
            ); exec(conv("highlight_advanced_settings"))
    enable_whitewater_simulation = BoolProperty(
            name="Enable Whitewater Simulation",
            description="Enable whitewater foam/bubble/spray particle solver",
            default=False,
            update=lambda self, context: self._update_enable_whitewater_simulation(context),
            options={'HIDDEN'},
            ); exec(conv("enable_whitewater_simulation"))
    enable_foam = BoolProperty(
            name="Foam",
            description="Enable solving for foam particles. Foam particles form"
                " a layer on the fluid surface and are advected with the fluid"
                " velocity. If disabled, any particles that enter the foam layer"
                " will be destroyed",
            default=True,
            ); exec(conv("enable_foam"))
    enable_bubbles = BoolProperty(
            name = "Bubbles",
            description="Enable solving for bubble particles. Bubble particles"
                " below the foam layer are advected with the fluid velocity and"
                " float towards the foam layer. If disabled, any particles that"
                " move below the foam layer will be destroyed. WARNING: Bubble"
                " particles are a large contributor to the foam layer and"
                " disabling may severely limit the amount of generated foam",
            default=True,
            ); exec(conv("enable_bubbles"))
    enable_spray = BoolProperty(
            name="Spray",
            description="Enable solving for spray particles. Spray particles"
                " above the foam layer are simulated ballistically with"
                " gravity. If disabled, any particles that move above the foam"
                " layer will be destroyed",
            default=True,
            ); exec(conv("enable_spray"))
    enable_dust = BoolProperty(
            name="Dust",
            description="Enable solving for dust particles. Dust particles are"
                " generated near obstacle surfaces and are advected with the"
                " fluid velocity while sinking towards the ground. If disabled,"
                " these particles will not be generated.",
            default=False,
            ); exec(conv("enable_dust"))
    generate_whitewater_motion_blur_data = BoolProperty(
            name="Generate Motion Blur Vectors",
            description="Generate whitewater speed vectors for motion blur"
                " rendering",
            default=False,
            ); exec(conv("generate_whitewater_motion_blur_data"))
    enable_whitewater_emission = bpy.props.BoolProperty(
            name="Enable Whitewater Emission",
            description="Allow whitewater emitters to generate new particles",
            default=True,
            ); exec(conv("enable_whitewater_emission"))
    whitewater_emitter_generation_rate = IntProperty(
            name="Emitter Generation Rate (Percent)", 
            description="Controls how many whitewater emitters are generated."
                " Emitters are generated at wavecrests and in areas high"
                " turbulence where fluid is likely to be aerated", 
            min=0, max=100,
            default=100,
            ); exec(conv("whitewater_emitter_generation_rate"))
    wavecrest_emission_rate = FloatProperty(
            name="Max Wavecrest Emission Rate", 
            description="Maximum number of whitewater particles that a"
                " single wavecrest emitter may generate per simulation second", 
            min=0, soft_max=1000,
            default=175,
            step=30,
            precision=0,
            ); exec(conv("wavecrest_emission_rate"))
    turbulence_emission_rate = FloatProperty(
            name="Max Turbulence Emission Rate", 
            description="Maximum number of whitewater particles that a"
                " single turbulence emitter may generate per simulation second", 
            min=0, soft_max=1000,
            default=175,
            step=30,
            precision=0,
            ); exec(conv("turbulence_emission_rate"))
    dust_emission_rate = FloatProperty(
            name="Max Dust Emission Rate", 
            description="Maximum number of dust particles that a"
                " single dust emitter may generate per simulation second", 
            min=0, soft_max=1000,
            default=175,
            step=30,
            precision=0,
            ); exec(conv("dust_emission_rate"))
    spray_emission_speed = FloatProperty(
            name="Spray Emission Speed", 
            description="Speed scaling factor for spray particle emission. Increasing"
                " this value will generate more spread out and exaggerated spray effects", 
            min=1.0, soft_max=3.0,
            default=1.0,
            ); exec(conv("spray_emission_speed"))
    min_max_whitewater_energy_speed = NewMinMaxFloatProperty(
            name_min="Min Energy Speed", 
            description_min="Fluid with speed less than this value will generate"
                " no whitewater", 
            min_min=0,
            default_min=0.2,
            precision_min=2,

            name_max="Max Energy Speed", 
            description_max="When fluid speed is greater than the min value, and"
                " less than the max value, proportionally increase the amount"
                " of whitewater emitted based on emission rate of the emitter", 
            min_max=0,
            default_max=3.0,
            precision_max=2,
            ); exec(conv("min_max_whitewater_energy_speed"))
    min_max_whitewater_wavecrest_curvature = NewMinMaxFloatProperty(
            name_min="Min Curvature", 
            description_min="Wavecrests with curvature less than this value will"
                " generate no whitewater. This value rarely needs to be changed", 
            min_min=0.0, max_min=5.0,
            default_min=0.4,
            precision_min=2,

            name_max="Max Curvature", 
            description_max="When wavecrest curvature is greater than the min value,"
                " and less than the max value, proportionally increase the amount"
                " of whitewater emitted based on the Wavecrest Emission Rate."
                " This value rarely needs to be changed", 
            min_max=0.0, max_max=5.0,
            default_max=1.0,
            precision_max=2,
            ); exec(conv("min_max_whitewater_wavecrest_curvature"))
    min_max_whitewater_turbulence = NewMinMaxFloatProperty(
            name_min="Min Turbulence", 
            description_min="Fluid with turbulence less than this value will"
                " generate no whitewater. This value rarely needs to be changed", 
            min_min=0,
            default_min=100,
            precision_min=0,

            name_max="Max Turbulence", 
            description_max="When the fluid turbulence is greater than the min value,"
                " and less than the max value, proportionally increase the amount"
                " of whitewater emitted based on the Turbulence Emission Rate."
                " This value rarely needs to be changed", 
            min_max=0,
            default_max=200,
            precision_max=0,
            ); exec(conv("min_max_whitewater_turbulence"))
    max_whitewater_particles = FloatProperty(
            name="Max Particles (in millions)", 
            description="Maximum number of whitewater particles (in millions)"
                " to simulate. The solver will stop generating new whitewater"
                " particles to prevent exceeding this limit", 
            min=0, max=2000,
            default=12,
            precision=2,
            ); exec(conv("max_whitewater_particles"))
    enable_whitewater_emission_near_boundary = BoolProperty(
            name="Enable Emission Near Domain Boundary",
            description="Allow whitewater emitters to generate particles at"
                " the domain boundary",
            default=True,
            ); exec(conv("enable_whitewater_emission_near_boundary"))
    enable_dust_emission_near_boundary = BoolProperty(
            name="Enable Dust Emission Near Domain Boundary",
            description="Allow whitewater emitters to generate dust particles near"
                " the domain floor",
            default=False,
            ); exec(conv("enable_dust_emission_near_boundary"))
    min_max_whitewater_lifespan = NewMinMaxFloatProperty(
            name_min="Min Lifespan", 
            description_min="Minimum whitewater particle lifespan in seconds", 
            min_min=0.0,
            default_min=0.5,
            precision_min=2,

            name_max="Max Lifespan", 
            description_max="Maximum whitewater particle lifespan in seconds", 
            min_max=0.0,
            default_max=6.0,
            precision_max=2,
            ); exec(conv("min_max_whitewater_lifespan"))
    whitewater_lifespan_variance = FloatProperty(
            name="Lifespan Variance", 
            description ="A random number of seconds in this range will be added"
                " or subtracted from the whitewater particle lifespan", 
            min=0.0,
            default=3.0,
            precision=2,
            ); exec(conv("whitewater_lifespan_variance"))
    foam_lifespan_modifier = FloatProperty(
            name="Foam Lifespan Modifier", 
            description="Multiply the lifespan of a foam particle by this value", 
            min=0.0,
            default=1.0,
            precision=1,
            ); exec(conv("foam_lifespan_modifier"))
    bubble_lifespan_modifier = FloatProperty(
            name="Bubble Lifespan Modifier", 
            description="Multiply the lifespan of a bubble particle by this value", 
            min=0.0,
            default=4.0,
            precision=1,
            ); exec(conv("bubble_lifespan_modifier"))
    spray_lifespan_modifier = FloatProperty(
            name="Spray Lifespan Modifier", 
            description="Multiply the lifespan of a spray particle by this value", 
            min=0.0,
            default=5.0,
            precision=1,
            ); exec(conv("spray_lifespan_modifier"))
    dust_lifespan_modifier = FloatProperty(
            name="Dust Lifespan Modifier", 
            description="Multiply the lifespan of a dust particle by this value", 
            min=0.0,
            default=2.0,
            precision=1,
            ); exec(conv("dust_lifespan_modifier"))
    foam_advection_strength = FloatProperty(
            name="Foam Advection Strength", 
            description="Controls how much the foam moves along with the motion"
                " of the fluid surface. High values cause tighter streaks of"
                " foam that closely follow the fluid motion. Lower values will"
                " cause more diffuse and spread out foam", 
            min=0.0, max=1.0,
            default=1.0,
            precision=2,
            subtype='FACTOR',
            ); exec(conv("foam_advection_strength"))
    foam_layer_depth = FloatProperty(
            name="Foam Layer Depth", 
            description="Set the thickness of the whitewater foam layer", 
            min=0.0,
            max=1.0,
            default=0.8,
            precision=2,
            subtype='FACTOR',
            ); exec(conv("foam_layer_depth"))
    foam_layer_offset = FloatProperty(
            name="Foam Layer Offset", 
            description="Set the offset of the whitewater foam layer above/below"
                " the fluid surface. If set to a value of 1, the foam layer will"
                " rest entirely above the fluid surface. A value of -1 will have"
                " the foam layer rest entirely below the fluid surface", 
            min=-1.0,
            max=1.0,
            default=0.5,
            precision=2,
            subtype='FACTOR',
            ); exec(conv("foam_layer_offset"))
    preserve_foam = BoolProperty(
            name="Preserve Foam",
            description="Increase the lifespan of foam particles based on the"
                " local density of foam particles, which can help create clumps"
                " and streaks of foam on the liquid surface over time",
            default=True,
            ); exec(conv("preserve_foam"))
    foam_preservation_rate = FloatProperty(
            name="Foam Preservation Rate", 
            description="Rate to add to the lifetime of preserved foam. This"
                " value is the number of seconds to add per second, so if"
                " greater than one can effectively preserve high density foam"
                " clumps from every being killed", 
            default=0.75,
            precision=2,
            ); exec(conv("foam_preservation_rate"))
    min_max_foam_density = NewMinMaxIntProperty(
            name_min="Min Foam Density", 
            description_min="Foam densities less than this value will not increase"
                " the lifetime of a foam particle. Foam density units are in"
                " number of particles per grid cell", 
            min_min=0,
            default_min=20,

            name_max="Max Foam Density", 
            description_max="Foam densities that are greater than the min value,"
                " and less than the max value, proportionally increase the"
                " particle lifetime based on the Foam Preservation Rate. Foam"
                " density units are in number of particles per grid cell", 
            min_max=0,
            default_max=45,
            ); exec(conv("min_max_foam_density"))
    bubble_drag_coefficient = FloatProperty(
            name="Bubble Drag Coefficient", 
            description="Controls how quickly bubble particles are dragged with"
                " the fluid velocity. If set to 1, bubble particles will be"
                " immediately dragged into the flow direction of the fluid", 
            min=0.0, max=1.0,
            default=0.8,
            precision=2,
            subtype='FACTOR',
            ); exec(conv("bubble_drag_coefficient"))
    bubble_bouyancy_coefficient = FloatProperty(
            name="Bubble Bouyancy Coefficient", 
            description="Controls how quickly bubble particles float towards"
                " the fluid surface. If set to a negative value, bubbles will"
                " sink away from the fluid surface", 
            default=2.5,
            precision=2,
            step=0.3,
            ); exec(conv("bubble_bouyancy_coefficient"))
    spray_drag_coefficient = FloatProperty(
            name="Spray Drag Coefficient", 
            description="Controls amount of air resistance on a spray particle", 
            min=0.0, max=5.0,
            default=3.0,
            precision=2,
            ); exec(conv("spray_drag_coefficient"))
    dust_drag_coefficient = FloatProperty(
            name="Dust Drag Coefficient", 
            description="Controls how quickly dust particles are dragged with"
                " the fluid velocity. If set to 1, dust particles will be"
                " immediately dragged into the flow direction of the fluid", 
            min=0.0, max=1.0,
            default=0.75,
            precision=2,
            subtype='FACTOR',
            ); exec(conv("dust_drag_coefficient"))
    dust_bouyancy_coefficient = FloatProperty(
            name="Dust Bouyancy Coefficient", 
            description="Controls how quickly dust particles sink towards"
                " the ground. Decreasing this value will cause particles to sink"
                " more quickly. If set to a positive value, dust will float towards"
                " fluid surface.", 
            default=-3.0,
            precision=2,
            step=0.3,
            ); exec(conv("dust_bouyancy_coefficient"))
    foam_boundary_behaviour = EnumProperty(
            name="Foam Behaviour At Limits",
            description="Specifies the foam particle behavior when hitting the"
                " domain boundary",
            items=types.boundary_behaviours,
            default='BEHAVIOUR_COLLIDE',
            ); exec(conv("foam_boundary_behaviour"))
    bubble_boundary_behaviour = EnumProperty(
            name="Bubble Behaviour At Limits",
            description="Specifies the bubble particle behavior when hitting"
                " the domain boundary",
            items=types.boundary_behaviours,
            default='BEHAVIOUR_COLLIDE',
            ); exec(conv("bubble_boundary_behaviour"))
    spray_boundary_behaviour = EnumProperty(
            name="Spray Behaviour At Limits",
            description="Specifies the spray particle behavior when hitting the"
                " domain boundary",
            items=types.boundary_behaviours,
            default='BEHAVIOUR_COLLIDE',
            ); exec(conv("spray_boundary_behaviour"))
    foam_boundary_active = BoolVectorProperty(
            name="",
            description="Activate behaviour on the corresponding side of the domain",
            default=(True, True, True, True, False, True),
            size=6,
            ); exec(conv("foam_boundary_active"))
    bubble_boundary_active = BoolVectorProperty(
            name="",
            description="Activate behaviour on the corresponding side of the domain",
            default=(True, True, True, True, False, True),
            size=6,
            ); exec(conv("bubble_boundary_active"))
    spray_boundary_active = BoolVectorProperty(
            name="",
            description="Activate behaviour on the corresponding side of the domain",
            default=(True, True, True, True, False, True),
            size=6,
            ); exec(conv("spray_boundary_active"))
    obstacle_influence_base_level = FloatProperty(
            name="Influence Base Level", 
            description="The default value of whitewater influence. If a location"
                " is not affected by an obstacle's influence, the amount"
                " of whitewater generated at this location will be scaled by"
                " this value. A value of 1.0 will generate a normal amount"
                " of whitewater, a value greater than 1.0 will generate more,"
                " a value less than 1.0 will generate less",
            min=0.0,
            default=1.0,
            precision=2,
            ); exec(conv("obstacle_influence_base_level"))
    obstacle_influence_decay_rate = FloatProperty(
            name="Influence Decay Rate", 
            description="The rate at which influence will decay towards the"
                " base level. If a keyframed/animated obstacle leaves an"
                " influence above/below the base level at some location," 
                " the value of influence at this location will adjust towards"
                " the base level value at this rate. This value is in amount" 
                " of influence per second",
            min=0.0,
            default=5.0,
            precision=2,
            ); exec(conv("obstacle_influence_decay_rate"))

    emitter_settings_expanded = BoolProperty(default=True); exec(conv("emitter_settings_expanded"))
    particle_settings_expanded = BoolProperty(default=False); exec(conv("particle_settings_expanded"))
    boundary_behaviour_settings_expanded = BoolProperty(default=False); exec(conv("boundary_behaviour_settings_expanded"))
    obstacle_settings_expanded = BoolProperty(default=False); exec(conv("obstacle_settings_expanded"))
    whitewater_display_settings_expanded = BoolProperty(default=False); exec(conv("whitewater_display_settings_expanded"))


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".enable_whitewater_simulation",             "Enable Whitewater",              group_id=0)
        add(path + ".enable_foam",                              "Enable Foam",                    group_id=0)
        add(path + ".enable_bubbles",                           "Enable Bubbles",                 group_id=0)
        add(path + ".enable_spray",                             "Enable Spray",                   group_id=0)
        add(path + ".enable_dust",                              "Enable Dust",                    group_id=0)
        add(path + ".generate_whitewater_motion_blur_data",     "Generate Motion Blur Data",      group_id=0)
        add(path + ".enable_whitewater_emission",               "Enable Emission",                group_id=0)
        add(path + ".whitewater_emitter_generation_rate",       "Emission Rate",                  group_id=0)
        add(path + ".wavecrest_emission_rate",                  "Wavecrest Emission Rate",        group_id=0)
        add(path + ".turbulence_emission_rate",                 "Turbulence Emission Rate",       group_id=0)
        add(path + ".dust_emission_rate",                       "Dust Emission Rate",             group_id=0)
        add(path + ".spray_emission_speed",                     "Spray Emission Speed",           group_id=0)
        add(path + ".min_max_whitewater_energy_speed",          "Min-Max Energy Speed",           group_id=0)
        add(path + ".min_max_whitewater_wavecrest_curvature",   "Min-Max Curvature",              group_id=0)
        add(path + ".min_max_whitewater_turbulence",            "Min-Max Turbulence",             group_id=0)
        add(path + ".max_whitewater_particles",                 "Max Particles",                  group_id=0)
        add(path + ".enable_whitewater_emission_near_boundary", "Emit Near Boundary",             group_id=0)
        add(path + ".enable_dust_emission_near_boundary",       "Emit Dust Near Boundary",        group_id=0)
        add(path + ".min_max_whitewater_lifespan",              "Min-Max Lifespane",              group_id=1)
        add(path + ".whitewater_lifespan_variance",             "Lifespan Variance",              group_id=1)
        add(path + ".foam_lifespan_modifier",                   "Foam Lifespan Modifier",         group_id=1)
        add(path + ".bubble_lifespan_modifier",                 "Bubble Lifespan Modifier",       group_id=1)
        add(path + ".spray_lifespan_modifier",                  "Spray Lifespan Modifier",        group_id=1)
        add(path + ".dust_lifespan_modifier",                   "Dust Lifespan Modifier",         group_id=1)
        add(path + ".foam_advection_strength",                  "Foam Advection Strength",        group_id=1)
        add(path + ".foam_layer_depth",                         "Foam Depth",                     group_id=1)
        add(path + ".foam_layer_offset",                        "Foam Offset",                    group_id=1)
        add(path + ".preserve_foam",                            "Preserve Foam",                  group_id=1)
        add(path + ".foam_preservation_rate",                   "Preservation Rate",              group_id=1)
        add(path + ".min_max_foam_density",                     "Min-Max Density",                group_id=1)
        add(path + ".bubble_drag_coefficient",                  "Bubble Drag",                    group_id=2)
        add(path + ".bubble_bouyancy_coefficient",              "Bubble Bouyancy",                group_id=2)
        add(path + ".spray_drag_coefficient",                   "Spray Drag",                     group_id=2)
        add(path + ".dust_drag_coefficient",                    "Dust Drag",                      group_id=2)
        add(path + ".dust_bouyancy_coefficient",                "Dust Bouyancy",                  group_id=2)
        add(path + ".foam_boundary_behaviour",                  "Foam Boundary Behaviour",        group_id=2)
        add(path + ".bubble_boundary_behaviour",                "Bubble Boundary Behaviour",      group_id=2)
        add(path + ".spray_boundary_behaviour",                 "Spray Boundary Behaviour",       group_id=2)
        add(path + ".foam_boundary_active",                     "Foam Boundary X–/+ Y–/+ Z–/+",   group_id=2)
        add(path + ".bubble_boundary_active",                   "Bubble Boundary X–/+ Y–/+ Z–/+", group_id=2)
        add(path + ".spray_boundary_active",                    "Spray Boundary X–/+ Y–/+ Z–/+",  group_id=2)
        add(path + ".obstacle_influence_base_level",            "Obstacle Influence Base Level",  group_id=2)
        add(path + ".obstacle_influence_decay_rate",            "Obstacle Influence Base Level",  group_id=2)


    def _update_enable_whitewater_simulation(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.enable_whitewater_simulation:
            dprops.mesh_cache.initialize_cache_objects()
            dprops.materials.whitewater_foam_material = dprops.materials.whitewater_foam_material
            dprops.materials.whitewater_bubble_material = dprops.materials.whitewater_bubble_material
            dprops.materials.whitewater_spray_material = dprops.materials.whitewater_spray_material
        else:
            dprops.mesh_cache.delete_whitewater_cache_objects()


def register():
    bpy.utils.register_class(DomainWhitewaterProperties)


def unregister():
    bpy.utils.unregister_class(DomainWhitewaterProperties)