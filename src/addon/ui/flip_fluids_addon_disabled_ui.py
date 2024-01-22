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

import bpy

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_FLIPFluidsAddonDisabledPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluids Addon Disabled"

    @classmethod
    def poll(cls, context):
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return is_addon_disabled

    def draw(self, context):
        column = self.layout.column(align=True)
        row = column.row(align=True)
        row.alert = True
        row.label(text="FLIP Fluids Addon has been disabled in this Blend file", icon="INFO")
        row = column.row(align=True)
        row.alert = True
        row.label(text="Click to re-enable and use the addon", icon="INFO")

        operator_name = "flip_fluid_operators.enable_addon_in_blend_file"
        icon = context.scene.flip_fluid.get_logo_icon()
        if icon is not None:
            column.operator(operator_name, icon_value=icon.icon_id)
        else:
            column.operator(operator_name, icon='X')


def register():
    bpy.utils.register_class(FLIPFLUID_PT_FLIPFluidsAddonDisabledPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_FLIPFluidsAddonDisabledPanel)
