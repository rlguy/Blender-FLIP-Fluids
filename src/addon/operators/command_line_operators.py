# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
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
from ..presets import render_passes 


### PREPARE VISIBLITY SETTINGS FOR PASSES ###

# Console output can be toggled with "Domain > Debug > Display Render Passes Console Output" option
# This function can be used exactly like Python print()
def print_render_pass_debug(*args, **kwargs):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is not None and dprops.debug.display_render_passes_console_output:
        print(*args, **kwargs)


def toggle_footageprojection(value):
    """Sets the blend input of the 'ff_fluidsurface_projection' node to the given value."""
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        return

    node_tree = material.node_tree
    target_node = node_tree.nodes.get("ff_fluidsurface_projection")
    if target_node:
        blend_input = target_node.inputs[0]
        if blend_input:
            blend_input.default_value = float(value)


def toggle_fluidfinder(value):
    """Sets the render_passes_toggle_projectiontester property in flip_fluid_helper to the given boolean."""
    bpy.context.scene.flip_fluid_helper.render_passes_toggle_projectiontester = value


def toggle_onlyreflections(value):
    """Sets ff_onlyreflections node (Mix Shader FAC input) to the given value."""
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        return

    node_tree = material.node_tree
    node_prefix = "ff_onlyreflections"
    
    # Look for Mix Shader nodes with the prefix "ff_onlyreflections"
    relevant_nodes = [
        node for node in node_tree.nodes
        if node.name.startswith(node_prefix) and node.type == 'MIX_SHADER'
    ]

    for node in relevant_nodes:
        # Adjust the FAC (inputs[0]) value of the Mix Shader
        node.inputs[0].default_value = float(value)


def toggle_transparent_or_holdout(value):
    """Sets ff_transparent_or_holdout node (Mix Shader FAC input) to the given value."""
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        return

    node_tree = material.node_tree
    node_prefix = "ff_transparent_or_holdout"

    # Look for Mix Shader nodes named ff_transparent_or_holdout
    relevant_nodes = [
        node for node in node_tree.nodes
        if node.name.startswith(node_prefix) and node.type == 'MIX_SHADER'
    ]

    for node in relevant_nodes:
        # Adjust the FAC (inputs[0]) value
        node.inputs[0].default_value = float(value)


def transfer_elements_to_elements_lists(hprops):
    # Clear elements lists
    hprops.render_passes_fg_elementslist.clear()
    hprops.render_passes_bg_elementslist.clear()
    hprops.render_passes_ref_elementslist.clear()
   
    for obj_prop in hprops.render_passes_objectlist:
        if obj_prop.fg_elements:
            new_fg_element = hprops.render_passes_fg_elementslist.add()
            print_render_pass_debug("added fg elemt")
            new_fg_element.name = obj_prop.name
        elif obj_prop.bg_elements:
            new_bg_element = hprops.render_passes_bg_elementslist.add()
            print_render_pass_debug("added bg elemt")
            new_bg_element.name = obj_prop.name
        elif obj_prop.ref_elements:
            new_ref_element = hprops.render_passes_ref_elementslist.add()
            print_render_pass_debug("added ref elemt")
            new_ref_element.name = obj_prop.name
          

def apply_visibility_settings_for_pass(pass_name):
    visibility_settings = render_passes.visibility_settings
    settings = visibility_settings.get(pass_name, {})
    hprops = bpy.context.scene.flip_fluid_helper

    # Aktualisiere die Listen basierend auf den Flags
    transfer_elements_to_elements_lists(hprops)

    print_render_pass_debug(f"Applying settings for pass: {pass_name}")
    print_render_pass_debug(f"Settings being applied: {settings}")

    # World- und Render-Einstellungen
    if 'world' in settings:
        apply_visibility_settings_for_world(bpy.context.scene.world, settings['world'])
    if 'film_transparent' in settings:
        apply_film_transparency(settings['film_transparent'])
    if 'transparent_glass' in settings:
        apply_transparent_glass_settings(settings['transparent_glass'])
    #if 'denoiser' in settings:
    #    apply_denoiser(settings['denoiser'])

    # Objekt-Sichtbarkeitseinstellungen
    for obj_name, obj_visibility in settings.items():
        if obj_name in ["selected_objects", "world", "film_transparent", "transparent_glass"]:
            continue 
        obj = bpy.data.objects.get(obj_name)
        if obj:
            print_render_pass_debug(f"Applying general settings to {obj_name}: {obj_visibility}")
            apply_visibility_settings_for_object(obj, obj_visibility, pass_name)
        else:
            print_render_pass_debug(f"Object not found in Blender: {obj_name}")

    # Einstellungen für ausgewaehlte Objekte
    if "selected_objects" in settings:
        object_list_settings = settings["selected_objects"]
        print_render_pass_debug(f"Settings for 'selected_objects' in pass '{pass_name}': {object_list_settings}")

        for obj_prop in hprops.render_passes_objectlist:
            obj = bpy.data.objects.get(obj_prop.name)
            if obj:
                # Falls "reset" → Sonderlogik, sonst direkt aus 'selected_objects'
                if pass_name == "reset":
                    # Ganz normal die Dictionary‐Werte anwenden
                    obj_visibility = object_list_settings
                else:
                    obj_visibility = object_list_settings
                
                apply_visibility_settings_for_object(obj, obj_visibility, pass_name)
            else:
                print_render_pass_debug(f"Selected object not found in Blender: {obj_prop.name}")

    # Einstellungen fuer Foreground-Elemente
    if "fg_elements" in settings:
        fg_elements_list_settings = settings["fg_elements"]
        print_render_pass_debug(f"Settings for 'fg_elements' in pass '{pass_name}': {fg_elements_list_settings}")

        for fg_elements_prop in hprops.render_passes_fg_elementslist:
            fg_elements = bpy.data.objects.get(fg_elements_prop.name)
            if fg_elements:
                print_render_pass_debug(f"Applying '{pass_name}' settings to foreground object {fg_elements_prop.name}")
                apply_visibility_settings_for_object(fg_elements, fg_elements_list_settings, pass_name)
            else:
                print_render_pass_debug(f"Foreground object not found in Blender: {fg_elements_prop.name}")

    # Einstellungen fuer Background-Elemente
    if "bg_elements" in settings:
        bg_elements_list_settings = settings["bg_elements"]
        print_render_pass_debug(f"Settings for 'bg_elements' in pass '{pass_name}': {bg_elements_list_settings}")

        for bg_elements_prop in hprops.render_passes_bg_elementslist:
            bg_elements = bpy.data.objects.get(bg_elements_prop.name)
            if bg_elements:
                print_render_pass_debug(f"Applying '{pass_name}' settings to background object {bg_elements_prop.name}")
                apply_visibility_settings_for_object(bg_elements, bg_elements_list_settings, pass_name)
            else:
                print_render_pass_debug(f"Background object not found in Blender: {bg_elements_prop.name}")

    # Einstellungen fuer Reflexionselemente
    if "ref_elements" in settings:
        ref_elements_list_settings = settings["ref_elements"]
        print_render_pass_debug(f"Settings for 'ref_elements' in pass '{pass_name}': {ref_elements_list_settings}")

        for ref_elements_prop in hprops.render_passes_ref_elementslist:
            ref_elements = bpy.data.objects.get(ref_elements_prop.name)
            if ref_elements:
                print_render_pass_debug(f"Applying '{pass_name}' settings to reflective object {ref_elements_prop.name}")
                apply_visibility_settings_for_object(ref_elements, ref_elements_list_settings, pass_name)
            else:
                print_render_pass_debug(f"Reflective object not found in Blender: {ref_elements_prop.name}")

    # Einstellungen fuer Ground-Objekte
    if "ground" in settings:
        ground_list_settings = settings["ground"]
        print_render_pass_debug(f"Settings for 'ground' in pass '{pass_name}': {ground_list_settings}")

        for obj_prop in hprops.render_passes_objectlist:
            if obj_prop.ground:
                ground = bpy.data.objects.get(obj_prop.name)
                if ground:
                    print_render_pass_debug(f"Applying '{pass_name}' settings to ground object {obj_prop.name}")
                    apply_visibility_settings_for_object(ground, ground_list_settings, pass_name)
                else:
                    print_render_pass_debug(f"Ground object not found in Blender: {obj_prop.name}")


def apply_film_transparency(film_transparent):
    bpy.context.scene.render.film_transparent = film_transparent
    print_render_pass_debug(f"Film transparency set to: {film_transparent}")

def apply_transparent_glass_settings(transparent_glass):
    bpy.context.scene.cycles.film_transparent_glass = transparent_glass
    print_render_pass_debug(f"Transparent glass set to: {transparent_glass}")

def apply_denoiser(denoiser):
    bpy.context.scene.cycles.use_denoising = denoiser
    print_render_pass_debug(f"Denoiser set to: {denoiser}")

def apply_visibility_settings_for_world(world, world_settings):
    if not world:
        print_render_pass_debug("No world found in the current scene.")
        return

    # Visibility settings for the world
    visibility_attributes = ['camera', 'diffuse', 'glossy', 'transmission', 'scatter', 'shadow']
    for attr in visibility_attributes:
        if attr in world_settings:
            setattr(world.cycles_visibility, attr, world_settings[attr])
            print_render_pass_debug(f"Set world ray visibility for {attr} to {world_settings[attr]}")


def apply_visibility_settings_for_object(obj, obj_visibility, pass_name=""):
    hprops = bpy.context.scene.flip_fluid_helper

    if not isinstance(obj_visibility, dict):
        print_render_pass_debug(f"Warning: obj_visibility for {obj.name} is not a dictionary! Received: {obj_visibility}")
        return

    if pass_name == "reset":
        # 1) Alle Werte aus dem "reset"-Dict übernehmen, inkl. is_shadow_catcher
        obj.visible_camera         = obj_visibility.get("camera", obj.visible_camera)
        obj.visible_diffuse        = obj_visibility.get("diffuse", obj.visible_diffuse)
        obj.visible_glossy         = obj_visibility.get("glossy", obj.visible_glossy)
        obj.visible_transmission   = obj_visibility.get("transmission", obj.visible_transmission)
        obj.visible_volume_scatter = obj_visibility.get("scatter", obj.visible_volume_scatter)
        obj.visible_shadow         = obj_visibility.get("shadow", obj.visible_shadow)
        obj.is_holdout             = obj_visibility.get("is_holdout", obj.is_holdout)
        obj.is_shadow_catcher      = obj_visibility.get("is_shadow_catcher", obj.is_shadow_catcher)

        # 2) Gibt es einen gespeicherten ShadowCatcher-Zustand?
        existing_entry = next(
            (s for s in hprops.render_passes_shadowcatcher_state if s.name == obj.name),
            None
        )
        if existing_entry:
            # Wenn ja: diesen Zustand *nachträglich* anwenden
            obj.is_shadow_catcher = existing_entry.is_shadow_catcher
            print_render_pass_debug(f"Reset: {obj.name} - Shadow Catcher auf gespeicherten Wert: {obj.is_shadow_catcher}")
        else:
            print_render_pass_debug(f"Reset: {obj.name} - Shadow Catcher laut reset-Dict: {obj.is_shadow_catcher}")

        return

    # -- Falls nicht reset, also normales Rendering --
    # Hier kommt das ganz normale Standardprozedere:
    obj.visible_camera        = obj_visibility.get("camera", obj.visible_camera)
    obj.visible_diffuse       = obj_visibility.get("diffuse", obj.visible_diffuse)
    obj.visible_glossy        = obj_visibility.get("glossy", obj.visible_glossy)
    obj.visible_transmission  = obj_visibility.get("transmission", obj.visible_transmission)
    obj.visible_volume_scatter= obj_visibility.get("scatter", obj.visible_volume_scatter)
    obj.visible_shadow        = obj_visibility.get("shadow", obj.visible_shadow)

    # Shadow Catcher
    obj.is_shadow_catcher     = obj_visibility.get("is_shadow_catcher", obj.is_shadow_catcher)
    obj.is_holdout            = obj_visibility.get("is_holdout", obj.is_holdout)

    print_render_pass_debug(f"Applied visibility settings for {obj.name} in pass {pass_name}")


def prepare_render_passes_blend_files():
    props = bpy.context.scene.flip_fluid_helper

    # Print message if render_passes is disabled
    if not props.render_passes:
        print_render_pass_debug("Render passes are disabled, but blend files will still be generated.")

    blend_file_directory = os.path.dirname(bpy.data.filepath)
    base_file_name = pathlib.Path(bpy.path.basename(bpy.data.filepath)).stem

    transfer_elements_to_elements_lists(props)

    # Initial list of suffixes with their corresponding lists
    pass_suffixes = [
        ("BG_elements_only",    props.render_passes_elements_only,         props.render_passes_bg_elementslist),
        ("REF_elements_only",   props.render_passes_elements_only,         props.render_passes_ref_elementslist),
        ("objects_only",        props.render_passes_objects_only,          None),
        ("fluidparticles_only", props.render_passes_fluidparticles_only,   None),
        ("fluid_only",          props.render_passes_fluid_only,            None),
        ("fluid_shadows_only",  props.render_passes_fluid_shadows_only,    None),
        ("reflr_only",          props.render_passes_reflr_only,            None),
        ("bubblesanddust_only", props.render_passes_bubblesanddust_only,   None),
        ("foamandspray_only",   props.render_passes_foamandspray_only,     None),
        ("FG_elements_only",    props.render_passes_elements_only,         props.render_passes_fg_elementslist),
    ]

    # Filter out suffixes with inactive flags or empty element lists
    filtered_suffixes = []
    for suffix, is_active, elements_list in pass_suffixes:
        if not is_active:
            continue
        if elements_list is not None and len(elements_list) == 0:
            print_render_pass_debug(f"Skipping {suffix} because the associated list is empty.")
            continue
        filtered_suffixes.append((suffix, is_active, elements_list))

    # Debug-Ausgabe
    print_render_pass_debug("Enabled passes after filtering:", [suffix for suffix, _, _ in filtered_suffixes])

    # Delete all existing passes-blendfiles before generating new ones
    for file_name in os.listdir(blend_file_directory):
        if any(suffix in file_name for suffix, _, _ in pass_suffixes):
            file_path = os.path.join(blend_file_directory, file_name)
            os.remove(file_path)
            print_render_pass_debug(f"Deleted old blend file: {file_path}")

    # Reset cache if needed
    clear_simulation_meshes_before_saving = True
    if clear_simulation_meshes_before_saving:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.reset_cache_objects()

    original_render_output_path = bpy.context.scene.render.filepath

    # For property retrieval/restoration
    hprops = bpy.context.scene.flip_fluid_helper

    # Generate new files
    for idx, (suffix, _, _) in enumerate(filtered_suffixes):
        number = idx + 1

        # -- Always store and override fluidfinder for each suffix --
        original_finder_val = hprops.render_passes_toggle_projectiontester
        toggle_fluidfinder(False)

        # We'll define original_fade_val here, so we can use it conditionally below
        original_fade_val = None

        if suffix == "reflr_only":
            toggle_onlyreflections(1.0)
            toggle_transparent_or_holdout(1.0)
            bpy.context.scene.render.use_compositing = True

            # Save original fade value and set it to 0
            original_fade_val = hprops.render_passes_blend_footage_to_fluidsurface
            toggle_footageprojection(0.0)

        elif suffix == "objects_only":
            toggle_transparent_or_holdout(1.0)

        elif suffix == "fluid_only":
            toggle_transparent_or_holdout(1.0)

            # Save original fade value and set it to 0
            original_fade_val = hprops.render_passes_blend_footage_to_fluidsurface
            toggle_footageprojection(0.0)

        # Apply visibility settings for the current pass
        apply_visibility_settings_for_pass(suffix)
        # Set render output path
        apply_render_output_path_for_pass(suffix, number, base_file_name)

        # Save the blend file
        blend_name = f"{number}_{base_file_name}_{suffix}.blend"
        blend_path = os.path.join(blend_file_directory, blend_name)
        bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)

        # -- Revert pass-specific toggles --
        if suffix == "reflr_only":
            toggle_onlyreflections(0.0)
            toggle_transparent_or_holdout(0.0)
            bpy.context.scene.render.use_compositing = False

            # Restore fade value if it was changed
            if original_fade_val is not None:
                toggle_footageprojection(original_fade_val)

        elif suffix == "objects_only":
            toggle_transparent_or_holdout(0.0)

        elif suffix == "fluid_only":
            toggle_transparent_or_holdout(0.0)

            # Restore fade value if it was changed
            if original_fade_val is not None:
                toggle_footageprojection(original_fade_val)

        # -- Restore fluidfinder for all suffixes --
        toggle_fluidfinder(original_finder_val)

        # Restore the render output path
        bpy.context.scene.render.filepath = original_render_output_path


def apply_render_output_path_for_pass(suffix, number, base_file_name):

    # Path to render directory
    original_output_folder = bpy.path.abspath(bpy.context.scene.render.filepath)
    # Remove filename
    output_folder = os.path.dirname(original_output_folder)
    
    # Add subdirectories
    render_output_subfolder = f"{number}_{suffix}"
    full_output_path = os.path.join(output_folder, render_output_subfolder)
    if not os.path.exists(full_output_path):
        os.makedirs(full_output_path)
    
    # Add new filenames
    output_filename = os.path.basename(original_output_folder)
    bpy.context.scene.render.filepath = os.path.join(full_output_path, f"{number}_{output_filename}_{suffix}")


def cleanup_object_list_for_operator(object_list):
        indices_to_remove = [index for index, obj in enumerate(object_list) if not bpy.data.objects.get(obj.name)]

        for index in reversed(indices_to_remove):
            object_list.remove(index)

        if indices_to_remove:
            print_render_pass_debug(f"Removed {len(indices_to_remove)} non-existent objects from the object list.")


def prepare_render_passes_for_operator(context):
    ### EXECUTE PREPARE RENDERPASSES ###
    prepare_render_passes_blend_files()
  
    bpy.ops.flip_fluid_operators.reset_passes_settings('INVOKE_DEFAULT')

    # Clean object list if objects were deleted
    hprops = context.scene.flip_fluid_helper
    cleanup_object_list_for_operator(hprops.render_passes_objectlist)


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


def launch_command_universal_os(command_text, script_prefix_string, keep_window_open=True, skip_launch=False):
    system = platform.system()
    if system == "Windows":
        script_extension = ".bat"
        script_header = "echo off\nchcp 65001\n\n"
        script_footer = ""
        if keep_window_open:
            script_footer = "\ncmd /k\n"
    else:
        # Darwin or Linux
        script_extension = ".sh"
        script_header = "#!/bin/bash\n\n"
        script_footer = ""

    blend_basename = bpy.path.basename(bpy.context.blend_data.filepath)
    blend_directory = os.path.dirname(bpy.data.filepath)

    script_name = script_prefix_string + blend_basename + script_extension
    script_filepath = os.path.join(blend_directory, script_name)

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

    skip_launch = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("skip_launch"))


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

        if hprops.cmd_bake_and_render_mode == 'CMD_BAKE_AND_RENDER_MODE_INTERLEAVED' and hprops.render_passes:
            self.report({'ERROR'}, "Compositing Tools Passes Rendering is not supported while in Render During Bake Mode. Passes rendering is only supported in Render After Bake mode.")
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

        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

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


### DF Add Passes here:

class FlipFluidPassesResetSettings(bpy.types.Operator):
    """Reset all visiblity settings to default"""
    bl_idname = "flip_fluid_operators.reset_passes_settings"
    bl_label = "Reset Passes Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        apply_visibility_settings_for_pass('reset')
        bpy.ops.flip_fluid_operators.reload_frame('INVOKE_DEFAULT')

        self.report({'INFO'}, "Pass settings have been reset.")
        return {'FINISHED'}

class FlipFluidHelperCommandLineRender(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render"
    bl_label = "Launch Render"
    bl_description = ("Launch a new command line window and start rendering the animation." +
                     " The .blend file will need to be saved before using this operator for changes to take effect")

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))

    skip_launch = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("skip_launch"))


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def is_render_output_format_image_required(self, context):
        hprops = context.scene.flip_fluid_helper 
        if hprops.render_passes:
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

        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            self.report({'ERROR'}, "System platform <" + platform.system() + "> not supported. This feature only supports Windows, MacOS, or Linux system platforms.")
            return {'CANCELLED'}


    def get_normal_render_command_text(self):
        if self.use_turbo_tools:
            command_text = "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" --python-expr \"import bpy; bpy.ops.threedi.render_animation()\""
        else:
            command_text = "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" -a"
        return command_text


    def get_single_frame_render_command_text(self, frameno):
        return "\"" + bpy.app.binary_path + "\" -b \"" + bpy.data.filepath + "\" -f " + str(frameno)


    def get_batch_render_command_text(self):
        hprops = bpy.context.scene.flip_fluid_helper
        directory_path, file_prefix, file_suffix = get_render_output_info()
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        frame_step = bpy.context.scene.frame_step

        frameno_list = list(range(frame_start, frame_end + 1, frame_step))
        if hprops.cmd_launch_render_animation_no_overwrite:
            filtered_frameno_list = []
            filename_list = os.listdir(directory_path)
            for frameno in frameno_list:
                frame_filename = file_prefix + str(frameno).zfill(4) + file_suffix
                frame_filename
                if frame_filename not in filename_list:
                    filtered_frameno_list.append(frameno)
            frameno_list = filtered_frameno_list

        command_text = ""
        for frameno in frameno_list:
            command_text += self.get_single_frame_render_command_text(frameno) + "\n"

        return command_text


    def get_multi_instance_render_command_text(self):
        hprops = bpy.context.scene.flip_fluid_helper
        num_instance_string = str(hprops.cmd_launch_render_animation_instances)
        use_overwrite_string = "0" if hprops.cmd_launch_render_animation_no_overwrite else "1"
        script_filepath = get_command_line_script_filepath("render_animation_multi_instance.py")

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_filepath + "\""
        command_text += " -- " + num_instance_string + " " + use_overwrite_string

        return command_text


    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        hprops = bpy.context.scene.flip_fluid_helper
        if hprops.render_passes:
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

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))


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

    use_turbo_tools = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("use_turbo_tools"))

    skip_launch = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("skip_launch"))


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
        if hprops.render_passes:
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

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\"" + " -- " + frame_string + " " + open_image_after

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

    skip_launch = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("skip_launch"))


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        save_blend_file_before_launch(override_preferences=False)
        restore_blender_original_cwd()

        script_path = get_command_line_script_filepath("alembic_export.py")
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""

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


class FlipFluidHelperCmdAlembicExportToClipboard(bpy.types.Operator):
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
        os.startfile(directory_path)
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


def get_render_passes_info(context):
    # Pass-Suffix-Liste mit den zugehoerigen Listen
    hprops = context.scene.flip_fluid_helper
    pass_suffixes = [
        ("BG_elements_only", hprops.render_passes_elements_only, hprops.render_passes_bg_elementslist),
        ("REF_elements_only", hprops.render_passes_elements_only, hprops.render_passes_ref_elementslist),
        ("objects_only", hprops.render_passes_objects_only, None),
        ("fluidparticles_only", hprops.render_passes_fluidparticles_only, None),
        ("fluid_only", hprops.render_passes_fluid_only, None),
        ("fluid_shadows_only", hprops.render_passes_fluid_shadows_only, None),
        ("reflr_only", hprops.render_passes_reflr_only, None),
        ("bubblesanddust_only", hprops.render_passes_bubblesanddust_only, None),
        ("foamandspray_only", hprops.render_passes_foamandspray_only, None),
        ("FG_elements_only", hprops.render_passes_elements_only, hprops.render_passes_fg_elementslist),
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

    skip_launch = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("skip_launch"))


    @classmethod
    def poll(cls, context):
        return (
            context.scene.flip_fluid.get_domain_object() is not None and
            bool(bpy.data.filepath) and
            context.scene.flip_fluid_helper.render_passes and
            context.scene.flip_fluid_helper.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_helper.render_passes_stillimagemode_toggle
        )


    def get_single_frame_render_pass_command_text(self, blend_filepath, frameno):
        return "\"" + bpy.app.binary_path + "\" -b \"" + blend_filepath + "\" -f " + str(frameno)


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
        script_filepath = get_command_line_script_filepath("render_animation_render_passes_multi_instance.py")

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_filepath + "\""
        command_text += " -- " + num_instance_string + " " + use_overwrite_string

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

        prepare_render_passes_for_operator(context)

        hprops = context.scene.flip_fluid_helper
        if hprops.cmd_launch_render_passes_animation_instances == 1:
            command_text = self.get_render_passes_batch_command_text(context)
        else:
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
            context.scene.flip_fluid_helper.render_passes and
            context.scene.flip_fluid_helper.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_helper.render_passes_stillimagemode_toggle
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

    skip_launch = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("skip_launch"))


    @classmethod
    def poll(cls, context):
        return (
            context.scene.flip_fluid.get_domain_object() is not None and
            bool(bpy.data.filepath) and
            context.scene.flip_fluid_helper.render_passes and
            context.scene.flip_fluid_helper.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_helper.render_passes_stillimagemode_toggle
        )


    def get_single_frame_render_pass_command_text(self, blend_filepath, frameno):
        return "\"" + bpy.app.binary_path + "\" -b \"" + blend_filepath + "\" -f " + str(frameno)


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

        prepare_render_passes_for_operator(context)

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
            context.scene.flip_fluid_helper.render_passes and
            context.scene.flip_fluid_helper.render_passes_is_any_pass_enabled and 
            not context.scene.flip_fluid_helper.render_passes_stillimagemode_toggle
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
    bpy.utils.register_class(FlipFluidHelperCmdRenderFrameToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineAlembicExport)
    bpy.utils.register_class(FlipFluidHelperCmdAlembicExportToClipboard)
    bpy.utils.register_class(FlipFluidHelperOpenRenderOutputFolder)
    bpy.utils.register_class(FlipFluidHelperOpenCacheOutputFolder)
    bpy.utils.register_class(FlipFluidHelperOpenAlembicOutputFolder)
    bpy.utils.register_class(FlipFluidPassesResetSettings)
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
    bpy.utils.unregister_class(FlipFluidHelperCmdRenderFrameToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineAlembicExport)
    bpy.utils.unregister_class(FlipFluidHelperCmdAlembicExportToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperOpenRenderOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperOpenCacheOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperOpenAlembicOutputFolder)
    bpy.utils.unregister_class(FlipFluidPassesResetSettings)
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
        km.keymap_items.remove(kmi)
    ADDON_KEYMAPS.clear()
