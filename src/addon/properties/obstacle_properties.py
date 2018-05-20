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

import bpy
from bpy.props import (
        BoolProperty,
        FloatProperty,
        PointerProperty
        )

from . import preset_properties


class FlipFluidObstacleProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.is_enabled = BoolProperty(
                name="Enabled",
                description="Object is present in the fluid simulation",
                default=True,
                )
        cls.is_inversed = BoolProperty(
                name="Inverse",
                description="Turn the obstacle 'inside-out'. Inside of the object"
                    " becomes hollow, and outside of the object becomes solid.",
                default=False,
                options={'HIDDEN'},
                )
        cls.export_animated_mesh = BoolProperty(
                name="Export Animated Mesh",
                description="Export this mesh as an animated one (slower, only"
                    " use if really necessary [e.g. armatures or parented objects],"
                    " animated pos/rot/scale F-curves do not require it",
                default=False,
                options={'HIDDEN'},
                )
        cls.mesh_expansion = FloatProperty(
                name="Expand",
                description="Expand the obstacle mesh by some value. This setting"
                    " can be used to prevent fluid from slipping through small"
                    " cracks between touching obstacles. If the object is composed"
                    " of multiple mesh pieces, each piece will be expanded"
                    " individually.",
                default=0.0,
                step=1,
                precision=4,
                )
        cls.friction = FloatProperty(
                name="Friction",
                description="Amount of friction between the fluid and the surface"
                    " of the obstacle",
                min=0.0, max=1.0,
                default=0.0,
                precision=2,
                )
        cls.property_registry = PointerProperty(
                name="Obstacle Property Registry",
                description="",
                type=preset_properties.PresetRegistry,
                )


    @classmethod
    def unregister(cls):
        pass


    def initialize(self):
        add = self.property_registry.add_property
        add("obstacle.is_enabled", "")
        add("obstacle.is_inversed", "")
        add("obstacle.export_animated_mesh", "")
        add("obstacle.mesh_expansion", "")
        add("obstacle.friction", "")
        self._validate_property_registry()


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + identifier + ", " + path + ">")


def register():
    bpy.utils.register_class(FlipFluidObstacleProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidObstacleProperties)