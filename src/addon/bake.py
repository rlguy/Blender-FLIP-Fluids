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

import sys, os, shutil, zipfile, json, struct, traceback, math

from .objects import flip_fluid_map
from .operators import bake_operators
from .pyfluid import (
        FluidSimulation,
        TriangleMesh,
        Vector3,
        AABB,
        MeshObject,
        MeshFluidSource,
        )

FLUIDSIM_OBJECT = None
SIMULATION_DATA = None
CACHE_DIRECTORY = ""


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


def __get_export_directory():
    return os.path.join(CACHE_DIRECTORY, "export")


def __get_mesh_directory(object_name):
    return os.path.join(__get_export_directory(), object_name)


def __get_mesh_info_filepath(object_name):
    return os.path.join(__get_export_directory(), object_name, "mesh.info")


def __get_static_mesh_filepath(object_name):
    return os.path.join(__get_mesh_directory(object_name), "mesh.bobj")


def __get_keyframed_mesh_filepath(object_name):
    return os.path.join(__get_mesh_directory(object_name), "mesh.bobj")


def __get_keyframed_transform_filepath(object_name):
    return os.path.join(__get_mesh_directory(object_name), "transforms.data")


def __get_animated_mesh_filepath(object_name, frameno):
    mesh_name = "mesh" + str(frameno).zfill(6) + ".bobj"
    return os.path.join(__get_mesh_directory(object_name), mesh_name)


def __is_object_static(object_name):
    info = __extract_mesh_info(object_name)
    return info['mesh_type'] == 'STATIC'


def __is_object_keyframed(object_name):
    info = __extract_mesh_info(object_name)
    return info['mesh_type'] == 'KEYFRAMED'


def __is_object_animated(object_name):
    info = __extract_mesh_info(object_name)
    return info['mesh_type'] == 'ANIMATED'


def __is_object_dynamic(object_name):
    info = __extract_mesh_info(object_name)
    return info['mesh_type'] == 'KEYFRAMED' or info['mesh_type'] == 'ANIMATED'


def __get_timeline_frame():
    fluidsim = __get_simulation_object()
    data = __get_simulation_data()
    frame_start = data.domain_data.initialize.frame_start
    return fluidsim.get_current_frame() + frame_start


def __get_frame_id():
    fluidsim = __get_simulation_object()
    return fluidsim.get_current_frame()


def __extract_mesh_info(object_name):
    mesh_directory = __get_mesh_directory(object_name)
    if not os.path.isdir(mesh_directory):
        msg = "Error extracting mesh data. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    info_filepath = __get_mesh_info_filepath(object_name)
    if not os.path.isfile(info_filepath):
        msg = "Error extracting mesh info. Exported object info not found: <" 
        msg += info_filepath + ">"
        raise Exception(msg)

    with open(info_filepath, 'r') as f:
        json_data = json.loads(f.read())

    return json_data


def __extract_static_mesh(object_name):
    mesh_directory = __get_mesh_directory(object_name)
    if not os.path.isdir(mesh_directory):
        msg = "Error extracting mesh data. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    filepath_static = __get_static_mesh_filepath(object_name)
    if not os.path.isfile(filepath_static):
        msg = "Error extracting mesh data. Exported object frame not found: <" 
        msg += object_name + ">"
        raise Exception(msg)

    with open(filepath_static, 'rb') as f:
        bobj_data = f.read()

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    tmesh = TriangleMesh.from_bobj(bobj_data)
    tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    tmesh.scale(scale)

    return tmesh


def __extract_transform_data(object_name, frameno):
    transform_filepath = __get_keyframed_transform_filepath(object_name)
    if not os.path.isfile(transform_filepath):
        msg = "Error extracting mesh transforms. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    with open(transform_filepath, 'r') as f:
        matrix_data = json.loads(f.read())

    key = str(frameno)
    if not key in matrix_data:
        msg = "Error extracting mesh transforms. Exported transform frame not found: <" 
        msg += object_name + ", " + str(frameno) + ">"
        raise Exception(msg)

    return matrix_data[key]


def __extract_keyframed_mesh(object_name, frameno):
    mesh_directory = __get_mesh_directory(object_name)
    filepath_keyframed = __get_keyframed_mesh_filepath(object_name)
    if not os.path.isdir(mesh_directory) or not os.path.isfile(filepath_keyframed):
        msg = "Error extracting mesh data. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    with open(filepath_keyframed, 'rb') as f:
        bobj_data = f.read()

    tmesh = TriangleMesh.from_bobj(bobj_data)
    tmesh.apply_transform(__extract_transform_data(object_name, frameno))

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    tmesh.scale(scale)

    return tmesh


def __extract_animated_mesh(object_name, frameno):
    mesh_directory = __get_mesh_directory(object_name)
    if not os.path.isdir(mesh_directory):
        msg = "Error extracting mesh data. Exported object not found: <" + object_name + ">"
        raise Exception(msg)

    filepath_animated = __get_animated_mesh_filepath(object_name, frameno)
    if not os.path.isfile(filepath_animated):
        msg = "Error extracting mesh data. Exported object frame not found: <" 
        msg += object_name + ", " + str(frameno) + ">"
        raise Exception(msg)

    with open(filepath_animated, 'rb') as f:
        bobj_data = f.read()

    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox
    tmesh = TriangleMesh.from_bobj(bobj_data)
    tmesh.translate(-bbox.x, -bbox.y, -bbox.z)
    tmesh.scale(scale)

    return tmesh


def __extract_mesh(object_name, frameno):
    info = __extract_mesh_info(object_name)
    if info['mesh_type'] == 'STATIC':
        return __extract_static_mesh(object_name)
    elif info['mesh_type'] == 'KEYFRAMED': 
        return __extract_keyframed_mesh(object_name, frameno)
    elif info['mesh_type'] == 'ANIMATED':
        return __extract_animated_mesh(object_name, frameno)


def __extract_static_frame_mesh(object_name):
    return __extract_static_mesh(object_name)


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


def __extract_dynamic_frame_meshes(object_name, frameno):
    info = __extract_mesh_info(object_name)
    if info['mesh_type'] == 'KEYFRAMED': 
        return __extract_keyframed_frame_meshes(object_name, frameno)
    elif info['mesh_type'] == 'ANIMATED':
        return __extract_animated_frame_meshes(object_name, frameno)


def __static_mesh_exists(object_name):
    mesh_directory = __get_mesh_directory(object_name)
    if not os.path.isdir(mesh_directory):
        return False
    filepath_static = __get_static_mesh_filepath(object_name)
    return os.path.isfile(filepath_static)


def __keyframed_mesh_exists(object_name, frameno):
    mesh_directory = __get_mesh_directory(object_name)
    if not os.path.isdir(mesh_directory):
        return False
    info = __extract_mesh_info(object_name)
    return frameno >= info['frame_start'] and frameno <= info['frame_end']


def __animated_mesh_exists(object_name, frameno):
    return __keyframed_mesh_exists(object_name, frameno)


def __extract_data(data_filepath):
    with open(data_filepath, 'r') as f:
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


def __read_save_state_file_data(file_data_path):
    with open(file_data_path, 'rb') as f:
        data = f.read()
    return data


def __write_save_state_file_data(file_data_path, data):
    with open(file_data_path, 'wb') as f:
        f.write(data)


def __load_save_state_marker_particle_data(fluidsim, save_state_directory, autosave_info):
    num_particles = autosave_info['num_marker_particles']
    if num_particles == 0:
        return

    d = save_state_directory
    position_data_file = os.path.join(d, autosave_info['marker_particle_position_filedata'])
    velocity_data_file = os.path.join(d, autosave_info['marker_particle_velocity_filedata'])

    position_data = __read_save_state_file_data(position_data_file)
    velocity_data = __read_save_state_file_data(velocity_data_file)

    fluidsim.load_marker_particle_data(num_particles, position_data, velocity_data)


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

    position_data = __read_save_state_file_data(position_data_file)
    velocity_data = __read_save_state_file_data(velocity_data_file)
    lifetime_data = __read_save_state_file_data(lifetime_data_file)
    type_data = __read_save_state_file_data(type_data_file)
    id_data = __read_save_state_file_data(id_data_file)

    fluidsim.load_diffuse_particle_data(num_particles, position_data, velocity_data,
                                        lifetime_data, type_data, id_data)


def __load_save_state_simulator_data(fluidsim, autosave_info):
    next_frame = autosave_info["frame_id"] + 1
    fluidsim.set_current_frame(next_frame)


def __delete_outdated_savestates(cache_directory, savestate_id):
    savestate_directory = os.path.join(cache_directory, "savestates")
    subdirs = os.listdir(savestate_directory)
    if "autosave" in subdirs:
        subdirs.remove("autosave")

    for d in subdirs:
        if int(d[-6:]) > savestate_id:
            path = os.path.join(savestate_directory, d)
            try:
                shutil.rmtree(path)
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
                os.remove(path)
            except:
                print("Error: unable to delete file <" + path + "> (skipping)")

    stats_filepath = os.path.join(cache_directory, "flipstats.data")
    with open(stats_filepath, 'r') as f:
        stats_info = json.loads(f.read())

    for key in stats_info.copy().keys():
        if int(key) > savestate_id:
            del stats_info[key]

    stats_json = json.dumps(stats_info, sort_keys=True, indent=4)
    with open(stats_filepath, 'w') as f:
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

    with open(autosave_info_file, 'r') as f:
        autosave_info = json.loads(f.read())

    __load_save_state_marker_particle_data(fluidsim, autosave_directory, autosave_info)
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
        fluidsim.enable_diffuse_foam = is_foam_enabled
        fluidsim.enable_diffuse_bubbles = is_bubbles_enabled
        fluidsim.enable_diffuse_spray = is_spray_enabled

        fluidsim.enable_whitewater_motion_blur = \
            __get_parameter_data(whitewater.generate_whitewater_motion_blur_data, frameno)

        is_generating_whitewater = __get_parameter_data(whitewater.enable_whitewater_emission, frameno)
        fluidsim.enable_diffuse_particle_emission = is_generating_whitewater

        emitter_pct = __get_parameter_data(whitewater.whitewater_emitter_generation_rate, frameno)
        fluidsim.diffuse_emitter_generation_rate = emitter_pct / 100

        wavecrest_rate = __get_parameter_data(whitewater.wavecrest_emission_rate, frameno)
        turbulence_rate = __get_parameter_data(whitewater.turbulence_emission_rate, frameno)
        fluidsim.diffuse_particle_wavecrest_emission_rate = wavecrest_rate
        fluidsim.diffuse_particle_turbulence_emission_rate = turbulence_rate

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
        fluidsim.foam_particle_lifetime_modifier = 1.0 / max(foam_modifier, 1e-6)
        fluidsim.bubble_particle_lifetime_modifier = 1.0 / max(bubble_modifier, 1e-6)
        fluidsim.spray_particle_lifetime_modifier = 1.0 / max(spray_modifier, 1e-6)

        foam_behaviour = __get_parameter_data(whitewater.foam_boundary_behaviour, frameno)
        bubble_behaviour = __get_parameter_data(whitewater.bubble_boundary_behaviour, frameno)
        spray_behaviour = __get_parameter_data(whitewater.spray_boundary_behaviour, frameno)
        foam_behaviour = __get_limit_behaviour_enum(foam_behaviour)
        bubble_behaviour = __get_limit_behaviour_enum(bubble_behaviour)
        spray_behaviour = __get_limit_behaviour_enum(spray_behaviour)
        fluidsim.diffuse_foam_limit_behaviour = foam_behaviour
        fluidsim.diffuse_bubble_limit_behaviour = bubble_behaviour
        fluidsim.diffuse_spray_limit_behaviour = spray_behaviour

        foam_active_sides = __get_parameter_data(whitewater.foam_boundary_active, frameno)
        bubble_active_sides = __get_parameter_data(whitewater.bubble_boundary_active, frameno)
        spray_active_sides = __get_parameter_data(whitewater.spray_boundary_active, frameno)
        fluidsim.diffuse_foam_active_boundary_sides = foam_active_sides
        fluidsim.diffuse_bubble_active_boundary_sides = bubble_active_sides
        fluidsim.diffuse_spray_active_boundary_sides = spray_active_sides

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

        drag = __get_parameter_data(whitewater.spray_drag_coefficient, frameno)
        fluidsim.diffuse_spray_drag_coefficient = drag

        base_level = __get_parameter_data(whitewater.obstacle_influence_base_level, frameno)
        fluidsim.diffuse_obstacle_influence_base_level = base_level

        decay_rate = __get_parameter_data(whitewater.obstacle_influence_decay_rate, frameno)
        fluidsim.diffuse_obstacle_influence_decay_rate = decay_rate

    # World Settings
    world = dprops.world
    fluidsim.add_body_force(__get_parameter_data(world.gravity, frameno))

    is_viscosity_enabled = __get_parameter_data(world.enable_viscosity, frameno)
    if is_viscosity_enabled:
        fluidsim.viscosity = __get_parameter_data(world.viscosity, frameno)

    is_surface_tension_enabled = __get_parameter_data(world.enable_surface_tension, frameno)
    if is_surface_tension_enabled:
        surface_tension = __get_parameter_data(world.surface_tension, frameno)
        surface_tension *= world.native_surface_tension_scale
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

    __set_meshing_volume_object(fluidsim, data, frameno)

    # Advanced Settings

    advanced = dprops.advanced
    min_substeps, max_substeps = __get_parameter_data(advanced.min_max_time_steps_per_frame, frameno)
    fluidsim.min_time_steps_per_frame = min_substeps
    fluidsim.max_time_steps_per_frame = max_substeps

    fluidsim.enable_adaptive_obstacle_time_stepping = \
        __get_parameter_data(advanced.enable_adaptive_obstacle_time_stepping, frameno)

    fluidsim.marker_particle_jitter_factor = \
        __get_parameter_data(advanced.particle_jitter_factor, frameno)
    fluidsim.jitter_surface_marker_particles = \
        __get_parameter_data(advanced.jitter_surface_particles, frameno)

    fluidsim.PICFLIP_ratio = __get_parameter_data(advanced.PICFLIP_ratio, frameno)

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
    if not fluid_object.target_object:
        return [0, 0, 0]

    target_object_name = fluid_object.target_object
    initial_speed = __get_parameter_data(fluid_object.initial_speed, frameid)
    timeline_frame = __get_timeline_frame()

    mesh1 = __extract_mesh(fluid_object.name, timeline_frame)
    mesh2 = __extract_mesh(target_object_name, timeline_frame)

    c1 = __get_mesh_centroid(mesh1)
    c2 = __get_mesh_centroid(mesh2)
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
    if not inflow_object.target_object:
        return [0, 0, 0]

    target_object_name = inflow_object.target_object
    inflow_speed = __get_parameter_data(inflow_object.inflow_speed, frameid)
    timeline_frame = __get_timeline_frame()

    mesh1 = __extract_mesh(inflow_object.name, timeline_frame)
    mesh2 = __extract_mesh(target_object_name, timeline_frame)

    c1 = __get_mesh_centroid(mesh1)
    c2 = __get_mesh_centroid(mesh2)
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
            fluidsim.add_mesh_fluid(fluid_object, velocity[0], velocity[1], velocity[2])
        else:
            mesh = __extract_static_frame_mesh(obj.name)

            fluid_object = MeshObject(isize, jsize, ksize, dx)
            fluid_object.update_mesh_static(mesh)
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

    fluidsim.initialize()

    bakedata.is_initialized = True


def __update_dynamic_object_mesh(animated_object, object_data):
    data = __get_simulation_data()
    scale = data.domain_data.initialize.scale
    bbox = data.domain_data.initialize.bbox

    timeline_frame = __get_timeline_frame()
    mesh_previous, mesh_current, mesh_next = __extract_dynamic_frame_meshes(object_data.name, timeline_frame)
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

        is_rigid = __get_parameter_data(data.inflow_mesh_type, frameid) == 'MESH_TYPE_RIGID'
        inflow.enable_rigid_mesh = is_rigid

        is_constrained = __get_parameter_data(data.constrain_fluid_velocity, frameid)
        inflow.enable_constrained_fluid_velocity = is_constrained


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
        __set_property(fluidsim, 'enable_diffuse_foam', is_foam_enabled)
        __set_property(fluidsim, 'enable_diffuse_bubbles', is_bubbles_enabled)
        __set_property(fluidsim, 'enable_diffuse_spray', is_spray_enabled)

        whitewater_motion_blur = __get_parameter_data(whitewater.generate_whitewater_motion_blur_data, frameno)
        __set_property(fluidsim, 'enable_whitewater_motion_blur', whitewater_motion_blur)

        emitter_pct = __get_parameter_data(whitewater.whitewater_emitter_generation_rate, frameno)
        __set_property(fluidsim, 'diffuse_emitter_generation_rate', emitter_pct / 100)

        wavecrest_rate = __get_parameter_data(whitewater.wavecrest_emission_rate, frameno)
        turbulence_rate = __get_parameter_data(whitewater.turbulence_emission_rate, frameno)
        __set_property(fluidsim, 'diffuse_particle_wavecrest_emission_rate', wavecrest_rate)
        __set_property(fluidsim, 'diffuse_particle_turbulence_emission_rate', turbulence_rate)

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
        __set_property(fluidsim, 'foam_particle_lifetime_modifier', 1.0 / max(foam_modifier, 1e-6))
        __set_property(fluidsim, 'bubble_particle_lifetime_modifier', 1.0 / max(bubble_modifier, 1e-6))
        __set_property(fluidsim, 'spray_particle_lifetime_modifier', 1.0 / max(spray_modifier, 1e-6))

        foam_behaviour = __get_parameter_data(whitewater.foam_boundary_behaviour, frameno)
        bubble_behaviour = __get_parameter_data(whitewater.bubble_boundary_behaviour, frameno)
        spray_behaviour = __get_parameter_data(whitewater.spray_boundary_behaviour, frameno)
        foam_behaviour = __get_limit_behaviour_enum(foam_behaviour)
        bubble_behaviour = __get_limit_behaviour_enum(bubble_behaviour)
        spray_behaviour = __get_limit_behaviour_enum(spray_behaviour)
        __set_property(fluidsim, 'diffuse_foam_limit_behaviour', foam_behaviour)
        __set_property(fluidsim, 'diffuse_bubble_limit_behaviour', bubble_behaviour)
        __set_property(fluidsim, 'diffuse_spray_limit_behaviour', spray_behaviour)

        foam_active_sides = __get_parameter_data(whitewater.foam_boundary_active, frameno)
        bubble_active_sides = __get_parameter_data(whitewater.bubble_boundary_active, frameno)
        spray_active_sides = __get_parameter_data(whitewater.spray_boundary_active, frameno)
        __set_property(fluidsim, 'diffuse_foam_active_boundary_sides', foam_active_sides)
        __set_property(fluidsim, 'diffuse_bubble_active_boundary_sides', bubble_active_sides)
        __set_property(fluidsim, 'diffuse_spray_active_boundary_sides', spray_active_sides)

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
        viscosity = __get_parameter_data(world.viscosity, frameno)
        __set_property(fluidsim, 'viscosity', viscosity)
    elif fluidsim.viscosity > 0.0:
        __set_property(fluidsim, 'viscosity', 0.0)

    is_surface_tension_enabled = __get_parameter_data(world.enable_surface_tension, frameno)
    if is_surface_tension_enabled:
        surface_tension = __get_parameter_data(world.surface_tension, frameno)
        surface_tension *= world.native_surface_tension_scale
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

    enable_time_stepping = \
        __get_parameter_data(advanced.enable_adaptive_obstacle_time_stepping, frameno)
    __set_property(fluidsim, 'enable_adaptive_obstacle_time_stepping', enable_time_stepping)

    jitter_factor = __get_parameter_data(advanced.particle_jitter_factor, frameno)
    __set_property(fluidsim, 'marker_particle_jitter_factor', jitter_factor)

    jitter_surface = __get_parameter_data(advanced.jitter_surface_particles, frameno)
    __set_property(fluidsim, 'jitter_surface_marker_particles', jitter_surface)

    PICFLIP_ratio = __get_parameter_data(advanced.PICFLIP_ratio, frameno)
    __set_property(fluidsim, 'PICFLIP_ratio', PICFLIP_ratio)

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


def __update_animatable_properties(fluidsim, data, frameno):
    __update_animatable_inflow_properties(data, frameno)
    __update_animatable_outflow_properties(data, frameno)
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
    with open(bounds_filepath, 'w') as f:
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


def __write_logfile_data(cache_directory, logfile_name, fluidsim):
    filedata = fluidsim.get_logfile_data()
    logpath = os.path.join(cache_directory, "logs", logfile_name)
    with open(logpath, 'a') as f:
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
    stats["foam"] = __get_mesh_stats_dict(cstats.foam)
    stats["bubble"] = __get_mesh_stats_dict(cstats.bubble)
    stats["spray"] = __get_mesh_stats_dict(cstats.spray)
    stats["foamblur"] = __get_mesh_stats_dict(cstats.foamblur)
    stats["bubbleblur"] = __get_mesh_stats_dict(cstats.bubbleblur)
    stats["sprayblur"] = __get_mesh_stats_dict(cstats.sprayblur)
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
    with open(statspath, 'w') as f:
        f.write(filedata)


def __write_autosave_data(domain_data, cache_directory, fluidsim, frameno):
    autosave_dir = os.path.join(cache_directory, "savestates", "autosave")
    if not os.path.exists(autosave_dir):
        os.makedirs(autosave_dir)

    position_data_path = os.path.join(autosave_dir, "marker_particle_position.data")
    data = fluidsim.get_marker_particle_position_data()
    __write_save_state_file_data(position_data_path, data)

    velocity_data_path = os.path.join(autosave_dir, "marker_particle_velocity.data")
    data = fluidsim.get_marker_particle_velocity_data()
    __write_save_state_file_data(velocity_data_path, data)

    if fluidsim.get_num_diffuse_particles() > 0:
        diffuse_position_data_path = os.path.join(autosave_dir, "diffuse_particle_position.data")
        data = fluidsim.get_diffuse_particle_position_data()
        __write_save_state_file_data(diffuse_position_data_path, data)

        diffuse_velocity_data_path = os.path.join(autosave_dir, "diffuse_particle_velocity.data")
        data = fluidsim.get_diffuse_particle_velocity_data()
        __write_save_state_file_data(diffuse_velocity_data_path, data)

        diffuse_lifetime_data_path = os.path.join(autosave_dir, "diffuse_particle_lifetime.data")
        data = fluidsim.get_diffuse_particle_lifetime_data()
        __write_save_state_file_data(diffuse_lifetime_data_path, data)

        diffuse_type_data_path = os.path.join(autosave_dir, "diffuse_particle_type.data")
        data = fluidsim.get_diffuse_particle_type_data()
        __write_save_state_file_data(diffuse_type_data_path, data)

        diffuse_id_data_path = os.path.join(autosave_dir, "diffuse_particle_id.data")
        data = fluidsim.get_diffuse_particle_id_data()
        __write_save_state_file_data(diffuse_id_data_path, data)


    frame_start, frame_end = domain_data.initialize.frame_start, domain_data.initialize.frame_end
    autosave_info = {}
    autosave_info['frame'] = frameno
    autosave_info['frame_start'] = frame_start
    autosave_info['frame_end'] = frame_end
    autosave_info['frame_id'] = fluidsim.get_current_frame() - 1
    autosave_info['last_frame_id'] = frame_end - frame_start
    autosave_info['num_marker_particles'] = fluidsim.get_num_marker_particles()
    autosave_info['marker_particle_position_filedata'] = "marker_particle_position.data"
    autosave_info['marker_particle_velocity_filedata'] = "marker_particle_velocity.data"
    autosave_info['num_diffuse_particles'] = fluidsim.get_num_diffuse_particles()

    if fluidsim.get_num_diffuse_particles() > 0:
        autosave_info['diffuse_particle_position_filedata'] = "diffuse_particle_position.data"
        autosave_info['diffuse_particle_velocity_filedata'] = "diffuse_particle_velocity.data"
        autosave_info['diffuse_particle_lifetime_filedata'] = "diffuse_particle_lifetime.data"
        autosave_info['diffuse_particle_type_filedata'] = "diffuse_particle_type.data"
        autosave_info['diffuse_particle_id_filedata'] = "diffuse_particle_id.data"
    else:
        autosave_info['diffuse_particle_position_filedata'] = ""
        autosave_info['diffuse_particle_velocity_filedata'] = ""
        autosave_info['diffuse_particle_lifetime_filedata'] = ""
        autosave_info['diffuse_particle_type_filedata'] = ""
        autosave_info['diffuse_particle_id_filedata'] = ""

    autosave_json = json.dumps(autosave_info, sort_keys=True, indent=4)
    autosave_info_path = os.path.join(autosave_dir, "autosave.state")
    with open(autosave_info_path, 'w') as f:
        f.write(autosave_json)

    init_data = domain_data.initialize
    if init_data.enable_savestates:
        interval = init_data.savestate_interval
        if (frameno + 1 - frame_start) % interval == 0:
            numstr = str(frameno).zfill(6)
            savestate_dir = os.path.join(cache_directory, "savestates", "autosave" + numstr)
            if os.path.isdir(savestate_dir):
                shutil.rmtree(savestate_dir)
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

    __write_logfile_data(cache_directory, domain_data.initialize.logfile_name, fluidsim)
    __write_frame_stats_data(cache_directory, fluidsim, frameno)
    __write_autosave_data(domain_data, cache_directory, fluidsim, frameno)


def __get_current_frame_delta_time(domain_data, frameno):
    simdata = domain_data.simulation
    init_data = domain_data.initialize
    time_scale = __get_parameter_data(simdata.time_scale, frameno)
    use_fps = __get_parameter_data(simdata.use_fps, frameno)
    if use_fps:
        fps = __get_parameter_data(simdata.frames_per_second, frameno)
        dt = (1.0 / fps) * time_scale
    else:
        num_frames = init_data.frame_end - init_data.frame_start + 1
        sim_time = simdata.end_time.data - simdata.start_time.data
        dt = (sim_time / num_frames) * time_scale

    return dt


def __run_simulation(fluidsim, data, cache_directory, bakedata):
    domain = data.domain_data
    init_data = domain.initialize
    num_frames = init_data.frame_end - init_data.frame_start + 1
    current_frame = fluidsim.get_current_frame()

    for i in range(current_frame, num_frames):
        simulator_frameno = fluidsim.get_current_frame()
        blender_frameno = simulator_frameno + init_data.frame_start

        __update_animatable_properties(fluidsim, data, simulator_frameno)
        __add_fluid_objects(fluidsim, data, bakedata, simulator_frameno)

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


def bake(datafile, cache_directory, bakedata, savestate_id=None):
    try:
        __set_cache_directory(cache_directory)

        data = __extract_data(datafile)
        __set_simulation_data(data)

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

        __initialize_fluid_simulation(fluidsim, data, cache_directory, bakedata, savestate_id)
        if __check_bake_cancelled(bakedata):
            return

        __run_simulation(fluidsim, data, cache_directory, bakedata)

    except Exception as e:
        errmsg = str(e)
        if "std::bad_alloc" in errmsg:
            errmsg = "Out of memory. "
        elif not errmsg:
            errmsg = "Unknown error. "
        if not errmsg.endswith(". "):
            errmsg += ". "
        errmsg += "See system console for error info."
        bakedata.error_message = errmsg
        traceback.print_exc()

    print("------------------------------------------------------------")
    print("Simulation Ended.\nThank you for using FLIP Fluids!")
    print("------------------------------------------------------------")

    __set_simulation_object(None)
    bakedata.is_finished = True
