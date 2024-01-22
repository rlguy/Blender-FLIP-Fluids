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

import numbers

from .vector3 import Vector3
from .gridindex import GridIndex

def ijk_or_gridindex(func):
    def ijk_or_gridindex_wrapper(self, *args):
        try:
            i, j, k = args
        except:
            i, j, k = args[0]
        return func(self, i, j, k)
    return ijk_or_gridindex_wrapper

def ijk_or_gridindex_and_value(func):
    def ijk_or_gridindex_and_value_wrapper(self, *args):
        try:
            return func(self, *args)
        except:
            i, j, k = args[0]
            return func(self, i, j, k, args[1])
    return ijk_or_gridindex_and_value_wrapper

def xyz_or_vector(func):
    def xyz_or_vector_wrapper(self, *args):
        try:
            return func(self, *args)
        except:
            return func(self, *args[0])
    return xyz_or_vector_wrapper

def xyz_or_vector_and_radius(func):
    def xyz_or_vector_wrapper(self, *args):
        try:
            return func(self, *args)
        except:
            x, y, z = args[0]
            return func(self, x, y, z, args[1])
    return xyz_or_vector_wrapper

def check_gt_zero(func):
    def check_values(self, *args):
        for arg in args:
            if isinstance(arg, numbers.Real) and arg <= 0:
                raise ValueError("Value must be greater than zero")
        return func(self, *args)
    return check_values

def check_ge_zero(func):
    def check_values(self, *args):
        for arg in args:
            if isinstance(arg, numbers.Real) and arg < 0:
                raise ValueError("Value must be greater than or equal to zero")
        return func(self, *args)
    return check_values

def check_gt(value):
    def check_gt_decorator(func):
        def check_gt_wrapper(self, *args):
            for arg in args:
                if isinstance(arg, numbers.Real) and arg <= value:
                    raise ValueError("Value must be greater than " + str(value))
            return func(self, *args)
        return check_gt_wrapper
    return check_gt_decorator

def check_ge(value):
    def check_ge_decorator(func):
        def check_ge_wrapper(self, *args):
            for arg in args:
                if isinstance(arg, numbers.Real) and arg < value:
                    raise ValueError("Value must be greater than or equal to " + str(value))
            return func(self, *args)
        return check_ge_wrapper
    return check_ge_decorator

def check_lt(value):
    def check_lt_decorator(func):
        def check_lt_wrapper(self, *args):
            for arg in args:
                if isinstance(arg, numbers.Real) and arg >= value:
                    raise ValueError("Value must be less than " + str(value))
            return func(self, *args)
        return check_lt_wrapper
    return check_lt_decorator

def check_le(value):
    def check_le_decorator(func):
        def check_le_wrapper(self, *args):
            for arg in args:
                if isinstance(arg, numbers.Real) and arg > value:
                    raise ValueError("Value must be less than or equal to " + str(value))
            return func(self, *args)
        return check_le_wrapper
    return check_le_decorator

def check_type(argtype):
    def check_type_decorator(func):
        def check_type_wrapper(self, *args):
            for arg in args:
                if not isinstance(arg, argtype):
                    raise TypeError("Argument must be of type " + str(argtype))
            return func(self, *args)
        return check_type_wrapper
    return check_type_decorator