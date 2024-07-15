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

import bpy, os, pathlib, stat, subprocess, platform, random, shutil, traceback
from bpy.props import (
        BoolProperty,
        )

from ..utils import version_compatibility_utils as vcu
from . import render_passes 


### PREPARE VISIBLITY SETTINGS FOR PASSES ###

def transfer_catchers_to_catcher_list(hprops):
    # Leere die bestehende Catcher-Liste
    hprops.render_passes_catcherlist.clear()
    
    # Übertrage die Catcher-Objekte in die Catcher-Liste
    for obj_prop in hprops.render_passes_objectlist:
        if obj_prop.catcher:
            new_catcher = hprops.render_passes_catcherlist.add()
            new_catcher.name = obj_prop.name
            new_catcher.catcher = obj_prop.catcher

def apply_visibility_settings_for_pass(pass_name):
    visibility_settings = render_passes.visibility_settings
    settings = visibility_settings.get(pass_name, {})
    hprops = bpy.context.scene.flip_fluid_helper

    # Übertrage Catcher-Objekte in die Catcher-Liste im Hintergrund
    transfer_catchers_to_catcher_list(hprops)

    print(f"Applying settings for pass: {pass_name}")
    print(f"Settings being applied: {settings}")

    # World- and rendersettings
    if 'world' in settings:
        apply_visibility_settings_for_world(bpy.context.scene.world, settings['world'])
    if 'film_transparent' in settings:
        apply_film_transparency(settings['film_transparent'])
    if 'transparent_glass' in settings:
        apply_transparent_glass_settings(settings['transparent_glass'])
    if 'denoiser' in settings:
        apply_denoiser(settings['denoiser'])

    # Objectsettings
    for obj_name, obj_visibility in settings.items():
        if obj_name in ["selected_objects", "world", "film_transparent", "transparent_glass"]:
            continue 
        obj = bpy.data.objects.get(obj_name)
        if obj:
            print(f"Applying general settings to {obj_name}: {obj_visibility}")
            apply_visibility_settings_for_object(obj, obj_visibility)
        else:
            print(f"Object not found in Blender: {obj_name}")

    if "selected_objects" in settings:
        object_list_settings = settings["selected_objects"]
        print(f"Settings for 'selected_objects' in pass '{pass_name}': {object_list_settings}")
        for obj_prop in hprops.render_passes_objectlist:
            obj = bpy.data.objects.get(obj_prop.name)
            if obj:
                print(f"Applying '{pass_name}' settings to selected object {obj_prop.name}")
                apply_visibility_settings_for_object(obj, object_list_settings)
            else:
                print(f"Selected object not found in Blender: {obj_prop.name}")

    if "catchers" in settings:
        catcher_list_settings = settings["catchers"]
        print(f"Settings for 'catchers' in pass '{pass_name}': {catcher_list_settings}")
        for catcher_prop in hprops.render_passes_catcherlist:
            catcher = bpy.data.objects.get(catcher_prop.name)
            if catcher:
                print(f"Applying '{pass_name}' settings to catcher {catcher_prop.name}")
                apply_visibility_settings_for_object(catcher, catcher_list_settings)
            else:
                print(f"Catcher object not found in Blender: {catcher_prop.name}")

def apply_film_transparency(film_transparent):
    bpy.context.scene.render.film_transparent = film_transparent
    print(f"Film transparency set to: {film_transparent}")

def apply_transparent_glass_settings(transparent_glass):
    bpy.context.scene.cycles.film_transparent_glass = transparent_glass
    print(f"Transparent glass set to: {transparent_glass}")

def apply_denoiser(denoiser):
    bpy.context.scene.cycles.use_denoising = denoiser
    print(f"Denoiser set to: {denoiser}")

def apply_visibility_settings_for_world(world, world_settings):
    if not world:
        print("No world found in the current scene.")
        return

    # Visibility settings for the world
    visibility_attributes = ['camera', 'diffuse', 'glossy', 'transmission', 'scatter', 'shadow']
    for attr in visibility_attributes:
        if attr in world_settings:
            setattr(world.cycles_visibility, attr, world_settings[attr])
            print(f"Set world ray visibility for {attr} to {world_settings[attr]}")

def apply_visibility_settings_for_object(obj, obj_visibility):
    obj.visible_camera = obj_visibility["camera"]
    obj.visible_diffuse = obj_visibility["diffuse"]
    obj.visible_glossy = obj_visibility["glossy"]
    obj.visible_transmission = obj_visibility["transmission"]
    obj.visible_volume_scatter = obj_visibility["scatter"]
    obj.visible_shadow = obj_visibility["shadow"]
    
    if "is_shadow_catcher" in obj_visibility:
        obj.is_shadow_catcher = obj_visibility["is_shadow_catcher"]
        
    if "is_holdout" in obj_visibility:
        obj.is_holdout = obj_visibility["is_holdout"]



def prepare_render_passes_blend_files():
    props = bpy.context.scene.flip_fluid_helper

    if not props.render_passes:
        return

    blend_file_directory = os.path.dirname(bpy.data.filepath)
    base_file_name = pathlib.Path(bpy.path.basename(bpy.data.filepath)).stem

    pass_suffixes = [
        ("catchers_only",       props.render_passes_catchers_only),
        ("objects_only",        props.render_passes_objects_only),
        ("fluidparticles_only", props.render_passes_fluidparticles_only),
        ("fluid_only",          props.render_passes_fluid_only),
        ("fluid_shadows_only",  props.render_passes_fluid_shadows_only),
        ("reflr_only",          props.render_passes_reflr_only),
        ("bubblesanddust_only", props.render_passes_bubblesanddust_only),
        ("foamandspray_only",   props.render_passes_foamandspray_only),
        # ("object_shadows_only", props.render_passes_object_shadows_only),  # Disabled for now
    ]

    clear_simulation_meshes_before_saving = True
    if clear_simulation_meshes_before_saving:
        # The simulation meshes can be cleared of data to reduce filesize
        # and speed up saving Blend files
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.reset_cache_objects()

    enabled_passes = [suffix for suffix, enabled in pass_suffixes if enabled]

    original_render_output_path = bpy.context.scene.render.filepath

    # Create a set of currently existing .blend and .blend1 files with the naming convention
    existing_files = {f for f in os.listdir(blend_file_directory)
                      if f.endswith(('.blend', '.blend1')) and
                      any(f.startswith(f"{i+1}_{base_file_name}_") for i in range(len(pass_suffixes)))}

    expected_render_pass_files = set()
    for idx, (suffix, is_active) in enumerate(pass_suffixes):
        if is_active:
            number = enabled_passes.index(suffix) + 1
            apply_visibility_settings_for_pass(suffix)
            apply_render_output_path_for_pass(suffix, number, base_file_name)

            blend_name = f"{number}_{base_file_name}_{suffix}.blend"
            blend_path = os.path.join(blend_file_directory, blend_name)
            bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)

            # Add the generated file names to the expected set
            expected_render_pass_files.add(blend_name)
            expected_render_pass_files.add(blend_name + "1")

            bpy.context.scene.render.filepath = original_render_output_path

    # Calculate the difference to find out which files should be removed
    files_to_remove = existing_files - expected_render_pass_files

    # Remove the files
    for filename in files_to_remove:
        blend_filepath = os.path.join(blend_file_directory, filename)

        # Note: Comment out os.remove() calls for the FLIP Fluids 1.8.0 release - just in case an unfound bug could
        # delete an incorrect Blend file.
        # All calls to os.remove should be implemented and checked in 
        #     filesystem/filesystem_protection_layer.py
        # According to the file and data protection guidelines:
        #     https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Cache-Settings#file-and-data-protection-features
        #
        # TODO: update this later - Ryan
        os.remove(blend_filepath)
        print(f"Removed file: {blend_filepath}")
        

def apply_render_output_path_for_pass(suffix, number, base_file_name):
    # Der Pfad zum Render-Verzeichnis
    original_output_folder = bpy.path.abspath(bpy.context.scene.render.filepath)
    # Entfernen Sie den Dateinamen, um nur das Verzeichnis zu erhalten
    output_folder = os.path.dirname(original_output_folder)
    
    # Erstellen des Unterverzeichnisses für den Pass
    render_output_subfolder = f"{number}_{suffix}"
    full_output_path = os.path.join(output_folder, render_output_subfolder)
    if not os.path.exists(full_output_path):
        os.makedirs(full_output_path)
    
    # Erstellen des neuen Dateinamens
    output_filename = os.path.basename(original_output_folder)
    bpy.context.scene.render.filepath = os.path.join(full_output_path, f"{number}_{output_filename}_{suffix}")


### END OF PREPARE VISIBLITY SETTINGS FOR PASSES ###


def get_command_line_script_filepath(script_filename):
    script_path = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.dirname(script_path)
    script_path = os.path.join(script_path, "resources", "command_line_scripts", script_filename)
    if not os.path.isfile(script_path):
        errmsg = "Unable to locate script <" + script_path + ">. Please contact the developers with this error."
        raise Exception(errmsg)
    return script_path


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


def get_blender_app_binary_path_windows():
    if vcu.is_blender_28():
        blender_exe_path = bpy.app.binary_path
        if " " in  blender_exe_path:
            # Some versions of Blender 2.8+ don't support spaces in the executable path
            blender_exe_path = "blender.exe"
    else:
        # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
        # executable path, so we'll just use blender.exe and hope that no other addon has
        # changed Blender's working directory
        blender_exe_path = "blender.exe"
    return blender_exe_path


def launch_command_darwin_or_linux(command_text, script_prefix_string):
    script_text = "#!/bin/bash\n" + command_text
    script_name = script_prefix_string + bpy.path.basename(bpy.context.blend_data.filepath) + ".sh"
    script_filepath = os.path.join(os.path.dirname(bpy.data.filepath), script_name)
    with open(script_filepath, 'w') as f:
        f.write(script_text)

    st = os.stat(script_filepath)
    os.chmod(script_filepath, st.st_mode | stat.S_IEXEC)

    system = platform.system()
    if system == "Darwin":
        subprocess.call(["open", "-a", "Terminal", script_filepath])
    elif system == "Linux":
        if shutil.which("gnome-terminal") is not None and shutil.which("bash") is not None:
            # Required to escape spaces for the script_filepath + "; exec bash" command to run
            script_filepath = script_filepath.replace(" ", "\\ ")
            subprocess.call(["gnome-terminal", "--", "bash", "-c", script_filepath + "; exec bash"])
        elif shutil.which("xterm") is not None:
            subprocess.call(["xterm", "-hold", "-e", script_filepath])
        else:
            errmsg = "This feature requires the (GNOME Terminal and Bash Shell), or the XTERM terminal emulator to be"
            errmsg += " installed and to be accessible on the system path. Either install these programs, restart Blender, and try again or use the"
            errmsg += " Copy Command to Clipboard operator and paste into a terminal program of your choice."
            bpy.ops.flip_fluid_operators.display_error(
                'INVOKE_DEFAULT',
                error_message="Linux: Unable to launch new terminal window",
                error_description=errmsg,
                popup_width=600
                )


def get_command_line_baking_script_filepath():
    hprops = bpy.context.scene.flip_fluid_helper
    script_name = "run_simulation.py"
    if hprops.cmd_bake_and_render:
        if hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_SEQUENCE':
            system = platform.system()
            render_mode = hprops.cmd_launch_render_after_bake_mode
            if system != "Windows":
                render_mode = 'CMD_RENDER_MODE_NORMAL'
            if render_mode == 'CMD_RENDER_MODE_NORMAL':
                script_name = "run_simulation_and_render_sequence.py"
            elif render_mode == 'CMD_RENDER_MODE_BATCH':
                script_name = "run_simulation_and_render_sequence_batch.py"
        elif hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED':
            script_name = "run_simulation_and_render_interleaved.py"
    return get_command_line_script_filepath(script_name)


def get_command_line_bake_subprocess_command_list():
    hprops = bpy.context.scene.flip_fluid_helper
    blender_exe_path = get_blender_app_binary_path_windows()
    script_filepath = get_command_line_baking_script_filepath()
    command_list = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "--python", script_filepath]
    if hprops.cmd_bake_and_render and hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED':
        num_instance_string = str(hprops.cmd_bake_and_render_interleaved_instances)
        use_overwrite_string = "0" if hprops.cmd_bake_and_render_interleaved_no_overwrite else "1"
        command_list += ["--", num_instance_string, use_overwrite_string]
    return command_list


def get_command_line_bake_command_text():
    hprops = bpy.context.scene.flip_fluid_helper
    script_filepath = get_command_line_baking_script_filepath()
    command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_filepath + "\""
    if hprops.cmd_bake_and_render and hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED':
        num_instance_string = str(hprops.cmd_bake_and_render_interleaved_instances)
        use_overwrite_string = "0" if hprops.cmd_bake_and_render_interleaved_no_overwrite else "1"
        command_text += " -- " + num_instance_string + " " + use_overwrite_string
    return command_text


class FlipFluidHelperCommandLineBake(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake"
    bl_label = "Launch Bake"
    bl_description = ("Launch a new command line window and start baking." +
                     " The .blend file will need to be saved for before using" +
                     " this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def is_render_output_format_image_required(self, context):
        hprops = context.scene.flip_fluid_helper
        is_bake_and_render_interleaved = hprops.cmd_bake_and_render and hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED'
        is_bake_and_render_batch = (hprops.cmd_bake_and_render and 
                                    hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_SEQUENCE' and 
                                    hprops.cmd_launch_render_after_bake_mode == 'CMD_RENDER_MODE_BATCH')
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


    def generate_bake_batch_file(self):
        # Launch using .bat file that can re-launch after crash is detected
        bat_template_path = get_command_line_script_filepath("cmd_bake_template.bat")
        with open(bat_template_path, 'r') as f:
            bat_text = f.read()

        prefs = vcu.get_addon_preferences()
        launch_attempts = prefs.cmd_bake_max_attempts
        launch_attempts_text = str(launch_attempts + 1)

        command_text = get_command_line_bake_command_text()
        bat_text = bat_text.replace("MAX_LAUNCH_ATTEMPTS", launch_attempts_text)
        bat_text = bat_text.replace("COMMAND_OPERATION", command_text)
        
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        cache_scripts_directory = os.path.join(cache_directory, "scripts")
        if not os.path.exists(cache_scripts_directory):
            os.makedirs(cache_scripts_directory)

        cmd_bake_script_filepath = os.path.join(cache_scripts_directory, "cmd_bake.bat")
        with open(cmd_bake_script_filepath, 'w') as f:
            f.write(bat_text)

        return cmd_bake_script_filepath


    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        command_list = get_command_line_bake_subprocess_command_list()
        command_text = get_command_line_bake_command_text()

        system = platform.system()
        if system == "Windows":
            if vcu.get_addon_preferences().cmd_bake_max_attempts == 0:
                # Launch with a single command
                subprocess.call(command_list, shell=True)
            else:
                cmd_bake_script_filepath = self.generate_bake_batch_file()
                os.startfile(cmd_bake_script_filepath)
        elif system == "Darwin" or system == "Linux":
            launch_command_darwin_or_linux(command_text, "BAKE_")

        info_msg = "Launched command line baking window. If the baking process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
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
        hprops = bpy.context.scene.flip_fluid_helper

        command_text = get_command_line_bake_command_text()
        bpy.context.window_manager.clipboard = command_text

        info_msg = "Copied the following baking command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line baking, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-bake"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}

### DF Add Passes here:

class FlipFluidPassesResetSettings(bpy.types.Operator):
    """Reset all visiblity settings to default"""
    bl_idname = "flip_fluid_operators.reset_passes_settings"
    bl_label = "Reset Passes Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        apply_visibility_settings_for_pass('reset')
        self.report({'INFO'}, "Pass settings have been reset.")
        return {'FINISHED'}

class FlipFluidHelperCommandLineRender(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render"
    bl_label = "Launch Render"
    bl_description = ("Launch a new command line window and start rendering the animation." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def check_and_report_operator_context_errors(self, context):
        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
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

        blender_exe_path = get_blender_app_binary_path_windows()
        command_list = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "-a"]
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" -a"

        if self.use_turbo_tools:
            command_list = ["start", "cmd", "/k", blender_exe_path, "-b", bpy.data.filepath, "--python-expr", "import bpy; bpy.ops.threedi.render_animation()"]
            command_text = "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" --python-expr \"import bpy; bpy.ops.threedi.render_animation()\""
        else:
            command_list = ["start", "cmd", "/k", blender_exe_path, "-b", bpy.data.filepath, "-a"]
            command_text = "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" -a"

        system = platform.system()
        if system == "Windows":
            subprocess.call(command_list, shell=True)
        elif system == "Darwin" or system == "Linux":
            launch_command_darwin_or_linux(command_text, "RENDER_ANIMATION_")

        info_msg = "Launched command line render window. If the render process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}



class FlipFluidHelperCommandLineRenderToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render_to_clipboard"
    bl_label = "Launch Render"
    bl_description = ("Copy command for rendering to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        if self.use_turbo_tools:
            command_text = "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" --python-expr \"import bpy; bpy.ops.threedi.render_animation()\""
        else:
            command_text = "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" -a"

        bpy.context.window_manager.clipboard = command_text
          
        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
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

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def check_and_report_operator_context_errors(self, context):
        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if not is_render_output_format_image():
            self.report({'ERROR'}, "Render output format must be an image format. Change render output to an image, save, and try again.")
            return {'CANCELLED'} 

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}


    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

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

        blender_exe_path = get_blender_app_binary_path_windows()
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\"" + " -- " + frame_string + " " + open_image_after
        command_list = ["start", "cmd", cmd_start_flag, blender_exe_path, "--background", bpy.data.filepath, "--python", script_path, "--", frame_string, open_image_after]

        system = platform.system()
        if system == "Windows":
            subprocess.call(command_list, shell=True)
        elif system == "Darwin" or system == "Linux":
            command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\"" + " -- " + frame_string + " " + open_image_after
            launch_command_darwin_or_linux(command_text, "RENDER_FRAME_")

        info_msg = "Launched command line render window. If the render process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-frame-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}



class FlipFluidHelperCmdRenderFrameToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_frame_to_clipboard"
    bl_label = "Launch Frame Render"
    bl_description = ("Copy command for frame rendering to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        frame_string = str(bpy.context.scene.frame_current)
        open_image_after = "0"
        if hprops.cmd_open_image_after_render:
            open_image_after = "1"
        
        script_path = get_command_line_script_filepath("render_single_frame.py")
        if self.use_turbo_tools:
            script_path = get_command_line_script_filepath("render_single_frame_turbo_tools.py")

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\"" + " -- " + frame_string + " " + open_image_after
        bpy.context.window_manager.clipboard = command_text
          
        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-frame-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineAlembicExport(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_alembic_export"
    bl_label = "Launch Alembic Export"
    bl_description = ("Launch a new command line window and start exporting the simulation meshes to the Alembic (.abc) format." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        script_path = get_command_line_script_filepath("alembic_export.py")
        blender_exe_path = get_blender_app_binary_path_windows()
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
        command_list = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "--python", script_path]

        system = platform.system()
        if system == "Windows":
            subprocess.call(command_list, shell=True)
        elif system == "Darwin" or system == "Linux":
            command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
            launch_command_darwin_or_linux(command_text, "ALEMBIC_EXPORT_")

        info_msg = "Launched command line Alembic export window. If the Alembic export process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line operators, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-alembic-export"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCmdAlembicExportToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_alembic_export_to_clipboard"
    bl_label = "Launch Alembic Export"
    bl_description = ("Copy command for Alembic export to your system clipboard." +
                     " The .blend file will need to be saved before running this command for changes to take effect")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        script_path = get_command_line_script_filepath("alembic_export.py")
        frame_string = str(bpy.context.scene.frame_current)
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
        bpy.context.window_manager.clipboard = command_text
          
        info_msg = "Copied the following Alembic export command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line tools, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-alembic-export"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


def get_render_output_info():
    full_path = bpy.path.abspath(bpy.context.scene.render.filepath)
    directory_path = full_path

    file_prefix = os.path.basename(directory_path)
    if file_prefix:
       directory_path = os.path.dirname(directory_path)

    file_format_to_suffix = {
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


class FlipFluidHelperCommandLineRenderToScriptfile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_to_scriptfile"
    bl_label = "Generate Batch File"
    bl_description = ("Generates a Windows batch file to render all frames one-by-one." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")


    @classmethod
    def poll(cls, context):
        system = platform.system()
        return bool(bpy.data.filepath) and system == "Windows"


    def get_missing_frames(self):
        directory_path, file_prefix, file_suffix = get_render_output_info()

        filenames = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        filenames = [f for f in filenames if f.startswith(file_prefix) and f.endswith(file_suffix)]
        frame_numbers = []
        for f in filenames:
            try:
                f = f[len(file_prefix):-len(file_suffix)]
                frame_numbers.append(int(f))
            except:
                pass

        frame_exists = {}
        for n in frame_numbers:
            frame_exists[n] = True

        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        missing_frames = []
        for i in range(frame_start, frame_end + 1):
            if not i in frame_exists:
                missing_frames.append(i)

        return missing_frames


    def generate_file_string(self, missing_frames):
        blender_exe_path = "\"" + bpy.app.binary_path + "\""
        blend_path = "\"" + bpy.data.filepath + "\""

        file_text = "echo.\n"
        for n in missing_frames:
            command_text = blender_exe_path + " -b " + blend_path + " -f " + str(n)
            file_text += command_text + "\n"
        file_text += "pause\n"

        return file_text


    def check_and_report_operator_context_errors(self, context):
        if not is_render_output_directory_createable():
            errmsg = "Render output directory is not valid or writeable: <" + get_render_output_directory() + ">"
            self.report({'ERROR'}, errmsg)
            return {'CANCELLED'}

        if not is_render_output_format_image():
            self.report({'ERROR'}, "Render output format must be an image format. Change render output to an image, save, and try again.")
            return {'CANCELLED'} 

        directory_path, file_prefix, file_suffix = get_render_output_info()
        if not directory_path:
            return {'CANCELLED'}

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}


    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        directory_path, file_prefix, file_suffix = get_render_output_info()

        more_info_string = "For more information on batch rendering, visit our documentation:\n"
        more_info_string += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render\n"
        render_output_info_string = "View the rendered files at <" + directory_path + ">\n"

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        missing_frames = self.get_missing_frames()
        if not missing_frames:
            info_msg = "No batch file generated! All frames have already been rendered.\n"
            info_msg += render_output_info_string + "\n"
            info_msg += more_info_string
            self.report({'INFO'}, info_msg)
            return {'CANCELLED'}

        file_text = self.generate_file_string(missing_frames)
        blend_directory = os.path.dirname(bpy.data.filepath)
        batch_filename = "RENDER_" + bpy.path.basename(bpy.context.blend_data.filepath) + ".bat"
        batch_filepath = os.path.join(blend_directory, batch_filename)
        with open(batch_filepath, "w") as renderscript_file:
            renderscript_file.write(file_text)

        total_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
        info_msg = "\nA batch file has been generated here: <" + batch_filepath + ">\n"
        info_msg += render_output_info_string + "\n"
        info_msg += str(total_frames - len(missing_frames)) + " frames in the " + file_suffix + " file format have already been rendered!\n"
        info_msg += str(len(missing_frames)) + " frames are not yet rendered!\n\n"
        info_msg += more_info_string

        self.report({'INFO'}, info_msg)
        
        return {'FINISHED'}


class FlipFluidHelperRunScriptfile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_run_batch_render_scriptfile"
    bl_label = "Launch Batch File Render"
    bl_description = ("Runs the generated batch file. If no batch file has been generated, one will be created automatically." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")


    regenerate_batch_file = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("regenerate_batch_file"))


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        directory = os.path.dirname(bpy.data.filepath)
        blend_filename = bpy.path.basename(bpy.context.blend_data.filepath)
        script_filename = "RENDER_" + blend_filename + ".bat"
        batch_filepath = os.path.join(directory, script_filename)

        if self.regenerate_batch_file or not os.path.isfile(batch_filepath):
            bpy.ops.flip_fluid_operators.helper_cmd_render_to_scriptfile()
            if not os.path.isfile(batch_filepath):
                self.report({'ERROR'}, "Unable to generate the render script.")

        os.startfile(batch_filepath)
          
        info_msg = "Beginning to run the batch render script!\n\n"
        info_msg += "For more information on batch file rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
        self.report({'INFO'}, info_msg)
        return {'FINISHED'}

    
class FlipFluidHelperOpenOutputFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_open_outputfolder"
    bl_label = "Opens The Output Folder"
    bl_description = ("Opens the output-folder that is set in the output settings. If the folder does not exist, it will be created." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        directory_path, file_prefix, file_suffix = get_render_output_info()
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        os.startfile(directory_path)
        return {'FINISHED'}


class FlipFluidHelperCommandLineRenderPassAnimation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_pass_animation"
    bl_label = "Launch Render Pass Animation"
    bl_description = ("Description: todo - launch render pass animation script")

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)

    def cleanup_object_list(self, object_list):
        indices_to_remove = [index for index, obj in enumerate(object_list) if not bpy.data.objects.get(obj.name)]

        for index in reversed(indices_to_remove):
            object_list.remove(index)

        if indices_to_remove:
            print(f"Removed {len(indices_to_remove)} non-existent objects from the object list.")

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

        if context.scene.render.engine == 'BLENDER_EEVEE':
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

        script_path = get_command_line_script_filepath("render_animation_render_passes.py")
        blender_exe_path = get_blender_app_binary_path_windows()

        ### EXECUTE PREPARE RENDERPASSES ###
        prepare_render_passes_blend_files()

        # Clean object list if objects were deleted
        hprops = bpy.context.scene.flip_fluid_helper
        self.cleanup_object_list(hprops.render_passes_objectlist)

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" + bpy.data.filepath + "\" --python \"" + script_path + "\""
        command_list = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "--python", script_path]

        system = platform.system()
        if system == "Windows":
            subprocess.call(command_list, shell=True)
        elif system == "Darwin" or system == "Linux":
            command_text = "\"" + bpy.app.binary_path + "\" --background \"" + bpy.data.filepath + "\" --python \"" + script_path + "\""
            launch_command_darwin_or_linux(command_text, "RENDER_PASS_ANIMATION_")

        info_msg = "Launched command line render window. If the render process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
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
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)

    def execute(self, context):
        ### EXECUTE PREPARE RENDERPASSES ###
        prepare_render_passes_blend_files()

        # Clean object list if objects were deleted
        hprops = bpy.context.scene.flip_fluid_helper
        self.cleanup_object_list(hprops.render_passes_objectlist)

        script_path = get_command_line_script_filepath("render_animation_render_passes.py")
        frame_string = str(bpy.context.scene.frame_current)
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" + bpy.data.filepath + "\" --python \"" + script_path + "\""
        bpy.context.window_manager.clipboard = command_text

        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-animation-render"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}

    def cleanup_object_list(self, object_list):
        indices_to_remove = [index for index, obj in enumerate(object_list) if not bpy.data.objects.get(obj.name)]

        for index in reversed(indices_to_remove):
            object_list.remove(index)

        if indices_to_remove:
            print(f"Removed {len(indices_to_remove)} non-existent objects from the object list.")


class FLIPFLUIDS_MT_render_menu(bpy.types.Menu):
    bl_label = "FLIP Fluids CMD Render"
    bl_idname = "FLIPFLUIDS_MT_render_menu"

    def draw(self, context):
        render_frame_text = "Shift F12"
        render_animation_text = "Shift Ctrl F12"
        render_batch_animation_text = "Shift Ctrl B"

        system = platform.system()

        row1 = self.layout.row()
        row2 = self.layout.row()
        if system == "Windows":
            row3 = self.layout.row()

        row1.operator(FlipFluidHelperCommandLineRenderFrame.bl_idname, icon="RENDER_STILL").use_turbo_tools=False
        row2.operator(FlipFluidHelperCommandLineRender.bl_idname, text="Launch Animation Render", icon="RENDER_ANIMATION").use_turbo_tools=False
        if system == "Windows":
            row3.operator(FlipFluidHelperRunScriptfile.bl_idname, text="Launch Batch Render", icon="CONSOLE").regenerate_batch_file=True

        row1.label(text=render_frame_text)
        row2.label(text=render_animation_text)
        if system == "Windows":
            row3.label(text=render_batch_animation_text)
        

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
    bpy.utils.register_class(FlipFluidHelperCmdRenderFrameToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineAlembicExport)
    bpy.utils.register_class(FlipFluidHelperCmdAlembicExportToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderToScriptfile)
    bpy.utils.register_class(FlipFluidHelperRunScriptfile)
    bpy.utils.register_class(FlipFluidHelperOpenOutputFolder)
    bpy.utils.register_class(FlipFluidPassesResetSettings)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderPassAnimation)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderPassAnimationToClipboard)

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

        system = platform.system()
        if system == "Windows":
            kmi = km.keymap_items.new(FlipFluidHelperRunScriptfile.bl_idname, type='B', value='PRESS', shift=True, ctrl=True)
            ADDON_KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBake)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRender)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderFrame)
    bpy.utils.unregister_class(FlipFluidHelperCmdRenderFrameToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineAlembicExport)
    bpy.utils.unregister_class(FlipFluidHelperCmdAlembicExportToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderToScriptfile)
    bpy.utils.unregister_class(FlipFluidHelperRunScriptfile)
    bpy.utils.unregister_class(FlipFluidHelperOpenOutputFolder)
    bpy.utils.unregister_class(FlipFluidPassesResetSettings)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderPassAnimation)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderPassAnimationToClipboard)

    bpy.utils.unregister_class(FLIPFLUIDS_MT_render_menu)
    try:
        # Blender 2.8+
        bpy.types.TOPBAR_MT_render.remove(draw_flip_fluids_render_menu)
    except:
        pass

    # Remove shortcuts
    for km, kmi in ADDON_KEYMAPS:
        km.keymap_items.remove(kmi)
    ADDON_KEYMAPS.clear()
