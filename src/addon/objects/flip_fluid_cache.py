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

import bpy, os, struct, math, json, mathutils, traceback
import numpy as np

from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        StringProperty,
        PointerProperty
        )

from .flip_fluid_aabb import AABB
from .flip_fluid_attribute import FLIPFluidVirtualUVWAttribute
from .. import render
from ..operators import draw_particles_operators
from ..operators import draw_force_field_operators
from ..operators import helper_operators
from ..utils import cache_utils
from ..utils import version_compatibility_utils as vcu
from .. import types
from ..types import DataType, MeshType, CacheObjectType

DISABLE_MESH_CACHE_LOAD = False
GL_POINT_CACHE_DATA = {}
GL_FORCE_FIELD_CACHE_DATA = {}


def add_mesh_data_attribute(bl_object, bl_attribute_name, bl_attribute_type, bl_attribute_domain, attribute_values):
    if bl_object is None:
        return
    if len(attribute_values) == 0:
        return

    try:
        bl_attribute = bl_object.data.attributes.get(bl_attribute_name)
        bl_object.data.attributes.remove(bl_attribute)
    except:
        pass

    bl_attribute = bl_object.data.attributes.new(bl_attribute_name, bl_attribute_type, bl_attribute_domain)
    if bl_attribute_type.endswith("VECTOR"):
        bl_attribute.data.foreach_set("vector", attribute_values)
    else:
        bl_attribute.data.foreach_set("value", attribute_values)


class EnabledMeshCacheObjects:
    fluid_surface = False
    fluid_particles = False
    whitewater_particles = False
    debug_obstacle = False


class FLIPFluidMeshBounds(bpy.types.PropertyGroup):
    x:      FloatProperty(default=0.0)
    y:      FloatProperty(default=0.0)
    z:      FloatProperty(default=0.0)
    width:  FloatProperty(default=1.0)
    height: FloatProperty(default=1.0)
    depth:  FloatProperty(default=1.0)
    dx:     FloatProperty(default=1.0)
    isize:  IntProperty(default=1)
    jsize:  IntProperty(default=1)
    ksize:  IntProperty(default=1)
    is_set: BoolProperty(default=False)


    def set(self, bounds_dict):
        if bounds_dict is None:
            self.reset()
            return
        self.x, self.y, self.z = bounds_dict['x'], bounds_dict['y'], bounds_dict['z']
        self.width = bounds_dict['width']
        self.height = bounds_dict['height']
        self.depth = bounds_dict['depth']
        self.dx = bounds_dict['dx']
        self.isize = bounds_dict['isize']
        self.jsize = bounds_dict['jsize']
        self.ksize = bounds_dict['ksize']


    def reset(self):
        for prop_name in self.__annotations__.keys():
            self.property_unset(prop_name)


    def is_set(self):
        return self.is_set


class FlipFluidLoadedMeshData(bpy.types.PropertyGroup):
    mesh_prefix:                            StringProperty(default="mesh_prefix")
    enable_velocity_attribute:              BoolProperty(default=False)
    enable_vorticity_attribute:             BoolProperty(default=False)
    enable_speed_attribute:                 BoolProperty(default=False)
    enable_age_attribute:                   BoolProperty(default=False)
    enable_color_attribute:                 BoolProperty(default=False)
    enable_uvw_attribute:                   BoolProperty(default=False)
    enable_source_id_attribute:             BoolProperty(default=False)
    enable_viscosity_attribute:             BoolProperty(default=False)
    enable_density_attribute:               BoolProperty(default=False)
    enable_id_attribute:                    BoolProperty(default=False)
    enable_uid_attribute:                   BoolProperty(default=False)
    enable_lifetime_attribute:              BoolProperty(default=False)
    enable_whitewater_proximity_attribute:  BoolProperty(default=False)
    wwp_import_percentage:                  IntProperty(default=0)
    ffp3_surface_import_percentage:         FloatProperty(default=0)
    ffp3_boundary_import_percentage:        FloatProperty(default=0)
    ffp3_interior_import_percentage:        FloatProperty(default=0)
    is_rendering:                           BoolProperty(default=True)
    frame:                                  IntProperty(default=-1)


    def reset(self):
        for prop_name in self.__annotations__.keys():
            self.property_unset(prop_name)


class FlipFluidMeshCache(bpy.types.PropertyGroup):
    # Object data
    cache_object_default_name:              StringProperty(default="")
    cache_object:                           PointerProperty(type=bpy.types.Object)
    cache_object_type:                      StringProperty(default=CacheObjectType.NONE)

    # Mesh import
    mesh_prefix:                            StringProperty(default="")
    mesh_display_name_prefix:               StringProperty(default="")
    mesh_file_extension:                    StringProperty(default="")

    wwp_import_percentage:                  IntProperty(default=100)
    ffp3_surface_import_percentage:         FloatProperty(default=0)
    ffp3_boundary_import_percentage:        FloatProperty(default=0)
    ffp3_interior_import_percentage:        FloatProperty(default=0)

    current_loaded_frame:                   IntProperty(default=-1)

    # Mesh attributes
    enable_velocity_attribute:              BoolProperty(default=False)
    enable_vorticity_attribute:             BoolProperty(default=False)
    enable_speed_attribute:                 BoolProperty(default=False)
    enable_age_attribute:                   BoolProperty(default=False)
    enable_color_attribute:                 BoolProperty(default=False)
    enable_uvw_attribute:                   BoolProperty(default=False)
    enable_source_id_attribute:             BoolProperty(default=False)
    enable_viscosity_attribute:             BoolProperty(default=False)
    enable_density_attribute:               BoolProperty(default=False)
    enable_id_attribute:                    BoolProperty(default=False)
    enable_uid_attribute:                   BoolProperty(default=False)
    enable_lifetime_attribute:              BoolProperty(default=False)
    enable_whitewater_proximity_attribute:  BoolProperty(default=False)

    # Virtual attributes
    virtual_uvw_attribute:         PointerProperty(type=FLIPFluidVirtualUVWAttribute)

    # Loaded data properties
    loaded_frame_data: PointerProperty(type=FlipFluidLoadedMeshData)
    bounds:            PointerProperty(type=FLIPFluidMeshBounds)


    def load_post(self):
        self.reset_virtual_uvw_attribute()


    def cache_update_callback(self):
        self.reset_virtual_uvw_attribute()


    def reset_virtual_uvw_attribute(self):
        self.virtual_uvw_attribute.reset()


    def reset_enabled_mesh_attributes(self):
        prop_names = [
            "enable_velocity_attribute",
            "enable_vorticity_attribute",
            "enable_speed_attribute",
            "enable_age_attribute",
            "enable_color_attribute",
            "enable_uvw_attribute",
            "enable_source_id_attribute",
            "enable_viscosity_attribute",
            "enable_density_attribute",
            "enable_id_attribute",
            "enable_uid_attribute",
            "enable_lifetime_attribute",
            "enable_whitewater_proximity_attribute",
        ]

        for name in prop_names:
            self.property_unset(name)


    def is_surface(self):
        return self.cache_object_type == CacheObjectType.SURFACE


    def is_fluid_particles(self):
        return self.cache_object_type == CacheObjectType.FLUID_PARTICLES


    def is_whitewater(self):
        return self.cache_object_type in types.WHITEWATER_CACHE_OBJECT_TYPES


    def is_obstacle(self):
        return self.cache_object_type == CacheObjectType.OBSTACLE_DEBUG


    def get_mesh_type(self):
        if self.is_surface():
            return MeshType.SURFACE
        elif self.is_obstacle():
            return MeshType.OBSTACLE
        elif self.is_whitewater():
            return MeshType.WHITEWATER
        elif self.is_fluid_particles():
            return MeshType.FLUID_PARTICLES
        else:
            raise Exception("FLIP Fluids Error: Unknown MeshType")


    def _get_cycles_use_motion_blur(self, bl_object):
        if vcu.is_cycles_enabled():
            return bl_object.cycles.use_motion_blur
        else:
            return False


    def _set_cycles_use_motion_blur(self, bl_object, bool_value):
        vcu.set_cycles_property(bl_object, "use_motion_blur", bool_value)


    def _is_object_motion_blur_enabled(self, bl_object_list):
        for bl_object in bl_object_list:
            if bl_object is None:
                continue
            if self._get_cycles_use_motion_blur(bl_object):
                return True
        return False


    def _initialize_cache_object_fluid_surface(self, bl_cache_object):
        resource_filepath = vcu.get_geometry_nodes_blend_filepath()

        gn_modifier = helper_operators.add_geometry_node_modifier(bl_cache_object, resource_filepath, "FF_GeometryNodesSurface")

        bl_domain_object = bpy.context.scene.flip_fluid.get_domain_object()

        # Depending on FLIP Fluids version, the GN set up may not
        # have these inputs. Available in FLIP Fluids 1.7.2 or later.
        key_value_pairs = [
            ("Input_6",                 True),                            # Enable Motion Blur
            ("Socket_7",                bl_domain_object),                # FLIP Domain Object
            ]

        for (key, value) in key_value_pairs:
            vcu.set_geometry_nodes_modifier_value(gn_modifier, key, value, ignore_errors=True)

        # Initialize with enabled object motion blur if other FLIP meshes have this enabled
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            other_mesh_objects = [
                    dprops.mesh_cache.particles.get_cache_object(),
                    dprops.mesh_cache.foam.get_cache_object(),
                    dprops.mesh_cache.bubble.get_cache_object(),
                    dprops.mesh_cache.spray.get_cache_object(),
                    dprops.mesh_cache.dust.get_cache_object()
                    ]

            if self._is_object_motion_blur_enabled(other_mesh_objects):
                self._set_cycles_use_motion_blur(bl_cache_object, True)


    def _initialize_cache_object_fluid_particles(self, bl_cache_object):
        resource_filepath = vcu.get_geometry_nodes_blend_filepath()
        gn_modifier = helper_operators.add_geometry_node_modifier(bl_cache_object, resource_filepath, "FF_GeometryNodesFluidParticles")

        bl_domain_object = bpy.context.scene.flip_fluid.get_domain_object()

        bl_surface_object = None
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            bl_surface_object = dprops.mesh_cache.surface.get_cache_object()

        # Depending on FLIP Fluids version, the GN set up may not
        # have these inputs. Available in FLIP Fluids 1.7.2 or later.
        key_value_pairs = [
            ("Input_5",                 bl_cache_object.active_material), # Material
            ("Input_8",                 True),                            # Enable Motion Blur
            ("Socket_46",               bl_domain_object),                # FLIP Domain Object
            ("Socket_49",               bl_surface_object),               # FLIP Surface Object
            ]

        for (key, value) in key_value_pairs:
            vcu.set_geometry_nodes_modifier_value(gn_modifier, key, value, ignore_errors=True)

        # Initialize with enabled object motion blur if other FLIP meshes have this enabled
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            other_mesh_objects = [
                    dprops.mesh_cache.surface.get_cache_object(),
                    dprops.mesh_cache.foam.get_cache_object(),
                    dprops.mesh_cache.bubble.get_cache_object(),
                    dprops.mesh_cache.spray.get_cache_object(),
                    dprops.mesh_cache.dust.get_cache_object()
                    ]

            if self._is_object_motion_blur_enabled(other_mesh_objects):
                self._set_cycles_use_motion_blur(bl_cache_object, True)


    def _initialize_cache_object_whitewater_particles(self, bl_cache_object):
        resource_filepath = vcu.get_geometry_nodes_blend_filepath()

        if   self.cache_object_type == CacheObjectType.WHITEWATER_FOAM:
            resource_name = "FF_GeometryNodesWhitewaterFoam"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_BUBBLE:
            resource_name = "FF_GeometryNodesWhitewaterBubble"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_SPRAY:
            resource_name = "FF_GeometryNodesWhitewaterSpray"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_DUST:
            resource_name = "FF_GeometryNodesWhitewaterDust"
        else:
            return

        gn_modifier = helper_operators.add_geometry_node_modifier(bl_cache_object, resource_filepath, resource_name)

        bl_domain_object = bpy.context.scene.flip_fluid.get_domain_object()

        bl_surface_object = None
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            bl_surface_object = dprops.mesh_cache.surface.get_cache_object()

        # Depending on FLIP Fluids version, the GN set up may not
        # have these inputs. Available in FLIP Fluids 1.7.2 or later.
        key_value_pairs = [
            ("Input_5",                 bl_cache_object.active_material), # Material
            ("Input_8",                 True),                            # Enable Motion Blur
            ("Socket_29",               bl_domain_object),                # FLIP Domain Object
            ("Socket_32",               bl_surface_object),               # FLIP Surface Object
            ]

        for (key, value) in key_value_pairs:
            vcu.set_geometry_nodes_modifier_value(gn_modifier, key, value, ignore_errors=True)


        # Initialize with enabled object motion blur if other FLIP meshes have this enabled
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is not None:
            other_mesh_objects = [
                    dprops.mesh_cache.surface.get_cache_object(),
                    dprops.mesh_cache.particles.get_cache_object()
                    ]

            if self._is_object_motion_blur_enabled(other_mesh_objects):
                self._set_cycles_use_motion_blur(bl_cache_object, True)


    def _update_ff_geometry_nodes_modifier_domain_object(self, bl_cache_object):
        if   self.cache_object_type == CacheObjectType.SURFACE:
            resource_name = "FF_GeometryNodesSurface"
            socket_key = "Socket_7"
        elif self.cache_object_type == CacheObjectType.FLUID_PARTICLES:
            resource_name = "FF_GeometryNodesFluidParticles"
            socket_key = "Socket_46"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_FOAM:
            resource_name = "FF_GeometryNodesWhitewaterFoam"
            socket_key = "Socket_29"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_BUBBLE:
            resource_name = "FF_GeometryNodesWhitewaterBubble"
            socket_key = "Socket_29"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_SPRAY:
            resource_name = "FF_GeometryNodesWhitewaterSpray"
            socket_key = "Socket_29"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_DUST:
            resource_name = "FF_GeometryNodesWhitewaterDust"
            socket_key = "Socket_29"
        else:
            return

        bl_domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        if bl_domain_object is None:
            return

        gn_modifier = helper_operators.get_geometry_node_modifier(bl_cache_object, resource_name)
        if gn_modifier is None:
            return

        if vcu.get_geometry_nodes_modifier_value(gn_modifier, socket_key, ignore_errors=True) != bl_domain_object:
            vcu.set_geometry_nodes_modifier_value(gn_modifier, socket_key, bl_domain_object, ignore_errors=True)


    def _update_ff_geometry_nodes_modifier_fluid_surface_object(self, bl_cache_object):
        if self.cache_object_type == 'CACHE_OBJECT_TYPE_SURFACE':
            # Avoid circular dependency
            return

        if   self.cache_object_type == CacheObjectType.FLUID_PARTICLES:
            resource_name = "FF_GeometryNodesFluidParticles"
            socket_key = "Socket_49"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_FOAM:
            resource_name = "FF_GeometryNodesWhitewaterFoam"
            socket_key = "Socket_32"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_BUBBLE:
            resource_name = "FF_GeometryNodesWhitewaterBubble"
            socket_key = "Socket_32"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_SPRAY:
            resource_name = "FF_GeometryNodesWhitewaterSpray"
            socket_key = "Socket_32"
        elif self.cache_object_type == CacheObjectType.WHITEWATER_DUST:
            resource_name = "FF_GeometryNodesWhitewaterDust"
            socket_key = "Socket_32"
        else:
            return

        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        bl_surface_object = dprops.mesh_cache.surface.get_cache_object()
        if bl_surface_object is None:
            return

        gn_modifier = helper_operators.get_geometry_node_modifier(bl_cache_object, resource_name)
        if gn_modifier is None:
            return

        if vcu.get_geometry_nodes_modifier_value(gn_modifier, socket_key, ignore_errors=True) != bl_surface_object:
            vcu.set_geometry_nodes_modifier_value(gn_modifier, socket_key, bl_surface_object, ignore_errors=True)


    def _update_ff_geometry_nodes_modifier(self, bl_cache_object):
        self._update_ff_geometry_nodes_modifier_domain_object(bl_cache_object)
        self._update_ff_geometry_nodes_modifier_fluid_surface_object(bl_cache_object)


    def initialize_cache_object(self):
        if not cache_utils.is_domain_set() or self._is_cache_object_initialized():
            return

        domain_object = cache_utils.get_domain_object()
        default_object_name = self.cache_object_default_name
        mesh_data_name = default_object_name + "_mesh"

        mesh_data = bpy.data.meshes.new(mesh_data_name)
        mesh_data.from_pydata([], [], [])
        cache_object = bpy.data.objects.new(default_object_name, mesh_data)
        cache_object.parent = domain_object
        cache_object.lock_location = (True, True, True)
        cache_object.lock_rotation = (True, True, True)
        cache_object.lock_scale = (True, True, True)
        vcu.link_fluid_mesh_object(cache_object)

        if self.cache_object_type in (CacheObjectType.SURFACE, CacheObjectType.OBSTACLE_DEBUG):
            smooth_mod = cache_object.modifiers.new("FF_Smooth", "SMOOTH")
            smooth_mod.factor = 1.5
            smooth_mod.iterations = 0

        self._set_cycles_use_motion_blur(cache_object, False)
        self._initialize_cache_object_octane(cache_object)

        if self.cache_object_type == CacheObjectType.SURFACE:
            self._initialize_cache_object_fluid_surface(cache_object)

        if self.cache_object_type == CacheObjectType.FLUID_PARTICLES:
            self._initialize_cache_object_fluid_particles(cache_object)

        if self.cache_object_type in types.WHITEWATER_CACHE_OBJECT_TYPES:
            self._initialize_cache_object_whitewater_particles(cache_object)

        self.cache_object = cache_object


    def initialize_cache_object_geometry_nodes(self):
        cache_object = self.get_cache_object()
        if cache_object is None:
            return

        if self.cache_object_type == CacheObjectType.SURFACE:
            self._initialize_cache_object_fluid_surface(cache_object)

        if self.cache_object_type == CacheObjectType.FLUID_PARTICLES:
            self._initialize_cache_object_fluid_particles(cache_object)

        if self.cache_object_type in types.WHITEWATER_CACHE_OBJECT_TYPES:
            self._initialize_cache_object_whitewater_particles(cache_object)

        self.cache_object = cache_object


    def delete_cache_object(self):
        if self.cache_object is None:
            return
        if not bpy.context.scene.flip_fluid.is_domain_in_active_scene():
            return
        cache_object = self.cache_object
        vcu.delete_object(cache_object)
        self.cache_object = None
        self.loaded_frame_data.reset()


    def reset_cache_object(self):
        if not cache_utils.is_domain_set() or not self._is_cache_object_initialized():
            return

        cache_object = self.get_cache_object()
        if cache_object.mode == 'EDIT':
            # Blender will error/crash if object is changed in edit mode
            warning = "FLIP Fluids Warning: Mesh object <" + cache_object.name + "> is in viewport 'Edit Mode'."
            warning += " Switch to viewport 'Object Mode' for full functionality and best experience."
            print(warning)
            return

        mesh_data = cache_object.data
        octane_mesh_type = self._get_octane_mesh_type(cache_object)

        vcu.swap_object_mesh_data_geometry(cache_object, [], [], 
                                           mesh_name=mesh_data,
                                           octane_mesh_type=octane_mesh_type)

        self._set_octane_settings(cache_object, octane_mesh_type)


    def _is_loaded_frame_up_to_date(self, frameno):
        ignore_properties = ["is_rendering", "frame"]

        is_setting_changed = False
        for prop_name in self.loaded_frame_data.__annotations__.keys():
            if prop_name in ignore_properties:
                continue
            if getattr(self, prop_name) != getattr(self.loaded_frame_data, prop_name):
                is_setting_changed = True

        is_render_status_changed = render.is_rendering() != self.loaded_frame_data.is_rendering
        is_loaded_frame_changed = self.current_loaded_frame != frameno
        is_up_to_date = not (is_setting_changed or is_render_status_changed or is_loaded_frame_changed)

        return is_up_to_date


    def _commit_loaded_frame_data(self, frameno):
        for prop_name in self.loaded_frame_data.__annotations__.keys():
            if not hasattr(self, prop_name):
                continue
            setattr(self.loaded_frame_data, prop_name, getattr(self, prop_name))

        self.loaded_frame_data.is_rendering = render.is_rendering()
        self.loaded_frame_data.frame = frameno


    def _is_load_frame_valid(self, frameno, force_load=False):
        global DISABLE_MESH_CACHE_LOAD
        if DISABLE_MESH_CACHE_LOAD:
            return False

        if not cache_utils.is_domain_set():
            return False

        current_frame = render.get_current_render_frame()
        if current_frame == self.current_loaded_frame and not force_load:
            return False

        if self._is_loaded_frame_up_to_date(frameno) and not force_load:
            return False

        return True


    def _update_id_attribute(self, frameno):
        if not self.enable_id_attribute:
            return

        id_data, ffp3_header_info = cache_utils.import_bakefile_attribute_data(
                mesh_cache=self,
                mesh_type=self.get_mesh_type(),
                mesh_name=self.mesh_prefix,
                attribute_name="id",
                data_type="UINT16",
                frameno=frameno
                )

        add_mesh_data_attribute(self.get_cache_object(), "flip_id", "INT", "POINT", id_data)

        if ffp3_header_info is not None:
            num_surface_particles = ffp3_header_info["num_surface_particles_to_read"]
            num_boundary_particles = ffp3_header_info["num_boundary_particles_to_read"]
            num_interior_particles = ffp3_header_info["num_interior_particles_to_read"]
            is_surface_data =  np.repeat([True,  False, False], [num_surface_particles, num_boundary_particles, num_interior_particles])
            is_boundary_data = np.repeat([False, True,  False], [num_surface_particles, num_boundary_particles, num_interior_particles])
            is_interior_data = np.repeat([False, False, True],  [num_surface_particles, num_boundary_particles, num_interior_particles])

            add_mesh_data_attribute(self.get_cache_object(), "flip_is_surface_particle",  "BOOLEAN", "POINT", is_surface_data)
            add_mesh_data_attribute(self.get_cache_object(), "flip_is_boundary_particle", "BOOLEAN", "POINT", is_boundary_data)
            add_mesh_data_attribute(self.get_cache_object(), "flip_is_interior_particle", "BOOLEAN", "POINT", is_interior_data)


    def _update_whitewater_proximity_attribute(self, frameno):
        if not self.enable_whitewater_proximity_attribute:
            return

        whitewater_proximity_data = cache_utils.import_bakefile_attribute_data_values(
                mesh_cache=self,
                mesh_type=self.get_mesh_type(),
                mesh_name=self.mesh_prefix,
                attribute_name="whitewaterproximity",
                data_type=DataType.FLOAT_VECTOR,
                frameno=frameno
                )

        foam_proximity_data = whitewater_proximity_data[0::3]
        bubble_proximity_data = whitewater_proximity_data[1::3]
        spray_proximity_data = whitewater_proximity_data[2::3]

        add_mesh_data_attribute(self.get_cache_object(), "flip_foam_proximity",   "FLOAT", "POINT", foam_proximity_data)
        add_mesh_data_attribute(self.get_cache_object(), "flip_bubble_proximity", "FLOAT", "POINT", bubble_proximity_data)
        add_mesh_data_attribute(self.get_cache_object(), "flip_spray_proximity",  "FLOAT", "POINT", spray_proximity_data)


    def _update_virtual_uvw_attribute(self):
        if not self.is_fluid_particles():
            # Currently only supported on fluid particles
            return

        if not self.enable_uid_attribute:
            # Feature depends on data from UID attribute
            return

        # Update virtual UVW cache
        dprops = cache_utils.get_domain_properties()
        uvw_attribute_items = dprops.particles.remap_uvw_attributes
        self.virtual_uvw_attribute.update_uvw_attributes(uvw_attribute_items, self.bounds)
        
        # Get current frame UID
        bl_particles = self.get_cache_object()
        uid_attribute = bl_particles.data.attributes.get("flip_uid")
        if uid_attribute is None or len(uid_attribute.data) == 0:
            # UID not available
            return

        uid_values = np.zeros(len(uid_attribute.data), dtype=np.intp)
        uid_attribute.data.foreach_get("value", uid_values)

        # Map UID -> UVW and set UVW attributes
        for item in uvw_attribute_items:
            lookup_table_func = self.virtual_uvw_attribute.get_frame_uid_to_uvw_lookup_table(item.frame)
            if lookup_table_func is None:
                # Bind frame not cached
                continue

            uvw_values = lookup_table_func(uid_values)
            add_mesh_data_attribute(bl_particles, item.attribute_name, "FLOAT_VECTOR", "POINT", uvw_values)


    # Cache values unrelated to geometry will be stored on the domain vertices
    # to minimize memory usage
    def _update_domain_data_storage_attributes(self, current_frame):
        domain_object = cache_utils.get_domain_object()
        if not domain_object:
            return

        # Store the max UID value from the cache on the domain vertices
        if self.enable_uid_attribute:
            bakefiles_directory = cache_utils.get_bakefiles_directory()
            if os.path.isdir(bakefiles_directory):
                bakefiles = os.listdir(bakefiles_directory)
                bakefiles = [name for name in bakefiles if name.startswith("finished")]

                max_frameno = -1
                max_frameno_filename = None
                for fname in bakefiles:
                    base = fname.split(".")[0]
                    try:
                        frame_number = int(base[-6:])
                        if frame_number > max_frameno:
                            max_frameno = frame_number
                            frame_str = cache_utils.frame_number_to_string(max_frameno)
                            max_frameno_filename = "fluidparticlesuidmax" + frame_str + ".txt"
                    except ValueError:
                        # In the case that there is a bakefile without a number
                        pass

                max_uid_value = None
                if max_frameno_filename:
                    filepath = os.path.join(bakefiles_directory, max_frameno_filename)
                    with open(filepath, "r") as max_uid_file:
                        file_text = max_uid_file.read()
                        max_uid_value = int(file_text)

                if max_uid_value:
                    attribute_name = "flip_uid_max"
                    mesh = domain_object.data
                    try:
                        mesh.attributes.remove(mesh.attributes.get(attribute_name))
                    except:
                        pass

                    attribute = mesh.attributes.new(attribute_name, "INT", "POINT")
                    attribute.data.foreach_set("value", [max_uid_value] * len(attribute.data))

        # Store per frame metadata values
        bakefiles_directory = cache_utils.get_bakefiles_directory()
        metadata_filename = "metadata" + cache_utils.frame_number_to_string(current_frame) + ".json"
        metadata_filepath = os.path.join(bakefiles_directory, metadata_filename)
        metadata_dict = {}
        if os.path.isfile(metadata_filepath):
            with open(metadata_filepath, "r") as metadata_file:
                metadata_dict = json.load(metadata_file)

        resolution = 1
        if 'resolution' in metadata_dict:
            resolution = metadata_dict['resolution']

        voxels = [1, 1, 1]
        if 'voxels' in metadata_dict:
            voxels = metadata_dict['voxels']

        dimensions = [1.0, 1.0, 1.0]
        if 'dimensions' in metadata_dict:
            dimensions = metadata_dict['dimensions']

        viewport_dimensions = [1.0, 1.0, 1.0]
        if 'viewport_dimensions' in metadata_dict:
            viewport_dimensions = metadata_dict['viewport_dimensions']

        dx = 1.0
        if 'dx' in metadata_dict:
            dx = metadata_dict['dx']

        viewport_dx = 1.0
        if 'viewport_dx' in metadata_dict:
            viewport_dx = metadata_dict['viewport_dx']

        time_scale_value = 1.0
        if 'time_scale' in metadata_dict:
            time_scale_value = metadata_dict['time_scale']

        world_scale_value = 1.0
        if 'world_scale' in metadata_dict:
            world_scale_value = metadata_dict['world_scale']

        attribute_list = [
                ("flip_resolution",          "INT",              resolution),
                ("flip_voxels",              "FLOAT_VECTOR",     voxels),
                ("flip_dimensions",          "FLOAT_VECTOR", dimensions),
                ("flip_viewport_dimensions", "FLOAT_VECTOR", viewport_dimensions),
                ("flip_dx",                  "FLOAT",        dx),
                ("flip_viewport_dx",         "FLOAT",        viewport_dx),
                ("flip_time_scale",          "FLOAT",        time_scale_value),
                ("flip_world_scale",         "FLOAT",        world_scale_value),
        ]

        for attribute_data in attribute_list:
            attribute_name = attribute_data[0]
            attribute_type = attribute_data[1]
            attribute_value = attribute_data[2]

            mesh = domain_object.data
            try:
                mesh.attributes.remove(mesh.attributes.get(attribute_name))
            except:
                pass

            attribute = mesh.attributes.new(attribute_name, attribute_type, "POINT")

            if attribute_type.endswith("VECTOR"):
                attribute.data.foreach_set("vector", attribute_value * len(attribute.data))
            else:
                attribute.data.foreach_set("value", [attribute_value] * len(attribute.data))


    def _update_attributes(self, frameno):
        # Update basic attributes
        constant_import_params = {
            "mesh_cache": self, 
            "mesh_type":  self.get_mesh_type(), 
            "mesh_name":  self.mesh_prefix,
            "frameno":    frameno
            }

        constant_attribute_params = {
            "bl_object":           self.get_cache_object(),
            "bl_attribute_domain": "POINT"
        }

        dt = DataType
        basic_attributes = [
            {"enabled": self.enable_velocity_attribute,  "import_params": {"attribute_name": "velocity",       "data_type": dt.FLOAT_VECTOR}, "attribute_params": {"bl_attribute_name": "flip_velocity",        "bl_attribute_type": "FLOAT_VECTOR"}},
            {"enabled": self.enable_speed_attribute,     "import_params": {"attribute_name": "speed",          "data_type": dt.FLOAT       }, "attribute_params": {"bl_attribute_name": "flip_speed",           "bl_attribute_type": "FLOAT"       }},
            {"enabled": self.enable_vorticity_attribute, "import_params": {"attribute_name": "vorticity",      "data_type": dt.FLOAT_VECTOR}, "attribute_params": {"bl_attribute_name": "flip_vorticity",       "bl_attribute_type": "FLOAT_VECTOR"}},
            {"enabled": self.enable_color_attribute,     "import_params": {"attribute_name": "color",          "data_type": dt.FLOAT_VECTOR}, "attribute_params": {"bl_attribute_name": "flip_color",           "bl_attribute_type": "FLOAT_VECTOR"}},
            {"enabled": self.enable_uvw_attribute,       "import_params": {"attribute_name": "uvw",            "data_type": dt.FLOAT_VECTOR}, "attribute_params": {"bl_attribute_name": "flip_uvw",             "bl_attribute_type": "FLOAT_VECTOR"}},
            {"enabled": self.enable_age_attribute,       "import_params": {"attribute_name": "age",            "data_type": dt.FLOAT       }, "attribute_params": {"bl_attribute_name": "flip_age",             "bl_attribute_type": "FLOAT"       }},
            {"enabled": self.enable_lifetime_attribute,  "import_params": {"attribute_name": "lifetime",       "data_type": dt.FLOAT       }, "attribute_params": {"bl_attribute_name": "flip_lifetime",        "bl_attribute_type": "FLOAT"       }},
            {"enabled": self.enable_viscosity_attribute, "import_params": {"attribute_name": "viscosity",      "data_type": dt.FLOAT       }, "attribute_params": {"bl_attribute_name": "flip_viscosity",       "bl_attribute_type": "FLOAT"       }},
            {"enabled": self.enable_density_attribute,   "import_params": {"attribute_name": "density",        "data_type": dt.FLOAT       }, "attribute_params": {"bl_attribute_name": "flip_density",         "bl_attribute_type": "FLOAT"       }},
            {"enabled": False,                           "import_params": {"attribute_name": "densityaverage", "data_type": dt.FLOAT       }, "attribute_params": {"bl_attribute_name": "flip_density_average", "bl_attribute_type": "FLOAT"       }},
            {"enabled": self.enable_source_id_attribute, "import_params": {"attribute_name": "sourceid",       "data_type": dt.INT         }, "attribute_params": {"bl_attribute_name": "flip_source_id",       "bl_attribute_type": "INT"         }},
            {"enabled": self.enable_uid_attribute,       "import_params": {"attribute_name": "uid",            "data_type": dt.INT         }, "attribute_params": {"bl_attribute_name": "flip_uid",             "bl_attribute_type": "INT"         }},
        ]

        for attribute in basic_attributes:
            if not attribute["enabled"]:
                continue

            try:
                params = attribute["import_params"] | constant_import_params
                attribute_values = cache_utils.import_bakefile_attribute_data_values(**params)

                params = attribute["attribute_params"] | constant_attribute_params | {"attribute_values": attribute_values}
                add_mesh_data_attribute(**params)
            except:
                traceback.print_exc()
                print("FLIP Fluids: An error has occurred while loading the frame. Please contact the developers with the above error message.")

        # Update custom attributes
        self._update_id_attribute(frameno)
        self._update_whitewater_proximity_attribute(frameno)

        # Update virtual attributes
        self._update_virtual_uvw_attribute()

        # Update domain attributes
        self._update_domain_data_storage_attributes(frameno)


    def _update_mesh_geometry(self, frameno):
        cache_object = self.get_cache_object()
        new_mesh_data_name = (self.mesh_display_name_prefix + 
                              cache_object.name + 
                              cache_utils.frame_number_to_string(frameno))
        octane_mesh_type = self._get_octane_mesh_type(cache_object)

        vertices, triangles = cache_utils.import_bakefile_mesh_data(
                mesh_cache=self,
                mesh_type=self.get_mesh_type(),
                mesh_name=self.mesh_prefix,
                attribute_name="",
                frameno=frameno
                )

        vcu.swap_object_mesh_data_geometry(cache_object, vertices, triangles, 
                                           mesh_name=new_mesh_data_name,
                                           octane_mesh_type=octane_mesh_type)


    def _update_bounds_data(self, frameno):
        filepath = cache_utils.get_geometry_data_filepath("bounds", "bbox", frameno)
        bounds_data = None
        if os.path.isfile(filepath):
            bounds_data = cache_utils.import_bbox(filepath)
        self.bounds.set(bounds_data)


    def load_frame(self, frameno, force_load=False, depsgraph=None):
        if not self._is_load_frame_valid(frameno, force_load):
            return

        cache_object = self.get_cache_object()
        if cache_object.mode == 'EDIT':
            # Blender will crash if object is reloaded in edit mode
            warning = "FLIP Fluids Warning: Mesh object <" + cache_object.name + "> is in viewport 'Edit Mode'."
            warning += " Switch to viewport 'Object Mode' for full functionality and best experience."
            print(warning)
            return

        if not self._is_cache_object_initialized():
            self.initialize_cache_object()

        self._update_bounds_data(frameno)
        self._update_mesh_geometry(frameno)
        self._update_transforms()
        self._update_ff_geometry_nodes_modifier(cache_object)
        self._update_attributes(frameno)

        self.current_loaded_frame = render.get_current_render_frame()
        self._commit_loaded_frame_data(frameno)


    def _update_transforms(self):
        cache_object = self.get_cache_object()
        transvect = mathutils.Vector((self.bounds.x, self.bounds.y, self.bounds.z))
        transmat = mathutils.Matrix.Translation(-transvect)
        cache_object.data.transform(transmat)
        domain_object = cache_utils.get_domain_object()
        dprops = cache_utils.get_domain_properties()

        domain_bounds = AABB.from_blender_object(domain_object)
        domain_pos = mathutils.Vector((domain_bounds.x, domain_bounds.y, domain_bounds.z))

        resolution = max(self.bounds.isize, self.bounds.jsize, self.bounds.ksize)
        isize, jsize, ksize, dx = dprops.simulation.get_viewport_grid_dimensions(resolution=resolution)

        scalex = (isize * dx) / self.bounds.width
        scaley = (jsize * dx) / self.bounds.height
        scalez = (ksize * dx) / self.bounds.depth
        scale = min(scalex, scaley, scalez)

        cache_object.matrix_world = mathutils.Matrix.Identity(4)
        cache_object.matrix_parent_inverse = domain_object.matrix_world.inverted()

        if len(cache_object.data.vertices) > 0:
            # Changing the scale of an object with no geometry (such as out of frame range)
            # seems to cause incorrect motion blur render
            cache_object.scale = (scale, scale, scale)

        cache_object.location = domain_pos


    def _is_octane_available(self):
        return hasattr(bpy.context.scene, 'octane')


    def get_cache_object(self):
        if not bpy.context.scene.flip_fluid.is_domain_in_active_scene():
            return None
        if self.cache_object is None:
            return None
            
        object_collection = bpy.context.scene.collection.all_objects
        if object_collection.get(self.cache_object.name) is None:
            self.delete_cache_object()
        return self.cache_object


    def _initialize_cache_object_octane(self, cache_object):
        if not self._is_octane_available():
            return

        GLOBAL = 'Global'
        SCATTER = 'Scatter'
        MOVABLE_PROXY = 'Movable proxy'
        RESHAPEABLE_PROXY = 'Reshapable proxy'

        if self.mesh_file_extension == 'bobj':
            cache_object.octane.object_mesh_type = RESHAPEABLE_PROXY
        elif self.mesh_file_extension == 'wwp':
            cache_object.octane.object_mesh_type = SCATTER


    def _is_cache_object_initialized(self):
        if self.cache_object is None:
                return False

        object_collection = bpy.context.scene.collection.all_objects
        if object_collection.get(self.cache_object.name) is None:
            self.delete_cache_object()
            return False
        return True


    def _get_octane_mesh_type(self, obj):
        if self._is_octane_available():
            return obj.octane.object_mesh_type
        return None


    def _set_octane_settings(self, obj, mesh_type):
        if self._is_octane_available() and mesh_type is not None:
            obj.octane.object_mesh_type = mesh_type


class FlipFluidGLPointCache(bpy.types.PropertyGroup):
    mesh_prefix: StringProperty(default="")
    mesh_file_extension: StringProperty(default="")
    current_loaded_frame: IntProperty(default=-1)
    uid: IntProperty(default=-1)
    is_enabled: BoolProperty(default=False)


    def enable(self):
        global GL_POINT_CACHE_DATA
        if self.is_enabled:
            return

        self.uid = 0
        for i in range(1024):
            if i not in GL_POINT_CACHE_DATA:
                self.uid = i
                GL_POINT_CACHE_DATA[i] = None
                break
        self.is_enabled = True


    def disable(self):
        global GL_POINT_CACHE_DATA
        if self.uid in GL_POINT_CACHE_DATA:
            del GL_POINT_CACHE_DATA[self.uid]
            self.uid = -1
        self.is_enabled = False


    def reset_cache(self):
        global GL_POINT_CACHE_DATA
        if self.uid != -1 and self.uid in GL_POINT_CACHE_DATA:
            del GL_POINT_CACHE_DATA[self.uid]
        draw_particles_operators.update_debug_particle_geometry(bpy.context)


    def get_point_cache_data(self):
        global GL_POINT_CACHE_DATA
        if self.uid in GL_POINT_CACHE_DATA:
            return GL_POINT_CACHE_DATA[self.uid]
        return None


    def load_frame(self, frameno, force_load = False):
        global GL_POINT_CACHE_DATA

        if not cache_utils.is_domain_set() or not self.is_enabled:
            return

        current_frame = render.get_current_render_frame()
        if current_frame == self.current_loaded_frame and not force_load:
            return

        particles, binstarts, binspeeds = self._import_frame_mesh(frameno)
        if len(particles) == 0:
            self.reset_cache()

        d = {
            'particles': particles,
            'binstarts': binstarts,
            'binspeeds': binspeeds
        }
        GL_POINT_CACHE_DATA[self.uid] = d

        self.current_loaded_frame = current_frame
        draw_particles_operators.update_debug_particle_geometry(bpy.context)


    def _import_frame_mesh(self, frameno):
        if not cache_utils.is_domain_set():
            return [], [], []
        filepath = cache_utils.get_geometry_data_filepath(self.mesh_prefix, self.mesh_file_extension, frameno)
        return cache_utils.import_fpd(filepath)


class FlipFluidGLForceFieldCache(bpy.types.PropertyGroup):
    mesh_prefix: StringProperty(default="")
    mesh_file_extension: StringProperty(default="")
    current_loaded_frame: IntProperty(default=-1)
    uid: IntProperty(default=-1)
    is_enabled: BoolProperty(default=False)


    def enable(self):
        global GL_FORCE_FIELD_CACHE_DATA
        if self.is_enabled:
            return

        self.uid = 0
        for i in range(1024):
            if i not in GL_FORCE_FIELD_CACHE_DATA:
                self.uid = i
                GL_FORCE_FIELD_CACHE_DATA[i] = None
                break
        self.is_enabled = True


    def disable(self):
        global GL_FORCE_FIELD_CACHE_DATA
        if self.uid in GL_FORCE_FIELD_CACHE_DATA:
            del GL_FORCE_FIELD_CACHE_DATA[self.uid]
            self.uid = -1
        self.is_enabled = False


    def reset_cache(self):
        global GL_FORCE_FIELD_CACHE_DATA
        if self.uid != -1 and self.uid in GL_FORCE_FIELD_CACHE_DATA:
            del GL_FORCE_FIELD_CACHE_DATA[self.uid]
        draw_force_field_operators.update_debug_force_field_geometry(bpy.context)


    def get_force_field_data(self):
        global GL_FORCE_FIELD_CACHE_DATA
        if self.uid in GL_FORCE_FIELD_CACHE_DATA:
            return GL_FORCE_FIELD_CACHE_DATA[self.uid]
        return None


    def load_frame(self, frameno, force_load = False):
        global GL_FORCE_FIELD_CACHE_DATA

        if not cache_utils.is_domain_set() or not self.is_enabled:
            return

        current_frame = render.get_current_render_frame()
        if current_frame == self.current_loaded_frame and not force_load:
            return

        vertices = self._import_frame_mesh(frameno)
        d = {
            'vertices': vertices
        }
        GL_FORCE_FIELD_CACHE_DATA[self.uid] = d

        self.current_loaded_frame = current_frame

        draw_force_field_operators.update_debug_force_field_geometry(bpy.context)


    def _import_frame_mesh(self, frameno):
        if not cache_utils.is_domain_set():
            return None
        filepath = cache_utils.get_geometry_data_filepath(self.mesh_prefix, self.mesh_file_extension, frameno)
        return cache_utils.import_ffd(filepath)


class FlipFluidCache(bpy.types.PropertyGroup):
    surface: PointerProperty(type=FlipFluidMeshCache)
    particles: PointerProperty(type=FlipFluidMeshCache)
    foam: PointerProperty(type=FlipFluidMeshCache)
    bubble: PointerProperty(type=FlipFluidMeshCache)
    spray: PointerProperty(type=FlipFluidMeshCache)
    dust: PointerProperty(type=FlipFluidMeshCache)
    gl_particles: PointerProperty(type=FlipFluidGLPointCache)
    gl_force_field: PointerProperty(type=FlipFluidGLForceFieldCache)
    obstacle: PointerProperty(type=FlipFluidMeshCache)


    def load_post(self):
        self.surface.load_post()
        self.obstacle.load_post()
        self.particles.load_post()
        self.foam.load_post()
        self.bubble.load_post()
        self.spray.load_post()
        self.dust.load_post()


    def cache_update_callback(self):
        self.surface.cache_update_callback()
        self.obstacle.cache_update_callback()
        self.particles.cache_update_callback()
        self.foam.cache_update_callback()
        self.bubble.cache_update_callback()
        self.spray.cache_update_callback()
        self.dust.cache_update_callback()


    def initialize_cache_settings(self):
        self.surface.mesh_prefix = ""
        self.surface.mesh_file_extension = "bobj"
        self.surface.cache_object_default_name = "fluid_surface"
        self.surface.cache_object_type = CacheObjectType.SURFACE

        self.particles.mesh_prefix = "fluidparticles"
        self.particles.mesh_file_extension = "ffp3"
        self.particles.cache_object_default_name = "fluid_particles"
        self.particles.cache_object_type = CacheObjectType.FLUID_PARTICLES

        self.foam.mesh_prefix = "foam"
        self.foam.mesh_file_extension = "wwp"
        self.foam.cache_object_default_name = "whitewater_foam"
        self.foam.cache_object_type = CacheObjectType.WHITEWATER_FOAM

        self.bubble.mesh_prefix = "bubble"
        self.bubble.mesh_file_extension = "wwp"
        self.bubble.cache_object_default_name = "whitewater_bubble"
        self.bubble.cache_object_type = CacheObjectType.WHITEWATER_BUBBLE

        self.spray.mesh_prefix = "spray"
        self.spray.mesh_file_extension = "wwp"
        self.spray.cache_object_default_name = "whitewater_spray"
        self.spray.cache_object_type = CacheObjectType.WHITEWATER_SPRAY

        self.dust.mesh_prefix = "dust"
        self.dust.mesh_file_extension = "wwp"
        self.dust.cache_object_default_name = "whitewater_dust"
        self.dust.cache_object_type = CacheObjectType.WHITEWATER_DUST

        self.gl_particles.mesh_prefix = "particles"
        self.gl_particles.mesh_file_extension = "fpd"

        self.gl_force_field.mesh_prefix = "forcefield"
        self.gl_force_field.mesh_file_extension = "ffd"

        self.obstacle.mesh_prefix = "obstacle"
        self.obstacle.mesh_file_extension = "bobj"
        self.obstacle.cache_object_default_name = "debug_obstacle"
        self.obstacle.cache_object_type = CacheObjectType.OBSTACLE_DEBUG


    def is_simulation_mesh_load_enabled(self, mesh_name):
        return render.is_simulation_mesh_load_enabled(mesh_name)


    def enable_simulation_mesh_load(self, mesh_name):
        return render.enable_simulation_mesh_load(mesh_name)


    def disable_simulation_mesh_load(self, mesh_name):
        return render.disable_simulation_mesh_load(mesh_name)


    def initialize_cache_objects(self, enabled_mesh_cache_objects=None):
        self.initialize_cache_settings()
        if not cache_utils.is_domain_set():
            return
        if not bpy.context.scene.flip_fluid.is_domain_in_active_scene():
            return

        enable_fluid_surface = True
        enable_fluid_particles = True
        enable_whitewater_particles = True
        enable_debug_obstacle = True
        if enabled_mesh_cache_objects is not None:
            enable_fluid_surface = enabled_mesh_cache_objects.fluid_surface
            enable_fluid_particles = enabled_mesh_cache_objects.fluid_particles
            enable_whitewater_particles = enabled_mesh_cache_objects.whitewater_particles
            enable_debug_obstacle = enabled_mesh_cache_objects.debug_obstacle

        dprops = cache_utils.get_domain_properties()
        if enable_fluid_surface and dprops.surface.enable_surface_mesh_generation:
            self.surface.initialize_cache_object()

        if enable_fluid_particles and dprops.particles.enable_fluid_particle_output:
            self.particles.initialize_cache_object()

        if enable_whitewater_particles and dprops.whitewater.enable_whitewater_simulation:
            self.foam.initialize_cache_object()
            self.bubble.initialize_cache_object()
            self.spray.initialize_cache_object()
            self.dust.initialize_cache_object()

        if enable_debug_obstacle and dprops.debug.export_internal_obstacle_mesh:
            self.obstacle.initialize_cache_object()


    def initialize_cache_objects_geometry_nodes(self, enabled_mesh_cache_objects=None):
        self.initialize_cache_settings()
        if not cache_utils.is_domain_set():
            return
        if not bpy.context.scene.flip_fluid.is_domain_in_active_scene():
            return

        enable_fluid_surface = True
        enable_fluid_particles = True
        enable_whitewater_particles = True
        enable_debug_obstacle = True
        if enabled_mesh_cache_objects is not None:
            enable_fluid_surface = enabled_mesh_cache_objects.fluid_surface
            enable_fluid_particles = enabled_mesh_cache_objects.fluid_particles
            enable_whitewater_particles = enabled_mesh_cache_objects.whitewater_particles
            enable_debug_obstacle = enabled_mesh_cache_objects.debug_obstacle

        dprops = cache_utils.get_domain_properties()
        if enable_fluid_surface and dprops.surface.enable_surface_mesh_generation:
            self.surface.initialize_cache_object_geometry_nodes()

        if enable_fluid_particles and dprops.particles.enable_fluid_particle_output:
            self.particles.initialize_cache_object_geometry_nodes()

        if enable_whitewater_particles and dprops.whitewater.enable_whitewater_simulation:
            self.foam.initialize_cache_object_geometry_nodes()
            self.bubble.initialize_cache_object_geometry_nodes()
            self.spray.initialize_cache_object_geometry_nodes()
            self.dust.initialize_cache_object_geometry_nodes()

        if enable_debug_obstacle and dprops.debug.export_internal_obstacle_mesh:
            self.obstacle.initialize_cache_object_geometry_nodes()


    def delete_cache_objects(self):
        self.initialize_cache_settings()
        self.surface.delete_cache_object()
        self.particles.delete_cache_object()
        self.foam.delete_cache_object()
        self.bubble.delete_cache_object()
        self.spray.delete_cache_object()
        self.dust.delete_cache_object()
        self.obstacle.delete_cache_object()


    def delete_surface_cache_objects(self):
        self.initialize_cache_settings()
        self.surface.delete_cache_object()


    def delete_particle_cache_objects(self):
        self.initialize_cache_settings()
        self.particles.delete_cache_object()


    def delete_whitewater_cache_objects(self, whitewater_type='TYPE_ALL'):
        self.initialize_cache_settings()

        delete_all_types = False
        if whitewater_type == "TYPE_ALL":
            delete_all_types = True
            
        if whitewater_type == "TYPE_FOAM" or delete_all_types:
            self.foam.delete_cache_object()
        if whitewater_type == "TYPE_BUBBLE" or delete_all_types:
            self.bubble.delete_cache_object()
        if whitewater_type == "TYPE_SPRAY" or delete_all_types:
            self.spray.delete_cache_object()
        if whitewater_type == "TYPE_DUST" or delete_all_types:
            self.dust.delete_cache_object()


    def delete_obstacle_cache_object(self):
        self.obstacle.delete_cache_object()


    def reset_cache_objects(self):
        self.initialize_cache_settings()
        if not cache_utils.is_domain_set():
            return
        if not bpy.context.scene.flip_fluid.is_domain_in_active_scene():
            return

        self.surface.reset_cache_object()
        self.particles.reset_cache_object()
        self.foam.reset_cache_object()
        self.bubble.reset_cache_object()
        self.spray.reset_cache_object()
        self.dust.reset_cache_object()
        self.obstacle.reset_cache_object()
        self.gl_particles.reset_cache()
        self.gl_force_field.reset_cache()


    def is_cache_object(self, obj):
        cache_objects = [self.surface, self.particles, self.foam, self.bubble, self.spray, self.dust]
        for c in cache_objects:
            cache_object = c.get_cache_object()
            if cache_object and cache_object.name == obj.name:
                return True
        return False


    def get_mesh_cache_from_blender_object(self, obj):
        cache_objects = [self.surface, self.particles, self.foam, self.bubble, self.spray, self.dust]
        for c in cache_objects:
            cache_object = c.get_cache_object()
            if cache_object and cache_object.name == obj.name:
                return c
        return None


def register():
    bpy.utils.register_class(FLIPFluidMeshBounds)
    bpy.utils.register_class(FlipFluidLoadedMeshData)
    bpy.utils.register_class(FlipFluidMeshCache)
    bpy.utils.register_class(FlipFluidGLPointCache)
    bpy.utils.register_class(FlipFluidGLForceFieldCache)
    bpy.utils.register_class(FlipFluidCache)


def unregister():
    bpy.utils.unregister_class(FLIPFluidMeshBounds)
    bpy.utils.unregister_class(FlipFluidLoadedMeshData)
    bpy.utils.unregister_class(FlipFluidMeshCache)
    bpy.utils.unregister_class(FlipFluidGLPointCache)
    bpy.utils.unregister_class(FlipFluidGLForceFieldCache)
    bpy.utils.unregister_class(FlipFluidCache)

    global GL_POINT_CACHE_DATA
    GL_POINT_CACHE_DATA = {}

    global GL_FORCE_FIELD_CACHE_DATA
    GL_FORCE_FIELD_CACHE_DATA = {}
