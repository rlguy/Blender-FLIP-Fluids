# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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

from . import domain_simulation_ui
from . import domain_cache_ui
from . import domain_display_ui
from . import domain_particles_ui
from . import domain_surface_ui
from . import domain_whitewater_ui
from . import domain_world_ui
from . import domain_materials_ui
from . import domain_advanced_ui
from . import domain_debug_ui
from . import domain_stats_ui


class FLIPFLUID_PT_DomainTypeTabbedPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Domain"

    @classmethod
    def poll(cls, context):
        if not vcu.get_addon_preferences(context).enable_tabbed_domain_settings_view:
            return False
        obj_props = vcu.get_active_object(context).flip_fluid
        is_addon_disabled = context.scene.flip_fluid.is_addon_disabled_in_blend_file()
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN" and not is_addon_disabled

    def draw(self, context):
        obj = vcu.get_active_object(context)
        obj_props = vcu.get_active_object(context).flip_fluid

        dprops = context.scene.flip_fluid.get_domain_properties()
        if dprops is None:
            return
        is_simulation_running = dprops.bake.is_simulation_running

        column = self.layout.column()
        column.enabled = not is_simulation_running
        column.prop(obj_props, "object_type")
        column.separator()

        column = self.layout.column(align=True)
        row = column.row(align=True)
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_SIMULATION')
        row = column.row(align=True)
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_CACHE')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_DISPLAY')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_SURFACE')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_PARTICLES')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_WHITEWATER')
        row = column.row(align=True)
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_WORLD')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_MATERIALS')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_ADVANCED')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_DEBUG')
        row.prop_enum(dprops, "domain_settings_tabbed_panel_view", 'DOMAIN_SETTINGS_PANEL_STATS')
        column.separator()

        selected_panel = dprops.domain_settings_tabbed_panel_view
        if   selected_panel == 'DOMAIN_SETTINGS_PANEL_SIMULATION':
            column.label(text="FLIP Fluid Simulation")
            domain_simulation_ui.DRAW_OBJECT_FLIP_TYPE_PROPERTY = False
            try:
                domain_simulation_ui.FLIPFLUID_PT_DomainTypePanel.draw(self, context)
            except Exception as e:
                domain_simulation_ui.DRAW_OBJECT_FLIP_TYPE_PROPERTY = True
                raise Exception(e)
            domain_simulation_ui.DRAW_OBJECT_FLIP_TYPE_PROPERTY = True
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_CACHE':
            column.label(text="FLIP Fluid Cache")
            domain_cache_ui.FLIPFLUID_PT_DomainTypeCachePanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_DISPLAY':
            column.label(text="FLIP Fluid Display Settings")
            domain_display_ui.FLIPFLUID_PT_DomainTypeDisplayPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_PARTICLES':
            column.label(text="FLIP Fluid Particles")
            domain_particles_ui.FLIPFLUID_PT_DomainTypeFluidParticlesPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_SURFACE':
            column.label(text="FLIP Fluid Surface")
            domain_surface_ui.FLIPFLUID_PT_DomainTypeFluidSurfacePanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_WHITEWATER':
            column.label(text="FLIP Fluid Whitewater")
            domain_whitewater_ui.FLIPFLUID_PT_DomainTypeWhitewaterPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_WORLD':
            column.label(text="FLIP Fluid World")
            domain_world_ui.FLIPFLUID_PT_DomainTypeFluidWorldPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_MATERIALS':
            column.label(text="FLIP Fluid Materials")
            domain_materials_ui.FLIPFLUID_PT_DomainTypeMaterialsPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_ADVANCED':
            column.label(text="FLIP Fluid Advanced Settings")
            domain_advanced_ui.FLIPFLUID_PT_DomainTypeAdvancedPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_DEBUG':
            column.label(text="FLIP Fluid Debug")
            domain_debug_ui.FLIPFLUID_PT_DomainTypeDebugPanel.draw(self, context)
        elif selected_panel == 'DOMAIN_SETTINGS_PANEL_STATS':
            column.label(text="FLIP Fluid Stats")
            domain_stats_ui.FLIPFLUID_PT_DomainTypeStatsPanel.draw(self, context)


def register():
    bpy.utils.register_class(FLIPFLUID_PT_DomainTypeTabbedPanel)


def unregister():
    bpy.utils.unregister_class(FLIPFLUID_PT_DomainTypeTabbedPanel)
