# Blender FLIP Fluid Add-on
# Copyright (C) 2019 Ryan L. Guy
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

from ..utils import version_compatibility_utils as vcu

    
class FLIPFLUID_PT_DomainTypeFluidSurfacePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Surface"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        obj = vcu.get_active_object(context)
        sprops = obj.flip_fluid.domain.surface
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode

        box = self.layout.box()
        column = box.column(align=True)

        if not show_advanced:
            column.label(text="Surface Mesh:")
            column.prop(sprops, "subdivisions")
            column.prop(sprops, "particle_scale")
            return

        split = column.split()
        column_surface = split.column(align=True)
        column_chunks = split.column(align=True)

        column_surface.label(text="Surface Mesh:")
        column_surface.prop(sprops, "subdivisions")
        column_surface.prop(sprops, "particle_scale")

        split = column_chunks.split(align=True)
        column_left = split.column(align=True)
        column_left.label(text="Compute Chunks:")
        row = column_left.row(align=True)
        row.prop(sprops, "compute_chunk_mode", expand=True)
        row = column_left.row(align=True)
        if sprops.compute_chunk_mode == 'COMPUTE_CHUNK_MODE_AUTO':
            row.enabled = False
            row.prop(sprops, "compute_chunks_auto")
        elif sprops.compute_chunk_mode == 'COMPUTE_CHUNK_MODE_FIXED':
            row.prop(sprops, "compute_chunks_fixed")

        object_collection = vcu.get_scene_collection()
        if vcu.is_blender_28():
            search_group = "all_objects"
        else:
            search_group = "objects"

        box = self.layout.box()
        box.label(text="Meshing Volume:")
        row = box.row(align=True)
        row.prop(sprops, "meshing_volume_mode", expand=True)
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column(align=True)
        column_right = split.column(align=True)
        column_right.enabled = sprops.meshing_volume_mode == "MESHING_VOLUME_MODE_OBJECT"
        column_right.prop_search(sprops, "meshing_volume_object", object_collection, search_group, text="Object")
        column_right.prop(sprops, "export_animated_meshing_volume_object")

        box = self.layout.box()
        box.label(text="Meshing Against Boundary:")
        column = box.column(align=True)
        split = column.split(align=True)
        column_left = split.column()
        column_left.prop(sprops, "remove_mesh_near_domain")
        column_right = split.column()
        column_right.enabled = sprops.remove_mesh_near_domain
        column_right.prop(sprops, "remove_mesh_near_domain_distance")

        box = self.layout.box()
        box.label(text="Meshing Against Obstacles:")
        column = box.column(align=True)
        column.prop(sprops, "enable_meshing_offset")
        row = box.row(align=True)
        row.enabled = sprops.enable_meshing_offset
        row.prop(sprops, "obstacle_meshing_mode", expand=True)

        box = self.layout.box()
        box.label(text="Smoothing:")
        row = box.row(align=True)
        row.prop(sprops, "smoothing_value")
        row.prop(sprops, "smoothing_iterations")

        # Motion Blur is no longer supported
        #column = self.layout.column(align=True)
        #column.separator()
        #column.prop(sprops, "generate_motion_blur_data")


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeFluidSurfacePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeFluidSurfacePanel)
