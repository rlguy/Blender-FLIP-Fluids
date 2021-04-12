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
        PointerProperty,
        EnumProperty
        )

from .custom_properties import (
        NewMinMaxFloatProperty
        )

from . import preset_properties
from .. import types
from ..utils import version_compatibility_utils as vcu


class FlipFluidForceFieldProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    force_field_type = EnumProperty(
            name="Type",
            description="Type of force field",
            items=types.force_field_types,
            default='FORCE_FIELD_TYPE_POINT',
            update=lambda self, context: self._update_force_field_type(context),
            options={'HIDDEN'},
            ); exec(conv("force_field_type"))
    is_enabled = BoolProperty(
            name="Enabled",
            description="Force field is active in the fluid simulation",
            default=True,
            ); exec(conv("is_enabled"))
    strength = FloatProperty(
            name="Strength",
            description="Strength of the force field. A negative value pulls fluid in,"
                " a positive value pushes fluid away",
            default=-9.81,
            precision=2,
            ); exec(conv("strength"))
    falloff_power = FloatProperty(
            name="Falloff Power",
            description="How quickly force strength decreases with distance. If "
                " r is the distance from the force object, the force strength changes"
                " with (1 / r^power). A value of 0 = constant force, 1 = linear falloff,"
                " 2 = gravitational falloff",
            default=1.0,
            min=0.0,
            soft_max=3.0, max=6.0,
            precision=2,
            ); exec(conv("falloff_power"))
    enable_min_distance = BoolProperty(
            name="Enable Min Distance",
            description="Use a minimum distance for the force field falloff",
            default=False,
            ); exec(conv("enable_min_distance"))
    enable_max_distance = BoolProperty(
            name="Enable Max Distance",
            description="Use a maximum distance for the force field to work",
            default=False,
            ); exec(conv("enable_max_distance"))
    min_max_distance = NewMinMaxFloatProperty(
            name_min="Min Distance", 
            description_min="The distance from the force object at which the strength"
                " begins to falloff", 
            min_min=0,
            default_min=0.0,
            precision_min=3,

            name_max="Max Distance", 
            description_max="Maximum distance from the force object that the force"
                " field will have an effect on the simulation. Limiting max distance"
                " can help speed up force field calculations", 
            min_max=0,
            default_max=0.0,
            precision_max=3,
            ); exec(conv("min_max_distance"))
    maximum_force_limit_factor = FloatProperty(
            name="Max Force Limit Factor",
            description="The maximum force in the field will be limited to the Strength"
                " multiplied by this value",
            default=3.0,
            min=0.0,
            soft_max=10.0,
            precision=2,
            ); exec(conv("maximum_force_limit_factor"))
    export_animated_mesh = bpy.props.BoolProperty(
            name="Export Animated Mesh",
            description="Export this mesh as an animated one (slower, only"
                " use if really necessary [e.g. armatures or parented objects],"
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

    maximum_strength_tooltip = BoolProperty(
            name="Maximum Force", 
            description="This value estimates the maximum possible force field strength"
                " generated by this object. Force field strengths are inversely proportional"
                " to distance and can become very large as distances decrease. Use the Max"
                " Force Limit Factor to reduce the maximum force. For reference, a force strength"
                " value of 9.81 is equal to the default strength of gravity", 
            default=True,
            ); exec(conv("maximum_strength_tooltip"))


    #
    # Properties for specific force field type
    #

    # Point Force Field
    falloff_shape = EnumProperty(
            name="Falloff Shape",
            description="(Placeholder, TODO) Specifies the shape of the force field. Only takes"
                " effect if the Falloff Power is greater than 0",
            items=types.force_field_falloff_shapes,
            default='FORCE_FIELD_FALLOFF_SPHERE',
            options={'HIDDEN'},
            ); exec(conv("falloff_shape"))
    gravity_scale_point = FloatProperty(
            name="Gravity Scale",
            description="Scale the force of gravity around this point by this value. A scale"
                " of 0.0 is zero gravity, a scale of 1.0 is full gravity",
            default=1.0,
            soft_min=0.0, soft_max=1.0,
            precision=2,
            ); exec(conv("gravity_scale_point"))
    gravity_scale_width_point = FloatProperty(
            name="Gravity Scale Width",
            description="The distance around this point that gravity scaling will take effect",
            default=1.0,
            min=0.0, soft_max=5.0,
            precision=2,
            ); exec(conv("gravity_scale_width_point"))

    # Surface Force Field
    gravity_scale_surface = FloatProperty(
            name="Gravity Scale",
            description="Scale the force of gravity near the surface by this value. A scale"
                " of 0.0 is zero gravity, a scale of 1.0 is full gravity",
            default=1.0,
            soft_min=0.0, soft_max=1.0,
            precision=2,
            ); exec(conv("gravity_scale_surface"))
    gravity_scale_width_surface = FloatProperty(
            name="Gravity Scale Width",
            description="The distance from the surface that gravity scaling will take effect",
            default=1.0,
            min=0.0, soft_max=5.0,
            precision=2,
            ); exec(conv("gravity_scale_width_surface"))

    # Volume Force Field
    gravity_scale_volume = FloatProperty(
            name="Gravity Scale",
            description="Scale the force of gravity inside the volume by this value. A scale"
                " of 0.0 is zero gravity, a scale of 1.0 is full gravity",
            default=1.0,
            soft_min=0.0, soft_max=1.0,
            precision=2,
            ); exec(conv("gravity_scale_volume"))
    gravity_scale_width_volume = FloatProperty(
            name="Gravity Scale Width",
            description="The distance from the outside of the volume's surface that gravity"
                " scaling will take effect",
            default=0.0,
            min=0.0, soft_max=5.0,
            precision=2,
            ); exec(conv("gravity_scale_width_volume"))

    # Curve Force Field
    flow_strength = FloatProperty(
            name="Flow Strength",
            description="Strength of the flow along the direction of the curve. The curve direction"
                " is in the vertex order of the Blender Curve object. A negative value will reverse"
                " the direction",
            default=0.0,
            precision=2,
            ); exec(conv("flow_strength"))
    spin_strength = FloatProperty(
            name="Spin Strength",
            description="Strength of the the force that directs fluid to spin around the curve. A positive"
                " strength uses the 'Right Hand Rule:' take your right hand and point your thumb in"
                " the direction of the curve (first vertex to last vertex). Curling your rght hand fingers"
                " around the curve will be the direction of spin. A negative strength will reverse the spin"
                " direction",
            default=0.0,
            precision=2,
            ); exec(conv("spin_strength"))
    gravity_scale_curve = FloatProperty(
            name="Gravity Scale",
            description="Scale the force of gravity near the curve by this value. A scale"
                " of 0.0 is zero gravity, a scale of 1.0 is full gravity",
            default=1.0,
            soft_min=0.0, soft_max=1.0,
            precision=2,
            ); exec(conv("gravity_scale_curve"))
    gravity_scale_width_curve = FloatProperty(
            name="Gravity Scale Width",
            description="The distance from the curve that gravity"
                " scaling will take effect",
            default=1.0,
            min=0.0, soft_max=5.0,
            precision=2,
            ); exec(conv("gravity_scale_width_curve"))
    enable_endcaps = BoolProperty(
            name="Enable End Caps",
            description="Whether fluid is attracted towards the ends of the curve segment. Disable"
                " to allow fluid to flow past the ends of the curve segment",
            default=True,
            ); exec(conv("enable_endcaps"))



    property_registry = PointerProperty(
            name="Outflow Property Registry",
            description="",
            type=preset_properties.PresetRegistry,
            ); exec(conv("property_registry"))


    def initialize(self):
        self.property_registry.clear()
        add = self.property_registry.add_property
        add("force_field.force_field_type", "")
        add("force_field.is_enabled", "")
        add("force_field.strength", "")
        add("force_field.flow_strength", "")
        add("force_field.spin_strength", "")
        add("force_field.enable_endcaps", "")
        add("force_field.falloff_power", "")
        add("force_field.falloff_shape", "")
        add("force_field.enable_min_distance", "")
        add("force_field.enable_max_distance", "")
        add("force_field.min_max_distance", "")
        add("force_field.maximum_force_limit_factor", "")
        add("force_field.gravity_scale_point", "")
        add("force_field.gravity_scale_surface", "")
        add("force_field.gravity_scale_volume", "")
        add("force_field.gravity_scale_curve", "")
        add("force_field.gravity_scale_width_point", "")
        add("force_field.gravity_scale_width_surface", "")
        add("force_field.gravity_scale_width_volume", "")
        add("force_field.gravity_scale_width_curve", "")
        add("force_field.export_animated_mesh", "")
        add("force_field.skip_reexport", "")
        add("force_field.force_reexport_on_next_bake", "")
        self._validate_property_registry()


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + 
                      identifier + ", " + path + ">")


    def _update_force_field_type(self, context):
        pass


    def load_post(self):
        self.initialize()


def load_post():
    force_field_objects = bpy.context.scene.flip_fluid.get_force_field_objects()
    for force_field in force_field_objects:
        force_field.flip_fluid.force_field.load_post()


def register():
    bpy.utils.register_class(FlipFluidForceFieldProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidForceFieldProperties)