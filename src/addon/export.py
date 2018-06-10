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

import bpy, math, array, json, os, zipfile
from mathutils import Vector

from .objects import flip_fluid_map
from .utils import export_utils as utils
from .objects.flip_fluid_aabb import AABB
from .pyfluid import TriangleMesh


def __get_domain_object():
    return bpy.context.scene.flip_fluid.get_domain_object()


def __get_domain_properties():
    return bpy.context.scene.flip_fluid.get_domain_properties()


def __export_simulation_data_to_file(context, simobjects, filename):
    data = __get_simulation_data_dict(context, simobjects)
    jsonstr = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        try:
            import zlib
            compression_mode = zipfile.ZIP_DEFLATED
        except:
            compression_mode = zipfile.ZIP_STORED

        zfile = zipfile.ZipFile(f, 'w', compression_mode)
        zfile.writestr("data.json", jsonstr)

        for i in range(len(data['fluid_data'])):
            fluid_data = data['fluid_data'][i]
            if fluid_data['is_animated']:
                mesh_data = simobjects.fluid_meshes[i]
                for midx, tmesh in enumerate(mesh_data['data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = fluid_data['mesh_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)

                for midx, tmesh in enumerate(mesh_data['translation_data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = fluid_data['translation_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)
            else:
                bobj_data = simobjects.fluid_meshes[i]['data'].to_bobj()
                zfile.writestr(fluid_data['mesh_data_file'], bobj_data)

        for i in range(len(data['obstacle_data'])):
            obstacle_data = data['obstacle_data'][i]
            if obstacle_data['is_animated']:
                mesh_data = simobjects.obstacle_meshes[i]
                for midx, tmesh in enumerate(mesh_data['data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = obstacle_data['mesh_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)

                for midx, tmesh in enumerate(mesh_data['translation_data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = obstacle_data['translation_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)
            else:
                bobj_data = simobjects.obstacle_meshes[i]['data'].to_bobj()
                zfile.writestr(obstacle_data['mesh_data_file'], bobj_data)

        for i in range(len(data['inflow_data'])):
            inflow_data = data['inflow_data'][i]
            if inflow_data['is_animated']:
                mesh_data = simobjects.inflow_meshes[i]
                for midx, tmesh in enumerate(mesh_data['data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = inflow_data['mesh_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)

                for midx, tmesh in enumerate(mesh_data['translation_data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = inflow_data['translation_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)
            else:
                bobj_data = simobjects.inflow_meshes[i]['data'].to_bobj()
                zfile.writestr(inflow_data['mesh_data_file'], bobj_data)

        for i in range(len(data['outflow_data'])):
            outflow_data = data['outflow_data'][i]
            if outflow_data['is_animated']:
                mesh_data = simobjects.outflow_meshes[i]
                for midx, tmesh in enumerate(mesh_data['data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = outflow_data['mesh_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)

                for midx, tmesh in enumerate(mesh_data['translation_data']):
                    bobj_data = tmesh.to_bobj()
                    file_name = outflow_data['translation_data_file'][midx]
                    zfile.writestr(file_name, bobj_data)
            else:
                bobj_data = simobjects.outflow_meshes[i]['data'].to_bobj()
                zfile.writestr(outflow_data['mesh_data_file'], bobj_data)

        zfile.close()


def __get_simulation_data_dict(context, simobjects):
    data = {}
    data['domain_data'] = __get_domain_data_dict(context, simobjects.domain)
    data['fluid_data'] = __get_fluid_data(
            context, 
            simobjects.fluid_objects,
            simobjects.fluid_meshes,
            simobjects.export_mesh_dict
            )
    data['obstacle_data'] = __get_obstacle_data(
            context, 
            simobjects.obstacle_objects,
            simobjects.obstacle_meshes
            )
    data['inflow_data'] = __get_inflow_data(
            context, 
            simobjects.inflow_objects,
            simobjects.inflow_meshes,
            simobjects.export_mesh_dict
            )
    data['outflow_data'] = __get_outflow_data(
            context, 
            simobjects.outflow_objects,
            simobjects.outflow_meshes
            )

    return data


def __get_domain_data_dict(context, dobj):
    dprops = dobj.flip_fluid.domain
    d = utils.flip_fluid_object_to_dict(dobj, dprops)

    initialize_properties = {}
    initialize_properties['name'] = dobj.name

    bbox = AABB.from_blender_object(dobj)
    max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
    if dprops.simulation.lock_cell_size:
        unlocked_dx = max_dim / dprops.simulation.resolution
        locked_dx = dprops.simulation.locked_cell_size
        dx = locked_dx
        if abs(locked_dx - unlocked_dx) < 1e-6:
            dx = unlocked_dx
    else:
        dx = max_dim / dprops.simulation.resolution
    preview_dx = max_dim / dprops.simulation.preview_resolution
    initialize_properties['isize'] = math.ceil(bbox.xdim / dx)
    initialize_properties['jsize'] = math.ceil(bbox.ydim / dx)
    initialize_properties['ksize'] = math.ceil(bbox.zdim / dx)

    dwidth = initialize_properties['isize'] * dx
    dheight = initialize_properties['jsize'] * dx
    ddepth = initialize_properties['ksize'] * dx
    initialize_properties['bbox'] = AABB(bbox.x, bbox.y, bbox.z, 
                                         dwidth, dheight, ddepth).to_dict()
    initialize_properties['scale'] = __get_domain_scale(bbox, dprops)
    initialize_properties['dx'] = dx * initialize_properties['scale']
    initialize_properties['preview_dx'] = preview_dx * initialize_properties['scale']

    initialize_properties['logfile_name'] = dprops.cache.logfile_name
    initialize_properties['frame_start'] = dprops.simulation.frame_start
    initialize_properties['frame_end'] = dprops.simulation.frame_end

    id_name = __name__.split(".")[0]
    preferences = bpy.context.user_preferences.addons[id_name].preferences
    if len(preferences.gpu_devices) > 0:
        initialize_properties['gpu_device'] = preferences.selected_gpu_device
    else:
        initialize_properties['gpu_device'] = ""
        
    d['initialize'] = initialize_properties

    d['advanced']['num_threads_auto_detect'] = dprops.advanced.num_threads_auto_detect
    d['world']['gravity'] = dprops.world.get_gravity_data_dict()
    d['surface']['native_particle_scale'] = dprops.surface.native_particle_scale
    d['surface']['compute_chunks_auto'] = dprops.surface.compute_chunks_auto

    return d


def __get_centroid_from_triangle_mesh(mesh):
    sumx = sumy = sumz = 0
    for i in range(0, len(mesh.vertices), 3):
        sumx += mesh.vertices[i]
        sumy += mesh.vertices[i + 1]
        sumz += mesh.vertices[i + 2]

    num_verts = len(mesh.vertices) // 3
    return Vector((sumx / num_verts, sumy / num_verts, sumz / num_verts))


def __get_centroid_data_dict_from_mesh_data_dict(mesh_data):
    if mesh_data['is_animated']:
        cdata = []
        for m in mesh_data['data']:
            cdata.append(__get_centroid_from_triangle_mesh(m))
        return {'is_animated' : True, 'data' : cdata}
    else:
        cdata = __get_centroid_from_triangle_mesh(mesh_data['data'])
        return {'is_animated' : False, 'data' : cdata}


def __get_velocity_target_data_dict(mesh_data1, mesh_data2, speed_data):
    centroid_data1 = __get_centroid_data_dict_from_mesh_data_dict(mesh_data1)
    centroid_data2 = __get_centroid_data_dict_from_mesh_data_dict(mesh_data2)

    is_animated = (centroid_data1['is_animated'] or 
                   centroid_data2['is_animated'] or 
                   speed_data['is_animated'])

    if is_animated:
        num_vals = 0
        if centroid_data1['is_animated']:
            num_vals = max(num_vals, len(centroid_data1['data']))
        if centroid_data2['is_animated']:
            num_vals = max(num_vals, len(centroid_data2['data']))
        if speed_data['is_animated']:
            num_vals = max(num_vals, len(speed_data['data']))

        utils.convert_to_animated_data_dict(centroid_data1, num_vals)
        utils.convert_to_animated_data_dict(centroid_data2, num_vals)
        utils.convert_to_animated_data_dict(speed_data, num_vals)

        velocities = []
        for i in range(num_vals):
            ndir = (centroid_data2['data'][i] - centroid_data1['data'][i]).normalized()
            velocity = speed_data['data'][i] * ndir
            velocity = [velocity[0], velocity[1], velocity[2]]
            velocities.append(velocity)

        return {'is_animated' : True, 'data' : velocities}
        
    else:
        ndir = (centroid_data2['data'] - centroid_data1['data']).normalized()
        velocity = speed_data['data'] * ndir
        velocity = [velocity[0], velocity[1], velocity[2]]

        return {'is_animated' : False, 'data' : velocity}


def __get_fluid_velocity_data_dict(obj, mesh_data_dict):
    fluid_props = obj.flip_fluid.fluid
    if not fluid_props.is_target_valid():
        return utils.get_vector_property_data_dict(obj, fluid_props, 'initial_velocity')

    object_mesh_data = mesh_data_dict[obj.name].data
    target_mesh_data = mesh_data_dict[fluid_props.target_object].data
    speed_data = utils.get_property_data_dict(obj, fluid_props, 'initial_speed')

    return __get_velocity_target_data_dict(object_mesh_data, target_mesh_data, speed_data)


def __get_mesh_data_file_path_data(base_path, mesh_data):
    mesh_file_path_data = None
    translation_file_path_data = None
    if mesh_data['is_animated']:
        mesh_file_path_data = []
        translation_file_path_data = []
        for i in range(len(mesh_data['data'])):
                numstr = str(i).zfill(6)
                mesh_path = base_path + "mesh" + numstr + ".bobj"
                translation_path = base_path + "translation" + numstr + ".bobj"
                mesh_file_path_data.append(mesh_path)
                translation_file_path_data.append(translation_path)
    else:
        mesh_file_path_data = base_path + "mesh.bobj"

    return mesh_file_path_data, translation_file_path_data


def __get_fluid_data(context, objects, meshes, mesh_data_dict):
    d = []
    for idx, obj in enumerate(objects):
        fprops = obj.flip_fluid.fluid
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.fluid)
        data['name'] = obj.name
        data['initial_velocity'] = __get_fluid_velocity_data_dict(obj, mesh_data_dict)

        mesh_data = meshes[idx]
        base_path = "fluid_data/" + obj.name + "/"
        mesh_file_path_data, translation_file_data = \
            __get_mesh_data_file_path_data(base_path, mesh_data)

        data['mesh_data_file'] = mesh_file_path_data
        data['translation_data_file'] = translation_file_data
        data['is_animated'] = mesh_data['is_animated']

        d.append(data)

    return d


def __get_obstacle_data(context, objects, meshes):
    d = []
    for idx, obj in enumerate(objects):
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.obstacle)
        data['name'] = obj.name

        mesh_data = meshes[idx]
        base_path = "obstacle_data/" + obj.name + "/"
        mesh_file_path_data, translation_file_data = \
                __get_mesh_data_file_path_data(base_path, mesh_data)
        data['mesh_data_file'] = mesh_file_path_data
        data['translation_data_file'] = translation_file_data
        data['is_animated'] = mesh_data['is_animated']

        d.append(data)

    return d


def __get_inflow_velocity_data_dict(obj, mesh_data_dict):
    inflow_props = obj.flip_fluid.inflow
    if not inflow_props.is_target_valid():
        return utils.get_vector_property_data_dict(obj, inflow_props, 'inflow_velocity')

    object_mesh_data = mesh_data_dict[obj.name].data
    target_mesh_data = mesh_data_dict[inflow_props.target_object].data
    speed_data = utils.get_property_data_dict(obj, inflow_props, 'inflow_speed')

    return __get_velocity_target_data_dict(object_mesh_data, target_mesh_data, speed_data)


def __get_inflow_data(context, objects, meshes, mesh_data_dict):
    d = []
    for idx, obj in enumerate(objects):
        props = obj.flip_fluid.inflow
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.inflow)
        data['name'] = obj.name
        data['inflow_velocity'] = __get_inflow_velocity_data_dict(obj, mesh_data_dict)

        mesh_data = meshes[idx]
        base_path = "inflow_data/" + obj.name + "/"
        mesh_file_path_data, translation_file_data = \
                __get_mesh_data_file_path_data(base_path, mesh_data)
        data['mesh_data_file'] = mesh_file_path_data
        data['translation_data_file'] = translation_file_data
        data['is_animated'] = mesh_data['is_animated']

        d.append(data)

    return d


def __get_outflow_data(context, objects, meshes):
    d = []
    for idx, obj in enumerate(objects):
        data = utils.flip_fluid_object_to_dict(obj, obj.flip_fluid.outflow)
        data['name'] = obj.name

        mesh_data = meshes[idx]
        base_path = "outflow_data/" + obj.name + "/"
        mesh_file_path_data, translation_file_data = \
                __get_mesh_data_file_path_data(base_path, mesh_data)
        data['mesh_data_file'] = mesh_file_path_data
        data['translation_data_file'] = translation_file_data
        data['is_animated'] = mesh_data['is_animated']

        d.append(data)

    return d


def __get_domain_scale(bbox, dprops):
    if not dprops.world.enable_real_world_size:
        return 1.0
    viewport_width = max(bbox.xdim, bbox.ydim, bbox.zdim)
    return dprops.world.real_world_size / viewport_width


def export(context, export_mesh_data, filepath):
    domain_object = __get_domain_object()
    dprops = __get_domain_properties()
    if domain_object is None:
        return False

    simprops = bpy.context.scene.flip_fluid
    fluid_objects = simprops.get_fluid_objects()
    obstacle_objects = simprops.get_obstacle_objects()
    inflow_objects = simprops.get_inflow_objects()
    outflow_objects = simprops.get_outflow_objects()

    fluid_meshes = []
    obstacle_meshes = []
    inflow_meshes = []
    outflow_meshes = []
    for obj in fluid_objects:
        mesh_data = export_mesh_data[obj.name].data
        fluid_meshes.append(mesh_data)
    for obj in obstacle_objects:
        mesh_data = export_mesh_data[obj.name].data
        obstacle_meshes.append(mesh_data)
    for obj in inflow_objects:
        mesh_data = export_mesh_data[obj.name].data
        inflow_meshes.append(mesh_data)
    for obj in outflow_objects:
        mesh_data = export_mesh_data[obj.name].data
        outflow_meshes.append(mesh_data)

    simulation_objects = flip_fluid_map.Map({})
    simulation_objects.domain = domain_object
    simulation_objects.fluid_objects = fluid_objects
    simulation_objects.obstacle_objects = obstacle_objects
    simulation_objects.inflow_objects = inflow_objects
    simulation_objects.outflow_objects = outflow_objects
    simulation_objects.fluid_meshes = fluid_meshes
    simulation_objects.obstacle_meshes = obstacle_meshes
    simulation_objects.inflow_meshes = inflow_meshes
    simulation_objects.outflow_meshes = outflow_meshes
    simulation_objects.export_mesh_dict = export_mesh_data

    __export_simulation_data_to_file(context, simulation_objects, filepath)

    return True
