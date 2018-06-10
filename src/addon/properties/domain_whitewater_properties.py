# Blender FLIP Fluid Add-on
# Copyright (C) 2018 Ryan L. Guy
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


class DomainWhitewaterProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.enable_whitewater_simulation = BoolProperty(
                name="Enable Whitewater Simulation",
                description="Enable whitewater foam/bubble/spray particle solver",
                default=False,
                update=lambda self, context: self._update_enable_whitewater_simulation(context),
                options={'HIDDEN'},
                )
        cls.enable_foam = BoolProperty(
                name="Foam",
                description="Enable solving for foam particles. Foam particles form"
                    " a layer on the fluid surface and are advected with the fluid"
                    " velocity. If disabled, any particles that enter the foam layer"
                    " will be destroyed.",
                default=True,
                )
        cls.enable_bubbles = BoolProperty(
                name = "Bubbles",
                description="Enable solving for bubble particles. Bubble particles"
                    " below the foam layer are advected with the fluid velocity and"
                    " float towards the foam layer. If disabled, any particles that"
                    " move below the foam layer will be destroyed. WARNING: Bubble"
                    " particles are a large contributor to the foam layer and"
                    " disabling may severely limit the amount of generated foam.",
                default=True,
                )
        cls.enable_spray = BoolProperty(
                name="Spray",
                description="Enable solving for spray particles. Spray particles"
                    " above the foam layer are simulated ballistically with"
                    " gravity. If disabled, any particles that move above the foam"
                    " layer will be destroyed.",
                default=True,
                )
        cls.enable_whitewater_emission = bpy.props.BoolProperty(
                name="Enable Whitewater Emission",
                description="Allow whitewater emitters to generate new particles",
                default=True,
                )
        cls.whitewater_emitter_generation_rate = IntProperty(
                name="Emitter Generation Rate", 
                description="Controls how many whitewater emitters are generated."
                    " Emitters are generated at wavecrests and in areas high"
                    " turbulence where fluid is likely to be aerated.", 
                min=0, max=100,
                default=100,
                subtype='PERCENTAGE',
                )
        cls.wavecrest_emission_rate = FloatProperty(
                name="Wavecrest Emission Rate", 
                description="Maximum number of whitewater particles that a"
                    " wavecrest emitter may generate per simulation second", 
                min=0, soft_max=1000,
                default=175,
                step=30,
                precision=0,
                )
        cls.turbulence_emission_rate = FloatProperty(
                name="Turbulence Emission Rate", 
                description="Maximum number of whitewater particles that a"
                    " turbulence emitter may generate per simulation second", 
                min=0, soft_max=1000,
                default=175,
                step=30,
                precision=0,
                )
        cls.min_max_whitewater_energy_speed = NewMinMaxFloatProperty(
                name_min="Min Energy Speed", 
                description_min="Fluid with speed less than this value will generate"
                    " no whitewater", 
                min_min=0,
                default_min=0.5,
                precision_min=1,

                name_max="Max Energy Speed", 
                description_max="When fluid speed is greater than the min value, and"
                    " less than the max value, proportionally increase the amount"
                    " of whitewater emitted based on emission rate of the emitter", 
                min_max=0,
                default_max=10.0,
                precision_max=1,
                )
        cls.min_max_whitewater_wavecrest_curvature = NewMinMaxFloatProperty(
                name_min="Min Curvature", 
                description_min="Wavecrests with curvature less than this value will"
                    " generate no whitewater", 
                default_min=0.4,
                precision_min=2,

                name_max="Max Curvature", 
                description_max="When wavecrest curvature is greater than the min value,"
                    " and less than the max value, proportionally increase the amount"
                    " of whitewater emitted based on the Wavecrest Emission Rate", 
                default_max=1.0,
                precision_max=2,
                )
        cls.min_max_whitewater_turbulence = NewMinMaxFloatProperty(
                name_min="Min Turbulence", 
                description_min="Fluid with turbulence less than this value will"
                    " generate no whitewater", 
                min_min=0,
                default_min=100,
                precision_min=0,

                name_max="Max Turbulence", 
                description_max="When the fluid turbulence is greater than the min value,"
                    " and less than the max value, proportionally increase the amount"
                    " of whitewater emitted based on the Turbulence Emission Rate", 
                min_max=0,
                default_max=200,
                precision_max=0,
                )
        cls.max_whitewater_particles = FloatProperty(
                name="Max Particles (in millions)", 
                description="Maximum number of whitewater particles (in millions)"
                    " to simulate. The solver will stop generating new whitewater"
                    " particles to prevent exceeding this limit.", 
                min=0, max=2000,
                default=12,
                precision=2,
                )
        cls.enable_whitewater_emission_near_boundary = BoolProperty(
                name="Enable Emission Near Domain Boundary",
                description="Allow whitewater emitters to generate particles at"
                    " the domain boundary",
                default = True,
                )
        cls.min_max_whitewater_lifespan = NewMinMaxFloatProperty(
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
                )
        cls.whitewater_lifespan_variance = FloatProperty(
                name="Lifespan Variance", 
                description ="A random number of seconds in this range will be added"
                    " or subtracted from the whitewater particle lifespan", 
                min=0.0,
                default=3.0,
                precision=2,
                )
        cls.foam_lifespan_modifier = FloatProperty(
                name="Foam Lifespan Modifier", 
                description="Multiply the lifespan of a foam particle by this value", 
                min=0.0,
                default=1.0,
                precision=1,
                )
        cls.bubble_lifespan_modifier = FloatProperty(
                name="Bubble Lifespan Modifier", 
                description="Multiply the lifespan of a bubble particle by this value", 
                min=0.0,
                default=4.0,
                precision=1,
                )
        cls.spray_lifespan_modifier = FloatProperty(
                name="Spray Lifespan Modifier", 
                description="Multiply the lifespan of a spray particle by this value", 
                min=0.0,
                default=5.0,
                precision=1,
                )
        cls.foam_advection_strength = FloatProperty(
                name="Foam Advection Strength", 
                description="Controls how much the foam moves along with the motion"
                    " of the fluid surface. High values cause tighter streaks of"
                    " foam that closely follow the fluid motion. Lower values will"
                    " cause more diffuse and spread out foam.", 
                min=0.0, max=1.0,
                default=1.0,
                precision=2,
                subtype='FACTOR',
                )
        cls.foam_layer_depth = FloatProperty(
                name="Foam Layer Depth", 
                description="Set the thickness of the whitewater foam layer.", 
                min=0.0,
                max=1.0,
                default=1.0,
                precision=2,
                subtype='FACTOR',
                )
        cls.foam_layer_offset = FloatProperty(
                name="Foam Layer Offset", 
                description="Set the offset of the whitewater foam layer above/below"
                    " the fluid surface. If set to a value of 1, the foam layer will"
                    " rest entirely above the fluid surface. A value of -1 will have"
                    " the foam layer rest entirely below the fluid surface.", 
                min=-1.0,
                max=1.0,
                default=0.5,
                precision=2,
                subtype='FACTOR',
                )
        cls.preserve_foam = BoolProperty(
                name="Preserve Foam",
                description="Increase the lifespan of foam particles based on the"
                    " local density of foam particles, which can help create clumps"
                    " and streaks of foam on the liquid surface over time",
                default=False,
                )
        cls.foam_preservation_rate = FloatProperty(
                name="Foam Preservation Rate", 
                description="Rate to add to the lifetime of preserved foam. This"
                    " value is the number of seconds to add per second, so if"
                    " greater than one can effectively preserve high density foam"
                    " clumps from every being killed.", 
                default=0.75,
                precision=2,
                )
        cls.min_max_foam_density = NewMinMaxIntProperty(
                name_min="Min Foam Density", 
                description_min="Foam densities less than this value will not increase"
                    " the lifetime of a foam particle. Foam density units are in"
                    " number of particles per grid cell.", 
                min_min=0,
                default_min=20,

                name_max="Max Foam Density", 
                description_max="Foam densities that are greater than the min value,"
                    " and less than the max value, proportionally increase the"
                    " particle lifetime based on the Foam Preservation Rate. Foam"
                    " density units are in number of particles per grid cell.", 
                min_max=0,
                default_max=45,
                )
        cls.bubble_drag_coefficient = FloatProperty(
                name="Bubble Drag Coefficient", 
                description="Controls how quickly bubble particles are dragged with"
                    " the fluid velocity. If set to 1, bubble particles will be"
                    " immediately dragged into the flow direction of the fluid.", 
                min=0.0, max=1.0,
                default=0.8,
                precision=2,
                subtype='FACTOR',
                )
        cls.bubble_bouyancy_coefficient = FloatProperty(
                name="Bubble Bouyancy Coefficient", 
                description="Controls how quickly bubble particles float towards"
                    " the fluid surface. If set to a negative value, bubbles will"
                    " sink away from the fluid surface.", 
                default=2.5,
                precision=2,
                step=0.3,
                )
        cls.spray_drag_coefficient = FloatProperty(
                name="Spray Drag Coefficient", 
                description="Controls amount of air resistance on a spray particle", 
                min=0.0, max=5.0,
                default=0.5,
                precision=2,
                )
        cls.foam_boundary_behaviour = EnumProperty(
                name="Foam Behaviour At Limits",
                description="Specifies the foam particle behavior when hitting the"
                    " domain boundary",
                items=types.boundary_behaviours,
                default='BEHAVIOUR_COLLIDE',
                )
        cls.bubble_boundary_behaviour = EnumProperty(
                name="Bubble Behaviour At Limits",
                description="Specifies the bubble particle behavior when hitting"
                    " the domain boundary",
                items=types.boundary_behaviours,
                default='BEHAVIOUR_COLLIDE',
                )
        cls.spray_boundary_behaviour = EnumProperty(
                name="Spray Behaviour At Limits",
                description="Specifies the spray particle behavior when hitting the"
                    " domain boundary",
                items=types.boundary_behaviours,
                default='BEHAVIOUR_COLLIDE',
                )
        cls.foam_boundary_active = BoolVectorProperty(
                name="",
                description="Activate behaviour on the corresponding side of the domain",
                default=(True, True, True, True, False, True),
                size=6,
                )
        cls.bubble_boundary_active = BoolVectorProperty(
                name="",
                description="Activate behaviour on the corresponding side of the domain",
                default=(True, True, True, True, False, True),
                size=6,
                )
        cls.spray_boundary_active = BoolVectorProperty(
                name="",
                description="Activate behaviour on the corresponding side of the domain",
                default=(True, True, True, True, False, True),
                size=6,
                )


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".enable_whitewater_simulation",             "Enable Whitewater",              group_id=0)
        add(path + ".enable_foam",                              "Enable Foam",                    group_id=0)
        add(path + ".enable_bubbles",                           "Enable Bubbles",                 group_id=0)
        add(path + ".enable_spray",                             "Enable Spray",                   group_id=0)
        add(path + ".enable_whitewater_emission",               "Enable Emission",                group_id=0)
        add(path + ".whitewater_emitter_generation_rate",       "Emission Rate",                  group_id=0)
        add(path + ".wavecrest_emission_rate",                  "Wavecrest Emission Rate",        group_id=0)
        add(path + ".turbulence_emission_rate",                 "Turbulence Emission Rate",       group_id=0)
        add(path + ".min_max_whitewater_energy_speed",          "Min-Max Energy Speed",           group_id=0)
        add(path + ".min_max_whitewater_wavecrest_curvature",   "Min-Max Curvature",              group_id=0)
        add(path + ".min_max_whitewater_turbulence",            "Min-Max Turbulence",             group_id=0)
        add(path + ".max_whitewater_particles",                 "Max Particles",                  group_id=0)
        add(path + ".enable_whitewater_emission_near_boundary", "Emit Near Boundary",             group_id=0)
        add(path + ".min_max_whitewater_lifespan",              "Min-Max Lifespane",              group_id=1)
        add(path + ".whitewater_lifespan_variance",             "Lifespan Variance",              group_id=1)
        add(path + ".foam_lifespan_modifier",                   "Foam Lifespan Modifier",         group_id=1)
        add(path + ".bubble_lifespan_modifier",                 "Bubble Lifespan Modifier",       group_id=1)
        add(path + ".spray_lifespan_modifier",                  "Spray Lifespan Modifier",        group_id=1)
        add(path + ".foam_advection_strength",                  "Foam Advection Strength",        group_id=1)
        add(path + ".foam_layer_depth",                         "Foam Depth",                     group_id=1)
        add(path + ".foam_layer_offset",                        "Foam Offset",                    group_id=1)
        add(path + ".preserve_foam",                            "Preserve Foam",                  group_id=1)
        add(path + ".foam_preservation_rate",                   "Preservation Rate",              group_id=1)
        add(path + ".min_max_foam_density",                     "Min-Max Density",                group_id=1)
        add(path + ".bubble_drag_coefficient",                  "Bubble Drag",                    group_id=2)
        add(path + ".bubble_bouyancy_coefficient",              "Bubble Bouyancy",                group_id=2)
        add(path + ".spray_drag_coefficient",                   "Spray Drag",                     group_id=2)
        add(path + ".foam_boundary_behaviour",                  "Foam Boundary Behaviour",        group_id=2)
        add(path + ".bubble_boundary_behaviour",                "Bubble Boundary Behaviour",      group_id=2)
        add(path + ".spray_boundary_behaviour",                 "Spray Boundary Behaviour",       group_id=2)
        add(path + ".foam_boundary_active",                     "Foam Boundary X–/+ Y–/+ Z–/+",   group_id=2)
        add(path + ".bubble_boundary_active",                   "Bubble Boundary X–/+ Y–/+ Z–/+", group_id=2)
        add(path + ".spray_boundary_active",                    "Spray Boundary X–/+ Y–/+ Z–/+",  group_id=2)


    def _update_enable_whitewater_simulation(self, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.enable_whitewater_simulation:
            dprops.mesh_cache.initialize_cache_objects()
            m = dprops.materials.whitewater_foam_material
            dprops.materials.whitewater_foam_material = dprops.materials.whitewater_foam_material
            dprops.materials.whitewater_bubble_material = dprops.materials.whitewater_bubble_material
            dprops.materials.whitewater_spray_material = dprops.materials.whitewater_spray_material
        else:
            dprops.mesh_cache.delete_whitewater_cache_objects(domain_object)


def register():
    bpy.utils.register_class(DomainWhitewaterProperties)


def unregister():
    bpy.utils.unregister_class(DomainWhitewaterProperties)