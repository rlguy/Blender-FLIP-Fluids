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

from .pyfluid import pyfluid as lib
from ctypes import c_char_p, c_int, byref

def check_success(success, errprefix):
    libfunc = lib.CBindings_get_error_message
    init_lib_func(libfunc, [], c_char_p)
    if not success:
        raise RuntimeError(errprefix + str(libfunc().decode("utf-8")))

def init_lib_func(libfunc, argtypes, restype):
    if libfunc.argtypes is None:
        libfunc.argtypes = argtypes
        libfunc.restype = restype

def execute_lib_func(libfunc, params):
    args = []
    for idx, arg in enumerate(params):
        try:
            cval = libfunc.argtypes[idx](arg)
        except:
            cval = arg
        args.append(cval)
    success = c_int();
    args.append(byref(success))

    result = None
    if libfunc.restype:
        funcresult = libfunc(*args)
        check_success(success, libfunc.__name__ + " - ")
        try:
            return libfunc.restype(funcresult).value
        except:
            return funcresult
    else:
        libfunc(*args)

    check_success(success, libfunc.__name__ + " - ")
    return result