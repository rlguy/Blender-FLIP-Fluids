# MIT License
# 
# Copyright (c) 2018 Ryan L. Guy
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from ctypes import c_void_p, c_char_p, c_int, c_float, c_double, byref

from .pyfluid import pyfluid as lib
from . import pybindings as pb
from . import method_decorators as decorators
from .trianglemesh import TriangleMesh_t

class MeshFluidSource():
    
    def __init__(self, i, j, k, dx, mesh_data, translation_data = None):
        if isinstance(mesh_data, list):
            if translation_data:
                self._init_from_meshes_translations(i, j, k, dx, 
                                                    mesh_data, translation_data)
            else:
                self._init_from_meshes(i, j, k, dx, mesh_data)
        else:
            self._init_from_mesh(i, j, k, dx, mesh_data)

    def __del__(self):
        libfunc = lib.MeshFluidSource_destroy
        pb.init_lib_func(libfunc, [c_void_p], None)
        try:
            libfunc(self._obj)
        except:
            pass

    def __call__(self):
        return self._obj

    def _init_from_mesh(self, i, j, k, dx, mesh):
        mesh_struct = mesh.to_struct()

        libfunc = lib.MeshFluidSource_new_from_mesh
        args = [c_int, c_int, c_int, c_double, c_void_p, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        self._obj = pb.execute_lib_func(libfunc, 
                                        [i, j, k, dx, byref(mesh_struct)])

    def _init_from_meshes(self, i, j, k, dx, meshes):
        num_meshes = len(meshes)
        mesh_structs = (TriangleMesh_t * num_meshes)()
        for idx, m in enumerate(meshes):
            mesh_structs[idx] = m.to_struct()

        libfunc = lib.MeshFluidSource_new_from_meshes
        args = [c_int, c_int, c_int, c_double, c_void_p, c_int, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        self._obj = pb.execute_lib_func(
                libfunc, [i, j, k, dx, mesh_structs, num_meshes]
        )

    def _init_from_meshes_translations(self, i, j, k, dx, meshes, translations):
        num_meshes = len(meshes)
        mesh_structs = (TriangleMesh_t * num_meshes)()
        translation_structs = (TriangleMesh_t * num_meshes)()
        for idx, m in enumerate(meshes):
            mesh_structs[idx] = m.to_struct()
        for idx, m in enumerate(translations):
            translation_structs[idx] = m.to_struct()

        libfunc = lib.MeshFluidSource_new_from_meshes_translations
        args = [c_int, c_int, c_int, c_double, c_void_p, c_void_p, c_int, c_void_p]
        pb.init_lib_func(libfunc, args, c_void_p)
        self._obj = pb.execute_lib_func(
                libfunc, [i, j, k, dx, mesh_structs, translation_structs, num_meshes]
        )

    @property
    def enable(self):
        libfunc = lib.MeshFluidSource_is_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable.setter
    def enable(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable
        else:
            libfunc = lib.MeshFluidSource_disable
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def substep_emissions(self):
        libfunc = lib.MeshFluidSource_get_substep_emissions
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return pb.execute_lib_func(libfunc, [self()])

    @substep_emissions.setter
    def substep_emissions(self, n):
        libfunc = lib.MeshFluidSource_set_substep_emissions
        pb.init_lib_func(libfunc, [c_void_p, c_int, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), n])

    @property
    def inflow(self):
        libfunc = lib.MeshFluidSource_is_inflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @inflow.setter
    def inflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_set_inflow
        else:
            libfunc = lib.MeshFluidSource_set_outflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def outflow(self):
        libfunc = lib.MeshFluidSource_is_inflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @outflow.setter
    def outflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_set_outflow
        else:
            libfunc = lib.MeshFluidSource_set_inflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def fluid_outflow(self):
        libfunc = lib.MeshFluidSource_is_fluid_outflow_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @fluid_outflow.setter
    def fluid_outflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_fluid_outflow
        else:
            libfunc = lib.MeshFluidSource_disable_fluid_outflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def diffuse_outflow(self):
        libfunc = lib.MeshFluidSource_is_diffuse_outflow_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @diffuse_outflow.setter
    def diffuse_outflow(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_diffuse_outflow
        else:
            libfunc = lib.MeshFluidSource_disable_diffuse_outflow
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    def get_velocity(self):
        libfunc = lib.MeshFluidSource_get_velocity
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], Vector3_t)
        cvect = pb.execute_lib_func(libfunc, [self()])
        return Vector3.from_struct(cvect)

    @decorators.xyz_or_vector
    def set_velocity(self, vx, vy, vz):
        libfunc = lib.MeshFluidSource_set_velocity
        pb.init_lib_func(
            libfunc, 
            [c_void_p, c_double, c_double, c_double, c_void_p], None
        )
        pb.execute_lib_func(libfunc, [self(), vx, vy, vz])

    @property
    def enable_append_object_velocity(self):
        libfunc = lib.MeshFluidSource_is_append_object_velocity_enabled
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_append_object_velocity.setter
    def enable_append_object_velocity(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_append_object_velocity
        else:
            libfunc = lib.MeshFluidSource_disable_append_object_velocity
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def object_velocity_influence(self):
        libfunc = lib.MeshFluidSource_get_object_velocity_influence
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_float)
        return pb.execute_lib_func(libfunc, [self()])

    @object_velocity_influence.setter
    def object_velocity_influence(self, value):
        libfunc = lib.MeshFluidSource_set_object_velocity_influence
        pb.init_lib_func(libfunc, [c_void_p, c_float, c_void_p], None)
        pb.execute_lib_func(libfunc, [self(), value])

    @property
    def enable_rigid_mesh(self):
        libfunc = lib.MeshFluidSource_is_mesh_rigid
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @enable_rigid_mesh.setter
    def enable_rigid_mesh(self, boolval):
        if boolval:
            libfunc = lib.MeshFluidSource_enable_rigid_mesh
        else:
            libfunc = lib.MeshFluidSource_disable_rigid_mesh
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
        pb.execute_lib_func(libfunc, [self()])

    @property
    def outflow_inverse(self):
        libfunc = lib.MeshFluidSource_is_outflow_inversed
        pb.init_lib_func(libfunc, [c_void_p, c_void_p], c_int)
        return bool(pb.execute_lib_func(libfunc, [self()]))

    @outflow_inverse.setter
    def outflow_inverse(self, boolval):
        do_inverse = (boolval and not self.outflow_inverse) or (not boolval and self.outflow_inverse)
        if do_inverse:
            libfunc = lib.MeshFluidSource_outflow_inverse
            pb.init_lib_func(libfunc, [c_void_p, c_void_p], None)
            pb.execute_lib_func(libfunc, [self()])