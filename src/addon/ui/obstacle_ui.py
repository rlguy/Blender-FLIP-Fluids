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


class FlipFluidObstacleTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"


    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_OBSTACLE"


    def draw(self, context):
        obj = context.scene.objects.active
        obj_props = context.scene.objects.active.flip_fluid
        obstacle_props = obj_props.obstacle

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        column = self.layout.column()
        column.prop(obstacle_props, "is_enabled")

        column = self.layout.column()
        column.prop(obstacle_props, "friction", slider = True)

        column = self.layout.column()
        column.prop(obstacle_props, "mesh_expansion")

        column = self.layout.column()
        column.prop(obstacle_props, "is_inversed")
        column.prop(obstacle_props, "export_animated_mesh")
    

def register():
    bpy.utils.register_class(FlipFluidObstacleTypePanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidObstacleTypePanel)
