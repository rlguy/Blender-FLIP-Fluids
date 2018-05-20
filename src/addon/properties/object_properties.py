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

if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'types',
        'fluid_properties',
        'obstacle_properties',
        'inflow_properties',
        'outflow_properties',
        'domain_properties',
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty
        )

from . import (
        domain_properties,
        fluid_properties,
        obstacle_properties,
        inflow_properties,
        outflow_properties
        )
from .. import types


class ObjectViewSettings(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        cls.hide_render = BoolProperty(default=False)
        cls.show_name = BoolProperty(default=False)
        cls.draw_type = StringProperty(default="")
        cls.layers = BoolVectorProperty(size=20)


    @classmethod
    def unregister(cls):
        pass


class FlipFluidObjectProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.flip_fluid = PointerProperty(
                name="Flip Fluid Object Properties",
                description="",
                type=cls,
                )
        cls.domain = PointerProperty(
                name="Flip Fluid Domain Properties",
                description="",
                type=domain_properties.FlipFluidDomainProperties,
                )
        cls.fluid = PointerProperty(
                name="Flip Fluid Fluid Properties",
                description="",
                type=fluid_properties.FlipFluidFluidProperties,
                )
        cls.obstacle = PointerProperty(
                name="Flip Fluid Obstacle Properties",
                description="",
                type=obstacle_properties.FlipFluidObstacleProperties,
                )
        cls.inflow = PointerProperty(
                name="Flip Fluid Inflow Properties",
                description="",
                type=inflow_properties.FlipFluidInflowProperties,
                )
        cls.outflow = PointerProperty(
                name="Flip Fluid Outflow Properties",
                description="",
                type=outflow_properties.FlipFluidOutflowProperties,
                )
        cls.object_type = EnumProperty(
                name="Type",
                description="Type of participation in the FLIP fluid simulation",
                items=types.object_types,
                default='TYPE_NONE',
                get=lambda self: self._get_object_type(),
                set=lambda self, value: self._set_object_type(value),
                update=lambda self, context: self._update_object_type(context),
                )
        cls.saved_view_settings = PointerProperty(
                name="Saved View Settings",
                description="",
                type=ObjectViewSettings,
                )

        cls.is_active = BoolProperty(default=False)
        cls.is_view_settings_saved = BoolProperty(default=False)
        

    @classmethod
    def unregister(cls):
        del bpy.types.Object.flip_fluid


    def get_object_type():
        return self.object_type


    def is_none(self):
        return self.object_type == 'TYPE_NONE'


    def is_domain(self):
        return self.object_type == 'TYPE_DOMAIN'


    def is_fluid(self):
        return self.object_type == 'TYPE_FLUID'


    def is_obstacle(self):
        return self.object_type == 'TYPE_OBSTACLE'


    def is_inflow(self):
        return self.object_type == 'TYPE_INFLOW'


    def is_outflow(self):
        return self.object_type == 'TYPE_OUTFLOW'


    def get_property_group(self):
        if self.is_domain():
            return self.domain
        if self.is_fluid():
            return self.fluid
        if self.is_obstacle():
            return self.obstacle
        if self.is_inflow():
            return self.inflow
        if self.is_outflow():
            return self.outflow


    def _get_object_type(self):
        try:
            return self["object_type"]
        except:
            return 0


    def _toggle_cycles_ray_visibility(self, obj, is_enabled):
        obj.cycles_visibility.camera = is_enabled
        obj.cycles_visibility.transmission = is_enabled
        obj.cycles_visibility.diffuse = is_enabled
        obj.cycles_visibility.scatter = is_enabled
        obj.cycles_visibility.glossy = is_enabled
        obj.cycles_visibility.shadow = is_enabled


    def _set_object_type(self, value):
        oldtype = self.object_type
        self['object_type'] = value

        if value == 0:
            newtype = 'TYPE_NONE'
        elif value == 1:
            newtype = 'TYPE_DOMAIN'
        elif value == 2:
            newtype = 'TYPE_FLUID'
        elif value == 3:
            newtype = 'TYPE_OBSTACLE'
        elif value == 4:
            newtype = 'TYPE_INFLOW'
        elif value == 5:
            newtype = 'TYPE_OUTFLOW'
        else:
            newtype = 'TYPE_NONE'

        active_object = bpy.context.scene.objects.active
        if oldtype == 'TYPE_NONE' and newtype != 'TYPE_NONE':
            self._save_object_view_settings(bpy.context.scene.objects.active)
        if oldtype != 'TYPE_NONE' and newtype == 'TYPE_NONE':
            self._reset_object_view_settings(bpy.context.scene.objects.active)
            self._toggle_cycles_ray_visibility(active_object, True)

        if oldtype != 'TYPE_DOMAIN' and newtype == 'TYPE_DOMAIN':
            active_object.flip_fluid.domain.initialize()
            active_object.lock_rotation = (True, True, True)
            self._toggle_cycles_ray_visibility(active_object, False)
        if oldtype == 'TYPE_DOMAIN' and newtype != 'TYPE_DOMAIN':
            active_object.lock_rotation = (False, False, False)
            active_object.flip_fluid.domain.destroy()

        if newtype != oldtype:
            if newtype == 'TYPE_FLUID':
                active_object.flip_fluid.fluid.initialize()
                self._toggle_cycles_ray_visibility(active_object, False)
            if newtype == 'TYPE_OBSTACLE':
                active_object.flip_fluid.obstacle.initialize()
                self._toggle_cycles_ray_visibility(active_object, True)
            if newtype == 'TYPE_INFLOW':
                active_object.flip_fluid.inflow.initialize()
                self._toggle_cycles_ray_visibility(active_object, False)
            if newtype == 'TYPE_OUTFLOW':
                active_object.flip_fluid.outflow.initialize()
                self._toggle_cycles_ray_visibility(active_object, False)


    def _update_object_type(self, context):
        obj = context.scene.objects.active
        primary_layer = 0
        object_layer = 14

        if self.object_type == 'TYPE_DOMAIN':
            obj.hide_render = True
            obj.draw_type = 'BOUNDS'
            obj.show_name = True
            self._set_object_layer(obj, object_layer)
            context.scene.layers[object_layer] = True

        elif self.object_type == 'TYPE_FLUID':
            obj.hide_render = True
            obj.draw_type = 'WIRE'
            obj.show_name = True
            self._set_object_layer(obj, object_layer)
            context.scene.layers[object_layer] = True

        elif self.object_type == 'TYPE_OBSTACLE':
            obj.hide_render = False
            obj.draw_type = 'TEXTURED'
            obj.show_name = True
            self._set_object_layers(obj, [primary_layer, object_layer])
            context.scene.layers[primary_layer] = True
            context.scene.layers[object_layer] = True

        elif self.object_type == 'TYPE_INFLOW':
            obj.hide_render = True
            obj.draw_type = 'WIRE'
            obj.show_name = True
            self._set_object_layer(obj, object_layer)
            context.scene.layers[object_layer] = True

        elif self.object_type == 'TYPE_OUTFLOW':
            obj.hide_render = True
            obj.draw_type = 'WIRE'
            obj.show_name = True
            self._set_object_layer(obj, object_layer)
            context.scene.layers[object_layer] = True


    def _save_object_view_settings(self, obj):
        if self.is_view_settings_saved:
            return

        self.saved_view_settings.hide_render = obj.hide_render
        self.saved_view_settings.show_name = obj.show_name
        self.saved_view_settings.draw_type = obj.draw_type
        for i in range(20):
            self.saved_view_settings.layers[i] = obj.layers[i]
        self.is_view_settings_saved = True
        

    def _reset_object_view_settings(self, obj):
        if not self.is_view_settings_saved:
            return

        obj.hide_render = self.saved_view_settings.hide_render
        obj.show_name = self.saved_view_settings.show_name
        obj.draw_type = self.saved_view_settings.draw_type
        for i in range(20):
            obj.layers[i] = True
        for i in range(20):
            obj.layers[i] = self.saved_view_settings.layers[i]
        self.is_view_settings_saved = False


    def _set_object_layer(self, obj, layeridx):
        obj.layers[layeridx] = True
        for i in range(20):
            obj.layers[i] = (i == layeridx)


    def _set_object_layers(self, obj, layers):
        obj.layers[layers[0]] = True
        for i in range(20):
            obj.layers[i] = (i in layers)


def scene_update_post(scene):
    domain_properties.scene_update_post(scene)


def frame_change_pre(scene):
    domain_properties.frame_change_pre(scene)


def load_pre():
    domain_properties.load_pre()


def load_post():
    domain_properties.load_post()


def save_pre():
    domain_properties.save_pre()


def save_post():
    domain_properties.save_post()


def register():
    domain_properties.register()
    obstacle_properties.register()
    fluid_properties.register()
    inflow_properties.register()
    outflow_properties.register()
    bpy.utils.register_class(ObjectViewSettings)
    bpy.utils.register_class(FlipFluidObjectProperties)


def unregister():
    domain_properties.unregister()
    obstacle_properties.unregister()
    fluid_properties.unregister()
    inflow_properties.unregister()
    outflow_properties.unregister()
    bpy.utils.unregister_class(ObjectViewSettings)
    bpy.utils.unregister_class(FlipFluidObjectProperties)
