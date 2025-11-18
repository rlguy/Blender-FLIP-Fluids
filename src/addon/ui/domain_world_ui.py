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

import bpy, math

from ..utils import version_compatibility_utils as vcu


def format_number_precision(self, value):
    value_str = '{:.9f}'.format(value)
    return value_str


class FLIPFLUID_PT_DomainTypeFluidWorldPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid World"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if vcu.get_addon_preferences(context).enable_tabbed_domain_settings_view:
            return False
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN" and not is_addon_disabled


    def draw(self, context):
        obj = vcu.get_active_object(context)
        sprops = obj.flip_fluid.domain.simulation
        attrprops = obj.flip_fluid.domain.surface
        wprops = obj.flip_fluid.domain.world
        aprops = obj.flip_fluid.domain.advanced

        #
        # World Scale Panel
        #
        box = self.layout.box()
        header, body = box.panel("world_scale_settings", default_closed=False)

        row = header.row(align=True)
        row.label(text="World Scale:")
        if body:
            row = body.row(align=True)
            row.prop(wprops, "world_scale_mode", expand=True)

            column = body.column(align=True)
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
        else:
            xdims, ydims, zdims = wprops.get_simulation_dimensions(context)
            xdims_str = '{:.2f}'.format(round(xdims, 2)) + " m"
            ydims_str = '{:.2f}'.format(round(ydims, 2)) + " m"
            zdims_str = '{:.2f}'.format(round(zdims, 2)) + " m"

            info_text = xdims_str + " x " + ydims_str + " x " + zdims_str
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=info_text)

        #
        # Gravity and Force Fields Panel
        #
        box = self.layout.box()
        header, body = box.panel("gravity_and_force_field_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Gravity and Force Fields:")
        if body:
            subbox = body.box()
            subbox.label(text="Gravity:")
            row = subbox.row(align=True)
            row.prop(wprops, "gravity_type", expand=True)

            column = subbox.column(align=True)
            split = column.split(align=True)
            column_left = split.column()
            column_right = split.column()

            gvector = wprops.get_gravity_vector()
            magnitude = (gvector[0] * gvector[0] + gvector[1] * gvector[1] + gvector[2] * gvector[2])**(1.0/2.0)
            gforce = magnitude / 9.81
            mag_str = '{:.2f}'.format(round(magnitude, 2))
            gforce_str = '{:.2f}'.format(round(gforce, 2))

            if wprops.gravity_type == 'GRAVITY_TYPE_SCENE':
                column_left.label(text="")
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="magnitude = " + mag_str)
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="g-force = " + gforce_str)

            column_right.enabled = not (wprops.gravity_type == 'GRAVITY_TYPE_SCENE')

            if wprops.gravity_type == 'GRAVITY_TYPE_SCENE':
                column_right.prop(context.scene, "use_gravity", text="Gravity Enabled")
                column_right.prop(context.scene, "gravity", text="")
            elif wprops.gravity_type == 'GRAVITY_TYPE_CUSTOM':
                column_right.prop(wprops, "gravity", text="")

            column = subbox.column(align=True)
            column.operator("flip_fluid_operators.make_zero_gravity")

            subbox = body.box()
            subbox.label(text="Force Field Resolution:")
            column = subbox.column(align=True)
            row = column.row(align=True)
            row.prop(wprops, "force_field_resolution", expand=True)

            column = subbox.column(align=True)
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

            subbox = body.box()
            subbox.label(text="Force Field Weights:")
            column = subbox.column(align=True)
            column.prop(wprops, "force_field_weight_fluid_particles", slider=True)
            column.prop(wprops, "force_field_weight_whitewater_foam", slider=True)
            column.prop(wprops, "force_field_weight_whitewater_bubble", slider=True)
            column.prop(wprops, "force_field_weight_whitewater_spray", slider=True)
            column.prop(wprops, "force_field_weight_whitewater_dust", slider=True)

        
        #
        # Viscosity Panel
        #
        is_variable_viscosity_enabled = attrprops.enable_viscosity_attribute

        box = self.layout.box()
        header, body = box.panel("viscosity_settings", default_closed=True)

        row = header.row(align=True)
        if not body:
            row.prop(wprops, "enable_viscosity", text="")
        row.label(text="Viscosity:")
        if body:
            column = body.column(align=True)
            row = column.row(align=True)
            row.prop(wprops, "enable_viscosity")

            if vcu.get_addon_preferences().is_extra_features_enabled():
                row = row.row(align=True)
                row.enabled = wprops.enable_viscosity
                row.prop(attrprops, "enable_viscosity_attribute", text="Variable Viscosity")

            column = body.column(align=True)
            column.enabled = wprops.enable_viscosity

            if is_variable_viscosity_enabled:
                column.label(text="Variable viscosity values can be set in the", icon='INFO')
                column.label(text="Fluid or Inflow physics properties menu", icon='INFO')
            else:
                column.prop(wprops, "viscosity", text="Base")
                column.prop(wprops, "viscosity_exponent", text="Exponent")

            column.prop(wprops, "viscosity_solver_error_tolerance", text="Solver Accuracy", slider=True)

            if is_variable_viscosity_enabled:
                column.label(text="")
            else:
                total_viscosity = wprops.viscosity * (10**(-wprops.viscosity_exponent))
                total_viscosity_str = "Total viscosity   =   " + format_number_precision(self, total_viscosity)
                column.label(text=total_viscosity_str)
        else:
            if not is_variable_viscosity_enabled:
                total_viscosity = wprops.viscosity * (10**(-wprops.viscosity_exponent))
                total_viscosity_str = format_number_precision(self, total_viscosity)
                row = row.row(align=True)
                row.alignment = 'RIGHT'
                row.enabled = wprops.enable_viscosity
                row.label(text=total_viscosity_str)

        #
        # Surface Tension Panel
        #
        box = self.layout.box()
        header, body = box.panel("surface_tension_settings", default_closed=True)

        row = header.row(align=True)
        if not body:
            row.prop(wprops, "enable_surface_tension", text="")
        row.label(text="Surface Tension:")
        if body:
            column = body.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.prop(wprops, "enable_surface_tension")
            column_left.label(text="")
            column_left.label(text="")
            column_left = column_left.column(align=True)
            column_left.enabled = wprops.enable_surface_tension
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
            surface_tension_str = format_number_precision(self, total_surface_tension)

            column_right = split.column(align=True)
            column_right.enabled = wprops.enable_surface_tension
            column_right.prop(wprops, "surface_tension", text="Base")
            column_right.prop(wprops, "surface_tension_exponent", text="Exponent")
            column_right.prop(wprops, "surface_tension_accuracy", text="Solver Accuracy")
            column_right.label(text=surface_tension_str)
            column_right.label(text=str(wprops.minimum_surface_tension_substeps))

            if wprops.enable_surface_tension and wprops.minimum_surface_tension_substeps > aprops.min_max_time_steps_per_frame.value_max:
                row = column.row(align=True)
                row.alert = True
                row.prop(wprops, "surface_tension_substeps_exceeded_tooltip", icon="QUESTION", emboss=False, text="")
                row.label(text="  Warning: Too Many Substeps")
        else:
            total_surface_tension = wprops.get_surface_tension_value()
            surface_tension_str = format_number_precision(self, total_surface_tension)
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.enabled = wprops.enable_surface_tension
            row.alert = wprops.enable_surface_tension and wprops.minimum_surface_tension_substeps > aprops.min_max_time_steps_per_frame.value_max
            row.label(text=surface_tension_str)

        #
        # Sheeting Effects Panel
        #
        box = self.layout.box()
        header, body = box.panel("sheeting_effects_settings", default_closed=True)

        row = header.row(align=True)
        if not body:
            row.prop(wprops, "enable_sheet_seeding", text="")
        row.label(text="Sheeting Effects:")
        if body:
            column = body.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_left.prop(wprops, "enable_sheet_seeding")
            column_right = split.column(align=True)
            column_right.enabled = wprops.enable_sheet_seeding
            column_right.prop(wprops, "sheet_fill_rate")
            column_right.prop(wprops, "sheet_fill_threshold")
            
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
        
        #
        # Variable Density Panel
        #
        box = self.layout.box()
        header, body = box.panel("variable_density_settings", default_closed=True)

        row = header.row(align=True)
        if not body:
            row.prop(wprops, "enable_density_attribute", text="")
        row.label(text="Variable Density:")
        if body:
            column = body.column(align=True)
            column.prop(wprops, "enable_density_attribute")

            column = body.column(align=True)
            column.enabled = wprops.enable_density_attribute
            column.label(text="Variable density values can be set in the", icon='INFO')
            column.label(text="Fluid or Inflow physics properties menu", icon='INFO')
                    
        #
        # Friction Panel
        #
        box = self.layout.box()
        header, body = box.panel("friction_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Friction:")
        if body:
            column = body.column()
            split = column.split(align=True)
            column_left = split.column()
            column_left.label(text="Boundary Friction:")
            column_right = split.column()
            column_right.prop(wprops, "boundary_friction", text="")

            #
            # Obstacle Friction Panel
            #
            box = body.box()
            header_obstacle_friction, body_obstacle_friction = box.panel("obstacle_friction_settings", default_closed=True)

            row_obstacle_friction = header_obstacle_friction.row(align=True)
            row_obstacle_friction.label(text="Obstacle Friction:")
            if body_obstacle_friction:
                obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()

                column = body_obstacle_friction.column(align=True)
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
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="Boundary Friction  ")
            row.prop(wprops, "boundary_friction", text="")

    
def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidWorldPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidWorldPanel)
