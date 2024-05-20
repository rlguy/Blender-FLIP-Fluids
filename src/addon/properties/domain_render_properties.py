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


    fluid_particle_render_display = EnumProperty(
            name="Fluid Particle Render Display Mode",
            description="How to display the fluid particles for rendering",
            items=types.display_modes,
            default='DISPLAY_FINAL',
            ); exec(conv("fluid_particle_render_display"))
    fluid_particle_viewport_display = EnumProperty(
            name="Whitewater Viewport Display Mode",
            description="How to display the fluid particles in the viewport",
            items=types.display_modes,
            default='DISPLAY_PREVIEW',
            ); exec(conv("fluid_particle_viewport_display"))
    render_fluid_particle_surface_pct = FloatProperty(
            name="Surface", 
            description="Amount of total surface fluid particles to display during render. Surface"
                " particles are near the fluid surface and border empty air, but are not near"
                " the domain boundary", 
            min=0.0, max=1.0,
            default=1.0,
            precision=5,
            ); exec(conv("render_fluid_particle_surface_pct"))
    render_fluid_particle_boundary_pct = FloatProperty(
            name="Boundary", 
            description="Amount of total boundary fluid particles to display during render. Boundary"
            " particles are located near the domain boundary", 
            min=0.0, max=1.0,
            default=1.0,
            precision=5,
            ); exec(conv("render_fluid_particle_boundary_pct"))
    render_fluid_particle_interior_pct = FloatProperty(
            name="Interior", 
            description="Amount of total interior fluid particles to display during render. Interior"
            " particles are within the fluid and are particles that have not been classified"
            " as either surface or boundary particles", 
            min=0.0, max=1.0,
            default=1.0,
            precision=5,
            ); exec(conv("render_fluid_particle_interior_pct"))
    viewport_fluid_particle_surface_pct = FloatProperty(
            name="Surface", 
            description="Amount of total surface fluid particles to display in the viewport. Surface"
                " particles are near the fluid surface or obstacles, but are not near"
                " the domain boundary", 
            min=0.0, max=1.0,
            default=0.5,
            precision=5,
            ); exec(conv("viewport_fluid_particle_surface_pct"))
    viewport_fluid_particle_boundary_pct = FloatProperty(
            name="Boundary", 
            description="Amount of total boundary fluid particles to display in the viewport. Boundary"
            " particles are located near the domain boundary", 
            min=0.0, max=1.0,
            default=0.25,
            precision=5,
            ); exec(conv("viewport_fluid_particle_boundary_pct"))
    viewport_fluid_particle_interior_pct = FloatProperty(
            name="Interior", 
            description="Amount of total interior fluid particles to display in the viewport. Interior"
            " particles are within the fluid and are particles that have not been classified"
            " as either surface or boundary particles ", 
            min=0.0, max=1.0,
            default=0.05,
            precision=5,
            ); exec(conv("viewport_fluid_particle_interior_pct"))


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
    whitewater_particle_object_settings_mode = EnumProperty(
            name="Particle Object Settings Mode",
            description="How particle object settings will be applied to whitewater particles",
            items=types.whitewater_object_settings_modes,
            default='WHITEWATER_OBJECT_SETTINGS_WHITEWATER',
            ); exec(conv("whitewater_particle_object_settings_mode"))

    # Particle scale settings are no longer used in FLIP Fluids 1.8.0+
    # Only used to update Blend files created in FLIP Fluids 1.7.5 and earlier
    # to newer addon versions.
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
    fluid_particle_display_settings_expanded = BoolProperty(default=False); exec(conv("fluid_particle_display_settings_expanded"))
    surface_display_settings_expanded = BoolProperty(default=True); exec(conv("surface_display_settings_expanded"))
    simulation_display_settings_expanded = BoolProperty(default=False); exec(conv("simulation_display_settings_expanded"))
    current_frame = IntProperty(default=-1); exec(conv("current_frame"))
    is_hold_frame_number_set = BoolProperty(default=False); exec(conv("is_hold_frame_number_set"))


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".render_display",                             "Surface Render",            group_id=0)
        add(path + ".viewport_display",                           "Surface Viewport",          group_id=0)
        add(path + ".fluid_particle_render_display",              "Particle Render",           group_id=0)
        add(path + ".fluid_particle_viewport_display",            "Particle Viewport",         group_id=0)
        add(path + ".whitewater_render_display",                  "Whitewater Render",         group_id=0)
        add(path + ".whitewater_viewport_display",                "Whitewater Viewport",       group_id=0)
        add(path + ".render_surface_motion_blur",                 "Render Motion Blur",        group_id=0)
        add(path + ".override_frame",                             "Override Frame",            group_id=0)

        add(path + ".whitewater_view_settings_mode",              "Whitewater View Mode",      group_id=1)
        add(path + ".whitewater_particle_object_settings_mode",   "Whitewater View Mode",      group_id=1)

        add(path + ".render_whitewater_pct",                      "Whitewater Render Pct",     group_id=1)
        add(path + ".viewport_whitewater_pct",                    "Whitewater Viewport Pct",   group_id=1)
        add(path + ".render_foam_pct",                            "Foam Render Pct",           group_id=1)
        add(path + ".render_bubble_pct",                          "Bubble Render Pct",         group_id=1)
        add(path + ".render_spray_pct",                           "Spray Render Pct",          group_id=1)
        add(path + ".render_dust_pct",                            "Dust Render Pct",           group_id=1)
        add(path + ".viewport_foam_pct",                          "Foam Viewport Pct",         group_id=1)
        add(path + ".viewport_bubble_pct",                        "Bubble Viewport Pct",       group_id=1)
        add(path + ".viewport_spray_pct",                         "Spray Viewport Pct",        group_id=1)
        add(path + ".viewport_dust_pct",                          "Dust Viewport Pct",         group_id=1)

        add(path + ".whitewater_particle_scale",                  "Whitewater Particle Scale", group_id=2)
        add(path + ".foam_particle_scale",                        "Foam Particle Scale",       group_id=2)
        add(path + ".bubble_particle_scale",                      "Bubble Particle Scale",     group_id=2)
        add(path + ".spray_particle_scale",                       "Spray Particle Scale",      group_id=2)
        add(path + ".dust_particle_scale",                        "Dust Particle Scale",       group_id=2)
        

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