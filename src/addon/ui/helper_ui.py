# Blender FLIP Fluids Add-on
# Copyright (C) 2020 Ryan L. Guy
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

import bpy, platform

from . import domain_simulation_ui
from .. import render
from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_HelperPanelMain(bpy.types.Panel):
    bl_label = "Simulation Setup"
    bl_category = "FLIP Fluids"
    bl_space_type = 'VIEW_3D'
    if vcu.is_blender_28():
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'


    @classmethod
    def poll(cls, context):
        return True


    def draw(self, context):
        hprops = context.scene.flip_fluid_helper
        preferences = vcu.get_addon_preferences(context)

        #
        # Bake Simulation
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "bake_simulation_expanded",
            icon="TRIA_DOWN" if hprops.bake_simulation_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Bake Simulation:")

        if hprops.bake_simulation_expanded:
            if context.scene.flip_fluid.is_domain_object_set():
                domain_simulation_ui.draw_bake_operator_UI_element(context, box)

                is_saved = bool(bpy.data.filepath)
                if is_saved:
                    dprops = context.scene.flip_fluid.get_domain_properties()
                    column = box.column(align=True)
                    column.label(text="Cache Directory:")
                    subcolumn = column.column(align=True)
                    subcolumn.enabled = not dprops.bake.is_simulation_running
                    subcolumn.prop(dprops.cache, "cache_directory")
                    row = column.row(align=True)
                    row.operator("flip_fluid_operators.relative_cache_directory")
                    row.operator("flip_fluid_operators.absolute_cache_directory")
                    row.operator("flip_fluid_operators.match_filename_cache_directory")
                    column.separator()
                else:
                    row = box.row(align=True)
                    row.alignment = 'LEFT'
                    row.prop(hprops, "unsaved_blend_file_tooltip", icon="ERROR", emboss=False, text="")
                    row = row.row(align=True)
                    row.alignment = 'LEFT'
                    row.alert = True
                    row.label(text="Unsaved File")
                    row = row.row(align=True)
                    row.alignment = 'RIGHT'
                    row.alert = False
                    row.operator("flip_fluid_operators.helper_save_blend_file", icon='FILE_TICK', text="Save")

            else:
                box.label(text="Please create a domain object")
                box.operator("flip_fluid_operators.helper_create_domain")

        #
        # Add Objects
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "add_remove_objects_expanded",
            icon="TRIA_DOWN" if hprops.add_remove_objects_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Add Objects:")

        if hprops.add_remove_objects_expanded:
            column = box.column()
            column.operator("flip_fluid_operators.helper_create_domain")

            column = box.column(align=True)
            column.operator(
                    "flip_fluid_operators.helper_add_objects", 
                    text="Obstacle"
                    ).object_type="TYPE_OBSTACLE"
            row = column.row(align=True)
            row.operator(
                    "flip_fluid_operators.helper_add_objects", 
                    text="Fluid"
                    ).object_type="TYPE_FLUID"
            row.operator(
                    "flip_fluid_operators.helper_add_objects", 
                    text="Inflow"
                    ).object_type="TYPE_INFLOW"
            row.operator(
                    "flip_fluid_operators.helper_add_objects", 
                    text="Outflow"
                    ).object_type="TYPE_OUTFLOW"
            row.operator(
                    "flip_fluid_operators.helper_add_objects", 
                    text="Force"
                    ).object_type="TYPE_FORCE_FIELD"
            column = box.column(align=True)
            column.operator("flip_fluid_operators.helper_remove_objects", text="Remove")

            column = box.column()
            column.label(text="Object Display:")
            row = column.row(align=True)
            row.operator(
                    "flip_fluid_operators.helper_set_object_viewport_display", 
                    text="Solid",
                    icon="MESH_CUBE" if vcu.is_blender_28() else "NONE"
                    ).display_mode="DISPLAY_MODE_SOLID"
            row.operator(
                    "flip_fluid_operators.helper_set_object_viewport_display", 
                    text="Wireframe",
                    icon="CUBE" if vcu.is_blender_28() else "NONE"
                    ).display_mode="DISPLAY_MODE_WIREFRAME"

            row = column.row(align=True)
            row.operator(
                    "flip_fluid_operators.helper_set_object_render_display", 
                    text="Show Render",
                    icon="RESTRICT_RENDER_OFF" if vcu.is_blender_28() else "NONE"
                    ).hide_render=False
            row.operator(
                    "flip_fluid_operators.helper_set_object_render_display", 
                    text="Hide Render",
                    icon="RESTRICT_RENDER_ON" if vcu.is_blender_28() else "NONE"
                    ).hide_render=True

        #
        # Select Objects
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "quick_select_expanded",
            icon="TRIA_DOWN" if hprops.quick_select_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Select Objects:")

        if hprops.quick_select_expanded:
            column = box.column(align=True)
            column.operator("flip_fluid_operators.helper_select_domain", text="Domain")

            column = box.column(align=True)
            column.operator(
                    "flip_fluid_operators.helper_select_objects", 
                    text="Obstacles"
                    ).object_type="TYPE_OBSTACLE"
            row = column.row(align=True)
            row.operator(
                    "flip_fluid_operators.helper_select_objects", 
                    text="Fluid"
                    ).object_type="TYPE_FLUID"
            row.operator(
                    "flip_fluid_operators.helper_select_objects", 
                    text="Inflows"
                    ).object_type="TYPE_INFLOW"
            row.operator(
                    "flip_fluid_operators.helper_select_objects", 
                    text="Outflows"
                    ).object_type="TYPE_OUTFLOW"
            row.operator(
                    "flip_fluid_operators.helper_select_objects", 
                    text="Forces"
                    ).object_type="TYPE_FORCE_FIELD"
            
            column = box.column(align=True)
            column.operator("flip_fluid_operators.helper_select_surface", text="Surface")
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_select_foam", text="Foam")
            row.operator("flip_fluid_operators.helper_select_bubble", text="Bubble")
            row.operator("flip_fluid_operators.helper_select_spray", text="Spray")
            row.operator("flip_fluid_operators.helper_select_dust", text="Dust")

        #
        # Outliner Organization
        #

        if vcu.is_blender_28():
            box = self.layout.box()
            row = box.row(align=True)
            row.alignment = 'LEFT'
            row.prop(hprops, "outliner_organization_expanded",
                icon="TRIA_DOWN" if hprops.outliner_organization_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Organize Outliner:")
            if not hprops.outliner_organization_expanded:
                row.operator("flip_fluid_operators.helper_organize_outliner", text="Organize")

            if hprops.outliner_organization_expanded:
                column = box.column(align=True)
                column.operator("flip_fluid_operators.helper_organize_outliner", text="FLIP Objects to Collections")
                column.operator("flip_fluid_operators.helper_undo_organize_outliner", text="Unlink FLIP Object Collections")

                column = box.column(align=True)
                column.operator("flip_fluid_operators.helper_separate_flip_meshes")
                column.operator("flip_fluid_operators.helper_undo_separate_flip_meshes", text="Unlink FLIP Mesh Collections")

        #
        # Command Line Tools
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "command_line_tools_expanded",
            icon="TRIA_DOWN" if hprops.command_line_tools_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Command Line Tools:")

        if hprops.command_line_tools_expanded:
            column = box.column(align=True)
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_command_line_bake")
            row.operator("flip_fluid_operators.helper_command_line_bake_to_clipboard", text="", icon='COPYDOWN')
            column = box.column(align=True)
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_command_line_render")
            row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN')

            system = platform.system()
            if system == "Windows":
                row = column.row(align=True)
                row.operator("flip_fluid_operators.helper_cmd_render_to_scriptfile")
                row.operator("flip_fluid_operators.helper_run_scriptfile", text="", icon='PLAY')
                row.operator("flip_fluid_operators.helper_open_outputfolder", text="", icon='FILE_FOLDER')
                column.separator()

        #
        # Beginner Tools
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "beginner_tools_expanded",
            icon="TRIA_DOWN" if hprops.beginner_tools_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Beginner Tools and Tips:")

        if hprops.beginner_tools_expanded:
            column = box.column(align=True)
            column.prop(preferences, "beginner_friendly_mode")
            column.prop(preferences, "show_documentation_in_ui")
            column.separator()

            if preferences.show_documentation_in_ui:
                column.operator(
                    "wm.url_open", 
                    text="Helper Menu Documentation", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings"
                column.separator()

            column.operator(
                "wm.url_open", 
                text="Video Learning Series", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Video-Learning-Series"
            column.operator(
                "wm.url_open", 
                text="Documentation and Wiki", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki"
            column.operator(
                "wm.url_open", 
                text="Recommended Topics", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki#the-most-important-documentation-topics"
            column.operator(
                "wm.url_open", 
                text="Frequently Asked Questions", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions"
            column.operator(
                "wm.url_open", 
                text="Scene Troubleshooting", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting"


class FLIPFLUID_PT_HelperPanelDisplay(bpy.types.Panel):
    bl_label = "Display and Render"
    bl_category = "FLIP Fluids"
    bl_space_type = 'VIEW_3D'
    if vcu.is_blender_28():
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'


    @classmethod
    def poll(cls, context):
        return True


    def draw(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            self.layout.label(text="Please create a domain object")
            self.layout.operator("flip_fluid_operators.helper_create_domain")
            return
        rprops = dprops.render
        hprops = context.scene.flip_fluid_helper

        #
        # Quick Viewport Display
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "quick_viewport_display_expanded",
            icon="TRIA_DOWN" if hprops.quick_viewport_display_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Quick Viewport Display:")

        if hprops.quick_viewport_display_expanded:
            column = box.column(align=True)

            column.label(text="Surface Display:")
            row = column.row(align=True)
            row.prop(rprops, "viewport_display", expand=True)

            column.separator()
            column.label(text="Whitewater Display:")
            row = column.row(align=True)
            row.prop(rprops, "whitewater_viewport_display", expand=True)

            column.separator()
            column.label(text="Load Frame:")
            column.operator("flip_fluid_operators.reload_frame", text="Reload Frame")

            column.operator("flip_fluid_operators.helper_load_last_frame")
            column.prop(hprops, "enable_auto_frame_load")

            column.separator()
            column.separator()

        #
        # Simulation Playback
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "simulation_playback_expanded",
            icon="TRIA_DOWN" if hprops.simulation_playback_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Simulation Playback:")

        if hprops.simulation_playback_expanded:
            subbox = box.box()
            subbox.label(text="Playback Mode:")
            row = subbox.row(align=True)
            row.prop(rprops, "simulation_playback_mode", expand=True)

            column = subbox.column()
            if rprops.simulation_playback_mode == 'PLAYBACK_MODE_TIMELINE':
                column.label(text="Current Timeline Frame:        " + str(context.scene.frame_current))
            elif rprops.simulation_playback_mode == 'PLAYBACK_MODE_OVERRIDE_FRAME':
                split = vcu.ui_split(column, factor=0.5, align=True)
                left_column = split.column(align=True)
                left_column.prop(rprops, "override_frame", text="Frame")

                right_column = split.column(align=True)
                right_column.operator("flip_fluid_operators.helper_set_linear_override_keyframes")
            elif rprops.simulation_playback_mode == 'PLAYBACK_MODE_HOLD_FRAME':
                split = vcu.ui_split(column, factor=0.5, align=True)
                left_column = split.column(align=True)
                left_column.prop(rprops, "hold_frame_number", text="Frame")

                right_column = split.column(align=True)
                right_column.alert = True
                right_column.operator("flip_fluid_operators.free_unheld_cache_files", 
                                      text="Delete Other Cache Files")

            column = box.column(align=True)
            column.separator()
            column.prop(hprops, "playback_frame_offset")
            column.label(text="Current Simulation Frame:     " + str(render.get_current_simulation_frame()))

            column.separator()
            column.separator()
            column.operator("flip_fluid_operators.reload_frame", text="Reload Frame")

        #
        # Render Tools
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "render_tools_expanded",
            icon="TRIA_DOWN" if hprops.render_tools_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Render Tools:")

        if hprops.render_tools_expanded:
            column = box.column(align=True)
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_command_line_render", text="Launch Command Line Render")
            row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN')

            system = platform.system()
            if system == "Windows":
                row = column.row(align=True)
                row.operator("flip_fluid_operators.helper_cmd_render_to_scriptfile")
                row.operator("flip_fluid_operators.helper_run_scriptfile", text="", icon='PLAY')
                row.operator("flip_fluid_operators.helper_open_outputfolder", text="", icon='FILE_FOLDER')
                
                column.separator()
                column.separator()


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

    

def register():
    # These panels will be registered in properties.preferences_properties.py
    pass


def unregister():
    try:
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelMain)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelDisplay)
    except:
        pass
