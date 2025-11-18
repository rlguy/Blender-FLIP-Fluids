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

import bpy, array, os, numpy

from ..ffengine import TriangleMesh

def is_blender_279():
    return bpy.app.version <= (2, 79, 999)

def is_blender_28():
    return bpy.app.version >= (2, 80, 0)


def is_blender_281():
    return bpy.app.version >= (2, 81, 0)


def is_blender_282():
    return bpy.app.version >= (2, 82, 0)


def is_blender_29():
    return bpy.app.version >= (2, 90, 0)


def is_blender_293():
    return bpy.app.version >= (2, 93, 0)


def is_blender_30():
    return bpy.app.version >= (3, 0, 0)


def is_blender_31():
    return bpy.app.version >= (3, 1, 0)


def is_blender_32():
    return bpy.app.version >= (3, 2, 0)


def is_blender_33():
    return bpy.app.version >= (3, 3, 0)


def is_blender_34():
    return bpy.app.version >= (3, 4, 0)


def is_blender_35():
    return bpy.app.version >= (3, 5, 0)


def is_blender_36():
    return bpy.app.version >= (3, 6, 0)


def is_blender_40():
    return bpy.app.version >= (4, 0, 0)


def is_blender_42():
    return bpy.app.version >= (4, 2, 0)


def is_blender_43():
    return bpy.app.version >= (4, 3, 0)


def is_blender_44():
    return bpy.app.version >= (4, 4, 0)


def is_blender_45():
    return bpy.app.version >= (4, 5, 0)


def convert_attribute_to_28(prop_name):
    print("FLIP Fluids Warning: 'convert_attribute_to_28' method is deprecated. Contact the developers if you see this message. This message is not an error and can be safely ignored.")
    p = prop_name
    return "temp_prop = " + p + "; del " + p + "; " + p + ": temp_prop; del temp_prop"


def get_active_object(context=None):
    if context is None:
        context = bpy.context
    return context.active_object


def set_active_object(obj, context=None):
    if context is None:
        context = bpy.context
    context.view_layer.objects.active = obj


def select_get(obj):
    return obj.select_get()


def select_set(obj, boolval):
    obj.select_set(boolval)



def get_object_display_type(obj):
    return obj.display_type


def set_object_display_type(obj, display_type):
    obj.display_type = display_type


def set_object_hide_viewport(obj, display_bool):
    if obj.hide_get() != display_bool:
        obj.hide_set(display_bool)


def get_object_hide_viewport(obj):
    return obj.hide_get()


def toggle_outline_eye_icon(obj):
    obj.hide_viewport = not obj.hide_viewport


def set_object_instance_type(obj, display_type):
    if obj.instance_type != display_type:
        obj.instance_type = display_type


def get_flip_fluids_collection(context):
    collection = bpy.data.collections.get("FLIPFluids")
    if collection is None:
        collection = bpy.data.collections.new('FLIPFluids')
        context.scene.collection.children.link(collection)
    return collection


def get_flip_mesh_collection(context):
    mesh_collection = bpy.data.collections.get("FLIPMeshes")
    if mesh_collection is None:
        flip_collection = get_flip_fluids_collection(context)
        mesh_collection = bpy.data.collections.new('FLIPMeshes')
        flip_collection.children.link(mesh_collection)
    return mesh_collection


def link_fluid_mesh_object(obj, context=None):
    if context is None:
        context = bpy.context
    mesh_collection = get_flip_mesh_collection(context)
    mesh_collection.objects.link(obj)


def link_object(obj, context=None):
    if context is None:
        context = bpy.context
    flip_collection = get_flip_fluids_collection(context)
    flip_collection.objects.link(obj)


def link_object_to_master_scene(obj, context=None):
    if context is None:
        context = bpy.context
    context.scene.collection.objects.link(obj)


def add_to_flip_fluids_collection(obj, context):
    if context is None:
        context = bpy.context
    flip_collection = get_flip_fluids_collection(context)
    if flip_collection.objects.get(obj.name):
        return
    flip_collection.objects.link(obj)


def remove_from_flip_fluids_collection(obj, context):
    if context is None:
        context = bpy.context

    flip_collection = get_flip_fluids_collection(context)

    num_collections = 0
    for collection in bpy.data.collections:
        if collection.name.startswith("RigidBodyWorld"):
            # The RigidBodyWorld collection (for RBD objects) is more hidden within the Blend file
            # and may not be apparent to many users. Ignore this collection in the count so that
            # it does not appear that the objects dissappear.
            continue
        if collection.objects.get(obj.name):
            num_collections += 1
    if num_collections == 1 and context.scene.collection.objects.get(obj.name) is None:
        context.scene.collection.objects.link(obj)

    if flip_collection.objects.get(obj.name):
        flip_collection.objects.unlink(obj)


def delete_object(obj, remove_mesh_data=True):
    if obj.type == 'MESH':
        mesh_data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if remove_mesh_data:
            mesh_data.user_clear()
            bpy.data.meshes.remove(mesh_data)
    else:
        bpy.data.objects.remove(obj, do_unlink=True)


def delete_mesh_data(mesh_data):
    mesh_data.user_clear()
    bpy.data.meshes.remove(mesh_data)


def get_scene_collection(context=None):
    if context is None:
        context = bpy.context
    return context.scene.collection


def get_all_scene_objects(context=None):
    if context is None:
        context = bpy.context
    return context.scene.collection.all_objects


def element_multiply(v1, v2):
    return v1 @ v2


def depsgraph_update(context=None):
    if context is None:
        context = bpy.context
    depsgraph = context.evaluated_depsgraph_get()
    depsgraph.update()


def object_to_triangle_mesh(obj, matrix_world=None):
    # To ensure the modifier stack is processed in 2.8, the object's 'hide in viewport'
    # must be False. This is a limitation of how meshes or exported in Blender.
    # The 'hide in viewport' status will be set back to the original value at the
    # end of this method.
    #
    # More info: https://developer.blender.org/T71556
    hide_viewport_status = obj.hide_viewport
    if hide_viewport_status:
        obj.hide_viewport = False

    # The 'Edge Split' modifier will disconnect faces from eachother, resulting in
    # a non-manifold mesh. Disable the edge split modifier from the modifier stack
    # before exporting. Original value will be set back at the end of this method
    edge_split_show_render_values = []
    edge_split_show_viewport_values = []
    for m in obj.modifiers:
        if m.type == 'EDGE_SPLIT':
            edge_split_show_render_values.append(m.show_render)
            edge_split_show_viewport_values.append(m.show_viewport)
            m.show_render = False
            m.show_viewport = False

    triangulation_mod = obj.modifiers.new("flip_triangulate", "TRIANGULATE")
    triangulation_mod.quad_method = 'FIXED'

    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    new_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

    vertex_components = []
    if matrix_world is None:
        for mv in new_mesh.vertices:
            v = mv.co
            vertex_components.append(v.x)
            vertex_components.append(v.y)
            vertex_components.append(v.z)
    else:
        for mv in new_mesh.vertices:
            v = matrix_world @ mv.co
            vertex_components.append(v.x)
            vertex_components.append(v.y)
            vertex_components.append(v.z)

    triangle_indices = []
    for t in new_mesh.polygons:
        for idx in t.vertices:
            triangle_indices.append(idx)
    
    tmesh = TriangleMesh()
    tmesh.vertices = array.array('f', vertex_components)
    tmesh.triangles = array.array('i', triangle_indices)

    obj_eval.to_mesh_clear()

    obj.modifiers.remove(triangulation_mod)

    for m in obj.modifiers:
        if m.type == 'EDGE_SPLIT':
            m.show_render = edge_split_show_render_values.pop(0)
            m.show_viewport = edge_split_show_viewport_values.pop(0)

    if hide_viewport_status != obj.hide_viewport:
        obj.hide_viewport = hide_viewport_status

    return tmesh


def _set_mesh_smoothness(mesh_data, is_smooth):
        values = [is_smooth] * len(mesh_data.polygons)
        mesh_data.polygons.foreach_set("use_smooth", values)


def _set_octane_mesh_type(obj, mesh_type):
        if hasattr(bpy.context.scene, 'octane') and mesh_type is not None:
            obj.octane.object_mesh_type = mesh_type


def _transfer_mesh_materials(src_mesh_data, dst_mesh_data):
        material_names = []
        for m in src_mesh_data.materials:
            material_names.append(m.name)

        for name in material_names:
            for m in bpy.data.materials:
                if m.name == name:
                    dst_mesh_data.materials.append(m)
                    break


def swap_object_mesh_data_geometry(bl_object, vertices=[], triangles=[], 
                                   mesh_name="Untitled",
                                   smooth_mesh=False,
                                   octane_mesh_type='Global'):

    vg_layer_names = [vg.name for vg in bl_object.vertex_groups]
    active_vertex_layer_index = bl_object.vertex_groups.active_index

    # UV Maps
    uv_layer_names = [uv.name for uv in bl_object.data.uv_layers]
    is_uv_layer_active = [uv.active for uv in bl_object.data.uv_layers]
    is_uv_layer_active_render = [uv.active_render for uv in bl_object.data.uv_layers]

    # Color Attributes
    ca_layer_names = [ca.name for ca in bl_object.data.color_attributes]
    ca_layer_data_types = [ca.data_type for ca in bl_object.data.color_attributes]
    ca_layer_domain_types = [ca.domain for ca in bl_object.data.color_attributes]
    active_color_layer_index = bl_object.data.color_attributes.active_color_index
    active_color_render_index = bl_object.data.color_attributes.render_color_index

    vertices = numpy.array(vertices, dtype=numpy.float32)
    num_vertices = vertices.shape[0] // 3
    vertex_index = numpy.array(triangles, dtype=numpy.int32)
    loop_start = numpy.array(list(range(0, len(triangles), 3)), dtype=numpy.int32)
    num_loops = loop_start.shape[0]
    loop_total = numpy.array([3] * (len(triangles) // 3), dtype=numpy.int32)

    bl_object.data.clear_geometry()
    bl_object.data.from_pydata(vertices, [], triangles)

    _set_mesh_smoothness(bl_object.data, smooth_mesh)
    _set_octane_mesh_type(bl_object, octane_mesh_type)

    # Vertex Groups
    for i, name in enumerate(vg_layer_names):
        vg_layer = bl_object.vertex_groups.new(name=name)
        if active_vertex_layer_index >= 0:
            bl_object.vertex_groups.active_index = active_vertex_layer_index

    # UV Maps
    for i, name in enumerate(uv_layer_names):
        uv_layer = bl_object.data.uv_layers.new(name=name)
        uv_layer.active = is_uv_layer_active[i]
        uv_layer.active_render = is_uv_layer_active_render[i]

    # Color Attributes
    for i, name in enumerate(ca_layer_names):
        ca_layer = bl_object.data.color_attributes.new(
                name=name, 
                type=ca_layer_data_types[i], 
                domain=ca_layer_domain_types[i]
                )
        # Unable to set active color/render index > 0. Possibly a Blender bug that we need
        # to report. For now, the Color Attributes layer will be limited to a single layer.
        # As far as we know, this feature does not need to be used outside of Octane Render.
        """
        if active_color_layer_index >= 0:
            bl_object.data.color_attributes.active_color_index = active_color_layer_index
        if active_color_render_index >= 0:
            bl_object.data.color_attributes.render_color_index = active_color_render_index
        """


def get_addon_directory():
    this_filepath = os.path.dirname(os.path.realpath(__file__))
    addon_directory = os.path.dirname(this_filepath)
    return addon_directory


def get_blender_preferences(context=None):
    if context is None:
        context = bpy.context
    return context.preferences


def get_blender_preferences_temporary_directory(context=None):
    if context is None:
        context = bpy.context
    return get_blender_preferences(context).filepaths.temporary_directory


def get_addon_preferences(context=None):
    from ..properties import preferences_properties
    return preferences_properties.get_addon_preferences(context)


#
# UI Compatibility
#


def ui_split(ui_element, factor=None, align=None):
    if factor is None and align is None:
        return ui_element.split()
    elif factor is None: 
        return ui_element.split(align=align)
    elif align is None:
        return ui_element.split(factor=factor)
    else:
        return ui_element.split(factor=factor, align=align)


def get_file_folder_icon():
    return "FILEBROWSER"


def get_hide_off_icon():
    return "HIDE_OFF"


def get_hide_on_icon():
     return "HIDE_ON"


def str_removesuffix(input_string, suffix):
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string