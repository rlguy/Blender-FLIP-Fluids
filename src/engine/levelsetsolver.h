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
Part of this levelset solver implementation was adapted from Doyub Kim's 
levelset solver methods: https://github.com/doyubkim/fluid-engine-dev

The MIT License (MIT)

Copyright (c) 2018 Doyub Kim

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in the 
Software without restriction, including without limitation the rights to use, 
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#ifndef FLUIDENGINE_LEVELSETSOLVER_H
#define FLUIDENGINE_LEVELSETSOLVER_H

#include <array>

#include "array3d.h"


class LevelSetSolver
{
public:
    LevelSetSolver();

    void reinitializeEno(Array3d<float> &inputSDF, 
                      float dx,
                      float maxDistance,
                      std::vector<GridIndex> &solverCells, 
                      Array3d<float> &outputSDF);

    void reinitializeUpwind(Array3d<float> &inputSDF, 
                      float dx,
                      float maxDistance,
                      std::vector<GridIndex> &solverCells, 
                      Array3d<float> &outputSDF);

private:

    float _maxCFL = 0.25;
    float _upwindErrorThreshold = 0.01;

    float _getPseudoTimeStep(Array3d<float> &sdf, float dx);
    float _sign(Array3d<float> &sdf, float dx, int i, int j, int k);
    int _getNumberOfIterations(float maxDistance, float dtau);

    void _stepSolverThreadEno(int startidx, int endidx, 
                           Array3d<float> *tempPtr,
                           Array3d<float> *outputPtr, 
                           float dx,
                           float dtau,
                           std::vector<GridIndex> *solverCells);
    void _getDerivativesEno(Array3d<float> *grid,
                        int i, int j, int k, float dx, 
                        std::array<float, 2> *derx,
                        std::array<float, 2> *dery,
                        std::array<float, 2> *derz);
    std::array<float, 2> _eno3(float *D0, float dx);

    void _stepSolverThreadUpwind(int startidx, int endidx, 
                             Array3d<float> *tempPtr,
                             Array3d<float> *outputPtr, 
                             float dx,
                             float dtau,
                             std::vector<GridIndex> *solverCells);
    void _getDerivativesUpwind(Array3d<float> *grid,
                               int i, int j, int k, float dx, 
                               std::array<float, 2> *derx,
                               std::array<float, 2> *dery,
                               std::array<float, 2> *derz);
    std::array<float, 2> _upwind1(float *D0, float dx);


    inline float _square(float s) { return s * s; }
};

#endif