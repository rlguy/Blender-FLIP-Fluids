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

#include "../forcefieldcurve.h"
#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

extern "C" {

    EXPORTDLL ForceFieldCurve* ForceFieldCurve_new(int *err) {

        *err = CBindings::SUCCESS;
        ForceFieldCurve *ffs = nullptr;
        try {
            ffs = new ForceFieldCurve();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return ffs;
    }

    EXPORTDLL void ForceFieldCurve_destroy(ForceFieldCurve *obj) {
        delete obj;
    }

    EXPORTDLL float ForceFieldCurve_get_flow_strength(ForceFieldCurve* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceFieldCurve::getFlowStrength, err
        );
    }

    EXPORTDLL void ForceFieldCurve_set_flow_strength(ForceFieldCurve* obj, float s, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceFieldCurve::setFlowStrength, s, err
        );
    }

    EXPORTDLL float ForceFieldCurve_get_spin_strength(ForceFieldCurve* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceFieldCurve::getSpinStrength, err
        );
    }

    EXPORTDLL void ForceFieldCurve_set_spin_strength(ForceFieldCurve* obj, float s, int *err) {
        CBindings::safe_execute_method_void_1param(
            obj, &ForceFieldCurve::setSpinStrength, s, err
        );
    }

    EXPORTDLL void ForceFieldCurve_enable_endcaps(ForceFieldCurve* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceFieldCurve::enableEndCaps, err
        );
    }

    EXPORTDLL void ForceFieldCurve_disable_endcaps(ForceFieldCurve* obj, int *err) {
        CBindings::safe_execute_method_void_0param(
            obj, &ForceFieldCurve::disableEndCaps, err
        );
    }

    EXPORTDLL int ForceFieldCurve_is_endcaps_enabled(ForceFieldCurve* obj, int *err) {
        return CBindings::safe_execute_method_ret_0param(
            obj, &ForceFieldCurve::isEndCapsEnabled, err
        );
    }
    
}