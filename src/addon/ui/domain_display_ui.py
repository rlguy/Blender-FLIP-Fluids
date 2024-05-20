# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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

from ..operators import helper_operators
from ..utils import version_compatibility_utils as vcu


def draw_simulation_display_settings(self, context):
    domain_object = vcu.get_active_object(context)
    rprops = domain_object.flip_fluid.domain.render
    scene_props = context.scene.flip_fluid

    box = self.layout.box()
    column = box.column()

    row = column.row(align=True)
    row.prop(rprops, "simulation_display_settings_expanded",
        icon="TRIA_DOWN" if rprops.simulation_display_settings_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )

    row.label(text="Simulation Visibility:")
    if not scene_props.show_viewport or not scene_props.show_render:
        visibility_text = ""
        if not scene_props.show_viewport and not scene_props.show_render:
            visibility_text += "Disabled in Viewport + Render"
        elif not scene_props.show_viewport:
            visibility_text += "Disabled in Viewport"
        elif not scene_props.show_render:
            visibility_text += "Disabled in Render"
            
        row = row.row(align=True)
        row.alert = True
        row.alignment = 'RIGHT'
        row.label(text=visibility_text, icon="CANCEL")

    if scene_props.show_viewport and scene_props.show_render:
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Visibility Enabled", icon="CHECKMARK")

    if not rprops.simulation_display_settings_expanded:
        return

    split = vcu.ui_split(column)
    column_left = split.column()
    column_left.prop(scene_props, "show_render", text="Show In Render", icon="RESTRICT_RENDER_OFF")

    column_right = split.column()
    column_right.prop(scene_props, "show_viewport", text="Show In Viewport", icon="RESTRICT_VIEW_OFF")


def draw_surface_display_settings(self, context, menu_expand_prop_group=None):
    domain_object = vcu.get_active_object(context)
    rprops = domain_object.flip_fluid.domain.render
    mprops = domain_object.flip_fluid.domain.materials

    box = self.layout.box()
    column = box.column()

    row = column.row(align=True)
    row.prop(menu_expand_prop_group, "surface_display_settings_expanded",
        icon="TRIA_DOWN" if getattr(menu_expand_prop_group, "surface_display_settings_expanded") else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Surface Display and Render:")

    if not getattr(menu_expand_prop_group, "surface_display_settings_expanded"):
        info_text = ""
        if rprops.render_display == 'DISPLAY_FINAL':
            info_text += "Render Final"
        elif rprops.render_display == 'DISPLAY_PREVIEW':
            info_text += "Render Preview"
        elif rprops.render_display == 'DISPLAY_NONE':
            info_text += "Render None"
        info_text += " / "
        if rprops.viewport_display == 'DISPLAY_FINAL':
            info_text += "View Final"
        elif rprops.viewport_display == 'DISPLAY_PREVIEW':
            info_text += "View Preview"
        elif rprops.viewport_display == 'DISPLAY_NONE':
            info_text += "View None"
        row = row.row(align=True)
        row.alignment='RIGHT'
        row.label(text=info_text)
        return

    split = vcu.ui_split(column, factor=0.5)
    column_left = split.column()
    column_left.label(text="Render Display Mode:")
    column_left.prop(rprops, "render_display", expand=True)

    column_right = split.column()
    column_right.label(text="Viewport Display Mode:")
    column_right.prop(rprops, "viewport_display", expand=True)

    column_left.label(text="Surface Material:")
    column_right.prop(mprops, "surface_material", text="")


def draw_fluid_particle_display_settings(self, context, menu_expand_prop_group=None):
    domain_object = vcu.get_active_object(context)
    dprops = domain_object.flip_fluid.domain
    rprops = domain_object.flip_fluid.domain.render
    mprops = domain_object.flip_fluid.domain.materials
    is_fluid_particles_enabled = domain_object.flip_fluid.domain.particles.enable_fluid_particle_output

    box = self.layout.box()
    column = box.column()

    if is_fluid_particles_enabled:
        row = column.row(align=True)
        row.prop(menu_expand_prop_group, "fluid_particle_display_settings_expanded",
            icon="TRIA_DOWN" if getattr(menu_expand_prop_group, "fluid_particle_display_settings_expanded") else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Fluid Particle Display and Render:")
    else:
        split = column.split()
        left_column = split.column()
        row = left_column.row(align=True)
        row.prop(menu_expand_prop_group, "fluid_particle_display_settings_expanded",
            icon="TRIA_DOWN" if getattr(menu_expand_prop_group, "fluid_particle_display_settings_expanded") else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Fluid Particle Display and Render:")

        right_column = split.column()
        row = right_column.row()
        row.alignment = 'RIGHT'
        c = row.row(align=True)
        c.alignment = 'RIGHT'
        c.enabled = False
        c.label(text="Enable in 'Particles' panel")
        row.operator("flip_fluid_operators.display_enable_fluid_particles_tooltip", 
                     text="", icon="QUESTION", emboss=False)

    if not getattr(menu_expand_prop_group, "fluid_particle_display_settings_expanded"):
        if is_fluid_particles_enabled:
            info_text = ""
            if rprops.fluid_particle_render_display == 'DISPLAY_FINAL':
                info_text += "Render Final"
            elif rprops.fluid_particle_render_display == 'DISPLAY_PREVIEW':
                info_text += "Render Preview"
            elif rprops.fluid_particle_render_display == 'DISPLAY_NONE':
                info_text += "Render None"
            info_text += " / "
            if rprops.fluid_particle_viewport_display == 'DISPLAY_FINAL':
                info_text += "View Final"
            elif rprops.fluid_particle_viewport_display == 'DISPLAY_PREVIEW':
                info_text += "View Preview"
            elif rprops.fluid_particle_viewport_display == 'DISPLAY_NONE':
                info_text += "View None"
            row = row.row(align=True)
            row.alignment='RIGHT'
            row.label(text=info_text)
            return

    if getattr(menu_expand_prop_group, "fluid_particle_display_settings_expanded"):
        subbox = box.box()
        column = subbox.column(align=True)
        column.enabled = is_fluid_particles_enabled
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Render Display Mode:")
        column_left.prop(rprops, "fluid_particle_render_display", expand=True)

        column_right = split.column()
        column_right.label(text="Viewport Display Mode:")
        column_right.prop(rprops, "fluid_particle_viewport_display", expand=True)

        subbox = box.box()
        column = subbox.column(align=True)
        column.enabled = is_fluid_particles_enabled
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column(align=True)
        column_left.label(text="Final Display Amount:")
        column_left.prop(rprops, "render_fluid_particle_surface_pct", slider=True)
        column_left.prop(rprops, "render_fluid_particle_boundary_pct", slider=True)
        column_left.prop(rprops, "render_fluid_particle_interior_pct", slider=True)

        column_right = split.column(align=True)
        column_right.label(text="Preview Display Amount:")
        column_right.prop(rprops, "viewport_fluid_particle_surface_pct", slider=True)
        column_right.prop(rprops, "viewport_fluid_particle_boundary_pct", slider=True)
        column_right.prop(rprops, "viewport_fluid_particle_interior_pct", slider=True)

        bl_fluid_particles_mesh_cache = dprops.mesh_cache.particles.get_cache_object()

        subbox = box.box()
        subbox.enabled = is_fluid_particles_enabled
        column = subbox.column(align=True)
        column.label(text="Particle Display Settings:")
        column.separator()

        bl_mod = get_motion_blur_geometry_node_modifier(bl_fluid_particles_mesh_cache)
        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Fluid Particles:")
        draw_fluid_particles_motion_blur_geometry_node_properties(row, bl_mod)

        subbox = box.box()
        column = subbox.column(align=True)
        column.enabled = is_fluid_particles_enabled
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_right = split.column()
        column_left.label(text="Fluid Particle Material:")
        column_right.prop(mprops, "fluid_particles_material", text="")


def get_motion_blur_geometry_node_modifier(bl_object):
    if bl_object is None:
        return None
    for mod in bl_object.modifiers:
        if mod.type == "NODES" and mod.node_group and mod.node_group.name.startswith("FF_MotionBlur"):
            return mod


def draw_whitewater_particles_motion_blur_geometry_node_properties(ui_row, bl_mod):
    if bl_mod is None:
        ui_row.alert = True
        ui_row.operator(
            "flip_fluid_operators.helper_initialize_cache_objects", 
            text="Initialize Geometry Nodes - Missing FF_MotionBlurWhitewater modifier",
            icon="ERROR"
            ).cache_object_type = 'CACHE_OBJECT_TYPE_WHITEWATER_PARTICLES'
        return

    ui_row.alignment = 'LEFT'
    if "Input_6" in bl_mod:
        ui_row.prop(bl_mod, '["Input_6"]',  text="Scale")
    if "Input_4" in bl_mod:
        ui_row.prop(bl_mod, '["Input_4"]',  text="Blur Scale")
    if "Input_8" in bl_mod:
        ui_row.prop(bl_mod, '["Input_8"]',  text="Motion Blur")
    if "Input_9" in bl_mod:
        ui_row.prop(bl_mod, '["Input_9"]',  text="Point Cloud")


def draw_fluid_particles_motion_blur_geometry_node_properties(ui_row, bl_mod):
    if bl_mod is None:
        ui_row.alert = True
        ui_row.operator(
            "flip_fluid_operators.helper_initialize_cache_objects", 
            text="Initialize Geometry Nodes - Missing FF_MotionBlurFluidParticles modifier",
            icon="ERROR"
            ).cache_object_type = 'CACHE_OBJECT_TYPE_FLUID_PARTICLES'
        return

    ui_row.alignment = 'LEFT'
    if "Input_6" in bl_mod:
        ui_row.prop(bl_mod, '["Input_6"]',  text="Scale")
    if "Input_4" in bl_mod:
        ui_row.prop(bl_mod, '["Input_4"]',  text="Blur Scale")
    if "Input_8" in bl_mod:
        ui_row.prop(bl_mod, '["Input_8"]',  text="Motion Blur")
    if "Input_9" in bl_mod:
        ui_row.prop(bl_mod, '["Input_9"]',  text="Point Cloud")


def draw_whitewater_display_settings(self, context, menu_expand_prop_group=None):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    rprops = dprops.render
    is_whitewater_enabled = dprops.whitewater.enable_whitewater_simulation

    master_box = self.layout.box()
    column = master_box.column()

    if is_whitewater_enabled:
        row = column.row(align=True)
        row.prop(menu_expand_prop_group, "whitewater_display_settings_expanded",
            icon="TRIA_DOWN" if getattr(menu_expand_prop_group, "whitewater_display_settings_expanded") else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Whitewater Display and Render:")
    else:
        split = column.split()
        left_column = split.column()
        row = left_column.row(align=True)
        row.prop(menu_expand_prop_group, "whitewater_display_settings_expanded",
            icon="TRIA_DOWN" if getattr(menu_expand_prop_group, "whitewater_display_settings_expanded") else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Whitewater Display and Render:")

        right_column = split.column()
        row = right_column.row()
        row.alignment = 'RIGHT'
        c = row.row(align=True)
        c.alignment = 'RIGHT'
        c.enabled = False
        c.label(text="Enable in 'Whitewater' panel")
        row.operator("flip_fluid_operators.display_enable_whitewater_tooltip", 
                     text="", icon="QUESTION", emboss=False)

    if not getattr(menu_expand_prop_group, "whitewater_display_settings_expanded"):
        if is_whitewater_enabled:
            info_text = ""
            if rprops.whitewater_render_display == 'DISPLAY_FINAL':
                info_text += "Render Final"
            elif rprops.whitewater_render_display == 'DISPLAY_PREVIEW':
                info_text += "Render Preview"
            elif rprops.whitewater_render_display == 'DISPLAY_NONE':
                info_text += "Render None"
            info_text += " / "
            if rprops.whitewater_viewport_display == 'DISPLAY_FINAL':
                info_text += "View Final"
            elif rprops.whitewater_viewport_display == 'DISPLAY_PREVIEW':
                info_text += "View Preview"
            elif rprops.whitewater_viewport_display == 'DISPLAY_NONE':
                info_text += "View None"
            row = row.row(align=True)
            row.alignment='RIGHT'
            row.label(text=info_text)
            return

    if getattr(menu_expand_prop_group, "whitewater_display_settings_expanded"):
        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label(text="Render Display Mode:")
        column.prop(rprops, "whitewater_render_display", expand=True)

        column = split.column(align=True)
        column.label(text="Viewport Display Mode:")
        column.prop(rprops, "whitewater_viewport_display", expand=True)

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

        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label(text="Final Display Amount:")
        column.prop(rprops, "render_foam_pct", slider=True)
        column.prop(rprops, "render_bubble_pct", slider=True)
        column.prop(rprops, "render_spray_pct", slider=True)
        column.prop(rprops, "render_dust_pct", slider=True)

        column = split.column(align=True)
        column.label(text="Preview Display Amount:")
        column.prop(rprops, "viewport_foam_pct", slider=True)
        column.prop(rprops, "viewport_bubble_pct", slider=True)
        column.prop(rprops, "viewport_spray_pct", slider=True)
        column.prop(rprops, "viewport_dust_pct", slider=True)

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        column.label(text="Particle Display Settings:")

        column.separator()
        split = vcu.ui_split(column, factor=0.1)
        column1 = split.column(align=True)
        column2 = split.column(align=True)

        whitewater_labels = ["Foam:", "Bubble:", "Spray:", "Dust:"]
        mesh_cache_objects = [
                dprops.mesh_cache.foam.get_cache_object(),
                dprops.mesh_cache.bubble.get_cache_object(),
                dprops.mesh_cache.spray.get_cache_object(),
                dprops.mesh_cache.dust.get_cache_object()
            ]

        for idx, bl_object in enumerate(mesh_cache_objects):
            bl_mod = get_motion_blur_geometry_node_modifier(bl_object)
            row = column1.row(align=True)
            row.label(text=whitewater_labels[idx])
            row = column2.row(align=True)
            draw_whitewater_particles_motion_blur_geometry_node_properties(row, bl_mod)

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        mprops = dprops.materials
        column = box.column(align=True)
        column.label(text="Particle Materials:")
        column.prop(mprops, "whitewater_foam_material", text="Foam")
        column.prop(mprops, "whitewater_bubble_material", text="Bubble")
        column.prop(mprops, "whitewater_spray_material", text="Spray")
        column.prop(mprops, "whitewater_dust_material", text="Dust")


class FLIPFLUID_PT_DomainTypeDisplayPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Display and Render Settings"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        if vcu.get_addon_preferences(context).enable_tabbed_domain_settings_view:
            return False
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN" and not is_addon_disabled


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

        draw_simulation_display_settings(self, context)
        draw_surface_display_settings(self, context, rprops)
        draw_fluid_particle_display_settings(self, context, rprops)
        draw_whitewater_display_settings(self, context, rprops)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeDisplayPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeDisplayPanel)
