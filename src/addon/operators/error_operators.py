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

import bpy, textwrap
from bpy.props import (
        StringProperty,
        IntProperty
        )

from ..utils import version_compatibility_utils as vcu


class FlipFluidDisplayError(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.display_error"
    bl_label = ""
    bl_description = ""

    error_message = StringProperty()
    exec(vcu.convert_attribute_to_28("error_message"))

    error_description = StringProperty()
    exec(vcu.convert_attribute_to_28("error_description"))

    popup_width = IntProperty(default=400)
    exec(vcu.convert_attribute_to_28("popup_width"))


    def draw(self, context):
        row = self.layout.row()
        row.alignment = 'CENTER'
        row.label(text=self.error_message, icon='ERROR')

        if self.error_description:
            text_list = textwrap.wrap(self.error_description, width=self.popup_width//6)
            column = self.layout.column(align=True)
            column.separator()
            column.separator()
            for idx,line in enumerate(text_list):
                column.label(text=line)

        self.layout.separator()
        self.layout.separator()


    def execute(self, context):
        self.report({'INFO'}, self.error_message)
        if self.error_description:
            self.report({'INFO'}, self.error_description)
        self.error_message = ""
        self.error_description = ""
        self.popup_width = 400
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=self.popup_width)


def register():
    bpy.utils.register_class(FlipFluidDisplayError)


def unregister():
    bpy.utils.unregister_class(FlipFluidDisplayError)
