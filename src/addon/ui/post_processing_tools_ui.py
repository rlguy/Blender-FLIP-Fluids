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

import bpy

from ..operators import post_processing_tools_operators
from ..objects import flip_fluid_attribute


class FLIPFLUID_UL_RemapUVWAttributes(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        self.use_filter_show = False

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        Status = flip_fluid_attribute.RemapUVWItemStatus
        status_to_ui_elements = {
            Status.READY:                        {"label": "Ready",          "icon": "NODE_SOCKET_VECTOR",  "prop": "status_ready_tooltip"},
            Status.LOADED:                       {"label": "Loaded",         "icon": "NODE_SOCKET_SHADER",  "prop": "status_loaded_tooltip"},
            Status.ERROR_REMAP_FRAME_NOT_CACHED: {"label": "Not Cached",     "icon": "NODE_SOCKET_RGBA",    "prop": "status_error_remap_frame_not_cached_tooltip"},
            Status.ERROR_UID_NOT_CACHED:         {"label": "Missing UID",    "icon": "STATUS_ERROR_FILLED", "prop": "status_error_uid_not_cached_tooltip"},
            Status.ERROR_ZERO_LENGTH_FRAME:      {"label": "Zero Particles", "icon": "NODE_SOCKET_RGBA",    "prop": "status_error_zero_length_frame_tooltip"},
            Status.ERROR_CORRUPT_FRAME:          {"label": "Corrupt Cache",  "icon": "STATUS_ERROR_FILLED", "prop": "status_error_corrupt_frame_tooltip"},
            Status.ERROR_UNKNOWN:                {"label": "Unknown Error",  "icon": "STATUS_ERROR_FILLED", "prop": "status_error_unknown_tooltip"},
        }
        status_ui = status_to_ui_elements[item.status]

        split = layout.split(factor=0.40)
        row1 = split.column().row()
        row2 = split.column().row()
        split = row2.split(factor=0.33)
        row2 = split.column().row()
        row3 = split.column().row()

        row1.prop(item, "attribute_name", text="", emboss=False, icon="UV")
        row2.alignment = 'LEFT'
        row2.prop(item, "frame", text="", emboss=False)
        row3.prop(dprops.particles, status_ui["prop"], text=status_ui["label"], emboss=False, icon=status_ui["icon"])
        row3.alignment = 'RIGHT'
        row3.operator("ffops.remap_uvw_attributes_load_frame", icon='FRAME_NEXT', text="").frame = item.frame


def _draw_remap_uvw_attributes_feature(self, context):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()

    box = self.layout.box()
    column = box.column(align=True)

    header, remap_uvw_attributes_body = column.panel("remap_uvw_attributes", default_closed=True)
    header.alignment = 'LEFT'
    header.prop(dprops.particles, "bind_fluid_particle_uvw_attribute_feature_tooltip", text="Bind Fluid Particle UVW Attributes", emboss=False)
    header.operator(
                "wm.url_open", 
                text="",
                icon='URL',
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Post-Processing-Tools#bind-fluid-particle-uvw-attributes"

    if not remap_uvw_attributes_body:
        return

    # Feature Requirements

    is_fluid_particles_enabled = dprops.particles.enable_fluid_particle_output
    is_uvw_enabled = dprops.particles.enable_fluid_particle_uvw_attribute
    is_uid_enabled = dprops.particles.enable_fluid_particle_uid_attribute and not dprops.particles.enable_fluid_particle_uid_attribute_reuse
    is_feature_ready = is_fluid_particles_enabled and is_uvw_enabled and is_uid_enabled

    cache_status = dprops.cache.cache_status
    is_fluid_particles_baked = cache_status.particle_bakefiles_exist
    is_uvw_baked = cache_status.particle_uvw_attribute_bakefiles_exist
    is_uid_baked = cache_status.particle_uid_attribute_bakefiles_exist
    is_data_baked = is_fluid_particles_baked and is_uvw_baked and is_uid_baked

    column.separator()

    req_box = column.box()
    req_col = req_box.column(align=True)
    req_header, req_body = req_col.panel("remap_uvw_attributes_requirements", default_closed=True)

    req_icon = "CHECKMARK" if is_feature_ready else "STATUS_ERROR_FILLED"
    if is_feature_ready and not is_data_baked:
        req_icon = "STATUS_WARNING_FILLED"

    req_header.alignment = 'LEFT'
    req_header.label(text="Feature Requirements", icon=req_icon)
    if not is_data_baked:
        req_header.label(text="(Baking Required)")

    if req_body:
        indent = 5
        split = req_col.split(factor=0.80)
        col_left = split.column()
        col_right = split.column()

        # Enable Fluid Particles
        row = col_left.row()
        row.alignment = 'LEFT'
        row.label(text=indent * " ")
        row.label(text="Enable Fluid Particles", icon="CHECKMARK" if is_fluid_particles_enabled else "STATUS_ERROR_FILLED")
        if is_fluid_particles_enabled:
            col_right.label(text="")
        else:
            col_right.operator("ffops.remap_uvw_attributes_enable_fluid_particles")

        # Enable Fluid Particle UVW Attribute
        row = col_left.row()
        row.alignment = 'LEFT'
        row.label(text=indent * " ")
        row.label(text="Enable Fluid Particle UVW Attribute", icon="CHECKMARK" if is_uvw_enabled else "STATUS_ERROR_FILLED")
        if is_uvw_enabled:
            col_right.label(text="")
        else:
            col_right.operator("ffops.remap_uvw_attributes_enable_uvw_attribute")

        # Enable Fluid Particle UID Attribute
        row = col_left.row()
        row.alignment = 'LEFT'
        row.label(text=indent * " ")
        row.label(text="Enable Fluid Particle UID Attribute", icon="CHECKMARK" if is_uid_enabled else "STATUS_ERROR_FILLED")
        if is_uid_enabled:
            col_right.label(text="")
        else:
            col_right.operator("ffops.remap_uvw_attributes_enable_uid_attribute")

        # Bake Simulation Data
        row = req_col.row()
        row.alignment = 'LEFT'
        row.label(text=indent * " ")
        row.label(text="Bake Simulation Data", icon="CHECKMARK" if is_data_baked else "STATUS_WARNING_FILLED")
        if not is_data_baked:
            row.label(text="Particles", icon="CHECKMARK" if is_fluid_particles_baked else "STATUS_ERROR_FILLED")
            row.label(text="UVW", icon="CHECKMARK" if is_uvw_baked else "STATUS_ERROR_FILLED")
            row.label(text="UID", icon="CHECKMARK" if is_uid_baked else "STATUS_ERROR_FILLED")

    column.separator()

    # UI List and Operators
    column = column.column(align=True)
    column.enabled = is_feature_ready

    split = column.split(factor=0.40)
    row1 = split.column().row()
    row2 = split.column().row()
    split = row2.split(factor=0.33)
    row2 = split.column().row()
    row3 = split.column().row()

    row1.alignment = 'LEFT'
    row1.prop(dprops.particles, "attribute_name_header_tooltip", text=10*" " + "UVW Attribute Name", emboss=False)
    row2.alignment = 'LEFT'
    row2.prop(dprops.particles, "bind_frame_header_tooltip", text="Bind Frame", emboss=False)
    row3.alignment = 'LEFT'
    row3.prop(dprops.particles, "status_frame_header_tooltip", text="Status", emboss=False)

    row = column.row()
    row.template_list(
        "FLIPFLUID_UL_RemapUVWAttributes", "",
        dprops.particles, "remap_uvw_attributes",
        dprops.particles, "remap_uvw_attributes_list_index"
    )
    
    col = row.column(align=True)
    col.operator("ffops.remap_uvw_attributes_new_item",    icon='ADD', text="")
    col.operator("ffops.remap_uvw_attributes_delete_item", icon='REMOVE', text="")
    col.separator()
    col.operator("ffops.remap_uvw_attributes_move_item",   icon='TRIA_UP', text="").direction = 'UP'
    col.operator("ffops.remap_uvw_attributes_move_item",   icon='TRIA_DOWN', text="").direction = 'DOWN'

    column.operator("flip_fluid_operators.reload_frame", text="Reload Frame")


def draw_post_processing_tools_panel(self, context):
    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        self.layout.label(text="Please create a domain object")
        self.layout.operator("flip_fluid_operators.helper_create_domain")
        return

    _draw_remap_uvw_attributes_feature(self, context)


def register():
    bpy.utils.register_class(FLIPFLUID_UL_RemapUVWAttributes)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_UL_RemapUVWAttributes)