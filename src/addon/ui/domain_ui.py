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

if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'domain_simulation_ui',
        'domain_cache_ui',
        'domain_display_ui',
        'domain_surface_ui',
        'domain_particles_ui',
        'domain_whitewater_ui',
        'domain_world_ui',
        'domain_presets_ui',
        'domain_materials_ui',
        'domain_advanced_ui',
        'domain_debug_ui',
        'domain_stats_ui',
        'domain_tabbed_ui',
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy

from . import(
        domain_simulation_ui,
        domain_cache_ui,
        domain_display_ui,
        domain_surface_ui,
        domain_particles_ui,
        domain_whitewater_ui,
        domain_world_ui,
        domain_presets_ui,
        domain_materials_ui,
        domain_advanced_ui,
        domain_debug_ui,
        domain_stats_ui,
        domain_tabbed_ui,
        )


def register():
    domain_simulation_ui.register()
    domain_cache_ui.register()
    domain_display_ui.register()
    domain_surface_ui.register()
    domain_particles_ui.register()
    domain_whitewater_ui.register()
    domain_world_ui.register()
    domain_presets_ui.register()
    domain_materials_ui.register()
    domain_advanced_ui.register()
    domain_debug_ui.register()
    domain_stats_ui.register()
    domain_tabbed_ui.register()


def unregister():
    domain_simulation_ui.unregister()
    domain_cache_ui.unregister()
    domain_display_ui.unregister()
    domain_surface_ui.unregister()
    domain_particles_ui.unregister()
    domain_whitewater_ui.unregister()
    domain_world_ui.unregister()
    domain_materials_ui.unregister()
    domain_presets_ui.unregister()
    domain_advanced_ui.unregister()
    domain_debug_ui.unregister()
    domain_stats_ui.unregister()
    domain_tabbed_ui.unregister()
