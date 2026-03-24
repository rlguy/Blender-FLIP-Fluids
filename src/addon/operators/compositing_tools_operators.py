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

import bpy, os, pathlib, math, datetime, re
from bpy_extras.io_utils import ImportHelper
from bpy.props import (
        StringProperty,
        CollectionProperty
        )

from ..filesystem import filesystem_protection_layer as fpl
from ..presets import render_passes 


def show_message_box(message="", title="Info", icon='INFO'):
    """Shows a popup message box with the given message."""
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


### PREPARE VISIBLITY SETTINGS FOR PASSES ###

# Console output can be toggled with "Domain > Debug > Display Render Passes Console Output" option
# This function can be used exactly like Python print_render_pass_debug()
def print_render_pass_debug(*args, **kwargs):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is not None and dprops.debug.display_render_passes_console_output:
        print_render_pass_debug(*args, **kwargs)


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
    bpy.context.scene.flip_fluid_compositing_tools.render_passes_toggle_projectiontester = value


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


def transfer_elements_to_elements_lists(cprops):
    # Clear elements lists
    cprops.render_passes_fg_elementslist.clear()
    cprops.render_passes_bg_elementslist.clear()
    cprops.render_passes_ref_elementslist.clear()
   
    for obj_prop in cprops.render_passes_objectlist:
        if obj_prop.fg_elements:
            new_fg_element = cprops.render_passes_fg_elementslist.add()
            print_render_pass_debug("added fg elemt")
            new_fg_element.name = obj_prop.name
        elif obj_prop.bg_elements:
            new_bg_element = cprops.render_passes_bg_elementslist.add()
            print_render_pass_debug("added bg elemt")
            new_bg_element.name = obj_prop.name
        elif obj_prop.ref_elements:
            new_ref_element = cprops.render_passes_ref_elementslist.add()
            print_render_pass_debug("added ref elemt")
            new_ref_element.name = obj_prop.name
          

def apply_visibility_settings_for_pass(pass_name):
    visibility_settings = render_passes.visibility_settings
    settings = visibility_settings.get(pass_name, {})
    cprops = bpy.context.scene.flip_fluid_compositing_tools

    # Aktualisiere die Listen basierend auf den Flags
    transfer_elements_to_elements_lists(cprops)

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

        for obj_prop in cprops.render_passes_objectlist:
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

        for fg_elements_prop in cprops.render_passes_fg_elementslist:
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

        for bg_elements_prop in cprops.render_passes_bg_elementslist:
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

        for ref_elements_prop in cprops.render_passes_ref_elementslist:
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

        for obj_prop in cprops.render_passes_objectlist:
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
    cprops = bpy.context.scene.flip_fluid_compositing_tools

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
            (s for s in cprops.render_passes_shadowcatcher_state if s.name == obj.name),
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
    cprops = bpy.context.scene.flip_fluid_compositing_tools

    # Print message if render_passes is disabled
    if not cprops.render_passes:
        print_render_pass_debug("Render passes are disabled, but blend files will still be generated.")

    blend_file_directory = os.path.dirname(bpy.data.filepath)
    base_file_name = pathlib.Path(bpy.path.basename(bpy.data.filepath)).stem

    transfer_elements_to_elements_lists(cprops)

    # Initial list of suffixes with their corresponding lists
    pass_suffixes = [
        ("BG_elements_only",    cprops.render_passes_elements_only,         cprops.render_passes_bg_elementslist),
        ("REF_elements_only",   cprops.render_passes_elements_only,         cprops.render_passes_ref_elementslist),
        ("objects_only",        cprops.render_passes_objects_only,          None),
        ("fluidparticles_only", cprops.render_passes_fluidparticles_only,   None),
        ("fluid_only",          cprops.render_passes_fluid_only,            None),
        ("fluid_shadows_only",  cprops.render_passes_fluid_shadows_only,    None),
        ("reflr_only",          cprops.render_passes_reflr_only,            None),
        ("bubblesanddust_only", cprops.render_passes_bubblesanddust_only,   None),
        ("foamandspray_only",   cprops.render_passes_foamandspray_only,     None),
        ("FG_elements_only",    cprops.render_passes_elements_only,         cprops.render_passes_fg_elementslist),
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

            # Safe method for deleting files to avoid accidental data loss
            fpl.delete_file(file_path)
            print_render_pass_debug(f"Deleted old blend file: {file_path}")

    # Reset cache if needed
    clear_simulation_meshes_before_saving = True
    if clear_simulation_meshes_before_saving:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.reset_cache_objects()

    original_render_output_path = bpy.context.scene.render.filepath

    # For property retrieval/restoration
    cprops = bpy.context.scene.flip_fluid_compositing_tools

    # Generate new files
    for idx, (suffix, _, _) in enumerate(filtered_suffixes):
        number = idx + 1

        # -- Always store and override fluidfinder for each suffix --
        original_finder_val = cprops.render_passes_toggle_projectiontester
        toggle_fluidfinder(False)

        # We'll define original_fade_val here, so we can use it conditionally below
        original_fade_val = None

        if suffix == "reflr_only":
            toggle_onlyreflections(1.0)
            toggle_transparent_or_holdout(1.0)
            bpy.context.scene.render.use_compositing = True

            # Save original fade value and set it to 0
            original_fade_val = cprops.render_passes_blend_footage_to_fluidsurface
            toggle_footageprojection(0.0)

        elif suffix == "objects_only":
            toggle_transparent_or_holdout(1.0)

        elif suffix == "fluid_only":
            toggle_transparent_or_holdout(1.0)

            # Save original fade value and set it to 0
            original_fade_val = cprops.render_passes_blend_footage_to_fluidsurface
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
    cprops = bpy.context.scene.flip_fluid_compositing_tools
    cleanup_object_list_for_operator(cprops.render_passes_objectlist)


### END OF PREPARE VISIBLITY SETTINGS FOR PASSES ###
        

### Compositing Tools ###
## 1st release version ##

def setup_compositor_for_indirect_passes():
    """
    This function sets up the Blender Compositor to:
    - Use a 'Render Layers' node (linked to the active scene layer).
    - Extract the 'Glossy Indirect' and 'Transmission Indirect' passes.
    - Add them together using a Math (Add) node.
    - Use the result as an Alpha mask in a 'Set Alpha' node.
    - Output the processed image to both a Composite and Viewer node.
    """

    # Enable compositing nodes
    scene = bpy.context.scene
    scene.use_nodes = True
    node_tree = scene.node_tree

    # Clear existing nodes
    node_tree.nodes.clear()

    # Step 1: Create Render Layers node
    render_layers_node = node_tree.nodes.new("CompositorNodeRLayers")
    render_layers_node.location = (-500, 0)
    render_layers_node.label = "Render Layers (Indirect Setup)"

    # Step 2: Create Math Add node (Glossy + Transmission)
    math_add_node = node_tree.nodes.new("CompositorNodeMath")
    math_add_node.location = (-200, 100)
    math_add_node.operation = 'ADD'
    math_add_node.label = "Glossy + Transmission"

    # Step 3: Create Set Alpha node
    set_alpha_node = node_tree.nodes.new("CompositorNodeSetAlpha")
    set_alpha_node.location = (100, 100)
    set_alpha_node.mode = 'REPLACE_ALPHA'
    set_alpha_node.label = "Set Alpha (Glossy + Transmission)"

    # Step 4: Create Composite node
    composite_node = node_tree.nodes.new("CompositorNodeComposite")
    composite_node.location = (400, 200)
    composite_node.label = "Composite (Indirect)"

    # Step 5: Create Viewer node
    viewer_node = node_tree.nodes.new("CompositorNodeViewer")
    viewer_node.location = (400, -100)
    viewer_node.label = "Viewer (Indirect)"

    # -- Link everything up --
    links = node_tree.links

    # a) Link Glossy Indirect -> Math Add (Input 1)
    if "GlossInd" in render_layers_node.outputs:
        links.new(render_layers_node.outputs["GlossInd"], math_add_node.inputs[0])

    # b) Link Transmission Indirect -> Math Add (Input 2)
    if "TransInd" in render_layers_node.outputs:
        links.new(render_layers_node.outputs["TransInd"], math_add_node.inputs[1])

    # c) Link Render Layers Image -> Set Alpha (Image)
    links.new(render_layers_node.outputs["Image"], set_alpha_node.inputs["Image"])

    # d) Link Math Add (Value) -> Set Alpha (Alpha)
    links.new(math_add_node.outputs[0], set_alpha_node.inputs["Alpha"])

    # e) Link Set Alpha (Image) -> Composite Node (Image)
    links.new(set_alpha_node.outputs["Image"], composite_node.inputs["Image"])

    # f) Link Set Alpha (Image) -> Viewer Node (Image)
    links.new(set_alpha_node.outputs["Image"], viewer_node.inputs["Image"])

    print_render_pass_debug("Compositor setup for Indirect Passes is complete.")

# Requirement: Initialize all will prepare all settings for compositing
class FlipFluidOperatorsInitializeCompositing(bpy.types.Operator):
    """Initialize Compositing Tools"""
    bl_idname = "flip_fluid_operators.helper_initialize_compositing"
    bl_label = "Initialize Compositing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        domain_obj = next(
            (obj for obj in bpy.data.objects if hasattr(obj, "flip_fluid") and obj.flip_fluid.object_type == 'TYPE_DOMAIN'),
            None
        )
        if not domain_obj:
            self.report({'ERROR'}, "No FLIP Fluids Domain object found.")
            return {'CANCELLED'}

        # Run the motion blur initialization operator
        bpy.ops.flip_fluid_operators.helper_initialize_motion_blur()

        # Set the required properties
        domain_obj.flip_fluid.domain.particles.enable_fluid_particle_velocity_vector_attribute = True
        domain_obj.flip_fluid.domain.whitewater.enable_velocity_vector_attribute = True
        domain_obj.flip_fluid.domain.surface.enable_velocity_vector_attribute = True
        # domain_obj.flip_fluid.domain.surface.remove_mesh_near_domain = True <- Seems not to be required. There are some advantages when set to FALSE
        domain_obj.flip_fluid.domain.surface.obstacle_meshing_mode = 'MESHING_MODE_OUTSIDE_SURFACE' # Helps to avoid shadow artifacts

        context.scene.render.engine = 'CYCLES'
        context.scene.render.film_transparent = True
        domain_obj.flip_fluid.domain.whitewater.enable_id_attribute = True

        # Enable Blender Passes on the active View Layer
        active_view_layer = context.view_layer
        if not active_view_layer:
            self.report({'WARNING'}, "No active view layer found. Could not enable passes.")
        else:
            active_view_layer.use_pass_glossy_indirect = True
            active_view_layer.use_pass_transmission_indirect = True

        # Set Light Paths for Full Global Illumination
        cycles = context.scene.cycles
        cycles.max_bounces = 32
        cycles.diffuse_bounces = 32
        cycles.glossy_bounces = 32
        cycles.transmission_bounces = 32
        cycles.volume_bounces = 32
        cycles.transparent_max_bounces = 32

        # Enable Caustics
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True

        # Set render resolution to quick 1st rendering
        context.scene.cycles.samples = 200


        # Check if GPU denoising is available
        gpu_denoiser_supported = (
            bpy.context.preferences.addons['cycles'].preferences.get_devices_for_type('CUDA') or
            bpy.context.preferences.addons['cycles'].preferences.get_devices_for_type('OPTIX') or
            bpy.context.preferences.addons['cycles'].preferences.get_devices_for_type('HIP') or
            bpy.context.preferences.addons['cycles'].preferences.get_devices_for_type('METAL')
        )

        if gpu_denoiser_supported:
            context.scene.cycles.denoising_use_gpu = True
            self.report({'INFO'}, "GPU Denoising enabled.")
        else:
            # Fallback to CPU denoising or disable it
            if hasattr(context.scene.cycles, "use_denoising"):
                context.scene.cycles.use_denoising = True  # Enable CPU denoising if available
                self.report({'WARNING'}, "GPU Denoising not supported. Falling back to CPU Denoising.")
            else:
                self.report({'WARNING'}, "Denoising not available. Rendering without denoising.")

        # Set View Transform to STANDARD
        context.scene.view_settings.view_transform = "Standard"

        # Check if all conditions are met
        conditions_met = (
            domain_obj.flip_fluid.domain.particles.enable_fluid_particle_velocity_vector_attribute and
            domain_obj.flip_fluid.domain.whitewater.enable_velocity_vector_attribute and
            domain_obj.flip_fluid.domain.surface.enable_velocity_vector_attribute and
            #domain_obj.flip_fluid.domain.surface.remove_mesh_near_domain and
            #context.scene.render.engine == 'CYCLES' and
            context.scene.render.film_transparent and
            domain_obj.flip_fluid.domain.whitewater.enable_id_attribute
        )

        if not conditions_met:
            self.report({'ERROR'}, "Compositing initialization failed. Check settings.")
            return {'CANCELLED'}

        # Set up the compositor
        #setup_compositor_for_indirect_passes() Disabled because of issues with colors/gamma when saving the files

        # Disable Compositing to be only enabled in refl-pass
        bpy.context.scene.render.use_compositing = False

        self.report({'INFO'}, "Compositing initialized successfully.")
        return {'FINISHED'}


# List for objects
# FG Element - Foreground Elements (don?t receive any shadows)
# BG Element - Background Elements (Receive shadows)
# ref_elements - Background Elements (Receive reflections & shadows)

# Function to set objects-fading-property
def update_unflagged_objects_property(context):
    """
    Updates the 'render_passes_has_unflagged_objects' property based on the object list.
    """
    cprops = context.scene.flip_fluid_compositing_tools
    has_unflagged = any(
        not (item.fg_elements or item.bg_elements or item.ref_elements or item.ground)
        for item in cprops.render_passes_objectlist
    )
    cprops.render_passes_has_unflagged_objects = has_unflagged
    bpy.context.view_layer.update()


def assign_objects_to_fading_network(context):
    """
    Assigns unflagged objects from the render passes object list to the fading network nodes.

    Args:
        context: Blender context for accessing scene-specific data.
    """
    # Update the unflagged objects property to ensure it's up-to-date
    update_unflagged_objects_property(context)

    # Get helper properties from the context
    cprops = context.scene.flip_fluid_compositing_tools

    # Check if there are unflagged objects
    if not cprops.render_passes_has_unflagged_objects:
        print_render_pass_debug("INFO: No unflagged objects available for assignment")
        return

    # Get the geometry node group
    geo_node = bpy.data.node_groups.get("FF_FadeNearObjects")
    if not geo_node:
        print_render_pass_debug("WARNING: Node group 'FF_FadeNearObjects' not found")
        return

    # Get the Object Info nodes from the geometry node group
    object_info_nodes = [
        geo_node.nodes.get(f"ff_fading_objects_{i}") for i in range(1, 11)
    ]
    object_info_nodes = [node for node in object_info_nodes if node]

    if not object_info_nodes:
        print_render_pass_debug("WARNING: No valid nodes found in 'FF_FadeNearObjects'")
        return

    # Iterate over the object list and assign only unflagged objects to free nodes
    for item in cprops.render_passes_objectlist:
        # Skip objects that already have an assigned node
        if item.assigned_node:
            continue

        # Skip flagged objects (based on your logic: flagged if any of these properties are True)
        if item.fg_elements or item.bg_elements or item.ref_elements or item.ground:
            print_render_pass_debug(f"INFO: Skipping flagged object {item.name}")
            continue

        # Find the next free node
        free_node = next(
            (node for node in object_info_nodes if not node.inputs["Object"].default_value),
            None
        )

        if free_node:
            # Assign the object to the node
            free_node.inputs["Object"].default_value = bpy.data.objects.get(item.name)
            item.assigned_node = free_node.name
            print_render_pass_debug(f"INFO: Assigned {item.name} to {free_node.name}")
        else:
            print_render_pass_debug(f"WARNING: No free node available for {item.name}")

    # Update the node group to reflect changes
    geo_node.update_tag()

    # Update the fader combination
    update_fader_combination_fluidsurface(context)


class FLIPFLUID_UL_passes_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)

            obj = bpy.data.objects.get(item.name)
            fade_depress = False
            fade_enabled = False

            if obj and obj.active_material and obj.active_material.node_tree:
                fade_node = obj.active_material.node_tree.nodes.get("ff_elements_fading")
                if fade_node:
                    fade_enabled = True
                    fade_depress = (fade_node.inputs[0].default_value == 0.0)

            # Check if the object is in the MediaProperty list and override fade_depress
            cprops = context.scene.flip_fluid_compositing_tools
            if any(media_item.object_name == item.name for media_item in cprops.render_passes_import_media):
                fade_enabled = True

            # Create row for F and C buttons, with scaling 0.3
            row_fade = row.row(align=True)
            row_fade.scale_x = 0.3
            row_fade.enabled = fade_enabled  # This applies to the F button

            # --- Fader Button ("F") ---
            fade_button = row_fade.operator(
                "flip_fluid_operators.toggle_fade",
                text="F",
                depress=fade_depress
            )
            fade_button.index = index

            # --- Shadow Catcher Button ("C") ---
            c_enabled = item.bg_elements or item.ref_elements  # Only enabled if BG or REF is active
            shadowcatcher_depress = obj.is_shadow_catcher if obj else False

            # Add the "C" button, explicitly setting its enabled state
            c_box = row_fade.row(align=True)
            c_box.scale_x = 0.5  # Ensures same size as "F"
            c_box.enabled = c_enabled  # Disable button if not BG or REF

            c_button = c_box.operator(
                "flip_fluid_operators.toggle_shadowcatcher",
                text="C",
                depress=shadowcatcher_depress if c_enabled else False  # Ensure proper color when disabled
            )
            c_button.index = index

            # Continue with the rest of the UI layout
            split = row.split(factor=0.5, align=True)
            column1 = split.column(align=True)
            op = column1.operator("flip_fluid_operators.select_object_in_list", text=item.name, icon='MESH_CUBE')
            op.index = index

            column2 = split.column(align=True)
            row_flags = column2.row(align=True)

            fg_button = row_flags.operator("flip_fluid_operators.toggle_fg_elements", text="FG", depress=item.fg_elements)
            fg_button.index = index

            bg_button = row_flags.operator("flip_fluid_operators.toggle_bg_elements", text="BG", depress=item.bg_elements)
            bg_button.index = index

            reflective_button = row_flags.operator("flip_fluid_operators.toggle_reflective", text="REF", depress=item.ref_elements)
            reflective_button.index = index

            ground_button = row_flags.operator("flip_fluid_operators.toggle_ground", text="GND", depress=item.ground)
            ground_button.index = index


# Operator for toggling ff_elements_fading node
class FlipFluidPassesToggleFade(bpy.types.Operator):
    """Toggle the 'ff_elements_fading' Node between default_value 0.0 and 1.0."""
    bl_idname = "flip_fluid_operators.toggle_fade"
    bl_label = "Toggle Fading"

    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        item = cprops.render_passes_objectlist[self.index]
        obj = bpy.data.objects.get(item.name)

        if not obj or not obj.active_material or not obj.active_material.node_tree:
            self.report({'WARNING'}, "Object or material not found.")
            return {'CANCELLED'}

        node_tree = obj.active_material.node_tree
        fade_node = node_tree.nodes.get("ff_elements_fading")
        if not fade_node:
            self.report({'WARNING'}, "Fading node not found in the material.")
            return {'CANCELLED'}

        # Switch 0.0 or 1.0
        fade_node.inputs[0].default_value = 1.0 if fade_node.inputs[0].default_value == 0.0 else 0.0

        return {'FINISHED'}


class FlipFluidPassesToggleShadowCatcher(bpy.types.Operator):
    """Toggle the object's Shadow Catcher state, or update it based on BG/REF state."""
    bl_idname = "flip_fluid_operators.toggle_shadowcatcher"
    bl_label = "Toggle Shadow Catcher"

    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        item = cprops.render_passes_objectlist[self.index]
        obj = bpy.data.objects.get(item.name)

        if not obj:
            self.report({'WARNING'}, "Object not found.")
            return {'CANCELLED'}

        # Suche nach einem bereits gespeicherten Zustand in render_passes_shadowcatcher_state
        existing_entry = next((entry for entry in cprops.render_passes_shadowcatcher_state if entry.name == obj.name), None)

        # --- Benutzer klickt auf den "C" Button im UI ---
        if context.area.type == 'VIEW_3D':  
            obj.is_shadow_catcher = not obj.is_shadow_catcher  # Toggle Zustand
            
            if existing_entry:
                existing_entry.is_shadow_catcher = obj.is_shadow_catcher  # Update gespeicherten Wert
            else:
                new_entry = cprops.render_passes_shadowcatcher_state.add()
                new_entry.name = obj.name
                new_entry.is_shadow_catcher = obj.is_shadow_catcher  # Speichere Wert

        else:
            # --- Automatisches Update basierend auf BG/REF Status ---
            if item.bg_elements or item.ref_elements:
                if existing_entry:
                    obj.is_shadow_catcher = existing_entry.is_shadow_catcher  # Wiederherstellen des gespeicherten Werts
            else:
                # Falls das Objekt vorher ein Shadow Catcher war, speichere diesen Zustand
                if obj.is_shadow_catcher:
                    if existing_entry:
                        existing_entry.is_shadow_catcher = obj.is_shadow_catcher  
                    else:
                        new_entry = cprops.render_passes_shadowcatcher_state.add()
                        new_entry.name = obj.name
                        new_entry.is_shadow_catcher = obj.is_shadow_catcher  
                
                obj.is_shadow_catcher = False  # Falls nicht BG/REF, ShadowCatcher deaktivieren

        return {'FINISHED'}


# Operator to add items to object list
class FlipFluidPassesAddItemToList(bpy.types.Operator):
    """Add selected items to the list of objects for rendering and update Geometry Nodes"""
    bl_idname = "flip_fluid_operators.add_item_to_list"
    bl_label = "Add Item to List"

    def execute(self, context):
        # List of objects that should not be added to the list
        excluded_objects = [
            "fluid_surface",
            "whitewater_bubble",
            "whitewater_dust",
            "whitewater_foam",
            "whitewater_spray",
            "fluid_particles",
            "ff_camera_screen",
            "ff_alignment_grid"
        ]

        # Automatically find FLIP Fluids Domain objects and exclude them
        domain_objects = [
            obj.name for obj in bpy.data.objects
            if hasattr(obj, "flip_fluid") and obj.flip_fluid.object_type == 'TYPE_DOMAIN'
        ]
        excluded_objects.extend(domain_objects)

        cprops = context.scene.flip_fluid_compositing_tools
        added_objects = 0

        # Try to retrieve Geometry Nodes network
        geo_node = bpy.data.node_groups.get("FF_FadeNearObjects")
        object_info_nodes = []

        if geo_node:
            # Retrieve Object Info Nodes if Geometry Nodes exist
            object_info_nodes = [geo_node.nodes.get(f"ff_fading_objects_{i}") for i in range(1, 11)]
            object_info_nodes = [node for node in object_info_nodes if node]

        # Check selected objects and add them to the list
        for obj in bpy.context.selected_objects:
            if obj.name in excluded_objects:
                show_message_box(f"{obj.name} cannot be added to the render pass list.", title="Excluded Object", icon='MOD_FLUIDSIM')
            elif obj.type == 'EMPTY':
                if len(obj.children) == 0:
                    show_message_box(f"{obj.name} is an empty object with no children and cannot be added to the render pass list.", title="Empty Object", icon='INFO')
                else:
                    for child in obj.children:
                        if child.name in excluded_objects:
                            show_message_box(f"{child.name} cannot be added to the render pass list.", title="Excluded Object", icon='MOD_FLUIDSIM')
                        elif any(item.name == child.name for item in cprops.render_passes_objectlist):
                            show_message_box(f"{child.name} is already in the render pass list.", title="Duplicate Object", icon='INFO')
                        else:
                            assigned_node = ""
                            if geo_node and object_info_nodes:
                                assigned_nodes = {item.assigned_node for item in cprops.render_passes_objectlist if item.assigned_node}
                                free_node = next((node for node in object_info_nodes if node.name not in assigned_nodes and not node.inputs["Object"].default_value), None)
                                if free_node:
                                    free_node.inputs["Object"].default_value = child
                                    assigned_node = free_node.name

                            item = cprops.render_passes_objectlist.add()
                            item.name = child.name
                            item.data_name = child.data.name
                            item.assigned_node = assigned_node
                            added_objects += 1
            else:
                if any(item.name == obj.name for item in cprops.render_passes_objectlist):
                    show_message_box(f"{obj.name} is already in the render pass list.", title="Duplicate Object", icon='INFO')
                else:
                    assigned_node = ""
                    if geo_node and object_info_nodes:
                        assigned_nodes = {item.assigned_node for item in cprops.render_passes_objectlist if item.assigned_node}
                        free_node = next((node for node in object_info_nodes if node.name not in assigned_nodes and not node.inputs["Object"].default_value), None)
                        if free_node:
                            free_node.inputs["Object"].default_value = obj
                            assigned_node = free_node.name

                    item = cprops.render_passes_objectlist.add()
                    item.name = obj.name
                    item.data_name = obj.data.name
                    item.assigned_node = assigned_node
                    added_objects += 1

        # Handle nodes based on Flags
        for item in cprops.render_passes_objectlist:
            if item.name in [obj.name for obj in bpy.context.selected_objects]:
                if item.fg_elements or item.bg_elements or item.ref_elements or item.ground:
                    # Remove object from nodes if it has a flag
                    if geo_node and item.assigned_node:
                        node = geo_node.nodes.get(item.assigned_node)
                        if node:
                            node.inputs["Object"].default_value = None

                        item.assigned_node = ""

        # Call function to collect all objects and materials from objects-list
        collect_all_objects_materials(context)

        # Call function to set objects-fading-property
        update_unflagged_objects_property(context)

        # Set the index to the last added object in the list
        if added_objects > 0:
            cprops.render_passes_objectlist_index = len(cprops.render_passes_objectlist) - 1

        # Call function to assign object to fading network
        assign_objects_to_fading_network(context)


        return {'FINISHED'}


class FlipFluidPassesDuplicateItemInList(bpy.types.Operator):
    """Duplicate an object from the list, including material and FADER"""
    bl_idname = "flip_fluid_operators.duplicate_item_in_list"
    bl_label = "Duplicate Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        # Ensure a valid object is selected in the list
        selected_index = cprops.render_passes_objectlist_index
        if selected_index < 0 or selected_index >= len(cprops.render_passes_objectlist):
            self.report({'ERROR'}, "No valid object selected. Please select an object from the list.")
            return {'CANCELLED'}

        # Retrieve the original object and its data
        original_item = cprops.render_passes_objectlist[selected_index]
        original_obj = bpy.data.objects.get(original_item.name)
        if not original_obj:
            self.report({'ERROR'}, f"Original object '{original_item.name}' not found.")
            return {'CANCELLED'}

        # Prevent duplication of Ground objects
        if original_item.ground:
            self.report({'ERROR'}, "Ground objects cannot be duplicated. Only one Ground object is allowed.")
            return {'CANCELLED'}

        # Duplicate the object
        new_obj = original_obj.copy()
        new_obj.data = original_obj.data.copy()
        bpy.context.collection.objects.link(new_obj)
        new_obj.name = f"{original_obj.name}_duplicate"

        # Duplicate the material and update its nodes
        if original_obj.data.materials:
            original_material = original_obj.data.materials[0]

            # Adjust the material name to insert `_duplicate` before `_@`
            if original_material.name.endswith("_@"):
                material_name_base = original_material.name[:-2]  # Remove "_@"
                new_material_name = f"{material_name_base}_duplicate_@"
            else:
                new_material_name = f"{original_material.name}_duplicate"

            # Duplicate and rename the material
            new_material = original_material.copy()
            new_material.name = new_material_name

            # Assign the duplicated material to the new object
            new_obj.data.materials.clear()
            new_obj.data.materials.append(new_material)

            # Update material nodes with the new FADER
            if new_material.use_nodes:
                node_tree = new_material.node_tree
                fader_node = node_tree.nodes.get("ff_compositing_shadowcatcher_fadercoordinate")
                if fader_node:
                    # Duplicate the FADER object
                    original_fader_name = f"FADER.{original_obj.name}_@"
                    fader_obj = bpy.data.objects.get(original_fader_name)
                    if fader_obj:
                        new_fader = self.duplicate_fader(context, fader_obj, new_obj.name)
                        fader_node.object = new_fader

        # Add the duplicated object to the list
        new_item = cprops.render_passes_objectlist.add()
        new_item.name = new_obj.name
        new_item.data_name = new_obj.data.name

        # Set the same FLAG as the original object
        new_item.fg_elements = original_item.fg_elements
        new_item.bg_elements = original_item.bg_elements
        new_item.ref_elements = original_item.ref_elements
        new_item.ground = original_item.ground

        # Update the DICT with the new FADER and material
        self.update_fader_dict(context, new_obj, new_material)

        # Call function to set objects-fading-property
        update_unflagged_objects_property(context)

        # Call function to assign object to fading network
        assign_objects_to_fading_network(context)

        # Refresh Object List
        bpy.ops.flip_fluid_operators.refresh_objectlist()

        self.report({'INFO'}, f"Object '{new_obj.name}' duplicated successfully.")
        return {'FINISHED'}

    def duplicate_fader(self, context, original_fader, new_obj_name):
        """Duplicate the FADER object with exact transformations and parent to the new object"""
        # Duplicate the original FADER
        new_fader = original_fader.copy()
        new_fader.name = f"FADER.{new_obj_name}_@"
        bpy.context.collection.objects.link(new_fader)

        # Store the original world matrix
        original_world_matrix = original_fader.matrix_world.copy()

        # Parent the new FADER to the new object
        new_parent = bpy.data.objects.get(new_obj_name)
        new_fader.parent = new_parent

        # Recalculate the parent inverse matrix to maintain the original world transformation
        if new_parent:
            new_fader.matrix_parent_inverse = new_parent.matrix_world.inverted()
            new_fader.matrix_world = original_world_matrix

        return new_fader

    def update_fader_dict(self, context, obj, material):
        """Update the FADER DICT with the new object and material"""
        cprops = context.scene.flip_fluid_compositing_tools
        fader_dict = cprops.render_passes_faderobjects_DICT

        # Construct FADER name
        fader_name = f"FADER.{obj.name}_@"
        fader_obj = bpy.data.objects.get(fader_name)

        # Update or add the new entry to the DICT
        existing_entry = next((entry for entry in fader_dict if entry.obj_name == obj.name), None)
        if existing_entry:
            existing_entry.node_object = fader_obj
            existing_entry.material_name = material.name
        else:
            new_entry = fader_dict.add()
            new_entry.obj_name = obj.name
            new_entry.node_object = fader_obj
            new_entry.material_name = material.name


# Operator to remove items from object list
class FlipFluidPassesRemoveItemFromList(bpy.types.Operator):
    """Remove an item from the list of objects for rendering and clear associated Object Info Node"""
    bl_idname = "flip_fluid_operators.remove_item_from_list"
    bl_label = "Remove Item from List"
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        # Ensure the index is within valid range
        if 0 <= self.index < len(cprops.render_passes_objectlist):
            # Get the item to be removed
            item = cprops.render_passes_objectlist[self.index]

            # Clear the associated Object Info Node
            assigned_node_name = item.assigned_node
            if assigned_node_name:
                geo_node = bpy.data.node_groups.get("FF_FadeNearObjects")
                if geo_node:
                    node = geo_node.nodes.get(assigned_node_name)
                    if node and node.type == 'OBJECT_INFO':
                        node.inputs["Object"].default_value = None  # Clear the object reference

            # Remove the item from the list
            cprops.render_passes_objectlist.remove(self.index)

            # Adjust the selected index
            cprops.render_passes_objectlist_index = min(max(0, self.index - 1), len(cprops.render_passes_objectlist) - 1)

        # Call function to set objects-fading-property
        update_unflagged_objects_property(context)

        # Call function to assign object to fading network
        assign_objects_to_fading_network(context)

        return {'FINISHED'}


def toggle_render_pass_flag(context, obj_name, flag_name, fgbg_value, reflective_value, enable_flag):
    """Toggle a render pass flag and update materials, nodes, and FADER objects."""
    cprops = context.scene.flip_fluid_compositing_tools
    all_objects_dict = cprops.render_passes_all_objects_materials_DICT
    fader_dict = cprops.render_passes_faderobjects_DICT

    blend_filename = "FF_Compositing.blend"
    parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_filepath = os.path.join(parent_path, "presets", "preset_library", "sys", blend_filename)

    if not os.path.exists(resource_filepath):
        raise FileNotFoundError(f"Blend file not found: {resource_filepath}")

    obj = bpy.data.objects.get(obj_name)
    if not obj:
        raise ValueError(f"Object '{obj_name}' not found.")

    # Suche nach einem bereits gespeicherten ShadowCatcher-Zustand
    existing_entry = next((entry for entry in cprops.render_passes_shadowcatcher_state if entry.name == obj_name), None)

    # **Speicherung des ShadowCatcher-Status, wenn BG/REF deaktiviert wird**
    if not enable_flag and flag_name in ("bg_elements", "ref_elements"):
        if obj.is_shadow_catcher:  
            if existing_entry:
                existing_entry.is_shadow_catcher = obj.is_shadow_catcher  # Update gespeicherten Wert
            else:
                new_entry = cprops.render_passes_shadowcatcher_state.add()
                new_entry.name = obj.name
                new_entry.is_shadow_catcher = obj.is_shadow_catcher  # Speichere neuen Wert
        obj.is_shadow_catcher = False

    # **Wiederherstellen des ShadowCatcher-Status, wenn BG/REF aktiviert wird**
    elif enable_flag and flag_name in ("bg_elements", "ref_elements"):
        if existing_entry:
            obj.is_shadow_catcher = existing_entry.is_shadow_catcher  # Setze gespeicherten Wert zurück

    # **Deaktiviere ShadowCatcher für FG/GND**
    elif flag_name in ("fg_elements", "ground"):
        obj.is_shadow_catcher = False 

    # Ensure only one Ground object exists
    if flag_name == "ground" and enable_flag:
        for item in cprops.render_passes_objectlist:
            if item.ground:
                show_message_box(
                    f"Only one object can be flagged as 'Ground'. '{item.name}' is already flagged.",
                    title="Ground Flag Conflict",
                    icon='ERROR'
                )
                return

    flipfluidpasses_createfaderobjects(context, [obj])

    # Construct expected FADER name
    expected_fader_name = f"FADER.{obj_name}_@"

    # Try to get the FADER object
    fader_object = bpy.data.objects.get(expected_fader_name)

    # Retrieve Geometry Nodes network
    geo_node = bpy.data.node_groups.get("FF_FadeNearObjects")
    object_info_nodes = []
    if geo_node:
        object_info_nodes = [geo_node.nodes.get(f"ff_fading_objects_{i}") for i in range(1, 11)]
        object_info_nodes = [node for node in object_info_nodes if node]

    # Disable all flags if the flag is being disabled
    if not enable_flag:
        for item in cprops.render_passes_objectlist:
            if item.name == obj_name:
                item.fg_elements = False
                item.bg_elements = False
                item.ref_elements = False
                item.ground = False

        # Restore the original material
        original_material = next(
            (entry.original_materialname for entry in all_objects_dict if entry.obj_name == obj_name), None
        )
        if original_material:
            material = bpy.data.materials.get(original_material)
            if material:
                obj.data.materials.clear()
                obj.data.materials.append(material)
                print_render_pass_debug(f"Restored original material '{original_material}' for object '{obj_name}'.")

        # Remove Modifiers if all toggles are off
        if obj:
            remove_modifiers_if_no_toggles(obj, cprops)

        # Reassign object to a free node if no flags are set
        for item in cprops.render_passes_objectlist:
            if item.name == obj_name and not (item.fg_elements or item.bg_elements or item.ref_elements or item.ground):
                assigned_nodes = {item.assigned_node for item in cprops.render_passes_objectlist if item.assigned_node}
                free_node = next((node for node in object_info_nodes if node.name not in assigned_nodes and not node.inputs["Object"].default_value), None)
                if free_node:
                    free_node.inputs["Object"].default_value = obj
                    item.assigned_node = free_node.name
        
        # Refresh Object List
        bpy.ops.flip_fluid_operators.refresh_objectlist()

        return

    # Enable the specified flag
    for item in cprops.render_passes_objectlist:
        if item.name == obj_name:
            item.fg_elements = (flag_name == "fg_elements")
            item.bg_elements = (flag_name == "bg_elements")
            item.ref_elements = (flag_name == "ref_elements")
            item.ground = (flag_name == "ground")

    # Construct the expected Passes Material name
    passes_material_base_name = f"FF Elements_Passes_{obj_name}"
    passes_material_name = passes_material_base_name if not passes_material_base_name.endswith("_@") else passes_material_base_name

    # Check if the material is already assigned
    current_material = obj.data.materials[0] if obj.data.materials else None
    if current_material and current_material.name.startswith("FF Elements_Passes"):
        material = current_material  # Ensure material is defined for node updates
    else:
        # Check if the material already exists
        material = bpy.data.materials.get(passes_material_name)
        if not material:
            material_name = "FF Elements_Passes"
            base_material = bpy.data.materials.get(material_name)

            if not base_material:
                with bpy.data.libraries.load(resource_filepath, link=False) as (data_from, data_to):
                    if material_name in data_from.materials:
                        data_to.materials = [material_name]
                    else:
                        raise ValueError(f"Material '{material_name}' not found in Blend file.")
                base_material = bpy.data.materials.get(material_name)

            # Duplicate and rename the material
            material = base_material.copy()
            material.name = passes_material_name
            material.asset_clear()

        # Assign the Passes material to the object
        obj.data.materials.clear()
        obj.data.materials.append(material)

    # Update Mix-Node values in the material
    if material.use_nodes:
        node_tree = material.node_tree
        fgbg_node = node_tree.nodes.get("ff_fgbg_element")
        reflective_node = node_tree.nodes.get("ff_reflective_element")
        fader_coordinate_node = node_tree.nodes.get("ff_compositing_shadowcatcher_fadercoordinate")

        if fgbg_node and reflective_node and fader_coordinate_node:
            # Update node outputs
            fgbg_node.outputs[0].default_value = fgbg_value
            reflective_node.outputs[0].default_value = reflective_value

            # Construct expected FADER name
            expected_fader_name = f"FADER.{obj_name}_@"

            # Try to get the FADER object
            fader_object = bpy.data.objects.get(expected_fader_name)

            # Update fader_dict with the FADER object
            fader_entry = next((entry for entry in fader_dict if entry.obj_name == obj_name), None)
            if fader_entry:
                fader_entry.node_object = fader_object
                fader_entry.material_name = material.name
            else:
                new_entry = fader_dict.add()
                new_entry.obj_name = obj_name
                new_entry.node_object = fader_object
                new_entry.material_name = material.name

            # Assign the FADER object to the node
            if fader_coordinate_node:
                fader_coordinate_node.object = fader_object

    # Remove object from nodes if any flag is enabled
    if enable_flag and geo_node:
        for item in cprops.render_passes_objectlist:
            if item.name == obj_name and item.assigned_node:
                node = geo_node.nodes.get(item.assigned_node)
                if node:
                    node.inputs["Object"].default_value = None

                item.assigned_node = ""

    # Fix Textures
    bpy.ops.flip_fluid_operators.helper_fix_compositingtextures()

    # Call function to set objects-fading-property
    update_unflagged_objects_property(context)

    # Refresh Object List
    bpy.ops.flip_fluid_operators.refresh_objectlist()

    return {'FINISHED'}


class FlipFluidPassesTogglefg_elements(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_fg_elements"
    bl_label = "Toggle FG Element"

    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        if 0 <= self.index < len(cprops.render_passes_objectlist):
            item = cprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "fg_elements", fgbg_value=0, reflective_value=0, enable_flag=not item.fg_elements)
        return {'FINISHED'}


class FlipFluidPassesTogglebg_elements(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_bg_elements"
    bl_label = "Toggle BG Element"

    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        if 0 <= self.index < len(cprops.render_passes_objectlist):
            item = cprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "bg_elements", fgbg_value=1, reflective_value=0, enable_flag=not item.bg_elements)
        return {'FINISHED'}


class FlipFluidPassesToggleReflective(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_reflective"
    bl_label = "Toggle Reflective"

    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        if 0 <= self.index < len(cprops.render_passes_objectlist):
            item = cprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "ref_elements", fgbg_value=1, reflective_value=1, enable_flag=not item.ref_elements)
        return {'FINISHED'}


class FlipFluidPassesToggleGround(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_ground"
    bl_label = "Toggle Ground"

    index: bpy.props.IntProperty()

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        if 0 <= self.index < len(cprops.render_passes_objectlist):
            item = cprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "ground", fgbg_value=0, reflective_value=0, enable_flag=not item.ground)
        return {'FINISHED'}


class FlipFluidPassesSelectObjectInList(bpy.types.Operator):
    """Select object in the viewport and Outliner when clicked in the list.
    If the same object has a FADER object as parent, toggle the selection 
    between the main object and the FADER object on repeated clicks."""
    bl_idname = "flip_fluid_operators.select_object_in_list"
    bl_label = "Select Object"

    index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        # Ensure the operator can only run in Object Mode
        return context.mode == 'OBJECT'

    def toggle_selection(self, obj, fader_obj, active_obj, context):
        """Toggle selection between the main object and its FADER object."""
        bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects

        # Check if the FADER object is in the current View Layer
        if fader_obj and fader_obj.name in context.view_layer.objects:
            # Toggle between object and FADER object
            if active_obj == obj:
                fader_obj.select_set(True)
                context.view_layer.objects.active = fader_obj
            elif active_obj == fader_obj:
                obj.select_set(True)
                context.view_layer.objects.active = obj
            else:
                obj.select_set(True)
                context.view_layer.objects.active = obj
        else:
            # If the FADER object is not in the View Layer, select the main object
            print_render_pass_debug(f"Warning: FADER object '{fader_obj.name if fader_obj else 'None'}' is not in the current View Layer.")
            obj.select_set(True)
            context.view_layer.objects.active = obj

    def clean_fader_dict(self, obj_name, cprops):
        """Remove invalid FADER entries from the FADER dictionary."""
        for entry in cprops.render_passes_faderobjects_DICT:
            if entry.obj_name == obj_name and (not entry.node_object or entry.node_object.name not in bpy.data.objects):
                print_render_pass_debug(f"Warning: FADER object for '{obj_name}' is missing and will be removed.")
                cprops.render_passes_faderobjects_DICT.remove(cprops.render_passes_faderobjects_DICT.find(entry.obj_name))
                break

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        # Ensure index is within valid range
        if 0 <= self.index < len(cprops.render_passes_objectlist):
            item = cprops.render_passes_objectlist[self.index]
            obj = bpy.data.objects.get(item.name)

            if obj:
                # Refresh Object List
                bpy.ops.flip_fluid_operators.refresh_objectlist()

                # Get the active object
                active_obj = context.view_layer.objects.active

                # Find the corresponding FADER object
                fader_obj = next(
                    (entry.node_object for entry in cprops.render_passes_faderobjects_DICT if entry.obj_name == obj.name),
                    None
                )

                # Handle missing FADER object
                if fader_obj and fader_obj.name not in bpy.data.objects:
                    self.clean_fader_dict(obj.name, cprops)
                    fader_obj = None  # Reset FADER object to None

                # Toggle selection between main object and FADER object
                self.toggle_selection(obj, fader_obj, active_obj, context)

                # Update the active index for the UIList
                cprops.render_passes_objectlist_index = self.index

        return {'FINISHED'}


class FlipFluidPassesRefreshObjectList(bpy.types.Operator):
    """Refreshes the render_passes_objectlist based on the current scene objects"""
    bl_idname = "flip_fluid_operators.refresh_objectlist"
    bl_label = "Refresh Object List"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        object_list = cprops.render_passes_objectlist
        fader_dict = cprops.render_passes_faderobjects_DICT

        # ------------------------
        # STEP 1: Sync object names in object_list
        # ------------------------
        for i in reversed(range(len(object_list))):
            item = object_list[i]
            obj = bpy.data.objects.get(item.name)

            # Falls das Objekt nicht existiert, versuche es per data_name zu finden
            if obj is None:
                for obj_in_scene in bpy.data.objects:
                    if obj_in_scene.data and obj_in_scene.data.name == item.data_name:
                        item.name = obj_in_scene.name
                        obj = obj_in_scene
                        break

            # Objekt noch immer nicht vorhanden oder ohne Collection => Eintrag entfernen
            if obj is None or len(obj.users_collection) == 0:
                object_list.remove(i)
                continue

            # Name anpassen, falls sich das Data-Name ge?dert hat
            if obj.data and obj.data.name == item.data_name and obj.name != item.name:
                item.name = obj.name

        # ------------------------
        # STEP 2: Sync FADER objects for each item
        # ------------------------
        for item in object_list:
            obj = bpy.data.objects.get(item.name)
            if not obj:
                continue

            fader_object = None
            for child in obj.children:
                if child.name.startswith("FADER."):
                    fader_object = child
                    break

            # If no FADER in children, but in Dictionary => Get it
            fader_entry = next((entry for entry in fader_dict if entry.obj_name == item.name), None)
            if not fader_object and fader_entry and fader_entry.node_object:
                fader_object = fader_entry.node_object

            # Check if FADER-Object is in der View Layer
            if fader_object:
                if fader_object.name not in context.view_layer.objects:
                    # FADER-Objekt zur?ck in die Scene Collection linken
                    print_render_pass_debug(f"Restoring FADER object '{fader_object.name}' to the scene.")
                    context.scene.collection.objects.link(fader_object)
                    fader_object.parent = obj
                    fader_object.matrix_parent_inverse = obj.matrix_world.inverted()
                    fader_object.rotation_euler = (1.5708, 0, 0)

                # Expected name
                expected_fader_name = f"FADER.{obj.name}_@"
                if fader_object.name != expected_fader_name:
                    fader_object.name = expected_fader_name

                # Fader DICT 
                if fader_entry:
                    fader_entry.node_object = fader_object
                    fader_entry.obj_name = obj.name
                    fader_entry.material_name = (
                        fader_object.active_material.name
                        if fader_object.active_material else "Unknown"
                    )
                else:
                    new_entry = fader_dict.add()
                    new_entry.obj_name = obj.name
                    new_entry.node_object = fader_object
                    new_entry.material_name = (
                        fader_object.active_material.name
                        if fader_object.active_material else "Unknown"
                    )

        # ------------------------
        # STEP 3: Re-add items based on data_name if applicable
        # ------------------------
        for item in object_list:
            obj = bpy.data.objects.get(item.name)
            if not obj:
                continue

            if obj.data and obj.data.name == item.data_name and obj.name != item.name:
                item.name = obj.name

        # Refresh unflagged objects
        update_unflagged_objects_property(context)

        return {'FINISHED'}


# Runs every time the scene changes or when new material is loaded
def update_camera_screen_scale(bl_camera_screen, bl_camera, image_aspect_ratio, maintain_aspect=True):
    # Update object list to remove deleted objects
    # update_object_list(bpy.context.scene)
    
    # Retrieve the depth value for placing the screen
    depth = bpy.context.scene.flip_fluid_compositing_tools.render_passes_camerascreen_distance
    camera_angle = bl_camera.data.angle
    camera_type = bl_camera.data.type
    camera_ortho_scale = bl_camera.data.ortho_scale

    # Initialize x and y scale
    x_scale = y_scale = 1.0

    # Adjust sensor_fit based on aspect ratio
    if image_aspect_ratio < 1.0:
        bl_camera.data.sensor_fit = 'VERTICAL'
    else:
        bl_camera.data.sensor_fit = 'HORIZONTAL'

    # Calculate screen size based on camera type
    if camera_type == 'PERSP' or camera_type == 'PANO':
        x_scale = y_scale = depth * math.tan(0.5 * camera_angle)
    elif camera_type == 'ORTHO':
        x_scale = y_scale = 0.5 * camera_ortho_scale

    # Maintain the aspect ratio of the image
    if maintain_aspect:
        if image_aspect_ratio < 1.0:
            x_scale *= image_aspect_ratio
        else:
            y_scale /= image_aspect_ratio

    # Set the location and scale of the camera screen
    bl_camera_screen.location = (0.0, 0.0, -depth)
    bl_camera_screen.scale = (abs(x_scale), abs(y_scale), 1.0)

def get_image_aspect_ratio(image_filepath):
    image = bpy.data.images.load(image_filepath)
    if image.size[0] != 0 and image.size[1] != 0:
        return image.size[0] / image.size[1]
    return 1.0  # Fallback to square if dimensions are invalid


class FlipFluidPassesAddCameraScreen(bpy.types.Operator, ImportHelper):
    """Add a Camera Screen plane linked to the selected camera with an image or video texture"""
    bl_idname = "flip_fluid_operators.add_camera_screen"
    bl_label = "Add CameraScreen"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
        default='*.png;*.jpg;*.jpeg;*.jp2;*.tif;*.exr;*.hdr;*.bmp;*.rgb;*.tga;*.cin;*.dpx;*.webp;*.avif',
        options={'HIDDEN'}
    )

    directory: StringProperty()
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    def check_and_report_operator_context_errors(self, context):
        valid_file_types = ('.png', '.jpg', '.jpeg', '.jp2', '.tif', '.exr', '.hdr', '.bmp', '.rgb', '.tga', '.cin', '.dpx', '.webp', '.avif')
        for file in self.files:
            if not file.name.lower().endswith(valid_file_types):
                filepath = os.path.join(self.directory, file.name)
                valid_types_string = " ".join(valid_file_types)
                errmsg = "Invalid file type selected: <" + filepath + ">."
                errmsg += " Supported file types: " + valid_types_string
                self.report({'ERROR'}, errmsg)
                return {'CANCELLED'}

        cprops = context.scene.flip_fluid_compositing_tools
        bl_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        if bl_camera is None:
            show_message_box(message=f"Camera object <{str(cprops.render_passes_cameraselection)}> not found", title="Error", icon='OUTLINER_OB_CAMERA')
            return {'CANCELLED'}

    def initialize_camera_screen_object(self, context, image_aspect_ratio):
        cprops = context.scene.flip_fluid_compositing_tools

        # Create and size camera screen plane
        bl_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        bpy.ops.mesh.primitive_plane_add()
        bl_camera_screen = context.active_object
        bl_camera_screen.name = "ff_camera_screen"
        bl_camera_screen.lock_location = (True, True, True)
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)

        depth = cprops.render_passes_camerascreen_distance
        bl_camera_screen.location = (0, 0, -depth)
        bl_camera_screen.parent = bl_camera

        update_camera_screen_scale(bl_camera_screen, bl_camera, image_aspect_ratio, maintain_aspect=True)

        return bl_camera_screen

    def initialize_image_texture_material(self, bl_camera_screen, image_filepaths):
        # Check if the material already exists and remove it
        mat_name = "ff_camera_screen"
        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])

        # Initialize material and nodes
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()  # Clear existing nodes

        # Create Material Output Node
        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (400, 0)

        # Create Emission Shader Node
        emission = nodes.new(type="ShaderNodeEmission")
        emission.location = (0, -100)

        # Create Transparent Shader Node
        transparent = nodes.new(type="ShaderNodeBsdfTransparent")
        transparent.location = (0, 100)

        # Create Mix Shader Node
        mix_shader = nodes.new(type="ShaderNodeMixShader")
        mix_shader.location = (200, 0)

        # Create Color Ramp Node
        color_ramp = nodes.new(type="ShaderNodeValToRGB")
        color_ramp.location = (-400, 100)
        color_ramp.color_ramp.interpolation = 'EASE'
        if len(color_ramp.color_ramp.elements) > 1:
            color_ramp.color_ramp.elements[1].position = 0.5

        # Create Gradient Texture Node
        gradient_texture = nodes.new(type="ShaderNodeTexGradient")
        gradient_texture.location = (-600, 100)
        gradient_texture.gradient_type = 'SPHERICAL'

        # Create Texture Coordinate Node and set name and label
        texture_coord = nodes.new(type="ShaderNodeTexCoord")
        texture_coord.location = (-800, 100)
        texture_coord.name = "ff_compositing_camerascreen_fadercoordinate"
        texture_coord.label = "ff_compositing_camerascreen_fadercoordinate"

        # Create Image Texture Node
        texture = nodes.new(type="ShaderNodeTexImage")
        texture.location = (-200, -100)
        texture.name = "ff_camera_screen"
        texture.label = "ff_camera_screen"
        texture.extension = 'EXTEND'

        # Link the nodes
        links = mat.node_tree.links
        links.new(output.inputs['Surface'], mix_shader.outputs[0])  # Connect Mix Shader to Material Output
        links.new(mix_shader.inputs[1], transparent.outputs[0])  # Transparent Shader to Mix Shader (Shader Input 1)
        links.new(mix_shader.inputs[2], emission.outputs[0])  # Emission Shader to Mix Shader (Shader Input 2)
        links.new(emission.inputs['Color'], texture.outputs['Color'])  # Texture Color to Emission Color

        # Connect Color Ramp to Mix Shader Fac
        links.new(mix_shader.inputs['Fac'], color_ramp.outputs['Color'])  # Color Ramp Color to Mix Shader Fac

        # Connect Gradient Texture to Color Ramp Fac
        links.new(color_ramp.inputs['Fac'], gradient_texture.outputs['Fac'])  # Gradient Texture to Color Ramp Fac

        # Connect Texture Coordinate to Gradient Texture
        links.new(gradient_texture.inputs['Vector'], texture_coord.outputs['Object'])  # Texture Coordinate to Gradient Texture Vector

        # Set the material on the screen object
        bl_camera_screen = bpy.context.active_object  # Assuming this is your camera screen object
        bl_camera_screen.data.materials.clear()
        bl_camera_screen.data.materials.append(mat)

        # Save the initial cursor location
        initial_cursor_location = bpy.context.scene.cursor.location.copy()

        # Set the cursor to the location of ff_camera_screen
        bl_camera_screen = bpy.context.active_object
        bl_camera_screen.name = "ff_camera_screen"
        #bpy.context.scene.cursor.location = bl_camera_screen.matrix_world.translation  # Use the world position of ff_camera_screen
        fader_location = bl_camera_screen.location
        bpy.ops.object.empty_add(type='CIRCLE', location=fader_location)

        # Create an Empty in circle form at the cursor location with no rotation
        bpy.ops.object.empty_add(type='CIRCLE', location=bpy.context.scene.cursor.location)
        fader_empty = bpy.context.active_object
        fader_empty.name = "FADER.ff_camera_screen_@"

        # Match the rotation of the Empty to ff_camera_screen
        fader_empty.rotation_euler[0] -= 1.5708 

        # Parent the Empty to the ff_camera_screen object
        fader_empty.parent = bl_camera_screen

        # Set the Empty in the Texture Coordinate Node's object field
        texture_coord = bl_camera_screen.active_material.node_tree.nodes.get("ff_compositing_camerascreen_fadercoordinate")
        texture_coord.object = fader_empty
        
        # Set the Empty to show its name in the viewport
        fader_empty.show_name = False

        # Restore the initial cursor location
        bpy.context.scene.cursor.location = initial_cursor_location

        def get_trailing_number_from_string(s):
            m = re.search(r'(\d+)$', s)
            return int(m.group()) if m else None

        # Find first frame number in image sequence if it exists
        is_frame_sequence_found = False
        frame_start = 2**32
        frame_start_filepath = None

        for filepath in image_filepaths:
            basename = pathlib.Path(filepath).stem
            frame_number = get_trailing_number_from_string(basename)
            if frame_number is not None and frame_number < frame_start:
                is_frame_sequence_found = True
                frame_start = frame_number
                frame_start_filepath = filepath

        image_type = None
        if len(image_filepaths) == 1:
            image_type = 'FILE'
        else:
            base_names = [pathlib.Path(filepath).stem for filepath in image_filepaths]
            trailing_numbers = [get_trailing_number_from_string(name) for name in base_names]
            
            if all(num is not None for num in trailing_numbers):
                sorted_numbers = sorted(trailing_numbers)
                is_sequential = all(
                    sorted_numbers[i] + 1 == sorted_numbers[i + 1]
                    for i in range(len(sorted_numbers) - 1)
                )
                if is_sequential:
                    image_type = 'SEQUENCE'
                else:
                    image_type = 'FILE'
            else:
                image_type = 'FILE'

        # Load or reuse existing images as image datablocks
        frame_start_image = None
        for filepath in image_filepaths:
            image_name = pathlib.Path(filepath).name
            # Check if the image is already loaded in Blender
            image = bpy.data.images.get(image_name)
            if image is None:
                # Load the image or movie if not already in memory
                image = bpy.data.images.load(filepath)
            if frame_start_image is None:
                frame_start_image = image
            if filepath == frame_start_filepath:
                frame_start_image = image

        # Set texture node based on image type
        if len(image_filepaths) == 1:
            texture.image = frame_start_image
            texture.image.source = 'FILE'
        elif image_type == 'SEQUENCE' and is_frame_sequence_found:
            texture.image = frame_start_image
            texture.image.source = 'SEQUENCE'
            texture.image_user.frame_duration = len(image_filepaths)
            texture.image_user.frame_start = frame_start
            texture.image_user.frame_offset = frame_start - 1
            texture.image_user.use_cyclic = True
            texture.image_user.use_auto_refresh = True
        elif image_type == 'MOVIE':
            texture.image = frame_start_image
            texture.image.source = 'MOVIE'
        return texture.image

    def set_camera_background_image(self, context, image_filepaths, frame_start, frame_duration, frame_offset):
        cprops = context.scene.flip_fluid_compositing_tools
        bl_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        
        if not bl_camera:
            print_render_pass_debug("Camera not found!")
            return
        
        # Check if a background image already exists
        if bl_camera.data.background_images:
            # Update the existing background image instead of adding a new one
            bg = bl_camera.data.background_images[0]  # Use the first available background image
        else:
            # Add a new background image if none exists
            bg = bl_camera.data.background_images.new()

        # Determine the image type
        if len(image_filepaths) == 1:
            image_type = 'FILE'
        else:
            image_type = 'SEQUENCE'

        # Set image and frame settings
        bg.image = bpy.data.images.get(pathlib.Path(image_filepaths[0]).name)
        if bg.image is not None:
            if image_type == 'FILE':
                bg.image.source = 'FILE'
            elif image_type == 'SEQUENCE':
                bg.image.source = 'SEQUENCE'
                bg.image_user.frame_duration = frame_duration
                bg.image_user.frame_start = frame_start
                bg.image_user.frame_offset = frame_offset
                bg.image_user.use_cyclic = True
                bg.image_user.use_auto_refresh = True

        bpy.context.view_layer.update()

    def invoke(self, context, event):
        self.filepath = ""  # Clear the filepath field
        cprops = context.scene.flip_fluid_compositing_tools

        # Check if 'ff_camera_screen' exists
        ff_camera_screen = bpy.data.objects.get("ff_camera_screen")
        if ff_camera_screen:
            # Check if the selected object is in the object list and has a valid flag
            selected_obj = context.view_layer.objects.active
            object_list = cprops.render_passes_objectlist  # List of all objects

            # Find the corresponding object in the list
            obj_entry = next((item for item in object_list if item.name == selected_obj.name), None)

            # Check if the object exists and is not marked as Ground
            if obj_entry and (obj_entry.fg_elements or obj_entry.bg_elements or obj_entry.ref_elements):
                # Function to get the world transform of an object
                def get_world_transform(obj):
                    if not obj:
                        return None, None, None
                    world_matrix = obj.matrix_world
                    position = world_matrix.to_translation()
                    rotation = world_matrix.to_euler()
                    scale = world_matrix.to_scale()
                    return position, rotation, scale

                # Retrieve the transformation of 'ff_camera_screen'
                position, rotation, scale = get_world_transform(ff_camera_screen)

                if position and rotation and scale:
                    # Apply the transformation to the selected object
                    selected_obj.location = position
                    selected_obj.rotation_euler = rotation
                    selected_obj.scale = scale
                    self.report({'INFO'}, f"Adjusted object '{selected_obj.name}' to match ff_camera_screen.")
                    return {'FINISHED'}
                else:
                    print_render_pass_debug("Failed to retrieve world transformation of ff_camera_screen.")
                    self.report({'ERROR'}, "Failed to retrieve transformation of ff_camera_screen.")
                    return {'CANCELLED'}

        # If 'ff_camera_screen' exists but no valid object was selected
        if ff_camera_screen:
            show_message_box(message="An object named 'ff_camera_screen' already exists. No new object created.", title="Warning", icon='IMAGE_BACKGROUND')
            return {'CANCELLED'}

        # If no Camera Screen exists, proceed with file selection
        return context.window_manager.fileselect_add(self) or {'RUNNING_MODAL'}


    def execute_with_existing_images(self, context, image_filepaths):
        cprops = context.scene.flip_fluid_compositing_tools
        bl_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        
        # Check if the camera has background images
        if bl_camera and bl_camera.data.background_images:
            bg_image = bl_camera.data.background_images[0]

            # Extract frame values from the existing background image
            frame_start = bg_image.image_user.frame_start
            frame_duration = bg_image.image_user.frame_duration
            frame_offset = bg_image.image_user.frame_offset

            # Use the same image paths as the background image
            image_filepaths = [bg_image.image.filepath]

            # Calculate the aspect ratio based on the render settings if updated by the user
            render = context.scene.render
            if render.resolution_x > 0 and render.resolution_y > 0:
                image_aspect_ratio = render.resolution_x / render.resolution_y
            else:
                # Fallback to aspect ratio of the background image if render settings are not valid
                image_aspect_ratio = bg_image.image.size[0] / bg_image.image.size[1] if bg_image.image.size[1] != 0 else 1.0

            # Initialize the ff_camera_screen object with the calculated aspect ratio
            bl_camera_screen = self.initialize_camera_screen_object(context, image_aspect_ratio)

            # Update the camera screen scale to ensure it fits the aspect ratio
            update_camera_screen_scale(bl_camera_screen, bl_camera, image_aspect_ratio, maintain_aspect=True)
            
            # Set the texture of the ff_camera_screen material with the same settings
            image = self.initialize_image_texture_material(bl_camera_screen, image_filepaths)
            
            # Set the texture to the same image sequence and frame values
            texture = bl_camera_screen.active_material.node_tree.nodes['ff_camera_screen']
            texture.image_user.frame_start = frame_start
            texture.image_user.frame_duration = frame_duration
            texture.image_user.frame_offset = frame_offset
            texture.image_user.use_cyclic = bg_image.image_user.use_cyclic
            texture.image_user.use_auto_refresh = bg_image.image_user.use_auto_refresh
        else:
            # If no background images are present, use a default aspect ratio or handle normally
            image_aspect_ratio = 1.0  # Default aspect ratio if no background image is present
            bl_camera_screen = self.initialize_camera_screen_object(context, image_aspect_ratio)
            image = self.initialize_image_texture_material(bl_camera_screen, image_filepaths)

        return {'FINISHED'}

    def execute(self, context):
        if any(obj.name == "ff_camera_screen" for obj in bpy.data.objects):
            show_message_box(message="An object named 'ff_camera_screen' already exists. No new object created.", title="Warning", icon='IMAGE_BACKGROUND')
            #self.report({'WARNING'}, "An object named 'ff_camera_screen' already exists. No new object created.")
            return {'CANCELLED'}

        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        image_filepaths = [os.path.join(self.directory, f.name) for f in self.files]
        
        # Get aspect ratio from the first image file
        image_aspect_ratio = get_image_aspect_ratio(image_filepaths[0]) if image_filepaths else 1.0

        # Update Blender render settings based on the image resolution
        image = bpy.data.images.load(image_filepaths[0])
        render = context.scene.render
        render.resolution_x = image.size[0]
        render.resolution_y = image.size[1]

        bl_camera_screen = self.initialize_camera_screen_object(context, image_aspect_ratio)
        image = self.initialize_image_texture_material(bl_camera_screen, image_filepaths)
        
        # Get frame data from "ff_camera_screen"
        frame_start = bl_camera_screen.active_material.node_tree.nodes['ff_camera_screen'].image_user.frame_start
        frame_duration = bl_camera_screen.active_material.node_tree.nodes['ff_camera_screen'].image_user.frame_duration
        frame_offset = bl_camera_screen.active_material.node_tree.nodes['ff_camera_screen'].image_user.frame_offset

        # Update the scene's frame range to match the Footage
        scene = context.scene
        scene.frame_start = frame_start
        scene.frame_end = frame_start + frame_duration - 1
        scene.frame_current = frame_start  # Optional: Set the current frame to the start frame
        
        # Transfer frame_offset parameters
        self.set_camera_background_image(context, image_filepaths, frame_start, frame_duration, frame_offset)
        return {'FINISHED'}


# Helper function to load media files
def add_imported_media_to_collection(cprops, file_name):
    """Adds the file to the collection and ensures texture assignment."""
    
    # Check if the file is already in the collection
    for item in cprops.render_passes_import_media:
        if item.file_name == file_name:
            return item  # Return existing entry

    # Add new file to the collection
    new_item = cprops.render_passes_import_media.add()
    new_item.file_name = file_name

    # Generate texture and object names based on the file name
    base_name = os.path.splitext(file_name)[0]
    new_item.texture_name = file_name  # 🔹 Speichere den echten Dateinamen!
    new_item.object_name = base_name

    # Ensure the fade_node default_value is set to 1.0 for MediaProperty objects
    obj = bpy.data.objects.get(base_name)
    if obj and obj.active_material and obj.active_material.node_tree:
        fade_node = obj.active_material.node_tree.nodes.get("ff_elements_fading")
        if fade_node:
            fade_node.inputs[0].default_value = 1.0  # Set to default disabled state

    return True

def update_texture_in_node(obj_name, texture_name, file_name, directory):
    """Update the texture node for the given object with the provided texture."""

    # Ensure the image file is loaded into Blender
    image_path = os.path.join(directory, file_name)
    if file_name not in bpy.data.images:
        try:
            bpy.data.images.load(image_path)
        except Exception as e:
            print_render_pass_debug(f"Failed to load image '{image_path}': {e}")
            return

    image = bpy.data.images.get(file_name)
    if not image:
        print_render_pass_debug(f"Image '{file_name}' could not be found in Blender after loading.")
        return

    # Get the object and its material
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.data.materials:
        print_render_pass_debug(f"Object '{obj_name}' does not have a material.")
        return

    material = obj.data.materials[0]

    # Ensure the material has a node tree
    if not material.use_nodes:
        print_render_pass_debug(f"Material on '{obj_name}' does not use nodes.")
        return

    node_tree = material.node_tree
    texture_node = node_tree.nodes.get("ff_camera_screen")

    if not texture_node:
        print_render_pass_debug(f"Node 'ff_camera_screen' not found in material for '{obj_name}'.")
        return

    # Is the object in the imported media list?
    cprops = context.scene.flip_fluid_compositing_tools
    media_item = next((item for item in cprops.render_passes_import_media if item.object_name == obj_name), None)

    if media_item:
        # Use the texture name stored in the media property
        #texture_name = media_item.texture_name
        image = bpy.data.images.get(file_name)

        if not image:
            print_render_pass_debug(f"Skipping texture update for '{obj_name}' because its texture '{texture_name}' could not be found.")
            return

    # Assign the image to the texture node
    texture_node.image = image
    print_render_pass_debug(f"Updated texture for '{obj_name}' with image '{image.name}'.")


class FlipFluidPassesImportMedia(bpy.types.Operator):
    """Operator to import images or videos and store them in a CollectionProperty"""
    bl_idname = "flip_fluid.passes_import_media"
    bl_label = "Import Media"

    option_path_supports_blend_relative = {'PATH_SUPPORTS_BLEND_RELATIVE'}

    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.tif;*.mp4;*.avi;*.mov;*.avif",
        options={'HIDDEN'}
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    directory: StringProperty(subtype='DIR_PATH', options=option_path_supports_blend_relative)

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        any_files_processed = False
        created_objects = []  # Track created objects

        for file in self.files:
            file_name = file.name
            base_name = os.path.splitext(file_name)[0]
            texture_name = f"ff_{base_name.lower()}_element"

            # Add to property collection and save filename
            if add_imported_media_to_collection(cprops, file_name):
                media_item = next((item for item in cprops.render_passes_import_media if item.object_name == base_name), None)
                if media_item:
                    media_item.texture_name = texture_name  # 🔹 Richtig abspeichern!

                # Call the Quick FG Catcher Operator
                bpy.ops.flip_fluid_operators.quick_foregroundcatcher(
                    obj_name=base_name,
                    texture_name=texture_name
                )

                created_objects.append((base_name, texture_name, file_name))
                any_files_processed = True

        # Update textures in nodes for all created objects
        for obj_name, texture_name, file_name in created_objects:
            update_texture_in_node(obj_name, texture_name, file_name, self.directory)

        if not any_files_processed:
            print_render_pass_debug("No new files were processed. All selected files were already imported.")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class FlipFluidToggleCameraScreenVisibility(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_camerascreen_visibility"
    bl_label = "Toggle CameraScreen Visibility"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        ff_camera_screen = bpy.data.objects.get("ff_camera_screen")
        if ff_camera_screen:
            ff_camera_screen.hide_viewport = not cprops.render_passes_camerascreen_visibility
        return {'FINISHED'}


class FlipFluidPassesToggleStillImageMode(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_still_image_mode"
    bl_label = "Toggle Still Image Mode"
    bl_description = "Perform actions when toggling Still Image Mode"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        if cprops.render_passes_stillimagemode_toggle:
            # Enable Still Image Mode
            self.enable_still_image_mode(context, cprops)
            self.report({'INFO'}, "Still Image Mode Enabled")
        else:
            # Disable Still Image Mode
            self.disable_still_image_mode(context, cprops)
            self.report({'INFO'}, "Still Image Mode Disabled")

        return {'FINISHED'}

    def enable_still_image_mode(self, context, cprops):
        # Step 1: Get the currently selected camera
        original_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        if not original_camera or original_camera.type != 'CAMERA':
            self.report({'ERROR'}, "Selected camera not found or invalid")
            return

        # Step 2: Check if a projector camera already exists
        projector_camera_name = "ff_stills_projector"
        projector_camera = bpy.data.objects.get(projector_camera_name)

        if not projector_camera:
            # Create a duplicate of the original camera
            projector_camera = original_camera.copy()
            projector_camera.data = original_camera.data.copy()
            projector_camera.name = projector_camera_name
            context.scene.collection.objects.link(projector_camera)

        # Make the projector camera visible for the viewport
        projector_camera.hide_viewport = False
        projector_camera.hide_render = False

        # Update camera selection to use the projector camera
        cprops.render_passes_cameraselection = projector_camera.name

        # Step 3: Hide ff_camera_screen and its parent object for viewport and rendering
        screen_object = bpy.data.objects.get("ff_camera_screen")
        if screen_object:
            self.set_visibility(screen_object, visible=True)

        # Step 4: Execute the compositing textures operator
        bpy.ops.flip_fluid_operators.helper_fix_compositingtextures()

        # Step 5: Ensure the original camera remains selected
        bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
        original_camera.select_set(True)  # Select the original camera
        context.view_layer.objects.active = original_camera  # Set it as active

    def disable_still_image_mode(self, context, cprops):
        # Step 1: Get the projector camera
        projector_camera = bpy.data.objects.get("ff_stills_projector")
        if not projector_camera:
            self.report({'ERROR'}, "Projector camera not found")
            return

        # Make the projector camera invisible for the viewport
        projector_camera.hide_viewport = True
        projector_camera.hide_render = True

        # Restore the original camera in the selection (unchanged behavior)
        original_camera = self.find_original_camera(projector_camera)
        if original_camera:
            cprops.render_passes_cameraselection = original_camera.name

        # Step 2: Unhide ff_camera_screen and its parent object for viewport and rendering
        screen_object = bpy.data.objects.get("ff_camera_screen")
        if screen_object:
            self.set_visibility(screen_object, visible=True)

        # Step 3: Execute the compositing textures operator
        bpy.ops.flip_fluid_operators.helper_fix_compositingtextures()

    def set_visibility(self, obj, visible):
        """Set the visibility of an object and its children for viewport and rendering."""
        obj.hide_viewport = not visible
        obj.hide_render = not visible
        # Set visibility for parented objects
        for child in obj.children:
            child.hide_viewport = not visible
            child.hide_render = not visible

    def find_original_camera(self, projector_camera):
        # Find the original camera (assuming it's not the projector camera)
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA' and obj != projector_camera:
                return obj
        return None


class FlipFluidAlignAndParentOperator(bpy.types.Operator):
    """Aligns and parents FADER objects to their respective parent objects, and updates the FADER and MATERIAL names if the parent object is renamed."""
    bl_idname = "flip_fluid_operators.align_and_parent"
    bl_label = "Align and Parent FADER Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Access the centralized fader_dict from the helper properties
        cprops = context.scene.flip_fluid_compositing_tools
        fader_dict = cprops.render_passes_faderobjects_DICT

        # List of objects to ignore
        ignore_list = [
            "whitewater_spray", "whitewater_foam", "whitewater_dust", 
            "whitewater_bubble", "fluid_particles"
        ]

        updated_fader_objects = {}  # New dictionary to store updated FADER names
        updated_material_names = {}  # New dictionary to store updated MATERIAL names

        # Loop over the entries in the fader_dict
        for idx, entry in enumerate(fader_dict):

            # Retrieve FADER, parent object, and material
            fader_obj = entry.node_object
            projection_fader_obj = entry.projectionnode_object
            parent_obj = bpy.data.objects.get(entry.obj_name)
            material = bpy.data.materials.get(entry.material_name)

            # Check existence of FADER object
            if not fader_obj:
                self.report({'WARNING'}, "FADER object not found. Skipping entry.")
                continue

            # Check existence of parent object
            if not parent_obj:
                self.report({'WARNING'}, f"Parent object '{entry.obj_name}' not found. Skipping entry.")
                continue

            # Check existence of material
            if not material:
                self.report({'WARNING'}, f"Material '{entry.material_name}' not found. Skipping entry.")
                continue

            # Ignore specific objects except fluid_surface
            if parent_obj.name in ignore_list:
                continue

            # Get the expected names based on the current parent name
            expected_fader_name = f"FADER.{parent_obj.name}_@"
            expected_material_name = f"FF Elements_Passes_{parent_obj.name}_@"

            # Update FADER object name if needed
            if "_@" in fader_obj.name:
                if fader_obj.name != expected_fader_name:
                    fader_obj.name = expected_fader_name
            else:
                # Align FADER object to the parent object's world matrix
                fader_obj.matrix_world = parent_obj.matrix_world
                fader_obj.parent = parent_obj
                fader_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()
                fader_obj.name = expected_fader_name

            # Skip renaming if it's the fluid_surface material
            if parent_obj.name != "fluid_surface":
                # Update Material name if it exists and needs renaming
                if "_@" in material.name:
                    if material.name != expected_material_name:
                        material.name = expected_material_name
                else:
                    material.name = expected_material_name

            # Update the dictionaries with the new FADER and MATERIAL names
            updated_fader_objects[expected_fader_name] = {
                'material': material.name if material else None,
                'node_object': fader_obj
            }
            updated_material_names[expected_material_name] = {
                'material': material.name if material else None,
                'node_object': fader_obj
            }

        # Clear the existing fader_dict and update it with the new FADER names
        fader_dict.clear()
        for new_fader_name, data in updated_fader_objects.items():
            new_entry = fader_dict.add()
            
            # Ensure node_object and parent are valid
            if not data['node_object']:
                self.report({'WARNING'}, f"Node object for '{new_fader_name}' is None. Skipping entry.")
                continue
            
            parent_name = data['node_object'].parent.name if data['node_object'].parent else "No Parent"
            if parent_name == "No Parent":
                self.report({'WARNING'}, f"Parent is missing for '{new_fader_name}'. Assigning default value.")
            
            new_entry.obj_name = parent_name  # Set parent name or fallback
            new_entry.material_name = data['material'] if data['material'] else "No Material"
            new_entry.node_object = data['node_object']
            
        # Ensure the scene is updated
        bpy.context.view_layer.update()

        #self.report({'INFO'}, "FADER objects and materials have been aligned, parented, renamed (if needed), and the dictionary updated.")
        return {'FINISHED'}

       
# Will be renamed to something like refresh - runs align&parent operator
class FlipFluidPassesFixCompositingTextures(bpy.types.Operator):
    """Fixes all ff_camera_screen textures to match your background, updates compositing texture coordinates, and assigns FADER object to relevant nodes."""
    bl_idname = "flip_fluid_operators.helper_fix_compositingtextures"
    bl_label = "Fix Compositing Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure the 'ff_camera_screen' object and material exist
        screen_obj = bpy.data.objects.get("ff_camera_screen")
        screen_material = bpy.data.materials.get("ff_camera_screen")
        if not screen_obj or not screen_material:
            # If either the object or material is missing, we don't want to cause a Python error.
            self.report({'WARNING'}, "Object or Material 'ff_camera_screen' not found. Skipping Operator.")
            return {'CANCELLED'}

        if not screen_material.use_nodes:
            self.report({'WARNING'}, "Material 'ff_camera_screen' does not use nodes. Skipping Operator.")
            return {'CANCELLED'}

        # Validate if the texture node exists
        screen_texture_node = next((node for node in screen_material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.name == "ff_camera_screen"), None)
        if not screen_texture_node or not screen_texture_node.image:
            self.report({'ERROR'}, "No valid ff_camera_screen texture node found in the material 'ff_camera_screen'.")
            return {'CANCELLED'}

        # Adjust texture parameters
        screen_texture_node.image_user.use_auto_refresh = True

        # Check if Motion Tracking area is available and set the tracking clip
        for area in context.screen.areas:
            if area.type == 'CLIP_EDITOR':
                clip_editor = area.spaces.active

                # Get the 'ff_camera_screen' node from the material
                texture_node = screen_material.node_tree.nodes.get("ff_camera_screen")
                if not texture_node or not texture_node.image:
                    self.report({'ERROR'}, "ff_camera_screen texture node not found or invalid.")
                    return {'CANCELLED'}

                # Retrieve image data and Image User properties
                image = texture_node.image
                image_user = texture_node.image_user

                # Get directory and all files of the sequence
                directory = bpy.path.abspath(os.path.dirname(image.filepath))
                base_name, ext = os.path.splitext(os.path.basename(image.filepath))

                # Extract the numerical part of the base name
                import re
                match = re.search(r'_(\d+)$', base_name)
                if not match:
                    self.report({'ERROR'}, f"Invalid file naming convention: {base_name}{ext}")
                    return {'CANCELLED'}

                # Get the numerical part and its length
                number_str = match.group(1)
                number_length = len(number_str)

                # Generate a list of files based on the sequence
                files = []
                for i in range(image_user.frame_duration):
                    frame_number = image_user.frame_start + i
                    filename = f"{base_name[:match.start(1)]}{frame_number:0{number_length}d}{ext}"
                    files.append({"name": filename})

                # Load the sequence using the Clip Open operator
                try:
                    bpy.ops.clip.open(
                        directory=directory,
                        files=files,
                        relative_path=False
                    )
                except RuntimeError as e:
                    self.report({'ERROR'}, f"Failed to load sequence: {e}")
                    return {'CANCELLED'}

                # Update the scene with the loaded clip
                movie_clip = bpy.data.movieclips[-1]
                movie_clip.name = "ff_camera_screen_clip"
                clip_editor.clip = movie_clip
                movie_clip.frame_start = bpy.context.scene.frame_start

                # Update the viewport
                bpy.context.view_layer.update()
                self.report({'INFO'}, "Tracking sequence loaded and applied to Motion Tracking Clip Editor.")

        # Assign the texture to relevant nodes in all objects
        for obj in bpy.data.objects:
            if obj.name == "ff_camera_screen":  # Skip the ff_camera_screen object
                continue

            # Skip objects in the list of imported files (Import to Elements)
            cprops = context.scene.flip_fluid_compositing_tools
            if any(media_item.object_name == obj.name for media_item in cprops.render_passes_import_media):
                continue

            for material_slot in obj.material_slots:
                material = material_slot.material
                if not material or not material.use_nodes:
                    continue

                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.name == "ff_camera_screen":
                        node.image = screen_texture_node.image
                        node.extension = 'EXTEND'
                        if node.image_user:
                            node.image_user.frame_start = screen_texture_node.image_user.frame_start
                            node.image_user.frame_duration = screen_texture_node.image_user.frame_duration
                            node.image_user.frame_offset = screen_texture_node.image_user.frame_offset
                            node.image_user.use_cyclic = screen_texture_node.image_user.use_cyclic
                            node.image_user.use_auto_refresh = True

        # Validate the camera specified in the Helper Panel properties
        cprops = context.scene.flip_fluid_compositing_tools
        bl_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        if not bl_camera or bl_camera.type != 'CAMERA':
            show_message_box(message="Camera specified in flip_fluid_compositing_tools not found or is not a camera.", title="Error", icon='OUTLINER_OB_CAMERA')
            return {'CANCELLED'}

        collect_fadercoordinate_objects(context)
        
        if bpy.data.objects.get("fluid_surface"):
            assign_fader_to_shaders(
                obj=bpy.data.objects["fluid_surface"],
                network_name="FF ClearWater_Passes",
                node_name="ff_compositing_fluidfadercoordinate",
                fader_type="normal"
            )

            assign_fader_to_shaders(
                obj=bpy.data.objects["fluid_surface"],
                network_name="FF ClearWater_Passes",
                node_name="ff_compositing_fluidfadercoordinate_footage",
                fader_type="footage"
            )

        assign_fader_to_modifiers(context)
        bpy.ops.flip_fluid_operators.align_and_parent()  # Renaming also happens here
        bpy.ops.flip_fluid_operators.prepare_uvprojection()
        bpy.ops.flip_fluid_operators.refresh_objectlist()

        # Order modifiers on these objects
        relevant_objects = [
            "fluid_particles",
            "fluid_surface",
            "whitewater_bubble",
            "whitewater_dust",
            "whitewater_foam",
            "whitewater_spray"
        ]

        for obj_name in relevant_objects:
            obj = bpy.data.objects.get(obj_name)
            if obj:
                ensure_modifier_order(obj)

        #self.report({'INFO'}, "Compositing textures and texture coordinates updated, textures reassigned where applicable, and FadeToEdges modifiers applied.")
        return {'FINISHED'}


def flipfluidpasses_createfaderobjects(context, objects):
    """
    Create or update FADER objects for the given objects, including Projection-FADER objects
    only for the fluid_surface object. Only the Projection-FADER of fluid_surface is rotated.

    :param context: Blender context to access scene and properties.
    :param objects: List of objects for which FADER objects need to be created.
    """
    cprops = context.scene.flip_fluid_compositing_tools
    fader_dict = cprops.render_passes_faderobjects_DICT

    def ensure_visibility(obj):
        """Temporarily enable visibility and renderability for the given object."""
        if obj is None:
            return None, None, None

        original_states = (
            obj.hide_get(),
            obj.hide_viewport,
            obj.hide_render,
        )

        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False

        return original_states


    def restore_visibility(obj, original_states):
        """Restore the original visibility and renderability state for the given object."""
        if obj and original_states:
            obj.hide_set(original_states[0])
            obj.hide_viewport = original_states[1]
            obj.hide_render = original_states[2]


    def create_or_update_fader(fader_name, obj, display_type, rotate=False):
        """Create or update a FADER object."""
        fader_object = bpy.data.objects.get(fader_name)
        if fader_object and fader_object.name.endswith("_@"):
            return fader_object

        if not fader_object:
            fader_object = bpy.data.objects.new(fader_name, None)
            bpy.context.scene.collection.objects.link(fader_object)

        fader_object.empty_display_type = display_type
        fader_object.parent = obj
        fader_object.matrix_parent_inverse = obj.matrix_world.inverted()
        fader_object.location = obj.location
        fader_object.scale = obj.scale

        # Apply rotation only if specified
        if rotate:
            fader_object.rotation_euler = (1.5708, 0, 0)

        return fader_object

    for obj in objects:
        if not obj:
            print_render_pass_debug("Warning: Invalid object passed to flipfluidpasses_createfaderobjects.")
            continue

        obj_name = obj.name
        is_fluid_surface = obj_name == "fluid_surface"
        original_states = ensure_visibility(obj) if is_fluid_surface else None

        # Create or update the main FADER object
        fader_name = f"FADER.{obj_name}_@"
        fader_object = create_or_update_fader(fader_name, obj, 'SPHERE' if is_fluid_surface else 'CIRCLE')

        # Add or update the entry in the FADER dictionary
        fader_entry = next((entry for entry in fader_dict if entry.obj_name == obj_name), None)
        if not fader_entry:
            fader_entry = fader_dict.add()
            fader_entry.obj_name = obj_name

        fader_entry.node_object = fader_object
        fader_entry.material_name = next((slot.material.name for slot in obj.material_slots if slot.material), "")

        # Create or update the Projection-FADER object (only for fluid_surface)
        if is_fluid_surface:
            projection_fader_name = f"FADER.{obj_name}_ref_and_footage_@"
            projection_fader_object = bpy.data.objects.get(projection_fader_name)

            if not projection_fader_object:
                projection_fader_object = create_or_update_fader(projection_fader_name, obj, 'CIRCLE', rotate=True)
            else:
                # Apply rotation to an existing Projection-FADER to ensure consistency
                projection_fader_object.rotation_euler = (1.5708, 0, 0)

            fader_entry.projectionnode_object = projection_fader_object

        # Restore visibility for the fluid_surface object
        if is_fluid_surface:
            restore_visibility(obj, original_states)

        # Update coordinates for the FADER objects
        collect_fadercoordinate_objects(context)

    
def assign_fader_to_shaders(obj, network_name, node_name, fader_type="normal"):
    """
    Assign a FADER object to a specific node in a Shader network.

    :param obj: The object for which the FADER is assigned.
    :param network_name: Name of the Shader network (material).
    :param node_name: Name of the node in the network where the FADER will be assigned.
    :param fader_type: Type of the FADER, either "normal" or "footage".
    """
    # Construct the FADER name based on the type
    if fader_type == "footage":
        fader_name = f"FADER.{obj.name}_ref_and_footage_@"
    else:
        fader_name = f"FADER.{obj.name}_@"

    fader_object = bpy.data.objects.get(fader_name)

    if not fader_object:
         return  # Skip execution if FADER does not exist

    # Handle Shader Nodes
    material = bpy.data.materials.get(network_name)
    if not material:
        return

    if not material.use_nodes:
        return

    node = material.node_tree.nodes.get(node_name)

    if not node:
        return

    # Assign the FADER object to the node
    if hasattr(node, "object"):
        node.object = fader_object


def assign_fader_to_modifiers(context):
    """Assigns the FADER object linked to fluid_surface to all relevant nodes in FF_Motion modifiers."""
    
    # Access the centralized fader_dict from the helper properties
    cprops = context.scene.flip_fluid_compositing_tools
    fader_dict = cprops.render_passes_faderobjects_DICT

    # Find the FADER object associated with fluid_surface
    fluid_surface_fader = None
    for entry in fader_dict:
        if entry.obj_name == "fluid_surface":
            fluid_surface_fader = entry.node_object
            break

    if not fluid_surface_fader:
        return

    # Iterate through the objects in the scene
    for obj in bpy.data.objects:
        # Look for modifiers that start with "FF_Motion"
        for modifier in obj.modifiers:
            if modifier.name.startswith("FF_Motion"):
                # Access the geometry nodes in the modifier (assuming it's a GeometryNodes modifier)
                if hasattr(modifier, 'node_group'):
                    for node in modifier.node_group.nodes:
                        # Find nodes that contain 'fadercoordinate' in their name
                        if 'fadercoordinate' in node.name and node.type == 'OBJECT_INFO':
                            node.inputs['Object'].default_value = fluid_surface_fader  # Assign the FADER object to the node's object input


def collect_fadercoordinate_objects(context):
    """Collects objects with materials and nodes, storing them in the centralized fader_dict, including original materials."""
    # Access the centralized fader_dict from the helper properties
    cprops = context.scene.flip_fluid_compositing_tools
    fader_dict = cprops.render_passes_faderobjects_DICT

    # Backup the current entries, ensuring nothing is deleted
    existing_fader_objects = {entry.obj_name: entry for entry in fader_dict}

    # Iterate through the objects in the scene and collect relevant FADER objects
    for obj in bpy.data.objects:
        for material_slot in obj.material_slots:
            material = material_slot.material
            if material and material.use_nodes and (material.name.startswith("FF") or material.name.startswith(".FF")):
                for node in material.node_tree.nodes:
                    # Handle normal FADER (fadercoordinate)
                    if node.name.endswith("fadercoordinate") and not node.name.endswith("_footage"):
                        if hasattr(node, 'object') and node.object:
                            node_object = node.object
                            # Check if this FADER object already exists in the dict
                            if obj.name in existing_fader_objects:
                                # Update the existing entry
                                existing_entry = existing_fader_objects[obj.name]
                                existing_entry.material_name = material.name
                                if not existing_entry.original_materialname:
                                    existing_entry.original_materialname = material.name
                                existing_entry.node_object = node_object
                            else:
                                # Add a new entry to the fader_dict
                                new_entry = fader_dict.add()
                                new_entry.obj_name = obj.name
                                new_entry.material_name = material.name
                                new_entry.original_materialname = material.name
                                new_entry.node_object = node_object

                    # Handle Projection-FADER (fadercoordinate_footage)
                    elif node.name.endswith("fadercoordinate_footage"):
                        if hasattr(node, 'object') and node.object:
                            projection_object = node.object
                            # Check if this FADER object already exists in the dict
                            if obj.name in existing_fader_objects:
                                # Update the existing entry
                                existing_entry = existing_fader_objects[obj.name]
                                existing_entry.projectionnode_object = projection_object
                            else:
                                # Add a new entry to the fader_dict
                                new_entry = fader_dict.add()
                                new_entry.obj_name = obj.name
                                new_entry.material_name = material.name
                                new_entry.original_materialname = material.name
                                new_entry.projectionnode_object = projection_object

                # Break after processing relevant nodes
                break

    # Ensure the existing entries are kept if they were not overwritten
    for obj_name, entry in existing_fader_objects.items():
        if obj_name not in [e.obj_name for e in fader_dict]:
            # Re-add the original entry if it wasn't updated
            new_entry = fader_dict.add()
            new_entry.obj_name = entry.obj_name
            new_entry.material_name = entry.material_name
            new_entry.original_materialname = entry.original_materialname
            new_entry.node_object = entry.node_object
            new_entry.projectionnode_object = getattr(entry, 'projectionnode_object', None)

    # Call this function after updating the dict to print its content
    #print_fader_dict(context)


# To change materials using the list?s buttons we must save original materials of all list-objects into a list
# If there is an object without any material, "FF NoMaterial" will be generated
def collect_all_objects_materials(context):
    """Collects materials for objects listed in render_passes_objectlist, storing them in the centralized dictionary."""
    cprops = context.scene.flip_fluid_compositing_tools
    all_objects_dict = cprops.render_passes_all_objects_materials_DICT
    object_list = cprops.render_passes_objectlist  # Only process objects in this list

    # Backup existing entries
    existing_entries = {entry.obj_name: entry for entry in all_objects_dict}

    # Check if the default material already exists
    default_material = bpy.data.materials.get("FF NoMaterial")
    if not default_material:
        # Create the default material if it doesn't exist
        default_material = bpy.data.materials.new(name="FF NoMaterial")
        default_material.use_nodes = True
        node_tree = default_material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        # Clear existing nodes
        for node in nodes:
            nodes.remove(node)

        # Add a Diffuse BSDF node and Output node
        diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")
        diffuse_node.location = (-300, 0)
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        output_node.location = (0, 0)

        # Link the nodes
        links.new(diffuse_node.outputs["BSDF"], output_node.inputs["Surface"])

    # Process only objects listed in render_passes_objectlist
    for item in object_list:
        obj = bpy.data.objects.get(item.name)
        if not obj:
            continue

        # Skip non-renderable or non-geometry objects (redundant but safe)
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue

        # Skip if already in the dict
        if obj.name in existing_entries:
            continue

        # Determine the material or assign the default one
        if not obj.material_slots or not obj.material_slots[0].material:
            if not obj.material_slots:
                obj.data.materials.append(default_material)
            else:
                obj.material_slots[0].material = default_material

            material = default_material
        else:
            # Use the existing material
            material = obj.material_slots[0].material

        # Add to the dictionary
        new_entry = all_objects_dict.add()
        new_entry.obj_name = obj.name
        new_entry.original_objectname = obj.name
        new_entry.material_name = material.name
        new_entry.original_materialname = material.name
        new_entry.node_object = None  # No specific node object for general objects

    # Re-add entries not updated in the current pass
    for obj_name, entry in existing_entries.items():
        if obj_name not in [e.obj_name for e in all_objects_dict]:
            new_entry = all_objects_dict.add()
            new_entry.obj_name = entry.obj_name
            new_entry.material_name = entry.material_name
            new_entry.original_materialname = entry.original_materialname
            new_entry.node_object = entry.node_object

    # Call this function after updating the dict to print its content
    #print_all_objects_materials_dict(context)


def print_fader_dict(context):
    """Prints the contents of the fader_dict for debugging."""
    # Access the centralized fader_dict from the helper properties
    cprops = context.scene.flip_fluid_compositing_tools
    fader_dict = cprops.render_passes_faderobjects_DICT

    # Iterate through the dict and print the contents
    for entry in fader_dict:
        print_render_pass_debug("FADER LIST ENTRY")
        print_render_pass_debug(f"Object Name: {entry.obj_name}")
        print_render_pass_debug(f"Material Name: {entry.material_name}")
        print_render_pass_debug(f"Original Material Name: {entry.original_materialname}")  # Added this line
        if entry.node_object:
            print_render_pass_debug(f"Node Object: {entry.node_object.name}")
        else:
            print_render_pass_debug("Node Object: None")
        print_render_pass_debug("-------------")


def print_all_objects_materials_dict(context):
    """Prints the contents of the all_objects_materials_dict for debugging."""
    # Access the centralized all_objects_materials_dict from the helper properties
    cprops = context.scene.flip_fluid_compositing_tools
    all_objects_dict = cprops.render_passes_all_objects_materials_DICT

    # Iterate through the dict and print the contents
    for entry in all_objects_dict:
        if entry.node_object:
            print_render_pass_debug(f"Node Object: {entry.node_object.name}")
        else:
            print_render_pass_debug("Node Object: None")
        print_render_pass_debug("-------------")


# Get relevant objects from DICT for modifiers
def get_relevant_objects_from_dict(fader_dict):
    """
    Extract relevant objects from the fader_dict for processing.
    :param fader_dict: The DICT containing object and material information.
    :return: A list of relevant objects.
    """
    relevant_objects = []
    for entry in fader_dict:
        obj = bpy.data.objects.get(entry.obj_name)
        if obj:
            relevant_objects.append(obj)
    return relevant_objects


def ensure_modifier_order(obj):
    priority_modifiers = [
        "Smooth",
        "FF_FadeNearDomain",
        "FF Subdiv. For Projection",
        "FF_FadeNearObjects",
        "FF_GeometryNodesSurface",
        "FF_GeometryNodesFluidParticles",
        "FF_GeometryNodesWhitewaterBubble",
        "FF_GeometryNodesWhitewaterDust",
        "FF_GeometryNodesWhitewaterFoam",
        "FF_GeometryNodesWhitewaterSpray",
        "FF Projection"
    ]

    # Add unknown modifiers to the end of the priority list
    priority_modifiers.extend([mod.name for mod in obj.modifiers if mod.name not in priority_modifiers])

    modifiers = obj.modifiers

    for target_index, priority_name in enumerate(priority_modifiers):
        current_index = next((i for i, mod in enumerate(modifiers) if mod.name == priority_name), None)

        if current_index is None:
            continue

        # Begrenze den target_index
        if target_index >= len(modifiers):
            target_index = len(modifiers) - 1

        # Verschiebe den Modifier
        while current_index != target_index:
            if current_index > target_index:
                modifiers.move(current_index, current_index - 1)
                bpy.context.view_layer.update()
                current_index -= 1
            elif current_index < target_index:
                modifiers.move(current_index, current_index + 1)
                bpy.context.view_layer.update()
                current_index += 1


def add_fadenear_modifiers(obj, modifier_name):
    """
    Add the 'FF_FadeNearDomain' Geometry Nodes modifier to the specified object
    from the Geometry Nodes library and assign the FLIP Fluids domain to the
    'ff_domain_for_fading' node in the modifier.

    :param obj: The object to add the modifier to.
    :param modifier_name: Name of the Geometry Nodes network to load.
    :return: The existing or newly added modifier.
    """
    # Check if the modifier already exists
    existing_modifier = obj.modifiers.get(modifier_name)
    if existing_modifier:
        return existing_modifier

    # Define resource paths
    blend_filename = "geometry_nodes_library.blend"
    parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", blend_filename)

    # Ensure the .blend file exists
    if not os.path.exists(resource_filepath):
        raise FileNotFoundError(f"Geometry Nodes library not found: {resource_filepath}")

    # Load the Geometry Nodes network from the .blend file
    with bpy.data.libraries.load(resource_filepath, link=False) as (data_from, data_to):
        if modifier_name not in data_from.node_groups:
            raise ValueError(f"Node '{modifier_name}' not found in Geometry Nodes library.")
        data_to.node_groups = [modifier_name]

    # Add the Geometry Nodes modifier to the object
    gn_modifier = obj.modifiers.new(name=modifier_name, type='NODES')
    gn_modifier.node_group = bpy.data.node_groups.get(modifier_name)

    # Ensure the modifier is at the correct position in the stack
    ensure_modifier_order(obj)

    return gn_modifier


class FlipFluidPassesApplyAllMaterials(bpy.types.Operator):
    """Apply all necessary materials to the corresponding objects and load the FADER object for fluid_surface."""
    bl_idname = "flip_fluid_operators.apply_all_materials"
    bl_label = "Apply All Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fluid_surface_obj = bpy.data.objects.get("fluid_surface")
        if not fluid_surface_obj:
            self.report({'ERROR'}, "The object 'fluid_surface' is missing. Please run the simulation first.")
            return {'CANCELLED'}

        materials_objects = {
            "FF Bubble_Passes": ["whitewater_bubble", "whitewater_dust"],
            "FF ClearWater_Passes": ["fluid_surface"],
            "FF FluidParticle_Passes": ["fluid_particles"],
            "FF Foam_Passes": ["whitewater_foam"],
            "FF Spray_Passes": ["whitewater_spray"]
        }

        blend_filename = "FF_Compositing.blend"
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blend_file_path = os.path.join(parent_path, "presets", "preset_library", "sys", blend_filename)

        if not os.path.exists(blend_file_path):
            self.report({'ERROR'}, f"Blend file not found: {blend_file_path}")
            return {'CANCELLED'}

        missing_materials = [mat for mat in materials_objects if mat not in bpy.data.materials]
        need_fader_fluid_surface = not any(
            obj.name.startswith("FADER.fluid_surface") for obj in bpy.data.objects.values()
        )

        if missing_materials or need_fader_fluid_surface:
            with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
                data_to.materials = [name for name in data_from.materials if name in missing_materials]
                if need_fader_fluid_surface and "FADER.fluid_surface" in data_from.objects:
                    data_to.objects = ["FADER.fluid_surface"]

            missing_after_load = [mat for mat in missing_materials if mat not in bpy.data.materials]
            if missing_after_load:
                self.report({'ERROR'}, f"Failed to load materials: {', '.join(missing_after_load)}")
                return {'CANCELLED'}

        for material_name, object_names in materials_objects.items():
            material = bpy.data.materials.get(material_name)
            for object_name in object_names:
                obj = bpy.data.objects.get(object_name)
                if obj and material:
                    if not obj.material_slots:
                        obj.data.materials.append(material)
                    else:
                        obj.material_slots[0].material = material

        fader_obj = next(
            (obj for obj in bpy.data.objects.values() if obj.name.startswith("FADER.fluid_surface")),
            None
        )
        if fader_obj and fader_obj.name not in bpy.context.scene.collection.objects:
            fader_footage_obj = fader_obj.copy()
            fader_footage_obj.name = "FADER.fluid_surface_ref_and_footage"
            bpy.context.scene.collection.objects.link(fader_obj)
            bpy.context.scene.collection.objects.link(fader_footage_obj)

        try:
            gn_modifier_domain = add_fadenear_modifiers(fluid_surface_obj, "FF_FadeNearDomain")
        except (FileNotFoundError, ValueError) as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        domain_obj = next(
            (obj for obj in bpy.data.objects if hasattr(obj, "flip_fluid") and obj.flip_fluid.object_type == 'TYPE_DOMAIN'),
            None
        )
        if not domain_obj:
            self.report({'ERROR'}, "No FLIP Fluids domain object found in the scene.")
            return {'CANCELLED'}

        try:
            node_name = "ff_domain_for_fading"
            node = gn_modifier_domain.node_group.nodes.get(node_name)
            if node and node.type == 'OBJECT_INFO':
                node.inputs[0].default_value = domain_obj
        except Exception as e:
            self.report({'ERROR'}, f"Failed to assign domain object: {str(e)}")
            return {'CANCELLED'}

        particle_objects = [
            "fluid_particles",
            "whitewater_bubble",
            "whitewater_dust",
            "whitewater_foam",
            "whitewater_spray"
        ]

        # Apply both FF_FadeNearDomain and FF_FadeNearObjects modifiers to particle objects
        for object_name in particle_objects:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                self.report({'WARNING'}, f"Object '{object_name}' not found. Skipping.")
                continue

            # Apply FF_FadeNearDomain modifier
            try:
                add_fadenear_modifiers(obj, "FF_FadeNearDomain")
            except ValueError as e:
                self.report({'ERROR'}, f"Failed to apply FF_FadeNearDomain to '{object_name}': {str(e)}")
                return {'CANCELLED'}

            # Apply FF_FadeNearObjects modifier
            try:
                add_fadenear_modifiers(obj, "FF_FadeNearObjects")
            except ValueError as e:
                self.report({'ERROR'}, f"Failed to apply FF_FadeNearObjects to '{object_name}': {str(e)}")
                return {'CANCELLED'}

        # Ensure fluid_surface also gets the FF_FadeNearObjects modifier
        try:
            add_fadenear_modifiers(fluid_surface_obj, "FF_FadeNearObjects")
        except ValueError as e:
            self.report({'ERROR'}, f"Failed to apply FF_FadeNearObjects to 'fluid_surface': {str(e)}")
            return {'CANCELLED'}

        assign_objects_to_fading_network(context)

        flipfluidpasses_createfaderobjects(context, [fluid_surface_obj])

        bpy.ops.flip_fluid_operators.helper_fix_compositingtextures()
        
        self.report({'INFO'}, "All materials and Geometry Nodes modifiers have been successfully applied.")
        return {'FINISHED'}


# New central function for create_quick_operators
def create_quick_catcher(context, base_name, flag_toggle_operator, fgbg_value, reflective_value):
    """Generic function to create a quick catcher element with specific settings."""
    cprops = context.scene.flip_fluid_compositing_tools

    # Find the ff_camera_screen object
    screen_obj = bpy.data.objects.get("ff_camera_screen")
    if not screen_obj:
        show_message_box("There is no ff_camera_screen object. Please add the CameraScreen first.", title="Missing Object", icon='IMAGE_BACKGROUND')
        return {'CANCELLED'}

    # Create a plane at the 3D cursor position
    bpy.ops.mesh.primitive_plane_add(align='WORLD', enter_editmode=False, location=bpy.context.scene.cursor.location)
    plane = bpy.context.object
    plane.rotation_euler = (1.5708, 0, 0)  # 90 degrees in radians (x-axis)

    # Rename the plane to the specified base name
    plane.name = base_name if not bpy.data.objects.get(base_name) else bpy.data.objects.get(base_name).name

    # Sync FADER DICT
    collect_fadercoordinate_objects(context)

    # Add to object list
    bpy.ops.flip_fluid_operators.add_item_to_list()

    # Get the index of the newly added object in the render_passes_objectlist
    new_index = len(cprops.render_passes_objectlist) - 1  # Assuming the new item is added at the end of the list

    # Check and apply the FF Elements_Passes material
    passes_material_name = f"FF Elements_Passes_{plane.name}"
    material = bpy.data.materials.get(passes_material_name)
    if not material:
        # Load or copy the base material if it doesn't exist
        blend_filename = "FF_Compositing.blend"
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_filepath = os.path.join(parent_path, "presets", "preset_library", "sys", blend_filename)
        if not os.path.exists(resource_filepath):
            raise FileNotFoundError(f"Blend file not found: {resource_filepath}")

        base_material_name = "FF Elements_Passes"
        with bpy.data.libraries.load(resource_filepath, link=False) as (data_from, data_to):
            if base_material_name in data_from.materials:
                data_to.materials = [base_material_name]
            else:
                raise ValueError(f"Material '{base_material_name}' not found in Blend file.")

        base_material = bpy.data.materials.get(base_material_name)
        material = base_material.copy()
        material.name = passes_material_name
        material.asset_clear()

    # Apply the material to the plane
    plane.data.materials.clear()
    plane.data.materials.append(material)

    # Update the material nodes
    if material.use_nodes:
        node_tree = material.node_tree
        fgbg_node = node_tree.nodes.get("ff_fgbg_element")
        reflective_node = node_tree.nodes.get("ff_reflective_element")
        fade_node = node_tree.nodes.get("ff_elements_fading")
        if fgbg_node and reflective_node:
            fgbg_node.outputs[0].default_value = fgbg_value
            reflective_node.outputs[0].default_value = reflective_value

        # Set fade_node default_value to 1.0 for MediaProperty objects
        if any(media_item.object_name == plane.name for media_item in cprops.render_passes_import_media):
            if fade_node:
                fade_node.inputs[0].default_value = 1.0  # Not pressed

    # Configure plane properties
    plane.show_name = False
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.shade_smooth()
    plane.visible_diffuse = True
    plane.visible_glossy = True
    plane.visible_transmission = True
    plane.visible_volume_scatter = True
    plane.visible_shadow = True
    
    # Cannot be called earlier! 
    # Set the appropriate flag using the provided operator
    flag_toggle_operator(index=new_index)

    bpy.ops.flip_fluid_operators.refresh_objectlist()
    bpy.ops.flip_fluid_operators.helper_fix_compositingtextures()

    return {'FINISHED'}


class FlipFluidPassesQuickForegroundCatcher(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.quick_foregroundcatcher"
    bl_label = "Add Quick ForegroundCatcher"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: StringProperty(name="Object Name", default="")
    texture_name: StringProperty(name="Texture Name", default="")

    def execute(self, context):
        base_name = self.obj_name if self.obj_name else "ff_foreground_element"
        return create_quick_catcher(
            context,
            base_name=base_name,
            flag_toggle_operator=bpy.ops.flip_fluid_operators.toggle_fg_elements,
            fgbg_value=0,
            reflective_value=0
        )


class FlipFluidPassesQuickBackgroundCatcher(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.quick_backgroundcatcher"
    bl_label = "Add Quick BackgroundCatcher"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return create_quick_catcher(
            context,
            base_name="ff_background_element",
            flag_toggle_operator=bpy.ops.flip_fluid_operators.toggle_bg_elements,
            fgbg_value=1,
            reflective_value=0
        )


class FlipFluidPassesQuickReflectiveCatcher(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.quick_reflectivecatcher"
    bl_label = "Add Quick ReflectiveCatcher"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return create_quick_catcher(
            context,
            base_name="ff_reflective_element",
            flag_toggle_operator=bpy.ops.flip_fluid_operators.toggle_reflective,
            fgbg_value=1,
            reflective_value=1
        )


class FlipFluidPassesQuickGround(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.quick_ground"
    bl_label = "Add Quick Ground"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        # Check if a Ground object already exists
        if any(item.ground for item in cprops.render_passes_objectlist):
            show_message_box(
                message="Only one object can be flagged as 'Ground'. A Ground object already exists.",
                title="Ground Object Conflict",
                icon='ERROR'
            )
            return {'CANCELLED'}  # Prevent the creation of a new Ground object

        # If no Ground object exists, proceed with creating the Quick Ground object
        return create_quick_catcher(
            context,
            base_name="ff_groundobject",
            flag_toggle_operator=bpy.ops.flip_fluid_operators.toggle_ground,
            fgbg_value=0,
            reflective_value=0
        )


class FlipFluidPrepareUVProjection(bpy.types.Operator):
    """Applies Subdivision Surface and UV Project Modifiers to objects with 'FF Elements' materials in the correct order, including 'fluid_surface'."""
    bl_idname = "flip_fluid_operators.prepare_uvprojection"
    bl_label = "Prepare UV Projection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the scene camera from the flip_fluid_compositing_tools properties
        cprops = context.scene.flip_fluid_compositing_tools
        scene_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
        if not scene_camera or scene_camera.type != 'CAMERA':
            show_message_box(message="Camera specified in flip_fluid_compositing_tools not found or is not a camera.", title="Error", icon='CAMERA_DATA')
            return {'CANCELLED'}

        # Prepare lists for objects
        subdivision_objects = []
        uv_projection_objects = []

        for obj in bpy.data.objects:
            # Always include fluid_surface in UV projection
            if obj.name == "fluid_surface":
                uv_projection_objects.append(obj)
                continue

            # Check if object has 'FF Elements' materials
            if obj.material_slots:
                for mat_slot in obj.material_slots:
                    material = mat_slot.material
                    if material and material.name.startswith("FF Elements"):
                        subdivision_objects.append(obj)
                        uv_projection_objects.append(obj)

        if not uv_projection_objects:
            show_message_box(message="No relevant objects found for UV projection.", title="Information", icon='INFO')
            return {'CANCELLED'}

        # Apply Subdivision Modifier to objects in the subdivision list
        for obj in subdivision_objects:
            subdiv_modifier = obj.modifiers.get("FF Subdiv. For Projection")
            if not subdiv_modifier:
                subdiv_modifier = obj.modifiers.new(name="FF Subdiv. For Projection", type='SUBSURF')
                subdiv_modifier.subdivision_type = 'CATMULL_CLARK' #'SIMPLE'
                subdiv_modifier.levels = 3
                subdiv_modifier.render_levels = 6

        # Apply UV Project Modifier to objects in the UV projection list
        for obj in uv_projection_objects:
            uv_project_modifier = obj.modifiers.get("FF Projection")
            if not uv_project_modifier:
                uv_project_modifier = obj.modifiers.new(name="FF Projection", type='UV_PROJECT')

            # Configure the UV Project Modifier
            if obj.data.uv_layers and "UVMap" in obj.data.uv_layers:
                uv_project_modifier.uv_layer = obj.data.uv_layers.get("UVMap").name
            else:
                # Skip UV Map check for fluid_surface
                if obj.name != "fluid_surface":
                    show_message_box(message=f"No UVMap found on {obj.name}.", title="Error", icon='UV')
                    continue

            uv_project_modifier.projector_count = 1
            if uv_project_modifier.projectors:
                uv_project_modifier.projectors[0].object = scene_camera
                render = context.scene.render
                aspect_x = render.resolution_x / render.resolution_y
                uv_project_modifier.aspect_x = aspect_x
                uv_project_modifier.aspect_y = 1.0 / aspect_x

            # Ensure correct modifier order
            ensure_modifier_order(obj)

        #self.report({'INFO'}, "UV Projection prepared.")
        return {'FINISHED'}


def remove_modifiers_if_no_toggles(obj, cprops):
    """Remove Subdivision and UV Project Modifiers if all toggles in list are off."""
    # Check if the object exists in the render_passes_objectlist
    item = next((i for i in cprops.render_passes_objectlist if i.name == obj.name), None)
    if not item or (item.fg_elements or item.bg_elements or item.ref_elements or item.ground):
        return  # Do nothing if any toggle is still active

    # Remove Subdivision Modifier
    subdiv_modifier = obj.modifiers.get("FF Subdiv. For Projection")
    if subdiv_modifier:
        obj.modifiers.remove(subdiv_modifier)

    # Remove UV Project Modifier
    uv_project_modifier = obj.modifiers.get("FF Projection")
    if uv_project_modifier:
        obj.modifiers.remove(uv_project_modifier)


class FlipFluidToggleAlignmentGridVisibility(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_alignmentgrid_visibility"
    bl_label = "Toggle Alignment Grid Visibility"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools

        ff_alignment_grid = bpy.data.objects.get("ff_alignment_grid")
        if ff_alignment_grid:
            ff_alignment_grid.hide_viewport = not cprops.render_passes_alignmentgrid_visibility
        return {'FINISHED'}


class FlipFluidPassesAddAlignmentGrid(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.add_alignment_grid"
    bl_label = "Add Alignment Grid"

    def execute(self, context):
        if bpy.data.objects.get("ff_alignment_grid"):
            show_message_box(message="An alignment grid already exists!", title="Warning", icon='GRID')
            return {'CANCELLED'}

        bpy.ops.mesh.primitive_plane_add(size=10, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        plane = bpy.context.object
        plane.name = "ff_alignment_grid"
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=5)
        bpy.ops.object.mode_set(mode='OBJECT')

        subdivision_mod = plane.modifiers.new(name="Subdivision", type='SUBSURF')
        subdivision_mod.levels = 1
        subdivision_mod.subdivision_type = 'SIMPLE'

        wireframe_mod = plane.modifiers.new(name="Wireframe", type='WIREFRAME')
        wireframe_mod.thickness = 0.005

        material = bpy.data.materials.new(name="FF Alignment Grid")
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        material_output = material.node_tree.nodes.get("Material Output")
        
        emission_node = material.node_tree.nodes.new('ShaderNodeEmission')
        emission_node.inputs['Color'].default_value = (1, 0, 0, 1)  # Rot
        emission_node.inputs['Strength'].default_value = 2

        material.node_tree.links.new(emission_node.outputs['Emission'], material_output.inputs['Surface'])
        plane.data.materials.append(material)

        plane.hide_render = True

        return {'FINISHED'}


### FADING:

class FlipFluidPassesToggleFaderObjectsVisibility(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_faderobjects_visibility"
    bl_label = "Toggle Fader Objects Visibility"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        visibility = cprops.render_passes_faderobjects_visibility

        # Iterate through all objects in the current Blender file
        for obj in bpy.data.objects:
            # Check if "fader" is in the object's name
            if "fader" in obj.name.lower():
                # Set the object's visibility for the viewport based on the property
                obj.hide_viewport = not visibility
                obj.hide_render = not visibility

        return {'FINISHED'}


class FlipFluidPassesToggleFaderObjectNamesVisibility(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_faderobjectnames_visibility"
    bl_label = "Toggle Fader Objects Names Visibility"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        visibility = cprops.render_passes_faderobjectnames_visibility

        # Iterate through all objects in the current Blender file
        for obj in bpy.data.objects:
            # Check if "fader" is in the object's name
            if "fader" in obj.name.lower():
                # Set the object's name visibility for the viewport based on the property
                obj.show_name = visibility

        return {'FINISHED'}


class FlipFluidPassesToggleObjectNamesVisibility(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_objectnames_visibility"
    bl_label = "Toggle Objects Names Visibility"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        visibility = cprops.render_passes_objectnames_visibility

        # Iterate through all objects in the current Blender file
        for obj in bpy.data.objects:
            # Set the object's name visibility for the viewport based on the property
            obj.show_name = visibility

        return {'FINISHED'}


def update_fader_combination_fluidsurface(context):
    """
    Update the fader combination property and propagate the value to relevant nodes.

    Args:
        context: Blender context for accessing scene-specific data.
        self: Optional reference to the operator calling this function (for reporting).
    """
    cprops = context.scene.flip_fluid_compositing_tools  # Zugriff auf die Compositing-Properties

    # Calculate the combined value from toggles and flags
    value = 0
    if cprops.render_passes_toggle_fader_fluidsurface:
        value += 1
    if cprops.render_passes_toggle_speed_fluidsurface:
        value += 2
    if cprops.render_passes_toggle_domain_fluidsurface:
        value += 4
    if cprops.render_passes_has_unflagged_objects:
        value += 8

    # Store the combined value
    cprops.render_passes_fader_combination_fluidsurface = value

    # Update unflagged objects property
    update_unflagged_objects_property(context)

    # Function to set the value in 'ff_combination_control_fluidsurface' nodes
    def update_combination_node(node):
        if node.type == 'VALUE' and node.name == "ff_combination_control_fluidsurface":
            node.outputs[0].default_value = value

    # Update materials
    for material in bpy.data.materials:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                update_combination_node(node)

    # Update Geometry Nodes
    for node_group in bpy.data.node_groups:
        if node_group.name.startswith("FF") or node_group.name.startswith(".FF"):
            for node in node_group.nodes:
                update_combination_node(node)

    # Optional reporting
    #if self:
    #    self.report({'INFO'}, "Fader combination updated successfully.")


class FlipFluidPassesCalculateFaderCombinationFluidSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_ops.calc_fader_comb_fluidsurface"
    bl_label = "Calculate Fader Combination for fluid_surface"

    def execute(self, context):
        update_fader_combination_fluidsurface(context)
        return {'FINISHED'}


class FlipFluidToggleFaderFluidSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_fader_fluidsurface"
    bl_label = "Toggle Fader Fluid Surface"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        cprops.render_passes_toggle_fader_fluidsurface = not cprops.render_passes_toggle_fader_fluidsurface
        return {'FINISHED'}


class FlipFluidToggleSpeedFluidSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_speed_fluidsurface"
    bl_label = "Toggle Speed Fluid Surface"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        cprops.render_passes_toggle_speed_fluidsurface = not cprops.render_passes_toggle_speed_fluidsurface
        return {'FINISHED'}


class FlipFluidToggleDomainFluidSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_domain_fluidsurface"
    bl_label = "Toggle Domain Fluid Surface"

    def execute(self, context):
        cprops = context.scene.flip_fluid_compositing_tools
        cprops.render_passes_toggle_domain_fluidsurface = not cprops.render_passes_toggle_domain_fluidsurface
        return {'FINISHED'}


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


def register():
    bpy.utils.register_class(FlipFluidOperatorsInitializeCompositing)
    bpy.utils.register_class(FlipFluidPassesToggleStillImageMode)
    bpy.utils.register_class(FlipFluidPassesToggleFade)
    bpy.utils.register_class(FlipFluidPassesToggleShadowCatcher)
    bpy.utils.register_class(FlipFluidPassesTogglefg_elements)
    bpy.utils.register_class(FlipFluidPassesTogglebg_elements)
    bpy.utils.register_class(FlipFluidPassesToggleReflective)
    bpy.utils.register_class(FlipFluidPassesToggleGround)
    bpy.utils.register_class(FlipFluidPassesAddItemToList)
    bpy.utils.register_class(FlipFluidPassesDuplicateItemInList)
    bpy.utils.register_class(FlipFluidPassesRemoveItemFromList)
    bpy.utils.register_class(FLIPFLUID_UL_passes_items)
    bpy.utils.register_class(FlipFluidPassesAddCameraScreen)
    bpy.utils.register_class(FlipFluidPassesImportMedia)
    bpy.utils.register_class(FlipFluidToggleCameraScreenVisibility)
    bpy.utils.register_class(FlipFluidPassesFixCompositingTextures)
    bpy.utils.register_class(FlipFluidPassesApplyAllMaterials)
    bpy.utils.register_class(FlipFluidPassesSelectObjectInList)
    bpy.utils.register_class(FlipFluidPassesRefreshObjectList)
    bpy.utils.register_class(FlipFluidAlignAndParentOperator)
    bpy.utils.register_class(FlipFluidPassesQuickForegroundCatcher)
    bpy.utils.register_class(FlipFluidPassesQuickBackgroundCatcher)
    bpy.utils.register_class(FlipFluidPassesQuickReflectiveCatcher)
    bpy.utils.register_class(FlipFluidPassesQuickGround)
    bpy.utils.register_class(FlipFluidToggleAlignmentGridVisibility)
    bpy.utils.register_class(FlipFluidPassesAddAlignmentGrid)
    bpy.utils.register_class(FlipFluidPrepareUVProjection)
    bpy.utils.register_class(FlipFluidPassesToggleFaderObjectsVisibility)
    bpy.utils.register_class(FlipFluidPassesToggleFaderObjectNamesVisibility)
    bpy.utils.register_class(FlipFluidPassesToggleObjectNamesVisibility)
    bpy.utils.register_class(FlipFluidToggleFaderFluidSurface)
    bpy.utils.register_class(FlipFluidToggleSpeedFluidSurface)
    bpy.utils.register_class(FlipFluidToggleDomainFluidSurface)
    bpy.utils.register_class(FlipFluidPassesCalculateFaderCombinationFluidSurface)
    bpy.utils.register_class(FlipFluidPassesResetSettings)


def unregister():
    bpy.utils.unregister_class(FlipFluidOperatorsInitializeCompositing)
    bpy.utils.unregister_class(FlipFluidPassesToggleStillImageMode)
    bpy.utils.unregister_class(FlipFluidPassesToggleFade)
    bpy.utils.unregister_class(FlipFluidPassesToggleShadowCatcher)
    bpy.utils.unregister_class(FlipFluidPassesTogglefg_elements)
    bpy.utils.unregister_class(FlipFluidPassesTogglebg_elements)
    bpy.utils.unregister_class(FlipFluidPassesToggleReflective)
    bpy.utils.unregister_class(FlipFluidPassesToggleGround)
    bpy.utils.unregister_class(FlipFluidPassesAddItemToList)
    bpy.utils.unregister_class(FlipFluidPassesDuplicateItemInList)
    bpy.utils.unregister_class(FlipFluidPassesRemoveItemFromList)
    bpy.utils.unregister_class(FLIPFLUID_UL_passes_items)
    bpy.utils.unregister_class(FlipFluidPassesAddCameraScreen)
    bpy.utils.unregister_class(FlipFluidPassesImportMedia)
    bpy.utils.unregister_class(FlipFluidToggleCameraScreenVisibility)
    bpy.utils.unregister_class(FlipFluidPassesFixCompositingTextures)
    bpy.utils.unregister_class(FlipFluidPassesApplyAllMaterials)
    bpy.utils.unregister_class(FlipFluidPassesSelectObjectInList)
    bpy.utils.unregister_class(FlipFluidPassesRefreshObjectList)
    bpy.utils.unregister_class(FlipFluidAlignAndParentOperator)
    bpy.utils.unregister_class(FlipFluidPassesQuickForegroundCatcher)
    bpy.utils.unregister_class(FlipFluidPassesQuickBackgroundCatcher)
    bpy.utils.unregister_class(FlipFluidPassesQuickReflectiveCatcher)
    bpy.utils.unregister_class(FlipFluidPassesQuickGround)
    bpy.utils.unregister_class(FlipFluidToggleAlignmentGridVisibility)
    bpy.utils.unregister_class(FlipFluidPassesAddAlignmentGrid)
    bpy.utils.unregister_class(FlipFluidPrepareUVProjection)
    bpy.utils.unregister_class(FlipFluidPassesToggleFaderObjectsVisibility)
    bpy.utils.unregister_class(FlipFluidPassesToggleFaderObjectNamesVisibility)
    bpy.utils.unregister_class(FlipFluidPassesToggleObjectNamesVisibility)
    bpy.utils.unregister_class(FlipFluidToggleFaderFluidSurface)
    bpy.utils.unregister_class(FlipFluidToggleSpeedFluidSurface)
    bpy.utils.unregister_class(FlipFluidToggleDomainFluidSurface)
    bpy.utils.unregister_class(FlipFluidPassesCalculateFaderCombinationFluidSurface)
    bpy.utils.unregister_class(FlipFluidPassesResetSettings)