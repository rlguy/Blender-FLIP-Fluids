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


/*
    Viscosity solver adapted from Christopher Batty's viscosity3d.cpp:
        https://github.com/christopherbatty/VariationalViscosity3D/blob/master/viscosity3d.cpp

    Accurate Viscous Free Surfaces for Buckling, Coiling, and Rotating Liquids
    C. Batty and R. Bridson
    http://www.cs.ubc.ca/nest/imager/tr/2008/Batty_ViscousFluids/viscosity.pdf
*/

#include "viscositysolver.h"

#include "threadutils.h"
#include "levelsetutils.h"
#include "macvelocityfield.h"
#include "particlelevelset.h"
#include "meshlevelset.h"
#include "interpolation.h"

ViscositySolver::ViscositySolver() {
}

ViscositySolver::~ViscositySolver() {
}

bool ViscositySolver::applyViscosityToVelocityField(ViscositySolverParameters params) {
    _initialize(params);
    _computeFaceStateGrid();
    _computeVolumeGrid();
    _computeMatrixIndexTable();

    int matsize = _matrixIndex.matrixSize;
    if (matsize == 0) {
        // Nothing to solve
        return true;
    }

    SparseMatrixf matrix(matsize, 15);
    std::vector<float> rhs(matsize, 0);
    std::vector<float> soln(matsize, 0);

    _initializeLinearSystem(matrix, rhs);

    bool success = _solveLinearSystem(matrix, rhs, soln);
    if (!success) {
        return false;
    }

    _applySolutionToVelocityField(soln);

    return true;
}

std::string ViscositySolver::getSolverStatus() {
    return _solverStatus;
}

void ViscositySolver::_initialize(ViscositySolverParameters params) {
    int isize, jsize, ksize;
    params.velocityField->getGridDimensions(&isize, &jsize, &ksize);

    _isize = isize;
    _jsize = jsize;
    _ksize = ksize;
    _dx = params.cellwidth;
    _deltaTime = params.deltaTime;
    _velocityField = params.velocityField;
    _liquidSDF = params.liquidSDF;
    _solidSDF = params.solidSDF;
    _viscosity = params.viscosity;
    _solverTolerance = params.errorTolerance;
}

void ViscositySolver::_computeFaceStateGrid() {
    Array3d<float> solidCenterPhi(_isize, _jsize, _ksize);
    _computeSolidCenterPhi(solidCenterPhi);

    _state = FaceStateGrid(_isize, _jsize, _ksize);

    int U = 0; int V = 1; int W = 2;
    _computeFaceStateGridMT(solidCenterPhi, U);
    _computeFaceStateGridMT(solidCenterPhi, V);
    _computeFaceStateGridMT(solidCenterPhi, W);
}

void ViscositySolver::_computeFaceStateGridMT(Array3d<float> &solidCenterPhi, int dir) {
    int U = 0; int V = 1; int W = 2;

    int gridsize = 0;
    if (dir == U) {
        gridsize = _state.U.width * _state.U.height * _state.U.depth;
    } else if (dir == V) {
        gridsize = _state.V.width * _state.V.height * _state.V.depth;
    } else if (dir == W) {
        gridsize = _state.W.width * _state.W.height * _state.W.depth;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ViscositySolver::_computeFaceStateGridThread, this,
                                 intervals[i], intervals[i + 1], &solidCenterPhi, dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ViscositySolver::_computeFaceStateGridThread(int startidx, int endidx, 
                                                  Array3d<float> *solidCenterPhi, int dir) {
    int U = 0; int V = 1; int W = 2;

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            bool isEdge = g.i == 0 || g.i == _state.U.width - 1;;
            if (isEdge || solidCenterPhi->get(g.i - 1, g.j, g.k) + solidCenterPhi->get(g.i, g.j, g.k) <= 0) {
                _state.U.set(g, FaceState::solid);
            } else { 
                _state.U.set(g, FaceState::fluid);
            }
        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            bool isEdge = g.j == 0 || g.j == _state.V.height - 1;
            if (isEdge || solidCenterPhi->get(g.i, g.j - 1, g.k) + solidCenterPhi->get(g.i, g.j, g.k) <= 0) {
                _state.V.set(g, FaceState::solid);
            } else { 
                _state.V.set(g, FaceState::fluid);
            }
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            bool isEdge = g.k == 0 || g.k == _state.W.depth - 1;
            if (isEdge || solidCenterPhi->get(g.i, g.j, g.k - 1) + solidCenterPhi->get(g.i, g.j, g.k) <= 0) {
                _state.W.set(g, FaceState::solid);
            } else { 
                _state.W.set(g, FaceState::fluid); 
            }
        }

    }
}

void ViscositySolver::_computeSolidCenterPhi(Array3d<float> &solidCenterPhi) {
    int gridsize = solidCenterPhi.width * solidCenterPhi.height * solidCenterPhi.depth;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ViscositySolver::_computeSolidCenterPhiThread, this,
                                 intervals[i], intervals[i + 1], &solidCenterPhi);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ViscositySolver::_computeSolidCenterPhiThread(int startidx, int endidx, 
                                                   Array3d<float> *solidCenterPhi) {
    int isize = solidCenterPhi->width;
    int jsize = solidCenterPhi->height;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        solidCenterPhi->set(g, _solidSDF->getDistanceAtCellCenter(g));
    }
}

void ViscositySolver::_computeVolumeGrid() {
    Array3d<bool> validCells(_isize + 1, _jsize + 1, _ksize + 1, false);
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (_liquidSDF->get(i, j, k) < 0) {
                    validCells.set(i, j, k, true);
                }
            }
        }
    }

    int layers = 2;
    for (int layer = 0; layer < layers; layer++) {
        GridIndex nbs[6];
        Array3d<bool> tempValid = validCells;
        for (int k = 0; k < _ksize + 1; k++) {
            for (int j = 0; j < _jsize + 1; j++) {
                for (int i = 0; i < _isize + 1; i++) {
                    if (validCells(i, j, k)) {
                        Grid3d::getNeighbourGridIndices6(i, j, k, nbs);
                        for (int nidx = 0; nidx < 6; nidx++) {
                            if (tempValid.isIndexInRange(nbs[nidx])) {
                                tempValid.set(nbs[nidx], true);
                            }
                        }
                    }
                }
            }
        }
        validCells = tempValid;
    }

    if (_volumes.isize != _isize || _volumes.jsize != _jsize || _volumes.ksize != _ksize) {
        _volumes = ViscosityVolumeGrid(_isize, _jsize, _ksize);
        _subcellVolumeGrid = Array3d<float>(2 * _isize, 2 * _jsize, 2 * _ksize, 0.0f);
    } else {
        _volumes.clear();
        _subcellVolumeGrid.fill(0.0f);
    }

    vmath::vec3 centerStart(0.25f * _dx, 0.25f * _dx, 0.25f * _dx);
    _estimateVolumeFractions(&_subcellVolumeGrid, &validCells, centerStart, 0.5f * _dx);

    struct WorkGroup {
        Array3d<float> *grid;
        GridIndex gridOffset;
        WorkGroup(Array3d<float> *gridptr, GridIndex gridoffset) : 
                    grid(gridptr), gridOffset(gridoffset) {}
    };

    std::vector<WorkGroup> workqueue({
        WorkGroup(&(_volumes.center), GridIndex( 0,  0,  0)),
        WorkGroup(&(_volumes.U),      GridIndex(-1,  0,  0)),
        WorkGroup(&(_volumes.V),      GridIndex( 0, -1,  0)),
        WorkGroup(&(_volumes.W),      GridIndex( 0,  0, -1)),
        WorkGroup(&(_volumes.edgeU),  GridIndex( 0, -1, -1)),
        WorkGroup(&(_volumes.edgeV),  GridIndex(-1,  0, -1)),
        WorkGroup(&(_volumes.edgeW),  GridIndex(-1, -1,  0))
    });

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, workqueue.size());
    std::vector<std::thread> threads(numthreads);

    while (!workqueue.empty()) {
        
        numthreads = (int)fmin(numCPU, workqueue.size());
        for (int tidx = 0; tidx < numthreads; tidx++) {
            WorkGroup workgroup = workqueue.back();
            workqueue.pop_back();

            threads[tidx] = std::thread(&ViscositySolver::_computeVolumeGridThread, this,
                                        workgroup.grid, &validCells, &_subcellVolumeGrid, 
                                        workgroup.gridOffset);
        }

        for (int tidx = 0; tidx < numthreads; tidx++) {
            threads[tidx].join();
        }
    }
}

void ViscositySolver::_estimateVolumeFractions(Array3d<float> *volumes, 
                                               Array3d<bool> *validCells, 
                                               vmath::vec3 centerStart, 
                                               float dx) {

    int gridsize = volumes->width * volumes->height * volumes->depth;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ViscositySolver::_estimateVolumeFractionsThread, this,
                                 intervals[i], intervals[i + 1], 
                                 volumes, validCells, centerStart, dx);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

}

void ViscositySolver::_estimateVolumeFractionsThread(int startidx, int endidx,
                                                     Array3d<float> *volumes, 
                                                     Array3d<bool> *validCells, 
                                                     vmath::vec3 centerStart, 
                                                     float dx) {

    int isize = volumes->width;
    int jsize = volumes->height;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        int i = g.i;
        int j = g.j;
        int k = g.k;

        if (!validCells->get(i / 2, j / 2, k / 2)) {
            continue;
        }

        vmath::vec3 center = centerStart + vmath::vec3(i * dx, j * dx, k * dx);
        float hdx = 0.5f * dx;

        float phi000 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(-hdx, -hdx, -hdx));
        float phi001 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(-hdx, -hdx, +hdx));
        float phi010 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(-hdx, +hdx, -hdx));
        float phi011 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(-hdx, +hdx, +hdx));
        float phi100 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(+hdx, -hdx, -hdx));
        float phi101 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(+hdx, -hdx, +hdx));
        float phi110 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(+hdx, +hdx, -hdx));
        float phi111 = _liquidSDF->trilinearInterpolate(center + vmath::vec3(+hdx, +hdx, +hdx));

        volumes->set(i, j, k, LevelsetUtils::volumeFraction(
                phi000, phi100, phi010, phi110, phi001, phi101, phi011, phi111
        ));
    }
}

void ViscositySolver::_computeVolumeGridThread(Array3d<float> *volumes, 
                                  Array3d<bool> *validCells,
                                  Array3d<float> *subcellVolumes,
                                  GridIndex gridOffset) {

    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if (!validCells->get(i, j, k)) {
                    continue;
                }

                int base_i = 2 * i + gridOffset.i;
                int base_j = 2 * j + gridOffset.j;
                int base_k = 2 * k + gridOffset.k;
                for (int k_off = 0; k_off < 2; k_off++) {
                    for (int j_off = 0; j_off < 2; j_off++) {
                        for (int i_off = 0; i_off < 2; i_off++) {
                            volumes->add(i, j, k, subcellVolumes->get(base_i + i_off, base_j + j_off, base_k + k_off));
                        }
                    }
                }
                volumes->set(i, j, k, 0.125f * volumes->get(i, j, k));

            }
        }
    }
}

void ViscositySolver::_destroyVolumeGrid() {
    _volumes.destroy();
}

void ViscositySolver::_computeMatrixIndexTable() {

    int dim = (_isize + 1) * _jsize * _ksize + 
              _isize * (_jsize + 1) * _ksize + 
              _isize * _jsize * (_ksize + 1);
    FaceIndexer fidx(_isize, _jsize, _ksize);

    std::vector<bool> isIndexInMatrix(dim, false);
    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if (_state.U(i, j, k) != FaceState::fluid) {
                    continue;
                }

                float v = _volumes.U(i, j, k);
                float vRight = _volumes.center(i, j, k);
                float vLeft = _volumes.center(i - 1, j, k);
                float vTop = _volumes.edgeW(i, j + 1, k);
                float vBottom = _volumes.edgeW(i, j, k);
                float vFront = _volumes.edgeV(i, j, k + 1);
                float vBack = _volumes.edgeV(i, j, k);

                if (v > 0.0 || vRight > 0.0 || vLeft > 0.0 || vTop > 0.0 || 
                        vBottom > 0.0 || vFront > 0.0 || vBack > 0.0) {
                    int index = fidx.U(i, j, k);
                    isIndexInMatrix[index] = true;
                }
            }
        }
    }

    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if (_state.V(i, j, k) != FaceState::fluid) {
                    continue;
                }

                float v = _volumes.V(i, j, k);
                float vRight = _volumes.edgeW(i + 1, j, k);
                float vLeft = _volumes.edgeW(i, j, k);
                float vTop = _volumes.center(i, j, k);
                float vBottom = _volumes.center(i, j - 1, k);
                float vFront = _volumes.edgeU(i, j, k + 1);
                float vBack = _volumes.edgeU(i, j, k);

                if (v > 0.0 || vRight > 0.0 || vLeft > 0.0 || vTop > 0.0 || 
                        vBottom > 0.0 || vFront > 0.0 || vBack > 0.0) {
                    int index = fidx.V(i, j, k);
                    isIndexInMatrix[index] = true;
                }
            }
        }
    }

    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if (_state.W(i, j, k) != FaceState::fluid) {
                    continue;
                }

                float v = _volumes.W(i, j, k);
                float vRight = _volumes.edgeV(i + 1, j, k);
                float vLeft = _volumes.edgeV(i, j, k);
                float vTop = _volumes.edgeU(i, j + 1, k);
                float vBottom = _volumes.edgeU(i, j, k);
                float vFront = _volumes.center(i, j, k);
                float vBack = _volumes.center(i, j, k - 1);

                if (v > 0.0 || vRight > 0.0 || vLeft > 0.0 || vTop > 0.0 || 
                        vBottom > 0.0 || vFront > 0.0 || vBack > 0.0) {
                    int index = fidx.W(i, j, k);
                    isIndexInMatrix[index] = true;
                }
            }
        }
    }

    std::vector<int> gridToMatrixIndex(dim, -1);
    int matrixindex = 0;
    for (size_t i = 0; i < isIndexInMatrix.size(); i++) {
        if (isIndexInMatrix[i]) {
            gridToMatrixIndex[i] = matrixindex;
            matrixindex++;
        }
    }

    _matrixIndex = MatrixIndexer(_isize, _jsize, _ksize, gridToMatrixIndex);
}

void ViscositySolver::_initializeLinearSystem(SparseMatrixf &matrix, std::vector<float> &rhs) {
    _initializeLinearSystemU(matrix, rhs);
    _initializeLinearSystemV(matrix, rhs);
    _initializeLinearSystemW(matrix, rhs);
}

void ViscositySolver::_initializeLinearSystemU(SparseMatrixf &matrix, std::vector<float> &rhs) {
    std::vector<GridIndex> indices;
    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if(_state.U(i, j, k) == FaceState::fluid && _matrixIndex.U(i, j, k) != -1) {
                    indices.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, indices.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, indices.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ViscositySolver::_initializeLinearSystemThreadU, this,
                                 intervals[i], intervals[i + 1], &indices, &matrix, &rhs);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ViscositySolver::_initializeLinearSystemV(SparseMatrixf &matrix, std::vector<float> &rhs) {
    std::vector<GridIndex> indices;
    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if(_state.V(i, j, k) == FaceState::fluid && _matrixIndex.V(i, j, k) != -1) {
                    indices.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, indices.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, indices.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ViscositySolver::_initializeLinearSystemThreadV, this,
                                 intervals[i], intervals[i + 1], &indices, &matrix, &rhs);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ViscositySolver::_initializeLinearSystemW(SparseMatrixf &matrix, std::vector<float> &rhs) {
    std::vector<GridIndex> indices;
    for (int k = 1; k < _ksize; k++) {
        for (int j = 1; j < _jsize; j++) {
            for (int i = 1; i < _isize; i++) {
                if(_state.W(i, j, k) == FaceState::fluid && _matrixIndex.W(i, j, k) != -1) {
                    indices.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, indices.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, indices.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ViscositySolver::_initializeLinearSystemThreadW, this,
                                 intervals[i], intervals[i + 1], &indices, &matrix, &rhs);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ViscositySolver::_initializeLinearSystemThreadU(int startidx, int endidx, 
                                                     std::vector<GridIndex> *indices,
                                                     SparseMatrixf *matrix, 
                                                     std::vector<float> *rhs) {
    MatrixIndexer &mj = _matrixIndex;
    FaceState FLUID = FaceState::fluid;
    FaceState SOLID = FaceState::solid;

    float invdx = 1.0f / _dx;
    float factor = _deltaTime * invdx * invdx;
    for (int idx = startidx; idx < endidx; idx++) {
        int i = indices->at(idx).i;
        int j = indices->at(idx).j;
        int k = indices->at(idx).k;
        int row = _matrixIndex.U(i, j, k);

        float viscRight = _viscosity->get(i, j, k);
        float viscLeft = _viscosity->get(i - 1, j, k);

        float viscTop    = 0.25f * (_viscosity->get(i - 1, j + 1, k) + 
                                    _viscosity->get(i - 1, j,     k) + 
                                    _viscosity->get(i,     j + 1, k) + 
                                    _viscosity->get(i,     j,     k));
        float viscBottom = 0.25f * (_viscosity->get(i - 1, j,     k) + 
                                    _viscosity->get(i - 1, j - 1, k) + 
                                    _viscosity->get(i,     j,     k) + 
                                    _viscosity->get(i,     j - 1, k));

        float viscFront = 0.25f * (_viscosity->get(i - 1, j, k + 1) + 
                                   _viscosity->get(i - 1, j, k    ) + 
                                   _viscosity->get(i,     j, k + 1) + 
                                   _viscosity->get(i,     j, k    ));
        float viscBack  = 0.25f * (_viscosity->get(i - 1, j, k    ) + 
                                   _viscosity->get(i - 1, j, k - 1) + 
                                   _viscosity->get(i,     j, k    ) + 
                                   _viscosity->get(i,     j, k - 1));

        float volRight = _volumes.center(i, j, k);
        float volLeft = _volumes.center(i-1, j, k);
        float volTop = _volumes.edgeW(i, j + 1, k);
        float volBottom = _volumes.edgeW(i, j, k);
        float volFront = _volumes.edgeV(i, j, k + 1);
        float volBack = _volumes.edgeV(i, j, k);

        float factorRight  = 2 * factor * viscRight * volRight;
        float factorLeft   = 2 * factor * viscLeft * volLeft;
        float factorTop    = factor * viscTop * volTop;
        float factorBottom = factor * viscBottom * volBottom;
        float factorFront  = factor * viscFront * volFront;
        float factorBack   = factor * viscBack * volBack;

        float diag = _volumes.U(i, j, k) + factorRight + factorLeft + factorTop + factorBottom + factorFront + factorBack;
        matrix->set(row, row, diag);
        if (_state.U(i + 1, j,     k    ) == FLUID) { matrix->add(row, mj.U(i + 1, j,     k    ), -factorRight ); }
        if (_state.U(i - 1, j,     k    ) == FLUID) { matrix->add(row, mj.U(i - 1, j,     k    ), -factorLeft  ); }
        if (_state.U(i,     j + 1, k    ) == FLUID) { matrix->add(row, mj.U(i,     j + 1, k    ), -factorTop   ); }
        if (_state.U(i,     j - 1, k    ) == FLUID) { matrix->add(row, mj.U(i,     j - 1, k    ), -factorBottom); }
        if (_state.U(i,     j,     k + 1) == FLUID) { matrix->add(row, mj.U(i,     j,     k + 1), -factorFront ); }
        if (_state.U(i,     j,     k - 1) == FLUID) { matrix->add(row, mj.U(i,     j,     k - 1), -factorBack  ); }

        if (_state.V(i,     j + 1, k    ) == FLUID) { matrix->add(row, mj.V(i,     j + 1, k    ), -factorTop   ); }
        if (_state.V(i - 1, j + 1, k    ) == FLUID) { matrix->add(row, mj.V(i - 1, j + 1, k    ),  factorTop   ); }
        if (_state.V(i,     j,     k    ) == FLUID) { matrix->add(row, mj.V(i,     j,     k    ),  factorBottom); }
        if (_state.V(i - 1, j,     k    ) == FLUID) { matrix->add(row, mj.V(i - 1, j,     k    ), -factorBottom); }
        
        if (_state.W(i,     j,     k + 1) == FLUID) { matrix->add(row, mj.W(i,     j,     k + 1), -factorFront ); }
        if (_state.W(i - 1, j,     k + 1) == FLUID) { matrix->add(row, mj.W(i - 1, j,     k + 1),  factorFront ); }
        if (_state.W(i,     j,     k    ) == FLUID) { matrix->add(row, mj.W(i,     j,     k    ),  factorBack  ); }
        if (_state.W(i - 1, j,     k    ) == FLUID) { matrix->add(row, mj.W(i - 1, j,     k    ), -factorBack  ); }

        float rval = _volumes.U(i, j, k) * _velocityField->U(i, j, k);
        if (_state.U(i + 1, j,     k)     == SOLID) { rval -= -factorRight  * _velocityField->U(i + 1, j,     k    ); }
        if (_state.U(i - 1, j,     k)     == SOLID) { rval -= -factorLeft   * _velocityField->U(i - 1, j,     k    ); }
        if (_state.U(i,     j + 1, k)     == SOLID) { rval -= -factorTop    * _velocityField->U(i,     j + 1, k    ); }
        if (_state.U(i,     j - 1, k)     == SOLID) { rval -= -factorBottom * _velocityField->U(i,     j - 1, k    ); }
        if (_state.U(i,     j,     k + 1) == SOLID) { rval -= -factorFront  * _velocityField->U(i,     j,     k + 1); }
        if (_state.U(i,     j,     k - 1) == SOLID) { rval -= -factorBack   * _velocityField->U(i,     j,     k - 1); }

        if (_state.V(i,     j + 1, k)     == SOLID) { rval -= -factorTop    * _velocityField->V(i,     j + 1, k    ); }
        if (_state.V(i - 1, j + 1, k)     == SOLID) { rval -=  factorTop    * _velocityField->V(i - 1, j + 1, k    ); }
        if (_state.V(i,     j,     k)     == SOLID) { rval -=  factorBottom * _velocityField->V(i,     j,     k    ); }
        if (_state.V(i - 1, j,     k)     == SOLID) { rval -= -factorBottom * _velocityField->V(i - 1, j,     k    ); }

        if (_state.W(i,     j,     k + 1) == SOLID) { rval -= -factorFront  * _velocityField->W(i,     j,     k + 1); } 
        if (_state.W(i - 1, j,     k + 1) == SOLID) { rval -=  factorFront  * _velocityField->W(i - 1, j,     k + 1); } 
        if (_state.W(i,     j,     k)     == SOLID) { rval -=  factorBack   * _velocityField->W(i,     j,     k    ); } 
        if (_state.W(i - 1, j,     k)     == SOLID) { rval -= -factorBack   * _velocityField->W(i - 1, j,     k    ); } 
        (*rhs)[row] = rval;
    }
}

void ViscositySolver::_initializeLinearSystemThreadV(int startidx, int endidx, 
                                                     std::vector<GridIndex> *indices,
                                                     SparseMatrixf *matrix, 
                                                     std::vector<float> *rhs) {
    MatrixIndexer &mj = _matrixIndex;
    FaceState FLUID = FaceState::fluid;
    FaceState SOLID = FaceState::solid;

    float invdx = 1.0f / _dx;
    float factor = _deltaTime * invdx * invdx;
    for (int idx = startidx; idx < endidx; idx++) {
        int i = indices->at(idx).i;
        int j = indices->at(idx).j;
        int k = indices->at(idx).k;
        int row = _matrixIndex.V(i, j, k);  

        float viscRight = 0.25f * (_viscosity->get(i,     j - 1, k) + 
                                   _viscosity->get(i + 1, j - 1, k) + 
                                   _viscosity->get(i,     j,     k) + 
                                   _viscosity->get(i + 1, j,     k));
        float viscLeft  = 0.25f * (_viscosity->get(i,     j - 1, k) + 
                                   _viscosity->get(i - 1, j - 1, k) + 
                                   _viscosity->get(i,     j,     k) + 
                                   _viscosity->get(i - 1, j,     k));
        
        float viscTop = _viscosity->get(i, j, k);
        float viscBottom = _viscosity->get(i, j - 1, k);
        
        float viscFront = 0.25f * (_viscosity->get(i, j - 1, k    ) + 
                                   _viscosity->get(i, j - 1, k + 1) + 
                                   _viscosity->get(i, j,     k    ) + 
                                   _viscosity->get(i, j,     k + 1));
        float viscBack  = 0.25f * (_viscosity->get(i, j - 1, k    ) + 
                                   _viscosity->get(i, j - 1, k - 1) + 
                                   _viscosity->get(i, j,     k    ) + 
                                   _viscosity->get(i, j,     k - 1));

        float volRight = _volumes.edgeW(i + 1, j, k);
        float volLeft = _volumes.edgeW(i, j, k);
        float volTop = _volumes.center(i, j, k);
        float volBottom = _volumes.center(i, j - 1, k);
        float volFront = _volumes.edgeU(i, j, k + 1);
        float volBack = _volumes.edgeU(i, j, k);

        float factorRight  = factor * viscRight * volRight;
        float factorLeft   = factor * viscLeft * volLeft;
        float factorTop    = 2 * factor * viscTop * volTop;
        float factorBottom = 2 * factor * viscBottom * volBottom;
        float factorFront  = factor * viscFront * volFront;
        float factorBack   = factor * viscBack*volBack;

        float diag = _volumes.V(i, j, k) + factorRight + factorLeft + factorTop + factorBottom + factorFront + factorBack;
        matrix->set(row, row, diag);
        if (_state.V(i + 1, j,     k    ) == FLUID) { matrix->add(row, mj.V(i + 1, j,     k    ), -factorRight ); }
        if (_state.V(i - 1, j,     k    ) == FLUID) { matrix->add(row, mj.V(i - 1, j,     k    ), -factorLeft  ); }
        if (_state.V(i,     j + 1, k    ) == FLUID) { matrix->add(row, mj.V(i,     j + 1, k    ), -factorTop   ); }
        if (_state.V(i,     j - 1, k    ) == FLUID) { matrix->add(row, mj.V(i,     j - 1, k    ), -factorBottom); }
        if (_state.V(i,     j,     k + 1) == FLUID) { matrix->add(row, mj.V(i,     j,     k + 1), -factorFront ); }
        if (_state.V(i,     j,     k - 1) == FLUID) { matrix->add(row, mj.V(i,     j,     k - 1), -factorBack  ); }

        if (_state.U(i + 1, j,     k    ) == FLUID) { matrix->add(row, mj.U(i + 1, j,     k    ), -factorRight ); }
        if (_state.U(i + 1, j - 1, k    ) == FLUID) { matrix->add(row, mj.U(i + 1, j - 1, k    ),  factorRight ); }
        if (_state.U(i,     j,     k    ) == FLUID) { matrix->add(row, mj.U(i,     j,     k    ),  factorLeft  ); }
        if (_state.U(i,     j - 1, k    ) == FLUID) { matrix->add(row, mj.U(i,     j - 1, k    ), -factorLeft  ); }
    
        if (_state.W(i,     j,     k + 1) == FLUID) { matrix->add(row, mj.W(i,     j,     k + 1), -factorFront ); }
        if (_state.W(i,     j - 1, k + 1) == FLUID) { matrix->add(row, mj.W(i,     j - 1, k + 1),  factorFront ); }
        if (_state.W(i,     j,     k    ) == FLUID) { matrix->add(row, mj.W(i,     j,     k    ),  factorBack  ); }
        if (_state.W(i,     j - 1, k    ) == FLUID) { matrix->add(row, mj.W(i,     j - 1, k    ), -factorBack  ); }

        float rval = _volumes.V(i, j, k) * _velocityField->V(i, j, k);
        if (_state.V(i + 1, j,     k)     == SOLID) { rval -= -factorRight  * _velocityField->V(i + 1, j,     k    ); }
        if (_state.V(i - 1, j,     k)     == SOLID) { rval -= -factorLeft   * _velocityField->V(i - 1, j,     k    ); }
        if (_state.V(i,     j + 1, k)     == SOLID) { rval -= -factorTop    * _velocityField->V(i,     j + 1, k    ); }
        if (_state.V(i ,    j - 1, k)     == SOLID) { rval -= -factorBottom * _velocityField->V(i,     j - 1, k    ); }
        if (_state.V(i    , j,     k + 1) == SOLID) { rval -= -factorFront  * _velocityField->V(i,     j,     k + 1); }
        if (_state.V(i,     j,     k - 1) == SOLID) { rval -= -factorBack   * _velocityField->V(i,     j,     k - 1); }

        if (_state.U(i + 1, j,     k)     == SOLID) { rval -= -factorRight  * _velocityField->U(i + 1, j,     k    ); }
        if (_state.U(i + 1, j - 1, k)     == SOLID) { rval -=  factorRight  * _velocityField->U(i + 1, j - 1, k    ); }
        if (_state.U(i,     j,     k)     == SOLID) { rval -=  factorLeft   * _velocityField->U(i,     j,     k    ); }
        if (_state.U(i,     j - 1, k)     == SOLID) { rval -= -factorLeft   * _velocityField->U(i,     j - 1, k    ); }

        if (_state.W(i,     j,     k + 1) == SOLID) { rval -= -factorFront  * _velocityField->W(i,     j,     k + 1); }
        if (_state.W(i,     j - 1, k + 1) == SOLID) { rval -=  factorFront  * _velocityField->W(i,     j - 1, k + 1); }
        if (_state.W(i,     j,     k)     == SOLID) { rval -=  factorBack   * _velocityField->W(i,     j,     k    ); }
        if (_state.W(i,     j - 1, k)     == SOLID) { rval -= -factorBack   * _velocityField->W(i,     j - 1, k    ); }
        (*rhs)[row] = rval;
    }
}

void ViscositySolver::_initializeLinearSystemThreadW(int startidx, int endidx, 
                                                     std::vector<GridIndex> *indices,
                                                     SparseMatrixf *matrix, 
                                                     std::vector<float> *rhs) {
    MatrixIndexer &mj = _matrixIndex;
    FaceState FLUID = FaceState::fluid;
    FaceState SOLID = FaceState::solid;

    float invdx = 1.0f / _dx;
    float factor = _deltaTime * invdx * invdx;
    for (int idx = startidx; idx < endidx; idx++) {
        int i = indices->at(idx).i;
        int j = indices->at(idx).j;
        int k = indices->at(idx).k;
        int row = _matrixIndex.W(i, j, k);

        float viscRight = 0.25f * (_viscosity->get(i,     j, k    ) + 
                                   _viscosity->get(i,     j, k - 1) + 
                                   _viscosity->get(i + 1, j, k    ) + 
                                   _viscosity->get(i + 1, j, k - 1));
        float viscLeft  = 0.25f * (_viscosity->get(i,     j, k    ) + 
                                   _viscosity->get(i,     j, k - 1) + 
                                   _viscosity->get(i - 1, j, k    ) + 
                                   _viscosity->get(i - 1, j, k - 1));

        float viscTop    = 0.25f * (_viscosity->get(i, j,     k    ) + 
                                    _viscosity->get(i, j,     k - 1) + 
                                    _viscosity->get(i, j + 1, k    ) + 
                                    _viscosity->get(i, j + 1, k - 1));
        float viscBottom = 0.25f * (_viscosity->get(i, j,     k    ) + 
                                    _viscosity->get(i, j,     k - 1) + 
                                    _viscosity->get(i, j - 1, k    ) + 
                                    _viscosity->get(i, j - 1, k - 1));

        float viscFront = _viscosity->get(i, j, k);   
        float viscBack = _viscosity->get(i, j, k - 1); 

        float volRight = _volumes.edgeV(i + 1, j, k);
        float volLeft = _volumes.edgeV(i, j, k);
        float volTop = _volumes.edgeU(i, j + 1, k);
        float volBottom = _volumes.edgeU(i, j, k);
        float volFront = _volumes.center(i, j, k);
        float volBack = _volumes.center(i, j, k - 1);

        float factorRight  = factor * viscRight * volRight;
        float factorLeft   = factor * viscLeft * volLeft;
        float factorTop    = factor * viscTop * volTop;
        float factorBottom = factor * viscBottom * volBottom;
        float factorFront  = 2 * factor * viscFront * volFront;
        float factorBack   = 2 * factor * viscBack*volBack;

        float diag = _volumes.W(i, j, k) + factorRight + factorLeft + factorTop + factorBottom + factorFront + factorBack;
        matrix->set(row, row, diag);
        if (_state.W(i + 1, j,     k    ) == FLUID) { matrix->add(row, mj.W(i + 1, j,     k    ), -factorRight ); }
        if (_state.W(i - 1, j,     k    ) == FLUID) { matrix->add(row, mj.W(i - 1, j,     k    ), -factorLeft  ); }
        if (_state.W(i,     j + 1, k    ) == FLUID) { matrix->add(row, mj.W(i,     j + 1, k    ), -factorTop   ); }
        if (_state.W(i,     j - 1, k    ) == FLUID) { matrix->add(row, mj.W(i,     j - 1, k    ), -factorBottom); }
        if (_state.W(i,     j,     k + 1) == FLUID) { matrix->add(row, mj.W(i,     j,     k + 1), -factorFront ); }
        if (_state.W(i,     j,     k - 1) == FLUID) { matrix->add(row, mj.W(i,     j,     k - 1), -factorBack  ); }

        if (_state.U(i + 1, j,     k    ) == FLUID) { matrix->add(row, mj.U(i + 1, j,     k    ), -factorRight ); } 
        if (_state.U(i + 1, j,     k - 1) == FLUID) { matrix->add(row, mj.U(i + 1, j,     k - 1),  factorRight ); }
        if (_state.U(i,     j,     k    ) == FLUID) { matrix->add(row, mj.U(i,     j,     k    ),  factorLeft  ); }
        if (_state.U(i,     j,     k - 1) == FLUID) { matrix->add(row, mj.U(i,     j,     k - 1), -factorLeft  ); }
        
        if (_state.V(i,     j + 1, k    ) == FLUID) { matrix->add(row, mj.V(i,     j + 1, k    ), -factorTop   ); }
        if (_state.V(i,     j + 1, k - 1) == FLUID) { matrix->add(row, mj.V(i,     j + 1, k - 1),  factorTop   ); }
        if (_state.V(i,     j,     k    ) == FLUID) { matrix->add(row, mj.V(i,     j,     k    ),  factorBottom); }
        if (_state.V(i,     j,     k - 1) == FLUID) { matrix->add(row, mj.V(i,     j,     k - 1), -factorBottom); }

        float rval = _volumes.W(i, j, k) * _velocityField->W(i, j, k);
        if (_state.W(i + 1, j,     k)     == SOLID) { rval -= -factorRight  * _velocityField->W(i + 1, j,     k    ); }
        if (_state.W(i - 1, j,     k)     == SOLID) { rval -= -factorLeft   * _velocityField->W(i - 1, j,     k    ); }
        if (_state.W(i,     j + 1, k)     == SOLID) { rval -= -factorTop    * _velocityField->W(i,     j + 1, k    ); }
        if (_state.W(i,     j - 1, k)     == SOLID) { rval -= -factorBottom * _velocityField->W(i,     j - 1, k    ); }
        if (_state.W(i,     j,     k + 1) == SOLID) { rval -= -factorFront  * _velocityField->W(i,     j,     k + 1); }
        if (_state.W(i,     j,     k - 1) == SOLID) { rval -= -factorBack   * _velocityField->W(i,     j,     k - 1); }

        if (_state.U(i + 1, j,     k)     == SOLID) { rval -= -factorRight  * _velocityField->U(i + 1, j,     k    ); }
        if (_state.U(i + 1, j,     k - 1) == SOLID) { rval -=  factorRight  * _velocityField->U(i + 1, j,     k - 1); }
        if (_state.U(i,     j,     k)     == SOLID) { rval -=  factorLeft   * _velocityField->U(i,     j,     k    ); }
        if (_state.U(i,     j,     k - 1) == SOLID) { rval -= -factorLeft   * _velocityField->U(i,     j,     k - 1); }

        if (_state.V(i,     j + 1, k)     == SOLID) { rval -= -factorTop    * _velocityField->V(i,     j + 1, k    ); }
        if (_state.V(i,     j + 1, k - 1) == SOLID) { rval -=  factorTop    * _velocityField->V(i,     j + 1, k - 1); }
        if (_state.V(i,     j,     k)     == SOLID) { rval -=  factorBottom * _velocityField->V(i,     j,     k    ); }
        if (_state.V(i,     j,     k - 1) == SOLID) { rval -= -factorBottom * _velocityField->V(i,     j,     k - 1); }
        (*rhs)[row] = rval;
    }
}

bool ViscositySolver::_solveLinearSystem(SparseMatrixf &matrix, std::vector<float> &rhs, 
                                         std::vector<float> &soln) {

    PCGSolver<float> solver;
    solver.setSolverParameters(_solverTolerance, _maxSolverIterations);

    float estimatedError;
    int numIterations;
    bool success = solver.solve(matrix, rhs, soln, estimatedError, numIterations);

    bool retval;
    std::ostringstream ss;
    if (success) {
        ss << "Viscosity Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        retval = true;
    } else if (numIterations == _maxSolverIterations && estimatedError < _acceptableTolerace) {
        ss << "Viscosity Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        retval = true;
    } else {
        std::ostringstream ss;
        ss << "***Viscosity Solver FAILED" <<
              "\nViscosity Solver Iterations: " << numIterations <<
              "\nEstimated Error: " << estimatedError;
        retval = false;
    }

    _solverStatus = ss.str();

    return retval;
}

void ViscositySolver::_applySolutionToVelocityField(std::vector<float> &soln) {
    _velocityField->clear();
    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize + 1; i++) {
                int matidx = _matrixIndex.U(i, j, k);
                if (matidx != -1) {
                    _velocityField->setU(i, j, k, soln[matidx]);
                }
            }
        }
    }

    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize + 1; j++) {
            for(int i = 0; i < _isize; i++) {
                int matidx = _matrixIndex.V(i, j, k);
                if (matidx != -1) {
                    _velocityField->setV(i, j, k, soln[matidx]);
                }
            }
        }
    }

    for(int k = 0; k < _ksize + 1; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize; i++) {
                int matidx = _matrixIndex.W(i, j, k);
                if (matidx != -1) {
                    _velocityField->setW(i, j, k, soln[matidx]);
                }
            }
        }
    }

}
