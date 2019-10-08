# Blender FLIP Fluid Add-on
# Copyright (C) 2019 Ryan L. Guy
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

import bpy, array

from ..pyfluid import TriangleMesh


def is_blender_28():
    return bpy.app.version >= (2, 80, 0)


def is_blender_281():
    return bpy.app.version >= (2, 81, 0)


def is_blender_279():
    return bpy.app.version <= (2, 79, 999)
    

def register_dict_property(dict_object, name_str, prop):
    if is_blender_28():
        # must use exec as the statement will result in invalid syntax
        # if script is run in Python versions that do nupport annotation syntax
        exec("dict_object[name_str]: prop")
    else:
        dict_object[name_str] = prop


def convert_attribute_to_28(prop_name):
    if is_blender_28():
        p = prop_name
        return "temp_prop = " + p + "; del " + p + "; " + p + ": temp_prop; del temp_prop"
    else:
        return ""


def get_active_object(context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        return context.active_object
    else:
        return context.scene.objects.active


def set_active_object(obj, context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        context.view_layer.objects.active = obj
    else:
        context.scene.objects.active = obj


def select_get(obj):
    if is_blender_28():
        return obj.select_get()
    else:
        return obj.select


def select_set(obj, boolval):
    if is_blender_28():
        obj.select_set(boolval)
    else:
        obj.select = boolval



def get_object_display_type(obj):
    if is_blender_28():
        return obj.display_type
    else:
        return obj.draw_type


def set_object_display_type(obj, display_type):
    if is_blender_28():
        obj.display_type = display_type
    else:
        obj.draw_type = display_type


def set_object_hide_viewport(obj, display_bool):
    if is_blender_28():
        obj.hide_viewport = display_bool
    else:
        obj.hide = display_bool


def get_object_hide_viewport(obj):
    if is_blender_28():
        return obj.hide_viewport
    else:
        return obj.hide


def set_object_instance_type(obj, display_type):
    if is_blender_28():
        if obj.instance_type != display_type:
            obj.instance_type = display_type
    else:
        if obj.dupli_type != display_type:
            obj.dupli_type = display_type


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
    if is_blender_28():
        mesh_collection = get_flip_mesh_collection(context)
        mesh_collection.objects.link(obj)
    else:
        context.scene.objects.link(obj)


def link_object(obj, context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        flip_collection = get_flip_fluids_collection(context)
        flip_collection.objects.link(obj)
    else:
        context.scene.objects.link(obj)


def add_to_flip_fluids_collection(obj, context):
    if context is None:
        context = bpy.context
    if is_blender_28():
        flip_collection = get_flip_fluids_collection(context)
        if flip_collection.objects.get(obj.name):
            return
        flip_collection.objects.link(obj)


def remove_from_flip_fluids_collection(obj, context):
    if context is None:
        context = bpy.context
    if is_blender_28():
        flip_collection = get_flip_fluids_collection(context)

        num_collections = 0
        for collection in bpy.data.collections:
            if collection.objects.get(obj.name):
                num_collections += 1
        if num_collections == 1 and context.scene.collection.objects.get(obj.name) is None:
            context.scene.collection.objects.link(obj)

        if flip_collection.objects.get(obj.name):
            flip_collection.objects.unlink(obj)


def delete_object(obj):
    mesh_data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    mesh_data.user_clear()
    bpy.data.meshes.remove(mesh_data)


def delete_mesh_data(mesh_data):
    mesh_data.user_clear()
    bpy.data.meshes.remove(mesh_data)


def get_scene_collection(context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        return context.scene.collection
    else:
        return context.scene


def get_all_scene_objects(context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        return context.scene.collection.all_objects
    else:
        return context.scene.objects


def element_multiply(v1, v2):
    if is_blender_28():
        return v1 @ v2
    else:
        return v1 * v2


def depsgraph_update(context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        depsgraph = context.evaluated_depsgraph_get()
        depsgraph.update()
    else:
        context.scene.update()


def object_to_triangle_mesh(obj, matrix_world=None):
    edge_split_show_render_values = []
    for m in obj.modifiers:
        if m.type == 'EDGE_SPLIT':
            edge_split_show_render_values.append(m.show_render)
            m.show_render = False

    triangulation_mod = obj.modifiers.new("flip_triangulate", "TRIANGULATE")

    is_28 = is_blender_28()
    if is_28:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        new_mesh = obj_eval.to_mesh()
    else:
        new_mesh = obj.to_mesh(scene=bpy.context.scene, 
                               apply_modifiers=True, 
                               settings='RENDER')

    vertex_components = []
    if matrix_world is None:
        for mv in new_mesh.vertices:
            v = mv.co
            vertex_components.append(v.x)
            vertex_components.append(v.y)
            vertex_components.append(v.z)
    else:
        if is_28:
            for mv in new_mesh.vertices:
                v = matrix_world @ mv.co
                vertex_components.append(v.x)
                vertex_components.append(v.y)
                vertex_components.append(v.z)
        else:
            for mv in new_mesh.vertices:
                v = matrix_world * mv.co
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

    if is_28:
        obj_eval.to_mesh_clear()
    else:
        new_mesh.user_clear()
        bpy.data.meshes.remove(new_mesh)

    obj.modifiers.remove(triangulation_mod)

    for m in obj.modifiers:
        if m.type == 'EDGE_SPLIT':
            m.show_render = edge_split_show_render_values.pop(0)

    return tmesh


def _set_mesh_smoothness(mesh_data, is_smooth):
        values = [is_smooth] * len(mesh_data.polygons)
        mesh_data.polygons.foreach_set("use_smooth", values)


def _set_octane_mesh_type(mesh_data, mesh_type):
        if hasattr(bpy.context.scene, 'octane') and mesh_type is not None:
            mesh_data.octane.mesh_type = mesh_type


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
                                   octane_mesh_type='0'):
    if is_blender_281():
        bl_object.data.clear_geometry()
        bl_object.data.from_pydata(vertices, [], triangles)
        _set_mesh_smoothness(bl_object.data, smooth_mesh)
        _set_octane_mesh_type(bl_object.data, octane_mesh_type)
    else:
        old_mesh_data = bl_object.data
        new_mesh_data = bpy.data.meshes.new(mesh_name)
        new_mesh_data.from_pydata(vertices, [], triangles)
        bl_object.data = new_mesh_data

        _transfer_mesh_materials(old_mesh_data, new_mesh_data)
        _set_mesh_smoothness(new_mesh_data, smooth_mesh)
        _set_octane_mesh_type(new_mesh_data, octane_mesh_type)

        old_mesh_data.user_clear()
        bpy.data.meshes.remove(old_mesh_data)


def get_blender_preferences(context=None):
    if context is None:
        context = bpy.context
    if is_blender_28():
        return context.preferences
    else:
        return context.user_preferences


def get_addon_preferences(context=None):
    if context is None:
        context = bpy.context
    id_name = __name__.split(".")[0]
    return get_blender_preferences(context).addons[id_name].preferences


#
# UI Compatibility
#


def ui_split(ui_element, factor=None, align=None):
    if is_blender_28():
        if factor is None and align is None:
            return ui_element.split()
        elif factor is None: 
            return ui_element.split(align=align)
        elif align is None:
            return ui_element.split(factor=factor)
        else:
            return ui_element.split(factor=factor, align=align)
    else:
        if factor is None and align is None:
            return ui_element.split()
        elif factor is None: 
            return ui_element.split(align=align)
        elif align is None:
            return ui_element.split(percentage=factor)
        else:
            return ui_element.split(percentage=factor, align=align)


def get_file_folder_icon():
    if is_blender_28():
        return "FILEBROWSER"
    else:
        return "FILESEL"