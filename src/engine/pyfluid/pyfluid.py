# MIT License
# 
# Copyright (c) 2019 Ryan L. Guy
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

class LibraryLoadError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PyFluidLib():
    def __init__(self):
        self._lib = None

    def __getattr__(self, name):
        if self.__dict__['_lib'] is None:
            self._lib = self._load_library("pyfluid")
        return getattr(self._lib, name)

    def _load_library(self, name):
        libdir = os.path.join(os.path.dirname(__file__), "lib")

        system = platform.system()
        if system == "Windows":
            libname = "libblpyfluid.dll"
        elif system == "Darwin":
            libname = "libblpyfluid.dylib"
        elif system == "Linux":
            libname = "libblpyfluid.so"
        else:
            raise LibraryLoadError("Unable to recognize system: " + system)

        libfile = os.path.join(libdir, libname)
        if not os.path.isfile(libfile):
            raise LibraryLoadError("Cannot find fluid engine library: " + libname)

        try:
            library = ctypes.cdll.LoadLibrary(libfile)
        except:
            msg = "Unable to load fluid engine library: <" + libname + ">"
            msg += " (1) Make sure that you are using a 64-bit version of Python/Blender"
            msg += " if built for 64-bit and likewise if built for 32-bit."
            msg += " (2) Try clearing your Blender user settings (make a backup first!)."
            msg += " (3) Contact the developers if you think that this is an error."
            raise LibraryLoadError(msg)

        return library


pyfluid = PyFluidLib()