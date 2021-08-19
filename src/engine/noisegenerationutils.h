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


#ifndef FLUIDENGINE_NOISEGENERATIONUTILS_H
#define FLUIDENGINE_NOISEGENERATIONUTILS_H

#include "vmath.h"

namespace NoiseGenerationUtils {

    struct NoiseSample {
        float value = 0.0f;
        vmath::vec3 derivative;
    };

    extern int _hashValues[];
    extern int _hasValuesMask;

    extern int _gradients1D[];
    extern int _gradients1DMask;

    extern vmath::vec3 _gradients2D[];
    extern int _gradients2DMask;
    extern float _sqrt2;

    extern vmath::vec3 _gradients3D[];
    extern int _gradients3DMask;

    inline int _fmodint(float value, float mod) {
        return (int)std::fmod(value, mod);
    }

    inline float _dot2D(vmath::vec3 vec, float x, float y) {
        return vec.x * x + vec.y * y;
    }

    inline float _dot3D(vmath::vec3 vec, float x, float y, float z) {
        return vec.x * x + vec.y * y + vec.z * z;
    }

    inline float _smooth(float t) {
        return t * t * t * (t * (t * 6.0f - 15.0f) + 10.0f);
    }

    inline float _smoothDerivative(float t) {
        return 30.0f * t * t * (t * (t - 2.0f) + 1.0f);
    }

    inline float normalizePerlinValue(float value) {
        return value * 0.5 + 0.5;
    }

    namespace Value1D {
        extern float value(vmath::vec3 p, float frequency);
        extern vmath::vec3 derivative(vmath::vec3 p, float frequency);
        extern NoiseSample sample(vmath::vec3 p, float frequency);
    }

    namespace Value2D {
        extern float value(vmath::vec3 p, float frequency);
        extern vmath::vec3 derivative(vmath::vec3 p, float frequency);
        extern NoiseSample sample(vmath::vec3 p, float frequency);
    }

    namespace Value3D {
        extern float value(vmath::vec3 p, float frequency);
        extern vmath::vec3 derivative(vmath::vec3 p, float frequency);
        extern NoiseSample sample(vmath::vec3 p, float frequency);
    }

    namespace Perlin1D {
        extern float value(vmath::vec3 p, float frequency);
        extern vmath::vec3 derivative(vmath::vec3 p, float frequency);
        extern NoiseSample sample(vmath::vec3 p, float frequency);
    }

    namespace Perlin2D {
        extern float value(vmath::vec3 p, float frequency);
        extern vmath::vec3 derivative(vmath::vec3 p, float frequency);
        extern NoiseSample sample(vmath::vec3 p, float frequency);
    }

    namespace Perlin3D {
        extern float value(vmath::vec3 p, float frequency);
        extern vmath::vec3 derivative(vmath::vec3 p, float frequency);
        extern NoiseSample sample(vmath::vec3 p, float frequency);
    }

    namespace Sum {
        extern float value(float (*noiseMethod)(vmath::vec3 p, float frequency), 
                           vmath::vec3 p, float frequency, int octaves, float lacunarity, float persistence);
        extern vmath::vec3 derivative(vmath::vec3 (*noiseMethod)(vmath::vec3 p, float frequency), 
                                      vmath::vec3 p, float frequency, int octaves, float lacunarity, float persistence);
        extern NoiseSample sample(NoiseSample (*noiseMethod)(vmath::vec3 p, float frequency), 
                                  vmath::vec3 p, float frequency, int octaves, float lacunarity, float persistence);
    }

    extern void test();

}

#endif