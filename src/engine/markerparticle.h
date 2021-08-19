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

#ifndef FLUIDENGINE_MARKERPARTICLE_H
#define FLUIDENGINE_MARKERPARTICLE_H

#include "vmath.h"

struct MarkerParticle {
    vmath::vec3 position;
    vmath::vec3 velocity;

    MarkerParticle() {}

    MarkerParticle(vmath::vec3 p) : position(p) {}
    MarkerParticle(vmath::vec3 p, vmath::vec3 v) : 
                                  position(p),
                                  velocity(v) {}

    MarkerParticle(double x, double y, double z) : 
                                  position(x, y, z) {}
};

struct MarkerParticleAffine {
    vmath::vec3 affineX;
    vmath::vec3 affineY;
    vmath::vec3 affineZ;

    MarkerParticleAffine(vmath::vec3 ax, vmath::vec3 ay, vmath::vec3 az) : 
                                  affineX(ax),
                                  affineY(ay),
                                  affineZ(az) {}
};

struct MarkerParticleAge {
    float age;

    MarkerParticleAge(float a) : age(a) {}
};

struct MarkerParticleColor {
    vmath::vec3 color;

    MarkerParticleColor(vmath::vec3 c) : color(c) {}
};

struct MarkerParticleSourceID {
    int sourceid;

    MarkerParticleSourceID(int id) : sourceid(id) {}
};

#endif