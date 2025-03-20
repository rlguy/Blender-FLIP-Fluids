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

#ifndef FLUIDENGINE_FORCEFIELD_H
#define FLUIDENGINE_FORCEFIELD_H

#include "trianglemesh.h"
#include "meshobject.h"
#include "macvelocityfield.h"
#include "forcefieldgravityscalegrid.h"


class ForceField
{
public:
    ForceField();
    virtual ~ForceField() = 0;

    void updateMeshStatic(TriangleMesh meshCurrent);
    void updateMeshAnimated(TriangleMesh meshPrevious, 
                            TriangleMesh meshCurrent, 
                            TriangleMesh meshNext);

    void enable();
    void disable();
    bool isEnabled();

    void initialize(int isize, int jsize, int ksize, double dx);

    bool isStateChanged();
    void clearState();

    float getStrength();
    void setStrength(float s);

    float getFalloffPower();
    void setFalloffPower(float p);

    float getMaxForceLimitFactor();
    void setMaxForceLimitFactor(float p);

    void enableMinDistance();
    void disableMinDistance();
    bool isMinDistanceEnabled();

    float getMinDistance();
    void setMinDistance(float d);

    void enableMaxDistance();
    void disableMaxDistance();
    bool isMaxDistanceEnabled();

    float getMaxDistance();
    void setMaxDistance(float d);

    void enableFrontfacing();
    void disableFrontfacing();
    bool isFrontfacingEnabled();

    void enableBackfacing();
    void disableBackfacing();
    bool isBackfacingEnabled();

    void enableEdgefacing();
    void disableEdgefacing();
    bool isEdgefacingEnabled();

    float getGravityScale();
    void setGravityScale(float s);

    float getGravityScaleWidth();
    void setGravityScaleWidth(float w);
    
    virtual void update(double dt, double frameInterpolation) = 0;
    virtual void addForceFieldToGrid(MACVelocityField &fieldGrid) = 0;
    virtual void addGravityScaleToGrid(ForceFieldGravityScaleGrid &scaleGrid) = 0;
    virtual std::vector<vmath::vec3> generateDebugProbes() = 0;

protected:

    virtual void _initialize() = 0;
    virtual bool _isSubclassStateChanged() = 0;
    virtual void _clearSubclassState() = 0;

    vmath::vec3 _limitForceVector(vmath::vec3 v, float strength);
    vmath::vec3 _calculateForceVector(float radius, vmath::vec3 normal);
    vmath::vec3 _calculateForceVector(float radius, float strength, vmath::vec3 normal);

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 1.0;
    bool _isInitialized = false;
    bool _isStateChanged = true;

    MeshObject _meshObject;

    float _strength = 0.0f;
    float _falloffPower = 1.0f;
    float _maxForceLimitFactor = 3.0f;

    bool _isMinDistanceEnabled = false;
    float _minDistance = 0.0f;

    bool _isMaxDistanceEnabled = false;
    float _maxDistance = 0.0f;

    float _isFrontfacingEnabled = true;
    float _isBackfacingEnabled = true;
    float _isEdgefacingEnabled = true;

    float _gravityScale = 1.0f;
    float _gravityScaleWidth = 0.0f;
    float _gravityScaleFalloffThreshold = 0.90f;    // in % of the width
    
};

#endif
