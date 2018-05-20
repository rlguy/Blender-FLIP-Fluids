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

#ifndef FLUIDENGINE_TURBULENCEFIELD_H
#define FLUIDENGINE_TURBULENCEFIELD_H

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include "vmath.h"
#include "array3d.h"

class MACVelocityField;
class GridIndexVector;
class ParticleLevelSet;

class TurbulenceField
{
public:
    TurbulenceField();
    ~TurbulenceField();

    void calculateTurbulenceField(MACVelocityField *vfield,
                                  GridIndexVector &fluidCells);
    void calculateTurbulenceField(MACVelocityField *vfield,
                                  ParticleLevelSet &liquidSDF);

    void destroyTurbulenceField();
    double evaluateTurbulenceAtPosition(vmath::vec3 p);

    float operator()(int i, int j, int k);
    float operator()(GridIndex g);

private:
    
    void _getVelocityGrid(MACVelocityField *macfield, 
                          Array3d<vmath::vec3> &vgrid);
    void _getVelocityGridThread(int startidx, int endidx, 
                                MACVelocityField *vfield, 
                                Array3d<vmath::vec3> *vgrid);
    void _calculateTurbulenceFieldThread(int startidx, int endidx,
                                         Array3d<vmath::vec3> *vgrid,
                                         GridIndexVector *fluidCells);

    Array3d<float> _field;

    int _isize, _jsize, _ksize;
    double _dx;
    double _radius;
};

#endif