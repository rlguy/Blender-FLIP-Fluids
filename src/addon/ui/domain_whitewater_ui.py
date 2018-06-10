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

import bpy


class FlipFluidDomainTypeWhitewaterPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Whitewater"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"

    def draw(self, context):
        obj = context.scene.objects.active
        dprops = obj.flip_fluid.domain
        wprops = dprops.whitewater
        is_whitewater_enabled = wprops.enable_whitewater_simulation

        column = self.layout.column(align=True)
        column.prop(wprops, "enable_whitewater_simulation")

        column = self.layout.column(align=True)
        column.label("Whitewater Particles:")
        column.enabled = is_whitewater_enabled

        split = column.split()
        column = split.column()
        column.prop(wprops, "enable_foam")
        column = split.column()
        column.prop(wprops, "enable_bubbles")
        column = split.column()
        column.prop(wprops, "enable_spray")

        self.layout.separator()
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        box.label("Emitter Settings:")
        column = box.column(align=True)
        column.prop(wprops, "enable_whitewater_emission")

        column = box.column(align=True)
        column.prop(wprops, "whitewater_emitter_generation_rate", slider=True)

        column = box.column(align=True)
        column.prop(wprops, "wavecrest_emission_rate")
        column.prop(wprops, "turbulence_emission_rate")

        column = box.column(align=True)
        row = column.row(align=True)
        row.prop(wprops.min_max_whitewater_wavecrest_curvature, "value_min")
        row.prop(wprops.min_max_whitewater_wavecrest_curvature, "value_max")

        row = column.row(align=True)
        row.prop(wprops.min_max_whitewater_turbulence, "value_min")
        row.prop(wprops.min_max_whitewater_turbulence, "value_max")

        row = column.row(align=True)
        row.prop(wprops.min_max_whitewater_energy_speed, "value_min")
        row.prop(wprops.min_max_whitewater_energy_speed, "value_max")

        column = box.column(align=True)
        column.prop(wprops, "max_whitewater_particles")

        column = box.column(align=True)
        column.prop(wprops, "enable_whitewater_emission_near_boundary")

        self.layout.separator()
        box = self.layout.box()
        box.enabled = is_whitewater_enabled
        box.label("Particle Settings:")
        column = box.column()
        column.label("Foam:")
        column.prop(wprops, "foam_advection_strength", text="Advection Strength", slider=True)
        column.prop(wprops, "foam_layer_depth", text="Depth", slider=True)
        column.prop(wprops, "foam_layer_offset", text="Offset", slider=True)
        column.prop(wprops, "preserve_foam")

        column = column.column(align=True)
        column.enabled = wprops.preserve_foam
        column.prop(wprops, "foam_preservation_rate")
        row = column.row(align=True)
        row.prop(wprops.min_max_foam_density, "value_min")
        row.prop(wprops.min_max_foam_density, "value_max")

        column = box.column()
        column.label("Bubble:")
        column.prop(wprops, "bubble_drag_coefficient", text="Drag Coefficient", slider=True)
        column.prop(wprops, "bubble_bouyancy_coefficient", text="Buoyancy Coefficient")

        column = box.column(align=True)
        column.label("Spray:")
        column.prop(wprops, "spray_drag_coefficient", text="Drag Coefficient", slider=True)

        self.layout.separator()
        column = box.column(align=True)
        split = column.split()
        column = split.column(align=True)
        column.label("Lifespan:")
        column.prop(wprops.min_max_whitewater_lifespan, "value_min", text="Min")
        column.prop(wprops.min_max_whitewater_lifespan, "value_max", text="Max")
        column.prop(wprops, "whitewater_lifespan_variance", text="Variance")

        column = split.column(align=True)
        column.label("Lifespan Modifiers:")
        column.prop(wprops, "foam_lifespan_modifier", text="Foam")
        column.prop(wprops, "bubble_lifespan_modifier", text="Bubble")
        column.prop(wprops, "spray_lifespan_modifier", text="Spray")

        column = box.column()
        column.label("Behaviour At Boundary:")
        row = box.row()
        column = row.column(align=True)
        column.label("Foam:")
        column.prop(wprops, "foam_boundary_behaviour", text="")
        if wprops.foam_boundary_behaviour != 'BEHAVIOUR_COLLIDE':
            r = column.row(align=True)
            r.prop(wprops, "foam_boundary_active", index=0, text="X –")
            r.prop(wprops, "foam_boundary_active", index=1, text="X+")
            r = column.row(align=True)
            r.prop(wprops, "foam_boundary_active", index=2, text="Y –")
            r.prop(wprops, "foam_boundary_active", index=3, text="Y+")
            r = column.row(align=True)
            r.prop(wprops, "foam_boundary_active", index=4, text="Z –")
            r.prop(wprops, "foam_boundary_active", index=5, text="Z+")

        column = row.column(align=True)
        column.label("Bubble:")
        column.prop(wprops, "bubble_boundary_behaviour", text="")
        if wprops.bubble_boundary_behaviour != 'BEHAVIOUR_COLLIDE':
            r = column.row(align=True)
            r.prop(wprops, "bubble_boundary_active", index=0, text="X –")
            r.prop(wprops, "bubble_boundary_active", index=1, text="X+")
            r = column.row(align=True)
            r.prop(wprops, "bubble_boundary_active", index=2, text="Y –")
            r.prop(wprops, "bubble_boundary_active", index=3, text="Y+")
            r = column.row(align=True)
            r.prop(wprops, "bubble_boundary_active", index=4, text="Z –")
            r.prop(wprops, "bubble_boundary_active", index=5, text="Z+")

        column = row.column(align=True)
        column.label("Spray:")
        column.prop(wprops, "spray_boundary_behaviour", text="")
        if wprops.spray_boundary_behaviour != 'BEHAVIOUR_COLLIDE':
            r = column.row(align=True)
            r.prop(wprops, "spray_boundary_active", index=0, text="X –")
            r.prop(wprops, "spray_boundary_active", index=1, text="X+")
            r = column.row(align=True)
            r.prop(wprops, "spray_boundary_active", index=2, text="Y –")
            r.prop(wprops, "spray_boundary_active", index=3, text="Y+")
            r = column.row(align=True)
            r.prop(wprops, "spray_boundary_active", index=4, text="Z –")
            r.prop(wprops, "spray_boundary_active", index=5, text="Z+")
    

def register():
    bpy.utils.register_class(FlipFluidDomainTypeWhitewaterPanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeWhitewaterPanel)
