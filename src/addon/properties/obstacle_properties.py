# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
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
from ..utils import version_compatibility_utils as vcu


class FlipFluidObstacleProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    is_enabled = BoolProperty(
            name="Enabled",
            description="Obstacle is present in the fluid simulation",
            default=True,
            ); exec(conv("is_enabled"))
    is_inversed = BoolProperty(
            name="Inverse",
            description="Turn the obstacle 'inside-out'. Enabling this option will make the inside solid parts"
                " of this obstacle empty while everything outside of the obstacle will become solid."
                " This option is useful for turning a closed shape into a perfect container to hold"
                " liquid without leakage",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("is_inversed"))
    export_animated_mesh = BoolProperty(
            name="Export Animated Mesh",
            description="Export this object as an animated mesh. Exporting animated meshes are"
                " slower, only use when necessary. This option is required for any animation that"
                " is more complex than just keyframed loc/rot/scale or F-Curves, such as parented"
                " relations, armatures, animated modifiers, deformable meshes, etc. This option is"
                " not needed for static objects",
            default=False,
            options={'HIDDEN'},
            ); exec(conv("export_animated_mesh"))
    skip_reexport = BoolProperty(
            name="Skip Mesh Re-Export",
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
    friction = FloatProperty(
            name="Friction",
            description="Amount of friction between the fluid and the surface"
                " of the obstacle",
            min=0.0, max=1.0,
            default=0.0,
            precision=2,
            ); exec(conv("friction"))
    velocity_scale = FloatProperty(
            name="Velocity Scale",
            description="Scale the object velocity by this amount. Values greater than 1.0"
                " will exaggerate the velocity and the simulation will behave as if the object"
                " is moving faster than it actually is. Values between 0.0 and 1.0 will dampen"
                " the velocity. Negative values will reverse the velocity. This setting is for"
                " artistic control and any value other than 1.0 will not be physically accurate",
            soft_min=0.0, soft_max=5.0,
            default=1.0,
            precision=2,
            ); exec(conv("velocity_scale"))
    whitewater_influence = FloatProperty(
            name="Whitewater Influence",
            description="Scale the amount of whitewater generated near this"
                " obstacle by this value. A value of 1.0 will generate the"
                " normal amount of whitewater, a value greater than 1.0 will"
                " generate more, a value less than 1.0 will generate less",
            min=0.0,
            default=1.0,
            precision=2,
            ); exec(conv("whitewater_influence"))
    dust_emission_strength = FloatProperty(
            name="Dust Emission Strength",
            description="Scale the amount of whitewater dust particles generated"
                " near this obstacle by this value. A value of 1.0 will generate the"
                " normal amount of dust, a value greater than 1.0 will"
                " generate more, a value less than 1.0 will generate less. Whitewater"
                " dust particle simulation must be enabled for this setting to take effect",
            min=0.0,
            default=1.0,
            precision=2,
            ); exec(conv("dust_emission_strength"))
    sheeting_strength = FloatProperty(
            name="Sheeting Strength Multiplier",
            description="Scale the amount of fluid sheeting strength against this"
                " obstacle by this value. This parameter will only take effect if"
                " sheeting effects are enabled in the World Panel",
            min=0.0,
            default=1.0,
            precision=2,
            ); exec(conv("sheeting_strength"))
    mesh_expansion = FloatProperty(
            name="Expand Geometry",
            description="Expand the obstacle mesh by this value. This setting"
                " can be used to prevent fluid from slipping through small"
                " cracks between touching obstacles. This setting is meant only to be"
                " used to prevent leakage in fractured objects and only small values"
                " should be used. This setting is not applicable for preventing leakage"
                " in thin-walled obstacles",
            default=0.0,
            soft_min=-0.05, soft_max=0.05,
            step=0.01,
            precision=5,
            ); exec(conv("mesh_expansion"))
    property_registry = PointerProperty(
            name="Obstacle Property Registry",
            description="",
            type=preset_properties.PresetRegistry,
            ); exec(conv("property_registry"))


    disabled_in_viewport_tooltip = BoolProperty(
            name="Object Disabled in Viewport", 
            description="This obstacle object is currently disabled in the viewport within the"
                " outliner (Monitor Icon) and will not be included in the simulation. If you"
                " want the object hidden in the viewport, but still have the object included in the"
                " simulation, use the outliner Hide in Viewport option instead (Eye Icon)", 
            default=True,
            ); exec(conv("disabled_in_viewport_tooltip"))



    def initialize(self):
        self._initialize_property_registry()


    def refresh_property_registry(self):
        self._initialize_property_registry()


    def _initialize_property_registry(self):
        try:
            self.property_registry.clear()
            add = self.property_registry.add_property
            add("obstacle.is_enabled", "")
            add("obstacle.is_inversed", "")
            add("obstacle.export_animated_mesh", "")
            add("obstacle.skip_reexport", "")
            add("obstacle.force_reexport_on_next_bake", "")
            add("obstacle.friction", "")
            add("obstacle.velocity_scale", "")
            add("obstacle.whitewater_influence", "")
            add("obstacle.dust_emission_strength", "")
            add("obstacle.sheeting_strength", "")
            add("obstacle.mesh_expansion", "")
            self._validate_property_registry()
        except:
            # Object is immutable if it is a linked library or library_override
            # In this case, pass on modifying the object
            pass


    def _validate_property_registry(self):
        for p in self.property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)
            if not hasattr(self, identifier):
                print("Property Registry Error: Unknown Identifier <" + identifier + ", " + path + ">")


    def load_post(self):
        self.initialize()


def load_post():
    obstacle_objects = bpy.context.scene.flip_fluid.get_obstacle_objects()
    for obstacle in obstacle_objects:
        obstacle.flip_fluid.obstacle.load_post()


def register():
    bpy.utils.register_class(FlipFluidObstacleProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidObstacleProperties)