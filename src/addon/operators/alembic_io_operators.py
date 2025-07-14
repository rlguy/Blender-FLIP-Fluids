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


import bpy, bpy_extras
import os
from . import helper_operators


class FLIPFluidsAlembicImporter(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "flip_fluid_operators.flip_fluids_alembic_importer"
    bl_label = "Import FF Alembic"
    bl_options = {'PRESET', 'UNDO'}
    bl_description = ("Import and set up a FLIP Fluids Alembic cache")

    filename_ext = ".abc"
    filter_glob: bpy.props.StringProperty(default="*.abc", options={'HIDDEN'})


    def find_flip_fluids_mesh(self, bl_object_list, name_prefix):
        bl_object = None
        for obj in bl_object_list:
            if obj.type == 'MESH' and obj.name.startswith(name_prefix):
                bl_object = obj
                break
        return bl_object


    def apply_default_modifier_settings(self, target_object, gn_modifier):
        gn_modifier["Input_2_use_attribute"] = True
        gn_modifier["Input_2_attribute_name"] = 'flip_velocity'
        gn_modifier["Output_3_attribute_name"] = 'velocity'

        gn_name = gn_modifier.name
        if gn_name.startswith("FF_GeometryNodesSurface"):
            # Depending on FLIP Fluids version, the GN set up may not
            # have these inputs. Available in FLIP Fluids 1.7.2 or later.
            try:
                # Enable Motion Blur
                gn_modifier["Input_6"] = True
            except:
                pass

        if gn_name.startswith("FF_GeometryNodesWhitewater") or gn_name.startswith("FF_GeometryNodesFluidParticles"):
            # Depending on FLIP Fluids version, the GN set up may not
            # have these inputs. Available in FLIP Fluids 1.7.2 or later.
            try:
                # Material
                gn_modifier["Input_5"] = target_object.active_material
            except:
                pass

            try:
                # Enable Motion Blur
                gn_modifier["Input_8"] = True
            except:
                pass

            try:
                # Enable Point Cloud
                gn_modifier["Input_9"] = True
            except:
                pass

            try:
                # Enable Instancing
                gn_modifier["Input_10"] = False
            except:
                pass


    def add_smooth_modifier(self, target_object):
        smooth_mod = target_object.modifiers.new("FF_Smooth", "SMOOTH")
        smooth_mod.factor = 1.5
        smooth_mod.iterations = 0
        return smooth_mod


    def execute(self, context):
        print("FLIP Fluids Alembic Import: <" + self.filepath + ">")

        bpy.ops.wm.alembic_import(filepath=self.filepath)

        bl_fluid_surface = self.find_flip_fluids_mesh(bpy.context.selected_objects, "fluid_surface")
        bl_fluid_particles = self.find_flip_fluids_mesh(bpy.context.selected_objects, "fluid_particles")
        bl_whitewater_foam = self.find_flip_fluids_mesh(bpy.context.selected_objects, "whitewater_foam")
        bl_whitewater_bubble = self.find_flip_fluids_mesh(bpy.context.selected_objects, "whitewater_bubble")
        bl_whitewater_spray = self.find_flip_fluids_mesh(bpy.context.selected_objects, "whitewater_spray")
        bl_whitewater_dust = self.find_flip_fluids_mesh(bpy.context.selected_objects, "whitewater_dust")

        blend_filename = "geometry_nodes_library.blend"
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", blend_filename)

        found_mesh_cache_list = []

        if bl_fluid_surface is not None:
            self.add_smooth_modifier(bl_fluid_surface)
            helper_operators.add_geometry_node_modifier(bl_fluid_surface, resource_filepath, "FF_AlembicImportSurface")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_fluid_surface, resource_filepath, "FF_GeometryNodesSurface")
            self.apply_default_modifier_settings(bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found fluid surface cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Surface")
        
        if bl_fluid_particles is not None:
            helper_operators.add_geometry_node_modifier(bl_fluid_particles, resource_filepath, "FF_AlembicImportFluidParticles")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_fluid_particles, resource_filepath, "FF_GeometryNodesFluidParticles")
            self.apply_default_modifier_settings(bl_fluid_particles, gn_modifier)
            self.report({'INFO'}, "Found fluid particle cache... Initialized geometry nodes")
            found_mesh_cache_list.append("FluidParticles")
        
        if bl_whitewater_foam is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_foam, resource_filepath, "FF_AlembicImportWhitewaterFoam")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_foam, resource_filepath, "FF_GeometryNodesWhitewaterFoam")
            self.apply_default_modifier_settings(bl_whitewater_foam, gn_modifier)
            self.report({'INFO'}, "Found whitewater foam cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Foam")
        
        if bl_whitewater_bubble is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_bubble, resource_filepath, "FF_AlembicImportWhitewaterBubble")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_bubble, resource_filepath, "FF_GeometryNodesWhitewaterBubble")
            self.apply_default_modifier_settings(bl_whitewater_bubble, gn_modifier)
            self.report({'INFO'}, "Found whitewater bubble cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Bubble")
        
        if bl_whitewater_spray is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_spray, resource_filepath, "FF_AlembicImportWhitewaterSpray")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_spray, resource_filepath, "FF_GeometryNodesWhitewaterSpray")
            self.apply_default_modifier_settings(bl_whitewater_spray, gn_modifier)
            self.report({'INFO'}, "Found whitewater spray cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Spray")
        
        if bl_whitewater_dust is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_dust, resource_filepath, "FF_AlembicImportWhitewaterDust")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_dust, resource_filepath, "FF_GeometryNodesWhitewaterDust")
            self.apply_default_modifier_settings(bl_whitewater_dust, gn_modifier)
            self.report({'INFO'}, "Found whitewater dust cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Dust")

        if found_mesh_cache_list:
            found_mesh_cache_string = "/".join(found_mesh_cache_list)
            self.report({'INFO'}, "Found and initialized " + found_mesh_cache_string + " objects and geometry nodes.")
        else:
            self.report({'WARNING'}, "No valid FLIP Fluids addon meshes found. Is this Alembic file a FLIP Fluids addon export?")

        return {'FINISHED'}


class FLIPFluidsAlembicExporter(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "flip_fluid_operators.flip_fluids_alembic_exporter"
    bl_label = "Export FF Alembic"
    bl_options = {'PRESET', 'UNDO'}
    bl_description = ("Prepare a FLIP Fluids simulation for Alembic export. After the file dialog, this exporter will" + 
                      " launch a new command line window and start exporting the simulation to the" +
                      " Alembic (.abc) format. This Blend file will need to be saved before accessing"
                      " this operator")

    filename_ext = ".abc"
    filter_glob: bpy.props.StringProperty(default="*.abc", options={'HIDDEN'})


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def draw(self, context):
        hprops = context.scene.flip_fluid_helper

        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        header, body = self.layout.panel("alembic_scene", default_closed=False)
        header.label(text="Scene")
        if body:
            column = body.column(align=True)
            column.prop(hprops, "alembic_frame_range_mode", text="Frame Range")

            if hprops.alembic_frame_range_mode == 'FRAME_RANGE_TIMELINE':
                column.prop(context.scene, "frame_start")
                column.prop(context.scene, "frame_end")
            else:
                column.prop(hprops.alembic_frame_range_custom, "value_min")
                column.prop(hprops.alembic_frame_range_custom, "value_max")

            column.separator()
            column.prop(hprops, "alembic_global_scale")

        header, body = self.layout.panel("alembic_include", default_closed=False)
        header.label(text="Include")
        if body:
            column = body.column(heading="Mesh", align=True)
            column.prop(hprops, "alembic_export_surface")
            column.prop(hprops, "alembic_export_fluid_particles")
            column.prop(hprops, "alembic_export_foam")
            column.prop(hprops, "alembic_export_bubble")
            column.prop(hprops, "alembic_export_spray")
            column.prop(hprops, "alembic_export_dust")

            column = body.column(heading="Attributes", align=True)
            column.prop(hprops, "alembic_export_velocity")
            column.prop(hprops, "alembic_export_color")

        header, body = self.layout.panel("alembic_command", default_closed=True)
        header.label(text="Command")
        if body:
            column = body.column(heading="Attributes", align=True)
            column.operator("flip_fluid_operators.helper_cmd_alembic_export_to_clipboard", text="Copy Command to Clipboard", icon='COPYDOWN')


    def execute(self, context):
        print("FLIP Fluids Alembic Export: <" + self.filepath + ">")

        hprops = context.scene.flip_fluid_helper
        hprops.alembic_output_filepath = self.filepath
        bpy.ops.flip_fluid_operators.helper_command_line_alembic_export('INVOKE_DEFAULT')

        return {'FINISHED'}



def menu_func_import(self, context):
    self.layout.operator(FLIPFluidsAlembicImporter.bl_idname, text="FLIP Fluids Alembic (.abc)")


def menu_func_export(self, context):
    self.layout.operator(FLIPFluidsAlembicExporter.bl_idname, text="FLIP Fluids Alembic (.abc)")


def register():
    bpy.utils.register_class(FLIPFluidsAlembicImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.utils.register_class(FLIPFluidsAlembicExporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(FLIPFluidsAlembicImporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.unregister_class(FLIPFluidsAlembicExporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
