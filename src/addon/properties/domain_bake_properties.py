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

import bpy, os, json
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import types


class DomainBakeProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.is_export_operator_running = BoolProperty(default=False)
        cls.is_export_operator_cancelled = BoolProperty(default=False)
        cls.export_progress = FloatProperty(default=0.0)
        cls.export_stage = StringProperty(default="")
        cls.export_filename = StringProperty(default='flipdata.sim')
        cls.export_filepath = StringProperty(default="")
        cls.export_success = BoolProperty(default=False)

        cls.is_simulation_running = BoolProperty(default=False)
        cls.bake_progress = FloatProperty(default=0.0)
        cls.is_bake_initialized = BoolProperty(default=False)
        cls.is_bake_cancelled = BoolProperty(default=False)
        cls.num_baked_frames = IntProperty(default=0)

        cls.is_autosave_available = BoolProperty(default=False)
        cls.is_autosave_last_frame = BoolProperty(default=False)
        cls.is_safe_to_exit = BoolProperty(default=False)
        cls.autosave_frame_id = IntProperty(default=-1)
        cls.autosave_frame = IntProperty(default=-1)


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        pass


    def load_post(self):
        self._check_properties_valid()
        self.check_autosave()


    def check_autosave(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        cache_directory = dprops.cache.get_cache_abspath()
        autosave_directory = os.path.join(cache_directory, "savestates", "autosave")

        if not os.path.isdir(autosave_directory):
            self.is_autosave_available = False
            return

        autosave_info_file = os.path.join(autosave_directory, "autosave.state")
        if not os.path.isfile(autosave_info_file):
            self.is_autosave_available = False
            return

        with open(autosave_info_file, 'r') as f:
            autosave_info = json.loads(f.read())

        self.is_autosave_available = True
        self.autosave_frame_id = autosave_info['frame_id']
        self.autosave_frame = autosave_info['frame']
        self.is_autosave_last_frame = autosave_info['frame_id'] == autosave_info['last_frame_id']


    def _check_properties_valid(self):
        if self.is_simulation_running:
            self.is_simulation_running = False
        if self.is_bake_initialized:
            self.is_bake_initialize = False
        if self.is_bake_cancelled:
            self.is_bake_cancelled = False


def register():
    bpy.utils.register_class(DomainBakeProperties)


def unregister():
    bpy.utils.unregister_class(DomainBakeProperties)