/*
MIT License

Copyright (c) 2019 Ryan L. Guy

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

#include "forcefieldpoint.h"

// DEBUG
#include <iostream>

#include <random>

#include "trianglemesh.h"
#include "grid3d.h"
#include "vmath.h"


ForceFieldPoint::ForceFieldPoint() {
}

ForceFieldPoint::~ForceFieldPoint() {
}

void ForceFieldPoint::update(double dt) {
    std::cout << "Updating ForceFieldPoint " << dt << std::endl;
}

void ForceFieldPoint::addForceFieldToGrid(MACVelocityField &fieldGrid) {
    std::cout << "Adding ForceFieldPoint to grid " << std::endl;

    TriangleMesh m = _meshObject.getMesh();
    vmath::vec3 p = m.getCentroid();

    float minDistance = -1.0f;
    float maxDistance = std::numeric_limits<float>::infinity();
    if (_isMinDistanceEnabled) {
        minDistance = _minDistance;
    }
    if (_isMaxDistanceEnabled) {
        maxDistance = _maxDistance;
    }

    float eps = 1e-6;
    float power = _falloffPower;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 gp = Grid3d::FaceIndexToPositionU(i, j, k, _dx);
                vmath::vec3 v = gp - p;
                float r = std::max(vmath::length(v), minDistance);
                if (r < eps || r > maxDistance) {
                    continue;
                }

                vmath::vec3 normal = vmath::normalize(v);
                vmath::vec3 force = _strength * (1.0f / std::pow(r, power)) * normal;
                fieldGrid.addU(i, j, k, force.x);
            }
        }
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize; i++) {
                vmath::vec3 gp = Grid3d::FaceIndexToPositionV(i, j, k, _dx);
                vmath::vec3 v = gp - p;
                float r = std::max(vmath::length(v), minDistance);
                if (r < eps || r > maxDistance) {
                    continue;
                }

                vmath::vec3 normal = vmath::normalize(v);
                vmath::vec3 force = _strength * (1.0f / std::pow(r, power)) * normal;
                fieldGrid.addV(i, j, k, force.y);
            }
        }
    }

    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                vmath::vec3 gp = Grid3d::FaceIndexToPositionW(i, j, k, _dx);
                vmath::vec3 v = gp - p;
                float r = std::max(vmath::length(v), minDistance);
                if (r < eps || r > maxDistance) {
                    continue;
                }

                vmath::vec3 normal = vmath::normalize(v);
                vmath::vec3 force = _strength * (1.0f / std::pow(r, power)) * normal;
                fieldGrid.addW(i, j, k, force.z);
            }
        }
    }
}

std::vector<vmath::vec3> ForceFieldPoint::generateDebugProbes() {
    TriangleMesh m = _meshObject.getMesh();
    vmath::vec3 p = m.getCentroid();

    std::mt19937 generator(0);
    std::uniform_real_distribution<float> uniform(0.0, 1.0);
    float pi = 3.14159265f;
    float eps = 1e-6;

    float radius = _minRadiusFactor * _dx;
    if (_isMinDistanceEnabled) {
        radius = std::max(radius, _minDistance);
    }
    if (_isMaxDistanceEnabled) {
        radius = std::min(radius, _maxDistance);
    }
    radius = std::max(radius, eps);

    std::vector<vmath::vec3> probes;
    for (int i = 0; i < _numDebugProbes; i++) {
        float theta = 2.0f * pi * uniform(generator);
        double phi = acos(1.0f - 2.0f * uniform(generator));
        double x = sin(phi) * cos(theta) * radius;
        double y = sin(phi) * sin(theta) * radius;
        double z = cos(phi) * radius;

        vmath::vec3 probe(x, y, z);
        probe += p;
        probes.push_back(probe);
    }

    return probes;
}

void ForceFieldPoint::_initialize() {
    std::cout << "Initializing ForceFieldPoint " << _isize << " " << _jsize << " " << _ksize << " " << _dx << std::endl;
}