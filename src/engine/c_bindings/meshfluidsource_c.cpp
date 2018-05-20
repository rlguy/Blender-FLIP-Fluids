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

#include "../meshfluidsource.h"
#include "../meshutils.h"
#include "../trianglemesh.h"
#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

extern "C" {

    EXPORTDLL MeshFluidSource* MeshFluidSource_new_from_mesh(
            int i, int j, int k, double dx, 
            MeshUtils::TriangleMesh_t *mesh_data, int *err) {

        *err = CBindings::SUCCESS;
        MeshFluidSource *source = nullptr;
        try {
            TriangleMesh mesh;
            MeshUtils::structToTriangleMesh(*mesh_data, mesh);
            source = new MeshFluidSource(i, j, k, dx, mesh);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return source;
    }

    EXPORTDLL MeshFluidSource* MeshFluidSource_new_from_meshes(
            int i, int j, int k, double dx, 
            MeshUtils::TriangleMesh_t *mesh_data, int num_meshes, int *err) {

        *err = CBindings::SUCCESS;
        MeshFluidSource *source = nullptr;
        try {
            std::vector<TriangleMesh> meshes;
            for (int idx = 0; idx < num_meshes; idx++) {
                TriangleMesh mesh;
                MeshUtils::structToTriangleMesh(mesh_data[idx], mesh);
                meshes.push_back(mesh);
            }
            source = new MeshFluidSource(i, j, k, dx, meshes);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return source;
    }

    EXPORTDLL MeshFluidSource* MeshFluidSource_new_from_meshes_translations(
            int i, int j, int k, double dx, 
            MeshUtils::TriangleMesh_t *mesh_data, 
            MeshUtils::TriangleMesh_t *translation_data, int num_meshes, int *err) {

        *err = CBindings::SUCCESS;
        MeshFluidSource *source = nullptr;
        try {
            std::vector<TriangleMesh> meshes;
            std::vector<TriangleMesh> translations;
            for (int idx = 0; idx < num_meshes; idx++) {
                TriangleMesh mesh;
                TriangleMesh translation;
                MeshUtils::structToTriangleMesh(mesh_data[idx], mesh);
                MeshUtils::structToTriangleMesh(translation_data[idx], translation);
                meshes.push_back(mesh);
                translations.push_back(translation);
            }
            source = new MeshFluidSource(i, j, k, dx, meshes, translations);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return source;
    }

    EXPORTDLL void MeshFluidSource_destroy(MeshFluidSource *obj) {
        delete obj;
    }

    EXPORTDLL void MeshFluidSource_enable(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::enable, err
        );
    }

    EXPORTDLL void MeshFluidSource_disable(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::disable, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_enabled(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isEnabled, err
        );
    }

    EXPORTDLL int MeshFluidSource_get_substep_emissions(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::getSubstepEmissions, err
        );
    }

    EXPORTDLL void MeshFluidSource_set_substep_emissions(MeshFluidSource* obj, int n, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshFluidSource::setSubstepEmissions, n, err
        );
    }

    EXPORTDLL void MeshFluidSource_set_inflow(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::setInflow, err
        );
    }

    EXPORTDLL void MeshFluidSource_set_outflow(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::setOutflow, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_inflow(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isInflow, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_outflow(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isOutflow, err
        );
    }

    EXPORTDLL void MeshFluidSource_enable_fluid_outflow(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::enableFluidOutflow, err
        );
    }

    EXPORTDLL void MeshFluidSource_disable_fluid_outflow(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::disableFluidOutflow, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_fluid_outflow_enabled(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isFluidOutflowEnabled, err
        );
    }

    EXPORTDLL void MeshFluidSource_enable_diffuse_outflow(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::enableDiffuseOutflow, err
        );
    }

    EXPORTDLL void MeshFluidSource_disable_diffuse_outflow(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::disableDiffuseOutflow, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_diffuse_outflow_enabled(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isDiffuseOutflowEnabled, err
        );
    }

    EXPORTDLL Vector3_t MeshFluidSource_get_velocity(MeshFluidSource* obj, int *err) {
        vmath::vec3 velocity = CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::getVelocity, err
        );
        return CBindings::to_struct(velocity);
    }

    EXPORTDLL void MeshFluidSource_set_velocity(MeshFluidSource* obj,
                                                double vx, double vy, double vz,
                                                int *err) {
        vmath::vec3 velocity(vx, vy, vz);
        CBindings::safe_execute_method_void_1param(
            obj, &MeshFluidSource::setVelocity, velocity, err
        );
    }

    EXPORTDLL void MeshFluidSource_enable_append_object_velocity(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::enableAppendObjectVelocity, err
        );
    }

    EXPORTDLL void MeshFluidSource_disable_append_object_velocity(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::disableAppendObjectVelocity, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_append_object_velocity_enabled(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isAppendObjectVelocityEnabled, err
        );
    }

    EXPORTDLL float MeshFluidSource_get_object_velocity_influence(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::getObjectVelocityInfluence, err
        );
    }

    EXPORTDLL void MeshFluidSource_set_object_velocity_influence(MeshFluidSource* obj, 
                                                                 float value,
                                                                 int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshFluidSource::setObjectVelocityInfluence, value, err
        );
    }

    EXPORTDLL void MeshFluidSource_enable_rigid_mesh(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::enableRigidMesh, err
        );
    }

    EXPORTDLL void MeshFluidSource_disable_rigid_mesh(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::disableRigidMesh, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_rigid_mesh_enabled(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isRigidMeshEnabled, err
        );
    }

    EXPORTDLL void MeshFluidSource_outflow_inverse(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::outflowInverse, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_outflow_inversed(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isOutflowInversed, err
        );
    }

}
