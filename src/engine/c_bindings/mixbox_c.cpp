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

#include <stddef.h>

#include "../mixbox/mixbox.h"
#include "vector3_c.h"
#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif


struct MixboxLutData {
    int size = 0;
    char *data;
};


extern "C" {

    EXPORTDLL void Mixbox_initialize(MixboxLutData data, int *err) {
        *err = CBindings::SUCCESS;
        try {
            mixbox_initialize(data.data, data.size);
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }

    EXPORTDLL int Mixbox_is_initialized(int *err) {
        *err = CBindings::SUCCESS;
        int result = 0;
        try {
            result = (int)mixbox_is_initialized();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return result;
    }

    EXPORTDLL Vector3_t Mixbox_lerp_srgb32f(float r1, float g1, float b1, float r2, float g2, float b2, float t, int *err) {
        *err = CBindings::SUCCESS;
        vmath::vec3 color;
        try {
            float r, g, b;
            mixbox_lerp_srgb32f(r1, g1, b1, r2, g2, b2, t, &r, &g, &b);
            color.x = r;
            color.y = g;
            color.z = b;
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return CBindings::to_struct(color);
    }

}
