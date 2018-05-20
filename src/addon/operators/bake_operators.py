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

import bpy, os, glob, json, threading

from .. import bake


class BakeData(object):
    def __init__(self):
        self.reset()

    def reset(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        self.progress = 0.0
        self.completed_frames = 0
        self.is_finished = False
        self.is_initialized = False
        self.is_cancelled = False
        self.is_safe_to_exit = True
        self.is_console_output_enabled = dprops.debug.display_console_output
        self.error_message = ""


class BakeFluidSimulation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.bake_fluid_simulation"
    bl_label = "Bake Fluid Simulation"
    bl_description = "Run fluid simulation"
    bl_options = {'REGISTER'}


    def __init__(self):
        self.timer = None
        self.thread = None
        self.is_export_operator_launched = False
        self.is_thread_launched = False
        self.is_thread_finished = False
        self.is_updating_status = False
        self.data = BakeData()


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def _reset_bake(self, context):
        dprops = self._get_domain_properties()
        dprops.bake.is_simulation_running = True
        dprops.bake.bake_progress = 0.0
        dprops.bake.num_baked_frames = 0
        dprops.stats.refresh_stats()
        self.data.reset()


    def _delete_cache_file(self, filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass


    def _initialize_domain_properties_frame_range(self, context):
        dprops = self._get_domain_properties()
        dprops.simulation.frame_start = context.scene.frame_start
        dprops.simulation.frame_end = context.scene.frame_end


    def _initialize_domain(self, context):
        dprops = self._get_domain_properties()
        self._initialize_domain_properties_frame_range(context)
        dprops.mesh_cache.reset_cache_objects()


    def _launch_thread(self):
        dprops = self._get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        export_filepath = os.path.join(cache_directory, dprops.bake.export_filename)
        self.data.progress = 0.0
        self.thread = threading.Thread(target = bake.bake, 
                                       args = (export_filepath, cache_directory, self.data,))
        self.thread.start()


    def _update_stats(self, context):
        dprops = self._get_domain_properties()
        cache_dir = dprops.cache.get_cache_abspath()
        statsfilepath = os.path.join(cache_dir, dprops.stats.stats_filename)
        if not os.path.isfile(statsfilepath):
            with open(statsfilepath, 'w') as f:
                f.write(json.dumps({}, sort_keys=True, indent=4))

        temp_dir = os.path.join(cache_dir, "temp")
        match_str = "framestats" + "[0-9]"*6 + ".data"
        stat_files = glob.glob(os.path.join(temp_dir, match_str))
        if not stat_files:
            return

        with open(statsfilepath, 'r') as f:
            stats_dict = json.loads(f.read())

        for statpath in stat_files:
            filename = os.path.basename(statpath)
            frameno = int(filename[len("framestats"):-len(".data")])
            with open(statpath, 'r') as frame_stats:
                try:
                    frame_stats_dict = json.loads(frame_stats.read())
                except:
                    # stats data may not be finished writing which could
                    # result in a decode error. Skip this data for now and
                    # process the next time stats are updated.
                    continue
                stats_dict[str(frameno)] = frame_stats_dict
            self._delete_cache_file(statpath)

        with open(statsfilepath, 'w') as f:
                f.write(json.dumps(stats_dict, sort_keys=True, indent=4))

        dprops.stats.is_stats_current = False
        context.scene.flip_fluid_helper.frame_complete_callback()


    def _update_status(self, context):
        if self.thread and not self.thread.is_alive():
            self.is_thread_finished = True
            self.thread = None

            if self.data.error_message:
                bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message="Error Baking Fluid Simulation",
                    error_description=self.data.error_message,
                    popup_width=400
                    )

        self._update_stats(context)

        dprops = self._get_domain_properties()
        dprops.bake.is_bake_initialized = self.data.is_initialized
        dprops.bake.bake_progress = self.data.progress
        dprops.bake.num_baked_frames = self.data.completed_frames
        dprops.bake.is_safe_to_exit = self.data.is_safe_to_exit
        self.data.is_cancelled = dprops.bake.is_bake_cancelled
        try:
            # Depending on window, area may be None
            context.area.tag_redraw()
        except:
            pass


    def _cancel_bake(self, context):
        if self.is_thread_finished:
            return
        dprops = self._get_domain_properties()
        dprops.bake.is_bake_cancelled = True
        self._update_status(context)


    def _is_export_file_available(self):
        dprops = self._get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        export_filepath = os.path.join(cache_directory, dprops.bake.export_filename)
        return os.path.isfile(export_filepath)


    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def modal(self, context, event):
        dprops = self._get_domain_properties()
        if dprops.simulation.settings_export_mode == 'EXPORT_DEFAULT':
            is_exporting = not dprops.bake.is_autosave_available
        elif dprops.simulation.settings_export_mode == 'EXPORT_SKIP':
            is_exporting = not self._is_export_file_available()
        elif dprops.simulation.settings_export_mode == 'EXPORT_FORCE':
            is_exporting = True

        if not self.is_export_operator_launched and is_exporting:
            bpy.ops.flip_fluid_operators.export_fluid_simulation("INVOKE_DEFAULT")
            self.is_export_operator_launched = True

        if dprops.bake.is_export_operator_running and is_exporting:
            return {'PASS_THROUGH'}

        if not self.is_thread_launched and dprops.bake.is_bake_cancelled:
            self.cancel(context)
            return {'FINISHED'}

        if not self.is_thread_launched:
            self._launch_thread()
            self.is_thread_launched = True

        if event.type == 'TIMER' and not self.is_updating_status:
            self.is_updating_status = True
            self._update_status(context)
            self.is_updating_status = False

        if self.is_thread_finished:
            self.cancel(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}


    def execute(self, context):
        if not context.scene.flip_fluid.is_domain_object_set():
            self.report({"ERROR_INVALID_INPUT"}, 
                         "Fluid simulation requires a domain object")
            self.cancel(context)
            return {'CANCELLED'}

        if context.scene.flip_fluid.get_num_domain_objects() > 1:
            self.report({"ERROR_INVALID_INPUT"}, 
                        "There must be only one domain object")
            self.cancel(context)
            return {'CANCELLED'}

        dprops = self._get_domain_properties()
        if dprops.bake.is_simulation_running:
            self.cancel(context)
            return {'CANCELLED'}

        dprops.cache.mark_cache_directory_set()
        self._reset_bake(context)
        self._initialize_domain(context)

        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(0.1, context.window)

        return {'RUNNING_MODAL'}


    def cancel(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None

        dprops = self._get_domain_properties()
        if dprops is None:
            return

        dprops.bake.is_simulation_running = False
        dprops.bake.is_bake_cancelled = False
        dprops.bake.check_autosave()
        try:
            # Depending on window, area may be None
            context.area.tag_redraw()
        except:
            pass


class CancelBakeFluidSimulation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.cancel_bake_fluid_simulation"
    bl_label = "Cancel Bake Fluid Simulation"
    bl_description = "Stop baking fluid simulation"

    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_bake_cancelled


    def execute(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        dprops.bake.is_bake_cancelled = True
        dprops.bake.is_export_operator_cancelled = True

        return {'FINISHED'}


class FlipFluidResetBake(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.reset_bake"
    bl_label = "Reset Bake"
    bl_description = ("Reset simulation bake to initial state. WARNING: this" + 
                      " operation will delete previously baked simulation data.")


    def _delete_cache_file(self, filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass


    def _delete_cache_directory(self, directory, extension):
        if not os.path.isdir(directory):
            return
        
        for f in os.listdir(directory):
            if f.endswith(extension):
                self._delete_cache_file(os.path.join(directory, f))

        if len(os.listdir(directory)) == 0:
            os.rmdir(directory)


    def _clear_cache(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        cache_dir = dprops.cache.get_cache_abspath()

        statsfilepath = os.path.join(cache_dir, dprops.stats.stats_filename)
        self._delete_cache_file(statsfilepath)

        bakefiles_dir = os.path.join(cache_dir, "bakefiles")
        self._delete_cache_directory(bakefiles_dir, ".bbox")
        self._delete_cache_directory(bakefiles_dir, ".bobj")
        self._delete_cache_directory(bakefiles_dir, ".wwp")
        self._delete_cache_directory(bakefiles_dir, ".fpd")

        temp_dir = os.path.join(cache_dir, "temp")
        self._delete_cache_directory(temp_dir, ".data")

        savestates_dir = os.path.join(cache_dir, "savestates")
        autosave_dir = os.path.join(savestates_dir, "autosave")
        self._delete_cache_directory(autosave_dir, ".state")
        self._delete_cache_directory(autosave_dir, ".data")
        self._delete_cache_directory(savestates_dir, ".state")
        self._delete_cache_directory(savestates_dir, ".data")


    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def execute(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        cache_path = dprops.cache.get_cache_abspath()
        if not os.path.isdir(cache_path):
            self.report({"ERROR"}, "Current cache directory does not exist")
            return {'CANCELLED'}
        dprops.cache.mark_cache_directory_set()

        self._clear_cache(context)
        dprops.mesh_cache.reset_cache_objects()
        
        self.report({"INFO"}, "Successfully reset bake")

        dprops.stats.refresh_stats()
        dprops.stats.reset_time_remaining()
        dprops.bake.check_autosave()
        dprops.render.reset_bake()

        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


def register():
    bpy.utils.register_class(BakeFluidSimulation)
    bpy.utils.register_class(CancelBakeFluidSimulation)
    bpy.utils.register_class(FlipFluidResetBake)


def unregister():
    bpy.utils.unregister_class(BakeFluidSimulation)
    bpy.utils.unregister_class(CancelBakeFluidSimulation)
    bpy.utils.unregister_class(FlipFluidResetBake)
