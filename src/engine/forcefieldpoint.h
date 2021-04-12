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

#ifndef FLUIDENGINE_FORCEFIELDPOINT_H
#define FLUIDENGINE_FORCEFIELDPOINT_H

#include "forcefield.h"


class ForceFieldPoint : public ForceField
{
public:
    ForceFieldPoint();
    virtual ~ForceFieldPoint();

    virtual void update(double dt, double frameInterpolation);
    virtual void addForceFieldToGrid(MACVelocityField &fieldGrid);
    virtual void addGravityScaleToGrid(ForceFieldGravityScaleGrid &scaleGrid);
    virtual std::vector<vmath::vec3> generateDebugProbes();

protected:
    virtual void _initialize();
    virtual bool _isSubclassStateChanged();
    virtual void _clearSubclassState();

private:

    void _addForceFieldToGridMT(MACVelocityField &fieldGrid, int dir);
    void _addForceFieldToGridThread(int startidx, int endidx, 
                                    MACVelocityField *fieldGrid, int dir);

    double _frameInterpolation = 0.0;
    int _numDebugProbes = 200;
    float _minRadiusFactor = 4.0f;

};

#endif
