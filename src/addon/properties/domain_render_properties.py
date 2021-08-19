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
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import types
from ..utils import version_compatibility_utils as vcu


def object_is_mesh_type_poll(self, obj):
    return obj.type == 'MESH'


class DomainRenderProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    render_display = EnumProperty(
            name="Render Display Mode",
            description="How to display the surface mesh for rendering",
            items=types.display_modes,
            default='DISPLAY_FINAL',
            ); exec(conv("render_display"))
    viewport_display = EnumProperty(
            name="Viewport Display Mode",
            description="How to display the surface mesh in the viewport",
            items=types.display_modes,
            default='DISPLAY_FINAL',
            ); exec(conv("viewport_display"))
    render_surface_motion_blur = BoolProperty(
            name="Render Motion Blur",
            description="Enable surface motion blur rendering. Motion blur"
                " vectors must be generated to render motion blur. See"
                " Surface panel to enable motion blur vector generation."
                " Motion blur must also be enabled in the Cycles render"
                " properties",
            default=True,
            ); exec(conv("render_surface_motion_blur"))
    surface_motion_blur_scale = FloatProperty(
            name="Scale",
            description="Scale of the surface motion blur vectors. Increasing this"
                " value will increase the amount of motion blur. Negative"
                " values will reverse the direction of blur",
            default=1.00,
            min=-10.0, max=10.0,
            step=0.1,
            precision=3,
            ); exec(conv("surface_motion_blur_scale"))
    whitewater_render_display = EnumProperty(
            name="Whitewater Render Display Mode",
            description="How to display the whitewater particles for rendering",
            items=types.display_modes,
            default='DISPLAY_FINAL',
            ); exec(conv("whitewater_render_display"))
    whitewater_viewport_display = EnumProperty(
            name="Whitewater Viewport Display Mode",
            description="How to display the whitewater particles in the viewport",
            items=types.display_modes,
            default='DISPLAY_FINAL',
            ); exec(conv("whitewater_viewport_display"))
    render_whitewater_motion_blur = BoolProperty(
            name="Render Motion Blur",
            description="Enable whitewater motion blur rendering. Motion blur"
                " vectors must be generated to render motion blur. See"
                " Whitewater panel to enable motion blur vector generation."
                " Motion blur must also be enabled in the Cycles render"
                " properties",
            default=True,
            ); exec(conv("render_whitewater_motion_blur"))
    whitewater_motion_blur_scale = FloatProperty(
            name="Scale",
            description="Scale of the whitewater motion blur vectors. Increasing this"
                " value will increase the amount of motion blur. Negative"
                " values will reverse the direction of blur",
            default=1.00,
            min=-10.0, max=10.0,
            step=0.1,
            precision=3,
            ); exec(conv("whitewater_motion_blur_scale"))
    render_whitewater_pct = IntProperty(
            name="Whitewater", 
            description="Percentage of total whitewater particles to display", 
            min=0, max=100,
            default=100,
            subtype='PERCENTAGE',
            ); exec(conv("render_whitewater_pct"))
    render_foam_pct = IntProperty(
            name="Foam", 
            description="Percentage of total foam particles to display", 
            min=0, max=100,
            default=100,
            subtype='PERCENTAGE',
            ); exec(conv("render_foam_pct"))
    render_bubble_pct = IntProperty(
            name="Bubble", 
            description="Percentage of total bubble particles to display", 
            min=0, max=100,
            default=100,
            subtype='PERCENTAGE',
            ); exec(conv("render_bubble_pct"))
    render_spray_pct = IntProperty(
            name="Spray", 
            description="Percentage of total spray particles to display", 
            min=0, max=100,
            default=100,
            subtype='PERCENTAGE',
            ); exec(conv("render_spray_pct"))
    render_dust_pct = IntProperty(
            name="Dust", 
            description="Percentage of total dust particles to display", 
            min=0, max=100,
            default=100,
            subtype='PERCENTAGE',
            ); exec(conv("render_dust_pct"))
    viewport_whitewater_pct = IntProperty(
            name="Whitewater", 
            description="Percentage of total whitewater particles to display", 
            min=0, max=100,
            default=5,
            subtype='PERCENTAGE',
            ); exec(conv("viewport_whitewater_pct"))
    viewport_foam_pct = IntProperty(
            name="Foam", 
            description="Percentage of total foam particles to display", 
            min=0, max=100,
            default=5,
            subtype='PERCENTAGE',
            ); exec(conv("viewport_foam_pct"))
    viewport_bubble_pct = IntProperty(
            name="Bubble", 
            description="Percentage of total bubble particles to display", 
            min=0, max=100,
            default=5,
            subtype='PERCENTAGE',
            ); exec(conv("viewport_bubble_pct"))
    viewport_spray_pct = IntProperty(
            name="Spray", 
            description="Percentage of total spray particles to display", 
            min=0, max=100,
            default=5,
            subtype='PERCENTAGE',
            ); exec(conv("viewport_spray_pct"))
    viewport_dust_pct = IntProperty(
            name="Dust", 
            description="Percentage of total dust particles to display", 
            min=0, max=100,
            default=5,
            subtype='PERCENTAGE',
            ); exec(conv("viewport_dust_pct"))
    whitewater_view_settings_mode = EnumProperty(
            name="View Settings Mode",
            description="How display settings will be applied to whitewater particles",
            items=types.whitewater_view_settings_modes,
            default='VIEW_SETTINGS_WHITEWATER',
            ); exec(conv("whitewater_view_settings_mode"))
    whitewater_particle_object = PointerProperty(
            name="Whitewater",
            description="Show this mesh object in place of whitewater particles",
            type=bpy.types.Object,
            poll=object_is_mesh_type_poll,
            ); exec(conv("whitewater_particle_object"))
    foam_particle_object = PointerProperty(
            name="Foam",
            description="Show this mesh object in place of foam particles",
            type=bpy.types.Object,
            poll=object_is_mesh_type_poll,
            ); exec(conv("foam_particle_object"))
    bubble_particle_object = PointerProperty(
            name="Bubble",
            description="Show this mesh object in place of bubble particles",
            type=bpy.types.Object,
            poll=object_is_mesh_type_poll,
            ); exec(conv("bubble_particle_object"))
    spray_particle_object = PointerProperty(
            name="Spray",
            description="Show this mesh object in place of spray particles",
            type=bpy.types.Object,
            poll=object_is_mesh_type_poll,
            ); exec(conv("spray_particle_object"))
    dust_particle_object = PointerProperty(
            name="Dust",
            description="Show this mesh object in place of dust particles",
            type=bpy.types.Object,
            poll=object_is_mesh_type_poll,
            ); exec(conv("dust_particle_object"))
    whitewater_particle_object_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="Type of whitewater particle geometry to use for rendering",
            items=types.whitewater_particle_object_modes,
            default='WHITEWATER_PARTICLE_ICOSPHERE',
            options = {'HIDDEN'},
            ); exec(conv("whitewater_particle_object_mode"))
    foam_particle_object_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="Type of foam particle geometry to use for rendering",
            items=types.whitewater_particle_object_modes,
            default='WHITEWATER_PARTICLE_ICOSPHERE',
            options = {'HIDDEN'},
            ); exec(conv("foam_particle_object_mode"))
    bubble_particle_object_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="Type of bubble particle geometry to use for rendering",
            items=types.whitewater_particle_object_modes,
            default='WHITEWATER_PARTICLE_ICOSPHERE',
            options = {'HIDDEN'},
            ); exec(conv("bubble_particle_object_mode"))
    spray_particle_object_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="Type of spray particle geometry to use for rendering",
            items=types.whitewater_particle_object_modes,
            default='WHITEWATER_PARTICLE_ICOSPHERE',
            options = {'HIDDEN'},
            ); exec(conv("spray_particle_object_mode"))
    dust_particle_object_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="Type of dust particle geometry to use for rendering",
            items=types.whitewater_particle_object_modes,
            default='WHITEWATER_PARTICLE_ICOSPHERE',
            options = {'HIDDEN'},
            ); exec(conv("dust_particle_object_mode"))
    only_display_whitewater_in_render = BoolProperty(
            name="Render Only",
            description="Only display whitewater particle object during render and"
                " hide in viewport. Hiding particle geometry in viewport will improve"
                " viewport performance",
            default = True,
            ); exec(conv("only_display_whitewater_in_render"))
    only_display_foam_in_render = BoolProperty(
            name="Render Only",
            description="Only display foam particle object during render and"
                " hide in viewport. Hiding particle geometry in viewport will improve"
                " viewport performance",
            default=True,
            ); exec(conv("only_display_foam_in_render"))
    only_display_bubble_in_render = BoolProperty(
            name="Render Only",
            description="Only display bubble particle object during render and"
                " hide in viewport. Hiding particle geometry in viewport will improve"
                " viewport performance",
            default=True,
            ); exec(conv("only_display_bubble_in_render"))
    only_display_spray_in_render = BoolProperty(
            name="Render Only",
            description="Only display spray particle object during render and"
                " hide in viewport. Hiding particle geometry in viewport will improve"
                " viewport performance",
            default=True,
            ); exec(conv("only_display_spray_in_render"))
    only_display_dust_in_render = BoolProperty(
            name="Render Only",
            description="Only display dust particle object during render and"
                " hide in viewport. Hiding particle geometry in viewport will improve"
                " viewport performance",
            default=True,
            ); exec(conv("only_display_dust_in_render"))
    whitewater_particle_scale = FloatProperty(
            name="Scale",
            description="Scale of the whitewater particle object",
            min=0.0,
            default=0.008,
            step=0.01,
            precision=4,
            ); exec(conv("whitewater_particle_scale"))
    foam_particle_scale = FloatProperty(
            name="Scale",
            description="Scale of the foam particle object",
            min=0.0,
            default=0.008,
            step=0.01,
            precision=4,
            ); exec(conv("foam_particle_scale"))
    bubble_particle_scale = FloatProperty(
            name="Scale",
            description="Scale of the bubble particle object",
            min=0.0,
            default=0.008,
            step=0.01,
            precision=4,
            ); exec(conv("bubble_particle_scale"))
    spray_particle_scale = FloatProperty(
            name="Scale",
            description="Scale of the spray particle object",
            min=0.0,
            default=0.008,
            step=0.01,
            precision=4,
            ); exec(conv("spray_particle_scale"))
    dust_particle_scale = FloatProperty(
            name="Scale",
            description="Scale of the dust particle object",
            min=0.0,
            default=0.008,
            step=0.01,
            precision=4,
            ); exec(conv("dust_particle_scale"))
    whitewater_particle_object_settings_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="How particle object settings will be applied to whitewater particles",
            items=types.whitewater_object_settings_modes,
            default='WHITEWATER_OBJECT_SETTINGS_WHITEWATER',
            ); exec(conv("whitewater_particle_object_settings_mode"))
    simulation_playback_mode = EnumProperty(
            name="Simulation Playback Mode",
            description="How to playback the simulation animation",
            items=types.simulation_playback_mode,
            default='PLAYBACK_MODE_TIMELINE',
            ); exec(conv("simulation_playback_mode"))
    override_frame = FloatProperty(
            name="Override Frame",
            description="The custom frame number to override. If this value is not a whole number,"
                " the frame to be loaded will be rounded down. TIP: This value can be keyframed for"
                " complex control of simulation playback",
            default=1.000,
            ); exec(conv("override_frame"))
    hold_frame_number = IntProperty(
            name="Hold Frame", 
            description="Frame number to be held in place",
            min=0,
            default=0,
            options = {'HIDDEN'},
            ); exec(conv("hold_frame_number"))


    whitewater_display_settings_expanded = BoolProperty(default=False); exec(conv("whitewater_display_settings_expanded"))
    current_frame = IntProperty(default=-1); exec(conv("current_frame"))
    is_hold_frame_number_set = BoolProperty(default=False); exec(conv("is_hold_frame_number_set"))


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".render_display",                             "Surface Render",            group_id=0)
        add(path + ".viewport_display",                           "Surface Viewport",          group_id=0)
        add(path + ".whitewater_render_display",                  "Whitewater Render",         group_id=0)
        add(path + ".whitewater_viewport_display",                "Whitewater Viewport",       group_id=0)
        add(path + ".render_surface_motion_blur",                 "Render Motion Blur",        group_id=0)
        add(path + ".override_frame",                             "Override Frame",            group_id=0)

        add(path + ".whitewater_view_settings_mode",              "Whitewater View Mode",      group_id=1, is_key=True)
        key_path = path + ".whitewater_view_settings_mode"
        value1 = "VIEW_SETTINGS_WHITEWATER"
        value2 = "VIEW_SETTINGS_FOAM_BUBBLE_SPRAY"

        add(path + ".render_whitewater_pct",                      "Whitewater Render Pct",     group_id=1, key_path=key_path, key_value=value1)
        add(path + ".viewport_whitewater_pct",                    "Whitewater Viewport Pct",   group_id=1, key_path=key_path, key_value=value1)
        add(path + ".render_foam_pct",                            "Foam Render Pct",           group_id=1, key_path=key_path, key_value=value2)
        add(path + ".render_bubble_pct",                          "Bubble Render Pct",         group_id=1, key_path=key_path, key_value=value2)
        add(path + ".render_spray_pct",                           "Spray Render Pct",          group_id=1, key_path=key_path, key_value=value2)
        add(path + ".render_dust_pct",                            "Dust Render Pct",           group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_foam_pct",                          "Foam Viewport Pct",         group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_bubble_pct",                        "Bubble Viewport Pct",       group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_spray_pct",                         "Spray Viewport Pct",        group_id=1, key_path=key_path, key_value=value2)
        add(path + ".viewport_dust_pct",                          "Dust Viewport Pct",         group_id=1, key_path=key_path, key_value=value2)

        add(path + ".whitewater_particle_object_settings_mode",   "Whitewater Particle Mode",  group_id=2, is_key=True)
        key_path = path + ".whitewater_particle_object_settings_mode"
        value1 = "WHITEWATER_OBJECT_SETTINGS_WHITEWATER"
        value2 = "WHITEWATER_OBJECT_SETTINGS_FOAM_BUBBLE_SPRAY"

        add(path + ".whitewater_particle_object_mode",            "Whitewater Particle",       group_id=2, key_path=key_path, key_value=value1)
        add(path + ".only_display_whitewater_in_render",          "Whitewater Render Only",    group_id=2, key_path=key_path, key_value=value1)
        add(path + ".whitewater_particle_scale",                  "Whitewater Particle Scale", group_id=2, key_path=key_path, key_value=value1)
        add(path + ".foam_particle_object_mode",                  "Foam Particle",             group_id=2, key_path=key_path, key_value=value2)
        add(path + ".bubble_particle_object_mode",                "Bubble Particle",           group_id=2, key_path=key_path, key_value=value2)
        add(path + ".spray_particle_object_mode",                 "Spray Particle",            group_id=2, key_path=key_path, key_value=value2)
        add(path + ".dust_particle_object_mode",                  "Dust Particle",             group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_foam_in_render",                "Foam Render Only",          group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_bubble_in_render",              "Bubble Render Only",        group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_spray_in_render",               "Spray Render Only",         group_id=2, key_path=key_path, key_value=value2)
        add(path + ".only_display_dust_in_render",                "Dust Render Only",          group_id=2, key_path=key_path, key_value=value2)
        add(path + ".foam_particle_scale",                        "Foam Particle Scale",       group_id=2, key_path=key_path, key_value=value2)
        add(path + ".bubble_particle_scale",                      "Bubble Particle Scale",     group_id=2, key_path=key_path, key_value=value2)
        add(path + ".spray_particle_scale",                       "Spray Particle Scale",      group_id=2, key_path=key_path, key_value=value2)
        add(path + ".dust_particle_scale",                        "Dust Particle Scale",       group_id=2, key_path=key_path, key_value=value2)
        

    def scene_update_post(self, scene):
        self._scene_update_post_update_hold_frame_number(scene)


    def reset_bake(self):
        self.is_hold_frame_number_set = False


    def _update_hold_frame(self, context):
        if self.simulation_playback_mode == 'PLAYBACK_MODE_HOLD_FRAME':
            self.is_hold_frame_number_set = True


    def _scene_update_post_update_hold_frame_number(self, scene):
        if self.simulation_playback_mode == 'PLAYBACK_MODE_HOLD_FRAME' or self.is_hold_frame_number_set:
            return
        if self.hold_frame_number != scene.frame_current:
            self.hold_frame_number = scene.frame_current


def register():
    bpy.utils.register_class(DomainRenderProperties)


def unregister():
    bpy.utils.unregister_class(DomainRenderProperties)