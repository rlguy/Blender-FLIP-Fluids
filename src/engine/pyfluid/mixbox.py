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

import ctypes
from ctypes import c_void_p, c_char_p, c_char, c_int, c_uint, c_float, c_double, byref

from .pyfluid import pyfluid as lib
from .vector3 import Vector3, Vector3_t
from . import pybindings as pb


class MixboxLutData_t(ctypes.Structure):
    _fields_ = [("size", c_int),
                ("data", c_char_p)]


def initialize(lut_data, lut_data_size):
    c_lut_data = (c_char * len(lut_data)).from_buffer_copy(lut_data)

    mb_data = MixboxLutData_t()
    mb_data.size = lut_data_size
    mb_data.data = ctypes.cast(c_lut_data, c_char_p)

    libfunc = lib.Mixbox_initialize
    pb.init_lib_func(libfunc, [MixboxLutData_t, c_void_p], None)
    pb.execute_lib_func(libfunc, [mb_data])


def is_initialized():
    libfunc = lib.Mixbox_is_initialized
    pb.init_lib_func(libfunc, [c_void_p], c_int)
    return bool(pb.execute_lib_func(libfunc, []))


def lerp_srgb32f(r1, g1, b1, r2, g2, b2, t):
    libfunc = lib.Mixbox_lerp_srgb32f
    pb.init_lib_func(libfunc, [c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_void_p], Vector3_t)
    cvect = pb.execute_lib_func(libfunc, [r1, g1, b1, r2, g2, b2, t])
    return cvect.x, cvect.y, cvect.z
