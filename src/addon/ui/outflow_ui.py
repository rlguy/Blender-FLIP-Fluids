# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
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


class FLIPFLUID_PT_OutflowTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"

    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_OUTFLOW" and not is_addon_disabled

    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        outflow_props = obj_props.outflow

        show_disabled_in_viewport_warning = True
        if show_disabled_in_viewport_warning and obj.hide_viewport:
            box = self.layout.box()
            box.alert = True
            column = box.column(align=True)
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.prop(outflow_props, "disabled_in_viewport_tooltip", icon="QUESTION", emboss=False, text="")
            row.label(text="Object is currently disabled in the viewport")
            row.label(text="", icon="RESTRICT_VIEW_ON")
            column.label(text="This object will not be included within the simulation")

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        column = self.layout.column()
        column.prop(outflow_props, "is_enabled")

        column = self.layout.column()
        split = column.split()
        column = split.column()
        column.prop(outflow_props, "remove_fluid")
        column = split.column()
        column.prop(outflow_props, "remove_whitewater")

        self.layout.separator()
        column = self.layout.column()
        column.prop(outflow_props, "is_inversed")
        
        box = self.layout.box()
        box.label(text="Mesh Data Export:")
        column = box.column(align=True)

        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.prop(outflow_props, "export_animated_mesh")

        is_child_object = obj.parent is not None
        is_hint_enabled = not vcu.get_addon_preferences().dismiss_export_animated_mesh_parented_relation_hint
        if is_hint_enabled and not outflow_props.export_animated_mesh and is_child_object:
            row.prop(context.scene.flip_fluid_helper, "export_animated_mesh_parent_tooltip", 
                    icon="QUESTION", emboss=False, text=""
                    )
            row.label(text="←Hint: export option may be required")

        column.prop(outflow_props, "skip_reexport")
        column.separator()
        column = box.column(align=True)
        column.enabled = outflow_props.skip_reexport
        column.prop(outflow_props, "force_reexport_on_next_bake", toggle=True)

        column = self.layout.column(align=True)
        column.separator()
        column.operator("flip_fluid_operators.copy_setting_to_selected", icon='COPYDOWN')
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_OutflowTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_OutflowTypePanel)
