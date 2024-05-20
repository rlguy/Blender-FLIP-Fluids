# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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

import bpy, os, struct, math, json, mathutils
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        StringProperty,
        PointerProperty
        )

from .flip_fluid_aabb import AABB
from .. import render
from ..operators import draw_particles_operators
from ..operators import draw_force_field_operators
from ..operators import helper_operators
from ..utils import version_compatibility_utils as vcu

DISABLE_MESH_CACHE_LOAD = False
GL_POINT_CACHE_DATA = {}
GL_FORCE_FIELD_CACHE_DATA = {}


class EnabledMeshCacheObjects:
    fluid_surface = False
    fluid_particles = False
    whitewater_particles = False
    debug_obstacle = False


class FLIPFluidMeshBounds(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    x =      FloatProperty(0.0);  exec(conv("x"))
    y =      FloatProperty(0.0);  exec(conv("y"))
    z =      FloatProperty(0.0);  exec(conv("z"))
    width =  FloatProperty(1.0);  exec(conv("width"))
    height = FloatProperty(1.0);  exec(conv("height"))
    depth =  FloatProperty(1.0);  exec(conv("depth"))
    dx =     FloatProperty(1.0);  exec(conv("dx"))
    isize =  IntProperty(0);      exec(conv("isize"))
    jsize =  IntProperty(0);      exec(conv("jsize"))
    ksize =  IntProperty(0);      exec(conv("ksize"))
    is_set = BoolProperty(False); exec(conv("is_set"))


    def set(self, bounds_dict):
        if bounds_dict is None:
            self.x, self.y, self.z = 0.0, 0.0, 0.0
            self.width, self.height, self.depth = 1.0, 1.0, 1.0
            self.dx = 1.0
            self.is_set = False
            return
        self.x, self.y, self.z = bounds_dict['x'], bounds_dict['y'], bounds_dict['z']
        self.width = bounds_dict['width']
        self.height = bounds_dict['height']
        self.depth = bounds_dict['depth']
        self.dx = bounds_dict['dx']
        self.isize = bounds_dict['isize']
        self.jsize = bounds_dict['jsize']
        self.ksize = bounds_dict['ksize']


    def is_set(self):
        return self.is_set


class FlipFluidLoadedMeshData(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    mesh_prefix =                            StringProperty(default="mesh_prefix"); exec(conv("mesh_prefix"))
    enable_motion_blur =                     BoolProperty(default=False);           exec(conv("enable_motion_blur"))
    motion_blur_scale =                      FloatProperty(default=-1.0);           exec(conv("motion_blur_scale"))
    enable_velocity_attribute =              BoolProperty(default=False);           exec(conv("enable_velocity_attribute"))
    enable_vorticity_attribute =             BoolProperty(default=False);           exec(conv("enable_vorticity_attribute"))
    enable_speed_attribute =                 BoolProperty(default=False);           exec(conv("enable_speed_attribute"))
    enable_age_attribute =                   BoolProperty(default=False);           exec(conv("enable_age_attribute"))
    enable_color_attribute =                 BoolProperty(default=False);           exec(conv("enable_color_attribute"))
    enable_source_id_attribute =             BoolProperty(default=False);           exec(conv("enable_source_id_attribute"))
    enable_viscosity_attribute =             BoolProperty(default=False);           exec(conv("enable_viscosity_attribute"))
    enable_id_attribute =                    BoolProperty(default=False);           exec(conv("enable_id_attribute"))
    enable_lifetime_attribute =              BoolProperty(default=False);           exec(conv("enable_lifetime_attribute"))
    enable_whitewater_proximity_attribute =  BoolProperty(default=False);           exec(conv("enable_whitewater_proximity_attribute"))
    wwp_import_percentage =                  IntProperty(default=0);                exec(conv("wwp_import_percentage"))
    ffp3_surface_import_percentage =         FloatProperty(default=0);              exec(conv("ffp3_surface_import_percentage"))
    ffp3_boundary_import_percentage =        FloatProperty(default=0);              exec(conv("ffp3_boundary_import_percentage"))
    ffp3_interior_import_percentage =        FloatProperty(default=0);              exec(conv("ffp3_interior_import_percentage"))
    is_rendering =                           BoolProperty(default=True);            exec(conv("is_rendering"))
    frame =                                  IntProperty(default=-1);               exec(conv("frame"))


    def reset(self):
        self.property_unset("mesh_prefix")
        self.property_unset("enable_motion_blur")
        self.property_unset("motion_blur_scale")
        self.property_unset("enable_velocity_attribute")
        self.property_unset("enable_vorticity_attribute")
        self.property_unset("enable_speed_attribute")
        self.property_unset("enable_age_attribute")
        self.property_unset("enable_color_attribute")
        self.property_unset("enable_source_id_attribute")
        self.property_unset("enable_viscosity_attribute")
        self.property_unset("enable_id_attribute")
        self.property_unset("enable_lifetime_attribute")
        self.property_unset("enable_whitewater_proximity_attribute")
        self.property_unset("wwp_import_percentage")
        self.property_unset("ffp3_surface_import_percentage")
        self.property_unset("ffp3_boundary_import_percentage")
        self.property_unset("ffp3_interior_import_percentage")
        self.property_unset("is_rendering")
        self.property_unset("frame")


class FlipFluidMeshCache(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    # Mesh properties
    mesh_prefix =                            StringProperty(default="");                       exec(conv("mesh_prefix"))
    mesh_display_name_prefix =               StringProperty(default="");                       exec(conv("mesh_display_name_prefix"))
    mesh_file_extension =                    StringProperty(default="");                       exec(conv("mesh_file_extension"))
    enable_motion_blur =                     BoolProperty(default=False);                      exec(conv("enable_motion_blur"))
    motion_blur_scale =                      FloatProperty(default=1.0);                       exec(conv("motion_blur_scale"))
    enable_velocity_attribute =              BoolProperty(default=False);                      exec(conv("enable_velocity_attribute"))
    enable_vorticity_attribute =             BoolProperty(default=False);                      exec(conv("enable_vorticity_attribute"))
    enable_speed_attribute =                 BoolProperty(default=False);                      exec(conv("enable_speed_attribute"))
    enable_age_attribute =                   BoolProperty(default=False);                      exec(conv("enable_age_attribute"))
    enable_color_attribute =                 BoolProperty(default=False);                      exec(conv("enable_color_attribute"))
    enable_source_id_attribute =             BoolProperty(default=False);                      exec(conv("enable_source_id_attribute"))
    enable_viscosity_attribute =             BoolProperty(default=False);                      exec(conv("enable_viscosity_attribute"))
    enable_id_attribute =                    BoolProperty(default=False);                      exec(conv("enable_id_attribute"))
    enable_lifetime_attribute =              BoolProperty(default=False);                      exec(conv("enable_lifetime_attribute"))
    enable_whitewater_proximity_attribute =  BoolProperty(default=False);                      exec(conv("enable_whitewater_proximity_attribute"))
    cache_object_default_name =              StringProperty(default="");                       exec(conv("cache_object_default_name"))
    cache_object =                           PointerProperty(type=bpy.types.Object);           exec(conv("cache_object"))
    is_mesh_shading_smooth =                 BoolProperty(default=True);                       exec(conv("is_mesh_shading_smooth"))
    current_loaded_frame =                   IntProperty(default=-1);                          exec(conv("current_loaded_frame"))
    import_function_name =                   StringProperty(default="import_empty");           exec(conv("import_function_name"))
    wwp_import_percentage =                  IntProperty(default=100);                         exec(conv("wwp_import_percentage"))
    ffp3_surface_import_percentage =         FloatProperty(default=0);                         exec(conv("ffp3_surface_import_percentage"))
    ffp3_boundary_import_percentage =        FloatProperty(default=0);                         exec(conv("ffp3_boundary_import_percentage"))
    ffp3_interior_import_percentage =        FloatProperty(default=0);                         exec(conv("ffp3_interior_import_percentage"))
    cache_object_type =                      StringProperty(default="CACHE_OBJECT_TYPE_NONE"); exec(conv("cache_object_type"))

    # Loaded data properties
    loaded_frame_data = PointerProperty(type=FlipFluidLoadedMeshData); exec(conv("loaded_frame_data"))
    bounds =            PointerProperty(type=FLIPFluidMeshBounds);     exec(conv("bounds"))


    def _initialize_cache_object_fluid_particles(self, bl_cache_object):
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blend_resource_filename = "geometry_nodes_library.blend"
        resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", blend_resource_filename)
        gn_modifier = helper_operators.add_geometry_node_modifier(bl_cache_object, resource_filepath, "FF_MotionBlurFluidParticles")

        # Depending on FLIP Fluids version, the GN set up may not
        # have these inputs. Available in FLIP Fluids 1.7.2 or later.
        try:
            # Input flip_velocity
            gn_modifier["Input_2_use_attribute"] = 1
            gn_modifier["Input_2_attribute_name"] = 'flip_velocity'
        except:
            pass

        try:
            # Output velocity
            gn_modifier["Output_3_attribute_name"] = 'velocity'
        except:
            pass

        try:
            # Material
            gn_modifier["Input_5"] = bl_cache_object.active_material
        except:
            pass

        try:
            # Enable Motion Blur
            gn_modifier["Input_8"] = False
        except:
            pass

        try:
            # Enable Point Cloud
            gn_modifier["Input_9"] = True
        except:
            pass


    def _initialize_cache_object_whitewater_particles(self, bl_cache_object):
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        blend_resource_filename = "geometry_nodes_library.blend"
        resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", blend_resource_filename)

        if   self.cache_object_type == 'CACHE_OBJECT_TYPE_FOAM':
            resource_name = "FF_MotionBlurWhitewaterFoam"
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_BUBBLE':
            resource_name = "FF_MotionBlurWhitewaterBubble"
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_SPRAY':
            resource_name = "FF_MotionBlurWhitewaterSpray"
        elif self.cache_object_type == 'CACHE_OBJECT_TYPE_DUST':
            resource_name = "FF_MotionBlurWhitewaterDust"

        gn_modifier = helper_operators.add_geometry_node_modifier(bl_cache_object, resource_filepath, resource_name)

        # Depending on FLIP Fluids version, the GN set up may not
        # have these inputs. Available in FLIP Fluids 1.7.2 or later.
        try:
            # Input flip_velocity
            gn_modifier["Input_2_use_attribute"] = 1
            gn_modifier["Input_2_attribute_name"] = 'flip_velocity'
        except:
            pass

        try:
            # Output velocity
            gn_modifier["Output_3_attribute_name"] = 'velocity'
        except:
            pass

        try:
            # Material
            gn_modifier["Input_5"] = bl_cache_object.active_material
        except:
            pass

        try:
            # Enable Motion Blur
            gn_modifier["Input_8"] = False
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


    def initialize_cache_object(self):
        if not self._is_domain_set() or self._is_cache_object_initialized():
            return

        domain_object = self._get_domain_object()
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

        smooth_mod = cache_object.modifiers.new("Smooth", "SMOOTH")
        smooth_mod.iterations = 0

        # Motion blur not supported. Leaving motion blur enabled can cause
        # slow render in versions of Blender 2.91+. Workaround is to
        # automatically disable motion blur on the object.
        try:
            # Cycles may not be enabled in the user's preferences
            cache_object.cycles.use_motion_blur = False
        except:
            pass

        self._initialize_cache_object_octane(cache_object)

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES' and vcu.is_blender_31():
            self._initialize_cache_object_fluid_particles(cache_object)

        if (self.cache_object_type == 'CACHE_OBJECT_TYPE_FOAM' or 
                self.cache_object_type == 'CACHE_OBJECT_TYPE_BUBBLE' or 
                self.cache_object_type == 'CACHE_OBJECT_TYPE_SPRAY' or 
                self.cache_object_type == 'CACHE_OBJECT_TYPE_DUST') and vcu.is_blender_31():
            self._initialize_cache_object_whitewater_particles(cache_object)

        self.cache_object = cache_object


    def initialize_cache_object_geometry_nodes(self):
        cache_object = self.get_cache_object()
        if cache_object is None:
            return

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES' and vcu.is_blender_31():
            self._initialize_cache_object_fluid_particles(cache_object)

        if (self.cache_object_type == 'CACHE_OBJECT_TYPE_FOAM' or 
                self.cache_object_type == 'CACHE_OBJECT_TYPE_BUBBLE' or 
                self.cache_object_type == 'CACHE_OBJECT_TYPE_SPRAY' or 
                self.cache_object_type == 'CACHE_OBJECT_TYPE_DUST') and vcu.is_blender_31():
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
        if not self._is_domain_set() or not self._is_cache_object_initialized():
            return

        cache_object = self.get_cache_object()
        if cache_object.mode == 'EDIT':
            # Blender will error/crash if object is changed in edit mode
            warning = "FLIP Fluids Warning: Mesh object <" + cache_object.name + "> is in viewport 'Edit Mode'."
            warning += " Switch to viewport 'Object Mode' for full functionality and best experience."
            print(warning)
            return

        if vcu.is_blender_281():
            mesh_data = cache_object.data

            is_smooth = self._is_mesh_smooth(mesh_data)
            octane_mesh_type = self._get_octane_mesh_type(cache_object)

            vcu.swap_object_mesh_data_geometry(cache_object, [], [], 
                                               mesh_data,
                                               is_smooth,
                                               octane_mesh_type)

            self._set_mesh_smoothness(mesh_data, is_smooth)
            self._set_octane_settings(cache_object, octane_mesh_type)

        else:
            old_mesh_data = cache_object.data

            mesh_data_name = self.cache_object_default_name + "_mesh"
            new_mesh_data = bpy.data.meshes.new(mesh_data_name)
            new_mesh_data.from_pydata([], [], [])
            
            self._transfer_mesh_materials(old_mesh_data, new_mesh_data)
            self._transfer_mesh_smoothness(old_mesh_data, new_mesh_data)
            self._transfer_octane_settings(cache_object, cache_object)

            cache_object.data = new_mesh_data

            vcu.delete_mesh_data(old_mesh_data)


    def _is_loaded_frame_up_to_date(self, frameno):
        d = self.loaded_frame_data
        return not (self.mesh_prefix                            != d.mesh_prefix or 
                    self.enable_motion_blur                     != d.enable_motion_blur or
                    self.motion_blur_scale                      != d.motion_blur_scale or
                    self.enable_velocity_attribute              != d.enable_velocity_attribute or
                    self.enable_vorticity_attribute             != d.enable_vorticity_attribute or
                    self.enable_speed_attribute                 != d.enable_speed_attribute or
                    self.enable_age_attribute                   != d.enable_age_attribute or
                    self.enable_color_attribute                 != d.enable_color_attribute or
                    self.enable_source_id_attribute             != d.enable_source_id_attribute or
                    self.enable_viscosity_attribute             != d.enable_viscosity_attribute or
                    self.enable_id_attribute                    != d.enable_id_attribute or
                    self.enable_lifetime_attribute              != d.enable_lifetime_attribute or
                    self.enable_whitewater_proximity_attribute  != d.enable_whitewater_proximity_attribute or
                    self.wwp_import_percentage                  != d.wwp_import_percentage or
                    self.ffp3_surface_import_percentage         != d.ffp3_surface_import_percentage or
                    self.ffp3_boundary_import_percentage        != d.ffp3_boundary_import_percentage or
                    self.ffp3_interior_import_percentage        != d.ffp3_interior_import_percentage or
                    render.is_rendering()                       != d.is_rendering or
                    self.current_loaded_frame                   != frameno)


    def _commit_loaded_frame_data(self, frameno):
        d = self.loaded_frame_data
        d.mesh_prefix                            = self.mesh_prefix
        d.enable_motion_blur                     = self.enable_motion_blur
        d.motion_blur_scale                      = self.motion_blur_scale
        d.enable_velocity_attribute              = self.enable_velocity_attribute
        d.enable_vorticity_attribute             = self.enable_vorticity_attribute
        d.enable_speed_attribute                 = self.enable_speed_attribute
        d.enable_age_attribute                   = self.enable_age_attribute
        d.enable_color_attribute                 = self.enable_color_attribute
        d.enable_source_id_attribute             = self.enable_source_id_attribute
        d.enable_viscosity_attribute             = self.enable_viscosity_attribute
        d.enable_id_attribute                    = self.enable_id_attribute
        d.enable_lifetime_attribute              = self.enable_lifetime_attribute
        d.enable_whitewater_proximity_attribute  = self.enable_whitewater_proximity_attribute
        d.wwp_import_percentage                  = self.wwp_import_percentage
        d.ffp3_surface_import_percentage         = self.ffp3_surface_import_percentage
        d.ffp3_boundary_import_percentage        = self.ffp3_boundary_import_percentage
        d.ffp3_interior_import_percentage        = self.ffp3_interior_import_percentage
        d.is_rendering                           = render.is_rendering()
        d.frame                                  = frameno


    def _is_load_frame_valid(self, frameno, force_load=False):
        global DISABLE_MESH_CACHE_LOAD
        if DISABLE_MESH_CACHE_LOAD:
            return False

        if not self._is_domain_set():
            return False

        current_frame = render.get_current_render_frame()
        if current_frame == self.current_loaded_frame and not force_load:
            return False

        if self._is_loaded_frame_up_to_date(frameno) and not force_load:
            return False

        return True


    def _update_motion_blur(self, frameno):
        is_motion_blur_support = False
        if not self.enable_motion_blur or not is_motion_blur_support:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        current_frame = render.get_current_render_frame()

        if vcu.is_blender_281() and cache_object.data.shape_keys is not None:
            for idx,key in enumerate(cache_object.data.shape_keys.key_blocks):
                cache_object.shape_key_remove(key=key)

        blur_data = self._import_motion_blur_data(frameno)
        if len(blur_data) == len(cache_object.data.vertices):
            cache_object.shape_key_add(name="basis" + frame_string, from_mix=False)
            shape_key = cache_object.shape_key_add(name="blur1" + frame_string, from_mix=False)
            for i, v in enumerate(shape_key.data):
                v.co[0] += blur_data[i][0] * self.motion_blur_scale
                v.co[1] += blur_data[i][1] * self.motion_blur_scale
                v.co[2] += blur_data[i][2] * self.motion_blur_scale
            shape_key.keyframe_insert(data_path='value', frame=current_frame)
            shape_key.value = 1
            shape_key.keyframe_insert(data_path='value', frame=current_frame + 1)
            shape_key.value = 0

            shape_key = cache_object.shape_key_add(name="blur2" + frame_string, from_mix=False)
            for i, v in enumerate(shape_key.data):
                v.co[0] -= blur_data[i][0] * self.motion_blur_scale
                v.co[1] -= blur_data[i][1] * self.motion_blur_scale
                v.co[2] -= blur_data[i][2] * self.motion_blur_scale
            shape_key.keyframe_insert(data_path='value', frame=current_frame)
            shape_key.value = 1
            shape_key.keyframe_insert(data_path='value', frame=current_frame - 1)
            shape_key.value = 0


    def _update_velocity_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_velocity_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        velocity_data, _ = self._import_velocity_attribute_data(frameno)

        if not velocity_data:
            return

        attribute_name = "flip_velocity"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT_VECTOR", "POINT")
        attribute.data.foreach_set("vector", velocity_data)


    def _update_speed_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_speed_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        speed_data, _ = self._import_speed_attribute_data(frameno)

        if not speed_data:
            return

        attribute_name = "flip_speed"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
        attribute.data.foreach_set("value", speed_data)


    def _update_vorticity_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_vorticity_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        vorticity_data, _ = self._import_vorticity_attribute_data(frameno)

        if not vorticity_data:
            return

        attribute_name = "flip_vorticity"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT_VECTOR", "POINT")
        attribute.data.foreach_set("vector", vorticity_data)


    def _update_age_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_age_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        age_data, _ = self._import_age_attribute_data(frameno)

        if not age_data:
            return

        attribute_name = "flip_age"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
        attribute.data.foreach_set("value", age_data)


    def _update_color_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_color_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        color_data, _ = self._import_color_attribute_data(frameno)

        if not color_data:
            return

        attribute_name = "flip_color"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT_VECTOR", "POINT")
        attribute.data.foreach_set("vector", color_data)


    def _update_source_id_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_source_id_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        source_id_data, _ = self._import_source_id_attribute_data(frameno)

        if not source_id_data:
            return

        attribute_name = "flip_source_id"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "INT", "POINT")
        attribute.data.foreach_set("value", source_id_data)


    def _update_viscosity_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_viscosity_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        viscosity_data, _ = self._import_viscosity_attribute_data(frameno)

        if not viscosity_data:
            return

        attribute_name = "flip_viscosity"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
        attribute.data.foreach_set("value", viscosity_data)


    def _update_id_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_id_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        id_data, ffp3_header_info = self._import_id_attribute_data(frameno)

        if not id_data:
            return

        attribute_name = "flip_id"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "INT", "POINT")
        attribute.data.foreach_set("value", id_data)

        if ffp3_header_info is not None:
            num_surface_particles = ffp3_header_info["num_surface_particles_to_read"]
            num_boundary_particles = ffp3_header_info["num_boundary_particles_to_read"]
            num_interior_particles = ffp3_header_info["num_interior_particles_to_read"]
            is_surface_data = [True] * num_surface_particles + [False] * num_boundary_particles + [False] * num_interior_particles
            is_boundary_data = [False] * num_surface_particles + [True] * num_boundary_particles + [False] * num_interior_particles
            is_interior_data = [False] * num_surface_particles + [False] * num_boundary_particles + [True] * num_interior_particles

            attribute_name = "flip_is_surface_particle"
            try:
                mesh.attributes.remove(mesh.attributes.get(attribute_name))
            except:
                pass
            attribute = mesh.attributes.new(attribute_name, "BOOLEAN", "POINT")
            attribute.data.foreach_set("value", is_surface_data)

            attribute_name = "flip_is_boundary_particle"
            try:
                mesh.attributes.remove(mesh.attributes.get(attribute_name))
            except:
                pass
            attribute = mesh.attributes.new(attribute_name, "BOOLEAN", "POINT")
            attribute.data.foreach_set("value", is_boundary_data)

            attribute_name = "flip_is_interior_particle"
            try:
                mesh.attributes.remove(mesh.attributes.get(attribute_name))
            except:
                pass
            attribute = mesh.attributes.new(attribute_name, "BOOLEAN", "POINT")
            attribute.data.foreach_set("value", is_interior_data)


    def _update_lifetime_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_lifetime_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        lifetime_data, _ = self._import_lifetime_attribute_data(frameno)

        if not lifetime_data:
            return

        attribute_name = "flip_lifetime"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
        attribute.data.foreach_set("value", lifetime_data)


    def _update_whitewater_proximity_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_whitewater_proximity_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        whitewater_proximity_data, _ = self._import_whitewater_proximity_attribute_data(frameno)
        foam_proximity_data = whitewater_proximity_data[0::3]
        bubble_proximity_data = whitewater_proximity_data[1::3]
        spray_proximity_data = whitewater_proximity_data[2::3]
        
        if not whitewater_proximity_data:
            return

        mesh = cache_object.data
        foam_attribute_name = "flip_foam_proximity"
        bubble_attribute_name = "flip_bubble_proximity"
        spray_attribute_name = "flip_spray_proximity"

        try:
            mesh.attributes.remove(mesh.attributes.get(foam_attribute_name))
        except:
            pass
        foam_attribute = mesh.attributes.new(foam_attribute_name, "FLOAT", "POINT")
        foam_attribute.data.foreach_set("value", foam_proximity_data)

        try:
            mesh.attributes.remove(mesh.attributes.get(bubble_attribute_name))
        except:
            pass
        bubble_attribute = mesh.attributes.new(bubble_attribute_name, "FLOAT", "POINT")
        bubble_attribute.data.foreach_set("value", bubble_proximity_data)

        try:
            mesh.attributes.remove(mesh.attributes.get(spray_attribute_name))
        except:
            pass
        spray_attribute = mesh.attributes.new(spray_attribute_name, "FLOAT", "POINT")
        spray_attribute.data.foreach_set("value", spray_proximity_data)


    def load_frame(self, frameno, force_load=False, depsgraph=None):
        if not self._is_load_frame_valid(frameno, force_load):
            return

        if not self._is_cache_object_initialized():
            self.initialize_cache_object()

        cache_object = self.get_cache_object()
        if cache_object.mode == 'EDIT':
            # Blender will crash if object is reloaded in edit mode
            warning = "FLIP Fluids Warning: Mesh object <" + cache_object.name + "> is in viewport 'Edit Mode'."
            warning += " Switch to viewport 'Object Mode' for full functionality and best experience."
            print(warning)
            return

        self._initialize_bounds_data(frameno)

        frame_string = self._frame_number_to_string(frameno)
        new_mesh_data_name = (self.mesh_display_name_prefix + 
                              cache_object.name + 
                              frame_string)
        is_smooth = self._is_mesh_smooth(cache_object.data)
        octane_mesh_type = self._get_octane_mesh_type(cache_object)

        vertices, triangles = self._import_frame_mesh(frameno)

        vcu.swap_object_mesh_data_geometry(cache_object, vertices, triangles, 
                                           new_mesh_data_name,
                                           is_smooth,
                                           octane_mesh_type)

        self.update_transforms()
        self._update_motion_blur(frameno)
        self._update_velocity_attribute(frameno)
        self._update_speed_attribute(frameno)
        self._update_vorticity_attribute(frameno)
        self._update_age_attribute(frameno)
        self._update_color_attribute(frameno)
        self._update_source_id_attribute(frameno)
        self._update_viscosity_attribute(frameno)
        self._update_id_attribute(frameno)
        self._update_lifetime_attribute(frameno)
        self._update_whitewater_proximity_attribute(frameno)

        self.current_loaded_frame = render.get_current_render_frame()
        self._commit_loaded_frame_data(frameno)

        if vcu.is_blender_279() or render.is_rendering():
            use_persistent_data = bpy.context.scene.render.use_persistent_data
            is_keyframed_hide_render = render.is_keyframed_hide_render_issue_relevant()
            if not use_persistent_data and not is_keyframed_hide_render:
                # Updating depsgraph when 'Persistent Data' option is enabled
                # causes incorrect render. Note: ignoring the depsgraph update
                # can result in more frequent render crashes. 
                if depsgraph is not None:
                    depsgraph.update()
                else:
                    vcu.depsgraph_update()


    def update_transforms(self):
        cache_object = self.get_cache_object()
        transvect = mathutils.Vector((self.bounds.x, self.bounds.y, self.bounds.z))
        transmat = mathutils.Matrix.Translation(-transvect)
        cache_object.data.transform(transmat)
        domain_object = self._get_domain_object()
        dprops = self._get_domain_properties()

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
            
        if vcu.is_blender_28():
            object_collection = bpy.context.scene.collection.all_objects
        else:
            object_collection = bpy.context.scene.objects

        if object_collection.get(self.cache_object.name) is None:
            self.delete_cache_object()
        return self.cache_object


    def import_bobj(self, filename, generate_flat_array=False):
        with open(filename, "rb") as f:
            bobj_data = f.read()

        if len(bobj_data) == 0:
            return [], []

        data_offset = 0
        num_vertices = struct.unpack_from('i', bobj_data, data_offset)[0]
        data_offset += 4

        num_floats = 3 * num_vertices
        num_bytes = 4 * num_floats

        if generate_flat_array:
            vertices = list(struct.unpack_from('{0}f'.format(num_floats), bobj_data, data_offset))
        else:
            it = iter(struct.unpack_from('{0}f'.format(num_floats), bobj_data, data_offset))
            vertices = list(zip(it, it, it))
        data_offset += num_bytes

        num_triangles = struct.unpack_from('i', bobj_data, data_offset)[0]
        data_offset += 4

        num_ints = 3 * num_triangles
        num_bytes = 4 * num_ints

        if generate_flat_array:
            triangles = list(struct.unpack_from('{0}i'.format(num_ints), bobj_data, data_offset))
        else:
            it = iter(struct.unpack_from('{0}i'.format(num_ints), bobj_data, data_offset))
            triangles = list(zip(it, it, it))

        return vertices, triangles


    def import_ffp3(self, filename, pct_surface=1.0, pct_boundary=1.0, pct_interior=1.0, attribute_type='ATTRIBUTE_TYPE_UNKNOWN', generate_flat_array=False):
        with open(filename, "rb") as f:
            attribute_data = f.read()

        vertices = []
        triangles = []
        header_info_dict = None

        if len(attribute_data) == 0:
            return vertices, triangles, header_info_dict
        if pct_surface == 0.0 and pct_boundary == 0.0 and pct_interior == 0.0:
            return vertices, triangles, header_info_dict

        if attribute_type == 'ATTRIBUTE_TYPE_VECTOR':
            sizeof_attribute = 12
            attribute_struct_format_str = '{0}f'
        elif attribute_type == 'ATTRIBUTE_TYPE_INT':
            sizeof_attribute = 4
            attribute_struct_format_str = '{0}i'
        elif attribute_type == 'ATTRIBUTE_TYPE_FLOAT':
            sizeof_attribute = 4
            attribute_struct_format_str = '{0}f'
        elif attribute_type == 'ATTRIBUTE_TYPE_UINT16':
            sizeof_attribute = 2
            attribute_struct_format_str = '{0}H'

        sizeof_uint = 4
        num_surface_particles  = struct.unpack_from('I', attribute_data, 0 * sizeof_uint)[0]
        num_boundary_particles = struct.unpack_from('I', attribute_data, 1 * sizeof_uint)[0]
        num_interior_particles = struct.unpack_from('I', attribute_data, 2 * sizeof_uint)[0]
        id_limit               = struct.unpack_from('I', attribute_data, 3 * sizeof_uint)[0]

        id_surface = int(math.ceil(pct_surface * (id_limit - 1)))
        id_boundary = int(math.ceil(pct_boundary * (id_limit - 1)))
        id_interior = int(math.ceil(pct_interior * (id_limit - 1)))

        id_data_byte_offset = 4 * sizeof_uint
        id_surface_byte_offset = id_data_byte_offset + id_surface * 3 * sizeof_uint + 0 * sizeof_uint
        id_boundary_byte_offset = id_data_byte_offset + id_boundary * 3 * sizeof_uint + 1 * sizeof_uint
        id_interior_byte_offset = id_data_byte_offset + id_interior * 3 * sizeof_uint + 2 * sizeof_uint

        num_surface_particles_to_read  = struct.unpack_from('I', attribute_data, id_surface_byte_offset)[0]
        num_boundary_particles_to_read = struct.unpack_from('I', attribute_data, id_boundary_byte_offset)[0]
        num_interior_particles_to_read = struct.unpack_from('I', attribute_data, id_interior_byte_offset)[0]

        tol = 1e-9
        if pct_surface < tol:
            num_surface_particles_to_read = 0
        if pct_boundary < tol:
            num_boundary_particles_to_read = 0
        if pct_interior < tol:
            num_interior_particles_to_read = 0

        particle_data_byte_offset = id_data_byte_offset + id_limit * 3 * sizeof_uint
        surface_particle_data_byte_offset = particle_data_byte_offset
        boundary_particle_data_byte_offset = surface_particle_data_byte_offset + num_surface_particles * sizeof_attribute
        interior_particle_data_byte_offset = boundary_particle_data_byte_offset + num_boundary_particles * sizeof_attribute

        if attribute_type == 'ATTRIBUTE_TYPE_VECTOR':
            if generate_flat_array:
                attribute_values  = list(struct.unpack_from(attribute_struct_format_str.format(3 * num_surface_particles_to_read),  attribute_data, surface_particle_data_byte_offset))
                attribute_values += list(struct.unpack_from(attribute_struct_format_str.format(3 * num_boundary_particles_to_read), attribute_data, boundary_particle_data_byte_offset))
                attribute_values += list(struct.unpack_from(attribute_struct_format_str.format(3 * num_interior_particles_to_read), attribute_data, interior_particle_data_byte_offset))
            else:
                surface_it  = iter(struct.unpack_from(attribute_struct_format_str.format(3 * num_surface_particles_to_read),  attribute_data, surface_particle_data_byte_offset))
                boundary_it = iter(struct.unpack_from(attribute_struct_format_str.format(3 * num_boundary_particles_to_read), attribute_data, boundary_particle_data_byte_offset))
                interior_it = iter(struct.unpack_from(attribute_struct_format_str.format(3 * num_interior_particles_to_read), attribute_data, interior_particle_data_byte_offset))
                attribute_values = list(zip(surface_it, surface_it, surface_it))
                attribute_values += list(zip(boundary_it, boundary_it, boundary_it))
                attribute_values += list(zip(interior_it, interior_it, interior_it))
        else:
            attribute_values  = list(struct.unpack_from(attribute_struct_format_str.format(num_surface_particles_to_read),  attribute_data, surface_particle_data_byte_offset))
            attribute_values += list(struct.unpack_from(attribute_struct_format_str.format(num_boundary_particles_to_read), attribute_data, boundary_particle_data_byte_offset))
            attribute_values += list(struct.unpack_from(attribute_struct_format_str.format(num_interior_particles_to_read), attribute_data, interior_particle_data_byte_offset))

        header_info_dict = {}
        header_info_dict["num_surface_particles"] = num_surface_particles
        header_info_dict["num_boundary_particles"] = num_boundary_particles
        header_info_dict["num_interior_particles"] = num_interior_particles
        header_info_dict["id_limit"] = id_limit
        header_info_dict["num_surface_particles_to_read"] = num_surface_particles_to_read
        header_info_dict["num_boundary_particles_to_read"] = num_boundary_particles_to_read
        header_info_dict["num_interior_particles_to_read"] = num_interior_particles_to_read

        return attribute_values, triangles, header_info_dict


    def import_wwp(self, filename, pct, generate_flat_array=False):
        if pct == 0:
            return [], []

        with open(filename, "rb") as f:
            wwp_data = f.read()

        if len(wwp_data) == 0:
            return [], []

        dataidx = int(math.ceil((pct / 100) * 255))
        num_vertices = struct.unpack_from('i', wwp_data, dataidx * 4)[0] + 1
        if num_vertices <= 0:
            return [], []

        num_floats = 3 * num_vertices
        data_offset = 256 * 4

        if generate_flat_array:
            vertices = list(struct.unpack_from('{0}f'.format(num_floats), wwp_data, data_offset))
        else:
            it = iter(struct.unpack_from('{0}f'.format(num_floats), wwp_data, data_offset))
            vertices = list(zip(it, it, it))
        triangles = []

        return vertices, triangles


    def import_wwi(self, filename, pct):
        if pct == 0:
            return [], []

        with open(filename, "rb") as f:
            wwi_data = f.read()

        if len(wwi_data) == 0:
            return [], []

        dataidx = int(math.ceil((pct / 100) * 255))
        num_vertices = struct.unpack_from('i', wwi_data, dataidx * 4)[0] + 1
        if num_vertices <= 0:
            return [], []

        num_ints = num_vertices
        data_offset = 256 * 4
        int_values = list(struct.unpack_from('{0}i'.format(num_ints), wwi_data, data_offset))
        triangles = []

        return int_values, triangles


    def import_wwf(self, filename, pct):
        if pct == 0:
            return [], []

        with open(filename, "rb") as f:
            wwi_data = f.read()

        if len(wwi_data) == 0:
            return [], []

        dataidx = int(math.ceil((pct / 100) * 255))
        num_vertices = struct.unpack_from('i', wwi_data, dataidx * 4)[0] + 1
        if num_vertices <= 0:
            return [], []

        num_ints = num_vertices
        data_offset = 256 * 4
        float_values = list(struct.unpack_from('{0}f'.format(num_ints), wwi_data, data_offset))
        triangles = []

        return float_values, triangles


    def import_floats(self, filename):
        with open(filename, "rb") as f:
            float_data = f.read()

        if len(float_data) == 0:
            return []

        datasize = len(float_data)
        num_floats = datasize // 4
        floats = list(struct.unpack_from('{0}f'.format(num_floats), float_data, 0))

        return floats


    def import_ints(self, filename):
        with open(filename, "rb") as f:
            int_data = f.read()

        if len(int_data) == 0:
            return []

        datasize = len(int_data)
        num_int = datasize // 4
        ints = list(struct.unpack_from('{0}i'.format(num_int), int_data, 0))

        return ints


    def import_empty(self, filename):
        return [], []


    def _is_domain_set(self):
        return bpy.context.scene.flip_fluid.get_domain_object() is not None


    def _get_domain_object(self):
        return bpy.context.scene.flip_fluid.get_domain_object()


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()

    
    def _get_cache_directory(self):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        return os.path.normpath(dprops.cache.get_cache_abspath())


    def _get_bakefiles_directory(self):
        cache_directory = self._get_cache_directory()
        return os.path.join(cache_directory, 'bakefiles')


    def _frame_number_to_string(self, frameno):
        return str(frameno).zfill(6)


    def _get_mesh_filepath(self, frameno):
        filename = (self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_motion_blur_filepath(self, frameno):
        filename = ("blur" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_velocity_attribute_filepath(self, frameno):
        filename = ("velocity" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_velocity_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "velocity" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_speed_attribute_filepath(self, frameno):
        filename = ("speed" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_speed_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "speed" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_vorticity_attribute_filepath(self, frameno):
        filename = ("vorticity" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_vorticity_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "vorticity" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_age_attribute_filepath(self, frameno):
        filename = ("age" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_age_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "age" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_color_attribute_filepath(self, frameno):
        filename = ("color" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_color_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "color" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_source_id_attribute_filepath(self, frameno):
        filename = ("sourceid" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_source_id_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "sourceid" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_viscosity_attribute_filepath(self, frameno):
        filename = ("viscosity" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_viscosity_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "viscosity" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_id_attribute_filepath(self, frameno):
        filename = ("id" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".wwi")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_id_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "id" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_lifetime_attribute_filepath(self, frameno, extension):
        filename = ("lifetime" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_lifetime_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "lifetime" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_whitewater_proximity_attribute_filepath(self, frameno):
        filename = ("whitewaterproximity" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".bobj")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_fluid_particle_whitewater_proximity_attribute_filepath(self, frameno):
        filename = (self.mesh_prefix + "whitewaterproximity" +
                    self._frame_number_to_string(frameno) + 
                    ".ffp3")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _is_frame_cached(self, frameno):
        path = self._get_mesh_filepath(frameno)
        return os.path.isfile(path)


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

        if vcu.is_blender_28():
            object_collection = bpy.context.scene.collection.all_objects
        else:
            object_collection = bpy.context.scene.objects

        if object_collection.get(self.cache_object.name) is None:
            self.delete_cache_object()
            return False
        return True


    def _transfer_mesh_materials(self, src_mesh_data, dst_mesh_data):
        material_names = []
        for m in src_mesh_data.materials:
            material_names.append(m.name)
        for name in material_names:
            for m in bpy.data.materials:
                if m.name == name:
                    dst_mesh_data.materials.append(m)
                    break
                    

    def _transfer_mesh_smoothness(self, src_mesh_data, dst_mesh_data):
        if self._is_mesh_smooth(src_mesh_data):
            self._smooth_mesh(dst_mesh_data)
        else:
            self._flatten_mesh(dst_mesh_data)


    def _set_mesh_smoothness(self, mesh_data, is_smooth):
        if is_smooth:
            self._smooth_mesh(mesh_data)
        else:
            self._flatten_mesh(mesh_data)


    def _transfer_octane_settings(self, src_obj, dst_obj):
        if self._is_octane_available():
            dst_obj.octane.object_mesh_type = src_obj.octane.object_mesh_type


    def _get_octane_mesh_type(self, obj):
        if self._is_octane_available():
            return obj.octane.object_mesh_type
        return None


    def _set_octane_settings(self, obj, mesh_type):
        if self._is_octane_available() and mesh_type is not None:
            obj.octane.object_mesh_type = mesh_type


    def _is_mesh_smooth(self, mesh_data):
        if len(mesh_data.polygons) == 0:
            return self.is_mesh_shading_smooth
        if mesh_data.polygons[0].use_smooth:
            self.is_mesh_shading_smooth = True
            return True
        self.is_mesh_shading_smooth = False
        return False


    def _smooth_mesh(self, mesh_data):
        values = [True] * len(mesh_data.polygons)
        mesh_data.polygons.foreach_set("use_smooth", values)


    def _flatten_mesh(self, mesh_data):
        values = [False] * len(mesh_data.polygons)
        mesh_data.polygons.foreach_set("use_smooth", values)


    def _import_frame_mesh(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return [], []

        filepath = self._get_mesh_filepath(frameno)

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            vertices, triangles = import_function(filepath, self.wwp_import_percentage)
        elif import_function == self.import_ffp3:
            vertices, triangles, _ = import_function(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_VECTOR'
                    )
        else:
            vertices, triangles = import_function(filepath)
        return vertices, triangles


    def _import_motion_blur_data(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return []

        filepath = self._get_motion_blur_filepath(frameno)
        if not os.path.exists(filepath):
            return []

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            translation_data, _ = import_function(filepath, self.wwp_import_percentage)
        else:
            translation_data, _ = import_function(filepath)
        return translation_data


    def _import_velocity_attribute_data(self, frameno):
        header_info = None
        velocity_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return velocity_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_velocity_attribute_filepath(frameno)
        else:
            filepath = self._get_velocity_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return velocity_data, header_info

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            velocity_data, _ = import_function(filepath, self.wwp_import_percentage, generate_flat_array=True)
        elif import_function == self.import_ffp3:
            velocity_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_VECTOR',
                    generate_flat_array=True
                    )
        else:
            velocity_data, _ = import_function(filepath, generate_flat_array=True)
        return velocity_data, header_info


    def _import_speed_attribute_data(self, frameno):
        header_info = None
        speed_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return speed_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_speed_attribute_filepath(frameno)
        else:
            filepath = self._get_speed_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return speed_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            speed_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_FLOAT'
                    )
        else:
            speed_data = self.import_floats(filepath)
        return speed_data, header_info


    def _import_vorticity_attribute_data(self, frameno):
        header_info = None
        vorticity_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return vorticity_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_vorticity_attribute_filepath(frameno)
        else:
            filepath = self._get_vorticity_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return vorticity_data, header_info

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            vorticity_data, _ = import_function(filepath, self.wwp_import_percentage, generate_flat_array=True)
        elif import_function == self.import_ffp3:
            vorticity_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_VECTOR',
                    generate_flat_array=True
                    )
        else:
            vorticity_data, _ = import_function(filepath, generate_flat_array=True)
        return vorticity_data, header_info


    def _import_age_attribute_data(self, frameno):
        header_info = None
        age_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return age_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_age_attribute_filepath(frameno)
        else:
            filepath = self._get_age_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return age_data, header_info

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            age_data, _ = import_function(filepath, self.wwp_import_percentage)
        elif import_function == self.import_ffp3:
            age_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_FLOAT'
                    )
        else:
            age_data = self.import_floats(filepath)
        return age_data, header_info


    def _import_color_attribute_data(self, frameno):
        header_info = None
        color_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return color_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_color_attribute_filepath(frameno)
        else:
            filepath = self._get_color_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return color_data, header_info

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            color_data, _ = import_function(filepath, self.wwp_import_percentage, generate_flat_array=True)
        elif import_function == self.import_ffp3:
            color_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_VECTOR', 
                    generate_flat_array=True
                    )
        else:
            color_data, _ = import_function(filepath, generate_flat_array=True)
        return color_data, header_info


    def _import_source_id_attribute_data(self, frameno):
        header_info = None
        source_id_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return source_id_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_source_id_attribute_filepath(frameno)
        else:
            filepath = self._get_source_id_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return source_id_data, header_info


        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            source_id_data, _ = import_function(filepath, self.wwp_import_percentage)
        elif import_function == self.import_ffp3:
            source_id_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_INT'
                    )
        else:
            source_id_data = self.import_ints(filepath)

        return source_id_data, header_info


    def _import_viscosity_attribute_data(self, frameno):
        header_info = None
        viscosity_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return viscosity_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_viscosity_attribute_filepath(frameno)
        else:
            filepath = self._get_viscosity_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return viscosity_data, header_info

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            viscosity_data, _ = import_function(filepath, self.wwp_import_percentage)
        elif import_function == self.import_ffp3:
            viscosity_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_FLOAT'
                    )
        else:
            viscosity_data = self.import_floats(filepath)

        return viscosity_data, header_info


    def _import_id_attribute_data(self, frameno):
        header_info = None
        id_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return id_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_id_attribute_filepath(frameno)
        else:
            filepath = self._get_id_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return id_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            id_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_UINT16'
                    )
        else:
            id_data, _ = self.import_wwi(filepath, self.wwp_import_percentage)
        return id_data, header_info


    def _import_lifetime_attribute_data(self, frameno):
        header_info = None
        lifetime_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return lifetime_data, header_info

        extension = ".data"
        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            extension = ".wwf"

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_lifetime_attribute_filepath(frameno)
        else:
            filepath = self._get_lifetime_attribute_filepath(frameno, extension)
            
        if not os.path.exists(filepath):
            return lifetime_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            lifetime_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_FLOAT'
                    )
        else:
            if import_function == self.import_wwp:
                lifetime_data, _ = self.import_wwf(filepath, self.wwp_import_percentage)
            else:
                lifetime_data = self.import_floats(filepath)

        return lifetime_data, header_info


    def _import_whitewater_proximity_attribute_data(self, frameno):
        header_info = None
        whitewater_proximity_data = []
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return whitewater_proximity_data, header_info

        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            filepath = self._get_fluid_particle_whitewater_proximity_attribute_filepath(frameno)
        else:
            filepath = self._get_whitewater_proximity_attribute_filepath(frameno)

        if not os.path.exists(filepath):
            return whitewater_proximity_data, header_info

        import_function = getattr(self, self.import_function_name)
        if self.cache_object_type == 'CACHE_OBJECT_TYPE_FLUID_PARTICLES':
            whitewater_proximity_data, _, header_info = self.import_ffp3(
                    filepath,
                    pct_surface=self.ffp3_surface_import_percentage,
                    pct_boundary=self.ffp3_boundary_import_percentage,
                    pct_interior=self.ffp3_interior_import_percentage,
                    attribute_type='ATTRIBUTE_TYPE_VECTOR',
                    generate_flat_array=True
                    )
        else:
            if import_function == self.import_wwp:
                whitewater_proximity_data, _ = import_function(filepath, self.wwp_import_percentage, generate_flat_array=True)
            else:
                whitewater_proximity_data, _ = import_function(filepath, generate_flat_array=True)

        return whitewater_proximity_data, header_info


    def _get_bounds_filepath(self, frameno):
        filename = ("bounds" + 
                    self._frame_number_to_string(frameno) + 
                    ".bbox")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _initialize_bounds_data(self, frameno):
        filepath = self._get_bounds_filepath(frameno)
        bounds_data = None
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                bounds_data = json.loads(f.read())
        self.bounds.set(bounds_data)


class FlipFluidGLPointCache(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    mesh_prefix = StringProperty(default=""); exec(conv("mesh_prefix"))
    mesh_file_extension = StringProperty(default=""); exec(conv("mesh_file_extension"))
    current_loaded_frame = IntProperty(default=-1); exec(conv("current_loaded_frame"))
    uid = IntProperty(default=-1); exec(conv("uid"))
    is_enabled = BoolProperty(default=False); exec(conv("is_enabled"))


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

        if not self._is_domain_set() or not self.is_enabled:
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


    def import_fpd(self, filename):
        with open(filename, "rb") as f:
            fpd_data = f.read()

        if len(fpd_data) == 0:
            return [], [], []

        data_offset = 0
        num_particles = struct.unpack_from('i', fpd_data, data_offset)[0]
        data_offset += 4

        num_floats = 3 * num_particles
        num_bytes = 4 * num_floats
        it = iter(struct.unpack_from('{0}f'.format(num_floats), fpd_data, data_offset))
        particles = list(zip(it, it, it))
        data_offset += num_bytes

        num_bins = struct.unpack_from('i', fpd_data, data_offset)[0]
        data_offset += 4

        num_floats = num_bins
        num_bytes = 4 * num_floats
        binstarts = struct.unpack_from('{0}i'.format(num_floats), fpd_data, data_offset)
        data_offset += num_bytes

        num_floats = num_bins
        num_bytes = 4 * num_floats
        binspeeds = struct.unpack_from('{0}f'.format(num_floats), fpd_data, data_offset)
        data_offset += num_bytes

        return particles, binstarts, binspeeds


    def _is_domain_set(self):
        return bpy.context.scene.flip_fluid.get_num_domain_objects() != 0


    def _get_domain_object(self):
        return bpy.context.scene.flip_fluid.get_domain_object()


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()

    
    def _get_cache_directory(self):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        return os.path.normpath(dprops.cache.get_cache_abspath())


    def _get_bakefiles_directory(self):
        cache_directory = self._get_cache_directory()
        return os.path.join(cache_directory, 'bakefiles')


    def _frame_number_to_string(self, frameno):
        return str(frameno).zfill(6)


    def _get_mesh_filepath(self, frameno):
        filename = (self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _is_frame_cached(self, frameno):
        path = self._get_mesh_filepath(frameno)
        return os.path.isfile(path)


    def _import_frame_mesh(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return [], [], []
        filepath = self._get_mesh_filepath(frameno)
        return self.import_fpd(filepath)


class FlipFluidGLForceFieldCache(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    mesh_prefix = StringProperty(default=""); exec(conv("mesh_prefix"))
    mesh_file_extension = StringProperty(default=""); exec(conv("mesh_file_extension"))
    current_loaded_frame = IntProperty(default=-1); exec(conv("current_loaded_frame"))
    uid = IntProperty(default=-1); exec(conv("uid"))
    is_enabled = BoolProperty(default=False); exec(conv("is_enabled"))


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

        if not self._is_domain_set() or not self.is_enabled:
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


    def import_ffd(self, filename):
        with open(filename, "rb") as f:
            ffd_data = f.read()

        if len(ffd_data) == 0:
            return None

        data_offset = 0
        num_vertices = struct.unpack_from('i', ffd_data, data_offset)[0]
        data_offset += 4

        if num_vertices == 0:
            return None

        num_floats = 4 * num_vertices
        num_bytes = 4 * num_floats
        it = iter(struct.unpack_from('{0}f'.format(num_floats), ffd_data, data_offset))
        vertices = list(zip(it, it, it, it))
        data_offset += num_bytes

        return vertices


    def _is_domain_set(self):
        return bpy.context.scene.flip_fluid.get_num_domain_objects() != 0


    def _get_domain_object(self):
        return bpy.context.scene.flip_fluid.get_domain_object()


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()

    
    def _get_cache_directory(self):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        return os.path.normpath(dprops.cache.get_cache_abspath())


    def _get_bakefiles_directory(self):
        cache_directory = self._get_cache_directory()
        return os.path.join(cache_directory, 'bakefiles')


    def _frame_number_to_string(self, frameno):
        return str(frameno).zfill(6)


    def _get_mesh_filepath(self, frameno):
        filename = (self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _is_frame_cached(self, frameno):
        path = self._get_mesh_filepath(frameno)
        return os.path.isfile(path)


    def _import_frame_mesh(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return None
        filepath = self._get_mesh_filepath(frameno)
        return self.import_ffd(filepath)


class FlipFluidCache(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    surface = PointerProperty(type=FlipFluidMeshCache); exec(conv("surface"))
    particles = PointerProperty(type=FlipFluidMeshCache); exec(conv("particles"))
    foam = PointerProperty(type=FlipFluidMeshCache); exec(conv("foam"))
    bubble = PointerProperty(type=FlipFluidMeshCache); exec(conv("bubble"))
    spray = PointerProperty(type=FlipFluidMeshCache); exec(conv("spray"))
    dust = PointerProperty(type=FlipFluidMeshCache); exec(conv("dust"))
    gl_particles = PointerProperty(type=FlipFluidGLPointCache); exec(conv("gl_particles"))
    gl_force_field = PointerProperty(type=FlipFluidGLForceFieldCache); exec(conv("gl_force_field"))
    obstacle = PointerProperty(type=FlipFluidMeshCache); exec(conv("obstacle"))


    def initialize_cache_settings(self):
        global import_bobj

        self.surface.mesh_prefix = ""
        self.surface.mesh_file_extension = "bobj"
        self.surface.cache_object_default_name = "fluid_surface"
        self.surface.import_function_name = "import_bobj"
        self.surface.cache_object_type = "CACHE_OBJECT_TYPE_SURFACE"

        self.particles.mesh_prefix = "fluidparticles"
        self.particles.mesh_file_extension = "ffp3"
        self.particles.cache_object_default_name = "fluid_particles"
        self.particles.import_function_name = "import_ffp3"
        self.particles.cache_object_type = "CACHE_OBJECT_TYPE_FLUID_PARTICLES"

        self.foam.mesh_prefix = "foam"
        self.foam.mesh_file_extension = "wwp"
        self.foam.cache_object_default_name = "whitewater_foam"
        self.foam.import_function_name = "import_wwp"
        self.foam.cache_object_type = "CACHE_OBJECT_TYPE_FOAM"

        self.bubble.mesh_prefix = "bubble"
        self.bubble.mesh_file_extension = "wwp"
        self.bubble.cache_object_default_name = "whitewater_bubble"
        self.bubble.import_function_name = "import_wwp"
        self.bubble.cache_object_type = "CACHE_OBJECT_TYPE_BUBBLE"

        self.spray.mesh_prefix = "spray"
        self.spray.mesh_file_extension = "wwp"
        self.spray.cache_object_default_name = "whitewater_spray"
        self.spray.import_function_name = "import_wwp"
        self.spray.cache_object_type = "CACHE_OBJECT_TYPE_SPRAY"

        self.dust.mesh_prefix = "dust"
        self.dust.mesh_file_extension = "wwp"
        self.dust.cache_object_default_name = "whitewater_dust"
        self.dust.import_function_name = "import_wwp"
        self.dust.cache_object_type = "CACHE_OBJECT_TYPE_DUST"

        self.gl_particles.mesh_prefix = "particles"
        self.gl_particles.mesh_file_extension = "fpd"

        self.gl_force_field.mesh_prefix = "forcefield"
        self.gl_force_field.mesh_file_extension = "ffd"

        self.obstacle.mesh_prefix = "obstacle"
        self.obstacle.mesh_file_extension = "bobj"
        self.obstacle.cache_object_default_name = "debug_obstacle"
        self.obstacle.import_function_name = "import_bobj"
        self.obstacle.cache_object_type = "CACHE_OBJECT_TYPE_OBSTACLE"


    def is_simulation_mesh_load_enabled(self, mesh_name):
        return render.is_simulation_mesh_load_enabled(mesh_name)


    def enable_simulation_mesh_load(self, mesh_name):
        return render.enable_simulation_mesh_load(mesh_name)


    def disable_simulation_mesh_load(self, mesh_name):
        return render.disable_simulation_mesh_load(mesh_name)


    def load_post(self):
        pass


    def initialize_cache_objects(self, enabled_mesh_cache_objects=None):
        self.initialize_cache_settings()
        if not self._is_domain_set():
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

        dprops = self._get_domain_properties()
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
        if not self._is_domain_set():
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

        dprops = self._get_domain_properties()
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
        if not self._is_domain_set():
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


    def _is_domain_set(self):
        return bpy.context.scene.flip_fluid.get_domain_object() is not None


    def _get_domain_object(self):
        return bpy.context.scene.flip_fluid.get_domain_object()


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties()

    
    def _get_cache_directory(self):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        return os.path.normpath(dprops.cache.get_cache_abspath())


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
