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

import bpy, bpy.utils.previews
import os, hashlib

try:
    from . import material_data
except ImportError:
    from ..objects import flip_fluid_map
    material_data = flip_fluid_map.Map({"materials": [], "blend_file":""})

CUSTOM_ICONS = None
IS_CUSTOM_ICONS_LOADED = False


def is_material_library_available():
    return material_data.materials and material_data.blend_file


def get_surface_material_enums_ui(scene = None, context = None):
    __check_custom_icons_initialized()

    non_library_enums = __get_non_material_library_enums()
    library_enums = __get_surface_material_library_enums()
    enums = non_library_enums + library_enums
    enums.insert(0, __get_none_material_enum())
    __add_material_enum_number_identifiers(enums)

    return enums


def get_whitewater_material_enums_ui(scene = None, context = None):
    __check_custom_icons_initialized()

    non_library_enums = __get_non_material_library_enums()
    library_enums = __get_whitewater_material_library_enums()
    enums = non_library_enums + library_enums
    enums.insert(0, __get_none_material_enum())
    __add_material_enum_number_identifiers(enums)

    return enums


def get_material_import_enums_ui(scene = None, context = None):
    __check_custom_icons_initialized()

    library_enums = __get_material_library_enums()
    library_enums.insert(0, __get_all_materials_enum())
    __add_material_enum_number_identifiers(library_enums)

    return library_enums


def is_imported_material(material):
    enums, materials = __get_imported_material_enums()
    for i, m in enumerate(materials):
        if m == material:
            return True, enums[i]
    return False, None


def import_all_materials():
    if not is_material_library_available():
        return

    material_enums = __get_material_library_enums()

    identifier_to_name = {}
    is_identifier_in_library = {}
    for e in material_enums:
        identifier_to_name[e[0]] = e[1]
        is_identifier_in_library[e[0]] = True

    imported_enums, _ = __get_imported_material_enums()
    is_identifier_imported = {}
    for e in imported_enums:
        is_identifier_imported[e[0]] = True

    filedir = os.path.dirname(os.path.realpath(__file__))
    blend_path = os.path.join(filedir, material_data.blend_file)
    with bpy.data.libraries.load(blend_path) as (data_from, data_to):
        added_material_identifiers = []
        for m in data_from.materials:
            if m in is_identifier_in_library and not m in is_identifier_imported:
                data_to.materials.append(m)
                added_material_identifiers.append(m)

    for i, m in enumerate(data_to.materials):
        if m is not None:
            mid = added_material_identifiers[i]
            m.name = identifier_to_name[mid]
            m.flip_fluid.is_library_material = True

    bpy.context.scene.update()


def import_material(enum_id):
    m = bpy.data.materials.get(enum_id)
    if m:
        return m

    imported_enums, imported_materials = __get_imported_material_enums()
    for i, e in enumerate(imported_enums):
        if e[0] == enum_id:
            return imported_materials[i]

    material_enums = __get_material_library_enums()
    for e in material_enums:
        if e[0] == enum_id:
            material_name = e[1]
            break

    filedir = os.path.dirname(os.path.realpath(__file__))
    blend_path = os.path.join(filedir, material_data.blend_file)
    with bpy.data.libraries.load(blend_path) as (data_from, data_to):
        for m in data_from.materials:
            if m == enum_id:
                data_to.materials.append(m)
                break

    material = None
    for m in data_to.materials:
        m.name = material_name
        m.flip_fluid.is_library_material = True
        return m

def material_identifier_to_name(identifier):
    mdata = material_data.materials
    for m in mdata:
        if m.identifier == identifier:
            return m.name
    return None


def __set_pixel(image, x, y, color):
    data_offset = (x + int(y * image.size[0])) * 4
    image.pixels[data_offset + 0] = color[0]
    image.pixels[data_offset + 1] = color[1]
    image.pixels[data_offset + 2] = color[2]
    image.pixels[data_offset + 3] = color[3]


def __draw_icon_overlay(image):
    width = image.size[0]
    height = image.size[1]

    tri_width = 12
    size = tri_width
    color = [0.0, 1.0, 0.229, 1.0]
    for j in range(0, tri_width):
        for i in range(width - size, width):
            __set_pixel(image, i, j, color)
        size -= 1


def __write_icon_to_file(filepath, icon):
    image = bpy.data.images.new("iconimg", width=icon.icon_size[0], 
                                           height=icon.icon_size[1],
                                           alpha=True)
    image.pixels = icon.icon_pixels_float
    image.filepath_raw = filepath
    image.file_format = 'PNG'
    __draw_icon_overlay(image)
    image.save()
    bpy.data.images.remove(image)


def __validate_material_enums(material_enums, blend_materials):
    for e in material_enums:
        identifier = e[0]
        if not identifier in blend_materials:
            errmsg = ("Error in material library: Material '" + 
                       identifier + "'' not found in '" + 
                       material_data.blend_file + "'" )
            print(errmsg)
            material_enums.remove(e)

        if identifier in blend_materials and blend_materials[identifier] is None:
            errmsg = ("Error in material library: Material '" + 
                       identifier + "'' could not be loaded from '" + 
                       material_data.blend_file + "'" )
            print(errmsg)
            material_enums.remove(e)


def __validate_enum_icons():
    if not is_material_library_available():
        return

    filedir = os.path.dirname(os.path.realpath(__file__))
    blend_path = os.path.join(filedir, material_data.blend_file)
    icon_dir = os.path.join(filedir, "icons")
    icon_hash_path = os.path.join(icon_dir, "icon_hash")
    os.makedirs(icon_dir, exist_ok=True)

    with open(blend_path, "rb") as f:
        bytes = f.read()
        current_blend_hash = hashlib.sha1(bytes).hexdigest()

    old_blend_hash = None
    if os.path.isfile(icon_hash_path):
        with open(icon_hash_path, "r") as f:
            old_blend_hash = f.read()

    if current_blend_hash != old_blend_hash:
        for f in os.listdir(icon_dir):
            fpath = os.path.join(icon_dir, f)
            try:
                os.remove(fpath)
            except OSError:
                pass

        with open(icon_hash_path, "w") as f:
            f.write(current_blend_hash)


def __initialize_material_library_icons():
    global CUSTOM_ICONS
    global IS_CUSTOM_ICONS_LOADED

    if not is_material_library_available():
        return

    material_enums = []
    mdata = material_data.materials
    for m in reversed(mdata):
        e = (m.identifier, m.name, m.description, len(material_enums))
        material_enums.append(e)

    filedir = os.path.dirname(os.path.realpath(__file__))
    blend_path = os.path.join(filedir, material_data.blend_file)
    icon_dir = os.path.join(filedir, "icons")

    __validate_enum_icons()

    with bpy.data.libraries.load(blend_path) as (data_from, data_to):
        data_to.materials = data_from.materials

    blend_materials = {}
    for m in data_to.materials:
        blend_materials[m.name] = m

    __validate_material_enums(material_enums, blend_materials)

    for i, e in enumerate(material_enums):
        identifier = e[0]
        icon_path = os.path.join(icon_dir, identifier + ".png")
        if not os.path.isfile(icon_path):
            material = blend_materials[identifier]
            __write_icon_to_file(icon_path, material.preview)

        if not identifier in CUSTOM_ICONS:
            CUSTOM_ICONS.load(identifier, icon_path, 'IMAGE')

    for m in data_to.materials:
        if m is not None:
            bpy.data.materials.remove(m)

    IS_CUSTOM_ICONS_LOADED = True


def __check_custom_icons_initialized():
    global IS_CUSTOM_ICONS_LOADED
    if not IS_CUSTOM_ICONS_LOADED:
        __initialize_material_library_icons()


def __add_material_enum_number_identifiers(enum_list):
    for i,e in enumerate(enum_list):
        h = int(abs(hash(e[0]))) % int(1e6)
        enum_list[i] = e + (h,)


def __get_none_material_enum():
    return ("MATERIAL_NONE", "None", "")


def __get_all_materials_enum():
    return ("ALL_MATERIALS", "All Materials", "Import all materials")


def __get_material_library_enums():
    global CUSTOM_ICONS
    enums = []
    mdata = material_data.materials
    for m in reversed(mdata):
        e = (m.identifier, 
             m.name, 
             m.description, 
             CUSTOM_ICONS[m.identifier].icon_id)
        enums.append(e)
    return enums


def __get_material_library_enums_by_type(material_type):
    global CUSTOM_ICONS
    enums = []
    mdata = material_data.materials
    for m in reversed(mdata):
        if m.type != material_type:
            continue
            
        e = (m.identifier, 
             m.name, 
             m.description, 
             CUSTOM_ICONS[m.identifier].icon_id)
        enums.append(e)
    return enums


def __get_surface_material_library_enums():
    return __get_material_library_enums_by_type('SURFACE')


def __get_whitewater_material_library_enums():
    return __get_material_library_enums_by_type('WHITEWATER')


def __get_non_material_library_enums():
    enums = []
    mdata = bpy.data.materials
    for m in reversed(mdata):
        e = (m.name, m.name, "", m.preview.icon_id)
        enums.append(e)
    return enums


def __get_imported_material_enums():
    material_enums = __get_material_library_enums()

    identifier_to_enum = {}
    name_to_identifier = {}
    is_name_in_library = {}
    for e in material_enums:
        identifier_to_enum[e[0]] = e
        name_to_identifier[e[1]] = e[0]
        is_name_in_library[e[1]] = True

    enums = []
    materials = []
    is_name_added = {}
    for m in bpy.data.materials:
        if not m.flip_fluid.is_library_material:
            continue
        # Remove suffix '.xxx' from name where x is in [0...9]. This suffix
        # is added by blender when a duplicate name is set.
        name = m.name
        components = name.split('.')
        suffix = components[-1]
        if len(components) > 1 and len(suffix) == 3 and suffix.isdigit():
            components.pop()
            name = ''.join(components)

        if name in is_name_in_library and not name in is_name_added:
            ident = name_to_identifier[name]
            enums.append(identifier_to_enum[ident])
            materials.append(m)
            is_name_added[name] = True

    return enums, materials


def load_post():
    __initialize_material_library_icons()


def register():
    global CUSTOM_ICONS
    CUSTOM_ICONS = bpy.utils.previews.new()


def unregister():
    global CUSTOM_ICONS
    bpy.utils.previews.remove(CUSTOM_ICONS)
