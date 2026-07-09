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

import bpy, bmesh, mathutils
import numpy as np

from . import version_compatibility_utils as vcu


def get_world_vertices(bl_object):
    return [bl_object.matrix_world @ v.co for v in bl_object.data.vertices]

def get_world_vertices_rotated_around_point(bl_object, bl_rotation_matrix, bl_point):
    vertices = get_world_vertices(bl_object)
    vertices = apply_translation_to_vertices(vertices, -bl_point)
    vertices = apply_rotation_to_vertices(vertices, bl_rotation_matrix)
    vertices = apply_translation_to_vertices(vertices, bl_point)
    return vertices

def apply_translation_to_vertices(vertex_list, bl_vector):
    return [v + bl_vector for v in vertex_list]


def apply_rotation_to_vertices(vertex_list, bl_rotation_matrix):
    return [bl_rotation_matrix @ v for v in vertex_list]


def apply_rotation_around_point_to_vertices(vertex_list, bl_rotation_matrix, bl_point):
    vertex_list = apply_translation_to_vertices(vertex_list, -bl_point)
    vertex_list = apply_rotation_to_vertices(vertex_list, bl_rotation_matrix)
    vertex_list = apply_translation_to_vertices(vertex_list, bl_point)
    return vertex_list


def flatten_matrix_column_order(m):
    # Use column order when setting a bpy.props.FloatVectorProperty set to 'MATRIX' subtype
    return [val for col in m.col for val in col]


def flatten_matrix_row_order(m):
    return [val for row in m for val in row]


def get_object_center(bl_object):
    vertices = get_world_vertices(bl_object)
    center = np.mean(vertices, axis=0)
    return mathutils.Vector(center)


def create_bl_cube(name="Cube", scale=(1.0, 1.0, 1.0), link=False):
    h = 0.5
    verts = [
        (-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h),
        (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)
    ]
    verts = [(v[0] * scale[0], v[1] * scale[1], v[2] * scale[2]) for v in verts]
    
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), 
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)
    ]
    
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    bl_cube = bpy.data.objects.new(name, mesh)
    
    if link:
        bpy.context.collection.objects.link(bl_cube)
        
    return bl_cube


def get_face_matrix(bl_object, face_index):
    bl_object.update_from_editmode()
    bm = bmesh.new()
    bm.from_mesh(bl_object.data)
    bm.faces.ensure_lookup_table()
    
    face = bm.faces[face_index]
    
    # Primary Axis
    z_axis = face.normal.copy()
    
    # Secondary Axis - needed to lock rotation about primary axis
    edge_axis = (face.verts[1].co - face.verts[0].co).normalized()
    
    x_axis = edge_axis.cross(z_axis).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    rot_matrix = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed()
    world_rot = bl_object.matrix_world.to_3x3() @ rot_matrix
    
    bm.free()

    return world_rot.to_4x4()


def align_object_rotation_to_target(bl_source_object, bl_target_object, source_face_index=0, target_face_index=0):
    source_matrix = get_face_matrix(bl_source_object, face_index=source_face_index) 
    target_matrix = get_face_matrix(bl_target_object, face_index=target_face_index)
    
    alignment_rotation = target_matrix @ source_matrix.inverted()
    bl_source_object.matrix_world = alignment_rotation @ bl_source_object.matrix_world
    
    bl_source_object.location = (0.0, 0.0, 0.0)
    bl_source_object.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    
    bl_source_object.data.transform(bl_source_object.matrix_world)
    bl_source_object.matrix_world = mathutils.Matrix.Identity(4)


def get_OBB_basis_vectors(bl_OBB):
    # Create a cube and align rotation to OBB
    # This cube will be used to extract basis vectors that match the OBB
    # Cube dimensions must be non-uniform to ensure correct PCA computation for basis vectors
    bl_cube = create_bl_cube(name="_ff_cube", scale=(3.0, 2.0, 1.0))
    align_object_rotation_to_target(bl_cube, bl_OBB)
    
    # Extract initial basis vectors
    vertices = get_world_vertices(bl_cube)
    vcu.delete_object(bl_cube)

    centered_vertices = vertices - np.mean(vertices, axis=0)
    covariance_matrix = np.cov(centered_vertices, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)
    basis = eigenvectors.T
    
    # Match basis to closest standard axes 
    standard_axes = np.eye(3)
    final_basis = np.zeros((3, 3))
    used_indices = set()

    for i in range(3):
        best_dot = -1
        best_idx = -1
        best_sign = 1
        
        for j in range(3):
            if j in used_indices: 
                continue
            
            dot = np.dot(standard_axes[i], basis[j])
            if abs(dot) > best_dot:
                best_dot = abs(dot)
                best_idx = j
                best_sign = np.sign(dot)
        
        final_basis[i] = basis[best_idx] * best_sign
        used_indices.add(best_idx)
        
    # Construct rotation matrix
    basis = final_basis
    b1 = mathutils.Vector(basis[0])
    b2 = mathutils.Vector(basis[1])
    b3 = mathutils.Vector(basis[2])
    
    return b1, b2, b3


def rotation_matrix_to_basis_vectors(m):
    b1 = mathutils.Vector([m[0][0], m[1][0], m[2][0]])
    b2 = mathutils.Vector([m[0][1], m[1][1], m[2][1]])
    b3 = mathutils.Vector([m[0][2], m[1][2], m[2][2]])
    return b1, b2, b3


def basis_vectors_to_rotation_matrix(b1, b2, b3):
    rotation_matrix = mathutils.Matrix(
        [[b1[0], b2[0], b3[0]], 
         [b1[1], b2[1], b3[1]],
         [b1[2], b2[2], b3[2]]]
        ).to_4x4()
    return rotation_matrix


def get_OBB_rotation_matrix(bl_OBB):
    b1, b2, b3 = get_OBB_basis_vectors(bl_OBB)
    bl_rotation_matrix = basis_vectors_to_rotation_matrix(b1, b2, b3)
    return bl_rotation_matrix


def get_OBB_min_vertex(bl_OBB, rotation_matrix=None):
    if rotation_matrix is None:
        rotation_matrix = get_OBB_rotation_matrix(bl_OBB)

    rotation_T = rotation_matrix.transposed()
    
    vertices_original = get_world_vertices(bl_OBB)
    vertices_AABB = apply_rotation_to_vertices(vertices_original, rotation_T)
    
    # Minimum corner of AABB is the vertex with the smallest x+y+z sum
    min_vertex_index = np.argmin(np.sum(vertices_AABB, axis=1))
    
    return vertices_original[min_vertex_index]


def OBB_to_AABB_min_max_vertex(bl_OBB, rotation_matrix=None):
    if rotation_matrix is None:
        rotation_matrix = get_OBB_rotation_matrix(bl_OBB)

    rotation_T = rotation_matrix.transposed()
    
    vertices_original = get_world_vertices(bl_OBB)
    vertices_AABB = apply_rotation_to_vertices(vertices_original, rotation_T)
    vertices_np = np.array(vertices_AABB)
    dimensions = mathutils.Vector(np.max(vertices_np, axis=0) - np.min(vertices_np, axis=0))

    min_vertex = get_OBB_min_vertex(bl_OBB, rotation_matrix=rotation_matrix)
    max_vertex = min_vertex + dimensions
    
    return min_vertex, max_vertex