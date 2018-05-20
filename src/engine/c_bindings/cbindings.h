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

#ifndef CBINDINGS_H
#define CBINDINGS_H

#include <exception>
#include <string>

#include "../vmath.h"
#include "../aabb.h"
#include "vector3_c.h"
#include "aabb_c.h"
#include "../markerparticle.h"
#include "../diffuseparticle.h"
#include "markerparticle_c.h"
#include "diffuseparticle_c.h"

namespace CBindings {

extern int SUCCESS;
extern int FAIL;
extern char CBINDINGS_ERROR_MESSAGE[4096];

extern void set_error_message(std::exception &ex);
extern char* get_error_message();

template<class CLASS>
void safe_execute_method_void_0param(CLASS *obj, void (CLASS::*funcptr)(void), int *err) {
    *err = SUCCESS;
    try {
        (obj->*funcptr)();
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }
}

template<typename T, class CLASS>
T safe_execute_method_ret_0param(CLASS *obj, T (CLASS::*funcptr)(void), int *err) {
    *err = SUCCESS;
    T result = T();
    try {
        result = (obj->*funcptr)();
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }

    return result;
}

template<typename T, class CLASS>
void safe_execute_method_void_1param(CLASS *obj, void (CLASS::*funcptr)(T), T param, int *err) {
    *err = SUCCESS;
    try {
        (obj->*funcptr)(param);
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }
}

template<typename T, typename RT, class CLASS>
RT safe_execute_method_ret_1param(CLASS *obj, RT (CLASS::*funcptr)(T), T param, int *err) {
    *err = SUCCESS;
    RT result = RT();
    try {
        result = (obj->*funcptr)(param);
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }

    return result;
}

template<typename T, class CLASS>
void safe_execute_method_void_2param(CLASS *obj,
                       void (CLASS::*funcptr)(T, T),
                       T param1, T param2, int *err) {
    *err = SUCCESS;
    try {
        (obj->*funcptr)(param1, param2);
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }
}

template<typename T, class RT, class CLASS>
RT safe_execute_method_ret_2param(CLASS *obj,
                       RT (CLASS::*funcptr)(T, T),
                       T param1, T param2, int *err) {
    RT result = RT();
    *err = SUCCESS;
    try {
        result = (obj->*funcptr)(param1, param2);
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }

    return result;
}

template<typename T, class CLASS>
void safe_execute_method_void_3param(CLASS *obj,
                         void (CLASS::*funcptr)(T, T, T),
                         T param1, T param2, T param3, int *err) {
    *err = SUCCESS;
    try {
        (obj->*funcptr)(param1, param2, param3);
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }
}

template<typename T, class RT, class CLASS>
RT safe_execute_method_ret_3param(CLASS *obj,
                       RT (CLASS::*funcptr)(T, T, T),
                       T param1, T param2, T param3, int *err) {
    RT result = RT();
    *err = SUCCESS;
    try {
        result = (obj->*funcptr)(param1, param2, param3);
    } catch (std::exception &ex) {
        CBindings::set_error_message(ex);
        *err = FAIL;
    }

    return result;
}

Vector3_t to_struct(vmath::vec3 v);
vmath::vec3 to_class(Vector3_t v);
AABB_t to_struct(AABB b);
AABB to_class(AABB_t v);
MarkerParticle_t to_struct(MarkerParticle p);
MarkerParticle to_class(MarkerParticle_t p);
DiffuseParticle_t to_struct(DiffuseParticle p);
DiffuseParticle to_class(DiffuseParticle_t p);

}

#endif