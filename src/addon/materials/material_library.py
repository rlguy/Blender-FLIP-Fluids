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

import bpy, os, hashlib
from bpy.props import (
        PointerProperty
        )

from ..objects import flip_fluid_material_library
from ..utils import version_compatibility_utils as vcu


def get_surface_material_enums_ui(scene=None, context=None):
    bpy.context.scene.flip_fluid_material_library.check_icons_initialized()
    enums = []
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_SURFACE')
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_ALL')
    enums += __get_non_material_library_enums_by_type()
    enums += [__get_none_material_enum()]
    enums.reverse()
    return enums


def get_whitewater_material_enums_ui(scene=None, context=None):
    bpy.context.scene.flip_fluid_material_library.check_icons_initialized()
    enums = []
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_WHITEWATER')
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_ALL')
    enums += __get_non_material_library_enums_by_type()
    enums += [__get_none_material_enum()]
    enums.reverse()
    return enums


def get_material_import_enums_ui(scene = None, context = None):
    bpy.context.scene.flip_fluid_material_library.check_icons_initialized()
    enums = []
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_SURFACE')
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_WHITEWATER')
    enums += __get_material_library_enums_by_type('MATERIAL_TYPE_ALL')
    enums += [__get_all_materials_enum()]
    enums.reverse()
    return enums


def import_material(material_name):
    return bpy.context.scene.flip_fluid_material_library.import_material(material_name)


def import_material_copy(material_name):
    return bpy.context.scene.flip_fluid_material_library.import_material_copy(material_name)


def is_material_imported(material_name):
    return bpy.context.scene.flip_fluid_material_library.is_material_imported(material_name)


def is_material_library_available():
    library = bpy.context.scene.flip_fluid_material_library
    return len(library.material_list) > 0


def __get_material_library_enums_by_type(material_type):
    library = bpy.context.scene.flip_fluid_material_library
    enums = []
    for mdata in library.material_list:
        if mdata.type == material_type:
            enums.append(mdata.get_ui_enum())
    return enums


def __get_non_material_library_enums_by_type():
    enums = []
    for m in bpy.data.materials:
        if not m.flip_fluid_material_library.is_library_material:
            if vcu.is_blender_30():
                # material preview can be None in Blender 3.0. Use the preview_ensure function
                # to make sure the preview is loaded
                m.preview_ensure()
            e = (m.name, m.name, "", m.preview.icon_id, __get_non_material_library_material_hash(m))
            enums.append(e)
    return enums


def __get_non_material_library_material_hash(material):
    return int(hashlib.sha1(material.name.encode('utf-8')).hexdigest(), 16) % int(1e6)


def __get_none_material_enum():
        return ("MATERIAL_NONE", "None", "", 0, 0)


def __get_all_materials_enum():
        return ("ALL_MATERIALS", "All Materials", "Import all materials", 0, 0)

def load_post():
    library_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "material_library")
    bpy.context.scene.flip_fluid_material_library.load_post()
    bpy.context.scene.flip_fluid_material_library.initialize(library_path)


def scene_update_post(scene):
    bpy.context.scene.flip_fluid_material_library.scene_update_post(scene)


def register():
    bpy.types.Scene.flip_fluid_material_library = PointerProperty(
                name="Flip Fluid Material Library",
                description="",
                type=flip_fluid_material_library.FLIPFluidMaterialLibrary,
                )


def unregister():
    del bpy.types.Scene.flip_fluid_material_library
