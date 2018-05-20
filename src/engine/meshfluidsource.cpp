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

#include "meshfluidsource.h"

int MeshFluidSource::_IDCounter = 0;

MeshFluidSource::MeshFluidSource() {
}

MeshFluidSource::MeshFluidSource(int i, int j, int k, double dx, TriangleMesh mesh) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), 
        _meshObject(i, j, k, dx, mesh),
        _sourceSDF(i, j, k, dx) {
    _initializeID();
}

MeshFluidSource::MeshFluidSource(int i, int j, int k, double dx, 
                   std::vector<TriangleMesh> meshes) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), 
        _meshObject(i, j, k, dx, meshes),
        _sourceSDF(i, j, k, dx) {
    _initializeID();
}

MeshFluidSource::MeshFluidSource(int i, int j, int k, double dx, 
                   std::vector<TriangleMesh> meshes,
                   std::vector<TriangleMesh> translations) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), 
        _meshObject(i, j, k, dx, meshes, translations),
        _sourceSDF(i, j, k, dx) {
    _initializeID();
}

MeshFluidSource::~MeshFluidSource() {
}

void MeshFluidSource::enable() {
    _isEnabled = true;
}

void MeshFluidSource::disable() {
    _isEnabled = false;
}

bool MeshFluidSource::isEnabled() {
    return _isEnabled;
}

void MeshFluidSource::setSubstepEmissions(int n) {
    if (n < 1) {
        n = 1;
    }
    _substepEmissions = n;
}

int MeshFluidSource::getSubstepEmissions() {
    return _substepEmissions;
}

void MeshFluidSource::setInflow() {
    _isInflow = true;
}

bool MeshFluidSource::isInflow() {
    return _isInflow;
}

void MeshFluidSource::setOutflow() {
    _isInflow = false;
}

bool MeshFluidSource::isOutflow() {
    return !_isInflow;
}

void MeshFluidSource::enableFluidOutflow() {
    _isFluidOutflowEnabled = true;
}

void MeshFluidSource::disableFluidOutflow() {
    _isFluidOutflowEnabled = false;
}

bool MeshFluidSource::isFluidOutflowEnabled() {
    return _isFluidOutflowEnabled;
}

void MeshFluidSource::enableDiffuseOutflow() {
    _isDiffuseOutflowEnabled = true;
}

void MeshFluidSource::disableDiffuseOutflow() {
    _isDiffuseOutflowEnabled = false;
}

bool MeshFluidSource::isDiffuseOutflowEnabled() {
    return _isDiffuseOutflowEnabled;
}

void MeshFluidSource::setVelocity(vmath::vec3 v) {
    _sourceVelocity = v;
}

vmath::vec3 MeshFluidSource::getVelocity() {
    return _sourceVelocity;
}

void MeshFluidSource::enableAppendObjectVelocity() {
    _meshObject.enableAppendObjectVelocity();
}

void MeshFluidSource::disableAppendObjectVelocity() {
     _meshObject.disableAppendObjectVelocity();
}

bool MeshFluidSource::isAppendObjectVelocityEnabled() {
    return _meshObject.isAppendObjectVelocityEnabled();
}

void MeshFluidSource::setObjectVelocityInfluence(float value) {
    _meshObject.setObjectVelocityInfluence(value);
}

float MeshFluidSource::getObjectVelocityInfluence() {
    return _meshObject.getObjectVelocityInfluence();
}

void MeshFluidSource::enableRigidMesh() {
    _isRigidMesh = true;
}

void MeshFluidSource::disableRigidMesh() {
    _isRigidMesh = false;
}

bool MeshFluidSource::isRigidMeshEnabled() {
    return _isRigidMesh;
}

void MeshFluidSource::outflowInverse() {
    _isOutflowInversed = !_isOutflowInversed;
}

bool MeshFluidSource::isOutflowInversed() {
    return _isOutflowInversed;
}

void MeshFluidSource::setFrame(int f, float frameInterpolation) {
    _meshObject.setFrame(f);

    float eps = 1e-6;
    bool isFrameChanged = f != _currentFrame;
    bool isInterpolationChanged = fabs(frameInterpolation - _currentFrameInterpolation) > eps;
    _currentFrame = f;
    _currentFrameInterpolation = frameInterpolation;

    if ((isFrameChanged || isInterpolationChanged) && _meshObject.isAnimated()) {
        _isUpToDate = false;
    }
}

void MeshFluidSource::update(double dt) {
    if (_isUpToDate) {
        return;
    }

    TriangleMesh sourceMesh = _meshObject.getMesh(_currentFrameInterpolation);
    std::vector<vmath::vec3> vertexVelocities = _meshObject.getVertexVelocities(dt, _currentFrameInterpolation);
    AABB domainbbox(vmath::vec3(), (_isize + 1) * _dx, (_jsize + 1) * _dx, (_ksize + 1) * _dx);

    if (_isRigidMesh) {
        _sourceSDF.disableVelocityData();
    } else {
        _sourceSDF.enableVelocityData();
    }
    _sourceSDF.fastCalculateSignedDistanceField(sourceMesh, vertexVelocities, _exactBand);

    if (!_isRigidMesh) {
        _calculateVelocityFieldData();
    }

    _isUpToDate = true;
}

void MeshFluidSource::getCells(std::vector<GridIndex> &cells) {
    getCells(0.0f, cells);
}

void MeshFluidSource::getCells(float frameInterpolation, std::vector<GridIndex> &cells) {
    _meshObject.getCells(frameInterpolation, cells);
}

MeshObject* MeshFluidSource::getMeshObject() {
    return &_meshObject;
}

MeshLevelSet* MeshFluidSource::getMeshLevelSet() {
    return &_sourceSDF;
}

RigidBodyVelocity MeshFluidSource::getRigidBodyVelocity(double framedt) {
    return _meshObject.getRigidBodyVelocity(framedt);
}

int MeshFluidSource::getID() {
    return _ID;
}

void MeshFluidSource::_initializeID() {
    _ID = _IDCounter++;
}

void MeshFluidSource::_calculateVelocityFieldData() {
    TriangleMesh sourceMesh = _meshObject.getMesh(_currentFrameInterpolation);
    AABB bbox(sourceMesh.vertices);
    bbox.expand(4.0*_dx);
    vmath::vec3 pmin = bbox.getMinPoint();
    vmath::vec3 pmax = bbox.getMaxPoint();
    GridIndex gmin = Grid3d::positionToGridIndex(pmin, _dx);
    GridIndex gmax = Grid3d::positionToGridIndex(pmax, _dx);

    gmin.i = fmax(gmin.i, 0);
    gmin.j = fmax(gmin.j, 0);
    gmin.k = fmax(gmin.k, 0);
    gmax.i = fmin(gmax.i, _isize - 1);
    gmax.j = fmin(gmax.j, _jsize - 1);
    gmax.k = fmin(gmax.k, _ksize - 1);

    int isize = gmax.i - gmin.i + 1;
    int jsize = gmax.j - gmin.j + 1;
    int ksize = gmax.k - gmin.k + 1;
    vmath::vec3 offset = Grid3d::GridIndexToPosition(gmin, _dx);

    VelocityFieldData vdata;
    vdata.vfield = MACVelocityField(isize, jsize, ksize, _dx);
    vdata.offset = offset;
    vdata.gridOffset = gmin;

    ValidVelocityComponentGrid valid(isize, jsize, ksize);
    VelocityDataGrid *sdfvgrid = _sourceSDF.getVelocityDataGrid();

    double maxd = 2.0 * _dx;
    float vscale = getObjectVelocityInfluence();
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize + 1; i++) {
                GridIndex g(gmin.i + i, gmin.j + j, gmin.k + k);
                vmath::vec3 p = Grid3d::FaceIndexToPositionU(g, _dx);
                float d = _sourceSDF.trilinearInterpolate(p);
                if (d < maxd) {
                    vdata.vfield.setU(i, j, k, vscale * sdfvgrid->field.U(g));
                    valid.validU.set(i, j, k, true);
                }
            }
        }
    }

    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize + 1; j++) {
            for (int i = 0; i < isize; i++) {
                GridIndex g(gmin.i + i, gmin.j + j, gmin.k + k);
                vmath::vec3 p = Grid3d::FaceIndexToPositionV(g, _dx);
                float d = _sourceSDF.trilinearInterpolate(p);
                if (d < maxd) {
                    vdata.vfield.setV(i, j, k, vscale * sdfvgrid->field.V(g));
                    valid.validV.set(i, j, k, true);
                }
            }
        }
    }

    for (int k = 0; k < ksize + 1; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                GridIndex g(gmin.i + i, gmin.j + j, gmin.k + k);
                vmath::vec3 p = Grid3d::FaceIndexToPositionW(g, _dx);
                float d = _sourceSDF.trilinearInterpolate(p);
                if (d < maxd) {
                    vdata.vfield.setW(i, j, k, vscale * sdfvgrid->field.W(g));
                    valid.validW.set(i, j, k, true);
                }
            }
        }
    }

    int layers = isize + jsize + ksize;
    vdata.vfield.extrapolateVelocityField(valid, layers);
    _vfieldData = vdata;
}

VelocityFieldData* MeshFluidSource::getVelocityFieldData() {
    return &_vfieldData;   
}