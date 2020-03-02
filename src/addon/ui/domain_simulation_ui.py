# Blender FLIP Fluid Add-on
# Copyright (C) 2019 Ryan L. Guy
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

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_DomainTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Simulation"


    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def draw_bake_operator(self, context, box):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        bakeprops = dprops.bake
        if not bakeprops.is_simulation_running:
            if bakeprops.is_autosave_available:
                frame_str = str(bakeprops.autosave_frame + 1)
                if dprops.simulation.enable_savestates:
                    frame_str = str(int(dprops.simulation.selected_savestate) + 1)

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
            num_frames = dprops.simulation.frame_end - dprops.simulation.frame_start + 1
            frame_progress_string = str(bakeprops.num_baked_frames) + " / " + str(num_frames)
            pct_string = str(round((bakeprops.num_baked_frames / num_frames) * 100, 1)) + "%"
            frames_string = pct_string + "   ( " + frame_progress_string + " )"
            operator_text = "Baking in progress...   " + frames_string

        column = box.column(align=True)
        column.separator()

        if not bakeprops.is_simulation_running and bakeprops.is_autosave_available:
            split = vcu.ui_split(column, factor=0.75, align=True)
            column_left = split.column(align=True)
            column_left.operator("flip_fluid_operators.bake_fluid_simulation", 
                                 text=operator_text)

            column_right = split.column(align=True)
            column_right.alert = True
            column_right.operator("flip_fluid_operators.reset_bake", 
                                  text="Reset")

            if dprops.simulation.enable_savestates:
                if dprops.simulation.get_num_savestate_enums() < 100:
                    column_left.prop(dprops.simulation, "selected_savestate", text="")
                else:
                    row = column_left.row(align=True)
                    row.prop(dprops.simulation, "selected_savestate_int", text="Resume from frame")
                    column_right.label(text=dprops.simulation.selected_savestate_int_label)

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


    def draw_more_bake_settings(self, context, box):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        sprops = dprops.simulation
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        if not show_advanced:
            return

        row = box.row()
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

        flip_props = context.scene.flip_fluid
        objects = (flip_props.get_obstacle_objects() + 
                       flip_props.get_fluid_objects() + 
                       flip_props.get_inflow_objects() + 
                       flip_props.get_outflow_objects())
        animated_objects = [x for x in objects if x.flip_fluid.get_property_group().export_animated_mesh]

        indent_str = 5 * " "

        column = subbox.column()
        column.label(text="Skip animated mesh re-export:")
        if len(animated_objects) == 0:
            column.label(text=indent_str + "No animated meshes found...")
        else:
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            for ob in animated_objects:
                pgroup = ob.flip_fluid.get_property_group()
                column_left.label(text=ob.name, icon="OBJECT_DATA")
                column_right.prop(pgroup, "skip_animated_mesh_reexport", text="skip")

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


    def draw_resolution_settings(self, context, box):
        obj = vcu.get_active_object(context)
        sprops = obj.flip_fluid.domain.simulation
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        column = box.column(align=True)
        column.label(text="Grid Resolution:")
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


    def draw_time_settings(self, context, box):
        obj = vcu.get_active_object(context)
        sprops = obj.flip_fluid.domain.simulation
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

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

        column = box.column()
        column.prop(sprops, "time_scale")

        """
        split = vcu.ui_split(column, factor=0.5)

        if show_advanced:
            column_left = split.column(align=True)
            column_left.prop(sprops, "use_fps")
            column_left = column_left.column(align=True)
            column_left.enabled = sprops.use_fps
            column_left.prop(sprops, "frames_per_second")

            column_right = split.column(align=True)
            column_right.enabled = not sprops.use_fps
            column_right.prop(sprops, "start_time", text="Start")
            column_right.prop(sprops, "end_time", text="End")

            column = box.column(align=True)
            column.prop(sprops, "time_scale")
        else:
            column = box.column(align=False)
            column.prop(sprops, "frames_per_second")
            column.prop(sprops, "time_scale")
        """


    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = vcu.get_active_object(context).flip_fluid

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        box = self.layout.box()
        self.draw_bake_operator(context, box)
        self.draw_more_bake_settings(context, box)

        box = self.layout.box()
        self.draw_resolution_settings(context, box)

        box = self.layout.box()
        self.draw_time_settings(context, box)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypePanel)
