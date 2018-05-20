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
        BoolVectorProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty
        )

from .custom_properties import (
        NewMinMaxFloatProperty
        )

from .. import (
        types,
        bake
        )


class DomainDebugProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.display_simulation_grid = BoolProperty(
                name="Display Domain Grid",
                description="Visualize the simulation/meshing grid",
                default=False,
                update=lambda self, context: self._update_display_simulation_grid(context),
                )
        cls.grid_display_mode = EnumProperty(
                name="Grid Display Mode",
                description="Type of grid debug info to display",
                items=types.grid_display_modes,
                default='GRID_DISPLAY_SIMULATION',
                )
        cls.grid_display_scale = IntProperty(
                name="Grid Display Scale",
                description="Number of grid cells that a single grid cell in the"
                    " viewport represents",
                min = 1, soft_max = 10,
                default=1,
                step=1,
                )
        cls.enabled_debug_grids = BoolVectorProperty(
                name="Enabled Debug Grids",
                description="Select which debug grids are displayed in the viewport",
                default=(True, True, True),
                size=3,
                subtype='XYZ',
                )
        cls.x_grid_color = FloatVectorProperty(  
               name="X Grid Color",
               subtype='COLOR',
               default=(0.5, 0.0, 0.0),
               min=0.0, max=1.0,
               description="X grid display color"
               )
        cls.y_grid_color = FloatVectorProperty(  
               name="Y Grid Color",
               subtype='COLOR',
               default=(0.0, 0.5, 0.0),
               min=0.0, max=1.0,
               description="Y grid display color"
               )
        cls.z_grid_color = FloatVectorProperty(  
               name="Z Grid Color",
               subtype='COLOR',
               default=(0.0, 0.0, 0.5),
               min=0.0, max=1.0,
               description="Z grid display color"
               )
        cls.debug_grid_offsets = FloatVectorProperty(
                name="Debug Grid Offsets",
                description="Offset at which an axis' grid is displayed in the viewport",
                min = 0.0, max = 1.0,
                default=(0.0, 0.0, 0.0),
                size=3,
                step=1,
                subtype='XYZ',
                )
        cls.snap_offsets_to_grid = BoolProperty(
                name="Snap Offsets to Grid",
                description="Align debug grids to gridcell locations",
                default=True,
                )
        cls.export_fluid_particles = BoolProperty(
                name="Enable Fluid Particle Debugging",
                description="Enable to export simulator fluid particle data and to"
                    " visualize and debug problems with fluid behaviour. Enable "
                    " this option before baking a simulation to use this feature.",
                default=False,
                update=lambda self, context: self._update_export_fluid_particles(context),
                )
        cls.low_speed_particle_color = FloatVectorProperty(  
               name="Low Speed Color",
               subtype='COLOR',
               default=(0.0, 0.0, 1.0),
               min=0.0, max=1.0,
               description="Color for low velocity fluid particles"
               )
        cls.high_speed_particle_color = FloatVectorProperty(  
               name="High Speed Color",
               subtype='COLOR',
               default=(1.0, 1.0, 1.0),
               min=0.0, max=1.0,
               description="Color for high velocity fluid particles"
               )
        cls.min_max_gradient_speed = NewMinMaxFloatProperty(
                name_min="Low Color Speed", 
                description_min="Low speed value for visualizing fluid particle velocity", 
                min_min=0,
                default_min=0.0,
                precision_min=2,

                name_max="High Color Speed", 
                description_max="High speed value for visualizing fluid particle velocity", 
                min_max=0,
                default_max=5.0,
                precision_max=2,
                )
        cls.fluid_particle_gradient_mode = EnumProperty(
                name="Gradient Mode",
                description="Type of color gradient",
                items=types.gradient_interpolation_modes,
                default='GRADIENT_RGB',
                )
        cls.particle_size = IntProperty(
                name="Particle Size", 
                description="Size to draw particles for visualization", 
                min=1, soft_max=10,
                default=1,
                )
        cls.particle_draw_aabb = StringProperty(
                name="Visualization Bounds",
                description="If set, only particles inside the object's axis-aligned"
                    " bounding box will be drawn.",
                )
        cls.export_internal_obstacle_mesh = BoolProperty(
                name="Enable Obstacle Debugging",
                description="Enable to export simulator obstacle data"
                            " and to visualize and debug problems with obstacles."
                            " Enable this setting before baking a simulation to"
                            " use this feature.",
                default=False,
                update=lambda self, context: self._update_export_internal_obstacle_mesh(context),
                )
        cls.display_console_output = BoolProperty(
                name="Display Console Output",
                description="Display simulation info in the Blender system console",
                default=False,
                update=lambda self, context: self._update_display_console_output(context),
                options={'HIDDEN'},
                )

        cls.is_draw_debug_grid_operator_running = BoolProperty(default=False)
        cls.is_draw_gl_particles_operator_running = BoolProperty(default=False)


    @classmethod
    def unregister(cls):
        pass


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".display_simulation_grid",         "Display Domain Grid",             group_id=0)
        add(path + ".grid_display_mode",               "Grid Display Mode",               group_id=0)
        add(path + ".grid_display_scale",              "Grid Scale",                      group_id=0)
        add(path + ".enabled_debug_grids",             "Draw Grids",                      group_id=0)
        add(path + ".x_grid_color",                    "X Grid Color",                    group_id=0)
        add(path + ".y_grid_color",                    "Y Grid Color",                    group_id=0)
        add(path + ".z_grid_color",                    "Z Grid Color",                    group_id=0)
        add(path + ".debug_grid_offsets",              "Grid Offsets",                    group_id=0)
        add(path + ".snap_offsets_to_grid",            "Snap Offsets to Grid",            group_id=0)
        add(path + ".export_fluid_particles",          "Enable Fluid Particle Debugging", group_id=1)
        add(path + ".low_speed_particle_color",        "Low Velocity Particle Color",     group_id=1)
        add(path + ".high_speed_particle_color",       "High Velocity Particle Color",    group_id=1)
        add(path + ".min_max_gradient_speed",          "Low-High Particle Velocities",    group_id=1)
        add(path + ".fluid_particle_gradient_mode",    "Fluid Speed Gradient Mode",       group_id=1)
        add(path + ".particle_size",                   "Particle Size",                   group_id=1)
        add(path + ".export_internal_obstacle_mesh",   "Enable Obstacle Debugging",       group_id=2)
        add(path + ".display_console_output",          "Display Console Output",          group_id=2)


    def load_post(self):
        if self.export_fluid_particles:
            bpy.ops.flip_fluid_operators.draw_gl_particles('INVOKE_DEFAULT')
        if self.display_simulation_grid:
            bpy.ops.flip_fluid_operators.draw_debug_grid('INVOKE_DEFAULT')


    def _update_export_fluid_particles(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.export_fluid_particles:
            dprops.mesh_cache.gl_particles.enable()
            if not self.is_draw_gl_particles_operator_running:
                bpy.ops.flip_fluid_operators.draw_gl_particles('INVOKE_DEFAULT')
        else:
            dprops.mesh_cache.gl_particles.disable()


    def _update_export_internal_obstacle_mesh(self, context):
        domain_object = context.scene.flip_fluid.get_domain_object()
        if domain_object is None:
            return
        dprops = domain_object.flip_fluid.domain

        if self.export_internal_obstacle_mesh:
            dprops.mesh_cache.initialize_cache_objects()
        else:
            dprops.mesh_cache.delete_obstacle_cache_object(domain_object)


    def _update_display_simulation_grid(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return

        if self.display_simulation_grid and not self.is_draw_debug_grid_operator_running:
            bpy.ops.flip_fluid_operators.draw_debug_grid('INVOKE_DEFAULT')


    def _update_display_console_output(self, context):
        bake.set_console_output(self.display_console_output)


def register():
    bpy.utils.register_class(DomainDebugProperties)


def unregister():
    bpy.utils.unregister_class(DomainDebugProperties)