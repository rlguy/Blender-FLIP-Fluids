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

import bpy, math, os, json
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .custom_properties import (
        NewMinMaxIntProperty,
        )

from .. import types
from ..objects.flip_fluid_aabb import AABB
from ..utils import version_compatibility_utils as vcu
from ..utils import export_utils


class DomainSimulationProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28

    frame_range_mode = EnumProperty(
            name="Frame Range Mode",
            description="Frame range to use for baking the simulation",
            items=types.frame_range_modes,
            default='FRAME_RANGE_TIMELINE',
            options={'HIDDEN'},
            ); exec(conv("frame_range_mode"))
    frame_range_custom = NewMinMaxIntProperty(
            name_min="Start Frame", 
            description_min="First frame of the simulation cache", 
            min_min=0,
            default_min=1,
            options_min={'HIDDEN'},

            name_max="End Frame", 
            description_max="Final frame of the simulation cache", 
            min_max=0,
            default_max=250,
            options_max={'HIDDEN'},
            ); exec(conv("frame_range_custom"))
    update_settings_on_resume = BoolProperty(
            name="Update Settings on Resume",
            description="Update simulation settings and meshes when resuming a bake."
                " If disabled, the simulator will use the original settings and meshes"
                " from when the bake was started",
            default=True,
            options={'HIDDEN'},
            ); exec(conv("update_settings_on_resume"))
    mesh_reexport_type_filter = EnumProperty(
            name="Object Motion Type",
            description="Filter objects by motion type for skip re-export list display",
            items=types.motion_filter_types,
            default='MOTION_FILTER_TYPE_ANIMATED',
            ); exec(conv("mesh_reexport_type_filter"))
    enable_savestates = BoolProperty(
            name="Enable Savestates",
            description="Generate savestates/checkpoints as the simulation progresses."
                " Savestates will allow you to rollback the simulation to an earlier"
                " point so that you can re-simulate from a previous frame",
            default=True,
            options = {'HIDDEN'},
            ); exec(conv("enable_savestates"))
    savestate_interval = IntProperty(
            name="Savestate Interval",
            description="Number of frames between each savestate",
            min=1,
            default=50,
            options={'HIDDEN'},
            ); exec(conv("savestate_interval"))
    delete_outdated_savestates = BoolProperty(
            name="Delete Outdated Savestates on Resume",
            description="When resuming a simulation from a previous frame, delete"
                " all savestates that are ahead in the timeline",
            default=True,
            options = {'HIDDEN'},
            ); exec(conv("delete_outdated_savestates"))
    delete_outdated_meshes = BoolProperty(
            name="Delete Outdated Meshes on Resume",
            description="When resuming a simulation from a previous frame, delete"
                " all simulation meshes that are ahead in the timeline",
            default=True,
            options = {'HIDDEN'},
            ); exec(conv("delete_outdated_meshes"))
    selected_savestate = EnumProperty(
            name="Selected Savestate",
            description="Resume simulation from this savestate frame",
            update=lambda self, context: self._update_selected_savestate(context),
            items=lambda self, context: self._get_savestate_enums(context),
            ); exec(conv("selected_savestate"))
    selected_savestate_int = IntProperty(
            name="Selected Savestate",
            description="Resume simulation from this savestate frame",
            update=lambda self, context: self._update_selected_savestate_int(context),
            options={'HIDDEN'},
            ); exec(conv("selected_savestate_int"))
    resolution = IntProperty(
            name="Resolution",
            description="Domain grid resolution. This value specifies the number of"
                " grid voxels on the longest side of the domain. See the tooltips in"
                " the Grid Info section below for a detailed explanation of the domain grid",
            min=10,
            default=65,
            update=lambda self, context: self._update_resolution(context),
            options={'HIDDEN'},
            ); exec(conv("resolution"))
    preview_resolution = IntProperty(
            name="Preview Resolution",
            description="The resolution to use for generating lower quality meshes for"
                " the preview fluid surface. Increasing this value will take no extra time"
                " to simulate, but will increase cache size",
            min=1, soft_max=150,
            default=45,
            update=lambda self, context: self._update_preview_resolution(context),
            options={'HIDDEN'},
            ); exec(conv("preview_resolution"))
    auto_preview_resolution = BoolProperty(
            name="Recommended",
            description="Set recommended preview resolution based on domain resolution and"
                " mesh generation settings",
            default=True,
            update=lambda self, context: self._update_auto_preview_resolution(context),
            options={'HIDDEN'},
            ); exec(conv("auto_preview_resolution"))
    lock_cell_size = BoolProperty(
            name="Lock Cell Size",
            description="Lock the current grid cell size and update the grid"
                " resolution as the domain dimensions are changed. Enable this"
                " option before resizing the domain to maintain a constant level"
                " of simulation detail",
            default=False,
            update=lambda self, context: self._update_lock_cell_size(context),
            options = {'HIDDEN'},
            ); exec(conv("lock_cell_size"))
    frame_rate_mode = EnumProperty(
            name="Frame Rate Mode",
            description="Select the frame rate for the simulation animation",
            items=types.frame_rate_modes,
            default='FRAME_RATE_MODE_SCENE',
            options={'HIDDEN'},
            ); exec(conv("frame_rate_mode"))
    frame_rate_custom = FloatProperty(
            name="Frame Rate", 
            description="Frame rate in frames per second", 
            min=0.001,
            default=60.0,
            precision=1,
            ); exec(conv("frame_rate_custom"))
    time_scale = FloatProperty(
            name="Speed", 
            description="Scale the frame timestep by this value. If set to less than"
                " 1.0, the simulation will appear in slow motion. If set to greater than"
                " 1.0, the simulation will appear sped up", 
            min=0.0,
            default=1.0,
            precision=3,
            ); exec(conv("time_scale"))
    
    locked_cell_size = FloatProperty(default=-1.0); exec(conv("locked_cell_size"))
    frame_start = IntProperty(default=-1); exec(conv("frame_start"))
    frame_end = IntProperty(default=-1); exec(conv("frame_end"))

    more_bake_settings_expanded = BoolProperty(default=False); exec(conv("more_bake_settings_expanded"))
    skip_mesh_reexport_expanded = BoolProperty(default=False); exec(conv("skip_mesh_reexport_expanded"))
    grid_info_expanded = BoolProperty(default=True); exec(conv("grid_info_expanded"))
    last_selected_savestate_int = IntProperty(default=-1); exec(conv("last_selected_savestate_int"))
    selected_savestate_int_label = StringProperty(default=""); exec(conv("selected_savestate_int_label"))

    current_isize = IntProperty(default=-1); exec(conv("current_isize"))
    current_jsize = IntProperty(default=-1); exec(conv("current_jsize"))
    current_ksize = IntProperty(default=-1); exec(conv("current_ksize"))
    current_dx = FloatProperty(default=-1.0); exec(conv("current_dx"))

    savestate_isize = IntProperty(default=-1); exec(conv("savestate_isize"))
    savestate_jsize = IntProperty(default=-1); exec(conv("savestate_jsize"))
    savestate_ksize = IntProperty(default=-1); exec(conv("savestate_ksize"))
    savestate_dx = FloatProperty(default=-1.0); exec(conv("savestate_dx"))

    upscale_trigger_factor = FloatProperty(default=0.05); exec(conv("upscale_trigger_factor"))

    upscale_resolution_tooltip = BoolProperty(
            name="Upscale Resolution Tooltip", 
            description="Upscaling converts a lower resolution savestate to a higher resolution savestate"
                " so that the simulation can resume baking at the increased resolution", 
            default=True,
            ); exec(conv("upscale_resolution_tooltip"))

    grid_voxels_tooltip = BoolProperty(
            name="Grid Voxels Tooltip", 
            description="The domain is a 3D grid of cubes called voxels, or cells. This info shows the"
            " number of voxels on each of the X/Y/Z axis of the domain. The voxels in the 3D grid are"
            " similar to the 2D pixels in a 2D image, except instead of storing color data, the voxels store"
            " physics data", 
            default=True,
            ); exec(conv("grid_voxels_tooltip"))

    grid_dimensions_tooltip = BoolProperty(
            name="Grid Dimensions Tooltip", 
            description="Displays the physical scale of the domain on the X/Y/Z axis in meters."
            " Setting an appropriate scale can be an important factor for realistic motion and speed"
            " of your simulated fluid", 
            default=True,
            ); exec(conv("grid_dimensions_tooltip"))

    grid_voxel_size_tooltip = BoolProperty(
            name="Voxel Size Tooltip", 
            description="Displays the physical size of a single voxel. You can think of a voxel as"
            " the 3D version of a 2D image pixel. In an image, the pixel size is the minimum"
            " amount of detail that can be resolved in the picture. In the domain, the voxel size is"
            " the minimum amount of physics detail that can be resolved in the simulation such as the"
            " smallest droplets and ripples or the thinnest splashes", 
            default=True,
            ); exec(conv("grid_voxel_size_tooltip"))

    grid_voxel_count_tooltip = BoolProperty(
            name="Voxel Count Tooltip", 
            description="Displays the total number of voxels in the domain. Physics are computed for each"
            " voxel and the total count can be a measure for how much work your system will be doing."
            " Small simulation = around 2 Million. Medium = around 10M. Large = around 40M."
            " Very Large = over 80M", 
            default=True,
            ); exec(conv("grid_voxel_count_tooltip"))


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".resolution",              "Resolution",              group_id=0)
        add(path + ".preview_resolution",      "Preview Resolution",      group_id=0)
        add(path + ".auto_preview_resolution", "Auto Preview Resolution", group_id=0)
        add(path + ".lock_cell_size",          "Lock Cell Size",          group_id=0)
        add(path + ".frame_rate_mode",         "Frame Rate Mode",         group_id=0)
        add(path + ".frame_rate_custom",       "Frame Rate",              group_id=0)
        add(path + ".time_scale",              "Time Scale",              group_id=0)

        add(path + ".frame_range_mode",           "Frame Range Mode",           group_id=1)
        add(path + ".frame_range_custom",         "Frame Range (Custom)",       group_id=1)
        add(path + ".update_settings_on_resume",  "Update Settings on Resume",  group_id=1)
        add(path + ".enable_savestates",          "Enable Savestates",          group_id=1)
        add(path + ".savestate_interval",         "Savestate Interval",         group_id=1)
        add(path + ".delete_outdated_savestates", "Delete Outdated Savestates", group_id=1)
        add(path + ".delete_outdated_meshes",     "Delete Outdated Meshes",     group_id=1)


    def initialize(self):
        self.frame_rate_custom = bpy.context.scene.render.fps


    def load_post(self):
        self._update_current_settings_grid_dimensions()


    def scene_update_post(self, scene):
        if self.grid_info_expanded:
            # Workaround to get UI panel to redraw when grid info is displayed
            self.resolution = self.resolution

        self._update_locked_cell_size_resolution()
        self._set_recommended_preview_resolution()
        self._update_current_settings_grid_dimensions()


    # World scale is not applied to dx, which will match dimensions within viewport
    def get_viewport_grid_dimensions(self, resolution=None, lock_cell_size=None):
        domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None or resolution == 0:
            return 1, 1, 1, 1.0

        if lock_cell_size is None:
            lock_cell_size = self.lock_cell_size
        if resolution is None:
            resolution = self.resolution
        else:
            lock_cell_size = False

        domain_bbox = AABB.from_blender_object(domain_object)
        max_dim = max(domain_bbox.xdim, domain_bbox.ydim, domain_bbox.zdim)
        if lock_cell_size:
            unlocked_dx = max_dim / resolution
            locked_dx = self.locked_cell_size
            dx = locked_dx
            if abs(locked_dx - unlocked_dx) < 1e-6:
                dx = unlocked_dx
        else:
            dx = max_dim / resolution

        precision = 5
        isize = math.ceil(round(domain_bbox.xdim / dx, precision))
        jsize = math.ceil(round(domain_bbox.ydim / dx, precision))
        ksize = math.ceil(round(domain_bbox.zdim / dx, precision))

        return isize, jsize, ksize, dx


    # World scale will be applied to dx, which will match dimensions within the simulation
    def get_simulation_grid_dimensions(self, resolution=None, lock_cell_size=None):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        isize, jsize, ksize, dx = self.get_viewport_grid_dimensions(resolution, lock_cell_size)
        dx *= dprops.world.get_world_scale()
        return isize, jsize, ksize, dx


    def get_viewport_preview_dx(self):
        domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return 1.0
        domain_bbox = AABB.from_blender_object(domain_object)
        max_dim = max(domain_bbox.xdim, domain_bbox.ydim, domain_bbox.zdim)
        return max_dim / self.preview_resolution


    def get_simulation_preview_dx(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        preview_dx = self.get_viewport_preview_dx()
        return preview_dx * dprops.world.get_world_scale()


    def get_frame_range(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if self.frame_range_mode == 'FRAME_RANGE_TIMELINE':
            frame_start = bpy.context.scene.frame_start
            if dprops.bake.is_autosave_available:
                frame_start = dprops.bake.original_frame_start
            return frame_start, bpy.context.scene.frame_end
        else:
            frame_start = self.frame_range_custom.value_min
            if dprops.bake.is_autosave_available:
                frame_start = dprops.bake.original_frame_start
            return frame_start, self.frame_range_custom.value_max


    def get_selected_savestate_id(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        savestate_id = None
        if dprops.bake.is_autosave_available:
            if self.enable_savestates:
                savestate_id = int(self.selected_savestate)
            else:
                return dprops.bake.autosave_frame
        return savestate_id


    def get_num_savestate_enums(self):
        return len(self._get_savestate_enums())


    def get_frame_rate(self):
        if self.frame_rate_mode == 'FRAME_RATE_MODE_SCENE':
            return bpy.context.scene.render.fps
        elif self.frame_rate_mode == 'FRAME_RATE_MODE_CUSTOM':
            return self.frame_rate_custom


    def get_frame_rate_data_dict(self):
        if self.frame_rate_mode == 'FRAME_RATE_MODE_SCENE':
            prop_group = bpy.context.scene.render
            return export_utils.get_property_data_dict(bpy.context.scene, prop_group, 'fps')
        elif self.frame_rate_mode == 'FRAME_RATE_MODE_CUSTOM':
            domain_object = bpy.context.scene.flip_fluid.get_domain_object()
            return export_utils.get_property_data_dict(domain_object, self, 'frame_rate_custom')


    def is_current_grid_upscaled(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if not dprops.bake.is_autosave_available:
            return False
        if self.savestate_isize <= 0 or self.savestate_jsize <= 0 or self.savestate_ksize <= 0 or self.savestate_dx <= 0.0:
            return False
        if self.current_isize <= 0 or self.current_jsize <= 0 or self.current_ksize <= 0 or self.current_dx <= 0.0:
            return False
        if self.current_dx > self.savestate_dx:
            # downscaled
            return False

        res_changed = (self.current_isize != self.savestate_isize or 
                        self.current_jsize != self.savestate_jsize or 
                        self.current_ksize != self.savestate_ksize)

        dx_eps = self.upscale_trigger_factor * self.savestate_dx
        dx_changed = abs(self.current_dx - self.savestate_dx) > dx_eps
        return res_changed and dx_changed


    def _update_resolution(self, context):
        self._set_recommended_preview_resolution(context)
        if self.preview_resolution > self.resolution:
            self.preview_resolution = self.resolution
        self._update_current_settings_grid_dimensions()


    def _update_preview_resolution(self, context):
        self._update_resolution(context)


    def _update_auto_preview_resolution(self, context):
        self._set_recommended_preview_resolution(context)


    def _set_recommended_preview_resolution(self, context=None):
        if not self.auto_preview_resolution:
            return
        if context is None:
            context = bpy.context
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops.surface.subdivisions > 1:
            preview = self.resolution
        else:
            preview = self.resolution // 2
        if self.preview_resolution != preview:
            self.preview_resolution = preview


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


    def _get_savestate_enums(self, context=None):
        if context is None:
            context = bpy.context
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops.bake.get_savestate_enums()


    def _update_selected_savestate(self, context):
        self["selected_savestate_int"] = int(self.selected_savestate) + 1
        self.last_selected_savestate_int = self.selected_savestate_int

        self.selected_savestate_int_label = ""
        enums = self._get_savestate_enums()
        for e in enums:
            if e[0] == self.selected_savestate:
                label = e[1]
                if not label:
                    break
                idx1 = label.find("(")
                idx2 = label.find(")")
                if idx1 == -1 or idx2 == -1:
                    break
                self.selected_savestate_int_label = label[idx1:idx2+1]

        self._update_selected_savestate_grid_dimensions(context)


    def _update_selected_savestate_int(self, context):
        last_id = self.last_selected_savestate_int - 1
        next_id = self.selected_savestate_int - 1

        enums = self._get_savestate_enums()
        ids = [int(e[0]) for e in enums]
        ids.sort()

        if next_id in ids:
            next_valid_id = next_id
        else:
            if next_id == last_id + 1:
                next_valid_id = ids[min(ids.index(last_id) + 1, len(ids) - 1)]
            elif next_id == last_id - 1:
                next_valid_id = ids[max(ids.index(last_id) - 1, 0)]
            else:
                nearest_id = min(ids, key=lambda x:abs(x-next_id))
                next_valid_id = nearest_id

        self.selected_savestate = str(next_valid_id)
        self["selected_savestate_int"] = next_valid_id + 1

        self.last_selected_savestate_int = self.selected_savestate_int

        self._update_selected_savestate_grid_dimensions(context)


    def _update_current_settings_grid_dimensions(self):
        isize, jsize, ksize, dx = self.get_simulation_grid_dimensions()

        eps = 1e-6
        if self.current_isize != isize:
            self.current_isize = isize
        if self.current_jsize != jsize:
            self.current_jsize = jsize
        if self.current_ksize != ksize:
            self.current_ksize = ksize
        if abs(self.current_dx - dx) > eps:
            self.current_dx = dx


    def _update_selected_savestate_grid_dimensions(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops.bake.is_simulation_running:
            return

        savestate_id = self.get_selected_savestate_id()

        cache_directory = dprops.cache.get_cache_abspath()
        savestate_directory = os.path.join(cache_directory, "savestates")
        savestate_name = "autosave" + str(savestate_id).zfill(6)
        autosave_directory = os.path.join(savestate_directory, savestate_name)
        if not os.path.isdir(autosave_directory):
            autosave_directory = os.path.join(savestate_directory, "autosave")

        if not os.path.isdir(autosave_directory):
            return
        
        autosave_info_file = os.path.join(autosave_directory, "autosave.state")
        if not os.path.isfile(autosave_info_file):
            return

        with open(autosave_info_file, 'r', encoding='utf-8') as f:
            autosave_info = json.loads(f.read())

        try:
            isize = autosave_info["isize"]
            jsize = autosave_info["jsize"]
            ksize = autosave_info["ksize"]
            dx = autosave_info["dx"]
        except KeyError:
            # Cache created in older FLIP Fluids version which does not contain
            # this info. Fill in properties with the current grid dimension settings.
            isize, jsize, ksize, dx = self.get_simulation_grid_dimensions()

        eps = 1e-6
        if self.savestate_isize != isize:
            self.savestate_isize = isize
        if self.savestate_jsize != jsize:
            self.savestate_jsize = jsize
        if self.savestate_ksize != ksize:
            self.savestate_ksize = ksize
        if abs(self.savestate_dx - dx) > eps:
            self.savestate_dx = dx


def register():
    bpy.utils.register_class(DomainSimulationProperties)


def unregister():
    bpy.utils.unregister_class(DomainSimulationProperties)