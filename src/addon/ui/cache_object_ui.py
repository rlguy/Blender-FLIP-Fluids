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

from . import domain_display_ui
from ..operators import helper_operators
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
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            return False
        obj = vcu.get_active_object(context)
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return dprops.mesh_cache.is_cache_object(obj) and not is_addon_disabled


    def get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def draw_surface_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Render Display Mode:")
        column_left.prop(rprops, "render_display", expand=True)

        column_right = split.column()
        column_right.label(text="Viewport Display Mode:")
        column_right.prop(rprops, "viewport_display", expand=True)


    def draw_fluid_particle_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Render Display Mode:")
        column_left.prop(rprops, "fluid_particle_render_display", expand=True)

        column_right = split.column()
        column_right.label(text="Viewport Display Mode:")
        column_right.prop(rprops, "fluid_particle_viewport_display", expand=True)

        box = self.layout.box()
        column = box.column(align=True)
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column(align=True)
        column_left.label(text="Final Display Settings:")
        column_left.prop(rprops, "render_fluid_particle_surface_pct", slider=True)
        column_left.prop(rprops, "render_fluid_particle_boundary_pct", slider=True)
        column_left.prop(rprops, "render_fluid_particle_interior_pct", slider=True)

        column_right = split.column(align=True)
        column_right.label(text="Preview Display Settings:")
        column_right.prop(rprops, "viewport_fluid_particle_surface_pct", slider=True)
        column_right.prop(rprops, "viewport_fluid_particle_boundary_pct", slider=True)
        column_right.prop(rprops, "viewport_fluid_particle_interior_pct", slider=True)

        bl_fluid_particles_mesh_cache = dprops.mesh_cache.particles.get_cache_object()
        point_cloud_detected = helper_operators.is_geometry_node_point_cloud_detected(bl_fluid_particles_mesh_cache)

        box = self.layout.box()
        column = box.column(align=True)
        column.label(text="Particle Object Settings:")
        column.separator()

        bl_mod = domain_display_ui.get_motion_blur_geometry_node_modifier(bl_fluid_particles_mesh_cache)
        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Fluid Particles:")
        domain_display_ui.draw_fluid_particles_motion_blur_geometry_node_properties(row, bl_mod)


    def draw_whitewater_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column()
        column_left.label(text="Render Display Mode:")
        column_left.prop(rprops, "whitewater_render_display", expand=True)

        column_right = split.column()
        column_right.label(text="Viewport Display Mode:")
        column_right.prop(rprops, "whitewater_viewport_display", expand=True)


    def draw_whitewater_viewport_render_settings(self, render_pct_prop, viewport_pct_prop):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column(align=True)
        split = column.split()
        column = split.column(align = True)
        column.label(text="Final Display Amount:")
        column.prop(rprops, render_pct_prop, slider = True)

        column = split.column(align = True)
        column.label(text="Preview Display Amount:")
        column.prop(rprops, viewport_pct_prop, slider = True)


    def draw_whitewater_particle_object_settings(self, prop_str, material_prop):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        bl_object = vcu.get_active_object()

        box = self.layout.box()
        box.label(text="Particle Display Settings:")
        column = box.column(align=True)
        column.separator()
        split = vcu.ui_split(column, factor=0.1)
        column1 = split.column(align=True)
        column2 = split.column(align=True)

        cache_props = dprops.mesh_cache.get_mesh_cache_from_blender_object(bl_object)
        if cache_props is not None:
            if cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_FOAM':
                whitewater_label = "Foam:"
            elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_BUBBLE':
                whitewater_label = "Bubble:"
            elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_SPRAY':
                whitewater_label = "Spray:"
            elif cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_DUST':
                whitewater_label = "Dust:"

            bl_mod = domain_display_ui.get_motion_blur_geometry_node_modifier(bl_object)
            row = column1.row(align=True)
            row.label(text=whitewater_label)
            row = column2.row(align=True)
            domain_display_ui.draw_whitewater_particles_motion_blur_geometry_node_properties(row, bl_mod)

        dprops = self.get_domain_properties()

        self.layout.separator()
        box = self.layout.box()
        box.label(text="Material Library")
        box.prop(dprops.materials, material_prop, text=prop_str)
        box.separator()


    def draw_surface(self, cache_props, domain_props):
        dprops = self.get_domain_properties()

        column = self.layout.column()
        column.label(text="Fluid Surface")
        column.separator()

        self.draw_surface_viewport_render_display()

        column = self.layout.column()
        column.separator()
        split = column.split()
        column_left = split.column(align=True)
        column_right = split.column(align=True)

        column_left.label(text="Surface Material")
        column_right.prop(dprops.materials, "surface_material", text="")

        self.layout.separator()
        column = self.layout.column()
        column.operator("flip_fluid_operators.helper_delete_surface_objects", icon="X")


    def draw_fluid_particles(self, cache_props, domain_props):
        dprops = self.get_domain_properties()

        column = self.layout.column()
        column.label(text="Fluid Particles")
        column.separator()

        self.draw_fluid_particle_viewport_render_display()

        self.layout.separator()
        box = self.layout.box()
        box.label(text="Material Library")
        box.prop(dprops.materials, "fluid_particles_material", text="Fluid Particles")
        box.separator()

        self.layout.separator()
        column = self.layout.column()
        column.operator("flip_fluid_operators.helper_delete_particle_objects", icon="X")


    def draw_foam(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Whitewater Foam")
        column.separator()
        
        self.draw_whitewater_viewport_render_display()
        self.draw_whitewater_viewport_render_settings('render_foam_pct', 'viewport_foam_pct')
        self.draw_whitewater_particle_object_settings("Foam", 'whitewater_foam_material')

        self.layout.separator()
        column = self.layout.column()
        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete Whitewater Foam Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_FOAM'

        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete All Whitewater Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_ALL'


    def draw_bubble(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Whitewater Bubble")
        column.separator()
        
        self.draw_whitewater_viewport_render_display()
        self.draw_whitewater_viewport_render_settings('render_bubble_pct', 'viewport_bubble_pct')
        self.draw_whitewater_particle_object_settings("Bubble", 'whitewater_bubble_material')

        self.layout.separator()
        column = self.layout.column()
        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete Whitewater Bubble Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_BUBBLE'

        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete All Whitewater Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_ALL'


    def draw_spray(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Whitewater Spray")
        column.separator()

        self.draw_whitewater_viewport_render_display()
        self.draw_whitewater_viewport_render_settings('render_spray_pct', 'viewport_spray_pct')
        self.draw_whitewater_particle_object_settings("Spray", 'whitewater_spray_material')

        self.layout.separator()
        column = self.layout.column()
        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete Whitewater Spray Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_SPRAY'

        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete All Whitewater Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_ALL'


    def draw_dust(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label(text="Whitewater Dust")
        column.separator()

        self.draw_whitewater_viewport_render_display()
        self.draw_whitewater_viewport_render_settings('render_dust_pct', 'viewport_dust_pct')
        self.draw_whitewater_particle_object_settings("Dust", 'whitewater_dust_material')

        self.layout.separator()
        column = self.layout.column()
        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete Whitewater Dust Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_DUST'

        column.operator("flip_fluid_operators.helper_delete_whitewater_objects", 
                        text="Delete All Whitewater Mesh Objects",
                        icon="X").whitewater_type = 'TYPE_ALL'


    def draw(self, context):
        dprops = self.get_domain_properties()

        obj = vcu.get_active_object(context)
        cache_props = dprops.mesh_cache.get_mesh_cache_from_blender_object(obj)
        if cache_props is None:
            return

        if cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_SURFACE':
            self.draw_surface(cache_props, dprops)
        if cache_props.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            self.draw_fluid_particles(cache_props, dprops)
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
