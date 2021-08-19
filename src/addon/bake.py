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

import sys, os, shutil, json, traceback, math

from .objects import flip_fluid_map
from .objects import flip_fluid_geometry_database
from .operators import bake_operators
from .filesystem import filesystem_protection_layer as fpl

from .pyfluid import (
        pyfluid,
        FluidSimulation,
        TriangleMesh,
        Vector3,
        AABB,
        MeshObject,
        MeshFluidSource,
        ForceFieldPoint,
        ForceFieldSurface,
        ForceFieldVolume,
        ForceFieldCurve
        )

from .utils import cache_utils

FLUIDSIM_OBJECT = None
SIMULATION_DATA = None
CACHE_DIRECTORY = ""
GEOMETRY_DATABASE = None


class LibraryVersionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)


def __set_simulation_object(fluidsim_object):
    global FLUIDSIM_OBJECT
    FLUIDSIM_OBJECT = fluidsim_object


def __get_simulation_object():
    global FLUIDSIM_OBJECT
    return FLUIDSIM_OBJECT


def __set_simulation_data(data):
    global SIMULATION_DATA
    SIMULATION_DATA = data


def __get_simulation_data():
    global SIMULATION_DATA
    return SIMULATION_DATA


def __set_cache_directory(cache_directory):
    global CACHE_DIRECTORY
    CACHE_DIRECTORY = cache_directory


def __get_cache_directory():
    global CACHE_DIRECTORY
    return CACHE_DIRECTORY


def __set_geometry_database(geometry_database):
    global GEOMETRY_DATABASE
    GEOMETRY_DATABASE = geometry_database


def __get_geometry_database():
    global GEOMETRY_DATABASE
    return GEOMETRY_DATABASE


def __get_export_directory():
    return os.path.join(CACHE_DIRECTORY, "export")


def __get_geometry_database_filepath():
    data = __get_simulation_data()
    return data.domain_data.initialize.geometry_database_filepath


def __get_name_slug(object_name):
    return cache_utils.string_to_cache_slug(object_name)


def __is_object_dynamic(object_name):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.is_object_dynamic(name_slug)


def __get_timeline_frame():
    fluidsim = __get_simulation_object()
    data = __get_simulation_data()
    frame_start = data.domain_data.initialize.frame_start
    return fluidsim.get_current_frame() + frame_start


def __get_frame_id():
    fluidsim = __get_simulation_object()
    return fluidsim.get_current_frame()


def __extract_static_mesh(object_name):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    bobj_data = geometry_database.get_mesh_static(name_slug)
    if bobj_data is None:
        msg = "Error extracting mesh data. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    tmesh = TriangleMesh.from_bobj(bobj_data)
    tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    tmesh.scale(scale)

    return tmesh


def __extract_transform_data(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    matrix_coefficients = geometry_database.get_mesh_keyframed_transform(name_slug, frameno)
    if matrix_coefficients is None:
        msg = "Error extracting mesh transforms. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    return matrix_coefficients


def __extract_keyframed_mesh(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    bobj_data = geometry_database.get_mesh_static(name_slug)
    if bobj_data is None:
        msg = "Error extracting mesh data. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    tmesh = TriangleMesh.from_bobj(bobj_data)
    tmesh.apply_transform(__extract_transform_data(object_name, frameno))

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    tmesh.scale(scale)

    return tmesh


def __extract_animated_mesh(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    bobj_data = geometry_database.get_mesh_animated(name_slug, frameno)

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    tmesh = TriangleMesh.from_bobj(bobj_data)
    tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    tmesh.scale(scale)

    return tmesh


def __extract_mesh(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    motion_type = geometry_database.get_object_motion_export_type(name_slug)

    if motion_type == 'STATIC':
        return __extract_static_mesh(object_name)
    elif motion_type == 'KEYFRAMED': 
        return __extract_keyframed_mesh(object_name, frameno)
    elif motion_type == 'ANIMATED':
        return __extract_animated_mesh(object_name, frameno)


def __extract_static_frame_mesh(object_name):
    return __extract_static_mesh(object_name)


def __extract_force_field_mesh(object_name, frame_id=0):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    export_dict = geometry_database.get_object_geometry_export_types(name_slug)
    if export_dict['mesh']:
        return __extract_mesh(object_name, frame_id)
    elif export_dict['centroid']:
        centroid = __extract_centroid(object_name, frame_id)
        tmesh = TriangleMesh()
        tmesh.vertices.extend([centroid[0], centroid[1], centroid[2]])
        return tmesh
    elif export_dict['curve']:
        return __extract_curve_mesh(object_name, frame_id)


def __extract_keyframed_frame_meshes(object_name, frameno):
    mesh_current = __extract_keyframed_mesh(object_name, frameno)
    if frameno - 1 < 0 or not __keyframed_mesh_exists(object_name, frameno - 1):
        mesh_previous = mesh_current
    else:
        mesh_previous = __extract_keyframed_mesh(object_name, frameno - 1)

    if not __keyframed_mesh_exists(object_name, frameno + 1):
        mesh_next = mesh_current
    else:
        mesh_next = __extract_keyframed_mesh(object_name, frameno + 1)
    return mesh_previous, mesh_current, mesh_next


def __extract_animated_frame_meshes(object_name, frameno):
    mesh_current = __extract_animated_mesh(object_name, frameno)
    if frameno - 1 < 0 or not __animated_mesh_exists(object_name, frameno - 1):
        mesh_previous = mesh_current
    else:
        mesh_previous = __extract_animated_mesh(object_name, frameno - 1)

    if not __animated_mesh_exists(object_name, frameno + 1):
        mesh_next = mesh_current
    else:
        mesh_next = __extract_animated_mesh(object_name, frameno + 1)
    return mesh_previous, mesh_current, mesh_next


def __extract_keyframed_frame_centroid_meshes(object_name, frameno):
    mesh_current = __extract_force_field_mesh(object_name, frameno)
    if frameno - 1 < 0 or not __keyframed_centroid_exists(object_name, frameno - 1):
        mesh_previous = mesh_current
    else:
        mesh_previous = __extract_force_field_mesh(object_name, frameno - 1)

    if not __keyframed_centroid_exists(object_name, frameno + 1):
        mesh_next = mesh_current
    else:
        mesh_next = __extract_force_field_mesh(object_name, frameno + 1)
    return mesh_previous, mesh_current, mesh_next


def __extract_animated_frame_centroid_meshes(object_name, frameno):
    mesh_current = __extract_force_field_mesh(object_name, frameno)
    if frameno - 1 < 0 or not __animated_centroid_exists(object_name, frameno - 1):
        mesh_previous = mesh_current
    else:
        mesh_previous = __extract_force_field_mesh(object_name, frameno - 1)

    if not __animated_centroid_exists(object_name, frameno + 1):
        mesh_next = mesh_current
    else:
        mesh_next = __extract_force_field_mesh(object_name, frameno + 1)
    return mesh_previous, mesh_current, mesh_next


def __extract_keyframed_frame_curve_meshes(object_name, frameno):
    mesh_current = __extract_force_field_mesh(object_name, frameno)
    if frameno - 1 < 0 or not __keyframed_curve_exists(object_name, frameno - 1):
        mesh_previous = mesh_current
    else:
        mesh_previous = __extract_force_field_mesh(object_name, frameno - 1)

    if not __keyframed_curve_exists(object_name, frameno + 1):
        mesh_next = mesh_current
    else:
        mesh_next = __extract_force_field_mesh(object_name, frameno + 1)
    return mesh_previous, mesh_current, mesh_next


def __extract_animated_frame_curve_meshes(object_name, frameno):
    mesh_current = __extract_force_field_mesh(object_name, frameno)
    if frameno - 1 < 0 or not __animated_curve_exists(object_name, frameno - 1):
        mesh_previous = mesh_current
    else:
        mesh_previous = __extract_force_field_mesh(object_name, frameno - 1)

    if not __animated_curve_exists(object_name, frameno + 1):
        mesh_next = mesh_current
    else:
        mesh_next = __extract_force_field_mesh(object_name, frameno + 1)
    return mesh_previous, mesh_current, mesh_next


def __extract_dynamic_frame_meshes(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    motion_type = geometry_database.get_object_motion_export_type(name_slug)
    if motion_type == 'KEYFRAMED':
        return __extract_keyframed_frame_meshes(object_name, frameno)
    elif motion_type == 'ANIMATED':
        return __extract_animated_frame_meshes(object_name, frameno)


def __extract_dynamic_force_field_frame_meshes(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    motion_type = geometry_database.get_object_motion_export_type(name_slug)
    export_dict = geometry_database.get_object_geometry_export_types(name_slug)
    if export_dict['mesh']:
        if motion_type == 'KEYFRAMED':
            return __extract_keyframed_frame_meshes(object_name, frameno)
        elif motion_type == 'ANIMATED':
            return __extract_animated_frame_meshes(object_name, frameno)
    elif export_dict['centroid']:
        if motion_type == 'KEYFRAMED':
            return __extract_keyframed_frame_centroid_meshes(object_name, frameno)
        elif motion_type == 'ANIMATED':
            return __extract_animated_frame_centroid_meshes(object_name, frameno)
    elif export_dict['curve']:
        if motion_type == 'KEYFRAMED':
            return __extract_keyframed_frame_curve_meshes(object_name, frameno)
        elif motion_type == 'ANIMATED':
            return __extract_animated_frame_curve_meshes(object_name, frameno)


def __extract_local_axis(object_name, frameno=0):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    motion_type = geometry_database.get_object_motion_export_type(name_slug)
    if motion_type == 'STATIC':
        local_x, local_y, local_z = geometry_database.get_axis_static(name_slug)
    elif motion_type == 'KEYFRAMED':
        local_x, local_y, local_z = geometry_database.get_axis_keyframed(name_slug, frameno)
    elif motion_type == 'ANIMATED':
        local_x, local_y, local_z = geometry_database.get_axis_animated(name_slug, frameno)
    return local_x, local_y, local_z


def __keyframed_mesh_exists(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.mesh_keyframed_exists(name_slug, frameno)


def __animated_mesh_exists(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.mesh_animated_exists(name_slug, frameno)


def __keyframed_centroid_exists(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.centroid_keyframed_exists(name_slug, frameno)


def __animated_centroid_exists(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.centroid_animated_exists(name_slug, frameno)


def __extract_centroid(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    motion_type = geometry_database.get_object_motion_export_type(name_slug)

    if motion_type == 'STATIC':
        centroid = geometry_database.get_centroid_static(name_slug)
    elif motion_type == 'KEYFRAMED': 
        centroid = geometry_database.get_centroid_keyframed(name_slug, frameno)
    elif motion_type == 'ANIMATED':
        centroid = geometry_database.get_centroid_animated(name_slug, frameno)

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    centroid[0] = (centroid[0] - bbox.x) * scale
    centroid[1] = (centroid[1] - bbox.y) * scale
    centroid[2] = (centroid[2] - bbox.z) * scale

    return centroid


def __keyframed_curve_exists(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.curve_keyframed_exists(name_slug, frameno)


def __animated_curve_exists(object_name, frameno):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    return geometry_database.curve_animated_exists(name_slug, frameno)


def __extract_curve_mesh(object_name, frameno=0):
    name_slug = __get_name_slug(object_name)
    geometry_database = __get_geometry_database()
    motion_type = geometry_database.get_object_motion_export_type(name_slug)

    if motion_type == 'STATIC':
        bobj_data = geometry_database.get_curve_static(name_slug)
    elif motion_type == 'KEYFRAMED': 
        bobj_data = geometry_database.get_curve_static(name_slug)
        matrix_coefficients = geometry_database.get_curve_keyframed_transform(name_slug, frameno)
    elif motion_type == 'ANIMATED':
        bobj_data = geometry_database.get_curve_animated(name_slug, frameno)

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    curve_tmesh = TriangleMesh.from_bobj(bobj_data)
    if motion_type == 'KEYFRAMED': 
        curve_tmesh.apply_transform(matrix_coefficients)

    curve_tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    curve_tmesh.scale(scale)

    return curve_tmesh


def __extract_data(data_filepath):
    with open(data_filepath, 'r', encoding='utf-8') as f:
        json_data = json.loads(f.read())
    data = flip_fluid_map.Map(json_data)
    return data


def __set_output_directories(cache_dir):
    cache_directories = [
        os.path.join(cache_dir, "bakefiles"),
        os.path.join(cache_dir, "logs"),
        os.path.join(cache_dir, "savestates"),
        os.path.join(cache_dir, "temp")
    ]

    for d in cache_directories:
        if not os.path.exists(d):
            os.makedirs(d)


def __check_bake_cancelled(bakedata):
    if bakedata.is_cancelled or not bake_operators.is_bake_operator_running():
        bakedata.is_finished = True
        return True
    return False


def __get_parameter_data(parameter, frameno = 0):
    if parameter is None:
        raise IndexError()

    if not hasattr(parameter, 'is_animated'):
        return parameter

    if parameter.is_animated:
        return parameter.data[frameno]
    else:
        return parameter.data


def __get_limit_behaviour_enum(b):
    if b == 'BEHAVIOUR_KILL':
        return 0
    if b == 'BEHAVIOUR_BALLISTIC':
        return 1
    if b == 'BEHAVIOUR_COLLIDE':
        return 2
    return int(b)


def __get_emission_boundary(settings, fluidsim):
    dims = fluidsim.get_simulation_dimensions()
    bounds = AABB(0.0, 0.0, 0.0, dims.x, dims.y, dims.z)

    generate_near_boundary = \
            __get_parameter_data(settings.enable_whitewater_emission_near_boundary)
    if not generate_near_boundary:
        pad_cells = 3.5
        pad = pad_cells * fluidsim.get_cell_size()
        bounds.expand(-2*pad)

    return bounds


def __get_obstacle_meshing_offset(obstacle_meshing_mode):
    if type(obstacle_meshing_mode) == float:
        if obstacle_meshing_mode == 0.0:
            obstacle_meshing_mode = 'MESHING_MODE_INSIDE_SURFACE'
        elif obstacle_meshing_mode == 1.0:
            obstacle_meshing_mode = 'MESHING_MODE_ON_SURFACE'
        elif obstacle_meshing_mode == 2.0:
            obstacle_meshing_mode = 'MESHING_MODE_OUTSIDE_SURFACE'

    if obstacle_meshing_mode == 'MESHING_MODE_INSIDE_SURFACE':
        return 0.25
    elif obstacle_meshing_mode == 'MESHING_MODE_ON_SURFACE':
        return 0.0
    elif obstacle_meshing_mode == 'MESHING_MODE_OUTSIDE_SURFACE':
        return -0.5


def __get_viscosity_value(world_data, frameno):
    base = __get_parameter_data(world_data.viscosity, frameno)
    exp = __get_parameter_data(world_data.viscosity_exponent, frameno)
    return base * (10**(-exp))


def __get_surface_tension_value(world_data, frameno):
    base = __get_parameter_data(world_data.surface_tension, frameno)
    exp = __get_parameter_data(world_data.surface_tension_exponent, frameno)
    return world_data.native_surface_tension_scale * base * (10**(-exp))


def __read_save_state_file_data(file_data_path, start_byte, end_byte):
    with open(file_data_path, 'rb') as f:
        f.seek(start_byte)
        data = f.read(end_byte - start_byte)
    return data


def __write_save_state_file_data(file_data_path, data, is_appending_data=False):
    write_mode = 'wb'
    if is_appending_data:
        write_mode = 'ab'
    with open(file_data_path, write_mode) as f:
        f.write(data)


def __load_save_state_marker_particle_data(fluidsim, save_state_directory, autosave_info, data):
    num_particles = autosave_info['num_marker_particles']
    if num_particles == 0:
        return

    d = save_state_directory
    position_data_file = os.path.join(d, autosave_info['marker_particle_position_filedata'])
    velocity_data_file = os.path.join(d, autosave_info['marker_particle_velocity_filedata'])

    velocity_transfer_method = data.domain_data.advanced.velocity_transfer_method.data
    is_apic_enabled = velocity_transfer_method == 'VELOCITY_TRANSFER_METHOD_APIC'
    load_apic_data = False
    if is_apic_enabled:
        is_apic_data_available = ('marker_particle_affinex_filedata' in autosave_info and
                                  'marker_particle_affiney_filedata' in autosave_info and
                                  'marker_particle_affinez_filedata' in autosave_info)
        is_apic_data_available = (is_apic_data_available and 
                                  autosave_info['marker_particle_affinex_filedata'] and 
                                  autosave_info['marker_particle_affiney_filedata'] and 
                                  autosave_info['marker_particle_affinez_filedata'])
        if is_apic_data_available:
            affinex_data_file = os.path.join(d, autosave_info['marker_particle_affinex_filedata'])
            affiney_data_file = os.path.join(d, autosave_info['marker_particle_affiney_filedata'])
            affinez_data_file = os.path.join(d, autosave_info['marker_particle_affinez_filedata'])
            load_apic_data = True

    is_age_attribute_enabled = data.domain_data.surface.enable_age_attribute.data
    load_age_data = False
    if is_age_attribute_enabled:
        age_path = 'marker_particle_age_filedata'
        is_age_data_available = (age_path in autosave_info) and autosave_info[age_path]
        if is_age_data_available:
            age_data_file = os.path.join(d, autosave_info['marker_particle_age_filedata'])
            load_age_data = True

    is_color_attribute_enabled = data.domain_data.surface.enable_color_attribute.data
    load_color_data = False
    if is_color_attribute_enabled:
        color_path = 'marker_particle_color_filedata'
        is_color_data_available = (color_path in autosave_info) and autosave_info[color_path]
        if is_color_data_available:
            color_data_file = os.path.join(d, autosave_info['marker_particle_color_filedata'])
            load_color_data = True

    is_source_id_attribute_enabled = data.domain_data.surface.enable_source_id_attribute.data
    load_source_id_data = False
    if is_source_id_attribute_enabled:
        source_id_path = 'marker_particle_source_id_filedata'
        is_source_id_data_available = (source_id_path in autosave_info) and autosave_info[source_id_path]
        if is_source_id_data_available:
            source_id_data_file = os.path.join(d, autosave_info['marker_particle_source_id_filedata'])
            load_source_id_data = True

    particles_per_read = 2**21
    bytes_per_vector = 12
    bytes_per_float = 4
    max_vector_byte = bytes_per_vector * num_particles
    max_float_byte = bytes_per_float * num_particles
    num_reads = int((num_particles // particles_per_read) + 1)
    for i in range(num_reads):
        start_vector_byte = i * bytes_per_vector * particles_per_read
        start_float_byte = i * bytes_per_float * particles_per_read
        start_int_byte = start_float_byte
        end_vector_byte = min((i + 1) * bytes_per_vector * particles_per_read, max_vector_byte)
        end_float_byte = min((i + 1) * bytes_per_float * particles_per_read, max_float_byte)
        end_int_byte =end_float_byte
        particle_count = int((end_vector_byte - start_vector_byte) // bytes_per_vector)

        position_data = __read_save_state_file_data(position_data_file, start_vector_byte, end_vector_byte)
        velocity_data = __read_save_state_file_data(velocity_data_file, start_vector_byte, end_vector_byte)
        fluidsim.load_marker_particle_data(particle_count, position_data, velocity_data)

        if load_apic_data:
            affinex_data = __read_save_state_file_data(affinex_data_file, start_vector_byte, end_vector_byte)
            affiney_data = __read_save_state_file_data(affiney_data_file, start_vector_byte, end_vector_byte)
            affinez_data = __read_save_state_file_data(affinez_data_file, start_vector_byte, end_vector_byte)
            fluidsim.load_marker_particle_affine_data(particle_count, affinex_data, affiney_data, affinez_data)

        if load_age_data:
            age_data = __read_save_state_file_data(age_data_file, start_float_byte, end_float_byte)
            fluidsim.load_marker_particle_age_data(particle_count, age_data)

        if load_color_data:
            color_data = __read_save_state_file_data(color_data_file, start_vector_byte, end_vector_byte)
            fluidsim.load_marker_particle_color_data(particle_count, color_data)

        if load_source_id_data:
            source_id_data = __read_save_state_file_data(source_id_data_file, start_int_byte, end_int_byte)
            fluidsim.load_marker_particle_source_id_data(particle_count, source_id_data)


def __load_save_state_diffuse_particle_data(fluidsim, save_state_directory, autosave_info):
    num_particles = autosave_info['num_diffuse_particles']
    if num_particles == 0:
        return

    d = save_state_directory
    position_data_file = os.path.join(d, autosave_info['diffuse_particle_position_filedata'])
    velocity_data_file = os.path.join(d, autosave_info['diffuse_particle_velocity_filedata'])
    lifetime_data_file = os.path.join(d, autosave_info['diffuse_particle_lifetime_filedata'])
    type_data_file = os.path.join(d, autosave_info['diffuse_particle_type_filedata'])
    id_data_file = os.path.join(d, autosave_info['diffuse_particle_id_filedata'])


    particles_per_read = 2**21
    bytes_per_vector = 12
    bytes_per_lifetime = 4
    bytes_per_type = 1
    bytes_per_id = 1
    max_byte_vector = bytes_per_vector * num_particles
    max_byte_lifetime = bytes_per_lifetime * num_particles
    max_byte_type = bytes_per_type * num_particles
    max_byte_id = bytes_per_id * num_particles
    num_reads = int((num_particles // particles_per_read) + 1)
    for i in range(num_reads):
        start_byte = i * bytes_per_vector * particles_per_read
        end_byte = min((i + 1) * bytes_per_vector * particles_per_read, max_byte_vector)
        particle_count = int((end_byte - start_byte) // bytes_per_vector)

        position_data = __read_save_state_file_data(position_data_file, start_byte, end_byte)
        velocity_data = __read_save_state_file_data(velocity_data_file, start_byte, end_byte)

        start_byte = i * bytes_per_lifetime * particles_per_read
        end_byte = min((i + 1) * bytes_per_lifetime * particles_per_read, max_byte_lifetime)
        lifetime_data = __read_save_state_file_data(lifetime_data_file, start_byte, end_byte)

        start_byte = i * bytes_per_type * particles_per_read
        end_byte = min((i + 1) * bytes_per_type * particles_per_read, max_byte_type)
        type_data = __read_save_state_file_data(type_data_file, start_byte, end_byte)

        start_byte = i * bytes_per_id * particles_per_read
        end_byte = min((i + 1) * bytes_per_id * particles_per_read, max_byte_id)
        id_data = __read_save_state_file_data(id_data_file, start_byte, end_byte)

        fluidsim.load_diffuse_particle_data(particle_count, position_data, velocity_data,
                                            lifetime_data, type_data, id_data)


def __load_save_state_simulator_data(fluidsim, autosave_info):
    next_frame = autosave_info["frame_id"] + 1
    fluidsim.set_current_frame(next_frame)


def __delete_outdated_savestates(cache_directory, savestate_id):
    savestate_directory = os.path.join(cache_directory, "savestates")
    subdirs = [d for d in os.listdir(savestate_directory) if os.path.isdir(os.path.join(savestate_directory, d)) ]
    if "autosave" in subdirs:
        subdirs.remove("autosave")

    extensions = [".state", ".data"]
    for d in subdirs:
        try: 
            savestate_number = int(d[-6:])
            if savestate_number < 0:
                continue
        except ValueError:
            continue

        if savestate_number > savestate_id:
            path = os.path.join(savestate_directory, d)
            try:
                fpl.delete_files_in_directory(path, extensions, remove_directory=True)
            except:
                print("Error: unable to delete directory <" + path + "> (skipping)")


def __delete_outdated_meshes(cache_directory, savestate_id):
    bakefiles_directory = os.path.join(cache_directory, "bakefiles")
    files = os.listdir(bakefiles_directory)
    for f in files:
        filename = f.split(".")[0]
        filenum = int(filename[-6:])
        if filenum > savestate_id:
            path = os.path.join(bakefiles_directory, f)
            try:
                fpl.delete_file(path)
            except:
                print("Error: unable to delete file <" + path + "> (skipping)")

    stats_filepath = os.path.join(cache_directory, "flipstats.data")
    with open(stats_filepath, 'r', encoding='utf-8') as f:
        stats_info = json.loads(f.read())

    for key in stats_info.copy().keys():
        if int(key) > savestate_id:
            del stats_info[key]

    stats_json = json.dumps(stats_info, sort_keys=True, indent=4)
    with open(stats_filepath, 'w', encoding='utf-8') as f:
        f.write(stats_json)


def __load_save_state_data(fluidsim, data, cache_directory, savestate_id):
    if savestate_id is None:
        return

    savestate_directory = os.path.join(cache_directory, "savestates")
    savestate_name = "autosave" + str(savestate_id).zfill(6)
    autosave_directory = os.path.join(savestate_directory, savestate_name)
    if not os.path.isdir(autosave_directory):
        autosave_directory = os.path.join(savestate_directory, "autosave")

    if not os.path.isdir(autosave_directory):
        return
    
    autosave_info_file = os.path.join(autosave_directory, "autosave.state")
    if not os.path.isfile(autosave_info_file):
        return

    with open(autosave_info_file, 'r', encoding='utf-8') as f:
        autosave_info = json.loads(f.read())

    __load_save_state_marker_particle_data(fluidsim, autosave_directory, autosave_info, data)
    __load_save_state_diffuse_particle_data(fluidsim, autosave_directory, autosave_info)
    __load_save_state_simulator_data(fluidsim, autosave_info)

    init_data = data.domain_data.initialize
    if init_data.delete_outdated_savestates:
        __delete_outdated_savestates(cache_directory, savestate_id)
    if init_data.delete_outdated_meshes:
        __delete_outdated_meshes(cache_directory, savestate_id)


def __initialize_fluid_simulation_settings(fluidsim, data):
    dprops = data.domain_data
    frameno = fluidsim.get_current_frame()

    # Domain Settings

    fluidsim.enable_preview_mesh_output = dprops.initialize.preview_dx
    if dprops.initialize.upscale_simulation:
        save_isize = dprops.initialize.savestate_isize
        save_jsize = dprops.initialize.savestate_jsize
        save_ksize = dprops.initialize.savestate_ksize
        save_dx = dprops.initialize.savestate_dx
        fluidsim.upscale_on_initialization(save_isize, save_jsize, save_ksize, save_dx)

    bbox = dprops.initialize.bbox
    fluidsim.set_domain_offset(bbox.x, bbox.y, bbox.z)
    fluidsim.set_domain_scale(1.0 / dprops.initialize.scale)

    # Whitewater Simulation Settings

    whitewater = dprops.whitewater
    is_whitewater_enabled = __get_parameter_data(whitewater.enable_whitewater_simulation, frameno)
    fluidsim.enable_diffuse_material_output = is_whitewater_enabled

    if is_whitewater_enabled:
        is_foam_enabled = __get_parameter_data(whitewater.enable_foam, frameno)
        is_bubbles_enabled = __get_parameter_data(whitewater.enable_bubbles, frameno)
        is_spray_enabled = __get_parameter_data(whitewater.enable_spray, frameno)
        is_dust_enabled = __get_parameter_data(whitewater.enable_dust, frameno)
        is_dust_boundary_emission_enabled = __get_parameter_data(whitewater.enable_dust_emission_near_boundary, frameno)
        fluidsim.enable_diffuse_foam = is_foam_enabled
        fluidsim.enable_diffuse_bubbles = is_bubbles_enabled
        fluidsim.enable_diffuse_spray = is_spray_enabled
        fluidsim.enable_diffuse_dust = is_dust_enabled
        fluidsim.enable_boundary_diffuse_dust_emission = is_dust_boundary_emission_enabled

        fluidsim.enable_whitewater_motion_blur = \
            __get_parameter_data(whitewater.generate_whitewater_motion_blur_data, frameno)

        is_generating_whitewater = __get_parameter_data(whitewater.enable_whitewater_emission, frameno)
        fluidsim.enable_diffuse_particle_emission = is_generating_whitewater

        emitter_pct = __get_parameter_data(whitewater.whitewater_emitter_generation_rate, frameno)
        fluidsim.diffuse_emitter_generation_rate = emitter_pct / 100

        wavecrest_rate = __get_parameter_data(whitewater.wavecrest_emission_rate, frameno)
        turbulence_rate = __get_parameter_data(whitewater.turbulence_emission_rate, frameno)
        dust_rate = __get_parameter_data(whitewater.dust_emission_rate, frameno)
        fluidsim.diffuse_particle_wavecrest_emission_rate = wavecrest_rate
        fluidsim.diffuse_particle_turbulence_emission_rate = turbulence_rate
        fluidsim.diffuse_particle_dust_emission_rate = dust_rate

        spray_emission_speed = __get_parameter_data(whitewater.spray_emission_speed, frameno)
        fluidsim.diffuse_spray_emission_speed = spray_emission_speed

        min_speed, max_speed = __get_parameter_data(whitewater.min_max_whitewater_energy_speed, frameno)
        fluidsim.min_diffuse_emitter_energy = 0.5 * min_speed * min_speed
        fluidsim.max_diffuse_emitter_energy = 0.5 * max_speed * max_speed

        mink, maxk = __get_parameter_data(whitewater.min_max_whitewater_wavecrest_curvature, frameno)
        fluidsim.min_diffuse_wavecrest_curvature = mink
        fluidsim.max_diffuse_wavecrest_curvature = maxk

        mint, maxt = __get_parameter_data(whitewater.min_max_whitewater_turbulence, frameno)
        fluidsim.min_diffuse_turbulence = mint
        fluidsim.max_diffuse_turbulence = maxt

        max_particles = __get_parameter_data(whitewater.max_whitewater_particles, frameno)
        fluidsim.max_num_diffuse_particles = int(max_particles * 1e6)

        bbox = __get_emission_boundary(whitewater, fluidsim)
        fluidsim.diffuse_emitter_generation_bounds = bbox

        min_lifespan, max_lifespan = __get_parameter_data(whitewater.min_max_whitewater_lifespan, frameno)
        lifespan_variance = __get_parameter_data(whitewater.whitewater_lifespan_variance, frameno)
        fluidsim.min_diffuse_particle_lifetime = min_lifespan
        fluidsim.max_diffuse_particle_lifetime = max_lifespan
        fluidsim.diffuse_particle_lifetime_variance = lifespan_variance

        foam_modifier = __get_parameter_data(whitewater.foam_lifespan_modifier, frameno)
        bubble_modifier = __get_parameter_data(whitewater.bubble_lifespan_modifier, frameno)
        spray_modifier = __get_parameter_data(whitewater.spray_lifespan_modifier, frameno)
        dust_modifier = __get_parameter_data(whitewater.dust_lifespan_modifier, frameno)
        fluidsim.foam_particle_lifetime_modifier = 1.0 / max(foam_modifier, 1e-6)
        fluidsim.bubble_particle_lifetime_modifier = 1.0 / max(bubble_modifier, 1e-6)
        fluidsim.spray_particle_lifetime_modifier = 1.0 / max(spray_modifier, 1e-6)
        fluidsim.dust_particle_lifetime_modifier = 1.0 / max(dust_modifier, 1e-6)

        foam_behaviour = __get_parameter_data(whitewater.foam_boundary_behaviour, frameno)
        bubble_behaviour = __get_parameter_data(whitewater.bubble_boundary_behaviour, frameno)
        spray_behaviour = __get_parameter_data(whitewater.spray_boundary_behaviour, frameno)
        dust_behaviour = __get_parameter_data(whitewater.bubble_boundary_behaviour, frameno) # Same as bubble for now
        foam_behaviour = __get_limit_behaviour_enum(foam_behaviour)
        bubble_behaviour = __get_limit_behaviour_enum(bubble_behaviour)
        spray_behaviour = __get_limit_behaviour_enum(spray_behaviour)
        dust_behaviour = __get_limit_behaviour_enum(dust_behaviour)
        fluidsim.diffuse_foam_limit_behaviour = foam_behaviour
        fluidsim.diffuse_bubble_limit_behaviour = bubble_behaviour
        fluidsim.diffuse_spray_limit_behaviour = spray_behaviour
        fluidsim.diffuse_dust_limit_behaviour = dust_behaviour

        foam_active_sides = __get_parameter_data(whitewater.foam_boundary_active, frameno)
        bubble_active_sides = __get_parameter_data(whitewater.bubble_boundary_active, frameno)
        spray_active_sides = __get_parameter_data(whitewater.spray_boundary_active, frameno)
        dust_active_sides = __get_parameter_data(whitewater.bubble_boundary_active, frameno) # Same as bubble for now
        fluidsim.diffuse_foam_active_boundary_sides = foam_active_sides
        fluidsim.diffuse_bubble_active_boundary_sides = bubble_active_sides
        fluidsim.diffuse_spray_active_boundary_sides = spray_active_sides
        fluidsim.diffuse_dust_active_boundary_sides = dust_active_sides

        strength = __get_parameter_data(whitewater.foam_advection_strength, frameno)
        foam_depth = __get_parameter_data(whitewater.foam_layer_depth, frameno)
        foam_offset = __get_parameter_data(whitewater.foam_layer_offset, frameno)
        fluidsim.diffuse_foam_layer_depth = foam_depth
        fluidsim.diffuse_foam_layer_offset = foam_offset
        fluidsim.diffuse_foam_advection_strength = strength

        preserve_foam = __get_parameter_data(whitewater.preserve_foam, frameno)
        preserve_rate = __get_parameter_data(whitewater.foam_preservation_rate, frameno)
        min_density, max_density = __get_parameter_data(whitewater.min_max_foam_density, frameno)
        fluidsim.enable_diffuse_preserve_foam = preserve_foam
        fluidsim.diffuse_foam_preservation_rate = preserve_rate
        fluidsim.min_diffuse_foam_density = min_density
        fluidsim.max_diffuse_foam_density = max_density

        drag = __get_parameter_data(whitewater.bubble_drag_coefficient, frameno)
        bouyancy = __get_parameter_data(whitewater.bubble_bouyancy_coefficient, frameno)
        fluidsim.diffuse_bubble_drag_coefficient = drag
        fluidsim.diffuse_bubble_bouyancy_coefficient = bouyancy

        drag = __get_parameter_data(whitewater.dust_drag_coefficient, frameno)
        bouyancy = __get_parameter_data(whitewater.dust_bouyancy_coefficient, frameno)
        fluidsim.diffuse_dust_drag_coefficient = drag
        fluidsim.diffuse_dust_bouyancy_coefficient = bouyancy

        drag = __get_parameter_data(whitewater.spray_drag_coefficient, frameno)
        fluidsim.diffuse_spray_drag_coefficient = drag

        base_level = __get_parameter_data(whitewater.obstacle_influence_base_level, frameno)
        fluidsim.diffuse_obstacle_influence_base_level = base_level

        decay_rate = __get_parameter_data(whitewater.obstacle_influence_decay_rate, frameno)
        fluidsim.diffuse_obstacle_influence_decay_rate = decay_rate

    # World Settings
    world = dprops.world
    fluidsim.add_body_force(__get_parameter_data(world.gravity, frameno))

    # Caches created in older versions may not contain force field data. Ignore these features
    # if force field data cannot be found in the cache
    is_force_field_data_available = data.force_field_data is not None
    if is_force_field_data_available:
        force_fields_exist = (len(data.force_field_data) > 0)
        is_debugging_force_fields = __get_parameter_data(dprops.debug.export_force_field, frameno)
        is_force_fields_enabled = force_fields_exist or is_debugging_force_fields
        
        fluidsim.enable_force_fields = is_force_fields_enabled
        if is_force_fields_enabled:
            field_quality = __get_parameter_data(world.force_field_resolution, frameno)
            if field_quality == 'FORCE_FIELD_RESOLUTION_LOW':
                reduction = 4
            elif field_quality == 'FORCE_FIELD_RESOLUTION_NORMAL':
                reduction = 3
            elif field_quality == 'FORCE_FIELD_RESOLUTION_HIGH':
                reduction = 2
            elif field_quality == 'FORCE_FIELD_RESOLUTION_ULTRA':
                reduction = 1
            fluidsim.force_field_reduction_level = reduction

    is_viscosity_enabled = __get_parameter_data(world.enable_viscosity, frameno)
    if is_viscosity_enabled:
        fluidsim.viscosity = __get_viscosity_value(world, frameno)

        tolerance_int = __get_parameter_data(world.viscosity_solver_error_tolerance, frameno)
        fluidsim.viscosity_solver_error_tolerance = 1.0 * 10.0**(-tolerance_int)

    is_surface_tension_enabled = __get_parameter_data(world.enable_surface_tension, frameno)
    if is_surface_tension_enabled:
        surface_tension = __get_surface_tension_value(world, frameno)
        fluidsim.surface_tension = surface_tension

        mincfl, maxcfl = world.minimum_surface_tension_cfl, world.maximum_surface_tension_cfl
        accuracy_pct = __get_parameter_data(world.surface_tension_accuracy, frameno) / 100.0
        surface_tension_number = mincfl + (1.0 - accuracy_pct) * (maxcfl - mincfl)
        fluidsim.surface_tension_condition_number = surface_tension_number

    is_sheet_seeding_enabled = __get_parameter_data(world.enable_sheet_seeding, frameno)
    if is_sheet_seeding_enabled:
        fluidsim.enable_sheet_seeding = is_sheet_seeding_enabled
        fluidsim.sheet_fill_rate = __get_parameter_data(world.sheet_fill_rate, frameno)
        threshold = __get_parameter_data(world.sheet_fill_threshold, frameno)
        fluidsim.sheet_fill_threshold = threshold - 1

    friction = __get_parameter_data(world.boundary_friction, frameno)
    fluidsim.boundary_friction = friction

    # Surface Settings

    surface = dprops.surface
    subdivisions = __get_parameter_data(surface.subdivisions, frameno) + 1
    fluidsim.surface_subdivision_level = subdivisions

    compute_chunk_mode = __get_parameter_data(surface.compute_chunk_mode, frameno)
    if compute_chunk_mode == 'COMPUTE_CHUNK_MODE_AUTO':
        num_chunks = __get_parameter_data(surface.compute_chunks_auto, frameno)
    elif compute_chunk_mode == 'COMPUTE_CHUNK_MODE_FIXED':
        num_chunks = __get_parameter_data(surface.compute_chunks_fixed, frameno)
    fluidsim.num_polygonizer_slices = num_chunks

    particle_scale = __get_parameter_data(surface.particle_scale, frameno)
    particle_scale *= surface.native_particle_scale
    fluidsim.marker_particle_scale = particle_scale

    fluidsim.surface_smoothing_value = \
        __get_parameter_data(surface.smoothing_value, frameno)
    fluidsim.surface_smoothing_iterations = \
        __get_parameter_data(surface.smoothing_iterations, frameno)

    enable_meshing_offset = __get_parameter_data(surface.enable_meshing_offset, frameno)
    fluidsim.enable_obstacle_meshing_offset = enable_meshing_offset

    meshing_mode = __get_parameter_data(surface.obstacle_meshing_mode, frameno)
    meshing_offset = __get_obstacle_meshing_offset(meshing_mode)
    fluidsim.obstacle_meshing_offset = meshing_offset

    fluidsim.enable_remove_surface_near_domain = \
        __get_parameter_data(surface.remove_mesh_near_domain, frameno)
    fluidsim.remove_surface_near_domain_distance = \
        __get_parameter_data(surface.remove_mesh_near_domain_distance, frameno) - 1

    fluidsim.enable_inverted_contact_normals = \
        __get_parameter_data(surface.invert_contact_normals, frameno)
    fluidsim.enable_surface_motion_blur = \
        __get_parameter_data(surface.generate_motion_blur_data, frameno)

    fluidsim.enable_surface_velocity_attribute = \
        __get_parameter_data(surface.enable_velocity_vector_attribute, frameno)
    fluidsim.enable_surface_speed_attribute = \
        __get_parameter_data(surface.enable_speed_attribute, frameno)
    fluidsim.enable_surface_age_attribute = \
        __get_parameter_data(surface.enable_age_attribute, frameno)
    fluidsim.enable_surface_color_attribute = \
        __get_parameter_data(surface.enable_color_attribute, frameno)
    fluidsim.enable_surface_source_id_attribute = \
        __get_parameter_data(surface.enable_source_id_attribute, frameno)

    __set_meshing_volume_object(fluidsim, data, frameno)

    # Advanced Settings

    advanced = dprops.advanced
    min_substeps, max_substeps = __get_parameter_data(advanced.min_max_time_steps_per_frame, frameno)
    fluidsim.min_time_steps_per_frame = min_substeps
    fluidsim.max_time_steps_per_frame = max_substeps

    fluidsim.enable_adaptive_obstacle_time_stepping = \
        __get_parameter_data(advanced.enable_adaptive_obstacle_time_stepping, frameno)
    fluidsim.enable_adaptive_force_field_time_stepping = \
        __get_parameter_data(advanced.enable_adaptive_force_field_time_stepping, frameno)

    fluidsim.marker_particle_jitter_factor = \
        __get_parameter_data(advanced.particle_jitter_factor, frameno)
    fluidsim.jitter_surface_marker_particles = \
        __get_parameter_data(advanced.jitter_surface_particles, frameno)

    velocity_transfer_method = __get_parameter_data(advanced.velocity_transfer_method, frameno)
    if velocity_transfer_method == 'VELOCITY_TRANSFER_METHOD_FLIP':
        fluidsim.set_velocity_transfer_method_FLIP()
    elif velocity_transfer_method == 'VELOCITY_TRANSFER_METHOD_APIC':
        fluidsim.set_velocity_transfer_method_APIC()

    fluidsim.PICFLIP_ratio = __get_parameter_data(advanced.PICFLIP_ratio, frameno)
    fluidsim.PICAPIC_ratio = __get_parameter_data(advanced.PICAPIC_ratio, frameno)

    CFL_number = __get_parameter_data(advanced.CFL_condition_number, frameno)
    fluidsim.CFL_condition_number = CFL_number

    fluidsim.enable_extreme_velocity_removal = \
        __get_parameter_data(advanced.enable_extreme_velocity_removal, frameno)

    threading_mode = __get_parameter_data(advanced.threading_mode, frameno)
    if threading_mode == 'THREADING_MODE_AUTO_DETECT':
        num_threads = __get_parameter_data(advanced.num_threads_auto_detect, frameno)
    elif threading_mode == 'THREADING_MODE_FIXED':
        num_threads = __get_parameter_data(advanced.num_threads_fixed, frameno)
    fluidsim.max_thread_count = num_threads

    fluidsim.enable_opencl_scalar_field = \
        __get_parameter_data(advanced.enable_gpu_features, frameno)
    fluidsim.enable_opencl_particle_advection = \
        __get_parameter_data(advanced.enable_gpu_features, frameno)

    fluidsim.preferred_gpu_device = dprops.initialize.gpu_device

    fluidsim.enable_asynchronous_meshing = \
        __get_parameter_data(advanced.enable_asynchronous_meshing, frameno)

    fluidsim.enable_static_solid_levelset_precomputation = \
        __get_parameter_data(advanced.precompute_static_obstacles, frameno)

    fluidsim.enable_temporary_mesh_levelset = \
        __get_parameter_data(advanced.reserve_temporary_grids, frameno)

    # Debug Settings

    fluidsim.enable_fluid_particle_output = \
        __get_parameter_data(dprops.debug.export_fluid_particles, frameno)

    fluidsim.enable_internal_obstacle_mesh_output = \
        __get_parameter_data(dprops.debug.export_internal_obstacle_mesh, frameno)

    if is_force_field_data_available:
        fluidsim.enable_force_field_debug_output = \
            __get_parameter_data(dprops.debug.export_force_field, frameno)

    # Internal Settings

    fluidsim.set_mesh_output_format_as_bobj()
    if is_whitewater_enabled:
        fluidsim.output_diffuse_material_as_separate_files = True


def __get_mesh_centroid(tmesh):
    vsum = [0.0, 0.0, 0.0]
    for i in range(0, len(tmesh.vertices), 3):
        vsum[0] += tmesh.vertices[i]
        vsum[1] += tmesh.vertices[i + 1]
        vsum[2] += tmesh.vertices[i + 2]
    vsum[0] /= (len(tmesh.vertices) / 3)
    vsum[1] /= (len(tmesh.vertices) / 3)
    vsum[2] /= (len(tmesh.vertices) / 3)
    return vsum


def __get_fluid_object_velocity(fluid_object, frameid):
    if fluid_object.fluid_velocity_mode.data == 'FLUID_VELOCITY_MANUAL':
        return __get_parameter_data(fluid_object.initial_velocity, frameid)
    elif fluid_object.fluid_velocity_mode.data == 'FLUID_VELOCITY_AXIS':
        timeline_frame = __get_timeline_frame()
        local_x, local_y, local_z = __extract_local_axis(fluid_object.name, timeline_frame)
        axis_mode = __get_parameter_data(fluid_object.fluid_axis_mode, frameid)
        if axis_mode == 'LOCAL_AXIS_POS_X' or axis_mode == 0.0:
            local_axis = local_x
        elif axis_mode == 'LOCAL_AXIS_POS_Y' or axis_mode == 1.0:
            local_axis = local_y
        elif axis_mode == 'LOCAL_AXIS_POS_Z' or axis_mode == 2.0:
            local_axis = local_z
        elif axis_mode == 'LOCAL_AXIS_NEG_X' or axis_mode == 3.0:
            local_axis = [-local_x[0], -local_x[1], -local_x[2]]
        elif axis_mode == 'LOCAL_AXIS_NEG_Y' or axis_mode == 4.0:
            local_axis = [-local_y[0], -local_y[1], -local_y[2]]
        elif axis_mode == 'LOCAL_AXIS_NEG_Z' or axis_mode == 5.0:
            local_axis = [-local_z[0], -local_z[1], -local_z[2]]

        initial_speed = __get_parameter_data(fluid_object.initial_speed, frameid)
        velocity = [initial_speed * local_axis[0], initial_speed * local_axis[1], initial_speed * local_axis[2]]
        return velocity

    # Use target
    if not fluid_object.target_object:
        return [0, 0, 0]

    target_object_name = fluid_object.target_object
    initial_speed = __get_parameter_data(fluid_object.initial_speed, frameid)
    timeline_frame = __get_timeline_frame()

    fluid_object_mesh = __extract_mesh(fluid_object.name, timeline_frame)
    c1 = __get_mesh_centroid(fluid_object_mesh)
    c2 = __extract_centroid(target_object_name, timeline_frame)
    vdir = [c2[0] - c1[0], c2[1] - c1[1], c2[2] - c1[2]]
    vlen = math.sqrt(vdir[0] * vdir[0] + vdir[1] * vdir[1] + vdir[2] * vdir[2])
    eps = 1e-6
    if vlen < eps:
        return [0, 0, 0]

    vdir[0] /= vlen
    vdir[1] /= vlen
    vdir[2] /= vlen
    vdir[0] *= initial_speed
    vdir[1] *= initial_speed
    vdir[2] *= initial_speed

    return vdir


def __get_inflow_object_velocity(inflow_object, frameid):
    if inflow_object.inflow_velocity_mode.data == 'INFLOW_VELOCITY_MANUAL':
        return __get_parameter_data(inflow_object.inflow_velocity, frameid)
    elif inflow_object.inflow_velocity_mode.data == 'INFLOW_VELOCITY_AXIS':
        timeline_frame = __get_timeline_frame()
        local_x, local_y, local_z = __extract_local_axis(inflow_object.name, timeline_frame)
        axis_mode = __get_parameter_data(inflow_object.inflow_axis_mode, frameid)
        if axis_mode == 'LOCAL_AXIS_POS_X' or axis_mode == 0.0:
            local_axis = local_x
        elif axis_mode == 'LOCAL_AXIS_POS_Y' or axis_mode == 1.0:
            local_axis = local_y
        elif axis_mode == 'LOCAL_AXIS_POS_Z' or axis_mode == 2.0:
            local_axis = local_z
        elif axis_mode == 'LOCAL_AXIS_NEG_X' or axis_mode == 3.0:
            local_axis = [-local_x[0], -local_x[1], -local_x[2]]
        elif axis_mode == 'LOCAL_AXIS_NEG_Y' or axis_mode == 4.0:
            local_axis = [-local_y[0], -local_y[1], -local_y[2]]
        elif axis_mode == 'LOCAL_AXIS_NEG_Z' or axis_mode == 5.0:
            local_axis = [-local_z[0], -local_z[1], -local_z[2]]

        inflow_speed = __get_parameter_data(inflow_object.inflow_speed, frameid)
        velocity = [inflow_speed * local_axis[0], inflow_speed * local_axis[1], inflow_speed * local_axis[2]]
        return velocity

    # Use target
    if not inflow_object.target_object:
        return [0, 0, 0]

    target_object_name = inflow_object.target_object
    inflow_speed = __get_parameter_data(inflow_object.inflow_speed, frameid)
    timeline_frame = __get_timeline_frame()

    fluid_object_mesh = __extract_mesh(inflow_object.name, timeline_frame)
    c1 = __get_mesh_centroid(fluid_object_mesh)
    c2 = __extract_centroid(target_object_name, timeline_frame)
    vdir = [c2[0] - c1[0], c2[1] - c1[1], c2[2] - c1[2]]
    vlen = math.sqrt(vdir[0] * vdir[0] + vdir[1] * vdir[1] + vdir[2] * vdir[2])
    eps = 1e-6
    if vlen < eps:
        return [0, 0, 0]

    vdir[0] /= vlen
    vdir[1] /= vlen
    vdir[2] /= vlen
    vdir[0] *= inflow_speed
    vdir[1] *= inflow_speed
    vdir[2] *= inflow_speed

    return vdir


def __add_fluid_objects(fluidsim, data, bakedata, frameid=0):
    init_data = data.domain_data.initialize
    bbox = init_data.bbox
    isize, jsize, ksize = init_data.isize, init_data.jsize, init_data.ksize
    dx = init_data.dx
    
    for obj in list(data.fluid_data):
        if obj.frame_offset_type.data == 'OFFSET_TYPE_FRAME':
            frame_offset = __get_parameter_data(obj.frame_offset, frameid)
            if frame_offset != frameid:
                continue
        elif obj.frame_offset_type.data == 'OFFSET_TYPE_TIMELINE':
            frame_offset = __get_parameter_data(obj.timeline_offset, frameid)
            if frame_offset != __get_timeline_frame():
                continue

        velocity = __get_fluid_object_velocity(obj, frameid)

        if __is_object_dynamic(obj.name):
            timeline_frame = __get_timeline_frame()
            previous_mesh, current_mesh, next_mesh = __extract_dynamic_frame_meshes(obj.name, timeline_frame)

            fluid_object = MeshObject(isize, jsize, ksize, dx)
            fluid_object.update_mesh_animated(previous_mesh, current_mesh, next_mesh)
            fluid_object.enable_append_object_velocity = __get_parameter_data(obj.append_object_velocity, frameid)
            fluid_object.object_velocity_influence = __get_parameter_data(obj.append_object_velocity_influence, frameid)
            fluid_object.source_id = __get_parameter_data(obj.source_id, frameid)
            fluid_object.set_source_color(__get_parameter_data(obj.color, frameid))
            fluidsim.add_mesh_fluid(fluid_object, velocity[0], velocity[1], velocity[2])
        else:
            mesh = __extract_static_frame_mesh(obj.name)

            fluid_object = MeshObject(isize, jsize, ksize, dx)
            fluid_object.update_mesh_static(mesh)
            fluid_object.source_id = __get_parameter_data(obj.source_id, frameid)
            fluid_object.set_source_color(__get_parameter_data(obj.color, frameid))
            fluidsim.add_mesh_fluid(fluid_object, velocity[0], velocity[1], velocity[2])

        data.fluid_data.remove(obj)
        if __check_bake_cancelled(bakedata):
            return


def __add_obstacle_objects(fluidsim, data, bakedata):
    init_data = data.domain_data.initialize
    bbox = init_data.bbox
    isize, jsize, ksize = init_data.isize, init_data.jsize, init_data.ksize
    dx = init_data.dx

    obstacle_objects = []
    for obj in data.obstacle_data:
        obstacle = MeshObject(isize, jsize, ksize, dx)
        obstacle.inverse = __get_parameter_data(obj.is_inversed)

        if not __is_object_dynamic(obj.name):
            mesh = __extract_static_frame_mesh(obj.name)
            obstacle.update_mesh_static(mesh)

        obstacle_objects.append(obstacle)
        fluidsim.add_mesh_obstacle(obstacle)

        if __check_bake_cancelled(bakedata):
            return

    return obstacle_objects


def __add_inflow_objects(fluidsim, data, bakedata):
    init_data = data.domain_data.initialize
    bbox = init_data.bbox
    isize, jsize, ksize = init_data.isize, init_data.jsize, init_data.ksize
    dx = init_data.dx

    inflow_objects = []
    for obj in data.inflow_data:
        source = MeshFluidSource(isize, jsize, ksize, dx)

        if not __is_object_dynamic(obj.name):
            mesh = __extract_static_frame_mesh(obj.name)
            source.update_mesh_static(mesh)

        fluidsim.add_mesh_fluid_source(source)
        inflow_objects.append(source)

        if __check_bake_cancelled(bakedata):
            return

    return inflow_objects


def __add_outflow_objects(fluidsim, data, bakedata):
    init_data = data.domain_data.initialize
    bbox = init_data.bbox
    isize, jsize, ksize = init_data.isize, init_data.jsize, init_data.ksize
    dx = init_data.dx

    outflow_objects = []
    for obj in data.outflow_data:
        source = MeshFluidSource(isize, jsize, ksize, dx)
        source.outflow = True
        source.outflow_inverse = __get_parameter_data(obj.is_inversed)

        if not __is_object_dynamic(obj.name):
            mesh = __extract_static_frame_mesh(obj.name)
            source.update_mesh_static(mesh)

        fluidsim.add_mesh_fluid_source(source)
        outflow_objects.append(source)

        if __check_bake_cancelled(bakedata):
            return

    return outflow_objects


def __add_force_field_objects(fluidsim, data, bakedata):
    force_field_objects = []
    if not fluidsim.enable_force_fields:
        return force_field_objects

    init_data = data.domain_data.initialize
    bbox = init_data.bbox
    isize, jsize, ksize = init_data.isize, init_data.jsize, init_data.ksize
    dx = init_data.dx

    force_field_grid = fluidsim.get_force_field_grid()
    force_field_objects = []
    for obj in data.force_field_data:
        field_type = obj.force_field_type.data
        field_object = None
        if field_type == 'FORCE_FIELD_TYPE_POINT':
            field_object = ForceFieldPoint()
        elif field_type == 'FORCE_FIELD_TYPE_SURFACE':
            field_object = ForceFieldSurface()
        elif field_type == 'FORCE_FIELD_TYPE_VOLUME':
            field_object = ForceFieldVolume()
        elif field_type == 'FORCE_FIELD_TYPE_CURVE':
            field_object = ForceFieldCurve()

        if not __is_object_dynamic(obj.name):
            mesh = __extract_force_field_mesh(obj.name)
            field_object.update_mesh_static(mesh)

        force_field_grid.add_force_field(field_object)
        force_field_objects.append(field_object)

        if __check_bake_cancelled(bakedata):
            return

    return force_field_objects


def __initialize_fluid_simulation(fluidsim, data, cache_directory, bakedata, savestate_id):
    set_console_output(bakedata.is_console_output_enabled)
    
    __load_save_state_data(fluidsim, data, cache_directory, savestate_id)

    init_data = data.domain_data.initialize
    num_frames = init_data.frame_end - init_data.frame_start + 1
    bakedata.completed_frames = fluidsim.get_current_frame()
    bakedata.progress = bakedata.completed_frames / num_frames

    __initialize_fluid_simulation_settings(fluidsim, data)

    __add_fluid_objects(fluidsim, data, bakedata, fluidsim.get_current_frame())
    data.obstacle_objects = __add_obstacle_objects(fluidsim, data, bakedata)
    data.inflow_objects = __add_inflow_objects(fluidsim, data, bakedata)
    data.outflow_objects = __add_outflow_objects(fluidsim, data, bakedata)
    data.force_field_objects = __add_force_field_objects(fluidsim, data, bakedata)

    fluidsim.initialize()

    bakedata.is_initialized = True


def __update_dynamic_object_mesh(animated_object, object_data):
    timeline_frame = __get_timeline_frame()
    mesh_previous, mesh_current, mesh_next = __extract_dynamic_frame_meshes(object_data.name, timeline_frame)
    animated_object.update_mesh_animated(mesh_previous, mesh_current, mesh_next)


def __update_dynamic_force_field_mesh(animated_object, object_data):
    timeline_frame = __get_timeline_frame()
    mesh_previous, mesh_current, mesh_next = __extract_dynamic_force_field_frame_meshes(object_data.name, timeline_frame)
    animated_object.update_mesh_animated(mesh_previous, mesh_current, mesh_next)


def __update_animatable_inflow_properties(data, frameid):
    inflow_objects = data.inflow_objects
    inflow_data = data.inflow_data

    for idx, inflow in enumerate(inflow_objects):
        data = inflow_data[idx]

        if __is_object_dynamic(data.name):
            __update_dynamic_object_mesh(inflow, data)
        
        inflow.enable = __get_parameter_data(data.is_enabled, frameid)
        inflow.set_velocity(__get_inflow_object_velocity(data, frameid))
        inflow.enable_append_object_velocity = \
            __get_parameter_data(data.append_object_velocity, frameid)
        inflow.object_velocity_influence = \
            __get_parameter_data(data.append_object_velocity_influence, frameid)
        inflow.substep_emissions = __get_parameter_data(data.substep_emissions, frameid)

        is_constrained = __get_parameter_data(data.constrain_fluid_velocity, frameid)
        inflow.enable_constrained_fluid_velocity = is_constrained

        inflow.source_id = __get_parameter_data(data.source_id, frameid)
        inflow.set_source_color(__get_parameter_data(data.color, frameid))


def __update_animatable_outflow_properties(data, frameid):
    outflow_objects = data.outflow_objects
    outflow_data = data.outflow_data

    for idx, outflow in enumerate(outflow_objects):
        data = outflow_data[idx]

        if __is_object_dynamic(data.name):
            __update_dynamic_object_mesh(outflow, data)

        outflow.enable = __get_parameter_data(data.is_enabled, frameid)
        outflow.fluid_outflow =  __get_parameter_data(data.remove_fluid, frameid)
        outflow.diffuse_outflow =  __get_parameter_data(data.remove_whitewater, frameid)


def __update_animatable_force_field_properties(data, frameid):
    force_field_objects = data.force_field_objects
    force_field_data = data.force_field_data

    for idx, force_field in enumerate(force_field_objects):
        data = force_field_data[idx]

        if __is_object_dynamic(data.name):
            __update_dynamic_force_field_mesh(force_field, data)

        force_field.enable = __get_parameter_data(data.is_enabled, frameid)
        force_field.strength = __get_parameter_data(data.strength, frameid)
        force_field.falloff_power = __get_parameter_data(data.falloff_power, frameid)
        force_field.max_force_limit_factor = __get_parameter_data(data.maximum_force_limit_factor, frameid)
        force_field.enable_min_distance = __get_parameter_data(data.enable_min_distance, frameid)
        force_field.enable_max_distance = __get_parameter_data(data.enable_max_distance, frameid)
        force_field.min_distance, force_field.max_distance = __get_parameter_data(data.min_max_distance, frameid)

        field_type = data.force_field_type.data
        if field_type == 'FORCE_FIELD_TYPE_POINT':
            force_field.gravity_scale = __get_parameter_data(data.gravity_scale_point, frameid)
            force_field.gravity_scale_width = __get_parameter_data(data.gravity_scale_width_point, frameid)
        elif field_type == 'FORCE_FIELD_TYPE_SURFACE':
            force_field.gravity_scale = __get_parameter_data(data.gravity_scale_surface, frameid)
            force_field.gravity_scale_width = __get_parameter_data(data.gravity_scale_width_surface, frameid)
        elif field_type == 'FORCE_FIELD_TYPE_VOLUME':
            force_field.gravity_scale = __get_parameter_data(data.gravity_scale_volume, frameid)
            force_field.gravity_scale_width = __get_parameter_data(data.gravity_scale_width_volume, frameid)
        elif field_type == 'FORCE_FIELD_TYPE_CURVE':
            force_field.flow_strength = __get_parameter_data(data.flow_strength, frameid)
            force_field.spin_strength = __get_parameter_data(data.spin_strength, frameid)
            force_field.enable_endcaps = __get_parameter_data(data.enable_endcaps, frameid)
            force_field.gravity_scale = __get_parameter_data(data.gravity_scale_curve, frameid)
            force_field.gravity_scale_width = __get_parameter_data(data.gravity_scale_width_curve, frameid)


def __update_animatable_obstacle_properties(data, frameid):
    obstacle_objects = data.obstacle_objects
    obstacle_data = data.obstacle_data

    for idx, mesh_object in enumerate(obstacle_objects):
        data = obstacle_data[idx]

        if __is_object_dynamic(data.name):
            __update_dynamic_object_mesh(mesh_object, data)

        mesh_object.enable = __get_parameter_data(data.is_enabled, frameid)
        mesh_object.friction = __get_parameter_data(data.friction, frameid)
        mesh_object.whitewater_influence = __get_parameter_data(data.whitewater_influence, frameid)
        mesh_object.dust_emission_strength = __get_parameter_data(data.dust_emission_strength, frameid)
        mesh_object.sheeting_strength = __get_parameter_data(data.sheeting_strength, frameid)
        mesh_object.mesh_expansion = __get_parameter_data(data.mesh_expansion, frameid)


def __update_animatable_meshing_volume_properties(data, frameid):
    surface_data = data.domain_data.surface
    meshing_volume_mode = __get_parameter_data(surface_data.meshing_volume_mode, frameid)
    if meshing_volume_mode != 'MESHING_VOLUME_MODE_OBJECT':
        return
    if not surface_data.meshing_volume_object:
        return

    volume_object = surface_data.meshing_volume_object_class
    volume_name = surface_data.meshing_volume_object
    if __is_object_dynamic(surface_data.meshing_volume_object):
        timeline_frame = __get_timeline_frame()
        mesh_previous, mesh_current, mesh_next = __extract_dynamic_frame_meshes(volume_name, timeline_frame)
        volume_object.update_mesh_animated(mesh_previous, mesh_current, mesh_next)


def __set_property(obj, pname, value):
    eps = 1e-6
    old_value = getattr(obj, pname)
    if isinstance(value, list):
        for i, v in enumerate(value):
            if v != old_value[i]:
                setattr(obj, pname, value)
                break
    elif abs(value - old_value) > eps:
        setattr(obj, pname, value)


def __set_body_force_property(fluidsim, body_force):
    eps = 1e-6
    old_body_force = fluidsim.get_constant_body_force()
    new_body_force = Vector3(body_force[0], body_force[1], body_force[2])
    if (new_body_force - old_body_force).length() > eps:
        fluidsim.reset_body_force()
        fluidsim.add_body_force(body_force)


def __set_whitewater_emission_boundary_property(fluidsim, bounds):
    eps = 1e-6
    old_bounds = fluidsim.diffuse_emitter_generation_bounds
    if ((bounds.position - old_bounds.position).length() > eps or
            abs(bounds.width - old_bounds.width) > eps or 
            abs(bounds.height - old_bounds.height) > eps or 
            abs(bounds.depth - old_bounds.depth) > eps):
        fluidsim.diffuse_emitter_generation_bounds = bounds


def __set_meshing_volume_object(fluidsim, data, frameid=0):
    init_data = data.domain_data.initialize
    surface_data = data.domain_data.surface
    bbox = init_data.bbox
    isize, jsize, ksize = init_data.isize, init_data.jsize, init_data.ksize
    dx = init_data.dx

    meshing_volume_mode = __get_parameter_data(surface_data.meshing_volume_mode, frameid)
    if meshing_volume_mode != 'MESHING_VOLUME_MODE_OBJECT':
        return
    if not surface_data.meshing_volume_object:
        return

    object_name = surface_data.meshing_volume_object
    if __is_object_dynamic(object_name):
        timeline_frame = __get_timeline_frame()
        previous_mesh, current_mesh, next_mesh = __extract_dynamic_frame_meshes(object_name, timeline_frame)
        volume_object = MeshObject(isize, jsize, ksize, dx)
        volume_object.update_mesh_animated(previous_mesh, current_mesh, next_mesh)
    else:
        mesh = __extract_static_frame_mesh(object_name)
        volume_object = MeshObject(isize, jsize, ksize, dx)
        volume_object.update_mesh_static(mesh)

    fluidsim.set_meshing_volume(volume_object)
    surface_data.meshing_volume_object_class = volume_object


def __update_animatable_domain_properties(fluidsim, data, frameno):
    dprops = data.domain_data

    # Whitewater Simulation Settings
    whitewater = dprops.whitewater
    if __get_parameter_data(whitewater.enable_whitewater_simulation):
        is_generating_whitewater = __get_parameter_data(whitewater.enable_whitewater_emission, frameno)
        __set_property(fluidsim, 'enable_diffuse_particle_emission', is_generating_whitewater)

        is_foam_enabled = __get_parameter_data(whitewater.enable_foam, frameno)
        is_bubbles_enabled = __get_parameter_data(whitewater.enable_bubbles, frameno)
        is_spray_enabled = __get_parameter_data(whitewater.enable_spray, frameno)
        is_dust_enabled = __get_parameter_data(whitewater.enable_dust, frameno)
        is_dust_boundary_emission_enabled = __get_parameter_data(whitewater.enable_dust_emission_near_boundary, frameno)
        __set_property(fluidsim, 'enable_diffuse_foam', is_foam_enabled)
        __set_property(fluidsim, 'enable_diffuse_bubbles', is_bubbles_enabled)
        __set_property(fluidsim, 'enable_diffuse_spray', is_spray_enabled)
        __set_property(fluidsim, 'enable_diffuse_dust', is_dust_enabled)
        __set_property(fluidsim, 'enable_boundary_diffuse_dust_emission', is_dust_boundary_emission_enabled)

        whitewater_motion_blur = __get_parameter_data(whitewater.generate_whitewater_motion_blur_data, frameno)
        __set_property(fluidsim, 'enable_whitewater_motion_blur', whitewater_motion_blur)

        emitter_pct = __get_parameter_data(whitewater.whitewater_emitter_generation_rate, frameno)
        __set_property(fluidsim, 'diffuse_emitter_generation_rate', emitter_pct / 100)

        wavecrest_rate = __get_parameter_data(whitewater.wavecrest_emission_rate, frameno)
        turbulence_rate = __get_parameter_data(whitewater.turbulence_emission_rate, frameno)
        dust_rate = __get_parameter_data(whitewater.dust_emission_rate, frameno)
        __set_property(fluidsim, 'diffuse_particle_wavecrest_emission_rate', wavecrest_rate)
        __set_property(fluidsim, 'diffuse_particle_turbulence_emission_rate', turbulence_rate)
        __set_property(fluidsim, 'diffuse_particle_dust_emission_rate', dust_rate)

        spray_emission_speed = __get_parameter_data(whitewater.spray_emission_speed, frameno)
        __set_property(fluidsim, 'diffuse_spray_emission_speed', spray_emission_speed)

        min_speed, max_speed = __get_parameter_data(whitewater.min_max_whitewater_energy_speed, frameno)
        __set_property(fluidsim, 'min_diffuse_emitter_energy', 0.5 * min_speed * min_speed)
        __set_property(fluidsim, 'max_diffuse_emitter_energy', 0.5 * max_speed * max_speed)

        mink, maxk = __get_parameter_data(whitewater.min_max_whitewater_wavecrest_curvature, frameno)
        __set_property(fluidsim, 'min_diffuse_wavecrest_curvature', mink)
        __set_property(fluidsim, 'max_diffuse_wavecrest_curvature', maxk)

        mint, maxt = __get_parameter_data(whitewater.min_max_whitewater_turbulence, frameno)
        __set_property(fluidsim, 'min_diffuse_turbulence', mint)
        __set_property(fluidsim, 'max_diffuse_turbulence', maxt)

        max_particles = __get_parameter_data(whitewater.max_whitewater_particles, frameno)
        __set_property(fluidsim, 'max_num_diffuse_particles', int(max_particles * 1e6))

        bounds = __get_emission_boundary(whitewater, fluidsim)
        __set_whitewater_emission_boundary_property(fluidsim, bounds)

        min_lifespan, max_lifespan = __get_parameter_data(whitewater.min_max_whitewater_lifespan, frameno)
        lifespan_variance = __get_parameter_data(whitewater.whitewater_lifespan_variance, frameno)
        __set_property(fluidsim, 'min_diffuse_particle_lifetime', min_lifespan)
        __set_property(fluidsim, 'max_diffuse_particle_lifetime', max_lifespan)
        __set_property(fluidsim, 'diffuse_particle_lifetime_variance', lifespan_variance)

        foam_modifier = __get_parameter_data(whitewater.foam_lifespan_modifier, frameno)
        bubble_modifier = __get_parameter_data(whitewater.bubble_lifespan_modifier, frameno)
        spray_modifier = __get_parameter_data(whitewater.spray_lifespan_modifier, frameno)
        dust_modifier = __get_parameter_data(whitewater.dust_lifespan_modifier, frameno)
        __set_property(fluidsim, 'foam_particle_lifetime_modifier', 1.0 / max(foam_modifier, 1e-6))
        __set_property(fluidsim, 'bubble_particle_lifetime_modifier', 1.0 / max(bubble_modifier, 1e-6))
        __set_property(fluidsim, 'spray_particle_lifetime_modifier', 1.0 / max(spray_modifier, 1e-6))
        __set_property(fluidsim, 'dust_particle_lifetime_modifier', 1.0 / max(dust_modifier, 1e-6))

        foam_behaviour = __get_parameter_data(whitewater.foam_boundary_behaviour, frameno)
        bubble_behaviour = __get_parameter_data(whitewater.bubble_boundary_behaviour, frameno)
        spray_behaviour = __get_parameter_data(whitewater.spray_boundary_behaviour, frameno)
        dust_behaviour = __get_parameter_data(whitewater.bubble_boundary_behaviour, frameno) # Same as bubble for now
        foam_behaviour = __get_limit_behaviour_enum(foam_behaviour)
        bubble_behaviour = __get_limit_behaviour_enum(bubble_behaviour)
        spray_behaviour = __get_limit_behaviour_enum(spray_behaviour)
        dust_behaviour = __get_limit_behaviour_enum(dust_behaviour)
        __set_property(fluidsim, 'diffuse_foam_limit_behaviour', foam_behaviour)
        __set_property(fluidsim, 'diffuse_bubble_limit_behaviour', bubble_behaviour)
        __set_property(fluidsim, 'diffuse_spray_limit_behaviour', spray_behaviour)
        __set_property(fluidsim, 'diffuse_dust_limit_behaviour', dust_behaviour)

        foam_active_sides = __get_parameter_data(whitewater.foam_boundary_active, frameno)
        bubble_active_sides = __get_parameter_data(whitewater.bubble_boundary_active, frameno)
        spray_active_sides = __get_parameter_data(whitewater.spray_boundary_active, frameno)
        dust_active_sides = __get_parameter_data(whitewater.bubble_boundary_active, frameno) # Same as bubble for now
        __set_property(fluidsim, 'diffuse_foam_active_boundary_sides', foam_active_sides)
        __set_property(fluidsim, 'diffuse_bubble_active_boundary_sides', bubble_active_sides)
        __set_property(fluidsim, 'diffuse_spray_active_boundary_sides', spray_active_sides)
        __set_property(fluidsim, 'diffuse_dust_active_boundary_sides', dust_active_sides)

        strength = __get_parameter_data(whitewater.foam_advection_strength, frameno)
        foam_depth = __get_parameter_data(whitewater.foam_layer_depth, frameno)
        foam_offset = __get_parameter_data(whitewater.foam_layer_offset, frameno)
        __set_property(fluidsim, 'diffuse_foam_layer_depth', foam_depth)
        __set_property(fluidsim, 'diffuse_foam_layer_offset', foam_offset)
        __set_property(fluidsim, 'diffuse_foam_advection_strength', strength)

        preserve_foam = __get_parameter_data(whitewater.preserve_foam, frameno)
        preserve_rate = __get_parameter_data(whitewater.foam_preservation_rate, frameno)
        min_density, max_density = __get_parameter_data(whitewater.min_max_foam_density, frameno)
        __set_property(fluidsim, 'enable_diffuse_preserve_foam', preserve_foam)
        __set_property(fluidsim, 'diffuse_foam_preservation_rate', preserve_rate)
        __set_property(fluidsim, 'min_diffuse_foam_density', min_density)
        __set_property(fluidsim, 'max_diffuse_foam_density', max_density)

        drag = __get_parameter_data(whitewater.bubble_drag_coefficient, frameno)
        bouyancy = __get_parameter_data(whitewater.bubble_bouyancy_coefficient, frameno)
        __set_property(fluidsim, 'diffuse_bubble_drag_coefficient', drag)
        __set_property(fluidsim, 'diffuse_bubble_bouyancy_coefficient', bouyancy)

        drag = __get_parameter_data(whitewater.dust_drag_coefficient, frameno)
        bouyancy = __get_parameter_data(whitewater.dust_bouyancy_coefficient, frameno)
        __set_property(fluidsim, 'diffuse_dust_drag_coefficient', drag)
        __set_property(fluidsim, 'diffuse_dust_bouyancy_coefficient', bouyancy)

        drag = __get_parameter_data(whitewater.spray_drag_coefficient, frameno)
        __set_property(fluidsim, 'diffuse_spray_drag_coefficient', drag)

        base_level = __get_parameter_data(whitewater.obstacle_influence_base_level, frameno)
        __set_property(fluidsim, 'diffuse_obstacle_influence_base_level', base_level)

        decay_rate = __get_parameter_data(whitewater.obstacle_influence_decay_rate, frameno)
        __set_property(fluidsim, 'diffuse_obstacle_influence_decay_rate', decay_rate)

    # World Settings

    world = dprops.world
    gravity = __get_parameter_data(world.gravity, frameno)
    __set_body_force_property(fluidsim, gravity)

    is_viscosity_enabled = __get_parameter_data(world.enable_viscosity, frameno)
    if is_viscosity_enabled:
        viscosity = __get_viscosity_value(world, frameno)
        __set_property(fluidsim, 'viscosity', viscosity)

        tolerance_int = __get_parameter_data(world.viscosity_solver_error_tolerance, frameno)
        error_tolerance = 1.0 * 10.0**(-tolerance_int)
        __set_property(fluidsim, 'viscosity_solver_error_tolerance', error_tolerance)
    elif fluidsim.viscosity > 0.0:
        __set_property(fluidsim, 'viscosity', 0.0)

    is_surface_tension_enabled = __get_parameter_data(world.enable_surface_tension, frameno)
    if is_surface_tension_enabled:
        surface_tension = __get_surface_tension_value(world, frameno)
        __set_property(fluidsim, 'surface_tension', surface_tension)

        mincfl, maxcfl = world.minimum_surface_tension_cfl, world.maximum_surface_tension_cfl
        accuracy_pct = __get_parameter_data(world.surface_tension_accuracy, frameno) / 100.0
        surface_tension_number = mincfl + (1.0 - accuracy_pct) * (maxcfl - mincfl)
        __set_property(fluidsim, 'surface_tension_condition_number', surface_tension_number)

    elif fluidsim.surface_tension > 0.0:
        __set_property(fluidsim, 'surface_tension', 0.0)

    is_sheet_seeding_enabled = __get_parameter_data(world.enable_sheet_seeding, frameno)
    if is_sheet_seeding_enabled:
        sheet_fill_rate = __get_parameter_data(world.sheet_fill_rate, frameno)
        threshold = __get_parameter_data(world.sheet_fill_threshold, frameno)
        __set_property(fluidsim, 'enable_sheet_seeding', is_sheet_seeding_enabled)
        __set_property(fluidsim, 'sheet_fill_rate', sheet_fill_rate)
        __set_property(fluidsim, 'sheet_fill_threshold', threshold - 1)

    friction = __get_parameter_data(world.boundary_friction, frameno)
    __set_property(fluidsim, 'boundary_friction', friction)

    # Surface Settings

    surface = dprops.surface
    subdivisions = __get_parameter_data(surface.subdivisions, frameno) + 1
    __set_property(fluidsim, 'surface_subdivision_level', subdivisions)

    compute_chunk_mode = __get_parameter_data(surface.compute_chunk_mode, frameno)
    if compute_chunk_mode == 'COMPUTE_CHUNK_MODE_AUTO':
        num_chunks = __get_parameter_data(surface.compute_chunks_auto, frameno)
    elif compute_chunk_mode == 'COMPUTE_CHUNK_MODE_FIXED':
        num_chunks = __get_parameter_data(surface.compute_chunks_fixed, frameno)
    __set_property(fluidsim, 'num_polygonizer_slices', num_chunks)

    particle_scale = __get_parameter_data(surface.particle_scale, frameno)
    particle_scale *= surface.native_particle_scale
    __set_property(fluidsim, 'marker_particle_scale', particle_scale)

    smoothing_value = __get_parameter_data(surface.smoothing_value, frameno)
    smoothing_iterations = __get_parameter_data(surface.smoothing_iterations, frameno)
    __set_property(fluidsim, 'surface_smoothing_value', smoothing_value)
    __set_property(fluidsim, 'surface_smoothing_iterations', smoothing_iterations)

    enable_meshing_offset = __get_parameter_data(surface.enable_meshing_offset, frameno)
    __set_property(fluidsim, 'enable_obstacle_meshing_offset', enable_meshing_offset)

    meshing_mode = __get_parameter_data(surface.obstacle_meshing_mode, frameno)
    meshing_offset = __get_obstacle_meshing_offset(meshing_mode)
    __set_property(fluidsim, 'obstacle_meshing_offset', meshing_offset)

    remove_near_domain = __get_parameter_data(surface.remove_mesh_near_domain, frameno)
    near_domain_distance = __get_parameter_data(surface.remove_mesh_near_domain_distance, frameno) - 1
    __set_property(fluidsim, 'enable_remove_surface_near_domain', remove_near_domain)
    __set_property(fluidsim, 'remove_surface_near_domain_distance', near_domain_distance)

    invert_contact = __get_parameter_data(surface.invert_contact_normals, frameno)
    __set_property(fluidsim, 'enable_inverted_contact_normals', invert_contact)

    motion_blur = __get_parameter_data(surface.generate_motion_blur_data, frameno)
    __set_property(fluidsim, 'enable_surface_motion_blur', motion_blur)

    # Advanced Settings

    advanced = dprops.advanced
    min_substeps, max_substeps = __get_parameter_data(advanced.min_max_time_steps_per_frame, frameno)
    __set_property(fluidsim, 'min_time_steps_per_frame', min_substeps)
    __set_property(fluidsim, 'max_time_steps_per_frame', max_substeps)

    enable_obstacle_time_stepping = \
        __get_parameter_data(advanced.enable_adaptive_obstacle_time_stepping, frameno)
    __set_property(fluidsim, 'enable_adaptive_obstacle_time_stepping', enable_obstacle_time_stepping)

    enable_force_field_time_stepping = \
        __get_parameter_data(advanced.enable_adaptive_force_field_time_stepping, frameno)
    __set_property(fluidsim, 'enable_adaptive_force_field_time_stepping', enable_force_field_time_stepping)

    jitter_factor = __get_parameter_data(advanced.particle_jitter_factor, frameno)
    __set_property(fluidsim, 'marker_particle_jitter_factor', jitter_factor)

    jitter_surface = __get_parameter_data(advanced.jitter_surface_particles, frameno)
    __set_property(fluidsim, 'jitter_surface_marker_particles', jitter_surface)

    PICFLIP_ratio = __get_parameter_data(advanced.PICFLIP_ratio, frameno)
    __set_property(fluidsim, 'PICFLIP_ratio', PICFLIP_ratio)

    PICAPIC_ratio = __get_parameter_data(advanced.PICAPIC_ratio, frameno)
    __set_property(fluidsim, 'PICAPIC_ratio', PICAPIC_ratio)

    CFL_number = __get_parameter_data(advanced.CFL_condition_number, frameno)
    __set_property(fluidsim, 'CFL_condition_number', CFL_number)

    enable_velocity_removal = __get_parameter_data(advanced.enable_extreme_velocity_removal, frameno)
    __set_property(fluidsim, 'enable_extreme_velocity_removal', enable_velocity_removal)

    threading_mode = __get_parameter_data(advanced.threading_mode, frameno)
    if threading_mode == 'THREADING_MODE_AUTO_DETECT':
        num_threads = __get_parameter_data(advanced.num_threads_auto_detect, frameno)
    elif threading_mode == 'THREADING_MODE_FIXED':
        num_threads = __get_parameter_data(advanced.num_threads_fixed, frameno)
    __set_property(fluidsim, 'max_thread_count', num_threads)

    enable_cl_scalar_field = __get_parameter_data(advanced.enable_gpu_features, frameno)
    enable_cl_advection = __get_parameter_data(advanced.enable_gpu_features, frameno)
    __set_property(fluidsim, 'enable_opencl_scalar_field', enable_cl_scalar_field)
    __set_property(fluidsim, 'enable_opencl_particle_advection', enable_cl_advection)

    enable_async_meshing = __get_parameter_data(advanced.enable_asynchronous_meshing, frameno)
    __set_property(fluidsim, 'enable_asynchronous_meshing', enable_async_meshing)

    precomp_static_sdf = __get_parameter_data(advanced.precompute_static_obstacles, frameno)
    __set_property(fluidsim, 'enable_static_solid_levelset_precomputation', precomp_static_sdf)

    reserve_temp_grids = __get_parameter_data(advanced.reserve_temporary_grids, frameno)
    __set_property(fluidsim, 'enable_temporary_mesh_levelset', reserve_temp_grids)

    # Debug Settings

    debug = dprops.debug
    export_internal_obstacle_mesh = __get_parameter_data(debug.export_internal_obstacle_mesh, frameno)
    __set_property(fluidsim, 'enable_internal_obstacle_mesh_output', export_internal_obstacle_mesh)

    # Caches created in older versions may not contain force field data. Ignore these features
    # if force field data cannot be found in the cache
    is_force_field_data_available = data.force_field_data is not None
    if is_force_field_data_available: 
        export_force_field = __get_parameter_data(debug.export_force_field, frameno)
        __set_property(fluidsim, 'enable_force_field_debug_output', export_force_field)


def __update_animatable_properties(fluidsim, data, frameno):
    __update_animatable_inflow_properties(data, frameno)
    __update_animatable_outflow_properties(data, frameno)
    __update_animatable_force_field_properties(data, frameno)
    __update_animatable_obstacle_properties(data, frameno)
    __update_animatable_meshing_volume_properties(data, frameno)
    __update_animatable_domain_properties(fluidsim, data, frameno)


def __frame_number_to_string(frameno):
        return str(frameno).zfill(6)


def __write_bounds_data(cache_directory, fluidsim, frameno):
    offset = fluidsim.get_domain_offset()
    scale = fluidsim.get_domain_scale()
    dims = fluidsim.get_simulation_dimensions()
    grid_dims = fluidsim.get_grid_dimensions()
    dx = fluidsim.get_cell_size()
    bounds = {
        "x": offset.x, "y": offset.y, "z": offset.z,
        "width": dims.x * scale,
        "height": dims.y * scale,
        "depth": dims.z * scale,
        "dx": dx * scale,
        "isize": grid_dims.i,
        "jsize": grid_dims.j,
        "ksize": grid_dims.k
    }
    fstring = __frame_number_to_string(frameno)
    bounds_filename = "bounds" + fstring + ".bbox"
    bounds_filepath = os.path.join(cache_directory, "bakefiles", bounds_filename)
    bounds_json = json.dumps(bounds)
    with open(bounds_filepath, 'w', encoding='utf-8') as f:
        f.write(bounds_json)


def __write_surface_data(cache_directory, fluidsim, frameno):
    fstring = __frame_number_to_string(frameno)

    surface_filename = fstring + ".bobj"
    surface_filepath = os.path.join(cache_directory, "bakefiles", surface_filename)
    filedata = fluidsim.get_surface_data()
    with open(surface_filepath, 'wb') as f:
        f.write(filedata)

    if fluidsim.enable_surface_motion_blur:
        blur_filename = "blur" + fstring + ".bobj"
        blur_filepath = os.path.join(cache_directory, "bakefiles", blur_filename)
        filedata = fluidsim.get_surface_blur_data()
        with open(blur_filepath, 'wb') as f:
            f.write(filedata)

    if fluidsim.enable_surface_velocity_attribute:
        velocity_filename = "velocity" + fstring + ".bobj"
        velocity_filepath = os.path.join(cache_directory, "bakefiles", velocity_filename)
        filedata = fluidsim.get_surface_velocity_attribute_data()
        with open(velocity_filepath, 'wb') as f:
            f.write(filedata)

    if fluidsim.enable_surface_speed_attribute:
        speed_filename = "speed" + fstring + ".data"
        speed_filepath = os.path.join(cache_directory, "bakefiles", speed_filename)
        filedata = fluidsim.get_surface_speed_attribute_data()
        with open(speed_filepath, 'wb') as f:
            f.write(filedata)

    if fluidsim.enable_surface_age_attribute:
        age_filename = "age" + fstring + ".data"
        age_filepath = os.path.join(cache_directory, "bakefiles", age_filename)
        filedata = fluidsim.get_surface_age_attribute_data()
        with open(age_filepath, 'wb') as f:
            f.write(filedata)

    if fluidsim.enable_surface_color_attribute:
        color_filename = "color" + fstring + ".bobj"
        color_filepath = os.path.join(cache_directory, "bakefiles", color_filename)
        filedata = fluidsim.get_surface_color_attribute_data()
        with open(color_filepath, 'wb') as f:
            f.write(filedata)

    if fluidsim.enable_surface_source_id_attribute:
        source_id_filename = "sourceid" + fstring + ".data"
        source_id_filepath = os.path.join(cache_directory, "bakefiles", source_id_filename)
        filedata = fluidsim.get_surface_source_id_attribute_data()
        with open(source_id_filepath, 'wb') as f:
            f.write(filedata)

    preview_filename = "preview" + fstring + ".bobj"
    preview_filepath = os.path.join(cache_directory, "bakefiles", preview_filename)
    filedata = fluidsim.get_surface_preview_data()
    with open(preview_filepath, 'wb') as f:
        f.write(filedata)


def __write_whitewater_data(cache_directory, fluidsim, frameno):
    fstring = __frame_number_to_string(frameno)

    foam_filename = "foam" + fstring + ".wwp"
    foam_filepath = os.path.join(cache_directory, "bakefiles", foam_filename)
    filedata = fluidsim.get_diffuse_foam_data()
    with open(foam_filepath, 'wb') as f:
        f.write(filedata)

    bubble_filename = "bubble" + fstring + ".wwp"
    bubble_filepath = os.path.join(cache_directory, "bakefiles", bubble_filename)
    filedata = fluidsim.get_diffuse_bubble_data()
    with open(bubble_filepath, 'wb') as f:
        f.write(filedata)

    spray_filename = "spray" + fstring + ".wwp"
    spray_filepath = os.path.join(cache_directory, "bakefiles", spray_filename)
    filedata = fluidsim.get_diffuse_spray_data()
    with open(spray_filepath, 'wb') as f:
        f.write(filedata)

    dust_filename = "dust" + fstring + ".wwp"
    dust_filepath = os.path.join(cache_directory, "bakefiles", dust_filename)
    filedata = fluidsim.get_diffuse_dust_data()
    with open(dust_filepath, 'wb') as f:
        f.write(filedata)

    if fluidsim.enable_whitewater_motion_blur:
        foam_blur_filename = "blurfoam" + fstring + ".wwp"
        foam_blur_filepath = os.path.join(cache_directory, "bakefiles", foam_blur_filename)
        filedata = fluidsim.get_diffuse_foam_blur_data()
        with open(foam_blur_filepath, 'wb') as f:
            f.write(filedata)

        bubble_blur_filename = "blurbubble" + fstring + ".wwp"
        bubble_blur_filepath = os.path.join(cache_directory, "bakefiles", bubble_blur_filename)
        filedata = fluidsim.get_diffuse_bubble_blur_data()
        with open(bubble_blur_filepath, 'wb') as f:
            f.write(filedata)

        spray_blur_filename = "blurspray" + fstring + ".wwp"
        spray_blur_filepath = os.path.join(cache_directory, "bakefiles", spray_blur_filename)
        filedata = fluidsim.get_diffuse_spray_blur_data()
        with open(spray_blur_filepath, 'wb') as f:
            f.write(filedata)

        dust_blur_filename = "blurdust" + fstring + ".wwp"
        dust_blur_filepath = os.path.join(cache_directory, "bakefiles", dust_blur_filename)
        filedata = fluidsim.get_diffuse_dust_blur_data()
        with open(dust_blur_filepath, 'wb') as f:
            f.write(filedata)


def __write_fluid_particle_data(cache_directory, fluidsim, frameno):
    fstring = __frame_number_to_string(frameno)

    particle_filename = "particles" + fstring + ".fpd"
    particle_filepath = os.path.join(cache_directory, "bakefiles", particle_filename)
    filedata = fluidsim.get_fluid_particle_data()
    with open(particle_filepath, 'wb') as f:
        f.write(filedata)


def __write_internal_obstacle_mesh_data(cache_directory, fluidsim, frameno):
    fstring = __frame_number_to_string(frameno)

    obstacle_filename = "obstacle" + fstring + ".bobj"
    obstacle_filepath = os.path.join(cache_directory, "bakefiles", obstacle_filename)
    filedata = fluidsim.get_internal_obstacle_mesh_data()
    with open(obstacle_filepath, 'wb') as f:
        f.write(filedata)


def __write_force_field_debug_data(cache_directory, fluidsim, frameno):
    fstring = __frame_number_to_string(frameno)

    force_field_filename = "forcefield" + fstring + ".ffd"
    force_field_filepath = os.path.join(cache_directory, "bakefiles", force_field_filename)
    filedata = fluidsim.get_force_field_debug_data()
    with open(force_field_filepath, 'wb') as f:
        f.write(filedata)


def __write_logfile_data(cache_directory, logfile_name, fluidsim):
    filedata = fluidsim.get_logfile_data()
    logpath = os.path.join(cache_directory, "logs", logfile_name)
    with open(logpath, 'a', encoding='utf-8') as f:
        f.write(filedata)


def __get_mesh_stats_dict(mstats):
    stats = {}
    stats["enabled"] = bool(mstats.enabled)
    stats["vertices"] = mstats.vertices
    stats["triangles"] = mstats.triangles
    stats["bytes"] = mstats.bytes
    return stats


def __get_timing_stats_dict(tstats):
    stats = {}
    stats["total"] = tstats.total
    stats["mesh"] = tstats.mesh
    stats["advection"] = tstats.advection
    stats["particles"] = tstats.particles
    stats["pressure"] = tstats.pressure
    stats["diffuse"] = tstats.diffuse
    stats["viscosity"] = tstats.viscosity
    stats["objects"] = tstats.objects
    return stats


def __get_frame_stats_dict(cstats):
    stats = {}
    stats["frame"] = cstats.frame
    stats["substeps"] = cstats.substeps
    stats["delta_time"] = cstats.delta_time
    stats["fluid_particles"] = cstats.fluid_particles
    stats["diffuse_particles"] = cstats.diffuse_particles
    stats["substeps"] = cstats.substeps
    stats["surface"] = __get_mesh_stats_dict(cstats.surface)
    stats["preview"] = __get_mesh_stats_dict(cstats.preview)
    stats["surfaceblur"] = __get_mesh_stats_dict(cstats.surfaceblur)
    stats["surfacevelocity"] = __get_mesh_stats_dict(cstats.surfacevelocity)
    stats["surfacespeed"] = __get_mesh_stats_dict(cstats.surfacespeed)
    stats["surfaceage"] = __get_mesh_stats_dict(cstats.surfaceage)
    stats["surfacecolor"] = __get_mesh_stats_dict(cstats.surfacecolor)
    stats["surfacesourceid"] = __get_mesh_stats_dict(cstats.surfacesourceid)
    stats["foam"] = __get_mesh_stats_dict(cstats.foam)
    stats["bubble"] = __get_mesh_stats_dict(cstats.bubble)
    stats["spray"] = __get_mesh_stats_dict(cstats.spray)
    stats["dust"] = __get_mesh_stats_dict(cstats.dust)
    stats["foamblur"] = __get_mesh_stats_dict(cstats.foamblur)
    stats["bubbleblur"] = __get_mesh_stats_dict(cstats.bubbleblur)
    stats["sprayblur"] = __get_mesh_stats_dict(cstats.sprayblur)
    stats["dustblur"] = __get_mesh_stats_dict(cstats.dustblur)
    stats["particles"] = __get_mesh_stats_dict(cstats.particles)
    stats["obstacle"] = __get_mesh_stats_dict(cstats.obstacle)
    stats["timing"] = __get_timing_stats_dict(cstats.timing)
    return stats


def __write_frame_stats_data(cache_directory, fluidsim, frameno):
    fstring = __frame_number_to_string(frameno)
    filename = "framestats" + fstring + ".data"
    tempdir =  os.path.join(cache_directory, "temp")
    statspath = os.path.join(tempdir, filename)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)

    cstats = fluidsim.get_frame_stats_data()
    stats = __get_frame_stats_dict(cstats)
    filedata = json.dumps(stats, sort_keys=True, indent=4)
    with open(statspath, 'w', encoding='utf-8') as f:
        f.write(filedata)


def __write_autosave_data(domain_data, cache_directory, fluidsim, frameno):
    autosave_dir = os.path.join(cache_directory, "savestates", "autosave")
    if not os.path.exists(autosave_dir):
        os.makedirs(autosave_dir)

    position_data_path = os.path.join(autosave_dir, "marker_particle_position.data")
    velocity_data_path = os.path.join(autosave_dir, "marker_particle_velocity.data")
    affinex_data_path = os.path.join(autosave_dir, "marker_particle_affinex.data")
    affiney_data_path = os.path.join(autosave_dir, "marker_particle_affiney.data")
    affinez_data_path = os.path.join(autosave_dir, "marker_particle_affinez.data")
    age_data_path = os.path.join(autosave_dir, "marker_particle_age.data")
    color_data_path = os.path.join(autosave_dir, "marker_particle_color.data")
    source_id_data_path = os.path.join(autosave_dir, "marker_particle_source_id.data")

    diffuse_position_data_path = os.path.join(autosave_dir, "diffuse_particle_position.data")
    diffuse_velocity_data_path = os.path.join(autosave_dir, "diffuse_particle_velocity.data")
    diffuse_lifetime_data_path = os.path.join(autosave_dir, "diffuse_particle_lifetime.data")
    diffuse_type_data_path = os.path.join(autosave_dir, "diffuse_particle_type.data")
    diffuse_id_data_path = os.path.join(autosave_dir, "diffuse_particle_id.data")
    autosave_info_path = os.path.join(autosave_dir, "autosave.state")
    temp_extension = ".backup"

    autosave_default_filepaths = [
            position_data_path,
            velocity_data_path,
            autosave_info_path
            ]
    autosave_apic_filepaths = [
            affinex_data_path,
            affiney_data_path,
            affinez_data_path
            ]
    autosave_age_filepaths = [
            age_data_path
            ]
    autosave_color_filepaths = [
            color_data_path
            ]
    autosave_source_id_filepaths = [
            source_id_data_path
            ]
    autosave_diffuse_filepaths = [
            diffuse_position_data_path,
            diffuse_velocity_data_path,
            diffuse_lifetime_data_path,
            diffuse_type_data_path,
            diffuse_id_data_path
            ]

    num_particles = fluidsim.get_num_marker_particles()
    marker_particles_per_write = 2**21
    num_marker_particle_writes = (num_particles // marker_particles_per_write) + 1
    try:
        for i in range(num_marker_particle_writes):
            start_idx = i * marker_particles_per_write
            end_idx = min((i + 1) * marker_particles_per_write, num_particles)
            is_appending = i != 0

            data = fluidsim.get_marker_particle_position_data_range(start_idx, end_idx)
            __write_save_state_file_data(position_data_path + temp_extension, data, is_appending_data=is_appending)
            data = fluidsim.get_marker_particle_velocity_data_range(start_idx, end_idx)
            __write_save_state_file_data(velocity_data_path + temp_extension, data, is_appending_data=is_appending)

            if fluidsim.is_velocity_transfer_method_APIC():
                data = fluidsim.get_marker_particle_affinex_data_range(start_idx, end_idx)
                __write_save_state_file_data(affinex_data_path + temp_extension, data, is_appending_data=is_appending)
                data = fluidsim.get_marker_particle_affiney_data_range(start_idx, end_idx)
                __write_save_state_file_data(affiney_data_path + temp_extension, data, is_appending_data=is_appending)
                data = fluidsim.get_marker_particle_affinez_data_range(start_idx, end_idx)
                __write_save_state_file_data(affinez_data_path + temp_extension, data, is_appending_data=is_appending)

            if fluidsim.enable_surface_age_attribute:
                data = fluidsim.get_marker_particle_age_data_range(start_idx, end_idx)
                __write_save_state_file_data(age_data_path + temp_extension, data, is_appending_data=is_appending)

            if fluidsim.enable_surface_color_attribute:
                data = fluidsim.get_marker_particle_color_data_range(start_idx, end_idx)
                __write_save_state_file_data(color_data_path + temp_extension, data, is_appending_data=is_appending)

            if fluidsim.enable_surface_source_id_attribute:
                data = fluidsim.get_marker_particle_source_id_data_range(start_idx, end_idx)
                __write_save_state_file_data(source_id_data_path + temp_extension, data, is_appending_data=is_appending)

        if fluidsim.get_num_diffuse_particles() > 0:
            num_particles = fluidsim.get_num_diffuse_particles()
            diffuse_particles_per_write = 2**21
            num_diffuse_particle_writes = (num_particles // diffuse_particles_per_write) + 1
            for i in range(num_diffuse_particle_writes):
                start_idx = i * diffuse_particles_per_write
                end_idx = min((i + 1) * diffuse_particles_per_write, num_particles)
                is_appending = i != 0

                data = fluidsim.get_diffuse_particle_position_data_range(start_idx, end_idx)
                __write_save_state_file_data(diffuse_position_data_path + temp_extension, data, is_appending_data=is_appending)
                data = fluidsim.get_diffuse_particle_velocity_data_range(start_idx, end_idx)
                __write_save_state_file_data(diffuse_velocity_data_path + temp_extension, data, is_appending_data=is_appending)
                data = fluidsim.get_diffuse_particle_lifetime_data_range(start_idx, end_idx)
                __write_save_state_file_data(diffuse_lifetime_data_path + temp_extension, data, is_appending_data=is_appending)
                data = fluidsim.get_diffuse_particle_type_data_range(start_idx, end_idx)
                __write_save_state_file_data(diffuse_type_data_path + temp_extension, data, is_appending_data=is_appending)
                data = fluidsim.get_diffuse_particle_id_data_range(start_idx, end_idx)
                __write_save_state_file_data(diffuse_id_data_path + temp_extension, data, is_appending_data=is_appending)

        init_data = domain_data.initialize
        frame_start, frame_end = init_data.frame_start, init_data.frame_end

        autosave_info = {}
        autosave_info['isize'] = init_data.isize
        autosave_info['jsize'] = init_data.jsize
        autosave_info['ksize'] = init_data.ksize
        autosave_info['dx'] = init_data.dx
        autosave_info['frame'] = frameno
        autosave_info['frame_start'] = frame_start
        autosave_info['frame_end'] = frame_end
        autosave_info['frame_id'] = fluidsim.get_current_frame() - 1
        autosave_info['last_frame_id'] = frame_end - frame_start
        autosave_info['num_marker_particles'] = fluidsim.get_num_marker_particles()
        autosave_info['marker_particle_position_filedata'] = "marker_particle_position.data"
        autosave_info['marker_particle_velocity_filedata'] = "marker_particle_velocity.data"
        autosave_info['num_diffuse_particles'] = fluidsim.get_num_diffuse_particles()

        autosave_info['marker_particle_affinex_filedata'] = ""
        autosave_info['marker_particle_affiney_filedata'] = ""
        autosave_info['marker_particle_affinez_filedata'] = ""

        autosave_info['marker_particle_age_filedata'] = ""
        autosave_info['marker_particle_color_filedata'] = ""
        autosave_info['marker_particle_source_id_filedata'] = ""

        autosave_info['diffuse_particle_position_filedata'] = ""
        autosave_info['diffuse_particle_velocity_filedata'] = ""
        autosave_info['diffuse_particle_lifetime_filedata'] = ""
        autosave_info['diffuse_particle_type_filedata'] = ""
        autosave_info['diffuse_particle_id_filedata'] = ""

        if fluidsim.is_velocity_transfer_method_APIC():
            autosave_info['marker_particle_affinex_filedata'] = "marker_particle_affinex.data"
            autosave_info['marker_particle_affiney_filedata'] = "marker_particle_affiney.data"
            autosave_info['marker_particle_affinez_filedata'] = "marker_particle_affinez.data"

        if fluidsim.enable_surface_age_attribute:
            autosave_info['marker_particle_age_filedata'] = "marker_particle_age.data"

        if fluidsim.enable_surface_color_attribute:
            autosave_info['marker_particle_color_filedata'] = "marker_particle_color.data"

        if fluidsim.enable_surface_source_id_attribute:
            autosave_info['marker_particle_source_id_filedata'] = "marker_particle_source_id.data"

        if fluidsim.get_num_diffuse_particles() > 0:
            autosave_info['diffuse_particle_position_filedata'] = "diffuse_particle_position.data"
            autosave_info['diffuse_particle_velocity_filedata'] = "diffuse_particle_velocity.data"
            autosave_info['diffuse_particle_lifetime_filedata'] = "diffuse_particle_lifetime.data"
            autosave_info['diffuse_particle_type_filedata'] = "diffuse_particle_type.data"
            autosave_info['diffuse_particle_id_filedata'] = "diffuse_particle_id.data"


        autosave_json = json.dumps(autosave_info, sort_keys=True, indent=4)
        with open(autosave_info_path + temp_extension, 'w', encoding='utf-8') as f:
            f.write(autosave_json)
    except Exception as e:
        print("FLIP Fluids: OS/Filesystem Error: Unable to write autosave files to storage")
        print("Error Message: ", e)
        print("Backup of the last successful autosave located here: <" + autosave_dir + ">")
        return

    try:
        data_filepaths = (
                          autosave_default_filepaths + 
                          autosave_apic_filepaths + 
                          autosave_age_filepaths + 
                          autosave_color_filepaths + 
                          autosave_source_id_filepaths + 
                          autosave_diffuse_filepaths
                          )
        for filepath in data_filepaths:
            if os.path.isfile(filepath):
                fpl.delete_file(filepath)
    except Exception as e:
        print("FLIP Fluids: OS/Filesystem Error: Unable to delete older autosave files from storage")
        print("Error Message: ", e)
        print("Backup of the last successful autosave located here: <" + autosave_dir + ">")
        return

    try:
        for filepath in autosave_default_filepaths:
            os.rename(filepath + temp_extension, filepath)
        if fluidsim.is_velocity_transfer_method_APIC():
            for filepath in autosave_apic_filepaths:
                os.rename(filepath + temp_extension, filepath)
        if fluidsim.enable_surface_age_attribute:
            for filepath in autosave_age_filepaths:
                os.rename(filepath + temp_extension, filepath)
        if fluidsim.enable_surface_color_attribute:
            for filepath in autosave_color_filepaths:
                os.rename(filepath + temp_extension, filepath)
        if fluidsim.enable_surface_source_id_attribute:
            for filepath in autosave_source_id_filepaths:
                os.rename(filepath + temp_extension, filepath)
        if fluidsim.get_num_diffuse_particles() > 0:
            for filepath in autosave_diffuse_filepaths:
                os.rename(filepath + temp_extension, filepath)
    except Exception as e:
        print("FLIP Fluids: OS/Filesystem Error: Unable to rename autosave files in storage")
        print("Error Message: ", e)
        print("Backup of the last successful autosave located here: <" + autosave_dir + ">")
        return

    init_data = domain_data.initialize
    if init_data.enable_savestates:
        interval = init_data.savestate_interval
        if (frameno + 1 - frame_start) % interval == 0 or frameno == frame_start:
            numstr = str(frameno).zfill(6)
            savestate_dir = os.path.join(cache_directory, "savestates", "autosave" + numstr)
            if os.path.isdir(savestate_dir):
                fpl.delete_files_in_directory(savestate_dir, [".state", ".data"], remove_directory=True)
            shutil.copytree(autosave_dir, savestate_dir)


def __write_simulation_output(domain_data, fluidsim, frameno, cache_directory):
    __write_bounds_data(cache_directory, fluidsim, frameno)
    __write_surface_data(cache_directory, fluidsim, frameno)

    if fluidsim.enable_diffuse_material_output:
        __write_whitewater_data(cache_directory, fluidsim, frameno)

    if fluidsim.enable_fluid_particle_output:
        __write_fluid_particle_data(cache_directory, fluidsim, frameno)

    if fluidsim.enable_internal_obstacle_mesh_output:
        __write_internal_obstacle_mesh_data(cache_directory, fluidsim, frameno)

    if fluidsim.enable_force_field_debug_output:
        __write_force_field_debug_data(cache_directory, fluidsim, frameno)

    __write_logfile_data(cache_directory, domain_data.initialize.logfile_name, fluidsim)
    __write_frame_stats_data(cache_directory, fluidsim, frameno)
    __write_autosave_data(domain_data, cache_directory, fluidsim, frameno)


def __get_current_frame_delta_time(domain_data, frameno):
    simdata = domain_data.simulation
    init_data = domain_data.initialize
    time_scale = __get_parameter_data(simdata.time_scale, frameno)
    fps = __get_parameter_data(simdata.frames_per_second, frameno)
    dt = (1.0 / fps) * time_scale
    return dt


def __run_simulation(fluidsim, data, cache_directory, bakedata):
    domain = data.domain_data
    init_data = domain.initialize
    num_frames = init_data.frame_end - init_data.frame_start + 1
    current_frame = fluidsim.get_current_frame()

    for i in range(current_frame, num_frames):
        simulator_frameno = fluidsim.get_current_frame()
        blender_frameno = simulator_frameno + init_data.frame_start

        geometry_database = __get_geometry_database()
        try:
            geometry_database.open()

            __update_animatable_properties(fluidsim, data, simulator_frameno)
            __add_fluid_objects(fluidsim, data, bakedata, simulator_frameno)

            geometry_database.close()
        except Exception:
            geometry_database.close()
            raise Exception

        dt = __get_current_frame_delta_time(domain, simulator_frameno)
        fluidsim.update(dt)

        if __check_bake_cancelled(bakedata):
            return

        bakedata.is_safe_to_exit = False
        __write_simulation_output(domain, fluidsim, blender_frameno, cache_directory)
        bakedata.is_safe_to_exit = True

        bakedata.completed_frames = simulator_frameno + 1
        bakedata.progress = (simulator_frameno + 1) / num_frames

        if __check_bake_cancelled(bakedata):
            return


def set_console_output(boolval):
    fluidsim_object = __get_simulation_object()
    if fluidsim_object is None or fluidsim_object._obj is None:
        return

    old_value = fluidsim_object.enable_console_output
    if fluidsim_object.enable_console_output == boolval:
        return

    fluidsim_object.enable_console_output = boolval


def __get_addon_version():
    module = sys.modules["flip_fluids_addon"]
    addon_major, addon_minor, addon_revision = module.bl_info.get('version', (-1, -1, -1))
    return str(addon_major) + "." + str(addon_minor) + "." + str(addon_revision)


def __get_engine_version(fluidsim):
    engine_major, engine_minor, engine_revision = fluidsim.get_version()
    return str(engine_major) + "." + str(engine_minor) + "." + str(engine_revision)


def __launch_bake(datafile, cache_directory, bakedata, savestate_id=None):
    __set_cache_directory(cache_directory)

    data = __extract_data(datafile)

    if data.domain_data.initialize.enable_engine_debug_mode:
        pyfluid.enable_debug_mode()
    else:
        pyfluid.disable_debug_mode()

    __set_simulation_data(data)

    db_filepath = __get_geometry_database_filepath()
    geometry_database = flip_fluid_geometry_database.GeometryDatabase(db_filepath)
    __set_geometry_database(geometry_database)

    if __check_bake_cancelled(bakedata):
        return

    __set_output_directories(cache_directory)

    init_data = data.domain_data.initialize
    fluidsim = FluidSimulation(init_data.isize, init_data.jsize, init_data.ksize, init_data.dx)
    __set_simulation_object(fluidsim)

    if __get_addon_version() != __get_engine_version(fluidsim):
        errmsg = ("The fluid engine version <" + __get_engine_version(fluidsim) + 
                  "> is not compatible with the addon version <" + 
                  __get_addon_version() + ">")
        raise LibraryVersionError(errmsg)

    if __check_bake_cancelled(bakedata):
        return

    geometry_database.open()
    __initialize_fluid_simulation(fluidsim, data, cache_directory, bakedata, savestate_id)
    geometry_database.close()

    if __check_bake_cancelled(bakedata):
        return

    __run_simulation(fluidsim, data, cache_directory, bakedata)


def bake(datafile, cache_directory, bakedata, savestate_id=None, bake_retries=0):
    max_baking_retries = bake_retries
    for retry_num in range(max_baking_retries + 1):
        try:
            __launch_bake(datafile, cache_directory, bakedata, savestate_id)

            print("------------------------------------------------------------")
            print("Simulation Ended.\nThank you for using FLIP Fluids!")
            print("------------------------------------------------------------")
            break

        except Exception as e:
            database = __get_geometry_database()
            database.close()

            error_string = str(e)
            errmsg = error_string
            if "std::bad_alloc" in errmsg:
                errmsg = "Out of memory. "
            elif not errmsg:
                errmsg = "Unknown error. "
            if not errmsg.endswith(". "):
                errmsg += ". "
            errmsg += "See system console for error info."
            traceback.print_exc()

            print("------------------------------------------------------------")
            print("SIMULATION TERMINATED DUE TO ERROR:")
            if "std::bad_alloc" in error_string:
                print("\tOut of Memory")
            else:
                print("\t" + error_string)
            print("\nThank you for using FLIP Fluids!")
            print("------------------------------------------------------------")

            if retry_num == max_baking_retries:
                bakedata.error_message = errmsg
                break
            else:
                retry_msg = "Attempting to re-launch bake... "
                retry_msg += "(retry attempt " + str(retry_num + 1) + "/" + str(max_baking_retries) + ")"
                print(retry_msg)

        __set_simulation_object(None)
        bakedata.is_finished = True
