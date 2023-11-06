# Blender FLIP Fluids Add-on
# Copyright (C) 2023 Ryan L. Guy
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

import bpy, os, pathlib

from ..utils import installation_utils


__EXTENSION_WHITELIST = [
    ".backup",
    ".bat",
    ".bbox",
    ".bin",
    ".blend",
    ".bobj",
    ".cpp",
    ".data",
    ".ffd",
    ".ffp3",
    ".fpd",
    ".h",
    ".info",
    ".json",
    ".md",
    ".png",
    ".preset",
    ".sim",
    ".sqlite3",
    ".state",
    ".txt",
    ".txt~",
    ".wwi",
    ".wwf",
    ".wwp"
    ]

# These extensions are not allowed to be mass-deleted within a directory
__DELETE_DIRECTORY_EXTENSION_BLACKLIST = [
    ".blend"
    ]


class FilesystemProtectionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def get_extension_whitelist():
    global __EXTENSION_WHITELIST
    return __EXTENSION_WHITELIST


def get_delete_directory_extension_blacklist():
    global __DELETE_DIRECTORY_EXTENSION_BLACKLIST
    return __DELETE_DIRECTORY_EXTENSION_BLACKLIST


def get_directory_whitelist():
    whitelist = []
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if dprops is not None:
        whitelist.append(dprops.cache.get_cache_abspath())

    this_filepath = os.path.realpath(__file__)
    addon_filepath = os.path.dirname(os.path.dirname(this_filepath))
    whitelist.append(addon_filepath)

    preset_library_installations = installation_utils.get_preset_library_installations()
    for install in preset_library_installations:
        whitelist.append(install["path"])

    return whitelist


def path_is_parent(parent_path, child_path):
    parent_path = os.path.abspath(parent_path)
    child_path = os.path.abspath(child_path)
    try:
        parent_child_commonpath = os.path.commonpath([parent_path, child_path])
    except ValueError:
        # paths not on same drive
        return False
    return os.path.commonpath([parent_path]) == parent_child_commonpath


def check_extensions_valid(extensions):
    extension_whitelist = get_extension_whitelist()
    bad_extensions = []
    for ext in extensions:
        if ext not in extension_whitelist:
            bad_extensions.append(ext)

    if bad_extensions:
        error_msg = "Extension not in whitelist: "
        for ext in bad_extensions:
            error_msg += "<" + ext + "> "
        error_msg += "***Please contact the developers with this error message***"
        raise FilesystemProtectionError(error_msg)


def check_directory_valid(base_directory):
    directory_whitelist = get_directory_whitelist()
    is_safe_sub_directory = False
    for d in directory_whitelist:
        if path_is_parent(d, base_directory):
            is_safe_sub_directory = True
            break

    if not is_safe_sub_directory:
        error_msg = "Directory is not in whitelist: <" + base_directory + "> Whitelist: "
        for d in directory_whitelist:
            error_msg += "<" + d + "> "
        error_msg += "***Please contact the developers with this error message***"
        raise FilesystemProtectionError(error_msg)


def delete_files_in_directory(base_directory, extensions, remove_directory=False):
    extension_blacklist = get_delete_directory_extension_blacklist()
    for ext in extension_blacklist:
        if ext in extensions:
            error_msg = "Extension in directory deletion blacklist: "
            error_msg += "<" + ext + "> "
            error_msg += "***Please contact the developers with this error message***"
            raise FilesystemProtectionError(error_msg)

    check_extensions_valid(extensions)
    check_directory_valid(base_directory)

    if not os.path.isdir(base_directory):
        return

    file_list = [f for f in os.listdir(base_directory) if os.path.isfile(os.path.join(base_directory, f))]
    valid_filepaths = []
    for f in file_list:
        if pathlib.Path(f).suffix in extensions:
            valid_filepaths.append(os.path.join(base_directory, f))

    remove_error_count = 0
    first_error = None
    for f in valid_filepaths:
        try:
            os.remove(f)
        except OSError as e:
            remove_error_count += 1
            if first_error is None:
                first_error = str(e)

    if remove_directory and not os.listdir(base_directory):
        try:
            os.rmdir(base_directory)
        except OSError as e:
            remove_error_count += 1
            if first_error is None:
                first_error = str(e)

    if remove_error_count > 0:
        errmsg = "Error encountered attempting to remove " + str(remove_error_count) + " file(s). Reason: <" + first_error + ">. "
        errmsg += "Try closing all applications accessing the directory, restarting Blender/System, or deleting directory manually."
        bpy.ops.flip_fluid_operators.display_error(
                'INVOKE_DEFAULT',
                error_message="Error Removing Files",
                error_description=errmsg,
                popup_width=700
                )


def delete_file(filepath, error_ok=False):
    if not os.path.isfile(filepath):
        return

    extension = pathlib.Path(filepath).suffix
    check_extensions_valid([extension])
    check_directory_valid(filepath)

    try:
        os.remove(filepath)
    except Exception as e:
        if error_ok:
            pass
        else:
            errmsg = "Error encountered attempting to remove file. Reason: <" + str(e) + ">."
            bpy.ops.flip_fluid_operators.display_error(
                    'INVOKE_DEFAULT',
                    error_message="Error Removing Files",
                    error_description=errmsg,
                    popup_width=700
                    )


def clear_cache_directory(cache_directory, clear_export=False, clear_logs=False, remove_directory=False):
    stats_filepath = os.path.join(cache_directory, "flipstats.data")
    delete_file(stats_filepath)

    bakefiles_dir = os.path.join(cache_directory, "bakefiles")
    extensions = [".bbox", ".bobj", ".data", ".wwp", ".wwf", ".wwi", ".fpd", ".ffd", ".ffp3"]
    delete_files_in_directory(bakefiles_dir, extensions, remove_directory=True)

    temp_dir = os.path.join(cache_directory, "temp")
    extensions = [".data"]
    delete_files_in_directory(temp_dir, extensions, remove_directory=True)

    scripts_dir = os.path.join(cache_directory, "scripts")
    extensions = [".bat"]
    delete_files_in_directory(scripts_dir, extensions, remove_directory=True)

    savestates_dir = os.path.join(cache_directory, "savestates")
    if os.path.isdir(savestates_dir):
        extensions = [".data", ".state", ".backup"]
        savestate_subdirs = [d for d in os.listdir(savestates_dir) if os.path.isdir(os.path.join(savestates_dir, d))]
        for subd in savestate_subdirs:
            if subd.startswith("autosave"):
                dirpath = os.path.join(savestates_dir, subd)
                delete_files_in_directory(dirpath, extensions, remove_directory=True)
        delete_files_in_directory(savestates_dir, [], remove_directory=True)

    if clear_export:
        export_dir = os.path.join(cache_directory, "export")
        if os.path.isdir(export_dir):
            extensions = [".sqlite3", ".sim"]
            delete_files_in_directory(export_dir, extensions, remove_directory=True)

    if clear_logs:
        logs_dir = os.path.join(cache_directory, "logs")
        if os.path.isdir(logs_dir):
            extensions = [".txt"]
            delete_files_in_directory(logs_dir, extensions, remove_directory=True)

    if remove_directory and not os.listdir(cache_directory):
        os.rmdir(cache_directory)