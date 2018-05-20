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

import bpy, json, os
from bpy.props import (
        BoolProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        CollectionProperty
        )

from ..presets import preset_library
from ..utils import preset_utils


class PresetStackProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.path = StringProperty()
        cls.value = StringProperty()
        cls.is_value_set = BoolProperty(default=False)


    @classmethod
    def unregister(cls):
        pass


    def get_value(self):
        if not self.is_value_set:
            return None
        return json.loads(self.value)


    def set_value(self, value):
        if value is None:
            self.value = ""
            self.is_value_set = False
            return
        self.value = json.dumps(value)
        self.is_value_set = True


class PresetStackMaterialInfo(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.preset_id = StringProperty()
        cls.loaded_id = StringProperty()


    @classmethod
    def unregister(cls):
        pass


class PresetStackElement(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.is_enabled = BoolProperty(
                name="Enabled",
                description="Enable effects of preset in the stack",
                default=True,
                update=lambda self, context: self._update_is_enabled(context),
                )

        cls.is_applied = BoolProperty(default=False)
        cls.is_active = BoolProperty(default=True)
        cls.identifier = StringProperty()
        cls.stack_uid = IntProperty(default=-1)
        cls.saved_properties = CollectionProperty(type=PresetStackProperty)
        cls.loaded_materials = CollectionProperty(type=PresetStackMaterialInfo)


    @classmethod
    def unregister(cls):
        pass


    def clear(self):
        self.property_unset("is_applied")
        self.property_unset("is_enabled")
        self.property_unset("is_active")
        self.property_unset("identifier")
        self.property_unset("stack_uid")
        self._clear_collection_property(self.saved_properties)
        self._clear_collection_property(self.loaded_materials)


    def save_properties(self, property_paths):
        self._clear_collection_property(self.saved_properties)
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        for path in property_paths:
            value = dprops.get_property_from_path(path)
            if value is None:
                continue
            saved_property = self.saved_properties.add()
            saved_property.path = path
            saved_property.set_value(value)


    def apply_saved_properties(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        for p in self.saved_properties:
            dprops.set_property_from_path(p.path, p.get_value())


    def apply_preset_properties(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        pinfo = preset_library.preset_identifier_to_info(self.identifier)

        self._load_preset_materials(pinfo)
        material_paths = preset_library.get_preset_material_paths()
        for p in pinfo['properties']:
            value = p['value']
            minfo = None
            if p['path'] in material_paths:
                minfo = self._get_loaded_material_info(value)
                if minfo is not None:
                    value = minfo.loaded_id
            dprops.set_property_from_path(p['path'], value)


    def unload_preset_materials(self):
        preset_utils.unload_preset_materials(self.loaded_materials)
        self._clear_collection_property(self.loaded_materials)


    def copy(self, other):
        self.is_applied = other.is_applied
        self.identifier = other.identifier
        for otherp in other.saved_properties:
            thisp = self.saved_properties.add()
            thisp.path = otherp.path
            thisp.set_value(otherp.get_value())
        for otherm in other.loaded_materials:
            thism = self.loaded_materials.add()
            thism.preset_id = otherm.preset_id
            thism.loaded_id = otherm.loaded_id


    def _get_loaded_material_info(self, preset_material_id):
        for minfo in self.loaded_materials:
            if minfo.preset_id == preset_material_id:
                return minfo
        return None


    def _load_preset_materials(self, preset_info):
        preset_utils.load_preset_materials(preset_info, self.loaded_materials)


    def _update_is_enabled(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        stack = dprops.presets.preset_stack
        for i,p in enumerate(stack.preset_stack):
            if p.stack_uid == self.stack_uid:
                if self.is_enabled:
                    stack.activate_preset(i)
                else:
                    stack.deactivate_preset(i)


    def _clear_collection_property(self, collection):
        num_items = len(collection)
        for i in range(num_items):
            collection.remove(0)


class FlipFluidPresetStack(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.is_enabled = BoolProperty(default=False)
        cls.staged_preset = PointerProperty(type=PresetStackElement)
        cls.is_preset_staged = BoolProperty(default=False)
        cls.preset_stack = CollectionProperty(type=PresetStackElement)


    @classmethod
    def unregister(cls):
        pass


    def enable(self):
        self.is_enabled = True
        self._apply_preset_stack()


    def disable(self):
        self.is_enabled = False
        self._unapply_preset_stack()


    def stage_preset(self, preset_id):
        if self.is_preset_staged and self.staged_preset.identifier == preset_id:
            return
        if self.is_preset_staged:
            self.unstage_preset()
        if preset_id == 'PRESET_NONE':
            return

        self.staged_preset.identifier = preset_id
        self._apply_preset(self.staged_preset)
        self.is_preset_staged = True


    def unstage_preset(self):
        if not self.is_preset_staged:
            return

        self._unapply_preset(self.staged_preset)
        self.staged_preset.clear()
        self.is_preset_staged = False


    def add_staged_preset_to_stack(self):
        if not self.is_preset_staged:
            return
        uid = self._generate_stack_uid()

        p = self.preset_stack.add()
        p.copy(self.staged_preset)
        p.stack_uid = uid
        self.staged_preset.clear()
        self.is_preset_staged = False


    def remove_package_presets_from_stack(self, package_id):
        preset_enums = preset_library.get_package_preset_enums(self, bpy.context, package_id)
        preset_identifiers = []
        for e in preset_enums:
            if e[0] != 'PRESET_NONE':
                preset_identifiers.append(e[0])

        found_presets = False
        for pe in self.preset_stack:
            if pe.identifier in preset_identifiers:
                found_presets = True
                break
        if not found_presets:
            return

        self._unapply_preset_stack()
        for i in range(len(self.preset_stack) - 1, -1, -1):
            if self.preset_stack[i].identifier in preset_identifiers:
                self.preset_stack.remove(i)
        self._apply_preset_stack()


    def remove_preset_from_stack_by_identifier(self, preset_identifier):
        for idx,se in enumerate(self.preset_stack):
            if se.identifier == preset_identifier:
                self.remove_preset_from_stack(idx)
                return idx
        return -1


    def remove_preset_from_stack(self, stack_index):
        if stack_index < 0 or stack_index >= len(self.preset_stack):
            return
        self._unapply_preset_stack()
        self.preset_stack.remove(stack_index)
        self._apply_preset_stack()


    def apply_and_remove_preset_from_stack(self, stack_index):
        if stack_index < 0 or stack_index >= len(self.preset_stack):
            return
        p = self.preset_stack[stack_index]
        for minfo in p.loaded_materials:
            m = bpy.data.materials.get(minfo.loaded_id)
            if m is not None:
                m.flip_fluid.skip_preset_unload = True
        self.preset_stack.remove(stack_index)


    def move_preset_up_in_stack(self, stack_index):
        if stack_index <= 0 or stack_index >= len(self.preset_stack):
            return
        self._unapply_preset_stack()
        self.preset_stack.move(stack_index, stack_index - 1)
        self._apply_preset_stack()


    def move_preset_down_in_stack(self, stack_index):
        if stack_index < 0 or stack_index >= len(self.preset_stack) - 1:
            return
        self._unapply_preset_stack()
        self.preset_stack.move(stack_index, stack_index + 1)
        self._apply_preset_stack()


    def insert_preset_into_stack(self, preset_identifier, stack_index):
        #if stack_index < 0 or stack_index >= len(self.preset_stack) - 1:
        #    return
        self._unapply_preset_stack()
        self.stage_preset(preset_identifier)
        self.add_staged_preset_to_stack()
        self.preset_stack.move(len(self.preset_stack) - 1, stack_index)
        self._apply_preset_stack()


    def activate_preset(self, stack_index):
        if stack_index < 0 or stack_index >= len(self.preset_stack):
            return
        if self.preset_stack[stack_index].is_active:
            return
        self._unapply_preset_stack()
        self.preset_stack[stack_index].is_active = True
        self._apply_preset_stack()


    def deactivate_preset(self, stack_index):
        if stack_index < 0 or stack_index >= len(self.preset_stack):
            return
        if not self.preset_stack[stack_index].is_active:
            return
        self._unapply_preset_stack()
        self.preset_stack[stack_index].is_active = False
        self._apply_preset_stack()


    def is_preset_in_stack(self, preset_identifier):
        for pe in self.preset_stack:
            if pe.identifier == preset_identifier:
                return True
        return False


    def validate_stack(self):
        preset_info = preset_library.get_preset_info_list()
        valid_identifiers = [info['identifier'] for info in preset_info]
        for i in range(len(self.preset_stack) - 1, -1, -1):
            pe = self.preset_stack[i]
            if pe.identifier not in valid_identifiers:
                errmsg = ("Preset Stack Warning: preset <" + pe.identifier + 
                          "> not found on system, removing from stack")
                print(errmsg)
                self.preset_stack.remove(i)


    def _apply_preset(self, stack_element):
        pinfo = preset_library.preset_identifier_to_info(stack_element.identifier)

        property_paths = []
        for p in pinfo['properties']:
            property_paths.append(p['path'])
        stack_element.save_properties(property_paths)
        stack_element.apply_preset_properties()

        stack_element.is_applied = True


    def _unapply_preset(self, stack_element):
        stack_element.apply_saved_properties()

        pid = stack_element.identifier
        preset_count = 0
        if self.is_preset_staged and self.staged_preset.identifier == pid:
            if self.staged_preset.is_applied:
                preset_count +=1
        for p in self.preset_stack:
            if p.identifier == pid and p.is_applied:
                preset_count += 1
        if preset_count == 1:
            stack_element.unload_preset_materials()

        stack_element.is_applied = False


    def _apply_preset_stack(self):
        for p in self.preset_stack:
            if not p.is_applied and p.is_active:
                self._apply_preset(p)
        if self.is_preset_staged and not self.staged_preset.is_applied:
            self._apply_preset(self.staged_preset)


    def _unapply_preset_stack(self):
        if self.is_preset_staged and self.staged_preset.is_applied:
            self._unapply_preset(self.staged_preset)
        for p in reversed(self.preset_stack):
            if p.is_applied and p.is_active:
                self._unapply_preset(p)

    def _generate_stack_uid(self):
        ids = [x.stack_uid for x in self.preset_stack]
        for i in range(0, 1000000):
            if not i in ids:
                return i
        return -1


def register():
    bpy.utils.register_class(PresetStackProperty)
    bpy.utils.register_class(PresetStackMaterialInfo)
    bpy.utils.register_class(PresetStackElement)
    bpy.utils.register_class(FlipFluidPresetStack)


def unregister():
    bpy.utils.unregister_class(PresetStackProperty)
    bpy.utils.unregister_class(PresetStackMaterialInfo)
    bpy.utils.unregister_class(PresetStackElement)
    bpy.utils.unregister_class(FlipFluidPresetStack)
