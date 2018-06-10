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

import bpy, os
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from .custom_properties import NewMinMaxIntProperty
from .. import types


class DomainAdvancedProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.min_max_time_steps_per_frame = NewMinMaxIntProperty(
                name_min="Min Substeps",
                description_min="Minimum number of substeps per frame calculation",
                min_min=1, max_min=100,
                default_min=1,

                name_max="Max Substeps",
                description_max="Maximum number of substeps per frame calculation",
                min_max=1, max_max=100,
                default_max=8,
                )
        cls.enable_adaptive_obstacle_time_stepping = BoolProperty(
                name="Enable Adaptive Time Stepping for Obstacles",
                description="Include obstacle velocities when calculating number"
                    " of frame substeps. Enabling may improve the accuracy of"
                    " fluid-solid interaction for fast moving obstacles.",
                default = False,
                )
        cls.particle_jitter_factor = FloatProperty(
                name="Particle Jitter",
                description="Amount of random jitter that is added to newly spawned"
                    " fluid particles. Higher values may improve simulation accuracy,"
                    " but may cause 'bumpy' artifacts in the initial mesh shape.",
                min=0.0, max=1.0,
                default=1.0,
                precision=2,
                subtype='FACTOR',
                )
        cls.PICFLIP_ratio = FloatProperty(
                name="PIC/FLIP Ratio",
                description="Ratio of PIC velocity to FLIP velocity update mixture."
                    " PIC velocity method is not very accurate, but stable. FLIP"
                    " velocity method is very accurate, but less stable. Using a"
                    " value of 0.0 results in a completely FLIP simulator, while"
                    " using a value of 1.0 results in a completely PIC simulator.",
                min=0.0, max=1.0,
                default=0.05,
                precision=2,
                subtype='FACTOR',
                )
        cls.CFL_condition_number = IntProperty(
                name="Safety Factor (CFL Number)",
                description="Maximum number of grid cells a particle can travel"
                    " in a single substep. A larger number may speed up simulation"
                    " baking by reducing the number of required substeps at the"
                    " cost of accuracy.",
                min=1, max=50,
                default=5,
                )
        cls.enable_extreme_velocity_removal = BoolProperty(
                name="Remove particles with extreme velocities",
                description="Attempt to remove extreme particle velocities that"
                    " cause the simulator to exceed the maximum number of allowed"
                    " frame substeps. Enabling this option may prevent simulation"
                    " blow-up in extreme cases. Disable this option if fast moving"
                    " fluid is disappearing from the simulation domain.",
                default=True,
                )
        cls.enable_gpu_features = BoolProperty(
                name="Enable GPU Features",
                description="Enable simulator to accelerate some computations"
                    " with your GPU device. TIP: Compare simulation performance"
                    " with this setting on/off to test what is faster on your"
                    " hardware setup. Note: you may only notice a difference on"
                    " higher resolution simulations.",
                default=True
                )
        cls.num_threads_auto_detect = IntProperty(
                name="Threads",
                description="Number of threads to use simultaneously while simulating",
                min=1, max=1024,
                default=1,
                )
        cls.num_threads_fixed = IntProperty(
                name="Threads",
                description="Number of threads to use simultaneously while simulating",
                min=1, max=1024,
                default=1,
                )
        cls.threading_mode = EnumProperty(
                name="Threading Mode",
                description="Determing the amount of simulation threads used",
                items=types.threading_modes,
                default='THREADING_MODE_AUTO_DETECT',
                options={'HIDDEN'},
                )
        cls.enable_asynchronous_meshing = BoolProperty(
                name="Enable Async Meshing",
                description="Run mesh generation process in a separate thread while"
                    " the simulation is running. May increase simulation performance"
                    " but will use more RAM if enabled.",
                default = True,
                )
        cls.precompute_static_obstacles = BoolProperty(
                name="Precompute Static Obstacles",
                description="Precompute data for static obstacles. If enabled,"
                    " the simulator will avoid recomputing data for non-animated"
                    " obstacles. Increases simulation performance but will use"
                    " more RAM if enabled.",
                default = True,
                )
        cls.reserve_temporary_grids = BoolProperty(
                name="Reserve Temporary Grid Memory",
                description="Reserve space in memory for temporary grids. Increases"
                    " simulation performance for scenes with animated or keyframed"
                    " obstacles but will use more RAM if enabled.",
                default = True,
                )
        cls.experimental_optimization_features = BoolProperty(
                name="Enable Experimental Optimization Features",
                description="Enable features that may boost performance. Compare"
                    " simulation performance with this setting on/off to test"
                    " what is faster on your hardware setup. Note: you may only"
                    " notice a difference on higher resolution simulations.",
                default = True,
                )


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".min_max_time_steps_per_frame",           "Min-Max Time Steps",                 group_id=0)
        add(path + ".enable_adaptive_obstacle_time_stepping", "Adaptive Obstacle Stepping",         group_id=0)
        add(path + ".particle_jitter_factor",                 "Jitter Factor",                      group_id=0)
        add(path + ".PICFLIP_ratio",                          "PIC/FLIP Ratio",                     group_id=0)
        add(path + ".CFL_condition_number",                   "CFL",                                group_id=0)
        add(path + ".enable_extreme_velocity_removal",        "Enable Extreme Velocity Removal",    group_id=0)
        add(path + ".enable_gpu_features",                    "Enable GPU Features",                group_id=1)
        add(path + ".threading_mode",                         "Threading Mode",                     group_id=1)
        add(path + ".num_threads_fixed",                      "Num Threads (fixed)",                group_id=1)
        add(path + ".enable_asynchronous_meshing",            "Async Meshing",                      group_id=1)
        add(path + ".precompute_static_obstacles",            "Precompute Static Obstacles",        group_id=1)
        add(path + ".reserve_temporary_grids",                "Reserve Temporary Grid Memory",      group_id=1)
        add(path + ".experimental_optimization_features",     "Experimental Optimization Features", group_id=1)


    def initialize(self):
        self._initialize_num_threads_auto_detect()


    def load_post(self):
        self._initialize_num_threads_auto_detect()
        

    def _initialize_num_threads_auto_detect(self):
        original_threads_mode = bpy.context.scene.render.threads_mode
        bpy.context.scene.render.threads_mode = 'AUTO'
        self.num_threads_auto_detect = bpy.context.scene.render.threads
        bpy.context.scene.render.threads_mode = original_threads_mode


    def _update_min_time_steps_per_frame(self, context):
        if self.min_time_steps_per_frame > self.max_time_steps_per_frame:
            self.max_time_steps_per_frame = self.min_time_steps_per_frame

    def _update_max_time_steps_per_frame(self, context):
        if self.max_time_steps_per_frame < self.min_time_steps_per_frame:
            self.min_time_steps_per_frame = self.max_time_steps_per_frame



def register():
    bpy.utils.register_class(DomainAdvancedProperties)


def unregister():
    bpy.utils.unregister_class(DomainAdvancedProperties)