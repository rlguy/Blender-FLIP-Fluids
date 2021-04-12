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

import bpy, os, shutil, zipfile, json, re, binascii, random, posixpath
from bpy.props import CollectionProperty
from mathutils import Vector

from ..materials import material_library
from ..utils import version_compatibility_utils as vcu
from ..filesystem import filesystem_protection_layer as fpl

PACKAGE_INFO_LIST = None
PRESET_INFO_LIST = None
CUSTOM_PRESET_ICONS = None
IS_CUSTOM_PRESET_ICONS_LOADED = False


def get_all_package_enums(self, context):
    sys_info_list = __get_sys_package_info_list()
    usr_info_list = __get_usr_package_info_list()
    info_list = sys_info_list + usr_info_list
    info_list = __sort_package_info_list(info_list)

    enums = []
    for info in info_list:
        e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)
    return enums


def get_user_package_enums(self, context):
    info_list = __get_usr_package_info_list()
    info_list = __sort_package_info_list(info_list)

    enums = []
    for info in info_list:
        e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)
    return enums


def get_deletable_package_enums(self, context):
    info_list = __get_usr_package_info_list()
    info_list = __sort_package_info_list(info_list)

    enums = []
    enums.append(('DELETE_PACKAGE_NONE', "None", "", 0))
    for info in info_list:
        e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)
    return enums


def get_exportable_package_enums(self, context):
    info_list = __get_usr_package_info_list()
    info_list = __sort_package_info_list(info_list)

    enums = []
    enums.append(('EXPORT_PACKAGE_NONE', "None", "", 0))
    for info in info_list:
        e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)
    return enums


def get_current_package_preset_enums(self, context):
    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return []
    current_package = dprops.presets.current_package
    package_info = package_identifier_to_info(current_package)
    info_list = get_package_presets_info_list(current_package)
    info_list = __sort_preset_info_list(info_list)
    preset_icons = get_custom_icons()

    enums = []
    for info in info_list:
        icon = None
        if package_info["use_custom_icons"]:
            if "icon" in info and info["icon"] in preset_icons:
                icon = preset_icons.get(info["icon"]).icon_id
        if icon:
            e = (info['identifier'], info['name'], info['description'], icon, info['uid'])
        else:
            e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)

    enums.append(('PRESET_NONE', "None", "", 0))

    # Reverse to display in order in template_icon_view
    if package_info["use_custom_icons"]:
        enums = enums[::-1]
    return enums


def get_package_preset_enums(self, context, package_id):
    if package_id == "":
        package_id = get_all_package_enums(self, context)[0][0]

    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return []
    package_info = package_identifier_to_info(package_id)
    info_list = get_package_presets_info_list(package_id)
    info_list = __sort_preset_info_list(info_list)
    preset_icons = get_custom_icons()

    enums = []
    for info in info_list:
        icon = None
        if package_info["use_custom_icons"]:
            if "icon" in info and info["icon"] in preset_icons:
                icon = preset_icons.get(info["icon"]).icon_id
        if icon:
            e = (info['identifier'], info['name'], info['description'], icon, info['uid'])
        else:
            e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)

    enums.append(('PRESET_NONE', "None", "", 0))

    # Reverse to display in order in template_icon_view
    if package_info["use_custom_icons"]:
        enums = enums[::-1]
    return enums


def get_deletable_preset_enums(self, context):
    dprops = context.scene.flip_fluid.get_domain_properties()
    if dprops is None:
        return []
    selected_package = dprops.presets.delete_preset_settings.package
    package_info = package_identifier_to_info(selected_package)
    preset_info_list = get_package_presets_info_list(selected_package)
    preset_info_list = __sort_preset_info_list(preset_info_list)
    preset_icons = get_custom_icons()

    enums = []
    enums.append(('DELETE_PRESET_NONE', "None", "", 0))
    for info in preset_info_list:
        icon = None
        if package_info["use_custom_icons"]:
            if "icon" in info and info["icon"] in preset_icons:
                icon = preset_icons.get(info["icon"]).icon_id
        if icon:
            e = (info['identifier'], info['name'], info['description'], icon, info['uid'])
        else:
            e = (info['identifier'], info['name'], info['description'], info['uid'])
        enums.append(e)
    return enums


def package_identifier_to_info(identifier):
    package_info_list = get_package_info_list()
    for info in package_info_list:
        if info['identifier'] == identifier:
            return info
    return None


def preset_identifier_to_info(identifier):
    preset_info_list = get_preset_info_list()
    for info in preset_info_list:
        if info['identifier'] == identifier:
            return info
    return None


def get_package_info_list():
    global PACKAGE_INFO_LIST
    if PACKAGE_INFO_LIST is None:
        __initialize_package_info_list()
    return PACKAGE_INFO_LIST


def get_preset_info_list():
    global PRESET_INFO_LIST
    if PRESET_INFO_LIST is None:
        __initialize_preset_info_list()
    return PRESET_INFO_LIST


def get_custom_icons():
    global CUSTOM_PRESET_ICONS
    global IS_CUSTOM_PRESET_ICONS_LOADED
    if not IS_CUSTOM_PRESET_ICONS_LOADED:
        __initialize_preset_info_list()
    return CUSTOM_PRESET_ICONS


def get_preset_material_paths():
    material_paths = [
        "domain.materials.surface_material",
        "domain.materials.whitewater_foam_material",
        "domain.materials.whitewater_bubble_material",
        "domain.materials.whitewater_spray_material"
    ]
    return material_paths


def get_user_package_info_list():
    package_info_list = get_package_info_list()
    pkgs = []
    for info in package_info_list:
        if not info['is_system_package']:
            pkgs.append(info)
    return pkgs


def get_default_user_package_info_list():
    package_info_list = get_package_info_list()
    pkgs = []
    for info in package_info_list:
        if info['is_default_user_package']:
            pkgs.append(info)
    return pkgs


def get_system_package_info_list():
    package_info_list = get_package_info_list()
    pkgs = []
    for info in package_info_list:
        if info['is_system_package']:
            pkgs.append(info)
    return pkgs


def get_package_presets_info_list(package_id):
    preset_info_list = get_preset_info_list()
    presets = []
    for p in preset_info_list:
        if p["package"] == package_id:
            presets.append(p)
    return presets


def generate_dummy_domain_object():
    dobj = bpy.context.scene.flip_fluid.get_domain_object()
    mesh_data = bpy.data.meshes.new("temp_domain_mesh")
    mesh_data.from_pydata([], [], [])
    dummy_object = bpy.data.objects.new("temp_domain_object", mesh_data)
    vcu.link_object(dummy_object, bpy.context)
    dummy_object.flip_fluid.domain.dummy_initialize()
    if dobj is not None:
        dummy_object.parent = dobj
    vcu.depsgraph_update()
    return dummy_object


def destroy_dummy_domain_object(domain_object):
    vcu.delete_object(domain_object)
    vcu.depsgraph_update()


def get_system_default_preset_dict():
    sys_path = __get_sys_preset_path()
    default_preset_path = os.path.join(sys_path, "default.preset")
    with open(default_preset_path, 'r', encoding='utf-8') as f:
        try:
            data = json.loads(f.read())
        except:
            print("Error decoding default preset file: <" + default_preset_path + ">")
    return data


def initialize_default_user_package():
    __initialize_default_user_package()
    __initialize_package_info_list()


def save_user_default_settings():
    domain_object = bpy.context.scene.flip_fluid.get_domain_object()
    if domain_object is None:
        return False

    usr_path = __get_usr_preset_path()
    default_file = os.path.join(usr_path, "default.preset")
    if os.path.exists(default_file):
        fpl.delete_file(default_file)

    preset_dict = __get_default_preset_dict(domain_object)
    __write_dict_to_json(preset_dict, default_file)

    return True


def delete_user_default_settings():
    domain_object = bpy.context.scene.flip_fluid.get_domain_object()
    if domain_object is None:
        return False

    usr_path = __get_usr_preset_path()
    default_file = os.path.join(usr_path, "default.preset")
    if os.path.exists(default_file):
        fpl.delete_file(default_file)

    return True


def load_default_settings(domain_properties):
    usr_path = __get_usr_preset_path()
    default_preset_file = os.path.join(usr_path, "default.preset")
    if not os.path.isfile(default_preset_file):
        sys_path = __get_sys_preset_path()
        default_preset_file = os.path.join(sys_path, "default.preset")
        if not os.path.isfile(default_preset_file):
            return

    with open(default_preset_file, 'r', encoding='utf-8') as f:
        try:
            default_data = json.loads(f.read())
        except:
            print("Error decoding default preset file: <" + default_preset_file + ">")

    for p in default_data['properties']:
        path, value = p['path'], p['value']
        domain_properties.set_property_from_path(path, value)


def restore_default_settings(domain_properties):
    sys_path = __get_sys_preset_path()
    default_preset_file = os.path.join(sys_path, "default.preset")
    if not os.path.isfile(default_preset_file):
        return "Missing default preset file: <" + default_preset_file + ">"

    with open(default_preset_file, 'r', encoding='utf-8') as f:
        try:
            default_data = json.loads(f.read())
        except:
            return "Unable to decode default preset file: <" + default_preset_file + ">"

    for p in default_data['properties']:
        path, value = p['path'], p['value']
        domain_properties.set_property_from_path(path, value)


def create_new_user_package(package_info_dict):
    name = package_info_dict['name']
    package_ids = __get_package_identifiers()
    identifier = __name_to_unique_identifier(name, package_ids)
    if not identifier:
        return "Unable to create unique package identifier"

    package_info_dict["identifier"] = identifier
    package_info_dict["uid"] = __generate_package_uid()
    package_info_dict["is_default_user_package"] = False
    package_info_dict["is_system_package"] = False

    usr_path = __get_usr_preset_path()
    package_path = os.path.join(usr_path, identifier)
    if os.path.exists(package_path):
        err = ("Unable to create package directory. Directory already exists <" +
               package_path + ">")
        return err

    try:
        os.makedirs(package_path)
    except:
        return "Unable to create package directory"

    info_file_path = os.path.join(package_path, "package.info")
    __write_dict_to_json(package_info_dict, info_file_path)
    __initialize_package_info_list()


def delete_package(identifier):
    package_info = package_identifier_to_info(identifier)
    package_path = package_info["path"]
    try:
        fpl.delete_files_in_directory(package_path, [".info", ".md"], remove_directory=True)
    except:
        return "Unable to delete package directory <" + package_path + ">"
    __initialize_package_info_list()


def create_new_user_preset(preset_info_dict):
    name = preset_info_dict['name']
    preset_ids = __get_preset_identifiers()
    identifier = __name_to_unique_identifier(name, preset_ids)
    if not identifier:
        return "Unable to create unique preset identifier"

    preset_info_dict["identifier"] = identifier
    preset_info_dict["uid"] = __generate_preset_uid()
    preset_info_dict["is_system_preset"] = False

    package_info = package_identifier_to_info(preset_info_dict["package"])
    package_path = package_info["path"]
    if not package_path:
        return "Unable to locate package directory: <" + preset_info_dict["package"] + ">"

    preset_directory = os.path.join(package_path, identifier)    
    preset_path = os.path.join(preset_directory, "data.preset")
    if os.path.exists(preset_directory):
        err = ("Unable to create preset directory. Directory already exists <" +
               preset_directory + ">")
        return err
    else:
        os.makedirs(preset_directory)

    if preset_info_dict["icon"]:
        icon_imgdata = bpy.data.images.get(preset_info_dict["icon"])
        if not icon_imgdata:
            return "Unable to locate icon: <" + preset_info_dict["icon"] + ">"

        icon_directory = preset_directory
        icon_name = "icon.png"
        if not os.path.isdir(icon_directory):
            os.makedirs(icon_directory)
        icon_path = os.path.join(icon_directory, icon_name)
        __write_preset_icon(icon_imgdata, icon_path)

    __write_preset_materials(preset_directory, preset_info_dict)

    del preset_info_dict["package"]
    del preset_info_dict["icon"]
    if 'edit_package' in preset_info_dict:
        del preset_info_dict['edit_package']
    if 'edit_preset' in preset_info_dict:
        del preset_info_dict['edit_preset']

    __write_dict_to_json(preset_info_dict, preset_path)
    __initialize_preset_info_list()


def edit_user_preset(preset_info_dict):
    edit_preset_info = preset_identifier_to_info(preset_info_dict['edit_preset'])
    original_preset_path = edit_preset_info['path']
    error = create_new_user_preset(preset_info_dict)
    if error:
        return error

    try:
        fpl.delete_files_in_directory(original_preset_path, [".preset", ".png"], remove_directory=True)
    except:
        return "Unable to delete original preset directory <" + original_preset_path + ">"

    __initialize_package_info_list()
    __initialize_preset_info_list()


def delete_preset(identifier):
    preset_info = preset_identifier_to_info(identifier)
    preset_path = preset_info["path"]
    try:
        fpl.delete_files_in_directory(preset_path, [".preset", ".png"], remove_directory=True)
    except:
        return "Unable to delete preset directory <" + preset_path + ">"
    __initialize_preset_info_list()


def export_package(identifier, filepath, create_directory=True):
    directory = os.path.dirname(filepath)
    if create_directory and not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except:
            return ("Unable to create file: <" + filepath + ">. Please choose" + 
                    " another filepath. This directory may be invalid or you may not" + 
                    " have permission to write in this directory.")
    if not os.path.isdir(directory):
        return "Directory does not exist <" + filepath + ">"

    info = package_identifier_to_info(identifier)
    if not info:
        return "Package does not exist <" + identifier + ">"
    package_path = info['path']
    
    try:
        shutil.make_archive(filepath.replace(".zip", ""), 'zip', package_path)
    except:
        return "Error creating package archive"


def import_package(package_filepath):
    package_data = {}
    error = decode_package_zipfile(package_filepath, package_data)
    if error:
        return error

    package_identifier = package_data['identifier']
    if package_data['is_system_package']:
        package_path = __get_sys_preset_path()
    else:
        package_path = __get_usr_preset_path()
    package_path = os.path.join(package_path, package_identifier)

    if os.path.isdir(package_path):
        return "Package already exists <" + package_path + ">"

    try:
        shutil.unpack_archive(package_filepath, package_path, 'zip')
    except:
        return "Unable to unpack package"

    __initialize_package_info_list()
    __initialize_preset_info_list()


def decode_package_zipfile(filepath, dst_data):
    if not os.path.isfile(filepath):
        return "Package file does not exist <" + filepath + ">"

    with open(filepath, 'rb') as f, zipfile.ZipFile(f, 'r') as zfile:
        filelist = zfile.namelist()

        package_file = None
        for f in filelist:
            if f == "package.info":
                package_file = f
                break
        if package_file is None:
            return "Unable to find package info file"

        with zfile.open(package_file, "r", encoding='utf-8') as info_file:
            try:
                pinfo = json.loads(info_file.read().decode("utf-8"))
            except:
                return "Unable to decode package info file"

        preset_data_files = []
        for f in filelist:
            if os.path.basename(f) == "data.preset":
                preset_data_files.append(f)

        dst_data.update(pinfo)
        dst_data['presets'] = []
        for f in preset_data_files:
            with zfile.open(f, 'r', encoding='utf-8') as info_file:
                try:
                    info = json.loads(info_file.read().decode("utf-8"))
                except:
                    return "Unable to decode preset info file <" + f + ">"

                icon_path = os.path.join(os.path.dirname(f), "icon.png")
                icon_path = posixpath.join(*icon_path.split('\\'))
                if icon_path in filelist:
                    temp_dir = __get_temp_preset_path()
                    zfile.extract(icon_path, temp_dir)
                    full_icon_path = os.path.normpath(os.path.join(temp_dir, icon_path))
                    info['icon'] = full_icon_path

                material_blend_path = os.path.join(os.path.dirname(f), "materials.blend")
                material_blend_path = posixpath.join(*material_blend_path.split('\\'))
                if material_blend_path in filelist:
                    temp_dir = __get_temp_preset_path()
                    zfile.extract(material_blend_path, temp_dir)
                    full_blend_path = os.path.normpath(os.path.join(temp_dir, material_blend_path))
                    info['material_blend'] = full_blend_path

                dst_data['presets'].append(info)


def clear_temp_files():
    temp_dir = __get_temp_preset_path()
    try:
        fpl.delete_files_in_directory(temp_dir, [".info", ".md"], remove_directory=True)
    except:
        print("Error clearing temp directory <" + temp_dir + ">")


def load_post():
    __initialize_package_info_list()
    __initialize_preset_info_list()


def initialize():
    __initialize_default_preset()
    __initialize_package_info_list()
    __initialize_preset_info_list()


def __get_preset_resources_path():
    file_path = os.path.dirname(os.path.realpath(__file__))
    res_path = os.path.join(file_path, "preset_library", "resources")
    if not os.path.exists(res_path):
        os.makedirs(res_path)
    return res_path


def __get_sys_preset_path():
    file_path = os.path.dirname(os.path.realpath(__file__))
    sys_path = os.path.join(file_path, "preset_library", "sys")
    if not os.path.exists(sys_path):
        os.makedirs(sys_path)
    return sys_path


def __get_usr_preset_path():
    file_path = os.path.dirname(os.path.realpath(__file__))
    usr_path = os.path.join(file_path, "preset_library", "usr")
    if not os.path.exists(usr_path):
        os.makedirs(usr_path)
    return usr_path


def __get_temp_preset_path():
    file_path = os.path.dirname(os.path.realpath(__file__))
    temp_path = os.path.join(file_path, "preset_library", "temp")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    return temp_path


def __create_empty_blend_file(dst_path):
    res_path = __get_preset_resources_path()
    empty_blend_path = os.path.join(res_path, "empty.blend")
    shutil.copyfile(empty_blend_path, dst_path)


def __write_dict_to_json(d, filepath):
    jsonstr = json.dumps(d, sort_keys=True, indent=4)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(jsonstr)


def __write_preset_icon(icon_imgdata, icon_path):
    icon_imgdata.filepath_raw = icon_path
    icon_imgdata.file_format = 'PNG'

    if icon_imgdata.size[0] == 0 or icon_imgdata.size[1] == 0:
        errmsg = ("Error reading preset icon: invalid size <" + str(icon_imgdata.size[0]) + 
                  ", " + str(icon_imgdata.size[1]) + ">")
        print(errmsg)
        image = bpy.data.images.new("blank_icon", width=256, height=256, alpha=True)
        image.filepath_raw = icon_path
        image.file_format = 'PNG'
        image.save()
        bpy.data.images.remove(image)
        return

    if icon_imgdata.size[0] != 256 or icon_imgdata.size[1] != 256:
        if icon_imgdata.size[0] > icon_imgdata.size[1]:
            yres = (icon_imgdata.size[1] / icon_imgdata.size[0]) * 256
            icon_imgdata.scale(256, yres)
        else:
            xres = (icon_imgdata.size[0] / icon_imgdata.size[1]) * 256
            icon_imgdata.scale(xres, 256)
    icon_imgdata.save()


def __write_preset_materials(preset_directory, preset_info):
    material_paths = get_preset_material_paths()
    non_library_material_names = []
    for p in preset_info['properties']:
        if not (p['path'] in material_paths) or p['value'] == 'MATERIAL_NONE':
            continue
        material_name = material_library.import_material(p['value'])
        material_object = bpy.data.materials.get(material_name)
        if material_object is None:
            continue
        if material_object.flip_fluid_material_library.is_library_material:
            continue
        if material_name in non_library_material_names:
            continue
        non_library_material_names.append(material_name)

        material_structs = set()
        material_structs.add(material_object)
        material_blend_path = os.path.join(preset_directory, material_name + ".blend")
        __create_empty_blend_file(material_blend_path)
        bpy.data.libraries.write(material_blend_path, material_structs, fake_user=True)


def __get_default_preset_dict(domain_object):
    preset = {}
    preset['name'] = 'Default'
    preset['identifier'] = 'PRESET_DEFAULT'
    preset['description'] = 'Default Settings'
    preset['properties'] = []

    dprops = domain_object.flip_fluid.domain
    property_paths = dprops.property_registry.get_property_paths()
    for p in property_paths:
        value = dprops.get_property_from_path(p)
        preset['properties'].append({'path': p, 'value': value})
    return preset


def __initialize_default_preset():
    sys_path = __get_sys_preset_path()
    default_file = os.path.join(sys_path, "default.preset")
    if os.path.exists(default_file):
        fpl.delete_file(default_file)

    domain_object = generate_dummy_domain_object()
    preset_dict = __get_default_preset_dict(domain_object)
    destroy_dummy_domain_object(domain_object)
    __write_dict_to_json(preset_dict, default_file)


def __get_default_user_package_dict():
    package_name = "Custom User Presets"
    package_ids = __get_package_identifiers()
    identifier = __name_to_unique_identifier(package_name, package_ids)

    pkg_info = {}
    pkg_info['name'] = package_name
    pkg_info['author'] = ""
    pkg_info['description'] = "Custom user created presets"
    pkg_info['identifier'] = identifier
    pkg_info['uid'] = __generate_package_uid()
    pkg_info['use_custom_icons'] = False
    pkg_info['is_default_user_package'] = True
    pkg_info['is_system_package'] = False
    return pkg_info


def __initialize_default_user_package():
    if __get_usr_package_info_list():
        return

    usr_path = __get_usr_preset_path()
    pkg_info_dict = __get_default_user_package_dict()
    usr_package_path = os.path.join(usr_path, pkg_info_dict['identifier'])
    os.makedirs(usr_package_path)

    info_file_path = os.path.join(usr_package_path, "package.info")
    __write_dict_to_json(pkg_info_dict, info_file_path)


def __initialize_package_info_list():
    global PACKAGE_INFO_LIST
    PACKAGE_INFO_LIST = __get_package_info_list()


def __initialize_preset_info_list():
    global PRESET_INFO_LIST
    global CUSTOM_PRESET_ICONS
    global IS_CUSTOM_PRESET_ICONS_LOADED

    CUSTOM_PRESET_ICONS.clear()
    PRESET_INFO_LIST = __get_preset_info_list()
    IS_CUSTOM_PRESET_ICONS_LOADED = True


def __get_sys_package_info_list():
    package_info_list = get_package_info_list()
    sys_info_list = []
    for info in package_info_list:
        if info['is_system_package']:
            sys_info_list.append(dict(info))
    return sys_info_list


def __get_usr_package_info_list():
    package_info_list = get_package_info_list()
    usr_info_list = []
    for info in package_info_list:
        if not info['is_system_package']:
            usr_info_list.append(dict(info))
    return usr_info_list


def __sort_package_info_list(info_list):
    sys_list = []
    usr_list = []
    usr_default_list = []
    for info in info_list:
        if info['is_system_package']:
            sys_list.append(info)
        else:
            if info['is_default_user_package']:
                usr_default_list.append(info)
            else:
                usr_list.append(info)

    sys_list = sorted(sys_list, key=lambda k: str.lower(k['name']), reverse=True)
    usr_default_list = sorted(usr_default_list, key=lambda k: str.lower(k['name']), reverse=True)
    usr_list = sorted(usr_list, key=lambda k: str.lower(k['name']), reverse=True)
    return usr_list + usr_default_list + sys_list

def __sort_preset_info_list(info_list):
    sorted_list = sorted(info_list, key=lambda k: str.lower(k['name']), reverse=True)
    return sorted_list


def __clear_collection_property(collection):
    num_items = len(collection)
    for i in range(num_items):
        collection.remove(0)


def __get_package_info_list_from_path(path):
    info_list = []
    for name in os.listdir(path):
        dirpath = os.path.join(path, name)
        if os.path.isdir(dirpath):
            info_filepath = os.path.join(dirpath, "package.info")
            if os.path.isfile(info_filepath):
                with open(info_filepath, 'r', encoding='utf-8') as f:
                    try:
                        package_info = json.loads(f.read())
                        package_info["path"] = dirpath
                        info_list.append(package_info)
                    except:
                        print("Error decoding package info file: <" + info_filepath + ">")
    return info_list


def __get_package_info_list():
    sys_info_list = __get_package_info_list_from_path(__get_sys_preset_path())
    usr_info_list = __get_package_info_list_from_path(__get_usr_preset_path())
    return sys_info_list + usr_info_list


def __get_preset_info_list_from_path(path):
    global CUSTOM_PRESET_ICONS

    info_list = []
    for item in os.listdir(path):
        package_directory = os.path.join(path, item)
        if not os.path.isdir(package_directory):
            continue

        package_info_filepath = os.path.join(package_directory, "package.info")
        if not os.path.isfile(package_info_filepath):
            continue

        with open(package_info_filepath, 'r', encoding='utf-8') as f:
            try:
                package_info = json.loads(f.read())
            except:
                print("Error decoding package info file: <" + info_filepath + ">")
                continue

        package_id = package_info["identifier"]
        use_icons = package_info["use_custom_icons"]
        for preset_item in os.listdir(package_directory):
            preset_directory = os.path.join(package_directory, preset_item)
            if not os.path.isdir(preset_directory):
                continue

            preset_info_filepath = os.path.join(preset_directory, "data.preset")
            if not os.path.isfile(preset_info_filepath):
                continue

            with open(preset_info_filepath, 'r', encoding='utf-8') as f:
                try:
                    preset_info = json.loads(f.read())
                except:
                    print("Error decoding preset info file: <" + preset_info_filepath + ">")
                    continue

            preset_info["path"] = preset_directory
            preset_info["package"] = package_id
            if use_icons:
                if preset_info["identifier"] in CUSTOM_PRESET_ICONS:
                    preset_info["icon"] = preset_info["identifier"]
                else:
                    icon_path = os.path.join(preset_directory, "icon.png")
                    if os.path.isfile(icon_path):
                        CUSTOM_PRESET_ICONS.load(preset_info["identifier"], icon_path, 'IMAGE')
                        preset_info["icon"] = preset_info["identifier"]
                    else:
                        print("Error missing icon file for preset: <" + preset_info['name'] + ">")
            info_list.append(preset_info)

            material_blend_path = os.path.join(preset_directory, "materials.blend")
            if os.path.isfile(material_blend_path):
                preset_info['material_blend'] = material_blend_path


    return info_list


def __get_preset_info_list():
    sys_info_list = __get_preset_info_list_from_path(__get_sys_preset_path())
    usr_info_list = __get_preset_info_list_from_path(__get_usr_preset_path())
    return sys_info_list + usr_info_list


def __get_package_identifiers():
    info_list = __get_package_info_list()
    identifier_list = []
    for info in info_list:
        identifier_list.append(info['identifier'])
    return identifier_list


def __get_preset_identifiers():
    info_list = __get_preset_info_list()
    identifier_list = []
    for info in info_list:
        identifier_list.append(info['identifier'])
    return identifier_list


def __name_to_unique_identifier(name, identifier_list):
    max_base_len = 31
    rand_hex_len = 8

    id_dict = {key: key for key in identifier_list}
    identifier_base = name.strip().replace(' ', '_')
    identifier_base = re.sub(r'[^\sa-zA-Z0-9_]', '', identifier_base).lower()
    if not identifier_base:
        identifier_base = "default_identifier"
    identifier_base = identifier_base[:max_base_len]

    max_tries = 100
    final_identifier = None
    for n in range(max_tries):
        rand_str = binascii.b2a_hex(os.urandom(rand_hex_len//2)).decode("utf-8")
        identifier = identifier_base + "_" + rand_str
        if identifier not in id_dict:
            final_identifier = identifier
            break
    return final_identifier


def __generate_package_uid():
    min_uid = 100          # 0-99 are reserved for system packages
    max_uid = 10000000     # Blender enum property seems to have trouble with
                           # larger id values
    return random.SystemRandom().randint(min_uid, max_uid)


def __generate_preset_uid():
    min_uid = 1000         # 0-999 are reserved for system packages
    max_uid = 10000000     # Blender enum property seems to have trouble with
                           # larger id values
    return random.SystemRandom().randint(min_uid, max_uid)


def register():
    global CUSTOM_PRESET_ICONS
    CUSTOM_PRESET_ICONS = bpy.utils.previews.new()


def unregister():
    global CUSTOM_PRESET_ICONS
    bpy.utils.previews.remove(CUSTOM_PRESET_ICONS)
