# Blender FLIP Fluid Add-on
# Copyright (C) 2018 Ryan L. Guy
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class AABB(object):
    def __init__(self, x=0, y=0, z=0, xdim=0, ydim=0, zdim=0):
        self.x = x
        self.y = y
        self.z = z
        self.xdim = xdim
        self.ydim = ydim
        self.zdim = zdim


    @classmethod
    def from_blender_object(cls, obj):
        xmin, ymin, zmin = float('inf'), float('inf'), float('inf')
        xmax, ymax, zmax = -float('inf'), -float('inf'), -float('inf')
        for mv in obj.data.vertices:
            v = obj.matrix_world * mv.co
            xmin = min(v.x, xmin)
            ymin = min(v.y, ymin)
            zmin = min(v.z, zmin)
            xmax = max(v.x, xmax)
            ymax = max(v.y, ymax)
            zmax = max(v.z, zmax)
        xdim, ydim, zdim = xmax - xmin, ymax - ymin, zmax - zmin

        return cls(xmin, ymin, zmin, xdim, ydim, zdim)


    def is_empty(self, tol = 1e-6):
        return self.xdim * self.ydim * self.zdim < tol


    def contains(self, bbox):
        return (bbox.x > self.x and bbox.y > self.y and bbox.z > self.z and
                bbox.x + bbox.xdim < self.x + self.xdim and
                bbox.y + bbox.ydim < self.y + self.ydim and
                bbox.z + bbox.zdim < self.z + self.zdim)


    def contains_point(self, p):
        return (p[0] >= self.x and p[0] < self.x + self.xdim and
                p[1] >= self.y and p[1] < self.y + self.ydim and
                p[2] >= self.z and p[2] < self.z + self.zdim)


    def expand(self, amount):
        hw = 0.5 * amount
        self.x -= hw
        self.y -= hw
        self.z -= hw
        self.xdim += hw
        self.ydim += hw
        self.zdim += hw

        return AABB(self.x - hw, self.y - hw, self.z - hw,
                    self.xdim + hw, self.ydim + hw, self.zdim + hw)


    def intersection(self, bbox):
        xmin = max(self.x, bbox.x)
        ymin = max(self.y, bbox.y)
        zmin = max(self.z, bbox.z)
        xmax = min(self.x + self.xdim, bbox.x + bbox.xdim)
        ymax = min(self.y + self.ydim, bbox.y + bbox.ydim)
        zmax = min(self.z + self.zdim, bbox.z + bbox.zdim)
        xdim = max(0.0, xmax - xmin)
        ydim = max(0.0, ymax - ymin)
        zdim = max(0.0, zmax - zmin)

        return AABB(xmin, ymin, zmin, xdim, ydim, zdim)


    def to_dict(self):
        return {'x': self.x, 'y': self.y, 'z': self.z,
                'xdim': self.xdim, 'ydim': self.ydim, 'zdim': self.zdim}
