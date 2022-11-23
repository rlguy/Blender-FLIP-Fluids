# Blender FLIP Fluids Add-on
# Copyright (C) 2022 Ryan L. Guy
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
from ..utils import api_workaround_utils as api_utils
from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils


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
        if not installation_utils.is_installation_complete():
            box = self.layout.box()
            box.label(text="IMPORTANT: Please Complete Installation", icon="ERROR")
            box.label(text="Click here to complete installation of the FLIP Fluids Addon:")
            box.operator("flip_fluid_operators.complete_installation", icon='MOD_FLUIDSIM')
            return

        hprops = context.scene.flip_fluid_helper
        preferences = vcu.get_addon_preferences(context)

        feature_dict = api_utils.get_enabled_features_affected_by_T88811()
        if feature_dict is not None and not preferences.dismiss_T88811_crash_warning:
            box = self.layout.box()
            api_utils.draw_T88811_ui_warning(box, preferences, feature_dict)

        is_persistent_data_enabled = api_utils.is_persistent_data_issue_relevant()
        if is_persistent_data_enabled and not preferences.dismiss_persistent_data_render_warning:
            box = self.layout.box()
            api_utils.draw_persistent_data_warning(box, preferences)

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
                    column.enabled = not dprops.bake.is_simulation_running
                    column.prop(dprops.simulation, "resolution")
                    column.separator()

                    column.label(text="Cache Directory:")
                    subcolumn = column.column(align=True)
                    row = subcolumn.row(align=True)
                    row.prop(dprops.cache, "cache_directory")
                    row.operator("flip_fluid_operators.increment_decrease_cache_directory", text="", icon="REMOVE").increment_mode = "DECREASE"
                    row.operator("flip_fluid_operators.increment_decrease_cache_directory", text="", icon="ADD").increment_mode = "INCREASE"
                    row = column.row(align=True)
                    row.operator("flip_fluid_operators.relative_cache_directory")
                    row.operator("flip_fluid_operators.absolute_cache_directory")
                    row.operator("flip_fluid_operators.match_filename_cache_directory")
                    column.separator()

                    column = box.column(align=True)
                    column.label(text="Render Output:")
                    column.prop(context.scene.render, "filepath", text="")
                    row = column.row(align=True)
                    row.operator("flip_fluid_operators.relative_to_blend_render_output")
                    row.operator("flip_fluid_operators.prefix_to_filename_render_output")
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
            column.operator("flip_fluid_operators.helper_delete_domain", text="Delete Domain", icon='X')

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
        row.alignment = 'LEFT'
        row.prop(hprops, "quick_select_expanded",
            icon="TRIA_DOWN" if hprops.quick_select_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Select Objects:")
        if not hprops.quick_select_expanded:
            row.operator("flip_fluid_operators.helper_select_domain", text="Domain")

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
            row = box.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="Save before running CMD operators:")
            row.operator("flip_fluid_operators.helper_save_blend_file", icon='FILE_TICK', text="Save").save_as_blend_file = False

            subbox = box.box()
            subbox.label(text="Bake:")
            column = subbox.column(align=True)
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_command_line_bake")
            row.operator("flip_fluid_operators.helper_command_line_bake_to_clipboard", text="", icon='COPYDOWN')
            row = column.row(align=True)
            row.prop(hprops, "cmd_launch_render_after_bake")

            system = platform.system()
            if system == "Windows":
                row = row.row(align=True)
                row.enabled = hprops.cmd_launch_render_after_bake
                row.prop(hprops, "cmd_launch_render_mode", text="")

            subbox = box.box()
            subbox.label(text="Render Animation:")
            column = subbox.column(align=True)
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

            subbox = box.box()
            subbox.label(text="Render Frame:")
            column = subbox.column(align=True)
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_command_line_render_frame")
            row.operator("flip_fluid_operators.helper_cmd_render_frame_to_clipboard", text="", icon='COPYDOWN')
            row = column.row(align=True)
            row.prop(hprops, "cmd_open_image_after_render")

            if system == "Windows":
                row = column.row(align=True)
                row.prop(hprops, "cmd_close_window_after_render")

        #
        # Geometry Node Tools
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "geometry_node_tools_expanded",
            icon="TRIA_DOWN" if hprops.geometry_node_tools_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Geometry Node Tools:")

        if hprops.geometry_node_tools_expanded:
            column = box.column(align=True)

            if not vcu.is_blender_31():
                column.label(text="Blender 3.1 or later required")

            prefs = vcu.get_addon_preferences()
            is_developer_mode = prefs.is_developer_tools_enabled()
            if not is_developer_mode:
                warn_box = box.box()
                warn_column = warn_box.column(align=True)
                warn_column.enabled = True
                warn_column.label(text="     Experimental Developer Tools must be")
                warn_column.label(text="     enabled in preferences to use this feature")
                warn_column.separator()
                warn_column.prop(prefs, "enable_developer_tools", text="Enable Developer Tools in Preferences")
                warn_column.separator()
                warn_column.operator(
                    "wm.url_open", 
                    text="Important Info and Limitations", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preferences-Menu-Settings#developer-tools"

            column = box.column(align=True)
            column.enabled = vcu.is_blender_31() and is_developer_mode
            column.operator("flip_fluid_operators.helper_initialize_motion_blur")
            

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
    bl_label = "Display and Playback"
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
        if not installation_utils.is_installation_complete():
            return

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
            scene_props = context.scene.flip_fluid

            column = box.column(align=True)
            row = column.row(align=True)
            row.label(text="Simulation Visibility:")
            if not scene_props.show_viewport:
                row = row.row(align=True)
                row.alert = True
                row.label(text="Disabled in Viewport", icon="CANCEL")

            column.prop(scene_props, "show_viewport", text="Show In Viewport", icon="RESTRICT_VIEW_OFF")

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
            row = column.row(align=True)
            row.prop(hprops, "enable_auto_frame_load")
            row = row.row(align=True)
            row.enabled = hprops.enable_auto_frame_load
            row.prop(hprops, "enable_auto_frame_load_cmd")

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


class FLIPFLUID_PT_HelperTechnicalSupport(bpy.types.Panel):
    bl_label = "Technical Support Tools"
    bl_category = "FLIP Fluids"
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if vcu.is_blender_28():
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'


    @classmethod
    def poll(cls, context):
        prefs = vcu.get_addon_preferences()
        return prefs.enable_support_tools


    def draw(self, context):
        column = self.layout.column()
        column.operator("flip_fluid_operators.print_system_info")
        column.operator("flip_fluid_operators.standardize_blend_file")
        column.operator("flip_fluid_operators.display_overlay_stats")
        column.separator()
        column.operator("flip_fluid_operators.select_simulation_objects")
        column.operator("flip_fluid_operators.invert_selection")
        column.separator()
        column.operator("flip_fluid_operators.print_hidden_simulation_objects")
        column.operator("flip_fluid_operators.select_hidden_simulation_objects")
        column.separator()
        column.operator("flip_fluid_operators.print_inverse_obstacles")
        column.operator("flip_fluid_operators.select_inverse_obstacles")
        column.separator()
        column.operator("flip_fluid_operators.increment_and_save_file", icon='FILE_TICK')


def register():
    # These panels will be registered in properties.preferences_properties.py
    pass


def unregister():
    try:
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelMain)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelDisplay)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperTechnicalSupport)
    except:
        pass
