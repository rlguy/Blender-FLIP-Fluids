# Blender FLIP Fluids Add-on
# Copyright (C) 2021 Ryan L. Guy
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

if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'flip_fluid_aabb',
        'flip_fluid_cache',
        'flip_fluid_material_library'
        'flip_fluid_map',
        'flip_fluid_geometry_export_object',
        'flip_fluid_geometry_database',
        'flip_fluid_geometry_exporter',
        'flip_fluid_preset_stack',
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy

from . import (
    flip_fluid_aabb,
    flip_fluid_cache,
    flip_fluid_material_library,
    flip_fluid_map,
    flip_fluid_geometry_export_object,
    flip_fluid_geometry_database,
    flip_fluid_geometry_exporter,
    flip_fluid_preset_stack,
    )


def register():
    flip_fluid_cache.register()
    flip_fluid_material_library.register()
    flip_fluid_preset_stack.register()


def unregister():
    flip_fluid_cache.unregister()
    flip_fluid_material_library.unregister()
    flip_fluid_preset_stack.unregister()