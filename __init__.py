# Blender FLIP Fluids Add-on
# Copyright (C) 2021 Ryan L. Guy
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

"""
This addon __init__.py file is not the actual FLIP Fluids addon. The purpose of this
file is to inform the user that what they have installed is not an installation file
and is not the correct way to install the FLIP Fluids addon.
"""

bl_info = {
    "name" : "FLIP Fluids - This is not an installation file",
    "description": "The file you have installed is not an addon. Enable for more info.",
    "author" : "The FLIP Fluids Development Team",
    "version" : (0, 0, 0),
    "blender" : (2, 81, 0),
    "location" : "",
    "warning" : "",
    "wiki_url" : "https://github.com/rlguy/Blender-FLIP-Fluids",
    "tracker_url" : "",
    "category" : ""
}

import bpy


class FLIPFluidInfoAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__.split(".")[0]

    def draw(self, context):
        column = self.layout.column(align=True)
        column.label(text="The file you have installed is not an addon.")
        column.label(text="This .zip file only contains the addon and simulation engine source code.")
        column.label(text="")
        column.label(text="The source code must be built and compiled for your system.")
        column.label(text="See the FLIP Fluids GitHub README for instructions.")
        column.operator(
                "wm.url_open", 
                text="FLIP Fluids addon GitHub", 
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids"
        column.separator()
        column.operator(
                "wm.url_open", 
                text="Try our FLIP Fluids Free Trial", 
            ).url = "https://github.com/rlguy/Blender-FLIP-Fluids/wiki/FLIP-Fluids-Demo-Addon"
        column.operator(
                "wm.url_open", 
                text="Purchase the FLIP Fluids addon on the Blender Market", 
            ).url = "https://blendermarket.com/products/flipfluids"


def register():
    bpy.utils.register_class(FLIPFluidInfoAddonPreferences)


def unregister():
    bpy.utils.unregister_class(FLIPFluidInfoAddonPreferences)

