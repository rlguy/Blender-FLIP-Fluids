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

import bpy, bgl, blf, math, colorsys
from bpy.props import (
        IntProperty
        )

from ..objects.flip_fluid_aabb import AABB
from ..utils import ui_utils
from ..utils import version_compatibility_utils as vcu
from .. import render

if vcu.is_blender_28():
    import gpu
    from gpu_extras.batch import batch_for_shader


particle_vertices = []
particle_vertex_colors = []
particle_shader = None
particle_batch_draw = None
def update_debug_particle_geometry(context):
    if render.is_rendering():
        # This method does not need to be run while rendering. Can cause
        # crashes on certain systems.
        return

    global particle_vertices
    global particle_vertex_colors

    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None or not dprops.debug.export_fluid_particles:
        return

    if not dprops.debug.fluid_particles_visibility:
        return

    particle_vertices = []
    particle_vertex_colors = []
    pdata = dprops.mesh_cache.gl_particles.get_point_cache_data()
    if pdata is None or len(pdata['particles']) == 0:
        return

    bbox_obj = dprops.debug.get_particle_draw_aabb_object()
    bbox = None if bbox_obj is None else AABB.from_blender_object(bbox_obj)

    min_color = dprops.debug.low_speed_particle_color
    max_color = dprops.debug.high_speed_particle_color
    num_gradient_colors = 128
    color_ranges = _get_color_ranges(pdata, num_gradient_colors)

    particles = pdata['particles']
    if bbox is None:
        particle_vertices = pdata['particles']

    for cidx in range(len(color_ranges)):
        start_idx = 0 if cidx == 0 else color_ranges[cidx - 1]
        end_idx = color_ranges[cidx]
        if end_idx - start_idx == 0:
            continue

        color_factor = cidx / (len(color_ranges) - 1)
        gmode = 'HSV' if dprops.debug.fluid_particle_gradient_mode == 'GRADIENT_HSV' else 'RGB'
        color = _lerp_rgb(min_color, max_color, color_factor, mode=gmode)
        color_tuple = (color[0], color[1], color[2], 1.0)

        if bbox is None:
            particle_vertex_colors += (end_idx - start_idx) * [color_tuple]
        else:
            for pidx in range(start_idx, end_idx):
                if bbox.contains_point(particles[pidx]):
                    particle_vertices.append(particles[pidx])
                    particle_vertex_colors.append(color_tuple)

    if vcu.is_blender_28():
        global particle_shader
        global particle_batch_draw

        vertex_shader = """
            uniform mat4 ModelViewProjectionMatrix;

            in vec3 pos;
            in vec4 color;

            out vec4 finalColor;

            void main()
            {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
                finalColor = color;
            }
        """

        fragment_shader = """
            in vec4 finalColor;
            out vec4 fragColor;

            void main()
            {
                fragColor = finalColor;
            }
        """

        particle_shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        particle_batch_draw = batch_for_shader(
            particle_shader, 'POINTS',
            {"pos": particle_vertices, "color": particle_vertex_colors},
        )


def _get_color_ranges(pdata, num_colors):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return

    particles = pdata['particles']
    binspeeds = pdata['binspeeds']
    binstarts = pdata['binstarts']

    if dprops.debug.fluid_particle_gradient_mode == 'GRADIENT_NONE':
        min_speed = max_speed = dprops.debug.max_gradient_speed
    else:
        min_speed = dprops.debug.min_gradient_speed
        max_speed = dprops.debug.max_gradient_speed

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


def _lerp_rgb(minc, maxc, factor, mode='RGB'):
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


class FlipFluidDrawGLParticles(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.draw_gl_particles"
    bl_label = "Draw GL Particles"
    bl_description = "Draw mesh cache particles"
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

        global particle_vertices
        global particle_vertex_colors

        domain = context.scene.flip_fluid.get_domain_object()
        dprops = context.scene.flip_fluid.get_domain_properties()
        if domain is None or len(particle_vertices) == 0:
            return

        if not dprops.debug.fluid_particles_visibility:
            return

        if vcu.get_object_hide_viewport(domain):
            return

        if not vcu.is_blender_28():
            dlayers = [i for i,v in enumerate(domain.layers) if v]
            slayers = [i for i,v in enumerate(context.scene.layers) if v]
            if not (set(dlayers) & set(slayers)):
                return

        if vcu.is_blender_28():
            global particle_shader
            global particle_batch_draw
            bgl.glPointSize(dprops.debug.particle_size)
            particle_batch_draw.draw(particle_shader)
        else:
            bgl.glPointSize(dprops.debug.particle_size)
            bgl.glBegin(bgl.GL_POINTS)

            current_color = None
            for i in range(len(particle_vertices)):
                if current_color != particle_vertex_colors[i]:
                    current_color = particle_vertex_colors[i]
                    bgl.glColor4f(current_color[0], current_color[1], current_color[2], 1.0)
                bgl.glVertex3f(*(particle_vertices[i]))

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
    bpy.utils.register_class(FlipFluidDrawGLParticles)


def unregister():
    bpy.utils.unregister_class(FlipFluidDrawGLParticles)
