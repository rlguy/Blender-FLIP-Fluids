/*
MIT License

Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender

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

#ifndef FLUIDENGINE_ATTRIBUTETOGRIDTRANSFER_H
#define FLUIDENGINE_ATTRIBUTETOGRIDTRANSFER_H


#include "blockarray3d.h"
#include "boundedbuffer.h"


template <class T>
struct AttributeTransferParameters {
    std::vector<vmath::vec3> *positions;
    std::vector<T> *attributes;
    Array3d<T> *attributeGrid;
    Array3d<bool> *validGrid;
    double particleRadius = 1.0;
    double dx = 1.0;
    bool normalize = true;
};


template <class T>
class AttributeToGridTransfer {

public:

    AttributeToGridTransfer() {}
    ~AttributeToGridTransfer() {}

    void transfer(AttributeTransferParameters<T> params) {
        _initializeParameters(params);

        BlockArray3d<AttributeData> blockphi;
        _initializeBlockGrid(blockphi);

        ParticleGridCountData gridCountData;
        _computeGridCountData(blockphi, gridCountData);

        std::vector<PointData> sortedParticleData;
        std::vector<int> blockToParticleDataIndex;
        _sortParticlesIntoBlocks(gridCountData, 
                                 sortedParticleData, 
                                 blockToParticleDataIndex);

        std::vector<GridBlock<AttributeData> > gridBlocks;
        blockphi.getActiveGridBlocks(gridBlocks);
        BoundedBuffer<ComputeBlock> computeBlockQueue(gridBlocks.size());
        BoundedBuffer<ComputeBlock> finishedComputeBlockQueue(gridBlocks.size());
        int numComputeBlocks = 0;
        for (size_t bidx = 0; bidx < gridBlocks.size(); bidx++) {
            GridBlock<AttributeData> b = gridBlocks[bidx];
            if (gridCountData.totalGridCount[b.id] == 0) {
                continue;
            }

            ComputeBlock computeBlock;
            computeBlock.gridBlock = b;
            computeBlock.particleData = &(sortedParticleData[blockToParticleDataIndex[b.id]]);
            computeBlock.numParticles = gridCountData.totalGridCount[b.id];
            computeBlock.radius = _particleRadius;
            computeBlockQueue.push(computeBlock);
            numComputeBlocks++;
        }

        int numCPU = ThreadUtils::getMaxThreadCount();
        int numthreads = (int)fmin(numCPU, std::ceil((float)computeBlockQueue.size() / (float)_numBlocksPerJob));
        std::vector<std::thread> producerThreads(numthreads);
        for (int i = 0; i < numthreads; i++) {
            producerThreads[i] = std::thread(&AttributeToGridTransfer::_transferProducerThread, this,
                                             &computeBlockQueue, &finishedComputeBlockQueue);
        }

        int numComputeBlocksProcessed = 0;
        while (numComputeBlocksProcessed < numComputeBlocks) {
            std::vector<ComputeBlock> finishedBlocks;
            finishedComputeBlockQueue.popAll(finishedBlocks);

            for (size_t i = 0; i < finishedBlocks.size(); i++) {
                ComputeBlock block = finishedBlocks[i];
                GridIndex gridOffset(block.gridBlock.index.i * _chunkWidth,
                                     block.gridBlock.index.j * _chunkWidth,
                                     block.gridBlock.index.k * _chunkWidth);

                float eps = 1e-6;
                int datasize = _chunkWidth * _chunkWidth * _chunkWidth;
                for (int vidx = 0; vidx < datasize; vidx++) {
                    GridIndex localidx = Grid3d::getUnflattenedIndex(vidx, _chunkWidth, _chunkWidth);
                    GridIndex grididx = GridIndex(localidx.i + gridOffset.i,
                                                  localidx.j + gridOffset.j,
                                                  localidx.k + gridOffset.k);
                    if (_attributeGrid->isIndexInRange(grididx)) {
                        _attributeGrid->set(grididx, block.gridBlock.data[vidx].value);
                        if (block.gridBlock.data[vidx].weight > eps) {
                            _validGrid->set(grididx, true);
                        }
                    }
                }
            }

            numComputeBlocksProcessed += finishedBlocks.size();
        }

        computeBlockQueue.notifyFinished();
        for (size_t i = 0; i < producerThreads.size(); i++) {
            computeBlockQueue.notifyFinished();
            producerThreads[i].join();
        }
    }
    
private:

    struct AttributeData {
        T value;
        float weight = 0.0f;
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


    struct PointData {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        T v;

        PointData() {}
        PointData(float px, float py, float pz, T val)
                    : x(px), y(py), z(pz), v(val) {}
    };


    struct ComputeBlock {
        GridBlock<AttributeData> gridBlock;
        PointData *particleData = nullptr;
        int numParticles = 0;
        float radius = 0.0f;
    };


    void _initializeParameters(AttributeTransferParameters<T> params) {
        _positions = *(params.positions);
        _attributes = *(params.attributes);
        _attributeGrid = params.attributeGrid;
        _validGrid = params.validGrid;
        _particleRadius = params.particleRadius;
        _dx = params.dx;
        _chunkdx = _dx * _chunkWidth;
        _normalize = params.normalize;
    }


    void _initializeBlockGrid(BlockArray3d<AttributeData> &blockphi) {
        int isize = _attributeGrid->width;
        int jsize = _attributeGrid->height;
        int ksize = _attributeGrid->depth;

        BlockArray3dParameters params;
        params.isize = isize;
        params.jsize = jsize;
        params.ksize = ksize;
        params.blockwidth = _chunkWidth;
        Dims3d dims = BlockArray3d<AttributeData>::getBlockDimensions(params);

        Array3d<bool> activeBlocks(dims.i, dims.j, dims.k, false);

        int numCPU = ThreadUtils::getMaxThreadCount();
        int numthreads = (int)fmin(numCPU, _positions.size());
        std::vector<std::thread> threads(numthreads);
        std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _attributes.size(), numthreads);

        for (int i = 0; i < numthreads; i++) {
            threads[i] = std::thread(&AttributeToGridTransfer::_initializeActiveBlocksThread, this,
                                     intervals[i], intervals[i + 1], &activeBlocks);
        }

        for (int i = 0; i < numthreads; i++) {
            threads[i].join();
        }

        GridUtils::featherGrid26(&activeBlocks, numthreads);

        for (int k = 0; k < dims.k; k++) {
            for (int j = 0; j < dims.j; j++) {
                for (int i = 0; i < dims.i; i++) {
                    if (activeBlocks(i, j, k)) {
                        params.activeblocks.push_back(GridIndex(i, j, k));
                    }
                }
            }
        }

        AttributeData emptyData;
        emptyData.value = T();
        emptyData.weight = 0.0f;

        blockphi = BlockArray3d<AttributeData>(params);
        blockphi.fill(emptyData);
    }


    void _initializeActiveBlocksThread(int startidx, int endidx, Array3d<bool> *activeBlocks) {
        vmath::vec3 offset = _getGridOffset();
        for (int i = startidx; i < endidx; i++) {
            vmath::vec3 p = _positions[i] - offset;
            GridIndex g = Grid3d::positionToGridIndex(p, _chunkdx);
            if (activeBlocks->isIndexInRange(g)) {
                activeBlocks->set(g, true);
            }
        }
    }


    void _computeGridCountData(BlockArray3d<AttributeData> &blockphi, ParticleGridCountData &countdata) {
        _initializeGridCountData(blockphi, countdata);

        int numthreads = countdata.numthreads;
        std::vector<std::thread> threads(numthreads);
        std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _positions.size(), numthreads);
        for (int i = 0; i < numthreads; i++) {
            threads[i] = std::thread(&AttributeToGridTransfer::_computeGridCountDataThread, this,
                                     intervals[i], intervals[i + 1],
                                     &blockphi, 
                                     &(countdata.threadGridCountData[i]));
        }

        for (int i = 0; i < numthreads; i++) {
            threads[i].join();
        }

        for (int tidx = 0; tidx < countdata.numthreads; tidx++) {
            std::vector<int> *threadGridCount = &(countdata.threadGridCountData[tidx].gridCount);
            for (size_t i = 0; i < countdata.totalGridCount.size(); i++) {
                countdata.totalGridCount[i] += threadGridCount->at(i);
            }
        }
    }


    void _initializeGridCountData(BlockArray3d<AttributeData> &blockphi, ParticleGridCountData &countdata) {
        int numCPU = ThreadUtils::getMaxThreadCount();
        int numthreads = (int)fmin(numCPU, _positions.size());
        int numblocks = blockphi.getNumActiveGridBlocks();
        countdata.numthreads = numthreads;
        countdata.gridsize = numblocks;
        countdata.threadGridCountData = std::vector<GridCountData>(numthreads);
        for (int i = 0; i < numthreads; i++) {
            countdata.threadGridCountData[i].gridCount = std::vector<int>(numblocks, 0);
        }
        countdata.totalGridCount = std::vector<int>(numblocks, 0);
    }


    void _computeGridCountDataThread(int startidx, int endidx, 
                                     BlockArray3d<AttributeData> *blockphi, 
                                     GridCountData *countdata) {
        
        countdata->simpleGridIndices = std::vector<int>(endidx - startidx, -1);
        countdata->invalidPoints = std::vector<bool>(endidx - startidx, false);
        countdata->startidx = startidx;
        countdata->endidx = endidx;

        float eps = 1e-6;
        float sr = _particleRadius + eps;
        float blockdx = _chunkdx;
        vmath::vec3 offset = _getGridOffset();
        for (int i = startidx; i < endidx; i++) {
            vmath::vec3 p = _positions[i] - offset;
            GridIndex blockIndex = Grid3d::positionToGridIndex(p, blockdx);
            vmath::vec3 blockPosition = Grid3d::GridIndexToPosition(blockIndex, blockdx);

            if (p.x - sr > blockPosition.x && 
                    p.y - sr > blockPosition.y && 
                    p.z - sr > blockPosition.z && 
                    p.x + sr < blockPosition.x + blockdx && 
                    p.y + sr < blockPosition.y + blockdx && 
                    p.z + sr < blockPosition.z + blockdx) {
                int blockid = blockphi->getBlockID(blockIndex);
                countdata->simpleGridIndices[i - startidx] = blockid;

                if (blockid != -1) {
                    countdata->gridCount[blockid]++;
                } else {
                    countdata->invalidPoints[i - startidx] = true;
                }
            } else {
                GridIndex gmin = Grid3d::positionToGridIndex(p.x - sr, p.y - sr, p.z - sr, blockdx);
                GridIndex gmax = Grid3d::positionToGridIndex(p.x + sr, p.y + sr, p.z + sr, blockdx);

                int overlapCount = 0;
                for (int gk = gmin.k; gk <= gmax.k; gk++) {
                    for (int gj = gmin.j; gj <= gmax.j; gj++) {
                        for (int gi = gmin.i; gi <= gmax.i; gi++) {
                            int blockid = blockphi->getBlockID(gi, gj, gk);
                            if (blockid != -1) {
                                countdata->gridCount[blockid]++;
                                countdata->overlappingGridIndices.push_back(blockid);
                                overlapCount++;
                            }
                        }
                    }
                }

                if (overlapCount == 0) {
                    countdata->invalidPoints[i - startidx] = true;
                }
                countdata->simpleGridIndices[i - startidx] = -overlapCount;
            }
        }

    }


    void _sortParticlesIntoBlocks(ParticleGridCountData &countdata, 
                                  std::vector<PointData> &sortedParticleData,
                                  std::vector<int> &blockToParticleIndex) {

        blockToParticleIndex = std::vector<int>(countdata.gridsize, 0);
        int currentIndex = 0;
        for (size_t i = 0; i < blockToParticleIndex.size(); i++) {
            blockToParticleIndex[i] = currentIndex;
            currentIndex += countdata.totalGridCount[i];
        }
        std::vector<int> blockToParticleIndexCurrent = blockToParticleIndex;
        int totalParticleCount = currentIndex;

        vmath::vec3 offset = _getGridOffset();
        sortedParticleData = std::vector<PointData>(totalParticleCount);

        for (int tidx = 0; tidx < countdata.numthreads; tidx++) {
            GridCountData *countData = &(countdata.threadGridCountData[tidx]);

            int indexOffset = countData->startidx;
            int currentOverlappingIndex = 0;
            for (size_t i = 0; i < countData->simpleGridIndices.size(); i++) {
                if (countData->invalidPoints[i]) {
                    continue;
                }

                vmath::vec3 p = _positions[i + indexOffset] - offset;
                T v = _attributes[i + indexOffset];
                PointData pdata(p.x, p.y, p.z, v);

                if (countData->simpleGridIndices[i] >= 0) {
                    int blockid = countData->simpleGridIndices[i];
                    int sortedIndex = blockToParticleIndexCurrent[blockid];
                    sortedParticleData[sortedIndex] = pdata;
                    blockToParticleIndexCurrent[blockid]++;
                } else {
                    int numblocks = -(countData->simpleGridIndices[i]);
                    for (int blockidx = 0; blockidx < numblocks; blockidx++) {
                        int blockid = countData->overlappingGridIndices[currentOverlappingIndex];
                        currentOverlappingIndex++;

                        int sortedIndex = blockToParticleIndexCurrent[blockid];
                        sortedParticleData[sortedIndex] = pdata;
                        blockToParticleIndexCurrent[blockid]++;
                    }
                }
            }
        }

    }


    void _transferProducerThread(BoundedBuffer<ComputeBlock> *blockQueue, 
                                 BoundedBuffer<ComputeBlock> *finishedBlockQueue) {

        float eps = 1e-6;
        float r = _particleRadius;
        float sr = _particleRadius + eps;
        float rsq = r * r;
        float coef1 = (4.0f / 9.0f) * (1.0f / (r*r*r*r*r*r));
        float coef2 = (17.0f / 9.0f) * (1.0f / (r*r*r*r));
        float coef3 = (22.0f / 9.0f) * (1.0f / (r*r));

        while (blockQueue->size() > 0) {
            std::vector<ComputeBlock> computeBlocks;
            int numBlocks = blockQueue->pop(_numBlocksPerJob, computeBlocks);
            if (numBlocks == 0) {
                continue;
            }

            for (size_t bidx = 0; bidx < computeBlocks.size(); bidx++) {
                ComputeBlock block = computeBlocks[bidx];
                GridIndex blockIndex = block.gridBlock.index;
                vmath::vec3 blockPositionOffset = Grid3d::GridIndexToPosition(blockIndex, _chunkWidth * _dx);

                for (int pidx = 0; pidx < block.numParticles; pidx++) {
                    PointData pdata = block.particleData[pidx];
                    vmath::vec3 p(pdata.x, pdata.y, pdata.z);
                    p -= blockPositionOffset;
                    T value = pdata.v;

                    vmath::vec3 pmin(p.x - sr, p.y - sr, p.z - sr);
                    vmath::vec3 pmax(p.x + sr, p.y + sr, p.z + sr);
                    GridIndex gmin = Grid3d::positionToGridIndex(pmin, _dx);
                    GridIndex gmax = Grid3d::positionToGridIndex(pmax, _dx);
                    gmin.i = std::max(gmin.i, 0);
                    gmin.j = std::max(gmin.j, 0);
                    gmin.k = std::max(gmin.k, 0);
                    gmax.i = std::min(gmax.i, _chunkWidth - 1);
                    gmax.j = std::min(gmax.j, _chunkWidth - 1);
                    gmax.k = std::min(gmax.k, _chunkWidth - 1);

                    for (int k = gmin.k; k <= gmax.k; k++) {
                        for (int j = gmin.j; j <= gmax.j; j++) {
                            for (int i = gmin.i; i <= gmax.i; i++) {
                                vmath::vec3 gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                                vmath::vec3 v = gpos - p;
                                float d2 = vmath::dot(v, v);
                                if (d2 < rsq) {
                                    float weight = 1.0f - coef1*d2*d2*d2 + coef2*d2*d2 - coef3*d2;

                                    int flatidx = Grid3d::getFlatIndex(i, j, k, _chunkWidth, _chunkWidth);
                                    block.gridBlock.data[flatidx].value += weight * value;
                                    block.gridBlock.data[flatidx].weight += weight;
                                }
                            }
                        }
                    }
                }

                if (_normalize) {
                    int numVals = _chunkWidth * _chunkWidth * _chunkWidth;
                    for (int i = 0; i < numVals; i++) {
                        if (block.gridBlock.data[i].weight > eps) {
                            block.gridBlock.data[i].value /= block.gridBlock.data[i].weight;
                        }
                    }
                }

                finishedBlockQueue->push(block);
            }
        }

    }


    vmath::vec3 _getGridOffset() {
        return vmath::vec3(0.0f, 0.0f, 0.0f);
    }


    std::vector<vmath::vec3> _positions;
    std::vector<T> _attributes;
    Array3d<T> *_attributeGrid;
    Array3d<bool> *_validGrid;
    double _particleRadius = 1.0;
    double _dx = 0.0;
    bool _normalize = true;

    double _chunkdx = 0.0;

    int _chunkWidth = 10;
    int _numBlocksPerJob = 10;
    
};

#endif
