# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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

from ..utils import version_compatibility_utils as vcu


class FLIPFLUID_PT_ObstacleTypePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid"


    @classmethod
    def poll(cls, context):
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_OBSTACLE" and not is_addon_disabled


    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = obj.flip_fluid
        obstacle_props = obj_props.obstacle
        preferences = vcu.get_addon_preferences(context)
        show_documentation = vcu.get_addon_preferences(context).show_documentation_in_ui

        column = self.layout.column()
        column.prop(obj_props, "object_type")

        if show_documentation:
            column = self.layout.column(align=True)
            column.operator(
                "wm.url_open", 
                text="Obstacle Object Documentation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Obstacle-Object-Settings"
            column.operator(
                "wm.url_open", 
                text="Obstacle objects must have manifold/watertight geometry", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Manifold-Meshes"
            column.operator(
                "wm.url_open", 
                text="Thin obstacles are leaking fluid", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#thin-obstacles-leaking-fluid"
            column.operator(
                "wm.url_open", 
                text="Animated obstacle is static in the simulation", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#animated-obstacle-is-static-when-running-the-simulation"
            column.operator(
                "wm.url_open", 
                text="How to debug issues with obstacle objects", 
                icon="WORLD"
            ).url = "https://blendermarket.com/posts/flip-fluids-10-tips-to-improve-your-blender-workflow"
            column.operator(
                "wm.url_open", 
                text="Mesh banding against curved obstacles", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Scene-Troubleshooting#mesh-banding-artifacts-against-curved-obstacles"
            column.operator(
                "wm.url_open", 
                text="Using the Inverse option to perfectly contain fluid", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Obstacle-Inverse-Workflow"
            column.operator(
                "wm.url_open", 
                text="Liquid volume loss with animated obstacle", 
                icon="WORLD"
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Limitations-of-the-FLIP-Fluids-addon#volume-and-mass-preservation"




        column = self.layout.column()
        column.prop(obstacle_props, "is_enabled")

        column = self.layout.column()
        column.prop(obstacle_props, "is_inversed")

        box = self.layout.box()
        box.label(text="Obstacle Properties")

        column = box.column()
        column.prop(obstacle_props, "friction", slider=True)

        column = box.column()
        column.prop(obstacle_props, "velocity_scale")

        column = box.column()
        column.prop(obstacle_props, "whitewater_influence")

        column = box.column()
        column.prop(obstacle_props, "dust_emission_strength")

        column = box.column()
        column.prop(obstacle_props, "sheeting_strength")

        column = box.column()
        alert_threshold = 0.05 + 1e-5
        if abs(obstacle_props.mesh_expansion) > alert_threshold:
            column.alert = True
        column.prop(obstacle_props, "mesh_expansion")

        box = self.layout.box()
        box.label(text="Mesh Data Export:")
        column = box.column(align=True)
        
        row = column.row(align=True)
        row.alignment = 'LEFT'
        row.prop(obstacle_props, "export_animated_mesh")

        is_child_object = obj.parent is not None
        is_hint_enabled = not vcu.get_addon_preferences().dismiss_export_animated_mesh_parented_relation_hint
        if is_hint_enabled and not obstacle_props.export_animated_mesh and is_child_object:
            row.prop(context.scene.flip_fluid_helper, "export_animated_mesh_parent_tooltip", 
                    icon="QUESTION", emboss=False, text=""
                    )
            row.label(text="←Hint: export option may be required")

        column.prop(obstacle_props, "skip_reexport")
        column.separator()
        column = box.column(align=True)
        column.enabled = obstacle_props.skip_reexport
        column.prop(obstacle_props, "force_reexport_on_next_bake", toggle=True)

        column = self.layout.column(align=True)
        column.separator()
        column.operator("flip_fluid_operators.copy_setting_to_selected", icon='COPYDOWN')
    

def register():
    bpy.utils.register_class(FLIPFLUID_PT_ObstacleTypePanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_ObstacleTypePanel)
