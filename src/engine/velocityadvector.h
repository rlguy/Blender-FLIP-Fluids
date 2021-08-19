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
Part of this levelset implementation was adapted from Christopher Batty's 
signed distance field generator: https://github.com/christopherbatty/SDFGen

The MIT License (MIT)

Copyright (c) 2015, Christopher Batty

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to 
deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO 
EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE 
USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#ifndef FLUIDENGINE_VELOCITYADVECTOR_H
#define FLUIDENGINE_VELOCITYADVECTOR_H

#include "fragmentedvector.h"
#include "markerparticle.h"
#include "array3d.h"
#include "blockarray3d.h"
#include "boundedbuffer.h"
#include "macvelocityfield.h"
#include "particlesystem.h"


enum class VelocityAdvectorTransferMethod : char { 
    FLIP = 0x00, 
    APIC = 0x01
};

struct VelocityAdvectorParameters {
    ParticleSystem *particles;
    MACVelocityField *vfield;
    ValidVelocityComponentGrid *validVelocities;
    double particleRadius = 1.0;
    VelocityAdvectorTransferMethod velocityTransferMethod = VelocityAdvectorTransferMethod::FLIP;
};


class VelocityAdvector {

public:
    VelocityAdvector();
    ~VelocityAdvector();

    void advect(VelocityAdvectorParameters params);
    
private:
    enum class Direction { U, V, W };

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

    struct ScalarData {
        float scalar = 0.0f;
        float weight = 0.0f;
    };

    struct PointData {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float v = 0.0f;

        PointData() {}
        PointData(float px, float py, float pz, float vel)
                    : x(px), y(py), z(pz), v(vel) {}
    };

    struct AffineData {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;

        AffineData() {}
        AffineData(float vx, float vy, float vz)
                    : x(vx), y(vy), z(vz) {}
        AffineData(vmath::vec3 v)
                    : x(v.x), y(v.y), z(v.z) {}
    };

    struct ComputeBlock {
        GridBlock<ScalarData> gridBlock;
        PointData *particleData = nullptr;
        AffineData *affineData = nullptr;
        int numParticles = 0;
        float radius = 0.0f;
    };

    void _initializeParameters(VelocityAdvectorParameters params);
    void _advectGrid(Direction dir);
    vmath::vec3 _getDirectionOffset(Direction dir);
    void _initializeBlockGrid(BlockArray3d<ScalarData> &blockphi, Direction dir);
    void _initializeActiveBlocksThread(int startidx, int endidx,
                                       Array3d<bool> *activeBlocks,
                                       Direction dir);
    void _computeGridCountData(BlockArray3d<ScalarData> &blockphi, 
                               ParticleGridCountData &countdata,
                               Direction dir);
    void _initializeGridCountData(BlockArray3d<ScalarData> &blockphi, 
                                  ParticleGridCountData &countdata);
    void _computeGridCountDataThread(int startidx, int endidx, 
                                     BlockArray3d<ScalarData> *blockphi, 
                                     GridCountData *countdata,
                                     Direction dir);
    void _sortParticlesIntoBlocks(ParticleGridCountData &countdata, 
                                  std::vector<PointData> &sortedParticleData, 
                                  std::vector<AffineData> &sortedAffineData, 
                                  std::vector<int> &blockToParticleIndex,
                                  Direction dir);

    void _advectionFLIPProducerThread(BoundedBuffer<ComputeBlock> *blockQueue, 
                                  BoundedBuffer<ComputeBlock> *finishedBlockQueue);
    void _advectionAPICProducerThread(BoundedBuffer<ComputeBlock> *blockQueue, 
                                      BoundedBuffer<ComputeBlock> *finishedBlockQueue);

    inline bool _isFLIP() { return _velocityTransferMethod == VelocityAdvectorTransferMethod::FLIP; }
    inline bool _isAPIC() { return _velocityTransferMethod == VelocityAdvectorTransferMethod::APIC; }

    // Parameters
    ParticleSystem *_particles;
    MACVelocityField *_vfield;
    ValidVelocityComponentGrid *_validVelocities;
    std::vector<vmath::vec3> _points;
    std::vector<vmath::vec3> _velocities;
    VelocityAdvectorTransferMethod _velocityTransferMethod = VelocityAdvectorTransferMethod::FLIP;

    // APIC Data
    std::vector<vmath::vec3> _affineX;
    std::vector<vmath::vec3> _affineY;
    std::vector<vmath::vec3> _affineZ;

    double _dx = 0.0;
    double _chunkdx = 0.0;
    double _particleRadius = 0.0;

    int _chunkWidth = 10;
    int _numBlocksPerJob = 10;
    
};

#endif
