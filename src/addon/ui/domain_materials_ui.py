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


class FlipFluidDomainTypeMaterialsPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Materials"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        if not material_library.is_material_library_available():
            self.layout.label("This feature is missing data and will be disabled.")
            self.layout.label("Please contact the developers if you think this is an error.")
            return

        obj = context.scene.objects.active
        mprops = obj.flip_fluid.domain.materials

        column = self.layout.column()
        column.prop(mprops, "surface_material")
        column.prop(mprops, "whitewater_foam_material")
        column.prop(mprops, "whitewater_bubble_material")
        column.prop(mprops, "whitewater_spray_material")

        self.layout.row().separator()
        row = self.layout.row(align = True)
        row.prop(mprops, "material_import", text = "")
        row.operator("flip_fluid_operators.import_material")


def register():
    bpy.utils.register_class(FlipFluidDomainTypeMaterialsPanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeMaterialsPanel)
