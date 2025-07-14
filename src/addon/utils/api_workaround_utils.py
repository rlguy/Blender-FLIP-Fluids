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

import bpy
from . import version_compatibility_utils as vcu
from .. import render


# Workaround for https://developer.blender.org/T71908
# This bug can cause keyframed parameters not to be evaluated during rendering
# when a frame_change handler is used.
#
# This workaround works by forcing an object to be evaluated and then setting
# the original object value to the evaluated values. This workaround can only
# be applied to Blender versions 2.81 and later.
def frame_change_post_apply_T71908_workaround(context, depsgraph=None):
    if not render.is_rendering():
        return
    if not vcu.is_blender_281():
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
        "Input_4",  # Motion Blur Scale
        "Input_6",  # Enable Motion Blur
        "Socket_0", # Blur Velocity For Fading
        "Socket_5", # Shade Smooth Surface
        "Socket_6", # Blur Iterations
    ]

    input_name_list_particles = [
        "Input_4",  # Motion Blur Scale
        "Input_5",  # Material
        "Input_6",  # Particle Scale
        "Input_8",  # Enable Motion Blur
        "Input_9",  # Enable Point Cloud
        "Input_10", # Enable Instancing
        "Socket_0", # Fading Strength
        "Socket_1", # Fading Width
        "Socket_2", # Particle Scale Random
        "Socket_4", # Fading Density
        "Socket_9", # Shade Smooth Instancing
    ]

    for obj in cache_objects:
        obj_eval = obj.evaluated_get(depsgraph)
        for i in range(len(obj.modifiers)):
            if obj.modifiers[i].type == 'NODES' and obj.modifiers[i].name.startswith("FF_GeometryNodes"):
                mod_name = obj.modifiers[i].name
                if   mod_name.startswith("FF_GeometryNodesSurface"):
                    input_name_list = input_name_list_surface
                elif mod_name.startswith("FF_GeometryNodesFluidParticles") or mod_name.startswith("FF_GeometryNodesWhitewater"):
                    input_name_list = input_name_list_particles
                else:
                    continue

                for input_name in input_name_list:
                    if input_name in obj.modifiers[i]:
                        obj.modifiers[i][input_name] = obj_eval.modifiers[i][input_name]


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
            if vcu.is_blender_30():
                bl_object.visible_camera = is_enabled
                bl_object.visible_diffuse = is_enabled
                bl_object.visible_glossy = is_enabled
                bl_object.visible_transmission = is_enabled
                bl_object.visible_volume_scatter = is_enabled
                bl_object.visible_shadow = is_enabled
            else:
                bl_object.cycles_visibility.camera = is_enabled
                bl_object.cycles_visibility.transmission = is_enabled
                bl_object.cycles_visibility.diffuse = is_enabled
                bl_object.cycles_visibility.scatter = is_enabled
                bl_object.cycles_visibility.glossy = is_enabled
                bl_object.cycles_visibility.shadow = is_enabled
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


def get_enabled_features_affected_by_T88811(domain_properties=None):
    if domain_properties is None:
        domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()
    if domain_properties is None:
        return None
    dprops = domain_properties

    data_dict = {}
    data_dict["attributes"] = {}
    data_dict["attributes"]["surface"] = []
    data_dict["attributes"]["whitewater"] = []
    data_dict["fluidparticles"] = []
    data_dict["viscosity"] = []

    if dprops.surface.enable_velocity_vector_attribute:
        data_dict["attributes"]["surface"].append("Velocity")
    if dprops.surface.enable_speed_attribute:
        data_dict["attributes"]["surface"].append("Speed")
    if dprops.surface.enable_vorticity_vector_attribute:
        data_dict["attributes"]["surface"].append("Vorticity")
    if dprops.surface.enable_color_attribute:
        data_dict["attributes"]["surface"].append("Color")
    if dprops.surface.enable_age_attribute:
        data_dict["attributes"]["surface"].append("Age")
    if dprops.surface.enable_lifetime_attribute:
        data_dict["attributes"]["surface"].append("Lifetime")
    if dprops.surface.enable_whitewater_proximity_attribute:
        data_dict["attributes"]["surface"].append("Whitewater Proximity")
    if dprops.surface.enable_source_id_attribute:
        data_dict["attributes"]["surface"].append("Source ID")

    if dprops.whitewater.enable_velocity_vector_attribute:
        data_dict["attributes"]["whitewater"].append("Velocity")

    # Disabled to prevent the warning popup from displaying on default settings (Whitewater ID enabled by default)
    # TODO: Rework this warning to be less intrusive
    """
    if dprops.whitewater.enable_id_attribute:
        data_dict["attributes"]["whitewater"].append("ID")
    """

    if dprops.whitewater.enable_lifetime_attribute:
        data_dict["attributes"]["whitewater"].append("Lifetime")

    if dprops.particles.enable_fluid_particle_output:
        data_dict["fluidparticles"].append("Fluid particle export and particle attributes")

    if dprops.world.enable_viscosity and dprops.surface.enable_viscosity_attribute:
        data_dict["viscosity"].append("Variable Viscosity")

    contains_info = (
            data_dict["attributes"]["surface"] or 
            data_dict["attributes"]["whitewater"] or 
            data_dict["fluidparticles"] or 
            data_dict["viscosity"]
            )
    if not contains_info:
        return None

    return data_dict


def get_enabled_features_string_T88811(feature_list):
    features_str = ""
    for i, item in enumerate(feature_list):
        features_str += item
        if i != len(feature_list) - 1:
            features_str += ", "
    return features_str


def draw_T88811_ui_warning(ui_box, preferences, feature_dict):
    row = ui_box.row(align=True)
    row.alert = True
    row.label(text="FLIP Fluids: Possible Render Crash Warning:", icon="ERROR")
    column = ui_box.column(align=True)
    column.label(text="A current bug in Blender may cause frequent") 
    column.label(text="render crashes or incorrect renders when") 
    column.label(text="using the following enabled features:")
    column.separator()

    if feature_dict["attributes"]["surface"]:
        column.label(text="Surface Attributes:", icon="ERROR")
        column.label(text=get_enabled_features_string_T88811(feature_dict["attributes"]["surface"]), icon="DOT")
    if feature_dict["attributes"]["whitewater"]:
        column.label(text="Whitewater Attributes:", icon="ERROR")
        column.label(text=get_enabled_features_string_T88811(feature_dict["attributes"]["whitewater"]), icon="DOT")
    if feature_dict["fluidparticles"]:
        column.label(text="Fluid Particle Features:", icon="ERROR")
        column.label(text=get_enabled_features_string_T88811(feature_dict["fluidparticles"]), icon="DOT")
    if feature_dict["viscosity"]:
        column.label(text="Viscosity Features:", icon="ERROR")
        column.label(text=get_enabled_features_string_T88811(feature_dict["viscosity"]), icon="DOT")
    column.separator()

    column.label(text="This bug can be prevented by rendering", icon="INFO")
    column.label(text="from the command line. See the cmd")
    column.label(text="rendering tools in the FLIP Fluids sidebar.")

    column.operator(
            "wm.url_open", 
            text="Documentation: Command Line Tools", 
            icon="URL"
        ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools"
    column.operator(
            "wm.url_open", 
            text="Bug Report: T88811", 
            icon="URL"
        ).url = "https://projects.blender.org/blender/blender/issues/88811"

    column.prop(preferences, "dismiss_T88811_crash_warning", text="Do not show this warning again")

def get_T88811_cmd_warning_string(feature_dict):
    warning = ""
    warning += "************************************************\n"
    warning += "FLIP Fluids: Possible Render Crash Warning\n\n"
    warning += "A current bug in Blender may cause frequent render crashes or incorrect renders when using the following enabled features:\n\n"

    if feature_dict["attributes"]["surface"]:
        warning += "* Surface Attributes:\n"
        warning += "    - " + get_enabled_features_string_T88811(feature_dict["attributes"]["surface"]) + "\n"
    if feature_dict["attributes"]["whitewater"]:
        warning += "* Whitewater Attributes:\n"
        warning += "    - " + get_enabled_features_string_T88811(feature_dict["attributes"]["whitewater"]) + "\n"
    if feature_dict["viscosity"]:
        warning += "* Viscosity Features:\n"
        warning += "    - " + get_enabled_features_string_T88811(feature_dict["viscosity"]) + "\n"

    warning += "\n"
    warning += "This bug can be prevented by rendering from the command line.\n"
    warning += "See the command line rendering tools in the FLIP Fluids sidebar.\n\n"
    warning += "Command Line Tools Documentation:\n    https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools\n"
    warning += "Bug Report T88811:\n    https://developer.blender.org/T88811\n"
    warning += "************************************************\n"

    return warning


def is_persistent_data_issue_relevant():
    if bpy.context.scene.render.engine != 'CYCLES':
        return False
    domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()
    if domain_properties is None:
        return False
    return bpy.context.scene.render.use_persistent_data


def draw_persistent_data_warning(ui_box, preferences):
    row = ui_box.row(align=True)
    row.alert = True
    row.label(text="FLIP Fluids: Incompatible Render Option Warning:", icon="ERROR")
    column = ui_box.column(align=True)
    column.label(text="The Cycles 'Persistent Data' render option is not")
    column.label(text="compatible with the simulation meshes. This may")
    column.label(text="cause static renders, incorrect renders, or")
    column.label(text="render crashes.")
    column.separator()
    column.label(text="This issue can be prevented by disabling")
    column.label(text="Render Properties > Performance > Persistent Data:")

    row = column.row(align=True)
    row.alignment = 'LEFT'
    row.label(text="     ")
    row.prop(bpy.context.scene.render, "use_persistent_data")

    column.label(text="Or by rendering from the command line. See the")
    column.label(text="cmd rendering tools in the FLIP Fluids sidebar.")

    column.operator(
            "wm.url_open", 
            text="Documentation: Command Line Tools", 
            icon="URL"
        ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools"

    column.prop(preferences, "dismiss_persistent_data_render_warning", text="Do not show this warning again")


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
            if not anim_data.action or not anim_data.action.fcurves:
                continue

            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == "hide_render":
                    is_relevant = True
                    break

    return is_relevant
