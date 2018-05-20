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

import bpy, array
from datetime import datetime
from . import (
        flip_fluid_map,
        flip_fluid_cache,
        flip_fluid_aabb
        )
from ..utils import export_utils as utils
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


    def _initialize_internal_mesh_data(self):
        scene = bpy.context.scene
        num_frames = scene.frame_end - scene.frame_start + 1

        for name in self.mesh_data.keys():
            d = flip_fluid_map.Map({})
            d.name = name
            d.export_type = self._get_mesh_export_type(name)
            d.next_frame = scene.frame_start

            if d.export_type == 'KEYFRAMED':
                obj = bpy.data.objects[name]
                matdata = utils.get_object_world_matrix_data_dict(obj)
                d.world_matrix_data = matdata['data']

            self.internal_mesh_data[name] = d


    def _initialize_mesh_data(self):
        scene = bpy.context.scene
        num_frames = scene.frame_end - scene.frame_start + 1

        for name in self.mesh_data.keys():
            internal_d = self.internal_mesh_data[name]

            d = flip_fluid_map.Map({})
            d.name = name
            if internal_d.export_type == 'STATIC':
                d.num_remaining = 1
                d.num_meshes = 1
                d.data = {'is_animated' : False, 'data' : None}
            else:
                d.num_remaining = num_frames
                d.num_meshes = num_frames
                d.data = {'is_animated' : True, 
                          'data' : [], 'translation_data' : []}
            d.is_export_finished = False

            self.mesh_data[name] = d


    def _initialize_target_mesh_data(self):
        scene = bpy.context.scene
        num_frames = scene.frame_end - scene.frame_start + 1

        object_names = list(self.mesh_data.keys())
        for name in object_names:
            obj = bpy.data.objects[name]
            if not obj.flip_fluid.is_fluid() and not obj.flip_fluid.is_inflow():
                continue

            props = obj.flip_fluid.get_property_group()
            if not props.is_target_valid():
                continue

            target_object = bpy.data.objects[props.target_object]
            target_name = target_object.name

            internal_data = flip_fluid_map.Map({})
            internal_data.name = target_name
            internal_data.export_type = self._get_target_export_type(target_name, props)
            internal_data.next_frame = scene.frame_start
            if internal_data.export_type == 'KEYFRAMED':
                matdata = utils.get_object_world_matrix_data_dict(target_object)
                internal_data.world_matrix_data = matdata['data']

            data = flip_fluid_map.Map({})
            data.name = target_name
            if internal_data.export_type == 'STATIC':
                data.num_remaining = 1
                data.num_meshes = 1
                data.data = {'is_animated' : False, 'data' : None}
            else:
                data.num_remaining = num_frames
                data.num_meshes = num_frames
                data.data = {'is_animated' : True, 
                             'data' : [], 'translation_data' : []}
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
            data.data['data'] = tmesh
            data.num_remaining = 0
            data.is_export_finished = True

            if self._get_elapsed_time(start_time) >= step_time:
                break

        return not objects


    def _get_static_triangle_mesh_data(self, obj):
        if obj.type == 'MESH':
            scene = bpy.context.scene

            # Ignore edge split modifiers. The edge split modifier does
            # not alter vertex positions and may generate a non-manifold mesh 
            # if edges are split
            edge_split_show_render_values = []
            for m in obj.modifiers:
                if m.type == 'EDGE_SPLIT':
                    edge_split_show_render_values.append(m.show_render)
                    m.show_render = False

            triangulation_mod = obj.modifiers.new("flip_triangulate", "TRIANGULATE")
            mesh = obj.to_mesh(scene = scene, 
                               apply_modifiers = True, 
                               settings = 'RENDER')

            triangle_mesh = self._mesh_data_to_triangle_mesh(mesh, obj.matrix_world)

            mesh.user_clear()
            bpy.data.meshes.remove(mesh)
            obj.modifiers.remove(triangulation_mod)

            for m in obj.modifiers:
                if m.type == 'EDGE_SPLIT':
                    m.show_render = edge_split_show_render_values.pop(0)

            return triangle_mesh
        else:
            return self._non_mesh_to_triangle_mesh(obj.matrix_world)


    def _update_keyframed_export(self, step_time):
        start_time = datetime.now()
        scene = bpy.context.scene

        is_finished = False
        while True:
            obj = self._get_next_keyframed_object()
            if not obj:
                is_finished = True
                break

            internal_data = self.internal_mesh_data[obj.name]
            data = self.mesh_data[obj.name]

            frameno = internal_data.next_frame
            meshno = frameno - scene.frame_start
            tmesh = self._get_keyframed_triangle_mesh_data(obj, meshno)
            data.data['data'].append(tmesh)
            data.num_remaining -= 1

            if meshno != 0:
                if meshno == 1:
                    trans_mesh = self._get_translation_data(obj, 0)
                    data.data['translation_data'].append(trans_mesh)
                trans_mesh = self._get_translation_data(obj, meshno)
                data.data['translation_data'].append(trans_mesh)

            internal_data.next_frame += 1

            if data.num_remaining == 0:
                data.is_export_finished = True

            if self._get_elapsed_time(start_time) >= step_time:
                break

        return is_finished


    def _get_keyframed_triangle_mesh_data(self, obj, frameno):
        internal_data = self.internal_mesh_data[obj.name]
        world_matrices = internal_data.world_matrix_data
        matrix_world = world_matrices[frameno]

        if obj.type == 'MESH':
            scene = bpy.context.scene

            triangulation_mod = obj.modifiers.new("flip_triangulate", "TRIANGULATE")
            mesh = obj.to_mesh(scene = scene, 
                               apply_modifiers = True, 
                               settings = 'RENDER')

            triangle_mesh = self._mesh_data_to_triangle_mesh(mesh, matrix_world)

            mesh.user_clear()
            bpy.data.meshes.remove(mesh)
            obj.modifiers.remove(triangulation_mod)

            return triangle_mesh
        else:
            return self._non_mesh_to_triangle_mesh(matrix_world)


    def _update_animated_export(self, step_time):
        start_time = datetime.now()
        scene = bpy.context.scene

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
            data.data['data'].append(tmesh)

            num_verts1 = len(data.data['data'][0].vertices) // 3
            num_verts2 = len(data.data['data'][-1].vertices) // 3
            if num_verts1 != num_verts2:
                errframeno = len(data.data['data'])
                errmsg = ("Error: unable to export animated mesh '" + obj.name +
                         "'. Animated meshes must have the same number of " +
                         "vertices for each frame.\n\nFrame 0: " + str(num_verts1) + 
                         "\nFrame " + str(errframeno) + ": " + str(num_verts2))
                self._set_error(errmsg)
                is_finished = True
                break

            data.num_remaining -= 1

            meshno = frameno - scene.frame_start
            if meshno != 0:
                if meshno == 1:
                    trans_mesh = self._get_translation_data(obj, 0)
                    data.data['translation_data'].append(trans_mesh)
                trans_mesh = self._get_translation_data(obj, meshno)
                data.data['translation_data'].append(trans_mesh)

            internal_data.next_frame += 1

            if data.num_remaining == 0:
                data.is_export_finished = True

            if self._get_elapsed_time(start_time) >= step_time:
                break

        if is_finished:
            scene.frame_set(self.saved_current_frame)

        return is_finished


    def _get_animated_triangle_mesh_data(self, obj):
        if obj.type == 'MESH':
            scene = bpy.context.scene
            triangulation_mod = obj.modifiers.new("flip_triangulate", "TRIANGULATE")
            mesh = obj.to_mesh(scene = scene, 
                               apply_modifiers = True, 
                               settings = 'RENDER')
            triangle_mesh = self._mesh_data_to_triangle_mesh(mesh, obj.matrix_world)

            mesh.user_clear()
            bpy.data.meshes.remove(mesh)
            obj.modifiers.remove(triangulation_mod)

            return triangle_mesh
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


    def _non_mesh_to_triangle_mesh(self, matrix_world):
        location = matrix_world.translation
        tmesh = TriangleMesh()
        tmesh.vertices = array.array('f', [location[0], location[1], location[2]])
        tmesh.triangles = array.array('i', [])
        return tmesh


    def _get_translation_data(self, obj, frameno):
        mesh_data = self.mesh_data[obj.name]
        triangle_meshes = mesh_data.data['data']

        if frameno == 0:
            mesh1 = triangle_meshes[frameno]
            mesh2 = triangle_meshes[frameno + 1]
        else:
            mesh1 = triangle_meshes[frameno - 1]
            mesh2 = triangle_meshes[frameno]

        vert_data = []
        for i in range(len(mesh1.vertices)):
            vert_data.append(mesh2.vertices[i] - mesh1.vertices[i])
        trans_mesh = TriangleMesh()
        trans_mesh.vertices = array.array('f', vert_data)
        trans_mesh.triangles = array.array('i', [])
        
        return trans_mesh


    def _set_error(self, msg):
        self.is_error = True
        self.error_message = msg
