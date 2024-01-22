# MIT License
# 
# Copyright (C) 2024 Ryan L. Guy, http://rlguy.com
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

import array
import ctypes
import math

class Vector3_t(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float),
                ("y", ctypes.c_float),
                ("z", ctypes.c_float)]

class Vector3(object):

    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        if isinstance(x, Vector3):
            self._values = array.array('f', [x.x, x.y, x.z])
        else:
            self._values = array.array('f', [x, y, z])

    @classmethod
    def from_struct(cls, cstruct):
        return cls(cstruct.x, cstruct.y, cstruct.z)

    def to_struct(self):
        return Vector3_t(self.x, self.y, self.z)

    def __str__(self):
        return str(self.x) + " " + str(self.y) + " " + str(self.z)

    def __getitem__(self, key):
        if key < 0 or key > 2:
            raise IndexError("Index must be in range [0, 2]")
        if not isinstance(key, int):
            raise TypeError("Index must be an integer")

        return self._values[key]

    def __setitem__(self, key, value):
        if key < 0 or key > 2:
            raise IndexError("Index must be in range [0, 2]")
        if not isinstance(key, int):
            raise TypeError("Index must be an integer")

        self._values[key] = value

    def __iter__(self):
        yield self._values[0]
        yield self._values[1]
        yield self._values[2]

    def __add__(self, other):
        return Vector3(self.x + other.x,
                       self.y + other.y,
                       self.z + other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        return Vector3(self.x - other.x,
                       self.y - other.y,
                       self.z - other.z)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, scale):
        return Vector3(scale * self.x, 
                       scale * self.y, 
                       scale * self.z)

    def __imul__(self, scale):
        self.x *= scale
        self.y *= scale
        self.z *= scale
        return self

    def __rmul__(self, scale):
        return Vector3(scale * self.x, 
                       scale * self.y, 
                       scale * self.z)

    def __div__(self, denominator):
        if denominator == 0.0:
            raise ZeroDivisionError

        inv = 1.0 / denominator

        return Vector3(self.x * inv,
                       self.y * inv,
                       self.z * inv)

    def __idiv__(self, denominator):
        if denominator == 0.0:
            raise ZeroDivisionError

        inv = 1.0 / denominator

        self.x *= inv
        self.y *= inv
        self.z *= inv
        return self

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __pos__(self):
        return Vector3(self)

    def __abs__(self):
        return Vector3(abs(self.x), abs(self.y), abs(self.z))

    def __invert__(self):
        return Vector3(1.0 / self.x, 
                       1.0 / self.y, 
                       1.0 / self.z)

    @property
    def x(self):
        return self._values[0]

    @property
    def y(self):
        return self._values[1]

    @property
    def z(self):
        return self._values[2]

    @x.setter
    def x(self, value):
        self._values[0] = value

    @y.setter
    def y(self, value):
        self._values[1] = value

    @z.setter
    def z(self, value):
        self._values[2] = value

    def add(self, vector):
        self += vector
        return self

    def sub(self, vector):
        self -= vector
        return self

    def mult(self, scale):
        self *= scale
        return self

    def div(self, denominator):
        self /= denominator
        return self

    def neg(self):
        self.x = -self.x
        self.y = -self.y
        self.z = -self.z
        return self

    def invert(self):
        self.x = 1.0 / self.x
        self.y = 1.0 / self.y
        self.z = 1.0 / self.z
        return self

    def dot(vector):
        return self.x*vector.x + self.y*vector.y + self.z*vector.z

    def cross(vector):
        return Vector3(self.y*vector.z - self.z*vector.y,
                       self.z*vector.x - self.x*vector.z,
                       self.x*vector.y - self.y*vector.x)

    def lengthsq(self):
        return self.x*self.x + self.y*self.y + self.z*self.z

    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)

    def normalize(self):
        length = self.length()
        if length == 0.0:
            raise ZeroDivisionError

        inv = 1.0 / length
        self *= inv
        return self
