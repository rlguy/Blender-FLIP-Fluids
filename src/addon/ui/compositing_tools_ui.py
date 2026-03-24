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

from . import domain_simulation_ui
from ..utils import installation_utils


def draw_compositing_tools_panel(self, context):
        layout = self.layout
        if not installation_utils.is_installation_complete():
            return

        hprops = context.scene.flip_fluid_helper
        cprops = context.scene.flip_fluid_compositing_tools

        # Domain-Check
        domain_obj = context.scene.flip_fluid.get_domain_object()
        has_domain = domain_obj is not None

        # Finished initialize?
        initialize_all_conditions_met = False
        if domain_obj:
            initialize_all_conditions_met = (
                domain_obj.flip_fluid.domain.particles.enable_fluid_particle_velocity_vector_attribute and
                domain_obj.flip_fluid.domain.whitewater.enable_velocity_vector_attribute and
                domain_obj.flip_fluid.domain.surface.enable_velocity_vector_attribute and
                #domain_obj.flip_fluid.domain.surface.remove_mesh_near_domain and # Disabled testwise
                #context.scene.render.engine == 'CYCLES' and # Disabled testwise
                context.scene.render.film_transparent and
                domain_obj.flip_fluid.domain.whitewater.enable_id_attribute
            )

        # CameraScreen-Check
        camera_screen_exists = bpy.data.objects.get("ff_camera_screen") is not None

        box = self.layout.box()

        # 1. Missing Domain
        if not has_domain:
            row = box.row()
            row.label(text="Missing FLIP Fluids Domain", icon='ERROR')
            return

        # 2. Initialize not finished
        if not initialize_all_conditions_met:
            row = box.row()
            row.label(text="Compositing setup is incomplete", icon='ERROR')

            # Initialize All Button
            row = box.row(align=True)
            row.operator(
                "flip_fluid_operators.helper_initialize_compositing", 
                text="Initialize All", 
                icon='SETTINGS'
            )
            return

        # 3. Missing CameraScreen
        if not camera_screen_exists:
            # Hinweis und Add Camera Screen Button im aufgeklappten Zustand
            row = box.row()
            row.label(text="Add CameraScreen to continue", icon='INFO')

            # Add Camera Screen Button
            row = box.row(align=True)
            row.operator("flip_fluid_operators.add_camera_screen", text="Add CameraScreen", icon='IMAGE_BACKGROUND')
            return

        # 4. Everything was setup. Continue:

        row = box.row(align=True)
        row.active = cprops.render_passes and cprops.render_passes_is_any_pass_enabled and not cprops.render_passes_stillimagemode_toggle
        row.operator("flip_fluid_operators.helper_command_line_render", text="Launch Render Passes").use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')

        # Render Passes Checkbox
        row = box.row(align=True)
        row.prop(cprops, "render_passes")

        row = box.row()
        row.alignment = 'LEFT'
        row.prop(context.scene.render, "film_transparent", text="Film Transparency")

        # Checkboxes for render passes with aligned width
        def add_fixed_width_prop(row, prop_name, enabled):
            box = row.box()
            col = box.column()
            col.scale_x = 1.5
            col.enabled = enabled  # Deaktiviert Checkbox wenn nicht verfügbar
            col.prop(cprops, prop_name)

        def add_fixed_width_placeholder(row):
            box = row.box()
            col = box.column()
            col.scale_x = 1.5
            col.label(text="")

        # ---------------------------------
        # Aktivitätsbedingungen ermitteln
        # ---------------------------------

        # 1) Fluid Surface
        has_fluid_surface = ("fluid_surface" in bpy.data.objects)

        # 2) Objekte ohne Flag (ungetagged)
        has_unflagged_objects = cprops.render_passes_has_unflagged_objects

        # 3) Elements
        has_elements = any(
            item.fg_elements or item.bg_elements or item.ref_elements
            for item in cprops.render_passes_objectlist
        )

        # 4) Fluid Particles/Whitewater -> gezielt Domain-Objekt abfragen
        has_fluid_particles = False
        has_whitewater = False
        if domain_obj is not None:
            has_fluid_particles = domain_obj.flip_fluid.domain.particles.enable_fluid_particle_output
            has_whitewater = domain_obj.flip_fluid.domain.whitewater.enable_whitewater_simulation

        # ---------------------------------
        # First row of checkboxes
        # ---------------------------------
        column = box.column(align=True)
        row1 = column.row(align=True)

        add_fixed_width_prop(row1, "render_passes_fluid_only", has_fluid_surface)
        add_fixed_width_prop(row1, "render_passes_objects_only", has_unflagged_objects)
        add_fixed_width_prop(row1, "render_passes_elements_only", has_elements)

        # ---------------------------------
        # Second row of checkboxes
        # ---------------------------------
        # row2 = column.row(align=True)
        # add_fixed_width_prop(row2, "render_passes_fluid_shadows_only", is_render_passes_active)
        # add_fixed_width_prop(row2, "render_passes_reflr_only", has_fluid_surface)
        # add_fixed_width_placeholder(row2)
        # DISABLED REFLECTIONS - NEED TO FIND A BETTER WORKFLOW

        # ---------------------------------
        # Third row of checkboxes
        # ---------------------------------
        row3 = column.row(align=True)
        add_fixed_width_prop(row3, "render_passes_fluidparticles_only", has_fluid_particles)
        add_fixed_width_prop(row3, "render_passes_foamandspray_only", has_whitewater)
        add_fixed_width_prop(row3, "render_passes_bubblesanddust_only", has_whitewater)

        box.separator()

        # Add separator and group elements for Camera, Alignment, and Background Image Settings
        settings_box = box.box()

        # Group Alignment and Camera Screen Settings
        camera_screen_exists = bpy.data.objects.get("ff_camera_screen") is not None
        alignment_grid_exists = bpy.data.objects.get("ff_alignment_grid") is not None
        
        row = settings_box.row(align=True)

        row1 = row.row()
        row1.enabled = camera_screen_exists
        row1.prop(cprops, "render_passes_camerascreen_visibility", text="Show CameraScreen")

        row2 = row.row()
        row2.enabled = alignment_grid_exists
        row2.prop(cprops, "render_passes_alignmentgrid_visibility", text="Show Alignment Grid")

        # Show Background Image checkbox and Opacity slider
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            row = settings_box.row(align=True)
            row.prop(camera.data, "show_background_images", text="Show Background Image")

            if not camera.data.background_images:
                bg_image = camera.data.background_images.new()
            else:
                bg_image = camera.data.background_images[0]

            if bg_image and bg_image.image:
                row.prop(bg_image, "alpha", text="Opacity")

        # Camera screen settings in compact layout
        column = settings_box.column(align=True)

        # First row for camera selection and camera screen distance
        row = column.row(align=True)
        row.prop(cprops, 'render_passes_cameraselection', text="")
        row.operator("flip_fluid_operators.add_camera_screen", text="CameraScreen", icon='IMAGE_BACKGROUND')
        row.prop(cprops, 'render_passes_camerascreen_distance', text="")

        # Second row for still image mode toggle
        row = column.row(align=True)
        row.prop(cprops, 'render_passes_stillimagemode_toggle', text="Still Image Mode", toggle=True, icon='IMAGE_DATA')

        # View Transform settings
        row = box.row(align=True)
        row.prop(context.scene.view_settings, "view_transform", text="View Transform")

        # Objects to render list
        row = box.row()
        row.label(text="Objects to render (no fluid objects):")
        row = box.row()
        row.template_list("FLIPFLUID_UL_passes_items", "", cprops, "render_passes_objectlist", cprops, "render_passes_objectlist_index")

        col = row.column(align=True)
        col.operator("flip_fluid_operators.add_item_to_list", icon='ADD', text="")
        col.operator("flip_fluid_operators.remove_item_from_list", icon='REMOVE', text="").index = cprops.render_passes_objectlist_index

        box.separator()


        column = box.column(align=True)

        # Import Media Button:
        row = column.row(align=True)
        row.enabled = cprops.render_passes_stillimagemode_toggle
        row.operator("flip_fluid.passes_import_media", text="Import Images as Elements", icon='FILE_IMAGE')

        # Foreground and Background Buttons:
        row = column.row(align=True)
        row.operator("flip_fluid_operators.quick_foregroundcatcher", text="FG Element", icon='IMAGE_REFERENCE')
        row.operator("flip_fluid_operators.quick_backgroundcatcher", text="BG Element", icon='IMAGE_BACKGROUND')
        row.operator("flip_fluid_operators.quick_reflectivecatcher", text="REF Element", icon='IMAGE_BACKGROUND')

        # Ground and Alignment Grid Buttons:
        row = column.row(align=True)
        row.operator("flip_fluid_operators.quick_ground", text="Ground Object", icon='ALIGN_BOTTOM')
        row.operator("flip_fluid_operators.duplicate_item_in_list", text="Duplicate Object", icon='DUPLICATE')
        row.operator("flip_fluid_operators.add_alignment_grid", text="Alignment Grid", icon='GRID')

        box.separator()

        # Fader area
        fader_box = box.box()
        fader_box.label(text="Fading Settings:")

        # Row for the "Show Faders" and "Blend Testcolor" checkboxes
        row_1 = fader_box.row(align=True)
        row_1.prop(cprops, "render_passes_faderobjects_visibility", text="Show Faders")
        row_1.prop(cprops, "render_passes_faderobjectnames_visibility", text="Fader Names")
        row_1.prop(cprops, "render_passes_objectnames_visibility", text="Object Names")

        # Row for the other three checkboxes
        row_2 = fader_box.row(align=True)
        row_2.prop(cprops, "render_passes_toggle_fader_fluidsurface", text="Fader")
        row_2.prop(cprops, "render_passes_toggle_speed_fluidsurface", text="Speed")
        row_2.prop(cprops, "render_passes_toggle_domain_fluidsurface", text="Domain")

        # Buttons and Sliders in compact layout using column
        column = fader_box.column(align=True)

        # Row for Buttons
        row_3 = column.row(align=True)

        # Row for Buttons (Velocity / Invert)
        row_3 = column.row(align=True)
        velocity_button = row_3.row(align=True)
        velocity_button.scale_x = 1.0
        velocity_button.enabled = cprops.render_passes_toggle_speed_fluidsurface == 1
        velocity_button.prop(cprops, "render_passes_toggle_velocity_fluidsurface", text="Velocity", icon='MOD_WAVE')

        invert_button = row_3.row(align=True)
        invert_button.scale_x = 1.0
        invert_button.enabled = cprops.render_passes_toggle_velocity_fluidsurface == 1
        invert_button.prop(cprops, "render_passes_toggle_velocity_invert", text="Invert", icon='ARROW_LEFTRIGHT')

        # Row for Sliders (Fade Footage / Footage / Normal)
        row_4 = column.row(align=True)
        row_4.prop(cprops, "render_passes_toggle_projectionfader", text="Fade Footage", icon='IMAGE_ALPHA')
        row_4.prop(cprops, "render_passes_blend_footage_to_fluidsurface", text="Footage")
        row_4.prop(cprops, "render_passes_blend_normalmap_to_fluidsurface", text="Normal")

        # Row for "Find Fluid" and "Find Reflections"
        row_find = column.row(align=True)
        row_find.prop(cprops, "render_passes_toggle_projectiontester", text="Find Fluid", icon='ZOOM_SELECTED')
        # row_find.prop(cprops, "render_passes_toggle_findreflections", text="Find Reflections", icon='ZOOM_SELECTED')
        # DISABLED TILL I FOUND A BETTER WORKFLOW FOR RENDERING


        # Collapsible Fader Panel (ColorRamps)
        def draw_fader_details(parent_layout, context):
            """Draws a collapsible section for ColorRamp settings and Fading controls within the Fading area."""
            hprops = context.scene.flip_fluid_helper
            cprops = context.scene.flip_fluid_compositing_tools

            # Collapsible Panel
            header, body_render_passes_show_fader_details = parent_layout.panel("render_passes_show_fader_details", default_closed=True)
            header.label(text="Advanced Fader Settings")

            # If the section is collapsed, don't draw the details
            if not body_render_passes_show_fader_details:
                return

            # Add ColorRamp nodes directly within the Fader Panel
            parent_layout.label(text="fluid_surface Fading Controls", icon='NODE_MATERIAL')

            material_name = "FF ClearWater_Passes"
            node_names = [
                "ff_fader_colorramp",
                "ff_objects_colorramp",
                "ff_speed_colorramp",
                "ff_domain_colorramp",
                "ff_footage_colorramp"
            ]

            mat = bpy.data.materials.get(material_name)
            if not mat:
                parent_layout.label(text=f"Material '{material_name}' not found.", icon='ERROR')
            elif not mat.use_nodes or not mat.node_tree:
                parent_layout.label(text="Material has no node setup.", icon='ERROR')
            else:
                node_tree = mat.node_tree
                # Loop through relevant ColorRamp nodes
                for node_name in node_names:
                    node = node_tree.nodes.get(node_name)
                    if node and node.type == 'VALTORGB':
                        # Draw each ColorRamp in the existing layout
                        row = parent_layout.row(align=True)
                        row.label(text=node_name)
                        row.template_color_ramp(node, "color_ramp", expand=False)
                    else:
                        parent_layout.label(text=f"'{node_name}' not found or not a ColorRamp.", icon='INFO')

            # Row for Object-Based Fading Width on fluid_surface
            row = parent_layout.row(align=True)
            row.prop(cprops, "render_passes_object_fading_width_fluid_surface", slider=True, text="Object Fading Width (fluid_surface)")

            # Row for Object-Based Fading Softness on fluid_surface
            row = parent_layout.row(align=True)
            row.prop(cprops, "render_passes_object_fading_softness_fluid_surface", slider=True, text="Object Fading Softness (fluid_surface)")

            # Add Sliders for GeometryNode Modifiers
            parent_layout.separator()
            parent_layout.label(text="Particle Fading Controls", icon='MODIFIER')

            # Row for Object-Based Fading Width
            row = parent_layout.row(align=True)
            row.prop(cprops, "render_passes_object_fading_width", slider=True, text="Object Fading Width (Particles)")

            # Row for Object-Based Fading Softness
            row = parent_layout.row(align=True)
            row.prop(cprops, "render_passes_object_fading_softness", slider=True, text="Object Fading Softness (Particles)")

            # Row for General Fading Width
            row = parent_layout.row(align=True)
            row.prop(cprops, "render_passes_general_fading_width", slider=True, text="General Fading Width")


        # Draw the collapsible Fader Details section directly in the Fader Panel
        draw_fader_details(fader_box, context)

        box.separator()

        # Reset and Apply buttons in compact layout
        column = box.column(align=True)

        if context.scene.flip_fluid.is_domain_object_set():
            row = column.row(align=True)
            
            # Select Domain Button
            row.operator("flip_fluid_operators.helper_select_domain", text="Select Domain Object", icon="MESH_GRID")

            # Unsaved File Warning
            is_saved = bool(bpy.data.filepath)
            if not is_saved:
                row.prop(hprops, "unsaved_blend_file_tooltip", icon="ERROR", emboss=False, text="")
                row.alert = True
                row.label(text="Unsaved File")
                row.operator("flip_fluid_operators.helper_save_blend_file", icon='FILE_TICK', text="Save")
                row.alert = False  # Reset alert state

            # Resolution Setting
            dprops = context.scene.flip_fluid.get_domain_properties()
            resolution_text = "Resolution"
            if dprops.simulation.lock_cell_size:
                resolution_text += " (voxel size locked)"

            row.enabled = not dprops.simulation.lock_cell_size and not dprops.bake.is_simulation_running
            row.prop(dprops.simulation, "resolution", text=resolution_text)

            # Bake Operator UI Element
            domain_simulation_ui.draw_bake_operator_UI_element(context, column)

        column.separator()

        # Row for Reset settings (separate row)
        row = column.row(align=True)
        row.operator("flip_fluid_operators.reset_passes_settings", text="Set Visibility Options", icon='HIDE_OFF')

        # Row for Apply Materials and Refresh/Fix All (in the same row)
        row = column.row(align=True)
        row.operator("flip_fluid_operators.apply_all_materials", text="Apply All Materials", icon='MATERIAL')
        row.operator("flip_fluid_operators.helper_fix_compositingtextures", text="Refresh / Fix All", icon='FILE_REFRESH')

        # Render Passes Launch buttons (separate row)
        row = column.row(align=True)
        row.active = cprops.render_passes and cprops.render_passes_is_any_pass_enabled and not cprops.render_passes_stillimagemode_toggle
        row.operator("flip_fluid_operators.helper_command_line_render", text="Launch Render Passes").use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_command_line_render_to_clipboard", text="", icon='COPYDOWN').use_turbo_tools = False
        row.operator("flip_fluid_operators.helper_open_render_output_folder", text="", icon='FILE_FOLDER')

        #maybe later:
        #row = column.row(align=True)
        #row.operator("flip_fluid_operators.create_resolve_project", text="Export Video Editor File", icon='FILE_MOVIE')