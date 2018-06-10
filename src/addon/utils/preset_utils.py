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

import bpy, os


def load_preset_materials(preset_info, loaded_materials_info):
    if "material_blend" not in preset_info:
        return

    material_blend_path = preset_info['material_blend']
    if not os.path.isfile(material_blend_path):
        return

    material_names_before = []
    material_names_after = []
    is_material_owner = []
    with bpy.data.libraries.load(material_blend_path) as (data_from, data_to):
        for m in data_from.materials:
            material_names_before.append(m)
            material = _find_preset_material(preset_info['identifier'], m)
            if material is not None:
                material_names_after.append(material.name)
                is_material_owner.append(False)
            else:
                data_to.materials.append(m)
                material_names_after.append(None)
                is_material_owner.append(True)

    for idx,m in enumerate(data_to.materials):
        m.flip_fluid.is_preset_material = True
        m.flip_fluid.preset_identifier = preset_info['identifier']
        m.flip_fluid.preset_blend_identifier = material_names_before[idx]
        for nidx,name in enumerate(material_names_after):
            if name is None:
                material_names_after[nidx] = m.name
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
            if material.flip_fluid.is_fake_use_set_by_addon and material.use_fake_user:
                material.use_fake_user = False
                material.flip_fluid.is_fake_use_set_by_addon = False
            remove_material = material is not None and material.users == 0
        if remove_material and not material.flip_fluid.skip_preset_unload:
            bpy.data.materials.remove(material)


def _find_preset_material(preset_id, material_id):
    for m in bpy.data.materials:
        if not m.flip_fluid.is_preset_material:
            continue
        if (m.flip_fluid.preset_identifier == preset_id and 
                m.flip_fluid.preset_blend_identifier == material_id):
            return m
    return None