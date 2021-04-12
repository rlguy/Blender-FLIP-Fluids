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

import bpy, os, copy
from datetime import datetime

from . import flip_fluid_cache
from .flip_fluid_geometry_export_object import GeometryExportObject, MotionExportType, GeometryExportType
from .flip_fluid_geometry_database import GeometryDatabase
from ..utils import version_compatibility_utils as vcu
from ..utils import cache_utils


class WorkQueueItem():
    def __init__(self):
        self.geometry_export_object = None
        self.geometry_export_type = None
        self.frame = 0
        self.apply_transforms = True


class GeometryExportManager():
    def __init__(self, export_directory):
        self.geometry_export_objects = []

        self._database_filename = "export_data.sqlite3"

        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        self._database_filepath = dprops.cache.get_geometry_database_abspath(export_directory, self._database_filename)
        self._is_linked_geometry_database = dprops.cache.is_linked_geometry_directory()

        self._geometry_database = GeometryDatabase(self._database_filepath, clear_database=False)

        self._geometry_export_objects_dict = {}
        self._is_initialized = False

        self._work_queue = []
        self._static_queue_size = 0
        self._keyframed_queue_size = 0
        self._animated_queue_size = 0
        self._num_static_processed = 0
        self._num_keyframed_processed = 0
        self._num_animated_processed = 0

        self._export_stage_string = ""
        self._export_stage_progress = 0.0
        self._is_error = False
        self._error_message = ""


    def add_geometry_export_object(self, export_object):
        if export_object.name_slug in self._geometry_export_objects_dict:
            existing_object = self._geometry_export_objects_dict[export_object.name_slug]
            existing_object.merge(export_object)
        else:
            self.geometry_export_objects.append(export_object)
            self._geometry_export_objects_dict[export_object.name_slug] = export_object


    def get_geometry_export_object(self, name):
        slug = cache_utils.string_to_cache_slug(name)
        if slug in self._geometry_export_objects_dict:
            return self._geometry_export_objects_dict[slug]
        return None


    def get_geometry_export_objects_by_export_type(self, export_type):
        if isinstance(export_type, MotionExportType):
            return [obj for obj in self.geometry_export_objects if obj.motion_export_type == export_type]
        elif isinstance(export_type, GeometryExportType):
            return [obj for obj in self.geometry_export_objects if export_type in obj.geometry_export_types]
        else:
            raise TypeError("Value must MotionExportType or GeometryExportType enum.")


    def initialize(self):
        if self._is_initialized:
            raise Exception("GeometryExportManager already initialized.")

        for obj in self.geometry_export_objects:
            obj.geometry_export_types.sort(key=lambda x: x.value)

        self._geometry_database.open()
        try:
            self._delete_geometry_export_objects_from_database()
            self._add_geometry_export_objects_to_database()
            self._initialize_geometry_export_object_ids()
            self._clean_unused_objects_from_database()
            self._initialize_frame_ranges()
            self._initialize_work_queues()
            self._geometry_database.commit()
        except Exception as e:
            self._geometry_database.close()
            raise e
        self._geometry_database.close()

        self._is_initialized = True


    def update_export(self, step_time):
        if not self._work_queue:
            return True

        self._geometry_database.open()
        self._geometry_database.begin()

        try:
            start_time = datetime.now()
            while self._work_queue:
                work_item = self._work_queue.pop()
                self._process_work_item(work_item)
                if self._is_error:
                    self._geometry_database.close()
                    return True
                if self._get_elapsed_time(start_time) >= step_time:
                    break

            self._set_export_state(work_item)
        except Exception as e:
            self._geometry_database.close()
            raise e

        self._geometry_database.commit()
        self._geometry_database.close()

        filesize = self._geometry_database.get_filesize()
        num_processed = (self._total_queue_size - len(self._work_queue))
        output_str = "Exporting... " + str(num_processed) + " / " + str(self._total_queue_size) + " objects "
        output_str += "\t(Database size: " + str(filesize) + ")"
        print(output_str)

        return not self._work_queue


    def get_export_progress(self):
        return self._export_stage_progress


    def get_export_stage(self):
        return self._export_stage_string


    def is_error(self):
        return self._is_error


    def get_error_message(self):
        return self._error_message


    def _initialize_work_queues(self):
        static_queue = self._generate_static_work_queue()
        keyframed_queue = self._generate_keyframed_work_queue()
        keyframed_static_basis_queue = self._generate_keyframed_static_basis_work_queue()
        animated_queue = self._generate_animated_work_queue()
        total_queue = animated_queue + keyframed_queue + keyframed_static_basis_queue + static_queue
        
        self._work_queue = total_queue
        self._static_queue_size = len(static_queue + keyframed_static_basis_queue)
        self._keyframed_queue_size = len(keyframed_queue)
        self._animated_queue_size = len(animated_queue)
        self._total_queue_size = len(total_queue)


    def _generate_static_work_queue(self):
        static_objects = self.get_geometry_export_objects_by_export_type(MotionExportType.STATIC)

        work_queue = []
        for obj in static_objects:
            for geotype in obj.geometry_export_types:
                if obj.skip_reexport:
                    export_data_exists = self._geometry_database.static_geometry_exists(obj.get_object_id(), geotype)
                    if export_data_exists:
                        continue

                w = WorkQueueItem()
                w.geometry_export_object = obj
                w.geometry_export_type = geotype
                work_queue.append(w)

        work_queue.reverse()
        return work_queue


    # Keyframed objects also need to export a static version of the geometry to apply
    # transforms upon
    def _generate_keyframed_static_basis_work_queue(self):
        keyframed_objects = self.get_geometry_export_objects_by_export_type(MotionExportType.KEYFRAMED)

        work_queue = []
        for obj in keyframed_objects:
            obj_copy = copy.copy(obj)
            obj_copy.motion_export_type = MotionExportType.STATIC
            for geotype in obj_copy.geometry_export_types:
                if obj_copy.skip_reexport:
                    export_data_exists = self._geometry_database.static_geometry_exists(obj_copy.get_object_id(), geotype)
                    if export_data_exists:
                        continue

                w = WorkQueueItem()
                w.geometry_export_object = obj_copy
                w.geometry_export_type = geotype
                w.apply_transforms = False
                work_queue.append(w)

        work_queue.reverse()
        return work_queue


    def _generate_dynamic_work_queue_for_frame(self, export_objects, frameno):
        work_queue = []
        for obj in export_objects:
            for geotype in obj.geometry_export_types:
                if obj.skip_reexport and obj.exported_frame_exists(geotype, frameno):
                    continue

                w = WorkQueueItem()
                w.geometry_export_object = obj
                w.geometry_export_type = geotype
                w.frame = frameno
                work_queue.append(w)

        return work_queue


    def _get_min_max_frame_range(self, export_object_list):
        min_obj = min(export_object_list, key=lambda x: x.frame_start) 
        max_obj = max(export_object_list, key=lambda x: x.frame_end)
        return min_obj.frame_start, max_obj.frame_end


    def _generate_keyframed_work_queue(self):
        work_queue = []
        keyframed_objects = self.get_geometry_export_objects_by_export_type(MotionExportType.KEYFRAMED)
        if not keyframed_objects:
            return work_queue

        frame_start, frame_end = self._get_min_max_frame_range(keyframed_objects)
        for frameno in range(frame_start, frame_end + 1):
            work_queue += self._generate_dynamic_work_queue_for_frame(keyframed_objects, frameno)

        work_queue.reverse()
        return work_queue


    def _generate_animated_work_queue(self):
        work_queue = []
        animated_objects = self.get_geometry_export_objects_by_export_type(MotionExportType.ANIMATED)
        if not animated_objects:
            return work_queue

        frame_start, frame_end = self._get_min_max_frame_range(animated_objects)
        for frameno in range(frame_start, frame_end + 1):
            work_queue += self._generate_dynamic_work_queue_for_frame(animated_objects, frameno)

        work_queue.reverse()
        return work_queue


    def _get_elapsed_time(self, start_time):
        dt = datetime.now() - start_time
        return dt.days * 86400 + dt.seconds + dt.microseconds / 1000000.0


    def _set_export_state(self, work_item):
        motion_type = work_item.geometry_export_object.motion_export_type
        if motion_type == MotionExportType.STATIC:
            self._export_stage_string = "STATIC"
            self._export_stage_progress = self._num_static_processed / self._static_queue_size
        elif motion_type == MotionExportType.KEYFRAMED:
            self._export_stage_string = "KEYFRAMED"
            self._export_stage_progress = self._num_keyframed_processed / self._keyframed_queue_size
        elif motion_type == MotionExportType.ANIMATED:
            self._export_stage_string = "ANIMATED"
            self._export_stage_progress = self._num_animated_processed / self._animated_queue_size


    def _set_error(self, errmsg):
        self._is_error = True
        self._error_message = errmsg


    ###########################################################################
    ### Database Operations
    ###########################################################################


    def _delete_geometry_export_objects_from_database(self):
        for obj in self.geometry_export_objects:
            if not obj.skip_reexport and self._geometry_database.object_exists(obj):
                self._geometry_database.delete_object_by_slug(obj.name_slug)


    def _add_geometry_export_objects_to_database(self):
        for obj in self.geometry_export_objects:
            if not self._geometry_database.object_exists(obj):
                self._geometry_database.add_object(obj)


    def _initialize_geometry_export_object_ids(self):
        for obj in self.geometry_export_objects:
            obj.set_object_id(self._geometry_database.get_object_id(obj))


    def _clean_unused_objects_from_database(self):
        if self._is_linked_geometry_database:
            return

        all_objects = self._geometry_database.get_all_objects()
        database_slugs = [row[2] for row in all_objects]
        current_slugs = [obj.name_slug for obj in self.geometry_export_objects]
        for slug in database_slugs:
            if slug not in current_slugs:
                self._geometry_database.delete_object_by_slug(slug)


    def _initialize_geometry_export_object_frame_range(self, obj):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        frame_start, frame_end = dprops.simulation.get_frame_range()
        obj.set_export_frame_range(frame_start, frame_end)
        if not obj.skip_reexport:
            return

        ident = obj.get_object_id()
        mtype = obj.motion_export_type
        frame_data_dict = {}
        for geotype in obj.geometry_export_types:
            frame_data_dict[geotype] = {}
            frame_list = self._geometry_database.get_dynamic_geometry_exported_frames(ident, mtype, geotype)

            for frame_id in range(frame_start, frame_end + 1):
                frame_data_dict[geotype][frame_id] = False
            for frame_id in frame_list:
                frame_data_dict[geotype][frame_id] = True

        obj.exported_frames = frame_data_dict


    def _initialize_frame_ranges(self):
        for obj in self.geometry_export_objects:
            if not obj.is_dynamic():
                continue
            self._initialize_geometry_export_object_frame_range(obj)





    ###########################################################################
    ### Process Geometry
    ###########################################################################


    def _update_blender_frame(self, frameno):
        if bpy.context.scene.frame_current == frameno:
            return
        flip_fluid_cache.DISABLE_MESH_CACHE_LOAD = True
        bpy.context.scene.frame_set(frameno)
        flip_fluid_cache.DISABLE_MESH_CACHE_LOAD = False


    def _process_mesh_object(self, work_item):
        motion_type = work_item.geometry_export_object.motion_export_type
        if motion_type == MotionExportType.STATIC:
            object_id = work_item.geometry_export_object.get_object_id()
            bobj_data = work_item.geometry_export_object.get_mesh_bobj(apply_transforms=work_item.apply_transforms)
            self._geometry_database.add_mesh_static(object_id, bobj_data)

        elif motion_type == MotionExportType.KEYFRAMED:
            object_id = work_item.geometry_export_object.get_object_id()
            frame_id = work_item.frame
            matrix_world = work_item.geometry_export_object.get_matrix_world_at_frame(frame_id)
            self._geometry_database.add_mesh_keyframed(object_id, frame_id, matrix_world)

        elif motion_type == MotionExportType.ANIMATED:
            frame_id = work_item.frame
            self._update_blender_frame(frame_id)
            name_slug = work_item.geometry_export_object.name_slug
            disable_warning = work_item.geometry_export_object.disable_changing_topology_warning
            bobj_data = work_item.geometry_export_object.get_mesh_bobj()

            if not disable_warning:
                current_frame_bytes = len(bobj_data)
                previous_frame_bytes = self._geometry_database.get_mesh_animated_blob_length(name_slug, frame_id - 1)
                if previous_frame_bytes is not None and current_frame_bytes != previous_frame_bytes:
                    current_bobj_data = bobj_data
                    previous_bobj_data = previous_frame_bytes = self._geometry_database.get_mesh_animated(name_slug, frame_id - 1)
                    current_vcount, current_tcount = work_item.geometry_export_object.get_bobj_vertex_triangle_count(current_bobj_data)
                    previous_vcount, previous_tcount = work_item.geometry_export_object.get_bobj_vertex_triangle_count(previous_bobj_data)

                    errmsg = ("Warning: unable to export animated mesh '" + work_item.geometry_export_object.name +
                             "'. Animated meshes must have the same number of " +
                             "vertices/triangles for each frame and must not change topology.\n\nFrame " + 
                             str(frame_id - 1) + ": " + str(previous_vcount) + " vertices, " + str(previous_tcount) + " triangles"
                             "\nFrame " + str(frame_id) + ": " + str(current_vcount)) + " vertices, " + str(current_tcount) + " triangles"

                    errmsg += ("\n\nDisable this warning in the Advanced Settings panel. Warning: " +
                              "mesh velocity data will not be computed for meshes with changing topology.")
                    self._set_error(errmsg)

            object_id = work_item.geometry_export_object.get_object_id()
            self._geometry_database.add_mesh_animated(object_id, frame_id, bobj_data)


    def _process_centroid_object(self, work_item):
        motion_type = work_item.geometry_export_object.motion_export_type
        if motion_type == MotionExportType.STATIC:
            object_id = work_item.geometry_export_object.get_object_id()
            centroid = work_item.geometry_export_object.get_centroid(apply_transforms=work_item.apply_transforms)
            self._geometry_database.add_centroid_static(object_id, centroid)

        elif motion_type == MotionExportType.KEYFRAMED:
            object_id = work_item.geometry_export_object.get_object_id()
            frame_id = work_item.frame
            centroid = work_item.geometry_export_object.get_centroid_at_frame(frame_id)
            self._geometry_database.add_centroid_keyframed(object_id, frame_id, centroid)

        elif motion_type == MotionExportType.ANIMATED:
            frame_id = work_item.frame
            self._update_blender_frame(frame_id)
            object_id = work_item.geometry_export_object.get_object_id()
            centroid = work_item.geometry_export_object.get_centroid()
            self._geometry_database.add_centroid_animated(object_id, frame_id, centroid)


    def _process_axis_object(self, work_item):
        motion_type = work_item.geometry_export_object.motion_export_type
        if motion_type == MotionExportType.STATIC:
            object_id = work_item.geometry_export_object.get_object_id()
            local_x, local_y, local_z = work_item.geometry_export_object.get_local_axis()
            self._geometry_database.add_axis_static(object_id, local_x, local_y, local_z)

        elif motion_type == MotionExportType.KEYFRAMED:
            object_id = work_item.geometry_export_object.get_object_id()
            frame_id = work_item.frame
            local_x, local_y, local_z = work_item.geometry_export_object.get_local_axis_at_frame(frame_id)
            self._geometry_database.add_axis_keyframed(object_id, frame_id, local_x, local_y, local_z)

        elif motion_type == MotionExportType.ANIMATED:
            frame_id = work_item.frame
            self._update_blender_frame(frame_id)
            object_id = work_item.geometry_export_object.get_object_id()
            local_x, local_y, local_z = work_item.geometry_export_object.get_local_axis()
            self._geometry_database.add_axis_animated(object_id, frame_id, local_x, local_y, local_z)


    def _process_curve_object(self, work_item):
        motion_type = work_item.geometry_export_object.motion_export_type
        if motion_type == MotionExportType.STATIC:
            object_id = work_item.geometry_export_object.get_object_id()
            bobj_data = work_item.geometry_export_object.get_curve_bobj(apply_transforms=work_item.apply_transforms)
            self._geometry_database.add_curve_static(object_id, bobj_data)

        elif motion_type == MotionExportType.KEYFRAMED:
            object_id = work_item.geometry_export_object.get_object_id()
            frame_id = work_item.frame
            matrix_world = work_item.geometry_export_object.get_matrix_world_at_frame(frame_id)
            self._geometry_database.add_curve_keyframed(object_id, frame_id, matrix_world)

        elif motion_type == MotionExportType.ANIMATED:
            frame_id = work_item.frame
            self._update_blender_frame(frame_id)
            object_id = work_item.geometry_export_object.get_object_id()
            bobj_data = work_item.geometry_export_object.get_curve_bobj()
            self._geometry_database.add_curve_animated(object_id, frame_id, bobj_data)


    def _process_work_item(self, work_item):
        export_type = work_item.geometry_export_type
        if export_type == GeometryExportType.MESH:
            self._process_mesh_object(work_item)
        elif export_type == GeometryExportType.VERTICES:
            pass
        elif export_type == GeometryExportType.CENTROID:
            self._process_centroid_object(work_item)
        elif export_type == GeometryExportType.AXIS:
            self._process_axis_object(work_item)
        elif export_type == GeometryExportType.CURVE:
            self._process_curve_object(work_item)

        motion_type = work_item.geometry_export_object.motion_export_type
        if motion_type == MotionExportType.STATIC:
            self._num_static_processed += 1
        elif motion_type == MotionExportType.KEYFRAMED:
            self._num_keyframed_processed += 1
        elif motion_type == MotionExportType.ANIMATED:
            self._num_animated_processed += 1