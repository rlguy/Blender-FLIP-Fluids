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

import ctypes
import array
import struct

class TriangleMesh_t(ctypes.Structure):
    _fields_ = [("vertices", ctypes.c_void_p),
                ("triangles", ctypes.c_void_p),
                ("num_vertices", ctypes.c_int),
                ("num_triangles", ctypes.c_int)]

class TriangleMesh(object):
    def __init__(self):
        self.vertices = array.array('f', [])
        self.triangles = array.array('i', [])


    @classmethod
    def from_bobj(cls, bobj_data):
        int_data, bobj_data = bobj_data[:4], bobj_data[4:]
        num_vertices = struct.unpack('i', int_data)[0]

        num_floats = 3 * num_vertices
        num_bytes = 4 * num_floats
        vertex_data, bobj_data = bobj_data[:num_bytes], bobj_data[num_bytes:]
        vertices = list(struct.unpack('{0}f'.format(num_floats), vertex_data))

        int_data, bobj_data = bobj_data[:4], bobj_data[4:]
        num_triangles = struct.unpack('i', int_data)[0]

        num_ints = 3 * num_triangles
        num_bytes = 4 * num_ints
        triangle_data, bobj_data = bobj_data[:num_bytes], bobj_data[num_bytes:]
        triangles = list(struct.unpack('{0}i'.format(num_ints), triangle_data))

        self = cls()
        self.vertices = array.array('f', vertices)
        self.triangles = array.array('i', triangles)

        return self


    def to_bobj(self):
        num_vertices = len(self.vertices) // 3
        num_triangles = len(self.triangles) // 3
        datastr = struct.pack('i', num_vertices)
        datastr += self.vertices.tobytes()
        datastr += struct.pack('i', num_triangles)
        datastr += self.triangles.tobytes()

        return datastr

    def to_struct(self):

        num_vertices = len(self.vertices) // 3
        num_triangles = len(self.triangles) // 3

        vertex_data = (ctypes.c_float * len(self.vertices))()
        for i in range(len(self.vertices)):
            vertex_data[i] = self.vertices[i]

        triangle_data = (ctypes.c_int * len(self.triangles))()
        for i in range(len(self.triangles)):
            triangle_data[i] = self.triangles[i]

        struct = TriangleMesh_t()
        struct.vertices = ctypes.cast(vertex_data, ctypes.c_void_p)
        struct.triangles = ctypes.cast(triangle_data, ctypes.c_void_p)
        struct.num_vertices = num_vertices
        struct.num_triangles = num_triangles

        return struct

    def apply_transform(self, matrix_world):
        m = matrix_world
        for i in range(0, len(self.vertices), 3):
            v = [self.vertices[i + 0], self.vertices[i + 1], self.vertices[i + 2], 1]
            self.vertices[i + 0] = v[0]*m[0] + v[1]*m[1] + v[2]*m[2] + v[3]*m[3]
            self.vertices[i + 1] = v[0]*m[4] + v[1]*m[5] + v[2]*m[6] + v[3]*m[7]
            self.vertices[i + 2] = v[0]*m[8] + v[1]*m[9] + v[2]*m[10] + v[3]*m[11]

    def translate(self, tx, ty, tz):
        for i in range(0, len(self.vertices), 3):
            self.vertices[i + 0] += tx
            self.vertices[i + 1] += ty
            self.vertices[i + 2] += tz

    def scale(self, scale):
        for i in range(0, len(self.vertices), 3):
            self.vertices[i + 0] *= scale
            self.vertices[i + 1] *= scale
            self.vertices[i + 2] *= scale