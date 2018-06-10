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
        StringProperty,
        PointerProperty
        )


class FlipFluidProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.flip_fluid = PointerProperty(
                name="Flip Fluid Properties",
                description="",
                type=cls,
                )

        cls.custom_icons = bpy.utils.previews.new()
        cls.is_custom_icons_loaded = BoolProperty(False)
        cls.logo_name = StringProperty("flip_fluids_logo")
        cls.domain_object_name = StringProperty(default="")


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.flip_fluid


    def scene_update_post(self, scene):
        if not self.is_custom_icons_loaded:
            self._initialize_custom_icons()


    def is_domain_object_set(self):
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_domain():
                return True


    def get_num_domain_objects(self):
        n = 0
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_domain():
                n += 1
        return n


    def get_domain_object(self):
        domain = bpy.data.objects.get(self.domain_object_name)
        if not domain or not domain.flip_fluid.is_domain():
            for obj in bpy.data.objects:
                if obj.flip_fluid.is_domain():
                    domain = obj
                    self.domain_object_name = domain.name
                    break
        if domain is not None and domain.flip_fluid.object_type != 'TYPE_DOMAIN':
            return None
        return domain


    def get_domain_properties(self):
        domain_object = self.get_domain_object()
        if domain_object is None:
            return
        return domain_object.flip_fluid.domain


    def get_num_fluid_objects(self):
        n = 0
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_fluid():
                n += 1
        return n


    def get_fluid_objects(self):
        objects = []
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_fluid():
                objects.append(obj)
        return objects


    def get_num_obstacle_objects(self):
        n = 0
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_obstacle():
                n += 1
        return n


    def get_obstacle_objects(self):
        objects = []
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_obstacle():
                objects.append(obj)
        return objects


    def get_num_inflow_objects(self):
        n = 0
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_inflow():
                n += 1
        return n


    def get_inflow_objects(self):
        objects = []
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_inflow():
                objects.append(obj)
        return objects


    def get_num_outflow_objects(self):
        n = 0
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_outflow():
                n += 1
        return n


    def get_outflow_objects(self):
        objects = []
        for obj in bpy.data.objects:
            if obj.flip_fluid.is_outflow():
                objects.append(obj)
        return objects


    def get_logo_icon(self):
        return self.custom_icons.get(self.logo_name)


    def _initialize_custom_icons(self):
        addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(addon_dir, "icons", "flip_fluids_logo.png")
        self.custom_icons.clear()
        self.custom_icons.load(self.logo_name, logo_path, 'IMAGE')
        self.is_custom_icons_loaded = True


def scene_update_post(scene):
    scene.flip_fluid.scene_update_post(scene)


def register():
    bpy.utils.register_class(FlipFluidProperties)


def unregister():
    bpy.utils.unregister_class(FlipFluidProperties)