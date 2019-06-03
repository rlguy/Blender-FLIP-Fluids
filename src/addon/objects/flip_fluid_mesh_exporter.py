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

import bpy, array
from datetime import datetime
from . import (
        flip_fluid_map,
        flip_fluid_cache,
        flip_fluid_aabb
        )
from ..utils import export_utils as utils
from ..utils import version_compatibility_utils as vcu
from ..pyfluid import TriangleMesh


class MeshExporter():
    def __init__(self, mesh_data_dict):
        self.internal_mesh_data = {}
        self.mesh_data = mesh_data_dict
        self.export_stage = 'STATIC'
        self.export_progress = 0.0
        self.saved_current_frame = bpy.context.scene.frame_current
        self.is_error = False
        self.error_message = ""
        
        self._initialize_internal_mesh_data()
        self._initialize_mesh_data()
        self._initialize_target_mesh_data()
        self._initialize_volume_meshing_mesh_data()


    def _initialize_internal_mesh_data(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        frame_start, frame_end = dprops.simulation.get_frame_range()
        num_frames = frame_end - frame_start + 1

        for name in self.mesh_data.keys():
            d = flip_fluid_map.Map({})
            d.name = name
            d.export_type = self._get_mesh_export_type(name)
            d.next_frame = self.mesh_data[name]['frame_start']
            d.num_verts = -1

            if d.export_type == 'KEYFRAMED':
                obj = bpy.data.objects[name]
                matdata = utils.get_object_world_matrix_data_dict(obj)
                d.world_matrix_data = matdata['data']

            self.internal_mesh_data[name] = d


    def _initialize_mesh_data(self):
        for name in self.mesh_data.keys():
            frame_start, frame_end = self.mesh_data[name]['frame_start'], self.mesh_data[name]['frame_end']
            num_frames = max(frame_end - frame_start + 1, 0)
            internal_d = self.internal_mesh_data[name]

            d = flip_fluid_map.Map({})
            d.name = name
            if internal_d.export_type == 'STATIC':
                d.num_remaining = 1
                d.num_meshes = 1
                d.is_export_finished = False
                d.data = {'mesh_type': internal_d.export_type, 'mesh_data': None, 'frame_data': None, 'matrix_data': None}
            elif internal_d.export_type == 'KEYFRAMED':
                d.num_remaining = 1
                d.num_meshes = 1
                d.is_export_finished = False
                d.data = {'mesh_type': internal_d.export_type, 'mesh_data': None, 'frame_data': None, 'matrix_data': None}
            elif internal_d.export_type == 'ANIMATED':
                d.num_remaining = num_frames
                d.num_meshes = num_frames
                d.is_export_finished = d.num_meshes <= 0
                d.data = {'mesh_type': internal_d.export_type, 'mesh_data': [], 'frame_data': [], 'matrix_data': None}

            self.mesh_data[name] = d


    def _initialize_target_mesh_data(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        frame_start, frame_end = dprops.simulation.get_frame_range()
        num_frames = max(frame_end - frame_start + 1, 0)

        object_names = list(self.mesh_data.keys())
        for name in object_names:
            obj = bpy.data.objects[name]
            if not obj.flip_fluid.is_fluid() and not obj.flip_fluid.is_inflow():
                continue

            props = obj.flip_fluid.get_property_group()
            if not props.is_target_valid():
                continue

            target_object = props.get_target_object()
            target_name = target_object.name

            internal_data = flip_fluid_map.Map({})
            internal_data.name = target_name
            internal_data.export_type = self._get_target_export_type(target_name, props)
            internal_data.next_frame = frame_start
            internal_data.num_verts = -1
            if internal_data.export_type == 'KEYFRAMED':
                matdata = utils.get_object_world_matrix_data_dict(target_object)
                internal_data.world_matrix_data = matdata['data']

            data = flip_fluid_map.Map({})
            data.name = target_name
            if internal_data.export_type == 'STATIC':
                data.num_remaining = 1
                data.num_meshes = 1
                data.data = {'mesh_type': internal_data.export_type, 'mesh_data': None, 'frame_data': None, 'matrix_data': None}
            elif internal_data.export_type == 'KEYFRAMED':
                data.num_remaining = 1
                data.num_meshes = 1
                data.data = {'mesh_type': internal_data.export_type, 'mesh_data': None, 'frame_data': None, 'matrix_data': None}
            elif internal_data.export_type == 'ANIMATED':
                data.num_remaining = num_frames
                data.num_meshes = num_frames
                data.data = {'mesh_type': internal_data.export_type, 'mesh_data': [], 'frame_data': [], 'matrix_data': None}
            data.is_export_finished = False

            if not target_name in self.mesh_data:
                self.mesh_data[target_name] = data
                self.internal_mesh_data[target_name] = internal_data
            else:
                set_internal_data = self.internal_mesh_data[target_name]
                set_rank = self._get_export_type_rank(set_internal_data.export_type)
                target_rank = self._get_export_type_rank(internal_data.export_type)
                if target_rank > set_rank:
                    self.mesh_data[target_name] = data
                    self.internal_mesh_data[target_name] = internal_data


    def _initialize_volume_meshing_mesh_data(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        frame_start, frame_end = dprops.simulation.get_frame_range()
        num_frames = max(frame_end - frame_start + 1, 0)

        if not dprops.surface.is_meshing_volume_object_valid():
            return

        obj = dprops.surface.get_meshing_volume_object()
        if obj is None:
            return

        internal_data = flip_fluid_map.Map({})
        internal_data.name = obj.name
        internal_data.export_type = self._get_meshing_volume_export_type(obj, dprops.surface)
        internal_data.next_frame = frame_start
        internal_data.num_verts = -1
        if internal_data.export_type == 'KEYFRAMED':
            matdata = utils.get_object_world_matrix_data_dict(obj)
            internal_data.world_matrix_data = matdata['data']

        data = flip_fluid_map.Map({})
        data.name = obj.name
        if internal_data.export_type == 'STATIC':
            data.num_remaining = 1
            data.num_meshes = 1
            data.data = {'mesh_type': internal_data.export_type, 'mesh_data': None, 'frame_data': None, 'matrix_data': None}
        elif internal_data.export_type == 'KEYFRAMED':
            data.num_remaining = 1
            data.num_meshes = 1
            data.data = {'mesh_type': internal_data.export_type, 'mesh_data': None, 'frame_data': None, 'matrix_data': None}
        elif internal_data.export_type == 'ANIMATED':
            data.num_remaining = num_frames
            data.num_meshes = num_frames
            data.data = {'mesh_type': internal_data.export_type, 'mesh_data': [], 'frame_data': [], 'matrix_data': None}
        data.is_export_finished = False

        if not obj.name in self.mesh_data:
            self.mesh_data[obj.name] = data
            self.internal_mesh_data[obj.name] = internal_data
        else:
            set_internal_data = self.internal_mesh_data[obj.name]
            set_rank = self._get_export_type_rank(set_internal_data.export_type)
            obj_rank = self._get_export_type_rank(internal_data.export_type)
            if obj_rank > set_rank:
                self.mesh_data[obj.name] = data
                self.internal_mesh_data[obj] = internal_data


    def _get_mesh_export_type(self, obj_name):
        obj = bpy.data.objects[obj_name]
        props = obj.flip_fluid.get_property_group()
        if hasattr(props, 'export_animated_mesh') and props.export_animated_mesh:
            return 'ANIMATED'
        if utils.is_object_keyframe_animated(obj):
            return 'KEYFRAMED'
        return 'STATIC'


    def _get_target_export_type(self, obj_name, props):
        obj = bpy.data.objects[obj_name]
        if hasattr(props, 'export_animated_target') and props.export_animated_target:
            return 'ANIMATED'
        if utils.is_object_keyframe_animated(obj):
            return 'KEYFRAMED'
        return 'STATIC'


    def _get_meshing_volume_export_type(self, obj, surface_props):
        if surface_props.export_animated_meshing_volume_object:
            return 'ANIMATED'
        if utils.is_object_keyframe_animated(obj):
            return 'KEYFRAMED'
        return 'STATIC'


    def _get_export_type_rank(self, export_type):
        if export_type == 'STATIC':
            return 0
        elif export_type == 'KEYFRAMED':
            return 1
        elif export_type == 'ANIMATED':
            return 2


    def _get_elapsed_time(self, start_time):
        dt = datetime.now() - start_time
        return dt.days * 86400 + dt.seconds + dt.microseconds / 1000000.0


    def update_export(self, step_time):
        if self.export_stage == 'STATIC':
            is_finished = self._update_static_export(step_time)
            self.export_progress = self._get_export_stage_progess('STATIC')
            if is_finished:
                self.export_stage = 'KEYFRAMED'
                self.export_progress = 0.0

        elif self.export_stage == 'KEYFRAMED':
            is_finished = self._update_keyframed_export(step_time)
            self.export_progress = self._get_export_stage_progess('KEYFRAMED')
            if is_finished:
                self.export_stage = 'ANIMATED'
                self.export_progress = 0.0

        elif self.export_stage == 'ANIMATED':
            is_finished = self._update_animated_export(step_time)
            self.export_progress = self._get_export_stage_progess('ANIMATED')
            if is_finished:
                self.export_stage = 'FINISHED'
                self.export_progress = 1.0

        elif self.export_stage == 'FINISHED':
            return True

        return False


    def _update_static_export(self, step_time):
        start_time = datetime.now()
        objects = self._get_unfinished_export_objects('STATIC')

        if not objects:
            return True

        while objects:
            obj = objects.pop()
            tmesh = self._get_static_triangle_mesh_data(obj)

            internal_data = self.internal_mesh_data[obj.name]
            internal_data.next_frame += 1

            data = self.mesh_data[obj.name]
            data.data['mesh_data'] = tmesh
            data.num_remaining = 0
            data.is_export_finished = True

            if self._get_elapsed_time(start_time) >= step_time:
                break

        return not objects


    def _get_static_triangle_mesh_data(self, obj):
        if obj.type == 'MESH':
            return vcu.object_to_triangle_mesh(obj, obj.matrix_world)
        else:
            return self._non_mesh_to_triangle_mesh(obj.matrix_world)


    def _update_keyframed_export(self, step_time):
        start_time = datetime.now()
        objects = self._get_unfinished_export_objects('KEYFRAMED')

        if not objects:
            return True

        while objects:
            obj = objects.pop()
            base_tmesh = self._get_keyframed_triangle_mesh_data(obj)
            transform_data = self._get_keyframed_matrix_world_data(obj)

            internal_data = self.internal_mesh_data[obj.name]
            internal_data.next_frame += 1

            data = self.mesh_data[obj.name]
            data.data['mesh_data'] = base_tmesh
            data.data['matrix_data'] = transform_data
            data.num_remaining = 0
            data.is_export_finished = True

            if self._get_elapsed_time(start_time) >= step_time:
                break

        return not objects


    def _get_keyframed_triangle_mesh_data(self, obj):
        if obj.type == 'MESH':
            return vcu.object_to_triangle_mesh(obj)
        else:
            return self._get_vertex_mesh((0, 0, 0))


    def _get_keyframed_matrix_world_data(self, obj):
        internal_data = self.internal_mesh_data[obj.name]
        transform_dict = {}
        for i, m in enumerate(internal_data['world_matrix_data']):
            current_frame = internal_data.next_frame + i
            mdata = [
                m[0][0], m[0][1], m[0][2], m[0][3],
                m[1][0], m[1][1], m[1][2], m[1][3],
                m[2][0], m[2][1], m[2][2], m[2][3],
                m[3][0], m[3][1], m[3][2], m[3][3]
                ]
            transform_dict[current_frame] = mdata

        return transform_dict


    def _update_animated_export(self, step_time):
        start_time = datetime.now()
        scene = bpy.context.scene
        dprops = scene.flip_fluid.get_domain_properties()
        show_topology_warning = not dprops.advanced.disable_changing_topology_warning

        is_finished = False
        while True:
            obj = self._get_next_animated_object()
            if not obj:
                is_finished = True
                break

            internal_data = self.internal_mesh_data[obj.name]
            data = self.mesh_data[obj.name]

            frameno = internal_data.next_frame
            if scene.frame_current != frameno:
                flip_fluid_cache.DISABLE_MESH_CACHE_LOAD = True
                scene.frame_set(frameno)
                flip_fluid_cache.DISABLE_MESH_CACHE_LOAD = False

                if self._get_elapsed_time(start_time) >= step_time:
                    break

            tmesh = self._get_animated_triangle_mesh_data(obj)
            data.data['mesh_data'].append(tmesh)
            data.data['frame_data'].append(internal_data.next_frame)

            if internal_data.num_verts < 0:
                internal_data.num_verts = len(tmesh.vertices) // 3
            else:
                num_verts1 = internal_data.num_verts
                num_verts2 = len(tmesh.vertices) // 3
                if show_topology_warning and (num_verts1 != num_verts2):
                    errframeno = internal_data.next_frame
                    errmsg = ("Warning: unable to export animated mesh '" + obj.name +
                             "'. Animated meshes must have the same number of " +
                             "vertices for each frame and must not change topology.\n\nFrame " + 
                             str(errframeno - 1) + ": " + str(num_verts1) +
                             "\nFrame " + str(errframeno) + ": " + str(num_verts2))

                    # Allowing changing topology does not seem stable enough
                    """
                    errmsg += ("\n\nDisable this warning in the Advanced Settings panel. Warning: " +
                              "mesh velocity data will not be computed for meshes with changing topology.")
                    """

                    self._set_error(errmsg)
                    is_finished = True
                    break

            data.num_remaining -= 1
            internal_data.next_frame += 1

            if data.num_remaining <= 0:
                data.is_export_finished = True

            if self._get_elapsed_time(start_time) >= step_time:
                break

        if is_finished:
            scene.frame_set(self.saved_current_frame)

        return is_finished


    def _get_animated_triangle_mesh_data(self, obj):
        if obj.type == 'MESH':
            return vcu.object_to_triangle_mesh(obj, obj.matrix_world)
        else:
            return self._non_mesh_to_triangle_mesh(obj.matrix_world)


    def _get_unfinished_export_objects(self, export_type):
        objects = []
        for name in self.internal_mesh_data.keys():
            internal_data = self.internal_mesh_data[name]
            data = self.mesh_data[name]
            if internal_data.export_type == export_type and not data.is_export_finished:
                obj = bpy.data.objects[name]
                objects.append(obj)
        return objects


    def _get_next_keyframed_object(self):
        object_names = []
        for name in self.internal_mesh_data.keys():
            internal_data = self.internal_mesh_data[name]
            data = self.mesh_data[name]
            if internal_data.export_type == 'KEYFRAMED' and not data.is_export_finished:
                object_names.append(name)

        if not object_names:
            return None

        min_frame = self.internal_mesh_data[object_names[0]].next_frame
        min_frame_object = object_names[0]
        for name in object_names:
            if self.internal_mesh_data[name].next_frame < min_frame:
                min_frame = self.internal_mesh_data[name].next_frame
                min_frame_object = name

        return bpy.data.objects[min_frame_object]


    def _get_next_animated_object(self):
        object_names = []
        for name in self.internal_mesh_data.keys():
            internal_data = self.internal_mesh_data[name]
            data = self.mesh_data[name]
            if internal_data.export_type == 'ANIMATED' and not data.is_export_finished:
                object_names.append(name)

        if not object_names:
            return None

        min_frame = self.internal_mesh_data[object_names[0]].next_frame
        min_frame_object = object_names[0]
        for name in object_names:
            if self.internal_mesh_data[name].next_frame < min_frame:
                min_frame = self.internal_mesh_data[name].next_frame
                min_frame_object = name

        return bpy.data.objects[min_frame_object]


    def _get_export_stage_progess(self, export_type):
        if export_type == 'ANIMATED':
            dprops = bpy.context.scene.flip_fluid.get_domain_properties()
            frame_start, frame_end = dprops.simulation.get_frame_range()
            frame_current = bpy.context.scene.frame_current
            progress = (frame_current - frame_start + 1) / (frame_end - frame_start + 1)
            return progress

        total_count = 0
        finished_count = 0
        for name in self.internal_mesh_data.keys():
            internal_data = self.internal_mesh_data[name]
            if internal_data.export_type == export_type:
                data = self.mesh_data[name]
                total_count += data.num_meshes
                finished_count += data.num_meshes - data.num_remaining

        if total_count == 0:
            return 1.0
        return finished_count / total_count


    def _mesh_data_to_triangle_mesh(self, mesh_data, matrix_world):
        vertex_components = []
        if vcu.is_blender_28():
            for mv in mesh_data.vertices:
                v = matrix_world @ mv.co
                vertex_components.append(v.x)
                vertex_components.append(v.y)
                vertex_components.append(v.z)
        else:
            for mv in mesh_data.vertices:
                v = matrix_world * mv.co
                vertex_components.append(v.x)
                vertex_components.append(v.y)
                vertex_components.append(v.z)

        
        triangle_indices = []
        for t in mesh_data.polygons:
            for idx in t.vertices:
                triangle_indices.append(idx)
        
        tmesh = TriangleMesh()
        tmesh.vertices = array.array('f', vertex_components)
        tmesh.triangles = array.array('i', triangle_indices)

        return tmesh


    def _keyframed_mesh_data_to_triangle_mesh(self, mesh_data):
        vertex_components = []
        for mv in mesh_data.vertices:
            v = mv.co
            vertex_components.append(v.x)
            vertex_components.append(v.y)
            vertex_components.append(v.z)
        
        triangle_indices = []
        for t in mesh_data.polygons:
            for idx in t.vertices:
                triangle_indices.append(idx)
        
        tmesh = TriangleMesh()
        tmesh.vertices = array.array('f', vertex_components)
        tmesh.triangles = array.array('i', triangle_indices)

        return tmesh


    def _non_mesh_to_triangle_mesh(self, matrix_world):
        location = matrix_world.translation
        tmesh = TriangleMesh()
        tmesh.vertices = array.array('f', [location[0], location[1], location[2]])
        tmesh.triangles = array.array('i', [])
        return tmesh


    def _get_vertex_mesh(self, vertex_location):
        tmesh = TriangleMesh()
        tmesh.vertices = array.array('f', [vertex_location[0], vertex_location[1], vertex_location[2]])
        tmesh.triangles = array.array('i', [])
        return tmesh


    def _set_error(self, msg):
        self.is_error = True
        self.error_message = msg
