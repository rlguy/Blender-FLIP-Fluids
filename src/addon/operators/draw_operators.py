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

import bpy, bgl, blf, math, colorsys
from bpy.props import (
        IntProperty
        )

from ..objects.flip_fluid_aabb import AABB
from ..utils import ui_utils


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


    def draw_callback_2d(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return
        dprops = context.scene.flip_fluid.get_domain_properties()

        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_PREVIEW':
            resolution = dprops.simulation.preview_resolution
        else:
            resolution = dprops.simulation.resolution

        bbox = AABB.from_blender_object(domain)
        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
        if dprops.simulation.lock_cell_size:
            unlocked_dx = max_dim / resolution
            locked_dx = dprops.simulation.locked_cell_size
            dx = locked_dx
            if abs(locked_dx - unlocked_dx) < 1e-6:
                dx = unlocked_dx
        else:
            dx = max_dim / resolution

        isize = math.ceil(bbox.xdim / dx)
        jsize = math.ceil(bbox.ydim / dx)
        ksize = math.ceil(bbox.zdim / dx)
        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_MESH':
            isize *= (dprops.surface.subdivisions + 1)
            jsize *= (dprops.surface.subdivisions + 1)
            ksize *= (dprops.surface.subdivisions + 1)
            dx /= (dprops.surface.subdivisions + 1)

        width = context.region.width
        height = context.region.height
        xstart = 20

        bgl.glEnable(bgl.GL_BLEND)

        font_id = 0
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)

        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_SIMULATION':
            blf.size(font_id, 20, 72)
            blf.position(font_id, xstart, height - 50, 0)
            blf.draw(font_id, "Simulation Grid")

            blf.size(font_id, 15, 72)
            blf.position(font_id, xstart + 10, height - 80, 0)
            blf.draw(font_id, "Grid Resolution: " + str(isize) + " x " + str(jsize) + " x " + str(ksize))

            blf.position(font_id, xstart + 10, height - 105, 0)
            blf.draw(font_id, "Grid Cell Count: " + format(isize*jsize*ksize, ",").replace(",", " "))

            blf.position(font_id, xstart + 10, height - 130, 0)
            blf.draw(font_id, "Grid Cell Width: " + str(round(dx, 4)))
        elif dprops.debug.grid_display_mode == 'GRID_DISPLAY_MESH':
            if dprops.surface.compute_chunk_mode == 'COMPUTE_CHUNK_MODE_AUTO':
                compute_chunks = dprops.surface.compute_chunks_auto
            else:
                compute_chunks = dprops.surface.compute_chunks_fixed

            blf.size(font_id, 20, 72)
            blf.position(font_id, xstart, height - 50, 0)
            blf.draw(font_id, "Final Surface Mesh Grid")

            blf.size(font_id, 15, 72)
            blf.position(font_id, xstart + 10, height - 80, 0)
            blf.draw(font_id, "Subdivisions: " + str(dprops.surface.subdivisions))

            blf.position(font_id, xstart + 10, height - 105, 0)
            blf.draw(font_id, "Compute Chunks: " + str(compute_chunks))

            blf.position(font_id, xstart + 10, height - 130, 0)
            blf.draw(font_id, "Grid Resolution: " + str(isize) + " x " + str(jsize) + " x " + str(ksize))

            num_cells = isize*jsize*ksize
            num_cells_str = format(num_cells, ",").replace(",", " ")
            chunk_cells_str = format(math.ceil(num_cells / compute_chunks), ",").replace(",", " ")
            blf.position(font_id, xstart + 10, height - 155, 0)
            blf.draw(font_id, "Grid Cell Count: " + num_cells_str + " (" + chunk_cells_str + " / chunk)")

            blf.position(font_id, xstart + 10, height - 180, 0)
            blf.draw(font_id, "Grid Cell Width: " + str(round(dx, 4)))
        elif dprops.debug.grid_display_mode == 'GRID_DISPLAY_PREVIEW':
            blf.size(font_id, 20, 72)
            blf.position(font_id, xstart, height - 50, 0)
            blf.draw(font_id, "Preview Surface Mesh Grid")

            blf.size(font_id, 15, 72)
            blf.position(font_id, xstart + 10, height - 80, 0)
            blf.draw(font_id, "Grid Resolution: " + str(isize) + " x " + str(jsize) + " x " + str(ksize))

            num_cells = isize*jsize*ksize
            num_cells_str = format(num_cells, ",").replace(",", " ")
            blf.position(font_id, xstart + 10, height - 105, 0)
            blf.draw(font_id, "Grid Cell Width: " + str(round(dx, 4)))

        bgl.glEnd()
        bgl.glLineWidth(1.0)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


    def draw_callback_3d(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return
        dprops = context.scene.flip_fluid.get_domain_properties()

        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_PREVIEW':
            resolution = dprops.simulation.preview_resolution
        else:
            resolution = dprops.simulation.resolution

        bbox = AABB.from_blender_object(domain)
        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
        if dprops.simulation.lock_cell_size:
            unlocked_dx = max_dim / resolution
            locked_dx = dprops.simulation.locked_cell_size
            dx = locked_dx
            if abs(locked_dx - unlocked_dx) < 1e-6:
                dx = unlocked_dx
        else:
            dx = max_dim / resolution

        isize = math.ceil(bbox.xdim / dx)
        jsize = math.ceil(bbox.ydim / dx)
        ksize = math.ceil(bbox.zdim / dx)
        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_MESH':
            isize *= (dprops.surface.subdivisions + 1)
            jsize *= (dprops.surface.subdivisions + 1)
            ksize *= (dprops.surface.subdivisions + 1)
            dx /= (dprops.surface.subdivisions + 1)

        disp_scale = dprops.debug.grid_display_scale
        igrid = math.ceil(isize / disp_scale)
        jgrid = math.ceil(jsize / disp_scale)
        kgrid = math.ceil(ksize / disp_scale)
        dxgrid = dx * disp_scale

        if dprops.debug.snap_offsets_to_grid:
            xoffset = math.ceil(dprops.debug.debug_grid_offsets[0] * igrid) * dxgrid
            yoffset = math.ceil(dprops.debug.debug_grid_offsets[1] * jgrid) * dxgrid
            zoffset = math.ceil(dprops.debug.debug_grid_offsets[2] * kgrid) * dxgrid
        else:
            xoffset = dprops.debug.debug_grid_offsets[0] * igrid * dxgrid
            yoffset = dprops.debug.debug_grid_offsets[1] * jgrid * dxgrid
            zoffset = dprops.debug.debug_grid_offsets[2] * kgrid * dxgrid

        x_color = dprops.debug.x_grid_color
        y_color = dprops.debug.y_grid_color
        z_color = dprops.debug.z_grid_color

        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINES)
        if dprops.debug.enabled_debug_grids[2]:
            bgl.glColor4f(*z_color, 1.0)
            for i in range(igrid + 1):
                bgl.glVertex3f(bbox.x + i * dxgrid, bbox.y, bbox.z + zoffset)
                bgl.glVertex3f(bbox.x + i * dxgrid, bbox.y + jgrid * dxgrid, bbox.z + zoffset)
            for j in range(jgrid + 1):
                bgl.glVertex3f(bbox.x, bbox.y + j * dxgrid, bbox.z + zoffset)
                bgl.glVertex3f(bbox.x + igrid * dxgrid, bbox.y + j * dxgrid, bbox.z + zoffset)

        if dprops.debug.enabled_debug_grids[1]:
            bgl.glColor4f(*y_color, 1.0)
            for i in range(igrid + 1):
                bgl.glVertex3f(bbox.x + i * dxgrid, bbox.y + yoffset, bbox.z)
                bgl.glVertex3f(bbox.x + i * dxgrid, bbox.y + yoffset, bbox.z + kgrid * dxgrid)
            for k in range(kgrid + 1):
                bgl.glVertex3f(bbox.x, bbox.y + yoffset, bbox.z + k * dxgrid)
                bgl.glVertex3f(bbox.x + igrid * dxgrid, bbox.y + yoffset, bbox.z + k * dxgrid)

        if dprops.debug.enabled_debug_grids[0]:
            bgl.glColor4f(*x_color, 1.0)
            for j in range(jgrid + 1):
                bgl.glVertex3f(bbox.x + xoffset, bbox.y + j * dxgrid, bbox.z)
                bgl.glVertex3f(bbox.x + xoffset, bbox.y + j * dxgrid, bbox.z + kgrid * dxgrid)
            for k in range(kgrid + 1):
                bgl.glVertex3f(bbox.x + xoffset, bbox.y, bbox.z + k * dxgrid)
                bgl.glVertex3f(bbox.x + xoffset, bbox.y + jgrid * dxgrid, bbox.z + k * dxgrid)

        bgl.glEnd()
        bgl.glLineWidth(1)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


    def modal(self, context, event):
        if not event.type == 'TIMER':
            return {'PASS_THROUGH'}
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None or not dprops.debug.display_simulation_grid:
            self.cancel(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}


    def invoke(self, context, event):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return
        args = (context,)
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_3d, args, 'WINDOW', 'POST_VIEW')
        self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        dprops.debug.is_draw_debug_grid_operator_running = True
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
        context.window_manager.event_timer_remove(self._timer)
        ui_utils.force_ui_redraw()
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            dprops.debug.is_draw_debug_grid_operator_running = False


class FlipFluidDrawGLParticles(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.draw_gl_particles"
    bl_label = "Draw GL Particles"
    bl_description = "Draw mesh cache particles"
    bl_options = {'REGISTER'}

    num_gradient_colors = IntProperty(default=128)

    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return True


    def get_color_ranges(self, pdata, num_colors):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        particles = pdata['particles']
        binspeeds = pdata['binspeeds']
        binstarts = pdata['binstarts']

        if dprops.debug.fluid_particle_gradient_mode == 'GRADIENT_NONE':
            min_speed = max_speed = dprops.debug.min_max_gradient_speed.value_max
        else:
            min_speed = dprops.debug.min_max_gradient_speed.value_min
            max_speed = dprops.debug.min_max_gradient_speed.value_max

        binidx = 0
        for i in range(len(binspeeds)):
            if binspeeds[i] > min_speed:
                binidx = max(i - 1, 0)
                break

        color_ranges = []
        for cidx in range(num_colors):
            if cidx == num_colors - 1:
                color_speed_limit = float('inf')
            else:
                speed_factor = (cidx + 1) / (num_colors - 1)
                color_speed_limit = min_speed + speed_factor * (max_speed - min_speed)

            for i in range(binidx, len(binspeeds)):
                if binspeeds[i] > color_speed_limit:
                    color_ranges.append(binstarts[i])
                    binidx = i
                    break
                if i == len(binspeeds) - 1:
                    color_ranges.append(len(particles))

        return color_ranges


    def lerp_rgb(self, minc, maxc, factor, mode='RGB'):
        if mode == 'RGB':
            r = minc[0] + factor * (maxc[0] - minc[0])
            g = minc[1] + factor * (maxc[1] - minc[1])
            b = minc[2] + factor * (maxc[2] - minc[2])
            return (r, g, b)
        elif mode == 'HSV':
            minhsv = colorsys.rgb_to_hsv(*minc)
            maxhsv = colorsys.rgb_to_hsv(*maxc)
            h = minhsv[0] + factor * (maxhsv[0] - minhsv[0])
            s = minhsv[1] + factor * (maxhsv[1] - minhsv[1])
            v = minhsv[2] + factor * (maxhsv[2] - minhsv[2])
            return colorsys.hsv_to_rgb(h, s, v)


    def draw_callback_3d(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return
        pdata = dprops.mesh_cache.gl_particles.get_point_cache_data()
        if pdata is None or len(pdata['particles']) == 0:
            return

        bbox_obj = bpy.data.objects.get(dprops.debug.particle_draw_aabb)
        bbox = None if bbox_obj is None else AABB.from_blender_object(bbox_obj)

        min_color = dprops.debug.low_speed_particle_color
        max_color = dprops.debug.high_speed_particle_color
        color_ranges = self.get_color_ranges(pdata, self.num_gradient_colors)

        bgl.glPointSize(dprops.debug.particle_size)
        bgl.glBegin(bgl.GL_POINTS)

        particles = pdata['particles']
        for cidx in range(len(color_ranges)):
            start_idx = 0 if cidx == 0 else color_ranges[cidx - 1]
            end_idx = color_ranges[cidx]
            if end_idx - start_idx == 0:
                continue

            color_factor = cidx / (len(color_ranges) - 1)
            gmode = 'HSV' if dprops.debug.fluid_particle_gradient_mode == 'GRADIENT_HSV' else 'RGB'
            color = self.lerp_rgb(min_color, max_color, color_factor, mode=gmode)
            bgl.glColor4f(color[0], color[1], color[2], 1.0)

            if bbox is None:
                for pidx in range(start_idx, end_idx):
                    bgl.glVertex3f(*(particles[pidx]))
            else:
                for pidx in range(start_idx, end_idx):
                    if bbox.contains_point(particles[pidx]):
                        bgl.glVertex3f(*(particles[pidx]))

        bgl.glEnd()
        bgl.glPointSize(1)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


    def modal(self, context, event):
        if not event.type == 'TIMER':
            return {'PASS_THROUGH'}
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None or not dprops.debug.export_fluid_particles:
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
        dprops.debug.is_draw_gl_particles_operator_running = True
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        context.window_manager.event_timer_remove(self._timer)
        ui_utils.force_ui_redraw()
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            dprops.debug.is_draw_gl_particles_operator_running = False


def register():
    bpy.utils.register_class(FlipFluidDrawDebugGrid)
    bpy.utils.register_class(FlipFluidDrawGLParticles)


def unregister():
    bpy.utils.unregister_class(FlipFluidDrawDebugGrid)
    bpy.utils.unregister_class(FlipFluidDrawGLParticles)
