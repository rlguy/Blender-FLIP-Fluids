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

if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'preferences_properties',
        'custom_properties',
        'preset_properties',
        'flip_fluid_properties',
        'object_properties',
        'material_properties',
        'helper_properties'
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy

from . import (
    preferences_properties,
    custom_properties,
    preset_properties,
    flip_fluid_properties,
    object_properties,
    material_properties,
    helper_properties
    )


def scene_update_post(scene):
    object_properties.scene_update_post(scene)
    flip_fluid_properties.scene_update_post(scene)


def frame_change_pre(scene):
    object_properties.frame_change_pre(scene)


def load_pre():
    object_properties.load_pre()


def load_post():
    preferences_properties.load_post()
    object_properties.load_post()


def save_pre():
    object_properties.save_pre()


def save_post():
    object_properties.save_post()


def register():
    preferences_properties.register()
    custom_properties.register()
    preset_properties.register()
    flip_fluid_properties.register()
    object_properties.register()
    material_properties.register()
    helper_properties.register()


def unregister():
    preferences_properties.unregister()
    custom_properties.unregister()
    preset_properties.unregister()
    flip_fluid_properties.unregister()
    object_properties.unregister()
    material_properties.unregister()
    helper_properties.unregister()