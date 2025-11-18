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

import bpy, os, pathlib, stat, subprocess, platform, math, mathutils, fnmatch, random, mathutils, datetime, shutil, traceback, re, time
from mathutils import Vector
from xml.etree.ElementTree import Element, SubElement, ElementTree
from bpy_extras.io_utils import ImportHelper
from bpy.props import (
        BoolProperty,
        StringProperty,
        CollectionProperty
        )

from ..utils import version_compatibility_utils as vcu
from ..utils import export_utils
from ..utils import audio_utils
from ..objects import flip_fluid_cache
from ..objects import flip_fluid_aabb
from . import bake_operators
from .. import render


def _select_make_active(context, active_object):
    for obj in context.selected_objects:
        vcu.select_set(obj, False)
    vcu.select_set(active_object, True)
    vcu.set_active_object(active_object, context)

def show_message_box(message="", title="Info", icon='INFO'):
    """Shows a popup message box with the given message."""
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

class FlipFluidHelperRemesh(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_remesh"
    bl_label = "FLIP Fluids Remesh Collection"
    bl_description = ("Combine object geometry within a collection and remesh into a single object for use in the simulator." +
        " Optionally convert non-mesh objects to mesh, apply modifiers, and skip objects hidden from render." +
        " Saving is recommended before using this operator - this operator may take some time to compute depending on complexity" +
        " of the input geometry. Use the link next to this operator to view documentation and a video guide" + 
        " for using this feature")

    skip_hide_render_objects: BoolProperty(True)

    apply_object_modifiers: BoolProperty(True)

    convert_objects_to_mesh: BoolProperty(True)


    @classmethod
    def poll(cls, context):
        return True


    def display_convert_to_mesh_popup(self, object_list):
        def draw_func(self, context):
            text_label = "The following (" + str(len(object_list)) 
            text_label += ") selected objects are required be converted to a mesh type before using this operator:"
            self.layout.label(text=text_label)
            column = self.layout.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            for obj in object_list:
                column_left.label(text=5*" " + "Name: " + obj.name)
                column_right.label(text="Type: " + obj.type)
            self.layout.label(text="")
            self.layout.label(text="Solutions: ", icon="INFO")
            self.layout.label(text=5*" " + "(1) Convert objects to a Blender mesh object")
            self.layout.label(text=5*" " + "(2) Or disable objects in viewport (outliner monitor icon)")
            self.layout.label(text=5*" " + "(3) Or enable 'Convert Objects to Mesh' option")

        bpy.context.window_manager.popup_menu(draw_func, title="FLIP Fluids Remesh: Actions Required", icon='INFO')


    def display_apply_modifiers_popup(self, object_list):
        def draw_func(self, context):
            text_label = "The following (" + str(len(object_list)) 
            text_label += ") selected objects are required to have modifiers applied before using this operator:"
            self.layout.label(text=text_label)
            column = self.layout.column(align=True)
            split = column.split(align=True)
            column_left = split.column(align=True)
            column_right = split.column(align=True)
            for obj in object_list:
                column_left.label(text=5*" " + "Name: " + obj.name)
                column_right.label(text="# Modifiers: " + str(len(obj.modifiers)))
            self.layout.label(text="")
            self.layout.label(text="Solutions: ", icon="INFO")
            self.layout.label(text=5*" " + "(1) Apply modifiers to objects")
            self.layout.label(text=5*" " + "(2) Or disable objects in viewport (outliner monitor icon)")
            self.layout.label(text=5*" " + "(3) Or enable 'Apply Object Modifiers' option")

        bpy.context.window_manager.popup_menu(draw_func, title="FLIP Fluids Remesh: Actions Required", icon='INFO')


    def set_blender_object_selection(self, context, object_list):
        # Select valid objects and set a valid active object if possible
        bpy.ops.object.select_all(action='DESELECT')
        if object_list:
            context.view_layer.objects.active = object_list[0]
        for obj in object_list:
            obj.select_set(True)


    def execute(self, context):
        # Object types that can be converted to a mesh and can have modifiers applied
        valid_object_types = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT']

        # Operator can only function in Object mode
        if bpy.context.object.mode != 'OBJECT':
            err_msg = "FLIP Fluids Remesh: Viewport must be in Object mode to use this operator. "
            err_msg += " Current viewport mode: <" + bpy.context.object.mode + ">."
            self.report({'ERROR'}, err_msg)
            return {'CANCELLED'}

        # Objects will be operated on if they are contained in this collection or any valid subcollections
        active_collection = context.view_layer.active_layer_collection.collection
        if active_collection is None:
            self.report({'ERROR'}, "FLIP Fluids Remesh: No collection selected. Select a collection to remesh.")
            return {'CANCELLED'}
        
        # Filter out objects that are invalid types that cannot be converted to a mesh and have modifiers applied
        skipped_invalid_type_objects = [obj for obj in active_collection.all_objects if obj.type not in valid_object_types]
        valid_collection_objects = [obj for obj in active_collection.all_objects if obj.type in valid_object_types]
        
        # Filter out objects that are disabled in the viewport and are unable to be operated on
        skipped_non_visible_objects = [obj for obj in valid_collection_objects if not obj.visible_get()]
        valid_collection_objects = [obj for obj in valid_collection_objects if obj.visible_get()]
        
        # Filter out objects that have selection disabled and are unable to be operated on
        skipped_hide_select_objects = [obj for obj in valid_collection_objects if obj.hide_select]
        valid_collection_objects = [obj for obj in valid_collection_objects if not obj.hide_select]

        # Filter out objects that have render visibility disabled
        skipped_hide_render_objects = []
        if self.skip_hide_render_objects:
            skipped_hide_render_objects = [obj for obj in valid_collection_objects if obj.hide_render]
            valid_collection_objects = [obj for obj in valid_collection_objects if not obj.hide_render]

        # If in the case there are no objects that can be operated on, there is nothing that can be done
        if not valid_collection_objects:
            self.report({'ERROR'}, "FLIP Fluids Remesh: No valid objects to remesh.")
            return {'CANCELLED'}

        # Objects that can be automatically converted to a mesh
        objects_to_convert_to_mesh = [obj for obj in valid_collection_objects if obj.type != 'MESH' and obj.type in valid_object_types]
        if not self.convert_objects_to_mesh and objects_to_convert_to_mesh:
            self.set_blender_object_selection(context, objects_to_convert_to_mesh)
            self.display_convert_to_mesh_popup(objects_to_convert_to_mesh)
            return {'CANCELLED'}

        # Objects that have modifiers to be applied
        objects_with_modifiers = [obj for obj in valid_collection_objects if len(obj.modifiers) >= 1]
        if not self.apply_object_modifiers and objects_with_modifiers:
            self.set_blender_object_selection(context, objects_with_modifiers)
            self.display_apply_modifiers_popup(objects_with_modifiers)
            return {'CANCELLED'}

        valid_object_count = len(valid_collection_objects)
        self.set_blender_object_selection(context, valid_collection_objects)
        
        # Covert all selected objects to MESH type and apply modifiers
        bpy.ops.object.convert(target='MESH')
        
        # Join all selected objects and rename object
        bpy.ops.object.join()
        context.view_layer.objects.active.name = active_collection.name + "_joined"

        # Add REMESH modifier
        remesh_modifier = context.view_layer.objects.active.modifiers.new("FLIP Fluids Remesh", 'REMESH')
        remesh_modifier.mode = 'VOXEL'
        remesh_modifier.voxel_size = 0.04
        remesh_modifier.adaptivity = 0.1
        remesh_modifier.use_smooth_shade = True

        info_msg = "FLIP Fluids Remesh: Successfully merged and remeshed " 
        info_msg += str(valid_object_count) + " valid objects into object <" + context.view_layer.objects.active.name + ">"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperSelectDomain(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_domain"
    bl_label = "Select Domain"
    bl_description = "Select the domain object"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        num_domains = 0
        found_domains = ""
        for scene in bpy.data.scenes:
            for obj in scene.objects:
                if obj.flip_fluid.is_domain():
                    num_domains += 1
                    found_domains += obj.name + " <scene: " + scene.name + ">, "
        found_domains = vcu.str_removesuffix(found_domains, ", ")
        if num_domains > 1:
            self.report({'ERROR'}, "Error: multiple domain objects found. Only one domain per Blend file is supported. Please remove other domains. Found domain objects: " + found_domains)
            return {'CANCELLED'}

        domain_found = False
        for obj in context.scene.objects:
            if obj.name == domain.name:
                domain_found = True
                break

        if not domain_found:
            scene_name = "Unknown Scene"
            for scene in bpy.data.scenes:
                for obj in scene.objects:
                    if obj.name == domain.name:
                        scene_name = scene.name
                        break
            self.report({'ERROR'}, "Unable to select domain object. Domain object is contained in another scene. Domain Scene: <" + scene_name + ">, Current Scene: <" + context.scene.name + ">")
            return {'CANCELLED'}


        """
        for scene in bpy.data.scenes:
            for obj in scene.objects:
                if obj.flip_fluid.is_domain():
                    domain_count += 1
                    found_domains.append(obj.name + " <scene: " + scene.name + ">")
        """

        _select_make_active(context, domain)
        return {'FINISHED'}


class FlipFluidHelperSelectSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_surface"
    bl_label = "Select Surface"
    bl_description = "Select the fluid surface object"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({'ERROR'}, "Unable to select Surface object: Domain object is not located in the active scene>")
            return {'CANCELLED'}

        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        objects_to_initialize.fluid_surface = True
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        surface_object = dprops.mesh_cache.surface.get_cache_object()
        if surface_object is None:
            self.report({'INFO'}, "Fluid Surface object not found in scene")
            return {'CANCELLED'}
        _select_make_active(context, surface_object)
        return {'FINISHED'}


class FlipFluidHelperSelectFluidParticles(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_fluid_particles"
    bl_label = "Select Fluid Particles"
    bl_description = "Select the fluid particles object"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({'ERROR'}, "Unable to select Surface object: Domain object is not located in the active scene>")
            return {'CANCELLED'}

        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        objects_to_initialize.fluid_particles = True
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        fluid_particles_object = dprops.mesh_cache.particles.get_cache_object()
        if fluid_particles_object is None:
            self.report({'INFO'}, "Fluid Particles object not found in scene")
            return {'CANCELLED'}
        _select_make_active(context, fluid_particles_object)
        return {'FINISHED'}


class FlipFluidHelperSelectFoam(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_foam"
    bl_label = "Select Foam"
    bl_description = "Select the whitewater foam object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({'ERROR'}, "Unable to select Whitewater Foam object: Domain object is not located in the active scene>")
            return {'CANCELLED'}

        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        objects_to_initialize.whitewater_particles = True
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        foam_object = dprops.mesh_cache.foam.get_cache_object()
        if foam_object is None:
            self.report({'INFO'}, "Whitewater Foam object not found in scene")
            return {'CANCELLED'}
        _select_make_active(context, foam_object)
        return {'FINISHED'}



class FlipFluidHelperSelectBubble(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_bubble"
    bl_label = "Select Bubble"
    bl_description = "Select the whitewater bubble object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({'ERROR'}, "Unable to select Whitewater Bubble object: Domain object is not located in the active scene>")
            return {'CANCELLED'}

        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        objects_to_initialize.whitewater_particles = True
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        bubble_object = dprops.mesh_cache.bubble.get_cache_object()
        if bubble_object is None:
            self.report({'INFO'}, "Whitewater Bubble object not found in scene")
            return {'CANCELLED'}
        _select_make_active(context, bubble_object)
        return {'FINISHED'}


class FlipFluidHelperSelectSpray(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_spray"
    bl_label = "Select Spray"
    bl_description = "Select the whitewater spray object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({'ERROR'}, "Unable to select Whitewater Spray object: Domain object is not located in the active scene>")
            return {'CANCELLED'}

        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        objects_to_initialize.whitewater_particles = True
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        spray_object = dprops.mesh_cache.spray.get_cache_object()
        if spray_object is None:
            self.report({'INFO'}, "Whitewater Spray object not found in scene")
            return {'CANCELLED'}
        _select_make_active(context, spray_object)
        return {'FINISHED'}


class FlipFluidHelperSelectDust(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_dust"
    bl_label = "Select Dust"
    bl_description = "Select the whitewater dust object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({'ERROR'}, "Unable to select Whitewater Dust object: Domain object is not located in the active scene>")
            return {'CANCELLED'}

        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        objects_to_initialize.whitewater_particles = True
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        dust_object = dprops.mesh_cache.dust.get_cache_object()
        if dust_object is None:
            self.report({'INFO'}, "Whitewater Dust object not found in scene")
            return {'CANCELLED'}
        _select_make_active(context, dust_object)
        return {'FINISHED'}


class FlipFluidHelperSelectObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_objects"
    bl_label = "Select Objects"
    bl_description = "Select all FLIP Fluid objects of this type"

    object_type: StringProperty("TYPE_NONE")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        bl_objects = []
        if self.object_type == 'TYPE_OBSTACLE':
            bl_objects = context.scene.flip_fluid.get_obstacle_objects()
        elif self.object_type == 'TYPE_FLUID':
            bl_objects = context.scene.flip_fluid.get_fluid_objects()
        elif self.object_type == 'TYPE_INFLOW':
            bl_objects = context.scene.flip_fluid.get_inflow_objects()
        elif self.object_type == 'TYPE_OUTFLOW':
            bl_objects = context.scene.flip_fluid.get_outflow_objects()
        elif self.object_type == 'TYPE_FORCE_FIELD':
            bl_objects = context.scene.flip_fluid.get_force_field_objects()

        for obj in bpy.context.selected_objects:
            vcu.select_set(obj, False)
        for obj in bl_objects:
            vcu.select_set(obj, True)
        if bpy.context.selected_objects:
            vcu.set_active_object(bpy.context.selected_objects[0])

        return {'FINISHED'}


class FlipFluidHelperCreateDomain(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_create_domain"
    bl_label = "Create Domain"
    bl_description = "Generate a domain object for your scene"


    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.flip_fluid.is_domain_object_set()


    def is_aabb(self, bl_object):
        if len(bl_object.data.vertices) != 8:
            return False

        bbox = flip_fluid_aabb.AABB.from_blender_object(bl_object)
        vertices = [
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
        ]

        result = [False, False, False, False, False, False, False, False]
        eps = 1e-6
        for mv in bl_object.data.vertices:
            v = vcu.element_multiply(bl_object.matrix_world, mv.co)
            for idx,corner in enumerate(vertices):
                vect = v - corner
                if vect.length < eps:
                    result[idx]= True
                    break

        return all(result)


    def set_object_as_domain(self, active_object):
        if active_object.flip_fluid.is_active and active_object.flip_fluid.object_type == 'TYPE_DOMAIN':
            self.report({'ERROR'}, "This object is already set as a FLIP Fluid Domain")
            return
        bpy.ops.flip_fluid_operators.flip_fluid_add()
        active_object.flip_fluid.object_type = 'TYPE_DOMAIN'

        # For object to be highlighted in viewport, depsgraph must be updated and selection
        # re-enabled on the object
        vcu.depsgraph_update()
        vcu.set_active_object(active_object)
        vcu.select_set(active_object, True)

        bpy.ops.ed.undo_push()


    def set_as_inverse_obstacle_and_generate_domain(self, active_object):
        bpy.ops.flip_fluid_operators.flip_fluid_add()
        active_object.flip_fluid.object_type = 'TYPE_OBSTACLE'
        active_object.flip_fluid.obstacle.is_inversed = True
        vcu.set_object_display_type(active_object, 'WIRE')
        active_object.show_wire = True
        active_object.show_all_edges = True

        default_resolution = 65
        pad_factor = 3.5

        bbox = flip_fluid_aabb.AABB.from_blender_object(active_object)
        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
        dx_estimate = max_dim / default_resolution
        pad = pad_factor * dx_estimate

        bbox = bbox.expand(pad)

        vertices = [
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
        ]
        faces = [(0, 2, 6, 4), (1, 3, 7, 5), (0, 1, 5, 4), (2, 3, 7, 6), (0, 1, 3, 2), (4, 5, 7, 6)]

        mesh_data = bpy.data.meshes.new("domain_mesh_data")
        mesh_data.from_pydata(vertices, [], faces)
        domain_object = bpy.data.objects.new("FLIP Domain", mesh_data)
        vcu.link_object(domain_object)

        origin = mathutils.Vector((bbox.x + 0.5 * bbox.xdim, bbox.y + 0.5 * bbox.ydim, bbox.z + 0.5 * bbox.zdim))
        domain_object.data.transform(mathutils.Matrix.Translation(-origin))
        domain_object.matrix_world.translation += origin

        bpy.ops.ed.undo_push()

        vcu.set_active_object(domain_object)
        vcu.select_set(domain_object, True)
        bpy.ops.flip_fluid_operators.flip_fluid_add()
        domain_object.flip_fluid.object_type = 'TYPE_DOMAIN'

        # For object to be highlighted in viewport, depsgraph must be updated and selection
        # re-enabled on the object
        vcu.depsgraph_update()
        vcu.set_active_object(domain_object)
        vcu.select_set(domain_object, True)

        bpy.ops.ed.undo_push()


    def create_new_domain(self):
        bbox = flip_fluid_aabb.AABB(-4, -4, 0, 8, 8, 4)
        vertices = [
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
        ]
        faces = [(0, 2, 6, 4), (1, 3, 7, 5), (0, 1, 5, 4), (2, 3, 7, 6), (0, 1, 3, 2), (4, 5, 7, 6)]

        mesh_data = bpy.data.meshes.new("domain_mesh_data")
        mesh_data.from_pydata(vertices, [], faces)
        domain_object = bpy.data.objects.new("FLIP Domain", mesh_data)
        vcu.link_object(domain_object)

        origin = mathutils.Vector((bbox.x + 0.5 * bbox.xdim, bbox.y + 0.5 * bbox.ydim, bbox.z + 0.5 * bbox.zdim))
        domain_object.data.transform(mathutils.Matrix.Translation(-origin))
        domain_object.matrix_world.translation += origin

        bpy.ops.ed.undo_push()

        vcu.set_active_object(domain_object)
        vcu.select_set(domain_object, True)
        bpy.ops.flip_fluid_operators.flip_fluid_add()
        domain_object.flip_fluid.object_type = 'TYPE_DOMAIN'

        # For object to be highlighted in viewport, depsgraph must be updated and selection
        # re-enabled on the object
        vcu.depsgraph_update()
        vcu.set_active_object(domain_object)
        vcu.select_set(domain_object, True)

        bpy.ops.ed.undo_push()


    def create_domain_to_contain_objects(self, bl_objects):
        xmin, ymin, zmin = float('inf'), float('inf'), float('inf')
        xmax, ymax, zmax = -float('inf'), -float('inf'), -float('inf')
        for obj in bl_objects:
            bbox = flip_fluid_aabb.AABB.from_blender_object(obj)
            xmin = min(bbox.x, xmin)
            ymin = min(bbox.y, ymin)
            zmin = min(bbox.z, zmin)
            xmax = max(bbox.x + bbox.xdim, xmax)
            ymax = max(bbox.y + bbox.ydim, ymax)
            zmax = max(bbox.z + bbox.zdim, zmax)
        bbox = flip_fluid_aabb.AABB(xmin, ymin, zmin, xmax - xmin, ymax - ymin, zmax - zmin)
        if bbox.is_empty():
            bbox.expand(1.0)

        default_resolution = 65
        ceiling_pad_factor = 5.0

        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
        dx_estimate = max_dim / default_resolution

        xpad = 2.0
        ypad = 2.0
        ceiling_pad = ceiling_pad_factor * dx_estimate
        floor_pad = 1.5

        bbox.x -= 0.5 * xpad
        bbox.y -= 0.5 * ypad
        bbox.z -= floor_pad
        bbox.xdim += xpad
        bbox.ydim += ypad
        bbox.zdim += ceiling_pad
        bbox.zdim += floor_pad

        drop_to_ground_ratio = 0.5
        if bbox.z > 0.0:
            dist_to_ground = bbox.z
            if dist_to_ground < drop_to_ground_ratio * max_dim:
                bbox.z = 0.0
                bbox.zdim += dist_to_ground

        vertices = [
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z)),
            mathutils.Vector((bbox.x,             bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y,             bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x,             bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
            mathutils.Vector((bbox.x + bbox.xdim, bbox.y + bbox.ydim, bbox.z + bbox.zdim)),
        ]
        faces = [(0, 2, 6, 4), (1, 3, 7, 5), (0, 1, 5, 4), (2, 3, 7, 6), (0, 1, 3, 2), (4, 5, 7, 6)]

        mesh_data = bpy.data.meshes.new("domain_mesh_data")
        mesh_data.from_pydata(vertices, [], faces)
        domain_object = bpy.data.objects.new("FLIP Domain", mesh_data)
        vcu.link_object(domain_object)

        origin = mathutils.Vector((bbox.x + 0.5 * bbox.xdim, bbox.y + 0.5 * bbox.ydim, bbox.z + 0.5 * bbox.zdim))
        domain_object.data.transform(mathutils.Matrix.Translation(-origin))
        domain_object.matrix_world.translation += origin

        bpy.ops.ed.undo_push()

        vcu.set_active_object(domain_object)
        vcu.select_set(domain_object, True)
        bpy.ops.flip_fluid_operators.flip_fluid_add()
        domain_object.flip_fluid.object_type = 'TYPE_DOMAIN'

        # For object to be highlighted in viewport, depsgraph must be updated and selection
        # re-enabled on the object
        vcu.depsgraph_update()
        vcu.set_active_object(domain_object)
        vcu.select_set(domain_object, True)

        bpy.ops.ed.undo_push()


    def filter_valid_selected_objects(self):
        valid_selected_objects = []
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH' or obj.type == 'EMPTY' or obj.type == 'CURVE':
                valid_selected_objects.append(obj)
        valid_active_object = vcu.get_active_object()
        if valid_active_object is not None:
            if valid_active_object.type != 'MESH' or valid_active_object.type != 'EMPTY' or valid_active_object.type != 'CURVE':
                if valid_selected_objects:
                    valid_active_object = valid_selected_objects[0]
                else:
                    valid_active_object = None
        if valid_active_object is not None:
            vcu.set_active_object(valid_active_object)

        return valid_active_object, valid_selected_objects


    def adjust_resolution_for_small_objects(self):
        simulation_objects = bpy.context.scene.flip_fluid.get_simulation_objects()
        if not simulation_objects:
            return

        bl_domain = bpy.context.scene.flip_fluid.get_domain_object()
        if bl_domain is None:
            return
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        resolution = dprops.simulation.resolution
        bbox = flip_fluid_aabb.AABB.from_blender_object(bl_domain)
        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
        dx_estimate = max_dim / resolution

        min_object_width = float('inf')
        eps = 0.01
        for obj in simulation_objects:
            if obj.flip_fluid.is_force_field() and obj.flip_fluid.force_field.force_field_type != 'FORCE_FIELD_TYPE_VOLUME':
                # Force field objects that are not volume force fields should not affect resolution
                continue
            obj_bbox = flip_fluid_aabb.AABB.from_blender_object(obj)
            min_width = min(obj_bbox.xdim, obj_bbox.ydim, obj_bbox.zdim)
            min_width = max(min_width, eps)
            min_object_width = min(min_width, min_object_width)

        min_coverage_factor = 2.5
        min_coverage_width = min_coverage_factor * dx_estimate
        if min_object_width < min_coverage_width:
            max_suggested_resolution = 400
            new_resolution = resolution * (min_coverage_width / min_object_width)
            dprops.simulation.resolution = min(math.ceil(new_resolution), max_suggested_resolution)


    def execute(self, context):
        if bpy.context.scene.flip_fluid.is_domain_object_set():
            self.report({'ERROR'}, "Scene already contains a domain object")
            return {'CANCELLED'}

        active_object, selected_objects = self.filter_valid_selected_objects()
        if len(selected_objects) == 0:
            simulation_objects = bpy.context.scene.flip_fluid.get_simulation_objects()
            if simulation_objects:
                self.create_domain_to_contain_objects(simulation_objects)
            else:
                self.create_new_domain()

        elif len(selected_objects) == 1:
            ffprops = active_object.flip_fluid
            if active_object.type != 'MESH' or (ffprops.is_active and ffprops.object_type != 'TYPE_NONE'):
                self.create_domain_to_contain_objects(selected_objects)
            elif self.is_aabb(active_object):
                self.set_object_as_domain(active_object)
            else:
                self.set_as_inverse_obstacle_and_generate_domain(active_object)

        elif len(selected_objects) > 1:
            self.create_domain_to_contain_objects(selected_objects)

        self.adjust_resolution_for_small_objects()

        return {'FINISHED'}


# Returns the lowest z-value of the object's bounding box in world space
def get_object_bottom_z_world(obj):
    min_z = float('inf')
    for corner in obj.bound_box:
        world_corner = obj.matrix_world @ Vector(corner)
        if world_corner.z < min_z:
            min_z = world_corner.z
    return min_z

class FlipFluidHelperAddObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_add_objects"
    bl_label = "Add Objects"
    bl_description = "Add selected objects as FLIP Fluid objects"

    object_type: StringProperty("TYPE_NONE")

    @classmethod
    def poll(cls, context):
        # Prevent changing the domain object type if a simulation is running
        if len(context.selected_objects) == 1:
            obj = context.selected_objects[0]
            if obj.flip_fluid.is_domain():
                if obj.flip_fluid.domain.bake.is_simulation_running:
                    return False

        # Allow operation only for valid object types
        for obj in context.selected_objects:
            if obj.type in {'MESH', 'CURVE', 'EMPTY'}:
                return True

        return False

    def execute(self, context):
        # Store the original active object
        original_active_object = vcu.get_active_object(context)

        for obj in context.selected_objects:
            # Force Field can only be applied to MESH, EMPTY, or CURVE
            if self.object_type == 'TYPE_FORCE_FIELD':
                if obj.type not in {'MESH', 'EMPTY', 'CURVE'}:
                    continue
            else:
                # For other types, only MESH objects are valid
                if obj.type != 'MESH':
                    continue

            # Prevent changing the domain type if the simulation is running
            if obj.flip_fluid.is_domain() and obj.flip_fluid.domain.bake.is_simulation_running:
                continue

            # If the selected object is a domain and the type is Fluid or Inflow
            if obj.flip_fluid.is_domain() and self.object_type in {'TYPE_FLUID', 'TYPE_INFLOW'}:
                # Set the domain object as active
                vcu.set_active_object(obj, context)
                # Create a new cube at the domain's location
                bpy.ops.mesh.primitive_cube_add(align='WORLD', location=obj.location, scale=(1, 1, 1))
                new_obj = context.view_layer.objects.active

                # Copy the rotation of the domain object
                new_obj.rotation_euler = obj.rotation_euler

                # Match dimensions and scale the Z-axis to 1/4 of the domain's scale
                new_obj.dimensions = obj.dimensions
                new_obj.scale.z = max(obj.scale.z * 0.25, 0.001)

                # Update the scene to recalculate the bounding box
                context.view_layer.update()

                # Align the bottom of the new object with the bottom of the domain object
                domain_bottom_z = get_object_bottom_z_world(obj)
                new_obj_bottom_z = get_object_bottom_z_world(new_obj)
                new_obj.location.z += (domain_bottom_z - new_obj_bottom_z)

                # Set the new object as active and assign FLIP Fluid properties
                vcu.set_active_object(new_obj, context)
                bpy.ops.flip_fluid_operators.flip_fluid_add()
                new_obj.flip_fluid.object_type = self.object_type
            else:
                # For all other object types, directly assign FLIP Fluid properties
                vcu.set_active_object(obj, context)
                bpy.ops.flip_fluid_operators.flip_fluid_add()
                obj.flip_fluid.object_type = self.object_type

        # Restore the original active object
        vcu.set_active_object(original_active_object, context)
        return {'FINISHED'}


class FlipFluidHelperRemoveObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_remove_objects"
    bl_label = "Remove Objects"
    bl_description = "Remove selected objects from FLIP Fluid simulation"

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) == 1:
            # Don't let user set domain object as another type while simulation is running
            obj = context.selected_objects[0]
            if obj.flip_fluid.is_domain():
                if obj.flip_fluid.domain.bake.is_simulation_running:
                    return False
        for obj in context.selected_objects:
            if obj.flip_fluid.is_active:
                return True
        return False


    def execute(self, context):
        original_active_object = vcu.get_active_object(context)
        for obj in context.selected_objects:
            if not (obj.type == 'MESH' or obj.type == 'EMPTY' or obj.type == 'CURVE'):
                continue
            if obj.flip_fluid.is_domain() and obj.flip_fluid.domain.bake.is_simulation_running:
                # Ignore removing domain type if a simulation is running
                continue
            if obj.flip_fluid.is_domain() and not obj.flip_fluid.domain.bake.is_simulation_running:
                obj.flip_fluid.domain.mesh_cache.delete_cache_objects()
            vcu.set_active_object(obj, context)
            bpy.ops.flip_fluid_operators.flip_fluid_remove()
        vcu.set_active_object(original_active_object, context)
        return {'FINISHED'}


class FlipFluidHelperDeleteDomain(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_delete_domain"
    bl_label = "Delete Domain"
    bl_description = ("Delete selected domain objects and remove simulation meshes. This operator will" + 
                      " not delete the cache directory. This operator is recommended for deleting domains as deleting" +
                      " in the viewport may leave behind stray simulation mesh objects")

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) == 1:
            # Don't let user set domain object as another type while simulation is running
            obj = context.selected_objects[0]
            if obj.flip_fluid.is_domain():
                if obj.flip_fluid.domain.bake.is_simulation_running:
                    return False
        for obj in context.selected_objects:
            if obj.flip_fluid.is_active and obj.flip_fluid.is_domain():
                return True
        return False


    def delete_domain(self, context, domain_name):
        domain_object = bpy.data.objects.get(domain_name)
        mesh_cache = domain_object.flip_fluid.domain.mesh_cache
        mesh_cache.delete_cache_objects()
        vcu.delete_object(domain_object, remove_mesh_data=False)


    def execute(self, context):
        domain_object_names = []
        for obj in context.selected_objects:
            if obj.flip_fluid.is_active and obj.flip_fluid.is_domain() and not obj.flip_fluid.domain.bake.is_simulation_running:
                domain_object_names.append(obj.name)

        for domain_name in domain_object_names:
            self.delete_domain(context, domain_name)
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidHelperDeleteSurfaceObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_delete_surface_objects"
    bl_label = "Delete Fluid Surface Mesh Objects"
    bl_description = ("Delete fluid surface mesh object." + 
                      " This object can be re-initialized by toggling the 'Enable Surface Mesh Generation'" + 
                      " feature off/on. This operator will not delete any data from the simulation cache." + 
                      " Warning: deleting this object will also remove any modifications such as added" + 
                      " modifiers and materials")

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_properties() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.delete_surface_cache_objects()
        self.report({'INFO'}, "Deleted fluid surface mesh object")
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidHelperDeleteParticleObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_delete_particle_objects"
    bl_label = "Delete Fluid Particle Mesh Objects"
    bl_description = ("Delete fluid particle mesh object." + 
                      " This object can be re-initialized by toggling the 'Enable Fluid Particle Export'" + 
                      " feature off/on. This operator will not delete any data from the simulation cache." + 
                      " Warning: deleting this object will also remove any modifications such as added" + 
                      " modifiers and materials")

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_properties() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.delete_particle_cache_objects()
        self.report({'INFO'}, "Deleted fluid particle mesh object")
        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidHelperDeleteWhitewaterObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_delete_whitewater_objects"
    bl_label = "Delete Whitewater Mesh Objects"
    bl_description = ("Delete any foam/bubble/spray/dust whitewater mesh objects." + 
                      " These objects can be re-initialized by toggling the 'Enable Whitewater Simulation'" + 
                      " feature off/on. This operator will not delete any data from the simulation cache." + 
                      " Warning: deleting these objects will also remove any modifications such as added" + 
                      " modifiers and materials")

    whitewater_type: StringProperty("TYPE_ALL")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_properties() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.delete_whitewater_cache_objects(whitewater_type=self.whitewater_type)

        if self.whitewater_type == "TYPE_ALL":
            self.report({'INFO'}, "Deleted foam, bubble, spray, and dust whitewater mesh objects")
        elif self.whitewater_type == "TYPE_FOAM":
            self.report({'INFO'}, "Deleted foam whitewater mesh objects")
        elif self.whitewater_type == "TYPE_BUBBLE":
            self.report({'INFO'}, "Deleted bubble whitewater mesh objects")
        elif self.whitewater_type == "TYPE_SPRAY":
            self.report({'INFO'}, "Deleted spray whitewater mesh objects")
        elif self.whitewater_type == "TYPE_DUST":
            self.report({'INFO'}, "Deleted dust whitewater mesh objects")

        return {'FINISHED'}


    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class FlipFluidHelperOrganizeOutliner(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_organize_outliner"
    bl_label = "Organize Outliner"
    bl_description = "Organize simulation objects into separate collections based on FLIP Fluid object type"


    @classmethod
    def poll(cls, context):
        return True


    def initialize_child_collection(self, context, child_name, parent_collection):
        child_collection = bpy.data.collections.get(child_name)
        if child_collection is None:
            child_collection = bpy.data.collections.new(child_name)
            parent_collection.children.link(child_collection)
        return child_collection


    def organize_object_type(self, context, bl_objects, collection_name):
        if not bl_objects:
            return
        flip_fluid_collection = vcu.get_flip_fluids_collection(context)
        object_collection = self.initialize_child_collection(context, collection_name, flip_fluid_collection)
        for obj in bl_objects:
            if not obj.name in object_collection.objects:
                object_collection.objects.link(obj)
        return object_collection


    def execute(self, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        simulation_objects = context.scene.flip_fluid.get_simulation_objects()
        if not domain_object and not simulation_objects:
            return {'FINISHED'}

        bpy.ops.flip_fluid_operators.helper_undo_organize_outliner()

        if domain_object:
            self.organize_object_type(context, [domain_object], "DOMAIN")

        obstacle_objects = context.scene.flip_fluid.get_obstacle_objects()
        self.organize_object_type(context, obstacle_objects, "OBSTACLE")

        fluid_objects = context.scene.flip_fluid.get_fluid_objects()
        self.organize_object_type(context, fluid_objects, "FLUID")

        fluid_target_objects = []
        for obj in fluid_objects:
            props = obj.flip_fluid.get_property_group()
            if props.is_target_valid():
                bl_target = props.get_target_object()
                if bl_target is not None:
                    fluid_target_objects.append(bl_target)
        self.organize_object_type(context, fluid_target_objects, "FLUID")

        inflow_objects = context.scene.flip_fluid.get_inflow_objects()
        self.organize_object_type(context, inflow_objects, "INFLOW")

        inflow_target_objects = []
        for obj in inflow_objects:
            props = obj.flip_fluid.get_property_group()
            if props.is_target_valid():
                bl_target = props.get_target_object()
                if bl_target is not None:
                    inflow_target_objects.append(bl_target)
        self.organize_object_type(context, inflow_target_objects, "INFLOW")

        outflow_objects = context.scene.flip_fluid.get_outflow_objects()
        self.organize_object_type(context, outflow_objects, "OUTFLOW")

        force_objects = context.scene.flip_fluid.get_force_field_objects()
        self.organize_object_type(context, force_objects, "FORCE")

        meshing_volume_objects = []
        if domain_object:
            dprops = context.scene.flip_fluid.get_domain_properties()
            if dprops.surface.is_meshing_volume_object_valid():
                bl_meshing_volume = dprops.surface.get_meshing_volume_object()
                if bl_meshing_volume is not None:
                    meshing_volume_objects.append(bl_meshing_volume)
        self.organize_object_type(context, meshing_volume_objects, "MESHING_VOLUME")

        all_objects = []
        if domain_object:
            all_objects += [domain_object]
        all_objects += simulation_objects + fluid_target_objects + inflow_target_objects + meshing_volume_objects
        all_collection = self.organize_object_type(context, all_objects, "ALL")

        flip_fluid_collection = vcu.get_flip_fluids_collection(context)
        for obj in flip_fluid_collection.objects:
            if obj.name in all_collection.objects:
                flip_fluid_collection.objects.unlink(obj)

        default_collections = [bpy.context.scene.collection, bpy.data.collections.get("Collection")]
        for default_collection in default_collections:
            if default_collection is not None:
                for obj in default_collection.objects:
                    if obj.name in all_collection.objects:
                        default_collection.objects.unlink(obj)

        return {'FINISHED'}


class FlipFluidHelperSeparateFLIPMeshes(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_separate_flip_meshes"
    bl_label = "FLIP Meshes to Collections"
    bl_description = ("Separate the fluid surface and whitewater meshes into separate collections. Useful for" +
        " separating simulation mesh objects into view and render layers")


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def initialize_child_collection(self, context, child_name, parent_collection):
        child_collection = bpy.data.collections.get(child_name)
        if child_collection is None:
            child_collection = bpy.data.collections.new(child_name)
            parent_collection.children.link(child_collection)
        return child_collection


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}

        mesh_collection = vcu.get_flip_mesh_collection(context)

        surface_object = dprops.mesh_cache.surface.get_cache_object()
        if surface_object is not None:
            collection = self.initialize_child_collection(context, "SURFACE", mesh_collection)
            if not surface_object.name in collection.objects:
                collection.objects.link(surface_object)
            if surface_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(surface_object)

        fluid_particle_object = dprops.mesh_cache.particles.get_cache_object()
        if fluid_particle_object is not None:
            collection = self.initialize_child_collection(context, "FLUID_PARTICLES", mesh_collection)
            if not fluid_particle_object.name in collection.objects:
                collection.objects.link(fluid_particle_object)
            if fluid_particle_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(fluid_particle_object)

        foam_object = dprops.mesh_cache.foam.get_cache_object()
        if foam_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not foam_object.name in collection.objects:
                collection.objects.link(foam_object)
            if foam_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(foam_object)

        bubble_object = dprops.mesh_cache.bubble.get_cache_object()
        if bubble_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not bubble_object.name in collection.objects:
                collection.objects.link(bubble_object)
            if bubble_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(bubble_object)

        spray_object = dprops.mesh_cache.spray.get_cache_object()
        if spray_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not spray_object.name in collection.objects:
                collection.objects.link(spray_object)
            if spray_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(spray_object)

        dust_object = dprops.mesh_cache.dust.get_cache_object()
        if dust_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not dust_object.name in collection.objects:
                collection.objects.link(dust_object)
            if dust_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(dust_object)

        return {'FINISHED'}


class FlipFluidHelperUndoOrganizeOutliner(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_undo_organize_outliner"
    bl_label = "Unlink FLIP Object Collections"
    bl_description = ("Unlink all FLIP Fluid objects from organized collections and place into the FLIPFluid" + 
        " collection. This operation will not delete any objects")


    @classmethod
    def poll(cls, context):
        return True


    def unlink_collection(self, context, collection_name):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            return

        parent_collection = vcu.get_flip_fluids_collection(context)
        if collection.name not in parent_collection.children.keys():
            return

        for obj in collection.objects:
            if obj.name not in parent_collection.objects:
                parent_collection.objects.link(obj)
            collection.objects.unlink(obj)

        if not collection.objects and not collection.children:
            parent_collection.children.unlink(collection)
            bpy.data.collections.remove(collection)


    def execute(self, context):
        collection_names = [
            "DOMAIN",
            "OBSTACLE",
            "FLUID",
            "INFLOW",
            "OUTFLOW",
            "FORCE",
            "MESHING_VOLUME",
            "ALL",
        ]

        for cname in collection_names:
            self.unlink_collection(context, cname)

        return {'FINISHED'}


class FlipFluidHelperUndoSeparateFLIPMeshes(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_undo_separate_flip_meshes"
    bl_label = "Unlink FLIP Mesh Collections"
    bl_description = ("Unlink all fluid surface and whitewater meshes from organized collections and place into the FLIPMeshes" + 
        " collection. This operation will not delete any objects")


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def unlink_collection(self, context, collection_name):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            return

        parent_collection = vcu.get_flip_mesh_collection(context)
        if collection.name not in parent_collection.children.keys():
            return

        for obj in collection.objects:
            if obj.name not in parent_collection.objects:
                parent_collection.objects.link(obj)
            collection.objects.unlink(obj)

        if not collection.objects and not collection.children:
            parent_collection.children.unlink(collection)
            bpy.data.collections.remove(collection)


    def execute(self, context):
        collection_names = [
            "SURFACE",
            "FLUID_PARTICLES",
            "WHITEWATER",
            "FOAM",
            "BUBBLE",
            "SPRAY",
            "DUST",
        ]

        for cname in collection_names:
            self.unlink_collection(context, cname)

        return {'FINISHED'}


class FlipFluidHelperSetObjectViewportDisplay(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_set_object_viewport_display"
    bl_label = "Object Viewport Display"
    bl_description = "Set how selected objects are displayed/rendered in the viewport"

    display_mode: StringProperty("TYPE_NONE")


    @classmethod
    def poll(cls, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                return True
        return False


    def execute(self, context):
        for obj in context.selected_objects:
            if not obj.type == 'MESH':
                continue
            if self.display_mode == 'DISPLAY_MODE_SOLID':
                vcu.set_object_display_type(obj, 'TEXTURED')
                obj.show_wire = False
                obj.show_all_edges = False
                
            elif self.display_mode == 'DISPLAY_MODE_WIREFRAME':
                vcu.set_object_display_type(obj, 'WIRE')
                obj.show_wire = True
                obj.show_all_edges = True

        return {'FINISHED'}


class FlipFluidHelperSetObjectRenderDisplay(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_set_object_render_display"
    bl_label = "Object Render Display"
    bl_description = "Set selected objects visiblility in the render"

    hide_render: BoolProperty(False)


    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)


    def execute(self, context):
        for obj in context.selected_objects:
            obj.hide_render = self.hide_render

        return {'FINISHED'}


class FlipFluidHelperLoadLastFrame(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_load_last_frame"
    bl_label = "Load Last Frame"
    bl_description = "Load the most recently computed frame"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        if render.is_rendering():
            # Setting a frame during render will disrupt the render process
            return {'CANCELLED'}

        if not context.scene.flip_fluid.is_domain_in_active_scene():
            # Active scene does not contain the simulation and should not load the frame
            return {'CANCELLED'}


        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_dir = dprops.cache.get_cache_abspath()
        bakefiles_dir = os.path.join(cache_dir, "bakefiles")
        if not os.path.exists(bakefiles_dir):
            return {'CANCELLED'}

        bakefiles = os.listdir(bakefiles_dir)
        max_frameno = -1
        for f in bakefiles:
            base = f.split(".")[0]
            try:
                frameno = int(base[-6:])
            except ValueError:
                continue
            max_frameno = max(frameno, max_frameno)

        if max_frameno != -1:
            timeline_frame = render.get_timeline_frame_from_simulation_frame(max_frameno)
            context.scene.frame_set(timeline_frame)

        return {'FINISHED'}


class FlipFluidEnableFluidParticleMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_fluid_particle_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_fluid_particle_output")


class FlipFluidEnableFluidParticleOutput(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_fluid_particle_output"
    bl_label = "Enable Fluid Particle Output"
    bl_description = "Enable Fluid Particle Output"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.particles.enable_fluid_particle_output = True
        return {'FINISHED'}


class FlipFluidDisplayEnableFluidParticlesTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.display_enable_fluid_particles_tooltip"
    bl_label = "Enable Fluid Particles Tooltip"
    bl_description = "Enable Fluid Particle Output"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_fluid_particle_menu")
        return {'FINISHED'}


class FlipFluidEnableWhitewaterMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_whitewater_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_whitewater_simulation")


class FlipFluidEnableWhitewaterSimulation(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_whitewater_simulation"
    bl_label = "Enable Whitewater Simulation"
    bl_description = "Enable Whitewater Simulation"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.whitewater.enable_whitewater_simulation = True
        return {'FINISHED'}


class FlipFluidDisplayEnableWhitewaterTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.display_enable_whitewater_tooltip"
    bl_label = "Enable Whitewater Tooltip"
    bl_description = "Enable whitewater simulation"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_whitewater_menu")
        return {'FINISHED'}


class FlipFluidEnableColorAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_color_attribute"
    bl_label = "Enable Color Attribute"
    bl_description = "Enable color attribute in the Domain FLIP Fluid Surface and FLIP Fluid Particles panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.surface.enable_color_attribute = True
        dprops.particles.enable_fluid_particle_color_attribute = True
        return {'FINISHED'}


class FlipFluidEnableColorMixAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_color_mix_attribute"
    bl_label = "Enable Color Attribute + Mixing"
    bl_description = "Enable color attribute and color mixing in the Domain FLIP Fluid Surface and FLIP Fluid Particles panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.surface.enable_color_attribute = True
        dprops.surface.enable_color_attribute_mixing = True
        dprops.particles.enable_fluid_particle_color_attribute = True
        return {'FINISHED'}


class FlipFluidEnableColorAttributeMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_color_attribute_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_color_attribute")
        self.layout.operator("flip_fluid_operators.enable_color_mix_attribute")


class FlipFluidEnableColorAttributeTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_color_attribute_tooltip"
    bl_label = "Enable Color Attribute"
    bl_description = "Click to enable the color attribute in the Domain FLIP Fluid Surface and FLIP Fluid Particles panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_color_attribute_menu")
        return {'FINISHED'}


class FlipFluidEnableViscosityAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_viscosity_attribute"
    bl_label = "Enable Viscosity Attribute"
    bl_description = "Enable viscosity solver and variable viscosity attribute in the Domain World panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.world.enable_viscosity = True
        dprops.surface.enable_viscosity_attribute = True
        return {'FINISHED'}


class FlipFluidEnableViscosityAttributeMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_viscosity_attribute_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_viscosity_attribute")


class FlipFluidEnableViscosityAttributeTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_viscosity_attribute_tooltip"
    bl_label = "Enable Viscosity Attribute"
    bl_description = "Click to enable the viscosity solver and variable viscosity attribute in the Domain FLIP Fluid World panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_viscosity_attribute_menu")
        return {'FINISHED'}


class FlipFluidEnableDensityAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_density_attribute"
    bl_label = "Enable Density Attribute"
    bl_description = "Enable variable density solver and attribute in the Domain World panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.world.enable_density_attribute = True
        return {'FINISHED'}


class FlipFluidEnableDensityAttributeMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_density_attribute_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_density_attribute")


class FlipFluidEnableDensityAttributeTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_density_attribute_tooltip"
    bl_label = "Enable Density Attribute"
    bl_description = "Click to enable the variable density solver and attribute in the Domain World panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_density_attribute_menu")
        return {'FINISHED'}


class FlipFluidEnableLifetimeAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_lifetime_attribute"
    bl_label = "Enable Lifetime Attribute"
    bl_description = "Enable lifetime attribute in the Domain Surface and/or Domain Particles panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.surface.enable_lifetime_attribute = True
        dprops.particles.enable_fluid_particle_lifetime_attribute = True
        dprops.whitewater.enable_lifetime_attribute = True
        return {'FINISHED'}


class FlipFluidEnableLifetimeAttributeMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_lifetime_attribute_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_lifetime_attribute")


class FlipFluidEnableLifetimeAttributeTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_lifetime_attribute_tooltip"
    bl_label = "Enable Lifetime Attribute"
    bl_description = "Click to enable the lifetime attribute in the Domain Surface and/or Domain Particles panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_lifetime_attribute_menu")
        return {'FINISHED'}


class FlipFluidEnableSourceIDAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_source_id_attribute"
    bl_label = "Enable Source ID Attribute"
    bl_description = "Enable source ID attribute in the Domain Surface and/or Particles panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.surface.enable_source_id_attribute = True
        dprops.particles.enable_fluid_particle_source_id_attribute = True
        return {'FINISHED'}


class FlipFluidEnableSourceIDAttributeMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_source_id_attribute_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_source_id_attribute")


class FlipFluidEnableSourceIDAttributeTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_source_id_attribute_tooltip"
    bl_label = "Enable Source ID Attribute"
    bl_description = "Click to enable the source ID attribute in the Domain Surface and/or Domain Particles panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_source_id_attribute_menu")
        return {'FINISHED'}


def is_geometry_node_point_cloud_detected(bl_mesh_cache_object=None):
    try:
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if bl_mesh_cache_object is None:
            cache_objects = [
                dprops.mesh_cache.foam.get_cache_object(),
                dprops.mesh_cache.bubble.get_cache_object(),
                dprops.mesh_cache.spray.get_cache_object(),
                dprops.mesh_cache.dust.get_cache_object(),
                ]
        else:
            cache_objects = [bl_mesh_cache_object]

        cache_objects = [c for c in cache_objects if c is not None]

        search_string_start1 = "FF_GeometryNodesWhitewater"
        search_string_start2 = "FF_GeometryNodesFluidParticles"
        for cobj in cache_objects:
            for mod in cobj.modifiers:
                is_name_correct = str(mod.name).startswith(search_string_start1) or str(mod.name).startswith(search_string_start2)
                if mod.type == 'NODES' and is_name_correct:
                    return True
    except:
        # Blender may be in the incorrect context for this operation
        print("FLIP Fluids Warning: incorrect context for helper_operators.is_geometry_node_point_cloud_detected()")
        return False

    return False



def update_geometry_node_material(bl_object, resource_name):
    if bl_object is None:
        return

    gn_modifier = None
    for mod in bl_object.modifiers:
        if mod.type == 'NODES' and mod.name == resource_name:
            gn_modifier = mod
            break

    if gn_modifier is not None:
        try:
            # Depending on FLIP Fluids version, the GN set up may not
            # have an Input_5
            gn_modifier["Input_5"] = bl_object.active_material
        except:
            pass


def add_geometry_node_modifier(target_object, resource_filepath, resource_name):
    for mod in target_object.modifiers:
        if mod.type == 'NODES' and mod.name == resource_name:
            # Already added
            return mod
        
    node_group = bpy.data.node_groups.get(resource_name)
    if node_group is None:
        is_resource_found = False
        with bpy.data.libraries.load(resource_filepath) as (data_from, data_to):
            resource = [name for name in data_from.node_groups if name == resource_name]
            if resource:
                is_resource_found = True
                data_to.node_groups = resource
                
        if not is_resource_found:
            return None
        
        imported_resource_name = data_to.node_groups[0].name
    else:
        # already imported
        imported_resource_name = node_group.name
        
    gn_modifier = target_object.modifiers.new(resource_name, type="NODES")
    gn_modifier.node_group = bpy.data.node_groups.get(imported_resource_name)
    return gn_modifier


def get_geometry_node_modifier(target_object, resource_name):
    for mod in target_object.modifiers:
        if mod.type == 'NODES' and mod.name == resource_name:
            return mod
    return None


class FlipFluidHelperInitializeMotionBlur(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_initialize_motion_blur"
    bl_label = "Initialize Motion Blur"
    bl_description = ("Initialize all settings and Geometry Node groups required for motion blur rendering." + 
                      " This will be applied to the fluid surface, fluid particles, and whitewater particles if enabled." + 
                      " Node groups can be viewed in the geometry nodes editor and modifier")

    resource_prefix: StringProperty(default="FF_GeometryNodes")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def apply_modifier_settings(self, target_object, gn_modifier):
        gn_name = gn_modifier.name
        if gn_name.startswith("FF_GeometryNodesSurface"):
            # Depending on FLIP Fluids version, the GN set up may not
            # have these inputs. Available in FLIP Fluids 1.7.2 or later.
            try:
                # Enable Motion Blur
                gn_modifier["Input_6"] = True
            except:
                pass

        if gn_name.startswith("FF_GeometryNodesWhitewater") or gn_name.startswith("FF_GeometryNodesFluidParticles"):
            # Depending on FLIP Fluids version, the GN set up may not
            # have these inputs. Available in FLIP Fluids 1.7.2 or later.
            try:
                # Material
                gn_modifier["Input_5"] = target_object.active_material
            except:
                pass

            try:
                # Enable Motion Blur
                gn_modifier["Input_8"] = True
            except:
                pass


    def execute(self, context):
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"}, 
                         "Active scene must contain domain object to use this operator. Select the scene that contains the domain object and try again.")
            return {'CANCELLED'}
        
        unsupported_render_engines = ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH']
        if context.scene.render.engine in unsupported_render_engines:
            context.scene.render.engine = 'CYCLES'
            self.report({'INFO'}, "Setting render engine to Cycles")
        if not context.scene.render.use_motion_blur:
            context.scene.render.use_motion_blur = True
            self.report({'INFO'}, "Enabled Cycles motion blur rendering")

        dprops = context.scene.flip_fluid.get_domain_properties()
        if not dprops.surface.enable_velocity_vector_attribute:
            dprops.surface.enable_velocity_vector_attribute = True
            self.report({'INFO'}, "Enabled generation of fluid surface velocity vector attributes in Domain Surface panel (baking required)")

        if not dprops.particles.enable_fluid_particle_velocity_vector_attribute:
            dprops.particles.enable_fluid_particle_velocity_vector_attribute = True
            self.report({'INFO'}, "Enabled generation of fluid particle velocity vector attributes in Domain Particles panel (baking required)")

        if not dprops.whitewater.enable_velocity_vector_attribute:
            dprops.whitewater.enable_velocity_vector_attribute = True
            self.report({'INFO'}, "Enabled generation of whitewater velocity vector attributes in Domain Whitewater (baking required)")

        blend_filename = "geometry_nodes_library.blend"
        surface_resource = self.resource_prefix + "Surface"
        fluid_particle_resource = self.resource_prefix + "FluidParticles"
        whitewater_foam_resource = self.resource_prefix + "WhitewaterFoam"
        whitewater_bubble_resource = self.resource_prefix + "WhitewaterBubble"
        whitewater_spray_resource = self.resource_prefix + "WhitewaterSpray"
        whitewater_dust_resource = self.resource_prefix + "WhitewaterDust"

        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", blend_filename)

        surface_mesh_caches = [dprops.mesh_cache.surface]
        surface_cache_objects = []
        for m in surface_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 surface_cache_objects.append(bl_object)

        fluid_particle_mesh_caches = [dprops.mesh_cache.particles]
        fluid_particle_cache_objects = []
        for m in fluid_particle_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 fluid_particle_cache_objects.append(bl_object)

        whitewater_mesh_caches = [
                dprops.mesh_cache.foam, 
                dprops.mesh_cache.bubble, 
                dprops.mesh_cache.spray, 
                dprops.mesh_cache.dust
                ]
        whitewater_cache_objects = []
        for m in whitewater_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 whitewater_cache_objects.append(bl_object)

        for target_object in surface_cache_objects:
            gn_modifier = add_geometry_node_modifier(target_object, resource_filepath, surface_resource)
            self.apply_modifier_settings(target_object, gn_modifier)
            info_msg = "Initialized " + gn_modifier.name + " Geometry Node modifier on " + target_object.name + " object"
            self.report({'INFO'}, info_msg)

        for target_object in fluid_particle_cache_objects:
            gn_modifier = add_geometry_node_modifier(target_object, resource_filepath, fluid_particle_resource)
            self.apply_modifier_settings(target_object, gn_modifier)
            info_msg = "Initialized " + gn_modifier.name + " Geometry Node modifier on " + target_object.name + " object"
            self.report({'INFO'}, info_msg)

        for target_object in whitewater_cache_objects:
            whitewater_resource = ""
            if target_object == dprops.mesh_cache.foam.get_cache_object():
                whitewater_resource = whitewater_foam_resource
            elif target_object == dprops.mesh_cache.bubble.get_cache_object():
                whitewater_resource = whitewater_bubble_resource
            elif target_object == dprops.mesh_cache.spray.get_cache_object():
                whitewater_resource = whitewater_spray_resource
            elif target_object == dprops.mesh_cache.dust.get_cache_object():
                whitewater_resource = whitewater_dust_resource

            gn_modifier = add_geometry_node_modifier(target_object, resource_filepath, whitewater_resource)
            self.apply_modifier_settings(target_object, gn_modifier)
            info_msg = "Initialized " + gn_modifier.name + " Geometry Node modifier on " + target_object.name + " object"
            self.report({'INFO'}, info_msg)

        for target_object in surface_cache_objects + fluid_particle_cache_objects + whitewater_cache_objects:
            if not target_object.cycles.use_motion_blur:
                target_object.cycles.use_motion_blur = True
                info_msg = "Enabled motion blur rendering on " + target_object.name + " object"
                self.report({'INFO'}, info_msg)

        self.report({'INFO'}, "Finished initializing motion blur geometry node groups and settings")

        return {'FINISHED'}


class FlipFluidHelperRemoveMotionBlur(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_remove_motion_blur"
    bl_label = "Remove Motion Blur"
    bl_description = ("Remove the motion blur setup from the fluid surface, fluid particles, and whitewater" +
            " particles (if enabled). This will remove the motion blur Geometry Node" +
            " groups and disable object motion blur for the surface/whitewater. Note: this" +
            " operator will not disable the Domain surface/particles/whitewater velocity attribute settings")


    resource_prefix: StringProperty(default="FF_GeometryNodes")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"}, 
                         "Active scene must contain domain object to use this operator. Select the scene that contains the domain object and try again.")
            return {'CANCELLED'}

        dprops = context.scene.flip_fluid.get_domain_properties()

        surface_mesh_caches = [dprops.mesh_cache.surface]
        surface_cache_objects = []
        for m in surface_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 surface_cache_objects.append(bl_object)

        fluid_particle_mesh_caches = [dprops.mesh_cache.particles]
        fluid_particle_cache_objects = []
        for m in fluid_particle_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 fluid_particle_cache_objects.append(bl_object)

        whitewater_mesh_caches = [
                dprops.mesh_cache.foam, 
                dprops.mesh_cache.bubble, 
                dprops.mesh_cache.spray, 
                dprops.mesh_cache.dust
                ]
        whitewater_cache_objects = []
        for m in whitewater_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 whitewater_cache_objects.append(bl_object)

        is_setup_modified = False
        cache_objects = surface_cache_objects + fluid_particle_cache_objects + whitewater_cache_objects
        modifier_name_prefix = self.resource_prefix
        for bl_object in cache_objects:
            geometry_node_modifiers = [mod for mod in bl_object.modifiers if mod.type == "NODES"]
            modifiers_to_remove = [mod for mod in geometry_node_modifiers if mod.node_group.name.startswith(modifier_name_prefix)]
            for mod in modifiers_to_remove:
                self.report({'INFO'}, "Removed " + mod.name + " Geometry Node modifier from " + bl_object.name + " object")
                bl_object.modifiers.remove(mod)
                is_setup_modified = True

        for bl_object in cache_objects:
            if bl_object.cycles.use_motion_blur:
                self.report({'INFO'}, "Disabled motion blur rendering on " + bl_object.name + " object")
                bl_object.cycles.use_motion_blur = False
                is_setup_modified = True

        if not is_setup_modified:
            self.report({'INFO'}, "No motion blur setup detected")

        return {'FINISHED'}


class FlipFluidHelperToggleMotionBlurRendering(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_toggle_motion_blur_rendering"
    bl_label = "Toggle Motion Blur Rendering"
    bl_description = ("Toggle motion blur rendering for the simulation meshes on or off. This operator will enable or" +
                      " disable the simulations mesh object and geometry node settings for motion blur rendering")

    enable_motion_blur_rendering: BoolProperty(default=True)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def get_motion_blur_geometry_node_modifier(self, bl_object):
        if bl_object is None:
            return None
        for mod in bl_object.modifiers:
            if mod.type == "NODES" and mod.node_group and mod.node_group.name.startswith("FF_GeometryNodes"):
                return mod


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        enable_status = self.enable_motion_blur_rendering
        enable_string = "ON" if self.enable_motion_blur_rendering else "OFF"

        mesh_caches = [
            dprops.mesh_cache.surface.get_cache_object(),
            dprops.mesh_cache.particles.get_cache_object(),
            dprops.mesh_cache.foam.get_cache_object(),
            dprops.mesh_cache.bubble.get_cache_object(),
            dprops.mesh_cache.spray.get_cache_object(),
            dprops.mesh_cache.dust.get_cache_object()
        ]
        mesh_caches = [bl_object for bl_object in mesh_caches if bl_object is not None]

        for bl_object in mesh_caches:
            if bl_object.cycles.use_motion_blur != enable_status:
                bl_object.cycles.use_motion_blur = enable_status
                self.report({'INFO'}, "Toggled Cycles motion blur rendering on <" + bl_object.name + "> object to " + enable_string)

        for bl_object in mesh_caches:
            gn_modifier = self.get_motion_blur_geometry_node_modifier(bl_object)
            if gn_modifier is None:
                continue
            if "Input_8" in gn_modifier:
                if gn_modifier["Input_8"] != enable_status:
                    gn_modifier["Input_8"] = enable_status
                    self.report({'INFO'}, "Toggled motion blur on <" + gn_modifier.name + "> geometry node modifier to " + enable_string)

        self.report({'INFO'}, "Finished toggling motion blur rendering on simulation meshes " + enable_string)

        return {'FINISHED'}


class FlipFluidHelperUpdateGeometryNodeModifiers(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_update_geometry_node_modifiers"
    bl_label = "Update Geometry Node Modifiers"
    bl_description = ("Update the fluid surface, particle, and whitewater geometry nodes modifiers to the current addon version and transfer settings." + 
                      " This operator will not delete existing FLIP Fluids modifiers or datablocks. Existing modifiers will be renamed with a" + 
                      " BACKUP prefix and disabled in the modifier stack. This backup can be removed if not wanted")

    resource_prefix: StringProperty(default="FF_GeometryNodes")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def transfer_gn_modifer_settings(self, old_gn_modifier, new_gn_modifier, old_new_key_pairs):
        for key in old_new_key_pairs:
            old_key = key[0]
            new_key = key[1]
            if old_key in old_gn_modifier:
                try:
                    new_gn_modifier[new_key] = old_gn_modifier[old_key]
                except:
                    pass


    def transfer_gn_modifier_settings_surface(self, old_gn_modifier, new_gn_modifier):
        # Old Key, New Key
        keys = [
            ("Input_6", "Input_6"),    # Enable Motion Blur
            ("Input_4", "Input_4"),    # Motion Blur Scale
        ]

        self.transfer_gn_modifer_settings(old_gn_modifier, new_gn_modifier, keys)


    def transfer_gn_modifier_settings_fluid_particle(self, old_gn_modifier, new_gn_modifier):
        # Old Key, New Key
        keys = [
            ("Input_5",  "Input_5"),    # Material
            ("Input_8",  "Input_8"),    # Enable Motion Blur
            ("Input_4",  "Input_4"),    # Motion Blur Scale
            ("Input_6",  "Input_6"),    # Particle Scale
            ("Socket_2", "Socket_2"),   # Particle Scale Random
            ("Socket_1", "Socket_1"),   # Fading Width
            ("Socket_0", "Socket_0"),   # Fading Strength
            ("Socket_4", "Socket_4"),   # Fading Density
        ]

        self.transfer_gn_modifer_settings(old_gn_modifier, new_gn_modifier, keys)


    def transfer_gn_modifier_settings_whitewater(self, old_gn_modifier, new_gn_modifier):
        # Old Key, New Key
        keys = [
            ("Input_5",  "Input_5"),    # Material
            ("Input_8",  "Input_8"),    # Enable Motion Blur
            ("Input_4",  "Input_4"),    # Motion Blur Scale
            ("Input_6",  "Input_6"),    # Particle Scale
            ("Socket_2", "Socket_2"),   # Particle Scale Random
            ("Socket_1", "Socket_1"),   # Fading Width
            ("Socket_0", "Socket_0"),   # Fading Strength
            ("Socket_4", "Socket_4"),   # Fading Density
        ]

        self.transfer_gn_modifer_settings(old_gn_modifier, new_gn_modifier, keys)


    def get_ff_geometry_node_modifiers(self, bl_object):
        modifiers = []
        if bl_object is None:
            return modifiers
        for mod in bl_object.modifiers:
            if mod.type == "NODES" and mod.node_group and mod.node_group.name.startswith("FF_GeometryNodes"):
                modifiers.append(mod)
        return modifiers


    def execute(self, context):
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"}, 
                         "Active scene must contain domain object to use this operator. Select the scene that contains the domain object and try again.")
            return {'CANCELLED'}

        dprops = context.scene.flip_fluid.get_domain_properties()

        # Gather Blender cache objects
        surface_mesh_caches = [dprops.mesh_cache.surface]
        surface_cache_objects = []
        for m in surface_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 surface_cache_objects.append(bl_object)

        fluid_particle_mesh_caches = [dprops.mesh_cache.particles]
        fluid_particle_cache_objects = []
        for m in fluid_particle_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 fluid_particle_cache_objects.append(bl_object)

        whitewater_mesh_caches = [
                dprops.mesh_cache.foam, 
                dprops.mesh_cache.bubble, 
                dprops.mesh_cache.spray, 
                dprops.mesh_cache.dust
                ]
        whitewater_cache_objects = []
        for m in whitewater_mesh_caches:
            bl_object = m.get_cache_object()
            if bl_object is not None:
                 whitewater_cache_objects.append(bl_object)

        bl_cache_objects = surface_cache_objects + fluid_particle_cache_objects + whitewater_cache_objects

        # Search for the last FF_GeometryNodes modifier in the stack for each cache object for transferring settings
        surface_gn_modifiers = []
        for bl_object in surface_cache_objects:
            existing_gn_modifiers = self.get_ff_geometry_node_modifiers(bl_object)
            if existing_gn_modifiers:
                surface_gn_modifiers.append(existing_gn_modifiers[-1])
            else:
                surface_gn_modifiers.append(None)

        fluid_particle_gn_modifiers = []
        for bl_object in fluid_particle_cache_objects:
            existing_gn_modifiers = self.get_ff_geometry_node_modifiers(bl_object)
            if existing_gn_modifiers:
                fluid_particle_gn_modifiers.append(existing_gn_modifiers[-1])
            else:
                fluid_particle_gn_modifiers.append(None)

        whitewater_gn_modifiers = []
        for bl_object in whitewater_cache_objects:
            existing_gn_modifiers = self.get_ff_geometry_node_modifiers(bl_object)
            if existing_gn_modifiers:
                whitewater_gn_modifiers.append(existing_gn_modifiers[-1])
            else:
                whitewater_gn_modifiers.append(None)

        # Disable existing FF_GeometryNode modifiers and rename with BACKUP_ prefix
        for bl_object in bl_cache_objects:
            existing_gn_modifiers = self.get_ff_geometry_node_modifiers(bl_object)
            for mod in existing_gn_modifiers:
                mod.show_viewport = False
                mod.show_render = False
                mod.show_expanded = False
                mod.name = "BACKUP_" + mod.name
                mod.node_group.name = "BACKUP_" + mod.node_group.name

        # Initialize current FF_GeometryNode modifiers
        geometry_nodes_library = "geometry_nodes_library.blend"
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", geometry_nodes_library)

        surface_resource = self.resource_prefix + "Surface"
        fluid_particle_resource = self.resource_prefix + "FluidParticles"
        whitewater_foam_resource = self.resource_prefix + "WhitewaterFoam"
        whitewater_bubble_resource = self.resource_prefix + "WhitewaterBubble"
        whitewater_spray_resource = self.resource_prefix + "WhitewaterSpray"
        whitewater_dust_resource = self.resource_prefix + "WhitewaterDust"

        for idx, bl_surface in enumerate(surface_cache_objects):
            old_gn_modifier = surface_gn_modifiers[idx]
            new_gn_modifier = add_geometry_node_modifier(bl_surface, resource_filepath, surface_resource)
            if old_gn_modifier and new_gn_modifier:
                self.transfer_gn_modifier_settings_surface(old_gn_modifier, new_gn_modifier)

        for idx, bl_fluid_particle in enumerate(fluid_particle_cache_objects):
            old_gn_modifier = fluid_particle_gn_modifiers[idx]
            new_gn_modifier = add_geometry_node_modifier(bl_fluid_particle, resource_filepath, fluid_particle_resource)
            if old_gn_modifier and new_gn_modifier:
                self.transfer_gn_modifier_settings_fluid_particle(old_gn_modifier, new_gn_modifier)

        for idx, bl_whitewater in enumerate(whitewater_cache_objects):
            whitewater_resource = ""
            if bl_whitewater == dprops.mesh_cache.foam.get_cache_object():
                whitewater_resource = whitewater_foam_resource
            elif bl_whitewater == dprops.mesh_cache.bubble.get_cache_object():
                whitewater_resource = whitewater_bubble_resource
            elif bl_whitewater == dprops.mesh_cache.spray.get_cache_object():
                whitewater_resource = whitewater_spray_resource
            elif bl_whitewater == dprops.mesh_cache.dust.get_cache_object():
                whitewater_resource = whitewater_dust_resource

            old_gn_modifier = whitewater_gn_modifiers[idx]
            new_gn_modifier = add_geometry_node_modifier(bl_whitewater, resource_filepath, whitewater_resource)
            if old_gn_modifier and new_gn_modifier:
                self.transfer_gn_modifier_settings_whitewater(old_gn_modifier, new_gn_modifier)

        self.report({'INFO'}, "Updated FLIP Fluids Geometry Node Modifiers")

        return {'FINISHED'}


class FlipFluidHelperInitializeCacheObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_initialize_cache_objects"
    bl_label = "Initialize Cache Objects"
    bl_description = ("Initialize simulation meshes, modifiers, and data")

    cache_object_type: StringProperty(default="CACHE_OBJECT_TYPE_NONE")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        objects_to_initialize = flip_fluid_cache.EnabledMeshCacheObjects()
        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_SURFACE':
            objects_to_initialize.fluid_surface = True
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            objects_to_initialize.fluid_particles = True
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_WHITEWATER_PARTICLES':
            objects_to_initialize.whitewater_particles = True
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_DEBUG_OBSTACLE':
            objects_to_initialize.debug_obstacle = True
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_ALL':
            objects_to_initialize.fluid_surface = True
            objects_to_initialize.fluid_particles = True
            objects_to_initialize.whitewater_particles = True
            objects_to_initialize.debug_obstacle = True

        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.mesh_cache.initialize_cache_objects(objects_to_initialize)
        dprops.mesh_cache.initialize_cache_objects_geometry_nodes(objects_to_initialize)

        return {'FINISHED'}


class FlipFluidHelperStableRendering279(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_stable_rendering_279"
    bl_label = "Enable Stable Rendering"
    bl_description = ("Activate to prevent crashes and incorrect results during render."
                      " Activation will automatically set the Render Display Mode to"
                      " 'Full Screen' (Properties > Render > Display) and is a recommendation"
                      " to prevent viewport instability")


    @classmethod
    def poll(cls, context):
        # render.display_mode is only available in Blender 2.79
        # poll() should return false for any other version of Blender
        try:
            return context.scene.render.display_mode != 'SCREEN'
        except:
            return False


    def execute(self, context):
        context.scene.render.display_mode = 'SCREEN'
        return {'FINISHED'}


class FlipFluidHelperStableRendering28(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_stable_rendering_28"
    bl_label = "Enable Stable Rendering"
    bl_description = ("Activate to prevent crashes and incorrect results during render."
                      " Activation will automatically lock the Blender interface"
                      " during render (Blender > Render > Lock Interface) and is highly"
                      " recommended")

    enable_state: BoolProperty(True)


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        context.scene.render.use_lock_interface = self.enable_state
        return {'FINISHED'}


class FlipFluidHelperSetLinearOverrideKeyframes(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_set_linear_override_keyframes"
    bl_label = "Make Keyframes Linear"
    bl_description = ("Automatically set the Override Frame interpolation mode to 'Linear'." +
        " TIP: The interpolation mode can also be set in the Blender Graph Editor when selecting the domain")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object()


    def execute(self, context):
        bl_domain = context.scene.flip_fluid.get_domain_object()
        if bl_domain is None:
            return {'CANCELLED'}
        dprops = context.scene.flip_fluid.get_domain_properties()

        try:
            fcurve = export_utils.get_property_fcurve(bl_domain, "override_frame")
        except AttributeError:
            self.report({'ERROR'}, "Override Frame value must contain keyframes for this operator to function")
            return {'CANCELLED'}

        for kp in fcurve.keyframe_points:
            kp.interpolation = 'LINEAR'

        return {'FINISHED'}


class FlipFluidHelperSaveBlendFile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_save_blend_file"
    bl_label = "Save File"
    bl_description = "Open the Blender file window to save the current .blend file"

    save_as_blend_file: BoolProperty(default=True)


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        if self.save_as_blend_file:
            bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        else: 
            bpy.ops.wm.save_mainfile('INVOKE_DEFAULT')
        return {'FINISHED'}


def _get_object_motion_type(obj):
        props = obj.flip_fluid.get_property_group()
        if hasattr(props, 'export_animated_mesh') and props.export_animated_mesh:
            return 'ANIMATED'
        if export_utils.is_object_keyframe_animated(obj):
            return 'KEYFRAMED'
        return 'STATIC'


def _get_simulation_objects_by_filtered_motion_type(context):
    dprops = context.scene.flip_fluid.get_domain_properties()
    sprops = dprops.simulation
    flip_props = context.scene.flip_fluid
    flip_objects = (flip_props.get_obstacle_objects() + 
                   flip_props.get_fluid_objects() + 
                   flip_props.get_inflow_objects() + 
                   flip_props.get_outflow_objects() + 
                   flip_props.get_force_field_objects())

    if sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_ALL':
        filtered_objects = flip_objects
    elif sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_STATIC':
        filtered_objects = [x for x in flip_objects if _get_object_motion_type(x) == 'STATIC']
    elif sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_KEYFRAMED':
        filtered_objects = [x for x in flip_objects if _get_object_motion_type(x) == 'KEYFRAMED']
    elif sprops.mesh_reexport_type_filter == 'MOTION_FILTER_TYPE_ANIMATED':
        filtered_objects = [x for x in flip_objects if _get_object_motion_type(x) == 'ANIMATED']
    return filtered_objects


class FlipFluidHelperBatchExportAnimatedMesh(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_batch_export_animated_mesh"
    bl_label = ""
    bl_description = "Enable or Disable the 'Export Animated Mesh' option for all objects in list"


    enable_state: BoolProperty(True)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        filtered_objects = _get_simulation_objects_by_filtered_motion_type(context)
        for obj in filtered_objects:
            oprops = obj.flip_fluid.get_property_group()
            oprops.export_animated_mesh = self.enable_state

        return {'FINISHED'}


class FlipFluidHelperBatchSkipReexport(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_batch_skip_reexport"
    bl_label = ""
    bl_description = "Enable or Disable the 'Skip Re-Export' option for all objects in list"


    enable_state: BoolProperty(True)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        filtered_objects = _get_simulation_objects_by_filtered_motion_type(context)
        for obj in filtered_objects:
            oprops = obj.flip_fluid.get_property_group()
            oprops.skip_reexport = self.enable_state

        return {'FINISHED'}


class FlipFluidHelperBatchForceReexport(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_batch_force_reexport"
    bl_label = ""
    bl_description = "Enable or Disable the 'Force Re-Export On Next Bake' option for all objects in list"


    enable_state: BoolProperty(True)


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        filtered_objects = _get_simulation_objects_by_filtered_motion_type(context)
        for obj in filtered_objects:
            oprops = obj.flip_fluid.get_property_group()
            oprops.force_reexport_on_next_bake = self.enable_state

        return {'FINISHED'}


class FlipFluidMakeRelativeToBlendRenderOutput(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.relative_to_blend_render_output"
    bl_label = "Set Relative to Blend"
    bl_description = ("Set a render output directory named 'render' that is located directly relative to the Blend file location")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        blend_filepath = bpy.path.abspath("//")
        if not blend_filepath:
            self.report({"ERROR"}, "Cannot make path relative to unsaved Blend file")
            return {'CANCELLED'}

        blend_name = os.path.basename(bpy.data.filepath)
        blend_name = os.path.splitext(blend_name)[0]

        output_str = "//" + blend_name + "_render/"
        context.scene.render.filepath = output_str

        return {'FINISHED'}


class FlipFluidMakePrefixFilenameRenderOutput(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.prefix_to_filename_render_output"
    bl_label = "Set Prefix as Filename"
    bl_description = ("Set the render output filename prefix to match the Blend filename with a trailing underscore")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        blend_filepath = bpy.path.abspath("//")
        if not blend_filepath:
            self.report({"ERROR"}, "Cannot retrieve Blend filename of unsaved file")
            return {'CANCELLED'}

        current_filepath = context.scene.render.filepath
        blend_name = os.path.basename(bpy.data.filepath)
        blend_name = os.path.splitext(blend_name)[0]

        new_filepath = current_filepath
        if current_filepath.endswith("/") or current_filepath.endswith("\\"):
            new_filepath += blend_name + "_"
        else:
            forward_index = current_filepath.rfind("/")
            backward_index = current_filepath.rfind("\\")
            separator_slash_char = "/"
            if backward_index > forward_index:
                separator_slash_char = "\\"
            filepath_suffix = current_filepath.split(separator_slash_char)[-1]
            new_filepath = current_filepath[:-len(filepath_suffix)] + blend_name + "_"

        context.scene.render.filepath = new_filepath

        return {'FINISHED'}


class FlipFluidAutoLoadBakedFramesCMD(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.auto_load_baked_frames_cmd"
    bl_label = "Auto-load Baked Frames CMD"
    bl_description = "Automatically load frames as they finish baking when running a command line bake"
    bl_options = {'REGISTER'}


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modal_ups = 1.0 / 2.0
        self.modal_ups_timer = None
        self.is_modal_update_required = False

        self.num_bakefiles = -1


    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return True


    def _count_files(self, directory):
        return len(os.listdir(directory))


    def _get_max_bakefile_frame(self, bakefiles_directory):
        bakefiles = os.listdir(bakefiles_directory)
        max_frameno = -1
        for f in bakefiles:
            base = f.split(".")[0]
            try:
                frameno = int(base[-6:])
                max_frameno = max(frameno, max_frameno)
            except ValueError:
                # In the case that there is a bakefile without a number
                pass
        return max_frameno


    def _update_frame(self, context, frameno):
        if not context.scene.flip_fluid.is_domain_in_active_scene():
            return
        if context.scene.frame_current != frameno and frameno >= 0:
            timeline_frame = render.get_timeline_frame_from_simulation_frame(frameno)
            context.scene.frame_set(timeline_frame)


    def _num_bakefiles_changed_handler(self, context, bakefiles_directory):
        last_frame = self._get_max_bakefile_frame(bakefiles_directory)
        self._update_frame(context, last_frame)
        bake_operators.update_stats()


    def _update_modal(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if dprops.bake.is_simulation_running:
            # Don't update if a simulation bake is already running in the UI
            return

        cache_directory = dprops.cache.get_cache_abspath()
        bakefiles_directory = os.path.join(cache_directory, "bakefiles")
        if not os.path.isdir(bakefiles_directory):
            return

        if self.num_bakefiles < 0:
            # Value of -1 indicates value has not been initialized
            self.num_bakefiles = self._count_files(bakefiles_directory)

        current_num_bakefiles = self._count_files(bakefiles_directory)
        if current_num_bakefiles != self.num_bakefiles:
            self.num_bakefiles = current_num_bakefiles
            self._num_bakefiles_changed_handler(context, bakefiles_directory)


    def set_running_state(self, is_running):
        for scene in bpy.data.scenes:
            scene.flip_fluid_helper.is_auto_frame_load_cmd_operator_running = is_running


    def modal(self, context, event):
        if self.is_modal_update_required:
            self.is_modal_update_required = False
            self._update_modal(context)

        if not context.scene.flip_fluid_helper.is_auto_frame_load_cmd_enabled():
            self.cancel(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}


    def invoke(self, context, event):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        # Timer functions need a unique name and cannot be declared in 'self' 
        # in order to be registered/unregistered without error. A random
        # number should be sufficient for the relatively low number of
        # baking servers a user would launch at a time in a single Blender 
        # session.
        def generate_timer_function():
            def func():
                self.is_modal_update_required = True
                return self.modal_ups
            func.__name__ = "timer_function" + str(random.randint(0, 100000))
            return func

        self.modal_ups_timer = generate_timer_function()

        context.window_manager.modal_handler_add(self)
        self.modal_timer = context.window_manager.event_timer_add(0.1, window=context.window)
        bpy.app.timers.register(self.modal_ups_timer)

        self.set_running_state(True)
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        if self.modal_timer:
            context.window_manager.event_timer_remove(self.modal_timer)
            self.modal_timer = None

        if bpy.app.timers.is_registered(self.modal_ups_timer):
            bpy.app.timers.unregister(self.modal_ups_timer)
        
        self.set_running_state(False)


class FlipFluidCopySettingsFromActive(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.copy_setting_to_selected"
    bl_label = "Copy Active Object Settings to Selected Objects"
    bl_description = ("Copy the settings of the active FLIP object (highlighted object) to all other selected"
                      " FLIP objects of the same type. The settings displayed in this panel are the settings"
                      " of the active FLIP object. Note: keyframed settings are not supported for this operator")


    @classmethod
    def poll(cls, context):
        return True


    def copy_settings(self, context, src_obj_props, dst_obj_props):
        property_registry = src_obj_props.property_registry
        for p in property_registry.properties:
            path = p.path
            base, identifier = path.split('.', 1)

            src_prop = getattr(src_obj_props, identifier)
            if hasattr(src_prop, "is_min_max_property"):
                dst_prop = getattr(dst_obj_props, identifier)
                setattr(dst_prop, "value_min", src_prop.value_min)
                setattr(dst_prop, "value_max", src_prop.value_max)
            else:
                src_value = getattr(src_obj_props, identifier)
                setattr(dst_obj_props, identifier, src_value)


    def toggle_cycles_ray_visibility(self, obj, is_enabled):
        # Cycles may not be enabled in the user's preferences
        try:
            obj.visible_camera = is_enabled
            obj.visible_diffuse = is_enabled
            obj.visible_glossy = is_enabled
            obj.visible_transmission = is_enabled
            obj.visible_volume_scatter = is_enabled
            obj.visible_shadow = is_enabled
        except:
            pass


    def execute(self, context):
        src_flip_object = vcu.get_active_object()
        selected_objects = context.selected_objects

        if not src_flip_object:
            err_msg = "Error: No active object selected."
            self.report({"ERROR_INVALID_INPUT"}, err_msg)
            return {'CANCELLED'}

        src_flip_type = src_flip_object.flip_fluid.object_type
        if src_flip_type == 'TYPE_NONE':
            err_msg = "Error: Domain type FLIP objects cannot have settings copied."
            self.report({"ERROR_INVALID_INPUT"}, err_msg)
            return {'CANCELLED'}
        elif src_flip_type == 'TYPE_DOMAIN':
            err_msg = "Error: None type FLIP objects cannot have settings copied."
            self.report({"ERROR_INVALID_INPUT"}, err_msg)
            return {'CANCELLED'}

        flip_type_string = ""
        if src_flip_type == 'TYPE_FLUID':
            flip_type_string = "Fluid"
        elif src_flip_type == 'TYPE_OBSTACLE':
            flip_type_string = "Obstacle"
        elif src_flip_type == 'TYPE_INFLOW':
            flip_type_string = "Inflow"
        elif src_flip_type == 'TYPE_OUTFLOW':
            flip_type_string = "Outflow"
        elif src_flip_type == 'TYPE_FORCE_FIELD':
            flip_type_string = "Force Field"

        dst_flip_objects = []
        for obj in selected_objects:
            if obj.flip_fluid.is_active and obj.flip_fluid.object_type == src_flip_type:
                if obj.name != src_flip_object.name:
                    dst_flip_objects.append(obj)

        if not dst_flip_objects:
            err_msg = "Error: No other FLIP " + flip_type_string + " objects in selection to copy to."
            self.report({"ERROR_INVALID_INPUT"}, err_msg)
            return {'CANCELLED'}

        for dst_flip_object in dst_flip_objects:
            if src_flip_type == 'TYPE_FLUID':
                src_props = src_flip_object.flip_fluid.fluid
                dst_props = dst_flip_object.flip_fluid.fluid
            elif src_flip_type == 'TYPE_OBSTACLE':
                src_props = src_flip_object.flip_fluid.obstacle
                dst_props = dst_flip_object.flip_fluid.obstacle
            elif src_flip_type == 'TYPE_INFLOW':
                src_props = src_flip_object.flip_fluid.inflow
                dst_props = dst_flip_object.flip_fluid.inflow
            elif src_flip_type == 'TYPE_OUTFLOW':
                src_props = src_flip_object.flip_fluid.outflow
                dst_props = dst_flip_object.flip_fluid.outflow
            elif src_flip_type == 'TYPE_FORCE_FIELD':
                src_props = src_flip_object.flip_fluid.force_field
                dst_props = dst_flip_object.flip_fluid.force_field

            self.copy_settings(context, src_props, dst_props)

        info_msg = "Copied active FLIP " + flip_type_string + " object settings to " + str(len(dst_flip_objects)) + " " + flip_type_string + " objects in selection"
        self.report({'INFO'}, info_msg)
        return {'FINISHED'}


class FlipFluidMeasureObjectSpeed(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.measure_object_speed"
    bl_label = "Measure Object Speed"
    bl_description = ("Measure and display the speed of the active object within the simulation" + 
        " for the current frame. The measured speed depends on the object animation, simulation" +
        " world scale and time scale, and animation frame rate." +
        " The objects center speed, min vertex speed, and max vertex speed will be computed. Using" +
        " this operator on an object with complex geometry or a high polycount may cause Blender to" +
        " pause during computation")


    @classmethod
    def poll(cls, context):
        if not hasattr(bpy.context, "selected_objects"):
            # bpy.context may not have "selected objects" in some situations
            # such as while rendering within the UI.
            return False        

        selected_objects = bpy.context.selected_objects
        bl_object = vcu.get_active_object(context)
        if selected_objects:
            if bl_object not in selected_objects:
                bl_object = selected_objects[0]
        else:
            bl_object = None
        return bl_object is not None


    def frame_set(self, context, frameno):
        from ..properties import helper_properties
        helper_properties.DISABLE_FRAME_CHANGE_POST_HANDLER = True
        flip_fluid_cache.DISABLE_MESH_CACHE_LOAD = True
        context.scene.frame_set(frameno)
        flip_fluid_cache.DISABLE_MESH_CACHE_LOAD = False
        helper_properties.DISABLE_FRAME_CHANGE_POST_HANDLER = False


    def get_object_vertices_and_center(self, context, bl_object, frameno):
        self.frame_set(context, frameno)

        vertices = []
        center = None
        if bl_object.type == 'EMPTY':
            vertices.append(mathutils.Vector(bl_object.matrix_world.translation))
            center = mathutils.Vector(bl_object.matrix_world.translation)
        else:
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval = bl_object.evaluated_get(depsgraph)
            evaluated_mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
            for mv in evaluated_mesh.vertices:
                vertices.append(obj_eval.matrix_world @ mv.co)

            local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in bl_object.bound_box), mathutils.Vector())
            center = bl_object.matrix_world @ local_bbox_center

        return vertices, center


    def execute(self, context):
        timer_start = datetime.datetime.now()

        hprops = context.scene.flip_fluid_helper
        hprops.is_translation_data_available = False

        selected_objects = bpy.context.selected_objects
        bl_object = vcu.get_active_object(context)
        if selected_objects:
            if bl_object not in selected_objects:
                bl_object = selected_objects[0]
        else:
            bl_object = None

        if bl_object is None:
            err_msg = "No active object selected."
            self.report({'ERROR'}, err_msg)
            print("Measure Object Speed Error: " + err_msg + "\n")
            return {'CANCELLED'}

        valid_object_types = ['MESH', 'EMPTY', 'CURVE']
        if bl_object.type not in valid_object_types:
            err_msg = "Invalid object type <" + bl_object.type + ">. Object must be a Mesh, Curve, or Empty to measure speed."
            self.report({'ERROR'}, err_msg)
            print("Measure Object Speed Error: " + err_msg + "\n")
            return {'CANCELLED'}

        original_frame = context.scene.frame_current
        frame1 = original_frame - 1
        frame2 = original_frame + 1

        print("Measure Object Speed: Exporting <" + bl_object.name + "> geometry for frame " + str(frame1) + "...", end=' ')
        vertices1, center1 = self.get_object_vertices_and_center(context, bl_object, frame1)
        print("Exported " + str(len(vertices1)) + " vertices.")

        if len(vertices1) == 0:
            err_msg = "Object does not contain geometry."
            self.report({'ERROR'}, err_msg)
            print("Measure Object Speed Error: " + err_msg + "\n")
            self.frame_set(context, original_frame)
            return {'CANCELLED'}

        print("Measure Object Speed: Exporting <" + bl_object.name + "> geometry for frame " + str(frame2) + "...", end=' ')
        vertices2, center2 = self.get_object_vertices_and_center(context, bl_object, frame2)
        print("Exported " + str(len(vertices2)) + " vertices.")
        self.frame_set(context, original_frame)

        if len(vertices1) != len(vertices1):
            err_msg = "Cannot measure velocity of object with changing topology."
            self.report({'ERROR'}, err_msg)
            print("Measure Object Speed Error: " + err_msg + "\n")
            return {'CANCELLED'}

        center_translation = (center2 - center1).length / float(frame2 - frame1)
        min_translation = float('inf')
        max_translation = -float('inf')
        sum_translation = 0.0
        for i in range(len(vertices1)):
            translation = (vertices2[i] - vertices1[i]).length / float(frame2 - frame1)
            min_translation = min(min_translation, translation)
            max_translation = max(max_translation, translation)
            sum_translation += translation
        avg_translation = sum_translation / len(vertices1)

        timer_end = datetime.datetime.now()
        ms_duration = int((timer_end - timer_start).microseconds / 1000)

        hprops.min_vertex_translation = min_translation
        hprops.max_vertex_translation = max_translation
        hprops.avg_vertex_translation = avg_translation
        hprops.center_translation = center_translation
        hprops.translation_data_object_name = bl_object.name
        hprops.translation_data_object_vertices = len(vertices1)
        hprops.translation_data_object_frame = original_frame
        hprops.translation_data_object_compute_time = ms_duration
        hprops.is_translation_data_available = True

        info_str = "Measure Object Speed: Finished computing <" + bl_object.name + "> vertex translations for frame "
        info_str += str(original_frame) + " in " + str(ms_duration) + " milliseconds.\n"
        print(info_str)

        return {'FINISHED'}


class FlipFluidClearMeasureObjectSpeed(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.clear_measure_object_speed"
    bl_label = "Clear Speed Data"
    bl_description = "Clear the measured object speed display"


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        hprops.is_translation_data_available = False
        return {'FINISHED'}


class FlipFluidDisableAddonInBlendFile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.disable_addon_in_blend_file"
    bl_label = "Disable FLIP Fluids in Blend File"
    bl_description = ("Disable the FLIP Fluids addon in this Blend file." +
        " The FLIP Fluids addon can add overhead to the Blend file due to" +
        " scripts that manage all of the functionality of the addon. This" +
        " operator can be used to temporarily disable the addon to speed up" +
        " this Blend file when you are not actively using the addon")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        if bake_operators.is_bake_operator_running():
            err_msg = "Unable to disable addon while simulation is baking. Stop simulation bake or reload the Blend file and try again."
            self.report({'ERROR'}, err_msg)
            return {'CANCELLED'}

        if render.is_rendering():
            err_msg = "Unable to disable addon while rendering. Stop the render or reload the Blend file and try again."
            self.report({'ERROR'}, err_msg)
            return {'CANCELLED'}

        for scene in bpy.data.scenes:
            scene.flip_fluid_helper.disable_addon_in_blend_file = True

        info_msg = "The FLIP Fluids Addon has been disabled in this Blend file. Re-enable to resume using the addon."
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidEnableAddonInBlendFile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_addon_in_blend_file"
    bl_label = "Enable FLIP Fluids in Blend File"
    bl_description = ("Re-enable the FLIP Fluids addon in this Blend file." +
        " This operator will re-activate the addons management scripts. Enabling" +
        " the addon is required to use the addon. Disabling addon" +
        " reduces overhead and can speed up Blend file when the addon is not actively used")


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        for scene in bpy.data.scenes:
            scene.flip_fluid_helper.disable_addon_in_blend_file = False

        from .. import load_post, load_pre
        load_pre(None)
        load_post(None)

        info_msg = "The FLIP Fluids Addon has been re-enabled in this Blend file."
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}
        

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

    print("Compositor setup for Indirect Passes is complete.")

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
    hprops = context.scene.flip_fluid_helper
    has_unflagged = any(
        not (item.fg_elements or item.bg_elements or item.ref_elements or item.ground)
        for item in hprops.render_passes_objectlist
    )
    hprops.render_passes_has_unflagged_objects = has_unflagged
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
    hprops = context.scene.flip_fluid_helper

    # Check if there are unflagged objects
    if not hprops.render_passes_has_unflagged_objects:
        print("INFO: No unflagged objects available for assignment")
        return

    # Get the geometry node group
    geo_node = bpy.data.node_groups.get("FF_FadeNearObjects")
    if not geo_node:
        print("WARNING: Node group 'FF_FadeNearObjects' not found")
        return

    # Get the Object Info nodes from the geometry node group
    object_info_nodes = [
        geo_node.nodes.get(f"ff_fading_objects_{i}") for i in range(1, 11)
    ]
    object_info_nodes = [node for node in object_info_nodes if node]

    if not object_info_nodes:
        print("WARNING: No valid nodes found in 'FF_FadeNearObjects'")
        return

    # Iterate over the object list and assign only unflagged objects to free nodes
    for item in hprops.render_passes_objectlist:
        # Skip objects that already have an assigned node
        if item.assigned_node:
            continue

        # Skip flagged objects (based on your logic: flagged if any of these properties are True)
        if item.fg_elements or item.bg_elements or item.ref_elements or item.ground:
            print(f"INFO: Skipping flagged object {item.name}")
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
            print(f"INFO: Assigned {item.name} to {free_node.name}")
        else:
            print(f"WARNING: No free node available for {item.name}")

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
            hprops = context.scene.flip_fluid_helper
            if any(media_item.object_name == item.name for media_item in hprops.render_passes_import_media):
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
        hprops = context.scene.flip_fluid_helper
        item = hprops.render_passes_objectlist[self.index]
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
        hprops = context.scene.flip_fluid_helper
        item = hprops.render_passes_objectlist[self.index]
        obj = bpy.data.objects.get(item.name)

        if not obj:
            self.report({'WARNING'}, "Object not found.")
            return {'CANCELLED'}

        # Suche nach einem bereits gespeicherten Zustand in render_passes_shadowcatcher_state
        existing_entry = next((entry for entry in hprops.render_passes_shadowcatcher_state if entry.name == obj.name), None)

        # --- Benutzer klickt auf den "C" Button im UI ---
        if context.area.type == 'VIEW_3D':  
            obj.is_shadow_catcher = not obj.is_shadow_catcher  # Toggle Zustand
            
            if existing_entry:
                existing_entry.is_shadow_catcher = obj.is_shadow_catcher  # Update gespeicherten Wert
            else:
                new_entry = hprops.render_passes_shadowcatcher_state.add()
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
                        new_entry = hprops.render_passes_shadowcatcher_state.add()
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

        hprops = context.scene.flip_fluid_helper
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
                        elif any(item.name == child.name for item in hprops.render_passes_objectlist):
                            show_message_box(f"{child.name} is already in the render pass list.", title="Duplicate Object", icon='INFO')
                        else:
                            assigned_node = ""
                            if geo_node and object_info_nodes:
                                assigned_nodes = {item.assigned_node for item in hprops.render_passes_objectlist if item.assigned_node}
                                free_node = next((node for node in object_info_nodes if node.name not in assigned_nodes and not node.inputs["Object"].default_value), None)
                                if free_node:
                                    free_node.inputs["Object"].default_value = child
                                    assigned_node = free_node.name

                            item = hprops.render_passes_objectlist.add()
                            item.name = child.name
                            item.data_name = child.data.name
                            item.assigned_node = assigned_node
                            added_objects += 1
            else:
                if any(item.name == obj.name for item in hprops.render_passes_objectlist):
                    show_message_box(f"{obj.name} is already in the render pass list.", title="Duplicate Object", icon='INFO')
                else:
                    assigned_node = ""
                    if geo_node and object_info_nodes:
                        assigned_nodes = {item.assigned_node for item in hprops.render_passes_objectlist if item.assigned_node}
                        free_node = next((node for node in object_info_nodes if node.name not in assigned_nodes and not node.inputs["Object"].default_value), None)
                        if free_node:
                            free_node.inputs["Object"].default_value = obj
                            assigned_node = free_node.name

                    item = hprops.render_passes_objectlist.add()
                    item.name = obj.name
                    item.data_name = obj.data.name
                    item.assigned_node = assigned_node
                    added_objects += 1

        # Handle nodes based on Flags
        for item in hprops.render_passes_objectlist:
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
            hprops.render_passes_objectlist_index = len(hprops.render_passes_objectlist) - 1

        # Call function to assign object to fading network
        assign_objects_to_fading_network(context)


        return {'FINISHED'}


class FlipFluidPassesDuplicateItemInList(bpy.types.Operator):
    """Duplicate an object from the list, including material and FADER"""
    bl_idname = "flip_fluid_operators.duplicate_item_in_list"
    bl_label = "Duplicate Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        # Ensure a valid object is selected in the list
        selected_index = hprops.render_passes_objectlist_index
        if selected_index < 0 or selected_index >= len(hprops.render_passes_objectlist):
            self.report({'ERROR'}, "No valid object selected. Please select an object from the list.")
            return {'CANCELLED'}

        # Retrieve the original object and its data
        original_item = hprops.render_passes_objectlist[selected_index]
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
        new_item = hprops.render_passes_objectlist.add()
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
        hprops = context.scene.flip_fluid_helper
        fader_dict = hprops.render_passes_faderobjects_DICT

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
        hprops = context.scene.flip_fluid_helper

        # Ensure the index is within valid range
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            # Get the item to be removed
            item = hprops.render_passes_objectlist[self.index]

            # Clear the associated Object Info Node
            assigned_node_name = item.assigned_node
            if assigned_node_name:
                geo_node = bpy.data.node_groups.get("FF_FadeNearObjects")
                if geo_node:
                    node = geo_node.nodes.get(assigned_node_name)
                    if node and node.type == 'OBJECT_INFO':
                        node.inputs["Object"].default_value = None  # Clear the object reference

            # Remove the item from the list
            hprops.render_passes_objectlist.remove(self.index)

            # Adjust the selected index
            hprops.render_passes_objectlist_index = min(max(0, self.index - 1), len(hprops.render_passes_objectlist) - 1)

        # Call function to set objects-fading-property
        update_unflagged_objects_property(context)

        # Call function to assign object to fading network
        assign_objects_to_fading_network(context)

        return {'FINISHED'}


def toggle_render_pass_flag(context, obj_name, flag_name, fgbg_value, reflective_value, enable_flag):
    """Toggle a render pass flag and update materials, nodes, and FADER objects."""
    hprops = context.scene.flip_fluid_helper
    all_objects_dict = hprops.render_passes_all_objects_materials_DICT
    fader_dict = hprops.render_passes_faderobjects_DICT

    blend_filename = "FF_Compositing.blend"
    parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_filepath = os.path.join(parent_path, "presets", "preset_library", "sys", blend_filename)

    if not os.path.exists(resource_filepath):
        raise FileNotFoundError(f"Blend file not found: {resource_filepath}")

    obj = bpy.data.objects.get(obj_name)
    if not obj:
        raise ValueError(f"Object '{obj_name}' not found.")

    # Suche nach einem bereits gespeicherten ShadowCatcher-Zustand
    existing_entry = next((entry for entry in hprops.render_passes_shadowcatcher_state if entry.name == obj_name), None)

    # **Speicherung des ShadowCatcher-Status, wenn BG/REF deaktiviert wird**
    if not enable_flag and flag_name in ("bg_elements", "ref_elements"):
        if obj.is_shadow_catcher:  
            if existing_entry:
                existing_entry.is_shadow_catcher = obj.is_shadow_catcher  # Update gespeicherten Wert
            else:
                new_entry = hprops.render_passes_shadowcatcher_state.add()
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
        for item in hprops.render_passes_objectlist:
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
        for item in hprops.render_passes_objectlist:
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
                print(f"Restored original material '{original_material}' for object '{obj_name}'.")

        # Remove Modifiers if all toggles are off
        if obj:
            remove_modifiers_if_no_toggles(obj, hprops)

        # Reassign object to a free node if no flags are set
        for item in hprops.render_passes_objectlist:
            if item.name == obj_name and not (item.fg_elements or item.bg_elements or item.ref_elements or item.ground):
                assigned_nodes = {item.assigned_node for item in hprops.render_passes_objectlist if item.assigned_node}
                free_node = next((node for node in object_info_nodes if node.name not in assigned_nodes and not node.inputs["Object"].default_value), None)
                if free_node:
                    free_node.inputs["Object"].default_value = obj
                    item.assigned_node = free_node.name
        
        # Refresh Object List
        bpy.ops.flip_fluid_operators.refresh_objectlist()

        return

    # Enable the specified flag
    for item in hprops.render_passes_objectlist:
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
        for item in hprops.render_passes_objectlist:
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
        hprops = context.scene.flip_fluid_helper
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            item = hprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "fg_elements", fgbg_value=0, reflective_value=0, enable_flag=not item.fg_elements)
        return {'FINISHED'}


class FlipFluidPassesTogglebg_elements(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_bg_elements"
    bl_label = "Toggle BG Element"

    index: bpy.props.IntProperty()

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            item = hprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "bg_elements", fgbg_value=1, reflective_value=0, enable_flag=not item.bg_elements)
        return {'FINISHED'}


class FlipFluidPassesToggleReflective(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_reflective"
    bl_label = "Toggle Reflective"

    index: bpy.props.IntProperty()

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            item = hprops.render_passes_objectlist[self.index]
            toggle_render_pass_flag(context, item.name, "ref_elements", fgbg_value=1, reflective_value=1, enable_flag=not item.ref_elements)
        return {'FINISHED'}


class FlipFluidPassesToggleGround(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_ground"
    bl_label = "Toggle Ground"

    index: bpy.props.IntProperty()

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            item = hprops.render_passes_objectlist[self.index]
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
            print(f"Warning: FADER object '{fader_obj.name if fader_obj else 'None'}' is not in the current View Layer.")
            obj.select_set(True)
            context.view_layer.objects.active = obj

    def clean_fader_dict(self, obj_name, hprops):
        """Remove invalid FADER entries from the FADER dictionary."""
        for entry in hprops.render_passes_faderobjects_DICT:
            if entry.obj_name == obj_name and (not entry.node_object or entry.node_object.name not in bpy.data.objects):
                print(f"Warning: FADER object for '{obj_name}' is missing and will be removed.")
                hprops.render_passes_faderobjects_DICT.remove(hprops.render_passes_faderobjects_DICT.find(entry.obj_name))
                break

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        # Ensure index is within valid range
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            item = hprops.render_passes_objectlist[self.index]
            obj = bpy.data.objects.get(item.name)

            if obj:
                # Refresh Object List
                bpy.ops.flip_fluid_operators.refresh_objectlist()

                # Get the active object
                active_obj = context.view_layer.objects.active

                # Find the corresponding FADER object
                fader_obj = next(
                    (entry.node_object for entry in hprops.render_passes_faderobjects_DICT if entry.obj_name == obj.name),
                    None
                )

                # Handle missing FADER object
                if fader_obj and fader_obj.name not in bpy.data.objects:
                    self.clean_fader_dict(obj.name, hprops)
                    fader_obj = None  # Reset FADER object to None

                # Toggle selection between main object and FADER object
                self.toggle_selection(obj, fader_obj, active_obj, context)

                # Update the active index for the UIList
                hprops.render_passes_objectlist_index = self.index

        return {'FINISHED'}


class FlipFluidPassesRefreshObjectList(bpy.types.Operator):
    """Refreshes the render_passes_objectlist based on the current scene objects"""
    bl_idname = "flip_fluid_operators.refresh_objectlist"
    bl_label = "Refresh Object List"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        object_list = hprops.render_passes_objectlist
        fader_dict = hprops.render_passes_faderobjects_DICT

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
                    print(f"Restoring FADER object '{fader_object.name}' to the scene.")
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
    depth = bpy.context.scene.flip_fluid_helper.render_passes_camerascreen_distance
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
        default='*.png;*.jpg;*.jpeg;*.jp2;*.tif;*.exr;*.hdr;*.bmp;*.rgb;*.tga;*.cin;*.dpx;*.webp',
        options={'HIDDEN'}
    )

    directory: StringProperty()
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    def check_and_report_operator_context_errors(self, context):
        valid_file_types = ('.png', '.jpg', '.jpeg', '.jp2', '.tif', '.exr', '.hdr', '.bmp', '.rgb', '.tga', '.cin', '.dpx', '.webp')
        for file in self.files:
            if not file.name.lower().endswith(valid_file_types):
                filepath = os.path.join(self.directory, file.name)
                valid_types_string = " ".join(valid_file_types)
                errmsg = "Invalid file type selected: <" + filepath + ">."
                errmsg += " Supported file types: " + valid_types_string
                self.report({'ERROR'}, errmsg)
                return {'CANCELLED'}

        hprops = context.scene.flip_fluid_helper
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        if bl_camera is None:
            show_message_box(message=f"Camera object <{str(hprops.render_passes_cameraselection)}> not found", title="Error", icon='OUTLINER_OB_CAMERA')
            return {'CANCELLED'}

    def initialize_camera_screen_object(self, context, image_aspect_ratio):
        hprops = context.scene.flip_fluid_helper

        # Create and size camera screen plane
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        bpy.ops.mesh.primitive_plane_add()
        bl_camera_screen = context.active_object
        bl_camera_screen.name = "ff_camera_screen"
        bl_camera_screen.lock_location = (True, True, True)
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)

        depth = hprops.render_passes_camerascreen_distance
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
        hprops = context.scene.flip_fluid_helper
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        
        if not bl_camera:
            print("Camera not found!")
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
        hprops = context.scene.flip_fluid_helper

        # Check if 'ff_camera_screen' exists
        ff_camera_screen = bpy.data.objects.get("ff_camera_screen")
        if ff_camera_screen:
            # Check if the selected object is in the object list and has a valid flag
            selected_obj = context.view_layer.objects.active
            object_list = hprops.render_passes_objectlist  # List of all objects

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
                    print("Failed to retrieve world transformation of ff_camera_screen.")
                    self.report({'ERROR'}, "Failed to retrieve transformation of ff_camera_screen.")
                    return {'CANCELLED'}

        # If 'ff_camera_screen' exists but no valid object was selected
        if ff_camera_screen:
            show_message_box(message="An object named 'ff_camera_screen' already exists. No new object created.", title="Warning", icon='IMAGE_BACKGROUND')
            return {'CANCELLED'}

        # If no Camera Screen exists, proceed with file selection
        return context.window_manager.fileselect_add(self) or {'RUNNING_MODAL'}


    def execute_with_existing_images(self, context, image_filepaths):
        hprops = context.scene.flip_fluid_helper
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        
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
def add_imported_media_to_collection(hprops, file_name):
    """Adds the file to the collection and ensures texture assignment."""
    
    # Check if the file is already in the collection
    for item in hprops.render_passes_import_media:
        if item.file_name == file_name:
            return item  # Return existing entry

    # Add new file to the collection
    new_item = hprops.render_passes_import_media.add()
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
            print(f"Failed to load image '{image_path}': {e}")
            return

    image = bpy.data.images.get(file_name)
    if not image:
        print(f"Image '{file_name}' could not be found in Blender after loading.")
        return

    # Get the object and its material
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.data.materials:
        print(f"Object '{obj_name}' does not have a material.")
        return

    material = obj.data.materials[0]

    # Ensure the material has a node tree
    if not material.use_nodes:
        print(f"Material on '{obj_name}' does not use nodes.")
        return

    node_tree = material.node_tree
    texture_node = node_tree.nodes.get("ff_camera_screen")

    if not texture_node:
        print(f"Node 'ff_camera_screen' not found in material for '{obj_name}'.")
        return

    # Is the object in the imported media list?
    hprops = bpy.context.scene.flip_fluid_helper
    media_item = next((item for item in hprops.render_passes_import_media if item.object_name == obj_name), None)

    if media_item:
        # Use the texture name stored in the media property
        #texture_name = media_item.texture_name
        image = bpy.data.images.get(file_name)

        if not image:
            print(f"Skipping texture update for '{obj_name}' because its texture '{texture_name}' could not be found.")
            return

    # Assign the image to the texture node
    texture_node.image = image
    print(f"Updated texture for '{obj_name}' with image '{image.name}'.")


class FlipFluidPassesImportMedia(bpy.types.Operator):
    """Operator to import images or videos and store them in a CollectionProperty"""
    bl_idname = "flip_fluid.passes_import_media"
    bl_label = "Import Media"

    option_path_supports_blend_relative = {'PATH_SUPPORTS_BLEND_RELATIVE'}

    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.tif;*.mp4;*.avi;*.mov",
        options={'HIDDEN'}
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    directory: StringProperty(subtype='DIR_PATH', options=option_path_supports_blend_relative)

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        any_files_processed = False
        created_objects = []  # Track created objects

        for file in self.files:
            file_name = file.name
            base_name = os.path.splitext(file_name)[0]
            texture_name = f"ff_{base_name.lower()}_element"

            # Add to property collection and save filename
            if add_imported_media_to_collection(hprops, file_name):
                media_item = next((item for item in hprops.render_passes_import_media if item.object_name == base_name), None)
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
            print("No new files were processed. All selected files were already imported.")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class FlipFluidToggleCameraScreenVisibility(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_camerascreen_visibility"
    bl_label = "Toggle CameraScreen Visibility"

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        ff_camera_screen = bpy.data.objects.get("ff_camera_screen")
        if ff_camera_screen:
            ff_camera_screen.hide_viewport = not hprops.render_passes_camerascreen_visibility
        return {'FINISHED'}


class FlipFluidPassesToggleStillImageMode(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_still_image_mode"
    bl_label = "Toggle Still Image Mode"
    bl_description = "Perform actions when toggling Still Image Mode"

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper

        if hprops.render_passes_stillimagemode_toggle:
            # Enable Still Image Mode
            self.enable_still_image_mode(context, hprops)
            self.report({'INFO'}, "Still Image Mode Enabled")
        else:
            # Disable Still Image Mode
            self.disable_still_image_mode(context, hprops)
            self.report({'INFO'}, "Still Image Mode Disabled")

        return {'FINISHED'}

    def enable_still_image_mode(self, context, hprops):
        # Step 1: Get the currently selected camera
        original_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
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
        hprops.render_passes_cameraselection = projector_camera.name

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

    def disable_still_image_mode(self, context, hprops):
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
            hprops.render_passes_cameraselection = original_camera.name

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
        hprops = context.scene.flip_fluid_helper
        fader_dict = hprops.render_passes_faderobjects_DICT

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
            hprops = context.scene.flip_fluid_helper
            if any(media_item.object_name == obj.name for media_item in hprops.render_passes_import_media):
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
        hprops = context.scene.flip_fluid_helper
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        if not bl_camera or bl_camera.type != 'CAMERA':
            show_message_box(message="Camera specified in flip_fluid_helper not found or is not a camera.", title="Error", icon='OUTLINER_OB_CAMERA')
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
    hprops = context.scene.flip_fluid_helper
    fader_dict = hprops.render_passes_faderobjects_DICT

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
            print("Warning: Invalid object passed to flipfluidpasses_createfaderobjects.")
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
    hprops = context.scene.flip_fluid_helper
    fader_dict = hprops.render_passes_faderobjects_DICT

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
    hprops = context.scene.flip_fluid_helper
    fader_dict = hprops.render_passes_faderobjects_DICT

    # Backup the current entries, ensuring nothing is deleted
    existing_fader_objects = {entry.obj_name: entry for entry in fader_dict}

    # Iterate through the objects in the scene and collect relevant FADER objects
    for obj in bpy.data.objects:
        for material_slot in obj.material_slots:
            material = material_slot.material
            if material and material.use_nodes and material.name.startswith("FF"):
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
    hprops = context.scene.flip_fluid_helper
    all_objects_dict = hprops.render_passes_all_objects_materials_DICT
    object_list = hprops.render_passes_objectlist  # Only process objects in this list

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
    hprops = context.scene.flip_fluid_helper
    fader_dict = hprops.render_passes_faderobjects_DICT

    # Iterate through the dict and print the contents
    for entry in fader_dict:
        print("FADER LIST ENTRY")
        print(f"Object Name: {entry.obj_name}")
        print(f"Material Name: {entry.material_name}")
        print(f"Original Material Name: {entry.original_materialname}")  # Added this line
        if entry.node_object:
            print(f"Node Object: {entry.node_object.name}")
        else:
            print("Node Object: None")
        print("-------------")

def print_all_objects_materials_dict(context):
    """Prints the contents of the all_objects_materials_dict for debugging."""
    # Access the centralized all_objects_materials_dict from the helper properties
    hprops = context.scene.flip_fluid_helper
    all_objects_dict = hprops.render_passes_all_objects_materials_DICT

    # Iterate through the dict and print the contents
    for entry in all_objects_dict:
        if entry.node_object:
            print(f"Node Object: {entry.node_object.name}")
        else:
            print("Node Object: None")
        print("-------------")

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
        hprops = context.scene.flip_fluid_helper
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
    hprops = context.scene.flip_fluid_helper

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
    new_index = len(hprops.render_passes_objectlist) - 1  # Assuming the new item is added at the end of the list

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
        if any(media_item.object_name == plane.name for media_item in hprops.render_passes_import_media):
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
        hprops = context.scene.flip_fluid_helper

        # Check if a Ground object already exists
        if any(item.ground for item in hprops.render_passes_objectlist):
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
        # Get the scene camera from the flip_fluid_helper properties
        hprops = context.scene.flip_fluid_helper
        scene_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        if not scene_camera or scene_camera.type != 'CAMERA':
            show_message_box(message="Camera specified in flip_fluid_helper not found or is not a camera.", title="Error", icon='CAMERA_DATA')
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

def remove_modifiers_if_no_toggles(obj, hprops):
    """Remove Subdivision and UV Project Modifiers if all toggles in list are off."""
    # Check if the object exists in the render_passes_objectlist
    item = next((i for i in hprops.render_passes_objectlist if i.name == obj.name), None)
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
        hprops = context.scene.flip_fluid_helper

        ff_alignment_grid = bpy.data.objects.get("ff_alignment_grid")
        if ff_alignment_grid:
            ff_alignment_grid.hide_viewport = not hprops.render_passes_alignmentgrid_visibility
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
        hprops = context.scene.flip_fluid_helper
        visibility = hprops.render_passes_faderobjects_visibility

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
        hprops = context.scene.flip_fluid_helper
        visibility = hprops.render_passes_faderobjectnames_visibility

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
        hprops = context.scene.flip_fluid_helper
        visibility = hprops.render_passes_objectnames_visibility

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
    hprops = context.scene.flip_fluid_helper  # Zugriff auf die Helper-Properties

    # Calculate the combined value from toggles and flags
    value = 0
    if hprops.render_passes_toggle_fader_fluidsurface:
        value += 1
    if hprops.render_passes_toggle_speed_fluidsurface:
        value += 2
    if hprops.render_passes_toggle_domain_fluidsurface:
        value += 4
    if hprops.render_passes_has_unflagged_objects:
        value += 8

    # Store the combined value
    hprops.render_passes_fader_combination_fluidsurface = value

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
        if node_group.name.startswith("FF"):
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
        hprops = context.scene.flip_fluid_helper
        hprops.render_passes_toggle_fader_fluidsurface = not hprops.render_passes_toggle_fader_fluidsurface
        return {'FINISHED'}

class FlipFluidToggleSpeedFluidSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_speed_fluidsurface"
    bl_label = "Toggle Speed Fluid Surface"

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        hprops.render_passes_toggle_speed_fluidsurface = not hprops.render_passes_toggle_speed_fluidsurface
        return {'FINISHED'}

class FlipFluidToggleDomainFluidSurface(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.toggle_domain_fluidsurface"
    bl_label = "Toggle Domain Fluid Surface"

    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        hprops.render_passes_toggle_domain_fluidsurface = not hprops.render_passes_toggle_domain_fluidsurface
        return {'FINISHED'}

def register():
    classes = [
        FlipFluidHelperRemesh,
        FlipFluidHelperSelectDomain,
        FlipFluidHelperSelectSurface,
        FlipFluidHelperSelectFluidParticles,
        FlipFluidHelperSelectFoam,
        FlipFluidHelperSelectBubble,
        FlipFluidHelperSelectSpray,
        FlipFluidHelperSelectDust,
        FlipFluidHelperSelectObjects,
        FlipFluidHelperCreateDomain,
        FlipFluidHelperAddObjects,
        FlipFluidHelperRemoveObjects,
        FlipFluidHelperDeleteDomain,
        FlipFluidHelperDeleteSurfaceObjects,
        FlipFluidHelperDeleteParticleObjects,
        FlipFluidHelperDeleteWhitewaterObjects,
        FlipFluidHelperOrganizeOutliner,
        FlipFluidHelperSeparateFLIPMeshes,
        FlipFluidHelperUndoOrganizeOutliner,
        FlipFluidHelperUndoSeparateFLIPMeshes,
        FlipFluidHelperSetObjectViewportDisplay,
        FlipFluidHelperSetObjectRenderDisplay,
        FlipFluidHelperLoadLastFrame,
        FlipFluidHelperInitializeMotionBlur,
        FlipFluidHelperRemoveMotionBlur,
        FlipFluidHelperToggleMotionBlurRendering,
        FlipFluidHelperUpdateGeometryNodeModifiers,
        FlipFluidHelperInitializeCacheObjects,
        FlipFluidHelperStableRendering279,
        FlipFluidHelperStableRendering28,
        FlipFluidHelperSetLinearOverrideKeyframes,
        FlipFluidHelperSaveBlendFile,
        FlipFluidHelperBatchExportAnimatedMesh,
        FlipFluidHelperBatchSkipReexport,
        FlipFluidHelperBatchForceReexport,
        FlipFluidEnableFluidParticleMenu,
        FlipFluidEnableFluidParticleOutput,
        FlipFluidDisplayEnableFluidParticlesTooltip,
        FlipFluidEnableWhitewaterSimulation,
        FlipFluidEnableWhitewaterMenu,
        FlipFluidDisplayEnableWhitewaterTooltip,
        FlipFluidEnableColorAttribute,
        FlipFluidEnableColorMixAttribute,
        FlipFluidEnableColorAttributeMenu,
        FlipFluidEnableColorAttributeTooltip,
        FlipFluidEnableViscosityAttribute,
        FlipFluidEnableViscosityAttributeMenu,
        FlipFluidEnableViscosityAttributeTooltip,
        FlipFluidEnableDensityAttribute,
        FlipFluidEnableDensityAttributeMenu,
        FlipFluidEnableDensityAttributeTooltip,
        FlipFluidEnableLifetimeAttribute,
        FlipFluidEnableLifetimeAttributeMenu,
        FlipFluidEnableLifetimeAttributeTooltip,
        FlipFluidEnableSourceIDAttribute,
        FlipFluidEnableSourceIDAttributeMenu,
        FlipFluidEnableSourceIDAttributeTooltip,
        FlipFluidMakeRelativeToBlendRenderOutput,
        FlipFluidMakePrefixFilenameRenderOutput,
        FlipFluidAutoLoadBakedFramesCMD,
        FlipFluidCopySettingsFromActive,
        FlipFluidMeasureObjectSpeed,
        FlipFluidClearMeasureObjectSpeed,
        FlipFluidDisableAddonInBlendFile,
        FlipFluidEnableAddonInBlendFile,
        FlipFluidOperatorsInitializeCompositing,
        FlipFluidPassesToggleStillImageMode,
        FlipFluidPassesToggleFade,
        FlipFluidPassesToggleShadowCatcher,
        FlipFluidPassesTogglefg_elements,
        FlipFluidPassesTogglebg_elements,
        FlipFluidPassesToggleReflective,
        FlipFluidPassesToggleGround,
        FlipFluidPassesAddItemToList,
        FlipFluidPassesDuplicateItemInList,
        FlipFluidPassesRemoveItemFromList,
        FLIPFLUID_UL_passes_items,
        FlipFluidPassesAddCameraScreen,
        FlipFluidPassesImportMedia,
        FlipFluidToggleCameraScreenVisibility,
        FlipFluidPassesFixCompositingTextures,
        FlipFluidPassesApplyAllMaterials,
        FlipFluidPassesSelectObjectInList,
        FlipFluidPassesRefreshObjectList,
        FlipFluidAlignAndParentOperator,
        FlipFluidPassesQuickForegroundCatcher,
        FlipFluidPassesQuickBackgroundCatcher,
        FlipFluidPassesQuickReflectiveCatcher,
        FlipFluidPassesQuickGround,
        FlipFluidToggleAlignmentGridVisibility,
        FlipFluidPassesAddAlignmentGrid,
        FlipFluidPrepareUVProjection,
        FlipFluidPassesToggleFaderObjectsVisibility,
        FlipFluidPassesToggleFaderObjectNamesVisibility,
        FlipFluidPassesToggleObjectNamesVisibility,
        FlipFluidToggleFaderFluidSurface,
        FlipFluidToggleSpeedFluidSurface,
        FlipFluidToggleDomainFluidSurface,
        FlipFluidPassesCalculateFaderCombinationFluidSurface,
        ]

    # Workaround for a bug in FLIP Fluids 1.6.0
    # These classes were not unregistered correctly.
    # This prevents errors when updating the addon to
    # a later version.
    for c in classes:
        try:
            bpy.utils.register_class(c)
        except:
            print(c)
            bpy.utils.unregister_class(c)
            bpy.utils.register_class(c)


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperRemesh)
    bpy.utils.unregister_class(FlipFluidHelperSelectDomain)
    bpy.utils.unregister_class(FlipFluidHelperSelectSurface)
    bpy.utils.unregister_class(FlipFluidHelperSelectFluidParticles)
    bpy.utils.unregister_class(FlipFluidHelperSelectFoam)
    bpy.utils.unregister_class(FlipFluidHelperSelectBubble)
    bpy.utils.unregister_class(FlipFluidHelperSelectSpray)
    bpy.utils.unregister_class(FlipFluidHelperSelectDust)
    bpy.utils.unregister_class(FlipFluidHelperSelectObjects)
    bpy.utils.unregister_class(FlipFluidHelperCreateDomain)
    bpy.utils.unregister_class(FlipFluidHelperAddObjects)
    bpy.utils.unregister_class(FlipFluidHelperRemoveObjects)
    bpy.utils.unregister_class(FlipFluidHelperDeleteDomain)
    bpy.utils.unregister_class(FlipFluidHelperDeleteSurfaceObjects)
    bpy.utils.unregister_class(FlipFluidHelperDeleteParticleObjects)
    bpy.utils.unregister_class(FlipFluidHelperDeleteWhitewaterObjects)
    bpy.utils.unregister_class(FlipFluidHelperOrganizeOutliner)
    bpy.utils.unregister_class(FlipFluidHelperSeparateFLIPMeshes)
    bpy.utils.unregister_class(FlipFluidHelperUndoOrganizeOutliner)
    bpy.utils.unregister_class(FlipFluidHelperUndoSeparateFLIPMeshes)
    bpy.utils.unregister_class(FlipFluidHelperSetObjectViewportDisplay)
    bpy.utils.unregister_class(FlipFluidHelperSetObjectRenderDisplay)
    bpy.utils.unregister_class(FlipFluidHelperLoadLastFrame)
    bpy.utils.unregister_class(FlipFluidHelperInitializeMotionBlur)
    bpy.utils.unregister_class(FlipFluidHelperRemoveMotionBlur)
    bpy.utils.unregister_class(FlipFluidHelperToggleMotionBlurRendering)
    bpy.utils.unregister_class(FlipFluidHelperUpdateGeometryNodeModifiers)
    bpy.utils.unregister_class(FlipFluidHelperInitializeCacheObjects)
    bpy.utils.unregister_class(FlipFluidHelperStableRendering279)
    bpy.utils.unregister_class(FlipFluidHelperStableRendering28)
    bpy.utils.unregister_class(FlipFluidHelperSetLinearOverrideKeyframes)
    bpy.utils.unregister_class(FlipFluidHelperSaveBlendFile)
    bpy.utils.unregister_class(FlipFluidHelperBatchExportAnimatedMesh)
    bpy.utils.unregister_class(FlipFluidHelperBatchSkipReexport)
    bpy.utils.unregister_class(FlipFluidHelperBatchForceReexport)
    bpy.utils.unregister_class(FlipFluidEnableFluidParticleMenu)
    bpy.utils.unregister_class(FlipFluidEnableFluidParticleOutput)
    bpy.utils.unregister_class(FlipFluidDisplayEnableFluidParticlesTooltip)
    bpy.utils.unregister_class(FlipFluidEnableWhitewaterSimulation)
    bpy.utils.unregister_class(FlipFluidEnableWhitewaterMenu)
    bpy.utils.unregister_class(FlipFluidDisplayEnableWhitewaterTooltip)
    bpy.utils.unregister_class(FlipFluidEnableColorAttribute)
    bpy.utils.unregister_class(FlipFluidEnableColorMixAttribute)
    bpy.utils.unregister_class(FlipFluidEnableColorAttributeMenu)
    bpy.utils.unregister_class(FlipFluidEnableColorAttributeTooltip)
    bpy.utils.unregister_class(FlipFluidEnableViscosityAttribute)
    bpy.utils.unregister_class(FlipFluidEnableViscosityAttributeMenu)
    bpy.utils.unregister_class(FlipFluidEnableViscosityAttributeTooltip)
    bpy.utils.unregister_class(FlipFluidEnableDensityAttribute)
    bpy.utils.unregister_class(FlipFluidEnableDensityAttributeMenu)
    bpy.utils.unregister_class(FlipFluidEnableDensityAttributeTooltip)
    bpy.utils.unregister_class(FlipFluidEnableLifetimeAttribute)
    bpy.utils.unregister_class(FlipFluidEnableLifetimeAttributeMenu)
    bpy.utils.unregister_class(FlipFluidEnableLifetimeAttributeTooltip)
    bpy.utils.unregister_class(FlipFluidEnableSourceIDAttribute)
    bpy.utils.unregister_class(FlipFluidEnableSourceIDAttributeMenu)
    bpy.utils.unregister_class(FlipFluidEnableSourceIDAttributeTooltip)
    bpy.utils.unregister_class(FlipFluidMakeRelativeToBlendRenderOutput)
    bpy.utils.unregister_class(FlipFluidMakePrefixFilenameRenderOutput)
    bpy.utils.unregister_class(FlipFluidAutoLoadBakedFramesCMD)
    bpy.utils.unregister_class(FlipFluidCopySettingsFromActive)
    bpy.utils.unregister_class(FlipFluidMeasureObjectSpeed)
    bpy.utils.unregister_class(FlipFluidClearMeasureObjectSpeed)
    bpy.utils.unregister_class(FlipFluidDisableAddonInBlendFile)
    bpy.utils.unregister_class(FlipFluidEnableAddonInBlendFile)
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