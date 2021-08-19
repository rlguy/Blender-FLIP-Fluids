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

#ifndef FLUIDENGINE_PARTICLEMESHER_H
#define FLUIDENGINE_PARTICLEMESHER_H

#include <vector>

#include "vmath.h"
#include "array3d.h"
#include "blockarray3d.h"
#include "scalarfield.h"
#include "boundedbuffer.h"

class TriangleMesh;
class MeshLevelSet;

struct ParticleMesherParameters {
    int isize = 0;
    int jsize = 0;
    int ksize = 0;
    double dx = 0.0;

    int subdivisions = 1;
    int computechunks = 1;
    double radius = 0.0;

    bool isPreviewMesherEnabled = false;
    double previewdx = 0.0;
    
    std::vector<vmath::vec3> *particles;
    MeshLevelSet *solidSDF;
};

class ParticleMesher {

public:
    ParticleMesher();
    TriangleMesh meshParticles(ParticleMesherParameters params);
    TriangleMesh getPreviewMesh();

private:
    enum class Direction { U, V, W };

    struct MesherComputeChunk {
        int id = 0;
        GridIndex minBlockIndex;
        GridIndex maxBlockIndex;
        GridIndex minGridIndex;
        GridIndex maxGridIndex;
        vmath::vec3 positionOffset;
        Direction splitDirection;
        int isize = 0;
        int jsize = 0;
        int ksize = 0;
    };

    struct MesherComputeChunkData {
        Array3d<bool> activeBlocks;
        std::vector<MesherComputeChunk> computeChunks;
    };

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

    struct ScalarFieldData {
        MesherComputeChunk computeChunk;
        BlockArray3d<float> scalarField;
        ScalarField fieldValues;
        std::vector<vmath::vec3> particles;
    };

    struct ComputeBlock {
        GridBlock<float> gridBlock;
        vmath::vec3 *particleData;
        int numParticles = 0;
    };

    struct ScalarFieldSeam {
        Direction direction;
        GridIndex minGridIndex;
        GridIndex maxGridIndex;
        Array3d<float> data;
        bool isInitialized = false;

        void reset() {
            direction = Direction::U;
            minGridIndex = GridIndex(-1, -1, -1);
            maxGridIndex = GridIndex(-1, -1, -1);
            data = Array3d<float>();
            isInitialized = false;
        }
    };

    void _initialize(ParticleMesherParameters params);
    void _initializePreviewMesher(double dx);
    void _initializeSeamData();

    void _generateComputeChunkData(MesherComputeChunkData &data);
    void _initializeComputeChunkDataActiveBlocks(MesherComputeChunkData &data);
    void _initializeComputeChunkDataComputeChunks(MesherComputeChunkData &data);

    TriangleMesh _polygonizeComputeChunk(MesherComputeChunk chunk, MesherComputeChunkData &data);
    void _initializeScalarFieldData(MesherComputeChunk chunk, MesherComputeChunkData &data,
                                    ScalarFieldData &fieldData);
    float _getMaxDistanceValue();
    void _computeScalarField(ScalarFieldData &fieldData);
    void _computeGridCountData(ScalarFieldData &fieldData, 
                               ParticleGridCountData &gridCountData);
    void _initializeGridCountData(ScalarFieldData &fieldData, 
                                  ParticleGridCountData &gridCountData);
    void _computeGridCountDataThread(int startidx, int endidx, 
                                     ScalarFieldData *fieldData, 
                                     GridCountData *countData);
    void _sortParticlesIntoBlocks(ScalarFieldData &fieldData, 
                                  ParticleGridCountData &gridCountData,
                                  std::vector<vmath::vec3> &sortedParticles,
                                  std::vector<int> &blockToParticleIndex);
    void _scalarFieldProducerThread(BoundedBuffer<ComputeBlock> *computeBlockQueue,
                                    BoundedBuffer<ComputeBlock> *finishedComputeBlockQueue);

    void _setScalarFieldSolidBorders(ScalarField &field);
    void _addComputeChunkScalarFieldToPreviewField(ScalarFieldData &fieldData);
    void _updateSeamData(ScalarFieldData &fieldData);
    void _applySeamData(ScalarFieldData &fieldData);
    void _commitSeamData(ScalarFieldData &fieldData);


    // Meshing Parameters

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    int _subisize = 0;
    int _subjsize = 0;
    int _subksize = 0;
    double _subdx = 0.0;

    int _subdivisions = 1;
    int _computechunks = 1;
    double _radius = 0.0;

    bool _isPreviewMesherEnabled = false;
    int _pisize = 0;
    int _pjsize = 0;
    int _pksize = 0;
    double _pdx = 0.0;
    ScalarField _pfield;

    std::vector<vmath::vec3> *_particles;
    MeshLevelSet *_solidSDF;

    // Internal Parameters
    int _blockwidth = 10;
    int _numComputeBlocksPerJob = 10;
    double _localdx = 0.1;
    float _searchRadiusFactor = 1.5f;
    ScalarFieldSeam _seamData;

};

#endif