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

import bpy, enum
from mathutils import Vector, Matrix, Quaternion, Euler, Color
from ..pyfluid import TriangleMesh
from ..utils import export_utils
from ..utils import version_compatibility_utils as vcu
from ..utils import cache_utils


###########################################################################
### Geometry Helpers
###########################################################################


def find_fcurve(id_data, path, index=0):
    anim_data = id_data.animation_data
    for fcurve in anim_data.action.fcurves:
        if fcurve.data_path == path and fcurve.array_index == index:
            return fcurve
        

def get_vector3_at_frame(obj, path, frame_id):
    xcurve = find_fcurve(obj, path, 0)
    ycurve = find_fcurve(obj, path, 1)
    zcurve = find_fcurve(obj, path, 2)
    x = xcurve.evaluate(frame_id) if xcurve else getattr(obj, path)[0]
    y = ycurve.evaluate(frame_id) if ycurve else getattr(obj, path)[1]
    z = zcurve.evaluate(frame_id) if zcurve else getattr(obj, path)[2]
    return (x, y, z)


def get_vector4_at_frame(obj, path, frame_id):
    wcurve = find_fcurve(obj, path, 0)
    xcurve = find_fcurve(obj, path, 1)
    ycurve = find_fcurve(obj, path, 2)
    zcurve = find_fcurve(obj, path, 3)
    w = wcurve.evaluate(frame_id) if wcurve else getattr(obj, path)[0]
    x = xcurve.evaluate(frame_id) if xcurve else getattr(obj, path)[1]
    y = ycurve.evaluate(frame_id) if ycurve else getattr(obj, path)[2]
    z = zcurve.evaluate(frame_id) if zcurve else getattr(obj, path)[3]
    return (w, x, y, z)


def get_rotation_mode_at_frame(obj, frame_id):
    mode_curve = find_fcurve(obj, "rotation_mode")
    mode = mode_curve.evaluate(frame_id) if mode_curve else getattr(obj, "rotation_mode")
    return mode


def get_matrix_world_at_frame(obj, frame_id):
    rotation_mode = get_rotation_mode_at_frame(obj, frame_id)
    if rotation_mode == 'AXIS_ANGLE':
        axis_angle = get_vector4_at_frame(obj, "rotation_axis_angle", frame_id)
        angle = axis_angle[0]
        axis = Vector((axis_angle[1], axis_angle[2], axis_angle[3]))
        rotation_matrix = Matrix.Rotation(angle, 4, axis)
    elif rotation_mode == 'QUATERNION':
        rotation_quat = get_vector4_at_frame(obj, "rotation_quaternion", frame_id)
        quaternion = Quaternion(rotation_quat)
        rotation_matrix = quaternion.to_euler().to_matrix().to_4x4()
    else:
        rotation = get_vector3_at_frame(obj, "rotation_euler", frame_id)
        euler_rotation = Euler(rotation, rotation_mode)
        rotation_matrix = euler_rotation.to_matrix().to_4x4()
        
    location = get_vector3_at_frame(obj, "location", frame_id)
    location_matrix = Matrix.Translation(location).to_4x4()
    
    scale = get_vector3_at_frame(obj, "scale", frame_id)
    scale_matrix = Matrix.Identity(4)
    scale_matrix[0][0] = scale[0]
    scale_matrix[1][1] = scale[1]
    scale_matrix[2][2] = scale[2]
    
    return vcu.element_multiply(vcu.element_multiply(location_matrix, rotation_matrix), scale_matrix)


def get_mesh_centroid(obj, apply_transforms=True):
    if apply_transforms:
        tmesh = vcu.object_to_triangle_mesh(obj, obj.matrix_world)
    else:
        tmesh = vcu.object_to_triangle_mesh(obj)
    num_vertices = len(tmesh.vertices) // 3
    if num_vertices == 0:
        return (0.0, 0.0, 0.0)

    xacc, yacc, zacc = 0.0, 0.0, 0.0
    for vidx in range(0, num_vertices):
        xacc += tmesh.vertices[3 * vidx + 0]
        yacc += tmesh.vertices[3 * vidx + 1]
        zacc += tmesh.vertices[3 * vidx + 2]

    xacc /= num_vertices
    yacc /= num_vertices
    zacc /= num_vertices

    return (xacc, yacc, zacc)


# Method adapted from: https://blender.stackexchange.com/a/93441
def curve_to_triangle_mesh(bl_curve_object, apply_transforms=True):
    if not apply_transforms:
        orig_location = Vector(bl_curve_object.location)
        if bl_curve_object.rotation_mode == 'QUATERNION':
            orig_rotation = Vector(bl_curve_object.rotation_quaternion)
            bl_curve_object.rotation_quaternion = (0, 0, 0, 0)
        elif bl_curve_object.rotation_mode == 'AXIS_ANGLE':
            orig_rotation = Vector(bl_curve_object.rotation_axis_angle)
            bl_curve_object.rotation_axis_angle = (0, 0, 0, 0)
        else:
            orig_rotation = Vector(bl_curve_object.rotation_euler)
            bl_curve_object.rotation_euler = (0, 0, 0)
        orig_scale = Vector(bl_curve_object.scale)
        
        bl_curve_object.location = (0, 0, 0)
        bl_curve_object.scale = (1, 1, 1)
    
    instance_obj = bpy.data.objects.new("Empty", None)
    vcu.link_object_to_master_scene(instance_obj)
    
    follow_path_constraint = instance_obj.constraints.new(type='FOLLOW_PATH')
    follow_path_constraint.target = bl_curve_object
    follow_path_constraint.use_fixed_location = True
    
    spline = bl_curve_object.data.splines[0]
    if spline.type == 'BEZIER':
        num_curve_points = len(spline.bezier_points)
    elif spline.type == 'NURBS' or spline.type == 'POLY':
        num_curve_points = len(spline.points)
    
    extra_vertex = 0 if spline.use_cyclic_u else 1
    resolution = spline.resolution_u + 1
    num_vertices = (num_curve_points + extra_vertex) * resolution
    
    instances = [instance_obj]
    for i in range(1, num_vertices + extra_vertex):
        temp_instance = instance_obj.copy()
        temp_instance_constraint = temp_instance.constraints[0]
        temp_instance_constraint.offset_factor = i / num_vertices
        vcu.link_object_to_master_scene(temp_instance)
        instances.append(temp_instance)
        
    vcu.depsgraph_update()
    
    tmesh = TriangleMesh()
    for instance in instances:
        instance_constraint = instance.constraints[0]
        vertex = instance.matrix_world.translation
        tmesh.vertices.append(vertex[0])
        tmesh.vertices.append(vertex[1])
        tmesh.vertices.append(vertex[2])
        instance.constraints.remove(instance_constraint)
        vcu.delete_object(instance)
        
    if not apply_transforms:
        bl_curve_object.location = orig_location
        if bl_curve_object.rotation_mode == 'QUATERNION':
            bl_curve_object.rotation_quaternion = orig_rotation
        elif bl_curve_object.rotation_mode == 'AXIS_ANGLE':
            bl_curve_object.rotation_axis_angle = orig_rotation
        else:
            bl_curve_object.rotation_euler = orig_rotation
        bl_curve_object.scale = orig_scale
        
    return tmesh


###########################################################################
### Geometry Export Object
###########################################################################


class MotionExportType(enum.Enum):
    STATIC    = 0
    KEYFRAMED = 1
    ANIMATED  = 2


class GeometryExportType(enum.Enum):
    MESH     = 0
    VERTICES = 1
    CENTROID = 2
    AXIS     = 3
    CURVE    = 4


class GeometryExportObject():
    def __init__(self, name):
        self.name = name
        self.name_slug = cache_utils.string_to_cache_slug(name)
        self.motion_export_type = self._initialize_motion_export_type()
        self.geometry_export_types = []
        self.skip_reexport = False
        self.disable_changing_topology_warning = False
        self.frame_start = 0
        self.frame_end = 0
        self.exported_frames = {}
        self._object_id = -1


    def get_blender_object(self):
        return bpy.data.objects[self.name]


    def is_static(self):
        return self.motion_export_type == MotionExportType.STATIC


    def is_keyframed(self):
        return self.motion_export_type == MotionExportType.KEYFRAMED


    def is_animated(self):
        return self.motion_export_type == MotionExportType.ANIMATED


    def is_dynamic(self):
        return self.is_keyframed() or self.is_animated()


    def motion_export_type_to_string(self):
        if self.is_static():
            return 'STATIC'
        elif self.is_keyframed():
            return 'KEYFRAMED'
        elif self.is_animated():
            return 'ANIMATED'


    def is_exporting_mesh(self):
        return GeometryExportType.MESH in self.geometry_export_types


    def is_exporting_vertices(self):
        return GeometryExportType.VERTICES in self.geometry_export_types


    def is_exporting_centroid(self):
        return GeometryExportType.CENTROID in self.geometry_export_types


    def is_exporting_axis(self):
        return GeometryExportType.AXIS in self.geometry_export_types


    def is_exporting_curve(self):
        return GeometryExportType.CURVE in self.geometry_export_types


    def set_export_frame_range(self, frame_start, frame_end):
        if self.is_static():
            raise Exception("Frame range must only be set for dynamic export objects.")
        self.frame_start = frame_start
        self.frame_end = frame_end


    def set_motion_export_type(self, motion_export_type_enum):
        if not isinstance(motion_export_type_enum, MotionExportType):
            raise TypeError("Value must MotionExportType enum.")
        self.motion_export_type = motion_export_type_enum


    def add_geometry_export_type(self, geometry_export_type):
        if not isinstance(geometry_export_type, GeometryExportType):
            raise TypeError("Value must GeometryExportType enum.")
        if geometry_export_type not in self.geometry_export_types:
            self.geometry_export_types.append(geometry_export_type)


    def clear_geometry_export_types(self):
        self.geometry_export_types = []


    def merge(self, other_export_object):
        if not isinstance(other_export_object, GeometryExportObject):
            raise TypeError("Value must GeometryExportObject enum.")
        if self.name != other_export_object.name:
            raise Exception("Export objects must have same name to be merged.")

        if other_export_object.motion_export_type.value > self.motion_export_type.value:
            self.set_motion_export_type(other_export_object.motion_export_type)
            self.frame_start = other_export_object.frame_start
            self.frame_end = other_export_object.frame_end

        for geometry_type in other_export_object.geometry_export_types:
            self.add_geometry_export_type(geometry_type)


    def set_object_id(self, database_object_id):
        self._database_object_id = database_object_id


    def get_object_id(self):
        return self._database_object_id


    def exported_frame_exists(self, geometry_export_type, frame_id):
        if not geometry_export_type in self.geometry_export_types:
            return False
        if not geometry_export_type in self.exported_frames:
            return False
        if not frame_id in self.exported_frames[geometry_export_type]:
            return False
        return self.exported_frames[geometry_export_type][frame_id]


    def get_mesh_bobj(self, apply_transforms=True):
        bl_object = self.get_blender_object()
        if apply_transforms:
            tmesh = vcu.object_to_triangle_mesh(bl_object, bl_object.matrix_world)
        else:
            tmesh = vcu.object_to_triangle_mesh(bl_object)
        return tmesh.to_bobj()


    def get_centroid(self, apply_transforms=True):
        bl_object = self.get_blender_object()
        if bl_object.type == 'MESH':
            return get_mesh_centroid(bl_object, apply_transforms=apply_transforms)
        else:
            vect = bl_object.matrix_world.translation
            return (vect.x, vect.y, vect.z)


    def get_centroid_at_frame(self, frame_id):
        bl_object = self.get_blender_object()
        matrix_world = self.get_matrix_world_at_frame(frame_id)
        if bl_object.type == 'MESH':
            c = get_mesh_centroid(bl_object, apply_transforms=False)
            centroid = Vector((c[0], c[1], c[2]))
            vect = vcu.element_multiply(matrix_world, centroid)
        else:
            vect = matrix_world.translation
        return (vect.x, vect.y, vect.z)


    def get_local_axis(self):
        bl_object = self.get_blender_object()
        mat = bl_object.matrix_world
        X = Vector((mat[0][0], mat[1][0], mat[2][0])).normalized()
        Y = Vector((mat[0][1], mat[1][1], mat[2][1])).normalized()
        Z = Vector((mat[0][2], mat[1][2], mat[2][2])).normalized()
        return (X.x, X.y, X.z), (Y.x, Y.y, Y.z), (Z.x, Z.y, Z.z)


    def get_local_axis_at_frame(self, frame_id):
        bl_object = self.get_blender_object()
        mat = self.get_matrix_world_at_frame(frame_id)
        X = Vector((mat[0][0], mat[1][0], mat[2][0])).normalized()
        Y = Vector((mat[0][1], mat[1][1], mat[2][1])).normalized()
        Z = Vector((mat[0][2], mat[1][2], mat[2][2])).normalized()
        return (X.x, X.y, X.z), (Y.x, Y.y, Y.z), (Z.x, Z.y, Z.z)


    def get_matrix_world_at_frame(self, frame_id):
        bl_object = self.get_blender_object()
        return get_matrix_world_at_frame(bl_object, frame_id)


    def get_curve_bobj(self, apply_transforms=True):
        bl_object = self.get_blender_object()
        tmesh = curve_to_triangle_mesh(bl_object, apply_transforms)
        return tmesh.to_bobj()


    def get_bobj_vertex_triangle_count(self, bobj_data):
        tmesh = TriangleMesh.from_bobj(bobj_data)
        return len(tmesh.vertices) // 3, len(tmesh.triangles) // 3


    def _initialize_motion_export_type(self):
        obj = self.get_blender_object()
        props = obj.flip_fluid.get_property_group()
        if hasattr(props, 'export_animated_mesh') and props.export_animated_mesh:
            return MotionExportType.ANIMATED
        if export_utils.is_object_keyframe_animated(obj):
            return MotionExportType.KEYFRAMED
        return MotionExportType.STATIC

