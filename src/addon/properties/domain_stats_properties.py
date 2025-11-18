# Blender FLIP Fluids Add-on
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
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
from ..operators import bake_operators


# ##############################################################################
#   STATS PROPERTIES
# ##############################################################################

class ByteProperty(bpy.types.PropertyGroup):
    bytes: FloatProperty(
            default=-1.0, 
            get=lambda self: self._get_bytes(),
            set=lambda self, value: self._set_bytes(value),
            )


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
    enabled: bpy.props.BoolProperty(default=False)
    verts: bpy.props.IntProperty(default=-1)
    faces: bpy.props.IntProperty(default=-1)
    bytes: PointerProperty(type=ByteProperty)


class TimeStatsProperties(bpy.types.PropertyGroup):
    time: FloatProperty(
            default=-1.0, 
            precision = 1
            )
    pct: FloatProperty(
            min=0, max=100,
            default=0.0, 
            precision = 1,
            subtype='PERCENTAGE',
            get=lambda self: self._get_time_pct(),
            set=lambda self, value: None,
            )


    def set_time_pct(self, value):
        self["pct"] = value


    def _get_time_pct(self):
        try: 
            return self["pct"] 
        except: 
            return 0.0


class SolverStressProperties(bpy.types.PropertyGroup):
    stress_level: FloatProperty(
            name="Stress Level",
            description="Amount of stress experienced by the solver. If the stress level exceeds"
                " 80% for multiple consecutive frames, this may indicate that the simulator requires"
                " more substeps to reduce stress and keep the simulation stable. Substeps can be adjusted"
                " in the Advanced panel. If a max stress level is reached, the solver may fail. It is okay"
                " and normal for the solver to fail infrequently, but if it is failing on multiple consecutive"
                " frames, this may result in an unstable simulation",
            min=0, max=100,
            default=0.0, 
            precision = 1,
            subtype='PERCENTAGE',
            get=lambda self: self._get_stress_level_pct(),
            set=lambda self, value: None,
            )


    def set_stress_level_pct(self, value):
        self["stress_level"] = value


    def _get_stress_level_pct(self):
        try: 
            return self["stress_level"] 
        except: 
            return 0.0


class DomainStatsProperties(bpy.types.PropertyGroup):

    # required for relative path support in Blender 4.5+
    # https://docs.blender.org/api/4.5/bpy_types_enum_items/property_flag_items.html#rna-enum-property-flag-items
    option_path_supports_blend_relative = {'PATH_SUPPORTS_BLEND_RELATIVE'}
    
    cache_info_type: EnumProperty(
            name="Cache Info Display Mode",
            description="Type of cache info to display",
            items=types.cache_info_modes,
            default='CACHE_INFO',
            update=lambda self, context: self._update_cache_info_type(context),
            )
    current_info_frame: IntProperty(
            name="Frame", 
            description="Select frame number", 
            min=0,
            default=0,
            update=lambda self, context: self._update_current_info_frame(context),
            )
    lock_info_frame_to_timeline: BoolProperty(
            name="Lock To Timeline",
            description="Set frame number to current frame in timeline",
            default=True,
            update=lambda self, context: self._update_lock_info_frame_to_timeline(context),
            )
    temp_directory = vcu.get_blender_preferences_temporary_directory()
    csv_save_filepath: StringProperty(
            name="",
            default=os.path.join(temp_directory, "flip_fluid_stats.csv"), 
            subtype='FILE_PATH',
            options=option_path_supports_blend_relative,
            )
    csv_region_format: EnumProperty(
            name="Region Format",
            description="CSV region formatting",
            items=types.csv_regions,
            default='CSV_REGION_US',
            )

    stats_filename: bpy.props.StringProperty(default='flipstats.data')
    is_stats_current: bpy.props.BoolProperty(default=False)

    # Cache Info
    is_cache_info_available: BoolProperty(default=False)
    frame_start: IntProperty(default=-1)
    num_cache_frames: IntProperty(default=-1)
    is_average_performance_score_enabled: BoolProperty(default=False)
    average_performance_score: IntProperty(default=-1)
    estimated_frame_speed: FloatProperty(default=-1)
    estimated_time_remaining: IntProperty(default=-1)
    estimated_time_remaining_timestamp: IntProperty(default=-1)
    is_estimated_time_remaining_available: BoolProperty(default=False)
    cache_bytes: PointerProperty(type=ByteProperty)

    pressure_solver_enabled: BoolProperty(default=False)
    pressure_solver_failures: IntProperty(default=-1)
    pressure_solver_steps: IntProperty(default=-1)
    pressure_solver_max_iterations: IntProperty(default=-1)
    pressure_solver_max_iterations_frame: IntProperty(default=-1)
    pressure_solver_max_error: FloatProperty(default=-1)
    pressure_solver_max_error_frame: IntProperty(default=-1)
    pressure_solver_max_stress: FloatProperty(default=-1)
    pressure_solver_max_stress_frame: IntProperty(default=-1)

    viscosity_solver_enabled: BoolProperty(default=False)
    viscosity_solver_failures: IntProperty(default=-1)
    viscosity_solver_steps: IntProperty(default=-1)
    viscosity_solver_max_iterations: IntProperty(default=-1)
    viscosity_solver_max_iterations_frame: IntProperty(default=-1)
    viscosity_solver_max_error: FloatProperty(default=-1)
    viscosity_solver_max_error_frame: IntProperty(default=-1)
    viscosity_solver_max_stress: FloatProperty(default=-1)
    viscosity_solver_max_stress_frame: IntProperty(default=-1)

    # Frame Info
    frame_info_simulation_stats_expanded: BoolProperty(default=True)
    frame_info_solver_stats_expanded: BoolProperty(default=True)
    frame_info_pressure_solver_stats_expanded: BoolProperty(default=True)
    frame_info_viscosity_solver_stats_expanded: BoolProperty(default=True)
    frame_info_timing_stats_expanded: BoolProperty(default=True)
    frame_info_mesh_stats_expanded: BoolProperty(default=True)
    display_frame_viscosity_timing_stats: BoolProperty(default=False)
    display_frame_diffuse_timing_stats: BoolProperty(default=False)
    display_frame_diffuse_particle_stats: BoolProperty(default=False)
    is_frame_info_available: bpy.props.BoolProperty(default=False)
    frame_info_id: IntProperty(default=-1)
    frame_substeps: IntProperty(default=-1)
    frame_delta_time: FloatProperty(default=0.0)
    frame_fluid_particles: IntProperty(default=-1)
    frame_diffuse_particles: IntProperty(default=-1)
    frame_performance_score: IntProperty(default=-1)

    frame_pressure_solver_enabled: BoolProperty(default=False)
    frame_pressure_solver_success: BoolProperty(default=True)
    frame_pressure_solver_error: FloatProperty(default=0.0)
    frame_pressure_solver_iterations: IntProperty(default=-1)
    frame_pressure_solver_max_iterations: IntProperty(default=-1)
    frame_pressure_solver_stress: PointerProperty(type=SolverStressProperties)

    frame_viscosity_solver_enabled: BoolProperty(default=False)
    frame_viscosity_solver_success: BoolProperty(default=True)
    frame_viscosity_solver_error: FloatProperty(default=0.0)
    frame_viscosity_solver_iterations: IntProperty(default=-1)
    frame_viscosity_solver_max_iterations: IntProperty(default=-1)
    frame_viscosity_solver_stress: PointerProperty(type=SolverStressProperties)

    # Mesh Info
    surface_mesh: PointerProperty(type=MeshStatsProperties)
    preview_mesh: PointerProperty(type=MeshStatsProperties)
    surfaceblur_mesh: PointerProperty(type=MeshStatsProperties)
    surfacevelocity_mesh: PointerProperty(type=MeshStatsProperties)
    surfacespeed_mesh: PointerProperty(type=MeshStatsProperties)
    surfacevorticity_mesh: PointerProperty(type=MeshStatsProperties)
    surfaceage_mesh: PointerProperty(type=MeshStatsProperties)
    surfacelifetime_mesh: PointerProperty(type=MeshStatsProperties)
    surfacewhitewaterproximity_mesh: PointerProperty(type=MeshStatsProperties)
    surfacecolor_mesh: PointerProperty(type=MeshStatsProperties)
    surfacesourceid_mesh: PointerProperty(type=MeshStatsProperties)
    surfaceviscosity_mesh: PointerProperty(type=MeshStatsProperties)
    surfacedensity_mesh: PointerProperty(type=MeshStatsProperties)
    foam_mesh: PointerProperty(type=MeshStatsProperties)
    bubble_mesh: PointerProperty(type=MeshStatsProperties)
    spray_mesh: PointerProperty(type=MeshStatsProperties)
    dust_mesh: PointerProperty(type=MeshStatsProperties)
    foamblur_mesh: PointerProperty(type=MeshStatsProperties)
    bubbleblur_mesh: PointerProperty(type=MeshStatsProperties)
    sprayblur_mesh: PointerProperty(type=MeshStatsProperties)
    dustblur_mesh: PointerProperty(type=MeshStatsProperties)
    foamvelocity_mesh: PointerProperty(type=MeshStatsProperties)
    bubblevelocity_mesh: PointerProperty(type=MeshStatsProperties)
    sprayvelocity_mesh: PointerProperty(type=MeshStatsProperties)
    dustvelocity_mesh: PointerProperty(type=MeshStatsProperties)
    foamid_mesh: PointerProperty(type=MeshStatsProperties)
    bubbleid_mesh: PointerProperty(type=MeshStatsProperties)
    sprayid_mesh: PointerProperty(type=MeshStatsProperties)
    dustid_mesh: PointerProperty(type=MeshStatsProperties)
    foamlifetime_mesh: PointerProperty(type=MeshStatsProperties)
    bubblelifetime_mesh: PointerProperty(type=MeshStatsProperties)
    spraylifetime_mesh: PointerProperty(type=MeshStatsProperties)
    dustlifetime_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_id_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_velocity_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_speed_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_vorticity_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_color_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_age_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_lifetime_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_viscosity_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_density_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_density_average_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_whitewater_proximity_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_source_id_mesh: PointerProperty(type=MeshStatsProperties)
    fluid_particle_uid_mesh: PointerProperty(type=MeshStatsProperties)
    debug_particle_mesh: PointerProperty(type=MeshStatsProperties)
    obstacle_mesh: PointerProperty(type=MeshStatsProperties)

    # Time Info
    time_mesh: PointerProperty(type=TimeStatsProperties)
    time_advection: PointerProperty(type=TimeStatsProperties)
    time_particles: PointerProperty(type=TimeStatsProperties)
    time_pressure: PointerProperty(type=TimeStatsProperties)
    time_diffuse: PointerProperty(type=TimeStatsProperties)
    time_viscosity: PointerProperty(type=TimeStatsProperties)
    time_objects: PointerProperty(type=TimeStatsProperties)
    time_other: PointerProperty(type=TimeStatsProperties)


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".cache_info_type",             "Info Type",              group_id=0)
        add(path + ".lock_info_frame_to_timeline", "Lock Frame to Timeline", group_id=0)
        add(path + ".csv_region_format",           "CSV Region Format",      group_id=0)


    def repair_corrupt_stats_file(self, stats_filepath):
        errmsg = "FLIP Fluids Error: Corrupt stats file detected: <" + stats_filepath + ">. "
        errmsg += "This file may have become corrupted after a Blender crash. Regenerating a new stats file. "
        errmsg += "Information in the 'Domain > FLIP Fluid Stats' panel may be missing data and may display inaccurate data."
        print(errmsg)
        empty_dict = {}
        empty_json = json.dumps(empty_dict)
        with open(stats_filepath, 'w', encoding='utf-8') as f:
            f.write(empty_json)
        return empty_dict


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
            "frame_performance_score",
            "frame_pressure_solver_enabled",
            "frame_pressure_solver_success",
            "frame_pressure_solver_error",
            "frame_pressure_solver_iterations",
            "frame_pressure_solver_max_iterations",
            "frame_viscosity_solver_enabled",
            "frame_viscosity_solver_success",
            "frame_viscosity_solver_error",
            "frame_viscosity_solver_iterations",
            "frame_viscosity_solver_max_iterations",
            "surface_mesh",
            "preview_mesh",
            "surfaceblur_mesh",
            "surfacevelocity_mesh",
            "surfacespeed_mesh",
            "surfacevorticity_mesh",
            "surfaceage_mesh",
            "surfacelifetime_mesh",
            "surfacewhitewaterproximity_mesh",
            "surfacecolor_mesh",
            "surfacesourceid_mesh",
            "surfaceviscosity_mesh",
            "surfacedensity_mesh",
            "foam_mesh",
            "bubble_mesh",
            "spray_mesh",
            "dust_mesh",
            "foamblur_mesh",
            "bubbleblur_mesh",
            "sprayblur_mesh",
            "dustblur_mesh",
            "foamvelocity_mesh",
            "bubblevelocity_mesh",
            "sprayvelocity_mesh",
            "dustvelocity_mesh",
            "foamid_mesh",
            "bubbleid_mesh",
            "sprayid_mesh",
            "dustid_mesh",
            "foamlifetime_mesh",
            "bubblelifetime_mesh",
            "spraylifetime_mesh",
            "dustlifetime_mesh",
            "fluid_particle_mesh",
            "fluid_particle_id_mesh",
            "fluid_particle_velocity_mesh",
            "fluid_particle_speed_mesh",
            "fluid_particle_vorticity_mesh",
            "fluid_particle_color_mesh",
            "fluid_particle_age_mesh",
            "fluid_particle_lifetime_mesh",
            "fluid_particle_viscosity_mesh",
            "fluid_particle_density_mesh",
            "fluid_particle_density_average_mesh",
            "fluid_particle_whitewater_proximity_mesh",
            "fluid_particle_source_id_mesh",
            "fluid_particle_uid_mesh",
            "debug_particle_mesh",
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
        bake_operators.update_stats()
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
            try:
                statsdata = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                # JSON file may have become corrupted after a crash.
                # In this case, repair the file by regenerating an
                # empty JSON file and continue with empty stats.
                statsdata = self.repair_corrupt_stats_file(statsfile)

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

        if 'performance_score' in data:
            self.frame_performance_score = data['performance_score']

        if 'pressure_solver_enabled' in data:
            self.frame_pressure_solver_enabled = bool(data['pressure_solver_enabled'])
            self.frame_pressure_solver_success = bool(data['pressure_solver_success'])
            self.frame_pressure_solver_error = data['pressure_solver_error']
            self.frame_pressure_solver_iterations = data['pressure_solver_iterations']
            self.frame_pressure_solver_max_iterations = data['pressure_solver_max_iterations']
            stress_pct = 100 * (self.frame_pressure_solver_iterations / self.frame_pressure_solver_max_iterations)
            self.frame_pressure_solver_stress.set_stress_level_pct(stress_pct)

        if 'viscosity_solver_enabled' in data:
            self.frame_viscosity_solver_enabled = bool(data['viscosity_solver_enabled'])
            self.frame_viscosity_solver_success = bool(data['viscosity_solver_success'])
            self.frame_viscosity_solver_error = data['viscosity_solver_error']
            self.frame_viscosity_solver_iterations = data['viscosity_solver_iterations']
            self.frame_viscosity_solver_max_iterations = data['viscosity_solver_max_iterations']
            stress_pct = 100 * (self.frame_viscosity_solver_iterations / self.frame_viscosity_solver_max_iterations)
            self.frame_viscosity_solver_stress.set_stress_level_pct(stress_pct)

        self._set_mesh_stats_data(self.surface_mesh,          data['surface'])
        self._set_mesh_stats_data(self.preview_mesh,          data['preview'])
        self._set_mesh_stats_data(self.surfaceblur_mesh,      data['surfaceblur'])
        
        if 'surfacevelocity' in data:
            # If statement to support older caches that do not have a surfacevelocity entry
            self._set_mesh_stats_data(self.surfacevelocity_mesh, data['surfacevelocity'])

        if 'surfacespeed' in data:
            # If statement to support older caches that do not have a surfacespeed entry
            self._set_mesh_stats_data(self.surfacespeed_mesh, data['surfacespeed'])

        if 'surfacevorticity' in data:
            # If statement to support older caches that do not have a surfacevorticity entry
            self._set_mesh_stats_data(self.surfacevorticity_mesh, data['surfacevorticity'])

        if 'surfaceage' in data:
            # If statement to support older caches that do not have a surfaceage entry
            self._set_mesh_stats_data(self.surfaceage_mesh, data['surfaceage'])

        if 'surfacelifetime' in data:
            # If statement to support older caches that do not have a surfacelifetime entry
            self._set_mesh_stats_data(self.surfacelifetime_mesh, data['surfacelifetime'])

        if 'surfacewhitewaterproximity' in data:
            # If statement to support older caches that do not have a surfacewhitewaterproximity entry
            self._set_mesh_stats_data(self.surfacewhitewaterproximity_mesh, data['surfacewhitewaterproximity'])

        if 'surfacecolor' in data:
            # If statement to support older caches that do not have a surfacecolor entry
            self._set_mesh_stats_data(self.surfacecolor_mesh, data['surfacecolor'])

        if 'surfacesourceid' in data:
            # If statement to support older caches that do not have a surfacesourceid entry
            self._set_mesh_stats_data(self.surfacesourceid_mesh, data['surfacesourceid'])

        if 'surfaceviscosity' in data:
            # If statement to support older caches that do not have a surfaceviscosity entry
            self._set_mesh_stats_data(self.surfaceviscosity_mesh, data['surfaceviscosity'])

        if 'surfacedensity' in data:
            # If statement to support older caches that do not have a surfacedensity entry
            self._set_mesh_stats_data(self.surfacedensity_mesh, data['surfacedensity'])

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

        if 'foamvelocity' in data:
            self._set_mesh_stats_data(self.foamvelocity_mesh,   data['foamvelocity'])
        if 'bubblevelocity' in data:
            self._set_mesh_stats_data(self.bubblevelocity_mesh, data['bubblevelocity'])
        if 'sprayvelocity' in data:
            self._set_mesh_stats_data(self.sprayvelocity_mesh,  data['sprayvelocity'])
        if 'dustvelocity' in data:
            self._set_mesh_stats_data(self.dustvelocity_mesh,   data['dustvelocity'])

        if 'foamid' in data:
            self._set_mesh_stats_data(self.foamid_mesh,   data['foamid'])
        if 'bubbleid' in data:
            self._set_mesh_stats_data(self.bubbleid_mesh, data['bubbleid'])
        if 'sprayid' in data:
            self._set_mesh_stats_data(self.sprayid_mesh,  data['sprayid'])
        if 'dustid' in data:
            self._set_mesh_stats_data(self.dustid_mesh,   data['dustid'])

        if 'foamlifetime' in data:
            self._set_mesh_stats_data(self.foamlifetime_mesh,   data['foamlifetime'])
        if 'bubblelifetime' in data:
            self._set_mesh_stats_data(self.bubblelifetime_mesh, data['bubblelifetime'])
        if 'spraylifetime' in data:
            self._set_mesh_stats_data(self.spraylifetime_mesh,  data['spraylifetime'])
        if 'dustlifetime' in data:
            self._set_mesh_stats_data(self.dustlifetime_mesh,   data['dustlifetime'])

        if 'fluidparticles' in data:
            # If statement to support older caches that do not have a fluidparticles entry
            self._set_mesh_stats_data(self.fluid_particle_mesh, data['fluidparticles'])

        if 'fluidparticlesid' in data:
            # If statement to support older caches that do not have a fluidparticlesid entry
            self._set_mesh_stats_data(self.fluid_particle_id_mesh, data['fluidparticlesid'])

        if 'fluidparticlesvelocity' in data:
            # If statement to support older caches that do not have a fluidparticlesvelocity entry
            self._set_mesh_stats_data(self.fluid_particle_velocity_mesh, data['fluidparticlesvelocity'])

        if 'fluidparticlesspeed' in data:
            # If statement to support older caches that do not have a fluidparticlesspeed entry
            self._set_mesh_stats_data(self.fluid_particle_speed_mesh, data['fluidparticlesspeed'])

        if 'fluidparticlesvorticity' in data:
            # If statement to support older caches that do not have a fluidparticlesvorticity entry
            self._set_mesh_stats_data(self.fluid_particle_vorticity_mesh, data['fluidparticlesvorticity'])

        if 'fluidparticlescolor' in data:
            # If statement to support older caches that do not have a fluidparticlescolor entry
            self._set_mesh_stats_data(self.fluid_particle_color_mesh, data['fluidparticlescolor'])

        if 'fluidparticlesage' in data:
            # If statement to support older caches that do not have a fluidparticlesage entry
            self._set_mesh_stats_data(self.fluid_particle_age_mesh, data['fluidparticlesage'])

        if 'fluidparticleslifetime' in data:
            # If statement to support older caches that do not have a fluidparticleslifetime entry
            self._set_mesh_stats_data(self.fluid_particle_lifetime_mesh, data['fluidparticleslifetime'])

        if 'fluidparticlesviscosity' in data:
            # If statement to support older caches that do not have a fluidparticlesviscosity entry
            self._set_mesh_stats_data(self.fluid_particle_viscosity_mesh, data['fluidparticlesviscosity'])

        if 'fluidparticlesdensity' in data:
            # If statement to support older caches that do not have a fluidparticlesdensity entry
            self._set_mesh_stats_data(self.fluid_particle_density_mesh, data['fluidparticlesdensity'])

        if 'fluidparticlesdensityaverage' in data:
            # If statement to support older caches that do not have a fluidparticlesdensityaverage entry
            self._set_mesh_stats_data(self.fluid_particle_density_average_mesh, data['fluidparticlesdensityaverage'])

        if 'fluidparticleswhitewaterproximity' in data:
            # If statement to support older caches that do not have a fluidparticleswhitewaterproximity entry
            self._set_mesh_stats_data(self.fluid_particle_whitewater_proximity_mesh, data['fluidparticleswhitewaterproximity'])

        if 'fluidparticlessourceid' in data:
            # If statement to support older caches that do not have a fluidparticlessourceid entry
            self._set_mesh_stats_data(self.fluid_particle_source_id_mesh, data['fluidparticlessourceid'])

        if 'fluidparticlesuid' in data:
            # If statement to support older caches that do not have a fluidparticlesuid entry
            self._set_mesh_stats_data(self.fluid_particle_uid_mesh, data['fluidparticlesuid'])

        self._set_mesh_stats_data(self.debug_particle_mesh, data['particles'])
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

        total_time = max(total_time, 1e-4)
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
            if 'surfacevorticity' in fdata and fdata['surfacevorticity']['enabled']: # If statement to support caches without a surfacevorticity entry
                cache_size += fdata['surfacevorticity']['bytes']
            if 'surfaceage' in fdata and fdata['surfaceage']['enabled']: # If statement to support caches without a surfaceage entry
                cache_size += fdata['surfaceage']['bytes']
            if 'surfacelifetime' in fdata and fdata['surfacelifetime']['enabled']: # If statement to support caches without a surfacelifetime entry
                cache_size += fdata['surfacelifetime']['bytes']
            if 'surfacewhitewaterproximity' in fdata and fdata['surfacewhitewaterproximity']['enabled']: # If statement to support caches without a surfacewhitewaterproximity entry
                cache_size += fdata['surfacewhitewaterproximity']['bytes']
            if 'surfacecolor' in fdata and fdata['surfacecolor']['enabled']: # If statement to support caches without a surfacecolor entry
                cache_size += fdata['surfacecolor']['bytes']
            if 'surfacesourceid' in fdata and fdata['surfacesourceid']['enabled']: # If statement to support caches without a surfacesourceid entry
                cache_size += fdata['surfacesourceid']['bytes']
            if 'surfaceviscosity' in fdata and fdata['surfaceviscosity']['enabled']: # If statement to support caches without a surfaceviscosity entry
                cache_size += fdata['surfaceviscosity']['bytes']
            if 'surfacedensity' in fdata and fdata['surfacedensity']['enabled']: # If statement to support caches without a surfacedensity entry
                cache_size += fdata['surfacedensity']['bytes']
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
            if 'foamvelocity' in fdata and fdata['foamvelocity']['enabled']:
                cache_size += fdata['foamvelocity']['bytes']
            if 'bubblevelocity' in fdata and fdata['bubblevelocity']['enabled']:
                cache_size += fdata['bubblevelocity']['bytes']
            if 'sprayvelocity' in fdata and fdata['sprayvelocity']['enabled']:
                cache_size += fdata['sprayvelocity']['bytes']
            if 'dustvelocity' in fdata and fdata['dustvelocity']['enabled']:
                cache_size += fdata['dustvelocity']['bytes']
            if 'foamid' in fdata and fdata['foamid']['enabled']:
                cache_size += fdata['foamid']['bytes']
            if 'bubbleid' in fdata and fdata['bubbleid']['enabled']:
                cache_size += fdata['bubbleid']['bytes']
            if 'sprayid' in fdata and fdata['sprayid']['enabled']:
                cache_size += fdata['sprayid']['bytes']
            if 'dustid' in fdata and fdata['dustid']['enabled']:
                cache_size += fdata['dustid']['bytes']
            if 'foamlifetime' in fdata and fdata['foamlifetime']['enabled']:
                cache_size += fdata['foamlifetime']['bytes']
            if 'bubblelifetime' in fdata and fdata['bubblelifetime']['enabled']:
                cache_size += fdata['bubblelifetime']['bytes']
            if 'spraylifetime' in fdata and fdata['spraylifetime']['enabled']:
                cache_size += fdata['spraylifetime']['bytes']
            if 'dustlifetime' in fdata and fdata['dustlifetime']['enabled']:
                cache_size += fdata['dustlifetime']['bytes']
            if 'fluidparticles' in fdata and fdata['fluidparticles']['enabled']:
                cache_size += fdata['fluidparticles']['bytes']
            if 'fluidparticlesid' in fdata and fdata['fluidparticlesid']['enabled']:
                cache_size += fdata['fluidparticlesid']['bytes']
            if 'fluidparticlesvelocity' in fdata and fdata['fluidparticlesvelocity']['enabled']:
                cache_size += fdata['fluidparticlesvelocity']['bytes']
            if 'fluidparticlesspeed' in fdata and fdata['fluidparticlesspeed']['enabled']:
                cache_size += fdata['fluidparticlesspeed']['bytes']
            if 'fluidparticlesvorticity' in fdata and fdata['fluidparticlesvorticity']['enabled']:
                cache_size += fdata['fluidparticlesvorticity']['bytes']
            if 'fluidparticlescolor' in fdata and fdata['fluidparticlescolor']['enabled']:
                cache_size += fdata['fluidparticlescolor']['bytes']
            if 'fluidparticlesage' in fdata and fdata['fluidparticlesage']['enabled']:
                cache_size += fdata['fluidparticlesage']['bytes']
            if 'fluidparticleslifetime' in fdata and fdata['fluidparticleslifetime']['enabled']:
                cache_size += fdata['fluidparticleslifetime']['bytes']
            if 'fluidparticlesviscosity' in fdata and fdata['fluidparticlesviscosity']['enabled']:
                cache_size += fdata['fluidparticlesviscosity']['bytes']
            if 'fluidparticlesdensity' in fdata and fdata['fluidparticlesdensity']['enabled']:
                cache_size += fdata['fluidparticlesdensity']['bytes']
            if 'fluidparticlesdensityaverage' in fdata and fdata['fluidparticlesdensityaverage']['enabled']:
                cache_size += fdata['fluidparticlesdensityaverage']['bytes']
            if 'fluidparticleswhitewaterproximity' in fdata and fdata['fluidparticleswhitewaterproximity']['enabled']:
                cache_size += fdata['fluidparticleswhitewaterproximity']['bytes']
            if 'fluidparticlessourceid' in fdata and fdata['fluidparticlessourceid']['enabled']:
                cache_size += fdata['fluidparticlessourceid']['bytes']
            if 'fluidparticlesuid' in fdata and fdata['fluidparticlesuid']['enabled']:
                cache_size += fdata['fluidparticlesuid']['bytes']
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
            try:
                cachedata = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                # JSON file may have become corrupted after a crash.
                # In this case, repair the file by regenerating an
                # empty JSON file and continue with empty stats.
                cachedata = self.repair_corrupt_stats_file(statsfile)

        self.is_cache_info_available = True

        is_surface_enabled = False
        is_preview_enabled = False
        is_surfaceblur_enabled = False
        is_surfacevelocity_enabled = False
        is_surfacespeed_enabled = False
        is_surfacevorticity_enabled = False
        is_surfaceage_enabled = False
        is_surfacelifetime_enabled = False
        is_surfacewhitewaterproximity_enabled = False
        is_surfacecolor_enabled = False
        is_surfacesourceid_enabled = False
        is_surfaceviscosity_enabled = False
        is_surfacedensity_enabled = False
        is_foam_enabled = False
        is_bubble_enabled = False
        is_spray_enabled = False
        is_dust_enabled = False
        is_foamblur_enabled = False
        is_bubbleblur_enabled = False
        is_sprayblur_enabled = False
        is_dustblur_enabled = False
        is_foamvelocity_enabled = False
        is_bubblevelocity_enabled = False
        is_sprayvelocity_enabled = False
        is_dustvelocity_enabled = False
        is_foamid_enabled = False
        is_bubbleid_enabled = False
        is_sprayid_enabled = False
        is_dustid_enabled = False
        is_foamlifetime_enabled = False
        is_bubblelifetime_enabled = False
        is_spraylifetime_enabled = False
        is_dustlifetime_enabled = False
        is_fluid_particles_enabled = False
        is_fluid_particles_id_enabled = False
        is_fluid_particles_velocity_enabled = False
        is_fluid_particles_vorticity_enabled = False
        is_fluid_particles_color_enabled = False
        is_fluid_particles_speed_enabled = False
        is_fluid_particles_age_enabled = False
        is_fluid_particles_lifetime_enabled = False
        is_fluid_particles_viscosity_enabled = False
        is_fluid_particles_density_enabled = False
        is_fluid_particles_density_average_enabled = False
        is_fluid_particles_whitewater_proximity_enabled = False
        is_fluid_particles_source_id_enabled = False
        is_fluid_particles_uid_enabled = False
        is_debug_particles_enabled = False
        is_obstacle_enabled = False
        surface_bytes = 0
        preview_bytes = 0
        surfaceblur_bytes = 0
        surfacevelocity_bytes = 0
        surfacespeed_bytes = 0
        surfacevorticity_bytes = 0
        surfaceage_bytes = 0
        surfacelifetime_bytes = 0
        surfacewhitewaterproximity_bytes = 0
        surfacecolor_bytes = 0
        surfacesourceid_bytes = 0
        surfaceviscosity_bytes = 0
        surfacedensity_bytes = 0
        foam_bytes = 0
        bubble_bytes = 0
        spray_bytes = 0
        dust_bytes = 0
        foamblur_bytes = 0
        bubbleblur_bytes = 0
        sprayblur_bytes = 0
        dustblur_bytes = 0
        foamvelocity_bytes = 0
        bubblevelocity_bytes = 0
        sprayvelocity_bytes = 0
        dustvelocity_bytes = 0
        foamid_bytes = 0
        bubbleid_bytes = 0
        sprayid_bytes = 0
        dustid_bytes = 0
        foamlifetime_bytes = 0
        bubblelifetime_bytes = 0
        spraylifetime_bytes = 0
        dustlifetime_bytes = 0
        fluid_particles_bytes = 0
        fluid_particles_id_bytes = 0
        fluid_particles_velocity_bytes = 0
        fluid_particles_speed_bytes = 0
        fluid_particles_vorticity_bytes = 0
        fluid_particles_color_bytes = 0
        fluid_particles_age_bytes = 0
        fluid_particles_lifetime_bytes = 0
        fluid_particles_viscosity_bytes = 0
        fluid_particles_density_bytes = 0
        fluid_particles_density_average_bytes = 0
        fluid_particles_whitewater_proximity_bytes = 0
        fluid_particles_source_id_bytes = 0
        fluid_particles_uid_bytes = 0
        debug_particles_bytes = 0
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
        average_performance_score = 0
        num_performance_score_frames = 0;
        is_average_performance_score_enabled = False
        for key in cachedata.keys():
            if not key.isdigit():
                continue

            is_data_in_cache = True
            num_cache_frames += 1

            fdata = cachedata[key]
            if 'performance_score' in fdata:
                if fdata['performance_score'] != -1:
                    num_performance_score_frames += 1
                    is_average_performance_score_enabled = True
                    average_performance_score += fdata['performance_score']

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
            if 'surfacevorticity' in fdata and fdata['surfacevorticity']['enabled']: # If statement to support caches without a surfacevorticity entry
                is_surfacevorticity_enabled = True
                surfacevorticity_bytes += fdata['surfacevorticity']['bytes']
            if 'surfaceage' in fdata and fdata['surfaceage']['enabled']: # If statement to support caches without a surfaceage entry
                is_surfaceage_enabled = True
                surfaceage_bytes += fdata['surfaceage']['bytes']
            if 'surfacelifetime' in fdata and fdata['surfacelifetime']['enabled']: # If statement to support caches without a surfacelifetime entry
                is_surfacelifetime_enabled = True
                surfacelifetime_bytes += fdata['surfacelifetime']['bytes']
            if 'surfacewhitewaterproximity' in fdata and fdata['surfacewhitewaterproximity']['enabled']: # If statement to support caches without a surfacewhitewaterproximity entry
                is_surfacewhitewaterproximity_enabled = True
                surfacewhitewaterproximity_bytes += fdata['surfacewhitewaterproximity']['bytes']
            if 'surfacecolor' in fdata and fdata['surfacecolor']['enabled']: # If statement to support caches without a surfacecolor entry
                is_surfacecolor_enabled = True
                surfacecolor_bytes += fdata['surfacecolor']['bytes']
            if 'surfacesourceid' in fdata and fdata['surfacesourceid']['enabled']: # If statement to support caches without a surfacesourceid entry
                is_surfacesourceid_enabled = True
                surfacesourceid_bytes += fdata['surfacesourceid']['bytes']
            if 'surfaceviscosity' in fdata and fdata['surfaceviscosity']['enabled']: # If statement to support caches without a surfaceviscosity entry
                is_surfaceviscosity_enabled = True
                surfaceviscosity_bytes += fdata['surfaceviscosity']['bytes']
            if 'surfacedensity' in fdata and fdata['surfacedensity']['enabled']: # If statement to support caches without a surfacedensity entry
                is_surfacedensity_enabled = True
                surfacedensity_bytes += fdata['surfacedensity']['bytes']
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
            if 'foamvelocity' in fdata and fdata['foamvelocity']['enabled']:
                is_foamvelocity_enabled = True
                foamvelocity_bytes += fdata['foamvelocity']['bytes']
            if 'bubblevelocity' in fdata and fdata['bubblevelocity']['enabled']:
                is_bubblevelocity_enabled = True
                bubblevelocity_bytes += fdata['bubblevelocity']['bytes']
            if 'sprayvelocity' in fdata and fdata['sprayvelocity']['enabled']:
                is_sprayvelocity_enabled = True
                sprayvelocity_bytes += fdata['sprayvelocity']['bytes']
            if 'dustvelocity' in fdata and fdata['dustvelocity']['enabled']:
                is_dustvelocity_enabled = True
                dustvelocity_bytes += fdata['dustvelocity']['bytes']
            if 'foamid' in fdata and fdata['foamid']['enabled']:
                is_foamid_enabled = True
                foamid_bytes += fdata['foamid']['bytes']
            if 'bubbleid' in fdata and fdata['bubbleid']['enabled']:
                is_bubbleid_enabled = True
                bubbleid_bytes += fdata['bubbleid']['bytes']
            if 'sprayid' in fdata and fdata['sprayid']['enabled']:
                is_sprayid_enabled = True
                sprayid_bytes += fdata['sprayid']['bytes']
            if 'dustid' in fdata and fdata['dustid']['enabled']:
                is_dustid_enabled = True
                dustid_bytes += fdata['dustid']['bytes']
            if 'foamlifetime' in fdata and fdata['foamlifetime']['enabled']:
                is_foamlifetime_enabled = True
                foamlifetime_bytes += fdata['foamlifetime']['bytes']
            if 'bubblelifetime' in fdata and fdata['bubblelifetime']['enabled']:
                is_bubblelifetime_enabled = True
                bubblelifetime_bytes += fdata['bubblelifetime']['bytes']
            if 'spraylifetime' in fdata and fdata['spraylifetime']['enabled']:
                is_spraylifetime_enabled = True
                spraylifetime_bytes += fdata['spraylifetime']['bytes']
            if 'dustlifetime' in fdata and fdata['dustlifetime']['enabled']:
                is_dustlifetime_enabled = True
                dustlifetime_bytes += fdata['dustlifetime']['bytes']
            if 'fluidparticles' in fdata and fdata['fluidparticles']['enabled']:
                is_fluid_particles_enabled = True
                fluid_particles_bytes += fdata['fluidparticles']['bytes']
            if 'fluidparticlesid' in fdata and fdata['fluidparticlesid']['enabled']:
                is_fluid_particles_id_enabled = True
                fluid_particles_id_bytes += fdata['fluidparticlesid']['bytes']
            if 'fluidparticlesvelocity' in fdata and fdata['fluidparticlesvelocity']['enabled']:
                is_fluid_particles_velocity_enabled = True
                fluid_particles_velocity_bytes += fdata['fluidparticlesvelocity']['bytes']
            if 'fluidparticlesspeed' in fdata and fdata['fluidparticlesspeed']['enabled']:
                is_fluid_particles_speed_enabled = True
                fluid_particles_speed_bytes += fdata['fluidparticlesspeed']['bytes']
            if 'fluidparticlesvorticity' in fdata and fdata['fluidparticlesvorticity']['enabled']:
                is_fluid_particles_vorticity_enabled = True
                fluid_particles_vorticity_bytes += fdata['fluidparticlesvorticity']['bytes']
            if 'fluidparticlescolor' in fdata and fdata['fluidparticlescolor']['enabled']:
                is_fluid_particles_color_enabled = True
                fluid_particles_color_bytes += fdata['fluidparticlescolor']['bytes']
            if 'fluidparticlesage' in fdata and fdata['fluidparticlesage']['enabled']:
                is_fluid_particles_age_enabled = True
                fluid_particles_age_bytes += fdata['fluidparticlesage']['bytes']
            if 'fluidparticleslifetime' in fdata and fdata['fluidparticleslifetime']['enabled']:
                is_fluid_particles_lifetime_enabled = True
                fluid_particles_lifetime_bytes += fdata['fluidparticleslifetime']['bytes']
            if 'fluidparticlesviscosity' in fdata and fdata['fluidparticlesviscosity']['enabled']:
                is_fluid_particles_viscosity_enabled = True
                fluid_particles_viscosity_bytes += fdata['fluidparticlesviscosity']['bytes']
            if 'fluidparticlesdensity' in fdata and fdata['fluidparticlesdensity']['enabled']:
                is_fluid_particles_density_enabled = True
                fluid_particles_density_bytes += fdata['fluidparticlesdensity']['bytes']
            if 'fluidparticlesdensityaverage' in fdata and fdata['fluidparticlesdensityaverage']['enabled']:
                is_fluid_particles_density_average_enabled = True
                fluid_particles_density_average_bytes += fdata['fluidparticlesdensityaverage']['bytes']
            if 'fluidparticleswhitewaterproximity' in fdata and fdata['fluidparticleswhitewaterproximity']['enabled']:
                is_fluid_particles_whitewater_proximity_enabled = True
                fluid_particles_whitewater_proximity_bytes += fdata['fluidparticleswhitewaterproximity']['bytes']
            if 'fluidparticlessourceid' in fdata and fdata['fluidparticlessourceid']['enabled']:
                is_fluid_particles_source_id_enabled = True
                fluid_particles_source_id_bytes += fdata['fluidparticlessourceid']['bytes']
            if 'fluidparticlesuid' in fdata and fdata['fluidparticlesuid']['enabled']:
                is_fluid_particles_uid_enabled = True
                fluid_particles_uid_bytes += fdata['fluidparticlesuid']['bytes']
            if fdata['particles']['enabled']:
                is_debug_particles_enabled = True
                debug_particles_bytes += fdata['particles']['bytes']
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

        if num_performance_score_frames > 0 and is_average_performance_score_enabled:
            average_performance_score /= num_performance_score_frames
        else:
            is_average_performance_score_enabled = False
            average_performance_score = 0

        self.frame_start, _ = dprops.simulation.get_frame_range()
        self.num_cache_frames = num_cache_frames
        self.is_average_performance_score_enabled = is_average_performance_score_enabled
        self.average_performance_score = int(average_performance_score)

        self.surface_mesh.enabled = is_surface_enabled
        self.preview_mesh.enabled = is_preview_enabled
        self.surfaceblur_mesh.enabled = is_surfaceblur_enabled
        self.surfacevelocity_mesh.enabled = is_surfacevelocity_enabled
        self.surfacespeed_mesh.enabled = is_surfacespeed_enabled
        self.surfacevorticity_mesh.enabled = is_surfacevorticity_enabled
        self.surfaceage_mesh.enabled = is_surfaceage_enabled
        self.surfacelifetime_mesh.enabled = is_surfacelifetime_enabled
        self.surfacewhitewaterproximity_mesh.enabled = is_surfacewhitewaterproximity_enabled
        self.surfacecolor_mesh.enabled = is_surfacecolor_enabled
        self.surfacesourceid_mesh.enabled = is_surfacesourceid_enabled
        self.surfaceviscosity_mesh.enabled = is_surfaceviscosity_enabled
        self.surfacedensity_mesh.enabled = is_surfacedensity_enabled
        self.foam_mesh.enabled = is_foam_enabled
        self.bubble_mesh.enabled = is_bubble_enabled
        self.spray_mesh.enabled = is_spray_enabled
        self.dust_mesh.enabled = is_dust_enabled
        self.foamblur_mesh.enabled = is_foamblur_enabled
        self.bubbleblur_mesh.enabled = is_bubbleblur_enabled
        self.sprayblur_mesh.enabled = is_sprayblur_enabled
        self.dustblur_mesh.enabled = is_dustblur_enabled
        self.foamvelocity_mesh.enabled = is_foamvelocity_enabled
        self.bubblevelocity_mesh.enabled = is_bubblevelocity_enabled
        self.sprayvelocity_mesh.enabled = is_sprayvelocity_enabled
        self.dustvelocity_mesh.enabled = is_dustvelocity_enabled
        self.foamid_mesh.enabled = is_foamid_enabled
        self.bubbleid_mesh.enabled = is_bubbleid_enabled
        self.sprayid_mesh.enabled = is_sprayid_enabled
        self.dustid_mesh.enabled = is_dustid_enabled
        self.foamlifetime_mesh.enabled = is_foamlifetime_enabled
        self.bubblelifetime_mesh.enabled = is_bubblelifetime_enabled
        self.spraylifetime_mesh.enabled = is_spraylifetime_enabled
        self.dustlifetime_mesh.enabled = is_dustlifetime_enabled
        self.fluid_particle_mesh.enabled = is_fluid_particles_enabled
        self.fluid_particle_id_mesh.enabled = is_fluid_particles_id_enabled
        self.fluid_particle_velocity_mesh.enabled = is_fluid_particles_velocity_enabled
        self.fluid_particle_speed_mesh.enabled = is_fluid_particles_speed_enabled
        self.fluid_particle_vorticity_mesh.enabled = is_fluid_particles_vorticity_enabled
        self.fluid_particle_color_mesh.enabled = is_fluid_particles_color_enabled
        self.fluid_particle_age_mesh.enabled = is_fluid_particles_age_enabled
        self.fluid_particle_lifetime_mesh.enabled = is_fluid_particles_lifetime_enabled
        self.fluid_particle_viscosity_mesh.enabled = is_fluid_particles_viscosity_enabled
        self.fluid_particle_density_mesh.enabled = is_fluid_particles_density_enabled
        self.fluid_particle_density_average_mesh.enabled = is_fluid_particles_density_average_enabled
        self.fluid_particle_whitewater_proximity_mesh.enabled = is_fluid_particles_whitewater_proximity_enabled
        self.fluid_particle_source_id_mesh.enabled = is_fluid_particles_source_id_enabled
        self.fluid_particle_uid_mesh.enabled = is_fluid_particles_uid_enabled
        self.debug_particle_mesh.enabled = is_debug_particles_enabled
        self.obstacle_mesh.enabled = is_obstacle_enabled

        self.surface_mesh.bytes.set(surface_bytes)
        self.preview_mesh.bytes.set(preview_bytes)
        self.surfaceblur_mesh.bytes.set(surfaceblur_bytes)
        self.surfacevelocity_mesh.bytes.set(surfacevelocity_bytes)
        self.surfacespeed_mesh.bytes.set(surfacespeed_bytes)
        self.surfacevorticity_mesh.bytes.set(surfacevorticity_bytes)
        self.surfaceage_mesh.bytes.set(surfaceage_bytes)
        self.surfacelifetime_mesh.bytes.set(surfacelifetime_bytes)
        self.surfacewhitewaterproximity_mesh.bytes.set(surfacewhitewaterproximity_bytes)
        self.surfacecolor_mesh.bytes.set(surfacecolor_bytes)
        self.surfacesourceid_mesh.bytes.set(surfacesourceid_bytes)
        self.surfaceviscosity_mesh.bytes.set(surfaceviscosity_bytes)
        self.surfacedensity_mesh.bytes.set(surfacedensity_bytes)
        self.foam_mesh.bytes.set(foam_bytes)
        self.bubble_mesh.bytes.set(bubble_bytes)
        self.spray_mesh.bytes.set(spray_bytes)
        self.dust_mesh.bytes.set(dust_bytes)
        self.foamblur_mesh.bytes.set(foamblur_bytes)
        self.bubbleblur_mesh.bytes.set(bubbleblur_bytes)
        self.sprayblur_mesh.bytes.set(sprayblur_bytes)
        self.dustblur_mesh.bytes.set(dustblur_bytes)
        self.foamvelocity_mesh.bytes.set(foamvelocity_bytes)
        self.bubblevelocity_mesh.bytes.set(bubblevelocity_bytes)
        self.sprayvelocity_mesh.bytes.set(sprayvelocity_bytes)
        self.dustvelocity_mesh.bytes.set(dustvelocity_bytes)
        self.foamid_mesh.bytes.set(foamid_bytes)
        self.bubbleid_mesh.bytes.set(bubbleid_bytes)
        self.sprayid_mesh.bytes.set(sprayid_bytes)
        self.dustid_mesh.bytes.set(dustid_bytes)
        self.foamlifetime_mesh.bytes.set(foamlifetime_bytes)
        self.bubblelifetime_mesh.bytes.set(bubblelifetime_bytes)
        self.spraylifetime_mesh.bytes.set(spraylifetime_bytes)
        self.dustlifetime_mesh.bytes.set(dustlifetime_bytes)
        self.fluid_particle_mesh.bytes.set(fluid_particles_bytes)
        self.fluid_particle_id_mesh.bytes.set(fluid_particles_id_bytes)
        self.fluid_particle_velocity_mesh.bytes.set(fluid_particles_velocity_bytes)
        self.fluid_particle_speed_mesh.bytes.set(fluid_particles_speed_bytes)
        self.fluid_particle_vorticity_mesh.bytes.set(fluid_particles_vorticity_bytes)
        self.fluid_particle_color_mesh.bytes.set(fluid_particles_color_bytes)
        self.fluid_particle_age_mesh.bytes.set(fluid_particles_age_bytes)
        self.fluid_particle_lifetime_mesh.bytes.set(fluid_particles_lifetime_bytes)
        self.fluid_particle_viscosity_mesh.bytes.set(fluid_particles_viscosity_bytes)
        self.fluid_particle_density_mesh.bytes.set(fluid_particles_density_bytes)
        self.fluid_particle_density_average_mesh.bytes.set(fluid_particles_density_average_bytes)
        self.fluid_particle_whitewater_proximity_mesh.bytes.set(fluid_particles_whitewater_proximity_bytes)
        self.fluid_particle_source_id_mesh.bytes.set(fluid_particles_source_id_bytes)
        self.fluid_particle_uid_mesh.bytes.set(fluid_particles_uid_bytes)
        self.debug_particle_mesh.bytes.set(debug_particles_bytes)
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

        total_time = max(total_time, 1e-4)
        self.time_mesh.set_time_pct(     100 * time_mesh      / total_time)
        self.time_advection.set_time_pct(100 * time_advection / total_time)
        self.time_particles.set_time_pct(100 * time_particles / total_time)
        self.time_pressure.set_time_pct( 100 * time_pressure  / total_time)
        self.time_diffuse.set_time_pct(  100 * time_diffuse   / total_time)
        self.time_viscosity.set_time_pct(100 * time_viscosity / total_time)
        self.time_objects.set_time_pct(  100 * time_objects   / total_time)
        self.time_other.set_time_pct(    100 * time_other     / total_time)

        self._update_cache_size(cachedata)

        pressure_enabled = False
        pressure_max_error = 0.0
        pressure_max_error_frame = -1
        pressure_max_iterations = 0
        pressure_max_iterations_frame = -1
        pressure_failures = 0
        pressure_steps = 0
        pressure_max_stress = 0.0
        pressure_max_stress_frame = -1

        viscosity_enabled = False
        viscosity_max_error = 0.0
        viscosity_max_error_frame = -1
        viscosity_max_iterations = 0
        viscosity_max_iterations_frame = -1
        viscosity_failures = 0
        viscosity_steps = 0
        viscosity_max_stress = 0.0
        viscosity_max_stress_frame = -1
        for key in cachedata.keys():
            if not key.isdigit():
                continue

            frameno = int(key)
            fdata = cachedata[key]
            if "pressure_solver_enabled" in fdata:
                pressure_enabled = pressure_enabled or bool(fdata["pressure_solver_enabled"])
                if fdata["pressure_solver_error"] > pressure_max_error:
                    pressure_max_error = fdata["pressure_solver_error"]
                    pressure_max_error_frame = frameno
                if fdata["pressure_solver_iterations"] > pressure_max_iterations:
                    pressure_max_iterations = fdata["pressure_solver_iterations"]
                    pressure_max_iterations_frame = frameno
                if not fdata["pressure_solver_success"]:
                    pressure_failures += 1
                pressure_steps += fdata["substeps"]
                stress = 100.0 * (fdata["pressure_solver_iterations"] / fdata["pressure_solver_max_iterations"])
                if stress > pressure_max_stress:
                    pressure_max_stress = stress
                    pressure_max_stress_frame = frameno

            if "viscosity_solver_enabled" in fdata:
                viscosity_enabled = viscosity_enabled or bool(fdata["viscosity_solver_enabled"])
                if fdata["viscosity_solver_error"] > viscosity_max_error:
                    viscosity_max_error = fdata["viscosity_solver_error"]
                    viscosity_max_error_frame = frameno
                if fdata["viscosity_solver_iterations"] > viscosity_max_iterations:
                    viscosity_max_iterations = fdata["viscosity_solver_iterations"]
                    viscosity_max_iterations_frame = frameno
                if not fdata["viscosity_solver_success"]:
                    viscosity_failures += 1
                viscosity_steps += fdata["substeps"]
                stress = 100.0 * (fdata["viscosity_solver_iterations"] / fdata["viscosity_solver_max_iterations"])
                if stress > viscosity_max_stress:
                    viscosity_max_stress = stress
                    viscosity_max_stress_frame = frameno

        self.pressure_solver_enabled = pressure_enabled
        self.pressure_solver_failures = pressure_failures
        self.pressure_solver_steps = pressure_steps
        self.pressure_solver_max_iterations = pressure_max_iterations
        self.pressure_solver_max_iterations_frame = pressure_max_iterations_frame
        self.pressure_solver_max_error = pressure_max_error
        self.pressure_solver_max_error_frame = pressure_max_error_frame
        self.pressure_solver_max_stress = pressure_max_stress
        self.pressure_solver_max_stress_frame = pressure_max_stress_frame

        self.viscosity_solver_enabled = viscosity_enabled
        self.viscosity_solver_failures = viscosity_failures
        self.viscosity_solver_steps = viscosity_steps
        self.viscosity_solver_max_iterations = viscosity_max_iterations
        self.viscosity_solver_max_iterations_frame = viscosity_max_iterations_frame
        self.viscosity_solver_max_error = viscosity_max_error
        self.viscosity_solver_max_error_frame = viscosity_max_error_frame
        self.viscosity_solver_max_stress = viscosity_max_stress
        self.viscosity_solver_max_stress_frame = viscosity_max_stress_frame


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
            try:
                cachedata = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                # JSON file may have become corrupted after a crash.
                # In this case, repair the file by regenerating an
                # empty JSON file and continue with empty stats.
                cachedata = self.repair_corrupt_stats_file(statsfile)

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
    bpy.utils.register_class(SolverStressProperties)
    bpy.utils.register_class(DomainStatsProperties)


def unregister():
    bpy.utils.unregister_class(ByteProperty)
    bpy.utils.unregister_class(MeshStatsProperties)
    bpy.utils.unregister_class(TimeStatsProperties)
    bpy.utils.unregister_class(SolverStressProperties)
    bpy.utils.unregister_class(DomainStatsProperties)