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

/*
    Noise generation methods adapted from Catlike Coding's Unity Tutorial resources:
        "Noise, being a pseudorandom artist" - https://catlikecoding.com/unity/tutorials/noise/
        "Noise Derivatives, going with the flow" - https://catlikecoding.com/unity/tutorials/noise-derivatives/
*/

#include "noisegenerationutils.h"

namespace NoiseGenerationUtils {

    int _hashValues[] = {
        151,160,137, 91, 90, 15,131, 13,201, 95, 96, 53,194,233,  7,225,
        140, 36,103, 30, 69,142,  8, 99, 37,240, 21, 10, 23,190,  6,148,
        247,120,234, 75,  0, 26,197, 62, 94,252,219,203,117, 35, 11, 32,
         57,177, 33, 88,237,149, 56, 87,174, 20,125,136,171,168, 68,175,
         74,165, 71,134,139, 48, 27,166, 77,146,158,231, 83,111,229,122,
         60,211,133,230,220,105, 92, 41, 55, 46,245, 40,244,102,143, 54,
         65, 25, 63,161,  1,216, 80, 73,209, 76,132,187,208, 89, 18,169,
        200,196,135,130,116,188,159, 86,164,100,109,198,173,186,  3, 64,
         52,217,226,250,124,123,  5,202, 38,147,118,126,255, 82, 85,212,
        207,206, 59,227, 47, 16, 58, 17,182,189, 28, 42,223,183,170,213,
        119,248,152,  2, 44,154,163, 70,221,153,101,155,167, 43,172,  9,
        129, 22, 39,253, 19, 98,108,110, 79,113,224,232,178,185,112,104,
        218,246, 97,228,251, 34,242,193,238,210,144, 12,191,179,162,241,
         81, 51,145,235,249, 14,239,107, 49,192,214, 31,181,199,106,157,
        184, 84,204,176,115,121, 50, 45,127,  4,150,254,138,236,205, 93,
        222,114, 67, 29, 24, 72,243,141,128,195, 78, 66,215, 61,156,180,

        151,160,137, 91, 90, 15,131, 13,201, 95, 96, 53,194,233,  7,225,
        140, 36,103, 30, 69,142,  8, 99, 37,240, 21, 10, 23,190,  6,148,
        247,120,234, 75,  0, 26,197, 62, 94,252,219,203,117, 35, 11, 32,
         57,177, 33, 88,237,149, 56, 87,174, 20,125,136,171,168, 68,175,
         74,165, 71,134,139, 48, 27,166, 77,146,158,231, 83,111,229,122,
         60,211,133,230,220,105, 92, 41, 55, 46,245, 40,244,102,143, 54,
         65, 25, 63,161,  1,216, 80, 73,209, 76,132,187,208, 89, 18,169,
        200,196,135,130,116,188,159, 86,164,100,109,198,173,186,  3, 64,
         52,217,226,250,124,123,  5,202, 38,147,118,126,255, 82, 85,212,
        207,206, 59,227, 47, 16, 58, 17,182,189, 28, 42,223,183,170,213,
        119,248,152,  2, 44,154,163, 70,221,153,101,155,167, 43,172,  9,
        129, 22, 39,253, 19, 98,108,110, 79,113,224,232,178,185,112,104,
        218,246, 97,228,251, 34,242,193,238,210,144, 12,191,179,162,241,
         81, 51,145,235,249, 14,239,107, 49,192,214, 31,181,199,106,157,
        184, 84,204,176,115,121, 50, 45,127,  4,150,254,138,236,205, 93,
        222,114, 67, 29, 24, 72,243,141,128,195, 78, 66,215, 61,156,180
        };
    int _hashValuesMask = 255;

    int _gradients1D[] = {-1, 1};
    int _gradients1DMask = 1;

    vmath::vec3 _gradients2D[] = {
        vmath::vec3( 1.0f,  0.0f, 0.0f),
        vmath::vec3(-1.0f,  0.0f, 0.0f),
        vmath::vec3( 0.0f,  1.0f, 0.0f),
        vmath::vec3( 0.0f, -1.0f, 0.0f),
        vmath::vec3( 1.0f,  1.0f, 0.0f).normalize(),
        vmath::vec3(-1.0f,  1.0f, 0.0f).normalize(),
        vmath::vec3( 1.0f, -1.0f, 0.0f).normalize(),
        vmath::vec3(-1.0f, -1.0f, 0.0f).normalize()
        };
    int _gradients2DMask = 7;
    float _sqrt2 = 1.41421356237;

    vmath::vec3 _gradients3D[] = {
        vmath::vec3( 1.0, 1.0, 0.0),
        vmath::vec3(-1.0, 1.0, 0.0),
        vmath::vec3( 1.0,-1.0, 0.0),
        vmath::vec3(-1.0,-1.0, 0.0),
        vmath::vec3( 1.0, 0.0, 1.0),
        vmath::vec3(-1.0, 0.0, 1.0),
        vmath::vec3( 1.0, 0.0,-1.0),
        vmath::vec3(-1.0, 0.0,-1.0),
        vmath::vec3( 0.0, 1.0, 1.0),
        vmath::vec3( 0.0,-1.0, 1.0),
        vmath::vec3( 0.0, 1.0,-1.0),
        vmath::vec3( 0.0,-1.0,-1.0),
        vmath::vec3( 1.0, 1.0, 0.0),
        vmath::vec3(-1.0, 1.0, 0.0),
        vmath::vec3( 0.0,-1.0, 1.0),
        vmath::vec3( 0.0,-1.0,-1.0)
        };
    int _gradients3DMask = 15;


    namespace Value1D {

        float value(vmath::vec3 p, float frequency) {
            p *= frequency;
            int i0 = (int)std::floor(p.x);
            float t = p.x - i0;
            i0 = _fmodint(i0, _hashValuesMask);
            int i1 = i0 + 1;

            int h0 = _hashValues[i0];
            int h1 = _hashValues[i1];
            int a = h0;
            int b = h1 - h0;

            t = _smooth(t);

            return (a + b * t) * (1.0f / _hashValuesMask);;
        }

        vmath::vec3 derivative(vmath::vec3 p, float frequency) {
            p *= frequency;
            int i0 = (int)std::floor(p.x);
            float t = p.x - i0;
            i0 = _fmodint(i0, _hashValuesMask);
            int i1 = i0 + 1;

            int h0 = _hashValues[i0];
            int h1 = _hashValues[i1];
            int b = h1 - h0;

            t = _smooth(t);
            float dt = _smoothDerivative(t);

            return vmath::vec3(b * dt * frequency * (1.0f / _hashValuesMask), 0.0f, 0.0f);
        }

        NoiseSample sample(vmath::vec3 p, float frequency) {
            p *= frequency;
            int i0 = (int)std::floor(p.x);
            float t = p.x - i0;
            i0 = _fmodint(i0, _hashValuesMask);
            int i1 = i0 + 1;

            int h0 = _hashValues[i0];
            int h1 = _hashValues[i1];
            int a = h0;
            int b = h1 - h0;

            t = _smooth(t);
            float dt = _smoothDerivative(t);
            
            NoiseSample sample;
            sample.value = (a + b * t) * (1.0f / _hashValuesMask);
            sample.derivative = vmath::vec3(b * dt * frequency * (1.0f / _hashValuesMask), 0.0f, 0.0f);

            return sample;
        }

    }


    namespace Value2D {

        float value(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            float tx = p.x - ix0;
            float ty = p.y - iy0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];

            int a = h00;
            int b = h10 - h00;
            int c = h01 - h00;
            int d = h11 - h01 - h10 + h00;

            tx = _smooth(tx);
            ty = _smooth(ty);

            return (a + b * tx + (c + d * tx) * ty) * (1.0f / _hashValuesMask);
        }

        vmath::vec3 derivative(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            float tx = p.x - ix0;
            float ty = p.y - iy0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];

            int b = h10 - h00;
            int c = h01 - h00;
            int d = h11 - h01 - h10 + h00;

            tx = _smooth(tx);
            ty = _smooth(ty);
            float dtx = _smoothDerivative(tx);
            float dty = _smoothDerivative(ty);

            return vmath::vec3(
                        ((b + d * ty) * dtx) * frequency * (1.0f / _hashValuesMask),
                        ((c + d * tx) * dty) * frequency * (1.0f / _hashValuesMask),
                        0.0f
                    );
        }

        NoiseSample sample(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            float tx = p.x - ix0;
            float ty = p.y - iy0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];

            int a = h00;
            int b = h10 - h00;
            int c = h01 - h00;
            int d = h11 - h01 - h10 + h00;

            tx = _smooth(tx);
            ty = _smooth(ty);
            float dtx = _smoothDerivative(tx);
            float dty = _smoothDerivative(ty);

            NoiseSample sample;
            sample.value = (a + b * tx + (c + d * tx) * ty) * (1.0f / _hashValuesMask);
            sample.derivative = vmath::vec3(
                        ((b + d * ty) * dtx) * frequency * (1.0f / _hashValuesMask),
                        ((c + d * tx) * dty) * frequency * (1.0f / _hashValuesMask),
                        0.0f
                    );

            return sample;
        }

    }


    namespace Value3D {

        float value(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            int iz0 = (int)std::floor(p.z);
            float tx = p.x - ix0;
            float ty = p.y - iy0;
            float tz = p.z - iz0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            iz0 = _fmodint(iz0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;
            int iz1 = iz0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];
            int h000 = _hashValues[h00 + iz0];
            int h100 = _hashValues[h10 + iz0];
            int h010 = _hashValues[h01 + iz0];
            int h110 = _hashValues[h11 + iz0];
            int h001 = _hashValues[h00 + iz1];
            int h101 = _hashValues[h10 + iz1];
            int h011 = _hashValues[h01 + iz1];
            int h111 = _hashValues[h11 + iz1];

            int a = h000;
            int b = h100 - h000;
            int c = h010 - h000;
            int d = h001 - h000;
            int e = h110 - h010 - h100 + h000;
            int f = h101 - h001 - h100 + h000;
            int g = h011 - h001 - h010 + h000;
            int h = h111 - h011 - h101 + h001 - h110 + h010 + h100 - h000;

            tx = _smooth(tx);
            ty = _smooth(ty);
            tz = _smooth(tz);

            return (a + b * tx + (c + e * tx) * ty + (d + f * tx + (g + h * tx) * ty) * tz) * (1.0f / _hashValuesMask);
        }

        vmath::vec3 derivative(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            int iz0 = (int)std::floor(p.z);
            float tx = p.x - ix0;
            float ty = p.y - iy0;
            float tz = p.z - iz0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            iz0 = _fmodint(iz0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;
            int iz1 = iz0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];
            int h000 = _hashValues[h00 + iz0];
            int h100 = _hashValues[h10 + iz0];
            int h010 = _hashValues[h01 + iz0];
            int h110 = _hashValues[h11 + iz0];
            int h001 = _hashValues[h00 + iz1];
            int h101 = _hashValues[h10 + iz1];
            int h011 = _hashValues[h01 + iz1];
            int h111 = _hashValues[h11 + iz1];

            int b = h100 - h000;
            int c = h010 - h000;
            int d = h001 - h000;
            int e = h110 - h010 - h100 + h000;
            int f = h101 - h001 - h100 + h000;
            int g = h011 - h001 - h010 + h000;
            int h = h111 - h011 - h101 + h001 - h110 + h010 + h100 - h000;

            tx = _smooth(tx);
            ty = _smooth(ty);
            tz = _smooth(tz);
            float dtx = _smoothDerivative(tx);
            float dty = _smoothDerivative(ty);
            float dtz = _smoothDerivative(tz);

            return vmath::vec3(
                        ((b + e * ty + (f + h * ty) * tz) * dtx) * frequency * (1.0f / _hashValuesMask),
                        ((c + e * tx + (g + h * tx) * tz) * dty) * frequency * (1.0f / _hashValuesMask),
                        ((d + f * tx + (g + h * tx) * ty) * dtz) * frequency * (1.0f / _hashValuesMask)
                    );
        }

        NoiseSample sample(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            int iz0 = (int)std::floor(p.z);
            float tx = p.x - ix0;
            float ty = p.y - iy0;
            float tz = p.z - iz0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            iz0 = _fmodint(iz0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;
            int iz1 = iz0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];
            int h000 = _hashValues[h00 + iz0];
            int h100 = _hashValues[h10 + iz0];
            int h010 = _hashValues[h01 + iz0];
            int h110 = _hashValues[h11 + iz0];
            int h001 = _hashValues[h00 + iz1];
            int h101 = _hashValues[h10 + iz1];
            int h011 = _hashValues[h01 + iz1];
            int h111 = _hashValues[h11 + iz1];

            int a = h000;
            int b = h100 - h000;
            int c = h010 - h000;
            int d = h001 - h000;
            int e = h110 - h010 - h100 + h000;
            int f = h101 - h001 - h100 + h000;
            int g = h011 - h001 - h010 + h000;
            int h = h111 - h011 - h101 + h001 - h110 + h010 + h100 - h000;

            tx = _smooth(tx);
            ty = _smooth(ty);
            tz = _smooth(tz);
            float dtx = _smoothDerivative(tx);
            float dty = _smoothDerivative(ty);
            float dtz = _smoothDerivative(tz);

            NoiseSample sample;
            sample.value = (a + b * tx + (c + e * tx) * ty + (d + f * tx + (g + h * tx) * ty) * tz) * (1.0f / _hashValuesMask);
            sample.derivative = vmath::vec3(
                        ((b + e * ty + (f + h * ty) * tz) * dtx) * frequency * (1.0f / _hashValuesMask),
                        ((c + e * tx + (g + h * tx) * tz) * dty) * frequency * (1.0f / _hashValuesMask),
                        ((d + f * tx + (g + h * tx) * ty) * dtz) * frequency * (1.0f / _hashValuesMask)
                    );

            return sample;
        }

    }


    namespace Perlin1D {

        float value(vmath::vec3 p, float frequency) {
            p *= frequency;
            int i0 = (int)std::floor(p.x);
            float t0 = p.x - i0;
            float t1 = t0 - 1.0;
            i0 = _fmodint(i0, _hashValuesMask);
            int i1 = i0 + 1;

            int g0 = _gradients1D[_hashValues[i0] % _gradients1DMask];
            int g1 = _gradients1D[_hashValues[i1] % _gradients1DMask];

            float v0 = g0 * t0;
            float v1 = g1 * t1;

            float a = v0;
            float b = v1 - v0;

            float t = _smooth(t0);

            return (a + b * t) * 2.0f;;
        }

        vmath::vec3 derivative(vmath::vec3 p, float frequency) {
            p *= frequency;
            int i0 = (int)std::floor(p.x);
            float t0 = p.x - i0;
            float t1 = t0 - 1.0;
            i0 = _fmodint(i0, _hashValuesMask);
            int i1 = i0 + 1;

            int g0 = _gradients1D[_hashValues[i0] % _gradients1DMask];
            int g1 = _gradients1D[_hashValues[i1] % _gradients1DMask];

            float v0 = g0 * t0;
            float v1 = g1 * t1;

            float b = v1 - v0;

            float da = g0;
            float db = g1 - g0;

            float t = _smooth(t0);
            float dt = _smoothDerivative(t0);

            return vmath::vec3(
                        (da + db * t + b * dt) * frequency * 2.0f,
                        0.0f,
                        0.0f
                    );
        }

        NoiseSample sample(vmath::vec3 p, float frequency) {
            p *= frequency;
            int i0 = (int)std::floor(p.x);
            float t0 = p.x - i0;
            float t1 = t0 - 1.0;
            i0 = _fmodint(i0, _hashValuesMask);
            int i1 = i0 + 1;

            int g0 = _gradients1D[_hashValues[i0] % _gradients1DMask];
            int g1 = _gradients1D[_hashValues[i1] % _gradients1DMask];

            float v0 = g0 * t0;
            float v1 = g1 * t1;

            float a = v0;
            float b = v1 - v0;

            float da = g0;
            float db = g1 - g0;

            float t = _smooth(t0);
            float dt = _smoothDerivative(t0);

            NoiseSample sample;
            sample.value = (a + b * t) * 2.0f;
            sample.derivative = vmath::vec3(
                        (da + db * t + b * dt) * frequency * 2.0f,
                        0.0f,
                        0.0f
                    );

            return sample;
        }

    }


    namespace Perlin2D {

        float value(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            float tx0 = p.x - ix0;
            float ty0 = p.y - iy0;
            float tx1 = tx0 - 1.0;
            float ty1 = ty0 - 1.0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            vmath::vec3 g00 = _gradients2D[_hashValues[h0 + iy0] % _gradients2DMask];
            vmath::vec3 g10 = _gradients2D[_hashValues[h1 + iy0] % _gradients2DMask];
            vmath::vec3 g01 = _gradients2D[_hashValues[h0 + iy1] % _gradients2DMask];
            vmath::vec3 g11 = _gradients2D[_hashValues[h1 + iy1] % _gradients2DMask];

            float v00 = _dot2D(g00, tx0, ty0);
            float v10 = _dot2D(g10, tx1, ty0);
            float v01 = _dot2D(g01, tx0, ty1);
            float v11 = _dot2D(g11, tx1, ty1);

            float a = v00;
            float b = v10 - v00;
            float c = v01 - v00;
            float d = v11 - v01 - v10 + v00;

            float tx = _smooth(tx0);
            float ty = _smooth(ty0);

            return (a + b * tx + (c + d * tx) * ty) * _sqrt2;
        }

        vmath::vec3 derivative(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            float tx0 = p.x - ix0;
            float ty0 = p.y - iy0;
            float tx1 = tx0 - 1.0;
            float ty1 = ty0 - 1.0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            vmath::vec3 g00 = _gradients2D[_hashValues[h0 + iy0] % _gradients2DMask];
            vmath::vec3 g10 = _gradients2D[_hashValues[h1 + iy0] % _gradients2DMask];
            vmath::vec3 g01 = _gradients2D[_hashValues[h0 + iy1] % _gradients2DMask];
            vmath::vec3 g11 = _gradients2D[_hashValues[h1 + iy1] % _gradients2DMask];

            float v00 = _dot2D(g00, tx0, ty0);
            float v10 = _dot2D(g10, tx1, ty0);
            float v01 = _dot2D(g01, tx0, ty1);
            float v11 = _dot2D(g11, tx1, ty1);

            float b = v10 - v00;
            float c = v01 - v00;
            float d = v11 - v01 - v10 + v00;

            vmath::vec3 da = g00;
            vmath::vec3 db = g10 - g00;
            vmath::vec3 dc = g01 - g00;
            vmath::vec3 dd = g11 - g01 - g10 + g00;

            float tx = _smooth(tx0);
            float ty = _smooth(ty0);
            float dtx = _smoothDerivative(tx0);
            float dty = _smoothDerivative(ty0);

            vmath::vec3 tempDerivative = da + db * tx + (dc + dd * tx) * ty;

            return vmath::vec3(
                        (tempDerivative.x + (b + d * ty) * dtx) * frequency * _sqrt2,
                        (tempDerivative.y + (c + d * tx) * dty) * frequency * _sqrt2,
                        0.0f
                    );
        }

        NoiseSample sample(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            float tx0 = p.x - ix0;
            float ty0 = p.y - iy0;
            float tx1 = tx0 - 1.0;
            float ty1 = ty0 - 1.0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            vmath::vec3 g00 = _gradients2D[_hashValues[h0 + iy0] % _gradients2DMask];
            vmath::vec3 g10 = _gradients2D[_hashValues[h1 + iy0] % _gradients2DMask];
            vmath::vec3 g01 = _gradients2D[_hashValues[h0 + iy1] % _gradients2DMask];
            vmath::vec3 g11 = _gradients2D[_hashValues[h1 + iy1] % _gradients2DMask];

            float v00 = _dot2D(g00, tx0, ty0);
            float v10 = _dot2D(g10, tx1, ty0);
            float v01 = _dot2D(g01, tx0, ty1);
            float v11 = _dot2D(g11, tx1, ty1);

            float a = v00;
            float b = v10 - v00;
            float c = v01 - v00;
            float d = v11 - v01 - v10 + v00;

            vmath::vec3 da = g00;
            vmath::vec3 db = g10 - g00;
            vmath::vec3 dc = g01 - g00;
            vmath::vec3 dd = g11 - g01 - g10 + g00;

            float tx = _smooth(tx0);
            float ty = _smooth(ty0);
            float dtx = _smoothDerivative(tx0);
            float dty = _smoothDerivative(ty0);

            vmath::vec3 tempDerivative = da + db * tx + (dc + dd * tx) * ty;

            NoiseSample sample;
            sample.value = (a + b * tx + (c + d * tx) * ty) * _sqrt2;
            sample.derivative = vmath::vec3(
                        (tempDerivative.x + (b + d * ty) * dtx) * frequency * _sqrt2,
                        (tempDerivative.y + (c + d * tx) * dty) * frequency * _sqrt2,
                        0.0f
                    );

            return sample;
        }

    }


    namespace Perlin3D {

        float value(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            int iz0 = (int)std::floor(p.z);
            float tx0 = p.x - ix0;
            float ty0 = p.y - iy0;
            float tz0 = p.z - iz0;
            float tx1 = tx0 - 1.0;
            float ty1 = ty0 - 1.0;
            float tz1 = tz0 - 1.0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            iz0 = _fmodint(iz0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;
            int iz1 = iz0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];
            vmath::vec3 g000 = _gradients3D[_hashValues[h00 + iz0] % _gradients3DMask];
            vmath::vec3 g100 = _gradients3D[_hashValues[h10 + iz0] % _gradients3DMask];
            vmath::vec3 g010 = _gradients3D[_hashValues[h01 + iz0] % _gradients3DMask];
            vmath::vec3 g110 = _gradients3D[_hashValues[h11 + iz0] % _gradients3DMask];
            vmath::vec3 g001 = _gradients3D[_hashValues[h00 + iz1] % _gradients3DMask];
            vmath::vec3 g101 = _gradients3D[_hashValues[h10 + iz1] % _gradients3DMask];
            vmath::vec3 g011 = _gradients3D[_hashValues[h01 + iz1] % _gradients3DMask];
            vmath::vec3 g111 = _gradients3D[_hashValues[h11 + iz1] % _gradients3DMask];

            float v000 = _dot3D(g000, tx0, ty0, tz0);
            float v100 = _dot3D(g100, tx1, ty0, tz0);
            float v010 = _dot3D(g010, tx0, ty1, tz0);
            float v110 = _dot3D(g110, tx1, ty1, tz0);
            float v001 = _dot3D(g001, tx0, ty0, tz1);
            float v101 = _dot3D(g101, tx1, ty0, tz1);
            float v011 = _dot3D(g011, tx0, ty1, tz1);
            float v111 = _dot3D(g111, tx1, ty1, tz1);

            float a = v000;
            float b = v100 - v000;
            float c = v010 - v000;
            float d = v001 - v000;
            float e = v110 - v010 - v100 + v000;
            float f = v101 - v001 - v100 + v000;
            float g = v011 - v001 - v010 + v000;
            float h = v111 - v011 - v101 + v001 - v110 + v010 + v100 - v000;

            float tx = _smooth(tx0);
            float ty = _smooth(ty0);
            float tz = _smooth(tz0);

            return a + b * tx + (c + e * tx) * ty + (d + f * tx + (g + h * tx) * ty) * tz;
        }

        vmath::vec3 derivative(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            int iz0 = (int)std::floor(p.z);
            float tx0 = p.x - ix0;
            float ty0 = p.y - iy0;
            float tz0 = p.z - iz0;
            float tx1 = tx0 - 1.0;
            float ty1 = ty0 - 1.0;
            float tz1 = tz0 - 1.0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            iz0 = _fmodint(iz0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;
            int iz1 = iz0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];
            vmath::vec3 g000 = _gradients3D[_hashValues[h00 + iz0] % _gradients3DMask];
            vmath::vec3 g100 = _gradients3D[_hashValues[h10 + iz0] % _gradients3DMask];
            vmath::vec3 g010 = _gradients3D[_hashValues[h01 + iz0] % _gradients3DMask];
            vmath::vec3 g110 = _gradients3D[_hashValues[h11 + iz0] % _gradients3DMask];
            vmath::vec3 g001 = _gradients3D[_hashValues[h00 + iz1] % _gradients3DMask];
            vmath::vec3 g101 = _gradients3D[_hashValues[h10 + iz1] % _gradients3DMask];
            vmath::vec3 g011 = _gradients3D[_hashValues[h01 + iz1] % _gradients3DMask];
            vmath::vec3 g111 = _gradients3D[_hashValues[h11 + iz1] % _gradients3DMask];

            float v000 = _dot3D(g000, tx0, ty0, tz0);
            float v100 = _dot3D(g100, tx1, ty0, tz0);
            float v010 = _dot3D(g010, tx0, ty1, tz0);
            float v110 = _dot3D(g110, tx1, ty1, tz0);
            float v001 = _dot3D(g001, tx0, ty0, tz1);
            float v101 = _dot3D(g101, tx1, ty0, tz1);
            float v011 = _dot3D(g011, tx0, ty1, tz1);
            float v111 = _dot3D(g111, tx1, ty1, tz1);

            float b = v100 - v000;
            float c = v010 - v000;
            float d = v001 - v000;
            float e = v110 - v010 - v100 + v000;
            float f = v101 - v001 - v100 + v000;
            float g = v011 - v001 - v010 + v000;
            float h = v111 - v011 - v101 + v001 - v110 + v010 + v100 - v000;

            vmath::vec3 da = g000;
            vmath::vec3 db = g100 - g000;
            vmath::vec3 dc = g010 - g000;
            vmath::vec3 dd = g001 - g000;
            vmath::vec3 de = g110 - g010 - g100 + g000;
            vmath::vec3 df = g101 - g001 - g100 + g000;
            vmath::vec3 dg = g011 - g001 - g010 + g000;
            vmath::vec3 dh = g111 - g011 - g101 + g001 - g110 + g010 + g100 - g000;

            float tx = _smooth(tx0);
            float ty = _smooth(ty0);
            float tz = _smooth(tz0);
            float dtx = _smoothDerivative(tx0);
            float dty = _smoothDerivative(ty0);
            float dtz = _smoothDerivative(tz0);

            vmath::vec3 tempDerivative = da + db * tx + (dc + de * tx) * ty + (dd + df * tx + (dg + dh * tx) * ty) * tz;

            return vmath::vec3(
                        (tempDerivative.x + (b + e * ty + (f + h * ty) * tz) * dtx) * frequency,
                        (tempDerivative.y + (c + e * tx + (g + h * tx) * tz) * dty) * frequency,
                        (tempDerivative.z + (d + f * tx + (g + h * tx) * ty) * dtz) * frequency
                    );
        }

        NoiseSample sample(vmath::vec3 p, float frequency) {
            p *= frequency;
            int ix0 = (int)std::floor(p.x);
            int iy0 = (int)std::floor(p.y);
            int iz0 = (int)std::floor(p.z);
            float tx0 = p.x - ix0;
            float ty0 = p.y - iy0;
            float tz0 = p.z - iz0;
            float tx1 = tx0 - 1.0;
            float ty1 = ty0 - 1.0;
            float tz1 = tz0 - 1.0;
            ix0 = _fmodint(ix0, _hashValuesMask);
            iy0 = _fmodint(iy0, _hashValuesMask);
            iz0 = _fmodint(iz0, _hashValuesMask);
            int ix1 = ix0 + 1;
            int iy1 = iy0 + 1;
            int iz1 = iz0 + 1;

            int h0 = _hashValues[ix0];
            int h1 = _hashValues[ix1];
            int h00 = _hashValues[h0 + iy0];
            int h10 = _hashValues[h1 + iy0];
            int h01 = _hashValues[h0 + iy1];
            int h11 = _hashValues[h1 + iy1];
            vmath::vec3 g000 = _gradients3D[_hashValues[h00 + iz0] % _gradients3DMask];
            vmath::vec3 g100 = _gradients3D[_hashValues[h10 + iz0] % _gradients3DMask];
            vmath::vec3 g010 = _gradients3D[_hashValues[h01 + iz0] % _gradients3DMask];
            vmath::vec3 g110 = _gradients3D[_hashValues[h11 + iz0] % _gradients3DMask];
            vmath::vec3 g001 = _gradients3D[_hashValues[h00 + iz1] % _gradients3DMask];
            vmath::vec3 g101 = _gradients3D[_hashValues[h10 + iz1] % _gradients3DMask];
            vmath::vec3 g011 = _gradients3D[_hashValues[h01 + iz1] % _gradients3DMask];
            vmath::vec3 g111 = _gradients3D[_hashValues[h11 + iz1] % _gradients3DMask];

            float v000 = _dot3D(g000, tx0, ty0, tz0);
            float v100 = _dot3D(g100, tx1, ty0, tz0);
            float v010 = _dot3D(g010, tx0, ty1, tz0);
            float v110 = _dot3D(g110, tx1, ty1, tz0);
            float v001 = _dot3D(g001, tx0, ty0, tz1);
            float v101 = _dot3D(g101, tx1, ty0, tz1);
            float v011 = _dot3D(g011, tx0, ty1, tz1);
            float v111 = _dot3D(g111, tx1, ty1, tz1);

            float a = v000;
            float b = v100 - v000;
            float c = v010 - v000;
            float d = v001 - v000;
            float e = v110 - v010 - v100 + v000;
            float f = v101 - v001 - v100 + v000;
            float g = v011 - v001 - v010 + v000;
            float h = v111 - v011 - v101 + v001 - v110 + v010 + v100 - v000;

            vmath::vec3 da = g000;
            vmath::vec3 db = g100 - g000;
            vmath::vec3 dc = g010 - g000;
            vmath::vec3 dd = g001 - g000;
            vmath::vec3 de = g110 - g010 - g100 + g000;
            vmath::vec3 df = g101 - g001 - g100 + g000;
            vmath::vec3 dg = g011 - g001 - g010 + g000;
            vmath::vec3 dh = g111 - g011 - g101 + g001 - g110 + g010 + g100 - g000;

            float tx = _smooth(tx0);
            float ty = _smooth(ty0);
            float tz = _smooth(tz0);
            float dtx = _smoothDerivative(tx0);
            float dty = _smoothDerivative(ty0);
            float dtz = _smoothDerivative(tz0);

            vmath::vec3 tempDerivative = da + db * tx + (dc + de * tx) * ty + (dd + df * tx + (dg + dh * tx) * ty) * tz;

            NoiseSample sample;
            sample.value = a + b * tx + (c + e * tx) * ty + (d + f * tx + (g + h * tx) * ty) * tz;
            sample.derivative = vmath::vec3(
                        (tempDerivative.x + (b + e * ty + (f + h * ty) * tz) * dtx) * frequency,
                        (tempDerivative.y + (c + e * tx + (g + h * tx) * tz) * dty) * frequency,
                        (tempDerivative.z + (d + f * tx + (g + h * tx) * ty) * dtz) * frequency
                    );

            return sample;
        }

    }


    namespace Sum {

        float value(float (*noiseMethod)(vmath::vec3 p, float frequency), 
                    vmath::vec3 p, float frequency, int octaves, float lacunarity, float persistence) {

            float value = noiseMethod(p, frequency);
            float amplitude = 1.0f;
            float height = 1.0f;

            for (int i = 1; i < octaves; i++) {
                frequency *= lacunarity;
                amplitude *= persistence;
                height += amplitude;

                float tempValue = noiseMethod(p, frequency);
                value += tempValue * amplitude;
            }
            
            value /= height;

            return value;
        }

        vmath::vec3 derivative(vmath::vec3 (*noiseMethod)(vmath::vec3 p, float frequency), 
                               vmath::vec3 p, float frequency, int octaves, float lacunarity, float persistence) {
            
            vmath::vec3 derivative = noiseMethod(p, frequency);
            float amplitude = 1.0f;
            float height = 1.0f;

            for (int i = 1; i < octaves; i++) {
                frequency *= lacunarity;
                amplitude *= persistence;
                height += amplitude;

                vmath::vec3 tempDerivative = noiseMethod(p, frequency);
                derivative += tempDerivative * amplitude;
            }

            derivative /= height;

            return derivative;
        }

        NoiseSample sample(NoiseSample (*noiseMethod)(vmath::vec3 p, float frequency), 
                           vmath::vec3 p, float frequency, int octaves, float lacunarity, float persistence) {

            NoiseSample sample = noiseMethod(p, frequency);
            float amplitude = 1.0f;
            float height = 1.0f;

            for (int i = 1; i < octaves; i++) {
                frequency *= lacunarity;
                amplitude *= persistence;
                height += amplitude;

                NoiseSample tempSample = noiseMethod(p, frequency);
                sample.value += tempSample.value * amplitude;
                sample.derivative += tempSample.derivative * amplitude;
            }

            sample.value /= height;
            sample.derivative /= height;

            return sample;
        }

    }

}