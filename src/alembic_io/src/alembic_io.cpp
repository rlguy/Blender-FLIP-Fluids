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

#include <Alembic/Abc/All.h>
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreOgawa/All.h>

#include <fstream>
#include <iostream>
#include <chrono>
#include <random>

#include "alembic_io.h"

const size_t g_num_verts = 8;
const Alembic::Abc::float32_t g_verts[] = { 
        -1.0f, -1.0f, -1.0f,
         1.0f, -1.0f, -1.0f,
        -1.0f,  1.0f, -1.0f,
         1.0f,  1.0f, -1.0f,
        -1.0f, -1.0f,  1.0f,
         1.0f, -1.0f,  1.0f,
        -1.0f,  1.0f,  1.0f,
         2.0f,  2.0f,  2.0f 
        };

const size_t g_num_indices = 24;
const Alembic::Abc::int32_t g_indices[] = {
        // LEFT
        0, 4, 6, 2,
        // RIGHT
        5, 1, 3, 7,
        // BOTTOM
        0, 1, 5, 4,
        // TOP,
        6, 7, 3, 2,
        // BACK
        1, 0, 2, 3,
        // FRONT
        4, 5, 7, 6 
        };

// "Face Counts" - number of vertices in each face.
const size_t g_num_counts = 6;
//const size_t g_num_face_corners = 4;
const Alembic::Abc::int32_t g_counts[] = {4, 4, 4, 4, 4, 4};

const size_t g_num_faces = 6;
const std::vector<Alembic::AbcGeom::C4f> g_face_colors = {
    Alembic::AbcGeom::C4f(1.0f, 0.0f, 0.0f, 1.0f),  // Front face - Red
    Alembic::AbcGeom::C4f(0.0f, 1.0f, 0.0f, 1.0f),  // Back face - Green  
    Alembic::AbcGeom::C4f(0.0f, 0.0f, 1.0f, 1.0f),  // Left face - Blue
    Alembic::AbcGeom::C4f(1.0f, 1.0f, 0.0f, 1.0f),  // Right face - Yellow
    Alembic::AbcGeom::C4f(1.0f, 0.0f, 1.0f, 1.0f),  // Bottom face - Magenta
    Alembic::AbcGeom::C4f(0.0f, 1.0f, 1.0f, 1.0f)   // Top face - Cyan
};

std::random_device random_device;
std::mt19937 random_generator(random_device());


std::string get_current_time_string()
{
    std::chrono::time_point<std::chrono::system_clock> clock_now = std::chrono::system_clock::now();
    time_t time_now = std::chrono::system_clock::to_time_t(clock_now);
    struct tm *gmt_time = gmtime(&time_now);

    std::stringstream sstream;
    sstream << std::put_time(gmt_time, "%Y-%m-%d %H:%M:%S");

    return sstream.str();
}


float random_range(float range_min, float range_max)
{
    std::uniform_real_distribution<> random_distribution(range_min, range_max);
    return random_distribution(random_generator);
}


Imath::V3f convert_to_blender_coordinates(const Imath::V3f &v)
{
    return Imath::V3f(v.x, v.z, -v.y);
}


void convert_to_blender_coordinates(std::vector<Imath::V3f> &vectors)
{
    for (size_t i = 0; i < vectors.size(); i++) {
        vectors[i] = convert_to_blender_coordinates(vectors[i]);
    }
}


std::vector<Imath::V3f> offset_vertices(const Alembic::Abc::float32_t *flat_vertices, const size_t num_vertices, const Imath::V3f offset)
{
    std::vector<Imath::V3f> vertices;
    vertices.reserve(num_vertices);
    for (size_t i = 0; i < num_vertices; i++) {
        Imath::V3f vertex(
            flat_vertices[3*i + 0] + offset[0],
            flat_vertices[3*i + 1] + offset[1],
            flat_vertices[3*i + 2] + offset[2]
            );
        vertices.push_back(vertex);
    }
    return vertices;
}


void write_alembic_example()
{
    fs::path output_directory(U"C:/path/to/output/directory");
    fs::create_directories(output_directory);
    
    fs::path filename(U"poly_mesh_out.abc");
    fs::path output_filepath = output_directory / filename;

    std::ofstream outfilestream;
    outfilestream.open(output_filepath, std::ios::out | std::ios::binary);

    // Frame rate and timing
    float frame_rate = 24.0f;
    float dt = 1.0f / frame_rate;
    int frame_start = 1;
    int frame_end = 24;
    float start_time = frame_start * dt;
    int num_frames = frame_end - frame_start + 1;
    Alembic::AbcGeom::TimeSampling *time_sampling = new Alembic::AbcGeom::TimeSampling(dt, start_time);
    Alembic::AbcGeom::TimeSamplingPtr time_sampling_ptr(time_sampling);

    // Create metadata
    Alembic::Abc::MetaData metadata_info;
    metadata_info.set(Alembic::Abc::kApplicationNameKey, "FLIP Fluids Addon - Alembic Exporter");
    metadata_info.set(Alembic::Abc::kDateWrittenKey ,    get_current_time_string());
    metadata_info.set(Alembic::Abc::kUserDescriptionKey, "Example Alembic Export");

    // Create archive writer
    Alembic::AbcCoreOgawa::WriteArchive archive_writer;
    Alembic::AbcCoreAbstract::ArchiveWriterPtr writer_ptr = archive_writer(&outfilestream, metadata_info);
    Alembic::AbcGeom::OArchive archive(writer_ptr);
    archive.addTimeSampling(*time_sampling_ptr);

    // Top of hierarchy
    Alembic::AbcGeom::OObject top_object(archive, Alembic::AbcGeom::kTop);

    // Create user data
    Alembic::Abc::OCompoundProperty user_metadata = top_object.getProperties();
    Alembic::Abc::OCompoundProperty archive_info(user_metadata,  "archive_info");
    Alembic::Abc::OStringProperty info_up_axis(archive_info,     "up_axis");
    Alembic::Abc::OStringProperty info_scene_units(archive_info, "scene_units");
    Alembic::Abc::OFloatProperty  info_frame_rate(archive_info,  "frame_rate");
    Alembic::Abc::OFloatProperty  info_start_time(archive_info,  "start_time");
    Alembic::Abc::OFloatProperty  info_end_time(archive_info,    "end_time");
    Alembic::Abc::OInt32Property  info_start_frame(archive_info, "start_frame");
    Alembic::Abc::OInt32Property  info_end_frame(archive_info,   "end_frame");

    info_up_axis.set("Z");
    info_scene_units.set("meters");
    info_frame_rate.set(frame_rate);
    info_start_time.set(start_time);
    info_end_time.set(start_time + num_frames * dt);
    info_start_frame.set(frame_start);
    info_end_frame.set(frame_end);

    // Create empty parent
    Alembic::AbcGeom::OXform empty_parent(top_object, "Empty");

    // Generate geometry and animation
    int num_cubes = 10;
    for (int object_idx = 0; object_idx < num_cubes; object_idx++) {

        // Initialize object schema
        std::string object_name = "Cube" + std::to_string(object_idx);
        Alembic::AbcGeom::OXform cube_transform(empty_parent, object_name);
        Alembic::AbcGeom::OPolyMesh cube_mesh(cube_transform, object_name);
        Alembic::AbcGeom::OPolyMeshSchema &cube_mesh_schema = cube_mesh.getSchema();
        cube_mesh_schema.setTimeSampling(time_sampling_ptr);

        Imath::V3f mesh_offset(
            random_range(-20.0f, 20.0f),
            random_range(-20.0f, 20.0f),
            random_range(-20.0f, 20.0f)
            );

        // Initialize vertex velocity attribute
        bool create_generic_velocity_attribute = true;
        bool create_builtin_velocity_attribute = true;
        Alembic::AbcGeom::OV3fGeomParam velocity_attribute;
        Alembic::AbcGeom::OCompoundProperty velocity_compound_property;
        if (create_generic_velocity_attribute) {
            velocity_compound_property = cube_mesh_schema.getArbGeomParams();
            velocity_attribute = Alembic::AbcGeom::OV3fGeomParam(
                velocity_compound_property, 
                "flip_velocity", false, Alembic::AbcGeom::kVertexScope, 1, 
                time_sampling_ptr
                );
        }

        Imath::V3f mesh_velocity(
                random_range(-30.0f, 30.0f),
                random_range(-30.0f, 30.0f),
                random_range(-30.0f, 30.0f)
                );

        // Initialize face corner color attribute
        Alembic::AbcGeom::OCompoundProperty color_compound_property = cube_mesh_schema.getArbGeomParams();
        Alembic::AbcGeom::OC4fGeomParam color_attribute(
            color_compound_property, 
            "color", true, Alembic::AbcGeom::kFacevaryingScope, 1, 
            time_sampling_ptr
            );

        // Initialize transform
        Imath::V3f transform_translation(
                random_range(-5.0f, 5.0f),
                random_range(-5.0f, 5.0f),
                random_range(-5.0f, 5.0f)
                );
        transform_translation = convert_to_blender_coordinates(transform_translation);

        for (int frameno = 0; frameno < num_frames; frameno++) {
            float current_time = frameno * dt;

            // Create geometry sample
            Imath::V3f total_offset = mesh_offset + mesh_velocity * current_time;
            std::vector<Imath::V3f> vertices = offset_vertices(g_verts, g_num_verts, total_offset);
            convert_to_blender_coordinates(vertices);

            Alembic::AbcGeom::OPolyMeshSchema::Sample mesh_sample(
                Alembic::Abc::V3fArraySample(vertices.data(), g_num_verts),
                Alembic::Abc::Int32ArraySample(g_indices, g_num_indices),
                Alembic::Abc::Int32ArraySample(g_counts, g_num_counts)
                );

            // Create vertex velocity attribute sample
            Imath::V3f transformed_mesh_velocity = convert_to_blender_coordinates(mesh_velocity);
            std::vector<Imath::V3f> velocities(g_num_verts, transformed_mesh_velocity);

            if (create_generic_velocity_attribute) {
                Alembic::AbcGeom::OV3fGeomParam::Sample velocity_sample(velocities, Alembic::AbcGeom::kVertexScope);
                velocity_attribute.set(velocity_sample);
            } 

            if (create_builtin_velocity_attribute) {
                Alembic::AbcGeom::V3fArraySample velocities_array(velocities);
                mesh_sample.setVelocities(velocities_array);
            }

            // Create face corner color attribute sample
            std::vector<Alembic::AbcGeom::C4f> face_corner_colors;
            std::vector<uint32_t> face_corner_color_indices;
            face_corner_colors.reserve(g_num_indices);
            face_corner_color_indices.reserve(g_num_indices);

            for (size_t face_idx = 0; face_idx < g_num_faces; face_idx++) {
                Alembic::AbcGeom::C4f base_color = g_face_colors[face_idx];

                float intensity = 0.5f + 0.5f * sin(current_time * 2.0f + face_idx * 0.5f);
                float alpha = 0.7f + 0.3f * cos(current_time * 1.5f + face_idx * 0.3f);

                for (int corner_idx = 0; corner_idx < 4; corner_idx++) {
                    float corner_phase = corner_idx * 0.25f * 3.14159f;
                    float corner_intensity = intensity + 0.2f * sin(current_time * 4.0f + corner_phase);
                    corner_intensity = std::max(0.1f, std::min(1.0f, corner_intensity));

                    Alembic::AbcGeom::C4f corner_color(
                        base_color.r * corner_intensity,
                        base_color.g * corner_intensity,
                        base_color.b * corner_intensity,
                        alpha
                        );

                    face_corner_colors.push_back(corner_color);
                    face_corner_color_indices.push_back(face_idx * 4 + corner_idx);
                }
            }

            Alembic::AbcGeom::OC4fGeomParam::Sample color_sample(
                Alembic::AbcGeom::C4fArraySample(face_corner_colors),
                Alembic::AbcGeom::UInt32ArraySample(face_corner_color_indices),
                Alembic::AbcGeom::kFacevaryingScope
                );
            color_attribute.set(color_sample);


            // Create transform sample
            Alembic::AbcGeom::OXformSchema& cube_transform_schema = cube_transform.getSchema();
            Alembic::AbcGeom::XformSample transform_sample;
            transform_sample.setTranslation(transform_translation);
            cube_transform_schema.set(transform_sample);

            // Set mesh sample
            cube_mesh_schema.set(mesh_sample);
        }

        std::cout << "Writing <" << filename << "> Object " << object_idx << " to output directory" <<  std::endl;
    }

}


void read_bobj(fs::path bobj_filepath, MeshData &mesh)
{
    size_t bytes_per_int = 4;
    size_t bytes_per_float = 4;
    size_t floats_per_vertex = 3;
    size_t bytes_per_vertex = floats_per_vertex * bytes_per_float;
    size_t ints_per_face = 3;
    size_t bytes_per_face = ints_per_face * bytes_per_int;

    std::ifstream infile(bobj_filepath, std::ios::binary);

    unsigned int num_vertices = 0;
    infile.read((char *)&num_vertices, bytes_per_int);
    mesh.num_vertices = num_vertices;

    mesh.vertex_data.resize(num_vertices);
    infile.read((char *)mesh.vertex_data.data(), num_vertices * bytes_per_vertex);

    unsigned int num_faces = 0;
    infile.read((char *)&num_faces, bytes_per_int);
    mesh.num_faces = num_faces;

    mesh.face_data.resize(num_faces * ints_per_face);
    infile.read((char *)mesh.face_data.data(), num_faces * bytes_per_face);

    mesh.face_counts.resize(num_faces, ints_per_face);
}


std::string zero_pad_int_to_string(int n, int width) 
{
    std::ostringstream oss;
    oss.width(width);
    oss.fill('0');
    oss << n;
    return oss.str();;
}


void flip_fluids_cache_to_alembic() 
{
    // Write Alembic
    fs::path output_directory(U"C:/path/to/output/directory");
    fs::create_directories(output_directory);
    
    fs::path filename(U"flip_fluids_alembic.abc");
    fs::path output_filepath = output_directory / filename;

    std::ofstream outfilestream;
    outfilestream.open(output_filepath, std::ios::out | std::ios::binary);

    // Frame rate and timing
    float frame_rate = 24.0f;
    float dt = 1.0f / frame_rate;
    int frame_start = 1;
    int frame_end = 100;
    float start_time = frame_start * dt;
    size_t num_frames = frame_end - frame_start + 1;
    Alembic::AbcGeom::TimeSampling *time_sampling = new Alembic::AbcGeom::TimeSampling(dt, start_time);
    Alembic::AbcGeom::TimeSamplingPtr time_sampling_ptr(time_sampling);

    // Create metadata
    Alembic::Abc::MetaData metadata_info;
    metadata_info.set(Alembic::Abc::kApplicationNameKey, "FLIP Fluids Addon - Alembic Exporter");
    metadata_info.set(Alembic::Abc::kDateWrittenKey ,    get_current_time_string());
    metadata_info.set(Alembic::Abc::kUserDescriptionKey, "Example Alembic Export");

    // Create archive writer
    Alembic::AbcCoreOgawa::WriteArchive archive_writer;
    Alembic::AbcCoreAbstract::ArchiveWriterPtr writer_ptr = archive_writer(&outfilestream, metadata_info);
    Alembic::AbcGeom::OArchive archive(writer_ptr);
    archive.addTimeSampling(*time_sampling_ptr);

    // Top of hierarchy
    Alembic::AbcGeom::OObject top_object(archive, Alembic::AbcGeom::kTop);

    // Create user data
    Alembic::Abc::OCompoundProperty user_metadata = top_object.getProperties();
    Alembic::Abc::OCompoundProperty archive_info(user_metadata,  "archive_info");
    Alembic::Abc::OStringProperty info_up_axis(archive_info,     "up_axis");
    Alembic::Abc::OStringProperty info_scene_units(archive_info, "scene_units");
    Alembic::Abc::OFloatProperty  info_frame_rate(archive_info,  "frame_rate");
    Alembic::Abc::OFloatProperty  info_start_time(archive_info,  "start_time");
    Alembic::Abc::OFloatProperty  info_end_time(archive_info,    "end_time");
    Alembic::Abc::OInt32Property  info_start_frame(archive_info, "start_frame");
    Alembic::Abc::OInt32Property  info_end_frame(archive_info,   "end_frame");

    info_up_axis.set("Z");
    info_scene_units.set("meters");
    info_frame_rate.set(frame_rate);
    info_start_time.set(start_time);
    info_end_time.set(start_time + num_frames * dt);
    info_start_frame.set(frame_start);
    info_end_frame.set(frame_end);

    // Create empty parent
    Alembic::AbcGeom::OXform empty_parent(top_object, "Domain");

    // Generate geometry and animation

    // Initialize object schema
    std::string object_name = "fluid_surface";
    Alembic::AbcGeom::OXform fluid_surface_transform(empty_parent, object_name);
    Alembic::AbcGeom::OPolyMesh fluid_surface_mesh(fluid_surface_transform, object_name);
    Alembic::AbcGeom::OPolyMeshSchema &fluid_surface_mesh_schema = fluid_surface_mesh.getSchema();
    fluid_surface_mesh_schema.setTimeSampling(time_sampling_ptr);

    // Initialize transform
    Imath::V3f transform_translation(0.0f, 0.0f, 0.0f);
    transform_translation = convert_to_blender_coordinates(transform_translation);

    std::chrono::time_point<std::chrono::steady_clock> time_start = std::chrono::steady_clock::now();

    fs::path bakefiles_directory(U"C:/path/to/cache_directory/bakefiles");
    for (size_t i = 0; i < num_frames; i++) {
        std::chrono::time_point<std::chrono::steady_clock> frame_time_start = std::chrono::steady_clock::now();

        // Create geometry sample
        int current_frame = frame_start + i;

        fs::path frame_filename(zero_pad_int_to_string(current_frame, 6) + ".bobj");
        fs::path bobj_filepath = bakefiles_directory / frame_filename;

        MeshData mesh;
        read_bobj(bobj_filepath, mesh);
        convert_to_blender_coordinates(mesh.vertex_data);

        Alembic::AbcGeom::OPolyMeshSchema::Sample mesh_sample(
                Alembic::Abc::V3fArraySample(mesh.vertex_data.data(), mesh.num_vertices),
                Alembic::Abc::Int32ArraySample(mesh.face_data.data(), mesh.face_data.size()),
                Alembic::Abc::Int32ArraySample(mesh.face_counts.data(), mesh.num_faces)
                );

        fluid_surface_mesh_schema.set(mesh_sample);

        std::chrono::time_point<std::chrono::steady_clock> frame_time_stop = std::chrono::steady_clock::now();
        std::chrono::duration<double, std::milli> frame_time_elapsed = frame_time_stop - frame_time_start;

        std::cout << "Writing Frame: " << current_frame << " - " << mesh.num_vertices << " vertices, " << mesh.num_faces << " triangles (" << (float)frame_time_elapsed.count() / 1000.0f << "s)" << std::endl;
    }

    std::chrono::time_point<std::chrono::steady_clock> time_stop = std::chrono::steady_clock::now();
    std::chrono::duration<double, std::milli> time_elapsed = time_stop - time_start;
    std::cout << "Elapsed Time: " << (float)time_elapsed.count() / 1000.0f << " s" << std::endl;

}
