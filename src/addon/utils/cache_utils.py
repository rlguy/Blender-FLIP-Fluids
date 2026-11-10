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

import bpy, os, struct, math, json, hashlib
import numpy as np

from ..types import DataType, MeshType


def string_to_cache_slug(string):
    max_hash_len = 16
    max_string_len = 64 - max_hash_len
    whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

    h = hashlib.md5()
    h.update(bytes(string, 'utf-8'))
    hexstr = h.hexdigest()
    hexstr = hexstr[:max_hash_len]

    slug = string[:max_string_len]
    slug = ''.join(c if c in whitelist else '-' for c in slug)
    slug += hexstr

    return slug


def is_domain_set():
    return bpy.context.scene.flip_fluid.get_domain_object() is not None


def get_domain_object():
    return bpy.context.scene.flip_fluid.get_domain_object()


def get_domain_properties():
    return bpy.context.scene.flip_fluid.get_domain_properties()


def get_cache_directory():
    if not is_domain_set():
        return
    dprops = get_domain_properties()
    return os.path.normpath(dprops.cache.get_cache_abspath())


def get_bakefiles_directory():
    cache_directory = get_cache_directory()
    return os.path.join(cache_directory, 'bakefiles')


def frame_number_to_string(frameno):
    return str(frameno).zfill(6)


def get_geometry_data_filepath(prefix, extension, frameno):
    bakefiles_directory = get_bakefiles_directory()
    filename = prefix + frame_number_to_string(frameno) + "." + extension
    return os.path.join(bakefiles_directory, filename)


def get_bakefile_filepath(mesh_type, mesh_name, attribute_name, data_type, frameno):
    frameno_str = frame_number_to_string(frameno)

    mt, dt = MeshType, DataType
    extension_type_map = {
        mt.SURFACE:         {dt.MESH: "bobj", dt.FLOAT_VECTOR: "bobj", dt.INT: "data", dt.FLOAT: "data", dt.UINT16: "data", dt.ULONGLONG: "data"},
        mt.OBSTACLE:        {dt.MESH: "bobj", dt.FLOAT_VECTOR: "bobj", dt.INT: "data", dt.FLOAT: "data", dt.UINT16: "data", dt.ULONGLONG: "data"},
        mt.FLUID_PARTICLES: {dt.MESH: "ffp3", dt.FLOAT_VECTOR: "ffp3", dt.INT: "ffp3", dt.FLOAT: "ffp3", dt.UINT16: "ffp3", dt.ULONGLONG: "ffp3"},
        mt.WHITEWATER:      {dt.MESH: "wwp",  dt.FLOAT_VECTOR: "wwp",  dt.INT: "wwi",  dt.FLOAT: "wwf",  dt.UINT16: "wwi",  dt.ULONGLONG: "wwi" },
        }

    if mesh_type in [mt.SURFACE, mt.OBSTACLE, mt.WHITEWATER]:
        filename_prefix = attribute_name + mesh_name
    elif mesh_type == mt.FLUID_PARTICLES:
        filename_prefix = mesh_name + attribute_name

    extension_str = extension_type_map[mesh_type][data_type]

    bakefiles_directory = get_bakefiles_directory()
    filename = filename_prefix + frameno_str + "." + extension_str
    filepath = os.path.join(bakefiles_directory, filename)

    return filepath


def get_import_bobj_arguments(filepath):
    return {"filepath": filepath}


def get_import_ffp3_arguments(filepath, mesh_cache, attribute_type):
    return {
        "filepath":       filepath, 
        "pct_surface":    mesh_cache.ffp3_surface_import_percentage, 
        "pct_boundary":   mesh_cache.ffp3_boundary_import_percentage, 
        "pct_interior":   mesh_cache.ffp3_interior_import_percentage, 
        "attribute_type": attribute_type
    }


def get_import_wwx_arguments(filepath, mesh_cache):
    return {
        "filepath": filepath,
        "percent":  mesh_cache.wwp_import_percentage,
    }


def import_bakefile_mesh_data(mesh_cache, mesh_type, mesh_name, attribute_name, frameno):
    vertices, triangles = [], []
    
    if not is_domain_set():
        return vertices, triangles

    filepath = get_bakefile_filepath(
        mesh_type=mesh_type, 
        mesh_name=mesh_name, 
        attribute_name=attribute_name, 
        data_type=DataType.MESH, 
        frameno=frameno
        )

    if not os.path.exists(filepath):
        return vertices, triangles

    import_function_map = {
        MeshType.SURFACE:         import_bobj,
        MeshType.OBSTACLE:        import_bobj,
        MeshType.FLUID_PARTICLES: import_ffp3_values,
        MeshType.WHITEWATER:      import_wwp,
        }

    import_function_arguments_map = {
            MeshType.SURFACE:         get_import_bobj_arguments(filepath),
            MeshType.OBSTACLE:        get_import_bobj_arguments(filepath),
            MeshType.FLUID_PARTICLES: get_import_ffp3_arguments(filepath, mesh_cache, DataType.FLOAT_VECTOR),
            MeshType.WHITEWATER:      get_import_wwx_arguments(filepath, mesh_cache),
        }

    import_function = import_function_map[mesh_type]
    import_arguments = import_function_arguments_map[mesh_type]
    import_data = import_function(**import_arguments)

    if isinstance(import_data, tuple):
        vertices = import_data[0]
        triangles = import_data[1]
    else:
        vertices = import_data

    return vertices, triangles


def import_bakefile_attribute_data(mesh_cache, mesh_type, mesh_name, attribute_name, data_type, frameno):
    attribute_data = []
    header_info = None

    if not is_domain_set():
        return attribute_data, header_info

    filepath = get_bakefile_filepath(
        mesh_type=mesh_type, 
        mesh_name=mesh_name, 
        attribute_name=attribute_name, 
        data_type=data_type, 
        frameno=frameno
        )

    if not os.path.exists(filepath):
        return attribute_data, header_info

    surface_import_function_map = {
        DataType.FLOAT_VECTOR: import_bobj_vertices,
        DataType.INT:          import_ints,
        DataType.FLOAT:        import_floats,
        DataType.UINT16:       import_ints,
        DataType.ULONGLONG:    import_ints,
        }

    whitewater_import_function_map = {
        DataType.FLOAT_VECTOR: import_wwp,
        DataType.INT:          import_wwi,
        DataType.FLOAT:        import_wwf,
        DataType.UINT16:       import_wwi,
        DataType.ULONGLONG:    import_wwi,
        }

    import_function_map = {
        MeshType.SURFACE:         surface_import_function_map[data_type],
        MeshType.OBSTACLE:        surface_import_function_map[data_type],
        MeshType.FLUID_PARTICLES: import_ffp3,
        MeshType.WHITEWATER:      whitewater_import_function_map[data_type],
        }

    import_function_arguments_map = {
        MeshType.SURFACE:         {"filepath": filepath},
        MeshType.OBSTACLE:        {"filepath": filepath},
        MeshType.FLUID_PARTICLES: get_import_ffp3_arguments(filepath, mesh_cache, data_type),
        MeshType.WHITEWATER:      get_import_wwx_arguments(filepath, mesh_cache),
    }

    import_function = import_function_map[mesh_type]
    import_arguments = import_function_arguments_map[mesh_type]
    import_data = import_function(**import_arguments)

    if isinstance(import_data, tuple):
        attribute_data = import_data[0]
        header_info = import_data[1]
    else:
        attribute_data = import_data

    return attribute_data, header_info


def import_bakefile_attribute_data_values(*args, **kwargs):
    attribute_values, _ = import_bakefile_attribute_data(*args, **kwargs)
    return attribute_values


def import_bobj(filepath):
    with open(filepath, "rb") as f:
        bobj_data = f.read()

    if len(bobj_data) == 0:
        return [], []

    data_offset = 0
    num_vertices = struct.unpack_from('i', bobj_data, data_offset)[0]
    data_offset += 4

    num_floats = 3 * num_vertices
    num_bytes = 4 * num_floats

    vertices = np.fromfile(filepath, dtype=np.float32, count=num_floats, offset=data_offset)

    data_offset += num_bytes

    num_triangles = struct.unpack_from('i', bobj_data, data_offset)[0]
    data_offset += 4

    num_ints = 3 * num_triangles
    num_bytes = 4 * num_ints

    triangles = np.fromfile(filepath, dtype=np.int32, count=num_ints, offset=data_offset)

    return vertices, triangles


def import_bobj_vertices(*args, **kwargs):
    vertices, _ = import_bobj(*args, **kwargs)
    return vertices


def import_ffp3(filepath, pct_surface=1.0, pct_boundary=1.0, pct_interior=1.0, attribute_type=None):
    with open(filepath, "rb") as f:
        attribute_data = f.read()

    attribute_values = []
    header_info_dict = None

    if len(attribute_data) == 0:
        return attribute_values, header_info_dict
    if pct_surface == 0.0 and pct_boundary == 0.0 and pct_interior == 0.0:
        return attribute_values, header_info_dict

    if attribute_type == DataType.FLOAT_VECTOR:
        sizeof_attribute = 12
        attribute_struct_format_str = '{0}f'
        numpy_type = np.float32
    elif attribute_type == DataType.INT:
        sizeof_attribute = 4
        attribute_struct_format_str = '{0}i'
        numpy_type = np.int32
    elif attribute_type == DataType.FLOAT:
        sizeof_attribute = 4
        attribute_struct_format_str = '{0}f'
        numpy_type = np.float32
    elif attribute_type == DataType.UINT16:
        sizeof_attribute = 2
        attribute_struct_format_str = '{0}H'
        numpy_type = np.uint16
    elif attribute_type == DataType.ULONGLONG:
        sizeof_attribute = 8
        attribute_struct_format_str = '{0}Q'
        numpy_type = np.ulonglong

    sizeof_uint = 4
    num_surface_particles  = struct.unpack_from('I', attribute_data, 0 * sizeof_uint)[0]
    num_boundary_particles = struct.unpack_from('I', attribute_data, 1 * sizeof_uint)[0]
    num_interior_particles = struct.unpack_from('I', attribute_data, 2 * sizeof_uint)[0]
    id_limit               = struct.unpack_from('I', attribute_data, 3 * sizeof_uint)[0]

    id_surface = int(math.ceil(pct_surface * (id_limit - 1)))
    id_boundary = int(math.ceil(pct_boundary * (id_limit - 1)))
    id_interior = int(math.ceil(pct_interior * (id_limit - 1)))

    id_data_byte_offset = 4 * sizeof_uint
    id_surface_byte_offset = id_data_byte_offset + id_surface * 3 * sizeof_uint + 0 * sizeof_uint
    id_boundary_byte_offset = id_data_byte_offset + id_boundary * 3 * sizeof_uint + 1 * sizeof_uint
    id_interior_byte_offset = id_data_byte_offset + id_interior * 3 * sizeof_uint + 2 * sizeof_uint

    num_surface_particles_to_read  = struct.unpack_from('I', attribute_data, id_surface_byte_offset)[0]
    num_boundary_particles_to_read = struct.unpack_from('I', attribute_data, id_boundary_byte_offset)[0]
    num_interior_particles_to_read = struct.unpack_from('I', attribute_data, id_interior_byte_offset)[0]

    tol = 1e-9
    if pct_surface < tol:
        num_surface_particles_to_read = 0
    if pct_boundary < tol:
        num_boundary_particles_to_read = 0
    if pct_interior < tol:
        num_interior_particles_to_read = 0

    particle_data_byte_offset = id_data_byte_offset + id_limit * 3 * sizeof_uint
    surface_particle_data_byte_offset = particle_data_byte_offset
    boundary_particle_data_byte_offset = surface_particle_data_byte_offset + num_surface_particles * sizeof_attribute
    interior_particle_data_byte_offset = boundary_particle_data_byte_offset + num_boundary_particles * sizeof_attribute

    if attribute_type == DataType.FLOAT_VECTOR:
        attribute_values = np.concatenate((
                np.fromfile(filepath, dtype=np.float32, count=3*num_surface_particles_to_read, offset=surface_particle_data_byte_offset),
                np.fromfile(filepath, dtype=np.float32, count=3*num_boundary_particles_to_read, offset=boundary_particle_data_byte_offset),
                np.fromfile(filepath, dtype=np.float32, count=3*num_interior_particles_to_read, offset=interior_particle_data_byte_offset)
                ))
    else:
        attribute_values = np.concatenate((
                np.fromfile(filepath, dtype=numpy_type, count=num_surface_particles_to_read, offset=surface_particle_data_byte_offset),
                np.fromfile(filepath, dtype=numpy_type, count=num_boundary_particles_to_read, offset=boundary_particle_data_byte_offset),
                np.fromfile(filepath, dtype=numpy_type, count=num_interior_particles_to_read, offset=interior_particle_data_byte_offset)
                ))

    header_info_dict = {}
    header_info_dict["num_surface_particles"] = num_surface_particles
    header_info_dict["num_boundary_particles"] = num_boundary_particles
    header_info_dict["num_interior_particles"] = num_interior_particles
    header_info_dict["id_limit"] = id_limit
    header_info_dict["num_surface_particles_to_read"] = num_surface_particles_to_read
    header_info_dict["num_boundary_particles_to_read"] = num_boundary_particles_to_read
    header_info_dict["num_interior_particles_to_read"] = num_interior_particles_to_read

    return attribute_values, header_info_dict


def import_ffp3_values(*args, **kwargs):
    attribute_values, _ = import_ffp3(*args, **kwargs)
    return attribute_values


def import_wwp(filepath, percent):
    vertices = []
    if percent == 0:
        return vertices

    with open(filepath, "rb") as f:
        wwp_data = f.read()

    if len(wwp_data) == 0:
        return vertices

    dataidx = int(math.ceil((percent / 100) * 255))
    num_vertices = struct.unpack_from('i', wwp_data, dataidx * 4)[0] + 1
    if num_vertices <= 0:
        return vertices
    num_floats = 3 * num_vertices
    data_offset = 256 * 4

    vertices = np.fromfile(filepath, dtype=np.float32, count=num_floats, offset=data_offset)

    return vertices


def import_wwi(filepath, percent):
    int_values = []
    if percent == 0:
        return int_values

    with open(filepath, "rb") as f:
        wwi_data = f.read()

    if len(wwi_data) == 0:
        return int_values

    dataidx = int(math.ceil((percent / 100) * 255))
    num_vertices = struct.unpack_from('i', wwi_data, dataidx * 4)[0] + 1
    if num_vertices <= 0:
        return int_values

    num_ints = num_vertices
    data_offset = 256 * 4
    int_values = np.fromfile(filepath, dtype=np.int32, count=num_ints, offset=data_offset)

    return int_values


def import_wwf(filepath, percent):
    float_values = []
    if percent == 0:
        return float_values

    with open(filepath, "rb") as f:
        wwi_data = f.read()

    if len(wwi_data) == 0:
        return float_values

    dataidx = int(math.ceil((percent / 100) * 255))
    num_vertices = struct.unpack_from('i', wwi_data, dataidx * 4)[0] + 1
    if num_vertices <= 0:
        return float_values

    num_floats = num_vertices
    data_offset = 256 * 4
    float_values = np.fromfile(filepath, dtype=np.float32, count=num_floats, offset=data_offset)
    triangles = float_values

    return float_values


def import_ffd(filepath):
    if not os.path.exists(filepath):
        return None

    with open(filepath, "rb") as f:
        ffd_data = f.read()

    if len(ffd_data) == 0:
        return None

    data_offset = 0
    num_vertices = struct.unpack_from('i', ffd_data, data_offset)[0]
    data_offset += 4

    if num_vertices == 0:
        return None

    num_floats = 4 * num_vertices
    num_bytes = 4 * num_floats
    it = iter(struct.unpack_from('{0}f'.format(num_floats), ffd_data, data_offset))
    vertices = list(zip(it, it, it, it))
    data_offset += num_bytes

    return vertices


def import_fpd(filepath):
    particles, binstarts, binspeeds = [], [], []

    if not os.path.exists(filepath):
        return particles, binstarts, binspeeds

    with open(filepath, "rb") as f:
        fpd_data = f.read()

    if len(fpd_data) == 0:
        return particles, binstarts, binspeeds

    data_offset = 0
    num_particles = struct.unpack_from('i', fpd_data, data_offset)[0]
    data_offset += 4

    num_floats = 3 * num_particles
    num_bytes = 4 * num_floats
    it = iter(struct.unpack_from('{0}f'.format(num_floats), fpd_data, data_offset))
    particles = list(zip(it, it, it))
    data_offset += num_bytes

    num_bins = struct.unpack_from('i', fpd_data, data_offset)[0]
    data_offset += 4

    num_floats = num_bins
    num_bytes = 4 * num_floats
    binstarts = struct.unpack_from('{0}i'.format(num_floats), fpd_data, data_offset)
    data_offset += num_bytes

    num_floats = num_bins
    num_bytes = 4 * num_floats
    binspeeds = struct.unpack_from('{0}f'.format(num_floats), fpd_data, data_offset)
    data_offset += num_bytes

    return particles, binstarts, binspeeds


def import_floats(filepath):
    floats = []

    datasize = os.path.getsize(filepath) 
    if datasize == 0:
        return floats

    num_floats = datasize // 4
    floats = np.fromfile(filepath, dtype=np.float32, count=num_floats, offset=0)

    return floats


def import_ints(filepath):
    ints = []

    datasize = os.path.getsize(filepath) 
    if datasize == 0:
        return ints

    num_ints = datasize // 4
    ints = np.fromfile(filepath, dtype=np.int32, count=num_ints, offset=0)

    return ints


def import_data_type(filepath, data_type=""):
    values = []
    if data_type == 'INT':
        values = import_ints(filepath)
    elif data_type == 'FLOAT':
        values = import_floats(filepath)
    return values


def import_bbox(filepath):
    bbox_dict = None
    with open(filepath, 'r', encoding='utf-8') as f:
        bbox_dict = json.loads(f.read())
    return bbox_dict