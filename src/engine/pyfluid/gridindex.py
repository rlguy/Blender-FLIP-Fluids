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

import array
import ctypes

class GridIndex_t(ctypes.Structure):
    _fields_ = [("i", ctypes.c_int),
                ("j", ctypes.c_int),
                ("k", ctypes.c_int)]

class GridIndex(object):

    def __init__(self, i = 0, j = 0, k = 0):
        if isinstance(i, GridIndex):
            self._values = array.array('i', [i.i, i.j, i.k])
        else:
            self._values = array.array('i', [i, j, k])

    def __str__(self):
        return str(self.i) + " " + str(self.j) + " " + str(self.k)

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

    @property
    def i(self):
        return self._values[0]

    @property
    def j(self):
        return self._values[1]

    @property
    def k(self):
        return self._values[2]

    @i.setter
    def i(self, value):
        self._values[0] = value

    @j.setter
    def j(self, value):
        self._values[1] = value

    @k.setter
    def k(self, value):
        self._values[2] = value
