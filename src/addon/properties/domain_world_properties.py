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

import bpy, os, math
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty
        )

from .. import types
from ..utils import export_utils
from ..utils import version_compatibility_utils as vcu
from ..objects.flip_fluid_aabb import AABB


class DomainWorldProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    world_scale_mode = EnumProperty(
            name="World Scaling Mode",
            description="Scaling mode for the physical size of the domain",
            items=types.world_scale_mode,
            default='WORLD_SCALE_MODE_RELATIVE',
            options={'HIDDEN'},
            ); exec(conv("world_scale_mode"))
    world_scale_relative = FloatProperty(
            name="Meters", 
            description="Size of a Blender unit in meters. If set to 1.0, each blender unit will be equal to 1.0 meter in the simulation", 
            min=0.0001,
            default=1.0,
            precision=3,
            update=lambda self, context: self._update_world_scale_relative(context),
            options={'HIDDEN'},
            ); exec(conv("world_scale_relative"))
    world_scale_absolute = FloatProperty(
            name="Meters", 
            description="Size of the longest side of the domain in meters", 
            min=0.001,
            default=10.0,
            precision=3,
            update=lambda self, context: self._update_world_scale_absolute(context),
            options={'HIDDEN'},
            ); exec(conv("world_scale_absolute"))
    gravity_type = EnumProperty(
            name="Gravity Type",
            description="Gravity Type",
            items=types.gravity_types,
            default='GRAVITY_TYPE_SCENE',
            options={'HIDDEN'},
            ); exec(conv("gravity_type"))
    gravity = FloatVectorProperty(
            name="Gravity",
            description="Gravity in X, Y, and Z direction",
            default=(0.0, 0.0, -9.81),
            precision=3,
            size=3,
            subtype='VELOCITY',
            ); exec(conv("gravity"))
    force_field_resolution = EnumProperty(
            name="Force Field Resolution",
            description="Amount of grid resolution to use when evaluating force fields."
                " Higher resolution improves force field accuracy at the cost of speed"
                " and RAM. Increase to resolve smaller/sharper details in your force"
                " field setup. Ultra is recommended for static force fields. High/Med/Low is"
                " recommended for animated force fields to optimize performance",
            items=types.force_field_resolution_modes,
            default='FORCE_FIELD_RESOLUTION_ULTRA',
            options={'HIDDEN'},
            ); exec(conv("force_field_resolution"))
    force_field_resolution_tooltip = BoolProperty(
            name="Force Field Grid Resolution", 
            description="Exact force field grid resolution calculated from the domain"
                " resolution. See Debug Panel for force field visualization tools", 
            default=True,
            ); exec(conv("force_field_resolution_tooltip"))
    enable_viscosity = BoolProperty(
            name="Enable Viscosity",
            description="Enable viscosity solver",
            default=False,
            ); exec(conv("enable_viscosity"))
    viscosity = FloatProperty(
            name="Viscosity", 
            description="Viscosity base value. This value is multipled by 10 to the"
                " power of (exponent * -1)", 
            min=0.0,
            default=5.0,
            precision=3,
            ); exec(conv("viscosity"))
    viscosity_exponent = IntProperty(
            name="Viscosity Exponent", 
            description="Viscosity exponent. Negative exponent for the viscosity value"
                " to simplify entering small values (ex: 5.0 * 10^-3 = 0.005)", 
            min=0,
            soft_max=4, max=8,
            default=0,
            update=lambda self, context: self._update_viscosity_exponent(context),
            options={'HIDDEN'},
            ); exec(conv("viscosity_exponent"))
    viscosity_solver_error_tolerance = IntProperty(
            description="Accuracy of the viscosity solver. Decrease to speed up baking at the cost of accuracy,"
                " increase to improve accuracy at the cost of baking speed. High viscosity thick or stiff fluids"
                " benefit the most from increasing accuracy. Low viscosity thin fluids often work well at the lowest"
                " accuracy. Setting above a value of 4 may have greatly diminishing returns on improvement", 
            min=1, max=6,
            default=4,
            ); exec(conv("viscosity_solver_error_tolerance"))
    enable_surface_tension = BoolProperty(
            name="Enable Surface Tension",
            description="Enable surface tension forces",
            default=False,
            ); exec(conv("enable_surface_tension"))
    surface_tension = FloatProperty(
            name="Surface Tension", 
            description="Surface tension base value. This value is multipled by 10 to the"
                " power of (exponent * -1)", 
            min=0.0,
            default=0.25,
            precision=3,
            ); exec(conv("surface_tension"))
    surface_tension_exponent = IntProperty(
            name="Viscosity Exponent", 
            description="Viscosity exponent. Negative exponent for the surface tension value"
                " to simplify entering small values (ex: 5.0 * 10^-3 = 0.005)", 
            min=0,
            soft_max=4, max=8,
            default=0,
            update=lambda self, context: self._update_surface_tension_exponent(context),
            options={'HIDDEN'},
            ); exec(conv("surface_tension_exponent"))
    surface_tension_accuracy = IntProperty(
            name="Surface Tension Accuracy", 
            description="Amount of accuracy when calculating surface tension. "
                " Increasing accuracy will produce more accurate surface tension"
                " results but will require more substeps and increase baking time", 
            min=0, max=100,
            default=90,
            subtype='PERCENTAGE',
            ); exec(conv("surface_tension_accuracy"))
    enable_sheet_seeding = BoolProperty(
            name="Enable Sheeting Effects",
            description="Fluid sheeting fills in gaps between fluid particles to"
                " help preserve thin fluid sheets and splashes. Tip: Sheeting will"
                " add fluid to the domain and prolonged use can result in an increased"
                " fluid volume. Keyframing the Sheeting Strength down to 0.0 when no longer"
                " needed can help prevent increased volume.",
            default=False,
            ); exec(conv("enable_sheet_seeding"))
    sheet_fill_rate = FloatProperty(
            name="Sheeting Strength", 
            description="The rate at which new sheeting particles are added."
                " A higher value will add sheeting particles more often and"
                " fill in gaps more quickly.", 
            min=0.0, max=1.0,
            default=0.5,
            precision=2,
            ); exec(conv("sheet_fill_rate"))
    sheet_fill_threshold = FloatProperty(
            name="Sheeting Thickness", 
            description="Controls how thick to fill in gaps", 
            min=0.0, max=1.0,
            soft_min=0.05,
            default=0.1,
            precision=2,
            ); exec(conv("sheet_fill_threshold"))
    boundary_friction = FloatProperty(
            name="Boundary Friction", 
            description="Amount of friction on the domain boundary walls", 
            min=0.0,
            max=1.0,
            default=0.0,
            precision=2,
            subtype='FACTOR',
            ); exec(conv("boundary_friction"))

    last_viscosity_exponent = IntProperty(default=0)
    exec(conv("last_viscosity_exponent"))

    last_surface_tension_exponent = IntProperty(default=0)
    exec(conv("last_surface_tension_exponent"))

    native_surface_tension_scale = FloatProperty(default=0.1)
    exec(conv("native_surface_tension_scale"))

    minimum_surface_tension_substeps = IntProperty(default=-1)
    exec(conv("minimum_surface_tension_substeps"))

    surface_tension_substeps_tooltip = BoolProperty(
            name="Estimated Substeps", 
            description="The estimated number of substeps per frame that the"
                " simulator will run in order to keep simulation stable during surface"
                " tension computation. This number will depend on domain resolution"
                " and size, framerate, amount of surface tension, and surface tension" 
                " accuracy", 
            default=True,
            ); exec(conv("surface_tension_substeps_tooltip"))

    surface_tension_substeps_exceeded_tooltip = BoolProperty(
            name="Warning: Too Many Substeps", 
            description="The estimated number of Surface Tension substeps per frame exceeds the Max Frame"
                " Substeps value. This can cause an unstable simulation. Either decrease the amount of"
                " Surface Tension in the FLIP Fluid World panel to lower the number of required substeps or"
                " increase the number of allowed Max Frame Substeps in the FLIP Fluid Advanced panel", 
            default=True,
            ); exec(conv("surface_tension_substeps_exceeded_tooltip"))

    minimum_surface_tension_cfl = FloatProperty(default=0.25)
    exec(conv("minimum_surface_tension_cfl"))

    maximum_surface_tension_cfl = FloatProperty(default=5.0)
    exec(conv("maximum_surface_tension_cfl"))

    world_scale_settings_expanded = BoolProperty(default=True); exec(conv("world_scale_settings_expanded"))
    force_field_settings_expanded = BoolProperty(default=False); exec(conv("force_field_settings_expanded"))
    viscosity_settings_expanded = BoolProperty(default=False); exec(conv("viscosity_settings_expanded"))
    surface_tension_settings_expanded = BoolProperty(default=False); exec(conv("surface_tension_settings_expanded"))
    sheeting_settings_expanded = BoolProperty(default=False); exec(conv("sheeting_settings_expanded"))
    friction_settings_expanded = BoolProperty(default=False); exec(conv("friction_settings_expanded"))
    obstacle_friction_expanded = BoolProperty(default=False); exec(conv("obstacle_friction_expanded"))


    def scene_update_post(self, scene):
        self._update_surface_tension_info()
        self._update_world_scale_relative(bpy.context)
        self._update_world_scale_absolute(bpy.context)


    def frame_change_post(self, scene):
        # Accounts for keyframed value changes after a frame change
        self._update_surface_tension_info()

    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".world_scale_mode",                 "World Scaling Mode",        group_id=0)
        add(path + ".world_scale_relative",             "Relative Scale",            group_id=0)
        add(path + ".world_scale_absolute",             "Absolute Scale",            group_id=0)
        add(path + ".gravity_type",                     "Gravity Type",              group_id=0)
        add(path + ".gravity",                          "Gravity",                   group_id=0)
        add(path + ".force_field_resolution",           "Force Field Resolution",    group_id=0)
        add(path + ".enable_viscosity",                 "Enable Viscosity",          group_id=0)
        add(path + ".viscosity",                        "Viscosity Base",            group_id=0)
        add(path + ".viscosity_exponent",               "Viscosity Exponent",        group_id=0)
        add(path + ".viscosity_solver_error_tolerance", "Viscosity Accuracy",        group_id=0)
        add(path + ".enable_surface_tension",           "Enable Surface Tension",    group_id=0)
        add(path + ".surface_tension",                  "Surface Tension",           group_id=0)
        add(path + ".surface_tension_exponent",         "Surface Tension Exponent",  group_id=0)
        add(path + ".surface_tension_accuracy",         "Surface Tension Accuracy",  group_id=0)
        add(path + ".enable_sheet_seeding",             "Enable Sheeting Effects",   group_id=0)
        add(path + ".sheet_fill_rate",                  "Sheeting Strength",         group_id=0)
        add(path + ".sheet_fill_threshold",             "Sheeting Thickness",        group_id=0)
        add(path + ".boundary_friction",                "Boundary Friction",         group_id=0)


    def get_gravity_data_dict(self):
        domain_object = bpy.context.scene.flip_fluid.get_domain_object()
        if self.gravity_type == 'GRAVITY_TYPE_SCENE':
            scene = bpy.context.scene
            return export_utils.get_vector_property_data_dict(scene, scene, 'gravity')
        elif self.gravity_type == 'GRAVITY_TYPE_CUSTOM':
            return export_utils.get_vector_property_data_dict(domain_object, self, 'gravity')


    def get_gravity_vector(self):
        if self.gravity_type == 'GRAVITY_TYPE_SCENE':
            return bpy.context.scene.gravity
        elif self.gravity_type == 'GRAVITY_TYPE_CUSTOM':
            return self.gravity


    def get_world_scale(self):
        return self.world_scale_relative


    def get_viewport_dimensions(self, context):
        domain = context.scene.flip_fluid.get_domain_object()
        minx = miny = minz = float("inf")
        maxx = maxy = maxz = -float("inf")
        for v in domain.data.vertices:
            p = vcu.element_multiply(v.co, domain.matrix_world)
            minx, miny, minz = min(p.x, minx), min(p.y, miny), min(p.z, minz)
            maxx, maxy, maxz = max(p.x, maxx), max(p.y, maxy), max(p.z, maxz)

        return maxx - minx, maxy - miny, maxz - minz


    def get_simulation_dimensions(self, context):
        view_x, view_y, view_z = self.get_viewport_dimensions(context)
        if self.world_scale_mode == 'WORLD_SCALE_MODE_RELATIVE':
            scale = self.world_scale_relative
        else:
            longest_side = max(view_x, view_y, view_z, 1e-6)
            scale = self.world_scale_absolute / longest_side
        
        return view_x * scale, view_y * scale, view_z * scale


    def get_surface_tension_value(self):
        return self.surface_tension * (10**(-self.surface_tension_exponent))


    def _update_world_scale_relative(self, context):
        if self.world_scale_mode == 'WORLD_SCALE_MODE_ABSOLUTE':
            return
        xdims, ydims, zdims = self.get_simulation_dimensions(context)
        absolute_scale = max(xdims, ydims, zdims)
        if self.world_scale_absolute != absolute_scale:
            self.world_scale_absolute = absolute_scale


    def _update_world_scale_absolute(self, context):
        if self.world_scale_mode == 'WORLD_SCALE_MODE_RELATIVE':
            return
        xdims, ydims, zdims = self.get_simulation_dimensions(context)
        xview, yview, zview = self.get_viewport_dimensions(context)
        relative_scale = max(xdims, ydims, zdims, 1e-6) / max(xview, yview, zview)
        if self.world_scale_relative != relative_scale:
            self.world_scale_relative = relative_scale


    def _update_surface_tension_info(self):
        domain = bpy.context.scene.flip_fluid.get_domain_object()
        if domain is None:
            return
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        _, _, _, dx = dprops.simulation.get_simulation_grid_dimensions()

        time_scale = dprops.simulation.time_scale
        frame_rate = dprops.simulation.get_frame_rate()
        dt = (1.0 / frame_rate) * time_scale

        mincfl, maxcfl = dprops.world.minimum_surface_tension_cfl, dprops.world.maximum_surface_tension_cfl
        accuracy_pct = dprops.world.surface_tension_accuracy / 100.0
        safety_factor = mincfl + (1.0 - accuracy_pct) * (maxcfl - mincfl)

        surface_tension = self.get_surface_tension_value() * dprops.world.native_surface_tension_scale
        eps = 1e-6

        restriction =  safety_factor * math.sqrt(dx * dx * dx) * math.sqrt(1.0 / (surface_tension + eps));
        num_substeps = math.ceil(dt / restriction)

        if self.minimum_surface_tension_substeps != num_substeps:
            self.minimum_surface_tension_substeps = num_substeps


    def _update_viscosity_exponent(self, context):
        last_value = self.last_viscosity_exponent
        new_value = self.viscosity_exponent
        multiplier = 10**(new_value - last_value)
        self.viscosity = multiplier * self.viscosity
        self.last_viscosity_exponent = new_value


    def _update_surface_tension_exponent(self, context):
        last_value = self.last_surface_tension_exponent
        new_value = self.surface_tension_exponent
        multiplier = 10**(new_value - last_value)
        self.surface_tension = multiplier * self.surface_tension
        self.last_surface_tension_exponent = new_value


def register():
    bpy.utils.register_class(DomainWorldProperties)


def unregister():
    bpy.utils.unregister_class(DomainWorldProperties)