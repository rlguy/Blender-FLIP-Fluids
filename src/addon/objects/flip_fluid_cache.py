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
from ..utils import version_compatibility_utils as vcu

DISABLE_MESH_CACHE_LOAD = False
GL_POINT_CACHE_DATA = {}
GL_FORCE_FIELD_CACHE_DATA = {}


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
    mesh_prefix =                StringProperty(default="mesh_prefix"); exec(conv("mesh_prefix"))
    enable_motion_blur =         BoolProperty(default=False);           exec(conv("enable_motion_blur"))
    motion_blur_scale =          FloatProperty(default=-1.0);           exec(conv("motion_blur_scale"))
    enable_velocity_attribute =  BoolProperty(default=False);           exec(conv("enable_velocity_attribute"))
    enable_speed_attribute =     BoolProperty(default=False);           exec(conv("enable_speed_attribute"))
    enable_age_attribute =       BoolProperty(default=False);           exec(conv("enable_age_attribute"))
    enable_color_attribute =     BoolProperty(default=False);           exec(conv("enable_color_attribute"))
    enable_source_id_attribute = BoolProperty(default=False);           exec(conv("enable_source_id_attribute"))
    wwp_import_percentage =      IntProperty(default=0);                exec(conv("wwp_import_percentage"))
    duplivert_scale =            FloatProperty(default=1.0);            exec(conv("duplivert_scale"))
    duplivert_vertices =         IntProperty(default=-1);               exec(conv("duplivert_vertices"))
    duplivert_faces =            IntProperty(default=-1);               exec(conv("duplivert_faces"))
    is_rendering =               BoolProperty(default=True);            exec(conv("is_rendering"))
    frame =                      IntProperty(default=-1);               exec(conv("frame"))


    def reset(self):
        self.property_unset("mesh_prefix")
        self.property_unset("enable_motion_blur")
        self.property_unset("motion_blur_scale")
        self.property_unset("enable_velocity_attribute")
        self.property_unset("enable_speed_attribute")
        self.property_unset("enable_age_attribute")
        self.property_unset("enable_color_attribute")
        self.property_unset("enable_source_id_attribute")
        self.property_unset("wwp_import_percentage")
        self.property_unset("duplivert_scale")
        self.property_unset("is_rendering")
        self.property_unset("frame")


class FlipFluidMeshCache(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    # Mesh properties
    mesh_prefix =                StringProperty(default="");                       exec(conv("mesh_prefix"))
    mesh_display_name_prefix =   StringProperty(default="");                       exec(conv("mesh_display_name_prefix"))
    mesh_file_extension =        StringProperty(default="");                       exec(conv("mesh_file_extension"))
    enable_motion_blur =         BoolProperty(default=False);                      exec(conv("enable_motion_blur"))
    motion_blur_scale =          FloatProperty(default=1.0);                       exec(conv("motion_blur_scale"))
    enable_velocity_attribute =  BoolProperty(default=False);                      exec(conv("enable_velocity_attribute"))
    enable_speed_attribute =     BoolProperty(default=False);                      exec(conv("enable_speed_attribute"))
    enable_age_attribute =       BoolProperty(default=False);                      exec(conv("enable_age_attribute"))
    enable_color_attribute =     BoolProperty(default=False);                      exec(conv("enable_color_attribute"))
    enable_source_id_attribute = BoolProperty(default=False);                      exec(conv("enable_source_id_attribute"))
    cache_object_default_name =  StringProperty(default="");                       exec(conv("cache_object_default_name"))
    cache_object =               PointerProperty(type=bpy.types.Object);           exec(conv("cache_object"))
    is_mesh_shading_smooth =     BoolProperty(default=True);                       exec(conv("is_mesh_shading_smooth"))
    current_loaded_frame =       IntProperty(default=-1);                          exec(conv("current_loaded_frame"))
    import_function_name =       StringProperty(default="import_empty");           exec(conv("import_function_name"))
    wwp_import_percentage =      IntProperty(default=100);                         exec(conv("wwp_import_percentage"))
    duplivert_scale =            FloatProperty(default=1.0);                       exec(conv("duplivert_scale"))
    cache_object_type =          StringProperty(default="CACHE_OBJECT_TYPE_NONE"); exec(conv("cache_object_type"))

    # Duplivert properties
    current_duplivert_loaded_frame = IntProperty(default=-1);                exec(conv("current_duplivert_loaded_frame"))
    duplivert_object_default_name =  StringProperty(default="_particle");    exec(conv("duplivert_object_default_name"))
    duplivert_object =               PointerProperty(type=bpy.types.Object); exec(conv("duplivert_object"))

    # Loaded data properties
    loaded_frame_data =           PointerProperty(type=FlipFluidLoadedMeshData); exec(conv("loaded_frame_data"))
    loaded_duplivert_frame_data = PointerProperty(type=FlipFluidLoadedMeshData); exec(conv("loaded_duplivert_frame_data"))
    bounds =                      PointerProperty(type=FLIPFluidMeshBounds);     exec(conv("bounds"))

    # Deprecated properties - only needed to migrate FLIP Fluids v1.0.6 or lower to newer versions
    # These properties should not be used unless for updating scene for newer versions
    cache_object_name =       StringProperty(default="");  exec(conv("cache_object_name"))
    duplivert_object_name =   StringProperty(default="");  exec(conv("duplivert_object_name"))
    is_duplivert_object_set = BoolProperty(default=False); exec(conv("is_duplivert_object_set"))


    def update_deprecated_mesh_storage(self):
        # In FLIP Fluids version 1.0.6 or lower, mesh cache objects were stored by name
        # In later versions, these objects are stored in a PointerProperty. The purpose
        # of this method is to update older .blend files to the new system by initializing
        # the PointerProperty if necessary.

        domain_object = self._get_domain_object()
        if domain_object is None:
            return

        if self.cache_object_name != "" and self.cache_object is None:
            cache_name = self.cache_object_name
            cache_object = None
            for obj in bpy.data.objects:
                if obj.name == cache_name and obj.parent == domain_object:
                    cache_object = obj
                    break
            if cache_object is not None:
                self.cache_object = cache_object

        if self.is_duplivert_object_set and self.duplivert_object is None:
            duplivert_object = bpy.data.objects.get(self.duplivert_object_name)
            if duplivert_object is not None:
                self.duplivert_object = duplivert_object


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
        cache_object.cycles.use_motion_blur = False

        self._initialize_cache_object_octane(cache_object)

        self.cache_object = cache_object


    def delete_cache_object(self):
        if self.cache_object is None:
            return
        self.unload_duplivert_object()
        cache_object = self.cache_object
        vcu.delete_object(cache_object)
        self.cache_object = None
        self.loaded_frame_data.reset()


    def reset_cache_object(self):
        if not self._is_domain_set() or not self._is_cache_object_initialized():
            return

        cache_object = self.get_cache_object()

        if vcu.is_blender_281():
            mesh_data = cache_object.data

            is_smooth = self._is_mesh_smooth(mesh_data)
            octane_mesh_type = self._get_octane_mesh_type(cache_object)

            mesh_data.clear_geometry()
            mesh_data.from_pydata([], [], [])

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
        return not (self.mesh_prefix                != d.mesh_prefix or 
                    self.enable_motion_blur         != d.enable_motion_blur or
                    self.motion_blur_scale          != d.motion_blur_scale or
                    self.enable_velocity_attribute  != d.enable_velocity_attribute or
                    self.enable_speed_attribute     != d.enable_speed_attribute or
                    self.enable_age_attribute       != d.enable_age_attribute or
                    self.enable_color_attribute     != d.enable_color_attribute or
                    self.enable_source_id_attribute != d.enable_source_id_attribute or
                    self.wwp_import_percentage      != d.wwp_import_percentage or
                    render.is_rendering()           != d.is_rendering or
                    self.current_loaded_frame       != frameno)


    def _commit_loaded_frame_data(self, frameno):
        d = self.loaded_frame_data
        d.mesh_prefix                = self.mesh_prefix
        d.enable_motion_blur         = self.enable_motion_blur
        d.motion_blur_scale          = self.motion_blur_scale
        d.enable_velocity_attribute  = self.enable_velocity_attribute
        d.enable_speed_attribute     = self.enable_speed_attribute
        d.enable_age_attribute       = self.enable_age_attribute
        d.enable_color_attribute     = self.enable_color_attribute
        d.enable_source_id_attribute = self.enable_source_id_attribute
        d.wwp_import_percentage      = self.wwp_import_percentage
        d.is_rendering               = render.is_rendering()
        d.frame  = frameno


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
        velocity_data = self._import_velocity_attribute_data(frameno)

        attribute_name = "flip_velocity"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT_VECTOR", "POINT")
        for i,value in enumerate(attribute.data):
            value.vector = velocity_data[i]


    def _update_speed_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_speed_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        speed_data = self._import_speed_attribute_data(frameno)

        attribute_name = "flip_speed"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
        for i,value in enumerate(attribute.data):
            value.value = speed_data[i]


    def _update_age_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_age_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        age_data = self._import_age_attribute_data(frameno)

        attribute_name = "flip_age"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT", "POINT")
        for i,value in enumerate(attribute.data):
            value.value = age_data[i]


    def _update_color_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_color_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        color_data = self._import_color_attribute_data(frameno)

        attribute_name = "flip_color"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "FLOAT_VECTOR", "POINT")
        for i,value in enumerate(attribute.data):
            value.vector = color_data[i]


    def _update_source_id_attribute(self, frameno):
        if not vcu.is_blender_293() or not self.enable_source_id_attribute:
            return

        cache_object = self.get_cache_object()
        frame_string = self._frame_number_to_string(frameno)
        source_id_data = self._import_source_id_attribute_data(frameno)

        attribute_name = "flip_source_id"
        mesh = cache_object.data
        try:
            mesh.attributes.remove(mesh.attributes.get(attribute_name))
        except:
            pass

        attribute = mesh.attributes.new(attribute_name, "INT", "POINT")
        for i,value in enumerate(attribute.data):
            value.value = source_id_data[i]


    def load_frame(self, frameno, force_load=False, depsgraph=None):
        if not self._is_load_frame_valid(frameno, force_load):
            return

        if not self._is_cache_object_initialized():
            self.initialize_cache_object()

        cache_object = self.get_cache_object()
        if cache_object.mode == 'EDIT':
            # Blender will crash if object is reloaded in edit mode
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
        self._update_age_attribute(frameno)
        self._update_color_attribute(frameno)
        self._update_source_id_attribute(frameno)

        self.current_loaded_frame = render.get_current_render_frame()
        self._commit_loaded_frame_data(frameno)

        use_persistent_data = bpy.context.scene.render.use_persistent_data
        if vcu.is_blender_279() or render.is_rendering():
            if not use_persistent_data:
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
        cache_object.scale = (scale, scale, scale)
        cache_object.location = domain_pos


    def apply_duplivert_object_material(self):
        duplivert_object = self.get_duplivert_object()
        if duplivert_object is None:
            return

        cache_object = self.get_cache_object()
        cache_object_materials = cache_object.data.materials
        duplivert_materials = duplivert_object.data.materials
        duplivert_materials.clear()
        if len(cache_object_materials) == 0:
            return

        material = cache_object_materials[cache_object.active_material_index]
        duplivert_materials.append(material)
        duplivert_object.active_material_index = 0


    def _is_loaded_duplivert_frame_up_to_date(self, frameno):
        d = self.loaded_duplivert_frame_data
        return not (self.mesh_prefix                != d.mesh_prefix or 
                    self.enable_motion_blur         != d.enable_motion_blur or
                    self.motion_blur_scale          != d.motion_blur_scale or
                    self.enable_velocity_attribute  != d.enable_velocity_attribute or
                    self.enable_speed_attribute     != d.enable_speed_attribute or
                    self.enable_age_attribute       != d.enable_age_attribute or
                    self.enable_color_attribute     != d.enable_color_attribute or
                    self.enable_source_id_attribute != d.enable_source_id_attribute or
                    self.wwp_import_percentage      != d.wwp_import_percentage or
                    self.duplivert_scale            != d.duplivert_scale or
                    self.duplivert_vertices         != d.duplivert_vertices or
                    self.duplivert_faces            != d.duplivert_faces or
                    render.is_rendering()           != d.is_rendering or
                    self.current_loaded_frame       != frameno)


    def _commit_loaded_duplivert_frame_data(self, frameno):
        d = self.loaded_duplivert_frame_data
        d.mesh_prefix                = self.mesh_prefix
        d.enable_motion_blur         = self.enable_motion_blur
        d.motion_blur_scale          = self.motion_blur_scale
        d.enable_velocity_attribute  = self.enable_velocity_attribute
        d.enable_speed_attribute     = self.enable_speed_attribute
        d.enable_age_attribute       = self.enable_age_attribute
        d.enable_color_attribute     = self.enable_color_attribute
        d.enable_source_id_attribute = self.enable_source_id_attribute
        d.wwp_import_percentage      = self.wwp_import_percentage
        d.duplivert_scale            = self.duplivert_scale
        d.duplivert_vertices         = self.duplivert_vertices
        d.duplivert_faces            = self.duplivert_faces
        d.is_rendering               = render.is_rendering()
        d.current_loaded_frame       = frameno


    def _is_load_duplivert_object_valid(self, force_load=False):
        if not self._is_domain_set():
            return False
        current_frame = render.get_current_render_frame()
        if current_frame == self.current_duplivert_loaded_frame and not force_load:
            return False
        if self._is_loaded_duplivert_frame_up_to_date(current_frame):
            return False
        return True


    def _is_octane_available(self):
        return hasattr(bpy.context.scene, 'octane')


    def _initialize_duplivert_object_octane(self, cache_object, duplivert_object):
        if not self._is_octane_available():
            return
        duplivert_object.octane.object_mesh_type = cache_object.octane.object_mesh_type


    def set_duplivert_instance_type(self, instance_type):
        cache_object = self.get_cache_object()
        if not cache_object:
            return
        vcu.set_object_instance_type(cache_object, instance_type)


    def set_duplivert_hide_viewport(self, display_bool):
        duplivert_object = self.get_duplivert_object()
        if not duplivert_object:
            return
        vcu.set_object_hide_viewport(duplivert_object, display_bool)


    def initialize_duplivert_object(self, vertices=[], polygons=[], scale=1.0, instance_type='VERTS'):
        if not self._is_cache_object_initialized():
            self.initialize_cache_object()
        cache_object = self.get_cache_object()

        if self._is_duplivert_object_initialized():
            return

        duplivert_object_name = cache_object.name + self.duplivert_object_default_name
        duplivert_mesh_name = duplivert_object_name + "_mesh"
        duplivert_mesh_data = bpy.data.meshes.new(duplivert_mesh_name)
        duplivert_mesh_data.from_pydata(vertices, [], polygons)
        duplivert_object = bpy.data.objects.new(duplivert_object_name, duplivert_mesh_data)
        duplivert_object.scale = (scale, scale, scale)
        duplivert_object.parent = cache_object
        vcu.link_fluid_mesh_object(duplivert_object)

        self._initialize_duplivert_object_octane(cache_object, duplivert_object)
        vcu.set_object_instance_type(cache_object, instance_type)
        vcu.set_object_hide_viewport(duplivert_object, True)

        # Motion blur not supported. Leaving motion blur enabled can cause
        # slow render in versions of Blender 2.91+. Workaround is to
        # automatically disable motion blur on the object.
        duplivert_object.cycles.use_motion_blur = False

        self.duplivert_object = duplivert_object


    def load_duplivert_object(self, vertices, faces, scale=1.0, force_load=False, depsgraph=None):
        self.duplivert_scale = scale
        self.duplivert_vertices = len(vertices)
        self.duplivert_faces = len(faces)
        if not self._is_load_duplivert_object_valid(force_load):
            return

        if not self._is_cache_object_initialized():
            self.initialize_cache_object()
        if not self._is_duplivert_object_initialized():
            self.initialize_duplivert_object()

        cache_object = self.get_cache_object()
        duplivert_object = self.get_duplivert_object()
        duplivert_mesh_name = cache_object.name + self.duplivert_object_default_name + "_mesh"
        is_smooth = True
        octane_mesh_type = self._get_octane_mesh_type(cache_object)

        vcu.swap_object_mesh_data_geometry(
                duplivert_object, 
                vertices, faces, 
                duplivert_mesh_name, 
                is_smooth, 
                octane_mesh_type
            )

        self.duplivert_object = duplivert_object

        duplivert_object.location = (0, 0, 0)
        duplivert_object.scale[0] = scale
        duplivert_object.scale[1] = scale
        duplivert_object.scale[2] = scale

        self.apply_duplivert_object_material()
        vcu.set_object_instance_type(cache_object, 'VERTS')

        current_frame = render.get_current_render_frame()
        self.current_duplivert_loaded_frame = current_frame
        self._commit_loaded_duplivert_frame_data(current_frame)

        if vcu.is_blender_279() or render.is_rendering():
            # This statement causes crashes if exporting Alembic in Blender 2.8x.
            if depsgraph is not None:
                depsgraph.update()
            else:
                vcu.depsgraph_update()


    def unload_duplivert_object(self):
        if not self._is_duplivert_object_initialized():
            return

        duplivert_object = self.get_duplivert_object()
        if duplivert_object is not None:
            vcu.delete_object(duplivert_object)

        cache_object = self.get_cache_object()
        vcu.set_object_instance_type(cache_object, 'NONE')

        self.duplivert_object = None
        self.current_duplivert_loaded_frame = -1
        self.loaded_duplivert_frame_data.reset()


    def get_cache_object(self):
        if self.cache_object is None:
            return None
            
        if vcu.is_blender_28():
            object_collection = bpy.context.scene.collection.all_objects
        else:
            object_collection = bpy.context.scene.objects

        if object_collection.get(self.cache_object.name) is None:
            self.delete_cache_object()
        return self.cache_object


    def _is_duplivert_object_initialized(self):
        return self.duplivert_object is not None


    def get_duplivert_object(self):
        return self.duplivert_object


    def import_bobj(self, filename):
        with open(filename, "rb") as f:
            bobj_data = f.read()

        if len(bobj_data) == 0:
            return [], []

        data_offset = 0
        num_vertices = struct.unpack_from('i', bobj_data, data_offset)[0]
        data_offset += 4

        num_floats = 3 * num_vertices
        num_bytes = 4 * num_floats
        it = iter(struct.unpack_from('{0}f'.format(num_floats), bobj_data, data_offset))
        vertices = list(zip(it, it, it))
        data_offset += num_bytes

        num_triangles = struct.unpack_from('i', bobj_data, data_offset)[0]
        data_offset += 4

        num_ints = 3 * num_triangles
        num_bytes = 4 * num_ints
        it = iter(struct.unpack_from('{0}i'.format(num_ints), bobj_data, data_offset))
        triangles = list(zip(it, it, it))

        return vertices, triangles


    def import_wwp(self, filename, pct):
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
        it = iter(struct.unpack_from('{0}f'.format(num_floats), wwp_data, data_offset))
        vertices = list(zip(it, it, it))
        triangles = []

        return vertices, triangles


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


    def _get_speed_attribute_filepath(self, frameno):
        filename = ("speed" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_age_attribute_filepath(self, frameno):
        filename = ("age" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_color_attribute_filepath(self, frameno):
        filename = ("color" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    "." + self.mesh_file_extension)
        bakefiles_directory = self._get_bakefiles_directory()
        return os.path.join(bakefiles_directory, filename)


    def _get_source_id_attribute_filepath(self, frameno):
        filename = ("sourceid" + self.mesh_prefix + 
                    self._frame_number_to_string(frameno) + 
                    ".data")
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
        for p in mesh_data.polygons:
            if p.use_smooth:
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
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return []

        filepath = self._get_velocity_attribute_filepath(frameno)
        if not os.path.exists(filepath):
            return []

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            velocity_data, _ = import_function(filepath, self.wwp_import_percentage)
        else:
            velocity_data, _ = import_function(filepath)
        return velocity_data


    def _import_speed_attribute_data(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return []

        filepath = self._get_speed_attribute_filepath(frameno)
        if not os.path.exists(filepath):
            return []
        speed_data = self.import_floats(filepath)
        return speed_data


    def _import_age_attribute_data(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return []

        filepath = self._get_age_attribute_filepath(frameno)
        if not os.path.exists(filepath):
            return []
        age_data = self.import_floats(filepath)
        return age_data


    def _import_color_attribute_data(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return []

        filepath = self._get_color_attribute_filepath(frameno)
        if not os.path.exists(filepath):
            return []

        import_function = getattr(self, self.import_function_name)
        if import_function == self.import_wwp:
            color_data, _ = import_function(filepath, self.wwp_import_percentage)
        else:
            color_data, _ = import_function(filepath)
        return color_data


    def _import_source_id_attribute_data(self, frameno):
        if not self._is_domain_set() or not self._is_frame_cached(frameno):
            return []

        filepath = self._get_source_id_attribute_filepath(frameno)
        if not os.path.exists(filepath):
            return []
        source_id_data = self.import_ints(filepath)
        return source_id_data


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


    def load_post(self):
        self._update_deprecated_mesh_storage()


    def initialize_cache_objects(self):
        self.initialize_cache_settings()
        if not self._is_domain_set():
            return

        self.surface.initialize_cache_object()

        dprops = self._get_domain_properties()
        if dprops.whitewater.enable_whitewater_simulation:
            self.foam.initialize_cache_object()
            self.bubble.initialize_cache_object()
            self.spray.initialize_cache_object()
            self.dust.initialize_cache_object()

            foam_vertices, foam_polygons = render.get_whitewater_particle_object_geometry('FOAM')
            bubble_vertices, bubble_polygons = render.get_whitewater_particle_object_geometry('BUBBLE')
            spray_vertices, spray_polygons = render.get_whitewater_particle_object_geometry('SPRAY')
            dust_vertices, dust_polygons = render.get_whitewater_particle_object_geometry('DUST')
            foam_scale = render.get_whitewater_particle_object_scale('FOAM')
            bubble_scale = render.get_whitewater_particle_object_scale('BUBBLE')
            spray_scale = render.get_whitewater_particle_object_scale('SPRAY')
            dust_scale = render.get_whitewater_particle_object_scale('DUST')

            self.foam.initialize_duplivert_object(vertices=foam_vertices, polygons=foam_polygons, scale=foam_scale, instance_type='NONE')
            self.bubble.initialize_duplivert_object(vertices=bubble_vertices, polygons=bubble_polygons, scale=bubble_scale, instance_type='NONE')
            self.spray.initialize_duplivert_object(vertices=spray_vertices, polygons=spray_polygons, scale=spray_scale, instance_type='NONE')
            self.dust.initialize_duplivert_object(vertices=dust_vertices, polygons=dust_polygons, scale=dust_scale, instance_type='NONE')

        if dprops.debug.export_internal_obstacle_mesh:
            self.obstacle.initialize_cache_object()


    def delete_cache_objects(self):
        self.initialize_cache_settings()
        self.surface.delete_cache_object()
        self.foam.delete_cache_object()
        self.bubble.delete_cache_object()
        self.spray.delete_cache_object()
        self.dust.delete_cache_object()
        self.obstacle.delete_cache_object()


    def delete_whitewater_cache_objects(self):
        self.initialize_cache_settings()
        self.foam.delete_cache_object()
        self.bubble.delete_cache_object()
        self.spray.delete_cache_object()
        self.dust.delete_cache_object()


    def delete_obstacle_cache_object(self):
        self.obstacle.delete_cache_object()


    def reset_cache_objects(self):
        self.initialize_cache_settings()
        if not self._is_domain_set():
            return
        self.surface.reset_cache_object()
        self.foam.reset_cache_object()
        self.bubble.reset_cache_object()
        self.spray.reset_cache_object()
        self.dust.reset_cache_object()
        self.obstacle.reset_cache_object()
        self.gl_particles.reset_cache()
        self.gl_force_field.reset_cache()


    def is_cache_object(self, obj):
        cache_objects = [self.surface, self.foam, self.bubble, self.spray, self.dust]
        for c in cache_objects:
            cache_object = c.get_cache_object()
            if cache_object and cache_object.name == obj.name:
                return True
        return False


    def get_mesh_cache_from_blender_object(self, obj):
        cache_objects = [self.surface, self.foam, self.bubble, self.spray, self.dust]
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


    def _update_deprecated_mesh_storage(self):
        self.surface.update_deprecated_mesh_storage()
        self.foam.update_deprecated_mesh_storage()
        self.bubble.update_deprecated_mesh_storage()
        self.spray.update_deprecated_mesh_storage()
        self.dust.update_deprecated_mesh_storage()
        self.obstacle.update_deprecated_mesh_storage()


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
