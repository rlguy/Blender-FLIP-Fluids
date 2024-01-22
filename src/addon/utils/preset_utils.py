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

import bpy, os, glob


def load_preset_materials(preset_info, loaded_materials_info):
    preset_directory = preset_info['path']
    blend_files = glob.glob(preset_directory + "/*.blend")
    if not blend_files:
        return

    for blend_file in blend_files:
        material_names_before = []
        material_names_after = []
        is_material_owner = []
        with bpy.data.libraries.load(blend_file) as (data_from, data_to):
            for blend_material_name in data_from.materials:
                material_names_before.append(blend_material_name)
                material_object = _find_preset_material(preset_info['identifier'], blend_material_name)
                if material_object is not None:
                    material_names_after.append(material_object.name)
                    is_material_owner.append(False)
                else:
                    data_to.materials.append(blend_material_name)
                    material_names_after.append(None)
                    is_material_owner.append(True)

        for idx,material_object in enumerate(data_to.materials):
            material_object.flip_fluid_material_library.is_preset_material = True
            material_object.flip_fluid_material_library.preset_identifier = preset_info['identifier']
            material_object.flip_fluid_material_library.preset_blend_identifier = material_names_before[idx]
            for nidx,material_name in enumerate(material_names_after):
                if material_name is None:
                    material_names_after[nidx] = material_object.name
                    break

        for i in range(len(material_names_before)):
            minfo = loaded_materials_info.add()
            minfo.preset_id = material_names_before[i]
            minfo.loaded_id = material_names_after[i]
            if hasattr(minfo, "is_owner"):
                minfo.is_owner = is_material_owner[i]


def unload_preset_materials(loaded_materials_info):
    for minfo in loaded_materials_info:
        material = bpy.data.materials.get(minfo.loaded_id)
        if hasattr(minfo, "is_owner"):
            remove_material = material is not None and minfo.is_owner
        else:
            if material.flip_fluid_material_library.is_fake_user_set_by_addon and material.use_fake_user:
                material.use_fake_user = False
                material.flip_fluid_material_library.is_fake_user_set_by_addon = False
            remove_material = material is not None and material.users == 0
        if remove_material and not material.flip_fluid_material_library.skip_preset_unload:
            bpy.data.materials.remove(material)


def _find_preset_material(preset_id, material_id):
    for m in bpy.data.materials:
        if not m.flip_fluid_material_library.is_preset_material:
            continue
        if (m.flip_fluid_material_library.preset_identifier == preset_id and 
                m.flip_fluid_material_library.preset_blend_identifier == material_id):
            return m
    return None