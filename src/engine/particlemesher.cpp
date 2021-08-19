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

#include "particlemesher.h"

#include "trianglemesh.h"
#include "polygonizer3d.h"
#include "threadutils.h"
#include "gridutils.h"


ParticleMesher::ParticleMesher() {
}

TriangleMesh ParticleMesher::meshParticles(ParticleMesherParameters params) {
    _initialize(params);

    MesherComputeChunkData data;
    _generateComputeChunkData(data);
    
    double scale = _localdx / _subdx;
    vmath::vec3 scaleVect(scale, scale, scale);
    vmath::vec3 invscaleVect(1.0/scale, 1.0/scale, 1.0/scale);

    TriangleMesh mesh;
    for (size_t i = 0; i < data.computeChunks.size(); i++) {
        MesherComputeChunk c = data.computeChunks[i];
        TriangleMesh chunkMesh = _polygonizeComputeChunk(c, data);
        chunkMesh.scale(scaleVect);
        mesh.join(chunkMesh);
    }
    mesh.scale(invscaleVect);

    return mesh;
}

TriangleMesh ParticleMesher::getPreviewMesh() {
    if (!_isPreviewMesherEnabled) {
        return TriangleMesh();
    }

    ScalarField field = _pfield;
    _setScalarFieldSolidBorders(field);

    Polygonizer3d polygonizer(&field);
    return polygonizer.polygonizeSurface();
}

void ParticleMesher::_initialize(ParticleMesherParameters params) {
    _isize = params.isize;
    _jsize = params.jsize;
    _ksize = params.ksize;
    _dx = params.dx;

    _subdivisions = params.subdivisions;
    _computechunks = params.computechunks;
    _radius = params.radius;

    _isPreviewMesherEnabled = params.isPreviewMesherEnabled;
    if (_isPreviewMesherEnabled) {
        _initializePreviewMesher(params.previewdx);
    }

    _particles = params.particles;
    _solidSDF = params.solidSDF;

    _subisize = _isize * _subdivisions + 1;
    _subjsize = _jsize * _subdivisions + 1;
    _subksize = _ksize * _subdivisions + 1;
    _subdx = _dx / (double)_subdivisions;

    _initializeSeamData();
}

void ParticleMesher::_initializePreviewMesher(double pdx) {
    double width = _isize * _dx;
    double height = _jsize * _dx;
    double depth = _ksize * _dx;

    _pisize = std::max((int)ceil(width / pdx), 1);
    _pjsize = std::max((int)ceil(height / pdx), 1);
    _pksize = std::max((int)ceil(depth / pdx), 1);
    _pdx = pdx;

    _pfield = ScalarField(_pisize + 1, _pjsize + 1, _pksize + 1, _pdx);
    _pfield.setSurfaceThreshold(0.0);
}

void ParticleMesher::_initializeSeamData() {
    _seamData.reset();
}

void ParticleMesher::_generateComputeChunkData(MesherComputeChunkData &data) {
    _initializeComputeChunkDataActiveBlocks(data);
    _initializeComputeChunkDataComputeChunks(data);
}

void ParticleMesher::_initializeComputeChunkDataActiveBlocks(MesherComputeChunkData &data) {
    BlockArray3dParameters temp;
    temp.isize = _subisize;
    temp.jsize = _subjsize;
    temp.ksize = _subksize;
    temp.blockwidth = _blockwidth;
    Dims3d dims = BlockArray3d<bool>::getBlockDimensions(temp);

    data.activeBlocks = Array3d<bool>(dims.i, dims.j, dims.k, false);

    double blockdx = _blockwidth * _subdx;
    for (size_t i = 0; i < _particles->size(); i++) {
        vmath::vec3 p = _particles->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, blockdx);
        data.activeBlocks.set(g, true);
    }

    int numthreads = ThreadUtils::getMaxThreadCount();
    GridUtils::featherGrid26(&(data.activeBlocks), numthreads);
}

void ParticleMesher::_initializeComputeChunkDataComputeChunks(MesherComputeChunkData &data) {
    int bi = data.activeBlocks.width;
    int bj = data.activeBlocks.height;
    int bk = data.activeBlocks.depth;

    Direction splitdir = Direction::U;
    int splitwidth = bi;
    if (bj > splitwidth) {
        splitdir = Direction::V;
        splitwidth = bj;
    }
    if (bk > splitwidth) {
        splitdir = Direction::W;
        splitwidth = bk;
    }

    int nchunks = _computechunks;
    int chunkwidth = (int)ceil((float)splitwidth/(float)nchunks);
    nchunks = (int)ceil((float)splitwidth/(float)chunkwidth);

    typedef std::pair<GridIndex, GridIndex> IndexPair;
    std::vector<IndexPair> chunkBounds;
    int startidx = 0;
    for (int i = 0; i < nchunks; i++) {
        int endidx = startidx + chunkwidth;
        endidx = std::min(endidx, splitwidth);

        GridIndex ming(0, 0, 0);
        GridIndex maxg(bi, bj, bk);
        if (splitdir == Direction::U) {
            ming.i = startidx;
            maxg.i = endidx;
        } else if (splitdir == Direction::V) {
            ming.j = startidx;
            maxg.j = endidx;
        } else if (splitdir == Direction::W) {
            ming.k = startidx;
            maxg.k = endidx;
        }

        maxg.i = std::min(maxg.i + 1, bi);
        maxg.j = std::min(maxg.j + 1, bj);
        maxg.k = std::min(maxg.k + 1, bk);

        chunkBounds.push_back(IndexPair(ming, maxg));
        startidx = endidx;
    }

    std::vector<IndexPair> chunkBoundsOptimized;
    for (size_t cidx = 0; cidx < chunkBounds.size(); cidx++) {
        GridIndex gmin = chunkBounds[cidx].first;
        GridIndex gmax = chunkBounds[cidx].second;

        bool isActive = false;
        GridIndex gminOptimized = gmax;
        GridIndex gmaxOptimized = gmin;

        for (int k = gmin.k; k < gmax.k; k++) {
            for (int j = gmin.j; j < gmax.j; j++) {
                for (int i = gmin.i; i < gmax.i; i++) {
                    if (data.activeBlocks(i, j, k)) {
                        isActive = true;
                        gminOptimized.i = std::min(gminOptimized.i, i);
                        gminOptimized.j = std::min(gminOptimized.j, j);
                        gminOptimized.k = std::min(gminOptimized.k, k);
                        gmaxOptimized.i = std::max(gmaxOptimized.i, i + 1);
                        gmaxOptimized.j = std::max(gmaxOptimized.j, j + 1);
                        gmaxOptimized.k = std::max(gmaxOptimized.k, k + 1);
                    }
                }
            }
        }

        if (splitdir == Direction::U) {
            gminOptimized.j = std::max(gminOptimized.j - 1, 0);
            gminOptimized.k = std::max(gminOptimized.k - 1, 0);
            gmaxOptimized.j = std::min(gmaxOptimized.j + 1, bj);
            gmaxOptimized.k = std::min(gmaxOptimized.k + 1, bk);
        } else if (splitdir == Direction::V) {
            gminOptimized.i = std::max(gminOptimized.i - 1, 0);
            gminOptimized.k = std::max(gminOptimized.k - 1, 0);
            gmaxOptimized.i = std::min(gmaxOptimized.i + 1, bi);
            gmaxOptimized.k = std::min(gmaxOptimized.k + 1, bk);
        } else if (splitdir == Direction::W) {
            gminOptimized.i = std::max(gminOptimized.i - 1, 0);
            gminOptimized.j = std::max(gminOptimized.j - 1, 0);
            gmaxOptimized.i = std::min(gmaxOptimized.i + 1, bi);
            gmaxOptimized.j = std::min(gmaxOptimized.j + 1, bj);
        }

        if (isActive) {
            chunkBoundsOptimized.push_back(IndexPair(gminOptimized, gmaxOptimized));
        }
    }


    chunkBounds = chunkBoundsOptimized;
    for (size_t cidx = 0; cidx < chunkBounds.size(); cidx++) {
        GridIndex gmin = chunkBounds[cidx].first;
        GridIndex gmax = chunkBounds[cidx].second;

        MesherComputeChunk c;
        c.id = cidx;
        c.minBlockIndex = gmin;
        c.maxBlockIndex = gmax;
        c.minGridIndex = GridIndex(_blockwidth * gmin.i, 
                                   _blockwidth * gmin.j, 
                                   _blockwidth * gmin.k);

        if (cidx == chunkBounds.size() - 1) {
            c.maxGridIndex = GridIndex(std::min(_blockwidth * gmax.i, _subisize), 
                                       std::min(_blockwidth * gmax.j, _subjsize), 
                                       std::min(_blockwidth * gmax.k, _subksize));
        } else {
            //c.maxGridIndex = GridIndex(std::min(_blockwidth * (gmax.i - 1) + 1, _subisize), 
            //                           std::min(_blockwidth * (gmax.j - 1) + 1, _subjsize), 
            //                           std::min(_blockwidth * (gmax.k - 1) + 1, _subksize));
            c.maxGridIndex = GridIndex(std::min(_blockwidth * gmax.i, _subisize), 
                                       std::min(_blockwidth * gmax.j, _subjsize), 
                                       std::min(_blockwidth * gmax.k, _subksize));
            if (splitdir == Direction::U) {
                c.maxGridIndex.i = std::min(_blockwidth * (gmax.i - 1) + 1, _subisize);
            } else if (splitdir == Direction::V) {
                c.maxGridIndex.j = std::min(_blockwidth * (gmax.j - 1) + 1, _subjsize);
            } else if (splitdir == Direction::W) {
                c.maxGridIndex.k = std::min(_blockwidth * (gmax.k - 1) + 1, _subksize);
            }
        }

        c.positionOffset = Grid3d::GridIndexToPosition(c.minGridIndex, _subdx);
        c.splitDirection = splitdir;
        c.isize = c.maxGridIndex.i - c.minGridIndex.i;
        c.jsize = c.maxGridIndex.j - c.minGridIndex.j;
        c.ksize = c.maxGridIndex.k - c.minGridIndex.k;

        data.computeChunks.push_back(c);
    }
}

TriangleMesh ParticleMesher::_polygonizeComputeChunk(MesherComputeChunk chunk, 
                                                     MesherComputeChunkData &data) {
    
    ScalarFieldData fieldData;
    _initializeScalarFieldData(chunk, data, fieldData);

    if (fieldData.particles.empty()) {
        return TriangleMesh();
    }

    _computeScalarField(fieldData);
    _updateSeamData(fieldData);

    Polygonizer3d polygonizer(&(fieldData.fieldValues), _solidSDF);

    TriangleMesh m = polygonizer.polygonizeSurface();
    m.translate(chunk.positionOffset);
    
    return m;
}

void ParticleMesher::_initializeScalarFieldData(MesherComputeChunk chunk,  
                                                MesherComputeChunkData &data,
                                                ScalarFieldData &fieldData) {
    float eps = 1e-6;
    vmath::vec3 pmin = chunk.positionOffset;
    vmath::vec3 pmax = Grid3d::GridIndexToPosition(chunk.maxGridIndex, _subdx);
    AABB bbox(pmin, pmax);
    bbox.expand(2.0f * (_radius + eps));
    int count = 0;
    for (size_t i = 0; i < _particles->size(); i++) {
        if (bbox.isPointInside(_particles->at(i))) {
            count++;
        }
    }

    if (count == 0) {
        return;
    }

    fieldData.particles.reserve(count);
    for (size_t i = 0; i < _particles->size(); i++) {
        vmath::vec3 p = _particles->at(i);
        if (bbox.isPointInside(p)) {
            fieldData.particles.push_back(p - chunk.positionOffset);
        }
    }

    BlockArray3dParameters params;
    params.isize = chunk.isize;
    params.jsize = chunk.jsize;
    params.ksize = chunk.ksize;
    params.blockwidth = _blockwidth;

    for (int k = chunk.minBlockIndex.k; k < chunk.maxBlockIndex.k; k++) {
        for (int j = chunk.minBlockIndex.j; j < chunk.maxBlockIndex.j; j++) {
            for (int i = chunk.minBlockIndex.i; i < chunk.maxBlockIndex.i; i++) {
                if (data.activeBlocks(i, j, k)) {
                    params.activeblocks.push_back(GridIndex(i - chunk.minBlockIndex.i,
                                                            j - chunk.minBlockIndex.j,
                                                            k - chunk.minBlockIndex.k));
                }
            }
        }
    }

    fieldData.computeChunk = chunk;
    fieldData.scalarField = BlockArray3d<float>(params);
    fieldData.scalarField.fill(_getMaxDistanceValue());

    fieldData.fieldValues = ScalarField(chunk.isize, chunk.jsize, chunk.ksize, _subdx);
    fieldData.fieldValues.fill(_getMaxDistanceValue());
    fieldData.fieldValues.setSurfaceThreshold(0.0);
    fieldData.fieldValues.setOffset(chunk.positionOffset);
    fieldData.fieldValues.setSolidSDF(*_solidSDF);
}

float ParticleMesher::_getMaxDistanceValue() {
    return 3.0 * _radius;
}

void ParticleMesher::_computeScalarField(ScalarFieldData &fieldData) {
    ParticleGridCountData gridCountData;
    _computeGridCountData(fieldData, gridCountData);

    std::vector<vmath::vec3> sortedParticles;
    std::vector<int> blockToParticleIndex;
    _sortParticlesIntoBlocks(fieldData, gridCountData, sortedParticles, blockToParticleIndex);

    std::vector<GridBlock<float> > gridBlocks;
    fieldData.scalarField.getActiveGridBlocks(gridBlocks);
    BoundedBuffer<ComputeBlock> computeBlockQueue(gridBlocks.size());
    BoundedBuffer<ComputeBlock> finishedComputeBlockQueue(gridBlocks.size());
    int numComputeBlocks = 0;
    for (size_t bidx = 0; bidx < gridBlocks.size(); bidx++) {
        GridBlock<float> b = gridBlocks[bidx];
        if (gridCountData.totalGridCount[b.id] == 0) {
            continue;
        }

        ComputeBlock computeBlock;
        computeBlock.gridBlock = b;
        computeBlock.particleData = &(sortedParticles[blockToParticleIndex[b.id]]);
        computeBlock.numParticles = gridCountData.totalGridCount[b.id];
        computeBlockQueue.push(computeBlock);
        numComputeBlocks++;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, computeBlockQueue.size());
    std::vector<std::thread> producerThreads(numthreads);
    for (int i = 0; i < numthreads; i++) {
        producerThreads[i] = std::thread(&ParticleMesher::_scalarFieldProducerThread, this,
                                         &computeBlockQueue, &finishedComputeBlockQueue);
    }

    Array3d<float>* fieldValues = fieldData.fieldValues.getPointerToScalarField();

    int numComputeBlocksProcessed = 0;
    while (numComputeBlocksProcessed < numComputeBlocks) {
        std::vector<ComputeBlock> finishedBlocks;
        finishedComputeBlockQueue.popAll(finishedBlocks);
        for (size_t i = 0; i < finishedBlocks.size(); i++) {
            ComputeBlock block = finishedBlocks[i];
            GridIndex gridOffset(block.gridBlock.index.i * _blockwidth,
                                 block.gridBlock.index.j * _blockwidth,
                                 block.gridBlock.index.k * _blockwidth);

            int datasize = _blockwidth * _blockwidth * _blockwidth;
            for (int vidx = 0; vidx < datasize; vidx++) {
                GridIndex localidx = Grid3d::getUnflattenedIndex(vidx, _blockwidth, _blockwidth);
                GridIndex fieldidx = GridIndex(localidx.i + gridOffset.i,
                                               localidx.j + gridOffset.j,
                                               localidx.k + gridOffset.k);
                if (fieldValues->isIndexInRange(fieldidx)) {
                    fieldValues->set(fieldidx, block.gridBlock.data[vidx]);
                }
            }
        }

        numComputeBlocksProcessed += finishedBlocks.size();
    }

    for (int k = 0; k < fieldValues->depth; k++) {
        for (int j = 0; j < fieldValues->height; j++) {
            for (int i = 0; i < fieldValues->width; i++) {
                fieldValues->set(i, j, k, -fieldValues->get(i, j, k));
            }
        }
    }

    computeBlockQueue.notifyFinished();
    for (size_t i = 0; i < producerThreads.size(); i++) {
        computeBlockQueue.notifyFinished();
        producerThreads[i].join();
    }

    if (_isPreviewMesherEnabled) {
        _addComputeChunkScalarFieldToPreviewField(fieldData);
    }
}

void ParticleMesher::_computeGridCountData(ScalarFieldData &fieldData, 
                                           ParticleGridCountData &gridCountData) {

    _initializeGridCountData(fieldData, gridCountData);

    int numthreads = gridCountData.numthreads;
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, fieldData.particles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleMesher::_computeGridCountDataThread, this,
                                 intervals[i], intervals[i + 1], &fieldData, 
                                 &(gridCountData.threadGridCountData[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    for (int tidx = 0; tidx < gridCountData.numthreads; tidx++) {
        std::vector<int> *threadGridCount = &(gridCountData.threadGridCountData[tidx].gridCount);
        for (size_t i = 0; i < gridCountData.totalGridCount.size(); i++) {
            gridCountData.totalGridCount[i] += threadGridCount->at(i);
        }
    }
}

void ParticleMesher::_initializeGridCountData(ScalarFieldData &fieldData, 
                                              ParticleGridCountData &gridCountData) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, fieldData.particles.size());
    int numblocks = fieldData.scalarField.getNumActiveGridBlocks();
    gridCountData.numthreads = numthreads;
    gridCountData.gridsize = numblocks;
    gridCountData.threadGridCountData = std::vector<GridCountData>(numthreads);
    for (int i = 0; i < numthreads; i++) {
        gridCountData.threadGridCountData[i].gridCount = std::vector<int>(numblocks, 0);
    }
    gridCountData.totalGridCount = std::vector<int>(numblocks, 0);
}

void ParticleMesher::_computeGridCountDataThread(int startidx, int endidx, 
                                                 ScalarFieldData *fieldData, 
                                                 GridCountData *countData) {

    countData->simpleGridIndices = std::vector<int>(endidx - startidx, -1);
    countData->invalidPoints = std::vector<bool>(endidx - startidx, false);
    countData->startidx = startidx;
    countData->endidx = endidx;

    float sr = _searchRadiusFactor * (float)_radius;
    float blockdx = _blockwidth * _subdx;
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = fieldData->particles[i];
        GridIndex blockIndex = Grid3d::positionToGridIndex(p, blockdx);
        vmath::vec3 blockPosition = Grid3d::GridIndexToPosition(blockIndex, blockdx);

        if (p.x - sr > blockPosition.x && 
                p.y - sr > blockPosition.y && 
                p.z - sr > blockPosition.z && 
                p.x + sr < blockPosition.x + blockdx && 
                p.y + sr < blockPosition.y + blockdx && 
                p.z + sr < blockPosition.z + blockdx) {
            int blockid = fieldData->scalarField.getBlockID(blockIndex);
            countData->simpleGridIndices[i - startidx] = blockid;

            if (blockid != -1) {
                countData->gridCount[blockid]++;
            } else {
                countData->invalidPoints[i - startidx] = true;
            }
        } else {
            GridIndex gmin = Grid3d::positionToGridIndex(p.x - sr, p.y - sr, p.z - sr, blockdx);
            GridIndex gmax = Grid3d::positionToGridIndex(p.x + sr, p.y + sr, p.z + sr, blockdx);

            int overlapCount = 0;
            for (int gk = gmin.k; gk <= gmax.k; gk++) {
                for (int gj = gmin.j; gj <= gmax.j; gj++) {
                    for (int gi = gmin.i; gi <= gmax.i; gi++) {
                        int blockid = fieldData->scalarField.getBlockID(gi, gj, gk);
                        if (blockid != -1) {
                            countData->gridCount[blockid]++;
                            countData->overlappingGridIndices.push_back(blockid);
                            overlapCount++;
                        }
                    }
                }
            }

            if (overlapCount == 0) {
                countData->invalidPoints[i - startidx] = true;
            }
            countData->simpleGridIndices[i - startidx] = -overlapCount;
        }
    }
}

void ParticleMesher::_sortParticlesIntoBlocks(ScalarFieldData &fieldData, 
                                              ParticleGridCountData &gridCountData,
                                              std::vector<vmath::vec3> &sortedParticles,
                                              std::vector<int> &blockToParticleIndex) {

    blockToParticleIndex = std::vector<int>(gridCountData.gridsize, 0);
    int currentIndex = 0;
    for (size_t i = 0; i < blockToParticleIndex.size(); i++) {
        blockToParticleIndex[i] = currentIndex;
        currentIndex += gridCountData.totalGridCount[i];
    }
    std::vector<int> blockToParticleIndexCurrent = blockToParticleIndex;
    int totalParticleCount = currentIndex;

    sortedParticles = std::vector<vmath::vec3>(totalParticleCount);
    for (int tidx = 0; tidx < gridCountData.numthreads; tidx++) {
        GridCountData *countData = &(gridCountData.threadGridCountData[tidx]);

        int indexOffset = countData->startidx;
        int currentOverlappingIndex = 0;
        for (size_t i = 0; i < countData->simpleGridIndices.size(); i++) {
            if (countData->invalidPoints[i]) {
                continue;
            }

            vmath::vec3 p = fieldData.particles[i + indexOffset];
            if (countData->simpleGridIndices[i] >= 0) {
                int blockid = countData->simpleGridIndices[i];
                int sortedIndex = blockToParticleIndexCurrent[blockid];
                sortedParticles[sortedIndex] = p;
                blockToParticleIndexCurrent[blockid]++;
            } else {
                int numblocks = -(countData->simpleGridIndices[i]);
                for (int blockidx = 0; blockidx < numblocks; blockidx++) {
                    int blockid = countData->overlappingGridIndices[currentOverlappingIndex];
                    currentOverlappingIndex++;

                    int sortedIndex = blockToParticleIndexCurrent[blockid];
                    sortedParticles[sortedIndex] = p;
                    blockToParticleIndexCurrent[blockid]++;
                }
            }
        }
    }
}

void ParticleMesher::_scalarFieldProducerThread(BoundedBuffer<ComputeBlock> *computeBlockQueue,
                                                BoundedBuffer<ComputeBlock> *finishedComputeBlockQueue) {
    
    float r = _radius;
    float sr = _searchRadiusFactor * r;

    while (computeBlockQueue->size() > 0) {
        std::vector<ComputeBlock> computeBlocks;
        int numBlocks = computeBlockQueue->pop(_numComputeBlocksPerJob, computeBlocks);
        if (numBlocks == 0) {
            continue;
        }

        for (size_t bidx = 0; bidx < computeBlocks.size(); bidx++) {
            ComputeBlock block = computeBlocks[bidx];
            GridIndex blockIndex = block.gridBlock.index;
            vmath::vec3 blockPositionOffset = Grid3d::GridIndexToPosition(blockIndex, _blockwidth * _subdx);

            for (int pidx = 0; pidx < block.numParticles; pidx++) {
                vmath::vec3 p = block.particleData[pidx];
                p -= blockPositionOffset;

                vmath::vec3 pmin(p.x - sr, p.y - sr, p.z - sr);
                vmath::vec3 pmax(p.x + sr, p.y + sr, p.z + sr);
                GridIndex gmin = Grid3d::positionToGridIndex(pmin, _subdx);
                GridIndex gmax = Grid3d::positionToGridIndex(pmax, _subdx);
                gmax.i++;
                gmax.j++;
                gmax.k++;

                for (int k = gmin.k; k <= gmax.k; k++) {
                    for (int j = gmin.j; j <= gmax.j; j++) {
                        for (int i = gmin.i; i <= gmax.i; i++) {
                            if (i < 0 || j < 0 || k < 0 ||
                                    i >= _blockwidth || j >= _blockwidth || k >= _blockwidth) {
                                continue;
                            }

                            vmath::vec3 gpos = Grid3d::GridIndexToPosition(i, j, k, _subdx);
                            float dist = vmath::length(gpos - p) - r;
                            int flatidx = Grid3d::getFlatIndex(i, j, k, _blockwidth, _blockwidth);
                            if (dist < block.gridBlock.data[flatidx]) {
                                 block.gridBlock.data[flatidx] = dist;
                            }
                        }
                    }
                }
            }

            finishedComputeBlockQueue->push(block);
        }
    }
}

void ParticleMesher::_setScalarFieldSolidBorders(ScalarField &field) {
    double eps = 1e-3;
    double thresh = field.getSurfaceThreshold() - eps;
    int si, sj, sk;
    field.getGridDimensions(&si, &sj, &sk);

    for (int j = 0; j < sj; j++) {
        for (int i = 0; i < si; i++) {
            field.setScalarFieldValue(i, j, 0, thresh);
            field.setScalarFieldValue(i, j, sk-1, thresh);
        }
    }

    for (int k = 0; k < sk; k++) {
        for (int i = 0; i < si; i++) {
            field.setScalarFieldValue(i, 0, k, thresh);
            field.setScalarFieldValue(i, sj-1, k, thresh);
        }
    }

    for (int k = 0; k < sk; k++) {
        for (int j = 0; j < sj; j++) {
            field.setScalarFieldValue(0, j, k, thresh);
            field.setScalarFieldValue(si-1, j, k, thresh);
        }
    }
}

void ParticleMesher::_addComputeChunkScalarFieldToPreviewField(ScalarFieldData &fieldData) {
    int isize, jsize, ksize;
    fieldData.fieldValues.getGridDimensions(&isize, &jsize, &ksize);

    double width = isize * _dx;
    double height = jsize * _dx;
    double depth = ksize * _dx;
    vmath::vec3 offset = fieldData.computeChunk.positionOffset;
    AABB bbox(offset, width, height, depth);

    vmath::vec3 pv;
    double eps = _dx * 1e-3;
    for (int k = 0; k < _pksize + 1; k++) {
        for (int j = 0; j < _pjsize + 1; j++) {
            for (int i = 0; i < _pisize + 1; i++) {
                pv = Grid3d::GridIndexToPosition(i, j, k, _pdx);
                if (!bbox.isPointInside(pv)) {
                    continue;
                }

                double fval = fieldData.fieldValues.trilinearInterpolation(pv - offset);
                if (std::abs(fval) > eps) {
                    _pfield.setScalarFieldValue(i, j, k, fval);
                }
            }
        }
    }
}

void ParticleMesher::_updateSeamData(ScalarFieldData &fieldData) {
    _applySeamData(fieldData);
    _commitSeamData(fieldData);
}

void ParticleMesher::_applySeamData(ScalarFieldData &fieldData) {
    if (!_seamData.isInitialized) {
        return;
    }

    MesherComputeChunk chunk = fieldData.computeChunk;
    GridIndex gmin = chunk.minGridIndex;
    Direction dir = chunk.splitDirection;

    bool isJoinedAtSeam = false;
    if (dir == Direction::U) {
        isJoinedAtSeam = gmin.i == _seamData.minGridIndex.i;
    } else if (dir == Direction::V) {
        isJoinedAtSeam = gmin.j == _seamData.minGridIndex.j;
    } else if (dir == Direction::W) {
        isJoinedAtSeam = gmin.k == _seamData.minGridIndex.k;
    }

    if (!isJoinedAtSeam) {
        return;
    }

    Array3d<float>* fieldValues = fieldData.fieldValues.getPointerToScalarField();
    for (int k = 0; k < _seamData.data.depth; k++) {
        for (int j = 0; j < _seamData.data.height; j++) {
            for (int i = 0; i < _seamData.data.width; i++) {
                GridIndex fieldIndex(_seamData.minGridIndex.i + i - gmin.i,
                                     _seamData.minGridIndex.j + j - gmin.j,
                                     _seamData.minGridIndex.k + k - gmin.k);
                if (!fieldValues->isIndexInRange(fieldIndex)) {
                    continue;
                }

                fieldValues->set(fieldIndex, _seamData.data(i, j, k));
            }
        }
    }
}

void ParticleMesher::_commitSeamData(ScalarFieldData &fieldData) {
    MesherComputeChunk chunk = fieldData.computeChunk;
    GridIndex gmin = chunk.minGridIndex;
    GridIndex gmax = chunk.maxGridIndex;
    Direction dir = chunk.splitDirection;

    Array3d<float>* fieldValues = fieldData.fieldValues.getPointerToScalarField();
    GridIndex fieldOffset;
    if (dir == Direction::U) {
        gmin.i = gmax.i - 1;
        fieldOffset = GridIndex(fieldValues->width - 1, 0, 0);
    } else if (dir == Direction::V) {
        gmin.j = gmax.j - 1;
        fieldOffset = GridIndex(0, fieldValues->height - 1, 0);
    } else if (dir == Direction::W) {
        gmin.k = gmax.k - 1;
        fieldOffset = GridIndex(0, 0, fieldValues->depth - 1);
    }

    _seamData.direction = dir;
    _seamData.minGridIndex = gmin;
    _seamData.maxGridIndex = gmax;

    _seamData.data = Array3d<float>(gmax.i - gmin.i, gmax.j - gmin.j, gmax.k - gmin.k);
    for (int k = 0; k < _seamData.data.depth; k++) {
        for (int j = 0; j < _seamData.data.height; j++) {
            for (int i = 0; i < _seamData.data.width; i++) {
                GridIndex fieldIndex(fieldOffset.i + i, 
                                     fieldOffset.j + j, 
                                     fieldOffset.k + k);
                _seamData.data.set(i, j, k, fieldValues->get(fieldIndex));
            }
        }
    }

    _seamData.isInitialized = true;
}