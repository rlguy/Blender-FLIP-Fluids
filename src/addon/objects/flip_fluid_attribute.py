# Blender FLIP Fluids Add-on
# Copyright (C) 2026 Ryan L. Guy & Dennis Fassbaender
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

import bpy, random, os, re, enum, traceback
import numpy as np

from ..utils import cache_utils
from ..types import DataType, MeshType


_RUNTIME_CACHE = {}
_DEFAULT_UVW = np.array([0.0, 0.0, 0.0], dtype=np.float32)


def get_new_id():
    global _RUNTIME_CACHE
    new_id = random.randint(0, int(1e9))
    while new_id in _RUNTIME_CACHE:
        new_id = random.randint(0, int(1e9))
    return new_id


def reset():
    global _RUNTIME_CACHE
    _RUNTIME_CACHE = {}


def update_remap_uvw_name(self, context):
    def get_base_name(s):
        return re.sub(r"\d+$", "", s)

    def get_unique_name(base_name, name_list):
        def get_integer_suffix(s):
            match = re.search(r'\d+$', s)
            return int(match.group()) if match else None
        max_int_suffix = -1
        has_int_suffix = False
        for name in name_list:
            if base_name != get_base_name(name):
                continue
            int_suffix = get_integer_suffix(name)
            if int_suffix:
                max_int_suffix = max(max_int_suffix, int_suffix)
                has_int_suffix = True
        if has_int_suffix:
            new_name = base_name + str(max_int_suffix + 1)
        else:
            new_name = base_name
            if new_name in name_list:
                new_name = base_name + "2"
        return new_name

    path = self.path_from_id()
    parent_path_match = re.match(r'(.*)\[\d+\]$', path)
    if parent_path_match:
        item_list = self.id_data.path_resolve(parent_path_match.group(1))
    else:
        return

    name_list = [item.attribute_name for item in item_list if item != self]
    unset_name = "unset_uvw_attribute_name"
    default_name = "flip_uvw"
    is_updated_by_user = self.attribute_name != unset_name

    new_name = self.attribute_name
    if is_updated_by_user:
        # Case 1: User Changed Name - Increment int suffix if needed
        if new_name in name_list:
            base_name = get_base_name(new_name)
            new_name = get_unique_name(base_name, name_list)
    else:
        # Case 2: New Entry - Set base name to base of last entry,
        # increment int suffix if needed
        base_name = default_name
        if name_list:
            base_name = get_base_name(name_list[-1])
        new_name = get_unique_name(base_name, name_list)

    self["attribute_name"] = new_name


def update_remap_uvw_frame(self, context):
    self.status = RemapUVWItemStatus.READY


class RemapUVWItemStatus(enum.StrEnum):
    READY                        = "READY"
    LOADED                       = "LOADED"
    ERROR_REMAP_FRAME_NOT_CACHED = "ERROR_REMAP_FRAME_NOT_CACHED"
    ERROR_UID_NOT_CACHED         = "ERROR_UID_NOT_CACHED"
    ERROR_ZERO_LENGTH_FRAME      = "ERROR_ZERO_LENGTH_FRAME"
    ERROR_CORRUPT_FRAME          = "ERROR_CORRUPT_FRAME"
    ERROR_UNKNOWN                = "ERROR_UNKNOWN"
    

class FLIPFluidRemapUVWItem(bpy.types.PropertyGroup):
    attribute_name: bpy.props.StringProperty(
        name="Attribute Name",
        description="Attribute name for the generated fluid particle UVW attribute. The associated UVW attribute can be accessed in a shader, geometry nodes, or spreadsheet editor under this attribute name",
        default="unset_uvw_attribute_name",
        update=update_remap_uvw_name,
        options={'HIDDEN'},
    )
    frame: bpy.props.IntProperty(
        name="Frame",
        description="Target bind frame in the timeline where UVW coordinates are aligned",
        default=1,
        update=update_remap_uvw_frame,
    )
    status: bpy.props.StringProperty(
        name="Remap UVW Status",
        description="Current status of the generated fluid particle UVW attribute. Reload frame to update status",
        default="READY",
        options={'HIDDEN'},
    )


class LUTMode(enum.Enum):
    DIRECT = 1
    SORTED = 2


class FLIPFluidVirtualUVWAttribute(bpy.types.PropertyGroup):
    runtime_cache_id: bpy.props.IntProperty(
        name="Runtime Cache ID",
        default=-1,
    )


    def init(self):
        global _RUNTIME_CACHE
        if self.runtime_cache_id == -1:
            self.runtime_cache_id = get_new_id()
        if self.runtime_cache_id not in _RUNTIME_CACHE:
            _RUNTIME_CACHE[self.runtime_cache_id] = {}


    def reset(self):
        global _RUNTIME_CACHE
        _RUNTIME_CACHE.pop(self.runtime_cache_id, None)
        self.property_unset("runtime_cache_id")


    def get_runtime_cache(self):
        global _RUNTIME_CACHE
        self.init()
        return _RUNTIME_CACHE[self.runtime_cache_id]


    def get_frame_uid_to_uvw_lookup_table(self, frameno):
        cache = self.get_runtime_cache()
        frame_cache = cache.get(frameno, None)
        if frame_cache is None:
            return None
        return frame_cache["lookup_table"]


    def _initialize_attribute_item(self, item, aabb):
        global _DEFAULT_UVW

        frameno = item.frame
        cache = self.get_runtime_cache()

        # Read frame data
        uid_filepath = cache_utils.get_bakefile_filepath(MeshType.FLUID_PARTICLES, "fluidparticles", "uid", DataType.INT, frameno)
        position_filepath = cache_utils.get_bakefile_filepath(MeshType.FLUID_PARTICLES, "fluidparticles", "", DataType.FLOAT_VECTOR, frameno)
        
        if not os.path.isfile(position_filepath):
            item.status = RemapUVWItemStatus.ERROR_REMAP_FRAME_NOT_CACHED
            return

        if not os.path.isfile(uid_filepath):
            item.status = RemapUVWItemStatus.ERROR_UID_NOT_CACHED
            return

        uid_data = cache_utils.import_ffp3_values(uid_filepath, attribute_type=DataType.INT)
        position_data = cache_utils.import_ffp3_values(position_filepath, attribute_type=DataType.FLOAT_VECTOR)
        if len(uid_data) == 0 or len(position_data) == 0:
            item.status = RemapUVWItemStatus.ERROR_ZERO_LENGTH_FRAME
            return

        if len(uid_data) != len(position_data) // 3:
            # This should not happen
            item.status = RemapUVWItemStatus.ERROR_CORRUPT_FRAME
            return

        try:
            # Compute frame UVW
            aabb_offset = np.array([aabb.x, aabb.y, aabb.z], dtype=np.float32)
            aabb_dims = np.array([aabb.width, aabb.height, aabb.depth], dtype=np.float32)
            uvw_data = ((position_data.reshape(-1, 3) - aabb_offset) / aabb_dims)

            # Construct UID -> UVW lookup table
            uid_min, uid_max = uid_data.min(), uid_data.max()
            uid_range = uid_max - uid_min + 1
            density = len(uid_data) / uid_range

            density_threshold = 0.50
            range_threshold = int(5e6)
            lut_mode = LUTMode.DIRECT if density > density_threshold or uid_range < range_threshold else LUTMode.SORTED

            lookup_table_func = None
            if lut_mode == LUTMode.DIRECT:
                uid_data -= uid_min
                max_key = uid_max - uid_min
                lookup_table = np.tile(_DEFAULT_UVW, (max_key + 1, 1))
                lookup_table[uid_data] = uvw_data

                def lookup_table_func_direct(np_index_list):
                    np_offset_index_list = np_index_list - uid_min
                    valid_mask = (np_offset_index_list >= 0) & (np_offset_index_list <= max_key)
                    np_result_shape = np_offset_index_list.shape + (3,)
                    np_result = np.tile(_DEFAULT_UVW, np_offset_index_list.shape + (1,)).reshape(np_result_shape)
                    np_result[valid_mask] = lookup_table[np_offset_index_list[valid_mask]]
                    return np_result.flatten()
                lookup_table_func = lookup_table_func_direct

            elif lut_mode == LUTMode.SORTED:
                sorted_indices = np.argsort(uid_data)
                uid_data = uid_data[sorted_indices]
                uvw_data = uvw_data[sorted_indices]

                def lookup_table_func_sorted(np_index_list):
                    search_indices = np.searchsorted(uid_data, np_index_list)
                    in_range_mask = search_indices < len(uid_data)
                    safe_indices = np.where(in_range_mask, search_indices, 0)
                    valid_mask = in_range_mask & (uid_data[safe_indices] == np_index_list)
                    np_result = np.empty((len(np_index_list), 3), dtype=np.float32)
                    np_result[:] = _DEFAULT_UVW
                    np_result[valid_mask] = uvw_data[safe_indices[valid_mask]]
                    return np_result.flatten()
                lookup_table_func = lookup_table_func_sorted
            
            cache[frameno] = {
                "frame": frameno,
                "lookup_table_mode": lut_mode,
                "lookup_table": lookup_table_func
                }

            if item.attribute_name == "flip_error_example":
                raise Exception("This is an example error triggered by setting the UVW attribute name to 'flip_error_example'")
        except:
            item.status = RemapUVWItemStatus.ERROR_UNKNOWN
            traceback.print_exc()
            print("FLIP Fluids: An error has occurred while loading the frame. Please contact the developers with the above error message.")
            return

        item.status = RemapUVWItemStatus.LOADED


    def update_uvw_attributes(self, uvw_attribute_items, aabb):
        frameno_list = [item.frame for item in uvw_attribute_items]

        cache = self.get_runtime_cache()
        for frameno in list(cache.keys()):
            if frameno not in frameno_list:
                cache.pop(frameno, None)

        initialize_item_list = []
        for item in uvw_attribute_items:
            if item.frame not in cache:
                initialize_item_list.append(item)

        for item in initialize_item_list:
            self._initialize_attribute_item(item, aabb)


def register():
    bpy.utils.register_class(FLIPFluidRemapUVWItem)
    bpy.utils.register_class(FLIPFluidVirtualUVWAttribute)


def unregister():
    bpy.utils.unregister_class(FLIPFluidRemapUVWItem)
    bpy.utils.unregister_class(FLIPFluidVirtualUVWAttribute)