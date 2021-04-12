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

#include "forcefield.h"

// DEBUG
#include <iostream>


ForceField::ForceField() {
}

ForceField::~ForceField() {
}

void ForceField::updateMeshStatic(TriangleMesh meshCurrent) {
    _meshObject.updateMeshStatic(meshCurrent);
}

void ForceField::updateMeshAnimated(TriangleMesh meshPrevious, 
                        TriangleMesh meshCurrent, 
                        TriangleMesh meshNext) {
    _meshObject.updateMeshAnimated(meshPrevious, meshCurrent, meshNext);
}

void ForceField::enable() {
    if (!_meshObject.isEnabled()) {
        _isStateChanged = true;
    }
    _meshObject.enable();
}

void ForceField::disable() {
    if (_meshObject.isEnabled()) {
        _isStateChanged = true;
    }
    _meshObject.disable();
}

bool ForceField::isEnabled() {
    return _meshObject.isEnabled();
}

void ForceField::initialize(int isize, int jsize, int ksize, double dx) {
    if (_isInitialized) {
        return;
    }

    _isize = isize;
    _jsize = jsize;
    _ksize = ksize;
    _dx = dx;
    _meshObject.resizeGrid(isize, jsize, ksize, dx);

    _initialize();

    _isStateChanged = true;
    _isInitialized = true;
}

bool ForceField::isStateChanged() {
    MeshObjectStatus s = _meshObject.getStatus();
    bool isMeshStateChanged = s.isStateChanged || (s.isEnabled && s.isAnimated && s.isMeshChanged);
    return _isStateChanged || isMeshStateChanged || _isSubclassStateChanged();
}

void ForceField::clearState() {
    _meshObject.clearObjectStatus();
    _isStateChanged = false;
    _clearSubclassState();
}

float ForceField::getStrength() {
    return _strength;
}

void ForceField::setStrength(float s) {
    float eps = 1e-6;
    if (std::abs(s - _strength) > eps) {
        _isStateChanged = true;
    }
    _strength = s;
}

float ForceField::getFalloffPower() {
    return _falloffPower;
}

void ForceField::setFalloffPower(float p) {
    float eps = 1e-6;
    if (std::abs(p - _falloffPower) > eps) {
        _isStateChanged = true;
    }
    _falloffPower = p;
}

float ForceField::getMaxForceLimitFactor() {
    return _maxForceLimitFactor;
}

void ForceField::setMaxForceLimitFactor(float factor) {
    float eps = 1e-6;
    if (std::abs(factor - _maxForceLimitFactor) > eps) {
        _isStateChanged = true;
    }
    _maxForceLimitFactor = factor;
}

void ForceField::enableMinDistance() {
    if (!_isMinDistanceEnabled) {
        _isStateChanged = true;
    }
    _isMinDistanceEnabled = true;
}

void ForceField::disableMinDistance() {
    if (_isMinDistanceEnabled) {
        _isStateChanged = true;
    }
    _isMinDistanceEnabled = false;
}

bool ForceField::isMinDistanceEnabled() {
    return _isMinDistanceEnabled;
}

float ForceField::getMinDistance() {
    return _minDistance;
}

void ForceField::setMinDistance(float d) {
    float eps = 1e-6;
    if (std::abs(d - _minDistance) > eps) {
        _isStateChanged = true;
    }
    _minDistance = d;
}

void ForceField::enableMaxDistance() {
    if (!_isMaxDistanceEnabled) {
        _isStateChanged = true;
    }
    _isMaxDistanceEnabled = true;
}

void ForceField::disableMaxDistance() {
    if (_isMaxDistanceEnabled) {
        _isStateChanged = true;
    }
    _isMaxDistanceEnabled = false;
}

bool ForceField::isMaxDistanceEnabled() {
    return _isMaxDistanceEnabled;
}

float ForceField::getMaxDistance() {
    return _maxDistance;
}

void ForceField::setMaxDistance(float d) {
    float eps = 1e-6;
    if (std::abs(d - _maxDistance) > eps) {
        _isStateChanged = true;
    }
    _maxDistance = d;
}

float ForceField::getGravityScale() {
    return _gravityScale;
}

void ForceField::setGravityScale(float s) {
    float eps = 1e-6;
    if (std::abs(s - _gravityScale) > eps) {
        _isStateChanged = true;
    }
    _gravityScale = s;
}

float ForceField::getGravityScaleWidth() {
    return _gravityScaleWidth;
}

void ForceField::setGravityScaleWidth(float w) {
    float eps = 1e-6;
    if (std::abs(w - _gravityScaleWidth) > eps) {
        _isStateChanged = true;
    }
    _gravityScaleWidth = w;
}

vmath::vec3 ForceField::_limitForceVector(vmath::vec3 v, float strength) {
    float eps = 1e-6;
    float maxForce = std::abs(strength) * _maxForceLimitFactor;
    float len = vmath::length(v);
    if (len <= maxForce || len < eps) {
        return v;
    }

    if (maxForce < eps) {
        return vmath::vec3();
    }

    return (maxForce / len) * v;
}

vmath::vec3 ForceField::_calculateForceVector(float distance, vmath::vec3 normal) {
    return _calculateForceVector(distance, _strength, normal);
}

vmath::vec3 ForceField::_calculateForceVector(float distance, float strength, vmath::vec3 normal) {
    vmath::vec3 force = strength * (1.0f / std::pow(distance, _falloffPower)) * normal;
    return _limitForceVector(force, strength);
}