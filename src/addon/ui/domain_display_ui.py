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


class FlipFluidDomainTypeDisplayPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Display Settings"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def draw_surface_display_settings(self, context):
        domain_object = context.scene.objects.active
        rprops = domain_object.flip_fluid.domain.render

        column = self.layout.column()
        column.label("Surface Display Settings:")

        box = self.layout.box()
        column = box.column()

        split = column.split(percentage=0.5)
        column_left = split.column()
        column_left.label("Surface Render Display:")
        column_left.prop(rprops, "render_display", text="")

        column_right = split.column()
        column_right.label("Surface Viewport Display:")
        column_right.prop(rprops, "viewport_display", text="")


    def draw_whitewater_display_settings(self, context):
        obj = context.scene.objects.active
        dprops = obj.flip_fluid.domain
        rprops = dprops.render
        is_whitewater_enabled = dprops.whitewater.enable_whitewater_simulation

        self.layout.separator()
        column = self.layout.column()
        split = column.split()
        left_column = split.column()
        left_column.label("Whitewater Display Settings:")

        right_column = split.column()
        if not is_whitewater_enabled:
            row = right_column.row()
            row.alignment = 'LEFT'
            c = row.column()
            c.enabled = False
            c.label("Enable in 'Whitewater' panel")
            row.operator("flip_fluid_operators.display_enable_whitewater_tooltip", 
                         text="", icon="QUESTION", emboss=False)

        master_box = self.layout.column()
        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label("Whitewater Render Display:")
        column.prop(rprops, "whitewater_render_display", text="")

        column = split.column(align=True)
        column.label("Whitewater Viewport Display:")
        column.prop(rprops, "whitewater_viewport_display", text="")
        master_box.separator()

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        column.label("Display Settings Mode:")
        row = column.row()
        row.prop(rprops, "whitewater_view_settings_mode", expand=True)

        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label("Final Display Settings:")
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            column.prop(rprops, "render_whitewater_pct", slider=True)
        else:
            column.prop(rprops, "render_foam_pct", slider=True)
            column.prop(rprops, "render_bubble_pct", slider=True)
            column.prop(rprops, "render_spray_pct", slider=True)

        column = split.column(align=True)
        column.label("Preview Display Settings:")
        if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
            column.prop(rprops, "viewport_whitewater_pct", slider=True)
        else:
            column.prop(rprops, "viewport_foam_pct", slider=True)
            column.prop(rprops, "viewport_bubble_pct", slider=True)
            column.prop(rprops, "viewport_spray_pct", slider=True)
        master_box.separator()

        box = master_box.box()
        box.enabled = is_whitewater_enabled

        column = box.column(align=True)
        column.label("Particle Object Settings Mode:")
        row = column.row()
        row.prop(rprops, "whitewater_particle_object_settings_mode", expand=True)
        column = box.column()

        box_column = box.column()
        if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
            row = box_column.row()
            column = row.column()
            split = column.split(percentage=0.25)
            column = split.column()
            column.label("Whitewater:")
            column = split.column()
            split = column.split(percentage=0.5)
            column = split.column(align=True)
            row = column.row(align=True)
            row.enabled = not rprops.whitewater_use_icosphere_object
            row.prop_search(rprops, "whitewater_particle_object", 
                               context.scene, "objects", text="")
            row = column.row(align=True)
            row.prop(rprops, "whitewater_particle_scale")
            column = split.column(align=True)
            column.prop(rprops, "whitewater_use_icosphere_object")
            column.prop(rprops, "only_display_whitewater_in_render")
        else:
            row = box_column.row()
            column = row.column()
            split = column.split(percentage=0.25)
            column = split.column()
            column.label("Foam:")
            column = split.column()
            split = column.split(percentage=0.5)
            column = split.column(align=True)
            row = column.row(align=True)
            row.enabled = not rprops.foam_use_icosphere_object
            row.prop_search(rprops, "foam_particle_object", 
                               context.scene, "objects", text="")
            row = column.row(align=True)
            row.prop(rprops, "foam_particle_scale")
            column = split.column()
            column.prop(rprops, "foam_use_icosphere_object")
            column.prop(rprops, "only_display_foam_in_render")
            row = box_column.row()

            row = box_column.row()
            column = row.column()
            split = column.split(percentage=0.25)
            column = split.column()
            column.label("Bubble:")
            column = split.column()
            split = column.split(percentage=0.5)
            column = split.column(align=True)
            row = column.row(align=True)
            row.enabled = not rprops.bubble_use_icosphere_object
            row.prop_search(rprops, "bubble_particle_object", 
                               context.scene, "objects", text="")
            row = column.row(align=True)
            row.prop(rprops, "bubble_particle_scale")
            column = split.column(align=True)
            column.prop(rprops, "bubble_use_icosphere_object")
            column.prop(rprops, "only_display_bubble_in_render")
            row = box_column.row()

            row = box_column.row()
            column = row.column()
            split = column.split(percentage=0.25)
            column = split.column()
            column.label("Spray:")
            column = split.column()
            split = column.split(percentage=0.5)
            column = split.column(align=True)
            row = column.row(align=True)
            row.enabled = not rprops.spray_use_icosphere_object
            row.prop_search(rprops, "spray_particle_object", 
                               context.scene, "objects", text="")
            row = column.row(align=True)
            row.prop(rprops, "spray_particle_scale")
            column = split.column(align=True)
            column.prop(rprops, "spray_use_icosphere_object")
            column.prop(rprops, "only_display_spray_in_render")


    def draw(self, context):
        domain_object = context.scene.objects.active
        rprops = domain_object.flip_fluid.domain.render

        self.draw_surface_display_settings(context)
        self.draw_whitewater_display_settings(context)
    

def register():
    bpy.utils.register_class(FlipFluidDomainTypeDisplayPanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeDisplayPanel)
