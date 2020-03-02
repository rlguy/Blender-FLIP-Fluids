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

#include "forcefieldsurface.h"

// DEBUG
#include <iostream>

#include "levelsetsolver.h"


ForceFieldSurface::ForceFieldSurface() {
}

ForceFieldSurface::~ForceFieldSurface() {
}

void ForceFieldSurface::update(double dt) {
    MeshObjectStatus status = _meshObject.getStatus();
    if (status.isMeshChanged) {
        _isLevelsetUpToDate = false;
    }

    float eps = 1e-6;
    if (_isMaxDistanceEnabled && std::abs(_maxDistance - _lastMaxDistance) > eps) {
        _isLevelsetUpToDate = false;
    }

    if (_isLevelsetUpToDate) {
        return;
    }

    std::cout << "Updating ForceFieldSurface " << dt << std::endl;

    TriangleMesh mesh = _meshObject.getMesh();

    if (_isMaxDistanceEnabled) {
        AABB bbox(mesh.vertices);
        bbox.expand(eps + 2.0f * _maxDistance);
        vmath::vec3 pmin = bbox.getMinPoint();
        vmath::vec3 pmax = bbox.getMaxPoint();

        GridIndex gmin = Grid3d::positionToGridIndex(pmin, _dx);
        GridIndex gmax = Grid3d::positionToGridIndex(pmax, _dx);

        _ioffsetSDF = std::max(gmin.i, 0);
        _joffsetSDF = std::max(gmin.j, 0);
        _koffsetSDF = std::max(gmin.k, 0);
        _offsetSDF = vmath::vec3(_ioffsetSDF * _dx, _joffsetSDF * _dx, _koffsetSDF * _dx);
        gmax.i = std::min(gmax.i + 1, _isize - 1);
        gmax.j = std::min(gmax.j + 1, _jsize - 1);
        gmax.k = std::min(gmax.k + 1, _ksize - 1);
        _isizeSDF = gmax.i - _ioffsetSDF + 1;
        _jsizeSDF = gmax.j - _joffsetSDF + 1;
        _ksizeSDF = gmax.k - _koffsetSDF + 1;
    } else {
        _ioffsetSDF = 0;
        _joffsetSDF = 0;
        _koffsetSDF = 0;
        _offsetSDF = vmath::vec3(0.0f, 0.0f, 0.0f);
        _isizeSDF = _isize;
        _jsizeSDF = _jsize;
        _ksizeSDF = _ksize;
    }

    int si, sj, sk;
    _sdf.getGridDimensions(&si, &sj, &sk);
    if (si != _isizeSDF || sj != _jsizeSDF || sk != _ksizeSDF) {
        _sdf = MeshLevelSet(_isizeSDF, _jsizeSDF, _ksizeSDF, _dx);
        _sdf.disableVelocityData();
        _sdf.disableSignCalculation();
    } else {
        _sdf.reset();
    }

    mesh.translate(-_offsetSDF);
    _sdf.fastCalculateSignedDistanceField(mesh, _exactBand);

    Array3d<float> *_phigrid = _sdf.getPhiArray3d();
    Array3d<float> tempphi(_phigrid->width, _phigrid->height, _phigrid->depth, 0.0f);

    std::vector<GridIndex> solverGridCells;
    solverGridCells.reserve(_phigrid->width * _phigrid->height * _phigrid->depth);
    for (int k = 0; k < _phigrid->depth; k++) {
        for (int j = 0; j < _phigrid->height; j++) {
            for (int i = 0; i < _phigrid->width; i++) {
                if (std::abs(_phigrid->get(i, j, k)) >= _exactBand * _dx) {
                    solverGridCells.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    float width = std::max(_isizeSDF, std::max(_jsizeSDF, _ksizeSDF)) * _dx;

    LevelSetSolver solver;
    solver.reinitializeUpwind(*_phigrid, _dx, width, solverGridCells, tempphi);

    for (size_t i = 0; i < solverGridCells.size(); i++) {
        GridIndex g = solverGridCells[i];
        _phigrid->set(g, tempphi(g));
    }

    _lastMaxDistance = _isMaxDistanceEnabled ? _maxDistance : -1.0f;
    _isLevelsetUpToDate = true;
}

void ForceFieldSurface::addForceFieldToGrid(MACVelocityField &fieldGrid) {
    std::cout << "Adding ForceFieldSurface to grid" << std::endl;

    float minDistance = -1.0f;
    float maxDistance = std::numeric_limits<float>::infinity();
    if (_isMinDistanceEnabled) {
        minDistance = _minDistance;
    }
    if (_isMaxDistanceEnabled) {
        maxDistance = _maxDistance;
    }

    float eps = 1e-6;
    float power = _falloffPower;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 gp = Grid3d::FaceIndexToPositionU(i, j, k, _dx);
                if (!Grid3d::isPositionInGrid(gp - _offsetSDF, _dx, _isizeSDF, _jsizeSDF, _ksizeSDF)) {
                    continue;
                }

                float r = std::max(std::abs(_sdf.trilinearInterpolate(gp - _offsetSDF)), minDistance);
                if (r < eps || r > maxDistance) {
                    continue;
                }

                vmath::vec3 dir = _sdf.trilinearInterpolateGradient(gp - _offsetSDF);
                if (dir.length() < eps) {
                    continue;
                }

                dir = dir.normalize();
                vmath::vec3 force = _strength * (1.0f / std::pow(r, power)) * dir;
                fieldGrid.addU(i, j, k, force.x);
            }
        }
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize; i++) {
                vmath::vec3 gp = Grid3d::FaceIndexToPositionV(i, j, k, _dx);
                if (!Grid3d::isPositionInGrid(gp - _offsetSDF, _dx, _isizeSDF, _jsizeSDF, _ksizeSDF)) {
                    continue;
                }

                float r = std::max(std::abs(_sdf.trilinearInterpolate(gp - _offsetSDF)), minDistance);
                if (r < eps || r > maxDistance) {
                    continue;
                }

                vmath::vec3 dir = _sdf.trilinearInterpolateGradient(gp - _offsetSDF);
                if (dir.length() < eps) {
                    continue;
                }

                dir = dir.normalize();
                vmath::vec3 force = _strength * (1.0f / std::pow(r, power)) * dir;
                fieldGrid.addV(i, j, k, force.y);
            }
        }
    }

    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                vmath::vec3 gp = Grid3d::FaceIndexToPositionW(i, j, k, _dx);
                if (!Grid3d::isPositionInGrid(gp - _offsetSDF, _dx, _isizeSDF, _jsizeSDF, _ksizeSDF)) {
                    continue;
                }

                float r = std::max(std::abs(_sdf.trilinearInterpolate(gp - _offsetSDF)), minDistance);
                if (r < eps || r > maxDistance) {
                    continue;
                }

                vmath::vec3 dir = _sdf.trilinearInterpolateGradient(gp - _offsetSDF);
                if (dir.length() < eps) {
                    continue;
                }

                dir = dir.normalize();
                vmath::vec3 force = _strength * (1.0f / std::pow(r, power)) * dir;
                fieldGrid.addW(i, j, k, force.z);
            }
        }
    }
}

std::vector<vmath::vec3> ForceFieldSurface::generateDebugProbes() {
    return std::vector<vmath::vec3>();
}

void ForceFieldSurface::_initialize() {
    std::cout << "Initializing ForceFieldSurface " << _isize << " " << _jsize << " " << _ksize << " " << _dx << std::endl;
}