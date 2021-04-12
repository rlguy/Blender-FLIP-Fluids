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

import bpy, os
from bpy.props import (
        BoolProperty,
        EnumProperty,
        StringProperty
        )

from ..materials import material_library
from ..utils import version_compatibility_utils as vcu


class DomainMaterialsProperties(bpy.types.PropertyGroup):
    conv = vcu.convert_attribute_to_28
    
    surface_material = EnumProperty(
            name="Surface",
            description="Select a material for the fluid surface. Tip: materials can also be"
                " created and assigned to the fluid_surface object in Blender's Material"
                " Properties panel",
            items=material_library.get_surface_material_enums_ui,
            update=lambda self, context: self._update_surface_material(context),
            ); exec(conv("surface_material"))
    whitewater_foam_material = EnumProperty(
            name="Whitewater Foam",
            description="Select a material for the foam particles. Tip: materials can also be"
                " created and assigned to the whitewater_foam object in Blender's Material"
                " Properties panel",
            items=material_library.get_whitewater_material_enums_ui,
            update=lambda self, context: self._update_whitewater_foam_material(context),
            ); exec(conv("whitewater_foam_material"))
    whitewater_bubble_material = EnumProperty(
            name="Whitewater Bubble",
            description="Select a material for the bubble particles. Tip: materials can also be"
                " created and assigned to the whitewater_bubble object in Blender's Material"
                " Properties panel",
            items=material_library.get_whitewater_material_enums_ui,
            update=lambda self, context: self._update_whitewater_bubble_material(context),
            ); exec(conv("whitewater_bubble_material"))
    whitewater_spray_material = EnumProperty(
            name="Whitewater Spray",
            description="Select a material for the spray particles. Tip: materials can also be"
                " created and assigned to the whitewater_spray object in Blender's Material"
                " Properties panel",
            items=material_library.get_whitewater_material_enums_ui,
            update=lambda self, context: self._update_whitewater_spray_material(context),
            ); exec(conv("whitewater_spray_material"))
    whitewater_dust_material = EnumProperty(
            name="Whitewater Dust",
            description="Select a material for the dust particles. Tip: materials can also be"
                " created and assigned to the whitewater_dust object in Blender's Material"
                " Properties panel",
            items=material_library.get_whitewater_material_enums_ui,
            update=lambda self, context: self._update_whitewater_dust_material(context),
            ); exec(conv("whitewater_dust_material"))
    material_import = EnumProperty(
            name="Import",
            description="Import materials into this scene",
            items=material_library.get_material_import_enums_ui,
            ); exec(conv("material_import"))

    last_surface_material = StringProperty(default=""); exec(conv("last_surface_material"))
    last_whitewater_foam_material = StringProperty(default=""); exec(conv("last_whitewater_foam_material"))
    last_whitewater_bubble_material = StringProperty(default=""); exec(conv("last_whitewater_bubble_material"))
    last_whitewater_spray_material = StringProperty(default=""); exec(conv("last_whitewater_spray_material"))
    last_whitewater_dust_material = StringProperty(default=""); exec(conv("last_whitewater_dust_material"))


    def load_post(self):
        self._check_material_properties_valid()


    def register_preset_properties(self, registry, path):
        add = registry.add_property
        add(path + ".surface_material",           "Surface Material", group_id=0)
        add(path + ".whitewater_foam_material",   "Foam Material",    group_id=0)
        add(path + ".whitewater_bubble_material", "Bubble Material",  group_id=0)
        add(path + ".whitewater_spray_material",  "Spray Material",   group_id=0)
        add(path + ".whitewater_dust_material",   "Dust Material",   group_id=0)


    def initialize(self):
        self.surface_material = 'MATERIAL_NONE'
        self.whitewater_foam_material = 'MATERIAL_NONE'
        self.whitewater_bubble_material = 'MATERIAL_NONE'
        self.whitewater_spray_material = 'MATERIAL_NONE'
        self.whitewater_dust_material = 'MATERIAL_NONE'
        self.material_import = 'ALL_MATERIALS'


    def scene_update_post(self, scene):
        self._check_material_properties()


    def save_pre(self):
        self._save_unused_materials_with_fake_user()


    def _is_domain_set(self):
        return bpy.context.scene.flip_fluid.get_num_domain_objects() != 0 


    def _get_domain_object(self):
        return bpy.context.scene.flip_fluid.get_domain_object() 


    def _get_domain_properties(self):
        return bpy.context.scene.flip_fluid.get_domain_properties() 


    def _update_surface_material(self, context):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        surface_object = dprops.mesh_cache.surface.get_cache_object()
        self._update_cache_object_material(
            surface_object,
            'surface_material', 'last_surface_material'
        )


    def _update_whitewater_foam_material(self, context):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        foam_object = dprops.mesh_cache.foam.get_cache_object()
        self._update_cache_object_material(
            foam_object,
            'whitewater_foam_material', 'last_whitewater_foam_material'
        )
        dprops.mesh_cache.foam.apply_duplivert_object_material()


    def _update_whitewater_bubble_material(self, context):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        bubble_object = dprops.mesh_cache.bubble.get_cache_object()
        self._update_cache_object_material(
            bubble_object,
            'whitewater_bubble_material', 'last_whitewater_bubble_material'
        )
        dprops.mesh_cache.bubble.apply_duplivert_object_material()


    def _update_whitewater_spray_material(self, context):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        spray_object = dprops.mesh_cache.spray.get_cache_object()
        self._update_cache_object_material(
            spray_object,
            'whitewater_spray_material', 'last_whitewater_spray_material'
        )
        dprops.mesh_cache.spray.apply_duplivert_object_material()


    def _update_whitewater_dust_material(self, context):
        if not self._is_domain_set():
            return
        dprops = self._get_domain_properties()
        dust_object = dprops.mesh_cache.dust.get_cache_object()
        self._update_cache_object_material(
            dust_object,
            'whitewater_dust_material', 'last_whitewater_dust_material'
        )
        dprops.mesh_cache.dust.apply_duplivert_object_material()


    def _remove_cache_object_material(self, cache_object, enum_ident):
        if cache_object is None:
            return
        mesh = cache_object.data
        for i in range(len(mesh.materials)):
            mesh.materials.pop(index=0)


    def _add_cache_object_material(self, cache_object, enum_ident):
        if cache_object is None:
            return

        mesh = cache_object.data
        material_name = material_library.import_material(enum_ident)
        material_object = bpy.data.materials.get(material_name)
        for i in range(len(mesh.materials)):
            mesh.materials.pop(index=0)

        mesh.materials.append(material_object)
        cache_object.active_material_index = 0


    def _update_cache_object_material(self, cache_object, 
                                     material_prop, last_material_prop):
        if not getattr(self, last_material_prop):
            setattr(self, last_material_prop, 'MATERIAL_NONE')

        oldval = getattr(self, last_material_prop)
        newval = getattr(self, material_prop)

        if newval == 'MATERIAL_NONE':
            self._remove_cache_object_material(cache_object, oldval)
        elif oldval == 'MATERIAL_NONE':
            self._add_cache_object_material(cache_object, newval)
        else:
            self._remove_cache_object_material(cache_object, oldval)
            self._add_cache_object_material(cache_object, newval)

        setattr(self, last_material_prop, newval)


    def _get_material_identifier_from_name(self, material_name, material_enums):
        for e in material_enums:
            if e[1] == material_name:
                return e[0]
        return None


    def _check_material_properties_valid(self):
        try:
            self.surface_material = self.surface_material
        except:
            self.surface_material = 'MATERIAL_NONE'

        try:
            self.whitewater_foam_material = self.whitewater_foam_material
        except:
            self.whitewater_foam_material = 'MATERIAL_NONE'

        try:
            self.whitewater_bubble_material = self.whitewater_bubble_material
        except:
            self.whitewater_bubble_material = 'MATERIAL_NONE'

        try:
            self.whitewater_spray_material = self.whitewater_spray_material
        except:
            self.whitewater_spray_material = 'MATERIAL_NONE'

        try:
            self.whitewater_dust_material = self.whitewater_dust_material
        except:
            self.whitewater_dust_material = 'MATERIAL_NONE'

        try:
            self.material_import = self.material_import
        except:
            self.material_import = 'ALL_MATERIALS'


    def _check_material_properties(self):
        if not self._is_domain_set():
            return
        self._check_surface_material()
        self._check_foam_material()
        self._check_bubble_material()
        self._check_spray_material()
        self._check_dust_material()


    def _check_surface_material(self):
        dprops = self._get_domain_properties()
        surface_object = dprops.mesh_cache.surface.get_cache_object()
        if surface_object is None:
            return

        if len(surface_object.data.materials) == 0:
            if self.surface_material != 'MATERIAL_NONE':
                self.surface_material = 'MATERIAL_NONE'
            return

        material_idx = surface_object.active_material_index
        material = surface_object.data.materials[material_idx]
        if material is None:
            self.surface_material = 'MATERIAL_NONE'
            return

        material_enums = material_library.get_surface_material_enums_ui()
        material_id = self._get_material_identifier_from_name(material.name, material_enums)
        if material_id is not None and self.surface_material != material_id:
            self.surface_material = material_id


    def _check_foam_material(self):
        dprops = self._get_domain_properties()
        self._check_whitewater_material(dprops.mesh_cache.foam, "whitewater_foam_material")


    def _check_bubble_material(self):
        dprops = self._get_domain_properties()
        self._check_whitewater_material(dprops.mesh_cache.bubble, "whitewater_bubble_material")


    def _check_spray_material(self):
        dprops = self._get_domain_properties()
        self._check_whitewater_material(dprops.mesh_cache.spray, "whitewater_spray_material")


    def _check_dust_material(self):
        dprops = self._get_domain_properties()
        self._check_whitewater_material(dprops.mesh_cache.dust, "whitewater_dust_material")


    def _check_whitewater_material(self, mesh_cache_object, material_prop):
        dprops = self._get_domain_properties()
        new_duplivert_material = None
        new_object_material = None

        duplivert_object = mesh_cache_object.get_duplivert_object()
        if duplivert_object is not None:
            if len(duplivert_object.data.materials) == 0:
                new_duplivert_material = 'MATERIAL_NONE'
            else:
                material_idx = duplivert_object.active_material_index
                material = duplivert_object.data.materials[material_idx]
                if material is not None:
                    material_enums = material_library.get_whitewater_material_enums_ui()
                    material_id = self._get_material_identifier_from_name(material.name, material_enums)
                    new_duplivert_material = material_id

        foam_object = mesh_cache_object.get_cache_object()
        if foam_object is None:
            return

        if len(foam_object.data.materials) == 0:
            new_object_material = 'MATERIAL_NONE'
        else:
            material_idx = foam_object.active_material_index
            material = foam_object.data.materials[material_idx]
            if material is not None:
                material_enums = material_library.get_whitewater_material_enums_ui()
                material_id = self._get_material_identifier_from_name(material.name, material_enums)
                new_object_material = material_id

        if (new_duplivert_material == getattr(self, material_prop) and 
                new_object_material == getattr(self, material_prop)):
            return

        if new_duplivert_material is None:
            if new_object_material is not None and getattr(self, material_prop) != new_object_material:
                setattr(self, material_prop, new_object_material)
            return

        if new_object_material is None:
            if getattr(self, material_prop) != new_duplivert_material:
                setattr(self, material_prop, new_duplivert_material)
            return

        if getattr(self, material_prop) != new_duplivert_material:
            setattr(self, material_prop, new_duplivert_material)
            return

        if getattr(self, material_prop) != new_object_material:
            setattr(self, material_prop, new_object_material)
            return


    def _save_unused_materials_with_fake_user(self):
        """
        TODO: Remove

        material_ids = [
            self.surface_material,
            self.whitewater_foam_material,
            self.whitewater_bubble_material,
            self.whitewater_spray_material,
            self.whitewater_dust_material
        ]
        material_ids = [x for x in material_ids if x is not 'MATERIAL_NONE']
        for mid in material_ids:
            mname = material_library.material_identifier_to_name(mid)
            if mname is None:
                mname = mid
            for m in bpy.data.materials:
                if m.name == mname and m.users == 0:
                    m.use_fake_user = True
                    m.flip_fluid.is_fake_use_set_by_addon = True
                    break
        """


def register():
    bpy.utils.register_class(DomainMaterialsProperties)


def unregister():
    bpy.utils.unregister_class(DomainMaterialsProperties)