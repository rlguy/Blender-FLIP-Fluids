# MIT License
# 
# Copyright (C) 2024 Ryan L. Guy
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

from abc import ABCMeta, abstractmethod
from ctypes import c_void_p, c_char_p, c_int, c_float, c_double, byref

from .pyfluid import pyfluid as lib
from . import pybindings as pb
from . import method_decorators as decorators
from .trianglemesh import TriangleMesh_t

class ForceField():
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def __init__():
        pass

    def __call__(self):
        return self._obj

    def update_mesh_static(self, mesh):
        mesh_struct = mesh.to_struct()
        libfunc = lib.ForceField_update_mesh_static
        args = [c_void_p, TriangleMesh_t, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        pb.execute_lib_func(libfunc, [self(), mesh_struct])

    def update_mesh_animated(self, mesh_previous, mesh_current, mesh_next):
        mesh_struct_previous = mesh_previous.to_struct()
        mesh_struct_current = mesh_current.to_struct()
        mesh_struct_next = mesh_next.to_struct()
        libfunc = lib.ForceField_update_mesh_animated
        args = [c_void_p, TriangleMesh_t, TriangleMesh_t, TriangleMesh_t, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        pb.execute_lib_func(libfunc, [self(), mesh_struct_previous, 
                                              mesh_struct_current, 
                                              mesh_struct_next])

    @property
    def enable(self):
        libfunc = lib.ForceField_is_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable.setter
    def enable(self, boolval):
        if boolval:
            libfunc = lib.ForceField_enable
        else:
            libfunc = lib.ForceField_disable
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def strength(self):
        libfunc = lib.ForceField_get_strength
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @strength.setter
    def strength(self, value):
        libfunc = lib.ForceField_set_strength
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def falloff_power(self):
        libfunc = lib.ForceField_get_falloff_power
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @falloff_power.setter
    def falloff_power(self, value):
        libfunc = lib.ForceField_set_falloff_power
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def max_force_limit_factor(self):
        libfunc = lib.ForceField_get_max_force_limit_factor
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @max_force_limit_factor.setter
    def max_force_limit_factor(self, value):
        libfunc = lib.ForceField_set_max_force_limit_factor
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def enable_min_distance(self):
        libfunc = lib.ForceField_is_min_distance_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_min_distance.setter
    def enable_min_distance(self, boolval):
        if boolval:
            libfunc = lib.ForceField_enable_min_distance
        else:
            libfunc = lib.ForceField_disable_min_distance
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def min_distance(self):
        libfunc = lib.ForceField_get_min_distance
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @min_distance.setter
    def min_distance(self, value):
        libfunc = lib.ForceField_set_min_distance
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def enable_max_distance(self):
        libfunc = lib.ForceField_is_max_distance_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_max_distance.setter
    def enable_max_distance(self, boolval):
        if boolval:
            libfunc = lib.ForceField_enable_max_distance
        else:
            libfunc = lib.ForceField_disable_max_distance
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def max_distance(self):
        libfunc = lib.ForceField_get_max_distance
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @max_distance.setter
    def max_distance(self, value):
        libfunc = lib.ForceField_set_max_distance
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def enable_frontfacing(self):
        libfunc = lib.ForceField_is_frontfacing_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_frontfacing.setter
    def enable_frontfacing(self, boolval):
        if boolval:
            libfunc = lib.ForceField_enable_frontfacing
        else:
            libfunc = lib.ForceField_disable_frontfacing
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_backfacing(self):
        libfunc = lib.ForceField_is_backfacing_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_backfacing.setter
    def enable_backfacing(self, boolval):
        if boolval:
            libfunc = lib.ForceField_enable_backfacing
        else:
            libfunc = lib.ForceField_disable_backfacing
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def enable_edgefacing(self):
        libfunc = lib.ForceField_is_edgefacing_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_edgefacing.setter
    def enable_edgefacing(self, boolval):
        if boolval:
            libfunc = lib.ForceField_enable_edgefacing
        else:
            libfunc = lib.ForceField_disable_edgefacing
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def gravity_scale(self):
        libfunc = lib.ForceField_get_gravity_scale
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @gravity_scale.setter
    def gravity_scale(self, value):
        libfunc = lib.ForceField_set_gravity_scale
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def gravity_scale_width(self):
        libfunc = lib.ForceField_get_gravity_scale
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @gravity_scale_width.setter
    def gravity_scale_width(self, value):
        libfunc = lib.ForceField_set_gravity_scale_width
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])