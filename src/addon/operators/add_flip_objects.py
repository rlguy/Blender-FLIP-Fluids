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

import bpy, mathutils, math


class VIEW3D_MT_FLIPFluidsAdd(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_FLIPFluidsAdd"
    bl_label = "FLIP Fluids"

    def draw(self, context):
        column = self.layout.column(align=True)
        column.operator("flip_fluid_operators.helper_create_domain", text="Create FLIP Domain", icon='CUBE')

        column.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="FLIP Obstacle",
                icon='MESH_CUBE'
                ).object_type="TYPE_OBSTACLE"
        column.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="FLIP Fluid",
                icon='MOD_FLUIDSIM'
                ).object_type="TYPE_FLUID"
        column.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="FLIP Inflow",
                icon='MOD_FLUIDSIM'
                ).object_type="TYPE_INFLOW"
        column.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="FLIP Outflow",
                icon='UGLYPACKAGE'
                ).object_type="TYPE_OUTFLOW"
        column.operator(
                "flip_fluid_operators.helper_add_objects", 
                text="FLIP Force Field",
                icon='OUTLINER_OB_FORCE_FIELD'
                ).object_type="TYPE_FORCE_FIELD"

        column.separator()
        column.operator("flip_fluid_operators.add_quick_liquid", text="Create Quick Liquid", icon='MOD_FLUIDSIM')
        column.operator("flip_fluid_operators.add_thick_viscous_liquid", text="Create Thick Viscous Liquid", icon='MOD_FLUIDSIM')
        column.operator("flip_fluid_operators.add_thin_viscous_liquid", text="Create Thin Viscous Liquid", icon='MOD_FLUIDSIM')

        column.separator()
        column.operator("flip_fluid_operators.helper_remove_objects", text="Remove FLIP Object", icon='REMOVE')
        column.operator("flip_fluid_operators.helper_delete_domain", text="Delete FLIP Domain", icon='X')


def add_menu_func(self, context):
    self.layout.separator()

    icon = context.scene.flip_fluid.get_logo_icon()
    if icon is not None:
        self.layout.menu("VIEW3D_MT_FLIPFluidsAdd", text="FLIP Fluids", icon_value=context.scene.flip_fluid.get_logo_icon().icon_id)
    else:
        self.layout.menu("VIEW3D_MT_FLIPFluidsAdd", text="FLIP Fluids", icon="MOD_FLUIDSIM")


def is_default_cube( bl_object):
    if bl_object is None:
        return False

    if bl_object.type != 'MESH':
        return False

    if bl_object.name != "Cube":
        return False

    if len(bl_object.modifiers) != 0:
        return False

    mesh_data = bl_object.data
    if mesh_data.name != "Cube":
        return False

    default_vertices = [
            mathutils.Vector((-1.0, -1.0, -1.0)), 
            mathutils.Vector((-1.0, 1.0, -1.0)),
            mathutils.Vector((1.0, 1.0, -1.0)), 
            mathutils.Vector((1.0, -1.0, -1.0)),
            mathutils.Vector((-1.0, -1.0, 1.0)), 
            mathutils.Vector((-1.0, 1.0, 1.0)),
            mathutils.Vector((1.0, 1.0, 1.0)), 
            mathutils.Vector((1.0, -1.0, 1.0))
            ]

    default_faces = [
            (4,5,1,0), 
            (5,6,2,1), 
            (6,7,3,2), 
            (7,4,0,3), 
            (0,1,2,3), 
            (7,6,5,4)
            ]

    if len(mesh_data.vertices) != len(default_vertices) or len(mesh_data.polygons) != len(default_faces):
        return False

    mesh_vertices = sorted([v.co for v in mesh_data.vertices], key=lambda v: (v.x, v.y, v.z))
    expected_mesh_vertices = sorted(default_vertices, key=lambda v: (v.x, v.y, v.z))
    eps = 1e-5
    for i in range(len(mesh_vertices)):
        vdiff = mesh_vertices[i] - expected_mesh_vertices[i]
        if abs(vdiff[0]) > eps or abs(vdiff[1]) > eps or abs(vdiff[2]) > eps:
            return False

    return True


class FlipFluidAddQuickLiquid(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.add_quick_liquid"
    bl_label = "FLIP Fluids Quick Liquid"
    bl_description = ("Create a basic FLIP Fluid liquid simulation. The Blend file must not already contain" + 
                      " a domain object to run this operator. This operator will function best in a new" + 
                      " saved Blend file with no FLIP objects")

    @classmethod
    def poll(cls, context):
        return True


    def check_and_report_operator_context_errors(self, context):
        # Cannot set up simulation with an existing domain
        bl_domain = bpy.context.scene.flip_fluid.get_domain_object()
        if bl_domain is not None:
            self.report({'ERROR'}, "Blend file already contains a domain <" + bl_domain.name + ">. Remove the domain or create and save a new Blend file.")
            return {'CANCELLED'}


    def create_quick_liquid(self):
        if bpy.context.mode != 'OBJECT':
            # Simulation setup must be in object mode
            bpy.ops.object.mode_set(mode='OBJECT')

        z_offset = 2.0

        # Delete default cube if selected
        bl_default_cube = bpy.context.active_object
        if is_default_cube(bl_default_cube):
            bpy.ops.object.select_all(action='DESELECT')
            bl_default_cube.select_set(True)
            bpy.ops.object.delete() 

        # Create Domain
        bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0.0, 0.0, 0.0 + z_offset))
        bl_cube = bpy.context.active_object
        bl_cube.name = "FLIP Domain"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_cube.flip_fluid.object_type = 'TYPE_DOMAIN'

        # Create Fluid Cube
        bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0.0, 0.0, -1.75 + z_offset), scale=(1.0, 1.0, 0.125))
        bl_cube = bpy.context.active_object
        bl_cube.name = "Fluid"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_cube.flip_fluid.object_type = 'TYPE_FLUID'

        # Create Inflow
        bpy.ops.mesh.primitive_cylinder_add(radius=0.25, location=(0.0, 0.0, 1.25 + z_offset), scale=(1.0, 1.0, 0.25))
        bl_cylinder = bpy.context.active_object
        bl_cylinder.name = "Inflow"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_cylinder.flip_fluid.object_type = 'TYPE_INFLOW'

        inflow_props = bl_cylinder.flip_fluid.get_property_group()
        inflow_props.inflow_velocity = (0.0, 0.0, -3.0)

        inflow_props.is_enabled = True
        bl_cylinder.keyframe_insert(data_path="flip_fluid.inflow.is_enabled", frame=1)
        inflow_props.is_enabled = False
        bl_cylinder.keyframe_insert(data_path="flip_fluid.inflow.is_enabled", frame=20)

        # Create Obstacle
        bpy.ops.mesh.primitive_ico_sphere_add(
                radius=0.75, 
                location=(0.0, 0.0, -0.25 + z_offset), 
                scale=(1.0, 1.0, 0.25), 
                rotation=(0.0, 0.5, 0.0),
                subdivisions=4
                )
        bpy.ops.object.shade_smooth()
        bl_sphere = bpy.context.active_object
        bl_sphere.name = "Obstacle"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_sphere.flip_fluid.object_type = 'TYPE_OBSTACLE'

        # Domain Settings
        domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()

        try:
            # Materials may not be available depending on addon version
            domain_properties.materials.surface_material = 'FF Water (ocean volumetric)'
        except:
            pass

        # Surface Settings
        domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()
        bl_fluid_surface = domain_properties.mesh_cache.surface.get_cache_object()
        for mod in bl_fluid_surface.modifiers:
            if mod.type == 'SMOOTH':
                mod.factor = 1.5
                mod.iterations = 5
                
        # Misc Settings
        bpy.ops.flip_fluid_operators.helper_initialize_motion_blur()
        bpy.ops.flip_fluid_operators.helper_organize_outliner()

        if bpy.data.filepath:
            bpy.context.scene.render.filepath = ""
            bpy.ops.flip_fluid_operators.relative_to_blend_render_output()


    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        self.create_quick_liquid()

        return {'FINISHED'}


class FlipFluidAddThickViscousLiquid(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.add_thick_viscous_liquid"
    bl_label = "FLIP Fluids Thick Viscous Liquid"
    bl_description = ("Create a basic thick viscous liquid that buckles and coils. The Blend file must not already contain" + 
                      " a domain object to run this operator. This operator will function best in a new" + 
                      " saved Blend file with no FLIP objects")

    @classmethod
    def poll(cls, context):
        return True


    def check_and_report_operator_context_errors(self, context):
        # Cannot set up simulation with an existing domain
        bl_domain = bpy.context.scene.flip_fluid.get_domain_object()
        if bl_domain is not None:
            self.report({'ERROR'}, "Blend file already contains a domain <" + bl_domain.name + ">. Remove the domain or create and save a new Blend file.")
            return {'CANCELLED'}


    def create_thick_viscous_liquid(self):
        if bpy.context.mode != 'OBJECT':
            # Simulation setup must be in object mode
            bpy.ops.object.mode_set(mode='OBJECT')

        z_offset = 2.0

        # Delete default cube if selected
        bl_default_cube = bpy.context.active_object
        if is_default_cube(bl_default_cube):
            bpy.ops.object.select_all(action='DESELECT')
            bl_default_cube.select_set(True)
            bpy.ops.object.delete() 

        # Create Domain
        bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0.0, 0.0, 0.0 + z_offset), scale=(0.5, 0.5, 1.0))
        bl_domain = bpy.context.active_object
        bl_domain.name = "FLIP Domain"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_domain.flip_fluid.object_type = 'TYPE_DOMAIN'

        # Domain Settings
        domain_props = bl_domain.flip_fluid.get_property_group()
        domain_props.simulation.resolution = 120
        domain_props.surface.subdivisions = 2
        domain_props.world.enable_viscosity = True
        domain_props.world.viscosity = 15
        domain_props.advanced.jitter_surface_particles = True

        try:
            # Materials may not be available depending on addon version
            domain_props.materials.surface_material = 'FF Caramel'
        except:
            pass

        # Create Inflow
        bpy.ops.mesh.primitive_cylinder_add(radius=0.25, location=(-0.125, -0.125, 1.25 + z_offset), scale=(0.4, 0.4, 0.25))
        bl_cylinder = bpy.context.active_object
        bl_cylinder.name = "Inflow"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_cylinder.flip_fluid.object_type = 'TYPE_INFLOW'

        inflow_props = bl_cylinder.flip_fluid.get_property_group()
        inflow_props.is_enabled = True
        bl_cylinder.keyframe_insert(data_path="flip_fluid.inflow.is_enabled", frame=1)
        inflow_props.is_enabled = False
        bl_cylinder.keyframe_insert(data_path="flip_fluid.inflow.is_enabled", frame=150)

        # Create Obstacle
        scale = math.sqrt(5.0/4.0)
        bpy.ops.mesh.primitive_ico_sphere_add(
                radius=2.0, 
                location=(-1.0, -1.0, -3.0 + z_offset), 
                scale=(scale, scale, scale),
                subdivisions=5
                )
        bl_sphere = bpy.context.active_object
        bl_sphere.name = "Obstacle"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_sphere.flip_fluid.object_type = 'TYPE_OBSTACLE'

        obstacle_props = bl_sphere.flip_fluid.get_property_group()
        obstacle_props.friction = 1.0

        mod = bl_sphere.modifiers.new("Boolean", "BOOLEAN")
        mod.operation = 'INTERSECT'
        mod.object = bl_domain

        # Surface Settings
        domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()
        bl_fluid_surface = domain_properties.mesh_cache.surface.get_cache_object()
        for mod in bl_fluid_surface.modifiers:
            if mod.type == 'SMOOTH':
                mod.factor = 1.5
                mod.iterations = 40
                
        # Misc Settings
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 250
        bpy.context.scene.render.fps = 24

        bpy.ops.flip_fluid_operators.helper_initialize_motion_blur()
        bpy.ops.flip_fluid_operators.helper_organize_outliner()

        if bpy.data.filepath:
            bpy.context.scene.render.filepath = ""
            bpy.ops.flip_fluid_operators.relative_to_blend_render_output()


    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        self.create_thick_viscous_liquid()

        return {'FINISHED'}


class FlipFluidAddThinViscousLiquid(bpy.types.Operator):
    bl_idname = "flip_fluid_operators.add_thin_viscous_liquid"
    bl_label = "FLIP Fluids Thin Viscous Liquid"
    bl_description = ("Create a smooth paint-like liquid with low viscosity and surface tension. The Blend file must not already contain" + 
                      " a domain object to run this operator. This operator will function best in a new" + 
                      " saved Blend file with no FLIP objects")

    @classmethod
    def poll(cls, context):
        return True


    def check_and_report_operator_context_errors(self, context):
        # Cannot set up simulation with an existing domain
        bl_domain = bpy.context.scene.flip_fluid.get_domain_object()
        if bl_domain is not None:
            self.report({'ERROR'}, "Blend file already contains a domain <" + bl_domain.name + ">. Remove the domain or create and save a new Blend file.")
            return {'CANCELLED'}


    def create_thin_viscous_liquid(self):
        if bpy.context.mode != 'OBJECT':
            # Simulation setup must be in object mode
            bpy.ops.object.mode_set(mode='OBJECT')

        z_offset = 2.0

        # Delete default cube if selected
        bl_default_cube = bpy.context.active_object
        if is_default_cube(bl_default_cube):
            bpy.ops.object.select_all(action='DESELECT')
            bl_default_cube.select_set(True)
            bpy.ops.object.delete() 

        # Create Domain
        bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0.0, 0.0, -0.8 + z_offset), scale=(0.5, 0.5, 0.6))
        bl_domain = bpy.context.active_object
        bl_domain.name = "FLIP Domain"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_domain.flip_fluid.object_type = 'TYPE_DOMAIN'

        # Domain Settings
        domain_props = bl_domain.flip_fluid.get_property_group()
        domain_props.simulation.resolution = 100
        domain_props.world.enable_viscosity = True
        domain_props.world.viscosity_settings_expaned = True
        domain_props.world.viscosity = 0.01
        domain_props.world.surface_tension_settings_expaned = True
        domain_props.world.enable_surface_tension = True
        domain_props.world.surface_tension = 0.3
        domain_props.advanced.jitter_surface_particles = True

        try:
            # Materials may not be available depending on addon version
            domain_props.materials.surface_material = 'FF Caramel'
        except:
            pass

        # Create Inflow
        bpy.ops.mesh.primitive_cylinder_add(radius=0.25, location=(-0.5, -0.5, 0.0 + z_offset), scale=(0.4, 0.4, 0.125))
        bl_cylinder = bpy.context.active_object
        bl_cylinder.name = "Inflow"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_cylinder.flip_fluid.object_type = 'TYPE_INFLOW'

        # Create Obstacle
        scale = math.sqrt(5.0/4.0)
        bpy.ops.mesh.primitive_ico_sphere_add(
                radius=2.0, 
                location=(-1.0, -1.0, -3.0 + z_offset), 
                scale=(scale, scale, scale),
                subdivisions=5
                )
        bl_sphere = bpy.context.active_object
        bl_sphere.name = "Obstacle"

        bpy.ops.flip_fluid_operators.flip_fluid_add()
        bl_sphere.flip_fluid.object_type = 'TYPE_OBSTACLE'

        obstacle_props = bl_sphere.flip_fluid.get_property_group()
        obstacle_props.friction = 1.0

        mod = bl_sphere.modifiers.new("Boolean", "BOOLEAN")
        mod.operation = 'INTERSECT'
        mod.object = bl_domain

        # Surface Settings
        domain_properties = bpy.context.scene.flip_fluid.get_domain_properties()
        bl_fluid_surface = domain_properties.mesh_cache.surface.get_cache_object()
        for mod in bl_fluid_surface.modifiers:
            if mod.type == 'SMOOTH':
                mod.factor = 1.5
                mod.iterations = 15
                
        # Misc Settings
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 200
        bpy.context.scene.render.fps = 24

        bpy.ops.flip_fluid_operators.helper_initialize_motion_blur()
        bpy.ops.flip_fluid_operators.helper_organize_outliner()

        if bpy.data.filepath:
            bpy.context.scene.render.filepath = ""
            bpy.ops.flip_fluid_operators.relative_to_blend_render_output()


    def execute(self, context):
        error_return = self.check_and_report_operator_context_errors(context)
        if error_return:
            return error_return

        self.create_thin_viscous_liquid()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(FlipFluidAddQuickLiquid)
    bpy.utils.register_class(FlipFluidAddThickViscousLiquid)
    bpy.utils.register_class(FlipFluidAddThinViscousLiquid)
    bpy.utils.register_class(VIEW3D_MT_FLIPFluidsAdd)

    bpy.types.VIEW3D_MT_add.append(add_menu_func)


def unregister():
    bpy.utils.unregister_class(FlipFluidAddQuickLiquid)
    bpy.utils.unregister_class(FlipFluidAddThickViscousLiquid)
    bpy.utils.unregister_class(FlipFluidAddThinViscousLiquid)
    bpy.utils.unregister_class(VIEW3D_MT_FLIPFluidsAdd)

    bpy.types.VIEW3D_MT_add.remove(add_menu_func)