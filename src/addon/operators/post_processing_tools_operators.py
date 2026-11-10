# Blender FLIP Fluids Add-on
# Copyright (C) 2026 Ryan L. Guy & Dennis Fassbaender
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

import bpy


from ..objects import flip_fluid_attribute
from .. import render


class FLIPFLUID_UL_RemapUVWAttributesNewItem(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_new_item"
    bl_label = "Add Generated UVW Attribute"
    bl_description = "Adds a new target frame to bind UVW coordinates. Use this to blend, transition, or reassemble textures at a set frame in the simulation"

    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        return dprops is not None


    def execute(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        item = dprops.particles.remap_uvw_attributes.add()
        item.frame = context.scene.frame_current
        flip_fluid_attribute.update_remap_uvw_name(item, context)

        item_list = dprops.particles.remap_uvw_attributes
        dprops.particles.remap_uvw_attributes_list_index = len(item_list) - 1

        return {'FINISHED'}


class FLIPFLUID_UL_RemapUVWAttributesDeleteItem(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_delete_item"
    bl_label = "Delete Generated UVW Attribute"
    bl_description = "Delete the generated UVW attribute"

    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return len(dprops.particles.remap_uvw_attributes) > 0


    def execute(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()

        item_list = dprops.particles.remap_uvw_attributes
        list_index = dprops.particles.remap_uvw_attributes_list_index

        item_list.remove(list_index)
        dprops.particles.remap_uvw_attributes_list_index = min(max(0, list_index - 1), len(item_list) - 1)
        
        return {'FINISHED'}


class FLIPFLUID_UL_RemapUVWAttributesMoveItem(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_move_item"
    bl_label = "Move Item"
    bl_description = "Move item up or down in the list"
    
    direction: bpy.props.EnumProperty(
        items=[('UP', "Up", ""), ('DOWN', "Down", "")]
    )
    
    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return False
        return len(dprops.particles.remap_uvw_attributes) > 0

    def execute(self, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        item_list = dprops.particles.remap_uvw_attributes
        active_index = dprops.particles.remap_uvw_attributes_list_index

        target_index = active_index - 1 if self.direction == 'UP' else active_index + 1
        if target_index < 0 or target_index >= len(item_list):
            return {'CANCELLED'}
        
        item_list.move(active_index, target_index)
        dprops.particles.remap_uvw_attributes_list_index = target_index
        return {'FINISHED'}


class FLIPFLUID_UL_RemapUVWAttributesLoadFrame(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_load_frame"
    bl_label = "Jump to Bind Frame"
    bl_description = "Jump to the Bind Frame of this generated attribute"
    
    frame: bpy.props.IntProperty(default=1)
    
    @classmethod
    def poll(cls, context):
        dprops = bpy.context.scene.flip_fluid.get_domain_properties()
        return dprops is not None

    def execute(self, context):
        if context.scene.frame_current == self.frame:
            bpy.ops.flip_fluid_operators.reload_frame()
        else:
            context.scene.frame_set(self.frame)
        return {'FINISHED'}


class FLIPFLUIDRemapUVWAttributesEnableFluidParticles(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_enable_fluid_particles"
    bl_label = "Enable"
    bl_description = "Enable the 'Domain > Particles > Enable Fluid Particle Export' option required for this feature. Fluid particles are required to be baked to use this feature"
    
    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None

    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.particles.enable_fluid_particle_output = True
        return {'FINISHED'}


class FLIPFLUIDRemapUVWAttributesEnableUVWAttribute(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_enable_uvw_attribute"
    bl_label = "Enable"
    bl_description = "Enable the 'Domain > Particles > Attributes > UVW' option required for this feature. Fluid particles UVW attributes are required to be baked to use this feature"
    
    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None

    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.particles.enable_fluid_particle_uvw_attribute = True
        return {'FINISHED'}


class FLIPFLUIDRemapUVWAttributesEnableUIDAttribute(bpy.types.Operator):
    bl_idname = "ffops.remap_uvw_attributes_enable_uid_attribute"
    bl_label = "Enable"
    bl_description = "Enable the 'Domain > Particles > Attributes > UID' option and disable the 'Reuse UIDs' option required for this feature. Fluid particles UID attributes are required to be baked to use this feature"
    
    @classmethod
    def poll(cls, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        return dprops is not None

    def execute(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        dprops.particles.enable_fluid_particle_uid_attribute = True
        dprops.particles.enable_fluid_particle_uid_attribute_reuse = False
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FLIPFLUID_UL_RemapUVWAttributesNewItem)
    bpy.utils.register_class(FLIPFLUID_UL_RemapUVWAttributesDeleteItem)
    bpy.utils.register_class(FLIPFLUID_UL_RemapUVWAttributesMoveItem)
    bpy.utils.register_class(FLIPFLUID_UL_RemapUVWAttributesLoadFrame)
    bpy.utils.register_class(FLIPFLUIDRemapUVWAttributesEnableFluidParticles)
    bpy.utils.register_class(FLIPFLUIDRemapUVWAttributesEnableUVWAttribute)
    bpy.utils.register_class(FLIPFLUIDRemapUVWAttributesEnableUIDAttribute)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_UL_RemapUVWAttributesNewItem)
    bpy.utils.unregister_class(FLIPFLUID_UL_RemapUVWAttributesDeleteItem)
    bpy.utils.unregister_class(FLIPFLUID_UL_RemapUVWAttributesMoveItem)
    bpy.utils.unregister_class(FLIPFLUID_UL_RemapUVWAttributesLoadFrame)
    bpy.utils.unregister_class(FLIPFLUIDRemapUVWAttributesEnableFluidParticles)
    bpy.utils.unregister_class(FLIPFLUIDRemapUVWAttributesEnableUVWAttribute)
    bpy.utils.unregister_class(FLIPFLUIDRemapUVWAttributesEnableUIDAttribute)