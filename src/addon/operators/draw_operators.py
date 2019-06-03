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

import bpy, bgl, blf, math, colorsys
from bpy.props import (
        IntProperty
        )

from ..objects.flip_fluid_aabb import AABB
from ..utils import ui_utils
from ..utils import version_compatibility_utils as vcu

if vcu.is_blender_28():
    import gpu
    from gpu_extras.batch import batch_for_shader


x_coords = []
y_coords = []
z_coords = []
bounds_coords = []
def update_debug_grid_geometry(context):
    global x_coords
    global y_coords
    global z_coords
    global bounds_coords

    x_coords = []
    y_coords = []
    z_coords = []
    bounds_coords = []

    domain = context.scene.flip_fluid.get_domain_object()
    if domain is None:
        return
    dprops = context.scene.flip_fluid.get_domain_properties()

    if not dprops.debug.is_simulation_grid_debugging_enabled():
        return

    bbox = AABB.from_blender_object(domain)
    max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
    if dprops.debug.grid_display_mode == 'GRID_DISPLAY_PREVIEW':
        presolution = dprops.simulation.preview_resolution
        isize, jsize, ksize, dx = dprops.simulation.get_grid_dimensions(resolution=presolution)
    else:
        isize, jsize, ksize, dx = dprops.simulation.get_grid_dimensions()

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

    # Geometry Data
    z_coords = []
    for i in range(igrid + 1):
        z_coords.append((bbox.x + i * dxgrid, bbox.y, bbox.z + zoffset))
        z_coords.append((bbox.x + i * dxgrid, bbox.y + jgrid * dxgrid, bbox.z + zoffset))
    for j in range(jgrid + 1):
        z_coords.append((bbox.x, bbox.y + j * dxgrid, bbox.z + zoffset))
        z_coords.append((bbox.x + igrid * dxgrid, bbox.y + j * dxgrid, bbox.z + zoffset))

    y_coords = []
    for i in range(igrid + 1):
        y_coords.append((bbox.x + i * dxgrid, bbox.y + yoffset, bbox.z))
        y_coords.append((bbox.x + i * dxgrid, bbox.y + yoffset, bbox.z + kgrid * dxgrid))
    for k in range(kgrid + 1):
        y_coords.append((bbox.x, bbox.y + yoffset, bbox.z + k * dxgrid))
        y_coords.append((bbox.x + igrid * dxgrid, bbox.y + yoffset, bbox.z + k * dxgrid))

    x_coords = []
    for j in range(jgrid + 1):
        x_coords.append((bbox.x + xoffset, bbox.y + j * dxgrid, bbox.z))
        x_coords.append((bbox.x + xoffset, bbox.y + j * dxgrid, bbox.z + kgrid * dxgrid))
    for k in range(kgrid + 1):
        x_coords.append((bbox.x + xoffset, bbox.y, bbox.z + k * dxgrid))
        x_coords.append((bbox.x + xoffset, bbox.y + jgrid * dxgrid, bbox.z + k * dxgrid))

    native_dx = max_dim / dprops.simulation.resolution
    solid_width = 1.5 * native_dx
    width = math.ceil(bbox.xdim / native_dx) * native_dx
    height = math.ceil(bbox.ydim / native_dx) * native_dx
    depth = math.ceil(bbox.zdim / native_dx) * native_dx
    minx = bbox.x + solid_width
    miny = bbox.y + solid_width
    minz = bbox.z + solid_width
    maxx = bbox.x + isize * dx - solid_width
    maxy = bbox.y + jsize * dx - solid_width
    maxz = bbox.z + ksize * dx - solid_width

    bounds_coords = [
        (minx, miny, minz), (maxx, miny, minz), (minx, maxy, minz), (maxx, maxy, minz), 
        (minx, miny, maxz), (maxx, miny, maxz), (minx, maxy, maxz), (maxx, maxy, maxz),
        (minx, miny, minz), (minx, maxy, minz), (maxx, miny, minz), (maxx, maxy, minz),
        (minx, miny, maxz), (minx, maxy, maxz), (maxx, miny, maxz), (maxx, maxy, maxz),
        (minx, miny, minz), (minx, miny, maxz), (maxx, miny, minz), (maxx, miny, maxz),
        (minx, maxy, minz), (minx, maxy, maxz), (maxx, maxy, minz), (maxx, maxy, maxz)
        ]


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

        if vcu.get_object_hide_viewport(domain):
            return
        if not dprops.debug.display_simulation_grid:
            return

        if not vcu.is_blender_28():
            dlayers = [i for i,v in enumerate(domain.layers) if v]
            slayers = [i for i,v in enumerate(context.scene.layers) if v]
            if not (set(dlayers) & set(slayers)):
                return

        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_PREVIEW':
            presolution = dprops.simulation.preview_resolution
            isize, jsize, ksize, dx = dprops.simulation.get_grid_dimensions(resolution=presolution)
        else:
            isize, jsize, ksize, dx = dprops.simulation.get_grid_dimensions()

        world_scale = dprops.world.get_world_scale()
        world_dx = world_scale * dx

        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_MESH':
            isize *= (dprops.surface.subdivisions + 1)
            jsize *= (dprops.surface.subdivisions + 1)
            ksize *= (dprops.surface.subdivisions + 1)
            dx /= (dprops.surface.subdivisions + 1)

        width = context.region.width
        if vcu.is_blender_28():
            height = 200
            xstart = context.region.width - 400
        else:
            height = context.region.height
            xstart = 50

        font_id = 0
        if dprops.debug.grid_display_mode == 'GRID_DISPLAY_SIMULATION':
            blf.size(font_id, 20, 72)
            blf.position(font_id, xstart, height - 50, 0)
            blf.draw(font_id, "Simulation Grid")

            blf.size(font_id, 15, 72)
            blf.position(font_id, xstart + 10, height - 80, 0)
            blf.draw(font_id, "Grid Resolution: " + str(isize) + " x " + str(jsize) + " x " + str(ksize))

            dimx = round(world_dx * isize, 4)
            dimy = round(world_dx * jsize, 4)
            dimz = round(world_dx * ksize, 4)
            blf.position(font_id, xstart + 10, height - 105, 0)
            blf.draw(font_id, "Grid Dimensions: " + str(dimx) + "m x " + str(dimy) + "m x " + str(dimz) + "m")

            blf.position(font_id, xstart + 10, height - 130, 0)
            blf.draw(font_id, "Grid Cell Count: " + format(isize*jsize*ksize, ",").replace(",", " "))

            blf.position(font_id, xstart + 10, height - 155, 0)
            blf.draw(font_id, "Grid Cell Width: " + str(round(world_dx, 4)) + "m")
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


    def draw_callback_3d(self, context):
        global x_coords
        global y_coords
        global z_coords
        global bounds_coords

        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return
        dprops = context.scene.flip_fluid.get_domain_properties()

        if vcu.get_object_hide_viewport(domain):
            return

        if not vcu.is_blender_28():
            dlayers = [i for i,v in enumerate(domain.layers) if v]
            slayers = [i for i,v in enumerate(context.scene.layers) if v]
            if not (set(dlayers) & set(slayers)):
                return

        x_color = dprops.debug.x_grid_color
        y_color = dprops.debug.y_grid_color
        z_color = dprops.debug.z_grid_color
        bounds_color = dprops.debug.domain_bounds_color

        # Draw
        display_grid = dprops.debug.display_simulation_grid
        if vcu.is_blender_28():
            if display_grid and dprops.debug.enabled_debug_grids[2]:
                shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                batch = batch_for_shader(shader, 'LINES', {"pos": z_coords})
                shader.bind()
                shader.uniform_float("color", (z_color[0], z_color[1], z_color[2], 1.0))
                batch.draw(shader)
            if display_grid and dprops.debug.enabled_debug_grids[1]:
                shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                batch = batch_for_shader(shader, 'LINES', {"pos": y_coords})
                shader.bind()
                shader.uniform_float("color", (y_color[0], y_color[1], y_color[2], 1.0))
                batch.draw(shader)
            if display_grid and dprops.debug.enabled_debug_grids[0]:
                shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                batch = batch_for_shader(shader, 'LINES', {"pos": x_coords})
                shader.bind()
                shader.uniform_float("color", (x_color[0], x_color[1], x_color[2], 1.0))
                batch.draw(shader)
            if dprops.debug.display_domain_bounds:
                shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                batch = batch_for_shader(shader, 'LINES', {"pos": bounds_coords})
                shader.bind()
                shader.uniform_float("color", (bounds_color[0], bounds_color[1], bounds_color[2], 1.0))
                batch.draw(shader)
        else:
            bgl.glLineWidth(1)
            bgl.glBegin(bgl.GL_LINES)

            if display_grid and dprops.debug.enabled_debug_grids[2]:
                bgl.glColor4f(*z_color, 1.0)
                for c in z_coords:
                    bgl.glVertex3f(*c)
            if display_grid and dprops.debug.enabled_debug_grids[1]:
                bgl.glColor4f(*y_color, 1.0)
                for c in y_coords:
                    bgl.glVertex3f(*c)
            if display_grid and dprops.debug.enabled_debug_grids[0]:
                bgl.glColor4f(*x_color, 1.0)
                for c in x_coords:
                    bgl.glVertex3f(*c)
            if dprops.debug.display_domain_bounds:
                bgl.glColor4f(*(bounds_color), 1.0)
                for c in bounds_coords:
                    bgl.glVertex3f(*c)

            bgl.glEnd()
            bgl.glLineWidth(1)
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


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
        self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_3d, args, 'WINDOW', 'POST_VIEW')

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


particle_vertices = []
particle_vertex_colors = []
particle_shader = None
particle_batch_draw = None
def update_debug_particle_geometry(context):
    global particle_vertices
    global particle_vertex_colors

    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None or not dprops.debug.export_fluid_particles:
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
            uniform float pointsize;

            in vec3 pos;
            in vec4 color;

            out vec4 finalColor;

            void main()
            {
                gl_PointSize = pointsize;
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
        particle_shader.uniform_float('pointsize', dprops.debug.particle_size)
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
        global particle_vertices
        global particle_vertex_colors

        domain = context.scene.flip_fluid.get_domain_object()
        dprops = context.scene.flip_fluid.get_domain_properties()
        if domain is None or len(particle_vertices) == 0:
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
    bpy.utils.register_class(FlipFluidDrawDebugGrid)
    bpy.utils.register_class(FlipFluidDrawGLParticles)


def unregister():
    bpy.utils.unregister_class(FlipFluidDrawDebugGrid)
    bpy.utils.unregister_class(FlipFluidDrawGLParticles)
