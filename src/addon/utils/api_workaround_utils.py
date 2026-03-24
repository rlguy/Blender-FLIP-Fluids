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
from . import version_compatibility_utils as vcu
from .. import render


# Workaround for https://projects.blender.org/blender/blender/issues/71908
# This bug can cause keyframed parameters not to be evaluated during rendering
# when a frame_change handler is used.
#
# This workaround works by forcing an object to be evaluated and then setting
# the original object value to the evaluated values. This workaround can only
# be applied to Blender versions 2.81 and later.
def frame_change_post_apply_T71908_workaround(context, depsgraph=None):
    if not render.is_rendering():
        return

    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return

    # Apply to Domain render properties

    domain_object = context.scene.flip_fluid.get_domain_object()
    if depsgraph is None:
        depsgraph = context.evaluated_depsgraph_get()

    domain_object_eval = domain_object.evaluated_get(depsgraph)
    dprops_eval = domain_object_eval.flip_fluid.domain

    property_paths = dprops.property_registry.get_property_paths()
    render_paths = [p.split('.')[-1] for p in property_paths if p.startswith("domain.render")]
    for p in render_paths:
        setattr(dprops.render, p, getattr(dprops_eval.render, p))

    # Apply to FLIP Fluids sidebar
    dprops.render.override_frame = dprops_eval.render.override_frame

    # Apply to any Ocean Modifer's 'Time' value on the mesh objects, a common issue for this bug

    cache_objects = [
        dprops.mesh_cache.surface.get_cache_object(),
        dprops.mesh_cache.particles.get_cache_object(),
        dprops.mesh_cache.foam.get_cache_object(),
        dprops.mesh_cache.bubble.get_cache_object(),
        dprops.mesh_cache.spray.get_cache_object(),
        dprops.mesh_cache.dust.get_cache_object()
        ]
    cache_objects = [x for x in cache_objects if x]

    for obj in cache_objects:
        obj_eval = obj.evaluated_get(depsgraph)
        for i in range(len(obj.modifiers)):
            if obj.modifiers[i].type == 'OCEAN':
                obj.modifiers[i].time = obj_eval.modifiers[i].time

    # Apply to any FF_GeometryNodes geometry node 'Motion Blur Scale' value on the mesh objects, another issue 
    # for this bug when adjusting motion blur for slow motion simulations.
    # Also apply to other FF_GeometryNodes inputs in case the user wants to keyframe these values.

    input_name_list_surface = [
        "Input_6",    # Enable Motion Blur
        "Input_4",    # Motion Blur Scale
        "Socket_8",   # Apply Simulation Time Scale
        "Socket_9",   # Apply Simulation World Scale
        "Socket_5",   # Shade Smooth Surface
        "Socket_11",  # Remove Mesh Near Domain Boundary
        "Socket_12",  # X-
        "Socket_13",  # Y-
        "Socket_14",  # Z-
        "Socket_15",  # X+
        "Socket_16",  # Y+
        "Socket_17",  # Z+ 
        "Socket_18",  # Distance
        "Socket_20",  # Flatten Mesh Near Domain Boundary
        "Socket_21",  # Water Level Mode
        "Socket_22",  # Water Level
        "Socket_24",  # Flattened Width
        "Socket_25",  # Transition Width
        "Socket_27",  # Store Displacement Attribute
        "Socket_26",  # Store Transition Mask Attribute
        "Socket_0",   # Blur Velocity For Fading
        "Socket_6",   # Blur Iterations
    ]

    input_name_list_fluid_particles = [
        "Socket_16",  # Apply Material
        "Input_8",    # Enable Motion Blur
        "Input_4",    # Motion Blur Scale
        "Socket_47",  # Apply Simulation Time Scale
        "Socket_48",  # Apply Simulation World Scale
        "Socket_12",  # Particle Display Mode
        "Input_6",    # Particle Scale
        "Socket_11",  # Particle Scale Multiplier
        "Socket_2",   # Particle Scale Random
        "Socket_21",  # Random Bias
        "Socket_14",  # Instancing Mode
        "Socket_18",  # Randomize Instance Rotation (FF 1.8.5)
        "Socket_19",  # Align Instance to Velocity  (FF 1.8.5)
        "Socket_53",  # Randomize Instance Rotation (FF 1.8.6)
        "Socket_54",  # Align Instance to Velocity  (FF 1.8.6)
        "Socket_10",  # Shade Smooth Instances
        "Socket_17",  # Realize Instances
        "Socket_59",  # Duplicate and Randomize Particles
        "Socket_60",  # Num Duplicates
        "Socket_61",  # Distribution Radius
        "Socket_62",  # Distribution Radius Multiplier
        "Socket_51",  # Match Flattened Surface Displacement
        "Socket_55",  # Store Transition Mask Attribute
        "Socket_56",  # Scale Particle With Transition Mask
        "Socket_30",  # Age Based Particle Scaling
        "Socket_31",  # Starting Scale Factor
        "Socket_32",  # Scaling Duration (Age)
        "Socket_33",  # Age Offset
        "Socket_34",  # Store Age Scaling Transition Attribute
        "Socket_24",  # Lifetime Based Particle Scaling
        "Socket_23",  # Final Scale Factor
        "Socket_25",  # Scaling Duration (Lifetime)
        "Socket_26",  # Lifetime Offset
        "Socket_28",  # Store Lifetime Scaling Transition Attribute
        "Socket_36",  # Filter Particle by Source ID
        "Socket_37",  # Source ID 0
        "Socket_38",  # Source ID 1
        "Socket_39",  # Source ID 2
        "Socket_40",  # Source ID 3
        "Socket_41",  # Source ID 4
        "Socket_42",  # Source ID 5
        "Socket_43",  # Source ID 6
        "Socket_44",  # Source ID 7
        "Socket_45",  # Source ID 8
        "Socket_1",   # Fading Width
        "Socket_0",   # Fading Strength
        "Socket_4",   # Fading Density
    ]

    input_name_list_whitewater = [
        "Socket_16",  # Apply Material
        "Input_8",    # Enable Motion Blur
        "Input_4",    # Motion Blur Scale
        "Socket_30",  # Apply Simulation Time Scale
        "Socket_31",  # Apply Simulation World Scale
        "Socket_12",  # Particle Display Mode
        "Input_6",    # Particle Scale
        "Socket_11",  # Particle Scale Multiplier
        "Socket_2",   # Particle Scale Random
        "Socket_21",  # Random Bias
        "Socket_14",  # Instancing Mode
        "Socket_18",  # Randomize Instance Rotation (FF 1.8.5)
        "Socket_19",  # Align Instance to Velocity  (FF 1.8.5)
        "Socket_36",  # Randomize Instance Rotation (FF 1.8.6)
        "Socket_37",  # Align Instance to Velocity  (FF 1.8.6)
        "Socket_10",  # Shade Smooth Instances
        "Socket_17",  # Realize Instances
        "Socket_41",  # Duplicate and Randomize Particles
        "Socket_42",  # Num Duplicates
        "Socket_43",  # Distribution Radius
        "Socket_44",  # Distribution Radius Multiplier
        "Socket_34",  # Matched Flattened Surface Displacement
        "Socket_38",  # Store Transition Mask Attribute
        "Socket_39",  # Scale Particle With Transition Mask
        "Socket_24",  # Lifetime Based Particle Scaling
        "Socket_23",  # Final Scale Factor
        "Socket_25",  # Scaling Duration (Lifetime)
        "Socket_26",  # Lifetime Offset
        "Socket_28",  # Store Lifetime Scaling Transition Attribute
        "Socket_1",   # Fading Width
        "Socket_0",   # Fading Strength
        "Socket_4",   # Fading Density
    ]

    for obj in cache_objects:
        obj_eval = obj.evaluated_get(depsgraph)
        for i in range(len(obj.modifiers)):
            if obj.modifiers[i].type == 'NODES' and obj.modifiers[i].name.startswith("FF_GeometryNodes"):
                mod_name = obj.modifiers[i].name
                if   mod_name.startswith("FF_GeometryNodesSurface"):
                    input_name_list = input_name_list_surface
                elif mod_name.startswith("FF_GeometryNodesFluidParticles"):
                    input_name_list = input_name_list_fluid_particles
                elif mod_name.startswith("FF_GeometryNodesWhitewater"):
                    input_name_list = input_name_list_whitewater
                else:
                    continue

                for input_name in input_name_list:
                    if input_name in obj.modifiers[i]:
                        obj.modifiers[i][input_name] = obj_eval.modifiers[i][input_name]


# Workaround for https://projects.blender.org/blender/blender/issues/71908
#
# If a FLIP Fluids Domain was previously initialized as a Mantaflow Liquid Domain,
# the object will contain a "Liquid" particle system. Particle systems on the domain
# trigger an issue where keyframed parameters are not evaluated during render.
# The 'frame_change_post_apply_T71908_workaround()' workaround does not work
# when the domain contains this particle system.
#
# To work around this issue, the particle systems should be removed when
# initializing the domain object.
def remove_domain_particle_systems_T71908_workaround(bl_object):
    particle_system_count = 0
    for mod in bl_object.modifiers:
        if mod.type == 'PARTICLE_SYSTEM':
            particle_system_count += 1

    if particle_system_count == 0:
        return

    infomsg =  "************************************************\n"
    infomsg += "FLIP Fluids: Removing the following particle system(s) from the Domain <" + bl_object.name + "> object:"
    print(infomsg)
    for mod in bl_object.modifiers:
        if mod.type == 'PARTICLE_SYSTEM':
            print("\t<" + mod.name + ">")
            try:
                bl_object.modifiers.remove(mod)
            except:
                pass

    infomsg =  "Particle Systems on the domain are not supported and can trigger a current\n"
    infomsg += "render bug in Blender (https://projects.blender.org/blender/blender/issues/71908).\n"
    infomsg += "************************************************\n"
    print(infomsg)


# In some versions of Blender the viewport rendered view is 
# not updated to display and object if the object's 'hide_render' 
# property has changed or ray visibility has changed via Python. 
# Toggling the object's hide_viewport option on and off
# is a workaround to get the viewport to update.
#
# Note: toggling hide_viewport will deselect the object, so this workaround
#       will also re-select the object if needed.
def toggle_viewport_visibility_to_update_rendered_viewport_workaround(bl_object):
    is_selected = vcu.select_get(bl_object)
    vcu.toggle_outline_eye_icon(bl_object)
    vcu.toggle_outline_eye_icon(bl_object)
    if is_selected:
        vcu.select_set(bl_object, True)


# Due to API changes in Cycles visibility properties in Blender 3.0, this will
# break compatibility when opening a .blend file saved in Blender 3.0 in earlier
# versions of Blender. This method updates FLIP Fluid object cycles visibility
# settings for 
def load_post_update_cycles_visibility_forward_compatibility_from_blender_3():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return

    last_version = dprops.debug.get_last_saved_blender_version()
    current_version = bpy.app.version

    if last_version == (-1, -1, -1):
        # Skip, file contains no version history.
        return

    if current_version >= last_version:
        # No compatibility update needed
        return

    # Downgrading from Blender 3.x. Compatibility update needed.
    def set_cycles_ray_visibility(bl_object, is_enabled):
        # Cycles may not be enabled in the user's preferences
        try:
            bl_object.visible_camera = is_enabled
            bl_object.visible_diffuse = is_enabled
            bl_object.visible_glossy = is_enabled
            bl_object.visible_transmission = is_enabled
            bl_object.visible_volume_scatter = is_enabled
            bl_object.visible_shadow = is_enabled
        except:
            pass

    flip_props = bpy.context.scene.flip_fluid
    invisible_objects = ([flip_props.get_domain_object()] +
                         flip_props.get_fluid_objects() +
                         flip_props.get_inflow_objects() +
                         flip_props.get_outflow_objects() +
                         flip_props.get_force_field_objects())

    for bl_object in invisible_objects:
        set_cycles_ray_visibility(bl_object, False)
        toggle_viewport_visibility_to_update_rendered_viewport_workaround(bl_object)


def is_persistent_data_issue_relevant():
    if bpy.context.scene.render.engine != 'CYCLES':
        return False
    domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()
    if domain_properties is None:
        return False
    return bpy.context.scene.render.use_persistent_data


def get_persistent_data_warning_string():
    warning = ""
    warning += "************************************************\n"
    warning += "FLIP Fluids: Incompatible Render Option Warning\n\n"
    warning += "The Cycles 'Persistent Data' render option is not compatible with the simulation meshes. This may cause static renders, incorrect renders, or render crashes.\n\n"
    warning += "This issue can be prevented by disabling the 'Render Properties > Performance > Persistent Data' option or by rendering from the command line.\n"
    warning += "See the command line rendering tools in the FLIP Fluids sidebar.\n\n"
    warning += "Command Line Tools Documentation:\n    https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools\n"
    warning += "************************************************\n"
    return warning


# Blender will crash during render if:
#     (Cycles render is used and motion blur is enabled) or other renderers are used
#     and if there is an object with a keyframed hide_render property
#
# In rare cases, Blender may also crash regardless of the above condition if there is an object with a
#     keyframed hide_render property. It is not certain what exact conditions are required for this case.
#
# Issue thread: https://github.com/rlguy/Blender-FLIP-Fluids/issues/566
#
# Workaround: detect these cases and remove depsgraph.update() calls during render calls
#     which will prevent the crash. Note: depsgraph.update() in our use case is not
#     supported in the Python API but has a side effect of making the render more stable.
#     Removing these calls will make the render more likely to crash, so rendering from the
#     command line is recommended in these cases.
def is_keyframed_hide_render_issue_relevant(scene):
    is_relevant = False
    using_cycles = scene.render.engine == 'CYCLES'
    override_condition = True
    if (using_cycles and scene.render.use_motion_blur) or not using_cycles or override_condition:
        for obj in bpy.data.objects:
            if not obj.animation_data:
                continue
            anim_data = obj.animation_data
            if not anim_data.action or not anim_data.action.layers[0].strips[0].channelbag(anim_data.action.slots[0]).fcurves:
                continue

            for fcurve in anim_data.action.layers[0].strips[0].channelbag(anim_data.action.slots[0]).fcurves:
                if fcurve.data_path == "hide_render":
                    is_relevant = True
                    break

    return is_relevant
