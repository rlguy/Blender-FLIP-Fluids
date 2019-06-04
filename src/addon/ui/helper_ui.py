# Blender FLIP Fluid Add-on
# Copyright (C) 2019 Ryan L. Guy
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


class FLIPFLUID_PT_HelperPanelMain(bpy.types.Panel):
    bl_label = "Main Operations"
    bl_category = "FLIP Fluids"
    bl_space_type = 'VIEW_3D'
    if vcu.is_blender_28():
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'


    @classmethod
    def poll(cls, context):
        return True


    def draw(self, context):
        hprops = context.scene.flip_fluid_helper
        preferences = vcu.get_addon_preferences(context)

        box = self.layout.box()
        column = box.column(align=True)
        column.label(text="Add/Remove Objects:")
        column.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="Obstacle"
                ).object_type="TYPE_OBSTACLE"
        row = column.row(align=True)
        row.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="Fluid"
                ).object_type="TYPE_FLUID"
        row.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="Inflow"
                ).object_type="TYPE_INFLOW"
        row.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="Outflow"
                ).object_type="TYPE_OUTFLOW"
        column = box.column(align=True)
        column.operator("flip_fluid_operators.helper_remove_objects", text="Remove")

        box = self.layout.box()
        column = box.column(align=True)
        column.label(text="Quick Select:")
        column.operator("flip_fluid_operators.helper_select_domain", text="Domain")
        column = box.column(align=True)
        column.operator("flip_fluid_operators.helper_select_surface", text="Surface")
        row = column.row(align=True)
        row.operator("flip_fluid_operators.helper_select_foam", text="Foam")
        row.operator("flip_fluid_operators.helper_select_bubble", text="Bubble")
        row.operator("flip_fluid_operators.helper_select_spray", text="Spray")

        column = self.layout.column()
        column.separator()
        column.operator(
                "flip_fluid_operators.check_for_updates", 
                text="Check for Updates", 
                icon="WORLD"
            )

        column.separator()
        column.prop(preferences, "beginner_friendly_mode")



class FLIPFLUID_PT_HelperPanelDisplay(bpy.types.Panel):
    bl_label = "Display Operators"
    bl_category = "FLIP Fluids"
    bl_space_type = 'VIEW_3D'
    if vcu.is_blender_28():
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'


    @classmethod
    def poll(cls, context):
        return True


    def draw(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            self.layout.label(text="Please create a domain object")
            return
        rprops = dprops.render
        hprops = context.scene.flip_fluid_helper

        box = self.layout.box()
        column = box.column(align=True)
        column.label(text="Quick Viewport Display:")

        row = column.row(align=True)
        row.operator("flip_fluid_operators.quick_viewport_display_final", text="Final")
        row.operator("flip_fluid_operators.quick_viewport_display_preview", text="Preview")
        row.operator("flip_fluid_operators.quick_viewport_display_none", text="None")
        column.operator("flip_fluid_operators.reload_frame", text="Reload Frame")

        column = box.column(align=True)
        column.operator("flip_fluid_operators.helper_load_last_frame")
        column.prop(hprops, "enable_auto_frame_load")

        column.separator()
        column.separator()
        column.prop(hprops, "playback_frame_offset")


        self.layout.separator()
        box = self.layout.box()
        column = box.column()
        split = vcu.ui_split(column, factor=0.4, align=True)
        left_column = split.column(align=True)
        left_column.separator()
        left_column.separator()
        left_column.separator()
        left_column.prop(rprops, "hold_frame")

        right_column = split.column(align=True)
        right_column.enabled = rprops.hold_frame
        right_column.operator("flip_fluid_operators.free_unheld_cache_files", 
                              text="Delete Other Cache Files")
        right_column.prop(rprops, "hold_frame_number")
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_HelperPanelMain)
    bpy.utils.register_class(FLIPFLUID_PT_HelperPanelDisplay)


def unregister():
    try:
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelMain)
        bpy.utils.unregister_class(FLIPFLUID_PT_HelperPanelDisplay)
    except:
        pass
