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

#include "influencegrid.h"

#include "meshlevelset.h"
#include "meshobject.h"
#include "threadutils.h"
#include "grid3d.h"
#include "fluidsimassert.h"


InfluenceGrid::InfluenceGrid() {
}

InfluenceGrid::InfluenceGrid(int isize, int jsize, int ksize, double dx, float baselevel) :
                                _isize(isize), _jsize(jsize), _ksize(ksize), _dx(dx),
                                _baselevel(baselevel),
                                _influence(isize, jsize, ksize, baselevel) {
}

InfluenceGrid::~InfluenceGrid() {
}

void InfluenceGrid::getGridDimensions(int *i, int *j, int *k) { 
    *i = _isize; *j = _jsize; *k = _ksize; 
}

float InfluenceGrid::getBaseLevel() {
    return _baselevel;
}

void InfluenceGrid::setBaseLevel(float level) {
    _baselevel = level;
}

float InfluenceGrid::getDecayRate() {
    return _decayrate;
}

void InfluenceGrid::setDecayRate(float rate) {
    _decayrate = rate;
}

Array3d<float>* InfluenceGrid::getInfluenceGrid() {
    return &_influence;
}

void InfluenceGrid::update(MeshLevelSet *solidSDF, double dt) {
    int si, sj, sk;
    solidSDF->getGridDimensions(&si, &sj, &sk);
    FLUIDSIM_ASSERT(_isize == si + 1 && _jsize == sj + 1 && _ksize == sk + 1);

    _updateDecay(dt);
    if (isSpreadEnabled) {
        _updateSpread(dt);
    }
    _updateInfluenceSources(solidSDF);
}

void InfluenceGrid::_updateDecay(double dt) {
    for (int k = 0; k < _influence.depth; k++) {
        for (int j = 0; j < _influence.height; j++) {
            for (int i = 0; i < _influence.width; i++) {
                float value = _influence(i, j, k);
                if (value < _baselevel) {
                    value = std::min(value + _decayrate * (float)dt, _baselevel);
                } else if (value > _baselevel) {
                    value = std::max(value - _decayrate * (float)dt, _baselevel);
                }
                _influence.set(i, j, k, value);
            }
        }
    }   
}

void InfluenceGrid::_updateSpread(double dt) {
    bool isInfluenceUniform = true;
    float constvalue = _influence(0, 0, 0);
    float eps = 1e-5;
    for (int k = 0; k < _influence.depth; k++) {
        for (int j = 0; j < _influence.height; j++) {
            for (int i = 0; i < _influence.width; i++) {
                if (std::abs(_influence(i, j, k) - constvalue) > eps) {
                    isInfluenceUniform = false;
                    goto endLoop;
                }
            }
        }
    }
    endLoop:

    if (isInfluenceUniform) {
        return;
    }

    if (_tempinfluence.width != _influence.width || 
            _tempinfluence.height != _influence.height || 
            _tempinfluence.depth != _influence.depth) {
        _tempinfluence = Array3d<float>(_influence.width, _influence.height, _influence.depth);
    }

    int gridsize = _isize * _jsize * _ksize;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&InfluenceGrid::_updateSpreadThread, this,
                                 intervals[i], intervals[i + 1], dt);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    for (int k = 0; k < _influence.depth; k++) {
        for (int j = 0; j < _influence.height; j++) {
            for (int i = 0; i < _influence.width; i++) {
                _influence.set(i, j, k, _tempinfluence(i, j, k));
            }
        }
    }   
}

void InfluenceGrid::_updateSpreadThread(int startidx, int endidx, double dt) {
    GridIndex nbs[6];
    float rate = _spreadFactor * _decayrate * dt;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
        Grid3d::getNeighbourGridIndices6(g, nbs);
        float currentvalue = _influence(g);
        float sum = 0.0f;
        int n = 0;
        for (int nidx = 0; nidx < 6; nidx++) {
            if (_influence.isIndexInRange(nbs[nidx])) {
                sum += rate * (_influence(nbs[nidx]) - currentvalue);
                n++;
            }
        }
        _tempinfluence.set(g, currentvalue + (sum / (float)n));
    }
}

void InfluenceGrid::_updateInfluenceSources(MeshLevelSet *solidSDF) {
    float width = _narrowBandWidth * _dx;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (std::abs(solidSDF->get(i, j, k)) > width) {
                    continue;
                }

                MeshObject *m = solidSDF->getClosestMeshObject(i, j, k);
                if (m != nullptr) {
                    _influence.set(i, j, k, m->getWhitewaterInfluence());
                }
            }
        }
    }   
}