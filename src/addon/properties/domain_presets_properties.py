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

import bpy, os
from bpy.props import (
        BoolProperty,
        EnumProperty,
        StringProperty,
        PointerProperty
        )

from . import preset_properties
from .. import types
from ..presets import preset_library
from ..objects import flip_fluid_preset_stack


class DomainPresetsProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.enable_presets = BoolProperty(
                name="Enable Presets",
                description="Enable functionality to apply fluid presets",
                default=False,
                update=lambda self, context: self._update_enable_presets(context),
                )
        cls.current_package = EnumProperty(
                name="Package",
                description="Preset package",
                items=preset_library.get_all_package_enums,
                update=lambda self, context: self._update_current_package(context),
                )
        cls.current_preset = EnumProperty(
                items=preset_library.get_current_package_preset_enums,
                name="Preset",
                description="Fluid Preset",
                update=lambda self, context: self._update_current_preset(context),
                )
        cls.preview_preset = BoolProperty(
                name="Preview",
                description="Preview the effects of the selected preset before"
                    " adding to the preset stack",
                default=False,
                update=lambda self, context: self._update_preview_preset(context),
                )
        cls.new_package_settings = PointerProperty(
                name="New Package Settings",
                description="",
                type=preset_properties.NewPresetPackageSettings,
                )
        cls.delete_package_settings = PointerProperty(
                name="Delete Package Settings",
                description="",
                type=preset_properties.DeletePresetPackageSettings,
                )
        cls.new_preset_settings = PointerProperty(
                name="New Preset Settings",
                description="",
                type=preset_properties.NewPresetSettings,
                )
        cls.delete_preset_settings = PointerProperty(
                name="Delete Preset Settings",
                description="",
                type=preset_properties.DeletePresetSettings,
                )
        cls.edit_preset_settings = PointerProperty(
                name="Edit Preset Settings",
                description="",
                type=preset_properties.EditPresetSettings,
                )
        cls.display_preset_settings = PointerProperty(
                name="Display Preset Settings",
                description="",
                type=preset_properties.DisplayPresetInfoSettings,
                )
        cls.export_package_settings = PointerProperty(
                name="Export Package Settings",
                description="",
                type=preset_properties.ExportPresetPackageSettings,
                )
        cls.import_package_settings = PointerProperty(
                name="Import Package Settings",
                description="",
                type=preset_properties.ImportPresetPackageSettings,
                )
        cls.preset_stack = PointerProperty(
                name="Flip Fluid Preset Stack",
                description="",
                type=flip_fluid_preset_stack.FlipFluidPresetStack,
                )

        cls.preset_manager_expanded = BoolProperty(default=False)


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        pass


    def initialize(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return
        preset_library.initialize()
        preset_library.load_default_settings(dprops)
        self._initialize_default_current_package()


    def load_post(self):
        self.preset_stack.validate_stack()
        self.check_preset_enums()


    def check_preset_enums(self):
        # Avoids blank package/preset enums if package or preset is missing
        current_preset = self.current_preset
        self.current_package = self.current_package
        self.current_preset = current_preset


    def _initialize_default_current_package(self):
        default_name = "Basic Fluids"
        enums = preset_library.get_all_package_enums(self, bpy.context)
        for e in enums:
            if e[1] == default_name:
                self.current_package = e[0]
                break

        # Prevents UI from displaying blank enum property
        try:
            self.current_package = self.current_package
        except:
            pass


    def _update_current_package(self, context):
        preset_enums = preset_library.get_current_package_preset_enums(self, context)
        package_info = preset_library.package_identifier_to_info(self.current_package)
        if len(preset_enums) > 1:
            if package_info['use_custom_icons']:
                for e in preset_enums:
                    if e[0] != 'PRESET_NONE':
                        self.current_preset = e[0]
                        break
            else:
                for e in reversed(preset_enums):
                    if e[0] != 'PRESET_NONE':
                        self.current_preset = e[0]
                        break
        else:
            self.current_preset = self.current_preset


    def _update_enable_presets(self, context):
        stack = self.preset_stack
        if self.enable_presets:
            stack.enable()
            if self.preview_preset:
                if not stack.is_preset_in_stack(self.current_preset):
                    stack.stage_preset(self.current_preset)
            else:
                stack.unstage_preset()
        else:
            stack.disable()


    def _update_current_preset(self, context):
        if not self.enable_presets or not self.preview_preset:
            return

        stack = self.preset_stack
        if not stack.is_preset_in_stack(self.current_preset):
            stack.stage_preset(self.current_preset)
        else:
            stack.unstage_preset()


    def _update_preview_preset(self, context):
        if not self.enable_presets:
            return

        stack = self.preset_stack
        if self.preview_preset and not stack.is_preset_in_stack(self.current_preset):
            stack.stage_preset(self.current_preset)
        else:
            stack.unstage_preset()


def register():
    bpy.utils.register_class(DomainPresetsProperties)


def unregister():
    bpy.utils.unregister_class(DomainPresetsProperties)