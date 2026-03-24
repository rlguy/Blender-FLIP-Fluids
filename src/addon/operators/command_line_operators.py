# Blender FLIP Fluids Add-on
# Copyright (C) 2026 Ryan L. Guy & Dennis Fassbaender
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

import bpy, os, pathlib, stat, subprocess, platform, random, shlex, shutil, traceback, ctypes, json
from bpy.props import (
        BoolProperty,
        )

from . import compositing_tools_operators
from ..utils import version_compatibility_utils as vcu
from ..utils import installation_utils
from ..filesystem import filesystem_protection_layer as fpl


def get_blender_launch_command(enable_render_logging=False):
    if installation_utils.is_linux_blender_flatpak_installation():
        command_text = "flatpak run org.blender.Blender"
    else:
        command_text = '"' + bpy.app.binary_path + '"'

    logging_commands = get_blender_logging_commands()
    if enable_render_logging and logging_commands:
        command_text += " " + get_blender_logging_commands()

    return command_text


def get_blender_logging_commands():
    logging_commands = ""
    if vcu.is_blender_50():
        logging_commands = "--log-level info"
    return logging_commands


def get_command_line_script_filepath(script_filename):
    script_path = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.dirname(script_path)
    script_path = os.path.join(script_path, "resources", "command_line_scripts", script_filename)
    if not os.path.isfile(script_path):
        errmsg = "Unable to locate script <" + script_path + ">. Please contact the developers with this error."
        raise Exception(errmsg)
    return script_path


def get_flip_fluids_alembic_exporter_filepath():
    executable_name = ""

    system = platform.system()
    if system == "Windows":
        executable_name = "ff_alembic_exporter_windows.exe"
    elif system == "Darwin":
        executable_name = "ff_alembic_exporter_macos"
    elif system == "Linux":
        executable_name = "ff_alembic_exporter_linux"

    executable_path = os.path.dirname(os.path.realpath(__file__))
    executable_path = os.path.dirname(executable_path)
    executable_path = os.path.join(executable_path, "ffengine", "lib", executable_name)
    if not os.path.isfile(executable_path):
        errmsg = "Unable to locate executable <" + executable_path + ">. Please contact the developers with this error."
        raise Exception(errmsg)
    return executable_path


def get_flip_fluids_alembic_exporter_lib_filepath():
    executable_name = ""

    system = platform.system()
    if system == "Windows":
        lib_name = "libffalembicengine.dll"
    elif system == "Darwin":
        lib_name = "libffalembicengine.dylib"
    elif system == "Linux":
        lib_name = "libffalembicengine.so"

    lib_path = os.path.dirname(os.path.realpath(__file__))
    lib_path = os.path.dirname(lib_path)
    lib_path = os.path.join(lib_path, "ffengine", "lib", lib_name)
    if not os.path.isfile(lib_path):
        errmsg = "Unable to locate executable <" + lib_path + ">. Please contact the developers with this error."
        raise Exception(errmsg)
    return lib_path


def save_blend_file_before_launch(override_preferences=False):
    prefs = vcu.get_addon_preferences()
    if prefs.cmd_save_blend_file_before_launch or override_preferences:
        bpy.ops.wm.save_mainfile()


def get_render_output_directory():
    frame_path = bpy.context.scene.render.frame_path()
    render_path = os.path.dirname(frame_path)
    return render_path


def is_render_output_directory_createable():
    render_path = get_render_output_directory()
    try:
        os.makedirs(render_path, exist_ok=True)
    except:
        return False
    return True


def restore_blender_original_cwd():
    # Restore Blender's original CWD in case another addon has changed this path
    # The command line launch features rely on the CWD being the default location
    # of the folder containing the Blender executable.
    # If the location is modified, the command line window will open to 
    # the modified location and launching Blender may fail.
    os.chdir(os.path.dirname(bpy.app.binary_path))


def get_scripts_directory():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is not None:
        cache_directory = dprops.cache.get_cache_abspath()
        scripts_directory = os.path.join(cache_directory, "scripts")
    else:
        blend_basename = bpy.path.basename(bpy.context.blend_data.filepath)
        blend_directory = os.path.dirname(bpy.data.filepath)
        scripts_directory = os.path.join(blend_directory, "flip_fluids_addon_scripts")
    return scripts_directory


def get_script_write_filepath(script_filename):
    scripts_directory = get_scripts_directory()
    os.makedirs(scripts_directory, exist_ok=True)
    script_filepath = os.path.join(scripts_directory, script_filename)
    return script_filepath


def write_scripts_directory_readme():
    scripts_directory = get_scripts_directory()
    os.makedirs(scripts_directory, exist_ok=True)
    readme_filename = "README.txt"
    readme_filepath = os.path.join(scripts_directory, readme_filename)

    if os.path.isfile(readme_filepath):
        # Already written
        return

    readme_text = "The script files in this directory are generated by the FLIP Fluids addon command line operators and\n"
    readme_text += "are used to launch and run command line processes.\n\n"
    readme_text += "These scripts can be run directly to start the command line process as an alternative to launching within Blender.\n\n"
    readme_text += "It is safe to delete these script files or this script directory, even while the scripts are running.\n\n"
    readme_text += "Command Line Tools documentation: https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools\n\n"
    readme_text += "- The FLIP Fluids Addon Development Team\n"
    with open(readme_filepath, 'w') as f:
        f.write(readme_text)


def launch_command_universal_os(command_text, script_prefix_string, keep_window_open=True, skip_launch=False, chcp=None):
    system = platform.system()
    if system == "Windows":
        code_page = 65001
        if chcp:
            code_page = chcp

        script_extension = ".bat"
        script_header = "echo off\nchcp " + str(code_page) + "\n\n"
        script_footer = ""
        if keep_window_open:
            script_footer = "\ncmd /k\n"
    else:
        # Darwin or Linux
        script_extension = ".sh"
        script_header = "#!/bin/sh\n\n"
        script_footer = ""

    blend_basename = bpy.path.basename(bpy.context.blend_data.filepath)

    script_filename = script_prefix_string + blend_basename + script_extension
    script_filepath = get_script_write_filepath(script_filename)

    script_text = script_header + command_text + "\n" + script_footer
    with open(script_filepath, 'w') as f:
        f.write(script_text)

    bpy.context.window_manager.clipboard = "\"" + script_filepath + "\""

    if not skip_launch:
        if system == "Darwin" or system == "Linux":
            # Add execution file permissions
            st = os.stat(script_filepath)
            os.chmod(script_filepath, st.st_mode | stat.S_IEXEC)

        if system == "Windows":
            os.startfile(script_filepath)
        elif system == "Darwin":
            subprocess.call(["open", "-a", "Terminal", script_filepath])
        elif system == "Linux":
            if shutil.which("gnome-terminal") is not None:
                subprocess.call(["gnome-terminal", "--", "/bin/sh", "-c", shlex.quote(script_filepath) + '; exec "${SHELL:-/bin/sh}"'])
            elif shutil.which("xterm") is not None:
                subprocess.call(["xterm", "-hold", "-e", script_filepath])
            else:
                errmsg = "This feature requires the GNOME Terminal or XTERM terminal emulator to be"
                errmsg += " installed and to be accessible on the system path and accessible within Blender. Either install these programs, restart Blender, and try again or use the"
                errmsg += " Copy Command to Clipboard operator and paste into a terminal program of your choice."
                bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message="Linux: Unable to launch new terminal window",
                    error_description=errmsg,
                    popup_width=600
                    )

    write_scripts_directory_readme()

    return script_filepath


def get_command_line_baking_script_filepath():
    hprops = bpy.context.scene.flip_fluid_helper
    script_name = "run_simulation.py"
    if hprops.cmd_bake_and_render:
        if hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_SEQUENCE':
            script_name = "run_simulation_and_render.py"
        elif hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED':
            script_name = "run_simulation_and_render_interleaved.py"
    return get_command_line_script_filepath(script_name)


def get_command_line_bake_command_text():
    hprops = bpy.context.scene.flip_fluid_helper
    script_filepath = get_command_line_baking_script_filepath()
    command_text = get_blender_launch_command() + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_filepath + "\""
    if hprops.cmd_bake_and_render and hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED':
        num_instance_string = str(hprops.cmd_bake_and_render_interleaved_instances)
        use_overwrite_string = "0" if hprops.cmd_bake_and_render_interleaved_no_overwrite else "1"
        run_as_flatpak = "1" if installation_utils.is_linux_blender_flatpak_installation() else "0"
        command_text += " -- " + num_instance_string + " " + use_overwrite_string + " " + run_as_flatpak
    return command_text


class FlipFluidHelperCommandLineBake(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake"
    bl_label = "Launch Bake"
    bl_description = ("Launch a new command line window and start baking." +
                     " The .blend file will need to be saved for before using" +
                     " this operator for changes to take effect")

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def is_render_output_format_image_required(self, context):
        hprops = context.scene.flip_fluid_helper
        is_bake_and_render_interleaved = hprops.cmd_bake_and_render and hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED'
        is_bake_and_render_batch = (hprops.cmd_bake_and_render and 
                                    hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_SEQUENCE' and 
                                    hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_BATCH')
        return is_bake_and_render_interleaved or is_bake_and_render_batch


    def check_and_report_operator_context_errors(self, context):
        hprops = context.scene.flip_fluid_helper

        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"}, 
                        "Active scene must contain domain object to launch bake. Select the scene that contains the domain object, save, and try again.")
            return {'CANCELLED'}

        if hprops.cmd_bake_and_render and not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if self.is_render_output_format_image_required(context) and not is_render_output_format_image():
            self.report({'ERROR'}, "Render output format must be an image format for this render mode. Change render output to an image, save, and try again.")
            return {'CANCELLED'}

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}


    def generate_bake_batch_file_command_text(self):
        # Launch using .bat file that can re-launch after crash is detected
        bat_template_path = get_command_line_script_filepath("cmd_bake_template.bat")
        with open(bat_template_path, 'r') as f:
            batch_text = f.read()

        prefs = vcu.get_addon_preferences()
        launch_attempts = prefs.cmd_bake_max_attempts
        launch_attempts_text = str(launch_attempts + 1)

        command_text = get_command_line_bake_command_text()
        batch_text = batch_text.replace("MAX_LAUNCH_ATTEMPTS", launch_attempts_text)
        batch_text = batch_text.replace("COMMAND_OPERATION", command_text)

        return batch_text


    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        cprops = context.scene.flip_fluid_compositing_tools

        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        # Only for passes rendering during bake and render interleaved
        is_bake_and_render_interleaved = hprops.cmd_bake_and_render and hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED'
        is_render_passes_interleaved = cprops.render_passes and is_bake_and_render_interleaved
        if is_render_passes_interleaved:
            compositing_tools_operators.compositing_tools_operators.prepare_render_passes_for_operator(context)

        command_text = get_command_line_bake_command_text()
        if platform.system() == "Windows" and vcu.get_addon_preferences().cmd_bake_max_attempts > 0:
            command_text = self.generate_bake_batch_file_command_text()

        script_filepath = launch_command_universal_os(command_text, "FF_BAKE_", keep_window_open=True, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line baking window. If the baking process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line baking, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-bake"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineBakeToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake_to_clipboard"
    bl_label = "Copy Bake Command to Clipboard"
    bl_description = ("Copy command for baking to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_command_line_bake('INVOKE_DEFAULT', skip_launch=True)

        info_msg = "Copied the following baking command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line baking, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-bake"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRender(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render"
    bl_label = "Launch Render"
    bl_description = ("Launch a new command line window and start rendering the animation." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    use_turbo_tools: BoolProperty(False)

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def is_render_output_format_image_required(self, context):
        hprops = context.scene.flip_fluid_helper
        cprops = context.scene.flip_fluid_compositing_tools
        if cprops.render_passes:
            return True
        else:
            return hprops.cmd_launch_render_animation_mode in ['CMD_RENDER_MODE_BATCH', 'CMD_RENDER_MODE_MULTI_INSTANCE']


    def check_and_report_operator_context_errors(self, context):
        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if self.is_render_output_format_image_required(context) and not is_render_output_format_image():
            self.report({'ERROR'}, "Render output format must be an image format for this render mode. Change render output to an image, save, and try again.")
            return {'CANCELLED'}

        if context.scene.flip_fluid_compositing_tools.render_passes:
            if not context.scene.flip_fluid_compositing_tools.render_passes_is_any_pass_enabled:
                self.report({'ERROR'}, "No Compositing Tools Render Passes are enabled. Enable at least 1 pass to begin render.")
                return {'CANCELLED'}

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}


    def get_normal_render_command_text(self):
        hprops = bpy.context.scene.flip_fluid_helper 
        skip_rendered_frames = hprops.cmd_launch_render_normal_animation_no_overwrite
        bool_string = str(not skip_rendered_frames)

        if self.use_turbo_tools:
            python_expr_string = " --python-expr \"import bpy; bpy.context.scene.render.use_overwrite = " + bool_string + "; bpy.ops.threedi.render_animation()\""
            command_text = get_blender_launch_command(enable_render_logging=True) + " -b \"" + bpy.data.filepath + "\" " + python_expr_string
        else:
            python_expr_string = " --python-expr \"import bpy; bpy.context.scene.render.use_overwrite = " + bool_string + "\""
            command_text = get_blender_launch_command(enable_render_logging=True) + " -b \"" + bpy.data.filepath + "\" " + python_expr_string + " -a"
        return command_text


    def get_single_frame_render_command_text(self, frameno):
        return get_blender_launch_command(enable_render_logging=True) + " -b \"" + bpy.data.filepath + "\" -f " + str(frameno)


    def wrap_command_in_no_overwrite_conditional(self, command_text, frame_filepath):
        system = platform.system()
        if system == 'Windows':
            # .bat syntax
            if_statement_prefix = "if NOT exist \"" + frame_filepath + "\" (\n    "
            if_statement_suffix = "\n) else (\n    "
            if_statement_suffix += "echo Skipping rendered frame: " + frame_filepath + "\n)"
        elif system in ['Darwin', 'Linux']:
            # .sh systax
            if_statement_prefix = "if [ ! -f \"" + frame_filepath + "\" ]; then\n    "
            if_statement_suffix = "\nelse\n    "
            if_statement_suffix += "echo \"Skipping rendered frame: " + frame_filepath + "\"\nfi"

        command_text = if_statement_prefix + command_text + if_statement_suffix

        return command_text


    def get_batch_render_command_text(self):
        hprops = bpy.context.scene.flip_fluid_helper
        directory_path, file_prefix, file_suffix = get_render_output_info()
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        frame_step = bpy.context.scene.frame_step

        frameno_list = list(range(frame_start, frame_end + 1, frame_step))

        full_command_text = ""
        for frameno in frameno_list:
            frame_filename = file_prefix + str(frameno).zfill(4) + file_suffix
            frame_filepath = os.path.join(directory_path, frame_filename)

            command_text = self.get_single_frame_render_command_text(frameno)
            if hprops.cmd_launch_render_animation_no_overwrite:
                command_text = self.wrap_command_in_no_overwrite_conditional(command_text, frame_filepath)

            full_command_text += command_text + "\n"

        return full_command_text


    def get_multi_instance_render_command_text(self):
        hprops = bpy.context.scene.flip_fluid_helper
        num_instance_string = str(hprops.cmd_launch_render_animation_instances)
        use_overwrite_string = "0" if hprops.cmd_launch_render_animation_no_overwrite else "1"
        run_as_flatpak = "1" if installation_utils.is_linux_blender_flatpak_installation() else "0"
        script_filepath = get_command_line_script_filepath("render_animation_multi_instance.py")

        command_text = get_blender_launch_command(enable_render_logging=True) + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_filepath + "\""
        command_text += " -- " + num_instance_string + " " + use_overwrite_string + " " + run_as_flatpak

        return command_text


    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        hprops = bpy.context.scene.flip_fluid_helper
        cprops = context.scene.flip_fluid_compositing_tools
        if cprops.render_passes:
            # Redirect to FlipFluidHelperCommandLineRenderPassAnimation operator
            bpy.ops.flip_fluid_operators.helper_cmd_render_pass_animation('INVOKE_DEFAULT', skip_launch=self.skip_launch)
            return {'FINISHED'}
        elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_NORMAL':
            command_text = self.get_normal_render_command_text()
        elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_BATCH':
            command_text = self.get_batch_render_command_text()
            if not command_text:
                errmsg = "All frames have already been rendered to <" + get_render_output_directory() + ">. Remove image files or disable the 'Skip rendered frames' option to re-render."
                if bpy.app.background:
                    print("\nNo frames were rendered. " + errmsg)
                else:
                    self.report({'ERROR'}, errmsg)
                return {'CANCELLED'}
        elif hprops.cmd_launch_render_animation_mode == 'CMD_RENDER_MODE_MULTI_INSTANCE':
            command_text = self.get_multi_instance_render_command_text()

        script_filepath = launch_command_universal_os(command_text, "FF_RENDER_ANIMATION_", keep_window_open=True, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line render window. If the render process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line rendering, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}



class FlipFluidHelperCommandLineRenderToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render_to_clipboard"
    bl_label = "Launch Render"
    bl_description = ("Copy command for rendering to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")

    use_turbo_tools: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_command_line_render('INVOKE_DEFAULT', use_turbo_tools=self.use_turbo_tools, skip_launch=True)
          
        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


### RENDER SINGLE FRAME ###
class FlipFluidHelperCommandLineRenderFrame(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render_frame"
    bl_label = "Launch Frame Render"
    bl_description = ("Launch a new command line window and start rendering the current timeline frame." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    use_turbo_tools: BoolProperty(False)

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def check_and_report_operator_context_errors(self, context):
        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if not is_render_output_format_image():
            self.report({'INFO'}, "Render output format is currently set to a video format. Frame will be rendered as a PNG.")

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}


    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        cprops = context.scene.flip_fluid_compositing_tools
        if cprops.render_passes:
            # Redirect to FlipFluidHelperCommandLineRenderPassFrame operator
            bpy.ops.flip_fluid_operators.helper_cmd_render_pass_frame('INVOKE_DEFAULT', skip_launch=self.skip_launch)
            return {'FINISHED'}

        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=True)
        restore_blender_original_cwd()

        frame_string = str(bpy.context.scene.frame_current)

        open_image_after = "0"
        if hprops.cmd_open_image_after_render:
            open_image_after = "1"

        cmd_start_flag = "/k"
        if hprops.cmd_close_window_after_render:
            cmd_start_flag = "/c"

        script_path = get_command_line_script_filepath("render_single_frame.py")
        if self.use_turbo_tools:
            script_path = get_command_line_script_filepath("render_single_frame_turbo_tools.py")

        command_text = get_blender_launch_command(enable_render_logging=True) + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\"" + " -- " + frame_string + " " + open_image_after

        script_filepath = launch_command_universal_os(command_text, "FF_RENDER_FRAME_", keep_window_open=not hprops.cmd_close_window_after_render, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line render window. If the render process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line rendering, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-frame-render"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}



class FlipFluidHelperCommandLineRenderFrameToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_frame_to_clipboard"
    bl_label = "Launch Frame Render"
    bl_description = ("Copy command for frame rendering to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")

    use_turbo_tools: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_command_line_render_frame('INVOKE_DEFAULT', use_turbo_tools=self.use_turbo_tools, skip_launch=True)
          
        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-frame-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineAlembicExport(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_alembic_export"
    bl_label = "Launch Alembic Export"
    bl_description = ("Launch a new command line window and start exporting the simulation meshes to the Alembic (.abc) format." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        script_path = get_command_line_script_filepath("alembic_export.py")
        command_text = get_blender_launch_command() + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""

        script_filepath = launch_command_universal_os(command_text, "FF_ALEMBIC_EXPORT_", keep_window_open=True, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line Alembic export window. If the Alembic export process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line operators, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-alembic-export"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineAlembicExportToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_alembic_export_to_clipboard"
    bl_label = "Launch Alembic Export"
    bl_description = ("Copy command for Alembic export to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_command_line_alembic_export('INVOKE_DEFAULT', skip_launch=True)
          
        info_msg = "Copied the following Alembic export command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line tools, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-alembic-export"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineCustomAlembicExport(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_custom_alembic_export"
    bl_label = "Launch Alembic Export"
    bl_description = ("Launch a new command line window and start exporting the simulation meshes to the Alembic (.abc) format." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def get_export_frame_range(self):
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        hprops = bpy.context.scene.flip_fluid_helper
        if hprops.alembic_frame_range_mode == 'FRAME_RANGE_CUSTOM':
            frame_start = hprops.alembic_frame_range_custom.value_min
            frame_end = hprops.alembic_frame_range_custom.value_max
        return frame_start, frame_end


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        script_path = get_command_line_script_filepath("flip_fluids_alembic_export.py")
        command_text = get_blender_launch_command() + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""

        script_filepath = launch_command_universal_os(command_text, "FF_ALEMBIC_EXPORT_", keep_window_open=True, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line Alembic export window. If the Alembic export process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line operators, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-alembic-export"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineCustomAlembicExportToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.cmd_custom_alembic_export_to_clipboard"
    bl_label = "Launch Alembic Export"
    bl_description = ("Copy command for Alembic export to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_cmd_custom_alembic_export('INVOKE_DEFAULT', skip_launch=True)
          
        info_msg = "Copied the following Alembic export command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line tools, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-alembic-export"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineUSDExport(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_usd_export"
    bl_label = "Launch USD Export"
    bl_description = ("Launch a new command line window and start exporting the simulation meshes to the Universal Scene Description (.usdc) format." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        script_path = get_command_line_script_filepath("usd_export.py")
        command_text = get_blender_launch_command() + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
        
        script_filepath = launch_command_universal_os(command_text, "FF_USD_EXPORT_", keep_window_open=True, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line USD export window. If the USD export process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line operators, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-usd-export"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineUSDExportToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_usd_export_to_clipboard"
    bl_label = "Launch USD Export"
    bl_description = ("Copy command for Universal Scene Description (USD) export to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_command_line_usd_export('INVOKE_DEFAULT', skip_launch=True)
          
        info_msg = "Copied the following Universal Scene Description (USD) export command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line tools, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-usd-export"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


def get_render_output_info():
    full_path = bpy.path.abspath(bpy.context.scene.render.filepath)
    directory_path = full_path

    file_prefix = os.path.basename(directory_path)
    if file_prefix:
       directory_path = os.path.dirname(directory_path)

    file_format_to_suffix = {
        "AVIF"                : ".avif",
        "BMP"                 : ".bmp",
        "IRIS"                : ".rgb",
        "PNG"                 : ".png",
        "JPEG"                : ".jpg",
        "JPEG2000"            : ".jp2",
        "TARGA"               : ".tga",
        "TARGA_RAW"           : ".tga",
        "CINEON"              : ".cin",
        "DPX"                 : ".dpx",
        "OPEN_EXR_MULTILAYER" : ".exr",
        "OPEN_EXR"            : ".exr",
        "HDR"                 : ".hdr",
        "TIFF"                : ".tif",
        "WEBP"                : ".webp",
        "AVI_JPEG"            : ".avi",
        "AVI_RAW"             : ".avi",
        "FFMPEG"              : ".mp4"
    }

    file_format = bpy.context.scene.render.image_settings.file_format
    file_suffix = file_format_to_suffix[file_format]

    return directory_path, file_prefix, file_suffix


def is_render_output_format_image():
    image_file_format_to_suffix = {
        "AVIF"                : ".avif",
        "BMP"                 : ".bmp",
        "IRIS"                : ".rgb",
        "PNG"                 : ".png",
        "JPEG"                : ".jpg",
        "JPEG2000"            : ".jp2",
        "TARGA"               : ".tga",
        "TARGA_RAW"           : ".tga",
        "CINEON"              : ".cin",
        "DPX"                 : ".dpx",
        "OPEN_EXR_MULTILAYER" : ".exr",
        "OPEN_EXR"            : ".exr",
        "HDR"                 : ".hdr",
        "TIFF"                : ".tif",
        "WEBP"                : ".webp",
    }

    file_format = bpy.context.scene.render.image_settings.file_format
    return file_format in image_file_format_to_suffix


def is_render_output_format_image_with_transparency():
    image_file_format_to_suffix = {
        "AVIF"                : ".avif",
        "IRIS"                : ".rgb",
        "PNG"                 : ".png",
        "JPEG2000"            : ".jp2",
        "TARGA"               : ".tga",
        "TARGA_RAW"           : ".tga",
        "DPX"                 : ".dpx",
        "OPEN_EXR_MULTILAYER" : ".exr",
        "OPEN_EXR"            : ".exr",
        "TIFF"                : ".tif",
        "WEBP"                : ".webp",
    }

    file_format = bpy.context.scene.render.image_settings.file_format
    return file_format in image_file_format_to_suffix


def is_render_output_format_image_set_to_RGBA_color_mode():
    color_mode = bpy.context.scene.render.image_settings.color_mode
    return color_mode == 'RGBA'


def open_file_browser_directory(directory_path):
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
    except:
        return False

    if directory_path.endswith("/") or directory_path.endswith("\\"):
        directory_path = directory_path[:-1]

    system = platform.system()
    if system == 'Windows':
        os.startfile(os.path.abspath(directory_path))
    elif system == 'Darwin':
        subprocess.call(['open', '--', directory_path])
    elif system == 'Linux':
        subprocess.call(['xdg-open', '--', directory_path])
    return True

    
class FlipFluidHelperOpenRenderOutputFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_open_render_output_folder"
    bl_label = "Open Render Output Directory"
    bl_description = ("Opens the render output directory set in the output properties. If the directory does not exist, it will be created." +
                      " The .blend file will need to be saved before using this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)

        directory_path, file_prefix, file_suffix = get_render_output_info()
        success = open_file_browser_directory(directory_path)

        if not success:
            if directory_path == "":
                directory_path = "No directory set"
            self.report({"ERROR"}, "Invalid render output directory: <" + directory_path + ">")
            return {'CANCELLED'}

        return {'FINISHED'}


class FlipFluidHelperOpenCacheOutputFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_open_cache_output_folder"
    bl_label = "Open Simulation Cache Directory"
    bl_description = ("Opens the simulation cache directory set in the domain cache settings. If the directory does not exist, it will be created." +
                      " The .blend file will need to be saved before using this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath) and context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        
        directory_path = context.scene.flip_fluid.get_domain_properties().cache.get_cache_abspath()
        success = open_file_browser_directory(directory_path)

        if not success:
            if directory_path == "":
                directory_path = "No directory set"
            self.report({"ERROR"}, "Invalid cache output directory: <" + directory_path + ">")
            return {'CANCELLED'}

        return {'FINISHED'}


class FlipFluidHelperOpenAlembicOutputFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_open_alembic_output_folder"
    bl_label = "Open Alembic Output Directory"
    bl_description = ("Opens the Alembic output directory set in the Alembic export tool. If the directory does not exist, it will be created." +
                      " The .blend file will need to be saved before using this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath) and context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        
        alembic_filepath = context.scene.flip_fluid_helper.get_alembic_output_abspath()
        directory_path = os.path.dirname(alembic_filepath)
        success = open_file_browser_directory(directory_path)

        if not success:
            if directory_path == "":
                directory_path = "No directory set"
            self.report({"ERROR"}, "Invalid cache output directory: <" + directory_path + ">")
            return {'CANCELLED'}

        return {'FINISHED'}


class FlipFluidHelperOpenUSDOutputFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_open_usd_output_folder"
    bl_label = "Open USD Output Directory"
    bl_description = ("Opens the USD output directory set in the USD export tool. If the directory does not exist, it will be created." +
                      " The .blend file will need to be saved before using this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath) and context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        
        usd_filepath = context.scene.flip_fluid_helper.get_usd_output_abspath()
        directory_path = os.path.dirname(usd_filepath)
        success = open_file_browser_directory(directory_path)

        if not success:
            if directory_path == "":
                directory_path = "No directory set"
            self.report({"ERROR"}, "Invalid cache output directory: <" + directory_path + ">")
            return {'CANCELLED'}

        return {'FINISHED'}


def get_render_passes_info(context):
    # Pass-Suffix-Liste mit den zugehoerigen Listen
    get_render_passes_info
    pass_suffixes = [
        ("BG_elements_only", cprops.render_passes_elements_only, cprops.render_passes_bg_elementslist),
        ("REF_elements_only", cprops.render_passes_elements_only, cprops.render_passes_ref_elementslist),
        ("objects_only", cprops.render_passes_objects_only, None),
        ("fluidparticles_only", cprops.render_passes_fluidparticles_only, None),
        ("fluid_only", cprops.render_passes_fluid_only, None),
        ("fluid_shadows_only", cprops.render_passes_fluid_shadows_only, None),
        ("reflr_only", cprops.render_passes_reflr_only, None),
        ("bubblesanddust_only", cprops.render_passes_bubblesanddust_only, None),
        ("foamandspray_only", cprops.render_passes_foamandspray_only, None),
        ("FG_elements_only", cprops.render_passes_elements_only, cprops.render_passes_fg_elementslist),
    ]

    # Entferne leere Listen-Suffixe
    filtered_suffixes = [
        suffix for suffix, is_active, elements_list in pass_suffixes
        if is_active and (elements_list is None or len(elements_list) > 0)
    ]

    blend_file_directory = os.path.dirname(bpy.data.filepath)
    base_file_name = pathlib.Path(bpy.path.basename(bpy.data.filepath)).stem

    info_dict_items = []
    for idx, suffix in enumerate(filtered_suffixes):
        pass_index = idx + 1

        render_pass_blend_filename = f"{pass_index}_{base_file_name}_{suffix}.blend"
        blend_filepath = os.path.join(blend_file_directory, render_pass_blend_filename)

        original_output_folder = bpy.path.abspath(bpy.context.scene.render.filepath)
        output_folder = os.path.dirname(original_output_folder)
        render_output_subfolder = f"{pass_index}_{suffix}"
        render_output_directory = os.path.join(output_folder, render_output_subfolder)
        output_filename = os.path.basename(original_output_folder)
        pass_file_prefix = f"{pass_index}_{output_filename}_{suffix}"

        rendered_files = os.listdir(render_output_directory)

        info = {}
        info['pass_index'] = pass_index
        info['blend_filepath'] = blend_filepath
        info['pass_file_prefix'] = pass_file_prefix
        info['rendered_files'] = rendered_files
        info_dict_items.append(info)

    return info_dict_items


class FlipFluidHelperCommandLineRenderPassAnimation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_pass_animation"
    bl_label = "Launch Render Pass Animation"
    bl_description = ("Description: todo - launch render pass animation script")

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return (
            context.scene.flip_fluid.get_domain_object() is not None and
            bool(bpy.data.filepath) and
            context.scene.flip_fluid_compositing_tools.render_passes and
            context.scene.flip_fluid_compositing_tools.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_compositing_tools.render_passes_stillimagemode_toggle
        )


    def get_single_frame_render_pass_command_text(self, blend_filepath, frameno):
        return get_blender_launch_command(enable_render_logging=True) + " -b \"" + blend_filepath + "\" -f " + str(frameno)


    def get_render_passes_batch_command_text(self, context):
        render_passes_info = get_render_passes_info(context)

        _, _, image_file_extension = get_render_output_info()
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        frame_step = bpy.context.scene.frame_step

        hprops = context.scene.flip_fluid_helper
        skip_rendered_frames = hprops.cmd_launch_render_passes_animation_no_overwrite

        render_command_queue = []
        for frameno in range(frame_start, frame_end + 1, frame_step):
            for pass_info in render_passes_info:
                blend_filepath = pass_info['blend_filepath']

                if skip_rendered_frames:                    
                    render_file_prefix = pass_info['pass_file_prefix']
                    rendered_files = pass_info['rendered_files']
                    rendered_filename = render_file_prefix + str(frameno).zfill(4) + image_file_extension
                    if not rendered_filename in rendered_files:
                        command_text = self.get_single_frame_render_pass_command_text(blend_filepath, frameno)
                        render_command_queue.append(command_text)
                else:
                    command_text = self.get_single_frame_render_pass_command_text(blend_filepath, frameno)
                    render_command_queue.append(command_text)

        full_command_text = ""
        for cmd in render_command_queue:
            full_command_text += cmd + "\n"

        return full_command_text


    def get_render_passes_multi_instance_command_text(self, context):
        hprops = context.scene.flip_fluid_helper
        num_instance_string = str(hprops.cmd_launch_render_passes_animation_instances)
        use_overwrite_string = "0" if hprops.cmd_launch_render_passes_animation_no_overwrite else "1"
        run_as_flatpak = "1" if installation_utils.is_linux_blender_flatpak_installation() else "0"
        script_filepath = get_command_line_script_filepath("render_animation_render_passes_multi_instance.py")

        command_text = get_blender_launch_command(enable_render_logging=True) + " --background \"" +  bpy.data.filepath + "\" --python \"" + script_filepath + "\""
        command_text += " -- " + num_instance_string + " " + use_overwrite_string + " " + run_as_flatpak

        return command_text


    def check_and_report_operator_context_errors(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"},
                        "Active scene must contain domain object to launch render. Select the scene that contains the domain object, save, and try again.")
            return {'CANCELLED'}

        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if context.scene.render.engine == 'BLENDER_EEVEE' or context.scene.render.engine == 'BLENDER_EEVEE_NEXT':
            self.report({'ERROR'}, "The EEVEE render engine is not supported for this feature. Set the render engine to Cycles, save, and try again.")
            return {'CANCELLED'}
        if context.scene.render.engine == 'BLENDER_WORKBENCH':
            self.report({'ERROR'}, "The Workbench render engine is not supported for this feature. Set the render engine to Cycles, save, and try again.")
            return {'CANCELLED'}

        if not is_render_output_format_image_with_transparency():
            errmsg = "Render output format must be an image format that supports transparency."
            errmsg += " The OpenEXR format is recommended."
            errmsg += " Change render output to an image format with transparency, save, and try again."
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if not is_render_output_format_image_set_to_RGBA_color_mode():
            errmsg = "Render output format color mode must be set to RGBA for transparency."
            errmsg += " The current color mode is set to <" + bpy.context.scene.render.image_settings.color_mode + ">."
            errmsg += " Change render output color mode to RGBA, save, and try again."
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}

    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        compositing_tools_operators.prepare_render_passes_for_operator(context)

        command_text = self.get_render_passes_multi_instance_command_text(context)

        script_filepath = launch_command_universal_os(command_text, "FF_RENDER_PASS_ANIMATION_", keep_window_open=True, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line render window. If the render process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line rendering, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRenderPassAnimationToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_pass_anim_clipboard"
    bl_label = "Copy Render Pass Animation Command to Clipboard"
    bl_description = ("Description: todo - launch render pass animation script to clipboard")

    @classmethod
    def poll(cls, context):
        return (
            context.scene.flip_fluid.get_domain_object() is not None and
            bool(bpy.data.filepath) and
            context.scene.flip_fluid_compositing_tools.render_passes and
            context.scene.flip_fluid_compositing_tools.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_compositing_tools.render_passes_stillimagemode_toggle
        )


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_cmd_render_pass_animation('INVOKE_DEFAULT', skip_launch=True)

        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRenderPassFrame(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_pass_frame"
    bl_label = "Launch Render Pass Frame"
    bl_description = ("Description: todo - launch render pass animation script")

    skip_launch: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return (
            context.scene.flip_fluid.get_domain_object() is not None and
            bool(bpy.data.filepath) and
            context.scene.flip_fluid_compositing_tools.render_passes and
            context.scene.flip_fluid_compositing_tools.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_compositing_tools.render_passes_stillimagemode_toggle
        )


    def get_single_frame_render_pass_command_text(self, blend_filepath, frameno):
        return get_blender_launch_command(enable_render_logging=True) + " -b \"" + blend_filepath + "\" -f " + str(frameno)


    def get_render_passes_single_frame_command_text(self, context):
        render_passes_info = get_render_passes_info(context)

        _, _, image_file_extension = get_render_output_info()
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        frame_step = bpy.context.scene.frame_step

        render_command_queue = []
        frameno = bpy.context.scene.frame_current
        for pass_info in render_passes_info:
            blend_filepath = pass_info['blend_filepath']
            command_text = self.get_single_frame_render_pass_command_text(blend_filepath, frameno)
            render_command_queue.append(command_text)

        full_command_text = ""
        for cmd in render_command_queue:
            full_command_text += cmd + "\n"

        return full_command_text


    def check_and_report_operator_context_errors(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"},
                        "Active scene must contain domain object to launch render. Select the scene that contains the domain object, save, and try again.")
            return {'CANCELLED'}

        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if context.scene.render.engine == 'BLENDER_EEVEE' or context.scene.render.engine == 'BLENDER_EEVEE_NEXT':
            self.report({'ERROR'}, "The EEVEE render engine is not supported for this feature. Set the render engine to Cycles, save, and try again.")
            return {'CANCELLED'}
        if context.scene.render.engine == 'BLENDER_WORKBENCH':
            self.report({'ERROR'}, "The Workbench render engine is not supported for this feature. Set the render engine to Cycles, save, and try again.")
            return {'CANCELLED'}

        if not is_render_output_format_image_with_transparency():
            errmsg = "Render output format must be an image format that supports transparency."
            errmsg += " The OpenEXR format is recommended."
            errmsg += " Change render output to an image format with transparency, save, and try again."
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if not is_render_output_format_image_set_to_RGBA_color_mode():
            errmsg = "Render output format color mode must be set to RGBA for transparency."
            errmsg += " The current color mode is set to <" + bpy.context.scene.render.image_settings.color_mode + ">."
            errmsg += " Change render output color mode to RGBA, save, and try again."
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}

    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        compositing_tools_operators.prepare_render_passes_for_operator(context)

        command_text = self.get_render_passes_single_frame_command_text(context)

        hprops = context.scene.flip_fluid_helper
        script_filepath = launch_command_universal_os(command_text, "FF_RENDER_PASS_FRAME_", keep_window_open=not hprops.cmd_close_window_after_render, skip_launch=self.skip_launch)

        if not self.skip_launch:
            info_msg = "Launched command line render window. If the render process did not begin,"
            info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
            info_msg += " automatic command execution. You may try running following script file manually:\n\n"
            info_msg += script_filepath + "\n\n"
            info_msg += "For more information on command line rendering, visit our documentation:\n"
            info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-frame-render"
            self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRenderPassFrameToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_pass_frame_clipboard"
    bl_label = "Copy Render Pass Frame Command to Clipboard"
    bl_description = ("Description: todo - launch render pass animation script to clipboard")

    @classmethod
    def poll(cls, context):
        return (
            context.scene.flip_fluid.get_domain_object() is not None and
            bool(bpy.data.filepath) and
            context.scene.flip_fluid_compositing_tools.render_passes and
            context.scene.flip_fluid_compositing_tools.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_compositing_tools.render_passes_stillimagemode_toggle
        )


    def execute(self, context):
        bpy.ops.flip_fluid_operators.helper_cmd_render_pass_frame('INVOKE_DEFAULT', skip_launch=True)

        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += bpy.context.window_manager.clipboard + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-frame-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FLIPFLUIDS_MT_render_menu(bpy.types.Menu):
    bl_label = "FLIP Fluids CMD Render"
    bl_idname = "FLIPFLUIDS_MT_render_menu"

    def draw(self, context):
        render_frame_text = "Shift F12"
        render_animation_text = "Shift Ctrl F12"

        system = platform.system()

        row1 = self.layout.row()
        row2 = self.layout.row()

        row1.operator(FlipFluidHelperCommandLineRenderFrame.bl_idname, icon="RENDER_STILL").use_turbo_tools=False
        row2.operator(FlipFluidHelperCommandLineRender.bl_idname, text="Launch Animation Render", icon="RENDER_ANIMATION").use_turbo_tools=False

        row1.label(text=render_frame_text)
        row2.label(text=render_animation_text)
        

def draw_flip_fluids_render_menu(self, context):
    self.layout.separator()
    self.layout.menu(FLIPFLUIDS_MT_render_menu.bl_idname, icon="CONSOLE")


ADDON_KEYMAPS = []

def register():
    bpy.utils.register_class(FlipFluidHelperCommandLineBake)
    bpy.utils.register_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRender)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderFrame)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderFrameToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineAlembicExport)
    bpy.utils.register_class(FlipFluidHelperCommandLineAlembicExportToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineCustomAlembicExport)
    bpy.utils.register_class(FlipFluidHelperCommandLineCustomAlembicExportToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineUSDExport)
    bpy.utils.register_class(FlipFluidHelperCommandLineUSDExportToClipboard)
    bpy.utils.register_class(FlipFluidHelperOpenRenderOutputFolder)
    bpy.utils.register_class(FlipFluidHelperOpenCacheOutputFolder)
    bpy.utils.register_class(FlipFluidHelperOpenAlembicOutputFolder)
    bpy.utils.register_class(FlipFluidHelperOpenUSDOutputFolder)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderPassAnimation)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderPassAnimationToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderPassFrame)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderPassFrameToClipboard)

    bpy.utils.register_class(FLIPFLUIDS_MT_render_menu)
    try:
        # Blender 2.8+
        bpy.types.TOPBAR_MT_render.append(draw_flip_fluids_render_menu)
    except Exception as e:
        print(traceback.format_exc())
        print(e)

    # Add Shortcuts
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D', region_type='WINDOW')
        kmi = km.keymap_items.new(FlipFluidHelperCommandLineRenderFrame.bl_idname, type='F12', value='PRESS', shift=True)
        ADDON_KEYMAPS.append((km, kmi))

        kmi = km.keymap_items.new(FlipFluidHelperCommandLineRender.bl_idname, type='F12', value='PRESS', shift=True, ctrl=True)
        ADDON_KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBake)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRender)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderFrame)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderFrameToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineAlembicExport)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineAlembicExportToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineCustomAlembicExport)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineCustomAlembicExportToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineUSDExport)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineUSDExportToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperOpenRenderOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperOpenCacheOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperOpenAlembicOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperOpenUSDOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderPassAnimation)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderPassAnimationToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderPassFrame)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderPassFrameToClipboard)

    bpy.utils.unregister_class(FLIPFLUIDS_MT_render_menu)
    try:
        # Blender 2.8+
        bpy.types.TOPBAR_MT_render.remove(draw_flip_fluids_render_menu)
    except:
        pass

    # Remove shortcuts
    for km, kmi in ADDON_KEYMAPS:
        try:
            # Keymap may be unavailable depending on context
            km.keymap_items.remove(kmi)
        except:
            pass
    ADDON_KEYMAPS.clear()