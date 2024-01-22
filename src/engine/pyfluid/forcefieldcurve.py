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
from .forcefield import ForceField
from . import pybindings as pb
from . import method_decorators as decorators

class ForceFieldCurve(ForceField):
    
    def __init__(self):
        libfunc = lib.ForceFieldCurve_new
        args = [c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        self._obj = pb.execute_lib_func(libfunc, [])
        
    def __del__(self):
        try:
            libfunc = lib.ForceFieldCurve_destroy
            pb.init_lib_func(libfunc, [c_void_p], None)
            libfunc(self._obj)
        except:
            pass

    def __call__(self):
        return self._obj

    @property
    def flow_strength(self):
        libfunc = lib.ForceFieldCurve_get_flow_strength
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @flow_strength.setter
    def flow_strength(self, value):
        libfunc = lib.ForceFieldCurve_set_flow_strength
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def spin_strength(self):
        libfunc = lib.ForceFieldCurve_get_spin_strength
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @spin_strength.setter
    def spin_strength(self, value):
        libfunc = lib.ForceFieldCurve_set_spin_strength
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def enable_endcaps(self):
        libfunc = lib.ForceFieldCurve_is_endcaps_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_endcaps.setter
    def enable_endcaps(self, boolval):
        if boolval:
            libfunc = lib.ForceFieldCurve_enable_endcaps
        else:
            libfunc = lib.ForceFieldCurve_disable_endcaps
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])