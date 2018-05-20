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
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import types
from ..objects.flip_fluid_aabb import AABB


class DomainSimulationProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.settings_export_mode = EnumProperty(
                name="Settings Export Mode",
                description="How the simulator will behave when exporting settings",
                items=types.export_modes,
                default='EXPORT_DEFAULT',
                options = {'HIDDEN'},
                )
        cls.resolution = IntProperty(
                name="Resolution",
                description="Domain resolution",
                min =1,
                default=65,
                update=lambda self, context: self._update_resolution(context),
                options={'HIDDEN'},
        )
        cls.preview_resolution = IntProperty(
                name="Preview Resolution",
                description="Preview resolution",
                min=1, soft_max=150,
                default=45,
                update=lambda self, context: self._update_preview_resolution(context),
                options={'HIDDEN'},
                )
        cls.lock_cell_size = BoolProperty(
                name="Lock Cell Size",
                description="Lock the current grid cell size and update the grid"
                    " resolution as the domain dimensions are changed",
                default=False,
                update=lambda self, context: self._update_lock_cell_size(context),
                options = {'HIDDEN'},
                )
        cls.start_time = bpy.props.FloatProperty(
                name="Start Time", 
                description="Simulation time of the first blender frame (in seconds)", 
                min=0.0,
                default=0.0,
                precision=3,
                update=lambda self, context: self._update_start_time(context),
                options={'HIDDEN'},
                )
        cls.end_time = bpy.props.FloatProperty(
                name="End Time", 
                description="Simulation time of the last blender frame (in seconds)", 
                min=0.0,
                default=4.0,
                precision=3,
                update=lambda self, context: self._update_end_time(context),
                options = {'HIDDEN'},
                )
        cls.use_fps = BoolProperty(
                name="Use Frame Rate",
                description="Calculate simulation time using rate of frames per second",
                default=True,
                update=lambda self, context: self._update_use_fps(context),
                options={'HIDDEN'},
                )
        cls.frames_per_second = FloatProperty(
                name="Frame Rate", 
                description="Frames per second", 
                min=0.001,
                default=60.0,
                precision=1,
                update=lambda self, context: self._update_frames_per_second(context),
                )
        cls.time_scale = FloatProperty(
                name="Speed", 
                description="Fluid motion rate (0 = stationary, 1 = normal speed)", 
                min=0.0,
                default=1.0,
                precision=3,
                )
        

        cls.locked_cell_size = FloatProperty(default=-1.0)
        cls.frame_start = IntProperty(default=-1)
        cls.frame_end = IntProperty(default=-1)


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".settings_export_mode", "Settings Export Mode", group_id=0)
        add(path + ".resolution",           "Resolution",           group_id=0)
        add(path + ".preview_resolution",   "Preview Resolution",   group_id=0)
        add(path + ".lock_cell_size",       "Lock Cell Size",       group_id=0)
        add(path + ".start_time",           "Start Time",           group_id=0)
        add(path + ".end_time",             "End Time",             group_id=0)
        add(path + ".use_fps",              "Use FPS",              group_id=0)
        add(path + ".frames_per_second",    "Frame Rate",           group_id=0)
        add(path + ".time_scale",           "Time Scale",           group_id=0)


    def initialize(self):
        self.frames_per_second = bpy.context.scene.render.fps
        num_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
        duration = num_frames / self.frames_per_second
        self.start_time = 0.0
        self.end_time = duration


    def scene_update_post(self, scene):
        self._update_locked_cell_size_resolution()
        self._update_start_end_time()


    def _update_resolution(self, context):
        if self.preview_resolution > self.resolution:
            self.preview_resolution = self.resolution


    def _update_preview_resolution(self, context):
        self._update_resolution(context)


    def _update_lock_cell_size(self, context):
        if self.lock_cell_size:
            domain_object = context.scene.flip_fluid.get_domain_object()
            bbox = AABB.from_blender_object(domain_object)
            max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
            self.locked_cell_size = max(max_dim / self.resolution, 1e-6)
        else:
            self.locked_cell_size = -1.0


    def _update_locked_cell_size_resolution(self):
        domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        if domain_object is None:
            return
        if not self.lock_cell_size:
            return
        bbox = AABB.from_blender_object(domain_object)
        max_dim = max(bbox.xdim, bbox.ydim, bbox.zdim)
        ratio = max_dim / self.locked_cell_size
        if abs(ratio - math.floor(ratio + 0.5)) < 1e-6:
            ratio = math.floor(ratio + 0.5)
        resolution = math.ceil(ratio)
        if self.resolution != resolution:
            self.resolution = resolution


    def _update_start_time(self, context):
        if self.start_time > self.end_time:
            self.end_time = self.start_time


    def _update_end_time(self, context):
        if self.end_time < self.start_time:
            self.start_time = self.end_time


    def _update_start_end_time(self):
        if self.use_fps:
            num_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
            duration = num_frames / self.frames_per_second
            eps = 1e-4
            if abs(self.start_time - 0.0) > eps:
                self.start_time = 0.0
            if abs(self.end_time - duration) > eps:
                self.end_time = duration


    def _update_use_fps(self, context):
        if self.use_fps:
            num_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
            duration = num_frames / self.frames_per_second
            self.start_time = 0.0
            self.end_time = duration


    def _update_frames_per_second(self, context):
        num_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
        duration = num_frames / self.frames_per_second
        self.start_time = 0.0
        self.end_time = duration


def register():
    bpy.utils.register_class(DomainSimulationProperties)


def unregister():
    bpy.utils.unregister_class(DomainSimulationProperties)