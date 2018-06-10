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
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        EnumProperty,
        )

from . import preset_properties
from .. import types


class FlipFluidInflowProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.is_enabled = BoolProperty(
                name="Enabled",
                description="Object contributes to the fluid simulation",
                default=True,
                )
        cls.substep_emissions = IntProperty(
                name="Substep Emissions",
                description="Number of times fluid is emitted from the inflow"
                    " per simulation substep. Increase to reduce stuttering"
                    " fluid artifacts with fast moving keyframed/animated inflow"
                    " objects.",
                min=1, soft_max=8,
                default=1,
                )
        cls.inflow_velocity = FloatVectorProperty(
                name="Inflow Velocity",
                description="Initial velocity of fluid (m/s)",
                default=(0.0, 0.0, 0.0),
                subtype='VELOCITY',
                precision=3,
                size=3,
                )
        cls.append_object_velocity = BoolProperty(
                name="Add Object Velocity to Infow",
                description="Add the velocity of the object to the inflow fluid"
                    " velocity. Object mesh must be rigid (non-deformable).",
                default=False,
                )
        cls.append_object_velocity_influence = FloatProperty(
                name="Influence",
                description="Amount of velocity that is added to the inflow fluid."
                    " A value of 1.0 is normal, less than 1.0 will dampen the"
                    " velocity, greater than 1.0 will exaggerate the velocity,"
                    " negative values will reverse velocity direction.",
                subtype='FACTOR',
                soft_min=0.0, soft_max=1.0,
                default=1.0,
                precision=2,
                )
        cls.inflow_mesh_type = EnumProperty(
                name="Mesh Type",
                description="Type of mesh used for the inflow object. Used to"
                    " correctly calculate object velocities.",
                items=types.mesh_types,
                default='MESH_TYPE_RIGID',
                options={'HIDDEN'},
                )
        cls.inflow_velocity_mode = EnumProperty(
                name="Velocity Mode",
                description="Set how the inflow fluid velocity is calculated",
                items=types.inflow_velocity_modes,
                default='INFLOW_VELOCITY_MANUAL',
                options={'HIDDEN'},
                )
        cls.inflow_speed = FloatProperty(
                name="Speed",
                description="Initial speed of fluid towards target (m/s)",
                default=0.0,
                precision=3,
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
        cls.property_registry = PointerProperty(
                name="Inflow Property Registry",
                description="",
                type=preset_properties.PresetRegistry,
                )


    @classmethod
    def unregister(cls):
        pass


    def initialize(self):
        add = self.property_registry.add_property
        add("inflow.is_enabled", "")
        add("inflow.substep_emissions", "")
        add("inflow.inflow_velocity_mode", "")
        add("inflow.inflow_velocity", "")
        add("inflow.append_object_velocity", "")
        add("inflow.append_object_velocity_influence", "")
        add("inflow.inflow_mesh_type", "")
        add("inflow.inflow_speed", "")
        add("inflow.export_animated_target", "")
        add("inflow.export_animated_mesh", "")
        self._validate_property_registry()


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + identifier + ", " + path + ">")


    def is_target_valid(self):
        return (self.inflow_velocity_mode == 'INFLOW_VELOCITY_TARGET' and 
                bpy.data.objects.get(self.target_object) is not None)


def register():
    bpy.utils.register_class(FlipFluidInflowProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidInflowProperties)