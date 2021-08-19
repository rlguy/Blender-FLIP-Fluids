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
        return obj_props.is_active and obj_props.object_type == "TYPE_OUTFLOW"

    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        outflow_props = obj_props.outflow
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Outflow Object Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Outflow-Object-Settings"
            column.operator(
                "wm.url_open", 
                text="Outflow objects must have manifold/watertight geometry", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Manifold-Meshes"

        column = self.layout.column()
        column.prop(outflow_props, "is_enabled")

        if show_advanced:
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
        column.prop(outflow_props, "export_animated_mesh")
        if show_advanced:
            column.prop(outflow_props, "skip_reexport")
            column.separator()
            column = box.column(align=True)
            column.enabled = outflow_props.skip_reexport
            column.prop(outflow_props, "force_reexport_on_next_bake", toggle=True)
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_OutflowTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_OutflowTypePanel)
