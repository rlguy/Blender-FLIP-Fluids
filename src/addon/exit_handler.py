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


import bpy, os, shutil

# These variables are used when running an exit handler where
# access to Blender data may no longer be available
IS_BLEND_FILE_SAVED = False
CACHE_DIRECTORY = ""

def on_exit():
    # nothing currently to do on exit
    pass


def save_post():
    global IS_BLEND_FILE_SAVED
    IS_BLEND_FILE_SAVED = True


def load_post():
    global IS_BLEND_FILE_SAVED
    base = os.path.basename(bpy.data.filepath)
    save_file = os.path.splitext(base)[0]
    is_unsaved = not base or not save_file
    IS_BLEND_FILE_SAVED = not is_unsaved


def set_cache_directory(dirpath):
    global CACHE_DIRECTORY
    CACHE_DIRECTORY = dirpath