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


class FlipFluidCacheObjectTypePanel(bpy.types.Panel):
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
        obj = context.scene.objects.active
        return dprops.mesh_cache.is_cache_object(obj)


    def get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def draw_surface_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = column.split(percentage=0.5)
        column_left = split.column()
        column_left.label("Surface Render Display:")
        column_left.prop(rprops, "render_display", text="")

        column_right = split.column()
        column_right.label("Surface Viewport Display:")
        column_right.prop(rprops, "viewport_display", text="")


    def draw_whitewater_viewport_render_display(self):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        column = box.column()
        split = column.split(percentage=0.5)
        column_left = split.column()
        column_left.label("Whitewater Render Display:")
        column_left.prop(rprops, "whitewater_render_display", text="")

        column_right = split.column()
        column_right.label("Whitewater Viewport Display:")
        column_right.prop(rprops, "whitewater_viewport_display", text="")


    def draw_whitewater_viewport_render_settings(self, render_pct_prop, viewport_pct_prop):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        box.label("Display Settings Mode:")
        row = box.row()
        row.prop(rprops, "whitewater_view_settings_mode", expand=True)

        column = box.column(align=True)
        split = column.split()
        column = split.column(align = True)
        column.label("Final Display Settings:")
        column.prop(rprops, render_pct_prop, slider = True)

        column = split.column(align = True)
        column.label("Preview Display Settings:")
        column.prop(rprops, viewport_pct_prop, slider = True)


    def draw_whitewater_particle_object_settings(self, 
                                                 label_str,
                                                 object_prop,
                                                 scale_prop,
                                                 use_icosphere_prop,
                                                 render_display_prop):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        box = self.layout.box()
        box.label("Particle Object Settings Mode:")
        row = box.row()
        row.prop(rprops, "whitewater_particle_object_settings_mode", expand=True)

        column = box.column()
        row = column.row()
        column = row.column()
        split = column.split(percentage = 0.25)
        column = split.column()
        column.label(label_str)
        column = split.column()
        split = column.split(percentage = 0.5)
        column = split.column(align = True)
        row = column.row(align = True)
        row.enabled = not rprops.whitewater_use_icosphere_object
        row.prop_search(rprops, object_prop, 
                        bpy.context.scene, "objects", text = "")
        row = column.row(align = True)
        row.prop(rprops, scale_prop)
        column = split.column(align = True)
        column.prop(rprops, use_icosphere_prop)
        column.prop(rprops, render_display_prop)


    def draw_whitewater_material_settings(self, domain_props, prop_str, material_prop):
        dprops = self.get_domain_properties()

        self.layout.separator()
        box = self.layout.box()
        box.label("Material Library")
        box.prop(dprops.materials, material_prop, text=prop_str)
        box.separator()


    def draw_surface(self, cache_props, domain_props):
        dprops = self.get_domain_properties()

        column = self.layout.column()
        column.label("Surface")
        column.separator()

        self.draw_surface_viewport_render_display()

        column = self.layout.column()
        column.separator()
        column.prop(dprops.materials, 'surface_material', text="Surface Material")


    def draw_foam(self, cache_props, domain_props):
        dprops = self.get_domain_properties()
        rprops = dprops.render

        column = self.layout.column()
        column.label("Foam")
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
                    "Whitewater:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_use_icosphere_object',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Foam:",
                    'foam_particle_object',
                    'foam_particle_scale',
                    'foam_use_icosphere_object',
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
        column.label("Bubble")
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
                    "Whitewater:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_use_icosphere_object',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Bubble:",
                    'bubble_particle_object',
                    'bubble_particle_scale',
                    'bubble_use_icosphere_object',
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
        column.label("Spray")
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
                    "Whitewater:",
                    'whitewater_particle_object',
                    'whitewater_particle_scale',
                    'whitewater_use_icosphere_object',
                    'only_display_whitewater_in_render'
                    )
        else:
            self.draw_whitewater_particle_object_settings(
                    "Spray:",
                    'spray_particle_object',
                    'spray_particle_scale',
                    'spray_use_icosphere_object',
                    'only_display_foam_in_render'
                    )

        self.draw_whitewater_material_settings(
                domain_props, 
                "Spray", 
                'whitewater_spray_material'
                )


    def draw(self, context):
        dprops = self.get_domain_properties()

        obj = context.scene.objects.active
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
    

def register():
    bpy.utils.register_class(FlipFluidCacheObjectTypePanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidCacheObjectTypePanel)
