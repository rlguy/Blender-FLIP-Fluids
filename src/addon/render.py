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

import bpy, math

from .utils import api_workaround_utils as api_utils
from .utils import version_compatibility_utils as vcu

IS_RENDERING = False
IS_FRAME_REQUIRING_RELOAD = False
IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT = False

ENABLE_LOAD = {
    "SURFACE": True,
    "FLUID_PARTICLES": True,
    "FOAM": True,
    "BUBBLE": True,
    "SPRAY": True,
    "DUST": True,
    "OBSTACLE_DEBUG": True,
    "PARTICLE_DEBUG": True,
    "FORCE_FIELD_DEBUG": True,
}


def is_rendering():
    global IS_RENDERING
    return IS_RENDERING


def is_simulation_mesh_load_enabled(mesh_name):
    global ENABLE_LOAD
    try:
        return ENABLE_LOAD[mesh_name]
    except KeyError:
        raise Exception("Unknown simulation mesh name: <" + mesh_name + ">")


def enable_simulation_mesh_load(mesh_name):
    global ENABLE_LOAD
    try:
        ENABLE_LOAD[mesh_name] = True
    except KeyError:
        raise Exception("Unknown simulation mesh name: <" + mesh_name + ">")


def disable_simulation_mesh_load(mesh_name):
    global ENABLE_LOAD
    try:
        ENABLE_LOAD[mesh_name] = False
    except KeyError:
        raise Exception("Unknown simulation mesh name: <" + mesh_name + ">")


def __update_is_keyframed_hide_render_issue_status(scene):
    global IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT
    IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT = False
    try:
        # See api_utils method for more information
        IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT = api_utils.is_keyframed_hide_render_issue_relevant(scene)
    except Exception as e:
        print("FLIP Fluids Error: ", str(e))


def is_keyframed_hide_render_issue_relevant():
    global IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT
    return IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT


def __get_domain_properties():
    return bpy.context.scene.flip_fluid.get_domain_properties() 


def __is_domain_set():
    return bpy.context.scene.flip_fluid.get_domain_object() is not None


def __is_domain_in_scene():
    bl_domain = bpy.context.scene.flip_fluid.get_domain_object()
    if bl_domain is None:
        return False
    return bl_domain.name in bpy.context.scene.collection.all_objects


def get_current_simulation_frame():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return 0 

    rprops = dprops.render
    if rprops.simulation_playback_mode == 'PLAYBACK_MODE_TIMELINE':
        current_frame = bpy.context.scene.frame_current
    elif rprops.simulation_playback_mode == 'PLAYBACK_MODE_OVERRIDE_FRAME':
        current_frame = math.floor(dprops.render.override_frame)
    elif rprops.simulation_playback_mode == 'PLAYBACK_MODE_HOLD_FRAME':
        current_frame = dprops.render.hold_frame_number

    return current_frame - bpy.context.scene.flip_fluid_helper.playback_frame_offset


def get_timeline_frame_from_simulation_frame(frameno):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return 0 

    rprops = dprops.render
    if rprops.simulation_playback_mode == 'PLAYBACK_MODE_TIMELINE':
        current_frame = frameno
    elif rprops.simulation_playback_mode == 'PLAYBACK_MODE_OVERRIDE_FRAME':
        current_frame = math.floor(dprops.render.override_frame)
    elif rprops.simulation_playback_mode == 'PLAYBACK_MODE_HOLD_FRAME':
        current_frame = dprops.render.hold_frame_number

    return current_frame + bpy.context.scene.flip_fluid_helper.playback_frame_offset


def get_current_render_frame():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return 0 
    return get_current_simulation_frame()


def __get_render_pre_current_frame():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return 0 
    return get_current_simulation_frame()


def __get_display_mode():
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if is_rendering():
        mode = dprops.render.render_display
        if not bpy.context.scene.flip_fluid.show_render:
            mode = 'DISPLAY_NONE'
    else:
        mode = dprops.render.viewport_display
        if not bpy.context.scene.flip_fluid.show_viewport:
            mode = 'DISPLAY_NONE'
    return mode


def __update_surface_display_mode():
    dprops = __get_domain_properties()
    surface_cache = dprops.mesh_cache.surface

    # For Final display mode
    surface_display_settings = {
        "enable_velocity_attribute":             dprops.surface.enable_velocity_vector_attribute,
        "enable_vorticity_attribute":            dprops.surface.enable_vorticity_vector_attribute,
        "enable_speed_attribute":                dprops.surface.enable_speed_attribute,
        "enable_age_attribute":                  dprops.surface.enable_age_attribute,
        "enable_lifetime_attribute":             dprops.surface.enable_lifetime_attribute,
        "enable_whitewater_proximity_attribute": dprops.surface.enable_whitewater_proximity_attribute,
        "enable_color_attribute":                dprops.surface.enable_color_attribute,
        "enable_uvw_attribute":                  dprops.surface.enable_uvw_attribute,
        "enable_source_id_attribute":            dprops.surface.enable_source_id_attribute,
        "enable_viscosity_attribute":            dprops.surface.enable_viscosity_attribute,
        "enable_density_attribute":              dprops.world.enable_density_attribute,
    }

    surface_cache.reset_enabled_mesh_attributes()
    display_mode = __get_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        surface_cache.mesh_prefix = ""
        surface_cache.mesh_display_name_prefix = "final_"
        for prop_name,value in surface_display_settings.items():
            setattr(surface_cache, prop_name, value)

    elif display_mode == 'DISPLAY_PREVIEW':
        surface_cache.mesh_prefix = "preview"
        surface_cache.mesh_display_name_prefix = "preview_"

    elif display_mode == 'DISPLAY_NONE':
        surface_cache.mesh_prefix = "none"
        surface_cache.mesh_display_name_prefix = "none_"


def __load_surface_frame(frameno, force_reload=False, depsgraph=None):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.surface.enable_surface_mesh_generation:
        return

    __update_surface_display_mode()

    force_load = force_reload or is_rendering()
    dprops = __get_domain_properties()

    if is_simulation_mesh_load_enabled('SURFACE'):
        dprops.mesh_cache.surface.load_frame(frameno, force_load, depsgraph)


def __get_fluid_particle_display_mode():
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if is_rendering():
        mode = dprops.render.fluid_particle_render_display
    else:
        mode = dprops.render.fluid_particle_viewport_display
    return mode


def __get_fluid_particle_display_percentages():
    dprops = __get_domain_properties()
    rprops = dprops.render

    display_mode = __get_fluid_particle_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        surface_pct = rprops.render_fluid_particle_surface_pct
        boundary_pct = rprops.render_fluid_particle_boundary_pct
        interior_pct = rprops.render_fluid_particle_interior_pct
    elif display_mode == 'DISPLAY_PREVIEW':
        surface_pct = rprops.viewport_fluid_particle_surface_pct
        boundary_pct = rprops.viewport_fluid_particle_boundary_pct
        interior_pct = rprops.viewport_fluid_particle_interior_pct
    elif display_mode == 'DISPLAY_NONE':
        surface_pct = boundary_pct = interior_pct = 0.0

    return surface_pct, boundary_pct, interior_pct


def __update_fluid_particle_display_mode():
    dprops = __get_domain_properties()
    particle_cache = dprops.mesh_cache.particles
    particle_props = dprops.particles

    # For Final/Preview display modes
    particle_display_settings = {
        "enable_velocity_attribute":             particle_props.enable_fluid_particle_velocity_vector_attribute,
        "enable_vorticity_attribute":            particle_props.enable_fluid_particle_vorticity_vector_attribute,
        "enable_speed_attribute":                particle_props.enable_fluid_particle_speed_attribute,
        "enable_age_attribute":                  particle_props.enable_fluid_particle_age_attribute,
        "enable_lifetime_attribute":             particle_props.enable_fluid_particle_lifetime_attribute,
        "enable_whitewater_proximity_attribute": particle_props.enable_fluid_particle_whitewater_proximity_attribute,
        "enable_color_attribute":                particle_props.enable_fluid_particle_color_attribute,
        "enable_uvw_attribute":                  particle_props.enable_fluid_particle_uvw_attribute,
        "enable_source_id_attribute":            particle_props.enable_fluid_particle_source_id_attribute,
        "enable_viscosity_attribute":            dprops.surface.enable_viscosity_attribute,
        "enable_density_attribute":              dprops.world.enable_density_attribute,
        "enable_id_attribute":                   particle_props.enable_fluid_particle_output,
        "enable_uid_attribute":                  particle_props.enable_fluid_particle_uid_attribute,
    }
    
    particle_cache.reset_enabled_mesh_attributes()
    display_mode = __get_fluid_particle_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        particle_cache.mesh_prefix = "fluidparticles"
        particle_cache.mesh_display_name_prefix = "final_"
        for prop_name,value in particle_display_settings.items():
            setattr(particle_cache, prop_name, value)

    elif display_mode == 'DISPLAY_PREVIEW':
        particle_cache.mesh_prefix = "fluidparticles"
        particle_cache.mesh_display_name_prefix = "preview_"
        for prop_name,value in particle_display_settings.items():
            setattr(particle_cache, prop_name, value)

    elif display_mode == 'DISPLAY_NONE':
        particle_cache.mesh_prefix = "none"
        particle_cache.mesh_display_name_prefix = "none_"

    surface_pct, boundary_pct, bubble_pct = __get_fluid_particle_display_percentages()
    particle_cache.ffp3_surface_import_percentage = surface_pct
    particle_cache.ffp3_boundary_import_percentage = boundary_pct
    particle_cache.ffp3_interior_import_percentage = bubble_pct


def __load_fluid_particle_frame(frameno, force_reload=False, depsgraph=None):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.particles.enable_fluid_particle_output:
        return

    __update_fluid_particle_display_mode()

    force_load = force_reload or is_rendering()
    dprops = __get_domain_properties()

    if is_simulation_mesh_load_enabled('FLUID_PARTICLES'):
        dprops.mesh_cache.particles.load_frame(frameno, force_load, depsgraph)


def __get_whitewater_display_mode():
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if is_rendering():
        mode = dprops.render.whitewater_render_display
    else:
        mode = dprops.render.whitewater_viewport_display
    return mode


def __get_whitewater_display_percentages():
    dprops = __get_domain_properties()
    rprops = dprops.render

    display_mode = __get_whitewater_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        foam_pct = rprops.render_foam_pct
        bubble_pct = rprops.render_bubble_pct
        spray_pct = rprops.render_spray_pct
        dust_pct = rprops.render_dust_pct
    elif display_mode == 'DISPLAY_PREVIEW':
        foam_pct = rprops.viewport_foam_pct
        bubble_pct = rprops.viewport_bubble_pct
        spray_pct = rprops.viewport_spray_pct
        dust_pct = rprops.viewport_dust_pct
    elif display_mode == 'DISPLAY_NONE':
        foam_pct = bubble_pct = spray_pct = dust_pct = 0

    return foam_pct, bubble_pct, spray_pct, dust_pct


def __update_whitewater_display_mode():
    dprops = __get_domain_properties()
    cache = dprops.mesh_cache
    whitewater_cache_objects = [
        cache.foam,
        cache.bubble,
        cache.spray,
        cache.dust,
    ]

    # For Final/Preview display modes
    particle_display_settings = {
        "enable_velocity_attribute": dprops.whitewater.enable_velocity_vector_attribute,
        "enable_id_attribute":       dprops.whitewater.enable_id_attribute,
        "enable_lifetime_attribute": dprops.whitewater.enable_lifetime_attribute,
    }

    cache.foam.reset_enabled_mesh_attributes()
    cache.bubble.reset_enabled_mesh_attributes()
    cache.spray.reset_enabled_mesh_attributes()
    cache.dust.reset_enabled_mesh_attributes()
    display_mode = __get_whitewater_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        cache.foam.mesh_prefix = "foam"
        cache.bubble.mesh_prefix = "bubble"
        cache.spray.mesh_prefix = "spray"
        cache.dust.mesh_prefix = "dust"

        for cache_object in whitewater_cache_objects:
            cache_object.mesh_display_name_prefix = "final_"
            for prop_name,value in particle_display_settings.items():
                setattr(cache_object, prop_name, value)

    elif display_mode == 'DISPLAY_PREVIEW':
        cache.foam.mesh_prefix = "foam"
        cache.bubble.mesh_prefix = "bubble"
        cache.spray.mesh_prefix = "spray"
        cache.dust.mesh_prefix = "dust"

        for cache_object in whitewater_cache_objects:
            cache_object.mesh_display_name_prefix = "preview_"
            for prop_name,value in particle_display_settings.items():
                setattr(cache_object, prop_name, value)

    elif display_mode == 'DISPLAY_NONE':
        cache.foam.mesh_prefix = "foam_none"
        cache.bubble.mesh_prefix = "bubble_none"
        cache.spray.mesh_prefix = "spray_none"
        cache.dust.mesh_prefix = "dust_none"
        
        for cache_object in whitewater_cache_objects:
            cache_object.mesh_display_name_prefix = "none_"

    foam_pct, bubble_pct, spray_pct, dust_pct = __get_whitewater_display_percentages()
    cache.foam.wwp_import_percentage = foam_pct
    cache.bubble.wwp_import_percentage = bubble_pct
    cache.spray.wwp_import_percentage = spray_pct
    cache.dust.wwp_import_percentage = dust_pct



def __load_whitewater_particle_frame(frameno, force_reload=False, depsgraph=None):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.whitewater.enable_whitewater_simulation:
        return

    __update_whitewater_display_mode()

    force_load = force_reload or is_rendering()
    if is_simulation_mesh_load_enabled('FOAM'):
        dprops.mesh_cache.foam.load_frame(frameno, force_load, depsgraph)
    if is_simulation_mesh_load_enabled('BUBBLE'):
        dprops.mesh_cache.bubble.load_frame(frameno, force_load, depsgraph)
    if is_simulation_mesh_load_enabled('SPRAY'):
        dprops.mesh_cache.spray.load_frame(frameno, force_load, depsgraph)
    if is_simulation_mesh_load_enabled('DUST'):
        dprops.mesh_cache.dust.load_frame(frameno, force_load, depsgraph)


def __load_fluid_particle_debug_frame(frameno, force_reload=False):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.enable_fluid_particle_debug_output:
        return

    force_load = force_reload or is_rendering()

    if is_simulation_mesh_load_enabled('PARTICLE_DEBUG'):
        dprops.mesh_cache.gl_particles.load_frame(frameno, force_load)


def __load_obstacle_debug_frame(frameno, force_reload=False):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_internal_obstacle_mesh or not dprops.debug.internal_obstacle_mesh_visibility:
        return

    force_load = force_reload or is_rendering()
    if is_simulation_mesh_load_enabled('OBSTACLE_DEBUG'):
        dprops.mesh_cache.obstacle.load_frame(frameno, force_load)


def __load_force_field_debug_frame(frameno, force_reload=False):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_force_field:
        return

    force_load = force_reload or is_rendering()
    if is_simulation_mesh_load_enabled('FORCE_FIELD_DEBUG'):
        dprops.mesh_cache.gl_force_field.load_frame(frameno, force_load)


def __load_frame(frameno, force_reload=False, depsgraph=None):
    if not __is_domain_set():
        return

    if not __is_domain_in_scene():
        # Domain shouldn't be operated on if it is not contained in the
        # active scene
        return

    dprops = __get_domain_properties()
    dprops.mesh_cache.initialize_cache_objects()

    __load_surface_frame(frameno, force_reload, depsgraph)
    __load_fluid_particle_frame(frameno, force_reload, depsgraph)
    __load_whitewater_particle_frame(frameno, force_reload, depsgraph)
    __load_fluid_particle_debug_frame(frameno, force_reload)
    __load_force_field_debug_frame(frameno, force_reload)
    __load_obstacle_debug_frame(frameno, force_reload)


def reload_frame(frameno):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return
    __load_frame(frameno, True)


def render_init(scene):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return

    global IS_RENDERING
    IS_RENDERING = True

    dprops = __get_domain_properties()
    dprops.mesh_cache.initialize_cache_objects()


def render_complete(scene):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return

    global IS_RENDERING
    global IS_FRAME_REQUIRING_RELOAD
    IS_RENDERING = False
    IS_FRAME_REQUIRING_RELOAD = True


def render_cancel(scene):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return

    render_complete(scene)


def render_pre(scene):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return

    is_running_cmd = bpy.app.background
    if is_running_cmd:
        print("\n\tFLIP Fluids: Rendering frame " + str(scene.frame_current) + " <" + bpy.data.filepath + ">\n")

    if not is_running_cmd:
        is_persistent_data_enabled = api_utils.is_persistent_data_issue_relevant()
        if is_persistent_data_enabled:
            warning_string = api_utils.get_persistent_data_warning_string()
            print(warning_string)

    __update_is_keyframed_hide_render_issue_status(scene)


def frame_change_post(scene, depsgraph=None):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return

    if is_rendering():
        if not scene.render.use_lock_interface:
            print("FLIP FLUIDS WARNING: The Blender interface should be locked during render to prevent render crashes (Blender > Render > Lock Interface).")


    force_reload = False
    frameno = get_current_render_frame()
    __load_frame(frameno, force_reload, depsgraph)
    dprops = __get_domain_properties()
    dprops.render.current_frame = frameno


def scene_update_post(scene):
    if not __is_domain_set():
        return
    if not __is_domain_in_scene():
        return

    global IS_FRAME_REQUIRING_RELOAD
    if IS_FRAME_REQUIRING_RELOAD:
        IS_FRAME_REQUIRING_RELOAD = False

        current_frame = get_current_render_frame()
        reload_frame(current_frame)
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        dprops.render.current_frame = current_frame
