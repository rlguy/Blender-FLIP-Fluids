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

import bpy, os, glob, hashlib, bpy.utils.previews
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        EnumProperty,
        StringProperty,
        PointerProperty,
        CollectionProperty
        )

from .. import types
from ..utils import version_compatibility_utils as vcu


class FLIPFluidMaterialLibraryMaterial(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    name = StringProperty(default=""); exec(conv("name"))
    description = StringProperty(default=""); exec(conv("description"))
    path = StringProperty(default=""); exec(conv("path"))
    type = EnumProperty(items=types.material_types, default="MATERIAL_TYPE_SURFACE"); exec(conv("type"))
    icon_id = IntProperty(default=-1); exec(conv("icon_id"))
    imported_icon_id = IntProperty(default=-1); exec(conv("imported_icon_id"))


    def get_ui_enum(self):
        library = bpy.context.scene.flip_fluid_material_library
        is_imported, imported_name = library.is_material_imported(self.name)
        if is_imported:
            display_name = imported_name
            icon_id = self.imported_icon_id
        else:
            display_name = self.name
            icon_id = self.icon_id
        return (self.name, display_name, self.description, icon_id, self._get_hash())


    def _get_hash(self):
        # Append text when generating library material hash so that different
        # hash values are created between library and non-library materials with
        # the same name
        hash_string = self.name + "flip_fluid_material_library"
        return int(hashlib.sha1(hash_string.encode('utf-8')).hexdigest(), 16) % int(1e6)


class FLIPFluidMaterialLibrary(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    library_path = StringProperty(default=""); exec(conv("library_path"))
    material_list = CollectionProperty(type=FLIPFluidMaterialLibraryMaterial); exec(conv("material_list"))


    @classmethod
    def register(cls):
        cls.material_icons = bpy.utils.previews.new()


    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.material_icons)


    def load_post(self):
        # Data block id (pointer) won't be consistent between saves so
        # need reinitialize values of imported material library materials
        for m in bpy.data.materials:
            if m.flip_fluid_material_library.is_library_material:
                m.flip_fluid_material_library.reinitialize_data_block_id(m)


    def scene_update_post(self, scene):
        for m in bpy.data.materials:
            if not m.flip_fluid_material_library.is_library_material:
                continue
            if not m.flip_fluid_material_library.is_original_data_block(m):
                m.flip_fluid_material_library.deactivate()


    def initialize(self, library_path):
        self.library_path = library_path
        self._initialize_library_material_list()
        self._initialize_preview_icons()


    def check_icons_initialized(self):
        # Icons will be cleared if Blender scripts are reloaded so
        # this method can check and re-initialize icons if needed
        if len(self.material_icons) > 0:
            return
        self._initialize_preview_icons()


    def import_material(self, material_name):
        if not self.is_material_in_library(material_name):
            return material_name

        is_imported, imported_name = self.is_material_imported(material_name)
        if is_imported:
            return imported_name

        mdata = self._get_material_data_from_name(material_name)
        with bpy.data.libraries.load(mdata.path) as (data_from, data_to):
            for material in data_from.materials:
                if material == material_name:
                    data_to.materials.append(material)
                    break

        material_object = data_to.materials[0]
        material_object.flip_fluid_material_library.activate(material_object, material_name)

        return material_object.name


    def get_import_material_copy_name(self, name):
        prefix = "FF "
        if name.startswith(prefix) and len(name) > len(prefix):
            name = name[len(prefix):]
        name = name.split('.')[0]

        if not bpy.data.materials.get(name):
            return name

        duplicates = []
        for m in bpy.data.materials:
            if m.name == name:
                duplicates.append(0)
                continue
            suffix = m.name.rsplit('.', 1)[-1]
            if m.name.startswith(name) and len(m.name) == len(name) + 4 and suffix.isdigit():
                duplicates.append(int(suffix))

        if not duplicates:
            return name

        for i in range(1, 999):
            if not i in duplicates:
                return name + "." + str(i).zfill(3)
        return name


    def import_material_copy(self, material_name):
        mdata = self._get_material_data_from_name(material_name)
        with bpy.data.libraries.load(mdata.path) as (data_from, data_to):
            for material in data_from.materials:
                if material == material_name:
                    data_to.materials.append(material)
                    break

        material_object = data_to.materials[0]
        material_object.name = self.get_import_material_copy_name(material_object.name)
        return material_object.name


    def get_imported_material(self, library_name):
        for m in bpy.data.materials:
            libprops = m.flip_fluid_material_library
            if libprops.is_library_material and libprops.library_name == library_name:
                return m.name
        return None


    def is_material_imported(self, library_name):
        for m in bpy.data.materials:
            libprops = m.flip_fluid_material_library
            if libprops.is_library_material and libprops.library_name == library_name:
                return True, m.name
        return False, ""


    def is_material_in_library(self, material_name):
        for mdata in self.material_list:
            if mdata.name == material_name:
                return True
        return False


    def _initialize_library_material_list(self):
        self.material_list.clear()

        extension = "blend"
        subdirs = ["surface", "whitewater", "all"]
        for subdir in subdirs:
            subdir_path = os.path.join(self.library_path, subdir)
            subdir_files = glob.glob(subdir_path + "/*." + extension)
            for f in subdir_files:
                if subdir == "surface":
                    mtype = 'MATERIAL_TYPE_SURFACE'
                elif subdir == "whitewater":
                    mtype = 'MATERIAL_TYPE_WHITEWATER'
                elif subdir == "all":
                    mtype = 'MATERIAL_TYPE_ALL'

                description_path = f[:-len(extension)] + "description"
                description_text = ""
                if os.path.isfile(description_path):
                    with open(description_path, 'r', encoding='utf-8') as description_file:
                        description_text = description_file.read()

                new_material = self.material_list.add()
                new_material.name = os.path.splitext(os.path.basename(f))[0]
                new_material.description = str(description_text)
                new_material.path = f
                new_material.type = mtype
                new_material.icon_id = -1   # Will be set after icons are initialized


    def _calculate_material_library_hash(self):
        if len(self.material_list) == 0:
            return "0"

        SHAhash = hashlib.md5()
        for m in self.material_list:
            with open(m.path, "rb") as f:
                bytes = f.read()
                SHAhash.update(hashlib.md5(bytes).hexdigest().encode('utf-8'))

        return SHAhash.hexdigest()


    def _update_material_library_hash(self):
        icon_dir = os.path.join(self.library_path, "icons")
        os.makedirs(icon_dir, exist_ok=True)

        icon_hash_path = os.path.join(icon_dir, "material_library_hash")
        old_material_library_hash = None
        if os.path.isfile(icon_hash_path):
            with open(icon_hash_path, 'r', encoding='utf-8') as f:
                old_material_library_hash = f.read()

        current_material_library_hash = self._calculate_material_library_hash()
        if current_material_library_hash != old_material_library_hash:
            with open(icon_hash_path, 'w', encoding='utf-8') as f:
                f.write(current_material_library_hash)
            return True

        return False


    def _set_pixel(self, image, x, y, color):
        data_offset = (x + int(y * image.size[0])) * 4
        image.pixels[data_offset + 0] = color[0]
        image.pixels[data_offset + 1] = color[1]
        image.pixels[data_offset + 2] = color[2]
        image.pixels[data_offset + 3] = color[3]


    def _draw_icon_overlay(self, image, color):
        width = image.size[0]
        height = image.size[1]

        tri_width = 16
        size = tri_width
        for j in range(0, tri_width):
            for i in range(width - size, width):
                self._set_pixel(image, i, j, color)
            size -= 1


    def _write_icon_to_file(self, material_preview, color, icon_path):
        image = bpy.data.images.new(
                "iconimg", 
                width=material_preview.icon_size[0], 
                height=material_preview.icon_size[1],
                alpha=True
                )
        image.pixels = material_preview.icon_pixels_float
        image.filepath_raw = icon_path
        image.file_format = 'PNG'
        self._draw_icon_overlay(image, color)
        image.save()
        bpy.data.images.remove(image)


    def _generate_material_library_icons(self):
        imported_material_names = []
        for m in self.material_list:
            with bpy.data.libraries.load(m.path) as (data_from, data_to):
                data_to.materials = data_from.materials
                for mdata in data_to.materials:
                    imported_material_names.append(mdata)

            icon_path = os.path.join(self.library_path, "icons", m.name + ".png")
            imported_icon_path = os.path.join(self.library_path, "icons", m.name + "_imported.png")
            material = data_to.materials[0]
            self._write_icon_to_file(material.preview, [1.0, 0.25, 0.02, 1.0], icon_path)
            self._write_icon_to_file(material.preview, [0.0, 1.0, 0.23, 1.0], imported_icon_path)

        for mname in imported_material_names:
            material = bpy.data.materials.get(mname)
            if material:
                bpy.data.materials.remove(material)


    def _initialize_preview_icons(self):
        require_update = self._update_material_library_hash()
        if require_update:
            self._generate_material_library_icons()

        self.material_icons.clear()
        for m in self.material_list:
            icon_path = os.path.join(self.library_path, "icons", m.name + ".png")
            imported_icon_path = os.path.join(self.library_path, "icons", m.name + "_imported.png")
            self.material_icons.load(m.name, icon_path, 'IMAGE')
            self.material_icons.load(m.name + "_imported", imported_icon_path, 'IMAGE')
            m.icon_id = self.material_icons[m.name].icon_id
            m.imported_icon_id = self.material_icons[m.name + "_imported"].icon_id


    def _get_material_data_from_name(self, name):
        mdata = None
        for m in self.material_list:
            if m.name == name:
                mdata = m
                break
        return mdata


def register():
    bpy.utils.register_class(FLIPFluidMaterialLibraryMaterial)
    bpy.utils.register_class(FLIPFluidMaterialLibrary)


def unregister():
    bpy.utils.unregister_class(FLIPFluidMaterialLibraryMaterial)
    bpy.utils.unregister_class(FLIPFluidMaterialLibrary)

