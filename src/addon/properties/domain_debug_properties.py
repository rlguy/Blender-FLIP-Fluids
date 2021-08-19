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

import bpy, os, sys, platform
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        CollectionProperty
        )

from .custom_properties import (
        NewMinMaxFloatProperty
        )

from .. import (
        types,
        bake
        )

from ..operators import draw_grid_operators
from ..operators import draw_particles_operators
from ..operators import draw_force_field_operators
from ..utils import version_compatibility_utils as vcu


class VersionHistoryItem(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    blender_version = StringProperty(default="-1"); exec(conv("blender_version"))
    flip_fluids_version = StringProperty(default="-1"); exec(conv("flip_fluids_version"))
    flip_fluids_label = StringProperty(default="-1"); exec(conv("flip_fluids_label"))
    operating_system = StringProperty(default="-1"); exec(conv("operating_system"))


    def get_info_string(self):
        return self.blender_version + "\t" + self.flip_fluids_version + "\t" + self.flip_fluids_label + "\t" + self.operating_system


class DomainDebugProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    display_simulation_grid = BoolProperty(
            name="Display Domain Grid",
            description="Visualize the domain voxel grid in the 3D viewport."
                " Try scaling different sides of the domain to better understand how the grid works."
                " Try enabling the Lock Cell Size option in the FLIP Fluid Simulation panel and compare"
                " the differences in how the grid changes as the domain is resized.",
            default=False,
            update=lambda self, context: self._update_display_simulation_grid(context),
            ); exec(conv("display_simulation_grid"))
    grid_display_mode = EnumProperty(
            name="Grid Display Mode",
            description="Type of grid debug info to display",
            items=types.grid_display_modes,
            default='GRID_DISPLAY_SIMULATION',
            update=lambda self, context: self._update_debug_grid_geometry(context),
            ); exec(conv("grid_display_mode"))
    grid_display_scale = IntProperty(
            name="Grid Display Scale",
            description="Number of grid cells that a single grid cell in the"
                " viewport represents",
            min = 1, soft_max = 10,
            default=1,
            step=1,
            update=lambda self, context: self._update_debug_grid_geometry(context),
            ); exec(conv("grid_display_scale"))
    enabled_debug_grids = BoolVectorProperty(
            name="Enabled Debug Grids",
            description="Select which debug grids are displayed in the viewport",
            default=(True, True, True),
            size=3,
            subtype='XYZ',
            update=lambda self, context: self._update_debug_grid_geometry(context),
            ); exec(conv("enabled_debug_grids"))
    x_grid_color = FloatVectorProperty(  
           name="X Grid Color",
           subtype='COLOR',
           default=(0.5, 0.0, 0.0),
           min=0.0, max=1.0,
           description="X grid display color"
           ); exec(conv("x_grid_color"))
    y_grid_color = FloatVectorProperty(  
           name="Y Grid Color",
           subtype='COLOR',
           default=(0.0, 0.5, 0.0),
           min=0.0, max=1.0,
           description="Y grid display color"
           ); exec(conv("y_grid_color"))
    z_grid_color = FloatVectorProperty(  
           name="Z Grid Color",
           subtype='COLOR',
           default=(0.0, 0.0, 0.5),
           min=0.0, max=1.0,
           description="Z grid display color"
           ); exec(conv("z_grid_color"))
    debug_grid_offsets = FloatVectorProperty(
            name="Debug Grid Offsets",
            description="Offset at which an axis' grid is displayed in the viewport",
            min = 0.0, max = 1.0,
            default=(0.0, 0.0, 0.0),
            size=3,
            step=1,
            subtype='XYZ',
            update=lambda self, context: self._update_debug_grid_geometry(context),
            ); exec(conv("debug_grid_offsets"))
    snap_offsets_to_grid = BoolProperty(
            name="Snap Offsets to Grid",
            description="Align debug grids to gridcell locations",
            default=True,
            update=lambda self, context: self._update_debug_grid_geometry(context),
            ); exec(conv("snap_offsets_to_grid"))
    display_domain_bounds = BoolProperty(
            name="Display Bounds",
            description="Display the true bounds of the domain object." + 
                " The domain boundary contains a thin solid layer. Enabling" + 
                " this visualization will display the actual fluid region of" + 
                " the domain",
            default=False,
            update=lambda self, context: self._update_display_domain_bounds(context),
            ); exec(conv("display_domain_bounds"))
    domain_bounds_color = FloatVectorProperty(  
           name="Domain Bounds Color",
           subtype='COLOR',
           default=(1.0, 1.0, 0.0),
           min=0.0, max=1.0,
           description="Color of the domain bounds visualization",
           update=lambda self, context: self._update_debug_grid_geometry(context),
           ); exec(conv("domain_bounds_color"))

    export_fluid_particles = BoolProperty(
            name="Enable Fluid Particle Debugging",
            description="Enable to export simulator fluid particle data and to"
                " visualize and debug problems with fluid behaviour. Enable"
                " this option before baking a simulation to use this feature",
            default=False,
            update=lambda self, context: self._update_export_fluid_particles(context),
            ); exec(conv("export_fluid_particles"))
    fluid_particles_visibility = BoolProperty(
            name="Fluid Particle Visibility",
            description="Show fluid particles in the viewport",
            default=True,
            update=lambda self, context: self._update_export_fluid_particles(context),
            ); exec(conv("fluid_particles_visibility"))
    low_speed_particle_color = FloatVectorProperty(  
           name="Low Speed Color",
           subtype='COLOR',
           default=(0.0, 0.0, 1.0),
           min=0.0, max=1.0,
           description="Color for low velocity fluid particles",
           update=lambda self, context: self._update_debug_particle_geometry(context),
           ); exec(conv("low_speed_particle_color"))
    high_speed_particle_color = FloatVectorProperty(  
           name="High Speed Color",
           subtype='COLOR',
           default=(1.0, 1.0, 1.0),
           min=0.0, max=1.0,
           description="Color for high velocity fluid particles",
           update=lambda self, context: self._update_debug_particle_geometry(context),
           ); exec(conv("high_speed_particle_color"))
    min_gradient_speed = FloatProperty(
            name="Low Color Speed", 
            description="Low speed value for visualizing fluid particle velocity", 
            min=0,
            default=0.0,
            precision=2,
            update=lambda self, context: self._update_min_gradient_speed(context),
            ); exec(conv("min_gradient_speed"))
    max_gradient_speed = FloatProperty(
            name="High Color Speed", 
            description="High speed value for visualizing fluid particle velocity", 
            min=0,
            default=5.0,
            precision=2,
            update=lambda self, context: self._update_max_gradient_speed(context),
            ); exec(conv("max_gradient_speed"))
    fluid_particle_gradient_mode = EnumProperty(
            name="Gradient Mode",
            description="Type of color gradient",
            items=types.gradient_interpolation_modes,
            default='GRADIENT_RGB',
            update=lambda self, context: self._update_max_gradient_speed(context),
            ); exec(conv("fluid_particle_gradient_mode"))
    particle_size = IntProperty(
            name="Particle Size", 
            description="Size to draw particles for visualization", 
            min=1, soft_max=10,
            default=1,
            update=lambda self, context: self._update_debug_particle_geometry(context),
            ); exec(conv("particle_size"))
    particle_draw_aabb = PointerProperty(
            name="Visualization Bounds", 
            description="If set, only particles inside the object's axis-aligned"
                " bounding box will be drawn",
            type=bpy.types.Object,
            update=lambda self, context: self._update_debug_particle_geometry(context),
            ); exec(conv("particle_draw_aabb"))

    export_force_field = BoolProperty(
            name="Enable Force Field Debugging",
            description="Enable to export simulator force field data and to"
                " visualize force field lines. Enable this option before baking"
                " a simulation to use this feature",
            default=False,
            update=lambda self, context: self._update_export_force_field(context),
            ); exec(conv("export_force_field"))
    force_field_visibility = BoolProperty(
            name="Force Field Visibility",
            description="Show force fields in the viewport",
            default=True,
            update=lambda self, context: self._update_export_force_field(context),
            ); exec(conv("force_field_visibility"))
    low_force_field_color = FloatVectorProperty(  
           name="Low Force Color",
           subtype='COLOR',
           default=(1.0, 1.0, 1.0),
           min=0.0, max=1.0,
           description="Color for low strength forces",
           update=lambda self, context: self._update_export_force_field(context),
           ); exec(conv("low_force_field_color"))
    high_force_field_color = FloatVectorProperty(  
           name="High Force Color",
           subtype='COLOR',
           default=(1.0, 0.0, 0.0),
           min=0.0, max=1.0,
           description="Color for high strength forces",
           update=lambda self, context: self._update_export_force_field(context),
           ); exec(conv("high_force_field_color"))
    min_gradient_force = FloatProperty(
            name="Low Color Force", 
            description="Low force strength value for visualizing force field lines", 
            min=0,
            default=0.0,
            precision=2,
            update=lambda self, context: self._update_min_gradient_force(context),
            ); exec(conv("min_gradient_force"))
    max_gradient_force = FloatProperty(
            name="High Color Force", 
            description="High force strength value for visualizing force field lines", 
            min=0,
            default=15.0,
            precision=2,
            update=lambda self, context: self._update_max_gradient_force(context),
            ); exec(conv("max_gradient_force"))
    force_field_gradient_mode = EnumProperty(
            name="Gradient Mode",
            description="Type of color gradient",
            items=types.gradient_interpolation_modes,
            default='GRADIENT_RGB',
            update=lambda self, context: self._update_max_gradient_force(context),
            ); exec(conv("force_field_gradient_mode"))
    force_field_display_amount = IntProperty(
            name="Display Amount", 
            description="Amount of force field lines to display in the viewport.", 
            min=0, max=100,
            default=25,
            subtype='PERCENTAGE',
            update=lambda self, context: self._update_force_field_geometry(context),
            ); exec(conv("force_field_display_amount"))
    force_field_line_size = IntProperty(
            name="Line Size", 
            description="Line thickness for force field visualization", 
            min=1, soft_max=10,
            default=2,
            update=lambda self, context: self._update_force_field_geometry(context),
            ); exec(conv("force_field_line_size"))

    export_internal_obstacle_mesh = BoolProperty(
            name="Enable Obstacle Debugging",
            description="Enable to export simulator obstacle data"
                        " and to visualize and debug problems with obstacles."
                        " Enable this setting before baking a simulation to"
                        " use this feature",
            default=False,
            update=lambda self, context: self._update_export_internal_obstacle_mesh(context),
            ); exec(conv("export_internal_obstacle_mesh"))
    internal_obstacle_mesh_visibility = BoolProperty(
            name="Obstacle Debugging Visibility",
            description="Show obstacle debug mesh in the viewport. If disabled, this prevents debug obstacle"
                " mesh data from being loaded into Blender. Frame must be reloaded after enabling this option for"
                " mesh to reload and become visible",
            default=True,
            update=lambda self, context: self._update_export_internal_obstacle_mesh(context),
            ); exec(conv("internal_obstacle_mesh_visibility"))

    display_console_output = BoolProperty(
            name="Display Console Output",
            description="Display simulation info in the Blender system console",
            default=True,
            update=lambda self, context: self._update_display_console_output(context),
            options={'HIDDEN'},
            ); exec(conv("display_console_output"))

    is_draw_debug_grid_operator_running = BoolProperty(default=False); exec(conv("is_draw_debug_grid_operator_running"))
    is_draw_gl_particles_operator_running = BoolProperty(default=False); exec(conv("is_draw_gl_particles_operator_running"))
    is_draw_gl_force_field_operator_running = BoolProperty(default=False); exec(conv("is_draw_gl_force_field_operator_running"))

    grid_display_settings_expanded = BoolProperty(default=True); exec(conv("grid_display_settings_expanded"))
    particle_debug_settings_expanded = BoolProperty(default=False); exec(conv("particle_debug_settings_expanded"))
    force_field_debug_settings_expanded = BoolProperty(default=False); exec(conv("force_field_debug_settings_expanded"))

    version_history = CollectionProperty(type=VersionHistoryItem); exec(conv("version_history"))


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".display_simulation_grid",           "Display Domain Grid",             group_id=0)
        add(path + ".grid_display_mode",                 "Grid Display Mode",               group_id=0)
        add(path + ".grid_display_scale",                "Grid Scale",                      group_id=0)
        add(path + ".enabled_debug_grids",               "Draw Grids",                      group_id=0)
        add(path + ".x_grid_color",                      "X Grid Color",                    group_id=0)
        add(path + ".y_grid_color",                      "Y Grid Color",                    group_id=0)
        add(path + ".z_grid_color",                      "Z Grid Color",                    group_id=0)
        add(path + ".debug_grid_offsets",                "Grid Offsets",                    group_id=0)
        add(path + ".snap_offsets_to_grid",              "Snap Offsets to Grid",            group_id=0)
        add(path + ".export_fluid_particles",            "Enable Fluid Particle Debugging", group_id=1)
        add(path + ".fluid_particles_visibility",        "Fluid Particle Visibility",       group_id=1)
        add(path + ".low_speed_particle_color",          "Low Velocity Particle Color",     group_id=1)
        add(path + ".high_speed_particle_color",         "High Velocity Particle Color",    group_id=1)
        add(path + ".min_gradient_speed",                "Low-High Particle Velocities",    group_id=1)
        add(path + ".max_gradient_speed",                "Low-High Particle Velocities",    group_id=1)
        add(path + ".fluid_particle_gradient_mode",      "Fluid Speed Gradient Mode",       group_id=1)
        add(path + ".particle_size",                     "Particle Size",                   group_id=1)
        add(path + ".low_force_field_color",             "Low Force Field Color",           group_id=2)
        add(path + ".high_force_field_color",            "High Force Field Color",          group_id=2)
        add(path + ".min_gradient_force",                "Low-High Force Strength",         group_id=2)
        add(path + ".max_gradient_force",                "Low-High Force Strength",         group_id=2)
        add(path + ".force_field_gradient_mode",         "Fluid Speed Gradient Mode",       group_id=2)
        add(path + ".export_force_field",                "Enable Force Field Debugging",    group_id=2)
        add(path + ".force_field_visibility",            "Force Field Visibility",          group_id=2)
        add(path + ".force_field_line_size",             "Line Size",                       group_id=2)
        add(path + ".export_internal_obstacle_mesh",     "Enable Obstacle Debugging",       group_id=3)
        add(path + ".internal_obstacle_mesh_visibility", "Obstacle Debugging Visibility", group_id=3)
        add(path + ".display_console_output",            "Display Console Output",        group_id=3)


    def load_post(self):
        self.is_draw_debug_grid_operator_running = False
        is_draw_gl_particles_operator_running = False

        if self.export_fluid_particles:
            self._update_debug_particle_geometry(bpy.context)
            bpy.ops.flip_fluid_operators.draw_gl_particles('INVOKE_DEFAULT')
        if self.is_simulation_grid_debugging_enabled():
            self._update_debug_grid_geometry(bpy.context)
            bpy.ops.flip_fluid_operators.draw_debug_grid('INVOKE_DEFAULT')
        if self.export_force_field:
            self._update_force_field_geometry(bpy.context)
            bpy.ops.flip_fluid_operators.draw_force_field('INVOKE_DEFAULT')


    def scene_update_post(self, scene):
        self._update_debug_grid_geometry(bpy.context)


    def save_pre(self):
        bl_info = sys.modules["flip_fluids_addon"].bl_info
        vdata = self.version_history.add()
        vdata.blender_version = bpy.app.version_string
        vdata.flip_fluids_version = str(bl_info.get('version', (-1, -1, -1)))
        vdata.flip_fluids_label = bl_info.get('description', "-1")
        vdata.operating_system = platform.system()
        if len(self.version_history) > 250:
            self.version_history.remove(0)


    def print_version_history(self):
        if len(self.version_history) == 0:
            print("No version history")
        for idx,vdata in enumerate(self.version_history):
            print(idx, vdata.get_info_string())


    def clear_version_history(self):
        self.version_history.clear()


    def get_particle_draw_aabb_object(self):
        obj = None
        try:
            obj = self.particle_draw_aabb
        except:
            pass
        return obj


    def is_simulation_grid_debugging_enabled(self):
        return self.display_simulation_grid or self.display_domain_bounds


    def _update_export_fluid_particles(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.export_fluid_particles:
            self._update_debug_particle_geometry(context)
            dprops.mesh_cache.gl_particles.enable()
            if not self.is_draw_gl_particles_operator_running:
                bpy.ops.flip_fluid_operators.draw_gl_particles('INVOKE_DEFAULT')
        else:
            dprops.mesh_cache.gl_particles.disable()


    def _update_export_internal_obstacle_mesh(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.export_internal_obstacle_mesh and self.internal_obstacle_mesh_visibility:
            dprops.mesh_cache.initialize_cache_objects()
        elif self.export_internal_obstacle_mesh and not self.internal_obstacle_mesh_visibility:
            dprops.mesh_cache.obstacle.reset_cache_object()
        else: 
            dprops.mesh_cache.delete_obstacle_cache_object()


    def _update_display_simulation_grid(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        self._update_debug_grid_geometry(context)
        if self.is_simulation_grid_debugging_enabled() and not self.is_draw_debug_grid_operator_running:
            bpy.ops.flip_fluid_operators.draw_debug_grid('INVOKE_DEFAULT')


    def _update_export_force_field(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.export_force_field:
            self._update_force_field_geometry(context)
            dprops.mesh_cache.gl_force_field.enable()
            if not self.is_draw_gl_force_field_operator_running:
                bpy.ops.flip_fluid_operators.draw_force_field('INVOKE_DEFAULT')
        else:
            dprops.mesh_cache.gl_force_field.disable()


    def _update_display_domain_bounds(self, context):
        self._update_display_simulation_grid(context)


    def _update_debug_grid_geometry(self, context):
        draw_grid_operators.update_debug_grid_geometry(context)


    def _update_min_gradient_speed(self, context):
        if self.min_gradient_speed > self.max_gradient_speed:
            self.max_gradient_speed = self.min_gradient_speed
        self._update_debug_particle_geometry(context)


    def _update_max_gradient_speed(self, context):
        if self.max_gradient_speed < self.min_gradient_speed:
            self.min_gradient_speed = self.max_gradient_speed
        self._update_debug_particle_geometry(context)


    def _update_debug_particle_geometry(self, context):
        draw_particles_operators.update_debug_particle_geometry(context)


    def _update_force_field_geometry(self, context):
        draw_force_field_operators.update_debug_force_field_geometry(context)


    def _update_min_gradient_force(self, context):
        if self.min_gradient_force > self.max_gradient_force:
            self.max_gradient_force = self.min_gradient_force
        self._update_force_field_geometry(context)


    def _update_max_gradient_force(self, context):
        if self.max_gradient_force < self.min_gradient_force:
            self.min_gradient_force = self.max_gradient_force
        self._update_force_field_geometry(context)


    def _update_display_console_output(self, context):
        bake.set_console_output(self.display_console_output)


def register():
    bpy.utils.register_class(VersionHistoryItem)
    bpy.utils.register_class(DomainDebugProperties)


def unregister():
    bpy.utils.unregister_class(VersionHistoryItem)
    bpy.utils.unregister_class(DomainDebugProperties)
