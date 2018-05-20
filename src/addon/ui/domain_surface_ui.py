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

import bpy

    
class FlipFluidDomainTypeFluidSurfacePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Surface"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        obj = context.scene.objects.active
        sprops = obj.flip_fluid.domain.surface

        column = self.layout.column(align=True)
        split = column.split()
        column_surface = split.column(align=True)
        column_chunks = split.column(align=True)

        column_surface.label("Surface Mesh:")
        column_surface.prop(sprops, "subdivisions")
        column_surface.prop(sprops, "particle_scale")

        split = column_chunks.split(align=True)
        column_left = split.column(align=True)
        column_left.label("Compute Chunks:")
        row = column_left.row(align=True)
        row.prop(sprops, "compute_chunk_mode", expand=True)
        row = column_left.row(align=True)
        if sprops.compute_chunk_mode == 'COMPUTE_CHUNK_MODE_AUTO':
            row.enabled = False
            row.prop(sprops, "compute_chunks_auto")
        elif sprops.compute_chunk_mode == 'COMPUTE_CHUNK_MODE_FIXED':
            row.prop(sprops, "compute_chunks_fixed")

        column = self.layout.column(align=True)
        column.label("Smoothing:")
        row = self.layout.row(align=True)
        row.prop(sprops, "smoothing_value")
        row.prop(sprops, "smoothing_iterations")

        column = self.layout.column(align=True)
        column.separator()
        column.prop(sprops, "enable_smooth_interface_meshing")
        column.prop(sprops, "invert_contact_normals")


def register():
    bpy.utils.register_class(FlipFluidDomainTypeFluidSurfacePanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeFluidSurfacePanel)
