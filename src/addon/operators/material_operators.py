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

import bpy

from ..materials import material_library


class FlipFluidImportMaterial(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.import_material"
    bl_label = "Import"
    bl_description = "Import selected material"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        import_material = dprops.materials.material_import
        if import_material == 'ALL_MATERIALS':
            material_library.import_all_materials()
        else:
            material_library.import_material(import_material)

        mname = material_library.material_identifier_to_name(import_material)
        if mname is None:
            mname = 'All Materials'
        self.report({'INFO'}, "Successfully imported library material: " + mname)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidImportMaterial)


def unregister():
    bpy.utils.unregister_class(FlipFluidImportMaterial)
