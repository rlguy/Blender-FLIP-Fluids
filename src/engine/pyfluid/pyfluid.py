# MIT License
# 
# Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ctypes
import os
import platform

DEBUG_MODE_ENABLED = False
IS_DEBUG_MODE_LIBRARY_LOADED = False

def enable_debug_mode():
    global DEBUG_MODE_ENABLED
    DEBUG_MODE_ENABLED = True


def disable_debug_mode():
    global DEBUG_MODE_ENABLED
    DEBUG_MODE_ENABLED = False


class LibraryLoadError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# The PyFluidLib class loads the FLIP Fluids addon simulation engine. The engine
# is a dynamic library which contains methods to process simulation calculations.
# The simulation engine is written in C and C++ and is controlled through Python
# using the built-in ctypes module (https://docs.python.org/3/library/ctypes.html).
#
# The files in src/engine/pyfluid contain Python bindings for the fluid simulation
# objects and methods. The Python bindings use ctypes to call corresponding C bindings
# found in src/engine/c_bindings. The C bindings call C++ methods found in src/engine.
#
# To begin following how the simulator is run from Python to C to C++, refer to the 
# baking script located at src/addon/bake.py starting at the bake(...) method. The
# arguments passed to bake(...) are generated and formed in the addon within the Bake
# Operators found in src/addon/operators/bake_operators.py as well as the Export
# Operators found in src/addon/operators/export_operators.py.
class PyFluidLib():
    def __init__(self):
        self._lib = None

    def __getattr__(self, name):
        global DEBUG_MODE_ENABLED
        global IS_DEBUG_MODE_LIBRARY_LOADED

        if self.__dict__['_lib'] is None:
            self._lib = self._load_library("pyfluid")
        elif DEBUG_MODE_ENABLED != IS_DEBUG_MODE_LIBRARY_LOADED:
            self._lib = self._load_library("pyfluid")

        return getattr(self._lib, name)

    def _load_library(self, name):
        libname_debug_prefix = "libblpyfluiddebug"
        libname_release_prefix = "libblpyfluidrelease"

        system = platform.system()
        if system == "Windows":
            library_extension = ".dll"
        elif system == "Darwin":
            library_extension = ".dylib"
        elif system == "Linux":
            library_extension = ".so"
        else:
            raise LibraryLoadError("Unable to recognize system: " + system)

        libdir = os.path.join(os.path.dirname(__file__), "lib")
        libnames= [f for f in os.listdir(libdir) if os.path.isfile(os.path.join(libdir, f))]
        libnames_debug = [n for n in libnames if n.startswith(libname_debug_prefix) and n.endswith(library_extension)]
        libnames_release = [n for n in libnames if n.startswith(libname_release_prefix) and n.endswith(library_extension)]

        # Sorting the library names by length is not necessary, but sorting from
        # longest name to shortest will bypass a possible user-error if the user does not
        # completely remove the previous installation before installing a new version.
        # A version update required a possible increase in the length of the library
        # name. This sort will ensure that the longer library name (newer version) 
        # is used before the shorter named file (older version) that could remain 
        # from an incorrect install or compile process.
        libnames_debug.sort(key=len, reverse=True)
        libnames_release.sort(key=len, reverse=True)

        libpaths_debug = [os.path.join(libdir, n) for n in libnames_debug]
        libpaths_release = [os.path.join(libdir, n) for n in libnames_release]

        # The addon requires both functioning release and debug library versions
        # for full functionality. Refer to the build instructions for building
        # both of these library versions: https://github.com/rlguy/Blender-FLIP-Fluids#building
        missing_libraries = []
        if not libpaths_debug:
            missing_libraries.append(libname_debug_prefix + library_extension)
        if not libpaths_release:
            missing_libraries.append(libname_release_prefix + library_extension)

        if missing_libraries:
            err_msg = "Cannot find fluid engine libraries: "
            for libname in missing_libraries:
                err_msg += "<" + libname + "> "
            raise LibraryLoadError(err_msg)

        global DEBUG_MODE_ENABLED
        global IS_DEBUG_MODE_LIBRARY_LOADED

        if DEBUG_MODE_ENABLED:
            libpaths = libpaths_debug
        else:
            libpaths = libpaths_release

        # The addon may be packaged with multiple versions of a library for the OS, not
        # all of which may be compatible with the specific OS version. Choose the first 
        # library that loads without error.
        # Refer to the LIBRARY_SUFFIX variable in the cmakelists.txt file for generating a
        # library with a suffix added to the name.
        loaded_library = None
        failed_libraries = []
        for libpath in libpaths:
            try:
                loaded_library = ctypes.cdll.LoadLibrary(libpath)
                IS_DEBUG_MODE_LIBRARY_LOADED = DEBUG_MODE_ENABLED
                break
            except:
                failed_libraries.append(libpath)
                loaded_library = None
                pass

        # Additional notes on the error message:
        # (1) Blender 2.80 and later are 64-bit and require a library that has been
        #     built as 64-bit. Make sure you are using a 64-bit compiler for these versions.
        #     Blender 2.79 distributes both 32-bit and 64-bit versions, so make sure your
        #     your compiler matches the target version of Blender 2.79.
        # (2) This resolves possible errors due to incorrect installation of the addon and
        #     possible conflicts between Blender versions (such as multiple daily builds).
        #     Refer to this document for addon installation troubleshooting:
        #         https://github.com/rlguy/Blender-FLIP-Fluids/wiki/Addon-Installation-Troubleshooting
        if loaded_library is None:
            failed_libraries_string = ""
            for libpath in failed_libraries:
                failed_libraries_string += "<" + libpath + "> "

            msg = "Unable to load fluid engine libraries: " + failed_libraries_string
            msg += " (1) Make sure that you are using a 64-bit version of Python/Blender"
            msg += " if built for 64-bit and likewise if built for 32-bit."
            msg += " (2) Try clearing your Blender user settings (make a backup first!)."
            raise LibraryLoadError(msg)

        return loaded_library


pyfluid = PyFluidLib()