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
        FloatProperty,
        FloatVectorProperty,
        StringProperty,
        BoolProperty,
        EnumProperty,
        IntProperty,
        PointerProperty
        )

from . import preset_properties
from .. import types


class FlipFluidFluidProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.initial_velocity = FloatVectorProperty(
                name="Initial Velocity",
                description="Initial velocity of fluid (m/s)",
                default =(0.0, 0.0, 0.0),
                size=3,
                precision=3,
                subtype='VELOCITY',
                )
        cls.append_object_velocity = BoolProperty(
                name="Add Object Velocity to Fluid",
                description="Add the velocity of the object to the initial velocity"
                    " of the fluid. Object mesh must be rigid (non-deformable).",
                default=False,
                )
        cls.append_object_velocity_influence = FloatProperty(
                name="Influence",
                description="Amount of velocity that is added to the fluid."
                    " A value of 1.0 is normal, less than 1.0 will dampen the"
                    " velocity, greater than 1.0 will exaggerate the velocity,"
                    " negative values will reverse velocity direction.",
                subtype='FACTOR',
                soft_min=0.0, soft_max=1.0,
                default=1.0,
                precision=2,
                )
        cls.use_initial_velocity_target = BoolProperty(
                name ="Set towards target",
                description="Set initial velocity towards a target object",
                default=False,
                options={'HIDDEN'}
                )
        cls.fluid_velocity_mode = EnumProperty(
                name="Velocity Mode",
                description="Set how the inital fluid velocity is calculated",
                items=types.fluid_velocity_modes,
                default='FLUID_VELOCITY_MANUAL',
                options={'HIDDEN'},
                )
        cls.initial_speed = bpy.props.FloatProperty(
                name="Speed",
                description="Initial speed of fluid towards target (m/s)",
                default=0.0,
                precision=3,
                options={'HIDDEN'},
                )
        cls.target_object = StringProperty(
                name="",
                description="Target object",
                )
        cls.export_animated_target = BoolProperty(
                name="Export Animated Target",
                description="Export this target as an animated one (slower, only"
                    " use if really necessary [e.g. armatures or parented objects],"
                    " animated pos/rot/scale F-curves do not require it",
                default=False,
                options={'HIDDEN'},
                )
        cls.export_animated_mesh = BoolProperty(
                name="Export Animated Mesh",
                description="Export this mesh as an animated one (slower, only use"
                    " if really necessary [e.g. armatures or parented objects],"
                    " animated pos/rot/scale F-curves do not require it",
                default=False,
                options={'HIDDEN'},
                )
        cls.frame_offset_type = EnumProperty(
                name="Trigger Type",
                description="When to trigger fluid object",
                items=types.frame_offset_types,
                default='OFFSET_TYPE_FRAME',
                options={'HIDDEN'},
                )
        cls.frame_offset = IntProperty(
                name="",
                description="Frame offset from start of simulation to add fluid object"
                    " to domain",
                min=0,
                default=0,
                options={'HIDDEN'},
                )
        cls.timeline_offset = bpy.props.IntProperty(
                name="",
                description="Timeline frame to add fluid object to domain",
                min=0,
                default=0,
                options={'HIDDEN'},
                )
        cls.property_registry = PointerProperty(
                name="Fluid Property Registry",
                description="",
                type=preset_properties.PresetRegistry,
                )


    @classmethod
    def unregister(cls):
        pass


    def initialize(self):
        add = self.property_registry.add_property
        add("fluid.initial_velocity", "")
        add("fluid.append_object_velocity", "")
        add("fluid.append_object_velocity_influence", "")
        add("fluid.fluid_velocity_mode", "")
        add("fluid.initial_speed", "")
        add("fluid.export_animated_target", "")
        add("fluid.export_animated_mesh", "")
        add("fluid.frame_offset_type", "")
        add("fluid.frame_offset", "")
        add("fluid.timeline_offset", "")
        self._validate_property_registry()


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + identifier + ", " + path + ">")


    def is_target_valid(self):
        return (self.fluid_velocity_mode == 'FLUID_VELOCITY_TARGET' and 
                bpy.data.objects.get(self.target_object) is not None)


def register():
    bpy.utils.register_class(FlipFluidFluidProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidFluidProperties)