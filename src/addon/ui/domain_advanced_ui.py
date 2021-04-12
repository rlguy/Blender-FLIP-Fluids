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
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        obj = vcu.get_active_object(context)
        aprops = obj.flip_fluid.domain.advanced
        wprops = obj.flip_fluid.domain.world
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Advanced Settings Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Advanced-Settings"

        subbox = self.layout.box()
        column = subbox.column(align=True)
        column.label(text="Frame Substeps:")

        if wprops.enable_surface_tension and aprops.min_max_time_steps_per_frame.value_max < wprops.minimum_surface_tension_substeps:
            row = column.row(align=True)
            row.alert = True
            row.prop(aprops, "surface_tension_substeps_exceeded_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="  Warning: Not Enough Max Substeps")

        row = column.row(align=True)
        row.prop(aprops.min_max_time_steps_per_frame, "value_min", text="Min")
        row.prop(aprops.min_max_time_steps_per_frame, "value_max", text="Max")
        column.prop(aprops, "CFL_condition_number")

        if show_advanced:
            column.prop(aprops, "enable_adaptive_obstacle_time_stepping")
            column.prop(aprops, "enable_adaptive_force_field_time_stepping")

        if show_documentation:
            column = subbox.column(align=True)
            column.operator(
                    "wm.url_open", 
                    text="What are substeps?", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Advanced-Settings#what-are-substeps-and-how-do-the-min-max-and-cfl-parameters-relate-to-each-other"

        subbox = self.layout.box()
        column = subbox.column(align=True)
        column.label(text="Simulation Method:")
        row = column.row(align=True)
        row.prop(aprops, "velocity_transfer_method", expand=True)
        if aprops.velocity_transfer_method == 'VELOCITY_TRANSFER_METHOD_FLIP':
            column.prop(aprops, "PICFLIP_ratio", slider=True)
        else:
            column.label(text="")

        if show_documentation:
            column = subbox.column(align=True)
            column.operator(
                "wm.url_open", 
                text="What are applications of the PIC/FLIP Ratio?", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Advanced-Settings#simulation-stability"
            column.operator(
                "wm.url_open", 
                text="FLIP vs APIC", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Advanced-Settings#flip-vs-apic"

        subbox = self.layout.box()
        column = subbox.column()
        column.label(text="Simulation Stability:")

        if show_advanced:
            row = column.row(align=True)
            row.prop(aprops, "particle_jitter_factor", slider=True)
            row.prop(aprops, "jitter_surface_particles")
            column.prop(aprops, "enable_extreme_velocity_removal")

        if show_advanced:
            subbox = self.layout.box()
            column = subbox.column()
            split = column.split(align=True)

            column_left = split.column(align=True)
            column_left.label(text="Multithreading:")
            row = column_left.row(align=True)
            row.prop(aprops, "threading_mode", expand=True)
            row = column_left.row(align=True)
            if aprops.threading_mode == 'THREADING_MODE_AUTO_DETECT':
                row.enabled = False
                row.prop(aprops, "num_threads_auto_detect")
            elif aprops.threading_mode == 'THREADING_MODE_FIXED':
                row.prop(aprops, "num_threads_fixed")

            if show_documentation:
                column = subbox.column(align=True)
                column.operator(
                    "wm.url_open", 
                    text="CPU usage is under 100%, is this normal?", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions#my-cpu-is-running-under-100-usage-while-simulating-is-this-normal"
            
            # Performance and optimization settings are hidden from the UI.
            # These should always be enabled for performance.
            """
            column = self.layout.column(align=True)
            column.separator()
            column.label(text="Performance and Optimization:")
            column.prop(aprops, "enable_asynchronous_meshing")
            column.prop(aprops, "precompute_static_obstacles")
            column.prop(aprops, "reserve_temporary_grids")
            """

            subbox = self.layout.box()
            column = subbox.column(align=True)
            column.separator()
            column.label(text="Warnings and Errors:")
            column.prop(aprops, "disable_changing_topology_warning")
        
    
def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeAdvancedPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeAdvancedPanel)
