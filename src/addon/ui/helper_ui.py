# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
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
        
    # Find Domain-Object for compositing/passes
    def get_domain_object():
        """Find the first object in the scene with flip_fluid.object_type = 'TYPE_DOMAIN'."""
        for obj in bpy.data.objects:
            if hasattr(obj, "flip_fluid") and obj.flip_fluid.object_type == 'TYPE_DOMAIN':
                return obj
        return None  # No domain object found

    def draw_simulation_setup_panel(self, context):
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
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
                is_saved = bool(bpy.data.filepath)
                if not is_saved:
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
                    
                domain_simulation_ui.draw_bake_operator_UI_element(context, box)

                dprops = context.scene.flip_fluid.get_domain_properties()
                column = box.column(align=True)
                column.enabled = not dprops.bake.is_simulation_running

                resolution_text = "Resolution"
                if dprops.simulation.lock_cell_size:
                    resolution_text += " (voxel size locked)"

                row = column.row(align=True)
                row.enabled = not dprops.simulation.lock_cell_size
                row.prop(dprops.simulation, "resolution", text=resolution_text)
                column.separator()

                split = column.split(align=True)
                column_left = split.column(align=True)
                column_left.label(text="Multithreading:")
                row = column_left.row(align=True)
                row.prop(dprops.advanced, "threading_mode", expand=True)
                row = column_left.row(align=True)
                if dprops.advanced.threading_mode == 'THREADING_MODE_AUTO_DETECT':
                    row.enabled = False
                    row.prop(dprops.advanced, "num_threads_auto_detect")
                elif dprops.advanced.threading_mode == 'THREADING_MODE_FIXED':
                    row.prop(dprops.advanced, "num_threads_fixed")
                column.separator()

                column.label(text="Cache Directory:")
                subcolumn = column.column(align=True)
                row = subcolumn.row(align=True)
                row.prop(dprops.cache, "cache_directory")
                row.operator("flip_fluid_operators.increase_decrease_cache_directory", text="", icon="REMOVE").increment_mode = "DECREASE"
                row.operator("flip_fluid_operators.increase_decrease_cache_directory", text="", icon="ADD").increment_mode = "INCREASE"
                row = column.row(align=True)
                row.operator("flip_fluid_operators.relative_cache_directory")
                row.operator("flip_fluid_operators.absolute_cache_directory")
                row.operator("flip_fluid_operators.match_filename_cache_directory")
                column.separator()

                column = box.column(align=True)
                column.label(text="Render Output:")
                row = column.row(align=True)
                row.prop(context.scene.render, "filepath", text="")
                row.operator("flip_fluid_operators.increase_decrease_render_directory", text="", icon="REMOVE").increment_mode = "DECREASE"
                row.operator("flip_fluid_operators.increase_decrease_render_directory", text="", icon="ADD").increment_mode = "INCREASE"
                row = column.row(align=True)
                row.operator("flip_fluid_operators.relative_to_blend_render_output")
                row.operator("flip_fluid_operators.prefix_to_filename_render_output")

                column = box.column(align=True)
                column.label(text="Cache and Render Output:")
                row = column.row(align=True)
                row.operator("flip_fluid_operators.increase_decrease_cache_render_version", text="Decrease Version", icon="REMOVE").increment_mode = "DECREASE"
                row.operator("flip_fluid_operators.increase_decrease_cache_render_version", text="Increase Version", icon="ADD").increment_mode = "INCREASE"

            else:
                box.label(text="Please create a domain object")
                box.operator("flip_fluid_operators.helper_create_domain")

        #
        # New Prepare Geometry Tools: 
        #
        
        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "prepare_geometry_tools_expanded",
            icon="TRIA_DOWN" if hprops.prepare_geometry_tools_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Prepare Geometry Tools:")

        if hprops.prepare_geometry_tools_expanded:
            column = box.column(align=True)

            if not vcu.is_blender_31():
                column.label(text="Blender 3.1 or later required")

            prefs = vcu.get_addon_preferences()
            is_developer_mode = prefs.is_extra_features_enabled()
            if is_developer_mode:
                active_collection = context.view_layer.active_layer_collection.collection
                is_active_collection_selected = False
                active_collection_name = "No Collection Selected"
                if active_collection is not None:
                    is_active_collection_selected = True
                    active_collection_name = active_collection.name

                options_box = column.box()
                options_box.label(text="Remesh Options:", icon='TOOL_SETTINGS')
                options_column = options_box.column(align=True)
                options_column.prop(hprops, "flip_fluids_remesh_convert_objects_to_mesh")
                options_column.prop(hprops, "flip_fluids_remesh_apply_object_modifiers")
                options_column.prop(hprops, "flip_fluids_remesh_skip_hide_render_objects")
                options_column.label(text="Active collection will be remeshed:")
                options_column.label(text=active_collection_name, icon="OUTLINER_COLLECTION")

                column = box.column(align=True)
                column.enabled = vcu.is_blender_31() and is_developer_mode
                column.alert = column.enabled and not is_active_collection_selected

                row = column.row(align=True)
                op = row.operator("flip_fluid_operators.helper_remesh", icon="MOD_REMESH")
                op.skip_hide_render_objects = hprops.flip_fluids_remesh_skip_hide_render_objects
                op.apply_object_modifiers = hprops.flip_fluids_remesh_apply_object_modifiers
                op.convert_objects_to_mesh = hprops.flip_fluids_remesh_convert_objects_to_mesh

                row.operator(
                        "wm.url_open", 
                        text="", 
                        icon="URL"
                    ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#prepare-geometry-tools"
            else:
                warn_box = box.box()
                warn_column = warn_box.column(align=True)
                warn_column.enabled = True
                warn_column.label(text="     This feature is affected by a current bug in Blender.", icon='ERROR')
                warn_column.label(text="     The Extra Features option must be enabled in preferences")
                warn_column.label(text="     to use this feature.")
                warn_column.separator()
                warn_column.prop(prefs, "enable_extra_features", text="Enable Extra Features in Preferences")
                warn_column.separator()
                warn_column.operator(
                    "wm.url_open", 
                    text="Important Info and Limitations", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preferences-Menu-Settings#developer-tools"
      
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
        row.label(text="Add / Remove Objects:")

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
            row.operator("flip_fluid_operators.helper_select_domain", text="Domain", icon="MESH_GRID")

        if hprops.quick_select_expanded:
            column = box.column(align=True)
            column.operator("flip_fluid_operators.helper_select_domain", text="Domain", icon="MESH_GRID")

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
            row = column.row(align=True)
            row.operator("flip_fluid_operators.helper_select_surface", text="Fluid Surface")
            row.operator("flip_fluid_operators.helper_select_fluid_particles", text="Fluid Particles")
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
                row.operator("flip_fluid_operators.helper_organize_outliner", text="Organize", icon="GROUP")

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
        
            if hprops.render_passes:
                subbox = box.box()
                hint_row = subbox.row()
                hint_row.alignment = 'CENTER'
                hint_row.label(text="Passes Rendering is ENABLED", icon='RENDERLAYERS')

            ### Command Line Bake ###

            subbox = box.box()
            row = subbox.row(align=True)
            row.prop(hprops, "command_line_bake_expanded",
                icon="TRIA_DOWN" if hprops.command_line_bake_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Bake:")

            if hprops.command_line_bake_expanded:
                column = subbox.column(align=True)
                row = column.row(align=True)
                row.operator("flip_fluid_operators.helper_command_line_bake")
                row.operator("flip_fluid_operators.helper_command_line_bake_to_clipboard", text="", icon='COPYDOWN')
                row.operator("flip_fluid_operators.helper_open_cache_output_folder", text="", icon='FILE_FOLDER')
                column.separator()
                
                column = subbox.column()
                row = column.row(align=True)
                row.prop(hprops, "cmd_bake_and_render")
                row = column.row(align=True)
                row.enabled = hprops.cmd_bake_and_render
                row.prop(hprops, "cmd_bake_and_render_mode", expand=True)

                column = subbox.column(align=True)
                column.enabled = hprops.cmd_bake_and_render
                row = column.row(align=True)
                row.enabled = hprops.cmd_bake_and_render
                row.alignment = 'EXPAND'
                if hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_SEQUENCE':
                    row.label(text="Render After Bake Mode:")
                    if hprops.render_passes:
                        row.prop(hprops, "cmd_launch_render_passes_animation_mode", text="")
                    else:
                        row.prop(hprops, "cmd_launch_render_animation_mode", text="")

                    if hprops.render_passes:
                        row = column.row(align=True)
                        row.label(text="")
                        row.prop(hprops, "cmd_launch_render_passes_animation_instances")
                        row = column.row(align=True)
                        row.label(text="")
                        row.prop(hprops, "cmd_launch_render_passes_animation_no_overwrite")
                    elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_BATCH':
                        row = column.row(align=True)
                        row.enabled = hprops.cmd_bake_and_render
                        row.label(text="")
                        row.prop(hprops, "cmd_launch_render_animation_no_overwrite")
                        column.label(text="")
                    elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_MULTI_INSTANCE':
                        row = column.row(align=True)
                        row.label(text="")
                        row.prop(hprops, "cmd_launch_render_animation_instances")
                        row = column.row(align=True)
                        row.label(text="")
                        row.prop(hprops, "cmd_launch_render_animation_no_overwrite")
                    else:
                        row = column.row(align=True)
                        row.label(text="")
                        row.prop(hprops, "cmd_launch_render_normal_animation_no_overwrite")
                        column.label(text="")
                elif hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED':
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_bake_and_render_interleaved_instances")
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_bake_and_render_interleaved_no_overwrite", text="Skip rendered frames")
                    column.label(text="")

            else:
                row = row.row(align=True)
                row.operator("flip_fluid_operators.helper_command_line_bake")
                row.operator("flip_fluid_operators.helper_command_line_bake_to_clipboard", text="", icon='COPYDOWN')
                row.operator("flip_fluid_operators.helper_open_cache_output_folder", text="", icon='FILE_FOLDER')

            ### Command Line Render Animation ###

            subbox = box.box()
            row = subbox.row(align=True)
            row.prop(hprops, "command_line_render_expanded",
                icon="TRIA_DOWN" if hprops.command_line_render_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Render Animation:")
            
            if hprops.command_line_render_expanded:
                column = subbox.column()
                row = column.row(align=True)
                row.operator("flip_fluid_operators.helper_command_line_render").use_turbo_tools = False
                row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = False
                row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')

                column = subbox.column(align=True)
                row = column.row(align=True)
                row.label(text="Render Mode:")
                if hprops.render_passes:
                    row.prop(hprops, "cmd_launch_render_passes_animation_mode", text="")
                else:
                    row.prop(hprops, "cmd_launch_render_animation_mode", text="")

                if hprops.render_passes:
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_launch_render_passes_animation_instances")
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_launch_render_passes_animation_no_overwrite")
                elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_BATCH':
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_launch_render_animation_no_overwrite")
                    column.label(text="")
                elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_MULTI_INSTANCE':
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_launch_render_animation_instances")
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_launch_render_animation_no_overwrite")
                else:
                    row = column.row(align=True)
                    row.label(text="")
                    row.prop(hprops, "cmd_launch_render_normal_animation_no_overwrite")
                    column.label(text="")

            else:
                row = row.row(align=True)
                row.operator("flip_fluid_operators.helper_command_line_render").use_turbo_tools = False
                row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = False
                row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')

            ### Command Line Render Frame ###

            subbox = box.box()
            row = subbox.row(align=True)
            row.prop(hprops, "command_line_render_frame_expanded",
                icon="TRIA_DOWN" if hprops.command_line_render_frame_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Render Frame:")

            if hprops.command_line_render_frame_expanded:
                column = subbox.column(align=True)
                row = column.row(align=True)
                row.operator("flip_fluid_operators.helper_command_line_render_frame")
                row.operator("flip_fluid_operators.helper_cmd_render_frame_to_clipboard", text="", icon='COPYDOWN')
                row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')
                row = column.row(align=True)
                row.enabled = not hprops.render_passes
                row.prop(hprops, "cmd_open_image_after_render")
                if hprops.render_passes:
                    row.label(text="Option not available for passes rendering")

                system = platform.system()
                if system == "Windows":
                    row = column.row(align=True)
                    row.prop(hprops, "cmd_close_window_after_render")
            else:
                row = row.row(align=True)
                row.operator("flip_fluid_operators.helper_command_line_render_frame")
                row.operator("flip_fluid_operators.helper_cmd_render_frame_to_clipboard", text="", icon='COPYDOWN')
                row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')


            ### Turbo Tools Command Line Render ###

            if installation_utils.is_turbo_tools_addon_enabled():
                subbox = box.box()
                row = subbox.row(align=True)
                row.prop(hprops, "command_line_render_turbo_tools_expanded",
                    icon="TRIA_DOWN" if hprops.command_line_render_turbo_tools_expanded else "TRIA_RIGHT",
                    icon_only=True, 
                    emboss=False
                )
                row.label(text="Turbo Tools Command Line Render:")

                if hprops.command_line_render_turbo_tools_expanded:
                    column = subbox.column(align=True)
                    row = subbox.row(align=True)
                    row.alignment = 'LEFT'
                    row.prop(hprops, "turbo_tools_render_tooltip", icon="QUESTION", emboss=False, text="")
                    row.label(text="Turbo Tools Addon Detected")

                    column = subbox.column(align=True)
                    row = column.row(align=True)
                    row.operator("flip_fluid_operators.helper_command_line_render", text="Render Animation").use_turbo_tools = True
                    row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = True
                    row = column.row(align=True)
                    row.operator("flip_fluid_operators.helper_command_line_render_frame", text="Render Frame").use_turbo_tools = True
                    row.operator("flip_fluid_operators.helper_cmd_render_frame_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = True
                    row = column.row(align=True)
                    row.prop(hprops, "cmd_open_image_after_render")

                    if platform.system() == "Windows":
                        row = column.row(align=True)
                        row.prop(hprops, "cmd_close_window_after_render")
                else:
                    row = row.row(align=True)
                    row.operator("flip_fluid_operators.helper_command_line_render", text="Render Animation").use_turbo_tools = True
                    row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = True

            ### Command Line Alembic Export ###

            subbox = box.box()
            row = subbox.row(align=True)
            row.prop(hprops, "command_line_alembic_export_expanded",
                icon="TRIA_DOWN" if hprops.command_line_alembic_export_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.label(text="Alembic Export:")

            if hprops.command_line_alembic_export_expanded:
                column = subbox.column(align=True)
                row = column.row(align=True)
                row.operator("flip_fluid_operators.flip_fluids_alembic_exporter", text="FLIP Fluids Alembic Export", icon="EXPORT")
                row.operator("flip_fluid_operators.helper_cmd_alembic_export_to_clipboard", text="", icon='COPYDOWN')
                row.operator("flip_fluid_operators.helper_open_alembic_output_folder", text="", icon='FILE_FOLDER')
                
                column.separator()
                row = column.row(align=True)
                row.operator("flip_fluid_operators.flip_fluids_alembic_importer", text="FLIP Fluids Alembic Import", icon="IMPORT")
                row.label(text="", icon='BLANK1')
                row.label(text="", icon='BLANK1')

            else:
                row = row.row(align=True)
                row.operator("flip_fluid_operators.flip_fluids_alembic_exporter", text="Launch Alembic Export", icon="EXPORT")
                row.operator("flip_fluid_operators.helper_cmd_alembic_export_to_clipboard", text="", icon='COPYDOWN')
                row.operator("flip_fluid_operators.helper_open_alembic_output_folder", text="", icon='FILE_FOLDER')

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

        prefs = vcu.get_addon_preferences()
        is_developer_mode = prefs.is_extra_features_enabled()
        if hprops.geometry_node_tools_expanded:
            column = box.column(align=True)

            if not vcu.is_blender_31():
                column.label(text="Blender 3.1 or later required")

            if not is_developer_mode:
                warn_box = box.box()
                warn_column = warn_box.column(align=True)
                warn_column.enabled = True
                warn_column.label(text="     This feature is affected by a current bug in Blender.", icon='ERROR')
                warn_column.label(text="     The Extra Features option must be enabled in preferences")
                warn_column.label(text="     to use this feature.")
                warn_column.separator()
                warn_column.prop(prefs, "enable_extra_features", text="Enable Extra Features in Preferences")
                warn_column.separator()
                warn_column.operator(
                    "wm.url_open", 
                    text="Important Info and Limitations", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preferences-Menu-Settings#developer-tools"

            column = box.column(align=False)
            column.enabled = vcu.is_blender_31() and is_developer_mode

            if vcu.is_blender_33():
                # Icon only available in Blender 3.3 or later
                column.operator("flip_fluid_operators.helper_initialize_motion_blur", icon='GEOMETRY_NODES')
            else:
                column.operator("flip_fluid_operators.helper_initialize_motion_blur")

            row = column.row(align=True)
            row.label(text="Toggle Motion Blur Rendering:")
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.operator("flip_fluid_operators.helper_toggle_motion_blur_rendering", 
                    text="ON", 
                    icon="CHECKMARK"
                    ).enable_motion_blur_rendering=True
            row.operator("flip_fluid_operators.helper_toggle_motion_blur_rendering", 
                    text="OFF", 
                    icon="X"
                    ).enable_motion_blur_rendering=False
        else:
            if is_developer_mode and vcu.is_blender_31():
                if vcu.is_blender_33():
                    # Icon only available in Blender 3.3 or later
                    row.operator("flip_fluid_operators.helper_initialize_motion_blur", icon='GEOMETRY_NODES')
                else:
                    row.operator("flip_fluid_operators.helper_initialize_motion_blur")

        #
        # Object Speed Measurement Tools
        #

        box = self.layout.box()
        row = box.row(align=True)
        row.prop(hprops, "object_speed_measurement_tools_expanded",
            icon="TRIA_DOWN" if hprops.object_speed_measurement_tools_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Measure Object Speed Tool:")

        if hprops.object_speed_measurement_tools_expanded:
            selected_objects = bpy.context.selected_objects
            bl_object = vcu.get_active_object(context)
            if selected_objects:
                if bl_object not in selected_objects:
                    bl_object = selected_objects[0]
            else:
                bl_object = None

            op_text = "Measure Object Speed: "
            if bl_object is not None:
                op_text += bl_object.name
            else:
                op_text += "No Object Selected"

            column = box.column(align=True)
            row = column.row(align=True)
            row.operator("flip_fluid_operators.measure_object_speed", text=op_text)
            if hprops.is_translation_data_available:
                row.operator("flip_fluid_operators.clear_measure_object_speed", text="", icon="X")

            column = column.column(align=True)
            split = vcu.ui_split(ui_element=column, factor=0.66, align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)

            column_left.prop(hprops, "update_object_speed_data_on_frame_change")
            row = column_right.row(align=True)
            row.prop(hprops, "measure_object_speed_units_mode", expand=True)
            column.separator()

            if not hprops.is_translation_data_available:
                column.label(text="No Speed Data Available")
                column.label(text="Select an object and use the above operator")
            else:
                try:
                    world_scale = 1.0
                    time_scale = 1.0
                    frame_rate = bpy.context.scene.render.fps
                    dprops = context.scene.flip_fluid.get_domain_properties()
                    if dprops is not None:
                        if dprops.world.world_scale_mode == 'WORLD_SCALE_MODE_RELATIVE':
                            world_scale = dprops.world.world_scale_relative
                        elif dprops.world.world_scale_mode == 'WORLD_SCALE_MODE_ABSOLUTE': 
                            view_x, view_y, view_z = dprops.world.get_viewport_dimensions(context)
                            longest_side = max(view_x, view_y, view_z, 1e-6)
                            world_scale = dprops.world.world_scale_absolute / longest_side

                        eps = 1e-6
                        time_scale = max(dprops.simulation.get_current_frame_time_scale(), eps)
                        frame_rate = dprops.simulation.get_frame_rate()
                except Exception as e:
                    print("FLIP Fluids Object Speed Measurement Tools Error: ", str(e))

                mps_speed_factor = world_scale * frame_rate / time_scale    # Meters per second factor
                fps_speed_factor = 3.28084 * mps_speed_factor               # Feet per second factor
                mps_to_kph_factor = 3.6
                mps_to_mph_factor = 2.23694

                units_str = "m/s"
                min_vertex_speed = mps_speed_factor * hprops.min_vertex_translation
                max_vertex_speed = mps_speed_factor * hprops.max_vertex_translation
                center_speed = mps_speed_factor * hprops.center_translation

                alt_units_str = "km/h"
                min_vertex_speed_alt = mps_to_kph_factor * min_vertex_speed
                max_vertex_speed_alt = mps_to_kph_factor * max_vertex_speed
                center_speed_alt = mps_to_kph_factor * center_speed

                if hprops.measure_object_speed_units_mode == 'MEASUREMENT_UNITS_MODE_IMPERIAL':
                    alt_units_str = "mph"
                    min_vertex_speed_alt = mps_to_mph_factor * min_vertex_speed
                    max_vertex_speed_alt = mps_to_mph_factor * max_vertex_speed
                    center_speed_alt = mps_to_mph_factor * center_speed

                    units_str = "ft/s"
                    min_vertex_speed = fps_speed_factor * hprops.min_vertex_translation
                    max_vertex_speed = fps_speed_factor * hprops.max_vertex_translation
                    center_speed = fps_speed_factor * hprops.center_translation

                header_text = "Name: " + hprops.translation_data_object_name + " | "
                header_text += "Frame: " + str(hprops.translation_data_object_frame) + " | "
                header_text += "Verts: " + str(hprops.translation_data_object_vertices) + " | "
                header_text += "Time: " + str(hprops.translation_data_object_compute_time) + "ms"
                column.label(text=header_text)
                column.separator()
                
                split = column.split(align=True)
                column1 = split.column(align=True)
                column2 = split.column(align=True)
                column3 = split.column(align=True)

                column1.label(text="Center Speed:")
                column1.label(text="Min Vertex Speed:")
                column1.label(text="Max Vertex Speed:")

                column2.label(text='{0:.2f}'.format(center_speed) + " " + units_str)
                column2.label(text='{0:.2f}'.format(min_vertex_speed) + " " + units_str)
                column2.label(text='{0:.2f}'.format(max_vertex_speed) + " " + units_str)

                column3.label(text='{0:.2f}'.format(center_speed_alt) + " " + alt_units_str)
                column3.label(text='{0:.2f}'.format(min_vertex_speed_alt) + " " + alt_units_str)
                column3.label(text='{0:.2f}'.format(max_vertex_speed_alt) + " " + alt_units_str)

                footer_text = "World Scale: " + '{0:.3f}'.format(world_scale) + " | "
                footer_text += "Time Scale: " + '{0:.3f}'.format(time_scale) + " | "
                footer_text += "FPS: " + '{0:.2f}'.format(frame_rate)
                column.separator()
                column.label(text=footer_text)


    def draw_disable_addon_submenu(self, context):
        #
        # Disable Addon in Blend File
        #

        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        hprops = context.scene.flip_fluid_helper
        preferences = vcu.get_addon_preferences(context)

        box = self.layout.box()
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.prop(hprops, "disable_addon_expanded",
            icon="TRIA_DOWN" if hprops.disable_addon_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        if is_addon_disabled:
            row.label(text="Enable Addon:")
            row.alert = True
            row.label(text="FLIP Fluids is disabled")
            row.label(text="", icon='X')
        else:
            row.label(text="Disable Addon:")
            row.label(text="FLIP Fluids is enabled")
            row.label(text="", icon='CHECKMARK')

        if hprops.disable_addon_expanded:
            if is_addon_disabled:
                operator_name = "flip_fluid_operators.enable_addon_in_blend_file"
            else:
                operator_name = "flip_fluid_operators.disable_addon_in_blend_file"

            icon = context.scene.flip_fluid.get_logo_icon()
            column = box.column(align=True)
            if icon is not None:
                column.operator(operator_name, icon_value=icon.icon_id)
            else:
                column.operator(operator_name, icon='X')


    def draw(self, context):
        if not installation_utils.is_installation_complete():
            box = self.layout.box()
            box.label(text="IMPORTANT: Please Complete Installation", icon="ERROR")
            box.label(text="Click here to complete installation of the FLIP Fluids Addon:")
            box.operator("flip_fluid_operators.complete_installation", icon='MOD_FLUIDSIM')
            return

        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        hprops = context.scene.flip_fluid_helper
        preferences = vcu.get_addon_preferences(context)

        if not is_addon_disabled:
            self.draw_simulation_setup_panel(context)

        self.draw_disable_addon_submenu(context)
        

class FLIPFLUID_PT_HelperPanelCompositingTools(bpy.types.Panel):
    bl_label = "Compositing Tools"
    bl_category = "FLIP Fluids"
    bl_space_type = 'VIEW_3D'
    bl_options = {'DEFAULT_CLOSED'}
    if vcu.is_blender_28():
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return not context.scene.flip_fluid.is_addon_disabled_in_blend_file()

    def draw(self, context):
        layout = self.layout
        if not installation_utils.is_installation_complete():
            return

        hprops = context.scene.flip_fluid_helper

        # Domain-Check
        domain_obj = context.scene.flip_fluid.get_domain_object()
        has_domain = domain_obj is not None

        # Finished initialize?
        initialize_all_conditions_met = False
        if domain_obj:
            initialize_all_conditions_met = (
                domain_obj.flip_fluid.domain.particles.enable_fluid_particle_velocity_vector_attribute and
                domain_obj.flip_fluid.domain.whitewater.enable_velocity_vector_attribute and
                domain_obj.flip_fluid.domain.surface.enable_velocity_vector_attribute and
                #domain_obj.flip_fluid.domain.surface.remove_mesh_near_domain and # Disabled testwise
                #context.scene.render.engine == 'CYCLES' and # Disabled testwise
                context.scene.render.film_transparent and
                domain_obj.flip_fluid.domain.whitewater.enable_id_attribute
            )

        # CameraScreen-Check
        camera_screen_exists = bpy.data.objects.get("ff_camera_screen") is not None

        box = self.layout.box()

        # 1. Missing Domain
        if not has_domain:
            row = box.row()
            row.label(text="Missing FLIP Fluids Domain", icon='ERROR')
            return

        # 2. Initialize not finished
        if not initialize_all_conditions_met:
            row = box.row()
            row.label(text="Compositing setup is incomplete", icon='ERROR')

            # Initialize All Button
            row = box.row(align=True)
            row.operator(
                "flip_fluid_operators.helper_initialize_compositing", 
                text="Initialize All", 
                icon='SETTINGS'
            )
            return

        # 3. Missing CameraScreen
        if not camera_screen_exists:
            # Hinweis und Add Camera Screen Button im aufgeklappten Zustand
            row = box.row()
            row.label(text="Add CameraScreen to continue", icon='INFO')

            # Add Camera Screen Button
            row = box.row(align=True)
            row.operator("flip_fluid_operators.add_camera_screen", text="Add CameraScreen", icon='IMAGE_BACKGROUND')
            return

        # 4. Everything was setup. Continue:

        row = box.row(align=True)
        row.active = hprops.render_passes and hprops.render_passes_is_any_pass_enabled and not hprops.render_passes_stillimagemode_toggle
        row.operator("flip_fluid_operators.helper_command_line_render", text="Launch Render Passes").use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')

        # Render Passes Checkbox
        row = box.row(align=True)
        row.prop(hprops, "render_passes")

        row = box.row()
        row.alignment = 'LEFT'
        row.prop(context.scene.render, "film_transparent", text="Film Transparency")

        # Checkboxes for render passes with aligned width
        def add_fixed_width_prop(row, prop_name, enabled):
            box = row.box()
            col = box.column()
            col.scale_x = 1.5
            col.enabled = enabled  # Deaktiviert Checkbox wenn nicht verfügbar
            col.prop(hprops, prop_name)

        def add_fixed_width_placeholder(row):
            box = row.box()
            col = box.column()
            col.scale_x = 1.5
            col.label(text="")

        # ---------------------------------
        # Aktivitätsbedingungen ermitteln
        # ---------------------------------

        # 1) Fluid Surface
        has_fluid_surface = ("fluid_surface" in bpy.data.objects)

        # 2) Objekte ohne Flag (ungetagged)
        has_unflagged_objects = hprops.render_passes_has_unflagged_objects

        # 3) Elements
        has_elements = any(
            item.fg_elements or item.bg_elements or item.ref_elements
            for item in hprops.render_passes_objectlist
        )

        # 4) Fluid Particles/Whitewater -> gezielt Domain-Objekt abfragen
        has_fluid_particles = False
        has_whitewater = False
        if domain_obj is not None:
            has_fluid_particles = domain_obj.flip_fluid.domain.particles.enable_fluid_particle_output
            has_whitewater = domain_obj.flip_fluid.domain.whitewater.enable_whitewater_simulation

        # ---------------------------------
        # First row of checkboxes
        # ---------------------------------
        column = box.column(align=True)
        row1 = column.row(align=True)

        add_fixed_width_prop(row1, "render_passes_fluid_only", has_fluid_surface)
        add_fixed_width_prop(row1, "render_passes_objects_only", has_unflagged_objects)
        add_fixed_width_prop(row1, "render_passes_elements_only", has_elements)

        # ---------------------------------
        # Second row of checkboxes
        # ---------------------------------
        # row2 = column.row(align=True)
        # add_fixed_width_prop(row2, "render_passes_fluid_shadows_only", is_render_passes_active)
        # add_fixed_width_prop(row2, "render_passes_reflr_only", has_fluid_surface)
        # add_fixed_width_placeholder(row2)
        # DISABLED REFLECTIONS - NEED TO FIND A BETTER WORKFLOW

        # ---------------------------------
        # Third row of checkboxes
        # ---------------------------------
        row3 = column.row(align=True)
        add_fixed_width_prop(row3, "render_passes_fluidparticles_only", has_fluid_particles)
        add_fixed_width_prop(row3, "render_passes_foamandspray_only", has_whitewater)
        add_fixed_width_prop(row3, "render_passes_bubblesanddust_only", has_whitewater)

        box.separator()

        # Add separator and group elements for Camera, Alignment, and Background Image Settings
        settings_box = box.box()

        # Group Alignment and Camera Screen Settings
        camera_screen_exists = bpy.data.objects.get("ff_camera_screen") is not None
        alignment_grid_exists = bpy.data.objects.get("ff_alignment_grid") is not None
        
        row = settings_box.row(align=True)

        row1 = row.row()
        row1.enabled = camera_screen_exists
        row1.prop(hprops, "render_passes_camerascreen_visibility", text="Show CameraScreen")

        row2 = row.row()
        row2.enabled = alignment_grid_exists
        row2.prop(hprops, "render_passes_alignmentgrid_visibility", text="Show Alignment Grid")

        # Show Background Image checkbox and Opacity slider
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            row = settings_box.row(align=True)
            row.prop(camera.data, "show_background_images", text="Show Background Image")

            if not camera.data.background_images:
                bg_image = camera.data.background_images.new()
            else:
                bg_image = camera.data.background_images[0]

            if bg_image and bg_image.image:
                row.prop(bg_image, "alpha", text="Opacity")

        # Camera screen settings in compact layout
        column = settings_box.column(align=True)

        # First row for camera selection and camera screen distance
        row = column.row(align=True)
        row.prop(hprops, 'render_passes_cameraselection', text="")
        row.operator("flip_fluid_operators.add_camera_screen", text="CameraScreen", icon='IMAGE_BACKGROUND')
        row.prop(hprops, 'render_passes_camerascreen_distance', text="")

        # Second row for still image mode toggle
        row = column.row(align=True)
        row.prop(hprops, 'render_passes_stillimagemode_toggle', text="Still Image Mode", toggle=True, icon='IMAGE_DATA')

        # View Transform settings
        row = box.row(align=True)
        row.prop(context.scene.view_settings, "view_transform", text="View Transform")

        # Objects to render list
        row = box.row()
        row.label(text="Objects to render (no fluid objects):")
        row = box.row()
        row.template_list("FLIPFLUID_UL_passes_items", "", hprops, "render_passes_objectlist", hprops, "render_passes_objectlist_index")

        col = row.column(align=True)
        col.operator("flip_fluid_operators.add_item_to_list", icon='ADD', text="")
        col.operator("flip_fluid_operators.remove_item_from_list", icon='REMOVE', text="").index = hprops.render_passes_objectlist_index

        box.separator()


        column = box.column(align=True)

        # Import Media Button:
        row = column.row(align=True)
        row.enabled = hprops.render_passes_stillimagemode_toggle
        row.operator("flip_fluid.passes_import_media", text="Import Images as Elements", icon='FILE_IMAGE')

        # Foreground and Background Buttons:
        row = column.row(align=True)
        row.operator("flip_fluid_operators.quick_foregroundcatcher", text="FG Element", icon='IMAGE_REFERENCE')
        row.operator("flip_fluid_operators.quick_backgroundcatcher", text="BG Element", icon='IMAGE_BACKGROUND')
        row.operator("flip_fluid_operators.quick_reflectivecatcher", text="REF Element", icon='IMAGE_BACKGROUND')

        # Ground and Alignment Grid Buttons:
        row = column.row(align=True)
        row.operator("flip_fluid_operators.quick_ground", text="Ground Object", icon='ALIGN_BOTTOM')
        row.operator("flip_fluid_operators.duplicate_item_in_list", text="Duplicate Object", icon='DUPLICATE')
        row.operator("flip_fluid_operators.add_alignment_grid", text="Alignment Grid", icon='GRID')

        box.separator()

        # Fader area
        fader_box = box.box()
        fader_box.label(text="Fading Settings:")

        # Row for the "Show Faders" and "Blend Testcolor" checkboxes
        row_1 = fader_box.row(align=True)
        row_1.prop(hprops, "render_passes_faderobjects_visibility", text="Show Faders")
        row_1.prop(hprops, "render_passes_faderobjectnames_visibility", text="Fader Names")
        row_1.prop(hprops, "render_passes_objectnames_visibility", text="Object Names")

        # Row for the other three checkboxes
        row_2 = fader_box.row(align=True)
        row_2.prop(hprops, "render_passes_toggle_fader_fluidsurface", text="Fader")
        row_2.prop(hprops, "render_passes_toggle_speed_fluidsurface", text="Speed")
        row_2.prop(hprops, "render_passes_toggle_domain_fluidsurface", text="Domain")

        # Buttons and Sliders in compact layout using column
        column = fader_box.column(align=True)

        # Row for Buttons
        row_3 = column.row(align=True)

        # Row for Buttons (Velocity / Invert)
        row_3 = column.row(align=True)
        velocity_button = row_3.row(align=True)
        velocity_button.scale_x = 1.0
        velocity_button.enabled = hprops.render_passes_toggle_speed_fluidsurface == 1
        velocity_button.prop(hprops, "render_passes_toggle_velocity_fluidsurface", text="Velocity", icon='MOD_WAVE')

        invert_button = row_3.row(align=True)
        invert_button.scale_x = 1.0
        invert_button.enabled = hprops.render_passes_toggle_velocity_fluidsurface == 1
        invert_button.prop(hprops, "render_passes_toggle_velocity_invert", text="Invert", icon='ARROW_LEFTRIGHT')

        # Row for Sliders (Fade Footage / Footage / Normal)
        row_4 = column.row(align=True)
        row_4.prop(hprops, "render_passes_toggle_projectionfader", text="Fade Footage", icon='IMAGE_ALPHA')
        row_4.prop(hprops, "render_passes_blend_footage_to_fluidsurface", text="Footage")
        row_4.prop(hprops, "render_passes_blend_normalmap_to_fluidsurface", text="Normal")

        # Row for "Find Fluid" and "Find Reflections"
        row_find = column.row(align=True)
        row_find.prop(hprops, "render_passes_toggle_projectiontester", text="Find Fluid", icon='ZOOM_SELECTED')
        # row_find.prop(hprops, "render_passes_toggle_findreflections", text="Find Reflections", icon='ZOOM_SELECTED')
        # DISABLED TILL I FOUND A BETTER WORKFLOW FOR RENDERING


        # Collapsible Fader Panel (ColorRamps)
        def draw_fader_details(parent_layout, context):
            """Draws a collapsible section for ColorRamp settings and Fading controls within the Fading area."""
            hprops = context.scene.flip_fluid_helper

            # Collapsible Toggle (row with icon and text)
            row_toggle = parent_layout.row()
            icon = 'TRIA_DOWN' if hprops.render_passes_show_fader_details else 'TRIA_RIGHT'
            row_toggle.prop(hprops, "render_passes_show_fader_details", icon=icon, emboss=False, text="Advanced Fader Settings")

            # If the section is collapsed, don't draw the details
            if not hprops.render_passes_show_fader_details:
                return

            # Add ColorRamp nodes directly within the Fader Panel
            parent_layout.label(text="fluid_surface Fading Controls", icon='NODE_MATERIAL')

            material_name = "FF ClearWater_Passes"
            node_names = [
                "ff_fader_colorramp",
                "ff_objects_colorramp",
                "ff_speed_colorramp",
                "ff_domain_colorramp",
                "ff_footage_colorramp"
            ]

            mat = bpy.data.materials.get(material_name)
            if not mat:
                parent_layout.label(text=f"Material '{material_name}' not found.", icon='ERROR')
            elif not mat.use_nodes or not mat.node_tree:
                parent_layout.label(text="Material has no node setup.", icon='ERROR')
            else:
                node_tree = mat.node_tree
                # Loop through relevant ColorRamp nodes
                for node_name in node_names:
                    node = node_tree.nodes.get(node_name)
                    if node and node.type == 'VALTORGB':
                        # Draw each ColorRamp in the existing layout
                        row = parent_layout.row(align=True)
                        row.label(text=node_name)
                        row.template_color_ramp(node, "color_ramp", expand=False)
                    else:
                        parent_layout.label(text=f"'{node_name}' not found or not a ColorRamp.", icon='INFO')

            # Row for Object-Based Fading Width on fluid_surface
            row = parent_layout.row(align=True)
            row.prop(hprops, "render_passes_object_fading_width_fluid_surface", slider=True, text="Object Fading Width (fluid_surface)")

            # Row for Object-Based Fading Softness on fluid_surface
            row = parent_layout.row(align=True)
            row.prop(hprops, "render_passes_object_fading_softness_fluid_surface", slider=True, text="Object Fading Softness (fluid_surface)")

            # Add Sliders for GeometryNode Modifiers
            parent_layout.separator()
            parent_layout.label(text="Particle Fading Controls", icon='MODIFIER')

            # Row for Object-Based Fading Width
            row = parent_layout.row(align=True)
            row.prop(hprops, "render_passes_object_fading_width", slider=True, text="Object Fading Width (Particles)")

            # Row for Object-Based Fading Softness
            row = parent_layout.row(align=True)
            row.prop(hprops, "render_passes_object_fading_softness", slider=True, text="Object Fading Softness (Particles)")

            # Row for General Fading Width
            row = parent_layout.row(align=True)
            row.prop(hprops, "render_passes_general_fading_width", slider=True, text="General Fading Width")


        # Draw the collapsible Fader Details section directly in the Fader Panel
        draw_fader_details(fader_box, context)

        box.separator()

        # Reset and Apply buttons in compact layout
        column = box.column(align=True)

        if context.scene.flip_fluid.is_domain_object_set():
            row = column.row(align=True)
            
            # Select Domain Button
            row.operator("flip_fluid_operators.helper_select_domain", text="Select Domain Object", icon="MESH_GRID")

            # Unsaved File Warning
            is_saved = bool(bpy.data.filepath)
            if not is_saved:
                row.prop(hprops, "unsaved_blend_file_tooltip", icon="ERROR", emboss=False, text="")
                row.alert = True
                row.label(text="Unsaved File")
                row.operator("flip_fluid_operators.helper_save_blend_file", icon='FILE_TICK', text="Save")
                row.alert = False  # Reset alert state

            # Resolution Setting
            dprops = context.scene.flip_fluid.get_domain_properties()
            resolution_text = "Resolution"
            if dprops.simulation.lock_cell_size:
                resolution_text += " (voxel size locked)"

            row.enabled = not dprops.simulation.lock_cell_size and not dprops.bake.is_simulation_running
            row.prop(dprops.simulation, "resolution", text=resolution_text)

            # Bake Operator UI Element
            domain_simulation_ui.draw_bake_operator_UI_element(context, column)

        column.separator()

        # Row for Reset settings (separate row)
        row = column.row(align=True)
        row.operator("flip_fluid_operators.reset_passes_settings", text="Set Visibility Options", icon='HIDE_OFF')

        # Row for Apply Materials and Refresh/Fix All (in the same row)
        row = column.row(align=True)
        row.operator("flip_fluid_operators.apply_all_materials", text="Apply All Materials", icon='MATERIAL')
        row.operator("flip_fluid_operators.helper_fix_compositingtextures", text="Refresh / Fix All", icon='FILE_REFRESH')

        # Render Passes Launch buttons (separate row)
        row = column.row(align=True)
        row.active = hprops.render_passes and hprops.render_passes_is_any_pass_enabled and not hprops.render_passes_stillimagemode_toggle
        row.operator("flip_fluid_operators.helper_command_line_render", text="Launch Render Passes").use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')

        #maybe later:
        #row = column.row(align=True)
        #row.operator("flip_fluid_operators.create_resolve_project", text="Export Video Editor File", icon='FILE_MOVIE')

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
        return not context.scene.flip_fluid.is_addon_disabled_in_blend_file()


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

            column.label(text="Fluid Particle Display:")
            row = column.row(align=True)
            row.prop(rprops, "fluid_particle_viewport_display", expand=True)


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
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return prefs.enable_support_tools and not is_addon_disabled


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
    # Small fix: It´s properties.helper_properties.py
    pass


def unregister():
    try:
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelMain)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelCompositingTools)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelDisplay)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperTechnicalSupport)

    except:
        pass
