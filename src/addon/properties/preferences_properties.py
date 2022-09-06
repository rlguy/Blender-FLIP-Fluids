# Blender FLIP Fluids Add-on
# Copyright (C) 2022 Ryan L. Guy
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

import bpy, colorsys

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
    panel_ids = ['FLIPFLUID_PT_HelperPanelMain', 'FLIPFLUID_PT_HelperPanelDisplay']
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

    beginner_friendly_mode = BoolProperty(
                name="Beginner Friendly Mode",
                description="Beginner friendly mode will show only the most important settings"
                    " and hide more advanced settings that are not as commonly used in basic"
                    " simulations. Enabling this will simplify the UI and help you focus on the"
                    " simulation settings that matter the most while you learn. This setting is"
                    " also available from the FLIP Fluids sidebar menu",
                default=False,
                options={'HIDDEN'},
                )
    exec(vcu.convert_attribute_to_28("beginner_friendly_mode"))
    FAKE_PREFERENCES.beginner_friendly_mode = False

    beginner_friendly_mode_tooltip = BoolProperty(
            name="Beginner Friendly Mode Tooltip", 
            description="Beginner Friendly Mode hides all but the most important settings and"
                " can be disabled in the FLIP Fluids preferences menu (Edit > Preferences >"
                " Addons > FLIP Fluids)", 
            default=True,
            ); 
    exec(vcu.convert_attribute_to_28("beginner_friendly_mode_tooltip"))
    FAKE_PREFERENCES.beginner_friendly_mode_tooltip = True

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

    enable_experimental_build_warning = BoolProperty(
            name="Show Experimental Build Warning", 
            description="Disable to hide the experimental build warning/notification in the Physics menu", 
            default=True,
            ); 
    exec(vcu.convert_attribute_to_28("enable_experimental_build_warning"))
    FAKE_PREFERENCES.enable_experimental_build_warning = True

    enable_developer_tools = BoolProperty(
            name="Enable Developer Tools", 
            description="Enable Developer Tools. Enable to unlock features that may be experimental, not yet completed,"
                " or considered unstable due to current bugs in Blender. Not recommended for production use."
                " Developer tools are always enabled in an experimental build regardless of whether or not this"
                " option is enabled", 
            default=False,
            ); 
    exec(vcu.convert_attribute_to_28("enable_developer_tools"))
    FAKE_PREFERENCES.enable_developer_tools = False

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
        column.label(text="Mixbox Color Blending Plugin:")

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

            if installation_utils.is_mixbox_supported():
                box.label(text="Optional: The Mixbox color blending plugin may be installed below now or after completing installation", icon="INFO")
            
            box.operator(
                    "wm.url_open", 
                    text="FLIP Fluids Addon Installation Instructions", 
                    icon="URL"
                ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Addon-Installation-and-Uninstallation"

            if installation_utils.is_mixbox_supported():
                box.operator(
                        "wm.url_open", 
                        text="Mixbox Plugin Installation Instructions", 
                        icon="URL"
                    ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Mixbox-Installation-and-Uninstallation"

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
        helper_column.prop(self, "beginner_friendly_mode")
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
        row = helper_column.row()
        row.label(text="     Re-launch bake after crash:")
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

        self.draw_mixbox_menu(context)

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
        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "dismiss_T88811_crash_warning")
        row.operator(
                "wm.url_open", 
                text="Bug Report: T88811", 
            ).url = "https://developer.blender.org/T88811"
        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "dismiss_persistent_data_render_warning")
        row.operator(
                "wm.url_open", 
                text="Related Bug Reports", 
            ).url = "https://developer.blender.org/maniphest/query/D0zO31gPuhUc/#R"


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
