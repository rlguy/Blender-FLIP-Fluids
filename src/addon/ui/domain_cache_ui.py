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

import bpy, math

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_DomainTypeCachePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Cache"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def format_bytes(self, num):
        # Method adapted from: http://stackoverflow.com/a/10171475
        unit_list = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']
        decimal_list = [0, 0, 1, 2, 2, 2]

        if num > 1:
            exponent = min(int(math.log(num, 1024)), len(unit_list) - 1)
            quotient = float(num) / 1024**exponent
            unit, num_decimals = unit_list[exponent], decimal_list[exponent]
            format_string = '{:.%sf} {}' % (num_decimals)
            return format_string.format(quotient, unit)
        if num == 0:
            return '0 bytes'
        if num == 1:
            return '1 byte'


    def draw(self, context):
        domain_object = vcu.get_active_object(context)
        dprops = domain_object.flip_fluid.domain
        cprops = dprops.cache
        show_advanced = not vcu.get_addon_preferences(context).beginner_friendly_mode
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Cache Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Domain-Cache-Settings"
            column.operator(
                "wm.url_open", 
                text="Exporting to Alemibc (.abc) cache", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Alembic-Export-Support"

        column = self.layout.column(align=True)
        column.label(text="Current Cache Directory:")
        subcolumn = column.column(align=True)
        subcolumn.enabled = not dprops.bake.is_simulation_running
        row = subcolumn.row(align=True)
        row.prop(cprops, "cache_directory")
        row.operator("flip_fluid_operators.increment_decrease_cache_directory", text="", icon="REMOVE").increment_mode = "DECREASE"
        row.operator("flip_fluid_operators.increment_decrease_cache_directory", text="", icon="ADD").increment_mode = "INCREASE"

        row = column.row(align=True)
        row.operator("flip_fluid_operators.relative_cache_directory")
        row.operator("flip_fluid_operators.absolute_cache_directory")
        row.operator("flip_fluid_operators.match_filename_cache_directory")
        column.separator()

        if not show_advanced:
            return

        column = self.layout.column(align=True)
        column.label(text="Link existing exported geometry:")
        subcolumn = column.column(align=True)
        subcolumn.enabled = not dprops.bake.is_simulation_running
        subcolumn.prop(cprops, "linked_geometry_directory")
        row = column.row(align=True)
        row.operator("flip_fluid_operators.relative_linked_geometry_directory")
        row.operator("flip_fluid_operators.absolute_linked_geometry_directory")
        column = column.column(align=True)
        column.operator("flip_fluid_operators.clear_linked_geometry_directory")
        column.separator()

        column = self.layout.column(align=True)
        column.label(text="Cache Operators:")

        # The move, rename, and copy cache operations should not be performed
        # in Blender and are removed from the UI. There is a potential for Blender 
        # to crash, which could lead to loss of data. It is best to perform these 
        # operations through the OS filesystem which is cabable of handling failures.
        """
        row = column.row(align=True)
        row.operator("flip_fluid_operators.move_cache", text="Move")
        row.prop(cprops, "move_cache_directory")

        row = column.row(align=True)
        row.operator("flip_fluid_operators.rename_cache", text="Rename")
        row.prop(cprops, "rename_cache_directory")

        row = column.row(align=True)
        row.operator("flip_fluid_operators.copy_cache", text="Copy")
        row.prop(cprops, "copy_cache_directory")
        """

        if dprops.stats.is_cache_info_available:
            free_text = "Free (" + self.format_bytes(dprops.stats.cache_bytes.get()) + ")"
        else:
            free_text = "Free"

        split = column.split(align=True)
        column_left = split.column(align=True)
        column_right = split.column(align=True)
        column_left.operator("flip_fluid_operators.free_cache", text=free_text)
        column_right.prop(cprops, "clear_cache_directory_logs", text="Free log files")
        column_right.prop(cprops, "clear_cache_directory_export", text="Free export files")
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeCachePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeCachePanel)
