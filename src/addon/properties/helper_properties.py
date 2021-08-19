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
        IntProperty,
        StringProperty,
        BoolProperty,
        PointerProperty
        )

from . import preset_properties
from ..utils import version_compatibility_utils as vcu


class FlipFluidHelperProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    enable_auto_frame_load = BoolProperty(
            name="Auto-Load Baked Frames",
            description="Automatically load frames as they finish baking",
            default=False,
            ); exec(conv("enable_auto_frame_load"))
    playback_frame_offset = IntProperty(
            name="Frame Offset",
            description="Frame offset for simulation playback",
            default=0,
            options={'HIDDEN'},
            ); exec(conv("playback_frame_offset"))

    unsaved_blend_file_tooltip = BoolProperty(
            name="Unsaved Blend File Tooltip", 
            description="This is currently an unsaved .blend file. We recommend saving your file before baking a"
                " simulation so you do not accidentally lose your simulation progress or settings", 
            default=True,
            ); exec(conv("unsaved_blend_file_tooltip"))

    bake_simulation_expanded = BoolProperty(default=True); exec(conv("bake_simulation_expanded"))
    add_remove_objects_expanded = BoolProperty(default=True); exec(conv("add_remove_objects_expanded"))
    outliner_organization_expanded = BoolProperty(default=False); exec(conv("outliner_organization_expanded"))
    quick_select_expanded = BoolProperty(default=False); exec(conv("quick_select_expanded"))
    command_line_tools_expanded = BoolProperty(default=False); exec(conv("command_line_tools_expanded"))
    beginner_tools_expanded = BoolProperty(default=False); exec(conv("beginner_tools_expanded"))

    quick_viewport_display_expanded = BoolProperty(default=True); exec(conv("quick_viewport_display_expanded"))
    simulation_playback_expanded = BoolProperty(default=False); exec(conv("simulation_playback_expanded"))
    render_tools_expanded = BoolProperty(default=False); exec(conv("render_tools_expanded"))


    @classmethod
    def register(cls):
        bpy.types.Scene.flip_fluid_helper = PointerProperty(
                name="Flip Fluid Helper Properties",
                description="",
                type=cls,
                )


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.flip_fluid_helper


    def get_addon_preferences(self):
        return vcu.get_addon_preferences()


    def frame_complete_callback(self):
        prefs = self.get_addon_preferences()
        if prefs.enable_helper and self.enable_auto_frame_load:
            bpy.ops.flip_fluid_operators.helper_load_last_frame()


def register():
    bpy.utils.register_class(FlipFluidHelperProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperProperties)