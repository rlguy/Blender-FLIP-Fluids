# MIT License
# 
# Copyright (c) 2018 Ryan L. Guy
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ctypes
from ctypes import c_void_p, c_char_p, c_char, c_int, c_uint, c_float, c_double, byref
import numbers

from .pyfluid import pyfluid as lib
from .vector3 import Vector3, Vector3_t
from .gridindex import GridIndex, GridIndex_t
from .aabb import AABB, AABB_t
from . import pybindings as pb
from . import method_decorators as decorators


def _check_simulation_initialized(func):
    def check_initialized_wrapper(self, *args):
        if isinstance(self, FluidSimulation) and not self.is_initialized():
            errmsg = "FluidSimulation must be initialized before calling this method"
            raise RuntimeError(errmsg)
        return func(self, *args)

    return check_initialized_wrapper

def _check_simulation_not_initialized(func):
    def check_not_initialized_wrapper(self, *args):
        if isinstance(self, FluidSimulation) and self.is_initialized():
            errmsg = "This method must be called before FluidSimulation is initialized"
            raise RuntimeError(errmsg)
        return func(self, *args)

    return check_not_initialized_wrapper

class FluidSimulation(object):

    def __init__(self, isize = None, jsize = None, ksize = None, dx = None):
        is_empty_constructor = all(x == None for x in (isize, jsize, ksize, dx))
        is_dimensions_constructor = (isinstance(isize, int) and
                                     isinstance(jsize, int) and
                                     isinstance(ksize, int) and
                                     isinstance(dx, numbers.Real))

        if is_empty_constructor:
            self._init_from_empty()
        elif is_dimensions_constructor:
            self._init_from_dimensions(isize, jsize, ksize, dx)
        else:
            errmsg = "FluidSimulation must be initialized with types:\n"
            errmsg += "isize:\t" + (str(int) + "\n" + 
                      "jsize:\t" + str(int) + "\n" + 
                      "ksize:\t" + str(int) + "\n" + 
                      "dx:\t" + str(float))
            raise TypeError(errmsg)

    def _init_from_empty(self):
        libfunc = lib.FluidSimulation_new_from_empty
        pb.init_lib_func(libfunc, [c_void_p], c_void_p)
        self._obj = pb.execute_lib_func(libfunc, [])

    @decorators.check_gt_zero
    def _init_from_dimensions(self, isize, jsize, ksize, dx):
        libfunc = lib.FluidSimulation_new_from_dimensions
        pb.init_lib_func(libfunc, 
                            [c_int, c_int, c_int, c_double, c_void_p], 
                            c_void_p)
        self._obj = pb.execute_lib_func(libfunc, [isize, jsize, ksize, dx])

    def __del__(self):
        libfunc = lib.FluidSimulation_destroy
        pb.init_lib_func(libfunc, [c_void_p], None)
        try:
            libfunc(self._obj)
        except:
            pass
        self._obj = None

    def __call__(self):
        return self._obj

    def get_version(self):
        libfunc = lib.FluidSimulation_get_version
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p], None)
        major = c_int()
        minor = c_int()
        revision = c_int()
        success = c_int()
        libfunc(self(), byref(major), byref(minor), byref(revision), byref(success))
        pb.check_success(success, libfunc.__name__ + " - ")
        return (major.value, minor.value, revision.value)

    def initialize(self):
        if self.is_initialized():
            return
        libfunc = lib.FluidSimulation_initialize
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def is_initialized(self):
        libfunc = lib.FluidSimulation_is_initialized
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @_check_simulation_initialized
    def update(self, dt):
        libfunc = lib.FluidSimulation_update
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), dt])

    def get_current_frame(self):
        libfunc = lib.FluidSimulation_get_current_frame
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    def set_current_frame(self, frameno):
        libfunc = lib.FluidSimulation_set_current_frame
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        return pb.execute_lib_func(libfunc, [self(), frameno])

    def is_current_frame_finished(self):
        libfunc = lib.FluidSimulation_is_current_frame_finished
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    def get_cell_size(self):
        libfunc = lib.FluidSimulation_get_cell_size
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    def get_grid_dimensions(self):
        libfunc = lib.FluidSimulation_get_grid_dimensions
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p], None)
        isize = c_int()
        jsize = c_int()
        ksize = c_int()
        success = c_int()
        libfunc(self(), byref(isize), byref(jsize), byref(ksize), byref(success))
        pb.check_success(success, libfunc.__name__ + " - ")

        return GridIndex(isize.value, jsize.value, ksize.value)

    def get_grid_width(self):
        libfunc = lib.FluidSimulation_get_grid_width
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    def get_grid_height(self):
        libfunc = lib.FluidSimulation_get_grid_height
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    def get_grid_depth(self):
        libfunc = lib.FluidSimulation_get_grid_depth
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    def get_simulation_dimensions(self):
        libfunc = lib.FluidSimulation_get_simulation_dimensions
        pb.init_lib_func(libfunc, 
                            [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p], 
                            None)
        width = c_double()
        height = c_double()
        depth = c_double()
        success = c_int()
        libfunc(self(), byref(width), byref(height), byref(depth), byref(success))
        pb.check_success(success, libfunc.__name__ + " - ")

        return Vector3(width.value, height.value, depth.value)

    def get_simulation_width(self):
        libfunc = lib.FluidSimulation_get_simulation_width
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    def get_simulation_height(self):
        libfunc = lib.FluidSimulation_get_simulation_height
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    def get_simulation_depth(self):
        libfunc = lib.FluidSimulation_get_simulation_depth
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @property
    def density(self):
        libfunc = lib.FluidSimulation_get_density
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @density.setter
    @decorators.check_gt_zero
    def density(self, value):
        libfunc = lib.FluidSimulation_set_density
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def marker_particle_scale(self):
        libfunc = lib.FluidSimulation_get_marker_particle_scale
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @marker_particle_scale.setter
    @decorators.check_ge_zero
    def marker_particle_scale(self, scale):
        libfunc = lib.FluidSimulation_set_marker_particle_scale
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), scale])

    @property
    def marker_particle_jitter_factor(self):
        libfunc = lib.FluidSimulation_get_marker_particle_jitter_factor
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @marker_particle_jitter_factor.setter
    @decorators.check_ge_zero
    def marker_particle_jitter_factor(self, jitter):
        libfunc = lib.FluidSimulation_set_marker_particle_jitter_factor
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), jitter])

    @property
    def surface_subdivision_level(self):
        libfunc = lib.FluidSimulation_get_surface_subdivision_level
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @surface_subdivision_level.setter
    @decorators.check_ge(1)
    def surface_subdivision_level(self, level):
        libfunc = lib.FluidSimulation_set_surface_subdivision_level
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(level)])

    @property
    def num_polygonizer_slices(self):
        libfunc = lib.FluidSimulation_get_num_polygonizer_slices
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @num_polygonizer_slices.setter
    @decorators.check_ge(1)
    def num_polygonizer_slices(self, slices):
        libfunc = lib.FluidSimulation_set_num_polygonizer_slices
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(slices)])

    @property
    def surface_smoothing_value(self):
        libfunc = lib.FluidSimulation_get_surface_smoothing_value
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @surface_smoothing_value.setter
    def surface_smoothing_value(self, s):
        libfunc = lib.FluidSimulation_set_surface_smoothing_value
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), s])

    @property
    def surface_smoothing_iterations(self):
        libfunc = lib.FluidSimulation_get_surface_smoothing_iterations
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @surface_smoothing_iterations.setter
    @decorators.check_ge(0)
    def surface_smoothing_iterations(self, n):
        libfunc = lib.FluidSimulation_set_surface_smoothing_iterations
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    @property
    def min_polyhedron_triangle_count(self):
        libfunc = lib.FluidSimulation_get_min_polyhedron_triangle_count
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @min_polyhedron_triangle_count.setter
    @decorators.check_ge_zero
    def min_polyhedron_triangle_count(self, count):
        libfunc = lib.FluidSimulation_set_min_polyhedron_triangle_count
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(count)])

    def get_domain_offset(self):
        libfunc = lib.FluidSimulation_get_domain_offset
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], Vector3_t)
        cvect = pb.execute_lib_func(libfunc, [self()])
        return Vector3.from_struct(cvect)

    @decorators.xyz_or_vector
    def set_domain_offset(self, x, y, z):
        libfunc = lib.FluidSimulation_set_domain_offset
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], None
        )
        pb.execute_lib_func(libfunc, [self(), x, y, z])

    def get_domain_scale(self):
        libfunc = lib.FluidSimulation_get_domain_scale
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    def set_domain_scale(self, scale):
        libfunc = lib.FluidSimulation_set_domain_scale
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), scale])

    def set_mesh_output_format_as_ply(self):
        libfunc = lib.FluidSimulation_set_mesh_output_format_as_ply
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def set_mesh_output_format_as_bobj(self):
        libfunc = lib.FluidSimulation_set_mesh_output_format_as_bobj
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_console_output(self):
        libfunc = lib.FluidSimulation_is_console_output_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_console_output.setter
    def enable_console_output(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_console_output
        else:
            libfunc = lib.FluidSimulation_disable_console_output
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_surface_reconstruction(self):
        libfunc = lib.FluidSimulation_is_surface_reconstruction_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_surface_reconstruction.setter
    def enable_surface_reconstruction(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_surface_reconstruction
        else:
            libfunc = lib.FluidSimulation_disable_surface_reconstruction
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_asynchronous_meshing(self):
        libfunc = lib.FluidSimulation_is_asynchronous_meshing_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_asynchronous_meshing.setter
    def enable_asynchronous_meshing(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_asynchronous_meshing
        else:
            libfunc = lib.FluidSimulation_disable_asynchronous_meshing
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_preview_mesh_output(self):
        libfunc = lib.FluidSimulation_is_preview_mesh_output_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_preview_mesh_output.setter
    @decorators.check_ge_zero
    def enable_preview_mesh_output(self, cellsize):
        if cellsize:
            libfunc = lib.FluidSimulation_enable_preview_mesh_output
            pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
            pb.execute_lib_func(libfunc, [self(), cellsize])
        else:
            libfunc = lib.FluidSimulation_disable_preview_mesh_output
            pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
            pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_smooth_interface_meshing(self):
        libfunc = lib.FluidSimulation_is_smooth_interface_meshing_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_smooth_interface_meshing.setter
    def enable_smooth_interface_meshing(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_smooth_interface_meshing
        else:
            libfunc = lib.FluidSimulation_disable_smooth_interface_meshing
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_inverted_contact_normals(self):
        libfunc = lib.FluidSimulation_is_inverted_contact_normals_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_inverted_contact_normals.setter
    def enable_inverted_contact_normals(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_inverted_contact_normals
        else:
            libfunc = lib.FluidSimulation_disable_inverted_contact_normals
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_fluid_particle_output(self):
        libfunc = lib.FluidSimulation_is_fluid_particle_output_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_fluid_particle_output.setter
    def enable_fluid_particle_output(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_fluid_particle_output
        else:
            libfunc = lib.FluidSimulation_disable_fluid_particle_output
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])


    @property
    def enable_internal_obstacle_mesh_output(self):
        libfunc = lib.FluidSimulation_is_internal_obstacle_mesh_output_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_internal_obstacle_mesh_output.setter
    def enable_internal_obstacle_mesh_output(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_internal_obstacle_mesh_output
        else:
            libfunc = lib.FluidSimulation_disable_internal_obstacle_mesh_output
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_diffuse_material_output(self):
        libfunc = lib.FluidSimulation_is_diffuse_material_output_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_diffuse_material_output.setter
    def enable_diffuse_material_output(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_diffuse_material_output
        else:
            libfunc = lib.FluidSimulation_disable_diffuse_material_output
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_diffuse_particle_emission(self):
        libfunc = lib.FluidSimulation_is_diffuse_particle_emission_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_diffuse_particle_emission.setter
    def enable_diffuse_particle_emission(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_diffuse_particle_emission
        else:
            libfunc = lib.FluidSimulation_disable_diffuse_particle_emission
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_diffuse_foam(self):
        libfunc = lib.FluidSimulation_is_diffuse_foam_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_diffuse_foam.setter
    def enable_diffuse_foam(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_diffuse_foam
        else:
            libfunc = lib.FluidSimulation_disable_diffuse_foam
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_diffuse_bubbles(self):
        libfunc = lib.FluidSimulation_is_diffuse_bubbles_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_diffuse_bubbles.setter
    def enable_diffuse_bubbles(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_diffuse_bubbles
        else:
            libfunc = lib.FluidSimulation_disable_diffuse_bubbles
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_diffuse_spray(self):
        libfunc = lib.FluidSimulation_is_diffuse_spray_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_diffuse_spray.setter
    def enable_diffuse_spray(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_diffuse_spray
        else:
            libfunc = lib.FluidSimulation_disable_diffuse_spray
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_bubble_diffuse_material(self):
        libfunc = lib.FluidSimulation_is_bubble_diffuse_material_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_bubble_diffuse_material.setter
    def enable_bubble_diffuse_material(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_bubble_diffuse_material
        else:
            libfunc = lib.FluidSimulation_disable_bubble_diffuse_material
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_spray_diffuse_material(self):
        libfunc = lib.FluidSimulation_is_spray_diffuse_material_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_spray_diffuse_material.setter
    def enable_spray_diffuse_material(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_spray_diffuse_material
        else:
            libfunc = lib.FluidSimulation_disable_spray_diffuse_material
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_foam_diffuse_material(self):
        libfunc = lib.FluidSimulation_is_foam_diffuse_material_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_foam_diffuse_material.setter
    def enable_foam_diffuse_material(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_foam_diffuse_particles
        else:
            libfunc = lib.FluidSimulation_disable_foam_diffuse_material
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def output_diffuse_material_as_separate_files(self):
        libfunc = lib.FluidSimulation_is_diffuse_material_output_as_separate_files
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @output_diffuse_material_as_separate_files.setter
    def output_diffuse_material_as_separate_files(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_output_diffuse_material_as_separate_files
        else:
            libfunc = lib.FluidSimulation_output_diffuse_material_as_single_file
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def diffuse_emitter_generation_rate(self):
        libfunc = lib.FluidSimulation_get_diffuse_emitter_generation_rate
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_emitter_generation_rate.setter
    @decorators.check_ge_zero
    @decorators.check_le(1.0)
    def diffuse_emitter_generation_rate(self, rate):
        libfunc = lib.FluidSimulation_set_diffuse_emitter_generation_rate
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), rate])

    @property
    def min_diffuse_emitter_energy(self):
        libfunc = lib.FluidSimulation_get_min_diffuse_emitter_energy
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @min_diffuse_emitter_energy.setter
    @decorators.check_ge_zero
    def min_diffuse_emitter_energy(self, e):
        libfunc = lib.FluidSimulation_set_min_diffuse_emitter_energy
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), e])

    @property
    def max_diffuse_emitter_energy(self):
        libfunc = lib.FluidSimulation_get_max_diffuse_emitter_energy
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @max_diffuse_emitter_energy.setter
    @decorators.check_ge_zero
    def max_diffuse_emitter_energy(self, e):
        libfunc = lib.FluidSimulation_set_max_diffuse_emitter_energy
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), e])

    @property
    def min_diffuse_wavecrest_curvature(self):
        libfunc = lib.FluidSimulation_get_min_diffuse_wavecrest_curvature
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @min_diffuse_wavecrest_curvature.setter
    def min_diffuse_wavecrest_curvature(self, k):
        libfunc = lib.FluidSimulation_set_min_diffuse_wavecrest_curvature
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), k])

    @property
    def max_diffuse_wavecrest_curvature(self):
        libfunc = lib.FluidSimulation_get_max_diffuse_wavecrest_curvature
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @max_diffuse_wavecrest_curvature.setter
    def max_diffuse_wavecrest_curvature(self, k):
        libfunc = lib.FluidSimulation_set_max_diffuse_wavecrest_curvature
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), k])

    @property
    def min_diffuse_turbulence(self):
        libfunc = lib.FluidSimulation_get_min_diffuse_turbulence
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @min_diffuse_turbulence.setter
    @decorators.check_ge_zero
    def min_diffuse_turbulence(self, t):
        libfunc = lib.FluidSimulation_set_min_diffuse_turbulence
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), t])

    @property
    def max_diffuse_turbulence(self):
        libfunc = lib.FluidSimulation_get_max_diffuse_turbulence
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @max_diffuse_turbulence.setter
    @decorators.check_ge_zero
    def max_diffuse_turbulence(self, t):
        libfunc = lib.FluidSimulation_set_max_diffuse_turbulence
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), t])

    @property
    def max_num_diffuse_particles(self):
        libfunc = lib.FluidSimulation_get_max_num_diffuse_particles
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @max_num_diffuse_particles.setter
    def max_num_diffuse_particles(self, num):
        libfunc = lib.FluidSimulation_set_max_num_diffuse_particles
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(num)])

    @property
    def diffuse_emitter_generation_bounds(self):
        libfunc = lib.FluidSimulation_get_diffuse_emitter_generation_bounds
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], AABB_t)
        return AABB.from_struct(pb.execute_lib_func(libfunc, [self()]))

    @diffuse_emitter_generation_bounds.setter
    def diffuse_emitter_generation_bounds(self, bounds):
        libfunc = lib.FluidSimulation_set_diffuse_emitter_generation_bounds
        pb.init_lib_func(libfunc, [c_void_p, AABB_t, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), bounds.to_struct()])

    @property
    def min_diffuse_particle_lifetime(self):
        libfunc = lib.FluidSimulation_get_min_diffuse_particle_lifetime
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @min_diffuse_particle_lifetime.setter
    @decorators.check_ge_zero
    def min_diffuse_particle_lifetime(self, lifetime):
        libfunc = lib.FluidSimulation_set_min_diffuse_particle_lifetime
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), lifetime])

    @property
    def max_diffuse_particle_lifetime(self):
        libfunc = lib.FluidSimulation_get_max_diffuse_particle_lifetime
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @max_diffuse_particle_lifetime.setter
    @decorators.check_ge_zero
    def max_diffuse_particle_lifetime(self, lifetime):
        libfunc = lib.FluidSimulation_set_max_diffuse_particle_lifetime
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), lifetime])

    @property
    def diffuse_particle_lifetime_variance(self):
        libfunc = lib.FluidSimulation_get_diffuse_particle_lifetime_variance
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_particle_lifetime_variance.setter
    @decorators.check_ge_zero
    def diffuse_particle_lifetime_variance(self, variance):
        libfunc = lib.FluidSimulation_set_diffuse_particle_lifetime_variance
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), variance])

    @property
    def foam_particle_lifetime_modifier(self):
        libfunc = lib.FluidSimulation_get_foam_particle_lifetime_modifier
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @foam_particle_lifetime_modifier.setter
    @decorators.check_ge_zero
    def foam_particle_lifetime_modifier(self, modifier):
        libfunc = lib.FluidSimulation_set_foam_particle_lifetime_modifier
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), modifier])

    @property
    def bubble_particle_lifetime_modifier(self):
        libfunc = lib.FluidSimulation_get_bubble_particle_lifetime_modifier
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @bubble_particle_lifetime_modifier.setter
    @decorators.check_ge_zero
    def bubble_particle_lifetime_modifier(self, modifier):
        libfunc = lib.FluidSimulation_set_bubble_particle_lifetime_modifier
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), modifier])

    @property
    def spray_particle_lifetime_modifier(self):
        libfunc = lib.FluidSimulation_get_spray_particle_lifetime_modifier
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @spray_particle_lifetime_modifier.setter
    @decorators.check_ge_zero
    def spray_particle_lifetime_modifier(self, modifier):
        libfunc = lib.FluidSimulation_set_spray_particle_lifetime_modifier
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), modifier])

    @property
    def diffuse_particle_wavecrest_emission_rate(self):
        libfunc = lib.FluidSimulation_get_diffuse_particle_wavecrest_emission_rate
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_particle_wavecrest_emission_rate.setter
    @decorators.check_ge_zero
    def diffuse_particle_wavecrest_emission_rate(self, rate):
        libfunc = lib.FluidSimulation_set_diffuse_particle_wavecrest_emission_rate
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), rate])

    @property
    def diffuse_particle_turbulence_emission_rate(self):
        libfunc = lib.FluidSimulation_get_diffuse_particle_turbulence_emission_rate
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_particle_turbulence_emission_rate.setter
    @decorators.check_ge_zero
    def diffuse_particle_turbulence_emission_rate(self, rate):
        libfunc = lib.FluidSimulation_set_diffuse_particle_turbulence_emission_rate
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), rate])

    @property
    def diffuse_foam_advection_strength(self):
        libfunc = lib.FluidSimulation_get_diffuse_foam_advection_strength
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_foam_advection_strength.setter
    @decorators.check_ge_zero
    @decorators.check_le(1.0)
    def diffuse_foam_advection_strength(self, s):
        libfunc = lib.FluidSimulation_set_diffuse_foam_advection_strength
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), s])

    @property
    def diffuse_foam_layer_depth(self):
        libfunc = lib.FluidSimulation_get_diffuse_foam_layer_depth
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_foam_layer_depth.setter
    @decorators.check_ge_zero
    @decorators.check_le(1.0)
    def diffuse_foam_layer_depth(self, depth):
        libfunc = lib.FluidSimulation_set_diffuse_foam_layer_depth
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), depth])

    @property
    def diffuse_foam_layer_offset(self):
        libfunc = lib.FluidSimulation_get_diffuse_foam_layer_offset
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_foam_layer_offset.setter
    @decorators.check_ge(-1.0)
    @decorators.check_le(1.0)
    def diffuse_foam_layer_offset(self, offset):
        libfunc = lib.FluidSimulation_set_diffuse_foam_layer_offset
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), offset])

    @property
    def enable_diffuse_preserve_foam(self):
        libfunc = lib.FluidSimulation_is_diffuse_preserve_foam_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_diffuse_preserve_foam.setter
    def enable_diffuse_preserve_foam(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_diffuse_preserve_foam
        else:
            libfunc = lib.FluidSimulation_disable_diffuse_preserve_foam
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def diffuse_foam_preservation_rate(self):
        libfunc = lib.FluidSimulation_get_diffuse_foam_preservation_rate
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_foam_preservation_rate.setter
    def diffuse_foam_preservation_rate(self, rate):
        libfunc = lib.FluidSimulation_set_diffuse_foam_preservation_rate
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), rate])

    @property
    def min_diffuse_foam_density(self):
        libfunc = lib.FluidSimulation_get_min_diffuse_foam_density
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @min_diffuse_foam_density.setter
    @decorators.check_ge_zero
    def min_diffuse_foam_density(self, t):
        libfunc = lib.FluidSimulation_set_min_diffuse_foam_density
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), t])

    @property
    def max_diffuse_foam_density(self):
        libfunc = lib.FluidSimulation_get_max_diffuse_foam_density
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @max_diffuse_foam_density.setter
    @decorators.check_ge_zero
    def max_diffuse_foam_density(self, t):
        libfunc = lib.FluidSimulation_set_max_diffuse_foam_density
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), t])

    @property
    def diffuse_bubble_drag_coefficient(self):
        libfunc = lib.FluidSimulation_get_diffuse_bubble_drag_coefficient
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_bubble_drag_coefficient.setter
    @decorators.check_ge_zero
    @decorators.check_le(1.0)
    def diffuse_bubble_drag_coefficient(self, d):
        libfunc = lib.FluidSimulation_set_diffuse_bubble_drag_coefficient
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), d])

    @property
    def diffuse_bubble_bouyancy_coefficient(self):
        libfunc = lib.FluidSimulation_get_diffuse_bubble_bouyancy_coefficient
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_bubble_bouyancy_coefficient.setter
    def diffuse_bubble_bouyancy_coefficient(self, b):
        libfunc = lib.FluidSimulation_set_diffuse_bubble_bouyancy_coefficient
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), b])

    @property
    def diffuse_spray_drag_coefficient(self):
        libfunc = lib.FluidSimulation_get_diffuse_spray_drag_coefficient
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_spray_drag_coefficient.setter
    def diffuse_spray_drag_coefficient(self, d):
        libfunc = lib.FluidSimulation_set_diffuse_spray_drag_coefficient
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), d])

    @property
    def diffuse_foam_limit_behaviour(self):
        libfunc = lib.FluidSimulation_get_diffuse_foam_limit_behaviour
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_foam_limit_behaviour.setter
    def diffuse_foam_limit_behaviour(self, behaviour):
        libfunc = lib.FluidSimulation_set_diffuse_foam_limit_behaviour
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(behaviour)])

    @property
    def diffuse_bubble_limit_behaviour(self):
        libfunc = lib.FluidSimulation_get_diffuse_bubble_limit_behaviour
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_bubble_limit_behaviour.setter
    def diffuse_bubble_limit_behaviour(self, behaviour):
        libfunc = lib.FluidSimulation_set_diffuse_bubble_limit_behaviour
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(behaviour)])

    @property
    def diffuse_spray_limit_behaviour(self):
        libfunc = lib.FluidSimulation_get_diffuse_spray_limit_behaviour
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @diffuse_spray_limit_behaviour.setter
    def diffuse_spray_limit_behaviour(self, behaviour):
        libfunc = lib.FluidSimulation_set_diffuse_spray_limit_behaviour
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(behaviour)])

    @property
    def diffuse_foam_active_boundary_sides(self):
        active = (c_int * 6)()
        libfunc = lib.FluidSimulation_get_diffuse_foam_active_boundary_sides
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], c_int)
        pb.execute_lib_func(libfunc, [self(), active])

        result = []
        for v in active:
            result.append(bool(v))

        return result

    @diffuse_foam_active_boundary_sides.setter
    def diffuse_foam_active_boundary_sides(self, active):
        c_active = (c_int * 6)()
        for i in range(6):
            c_active[i] = int(active[i])

        libfunc = lib.FluidSimulation_set_diffuse_foam_active_boundary_sides
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), c_active])

    @property
    def diffuse_bubble_active_boundary_sides(self):
        active = (c_int * 6)()
        libfunc = lib.FluidSimulation_get_diffuse_bubble_active_boundary_sides
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], c_int)
        pb.execute_lib_func(libfunc, [self(), active])

        result = []
        for v in active:
            result.append(bool(v))

        return result

    @diffuse_bubble_active_boundary_sides.setter
    def diffuse_bubble_active_boundary_sides(self, active):
        c_active = (c_int * 6)()
        for i in range(6):
            c_active[i] = int(active[i])

        libfunc = lib.FluidSimulation_set_diffuse_bubble_active_boundary_sides
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), c_active])

    @property
    def diffuse_spray_active_boundary_sides(self):
        active = (c_int * 6)()
        libfunc = lib.FluidSimulation_get_diffuse_spray_active_boundary_sides
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], c_int)
        pb.execute_lib_func(libfunc, [self(), active])

        result = []
        for v in active:
            result.append(bool(v))

        return result

    @diffuse_spray_active_boundary_sides.setter
    def diffuse_spray_active_boundary_sides(self, active):
        c_active = (c_int * 6)()
        for i in range(6):
            c_active[i] = int(active[i])

        libfunc = lib.FluidSimulation_set_diffuse_spray_active_boundary_sides
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), c_active])

    @property
    def enable_opencl_particle_advection(self):
        libfunc = lib.FluidSimulation_is_opencl_particle_advection_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_opencl_particle_advection.setter
    def enable_opencl_particle_advection(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_opencl_particle_advection
        else:
            libfunc = lib.FluidSimulation_disable_opencl_particle_advection
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_opencl_scalar_field(self):
        libfunc = lib.FluidSimulation_is_opencl_scalar_field_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_opencl_scalar_field.setter
    def enable_opencl_scalar_field(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_opencl_scalar_field
        else:
            libfunc = lib.FluidSimulation_disable_opencl_scalar_field
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def particle_advection_kernel_workload_size(self):
        libfunc = lib.FluidSimulation_get_particle_advection_kernel_workload_size
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @particle_advection_kernel_workload_size.setter
    @decorators.check_ge(1)
    def particle_advection_kernel_workload_size(self, size):
        libfunc = lib.FluidSimulation_set_particle_advection_kernel_workload_size
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(size)])

    @property
    def scalar_field_kernel_workload_size(self):
        libfunc = lib.FluidSimulation_get_scalar_field_kernel_workload_size
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @scalar_field_kernel_workload_size.setter
    @decorators.check_ge(1)
    def scalar_field_kernel_workload_size(self, size):
        libfunc = lib.FluidSimulation_set_scalar_field_kernel_workload_size
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(size)])

    @property
    def max_thread_count(self):
        libfunc = lib.FluidSimulation_get_max_thread_count
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @max_thread_count.setter
    @decorators.check_ge(1)
    def max_thread_count(self, n):
        libfunc = lib.FluidSimulation_set_max_thread_count
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    @decorators.xyz_or_vector
    def add_body_force(self, fx, fy, fz):
        libfunc = lib.FluidSimulation_add_body_force
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], None
        )
        pb.execute_lib_func(libfunc, [self(), fx, fy, fz])

    def get_constant_body_force(self):
        libfunc = lib.FluidSimulation_get_constant_body_force
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], Vector3_t)
        cvect = pb.execute_lib_func(libfunc, [self()])
        return Vector3.from_struct(cvect)

    @decorators.xyz_or_vector
    def get_variable_body_force(self, px, py, pz):
        libfunc = lib.FluidSimulation_get_variable_body_force
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], Vector3_t
        )
        cvect = pb.execute_lib_func(libfunc, [self(), px, py, pz])
        return Vector3.from_struct(cvect)

    @decorators.xyz_or_vector
    def get_total_body_force(self, px, py, pz):
        libfunc = lib.FluidSimulation_get_total_body_force
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], Vector3_t
        )
        cvect = pb.execute_lib_func(libfunc, [self(), px, py, pz])
        return Vector3.from_struct(cvect)

    def reset_body_force(self):
        libfunc = lib.FluidSimulation_reset_body_force
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def viscosity(self):
        libfunc = lib.FluidSimulation_get_viscosity
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @viscosity.setter
    @decorators.check_ge_zero
    def viscosity(self, value):
        libfunc = lib.FluidSimulation_set_viscosity
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def boundary_friction(self):
        libfunc = lib.FluidSimulation_get_boundary_friction
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @boundary_friction.setter
    @decorators.check_ge_zero
    @decorators.check_le(1.0)
    def boundary_friction(self, s):
        libfunc = lib.FluidSimulation_set_boundary_friction
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), s])

    @property
    def CFL_condition_number(self):
        libfunc = lib.FluidSimulation_get_CFL_condition_number
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @CFL_condition_number.setter
    @decorators.check_ge(1)
    def CFL_condition_number(self, n):
        libfunc = lib.FluidSimulation_set_CFL_condition_number
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    @property
    def min_time_steps_per_frame(self):
        libfunc = lib.FluidSimulation_get_min_time_steps_per_frame
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @min_time_steps_per_frame.setter
    @decorators.check_ge(1)
    def min_time_steps_per_frame(self, n):
        libfunc = lib.FluidSimulation_set_min_time_steps_per_frame
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    @property
    def max_time_steps_per_frame(self):
        libfunc = lib.FluidSimulation_get_max_time_steps_per_frame
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_adaptive_obstacle_time_stepping(self):
        libfunc = lib.FluidSimulation_is_adaptive_obstacle_time_stepping_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_adaptive_obstacle_time_stepping.setter
    def enable_adaptive_obstacle_time_stepping(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_adaptive_obstacle_time_stepping
        else:
            libfunc = lib.FluidSimulation_disable_adaptive_obstacle_time_stepping
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @max_time_steps_per_frame.setter
    @decorators.check_ge(1)
    def max_time_steps_per_frame(self, n):
        libfunc = lib.FluidSimulation_set_max_time_steps_per_frame
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    @property
    def enable_extreme_velocity_removal(self):
        libfunc = lib.FluidSimulation_is_extreme_velocity_removal_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_extreme_velocity_removal.setter
    def enable_extreme_velocity_removal(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_extreme_velocity_removal
        else:
            libfunc = lib.FluidSimulation_disable_extreme_velocity_removal
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def PICFLIP_ratio(self):
        libfunc = lib.FluidSimulation_get_PICFLIP_ratio
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_double)
        return pb.execute_lib_func(libfunc, [self()])

    @PICFLIP_ratio.setter
    @decorators.check_ge_zero
    @decorators.check_le(1.0)
    def PICFLIP_ratio(self, ratio):
        libfunc = lib.FluidSimulation_set_PICFLIP_ratio
        pb.init_lib_func(libfunc, [c_void_p, c_double, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), ratio])

    @property
    def preferred_gpu_device(self):
        c_str = ctypes.create_string_buffer(4096)
        libfunc = lib.FluidSimulation_get_preferred_gpu_device
        pb.init_lib_func(libfunc, [c_void_p, c_char_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), c_str])
        return c_str.value.decode("utf-8")

    @preferred_gpu_device.setter
    def preferred_gpu_device(self, device_name):
        c_device_name = ctypes.create_string_buffer(bytes(device_name, 'utf-8'), 4096)
        libfunc = lib.FluidSimulation_set_preferred_gpu_device
        pb.init_lib_func(libfunc, [c_void_p, c_char_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), c_device_name])

    @property
    def enable_experimental_optimization_features(self):
        libfunc = lib.FluidSimulation_is_experimental_optimization_features_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_experimental_optimization_features.setter
    def enable_experimental_optimization_features(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_experimental_optimization_features
        else:
            libfunc = lib.FluidSimulation_disable_experimental_optimization_features
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_static_solid_levelset_precomputation(self):
        libfunc = lib.FluidSimulation_is_static_solid_levelset_precomputation_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_static_solid_levelset_precomputation.setter
    def enable_static_solid_levelset_precomputation(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_static_solid_levelset_precomputation
        else:
            libfunc = lib.FluidSimulation_disable_static_solid_levelset_precomputation
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_temporary_mesh_levelset(self):
        libfunc = lib.FluidSimulation_is_temporary_mesh_levelset_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_temporary_mesh_levelset.setter
    def enable_temporary_mesh_levelset(self, boolval):
        if boolval:
            libfunc = lib.FluidSimulation_enable_temporary_mesh_levelset
        else:
            libfunc = lib.FluidSimulation_disable_temporary_mesh_levelset
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def add_mesh_fluid_source(self, mesh_fluid_source):
        libfunc = lib.FluidSimulation_add_mesh_fluid_source
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), mesh_fluid_source()])

    def remove_mesh_fluid_source(self, mesh_fluid_source):
        libfunc = lib.FluidSimulation_remove_mesh_fluid_source
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), mesh_fluid_source()])

    def remove_mesh_fluid_sources(self):
        libfunc = lib.FluidSimulation_remove_mesh_fluid_sources
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def add_mesh_obstacle(self, mesh_object):
        libfunc = lib.FluidSimulation_add_mesh_obstacle
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), mesh_object()])

    def remove_mesh_obstacle(self, mesh_object):
        libfunc = lib.FluidSimulation_remove_mesh_obstacle
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), mesh_object()])

    def remove_mesh_obstacles(self):
        libfunc = lib.FluidSimulation_remove_mesh_obstacles
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def add_mesh_fluid(self, mesh_object, vx = 0.0, vy = 0.0, vz = 0.0):
        velocity = Vector3_t(vx, vy, vz)
        libfunc = lib.FluidSimulation_add_mesh_fluid
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, Vector3_t, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), mesh_object(), velocity])

    def get_num_marker_particles(self):
        libfunc = lib.FluidSimulation_get_num_marker_particles
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    def get_marker_particles(self, startidx = None, endidx = None):
        nparticles = self.get_num_marker_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (MarkerParticle_t * n)()

        libfunc = lib.FluidSimulation_get_marker_particles
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        return out

    def get_marker_particle_positions(self, startidx = None, endidx = None):
        nparticles = self.get_num_marker_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (Vector3_t * n)()

        libfunc = lib.FluidSimulation_get_marker_particle_positions
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        return out

    def get_marker_particle_velocities(self, startidx = None, endidx = None):
        nparticles = self.get_num_marker_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (Vector3_t * n)()

        libfunc = lib.FluidSimulation_get_marker_particle_velocities
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        return out

    def get_num_diffuse_particles(self):
        libfunc = lib.FluidSimulation_get_num_diffuse_particles
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    def get_diffuse_particles(self, startidx = None, endidx = None):
        nparticles = self.get_num_diffuse_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (DiffuseParticle_t * n)()

        libfunc = lib.FluidSimulation_get_diffuse_particles
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        return out

    def get_diffuse_particle_positions(self, startidx = None, endidx = None):
        nparticles = self.get_num_diffuse_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (Vector3_t * n)()

        libfunc = lib.FluidSimulation_get_diffuse_particle_positions
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        return out

    def get_diffuse_particle_velocities(self, startidx = None, endidx = None):
        nparticles = self.get_num_diffuse_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (Vector3_t * n)()

        libfunc = lib.FluidSimulation_get_diffuse_particle_velocities
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        return out

    def get_diffuse_particle_lifetimes(self, startidx = None, endidx = None):
        nparticles = self.get_num_diffuse_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (c_float * n)()

        libfunc = lib.FluidSimulation_get_diffuse_particle_lifetimes
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        floats = []
        for f in out:
            floats.append(float(f))

        return floats

    def get_diffuse_particle_types(self, startidx = None, endidx = None):
        nparticles = self.get_num_diffuse_particles()
        startidx, endidx = self._check_range(startidx, endidx, 0, nparticles)
        n = endidx - startidx
        out = (c_char * n)()

        libfunc = lib.FluidSimulation_get_diffuse_particle_types
        pb.init_lib_func(libfunc, 
                         [c_void_p, c_int, c_int, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), startidx, endidx, out])

        types = []
        for t in out:
            types.append(ord(t))

        return types

    def get_surface_data(self):
        return self._get_output_data(lib.FluidSimulation_get_surface_data_size,
                                     lib.FluidSimulation_get_surface_data)

    def get_surface_preview_data(self):
        return self._get_output_data(lib.FluidSimulation_get_surface_preview_data_size,
                                     lib.FluidSimulation_get_surface_preview_data)

    def get_diffuse_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_data_size,
                                     lib.FluidSimulation_get_diffuse_data)

    def get_diffuse_foam_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_foam_data_size,
                                     lib.FluidSimulation_get_diffuse_foam_data)

    def get_diffuse_bubble_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_bubble_data_size,
                                     lib.FluidSimulation_get_diffuse_bubble_data)

    def get_diffuse_spray_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_spray_data_size,
                                     lib.FluidSimulation_get_diffuse_spray_data)

    def get_fluid_particle_data(self):
        return self._get_output_data(lib.FluidSimulation_get_fluid_particle_data_size,
                                     lib.FluidSimulation_get_fluid_particle_data)

    def get_internal_obstacle_mesh_data(self):
        return self._get_output_data(lib.FluidSimulation_get_internal_obstacle_mesh_data_size,
                                     lib.FluidSimulation_get_internal_obstacle_mesh_data)

    def get_logfile_data(self):
        byte_str = self._get_output_data(lib.FluidSimulation_get_logfile_data_size,
                                         lib.FluidSimulation_get_logfile_data)
        return byte_str.decode("utf-8")

    def get_frame_stats_data(self):
        libfunc = lib.FluidSimulation_get_frame_stats_data
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], FluidSimulationFrameStats_t)
        stats = pb.execute_lib_func(libfunc, [self()])
        return stats

    def get_marker_particle_position_data(self):
        return self._get_output_data(lib.FluidSimulation_get_marker_particle_position_data_size,
                                     lib.FluidSimulation_get_marker_particle_position_data)

    def get_marker_particle_velocity_data(self):
        return self._get_output_data(lib.FluidSimulation_get_marker_particle_velocity_data_size,
                                     lib.FluidSimulation_get_marker_particle_velocity_data)

    def get_diffuse_particle_position_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_particle_position_data_size,
                                     lib.FluidSimulation_get_diffuse_particle_position_data)

    def get_diffuse_particle_velocity_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_particle_velocity_data_size,
                                     lib.FluidSimulation_get_diffuse_particle_velocity_data)

    def get_diffuse_particle_lifetime_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_particle_lifetime_data_size,
                                     lib.FluidSimulation_get_diffuse_particle_lifetime_data)

    def get_diffuse_particle_type_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_particle_type_data_size,
                                     lib.FluidSimulation_get_diffuse_particle_type_data)

    def get_diffuse_particle_id_data(self):
        return self._get_output_data(lib.FluidSimulation_get_diffuse_particle_id_data_size,
                                     lib.FluidSimulation_get_diffuse_particle_id_data)

    def _get_output_data(self, size_libfunc, data_libfunc):
        libfunc = size_libfunc
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_uint)
        data_size = pb.execute_lib_func(libfunc, [self()])

        c_data = (c_char * data_size)()

        libfunc = data_libfunc
        pb.init_lib_func(libfunc, [c_void_p, c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), c_data])

        return bytes(c_data)

    def _check_range(self, startidx, endidx, minidx, maxidx):
        if startidx is None:
            startidx = minidx
        if endidx is None:
            endidx = maxidx

        if not isinstance(startidx, int) or not isinstance(endidx, int):
            raise TypeError("Index range must be integers")
        if startidx < minidx:
            raise IndexError("startidx out of range: " + str(startidx))
        if endidx > maxidx:
            raise IndexError("endidx out of range: " + str(endidx))
        if endidx < startidx:
            endidx = startidx

        return startidx, endidx

    def load_marker_particle_data(self, num_particles, position_data, velocity_data):
        c_position_data = (c_char * len(position_data)).from_buffer_copy(position_data)
        c_velocity_data = (c_char * len(velocity_data)).from_buffer_copy(velocity_data)

        pdata = FluidSimulationMarkerParticleData_t()
        pdata.size = c_int(num_particles)
        pdata.positions = ctypes.cast(c_position_data, c_char_p)
        pdata.velocities = ctypes.cast(c_velocity_data, c_char_p)

        libfunc = lib.FluidSimulation_load_marker_particle_data
        pb.init_lib_func(libfunc, [c_void_p, FluidSimulationMarkerParticleData_t, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), pdata])

    def load_diffuse_particle_data(self, num_particles, position_data, velocity_data,
                                         lifetime_data, type_data, id_data):
        c_position_data = (c_char * len(position_data)).from_buffer_copy(position_data)
        c_velocity_data = (c_char * len(velocity_data)).from_buffer_copy(velocity_data)
        c_lifetime_data = (c_char * len(lifetime_data)).from_buffer_copy(lifetime_data)
        c_type_data = (c_char * len(type_data)).from_buffer_copy(type_data)
        c_id_data = (c_char * len(id_data)).from_buffer_copy(id_data)

        pdata = FluidSimulationDiffuseParticleData_t()
        pdata.size = c_int(num_particles)
        pdata.positions = ctypes.cast(c_position_data, c_char_p)
        pdata.velocities = ctypes.cast(c_velocity_data, c_char_p)
        pdata.lifetimes = ctypes.cast(c_lifetime_data, c_char_p)
        pdata.types = ctypes.cast(c_type_data, c_char_p)
        pdata.ids = ctypes.cast(c_id_data, c_char_p)

        libfunc = lib.FluidSimulation_load_diffuse_particle_data
        pb.init_lib_func(libfunc, [c_void_p, FluidSimulationDiffuseParticleData_t, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), pdata])



class MarkerParticle_t(ctypes.Structure):
    _fields_ = [("position", Vector3_t),
                ("velocity", Vector3_t)]

class DiffuseParticle_t(ctypes.Structure):
    _fields_ = [("position", Vector3_t),
                ("velocity", Vector3_t),
                ("lifetime", c_float),
                ("type", c_char)]

class FluidSimulationMeshStats_t(ctypes.Structure):
    _fields_ = [("enabled", c_int),
                ("vertices", c_int),
                ("triangles", c_int),
                ("bytes", c_uint)]

class FluidSimulationTimingStats_t(ctypes.Structure):
    _fields_ = [("total", c_double),
                ("mesh", c_double),
                ("advection", c_double),
                ("particles", c_double),
                ("pressure", c_double),
                ("diffuse", c_double),
                ("viscosity", c_double),
                ("objects", c_double)]

class FluidSimulationFrameStats_t(ctypes.Structure):
    _fields_ = [("frame", c_int),
                ("substeps", c_int),
                ("delta_time", c_double),
                ("fluid_particles", c_int),
                ("diffuse_particles", c_int),
                ("surface", FluidSimulationMeshStats_t),
                ("preview", FluidSimulationMeshStats_t),
                ("foam", FluidSimulationMeshStats_t),
                ("bubble", FluidSimulationMeshStats_t),
                ("spray", FluidSimulationMeshStats_t),
                ("particles", FluidSimulationMeshStats_t),
                ("obstacle", FluidSimulationMeshStats_t),
                ("timing", FluidSimulationTimingStats_t)]

class FluidSimulationMarkerParticleData_t(ctypes.Structure):
    _fields_ = [("size", c_int),
                ("positions", c_char_p),
                ("velocities", c_char_p)]

class FluidSimulationDiffuseParticleData_t(ctypes.Structure):
    _fields_ = [("size", c_int),
                ("positions", c_char_p),
                ("velocities", c_char_p),
                ("lifetimes", c_char_p),
                ("types", c_char_p),
                ("ids", c_char_p)]