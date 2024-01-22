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
from . import pybindings as pb

DEVICE_STRING_LEN = 4096

class GPUDevice_t(ctypes.Structure):
    _fields_ = [("name", ctypes.c_char * DEVICE_STRING_LEN),
                ("description", ctypes.c_char * DEVICE_STRING_LEN),
                ("score", ctypes.c_float)]


def get_num_gpu_devices():
    libfunc = lib.OpenCLUtils_get_num_gpu_devices
    pb.init_lib_func(libfunc, [c_void_p], c_int)
    return pb.execute_lib_func(libfunc, [])

def find_gpu_devices():
    num_devices = get_num_gpu_devices()
    if num_devices == 0:
        return []

    device_structs = (GPUDevice_t * num_devices)()
    libfunc = lib.OpenCLUtils_get_gpu_devices
    pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
    pb.execute_lib_func(libfunc, [device_structs, num_devices])

    devices = []
    for d in device_structs:
        device_info = {"name": d.name.decode("utf-8"),
                       "description": d.description.decode("utf-8"),
                       "score": d.score}
        devices.append(device_info)

    return devices
