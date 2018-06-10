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
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty
        )

from .. import types
from ..utils import export_utils


class DomainWorldProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.enable_real_world_size = BoolProperty(
                name="Real World Size",
                description="Enable domain to be scaled to a size in meters",
                default = False,
                options = {'HIDDEN'},
                )
        cls.real_world_size = FloatProperty(
                name="Meters", 
                description="Size of the simulation domain in meters", 
                min=0.001,
                default=10.0,
                precision=3,
                options={'HIDDEN'},
                )
        cls.gravity_type = EnumProperty(
                name="Gravity Type",
                description="Gravity Type",
                items=types.gravity_types,
                default='GRAVITY_TYPE_SCENE',
                options={'HIDDEN'},
                )
        cls.gravity = FloatVectorProperty(
                name="Gravity",
                description="Gravity in X, Y, and Z direction",
                default=(0.0, 0.0, -9.81),
                precision=2,
                size=3,
                subtype='VELOCITY',
                )
        cls.enable_viscosity = BoolProperty(
                name="Enable Viscosity",
                description="Enable viscosity solver",
                default=False,
                )
        cls.viscosity = FloatProperty(
                name="Viscosity", 
                description="Fluid viscosity value", 
                min=0.0,
                default=5.0,
                precision=3,
                )
        cls.boundary_friction = FloatProperty(
                name="Boundary Friction", 
                description="Amount of friction on the domain boundary walls", 
                min=0.0,
                max=1.0,
                default=0.0,
                precision=2,
                subtype='FACTOR',
                )


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".enable_real_world_size", "Enable World Scaling", group_id=0)
        add(path + ".real_world_size",        "World Size",           group_id=0)
        add(path + ".gravity_type",           "Gravity Type",         group_id=0)
        add(path + ".gravity",                "Gravity",              group_id=0)
        add(path + ".enable_viscosity",       "Enable Viscosity",     group_id=0)
        add(path + ".viscosity",              "Viscosity",            group_id=0)
        add(path + ".boundary_friction",      "Boundary Friction",    group_id=0)


    def get_gravity_data_dict(self):
        domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        if self.gravity_type == 'GRAVITY_TYPE_SCENE':
            scene = bpy.context.scene
            return export_utils.get_vector_property_data_dict(scene, scene, 'gravity')
        elif self.gravity_type == 'GRAVITY_TYPE_CUSTOM':
            return export_utils.get_vector_property_data_dict(domain_object, self, 'gravity')


def register():
    bpy.utils.register_class(DomainWorldProperties)


def unregister():
    bpy.utils.unregister_class(DomainWorldProperties)