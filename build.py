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

import os, shutil, subprocess, platform, argparse


def cmake_make(cmakelists_dir, cmake_path, make_path, build_debug=True, make_build=True, darwin_arch=""):
    if build_debug:
        build_debug_flag = "-DBUILD_DEBUG=ON"
    else:
        build_debug_flag = "-DBUILD_DEBUG=OFF"

    system = platform.system()
    if system == "Windows":
        cmake_command = [cmake_path, cmakelists_dir, "-G", "MinGW Makefiles", build_debug_flag]
    elif system == "Darwin":
        cmake_command = [cmake_path, cmakelists_dir, build_debug_flag]
        if darwin_arch:
            cmake_command.append("-DCMAKE_OSX_ARCHITECTURES=" + darwin_arch)
    elif system == "Linux":
        cmake_command = [cmake_path, cmakelists_dir, build_debug_flag]

    subprocess.check_call(cmake_command)

    if make_build:
        make_command = [make_path]
        subprocess.check_call(make_command)


def clean_build_directory(build_dir):
    items = [
        "bl_flip_fluids",
        "CMakeFiles",
        "cmake_install.cmake",
        "CMakeCache.txt",
        "Makefile"
    ]

    for item in items:
        item_path = os.path.join(build_dir, item)
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            if os.path.isfile(item_path):
                os.remove(item_path)


def process_path(p):
    p = os.path.expanduser(p)
    p = os.path.normpath(p)
    p = os.path.realpath(p)
    p = os.path.abspath(p)
    return p


def main():
    parser = argparse.ArgumentParser(description="FLIP Fluids Addon build and compile script")
    parser.add_argument("-build-directory", help="Path to destination build directory")
    parser.add_argument("-darwin-arch", help="Target architecture to set for CMAKE_OSX_ARCHITECTURES")
    parser.add_argument("-cmake-path", help="Specify path to CMake binary (www.cmake.org)")
    parser.add_argument("-make-path", help="Specify path to GNU Make binary (www.gnu.org/software/make)")
    parser.add_argument('--clean', action="store_true", help="Clear generated files in the build directory before building")
    parser.add_argument('-no-compile', action="store_true", help="Do not compile libraries")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(root_dir, "build")
    if args.build_directory:
        build_dir = process_path(args.build_directory)

    darwin_arch = ""
    if args.darwin_arch:
        darwin_arch = args.darwin_arch

    cmake_path = "cmake"
    if args.cmake_path:
        cmake_path = process_path(args.cmake_path)
        if not os.path.isfile(cmake_path):
            print("\n***ERROR: Could not find file: <" + cmake_path + ">***\n")
            return
    else:
        if shutil.which(cmake_path) is None:
            parser.print_help()
            print("\n***ERROR: Could not find CMake (cmake) on your system path. See above for help.***\n")
            return

    make_path = "make"
    if args.make_path:
        make_path = process_path(args.make_path)
        if not os.path.isfile(make_path):
            print("\n***ERROR: Could not find file: <" + make_path + ">***\n")
            return
    else:
        if shutil.which(make_path) is None:
            parser.print_help()
            print("\n***ERROR: Could not find GNU Make (make) on your system path. See above for help.***\n")
            return

    try:
        original_cwd = os.getcwd()
        cmakelists_file = os.path.join(root_dir, "cmake", "CMakeLists.txt")
        temp_cmakelists_file = os.path.join(root_dir, "CMakeLists.txt")

        shutil.copyfile(cmakelists_file, temp_cmakelists_file)
        os.makedirs(build_dir, exist_ok=True)
        os.chdir(build_dir)

        if args.clean:
            clean_build_directory(build_dir)

        cmake_make(root_dir, cmake_path, make_path, build_debug=True, make_build=not args.no_compile, darwin_arch=darwin_arch)
        cmake_make(root_dir, cmake_path, make_path, build_debug=False, make_build=not args.no_compile, darwin_arch=darwin_arch)

        lib_dir = os.path.join(build_dir, "bl_flip_fluids", "flip_fluids_addon", "pyfluid", "lib")
        if os.path.isdir(lib_dir):
            for filename in os.listdir(lib_dir):
                if filename.endswith(".dll.a"):
                    os.remove(os.path.join(lib_dir, filename))

    except Exception as e:
        if os.path.isfile(temp_cmakelists_file):
            os.remove(temp_cmakelists_file)
        os.chdir(original_cwd)
        raise e

    os.chdir(original_cwd)

    addon_dir = os.path.join(build_dir, "bl_flip_fluids", "flip_fluids_addon")
    print("\n" + "-"*80)
    print("FLIP Fluids addon successfully built and compiled to:")
    print("\t<" + addon_dir + ">")


if __name__ == "__main__":
    main()