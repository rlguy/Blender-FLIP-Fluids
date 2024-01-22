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

import os

from ..pyfluid import (
        mixbox,
        )


def mixbox_lerp_srgb32f(r1, g1, b1, r2, g2, b2, t):
    if not mixbox.is_initialized():
        __initialize_mixbox()
    return mixbox.lerp_srgb32f(r1, g1, b1, r2, g2, b2, t)


def __initialize_mixbox():
    module_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    lut_filepath = os.path.join(module_dir, "third_party", "mixbox", "mixbox_lut_data.bin")
    with open(lut_filepath, 'rb') as f:
        lut_data = f.read()
        lut_data_bytes = len(lut_data)
        mixbox.initialize(lut_data, lut_data_bytes)
