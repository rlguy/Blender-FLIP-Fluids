# MIT License
# 
# Copyright (C) 2021 Ryan L. Guy
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

from ctypes import c_void_p, c_char_p, c_int, c_float, c_double, byref

from .pyfluid import pyfluid as lib
from . import pybindings as pb
from . import method_decorators as decorators
from .trianglemesh import TriangleMesh_t

class MeshFluidSource():
    
    def __init__(self, i, j, k, dx):
        libfunc = lib.MeshFluidSource_new
        args = [c_int, c_int, c_int, c_double, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        self._obj = pb.execute_lib_func(libfunc, [i, j, k, dx])

    def __del__(self):
        try:
            libfunc = lib.MeshFluidSource_destroy
            pb.init_lib_func(libfunc, [c_void_p], None)
            libfunc(self._obj)
        except:
            pass

    def __call__(self):
        return self._obj

    def update_mesh_static(self, mesh):
        mesh_struct = mesh.to_struct()
        libfunc = lib.MeshFluidSource_update_mesh_static
        args = [c_void_p, TriangleMesh_t, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        pb.execute_lib_func(libfunc, [self(), mesh_struct])

    def update_mesh_animated(self, mesh_previous, mesh_current, mesh_next):
        mesh_struct_previous = mesh_previous.to_struct()
        mesh_struct_current = mesh_current.to_struct()
        mesh_struct_next = mesh_next.to_struct()
        libfunc = lib.MeshFluidSource_update_mesh_animated
        args = [c_void_p, TriangleMesh_t, TriangleMesh_t, TriangleMesh_t, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        pb.execute_lib_func(libfunc, [self(), mesh_struct_previous, 
                                              mesh_struct_current, 
                                              mesh_struct_next])

    @property
    def enable(self):
        libfunc = lib.MeshFluidSource_is_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable.setter
    def enable(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable
        else:
            libfunc = lib.MeshFluidSource_disable
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def substep_emissions(self):
        libfunc = lib.MeshFluidSource_get_substep_emissions
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @substep_emissions.setter
    def substep_emissions(self, n):
        libfunc = lib.MeshFluidSource_set_substep_emissions
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    @property
    def inflow(self):
        libfunc = lib.MeshFluidSource_is_inflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @inflow.setter
    def inflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_set_inflow
        else:
            libfunc = lib.MeshFluidSource_set_outflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def outflow(self):
        libfunc = lib.MeshFluidSource_is_inflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @outflow.setter
    def outflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_set_outflow
        else:
            libfunc = lib.MeshFluidSource_set_inflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def fluid_outflow(self):
        libfunc = lib.MeshFluidSource_is_fluid_outflow_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @fluid_outflow.setter
    def fluid_outflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_fluid_outflow
        else:
            libfunc = lib.MeshFluidSource_disable_fluid_outflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def diffuse_outflow(self):
        libfunc = lib.MeshFluidSource_is_diffuse_outflow_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @diffuse_outflow.setter
    def diffuse_outflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_diffuse_outflow
        else:
            libfunc = lib.MeshFluidSource_disable_diffuse_outflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def get_velocity(self):
        libfunc = lib.MeshFluidSource_get_velocity
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], Vector3_t)
        cvect = pb.execute_lib_func(libfunc, [self()])
        return Vector3.from_struct(cvect)

    @decorators.xyz_or_vector
    def set_velocity(self, vx, vy, vz):
        libfunc = lib.MeshFluidSource_set_velocity
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], None
        )
        pb.execute_lib_func(libfunc, [self(), vx, vy, vz])

    @property
    def enable_append_object_velocity(self):
        libfunc = lib.MeshFluidSource_is_append_object_velocity_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_append_object_velocity.setter
    def enable_append_object_velocity(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_append_object_velocity
        else:
            libfunc = lib.MeshFluidSource_disable_append_object_velocity
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def object_velocity_influence(self):
        libfunc = lib.MeshFluidSource_get_object_velocity_influence
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @object_velocity_influence.setter
    def object_velocity_influence(self, value):
        libfunc = lib.MeshFluidSource_set_object_velocity_influence
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def enable_constrained_fluid_velocity(self):
        libfunc = lib.MeshFluidSource_is_constrained_fluid_velocity_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_constrained_fluid_velocity.setter
    def enable_constrained_fluid_velocity(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_constrained_fluid_velocity
        else:
            libfunc = lib.MeshFluidSource_disable_constrained_fluid_velocity
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def outflow_inverse(self):
        libfunc = lib.MeshFluidSource_is_outflow_inversed
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @outflow_inverse.setter
    def outflow_inverse(self, boolval):
        do_inverse = (boolval and not self.outflow_inverse) or (not boolval and self.outflow_inverse)
        if do_inverse:
            libfunc = lib.MeshFluidSource_outflow_inverse
            pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
            pb.execute_lib_func(libfunc, [self()])

    @property
    def source_id(self):
        libfunc = lib.MeshFluidSource_get_source_id
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @source_id.setter
    def source_id(self, n):
        libfunc = lib.MeshFluidSource_set_source_id
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), int(n)])

    def get_source_color(self):
        libfunc = lib.MeshFluidSource_get_source_color
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], Vector3_t)
        cvect = pb.execute_lib_func(libfunc, [self()])
        return Vector3.from_struct(cvect)

    @decorators.xyz_or_vector
    def set_source_color(self, r, g, b):
        libfunc = lib.MeshFluidSource_set_source_color
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], None
        )
        pb.execute_lib_func(libfunc, [self(), r, g, b])