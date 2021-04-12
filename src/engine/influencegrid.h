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

#ifndef FLUIDENGINE_INFLUENCEGRID_H
#define FLUIDENGINE_INFLUENCEGRID_H

#include "array3d.h"

class MeshLevelSet;

class InfluenceGrid
{
public:
    InfluenceGrid();
    InfluenceGrid(int isize, int jsize, int ksize, double dx, float baselevel);
    ~InfluenceGrid();

    void getGridDimensions(int *i, int *j, int *k);
    float getBaseLevel();
    void setBaseLevel(float level);
    float getDecayRate();
    void setDecayRate(float rate);
    Array3d<float>* getInfluenceGrid();

    void update(MeshLevelSet *solidSDF, double dt);

private:

    void _updateDecay(double dt);
    void _updateSpread(double dt);
    void _updateSpreadThread(int startidx, int endidx, double dt);
    void _updateInfluenceSources(MeshLevelSet *solidSDF);

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0;
    float _baselevel = 1.0f;
    float _decayrate = 2.0f;
    float _spreadFactor = 2.0;
    bool isSpreadEnabled = false;
    float _narrowBandWidth = 3.0;   // In # of cells

    Array3d<float> _influence;
    Array3d<float> _tempinfluence;
};

#endif