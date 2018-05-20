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

#include "pressuresolver.h"

#include "pcgsolver/pcgsolver.h"
#include "threadutils.h"
#include "macvelocityfield.h"
#include "particlelevelset.h"
#include "meshlevelset.h"

/********************************************************************************
    PressureSolver
********************************************************************************/

PressureSolver::PressureSolver() {
}

PressureSolver::~PressureSolver() {
}

Array3d<float> PressureSolver::solve(PressureSolverParameters params, bool *success) {
    _initialize(params);
    _conditionSolidVelocityField();

    std::vector<double> rhs(_matSize, 0.0);
    _calculateNegativeDivergenceVector(rhs);

    double maxAbsCoeff = 0.0;
    for (size_t i = 0; i < rhs.size(); i++) {
        if (fabs(rhs[i]) > maxAbsCoeff) {
            maxAbsCoeff = fabs(rhs[i]);
        }
    }

    if (maxAbsCoeff < _pressureSolveTolerance) {
        return Array3d<float>(_isize, _jsize, _ksize, 0.0);
    }

    SparseMatrixd matrix(_matSize);
    _calculateMatrixCoefficients(matrix);

    PCGSolver<double> solver;
    solver.setSolverParameters(_pressureSolveTolerance, _maxCGIterations);

    double estimatedError;
    int numIterations;
    std::vector<double> soln(_matSize, 0.0);

    bool solverSuccess = solver.solve(matrix, rhs, soln, estimatedError, numIterations);

    std::ostringstream ss;
    if (solverSuccess) {
        ss << "Pressure Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        *success = true;
    } else if (numIterations == _maxCGIterations && 
                    estimatedError < _pressureSolveAcceptableTolerance) {
        ss << "Pressure Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        *success = true;
    } else {
        ss << "***Pressure Solver FAILED" <<
              "\nPressure Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        *success = false;
    }

    _solverStatus = ss.str();

    Array3d<float> pressureGrid(_isize, _jsize, _ksize, 0.0);
    for (int i = 0; i < (int)_pressureCells.size(); i++) {
        GridIndex g = _pressureCells.get(i);
        pressureGrid.set(g, soln[i]);
    }

    return pressureGrid;
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
    _liquidSDF = params.liquidSDF;
    _solidSDF = params.solidSDF;
    _weightGrid = params.weightGrid;

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
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = _pressureCells[idx];
        int i = g.i;
        int j = g.j;
        int k = g.k;

        double divergence = 0.0;
        divergence -= _weightGrid->U(i + 1, j, k) * _vField->U(i + 1, j, k);
        divergence += _weightGrid->U(i, j, k)     * _vField->U(i, j, k);
        divergence -= _weightGrid->V(i, j + 1, k) * _vField->V(i, j + 1, k);
        divergence += _weightGrid->V(i, j, k)     * _vField->V(i, j, k);
        divergence -= _weightGrid->W(i, j, k + 1) * _vField->W(i, j, k + 1);
        divergence += _weightGrid->W(i, j, k)     * _vField->W(i, j, k);

        double vol = _weightGrid->center(i, j, k);
        divergence += (_weightGrid->U(i + 1, j,     k    ) - vol) * _solidSDF->getFaceVelocityU(i + 1, j,     k    );
        divergence -= (_weightGrid->U(i,     j,     k    ) - vol) * _solidSDF->getFaceVelocityU(i,     j,     k    );
        divergence += (_weightGrid->V(i,     j + 1, k    ) - vol) * _solidSDF->getFaceVelocityV(i,     j + 1, k    );
        divergence -= (_weightGrid->V(i,     j,     k    ) - vol) * _solidSDF->getFaceVelocityV(i,     j,     k    );
        divergence += (_weightGrid->W(i,     j,     k + 1) - vol) * _solidSDF->getFaceVelocityW(i,     j,     k + 1);
        divergence -= (_weightGrid->W(i,     j,     k    ) - vol) * _solidSDF->getFaceVelocityW(i,     j,     k    );

        divergence /= _dx;

        (*rhs)[_GridToVectorIndex(i, j, k)] = divergence;
    }
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
    double scale = _deltaTime / (_dx * _dx);
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = _pressureCells[idx];
        int i = g.i;
        int j = g.j;
        int k = g.k;
        int index = _GridToVectorIndex(i, j, k);

        float diag = 0.0f;

        //right neighbour
        float term = _weightGrid->U(i + 1, j, k) * scale;
        float phiRight = _liquidSDF->get(i + 1, j, k);
        if(phiRight < 0) {
            diag += term;
            matrix->add(index, _GridToVectorIndex(i + 1, j, k), -term);
        } else {
            float theta = fmax(_liquidSDF->getFaceWeightU(i + 1, j, k), _minfrac);
            diag += term / theta;
        }

        //left neighbour
        term = _weightGrid->U(i, j, k) * scale;
        float phiLeft = _liquidSDF->get(i - 1, j, k);
        if(phiLeft < 0) {
            diag += term;
            matrix->add(index, _GridToVectorIndex(i - 1, j, k), -term);
        } else {
            float theta = fmax(_liquidSDF->getFaceWeightU(i, j, k), _minfrac);
            diag += term / theta;
        }

        //top neighbour
        term = _weightGrid->V(i, j + 1, k) * scale;
        float phiTop = _liquidSDF->get(i, j + 1, k);
        if(phiTop < 0) {
            diag += term;
            matrix->add(index, _GridToVectorIndex(i, j + 1, k), -term);
        } else {
            float theta = fmax(_liquidSDF->getFaceWeightV(i, j + 1, k), _minfrac);
            diag += term / theta;
        }

        //bottom neighbour
        term = _weightGrid->V(i, j, k) * scale;
        float phiBot = _liquidSDF->get(i, j - 1, k);
        if(phiBot < 0) {
            diag += term;
            matrix->add(index, _GridToVectorIndex(i, j - 1, k), -term);
        } else {
            float theta = fmax(_liquidSDF->getFaceWeightV(i, j, k), _minfrac);
            diag += term / theta;
        }

        //far neighbour
        term = _weightGrid->W(i, j, k + 1) * scale;
        float phiFar = _liquidSDF->get(i, j, k + 1);
        if(phiFar < 0) {
            diag += term;
            matrix->add(index, _GridToVectorIndex(i, j, k + 1), -term);
        } else {
            float theta = fmax(_liquidSDF->getFaceWeightW(i, j, k + 1), _minfrac);
            diag += term / theta;
        }

        //near neighbour
        term =_weightGrid->W(i, j, k) * scale;
        float phiNear = _liquidSDF->get(i, j, k - 1);
        if(phiNear < 0) {
            diag += term;
            matrix->add(index, _GridToVectorIndex(i, j, k - 1), -term);
        } else {
            float theta = fmax(_liquidSDF->getFaceWeightW(i, j, k), _minfrac);
            diag += term / theta;
        }

        matrix->set(index, index, diag);
    }
}