/*
MIT License

Copyright (C) 2024 Ryan L. Guy

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

#include "forcefieldgrid.h"

#include <random>
#include <algorithm>

#include "forcefield.h"
#include "aabb.h"


ForceFieldGrid::ForceFieldGrid() {
}

ForceFieldGrid::~ForceFieldGrid() {
}

void ForceFieldGrid::initialize(int isize, int jsize, int ksize, double dx) {
    if (_isInitialized) {
        return;
    }

    _isize = isize;
    _jsize = jsize;
    _ksize = ksize;
    _dx = dx;

    _forceField = MACVelocityField(_isize, _jsize, _ksize, _dx);
    _gravityScaleGrid = ForceFieldGravityScaleGrid(_isize + 1, _jsize + 1, _ksize + 1);
    for (size_t i = 0; i < _forceFields.size(); i++) {
        _forceFields[i]->initialize(isize, jsize, ksize, dx);
    }

    _isStateChanged = true;
    _isInitialized = true;
}

void ForceFieldGrid::addForceField(ForceField *field) {
    if (_isInitialized) {
        field->initialize(_isize, _jsize, _ksize, _dx);
    }

    _forceFields.push_back(field);
    _isStateChanged = true;
}

void ForceFieldGrid::update(double dt, double frameInterpolation) {
    _updateForceFields(dt, frameInterpolation);

    for (size_t i = 0; i < _forceFields.size(); i++) {
        if (_forceFields[i]->isStateChanged()) {
            _isStateChanged = true;
            break;
        }
    }

    if (!_isStateChanged) {
        return;
    }

    _forceField.clear();
    _applyForceFields();
    _applyGravity();

    for (size_t i = 0; i < _forceFields.size(); i++) {
        _forceFields[i]->clearState();
    }

    _isStateChanged = false;
}

vmath::vec3 ForceFieldGrid::getGravityVector() {
    return _gravityVector;
}

void ForceFieldGrid::setGravityVector(vmath::vec3 g) {
    float eps = 1e-6;
    if ((g - _gravityVector).length() > eps) {
        _isStateChanged = true;
    }
    _gravityVector = g;
}

vmath::vec3 ForceFieldGrid::evaluateForceAtPosition(vmath::vec3 p, float forceScale) {
    vmath::vec3 forceVector = _forceField.evaluateVelocityAtPositionLinear(p.x, p.y, p.z);
    float gravityScale = Interpolation::trilinearInterpolate(p, _dx, _gravityScaleGrid.gravityScale);
    vmath::vec3 totalForce = forceScale * forceVector + gravityScale * _gravityVector;
    return totalForce;
}

float ForceFieldGrid::evaluateForceAtPositionU(vmath::vec3 p, float forceScale) {
    float forceU = _forceField.evaluateVelocityAtPositionLinearU(p.x, p.y, p.z);
    float gravityScale = Interpolation::trilinearInterpolate(p, _dx, _gravityScaleGrid.gravityScale);
    float totalForceU = forceScale * forceU + gravityScale * _gravityVector.x;
    return totalForceU;
}

float ForceFieldGrid::evaluateForceAtPositionV(vmath::vec3 p, float forceScale) {
    float forceV = _forceField.evaluateVelocityAtPositionLinearV(p.x, p.y, p.z);
    float gravityScale = Interpolation::trilinearInterpolate(p, _dx, _gravityScaleGrid.gravityScale);
    float totalForceV = forceScale * forceV + gravityScale * _gravityVector.y;
    return totalForceV;
}

float ForceFieldGrid::evaluateForceAtPositionW(vmath::vec3 p, float forceScale) {
    float forceW = _forceField.evaluateVelocityAtPositionLinearW(p.x, p.y, p.z);
    float gravityScale = Interpolation::trilinearInterpolate(p, _dx, _gravityScaleGrid.gravityScale);
    float totalForceW = forceScale * forceW + gravityScale * _gravityVector.z;
    return totalForceW;
}

void ForceFieldGrid::generateDebugNodes(std::vector<ForceFieldDebugNode> &nodes) {
    float eps = 1e-6;
    float forceScale = 1.0f;

    int gridpad = 1;
    vmath::vec3 debugmin = Grid3d::GridIndexToPosition(gridpad, gridpad, gridpad, _dx);
    vmath::vec3 debugmax = Grid3d::GridIndexToPosition(_isize - gridpad, _jsize - gridpad, _ksize - gridpad, _dx);
    AABB debugBounds(debugmin, debugmax);

    std::vector<vmath::vec3> probes;
    for (size_t i = 0; i < _forceFields.size(); i++) {
        std::vector<vmath::vec3> fieldProbes = _forceFields[i]->generateDebugProbes();
        probes.insert(probes.end(), fieldProbes.begin(), fieldProbes.end());
    }

    std::mt19937 generator(0);
    std::shuffle(probes.begin(), probes.end(), generator);

    nodes.clear();
    int numSegments = _numProbeSegments;
    int minSegments = _minProbeSegments;
    float stepDistance = _stepDistanceFactor * _dx;
    for (size_t i = 0; i < probes.size(); i++) {
        vmath::vec3 seed = probes[i];
        vmath::vec3 seedforce = evaluateForceAtPosition(seed, forceScale);
        float seedstrength = seedforce.length();

        vmath::vec3 p1 = seed + seedforce.normalize() * stepDistance;
        vmath::vec3 p2 = seed + -seedforce.normalize() * stepDistance;
        float s1 = evaluateForceAtPosition(p1, forceScale).length();
        float s2 = evaluateForceAtPosition(p2, forceScale).length();
        float direction = 1.0f;
        if (s1 > seedstrength) {
            direction = -1.0f;
        } else if (s2 > seedstrength) {
            direction = 1.0f;
        }

        std::vector<ForceFieldDebugNode> forceline;
        for (int sidx = 0; sidx < numSegments; sidx++) {
            vmath::vec3 force = evaluateForceAtPosition(seed, forceScale);

            ForceFieldDebugNode node;
            node.x = seed.x;
            node.y = seed.y;
            node.z = seed.z;
            node.strength = force.length();
            forceline.push_back(node);

            seed = seed + direction * force.normalize() * stepDistance;
            if (!Grid3d::isPositionInGrid(seed, _dx, _isize, _jsize, _ksize)) {
                break;
            }
        }

        if ((int)forceline.size() < minSegments) {
            continue;
        }

        std::vector<ForceFieldDebugNode> arrowNodes;
        for (size_t sidx = 1; sidx < forceline.size() - 1; sidx += _segmentsPerArrow) {
            if (forceline[sidx].strength < eps) {
                continue;
            }

            ForceFieldDebugNode n1 = forceline[sidx - 1];
            ForceFieldDebugNode n2 = forceline[sidx];
            ForceFieldDebugNode n3 = forceline[sidx + 1];

            vmath::vec3 p1(n1.x, n1.y, n1.z);
            vmath::vec3 p2(n2.x, n2.y, n2.z);
            vmath::vec3 p3(n3.x, n3.y, n3.z);
            vmath::vec3 forcedir = evaluateForceAtPosition(p2, forceScale).normalize();

            vmath::vec3 v1 = p1 - p2;
            vmath::vec3 v2 = p3 - p2;
            vmath::vec3 cross = vmath::cross(v1, v2);

            vmath::vec3 crossdir(1.0f, 0.0f, 0.0f);
            if (vmath::length(cross) > eps) {
                crossdir = cross.normalize();
            }

            vmath::vec3 arrowdir1 = vmath::normalize(-forcedir + crossdir);
            vmath::vec3 arrowdir2 = vmath::normalize(-forcedir - crossdir);

            for (int aidx = 0; aidx < _numArrowSegments; aidx++) {
                vmath::vec3 a1 = p2 + aidx * stepDistance * arrowdir1;
                vmath::vec3 a2 = p2 + aidx * stepDistance * arrowdir2;

                if (!Grid3d::isPositionInGrid(a1, _dx, _isize, _jsize, _ksize) || 
                        !Grid3d::isPositionInGrid(a2, _dx, _isize, _jsize, _ksize)) {
                    break;
                }

                float s1 = evaluateForceAtPosition(a1, forceScale).length();
                float s2 = evaluateForceAtPosition(a2, forceScale).length();

                ForceFieldDebugNode n1;
                n1.x = a1.x;
                n1.y = a1.y;
                n1.z = a1.z;
                n1.strength = s1;

                ForceFieldDebugNode n2;
                n2.x = a2.x;
                n2.y = a2.y;
                n2.z = a2.z;
                n2.strength = s2;

                arrowNodes.push_back(n1);
                arrowNodes.push_back(n2);
            }
        }

        forceline.insert(forceline.end(), arrowNodes.begin(), arrowNodes.end());
        for (size_t fidx = 0; fidx < forceline.size(); fidx++) {
            ForceFieldDebugNode n = forceline[fidx];
            vmath::vec3 p(n.x, n.y, n.z);
            if (debugBounds.isPointInside(p)) {
                nodes.push_back(n);
            }
        }
    }
}

void ForceFieldGrid::_updateForceFields(double dt, double frameInterpolation) {
    for (size_t i = 0; i < _forceFields.size(); i++) {
        _forceFields[i]->update(dt, frameInterpolation);
    }
}

void ForceFieldGrid::_applyForceFields() {
    for (size_t i = 0; i < _forceFields.size(); i++) {
        if (_forceFields[i]->isEnabled()) {
            _forceFields[i]->addForceFieldToGrid(_forceField);
        }
    }
}

void ForceFieldGrid::_applyGravity() {
    _gravityScaleGrid.reset();
    for (size_t i = 0; i < _forceFields.size(); i++) {
        if (_forceFields[i]->isEnabled()) {
            _forceFields[i]->addGravityScaleToGrid(_gravityScaleGrid);
        }
    }
    _gravityScaleGrid.normalize();
    _forceField.setOutOfRangeVector(_gravityVector);
}