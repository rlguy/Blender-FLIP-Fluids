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

from bpy.props import (
        BoolProperty,
        StringProperty,
        FloatProperty,
        CollectionProperty,
        EnumProperty
        )

from ..ui import helper_ui
from ..utils import version_compatibility_utils as vcu


class FLIPFluidGPUDevice(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    name = StringProperty(); exec(conv("name"))
    description = StringProperty(); exec(conv("description"))
    score = FloatProperty(); exec(conv("score"))


class FLIPFluidAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__.split(".")[0]

    enable_helper = BoolProperty(
                name="Enable Helper Toolbox",
                description="Enable the FLIP Fluid helper menu in the 3D view toolbox."
                    " This menu contains operators to help with workflow and simulation setup",
                default=True,
                update=lambda self, context: self._update_enable_helper(context),
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("enable_helper"))

    beginner_friendly_mode = BoolProperty(
                name="Beginner Friendly Mode",
                description="Beginner friendly mode will show only the most important settings"
                    " and hide more advanced settings that are not as commonly used in basic"
                    " simulations. Enabling this will simplify the UI and help you focus on the"
                    " simulation settings that matter the most while you learn. This setting is"
                    " also available from the FLIP Fluids toolbox menu",
                default=False,
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("beginner_friendly_mode"))

    selected_gpu_device = EnumProperty(
                name="GPU Compute Device",
                description="Device that will be used for GPU acceleration features",
                items=lambda self, context=None: self._get_gpu_device_enums(context),
                )
    exec(vcu.convert_attribute_to_28("selected_gpu_device"))

    gpu_devices = CollectionProperty(type=FLIPFluidGPUDevice)
    exec(vcu.convert_attribute_to_28("gpu_devices"))

    is_gpu_devices_initialized = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("is_gpu_devices_initialized"))


    def _update_enable_helper(self, context):
        if self.enable_helper:
            try:
                helper_ui.register()
            except:
                pass
        else:
            try:
                helper_ui.unregister()
            except:
                pass


    def draw(self, context):
        column = self.layout.column(align=True)

        split = column.split()
        column_left = split.column(align=True)
        column_right = split.column()

        helper_column = column_left.column()
        helper_column.prop(self, "beginner_friendly_mode")
        helper_column.prop(self, "enable_helper")
        helper_column.separator()
        helper_column.separator()

        # These operators need to be reworked to support both 2.79 and 2.80
        """
        column_left.label(text="User Settings:")
        column_left.operator("flip_fluid_operators.preferences_import_user_data", icon="IMPORT")
        column_left.operator("flip_fluid_operators.preferences_export_user_data", icon="EXPORT")
        column_left.separator()
        column_left.separator()
        """

        column_left.label(text="Info and Links:")
        column_left.operator(
                "wm.url_open", 
                text="Frequently Asked Questions", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions"
        column_left.operator(
                "wm.url_open", 
                text="Scene Troubleshooting", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting"
        column_left.operator(
                "wm.url_open", 
                text="Tutorials and Learning Resources", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Video-Learning-Series"

        column_left.separator()
        row = column_left.row(align=True)
        row.operator(
                "wm.url_open", 
                text="Facebook", 
            ).url = "https://www.facebook.com/FLIPFluids"
        row.operator(
                "wm.url_open", 
                text="Twitter", 
            ).url = "https://twitter.com/flipfluids"
        row.operator(
                "wm.url_open", 
                text="Instagram", 
            ).url = "https://www.instagram.com/flip.fluids/"
        row.operator(
                "wm.url_open", 
                text="YouTube", 
            ).url = "https://www.youtube.com/channel/UCJlVTm456gRwxt86vfGvyRg"

        column_left.separator()
        column_left.operator(
                "flip_fluid_operators.check_for_updates", 
                text="Check for Updates", 
                icon="WORLD"
            )
        column_left.separator()


    def _get_gpu_device_enums(self, context=None):
        device_enums = []
        for d in self.gpu_devices:
            device_enums.append((d.name, d.name, d.description))
        return device_enums



def load_post():
    id_name = __name__.split(".")[0]
    preferences = vcu.get_blender_preferences(bpy.context).addons[id_name].preferences
    if not preferences.enable_helper:
        helper_ui.unregister()


def register():
    bpy.utils.register_class(FLIPFluidGPUDevice)
    bpy.utils.register_class(FLIPFluidAddonPreferences)


def unregister():
    bpy.utils.unregister_class(FLIPFluidGPUDevice)
    bpy.utils.unregister_class(FLIPFluidAddonPreferences)
