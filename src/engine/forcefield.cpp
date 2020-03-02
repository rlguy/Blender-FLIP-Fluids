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
    _meshObject.enable();
}

void ForceField::disable() {
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

    _isInitialized = true;
}

float ForceField::getStrength() {
    return _strength;
}

void ForceField::setStrength(float s) {
    _strength = s;
}

float ForceField::getFalloffPower() {
    return _falloffPower;
}

void ForceField::setFalloffPower(float p) {
    _falloffPower = p;
}

void ForceField::enableMinDistance() {
    _isMinDistanceEnabled = true;
}

void ForceField::disableMinDistance() {
    _isMinDistanceEnabled = false;
}

bool ForceField::isMinDistanceEnabled() {
    return _isMinDistanceEnabled;
}

float ForceField::getMinDistance() {
    return _minDistance;
}

void ForceField::setMinDistance(float d) {
    _minDistance = d;
}

void ForceField::enableMaxDistance() {
    _isMaxDistanceEnabled = true;
}

void ForceField::disableMaxDistance() {
    _isMaxDistanceEnabled = false;
}

bool ForceField::isMaxDistanceEnabled() {
    return _isMaxDistanceEnabled;
}

float ForceField::getMaxDistance() {
    return _maxDistance;
}

void ForceField::setMaxDistance(float d) {
    _maxDistance = d;
}

