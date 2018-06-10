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

import bpy, os, json, math, datetime
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .. import types

# ##############################################################################
#   STATS PROPERTIES
# ##############################################################################

class ByteProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.bytes = FloatProperty(
                default=-1.0, 
                get=lambda self: self._get_bytes(),
                set=lambda self, value: self._set_bytes(value),
                )


    @classmethod
    def unregister(cls):
        pass


    def get(self):
        return int(self.bytes)


    def set(self, value):
        self.bytes = value


    def _get_bytes(self):
        try: 
            return int(math.ceil(self["bytes"] * 1e4)) 
        except: 
            return 0


    def _set_bytes(self, value):
        self["bytes"] = value / 1e4


class MeshStatsProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.enabled = bpy.props.BoolProperty(default=False)
        cls.verts = bpy.props.IntProperty(default=-1)
        cls.faces = bpy.props.IntProperty(default=-1)
        cls.bytes = PointerProperty(type=ByteProperty)


    @classmethod
    def unregister(cls):
        pass


class TimeStatsProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.time = FloatProperty(
                default=-1.0, 
                precision = 1
                )
        cls.pct = FloatProperty(
                min=0, max=100,
                default=0.0, 
                precision = 1,
                subtype='PERCENTAGE',
                get=lambda self: self._get_time_pct(),
                set=lambda self, value: None,
                )


    @classmethod
    def unregister(cls):
        pass


    def set_time_pct(self, value):
        self["pct"] = value


    def _get_time_pct(self):
        try: 
            return self["pct"] 
        except: 
            return 0.0


class DomainStatsProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.cache_info_type = EnumProperty(
                name="Cache Info Display Mode",
                description="Type of cache info to display",
                items=types.cache_info_modes,
                default='CACHE_INFO',
                update=lambda self, context: self._update_cache_info_type(context),
                )
        cls.current_info_frame = IntProperty(
                name="Frame", 
                description="Select frame number", 
                min=0,
                default=0,
                update=lambda self, context: self._update_current_info_frame(context),
                )
        cls.lock_info_frame_to_timeline = BoolProperty(
                name="Lock To Timeline",
                description="Set frame number to current frame in timeline",
                default=True,
                update=lambda self, context: self._update_lock_info_frame_to_timeline(context),
                )
        temp_directory = bpy.context.user_preferences.filepaths.temporary_directory
        cls.csv_save_filepath = StringProperty(
                name="",
                default=os.path.join(temp_directory, "flip_fluid_stats.csv"), 
                subtype='FILE_PATH'
                )
        cls.csv_region_format = EnumProperty(
                name="Region Format",
                description="CSV region formatting",
                items=types.csv_regions,
                default='CSV_REGION_US',
                )

        cls.stats_filename = bpy.props.StringProperty(default='flipstats.data')
        cls.is_stats_current = bpy.props.BoolProperty(default=False)

        # Cache Info
        cls.cache_info_simulation_stats_expanded = BoolProperty(default=True)
        cls.cache_info_timing_stats_expanded = BoolProperty(default=True)
        cls.cache_info_mesh_stats_expanded = BoolProperty(default=True)
        cls.is_cache_info_available = BoolProperty(default=False)
        cls.num_cache_frames = IntProperty(default=-1)
        cls.estimated_frame_speed = FloatProperty(default=-1)
        cls.estimated_time_remaining = IntProperty(default=-1)
        cls.estimated_time_remaining_timestamp = IntProperty(default=-1)
        cls.is_estimated_time_remaining_available = BoolProperty(default=False)
        cls.cache_bytes = PointerProperty(type=ByteProperty)

        # Frame Info
        cls.frame_info_simulation_stats_expanded = BoolProperty(default=True)
        cls.frame_info_timing_stats_expanded = BoolProperty(default=True)
        cls.frame_info_mesh_stats_expanded = BoolProperty(default=True)
        cls.display_frame_viscosity_timing_stats = BoolProperty(default=False)
        cls.display_frame_diffuse_timing_stats = BoolProperty(default=False)
        cls.display_frame_diffuse_particle_stats = BoolProperty(default=False)
        cls.is_frame_info_available = bpy.props.BoolProperty(default=False)
        cls.frame_info_id = IntProperty(default=-1)
        cls.frame_substeps = IntProperty(default=-1)
        cls.frame_delta_time = FloatProperty(default=0.0)
        cls.frame_fluid_particles = IntProperty(default=-1)
        cls.frame_diffuse_particles = IntProperty(default=-1)

        # Mesh Info
        cls.surface_mesh = PointerProperty(type=MeshStatsProperties)
        cls.preview_mesh = PointerProperty(type=MeshStatsProperties)
        cls.foam_mesh = PointerProperty(type=MeshStatsProperties)
        cls.bubble_mesh = PointerProperty(type=MeshStatsProperties)
        cls.spray_mesh = PointerProperty(type=MeshStatsProperties)
        cls.particle_mesh = PointerProperty(type=MeshStatsProperties)
        cls.obstacle_mesh = PointerProperty(type=MeshStatsProperties)

        # Time Info
        cls.time_mesh = PointerProperty(type=TimeStatsProperties)
        cls.time_advection = PointerProperty(type=TimeStatsProperties)
        cls.time_particles = PointerProperty(type=TimeStatsProperties)
        cls.time_pressure = PointerProperty(type=TimeStatsProperties)
        cls.time_diffuse = PointerProperty(type=TimeStatsProperties)
        cls.time_viscosity = PointerProperty(type=TimeStatsProperties)
        cls.time_objects = PointerProperty(type=TimeStatsProperties)
        cls.time_other = PointerProperty(type=TimeStatsProperties)


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".cache_info_type",             "Info Type",              group_id=0)
        add(path + ".lock_info_frame_to_timeline", "Lock Frame to Timeline", group_id=0)
        add(path + ".csv_region_format",           "CSV Region Format",      group_id=0)


    def format_long_time(self, t):
        m, s = divmod(t, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def get_time_remaining_string(self, context):
        ret_str = ""
        if self.is_estimated_time_remaining_available:
            now = self.get_timestamp()
            dt = now - self.estimated_time_remaining_timestamp
            time_remaining = self.estimated_time_remaining - dt
            time_remaining = max(0, time_remaining)
            ret_str = self.format_long_time(time_remaining)
        return ret_str


    def reset_time_remaining(self):
        self.is_estimated_time_remaining_available = False


    def refresh_stats(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if not dprops:
            self.is_cache_info_available = False
            return

        cache_directory = dprops.cache.get_cache_abspath()
        statsfile = os.path.join(cache_directory, self.stats_filename)
        if not os.path.isfile(statsfile):
            self.is_cache_info_available = False
            return
        self.is_cache_info_available = True

        if self.cache_info_type == "FRAME_INFO":
            if self.lock_info_frame_to_timeline:
                self.current_info_frame = bpy.context.scene.frame_current
            else:
                self._update_frame_stats()
        elif self.cache_info_type == "CACHE_INFO":
            self._update_cache_stats()
        self.is_stats_current = True


    def scene_update_post(self, scene):
        if self.is_stats_current:
            return
        self.refresh_stats()


    def frame_change_pre(self, scene):
        if self.cache_info_type == "FRAME_INFO" and self.lock_info_frame_to_timeline:
            if self.current_info_frame != scene.frame_current:
                self.current_info_frame = scene.frame_current


    def load_post(self):
        self.refresh_stats()


    def get_timestamp(self):
        dt = datetime.datetime.now() - datetime.datetime.utcfromtimestamp(0)
        return int(dt.total_seconds())


    def _update_current_info_frame(self, context):
        self._update_frame_stats()


    def _update_cache_info_type(self, context):
        if self.cache_info_type == 'CACHE_INFO':
            self._update_cache_stats()
        elif self.cache_info_type == 'FRAME_INFO':
            if self.lock_info_frame_to_timeline:
                if self.current_info_frame != context.scene.frame_current:
                    self.current_info_frame = context.scene.frame_current
            self._update_frame_stats()


    def _update_lock_info_frame_to_timeline(self, context):
        if self.lock_info_frame_to_timeline:
            self.current_info_frame = context.scene.frame_current


    def _update_frame_stats(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        frameno = self.current_info_frame
        cache_directory = dprops.cache.get_cache_abspath()
        statsfile = os.path.join(cache_directory, self.stats_filename)
        if not os.path.isfile(statsfile):
            self.is_frame_info_available = False
            return

        with open(statsfile, 'r') as f:
            statsdata = json.loads(f.read())

        framekey = str(self.current_info_frame)
        if not framekey in statsdata:
            self.is_frame_info_available = False
            return

        data = statsdata[framekey]
        self.is_frame_info_available = True
        self.frame_info_id = data['frame']
        self.frame_substeps = data['substeps']
        self.frame_delta_time = data['delta_time']
        self.frame_fluid_particles = data['fluid_particles']
        self.frame_diffuse_particles = data['diffuse_particles']

        self._set_mesh_stats_data(self.surface_mesh,  data['surface'])
        self._set_mesh_stats_data(self.preview_mesh,  data['preview'])
        self._set_mesh_stats_data(self.foam_mesh,     data['foam'])
        self._set_mesh_stats_data(self.bubble_mesh,   data['bubble'])
        self._set_mesh_stats_data(self.spray_mesh,    data['spray'])
        self._set_mesh_stats_data(self.particle_mesh, data['particles'])
        self._set_mesh_stats_data(self.obstacle_mesh, data['obstacle'])

        total_time = max(data['timing']['total'], 1e-6)
        time_other = (total_time - data['timing']['mesh']
                                 - data['timing']['advection']
                                 - data['timing']['particles']
                                 - data['timing']['pressure']
                                 - data['timing']['diffuse']
                                 - data['timing']['viscosity']
                                 - data['timing']['objects'])
        time_other = max(0.0, time_other)

        self.time_mesh.set_time_pct(     100 * data['timing']['mesh']      / total_time)
        self.time_advection.set_time_pct(100 * data['timing']['advection'] / total_time)
        self.time_particles.set_time_pct(100 * data['timing']['particles'] / total_time)
        self.time_pressure.set_time_pct( 100 * data['timing']['pressure']  / total_time)
        self.time_diffuse.set_time_pct(  100 * data['timing']['diffuse']   / total_time)
        self.time_viscosity.set_time_pct(100 * data['timing']['viscosity'] / total_time)
        self.time_objects.set_time_pct(  100 * data['timing']['objects']   / total_time)
        self.time_other.set_time_pct(    100 * time_other                  / total_time)

        precision = 2
        self.time_mesh.time      = round(data['timing']['mesh'], precision)
        self.time_advection.time = round(data['timing']['advection'], precision)
        self.time_particles.time = round(data['timing']['particles'], precision)
        self.time_pressure.time  = round(data['timing']['pressure'], precision)
        self.time_diffuse.time   = round(data['timing']['diffuse'], precision)
        self.time_viscosity.time = round(data['timing']['viscosity'], precision)
        self.time_objects.time   = round(data['timing']['objects'], precision)
        self.time_other.time     = round(time_other, precision)

        self.display_frame_viscosity_timing_stats = False
        self.display_frame_diffuse_timing_stats = False
        self.display_frame_diffuse_particle_stats = False
        for key in statsdata.keys():
            if key.isdigit():
                if statsdata[key]['diffuse_particles'] > 0.0:
                    self.display_frame_diffuse_particle_stats = True
                    break
        for key in statsdata.keys():
            if key.isdigit():
                if statsdata[key]['timing']['viscosity'] > 0.0:
                    self.display_frame_viscosity_timing_stats = True
                    break
        for key in statsdata.keys():
            if key.isdigit():
                if statsdata[key]['timing']['diffuse'] > 0.0:
                    self.display_frame_diffuse_timing_stats = True
                    break

        self._update_cache_size(statsdata)


    def _set_mesh_stats_data(self, mesh_stats, mesh_stats_dict):
        mesh_stats.enabled = mesh_stats_dict['enabled']
        mesh_stats.verts   = mesh_stats_dict['vertices']
        mesh_stats.faces   = mesh_stats_dict['triangles']
        mesh_stats.bytes.set(mesh_stats_dict['bytes'])


    def _update_cache_size(self, cachedata):
        cache_size = 0
        for key in cachedata.keys():
            if not key.isdigit():
                continue
            fdata = cachedata[key]
            if fdata['surface']['enabled']:
                cache_size += fdata['surface']['bytes']
            if fdata['preview']['enabled']:
                cache_size += fdata['preview']['bytes']
            if fdata['foam']['enabled']:
                cache_size += fdata['foam']['bytes']
            if fdata['bubble']['enabled']:
                cache_size += fdata['bubble']['bytes']
            if fdata['spray']['enabled']:
                cache_size += fdata['spray']['bytes']
            if fdata['particles']['enabled']:
                cache_size += fdata['particles']['bytes']
            if fdata['obstacle']['enabled']:
                cache_size += fdata['obstacle']['bytes']
        self.cache_bytes.set(cache_size)


    def _update_cache_stats(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        cache_directory = dprops.cache.get_cache_abspath()
        statsfile = os.path.join(cache_directory, self.stats_filename)
        if not os.path.isfile(statsfile):
            self.is_frame_info_available = False
            return

        with open(statsfile, 'r') as f:
            cachedata = json.loads(f.read())

        self.is_cache_info_available = True

        is_surface_enabled = False
        is_preview_enabled = False
        is_foam_enabled = False
        is_bubble_enabled = False
        is_spray_enabled = False
        is_particles_enabled = False
        is_obstacle_enabled = False
        surface_bytes = 0
        preview_bytes = 0
        foam_bytes = 0
        bubble_bytes = 0
        spray_bytes = 0
        particles_bytes = 0
        obstacle_bytes = 0

        total_time = 0.0
        time_mesh = 0.0
        time_advection = 0.0
        time_particles = 0.0
        time_pressure = 0.0
        time_diffuse = 0.0
        time_viscosity = 0.0
        time_objects = 0.0
        time_other = 0.0
        is_data_in_cache = False
        num_cache_frames = 0
        for key in cachedata.keys():
            if not key.isdigit():
                continue

            is_data_in_cache = True
            num_cache_frames += 1

            fdata = cachedata[key]
            if fdata['surface']['enabled']:
                is_surface_enabled = True
                surface_bytes += fdata['surface']['bytes']
            if fdata['preview']['enabled']:
                is_preview_enabled = True
                preview_bytes += fdata['preview']['bytes']
            if fdata['foam']['enabled']:
                is_foam_enabled = True
                foam_bytes += fdata['foam']['bytes']
            if fdata['bubble']['enabled']:
                is_bubble_enabled = True
                bubble_bytes += fdata['bubble']['bytes']
            if fdata['spray']['enabled']:
                is_spray_enabled = True
                spray_bytes += fdata['spray']['bytes']
            if fdata['particles']['enabled']:
                is_particles_enabled = True
                particles_bytes += fdata['particles']['bytes']
            if fdata['obstacle']['enabled']:
                is_obstacle_enabled = True
                obstacle_bytes += fdata['obstacle']['bytes']

            total_time     += fdata['timing']['total']
            time_mesh      += fdata['timing']['mesh']
            time_advection += fdata['timing']['advection']
            time_particles += fdata['timing']['particles']
            time_pressure  += fdata['timing']['pressure']
            time_diffuse   += fdata['timing']['diffuse']
            time_viscosity += fdata['timing']['viscosity']
            time_objects   += fdata['timing']['objects']

        if not is_data_in_cache:
            self.is_cache_info_available = False
            return

        self.num_cache_frames = num_cache_frames

        self.surface_mesh.enabled = is_surface_enabled
        self.preview_mesh.enabled = is_preview_enabled
        self.foam_mesh.enabled = is_foam_enabled
        self.bubble_mesh.enabled = is_bubble_enabled
        self.spray_mesh.enabled = is_spray_enabled
        self.particle_mesh.enabled = is_particles_enabled
        self.obstacle_mesh.enabled = is_obstacle_enabled

        self.surface_mesh.bytes.set(surface_bytes)
        self.preview_mesh.bytes.set(preview_bytes)
        self.foam_mesh.bytes.set(foam_bytes)
        self.bubble_mesh.bytes.set(bubble_bytes)
        self.spray_mesh.bytes.set(spray_bytes)
        self.particle_mesh.bytes.set(particles_bytes)
        self.obstacle_mesh.bytes.set(obstacle_bytes)

        time_other = (total_time - time_mesh
                                 - time_advection
                                 - time_particles
                                 - time_pressure
                                 - time_diffuse
                                 - time_viscosity
                                 - time_objects)

        self.time_mesh.time      = time_mesh
        self.time_advection.time = time_advection
        self.time_particles.time = time_particles
        self.time_pressure.time  = time_pressure
        self.time_diffuse.time   = time_diffuse
        self.time_viscosity.time = time_viscosity
        self.time_objects .time  = time_objects
        self.time_other.time     = time_other
        self.display_frame_viscosity_timing_stats = time_viscosity > 0.0
        self.display_frame_diffuse_timing_stats = time_diffuse > 0.0

        self.time_mesh.set_time_pct(     100 * time_mesh      / total_time)
        self.time_advection.set_time_pct(100 * time_advection / total_time)
        self.time_particles.set_time_pct(100 * time_particles / total_time)
        self.time_pressure.set_time_pct( 100 * time_pressure  / total_time)
        self.time_diffuse.set_time_pct(  100 * time_diffuse   / total_time)
        self.time_viscosity.set_time_pct(100 * time_viscosity / total_time)
        self.time_objects.set_time_pct(  100 * time_objects   / total_time)
        self.time_other.set_time_pct(    100 * time_other     / total_time)

        frame_speed = self._get_estimated_frame_speed(cachedata)
        self.estimated_frame_speed = frame_speed
        self.is_estimated_time_remaining_available = frame_speed > 0

        if self.is_estimated_time_remaining_available:
            num_frames = dprops.simulation.frame_end - dprops.simulation.frame_start + 1
            frames_left = num_frames - dprops.bake.num_baked_frames
            time_remaining = int(math.ceil((1.0 / frame_speed) * frames_left))
            time_remaining = min(time_remaining, 2147483648 - 1)
            self.estimated_time_remaining = time_remaining
            self.estimated_time_remaining_timestamp = self.get_timestamp()

        self._update_cache_size(cachedata)


    def _get_estimated_frame_speed(self, cachedata):
        max_frame = 0
        num_frames = 0
        total_time = 0.0
        for key in cachedata.keys():
            if not key.isdigit():
                continue
            max_frame = max(max_frame, cachedata[key]['frame'])
            num_frames += 1
            total_time += cachedata[key]['timing']['total']

        if num_frames <= 1:
            return -1.0

        avg_frame_time = total_time / num_frames

        is_frame_data_available = (max_frame + 1) * [False]
        for key in cachedata.keys():
            if not key.isdigit():
                continue
            is_frame_data_available[cachedata[key]['frame']] = True

        frame_times = (max_frame + 1) * [avg_frame_time]
        for key in cachedata.keys():
            if not key.isdigit():
                continue
            frame_times[cachedata[key]['frame']] = cachedata[key]['timing']['total']

        # First frame is often innaccurate, so discard
        frame_times.pop(0)

        frame_speeds = []
        for t in frame_times:
            frame_speeds.append(1.0 / max(1e-6, t))

        smoothing_factor = 0.1
        average_speed = frame_speeds[0]
        for s in frame_speeds:
            average_speed = smoothing_factor * s + (1.0 - smoothing_factor) * average_speed
        return average_speed


def register():
    bpy.utils.register_class(ByteProperty)
    bpy.utils.register_class(MeshStatsProperties)
    bpy.utils.register_class(TimeStatsProperties)
    bpy.utils.register_class(DomainStatsProperties)


def unregister():
    bpy.utils.unregister_class(ByteProperty)
    bpy.utils.unregister_class(MeshStatsProperties)
    bpy.utils.unregister_class(TimeStatsProperties)
    bpy.utils.unregister_class(DomainStatsProperties)