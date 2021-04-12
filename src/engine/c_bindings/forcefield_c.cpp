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

#include "../forcefield.h"
#include "../meshutils.h"
#include "../trianglemesh.h"
#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

extern "C" {

    EXPORTDLL void ForceField_update_mesh_static(
            ForceField* obj, 
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

    EXPORTDLL void ForceField_update_mesh_animated(
            ForceField* obj, 
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

    EXPORTDLL void ForceField_enable(ForceField* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceField::enable, err
        );
    }

    EXPORTDLL void ForceField_disable(ForceField* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceField::disable, err
        );
    }

    EXPORTDLL int ForceField_is_enabled(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::isEnabled, err
        );
    }
    
    EXPORTDLL float ForceField_get_strength(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getStrength, err
        );
    }

    EXPORTDLL void ForceField_set_strength(ForceField* obj, float s, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setStrength, s, err
        );
    }

    EXPORTDLL float ForceField_get_falloff_power(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getFalloffPower, err
        );
    }

    EXPORTDLL void ForceField_set_falloff_power(ForceField* obj, float p, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setFalloffPower, p, err
        );
    }

    EXPORTDLL float ForceField_get_max_force_limit_factor(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getMaxForceLimitFactor, err
        );
    }

    EXPORTDLL void ForceField_set_max_force_limit_factor(ForceField* obj, float factor, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setMaxForceLimitFactor, factor, err
        );
    }

    EXPORTDLL void ForceField_enable_min_distance(ForceField* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceField::enableMinDistance, err
        );
    }

    EXPORTDLL void ForceField_disable_min_distance(ForceField* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceField::disableMinDistance, err
        );
    }

    EXPORTDLL int ForceField_is_min_distance_enabled(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::isMinDistanceEnabled, err
        );
    }

    EXPORTDLL float ForceField_get_min_distance(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getMinDistance, err
        );
    }

    EXPORTDLL void ForceField_set_min_distance(ForceField* obj, float d, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setMinDistance, d, err
        );
    }

    EXPORTDLL void ForceField_enable_max_distance(ForceField* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceField::enableMaxDistance, err
        );
    }

    EXPORTDLL void ForceField_disable_max_distance(ForceField* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceField::disableMaxDistance, err
        );
    }

    EXPORTDLL int ForceField_is_max_distance_enabled(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::isMaxDistanceEnabled, err
        );
    }

    EXPORTDLL float ForceField_get_max_distance(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getMaxDistance, err
        );
    }

    EXPORTDLL void ForceField_set_max_distance(ForceField* obj, float d, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setMaxDistance, d, err
        );
    }

    EXPORTDLL float ForceField_get_gravity_scale(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getGravityScale, err
        );
    }

    EXPORTDLL void ForceField_set_gravity_scale(ForceField* obj, float s, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setGravityScale, s, err
        );
    }

    EXPORTDLL float ForceField_get_gravity_scale_width(ForceField* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceField::getGravityScaleWidth, err
        );
    }

    EXPORTDLL void ForceField_set_gravity_scale_width(ForceField* obj, float w, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceField::setGravityScaleWidth, w, err
        );
    }
}