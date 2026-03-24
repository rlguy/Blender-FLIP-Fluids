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


import bpy, bpy_extras
import os
from . import helper_operators


class FLIPFluidsUSDImporter(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "flip_fluid_operators.flip_fluids_usd_importer"
    bl_label = "Import FF USD"
    bl_options = {'PRESET', 'UNDO'}
    bl_description = ("Import and set up a FLIP Fluids USD cache")

    filename_ext = ".usdc"
    filter_glob: bpy.props.StringProperty(default="*.usdc", options={'HIDDEN'})


    def find_mesh_object(self, bl_object_list, search_string):
        for obj in bl_object_list:
            if obj.type != 'MESH':
                continue
            if search_string in obj.name:
                return obj
            

    def find_pointcloud_object(self, bl_object_list, search_string):
        for obj in bl_object_list:
            if obj.type != 'POINTCLOUD':
                continue
            
            obj_parent = obj.parent
            if not obj_parent:
                continue
            
            if obj_parent.parent:
                # Duplicate ppoint cloud object
                continue
            
            if search_string in obj_parent.name:
                return obj
            
            
    def find_pointcloud_object_duplicates(self, bl_object_list):
        bl_duplicates = []
        for obj in bl_object_list:
            if obj.type != 'POINTCLOUD':
                continue
            
            obj_parent = obj.parent
            if not obj_parent:
                continue
            
            if obj_parent.parent:
                # Duplicate ppoint cloud object
                bl_duplicates.append(obj)
        
        return bl_duplicates


    def delete_object(self, bl_object):
        if bl_object.type == 'EMPTY':
            bpy.data.objects.remove(bl_object, do_unlink=True)
            return
        
        bl_object_type = bl_object.type
        bl_object_data = bl_object.data
        bpy.data.objects.remove(bl_object, do_unlink=True)
        bl_object_data.user_clear()
        
        if bl_object_type == 'MESH':
            bpy.data.meshes.remove(bl_object_data)
        elif bl_object_type == 'POINTCLOUD':
            bpy.data.pointclouds.remove(bl_object_data)
            
            
    def toggle_cycles_ray_visibility(self, bl_object, is_enabled):
        # Cycles may not be enabled in the user's preferences
        try:
            bl_object.visible_camera = is_enabled
            bl_object.visible_diffuse = is_enabled
            bl_object.visible_glossy = is_enabled
            bl_object.visible_transmission = is_enabled
            bl_object.visible_volume_scatter = is_enabled
            bl_object.visible_shadow = is_enabled
        except:
            pass
        
        
    def add_smooth_modifier(self, bl_object):
        smooth_mod = bl_object.modifiers.new("FF_Smooth", "SMOOTH")
        smooth_mod.factor = 1.5
        smooth_mod.iterations = 0
        return smooth_mod


    def execute(self, context):
        print("FLIP Fluids Universal Scene Description (USD) Import: <" + self.filepath + ">")

        bpy.ops.wm.usd_import(
            filepath=self.filepath,
            import_cameras=False,
            import_lights=False,
            import_materials=False,
            import_all_materials=False,
            support_scene_instancing=False,
            import_visible_only=False,
            create_collection=True,
            import_usd_preview=False,
            set_material_blend=False,
            create_world_material=False,
            merge_parent_xform=False,
            import_textures_mode='IMPORT_NONE',
            )

        # Imported Objects
        bl_objects = []
        bl_object_names = []
        for obj in bpy.context.selected_objects:
            bl_objects.append(obj)
            bl_object_names.append(obj.name)

        # Initialize Collection
        usd_collection = bpy.context.view_layer.active_layer_collection.collection
        usd_collection.name = "FLIPFluidsUSD"

        # Initialize Domain
        bl_domain = self.find_mesh_object(bl_objects, "ff_usd_domain")
        if bl_domain:
            bl_domain.name = "FLIP Domain"
            bl_domain.data.name = "flip_domain_data"
            
            if bl_domain.parent:
                bl_domain.location = bl_domain.parent.location
            
        # Initialize Fluid Surface
        bl_fluid_surface = self.find_mesh_object(bl_objects, "ff_usd_fluid_surface")
        if bl_fluid_surface:
            bl_fluid_surface.name = "fluid_surface"
            bl_fluid_surface.data.name = "fluid_surface_data"
            
        # Initialize Point Clouds
        point_cloud_info = [
            {"search_string": "ff_usd_fluid_particles",   "bl_object_name": "fluid_particles"},
            {"search_string": "ff_usd_whitewater_foam",   "bl_object_name": "whitewater_foam"},
            {"search_string": "ff_usd_whitewater_bubble", "bl_object_name": "whitewater_bubble"},
            {"search_string": "ff_usd_whitewater_spray",  "bl_object_name": "whitewater_spray"},
            {"search_string": "ff_usd_whitewater_dust",   "bl_object_name": "whitewater_dust"},
            ]

        for info in point_cloud_info:
            bl_object = self.find_pointcloud_object(bl_objects, info["search_string"])
            if bl_object:
                bl_object.name = info["bl_object_name"]
                bl_object.data.name = info["bl_object_name"] + "_data"
                
        # Remove Duplicate Point Clouds
        bl_pointcloud_duplicates = self.find_pointcloud_object_duplicates(bl_objects)
        for obj in bl_pointcloud_duplicates:
            self.delete_object(obj)
            
        # Remove Empty Objects
        for bl_object in bpy.context.selected_objects:
            if bl_object.type == 'EMPTY':
                self.delete_object(bl_object)
                
        # Set set simulation meshes as domain children
        if bl_domain:
            for bl_object in bpy.context.selected_objects:
                if bl_object == bl_domain:
                    continue
                bl_object.parent = bl_domain
                
        # Collapse current modifiers
        for bl_object in bpy.context.selected_objects:
            for mod in bl_object.modifiers:
                mod.show_expanded = False

        # Set Domain Visibility
        if bl_domain:
            bl_domain.hide_render = True
            bl_domain.display_type = 'BOUNDS'
            self.toggle_cycles_ray_visibility(bl_domain, False)
                
        # Add FF_GeometryNodes modifiers
        blend_filename = "geometry_nodes_library.blend"
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_filepath = os.path.join(parent_path, "resources", "geometry_nodes", blend_filename)

        for bl_object in bpy.context.selected_objects:
            if bl_object == bl_domain:
                continue
            
            if "fluid_surface" in bl_object.name:
                self.add_smooth_modifier(bl_fluid_surface)
                gn_modifier = helper_operators.add_geometry_node_modifier(bl_fluid_surface, resource_filepath, "FF_GeometryNodesUSDSurface")
                try:
                    gn_modifier["Socket_7"] = bl_domain
                except:
                    pass

            if "fluid_particles" in bl_object.name:
                gn_modifier = helper_operators.add_geometry_node_modifier(bl_object, resource_filepath, "FF_USDImportParticles")
                gn_modifier.show_expanded = False

                gn_modifier = helper_operators.add_geometry_node_modifier(bl_object, resource_filepath, "FF_GeometryNodesUSDFluidParticles")
                try:
                    gn_modifier["Socket_46"] = bl_domain
                    gn_modifier["Socket_49"] = bl_fluid_surface
                except:
                    pass

            if "whitewater" in bl_object.name:
                gn_modifier = helper_operators.add_geometry_node_modifier(bl_object, resource_filepath, "FF_USDImportParticles")
                gn_modifier.show_expanded = False

                gn_modifier = helper_operators.add_geometry_node_modifier(bl_object, resource_filepath, "FF_GeometryNodesUSDWhitewater")
                try:
                    gn_modifier["Socket_46"] = bl_domain
                    gn_modifier["Socket_49"] = bl_fluid_surface
                except:
                    pass

        """
        print("FLIP Fluids Alembic Import: <" + self.filepath + ">")

        bpy.ops.wm.alembic_import(filepath=self.filepath, always_add_cache_reader=True)

        bl_domain = self.find_flip_fluids_mesh(bpy.context.selected_objects, "FLIP_Domain")
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

        if bl_domain is not None:
            bl_domain.hide_render = True
            bl_domain.display_type = 'BOUNDS'
            self.toggle_cycles_ray_visibility(bl_domain, False)

        if bl_fluid_surface is not None:
            self.add_smooth_modifier(bl_fluid_surface)
            helper_operators.add_geometry_node_modifier(bl_fluid_surface, resource_filepath, "FF_AlembicImportSurface")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_fluid_surface, resource_filepath, "FF_GeometryNodesAlembicSurface")
            self.apply_default_modifier_settings(bl_fluid_surface, bl_domain, bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found fluid surface cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Surface")
        
        if bl_fluid_particles is not None:
            helper_operators.add_geometry_node_modifier(bl_fluid_particles, resource_filepath, "FF_AlembicImportFluidParticles")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_fluid_particles, resource_filepath, "FF_GeometryNodesAlembicParticles")
            self.apply_default_modifier_settings(bl_fluid_particles, bl_domain, bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found fluid particle cache... Initialized geometry nodes")
            found_mesh_cache_list.append("FluidParticles")
        
        if bl_whitewater_foam is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_foam, resource_filepath, "FF_AlembicImportWhitewaterFoam")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_foam, resource_filepath, "FF_GeometryNodesAlembicParticles")
            self.apply_default_modifier_settings(bl_whitewater_foam, bl_domain, bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found whitewater foam cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Foam")
        
        if bl_whitewater_bubble is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_bubble, resource_filepath, "FF_AlembicImportWhitewaterBubble")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_bubble, resource_filepath, "FF_GeometryNodesAlembicParticles")
            self.apply_default_modifier_settings(bl_whitewater_bubble, bl_domain, bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found whitewater bubble cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Bubble")
        
        if bl_whitewater_spray is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_spray, resource_filepath, "FF_AlembicImportWhitewaterSpray")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_spray, resource_filepath, "FF_GeometryNodesAlembicParticles")
            self.apply_default_modifier_settings(bl_whitewater_spray, bl_domain, bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found whitewater spray cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Spray")
        
        if bl_whitewater_dust is not None:
            helper_operators.add_geometry_node_modifier(bl_whitewater_dust, resource_filepath, "FF_AlembicImportWhitewaterDust")
            gn_modifier = helper_operators.add_geometry_node_modifier(bl_whitewater_dust, resource_filepath, "FF_GeometryNodesAlembicParticles")
            self.apply_default_modifier_settings(bl_whitewater_dust, bl_domain, bl_fluid_surface, gn_modifier)
            self.report({'INFO'}, "Found whitewater dust cache... Initialized geometry nodes")
            found_mesh_cache_list.append("Dust")

        if found_mesh_cache_list:
            found_mesh_cache_string = "/".join(found_mesh_cache_list)
            self.report({'INFO'}, "Found and initialized " + found_mesh_cache_string + " objects and geometry nodes.")
        else:
            self.report({'WARNING'}, "No valid FLIP Fluids addon meshes found. Is this Alembic file a FLIP Fluids addon export?")
        """

        return {'FINISHED'}


class FLIPFluidsUSDExporter(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "flip_fluid_operators.flip_fluids_usd_exporter"
    bl_label = "Export FF USD"
    bl_options = {'PRESET', 'UNDO'}
    bl_description = ("Prepare a FLIP Fluids simulation for Universal Scene Description (USD) export." + 
                      " USD is the recommended format for export as USD supports more features and full FLIP Fluids export compatibility." + 
                      " After the file dialog, this exporter will" + 
                      " launch a new command line window and start exporting the simulation to the" +
                      " USD (.usdc) format. This Blend file will need to be saved before accessing"
                      " this operator")

    filename_ext = ".usdc"
    filter_glob: bpy.props.StringProperty(default="*.usdc", options={'HIDDEN'})


    @classmethod
    def poll(cls, context):
        return context.scene.flip_fluid.get_domain_object() is not None and bool(bpy.data.filepath)


    def check_cache_exists(self, context):
        dprops = context.scene.flip_fluid.get_domain_properties()
        cache_directory = dprops.cache.get_cache_abspath()
        bakefiles_directory = os.path.join(cache_directory, "bakefiles")

        file_count = 0
        cache_exists = False
        if os.path.isdir(bakefiles_directory):
            cache_exists = True
            file_count = len(os.listdir(bakefiles_directory))

        if not cache_exists or file_count == 0:
            return False
        return True


    def draw(self, context):
        hprops = context.scene.flip_fluid_helper

        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        header, body = self.layout.panel("usd_scene", default_closed=False)
        header.label(text="Scene")
        if body:
            column = body.column(align=True)
            column.prop(hprops, "usd_frame_range_mode", text="Frame Range")

            if hprops.usd_frame_range_mode == 'FRAME_RANGE_TIMELINE':
                column.prop(context.scene, "frame_start")
                column.prop(context.scene, "frame_end")
            else:
                column.prop(hprops.usd_frame_range_custom, "value_min")
                column.prop(hprops.usd_frame_range_custom, "value_max")


        header, body = self.layout.panel("usd_include", default_closed=False)
        header.label(text="Include")
        if body:
            column = body.column(heading="Mesh", align=True)
            column.prop(hprops, "usd_export_surface")
            column.prop(hprops, "usd_export_fluid_particles")
            column.prop(hprops, "usd_export_foam")
            column.prop(hprops, "usd_export_bubble")
            column.prop(hprops, "usd_export_spray")
            column.prop(hprops, "usd_export_dust")

            column = body.column(heading="Attributes", align=True)
            column.prop(hprops, "usd_export_velocity")
            column.prop(hprops, "usd_export_speed")
            column.prop(hprops, "usd_export_vorticity")
            column.prop(hprops, "usd_export_color")
            column.prop(hprops, "usd_export_age")
            column.prop(hprops, "usd_export_lifetime")
            column.prop(hprops, "usd_export_whitewater_proximity")
            column.prop(hprops, "usd_export_viscosity")
            column.prop(hprops, "usd_export_density")
            column.prop(hprops, "usd_export_id")
            column.prop(hprops, "usd_export_uid")
            column.prop(hprops, "usd_export_source_id")

            header, body = self.layout.panel("usd_command", default_closed=True)
            header.label(text="Command")
            if body:
                hprops = context.scene.flip_fluid_helper
                column = body.column(heading="Command", align=True)
                column.operator("flip_fluid_operators.helper_cmd_usd_export_to_clipboard", text="Copy Command to Clipboard", icon='COPYDOWN')


    def execute(self, context):
        if not self.check_cache_exists(context):
            dprops = context.scene.flip_fluid.get_domain_properties()
            cache_directory = dprops.cache.get_cache_abspath()
            self.report({'ERROR'}, "No data in simulation cache. Nothing to export in <" + cache_directory + ">")
            return {'CANCELLED'}

        print("FLIP Fluids Universal Scene Description (USD) Export: <" + self.filepath + ">")

        hprops = context.scene.flip_fluid_helper
        hprops.usd_output_filepath = self.filepath
        bpy.ops.flip_fluid_operators.helper_command_line_usd_export('INVOKE_DEFAULT')

        return {'FINISHED'}



def menu_func_import(self, context):
    self.layout.operator(FLIPFluidsUSDImporter.bl_idname, text="FLIP Fluids Universal Scene Description (.usd*)")


def menu_func_export(self, context):
    self.layout.operator(FLIPFluidsUSDExporter.bl_idname, text="FLIP Fluids Universal Scene Description (.usd*)")


def register():
    bpy.utils.register_class(FLIPFluidsUSDImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.utils.register_class(FLIPFluidsUSDExporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(FLIPFluidsUSDImporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.unregister_class(FLIPFluidsUSDExporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
