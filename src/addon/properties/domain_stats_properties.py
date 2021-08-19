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
from ..utils import version_compatibility_utils as vcu

# ##############################################################################
#   STATS PROPERTIES
# ##############################################################################

class ByteProperty(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    bytes = FloatProperty(
            default=-1.0, 
            get=lambda self: self._get_bytes(),
            set=lambda self, value: self._set_bytes(value),
            ); exec(conv("bytes"))


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
    conv = vcu.convert_attribute_to_28
    enabled = bpy.props.BoolProperty(default=False); exec(conv("enabled"))
    verts = bpy.props.IntProperty(default=-1); exec(conv("verts"))
    faces = bpy.props.IntProperty(default=-1); exec(conv("faces"))
    bytes = PointerProperty(type=ByteProperty); exec(conv("bytes"))


class TimeStatsProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    time = FloatProperty(
            default=-1.0, 
            precision = 1
            ); exec(conv("time"))
    pct = FloatProperty(
            min=0, max=100,
            default=0.0, 
            precision = 1,
            subtype='PERCENTAGE',
            get=lambda self: self._get_time_pct(),
            set=lambda self, value: None,
            ); exec(conv("pct"))


    def set_time_pct(self, value):
        self["pct"] = value


    def _get_time_pct(self):
        try: 
            return self["pct"] 
        except: 
            return 0.0


class DomainStatsProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    cache_info_type = EnumProperty(
            name="Cache Info Display Mode",
            description="Type of cache info to display",
            items=types.cache_info_modes,
            default='CACHE_INFO',
            update=lambda self, context: self._update_cache_info_type(context),
            ); exec(conv("cache_info_type"))
    current_info_frame = IntProperty(
            name="Frame", 
            description="Select frame number", 
            min=0,
            default=0,
            update=lambda self, context: self._update_current_info_frame(context),
            ); exec(conv("current_info_frame"))
    lock_info_frame_to_timeline = BoolProperty(
            name="Lock To Timeline",
            description="Set frame number to current frame in timeline",
            default=True,
            update=lambda self, context: self._update_lock_info_frame_to_timeline(context),
            ); exec(conv("lock_info_frame_to_timeline"))
    temp_directory = vcu.get_blender_preferences_temporary_directory()
    csv_save_filepath = StringProperty(
            name="",
            default=os.path.join(temp_directory, "flip_fluid_stats.csv"), 
            subtype='FILE_PATH'
            ); exec(conv("csv_save_filepath"))
    csv_region_format = EnumProperty(
            name="Region Format",
            description="CSV region formatting",
            items=types.csv_regions,
            default='CSV_REGION_US',
            ); exec(conv("csv_region_format"))

    stats_filename = bpy.props.StringProperty(default='flipstats.data'); exec(conv("stats_filename"))
    is_stats_current = bpy.props.BoolProperty(default=False); exec(conv("is_stats_current"))

    # Cache Info
    cache_info_simulation_stats_expanded = BoolProperty(default=True); exec(conv("cache_info_simulation_stats_expanded"))
    cache_info_timing_stats_expanded = BoolProperty(default=True); exec(conv("cache_info_timing_stats_expanded"))
    cache_info_mesh_stats_expanded = BoolProperty(default=True); exec(conv("cache_info_mesh_stats_expanded"))
    is_cache_info_available = BoolProperty(default=False); exec(conv("is_cache_info_available"))
    num_cache_frames = IntProperty(default=-1); exec(conv("num_cache_frames"))
    estimated_frame_speed = FloatProperty(default=-1); exec(conv("estimated_frame_speed"))
    estimated_time_remaining = IntProperty(default=-1); exec(conv("estimated_time_remaining"))
    estimated_time_remaining_timestamp = IntProperty(default=-1); exec(conv("estimated_time_remaining_timestamp"))
    is_estimated_time_remaining_available = BoolProperty(default=False); exec(conv("is_estimated_time_remaining_available"))
    cache_bytes = PointerProperty(type=ByteProperty); exec(conv("cache_bytes"))

    # Frame Info
    frame_info_simulation_stats_expanded = BoolProperty(default=True); exec(conv("frame_info_simulation_stats_expanded"))
    frame_info_timing_stats_expanded = BoolProperty(default=True); exec(conv("frame_info_timing_stats_expanded"))
    frame_info_mesh_stats_expanded = BoolProperty(default=True); exec(conv("frame_info_mesh_stats_expanded"))
    display_frame_viscosity_timing_stats = BoolProperty(default=False); exec(conv("display_frame_viscosity_timing_stats"))
    display_frame_diffuse_timing_stats = BoolProperty(default=False); exec(conv("display_frame_diffuse_timing_stats"))
    display_frame_diffuse_particle_stats = BoolProperty(default=False); exec(conv("display_frame_diffuse_particle_stats"))
    is_frame_info_available = bpy.props.BoolProperty(default=False); exec(conv("is_frame_info_available"))
    frame_info_id = IntProperty(default=-1); exec(conv("frame_info_id"))
    frame_substeps = IntProperty(default=-1); exec(conv("frame_substeps"))
    frame_delta_time = FloatProperty(default=0.0); exec(conv("frame_delta_time"))
    frame_fluid_particles = IntProperty(default=-1); exec(conv("frame_fluid_particles"))
    frame_diffuse_particles = IntProperty(default=-1); exec(conv("frame_diffuse_particles"))

    # Mesh Info
    surface_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surface_mesh"))
    preview_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("preview_mesh"))
    surfaceblur_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surfaceblur_mesh"))
    surfacevelocity_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surfacevelocity_mesh"))
    surfacespeed_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surfacespeed_mesh"))
    surfaceage_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surfaceage_mesh"))
    surfacecolor_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surfacecolor_mesh"))
    surfacesourceid_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("surfacesourceid_mesh"))
    foam_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("foam_mesh"))
    bubble_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("bubble_mesh"))
    spray_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("spray_mesh"))
    dust_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("dust_mesh"))
    foamblur_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("foamblur_mesh"))
    bubbleblur_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("bubbleblur_mesh"))
    sprayblur_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("sprayblur_mesh"))
    dustblur_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("dustblur_mesh"))
    particle_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("particle_mesh"))
    obstacle_mesh = PointerProperty(type=MeshStatsProperties); exec(conv("obstacle_mesh"))

    # Time Info
    time_mesh = PointerProperty(type=TimeStatsProperties); exec(conv("time_mesh"))
    time_advection = PointerProperty(type=TimeStatsProperties); exec(conv("time_advection"))
    time_particles = PointerProperty(type=TimeStatsProperties); exec(conv("time_particles"))
    time_pressure = PointerProperty(type=TimeStatsProperties); exec(conv("time_pressure"))
    time_diffuse = PointerProperty(type=TimeStatsProperties); exec(conv("time_diffuse"))
    time_viscosity = PointerProperty(type=TimeStatsProperties); exec(conv("time_viscosity"))
    time_objects = PointerProperty(type=TimeStatsProperties); exec(conv("time_objects"))
    time_other = PointerProperty(type=TimeStatsProperties); exec(conv("time_other"))


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


    def reset_stats_values(self):
        prop_names = [
            "frame_info_id",
            "frame_substeps",
            "frame_delta_time",
            "frame_fluid_particles",
            "frame_diffuse_particles",
            "surface_mesh",
            "preview_mesh",
            "surfaceblur_mesh",
            "surfacevelocity_mesh",
            "surfacespeed_mesh",
            "surfaceage_mesh",
            "surfacecolor_mesh",
            "surfacesourceid_mesh",
            "foam_mesh",
            "bubble_mesh",
            "spray_mesh",
            "dust_mesh",
            "foamblur_mesh",
            "bubbleblur_mesh",
            "sprayblur_mesh",
            "dustblur_mesh",
            "particle_mesh",
            "obstacle_mesh",
            "time_mesh",
            "time_advection",
            "time_particles",
            "time_pressure",
            "time_diffuse",
            "time_viscosity",
            "time_objects",
            "time_other"
            ]

        for name in prop_names:
            self.property_unset(name)


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

        self._update_estimated_time_remaining()

        self.is_stats_current = True


    def scene_update_post(self, scene):
        if self.is_stats_current:
            return
        self.refresh_stats()


    def frame_change_post(self, scene, depsgraph=None):
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

        self._update_estimated_time_remaining()


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

        with open(statsfile, 'r', encoding='utf-8') as f:
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

        self._set_mesh_stats_data(self.surface_mesh,          data['surface'])
        self._set_mesh_stats_data(self.preview_mesh,          data['preview'])
        self._set_mesh_stats_data(self.surfaceblur_mesh,      data['surfaceblur'])
        
        if 'surfacevelocity' in data:
            # If statement to support older caches that do not have a surfacevelocity entry
            self._set_mesh_stats_data(self.surfacevelocity_mesh, data['surfacevelocity'])

        if 'surfacespeed' in data:
            # If statement to support older caches that do not have a surfacespeed entry
            self._set_mesh_stats_data(self.surfacespeed_mesh, data['surfacespeed'])

        if 'surfaceage' in data:
            # If statement to support older caches that do not have a surfaceage entry
            self._set_mesh_stats_data(self.surfaceage_mesh, data['surfaceage'])

        if 'surfacecolor' in data:
            # If statement to support older caches that do not have a surfacecolor entry
            self._set_mesh_stats_data(self.surfacecolor_mesh, data['surfacecolor'])

        if 'surfacesourceid' in data:
            # If statement to support older caches that do not have a surfacesourceid entry
            self._set_mesh_stats_data(self.surfacesourceid_mesh, data['surfacesourceid'])

        self._set_mesh_stats_data(self.foam_mesh,             data['foam'])
        self._set_mesh_stats_data(self.bubble_mesh,           data['bubble'])
        self._set_mesh_stats_data(self.spray_mesh,            data['spray'])

        if 'dust' in data:
            # If statement to support older caches that do not have a dust entry
            self._set_mesh_stats_data(self.dust_mesh,         data['dust'])

        self._set_mesh_stats_data(self.foamblur_mesh,   data['foamblur'])
        self._set_mesh_stats_data(self.bubbleblur_mesh, data['bubbleblur'])
        self._set_mesh_stats_data(self.sprayblur_mesh,  data['sprayblur'])

        if 'dustblur' in data:
            # If statement to support older caches that do not have a dustblur entry
            self._set_mesh_stats_data(self.dustblur_mesh,   data['dustblur'])

        self._set_mesh_stats_data(self.particle_mesh,   data['particles'])
        self._set_mesh_stats_data(self.obstacle_mesh,   data['obstacle'])

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
            if fdata['surfaceblur']['enabled']:
                cache_size += fdata['surfaceblur']['bytes']
            if 'surfacevelocity' in fdata and fdata['surfacevelocity']['enabled']: # If statement to support caches without a surfacevelocity entry
                cache_size += fdata['surfacevelocity']['bytes']
            if 'surfacespeed' in fdata and fdata['surfacespeed']['enabled']: # If statement to support caches without a surfacespeed entry
                cache_size += fdata['surfacespeed']['bytes']
            if 'surfaceage' in fdata and fdata['surfaceage']['enabled']: # If statement to support caches without a surfaceage entry
                cache_size += fdata['surfaceage']['bytes']
            if 'surfacecolor' in fdata and fdata['surfacecolor']['enabled']: # If statement to support caches without a surfacecolor entry
                cache_size += fdata['surfacecolor']['bytes']
            if 'surfacesourceid' in fdata and fdata['surfacesourceid']['enabled']: # If statement to support caches without a surfacesourceid entry
                cache_size += fdata['surfacesourceid']['bytes']
            if fdata['foam']['enabled']:
                cache_size += fdata['foam']['bytes']
            if fdata['bubble']['enabled']:
                cache_size += fdata['bubble']['bytes']
            if fdata['spray']['enabled']:
                cache_size += fdata['spray']['bytes']
            if 'dust' in fdata and fdata['dust']['enabled']: # If statement to support caches without a dust entry
                cache_size += fdata['dust']['bytes']
            if fdata['foamblur']['enabled']:
                cache_size += fdata['foamblur']['bytes']
            if fdata['bubbleblur']['enabled']:
                cache_size += fdata['bubbleblur']['bytes']
            if fdata['sprayblur']['enabled']:
                cache_size += fdata['sprayblur']['bytes']
            if 'dustblur' in fdata and fdata['dustblur']['enabled']: # If statement to support caches without a dustblur entry
                cache_size += fdata['dustblur']['bytes']
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

        with open(statsfile, 'r', encoding='utf-8') as f:
            cachedata = json.loads(f.read())

        self.is_cache_info_available = True

        is_surface_enabled = False
        is_preview_enabled = False
        is_surfaceblur_enabled = False
        is_surfacevelocity_enabled = False
        is_surfacespeed_enabled = False
        is_surfaceage_enabled = False
        is_surfacecolor_enabled = False
        is_surfacesourceid_enabled = False
        is_foam_enabled = False
        is_bubble_enabled = False
        is_spray_enabled = False
        is_dust_enabled = False
        is_foamblur_enabled = False
        is_bubbleblur_enabled = False
        is_sprayblur_enabled = False
        is_dustblur_enabled = False
        is_particles_enabled = False
        is_obstacle_enabled = False
        surface_bytes = 0
        preview_bytes = 0
        surfaceblur_bytes = 0
        surfacevelocity_bytes = 0
        surfacespeed_bytes = 0
        surfaceage_bytes = 0
        surfacecolor_bytes = 0
        surfacesourceid_bytes = 0
        foam_bytes = 0
        bubble_bytes = 0
        spray_bytes = 0
        dust_bytes = 0
        foamblur_bytes = 0
        bubbleblur_bytes = 0
        sprayblur_bytes = 0
        dustblur_bytes = 0
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
            if fdata['surfaceblur']['enabled']:
                is_surfaceblur_enabled = True
                surfaceblur_bytes += fdata['surfaceblur']['bytes']
            if 'surfacevelocity' in fdata and fdata['surfacevelocity']['enabled']: # If statement to support caches without a surfacevelocity entry
                is_surfacevelocity_enabled = True
                surfacevelocity_bytes += fdata['surfacevelocity']['bytes']
            if 'surfacespeed' in fdata and fdata['surfacespeed']['enabled']: # If statement to support caches without a surfacespeed entry
                is_surfacespeed_enabled = True
                surfacespeed_bytes += fdata['surfacespeed']['bytes']
            if 'surfaceage' in fdata and fdata['surfaceage']['enabled']: # If statement to support caches without a surfaceage entry
                is_surfaceage_enabled = True
                surfaceage_bytes += fdata['surfaceage']['bytes']
            if 'surfacecolor' in fdata and fdata['surfacecolor']['enabled']: # If statement to support caches without a surfacecolor entry
                is_surfacecolor_enabled = True
                surfacecolor_bytes += fdata['surfacecolor']['bytes']
            if 'surfacesourceid' in fdata and fdata['surfacesourceid']['enabled']: # If statement to support caches without a surfacesourceid entry
                is_surfacesourceid_enabled = True
                surfacesourceid_bytes += fdata['surfacesourceid']['bytes']
            if fdata['foam']['enabled']:
                is_foam_enabled = True
                foam_bytes += fdata['foam']['bytes']
            if fdata['bubble']['enabled']:
                is_bubble_enabled = True
                bubble_bytes += fdata['bubble']['bytes']
            if fdata['spray']['enabled']:
                is_spray_enabled = True
                spray_bytes += fdata['spray']['bytes']
            if 'dust' in fdata and fdata['dust']['enabled']: # If statement to support caches without a dust entry
                is_dust_enabled = True
                dust_bytes += fdata['dust']['bytes']
            if fdata['foamblur']['enabled']:
                is_foamblur_enabled = True
                foamblur_bytes += fdata['foamblur']['bytes']
            if fdata['bubbleblur']['enabled']:
                is_bubbleeblur_enabled = True
                bubbleblur_bytes += fdata['bubbleblur']['bytes']
            if fdata['sprayblur']['enabled']:
                is_sprayblur_enabled = True
                sprayblur_bytes += fdata['sprayblur']['bytes']
            if 'dustblur' in fdata and fdata['sprayblur']['enabled']: # If statement to support caches without a dustblur entry
                is_dustblur_enabled = True
                dustblur_bytes += fdata['dustblur']['bytes']
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
        self.surfaceblur_mesh.enabled = is_surfaceblur_enabled
        self.surfacevelocity_mesh.enabled = is_surfacevelocity_enabled
        self.surfacespeed_mesh.enabled = is_surfacespeed_enabled
        self.surfaceage_mesh.enabled = is_surfaceage_enabled
        self.surfacecolor_mesh.enabled = is_surfacecolor_enabled
        self.surfacesourceid_mesh.enabled = is_surfacesourceid_enabled
        self.foam_mesh.enabled = is_foam_enabled
        self.bubble_mesh.enabled = is_bubble_enabled
        self.spray_mesh.enabled = is_spray_enabled
        self.dust_mesh.enabled = is_dust_enabled
        self.foamblur_mesh.enabled = is_foamblur_enabled
        self.bubbleblur_mesh.enabled = is_bubbleblur_enabled
        self.sprayblur_mesh.enabled = is_sprayblur_enabled
        self.dustblur_mesh.enabled = is_dustblur_enabled
        self.particle_mesh.enabled = is_particles_enabled
        self.obstacle_mesh.enabled = is_obstacle_enabled

        self.surface_mesh.bytes.set(surface_bytes)
        self.preview_mesh.bytes.set(preview_bytes)
        self.surfaceblur_mesh.bytes.set(surfaceblur_bytes)
        self.surfacevelocity_mesh.bytes.set(surfacevelocity_bytes)
        self.surfacespeed_mesh.bytes.set(surfacespeed_bytes)
        self.surfaceage_mesh.bytes.set(surfaceage_bytes)
        self.surfacecolor_mesh.bytes.set(surfacecolor_bytes)
        self.surfacesourceid_mesh.bytes.set(surfacesourceid_bytes)
        self.foam_mesh.bytes.set(foam_bytes)
        self.bubble_mesh.bytes.set(bubble_bytes)
        self.spray_mesh.bytes.set(spray_bytes)
        self.dust_mesh.bytes.set(dust_bytes)
        self.foamblur_mesh.bytes.set(foamblur_bytes)
        self.bubbleblur_mesh.bytes.set(bubbleblur_bytes)
        self.sprayblur_mesh.bytes.set(sprayblur_bytes)
        self.dustblur_mesh.bytes.set(dustblur_bytes)
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


    def _update_estimated_time_remaining(self):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        cache_directory = dprops.cache.get_cache_abspath()
        statsfile = os.path.join(cache_directory, self.stats_filename)
        if not os.path.isfile(statsfile):
            return

        with open(statsfile, 'r', encoding='utf-8') as f:
            cachedata = json.loads(f.read())

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