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

#ifndef FLUIDENGINE_FORCEFIELDGRAVITYSCALEGRID_H
#define FLUIDENGINE_FORCEFIELDGRAVITYSCALEGRID_H

#include "array3d.h"
#include "interpolation.h"

struct ForceFieldGravityScaleGrid {
    Array3d<float> gravityScale;
    Array3d<int> gravityCount;

    ForceFieldGravityScaleGrid() {
    }

    ForceFieldGravityScaleGrid(int isize, int jsize, int ksize) {
        gravityScale = Array3d<float>(isize, jsize, ksize, 0.0f);
        gravityCount = Array3d<int>(isize, jsize, ksize, 0);
    }

    void reset() {
        gravityScale.fill(0.0f);
        gravityCount.fill(0);
    }

    void addScale(int i, int j, int k, float scale) {
        gravityScale.add(i, j, k, scale);
        gravityCount.add(i, j, k, 1);
    }

    void addScale(GridIndex g, float scale) {
        addScale(g.i, g.j, g.k, scale);
    }

    void normalize() {
        for (int k = 0; k < gravityScale.depth; k++) {
            for (int j = 0; j < gravityScale.height; j++) {
                for (int i = 0; i < gravityScale.width; i++) {
                    int count = gravityCount(i, j, k);
                    if (count == 0) {
                        gravityScale.set(i, j, k, 1.0f);
                    } else {
                        float avg = gravityScale(i, j, k) / count;
                        gravityScale.set(i, j, k, avg);
                    }
                }
            }
        }
    }

    float operator()(int i, int j, int k) {
        return gravityScale(i, j, k);
    }

    float operator()(GridIndex g) {
        return gravityScale(g);
    }
};

#endif