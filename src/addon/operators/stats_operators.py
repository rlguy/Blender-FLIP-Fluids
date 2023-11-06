# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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

from . import bake_operators


class FlipFluidRefreshStats(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.refresh_stats"
    bl_label = "Refresh Stats"
    bl_description = "Refresh and update the cache and frame stats"
    bl_options = {'REGISTER'}


    @classmethod
    def poll(csl, context):
        return True


    def execute(self, context):
        num_updated_frames = bake_operators.update_stats()
        self.report({'INFO'}, "Cache and frame stats have been refreshed. Found (" + str(num_updated_frames) + ") new frames.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidRefreshStats)


def unregister():
    bpy.utils.unregister_class(FlipFluidRefreshStats)
