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

import bpy, math

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


    def draw(self, context):
        obj = vcu.get_active_object(context)
        sprops = obj.flip_fluid.domain.simulation
        wprops = obj.flip_fluid.domain.world
        aprops = obj.flip_fluid.domain.advanced
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        if show_advanced:
            box = self.layout.box()
            box.label(text="World Scaling Mode:")
            row = box.row(align=True)
            row.prop(wprops, "world_scale_mode", expand=True)

            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column()
            column_right = split.column()

            if wprops.world_scale_mode == 'WORLD_SCALE_MODE_RELATIVE':
                row = column_left.row(align=True)
                row.alignment = 'RIGHT'
                row.label(text="1 Blender Unit = ")
                column_right.prop(wprops, "world_scale_relative")
            else:
                row = column_left.row(align=True)
                row.alignment = 'RIGHT'
                row.label(text="Domain Length = ")
                column_right.prop(wprops, "world_scale_absolute")

            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="Simulation dimensions:  X = ")
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="Y = ")
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="Z = ")

            xdims, ydims, zdims = wprops.get_simulation_dimensions(context)
            xdims_str = '{:.2f}'.format(round(xdims, 2)) + " m"
            ydims_str = '{:.2f}'.format(round(ydims, 2)) + " m"
            zdims_str = '{:.2f}'.format(round(zdims, 2)) + " m"

            column_right.label(text=xdims_str)
            column_right.label(text=ydims_str)
            column_right.label(text=zdims_str)

            box = self.layout.box()
            box.label(text="Gravity:")
            row = box.row(align=True)
            row.prop(wprops, "gravity_type", expand=True)

            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column()
            column_right = split.column()

            gvector = wprops.get_gravity_vector()
            magnitude = (gvector[0] * gvector[0] + gvector[1] * gvector[1] + gvector[2] * gvector[2])**(1.0/2.0)
            gforce = magnitude / 9.81
            mag_str = '{:.2f}'.format(round(magnitude, 2))
            gforce_str = '{:.2f}'.format(round(gforce, 2))

            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="magnitude = " + mag_str)
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="g-force = " + gforce_str)

            column_right.enabled = not (wprops.gravity_type == 'GRAVITY_TYPE_SCENE')

            if wprops.gravity_type == 'GRAVITY_TYPE_SCENE':
                column_right.prop(context.scene, "gravity", text="")
            elif wprops.gravity_type == 'GRAVITY_TYPE_CUSTOM':
                column_right.prop(wprops, "gravity", text="")

            # Force field features currently hidden from UI
            """
            box.label(text="Force Field Resolution:")
            column = box.column(align=True)
            row = column.row(align=True)
            row.prop(wprops, "force_field_resolution", expand=True)

            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)

            field_resolution = sprops.resolution
            if wprops.force_field_resolution == 'FORCE_FIELD_RESOLUTION_LOW':
                field_resolution = int(math.ceil(field_resolution / 4))
            elif wprops.force_field_resolution == 'FORCE_FIELD_RESOLUTION_NORMAL':
                field_resolution = int(math.ceil(field_resolution / 3))
            elif wprops.force_field_resolution == 'FORCE_FIELD_RESOLUTION_HIGH':
                field_resolution = int(math.ceil(field_resolution / 2))

            row = column_left.row()
            row.prop(wprops, "force_field_resolution_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="Grid resolution: ")
            column_right.label(text=str(field_resolution))
            """


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
