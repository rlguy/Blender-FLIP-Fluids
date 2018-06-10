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

from bpy.props import (
        BoolProperty,
        StringProperty,
        FloatProperty,
        CollectionProperty,
        EnumProperty
        )

from ..ui import helper_ui


class FLIPFluidGPUDevice(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.name = StringProperty()
        cls.description = StringProperty()
        cls.score = FloatProperty()


    @classmethod
    def unregister(cls):
        pass


class FLIPFluidAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__.split(".")[0]

    enable_helper = BoolProperty(
                name="Enable Helper Toolbox",
                description="Enable the FLIP Fluid helper menu in the 3D view toolbox."
                    " This menu contains operators to help with workflow and simulation setup.",
                default=True,
                update=lambda self, context: self._update_enable_helper(context),
                options={'HIDDEN'},
                )
    selected_gpu_device = EnumProperty(
                name="GPU Compute Device",
                description="Device that will be used for GPU acceleration features",
                items=lambda self, context=None: self._get_gpu_device_enums(context),
                )

    gpu_devices = CollectionProperty(type=FLIPFluidGPUDevice)
    is_gpu_devices_initialized = BoolProperty(False)


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

        column_left.prop(self, "enable_helper")
        column_left.separator()
        column_left.separator()

        column_left.label("GPU Compute Device:")
        if self.is_gpu_devices_initialized:
            column_left.operator(
                "flip_fluid_operators.preferences_find_gpu_devices", 
                text="Refresh GPU Device List", 
                icon="FILE_REFRESH"
            )
        else:
            column_left.operator(
                "flip_fluid_operators.preferences_find_gpu_devices", 
                text="Search for GPU Devices", 
                icon="VIEWZOOM"
            )

        gpu_box = column_left.box()
        if not self.is_gpu_devices_initialized:
            gpu_box.label("Click 'Search for GPU Devices' to initialize device list...")
        else:
            if len(self.gpu_devices) == 1:
                gpu_box.label(str(len(self.gpu_devices)) + " device found:")
            else:
                gpu_box.label(str(len(self.gpu_devices)) + " devices found:")

        if len(self.gpu_devices) > 0:
            gpu_box.prop(self, "selected_gpu_device", expand=True)

        column_left.separator()
        column_left.separator()

        column_left.label("User Settings:")
        column_left.operator("flip_fluid_operators.preferences_import_user_data", icon="IMPORT")
        column_left.operator("flip_fluid_operators.preferences_export_user_data", icon="EXPORT")
        column_left.separator()


    def _get_gpu_device_enums(self, context=None):
        device_enums = []
        for d in self.gpu_devices:
            device_enums.append((d.name, d.name, d.description))
        return device_enums



def load_post():
    id_name = __name__.split(".")[0]
    preferences = bpy.context.user_preferences.addons[id_name].preferences
    if not preferences.enable_helper:
        helper_ui.unregister()


def register():
    bpy.utils.register_class(FLIPFluidGPUDevice)
    bpy.utils.register_class(FLIPFluidAddonPreferences)


def unregister():
    bpy.utils.unregister_class(FLIPFluidGPUDevice)
    bpy.utils.unregister_class(FLIPFluidAddonPreferences)
