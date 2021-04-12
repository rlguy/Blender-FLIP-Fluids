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
#include "blockarray3d.h"
#include "boundedbuffer.h"
#include "particlesystem.h"

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

    void calculateSignedDistanceField(ParticleSystem &particles, 
                                      double radius);
    void postProcessSignedDistanceField(MeshLevelSet &solidPhi);
    void calculateCurvatureGrid(Array3d<float> &surfacePhi, Array3d<float> &kgrid);

private:

    struct GridCountData {
        std::vector<int> gridCount;
        std::vector<int> simpleGridIndices;
        std::vector<int> overlappingGridIndices;
        std::vector<bool> invalidPoints;
        int startidx = 0;
        int endidx = 0;
    };

    struct ParticleGridCountData {
        int numthreads = 1;
        int gridsize = 1;
        std::vector<int> totalGridCount;
        std::vector<GridCountData> threadGridCountData;
    };

    struct ComputeBlock {
        GridBlock<float> gridBlock;
        vmath::vec3 *particleData;
        int numParticles = 0;
        float radius = 0.0f;
    };

    float _getMaxDistance();

    void _computeSignedDistanceFromParticles(std::vector<vmath::vec3> &particles, 
                                             double radius);
    void _initializeBlockGrid(std::vector<vmath::vec3> &particles,
                              BlockArray3d<float> &blockphi);
    void _initializeActiveBlocksThread(int startidx, int endidx, 
                                       std::vector<vmath::vec3> *particles,
                                       Array3d<bool> *activeBlocks);
    void _computeGridCountData(std::vector<vmath::vec3> &particles,
                               double radius,
                               BlockArray3d<float> &blockphi, 
                               ParticleGridCountData &countdata);
    void _initializeGridCountData(std::vector<vmath::vec3> &particles,
                                  BlockArray3d<float> &blockphi, 
                                  ParticleGridCountData &countdata);
    void _computeGridCountDataThread(int startidx, int endidx, 
                                     std::vector<vmath::vec3> *particles,
                                     double radius,
                                     BlockArray3d<float> *blockphi, 
                                     GridCountData *countdata);
    void _sortParticlesIntoBlocks(std::vector<vmath::vec3> &particles,
                                  ParticleGridCountData &countdata, 
                                  std::vector<vmath::vec3> &sortedParticleData, 
                                  std::vector<int> &blockToParticleDataIndex);
    void _computeExactBandProducerThread(BoundedBuffer<ComputeBlock> *computeBlockQueue,
                                         BoundedBuffer<ComputeBlock> *finishedComputeBlockQueue);

    void _initializeCurvatureGridScalarField(ScalarField &field);
    void _initializeCurvatureGridScalarFieldThread(int startidx, int endidx, 
                                                   ScalarField *field);
    void _getValidCurvatureNodes(Array3d<float> &surfacePhi, Array3d<bool> &validNodes);
    float _getCurvature(int i, int j, int k, Array3d<float> &phi);
    
    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;
    Array3d<float> _phi;

    int _curvatureGridExactBand = 3;
    int _curvatureGridExtrapolationLayers = 3;
    float _outOfRangeDistance = 5.0f;  // in # of grid cells

    int _blockwidth = 10;
    int _numComputeBlocksPerJob = 10;
    float _searchRadiusFactor = 2.0f;
};

#endif
