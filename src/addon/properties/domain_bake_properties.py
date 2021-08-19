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
from ..utils import version_compatibility_utils as vcu

SAVESTATE_ENUMS = []
IS_SAVESTATE_ENUMS_INITIALIZED = False


class DomainBakeProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    is_export_operator_running = BoolProperty(default=False); exec(conv("is_export_operator_running"))
    is_export_operator_cancelled = BoolProperty(default=False); exec(conv("is_export_operator_cancelled"))
    export_progress = FloatProperty(default=0.0); exec(conv("export_progress"))
    export_stage = StringProperty(default=""); exec(conv("export_stage"))

    export_filename = StringProperty(default='flipdata.sim'); exec(conv("export_filename"))
    export_directory_name = StringProperty(default='export'); exec(conv("export_directory_name"))
    export_filepath = StringProperty(default=""); exec(conv("export_filepath"))
    export_success = BoolProperty(default=False); exec(conv("export_success"))

    is_simulation_running = BoolProperty(default=False); exec(conv("is_simulation_running"))
    bake_progress = FloatProperty(default=0.0); exec(conv("bake_progress"))
    is_bake_initialized = BoolProperty(default=False); exec(conv("is_bake_initialized"))
    is_bake_cancelled = BoolProperty(default=False); exec(conv("is_bake_cancelled"))
    num_baked_frames = IntProperty(default=0); exec(conv("num_baked_frames"))

    is_autosave_available = BoolProperty(default=False); exec(conv("is_autosave_available"))
    is_autosave_last_frame = BoolProperty(default=False); exec(conv("is_autosave_last_frame"))
    is_safe_to_exit = BoolProperty(default=False); exec(conv("is_safe_to_exit"))
    autosave_frame_id = IntProperty(default=-1); exec(conv("autosave_frame_id"))
    autosave_frame = IntProperty(default=-1); exec(conv("autosave_frame"))

    original_frame_start = IntProperty(
            name="Start Frame",
            description="First frame of the simulation cache. Cannot be changed"
                " after beginning a simulation",
            default=-1,
            options={'HIDDEN'},
    ); exec(conv("original_frame_start"))


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

        try:
            with open(autosave_info_file, 'r', encoding='utf-8') as f:
                autosave_info = json.loads(f.read())
        except:
            # Autosave file might not be completely written. Wait and try again.
            import time
            time.sleep(0.25)
            try:
                with open(autosave_info_file, 'r', encoding='utf-8') as f:
                    autosave_info = json.loads(f.read())
            except:
                # skip this autosave frame if it still cannot be read. The autosave
                # should be able to be reinitialized when reloading the .blend file.
                return

        self.is_autosave_available = True
        self.autosave_frame_id = autosave_info['frame_id']
        self.autosave_frame = autosave_info['frame']
        self.is_autosave_last_frame = autosave_info['frame_id'] == autosave_info['last_frame_id']
        self.original_frame_start = autosave_info['frame_start']

        self._update_savestate_enums()


    def frame_complete_callback(self):
        self.check_autosave()


    def get_savestate_enums(self):
        global SAVESTATE_ENUMS
        global IS_SAVESTATE_ENUMS_INITIALIZED
        if not IS_SAVESTATE_ENUMS_INITIALIZED:
            self._update_savestate_enums()
        return SAVESTATE_ENUMS


    def _check_properties_valid(self):
        if self.is_simulation_running:
            self.is_simulation_running = False
        if self.is_bake_initialized:
            self.is_bake_initialize = False
        if self.is_bake_cancelled:
            self.is_bake_cancelled = False

    def _update_savestate_enums(self):
        global SAVESTATE_ENUMS
        global IS_SAVESTATE_ENUMS_INITIALIZED
        SAVESTATE_ENUMS = []
        IS_SAVESTATE_ENUMS_INITIALIZED = True

        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        savestates_directory = os.path.join(cache_directory, "savestates")
        subdirs = [d for d in os.listdir(savestates_directory) if os.path.isdir(os.path.join(savestates_directory, d))]
        if "autosave" in subdirs:
            subdirs.remove("autosave")
        autosave_frame = self.autosave_frame

        savestate_frames = []
        for d in subdirs:
            try:
                savestate_frames.append(int(d[-6:]))
            except:
                pass

        if autosave_frame in savestate_frames:
            savestate_frames.remove(autosave_frame)

        for frameno in savestate_frames:
            name ="Resume from frame " + str(frameno + 1)
            if frameno > autosave_frame:
                name += " (outdated)"
            e = (str(frameno), name, "")
            SAVESTATE_ENUMS.append(e)
        e = (str(autosave_frame), "Resume from frame " + str(autosave_frame + 1) + " (most recent)", "")
        SAVESTATE_ENUMS.append(e)

        try:
            dprops.simulation.selected_savestate = str(autosave_frame)
        except:
            pass


def register():
    bpy.utils.register_class(DomainBakeProperties)


def unregister():
    bpy.utils.unregister_class(DomainBakeProperties)