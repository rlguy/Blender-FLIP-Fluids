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


class FLIPFLUID_PT_CacheObjectTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Mesh Display"

    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        obj = vcu.get_active_object(context)
        return dprops.mesh_cache.is_cache_object(obj)


    def get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def draw_surface_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Surface Render Display:")
        column_left.prop(rprops, "render_display", text="")

        column_right = split.column()
        column_right.label(text="Surface Viewport Display:")
        column_right.prop(rprops, "viewport_display", text="")


    def draw_whitewater_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Whitewater Render Display:")
        column_left.prop(rprops, "whitewater_render_display", text="")

        column_right = split.column()
        column_right.label(text="Whitewater Viewport Display:")
        column_right.prop(rprops, "whitewater_viewport_display", text="")


    def draw_whitewater_viewport_render_settings(self, render_pct_prop, viewport_pct_prop):
        dprops = self.get_domain_properties()
        rprops = dprops.render
        show_advanced = not vcu.get_addon_preferences(bpy.context).beginner_friendly_mode

        box = self.layout.box()

        if show_advanced:
            box.label(text="Display Settings Mode:")
            row = box.row()
            row.prop(rprops, "whitewater_view_settings_mode", expand=True)

        column = box.column(align=True)
        split = column.split()
        column = split.column(align = True)
        column.label(text="Final Display Settings:")
        column.prop(rprops, render_pct_prop, slider = True)

        column = split.column(align = True)
        column.label(text="Preview Display Settings:")
        column.prop(rprops, viewport_pct_prop, slider = True)


    def draw_whitewater_particle_object_settings(self, 
                                                 label_str,
                                                 object_prop,
                                                 scale_prop,
                                                 particle_object_mode_prop,
                                                 render_display_prop):
        dprops = self.get_domain_properties()
        rprops = dprops.render
        show_advanced = not vcu.get_addon_preferences(bpy.context).beginner_friendly_mode

        if not show_advanced:
            box = self.layout.box()
            box.label(text="Particle Object Settings:")
            row = box.row(align=True)
            row.prop(rprops, scale_prop)
            row.prop(rprops, render_display_prop)
            return

        box = self.layout.box()
        box.label(text="Particle Object Settings Mode:")
        row = box.row()
        row.prop(rprops, "whitewater_particle_object_settings_mode", expand=True)

        box = box.box()
        column = box.column()
        column.label(text=label_str)
        split = vcu.ui_split(column, factor=0.75, align=True)
        column1 = split.column(align=True)
        column2 = split.column(align=True)
        row = column1.row(align=True)
        row.prop(rprops, particle_object_mode_prop, expand=True)
        row = column2.row(align=True)
        row.enabled = getattr(rprops, particle_object_mode_prop) == 'WHITEWATER_PARTICLE_CUSTOM'
        row.prop(rprops, object_prop, text="")
        row = column.row()
        row.prop(rprops, scale_prop, text="Particle Scale")
        row.prop(rprops, render_display_prop, text="Hide particles in viewport")


    def draw_whitewater_material_settings(self, domain_props, prop_str, material_prop):
        dprops = self.get_domain_properties()

        self.layout.separator()
        box = self.layout.box()
        box.label(text="Material Library")
        box.prop(dprops.materials, material_prop, text=prop_str)
        box.separator()


    def draw_surface(self, cache_props, domain_props):
        dprops = self.get_domain_properties()

        column = self.layout.column()
        column.label(text="Surface")
        column.separator()

        self.draw_surface_viewport_render_display()

        column = self.layout.column()
        column.separator()
        split = column.split()
        column_left = split.column(align=True)
        column_right = split.column(align=True)

        column_left.label(text="Surface Material")
        column_right.prop(dprops.materials, "surface_material", text="")


    def draw_foam(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Foam")
        column.separator()
        
        self.draw_whitewater_viewport_render_display()

        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            self.draw_whitewater_viewport_render_settings(
                    'render_whitewater_pct',
                    'viewport_whitewater_pct'
                    )
        else:
            self.draw_whitewater_viewport_render_settings(
                    'render_foam_pct',
                    'viewport_foam_pct'
                    )

        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            self.draw_whitewater_particle_object_settings(
                    "Whitewater Particle Object:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_particle_object_mode',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Foam Particle Object:",
                    'foam_particle_object',
                    'foam_particle_scale',
                    'foam_particle_object_mode',
                    'only_display_foam_in_render'
                    )

        self.draw_whitewater_material_settings(
                domain_props, 
                "Foam", 
                'whitewater_foam_material'
                )


    def draw_bubble(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Bubble")
        column.separator()
        
        self.draw_whitewater_viewport_render_display()
        
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            self.draw_whitewater_viewport_render_settings(
                    'render_whitewater_pct',
                    'viewport_whitewater_pct'
                    )
        else:
            self.draw_whitewater_viewport_render_settings(
                    'render_bubble_pct',
                    'viewport_bubble_pct'
                    )

        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            self.draw_whitewater_particle_object_settings(
                    "Whitewater Particle Object:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_particle_object_mode',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Bubble Particle Object:",
                    'bubble_particle_object',
                    'bubble_particle_scale',
                    'bubble_particle_object_mode',
                    'only_display_bubble_in_render'
                    )

        self.draw_whitewater_material_settings(
                domain_props, 
                "Bubble", 
                'whitewater_bubble_material'
                )


    def draw_spray(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Spray")
        column.separator()

        self.draw_whitewater_viewport_render_display()
        
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            self.draw_whitewater_viewport_render_settings(
                    'render_whitewater_pct',
                    'viewport_whitewater_pct'
                    )
        else:
            self.draw_whitewater_viewport_render_settings(
                    'render_spray_pct',
                    'viewport_spray_pct'
                    )

        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            self.draw_whitewater_particle_object_settings(
                    "Whitewater Particle Object:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_particle_object_mode',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Spray Particle Object:",
                    'spray_particle_object',
                    'spray_particle_scale',
                    'spray_particle_object_mode',
                    'only_display_spray_in_render'
                    )

        self.draw_whitewater_material_settings(
                domain_props, 
                "Spray", 
                'whitewater_spray_material'
                )

    def draw_dust(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Dust")
        column.separator()

        self.draw_whitewater_viewport_render_display()
        
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            self.draw_whitewater_viewport_render_settings(
                    'render_whitewater_pct',
                    'viewport_whitewater_pct'
                    )
        else:
            self.draw_whitewater_viewport_render_settings(
                    'render_dust_pct',
                    'viewport_dust_pct'
                    )

        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            self.draw_whitewater_particle_object_settings(
                    "Whitewater Particle Object:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_particle_object_mode',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Dust Particle Object:",
                    'dust_particle_object',
                    'dust_particle_scale',
                    'dust_particle_object_mode',
                    'only_display_dust_in_render'
                    )

        self.draw_whitewater_material_settings(
                domain_props, 
                "Dust", 
                'whitewater_dust_material'
                )


    def draw(self, context):
        dprops = self.get_domain_properties()

        obj = vcu.get_active_object(context)
        cache_props = dprops.mesh_cache.get_mesh_cache_from_blender_object(obj)
        if cache_props is None:
            return

        if cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_SURFACE':
            self.draw_surface(cache_props, dprops)
        elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_FOAM':
            self.draw_foam(cache_props, dprops)
        elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_BUBBLE':
            self.draw_bubble(cache_props, dprops)
        elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_SPRAY':
            self.draw_spray(cache_props, dprops)
        elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_DUST':
            self.draw_dust(cache_props, dprops)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_CacheObjectTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_CacheObjectTypePanel)
