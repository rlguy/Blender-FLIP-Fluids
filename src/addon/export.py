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

import bpy, math, array, json, os, zipfile, shutil
from mathutils import Vector

from .objects import flip_fluid_map
from .utils import export_utils as utils
from .objects.flip_fluid_aabb import AABB
from .pyfluid import TriangleMesh
from .utils import version_compatibility_utils as vcu


def __get_domain_object():
    return bpy.context.scene.flip_fluid.get_domain_object()


def __get_domain_properties():
    return bpy.context.scene.flip_fluid.get_domain_properties()


def __export_simulation_data_to_file(context, simobjects, filename):
    data = __get_simulation_data_dict(context, simobjects)
    jsonstr = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(jsonstr)


def __get_simulation_data_dict(context, simobjects):
    data = {}
    data['domain_data'] = __get_domain_data_dict(context, simobjects.domain)
    data['fluid_data'] = __get_fluid_data(context, simobjects.fluid_objects)
    data['obstacle_data'] = __get_obstacle_data(context, simobjects.obstacle_objects)
    data['inflow_data'] = __get_inflow_data(context, simobjects.inflow_objects)
    data['outflow_data'] = __get_outflow_data(context, simobjects.outflow_objects)
    return data


def __get_domain_data_dict(context, dobj):
    dprops = dobj.flip_fluid.domain
    d = utils.flip_fluid_object_to_dict(dobj, dprops)

    initialize_properties = {}
    initialize_properties['name'] = dobj.name

    bbox = AABB.from_blender_object(dobj)
    isize, jsize, ksize, dx = dprops.simulation.get_grid_dimensions()
    preview_dx = dprops.simulation.get_preview_dx()

    initialize_properties['isize'] = isize
    initialize_properties['jsize'] = jsize
    initialize_properties['ksize'] = ksize

    dwidth = initialize_properties['isize'] * dx
    dheight = initialize_properties['jsize'] * dx
    ddepth = initialize_properties['ksize'] * dx
    initialize_properties['bbox'] = AABB(bbox.x, bbox.y, bbox.z, 
                                         dwidth, dheight, ddepth).to_dict()
    initialize_properties['scale'] = dprops.world.get_world_scale()
    initialize_properties['dx'] = dx * initialize_properties['scale']
    initialize_properties['preview_dx'] = preview_dx * initialize_properties['scale']

    initialize_properties['logfile_name'] = dprops.cache.logfile_name
    initialize_properties['frame_start'] = dprops.simulation.frame_start
    initialize_properties['frame_end'] = dprops.simulation.frame_end

    initialize_properties['enable_savestates'] = dprops.simulation.enable_savestates
    initialize_properties['savestate_interval'] = dprops.simulation.savestate_interval
    initialize_properties['delete_outdated_savestates'] = dprops.simulation.delete_outdated_savestates
    initialize_properties['delete_outdated_meshes'] = dprops.simulation.delete_outdated_meshes

    id_name = __name__.split(".")[0]
    preferences = vcu.get_blender_preferences(context).addons[id_name].preferences
    if len(preferences.gpu_devices) > 0:
        initialize_properties['gpu_device'] = preferences.selected_gpu_device
    else:
        initialize_properties['gpu_device'] = ""
        
    d['initialize'] = initialize_properties

    d['advanced']['num_threads_auto_detect'] = dprops.advanced.num_threads_auto_detect
    d['world']['gravity'] = dprops.world.get_gravity_data_dict()
    d['world']['native_surface_tension_scale'] = dprops.world.native_surface_tension_scale
    d['world']['minimum_surface_tension_cfl'] = dprops.world.minimum_surface_tension_cfl
    d['world']['maximum_surface_tension_cfl'] = dprops.world.maximum_surface_tension_cfl
    d['surface']['native_particle_scale'] = dprops.surface.native_particle_scale
    d['surface']['compute_chunks_auto'] = dprops.surface.compute_chunks_auto

    volume_object_name = ""
    if dprops.surface.meshing_volume_object:
        volume_object_name = dprops.surface.meshing_volume_object.name
    d['surface']['meshing_volume_object'] = volume_object_name

    return d


def __get_fluid_data(context, objects):
    d = []
    for idx, obj in enumerate(objects):
        fprops = obj.flip_fluid.fluid
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.fluid)
        data['name'] = obj.name

        target_object = fprops.get_target_object()
        target_object_name = ""
        if target_object:
            target_object_name = target_object.name
        data['target_object'] = target_object_name

        d.append(data)

    return d


def __get_obstacle_data(context, objects):
    d = []
    for idx, obj in enumerate(objects):
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.obstacle)
        data['name'] = obj.name
        d.append(data)

    return d


def __get_inflow_data(context, objects):
    d = []
    for idx, obj in enumerate(objects):
        props = obj.flip_fluid.inflow
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.inflow)
        data['name'] = obj.name

        target_object = props.get_target_object()
        target_object_name = ""
        if target_object:
            target_object_name = target_object.name
        data['target_object'] = target_object_name

        d.append(data)

    return d


def __get_outflow_data(context, objects):
    d = []
    for idx, obj in enumerate(objects):
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.outflow)
        data['name'] = obj.name
        d.append(data)

    return d


def __format_bytes(num):
    # Method adapted from: http://stackoverflow.com/a/10171475
    unit_list = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']
    decimal_list = [0, 0, 1, 2, 2, 2]

    if num > 1:
        exponent = min(int(math.log(num, 1024)), len(unit_list) - 1)
        quotient = float(num) / 1024**exponent
        unit, num_decimals = unit_list[exponent], decimal_list[exponent]
        format_string = '{:.%sf} {}' % (num_decimals)
        return format_string.format(quotient, unit)
    if num == 0:
        return '0 bytes'
    if num == 1:
        return '1 byte'


def __export_static_mesh_data(object_data, mesh_directory):
    mesh_data = object_data['data']['mesh_data']
    bobj_data = mesh_data.to_bobj()
    filepath = os.path.join(mesh_directory, "mesh.bobj")
 
    with open(filepath, 'wb') as mesh_file:
            mesh_file.write(bobj_data)

    info = {'mesh_type': 'STATIC'}
    info_json = json.dumps(info, sort_keys=True)
    info_filepath = os.path.join(mesh_directory, "mesh.info")
    with open(info_filepath, "w") as f:
        f.write(info_json)

    dprops = __get_domain_properties()
    if dprops.debug.display_console_output:
        export_str = "Exporting static mesh: <" + object_data['name'] + ">, "
        export_str += "verts: " + str(len(mesh_data.vertices) // 3)
        export_str += ", tris: " + str(len(mesh_data.triangles) // 3)
        export_str += ", filesize: " + __format_bytes(len(bobj_data))
        print(export_str)

    object_data['data']['mesh_data'] = None


def __export_keyframed_mesh_data(object_data, mesh_directory):
    mesh_data = object_data['data']['mesh_data']
    bobj_data = mesh_data.to_bobj()
    mesh_filepath = os.path.join(mesh_directory, "mesh.bobj")
    with open(mesh_filepath, 'wb') as mesh_file:
            mesh_file.write(bobj_data)

    matrix_data = object_data['data']['matrix_data']
    matrix_json = json.dumps(matrix_data)
    matrix_filepath = os.path.join(mesh_directory, "transforms.data")
    with open(matrix_filepath, "w") as f:
        f.write(matrix_json)

    info = {
            'mesh_type': 'KEYFRAMED', 
            'frame_start': min(matrix_data.keys()), 
            'frame_end': max(matrix_data.keys())
            }
    info_json = json.dumps(info, sort_keys=True)
    info_filepath = os.path.join(mesh_directory, "mesh.info")
    with open(info_filepath, "w") as f:
        f.write(info_json)

    matrix_filesize = os.stat(matrix_filepath).st_size 
    filesize = len(bobj_data) + matrix_filesize

    dprops = __get_domain_properties()
    if dprops.debug.display_console_output:
        export_str = "Exporting keyframed mesh: <" + object_data['name'] + ">, "
        export_str += "numframes: " + str(len(matrix_data))
        export_str += ", verts: " + str(len(mesh_data.vertices) // 3)
        export_str += ", tris: " + str(len(mesh_data.triangles) // 3)
        export_str += ", filesize: " + __format_bytes(filesize)
        print(export_str)

    object_data['data']['mesh_data'] = None
    object_data['data']['matrix_data'] = None


def __export_animated_mesh_data(object_data, mesh_directory):
    mesh_data = object_data['data']['mesh_data']
    frame_data = object_data['data']['frame_data']

    dprops = __get_domain_properties()
    for i, mesh in enumerate(mesh_data):
        bobj_data = mesh.to_bobj()
        frameno = frame_data[i]
        mesh_name = "mesh" + str(frameno).zfill(6) + ".bobj"
        filepath = os.path.join(mesh_directory, mesh_name)

        with open(filepath, 'wb') as mesh_file:
            mesh_file.write(bobj_data)

        if dprops.debug.display_console_output:
            export_str = "Exporting animated mesh: <" + object_data['name'] + ">, "
            export_str += "frame: " + str(frameno)
            export_str += ", verts: " + str(len(mesh.vertices) // 3)
            export_str += ", tris: " + str(len(mesh.triangles) // 3)
            export_str += ", filesize: " + __format_bytes(len(bobj_data))
            print(export_str)

    files = os.listdir(mesh_directory)
    files = [f.split('.')[0][-6:] for f in files]
    file_numbers = [int(f) for f in files if f.isdigit()]

    info = {
            'mesh_type': 'ANIMATED', 
            'frame_start': min(file_numbers), 
            'frame_end': max(file_numbers)
            }
    info_json = json.dumps(info, sort_keys=True)
    info_filepath = os.path.join(mesh_directory, "mesh.info")
    with open(info_filepath, "w") as f:
        f.write(info_json)

    object_data['data']['mesh_data'] = []
    frame_data = object_data['data']['frame_data'] = []


def export_mesh_data(mesh_exporter_data, export_directory):
    os.makedirs(export_directory, exist_ok=True)

    for object_name, object_data in mesh_exporter_data.items():
        if not object_data['data']['mesh_data']:
            continue

        mesh_directory = os.path.join(export_directory, object_name)
        os.makedirs(mesh_directory, exist_ok=True)

        mesh_type = object_data['data']['mesh_type']
        if mesh_type == 'STATIC':
            __export_static_mesh_data(object_data, mesh_directory)
        elif mesh_type == 'KEYFRAMED':
            __export_keyframed_mesh_data(object_data, mesh_directory)
        elif mesh_type == 'ANIMATED':
            __export_animated_mesh_data(object_data, mesh_directory)


def clean_export_directory(export_object_names, export_directory):
    os.makedirs(export_directory, exist_ok=True)
    dprops = __get_domain_properties()

    subdirs = [x for x in os.listdir(export_directory) if os.path.isdir(os.path.join(export_directory, x))]
    for d in subdirs:
        if not d in export_object_names:
            shutil.rmtree(os.path.join(export_directory, d))

    for name in export_object_names:
        object_dir = os.path.join(export_directory, name)
        if not os.path.isdir(object_dir):
            continue
        obj = bpy.data.objects.get(name)
        props = obj.flip_fluid.get_property_group()
        if not props.export_animated_mesh:
            shutil.rmtree(object_dir)
        if props.export_animated_mesh and not props.skip_animated_mesh_reexport:
            shutil.rmtree(object_dir)


def get_mesh_exporter_parameter_dict(export_object_names, export_directory):
    dprops = __get_domain_properties()
    frame_start, frame_end = dprops.simulation.get_frame_range()
    mesh_data = {}
    for name in export_object_names:
        object_dir = os.path.join(export_directory, name)
        obj = bpy.data.objects.get(name)
        props = obj.flip_fluid.get_property_group()

        if props.export_animated_mesh and props.skip_animated_mesh_reexport:
            if not os.path.isdir(object_dir):
                mesh_data[name] = {'frame_start': frame_start, 'frame_end': frame_end}
                continue

            files = os.listdir(object_dir)
            files = [f.split('.')[0][-6:] for f in files]
            file_numbers = [int(f) for f in files if f.isdigit()]
            file_numbers.sort()

            if not file_numbers or frame_start < file_numbers[0]:
                mesh_data[name] = {'frame_start': frame_start, 'frame_end': frame_end}
                continue

            next_number = file_numbers[-1] + 1
            mesh_data[name] = {'frame_start': next_number, 'frame_end': frame_end}
        else:
            mesh_data[name] = {'frame_start': frame_start, 'frame_end': frame_end}

    return mesh_data



def export_simulation_data(context, data_filepath):
    domain_object = __get_domain_object()
    dprops = __get_domain_properties()
    if domain_object is None:
        return False

    simprops = bpy.context.scene.flip_fluid

    simulation_objects = flip_fluid_map.Map({})
    simulation_objects.domain = domain_object
    simulation_objects.fluid_objects = simprops.get_fluid_objects()
    simulation_objects.obstacle_objects = simprops.get_obstacle_objects()
    simulation_objects.inflow_objects = simprops.get_inflow_objects()
    simulation_objects.outflow_objects = simprops.get_outflow_objects()

    __export_simulation_data_to_file(context, simulation_objects, data_filepath)

    return True
