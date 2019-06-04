# Blender FLIP Fluid Add-on
# Copyright (C) 2019 Ryan L. Guy
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
from ..utils import version_compatibility_utils as vcu


class FlipFluidOutflowProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    is_enabled = BoolProperty(
            name="Enabled",
            description="Object contributes to the fluid simulation",
            default=True,
            ); exec(conv("is_enabled"))
    remove_fluid = BoolProperty(
            name="Remove Fluid",
            description="Enable removing fluid particles from the domain",
            default=True,
            ); exec(conv("remove_fluid"))
    remove_whitewater = bpy.props.BoolProperty(
            name="Remove Whitewater",
            description="Enable removing whitewater particles from the domain",
            default=True,
            ); exec(conv("remove_whitewater"))
    is_inversed = BoolProperty(
            name="Inverse",
            description="Turn the outflow object 'inside-out'. If enabled,"
                " the outflow will remove fluid that is outside of the mesh"
                " instead of removing fluid that is inside of the mesh",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("is_inversed"))
    export_animated_mesh = bpy.props.BoolProperty(
            name="Export Animated Mesh",
            description="Export this mesh as an animated one (slower, only"
                " use if really necessary [e.g. armatures or parented objects],"
                " animated pos/rot/scale F-curves do not require it",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("export_animated_mesh"))
    skip_animated_mesh_reexport = BoolProperty(
            name="Skip re-export",
            description="Skip re-exporting this mesh when starting or resuming"
                " a bake. If this mesh has not been exported or is missing files,"
                " the addon will automatically export the required files",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("skip_animated_mesh_reexport"))
    property_registry = PointerProperty(
            name="Outflow Property Registry",
            description="",
            type=preset_properties.PresetRegistry,
            ); exec(conv("property_registry"))


    def initialize(self):
        self.property_registry.clear()
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


    def load_post(self):
        self.initialize()


def load_post():
    outflow_objects = bpy.context.scene.flip_fluid.get_outflow_objects()
    for outflow in outflow_objects:
        outflow.flip_fluid.outflow.load_post()


def register():
    bpy.utils.register_class(FlipFluidOutflowProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidOutflowProperties)