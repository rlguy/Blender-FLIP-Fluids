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
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        column = self.layout.column(align=True)
        column.label(text="Frame Substeps:")
        row = column.row(align=True)
        row.prop(aprops.min_max_time_steps_per_frame, "value_min", text="Min")
        row.prop(aprops.min_max_time_steps_per_frame, "value_max", text="Max")

        if show_advanced:
            column.prop(aprops, "enable_adaptive_obstacle_time_stepping")

        column = self.layout.column()
        column.label(text="Simulation Stability:")

        if show_advanced:
            row = column.row(align=True)
            row.prop(aprops, "particle_jitter_factor", slider=True)
            row.prop(aprops, "jitter_surface_particles")
        column.prop(aprops, "PICFLIP_ratio", slider=True)
        column = self.layout.column(align=True)
        column.prop(aprops, "CFL_condition_number")

        if show_advanced:
            column.prop(aprops, "enable_extreme_velocity_removal")

        if show_advanced:
            column = self.layout.column()
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
            
            column = self.layout.column(align=True)
            column.separator()
            column.label(text="Performance and Optimization:")
            column.prop(aprops, "enable_asynchronous_meshing")
            column.prop(aprops, "precompute_static_obstacles")
            column.prop(aprops, "reserve_temporary_grids")

            # Allowing changing topology is disabled. Does not seem to be stable
            """
            column = self.layout.column(align=True)
            column.separator()
            column.label(text="Warnings and Errors:")
            column.prop(aprops, "disable_changing_topology_warning")
            """
        
    
def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeAdvancedPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeAdvancedPanel)
