# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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

from ..utils import export_utils
from ..utils import version_compatibility_utils as vcu


DRAW_OBJECT_FLIP_TYPE_PROPERTY = True


def draw_bake_operator_UI_element(context, ui_box):
    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return

    bakeprops = dprops.bake
    simprops = dprops.simulation
    if not bakeprops.is_simulation_running:
        if bakeprops.is_autosave_available:
            frame_str = str(bakeprops.autosave_frame + 1)
            if simprops.enable_savestates:
                frame_str = str(int(simprops.selected_savestate) + 1)

            operator_text = "Resume Baking  (from frame " + frame_str + ")"
        else:
            operator_text = "Bake"
    elif bakeprops.is_export_operator_running:
        progress = bakeprops.export_progress
        stage = bakeprops.export_stage
        pct_string = str(round(progress * 100, 1)) + "%"

        if stage == 'STATIC':
            operator_text = "Exporting static data... " + pct_string
        elif stage == 'KEYFRAMED':
            operator_text = "Exporting keyframe data... " + pct_string
        elif stage == 'ANIMATED':
            operator_text = "Exporting animated data... " + pct_string
        else:
            operator_text = "Exporting data... "

    elif not bakeprops.is_bake_initialized:
        operator_text = "Baking in progress... initializing"
    elif bakeprops.is_bake_cancelled:
        if bakeprops.is_safe_to_exit:
            safety_str = "Safe to quit Blender"
        else:
            safety_str = "Do NOT quit Blender"
        operator_text = "Cancelling... " + safety_str
    else:
        num_frames = simprops.frame_end - simprops.frame_start + 1
        frame_progress_string = str(bakeprops.num_baked_frames) + " / " + str(num_frames)
        pct_string = str(round((bakeprops.num_baked_frames / num_frames) * 100, 1)) + "%"
        frames_string = pct_string + "  (" + frame_progress_string + ")"
        frames_string += "  (" + str(simprops.frame_start + bakeprops.num_baked_frames) + ")"
        operator_text = "Baking in progress...   " + frames_string

    column = ui_box.column(align=True)

    if not bakeprops.is_simulation_running and bakeprops.is_autosave_available:
        split = vcu.ui_split(column, factor=0.75, align=True)
        column_left = split.column(align=True)
        column_left.operator("flip_fluid_operators.bake_fluid_simulation", 
                             text=operator_text)

        column_right = split.column(align=True)
        column_right.alert = True
        column_right.operator("flip_fluid_operators.reset_bake", 
                              text="Reset")

        if simprops.enable_savestates:
            if simprops.get_num_savestate_enums() < 100:
                column_left.prop(simprops, "selected_savestate", text="")
            else:
                column_right.alert = False
                row = column_left.row(align=True)
                row.prop(simprops, "selected_savestate_int", text="Resume from frame")
                column_right.label(text=simprops.selected_savestate_int_label)
            
    else:
        column.operator("flip_fluid_operators.bake_fluid_simulation", 
                        text=operator_text)
        if bakeprops.is_simulation_running:
            column.operator("flip_fluid_operators.cancel_bake_fluid_simulation", 
                            text="Stop / Pause")

    if dprops.bake.is_simulation_running:
        row = column.row()
        row.alignment = "RIGHT"
        if dprops.stats.is_estimated_time_remaining_available:
            row.label(text="Estimated Time Remaining:    " + dprops.stats.get_time_remaining_string(context))
        else:
            row.label(text="Calculating time remaining...")


def draw_bake_operator(self, context, box):
    box.label(text="Bake Simulation:")
    draw_bake_operator_UI_element(context, box)


def draw_more_bake_settings(self, context, box):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    sprops = dprops.simulation
    show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

    if not show_advanced:
        return

    row = box.row(align=True)
    row.prop(sprops, "more_bake_settings_expanded",
        icon="TRIA_DOWN" if sprops.more_bake_settings_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="More Bake Settings")

    if not sprops.more_bake_settings_expanded:
        return

    subbox = box.box()
    column = subbox.column(align=True)
    column.label(text="Frame Range:")
    row = column.row()
    row.prop(sprops, "frame_range_mode", expand=True)
    row = column.row(align=True)
    if sprops.frame_range_mode == 'FRAME_RANGE_TIMELINE':
        row_left = row.row(align=True)
        row_right = row.row(align=True)
        if dprops.bake.is_autosave_available:
            row_left.enabled = False
            row_left.prop(dprops.bake, "original_frame_start")
        else:
            row_left.prop(context.scene, "frame_start")
        row_right.prop(context.scene, "frame_end")
    else:
        row_left = row.row(align=True)
        row_right = row.row(align=True)
        if dprops.bake.is_autosave_available:
            row_left.enabled = False
            row_left.prop(dprops.bake, "original_frame_start")
        else:
            row_left.prop(sprops.frame_range_custom, "value_min")
        row_right.prop(sprops.frame_range_custom, "value_max")

    subbox = box.box()
    column = subbox.column(align=True)
    column.label(text="Settings and Mesh Export:")
    column.prop(sprops, "update_settings_on_resume")

    indent_str = 5 * " "

    subbox = subbox.box()
    row = subbox.row(align=True)
    row.prop(sprops, "skip_mesh_reexport_expanded",
        icon="TRIA_DOWN" if sprops.skip_mesh_reexport_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Skip Mesh Re-Export:")

    if sprops.skip_mesh_reexport_expanded:
        column = subbox.column()
        column.label(text="Object Motion Type:")
        row = column.row(align=True)
        row.prop(sprops, "mesh_reexport_type_filter", expand=True)

        flip_props = context.scene.flip_fluid
        flip_objects = (flip_props.get_obstacle_objects() + 
                       flip_props.get_fluid_objects() + 
                       flip_props.get_inflow_objects() + 
                       flip_props.get_outflow_objects() + 
                       flip_props.get_force_field_objects())
        flip_objects.sort(key=lambda x: x.name)

        is_all_filter_selected = sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_ALL'
        if sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_ALL':
            filtered_objects = flip_objects
            motion_type_string = "simulation"
        elif sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_STATIC':
            filtered_objects = [x for x in flip_objects if _get_object_motion_type(self, x) == 'STATIC']
            motion_type_string = "static"
        elif sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_KEYFRAMED':
            filtered_objects = [x for x in flip_objects if _get_object_motion_type(self, x) == 'KEYFRAMED']
            motion_type_string = "keyframed"
        elif sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_ANIMATED':
            filtered_objects = [x for x in flip_objects if _get_object_motion_type(self, x) == 'ANIMATED']
            motion_type_string = "animated"

        if len(filtered_objects) == 0:
            column.label(text=indent_str + "No " + motion_type_string + " objects found...")
        else:
            split = column.split()
            column_left = split.column(align=True)
            if is_all_filter_selected:
                column_animated = split.column(align=True)

            column_middle = split.column(align=True)
            column_right = split.column(align=True)

            column_left.label(text="")
            column_left.label(text="Object")
            op_box = column_left.box()
            op_box.label(text="")

            if is_all_filter_selected:
                column_animated.label(text="")
                column_animated.label(text="Export Animated")
                op_box = column_animated.box()
                row = op_box.row(align=True)
                row.alignment = 'LEFT'
                row.operator("flip_fluid_operators.helper_batch_export_animated_mesh", icon='CHECKBOX_HLT', text="").enable_state = True
                row.operator("flip_fluid_operators.helper_batch_export_animated_mesh", icon='CHECKBOX_DEHLT', text="").enable_state = False
                row.label(text="All")

            column_middle.label(text="")
            column_middle.label(text="Skip Re-Export")
            op_box = column_middle.box()
            row = op_box.row(align=True)
            row.alignment = 'LEFT'
            row.operator("flip_fluid_operators.helper_batch_skip_reexport", icon='CHECKBOX_HLT', text="").enable_state = True
            row.operator("flip_fluid_operators.helper_batch_skip_reexport", icon='CHECKBOX_DEHLT', text="").enable_state = False
            row.label(text="All")

            column_right.label(text="Force Export")
            column_right.label(text="On Next Bake")
            op_box = column_right.box()
            row = op_box.row(align=True)
            row.alignment = 'LEFT'
            row.operator("flip_fluid_operators.helper_batch_force_reexport", icon='CHECKBOX_HLT', text="").enable_state = True
            row.operator("flip_fluid_operators.helper_batch_force_reexport", icon='CHECKBOX_DEHLT', text="").enable_state = False
            row.label(text="All")

            for ob in filtered_objects:
                pgroup = ob.flip_fluid.get_property_group()
                column_left.label(text=ob.name, icon="OBJECT_DATA")
                if is_all_filter_selected:
                    column_animated.prop(pgroup, "export_animated_mesh", text="animated", toggle=True)
                column_middle.prop(pgroup, "skip_reexport", text="skip", toggle=True)
                column_right.prop(pgroup, "force_reexport_on_next_bake", text="force", toggle=True)

    subbox = box.box()
    column = subbox.column(align=True)
    column.label(text="Savestates:")
    column.prop(sprops, "enable_savestates")
    column = subbox.column(align=True)
    column.enabled = sprops.enable_savestates
    split = column.split()
    column = split.column()
    row = column.row()
    row.alignment = 'RIGHT'
    row.label(text="Generate savestate every")
    column = split.column()
    split = column.split()
    column = split.column()
    row = column.row(align=True)
    row.prop(sprops, "savestate_interval", text="")
    row.label(text="frames")
    column = subbox.column(align=True)
    column.enabled = sprops.enable_savestates
    column.prop(sprops, "delete_outdated_savestates")
    column.prop(sprops, "delete_outdated_meshes")


def draw_resolution_settings(self, context, master_column):
    obj = vcu.get_active_object(context)
    dprops = obj.flip_fluid.domain
    sprops = dprops.simulation
    wprops = dprops.world
    aprops = dprops.advanced
    show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
    show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

    box = master_column.box()
    column = box.column(align=True)
    split = column.split(align=True)
    column_left = split.column(align=True)
    column_right = split.column(align=True)
    row = column_left.row(align=True)
    row.prop(sprops, "simulation_resolution_expanded",
        icon="TRIA_DOWN" if sprops.simulation_resolution_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Grid Resolution:")

    if not sprops.simulation_resolution_expanded:
        row = column_right.row(align=True)
        row.prop(sprops, "resolution", text="Resolution")
    else:
        column = box.column(align=True)
        split = vcu.ui_split(column, factor=0.5, align=True)
        
        column_left = split.column(align=True)
        column_left.enabled = not sprops.lock_cell_size
        column_left.prop(sprops, "resolution")

        column_right = split.column(align=True)
        column_right.enabled = not sprops.auto_preview_resolution
        column_right.prop(sprops, "preview_resolution")

        column = box.column(align=True)
        split = vcu.ui_split(column, factor=0.5)
        column_left = split.column(align=True)
        column_right = split.column(align=True)
        if show_advanced:
            column_left.prop(sprops, "lock_cell_size")

        column_right.prop(sprops, "auto_preview_resolution", text="Use Recommended")

        if not dprops.bake.is_simulation_running and sprops.is_current_grid_upscaled():
            old_resolution = max(sprops.savestate_isize, sprops.savestate_jsize, sprops.savestate_ksize)

            indent = 7
            subbox = box.box()
            column = subbox.column(align=True)
            column.label(text="Increased resolution detected")
            row = column.row()
            row.prop(sprops, "upscale_resolution_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="Simulation will be upscaled on resume.")
            column.label(text=indent*" " + "     Cache resolution:    " + str(old_resolution))
            column.label(text=indent*" " + "     Current resolution:  " + str(sprops.resolution))

    box = master_column.box()
    row = box.row(align=True)
    row.prop(sprops, "grid_info_expanded",
        icon="TRIA_DOWN" if sprops.grid_info_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Grid Info:")
    row = row.row()
    row.alignment = 'RIGHT'
    row.prop(dprops.debug, "display_simulation_grid", text="Visualize Grid")

    if sprops.grid_info_expanded:
        column = box.column(align=True)

        split = vcu.ui_split(column, factor=0.05, align=True)
        column_left = split.column(align=True)
        column_right = split.column(align=True)
        split = vcu.ui_split(column_right, factor=0.4, align=True)
        column_middle = split.column(align=True)
        column_right = split.column(align=True)

        column_left.prop(sprops, "grid_voxels_tooltip", icon="QUESTION", emboss=False, text="")
        column_left.prop(sprops, "grid_dimensions_tooltip", icon="QUESTION", emboss=False, text="")
        column_left.prop(sprops, "grid_voxel_size_tooltip", icon="QUESTION", emboss=False, text="")
        column_left.prop(sprops, "grid_voxel_count_tooltip", icon="QUESTION", emboss=False, text="")

        row = column_middle.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Voxels 3D =")

        row = column_middle.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Dimensions 3D =")

        row = column_middle.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Voxel Size =")

        row = column_middle.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Voxel Count =")

        isize, jsize, ksize, dx = sprops.get_simulation_grid_dimensions()
        voxel_str = str(isize) + "  x  " + str(jsize) + "  x  " + str(ksize)

        xdims, ydims, zdims = wprops.get_simulation_dimensions(context)
        xdims_str = '{:.2f}'.format(round(xdims, 2))
        ydims_str = '{:.2f}'.format(round(ydims, 2))
        zdims_str = '{:.2f}'.format(round(zdims, 2))
        xdims_str = xdims_str.rstrip("0").rstrip(".") + "m"
        ydims_str = ydims_str.rstrip("0").rstrip(".") + "m"
        zdims_str = zdims_str.rstrip("0").rstrip(".") + "m"
        dimensions_str = str(xdims_str) + "  x  " + str(ydims_str) + "  x  " + str(zdims_str)

        display_dx = dx
        suffix = "m"
        if int(display_dx) == 0:
            display_dx *= 100
            suffix = "cm"
        if int(display_dx) == 0:
            display_dx *= 10
            suffix = "mm"
        voxel_size_str = '{:.3f}'.format(round(display_dx, 3)) + " " + suffix

        voxel_count_str = '{:,}'.format(isize * jsize * ksize).replace(',', ' ')

        column_right.label(text=voxel_str)
        column_right.label(text=dimensions_str)
        column_right.label(text=voxel_size_str)
        column_right.label(text=voxel_count_str)

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                    "wm.url_open", 
                    text="What is the simulation grid?", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Simulation-Settings#what-is-the-domain-simulation-grid"

    box = master_column.box()
    column = box.column(align=True)
    split = column.split(align=True)
    column_left = split.column(align=True)
    column_right = split.column(align=True)
    row = column_left.row(align=True)
    row.prop(sprops, "simulation_method_expanded",
        icon="TRIA_DOWN" if sprops.simulation_method_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Simulation Method:")

    if not sprops.simulation_method_expanded:
        row = column_right.row()
        row.prop(aprops, "velocity_transfer_method", expand=True)
        pass
    else:
        column = box.column(align=True)
        row = column.row(align=True)
        row.prop(aprops, "velocity_transfer_method", expand=True)
        row = column.row(align=True)
        if aprops.velocity_transfer_method == 'VELOCITY_TRANSFER_METHOD_FLIP':
            row.prop(aprops, "PICFLIP_ratio", slider=True)
        else:
            row.label(text="")

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                "wm.url_open", 
                text="FLIP vs APIC", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Advanced-Settings#flip-vs-apic"
    
    box = master_column.box()
    row = box.row(align=True)
    row.prop(sprops, "world_scale_expanded",
        icon="TRIA_DOWN" if sprops.world_scale_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )

    xdims, ydims, zdims = wprops.get_simulation_dimensions(context)
    xdims_str = '{:.2f}'.format(round(xdims, 2))
    ydims_str = '{:.2f}'.format(round(ydims, 2))
    zdims_str = '{:.2f}'.format(round(zdims, 2))
    xdims_str = xdims_str.rstrip("0").rstrip(".") + "m"
    ydims_str = ydims_str.rstrip("0").rstrip(".") + "m"
    zdims_str = zdims_str.rstrip("0").rstrip(".") + "m"
    dimensions_str = str(xdims_str) + "  x  " + str(ydims_str) + "  x  " + str(zdims_str)
    row.label(text="World Scale:")
    row = row.row(align=True)
    row.alignment = 'LEFT'
    row.label(text=dimensions_str)

    if not sprops.world_scale_expanded:
        pass
    else:
        row = box.row(align=True)
        row.prop(wprops, "world_scale_mode", expand=True)

        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_right = split.column()

        if wprops.world_scale_mode == 'WORLD_SCALE_MODE_RELATIVE':
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="1 Blender Unit = ")
            column_right.prop(wprops, "world_scale_relative")
        else:
            row = column_left.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="Domain Length = ")
            column_right.prop(wprops, "world_scale_absolute")


        if show_documentation:
            column = box.column(align=True)
            column.operator(
                    "wm.url_open", 
                    text="World Scaling Documentation", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-World-Settings#world-size"

    box = master_column.box()
    row = box.row(align=True)
    row.prop(sprops, "boundary_collisions_expanded",
        icon="TRIA_DOWN" if sprops.boundary_collisions_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Domain Boundary Collisions:")

    if all(sprops.fluid_boundary_collisions):
        boundary_collision_status_str = "Closed"
    elif not any(sprops.fluid_boundary_collisions):
        boundary_collision_status_str = "Open"
    else:
        boundary_collision_status_str = "Mixed"

    row = row.row(align=True)
    row.alignment = 'RIGHT'
    row.label(text=boundary_collision_status_str)

    if not sprops.boundary_collisions_expanded:
        pass
    else:
        column = box.column(align=True)
        row = column.row(align=True)
        row.prop(sprops, "fluid_boundary_collisions", index=0, text="X –")
        row.prop(sprops, "fluid_boundary_collisions", index=1, text="X+")
        row = column.row(align=True)
        row.prop(sprops, "fluid_boundary_collisions", index=2, text="Y –")
        row.prop(sprops, "fluid_boundary_collisions", index=3, text="Y+")
        row = column.row(align=True)
        row.prop(sprops, "fluid_boundary_collisions", index=4, text="Z –")
        row.prop(sprops, "fluid_boundary_collisions", index=5, text="Z+")
        column.prop(sprops, "fluid_open_boundary_width", slider=True)


def _get_object_motion_type(self, obj):
    props = obj.flip_fluid.get_property_group()
    if hasattr(props, 'export_animated_mesh') and props.export_animated_mesh:
        return 'ANIMATED'
    if export_utils.is_object_keyframe_animated(obj):
        return 'KEYFRAMED'
    return 'STATIC'


def draw_time_settings(self, context, box):
    obj = vcu.get_active_object(context)
    sprops = obj.flip_fluid.domain.simulation
    show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

    row = box.row(align=True)
    row.prop(sprops, "frame_rate_and_time_scale_expanded",
        icon="TRIA_DOWN" if sprops.frame_rate_and_time_scale_expanded else "TRIA_RIGHT",
        icon_only=True, 
        emboss=False
    )
    row.label(text="Frame Rate and Time Scale:")

    if not sprops.frame_rate_and_time_scale_expanded:
        fps_str = "{:.2f}".format(sprops.get_frame_rate()) + " FPS"
        row = row.row(align =True)
        row.alignment = 'RIGHT'
        row.label(text=fps_str)
        return

    column = box.column(align=True)
    column.label(text="Frame Rate:")

    row = column.row(align=True)
    row.prop(sprops, "frame_rate_mode", expand=True)
    column = column.column(align=True)
    column.enabled = sprops.frame_rate_mode == 'FRAME_RATE_MODE_CUSTOM'
    if sprops.frame_rate_mode == 'FRAME_RATE_MODE_SCENE':
        column.prop(context.scene.render, "fps", text="Scene Frame Rate")
    else:
        column.prop(sprops, "frame_rate_custom", text="Custom Frame Rate")

    column = box.column(align=True)
    column.label(text="Time Scale:")

    row = column.row(align=True)
    row.prop(sprops, "time_scale_mode", expand=True)
    column = column.column(align=True)

    if sprops.time_scale_mode == 'TIME_SCALE_MODE_CUSTOM':
        column.prop(sprops, "time_scale", text="Custom Time Scale")
    elif sprops.time_scale_mode == 'TIME_SCALE_MODE_RIGID_BODY':
        if bpy.context.scene.rigidbody_world is not None:
            column.prop(bpy.context.scene.rigidbody_world, "time_scale", text="Rigid Body Time Scale")
        else:
            row = column.row(align=True)
            row.label(text="No Rigid Body World: ")
            row.operator("rigidbody.world_add")

    elif sprops.time_scale_mode == 'TIME_SCALE_MODE_SOFT_BODY':
        split = column.split(align=True)
        column_left = split.column(align=True)
        column_right = split.column(align=True)
        column_left.label(text="Soft Body Object:")
        column_right.prop(sprops, "time_scale_object_soft_body", text="")
        
        row = column.row(align=True)
        soft_body_modifier = sprops.get_selected_time_scale_object_soft_body_modifier()
        if soft_body_modifier is not None:
            row.prop(soft_body_modifier.settings, "speed", text="Soft Body Time Scale")
        else:
            if sprops.time_scale_object_soft_body is not None:
                row.label(text="No soft body simulation found on object")
            else:
                row.label(text="No soft body object selected")

    elif sprops.time_scale_mode == 'TIME_SCALE_MODE_CLOTH':
        split = column.split(align=True)
        column_left = split.column(align=True)
        column_right = split.column(align=True)
        column_left.label(text="Cloth Object:")
        column_right.prop(sprops, "time_scale_object_cloth", text="")
        
        row = column.row(align=True)
        cloth_modifier = sprops.get_selected_time_scale_object_cloth_modifier()
        if cloth_modifier is not None:
            row.prop(cloth_modifier.settings, "time_scale", text="Cloth Time Scale")
        else:
            if sprops.time_scale_object_cloth is not None:
                row.label(text="No cloth simulation found on object")
            else:
                row.label(text="No cloth object selected")

    elif sprops.time_scale_mode == 'TIME_SCALE_MODE_FLUID':
        if vcu.is_blender_282():
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            column_left.label(text="Fluid Domain Object:")
            column_right.prop(sprops, "time_scale_object_fluid", text="")
            
            row = column.row(align=True)
            fluid_modifier = sprops.get_selected_time_scale_object_fluid_modifier()
            if fluid_modifier is not None:
                row.prop(fluid_modifier.domain_settings, "time_scale", text="Fluid Time Scale")
            else:
                if sprops.time_scale_object_fluid is not None:
                    row.label(text="No Mantaflow domain found on object")
                else:
                    row.label(text="No Mantaflow domain object selected")
        else:
            column.label(text="Mantaflow fluid simulation time scale mode")
            column.label(text="only supported in Blender 2.82 or later")


class FLIPFLUID_PT_DomainTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Simulation"


    @classmethod
    def poll(cls, context):
        if vcu.get_addon_preferences(context).enable_tabbed_domain_settings:
            return False
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = vcu.get_active_object(context).flip_fluid
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return
        is_simulation_running = dprops.bake.is_simulation_running

        global DRAW_OBJECT_FLIP_TYPE_PROPERTY
        if DRAW_OBJECT_FLIP_TYPE_PROPERTY:
            column = self.layout.column()
            column.enabled = not is_simulation_running
            column.prop(obj_props, "object_type")

        box = self.layout.box()
        draw_bake_operator(self, context, box)
        draw_more_bake_settings(self, context, box)

        if show_documentation:
            column = box.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Simulation and Baking Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Simulation-Settings"
            column.operator(
                "wm.url_open", 
                text="More Bake Settings Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Simulation-Settings#more-bake-settings"
            column.operator(
                "wm.url_open", 
                text="Baking from the command line", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Baking-from-the-Command-Line"

        column = self.layout.column()
        draw_resolution_settings(self, context, column)

        box = self.layout.box()
        draw_time_settings(self, context, box)

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Domain Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Object-Settings"
            column.operator(
                "wm.url_open", 
                text="How large should I make my domain?", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Object-Settings#how-large-should-i-make-my-domain-object"
            column.operator(
                "wm.url_open", 
                text="Simulation baking taking too long!", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Performance-Notes-and-Tips#simulation-optimization-tips"
            column.operator(
                "wm.url_open", 
                text="CPU Usage Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Performance-Notes-and-Tips"
            column.operator(
                "wm.url_open", 
                text="Tutorials and Learning Resources", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Video-Learning-Series"
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypePanel)
