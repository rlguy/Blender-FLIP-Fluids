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

import bpy, string, re, os, json
from mathutils import Vector
from bpy.props import (
        IntProperty,
        FloatProperty,
        BoolProperty,
        StringProperty,
        EnumProperty,
        PointerProperty,
        CollectionProperty
        )

from .. import types
from ..presets import preset_library
from ..utils import ui_utils, preset_utils
from ..utils import version_compatibility_utils as vcu
from ..materials import material_library


DUMMY_DOMAIN_OBJECT = None


class PresetRegistryProperty(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    path = StringProperty(); exec(conv("path"))
    label = StringProperty(); exec(conv("label"))
    is_key = BoolProperty(); exec(conv("is_key"))
    key_path = StringProperty(); exec(conv("key_path"))
    key_value = StringProperty(); exec(conv("key_value"))
    group_id = IntProperty(); exec(conv("group_id"))


class PresetRegistry(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    properties = CollectionProperty(type=PresetRegistryProperty); exec(conv("properties"))


    def clear(self):
        num_items = len(self.properties)
        for i in range(num_items):
            self.properties.remove(0)


    def add_property(self, path, label, is_key=False, key_path="", key_value="", group_id=0):
        p = self.properties.add()
        p.path = path
        p.label = label
        p.is_key = is_key
        p.key_path = key_path
        p.key_value = key_value
        p.group_id = group_id


    def get_property_paths(self):
        paths = []
        for p in self.properties:
            paths.append(p.path)
        return paths


class NewPresetPackageSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    name = StringProperty(
            name="",
            description="Preset package name",
            default="New Package"
            ); exec(conv("name"))
    author = StringProperty(
            name="",
            description="Preset package author (optional)",
            default=""
            ); exec(conv("author"))
    description = StringProperty(
            name="",
            description="Preset package description (optional)",
            default=""
            ); exec(conv("description"))
    use_custom_icons = BoolProperty(
            name="",
            description="Use custom icon images for package presets. "
                "Images should be 256x256 resolution and PNG format",
            default=False
            ); exec(conv("use_custom_icons"))


    def reset(self):
        self.property_unset('name')
        self.property_unset('author')
        self.property_unset('description')
        self.property_unset('use_custom_icons')


    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['author'] = self.author
        d['description'] = self.description
        d['use_custom_icons'] = self.use_custom_icons
        return d


class DeletePresetPackageSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    package = EnumProperty(
            name="Remove Package",
            description="Select a package to remove",
            items=preset_library.get_deletable_package_enums,
            ); exec(conv("package"))


    def reset(self):
        self.package = 'DELETE_PACKAGE_NONE'


class PresetPropertyUI(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    path = StringProperty(default=""); exec(conv("path"))
    label = StringProperty(default=""); exec(conv("label"))
    value = StringProperty(default=""); exec(conv("value"))
    enabled = BoolProperty(default=True); exec(conv("enabled"))
    dummy_prop = BoolProperty(default=True); exec(conv("dummy_prop"))


    def set_value(self, value):
        self.value = json.dumps(value)


    def get_value(self):
        if self.value == "":
            return None
        return json.loads(self.value)


class PresetPropertiesUI(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    simulation = CollectionProperty(type=PresetPropertyUI); exec(conv("simulation"))
    render = CollectionProperty(type=PresetPropertyUI); exec(conv("render"))
    surface = CollectionProperty(type=PresetPropertyUI); exec(conv("surface"))
    whitewater = CollectionProperty(type=PresetPropertyUI); exec(conv("whitewater"))
    world = CollectionProperty(type=PresetPropertyUI); exec(conv("world"))
    materials = CollectionProperty(type=PresetPropertyUI); exec(conv("materials"))
    advanced = CollectionProperty(type=PresetPropertyUI); exec(conv("advanced"))
    debug = CollectionProperty(type=PresetPropertyUI); exec(conv("debug"))
    stats = CollectionProperty(type=PresetPropertyUI); exec(conv("stats"))
    is_initialized = BoolProperty(default=False); exec(conv("is_initialized"))


    def initialize(self):
        if not self.is_initialized:
            self.reset()
        self.is_initialized = True


    def enable_all(self, enable=True):
        self._enable_collection("simulation", enable)
        self._enable_collection("render", enable)
        self._enable_collection("surface", enable)
        self._enable_collection("whitewater", enable)
        self._enable_collection("world", enable)
        self._enable_collection("materials", enable)
        self._enable_collection("advanced", enable)
        self._enable_collection("debug", enable)
        self._enable_collection("stats", enable)


    def disable_all(self, disable=True):
        self.enable_all(not disable)


    def enable_collection(self, collection_id, enable=True):
        self._enable_collection(collection_id, enable)


    def disable_collection(self, collection_id, disable=True):
        self.enable_collection(collection_id, not disable)


    def enable_all_auto(self):
        diff_paths = self._get_diff_property_paths()
        diff_path_dict = {x: True for x in diff_paths}
        props = self.get_all_properties()
        for p in props:
            p.enabled = p.path in diff_path_dict


    def enable_collection_auto(self, collection_id):
        diff_paths = self._get_diff_property_paths()
        diff_path_dict = {x: True for x in diff_paths}
        props = getattr(self, collection_id)
        for p in props:
            p.enabled = p.path in diff_path_dict


    def get_all_properties(self):
        props = []
        for p in self.simulation:
            props.append(p)
        for p in self.render:
            props.append(p)
        for p in self.surface:
            props.append(p)
        for p in self.whitewater:
            props.append(p)
        for p in self.world:
            props.append(p)
        for p in self.materials:
            props.append(p)
        for p in self.advanced:
            props.append(p)
        for p in self.debug:
            props.append(p)
        for p in self.stats:
            props.append(p)
        return props


    def save_property_values(self, dprops):
        property_paths = dprops.property_registry.get_property_paths()
        property_value_dict = {}
        for p in property_paths:
            value = dprops.get_property_from_path(p)
            if value is not None:
                property_value_dict[p] = value

        ui_properties = self.get_all_properties()
        for uip in ui_properties:
            if uip.path in property_value_dict:
                uip.set_value(property_value_dict[uip.path])


    def reset(self):
        self.clear()

        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        for prop in dprops.property_registry.properties:
            path_split = prop.path.split('.')
            collection = getattr(self, path_split[1])

            ui_element = collection.add()
            ui_element.path = prop.path
            ui_element.label = prop.label
            ui_element.enabled = True


    def clear(self):
        self._clear_collection_property(self.simulation)
        self._clear_collection_property(self.render)
        self._clear_collection_property(self.surface)
        self._clear_collection_property(self.whitewater)
        self._clear_collection_property(self.world)
        self._clear_collection_property(self.materials)
        self._clear_collection_property(self.advanced)
        self._clear_collection_property(self.debug)
        self._clear_collection_property(self.stats)


    def generate_column_partition_chunks(self, collection_ids):
        chunks = []
        if 'simulation' in collection_ids:
            chunks.append({'label': "FLIP Fluid Simulation", 'collection': self.simulation})
        if 'render' in collection_ids:
            chunks.append({'label': "FLIP Fluid Display Settings", 'collection': self.render})
        if 'surface' in collection_ids:
            chunks.append({'label': "FLIP Fluid Surface", 'collection': self.surface})
        if 'whitewater' in collection_ids:
            chunks.append({'label': "FLIP Fluid Whitewater", 'collection': self.whitewater})
        if 'world' in collection_ids:
            chunks.append({'label': "FLIP Fluid World", 'collection': self.world})
        if 'materials' in collection_ids:
            chunks.append({'label': "FLIP Fluid Materials", 'collection': self.materials})
        if 'advanced' in collection_ids:
            chunks.append({'label': "FLIP Fluid Advanced", 'collection': self.advanced})
        if 'debug' in collection_ids:
            chunks.append({'label': "FLIP Fluid Debug", 'collection': self.debug})
        if 'stats' in collection_ids:
            chunks.append({'label': "FLIP Fluid Stats", 'collection': self.stats})

        for c in chunks:
             c['size'] = len(c['collection'])

        sub_chunks = []
        min_sub_chunk_size = 5
        for index, c in enumerate(chunks):
            num_split = c['size'] // min_sub_chunk_size
            num_split = max(num_split, 1)
            for i in range(num_split):
                label = c['label']
                is_continuation = False
                if i > 0:
                    label += " (continued...)"
                    is_continuation = True
                if num_split == 1:
                    size = c['size']
                else:
                    if i == 0:
                        size = c['size'] - (num_split - 1) * min_sub_chunk_size
                    else:
                        size = min_sub_chunk_size
                sc = {
                    'label': label,
                    'size': size,
                    'collection': c['collection'],
                    'is_continuation': is_continuation,
                    'id': index
                }
                sub_chunks.append(sc)
        return sub_chunks


    def generate_columns3(self, collection_id, property_registry):
        collection, label = [], "None"
        if collection_id == 'simulation':
            collection, label = self.simulation, "FLIP Fluid Simulation"
        if collection_id == 'render':
            collection, label = self.render,     "FLIP Fluid Display Settings"
        if collection_id == 'surface':
            collection, label = self.surface,    "FLIP Fluid Surface"
        if collection_id == 'whitewater':
            collection, label = self.whitewater, "FLIP Fluid Whitewater"
        if collection_id == 'world':
            collection, label = self.world,      "FLIP Fluid World"
        if collection_id == 'materials':
            collection, label = self.materials,  "FLIP Fluid Materials"
        if collection_id == 'advanced':
            collection, label = self.advanced,   "FLIP Fluid Advanced"
        if collection_id == 'debug':
            collection, label = self.debug,      "FLIP Fluid Debug"
        if collection_id == 'stats':
            collection, label = self.stats,      "FLIP Fluid Stats"


        path_to_group_id = {}
        for p in property_registry.properties:
            path_to_group_id[p.path] = p.group_id

        columns = [
            {'column_id': 0, 'label': label, 'collection': collection, 'properties': []},
            {'column_id': 1, 'label': label, 'collection': collection, 'properties': []},
            {'column_id': 2, 'label': label, 'collection': collection, 'properties': []},
        ]
        for uip in collection:
            group_id = path_to_group_id[uip.path]
            columns[group_id]['properties'].append(uip)

        return columns


    def _clear_collection_property(self, collection):
        num_items = len(collection)
        for i in range(num_items):
            collection.remove(0)


    def _enable_collection(self, collection_id, is_enabled):
        collection = getattr(self, collection_id)
        for p in collection:
            p.enabled = is_enabled


    def _is_different(self, value1, value2):
        eps = 1e-9
        if isinstance(value1, float):
            return abs(value1 - value2) > eps
        elif isinstance(value1, Vector):
            return (abs(value1[0] - value2[0]) > eps or 
                    abs(value1[1] - value2[1]) > eps or 
                    abs(value1[2] - value2[2]) > eps)
        else:
            return value1 != value2


    def _get_diff_property_paths(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        default_data = preset_library.get_system_default_preset_dict()
        path_to_default_value = {}
        for prop in default_data['properties']:
            path_to_default_value[prop['path']] = prop['value']

        property_paths = dprops.property_registry.get_property_paths()
        diff_paths = []
        for path in property_paths:
            if path not in path_to_default_value:
                continue
            v1 = dprops.get_property_from_path(path)
            v2 = path_to_default_value[path]
            if self._is_different(v1, v2):
                diff_paths.append(path)

        return diff_paths


class NewPresetSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    package = EnumProperty(
            name="Preset Package",
            description="Add preset to this package",
            items=preset_library.get_user_package_enums,
            ); exec(conv("package"))
    name = StringProperty(
            name="Name",
            description="Preset name",
            default="New Preset"
            ); exec(conv("name"))
    description = StringProperty(
            name="Description",
            description="Preset description (optional)",
            default=""
            ); exec(conv("description"))
    icon = StringProperty(
            name="Icon",
            description="Icons should be 256x256 resolution and in PNG format."
                " Images must be imported into the Blender UV/Image Editor before" 
                " they can be selected. Your menu edits will be saved if you close"
                " this popup",
            default="",
            update=lambda self, context=None: self._update_icon(context),
            ); exec(conv("icon"))
    display_icon = EnumProperty(
            name="Preset Icon",
            description="",
            items=lambda self, context=None: self._get_display_icon_enum(context),
            ); exec(conv("display_icon"))
    export_simulation = BoolProperty(
            name="Simulation",
            description="Export 'FLIP Fluid Simulation' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_simulation"))
    export_display = BoolProperty(
            name="Display Settings",
            description="Export 'FLIP Fluid Display Settings' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_display"))
    export_surface = BoolProperty(
            name="Surface",
            description="Export 'FLIP Fluid Surface' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_surface"))
    export_whitewater = BoolProperty(
            name="Whitewater",
            description="Export 'FLIP Fluid Whitewater' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_whitewater"))
    export_world = BoolProperty(
            name="World",
            description="Export 'FLIP Fluid World' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_world"))
    export_materials = BoolProperty(
            name="Materials",
            description="Export 'FLIP Fluid Materials' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_materials"))
    export_advanced = BoolProperty(
            name="Advanced",
            description="Export 'FLIP Fluid Advanced' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_advanced"))
    export_debug = BoolProperty(
            name="Debug",
            description="Export 'FLIP Fluid Debug' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_debug"))
    export_stats = BoolProperty(
            name="Stats",
            description="Export 'FLIP Fluid Stats' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_stats"))
    ui_sort = BoolProperty(
            name="Sort Attributes",
            description="Sort attributes by enabled/disabled",
            default=False,
    ); exec(conv("ui_sort"))
    current_display_panel = EnumProperty(
        name="Current Preset Display",
        description="Current preset panel to display",
        items=lambda self, context=None: self.get_preset_panel_selector_enums(context),
    ); exec(conv("current_display_panel"))


    ui_properties = PointerProperty(type=PresetPropertiesUI); exec(conv("ui_properties"))
    is_unedited = BoolProperty(default=True); exec(conv("is_unedited"))

    # If set to 'True', new preset menu will automatically select which
    # panels to export by comparing current property values to system devault
    # values. 
    # If set to 'False', new preset menu will start with a blank panel 
    # export selection.
    autoselect_exported_panels = BoolProperty(default=False); exec(conv("autoselect_exported_panels"))


    def initialize(self):
        self.ui_properties.initialize()
        if self.is_unedited:
            self._initialize_selected_package()
            self._initialize_export_settings()
            self.is_unedited = False


    def reset(self):
        self.property_unset('name')
        self.property_unset('description')
        self.property_unset('icon')
        self.property_unset('ui_sort')
        self.property_unset('is_unedited')
        self.ui_properties.reset()
        self._initialize_selected_package()
        self._initialize_export_settings()


    def get_export_identifier_from_collection(self, collection):
        uips = self.ui_properties
        collection_to_export_identifier = {
            uips.simulation: "export_simulation",
            uips.render:     "export_display",
            uips.surface:    "export_surface",
            uips.whitewater: "export_whitewater",
            uips.world:      "export_world",
            uips.materials:  "export_materials",
            uips.advanced:   "export_advanced",
            uips.debug:      "export_debug",
            uips.stats:      "export_stats",
        }
        return collection_to_export_identifier[collection]


    def get_collection_identifier_from_collection(self, collection):
        uips = self.ui_properties
        collection_to_collection_identifier = {
            uips.simulation: "simulation",
            uips.render:     "render",
            uips.surface:    "surface",
            uips.whitewater: "whitewater",
            uips.world:      "world",
            uips.materials:  "materials",
            uips.advanced:   "advanced",
            uips.debug:      "debug",
            uips.stats:      "stats",
        }
        return collection_to_collection_identifier[collection]


    def get_exported_ui_properties(self):
        exported_panels = {}
        if self.export_simulation:
            exported_panels["simulation"] = True
        if self.export_display:
            exported_panels["render"] = True
        if self.export_surface:
            exported_panels["surface"] = True
        if self.export_whitewater:
            exported_panels["whitewater"] = True
        if self.export_world:
            exported_panels["world"] = True
        if self.export_materials:
            exported_panels["materials"] = True
        if self.export_advanced:
            exported_panels["advanced"] = True
        if self.export_debug:
            exported_panels["debug"] = True
        if self.export_stats:
            exported_panels["stats"] = True

        all_props = self.ui_properties.get_all_properties()
        exported_props = []
        for p in all_props:
            if not p.enabled:
                continue
            split = p.path.split(".")
            if split[1] in exported_panels:
                exported_props.append(p)
        return exported_props


    def enable_all(self, enable=True):
        self.ui_properties.enable_all(enable)


    def disable_all(self, disable=True):
        self.enable_all(not disable)


    def enable_collection(self, collection_id, enable=True):
        self.ui_properties.enable_collection(collection_id, enable)


    def disable_collection(self, collection_id, disable=True):
        self.enable_collection(collection_id, not disable)


    def enable_all_auto(self):
        self.ui_properties.enable_all_auto()


    def enable_collection_auto(self, collection_id):
        self.ui_properties.enable_collection_auto(collection_id)


    def get_preset_panel_selector_enums(self, context=None):
        enums = []
        if self.export_simulation:
            enums.append(('simulation', "Simulation", "FLIP Fluid Simulation", 1))
        if self.export_display:
            enums.append(('render', "Display", "FLIP Fluid Display Settings", 2))
        if self.export_surface:
            enums.append(('surface', "Surface", "FLIP Fluid Surface", 3))
        if self.export_whitewater:
            enums.append(('whitewater', "Whitewater", "FLIP Fluid Whitewater", 4))
        if self.export_world:
            enums.append(('world', "World", "FLIP Fluid World", 5))
        if self.export_materials:
            enums.append(('materials', "Materials", "FLIP Fluid Materials", 6))
        if self.export_advanced:
            enums.append(('advanced', "Advanced", "FLIP Fluid Advanced", 7))
        if self.export_debug:
            enums.append(('debug', "Debug", "FLIP Fluid Debug", 8))
        if self.export_stats:
            enums.append(('stats', "Stats", "FLIP Fluid Stats", 9))

        if not enums:
            enums.append(('NONE', "None", "No panel to select", 0))
        return enums


    def to_dict(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        d = {}
        d["name"] = self.name
        d["description"] = self.description
        d["package"] = self.package
        d["icon"] = self.icon

        props = self.get_exported_ui_properties()
        d["properties"] = []
        for p in props:
            pd = {}
            pd["path"] = p.path
            pd["value"] = dprops.get_property_from_path(p.path)
            d["properties"].append(pd)
        return d


    def _check_current_display_panel(self, context=None):
        # Stops UI from drawing enum as unselected
        try:
            self.current_display_panel = self.current_display_panel
        except:
            self.current_display_panel = self.get_preset_panel_selector_enums()[0][0]


    def _initialize_selected_package(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        current_package = dprops.presets.current_package
        current_info = preset_library.package_identifier_to_info(current_package)
        if current_info['is_system_package']:
            user_packages = preset_library.get_user_package_info_list()
            if len(user_packages) == 0:
                preset_library.initialize_default_user_package()
                user_packages = preset_library.get_user_package_info_list()

            selected_package = None
            for info in user_packages:
                if info['is_default_user_package']:
                    selected_package = info['identifier']
                    break
            if not selected_package:
                selected_package = user_packages[0]['identifier']

            self.package = selected_package
        else:
            self.package = current_package


    def _is_different(self, value1, value2):
        eps = 1e-9
        if isinstance(value1, float):
            return abs(value1 - value2) > eps
        elif isinstance(value1, Vector):
            return (abs(value1[0] - value2[0]) > eps or 
                    abs(value1[1] - value2[1]) > eps or 
                    abs(value1[2] - value2[2]) > eps)
        else:
            return value1 != value2


    def _initialize_export_settings(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        enable_dict = {
                'simulation': False, 'render': False, 'surface': False, 'whitewater': False,
                'world': False, 'materials': False, 'advanced': False, 'debug': False, 'stats': False
            }

        if self.autoselect_exported_panels:
            default_data = preset_library.get_system_default_preset_dict()
            path_to_default_value = {}
            for prop in default_data['properties']:
                path_to_default_value[prop['path']] = prop['value']

            property_paths = dprops.property_registry.get_property_paths()
            diff_paths = []
            for path in property_paths:
                if path not in path_to_default_value:
                    continue
                v1 = dprops.get_property_from_path(path)
                v2 = path_to_default_value[path]
                if self._is_different(v1, v2):
                    diff_paths.append(path)

            for path in diff_paths:
                split = path.split('.')
                enable_dict[split[1]] = True

        self.export_simulation = enable_dict['simulation']
        self.export_display =    enable_dict['render']
        self.export_surface =    enable_dict['surface']
        self.export_whitewater = enable_dict['whitewater']
        self.export_world =      enable_dict['world']
        self.export_materials =  enable_dict['materials']
        self.export_advanced =   enable_dict['advanced']
        self.export_debug =      enable_dict['debug']
        self.export_stats =      enable_dict['stats']


    def _update_icon(self, context):
        package_info = preset_library.package_identifier_to_info(self.package)
        if package_info["use_custom_icons"]:
            img_icon = bpy.data.images.get(self.icon)
            if img_icon:
                self.display_icon = self.icon
                return
        self.display_icon = 'ICON_NONE'


    def _get_display_icon_enum(self, context=None):
        package_info = preset_library.package_identifier_to_info(self.package)
        if package_info["use_custom_icons"]:
            img_icon = bpy.data.images.get(self.icon)
            if img_icon:
                return [(self.icon, self.icon, "", img_icon.preview.icon_id, img_icon.preview.icon_id)]
        return [('ICON_NONE', "None", "No icon loaded...")]


class DeletePresetSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    package = EnumProperty(
            name="Package",
            description="Select preset package",
            items=preset_library.get_user_package_enums,
            ); exec(conv("package"))
    preset = EnumProperty(
            name="Remove Preset",
            description="Select a preset to remove",
            items=preset_library.get_deletable_preset_enums,
            ); exec(conv("preset"))


    def reset(self):
        self.preset = 'DELETE_PRESET_NONE'
        self._initialize_selected_package()


    def _initialize_selected_package(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        current_package = dprops.presets.current_package
        current_info = preset_library.package_identifier_to_info(current_package)
        if current_info['is_system_package']:
            user_packages = preset_library.get_user_package_info_list()
            if len(user_packages) == 0:
                preset_library.initialize_default_user_package()
                user_packages = preset_library.get_user_package_info_list()

            selected_package = None
            for info in user_packages:
                if info['is_default_user_package']:
                    selected_package = info['identifier']
                    break
            if not selected_package:
                selected_package = user_packages[0]['identifier']

            self.package = selected_package
        else:
            self.package = current_package


class ExportPresetPackageSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    package = EnumProperty(
            name="Export Package",
            description="Select a package to export",
            items=preset_library.get_exportable_package_enums,
            update=lambda self, context: self._initialize_export_filename(),
            ); exec(conv("package"))
    export_directory = StringProperty(
            name="",
            description="Preset package will be exported to this directory",
            default=vcu.get_blender_preferences_temporary_directory(), 
            subtype='DIR_PATH',
            ); exec(conv("export_directory"))
    export_filename = StringProperty(
            name="",
            description="Filename of exported package",
            default="",
            update=lambda self, context: self._initialize_export_filepath(),
            ); exec(conv("export_filename"))
    export_filepath = StringProperty(
            name="",
            description="",
            default="",
            subtype='FILE_PATH',
            ); exec(conv("export_filepath"))
    create_subdirectories = BoolProperty(
            name="Create Missing Subdirectories",
            description="Create missing subdirectories if export directory does not exist",
            default=True,
            ); exec(conv("create_subdirectories"))


    def reset(self):
        self.property_unset('package')
        self.property_unset('export_filename')
        self.property_unset('export_filepath')
        self.property_unset('create_subdirectories')


    def initialize(self):
        self._initialize_selected_package()
        self._initialize_export_filename()
        self._initialize_export_filepath()


    def _initialize_selected_package(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        current_package = dprops.presets.current_package
        info = preset_library.package_identifier_to_info(current_package)
        if not info:
            return

        if not info['is_system_package']:
            self.package = current_package
        else:
            self.package = 'EXPORT_PACKAGE_NONE'


    def _initialize_export_filename(self):
        if self.package == 'EXPORT_PACKAGE_NONE':
            return

        info = preset_library.package_identifier_to_info(self.package)
        name = info['name'].strip().replace(' ', '_')
        name = re.sub(r'[^\sa-zA-Z0-9_]', '', name).lower()
        if not name:
            name = "package.zip"
        if not name.endswith(".zip"):
            name += ".zip"
        self.export_filename = name


    def _initialize_export_filepath(self):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in self.export_filename if c in valid_chars)
        if not filename:
            filename = "package.zip"
        if not filename.endswith(".zip"):
            filename += ".zip"
        filepath = os.path.join(self.export_directory, filename)
        filepath = os.path.normpath(filepath)
        self.export_filepath = filepath


class MaterialPropertyInfo(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    preset_id = StringProperty(); exec(conv("preset_id"))
    loaded_id = StringProperty(); exec(conv("loaded_id"))
    is_owner = BoolProperty(default=False); exec(conv("is_owner"))


class DisplayPresetInfoSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    display_icon = EnumProperty(
            name="Preset Icon",
            description="",
            items=lambda self, context=None: self._get_display_icon_enum(context),
            ); exec(conv("display_icon"))
    current_display_panel = EnumProperty(
            name="Current Preset Display",
            description="Current preset panel to display",
            items=lambda self, context=None: self.get_preset_panel_selector_enums(context),
            update=lambda self, context: self._initialize_dummy_domain_values(),
            ); exec(conv("current_display_panel"))

    identifier = StringProperty(default=""); exec(conv("identifier"))
    ui_properties = PointerProperty(type=PresetPropertiesUI); exec(conv("ui_properties"))
    loaded_materials = CollectionProperty(type=MaterialPropertyInfo); exec(conv("loaded_materials"))


    def initialize(self):
        self.ui_properties.initialize()
        if self._get_display_icon_enum():
            # Stops UI from drawing enum as unselected
            try:
                self.display_icon = self.display_icon
            except:
                self.display_icon = self._get_display_icon_enum()[0][0]
        self._check_current_display_panel()

        global DUMMY_DOMAIN_OBJECT
        DUMMY_DOMAIN_OBJECT = preset_library.generate_dummy_domain_object()

        self._initialize_ui_properties()
        self._load_preset_materials()
        self._initialize_dummy_domain_values()


    def reinitialize_display_values(self):
        self._initialize_dummy_domain_values()


    def reset(self):
        self.ui_properties.reset()
        self._unload_preset_materials()
        global DUMMY_DOMAIN_OBJECT
        if DUMMY_DOMAIN_OBJECT is not None:
            preset_library.destroy_dummy_domain_object(DUMMY_DOMAIN_OBJECT)
            DUMMY_DOMAIN_OBJECT = None


    def get_dummy_domain_properties(self):
        global DUMMY_DOMAIN_OBJECT
        if DUMMY_DOMAIN_OBJECT is not None:
            return DUMMY_DOMAIN_OBJECT.flip_fluid.domain


    def get_preset_panel_selector_enums(self, context=None):
        info = preset_library.preset_identifier_to_info(self.identifier)
        property_paths = []
        for p in info['properties']:
            property_paths.append(p['path'])
        return ui_utils.get_domain_panel_enums_from_paths(property_paths)


    def _get_display_icon_enum(self, context=None):
        info = preset_library.preset_identifier_to_info(self.identifier)

        if "icon" in info:
            preset_icons = preset_library.get_custom_icons()
            icon_id = preset_icons.get(info['icon']).icon_id
            return [(self.identifier, info['name'], "", icon_id, info['uid'])]
        return []


    def _check_current_display_panel(self, context=None):
        # Stops UI from drawing enum as unselected
        try:
            self.current_display_panel = self.current_display_panel
        except:
            self.current_display_panel = self.get_preset_panel_selector_enums()[0][0]


    def _initialize_ui_properties(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        info = preset_library.preset_identifier_to_info(self.identifier)

        path_to_label = {}
        for p in dprops.property_registry.properties:
            path_to_label[p.path] = p.label

        uips = self.ui_properties
        uips.clear()
        for p in info['properties']:
            if not p['path'] in path_to_label:
                continue

            split = p['path'].split(".")
            collection = getattr(uips, split[1])
            ui_element = collection.add()
            ui_element.path = p['path']
            ui_element.label = path_to_label[p['path']]
            ui_element.enabled = True


    def _load_preset_materials(self):
        preset_info = preset_library.preset_identifier_to_info(self.identifier)
        preset_utils.load_preset_materials(preset_info, self.loaded_materials)


    def _unload_preset_materials(self):
        preset_utils.unload_preset_materials(self.loaded_materials)
        self._clear_collection_property(self.loaded_materials)


    def _get_loaded_material_id(self, preset_material_id):
        for minfo in self.loaded_materials:
            if minfo.preset_id == preset_material_id:
                return minfo.loaded_id
        return preset_material_id


    def _initialize_dummy_domain_values(self):
        info = preset_library.preset_identifier_to_info(self.identifier)

        dummy_props = self.get_dummy_domain_properties()
        if dummy_props is None:
            return

        material_paths = preset_library.get_preset_material_paths()
        for p in info['properties']:
            value = p['value']
            if p['path'] in material_paths:
                value = self._get_loaded_material_id(value)
            dummy_props.set_property_from_path(p['path'], value)


    def _clear_collection_property(self, collection):
        num_items = len(collection)
        for i in range(num_items):
            collection.remove(0)


class PresetProperty(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    path = StringProperty(); exec(conv("path"))
    value = StringProperty(); exec(conv("value"))


class PresetInfo(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    name = StringProperty(); exec(conv("name"))
    description = StringProperty(); exec(conv("description"))
    identifier = StringProperty(); exec(conv("identifier"))
    is_system_preset = BoolProperty(); exec(conv("is_system_preset"))
    uid = IntProperty(); exec(conv("uid"))
    icon_id = IntProperty(default=-1); exec(conv("icon_id"))
    material_blend = StringProperty(default=""); exec(conv("material_blend"))
    properties = CollectionProperty(type=PresetProperty); exec(conv("properties"))


class PresetPackageInfo(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    name = StringProperty(); exec(conv("name"))
    author = StringProperty(); exec(conv("author"))
    description = StringProperty(); exec(conv("description"))
    identifier = StringProperty(); exec(conv("identifier"))
    is_system_package = BoolProperty(); exec(conv("is_system_package"))
    is_default_user_package = BoolProperty(); exec(conv("is_default_user_package"))
    use_custom_icons = BoolProperty(); exec(conv("use_custom_icons"))
    uid = IntProperty(); exec(conv("uid"))
    presets = CollectionProperty(type=PresetInfo); exec(conv("presets"))


    @classmethod
    def register(cls):
        cls.previews = bpy.utils.previews.new()


    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.previews)


    def initialize(self, data):
        self.reset()

        self.name =                    data['name']
        self.author =                  data['author']
        self.description =             data['description']
        self.identifier =              data['identifier']
        self.is_system_package =       data['is_system_package']
        self.is_default_user_package = data['is_default_user_package']
        self.use_custom_icons =        data['use_custom_icons']
        self.uid =                     data['uid']

        for pinfo in data['presets']:
            preset = self.presets.add()
            preset.name =             pinfo['name']
            preset.description =      pinfo['description']
            preset.identifier =       pinfo['identifier']
            preset.is_system_preset = pinfo['is_system_preset']
            preset.uid =              pinfo['uid']
            for p in pinfo['properties']:
                prop = preset.properties.add()
                prop.path = p['path']
                prop.value = json.dumps(p['value'])

            if 'icon' in pinfo:
                preview = self.previews.load(pinfo['identifier'], pinfo['icon'], 'IMAGE')
                preset.icon_id = preview.icon_id

            if 'material_blend' in pinfo:
                preset.material_blend = pinfo['material_blend']


    def reset(self):
        self.previews.clear()
        num_items = len(self.presets)
        for i in range(num_items):
            self.presets.remove(0)


class ImportPresetPackageSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    package_filepath = StringProperty(
            name="",
            description="Package zip file",
            default="",
            ); exec(conv("package_filepath"))
    selected_preset = EnumProperty(
            name="Preset",
            description="Select a package preset to view details",
            items=lambda self, context=None: self.get_package_preset_enums(context),
            update=lambda self, context: self._update_selected_package(context),
            ); exec(conv("selected_preset"))
    display_icon = EnumProperty(
            name="Preset Icon",
            description="",
            items=lambda self, context=None: self._get_display_icon_enum(context),
            ); exec(conv("display_icon"))
    current_display_panel = EnumProperty(
            name="Current Preset Display",
            description="Current preset panel to display",
            items=lambda self, context=None: self.get_preset_panel_selector_enums(context),
            update=lambda self, context: self._initialize_dummy_domain_values(),
            ); exec(conv("current_display_panel"))

    ui_properties = PointerProperty(type=PresetPropertiesUI); exec(conv("ui_properties"))
    loaded_materials = CollectionProperty(type=MaterialPropertyInfo); exec(conv("loaded_materials"))
    package_info = PointerProperty(type=PresetPackageInfo); exec(conv("package_info"))


    def initialize(self, data):
        self.reset()
        self.package_info.initialize(data)

        self.ui_properties.initialize()
        self._check_enum_properties()

        global DUMMY_DOMAIN_OBJECT
        DUMMY_DOMAIN_OBJECT = preset_library.generate_dummy_domain_object()

        self._initialize_ui_properties()
        self._load_preset_materials()
        self._initialize_dummy_domain_values()


    def reinitialize_display_values(self):
        self._initialize_dummy_domain_values()


    def reset(self):
        self.ui_properties.reset()
        self._unload_preset_materials()
        global DUMMY_DOMAIN_OBJECT
        if DUMMY_DOMAIN_OBJECT is not None:
            preset_library.destroy_dummy_domain_object(DUMMY_DOMAIN_OBJECT)
            DUMMY_DOMAIN_OBJECT = None


    def get_dummy_domain_properties(self):
        global DUMMY_DOMAIN_OBJECT
        if DUMMY_DOMAIN_OBJECT is not None:
            return DUMMY_DOMAIN_OBJECT.flip_fluid.domain


    def get_preset_panel_selector_enums(self, context=None):
        if not self.package_info.presets:
            return

        info = self.get_selected_preset_info()
        property_paths = []
        for p in info.properties:
            property_paths.append(p.path)
        return ui_utils.get_domain_panel_enums_from_paths(property_paths)


    def get_selected_preset_info(self):
        for info in self.package_info.presets:
            if info.identifier == self.selected_preset:
                return info
        return None


    def get_package_preset_enums(self, context=None):
        enums = []
        for info in self.package_info.presets:
            icon = None
            if info.icon_id != -1:
                icon = info.icon_id
            if icon:
                e = (info.identifier, info.name, info.description, icon, info.uid)
            else:
                e = (info.identifier, info.name, info.description, info.uid)
            enums.append(e)

        if not enums:
            enums.append(('PRESET_NONE', "None", "", 0))
        return enums


    def _get_display_icon_enum(self, context=None):
        info = self.get_selected_preset_info()
        if info is not None and info.icon_id != -1:
            return [(info.identifier, info.name, "", info.icon_id, info.uid)]
        return []


    def _check_enum_properties(self, context=None):
        # Stops UI from drawing enum as unselected
        if self.get_preset_panel_selector_enums():
            self.current_display_panel = self.current_display_panel

        if self._get_display_icon_enum():
            self.display_icon = self.display_icon

        self.selected_preset = self.selected_preset


    def _update_selected_package(self, context=None):
        if self._get_display_icon_enum():
            self.display_icon = self.display_icon

        self._initialize_ui_properties()
        self._unload_preset_materials()
        self._load_preset_materials()
        self._initialize_dummy_domain_values()

        if self.get_preset_panel_selector_enums():
            self.current_display_panel = self.current_display_panel


    def _initialize_ui_properties(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        info = self.get_selected_preset_info()
        if info is None:
            return

        path_to_label = {}
        for p in dprops.property_registry.properties:
            path_to_label[p.path] = p.label

        uips = self.ui_properties
        uips.clear()
        for p in info.properties:
            if not p.path in path_to_label:
                continue

            split = p.path.split(".")
            collection = getattr(uips, split[1])
            ui_element = collection.add()
            ui_element.path = p.path
            ui_element.label = path_to_label[p.path]
            ui_element.enabled = True


    def _load_preset_materials(self):
        preset_info = self.get_selected_preset_info()
        preset_utils.load_preset_materials(preset_info, self.loaded_materials)


    def _unload_preset_materials(self):
        preset_utils.unload_preset_materials(self.loaded_materials)
        self._clear_collection_property(self.loaded_materials)


    def _get_loaded_material_id(self, preset_material_id):
        for minfo in self.loaded_materials:
            if minfo.preset_id == preset_material_id:
                return minfo.loaded_id
        return preset_material_id


    def _initialize_dummy_domain_values(self):
        dummy_props = self.get_dummy_domain_properties()
        if dummy_props is None:
            return

        info = self.get_selected_preset_info()
        if info is None:
            return

        material_paths = preset_library.get_preset_material_paths()
        for p in info.properties:
            value = json.loads(p.value)
            if p['path'] in material_paths:
                value = self._get_loaded_material_id(value)
            dummy_props.set_property_from_path(p.path, value)


    def _clear_collection_property(self, collection):
        num_items = len(collection)
        for i in range(num_items):
            collection.remove(0)


class EditPresetSettings(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    edit_package = EnumProperty(
            name="Preset Package",
            description="Edit preset from this package",
            items=preset_library.get_user_package_enums,
            update=lambda self, context=None: self._update_edit_package(context),
            ); exec(conv("edit_package"))
    edit_preset = EnumProperty(
            name="Edit Preset",
            description="Select a preset to edit",
            items=lambda self, context=None: preset_library.get_package_preset_enums(self, context, self.edit_package),
            update=lambda self, context=None: self._update_edit_preset(context),
            ); exec(conv("edit_preset"))
    package = EnumProperty(
            name="Preset Package",
            description="Move preset to this package",
            items=preset_library.get_user_package_enums,
            ); exec(conv("package"))
    name = StringProperty(
            name="Name",
            description="New preset name",
            default="New Preset"
            ); exec(conv("name"))
    description = StringProperty(
            name="Description",
            description="New preset description (optional)",
            default=""
            ); exec(conv("description"))
    icon = StringProperty(
            name="Icon",
            description="Icons should be 256x256 resolution and in PNG format."
                " Images must be imported into the Blender UV/Image Editor before" 
                " they can be selected. Your menu edits will be saved if you close"
                " this popup",
            default="",
            update=lambda self, context=None: self._update_icon(context),
            ); exec(conv("icon"))
    display_icon = display_icon = EnumProperty(
            name="Preset Icon",
            description="",
            items=lambda self, context=None: self._get_display_icon_enum(context),
            ); exec(conv("display_icon"))
    export_simulation = BoolProperty(
            name="Simulation",
            description="Export 'FLIP Fluid Simulation' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_simulation"))
    export_display = BoolProperty(
            name="Display Settings",
            description="Export 'FLIP Fluid Display Settings' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_display"))
    export_surface = BoolProperty(
            name="Surface",
            description="Export 'FLIP Fluid Surface' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_surface"))
    export_whitewater = BoolProperty(
            name="Whitewater",
            description="Export 'FLIP Fluid Whitewater' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_whitewater"))
    export_world = BoolProperty(
            name="World",
            description="Export 'FLIP Fluid World' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_world"))
    export_materials = BoolProperty(
            name="Materials",
            description="Export 'FLIP Fluid Materials' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_materials"))
    export_advanced = BoolProperty(
            name="Advanced",
            description="Export 'FLIP Fluid Advanced' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_advanced"))
    export_debug = BoolProperty(
            name="Debug",
            description="Export 'FLIP Fluid Debug' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_debug"))
    export_stats = BoolProperty(
            name="Stats",
            description="Export 'FLIP Fluid Stats' panel settings",
            default=False,
            update=lambda self, context=None: self._check_current_display_panel(context),
            ); exec(conv("export_stats"))
    ui_sort = BoolProperty(
            name="Sort Attributes",
            description="Sort attributes by enabled/disabled",
            default=False,
    ); exec(conv("ui_sort"))
    current_display_panel = EnumProperty(
        name="Current Preset Display",
        description="Current preset panel to display",
        items=lambda self, context=None: self.get_preset_panel_selector_enums(context),
    ); exec(conv("current_display_panel"))


    ui_properties = PointerProperty(type=PresetPropertiesUI); exec(conv("ui_properties"))
    loaded_icon_image_name = StringProperty(""); exec(conv("loaded_icon_image_name"))
    loaded_materials = CollectionProperty(type=MaterialPropertyInfo); exec(conv("loaded_materials"))
    is_unedited = BoolProperty(default=True); exec(conv("is_unedited"))


    def initialize(self):
        global DUMMY_DOMAIN_OBJECT
        DUMMY_DOMAIN_OBJECT = preset_library.generate_dummy_domain_object()

        if self.is_unedited and self.edit_preset != "PRESET_NONE":
            self.ui_properties.initialize()
            self._initialize_menu_settings()
            self.is_unedited = False

        if self.is_unedited:
            try:
                self.edit_package = self.edit_package
            except:
                self.edit_package = preset_library.get_all_package_enums(self, bpy.context)[0][0]

            self.edit_preset = self.edit_preset

        try:
            self.current_display_panel = self.current_display_panel
        except:
            self.current_display_panel = self.get_preset_panel_selector_enums(bpy.context)[0][0]

        self._load_preset_materials()
        self._load_icon_image()
        self._load_saved_property_values()
        self.icon = self.icon


    def reset_preset_edits(self):
        self.ui_properties.initialize()
        self._initialize_menu_settings()


    def unload(self):
        self._save_property_values()
        self._destroy_dummy_domain_object()
        self._unload_preset_materials()
        self._unload_icon_image()


    def get_dummy_domain_properties(self):
        global DUMMY_DOMAIN_OBJECT
        if DUMMY_DOMAIN_OBJECT is not None:
            return DUMMY_DOMAIN_OBJECT.flip_fluid.domain


    def reset(self):
        self.ui_properties.reset()
        self._unload_preset_materials()
        self._unload_icon_image()
        self._destroy_dummy_domain_object()
        self.property_unset('edit_package')
        self.property_unset('edit_preset')
        self.property_unset('name')
        self.property_unset('description')
        self.property_unset('icon')
        self.property_unset('ui_sort')
        self.property_unset('is_unedited')
        self.property_unset('loaded_icon_image_name')


    def get_export_identifier_from_collection(self, collection):
        uips = self.ui_properties
        collection_to_export_identifier = {
            uips.simulation: "export_simulation",
            uips.render:     "export_display",
            uips.surface:    "export_surface",
            uips.whitewater: "export_whitewater",
            uips.world:      "export_world",
            uips.materials:  "export_materials",
            uips.advanced:   "export_advanced",
            uips.debug:      "export_debug",
            uips.stats:      "export_stats",
        }
        return collection_to_export_identifier[collection]


    def get_collection_identifier_from_collection(self, collection):
        uips = self.ui_properties
        collection_to_collection_identifier = {
            uips.simulation: "simulation",
            uips.render:     "render",
            uips.surface:    "surface",
            uips.whitewater: "whitewater",
            uips.world:      "world",
            uips.materials:  "materials",
            uips.advanced:   "advanced",
            uips.debug:      "debug",
            uips.stats:      "stats",
        }
        return collection_to_collection_identifier[collection]


    def get_exported_ui_properties(self):
        exported_panels = {}
        if self.export_simulation:
            exported_panels["simulation"] = True
        if self.export_display:
            exported_panels["render"] = True
        if self.export_surface:
            exported_panels["surface"] = True
        if self.export_whitewater:
            exported_panels["whitewater"] = True
        if self.export_world:
            exported_panels["world"] = True
        if self.export_materials:
            exported_panels["materials"] = True
        if self.export_advanced:
            exported_panels["advanced"] = True
        if self.export_debug:
            exported_panels["debug"] = True
        if self.export_stats:
            exported_panels["stats"] = True

        all_props = self.ui_properties.get_all_properties()
        exported_props = []
        for p in all_props:
            if not p.enabled:
                continue
            split = p.path.split(".")
            if split[1] in exported_panels:
                exported_props.append(p)
        return exported_props


    def enable_all(self, enable=True):
        self.ui_properties.enable_all(enable)


    def disable_all(self, disable=True):
        self.enable_all(not disable)


    def enable_collection(self, collection_id, enable=True):
        self.ui_properties.enable_collection(collection_id, enable)


    def disable_collection(self, collection_id, disable=True):
        self.enable_collection(collection_id, not disable)


    def get_preset_panel_selector_enums(self, context=None):
        enums = []
        if self.export_simulation:
            enums.append(('simulation', "Simulation", "FLIP Fluid Simulation", 1))
        if self.export_display:
            enums.append(('render', "Display", "FLIP Fluid Display Settings", 2))
        if self.export_surface:
            enums.append(('surface', "Surface", "FLIP Fluid Surface", 3))
        if self.export_whitewater:
            enums.append(('whitewater', "Whitewater", "FLIP Fluid Whitewater", 4))
        if self.export_world:
            enums.append(('world', "World", "FLIP Fluid World", 5))
        if self.export_materials:
            enums.append(('materials', "Materials", "FLIP Fluid Materials", 6))
        if self.export_advanced:
            enums.append(('advanced', "Advanced", "FLIP Fluid Advanced", 7))
        if self.export_debug:
            enums.append(('debug', "Debug", "FLIP Fluid Debug", 8))
        if self.export_stats:
            enums.append(('stats', "Stats", "FLIP Fluid Stats", 9))

        if not enums:
            enums.append(('NONE', "None", "No panel to select", 0))
        return enums


    def to_dict(self):
        d = {}
        d["edit_package"] = self.edit_package
        d["edit_preset"] = self.edit_preset 
        d["name"] = self.name
        d["description"] = self.description
        d["package"] = self.package
        d["icon"] = self.icon

        dummy_props = self.get_dummy_domain_properties()
        props = self.get_exported_ui_properties()
        d["properties"] = []
        for p in props:
            pd = {}
            pd["path"] = p.path
            pd["value"] = dummy_props.get_property_from_path(p.path)
            d["properties"].append(pd)
        return d


    def _initialize_menu_settings(self):
        if self.edit_preset == "PRESET_NONE":
            return

        edit_package_info = preset_library.package_identifier_to_info(self.edit_package)
        edit_preset_info = preset_library.preset_identifier_to_info(self.edit_preset)
        if edit_package_info is None or edit_preset_info is None:
            return
        self.ui_properties.initialize()
        self._initialize_menu_preset_info_settings(edit_package_info, edit_preset_info)
        self._initialize_menu_export_settings(edit_preset_info)
        self._initialize_menu_dummy_domain_values(edit_preset_info)
        self._initialize_ui_property_attributes(edit_preset_info)

        self.is_unedited = False


    def _initialize_menu_preset_info_settings(self, package_info, preset_info):
        self.package = package_info['identifier']
        self.name = preset_info['name']
        self.description = preset_info['description']

        self._unload_icon_image()
        icon_path = os.path.join(preset_info['path'], "icon.png")
        if os.path.isfile(icon_path):
            image = self._load_icon_image(preset_info)
            if image is not None:
                self.icon = image.name
        else:
            self.icon = ""


    def _load_icon_image(self, preset_info=None):
        if self.edit_preset == 'PRESET_NONE':
            return
        if preset_info is None:
            preset_info = preset_library.preset_identifier_to_info(self.edit_preset)
        icon_path = os.path.join(preset_info['path'], "icon.png")
        if os.path.isfile(icon_path):
            image_name = preset_info['name'] + "-icon.png"
            image = bpy.data.images.load(icon_path)
            image.name = image_name
            self.loaded_icon_image_name = image.name
            return image


    def _unload_icon_image(self):
        if not self.loaded_icon_image_name:
            return
        image = bpy.data.images.get(self.loaded_icon_image_name)
        if image is not None:
            bpy.data.images.remove(image)
        self.loaded_icon_image_name = ""


    def _load_preset_materials(self):
        if self.edit_preset == 'PRESET_NONE':
            return
        preset_info = preset_library.preset_identifier_to_info(self.edit_preset)
        preset_utils.load_preset_materials(preset_info, self.loaded_materials)


    def _unload_preset_materials(self):
        preset_utils.unload_preset_materials(self.loaded_materials)
        self.loaded_materials.clear()


    def _get_loaded_material_id(self, preset_material_id):
        for minfo in self.loaded_materials:
            if minfo.preset_id == preset_material_id:
                return minfo.loaded_id
        return preset_material_id


    def _initialize_menu_export_settings(self, preset_info):
        properties = preset_info['properties']
        enable_dict = {
                'simulation': False, 'render': False, 'surface': False, 'whitewater': False,
                'world': False, 'materials': False, 'advanced': False, 'debug': False, 'stats': False
            }

        for p in properties:
            split = p['path'].split('.')
            enable_dict[split[1]] = True

        self.export_simulation = enable_dict['simulation']
        self.export_display =    enable_dict['render']
        self.export_surface =    enable_dict['surface']
        self.export_whitewater = enable_dict['whitewater']
        self.export_world =      enable_dict['world']
        self.export_materials =  enable_dict['materials']
        self.export_advanced =   enable_dict['advanced']
        self.export_debug =      enable_dict['debug']
        self.export_stats =      enable_dict['stats']


    def _initialize_menu_dummy_domain_values(self, preset_info):
        dummy_props = self.get_dummy_domain_properties()
        if dummy_props is None:
            return

        self._unload_preset_materials()
        self._load_preset_materials()

        material_paths = preset_library.get_preset_material_paths()
        for p in preset_info['properties']:
            value = p['value']
            if p['path'] in material_paths:
                value = self._get_loaded_material_id(value)
            dummy_props.set_property_from_path(p['path'], value)


    def _save_property_values(self):
        dprops = self.get_dummy_domain_properties()
        if dprops is not None:
            self.ui_properties.save_property_values(dprops)


    def _load_saved_property_values(self):
        ui_properties = self.ui_properties.get_all_properties()
        dummy_props = self.get_dummy_domain_properties()
        for uip in ui_properties:
            value = uip.get_value()
            dummy_props.set_property_from_path(uip.path, value)


    def _initialize_ui_property_attributes(self, preset_info):
        property_enabled_dict = {}
        for p in preset_info['properties']:
            property_enabled_dict[p['path']] = True
        uips = self.ui_properties.get_all_properties()
        for uip in uips:
            uip.enabled = uip.path in property_enabled_dict


    def _check_current_display_panel(self, context=None):
        # Stops UI from drawing enum as unselected
        try:
            self.current_display_panel = self.current_display_panel
        except:
            self.current_display_panel = self.get_preset_panel_selector_enums(bpy.context)[0][0]


    def _initialize_selected_edit_package(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        current_package = dprops.presets.current_package
        current_package_info = preset_library.package_identifier_to_info(current_package)
        if current_package_info['is_system_package']:
            user_packages = preset_library.get_user_package_info_list()
            if len(user_packages) == 0:
                preset_library.initialize_default_user_package()
                user_packages = preset_library.get_user_package_info_list()

            selected_package = None
            for info in user_packages:
                if info['is_default_user_package']:
                    selected_package = info['identifier']
                    break
            if not selected_package:
                selected_package = user_packages[0]['identifier']

            self.edit_package = selected_package
        else:
            self.edit_package = current_package


    def _is_different(self, value1, value2):
        eps = 1e-9
        if isinstance(value1, float):
            return abs(value1 - value2) > eps
        elif isinstance(value1, Vector):
            return (abs(value1[0] - value2[0]) > eps or 
                    abs(value1[1] - value2[1]) > eps or 
                    abs(value1[2] - value2[2]) > eps)
        else:
            return value1 != value2


    def _update_icon(self, context):
        if self.package == "":
            self.package = preset_library.get_all_package_enums(self, context)[0][0]

        package_info = preset_library.package_identifier_to_info(self.package)
        if package_info["use_custom_icons"]:
            img_icon = bpy.data.images.get(self.icon)
            if img_icon:
                self.display_icon = self.icon
                return
        self.display_icon = 'ICON_NONE'


    def _get_display_icon_enum(self, context=None):
        package_info = preset_library.package_identifier_to_info(self.package)
        if package_info["use_custom_icons"]:
            img_icon = bpy.data.images.get(self.icon)
            if img_icon:
                return [(self.icon, self.icon, "", img_icon.preview.icon_id, img_icon.preview.icon_id)]
        return [('ICON_NONE', "None", "No icon loaded...")]


    def _update_edit_package(self, context=None):
        self.edit_preset = "PRESET_NONE"


    def _update_edit_preset(self, context=None):
        self._initialize_menu_settings()


    def _destroy_dummy_domain_object(self):
        global DUMMY_DOMAIN_OBJECT
        if DUMMY_DOMAIN_OBJECT is not None:
            preset_library.destroy_dummy_domain_object(DUMMY_DOMAIN_OBJECT)
            DUMMY_DOMAIN_OBJECT = None


def register():
    bpy.utils.register_class(PresetRegistryProperty)
    bpy.utils.register_class(PresetRegistry)
    bpy.utils.register_class(MaterialPropertyInfo)

    bpy.utils.register_class(NewPresetPackageSettings)
    bpy.utils.register_class(DeletePresetPackageSettings)
    bpy.utils.register_class(ExportPresetPackageSettings)

    bpy.utils.register_class(PresetPropertyUI)
    bpy.utils.register_class(PresetPropertiesUI)
    bpy.utils.register_class(NewPresetSettings)
    bpy.utils.register_class(DeletePresetSettings)
    bpy.utils.register_class(EditPresetSettings)

    bpy.utils.register_class(DisplayPresetInfoSettings)

    bpy.utils.register_class(PresetProperty)
    bpy.utils.register_class(PresetInfo)
    bpy.utils.register_class(PresetPackageInfo)
    bpy.utils.register_class(ImportPresetPackageSettings)


def unregister():
    bpy.utils.unregister_class(PresetRegistryProperty)
    bpy.utils.unregister_class(PresetRegistry)
    bpy.utils.unregister_class(MaterialPropertyInfo)

    bpy.utils.unregister_class(NewPresetPackageSettings)
    bpy.utils.unregister_class(DeletePresetPackageSettings)
    bpy.utils.unregister_class(ExportPresetPackageSettings)

    bpy.utils.unregister_class(PresetPropertyUI)
    bpy.utils.unregister_class(PresetPropertiesUI)
    bpy.utils.unregister_class(NewPresetSettings)
    bpy.utils.unregister_class(DeletePresetSettings)
    bpy.utils.unregister_class(EditPresetSettings)

    bpy.utils.unregister_class(DisplayPresetInfoSettings)

    bpy.utils.unregister_class(PresetProperty)
    bpy.utils.unregister_class(PresetInfo)
    bpy.utils.unregister_class(PresetPackageInfo)
    bpy.utils.unregister_class(ImportPresetPackageSettings)
