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

if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'none_ui',
        'fluid_ui',
        'obstacle_ui',
        'inflow_ui',
        'outflow_ui',
        'force_field_ui',
        'domain_ui',
        'cache_object_ui',
        'helper_ui'
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy

from . import(
        none_ui,
        fluid_ui,
        obstacle_ui,
        inflow_ui,
        outflow_ui,
        force_field_ui,
        domain_ui,
        cache_object_ui,
        helper_ui
        )

from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils


def append_to_PHYSICS_PT_add_panel(self, context):
    obj = vcu.get_active_object(context)
    if not (obj.type == 'MESH' or obj.type == 'EMPTY', obj.type == 'CURVE'):
        return

    column = self.layout.column(align=True)
    split = vcu.ui_split(column, factor=0.5)
    column_left = split.column()
    column_right = split.column()

    if obj.flip_fluid.is_active:
        row = column_right.row(align=True)
        row.operator(
                "flip_fluid_operators.flip_fluid_remove", 
                 text="FLIP Fluid", 
                 icon='X'
                )

        if obj.flip_fluid.is_domain():
            row.prop(context.scene.flip_fluid, "show_viewport", icon="RESTRICT_VIEW_OFF", text="")
            row.prop(context.scene.flip_fluid, "show_render", icon="RESTRICT_RENDER_OFF", text="")

        addon_prefs = vcu.get_addon_preferences(context)
        if addon_prefs.beginner_friendly_mode:
            tooltip_column = self.layout.column(align=True)
            row = tooltip_column.row(align=True)
            row.alignment = 'LEFT'
            row.prop(addon_prefs, "beginner_friendly_mode_tooltip", icon='QUESTION', emboss=False, text="")
            row.label(text="FLIP Fluids Beginner Friendly Mode is enabled")

        
        # Experimental Build Warning
        addon_prefs.enable_experimental_build_warning = False    # Remove this line for experimental release
        if addon_prefs.enable_experimental_build_warning:
            box = self.layout.box()
            column = box.column(align=True)
            column.label(text="This is an experimental build of the FLIP Fluids addon", icon='ERROR')
            column.label(text="Not for production. Use at your own risk.", icon='ERROR')
            column.label(text="Please read before using:", icon='ERROR')
            column.operator(
                    "wm.url_open", 
                    text="Experimental Builds", 
                    icon="WORLD"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Experimental-Builds"

        is_saved = bool(bpy.data.filepath)
        if not is_saved and obj.flip_fluid.is_domain():
            hprops = context.scene.flip_fluid_helper
            box = self.layout.box()
            row = box.row(align=True)
            row.prop(hprops, "unsaved_blend_file_tooltip", icon="ERROR", emboss=False, text="")
            row = row.row(align=True)
            row.alert = True
            row.label(text="Unsaved File")
            row = row.row(align=True)
            row.alert = False
            row.operator("flip_fluid_operators.helper_save_blend_file", icon='FILE_TICK', text="Save")


    else:
        if not installation_utils.is_installation_complete():
            column_right.operator(
                        "flip_fluid_operators.flip_fluid_add", 
                        text="FLIP Fluid", 
                        icon='ERROR'
                        )
        else:
            use_custom_icon = True
            icon = context.scene.flip_fluid.get_logo_icon()
            if use_custom_icon and icon is not None:
                column_right.operator(
                        "flip_fluid_operators.flip_fluid_add", 
                        text="FLIP Fluid", 
                        icon_value=context.scene.flip_fluid.get_logo_icon().icon_id
                        )
            else:
                column_right.operator(
                        "flip_fluid_operators.flip_fluid_add", 
                        text="FLIP Fluid", 
                        icon='MOD_FLUIDSIM'
                        )

    if not installation_utils.is_installation_complete():
        box = self.layout.box()
        box.label(text="IMPORTANT: Blender restart required", icon="ERROR")
        box.label(text="Please restart Blender to complete")
        box.label(text="installation of the FLIP Fluids add-on.")


def register():
    none_ui.register()
    fluid_ui.register()
    obstacle_ui.register()
    inflow_ui.register()
    outflow_ui.register()
    force_field_ui.register()
    domain_ui.register()
    cache_object_ui.register()
    helper_ui.register()

    bpy.types.PHYSICS_PT_add.append(append_to_PHYSICS_PT_add_panel)


def unregister():
    none_ui.unregister()
    fluid_ui.unregister()
    obstacle_ui.unregister()
    inflow_ui.unregister()
    outflow_ui.unregister()
    force_field_ui.unregister()
    domain_ui.unregister()
    cache_object_ui.unregister()
    helper_ui.unregister()
        
    bpy.types.PHYSICS_PT_add.remove(append_to_PHYSICS_PT_add_panel)
