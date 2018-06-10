# Blender FLIP Fluid Add-on
# Copyright (C) 2018 Ryan L. Guy
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

DISABLE_MESH_CACHE_LOAD = False
GL_POINT_CACHE_DATA = {}


class FLIPFluidMeshBounds(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.x = FloatProperty(0.0)
        cls.y = FloatProperty(0.0)
        cls.z = FloatProperty(0.0)
        cls.width = FloatProperty(1.0)
        cls.height = FloatProperty(1.0)
        cls.depth = FloatProperty(1.0)
        cls.dx = FloatProperty(1.0)
        cls.is_set = BoolProperty(False)


    @classmethod
    def unregister(cls):
        pass


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


    def is_set(self):
        return self.is_set


class FlipFluidMeshCache(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.mesh_prefix = StringProperty(default="")
        cls.mesh_display_name_prefix = StringProperty(default="")
        cls.mesh_file_extension = StringProperty(default="")
        cls.cache_object_default_name = StringProperty(default="")
        cls.cache_object_name = StringProperty(default="")
        cls.is_mesh_shading_smooth = BoolProperty(default=False)
        cls.current_loaded_frame = IntProperty(default=-1)
        cls.import_function_name = StringProperty(default="import_empty")
        cls.wwp_import_percentage = IntProperty(default=100)
        cls.cache_object_type = StringProperty(default="CACHE_OBJECT_TYPE_NONE")

        cls.is_duplivert_object_set = BoolProperty(default=False)
        cls.current_duplivert_loaded_frame = IntProperty(default=-1)
        cls.duplivert_object_default_name = StringProperty(default="_particle")
        cls.duplivert_object_name = StringProperty(default="")
        cls.bounds = PointerProperty(type=FLIPFluidMeshBounds)


    @classmethod
    def unregister(cls):
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
        bpy.context.scene.objects.link(cache_object)

        self.cache_object_name = cache_object.name
        self._initialize_cache_object_octane(cache_object)


    def delete_cache_object(self, domain_object):
        if not self._is_cache_object_initialized(domain_object):
            return
        cache_object = self.get_cache_object(domain_object)
        mesh_data = cache_object.data
        bpy.data.objects.remove(cache_object, True)
        mesh_data.user_clear()
        bpy.data.meshes.remove(mesh_data)
        self.cache_object_name = ""


    def reset_cache_object(self):
        if not self._is_domain_set() or not self._is_cache_object_initialized():
            return

        cache_object = self.get_cache_object()
        old_mesh_data = cache_object.data

        mesh_data_name = self.cache_object_default_name + "_mesh"
        new_mesh_data = bpy.data.meshes.new(mesh_data_name)
        new_mesh_data.from_pydata([], [], [])
        
        self._transfer_mesh_materials(old_mesh_data, new_mesh_data)
        self._transfer_mesh_smoothness(old_mesh_data, new_mesh_data)
        self._transfer_octane_settings(old_mesh_data, new_mesh_data)

        cache_object.data = new_mesh_data
        domain_object = self._get_domain_object()

        old_mesh_data.user_clear()
        bpy.data.meshes.remove(old_mesh_data)


    def load_frame(self, frameno, force_load = False):
        global DISABLE_MESH_CACHE_LOAD
        if DISABLE_MESH_CACHE_LOAD:
            return

        if not self._is_domain_set():
            return

        current_frame = bpy.context.scene.frame_current
        if current_frame == self.current_loaded_frame and not force_load:
            return

        if not self._is_cache_object_initialized():
            self.initialize_cache_object()

        cache_object = self.get_cache_object()
        old_mesh_data = cache_object.data
        if cache_object.mode == 'EDIT':
            # Blender will crash if object is reloaded in edit mode
            return

        self._initialize_bounds_data(frameno)
        vertices, triangles = self._import_frame_mesh(frameno)

        frame_string = self._frame_number_to_string(frameno)
        new_mesh_data_name = (self.mesh_display_name_prefix + 
                              self.cache_object_name + 
                              frame_string)
        new_mesh_data = bpy.data.meshes.new(new_mesh_data_name)
        new_mesh_data.from_pydata(vertices, [], triangles)
        self._transfer_mesh_materials(old_mesh_data, new_mesh_data)
        self._transfer_mesh_smoothness(old_mesh_data, new_mesh_data)
        self._transfer_octane_settings(old_mesh_data, new_mesh_data)

        cache_object.data = new_mesh_data
        old_mesh_data.user_clear()
        bpy.data.meshes.remove(old_mesh_data)

        self.update_transforms()

        self.current_loaded_frame = current_frame


    def update_transforms(self):
        cache_object = self.get_cache_object()
        transvect = mathutils.Vector((self.bounds.x, self.bounds.y, self.bounds.z))
        transmat = mathutils.Matrix.Translation(-transvect)
        cache_object.data.transform(transmat)
        domain_object = self._get_domain_object()
        domain_bounds = AABB.from_blender_object(domain_object)

        domain_pos = mathutils.Vector((domain_bounds.x, domain_bounds.y, domain_bounds.z))
        scalex = (math.ceil(domain_bounds.xdim / self.bounds.dx) * self.bounds.dx) / self.bounds.width
        scaley = (math.ceil(domain_bounds.ydim / self.bounds.dx) * self.bounds.dx) / self.bounds.height
        scalez = (math.ceil(domain_bounds.zdim / self.bounds.dx) * self.bounds.dx) / self.bounds.depth
        scale = min(scalex, scaley, scalez)
        cache_object.matrix_world = mathutils.Matrix.Identity(4)
        cache_object.matrix_parent_inverse = domain_object.matrix_world.inverted()
        cache_object.scale = (scale, scale, scale)
        cache_object.location = domain_pos


    def apply_duplivert_object_material(self, duplivert_object=None):
        if duplivert_object is None:
            duplivert_object = bpy.data.objects.get(self.duplivert_object_name)
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


    def load_duplivert_object(self, obj, 
                              scale=1.0, display_in_viewport=False, force_load=False):
        if not self._is_domain_set():
            return

        current_frame = bpy.context.scene.frame_current
        if current_frame == self.current_duplivert_loaded_frame and not force_load:
            return
        if not self._is_cache_object_initialized():
            self.initialize_cache_object()
        if self.is_duplivert_object_set:
            self.unload_duplivert_object()

        cache_object = self.get_cache_object()
        duplivert_object_name = self.cache_object_name + self.duplivert_object_default_name
        duplivert_mesh_name = duplivert_object_name + "_mesh"
        duplivert_mesh_data = obj.data.copy()
        duplivert_mesh_data.name = duplivert_mesh_name
        duplivert_object = bpy.data.objects.new(duplivert_object_name, duplivert_mesh_data)
        duplivert_object.parent = cache_object
        duplivert_object.hide = not display_in_viewport
        duplivert_object.matrix_world = obj.matrix_world.copy()
        duplivert_object.location = (0, 0, 0)
        duplivert_object.scale[0] *= scale
        duplivert_object.scale[1] *= scale
        duplivert_object.scale[2] *= scale
        self.apply_duplivert_object_material(duplivert_object)
        bpy.context.scene.objects.link(duplivert_object)

        cache_object.dupli_type = 'VERTS'

        self.is_duplivert_object_set = True
        self.duplivert_object_name = duplivert_object.name
        self.load_duplivert_object_octane(cache_object, duplivert_object)

        self.current_duplivert_loaded_frame = current_frame


    def unload_duplivert_object(self):
        if not self.is_duplivert_object_set:
            return

        duplivert_object = bpy.data.objects.get(self.duplivert_object_name)
        if duplivert_object is not None:
            mesh_data = duplivert_object.data
            bpy.data.objects.remove(duplivert_object, True)
            mesh_data.user_clear()
            bpy.data.meshes.remove(mesh_data)

        cache_object = self.get_cache_object()
        cache_object.dupli_type = 'NONE'

        self.is_duplivert_object_set = False
        self.duplivert_object_name = ""
        self.current_duplivert_loaded_frame = -1


    def get_cache_object(self, domain_object = None):
        if domain_object is None and not self._is_domain_set():
            return None

        if domain_object is None:
            domain_object = self._get_domain_object()

        cache_name = self.cache_object_name
        for obj in bpy.data.objects:
            if obj.name == cache_name and obj.parent == domain_object:
                return obj
        return None


    def get_duplivert_object(self, domain_object = None):
        if not self.is_duplivert_object_set or not self._is_domain_set():
            return None
        return bpy.data.objects.get(self.duplivert_object_name)


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


    def import_empty(self, filename):
        return [], []


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


    def _initialize_cache_object_octane(self, cache_object):
        if not self._is_octane_available():
            return

        GLOBAL = '0'
        SCATTER = '1'
        MOVABLE_PROXY = '2'
        RESHAPEABLE_PROXY = '3'

        if self.mesh_file_extension == 'bobj':
            cache_object.data.octane.mesh_type = GLOBAL
        elif self.mesh_file_extension == 'wwp':
            cache_object.data.octane.mesh_type = SCATTER


    def _is_octane_available(self):
        return hasattr(bpy.context.scene, 'octane')


    def load_duplivert_object_octane(self, cache_object, duplivert_object):
        if not self._is_octane_available():
            return
        duplivert_object.data.octane.mesh_type = cache_object.data.octane.mesh_type


    def _is_cache_object_initialized(self, domain_object = None):
        if domain_object is None and not self._is_domain_set():
            return False

        if domain_object is None:
            domain_object = self._get_domain_object()

        cache_name = self.cache_object_name
        for obj in bpy.data.objects:
            if obj.name == cache_name and obj.parent == domain_object:
                return True
        return False


    def _transfer_mesh_materials(self, src_mesh_data, dst_mesh_data):
        for m in dst_mesh_data.materials:
            dst_mesh_data.materials.pop(0, update_data=True)
        for m in src_mesh_data.materials:
            dst_mesh_data.materials.append(m)


    def _transfer_mesh_smoothness(self, src_mesh_data, dst_mesh_data):
        if self._is_mesh_smooth(src_mesh_data):
            self._smooth_mesh(dst_mesh_data)
        else:
            self._flatten_mesh(dst_mesh_data)


    def _transfer_octane_settings(self, src_mesh_data, dst_mesh_data):
        if self._is_octane_available():
            dst_mesh_data.octane.mesh_type = src_mesh_data.octane.mesh_type


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
        for p in mesh_data.polygons:
            p.use_smooth = True


    def _flatten_mesh(self, mesh_data):
        for p in mesh_data.polygons:
            p.use_smooth = False


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
            with open(filepath, 'r') as f:
                bounds_data = json.loads(f.read())
        self.bounds.set(bounds_data)


class FlipFluidGLPointCache(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.mesh_prefix = StringProperty(default="")
        cls.mesh_file_extension = StringProperty(default="")
        cls.current_loaded_frame = IntProperty(default=-1)
        cls.uid = IntProperty(default=-1)
        cls.is_enabled = BoolProperty(default=False)


    @classmethod
    def unregister(cls):
        pass


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


    def get_point_cache_data(self):
        global GL_POINT_CACHE_DATA
        if self.uid in GL_POINT_CACHE_DATA:
            return GL_POINT_CACHE_DATA[self.uid]
        return None


    def load_frame(self, frameno, force_load = False):
        global GL_POINT_CACHE_DATA

        if not self._is_domain_set() or not self.is_enabled:
            return

        current_frame = bpy.context.scene.frame_current
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


class FlipFluidCache(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.surface = PointerProperty(type=FlipFluidMeshCache)
        cls.foam = PointerProperty(type=FlipFluidMeshCache)
        cls.bubble = PointerProperty(type=FlipFluidMeshCache)
        cls.spray = PointerProperty(type=FlipFluidMeshCache)
        cls.gl_particles = PointerProperty(type=FlipFluidGLPointCache)
        cls.obstacle = PointerProperty(type=FlipFluidMeshCache)


    @classmethod
    def unregister(cls):
        pass


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

        self.gl_particles.mesh_prefix = "particles"
        self.gl_particles.mesh_file_extension = "fpd"

        self.obstacle.mesh_prefix = "obstacle"
        self.obstacle.mesh_file_extension = "bobj"
        self.obstacle.cache_object_default_name = "debug_obstacle"
        self.obstacle.import_function_name = "import_bobj"
        self.obstacle.cache_object_type = "CACHE_OBJECT_TYPE_OBSTACLE"


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

        if dprops.debug.export_internal_obstacle_mesh:
            self.obstacle.initialize_cache_object()


    def delete_cache_objects(self, domain_object):
        self.initialize_cache_settings()
        self.surface.delete_cache_object(domain_object)
        self.foam.delete_cache_object(domain_object)
        self.bubble.delete_cache_object(domain_object)
        self.spray.delete_cache_object(domain_object)
        self.obstacle.delete_cache_object(domain_object)


    def delete_whitewater_cache_objects(self, domain_object):
        self.initialize_cache_settings()
        self.foam.delete_cache_object(domain_object)
        self.bubble.delete_cache_object(domain_object)
        self.spray.delete_cache_object(domain_object)


    def delete_obstacle_cache_object(self, domain_object):
        self.obstacle.delete_cache_object(domain_object)


    def reset_cache_objects(self):
        self.initialize_cache_settings()
        if not self._is_domain_set():
            return
        self.surface.reset_cache_object()
        self.foam.reset_cache_object()
        self.bubble.reset_cache_object()
        self.spray.reset_cache_object()
        self.obstacle.reset_cache_object()
        self.gl_particles.reset_cache()


    def is_cache_object(self, obj):
        cache_objects = [self.surface, self.foam, self.bubble, self.spray]
        for c in cache_objects:
            cache_object = c.get_cache_object()
            if cache_object and cache_object.name == obj.name:
                return True
        return False


    def get_mesh_cache_from_blender_object(self, obj):
        cache_objects = [self.surface, self.foam, self.bubble, self.spray]
        for c in cache_objects:
            cache_object = c.get_cache_object()
            if cache_object and cache_object.name == obj.name:
                return c
        return None


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


def register():
    bpy.utils.register_class(FLIPFluidMeshBounds)
    bpy.utils.register_class(FlipFluidMeshCache)
    bpy.utils.register_class(FlipFluidGLPointCache)
    bpy.utils.register_class(FlipFluidCache)


def unregister():
    bpy.utils.unregister_class(FLIPFluidMeshBounds)
    bpy.utils.unregister_class(FlipFluidMeshCache)
    bpy.utils.unregister_class(FlipFluidGLPointCache)
    bpy.utils.unregister_class(FlipFluidCache)

    global GL_POINT_CACHE_DATA
    GL_POINT_CACHE_DATA = {}
