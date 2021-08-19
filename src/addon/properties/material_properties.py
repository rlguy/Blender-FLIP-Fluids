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
from bpy.props import (
        BoolProperty,
        IntProperty,
        StringProperty,
        PointerProperty
        )

from ..utils import version_compatibility_utils as vcu


class FlipFluidMaterialLibraryProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    # Material Library Data
    is_library_material = BoolProperty(default=False); exec(conv("is_library_material"))
    library_name = StringProperty(default=""); exec(conv("library_name"))
    imported_name = StringProperty(default=""); exec(conv("imported_name"))
    data_block_id = StringProperty(default="-1"); exec(conv("data_block_id"))

    # Preset Library Data
    is_preset_material = BoolProperty(default=False); exec(conv("is_preset_material"))
    preset_identifier = StringProperty(default=""); exec(conv("preset_identifier"))
    preset_blend_identifier = StringProperty(default=""); exec(conv("preset_blend_identifier"))
    is_fake_user_set_by_addon = BoolProperty(default=False); exec(conv("is_fake_user_set_by_addon"))
    skip_preset_unload = BoolProperty(default=False); exec(conv("skip_preset_unload"))


    @classmethod
    def register(cls):
        bpy.types.Material.flip_fluid_material_library = PointerProperty(
                name="Flip Fluid Material Library Properties",
                description="",
                type=cls,
                )
        

    @classmethod
    def unregister(cls):
        del bpy.types.Material.flip_fluid_material_library


    def activate(self, material_object, library_name):
        self.is_library_material = True
        self.library_name = library_name
        self.imported_name = material_object.name
        self.data_block_id = str(material_object.as_pointer())


    def deactivate(self):
        self.property_unset("is_library_material")
        self.property_unset("library_name")
        self.property_unset("imported_name")
        self.property_unset("data_block_id")


    def reinitialize_data_block_id(self, material_object):
        self.data_block_id = str(material_object.as_pointer())


    def is_original_data_block(self, material_object):
        return self.data_block_id == str(material_object.as_pointer())


def register():
    bpy.utils.register_class(FlipFluidMaterialLibraryProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidMaterialLibraryProperties)