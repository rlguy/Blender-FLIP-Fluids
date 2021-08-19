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

#include "../meshobject.h"
#include "../meshutils.h"
#include "../trianglemesh.h"
#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

extern "C" {

    EXPORTDLL MeshObject* MeshObject_new(int i, int j, int k, double dx, int *err) {

        *err = CBindings::SUCCESS;
        MeshObject *obstacle = nullptr;
        try {
            obstacle = new MeshObject(i, j, k, dx);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return obstacle;
    }

    EXPORTDLL void MeshObject_destroy(MeshObject *obj) {
        delete obj;
    }

    EXPORTDLL void MeshObject_update_mesh_static(
            MeshObject* obj, 
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

    EXPORTDLL void MeshObject_update_mesh_animated(
            MeshObject* obj, 
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

    EXPORTDLL void MeshObject_enable(MeshObject* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshObject::enable, err
        );
    }

    EXPORTDLL void MeshObject_disable(MeshObject* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshObject::disable, err
        );
    }

    EXPORTDLL int MeshObject_is_enabled(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::isEnabled, err
        );
    }

    EXPORTDLL void MeshObject_inverse(MeshObject* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshObject::inverse, err
        );
    }

    EXPORTDLL int MeshObject_is_inversed(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::isInversed, err
        );
    }

    EXPORTDLL float MeshObject_get_friction(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getFriction, err
        );
    }

    EXPORTDLL void MeshObject_set_friction(MeshObject* obj, float f, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setFriction, f, err
        );
    }

    EXPORTDLL float MeshObject_get_whitewater_influence(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getWhitewaterInfluence, err
        );
    }

    EXPORTDLL void MeshObject_set_whitewater_influence(MeshObject* obj, float value, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setWhitewaterInfluence, value, err
        );
    }

    EXPORTDLL float MeshObject_get_dust_emission_strength(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getDustEmissionStrength, err
        );
    }

    EXPORTDLL void MeshObject_set_dust_emission_strength(MeshObject* obj, float value, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setDustEmissionStrength, value, err
        );
    }

    EXPORTDLL float MeshObject_get_sheeting_strength(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getSheetingStrength, err
        );
    }

    EXPORTDLL void MeshObject_set_sheeting_strength(MeshObject* obj, float value, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setSheetingStrength, value, err
        );
    }

    EXPORTDLL float MeshObject_get_mesh_expansion(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getMeshExpansion, err
        );
    }

    EXPORTDLL void MeshObject_set_mesh_expansion(MeshObject* obj, 
                                                 float ex,
                                                 int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setMeshExpansion, ex, err
        );
    }

    EXPORTDLL void MeshObject_enable_append_object_velocity(MeshObject* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshObject::enableAppendObjectVelocity, err
        );
    }

    EXPORTDLL void MeshObject_disable_append_object_velocity(MeshObject* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &MeshObject::disableAppendObjectVelocity, err
        );
    }

    EXPORTDLL int MeshObject_is_append_object_velocity_enabled(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::isAppendObjectVelocityEnabled, err
        );
    }

    EXPORTDLL float MeshObject_get_object_velocity_influence(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getObjectVelocityInfluence, err
        );
    }

    EXPORTDLL void MeshObject_set_object_velocity_influence(MeshObject* obj, 
                                                            float value,
                                                            int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setObjectVelocityInfluence, value, err
        );
    }

    EXPORTDLL int MeshObject_get_source_id(MeshObject* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getSourceID, err
        );
    }

    EXPORTDLL void MeshObject_set_source_id(MeshObject* obj, int id, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setSourceID, id, err
        );
    }

    EXPORTDLL Vector3_t MeshObject_get_source_color(MeshObject* obj, int *err) {
        vmath::vec3 color = CBindings::safe_execute_method_ret_0param(
            obj, &MeshObject::getSourceColor, err
        );
        return CBindings::to_struct(color);
    }

    EXPORTDLL void MeshObject_set_source_color(MeshObject* obj,
                                             double r, double g, double b,
                                             int *err) {
        vmath::vec3 color(r, g, b);
        CBindings::safe_execute_method_void_1param(
            obj, &MeshObject::setSourceColor, color, err
        );
    }
}