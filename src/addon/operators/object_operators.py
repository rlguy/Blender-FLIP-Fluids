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


class FlipFluidAdd(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.flip_fluid_add"
    bl_label = "Add FLIP fluid object"
    bl_description = "Add active object as FLIP Fluid"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.scene.objects.active
        obj.flip_fluid.is_active = True
        return {'FINISHED'}


class FlipFluidRemove(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.flip_fluid_remove"
    bl_label = "Remove FLIP fluid object"
    bl_description = "Remove FLIP Fluid settings from Object"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.scene.objects.active
        obj.flip_fluid.object_type = 'TYPE_NONE'
        obj.flip_fluid.is_active = False
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidAdd)
    bpy.utils.register_class(FlipFluidRemove)


def unregister():
    bpy.utils.unregister_class(FlipFluidAdd)
    bpy.utils.unregister_class(FlipFluidRemove)
