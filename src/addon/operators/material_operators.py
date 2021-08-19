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

import bpy

from ..materials import material_library


class FlipFluidImportMaterial(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.import_material"
    bl_label = "Import"
    bl_description = "Import the selected material and link to material library"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(cls, context):
        return True


    def import_single_material(self, library_name):
        is_imported, imported_material_name = material_library.is_material_imported(library_name)
        if is_imported:
            msg = "Library material already imported: <" + library_name + ">"
            if library_name != imported_material_name:
                msg += " as <" + imported_material_name + ">"
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        imported_material_name = material_library.import_material(library_name)

        msg = "Successfully imported library material: <" + library_name + ">"
        if library_name != imported_material_name:
            msg += " as <" + imported_material_name + ">"
        self.report({'INFO'}, msg)

        return {'FINISHED'}


    def import_all_materials(self):
        material_list = bpy.context.scene.flip_fluid_material_library.material_list
        for mdata in material_list:
            self.import_single_material(mdata.name)

        return {'FINISHED'}


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        material_library_name = dprops.materials.material_import
        if material_library_name == 'ALL_MATERIALS':
            return_enum = self.import_all_materials()
        else:
            return_enum = self.import_single_material(material_library_name)

        return return_enum


class FlipFluidImportMaterialCopy(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.import_material_copy"
    bl_label = "Import Copy"
    bl_description = "Import a copy of the selected material and do not link to material library"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(cls, context):
        return True


    def import_single_material(self, library_name):
        imported_name = material_library.import_material_copy(library_name)

        msg = "Successfully imported copy of library material: <" + library_name + ">"
        if library_name != imported_name:
            msg += " as <" + imported_name + ">"

        self.report({'INFO'}, msg)

        return {'FINISHED'}


    def import_all_materials(self):
        material_list = bpy.context.scene.flip_fluid_material_library.material_list
        for mdata in material_list:
            self.import_single_material(mdata.name)

        return {'FINISHED'}


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        material_library_name = dprops.materials.material_import
        if material_library_name == 'ALL_MATERIALS':
            return_enum = self.import_all_materials()
        else:
            return_enum = self.import_single_material(material_library_name)

        return return_enum


def register():
    bpy.utils.register_class(FlipFluidImportMaterial)
    bpy.utils.register_class(FlipFluidImportMaterialCopy)


def unregister():
    bpy.utils.unregister_class(FlipFluidImportMaterial)
    bpy.utils.unregister_class(FlipFluidImportMaterialCopy)
