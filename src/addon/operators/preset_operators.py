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

import bpy, textwrap
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from ..presets import preset_library
from ..utils import ui_utils
from ..utils import version_compatibility_utils as vcu

from bpy.props import (
        IntProperty,
        StringProperty,
        BoolProperty
        )


class FlipFluidPresetRestoreDefault(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_restore_default_settings"
    bl_label = "Restore Default Settings"
    bl_description = "Restore domain settings to default values"


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if not dprops:
            return {'CANCELLED'}

        error_msg = preset_library.restore_default_settings(dprops)
        if error_msg:
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

        self.report({'INFO'}, "Successfully restored default settings")

        return {'FINISHED'}


class FlipFluidPresetSaveUserDefault(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_save_user_default_settings"
    bl_label = "Save Default Settings"
    bl_description = "Save the current domain settings as defaults"


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if not dprops:
            return {'CANCELLED'}

        success = preset_library.save_user_default_settings()
        if not success:
            self.report({'ERROR'}, "Error saving user default settings")

        self.report({'INFO'}, "Successfully saved default settings")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidPresetRestoreSystemDefault(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_restore_system_default_settings"
    bl_label = "Restore Original Default Settings"
    bl_description = "Restore default domain settings to original system values"


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if not dprops:
            return {'CANCELLED'}

        success = preset_library.delete_user_default_settings()
        if not success:
            self.report({'ERROR'}, "Error restoring system default settings")

        self.report({'INFO'}, "Successfully restored default settings")
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidPresetCreateNewPackage(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_package"
    bl_label = "Create New Package"
    bl_description = "Create a new preset package"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def draw(self, context):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.new_package_settings

        column = self.layout.column()
        column.prop(settings, 'name', text="Name")
        column.prop(settings, 'author', text="Author")
        column.prop(settings, 'description', text="Description")
        column.prop(settings, 'use_custom_icons', text="Use Custom Icons")
        column.separator()


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.new_package_settings
        if not settings.name:
            errmsg = "Error: New package must have a name"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        error = preset_library.create_new_user_package(settings.to_dict())
        if error:
            errmsg = "Error: Unable to create new preset"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        self.report({'INFO'}, "Successfully created package <" + settings.name + ">")
        settings.reset()
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class FlipFluidPresetDeletePackage(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_delete_package"
    bl_label = "Remove Package"
    bl_description = ("Remove a preset package. A menu will be displayed to select" +
                      " a package for removal")

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def draw(self, context):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.delete_package_settings

        column = self.layout.column()
        column.separator()
        column.label(text="Select Package:")
        column.prop(settings, 'package', text="")
        column.separator()
        column.label(text="Are you sure? This action cannot be undone.")


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.delete_package_settings
        if settings.package == 'DELETE_PACKAGE_NONE':
            errmsg = "Error: No package was selected for removal"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        package_info = preset_library.package_identifier_to_info(settings.package)
        name = package_info['name']

        dprops.presets.preset_stack.remove_package_presets_from_stack(settings.package)

        error = preset_library.delete_package(settings.package)
        if error:
            errmsg = "Error: Unable to remove package"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        dprops.presets.check_preset_enums()
        self.report({'INFO'}, "Successfully deleted package <" + name + ">")
        return {'FINISHED'}


    def invoke(self, context, event):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.delete_package_settings
        settings.reset()
        return context.window_manager.invoke_props_dialog(self)


class FlipFluidPresetCreateNewPresetEnableAll(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_preset_enable_all"
    bl_label = "Enable All"
    bl_description = "Enable all preset attributes"

    collection_id = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("collection_id"))


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        if self.collection_id:
            settings.enable_collection(self.collection_id)
        else:
            settings.enable_all()
        self.collection_id = ""
        return {'FINISHED'}


class FlipFluidPresetCreateNewPresetDisableAll(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_preset_disable_all"
    bl_label = "Disable All"
    bl_description = "Disable all preset attributes"

    collection_id = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("collection_id"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        if self.collection_id:
            settings.disable_collection(self.collection_id)
        else:
            settings.disable_all()
        self.collection_id = ""
        return {'FINISHED'}


class FlipFluidPresetCreateNewPresetEnableAuto(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_preset_enable_auto"
    bl_label = "Enable Auto"
    bl_description = ("Automatically enable/disable preset attributes by" +
                      " comparing to system default settings")

    collection_id = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("collection_id"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        if self.collection_id:
            settings.enable_collection_auto(self.collection_id)
        else:
            settings.enable_all_auto()
        self.collection_id = ""
        return {'FINISHED'}


class FlipFluidPresetCreateNewPresetSelectPrevious(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_select_prev"
    bl_label = "Previous"
    bl_description = "Select previous display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i - 1 if i - 1 >= 0 else len(enums) - 1
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetCreateNewPresetSelectNext(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_select_next"
    bl_label = "Next"
    bl_description = "Select next display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i + 1 if i + 1 < len(enums) else 0
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetCreateNewPresetReset(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_reset"
    bl_label = "Reset Menu"
    bl_description = "Reset menu settings"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        settings.reset()
        return {'FINISHED'}


class FlipFluidPresetCreateNewPreset(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_create_new_preset"
    bl_label = "Create New Preset"
    bl_description = "Create new preset based on the current domain settings"


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def check(self, context):
        return True


    def draw_column(self, context, column_data, column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.new_preset_settings
        collection = column_data['collection']

        registry = dprops.property_registry.properties
        is_key_property = {}
        is_keyed_property = {}
        unlocked_status = {}
        for p in registry:
            if p.is_key:
                is_key_property[p.path] = True
            if p.key_path:
                is_keyed_property[p.path] = True
                unlocked_status[p.path] = p.key_value == dprops.get_property_from_path(p.key_path)

        row = column.row()
        if column_data['column_id'] == 0:
            row.label(text=column_data['label'])

            export_id = settings.get_export_identifier_from_collection(collection)
            collection_id = settings.get_collection_identifier_from_collection(collection)
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.operator("flip_fluid_operators.preset_create_new_preset_enable_all", 
                    text="", 
                    icon="FILE_TICK", 
                    emboss=False
                    ).collection_id=collection_id
            row.operator("flip_fluid_operators.preset_create_new_preset_disable_all", 
                    text="", 
                    icon="CANCEL", 
                    emboss=False
                    ).collection_id=collection_id
            row.operator("flip_fluid_operators.preset_create_new_preset_enable_auto", 
                    text="", 
                    icon="AUTO", 
                    emboss=False
                    ).collection_id=collection_id
            row.prop(settings, export_id, icon="X", icon_only=True, emboss=False)

            column.box()
        column.separator()

        ui_properties = [x for x in column_data['properties']]
        if settings.ui_sort:
            new_ui_properties = ([x for x in ui_properties if x.enabled] +
                                 [x for x in ui_properties if not x.enabled])
            ui_properties = new_ui_properties

        for p in ui_properties:
            split_vals = p.path.split('.')
            prop_group = getattr(dprops, split_vals[1])
            identifier = split_vals[2]

            split = vcu.ui_split(column, factor=0.02, align=True)
            tick_column = split.column(align=True)
            temp_column = split.column(align=True)
            split = vcu.ui_split(temp_column, factor=0.42)
            label_column = split.column(align=True)
            temp_column = split.column(align=True)
            split = vcu.ui_split(temp_column, factor=0.02)

            lock_column = split.column()
            prop_column = split.column(align=True)
            prop_column = prop_column.row(align=True)

            tick_column.prop(p, 'enabled', 
                    icon="FILE_TICK" if p.enabled else "CANCEL", 
                    icon_only=True, 
                    emboss=False
                    )

            label_column.label(text=p.label)

            if p.path in is_key_property:
                lock_column.prop(p, 'dummy_prop', 
                    icon="KEY_HLT", 
                    icon_only=True, 
                    emboss=False
                    )
            elif p.path in is_keyed_property:
                unlocked = unlocked_status[p.path]
                lock_column.prop(p, 'dummy_prop', 
                    icon="UNLOCKED" if unlocked else "LOCKED", 
                    icon_only=True, 
                    emboss=False
                    )
                if not unlocked:
                    prop_column.enabled = False
                    lock_column.enabled = False

            prop_column.alert = not p.enabled

            prop = getattr(prop_group, identifier)
            if hasattr(prop, "is_min_max_property"):
                row = prop_column.row(align=True)
                row.prop(prop, "value_min", text="")
                row.prop(prop, "value_max", text="")
            else:
                if p.path in is_key_property:
                    prop_column.prop(prop_group, identifier, expand=True)
                else:
                    prop_column.prop(prop_group, identifier, text="")

        column.separator()
        column.separator()


    def draw_custom_properties(self, context, base_column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.new_preset_settings

        base_column.separator()
        base_column.separator()
        base_column.separator()

        split = vcu.ui_split(base_column, factor=1/6)
        column = split.column()
        column.label(text="Customize Preset Attributes:")
        column.box()
        column.separator()
        column = split.column()

        column = base_column.column()
        if settings.current_display_panel != 'NONE':
            row = column.row(align=True)
            row.alignment='LEFT'
            row.operator("flip_fluid_operators.preset_create_new_preset_enable_all",
                         icon="FILE_TICK")
            row.operator("flip_fluid_operators.preset_create_new_preset_disable_all",
                         icon="CANCEL")
            row.operator("flip_fluid_operators.preset_create_new_preset_enable_auto",
                         text="Auto",
                         icon="AUTO")
            row.label(text="")
            row.prop(settings, "ui_sort")

            column.separator()
            column.separator()
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.operator("flip_fluid_operators.preset_create_new_select_prev",
                         text="",
                         icon="TRIA_LEFT")
            row.prop(settings, "current_display_panel", expand=True)
            row.operator("flip_fluid_operators.preset_create_new_select_next",
                         text="",
                         icon="TRIA_RIGHT")
        else:
            column.label(text="No panels selected for export...")
            return


        column.separator()
        column.separator()
        column.separator()
        split = column.split()

        buffer_pct = 0.95
        column1 = split.column()
        temp_split = vcu.ui_split(column1, factor=buffer_pct)
        column1 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column2 = split.column()
        temp_split = vcu.ui_split(column2, factor=buffer_pct)
        column2 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column3 = split.column()
        temp_split = vcu.ui_split(column3, factor=buffer_pct)
        column3 = temp_split.column(align=True)
        temp_column = temp_split.column()

        settings = dprops.presets.new_preset_settings
        collection_id = settings.current_display_panel
        columns = settings.ui_properties.generate_columns3(collection_id, dprops.property_registry)
        self.draw_column(context, columns[0], column1)
        self.draw_column(context, columns[1], column2)
        self.draw_column(context, columns[2], column3)


    def draw(self, context):
        default_window_height = 28

        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.new_preset_settings
        package_info = preset_library.package_identifier_to_info(settings.package)

        base_column = self.layout.column()
        base_column.separator()
        split = vcu.ui_split(base_column, factor=0.01)
        column = split.column()
        for i in range(default_window_height):
            column.label(text="")

        base_column = split.column()

        split = base_column.split(align=True)
        name_column = split.column(align=True)
        export_column = split.column(align=True)

        name_column_split = vcu.ui_split(name_column, factor=0.95)
        name_column1 = name_column_split.column()
        name_column2 = name_column_split.column()

        row = name_column1.row()
        row.label(text="Preset Info:")
        row = row.row()
        row.alignment = "RIGHT"
        row.operator("flip_fluid_operators.preset_create_new_reset", 
                icon="RECOVER_LAST", 
                text="", 
                emboss=False
                )
        name_column1.box()
        name_column1.separator()

        if package_info["use_custom_icons"]:
            split = vcu.ui_split(name_column1, factor=0.23)
            name_column_icon = split.column()
            name_column_left = split.column()
            split = vcu.ui_split(name_column_left, factor=0.2)
            name_column_left = split.column()
            name_column_right = split.column()
        else:
            split = vcu.ui_split(name_column1, factor=0.3)
            name_column_left = split.column()
            name_column_right = split.column()

        if package_info["use_custom_icons"]:
            name_column_icon.enabled = False
            name_column_icon.template_icon_view(settings, "display_icon")

        name_column_left.label(text="Package: ")
        name_column_left.separator()
        name_column_left.separator()
        name_column_left.label(text="Name: ")
        name_column_left.label(text="Description: ")
        name_column_left.label(text="Icon: ")

        name_column_right.prop(settings, 'package', text="")
        name_column_right.separator()
        name_column_right.separator()
        name_column_right.prop(settings, 'name', text="")
        name_column_right.prop(settings, 'description', text="")

        if package_info["use_custom_icons"]:
            name_column_right.prop_search(settings, "icon", bpy.data, "images", text="")
        else:
            name_column_right.label(text="(Custom icons are not enabled for this package)")

        split = vcu.ui_split(export_column, factor=0.95)
        export_column = split.column()
        export_column.label(text="Export Panel Settings:")
        export_column.box()
        export_column.separator()
        export_column_split = export_column.split()
        export_column1 = export_column_split.column()
        export_column2 = export_column_split.column()
        export_column3 = export_column_split.column()

        export_column1.prop(settings, 'export_simulation')
        export_column1.prop(settings, 'export_display')
        export_column1.prop(settings, 'export_surface')
        export_column2.prop(settings, 'export_whitewater')
        export_column2.prop(settings, 'export_world')
        export_column2.prop(settings, 'export_materials')
        export_column3.prop(settings, 'export_advanced')
        export_column3.prop(settings, 'export_debug')
        export_column3.prop(settings, 'export_stats')

        self.draw_custom_properties(context, base_column)

        column.separator()
        column.separator()


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings

        if not settings.name:
            errmsg = "Error: New preset must have a name"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        package_info = preset_library.package_identifier_to_info(settings.package)
        if package_info["use_custom_icons"]:
            icon_img = bpy.data.images.get(settings.icon)
            if not icon_img:
                errmsg = "Error: No image icon selected"
                errdesc = ("This package uses custom image icons." +
                          " Import an image into the Blender UV/Image Editor and select" + 
                          " the image in the 'Create New Preset' popup dialog.")
                bpy.ops.flip_fluid_operators.display_error(
                        'INVOKE_DEFAULT',
                        error_message=errmsg,
                        error_description=errdesc,
                        popup_width=400
                        )
                return {'CANCELLED'}
        else:
            settings.icon = ""

        exported_props = settings.get_exported_ui_properties()
        if not exported_props:
            errmsg = "Error: Preset has no settings selected for export"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        error = preset_library.create_new_user_preset(settings.to_dict())
        if error:
            errmsg = "Error: Unable to create new preset"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        self.report({'INFO'}, "Successfully created preset <" + settings.name + ">")
        settings.reset()
        return {'FINISHED'}


    def invoke(self, context, event):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.new_preset_settings
        settings.initialize()
        return context.window_manager.invoke_props_dialog(self, width=1300)


class FlipFluidPresetSelectNext(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_select_next"
    bl_label = "Next"
    bl_description = "Select the next package preset"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        enums = preset_library.get_current_package_preset_enums(self, context)
        for i, e in enumerate(enums):
            if e[0] == dprops.presets.current_preset:
                next_idx = i + 1 if i + 1 < len(enums) else 0
                if enums[next_idx][0] == 'PRESET_NONE':
                    next_idx = next_idx + 1 if next_idx + 1 < len(enums) else 0
                dprops.presets.current_preset = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetSelectPrevious(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_select_previous"
    bl_label = "Previous"
    bl_description = "Select the previous package preset"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        enums = preset_library.get_current_package_preset_enums(self, context)
        for i, e in enumerate(enums):
            if e[0] == dprops.presets.current_preset:
                next_idx = i - 1 if i - 1 >= 0 else len(enums) - 1
                if enums[next_idx][0] == 'PRESET_NONE':
                    next_idx = next_idx - 1 if next_idx - 1 >= 0 else len(enums) - 1
                dprops.presets.current_preset = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetDeletePreset(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_delete_preset"
    bl_label = "Remove Preset"
    bl_description = ("Remove a preset. A menu will be displayed to select" +
                      " a preset for removal")

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def draw(self, context):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.delete_preset_settings

        column = self.layout.column()
        column.separator()
        column.label(text="Package:")
        column.prop(settings, 'package', text="")
        column.separator()
        column.label(text="Preset:")
        column.prop(settings, 'preset', text="")
        column.separator()
        column.label(text="Are you sure? This action cannot be undone.")


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.delete_preset_settings
        if settings.preset == 'DELETE_PRESET_NONE':
            errmsg = "Error: No preset was selected for removal"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        preset_info = preset_library.preset_identifier_to_info(settings.preset)
        name = preset_info['name']

        is_deleting_current_preset = settings.preset == dprops.presets.current_preset

        preset_stack = dprops.presets.preset_stack
        preset_stack.remove_preset_from_stack_by_identifier(settings.preset)

        error = preset_library.delete_preset(settings.preset)
        if error:
            errmsg = "Error: Unable to remove preset"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        if is_deleting_current_preset:
            dprops.presets.current_preset = 'PRESET_NONE'

        self.report({'INFO'}, "Successfully deleted preset <" + name + ">")
        return {'FINISHED'}


    def invoke(self, context, event):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.delete_preset_settings
        settings.reset()
        return context.window_manager.invoke_props_dialog(self)


class FlipFluidPresetDisplayInfoSelectPrevious(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_display_info_select_prev"
    bl_label = "Previous"
    bl_description = "Select previous display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.display_preset_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i - 1 if i - 1 >= 0 else len(enums) - 1
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetDisplayInfoSelectNext(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_display_info_select_next"
    bl_label = "Next"
    bl_description = "Select next display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.display_preset_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i + 1 if i + 1 < len(enums) else 0
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetDisplayInfo(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_display_info"
    bl_label = "Preset Info"
    bl_description = "Display preset information"

    identifier = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("identifier"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def check(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.display_preset_settings
        settings.reinitialize_display_values()
        return True


    def generation_column_partitions(self, context):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.display_preset_settings
        collection_ids = [settings.current_display_panel]
        chunks = settings.ui_properties.generate_column_partition_chunks(collection_ids)
        return ui_utils.partition_chunks_column3(chunks)


    def draw_partition_chunk(self, context, chunk, column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.display_preset_settings
        dummy_props = settings.get_dummy_domain_properties()
        collection = chunk['collection']

        row = column.row()
        if not chunk['is_continuation']:
            row.label(text=chunk['label'])
            column.box()
        column.separator()

        collection = [x for x in chunk['collection']]
        for i in range(chunk['range'][0], chunk['range'][1]):
            p = collection[i]

            split_vals = p.path.split('.')
            prop_group = getattr(dummy_props, split_vals[1])
            identifier = split_vals[2]

            split = vcu.ui_split(column, factor=0.05, align=True)
            tick_column = split.column(align=True)
            tick_column.enabled = False
            temp_column = split.column(align=True)
            split = vcu.ui_split(temp_column, factor=0.5)
            label_column = split.column(align=True)
            prop_column = split.column(align=True)
            prop_column = prop_column.row(align=True)

            tick_column.prop(p, 'enabled', 
                    icon="KEYTYPE_JITTER_VEC" if p.enabled else "CANCEL", 
                    icon_only=True, 
                    emboss=False
                    )

            label_column.label(text=p.label)

            prop_column.alert = not p.enabled

            prop = getattr(prop_group, identifier)
            if hasattr(prop, "is_min_max_property"):
                row = prop_column.row(align=True)
                row.prop(prop, "value_min", text="")
                row.prop(prop, "value_max", text="")
            else:
                prop_column.prop(prop_group, identifier, text="")

        column.separator()
        column.separator()


    def draw_partition(self, context, partition, column):
        for c in partition:
            self.draw_partition_chunk(context, c, column)


    def draw_preset_properties(self, context, base_column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.display_preset_settings

        base_column.separator()
        column = base_column.column()
        if settings.current_display_panel != 'NONE':
            row = column.row(align=True)
            column.separator()
            column.separator()
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.operator("flip_fluid_operators.preset_display_info_select_prev",
                         text="",
                         icon="TRIA_LEFT")
            row.prop(settings, "current_display_panel", expand=True)
            row.operator("flip_fluid_operators.preset_display_info_select_next",
                         text="",
                         icon="TRIA_RIGHT")
        else:
            column.label(text="No panels selected for export...")

        column.separator()
        split = column.split()

        buffer_pct = 0.95
        column1 = split.column()
        temp_split = vcu.ui_split(column1, factor=buffer_pct)
        column1 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column2 = split.column()
        temp_split = vcu.ui_split(column2, factor=buffer_pct)
        column2 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column3 = split.column()
        temp_split = vcu.ui_split(column3, factor=buffer_pct)
        column3 = temp_split.column(align=True)
        temp_column = temp_split.column()

        partitions = self.generation_column_partitions(context)
        self.draw_partition(context, partitions[0], column1)
        self.draw_partition(context, partitions[1], column2)
        self.draw_partition(context, partitions[2], column3)


    def draw(self, context):
        default_window_height = 23

        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.display_preset_settings

        base_column = self.layout.column()
        base_column.separator()
        split = vcu.ui_split(base_column, factor=0.01)
        column = split.column()
        for i in range(default_window_height):
            column.label(text="")

        base_column = split.column()

        split = vcu.ui_split(base_column, align=True, factor=0.65)
        name_column = split.column(align=True)
        export_column = split.column(align=True)

        name_column_split = vcu.ui_split(name_column, factor=0.95)
        name_column1 = name_column_split.column()
        name_column2 = name_column_split.column()

        preset_info = preset_library.preset_identifier_to_info(self.identifier)

        row = name_column1.row()
        row.label(text=preset_info['name'])
        name_column1.box()
        name_column1.separator()

        if "icon" in preset_info:
            split = vcu.ui_split(name_column1, factor=0.17)
            name_column_icon = split.column()
            name_column1 = split.column()
            split = vcu.ui_split(name_column1, factor=0.15)
            name_column_left = split.column()
            name_column_right = split.column()

            name_column_icon.template_icon_view(settings, "display_icon")
        else:
            split = vcu.ui_split(name_column1, factor=0.15)
            name_column_left = split.column()
            name_column_right = split.column()

        name_column_left.label(text="Preset: ")
        name_column_left.separator()
        name_column_left.label(text="Package: ")
        name_column_left.separator()
        name_column_left.label(text="Description: ")

        current_package = dprops.presets.current_package
        package_name = self.layout.enum_item_name(
                dprops.presets, "current_package", current_package
                )

        name_column_right.label(text=preset_info['name'])
        name_column_right.separator()
        name_column_right.label(text=package_name)
        name_column_right.separator()

        text_list = textwrap.wrap(preset_info['description'], width=80)
        for line in text_list:
            name_column_right.label(text=line)

        self.draw_preset_properties(context, base_column)

        column.separator()
        column.separator()


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.display_preset_settings
        settings.reset()
        self.identifier = ""
        return {'FINISHED'}


    def invoke(self, context, event):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not self.identifier:
            self.identifier = dprops.presets.current_preset

        settings = dprops.presets.display_preset_settings
        settings.identifier = self.identifier
        settings.initialize()
        return context.window_manager.invoke_props_dialog(self, width=1250)


    def cancel(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.display_preset_settings
        settings.reset()
        self.identifier = ""


class FlipFluidPresetExportPackage(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_export_package"
    bl_label = "Export Package"
    bl_description = ("Export preset package as a .zip file. A menu will be"
                      " displayed to select a package to export.")

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def check(self, context):
        return True


    def draw(self, context):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.export_package_settings

        split = vcu.ui_split(self.layout, factor=0.25)
        column = split.column()
        column.label(text="Package:")
        column.label(text="Filename:")

        column = split.column()
        column.prop(settings, "package", text="")
        column.prop(settings, "export_filename", text="")
        column.prop(settings, "create_subdirectories")

        column = self.layout.column()
        column.separator()
        column.label(text="Package will be exported to:")
        column.label(text=" "*5 + settings.export_filepath)
        column.separator()


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.export_package_settings
        if settings.package == 'EXPORT_PACKAGE_NONE':
            errmsg = "Error: No package was selected for export"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        filepath = settings.export_filepath
        create_dirs = settings.create_subdirectories
        error = preset_library.export_package(
                settings.package, filepath, create_directory=create_dirs
                )
        if error:
            errmsg = "Error: Unable to export package"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        settings.reset()
        self.report({'INFO'}, "Successfully exported package to <" + filepath + ">")
        return {'FINISHED'}


    def invoke(self, context, event):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.export_package_settings
        settings.initialize()
        return context.window_manager.invoke_props_dialog(self, width=400)


class SelectPresetPackageZipFile(bpy.types.Operator, ImportHelper):
    bl_idname = "flip_fluid_operators.select_package_zipfile"
    bl_label = "Select Package Zipfile"

    filename_ext = "*.zip"
    filter_glob = StringProperty(
            default="*.zip",
            options={'HIDDEN'},
            maxlen=255,
            )
    exec(vcu.convert_attribute_to_28("filter_glob"))


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.presets.import_package_settings.package_filepath = self.filepath
        return {'FINISHED'}


class FlipFluidPresetImportPackageSelectPrevious(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_import_select_prev"
    bl_label = "Previous"
    bl_description = "Select previous display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.import_package_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i - 1 if i - 1 >= 0 else len(enums) - 1
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetImportPackageSelectNext(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_import_select_next"
    bl_label = "Next"
    bl_description = "Select next display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.import_package_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i + 1 if i + 1 < len(enums) else 0
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetImportPackageSelectPresetPrevious(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_import_select_preset_prev"
    bl_label = "Previous"
    bl_description = "Select previous preset"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.import_package_settings
        enums = settings.get_package_preset_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.selected_preset:
                next_idx = i - 1 if i - 1 >= 0 else len(enums) - 1
                settings.selected_preset = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetImportPackageSelectPresetNext(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_import_select_preset_next"
    bl_label = "Next"
    bl_description = "Select next preset"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.import_package_settings
        enums = settings.get_package_preset_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.selected_preset:
                next_idx = i + 1 if i + 1 < len(enums) else 0
                settings.selected_preset = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetImportPackage(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_import_package"
    bl_label = "Install Package"
    bl_description = ("Install a preset package. A popup will be displayed " + 
                      "detailing the package contents.")


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def check(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.import_package_settings
        settings.reinitialize_display_values()
        return True


    def generation_column_partitions(self, context):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.import_package_settings
        collection_ids = [settings.current_display_panel]
        chunks = settings.ui_properties.generate_column_partition_chunks(collection_ids)
        return ui_utils.partition_chunks_column3(chunks)


    def draw_partition_chunk(self, context, chunk, column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.import_package_settings
        dummy_props = settings.get_dummy_domain_properties()
        collection = chunk['collection']

        row = column.row()
        if not chunk['is_continuation']:
            row.label(chunk['label'])
            column.box()
        column.separator()

        collection = [x for x in chunk['collection']]
        for i in range(chunk['range'][0], chunk['range'][1]):
            p = collection[i]

            split_vals = p.path.split('.')
            prop_group = getattr(dummy_props, split_vals[1])
            identifier = split_vals[2]

            split = vcu.ui_split(column, factor=0.05, align=True)
            tick_column = split.column(align=True)
            tick_column.enabled = False
            temp_column = split.column(align=True)
            split = vcu.ui_split(temp_column, factor=0.5)
            label_column = split.column(align=True)
            prop_column = split.column(align=True)
            prop_column = prop_column.row(align=True)

            tick_column.prop(p, 'enabled', 
                    icon="KEYTYPE_JITTER_VEC" if p.enabled else "CANCEL", 
                    icon_only=True, 
                    emboss=False
                    )

            label_column.label(text=p.label)

            prop_column.alert = not p.enabled

            prop = getattr(prop_group, identifier)
            if hasattr(prop, "is_min_max_property"):
                row = prop_column.row(align=True)
                row.prop(prop, "value_min", text="")
                row.prop(prop, "value_max", text="")
            else:
                prop_column.prop(prop_group, identifier, text="")

        column.separator()
        column.separator()


    def draw_partition(self, context, partition, column):
        for c in partition:
            self.draw_partition_chunk(context, c, column)


    def draw_preset_properties(self, context, base_column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.import_package_settings

        base_column.separator()
        column = base_column.column()
        if settings.current_display_panel != 'NONE':
            row = column.row(align=True)
            column.separator()
            column.label(text="Preset Attributes:")
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.operator("flip_fluid_operators.preset_import_select_prev",
                         text="",
                         icon="TRIA_LEFT")
            row.prop(settings, "current_display_panel", expand=True)
            row.operator("flip_fluid_operators.preset_import_select_next",
                         text="",
                         icon="TRIA_RIGHT")
        else:
            column.label(text="No panels selected for export...")


        column.separator()
        split = column.split()

        buffer_pct = 0.95
        column1 = split.column()
        temp_split = vcu.ui_split(column1, factor=buffer_pct)
        column1 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column2 = split.column()
        temp_split = vcu.ui_split(column2, factor=buffer_pct)
        column2 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column3 = split.column()
        temp_split = vcu.ui_split(column3, factor=buffer_pct)
        column3 = temp_split.column(align=True)
        temp_column = temp_split.column()

        partitions = self.generation_column_partitions(context)
        self.draw_partition(context, partitions[0], column1)
        self.draw_partition(context, partitions[1], column2)
        self.draw_partition(context, partitions[2], column3)


    def draw(self, context):
        default_window_height = 28

        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.import_package_settings

        base_column = self.layout.column()
        base_column.separator()
        split = vcu.ui_split(base_column, factor=0.01)
        column = split.column()
        for i in range(default_window_height):
            column.label(text="")

        base_column = split.column()

        split = vcu.ui_split(base_column, align=True, factor=0.65)
        name_column = split.column(align=True)
        export_column = split.column(align=True)

        name_column_split = vcu.ui_split(name_column, factor=0.95)
        name_column1 = name_column_split.column()
        name_column2 = name_column_split.column()

        row = name_column1.row()
        row.label(text="Package Info")
        name_column1.box()
        name_column1.separator()

        row = name_column1.row()
        split_column = vcu.ui_split(row, factor=0.1)
        package_info_left = split_column.column()
        package_info_left.label(text="Package:")
        package_info_right = split_column.column()
        package_info_right.label(settings.package_info.name)

        if settings.package_info.author:
            row = name_column1.row()
            split_column = vcu.ui_split(row, factor=0.1)
            package_info_left = split_column.column()
            package_info_left.label(text="Author:")
            package_info_right = split_column.column()
            package_info_right.label(settings.package_info.author)

        if settings.package_info.description:
            row = name_column1.row()
            split_column = vcu.ui_split(row, factor=0.1)
            package_info_left = split_column.column()
            package_info_left.label(text="Description:")
            package_info_right = split_column.column()
            text_list = textwrap.wrap(settings.package_info.description, width=120)
            for line in text_list:
                package_info_right.label(text=line)

        name_column1.separator()
        row = name_column1.row()
        split_column = vcu.ui_split(row, factor=0.1)
        package_info_left = split_column.column()
        package_info_left.label(text="Presets:")
        package_info_right = split_column.column()
        presets_row = package_info_right.row(align=True)
        presets_row.alignment = 'LEFT'
        presets_row.prop(settings, "selected_preset", text="")
        package_info_right.separator()
        package_info_right.separator()

        row = name_column1.row(align=True)
        row.alignment = 'LEFT'
        row.operator("flip_fluid_operators.preset_import_select_preset_prev",
                     text="",
                     icon="TRIA_LEFT", emboss=False)
        row.label(text="Preset Info")
        row.operator("flip_fluid_operators.preset_import_select_preset_next",
                     text="",
                     icon="TRIA_RIGHT", emboss=False)
        split = vcu.ui_split(name_column1, factor=0.5)
        split.column().box()
        name_column1.separator()

        if settings.selected_preset == 'PRESET_NONE':
            name_column1.label(text="This package does not contain any presets...")
            return

        preset_info = settings.get_selected_preset_info()

        if preset_info.icon_id != -1:
            split = vcu.ui_split(name_column1, factor=0.17)
            name_column_icon = split.column()
            name_column1 = split.column()
            split = vcu.ui_split(name_column1, factor=0.12)
            name_column_left = split.column()
            name_column_right = split.column()

            name_column_icon.template_icon_view(settings, "display_icon")
        else:
            split = vcu.ui_split(name_column1, factor=0.1)
            name_column_left = split.column()
            name_column_right = split.column()

        name_column_left.label(text="Preset: ")
        name_column_left.separator()
        name_column_left.label(text="Description: ")

        name_column_right.label(text=preset_info.name)
        name_column_right.separator()

        text_list = textwrap.wrap(preset_info['description'], width=80)
        for line in text_list:
            name_column_right.label(text=line)

        self.draw_preset_properties(context, base_column)

        column.separator()
        column.separator()


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.import_package_settings
        error = preset_library.import_package(settings.package_filepath)
        if error:
            errmsg = "Error: Unable to import package"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        pinfo = {}
        preset_library.decode_package_zipfile(settings.package_filepath, pinfo)

        settings.reset()
        self.report({'INFO'}, "Successfully imported package <" + pinfo['name'] + ">")
        preset_library.clear_temp_files()

        return {'FINISHED'}


    def invoke(self, context, event):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.import_package_settings

        data = {}
        error = preset_library.decode_package_zipfile(settings.package_filepath, data)
        if error:
            errmsg = "Error: Unable to import package"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        settings.initialize(data)

        return context.window_manager.invoke_props_dialog(self, width=1250)


    def cancel(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.import_package_settings
        settings.reset()
        preset_library.clear_temp_files()


class FlipFluidPresetAddPresetToStack(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_add_to_stack"
    bl_label = "Add to Preset Stack"
    bl_description = "Add selected preset to the preset stack"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.presets.preset_stack.stage_preset(dprops.presets.current_preset)
        dprops.presets.preset_stack.add_staged_preset_to_stack()
        return {'FINISHED'}


class FlipFluidPresetRemovePresetFromStack(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_remove_from_stack"
    bl_label = "Remove From Preset Stack"
    bl_description = "Remove from preset stack"

    stack_index = IntProperty(default=-1)
    exec(vcu.convert_attribute_to_28("stack_index"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None or self.stack_index == -1:
            return {'CANCELLED'}
        dprops.presets.preset_stack.remove_preset_from_stack(self.stack_index)
        self.stack_index = -1
        return {'FINISHED'}


class FlipFluidPresetMovePresetUpInStack(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_move_up_in_stack"
    bl_label = "Move Up"
    bl_description = "Move preset up in the stack"

    stack_index = IntProperty(default=-1)
    exec(vcu.convert_attribute_to_28("stack_index"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None or self.stack_index == -1:
            return {'CANCELLED'}
        dprops.presets.preset_stack.move_preset_up_in_stack(self.stack_index)
        self.stack_index = -1
        return {'FINISHED'}


class FlipFluidPresetMovePresetDownInStack(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_move_down_in_stack"
    bl_label = "Move Down"
    bl_description = "Move preset down in the stack"

    stack_index = IntProperty(default=-1)
    exec(vcu.convert_attribute_to_28("stack_index"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None or self.stack_index == -1:
            return {'CANCELLED'}
        dprops.presets.preset_stack.move_preset_down_in_stack(self.stack_index)
        self.stack_index = -1
        return {'FINISHED'}


class FlipFluidPresetApplyAndRemoveFromStack(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_apply_remove_from_stack"
    bl_label = "Apply"
    bl_description = "Apply preset and remove from the stack"

    stack_index = IntProperty(default=-1)
    exec(vcu.convert_attribute_to_28("stack_index"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None or self.stack_index == -1:
            return {'CANCELLED'}
        dprops.presets.preset_stack.apply_and_remove_preset_from_stack(self.stack_index)
        self.stack_index = -1
        return {'FINISHED'}


class FlipFluidPresetEditPresetReset(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_edit_reset"
    bl_label = "Reset Preset Edits"
    bl_description = "Reset preset edits to original values"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        settings.reset_preset_edits()
        return {'FINISHED'}



class FlipFluidPresetEditPresetEnableAll(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_edit_preset_enable_all"
    bl_label = "Enable All"
    bl_description = "Enable all preset attributes"

    collection_id = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("collection_id"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        if self.collection_id:
            settings.enable_collection(self.collection_id)
        else:
            settings.enable_all()
        self.collection_id = ""
        return {'FINISHED'}


class FlipFluidPresetEditPresetDisableAll(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_edit_preset_disable_all"
    bl_label = "Disable All"
    bl_description = "Disable all preset attributes"

    collection_id = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("collection_id"))

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        if self.collection_id:
            settings.disable_collection(self.collection_id)
        else:
            settings.disable_all()
        self.collection_id = ""
        return {'FINISHED'}


class FlipFluidPresetEditPresetSelectPrevious(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_edit_select_prev"
    bl_label = "Previous"
    bl_description = "Select previous display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i - 1 if i - 1 >= 0 else len(enums) - 1
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetEditPresetSelectNext(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_edit_select_next"
    bl_label = "Next"
    bl_description = "Select next display panel"

    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        enums = settings.get_preset_panel_selector_enums()
        for i, e in enumerate(enums):
            if e[0] == settings.current_display_panel:
                next_idx = i + 1 if i + 1 < len(enums) else 0
                settings.current_display_panel = enums[next_idx][0]
                break
        return {'FINISHED'}


class FlipFluidPresetEditPreset(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.preset_edit_preset"
    bl_label = "Edit Preset"
    bl_description = "Edit preset settings"


    @classmethod
    def poll(cls, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        return domain_object is not None


    def check(self, context):
        return True


    def draw_column(self, context, column_data, column):
        dprops = context.scene.flip_fluid.get_domain_properties()
        settings = dprops.presets.edit_preset_settings
        dummy_props = settings.get_dummy_domain_properties()
        collection = column_data['collection']

        registry = dprops.property_registry.properties
        is_key_property = {}
        is_keyed_property = {}
        unlocked_status = {}
        for p in registry:
            if p.is_key:
                is_key_property[p.path] = True
            if p.key_path:
                is_keyed_property[p.path] = True
                unlocked_status[p.path] = p.key_value == dummy_props.get_property_from_path(p.key_path)

        row = column.row()
        if column_data['column_id'] == 0:
            row.label(text=column_data['label'])

            export_id = settings.get_export_identifier_from_collection(collection)
            collection_id = settings.get_collection_identifier_from_collection(collection)
            row = row.row(align=True)
            row.alignment = 'RIGHT'
            row.operator("flip_fluid_operators.preset_create_new_preset_enable_all", 
                    text="", 
                    icon="FILE_TICK", 
                    emboss=False
                    ).collection_id=collection_id
            row.operator("flip_fluid_operators.preset_create_new_preset_disable_all", 
                    text="", 
                    icon="CANCEL", 
                    emboss=False
                    ).collection_id=collection_id
            row.operator("flip_fluid_operators.preset_create_new_preset_enable_auto", 
                    text="", 
                    icon="AUTO", 
                    emboss=False
                    ).collection_id=collection_id
            row.prop(settings, export_id, icon="X", icon_only=True, emboss=False)

            column.box()
        column.separator()

        ui_properties = [x for x in column_data['properties']]
        if settings.ui_sort:
            new_ui_properties = ([x for x in ui_properties if x.enabled] +
                                 [x for x in ui_properties if not x.enabled])
            ui_properties = new_ui_properties

        for p in ui_properties:
            split_vals = p.path.split('.')
            prop_group = getattr(dummy_props, split_vals[1])
            identifier = split_vals[2]

            split = vcu.ui_split(column, factor=0.02, align=True)
            tick_column = split.column(align=True)
            temp_column = split.column(align=True)
            split = vcu.ui_split(temp_column, factor=0.42)
            label_column = split.column(align=True)
            temp_column = split.column(align=True)
            split = vcu.ui_split(temp_column, factor=0.02)
            lock_column = split.column()
            prop_column = split.column(align=True)
            prop_column = prop_column.row(align=True)

            tick_column.prop(p, 'enabled', 
                    icon="FILE_TICK" if p.enabled else "CANCEL", 
                    icon_only=True, 
                    emboss=False
                    )

            label_column.label(text=p.label)

            if p.path in is_key_property:
                lock_column.prop(p, 'dummy_prop', 
                    icon="KEY_HLT", 
                    icon_only=True, 
                    emboss=False
                    )
            elif p.path in is_keyed_property:
                unlocked = unlocked_status[p.path]
                lock_column.prop(p, 'dummy_prop', 
                    icon="UNLOCKED" if unlocked else "LOCKED", 
                    icon_only=True, 
                    emboss=False
                    )
                if not unlocked:
                    prop_column.enabled = False
                    lock_column.enabled = False

            prop_column.alert = not p.enabled

            prop = getattr(prop_group, identifier)
            if hasattr(prop, "is_min_max_property"):
                row = prop_column.row(align=True)
                row.prop(prop, "value_min", text="")
                row.prop(prop, "value_max", text="")
            else:
                if p.path in is_key_property:
                    prop_column.prop(prop_group, identifier, expand=True)
                else:
                    prop_column.prop(prop_group, identifier, text="")
        column.separator()
        column.separator()


    def draw_custom_properties(self, context, base_column):
        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.edit_preset_settings

        base_column.separator()
        base_column.separator()
        base_column.separator()

        split = vcu.ui_split(base_column, factor=1/6)
        column = split.column()
        column.label(text="Edit Preset Attributes:")
        column.box()
        column.separator()
        column = split.column()

        column = base_column.column()
        if settings.current_display_panel != 'NONE':
            row = column.row(align=True)
            row.alignment='LEFT'
            row.operator("flip_fluid_operators.preset_edit_preset_enable_all",
                         icon="FILE_TICK")
            row.operator("flip_fluid_operators.preset_edit_preset_disable_all",
                         icon="CANCEL")
            row.label(text="")
            row.prop(settings, "ui_sort")

            column.separator()
            column.separator()
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.operator("flip_fluid_operators.preset_edit_select_prev",
                         text="",
                         icon="TRIA_LEFT")
            row.prop(settings, "current_display_panel", expand=True)
            row.operator("flip_fluid_operators.preset_edit_select_next",
                         text="",
                         icon="TRIA_RIGHT")
        else:
            column.label(text="No panels selected for export...")


        column.separator()
        column.separator()
        column.separator()
        split = column.split()

        buffer_pct = 0.95
        column1 = split.column()
        temp_split = vcu.ui_split(column1, factor=buffer_pct)
        column1 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column2 = split.column()
        temp_split = vcu.ui_split(column2, factor=buffer_pct)
        column2 = temp_split.column(align=True)
        temp_column = temp_split.column()

        column3 = split.column()
        temp_split = vcu.ui_split(column3, factor=buffer_pct)
        column3 = temp_split.column(align=True)
        temp_column = temp_split.column()

        collection_id = settings.current_display_panel
        columns = settings.ui_properties.generate_columns3(collection_id, dprops.property_registry)
        self.draw_column(context, columns[0], column1)
        self.draw_column(context, columns[1], column2)
        self.draw_column(context, columns[2], column3)


    def draw(self, context):
        default_window_height = 30

        dprops = vcu.get_active_object(context).flip_fluid.domain
        settings = dprops.presets.edit_preset_settings
        package_info = preset_library.package_identifier_to_info(settings.package)

        base_column = self.layout.column()
        base_column.separator()
        split = vcu.ui_split(base_column, factor=0.01)
        column = split.column()
        for i in range(default_window_height):
            column.label(text="")

        base_column = split.column()

        split = base_column.split(align=True)
        name_column = split.column(align=True)
        export_column = split.column(align=True)

        name_column_split = vcu.ui_split(name_column, factor=0.95)
        name_column1 = name_column_split.column()
        name_column2 = name_column_split.column()

        split = vcu.ui_split(name_column1, factor=0.5)
        edit_select_column1 = split.column()
        edit_select_column2 = split.column()
        edit_select_column1.prop(settings, "edit_package")
        edit_select_column1.prop(settings, "edit_preset")
        name_column1.separator()

        if settings.edit_preset == 'PRESET_NONE':
            name_column1.label(text="No preset selected to edit...")
            return

        row = name_column1.row()
        row.label(text="Edit Preset Info:")
        row = row.row()
        row.alignment = "RIGHT"
        row.operator("flip_fluid_operators.preset_edit_reset", 
                icon="RECOVER_LAST", 
                text="", 
                emboss=False
                )
        name_column1.box()
        name_column1.separator()

        if package_info["use_custom_icons"]:
            split = vcu.ui_split(name_column1, factor=0.23)
            name_column_icon = split.column()
            name_column_left = split.column()
            split = vcu.ui_split(name_column_left, factor=0.25)
            name_column_left = split.column()
            name_column_right = split.column()
        else:
            split = vcu.ui_split(name_column1, factor=0.2)
            name_column_left = split.column()
            name_column_right = split.column()

        if package_info["use_custom_icons"]:
            name_column_icon.enabled = False
            name_column_icon.template_icon_view(settings, "display_icon")

        name_column_left.label(text="New Package: ")
        name_column_left.separator()
        name_column_left.separator()
        name_column_left.label(text="New Name: ")
        name_column_left.label(text="New Description: ")
        name_column_left.label(text="New Icon: ")

        name_column_right.prop(settings, 'package', text="")
        name_column_right.separator()
        name_column_right.separator()
        name_column_right.prop(settings, 'name', text="")
        name_column_right.prop(settings, 'description', text="")

        if package_info["use_custom_icons"]:
            name_column_right.prop_search(settings, "icon", bpy.data, "images", text="")
        else:
            name_column_right.label(text="(Custom icons are not enabled for this package)")

        split = vcu.ui_split(export_column, factor=0.95)
        export_column = split.column()
        export_column.label(text="Edit Export Panel Settings:")
        export_column.box()
        export_column.separator()
        export_column_split = export_column.split()
        export_column1 = export_column_split.column()
        export_column2 = export_column_split.column()
        export_column3 = export_column_split.column()

        export_column1.prop(settings, 'export_simulation')
        export_column1.prop(settings, 'export_display')
        export_column1.prop(settings, 'export_surface')
        export_column2.prop(settings, 'export_whitewater')
        export_column2.prop(settings, 'export_world')
        export_column2.prop(settings, 'export_materials')
        export_column3.prop(settings, 'export_advanced')
        export_column3.prop(settings, 'export_debug')
        export_column3.prop(settings, 'export_stats')

        self.draw_custom_properties(context, base_column)

        column.separator()
        column.separator()


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        settings = dprops.presets.edit_preset_settings
        if settings.edit_preset == 'PRESET_NONE':
            errmsg = "Error: No preset was selected for edit"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        if not settings.name:
            errmsg = "Error: Edited preset must have a name"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        package_info = preset_library.package_identifier_to_info(settings.package)
        if package_info["use_custom_icons"]:
            icon_img = bpy.data.images.get(settings.icon)
            if not icon_img:
                errmsg = "Error: No image icon selected"
                errdesc = ("This package uses custom image icons." +
                          " Import an image into the Blender UV/Image Editor and select" + 
                          " the image in the 'Create New Preset' popup dialog.")
                bpy.ops.flip_fluid_operators.display_error(
                        'INVOKE_DEFAULT',
                        error_message=errmsg,
                        error_description=errdesc,
                        popup_width=400
                        )
                return {'CANCELLED'}
        else:
            settings.icon = ""

        exported_props = settings.get_exported_ui_properties()
        if not exported_props:
            errmsg = "Error: Edited preset has no settings selected for export"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    popup_width=400
                    )
            return {'CANCELLED'}

        edit_preset_info = preset_library.preset_identifier_to_info(settings.edit_preset)
        edit_preset_name = edit_preset_info['name']
        is_editing_current_preset = dprops.presets.current_preset == settings.edit_preset

        preset_stack = dprops.presets.preset_stack
        stack_idx = preset_stack.remove_preset_from_stack_by_identifier(settings.edit_preset)

        preset_info_dict = settings.to_dict()
        error = preset_library.edit_user_preset(preset_info_dict)
        if error:
            errmsg = "Error: Unable to edit preset"
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message=errmsg,
                    error_description=error,
                    popup_width=400
                    )
            return {'CANCELLED'}

        if is_editing_current_preset:
            new_identifier = preset_info_dict['identifier']
            dprops.presets.current_preset = new_identifier

        if stack_idx != -1:
            new_identifier = preset_info_dict['identifier']
            preset_stack.insert_preset_into_stack(new_identifier, stack_idx)

        msg = "Successfully edited preset <" + edit_preset_name + "> -> <" + settings.name + ">"
        self.report({'INFO'}, msg)
        settings.reset();
        return {'FINISHED'}


    def cancel(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        settings.unload()


    def invoke(self, context, event):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        settings = dprops.presets.edit_preset_settings
        settings.initialize()
        return context.window_manager.invoke_props_dialog(self, width=1300)


def register():
    bpy.utils.register_class(FlipFluidPresetRestoreDefault)
    bpy.utils.register_class(FlipFluidPresetSaveUserDefault)
    bpy.utils.register_class(FlipFluidPresetRestoreSystemDefault)

    bpy.utils.register_class(FlipFluidPresetCreateNewPackage)
    bpy.utils.register_class(FlipFluidPresetDeletePackage)
    bpy.utils.register_class(FlipFluidPresetExportPackage)

    bpy.utils.register_class(SelectPresetPackageZipFile)
    bpy.utils.register_class(FlipFluidPresetImportPackageSelectPrevious)
    bpy.utils.register_class(FlipFluidPresetImportPackageSelectNext)
    bpy.utils.register_class(FlipFluidPresetImportPackageSelectPresetPrevious)
    bpy.utils.register_class(FlipFluidPresetImportPackageSelectPresetNext)
    bpy.utils.register_class(FlipFluidPresetImportPackage)

    bpy.utils.register_class(FlipFluidPresetCreateNewPreset)
    bpy.utils.register_class(FlipFluidPresetCreateNewPresetSelectPrevious)
    bpy.utils.register_class(FlipFluidPresetCreateNewPresetSelectNext)
    bpy.utils.register_class(FlipFluidPresetCreateNewPresetEnableAll)
    bpy.utils.register_class(FlipFluidPresetCreateNewPresetDisableAll)
    bpy.utils.register_class(FlipFluidPresetCreateNewPresetEnableAuto)
    bpy.utils.register_class(FlipFluidPresetCreateNewPresetReset)
    bpy.utils.register_class(FlipFluidPresetDeletePreset)

    bpy.utils.register_class(FlipFluidPresetEditPreset)
    bpy.utils.register_class(FlipFluidPresetEditPresetSelectPrevious)
    bpy.utils.register_class(FlipFluidPresetEditPresetSelectNext)
    bpy.utils.register_class(FlipFluidPresetEditPresetEnableAll)
    bpy.utils.register_class(FlipFluidPresetEditPresetDisableAll)
    bpy.utils.register_class(FlipFluidPresetEditPresetReset)

    bpy.utils.register_class(FlipFluidPresetSelectPrevious)
    bpy.utils.register_class(FlipFluidPresetSelectNext)

    bpy.utils.register_class(FlipFluidPresetDisplayInfoSelectPrevious)
    bpy.utils.register_class(FlipFluidPresetDisplayInfoSelectNext)
    bpy.utils.register_class(FlipFluidPresetDisplayInfo)

    bpy.utils.register_class(FlipFluidPresetAddPresetToStack)
    bpy.utils.register_class(FlipFluidPresetRemovePresetFromStack)
    bpy.utils.register_class(FlipFluidPresetMovePresetUpInStack)
    bpy.utils.register_class(FlipFluidPresetMovePresetDownInStack)
    bpy.utils.register_class(FlipFluidPresetApplyAndRemoveFromStack)


def unregister():
    bpy.utils.unregister_class(FlipFluidPresetRestoreDefault)
    bpy.utils.unregister_class(FlipFluidPresetSaveUserDefault)
    bpy.utils.unregister_class(FlipFluidPresetRestoreSystemDefault)

    bpy.utils.unregister_class(FlipFluidPresetCreateNewPackage)
    bpy.utils.unregister_class(FlipFluidPresetDeletePackage)
    bpy.utils.unregister_class(FlipFluidPresetExportPackage)

    bpy.utils.unregister_class(SelectPresetPackageZipFile)
    bpy.utils.unregister_class(FlipFluidPresetImportPackageSelectPrevious)
    bpy.utils.unregister_class(FlipFluidPresetImportPackageSelectNext)
    bpy.utils.unregister_class(FlipFluidPresetImportPackageSelectPresetPrevious)
    bpy.utils.unregister_class(FlipFluidPresetImportPackageSelectPresetNext)
    bpy.utils.unregister_class(FlipFluidPresetImportPackage)

    bpy.utils.unregister_class(FlipFluidPresetCreateNewPreset)
    bpy.utils.unregister_class(FlipFluidPresetCreateNewPresetSelectPrevious)
    bpy.utils.unregister_class(FlipFluidPresetCreateNewPresetSelectNext)
    bpy.utils.unregister_class(FlipFluidPresetCreateNewPresetEnableAll)
    bpy.utils.unregister_class(FlipFluidPresetCreateNewPresetDisableAll)
    bpy.utils.unregister_class(FlipFluidPresetCreateNewPresetEnableAuto)
    bpy.utils.unregister_class(FlipFluidPresetCreateNewPresetReset)
    bpy.utils.unregister_class(FlipFluidPresetDeletePreset)

    bpy.utils.unregister_class(FlipFluidPresetEditPreset)
    bpy.utils.unregister_class(FlipFluidPresetEditPresetSelectPrevious)
    bpy.utils.unregister_class(FlipFluidPresetEditPresetSelectNext)
    bpy.utils.unregister_class(FlipFluidPresetEditPresetEnableAll)
    bpy.utils.unregister_class(FlipFluidPresetEditPresetDisableAll)
    bpy.utils.unregister_class(FlipFluidPresetEditPresetReset)

    bpy.utils.unregister_class(FlipFluidPresetSelectPrevious)
    bpy.utils.unregister_class(FlipFluidPresetSelectNext)

    bpy.utils.unregister_class(FlipFluidPresetDisplayInfoSelectPrevious)
    bpy.utils.unregister_class(FlipFluidPresetDisplayInfoSelectNext)
    bpy.utils.unregister_class(FlipFluidPresetDisplayInfo)

    bpy.utils.unregister_class(FlipFluidPresetAddPresetToStack)
    bpy.utils.unregister_class(FlipFluidPresetRemovePresetFromStack)
    bpy.utils.unregister_class(FlipFluidPresetMovePresetUpInStack)
    bpy.utils.unregister_class(FlipFluidPresetMovePresetDownInStack)
    bpy.utils.unregister_class(FlipFluidPresetApplyAndRemoveFromStack)
