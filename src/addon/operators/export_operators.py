# Blender FLIP Fluids Add-on
# Copyright (C) 2026 Ryan L. Guy & Dennis Fassbaender
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

import bpy, os, json, csv, math

from ..objects import flip_fluid_geometry_exporter as geometry_exporter
from .. import export


OBJECT_MODIFIERS_IGNORE_LIST = []


def handler_export_pre(context):
    global OBJECT_MODIFIERS_IGNORE_LIST
    OBJECT_MODIFIERS_IGNORE_LIST = []

    ignore_substring = "ff_sim_disable"
    for bl_object in bpy.data.objects:
        for modifier in bl_object.modifiers:
            if not modifier.show_viewport:
                continue

            mod_name = modifier.name
            node_group_name = modifier.node_group.name if modifier.type == 'NODES' else ""
            if (ignore_substring in mod_name.lower()) or (ignore_substring in node_group_name.lower()):
                modifier.show_viewport = False
                OBJECT_MODIFIERS_IGNORE_LIST.append((bl_object.name, mod_name, node_group_name))

    print("\nDisabling Modifiers From Simulation:")
    print("------------------------------------------------------------")
    if OBJECT_MODIFIERS_IGNORE_LIST:
        table_entries = []
        col_width1 = 0
        col_width2 = 0
        col_width3 = 0
        for item in OBJECT_MODIFIERS_IGNORE_LIST:
            object_string = "Object: <" + item[0] + ">"
            modifier_string = "Modifier: <" + item[1] + ">"
            node_group_string = "Node Group: N/A"
            if item[2]:
                node_group_string = "Node Group: <" + item[2] + ">"

            col_width1 = max(col_width1, len(object_string))
            col_width2 = max(col_width2, len(modifier_string))
            col_width3 = max(col_width3, len(node_group_string))

            table_entries.append((object_string, modifier_string, node_group_string))

        col_pad = 4
        col_width1 += col_pad
        col_width2 += col_pad
        col_width3 += col_pad
        for entry in table_entries:
            print(f"{entry[0]:<{col_width1}}{entry[1]:<{col_width2}}{entry[2]:<{col_width3}}")
    else:
        print("No modifiers are disabled from the FLIP Fluids simulation.")
        print("To disable a modifier from the simulation, include the text FF_SIM_DISABLE in the modifier name or node group name.")
    print("------------------------------------------------------------")

def handler_export_post(context):
    global OBJECT_MODIFIERS_IGNORE_LIST

    for item in OBJECT_MODIFIERS_IGNORE_LIST:
        bl_object = bpy.data.objects.get(item[0])
        if bl_object is None:
            continue

        modifier = bl_object.modifiers.get(item[1])
        if modifier is None:
            continue

        modifier.show_viewport = True

    OBJECT_MODIFIERS_IGNORE_LIST = []


class ExportFluidSimulation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.export_fluid_simulation"
    bl_label = "Export Fluid Simulation"
    bl_description = "Export fluid simulation data"
    bl_options = {'REGISTER'}


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer = None
        self.is_executing_timer_event = False
        self.geometry_exporter = None
        self.export_step_time = 1.0 / 15.0
        self.mesh_data = None


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()


    def _initialize_geometry_exporter(self, context):
        print("Exporting Simulation Meshes:")
        print("------------------------------------------------------------")

        export_dir = self._get_export_directory()
        self.geometry_exporter = geometry_exporter.GeometryExportManager(export_dir)
        export.add_objects_to_geometry_exporter(self.geometry_exporter)


    def _get_logfile_name(self, context):
        dprops = self._get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        logs_directory = os.path.join(cache_directory, "logs")

        basename = os.path.basename(bpy.data.filepath)
        basename = os.path.splitext(basename)[0]
        if not basename:
            basename = "untitled"

        # Filesystem may have a limit on path length. Truncate name to some max length
        # to avoid errors in cases where the path could become long
        max_length = 16
        if len(basename) > max_length:
            basename = basename[:max_length]

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
        self.timer = context.window_manager.event_timer_add(0.01, window=context.window)

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


    def _get_export_directory(self):
        dprops = self._get_domain_properties()
        return os.path.join(dprops.cache.get_cache_abspath(), 
                            dprops.bake.export_directory_name)


    def _export_simulation_data_file(self):
        dprops = self._get_domain_properties()
        dprops.bake.export_filepath = self._get_export_filepath()
        dprops.bake.export_success = export.export_simulation_data(
                bpy.context,
                dprops.bake.export_filepath
                )

        if dprops.bake.export_success:
            dprops.bake.is_cache_directory_set = True


    def _update_flip_object_force_reexport_on_bake(self, context):
        sim_objects = context.scene.flip_fluid.get_simulation_objects()
        for obj in sim_objects:
            props = obj.flip_fluid.get_property_group()
            if hasattr(props, "force_reexport_on_next_bake"):
                props.force_reexport_on_next_bake = False


    @classmethod
    def poll(cls, context):
        return bpy.context.scene.flip_fluid.is_domain_object_set()


    def modal(self, context, event):
        dprops = self._get_domain_properties()
        if dprops is None:
            self.report({"ERROR_INVALID_INPUT"}, "Export operator requires a domain object")
            self.cancel(context)
            return {'CANCELLED'}

        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"},
                        "Active scene must contain domain object during export - halting export and baking process. Please do not switch active scenes during export.")
            self.cancel(context)
            return {'CANCELLED'}

        if dprops.bake.is_export_operator_cancelled:
            self.cancel(context)
            return {'FINISHED'}

        if event.type == 'TIMER' and not self.is_executing_timer_event:
            self.is_executing_timer_event = True

            is_finished = self.geometry_exporter.update_export(self.export_step_time)

            dprops.bake.export_progress = self.geometry_exporter.get_export_progress()
            dprops.bake.export_stage = self.geometry_exporter.get_export_stage()
            if is_finished:
                if self.geometry_exporter.is_error():
                    self.report({"ERROR"}, self.geometry_exporter.get_error_message())
                    dprops.bake.is_bake_cancelled = True
                    self.cancel(context)
                    return {'FINISHED'}

                self._export_simulation_data_file()
                if not dprops.bake.export_success:
                    dprops.bake.is_bake_cancelled = True
                    self.cancel(context)
                    return {'FINISHED'}

                self._update_flip_object_force_reexport_on_bake(context)
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
        handler_export_pre(context)
        self._initialize_geometry_exporter(context)
        self._initialize_operator(context)
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None

        handler_export_post(context)

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

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
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

        with open(statsfile, 'r', encoding='utf-8') as f:
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
