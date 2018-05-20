/*
MIT License

Copyright (c) 2018 Ryan L. Guy

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

#include "../fluidsimulation.h"

#include <cstring>

#include "cbindings.h"
#include "aabb_c.h"
#include "gridindex_c.h"
#include "vector3_c.h"
#include "markerparticle_c.h"
#include "diffuseparticle_c.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

extern "C" {
    EXPORTDLL FluidSimulation* FluidSimulation_new_from_empty(int *err) {
        FluidSimulation *fluidsim = nullptr;
        *err = CBindings::SUCCESS;
        try {
            fluidsim = new FluidSimulation();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return fluidsim;
    }

    EXPORTDLL FluidSimulation* FluidSimulation_new_from_dimensions(
            int isize, int jsize, int ksize, double dx, int *err) {

        FluidSimulation *fluidsim = nullptr;
        *err = CBindings::SUCCESS;
        try {
            fluidsim = new FluidSimulation(isize, jsize, ksize, dx);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return fluidsim;
    }

    EXPORTDLL void FluidSimulation_destroy(FluidSimulation* obj) {
        delete obj;
    }

    EXPORTDLL void FluidSimulation_get_version(
            FluidSimulation* obj, int *major, int *minor, int *revision, int *err) {
        CBindings::safe_execute_method_void_3param(
            obj, &FluidSimulation::getVersion, major, minor, revision, err
        );
    }

    EXPORTDLL void FluidSimulation_initialize(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(obj, &FluidSimulation::initialize, err);
    }

    EXPORTDLL int FluidSimulation_is_initialized(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isInitialized, err
        );
    }

    EXPORTDLL void FluidSimulation_update(FluidSimulation* obj, double dt, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::update, dt, err
        );
    }

    EXPORTDLL int FluidSimulation_get_current_frame(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getCurrentFrame, err
        );
    }

    EXPORTDLL void FluidSimulation_set_current_frame(FluidSimulation* obj, 
                                                     int frameno, int *err) {
        return CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setCurrentFrame, frameno, err
        );
    }

    EXPORTDLL int FluidSimulation_is_current_frame_finished(FluidSimulation* obj, 
                                                            int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isCurrentFrameFinished, err
        );
    }

    EXPORTDLL double FluidSimulation_get_cell_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getCellSize, err
        );
    }

    EXPORTDLL void FluidSimulation_get_grid_dimensions(
            FluidSimulation* obj, int *i, int *j, int *k, int *err) {
        CBindings::safe_execute_method_void_3param(
            obj, &FluidSimulation::getGridDimensions, i, j, k, err
        );
    }

    EXPORTDLL int FluidSimulation_get_grid_width(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getGridWidth, err
        );
    }

    EXPORTDLL int FluidSimulation_get_grid_height(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getGridHeight, err
        );
    }

    EXPORTDLL int FluidSimulation_get_grid_depth(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getGridDepth, err
        );
    }

    EXPORTDLL void FluidSimulation_get_simulation_dimensions(
            FluidSimulation* obj, 
            double *width, double *height, double *depth, int *err) {
        CBindings::safe_execute_method_void_3param(
            obj, &FluidSimulation::getSimulationDimensions, width, height, depth, err
        );
    }

    EXPORTDLL double FluidSimulation_get_simulation_width(FluidSimulation* obj, 
                                                          int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSimulationWidth, err
        );
    }

    EXPORTDLL double FluidSimulation_get_simulation_height(FluidSimulation* obj, 
                                                           int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSimulationHeight, err
        );
    }

    EXPORTDLL double FluidSimulation_get_simulation_depth(FluidSimulation* obj, 
                                                          int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSimulationDepth, err
        );
    }

    EXPORTDLL double FluidSimulation_get_density(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDensity, err
        );
    }

    EXPORTDLL void FluidSimulation_set_density(FluidSimulation* obj, 
                                               double density,
                                               int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDensity, density, err
        );
    }

    EXPORTDLL double FluidSimulation_get_marker_particle_scale(FluidSimulation* obj, 
                                                               int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMarkerParticleScale, err
        );
    }

    EXPORTDLL void FluidSimulation_set_marker_particle_scale(FluidSimulation* obj, 
                                                             double scale,
                                                             int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMarkerParticleScale, scale, err
        );
    }

    EXPORTDLL double FluidSimulation_get_marker_particle_jitter_factor(FluidSimulation* obj, 
                                                                       int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMarkerParticleJitterFactor, err
        );
    }

    EXPORTDLL void FluidSimulation_set_marker_particle_jitter_factor(FluidSimulation* obj, 
                                                                     double jit,
                                                                     int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMarkerParticleJitterFactor, jit, err
        );
    }

    EXPORTDLL int FluidSimulation_get_surface_subdivision_level(FluidSimulation* obj, 
                                                                int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSurfaceSubdivisionLevel, err
        );
    }

    EXPORTDLL void FluidSimulation_set_surface_subdivision_level(FluidSimulation* obj, 
                                                                 int level,
                                                                 int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setSurfaceSubdivisionLevel, level, err
        );
    }

    EXPORTDLL int FluidSimulation_get_num_polygonizer_slices(FluidSimulation* obj, 
                                                             int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getNumPolygonizerSlices, err
        );
    }

    EXPORTDLL void FluidSimulation_set_num_polygonizer_slices(FluidSimulation* obj, 
                                                              int numslices,
                                                              int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setNumPolygonizerSlices, numslices, err
        );
    }

    EXPORTDLL double FluidSimulation_get_surface_smoothing_value(FluidSimulation* obj, 
                                                                 int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSurfaceSmoothingValue, err
        );
    }

    EXPORTDLL void FluidSimulation_set_surface_smoothing_value(FluidSimulation* obj, 
                                                               double s,
                                                               int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setSurfaceSmoothingValue, s, err
        );
    }

    EXPORTDLL int FluidSimulation_get_surface_smoothing_iterations(FluidSimulation* obj, 
                                                                 int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSurfaceSmoothingIterations, err
        );
    }

    EXPORTDLL void FluidSimulation_set_surface_smoothing_iterations(FluidSimulation* obj, 
                                                                    int n,
                                                                    int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setSurfaceSmoothingIterations, n, err
        );
    }

    EXPORTDLL int FluidSimulation_get_min_polyhedron_triangle_count(FluidSimulation* obj, 
                                                                    int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinPolyhedronTriangleCount, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_polyhedron_triangle_count(FluidSimulation* obj, 
                                                                     int count,
                                                                     int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinPolyhedronTriangleCount, count, err
        );
    }

    EXPORTDLL Vector3_t FluidSimulation_get_domain_offset(FluidSimulation* obj,
                                                          int *err) {
        vmath::vec3 offset = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDomainOffset, err
        );
        return CBindings::to_struct(offset);
    }

    EXPORTDLL void FluidSimulation_set_domain_offset(FluidSimulation* obj,
                                                     double x, double y, double z,
                                                     int *err) {
        CBindings::safe_execute_method_void_3param(
            obj, &FluidSimulation::setDomainOffset, x, y, z, err
        );
    }

    EXPORTDLL double FluidSimulation_get_domain_scale(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDomainScale, err
        );
    }

    EXPORTDLL void FluidSimulation_set_domain_scale(FluidSimulation* obj, 
                                                    double scale,
                                                    int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDomainScale, scale, err
        );
    }

    EXPORTDLL void FluidSimulation_set_mesh_output_format_as_ply(FluidSimulation* obj, 
                                                                 int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::setMeshOutputFormatAsPLY, err
        );
    }

    EXPORTDLL void FluidSimulation_set_mesh_output_format_as_bobj(FluidSimulation* obj, 
                                                                  int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::setMeshOutputFormatAsBOBJ, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_console_output(FluidSimulation* obj,
                                                         int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableConsoleOutput, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_console_output(FluidSimulation* obj,
                                                          int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableConsoleOutput, err
        );
    }

    EXPORTDLL int FluidSimulation_is_console_output_enabled(FluidSimulation* obj,
                                                            int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isConsoleOutputEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_surface_reconstruction(FluidSimulation* obj,
                                                                           int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableSurfaceReconstruction, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_surface_reconstruction(FluidSimulation* obj,
                                                                            int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableSurfaceReconstruction, err
        );
    }

    EXPORTDLL int FluidSimulation_is_surface_reconstruction_enabled(FluidSimulation* obj,
                                                                              int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isSurfaceReconstructionEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_asynchronous_meshing(FluidSimulation* obj,
                                                               int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableAsynchronousMeshing, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_asynchronous_meshing(FluidSimulation* obj,
                                                                int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableAsynchronousMeshing, err
        );
    }

    EXPORTDLL int FluidSimulation_is_asynchronous_meshing_enabled(FluidSimulation* obj,
                                                                  int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isAsynchronousMeshingEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_preview_mesh_output(FluidSimulation* obj,
                                                              double dx,
                                                              int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::enablePreviewMeshOutput, dx, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_preview_mesh_output(FluidSimulation* obj,
                                                               int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disablePreviewMeshOutput, err
        );
    }

    EXPORTDLL int FluidSimulation_is_preview_mesh_output_enabled(FluidSimulation* obj,
                                                                 int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isPreviewMeshOutputEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_smooth_interface_meshing(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableSmoothInterfaceMeshing, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_smooth_interface_meshing(FluidSimulation* obj,
                                                                    int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableSmoothInterfaceMeshing, err
        );
    }

    EXPORTDLL int FluidSimulation_is_smooth_interface_meshing_enabled(FluidSimulation* obj,
                                                                      int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isSmoothInterfaceMeshingEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_inverted_contact_normals(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableInvertedContactNormals, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_inverted_contact_normals(FluidSimulation* obj,
                                                                    int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableInvertedContactNormals, err
        );
    }

    EXPORTDLL int FluidSimulation_is_inverted_contact_normals_enabled(FluidSimulation* obj,
                                                                      int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isInvertedContactNormalsEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_fluid_particle_output(FluidSimulation* obj,
                                                                int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableFluidParticleOutput, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_fluid_particle_output(FluidSimulation* obj,
                                                                 int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableFluidParticleOutput, err
        );
    }

    EXPORTDLL int FluidSimulation_is_fluid_particle_output_enabled(FluidSimulation* obj,
                                                                   int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isFluidParticleOutputEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_internal_obstacle_mesh_output(FluidSimulation* obj,
                                                                        int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableInternalObstacleMeshOutput, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_internal_obstacle_mesh_output(FluidSimulation* obj,
                                                                         int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableInternalObstacleMeshOutput, err
        );
    }

    EXPORTDLL int FluidSimulation_is_internal_obstacle_mesh_output_enabled(FluidSimulation* obj,
                                                                           int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isInternalObstacleMeshOutputEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_diffuse_material_output(FluidSimulation* obj,
                                                                  int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableDiffuseMaterialOutput, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_diffuse_material_output(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableDiffuseMaterialOutput, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_material_output_enabled(FluidSimulation* obj,
                                                                     int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffuseMaterialOutputEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_diffuse_particle_emission(FluidSimulation* obj,
                                                                    int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableDiffuseParticleEmission, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_diffuse_particle_emission(FluidSimulation* obj,
                                                                     int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableDiffuseParticleEmission, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_particle_emission_enabled(FluidSimulation* obj,
                                                                       int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffuseParticleEmissionEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_diffuse_foam(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableDiffuseFoam, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_diffuse_foam(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableDiffuseFoam, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_foam_enabled(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffuseFoamEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_diffuse_bubbles(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableDiffuseBubbles, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_diffuse_bubbles(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableDiffuseBubbles, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_bubbles_enabled(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffuseBubblesEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_diffuse_spray(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableDiffuseSpray, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_diffuse_spray(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableDiffuseSpray, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_spray_enabled(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffuseSprayEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_bubble_diffuse_material(FluidSimulation* obj,
                                                                  int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableBubbleDiffuseMaterial, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_bubble_diffuse_material(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableBubbleDiffuseMaterial, err
        );
    }

    EXPORTDLL int FluidSimulation_is_bubble_diffuse_material_enabled(FluidSimulation* obj,
                                                                     int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isBubbleDiffuseMaterialEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_spray_diffuse_material(FluidSimulation* obj,
                                                                  int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableSprayDiffuseMaterial, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_spray_diffuse_material(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableSprayDiffuseMaterial, err
        );
    }

    EXPORTDLL int FluidSimulation_is_spray_diffuse_material_enabled(FluidSimulation* obj,
                                                                     int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isSprayDiffuseMaterialEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_foam_diffuse_material(FluidSimulation* obj,
                                                                  int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableFoamDiffuseMaterial, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_foam_diffuse_material(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableFoamDiffuseMaterial, err
        );
    }

    EXPORTDLL int FluidSimulation_is_foam_diffuse_material_enabled(FluidSimulation* obj,
                                                                     int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isFoamDiffuseMaterialEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_output_diffuse_material_as_single_file(FluidSimulation* obj,
                                                                          int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::outputDiffuseMaterialAsSingleFile, err
        );
    }

    EXPORTDLL void FluidSimulation_output_diffuse_material_as_separate_files(FluidSimulation* obj,
                                                                             int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::outputDiffuseMaterialAsSeparateFiles, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_material_output_as_separate_files(FluidSimulation* obj,
                                                                               int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffuseMaterialOutputAsSeparateFiles, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_emitter_generation_rate(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseEmitterGenerationRate, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_emitter_generation_rate(FluidSimulation* obj, 
                                                                       double rate, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseEmitterGenerationRate, rate, err
        );
    }

    EXPORTDLL double FluidSimulation_get_min_diffuse_emitter_energy(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinDiffuseEmitterEnergy, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_diffuse_emitter_energy(FluidSimulation* obj, 
                                                                  double e, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinDiffuseEmitterEnergy, e, err
        );
    }

    EXPORTDLL double FluidSimulation_get_max_diffuse_emitter_energy(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxDiffuseEmitterEnergy, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_diffuse_emitter_energy(FluidSimulation* obj, 
                                                                  double e, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxDiffuseEmitterEnergy, e, err
        );
    }

    EXPORTDLL double FluidSimulation_get_min_diffuse_wavecrest_curvature(FluidSimulation* obj, 
                                                                         int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinDiffuseWavecrestCurvature, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_diffuse_wavecrest_curvature(FluidSimulation* obj, 
                                                                       double k, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinDiffuseWavecrestCurvature, k, err
        );
    }

    EXPORTDLL double FluidSimulation_get_max_diffuse_wavecrest_curvature(FluidSimulation* obj, 
                                                                         int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxDiffuseWavecrestCurvature, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_diffuse_wavecrest_curvature(FluidSimulation* obj, 
                                                                       double k, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxDiffuseWavecrestCurvature, k, err
        );
    }

    EXPORTDLL double FluidSimulation_get_min_diffuse_turbulence(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinDiffuseTurbulence, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_diffuse_turbulence(FluidSimulation* obj, 
                                                              double t, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinDiffuseTurbulence, t, err
        );
    }

    EXPORTDLL double FluidSimulation_get_max_diffuse_turbulence(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxDiffuseTurbulence, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_diffuse_turbulence(FluidSimulation* obj, 
                                                              double t, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxDiffuseTurbulence, t, err
        );
    }

    EXPORTDLL int FluidSimulation_get_max_num_diffuse_particles(FluidSimulation* obj,
                                                                int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxNumDiffuseParticles, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_num_diffuse_particles(FluidSimulation* obj,
                                                                 int n, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxNumDiffuseParticles, n, err
        );
    }

    EXPORTDLL AABB_t FluidSimulation_get_diffuse_emitter_generation_bounds(FluidSimulation* obj,
                                                                           int *err) {
        AABB bounds = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseEmitterGenerationBounds, err
        );

        return CBindings::to_struct(bounds);
    }

    EXPORTDLL void FluidSimulation_set_diffuse_emitter_generation_bounds(FluidSimulation* obj,
                                                                         AABB_t bounds, int *err) {
        AABB bounds_cpp = CBindings::to_class(bounds);
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseEmitterGenerationBounds, bounds_cpp, err
        );
    }

    EXPORTDLL double FluidSimulation_get_min_diffuse_particle_lifetime(FluidSimulation* obj,
                                                                       int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinDiffuseParticleLifetime, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_diffuse_particle_lifetime(FluidSimulation* obj,
                                                                     double lifetime, 
                                                                     int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinDiffuseParticleLifetime, lifetime, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_particle_lifetime_variance(FluidSimulation* obj,
                                                                            int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleLifetimeVariance, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_particle_lifetime_variance(FluidSimulation* obj,
                                                                          double variance, 
                                                                          int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseParticleLifetimeVariance, variance, err
        );
    }

    EXPORTDLL double FluidSimulation_get_foam_particle_lifetime_modifier(FluidSimulation* obj,
                                                                         int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getFoamParticleLifetimeModifier, err
        );
    }

    EXPORTDLL void FluidSimulation_set_foam_particle_lifetime_modifier(FluidSimulation* obj,
                                                                       double modifier, 
                                                                       int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setFoamParticleLifetimeModifier, modifier, err
        );
    }

    EXPORTDLL double FluidSimulation_get_bubble_particle_lifetime_modifier(FluidSimulation* obj,
                                                                           int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getBubbleParticleLifetimeModifier, err
        );
    }

    EXPORTDLL void FluidSimulation_set_bubble_particle_lifetime_modifier(FluidSimulation* obj,
                                                                       double modifier, 
                                                                       int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setBubbleParticleLifetimeModifier, modifier, err
        );
    }

    EXPORTDLL double FluidSimulation_get_spray_particle_lifetime_modifier(FluidSimulation* obj,
                                                                         int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getSprayParticleLifetimeModifier, err
        );
    }

    EXPORTDLL void FluidSimulation_set_spray_particle_lifetime_modifier(FluidSimulation* obj,
                                                                       double modifier, 
                                                                       int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setSprayParticleLifetimeModifier, modifier, err
        );
    }

    EXPORTDLL double FluidSimulation_get_max_diffuse_particle_lifetime(FluidSimulation* obj,
                                                                       int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxDiffuseParticleLifetime, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_diffuse_particle_lifetime(FluidSimulation* obj,
                                                                     double lifetime, 
                                                                     int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxDiffuseParticleLifetime, lifetime, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_particle_wavecrest_emission_rate(
            FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleWavecrestEmissionRate, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_particle_wavecrest_emission_rate(
            FluidSimulation* obj, double rate, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseParticleWavecrestEmissionRate, rate, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_particle_turbulence_emission_rate(
            FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleTurbulenceEmissionRate, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_particle_turbulence_emission_rate(
            FluidSimulation* obj, double rate, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseParticleTurbulenceEmissionRate, rate, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_foam_advection_strength(FluidSimulation* obj, 
                                                                         int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseFoamAdvectionStrength, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_foam_advection_strength(FluidSimulation* obj, 
                                                                       double s, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseFoamAdvectionStrength, s, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_foam_layer_depth(FluidSimulation* obj, 
                                                                  int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseFoamLayerDepth, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_foam_layer_depth(FluidSimulation* obj, 
                                                                double depth, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseFoamLayerDepth, depth, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_foam_layer_offset(FluidSimulation* obj, 
                                                                   int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseFoamLayerOffset, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_foam_layer_offset(FluidSimulation* obj, 
                                                                 double offset, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseFoamLayerOffset, offset, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_diffuse_preserve_foam(FluidSimulation* obj,
                                                                int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableDiffusePreserveFoam, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_diffuse_preserve_foam(FluidSimulation* obj,
                                                                 int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableDiffusePreserveFoam, err
        );
    }

    EXPORTDLL int FluidSimulation_is_diffuse_preserve_foam_enabled(FluidSimulation* obj,
                                                                   int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isDiffusePreserveFoamEnabled, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_foam_preservation_rate(FluidSimulation* obj, 
                                                                        int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseFoamPreservationRate, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_foam_preservation_rate(FluidSimulation* obj, 
                                                                       double rate, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseFoamPreservationRate, rate, err
        );
    }

    EXPORTDLL double FluidSimulation_get_min_diffuse_foam_density(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinDiffuseFoamDensity, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_diffuse_foam_density(FluidSimulation* obj, 
                                                              double d, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinDiffuseFoamDensity, d, err
        );
    }

    EXPORTDLL double FluidSimulation_get_max_diffuse_foam_density(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxDiffuseFoamDensity, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_diffuse_foam_density(FluidSimulation* obj, 
                                                              double d, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxDiffuseFoamDensity, d, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_bubble_drag_coefficient(FluidSimulation* obj, 
                                                                         int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseBubbleDragCoefficient, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_bubble_drag_coefficient(FluidSimulation* obj, 
                                                                       double d, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseBubbleDragCoefficient, d, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_bubble_bouyancy_coefficient(FluidSimulation* obj, 
                                                                             int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseBubbleBouyancyCoefficient, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_bubble_bouyancy_coefficient(FluidSimulation* obj, 
                                                                           double b, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseBubbleBouyancyCoefficient, b, err
        );
    }

    EXPORTDLL double FluidSimulation_get_diffuse_spray_drag_coefficient(FluidSimulation* obj, 
                                                                        int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseSprayDragCoefficient, err
        );
    }

    EXPORTDLL void FluidSimulation_set_diffuse_spray_drag_coefficient(FluidSimulation* obj, 
                                                                      double d, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseSprayDragCoefficient, d, err
        );
    }

    EXPORTDLL int FluidSimulation_get_diffuse_foam_limit_behaviour(FluidSimulation* obj, 
                                                                   int *err) {
        LimitBehaviour b = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseFoamLimitBehaviour, err
        );

        int enum_value = 0;
        if (b == LimitBehaviour::kill) {
            enum_value = 0;
        } else if (b == LimitBehaviour::ballistic) {
            enum_value = 1;
        } else if (b == LimitBehaviour::collide) {
            enum_value = 2;
        }

        return enum_value;
    }

    EXPORTDLL void FluidSimulation_set_diffuse_foam_limit_behaviour(FluidSimulation* obj, 
                                                                    int enum_value,
                                                                    int *err) {
        LimitBehaviour b = LimitBehaviour::kill;
        if (enum_value == 0) {
            b = LimitBehaviour::kill;
        } else if (enum_value == 1) {
            b = LimitBehaviour::ballistic;
        } else if (enum_value == 2) {
            b = LimitBehaviour::collide;
        }

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseFoamLimitBehaviour, b, err
        );
    }

    EXPORTDLL int FluidSimulation_get_diffuse_bubble_limit_behaviour(FluidSimulation* obj, 
                                                                    int *err) {
        LimitBehaviour b = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseBubbleLimitBehaviour, err
        );

        int enum_value = 0;
        if (b == LimitBehaviour::kill) {
            enum_value = 0;
        } else if (b == LimitBehaviour::ballistic) {
            enum_value = 1;
        } else if (b == LimitBehaviour::collide) {
            enum_value = 2;
        }

        return enum_value;
    }

    EXPORTDLL void FluidSimulation_set_diffuse_bubble_limit_behaviour(FluidSimulation* obj, 
                                                                      int enum_value,
                                                                      int *err) {
        LimitBehaviour b = LimitBehaviour::kill;
        if (enum_value == 0) {
            b = LimitBehaviour::kill;
        } else if (enum_value == 1) {
            b = LimitBehaviour::ballistic;
        } else if (enum_value == 2) {
            b = LimitBehaviour::collide;
        }

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseBubbleLimitBehaviour, b, err
        );
    }

    EXPORTDLL int FluidSimulation_get_diffuse_spray_limit_behaviour(FluidSimulation* obj, 
                                                                    int *err) {
        LimitBehaviour b = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseSprayLimitBehaviour, err
        );

        int enum_value = 0;
        if (b == LimitBehaviour::kill) {
            enum_value = 0;
        } else if (b == LimitBehaviour::ballistic) {
            enum_value = 1;
        } else if (b == LimitBehaviour::collide) {
            enum_value = 2;
        }

        return enum_value;
    }

    EXPORTDLL void FluidSimulation_set_diffuse_spray_limit_behaviour(FluidSimulation* obj, 
                                                                     int enum_value,
                                                                     int *err) {
        LimitBehaviour b = LimitBehaviour::kill;
        if (enum_value == 0) {
            b = LimitBehaviour::kill;
        } else if (enum_value == 1) {
            b = LimitBehaviour::ballistic;
        } else if (enum_value == 2) {
            b = LimitBehaviour::collide;
        }

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseSprayLimitBehaviour, b, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_foam_active_boundary_sides(FluidSimulation* obj, 
                                                                          int *result,
                                                                          int *err) {
        std::vector<bool> boolvect = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseFoamActiveBoundarySides, err
        );

        for (int i = 0; i < 6; i++) {
            result[i] = boolvect[i];
        }
    }

    EXPORTDLL void FluidSimulation_set_diffuse_foam_active_boundary_sides(FluidSimulation* obj, 
                                                                          int *active, int *err) {
        std::vector<bool> boolvect;
        for (int i = 0; i < 6; i++) {
            boolvect.push_back(active[i] != 0);
        }

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseFoamActiveBoundarySides, boolvect, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_bubble_active_boundary_sides(FluidSimulation* obj, 
                                                                          int *result,
                                                                          int *err) {
        std::vector<bool> boolvect = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseBubbleActiveBoundarySides, err
        );

        for (int i = 0; i < 6; i++) {
            result[i] = boolvect[i];
        }
    }

    EXPORTDLL void FluidSimulation_set_diffuse_bubble_active_boundary_sides(FluidSimulation* obj, 
                                                                          int *active, int *err) {
        std::vector<bool> boolvect;
        for (int i = 0; i < 6; i++) {
            boolvect.push_back(active[i] != 0);
        }

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseBubbleActiveBoundarySides, boolvect, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_spray_active_boundary_sides(FluidSimulation* obj, 
                                                                          int *result,
                                                                          int *err) {
        std::vector<bool> boolvect = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseSprayActiveBoundarySides, err
        );

        for (int i = 0; i < 6; i++) {
            result[i] = (bool)boolvect[i];
        }
    }

    EXPORTDLL void FluidSimulation_set_diffuse_spray_active_boundary_sides(FluidSimulation* obj, 
                                                                          int *active, int *err) {
        std::vector<bool> boolvect;
        for (int i = 0; i < 6; i++) {
            boolvect.push_back(active[i] != 0);
        }

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setDiffuseSprayActiveBoundarySides, boolvect, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_opencl_particle_advection(FluidSimulation* obj, 
                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableOpenCLParticleAdvection, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_opencl_particle_advection(FluidSimulation* obj,
                                                    int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableOpenCLParticleAdvection, err
        );
    }

    EXPORTDLL int FluidSimulation_is_opencl_particle_advection_enabled(FluidSimulation* obj,
                                                      int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isOpenCLParticleAdvectionEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_opencl_scalar_field(FluidSimulation* obj, 
                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableOpenCLScalarField, err
        );
    }

    EXPORTDLL int FluidSimulation_get_particle_advection_kernel_workload_size(
            FluidSimulation* obj, int *err) {

        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getParticleAdvectionKernelWorkLoadSize, err
        );
    }

    EXPORTDLL void FluidSimulation_set_particle_advection_kernel_workload_size(
            FluidSimulation* obj, int size, int *err) {

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setParticleAdvectionKernelWorkLoadSize, size, err
        );
    }

    EXPORTDLL int FluidSimulation_get_scalar_field_kernel_workload_size(
            FluidSimulation* obj, int *err) {

        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getScalarFieldKernelWorkLoadSize, err
        );
    }

    EXPORTDLL void FluidSimulation_set_scalar_field_kernel_workload_size(
            FluidSimulation* obj, int size, int *err) {
        
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setScalarFieldKernelWorkLoadSize, size, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_opencl_scalar_field(FluidSimulation* obj,
                                                    int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableOpenCLScalarField, err
        );
    }

    EXPORTDLL int FluidSimulation_is_opencl_scalar_field_enabled(FluidSimulation* obj,
                                                      int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isOpenCLScalarFieldEnabled, err
        );
    }

     EXPORTDLL int FluidSimulation_get_max_thread_count(
            FluidSimulation* obj, int *err) {

        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxThreadCount, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_thread_count(FluidSimulation* obj, 
                                                        int n, int *err) {
        
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxThreadCount, n, err
        );
    }

    EXPORTDLL void FluidSimulation_add_body_force(FluidSimulation* obj,
                                                  double fx, double fy, double fz,
                                                  int *err) {
        CBindings::safe_execute_method_void_3param(
            obj, &FluidSimulation::addBodyForce, fx, fy, fz, err
        );
    }

    EXPORTDLL Vector3_t FluidSimulation_get_constant_body_force(FluidSimulation* obj,
                                                                int *err) {
        vmath::vec3 f = CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getConstantBodyForce, err
        );
        return CBindings::to_struct(f);
    }

    EXPORTDLL Vector3_t FluidSimulation_get_variable_body_force(FluidSimulation* obj,
                                                                double px, 
                                                                double py, 
                                                                double pz, int *err) {
        vmath::vec3 f = CBindings::safe_execute_method_ret_3param(
            obj, &FluidSimulation::getVariableBodyForce, px, py, pz, err
        );
        return CBindings::to_struct(f);
    }

    EXPORTDLL Vector3_t FluidSimulation_get_total_body_force(FluidSimulation* obj,
                                                             double px, 
                                                             double py, 
                                                             double pz, int *err) {
        vmath::vec3 f = CBindings::safe_execute_method_ret_3param(
            obj, &FluidSimulation::getTotalBodyForce, px, py, pz, err
        );
        return CBindings::to_struct(f);
    }

    EXPORTDLL void FluidSimulation_reset_body_force(FluidSimulation* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::resetBodyForce, err
        );
    }

    EXPORTDLL double FluidSimulation_get_viscosity(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getViscosity, err
        );
    }

    EXPORTDLL void FluidSimulation_set_viscosity(FluidSimulation* obj, 
                                                double v,
                                                int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setViscosity, v, err
        );
    }

    EXPORTDLL void FluidSimulation_set_boundary_friction(FluidSimulation* obj, double f, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setBoundaryFriction, f, err
        );
    }

    EXPORTDLL double FluidSimulation_get_boundary_friction(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getBoundaryFriction, err
        );
    }

    EXPORTDLL int FluidSimulation_get_CFL_condition_number(
            FluidSimulation* obj, int *err) {

        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getCFLConditionNumber, err
        );
    }

    EXPORTDLL void FluidSimulation_set_CFL_condition_number(
            FluidSimulation* obj, int n, int *err) {

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setCFLConditionNumber, n, err
        );
    }

    EXPORTDLL int FluidSimulation_get_min_time_steps_per_frame(
            FluidSimulation* obj, int *err) {

        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMinTimeStepsPerFrame, err
        );
    }

    EXPORTDLL void FluidSimulation_set_min_time_steps_per_frame(
            FluidSimulation* obj, int n, int *err) {

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMinTimeStepsPerFrame, n, err
        );
    }

    EXPORTDLL int FluidSimulation_get_max_time_steps_per_frame(
            FluidSimulation* obj, int *err) {

        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMaxTimeStepsPerFrame, err
        );
    }

    EXPORTDLL void FluidSimulation_set_max_time_steps_per_frame(
            FluidSimulation* obj, int n, int *err) {

        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setMaxTimeStepsPerFrame, n, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_adaptive_obstacle_time_stepping(FluidSimulation* obj,
                                                                          int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableAdaptiveObstacleTimeStepping, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_adaptive_obstacle_time_stepping(FluidSimulation* obj,
                                                                           int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableAdaptiveObstacleTimeStepping, err
        );
    }

    EXPORTDLL int FluidSimulation_is_adaptive_obstacle_time_stepping_enabled(FluidSimulation* obj,
                                                                             int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isAdaptiveObstacleTimeSteppingEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_extreme_velocity_removal(FluidSimulation* obj,
                                                                   int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableExtremeVelocityRemoval, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_extreme_velocity_removal(FluidSimulation* obj,
                                                                    int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableExtremeVelocityRemoval, err
        );
    }

    EXPORTDLL int FluidSimulation_is_extreme_velocity_removal_enabled(FluidSimulation* obj,
                                                                     int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isExtremeVelocityRemovalEnabled, err
        );
    }

    EXPORTDLL double FluidSimulation_get_PICFLIP_ratio(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getPICFLIPRatio, err
        );
    }

    EXPORTDLL void FluidSimulation_set_PICFLIP_ratio(FluidSimulation* obj, 
                                                     double ratio, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setPICFLIPRatio, ratio, err
        );
    }

    EXPORTDLL void FluidSimulation_get_preferred_gpu_device(FluidSimulation* obj, 
                                                            char *device_name, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::string name = obj->getPreferredGPUDevice();
            name.copy(device_name, 4096);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_set_preferred_gpu_device(FluidSimulation* obj, 
                                                            char *device_name, int *err) {
        std::string str_device_name = device_name;
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::setPreferredGPUDevice, str_device_name, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_experimental_optimization_features(FluidSimulation* obj,
                                                                             int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableExperimentalOptimizationFeatures, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_experimental_optimization_features(FluidSimulation* obj,
                                                                              int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableExperimentalOptimizationFeatures, err
        );
    }

    EXPORTDLL int FluidSimulation_is_experimental_optimization_features_enabled(FluidSimulation* obj,
                                                                                int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isExperimentalOptimizationFeaturesEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_static_solid_levelset_precomputation(FluidSimulation* obj,
                                                                               int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableStaticSolidLevelSetPrecomputation, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_static_solid_levelset_precomputation(FluidSimulation* obj,
                                                                                int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableStaticSolidLevelSetPrecomputation, err
        );
    }

    EXPORTDLL int FluidSimulation_is_static_solid_levelset_precomputation_enabled(FluidSimulation* obj,
                                                                                  int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isStaticSolidLevelSetPrecomputationEnabled, err
        );
    }

    EXPORTDLL void FluidSimulation_enable_temporary_mesh_levelset(FluidSimulation* obj,
                                                                               int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::enableTemporaryMeshLevelSet, err
        );
    }

    EXPORTDLL void FluidSimulation_disable_temporary_mesh_levelset(FluidSimulation* obj,
                                                                                int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::disableTemporaryMeshLevelSet, err
        );
    }

    EXPORTDLL int FluidSimulation_is_temporary_mesh_levelset_enabled(FluidSimulation* obj,
                                                                                  int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::isTemporaryMeshLevelSetEnabled, err
        );
    }


    EXPORTDLL void FluidSimulation_add_mesh_fluid_source(FluidSimulation* obj, 
                                                         MeshFluidSource *source,
                                                         int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::addMeshFluidSource, source, err
        );
    }

    EXPORTDLL void FluidSimulation_remove_mesh_fluid_source(FluidSimulation* obj,
                                                            MeshFluidSource *source,
                                                            int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::removeMeshFluidSource, source, err
        );
    }

    EXPORTDLL void FluidSimulation_remove_mesh_fluid_sources(FluidSimulation* obj, 
                                                             int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::removeMeshFluidSources, err
        );
    }

    EXPORTDLL void FluidSimulation_add_mesh_obstacle(FluidSimulation* obj, 
                                                     MeshObject *obstacle,
                                                     int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::addMeshObstacle, obstacle, err
        );
    }

    EXPORTDLL void FluidSimulation_remove_mesh_obstacle(FluidSimulation* obj,
                                                        MeshObject *obstacle,
                                                        int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::removeMeshObstacle, obstacle, err
        );
    }

    EXPORTDLL void FluidSimulation_remove_mesh_obstacles(FluidSimulation* obj, 
                                                         int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &FluidSimulation::removeMeshObstacles, err
        );
    }

    EXPORTDLL void FluidSimulation_add_mesh_fluid(FluidSimulation* obj, 
                                                     MeshObject *fluid,
                                                     Vector3_t velocity,
                                                     int *err) {
        vmath::vec3 v(velocity.x, velocity.y, velocity.z);

        *err = CBindings::SUCCESS;
        try {
            obj->addMeshFluid(*fluid, v);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL int FluidSimulation_get_num_marker_particles(FluidSimulation* obj, 
                                                           int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getNumMarkerParticles, err
        );
    }

    EXPORTDLL void FluidSimulation_get_marker_particles(
            FluidSimulation* obj, 
            int startidx, int endidx,
            MarkerParticle_t *out, int *err) {

        std::vector<MarkerParticle> mps = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getMarkerParticles,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < mps.size(); i++) {
            out[i] = CBindings::to_struct(mps[i]);
        }
    }

    EXPORTDLL void FluidSimulation_get_marker_particle_positions(
            FluidSimulation* obj, 
            int startidx, int endidx,
            Vector3_t *out, int *err) {

        std::vector<vmath::vec3> mps = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getMarkerParticlePositions,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < mps.size(); i++) {
            out[i] = CBindings::to_struct(mps[i]);
        }
    }

    EXPORTDLL void FluidSimulation_get_marker_particle_velocities(
            FluidSimulation* obj, 
            int startidx, int endidx,
            Vector3_t *out, int *err) {

        std::vector<vmath::vec3> mvs = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getMarkerParticleVelocities,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < mvs.size(); i++) {
            out[i] = CBindings::to_struct(mvs[i]);
        }
    }

    EXPORTDLL int FluidSimulation_get_num_diffuse_particles(FluidSimulation* obj, 
                                                            int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getNumDiffuseParticles, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particles(
            FluidSimulation* obj, 
            int startidx, int endidx,
            DiffuseParticle_t *out, int *err) {

        std::vector<DiffuseParticle> dps = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getDiffuseParticles,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < dps.size(); i++) {
            out[i] = CBindings::to_struct(dps[i]);
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_positions(
            FluidSimulation* obj, 
            int startidx, int endidx,
            Vector3_t *out, int *err) {

        std::vector<vmath::vec3> dps = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getDiffuseParticlePositions,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < dps.size(); i++) {
            out[i] = CBindings::to_struct(dps[i]);
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_velocities(
            FluidSimulation* obj, 
            int startidx, int endidx,
            Vector3_t *out, int *err) {

        std::vector<vmath::vec3> dvs = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getDiffuseParticleVelocities,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < dvs.size(); i++) {
            out[i] = CBindings::to_struct(dvs[i]);
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_lifetimes(
            FluidSimulation* obj, 
            int startidx, int endidx,
            float *out, int *err) {

        std::vector<float> lfs = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getDiffuseParticleLifetimes,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < lfs.size(); i++) {
            out[i] = lfs[i];
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_types(
            FluidSimulation* obj, 
            int startidx, int endidx,
            char *out, int *err) {

        std::vector<char> types = CBindings::safe_execute_method_ret_2param(
            obj, &FluidSimulation::getDiffuseParticleTypes,
            startidx, endidx, err
        );

        for (unsigned int i = 0; i < types.size(); i++) {
            out[i] = types[i];
        }
    }

    EXPORTDLL char* FluidSimulation_get_error_message() {
        return CBindings::get_error_message();
    }

    EXPORTDLL int FluidSimulation_get_surface_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getSurfaceData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_surface_preview_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getSurfacePreviewData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_diffuse_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_diffuse_foam_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseFoamData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_diffuse_bubble_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseBubbleData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_diffuse_spray_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseSprayData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_fluid_particle_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getFluidParticleData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_internal_obstacle_mesh_data_size(FluidSimulation* obj, 
                                                                       int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getInternalObstacleMeshData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL int FluidSimulation_get_logfile_data_size(FluidSimulation* obj, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getLogFileData();
            return (int)data->size();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return 0;
    }

    EXPORTDLL unsigned int FluidSimulation_get_marker_particle_position_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMarkerParticlePositionDataSize, err
        );
    }

    EXPORTDLL unsigned int FluidSimulation_get_marker_particle_velocity_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getMarkerParticleVelocityDataSize, err
        );
    }

    EXPORTDLL unsigned int FluidSimulation_get_diffuse_particle_position_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticlePositionDataSize, err
        );
    }

    EXPORTDLL unsigned int FluidSimulation_get_diffuse_particle_velocity_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleVelocityDataSize, err
        );
    }

    EXPORTDLL unsigned int FluidSimulation_get_diffuse_particle_lifetime_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleLifetimeDataSize, err
        );
    }

    EXPORTDLL unsigned int FluidSimulation_get_diffuse_particle_type_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleTypeDataSize, err
        );
    }

    EXPORTDLL unsigned int FluidSimulation_get_diffuse_particle_id_data_size(FluidSimulation* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getDiffuseParticleIdDataSize, err
        );
    }

    EXPORTDLL void FluidSimulation_get_surface_data(FluidSimulation* obj, 
                                                             char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getSurfaceData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_surface_preview_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getSurfacePreviewData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_data(FluidSimulation* obj, 
                                                    char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_foam_data(FluidSimulation* obj, 
                                                    char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseFoamData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_bubble_data(FluidSimulation* obj, 
                                                    char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseBubbleData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_diffuse_spray_data(FluidSimulation* obj, 
                                                          char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getDiffuseSprayData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_fluid_particle_data(FluidSimulation* obj, 
                                                           char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getFluidParticleData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_internal_obstacle_mesh_data(FluidSimulation* obj, 
                                                                   char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getInternalObstacleMeshData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void FluidSimulation_get_logfile_data(FluidSimulation* obj, 
                                                    char *c_data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            std::vector<char> *data = obj->getLogFileData();
            std::memcpy(c_data, data->data(), data->size());
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL FluidSimulationFrameStats FluidSimulation_get_frame_stats_data(FluidSimulation* obj, 
                                                                             int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &FluidSimulation::getFrameStatsData, err
        );
    }

    EXPORTDLL void FluidSimulation_get_marker_particle_position_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getMarkerParticlePositionData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_get_marker_particle_velocity_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getMarkerParticleVelocityData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_position_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getDiffuseParticlePositionData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_velocity_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getDiffuseParticleVelocityData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_lifetime_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getDiffuseParticleLifetimeData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_type_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getDiffuseParticleTypeData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_get_diffuse_particle_id_data(FluidSimulation* obj, 
                                                                     char *c_data, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::getDiffuseParticleIdData, c_data, err
        );
    }

    EXPORTDLL void FluidSimulation_load_marker_particle_data(FluidSimulation* obj, 
                                                             FluidSimulationMarkerParticleData data, 
                                                             int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::loadMarkerParticleData, data, err
        );
    }

    EXPORTDLL void FluidSimulation_load_diffuse_particle_data(FluidSimulation* obj, 
                                                              FluidSimulationDiffuseParticleData data, 
                                                              int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &FluidSimulation::loadDiffuseParticleData, data, err
        );
    }
}
