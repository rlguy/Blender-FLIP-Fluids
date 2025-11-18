/*
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
*/

#pragma once

#include <Alembic/Abc/All.h>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreOgawa/All.h>

#include <filesystem>
#include <vector>

#if __cpp_lib_filesystem
    namespace fs = std::filesystem;
#else
    // Older compiler versions may use experimental filesystem namespace
    namespace fs = std::__fs::filesystem;
#endif

struct MeshData {
    size_t num_vertices = 0;
    size_t num_faces = 0;
    std::vector<Imath::V3f> vertex_data;
    std::vector<int> face_data;
    std::vector<int> face_counts;
};

std::string get_current_time_string();
float random_range(float range_min, float range_max);
Imath::V3f convert_to_blender_coordinates(const Imath::V3f &pos);
void convert_to_blender_coordinates(std::vector<Imath::V3f> &vectors);
std::vector<Imath::V3f> offset_vertices(Alembic::Abc::float32_t *flat_vertices, size_t num_vertices, Imath::V3f offset);
void write_alembic_example();

void read_bobj(fs::path bobj_filepath, MeshData &mesh);
std::string zero_pad_int_to_string(int n, int width);
std::string format_seconds_to_MMSS(float total_seconds);
std::string get_time_elapsed_string(std::chrono::time_point<std::chrono::steady_clock> time_start);
void flip_fluids_cache_to_alembic(std::string config_json_string);