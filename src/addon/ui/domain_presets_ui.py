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

import bpy

from ..presets import preset_library
from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_DomainTypePresetsPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Presets"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def draw_preset_selector(self, context):
        obj = vcu.get_active_object(context)
        dprops = obj.flip_fluid.domain
        preprops = dprops.presets

        column = self.layout.column()
        column.prop(preprops, "enable_presets")

        column = self.layout.column()
        column.enabled = preprops.enable_presets
        column.label(text="Preset Package:")
        column.prop(preprops, "current_package", text="")

        current_package_info = \
            preset_library.package_identifier_to_info(preprops.current_package)

        if current_package_info["use_custom_icons"]:
            column.label(text="Preset:")
            row = column.row()
            row.prop(preprops, "current_preset", text="")
            if preprops.current_preset != "PRESET_NONE":
                row.operator(
                        "flip_fluid_operators.preset_display_info",
                        text="",
                        icon="INFO",
                        )

            row = column.row()
            subcol = row.column()
            subcol.scale_y = 6
            subcol.operator(
                    "flip_fluid_operators.preset_select_previous",
                    text="",
                    icon="TRIA_LEFT"
                    )

            subcol = row.column()
            subcol.template_icon_view(preprops, "current_preset", show_labels=True)

            subcol = row.column()
            subcol.scale_y = 6
            subcol.operator(
                    "flip_fluid_operators.preset_select_next",
                    text="",
                    icon="TRIA_RIGHT"
                    )

            split = column.split()
            column_left = split.column()
            column_right = split.column()
            row_left = column_left.row()
            row_right = column_right.row()

            row_left.alignment = 'LEFT'
            row_left.prop(preprops, "preview_preset", text="Auto Assign Preset")

            if preprops.current_preset != "PRESET_NONE":
                is_on_stack = preprops.preset_stack.is_preset_in_stack(preprops.current_preset)
                op_text = "Added to Stack" if is_on_stack else "Add to Stack"

                row_right.enabled = not is_on_stack
                row_right.alignment = 'RIGHT'
                row_right.operator(
                        "flip_fluid_operators.preset_add_to_stack",
                        text=op_text,
                        )
        else:
            column.label(text="Preset:")
            row = column.row()
            row.prop(preprops, "current_preset", text="")
            if preprops.current_preset != "PRESET_NONE":
                row.operator(
                        "flip_fluid_operators.preset_display_info",
                        text="",
                        icon="INFO",
                        )

            split = column.split()
            column_left = split.column()
            column_right = split.column()
            row_left = column_left.row()
            row_right = column_right.row()

            row_left.alignment = 'LEFT'
            row_left.prop(preprops, "preview_preset", text="Auto Assign Preset")

            if preprops.current_preset != "PRESET_NONE":
                is_on_stack = preprops.preset_stack.is_preset_in_stack(preprops.current_preset)
                op_text = "Added to Stack" if is_on_stack else "Add to Stack"

                row_right.enabled = not is_on_stack
                row_right.alignment = 'RIGHT'
                row_right.operator(
                        "flip_fluid_operators.preset_add_to_stack",
                        text=op_text,
                        )


    def draw_preset_stack(self, context):
        obj = vcu.get_active_object(context)
        preprops = obj.flip_fluid.domain.presets

        column = self.layout.column()
        column.enabled = preprops.enable_presets
        column.separator()
        column.separator()
        box = column.box()
        box.label(text="Preset Stack:")
        column = box.column(align=True)
        preset_icons = preset_library.get_custom_icons()
        if len(preprops.preset_stack.preset_stack) == 0:
            column.label(text="No presets loaded...")
        for pidx,p in enumerate(preprops.preset_stack.preset_stack):
            info = preset_library.preset_identifier_to_info(p.identifier)
            subbox = column.box()
            split = vcu.ui_split(subbox, factor=0.5, align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            row_left = column_left.row(align=True)
            row_right = column_right.row()

            if "icon" in info and info['icon'] in preset_icons:
                row_left.label(text=info['name'], icon_value=preset_icons.get(info['icon']).icon_id)
            else:
                row_left.label(text=" "*5 + info['name'])

            row_right.alignment='RIGHT'
            row_right.operator(
                        "flip_fluid_operators.preset_display_info",
                        text="",
                        icon="INFO",
                        emboss=False,
                        ).identifier = p.identifier
            row_right.operator(
                        "flip_fluid_operators.preset_apply_remove_from_stack",
                        ).stack_index=pidx
            row_right.prop(p, "is_enabled", text="", icon='RESTRICT_VIEW_OFF')
            row_right = row_right.row(align=True)
            row_right.operator(
                        "flip_fluid_operators.preset_move_up_in_stack",
                        text="",
                        icon="TRIA_UP",
                        ).stack_index=pidx
            row_right.operator(
                        "flip_fluid_operators.preset_move_down_in_stack",
                        text="",
                        icon="TRIA_DOWN",
                        ).stack_index=pidx
            row_right = row_right.row()
            row_right.operator(
                        "flip_fluid_operators.preset_remove_from_stack",
                        text="",
                        icon="X",
                        emboss=False,
                        ).stack_index=pidx


    def draw_preset_manager(self, context):
        obj = vcu.get_active_object(context)
        preprops = obj.flip_fluid.domain.presets

        self.layout.separator()
        box = self.layout.box()
        row = box.row()
        row.prop(preprops, "preset_manager_expanded",
            icon="TRIA_DOWN" if preprops.preset_manager_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label(text="Preset Manager")
        if preprops.preset_manager_expanded:
            column = box.column(align=True)
            column.label(text="Package Operators:")
            column.operator("flip_fluid_operators.preset_create_new_package")
            column.operator("flip_fluid_operators.preset_delete_package")
            column.separator()

            # These operators need to be reworked to support both 2.79 and 2.80
            """
            split = column.split(align=True)
            split_column = split.column(align=True)
            split_column.enabled = bool(preprops.import_package_settings.package_filepath)
            split_column.operator("flip_fluid_operators.preset_import_package")
            split_column = split.column(align=True)
            row = split_column.row(align=True)
            row.prop(preprops.import_package_settings, "package_filepath")
            row.operator("flip_fluid_operators.select_package_zipfile", text="", icon=vcu.get_file_folder_icon())

            row = column.row(align=True)
            row.operator("flip_fluid_operators.preset_export_package")
            row.prop(preprops.export_package_settings, "export_directory")
            """

            column = box.column(align=True)
            column.label(text="Preset Operators:")
            column.operator("flip_fluid_operators.preset_create_new_preset")
            column.operator("flip_fluid_operators.preset_delete_preset")
            column.operator("flip_fluid_operators.preset_edit_preset")


    def draw_default_settings_operators(self, context):
        self.layout.separator()
        box = self.layout.box()
        column = box.column(align=True)
        column.label(text="Default Settings:")
        split = vcu.ui_split(column, align=True, factor=0.66)
        column = split.column(align=True)
        column.operator(
                "flip_fluid_operators.preset_save_user_default_settings", 
                text="Save", 
                icon='FILE_TICK'
                )
        column = split.column(align=True)
        column.operator(
                "flip_fluid_operators.preset_restore_system_default_settings", 
                text="Restore",
                )


    def draw(self, context):
        if not preset_library.get_user_package_info_list():
            self.layout.label(text="This feature is missing data and will be disabled.")
            self.layout.label(text="Please contact the developers if you think this is an error.")
            return

        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        self.draw_preset_selector(context)
        self.draw_preset_stack(context)

        if show_advanced:
            self.draw_preset_manager(context)
            self.draw_default_settings_operators(context)


def register():
    preferences = vcu.get_addon_preferences()
    if preferences.enable_presets:
        bpy.utils.register_class(FLIPFLUID_PT_DomainTypePresetsPanel)


def unregister():
    try:
        bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypePresetsPanel)
    except:
        pass
