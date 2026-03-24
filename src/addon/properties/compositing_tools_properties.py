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

import bpy
from bpy.props import (
        IntProperty,
        FloatProperty,
        StringProperty,
        BoolProperty,
        PointerProperty,
        EnumProperty
        )

from ..operators import compositing_tools_operators
from ..operators.compositing_tools_operators import print_render_pass_debug

DISABLE_FRAME_CHANGE_POST_HANDLER = False


# Compositing:
def _update_render_passes_camera_screen(self, context):
    cprops = context.scene.flip_fluid_compositing_tools

    # Retrieve the camera screen object
    bl_camera_screen = bpy.data.objects.get("ff_camera_screen")
    if bl_camera_screen is None:
        #print_render_pass_debug("Camera screen not found.")
        return

    # Retrieve the camera object
    bl_camera = bpy.data.objects.get(cprops.render_passes_cameraselection)
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
    compositing_tools_operators.update_camera_screen_scale(
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
    
    cprops = context.scene.flip_fluid_compositing_tools

    # Hole das FLIP Fluids Domain-Objekt, falls vorhanden
    domain = context.scene.flip_fluid.get_domain_object()

    # Fluid Surface nur wenn "fluid_surface" existiert
    if "fluid_surface" not in bpy.data.objects and cprops.render_passes_fluid_only:
        cprops.render_passes_fluid_only = False

    # Objects nur wenn ungetaggte Objekte existieren
    if not cprops.render_passes_has_unflagged_objects and cprops.render_passes_objects_only:
        cprops.render_passes_objects_only = False

    # Elements nur wenn mindestens ein Objekt FG, BG oder REF hat
    has_elements = any(
        item.fg_elements or item.bg_elements or item.ref_elements
        for item in cprops.render_passes_objectlist
    )
    if not has_elements and cprops.render_passes_elements_only:
        cprops.render_passes_elements_only = False

    # Fluid Particles nur wenn im Simulator aktiviert
    if domain and not domain.flip_fluid.domain.particles.enable_fluid_particle_output and cprops.render_passes_fluidparticles_only:
        cprops.render_passes_fluidparticles_only = False

    # Foam & Spray & Bubbles & Dust nur wenn WhiteWater aktiviert ist
    if domain and not domain.flip_fluid.domain.whitewater.enable_whitewater_simulation:
        if cprops.render_passes_foamandspray_only:
            cprops.render_passes_foamandspray_only = False
        if cprops.render_passes_bubblesanddust_only:
            cprops.render_passes_bubblesanddust_only = False


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
    # Store a reference to the Flip Fluid Compositing Tools properties
    cprops = context.scene.flip_fluid_compositing_tools

    # Save the current state of Velocity if Speed is being disabled
    if not cprops.render_passes_toggle_speed_fluidsurface:
        cprops.render_passes_last_velocity_state = cprops.render_passes_toggle_velocity_fluidsurface
        cprops.render_passes_toggle_velocity_fluidsurface = 0  # Disable Velocity when Speed is off

    # Restore the last saved state of Velocity if Speed is being enabled
    elif cprops.render_passes_toggle_speed_fluidsurface:
        cprops.render_passes_toggle_velocity_fluidsurface = cprops.render_passes_last_velocity_state

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
                    modifier["Socket_2"] = context.scene.flip_fluid_compositing_tools.render_passes_object_fading_width
                
                # Update Fading Softness (Socket_3)
                if "Socket_3" in modifier.keys():
                    modifier["Socket_3"] = context.scene.flip_fluid_compositing_tools.render_passes_object_fading_softness

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
                    modifier["Socket_2"] = context.scene.flip_fluid_compositing_tools.render_passes_object_fading_width_fluid_surface
                
                # Update Fading Softness (Socket_3)
                if "Socket_3" in modifier.keys():
                    modifier["Socket_3"] = context.scene.flip_fluid_compositing_tools.render_passes_object_fading_softness_fluid_surface

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
                    modifier["Socket_1"] = context.scene.flip_fluid_compositing_tools.render_passes_general_fading_width

                    modifier.show_viewport = False
                    modifier.show_viewport = True

    bpy.context.view_layer.update()


def update_findreflections_toggle(self, context):
    """When 'Find Reflections' is toggled, update the scene accordingly by modifying material node settings directly."""
    cprops = context.scene.flip_fluid_compositing_tools

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
        self.render_passes_findreflections_previousfade = cprops.render_passes_blend_footage_to_fluidsurface

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
class FFCompositingToolsPropertiesRenderPassesObjectslist(bpy.types.PropertyGroup):
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
class FFCompositingToolsPropertiesRenderPassesFaderobjectsDICT(bpy.types.PropertyGroup):
    obj_name: bpy.props.StringProperty(name="Object Name")
    material_name: bpy.props.StringProperty(name="Material Name")
    original_materialname: bpy.props.StringProperty(name="Original Material Name")
    node_object: bpy.props.PointerProperty(name="FADER Object", type=bpy.types.Object)
    projectionnode_object: bpy.props.PointerProperty(name="Projection FADER Object", type=bpy.types.Object)

# Dictionary to save ALL Objects an Material:
class FFCompositingToolsPropertiesRenderPassesAllObjectsMaterialsDICT(bpy.types.PropertyGroup): 
    obj_name: bpy.props.StringProperty(name="Object Name")
    original_objectname: bpy.props.StringProperty(name="Original Object Name")
    material_name: bpy.props.StringProperty(name="Material Name")
    original_materialname: bpy.props.StringProperty(name="Original Material Name")
    node_object: bpy.props.PointerProperty(name="FADER Object", type=bpy.types.Object)

# Dictionary to save ALL Objects for 2.5D scenes
class FFCompositingToolsPropertiesRenderPassesImportMediaDICT(bpy.types.PropertyGroup):
    file_name: StringProperty(name="File Name")
    texture_name: StringProperty(name="Texture Name")
    object_name: StringProperty(name="Object Name")

# To save shadowcatcher-states
class FFCompositingToolsPropertiesShadowCatcherState(bpy.types.PropertyGroup):
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
class FFCompositingToolsProperties(bpy.types.PropertyGroup):        

    ### NEW RENDER PASSES ###
   
    render_passes: BoolProperty(
            name="Activate Passes Rendering",
            description="Activate rendering of selected passes",
            default=False
            )
        
    render_passes_objectlist: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesObjectslist)
    render_passes_fg_elementslist: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesObjectslist)
    render_passes_bg_elementslist: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesObjectslist)
    render_passes_ref_elementslist: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesObjectslist)
    render_passes_groundlist: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesObjectslist)
    render_passes_import_media: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesImportMediaDICT)
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
        type=FFCompositingToolsPropertiesShadowCatcherState
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
    render_passes_faderobjects_DICT: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesFaderobjectsDICT)
    
    # All Objects Dict:
    render_passes_all_objects_materials_DICT: bpy.props.CollectionProperty(type=FFCompositingToolsPropertiesRenderPassesAllObjectsMaterialsDICT)
 
    ### END OF PASSES ###

    @classmethod
    def register(cls):
        bpy.types.Scene.flip_fluid_compositing_tools = PointerProperty(
                name="Flip Fluid Compositing Tools Properties",
                description="",
                type=cls,
                )


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.flip_fluid_compositing_tools


    def load_post(self):
        pass


    def scene_update_post(self, scene):
        _update_render_passes_camera_screen(self, bpy.context)


    def save_post(self):
        pass


    def frame_change_post(self, scene, depsgraph=None):
        pass


def load_post():
    bpy.context.scene.flip_fluid_compositing_tools.load_post()


def scene_update_post(scene):
    scene.flip_fluid_compositing_tools.scene_update_post(scene)


def frame_change_post(scene, depsgraph=None):
    global DISABLE_FRAME_CHANGE_POST_HANDLER
    if DISABLE_FRAME_CHANGE_POST_HANDLER:
        return
    bpy.context.scene.flip_fluid_compositing_tools.frame_change_post(scene, depsgraph)


def save_post():
    bpy.context.scene.flip_fluid_compositing_tools.save_post()


def register():
    bpy.utils.register_class(FFCompositingToolsPropertiesRenderPassesObjectslist)
    bpy.utils.register_class(FFCompositingToolsPropertiesRenderPassesFaderobjectsDICT)
    bpy.utils.register_class(FFCompositingToolsPropertiesRenderPassesAllObjectsMaterialsDICT)
    bpy.utils.register_class(FFCompositingToolsPropertiesRenderPassesImportMediaDICT)
    bpy.utils.register_class(FFCompositingToolsPropertiesShadowCatcherState)
    bpy.utils.register_class(FFCompositingToolsProperties)


def unregister():
    bpy.utils.unregister_class(FFCompositingToolsPropertiesRenderPassesObjectslist)
    bpy.utils.unregister_class(FFCompositingToolsPropertiesRenderPassesFaderobjectsDICT)
    bpy.utils.unregister_class(FFCompositingToolsPropertiesRenderPassesAllObjectsMaterialsDICT)
    bpy.utils.unregister_class(FFCompositingToolsPropertiesRenderPassesImportMediaDICT)
    bpy.utils.unregister_class(FFCompositingToolsPropertiesShadowCatcherState)
    bpy.utils.unregister_class(FFCompositingToolsProperties)
