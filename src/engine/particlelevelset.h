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

#ifndef FLUIDENGINE_PARTICLELEVELSET_H
#define FLUIDENGINE_PARTICLELEVELSET_H

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include "fragmentedvector.h"
#include "array3d.h"
#include "vmath.h"

class MeshLevelSet;
class ScalarField;
struct MarkerParticle;

class ParticleLevelSet {

public:
    ParticleLevelSet();
    ParticleLevelSet(int i, int j, int k, double dx);
    ~ParticleLevelSet();

    float operator()(int i, int j, int k);
    float operator()(GridIndex g);
    float get(int i, int j, int k);
    float get(GridIndex g);
    float getFaceWeightU(int i, int j, int k);
    float getFaceWeightU(GridIndex g);
    float getFaceWeightV(int i, int j, int k);
    float getFaceWeightV(GridIndex g);
    float getFaceWeightW(int i, int j, int k);
    float getFaceWeightW(GridIndex g);
    void getNodalPhi(Array3d<float> &nodalPhi);
    float trilinearInterpolate(vmath::vec3 pos);
    float getDistanceAtNode(int i, int j, int k);
    float getDistanceAtNode(GridIndex g);

    void calculateSignedDistanceField(FragmentedVector<MarkerParticle> &particles, 
                                      double radius);
    void extrapolateSignedDistanceIntoSolids(MeshLevelSet &solidPhi);
    void calculateCurvatureGrid(MeshLevelSet &surfacePhi, Array3d<float> &kgrid);

private:

    float _getMaxDistance();
    void _computeSignedDistanceFromParticles(FragmentedVector<MarkerParticle> &particles, 
                                             double radius);
    void _computeSignedDistanceFromParticlesThread(int startidx, int endidx, 
                                                   FragmentedVector<MarkerParticle> *particles, 
                                                   double radius, int splitdir);
    void _initializeCurvatureGridScalarField(ScalarField &field);
    void _initializeCurvatureGridScalarFieldThread(int startidx, int endidx, 
                                                   ScalarField *field);
    void _getValidCurvatureNodes(MeshLevelSet &surfacePhi, Array3d<bool> &validNodes);
    
    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;
    Array3d<float> _phi;

    double _curvatureGridSmoothingValue = 0.5;
    int _curvatureGridSmoothingIterations = 2;
    int _curvatureGridExactBand = 2;
    int _curvatureGridExtrapolationLayers = 5;
};

#endif
