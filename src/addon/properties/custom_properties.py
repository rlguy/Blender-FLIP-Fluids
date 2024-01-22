# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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

import bpy
from bpy.props import (
        IntProperty,
        FloatProperty,
        BoolProperty,
        PointerProperty
        )

def NewMinMaxIntProperty(**args):
    dmin, dmax = _format_min_max_properties(args)

    def update_value_min(self, context):
        if self.value_min > self.value_max:
            self.value_max = self.value_min

    def update_value_max(self, context):
        if self.value_max < self.value_min:
            self.value_min = self.value_max

    dmin['update'] = update_value_min
    dmax['update'] = update_value_max

    class MinMaxIntProperty(bpy.types.PropertyGroup):
        @classmethod
        def register(cls):
            cls.value_min = IntProperty(**dmin)
            cls.value_max = IntProperty(**dmax)
            cls.is_min_max_property = BoolProperty(default=True)
        def min(self):
            return self.value_min
        def max(self):
            return self.value_max

    bpy.utils.register_class(MinMaxIntProperty)
    return PointerProperty(type=MinMaxIntProperty)


def NewMinMaxFloatProperty(**args):
    dmin, dmax = _format_min_max_properties(args)

    def update_value_min(self, context):
        if self.value_min > self.value_max:
            self.value_max = self.value_min

    def update_value_max(self, context):
        if self.value_max < self.value_min:
            self.value_min = self.value_max

    dmin['update'] = update_value_min
    dmax['update'] = update_value_max

    class MinMaxFloatProperty(bpy.types.PropertyGroup):
        @classmethod
        def register(cls):
            cls.value_min = FloatProperty(**dmin)
            cls.value_max = FloatProperty(**dmax)
            cls.is_min_max_property = BoolProperty(default=True)
        def min(self):
            return self.value_min
        def max(self):
            return self.value_max

    bpy.utils.register_class(MinMaxFloatProperty)
    return PointerProperty(type=MinMaxFloatProperty)


def _format_min_max_properties(args):
    dmin, dmax = {}, {}
    for k,v in args.items():
        if k.endswith("_min"):
            k = k.replace("_min", "")
            dmin[k] = v
        elif k.endswith("_max"):
            k = k.replace("_max", "")
            dmax[k] = v
    return dmin, dmax


def register():
    pass


def unregister():
    pass
