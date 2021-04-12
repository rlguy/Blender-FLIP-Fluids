# Blender FLIP Fluids Add-on
# Copyright (C) 2021 Ryan L. Guy
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

    # Apply to any Ocean Modifer's 'Time' value on the mesh objects, a common issue for this bug

    cache_objects = [
        dprops.mesh_cache.surface.get_cache_object(),
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
                print("updated", obj.modifiers[i])


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