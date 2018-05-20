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

import bpy, os, math
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        EnumProperty
        )

from .. import types
from ..objects.flip_fluid_aabb import AABB

class DomainSurfaceProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.subdivisions = IntProperty(
                name="Subdivisions",
                description="Number of isosurface subdivisions",
                min=0,
                soft_max=2,
                default=0,
                )
        cls.compute_chunks_auto = IntProperty(
                name="Compute Chunks",
                description="Number of chunks to break up isosurface into during"
                    " computation. Increase to reduce memory usage.",
                min=1,
                default=1,
                )
        cls.compute_chunks_fixed = IntProperty(
                name="Compute Chunks",
                description="Number of chunks to break up surface into during"
                    " mesh generation. Increase to reduce memory usage.",
                min=1,
                default=1,
                )
        cls.compute_chunk_mode = EnumProperty(
                name="Threading Mode",
                description="Determing the number of compute chunks to use when"
                    " generating the surface mesh",
                items=types.surface_compute_chunk_modes,
                default='COMPUTE_CHUNK_MODE_AUTO',
                options={'HIDDEN'},
                )
        cls.smoothing_value = FloatProperty(
                name="Factor", 
                description="Amount of surface smoothing", 
                min=0.0, max=1.0,
                default=0.5,
                precision=3,
                subtype='FACTOR',
                )
        cls.smoothing_iterations = IntProperty(
                name="Repeat",
                description="Number of smoothing iterations",
                min=0, max=30,
                default=2,
                )
        cls.particle_scale = FloatProperty(
                name="Particle Scale", 
                description = "Size of particles for isosurface generation", 
                min=0.0, soft_min=1.0,
                default=1.0,
                precision=2,
                )
        cls.enable_smooth_interface_meshing = BoolProperty(
                name="Mesh Around Obstacles",
                description="Generate mesh around obstacles by creating a smooth" 
                    " fluid-obstacle interface. If disabled, the surface mesh"
                    " will be allowed to penetrate through obstacle surfaces.",
                default=True,
                )
        cls.invert_contact_normals = BoolProperty(
                name="Invert Fluid-Obstacle Contact Normals",
                description="Invert surface mesh normals that contact obstacle"
                    " surfaces. Enable for correct refraction rendering with"
                    " water-glass interfaces. Note: 'Mesh Around Obstacles'"
                    " should be enabled when using this feature.",
                default=False,
                )

        cls.native_particle_scale = FloatProperty(default=3.0)
        cls.default_cells_per_compute_chunk = FloatProperty(default=33.5)   # in millions


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".subdivisions",                    "Subdivisions",               group_id=0)
        add(path + ".particle_scale",                  "Particle Scale",             group_id=0)
        add(path + ".compute_chunk_mode",              "Compute Chunk Mode",         group_id=0)
        add(path + ".compute_chunks_fixed",            "Num Compute Chunks (fixed)", group_id=0)
        add(path + ".smoothing_value",                 "Smoothing Value",            group_id=0)
        add(path + ".smoothing_iterations",            "Smoothing Iterations",       group_id=0)
        add(path + ".enable_smooth_interface_meshing", "Mesh Around Obstacles",      group_id=0)
        add(path + ".invert_contact_normals",          "Invert Contact Normals",     group_id=0)


    def scene_update_post(self, scene):
        self._update_auto_compute_chunks()


    def _update_auto_compute_chunks(self):
        domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        if domain_object is None:
            return
        bbox = AABB.from_blender_object(domain_object)
        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)

        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops.simulation.lock_cell_size:
            unlocked_dx = max_dim / dprops.simulation.resolution
            locked_dx = dprops.simulation.locked_cell_size
            dx = locked_dx
            if abs(locked_dx - unlocked_dx) < 1e-6:
                dx = unlocked_dx
        else:
            dx = max_dim / dprops.simulation.resolution

        subdivisions = self.subdivisions + 1
        isize = math.ceil(bbox.xdim / dx) * subdivisions
        jsize = math.ceil(bbox.ydim / dx) * subdivisions
        ksize = math.ceil(bbox.zdim / dx) * subdivisions
        total_cells = isize * jsize * ksize
        cells_per_chunk = self.default_cells_per_compute_chunk * 1e6
        num_chunks = math.ceil(total_cells / cells_per_chunk)
        num_chunks = max(min(num_chunks, isize), 1)
        if self.compute_chunks_auto != num_chunks:
            self.compute_chunks_auto = num_chunks


def register():
    bpy.utils.register_class(DomainSurfaceProperties)


def unregister():
    bpy.utils.unregister_class(DomainSurfaceProperties)