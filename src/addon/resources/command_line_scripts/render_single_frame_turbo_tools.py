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

import bpy, sys, os, platform, subprocess

argv = sys.argv
argv = argv[argv.index("--") + 1:]
frameno = int(argv[0])
open_image_after = False
if argv[1] == "1":
    open_image_after = True

original_output_path = bpy.context.scene.render.filepath
image_path = bpy.context.scene.render.frame_path(frame=frameno)

bpy.context.scene.frame_set(frameno)
bpy.context.scene.render.filepath = image_path
bpy.ops.threedi.render_still(write_still=True)
bpy.context.scene.render.filepath = original_output_path

if open_image_after:
    print("Attempting to open image: <" + image_path + ">")
    system = platform.system()
    if system == "Windows":
        os.startfile(image_path)
    elif system == "Darwin":
        subprocess.call(["open", image_path])
    elif system == "Linux":
        subprocess.call(["xdg-open", image_path])
        pass