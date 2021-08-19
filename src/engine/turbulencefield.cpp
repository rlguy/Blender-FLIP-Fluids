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

#include "turbulencefield.h"

#include "threadutils.h"
#include "interpolation.h"
#include "fluidsimassert.h"
#include "grid3d.h"
#include "macvelocityfield.h"
#include "particlelevelset.h"

TurbulenceField::TurbulenceField() {
}


TurbulenceField::~TurbulenceField() {
}

float TurbulenceField::operator()(int i, int j, int k) {
    FLUIDSIM_ASSERT(_field.isIndexInRange(i, j, k));
    return _field(i, j, k);
}

float TurbulenceField::operator()(GridIndex g) {
    FLUIDSIM_ASSERT(_field.isIndexInRange(g));
    return _field(g);
}

void TurbulenceField::_getVelocityGrid(MACVelocityField *macfield, 
                                       Array3d<vmath::vec3> &vgrid) {

    int gridsize = vgrid.width * vgrid.height * vgrid.depth;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&TurbulenceField::_getVelocityGridThread, this,
                                 intervals[i], intervals[i + 1], macfield, &vgrid);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void TurbulenceField::_getVelocityGridThread(int startidx, int endidx, 
                                             MACVelocityField *vfield, 
                                             Array3d<vmath::vec3> *vgrid) {
    int isize = vgrid->width;
    int jsize = vgrid->height;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        vgrid->set(g, vfield->evaluateVelocityAtCellCenter(g.i, g.j, g.k));
    }
}

void TurbulenceField::calculateTurbulenceField(MACVelocityField *vfield,
                                               ParticleLevelSet &liquidSDF) {

    int isize, jsize, ksize;
    vfield->getGridDimensions(&isize, &jsize, &ksize);

    GridIndexVector fluidcells(isize, jsize, ksize);
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                if (liquidSDF(i, j, k) < 0.0f) {
                    fluidcells.push_back(i, j, k);
                }
            }
        }
    }

    calculateTurbulenceField(vfield, fluidcells);
}

void TurbulenceField::calculateTurbulenceField(MACVelocityField *vfield,
                                               GridIndexVector &fluidCells) {
    vfield->getGridDimensions(&_isize, &_jsize, &_ksize);
    _dx = vfield->getGridCellSize();
    _radius = sqrt(3.0*(2*_dx)*(2*_dx));  // maximum distance from center grid cell
                                          // to its 124 neighbours

    if (_field.width != _isize || _field.height != _jsize || _field.depth != _ksize) {
        _field = Array3d<float>(_isize, _jsize, _ksize);
    }
    _field.fill(0.0f);

    Array3d<vmath::vec3> vgrid = Array3d<vmath::vec3>(_isize, _jsize, _ksize);
    _getVelocityGrid(vfield, vgrid);

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, fluidCells.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, fluidCells.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&TurbulenceField::_calculateTurbulenceFieldThread, this,
                                 intervals[i], intervals[i + 1], &vgrid, &fluidCells);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void TurbulenceField::_calculateTurbulenceFieldThread(int startidx, int endidx,
                                                      Array3d<vmath::vec3> *vgrid,
                                                      GridIndexVector *fluidCells) {
    double eps = 10e-6;
    double invradius = 1.0 / _radius;
    vmath::vec3 vi, vj, vij, vijnorm, xi, xj, xij, xijnorm;

    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = fluidCells->at(idx);
        int i = g.i;
        int j = g.j;
        int k = g.k;

        vi = vgrid->get(i, j, k);
        xi = Grid3d::GridIndexToCellCenter(i, j, k, _dx);
        double vlen, xlen;
        double turb = 0.0;

        for (int nk = fmax(k - 2, 0); nk < fmin(k + 2, _ksize - 1); nk++) {
            for (int nj = fmax(j - 2, 0); nj < fmin(j + 2, _jsize - 1); nj++) {
                for (int ni = fmax(i - 2, 0); ni < fmin(i + 2, _isize - 1); ni++) {
                    vj = vgrid->get(ni, nj, nk);
                    vij = vi - vj;
                    vlen = vmath::length(vij);

                    if (fabs(vlen) < eps) {
                        continue;
                    }
                    vijnorm = vij / (float)vlen;

                    xj = Grid3d::GridIndexToCellCenter(ni, nj, nk, _dx);
                    xij = xi - xj;
                    xlen = vmath::length(xij);
                    xijnorm = xij / (float)xlen;

                    turb += vlen*(1.0 - vmath::dot(vijnorm, xijnorm))*(1.0 - (xlen*invradius));
                }
            }
        }

        _field.set(i, j, k, turb);
    }
}

void TurbulenceField::destroyTurbulenceField() {
    _field = Array3d<float>(0, 0, 0);
}

double TurbulenceField::evaluateTurbulenceAtPosition(vmath::vec3 p) {
    FLUIDSIM_ASSERT(Grid3d::isPositionInGrid(p, _dx, _isize, _jsize, _ksize));

    p -= vmath::vec3(0.5*_dx, 0.5*_dx, 0.5*_dx);

    int i, j, k;
    double gx, gy, gz;
    Grid3d::positionToGridIndex(p.x, p.y, p.z, _dx, &i, &j, &k);
    Grid3d::GridIndexToPosition(i, j, k, _dx, &gx, &gy, &gz);

    double inv_dx = 1 / _dx;
    double ix = (p.x - gx)*inv_dx;
    double iy = (p.y - gy)*inv_dx;
    double iz = (p.z - gz)*inv_dx;

    double points[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    if (_field.isIndexInRange(i,   j,   k))   { points[0] = _field(i,   j,   k); }
    if (_field.isIndexInRange(i+1, j,   k))   { points[1] = _field(i+1, j,   k); }
    if (_field.isIndexInRange(i,   j+1, k))   { points[2] = _field(i,   j+1, k); }
    if (_field.isIndexInRange(i,   j,   k+1)) { points[3] = _field(i,   j,   k+1); }
    if (_field.isIndexInRange(i+1, j,   k+1)) { points[4] = _field(i+1, j,   k+1); }
    if (_field.isIndexInRange(i,   j+1, k+1)) { points[5] = _field(i,   j+1, k+1); }
    if (_field.isIndexInRange(i+1, j+1, k))   { points[6] = _field(i+1, j+1, k); }
    if (_field.isIndexInRange(i+1, j+1, k+1)) { points[7] = _field(i+1, j+1, k+1); }

    return Interpolation::trilinearInterpolate(points, ix, iy, iz);
}