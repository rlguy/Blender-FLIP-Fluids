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
import array
from gridindex import GridIndex
import method_decorators as decorators

class Array3d:
    __metaclass__ = ABCMeta

    def __init__(self, isize, jsize, ksize):
        self.width, self.height, self.depth = isize, jsize, ksize
        self._num_elements = isize*jsize*ksize

    @abstractmethod
    def _init_grid(self, data):
        pass

    def fill(self, value):
        for i in range(self._num_elements):
            self._grid[i] = value

    @decorators.ijk_or_gridindex
    def __call__(self, i, j, k):
        if not self._is_index_in_range(i, j, k) and self._out_of_range_value != None:
            return self._out_of_range_value
        return self._grid[self._get_flat_index(i, j, k)]

    def __iter__(self):
        i = j = k = 0
        for v in self._grid:
            yield i, j, k, v
            i += 1
            if i >= self.width: 
                i = 0
                j += 1
                if j >= self.height:
                    j = 0
                    k += 1

    @decorators.ijk_or_gridindex
    def get(self, i, j, k):
        return self(i, j, k)

    @decorators.ijk_or_gridindex_and_value
    def set(self, i, j, k, value):
        self._grid[self._get_flat_index(i, j, k)] = value

    @decorators.ijk_or_gridindex_and_value
    def add(self, i, j, k, value):
        self._grid[self._get_flat_index(i, j, k)] += value

    def get_num_elements(self):
        return self._num_elements

    def set_out_of_range_value(self, value = None):
        self._out_of_range_value = value

    def get_out_of_range_value(self):
        return self._out_of_range_value

    def _is_index_in_range(self, i, j, k):
        return (i >= 0 and j >= 0 and k >= 0 and 
                i < self.width and j < self.height and k < self.depth)

    def _get_flat_index(self, i, j, k):
        return i + self.width*(j + self.height*k)
        

class Array3di(Array3d):
    def __init__(self, isize, jsize, ksize, default_value = int()):
        Array3d.__init__(self, isize, jsize, ksize)
        self._init_grid(default_value)

    def _init_grid(self, default_value):
        self._grid = array.array('i', [default_value]*self.get_num_elements())

class Array3df(Array3d):
    def __init__(self, isize, jsize, ksize, default_value = float()):
        Array3d.__init__(self, isize, jsize, ksize)
        self._init_grid(default_value)

    def _init_grid(self, default_value):
        self._grid = array.array('f', [default_value]*self.get_num_elements())

class Array3dd(Array3d):
    def __init__(self, isize, jsize, ksize, default_value = float()):
        Array3d.__init__(self, isize, jsize, ksize)
        self._init_grid(default_value)

    def _init_grid(self, default_value):
        self._grid = array.array('d', [default_value]*self.get_num_elements())