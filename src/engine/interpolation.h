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

#ifndef FLUIDENGINE_INTERPOLATION_H
#define FLUIDENGINE_INTERPOLATION_H

#include "vmath.h"
#include "array3d.h"

namespace Interpolation {

    extern double cubicInterpolate(double p[4], double x);
    extern double bicubicInterpolate(double p[4][4], double x, double y);
    extern double tricubicInterpolate(double p[4][4][4], double x, double y, double z);

    extern double trilinearInterpolate(double p[8], double x, double y, double z);
    extern double trilinearInterpolate(vmath::vec3 p, double dx, Array3d<float> &grid);

    extern double bilinearInterpolate(double v00, double v10, double v01, double v11, 
                                      double ix, double iy);
    extern void trilinearInterpolateGradient(
            vmath::vec3 p, double dx, Array3d<float> &grid, vmath::vec3 *grad);
}

#endif