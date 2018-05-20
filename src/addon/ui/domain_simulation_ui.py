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


class FlipFluidDomainTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Simulation"


    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def draw_bake_operator(self, context, box):
        dprops = context.scene.objects.active.flip_fluid.domain
        bakeprops = dprops.bake
        if not bakeprops.is_simulation_running:
            if bakeprops.is_autosave_available:
                frame_str = str(bakeprops.autosave_frame + 1)
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
            frames = "( " + str(bakeprops.num_baked_frames) + " / " + str(num_frames) + " )"
            operator_text = "Baking in progress...    " + frames

        column = box.column(align=True)
        column.separator()

        if not bakeprops.is_simulation_running and bakeprops.is_autosave_available:
            split = column.split(percentage = 0.75, align = True)
            column = split.column(align = True)
            column.operator("flip_fluid_operators.bake_fluid_simulation", 
                            text=operator_text)

            column = split.column(align = True)
            column.alert = True
            column.operator("flip_fluid_operators.reset_bake", 
                            text="Reset")
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
                row.label("Estimated Time Remaining:    " + dprops.stats.get_time_remaining_string(context))
            else:
                row.label("Calculating time remaining...")


    def draw_export_settings(self, context, box):
        obj = context.scene.objects.active
        sprops = obj.flip_fluid.domain.simulation

        column = box.column(align=True)
        column.label("Bake Export Settings:")
        row = column.row(align=True)
        row.prop(sprops, "settings_export_mode", expand=True)


    def draw_resolution_settings(self, context, box):
        obj = context.scene.objects.active
        sprops = obj.flip_fluid.domain.simulation

        column = box.column(align=True)
        column.label("Grid Resolution:")
        split = column.split(percentage=0.5, align=True)
        
        column_left = split.column(align=True)
        column_left.enabled = not sprops.lock_cell_size
        column_left.prop(sprops, "resolution")

        column_right = split.column(align=True)
        column_right.prop(sprops, "preview_resolution")

        column = box.column(align=True)
        split = column.split(percentage=0.5)
        column_left = split.column(align=True)
        column_left.prop(sprops, "lock_cell_size")


    def draw_time_settings(self, context, box):
        obj = context.scene.objects.active
        sprops = obj.flip_fluid.domain.simulation

        column = box.column(align=True)
        column.label("Time:")

        split = column.split(percentage=0.5)
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


    def draw(self, context):
        obj = context.scene.objects.active
        obj_props = context.scene.objects.active.flip_fluid

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        box = self.layout.box()
        self.draw_bake_operator(context, box)
        self.draw_export_settings(context, box)

        box = self.layout.box()
        self.draw_resolution_settings(context, box)

        box = self.layout.box()
        self.draw_time_settings(context, box)
    

def register():
    bpy.utils.register_class(FlipFluidDomainTypePanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypePanel)
