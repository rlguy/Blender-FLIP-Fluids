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
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="World Panel Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings"

        if show_advanced:
            box = self.layout.box()

            row = box.row(align=True)
            row.prop(wprops, "world_scale_settings_expanded",
                icon="TRIA_DOWN" if wprops.world_scale_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="World Scaling:")

            if wprops.world_scale_settings_expanded:
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

            if show_documentation:
                column = box.column(align=True)
                column.operator(
                    "wm.url_open", 
                    text="World Scaling Documentation", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#world-size"
                column.operator(
                    "wm.url_open", 
                    text="How to use relative and absolute scaling modes", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#how-to-use-relative-and-absolute-world-scaling-in-your-workflow"
                column.operator(
                    "wm.url_open", 
                    text="The Importance of Scale", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#the-importance-of-scale"
                column.operator(
                    "wm.url_open", 
                    text="Tips on simulating small scale fluids", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#tips-on-simulating-small-world-sizes"

            box = self.layout.box()
            row = box.row(align=True)
            row.prop(wprops, "force_field_settings_expanded",
                icon="TRIA_DOWN" if wprops.force_field_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Gravity and Force Fields:")

            if wprops.force_field_settings_expanded:
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

                column = box.column(align=True)
                column.operator("flip_fluid_operators.make_zero_gravity")

                
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

            if show_documentation:
                column = box.column(align=True)
                column.operator(
                    "wm.url_open", 
                    text="Force Field Resolution", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#force-field-resolution"
                column.operator(
                    "wm.url_open", 
                    text="Force Field Example Scenes", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions#force-field-examples"
                
        box = self.layout.box()
        row = box.row(align=True)
        row.prop(wprops, "viscosity_settings_expanded",
            icon="TRIA_DOWN" if wprops.viscosity_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        if not wprops.viscosity_settings_expanded:
                row.prop(wprops, "enable_viscosity", text="")
        row.label(text="Viscosity:")

        if wprops.viscosity_settings_expanded:
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.prop(wprops, "enable_viscosity")
            column_left.label(text="")
            column_left.label(text="")
            row = column_left.row(align=True)
            row.alignment='RIGHT'
            row.enabled = wprops.enable_viscosity
            row.label(text="Total viscosity =")

            total_viscosity = wprops.viscosity * (10**(-wprops.viscosity_exponent))
            viscosity_str = self.format_number_precision(total_viscosity, 6)

            column_right = split.column(align=True)
            column_right.enabled = wprops.enable_viscosity
            column_right.prop(wprops, "viscosity", text="Base")
            column_right.prop(wprops, "viscosity_exponent", text="Exponent")
            column_right.prop(wprops, "viscosity_solver_error_tolerance", text="Accuracy", slider=True)
            column_right.label(text=viscosity_str)

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Viscosity Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#viscosity"

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(wprops, "surface_tension_settings_expanded",
            icon="TRIA_DOWN" if wprops.surface_tension_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        if not wprops.surface_tension_settings_expanded:
                row.prop(wprops, "enable_surface_tension", text="")
        row.label(text="Surface Tension:")

        if wprops.surface_tension_settings_expanded:
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.prop(wprops, "enable_surface_tension")
            column_left.label(text="")
            column_left.label(text="")
            row = column_left.row(align=True)
            row.enabled = wprops.enable_surface_tension
            row.alignment='RIGHT'
            row.label(text="Total Surface Tension =")
            row = column_left.row(align=True)
            row.enabled = wprops.enable_surface_tension
            row.alignment='RIGHT'
            row.prop(wprops, "surface_tension_substeps_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="Estimated substeps =")

            total_surface_tension = wprops.get_surface_tension_value()
            surface_tension_str = self.format_number_precision(total_surface_tension, 6)

            column_right = split.column(align=True)
            column_right.enabled = wprops.enable_surface_tension
            column_right.prop(wprops, "surface_tension", text="Base")
            column_right.prop(wprops, "surface_tension_exponent", text="Exponent")
            column_right.prop(wprops, "surface_tension_accuracy", text="Accuracy")
            column_right.label(text=surface_tension_str)
            column_right.label(text=str(wprops.minimum_surface_tension_substeps))

            if wprops.enable_surface_tension and wprops.minimum_surface_tension_substeps > aprops.min_max_time_steps_per_frame.value_max:
                row = column.row(align=True)
                row.alert = True
                row.prop(wprops, "surface_tension_substeps_exceeded_tooltip", icon="QUESTION", emboss=False, text="")
                row.label(text="  Warning: Too Many Substeps")

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Surface Tension Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#surface-tension"

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(wprops, "sheeting_settings_expanded",
            icon="TRIA_DOWN" if wprops.sheeting_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        if not wprops.sheeting_settings_expanded:
                row.prop(wprops, "enable_sheet_seeding", text="")
        row.label(text="Sheeting Effects:")

        if wprops.sheeting_settings_expanded:
            box.label(text="Sheeting Effects:")
            column = box.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
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

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Sheeting Effects Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#sheeting-effects"

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(wprops, "friction_settings_expanded",
            icon="TRIA_DOWN" if wprops.friction_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Friction:")

        if wprops.friction_settings_expanded:
            column = box.column()
            split = column.split(align=True)
            column_left = split.column()
            column_left.label(text="Boundary Friction:")
            column_right = split.column()
            column_right.prop(wprops, "boundary_friction", text="")

            row = box.row(align=True)
            row.prop(wprops, "obstacle_friction_expanded",
                icon="TRIA_DOWN" if wprops.obstacle_friction_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Obstacle Friction:")

            if wprops.obstacle_friction_expanded:
                obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()

                column = box.column(align=True)
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


    def format_number_precision(self, value, precision):
        decimal_part, int_part = math.modf(value)
        int_str = str(int(int_part))
        decimal_str = ""
        found_nonzero = False
        nonzero_count = 0
        for ch in str(decimal_part)[2:]:
            if ch != '0':
                found_nonzero = True
            if found_nonzero:
                nonzero_count += 1
            if nonzero_count > precision:
                break
            decimal_str += ch
        return int_str + "." + decimal_str
    
def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidWorldPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidWorldPanel)
