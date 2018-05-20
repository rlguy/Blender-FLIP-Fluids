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

#include "particlelevelset.h"

#include "levelsetutils.h"
#include "interpolation.h"
#include "polygonizer3d.h"
#include "gridutils.h"
#include "threadutils.h"
#include "markerparticle.h"
#include "grid3d.h"
#include "meshlevelset.h"
#include "scalarfield.h"

ParticleLevelSet::ParticleLevelSet() {
}

ParticleLevelSet::ParticleLevelSet(int i, int j, int k, double dx) : 
                    _isize(i), _jsize(j), _ksize(k), _dx(dx) {
    _phi = Array3d<float>(i, j, k, _getMaxDistance());
}

ParticleLevelSet::~ParticleLevelSet() {
}

float ParticleLevelSet::operator()(int i, int j, int k) {
    return get(i, j, k);
}

float ParticleLevelSet::operator()(GridIndex g) {
    return get(g);
}

float ParticleLevelSet::get(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));
    return _phi(i, j, k);
}

float ParticleLevelSet::get(GridIndex g) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize));
    return _phi(g);
}

float ParticleLevelSet::getFaceWeightU(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize, _ksize));
    return LevelsetUtils::fractionInside(_phi(i - 1, j, k), _phi(i, j, k));
}

float ParticleLevelSet::getFaceWeightU(GridIndex g) {
    return getFaceWeightU(g.i, g.j, g.k);
}

float ParticleLevelSet::getFaceWeightV(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize + 1, _ksize));
    return LevelsetUtils::fractionInside(_phi(i, j - 1, k), _phi(i, j, k));
}

float ParticleLevelSet::getFaceWeightV(GridIndex g) {
    return getFaceWeightV(g.i, g.j, g.k);
}

float ParticleLevelSet::getFaceWeightW(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize + 1));
    return LevelsetUtils::fractionInside(_phi(i, j, k - 1), _phi(i, j, k));
}

float ParticleLevelSet::getFaceWeightW(GridIndex g) {
    return getFaceWeightW(g.i, g.j, g.k);
}

void ParticleLevelSet::getNodalPhi(Array3d<float> &nodalPhi) {
    FLUIDSIM_ASSERT(nodalPhi.width == _isize + 1 && 
                    nodalPhi.height == _jsize + 1 && 
                    nodalPhi.depth == _ksize + 1);

    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {

                float sum = 0.0;
                if (Grid3d::isGridIndexInRange(i - 1, j - 1, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j - 1, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i, j - 1, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j - 1, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i - 1, j, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i, j, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i - 1, j - 1, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j - 1, k);
                }
                if (Grid3d::isGridIndexInRange(i, j - 1, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j - 1, k);
                }
                if (Grid3d::isGridIndexInRange(i - 1, j, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j, k);
                }
                if (Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j, k);
                }

                nodalPhi.set(i, j, k, 0.125f * sum);
            }
        }
    }
}

float ParticleLevelSet::trilinearInterpolate(vmath::vec3 pos) {
    return Interpolation::trilinearInterpolate(pos - vmath::vec3(0.5*_dx, 0.5*_dx, 0.5*_dx), _dx, _phi);
}

float ParticleLevelSet::getDistanceAtNode(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize + 1, _ksize + 1));

    if (Grid3d::isGridIndexOnBorder(i, j, k, _isize + 1, _jsize + 1, _ksize + 1)) {
        return _getMaxDistance();
    }

    return 0.125f * (_phi(i - 1, j - 1, k - 1) + 
                     _phi(i    , j - 1, k - 1) + 
                     _phi(i - 1, j    , k - 1) + 
                     _phi(i    , j    , k - 1) +
                     _phi(i - 1, j - 1, k    ) + 
                     _phi(i    , j - 1, k    ) + 
                     _phi(i - 1, j    , k    ) + 
                     _phi(i    , j    , k    ));
}

float ParticleLevelSet::getDistanceAtNode(GridIndex g) {
    return getDistanceAtNode(g.i, g.j, g.k);
}

void ParticleLevelSet::calculateSignedDistanceField(FragmentedVector<MarkerParticle> &particles, 
                                                    double radius) {
    _computeSignedDistanceFromParticles(particles, radius);
}

void ParticleLevelSet::extrapolateSignedDistanceIntoSolids(MeshLevelSet &solidPhi) {
    int si, sj, sk;
    solidPhi.getGridDimensions(&si, &sj, &sk);
    FLUIDSIM_ASSERT(si == _isize && sj == _jsize && sk == _ksize);

    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize; i++) {
                if(_phi(i, j, k) < 0.5 * _dx) {
                    if(solidPhi.getDistanceAtCellCenter(i, j, k) < 0) {
                        _phi.set(i, j, k, -0.5f * _dx);
                    }
                }
            }
        }
    }
}

void ParticleLevelSet::calculateCurvatureGrid(MeshLevelSet &surfacePhi, 
                                              Array3d<float> &kgrid) {

    int si, sj, sk;
    surfacePhi.getGridDimensions(&si, &sj, &sk);
    FLUIDSIM_ASSERT(si == _isize && sj == _jsize && sk == _ksize);
    FLUIDSIM_ASSERT(kgrid.width == _isize + 1 && 
                    kgrid.height == _jsize + 1 && 
                    kgrid.depth == _ksize + 1);


    ScalarField field = ScalarField(_isize + 1, _jsize + 1, _ksize + 1, _dx);
    field.setSurfaceThreshold(0.0f);
    _initializeCurvatureGridScalarField(field);

    Polygonizer3d polygonizer(&field);
    TriangleMesh surfaceMesh = polygonizer.polygonizeSurface();
    surfaceMesh.smooth(_curvatureGridSmoothingValue, _curvatureGridSmoothingIterations);

    surfacePhi.disableVelocityData();
    surfacePhi.disableSignCalculation();
    surfacePhi.fastCalculateSignedDistanceField(surfaceMesh, _curvatureGridExactBand);

    // Signs are already computed and are stored on the scalar field. Note:
    // field signs are reversed, so values > 0 are inside.
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                if (field.getRawScalarFieldValue(i, j, k) > 0) {
                    surfacePhi.set(i, j, k, -surfacePhi(i, j, k));
                }
            }
        }
    }

    Array3d<bool> validCurvatureNodes(_isize + 1, _jsize + 1, _ksize + 1);
    _getValidCurvatureNodes(surfacePhi, validCurvatureNodes);

    kgrid.fill(0.0f);
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                if (validCurvatureNodes(i, j, k)) {
                    kgrid.set(i, j, k, surfacePhi.getCurvature(i, j, k));
                }
            }
        }
    }

    GridUtils::extrapolateGrid(&kgrid, &validCurvatureNodes, _curvatureGridExtrapolationLayers);
}

float ParticleLevelSet::_getMaxDistance() {
    return 3.0 * _dx;
}

void ParticleLevelSet::_computeSignedDistanceFromParticles(FragmentedVector<MarkerParticle> &particles, 
                                                           double radius) {
    _phi.fill(_getMaxDistance());

    if (particles.empty()) {
        return;
    }

    int U = 0; int V = 1; int W = 2;

    vmath::vec3 minp = particles[0].position;
    vmath::vec3 maxp = particles[0].position;
    for (size_t i = 0; i < particles.size(); i++) {
        vmath::vec3 p = particles[i].position;
        minp.x = fmin(minp.x, p.x);
        minp.y = fmin(minp.y, p.y);
        minp.z = fmin(minp.z, p.z);
        maxp.x = fmax(maxp.x, p.x);
        maxp.y = fmax(maxp.y, p.y);
        maxp.z = fmax(maxp.z, p.z);
    }
    vmath::vec3 rvect(radius, radius, radius);
    minp -= rvect;
    maxp += rvect;
    vmath::vec3 diff = maxp - minp;

    int splitdir = U;
    if (diff.x > diff.y) {
        if (diff.x > diff.z) {
            splitdir = U;
        } else {
            splitdir = W;
        }
    } else {
        if (diff.y > diff.z) {
            splitdir = V;
        } else {
            splitdir = W;
        }
    }

    int i1 = 0;
    int i2 = 0;
    GridIndex gmin = Grid3d::positionToGridIndex(minp, _dx);
    GridIndex gmax = Grid3d::positionToGridIndex(maxp, _dx);
    int buffersize = 1;
    if (splitdir == U) {
        i1 = fmax(gmin.i - buffersize, 0);
        i2 = fmin(gmax.i + buffersize, _isize);
    } else if (splitdir == V) {
        i1 = fmax(gmin.j - buffersize, 0);
        i2 = fmin(gmax.j + buffersize, _jsize);
    } else if (splitdir == W) {
        i1 = fmax(gmin.k - buffersize, 0);
        i2 = fmin(gmax.k + buffersize, _ksize);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, i2 - i1);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(i1, i2, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleLevelSet::_computeSignedDistanceFromParticlesThread, this,
                                 intervals[i], intervals[i + 1], &particles, radius, splitdir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ParticleLevelSet::_computeSignedDistanceFromParticlesThread(int startidx, int endidx, 
                                                                 FragmentedVector<MarkerParticle> *particles, 
                                                                 double radius, int splitdir) {
    int U = 0; int V = 1; int W = 2;

    vmath::vec3 minp, maxp;
    if (splitdir == U) {
        minp = vmath::vec3(startidx * _dx, 0.0, 0.0);
        maxp = vmath::vec3((endidx - 1) * _dx, _jsize * _dx, _ksize * _dx);
    } else if (splitdir == V) {
        minp = vmath::vec3(0.0, startidx * _dx, 0.0);
        maxp = vmath::vec3(_isize * _dx, (endidx - 1) * _dx, _ksize * _dx);
    } else if (splitdir == W) {
        minp = vmath::vec3(0.0, 0.0, startidx * _dx);
        maxp = vmath::vec3(_isize * _dx, _jsize * _dx, (endidx - 1) * _dx);
    }
    AABB bbox(minp, maxp);
    bbox.expand(2 * radius);

    GridIndex g, gmin, gmax;
    for (size_t pidx = 0; pidx < particles->size(); pidx++) {
        vmath::vec3 p = particles->at(pidx).position;

        if (!bbox.isPointInside(p)) {
            continue;
        }

        g = Grid3d::positionToGridIndex(p, _dx);
        gmin = GridIndex(fmax(0, g.i - 1), fmax(0, g.j - 1), fmax(0, g.k - 1));
        gmax = GridIndex(fmin(g.i + 1, _isize - 1), 
                         fmin(g.j + 1, _jsize - 1), 
                         fmin(g.k + 1, _ksize - 1));

        if (splitdir == U) {
            gmin.i = fmax(gmin.i, startidx);
            gmax.i = fmin(gmax.i, endidx - 1);
        } else if (splitdir == V) {
            gmin.j = fmax(gmin.j, startidx);
            gmax.j = fmin(gmax.j, endidx - 1);
        } else if (splitdir == W) {
            gmin.k = fmax(gmin.k, startidx);
            gmax.k = fmin(gmax.k, endidx - 1);
        }

        for(int k = gmin.k; k <= gmax.k; k++) {
            for(int j = gmin.j; j <= gmax.j; j++) {
                for(int i = gmin.i; i <= gmax.i; i++) {
                    vmath::vec3 cpos = Grid3d::GridIndexToCellCenter(i, j, k, _dx);
                    float dist = vmath::length(cpos - p) - radius;
                    if(dist < _phi(i, j, k)) {
                        _phi.set(i, j, k, dist);
                    }
                }
            }
        }

    }
}

void ParticleLevelSet::_initializeCurvatureGridScalarField(ScalarField &field) {
    int gridsize = (_isize + 1) * (_jsize + 1) * (_ksize + 1);
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleLevelSet::_initializeCurvatureGridScalarFieldThread, this,
                                 intervals[i], intervals[i + 1], &field);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ParticleLevelSet::_initializeCurvatureGridScalarFieldThread(int startidx, int endidx, 
                                                                 ScalarField *field) {
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize + 1);
        field->setScalarFieldValue(g, -getDistanceAtNode(g));
    }
}

void ParticleLevelSet::_getValidCurvatureNodes(MeshLevelSet &surfacePhi, 
                                               Array3d<bool> &validNodes) {

    float distUpperBound = surfacePhi.getDistanceUpperBound();
    Array3d<bool> tempValid(_isize + 1, _jsize + 1, _ksize + 1, false);
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                float d = fabs(surfacePhi(i, j, k));
                tempValid.set(i, j, k, d < distUpperBound);
            }
        }
    }

    validNodes.fill(false);
    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if (!tempValid(i, j, k)) {
                    continue;
                }

                bool isValid = tempValid(i + 1, j, k) &&
                               tempValid(i - 1, j, k) &&
                               tempValid(i, j + 1, k) &&
                               tempValid(i, j - 1, k) &&
                               tempValid(i, j, k + 1) &&
                               tempValid(i, j, k - 1);
                validNodes.set(i, j, k, isValid);
            }
        }
    }
}
