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

import bpy, blf, math, colorsys
import mathutils
from mathutils import Vector, Matrix

from bpy.props import (
        IntProperty
        )

from ..objects.flip_fluid_aabb import AABB
from ..utils import ui_utils
from ..utils import geometry_utils
from ..utils import version_compatibility_utils as vcu
from .. import render

import gpu
from gpu_extras.batch import batch_for_shader


def _rotate_vertices_to_domain_OBB(bl_vertices, bl_domain, slerp=1.0):
    dprops = bl_domain.flip_fluid.domain
    rotation_matrix = dprops.rotation_matrix
    if slerp < 1.0:
        mat_a = Matrix.Identity(4)
        mat_b = rotation_matrix
        quat_a = mat_a.to_quaternion()
        quat_b = mat_b.to_quaternion()
        slerp_quat = quat_a.slerp(quat_b, slerp)
        rotation_matrix = slerp_quat.to_matrix().to_4x4()

    return geometry_utils.apply_rotation_around_point_to_vertices(bl_vertices, rotation_matrix, dprops.AABB_min)


DRAW_VERTICES_X = []
DRAW_VERTICES_Y = []
DRAW_VERTICES_Z = []
DRAW_VERTICES_INTERNAL_X = []
DRAW_VERTICES_INTERNAL_Y = []
DRAW_VERTICES_INTERNAL_Z = []
BOUNDS_DRAW_VERTICES = []
BOUNDS_DRAW_VERTICES_INTERNAL = []
DOMAIN_DRAW_VERTICES_INTERNAL = []
def _clear_global_draw_data():
    global DRAW_VERTICES_X, DRAW_VERTICES_Y, DRAW_VERTICES_Z
    global DRAW_VERTICES_INTERNAL_X, DRAW_VERTICES_INTERNAL_Y, DRAW_VERTICES_INTERNAL_Z
    global BOUNDS_DRAW_VERTICES
    global BOUNDS_DRAW_VERTICES_INTERNAL
    global DOMAIN_DRAW_VERTICES_INTERNAL

    DRAW_VERTICES_X, DRAW_VERTICES_Y, DRAW_VERTICES_Z = [], [], []
    DRAW_VERTICES_INTERNAL_X, DRAW_VERTICES_INTERNAL_Y, DRAW_VERTICES_INTERNAL_Z = [], [], []
    BOUNDS_DRAW_VERTICES = []
    BOUNDS_DRAW_VERTICES_INTERNAL = []
    DOMAIN_DRAW_VERTICES_INTERNAL = []


def update_debug_grid_geometry(context):
    if render.is_rendering():
        # This method does not need to be run while rendering. Can cause
        # crashes on certain systems.
        return

    global DRAW_VERTICES_X, DRAW_VERTICES_Y, DRAW_VERTICES_Z
    global DRAW_VERTICES_INTERNAL_X, DRAW_VERTICES_INTERNAL_Y, DRAW_VERTICES_INTERNAL_Z
    global BOUNDS_DRAW_VERTICES
    global BOUNDS_DRAW_VERTICES_INTERNAL
    global DOMAIN_DRAW_VERTICES_INTERNAL

    _clear_global_draw_data()

    domain = context.scene.flip_fluid.get_domain_object()
    if domain is None:
        return
    dprops = context.scene.flip_fluid.get_domain_properties()

    if not dprops.debug.is_simulation_grid_debugging_enabled():
        return

    minp, maxp = dprops.AABB_min, dprops.AABB_max
    bbox = AABB.from_corners(minp, maxp)
    max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
    internal_grid_slerp = 1.0 - dprops.debug.internal_simulation_grid_interpolation

    if dprops.debug.grid_display_mode == 'GRID_DISPLAY_SIMULATION':
        isize, jsize, ksize, dx = dprops.simulation.get_viewport_grid_dimensions()
    elif dprops.debug.grid_display_mode == 'GRID_DISPLAY_PREVIEW':
        presolution = dprops.simulation.preview_resolution
        isize, jsize, ksize, dx = dprops.simulation.get_viewport_grid_dimensions(resolution=presolution)
    else:
        isize, jsize, ksize, dx = dprops.simulation.get_viewport_grid_dimensions()

    if dprops.debug.grid_display_mode == 'GRID_DISPLAY_MESH':
        isize *= (dprops.surface.subdivisions + 1)
        jsize *= (dprops.surface.subdivisions + 1)
        ksize *= (dprops.surface.subdivisions + 1)
        dx /= (dprops.surface.subdivisions + 1)

    elif dprops.debug.grid_display_mode == 'GRID_DISPLAY_FORCE_FIELD':
        isize, jsize, ksize, dx = dprops.simulation.get_viewport_grid_dimensions()
        reduction = dprops.world.get_force_field_grid_reduction()
        isize = int(math.ceil(isize / reduction))
        jsize = int(math.ceil(jsize / reduction))
        ksize = int(math.ceil(ksize / reduction))
        dx *= reduction

    disp_scale = dprops.debug.grid_display_scale
    igrid = math.ceil(isize / disp_scale)
    jgrid = math.ceil(jsize / disp_scale)
    kgrid = math.ceil(ksize / disp_scale)
    dxgrid = dx * disp_scale

    if dprops.debug.snap_offsets_to_grid:
        xoffset = math.ceil(dprops.debug.debug_grid_offsets[2] * igrid) * dxgrid
        yoffset = math.ceil(dprops.debug.debug_grid_offsets[1] * jgrid) * dxgrid
        zoffset = math.ceil(dprops.debug.debug_grid_offsets[0] * kgrid) * dxgrid
    else:
        xoffset = dprops.debug.debug_grid_offsets[2] * igrid * dxgrid
        yoffset = dprops.debug.debug_grid_offsets[1] * jgrid * dxgrid
        zoffset = dprops.debug.debug_grid_offsets[0] * kgrid * dxgrid

    # Grid Draw Data
    vertices_z = []
    for i in range(igrid + 1):
        vertices_z.append([bbox.x + i * dxgrid, bbox.y, bbox.z + zoffset])
        vertices_z.append([bbox.x + i * dxgrid, bbox.y + jgrid * dxgrid, bbox.z + zoffset])
    for j in range(jgrid + 1):
        vertices_z.append([bbox.x, bbox.y + j * dxgrid, bbox.z + zoffset])
        vertices_z.append([bbox.x + igrid * dxgrid, bbox.y + j * dxgrid, bbox.z + zoffset])
    vertices_z = [Vector(v) for v in vertices_z]
    DRAW_VERTICES_Z = _rotate_vertices_to_domain_OBB(vertices_z, domain)
    DRAW_VERTICES_INTERNAL_Z = _rotate_vertices_to_domain_OBB(vertices_z, domain, slerp=internal_grid_slerp)

    vertices_y = []
    for i in range(igrid + 1):
        vertices_y.append([bbox.x + i * dxgrid, bbox.y + yoffset, bbox.z])
        vertices_y.append([bbox.x + i * dxgrid, bbox.y + yoffset, bbox.z + kgrid * dxgrid])
    for k in range(kgrid + 1):
        vertices_y.append([bbox.x, bbox.y + yoffset, bbox.z + k * dxgrid])
        vertices_y.append([bbox.x + igrid * dxgrid, bbox.y + yoffset, bbox.z + k * dxgrid])
    vertices_y = [Vector(v) for v in vertices_y]
    DRAW_VERTICES_Y = _rotate_vertices_to_domain_OBB(vertices_y, domain)
    DRAW_VERTICES_INTERNAL_Y = _rotate_vertices_to_domain_OBB(vertices_y, domain, slerp=internal_grid_slerp)

    vertices_z = []
    for j in range(jgrid + 1):
        vertices_z.append([bbox.x + xoffset, bbox.y + j * dxgrid, bbox.z])
        vertices_z.append([bbox.x + xoffset, bbox.y + j * dxgrid, bbox.z + kgrid * dxgrid])
    for k in range(kgrid + 1):
        vertices_z.append([bbox.x + xoffset, bbox.y, bbox.z + k * dxgrid])
        vertices_z.append([bbox.x + xoffset, bbox.y + jgrid * dxgrid, bbox.z + k * dxgrid])
    vertices_z = [Vector(v) for v in vertices_z]
    DRAW_VERTICES_X = _rotate_vertices_to_domain_OBB(vertices_z, domain)
    DRAW_VERTICES_INTERNAL_X = _rotate_vertices_to_domain_OBB(vertices_z, domain, slerp=internal_grid_slerp)


    # Bounds Draw Data
    def get_bounds_vertices(minp, maxp):
        vertices_bounds = [
            (minp.x, minp.y, minp.z), (maxp.x, minp.y, minp.z), (minp.x, maxp.y, minp.z), (maxp.x, maxp.y, minp.z), 
            (minp.x, minp.y, maxp.z), (maxp.x, minp.y, maxp.z), (minp.x, maxp.y, maxp.z), (maxp.x, maxp.y, maxp.z),
            (minp.x, minp.y, minp.z), (minp.x, maxp.y, minp.z), (maxp.x, minp.y, minp.z), (maxp.x, maxp.y, minp.z),
            (minp.x, minp.y, maxp.z), (minp.x, maxp.y, maxp.z), (maxp.x, minp.y, maxp.z), (maxp.x, maxp.y, maxp.z),
            (minp.x, minp.y, minp.z), (minp.x, minp.y, maxp.z), (maxp.x, minp.y, minp.z), (maxp.x, minp.y, maxp.z),
            (minp.x, maxp.y, minp.z), (minp.x, maxp.y, maxp.z), (maxp.x, maxp.y, minp.z), (maxp.x, maxp.y, maxp.z)
            ]
        vertices_bounds = [Vector(v) for v in vertices_bounds]
        return vertices_bounds

    native_dx = max_dim / dprops.simulation.resolution
    solid_width = Vector([1.5 * native_dx] * 3)
    dimensions = Vector([math.ceil(bbox.xdim / native_dx) * native_dx,
                         math.ceil(bbox.ydim / native_dx) * native_dx,
                         math.ceil(bbox.zdim / native_dx) * native_dx])
    minp = Vector([bbox.x, bbox.y, bbox.z])
    maxp = Vector([bbox.x, bbox.y, bbox.z]) + dimensions

    minp = minp + solid_width
    maxp = maxp - solid_width
    if minp.x > maxp.x:
        minp.x = bbox.x + 0.5 * isize * dx
        maxp.x = minp.x
    if minp.y > maxp.y:
        minp.y = bbox.y + 0.5 * jsize * dx
        maxp.y = minp.y
    if minp.z > maxp.z:
        minp.z = bbox.z + 0.5 * ksize * dx
        maxp.z = minp.z

    vertices_bounds = get_bounds_vertices(minp, maxp)
    BOUNDS_DRAW_VERTICES = _rotate_vertices_to_domain_OBB(vertices_bounds, domain)
    BOUNDS_DRAW_VERTICES_INTERNAL = _rotate_vertices_to_domain_OBB(vertices_bounds, domain, slerp=internal_grid_slerp)

    minp_domain, maxp_domain = dprops.AABB_min, dprops.AABB_max
    vertices_domain = get_bounds_vertices(minp_domain, maxp_domain)
    DOMAIN_DRAW_VERTICES_INTERNAL = _rotate_vertices_to_domain_OBB(vertices_domain, domain, slerp=internal_grid_slerp)


class FlipFluidDrawDebugGrid(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.draw_debug_grid"
    bl_label = "Draw Debug Grid"
    bl_description = "Draw debug view of the domain simulation grid"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return True


    def draw_callback_3d(self, context):
        if render.is_rendering():
            # This method does not need to be run while rendering. Can cause
            # crashes on certain systems.
            return
            
        global DRAW_VERTICES_X, DRAW_VERTICES_Y, DRAW_VERTICES_Z
        global DRAW_VERTICES_INTERNAL_X, DRAW_VERTICES_INTERNAL_Y, DRAW_VERTICES_INTERNAL_Z
        global BOUNDS_DRAW_VERTICES
        global BOUNDS_DRAW_VERTICES_INTERNAL
        global DOMAIN_DRAW_VERTICES_INTERNAL

        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return
        dprops = context.scene.flip_fluid.get_domain_properties()

        if vcu.get_object_hide_viewport(domain):
            return

        display_grid = dprops.debug.display_simulation_grid
        display_bounds = dprops.debug.display_domain_bounds
        display_internal_grid = dprops.debug.display_internal_simulation_grid
        x_draw_color = dprops.debug.x_grid_color
        y_draw_color = dprops.debug.y_grid_color
        z_draw_color = dprops.debug.z_grid_color
        bounds_draw_color = dprops.debug.domain_bounds_color
        internal_opacity = dprops.debug.internal_simulation_grid_opacity

        # (Vertex list, RGBA tuple, Draw True/False)
        draw_info = [
            (DRAW_VERTICES_X, (*z_draw_color, 1.0), display_grid and dprops.debug.enabled_debug_grids[2]),
            (DRAW_VERTICES_Y, (*y_draw_color, 1.0), display_grid and dprops.debug.enabled_debug_grids[1]),
            (DRAW_VERTICES_Z, (*x_draw_color, 1.0), display_grid and dprops.debug.enabled_debug_grids[0]),
            (BOUNDS_DRAW_VERTICES, (*bounds_draw_color, 1.0), display_bounds),

            (DRAW_VERTICES_INTERNAL_X, (*z_draw_color, internal_opacity), display_internal_grid and dprops.debug.enabled_debug_grids[2]),
            (DRAW_VERTICES_INTERNAL_Y, (*y_draw_color, internal_opacity), display_internal_grid and dprops.debug.enabled_debug_grids[1]),
            (DRAW_VERTICES_INTERNAL_Z, (*x_draw_color, internal_opacity), display_internal_grid and dprops.debug.enabled_debug_grids[0]),
            (BOUNDS_DRAW_VERTICES_INTERNAL, (*bounds_draw_color, internal_opacity), display_internal_grid),
            (DOMAIN_DRAW_VERTICES_INTERNAL, (1.0, 1.0, 1.0, internal_opacity), display_internal_grid)
            ]

        for info in draw_info:
            draw_enabled = info[2]
            if not draw_enabled:
                continue

            vertices = info[0]
            color = info[1]

            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINES', {"pos": vertices})
            shader.bind()

            shader.uniform_float("color", color)
            shader.uniform_bool("lineSmooth", True)
            shader.uniform_float("lineWidth", 1.0)
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h))

            gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('LESS_EQUAL')
            gpu.state.depth_mask_set(True)

            batch.draw(shader)

            gpu.state.blend_set('NONE')
            gpu.state.depth_test_set('NONE')
            gpu.state.depth_mask_set(False)


    def modal(self, context, event):
        if not event.type == 'TIMER':
            return {'PASS_THROUGH'}
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None or not dprops.debug.is_simulation_grid_debugging_enabled():
            self.cancel(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}


    def invoke(self, context, event):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return
        args = (context,)
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_3d, args, 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        dprops.debug.is_draw_debug_grid_operator_running = True
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        context.window_manager.event_timer_remove(self._timer)
        ui_utils.force_ui_redraw()
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            dprops.debug.is_draw_debug_grid_operator_running = False


def register():
    bpy.utils.register_class(FlipFluidDrawDebugGrid)


def unregister():
    bpy.utils.unregister_class(FlipFluidDrawDebugGrid)
