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

import bpy, os, platform, math, mathutils
from bpy.props import (
        IntProperty,
        FloatProperty,
        StringProperty,
        BoolProperty,
        PointerProperty,
        EnumProperty
        )

from .custom_properties import (
        NewMinMaxIntProperty,
        )

from . import preset_properties
from .. import types
from ..operators import helper_operators
from ..utils import version_compatibility_utils as vcu

from ..operators.command_line_operators import print_render_pass_debug

DISABLE_FRAME_CHANGE_POST_HANDLER = False

# Compositing:
def _update_render_passes_camera_screen(self, context):
    hprops = context.scene.flip_fluid_helper
    override_preferences = True  # Feature enable override for development purposes
    if hprops.display_compositing_tools_in_ui or override_preferences:

        # Retrieve the camera screen object
        bl_camera_screen = bpy.data.objects.get("ff_camera_screen")
        if bl_camera_screen is None:
            #print_render_pass_debug("Camera screen not found.")
            return

        # Retrieve the camera object
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        if bl_camera is None:
            #print_render_pass_debug("Camera not found.")
            return

        # Default image aspect ratio
        image_aspect_ratio = 1.0  

        # Derive aspect ratio from the Plane's dimensions
        dimensions = bl_camera_screen.dimensions
        if dimensions.x > 0 and dimensions.y > 0:
            image_aspect_ratio = dimensions.x / dimensions.y
        else:
            print_render_pass_debug("Warning: Invalid Plane dimensions. Defaulting to aspect ratio of 1.0.")

        # Update the camera screen scale
        helper_operators.update_camera_screen_scale(
            bl_camera_screen,
            bl_camera,
            image_aspect_ratio=image_aspect_ratio
        )


# Camerascreen:
def update_camerascreen_visibility(self, context):
    bpy.ops.flip_fluid_operators.toggle_camerascreen_visibility()


# Still Image Modes:
def still_image_mode_updated(self, context):
    bpy.ops.flip_fluid_operators.toggle_still_image_mode()


# Alignment Grid:    
def update_alignmentgrid_visibility(self, context):
    bpy.ops.flip_fluid_operators.toggle_alignmentgrid_visibility()


# Wrapper for updatefunctions of the passes:
def update_render_pass_property_and_availability(self, context):
    """Wrapper function to call both update functions"""
    update_render_pass_property(self, context)
    update_render_passes_availability(context)


def update_render_passes_availability(context):
    """Updates the availability of render pass checkboxes based on scene conditions."""
    
    hprops = context.scene.flip_fluid_helper

    # Hole das FLIP Fluids Domain-Objekt, falls vorhanden
    domain = context.scene.flip_fluid.get_domain_object()

    # Fluid Surface nur wenn "fluid_surface" existiert
    if "fluid_surface" not in bpy.data.objects and hprops.render_passes_fluid_only:
        hprops.render_passes_fluid_only = False

    # Objects nur wenn ungetaggte Objekte existieren
    if not hprops.render_passes_has_unflagged_objects and hprops.render_passes_objects_only:
        hprops.render_passes_objects_only = False

    # Elements nur wenn mindestens ein Objekt FG, BG oder REF hat
    has_elements = any(
        item.fg_elements or item.bg_elements or item.ref_elements
        for item in hprops.render_passes_objectlist
    )
    if not has_elements and hprops.render_passes_elements_only:
        hprops.render_passes_elements_only = False

    # Fluid Particles nur wenn im Simulator aktiviert
    if domain and not domain.flip_fluid.domain.particles.enable_fluid_particle_output and hprops.render_passes_fluidparticles_only:
        hprops.render_passes_fluidparticles_only = False

    # Foam & Spray & Bubbles & Dust nur wenn WhiteWater aktiviert ist
    if domain and not domain.flip_fluid.domain.whitewater.enable_whitewater_simulation:
        if hprops.render_passes_foamandspray_only:
            hprops.render_passes_foamandspray_only = False
        if hprops.render_passes_bubblesanddust_only:
            hprops.render_passes_bubblesanddust_only = False


def update_render_pass_property(self, context):
    """Callback function to update render_passes_is_any_pass_enabled"""
    update_render_passes_is_any_pass_enabled(self)


# Each Render Passes State:
def update_render_passes_is_any_pass_enabled(self):
    """Check if at least one render pass is enabled and update the property"""
    self.render_passes_is_any_pass_enabled = (
        self.render_passes_fluid_only or
        self.render_passes_fluidparticles_only or
        self.render_passes_objects_only or
        self.render_passes_elements_only or
        self.render_passes_bubblesanddust_only or
        self.render_passes_foamandspray_only
    )


# Fading:
def update_faderobjects_visibility(self, context):
    bpy.ops.flip_fluid_operators.toggle_faderobjects_visibility()

def update_faderobjectnames_visibility(self, context):
    bpy.ops.flip_fluid_operators.toggle_faderobjectnames_visibility()

def update_objectnames_visibility(self, context):
    bpy.ops.flip_fluid_operators.toggle_objectnames_visibility()

def update_fader_fluidsurface_toggle(self, context):
    bpy.ops.flip_fluid_ops.calc_fader_comb_fluidsurface()
 
def update_speed_fluidsurface_toggle(self, context):
    """
    Update the state of the Speed toggle and manage Velocity accordingly.
    """
    # Store a reference to the Flip Fluid Helper properties
    hprops = context.scene.flip_fluid_helper

    # Save the current state of Velocity if Speed is being disabled
    if not hprops.render_passes_toggle_speed_fluidsurface:
        hprops.render_passes_last_velocity_state = hprops.render_passes_toggle_velocity_fluidsurface
        hprops.render_passes_toggle_velocity_fluidsurface = 0  # Disable Velocity when Speed is off

    # Restore the last saved state of Velocity if Speed is being enabled
    elif hprops.render_passes_toggle_speed_fluidsurface:
        hprops.render_passes_toggle_velocity_fluidsurface = hprops.render_passes_last_velocity_state

    # Call any additional operations
    bpy.ops.flip_fluid_ops.calc_fader_comb_fluidsurface()

        
def update_domain_fluidsurface_toggle(self, context):
    bpy.ops.flip_fluid_ops.calc_fader_comb_fluidsurface()


def update_blend_footage(self, context):
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        return

    node_tree = material.node_tree
    target_node = node_tree.nodes.get("ff_fluidsurface_projection")
    if target_node:
        blend_input = target_node.inputs[0]
        if blend_input:
            blend_input.default_value = self.render_passes_blend_footage_to_fluidsurface

def update_blend_normalmap(self, context):
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        return

    node_tree = material.node_tree
    target_node = node_tree.nodes.get("ff_normalmap_to_surface")
    if target_node:
        blend_input = target_node.inputs[0]
        if blend_input:
            blend_input.default_value = self.render_passes_blend_normalmap_to_fluidsurface

def update_velocity_fluidsurface_toggle(self, context):
    """Update the velocity blending toggle in the material node and Geometry Node networks."""
    # Update the Shader Node in the material
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        print_render_pass_debug("Material 'FF ClearWater_Passes' not found or it does not use nodes.")
    else:
        node_tree = material.node_tree

        # Search for the node 'ff_use_velocity_for_blending'
        for node in node_tree.nodes:
            if node.name == "ff_use_velocity_for_blending" and node.type == 'MIX':  # Ensure it's the correct type
                # Set the Factor input based on the toggle state
                node.inputs[0].default_value = 0.0 if not self.render_passes_toggle_velocity_fluidsurface else 1.0
                break
        else:
            print_render_pass_debug("Node 'ff_use_velocity_for_blending' not found in material 'FF ClearWater_Passes'.")

    # Update the Geometry Nodes in the networks
    geonode_networks = [
        "FF_GeometryNodesFluidParticles",
        "FF_GeometryNodesWhitewaterBubble",
        "FF_GeometryNodesWhitewaterSpray",
        "FF_GeometryNodesWhitewaterFoam",
        "FF_GeometryNodesWhitewaterDust"
    ]

    for network_name in geonode_networks:
        geo_node_group = bpy.data.node_groups.get(network_name)
        if not geo_node_group:
            continue

        # Search for the node 'ff_use_velocity_for_blending'
        node = geo_node_group.nodes.get("ff_use_velocity_for_blending")
        if node:
            # Set the Factor input based on the toggle state
            if "Factor" in node.inputs:
                node.inputs[0].default_value = 0.0 if not self.render_passes_toggle_velocity_fluidsurface else 1.0
            else:
                print_render_pass_debug(f"Node '{node.name}' in Geometry Node group '{network_name}' does not have a 'Factor' input.")
        else:
            print_render_pass_debug(f"Node 'ff_use_velocity_for_blending' not found in Geometry Node group '{network_name}'.")

def update_velocity_invert_toggle(self, context):
    """
    Update the 'Invert Velocity' property in the FF ClearWater_Passes material and Geometry Node networks.
    """
    # Update the Shader Node in the material
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        print_render_pass_debug("Material 'FF ClearWater_Passes' not found or it does not use nodes.")
    else:
        node_tree = material.node_tree
        target_node = node_tree.nodes.get("ff_invert_velocity")
        if target_node:
            invert_input = target_node.inputs[0]
            if invert_input:
                invert_input.default_value = 1 if self.render_passes_toggle_velocity_invert else 0

    # Update the Geometry Nodes in the networks
    geonode_networks = [
        "FF_GeometryNodesFluidParticles",
        "FF_GeometryNodesWhitewaterBubble",
        "FF_GeometryNodesWhitewaterSpray",
        "FF_GeometryNodesWhitewaterFoam",
        "FF_GeometryNodesWhitewaterDust"
    ]

    for network_name in geonode_networks:
        geo_node_group = bpy.data.node_groups.get(network_name)
        if not geo_node_group:
            print_render_pass_debug(f"Geometry Node group '{network_name}' not found.")
            continue

        # Search for the node 'ff_invert_velocity'
        target_node = geo_node_group.nodes.get("ff_invert_velocity")
        if target_node:
            # Update the Multiply Node input value
            try:
                multiply_input = target_node.inputs[1]  # Direktzugriff auf den zweiten Input
                multiply_input.default_value = 1 if not self.render_passes_toggle_velocity_invert else -1
            except IndexError:
                print_render_pass_debug(f"Node '{target_node.name}' in Geometry Node group '{network_name}' does not have enough inputs.")
        else:
            print_render_pass_debug(f"Node 'ff_invert_velocity' not found in Geometry Node group '{network_name}'.")


def update_testcolor_toggle(self, context):
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        return

    node_tree = material.node_tree
    relevant_node_prefix = "ff_projection_tester"
    relevant_nodes = [
        node for node in node_tree.nodes 
        if node.name.startswith(relevant_node_prefix) and node.type == 'VALUE'
    ]

    for node in relevant_nodes:
        node.outputs[0].default_value = float(self.render_passes_toggle_projectiontester)


def update_projectionfader_toggle(self, context):
    print_render_pass_debug("Update function triggered!")
    material = bpy.data.materials.get("FF ClearWater_Passes")
    if not material or not material.use_nodes:
        print_render_pass_debug("Material not found or does not use nodes.")
        return

    node_tree = material.node_tree
    relevant_node_prefix = "ff_projection_fader"

    # Filtern der relevanten ShaderNodeMix-Nodes
    relevant_nodes = [
        node for node in node_tree.nodes
        if node.name.startswith(relevant_node_prefix) and node.type == 'MIX'
    ]

    for node in relevant_nodes:
        print_render_pass_debug(f"Node Name: {node.name}")
        print_render_pass_debug(f"Node Type: {node.type}")
        print_render_pass_debug(f"Node Inputs: {[input.name for input in node.inputs]}")

        # Prüfen, ob der Factor-Socket (Input 0) nicht verlinkt ist
        if not node.inputs[0].is_linked:
            node.inputs[0].default_value = float(self.render_passes_toggle_projectionfader)
            print_render_pass_debug(f"Updated Node '{node.name}' Factor to {node.inputs[0].default_value}")
        else:
            print_render_pass_debug(f"Input[0] of Node '{node.name}' is linked. Skipping update.")


def update_object_fading_width(self, context):
    """Update the object-based fading width and softness for all specified objects."""
    objects = [
        "fluid_particles",
        "whitewater_foam",
        "whitewater_bubble",
        "whitewater_spray",
        "whitewater_dust"
    ]
    for obj_name in objects:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            modifier = obj.modifiers.get("FF_FadeNearObjects")
            if modifier:
                # Update Fading Width (Socket_2)
                if "Socket_2" in modifier.keys():
                    modifier["Socket_2"] = context.scene.flip_fluid_helper.render_passes_object_fading_width
                
                # Update Fading Softness (Socket_3)
                if "Socket_3" in modifier.keys():
                    modifier["Socket_3"] = context.scene.flip_fluid_helper.render_passes_object_fading_softness

                # Refresh the modifier
                modifier.show_viewport = False
                modifier.show_viewport = True

    bpy.context.view_layer.update()


def update_object_fading_width_fluid_surface(self, context):
    """Update the object-based fading width and softness for all specified objects."""
    objects = [
        "fluid_surface"
    ]
    for obj_name in objects:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            modifier = obj.modifiers.get("FF_FadeNearObjects")
            if modifier:
                # Update Fading Width (Socket_2)
                if "Socket_2" in modifier.keys():
                    modifier["Socket_2"] = context.scene.flip_fluid_helper.render_passes_object_fading_width_fluid_surface
                
                # Update Fading Softness (Socket_3)
                if "Socket_3" in modifier.keys():
                    modifier["Socket_3"] = context.scene.flip_fluid_helper.render_passes_object_fading_softness_fluid_surface

                # Refresh the modifier
                modifier.show_viewport = False
                modifier.show_viewport = True

    bpy.context.view_layer.update()


def update_general_fading_width(self, context):
    """Update the general fading width for all specified objects."""
    objects = [
        "fluid_particles",
        "whitewater_foam",
        "whitewater_bubble",
        "whitewater_spray",
        "whitewater_dust"
    ]
    for obj_name in objects:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            # Find the correct MotionBlur modifier
            for modifier in obj.modifiers:
                if modifier.name.startswith("FF_GeometryNodes") and "Socket_1" in modifier.keys():
                    # Direkt auf die Property zugreifen
                    modifier["Socket_1"] = context.scene.flip_fluid_helper.render_passes_general_fading_width

                    modifier.show_viewport = False
                    modifier.show_viewport = True

    bpy.context.view_layer.update()


def update_findreflections_toggle(self, context):
    """When 'Find Reflections' is toggled, update the scene accordingly by modifying material node settings directly."""
    hprops = context.scene.flip_fluid_helper

    # We'll work directly on the "FF ClearWater_Passes" material nodes:
    material = bpy.data.materials.get("FF ClearWater_Passes")

    # Helper inline function to set a Mix Shader node (FAC input) by node prefix
    def set_mix_shader_fac(prefix, value):
        if material and material.use_nodes:
            node_tree = material.node_tree
            relevant_nodes = [
                node for node in node_tree.nodes
                if node.name.startswith(prefix) and node.type == 'MIX_SHADER'
            ]
            for node in relevant_nodes:
                node.inputs[0].default_value = float(value)

    # Helper inline function to set the footage projection (fade) to a given value
    def set_footage_fade(value):
        if material and material.use_nodes:
            node_tree = material.node_tree
            target_node = node_tree.nodes.get("ff_fluidsurface_projection")
            if target_node:
                blend_input = target_node.inputs[0]
                if blend_input:
                    blend_input.default_value = float(value)

    if self.render_passes_toggle_findreflections:
        # User turned "Find Reflections" ON
        self.render_passes_findreflections_previousfade = hprops.render_passes_blend_footage_to_fluidsurface

        # 1) onlyreflections => 1.0
        set_mix_shader_fac("ff_onlyreflections", 1.0)
        # 2) transparent_or_holdout => 1.0
        set_mix_shader_fac("ff_transparent_or_holdout", 1.0)
        # 3) set the footage projection (fade) to 0.0
        set_footage_fade(0.0)

        # Enable compositing
        bpy.context.scene.render.use_compositing = True

    else:
        # User turned "Find Reflections" OFF

        # 1) onlyreflections => 0.0
        set_mix_shader_fac("ff_onlyreflections", 0.0)
        # 2) transparent_or_holdout => 0.0
        set_mix_shader_fac("ff_transparent_or_holdout", 0.0)
        # 3) restore the fade value
        set_footage_fade(self.render_passes_findreflections_previousfade)

        # Disable compositing
        bpy.context.scene.render.use_compositing = False

def get_default_findreflections_previousfade():
    return 0.0


# Object List for Passes Rendering:
class FlipFluidHelperPropertiesRenderPassesObjectslist(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    data_name: bpy.props.StringProperty(name="Data Name")
    fg_elements: bpy.props.BoolProperty(
        name="fg_elements",
        description="Object will be used as foreground element",
        default=False
    )
    bg_elements: bpy.props.BoolProperty(
        name="bg_elements",
        description="Object will be used as background element",
        default=False
    )
    ref_elements: bpy.props.BoolProperty(
        name="ref_elements",
        description="Object will be used for reflections",
        default=False
    )
    ground: bpy.props.BoolProperty(
        name="Ground",
        description="Object will be used as ground",
        default=False
    )
    assigned_node: bpy.props.StringProperty(
        name="Assigned Node",
        description="Name of the assigned Object Info Node",
        default=""
    )


# Dictionary to save Objects, Material, Fader Objects:
class FlipFluidHelperPropertiesRenderPassesFaderobjectsDICT(bpy.types.PropertyGroup):
    obj_name: bpy.props.StringProperty(name="Object Name")
    material_name: bpy.props.StringProperty(name="Material Name")
    original_materialname: bpy.props.StringProperty(name="Original Material Name")
    node_object: bpy.props.PointerProperty(name="FADER Object", type=bpy.types.Object)
    projectionnode_object: bpy.props.PointerProperty(name="Projection FADER Object", type=bpy.types.Object)

# Dictionary to save ALL Objects an Material:
class FlipFluidHelperPropertiesRenderPassesAllObjectsMaterialsDICT(bpy.types.PropertyGroup): 
    obj_name: bpy.props.StringProperty(name="Object Name")
    original_objectname: bpy.props.StringProperty(name="Original Object Name")
    material_name: bpy.props.StringProperty(name="Material Name")
    original_materialname: bpy.props.StringProperty(name="Original Material Name")
    node_object: bpy.props.PointerProperty(name="FADER Object", type=bpy.types.Object)

# Dictionary to save ALL Objects for 2.5D scenes
class FlipFluidHelperPropertiesRenderPassesImportMediaDICT(bpy.types.PropertyGroup):
    file_name: StringProperty(name="File Name")
    texture_name: StringProperty(name="Texture Name")
    object_name: StringProperty(name="Object Name")

# To save shadowcatcher-states
class FlipFluidHelperPropertiesShadowCatcherState(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Object Name",
        description="Name of the object for which the shadow catcher state is stored"
    )
    is_shadow_catcher: bpy.props.BoolProperty(
        name="Shadow Catcher State",
        description="Stores the shadow catcher state of the object",
        default=False
    )


# Properties:
class FlipFluidHelperProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    option_path_supports_blend_relative = set()
    if vcu.is_blender_45():
        # required for relative path support in Blender 4.5+
        # https://docs.blender.org/api/4.5/bpy_types_enum_items/property_flag_items.html#rna-enum-property-flag-items
        option_path_supports_blend_relative = {'PATH_SUPPORTS_BLEND_RELATIVE'}

    enable_auto_frame_load = BoolProperty(
            name="Auto-Load Baked Frames",
            description="Automatically load frames as they finish baking",
            default=False,
            update=lambda self, context: self._update_enable_auto_frame_load_cmd(context),
            ); exec(conv("enable_auto_frame_load"))
    enable_auto_frame_load_cmd = BoolProperty(
            name="Sync With CMD Bake",
            description="Automatically load frames as they finish baking when running a command"
                " line bake. Note: this feature may decrease Blender performance and responsiveness"
                " when a CMD bake is not running. If this is an issue, it is recommended to disable"
                " this option when a CMD bake is not running",
            default=False,
            update=lambda self, context: self._update_enable_auto_frame_load_cmd(context),
            ); exec(conv("enable_auto_frame_load_cmd"))
    playback_frame_offset = IntProperty(
            name="Frame Offset",
            description="Frame offset for simulation playback. A positive offset will shift simulation playback forwards in the timeline while a negative offset will shift playback backwards in the timeline",
            default=0,
            options={'HIDDEN'},
            ); exec(conv("playback_frame_offset"))

    cmd_bake_and_render = BoolProperty(
            name="Bake and Render",
            description="Enable both baking and rendering in the command line process",
            default=False,
            ); exec(conv("cmd_bake_and_render"))
    cmd_bake_and_render_mode = EnumProperty(
            name="CMD Bake and Render Mode",
            description="How to bake and render the simulation",
            items=types.cmd_bake_and_render_mode,
            default='CMD_BAKE_AND_RENDER_MODE_SEQUENCE',
            options={'HIDDEN'},
            ); exec(conv("cmd_bake_and_render_mode"))
    cmd_bake_and_render_interleaved_instances = IntProperty(
            name="Render Instances",
            description="Maximum number of render instances to run simultaneously. This number is how many frames"
                " are allowed to be rendered at the same time. More render instances maximizes system resource usage"
                " if the simulation is running faster than the render but will require more RAM and also VRAM if"
                " rendering on the GPU",
            default=1,
            min=1,
            soft_max=8,
            options={'HIDDEN'},
            ); exec(conv("cmd_bake_and_render_interleaved_instances"))
    cmd_bake_and_render_interleaved_no_overwrite = BoolProperty(
            name="Continue render from last rendered frame",
            description="Skip rendering frames that already exist in the render output directory. Useful for continuing a render from the last completed frame. If disabled, rendered frames will be overwritten",
            default=True,
            ); exec(conv("cmd_bake_and_render_interleaved_no_overwrite"))
    cmd_launch_render_animation_mode = EnumProperty(
            name="Animation Render Mode",
            description="How to render the animation",
            items=types.cmd_render_animation_mode,
            default='CMD_RENDER_MODE_NORMAL',
            options={'HIDDEN'},
            ); exec(conv("cmd_launch_render_animation_mode"))
    cmd_launch_render_passes_animation_mode = EnumProperty(
            name="Animation Render Mode",
            description="How to render the compositing tools render passes animation",
            items=types.cmd_render_passes_animation_mode,
            default='CMD_RENDER_MODE_RENDER_PASSES',
            options={'HIDDEN'},
            ); exec(conv("cmd_launch_render_passes_animation_mode"))
    cmd_launch_render_normal_animation_no_overwrite = BoolProperty(
            name="Skip rendered frames",
            description="Skip rendering frames that already exist in the render output directory. Useful for continuing a render from the last completed frame. If disabled, rendered frames will be overwritten",
            default=False,
            ); exec(conv("cmd_launch_render_normal_animation_no_overwrite"))
    cmd_launch_render_animation_no_overwrite = BoolProperty(
            name="Skip rendered frames",
            description="Skip rendering frames that already exist in the render output directory. Useful for continuing a render from the last completed frame. If disabled, rendered frames will be overwritten",
            default=True,
            ); exec(conv("cmd_launch_render_animation_no_overwrite"))
    cmd_launch_render_passes_animation_no_overwrite = BoolProperty(
            name="Skip rendered frames",
            description="Skip rendering compositing pass frames that already exist in the render output directory. Useful for continuing a render from the last completed compositing pass frame. If disabled, rendered frames will be overwritten",
            default=True,
            ); exec(conv("cmd_launch_render_passes_animation_no_overwrite"))
    cmd_launch_render_animation_instances = IntProperty(
            name="Render Instances",
            description="Maximum number of render instances to run simultaneously. This number is how many frames"
                " are allowed to be rendered at the same time. More render instances maximizes system resource usage"
                " but will require more RAM and also VRAM if rendering on the GPU",
            default=2,
            min=1,
            soft_max=8,
            options={'HIDDEN'},
            ); exec(conv("cmd_launch_render_animation_instances"))
    cmd_launch_render_passes_animation_instances = IntProperty(
            name="Render Instances",
            description="Maximum number of render instances to run simultaneously. This number is how many compositing pass frames"
                " are allowed to be rendered at the same time. More render instances maximizes system resource usage"
                " but will require more RAM and also VRAM if rendering on the GPU",
            default=1,
            min=1,
            soft_max=8,
            options={'HIDDEN'},
            ); exec(conv("cmd_launch_render_passes_animation_instances"))
    cmd_open_image_after_render = BoolProperty(
            name="Open Image After Render",
            description="After the command line render process is finished, open the image in your default OS image program",
            default=True,
            ); exec(conv("cmd_open_image_after_render"))
    cmd_close_window_after_render = BoolProperty(
            name="Close CMD Window After Render",
            description="After the command line render process is finished, open the image in your default OS image program",
            default=False,
            ); exec(conv("cmd_close_window_after_render"))
            

    ### NEW RENDER PASSES ###

    # Disabled by default for the release of FLIP Fluids 1.8.0
    display_compositing_tools_in_ui = BoolProperty(default=False); exec(conv("display_compositing_tools_in_ui"))
   
    render_passes = BoolProperty(
            name="Activate Passes Rendering",
            description="Activate rendering of selected passes",
            default=False
            ); exec(conv("render_passes"))
        
    render_passes_objectlist: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesObjectslist)
    render_passes_fg_elementslist: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesObjectslist)
    render_passes_bg_elementslist: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesObjectslist)
    render_passes_ref_elementslist: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesObjectslist)
    render_passes_groundlist: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesObjectslist)
    render_passes_import_media: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesImportMediaDICT)
    render_passes_objectlist_index: bpy.props.IntProperty()
    render_passes_fg_elementslist_index: bpy.props.IntProperty()
    render_passes_bg_elementslist_index: bpy.props.IntProperty()
    render_passes_ref_elementslist_index: bpy.props.IntProperty()
    render_passes_groundlist_index: bpy.props.IntProperty()
        
    def get_camera_items(self, context):
        return [(cam.name, cam.name, "") for cam in bpy.data.objects if cam.type == 'CAMERA']
      
    render_passes_initialized: bpy.props.BoolProperty(
        name="Render Passes Initialized",
        description="Indicates whether compositing tools have been initialized",
        default=False
    )

    render_passes_fluid_only: bpy.props.BoolProperty(
        name="Fluid Surface",
        description="Only the fluid_surface",
        default=False,
        update=update_render_pass_property_and_availability
    )
    
    render_passes_fluidparticles_only: bpy.props.BoolProperty(
        name="Fluid Particles",
        description="Only the fluidparticles with reflections from the background only",
        default=False,
        update=update_render_pass_property_and_availability
    )

    render_passes_fluid_shadows_only: bpy.props.BoolProperty(
        name="Fluid Surface Shadows",
        description="Only the Shadow of the fluid_surface",
        default=False,
        update=update_render_pass_property_and_availability
    )    

    render_passes_reflr_only: bpy.props.BoolProperty(
        name="Reflections & Refractions",
        description="Only reflections and refractions",
        default=False,
        update=update_render_pass_property_and_availability
    )

    render_passes_objects_only: bpy.props.BoolProperty(
        name="Objects",
        description="Only visible objects",
        default=False,
        update=update_render_pass_property_and_availability
    )
    
    render_passes_elements_only: bpy.props.BoolProperty(
        name="Elements",
        description="Only Fore- and Background and Reflective Elements",
        default=False,
        update=update_render_pass_property_and_availability
    )

    render_passes_object_shadows_only: bpy.props.BoolProperty(
        name="Object Shadows",
        description="Only the shadows of visible objects",
        default=False,
        update=update_render_pass_property_and_availability
    )       
 
    render_passes_bubblesanddust_only: bpy.props.BoolProperty(
        name="Bubbles & Dust",
        description="Bubbles And Dust Only",
        default=False,
        update=update_render_pass_property_and_availability
    )    
 
    render_passes_foamandspray_only: bpy.props.BoolProperty(
        name="Foam & Spray",
        description="Foam And Spray Only",
        default=False,
        update=update_render_pass_property_and_availability
    )    
    

    render_passes_is_any_pass_enabled: bpy.props.BoolProperty(
        name="Any pass",
        description="Makes sure, that any pass is enabled for rendering",
        default=False
    )    
    

    render_passes_cameraselection: bpy.props.EnumProperty(
        items=get_camera_items,
        name="Camera Selection",
        description="Select a camera for rendering"
    )
    
    render_passes_camerascreen_distance: bpy.props.FloatProperty(
        name="CameraScreen Distance",
        description="Controls the distance to the selected camera",
        default=50.0,
        min=1.0,
        max=10000.0,
        update=_update_render_passes_camera_screen
    )
    
    render_passes_camerascreen_visibility: bpy.props.BoolProperty(
        name="CameraScreen Visibility",
        description="Quick enable/disable ff_camera_screen viewport visibility",
        default=True,
        update=update_camerascreen_visibility
    )
    
    render_passes_stillimagemode_toggle: bpy.props.BoolProperty(
        name="Still Image Mode",
        description="Toggle to enable or disable still image mode",
        default=False,
        update=still_image_mode_updated  # Trigger the callback
    )

    render_passes_alignmentgrid_visibility: bpy.props.BoolProperty(
        name="Alignment Grid Visibility",
        description="Quick enable/disable ff_alignment_grid viewport visibility",
        default=True,
        update=update_alignmentgrid_visibility
    )

    render_passes_shadowcatcher_state: bpy.props.CollectionProperty(
        name="Shadow Catcher States",
        description="Stores shadow catcher states for multiple objects",
        type=FlipFluidHelperPropertiesShadowCatcherState
    )
       
    ### FADING: 
    render_passes_faderobjects_visibility: bpy.props.BoolProperty(
        name="Fader Objects Visibility",
        description="Quick enable/disable fader objects viewport visibility",
        default=True,
        update=update_faderobjects_visibility
    ) 

    render_passes_faderobjectnames_visibility: bpy.props.BoolProperty(
        name="Fader Object Names Visibility",
        description="Quick enable/disable fader object names viewport visibility",
        default=False,
        update=update_faderobjectnames_visibility
    )   
    
    render_passes_objectnames_visibility: bpy.props.BoolProperty(
        name="Object Names Visibility",
        description="Quick enable/disable object names viewport visibility",
        default=True,
        update=update_objectnames_visibility
    )

    render_passes_toggle_fader_fluidsurface: bpy.props.BoolProperty(
        name="Fade fluid_surface using Fader",
        description="Toggle fading for fluid_surface using Fader",
        default=False,
        update=update_fader_fluidsurface_toggle
    )
    
    render_passes_toggle_speed_fluidsurface: bpy.props.BoolProperty(
        name="Fade fluid_surface using Speed",
        description="Toggle fading for fluid_surface using Speed Attribute",
        default=False,
        update=update_speed_fluidsurface_toggle
    )

    render_passes_toggle_domain_fluidsurface: bpy.props.BoolProperty(
        name="Fade fluid_surface using Domain Boundaries",
        description="Toggle fading for fluid_surface using Domain Boundaries",
        default=False,
        update=update_domain_fluidsurface_toggle
    )

    render_passes_has_unflagged_objects: bpy.props.BoolProperty(
        name="Has Unflagged Objects",
        description="Indicates if there are objects in the list without any flags.",
        default=False
    )

    render_passes_fader_combination_fluidsurface: bpy.props.IntProperty(
        name="Fader Combination for fluid_surface",
        description="Combined value of Fader toggles for fluid_surface",
        default=0
    )

    render_passes_blend_footage_to_fluidsurface: bpy.props.FloatProperty(
        name="Slider to blend footage to the fluid_surface",
        description="Controls mix slider in material to blend footage to the fluid_surface",
        default=0,
        min=0.0,
        max=1.0,
        step=0.1,
        update=update_blend_footage
    )

    render_passes_blend_normalmap_to_fluidsurface: bpy.props.FloatProperty(
        name="Slider to blend normalmap to the fluid_surface",
        description="Controls strength slider in material to blend normalmap to the fluid_surface",
        default=0,
        min=0.0,
        max=1.0,
        step=0.1,
        update=update_blend_normalmap
    )

    render_passes_toggle_velocity_fluidsurface: bpy.props.BoolProperty(
        name="Enable velocity-based fading for blended footage",
        description="Controls nodes in material to show velocity",
        default=False,
        update=update_velocity_fluidsurface_toggle
    )

    render_passes_last_velocity_state: bpy.props.BoolProperty(
        name="Last Velocity State",
        description="Stores the last state of the velocity toggle when speed is turned off",
        default=False
    )

    render_passes_toggle_velocity_invert: bpy.props.BoolProperty(
        name="Invert Velocity",
        description="Invert velocity-based fading for blended footage",
        default=False,
        update=update_velocity_invert_toggle
    )

    render_passes_toggle_projectiontester: bpy.props.BoolProperty(
        name="Show a testcolor",
        description="Controls nodes in material to show a testcolor",
        default=False,
        update=update_testcolor_toggle
    )

    render_passes_toggle_projectionfader: bpy.props.BoolProperty(
        name="Fade blended footage",
        description="Controls nodes in material to fade blended footage",
        default=False,
        update=update_projectionfader_toggle
    )

    render_passes_show_fader_details: BoolProperty(
        name="Fader Details",
        description="Show or hide the ColorRamp settings for fading",
        default=False
    )

    render_passes_object_fading_width: FloatProperty(
        name="Object-Based Fading Width",
        description="Controls the object-based fading width for all specified objects",
        default=1.0,
        min=0.1,
        max=10.0,
        step=0.1,
        update=update_object_fading_width
    )

    render_passes_object_fading_softness: FloatProperty(
        name="Object-Based Fading Softness",
        description="Controls the softness of the object-based fading for all specified objects",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.1,
        update=update_object_fading_width
    )

    render_passes_object_fading_width_fluid_surface: FloatProperty(
        name="Object-Based Fading Width",
        description="Controls the object-based fading width for all specified objects",
        default=1.0,
        min=0.1,
        max=10.0,
        step=0.1,
        update=update_object_fading_width_fluid_surface
    )

    render_passes_object_fading_softness_fluid_surface: FloatProperty(
        name="Object-Based Fading Softness",
        description="Controls the softness of the object-based fading for all specified objects",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.1,
        update=update_object_fading_width_fluid_surface
    )


    render_passes_general_fading_width: FloatProperty(
        name="General Fading Width",
        description="Controls the general fading width for all specified objects",
        default=1.0,
        min=0.1,
        max=10.0,
        step=0.1,
        update=update_general_fading_width
    )


    render_passes_toggle_findreflections: BoolProperty(
        name="Find Reflections",
        description="Enable reflection-specific preview in the material (similar to reflr_only pass)",
        default=False,
        update=update_findreflections_toggle
    )

    render_passes_findreflections_previousfade: FloatProperty(
        name="Previous fade value for reflections",
        description="Stores the original fade value before enabling 'Find Reflections'",
        default=0.0
    )


    # Fader Dict:
    render_passes_faderobjects_DICT: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesFaderobjectsDICT)
    # All Objects Dict:
    render_passes_all_objects_materials_DICT: bpy.props.CollectionProperty(type=FlipFluidHelperPropertiesRenderPassesAllObjectsMaterialsDICT)
 
    ### END OF PASSES ###

    alembic_export_surface = BoolProperty(
            name="Surface",
            description="Include fluid surface mesh in the Alembic export",
            default=True,
            ); exec(conv("alembic_export_surface"))
    alembic_export_fluid_particles = BoolProperty(
            name="Fluid Particles",
            description="Include fluid particles in the Alembic export",
            default=False,
            ); exec(conv("alembic_export_fluid_particles"))
    alembic_export_foam = BoolProperty(
            name="Foam",
            description="Include whitewater foam mesh in the Alembic export if applicable. This mesh will be exported as a vertex-only mesh",
            default=True,
            ); exec(conv("alembic_export_foam"))
    alembic_export_bubble = BoolProperty(
            name="Bubble",
            description="Include whitewater bubble mesh in the Alembic export if applicable. This mesh will be exported as a vertex-only mesh",
            default=True,
            ); exec(conv("alembic_export_bubble"))
    alembic_export_spray = BoolProperty(
            name="Spray",
            description="Include whitewater spray mesh in the Alembic export if applicable. This mesh will be exported as a vertex-only mesh",
            default=True,
            ); exec(conv("alembic_export_spray"))
    alembic_export_dust = BoolProperty(
            name="Dust",
            description="Include whitewater dust mesh in the Alembic export if applicable. This mesh will be exported as a vertex-only mesh",
            default=True,
            ); exec(conv("alembic_export_dust"))
    alembic_export_velocity = BoolProperty(
            name="Export Velocity",
            description="Include velocity data in the Alembic export. This data will be available"
                " under the 'velocity' point attribute of the Alembic export and can be used for motion"
                " blur rendering. Velocity attributes for the surface, fluid particles, and/or whitewater are required to"
                " be baked before export",
            default=False,
            ); exec(conv("alembic_export_velocity"))
    alembic_export_color = BoolProperty(
            name="Export Color",
            description="Include color attribute data in the Alembic export. This data will be available"
                " under the 'color' face-corner attribute of the Alembic export and can be used for material shading."
                " This attribute is only supported for the Surface mesh."
                " Color attributes for the surface are required to be baked before export",
            default=False,
            ); exec(conv("alembic_export_color"))
    alembic_global_scale = FloatProperty(
            name="Scale", 
            description="Scale value by which to enlarge or shrink the simulation meshes with respect to the world's origin", 
            min=0.0001,
            max=1000.0,
            default=1.0,
            precision=3,
            ); exec(conv("alembic_global_scale"))
    alembic_frame_range_mode = EnumProperty(
            name="Frame Range Mode",
            description="Frame range to use for Alembic Export",
            items=types.frame_range_modes,
            default='FRAME_RANGE_TIMELINE',
            options={'HIDDEN'},
            ); exec(conv("alembic_frame_range_mode"))
    alembic_frame_range_custom = NewMinMaxIntProperty(
            name_min="Start Frame", 
            description_min="First frame of the Alembic export", 
            min_min=0,
            default_min=1,
            options_min={'HIDDEN'},

            name_max="End Frame", 
            description_max="Final frame of the Alembic export", 
            min_max=0,
            default_max=250,
            options_max={'HIDDEN'},
            ); exec(conv("alembic_frame_range_custom"))
    alembic_output_filepath = StringProperty(
            name="",
            description="Alembic export will be saved to this filepath. Remember to save the Blend file before"
                " starting the Alembic export",
            default="//untitled.abc", 
            subtype='FILE_PATH',
            options=option_path_supports_blend_relative,
            update=lambda self, context: self._update_alembic_output_filepath(context),
            ); exec(conv("alembic_output_filepath"))
    is_alembic_output_filepath_set = BoolProperty(default=False); exec(conv("is_alembic_output_filepath_set"))

    unsaved_blend_file_tooltip = BoolProperty(
            name="Unsaved Blend File Tooltip", 
            description="This is currently an unsaved .blend file. We recommend saving your file before baking a"
                " simulation so you do not accidentally lose your simulation progress or settings", 
            default=True,
            ); exec(conv("unsaved_blend_file_tooltip"))

    turbo_tools_render_tooltip = BoolProperty(
            name="Turbo Tools command line rendering support", 
            description="An installation of the Turbo Tools addon has been detected. Use these operators to launch"
                " a Turbo Tools render process or copy the render command. Refer to the Turbo Tools documentation for more info"
                " on command line rendering", 
            default=True,
            ); exec(conv("turbo_tools_render_tooltip"))

    flip_fluids_remesh_skip_hide_render_objects = BoolProperty(
            name="Skip Hidden Render Objects",
            description="Skip remeshing objects in the collection that are hidden from render (outliner camera icon)",
            default=False,
            ); exec(conv("flip_fluids_remesh_skip_hide_render_objects"))
    flip_fluids_remesh_apply_object_modifiers = BoolProperty(
            name="Apply Object Modifiers",
            description="Automatically apply modifiers to objects in collection. If disabled, objects with modifiers will"
                " need to have modifiers applied manually or excluded from the viewport (disable outliner monitor icon)"
                " before proceeding with the remesh process. Modifiers may not be applied in the intended order and objects"
                " with complex modifier dependencies may need to be applied manually for accuracy",
            default=True,
            ); exec(conv("flip_fluids_remesh_apply_object_modifiers"))
    flip_fluids_remesh_convert_objects_to_mesh = BoolProperty(
            name="Convert Objects to Mesh",
            description="Automatically convert non-mesh type objects in the collection to a mesh type if applicable. If an object cannot"
                " be converted to a mesh (empties, armatures, etc), the object will be skipped from the remeshing process."
                " If disabled, non-mesh type objects will need to be manually converted to a mesh or excluded from the viewport"
                " (disable outliner monitor icon) before proceeding with the remesh process",
            default=True,
            ); exec(conv("flip_fluids_remesh_convert_objects_to_mesh"))
    update_object_speed_data_on_frame_change = BoolProperty(
            name="Update on frame change",
            description="Update the object speed measurement for the active object after changing a frame. Not recommended"
            " to leave this option enabled when not in use as this could slow down Blender when measuring complex or high poly geometry",
            default=False,
            ); exec(conv("update_object_speed_data_on_frame_change"))
    measure_object_speed_units_mode = EnumProperty(
            name="Measurement Units",
            description="Display speed in metric or imperial units",
            items=types.measurement_units_mode,
            default='MEASUREMENT_UNITS_MODE_METRIC',
            options={'HIDDEN'},
            ); exec(conv("measure_object_speed_units_mode"))

    disable_addon_in_blend_file = BoolProperty(
            name="Disable Addon in Blend File",
            description="",
            default=False,
            ); exec(conv("disable_addon_in_blend_file"))

    is_auto_frame_load_cmd_operator_running = BoolProperty(default=False); exec(conv("is_auto_frame_load_cmd_operator_running"))

    export_animated_mesh_parent_tooltip = BoolProperty(
            name="Hint: Export Animated Mesh", 
            description="A parented relation has been detected on this object. If this object"
                " is moving, enabling the 'Export Animated Mesh' option is required to evaluate"
                " parented relationships for the simulator. This option is needed for any object"
                " animation that is more complex than keyframed loc/rot/scale such as parented objects."
                " If the object is static, keep this option disabled", 
            default=True,
            ); exec(conv("export_animated_mesh_parent_tooltip"))

    # Used in Helper Operators > FlipFluidMeasureObjectSpeed operator
    is_translation_data_available = BoolProperty(default=False); exec(conv("is_translation_data_available"))
    min_vertex_translation = FloatProperty(default=0.0); exec(conv("min_vertex_translation"))
    max_vertex_translation = FloatProperty(default=0.0); exec(conv("max_vertex_translation"))
    avg_vertex_translation = FloatProperty(default=0.0); exec(conv("avg_vertex_translation"))
    center_translation = FloatProperty(default=0.0); exec(conv("center_translation"))
    translation_data_object_name = StringProperty(default="Name Not Available"); exec(conv("translation_data_object_name"))
    translation_data_object_vertices = IntProperty(default=-1); exec(conv("translation_data_object_vertices"))
    translation_data_object_frame = IntProperty(default=-1); exec(conv("translation_data_object_frame"))
    translation_data_object_compute_time = IntProperty(default=-1); exec(conv("translation_data_object_compute_time"))

    prepare_geometry_tools_expanded = BoolProperty(default=False); exec(conv("prepare_geometry_tools_expanded"))
    bake_simulation_expanded = BoolProperty(default=True); exec(conv("bake_simulation_expanded"))
    add_remove_objects_expanded = BoolProperty(default=False); exec(conv("add_remove_objects_expanded"))
    outliner_organization_expanded = BoolProperty(default=False); exec(conv("outliner_organization_expanded"))
    quick_select_expanded = BoolProperty(default=False); exec(conv("quick_select_expanded"))

    command_line_tools_expanded = BoolProperty(default=True); exec(conv("command_line_tools_expanded"))
    command_line_bake_expanded = BoolProperty(default=False); exec(conv("command_line_bake_expanded"))
    command_line_render_passes_expanded = BoolProperty(default=False); exec(conv("command_line_render_passes_expanded"))
    command_line_render_expanded = BoolProperty(default=False); exec(conv("command_line_render_expanded"))
    command_line_render_frame_expanded = BoolProperty(default=False); exec(conv("command_line_render_frame_expanded"))
    command_line_render_turbo_tools_expanded  = BoolProperty(default=False); exec(conv("command_line_render_turbo_tools_expanded"))
    command_line_alembic_export_expanded = BoolProperty(default=False); exec(conv("command_line_alembic_export_expanded"))

    geometry_node_tools_expanded = BoolProperty(default=False); exec(conv("geometry_node_tools_expanded"))
    object_speed_measurement_tools_expanded = BoolProperty(default=False); exec(conv("object_speed_measurement_tools_expanded"))
    beginner_tools_expanded = BoolProperty(default=False); exec(conv("beginner_tools_expanded"))
    disable_addon_expanded = BoolProperty(default=False); exec(conv("disable_addon_expanded"))

    quick_viewport_display_expanded = BoolProperty(default=True); exec(conv("quick_viewport_display_expanded"))
    simulation_playback_expanded = BoolProperty(default=False); exec(conv("simulation_playback_expanded"))
    render_tools_expanded = BoolProperty(default=False); exec(conv("render_tools_expanded"))


    @classmethod
    def register(cls):
        bpy.types.Scene.flip_fluid_helper = PointerProperty(
                name="Flip Fluid Helper Properties",
                description="",
                type=cls,
                )


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.flip_fluid_helper


    def load_post(self):
        self.is_auto_frame_load_cmd_operator_running = False
        is_background_mode = bpy.app.background
        if self.is_auto_frame_load_cmd_enabled() and not is_background_mode:
            bpy.ops.flip_fluid_operators.auto_load_baked_frames_cmd('INVOKE_DEFAULT')

        self.check_alembic_output_filepath()


    def scene_update_post(self, scene):
        _update_render_passes_camera_screen(self, bpy.context)


    def save_post(self):
        self.check_alembic_output_filepath()


    def frame_change_post(self, scene, depsgraph=None):
        if self.update_object_speed_data_on_frame_change:
            try:
                if bpy.ops.flip_fluid_operators.measure_object_speed.poll():
                    print_render_pass_debug("Measure Object Speed: Update on frame change option is enabled.")
                    bpy.ops.flip_fluid_operators.measure_object_speed('INVOKE_DEFAULT')
                else:
                    bpy.ops.flip_fluid_operators.clear_measure_object_speed('INVOKE_DEFAULT')
            except:
                pass


    def is_addon_disabled_in_blend_file(self):
        is_disabled = False
        for scene in bpy.data.scenes:
            is_disabled = is_disabled or scene.flip_fluid_helper.disable_addon_in_blend_file
        return is_disabled


    def get_addon_preferences(self):
        return vcu.get_addon_preferences()


    def frame_complete_callback(self):
        prefs = self.get_addon_preferences()
        if prefs.enable_helper and self.enable_auto_frame_load:
            bpy.ops.flip_fluid_operators.helper_load_last_frame()


    def is_auto_frame_load_cmd_enabled(self):
        return self.enable_auto_frame_load and self.enable_auto_frame_load_cmd


    def _update_enable_auto_frame_load_cmd(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        is_auto_load_cmd_enabled = self.is_auto_frame_load_cmd_enabled()
        is_background_mode = bpy.app.background
        if is_auto_load_cmd_enabled and not self.is_auto_frame_load_cmd_operator_running and not is_background_mode:
            bpy.ops.flip_fluid_operators.auto_load_baked_frames_cmd('INVOKE_DEFAULT')


    def _update_alembic_output_filepath(self, context):
        self.is_alembic_output_filepath_set = True

        relprefix = "//"
        if self.alembic_output_filepath == "" or self.alembic_output_filepath == relprefix:
            # Don't want the user to set an empty path
            if bpy.data.filepath:
                base = os.path.basename(bpy.data.filepath)
                save_file = os.path.splitext(base)[0]
                output_folder_parent = os.path.dirname(bpy.data.filepath)

                output_filepath = os.path.join(output_folder_parent, save_file + ".abc")
                relpath = os.path.relpath(output_filepath, output_folder_parent)

                default_cache_directory_str = relprefix + relpath
            else:
                temp_directory = vcu.get_blender_preferences_temporary_directory()
                default_cache_directory_str = os.path.join(temp_directory, "untitled.abc")
            self["alembic_output_filepath"] = default_cache_directory_str


    def check_alembic_output_filepath(self):
        if self.is_alembic_output_filepath_set:
            return

        base = os.path.basename(bpy.data.filepath)
        save_file = os.path.splitext(base)[0]
        if not save_file:
            save_file = "untitled"
            self.alembic_output_filepath = save_file + ".abc"
            self.is_alembic_output_filepath_set = False
            return

        alembic_folder_parent = os.path.dirname(bpy.data.filepath)
        alembic_path = os.path.join(alembic_folder_parent, save_file + ".abc")
        relpath = os.path.relpath(alembic_path, alembic_folder_parent)

        relprefix = "//"
        self.alembic_output_filepath = relprefix + relpath
        self.is_alembic_output_filepath_set = True


    def get_alembic_output_abspath(self):
        relprefix = "//"
        path_prop = self.alembic_output_filepath
        path = self.alembic_output_filepath
        if path_prop.startswith(relprefix):
            path_prop = path_prop[len(relprefix):]
            blend_directory = os.path.dirname(bpy.data.filepath)
            path = os.path.join(blend_directory, path_prop)
        path = os.path.abspath(os.path.normpath(path))
        if platform.system() != "Windows":
            # Blend file may have been saved on windows and opened on macOS/Linux. In this case,
            # backslash should be converted to forward slash.
            path = os.path.join(*path.split("\\"))
        return path


def load_post():
    bpy.context.scene.flip_fluid_helper.load_post()


def scene_update_post(scene):
    scene.flip_fluid_helper.scene_update_post(scene)


def frame_change_post(scene, depsgraph=None):
    global DISABLE_FRAME_CHANGE_POST_HANDLER
    if DISABLE_FRAME_CHANGE_POST_HANDLER:
        return
    bpy.context.scene.flip_fluid_helper.frame_change_post(scene, depsgraph)


def save_post():
    bpy.context.scene.flip_fluid_helper.save_post()


def register():
    bpy.utils.register_class(FlipFluidHelperPropertiesRenderPassesObjectslist)
    bpy.utils.register_class(FlipFluidHelperPropertiesRenderPassesFaderobjectsDICT)
    bpy.utils.register_class(FlipFluidHelperPropertiesRenderPassesAllObjectsMaterialsDICT)
    bpy.utils.register_class(FlipFluidHelperPropertiesRenderPassesImportMediaDICT)
    bpy.utils.register_class(FlipFluidHelperPropertiesShadowCatcherState)
    bpy.utils.register_class(FlipFluidHelperProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperPropertiesRenderPassesObjectslist)
    bpy.utils.unregister_class(FlipFluidHelperPropertiesRenderPassesFaderobjectsDICT)
    bpy.utils.unregister_class(FlipFluidHelperPropertiesRenderPassesAllObjectsMaterialsDICT)
    bpy.utils.unregister_class(FlipFluidHelperPropertiesRenderPassesImportMediaDICT)
    bpy.utils.unregister_class(FlipFluidHelperPropertiesShadowCatcherState)
    bpy.utils.unregister_class(FlipFluidHelperProperties)
