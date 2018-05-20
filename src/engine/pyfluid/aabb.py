# MIT License
# 
# Copyright (c) 2018 Ryan L. Guy
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

from .vector3 import Vector3, Vector3_t
from .gridindex import GridIndex
from . import method_decorators as decorators
import ctypes

class AABB_t(ctypes.Structure):
    _fields_ = [("position", Vector3_t),
                ("width", ctypes.c_float),
                ("height", ctypes.c_float),
                ("depth", ctypes.c_float)]

class AABB(object):

    def __init__(self, *args):
        if len(args) == 4 and isinstance(args[0], Vector3):
            self.position = args[0]
            self.width = args[1]
            self.height = args[2]
            self.depth = args[3]
        elif len(args) == 6:
            self._position = Vector3(args[0], args[1], args[2])
            self.width = args[3]
            self.height = args[4]
            self.depth = args[5]
        elif len(args) == 0:
            self.position = Vector3()
            self.width = 0.0
            self.height = 0.0
            self.depth = 0.0
        else:
            errmsg = "AABB must be initialized with types:\n"
            errmsg += "x:        " + (str(float) + "\n" + 
                      "y:        " + str(float) + "\n" + 
                      "z:        " + str(float) + "\n" + 
                      "width:    " + str(float) + "\n" +
                      "height:   " + str(float) + "\n" +
                      "depth:    " + str(float) + "\n\n" +
                      "or\n\n" +
                      "position: " + (str(Vector3)) + "\n" + 
                      "width:    " + str(float) + "\n" + 
                      "height:   " + str(float) + "\n" + 
                      "depth:    " + str(float))
            raise TypeError(errmsg)

    def __str__(self):
        return (str(self.position) + " " + str(self.width) + " " + 
                                           str(self.height) + " " + 
                                           str(self.depth))
     
    @classmethod
    @decorators.check_type(Vector3)
    def from_corners(cls, pmin = Vector3(), pmax = Vector3()):
        minx = min(pmin.x, pmax.x)
        miny = min(pmin.y, pmax.y)
        minz = min(pmin.z, pmax.z)
        maxx = max(pmin.x, pmax.x)
        maxy = max(pmin.y, pmax.y)
        maxz = max(pmin.z, pmax.z)
        width = maxx - minx
        height = maxy - miny
        depth = maxz - minz

        return cls(minx, miny, minz, width, height, depth)

    @classmethod
    def from_points(cls, point_list):
        if len(point_list) == 0:
            return cls()

        minx, miny, minz = point_list[0]
        maxx, maxy, maxz = point_list[0]
        for p in point_list:
            minx = min(p.x, minx);
            miny = min(p.y, miny);
            minz = min(p.z, minz);
            maxx = max(p.x, maxx);
            maxy = max(p.y, maxy);
            maxz = max(p.z, maxz);

        eps = 1e-9;
        width = maxx - minx + eps;
        height = maxy - miny + eps;
        depth = maxz - minz + eps;

        return cls(minx, miny, minz, width, height, depth)

    @classmethod
    def from_struct(cls, cstruct):
        return cls(Vector3.from_struct(cstruct.position), 
                   float(cstruct.width), 
                   float(cstruct.height), 
                   float(cstruct.depth))

    def to_struct(self):
        return AABB_t(Vector3_t(self.x, self.y, self.z), 
                      self.width, self.height, self.depth)

    @classmethod
    def from_grid_index(cls, grid_index = GridIndex(), dx = 0.0):
        return cls(grid_index.i*dx, grid_index.j*dx, grid_index.k*dx, dx, dx, dx)

    @property
    def x(self):
        return self._position.x

    @property
    def y(self):
        return self._position.y

    @property
    def z(self):
        return self._position.z

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def depth(self):
        return self._depth

    @property
    def position(self):
        return self._position

    @x.setter
    def x(self, value):
        self._position.x = value

    @y.setter
    def y(self, value):
        self._position.y = value

    @z.setter
    def z(self, value):
        self._position.z = value

    @width.setter
    @decorators.check_ge_zero
    def width(self, value):
        self._width = float(value)

    @height.setter
    @decorators.check_ge_zero
    def height(self, value):
        self._height = float(value)

    @depth.setter
    @decorators.check_ge_zero
    def depth(self, value):
        self._depth = float(value)

    @position.setter
    @decorators.check_type(Vector3)
    def position(self, vector):
        self._position = vector

    def expand(self, v):
        h = 0.5 * v;
        self.position -= Vector3(h, h, h);
        self.width += v;
        self.height += v;
        self.depth += v;

    @decorators.xyz_or_vector
    def contains_point(self, x, y, z):
        return (x >= self.x and y >= self.y and z >= self.z and
                x < self.x + self.width and 
                y < self.y + self.height and 
                z < self.z + self.depth)

    def get_min_point(self):
        return self.position

    def get_max_point(self):
        return self.position + Vector3(self.width, self.height, self.depth)

    def get_intersection(self, bbox):
        minp1 = self.get_min_point()
        minp2 = bbox.get_min_point()
        maxp1 = self.get_max_point()
        maxp2 = bbox.get_max_point()

        if minp1.x > maxp2.x or minp1.y > maxp2.y or minp1.z > maxp2.z:
            return AABB()

        interminx = max(minp1.x, minp2.x)
        interminy = max(minp1.y, minp2.y)
        interminz = max(minp1.z, minp2.z)
        intermaxx = min(maxp1.x, maxp2.x)
        intermaxy = min(maxp1.y, maxp2.y)
        intermaxz = min(maxp1.z, maxp2.z)

        return AABB.from_corners(Vector3(interminx, interminy, interminz), 
                                 Vector3(intermaxx, intermaxy, intermaxz))

    def get_union(self, bbox):
        minp1 = self.get_min_point()
        minp2 = bbox.get_min_point()
        maxp1 = self.get_max_point()
        maxp2 = bbox.get_max_point()

        if minp1.x > maxp2.x or minp1.y > maxp2.y or minp1.z > maxp2.z:
            return AABB()

        unionminx = min(minp1.x, minp2.x)
        unionminy = min(minp1.y, minp2.y)
        unionminz = min(minp1.z, minp2.z)
        unionmaxx = max(maxp1.x, maxp2.x)
        unionmaxy = max(maxp1.y, maxp2.y)
        unionmaxz = max(maxp1.z, maxp2.z)

        return AABB.from_corners(Vector3(unionminx, unionminy, unionminz), 
                                 Vector3(unionmaxx, unionmaxy, unionmaxz))