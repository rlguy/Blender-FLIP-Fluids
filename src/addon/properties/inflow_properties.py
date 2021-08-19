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
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        EnumProperty,
        )

from . import preset_properties
from .. import types
from ..utils import version_compatibility_utils as vcu


class FlipFluidInflowProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    is_enabled = BoolProperty(
            name="Enabled",
            description="Inflow emits fluid into the domain. Tip: keyframe this option on/off to start and stop inflow emission",
            default=True,
            ); exec(conv("is_enabled"))
    substep_emissions = IntProperty(
            name="Substep Emissions",
            description="Number of times fluid is emitted from the inflow"
                " per simulation substep. Increase to reduce stuttering"
                " fluid artifacts with fast moving keyframed/animated inflow"
                " objects. If set to 0, the inflow will only emit on the first"
                " substep of a frame",
            min=0, soft_max=8,
            default=1,
            ); exec(conv("substep_emissions"))
    inflow_velocity = FloatVectorProperty(
            name="Inflow Velocity",
            description="Initial velocity of fluid (m/s)",
            default=(0.0, 0.0, 0.0),
            subtype='VELOCITY',
            precision=3,
            size=3,
            ); exec(conv("inflow_velocity"))
    append_object_velocity = BoolProperty(
            name="Add Object Velocity to Infow",
            description="Add the velocity of the object to the inflow fluid"
                " velocity",
            default=False,
            ); exec(conv("append_object_velocity"))
    append_object_velocity_influence = FloatProperty(
            name="Influence",
            description="Amount of velocity that is added to the inflow fluid."
                " A value of 1.0 is normal, less than 1.0 will dampen the"
                " velocity, greater than 1.0 will exaggerate the velocity,"
                " negative values will reverse velocity direction",
            subtype='FACTOR',
            soft_min=0.0, soft_max=1.0,
            default=1.0,
            precision=2,
            ); exec(conv("append_object_velocity_influence"))
    inflow_velocity_mode = EnumProperty(
            name="Velocity Mode",
            description="Set how the inflow fluid velocity is calculated",
            items=types.inflow_velocity_modes,
            default='INFLOW_VELOCITY_MANUAL',
            options={'HIDDEN'},
            ); exec(conv("inflow_velocity_mode"))
    inflow_speed = FloatProperty(
            name="Speed",
            description="Initial speed of fluid towards target (m/s)",
            default=0.0,
            precision=3,
            ); exec(conv("inflow_speed"))
    inflow_axis_mode = EnumProperty(
            name="Local Axis",
            description="Set local axis direction of fluid",
            items=types.local_axis_directions,
            default='LOCAL_AXIS_POS_X',
            ); exec(conv("inflow_axis_mode"))
    target_object = PointerProperty(
            name="Target Object", 
            type=bpy.types.Object
            ); exec(conv("target_object"))
    export_animated_target = BoolProperty(
            name="Export Animated Target",
            description="Export this target as an animated one (slower, only"
                " use if really necessary [e.g. armatures or parented objects],"
                " animated pos/rot/scale F-curves do not require it",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("export_animated_target"))
    constrain_fluid_velocity = BoolProperty(
            name="Constrain Fluid Velocity",
            description="Force fluid inside of the inflow to match the inflow" +
                " emission velocity. If enabled, the inflow will continue to" +
                " push around fluid when submerged. Setting low inflow velocity" + 
                " values will have the effect of slowing down fluid emission",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("constrain_fluid_velocity"))
    source_id = IntProperty(
            name="Source ID Attribute",
            description="Assign this identifier value to the fluid generated by this inflow. After"
                " baking, the source ID attribute values can be accessed in a Cycles Attribute Node"
                " with the name 'flip_source_id' from the Fac output. This can be used to create"
                " basic multiple material liquid effects. Enable this feature in the Domain FLIP"
                " Fluid Surface panel",
            min=0, soft_max=16,
            default=0,
            options={'HIDDEN'},
            ); exec(conv("source_id"))
    color = FloatVectorProperty(
            name="Color Attribute",
            description="Assign this color to the fluid generated by this object. After"
                " baking, the color attribute values can be accessed in a Cycles Attribute Node"
                " with the name 'flip_color' from the Color output. This can be used to create"
                " basic varying color liquid effects. Enable this feature in the Domain FLIP"
                " Fluid Surface panel",
            default=(1.0, 1.0, 1.0),
            min=0.0, max=1.0,
            size=3,
            precision=3,
            subtype='COLOR',
            ); exec(conv("color"))
    export_animated_mesh = BoolProperty(
            name="Export Animated Mesh",
            description="Export this mesh as an animated one (slower, only use"
                " if really necessary [e.g. armatures or parented objects],"
                " animated pos/rot/scale F-curves do not require it",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("export_animated_mesh"))
    skip_reexport = BoolProperty(
            name="Skip re-export",
            description="Skip re-exporting this mesh when starting or resuming"
                " a bake. If this mesh has not been exported or is missing files,"
                " the addon will automatically export the required files",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("skip_reexport"))
    force_reexport_on_next_bake = BoolProperty(
            name="Force Re-Export On Next Bake",
            description="Override the 'Skip Re-Export' option and force this mesh to be"
                " re-exported and updated on the next time a simulation start/resumes"
                " baking. Afting starting/resuming the baking process, this option"
                " will automatically be disabled once the object has been fully exported."
                " This option is only applicable if 'Skip Re-Export' is enabled",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("force_reexport_on_next_bake"))
    property_registry = PointerProperty(
            name="Inflow Property Registry",
            description="",
            type=preset_properties.PresetRegistry,
            ); exec(conv("property_registry"))


    def initialize(self):
        self.property_registry.clear()
        add = self.property_registry.add_property
        add("inflow.is_enabled", "")
        add("inflow.substep_emissions", "")
        add("inflow.inflow_velocity_mode", "")
        add("inflow.inflow_velocity", "")
        add("inflow.append_object_velocity", "")
        add("inflow.append_object_velocity_influence", "")
        add("inflow.constrain_fluid_velocity", "")
        add("inflow.inflow_speed", "")
        add("inflow.inflow_axis_mode", "")
        add("inflow.source_id", "")
        add("inflow.color", "")
        add("inflow.export_animated_target", "")
        add("inflow.export_animated_mesh", "")
        add("inflow.skip_reexport", "")
        add("inflow.force_reexport_on_next_bake", "")
        self._validate_property_registry()


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + identifier + ", " + path + ">")


    def get_target_object(self):
        obj = None
        try:
            all_objects = vcu.get_all_scene_objects()
            obj = self.target_object
            obj = all_objects.get(obj.name)
        except:
            pass
        return obj


    def is_target_valid(self):
        return (self.inflow_velocity_mode == 'INFLOW_VELOCITY_TARGET' and 
                self.get_target_object() is not None)


    def load_post(self):
        self.initialize()


def load_post():
    inflow_objects = bpy.context.scene.flip_fluid.get_inflow_objects()
    for inflow in inflow_objects:
        inflow.flip_fluid.inflow.load_post()


def register():
    bpy.utils.register_class(FlipFluidInflowProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidInflowProperties)