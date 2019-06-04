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

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_DomainTypeFluidWorldPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid World"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def get_domain_size(self, context):
        domain = vcu.get_active_object(context)
        minx = miny = minz = float("inf")
        maxx = maxy = maxz = -float("inf")
        for v in domain.data.vertices:
            p = vcu.element_multiply(v.co, domain.matrix_world)
            minx, miny, minz = min(p.x, minx), min(p.y, miny), min(p.z, minz)
            maxx, maxy, maxz = max(p.x, maxx), max(p.y, maxy), max(p.z, maxz)
        return max(maxx - minx, maxy - miny, maxz - minz)

    def draw(self, context):
        obj = vcu.get_active_object(context)
        wprops = obj.flip_fluid.domain.world
        aprops = obj.flip_fluid.domain.advanced
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        if show_advanced:
            box = self.layout.box()
            box.label(text="World Size:")
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column()
            column_left.prop(wprops, "enable_real_world_size", 
                                     text='Enable World Scaling')

            column_right = split.column()
            column_right.enabled = wprops.enable_real_world_size
            column_right.prop(wprops, "real_world_size")

            column_right_split = vcu.ui_split(column_right, factor=0.66)
            column_right_left = column_right_split.column()
            column_right_left.label(text="Size In Viewport:")

            column_right_right = column_right_split.column()
            size_str = str(round(self.get_domain_size(context), 1)) + "m"
            column_right_right.label(text=size_str)

            box = self.layout.box()
            box.label(text="Gravity:")
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
        box.label(text="Viscosity:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.prop(wprops, "enable_viscosity")

        column_right = split.column()
        column_right.enabled = wprops.enable_viscosity
        column_right.prop(wprops, "viscosity", text="")

        box = self.layout.box()
        box.label(text="Surface Tension:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column(align=True)
        column_left.prop(wprops, "enable_surface_tension")
        column_left.label(text="")
        row = column_left.row()
        row.enabled = wprops.enable_surface_tension
        row.prop(wprops, "surface_tension_substeps_tooltip", icon="QUESTION", emboss=False, text="")
        row.label(text="Estimated substeps: ")

        column_right = split.column(align=True)
        column_right.enabled = wprops.enable_surface_tension
        column_right.prop(wprops, "surface_tension", text="Surface Tension")
        column_right.prop(wprops, "surface_tension_accuracy", text="Accuracy")
        column_right.label(text=str(wprops.minimum_surface_tension_substeps))

        box = self.layout.box()
        box.label(text="Sheeting Effects:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.prop(wprops, "enable_sheet_seeding")
        column_right = split.column(align=True)
        column_right.enabled = wprops.enable_sheet_seeding
        column_right.prop(wprops, "sheet_fill_rate")
        column_right.prop(wprops, "sheet_fill_threshold")

        if show_advanced:
            obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()
            indent_str = 5 * " "
            column.label(text="Obstacle Sheeting:")
            if len(obstacle_objects) == 0:
                column.label(text=indent_str + "No obstacle objects found...")
            else:
                split = column.split(align=True)
                column_left = split.column(align=True)
                column_right = split.column(align=True)
                for ob in obstacle_objects:
                    pgroup = ob.flip_fluid.get_property_group()
                    column_left.label(text=ob.name, icon="OBJECT_DATA")
                    column_right.prop(pgroup, "sheeting_strength", text="Strength Scale")

        box = self.layout.box()
        box.label(text="Friction:")
        column = box.column()
        split = column.split(align=True)
        column_left = split.column()
        column_left.label(text="Boundary Friction:")
        column_right = split.column()
        column_right.prop(wprops, "boundary_friction", text="")

        obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()
        column.label(text="Obstacle Friction:")
        indent_str = 5 * " "
        if len(obstacle_objects) == 0:
            column.label(text=indent_str + "No obstacle objects found...")
        else:
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            for ob in obstacle_objects:
                pgroup = ob.flip_fluid.get_property_group()
                column_left.label(text=ob.name, icon="OBJECT_DATA")
                column_right.prop(pgroup, "friction")
        
    
def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidWorldPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidWorldPanel)
