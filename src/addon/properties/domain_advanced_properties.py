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
from ..utils import version_compatibility_utils as vcu


class DomainAdvancedProperties(bpy.types.PropertyGroup):
    
    min_max_time_steps_per_frame: NewMinMaxIntProperty(
            name_min="Min Substeps",
            description_min="Minimum number of substeps per frame calculation",
            min_min=1, max_min=1000000,
            soft_max_min=100,
            default_min=1,

            name_max="Max Substeps",
            description_max="Maximum number of substeps per frame calculation",
            min_max=1, max_max=1000000,
            soft_max_max=100,
            default_max=24,
            )
    enable_adaptive_obstacle_time_stepping: BoolProperty(
            name="Enable Adaptive Time Stepping for Obstacles",
            description="Include obstacle velocities when calculating number"
                " of frame substeps. Enabling may improve the accuracy of"
                " fluid-solid interaction for fast moving obstacles, but"
                " may take longer to simulate",
            default = False,
            )
    enable_adaptive_force_field_time_stepping: BoolProperty(
            name="Enable Adaptive Time Stepping for Force Fields",
            description="Include force field velocities when calculating number"
                " of frame substeps. Enabling may improve the accuracy of"
                " fluid-forcefield interaction for fast moving force fields, but"
                " will take longer to simulate",
            default = False,
            )
    particle_jitter_factor: FloatProperty(
            name="Particle Jitter",
            description="Amount of random jitter that is added to newly spawned"
                " fluid particles. Higher values may improve simulation accuracy",
            min=0.0, max=1.0,
            default=1.0,
            precision=2,
            subtype='FACTOR',
            )
    jitter_surface_particles: BoolProperty(
            name="Jitter Surface Particles",
            description="If disabled, a random jitter position will only be applied to particles within"
            " the interior of the Inflow/Fluid object shape. If enabled, all emitted particles"
            " will be jittered. Enabling may cause bumpy mesh artifacts on the"
            " initial surface mesh shape and may require additional smoothing."
            " Enabling is recommended for fluid particle effects and results in"
            " more natural particle generation",
            default=False,
            )
    pressure_solver_max_iterations: IntProperty(
            name="Pressure Solver Max Iterations",
            description="Maximum number of iterations that the pressure solver is allowed"
                " to run during a substep. The default value of 900 is often a good choice and does"
                " not need to be changed. See documentation for more information on this setting",
            min=1, soft_max=10000,
            default=900,
            )
    viscosity_solver_max_iterations: IntProperty(
            name="Viscosity Solver Max Iterations",
            description="Maximum number of iterations that the viscosity solver is allowed"
                " to run during a substep. The default value of 900 is often a good choice and does"
                " not need to be changed. See documentation for more information on this setting",
            min=1, soft_max=10000,
            default=900,
            )
    velocity_transfer_method: EnumProperty(
            name="Velocity Transfer Method",
            description="Simulation method to use",
            items=types.velocity_transfer_methods,
            default='VELOCITY_TRANSFER_METHOD_FLIP',
            options={'HIDDEN'},
            )
    PICFLIP_ratio: FloatProperty(
            name="PIC/FLIP Ratio",
            description="Ratio of PIC velocity to FLIP velocity update mixture."
                " PIC velocity method is not very accurate, but stable. FLIP"
                " velocity method is very accurate, but less stable. Using a"
                " value of 0.0 results in a completely FLIP simulator, while"
                " using a value of 1.0 results in a completely PIC simulator",
            min=0.0, max=1.0,
            default=0.05,
            precision=2,
            subtype='FACTOR',
            )
    PICAPIC_ratio: FloatProperty(
            name="PIC/APIC Ratio",
            description="Placeholder",
            min=0.0, max=1.0,
            default=0.00,
            precision=2,
            subtype='FACTOR',
            )
    CFL_condition_number: IntProperty(
            name="Safety Factor (CFL Number)",
            description="Maximum number of voxels that a particle can travel"
                " in a single substep. A larger number may speed up simulation"
                " baking by reducing the number of required substeps at the"
                " cost of simulation accuracy",
            min=1, max=30,
            default=5,
            )
    enable_extreme_velocity_removal: BoolProperty(
            name="Remove particles with extreme velocities",
            description="Attempt to remove extreme particle velocities that"
                " cause the simulator to exceed the maximum number of allowed"
                " frame substeps. Enabling this option may prevent simulation"
                " blow-up in extreme cases. It is not recommended to disable"
                " this option outside of experimentation and testing. Disabling"
                " can result in unstable simulations and/or extreme simulation times",
            default=True,
            )
    enable_gpu_features: BoolProperty(
            name="Enable GPU Features",
            description="Enable simulator to accelerate some computations"
                " with your GPU device. TIP: Compare simulation performance"
                " with this setting on/off to test what is faster on your"
                " hardware setup. Note: you may only notice a difference on"
                " higher resolution simulations",
            default=True
            )
    num_threads_auto_detect: IntProperty(
            name="Threads",
            description="Number of threads to use simultaneously while simulating",
            min=1, max=1024,
            default=1,
            )
    num_threads_fixed: IntProperty(
            name="Threads",
            description="Number of threads to use simultaneously while simulating",
            min=1, max=1024,
            default=4,
            )
    threading_mode: EnumProperty(
            name="Threading Mode",
            description="Determing the amount of simulation threads used",
            items=types.threading_modes,
            default='THREADING_MODE_AUTO_DETECT',
            update=lambda self, context: self.initialize_num_threads_auto_detect(),
            options={'HIDDEN'},
            )
    enable_fracture_optimization: BoolProperty(
            name="Enable Fracture Optimizations",
            description="Enable optimizations when using animated fracture simulations as"
                " FLIP obstacles. These optimizations can greatly improve simulation performance"
                " when there are a large number of small separate FLIP Obstacle objects, such"
                " as in Cell Fracture and RBDLab simulations. Not recommended for fracture simulations"
                " where all pieces are contained within a single FLIP Obstacle as this can harm performance. Enabling"
                " this option can increase memory requirements",
            default = False,
            options={'HIDDEN'},
            )
    enable_asynchronous_meshing: BoolProperty(
            name="Enable Async Meshing",
            description="Run mesh generation process in a separate thread while"
                " the simulation is running. May increase simulation performance"
                " but will use more RAM if enabled",
            default = True,
            )
    precompute_static_obstacles: BoolProperty(
            name="Precompute Static Obstacles",
            description="Precompute data for static obstacles. If enabled,"
                " the simulator will avoid recomputing data for non-animated"
                " obstacles. Increases simulation performance but will use"
                " more RAM if enabled",
            default = True,
            )
    reserve_temporary_grids: BoolProperty(
            name="Reserve Temporary Grid Memory",
            description="Reserve space in memory for temporary grids. Increases"
                " simulation performance for scenes with animated or keyframed"
                " obstacles but will use more RAM if enabled",
            default = True,
            )
    disable_changing_topology_warning: BoolProperty(
            name="Disable Changing Topology Warning",
            description="Disable warning that is displayed when exporting an"
            " animated mesh with changing topology. WARNING: mesh velocity"
            " data cannot be computed for meshes that change topology. This may"
            " result in unexpected object-fluid interaction as these objects will"
            " not be able to push around the fluid",
            default=False,
            options={'HIDDEN'},
            )

    surface_tension_substeps_exceeded_tooltip: BoolProperty(
            name="Warning: Not Enough Max Substeps", 
            description="The estimated number of Surface Tension substeps per frame exceeds the Max Frame"
                " Substeps value. This can cause an unstable simulation. Either decrease the amount of"
                " Surface Tension in the FLIP Fluid World panel to lower the number of required substeps or"
                " increase the number of allowed Max Frame Substeps in the FLIP Fluid Advanced panel", 
            default=True,
            )
    

    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".min_max_time_steps_per_frame",              "Min-Max Time Steps",                 group_id=0)
        add(path + ".enable_adaptive_obstacle_time_stepping",    "Adaptive Obstacle Stepping",         group_id=0)
        add(path + ".enable_adaptive_force_field_time_stepping", "Adaptive Force Field Stepping",      group_id=0)
        add(path + ".particle_jitter_factor",                    "Jitter Factor",                      group_id=0)
        add(path + ".jitter_surface_particles",                  "Jitter Surface Particles",           group_id=0)
        add(path + ".pressure_solver_max_iterations",            "Pressure Solver Iterations",         group_id=0)
        add(path + ".viscosity_solver_max_iterations",           "Viscosity Solver Iterations",        group_id=0)
        add(path + ".velocity_transfer_method",                  "Velocity Transfer Method",           group_id=0)
        add(path + ".PICFLIP_ratio",                             "PIC/FLIP Ratio",                     group_id=0)
        add(path + ".PICAPIC_ratio",                             "PIC/APIC Ratio",                     group_id=0)
        add(path + ".CFL_condition_number",                      "CFL",                                group_id=0)
        add(path + ".enable_extreme_velocity_removal",           "Enable Extreme Velocity Removal",    group_id=0)
        add(path + ".enable_gpu_features",                       "Enable GPU Features",                group_id=1)
        add(path + ".threading_mode",                            "Threading Mode",                     group_id=1)
        add(path + ".num_threads_fixed",                         "Num Threads (fixed)",                group_id=1)
        add(path + ".enable_asynchronous_meshing",               "Async Meshing",                      group_id=1)
        add(path + ".enable_fracture_optimization",              "Enable Fracture Optimization",        group_id=1)
        add(path + ".precompute_static_obstacles",               "Precompute Static Obstacles",        group_id=1)
        add(path + ".reserve_temporary_grids",                   "Reserve Temporary Grid Memory",      group_id=1)
        add(path + ".disable_changing_topology_warning",         "Disable Changing Topology Warning",  group_id=1)


    def initialize(self):
        self.initialize_num_threads_auto_detect()


    def load_post(self):
        self.initialize_num_threads_auto_detect()
        

    def initialize_num_threads_auto_detect(self):
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