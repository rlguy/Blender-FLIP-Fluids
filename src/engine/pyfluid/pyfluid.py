# MIT License
# 
# Copyright (C) 2021 Ryan L. Guy
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
        libdir = os.path.join(os.path.dirname(__file__), "lib")

        system = platform.system()
        if system == "Windows":
            libname_debug = "libblpyfluiddebug.dll"
            libname_release = "libblpyfluidrelease.dll"
        elif system == "Darwin":
            libname_debug = "libblpyfluiddebug.dylib"
            libname_release = "libblpyfluidrelease.dylib"
        elif system == "Linux":
            libname_debug = "libblpyfluiddebug.so"
            libname_release = "libblpyfluidrelease.so"
        else:
            raise LibraryLoadError("Unable to recognize system: " + system)

        libfile_debug = os.path.join(libdir, libname_debug)
        libfile_release = os.path.join(libdir, libname_release)

        library_files = [libfile_debug, libfile_release]
        missing_libraries = []
        for lib in library_files:
            if not os.path.isfile(lib):
                missing_libraries.append(os.path.basename(lib))

        if missing_libraries:
            err_msg = "Cannot find fluid engine libraries: "
            for libname in missing_libraries:
                err_msg += "<" + libname + "> "
            raise LibraryLoadError(err_msg)

        global DEBUG_MODE_ENABLED
        global IS_DEBUG_MODE_LIBRARY_LOADED

        if DEBUG_MODE_ENABLED:
            libfile = libfile_debug
        else:
            libfile = libfile_release

        try:
            library = ctypes.cdll.LoadLibrary(libfile)
            IS_DEBUG_MODE_LIBRARY_LOADED = DEBUG_MODE_ENABLED
        except:
            msg = "Unable to load fluid engine library: <" + libfile + ">"
            msg += " (1) Make sure that you are using a 64-bit version of Python/Blender"
            msg += " if built for 64-bit and likewise if built for 32-bit."
            msg += " (2) Try clearing your Blender user settings (make a backup first!)."
            msg += " (3) Contact the developers if you think that this is an error."
            raise LibraryLoadError(msg)

        return library


pyfluid = PyFluidLib()
