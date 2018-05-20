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

/*
    This pressure solver is based on:

    A Fast Variational Framework for Accurate Solid-Fluid Coupling
     - Christopher Batty, Florence Bertails, Robert Bridson
    https://hal.archives-ouvertes.fr/file/index/docid/384725/filename/variationalFluids.pdf

    Source Code: https://github.com/christopherbatty/Fluid3D
*/
#ifndef FLUIDENGINE_PRESSURESOLVER_H
#define FLUIDENGINE_PRESSURESOLVER_H

#include "pcgsolver/sparsematrix.h"
#include "gridindexkeymap.h"
#include "gridindexvector.h"

class MACVelocityField;
class ParticleLevelSet;
class MeshLevelSet;

struct WeightGrid {
    Array3d<float> center;
    Array3d<float> U;
    Array3d<float> V;
    Array3d<float> W;

    WeightGrid() {}
    WeightGrid(int i, int j, int k) :
        center(i, j, k, 0.0f),
        U(i + 1, j, k, 0.0f),
        V(i, j + 1, k, 0.0f),
        W(i, j, k + 1, 0.0f) {}
};


struct PressureSolverParameters {
    double cellwidth;
    double deltaTime;
    double tolerance;
    double acceptableTolerance;
    int maxIterations;
    
    MACVelocityField *velocityField;
    ParticleLevelSet *liquidSDF;
    MeshLevelSet *solidSDF;
    WeightGrid *weightGrid;
};

/********************************************************************************
    PressureSolver
********************************************************************************/

class PressureSolver
{
public:
    PressureSolver();
    ~PressureSolver();

    Array3d<float> solve(PressureSolverParameters params, bool *success);
    std::string getSolverStatus();

private:

    inline int _GridToVectorIndex(GridIndex g) {
        return _keymap.find(g);
    }
    inline int _GridToVectorIndex(int i, int j, int k) {
        return _keymap.find(i, j, k);
    }
    inline GridIndex _VectorToGridIndex(int i) {
        return _pressureCells.at(i);
    }
    inline int _isPressureCell(GridIndex g) {
        return _keymap.find(g) != -1;
    }
    inline int _isPressureCell(int i, int j, int k) {
        return _keymap.find(i, j, k) != -1;
    }

    void _initialize(PressureSolverParameters params);
    void _initializeGridIndexKeyMap();
    void _conditionSolidVelocityField();
    void _computeBordersAirGridThread(int startidx, int endidx, 
                                      Array3d<bool> *bordersAir);
    void _calculateNegativeDivergenceVector(std::vector<double> &rhs);
    void _calculateNegativeDivergenceVectorThread(int startidx, 
                                                  int endidx, std::vector<double> *rhs);
    void _calculateMatrixCoefficients(SparseMatrixd &matrix);
    void _calculateMatrixCoefficientsThread(int startidx, int endidx,
                                            SparseMatrixd *matrix);

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0;
    double _deltaTime = 0;
    int _matSize = 0;

    double _pressureSolveTolerance = 1e-9;
    double _pressureSolveAcceptableTolerance = 1.0;
    int _maxCGIterations = 200;
    double _minfrac = 0.01f;

    GridIndexVector _pressureCells;

    MACVelocityField *_vField;
    ParticleLevelSet *_liquidSDF;
    MeshLevelSet *_solidSDF;
    WeightGrid *_weightGrid;

    GridIndexKeyMap _keymap;

    std::string _solverStatus;
};

#endif
