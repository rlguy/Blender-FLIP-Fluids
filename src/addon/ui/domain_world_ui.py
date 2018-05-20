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


class FlipFluidDomainTypeFluidWorldPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid World"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def get_domain_size(self, context):
        domain = context.scene.objects.active
        minx = miny = minz = float("inf")
        maxx = maxy = maxz = -float("inf")
        for v in domain.data.vertices:
            p = v.co * domain.matrix_world
            minx, miny, minz = min(p.x, minx), min(p.y, miny), min(p.z, minz)
            maxx, maxy, maxz = max(p.x, maxx), max(p.y, maxy), max(p.z, maxz)
        return max(maxx - minx, maxy - miny, maxz - minz)

    def draw(self, context):
        obj = context.scene.objects.active
        wprops = obj.flip_fluid.domain.world

        box = self.layout.box()
        box.label("World Size:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.prop(wprops, "enable_real_world_size", 
                                 text='Enable World Scaling')

        column_right = split.column()
        column_right.enabled = wprops.enable_real_world_size
        column_right.prop(wprops, "real_world_size")

        column_right_split = column_right.split(percentage=0.66)
        column_right_left = column_right_split.column()
        column_right_left.label("Size In Viewport:")

        column_right_right = column_right_split.column()
        size_str = str(round(self.get_domain_size(context), 1)) + "m"
        column_right_right.label(size_str)

        box = self.layout.box()
        box.label("Gravity:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.prop(wprops, "gravity_type", text="")

        column_right = split.column()
        column_right.enabled = not (wprops.gravity_type == 'GRAVITY_TYPE_SCENE')
        if wprops.gravity_type == 'GRAVITY_TYPE_SCENE':
            column_right.prop(context.scene, "gravity", text="")
        elif wprops.gravity_type == 'GRAVITY_TYPE_CUSTOM':
            column_right.prop(wprops, "gravity", text="")

        box = self.layout.box()
        box.label("Viscosity:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.prop(wprops, "enable_viscosity")

        column_right = split.column()
        column_right.enabled = wprops.enable_viscosity
        column_right.prop(wprops, "viscosity", text="")

        box = self.layout.box()
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.label("Boundary Friction:")
        column_right = split.column()
        column_right.prop(wprops, "boundary_friction", text="")

        
    
def register():
    bpy.utils.register_class(FlipFluidDomainTypeFluidWorldPanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeFluidWorldPanel)
