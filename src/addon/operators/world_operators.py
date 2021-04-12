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


class FlipFluidMakeZeroGravity(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.make_zero_gravity"
    bl_label = "Set to Zero Gravity"
    bl_description = "Quickly switch to custom gravity mode set to zero gravity"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        dprops.world.gravity_type = 'GRAVITY_TYPE_CUSTOM'
        dprops.world.gravity = (0.0, 0.0, 0.0)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidMakeZeroGravity)


def unregister():
    bpy.utils.unregister_class(FlipFluidMakeZeroGravity)
