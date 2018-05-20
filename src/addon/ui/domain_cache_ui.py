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

import bpy, math


class FlipFluidDomainTypeCachePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Cache"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
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
        domain_object = context.scene.objects.active
        dprops = domain_object.flip_fluid.domain
        cprops = dprops.cache

        column = self.layout.column(align=True)
        column.label("Current Cache Directory:")
        subcolumn = column.column(align=True)
        subcolumn.enabled = not dprops.bake.is_simulation_running
        subcolumn.prop(cprops, "cache_directory")
        row = column.row(align=True)
        row.operator("flip_fluid_operators.relative_cache_directory")
        row.operator("flip_fluid_operators.absolute_cache_directory")
        column.separator()

        column = self.layout.column(align=True)
        column.label("Cache Operators:")
        row = column.row(align=True)
        row.operator("flip_fluid_operators.move_cache", text="Move")
        row.prop(cprops, "move_cache_directory")

        row = column.row(align=True)
        row.operator("flip_fluid_operators.rename_cache", text="Rename")
        row.prop(cprops, "rename_cache_directory")

        row = column.row(align=True)
        row.operator("flip_fluid_operators.copy_cache", text="Copy")
        row.prop(cprops, "copy_cache_directory")

        if dprops.stats.is_cache_info_available:
            free_text = "Free (" + self.format_bytes(dprops.stats.cache_bytes.get()) + ")"
        else:
            free_text = "Free"

        row = column.row(align = True)
        row.operator("flip_fluid_operators.free_cache", text = free_text)
        row.prop(cprops, "clear_cache_directory_logs")
    

def register():
    bpy.utils.register_class(FlipFluidDomainTypeCachePanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeCachePanel)
