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

#ifndef FLUIDENGINE_FORCEFIELDGRID_H
#define FLUIDENGINE_FORCEFIELDGRID_H

#include <vector>

#include "macvelocityfield.h"
#include "forcefieldgravityscalegrid.h"
#include "vmath.h"

class ForceField;

struct ForceFieldDebugNode {
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float strength = 0.0f;
};


class ForceFieldGrid
{
public:
    ForceFieldGrid();
    ~ForceFieldGrid();
    
    void initialize(int isize, int jsize, int ksize, double dx);
    void addForceField(ForceField *field);
    void update(double dt, double frameInterpolation);

    vmath::vec3 evaluateForceAtPosition(vmath::vec3 p);
    float evaluateForceAtPositionU(vmath::vec3 p);
    float evaluateForceAtPositionV(vmath::vec3 p);
    float evaluateForceAtPositionW(vmath::vec3 p);

    vmath::vec3 getGravityVector();
    void setGravityVector(vmath::vec3 g);

    void generateDebugNodes(std::vector<ForceFieldDebugNode> &nodes);

private:

    void _updateForceFields(double dt, double frameInterpolation);
    void _applyForceFields();
    void _applyGravity();

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 1.0;
    bool _isInitialized = false;
    bool _isStateChanged = true;

    std::vector<ForceField*> _forceFields;
    MACVelocityField _forceField;
    ForceFieldGravityScaleGrid _gravityScaleGrid;

    vmath::vec3 _gravityVector;

    // Debug Generation
    int _numProbeSegments = 250;
    int _minProbeSegments = 20;
    int _segmentsPerArrow = 50;
    int _numArrowSegments = 5;
    float _stepDistanceFactor = 0.125;
};

#endif
