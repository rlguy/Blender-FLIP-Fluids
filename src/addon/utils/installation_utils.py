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

import bpy, os

IS_INSTALLATION_UTILS_INITIALIZED = False
IS_INSTALLATION_COMPLETE = False

def is_installation_complete():
    global IS_INSTALLATION_UTILS_INITIALIZED
    global IS_INSTALLATION_COMPLETE

    if IS_INSTALLATION_UTILS_INITIALIZED:
        return IS_INSTALLATION_COMPLETE

    script_dir = os.path.dirname(os.path.realpath(__file__))
    addon_dir = os.path.dirname(script_dir)
    install_file = os.path.join(addon_dir, "resources", "installation_data", "installation_complete")

    if os.path.exists(install_file):
        IS_INSTALLATION_COMPLETE = True
    else:
        IS_INSTALLATION_COMPLETE = False

    IS_INSTALLATION_UTILS_INITIALIZED = True

    return IS_INSTALLATION_COMPLETE


def complete_installation():
    global IS_INSTALLATION_UTILS_INITIALIZED
    global IS_INSTALLATION_COMPLETE

    script_dir = os.path.dirname(os.path.realpath(__file__))
    addon_dir = os.path.dirname(script_dir)
    install_file = os.path.join(addon_dir, "resources", "installation_data", "installation_complete")

    if not os.path.exists(install_file):
        with open(install_file, 'w') as f:
            f.write("1")

    IS_INSTALLATION_COMPLETE = True
    IS_INSTALLATION_UTILS_INITIALIZED = True
