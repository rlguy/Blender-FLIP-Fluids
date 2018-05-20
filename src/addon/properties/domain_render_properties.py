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
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import types


class DomainRenderProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.render_display = EnumProperty(
                name="Render Display Mode",
                description="How to display the surface mesh for rendering",
                items=types.display_modes,
                default='DISPLAY_FINAL',
                )
        cls.viewport_display = EnumProperty(
                name="Viewport Display Mode",
                description="How to display the surface mesh in the viewport",
                items=types.display_modes,
                default='DISPLAY_FINAL',
                )
        cls.whitewater_render_display = EnumProperty(
                name="Whitewater Render Display Mode",
                description="How to display the whitewater particles for rendering",
                items=types.display_modes,
                default='DISPLAY_FINAL',
                )
        cls.whitewater_viewport_display = EnumProperty(
                name="Whitewater Viewport Display Mode",
                description="How to display the whitewater particles in the viewport",
                items=types.display_modes,
                default='DISPLAY_FINAL',
                )
        cls.render_whitewater_pct = IntProperty(
                name="Whitewater", 
                description="Percentage of total whitewater particles to display", 
                min=0, max=100,
                default=100,
                subtype='PERCENTAGE',
                )
        cls.render_foam_pct = IntProperty(
                name="Foam", 
                description="Percentage of total foam particles to display", 
                min=0, max=100,
                default=100,
                subtype='PERCENTAGE',
                )
        cls.render_bubble_pct = IntProperty(
                name="Bubble", 
                description="Percentage of total bubble particles to display", 
                min=0, max=100,
                default=100,
                subtype='PERCENTAGE',
                )
        cls.render_spray_pct = IntProperty(
                name="Spray", 
                description="Percentage of total spray particles to display", 
                min=0, max=100,
                default=100,
                subtype='PERCENTAGE',
                )
        cls.viewport_whitewater_pct = IntProperty(
                name="Whitewater", 
                description="Percentage of total whitewater particles to display", 
                min=0, max=100,
                default=25,
                subtype='PERCENTAGE',
                )
        cls.viewport_foam_pct = IntProperty(
                name="Foam", 
                description="Percentage of total foam particles to display", 
                min=0, max=100,
                default=25,
                subtype='PERCENTAGE',
                )
        cls.viewport_bubble_pct = IntProperty(
                name="Bubble", 
                description="Percentage of total bubble particles to display", 
                min=0, max=100,
                default=25,
                subtype='PERCENTAGE',
                )
        cls.viewport_spray_pct = IntProperty(
                name="Spray", 
                description="Percentage of total spray particles to display", 
                min=0, max=100,
                default=25,
                subtype='PERCENTAGE',
                )
        cls.whitewater_view_settings_mode = EnumProperty(
                name="View Settings Mode",
                description="How display settings will be applied to whitewater particles",
                items=types.whitewater_view_settings_modes,
                default='VIEW_SETTINGS_WHITEWATER',
                )
        cls.whitewater_particle_object = StringProperty(
                name="Whitewater",
                description="Show this object in place of whitewater particles",
                )
        cls.foam_particle_object = StringProperty(
                name="Foam",
                description="Show this object in place of foam particles",
                )
        cls.bubble_particle_object = StringProperty(
                name="Bubble",
                description="Show this object in place of bubble particles",
                )
        cls.spray_particle_object = StringProperty(
                name="Spray",
                description="Show this object in place of spray particles",
                )
        cls.whitewater_use_icosphere_object = BoolProperty(
                name="Icosphere",
                description="Show an icosphere in place of whitewater particles",
                default=True,
                )
        cls.foam_use_icosphere_object = BoolProperty(
                name="Icosphere",
                description="Show an icosphere in place of foam particles",
                default=True,
                )
        cls.bubble_use_icosphere_object = BoolProperty(
                name="Icosphere",
                description="Show an icosphere in place of bubble particles",
                default=True,
                )
        cls.spray_use_icosphere_object = BoolProperty(
                name="Icosphere",
                description="Show an icosphere in place of spray particles",
                default=True,
                )
        cls.only_display_whitewater_in_render = BoolProperty(
                name="Render Only",
                description="Only display whitewater particle object during render."
                    " Exclude in viewport.",
                default = True,
                )
        cls.only_display_foam_in_render = BoolProperty(
                name="Render Only",
                description="Only display foam particle object during render."
                    " Exclude in viewport.",
                default=True,
                )
        cls.only_display_bubble_in_render = BoolProperty(
                name="Render Only",
                description="Only display bubble particle object during render."
                    " Exclude in viewport.",
                default=True,
                )
        cls.only_display_spray_in_render = BoolProperty(
                name="Render Only",
                description="Only display spray particle object during render."
                    " Exclude in viewport.",
                default=True,
                )
        cls.whitewater_particle_scale = FloatProperty(
                name="Scale",
                description="Scale of the whitewater particle object",
                min=0.0,
                default=0.04,
                step=0.1,
                precision=3,
                )
        cls.foam_particle_scale = FloatProperty(
                name="Scale",
                description="Scale of the foam particle object",
                min=0.0,
                default=0.04,
                step=0.1,
                precision=3,
                )
        cls.bubble_particle_scale = FloatProperty(
                name="Scale",
                description="Scale of the bubble particle object",
                min=0.0,
                default=0.04,
                step=0.1,
                precision=3,
                )
        cls.spray_particle_scale = FloatProperty(
                name="Scale",
                description="Scale of the spray particle object",
                min=0.0,
                default=0.04,
                step=0.1,
                precision=3,
                )
        cls.whitewater_particle_object_settings_mode = EnumProperty(
                name="Particle Object Settings Mode",
                description="How particle object settings will be applied to whitewater particles",
                items=types.whitewater_object_settings_modes,
                default='WHITEWATER_OBJECT_SETTINGS_WHITEWATER',
                )
        cls.hold_frame = BoolProperty(
                name="Hold Frame",
                description="Hold a frame in place, regardless of timeline position",
                default=False,
                update=lambda self, context: self._update_hold_frame(context),
                )
        cls.hold_frame_number = IntProperty(
                name="Frame", 
                description="Frame number to be held",
                min=0,
                default=0,
                ) 


        cls.current_frame = IntProperty(default=-1)
        cls.is_hold_frame_number_set = BoolProperty(default=False)


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".render_display",                             "Surface Render",            group_id=0)
        add(path + ".viewport_display",                           "Surface Viewport",          group_id=0)
        add(path + ".whitewater_render_display",                  "Whitewater Render",         group_id=0)
        add(path + ".whitewater_viewport_display",                "Whitewater Viewport",       group_id=0)

        add(path + ".whitewater_view_settings_mode",              "Whitewater View Mode",      group_id=1, is_key=True)
        key_path = path + ".whitewater_view_settings_mode"
        value1 = "VIEW_SETTINGS_WHITEWATER"
        value2 = "VIEW_SETTINGS_FOAM_BUBBLE_SPRAY"

        add(path + ".render_whitewater_pct",                      "Whitewater Render Pct",     group_id=1, key_path=key_path, key_value=value1)
        add(path + ".viewport_whitewater_pct",                    "Whitewater Viewport Pct",   group_id=1, key_path=key_path, key_value=value1)
        add(path + ".render_foam_pct",                            "Foam Render Pct",           group_id=1, key_path=key_path, key_value=value2)
        add(path + ".render_bubble_pct",                          "Bubble Render Pct",         group_id=1, key_path=key_path, key_value=value2)
        add(path + ".render_spray_pct",                           "Spray Render Pct",          group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_foam_pct",                          "Foam Viewport Pct",         group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_bubble_pct",                        "Bubble Viewport Pct",       group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_spray_pct",                         "Spray Viewport Pct",        group_id=1, key_path=key_path, key_value=value2)

        add(path + ".whitewater_particle_object_settings_mode",   "Whitewater Particle Mode",  group_id=2, is_key=True)
        key_path = path + ".whitewater_particle_object_settings_mode"
        value1 = "WHITEWATER_OBJECT_SETTINGS_WHITEWATER"
        value2 = "WHITEWATER_OBJECT_SETTINGS_FOAM_BUBBLE_SPRAY"

        add(path + ".whitewater_use_icosphere_object",            "Whitewater Use Icosphere",  group_id=2, key_path=key_path, key_value=value1)
        add(path + ".only_display_whitewater_in_render",          "Whitewater Render Only",    group_id=2, key_path=key_path, key_value=value1)
        add(path + ".whitewater_particle_scale",                  "Whitewater Particle Scale", group_id=2, key_path=key_path, key_value=value1)
        add(path + ".foam_use_icosphere_object",                  "Foam Use Icosphere",        group_id=2, key_path=key_path, key_value=value2)
        add(path + ".bubble_use_icosphere_object",                "Bubble Use Icosphere",      group_id=2, key_path=key_path, key_value=value2)
        add(path + ".spray_use_icosphere_object",                 "Spray Use Icosphere",       group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_foam_in_render",                "Foam Render Only",          group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_bubble_in_render",              "Bubble Render Only",        group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_spray_in_render",               "Spray Render Only",         group_id=2, key_path=key_path, key_value=value2)
        add(path + ".foam_particle_scale",                        "Foam Particle Scale",       group_id=2, key_path=key_path, key_value=value2)
        add(path + ".bubble_particle_scale",                      "Bubble Particle Scale",     group_id=2, key_path=key_path, key_value=value2)
        add(path + ".spray_particle_scale",                       "Spray Particle Scale",      group_id=2, key_path=key_path, key_value=value2)
        

    def scene_update_post(self, scene):
        self._scene_update_post_update_hold_frame_number(scene)


    def reset_bake(self):
        self.is_hold_frame_number_set = False


    def _update_hold_frame(self, context):
        if self.hold_frame:
            self.is_hold_frame_number_set = True


    def _scene_update_post_update_hold_frame_number(self, scene):
        if self.hold_frame or self.is_hold_frame_number_set:
            return
        if self.hold_frame_number != scene.frame_current:
            self.hold_frame_number = scene.frame_current


def register():
    bpy.utils.register_class(DomainRenderProperties)


def unregister():
    bpy.utils.unregister_class(DomainRenderProperties)