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

import bpy, os, json, csv

from ..objects import flip_fluid_mesh_exporter
from .. import export


class ExportFluidSimulation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.export_fluid_simulation"
    bl_label = "Export Fluid Simulation"
    bl_description = "Export fluid simulation data"
    bl_options = {'REGISTER'}


    def __init__(self):
        self.timer = None
        self.is_executing_timer_event = False
        self.mesh_exporter = None
        self.export_step_time = 1.0 / 30.0
        self.mesh_data = None


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def _initialize_mesh_exporter(self, context):
        simprops = context.scene.flip_fluid
        objects = (simprops.get_fluid_objects() +
                   simprops.get_obstacle_objects() +
                   simprops.get_inflow_objects() + 
                   simprops.get_outflow_objects())
        object_names = [obj.name for obj in objects]

        self.mesh_data = {key: None for key in object_names}
        self.mesh_exporter = flip_fluid_mesh_exporter.MeshExporter(self.mesh_data)


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


    def _initialize_operator(self, context):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(0.01, context.window)

        dprops = self._get_domain_properties()
        dprops.bake.is_export_operator_cancelled = False
        dprops.bake.is_export_operator_running = True
        dprops.bake.export_progress = 0.0
        dprops.bake.export_stage = 'STATIC'
        dprops.cache.logfile_name = self._get_logfile_name(context)


    def _export_simulation_data_file(self):
        dprops = self._get_domain_properties()
        dprops.bake.export_filepath = os.path.join(dprops.cache.get_cache_abspath(), 
                                                   dprops.bake.export_filename)
        dprops.bake.export_success = export.export(
                bpy.context, 
                self.mesh_data, 
                dprops.bake.export_filepath
                )

        if dprops.bake.export_success:
            dprops.bake.is_cache_directory_set = True


    @classmethod
    def poll(cls, context):
        return bpy.context.scene.flip_fluid.is_domain_object_set()


    def modal(self, context, event):
        dprops = self._get_domain_properties()
        if dprops is None:
            self.report({"ERROR_INVALID_INPUT"}, "Export operator requires a domain object")
            self.cancel(context)
            return {'CANCELLED'}

        if dprops.bake.is_export_operator_cancelled:
            self.cancel(context)
            return {'FINISHED'}

        if event.type == 'TIMER' and not self.is_executing_timer_event:
            self.is_executing_timer_event = True

            is_finished = self.mesh_exporter.update_export(self.export_step_time)
            dprops.bake.export_progress = self.mesh_exporter.export_progress
            dprops.bake.export_stage = self.mesh_exporter.export_stage
            if is_finished:
                if self.mesh_exporter.is_error:
                    self.report({"ERROR"}, self.mesh_exporter.error_message)
                    dprops.bake.is_bake_cancelled = True
                    self.cancel(context)
                    return {'FINISHED'}

                self._export_simulation_data_file()
                self.cancel(context)
                return {'FINISHED'}

            try:
                # Depending on window, area may be None
                context.area.tag_redraw()
            except:
                pass
            self.is_executing_timer_event = False

        return {'PASS_THROUGH'}


    def execute(self, context):
        self._initialize_mesh_exporter(context)
        self._initialize_operator(context)
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None

        dprops = self._get_domain_properties()
        if dprops is None:
            return
        dprops.bake.is_export_operator_running = False


class FlipFluidExportStatsCSV(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.export_stats_csv"
    bl_label = "Export CSV"
    bl_description = "Export simulation stats to CSV file format"


    @classmethod
    def poll(cls, context):
        return True


    def format_float(self, n):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops.stats.csv_region_format == 'CSV_REGION_US':
            s = "{:.3f}".format(n)
        else:
            s = "{:.3f}".format(n)
            s = s.replace('.', ',')
        return s


    def export_simulation_stats_to_csv(self, stats_data, filepath):
        max_frame_id = 0
        frame_count = False
        for key in stats_data.keys():
            if key.isdigit():
                max_frame_id = max(stats_data[key]['frame'], max_frame_id)
                frame_count += 1

        if frame_count == 0:
            self.report({"ERROR"}, str(export_csv.error_message))
            return False

        frame_list = [None] * (max_frame_id + 1)
        field_names = [
            'frame_id', 
            'frame_timeline',
            'timestep',
            'substeps',
            'particles_fluid',
            'particles_whitewater',
            'time_mesh_generation',
            'time_velocity_advection',
            'time_fluid_particles',
            'time_pressure_solver',
            'time_whitewater_solver',
            'time_viscosity_solver',
            'time_simulation_objects',
            'time_other',
            'time_total',
            'mesh_surface_enabled',
            'mesh_surface_vertices',
            'mesh_surface_triangles',
            'mesh_surface_bytes',
            'mesh_preview_enabled',
            'mesh_preview_vertices',
            'mesh_preview_triangles',
            'mesh_preview_bytes',
            'mesh_foam_enabled',
            'mesh_foam_vertices',
            'mesh_foam_triangles',
            'mesh_foam_bytes',
            'mesh_bubble_enabled',
            'mesh_bubble_vertices',
            'mesh_bubble_triangles',
            'mesh_bubble_bytes',
            'mesh_spray_enabled',
            'mesh_spray_vertices',
            'mesh_spray_triangles',
            'mesh_spray_bytes',
            'mesh_obstacle_enabled',
            'mesh_obstacle_vertices',
            'mesh_obstacle_triangles',
            'mesh_obstacle_bytes',
            'debug_particles_enabled',
            'debug_particles_vertices',
            'debug_particles_triangles',
            'debug_particles_bytes'
        ]

        for key in stats_data.keys():
            if not key.isdigit():
                continue

            frame_data = stats_data[key]
            frame_id = frame_data['frame']

            time_other = max(frame_data['timing']['total'] - 
                             frame_data['timing']['mesh'] -
                             frame_data['timing']['advection'] -
                             frame_data['timing']['particles'] -
                             frame_data['timing']['pressure'] -
                             frame_data['timing']['diffuse'] -
                             frame_data['timing']['viscosity'] -
                             frame_data['timing']['objects'], 0)

            trueval = 'TRUE'
            falseval = 'FALSE'

            frame_list[frame_id] = {
                'frame_id':                  frame_id,
                'frame_timeline':            int(key),
                'timestep':                  self.format_float(frame_data['delta_time']),
                'substeps':                  frame_data['substeps'],
                'particles_fluid':           frame_data['fluid_particles'],
                'particles_whitewater':      frame_data['diffuse_particles'],
                'time_mesh_generation':      self.format_float(frame_data['timing']['mesh']),
                'time_velocity_advection':   self.format_float(frame_data['timing']['advection']),
                'time_fluid_particles':      self.format_float(frame_data['timing']['particles']),
                'time_pressure_solver':      self.format_float(frame_data['timing']['pressure']),
                'time_whitewater_solver':    self.format_float(frame_data['timing']['diffuse']),
                'time_viscosity_solver':     self.format_float(frame_data['timing']['viscosity']),
                'time_simulation_objects':   self.format_float(frame_data['timing']['objects']),
                'time_other':                self.format_float(time_other),
                'time_total':                self.format_float(frame_data['timing']['total']),
                'mesh_surface_enabled':      trueval if frame_data['surface']['enabled'] else falseval,
                'mesh_surface_vertices':     max(frame_data['surface']['vertices'], 0),
                'mesh_surface_triangles':    max(frame_data['surface']['triangles'], 0),
                'mesh_surface_bytes':        frame_data['surface']['bytes'],
                'mesh_preview_enabled':      trueval if frame_data['preview']['enabled'] else falseval,
                'mesh_preview_vertices':     max(frame_data['preview']['vertices'], 0),
                'mesh_preview_triangles':    max(frame_data['preview']['triangles'], 0),
                'mesh_preview_bytes':        frame_data['preview']['bytes'],
                'mesh_foam_enabled':         trueval if frame_data['foam']['enabled'] else falseval,
                'mesh_foam_vertices':        max(frame_data['foam']['vertices'], 0),
                'mesh_foam_triangles':       max(frame_data['foam']['triangles'], 0),
                'mesh_foam_bytes':           frame_data['foam']['bytes'],
                'mesh_bubble_enabled':       trueval if frame_data['bubble']['enabled'] else falseval,
                'mesh_bubble_vertices':      max(frame_data['bubble']['vertices'], 0),
                'mesh_bubble_triangles':     max(frame_data['bubble']['triangles'], 0),
                'mesh_bubble_bytes':         frame_data['bubble']['bytes'],
                'mesh_spray_enabled':        trueval if frame_data['spray']['enabled'] else falseval,
                'mesh_spray_vertices':       max(frame_data['spray']['vertices'], 0),
                'mesh_spray_triangles':      max(frame_data['spray']['triangles'], 0),
                'mesh_spray_bytes':          frame_data['spray']['bytes'],
                'mesh_obstacle_enabled':     trueval if frame_data['obstacle']['enabled'] else falseval,
                'mesh_obstacle_vertices':    max(frame_data['obstacle']['vertices'], 0),
                'mesh_obstacle_triangles':   max(frame_data['obstacle']['triangles'], 0),
                'mesh_obstacle_bytes':       frame_data['obstacle']['bytes'],
                'debug_particles_enabled':   trueval if frame_data['particles']['enabled'] else falseval,
                'debug_particles_vertices':  max(frame_data['particles']['vertices'], 0),
                'debug_particles_triangles': max(frame_data['particles']['triangles'], 0),
                'debug_particles_bytes':     frame_data['particles']['bytes']
            }

        csv_rows = []
        for d in frame_list:
            if d is not None:
                csv_rows.append(d)

        with open(filepath, 'w', newline='') as csvfile:
            dprops = bpy.context.scene.flip_fluid.get_domain_properties()
            if dprops.stats.csv_region_format == 'CSV_REGION_US':
                delimiter = ','
            else:
                delimiter = ';'
            writer = csv.DictWriter(csvfile, fieldnames=field_names, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(csv_rows)

        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        cache_directory = dprops.cache.get_cache_abspath()
        statsfile = os.path.join(cache_directory, dprops.stats.stats_filename)
        if not os.path.isfile(statsfile):
            self.report({"ERROR"}, "Missing simulation stats data file: " + statsfile)
            return {'CANCELLED'}

        with open(statsfile, 'r') as f:
            statsdata = json.loads(f.read())

        csv_filepath = dprops.stats.csv_save_filepath
        csv_directory = os.path.dirname(csv_filepath)

        try:
            if not os.path.exists(csv_directory):
                os.makedirs(csv_directory)
        except Exception as e:
            self.report({"ERROR"}, "Error creating csv file directory: " + str(e))
            return {'CANCELLED'}

        success = self.export_simulation_stats_to_csv(statsdata, csv_filepath)
        if not success:
            return {'CANCELLED'}

        self.report({"INFO"}, "Successfully exported to CSV: " + csv_filepath)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ExportFluidSimulation)
    bpy.utils.register_class(FlipFluidExportStatsCSV)


def unregister():
    bpy.utils.unregister_class(ExportFluidSimulation)
    bpy.utils.unregister_class(FlipFluidExportStatsCSV)
