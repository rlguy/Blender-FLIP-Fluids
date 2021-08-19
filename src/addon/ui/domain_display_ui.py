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


class FLIPFLUID_PT_DomainTypeDisplayPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Display Settings"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def draw_render_settings(self, context):
        self.layout.separator()
        box = self.layout.box()
        box.label(text="Render Tools:")
        column = box.column(align=True)
        if vcu.is_blender_28():
            lock_interface = context.scene.render.use_lock_interface
            status = "Enabled" if lock_interface else 'Disabled'
            icon = 'FUND' if lock_interface else 'ERROR'

            if lock_interface:
                column.operator("flip_fluid_operators.helper_stable_rendering_28", text="Disable Stable Rendering").enable_state = False
            else:
                column.operator("flip_fluid_operators.helper_stable_rendering_28", text="Enable Stable Rendering").enable_state = True
                
            row = column.row(align=True)
            if not lock_interface:
                row.alert = True
            row.label(text="Current status: " + status, icon=icon)
        else:
            status = "Enabled" if context.scene.render.display_mode == 'SCREEN' else 'Disabled'
            icon = 'FILE_TICK' if context.scene.render.display_mode == 'SCREEN' else 'ERROR'
            column.operator("flip_fluid_operators.helper_stable_rendering_279")
            column.label(text="Current status: " + status, icon=icon)


    def draw_surface_display_settings(self, context):
        domain_object = vcu.get_active_object(context)
        rprops = domain_object.flip_fluid.domain.render
        mprops = domain_object.flip_fluid.domain.materials
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        box = self.layout.box()
        column = box.column()
        column.label(text="Surface Display Settings:")
        column.separator()

        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Surface Render Display:")
        column_left.prop(rprops, "render_display", expand=True)

        column_right = split.column()
        column_right.label(text="Surface Viewport Display:")
        column_right.prop(rprops, "viewport_display", expand=True)

        column_left.label(text="Surface Material")
        column_right.prop(mprops, "surface_material", text="")

        # Motion blur rendering is currently not supported due
        # to limitations in Blender
        """
        if show_advanced:
            column = box.column()
            column.label(text="Motion Blur:")

            split = vcu.ui_split(column, factor=0.5)
            column_left = split.column()
            column_left.prop(rprops, "render_surface_motion_blur")

            column_right = split.column()
            column_right.prop(rprops, "surface_motion_blur_scale")
        """



    def draw_whitewater_display_settings(self, context):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        rprops = dprops.render
        is_whitewater_enabled = dprops.whitewater.enable_whitewater_simulation
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        self.layout.separator()

        master_box = self.layout.box()
        column = master_box.column()

        if is_whitewater_enabled:
            row = column.row(align=True)
            row.prop(rprops, "whitewater_display_settings_expanded",
                icon="TRIA_DOWN" if rprops.whitewater_display_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Whitewater Display Settings:")
        else:
            split = column.split()
            left_column = split.column()
            row = left_column.row(align=True)
            row.prop(rprops, "whitewater_display_settings_expanded",
                icon="TRIA_DOWN" if rprops.whitewater_display_settings_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Whitewater Display Settings:")

            right_column = split.column()
            row = right_column.row()
            row.alignment = 'LEFT'
            c = row.column()
            c.enabled = False
            c.label(text="Enable in 'Whitewater' panel")
            row.operator("flip_fluid_operators.display_enable_whitewater_tooltip", 
                         text="", icon="QUESTION", emboss=False)

        if not rprops.whitewater_display_settings_expanded:
            return

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label(text="Whitewater Render Display:")
        column.prop(rprops, "whitewater_render_display", expand=True)

        column = split.column(align=True)
        column.label(text="Whitewater Viewport Display:")
        column.prop(rprops, "whitewater_viewport_display", expand=True)
        master_box.separator()

        # Whitewater motion blur rendering is currently too resource intensive
        # for Blender Cycles
        """
        column = box.column()
        column.label(text="Motion Blur:")

        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.prop(rprops, "render_whitewater_motion_blur")

        column_right = split.column()
        column_right.prop(rprops, "whitewater_motion_blur_scale")
        """

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        if show_advanced:
            column = box.column(align=True)
            column.label(text="Display Settings Mode:")
            row = column.row()
            row.prop(rprops, "whitewater_view_settings_mode", expand=True)

        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label(text="Final Display Settings:")
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            column.prop(rprops, "render_whitewater_pct", slider=True)
        else:
            column.prop(rprops, "render_foam_pct", slider=True)
            column.prop(rprops, "render_bubble_pct", slider=True)
            column.prop(rprops, "render_spray_pct", slider=True)
            column.prop(rprops, "render_dust_pct", slider=True)

        column = split.column(align=True)
        column.label(text="Preview Display Settings:")
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            column.prop(rprops, "viewport_whitewater_pct", slider=True)
        else:
            column.prop(rprops, "viewport_foam_pct", slider=True)
            column.prop(rprops, "viewport_bubble_pct", slider=True)
            column.prop(rprops, "viewport_spray_pct", slider=True)
            column.prop(rprops, "viewport_dust_pct", slider=True)
        master_box.separator()

        if not show_advanced:
            box = master_box.box()
            box.enabled = is_whitewater_enabled
            box.label(text="Particle Object Settings:")
            row = box.row(align=True)
            row.prop(rprops, "whitewater_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_whitewater_in_render")
            return

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        column.label(text="Particle Object Settings Mode:")
        row = column.row()
        row.prop(rprops, "whitewater_particle_object_settings_mode", expand=True)
        column = box.column()

        box_column = box.column()
        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            column = box_column.column()
            column.label(text="Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "whitewater_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.whitewater_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop(rprops, "whitewater_particle_object", text="")
            row = column.row()
            row.prop(rprops, "whitewater_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_whitewater_in_render", text="Hide particles in viewport")
        else:
            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Foam Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "foam_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.foam_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop(rprops, "foam_particle_object", text="")
            row = column.row()
            row.prop(rprops, "foam_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_foam_in_render", text="Hide particles in viewport")

            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Bubble Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "bubble_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.bubble_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop(rprops, "bubble_particle_object", text="")
            row = column.row()
            row.prop(rprops, "bubble_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_bubble_in_render", text="Hide particles in viewport")

            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Spray Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "spray_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.spray_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop(rprops, "spray_particle_object", text="")
            row = column.row()
            row.prop(rprops, "spray_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_spray_in_render", text="Hide particles in viewport")

            particle_box = box_column.box()
            column = particle_box.column()
            column.label(text="Dust Particle Object:")
            split = vcu.ui_split(column, factor=0.75, align=True)
            column1 = split.column(align=True)
            column2 = split.column(align=True)
            row = column1.row(align=True)
            row.prop(rprops, "dust_particle_object_mode", expand=True)
            row = column2.row(align=True)
            row.enabled = rprops.dust_particle_object_mode == 'WHITEWATER_PARTICLE_CUSTOM'
            row.prop(rprops, "dust_particle_object", text="")
            row = column.row()
            row.prop(rprops, "dust_particle_scale", text="Particle Scale")
            row.prop(rprops, "only_display_dust_in_render", text="Hide particles in viewport")

        master_box.separator()
        box = master_box.box()
        box.enabled = is_whitewater_enabled

        mprops = dprops.materials
        column = box.column(align=True)
        column.label(text="Particle Materials:")
        column.prop(mprops, "whitewater_foam_material", text="Foam")
        column.prop(mprops, "whitewater_bubble_material", text="Bubble")
        column.prop(mprops, "whitewater_spray_material", text="Spray")
        column.prop(mprops, "whitewater_dust_material", text="Dust")


    def draw(self, context):
        domain_object = vcu.get_active_object(context)
        rprops = domain_object.flip_fluid.domain.render
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Display and Render Settings Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Display-Settings"
            column.operator(
                "wm.url_open", 
                text="Rendering from the command line", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Rendering-from-the-Command-Line"
            column.operator(
                "wm.url_open", 
                text="Whitewater particles are rendered too large", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#whitewater-particles-are-too-largesmall-when-rendered"
            column.operator(
                "wm.url_open", 
                text="Whitewater particles are not rendered in preview render", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#whitewater-particles-are-not-rendered-when-viewport-shading-is-set-to-rendered"
            column.operator(
                "wm.url_open", 
                text="Simulation meshes not appearing in viewport/render", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#simulation-meshes-are-not-appearing-in-the-viewport-andor-render"

        self.draw_surface_display_settings(context)
        self.draw_whitewater_display_settings(context)
        self.draw_render_settings(context)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeDisplayPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeDisplayPanel)
