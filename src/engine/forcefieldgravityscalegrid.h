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

#ifndef FLUIDENGINE_FORCEFIELDGRAVITYSCALEGRID_H
#define FLUIDENGINE_FORCEFIELDGRAVITYSCALEGRID_H

#include "array3d.h"
#include "interpolation.h"

struct ForceFieldGravityScaleGrid {
    Array3d<float> gravityScale;
    Array3d<float> gravityWeight;

    ForceFieldGravityScaleGrid() {
    }

    ForceFieldGravityScaleGrid(int isize, int jsize, int ksize) {
        gravityScale = Array3d<float>(isize, jsize, ksize, 0.0f);
        gravityWeight = Array3d<float>(isize, jsize, ksize, 0.0f);
    }

    void reset() {
        gravityScale.fill(0.0f);
        gravityWeight.fill(0.0f);
    }

    void addScale(int i, int j, int k, float scale, float weight) {
        gravityScale.add(i, j, k, scale);
        gravityWeight.add(i, j, k, weight);
    }

    void addScale(GridIndex g, float scale, float weight) {
        addScale(g.i, g.j, g.k, scale, weight);
    }

    void normalize() {
        float eps = 1e-6f;
        for (int k = 0; k < gravityScale.depth; k++) {
            for (int j = 0; j < gravityScale.height; j++) {
                for (int i = 0; i < gravityScale.width; i++) {
                    float weight = gravityWeight(i, j, k);
                    if (weight < eps) {
                        gravityScale.set(i, j, k, 1.0f);
                    } else {
                        float avg = gravityScale(i, j, k) / weight;
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