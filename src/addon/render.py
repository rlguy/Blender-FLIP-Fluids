# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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
RENDER_PRE_FRAME_NUMBER = 0
IS_KEYFRAMED_HIDE_RENDER_ISSUE_RELEVANT = False

ENABLE_SURFACE_LOAD = True
ENABLE_FOAM_LOAD = True
ENABLE_BUBBLE_LOAD = True
ENABLE_SPRAY_LOAD = True
ENABLE_DUST_LOAD = True
ENABLE_OBSTACLE_DEBUG_LOAD = True
ENABLE_PARTICLE_DEBUG_LOAD = True
ENABLE_FORCE_FIELD_DEBUG_LOAD = True


def is_rendering():
    global IS_RENDERING
    return IS_RENDERING


def is_simulation_mesh_load_enabled(mesh_name):
    global ENABLE_SURFACE_LOAD
    global ENABLE_FOAM_LOAD
    global ENABLE_BUBBLE_LOAD
    global ENABLE_SPRAY_LOAD
    global ENABLE_DUST_LOAD
    global ENABLE_OBSTACLE_DEBUG_LOAD
    global ENABLE_PARTICLE_DEBUG_LOAD
    global ENABLE_FORCE_FIELD_DEBUG_LOAD

    if   mesh_name == 'SURFACE':
        return ENABLE_SURFACE_LOAD
    elif mesh_name == 'FOAM':
        return ENABLE_FOAM_LOAD
    elif mesh_name == 'BUBBLE':
        return ENABLE_BUBBLE_LOAD
    elif mesh_name == 'SPRAY':
        return ENABLE_SPRAY_LOAD
    elif mesh_name == 'DUST':
        return ENABLE_DUST_LOAD
    elif mesh_name == 'OBSTACLE_DEBUG':
        return ENABLE_OBSTACLE_DEBUG_LOAD
    elif mesh_name == 'PARTICLE_DEBUG':
        return ENABLE_PARTICLE_DEBUG_LOAD
    elif mesh_name == 'FORCE_FIELD_DEBUG':
        return ENABLE_FORCE_FIELD_DEBUG_LOAD
    else:
        raise Exception("Unknown simulation mesh name: <" + mesh_name + ">")


def enable_simulation_mesh_load(mesh_name):
    global ENABLE_SURFACE_LOAD
    global ENABLE_FOAM_LOAD
    global ENABLE_BUBBLE_LOAD
    global ENABLE_SPRAY_LOAD
    global ENABLE_DUST_LOAD
    global ENABLE_OBSTACLE_DEBUG_LOAD
    global ENABLE_PARTICLE_DEBUG_LOAD
    global ENABLE_FORCE_FIELD_DEBUG_LOAD

    if   mesh_name == 'SURFACE':
        ENABLE_SURFACE_LOAD = True
    elif mesh_name == 'FOAM':
        ENABLE_FOAM_LOAD = True
    elif mesh_name == 'BUBBLE':
        ENABLE_BUBBLE_LOAD = True
    elif mesh_name == 'SPRAY':
        ENABLE_SPRAY_LOAD = True
    elif mesh_name == 'DUST':
        ENABLE_DUST_LOAD = True
    elif mesh_name == 'OBSTACLE_DEBUG':
        ENABLE_OBSTACLE_DEBUG_LOAD = True
    elif mesh_name == 'PARTICLE_DEBUG':
        ENABLE_PARTICLE_DEBUG_LOAD = True
    elif mesh_name == 'FORCE_FIELD_DEBUG':
        ENABLE_FORCE_FIELD_DEBUG_LOAD = True
    else:
        raise Exception("Unknown simulation mesh name: <" + mesh_name + ">")


def disable_simulation_mesh_load(mesh_name):
    global ENABLE_SURFACE_LOAD
    global ENABLE_FOAM_LOAD
    global ENABLE_BUBBLE_LOAD
    global ENABLE_SPRAY_LOAD
    global ENABLE_DUST_LOAD
    global ENABLE_OBSTACLE_DEBUG_LOAD
    global ENABLE_PARTICLE_DEBUG_LOAD
    global ENABLE_FORCE_FIELD_DEBUG_LOAD

    if   mesh_name == 'SURFACE':
        ENABLE_SURFACE_LOAD = False
    elif mesh_name == 'FOAM':
        ENABLE_FOAM_LOAD = False
    elif mesh_name == 'BUBBLE':
        ENABLE_BUBBLE_LOAD = False
    elif mesh_name == 'SPRAY':
        ENABLE_SPRAY_LOAD = False
    elif mesh_name == 'DUST':
        ENABLE_DUST_LOAD = False
    elif mesh_name == 'OBSTACLE_DEBUG':
        ENABLE_OBSTACLE_DEBUG_LOAD = False
    elif mesh_name == 'PARTICLE_DEBUG':
        ENABLE_PARTICLE_DEBUG_LOAD = False
    elif mesh_name == 'FORCE_FIELD_DEBUG':
        ENABLE_FORCE_FIELD_DEBUG_LOAD = False
    else:
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


def get_current_render_frame():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return 0 

    """
    # https://developer.blender.org/T71908 currently breaks
    # this return due to incorrect frame number that is not
    # available on render_pre.
    #
    # Reason for this return is to prevent the Blender compositor
    # from changing frames while rendering a single frame, but this
    # use case is rare.

    if is_rendering():
        global RENDER_PRE_FRAME_NUMBER
        return RENDER_PRE_FRAME_NUMBER
    """

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
    if IS_RENDERING:
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

    display_mode = __get_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        surface_cache.mesh_prefix = ""
        surface_cache.mesh_display_name_prefix = "final_"
        render_blur = IS_RENDERING and dprops.render.render_surface_motion_blur
        surface_cache.enable_motion_blur = render_blur
        surface_cache.motion_blur_scale = dprops.render.surface_motion_blur_scale
        surface_cache.enable_velocity_attribute = dprops.surface.enable_velocity_vector_attribute
        surface_cache.enable_vorticity_attribute = dprops.surface.enable_vorticity_vector_attribute
        surface_cache.enable_speed_attribute = dprops.surface.enable_speed_attribute
        surface_cache.enable_age_attribute = dprops.surface.enable_age_attribute
        surface_cache.enable_color_attribute = dprops.surface.enable_color_attribute
        surface_cache.enable_source_id_attribute = dprops.surface.enable_source_id_attribute
        surface_cache.enable_viscosity_attribute = dprops.surface.enable_viscosity_attribute
        surface_cache.enable_id_attribute = False
        surface_cache.enable_lifetime_attribute = False
    elif display_mode == 'DISPLAY_PREVIEW':
        surface_cache.mesh_prefix = "preview"
        surface_cache.mesh_display_name_prefix = "preview_"
        surface_cache.enable_motion_blur = False
        surface_cache.enable_velocity_attribute = False
        surface_cache.enable_vorticity_attribute = False
        surface_cache.enable_speed_attribute = False
        surface_cache.enable_age_attribute = False
        surface_cache.enable_color_attribute = False
        surface_cache.enable_source_id_attribute = False
        surface_cache.enable_viscosity_attribute = False
        surface_cache.enable_id_attribute = False
        surface_cache.enable_lifetime_attribute = False
    elif display_mode == 'DISPLAY_NONE':
        surface_cache.mesh_prefix = "none"
        surface_cache.mesh_display_name_prefix = "none_"
        surface_cache.enable_motion_blur = False
        surface_cache.enable_velocity_attribute = False
        surface_cache.enable_vorticity_attribute = False
        surface_cache.enable_speed_attribute = False
        surface_cache.enable_age_attribute = False
        surface_cache.enable_color_attribute = False
        surface_cache.enable_source_id_attribute = False
        surface_cache.enable_viscosity_attribute = False
        surface_cache.enable_id_attribute = False
        surface_cache.enable_lifetime_attribute = False


def __load_surface_frame(frameno, force_reload=False, depsgraph=None):
    global IS_RENDERING
    if not __is_domain_set():
        return

    __update_surface_display_mode()

    force_load = force_reload or IS_RENDERING
    dprops = __get_domain_properties()

    if is_simulation_mesh_load_enabled('SURFACE'):
        dprops.mesh_cache.surface.load_frame(frameno, force_load, depsgraph)


def __get_whitewater_display_mode():
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if IS_RENDERING:
        mode = dprops.render.whitewater_render_display
    else:
        mode = dprops.render.whitewater_viewport_display
    return mode


def __get_whitewater_display_percentages():
    dprops = __get_domain_properties()
    rprops = dprops.render

    display_mode = __get_whitewater_display_mode()
    if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
        if display_mode == 'DISPLAY_FINAL':
            pct = rprops.render_whitewater_pct
        elif display_mode == 'DISPLAY_PREVIEW':
            pct = rprops.viewport_whitewater_pct
        elif display_mode == 'DISPLAY_NONE':
            pct = 0
        foam_pct = bubble_pct = spray_pct = dust_pct = pct
    else:
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

    display_mode = __get_whitewater_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        cache.foam.mesh_prefix = "foam"
        cache.bubble.mesh_prefix = "bubble"
        cache.spray.mesh_prefix = "spray"
        cache.dust.mesh_prefix = "dust"
        cache.foam.mesh_display_name_prefix = "final_"
        cache.bubble.mesh_display_name_prefix = "final_"
        cache.spray.mesh_display_name_prefix = "final_"
        cache.dust.mesh_display_name_prefix = "final_"

        render_blur = IS_RENDERING and dprops.render.render_whitewater_motion_blur
        cache.foam.enable_motion_blur = render_blur
        cache.bubble.enable_motion_blur = render_blur
        cache.spray.enable_motion_blur = render_blur
        cache.dust.enable_motion_blur = render_blur
        cache.foam.motion_blur_scale = dprops.render.whitewater_motion_blur_scale
        cache.bubble.motion_blur_scale = dprops.render.whitewater_motion_blur_scale
        cache.spray.motion_blur_scale = dprops.render.whitewater_motion_blur_scale
        cache.dust.motion_blur_scale = dprops.render.whitewater_motion_blur_scale
        cache.foam.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.bubble.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.spray.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.dust.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.foam.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.bubble.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.spray.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.dust.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.foam.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.bubble.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.spray.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.dust.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.foam.enable_vorticity_attribute = False
        cache.bubble.enable_vorticity_attribute = False
        cache.spray.enable_vorticity_attribute = False
        cache.dust.enable_vorticityy_attribute = False
        cache.foam.enable_speed_attribute = False
        cache.bubble.enable_speed_attribute = False
        cache.spray.enable_speed_attribute = False
        cache.dust.enable_speed_attribute = False
        cache.foam.enable_age_attribute = False
        cache.bubble.enable_age_attribute = False
        cache.spray.enable_age_attribute = False
        cache.dust.enable_age_attribute = False
        cache.foam.enable_color_attribute = False
        cache.bubble.enable_color_attribute = False
        cache.spray.enable_color_attribute = False
        cache.dust.enable_color_attribute = False
        cache.foam.enable_source_id_attribute = False
        cache.bubble.enable_source_id_attribute = False
        cache.spray.enable_source_id_attribute = False
        cache.dust.enable_source_id_attribute = False
        cache.foam.enable_viscosity_attribute = False
        cache.bubble.enable_viscosity_attribute = False
        cache.spray.enable_viscosity_attribute = False
        cache.dust.enable_viscosity_attribute = False
    elif display_mode == 'DISPLAY_PREVIEW':
        cache.foam.mesh_prefix = "foam"
        cache.bubble.mesh_prefix = "bubble"
        cache.spray.mesh_prefix = "spray"
        cache.dust.mesh_prefix = "dust"
        cache.foam.mesh_display_name_prefix = "preview_"
        cache.bubble.mesh_display_name_prefix = "preview_"
        cache.spray.mesh_display_name_prefix = "preview_"
        cache.dust.mesh_display_name_prefix = "preview_"
        cache.foam.enable_motion_blur = False
        cache.bubble.enable_motion_blur = False
        cache.spray.enable_motion_blur = False
        cache.dust.enable_motion_blur = False
        cache.foam.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.bubble.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.spray.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.dust.enable_velocity_attribute = dprops.whitewater.enable_velocity_vector_attribute
        cache.foam.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.bubble.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.spray.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.dust.enable_id_attribute = dprops.whitewater.enable_id_attribute
        cache.foam.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.bubble.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.spray.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.dust.enable_lifetime_attribute = dprops.whitewater.enable_lifetime_attribute
        cache.foam.enable_vorticity_attribute = False
        cache.bubble.enable_vorticity_attribute = False
        cache.spray.enable_vorticity_attribute = False
        cache.dust.enable_vorticity_attribute = False
        cache.foam.enable_speed_attribute = False
        cache.bubble.enable_speed_attribute = False
        cache.spray.enable_speed_attribute = False
        cache.dust.enable_speed_attribute = False
        cache.foam.enable_age_attribute = False
        cache.bubble.enable_age_attribute = False
        cache.spray.enable_age_attribute = False
        cache.dust.enable_age_attribute = False
        cache.foam.enable_color_attribute = False
        cache.bubble.enable_color_attribute = False
        cache.spray.enable_color_attribute = False
        cache.dust.enable_color_attribute = False
        cache.foam.enable_source_id_attribute = False
        cache.bubble.enable_source_id_attribute = False
        cache.spray.enable_source_id_attribute = False
        cache.dust.enable_source_id_attribute = False
        cache.foam.enable_viscosity_attribute = False
        cache.bubble.enable_viscosity_attribute = False
        cache.spray.enable_viscosity_attribute = False
        cache.dust.enable_viscosity_attribute = False
    elif display_mode == 'DISPLAY_NONE':
        cache.foam.mesh_prefix = "foam_none"
        cache.bubble.mesh_prefix = "bubble_none"
        cache.spray.mesh_prefix = "spray_none"
        cache.dust.mesh_prefix = "dust_none"
        cache.foam.mesh_display_name_prefix = "none_"
        cache.bubble.mesh_display_name_prefix = "none_"
        cache.spray.mesh_display_name_prefix = "none_"
        cache.dust.mesh_display_name_prefix = "none_"
        cache.foam.enable_motion_blur = False
        cache.bubble.enable_motion_blur = False
        cache.spray.enable_motion_blur = False
        cache.dust.enable_motion_blur = False
        cache.foam.enable_velocity_attribute = False
        cache.bubble.enable_velocity_attribute = False
        cache.spray.enable_velocity_attribute = False
        cache.dust.enable_velocity_attribute = False
        cache.foam.enable_id_attribute = False
        cache.bubble.enable_id_attribute = False
        cache.spray.enable_id_attribute = False
        cache.dust.enable_id_attribute = False
        cache.foam.enable_lifetime_attribute = False
        cache.bubble.enable_lifetime_attribute = False
        cache.spray.enable_lifetime_attribute = False
        cache.dust.enable_lifetime_attribute = False
        cache.foam.enable_vorticity_attribute = False
        cache.bubble.enable_vorticity_attribute = False
        cache.spray.enable_vorticity_attribute = False
        cache.dust.enable_vorticity_attribute = False
        cache.foam.enable_speed_attribute = False
        cache.bubble.enable_speed_attribute = False
        cache.spray.enable_speed_attribute = False
        cache.dust.enable_speed_attribute = False
        cache.foam.enable_age_attribute = False
        cache.bubble.enable_age_attribute = False
        cache.spray.enable_age_attribute = False
        cache.dust.enable_age_attribute = False
        cache.foam.enable_color_attribute = False
        cache.bubble.enable_color_attribute = False
        cache.spray.enable_color_attribute = False
        cache.dust.enable_color_attribute = False
        cache.foam.enable_source_id_attribute = False
        cache.bubble.enable_source_id_attribute = False
        cache.spray.enable_source_id_attribute = False
        cache.dust.enable_source_id_attribute = False
        cache.foam.enable_viscosity_attribute = False
        cache.bubble.enable_viscosity_attribute = False
        cache.spray.enable_viscosity_attribute = False
        cache.dust.enable_viscosity_attribute = False

    foam_pct, bubble_pct, spray_pct, dust_pct = __get_whitewater_display_percentages()
    cache.foam.wwp_import_percentage = foam_pct
    cache.bubble.wwp_import_percentage = bubble_pct
    cache.spray.wwp_import_percentage = spray_pct
    cache.dust.wwp_import_percentage = dust_pct



def __load_whitewater_particle_frame(frameno, force_reload=False, depsgraph=None):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.whitewater.enable_whitewater_simulation:
        return

    __update_whitewater_display_mode()

    force_load = force_reload or IS_RENDERING
    if is_simulation_mesh_load_enabled('FOAM'):
        dprops.mesh_cache.foam.load_frame(frameno, force_load, depsgraph)
    if is_simulation_mesh_load_enabled('BUBBLE'):
        dprops.mesh_cache.bubble.load_frame(frameno, force_load, depsgraph)
    if is_simulation_mesh_load_enabled('SPRAY'):
        dprops.mesh_cache.spray.load_frame(frameno, force_load, depsgraph)
    if is_simulation_mesh_load_enabled('DUST'):
        dprops.mesh_cache.dust.load_frame(frameno, force_load, depsgraph)


def __generate_icosphere_geometry():
    # Icosphere with 1 subdivision (20 sides) centred at origin
    verts = [
        (0.0000, 0.0000, -1.0000), (0.7236, -0.5257, -0.4472), (-0.2764, -0.8506, -0.4472),
        (-0.8944, 0.0000, -0.4472), (-0.2764, 0.8506, -0.4472), (0.7236, 0.5257, -0.4472),
        (0.2764, -0.8506, 0.4472), (-0.7236, -0.5257, 0.4472), (-0.7236, 0.5257, 0.4472),
        (0.2764, 0.8506, 0.4472), (0.8944, 0.0000, 0.4472), (0.0000, 0.0000, 1.0000)
    ]
    tris = [
        (0, 1, 2), (1, 0, 5), (0, 2, 3), (0, 3, 4), (0, 4, 5), (1, 5, 10), (2, 1, 6), (3, 2, 7),
        (4, 3, 8), (5, 4, 9), (1, 10, 6), (2, 6, 7), (3, 7, 8), (4, 8, 9), (5, 9, 10), (6, 10, 11),
        (7, 6, 11), (8, 7, 11), (9, 8, 11), (10, 9, 11)
    ]
    return verts, tris


def __generate_cube_geometry():
    # cube with 6 sides centred at origin
    h = 0.5
    verts = [
        (h, h, -h), (h, -h, -h), (-h, -h, -h), (-h, h, -h), (h, h, h), (h, -h, h), (-h, -h, h), (-h, h, h)
    ]
    tris = [
        (0, 1, 2, 3), (4, 7, 6, 5),  (0, 4, 5, 1),  (1, 5, 6, 2),  (2, 6, 7, 3),  (4, 0, 3, 7)
    ]
    return verts, tris


def __get_object_geometry(bl_object):
    verts, faces = [], []
    for v in bl_object.data.vertices:
        verts.append((v.co.x, v.co.y, v.co.z))
    for p in bl_object.data.polygons:
        face = []
        for idx in p.vertices:
            face.append(idx)
        faces.append(tuple(face))
    return verts, faces


def __get_whitewater_particle_object_geometry(whitewater_type):
    dprops = __get_domain_properties()
    rprops = dprops.render

    if whitewater_type == 'FOAM':
        particle_mode = rprops.foam_particle_object_mode
        particle_object = rprops.foam_particle_object
    elif whitewater_type == 'BUBBLE':
        particle_mode = rprops.bubble_particle_object_mode
        particle_object = rprops.bubble_particle_object
    elif whitewater_type == 'SPRAY':
        particle_mode = rprops.spray_particle_object_mode
        particle_object = rprops.spray_particle_object
    elif whitewater_type == 'DUST':
        particle_mode = rprops.dust_particle_object_mode
        particle_object = rprops.dust_particle_object

    merge_settings = rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER'
    if merge_settings:
            use_builtin_object = rprops.whitewater_particle_object_mode != 'WHITEWATER_PARTICLE_CUSTOM'
            particle_mode = rprops.whitewater_particle_object_mode
    else:
        use_builtin_object = particle_mode != 'WHITEWATER_PARTICLE_CUSTOM'

    if use_builtin_object:
        if particle_mode == 'WHITEWATER_PARTICLE_ICOSPHERE':
            return __generate_icosphere_geometry()
        elif particle_mode == 'WHITEWATER_PARTICLE_CUBE':
            return __generate_cube_geometry()
    else:
        if merge_settings:
            particle_object = rprops.whitewater_particle_object

        if particle_object is None:
            # No custom particle object has been set
            return [], []
            
        bl_object = bpy.data.objects.get(particle_object.name)

        if bl_object is not None:
            return __get_object_geometry(bl_object)
        else:
            return [], []


def get_whitewater_particle_object_geometry(whitewater_type):
    return __get_whitewater_particle_object_geometry(whitewater_type)


def __get_whitewater_particle_object_scale(whitewater_type):
    dprops = __get_domain_properties()
    rprops = dprops.render

    if whitewater_type == 'FOAM':
        particle_object_scale = rprops.foam_particle_scale
    elif whitewater_type == 'BUBBLE':
        particle_object_scale = rprops.bubble_particle_scale
    elif whitewater_type == 'SPRAY':
        particle_object_scale = rprops.spray_particle_scale
    elif whitewater_type == 'DUST':
        particle_object_scale = rprops.dust_particle_scale

    if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
        return rprops.whitewater_particle_scale
    else:
        return particle_object_scale


def get_whitewater_particle_object_scale(whitewater_type):
    return __get_whitewater_particle_object_scale(whitewater_type)

def __get_whitewater_particle_object_display_bool(whitewater_type):
    global IS_RENDERING
    dprops = __get_domain_properties()
    rprops = dprops.render

    if whitewater_type == 'FOAM':
        particle_object_viewport_display = not rprops.only_display_foam_in_render
    elif whitewater_type == 'BUBBLE':
        particle_object_viewport_display = not rprops.only_display_bubble_in_render
    elif whitewater_type == 'SPRAY':
        particle_object_viewport_display = not rprops.only_display_spray_in_render
    elif whitewater_type == 'DUST':
        particle_object_viewport_display = not rprops.only_display_dust_in_render

    if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
        return (not rprops.only_display_whitewater_in_render) or IS_RENDERING
    else:
        return particle_object_viewport_display or IS_RENDERING


def __load_whitewater_particle_object_frame(frameno, force_reload=False, depsgraph=None):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.whitewater.enable_whitewater_simulation:
        return

    foam_verts,   foam_tris =   __get_whitewater_particle_object_geometry("FOAM")
    bubble_verts, bubble_tris = __get_whitewater_particle_object_geometry("BUBBLE")
    spray_verts,  spray_tris =  __get_whitewater_particle_object_geometry("SPRAY")
    dust_verts,   dust_tris =   __get_whitewater_particle_object_geometry("DUST")

    foam_scale =   __get_whitewater_particle_object_scale('FOAM')
    bubble_scale = __get_whitewater_particle_object_scale('BUBBLE')
    spray_scale =  __get_whitewater_particle_object_scale('SPRAY')
    dust_scale =   __get_whitewater_particle_object_scale('DUST')

    display_foam_particle =   __get_whitewater_particle_object_display_bool('FOAM')
    display_bubble_particle = __get_whitewater_particle_object_display_bool('BUBBLE')
    display_spray_particle =  __get_whitewater_particle_object_display_bool('SPRAY')
    display_dust_particle =   __get_whitewater_particle_object_display_bool('DUST')

    force_load = force_reload or IS_RENDERING
    if foam_verts and display_foam_particle and is_simulation_mesh_load_enabled('FOAM'):
        dprops.mesh_cache.foam.load_duplivert_object(
                foam_verts, foam_tris,
                foam_scale,
                force_load,
                depsgraph
                )
        dprops.mesh_cache.foam.set_duplivert_instance_type('VERTS')
        if vcu.is_blender_279():
            # In Blender 2.79, the duplivert object must not be hidden
            # in the viewport in order to be displayed in the viewport.
            dprops.mesh_cache.foam.set_duplivert_hide_viewport(False)
    else:
        dprops.mesh_cache.foam.set_duplivert_instance_type('NONE')
        if vcu.is_blender_279():
            dprops.mesh_cache.foam.set_duplivert_hide_viewport(True)
        
    if bubble_verts and display_bubble_particle and is_simulation_mesh_load_enabled('BUBBLE'):
        dprops.mesh_cache.bubble.load_duplivert_object(
                bubble_verts, bubble_tris,
                bubble_scale,
                force_load,
                depsgraph
                )
        dprops.mesh_cache.bubble.set_duplivert_instance_type('VERTS')
        if vcu.is_blender_279():
            dprops.mesh_cache.bubble.set_duplivert_hide_viewport(False)
    else:
        dprops.mesh_cache.bubble.set_duplivert_instance_type('NONE')
        if vcu.is_blender_279():
            dprops.mesh_cache.bubble.set_duplivert_hide_viewport(True)

    if spray_verts and display_spray_particle and is_simulation_mesh_load_enabled('SPRAY'):
        dprops.mesh_cache.spray.load_duplivert_object(
                spray_verts, spray_tris,
                spray_scale,
                force_load,
                depsgraph
                )
        dprops.mesh_cache.spray.set_duplivert_instance_type('VERTS')
        if vcu.is_blender_279():
            dprops.mesh_cache.spray.set_duplivert_hide_viewport(False)
    else:
        dprops.mesh_cache.spray.set_duplivert_instance_type('NONE')
        if vcu.is_blender_279():
            dprops.mesh_cache.spray.set_duplivert_hide_viewport(True)

    if dust_verts and display_dust_particle and is_simulation_mesh_load_enabled('DUST'):
        dprops.mesh_cache.dust.load_duplivert_object(
                dust_verts, dust_tris,
                dust_scale,
                force_load,
                depsgraph
                )
        dprops.mesh_cache.dust.set_duplivert_instance_type('VERTS')
        if vcu.is_blender_279():
            dprops.mesh_cache.dust.set_duplivert_hide_viewport(False)
    else:
        dprops.mesh_cache.dust.set_duplivert_instance_type('NONE')
        if vcu.is_blender_279():
            dprops.mesh_cache.dust.set_duplivert_hide_viewport(True)


def __load_whitewater_frame(frameno, force_reload=False, depsgraph=None):
    __load_whitewater_particle_frame(frameno, force_reload, depsgraph)
    __load_whitewater_particle_object_frame(frameno, force_reload, depsgraph)


def __load_fluid_particle_debug_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_fluid_particles:
        return

    force_load = force_reload or IS_RENDERING

    if is_simulation_mesh_load_enabled('PARTICLE_DEBUG'):
        dprops.mesh_cache.gl_particles.load_frame(frameno, force_load)


def __load_obstacle_debug_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_internal_obstacle_mesh or not dprops.debug.internal_obstacle_mesh_visibility:
        return

    force_load = force_reload or IS_RENDERING
    if is_simulation_mesh_load_enabled('OBSTACLE_DEBUG'):
        dprops.mesh_cache.obstacle.load_frame(frameno, force_load)


def __load_force_field_debug_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_force_field:
        return

    force_load = force_reload or IS_RENDERING
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
    __load_whitewater_frame(frameno, force_reload, depsgraph)
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

    if dprops.whitewater.enable_whitewater_simulation:
        dprops.mesh_cache.foam.initialize_duplivert_object()
        dprops.mesh_cache.bubble.initialize_duplivert_object()
        dprops.mesh_cache.spray.initialize_duplivert_object()
        dprops.mesh_cache.dust.initialize_duplivert_object()


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

    global RENDER_PRE_FRAME_NUMBER
    RENDER_PRE_FRAME_NUMBER = __get_render_pre_current_frame()

    is_running_cmd = bpy.app.background
    if not is_running_cmd:
        features_dict = api_utils.get_enabled_features_affected_by_T88811()
        if features_dict is not None:
            warning_string = api_utils.get_T88811_cmd_warning_string(features_dict)
            print(warning_string)

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

    if is_rendering() and vcu.is_blender_28():
        if not scene.render.use_lock_interface:
                print("FLIP FLUIDS WARNING: The Blender interface should be locked during render to prevent render crashes (Blender > Render > Lock Interface).")
        if not vcu.is_blender_281():
            print("FLIP FLUIDS WARNING: Blender 2.80 contains a bug that can cause frequent render crashes and incorrect render results. Blender version 2.81 or higher is recommended.")

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


def is_rendering():
    global IS_RENDERING
    return IS_RENDERING
