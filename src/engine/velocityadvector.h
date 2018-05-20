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
#include "boundedbuffer.h"
#include "macvelocityfield.h"

struct VelocityAdvectorParameters {
    FragmentedVector<MarkerParticle> *particles;
    MACVelocityField *vfield;
    ValidVelocityComponentGrid *validVelocities;
};

class VelocityAdvector {

public:
    VelocityAdvector();
    ~VelocityAdvector();

    void advect(VelocityAdvectorParameters params);
    
private:
    enum class Direction { U, V, W };

    struct CountGridData {
        Array3d<int> countGrid;
        std::vector<int> simpleGridIndices;
        std::vector<int> overlappingGridIndices;
        int startidx = 0;
        int endidx = 0;

        CountGridData() {}
        CountGridData(int isize, int jsize, int ksize) : 
                        countGrid(isize, jsize, ksize, 0) {}
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

    struct BlockData {
        int blockID;
        GridIndex blockIndex;
        PointData *pointData;
        int numPoints;
        float *velocityData;
        float *weightData;
    };

    void _initializeParameters(VelocityAdvectorParameters params);
    void _advectGrid(Direction dir);
    void _computeCountGridDataThread(int startidx, int endidx, Direction dir, 
                                     CountGridData *data);
    void _advectionProducerThread(BoundedBuffer<BlockData> *blockQueue, 
                                  BoundedBuffer<BlockData> *finishedBlockQueue, 
                                  Direction dir);

    // Parameters
    FragmentedVector<MarkerParticle> *_particles;
    MACVelocityField *_vfield;
    ValidVelocityComponentGrid *_validVelocities;
    std::vector<vmath::vec3> _points;
    std::vector<vmath::vec3> _velocities;
    double _dx = 0.0;
    double _chunkdx = 0.0;
    double _particleRadius = 0.0;

    int _chunkWidth = 10;
    int _numBlocksPerJob = 10;
    
};

#endif
