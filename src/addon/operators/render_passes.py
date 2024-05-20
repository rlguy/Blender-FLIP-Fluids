# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Dennis Fassbaender
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
import os

# Define visibility settings and render settings for each setup
visibility_settings = {
    "fluid_only": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "fluid_particles": {"camera": False, "diffuse": False, "glossy": True, "transmission": True, "scatter": False, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_bubble": {"camera": False, "diffuse": False, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_dust": {"camera": False, "diffuse": False, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_foam": {"camera": False, "diffuse": False, "glossy": True, "transmission": True, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_spray": {"camera": False, "diffuse": False, "glossy": True, "transmission": True, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "world": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "film_transparent": True,
        "transparent_glass": False,
     },
     
    "fluidparticles_only": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "fluid_particles": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_bubble": {"camera": True, "diffuse": False, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_dust": {"camera": True, "diffuse": False, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_foam": {"camera": True, "diffuse": False, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_spray": {"camera": True, "diffuse": False, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "world": {"camera": False, "diffuse": True, "glossy": False, "transmission": True, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "film_transparent": True,
        "transparent_glass": True,
     },
 
    "bubblesanddust_only": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "fluid_particles": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_bubble": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_dust": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_foam": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_spray": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False},
        #"Ground": {"camera": False, "diffuse": False, "glossy": True, "transmission": True, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "world": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "film_transparent": True,
        "transparent_glass": True,
        "denoiser": True,
    },
    
    
     "foamandspray_only": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "fluid_particles": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_bubble": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_dust": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_foam": {"camera": True, "diffuse": True, "glossy": False, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_spray": {"camera": True, "diffuse": True, "glossy": False, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False},
        #"Ground": {"camera": False, "diffuse": False, "glossy": True, "transmission": True, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "world": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False, "is_shadow_catcher": True, "is_holdout": False},
        "film_transparent": True,
        "transparent_glass": True,
        "denoiser": True,
    },

    "reflr_only": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "fluid_particles": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_bubble": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_dust": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_foam": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "whitewater_spray": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": False, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "world": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": True},
        "film_transparent": True,
        "transparent_glass": True,
        # Combine with "color" or "vivid" as example
    },
    
    "objects_only": {
        #"fluid_surface_material": DefaultShader,
        "fluid_surface": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "fluid_particles": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_bubble": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_dust": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_foam": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_spray": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "world": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": False, "is_holdout": False},
        "film_transparent": True,
        "transparent_glass": True,
    },

    "fluid_shadows_only": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": True},
        "fluid_particles": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_bubble": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_dust": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_foam": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_spray": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": True, "is_holdout": False},
        "world": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": False},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "film_transparent": True,
        "transparent_glass": True,
    },
    
    "object_shadows_only": {
        #"fluid_surface_material": DefaultShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": False, "is_shadow_catcher": True, "is_holdout": False},
        "fluid_particles": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_bubble": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_dust": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_foam": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "whitewater_spray": {"camera": True, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": True, "is_holdout": False},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False, "is_shadow_catcher": True, "is_holdout": False},
        "world": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": True},
        "selected_objects": {"camera": False, "diffuse": True, "glossy": False, "transmission": False, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "film_transparent": True,
        "transparent_glass": True,
    },
    
    "reset": {
        #"fluid_surface_material": CompShader,
        "fluid_surface": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "fluid_particles": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_bubble": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_dust": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_foam": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "whitewater_spray": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "ff_camera_screen": {"camera": False, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": False},
        #"Ground": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "world": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True},
        "selected_objects": {"camera": True, "diffuse": True, "glossy": True, "transmission": True, "scatter": True, "shadow": True, "is_shadow_catcher": False, "is_holdout": False},
        "film_transparent": True,
        "transparent_glass": False,
    }
}

