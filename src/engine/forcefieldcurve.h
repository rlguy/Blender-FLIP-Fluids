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

#ifndef FLUIDENGINE_FORCEFIELDCURVE_H
#define FLUIDENGINE_FORCEFIELDCURVE_H

#include "forcefield.h"
#include "meshlevelset.h"


class ForceFieldCurve : public ForceField
{
public:
    ForceFieldCurve();
    virtual ~ForceFieldCurve();

    virtual void update(double dt, double frameInterpolation);
    virtual void addForceFieldToGrid(MACVelocityField &fieldGrid);
    virtual void addGravityScaleToGrid(ForceFieldGravityScaleGrid &scaleGrid);
    virtual std::vector<vmath::vec3> generateDebugProbes();

    float getFlowStrength();
    void setFlowStrength(float s);

    float getSpinStrength();
    void setSpinStrength(float s);

    void enableEndCaps();
    void disableEndCaps();
    bool isEndCapsEnabled();

protected:
    virtual void _initialize();
    virtual bool _isSubclassStateChanged();
    virtual void _clearSubclassState();

private:

    void _updateGridDimensions(TriangleMesh &mesh);
    void _addForceFieldToGridMT(MACVelocityField &fieldGrid, int dir);
    void _addForceFieldToGridThread(int startidx, int endidx, 
                                    MACVelocityField *fieldGrid, int dir);
    TriangleMesh _curveVerticesToTriangleMesh(std::vector<vmath::vec3> vertices);
    vmath::vec3 _getFlowDirection(vmath::vec3 p);
    bool _isPositionNearEndCap(vmath::vec3 p);

    int _ioffsetSDF = 0;
    int _joffsetSDF = 0;
    int _koffsetSDF = 0;
    vmath::vec3 _offsetSDF;
    int _isizeSDF = 0;
    int _jsizeSDF = 0;
    int _ksizeSDF = 0;

    bool _isLevelsetUpToDate = false;
    float _lastMaxDistance = -1.0f;

    TriangleMesh _curveTriangleMesh;
    float _flowStrength = 1.0;
    float _spinStrength = 2.0;
    bool _enableEndCaps = false;
    bool _isSubclassStateChangedValue = false;

    MeshLevelSet _sdf;
    Array3d<vmath::vec3> _vectorField;

    int _numDebugProbes = 600;
    float _jitterFactor = 0.25;
    float _minRadiusFactor = 0.5f;
    float _maxRadiusFactor = 5.0f;

};

#endif
