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

import bpy, os, subprocess, platform
from bpy.props import (
        StringProperty
        )

from ..utils import version_compatibility_utils as vcu
from .. import render


def _select_make_active(context, active_object):
    for obj in context.selected_objects:
        vcu.select_set(obj, False)
    vcu.select_set(active_object, True)
    vcu.set_active_object(active_object, context)


class FlipFluidHelperSelectDomain(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_domain"
    bl_label = "Select Domain"
    bl_description = "Select the domain object"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}
        _select_make_active(context, domain)
        return {'FINISHED'}


class FlipFluidHelperSelectSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_surface"
    bl_label = "Select Surface"
    bl_description = "Select the fluid surface object"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        surface_object = dprops.mesh_cache.surface.get_cache_object()
        if surface_object is None:
            return {'CANCELLED'}
        _select_make_active(context, surface_object)
        return {'FINISHED'}


class FlipFluidHelperSelectFoam(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_foam"
    bl_label = "Select Foam"
    bl_description = "Select the whitewater foam object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        foam_object = dprops.mesh_cache.foam.get_cache_object()
        if foam_object is None:
            return {'CANCELLED'}
        _select_make_active(context, foam_object)
        return {'FINISHED'}



class FlipFluidHelperSelectBubble(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_bubble"
    bl_label = "Select Bubble"
    bl_description = "Select the whitewater bubble object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        bubble_object = dprops.mesh_cache.bubble.get_cache_object()
        if bubble_object is None:
            return {'CANCELLED'}
        _select_make_active(context, bubble_object)
        return {'FINISHED'}


class FlipFluidHelperSelectSpray(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_spray"
    bl_label = "Select Spray"
    bl_description = "Select the whitewater spray object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        spray_object = dprops.mesh_cache.spray.get_cache_object()
        if spray_object is None:
            return {'CANCELLED'}
        _select_make_active(context, spray_object)
        return {'FINISHED'}


class FlipFluidHelperAddObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_add_objects"
    bl_label = "Add Objects"
    bl_description = "Add selected objects as FLIP Fluid objects"

    object_type = StringProperty("TYPE_NONE")
    exec(vcu.convert_attribute_to_28("object_type"))


    @classmethod
    def poll(cls, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                return True
        return False


    def execute(self, context):
        original_active_object = vcu.get_active_object(context)
        for obj in context.selected_objects:
            if not obj.type == 'MESH':
                continue
            vcu.set_active_object(obj, context)
            bpy.ops.flip_fluid_operators.flip_fluid_add()
            obj.flip_fluid.object_type = self.object_type
        vcu.set_active_object(original_active_object, context)
        return {'FINISHED'}


class FlipFluidHelperRemoveObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_remove_objects"
    bl_label = "Remove Objects"
    bl_description = "Remove selected objects from FLIP Fluid simulation"

    @classmethod
    def poll(cls, context):
        for obj in context.selected_objects:
            if obj.flip_fluid.is_active:
                return True
        return False


    def execute(self, context):
        original_active_object = vcu.get_active_object(context)
        for obj in context.selected_objects:
            if not obj.type == 'MESH':
                continue
            vcu.set_active_object(obj, context)
            bpy.ops.flip_fluid_operators.flip_fluid_remove()
        vcu.set_active_object(original_active_object, context)
        return {'FINISHED'}


class FlipFluidHelperSetObjectViewportDisplay(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_set_object_viewport_display"
    bl_label = "Object Viewport Display"
    bl_description = "Set how selected objects are displayed in the viewport"

    display_mode = StringProperty("TYPE_NONE")
    exec(vcu.convert_attribute_to_28("display_mode"))


    @classmethod
    def poll(cls, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                return True
        return False


    def execute(self, context):
        for obj in context.selected_objects:
            if not obj.type == 'MESH':
                continue
            if self.display_mode == 'DISPLAY_MODE_SOLID':
                vcu.set_object_display_type(obj, 'TEXTURED')
                obj.show_wire = False
                obj.show_all_edges = False
            elif self.display_mode == 'DISPLAY_MODE_WIREFRAME':
                vcu.set_object_display_type(obj, 'WIRE')
                obj.show_wire = True
                obj.show_all_edges = True

        return {'FINISHED'}


class FlipFluidHelperLoadLastFrame(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_load_last_frame"
    bl_label = "Load Last Frame"
    bl_description = "Load the most recently computed frame"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        if render.is_rendering():
            # Setting a frame during render will disrupt the render process
            return {'CANCELLED'}

        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_dir = dprops.cache.get_cache_abspath()
        bakefiles_dir = os.path.join(cache_dir, "bakefiles")
        if not os.path.exists(bakefiles_dir):
            return {'CANCELLED'}

        bakefiles = os.listdir(bakefiles_dir)
        max_frameno = -1
        for f in bakefiles:
            base = f.split(".")[0]
            frameno = int(base[-6:])
            max_frameno = max(frameno, max_frameno)
        context.scene.frame_set(max_frameno)
        return {'FINISHED'}


class FlipFluidEnableWhitewaterMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_whitewater_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_whitewater_simulation")


class FlipFluidEnableWhitewaterSimulation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_whitewater_simulation"
    bl_label = "Enable Whitewater Simulation"
    bl_description = "Enable Whitewater Simulation"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.whitewater.enable_whitewater_simulation = True
        if not dprops.render.whitewater_display_settings_expanded:
            dprops.render.whitewater_display_settings_expanded = True
        return {'FINISHED'}


class FlipFluidDisplayEnableWhitewaterTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.display_enable_whitewater_tooltip"
    bl_label = "Enable Whitewater Tooltip"
    bl_description = "Enable whitewater simulation"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_whitewater_menu")
        return {'FINISHED'}


class FlipFluidHelperCommandLineBake(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake"
    bl_label = "Launch Bake"
    bl_description = ("Launch a new command line window and start baking." +
                     " The .blend file will need to be saved before using" +
                     " this operator")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        script_path = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.dirname(script_path)
        script_path = os.path.join(script_path, "resources", "command_line_scripts", "run_simulation.py")

        system = platform.system()
        if system == "Windows":
            if vcu.is_blender_28():
                blender_exe_path = bpy.app.binary_path
            else:
                # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
                # executable path, so we'll just use blender.exe and hope that no other addon has
                # changed Blender's working directory
                blender_exe_path = "blender.exe"
            command = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "--python", script_path]
        elif system == "Darwin":
            # Feature not available on MacOS
            return {'CANCELLED'}
        elif system == "Linux":
            # Feature not available on Linux
            return {'CANCELLED'}

        subprocess.call(command, shell=True)

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""

        info_msg = "Launched command line baking window. If the baking process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line baking, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Baking-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineBakeToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake_to_clipboard"
    bl_label = "Copy Bake Command to Clipboard"
    bl_description = ("Copy command for baking to your system clipboard." +
                     " The .blend file will need to be saved before using" +
                     " this operator")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        script_path = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.dirname(script_path)
        script_path = os.path.join(script_path, "resources", "command_line_scripts", "run_simulation.py")

        system = platform.system()
        if system == "Windows":
            if vcu.is_blender_28():
                blender_exe_path = bpy.app.binary_path
            else:
                # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
                # executable path, so we'll just use blender.exe and hope that no other addon has
                # changed Blender's working directory
                blender_exe_path = "blender.exe"
            command = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "--python", script_path]
        elif system == "Darwin":
            # Feature not available on MacOS
            return {'CANCELLED'}
        elif system == "Linux":
            # Feature not available on Linux
            return {'CANCELLED'}

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
        bpy.context.window_manager.clipboard = command_text

        info_msg = "Copied the following baking command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line baking, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Baking-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRender(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render"
    bl_label = "Launch Render"
    bl_description = ("Launch a new command line window and start rendering the animation." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):        
        system = platform.system()
        if system == "Windows":
            if vcu.is_blender_28():
                blender_exe_path = bpy.app.binary_path
            else:
                # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
                # executable path, so we'll just use blender.exe and hope that no other addon has
                # changed Blender's working directory
                blender_exe_path = "blender.exe"
            command = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "-a"]
        elif system == "Darwin":
            # Feature not available on MacOS
            return {'CANCELLED'}
        elif system == "Linux":
            # Feature not available on Linux
            return {'CANCELLED'}

        subprocess.call(command, shell=True)

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" -a"

        info_msg = "Launched command line render window. If the render process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Rendering-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRenderToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render_to_clipboard"
    bl_label = "Launch Render"
    bl_description = ("Copy command for rendering to your system clipboard." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        system = platform.system()
        if system == "Windows":
            if vcu.is_blender_28():
                blender_exe_path = bpy.app.binary_path
            else:
                # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
                # executable path, so we'll just use blender.exe and hope that no other addon has
                # changed Blender's working directory
                blender_exe_path = "blender.exe"
            command = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "-a"]
        elif system == "Darwin":
            # Feature not available on MacOS
            return {'CANCELLED'}
        elif system == "Linux":
            # Feature not available on Linux
            return {'CANCELLED'}

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" -a"
        bpy.context.window_manager.clipboard = command_text

        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Rendering-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperStableRendering279(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_stable_rendering_279"
    bl_label = "Enable Stable Rendering"
    bl_description = ("Activate to prevent crashes and incorrect results during render."
                      " Activation will automatically set the Render Display Mode to"
                      " 'Full Screen' (Properties > Render > Display) and is a recommendation"
                      " to prevent viewport instability")


    @classmethod
    def poll(cls, context):
        return context.scene.render.display_mode != 'SCREEN'


    def execute(self, context):
        context.scene.render.display_mode = 'SCREEN'
        return {'FINISHED'}


class FlipFluidHelperStableRendering28(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_stable_rendering_28"
    bl_label = "Enable Stable Rendering"
    bl_description = ("Activate to prevent crashes and incorrect results during render."
                      " Activation will automatically lock the Blender interface"
                      " during render (Blender > Render > Lock Interface) and is highly"
                      " recommended")


    @classmethod
    def poll(cls, context):
        return not context.scene.render.use_lock_interface


    def execute(self, context):
        context.scene.render.use_lock_interface = True
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidHelperSelectDomain)
    bpy.utils.register_class(FlipFluidHelperSelectSurface)
    bpy.utils.register_class(FlipFluidHelperSelectFoam)
    bpy.utils.register_class(FlipFluidHelperSelectBubble)
    bpy.utils.register_class(FlipFluidHelperSelectSpray)
    bpy.utils.register_class(FlipFluidHelperAddObjects)
    bpy.utils.register_class(FlipFluidHelperRemoveObjects)
    bpy.utils.register_class(FlipFluidHelperSetObjectViewportDisplay)
    bpy.utils.register_class(FlipFluidHelperLoadLastFrame)
    bpy.utils.register_class(FlipFluidHelperCommandLineBake)
    bpy.utils.register_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRender)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.register_class(FlipFluidHelperStableRendering279)
    bpy.utils.register_class(FlipFluidHelperStableRendering28)

    bpy.utils.register_class(FlipFluidEnableWhitewaterSimulation)
    bpy.utils.register_class(FlipFluidEnableWhitewaterMenu)
    bpy.utils.register_class(FlipFluidDisplayEnableWhitewaterTooltip)


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperSelectDomain)
    bpy.utils.unregister_class(FlipFluidHelperSelectSurface)
    bpy.utils.unregister_class(FlipFluidHelperSelectFoam)
    bpy.utils.unregister_class(FlipFluidHelperSelectBubble)
    bpy.utils.unregister_class(FlipFluidHelperSelectSpray)
    bpy.utils.unregister_class(FlipFluidHelperAddObjects)
    bpy.utils.unregister_class(FlipFluidHelperRemoveObjects)
    bpy.utils.unregister_class(FlipFluidHelperSetObjectViewportDisplay)
    bpy.utils.unregister_class(FlipFluidHelperLoadLastFrame)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBake)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRender)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperStableRendering279)
    bpy.utils.unregister_class(FlipFluidHelperStableRendering28)

    bpy.utils.unregister_class(FlipFluidEnableWhitewaterSimulation)
    bpy.utils.unregister_class(FlipFluidEnableWhitewaterMenu)
    bpy.utils.unregister_class(FlipFluidDisplayEnableWhitewaterTooltip)

