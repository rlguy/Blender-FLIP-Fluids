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

void ForceFieldPoint::update(double dt, double frameInterpolation) {
    _frameInterpolation = frameInterpolation;
}

void ForceFieldPoint::addForceFieldToGrid(MACVelocityField &fieldGrid) {
    int U = 0; int V = 1; int W = 2;
    _addForceFieldToGridMT(fieldGrid, U);
    _addForceFieldToGridMT(fieldGrid, V);
    _addForceFieldToGridMT(fieldGrid, W);
}

void ForceFieldPoint::addGravityScaleToGrid(ForceFieldGravityScaleGrid &scaleGrid) {
    float scaleWidth = _gravityScaleWidth;
    if (_isMaxDistanceEnabled) {
        scaleWidth = std::min(scaleWidth, _maxDistance);
    }

    TriangleMesh m = _meshObject.getMesh(_frameInterpolation);
    vmath::vec3 p = m.getCentroid();

    for (int k = 0; k < scaleGrid.gravityScale.depth; k++) {
        for (int j = 0; j < scaleGrid.gravityScale.height; j++) {
            for (int i = 0; i < scaleGrid.gravityScale.width; i++) {
                vmath::vec3 gp = Grid3d::GridIndexToPosition(i, j, k, _dx);
                vmath::vec3 v = gp - p;
                float d = vmath::length(v);
                if (d < scaleWidth) {
                    float factor = 1.0f - (d / scaleWidth);
                    float scale = factor * _gravityScale + (1.0f - factor);
                    scaleGrid.addScale(i, j, k, scale);
                }
            }
        }
    }
}

std::vector<vmath::vec3> ForceFieldPoint::generateDebugProbes() {
    TriangleMesh m = _meshObject.getMesh(_frameInterpolation);
    vmath::vec3 p = m.getCentroid();

    std::mt19937 generator(0);
    std::uniform_real_distribution<float> uniform(0.0, 1.0);
    float pi = 3.14159265f;
    float minradius = _minRadiusFactor * _dx;
    
    float radius = minradius;
    if (_isMinDistanceEnabled) {
        radius = std::max(radius, _minDistance);
    }
    if (_isMaxDistanceEnabled) {
        radius = std::min(radius, _maxDistance);
    }
    radius = std::max(radius, minradius);

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
}

bool ForceFieldPoint::_isSubclassStateChanged() {
    return false;
}

void ForceFieldPoint::_clearSubclassState() {
    
}

void ForceFieldPoint::_addForceFieldToGridMT(MACVelocityField &fieldGrid, int dir) {

    int U = 0; int V = 1; int W = 2;

    int gridsize = 0;
    if (dir == U) {
        gridsize = (_isize + 1) * _jsize * _ksize;
    } else if (dir == V) {
        gridsize = _isize * (_jsize + 1) * _ksize;
    } else if (dir == W) {
        gridsize = _isize * _jsize * (_ksize + 1);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ForceFieldPoint::_addForceFieldToGridThread, this,
                                 intervals[i], intervals[i + 1], &fieldGrid, dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ForceFieldPoint::_addForceFieldToGridThread(int startidx, int endidx, 
                                                 MACVelocityField *fieldGrid, int dir) {
    int U = 0; int V = 1; int W = 2;

    TriangleMesh m = _meshObject.getMesh(_frameInterpolation);
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

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            vmath::vec3 gp = Grid3d::FaceIndexToPositionU(g, _dx);
            vmath::vec3 v = gp - p;
            float r = std::max(vmath::length(v), minDistance);
            if (r < eps || r > maxDistance) {
                continue;
            }

            vmath::vec3 normal = vmath::normalize(v);
            vmath::vec3 force = _calculateForceVector(r, normal);
            fieldGrid->addU(g, force.x);
        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            vmath::vec3 gp = Grid3d::FaceIndexToPositionV(g, _dx);
            vmath::vec3 v = gp - p;
            float r = std::max(vmath::length(v), minDistance);
            if (r < eps || r > maxDistance) {
                continue;
            }

            vmath::vec3 normal = vmath::normalize(v);
            vmath::vec3 force = _calculateForceVector(r, normal);
            fieldGrid->addV(g, force.y);
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            vmath::vec3 gp = Grid3d::FaceIndexToPositionW(g, _dx);
            vmath::vec3 v = gp - p;
            float r = std::max(vmath::length(v), minDistance);
            if (r < eps || r > maxDistance) {
                continue;
            }

            vmath::vec3 normal = vmath::normalize(v);
            vmath::vec3 force = _calculateForceVector(r, normal);
            fieldGrid->addW(g, force.z);
        }

    }
}