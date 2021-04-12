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

#include "velocityadvector.h"

#include "macvelocityfield.h"
#include "gridutils.h"
#include "threadutils.h"


VelocityAdvector::VelocityAdvector() {
}

VelocityAdvector::~VelocityAdvector() {
}

void VelocityAdvector::advect(VelocityAdvectorParameters params) {
    _initializeParameters(params);
    _advectGrid(Direction::U);
    _advectGrid(Direction::V);
    _advectGrid(Direction::W);
}

void VelocityAdvector::_initializeParameters(VelocityAdvectorParameters params) {
    _particles = params.particles;
    _vfield = params.vfield;
    _validVelocities = params.validVelocities;
    _particleRadius = params.particleRadius;
    _velocityTransferMethod = params.velocityTransferMethod;
    
    _dx = _vfield->getGridCellSize();
    _chunkdx = _dx * _chunkWidth;

    std::vector<vmath::vec3> *positions, *velocities;
    _particles->getAttributeValues("POSITION", positions);
    _particles->getAttributeValues("VELOCITY", velocities);

    _points = *positions;
    _velocities = *velocities;

    if (_isAPIC()) {
        std::vector<vmath::vec3> *affineX, *affineY, *affineZ;
        _particles->getAttributeValues("AFFINEX", affineX);
        _particles->getAttributeValues("AFFINEY", affineY);
        _particles->getAttributeValues("AFFINEZ", affineZ);

        _affineX = *affineX;
        _affineY = *affineY;
        _affineZ = *affineZ;
    }
}

void VelocityAdvector::_advectGrid(Direction dir) {
    BlockArray3d<ScalarData> blockphi;
    _initializeBlockGrid(blockphi, dir);

    ParticleGridCountData gridCountData;
    _computeGridCountData(blockphi, gridCountData, dir);

    std::vector<PointData> sortedParticleData;
    std::vector<AffineData> sortedAffineData;
    std::vector<int> blockToParticleDataIndex;
    _sortParticlesIntoBlocks(gridCountData, 
                             sortedParticleData, sortedAffineData, 
                             blockToParticleDataIndex, 
                             dir);

    std::vector<GridBlock<ScalarData> > gridBlocks;
    blockphi.getActiveGridBlocks(gridBlocks);
    BoundedBuffer<ComputeBlock> computeBlockQueue(gridBlocks.size());
    BoundedBuffer<ComputeBlock> finishedComputeBlockQueue(gridBlocks.size());
    int numComputeBlocks = 0;
    for (size_t bidx = 0; bidx < gridBlocks.size(); bidx++) {
        GridBlock<ScalarData> b = gridBlocks[bidx];
        if (gridCountData.totalGridCount[b.id] == 0) {
            continue;
        }

        ComputeBlock computeBlock;
        computeBlock.gridBlock = b;
        computeBlock.particleData = &(sortedParticleData[blockToParticleDataIndex[b.id]]);

        if (_isAPIC()) {
            computeBlock.affineData = &(sortedAffineData[blockToParticleDataIndex[b.id]]);
        }

        computeBlock.numParticles = gridCountData.totalGridCount[b.id];
        computeBlock.radius = _particleRadius;
        computeBlockQueue.push(computeBlock);
        numComputeBlocks++;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, std::ceil((float)computeBlockQueue.size() / (float)_numBlocksPerJob));
    std::vector<std::thread> producerThreads(numthreads);
    for (int i = 0; i < numthreads; i++) {
        if (_isFLIP()) {
            producerThreads[i] = std::thread(&VelocityAdvector::_advectionFLIPProducerThread, this,
                                             &computeBlockQueue, &finishedComputeBlockQueue);
        } else {
            producerThreads[i] = std::thread(&VelocityAdvector::_advectionAPICProducerThread, this,
                                         &computeBlockQueue, &finishedComputeBlockQueue);
        }
    }

    Array3d<float> *vfieldgrid = NULL;
    Array3d<bool> *validgrid = NULL;
    if (dir == Direction::U) {
        vfieldgrid = _vfield->getArray3dU();
        validgrid = &(_validVelocities->validU);
    } else if (dir == Direction::V) {
        vfieldgrid = _vfield->getArray3dV();
        validgrid = &(_validVelocities->validV);
    } else if (dir == Direction::W) {
        vfieldgrid = _vfield->getArray3dW();
        validgrid = &(_validVelocities->validW);
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
                GridIndex vfieldidx = GridIndex(localidx.i + gridOffset.i,
                                               localidx.j + gridOffset.j,
                                               localidx.k + gridOffset.k);
                if (vfieldgrid->isIndexInRange(vfieldidx)) {
                    vfieldgrid->set(vfieldidx, block.gridBlock.data[vidx].scalar);
                    if (block.gridBlock.data[vidx].weight > eps) {
                        validgrid->set(vfieldidx, true);
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

vmath::vec3 VelocityAdvector::_getDirectionOffset(Direction dir) {
    vmath::vec3 offset;
    if (dir == Direction::U) {
        offset = vmath::vec3(0.0, 0.5*_dx, 0.5*_dx);
    } else if (dir == Direction::V) {
        offset = vmath::vec3(0.5*_dx, 0.0, 0.5*_dx);
    } else if (dir == Direction::W) {
        offset = vmath::vec3(0.5*_dx, 0.5*_dx, 0.0);
    }

    return offset;
}

void VelocityAdvector::_initializeBlockGrid(BlockArray3d<ScalarData> &blockphi, Direction dir) {
    int isize, jsize, ksize;
    _vfield->getGridDimensions(&isize, &jsize, &ksize);
    if (dir == Direction::U) {
        isize += 1;
    } else if (dir == Direction::V) {
        jsize += 1;
    } else if (dir == Direction::W) {
        ksize += 1;
    }

    BlockArray3dParameters params;
    params.isize = isize;
    params.jsize = jsize;
    params.ksize = ksize;
    params.blockwidth = _chunkWidth;
    Dims3d dims = BlockArray3d<ScalarData>::getBlockDimensions(params);

    Array3d<bool> activeBlocks(dims.i, dims.j, dims.k, false);

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _points.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _points.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&VelocityAdvector::_initializeActiveBlocksThread, this,
                                 intervals[i], intervals[i + 1], &activeBlocks, dir);
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

    ScalarData emptyData;
    blockphi = BlockArray3d<ScalarData>(params);
    blockphi.fill(emptyData);
}

void VelocityAdvector::_initializeActiveBlocksThread(int startidx, int endidx, 
                                                     Array3d<bool> *activeBlocks, 
                                                     Direction dir) {
    vmath::vec3 offset = _getDirectionOffset(dir);
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = _points[i] - offset;
        GridIndex g = Grid3d::positionToGridIndex(p, _chunkdx);
        if (activeBlocks->isIndexInRange(g)) {
            activeBlocks->set(g, true);
        }
    }
}

void VelocityAdvector::_computeGridCountData(BlockArray3d<ScalarData> &blockphi, 
                                             ParticleGridCountData &countdata,
                                             Direction dir) {

    _initializeGridCountData(blockphi, countdata);

    int numthreads = countdata.numthreads;
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _points.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&VelocityAdvector::_computeGridCountDataThread, this,
                                 intervals[i], intervals[i + 1],
                                 &blockphi, 
                                 &(countdata.threadGridCountData[i]),
                                 dir);
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

void VelocityAdvector::_initializeGridCountData(BlockArray3d<ScalarData> &blockphi, 
                                                ParticleGridCountData &countdata) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _points.size());
    int numblocks = blockphi.getNumActiveGridBlocks();
    countdata.numthreads = numthreads;
    countdata.gridsize = numblocks;
    countdata.threadGridCountData = std::vector<GridCountData>(numthreads);
    for (int i = 0; i < numthreads; i++) {
        countdata.threadGridCountData[i].gridCount = std::vector<int>(numblocks, 0);
    }
    countdata.totalGridCount = std::vector<int>(numblocks, 0);
}

void VelocityAdvector::_computeGridCountDataThread(int startidx, int endidx, 
                                                   BlockArray3d<ScalarData> *blockphi, 
                                                   GridCountData *countdata,
                                                   Direction dir) {
    
    countdata->simpleGridIndices = std::vector<int>(endidx - startidx, -1);
    countdata->invalidPoints = std::vector<bool>(endidx - startidx, false);
    countdata->startidx = startidx;
    countdata->endidx = endidx;

    float eps = 1e-6;
    float sr = _particleRadius + eps;
    float blockdx = _chunkdx;
    vmath::vec3 offset = _getDirectionOffset(dir);
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = _points[i] - offset;
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

void VelocityAdvector::_sortParticlesIntoBlocks(ParticleGridCountData &countdata, 
                                                std::vector<PointData> &sortedParticleData, 
                                                std::vector<AffineData> &sortedAffineData, 
                                                std::vector<int> &blockToParticleIndex,
                                                Direction dir) {
    int diridx = 0;
    if (dir == Direction::U) {
        diridx = 0;
    } else if (dir == Direction::V) {
        diridx = 1;
    } else if (dir == Direction::W) {
        diridx = 2;
    }

    blockToParticleIndex = std::vector<int>(countdata.gridsize, 0);
    int currentIndex = 0;
    for (size_t i = 0; i < blockToParticleIndex.size(); i++) {
        blockToParticleIndex[i] = currentIndex;
        currentIndex += countdata.totalGridCount[i];
    }
    std::vector<int> blockToParticleIndexCurrent = blockToParticleIndex;
    int totalParticleCount = currentIndex;

    vmath::vec3 offset = _getDirectionOffset(dir);
    sortedParticleData = std::vector<PointData>(totalParticleCount);

    if (_isFLIP()) {

        for (int tidx = 0; tidx < countdata.numthreads; tidx++) {
            GridCountData *countData = &(countdata.threadGridCountData[tidx]);

            int indexOffset = countData->startidx;
            int currentOverlappingIndex = 0;
            for (size_t i = 0; i < countData->simpleGridIndices.size(); i++) {
                if (countData->invalidPoints[i]) {
                    continue;
                }

                vmath::vec3 p = _points[i + indexOffset] - offset;
                float v = _velocities[i + indexOffset][diridx];
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

    } else if (_isAPIC()) {

        sortedAffineData = std::vector<AffineData>(totalParticleCount);
        for (int tidx = 0; tidx < countdata.numthreads; tidx++) {
            GridCountData *countData = &(countdata.threadGridCountData[tidx]);

            int indexOffset = countData->startidx;
            int currentOverlappingIndex = 0;
            for (size_t i = 0; i < countData->simpleGridIndices.size(); i++) {
                if (countData->invalidPoints[i]) {
                    continue;
                }

                vmath::vec3 p = _points[i + indexOffset] - offset;
                float v = _velocities[i + indexOffset][diridx];
                PointData pdata(p.x, p.y, p.z, v);
                AffineData adata;

                if (dir == Direction::U) {
                    adata = AffineData(_affineX[i + indexOffset]);
                } else if (dir == Direction::V) {
                    adata = AffineData(_affineY[i + indexOffset]);
                } else if (dir == Direction::W) {
                    adata = AffineData(_affineZ[i + indexOffset]);
                }

                if (countData->simpleGridIndices[i] >= 0) {
                    int blockid = countData->simpleGridIndices[i];
                    int sortedIndex = blockToParticleIndexCurrent[blockid];
                    sortedParticleData[sortedIndex] = pdata;
                    sortedAffineData[sortedIndex] = adata;
                    blockToParticleIndexCurrent[blockid]++;
                } else {
                    int numblocks = -(countData->simpleGridIndices[i]);
                    for (int blockidx = 0; blockidx < numblocks; blockidx++) {
                        int blockid = countData->overlappingGridIndices[currentOverlappingIndex];
                        currentOverlappingIndex++;

                        int sortedIndex = blockToParticleIndexCurrent[blockid];
                        sortedParticleData[sortedIndex] = pdata;
                        sortedAffineData[sortedIndex] = adata;
                        blockToParticleIndexCurrent[blockid]++;
                    }
                }
            }
        }

    }

}

void VelocityAdvector::_advectionFLIPProducerThread(BoundedBuffer<ComputeBlock> *blockQueue, 
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
                float velocity = pdata.v;

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
                                block.gridBlock.data[flatidx].scalar += weight * velocity;
                                block.gridBlock.data[flatidx].weight += weight;
                            }
                        }
                    }
                }
            }

            int numVals = _chunkWidth * _chunkWidth * _chunkWidth;
            for (int i = 0; i < numVals; i++) {
                if (block.gridBlock.data[i].weight > eps) {
                    block.gridBlock.data[i].scalar /= block.gridBlock.data[i].weight;
                }
            }

            finishedBlockQueue->push(block);
        }
    }

}

/*
    The APIC (Affine Particle-In-Cell) velocity transfer method was adapted from
    Doyub Kim's 'Fluid Engine Dev' repository:
        https://github.com/doyubkim/fluid-engine-dev
*/
void VelocityAdvector::_advectionAPICProducerThread(BoundedBuffer<ComputeBlock> *blockQueue, 
                                                    BoundedBuffer<ComputeBlock> *finishedBlockQueue) {

    float eps = 1e-6;
    GridIndex indices[8];
    float weights[8];

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
                AffineData adata = block.affineData[pidx];

                vmath::vec3 p(pdata.x, pdata.y, pdata.z);
                p -= blockPositionOffset;
                float velocity = pdata.v;
                vmath::vec3 affine = vmath::vec3(adata.x, adata.y, adata.z);

                GridIndex g = Grid3d::positionToGridIndex(p, _dx);
                vmath::vec3 gpos = Grid3d::GridIndexToPosition(g, _dx);
                vmath::vec3 ipos = (p - gpos) / _dx;

                indices[0] = GridIndex(g.i,     g.j,     g.k);
                indices[1] = GridIndex(g.i + 1, g.j,     g.k);
                indices[2] = GridIndex(g.i,     g.j + 1, g.k);
                indices[3] = GridIndex(g.i + 1, g.j + 1, g.k);
                indices[4] = GridIndex(g.i,     g.j,     g.k + 1);
                indices[5] = GridIndex(g.i + 1, g.j,     g.k + 1);
                indices[6] = GridIndex(g.i,     g.j + 1, g.k + 1);
                indices[7] = GridIndex(g.i + 1, g.j + 1, g.k + 1);

                weights[0] = (1.0f - ipos.x) * (1.0f - ipos.y) * (1.0f - ipos.z);
                weights[1] = ipos.x * (1.0f - ipos.y) * (1.0f - ipos.z);
                weights[2] = (1.0f - ipos.x) * ipos.y * (1.0f - ipos.z);
                weights[3] = ipos.x * ipos.y * (1.0f - ipos.z);
                weights[4] = (1.0f - ipos.x) * (1.0f - ipos.y) * ipos.z;
                weights[5] = ipos.x * (1.0f - ipos.y) * ipos.z;
                weights[6] = (1.0f - ipos.x) * ipos.y * ipos.z;
                weights[7] = ipos.x * ipos.y * ipos.z;

                for (int gidx = 0; gidx < 8; gidx++) {
                    GridIndex index = indices[gidx];
                    if (index.i < 0 || index.j < 0 || index.k < 0 || 
                            index.i >= _chunkWidth || index.j >= _chunkWidth || index.k >= _chunkWidth) {
                        continue;
                    }

                    vmath::vec3 nodepos = Grid3d::GridIndexToPosition(index, _dx);
                    float apicTerm = vmath::dot(affine, nodepos - p);
                    float weight = weights[gidx];

                    int flatidx = Grid3d::getFlatIndex(index, _chunkWidth, _chunkWidth);
                    block.gridBlock.data[flatidx].scalar += weight * (velocity + apicTerm);
                    block.gridBlock.data[flatidx].weight += weight;
                }

            }

            int numVals = _chunkWidth * _chunkWidth * _chunkWidth;
            for (int i = 0; i < numVals; i++) {
                if (block.gridBlock.data[i].weight > eps) {
                    block.gridBlock.data[i].scalar /= block.gridBlock.data[i].weight;
                }
            }

            finishedBlockQueue->push(block);
        }
    }

}
