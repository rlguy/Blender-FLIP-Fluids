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
from ..utils import version_compatibility_utils as vcu


class DomainPresetsProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    enable_presets = BoolProperty(
            name="Enable Presets",
            description="Enable functionality to apply fluid presets",
            default=False,
            update=lambda self, context: self._update_enable_presets(context),
            ); exec(conv("enable_presets"))
    current_package = EnumProperty(
            name="Package",
            description="Preset package",
            items=preset_library.get_all_package_enums,
            update=lambda self, context: self._update_current_package(context),
            ); exec(conv("current_package"))
    current_preset = EnumProperty(
            items=preset_library.get_current_package_preset_enums,
            name="Preset",
            description="Fluid Preset",
            update=lambda self, context: self._update_current_preset(context),
            ); exec(conv("current_preset"))
    preview_preset = BoolProperty(
            name="Preview",
            description="Automatically assign preset on change (without"
                " needing to add to the preset stack)",
            default=False,
            update=lambda self, context: self._update_preview_preset(context),
            ); exec(conv("preview_preset"))
    new_package_settings = PointerProperty(
            name="New Package Settings",
            description="",
            type=preset_properties.NewPresetPackageSettings,
            ); exec(conv("new_package_settings"))
    delete_package_settings = PointerProperty(
            name="Delete Package Settings",
            description="",
            type=preset_properties.DeletePresetPackageSettings,
            ); exec(conv("delete_package_settings"))
    new_preset_settings = PointerProperty(
            name="New Preset Settings",
            description="",
            type=preset_properties.NewPresetSettings,
            ); exec(conv("new_preset_settings"))
    delete_preset_settings = PointerProperty(
            name="Delete Preset Settings",
            description="",
            type=preset_properties.DeletePresetSettings,
            ); exec(conv("delete_preset_settings"))
    edit_preset_settings = PointerProperty(
            name="Edit Preset Settings",
            description="",
            type=preset_properties.EditPresetSettings,
            ); exec(conv("edit_preset_settings"))
    display_preset_settings = PointerProperty(
            name="Display Preset Settings",
            description="",
            type=preset_properties.DisplayPresetInfoSettings,
            ); exec(conv("display_preset_settings"))
    export_package_settings = PointerProperty(
            name="Export Package Settings",
            description="",
            type=preset_properties.ExportPresetPackageSettings,
            ); exec(conv("export_package_settings"))
    import_package_settings = PointerProperty(
            name="Import Package Settings",
            description="",
            type=preset_properties.ImportPresetPackageSettings,
            ); exec(conv("import_package_settings"))
    preset_stack = PointerProperty(
            name="Flip Fluid Preset Stack",
            description="",
            type=flip_fluid_preset_stack.FlipFluidPresetStack,
            ); exec(conv("preset_stack"))

    preset_manager_expanded = BoolProperty(default=False); exec(conv("preset_manager_expanded"))
    deprecated_presets_disabled_on_load = BoolProperty(default=False); exec(conv("deprecated_presets_disabled_on_load"))


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
        self._check_presets_disable_on_load()


    def check_preset_enums(self):
        # Avoids blank package/preset enums if package or preset is missing
        current_preset = self.current_preset
        try:
            self.current_package = self.current_package
        except:
            enums = preset_library.get_all_package_enums(self, bpy.context)
            self.current_package = enums[0][0]

        try:
            # preset does not exist in this addon installation
            self.current_preset = current_preset
        except:
            self.current_preset = 'PRESET_NONE'


    def _check_presets_disable_on_load(self):
        if self.deprecated_presets_disabled_on_load:
            return
        self.enable_presets = False
        self.deprecated_presets_disabled_on_load = True


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