# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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

import bpy, colorsys, os, json

from bpy.props import (
        BoolProperty,
        StringProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        CollectionProperty,
        EnumProperty
        )

from ..objects import flip_fluid_map
from ..ui import helper_ui
from ..utils import installation_utils
from ..utils import color_utils
from ..utils import version_compatibility_utils as vcu
from ..operators import preferences_operators
from ..filesystem import filesystem_protection_layer as fpl
from .. import types


# Due to a bug in Blender 2.93 (https://developer.blender.org/T87629), preferences
# may not be accessible. In this case, a fake set of preferences can be used in 
# it's place with default values. The values will be populated in 
# FLIPFluidAddonPreferences
FAKE_PREFERENCES = flip_fluid_map.Map({})


def get_addon_preferences(context=None):
    if context is None:
        context = bpy.context
    id_name = __name__.split(".")[0]
    prefs = vcu.get_blender_preferences(context)
    if id_name not in prefs.addons:
        global FAKE_PREFERENCES
        return FAKE_PREFERENCES
    return prefs.addons[id_name].preferences


class FLIPFluidGPUDevice(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    name = StringProperty(); exec(conv("name"))
    description = StringProperty(); exec(conv("description"))
    score = FloatProperty(); exec(conv("score"))


class FLIPFluidColorMixbox(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    color = FloatVectorProperty(default=(0, 0, 0), subtype='COLOR', description="Color mix using Mixbox blending"); exec(conv("color"))


class FLIPFluidColorRGB(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    color = FloatVectorProperty(default=(0, 0, 0), subtype='COLOR', description="Color mix using basic RGB blending"); exec(conv("color"))


def update_helper_category_name(self, context):
    panel_ids = ['FLIPFLUID_PT_HelperPanelMain', 'FLIPFLUID_PT_HelperPanelDisplay', 'FLIPFLUID_PT_HelperTechnicalSupport']
    for pid in panel_ids:
        is_panel_registered = hasattr(bpy.types, pid)
        if is_panel_registered:
            try:
                bpy.utils.unregister_class(getattr(bpy.types, pid))
            except:
                pass

    if self.enable_helper:
        for pid in panel_ids:
            panel = getattr(helper_ui, pid)
            panel.bl_category = self.helper_category_name
            bpy.utils.register_class(panel)


class FLIPFluidAddonPreferences(bpy.types.AddonPreferences):
    global FAKE_PREFERENCES
    bl_idname = __name__.split(".")[0]

    enable_helper = BoolProperty(
                name="Enable Helper Sidebar",
                description="Enable the FLIP Fluid helper menu in the 3D view sidebar."
                    " This menu contains operators to help with workflow and simulation setup",
                default=True,
                update=lambda self, context: self._update_enable_helper(context),
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("enable_helper"))
    FAKE_PREFERENCES.enable_helper = True

    helper_category_name = StringProperty(
                name="Panel Category",
                description="Choose a category for the FLIP Fluids helper panel tab in the sidebar",
                default="FLIP Fluids",
                update=lambda self, context: self._update_helper_category_name(context),
                )
    exec(vcu.convert_attribute_to_28("helper_category_name"))
    FAKE_PREFERENCES.helper_category_name = "FLIP Fluids"

    show_documentation_in_ui = BoolProperty(
                name="Display documentation links in UI",
                description="Display relevant documentation links within the UI. Documentation links will open in your browser."
                    " This setting is also available from the FLIP Fluids sidebar menu",
                default=False,
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("show_documentation_in_ui"))
    FAKE_PREFERENCES.show_documentation_in_ui = False

    engine_debug_mode = BoolProperty(
            name="Engine Debug Mode", 
            description="Enable to run simulation engine in debug mode (slower, but is able to"
                " generate crash errors). Disabling can speed up simulation by 10% - 15%, but if"
                " a crash is encountered, no error messages will be generated. If encountering a"
                " persistent simulation crash, switch to debug mode and resume to check for error"
                " messages. Error messages are not guaranteed on a crash and will depend on system and"
                " situation. Running with debug mode on or off will not affect simulation results", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("engine_debug_mode"))
    FAKE_PREFERENCES.engine_debug_mode = False

    enable_addon_directory_renaming = BoolProperty(
            name="Allow Addon Directory Renaming", 
            description="For advanced installation. Enable to allow renaming of the default flip_fluids_addon"
                " folder in the Blender addons directory. Use to install multiple versions of the FLIP Fluids addon."
                " Ensure that only one version of the FLIP Fluids addon is enabled at any time and restart Blender"
                " after switching to another version. Do not use any special characters when renaming, including periods", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("enable_addon_directory_renaming"))
    FAKE_PREFERENCES.enable_addon_directory_renaming = False

    enable_blend_file_logging = BoolProperty(
            name="Save Blender Installation and Simulation Info to Blend File", 
            description="If enabled, save info about your Blender installation and simulation set up into the"
                " Blend file. Saving this info into the Blend file helps improve turnaround time when requesting"
                " technical support and improves accuracy when diagnosing issues. To view the type of info that is"
                " saved, use the [Help > FLIP Fluids > Copy System & Blend Info] operator. If disabled, this info"
                " will be cleared upon the next save of your Blend file, but it may be required to provide"
                " additional items and info when requesting support", 
            default=True,
            ); 
    exec(vcu.convert_attribute_to_28("enable_blend_file_logging"))
    FAKE_PREFERENCES.enable_blend_file_logging = True

    enable_experimental_build_warning = BoolProperty(
            name="Show Experimental Build Warning", 
            description="Disable to hide the experimental build warning/notification in the Physics menu", 
            default=True,
            ); 
    exec(vcu.convert_attribute_to_28("enable_experimental_build_warning"))
    FAKE_PREFERENCES.enable_experimental_build_warning = True

    enable_developer_tools = BoolProperty(
            name="Enable Developer Tools", 
            description="Enable to unlock developer tools and hidden features. Enable to unlock features"
                " that may be experimental or considered unstable for rendering due to current bugs in Blender."
                " Rendering issues can be completely avoided by rendering from the command line", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("enable_developer_tools"))
    FAKE_PREFERENCES.enable_developer_tools = False

    enable_support_tools = BoolProperty(
            name="Enable Technical Support Tools", 
            description="Used by the developers to assist in technical support requests", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("enable_support_tools"))
    FAKE_PREFERENCES.enable_support_tools = False

    cmd_save_before_launch = BoolProperty(
            name="Autosave Blend file before launching command line operators (Recommended)", 
            description="Command line operators require the Blend file to be saved for changes to take effect when using command"
            " line operators. If enabled, the Blend file will be automatically saved when using command line operators so that"
            " manual saving is not necessary", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("cmd_save_before_launch"))
    FAKE_PREFERENCES.cmd_save_before_launch = False

    cmd_bake_max_attempts = IntProperty(
            name="Max Attempts",
            description="When using the command line baking operator, if a bake fails due to a crash or an error, attempt"
                " to automatically re-launch and resume the baking process. This value is the maximum number of attempts that"
                " the addon will try to resume the baking process. Set a value greater than 0 to activate. Only supported on Windows OS",
            min=0,
            default=5,
            options={'HIDDEN'},
            )
    exec(vcu.convert_attribute_to_28("cmd_bake_max_attempts"))
    FAKE_PREFERENCES.cmd_bake_max_attempts = False

    enable_bake_alarm = BoolProperty(
            name="Play alarm after simulation finishes", 
            description="Play an alarm sound when the simulation baking process completes. The alarm will sound on both a"
                " successful bake as well as a bake where an error is encountered. This feature may not work correctly if"
                " a crash is encountered", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("enable_bake_alarm"))
    FAKE_PREFERENCES.enable_experimental_build_warning = False

    enable_presets = BoolProperty(
                name="Enable Presets",
                description="Presets are a deprecated feature that will no longer be updated. Enable to use the older preset"
                    " features, but be aware that you may encounter bugs or issues. Use at your own risk. Blender must be"
                    " restarted after enabling this option. See documentation for more info and future plans",
                default=False,
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("enable_presets"))
    FAKE_PREFERENCES.enable_presets = False

    selected_gpu_device = EnumProperty(
                name="GPU Compute Device",
                description="Device that will be used for GPU acceleration features",
                items=lambda self, context=None: self._get_gpu_device_enums(context),
                )
    exec(vcu.convert_attribute_to_28("selected_gpu_device"))
    FAKE_PREFERENCES.selected_gpu_device = None

    gpu_devices = CollectionProperty(type=FLIPFluidGPUDevice)
    exec(vcu.convert_attribute_to_28("gpu_devices"))
    FAKE_PREFERENCES.gpu_devices = []

    is_gpu_devices_initialized = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("is_gpu_devices_initialized"))
    FAKE_PREFERENCES.is_gpu_devices_initialized = False

    show_mixbox_menu = BoolProperty(default=False)
    exec(vcu.convert_attribute_to_28("show_mixbox_menu"))
    FAKE_PREFERENCES.show_mixbox_menu = False

    is_mixbox_installation_error = BoolProperty(default=False)
    exec(vcu.convert_attribute_to_28("is_mixbox_installation_error"))
    FAKE_PREFERENCES.is_mixbox_installation_error = False

    mixbox_installation_error_message = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("mixbox_installation_error_message"))
    FAKE_PREFERENCES.mixbox_installation_error_message = ""

    mixbox_color1 = FloatVectorProperty(  
                name="Color 1",
                subtype='COLOR',
                default=(0.0, 0.0, 0.24),
                min=0.0, max=1.0,
                description="Color Input 1",
                update=lambda self, context: self._update_mixbox_color_test(context),
                ); exec(vcu.convert_attribute_to_28("mixbox_color1"))

    mixbox_color2 = FloatVectorProperty(  
                name="Color 2",
                subtype='COLOR',
                default=(0.7, 0.7, 0.0),
                min=0.0, max=1.0,
                description="Color Input 2",
                update=lambda self, context: self._update_mixbox_color_test(context),
                ); exec(vcu.convert_attribute_to_28("mixbox_color2"))

    num_gradient_samples = IntProperty(default=25)
    exec(vcu.convert_attribute_to_28("num_gradient_samples"))
    FAKE_PREFERENCES.num_gradient_samples = 0

    mixbox_gradient_result = CollectionProperty(type=FLIPFluidColorMixbox)
    exec(vcu.convert_attribute_to_28("mixbox_gradient_result"))
    FAKE_PREFERENCES.mixbox_gradient_result = []

    rgb_gradient_result = CollectionProperty(type=FLIPFluidColorRGB)
    exec(vcu.convert_attribute_to_28("rgb_gradient_result"))
    FAKE_PREFERENCES.rgb_gradient_result = []

    test_mixbox_expanded = BoolProperty(
                default=False, 
                update=lambda self, context: self._update_mixbox_color_test(context)
                ); 
    exec(vcu.convert_attribute_to_28("test_mixbox_expanded"))

    preset_library_install_mode = EnumProperty(
            name="Preset Library Install Method",
            description="Installation Method",
            items=types.preset_library_install_modes,
            default='PRESET_LIBRARY_INSTALL_ZIP',
            options={'HIDDEN'},
            ); exec(vcu.convert_attribute_to_28("preset_library_install_mode"))

    preset_library_install_location = StringProperty(
            name="",
            description="Select a location to install the Preset Scenes Library."
                " This should be a location on your system where you have read and write file permissions",
            default="", 
            subtype='DIR_PATH',
            ); 
    exec(vcu.convert_attribute_to_28("preset_library_install_location"))
    FAKE_PREFERENCES.preset_library_install_location = ""

    is_preset_library_installation_error = BoolProperty(default=False)
    exec(vcu.convert_attribute_to_28("is_preset_library_installation_error"))
    FAKE_PREFERENCES.is_preset_library_installation_error = False

    preset_library_installation_error_message = StringProperty(default="")
    exec(vcu.convert_attribute_to_28("preset_library_installation_error_message"))
    FAKE_PREFERENCES.preset_library_installation_error_message = ""

    preset_library_installations_expanded = BoolProperty(default=True); 
    exec(vcu.convert_attribute_to_28("preset_library_installations_expanded"))

    dismiss_T88811_crash_warning = BoolProperty(
            name="Dismiss render crash bug warnings", 
            description="Dismiss warnings in UI when features are enabled that can trigger a"
                " bug in Blender (T88811) that can cause frequent render crashes or incorrect"
                " renders. The workaround to this issue is to render from the command line. See"
                " the FLIP Fluids sidebar helper menu for tools to help automatically launch a"
                " cmd render. This option can be reset in the addon preferences", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("dismiss_T88811_crash_warning"))
    FAKE_PREFERENCES.dismiss_T88811_crash_warning = False

    dismiss_persistent_data_render_warning = BoolProperty(
            name="Dismiss persistent data warnings", 
            description="Dismiss warnings in UI when the Cycles Persistent Data option is enabled."
            " This render option is not compatible with the simulation meshes and can cause render"
            " crashes, incorrect renders, or static renders. The workaround to this issue is to"
            " disable the 'Render Properties > Performance > Persistent Data' option or to render"
            " from the command line. See the FLIP Fluids sidebar helper menu for tools to help"
            " automatically launch a cmd render. This option can be reset in the addon preferences", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("dismiss_persistent_data_render_warning"))
    FAKE_PREFERENCES.dismiss_persistent_data_render_warning = False

    dismiss_rtx_driver_warning = BoolProperty(
            name="Dismiss NVIDIA GeForce RTX Driver Warning", 
            description="Dismiss warning in the FLIP Fluids preferences menu related to a recent NVIDIA"
                " GeForce RTX 'Game Ready Driver' update that may cause Blender to crash frequently when baking"
                " a simulation. If you are experiencing this issue, the current solution is to update to"
                " the NVIDIA 'Studio Driver' version. Studio drivers are typically more stable for content"
                " creation software",
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("dismiss_rtx_driver_warning"))
    FAKE_PREFERENCES.dismiss_rtx_driver_warning = False

    dismiss_export_animated_mesh_parented_relation_hint = BoolProperty(
            name="Dismiss 'Export Animated Mesh' parented relation hint", 
            description="Dismiss hints about enabling 'Export Animated Mesh' in the FLIP object UI"
                " when parented relations are detected. The 'Export Animated Mesh' option is required"
                " for any animation that is more complex than just keyframed loc/rot/scale or F-Curves,"
                " such as parented relations, armatures, animated modifiers, deformable meshes, etc."
                " This option is not needed for static objects",
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("dismiss_export_animated_mesh_parented_relation_hint"))
    FAKE_PREFERENCES.dismiss_export_animated_mesh_parented_relation_hint = False

    enable_tabbed_domain_settings = BoolProperty(
                name="Enable Tabbed Domain Settings (Recommended)",
                description="Enable tabbed domain settings view. If enabled, domain panel categories will be displayed"
                    " using a tab header selector. If disabled, the classic view will display all domain panel categories in a vertical stack",
                default=False,
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("enable_tabbed_domain_settings"))
    FAKE_PREFERENCES.enable_tabbed_domain_settings = False


    def is_developer_tools_enabled(self):
        return self.enable_developer_tools or installation_utils.is_experimental_build()


    def _update_enable_helper(self, context):
        update_helper_category_name(self, context)


    def _update_helper_category_name(self, context):
        update_helper_category_name(self, context)


    def _update_mixbox_color_test(self, context):
        c1 = self.mixbox_color1
        c2 = self.mixbox_color2

        if len(self.mixbox_gradient_result) != self.num_gradient_samples:
            self.mixbox_gradient_result.clear()
            for i in range(self.num_gradient_samples):
                self.mixbox_gradient_result.add()

        if len(self.rgb_gradient_result) != self.num_gradient_samples:
            self.rgb_gradient_result.clear()
            for i in range(self.num_gradient_samples):
                self.rgb_gradient_result.add()

        tstep = 1.0 / (self.num_gradient_samples - 1)
        for i in range(self.num_gradient_samples):
            t = i * tstep
            r, g, b = color_utils.mixbox_lerp_srgb32f(c1[0], c1[1], c1[2], c2[0], c2[1], c2[2], t)

            saturation_factor = installation_utils.get_mixbox_boost_factor()
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            s = min(s * saturation_factor, 1.0)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)

            self.mixbox_gradient_result[i].color = (r, g, b)

            r = (1.0 - t) * c1[0] + t * c2[0]
            g = (1.0 - t) * c1[1] + t * c2[1]
            b = (1.0 - t) * c1[2] + t * c2[2]
            self.rgb_gradient_result[i].color = (r, g, b)


    def draw_mixbox_menu(self, context):
        preferences = vcu.get_addon_preferences()
        preferences.show_mixbox_menu = True
        if not preferences.show_mixbox_menu:
            return

        is_installed = installation_utils.is_mixbox_installation_complete()

        box = self.layout.box()
        column = box.column(align=True)
        column.label(text="Install Mixbox Color Blending Plugin:")

        if not self.is_developer_tools_enabled():
            if installation_utils.is_mixbox_supported():
                column.label(text="Activate the 'Enable Developer Tools' option to access this feature:", icon='INFO')

                row = column.row(align=True)
                row.alignment = 'LEFT'
                row.prop(self, "enable_developer_tools")
                row.operator(
                    "wm.url_open", 
                    text="What are the developer tools and hidden features?", 
                    icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preferences-Menu-Settings#developer-tools"

                column.separator()
                column.operator(
                    "wm.url_open", 
                    text="Mixbox Installation Instructions", 
                    icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Mixbox-Installation-and-Uninstallation"
                return

        if not installation_utils.is_mixbox_supported():
            column.label(text="Mixbox color blending features are not supported in this version of the FLIP Fluids addon.", icon="ERROR")
            column.label(text="These features are only available in the full version.", icon="ERROR")
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="Learn more about the Mixbox pigment mixing technology here: ", icon='INFO')
            row = row.row(align=True)
            row.operator(
                "wm.url_open", 
                text="", 
                icon="URL"
            ).url = "https://scrtwpns.com/mixbox/"
            return
        
        if not vcu.is_blender_293():
            box.label(text="Blender 2.93 or later is required for this feature", icon='ERROR')

        column = box.column(align=True)
        column.enabled = vcu.is_blender_293()
        if not is_installed:
            subbox = column.box()
            sub_column = subbox.column(align=True)
            sub_column.label(text="Install the FLIP Fluids Mixbox Plugin to enable physically accurate color mixing and blending features.")
            row = sub_column.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="Learn more about the Mixbox pigment mixing technology here: ", icon='INFO')
            row = row.row(align=True)
            row.operator(
                "wm.url_open", 
                text="", 
                icon="URL"
            ).url = "https://scrtwpns.com/mixbox/"

            sub_column.label(text="The Mixbox plugin installation file can be found in FLIP Fluids addon downloads labeled as <Mixbox.plugin>.", icon="INFO")
            sub_column.label(text="Use the operator below to select and install the Mixbox.plugin file.", icon='INFO')

        subbox = column.box()
        sub_column = subbox.column(align=True)
        split = sub_column.split()
        column_left = split.column(align=True)
        column_right = split.column()

        if is_installed:
            column_left.operator("flip_fluid_operators.uninstall_mixbox_plugin", text="Uninstall Mixbox Plugin")
        else:
            column_left.operator("flip_fluid_operators.install_mixbox_plugin", text="Install Mixbox Plugin")
            column_left.separator()
            column_left.operator(
                        "wm.url_open", 
                        text="Mixbox Installation Instructions", 
                        icon="URL"
                    ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Mixbox-Installation-and-Uninstallation"

        if is_installed:
            column_right.label(text="Status: Installed", icon="CHECKMARK")
        else:
            column_right.alert = True
            column_right.label(text="Status: Not Installed", icon="CANCEL")

        if not is_installed and preferences.is_mixbox_installation_error:
            errmsg = preferences.mixbox_installation_error_message
            sub_column = subbox.column(align=True)
            sub_column.alert = True
            sub_column.label(text=errmsg, icon='ERROR')

        if is_installed:
            enable_mixing_widget = True
            if enable_mixing_widget:
                column.separator()
                subbox = column.box()

                row = subbox.row(align=True)
                row.prop(preferences, "test_mixbox_expanded",
                    icon="TRIA_DOWN" if preferences.test_mixbox_expanded else "TRIA_RIGHT",
                    icon_only=True, 
                    emboss=False
                )
                row.alignment = "LEFT"
                row.label(text="Test Mixbox:")

                if not preferences.test_mixbox_expanded:
                    row.prop(preferences, "mixbox_color1", text="")
                    row.prop(preferences, "mixbox_color2", text="")
                    row.label(text="(Expand to see gradient)")

                if preferences.test_mixbox_expanded:
                    sub_column = subbox.column(align=True)

                    split = vcu.ui_split(sub_column, factor=1/8)
                    column1 = split.column(align=True)
                    column2 = split.column(align=True)

                    row = column2.row(align=True)
                    row.label(text="Gradient Color1")
                    row.label(text="Gradient Color2")

                    row = column2.row(align=True)
                    row.prop(preferences, "mixbox_color1", text="")
                    row.prop(preferences, "mixbox_color2", text="")

                    sub_column.separator()

                    split = vcu.ui_split(sub_column, factor=1/8)
                    column1 = split.column(align=True)
                    column2 = split.column(align=True)

                    if len(self.mixbox_gradient_result) > 0:
                        column1.label(text="Mixbox:")
                        column1.label(text="RGB:")

                    row = column2.row(align=True)
                    for i in range(len(self.mixbox_gradient_result)):
                        c = self.mixbox_gradient_result[i]
                        row.prop(c, "color", text="")

                    row = column2.row(align=True)
                    for i in range(len(self.rgb_gradient_result)):
                        c = self.rgb_gradient_result[i]
                        row.prop(c, "color", text="")

                    sub_column = subbox.column(align=True)
                    row = sub_column.row(align=True)
                    row.alignment = 'LEFT'
                    row.label(text="Learn more about the Mixbox pigment mixing technology here: ", icon='INFO')
                    row = row.row(align=True)
                    row.operator(
                        "wm.url_open", 
                        text="", 
                        icon="URL"
                    ).url = "https://scrtwpns.com/mixbox/"


    def get_date_string(self, dd, mm, yyyy):
        month_to_str = {}
        month_to_str[1] = "jan"
        month_to_str[2] = "feb"
        month_to_str[3] = "mar"
        month_to_str[4] = "apr"
        month_to_str[5] = "may"
        month_to_str[6] = "jun"
        month_to_str[7] = "jul"
        month_to_str[8] = "aug"
        month_to_str[9] = "sep"
        month_to_str[10] = "oct"
        month_to_str[11] = "nov"
        month_to_str[12] = "dec"

        date_str = "(" + str(dd).zfill(2) + "-" + month_to_str[int(mm)] + "-" + str(yyyy) + ")"
        return date_str


    def draw_preset_library_menu(self, context):
        box = self.layout.box()
        box.label(text="Install Preset Scenes Library:")

        if not vcu.is_blender_33():
            box.label(text="Blender 3.3 or later is required for this feature", icon="ERROR")

        is_preset_library_supported = False
        if not is_preset_library_supported:
            column = box.column(align=True)
            column.label(text="Preset Library features are not supported in this version of the FLIP Fluids addon.", icon="ERROR")
            column.label(text="These features are only available in the full version.", icon="ERROR")
            row = column.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="Learn more about the Preset Scenes Library here: ", icon='INFO')
            row = row.row(align=True)
            row.operator(
                "wm.url_open", 
                text="", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preset-Library-Installation-and-Uninstallation"
            return

        subbox = box.box()
        column = subbox.column(align=True)
        column.label(text="This is an initial test phase for the new Preset Library integration into the", icon="INFO")
        column.label(text="Blender Asset Browser. Read more about this feature and known limitations here:", icon="INFO")
        column.operator(
                "wm.url_open", 
                text="Preset Library Installation and Notes", 
                icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preset-Library-Installation-and-Uninstallation"

        column = box.column(align=True)
        column.enabled = vcu.is_blender_33()

        row = column.row()
        row.prop(self, "preset_library_install_mode", expand=True)

        subbox = box.box()
        column = subbox.column(align=True)

        if self.preset_library_install_mode == 'PRESET_LIBRARY_INSTALL_ZIP':
            column.label(text="1. Select an install location")
            column.prop(self, "preset_library_install_location")

            location_text1 = ""
            location_text2 = ""
            if not self.preset_library_install_location:
                location_text1 = "No install location selected"
            else:
                install_path = os.path.join(self.preset_library_install_location, "FLIP_Fluids_Addon_Presets")
                location_text1 = "Preset Scenes Library will be installed to:"
                location_text2 = " "*12 + install_path

            column.label(text=location_text1, icon='INFO')
            if location_text2:
                row = column.row(align=True)
                row.enabled = False
                row.label(text=location_text2)
            else:
                column.label(text="")
            column.separator()

            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)

            column_left.label(text="2. Select and install Preset Scenes zip file")
            column_left.operator("flip_fluid_operators.install_preset_library", text="Install Preset Scenes Library")

            is_installed = installation_utils.is_preset_library_installation_complete()
            column_right.label(text="")
            if is_installed:
                column_right.label(text="Status: Installed", icon="CHECKMARK")
            else:
                column_right.alert = True
                column_right.label(text="Status: Not Installed", icon="CANCEL")

            if self.is_preset_library_installation_error:
                errmsg = self.preset_library_installation_error_message
                sub_column = subbox.column(align=True)
                sub_column.alert = True
                sub_column.label(text=errmsg, icon='ERROR')
        else:
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)

            column_left.operator("flip_fluid_operators.select_preset_library_folder", text="Select Preset Library Folder")

            is_installed = installation_utils.is_preset_library_installation_complete()
            if is_installed:
                column_right.label(text="Status: Installed", icon="CHECKMARK")
            else:
                column_right.alert = True
                column_right.label(text="Status: Not Installed", icon="CANCEL")

            if self.is_preset_library_installation_error:
                errmsg = self.preset_library_installation_error_message
                sub_column = subbox.column(align=True)
                sub_column.alert = True
                sub_column.label(text=errmsg, icon='ERROR')

        is_installed = installation_utils.is_preset_library_installation_complete()
        if is_installed:
            box.separator()
            subbox = box.box()

            row = subbox.row(align=True)
            row.prop(self, "preset_library_installations_expanded",
                icon="TRIA_DOWN" if self.preset_library_installations_expanded else "TRIA_RIGHT",
                icon_only=True, 
                emboss=False
            )
            row.alignment = "LEFT"

            preset_library_installations = installation_utils.get_preset_library_installations()
            if len(preset_library_installations) > 1:
                box_label = "Preset Library Installations:"
            else:
                box_label = "Preset Library Installation:"

            row.label(text=box_label)

            if self.preset_library_installations_expanded:
                for install_info in preset_library_installations:
                    name = install_info["name"]
                    path = install_info["path"]
                    metadata = install_info["metadata"]
                    date_string = self.get_date_string(metadata["date_dd"], metadata["date_mm"], metadata["date_yyyy"])

                    install_box = subbox.box()
                    column = install_box.column(align=True)
                    row = column.row(align=True)
                    row.label(text=name + " " + date_string, icon='KEYTYPE_BREAKDOWN_VEC')
                    row = row.row(align=True)
                    row.alignment = 'RIGHT'
                    row.operator("flip_fluid_operators.preset_library_copy_install_location", 
                            text="Copy Install Location", 
                            icon='COPYDOWN'
                            ).install_location = install_info["install_path"]
                    row = row.row(align=True)
                    row.alignment = 'RIGHT'
                    row.alert = True
                    op = row.operator("flip_fluid_operators.uninstall_preset_library", text="Uninstall", icon='X')
                    op.install_info_json_string = json.dumps(install_info)

                    row = column.row(align=True)
                    row.operator("wm.path_open", 
                            text="", 
                            icon='FILE_FOLDER'
                            ).filepath = install_info["path"]
                    row = row.row(align=True)
                    row.enabled = False
                    row.label(text="    Path: " + path)


    def draw(self, context):
        is_installation_complete = installation_utils.is_installation_complete()
        column = self.layout.column(align=True)
        if not is_installation_complete:
            box = column.box()
            box.label(text="IMPORTANT: Please Complete Installation", icon='ERROR')
            row = box.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="To complete installation of the FLIP Fluids addon, click here: ")
            row.operator("flip_fluid_operators.complete_installation", icon='MOD_FLUIDSIM')
            box.label(text="Or you may restart Blender to complete installation")
            box.label(text="Preferences will become available after the installation is complete")
            box.label(text="Optional: The Mixbox color blending plugin may be installed below now or after completing installation", icon="INFO")
            box.operator(
                    "wm.url_open", 
                    text="FLIP Fluids Addon Installation Instructions", 
                    icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Addon-Installation-and-Uninstallation"
            box.operator(
                    "wm.url_open", 
                    text="Mixbox Plugin Installation Instructions", 
                    icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Mixbox-Installation-and-Uninstallation"

        show_rtx_driver_warning = False  # Fixed in recent drivers (~January 2023)
        if not self.dismiss_rtx_driver_warning and show_rtx_driver_warning:
            model_search_string = "RTX"
            gpu_model_string = preferences_operators.get_gpu_string()
            if model_search_string in gpu_model_string:
                column = self.layout.column(align=True)
                box = column.box()
                column = box.column(align=True)
                column.alert = True
                column.label(text="Warning: Potential NVIDIA GeForce RTX Driver Incompatibility", icon='ERROR')
                column = box.column(align=True)
                column.label(text="GPU Model: " + gpu_model_string, icon="INFO")
                column.label(text="    A recent NVIDIA RTX 'Game Ready Driver' update may cause frequent Blender crashes.")
                column.label(text="    It is recommented to update to the NVIDIA RTX 'Studio Drivers' that are typically more stable")
                column.label(text="    when using content creation software.")
                column.label(text="    If you are already running the Studio Drivers, ignore this message.")
                column.separator()
                box.operator(
                        "wm.url_open", 
                        text="Click for more information about this issue", 
                        icon="URL"
                    ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/issues/599"
                box.operator(
                        "wm.url_open", 
                        text="Download NVIDIA Drivers", 
                        icon="URL"
                    ).url = "https://www.nvidia.com/en-us/geforce/drivers/"
                box.prop(self, "dismiss_rtx_driver_warning", text="Dismiss this warning", toggle=1, icon='X')

        if vcu.is_blender_28() and not vcu.is_blender_281():
            box = column.box()
            box.label(text="WARNING: Blender 2.80 contains bugs that can cause frequent crashes", icon='ERROR')
            box.label(text="     during render, Alembic export, and rigid/cloth simulation baking.")
            box.separator()
            box.label(text="     Blender version 2.81 or higher is recommended.")
            box.separator()
            box.operator(
                    "wm.url_open", 
                    text="Blender 2.80 Known Issues and Workarounds", 
                    icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Blender-2.8-Support#known-issues"
            column.separator()
            column.separator()

        """
        if vcu.is_blender_28():
            box = column.box()
            box.label(text="Reminder: It is necessary to lock the Blender interface during render to ", icon='INFO')
            box.label(text="     prevent crashes (Blender > Render > Lock Interface).")
        """

        box = self.layout.box()
        box.enabled = is_installation_complete
        helper_column = box.column(align=True)
        helper_column.label(text="UI Options:")
        helper_column.prop(self, "enable_tabbed_domain_settings")
        helper_column.prop(self, "show_documentation_in_ui")

        row = helper_column.row()
        row.alignment = 'LEFT'
        row.prop(self, "enable_helper")
        row = row.row()
        row.alignment = 'LEFT'
        row.enabled = self.enable_helper
        row.prop(self, "helper_category_name")
        helper_column.separator()

        box = self.layout.box()
        box.enabled = is_installation_complete
        helper_column = box.column(align=True)
        helper_column.label(text="Command Line Tools:")
        row = helper_column.row(align=True)
        row.prop(self, "cmd_save_before_launch")
        row = helper_column.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Re-launch bake after crash:", icon='FILE_REFRESH')
        row.prop(self, "cmd_bake_max_attempts")
        row.label(text="")
        helper_column.separator()

        if vcu.is_blender_28():
            box = self.layout.box()
            box.enabled = is_installation_complete
            helper_column = box.column(align=True)
            helper_column.label(text="Sounds:")
            row = helper_column.row(align=True)
            row.alignment = 'LEFT'
            row.prop(self, "enable_bake_alarm")
            row.operator("flip_fluid_operators.test_bake_alarm", icon='PLAY_SOUND')

        box = self.layout.box()
        box.enabled = is_installation_complete
        helper_column = box.column(align=True)
        helper_column.label(text="Experimental & Debug Tools:")

        if installation_utils.is_experimental_build():
            helper_column.prop(self, "enable_experimental_build_warning")

        row = helper_column.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "enable_developer_tools")
        row.operator(
            "wm.url_open", 
            text="What are the developer tools and hidden features?", 
            icon="URL"
        ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Preferences-Menu-Settings#developer-tools"

        helper_column.prop(self, "engine_debug_mode")
        helper_column.prop(self, "enable_addon_directory_renaming")
        helper_column.prop(self, "enable_blend_file_logging")
        helper_column.prop(self, "enable_support_tools")

        self.draw_mixbox_menu(context)
        self.draw_preset_library_menu(context)

        """
        helper_column.separator()
        helper_column.label(text="Deprecated Features:")
        helper_column.prop(self, "enable_presets")

        helper_column.operator(
                "wm.url_open", 
                text="Why Are Preset Features Deprecated?", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Preset-Settings"
        """

        box = self.layout.box()
        box.enabled = is_installation_complete
        column = box.column(align=True)
        split = column.split()
        column_left = split.column(align=True)
        column_right = split.column()
        
        column_left.label(text="Help and Support:")
        column_left.operator(
                "wm.url_open", 
                text="Frequently Asked Questions", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Frequently-Asked-Questions"
        column_left.operator(
                "wm.url_open", 
                text="Scene Troubleshooting Tips", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting"
        column_left.operator(
                "wm.url_open", 
                text="Example Scenes", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Example-Scene-Descriptions"
        column_left.operator(
                "wm.url_open", 
                text="Tutorials and Learning Resources", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Video-Learning-Series"

        column_left.label(text="Report a Bug:")
        column_left.operator(
                "wm.url_open", 
                text="Bug Report Guidelines", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Guidelines-for-Reporting-Bugs-and-Issues"
        column_left.operator("flip_fluid_operators.report_bug_prefill", icon="URL")
        column_left.operator("flip_fluid_operators.copy_system_info", icon="COPYDOWN")

        column = box.column(align=True)
        column.label(text="Reports can also be sent through official marketplaces or to support@flipfluids.com")

        box = self.layout.box()
        box.enabled = is_installation_complete
        column = box.column(align=True)
        split = column.split()
        column_left = split.column(align=True)
        column_right = split.column()

        column_left.label(text="Info and Links:")
        column_left.operator(
                "wm.url_open", 
                text="Documentation and Wiki", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki"
        column_left.operator(
                "wm.url_open", 
                text="Recommended Documentation Topics", 
                icon="URL"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki#the-most-important-documentation-topics"
        column_left.operator(
                "wm.url_open", 
                text="FLIP Fluids Homepage", 
                icon="URL"
            ).url = "http://flipfluids.com"

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
            ).url = "https://www.youtube.com/FLIPFluids"

        box = self.layout.box()
        box.enabled = is_installation_complete
        column = box.column()
        column.label(text="Warnings and Errors:")

        split = vcu.ui_split(column, factor=0.666, align=True)
        column_left = split.column(align=True)
        column_right = split.column(align=True)

        row = column_left.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "dismiss_T88811_crash_warning")

        row = column_left.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "dismiss_persistent_data_render_warning")

        if show_rtx_driver_warning:
            row = column_left.row(align=True)
            row.alignment = 'LEFT'
            row.prop(self, "dismiss_rtx_driver_warning")

        row = column_right.row(align=True)
        row.alignment = 'EXPAND'
        row.operator(
                "wm.url_open", 
                text="Bug Report: T88811", 
            ).url = "https://projects.blender.org/blender/blender/issues/88811"

        row = column_right.row(align=True)
        row.alignment = 'EXPAND'
        row.operator(
                "wm.url_open", 
                text="Related Bug Reports", 
            ).url = "https://projects.blender.org/blender/blender/issues?type=all&state=open&labels=&milestone=0&project=0&assignee=0&poster=0&q=Persistent+Data"

        row = column_left.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "dismiss_export_animated_mesh_parented_relation_hint")

        if show_rtx_driver_warning:
            row = column_right.row(align=True)
            row.alignment = 'EXPAND'
            row.operator(
                    "wm.url_open", 
                    text="Click for More Info", 
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/issues/599"

        row = column_right.row(align=True)
        row.alignment = 'EXPAND'
        row.operator(
                "wm.url_open", 
                text="Mesh Export Documentation", 
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Obstacle-Object-Settings#mesh-data-export"


    def _get_gpu_device_enums(self, context=None):
        device_enums = []
        for d in self.gpu_devices:
            device_enums.append((d.name, d.name, d.description))
        return device_enums


def load_post():
    id_name = __name__.split(".")[0]
    preferences = vcu.get_addon_preferences()
    if not preferences.enable_helper:
        helper_ui.unregister()

    installation_utils.update_mixbox_installation_status()
    preferences.is_mixbox_installation_error = False
    preferences.mixbox_installation_error_message = ""

    installation_utils.update_preset_library_installation_status()
    preferences.is_preset_library_installation_error = False
    preferences.preset_library_installation_error_message = ""


def register():
    bpy.utils.register_class(FLIPFluidGPUDevice)
    bpy.utils.register_class(FLIPFluidColorMixbox)
    bpy.utils.register_class(FLIPFluidColorRGB)
    bpy.utils.register_class(FLIPFluidAddonPreferences)

    id_name = __name__.split(".")[0]
    preferences = vcu.get_addon_preferences()
    update_helper_category_name(preferences, bpy.context)


def unregister():
    bpy.utils.unregister_class(FLIPFluidGPUDevice)
    bpy.utils.unregister_class(FLIPFluidColorMixbox)
    bpy.utils.unregister_class(FLIPFluidColorRGB)
    bpy.utils.unregister_class(FLIPFluidAddonPreferences)
