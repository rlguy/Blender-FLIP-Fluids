# Blender FLIP Fluids Add-on
# Copyright (C) 2022 Ryan L. Guy
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

import bpy, os, pathlib, stat, subprocess, platform, math, mathutils, fnmatch, random, mathutils, datetime, shutil, traceback, re
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


class FlipFluidHelperRemesh(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_remesh"
    bl_label = "FLIP Fluids Remesh Collection"
    bl_description = ("Combine object geometry within a collection and remesh into a single object for use in the simulator." +
        " Optionally convert non-mesh objects to mesh, apply modifiers, and skip objects hidden from render." +
        " Saving is recommended before using this operator - this operator may take some time to compute depending on complexity" +
        " of the input geometry. Use the link next to this operator to view documentation and a video guide" + 
        " for using this feature")

    skip_hide_render_objects = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("skip_hide_render_objects"))

    apply_object_modifiers = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("apply_object_modifiers"))

    convert_objects_to_mesh = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("convert_objects_to_mesh"))


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

    object_type = StringProperty("TYPE_NONE")
    exec(vcu.convert_attribute_to_28("object_type"))


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


class FlipFluidHelperAddObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_add_objects"
    bl_label = "Add Objects"
    bl_description = "Add selected objects as FLIP Fluid objects"

    object_type = StringProperty("TYPE_NONE")
    exec(vcu.convert_attribute_to_28("object_type"))


    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) == 1:
            # Don't let user set domain object as another type while simulation is running
            obj = context.selected_objects[0]
            if obj.flip_fluid.is_domain():
                if obj.flip_fluid.domain.bake.is_simulation_running:
                    return False
        for obj in context.selected_objects:
            if obj.type == 'MESH' or obj.type == 'CURVE' or obj.type == 'EMPTY':
                return True
        return False


    def execute(self, context):
        original_active_object = vcu.get_active_object(context)
        for obj in context.selected_objects:
            if self.object_type == 'TYPE_FORCE_FIELD':
                if not (obj.type == 'MESH' or obj.type == 'EMPTY' or obj.type == 'CURVE'):
                    continue
            else:
                if not obj.type == 'MESH':
                    continue

            if obj.flip_fluid.is_domain() and obj.flip_fluid.domain.bake.is_simulation_running:
                # Ignore changing domain type if a simulation is running
                continue

            vcu.set_active_object(obj, context)
            bpy.ops.flip_fluid_operators.flip_fluid_add()
            obj.flip_fluid.object_type = self.object_type

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

    whitewater_type = StringProperty("TYPE_ALL")
    exec(vcu.convert_attribute_to_28("whitewater_type"))


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
        return vcu.is_blender_28()


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
        return vcu.is_blender_28() and dprops is not None


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
        return vcu.is_blender_28()


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
        return vcu.is_blender_28() and dprops is not None


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

    display_mode = StringProperty("TYPE_NONE")
    exec(vcu.convert_attribute_to_28("display_mode"))


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

    hide_render = BoolProperty(False)
    exec(vcu.convert_attribute_to_28("hide_render"))


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
            context.scene.frame_set(max_frameno)

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
    bl_description = "Enable viscosity solver and variable viscosity attribute in the Domain FLIP Fluid World panel"

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


class FlipFluidEnableLifetimeAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_lifetime_attribute"
    bl_label = "Enable Lifetime Attribute"
    bl_description = "Enable lifetime attribute in the Domain FLIP Fluid Surface and Domain FLIP Fluid Particles panel"

    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.surface.enable_lifetime_attribute = True
        dprops.particles.enable_lifetime_attribute = True
        return {'FINISHED'}


class FlipFluidEnableLifetimeAttributeMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "FLIP_FLUID_MENUS_MT_enable_lifetime_attribute_menu"

    def draw(self, context):
        self.layout.operator("flip_fluid_operators.enable_lifetime_attribute")


class FlipFluidEnableLifetimeAttributeTooltip(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_lifetime_attribute_tooltip"
    bl_label = "Enable Lifetime Attribute"
    bl_description = "Click to enable the lifetime attribute in the Domain FLIP Fluid Surface and Domain FLIP Fluid Particles panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_lifetime_attribute_menu")
        return {'FINISHED'}


class FlipFluidEnableSourceIDAttribute(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.enable_source_id_attribute"
    bl_label = "Enable Source ID Attribute"
    bl_description = "Enable source ID attribute in the Domain FLIP Fluid Surface and FLIP Fluid Particles panel"

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
    bl_description = "Click to enable the source ID attribute in the Domain FLIP Fluid Surface and FLIP Fluid Particles panel"


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        bpy.ops.wm.call_menu(name="FLIP_FLUID_MENUS_MT_enable_source_id_attribute_menu")
        return {'FINISHED'}


def is_geometry_node_point_cloud_detected(bl_mesh_cache_object=None):
    if not vcu.is_blender_31():
        return False

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

        search_string_start1 = "FF_MotionBlurWhitewater"
        search_string_start2 = "FF_MotionBlurFluidParticles"
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
    if not vcu.is_blender_31() or bl_object is None:
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


class FlipFluidHelperInitializeMotionBlur(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_initialize_motion_blur"
    bl_label = "Initialize Motion Blur"
    bl_description = ("Initialize all settings and Geometry Node groups required for motion blur rendering." + 
                      " This will be applied to the fluid surface, fluid particles, and whitewater particles if enabled." + 
                      " Node groups can be viewed in the geometry nodes editor and modifier")

    resource_prefix = StringProperty(default="FF_MotionBlur")
    exec(vcu.convert_attribute_to_28("resource_prefix"))


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def apply_modifier_settings(self, target_object, gn_modifier):
        gn_modifier["Input_2_use_attribute"] = 1
        gn_modifier["Input_2_attribute_name"] = 'flip_velocity'
        gn_modifier["Output_3_attribute_name"] = 'velocity'

        gn_name = gn_modifier.name
        if gn_name.startswith("FF_MotionBlurSurface"):
            # Depending on FLIP Fluids version, the GN set up may not
            # have these inputs. Available in FLIP Fluids 1.7.2 or later.
            try:
                # Enable Motion Blur
                gn_modifier["Input_6"] = True
            except:
                pass

        if gn_name.startswith("FF_MotionBlurWhitewater") or gn_name.startswith("FF_MotionBlurFluidParticles"):
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

            try:
                # Enable Point Cloud
                gn_modifier["Input_9"] = True
            except:
                pass

            try:
                # Enable Instancing
                gn_modifier["Input_10"] = False
            except:
                pass


    def execute(self, context):
        if not vcu.is_blender_31():
            self.report({'INFO'}, "Blender 3.1 or later is required for this feature")
            return {'CANCELLED'}

        if not context.scene.flip_fluid.is_domain_in_active_scene():
            self.report({"ERROR"}, 
                         "Active scene must contain domain object to use this operator. Select the scene that contains the domain object and try again.")
            return {'CANCELLED'}
        
        if context.scene.render.engine != 'CYCLES':
            context.scene.render.engine = 'CYCLES'
            self.report({'INFO'}, "Setting render engine to Cycles")
        if not context.scene.render.use_motion_blur:
            context.scene.render.use_motion_blur = True
            self.report({'INFO'}, "Enabled Cycles motion blur rendering")

        dprops = context.scene.flip_fluid.get_domain_properties()
        if not dprops.surface.enable_velocity_vector_attribute:
            dprops.surface.enable_velocity_vector_attribute = True
            self.report({'INFO'}, "Enabled generation of fluid surface velocity vector attributes in FLIP Fluid Surface panel (baking required)")

        if not dprops.particles.enable_fluid_particle_velocity_vector_attribute:
            dprops.particles.enable_fluid_particle_velocity_vector_attribute = True
            self.report({'INFO'}, "Enabled generation of fluid particle velocity vector attributes in FLIP Fluid Particles panel (baking required)")

        if not dprops.whitewater.enable_velocity_vector_attribute:
            dprops.whitewater.enable_velocity_vector_attribute = True
            self.report({'INFO'}, "Enabled generation of whitewater velocity vector attributes in FLIP Fluid Whitewater (baking required)")

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


    resource_prefix = StringProperty(default="FF_MotionBlur")
    exec(vcu.convert_attribute_to_28("resource_prefix"))


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def execute(self, context):
        if not vcu.is_blender_31():
            self.report({'INFO'}, "Blender 3.1 or later is required for this feature")
            return {'CANCELLED'}

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

    enable_motion_blur_rendering = BoolProperty(default=True)
    exec(vcu.convert_attribute_to_28("enable_motion_blur_rendering"))


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None


    def get_motion_blur_geometry_node_modifier(self, bl_object):
        if bl_object is None:
            return None
        for mod in bl_object.modifiers:
            if mod.type == "NODES" and mod.node_group and mod.node_group.name.startswith("FF_MotionBlur"):
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


class FlipFluidHelperInitializeCacheObjects(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_initialize_cache_objects"
    bl_label = "Initialize Cache Objects"
    bl_description = ("Initialize simulation meshes, modifiers, and data")

    cache_object_type = StringProperty(default="CACHE_OBJECT_TYPE_NONE")
    exec(vcu.convert_attribute_to_28("cache_object_type"))


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

    enable_state = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("enable_state"))


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

    save_as_blend_file = BoolProperty(default=True)
    exec(vcu.convert_attribute_to_28("save_as_blend_file"))


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


    enable_state = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("enable_state"))


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


    enable_state = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("enable_state"))


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


    enable_state = BoolProperty(True)
    exec(vcu.convert_attribute_to_28("enable_state"))


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


    def __init__(self):
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
            context.scene.frame_set(frameno)


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
            if vcu.is_blender_30():
                obj.visible_camera = is_enabled
                obj.visible_diffuse = is_enabled
                obj.visible_glossy = is_enabled
                obj.visible_transmission = is_enabled
                obj.visible_volume_scatter = is_enabled
                obj.visible_shadow = is_enabled
            else:
                obj.cycles_visibility.camera = is_enabled
                obj.cycles_visibility.transmission = is_enabled
                obj.cycles_visibility.diffuse = is_enabled
                obj.cycles_visibility.scatter = is_enabled
                obj.cycles_visibility.glossy = is_enabled
                obj.cycles_visibility.shadow = is_enabled
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
        

# List for objects
# Operator to add items to object list
class FlipFluidPassesAddItemToList(bpy.types.Operator):
    """Add selected items to the list of objects for rendering"""
    bl_idname = "flip_fluid_operators.add_item_to_list"
    bl_label = "Add Item to List"
    
    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        for obj in bpy.context.selected_objects:
            item = hprops.render_passes_objectlist.add()
            item.name = obj.name

        hprops.render_passes_objectlist_index = len(hprops.render_passes_objectlist) - 1

        return {'FINISHED'}

# Operator to remove items from object list
class FlipFluidPassesRemoveItemFromList(bpy.types.Operator):
    """Remove an item from the list of objects for rendering"""
    bl_idname = "flip_fluid_operators.remove_item_from_list"
    bl_label = "Remove Item from List"
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            hprops.render_passes_objectlist.remove(self.index)
            hprops.render_passes_objectlist_index = min(max(0, self.index - 1), len(hprops.render_passes_objectlist) - 1)
        return {'FINISHED'}


# Operator to toggle the catcher status
class FlipFluidPassesToggleCatcher(bpy.types.Operator):
    """Toggle catcher status for an item in the list"""
    bl_idname = "flip_fluid_operators.toggle_catcher"
    bl_label = "Toggle Catcher"
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        hprops = context.scene.flip_fluid_helper
        if 0 <= self.index < len(hprops.render_passes_objectlist):
            item = hprops.render_passes_objectlist[self.index]
            item.catcher = not item.catcher
        return {'FINISHED'}

# Custom UI List for objects
class FLIPFLUID_UL_passes_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.75, align=True)
            column1 = split.column(align=True)
            column1.label(text=item.name, icon='MESH_CUBE')
            column2 = split.column(align=True)
            column2.prop(item, "catcher", text="Catcher", toggle=True)
            #column2.operator("flip_fluid_operators.remove_item_from_list", text="", icon='REMOVE').index = index


# Runs every time the scene changes
def update_camera_screen_scale(bl_camera_screen, bl_camera):
    depth = bpy.context.scene.flip_fluid_helper.render_passes_camerascreen_distance
    camera_angle = bl_camera.data.angle
    camera_type = bl_camera.data.type
    camera_ortho_scale = bl_camera.data.ortho_scale
    
    resolution_x = bpy.context.scene.render.resolution_x
    resolution_y = bpy.context.scene.render.resolution_y
    pixel_aspect_x = bpy.context.scene.render.pixel_aspect_x
    pixel_aspect_y = bpy.context.scene.render.pixel_aspect_y
    aspect_ratio = (resolution_x * pixel_aspect_x) / (resolution_y * pixel_aspect_y)

    x_scale = y_scale = 1.0
    if camera_type == 'PERSP' or camera_type == 'PANO':
        x_scale = y_scale = -depth * math.tan(0.5 * camera_angle)
    elif camera_type == 'ORTHO': 
        x_scale = y_scale = 0.5 * camera_ortho_scale

    if aspect_ratio < 1.0:
        x_scale *= aspect_ratio
    else:
        y_scale *= (1.0 / aspect_ratio)

    bl_camera_screen.location = (0.0, 0.0, -depth / bl_camera.scale[2])
    bl_camera_screen.scale = (abs(x_scale / bl_camera.scale[0]), abs(y_scale / bl_camera.scale[1]), 1.0)


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
            self.report({'ERROR'}, "Camera object <" + str(hprops.render_passes_cameraselection) + "> not found")
            return {'CANCELLED'}


    def initialize_camera_screen_object(self, context):
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

        update_camera_screen_scale(bl_camera_screen, bl_camera)

        return bl_camera_screen


    def initialize_image_texture_material(self, bl_camera_screen, image_filepaths):
        # Check if material already exists and remove it
        mat_name = "ff_camera_screen"
        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])

        # Initialize material and nodes
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.remove(nodes.get('Principled BSDF'))

        output = nodes['Material Output']

        emission = nodes.new('ShaderNodeEmission')
        emission.location.x = output.location.x - 200
        emission.location.y = output.location.y

        texture = nodes.new('ShaderNodeTexImage')
        texture.location.x = emission.location.x - 300
        texture.location.y = output.location.y

        # Set the name and label of the texture node
        texture.name = "ff_camera_screen"
        texture.label = "ff_camera_screen"
        
        mat.node_tree.links.new(emission.inputs['Color'], texture.outputs['Color'])
        mat.node_tree.links.new(output.inputs['Surface'], emission.outputs['Emission'])
        bl_camera_screen.data.materials.append(mat)

        def get_trailing_number_from_string(s):
            m = re.search(r'\d+$', s)
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

        # Load selected files as image datablocks
        frame_start_image = None
        for filepath in image_filepaths:
            image = bpy.data.images.load(filepath)
            if frame_start_image is None:
                frame_start_image = image
            if filepath == frame_start_filepath:
                frame_start_image = image

        # Set texture node image sequence or single image
        if len(image_filepaths) > 1 and is_frame_sequence_found:
            texture.image = frame_start_image
            texture.image.source = 'SEQUENCE'
            texture.image_user.frame_duration = len(image_filepaths)
            texture.image_user.frame_start = frame_start
            texture.image_user.frame_offset = frame_start - 1
            texture.image_user.use_cyclic = True
            texture.image_user.use_auto_refresh = True
        else:
            texture.image = frame_start_image

        return texture.image



    def set_camera_background_image(self, context, image):
        hprops = context.scene.flip_fluid_helper
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        
        if bl_camera:
            # Remove existing background images
            bl_camera.data.background_images.clear()
            
            # Add new background image
            bg = bl_camera.data.background_images.new()
            bg.image = image
            bg.display_depth = 'BACK'


    def invoke(self, context, event):
        self.filepath = ""  # Clear the filepath field
        hprops = context.scene.flip_fluid_helper
        bl_camera = bpy.data.objects.get(hprops.render_passes_cameraselection)
        
        # Check if the camera already has a background image assigned
        if bl_camera and bl_camera.data.background_images:
            bg_images = bl_camera.data.background_images
            image_filepaths = [bg_image.image.filepath for bg_image in bg_images if bg_image.image is not None]
            if image_filepaths:
                self.execute_with_existing_images(context, image_filepaths)
                return {'FINISHED'}
        
        if 'ff_camera_screen' in context.scene.objects:
            self.report({'ERROR'}, "ff_camera_screen object already exists.")
            return {'CANCELLED'}
        return context.window_manager.fileselect_add(self) or {'RUNNING_MODAL'}

    def execute_with_existing_images(self, context, image_filepaths):
        bl_camera_screen = self.initialize_camera_screen_object(context)
        image = self.initialize_image_texture_material(bl_camera_screen, image_filepaths)
        self.set_camera_background_image(context, image)
        return {'FINISHED'}

    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        image_filepaths = [os.path.join(self.directory, f.name) for f in self.files]
        bl_camera_screen = self.initialize_camera_screen_object(context)
        image = self.initialize_image_texture_material(bl_camera_screen, image_filepaths)
        self.set_camera_background_image(context, image)
        return {'FINISHED'}

class FlipFluidPassesFixCompositingTextures(bpy.types.Operator):
    """Fixes all ff_camera_screen textures to match your background"""
    bl_idname = "flip_fluid_operators.helper_fix_compositingtextures"
    bl_label = "Fix Compositing Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find the ff_camera_screen object
        screen_obj = bpy.data.objects.get("ff_camera_screen")
        if not screen_obj:
            self.report({'ERROR'}, "There is no ff_camera_screen object. Please add the CameraScreen first.")
            return {'CANCELLED'}

        # Ensure the ff_camera_screen object has the correct material
        if "ff_camera_screen" not in [mat.name for mat in screen_obj.material_slots]:
            self.report({'ERROR'}, "ff_camera_screen object does not have a material named 'ff_camera_screen'.")
            return {'CANCELLED'}

        # Find the ff_camera_screen material
        screen_material = bpy.data.materials.get("ff_camera_screen")
        if not screen_material or not screen_material.use_nodes:
            self.report({'ERROR'}, "Material 'ff_camera_screen' not found or it does not use nodes.")
            return {'CANCELLED'}

        # Find the ff_camera_screen texture node in the ff_camera_screen material
        screen_texture_node = None
        for node in screen_material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.name == "ff_camera_screen":
                screen_texture_node = node
                break

        if not screen_texture_node or not screen_texture_node.image:
            self.report({'ERROR'}, "No valid ff_camera_screen texture node found in the material 'ff_camera_screen'.")
            return {'CANCELLED'}

        # Get the image from the ff_camera_screen texture node
        screen_image = screen_texture_node.image

        # Iterate over all objects and materials to update the ff_camera_screen texture nodes
        for obj in bpy.data.objects:
            if obj.name == "ff_camera_screen":
                continue

            for material_slot in obj.material_slots:
                material = material_slot.material
                if not material or not material.use_nodes:
                    continue

                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.name == "ff_camera_screen":
                        node.image = screen_image

        self.report({'INFO'}, "All compositing textures have been updated.")
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
        FlipFluidPassesToggleCatcher,
        FlipFluidPassesAddItemToList,
        FlipFluidPassesRemoveItemFromList,
        FLIPFLUID_UL_passes_items,
        FlipFluidPassesAddCameraScreen,
        FlipFluidPassesFixCompositingTextures,
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
    bpy.utils.unregister_class(FlipFluidPassesToggleCatcher)
    bpy.utils.unregister_class(FlipFluidPassesAddItemToList)
    bpy.utils.unregister_class(FlipFluidPassesRemoveItemFromList)
    bpy.utils.unregister_class(FLIPFLUID_UL_passes_items)
    bpy.utils.unregister_class(FlipFluidPassesAddCameraScreen)
    bpy.utils.unregister_class(FlipFluidPassesFixCompositingTextures)
    

