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

#include "pressuresolver.h"

#include "pcgsolver/pcgsolver.h"
#include "threadutils.h"
#include "macvelocityfield.h"
#include "particlelevelset.h"
#include "meshlevelset.h"
#include "interpolation.h"

/********************************************************************************
    PressureSolver
********************************************************************************/

PressureSolver::PressureSolver() {
}

PressureSolver::~PressureSolver() {
}

bool PressureSolver::solve(PressureSolverParameters params) {
    _initialize(params);
    _conditionSolidVelocityField();
    _initializeSurfaceTensionClusterData();

    std::vector<double> rhs(_matSize, 0);
    _calculateNegativeDivergenceVector(rhs);

    double maxAbsCoeff = 0.0;
    for (size_t i = 0; i < rhs.size(); i++) {
        if (fabs(rhs[i]) > maxAbsCoeff) {
            maxAbsCoeff = fabs(rhs[i]);
        }
    }

    if (maxAbsCoeff < _pressureSolveTolerance) {
        _solverStatus = "Pressure Solver Iterations: 0\nEstimated Error: 0.0";
        return true;
    }

    std::vector<double> soln(_matSize, 0);
    SparseMatrixd matrix(_matSize, 7);
    _calculateMatrixCoefficients(matrix);

    bool success = _solveLinearSystem(matrix, rhs, soln);

    if (!success) {
        return false;
    }

    _applySolutionToVelocityField(soln);

    return true;
}

std::string PressureSolver::getSolverStatus() {
    return _solverStatus;
}

void PressureSolver::_initialize(PressureSolverParameters params) {
    params.velocityField->getGridDimensions(&_isize, &_jsize, &_ksize);
    _dx = params.cellwidth;
    _deltaTime = params.deltaTime;
    _pressureSolveTolerance = params.tolerance;
    _pressureSolveAcceptableTolerance = params.acceptableTolerance;
    _maxCGIterations = params.maxIterations;

    _vField = params.velocityField;
    _validVelocities = params.validVelocities;
    _liquidSDF = params.liquidSDF;
    _solidSDF = params.solidSDF;
    _weightGrid = params.weightGrid;

    _isSurfaceTensionEnabled = params.isSurfaceTensionEnabled;
    _surfaceTensionConstant = params.surfaceTensionConstant;
    _curvatureGrid = params.curvatureGrid;

    _pressureCells = GridIndexVector(_isize, _jsize, _ksize);
    for(int k = 1; k < _ksize - 1; k++) {
        for(int j = 1; j < _jsize - 1; j++) {
            for(int i = 1; i < _isize - 1; i++) {
                if(_liquidSDF->get(i, j, k) < 0) {
                    _pressureCells.push_back(i, j, k);
                }
            }
        }
    }

    _matSize = (int)_pressureCells.size();

    _initializeGridIndexKeyMap();
}

void PressureSolver::_initializeGridIndexKeyMap() {
    _keymap = GridIndexKeyMap(_isize, _jsize, _ksize);
    for (unsigned int idx = 0; idx < _pressureCells.size(); idx++) {
        _keymap.insert(_pressureCells[idx], idx);
    }
}

void PressureSolver::_conditionSolidVelocityField() {
    // This method detects isolated pockets of fluid surrounded by solids and 
    // sets the surrounding solid velocities to 0 in order to remove 
    // inconsistencies from the linear system.

    int gridsize = _isize * _jsize * _ksize;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);

    Array3d<bool> bordersAir(_isize, _jsize, _ksize, false);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_computeBordersAirGridThread, this,
                                 intervals[i], intervals[i + 1], &bordersAir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    std::vector<GridIndex> group;
    Array3d<bool> isProcessed(_isize, _jsize, _ksize, false);
    std::vector<GridIndex> queue;
    float eps = 1e-6;
    for (int k = 1; k < _ksize - 1; k++) {
        for (int j = 1; j < _jsize - 1; j++) {
            for (int i = 1; i < _isize - 1; i++) {

                if (_liquidSDF->get(i, j, k) >= 0.0f) {
                    isProcessed.set(i, j, k, true);
                    continue;
                }

                if (isProcessed(i, j, k)) {
                    continue;
                }

                GridIndex seed(i, j, k);
                queue.push_back(seed);
                isProcessed.set(seed, true);
                
                group.clear();
                while (!queue.empty()) {
                    GridIndex g = queue.back();
                    queue.pop_back();

                    if (!isProcessed(g.i - 1, g.j, g.k) && 
                            _liquidSDF->get(g.i - 1, g.j, g.k) < 0.0f && 
                            _weightGrid->U(g.i, g.j, g.k) >= 0.0f + eps) {
                        queue.push_back(GridIndex(g.i - 1, g.j, g.k));
                        isProcessed.set(g.i - 1, g.j, g.k, true);
                    }

                    if (!isProcessed(g.i + 1, g.j, g.k) && 
                            _liquidSDF->get(g.i + 1, g.j, g.k) < 0.0f && 
                            _weightGrid->U(g.i + 1, g.j, g.k) >= 0.0f + eps) {
                        queue.push_back(GridIndex(g.i + 1, g.j, g.k));
                        isProcessed.set(g.i + 1, g.j, g.k, true);
                    }

                    if (!isProcessed(g.i, g.j - 1, g.k) && 
                            _liquidSDF->get(g.i, g.j - 1, g.k) < 0.0f && 
                            _weightGrid->V(g.i, g.j, g.k) >= 0.0f + eps) {
                        queue.push_back(GridIndex(g.i, g.j - 1, g.k));
                        isProcessed.set(g.i, g.j - 1, g.k, true);
                    }

                    if (!isProcessed(g.i, g.j + 1, g.k) && 
                            _liquidSDF->get(g.i, g.j + 1, g.k) < 0.0f && 
                            _weightGrid->V(g.i, g.j + 1, g.k) >= 0.0f + eps) {
                        queue.push_back(GridIndex(g.i, g.j + 1, g.k));
                        isProcessed.set(g.i, g.j + 1, g.k, true);
                    }

                    if (!isProcessed(g.i, g.j, g.k - 1) && 
                            _liquidSDF->get(g.i, g.j, g.k - 1) < 0.0f && 
                            _weightGrid->W(g.i, g.j, g.k) >= 0.0f + eps) {
                        queue.push_back(GridIndex(g.i, g.j, g.k - 1));
                        isProcessed.set(g.i, g.j, g.k - 1, true);
                    }

                    if (!isProcessed(g.i, g.j, g.k + 1) && 
                            _liquidSDF->get(g.i, g.j, g.k + 1) < 0.0f && 
                            _weightGrid->W(g.i, g.j, g.k + 1) >= 0.0f + eps) {
                        queue.push_back(GridIndex(g.i, g.j, g.k + 1));
                        isProcessed.set(g.i, g.j, g.k + 1, true);
                    }

                    group.push_back(g);
                }

                if (group.size() == 1) {
                    continue;
                }

                bool isIsolated = true;
                for (size_t gidx = 0; gidx < group.size(); gidx++) {
                    if (bordersAir(group[gidx])) {
                        isIsolated = false;
                        break;
                    }
                }

                if (isIsolated) {
                    for (size_t gidx = 0; gidx < group.size(); gidx++) {
                        GridIndex g = group[gidx];
                        _solidSDF->setFaceVelocityU(g.i,     g.j,     g.k,     0.0f);
                        _solidSDF->setFaceVelocityU(g.i + 1, g.j,     g.k,     0.0f);
                        _solidSDF->setFaceVelocityV(g.i,     g.j,     g.k,     0.0f);
                        _solidSDF->setFaceVelocityV(g.i,     g.j + 1, g.k,     0.0f);
                        _solidSDF->setFaceVelocityW(g.i,     g.j,     g.k,     0.0f);
                        _solidSDF->setFaceVelocityW(g.i,     g.j,     g.k + 1, 0.0f);
                    }
                }

            }
        }
    }

}

void PressureSolver::_computeBordersAirGridThread(int startidx, int endidx, 
                                                  Array3d<bool> *bordersAir) {
    float eps = 1e-6;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
        if (Grid3d::isGridIndexOnBorder(g, _isize, _jsize, _ksize)) {
            continue;
        }

        int i = g.i;
        int j = g.j;
        int k = g.k;
        if ((_weightGrid->U(i,     j,     k    ) >= 0.0f + eps && _liquidSDF->get(i - 1, j,     k    ) >= 0.0f) || 
            (_weightGrid->U(i + 1, j,     k    ) >= 0.0f + eps && _liquidSDF->get(i + 1, j,     k    ) >= 0.0f) || 
            (_weightGrid->V(i,     j,     k    ) >= 0.0f + eps && _liquidSDF->get(i,     j - 1, k    ) >= 0.0f) || 
            (_weightGrid->V(i,     j + 1, k    ) >= 0.0f + eps && _liquidSDF->get(i,     j + 1, k    ) >= 0.0f) || 
            (_weightGrid->W(i,     j,     k    ) >= 0.0f + eps && _liquidSDF->get(i,     j,     k - 1) >= 0.0f) || 
            (_weightGrid->W(i,     j,     k + 1) >= 0.0f + eps && _liquidSDF->get(i,     j,     k + 1) >= 0.0f)) {

            bordersAir->set(i, j, k, true);
        }
    }
}

void PressureSolver::_initializeSurfaceTensionClusterData() {
    if (!_isSurfaceTensionEnabled) {
        return;
    }

    int bisize = _isize / _blockwidth;
    int bjsize = _jsize / _blockwidth;
    int bksize = _ksize / _blockwidth;

    /*
    char HAS_INSIDE =  0x01;
    char HAS_OUTSIDE = 0x02;
    */
    Array3d<char> blockstatus(bisize, bjsize, bksize, 0x00);

    int gridsize = bisize * bjsize * bksize;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_initializeBlockStatusGridThread, this,
                                 intervals[i], intervals[i + 1], &blockstatus);
    }
    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    /*
    char UNSET       = 0x00;
    char OK_INSIDE   = 0x01;
    char OK_OUTSIDE  = 0x02;
    char BAD_INSIDE  = 0x04;
    char BAD_OUTSIDE = 0x08;
    char BORDER      = 0x10;
    */
    _surfaceTensionClusterStatus = Array3d<char>(_isize, _jsize, _ksize, 0x00);

    gridsize = _isize * _jsize * _ksize;
    numthreads = (int)fmin(numCPU, gridsize);
    threads = std::vector<std::thread>(numthreads);
    intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_initializeCellStatusGridThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &blockstatus, &_surfaceTensionClusterStatus);
    }
    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    gridsize = _isize * _jsize * _ksize;
    numthreads = (int)fmin(numCPU, gridsize);
    threads = std::vector<std::thread>(numthreads);
    intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    std::vector<std::vector<GridIndex> > threadResults(numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_findSurfaceCellsThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &_surfaceTensionClusterStatus, &(threadResults[i]));
    }

    int cellcount = 0;
    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
        cellcount += threadResults[i].size();
    }

    std::vector<GridIndex> surfaceCells;
    surfaceCells.reserve(cellcount);
    for (size_t i = 0; i < threadResults.size(); i++) {
        surfaceCells.insert(surfaceCells.end(), threadResults[i].begin(), threadResults[i].end());
    }

    numthreads = (int)fmin(numCPU, surfaceCells.size());
    threads = std::vector<std::thread>(numthreads);
    intervals = ThreadUtils::splitRangeIntoIntervals(0, surfaceCells.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_calculateSurfaceCellStatusThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &surfaceCells, &_surfaceTensionClusterStatus);
    }
    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void PressureSolver::_initializeBlockStatusGridThread(int startidx, int endidx,
                                                      Array3d<char> *blockstatus) {
    char HAS_INSIDE = 0x01;
    char HAS_OUTSIDE =  0x02;

    GridIndex startg = Grid3d::getUnflattenedIndex(startidx, blockstatus->width, blockstatus->height);
    GridIndex endg = Grid3d::getUnflattenedIndex(endidx - 1, blockstatus->width, blockstatus->height);
    startg.i *= _blockwidth;
    startg.j *= _blockwidth;
    startg.k *= _blockwidth;
    endg.i = endg.i * _blockwidth + 3;
    endg.j = endg.j * _blockwidth + 3;
    endg.k = endg.k * _blockwidth + 3;

    int cellstartidx = Grid3d::getFlatIndex(startg, _isize, _jsize);
    int cellendidx = Grid3d::getFlatIndex(endg, _isize, _jsize);

    for (int idx = cellstartidx; idx <= cellendidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
        int bi = g.i / _blockwidth;
        int bj = g.j / _blockwidth;
        int bk = g.k / _blockwidth;
        if (!blockstatus->isIndexInRange(bi, bj, bk)) {
            continue;
        }

        int flatidx = Grid3d::getFlatIndex(bi, bj, bk, blockstatus->width, blockstatus->height);
        if (flatidx < startidx || flatidx >= endidx) {
            continue;
        }

        char bstatus = blockstatus->get(bi, bj, bk);
        char cstatus = _liquidSDF->get(g) < 0 ? HAS_INSIDE : HAS_OUTSIDE;
        if (!(bstatus & cstatus)) {
            blockstatus->set(bi, bj, bk, bstatus | cstatus);
        }
    }
}

void PressureSolver::_initializeCellStatusGridThread(int startidx, int endidx,
                                                     Array3d<char> *blockstatus, 
                                                     Array3d<char> *cellstatus) {
    char HAS_INSIDE =  0x01;
    char HAS_OUTSIDE = 0x02;

    char OK_INSIDE   = 0x01;
    char OK_OUTSIDE  = 0x02;
    char BORDER      = 0x10;

    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
        if (Grid3d::isGridIndexOnBorder(g, _isize, _jsize, _ksize)) {
            cellstatus->set(g, BORDER);
            continue;
        }

        int bi = g.i / _blockwidth;
        int bj = g.j / _blockwidth;
        int bk = g.k / _blockwidth;
        if (!blockstatus->isIndexInRange(bi, bj, bk)) {
            continue;
        }

        char bstatus = blockstatus->get(bi, bj, bk);
        if ((bstatus & HAS_INSIDE) && !(bstatus & HAS_OUTSIDE)) {
            cellstatus->set(g, OK_INSIDE);
        } else if (!(bstatus & HAS_INSIDE) && (bstatus & HAS_OUTSIDE)) {
            cellstatus->set(g, OK_OUTSIDE);
        }
    }
}

void PressureSolver::_findSurfaceCellsThread(int startidx, int endidx,
                                             Array3d<char> *cellstatus,
                                             std::vector<GridIndex> *cells) {
    char UNSET       = 0x00;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
        if (Grid3d::isGridIndexOnBorder(g, _isize, _jsize, _ksize) || cellstatus->get(g) != UNSET) {
            continue;
        }

        bool isfluid = _liquidSDF->get(g) < 0.0f;
        GridIndex n(g.i + 1, g.j, g.k);
        float nd = _liquidSDF->get(n);
        if ((isfluid ? nd >= 0.0f : nd < 0.0f)) {
            cells->push_back(g);
            continue;
        }

        n = GridIndex(g.i - 1, g.j, g.k);
        nd = _liquidSDF->get(n);
        if ((isfluid ? nd >= 0.0f : nd < 0.0f)) {
            cells->push_back(g);
            continue;
        }

        n = GridIndex(g.i, g.j + 1, g.k);
        nd = _liquidSDF->get(n);
        if ((isfluid ? nd >= 0.0f : nd < 0.0f)) {
            cells->push_back(g);
            continue;
        }

        n = GridIndex(g.i, g.j - 1, g.k);
        nd = _liquidSDF->get(n);
        if ((isfluid ? nd >= 0.0f : nd < 0.0f)) {
            cells->push_back(g);
            continue;
        }

        n = GridIndex(g.i, g.j, g.k + 1);
        nd = _liquidSDF->get(n);
        if ((isfluid ? nd >= 0.0f : nd < 0.0f)) {
            cells->push_back(g);
            continue;
        }

        n = GridIndex(g.i, g.j, g.k - 1);
        nd = _liquidSDF->get(n);
        if ((isfluid ? nd >= 0.0f : nd < 0.0f)) {
            cells->push_back(g);
            continue;
        }
    }
}

void PressureSolver::_calculateSurfaceCellStatusThread(int startidx, int endidx,
                                                       std::vector<GridIndex> *cells,
                                                       Array3d<char> *cellstatus) {
    char UNSET       = 0x00;
    char OK_INSIDE   = 0x01;
    char OK_OUTSIDE  = 0x02;
    char BAD_INSIDE  = 0x04;
    char BAD_OUTSIDE = 0x08;
    char BORDER      = 0x10;

    Array3d<bool> isProcessed(_isize, _jsize, _ksize, false);

    GridIndex neighbours[6];
    std::vector<GridIndex> queue;
    size_t fifoidx = 0;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex seed = cells->at(idx);
        if (cellstatus->get(seed) != UNSET) {
            continue;
        }

        queue.clear();
        queue.push_back(seed);
        fifoidx = 0;
        isProcessed.set(seed, true);
        bool isfluid = _liquidSDF->get(seed) < 0.0f;
        char result = UNSET;
        bool breaksearch = false;

        while (fifoidx < queue.size()) {
            GridIndex g = queue[fifoidx];
            fifoidx++;

            neighbours[0] = GridIndex(g.i + 1, g.j, g.k); neighbours[1] = GridIndex(g.i - 1, g.j, g.k);
            neighbours[2] = GridIndex(g.i, g.j + 1, g.k); neighbours[3] = GridIndex(g.i, g.j - 1, g.k);
            neighbours[4] = GridIndex(g.i, g.j, g.k + 1); neighbours[5] = GridIndex(g.i, g.j, g.k - 1);
            for (int nidx = 0; nidx < 6; nidx++) {
                GridIndex n = neighbours[nidx];
                if (isProcessed(n)) {
                    continue;
                }

                if (!(isfluid ? _liquidSDF->get(n) < 0.0f : _liquidSDF->get(n) >= 0.0f)) {
                    continue;
                }

                char nstatus = cellstatus->get(n);
                if (nstatus == BORDER) {
                    continue;
                }

                if (nstatus != UNSET) {
                    result = nstatus;
                    breaksearch = true;
                    break;
                }

                queue.push_back(n);
                isProcessed.set(n, true);
                if ((int)queue.size() == _surfaceTensionClusterThreshold) {
                    result = isfluid ? OK_INSIDE : OK_OUTSIDE;
                }
            }

            if (breaksearch) {
                break;
            }
        }

        if (result == UNSET && (int)queue.size() < _surfaceTensionClusterThreshold) {
            result = isfluid ? BAD_INSIDE : BAD_OUTSIDE;
        }

        for (size_t qidx = 0; qidx < queue.size(); qidx++) {
            cellstatus->set(queue[qidx], result);
            isProcessed.set(queue[qidx], false);
        }
    }
}

void PressureSolver::_calculateNegativeDivergenceVector(std::vector<double> &rhs) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _pressureCells.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _pressureCells.size(), 
                                                                      numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_calculateNegativeDivergenceVectorThread, this,
                                 intervals[i], intervals[i + 1], &rhs);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void PressureSolver::_calculateNegativeDivergenceVectorThread(int startidx, 
                                                              int endidx, std::vector<double> *rhs) {
    double factor = 1.0 / _dx;
    double stfactor = _deltaTime / (_dx * _dx);
    double eps = 1e-9;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = _pressureCells[idx];
        int i = g.i;
        int j = g.j;
        int k = g.k;
        int index = _GridToVectorIndex(i, j, k);

        double volCenter = _weightGrid->center(i, j, k);
        double volRight =  _weightGrid->U(i + 1, j,     k    );
        double volLeft =   _weightGrid->U(i,     j,     k    );
        double volTop =    _weightGrid->V(i,     j + 1, k    );
        double volBottom = _weightGrid->V(i,     j,     k    );
        double volFront =  _weightGrid->W(i,     j,     k + 1);
        double volBack =   _weightGrid->W(i,     j,     k    );

        double divergence = 0.0;
        divergence += -factor * volRight  * _vField->U(i + 1, j,     k    );
        divergence +=  factor * volLeft   * _vField->U(i,     j,     k    );
        divergence += -factor * volTop    * _vField->V(i,     j + 1, k    );
        divergence +=  factor * volBottom * _vField->V(i,     j,     k    );
        divergence += -factor * volFront  * _vField->W(i,     j,     k + 1);
        divergence +=  factor * volBack   * _vField->W(i,     j,     k    );

        divergence +=  factor * (volRight -  volCenter) * _solidSDF->getFaceVelocityU(i + 1, j,     k    );
        divergence += -factor * (volLeft -   volCenter) * _solidSDF->getFaceVelocityU(i,     j,     k    );
        divergence +=  factor * (volTop -    volCenter) * _solidSDF->getFaceVelocityV(i,     j + 1, k    );
        divergence += -factor * (volBottom - volCenter) * _solidSDF->getFaceVelocityV(i,     j,     k    );
        divergence +=  factor * (volFront -  volCenter) * _solidSDF->getFaceVelocityW(i,     j,     k + 1);
        divergence += -factor * (volBack -   volCenter) * _solidSDF->getFaceVelocityW(i,     j,     k    );

        if (_isSurfaceTensionEnabled) {
            double phiCenter = _liquidSDF->get(i,     j,     k    );
            double phiRight =  _liquidSDF->get(i + 1, j,     k    );
            double phiLeft =   _liquidSDF->get(i - 1,     j, k    );
            double phiTop =    _liquidSDF->get(i,     j + 1, k    );
            double phiBottom = _liquidSDF->get(i,     j - 1, k    );
            double phiFront =  _liquidSDF->get(i,     j,     k + 1);
            double phiBack =   _liquidSDF->get(i,     j,     k - 1);

            if (phiRight >= 0.0) {
                double tension = _getSurfaceTensionTerm(GridIndex(i, j, k), GridIndex(i + 1, j, k));
                double theta = (phiCenter - phiRight) / (phiCenter + eps);
                theta = _clamp(theta, -_maxtheta, _maxtheta);
                divergence += stfactor * volRight * theta * tension;
            }

            if (phiLeft >= 0.0) {
                double tension = _getSurfaceTensionTerm(GridIndex(i, j, k), GridIndex(i - 1, j, k));
                double theta = (phiCenter - phiLeft) / (phiCenter + eps);
                theta = _clamp(theta, -_maxtheta, _maxtheta);
                divergence += stfactor * volLeft * theta * tension;
            }

            if (phiTop >= 0.0) {
                double tension = _getSurfaceTensionTerm(GridIndex(i, j, k), GridIndex(i, j + 1, k));
                double theta = (phiCenter - phiTop) / (phiCenter + eps);
                theta = _clamp(theta, -_maxtheta, _maxtheta);
                divergence += stfactor * volTop * theta * tension;
            }

            if (phiBottom >= 0.0) {
                double tension = _getSurfaceTensionTerm(GridIndex(i, j, k), GridIndex(i, j - 1, k));
                double theta = (phiCenter - phiBottom) / (phiCenter + eps);
                theta = _clamp(theta, -_maxtheta, _maxtheta);
                divergence += stfactor * volBottom * theta * tension;
            }

            if (phiFront >= 0.0) {
                double tension = _getSurfaceTensionTerm(GridIndex(i, j, k), GridIndex(i, j, k + 1));
                double theta = (phiCenter - phiFront) / (phiCenter + eps);
                theta = _clamp(theta, -_maxtheta, _maxtheta);
                divergence += stfactor * volFront * theta * tension;
            }

            if (phiBack >= 0.0) {
                double tension = _getSurfaceTensionTerm(GridIndex(i, j, k), GridIndex(i, j, k - 1));
                double theta = (phiCenter - phiBack) / (phiCenter + eps);
                theta = _clamp(theta, -_maxtheta, _maxtheta);
                divergence += stfactor * volBack * theta * tension;
            }
        }

        (*rhs)[index] = divergence;
    }
}

double PressureSolver::_getSurfaceTensionTerm(GridIndex g1, GridIndex g2) {
    if (!_isSurfaceTensionEnabled) {
        return 0.0;
    }

    char BAD_INSIDE  = 0x04;
    char BAD_OUTSIDE = 0x08;
    char s = _surfaceTensionClusterStatus(g1) | _surfaceTensionClusterStatus(g2);
    if ((s & BAD_INSIDE) || (s & BAD_OUTSIDE)) {
        return 0.0;
    }

    vmath::vec3 p1 = Grid3d::GridIndexToCellCenter(g1, _dx);
    vmath::vec3 p2 = Grid3d::GridIndexToCellCenter(g2, _dx);
    float phi1 = _liquidSDF->get(g1);
    float phi2 = _liquidSDF->get(g2);

    if ((phi1 < 0.0f && phi2 < 0.0f) || (phi1 >= 0.0f && phi2 >= 0.0f)) {
        return 0.0;
    }

    vmath::vec3 p;
    float eps = 1e-6;
    if (std::abs(phi2 - phi1) < eps) {
        p = p1 + 0.5f * (p2 - p1);
    } else {
        float theta = phi1 / (phi1 - phi2);
        p = p1 + theta * (p2 - p1);
    }

    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    double curvature = (double)Interpolation::trilinearInterpolate(p - hdx, _dx, *_curvatureGrid);
    
    return _surfaceTensionConstant * curvature;
}

void PressureSolver::_calculateMatrixCoefficients(SparseMatrixd &matrix) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _pressureCells.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _pressureCells.size(), 
                                                                      numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_calculateMatrixCoefficientsThread, this,
                                 intervals[i], intervals[i + 1], &matrix);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void PressureSolver::_calculateMatrixCoefficientsThread(int startidx, int endidx,
                                                        SparseMatrixd *matrix) {
    double factor = _deltaTime / (_dx * _dx);
    double eps = 1e-9;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = _pressureCells[idx];
        int i = g.i;
        int j = g.j;
        int k = g.k;
        int index = _GridToVectorIndex(i, j, k);

        double volRight =  _weightGrid->U(i + 1, j,     k    );
        double volLeft =   _weightGrid->U(i,     j,     k    );
        double volTop =    _weightGrid->V(i,     j + 1, k    );
        double volBottom = _weightGrid->V(i,     j,     k    );
        double volFront =  _weightGrid->W(i,     j,     k + 1);
        double volBack =   _weightGrid->W(i,     j,     k    );

        double phiCenter = _liquidSDF->get(i,     j,     k    );
        double phiRight =  _liquidSDF->get(i + 1, j,     k    );
        double phiLeft =   _liquidSDF->get(i - 1,     j, k    );
        double phiTop =    _liquidSDF->get(i,     j + 1, k    );
        double phiBottom = _liquidSDF->get(i,     j - 1, k    );
        double phiFront =  _liquidSDF->get(i,     j,     k + 1);
        double phiBack =   _liquidSDF->get(i,     j,     k - 1);

        double diag = (volRight + volLeft + volTop + volBottom + volFront + volBack) * factor;

        // X+ neighbour
        if (phiRight < 0.0) {
            matrix->add(index, _GridToVectorIndex(i + 1, j, k), -volRight * factor);
        } else {
            double theta = phiRight / (phiCenter + eps);
            theta = _clamp(theta, -_maxtheta, _maxtheta);
            diag -= volRight * factor * theta;
        }

        // X- neighbour
        if (phiLeft < 0.0) {
            matrix->add(index, _GridToVectorIndex(i - 1, j, k), -volLeft * factor);
        } else {
            double theta = phiLeft / (phiCenter + eps);
            theta = _clamp(theta, -_maxtheta, _maxtheta);
            diag -= volLeft * factor * theta;
        }

        // Y+ neighbour
        if (phiTop < 0.0) {
            matrix->add(index, _GridToVectorIndex(i, j + 1, k), -volTop * factor);
        } else {
            double theta = phiTop / (phiCenter + eps);
            theta = _clamp(theta, -_maxtheta, _maxtheta);
            diag -= volTop * factor * theta;
        }

        // Y- neighbour
        if (phiBottom < 0.0) {
            matrix->add(index, _GridToVectorIndex(i, j - 1, k), -volBottom * factor);
        } else {
            double theta = phiBottom / (phiCenter + eps);
            theta = _clamp(theta, -_maxtheta, _maxtheta);
            diag -= volBottom * factor * theta;
        }

        // Z+ neighbour
        if (phiFront < 0.0) {
            matrix->add(index, _GridToVectorIndex(i, j, k + 1), -volFront * factor);
        } else {
            double theta = phiFront / (phiCenter + eps);
            theta = _clamp(theta, -_maxtheta, _maxtheta);
            diag -= volFront * factor * theta;
        }

        // Z- neighbour
        if (phiBack < 0.0) {
            matrix->add(index, _GridToVectorIndex(i, j, k - 1), -volBack * factor);
        } else {
            double theta = phiBack / (phiCenter + eps);
            theta = _clamp(theta, -_maxtheta, _maxtheta);
            diag -= volBack * factor * theta;
        }

        diag = std::max(diag, 0.0);
        matrix->set(index, index, diag);
    }
}

bool PressureSolver::_solveLinearSystem(SparseMatrixd &matrix, std::vector<double> &rhs, 
                                        std::vector<double> &soln) {
    PCGSolver<double> solver;
    solver.setSolverParameters(_pressureSolveTolerance, _maxCGIterations);

    double estimatedError;
    int numIterations;
    bool success = solver.solve(matrix, rhs, soln, estimatedError, numIterations);

    bool retval;
    std::ostringstream ss;
    if (success) {
        ss << "Pressure Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        retval = true;
    } else if (numIterations == _maxCGIterations && 
                    estimatedError < _pressureSolveAcceptableTolerance) {
        ss << "Pressure Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        retval = true;
    } else {
        ss << "***Pressure Solver FAILED" <<
              "\nPressure Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        retval = false;
    }

    _solverStatus = ss.str();

    return retval;
}

void PressureSolver::_applySolutionToVelocityField(std::vector<double> &soln) {
    Array3d<float> pressureGrid(_isize, _jsize, _ksize, 0.0);
    for (int i = 0; i < (int)_pressureCells.size(); i++) {
        GridIndex g = _pressureCells.get(i);
        pressureGrid.set(g, soln[i]);
    }

    FluidMaterialGrid mgrid(_isize, _jsize, _ksize);
    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize; i++) {
                if (_liquidSDF->get(i, j, k) < 0.0) {
                    mgrid.setFluid(i, j, k);
                }
            }
        }
    }

    _validVelocities->reset();

    int U = 0; int V = 1; int W = 2;
    _applyPressureToVelocityFieldMT(pressureGrid, mgrid, U);
    _applyPressureToVelocityFieldMT(pressureGrid, mgrid, V);
    _applyPressureToVelocityFieldMT(pressureGrid, mgrid, W);
}

void PressureSolver::_applyPressureToVelocityFieldMT(Array3d<float> &pressureGrid, 
                                                      FluidMaterialGrid &mgrid,
                                                      int dir) {
    int U = 0; int V = 1; int W = 2;

    int gridsize = 0;
    if (dir == U) {
        gridsize = (_isize + 1) * _jsize * _ksize;
    } else if (dir == V) {
        gridsize = _isize * (_jsize + 1) * _ksize;
    } else if (dir == W) {
        gridsize = _isize * _jsize * (_ksize + 1);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&PressureSolver::_applyPressureToVelocityFieldThread, this,
                                 intervals[i], intervals[i + 1], &pressureGrid, &mgrid, dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void PressureSolver::_applyPressureToVelocityFieldThread(int startidx, int endidx, 
                                                          Array3d<float> *pressureGrid, 
                                                          FluidMaterialGrid *mgrid,
                                                          int dir) {
    int U = 0; int V = 1; int W = 2;
    float factor = _deltaTime / _dx;
    float eps = 1e-6;

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            if (g.i == 0 || g.i == _isize - 1) {
                continue;
            }

            int pi = g.i - 1;
            int pj = g.j;
            int pk = g.k;

            if (_weightGrid->U(g) > 0 && mgrid->isFaceBorderingFluidU(g)) {

                float p1 = 0.0f;
                float p2 = 0.0f;
                if (mgrid->isCellFluid(pi, pj, pk) && mgrid->isCellFluid(pi + 1, pj, pk)) {
                    p1 = pressureGrid->get(pi, pj, pk);
                    p2 = pressureGrid->get(pi + 1, pj, pk);
                } else {
                    float phi1 = _liquidSDF->get(pi, pj, pk);
                    float phi2 = _liquidSDF->get(pi + 1, pj, pk);
                    double tension = _getSurfaceTensionTerm(GridIndex(pi, pj, pk), GridIndex(pi + 1, pj, pk));
                    if (mgrid->isCellFluid(pi, pj, pk)) {
                        float thetaPressure = phi2 / (phi1 + eps);
                        thetaPressure = _clamp((double)thetaPressure, -_maxtheta, _maxtheta);
                        float thetaTension = (phi1 - phi2) / (phi1 + eps);
                        thetaTension = _clamp((double)thetaTension, -_maxtheta, _maxtheta);
                        p1 = pressureGrid->get(pi, pj, pk);
                        p2 = thetaTension * tension + thetaPressure * p1;
                    } else {
                        float thetaPressure = phi1 / (phi2 + eps);
                        thetaPressure = _clamp((double)thetaPressure, -_maxtheta, _maxtheta);
                        float thetaTension = (phi2 - phi1) / (phi2 + eps);
                        thetaTension = _clamp((double)thetaTension, -_maxtheta, _maxtheta);
                        p2 = pressureGrid->get(pi + 1, pj, pk);
                        p1 = thetaTension * tension + thetaPressure * p2;
                    }
                }
                _vField->addU(g, -factor * (p2 - p1));
                _validVelocities->validU.set(g, true);

            } else {
                _vField->setU(g, 0.0);
            }

        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            if (g.j == 0 || g.j == _jsize - 1) {
                continue;
            }

            int pi = g.i;
            int pj = g.j - 1;
            int pk = g.k;

            if (_weightGrid->V(g) > 0 && mgrid->isFaceBorderingFluidV(g)) {

                float p1 = 0.0f;
                float p2 = 0.0f;
                if (mgrid->isCellFluid(pi, pj, pk) && mgrid->isCellFluid(pi, pj + 1, pk)) {
                    p1 = pressureGrid->get(pi, pj, pk);
                    p2 = pressureGrid->get(pi, pj + 1, pk);
                } else {
                    float phi1 = _liquidSDF->get(pi, pj, pk);
                    float phi2 = _liquidSDF->get(pi, pj + 1, pk);
                    double tension = _getSurfaceTensionTerm(GridIndex(pi, pj, pk), GridIndex(pi, pj + 1, pk));
                    if (mgrid->isCellFluid(pi, pj, pk)) {
                        float thetaPressure = phi2 / (phi1 + eps);
                        thetaPressure = _clamp((double)thetaPressure, -_maxtheta, _maxtheta);
                        float thetaTension = (phi1 - phi2) / (phi1 + eps);
                        thetaTension = _clamp((double)thetaTension, -_maxtheta, _maxtheta);
                        p1 = pressureGrid->get(pi, pj, pk);
                        p2 = thetaTension * tension + thetaPressure * p1;
                    } else {
                        float thetaPressure = phi1 / (phi2 + eps);
                        thetaPressure = _clamp((double)thetaPressure, -_maxtheta, _maxtheta);
                        float thetaTension = (phi2 - phi1) / (phi2 + eps);
                        thetaTension = _clamp((double)thetaTension, -_maxtheta, _maxtheta);
                        p2 = pressureGrid->get(pi, pj + 1, pk);
                        p1 = thetaTension * tension + thetaPressure * p2;
                    }
                }
                _vField->addV(g, -factor * (p2 - p1));
                _validVelocities->validV.set(g, true);

            } else {
                _vField->setV(g, 0.0);
            }
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            if (g.k == 0 || g.k == _ksize - 1) {
                continue;
            }

            int pi = g.i;
            int pj = g.j;
            int pk = g.k - 1;

            if (_weightGrid->W(g) > 0 && mgrid->isFaceBorderingFluidW(g)) {

                float p1 = 0.0f;
                float p2 = 0.0f;
                if (mgrid->isCellFluid(pi, pj, pk) && mgrid->isCellFluid(pi, pj, pk + 1)) {
                    p1 = pressureGrid->get(pi, pj, pk);
                    p2 = pressureGrid->get(pi, pj, pk + 1);
                } else {
                    float phi1 = _liquidSDF->get(pi, pj, pk);
                    float phi2 = _liquidSDF->get(pi, pj, pk + 1);
                    double tension = _getSurfaceTensionTerm(GridIndex(pi, pj, pk), GridIndex(pi, pj, pk + 1));
                    if (mgrid->isCellFluid(pi, pj, pk)) {
                        float thetaPressure = phi2 / (phi1 + eps);
                        thetaPressure = _clamp((double)thetaPressure, -_maxtheta, _maxtheta);
                        float thetaTension = (phi1 - phi2) / (phi1 + eps);
                        thetaTension = _clamp((double)thetaTension, -_maxtheta, _maxtheta);
                        p1 = pressureGrid->get(pi, pj, pk);
                        p2 = thetaTension * tension + thetaPressure * p1;
                    } else {
                        float thetaPressure = phi1 / (phi2 + eps);
                        thetaPressure = _clamp((double)thetaPressure, -_maxtheta, _maxtheta);
                        float thetaTension = (phi2 - phi1) / (phi2 + eps);
                        thetaTension = _clamp((double)thetaTension, -_maxtheta, _maxtheta);
                        p2 = pressureGrid->get(pi, pj, pk + 1);
                        p1 = thetaTension * tension + thetaPressure * p2;
                    }
                }
                _vField->addW(g, -factor * (p2 - p1));
                _validVelocities->validW.set(g, true);

            } else {
                _vField->setW(g, 0.0);
            }
        }

    }
}