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

import bpy, os, json, time, aud

from . import version_compatibility_utils as vcu


def get_sounds_directory():
    return os.path.join(vcu.get_addon_directory(), "resources", "sounds")


def play_sound(json_audio_filepath, block=False):
    with open(json_audio_filepath, 'r', encoding='utf-8') as f:
        json_data = json.loads(f.read())

    audio_length = float(json_data["length"])
    audio_filename = json_data["filename"]
    audio_filepath = os.path.join(os.path.dirname(json_audio_filepath), audio_filename)
    
    device = aud.Device()
    sound = aud.Sound(audio_filepath)
    handle = device.play(sound)

    if block:
        time.sleep(audio_length)
        handle.stop()