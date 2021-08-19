# Blender FLIP Fluids Add-on
# Copyright (C) 2020 Ryan L. Guy
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

import bpy, os, subprocess, platform, mathutils, fnmatch
from bpy.props import (
        BoolProperty,
        StringProperty
        )

from ..utils import version_compatibility_utils as vcu
from ..utils import export_utils
from ..objects import flip_fluid_aabb
from .. import render


def _select_make_active(context, active_object):
    for obj in context.selected_objects:
        vcu.select_set(obj, False)
    vcu.select_set(active_object, True)
    vcu.set_active_object(active_object, context)


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
        dprops.mesh_cache.initialize_cache_objects()
        surface_object = dprops.mesh_cache.surface.get_cache_object()
        if surface_object is None:
            return {'CANCELLED'}
        _select_make_active(context, surface_object)
        return {'FINISHED'}


class FlipFluidHelperSelectFoam(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_select_foam"
    bl_label = "Select Foam"
    bl_description = "Select the whitewater foam object"


    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        foam_object = dprops.mesh_cache.foam.get_cache_object()
        if foam_object is None:
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
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        bubble_object = dprops.mesh_cache.bubble.get_cache_object()
        if bubble_object is None:
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
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        spray_object = dprops.mesh_cache.spray.get_cache_object()
        if spray_object is None:
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
        return dprops is not None and dprops.whitewater.enable_whitewater_simulation


    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return {'CANCELLED'}
        dprops.mesh_cache.initialize_cache_objects()
        dust_object = dprops.mesh_cache.dust.get_cache_object()
        if dust_object is None:
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
            obj_bbox = flip_fluid_aabb.AABB.from_blender_object(obj)
            min_width = min(obj_bbox.xdim, obj_bbox.ydim, obj_bbox.zdim)
            min_width = max(min_width, eps)
            min_object_width = min(min_width, min_object_width)

        min_coverage_factor = 2.5
        min_coverage_width = min_coverage_factor * dx_estimate
        if min_object_width < min_coverage_width:
            new_resolution = resolution * (min_coverage_width / min_object_width)
            dprops.simulation.resolution = new_resolution


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
        for obj in context.selected_objects:
            if obj.flip_fluid.is_active:
                return True
        return False


    def execute(self, context):
        original_active_object = vcu.get_active_object(context)
        for obj in context.selected_objects:
            if not obj.type == 'MESH':
                continue
            vcu.set_active_object(obj, context)
            bpy.ops.flip_fluid_operators.flip_fluid_remove()
        vcu.set_active_object(original_active_object, context)
        return {'FINISHED'}


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

        particle_object = dprops.mesh_cache.foam.get_duplivert_object()
        if particle_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not particle_object.name in collection.objects:
                collection.objects.link(particle_object)
            if particle_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(particle_object)

        particle_object = dprops.mesh_cache.bubble.get_duplivert_object()
        if particle_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not particle_object.name in collection.objects:
                collection.objects.link(particle_object)
            if particle_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(particle_object)

        particle_object = dprops.mesh_cache.spray.get_duplivert_object()
        if particle_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not particle_object.name in collection.objects:
                collection.objects.link(particle_object)
            if particle_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(particle_object)

        particle_object = dprops.mesh_cache.dust.get_duplivert_object()
        if particle_object is not None:
            collection = self.initialize_child_collection(context, "WHITEWATER", mesh_collection)
            if not particle_object.name in collection.objects:
                collection.objects.link(particle_object)
            if particle_object.name in mesh_collection.objects:
                mesh_collection.objects.unlink(particle_object)

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

        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_dir = dprops.cache.get_cache_abspath()
        bakefiles_dir = os.path.join(cache_dir, "bakefiles")
        if not os.path.exists(bakefiles_dir):
            return {'CANCELLED'}

        bakefiles = os.listdir(bakefiles_dir)
        max_frameno = -1
        for f in bakefiles:
            base = f.split(".")[0]
            frameno = int(base[-6:])
            max_frameno = max(frameno, max_frameno)
        context.scene.frame_set(max_frameno)
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
        if not dprops.render.whitewater_display_settings_expanded:
            dprops.render.whitewater_display_settings_expanded = True
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


class FlipFluidHelperCommandLineBake(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake"
    bl_label = "Launch Bake"
    bl_description = ("Launch a new command line window and start baking." +
                     " The .blend file will need to be saved before using" +
                     " this operator. Only available on Windows OS." +
                     " For MacOS/Linux, use the copy operator to copy the command to the clipboard")


    @classmethod
    def poll(cls, context):
        system = platform.system()
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath) and system == "Windows"


    def execute(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        script_path = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.dirname(script_path)
        script_path = os.path.join(script_path, "resources", "command_line_scripts", "run_simulation.py")

        system = platform.system()
        if system == "Windows":
            if vcu.is_blender_28():
                blender_exe_path = bpy.app.binary_path
                if " " in blender_exe_path:
                    # Some versions of Blender 2.8+ don't support spaces in the executable path
                    blender_exe_path = "blender.exe"
            else:
                # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
                # executable path, so we'll just use blender.exe and hope that no other addon has
                # changed Blender's working directory
                blender_exe_path = "blender.exe"
            command = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "--python", script_path]
        elif system == "Darwin":
            # Feature not available on MacOS
            return {'CANCELLED'}
        elif system == "Linux":
            # Feature not available on Linux
            return {'CANCELLED'}

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
        prefs = vcu.get_addon_preferences()
        launch_attempts = prefs.cmd_bake_max_attempts
        launch_attempts_text = str(launch_attempts + 1)

        if launch_attempts == 0:
            # Launch with a single command
            subprocess.call(command, shell=True)
        else:
            # Launch using .bat file that can re-launch after crash is detected
            bat_template_path = os.path.dirname(os.path.realpath(__file__))
            bat_template_path = os.path.dirname(bat_template_path)
            bat_template_path = script_path = os.path.join(bat_template_path, "resources", "command_line_scripts", "cmd_bake_template.bat")
            with open(bat_template_path, 'r') as f:
                bat_text = f.read()

            bat_text = bat_text.replace("MAX_LAUNCH_ATTEMPTS", launch_attempts_text)
            bat_text = bat_text.replace("COMMAND_OPERATION", command_text)
            
            dprops = context.scene.flip_fluid.get_domain_properties()
            cache_directory = dprops.cache.get_cache_abspath()
            cache_scripts_directory = os.path.join(cache_directory, "scripts")
            if not os.path.exists(cache_scripts_directory):
                os.makedirs(cache_scripts_directory)

            cmd_bake_script_filepath = os.path.join(cache_scripts_directory, "cmd_bake.bat")
            with open(cmd_bake_script_filepath, 'w') as f:
                f.write(bat_text)

            os.startfile(cmd_bake_script_filepath)

        info_msg = "Launched command line baking window. If the baking process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line baking, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Baking-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineBakeToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_bake_to_clipboard"
    bl_label = "Copy Bake Command to Clipboard"
    bl_description = ("Copy command for baking to your system clipboard." +
                     " The .blend file will need to be saved before using" +
                     " this operator")


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def execute(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return {'CANCELLED'}

        script_path = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.dirname(script_path)
        script_path = os.path.join(script_path, "resources", "command_line_scripts", "run_simulation.py")

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" --python \"" + script_path + "\""
        bpy.context.window_manager.clipboard = command_text

        info_msg = "Copied the following baking command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line baking, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Baking-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


class FlipFluidHelperCommandLineRender(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render"
    bl_label = "Launch Render"
    bl_description = ("Launch a new command line window and start rendering the animation." +
                     " The .blend file will need to be saved before using this operator." +
                     " Only available on Windows OS. For MacOS/Linux, use" +
                     " the copy operator to copy the command to the clipboard")


    @classmethod
    def poll(cls, context):
        system = platform.system()
        return bool(bpy.data.filepath) and system == "Windows"


    def execute(self, context):        
        system = platform.system()
        if system == "Windows":
            if vcu.is_blender_28():
                blender_exe_path = bpy.app.binary_path
                if " " in blender_exe_path:
                    # Some versions of Blender 2.8+ don't support spaces in the executable path
                    blender_exe_path = "blender.exe"
            else:
                # subproccess.call() in Blender 2.79 Python does not seem to support spaces in the 
                # executable path, so we'll just use blender.exe and hope that no other addon has
                # changed Blender's working directory
                blender_exe_path = "blender.exe"
            command = ["start", "cmd", "/k", blender_exe_path, "--background", bpy.data.filepath, "-a"]
        elif system == "Darwin":
            # Feature not available on MacOS
            return {'CANCELLED'}
        elif system == "Linux":
            # Feature not available on Linux
            return {'CANCELLED'}

        subprocess.call(command, shell=True)

        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" -a"

        info_msg = "Launched command line render window. If the render process did not begin,"
        info_msg += " this may be caused by a conflict with another addon or a security feature of your OS that restricts"
        info_msg += " automatic command execution. You may try copying the following command manually into a command line window:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Rendering-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}



class FlipFluidHelperCommandLineRenderToClipboard(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_command_line_render_to_clipboard"
    bl_label = "Launch Render"
    bl_description = ("Copy command for rendering to your system clipboard." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        system = platform.system()
        return bool(bpy.data.filepath) and system == "Windows"


    def execute(self, context):
        
        command_text = "\"" + bpy.app.binary_path + "\" --background \"" +  bpy.data.filepath + "\" -a"
        bpy.context.window_manager.clipboard = command_text
          
        info_msg = "Copied the following render command to your clipboard:\n\n"
        info_msg += command_text + "\n\n"
        info_msg += "For more information on command line rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Rendering-from-the-Command-Line"
        self.report({'INFO'}, info_msg)

        return {'FINISHED'}


def get_render_output_info():
    full_path = bpy.path.abspath(bpy.context.scene.render.filepath)
    directory_path = full_path

    file_prefix = os.path.basename(directory_path)
    if file_prefix:
       directory_path = os.path.dirname(directory_path)

    file_format_to_suffix = {
        "BMP"                 : ".bmp",
        "IRIS"                : ".rgb",
        "PNG"                 : ".png",
        "JPEG"                : ".jpg",
        "JPEG2000"            : ".jp2",
        "TARGA"               : ".tga",
        "TARGA_RAW"           : ".tga",
        "CINEON"              : ".cin",
        "DPX"                 : ".dpx",
        "OPEN_EXR_MULTILAYER" : ".exr",
        "OPEN_EXR"            : ".exr",
        "HDR"                 : ".hdr",
        "TIFF"                : ".tif"
    }

    file_format = bpy.context.scene.render.image_settings.file_format
    if file_format not in file_format_to_suffix:
        self.report({'ERROR'}, "Render output file format must be an image format.")
        return None, None, None

    file_suffix = file_format_to_suffix[file_format]

    return directory_path, file_prefix, file_suffix


class FlipFluidHelperCommandLineRenderToScriptfile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_cmd_render_to_scriptfile"
    bl_label = "Generate Batch File"
    bl_description = ("Generates a Windows batch file to render all frames one-by-one." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        system = platform.system()
        return bool(bpy.data.filepath) and system == "Windows"


    def get_missing_frames(self):
        directory_path, file_prefix, file_suffix = get_render_output_info()

        filenames = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        filenames = [f for f in filenames if f.startswith(file_prefix) and f.endswith(file_suffix)]
        frame_numbers = []
        for f in filenames:
            try:
                f = f[len(file_prefix):-len(file_suffix)]
                frame_numbers.append(int(f))
            except:
                pass

        frame_exists = {}
        for n in frame_numbers:
            frame_exists[n] = True

        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        missing_frames = []
        for i in range(frame_start, frame_end + 1):
            if not i in frame_exists:
                missing_frames.append(i)

        return missing_frames


    def generate_file_string(self, missing_frames):
        blender_exe_path = "\"" + bpy.app.binary_path + "\""
        blend_path = "\"" + bpy.data.filepath + "\""

        file_text = "echo.\n"
        for n in missing_frames:
            command_text = blender_exe_path + " -b " + blend_path + " -f " + str(n)
            file_text += command_text + "\n"

        return file_text


    def execute(self, context):
        directory_path, file_prefix, file_suffix = get_render_output_info()
        if not directory_path:
            return {'CANCELLED'}

        more_info_string = "For more information on batch rendering, visit our documentation:\n"
        more_info_string += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools\n"
        render_output_info_string = "View the rendered files at <" + directory_path + ">\n"

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        missing_frames = self.get_missing_frames()
        if not missing_frames:
            info_msg = "No batch file generated! All frames have already been rendered.\n"
            info_msg += render_output_info_string + "\n"
            info_msg += more_info_string
            self.report({'INFO'}, info_msg)
            return {'FINISHED'}

        file_text = self.generate_file_string(missing_frames)
        blend_directory = os.path.dirname(bpy.data.filepath)
        batch_filename = "RENDER_" + bpy.path.basename(bpy.context.blend_data.filepath) + ".bat"
        batch_filepath = os.path.join(blend_directory, batch_filename)
        with open(batch_filepath, "w") as renderscript_file:
            renderscript_file.write(file_text)

        total_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
        info_msg = "\nA batch file has been generated here: <" + batch_filepath + ">\n"
        info_msg += render_output_info_string + "\n"
        info_msg += str(total_frames - len(missing_frames)) + " frames in the " + file_suffix + " file format have already been rendered!\n"
        info_msg += str(len(missing_frames)) + " frames are not yet rendered!\n\n"
        info_msg += more_info_string

        self.report({'INFO'}, info_msg)
        
        return {'FINISHED'}


class FlipFluidHelperRunScriptfile(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_run_scriptfile"
    bl_label = "Launch Batch File Render"
    bl_description = ("Runs the generated batch file. If no batch file has been generated, one will be created automatically." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        directory = os.path.dirname(bpy.data.filepath)
        blend_filename = bpy.path.basename(bpy.context.blend_data.filepath)
        script_filename = "RENDER_" + blend_filename + ".bat"
        batch_filepath = os.path.join(directory, script_filename)

        if not os.path.isfile(batch_filepath):
            bpy.ops.flip_fluid_operators.helper_cmd_render_to_scriptfile()
            if not os.path.isfile(batch_filepath):
                self.report({'ERROR'}, "Unable to generate the render script.")

        os.startfile(batch_filepath)
          
        info_msg = "Beginning to run the renderscript!\n\n"
        info_msg += "For more information on batchfile rendering, visit our documentation:\n"
        info_msg += "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Helper-Menu-Settings#command-line-tools"
        self.report({'INFO'}, info_msg)
        return {'FINISHED'}

    
class FlipFluidHelperOpenOutputFolder(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.helper_open_outputfolder"
    bl_label = "Opens The Output Folder"
    bl_description = ("Opens the output-folder that is set in the output settings. If the folder does not exist, it will be created." +
                     " The .blend file will need to be saved before using this operator")


    @classmethod
    def poll(cls, context):
        return bool(bpy.data.filepath)


    def execute(self, context):
        directory_path, file_prefix, file_suffix = get_render_output_info()
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        os.startfile(directory_path)
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


    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
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


def register():
    bpy.utils.register_class(FlipFluidHelperSelectDomain)
    bpy.utils.register_class(FlipFluidHelperSelectSurface)
    bpy.utils.register_class(FlipFluidHelperSelectFoam)
    bpy.utils.register_class(FlipFluidHelperSelectBubble)
    bpy.utils.register_class(FlipFluidHelperSelectSpray)
    bpy.utils.register_class(FlipFluidHelperSelectDust)
    bpy.utils.register_class(FlipFluidHelperSelectObjects)
    bpy.utils.register_class(FlipFluidHelperCreateDomain)
    bpy.utils.register_class(FlipFluidHelperAddObjects)
    bpy.utils.register_class(FlipFluidHelperRemoveObjects)
    bpy.utils.register_class(FlipFluidHelperOrganizeOutliner)
    bpy.utils.register_class(FlipFluidHelperSeparateFLIPMeshes)
    bpy.utils.register_class(FlipFluidHelperUndoOrganizeOutliner)
    bpy.utils.register_class(FlipFluidHelperUndoSeparateFLIPMeshes)
    bpy.utils.register_class(FlipFluidHelperSetObjectViewportDisplay)
    bpy.utils.register_class(FlipFluidHelperSetObjectRenderDisplay)
    bpy.utils.register_class(FlipFluidHelperLoadLastFrame)
    bpy.utils.register_class(FlipFluidHelperCommandLineBake)
    bpy.utils.register_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRender)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.register_class(FlipFluidHelperCommandLineRenderToScriptfile)
    bpy.utils.register_class(FlipFluidHelperRunScriptfile)
    bpy.utils.register_class(FlipFluidHelperOpenOutputFolder)
    bpy.utils.register_class(FlipFluidHelperStableRendering279)
    bpy.utils.register_class(FlipFluidHelperStableRendering28)
    bpy.utils.register_class(FlipFluidHelperSetLinearOverrideKeyframes)
    bpy.utils.register_class(FlipFluidHelperSaveBlendFile)
    bpy.utils.register_class(FlipFluidHelperBatchSkipReexport)
    bpy.utils.register_class(FlipFluidHelperBatchForceReexport)

    bpy.utils.register_class(FlipFluidEnableWhitewaterSimulation)
    bpy.utils.register_class(FlipFluidEnableWhitewaterMenu)
    bpy.utils.register_class(FlipFluidDisplayEnableWhitewaterTooltip)


def unregister():
    bpy.utils.unregister_class(FlipFluidHelperSelectDomain)
    bpy.utils.unregister_class(FlipFluidHelperSelectSurface)
    bpy.utils.unregister_class(FlipFluidHelperSelectFoam)
    bpy.utils.unregister_class(FlipFluidHelperSelectBubble)
    bpy.utils.unregister_class(FlipFluidHelperSelectSpray)
    bpy.utils.unregister_class(FlipFluidHelperSelectDust)
    bpy.utils.unregister_class(FlipFluidHelperSelectObjects)
    bpy.utils.unregister_class(FlipFluidHelperCreateDomain)
    bpy.utils.unregister_class(FlipFluidHelperAddObjects)
    bpy.utils.unregister_class(FlipFluidHelperRemoveObjects)
    bpy.utils.unregister_class(FlipFluidHelperOrganizeOutliner)
    bpy.utils.unregister_class(FlipFluidHelperSeparateFLIPMeshes)
    bpy.utils.unregister_class(FlipFluidHelperUndoOrganizeOutliner)
    bpy.utils.unregister_class(FlipFluidHelperUndoSeparateFLIPMeshes)
    bpy.utils.unregister_class(FlipFluidHelperSetObjectViewportDisplay)
    bpy.utils.unregister_class(FlipFluidHelperSetObjectRenderDisplay)
    bpy.utils.unregister_class(FlipFluidHelperLoadLastFrame)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBake)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineBakeToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRender)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderToClipboard)
    bpy.utils.unregister_class(FlipFluidHelperCommandLineRenderToScriptfile)
    bpy.utils.unregister_class(FlipFluidHelperRunScriptfile)
    bpy.utils.unregister_class(FlipFluidHelperOpenOutputFolder)
    bpy.utils.unregister_class(FlipFluidHelperStableRendering279)
    bpy.utils.unregister_class(FlipFluidHelperStableRendering28)
    bpy.utils.unregister_class(FlipFluidHelperSetLinearOverrideKeyframes)
    bpy.utils.unregister_class(FlipFluidHelperSaveBlendFile)
    bpy.utils.unregister_class(FlipFluidHelperBatchSkipReexport)
    bpy.utils.unregister_class(FlipFluidHelperBatchForceReexport)

    bpy.utils.unregister_class(FlipFluidEnableWhitewaterSimulation)
    bpy.utils.unregister_class(FlipFluidEnableWhitewaterMenu)
    bpy.utils.unregister_class(FlipFluidDisplayEnableWhitewaterTooltip)

