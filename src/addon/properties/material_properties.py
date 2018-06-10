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
        StringProperty,
        PointerProperty
        )


class FlipFluidMaterialProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Material.flip_fluid = PointerProperty(
                name="Flip Fluid Material Properties",
                description="",
                type=cls,
                )

        cls.is_library_material = BoolProperty(default=False)
        cls.is_preset_material = BoolProperty(default=False)
        cls.skip_preset_unload = BoolProperty(default=False)
        cls.preset_identifier = StringProperty(default="")
        cls.preset_blend_identifier = StringProperty(default="")
        cls.is_fake_use_set_by_addon = BoolProperty(default=False)

    @classmethod
    def unregister(cls):
        del bpy.types.Material.flip_fluid


def register():
    bpy.utils.register_class(FlipFluidMaterialProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidMaterialProperties)