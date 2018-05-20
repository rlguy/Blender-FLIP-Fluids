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


class FlipFluidDomainTypeDebugPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Debug"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        obj = context.scene.objects.active
        gprops = obj.flip_fluid.domain.debug

        box = self.layout.box()
        split = box.split(align=True, percentage=0.3)
        column = split.column(align=True)
        column.prop(gprops, "display_simulation_grid", text="Display Grid")
        column = split.column(align=True)
        column.enabled = gprops.display_simulation_grid
        split = column.split(align=True)
        column = split.column(align=True)
        column.prop(gprops, "grid_display_mode", text="")
        column = split.column(align=True)
        column.prop(gprops, "grid_display_scale", text="Draw Scale")

        split = box.split(align=True, percentage=0.3)
        column = split.column(align=True)
        column.enabled = gprops.display_simulation_grid
        column.label("Enabled Grids:")
        column.label("Grid Colors:")
        column.label("Grid Offsets:")
        column = split.column(align=True)
        column.enabled = gprops.display_simulation_grid
        row = column.row(align=True)
        row.prop(gprops, "enabled_debug_grids", text="", toggle=True)
        row = column.row(align=True)
        row.prop(gprops, "x_grid_color", text="")
        row.prop(gprops, "y_grid_color", text="")
        row.prop(gprops, "z_grid_color", text="")
        row = column.row(align=True)
        row.prop(gprops, "debug_grid_offsets", text="", slider=True)
        column.prop(gprops, "snap_offsets_to_grid")

        box = self.layout.box()
        box.prop(gprops, "export_fluid_particles")
        column = box.column(align=True)
        column.enabled = gprops.export_fluid_particles
        column.label("Particle Display Settings:")
        row = column.row(align=True)
        row.prop(gprops.min_max_gradient_speed, "value_min")
        row.prop(gprops.min_max_gradient_speed, "value_max")
        row = column.row(align=True)
        row.prop(gprops, "low_speed_particle_color", text="")
        row.prop(gprops, "high_speed_particle_color", text="")
        row = column.row(align=True)
        row.prop(gprops, "fluid_particle_gradient_mode", expand=True)

        column = box.column()
        column.enabled = gprops.export_fluid_particles
        split = column.split(percentage=0.33)
        column = split.column()
        column.label("Particle Size:")
        column.label("Draw Bounds:")
        column = split.column()
        column.prop(gprops, "particle_size", text="")
        column.prop_search(gprops, "particle_draw_aabb", context.scene, "objects", text="")

        column = self.layout.column(align=True)
        column.prop(gprops, "export_internal_obstacle_mesh")

        column = self.layout.column(align=True)
        column.prop(gprops, "display_console_output")


def register():
    bpy.utils.register_class(FlipFluidDomainTypeDebugPanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeDebugPanel)
