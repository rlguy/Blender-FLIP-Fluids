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

from .utils import version_compatibility_utils as vcu


def object_types(self, context):
    return object_types_mesh

object_types_mesh = (
    ('TYPE_NONE',        "None",        "", 0),
    ('TYPE_DOMAIN',      "Domain",      "Bounding box of this object represents the computational domain of the fluid simulation", 1),
    ('TYPE_FLUID',       "Fluid",       "Object represents a volume of fluid in the simulation", 2),
    ('TYPE_OBSTACLE',    "Obstacle",    "Object represents an obstacle", 3),
    ('TYPE_INFLOW',      "Inflow",      "Object adds fluid to the simulation", 4),
    ('TYPE_OUTFLOW',     "Outflow",     "Object removes fluid from the simulation", 5),
    ('TYPE_FORCE_FIELD', "Force Field", "Object acts as a force field to push fluid within the simulation", 6)
    )

object_types_empty = (
    ('TYPE_NONE',        "None",        "", 0),
    ('TYPE_FORCE_FIELD', "Force Field", "Object acts as a force field to push fluid within the simulation", 6)
    )

motion_filter_types = (
    ('MOTION_FILTER_TYPE_ALL',       "All",       "Select all object animation types: static, keyframed, and animated."),
    ('MOTION_FILTER_TYPE_STATIC',    "Static",    "Select only static objects. Objects that do not move"),
    ('MOTION_FILTER_TYPE_KEYFRAMED', "Keyframed", "Select only keyframed objects. Objects with keyframed location/rotation/scale or f-curves"),
    ('MOTION_FILTER_TYPE_ANIMATED',  "Animated",  "Select only animated objects. Objects with complex motion such as animation through parenting or armatures. These objects must be marked as animated in their object settings.")
)

force_field_types = (
    ('FORCE_FIELD_TYPE_POINT',        "Point Force",                                   "Force field directed towards a single point", 'EMPTY_AXIS', 0),
    ('FORCE_FIELD_TYPE_SURFACE',      "Surface Force",                                 "Force field directed towards an object's surface", 'OUTLINER_DATA_SURFACE', 1),
    ('FORCE_FIELD_TYPE_VOLUME',       "Volume Force",                                  "Force field directed to fill an object's volume", 'MESH_MONKEY', 2),
    ('FORCE_FIELD_TYPE_CURVE',        "Curve Guide Force",                             "Force field directed along a curve object", 'FORCE_CURVE', 3),
    )

force_field_resolution_modes = (
    ('FORCE_FIELD_RESOLUTION_LOW',    "Low",    "Low resolution force field grid. Domain resolution divided by 4."),
    ('FORCE_FIELD_RESOLUTION_NORMAL', "Medium", "Medium resolution force field grid. Domain resolution divided by 3."),
    ('FORCE_FIELD_RESOLUTION_HIGH',   "High",   "High resolution force field grid. Domain resolution divided by 2."),
    ('FORCE_FIELD_RESOLUTION_ULTRA',  "Ultra",  "Very high resolution force field grid. Matches domain resolution."),
    )

force_field_falloff_shapes = (
    ('FORCE_FIELD_FALLOFF_SPHERE', "Sphere", "Field strength falloff is uniform is all directions, as in a sphere"),
    ('FORCE_FIELD_FALLOFF_TUBE',   "Tube",   "Field strength falloff results in a tube-shaped force field. Direction of the tube uses the object local Z-axis."),
    ('FORCE_FIELD_FALLOFF_CONE',   "Cone",   "Field strength falloff results in a cone-shaped force field. Direction of the cone uses the object local Z-axis."),
    )

frame_range_modes = (
    ('FRAME_RANGE_TIMELINE', "Timeline", "Use the start and end frame range from the timeline"),
    ('FRAME_RANGE_CUSTOM',   "Custom",   "Use a custom start and end frame range")
    )

frame_rate_modes = (
    ('FRAME_RATE_MODE_SCENE',  "Scene",  "Use the frame rate specified in the scene render properties"),
    ('FRAME_RATE_MODE_CUSTOM', "Custom", "Use a custom frame rate")
    )

time_scale_modes = (
    ('TIME_SCALE_MODE_RIGID_BODY', "Rigid",  "Use the simulation time scale specified in the rigid body world."),
    ('TIME_SCALE_MODE_SOFT_BODY',  "Soft",   "Use the simulation time scale specified in the object softbody modifier."),
    ('TIME_SCALE_MODE_CLOTH',      "Cloth",  "Use the simulation time scale specified in the object cloth modifier."),
    ('TIME_SCALE_MODE_FLUID',      "Fluid",  "Use the simulation time scale specified in the Blender Mantaflow domain object fluid modifier."),
    ('TIME_SCALE_MODE_CUSTOM',     "Custom", "Use a custom simulation time scale.")
    )

simulation_playback_mode = (
    ('PLAYBACK_MODE_TIMELINE',       "Timeline",       "Use the current timeline frame for simulation playback"),
    ('PLAYBACK_MODE_OVERRIDE_FRAME', "Override Frame", "Use a custom frame for simulation playback instead of the current timeline frame. TIP: the overridden frame value can be keyframed for complex control of playback"),
    ('PLAYBACK_MODE_HOLD_FRAME',     "Hold Frame",     "Hold a frame in place, regardless of timeline position")
    )

frame_offset_types = (
    ('OFFSET_TYPE_TIMELINE', "Timeline Frame", "Trigger fluid object at frame in timeline"),
    ('OFFSET_TYPE_FRAME',    "Frame Offset",   "Trigger fluid object at a frame offset from start of the simulation")
    )

fluid_velocity_modes = (
    ('FLUID_VELOCITY_MANUAL', "Manual", "Set fluid velocity vector manually."),
    ('FLUID_VELOCITY_AXIS',   "Axis",   "Set fluid velocity in direction of the object's local X/Y/Z axis."),
    ('FLUID_VELOCITY_TARGET', "Target", "Set fluid velocity vector towards a target object.")
    )

inflow_velocity_modes = (
    ('INFLOW_VELOCITY_MANUAL', "Vector", "Set inflow velocity vector manually."),
    ('INFLOW_VELOCITY_AXIS',   "Axis",   "Set inflow velocity in direction of the object's local X/Y/Z axis."),
    ('INFLOW_VELOCITY_TARGET', "Target", "Set inflow velocity vector towards a target object.")
    )

local_axis_directions = (
    ('LOCAL_AXIS_POS_X', "+X", "Direction of object's local +X axis."),
    ('LOCAL_AXIS_POS_Y', "+Y", "Direction of object's local +Y axis."),
    ('LOCAL_AXIS_POS_Z', "+Z", "Direction of object's local +Z axis."),
    ('LOCAL_AXIS_NEG_X', "−X", "Direction of object's local −X axis."),
    ('LOCAL_AXIS_NEG_Y', "−Y", "Direction of object's local −Y axis."),
    ('LOCAL_AXIS_NEG_Z', "−Z", "Direction of object's local −Z axis.")
    )

mesh_types = (
    ('MESH_TYPE_RIGID',  "Rigid",      "Mesh shape does not change/deform during animation."),
    ('MESH_TYPE_DEFORM', "Deformable", "Mesh shape changes/deforms during animation. Slower to calculate, only use if really necessary.")
    )

display_modes = (
    ('DISPLAY_FINAL',   "Final",   "Display final quality results"),
    ('DISPLAY_PREVIEW', "Preview", "Display preview quality results"),
    ('DISPLAY_NONE',    "None",    "Display nothing")
    )

whitewater_view_settings_modes = (
    ('VIEW_SETTINGS_WHITEWATER',        "Whitewater",             "Adjust view settings for all whitewater particles"),
    ('VIEW_SETTINGS_FOAM_BUBBLE_SPRAY', "Foam Bubble Spray Dust", "Adjust view settings for foam, bubble, spray, and particles separately")
    )

whitewater_object_settings_modes = (
    ('WHITEWATER_OBJECT_SETTINGS_WHITEWATER',        "Whitewater",             "Adjust particle object settings for all whitewater particles"),
    ('WHITEWATER_OBJECT_SETTINGS_FOAM_BUBBLE_SPRAY', "Foam Bubble Spray Dust", "Adjust particle object settings for foam, bubble, spray, and dust particles separately")
    )

whitewater_particle_object_modes = (
    ('WHITEWATER_PARTICLE_ICOSPHERE',   "Icosphere",    "Render whitewater particles as a 20 sided icosphere"),
    ('WHITEWATER_PARTICLE_CUBE',        "Cube",         "Render whitewater particles as a 6 sided cube"),
    ('WHITEWATER_PARTICLE_CUSTOM',      "Custom",       "Render whitewater particles as a custom blender object")
    )

whitewater_ui_modes = (
    ('WHITEWATER_UI_MODE_BASIC',    "Basic",    "Display only the basic and most important whitewater simulation parameters"),
    ('WHITEWATER_UI_MODE_ADVANCED', "Advanced", "Display all whitewater simulation parameters. Advanced settings will be highlighted in red by default. For most simulations, you will not need to change these settings from their defaults.")
    )

cache_info_modes = (
    ('CACHE_INFO', "Cache Info", "Display info about the entire simulation cache"),
    ('FRAME_INFO', "Frame Info", "Display info about a single simulation frame")
    )

csv_regions = (
    ('CSV_REGION_US',  "US",  "US format - Decimals in numbers (1.23), commas to separate values"),
    ('CSV_REGION_EUR', "EUR", "European format - Commas in numbers (1,23); semicolons to separate values")
    )

boundary_behaviours = (
    ('BEHAVIOUR_KILL',      "Kill",      "Kill any foam particles when outside boundary limits"),
    ('BEHAVIOUR_BALLISTIC', "Ballistic", "Make foam particles follow ballistic trajectory"),
    ('BEHAVIOUR_COLLIDE',   "Collide",   "Collide with boundary limits")
    )

boundary_collisions_modes = (
    ('BOUNDARY_COLLISIONS_MODE_INHERIT', "Inherit", "Use the same boundary collisions as set in the FLIP Fluid Simulation panel"),
    ('BOUNDARY_COLLISIONS_MODE_CUSTOM',  "Custom",  "Set custom boundary collisions for each whitewater particle type")
    )

world_scale_mode = (
    ('WORLD_SCALE_MODE_RELATIVE',  "Relative", "Set the physics scale of the domain relative to the size of a Blender Unit"),
    ('WORLD_SCALE_MODE_ABSOLUTE',  "Absolute", "Set the physics scale of the domain by specifying the size of the longest side of the domain")
    )

gravity_types = (
    ('GRAVITY_TYPE_SCENE',  "Scene",  "Use scene gravity values"),
    ('GRAVITY_TYPE_CUSTOM', "Custom", "Use custom gravity values")
    )

surface_compute_chunk_modes = (
    ('COMPUTE_CHUNK_MODE_AUTO',  "Auto",  "Automatically determine the number of compute chunks, based on meshing grid dimensions"),
    ('COMPUTE_CHUNK_MODE_FIXED', "Fixed", "Manually determine the number of compute chunks")
    )

meshing_volume_modes = (
    ('MESHING_VOLUME_MODE_DOMAIN',  "Domain Volume", "Mesh all fluid that is inside of the domain."),
    ('MESHING_VOLUME_MODE_OBJECT',  "Object Volume", "Mesh only fluid that is inside of a custom object.")
    )

obstacle_meshing_modes = (
    ('MESHING_MODE_INSIDE_SURFACE',  "Inside Surface",  "Generate fluid-solid interface on the inside of the obstacle. Fluid surface will penetrate the obstacle."),
    ('MESHING_MODE_ON_SURFACE',      "On Surface",      "Generate fluid-solid interface directly on the obstacle surface. May lead to rendering artifacts."),
    ('MESHING_MODE_OUTSIDE_SURFACE', "Outside Surface", "Generate fluid-solid interface on the outside of the obstacle. Leaves a gap between the fluid surface and obstacle.")
    )

velocity_transfer_methods = (
    ('VELOCITY_TRANSFER_METHOD_FLIP', "FLIP", "Choose FLIP for high energy, noisy, and chaotic simulations. Generally better for large scale simulations where noisy splashes are desirable."),
    ('VELOCITY_TRANSFER_METHOD_APIC', "APIC", "Choose APIC for high vorticity, swirly, and stable simulations. Generally better for small scale simulations where reduced surface noise is desirable or for viscous simulations.")
    )

surface_tension_solver_methods = (
    ('SURFACE_TENSION_SOLVER_METHOD_REGULAR', "Regular", "Choose for general purpose surface tension effects."),
    ('SURFACE_TENSION_SOLVER_METHOD_SMOOTH',  "Smooth",  "Choose for improved stability and smoother results in small-scale surface tension effects. Good for thin streams/strands of liquid and for high surface tension effects. Not recommended for highly chaotic liquid motion or large volumes of liquid as this can result in volume increase issues.")
    )

threading_modes = (
    ('THREADING_MODE_AUTO_DETECT', "Auto-detect", "Use the maximum number of threads available on the CPU for the simulation. Tip: Running smaller low resolution simulations with too many threads may actually harm performance due to overhead of thread management - this mode may be more performant for running medium to high resolution simulations."),
    ('THREADING_MODE_FIXED',       "Fixed",       "Use a specified fixed number of threads for the simulation. TIP: Running smaller low resolution simulations with less threads may boost baking speed due to reducing overhead from thread management - try values around 4 threads for default lower resolution simulations.")
    )


grid_display_modes = (
    ('GRID_DISPLAY_SIMULATION',  "Simulation Grid",   "Display the domain simulation grid"),
    ('GRID_DISPLAY_MESH',        "Final Mesh Grid",   "Display the domain surface mesh grid"),
    ('GRID_DISPLAY_PREVIEW',     "Preview Mesh Grid", "Display the domain surface preview mesh grid"),
    )

grid_display_modes = (
    ('GRID_DISPLAY_SIMULATION',  "Simulation Grid",   "Display the domain simulation grid"),
    ('GRID_DISPLAY_MESH',        "Final Mesh Grid",   "Display the domain surface mesh grid"),
    ('GRID_DISPLAY_PREVIEW',     "Preview Mesh Grid", "Display the domain surface preview mesh grid"),
    ('GRID_DISPLAY_FORCE_FIELD', "Force Field Grid",  "Display the domain force field grid"),
    )

gradient_interpolation_modes = (
    ('GRADIENT_NONE', "No Gradient",  "Do not interpolate between colors"),
    ('GRADIENT_RGB',  "RGB Gradient", "Interpolate between colors in RGB colorspace"),
    ('GRADIENT_HSV',  "HSV Gradient", "Interpolate between colors in HSV colorspace"),
    )

material_types = (
    ('MATERIAL_TYPE_SURFACE',    "Surface",    "Material suitable for surface mesh"),
    ('MATERIAL_TYPE_WHITEWATER', "Whitewater", "Material suitable for whitewater mesh"),
    ('MATERIAL_TYPE_ALL',        "All",        "Material suitable for any mesh"),
    )

cmd_render_mode = (
    ('CMD_RENDER_MODE_NORMAL', "Normal", "Launch normal command line render. This is equivalent to executing the 'Launch Render' operator."),
    ('CMD_RENDER_MODE_BATCH',  "Batch",  "Launch batch file command line render. This is equivalent to executing the 'Generate Batch File' operator followed by the 'Launch Batch File Render' operator."),
    )

color_mixing_modes = (
    ('COLOR_MIXING_MODE_RGB',    "RGB",    "Simulate color mixing using basic additive RGB blending."),
    ('COLOR_MIXING_MODE_MIXBOX', "Mixbox", "(recommended) Simulate color mixing using the physically accurate Mixbox pigment blending technology. Requires installation of the FLIP Fluids Mixbox plugin."),
    )

preset_library_install_modes = (
    ('PRESET_LIBRARY_INSTALL_ZIP',    "Install Preset Library Zip File",        "Install the Preset Library zip file to a location of your choice. Choose this option for installing or updating to new preset library versions."),
    ('PRESET_LIBRARY_INSTALL_FOLDER', "Install Existing Preset Library Folder", "Install an existing Preset Library folder. Choose this option to select a preset library that was already installed in another version of Blender."),
    )

domain_settings_panel = (
    ('DOMAIN_SETTINGS_PANEL_SIMULATION', "Simulation", "Grid resolution, simulation method, world scale, frame rate, and time scale settings"),
    ('DOMAIN_SETTINGS_PANEL_CACHE',      "Cache",      "Cache directory location settings"),
    ('DOMAIN_SETTINGS_PANEL_DISPLAY',    "Display",    "Viewport display and render display settings"),
    ('DOMAIN_SETTINGS_PANEL_SURFACE',    "Surface",    "Surface mesh generation and surface attribute settings"),
    ('DOMAIN_SETTINGS_PANEL_WHITEWATER', "Whitewater", "Whitewater simulation and whitewater attribute settings"),
    ('DOMAIN_SETTINGS_PANEL_WORLD',      "World",      "World scale, gravity and forcefield, viscosity, surface tension, sheeting effects, and friction settings"),
    ('DOMAIN_SETTINGS_PANEL_MATERIALS',  "Materials",  "Surface and whitewater material library settings"),
    ('DOMAIN_SETTINGS_PANEL_ADVANCED',   "Advanced",   "Frame substeps, simulation method, simulation stability, and multithreading settings"),
    ('DOMAIN_SETTINGS_PANEL_DEBUG',      "Debug",      "Grid visualization, particle debugging, force field debugging, and obstacle debugging settings"),
    ('DOMAIN_SETTINGS_PANEL_STATS',      "Stats",      "View cache and frame stats of the simulation cache")
    )

measurement_units_mode = (
    ('MEASUREMENT_UNITS_MODE_METRIC',   "Metric",   "Display measurements in metric units"),
    ('MEASUREMENT_UNITS_MODE_IMPERIAL', "Imperial", "Display measurements in imperial units")
    )