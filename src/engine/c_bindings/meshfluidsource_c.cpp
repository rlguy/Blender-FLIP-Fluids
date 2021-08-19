/*
MIT License

Copyright (C) 2021 Ryan L. Guy

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

    EXPORTDLL MeshFluidSource* MeshFluidSource_new(int i, int j, int k, double dx, int *err) {

        *err = CBindings::SUCCESS;
        MeshFluidSource *source = nullptr;
        try {
            source = new MeshFluidSource(i, j, k, dx);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return source;
    }

    EXPORTDLL void MeshFluidSource_destroy(MeshFluidSource *obj) {
        delete obj;
    }

    EXPORTDLL void MeshFluidSource_update_mesh_static(
            MeshFluidSource* obj, 
            MeshUtils::TriangleMesh_t mesh_data, int *err) {

        *err = CBindings::SUCCESS;
        try {
            TriangleMesh mesh;
            MeshUtils::structToTriangleMesh(mesh_data, mesh);
            obj->updateMeshStatic(mesh);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL void MeshFluidSource_update_mesh_animated(
            MeshFluidSource* obj, 
            MeshUtils::TriangleMesh_t mesh_data_previous,
            MeshUtils::TriangleMesh_t mesh_data_current,
            MeshUtils::TriangleMesh_t mesh_data_next, int *err) {

        *err = CBindings::SUCCESS;
        try {
            TriangleMesh meshPrevious, meshCurrent, meshNext;
            MeshUtils::structToTriangleMesh(mesh_data_previous, meshPrevious);
            MeshUtils::structToTriangleMesh(mesh_data_current, meshCurrent);
            MeshUtils::structToTriangleMesh(mesh_data_next, meshNext);
            obj->updateMeshAnimated(meshPrevious, meshCurrent, meshNext);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
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

    EXPORTDLL void MeshFluidSource_enable_constrained_fluid_velocity(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::enableConstrainedFluidVelocity, err
        );
    }

    EXPORTDLL void MeshFluidSource_disable_constrained_fluid_velocity(MeshFluidSource* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshFluidSource::disableConstrainedFluidVelocity, err
        );
    }

    EXPORTDLL int MeshFluidSource_is_constrained_fluid_velocity_enabled(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::isConstrainedFluidVelocityEnabled, err
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

    EXPORTDLL int MeshFluidSource_get_source_id(MeshFluidSource* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::getSourceID, err
        );
    }

    EXPORTDLL void MeshFluidSource_set_source_id(MeshFluidSource* obj, int id, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshFluidSource::setSourceID, id, err
        );
    }

    EXPORTDLL Vector3_t MeshFluidSource_get_source_color(MeshFluidSource* obj, int *err) {
        vmath::vec3 color = CBindings::safe_execute_method_ret_0param(
            obj, &MeshFluidSource::getSourceColor, err
        );
        return CBindings::to_struct(color);
    }

    EXPORTDLL void MeshFluidSource_set_source_color(MeshFluidSource* obj,
                                             double r, double g, double b,
                                             int *err) {
        vmath::vec3 color(r, g, b);
        CBindings::safe_execute_method_void_1param(
            obj, &MeshFluidSource::setSourceColor, color, err
        );
    }

}
