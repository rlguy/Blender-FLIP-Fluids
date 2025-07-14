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
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        EnumProperty,
        PointerProperty
        )

from ..objects import flip_fluid_cache
from ..utils import version_compatibility_utils as vcu


class DomainParticlesProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    enable_fluid_particle_output = BoolProperty(
            name="Enable Fluid Particle Export",
            description="Enable fluid particle data to be exported to the simulation cache",
            default=False,
            update=lambda self, context: self._update_enable_fluid_particle_output(context),
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_output"))
    fluid_particle_output_amount = FloatProperty(
            name="Particle Export Amount", 
            description="Amount of fluid particles to export. A value of 1.0 will export all fluid particles."
                " Decrease this value to reduce cache size if not all particles will need to be displayed or"
                " rendered. The number of particles to display/render can be further reduced in the display settings", 
            soft_min=0.001, 
            min=0.00001, max=1.0,
            default=1.0,
            precision=5,
            subtype='FACTOR',
            options={'HIDDEN'},
            ); exec(conv("fluid_particle_output_amount"))
    enable_fluid_particle_surface_output = BoolProperty(
            name="Export Surface Particles",
            description="Export fluid particles near the fluid surface. Particles are considered"
                " to be surface particles if they are near empty air, but are not near the domain boundary",
            default=True,
            ); exec(conv("enable_fluid_particle_surface_output"))
    enable_fluid_particle_boundary_output = BoolProperty(
            name="Export Boundary Particles",
            description="Export fluid particles near the domain boundary. Particles are considered to"
                " be boundary particles if they are near the boundary of the domain. If a surface"
                " Meshing Volume object is set, particles near the surface of this object are considered"
                " boundary particles",
            default=True,
            ); exec(conv("enable_fluid_particle_boundary_output"))
    enable_fluid_particle_interior_output = BoolProperty(
            name="Export Interior Particles",
            description="Export fluid particles inside of the fluid surface. Particles are considered"
                " to be interior particles if they are not classified as either surface or boundary particles",
            default=True,
            ); exec(conv("enable_fluid_particle_interior_output"))
    fluid_particle_source_id_blacklist = IntProperty(
            name="Skip Source ID",
            description="If the Source ID attribute is enabled, do not export fluid particles with the specified"
                " Source ID value. Useful to reduce cache size and speed up playback in situations where particles"
                " are not needed from specific Fluid or Inflow objects",
            min=-1,
            default=-1,
            ); exec(conv("fluid_particle_source_id_blacklist"))
    enable_fluid_particle_velocity_vector_attribute = BoolProperty(
            name="Generate Velocity Attributes",
            description="Generate fluid 3D velocity vector attributes for the fluid particles. After"
                " baking, the velocity vectors (in m/s) can be accessed in a Cycles Attribute"
                " Node or in Geometry Nodes with the name 'flip_velocity' from the Vector output."
                " This attribute is required for motion blur rendering. If the velocity"
                " direction is not needed, use Generate Speed Attributes instead",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_velocity_vector_attribute"))
    enable_fluid_particle_speed_attribute = BoolProperty(
            name="Generate Speed Attributes",
            description="Generate fluid speed attributes for the fluid particles. After"
                " baking, the speed values (in m/s) can be accessed in a Cycles Attribute"
                " Node or in Geometry Nodes with the name 'flip_speed' from the Fac output",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_speed_attribute"))
    enable_fluid_particle_vorticity_vector_attribute = BoolProperty(
            name="Generate Vorticity Attributes",
            description="Generate fluid 3D vorticity vector attributes for the fluid particles. After"
                " baking, the vorticity vectors can be accessed in a Cycles Attribute"
                " Node or in Geometry Nodes with the name 'flip_vorticity' from the Vector output",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_vorticity_vector_attribute"))
    enable_fluid_particle_color_attribute = BoolProperty(
            name="Generate Color Attributes",
            description="Generate fluid color attributes for the fluid particles. Each"
                " Inflow/Fluid object can set to assign color to the generated fluid. After"
                " baking, the color values can be accessed in a Cycles Attribute Node or in Geometry Nodes"
                " with the name 'flip_color' from the Color output. This can be used to create varying color"
                " liquid effects",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_color_attribute"))
    enable_fluid_particle_age_attribute = BoolProperty(
            name="Generate Age Attributes",
            description="Generate fluid age attributes for the fluid particles."
                " The age attribute starts at 0.0 when the liquid is spawned and counts up in"
                " seconds. After baking, the age values can be accessed in a Cycles Attribute"
                " Node or in Geometry Nodes with the name 'flip_age' from the Fac output",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_age_attribute"))
    enable_fluid_particle_lifetime_attribute = BoolProperty(
            name="Generate Lifetime Attributes",
            description="Generate fluid lifetime attributes for the fluid particles. This attribute allows the"
                " fluid to start with a lifetime value that counts down in seconds and once the lifetime reaches 0,"
                " the fluid is removed from the simulation. Each Inflow/Fluid object can be set to assign a"
                " starting lifetime to the generated fluid. After baking, the lifetime remaining values"
                " can be accessed in a Cycles Attribute Node or in Geometry Nodes with the name 'flip_lifetime' from"
                " the Fac output",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_lifetime_attribute"))
    enable_fluid_particle_whitewater_proximity_attribute = BoolProperty(
            name="Generate Whitewater Proximity Attributes",
            description="Generate whitewater proximity attributes for the fluid particles. The attribute values represent"
                " how many foam, bubble, or spray particles are near a fluid particle and can be used in a material to shade"
                " particles that are near whitewater particles. After baking, the proximity attribute can be accessed"
                " in a Cycles Attribute Node or in Geometry Nodes with the names 'flip_foam_proximity', 'flip_bubble_proximity',"
                " and 'flip_spray_proximity' from the Fac output",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_whitewater_proximity_attribute"))
    enable_fluid_particle_source_id_attribute = BoolProperty(
            name="Generate Source ID Attributes",
            description="Generate fluid source identifiers for the fluid particles. Each"
                " Inflow/Fluid object can set to assign a source ID to the generated particles. After"
                " baking, the ID values can be accessed in a Cycles Attribute Node or in Geometry nodes with the name"
                " 'flip_source_id' from the Fac output. This can be used to identifty fluid from"
                " different sources in a material or geometry node group. Warning: this attribute is"
                " not supported with sheeting effects or resolution upscaling features",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_source_id_attribute"))
    enable_fluid_particle_uid_attribute = BoolProperty(
            name="Generate UID Attributes",
            description="Generate Unique IDs for fluid particles. After"
                " baking, the UID values can be accessed in a Cycles Attribute Node or in Geometry nodes with the name"
                " 'flip_uid' from the Fac output. This can be used to uniquely identify particles which can be useful"
                " for attribute storage and tracking in simulation nodes. Warning: this attribute can require a larger"
                " amount of cache storage compared to the built-in 'flip_id' attribute. If unique IDs are not required,"
                " leave this attribute disabled",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_uid_attribute"))
    enable_fluid_particle_uid_attribute_reuse = BoolProperty(
            name="Reuse UIDs",
            description="Reuse UID attribute values. If enabled, particles that are removed from the simulation may have"
                " their UID reused in a later frame. If a particle is removed from the simulation, the UID will not be"
                " reused until at least a 1 frame gap has passed. UID values will only be unique to a single frame."
                " Enabling is recommended for use in simulation nodes to reduce resource usage. If disabled, UID values"
                " will be unique to the entire simulation. Disabling is recommended for tracking individual particles"
                " in geometry nodes",
            default=True,
            options={'HIDDEN'},
            ); exec(conv("enable_fluid_particle_uid_attribute_reuse"))

    fluid_particles_expanded = BoolProperty(default=True); exec(conv("fluid_particles_expanded"))
    fluid_particle_generation_expanded = BoolProperty(default=False); exec(conv("fluid_particle_generation_expanded"))
    fluid_particle_display_settings_expanded = BoolProperty(default=False); exec(conv("fluid_particle_display_settings_expanded"))
    geometry_attributes_expanded = BoolProperty(default=False); exec(conv("geometry_attributes_expanded"))
    velocity_attributes_expanded = BoolProperty(default=False); exec(conv("velocity_attributes_expanded"))
    color_attributes_expanded = BoolProperty(default=False); exec(conv("color_attributes_expanded"))
    other_attributes_expanded = BoolProperty(default=False); exec(conv("other_attributes_expanded"))


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".enable_fluid_particle_output",                         "Enable Fluid Particle Export", group_id=0)
        add(path + ".fluid_particle_output_amount",                         "Export Amount",                group_id=0)
        add(path + ".enable_fluid_particle_surface_output",                 "Export Surface Particles",     group_id=0)
        add(path + ".enable_fluid_particle_boundary_output",                "Export Boundary Particles",    group_id=0)
        add(path + ".enable_fluid_particle_interior_output",                "Export Interior Particles",    group_id=0)
        add(path + ".fluid_particle_source_id_blacklist",                   "Skip Source ID",               group_id=0)
        add(path + ".enable_fluid_particle_velocity_vector_attribute",      "Velocity Attribute",           group_id=0)
        add(path + ".enable_fluid_particle_speed_attribute",                "Speed Attribute",              group_id=0)
        add(path + ".enable_fluid_particle_vorticity_vector_attribute",     "Vorticity Attribute",          group_id=0)
        add(path + ".enable_fluid_particle_color_attribute",                "Color Attribute",              group_id=0)
        add(path + ".enable_fluid_particle_age_attribute",                  "Age Attribute",                group_id=0)
        add(path + ".enable_fluid_particle_lifetime_attribute",             "Lifetime Attribute",           group_id=0)
        add(path + ".enable_fluid_particle_whitewater_proximity_attribute", "Lifetime Attribute",           group_id=0)
        add(path + ".enable_fluid_particle_source_id_attribute",            "Source ID Attribute",          group_id=0)
        add(path + ".enable_fluid_particle_uid_attribute",                  "UID Attribute",                group_id=0)
        add(path + ".enable_fluid_particle_uid_attribute_reuse",            "Reuse UIDs",                group_id=0)


    def _update_enable_fluid_particle_output(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.enable_fluid_particle_output:
            objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
            objects_to_initialize.fluid_particles = True

            dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        else:
            dprops.mesh_cache.particles.reset_cache_object()


def register():
    bpy.utils.register_class(DomainParticlesProperties)


def unregister():
    bpy.utils.unregister_class(DomainParticlesProperties)