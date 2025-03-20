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


class FLIPFLUID_PT_DomainTypeDebugPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Debug"
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
        gprops = obj.flip_fluid.domain.debug
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Debug Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Debug-Settings"
            column.operator(
                "wm.url_open", 
                text="How to use grid visualization and obstacle debugging", 
                icon="WORLD"
            ).url = "https://blendermarket.com/posts/flip-fluids-10-tips-to-improve-your-blender-workflow"

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(gprops, "grid_display_settings_expanded",
            icon="TRIA_DOWN" if gprops.grid_display_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        if not gprops.grid_display_settings_expanded:
                row.prop(gprops, "display_simulation_grid", text="")
        row.label(text="Grid Visualization:")

        if gprops.grid_display_settings_expanded:
            split = vcu.ui_split(box, align=True, factor=0.3)
            column = split.column(align=True)
            column.prop(gprops, "display_simulation_grid", text="Display Grid")

            column = split.column(align=True)
            column.enabled = gprops.display_simulation_grid
            split = column.split(align=True)
            column = split.column(align=True)
            column.prop(gprops, "grid_display_mode", text="")
            column = split.column(align=True)
            column.prop(gprops, "grid_display_scale", text="Draw Scale")

            split = vcu.ui_split(box, align=True, factor=0.3)
            column = split.column(align=True)
            column.enabled = gprops.display_simulation_grid
            column.label(text="Enabled Grids:")
            column.label(text="Grid Colors:")
            column.label(text="Grid Offsets:")
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
            
            column = box.column(align=True)
            split = vcu.ui_split(column, align=True, factor=0.3)
            column = split.column(align=True)
            column.prop(gprops, "display_domain_bounds")

            column = split.column(align=True)
            column.enabled = gprops.display_simulation_grid or gprops.display_domain_bounds
            column.prop(gprops, "domain_bounds_color", text="")

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(gprops, "particle_debug_settings_expanded",
            icon="TRIA_DOWN" if gprops.particle_debug_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
            )
        if not gprops.particle_debug_settings_expanded:
            row.prop(gprops, "enable_fluid_particle_debug_output", text="")
        row.label(text="Fluid Particle Debugging:")

        next_row = row.row()
        next_row.alignment = 'RIGHT'
        next_row.prop(gprops, "fluid_particles_visibility", 
            text="", 
            icon=vcu.get_hide_off_icon() if gprops.fluid_particles_visibility else vcu.get_hide_on_icon(),
            emboss=False
            )


        if gprops.particle_debug_settings_expanded:
            box.prop(gprops, "enable_fluid_particle_debug_output")
            column = box.column(align=True)
            column.enabled = gprops.enable_fluid_particle_debug_output
            column.label(text="Particle Display Settings:")
            row = column.row(align=True)
            row.prop(gprops, "min_gradient_speed")
            row.prop(gprops, "max_gradient_speed")
            row = column.row(align=True)
            row.prop(gprops, "low_speed_particle_color", text="")
            row.prop(gprops, "high_speed_particle_color", text="")
            row = column.row(align=True)
            row.prop(gprops, "fluid_particle_gradient_mode", expand=True)

            column = box.column()
            column.enabled = gprops.enable_fluid_particle_debug_output
            split = vcu.ui_split(column, factor=0.33)
            column = split.column()
            column.label(text="Particle Size:")
            column.label(text="Draw Bounds:")
            column = split.column()
            column.prop(gprops, "particle_size", text="")
            column.prop_search(gprops, "particle_draw_aabb", bpy.data, "objects", text="")

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(gprops, "force_field_debug_settings_expanded",
            icon="TRIA_DOWN" if gprops.force_field_debug_settings_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        if not gprops.force_field_debug_settings_expanded:
            row.prop(gprops, "export_force_field", text="")
        row.label(text="Force Field Debugging:")

        next_row = row.row()
        next_row.alignment = 'RIGHT'
        next_row.prop(gprops, "force_field_visibility", 
            text="", 
            icon=vcu.get_hide_off_icon() if gprops.force_field_visibility else vcu.get_hide_on_icon(),
            emboss=False
            )

        if gprops.force_field_debug_settings_expanded:
            box.prop(gprops, "export_force_field")
            column = box.column(align=True)
            column.enabled = gprops.export_force_field
            column.label(text="Force Field Display Settings:")

            row = column.row(align=True)
            row.prop(gprops, "min_gradient_force")
            row.prop(gprops, "max_gradient_force")
            row = column.row(align=True)
            row.prop(gprops, "low_force_field_color", text="")
            row.prop(gprops, "high_force_field_color", text="")
            row = column.row(align=True)
            row.prop(gprops, "force_field_gradient_mode", expand=True)

            column = box.column()
            column.enabled = gprops.export_force_field
            split = vcu.ui_split(column, factor=0.33)
            column = split.column()
            column.label(text="Display Amount:")
            column.label(text="Line Size:")
            column = split.column()

            column.prop(gprops, "force_field_display_amount", text="")
            column.prop(gprops, "force_field_line_size", text="")

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(gprops, "export_internal_obstacle_mesh")
        next_row = row.row()
        next_row.alignment = 'RIGHT'
        next_row.prop(gprops, "internal_obstacle_mesh_visibility", 
                text="", 
                icon=vcu.get_hide_off_icon() if gprops.internal_obstacle_mesh_visibility else vcu.get_hide_on_icon(),
                emboss=False
                )

        box = self.layout.box()
        column = box.column(align=True)
        column.prop(gprops, "display_render_passes_console_output")
        column.prop(gprops, "display_console_output")


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeDebugPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeDebugPanel)
