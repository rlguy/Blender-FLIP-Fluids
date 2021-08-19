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

#ifndef FLUIDENGINE_PARTICLEMASKGRID_H
#define FLUIDENGINE_PARTICLEMASKGRID_H

#include "array3d.h"
#include "vmath.h"

class ParticleMaskGrid
{
public:
    ParticleMaskGrid();
    ParticleMaskGrid(int i, int j, int k, double dx);
    ~ParticleMaskGrid();

    void clear();
    unsigned char operator()(int i, int j, int k);
    unsigned char operator()(GridIndex g);
    void addParticle(vmath::vec3 p);
    void addParticles(std::vector<vmath::vec3> &particles);
    bool isSubCellSet(int i, int j, int k);
    bool isSubCellSet(GridIndex g);
    bool isSubCellSet(vmath::vec3 p);

private:

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;
    double _subdx = 0.0;

    Array3d<unsigned char> _maskGrid;

};

#endif
