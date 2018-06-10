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

if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'none_ui',
        'fluid_ui',
        'obstacle_ui',
        'inflow_ui',
        'outflow_ui',
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
        domain_ui,
        cache_object_ui,
        helper_ui
        )


def append_to_PHYSICS_PT_add_panel(self, context):
    obj = context.scene.objects.active
    if not obj.type == 'MESH':
        return

    column = self.layout.column(align=True)
    split = column.split(percentage=0.5)
    column_left = split.column()
    column_right = split.column()

    if obj.flip_fluid.is_active:
        column_right.operator(
                "flip_fluid_operators.flip_fluid_remove", 
                 text="FLIP Fluid", 
                 icon='X'
                )
    else:
        icon = context.scene.flip_fluid.get_logo_icon()
        if icon is not None:
            # Icon needs to be reworked
            """
            column_right.operator(
                    "flip_fluid_operators.flip_fluid_add", 
                    text="FLIP Fluid", 
                    icon_value=context.scene.flip_fluid.get_logo_icon().icon_id
                    )
            """
            column_right.operator(
                    "flip_fluid_operators.flip_fluid_add", 
                    text="FLIP Fluid", 
                    icon='MOD_FLUIDSIM'
                    )
        else:
            column_right.operator(
                    "flip_fluid_operators.flip_fluid_add", 
                    text="FLIP Fluid", 
                    icon='MOD_FLUIDSIM'
                    )


def register():
    none_ui.register()
    fluid_ui.register()
    obstacle_ui.register()
    inflow_ui.register()
    outflow_ui.register()
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
    domain_ui.unregister()
    cache_object_ui.unregister()
    helper_ui.unregister()
    bpy.types.PHYSICS_PT_add.remove(append_to_PHYSICS_PT_add_panel)
