/*
MIT License

Copyright (c) 2018 Ryan L. Guy

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

#ifndef FLUIDENGINE_MESHFLUIDSOURCE_H
#define FLUIDENGINE_MESHFLUIDSOURCE_H

#include "meshobject.h"
#include "macvelocityfield.h"

struct VelocityFieldData {
        MACVelocityField vfield;
        vmath::vec3 offset;
        GridIndex gridOffset;
    };

class MeshFluidSource
{
public:
    MeshFluidSource();
    MeshFluidSource(int i, int j, int k, double dx, TriangleMesh mesh);
    MeshFluidSource(int i, int j, int k, double dx, std::vector<TriangleMesh> meshes);
    MeshFluidSource(int i, int j, int k, double dx, 
                    std::vector<TriangleMesh> meshes, 
                    std::vector<TriangleMesh> translations);
    ~MeshFluidSource();
    
    void enable();
    void disable();
    bool isEnabled();

    void setSubstepEmissions(int n);
    int getSubstepEmissions();

    void setInflow();
    bool isInflow();
    void setOutflow();
    bool isOutflow();

    void enableFluidOutflow();
    void disableFluidOutflow();
    bool isFluidOutflowEnabled();

    void enableDiffuseOutflow();
    void disableDiffuseOutflow();
    bool isDiffuseOutflowEnabled();

    void setVelocity(vmath::vec3 v);
    vmath::vec3 getVelocity();

    void enableAppendObjectVelocity();
    void disableAppendObjectVelocity();
    bool isAppendObjectVelocityEnabled();

    void setObjectVelocityInfluence(float value);
    float getObjectVelocityInfluence();

    void enableRigidMesh();
    void disableRigidMesh();
    bool isRigidMeshEnabled();

    void outflowInverse();
    bool isOutflowInversed();

    void setFrame(int f, float frameInterpolation);
    void update(double dt);
    void getCells(std::vector<GridIndex> &cells);
    void getCells(float frameInterpolation, std::vector<GridIndex> &cells);
    MeshObject* getMeshObject();
    MeshLevelSet* getMeshLevelSet();
    RigidBodyVelocity getRigidBodyVelocity(double framedt);
    VelocityFieldData* getVelocityFieldData();
    int getID();

private:

    void _initializeID();
    void _calculateVelocityFieldData();

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    int _currentFrame = 0;
    float _currentFrameInterpolation = 0.0f;
    bool _isUpToDate = false;
    int _exactBand = 2;

    bool _isEnabled = true;
    int _substepEmissions = 1;
    bool _isInflow = true;
    bool _isFluidOutflowEnabled = true;
    bool _isDiffuseOutflowEnabled = true;
    bool _isOutflowInversed = false;
    bool _isRigidMesh = true;
    vmath::vec3 _sourceVelocity;
    VelocityFieldData _vfieldData;

    MeshObject _meshObject;
    MeshLevelSet _sourceSDF;

    int _ID;
    static int _IDCounter;

};

#endif
