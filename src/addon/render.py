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

import bpy

IS_RENDERING = False
IS_FRAME_REQUIRING_RELOAD = False


def frame_change_pre(scene):
    global IS_RENDERING
    if not __is_domain_set():
        return
        
    __load_frame(__get_current_frame())
    dprops = __get_domain_properties()
    dprops.render.current_frame = __get_current_frame()

    IS_RENDERING = False


def render_pre(scene):
    global IS_RENDERING
    IS_RENDERING = True


def render_post(scene):
    global IS_RENDERING
    IS_RENDERING = False


def render_cancel(scene):
    global IS_RENDERING
    global IS_FRAME_REQUIRING_RELOAD
    IS_RENDERING = False
    IS_FRAME_REQUIRING_RELOAD = True


def render_complete(scene):
    global IS_FRAME_REQUIRING_RELOAD
    IS_FRAME_REQUIRING_RELOAD = True


def scene_update_post(scene):
    global IS_FRAME_REQUIRING_RELOAD
    if IS_FRAME_REQUIRING_RELOAD:
        IS_FRAME_REQUIRING_RELOAD = False
        reload_frame(__get_current_frame())


def reload_frame(frameno):
    if not __is_domain_set():
        return
    __load_frame(frameno, True)
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    dprops.render.current_frame = frameno


def __is_domain_set():
    return bpy.context.scene.flip_fluid.get_num_domain_objects() != 0 


def __get_domain_object():
    return bpy.context.scene.flip_fluid.get_domain_object() 


def __get_domain_properties():
    return bpy.context.scene.flip_fluid.get_domain_properties() 


def __get_current_frame():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return 0 

    if dprops.render.hold_frame:
        current_frame = dprops.render.hold_frame_number
    else:
        current_frame = bpy.context.scene.frame_current
    return current_frame - bpy.context.scene.flip_fluid_helper.playback_frame_offset


def __get_display_mode():
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if IS_RENDERING:
        mode = dprops.render.render_display
    else:
        mode = dprops.render.viewport_display
    return mode


def __get_whitewater_display_mode():
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if IS_RENDERING:
        mode = dprops.render.whitewater_render_display
    else:
        mode = dprops.render.whitewater_viewport_display
    return mode


def __load_surface_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    cache = dprops.mesh_cache
    display_mode = __get_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        cache.surface.mesh_prefix = ""
        cache.surface.mesh_display_name_prefix = "final_"
    elif display_mode == 'DISPLAY_PREVIEW':
        cache.surface.mesh_prefix = "preview"
        cache.surface.mesh_display_name_prefix = "preview_"
    elif display_mode == 'DISPLAY_NONE':
        cache.surface.mesh_prefix = "none"
        cache.surface.mesh_display_name_prefix = "none_"

    force_load = force_reload or IS_RENDERING
    cache.surface.load_frame(frameno, force_load)


def __load_whitewater_particle_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    domain_object = __get_domain_object()
    dprops = __get_domain_properties()
    rprops = dprops.render
    cache = dprops.mesh_cache
    if not dprops.whitewater.enable_whitewater_simulation:
        return

    display_mode = __get_whitewater_display_mode()
    if display_mode == 'DISPLAY_FINAL':
        cache.foam.mesh_prefix = "foam"
        cache.bubble.mesh_prefix = "bubble"
        cache.spray.mesh_prefix = "spray"
        cache.foam.mesh_display_name_prefix = "final_"
        cache.bubble.mesh_display_name_prefix = "final_"
        cache.spray.mesh_display_name_prefix = "final_"
    elif display_mode == 'DISPLAY_PREVIEW':
        cache.foam.mesh_prefix = "foam"
        cache.bubble.mesh_prefix = "bubble"
        cache.spray.mesh_prefix = "spray"
        cache.foam.mesh_display_name_prefix = "preview_"
        cache.bubble.mesh_display_name_prefix = "preview_"
        cache.spray.mesh_display_name_prefix = "preview_"
    elif display_mode == 'DISPLAY_NONE':
        cache.foam.mesh_prefix = "foam_none"
        cache.bubble.mesh_prefix = "bubble_none"
        cache.spray.mesh_prefix = "spray_none"
        cache.foam.mesh_display_name_prefix = "none_"
        cache.bubble.mesh_display_name_prefix = "none_"
        cache.spray.mesh_display_name_prefix = "none_"

    if rprops.whitewater_view_settings_mode == 'VIEW_SETTINGS_WHITEWATER':
        if display_mode == 'DISPLAY_FINAL':
            pct = rprops.render_whitewater_pct
        elif display_mode == 'DISPLAY_PREVIEW':
            pct = rprops.viewport_whitewater_pct
        elif display_mode == 'DISPLAY_NONE':
            pct = 0
        foam_pct = bubble_pct = spray_pct = pct
    else:
        if display_mode == 'DISPLAY_FINAL':
            foam_pct = rprops.render_foam_pct
            bubble_pct = rprops.render_bubble_pct
            spray_pct = rprops.render_spray_pct
        elif display_mode == 'DISPLAY_PREVIEW':
            foam_pct = rprops.viewport_foam_pct
            bubble_pct = rprops.viewport_bubble_pct
            spray_pct = rprops.viewport_spray_pct
        elif display_mode == 'DISPLAY_NONE':
            foam_pct = bubble_pct = spray_pct = 0

    cache.foam.wwp_import_percentage = foam_pct
    cache.bubble.wwp_import_percentage = bubble_pct
    cache.spray.wwp_import_percentage = spray_pct

    force_load = force_reload or IS_RENDERING
    cache.foam.load_frame(frameno, force_load)
    cache.bubble.load_frame(frameno, force_load)
    cache.spray.load_frame(frameno, force_load)


def __delete_object(obj):
    mesh_data = obj.data
    bpy.data.objects.remove(obj, True)
    mesh_data.user_clear()
    bpy.data.meshes.remove(mesh_data)


def __generate_icosphere():
    # Icosphere with 1 subdivision centred at origin
    verts = [
        (0.0000, 0.0000, -1.0000),
        (0.7236, -0.5257, -0.4472),
        (-0.2764, -0.8506, -0.4472),
        (-0.8944, 0.0000, -0.4472),
        (-0.2764, 0.8506, -0.4472),
        (0.7236, 0.5257, -0.4472),
        (0.2764, -0.8506, 0.4472),
        (-0.7236, -0.5257, 0.4472),
        (-0.7236, 0.5257, 0.4472),
        (0.2764, 0.8506, 0.4472),
        (0.8944, 0.0000, 0.4472),
        (0.0000, 0.0000, 1.0000)
    ]

    faces = [
        (0, 1, 2),
        (1, 0, 5),
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (1, 5, 10),
        (2, 1, 6),
        (3, 2, 7),
        (4, 3, 8),
        (5, 4, 9),
        (1, 10, 6),
        (2, 6, 7),
        (3, 7, 8),
        (4, 8, 9),
        (5, 9, 10),
        (6, 10, 11),
        (7, 6, 11),
        (8, 7, 11),
        (9, 8, 11),
        (10, 9, 11)
    ]

    mesh = bpy.data.meshes.new("IcosphereMesh")
    mesh.from_pydata(verts, [], faces)
    for p in mesh.polygons:
        p.use_smooth = True

    obj = bpy.data.objects.new("Icosphere", mesh)
    bpy.context.scene.objects.link(obj) 

    return obj


def __load_whitewater_particle_object_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    domain_object = __get_domain_object()
    dprops = __get_domain_properties()
    rprops = dprops.render
    cache = dprops.mesh_cache
    if not dprops.whitewater.enable_whitewater_simulation:
        return

    if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
        foam_object = rprops.whitewater_particle_object
        bubble_object = rprops.whitewater_particle_object
        spray_object = rprops.whitewater_particle_object
    else:
        foam_object = rprops.foam_particle_object
        bubble_object = rprops.bubble_particle_object
        spray_object = rprops.spray_particle_object

    foam_object = bpy.data.objects.get(foam_object)
    bubble_object = bpy.data.objects.get(bubble_object)
    spray_object = bpy.data.objects.get(spray_object)

    destroy_foam_object = destroy_bubble_object = destroy_spray_object = False
    if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
        if rprops.whitewater_use_icosphere_object:
            foam_object = __generate_icosphere()
            bubble_object = __generate_icosphere()
            spray_object = __generate_icosphere()
            destroy_foam_object = destroy_bubble_object = destroy_spray_object = True
    else:
        if rprops.foam_use_icosphere_object:
            foam_object = __generate_icosphere()
            destroy_foam_object = True
        if rprops.bubble_use_icosphere_object:
            bubble_object = __generate_icosphere()
            destroy_bubble_object = True
        if rprops.spray_use_icosphere_object:
            spray_object = __generate_icosphere()
            destroy_spray_object = True

    if rprops.whitewater_particle_object_settings_mode == 'WHITEWATER_OBJECT_SETTINGS_WHITEWATER':
        display_viewport = not rprops.only_display_whitewater_in_render
        display_object = IS_RENDERING or display_viewport
        display_foam_viewport = display_bubble_viewport = display_spray_viewport = display_viewport
        display_foam = display_bubble = display_spray = display_object
        foam_scale = bubble_scale = spray_scale = rprops.whitewater_particle_scale
    else:
        display_foam_viewport = not rprops.only_display_foam_in_render
        display_bubble_viewport = not rprops.only_display_bubble_in_render
        display_spray_viewport = not rprops.only_display_spray_in_render
        display_foam = IS_RENDERING or display_foam_viewport
        display_bubble = IS_RENDERING or display_bubble_viewport
        display_spray = IS_RENDERING or display_spray_viewport
        foam_scale = rprops.foam_particle_scale
        bubble_scale = rprops.bubble_particle_scale
        spray_scale = rprops.spray_particle_scale

    force_load = force_reload or IS_RENDERING
    if foam_object and display_foam:
        cache.foam.load_duplivert_object(
                foam_object, 
                foam_scale, 
                display_foam_viewport, 
                force_load
                )
    else:
        cache.foam.unload_duplivert_object()
        
    if bubble_object and display_bubble:
        cache.bubble.load_duplivert_object(
                bubble_object, 
                bubble_scale, 
                display_bubble_viewport, 
                force_load
                )
    else:
        cache.bubble.unload_duplivert_object()

    if spray_object and display_spray:
        cache.spray.load_duplivert_object(
                spray_object, 
                spray_scale, 
                display_spray_viewport, 
                force_load
                )
    else:
        cache.spray.unload_duplivert_object()

    if destroy_foam_object:
        __delete_object(foam_object)
    if destroy_bubble_object:
        __delete_object(bubble_object)
    if destroy_spray_object:
        __delete_object(spray_object)

    bpy.context.scene.update()


def __load_whitewater_frame(frameno, force_reload=False):
    __load_whitewater_particle_frame(frameno, force_reload)
    __load_whitewater_particle_object_frame(frameno, force_reload)


def __load_obstacle_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_internal_obstacle_mesh:
        return

    force_load = force_reload or IS_RENDERING
    dprops.mesh_cache.obstacle.load_frame(frameno, force_load)


def __load_particle_frame(frameno, force_reload=False):
    global IS_RENDERING
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    if not dprops.debug.export_fluid_particles:
        return

    force_load = force_reload or IS_RENDERING
    dprops.mesh_cache.gl_particles.load_frame(frameno, force_load)


def __load_frame(frameno, force_reload=False):
    if not __is_domain_set():
        return

    dprops = __get_domain_properties()
    dprops.mesh_cache.initialize_cache_settings()
    __load_surface_frame(frameno, force_reload)
    __load_whitewater_frame(frameno, force_reload)
    __load_particle_frame(frameno, force_reload)
    __load_obstacle_frame(frameno, force_reload)
