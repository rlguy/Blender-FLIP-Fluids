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

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_DomainTypeAdvancedPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Advanced Settings"
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
        aprops = obj.flip_fluid.domain.advanced
        wprops = obj.flip_fluid.domain.world

        #
        # Frame Substeps Panel
        #
        box = self.layout.box()
        header, body = box.panel("frame_substeps_settings", default_closed=False)

        row = header.row(align=True)
        row.label(text="Frame Substeps:")
        if body:
            column = body.column(align=True)
            if wprops.enable_surface_tension and aprops.min_max_time_steps_per_frame.value_max < wprops.minimum_surface_tension_substeps:
                row = column.row(align=True)
                row.alert = True
                row.prop(aprops, "surface_tension_substeps_exceeded_tooltip", icon="QUESTION", emboss=False, text="")
                row.label(text="  Warning: Not Enough Max Substeps")

            row = column.row(align=True)
            row.prop(aprops.min_max_time_steps_per_frame, "value_min", text="Min")
            row.prop(aprops.min_max_time_steps_per_frame, "value_max", text="Max")
            column.prop(aprops, "CFL_condition_number")
            column.prop(aprops, "enable_adaptive_obstacle_time_stepping")
            column.prop(aprops, "enable_adaptive_force_field_time_stepping")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(aprops.min_max_time_steps_per_frame, "value_min", text="Min")
            row.prop(aprops.min_max_time_steps_per_frame, "value_max", text="Max")

        #
        # Simulation Method Panel
        #
        box = self.layout.box()
        header, body = box.panel("simulation_method_settings", default_closed=False)

        row = header.row(align=True)
        row.label(text="Simulation Method:")
        if body:
            column = body.column(align=True)
            row = column.row(align=True)
            row.prop(aprops, "velocity_transfer_method", expand=True)
            if aprops.velocity_transfer_method == 'VELOCITY_TRANSFER_METHOD_FLIP':
                column.prop(aprops, "PICFLIP_ratio", slider=True)
            else:
                column.label(text="")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(aprops, "velocity_transfer_method", expand=True)
        
        #
        # Simulation and Particle Stability Panel
        #
        box = self.layout.box()
        header, body = box.panel("simulation_and_particle_stability_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Simulation and Particle Stability:")
        if body:
            column = body.column()
            row = column.row(align=True)
            row.prop(aprops, "particle_jitter_factor", slider=True)
            row.prop(aprops, "jitter_surface_particles")
            column.prop(aprops, "enable_extreme_velocity_removal")
            column.separator()
            column = body.column(align=True)
            column.prop(aprops, "pressure_solver_max_iterations")
            column.prop(aprops, "viscosity_solver_max_iterations")
        else:
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.prop(aprops, "jitter_surface_particles")

        #
        # Multithreading and Performance Panel
        #
        box = self.layout.box()
        header, body = box.panel("multithreading_and_performance_settings", default_closed=False)

        row = header.row(align=True)
        row.label(text="Multithreading and Performance:")
        if body:
            column = body.column()
            split = column.split(align=True)

            column_left = split.column(align=True)
            row = column_left.row(align=True)
            row.prop(aprops, "threading_mode", expand=True)
            row = column_left.row(align=True)
            if aprops.threading_mode == 'THREADING_MODE_AUTO_DETECT':
                row.enabled = False
                row.prop(aprops, "num_threads_auto_detect")
            elif aprops.threading_mode == 'THREADING_MODE_FIXED':
                row.prop(aprops, "num_threads_fixed")

            column = body.column()
            column.prop(aprops, "enable_fracture_optimization")
        else:
            info_text = ""
            if aprops.threading_mode == 'THREADING_MODE_AUTO_DETECT':
                info_text = "Auto-detect " + str(aprops.num_threads_auto_detect) + " threads"
            elif aprops.threading_mode == 'THREADING_MODE_FIXED':
                info_text = "Fixed " + str(aprops.num_threads_fixed) + " threads"

            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=info_text)

        #
        # Warnings and Errors Panel
        #
        box = self.layout.box()
        header, body = box.panel("warnings_and_errors_settings", default_closed=True)

        row = header.row(align=True)
        row.label(text="Warnings and Errors:")
        if body:
            column = body.column(align=True)
            column.prop(aprops, "disable_changing_topology_warning")
        
    
def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeAdvancedPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeAdvancedPanel)
