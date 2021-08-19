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

import hashlib


def string_to_cache_slug(string):
    max_hash_len = 16
    max_string_len = 64 - max_hash_len
    whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

    h = hashlib.md5()
    h.update(bytes(string, 'utf-8'))
    hexstr = h.hexdigest()
    hexstr = hexstr[:max_hash_len]

    slug = string[:max_string_len]
    slug = ''.join(c if c in whitelist else '-' for c in slug)
    slug += hexstr

    return slug
