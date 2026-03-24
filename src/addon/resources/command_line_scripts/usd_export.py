
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

import bpy, mathutils, os, time, sys

def check_cache_exists():
    cache_directory = dprops.cache.get_cache_abspath()
    bakefiles_directory = os.path.join(cache_directory, "bakefiles")

    file_count = 0
    cache_exists = False
    if os.path.isdir(bakefiles_directory):
        cache_exists = True
        file_count = len(os.listdir(bakefiles_directory))

    if not cache_exists or file_count == 0:
        print("\nError: Simulation cache does not exist. Nothing to export. Exiting.")
        return False
    return True


def create_mesh_proxy_object(bl_collection, object_name):
    proxy_mesh = bpy.data.meshes.new(object_name + "_mesh_data")
    proxy_object = bpy.data.objects.new(object_name, proxy_mesh)
    bl_collection.objects.link(proxy_object)
    return proxy_object


def create_pointcloud_proxy_object(bl_collection, object_name):
    proxy_mesh = bpy.data.pointclouds.new(object_name + "_pointcloud_data")
    proxy_object = bpy.data.objects.new(object_name, proxy_mesh)
    bl_collection.objects.link(proxy_object)
    return proxy_object


def get_active_flip_fluids_geometry_node_modifiers(bl_object):
    modifiers = []
    for mod in bl_object.modifiers:
        if mod.type == 'NODES' and mod.show_viewport and ff_modifier_substring in mod.name:
            modifiers.append(mod)
    return modifiers


def add_geometry_node_modifier(target_object, resource_filepath, resource_name):
    for mod in target_object.modifiers:
        if mod.type == 'NODES' and mod.name == resource_name:
            # Already added
            return mod
        
    node_group = bpy.data.node_groups.get(resource_name)
    if node_group is None:
        is_resource_found = False
        with bpy.data.libraries.load(resource_filepath) as (data_from, data_to):
            resource = [name for name in data_from.node_groups if name == resource_name]
            if resource:
                is_resource_found = True
                data_to.node_groups = resource
                
        if not is_resource_found:
            return None
        
        imported_resource_name = data_to.node_groups[0].name
    else:
        # already imported
        imported_resource_name = node_group.name
        
    gn_modifier = target_object.modifiers.new(resource_name, type="NODES")
    gn_modifier.node_group = bpy.data.node_groups.get(imported_resource_name)
    return gn_modifier


def add_dummy_modifier(bl_object):
    # Smooth modifier that is active (factor > 0), but does nothing (iterations = 0)
    smooth_mod = bl_object.modifiers.new("FF_DummyModifier", "SMOOTH")
    smooth_mod.factor = 1.0
    smooth_mod.iterations = 0
    return smooth_mod


def get_object_centroid_world(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    vector_sum = sum((v.co for v in obj_eval.data.vertices), mathutils.Vector())
    centroid_local = vector_sum / len(obj_eval.data.vertices)
    centroid_world = obj_eval.matrix_world @ centroid_local
    return centroid_world


def get_export_frame_range():
    hprops = bpy.context.scene.flip_fluid_helper
    if hprops.usd_frame_range_mode == 'FRAME_RANGE_CUSTOM':
        bpy.context.scene.frame_start = hprops.usd_frame_range_custom.value_min
        bpy.context.scene.frame_end = hprops.usd_frame_range_custom.value_max

    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end

    return frame_start, frame_end


def get_usd_output_filepath():
    hprops = bpy.context.scene.flip_fluid_helper

    script_arguments = None
    if "--" in sys.argv:
        script_arguments = sys.argv[sys.argv.index("--") + 1:]

    # If an argument has been passed in, override the 'usd_output_filepath' property
    if script_arguments is not None and len(script_arguments) >= 1:
        override_filepath = script_arguments[0]
        hprops.usd_output_filepath = override_filepath
        print("Overriding USD output filepath to script argument at position 0: <" + override_filepath + ">")

    usd_filepath = hprops.get_usd_output_abspath()
    if not usd_filepath.endswith(".usdc"):
        if usd_filepath.endswith("."):
            usd_filepath += "usdc"
        else:
            usd_filepath += ".usdc"

    return usd_filepath


#
# Error Checking
#

dprops = bpy.context.scene.flip_fluid.get_domain_properties()
if dprops is None:
    print("\nError: No domain found in Blend file. Hint: Did you remember to save the Blend file before running this operator? Exiting.")
    exit()

retval = check_cache_exists()
if not retval:
    exit()

#
# Prepare scene for export
#

print("\n*** Preparing Universal Scene Description (USD) Export ***\n")

if bpy.context.mode != 'OBJECT':
    # Meshes can only be exported in Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Viewport set to Object Mode.\n")

hprops = bpy.context.scene.flip_fluid_helper

# Collection for proxy objects
usd_collection_name = "_FF_USDExport"
usd_collection = bpy.data.collections.get(usd_collection_name)
if not usd_collection:
    usd_collection = bpy.data.collections.new(usd_collection_name)
    bpy.context.scene.collection.children.link(usd_collection)

# Create proxy objects
bl_domain = bpy.context.scene.flip_fluid.get_domain_object()
bl_fluid_surface = dprops.mesh_cache.surface.get_cache_object()
bl_fluid_particles = dprops.mesh_cache.particles.get_cache_object()
bl_whitewater_foam = dprops.mesh_cache.foam.get_cache_object()
bl_whitewater_bubble = dprops.mesh_cache.bubble.get_cache_object()
bl_whitewater_spray = dprops.mesh_cache.spray.get_cache_object()
bl_whitewater_dust = dprops.mesh_cache.dust.get_cache_object()

proxy_object_info = [
    {"enabled": False, "export_prop_name": "usd_export_domain",          "bl_cache_object": bl_domain,            "proxy_object_name": "ff_usd_domain",            "proxy_object_type": "DOMAIN",         "geometry_nodes_display_mode": 0},
    {"enabled": False, "export_prop_name": "usd_export_surface",         "bl_cache_object": bl_fluid_surface,     "proxy_object_name": "ff_usd_fluid_surface",     "proxy_object_type": "SURFACE",        "geometry_nodes_display_mode": 0},
    {"enabled": False, "export_prop_name": "usd_export_fluid_particles", "bl_cache_object": bl_fluid_particles,   "proxy_object_name": "ff_usd_fluid_particles",   "proxy_object_type": "FLUID_PARTICLE", "geometry_nodes_display_mode": 0},
    {"enabled": False, "export_prop_name": "usd_export_foam",            "bl_cache_object": bl_whitewater_foam,   "proxy_object_name": "ff_usd_whitewater_foam",   "proxy_object_type": "WHITEWATER",     "geometry_nodes_display_mode": 0},
    {"enabled": False, "export_prop_name": "usd_export_bubble",          "bl_cache_object": bl_whitewater_bubble, "proxy_object_name": "ff_usd_whitewater_bubble", "proxy_object_type": "WHITEWATER",     "geometry_nodes_display_mode": 0},
    {"enabled": False, "export_prop_name": "usd_export_spray",           "bl_cache_object": bl_whitewater_spray,  "proxy_object_name": "ff_usd_whitewater_spray",  "proxy_object_type": "WHITEWATER",     "geometry_nodes_display_mode": 0},
    {"enabled": False, "export_prop_name": "usd_export_dust",            "bl_cache_object": bl_whitewater_dust,   "proxy_object_name": "ff_usd_whitewater_dust",   "proxy_object_type": "WHITEWATER",     "geometry_nodes_display_mode": 0},
    ]

for info in proxy_object_info:
    if not getattr(hprops, info["export_prop_name"]) or not info["bl_cache_object"]:
        continue

    if   info["proxy_object_type"] in ["SURFACE", "DOMAIN"]:
        bl_object = create_mesh_proxy_object(usd_collection, info["proxy_object_name"])
    elif info["proxy_object_type"] in ["FLUID_PARTICLE", "WHITEWATER"]:
        bl_object = create_pointcloud_proxy_object(usd_collection, info["proxy_object_name"])

    info["proxy_object_name"] = bl_object.name
    info["enabled"] = True

# Adjust source objects
for info in proxy_object_info:
    if not info["enabled"]:
        continue
    # Workaround for exporters not recognizing objects as animated unless object contains a modifier.
    # Add a 'dummy' modifier that does nothing.
    add_dummy_modifier(info["bl_cache_object"])

# Adjust source FF_GeometryNodes modifiers
ff_modifier_substring = "FF_GeometryNodes"
particle_display_mode_socket = "Socket_12"
display_mode_none_enum = 0
display_mode_pointcloud_enum = 1
for info in proxy_object_info:
    if not info["enabled"] or not info["proxy_object_type"] in ["FLUID_PARTICLE", "WHITEWATER"]:
        continue

    bl_cache_object = info["bl_cache_object"]
    ff_geometry_node_modifiers = get_active_flip_fluids_geometry_node_modifiers(bl_cache_object)
    for mod in ff_geometry_node_modifiers:
        if particle_display_mode_socket in mod and isinstance(mod[particle_display_mode_socket], int):
            # Only Point Cloud display modes are supported for export.
            if not mod[particle_display_mode_socket] == display_mode_pointcloud_enum:
                mod[particle_display_mode_socket] = display_mode_pointcloud_enum
            info["geometry_nodes_display_mode"] = mod[particle_display_mode_socket]
        else:
            # Invalid display mode socket - may be an older FF_GeometryNodes version. In this case, remove modifier.
            bl_cache_object.modifiers.remove(bl_cache_object.modifiers[mod.name])
            info["geometry_nodes_display_mode"] = display_mode_none_enum


# Add FF_USDExport modifiers to proxy objects
resources_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
geometry_nodes_library = os.path.join(resources_path, "geometry_nodes", "geometry_nodes_library.blend")

attribute_export_prop_names = [
    "usd_export_velocity",
    "usd_export_speed",
    "usd_export_vorticity",
    "usd_export_color",
    "usd_export_age",
    "usd_export_lifetime",
    "usd_export_whitewater_proximity",
    "usd_export_viscosity",
    "usd_export_density",
    "usd_export_id",
    "usd_export_uid",
    "usd_export_source_id",
    ]

option_to_socket_mapping = {
    "input_object":                       "Socket_2",
    "convert_to_point_cloud":             "Socket_3",
    "usd_export_velocity":                "Socket_4",
    "usd_export_speed":                   "Socket_5",
    "usd_export_vorticity":               "Socket_6",
    "usd_export_color":                   "Socket_7",
    "usd_export_age":                     "Socket_8",
    "usd_export_lifetime":                "Socket_9",
    "usd_export_whitewater_proximity":    "Socket_10",
    "usd_export_viscosity":               "Socket_11",
    "usd_export_density":                 "Socket_12",
    "usd_export_id":                      "Socket_13",
    "usd_export_uid":                     "Socket_14",
    "usd_export_source_id":               "Socket_15",
    "prevent_empty_point_cloud_geometry": "Socket_19",
    }

display_mode_pointcloud_enum = 1
for info in proxy_object_info:
    if not info["enabled"]:
        continue

    bl_proxy = bpy.data.objects.get(info["proxy_object_name"])
    gn_modifier = add_geometry_node_modifier(bl_proxy, geometry_nodes_library, "FF_USDExport")

    # Set modifier options
    convert_to_point_cloud = info["proxy_object_type"] in ["FLUID_PARTICLE", "WHITEWATER"] and info["geometry_nodes_display_mode"] != display_mode_pointcloud_enum
    gn_modifier[option_to_socket_mapping["input_object"]] = info["bl_cache_object"]
    gn_modifier[option_to_socket_mapping["convert_to_point_cloud"]] = convert_to_point_cloud
    for prop_name in attribute_export_prop_names:
        gn_modifier[option_to_socket_mapping[prop_name]] = not getattr(hprops, prop_name)

    # USD exporter/importer crashes on frames with empty point cloud geometry in Blender 5.0 and earlier.
    apply_workaround = bpy.app.version < (5, 1, 0) and info["proxy_object_type"] in ["FLUID_PARTICLE", "WHITEWATER"]
    gn_modifier[option_to_socket_mapping["prevent_empty_point_cloud_geometry"]] = apply_workaround

# Set export proxy object origins to centroid of domain
domain_centroid = get_object_centroid_world(bl_domain)
for info in proxy_object_info:
    if not info["enabled"]:
        continue
    bl_proxy_object = bpy.data.objects.get(info["proxy_object_name"])
    bl_proxy_object.location = domain_centroid

# Select objects for export
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = None
for info in proxy_object_info:
    if not info["enabled"]:
        continue
    bl_proxy_object = bpy.data.objects.get(info['proxy_object_name'])
    bl_proxy_object.select_set(True)

#
# Begin USD export
#

frame_start, frame_end = get_export_frame_range()
usd_filepath = get_usd_output_filepath()

EXPORT_FINISHED = False
FRAME_END = frame_end
TIMESTAMP = time.time()
TOTAL_TIME = 0.0
def frame_change_handler(scene):
    global EXPORT_FINISHED
    global FRAME_END
    global TIMESTAMP
    global TOTAL_TIME
    
    if not EXPORT_FINISHED:
        current_time = time.time()
        elapsed_time = current_time - TIMESTAMP
        TIMESTAMP = current_time
        TOTAL_TIME += elapsed_time
        
        info_msg = "Exported frame " + str(scene.frame_current)
        info_msg += " in " + '{0:.3f}'.format(elapsed_time) + " seconds  (total: " + '{0:.3f}'.format(TOTAL_TIME) + "s)"
        print(info_msg)
        
    if scene.frame_current == FRAME_END:
        EXPORT_FINISHED = True

bpy.app.handlers.frame_change_post.append(frame_change_handler)

print("Exporting Universal Scene Description (USD) to: <" + usd_filepath + ">")
print("Frame Range: " + str(frame_start) + " to " + str(frame_end))
print("")

bpy.ops.wm.usd_export(
        filepath=usd_filepath, 
        selected_objects_only=True,
        export_animation=True,
        evaluation_mode='VIEWPORT',
        export_lights=False,
        convert_world_material=False,
        export_cameras=False,
        export_materials=False,
        generate_preview_surface=False,
        )
