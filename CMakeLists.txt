#[[
MIT License

Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
]]

cmake_minimum_required(VERSION 3.5...4.2.0)

function(set_output_directories DIR)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${DIR} PARENT_SCOPE)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${DIR} PARENT_SCOPE)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${DIR} PARENT_SCOPE)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${DIR} PARENT_SCOPE)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${DIR} PARENT_SCOPE)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${DIR} PARENT_SCOPE)
endfunction(set_output_directories)

include(CheckLinkerFlag)

# Build Options
set(BUILD_DEBUG OFF CACHE BOOL "Turn on to build a debug release")
option(DISTRIBUTE_SOURCE "Include source code in addon" ON)
option(WITH_MIXBOX "Compile with Mixbox pigment mixing feature" OFF)

# Configure Project
project(bl_flip_fluids)
set(CMAKE_BUILD_TYPE Release)

if(APPLE)
    set(MACOSX_DEPLOYMENT_TARGET 10.10) # OS X Yosemite
endif()

# Set Version Info
set(FFENGINE_VERSION_TYPE_IS_STABLE_BUILD TRUE)
set(FFENGINE_VERSION_MAJOR 1)
set(FFENGINE_VERSION_MINOR 8)
set(FFENGINE_VERSION_REVISION 5)
set(FFENGINE_VERSION_DATE_YYYY "2025")
set(FFENGINE_VERSION_DATE_MM "11")
set(FFENGINE_VERSION_DATE_DD "18")
set(FFENGINE_VERSION_SUPPORT_LICENSE_TYPE "GitHub")
set(FFENGINE_VERSION_RELEASE_TYPE "Release")

# Format Version Info
if(FFENGINE_VERSION_TYPE_IS_STABLE_BUILD)
    if(FFENGINE_VERSION_IS_FULL_RELEASE)
    else()
    endif()
    set(FFENGINE_VERSION_TYPE_LABEL ${FFENGINE_VERSION_RELEASE_TYPE})
    set(FFENGINE_VERSION_TYPE_IS_STABLE_BUILD_PYTHON "True")
else()
    set(FFENGINE_VERSION_TYPE_LABEL "Experimental")
    set(FFENGINE_VERSION_TYPE_IS_STABLE_BUILD_PYTHON "False")
endif()

set(FFENGINE_VERSION_DATE "${FFENGINE_VERSION_DATE_YYYY}-${FFENGINE_VERSION_DATE_MM}-${FFENGINE_VERSION_DATE_DD}")
set(FFENGINE_VERSION_LABEL "\
${FFENGINE_VERSION_MAJOR}.${FFENGINE_VERSION_MINOR}.${FFENGINE_VERSION_REVISION} \
${FFENGINE_VERSION_SUPPORT_LICENSE_TYPE} \
${FFENGINE_VERSION_TYPE_LABEL} \
${FFENGINE_VERSION_DATE}\
")

string(RANDOM LENGTH 1 ALPHABET "123456789" RANDOM_DIGITS_1)
string(RANDOM LENGTH 2 ALPHABET "0123456789" RANDOM_DIGITS_2)
string(RANDOM LENGTH 1 ALPHABET "ABCEGJKLMNPRTVXY" RANDOM_LETTERS_1)
string(RANDOM LENGTH 1 ALPHABET "ABCEGJKLMNPRTVWXYZ" RANDOM_LETTERS_2)
set(FFENGINE_VERSION_SUPPORT_LICENSE_ID "${RANDOM_DIGITS_1}${RANDOM_DIGITS_2}${RANDOM_LETTERS_1}${RANDOM_LETTERS_2}")

# Begin Build
message(STATUS "FLIP Fluids Version ${FFENGINE_VERSION_LABEL}")
if(BUILD_DEBUG)
    message(STATUS "Building in debug mode")
else()
    message(STATUS "Building in release mode")
endif()

# Configure Mixbox
if(WITH_MIXBOX)
    set(FFENGINE_IS_MIXBOX_SUPPORTED "True")
    add_definitions(-DWITH_MIXBOX=1)
    set(MIXBOX_SOURCE_CPP "src/engine/mixbox/mixbox.cpp")
else()
    set(FFENGINE_IS_MIXBOX_SUPPORTED "False")
    add_definitions(-DWITH_MIXBOX=0)
    set(MIXBOX_SOURCE_CPP "src/engine/mixbox/mixbox_stub.cpp")
endif()

# Configure Compiler/OS Specific Flags
if(MSVC)
    message(FATAL_ERROR "Error: Compilation using MSVC (Microsoft Visual Studio) is not supported. Building with MSVC will result in errors, performance issues, and broken simulation features. Change this FATAL_ERROR to WARNING in the CMake script to continue at your own risk.")
    add_definitions(-DNOMINMAX -D_CRT_SECURE_NO_WARNINGS)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /O2 /W4 /EHsc /wd4244")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} /LARGEADDRESSAWARE")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} /LARGEADDRESSAWARE")
elseif(MINGW)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static -static-libgcc -static-libstdc++ -fopenmp -O3 -std=c++17 -Wall")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,--enable-stdcall-fixup")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,--enable-stdcall-fixup")
elseif(APPLE)
    set(CMAKE_MACOSX_RPATH ON)
    set(CMAKE_SKIP_BUILD_RPATH FALSE)
    set(CMAKE_INSTALL_RPATH "@loader_path")
    set(CMAKE_BUILD_RPATH "@loader_path")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -std=c++17 -Wall -Wno-return-type-c-linkage")

    # Older compiler versions may not support or require -lstdc++fs linker flag
    check_linker_flag(CXX "-lstdc++fs" LINKER_SUPPORTS_FILESYSTEM)
    if(LINKER_SUPPORTS_FILESYSTEM)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -lstdc++fs")
    endif()
elseif(UNIX AND NOT APPLE)
    set(CMAKE_SKIP_BUILD_RPATH FALSE)
    set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
    set(CMAKE_INSTALL_RPATH "$ORIGIN")
    set(CMAKE_BUILD_RPATH "$ORIGIN")
    set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 -lstdc++fs -D_GLIBCXX_USE_NANOSLEEP -fopenmp -O3 -Wall -fPIC -pthread")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -include ${PROJECT_SOURCE_DIR}/src/engine/glibc_version_header/force_link_glibc_2.5.h")
else()
    message(FATAL_ERROR "Target OS/Compiler is not recognized.")
endif()

if(BUILD_DEBUG)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DBUILD_DEBUG")
endif()

# Write Compiler Info
set(COMPILER_DATA_DIRECTORY "${CMAKE_BINARY_DIR}/bl_flip_fluids/flip_fluids_addon/resources/compiler_data/")
set(COMPILER_DATA_FILENAME "${CMAKE_SYSTEM_NAME}_${CMAKE_CXX_COMPILER_ID}_${CMAKE_CXX_COMPILER_VERSION}.txt")
string(TIMESTAMP COMPILER_TIMSTAMP "%Y-%m-%d %H:%M:%S %z")
set(COMPILER_INFO "${CMAKE_SYSTEM_NAME} ${CMAKE_SYSTEM_VERSION} ${CMAKE_CXX_COMPILER} ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION} ${CMAKE_COMPILER_IS_GNUCXX} ${COMPILER_TIMSTAMP}")
file(WRITE "${COMPILER_DATA_DIRECTORY}/${COMPILER_DATA_FILENAME}" "${COMPILER_INFO}")

# Configure Files
configure_file(
  "${PROJECT_SOURCE_DIR}/src/engine/versionutils.cpp.in"
  "${PROJECT_SOURCE_DIR}/src/engine/versionutils.cpp"
)
configure_file(
  "${PROJECT_SOURCE_DIR}/src/addon/__init__.py.in"
  "${PROJECT_SOURCE_DIR}/src/addon/__init__.py"
)
configure_file(
  "${PROJECT_SOURCE_DIR}/src/addon/blender_manifest.toml.in"
  "${PROJECT_SOURCE_DIR}/src/addon/blender_manifest.toml"
)
configure_file(
  "${PROJECT_SOURCE_DIR}/src/addon/utils/installation_utils.py.in"
  "${PROJECT_SOURCE_DIR}/src/addon/utils/installation_utils.py"
)

# Sources
set(SOURCES_FLUID_ENGINE_LIBRARY
    src/engine/aabb.cpp
    src/engine/collision.cpp
    src/engine/diffuseparticlesimulation.cpp
    src/engine/fluidmaterialgrid.cpp
    src/engine/fluidsimulation.cpp
    src/engine/forcefield.cpp
    src/engine/forcefieldcurve.cpp
    src/engine/forcefieldgrid.cpp
    src/engine/forcefieldpoint.cpp
    src/engine/forcefieldsurface.cpp
    src/engine/forcefieldutils.cpp
    src/engine/forcefieldvolume.cpp
    src/engine/gridindexkeymap.cpp
    src/engine/gridindexvector.cpp
    src/engine/gridutils.cpp
    src/engine/influencegrid.cpp
    src/engine/interpolation.cpp
    src/engine/levelsetsolver.cpp
    src/engine/levelsetutils.cpp
    src/engine/logfile.cpp
    src/engine/macvelocityfield.cpp
    src/engine/meshfluidsource.cpp
    src/engine/meshlevelset.cpp
    src/engine/meshobject.cpp
    src/engine/meshutils.cpp
    src/engine/noisegenerationutils.cpp
    src/engine/particlelevelset.cpp
    src/engine/particlemaskgrid.cpp
    src/engine/particlemesher.cpp
    src/engine/particlesheeter.cpp
    src/engine/particlesystem.cpp
    src/engine/polygonizer3d.cpp
    src/engine/pressuresolver.cpp
    src/engine/scalarfield.cpp
    src/engine/spatialpointgrid.cpp
    src/engine/stopwatch.cpp
    src/engine/threadutils.cpp
    src/engine/trianglemesh.cpp
    src/engine/turbulencefield.cpp
    src/engine/velocityadvector.cpp
    src/engine/versionutils.cpp
    src/engine/viscositysolver.cpp
    src/engine/vmath.cpp
    src/engine/c_bindings/cbindings.cpp
    src/engine/c_bindings/fluidsimulation_c.cpp
    src/engine/c_bindings/forcefield_c.cpp
    src/engine/c_bindings/forcefieldcurve_c.cpp
    src/engine/c_bindings/forcefieldgrid_c.cpp
    src/engine/c_bindings/forcefieldpoint_c.cpp
    src/engine/c_bindings/forcefieldsurface_c.cpp
    src/engine/c_bindings/forcefieldvolume_c.cpp
    src/engine/c_bindings/meshfluidsource_c.cpp
    src/engine/c_bindings/meshobject_c.cpp
    src/engine/c_bindings/mixbox_c.cpp
    ${MIXBOX_SOURCE_CPP}
)

set(SOURCES_ALEMBIC_IO
    src/alembic_io/src/alembic_io.cpp
    src/alembic_io/src/c_bindings/alembic_io_c.cpp
)

set(SOURCES_ALEMBIC_IO_LIBRARY 
    ${SOURCES_FLUID_ENGINE_LIBRARY} 
    ${SOURCES_ALEMBIC_IO}
)

# Configure Output Directories
set(BLENDER_ADDON_DIR "${CMAKE_BINARY_DIR}/bl_flip_fluids/flip_fluids_addon")
set_output_directories("${BLENDER_ADDON_DIR}/ffengine/lib")

# Add Alembic Dependency
if(ALEMBIC_PACKAGE_ROOT)
    message(STATUS "Using ALEMBIC_PACKAGE_ROOT=" ${ALEMBIC_PACKAGE_ROOT})
    find_package(Alembic REQUIRED PATHS ${ALEMBIC_PACKAGE_ROOT} NO_DEFAULT_PATH)
else()
    find_package(Alembic REQUIRED)
endif()

# Alembic IO Engine Objects
file(GLOB ALEMBIC_IO_LIBRARY_SOURCES 
        "src/engine/*.cpp" 
        "src/engine/c_bindings/*.cpp"
        "src/alembic_io/src/alembic_io.cpp"
        "src/alembic_io/src/c_bindings/*.cpp" 
        ${MIXBOX_SOURCE_CPP}
        )

add_library(alembic_objects OBJECT ${ALEMBIC_IO_LIBRARY_SOURCES})
target_link_libraries(alembic_objects PRIVATE Alembic::Alembic)
target_compile_features(alembic_objects PRIVATE cxx_std_17)

# Alembic IO Engine Library
add_library(ffalembicengine SHARED $<TARGET_OBJECTS:alembic_objects>)
target_link_libraries(ffalembicengine PRIVATE Alembic::Alembic)

# FLIP Fluids Engine Objects
add_library(fluid_engine_objects OBJECT ${SOURCES_FLUID_ENGINE_LIBRARY})

# FLIP Fluids Engine Library
add_library(ffengine SHARED $<TARGET_OBJECTS:fluid_engine_objects>)

# Copy Libraries To Addon
file(COPY "${CMAKE_SOURCE_DIR}/src/addon/" DESTINATION "${BLENDER_ADDON_DIR}")
file(COPY "${CMAKE_SOURCE_DIR}/src/engine/ffengine/" DESTINATION "${BLENDER_ADDON_DIR}/ffengine")

# Package Sources
if(DISTRIBUTE_SOURCE)
    set(SOURCES_ARCHIVE_ROOT
        "${CMAKE_SOURCE_DIR}/.gitignore"
        "${CMAKE_SOURCE_DIR}/__init__.py"
        "${CMAKE_SOURCE_DIR}/build.py"
        "${CMAKE_SOURCE_DIR}/CMakeLists.txt"
        "${CMAKE_SOURCE_DIR}/LICENSE_GPLv3.md"
        "${CMAKE_SOURCE_DIR}/LICENSE_MIT.md"
        "${CMAKE_SOURCE_DIR}/LICENSE_Standard_Royalty_Free.md"
        "${CMAKE_SOURCE_DIR}/README.md"
    )

    file(GLOB_RECURSE SOURCES_ARCHIVE "${CMAKE_SOURCE_DIR}/src/*")
    list (APPEND SOURCES_ARCHIVE ${SOURCES_ARCHIVE_ROOT})
    file(MAKE_DIRECTORY ${BLENDER_ADDON_DIR}/source)
    file(ARCHIVE_CREATE OUTPUT "${BLENDER_ADDON_DIR}/source/flip_fluids_addon_source.zip" PATHS ${SOURCES_ARCHIVE} FORMAT "zip")
endif()