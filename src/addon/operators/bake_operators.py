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

import bpy, os, glob, json, threading

from .. import bake
from ..objects import flip_fluid_geometry_exporter
from .. import export
from ..utils import installation_utils
from ..filesystem import filesystem_protection_layer as fpl
from ..utils import version_compatibility_utils as vcu

_IS_BAKE_OPERATOR_RUNNING = False


def _notify_bake_operator_running():
    global _IS_BAKE_OPERATOR_RUNNING
    _IS_BAKE_OPERATOR_RUNNING = True


def _notify_bake_operator_cancelled():
    global _IS_BAKE_OPERATOR_RUNNING
    _IS_BAKE_OPERATOR_RUNNING = False


def is_bake_operator_running():
    global _IS_BAKE_OPERATOR_RUNNING
    return _IS_BAKE_OPERATOR_RUNNING


def _update_stats(context):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    cache_dir = dprops.cache.get_cache_abspath()
    statsfilepath = os.path.join(cache_dir, dprops.stats.stats_filename)
    if not os.path.isfile(statsfilepath):
        with open(statsfilepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps({}, sort_keys=True, indent=4))

    temp_dir = os.path.join(cache_dir, "temp")
    match_str = "framestats" + "[0-9]"*6 + ".data"
    stat_files = glob.glob(os.path.join(temp_dir, match_str))
    if not stat_files:
        return

    with open(statsfilepath, 'r', encoding='utf-8') as f:
        stats_dict = json.loads(f.read())

    for statpath in stat_files:
        filename = os.path.basename(statpath)
        frameno = int(filename[len("framestats"):-len(".data")])
        with open(statpath, 'r', encoding='utf-8') as frame_stats:
            try:
                frame_stats_dict = json.loads(frame_stats.read())
            except:
                # stats data may not be finished writing which could
                # result in a decode error. Skip this data for now and
                # process the next time stats are updated.
                continue
            stats_dict[str(frameno)] = frame_stats_dict
        fpl.delete_file(statpath, error_ok=True)

    with open(statsfilepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(stats_dict, sort_keys=True, indent=4))

    dprops.stats.is_stats_current = False
    context.scene.flip_fluid_helper.frame_complete_callback()
    dprops.bake.frame_complete_callback()



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
        self.is_console_output_enabled = True
        if dprops is not None:
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


    def _initialize_domain_properties_frame_range(self, context):
        dprops = self._get_domain_properties()
        frame_start, frame_end = dprops.simulation.get_frame_range()
        dprops.simulation.frame_start = frame_start
        dprops.simulation.frame_end = frame_end


    def _initialize_domain(self, context):
        dprops = self._get_domain_properties()
        self._initialize_domain_properties_frame_range(context)
        dprops.mesh_cache.reset_cache_objects()


    def _get_export_filepath(self):
        dprops = self._get_domain_properties()
        return os.path.join(dprops.cache.get_cache_abspath(), 
                            dprops.bake.export_directory_name,
                            dprops.bake.export_filename)


    def _launch_thread(self):
        dprops = self._get_domain_properties()
        savestate_id = dprops.simulation.get_selected_savestate_id()
        cache_directory = dprops.cache.get_cache_abspath()
        dprops.bake.export_filepath = self._get_export_filepath()
        self.data.progress = 0.0
        self.thread = threading.Thread(
                target=bake.bake, 
                args=(dprops.bake.export_filepath, cache_directory, self.data, savestate_id,)
                )
        self.thread.start()


    def _update_stats(self, context):
        _update_stats(context)


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


    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return not dprops.bake.is_simulation_running


    def modal(self, context, event):
        dprops = self._get_domain_properties()

        is_exporting = (not dprops.bake.is_autosave_available or 
                        dprops.simulation.update_settings_on_resume)

        if not self.is_thread_launched and not self.is_export_operator_launched and is_exporting:
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
        if not installation_utils.is_installation_complete():
            self.report({"ERROR"}, 
                         "FLIP Fluids installation incomplete. Restart Blender to complete installation. If you think this is an error, please contact the developers.")
            self.cancel(context)
            return {'CANCELLED'}

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

        cache_directory = dprops.cache.get_cache_abspath()
        if not os.path.exists(cache_directory):
            try:
                os.makedirs(cache_directory)
            except:
                msg = "Unable to create cache directory: <" + cache_directory + ">"
                self.report({"ERROR_INVALID_INPUT"}, msg)
                return {'CANCELLED'}

        dprops.cache.mark_cache_directory_set()
        self._reset_bake(context)
        self._initialize_domain(context)

        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
        _notify_bake_operator_running()

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

        _notify_bake_operator_cancelled()


class BakeFluidSimulationCommandLine(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.bake_fluid_simulation_cmd"
    bl_label = "Bake Fluid Simulation"
    bl_description = "Bake fluid simulation from command line"
    bl_options = {'REGISTER'}


    def __init__(self):
        self.thread = None
        self.mesh_data = {}
        self.data = BakeData()
        self.geometry_exporter = None


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def _reset_bake(self, context):
        dprops = self._get_domain_properties()
        dprops.bake.is_simulation_running = True
        dprops.bake.bake_progress = 0.0
        dprops.bake.num_baked_frames = 0
        dprops.stats.refresh_stats()
        self.data.reset()


    def _initialize_domain_properties_frame_range(self, context):
        dprops = self._get_domain_properties()
        frame_start, frame_end = dprops.simulation.get_frame_range()
        dprops.simulation.frame_start = frame_start
        dprops.simulation.frame_end = frame_end


    def _initialize_domain(self, context):
        dprops = self._get_domain_properties()
        self._initialize_domain_properties_frame_range(context)
        dprops.mesh_cache.reset_cache_objects()


    def _get_export_directory(self):
        dprops = self._get_domain_properties()
        return os.path.join(dprops.cache.get_cache_abspath(), 
                            dprops.bake.export_directory_name)


    def _initialize_geometry_exporter(self, context):
        print("Exporting Simulation Meshes:")
        print("------------------------------------------------------------")

        export_dir = self._get_export_directory()
        self.geometry_exporter = flip_fluid_geometry_exporter.GeometryExportManager(export_dir)
        export.add_objects_to_geometry_exporter(self.geometry_exporter)


    def _get_logfile_name(self, context):
        dprops = self._get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        logs_directory = os.path.join(cache_directory, "logs")

        basename = os.path.basename(bpy.data.filepath)
        basename = os.path.splitext(basename)[0]
        if not basename:
            basename = "untitled"

        filename = basename
        filepath = os.path.join(logs_directory, filename + ".txt")
        if os.path.isfile(filepath):
            for i in range(1, 1000):
                filename = basename + "." + str(i).zfill(3)
                filepath = os.path.join(logs_directory, filename + ".txt")
                if not os.path.isfile(filepath):
                    break;

        return filename + ".txt"


    def _initialize_export_operator(self, context):
        dprops = self._get_domain_properties()
        dprops.bake.is_export_operator_cancelled = False
        dprops.bake.is_export_operator_running = True
        dprops.bake.export_progress = 0.0
        dprops.bake.export_stage = 'STATIC'
        dprops.cache.logfile_name = self._get_logfile_name(context)


    def _get_export_filepath(self):
        dprops = self._get_domain_properties()
        return os.path.join(dprops.cache.get_cache_abspath(), 
                            dprops.bake.export_directory_name,
                            dprops.bake.export_filename)


    def _export_simulation_data_file(self):
        dprops = self._get_domain_properties()
        dprops.bake.export_filepath = self._get_export_filepath()
        dprops.bake.export_success = export.export_simulation_data(
                bpy.context,
                dprops.bake.export_filepath
                )

        if dprops.bake.export_success:
            dprops.bake.is_cache_directory_set = True


    def _export_simulation_data(self, context):
        print("Exporting simulation data...")
        dprops = self._get_domain_properties()

        is_exporting = (not dprops.bake.is_autosave_available or 
                        dprops.simulation.update_settings_on_resume)
        if not is_exporting:
            return

        self._initialize_geometry_exporter(context)
        self._initialize_export_operator(context)

        while True:
            is_finished = self.geometry_exporter.update_export(1.0/15.0)
            dprops.bake.export_progress = self.geometry_exporter.get_export_progress()
            dprops.bake.export_stage = self.geometry_exporter.get_export_stage()
            if is_finished:
                if self.geometry_exporter.is_error():
                    self.report({"ERROR"}, self.geometry_exporter.get_error_message())
                    dprops.bake.is_bake_cancelled = True
                    dprops.bake.is_export_operator_running = False
                    return

                self._export_simulation_data_file()
                dprops.bake.is_export_operator_running = False
                return


    def _update_simulation_stats(self, context):
        _update_stats(context)


    def _run_fluid_simulation(self, context):
        preferences = vcu.get_addon_preferences()

        print("Running fluid simulation...")
        dprops = self._get_domain_properties()
        savestate_id = dprops.simulation.get_selected_savestate_id()
        max_baking_retries = preferences.cmd_bake_max_attempts
        cache_directory = dprops.cache.get_cache_abspath()
        dprops.bake.export_filepath = self._get_export_filepath()
        self.data.progress = 0.0
        self.data.is_console_output_enabled = True
        self._update_simulation_stats(context)
        bake.bake(dprops.bake.export_filepath, cache_directory, self.data, savestate_id, max_baking_retries)
        self._update_simulation_stats(context)


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

        self._reset_bake(context)
        self._initialize_domain(context)
        self._export_simulation_data(context)

        dprops = self._get_domain_properties()
        if dprops.bake.is_bake_cancelled:
            self.cancel(context)
            return {'FINISHED'}

        _notify_bake_operator_running()
        self._run_fluid_simulation(context)
        self.cancel(context)

        return {'FINISHED'}


    def cancel(self, context):
        dprops = self._get_domain_properties()
        if dprops is None:
            return
        dprops.bake.is_simulation_running = False
        dprops.bake.is_bake_cancelled = False
        dprops.bake.is_export_operator_running = False
        dprops.bake.check_autosave()
        _notify_bake_operator_cancelled()


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


    def _clear_cache(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        fpl.clear_cache_directory(cache_directory, 
            clear_export=False, 
            clear_logs=False, 
            remove_directory=False
            )


    def _reset_property_data(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.reset_cache_objects()
        dprops.stats.refresh_stats()
        dprops.stats.reset_time_remaining()
        dprops.stats.reset_stats_values()
        dprops.bake.check_autosave()
        dprops.render.reset_bake()



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
            self._reset_property_data()
            self.report({"INFO"}, "Current cache directory does not exist - skipping cache reset")
            return {'FINISHED'}

        dprops.cache.mark_cache_directory_set()
        self._clear_cache(context)
        self._reset_property_data()

        self.report({"INFO"}, "Successfully reset bake")
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


def register():
    bpy.utils.register_class(BakeFluidSimulation)
    bpy.utils.register_class(BakeFluidSimulationCommandLine)
    bpy.utils.register_class(CancelBakeFluidSimulation)
    bpy.utils.register_class(FlipFluidResetBake)


def unregister():
    bpy.utils.unregister_class(BakeFluidSimulation)
    bpy.utils.unregister_class(BakeFluidSimulationCommandLine)
    bpy.utils.unregister_class(CancelBakeFluidSimulation)
    bpy.utils.unregister_class(FlipFluidResetBake)
