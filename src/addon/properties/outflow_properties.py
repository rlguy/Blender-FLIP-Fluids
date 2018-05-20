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
        PointerProperty
        )

from . import preset_properties


class FlipFluidOutflowProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.is_enabled = BoolProperty(
                name="Enabled",
                description="Object contributes to the fluid simulation",
                default=True,
                )
        cls.remove_fluid = BoolProperty(
                name="Remove Fluid",
                description="Enable removing fluid particles from the domain",
                default=True,
                )
        cls.remove_whitewater = bpy.props.BoolProperty(
                name="Remove Whitewater",
                description="Enable removing whitewater particles from the domain",
                default=True,
                )
        cls.is_inversed = BoolProperty(
                name="Inverse",
                description="Turn the outflow object 'inside-out'. If enabled,"
                    " the outflow will remove fluid that is outside of the mesh"
                    " instead of removing fluid that is inside of the mesh.",
                default=False,
                options={'HIDDEN'},
                )
        cls.export_animated_mesh = bpy.props.BoolProperty(
                name="Export Animated Mesh",
                description="Export this mesh as an animated one (slower, only"
                    " use if really necessary [e.g. armatures or parented objects],"
                    " animated pos/rot/scale F-curves do not require it",
                default=False,
                options={'HIDDEN'},
                )
        cls.property_registry = PointerProperty(
                name="Outflow Property Registry",
                description="",
                type=preset_properties.PresetRegistry,
                )


    @classmethod
    def unregister(cls):
        pass


    def initialize(self):
        add = self.property_registry.add_property
        add("outflow.is_enabled", "")
        add("outflow.remove_fluid", "")
        add("outflow.remove_whitewater", "")
        add("outflow.is_inversed", "")
        add("outflow.export_animated_mesh", "")
        self._validate_property_registry()


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + 
                      identifier + ", " + path + ">")


def register():
    bpy.utils.register_class(FlipFluidOutflowProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidOutflowProperties)