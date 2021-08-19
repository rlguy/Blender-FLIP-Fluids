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

#include "meshfluidsource.h"

int MeshFluidSource::_IDCounter = 0;

MeshFluidSource::MeshFluidSource() {
}

MeshFluidSource::MeshFluidSource(int i, int j, int k, double dx) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), 
        _meshObject(i, j, k, dx) {
    _initializeID();
}

MeshFluidSource::~MeshFluidSource() {
}

void MeshFluidSource::updateMeshStatic(TriangleMesh meshCurrent) {
    _meshObject.updateMeshStatic(meshCurrent);
}

void MeshFluidSource::updateMeshAnimated(TriangleMesh meshPrevious, 
                                         TriangleMesh meshCurrent, 
                                         TriangleMesh meshNext) {
    _meshObject.updateMeshAnimated(meshPrevious, meshCurrent, meshNext);
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
    if (n < 0) {
        n = 0;
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

bool MeshFluidSource::isRigidBody() {
    return _meshObject.isRigidBody();
}

void MeshFluidSource::enableConstrainedFluidVelocity() {
    _isConstrainedFluidVelocity = true;
}

void MeshFluidSource::disableConstrainedFluidVelocity() {
    _isConstrainedFluidVelocity = false;
}

bool MeshFluidSource::isConstrainedFluidVelocityEnabled() {
    return _isConstrainedFluidVelocity;
}

void MeshFluidSource::outflowInverse() {
    _isOutflowInversed = !_isOutflowInversed;
}

bool MeshFluidSource::isOutflowInversed() {
    return _isOutflowInversed;
}

void MeshFluidSource::setFrame(int f, float frameInterpolation) {
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

    GridIndex gmin, gmax;
    _getGridBoundsFromTriangleMesh(sourceMesh, _gridpad, gmin, gmax);
    _sourceSDFGridOffset = gmin;
    _sourceSDFOffset = Grid3d::GridIndexToPosition(gmin, _dx);
    int isdf = std::max(gmax.i - gmin.i + 1, 1);
    int jsdf = std::max(gmax.j - gmin.j + 1, 1);
    int ksdf = std::max(gmax.k - gmin.k + 1, 1);

    int isdfcurr, jsdfcurr, ksdfcurr;
    _sourceSDF.getGridDimensions(&isdfcurr, &jsdfcurr, &ksdfcurr);

    if (isdfcurr != isdf || jsdfcurr != jsdf || ksdfcurr != ksdf) {
        _sourceSDF = MeshLevelSet(isdf, jsdf, ksdf, _dx);
    }

    std::vector<vmath::vec3> vertexVelocities = _meshObject.getVertexVelocities(dt, _currentFrameInterpolation);
    AABB domainbbox(vmath::vec3(), (_isize + 1) * _dx, (_jsize + 1) * _dx, (_ksize + 1) * _dx);
    AABB meshbbox(sourceMesh.vertices);
    double eps = (_dx * _dx * _dx) * 0.125;
    if (!meshbbox.isIntersecting(domainbbox, eps)) {
        sourceMesh = TriangleMesh();
        vertexVelocities.clear();
    }
    sourceMesh.translate(-_sourceSDFOffset);

    if (isRigidBody()) {
        _sourceSDF.disableVelocityData();
    } else {
        _sourceSDF.enableVelocityData();
    }
    _sourceSDF.fastCalculateSignedDistanceField(sourceMesh, vertexVelocities, _exactBand);

    if (!isRigidBody() && meshbbox.isIntersecting(domainbbox)) {
        _calculateVelocityFieldData();
    }

    _isUpToDate = true;
}

float MeshFluidSource::trilinearInterpolate(vmath::vec3 p) {
    return _sourceSDF.trilinearInterpolate(p - _sourceSDFOffset);
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

vmath::vec3 MeshFluidSource::getMeshLevelSetOffset() {
    return _sourceSDFOffset;
}

RigidBodyVelocity MeshFluidSource::getRigidBodyVelocity(double framedt) {
    return _meshObject.getRigidBodyVelocity(framedt);
}

int MeshFluidSource::getID() {
    return _ID;
}

void MeshFluidSource::setSourceID(int id) {
    _meshObject.setSourceID(id);
}

int MeshFluidSource::getSourceID() {
    return _meshObject.getSourceID();
}

void MeshFluidSource::setSourceColor(vmath::vec3 c) {
    _meshObject.setSourceColor(c);
}

vmath::vec3 MeshFluidSource::getSourceColor() {
    return _meshObject.getSourceColor();
}

void MeshFluidSource::_initializeID() {
    _ID = _IDCounter++;
}

void MeshFluidSource::_calculateVelocityFieldData() {
    int isize, jsize, ksize;
    _sourceSDF.getGridDimensions(&isize, &jsize, &ksize);

    VelocityFieldData vdata;
    vdata.vfield = MACVelocityField(isize, jsize, ksize, _dx);
    vdata.offset = _sourceSDFOffset;
    vdata.gridOffset = _sourceSDFGridOffset;

    ValidVelocityComponentGrid valid(isize, jsize, ksize);
    VelocityDataGrid *sdfvgrid = _sourceSDF.getVelocityDataGrid();

    double maxd = 2.0 * _dx;
    float vscale = getObjectVelocityInfluence();
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize + 1; i++) {
                vmath::vec3 p = Grid3d::FaceIndexToPositionU(i, j, k, _dx);
                float d = _sourceSDF.trilinearInterpolate(p);
                if (d < maxd) {
                    vdata.vfield.setU(i, j, k, vscale * sdfvgrid->field.U(i, j, k));
                    valid.validU.set(i, j, k, true);
                }
            }
        }
    }

    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize + 1; j++) {
            for (int i = 0; i < isize; i++) {
                vmath::vec3 p = Grid3d::FaceIndexToPositionV(i, j, k, _dx);
                float d = _sourceSDF.trilinearInterpolate(p);
                if (d < maxd) {
                    vdata.vfield.setV(i, j, k, vscale * sdfvgrid->field.V(i, j, k));
                    valid.validV.set(i, j, k, true);
                }
            }
        }
    }

    for (int k = 0; k < ksize + 1; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                vmath::vec3 p = Grid3d::FaceIndexToPositionW(i, j, k, _dx);
                float d = _sourceSDF.trilinearInterpolate(p);
                if (d < maxd) {
                    vdata.vfield.setW(i, j, k, vscale * sdfvgrid->field.W(i, j, k));
                    valid.validW.set(i, j, k, true);
                }
            }
        }
    }

    int layers = isize + jsize + ksize;
    vdata.vfield.extrapolateVelocityField(valid, layers);
    _vfieldData = vdata;
}

void MeshFluidSource::_getGridBoundsFromTriangleMesh(TriangleMesh &m, double pad, 
                                                     GridIndex &gmin, GridIndex &gmax) {
    AABB bbox(m.vertices);
    bbox.expand(pad * _dx);
    vmath::vec3 pmin = bbox.getMinPoint();
    vmath::vec3 pmax = bbox.getMaxPoint();
    gmin = Grid3d::positionToGridIndex(pmin, _dx);
    gmax = Grid3d::positionToGridIndex(pmax, _dx);

    gmin.i = fmax(gmin.i, 0);
    gmin.j = fmax(gmin.j, 0);
    gmin.k = fmax(gmin.k, 0);
    gmax.i = fmin(gmax.i, _isize - 1);
    gmax.j = fmin(gmax.j, _jsize - 1);
    gmax.k = fmin(gmax.k, _ksize - 1);
}

VelocityFieldData* MeshFluidSource::getVelocityFieldData() {
    return &_vfieldData;   
}