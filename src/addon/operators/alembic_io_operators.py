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


    def apply_default_modifier_settings(self, target_object, domain_object, surface_object, gn_modifier):
        # Apply Simulation Time Scale and Apply Simulation Time Scale should be disabled.
        # These modifier features require a FLIP Domain and addon scripting to function. If enabled,
        # motion blur velocity will be set to (0.0, 0.0, 0.0)
        key_value_pairs_surface = [
            ("Input_6",  True),          # Enable Motion Blur
            ("Socket_8", False),         # Apply Simulation Time Scale - Disable: Requires FLIP Domain and addon scripting 
            ("Socket_9", False),         # Apply Simulation Time Scale - Disable: Requires FLIP Domain and addon scripting
            ("Socket_7", domain_object), # FLIP Domain Object
            ]

        key_value_pairs_particles = [
            ("Input_8",   True),           # Enable Motion Blur
            ("Socket_47", False),          # Apply Simulation Time Scale - Disable: Requires FLIP Domain and addon scripting
            ("Socket_48", False),          # Apply Simulation World Scale - Disable: Requires FLIP Domain and addon scripting
            ("Socket_46", domain_object),  # FLIP Domain Object
            ("Socket_49", surface_object), # FLIP Surface Object
            ]

        # Depending on FLIP Fluids version, the GN set up may not
        # have these inputs.

        gn_name = gn_modifier.name
        if gn_name.startswith("FF_GeometryNodesAlembicSurface"):
            for (key, value) in key_value_pairs_surface:
                try:
                    gn_modifier[key] = value
                except:
                    pass

        if gn_name.startswith("FF_GeometryNodesAlembicParticles"):
            for (key, value) in key_value_pairs_particles:
                try:
                    gn_modifier[key] = value
                except:
                    pass


    def add_smooth_modifier(self, target_object):
        smooth_mod = target_object.modifiers.new("FF_Smooth", "SMOOTH")
        smooth_mod.factor = 1.5
        smooth_mod.iterations = 0
        return smooth_mod


    def toggle_cycles_ray_visibility(self, obj, is_enabled):
        # Cycles may not be enabled in the user's preferences
        try:
            obj.visible_camera = is_enabled
            obj.visible_diffuse = is_enabled
            obj.visible_glossy = is_enabled
            obj.visible_transmission = is_enabled
            obj.visible_volume_scatter = is_enabled
            obj.visible_shadow = is_enabled
        except:
            pass


    def execute(self, context):
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


    def draw_alembic_export_engine_blender(self, context):
        hprops = context.scene.flip_fluid_helper
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        header, body = self.layout.panel("alembic_export_engine", default_closed=False)
        header.label(text="Alembic Exporter")
        if body:
            column = body.column(align=True)
            column.prop(hprops, "alembic_export_engine", text="Engine")

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
            hprops = context.scene.flip_fluid_helper
            column = body.column(heading="Command", align=True)
            column.operator("flip_fluid_operators.helper_cmd_alembic_export_to_clipboard", text="Copy Command to Clipboard", icon='COPYDOWN')


    def draw_alembic_export_engine_flip_fluids(self, context):
        hprops = context.scene.flip_fluid_helper
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        header, body = self.layout.panel("alembic_export_engine", default_closed=False)
        header.label(text="Alembic Exporter")
        if body:
            column = body.column(align=True)
            column.prop(hprops, "alembic_export_engine", text="Engine")

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
            column.prop(hprops, "alembic_global_scale", text="Scale (TODO)")

        header, body = self.layout.panel("alembic_include", default_closed=False)
        header.label(text="Include")
        if body:
            column = body.column(heading="Mesh", align=True)
            column.prop(hprops, "alembic_export_surface")
            column.prop(hprops, "alembic_export_surface_preview", text="Surface Preview (TODO)")
            column.prop(hprops, "alembic_export_fluid_particles", text="Fluid Particles (TODO)")
            column.prop(hprops, "alembic_export_foam", text="Foam (TODO)")
            column.prop(hprops, "alembic_export_bubble", text="Bubble (TODO)")
            column.prop(hprops, "alembic_export_spray", text="Spray (TODO)")
            column.prop(hprops, "alembic_export_dust", text="Dust (TODO)")

            column = body.column(heading="Attributes", align=True)
            column.prop(hprops, "alembic_export_velocity", text="Velocity (TODO)")
            column.prop(hprops, "alembic_export_color", text="Color (TODO)")

        header, body = self.layout.panel("alembic_command", default_closed=True)
        header.label(text="Command")
        if body:
            hprops = context.scene.flip_fluid_helper
            column = body.column(heading="Command", align=True)
            column.enabled = False
            column.operator("flip_fluid_operators.cmd_custom_alembic_export_to_clipboard", text="Copy Command to Clipboard (TODO)", icon='COPYDOWN')


    def draw(self, context):
        hprops = context.scene.flip_fluid_helper
        if hprops.alembic_export_engine == 'ALEMBIC_EXPORT_ENGINE_FLIP_FLUIDS':
            self.draw_alembic_export_engine_flip_fluids(context)
        elif hprops.alembic_export_engine == 'ALEMBIC_EXPORT_ENGINE_BLENDER':
            self.draw_alembic_export_engine_blender(context)


    def alembic_export_engine_flip_fluids(self):
        hprops = bpy.context.scene.flip_fluid_helper
        hprops.alembic_output_filepath = self.filepath
        bpy.ops.flip_fluid_operators.helper_cmd_custom_alembic_export('INVOKE_DEFAULT')


    def alembic_export_engine_blender(self):
        hprops = bpy.context.scene.flip_fluid_helper
        hprops.alembic_output_filepath = self.filepath
        bpy.ops.flip_fluid_operators.helper_command_line_alembic_export('INVOKE_DEFAULT')


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


    def execute(self, context):
        if not self.check_cache_exists(context):
            dprops = context.scene.flip_fluid.get_domain_properties()
            cache_directory = dprops.cache.get_cache_abspath()
            self.report({'ERROR'}, "No data in simulation cache. Nothing to export in <" + cache_directory + ">")
            return {'CANCELLED'}

        print("FLIP Fluids Alembic Export: <" + self.filepath + ">")

        hprops = context.scene.flip_fluid_helper
        if hprops.alembic_export_engine == 'ALEMBIC_EXPORT_ENGINE_FLIP_FLUIDS':
            self.alembic_export_engine_flip_fluids()
        elif hprops.alembic_export_engine == 'ALEMBIC_EXPORT_ENGINE_BLENDER':
            self.alembic_export_engine_blender()
        else:
            self.report({'WARNING'}, "Unknown Alembic Export Engine: " + hprops.alembic_export_engine)
            return {'CANCELLED'}

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
