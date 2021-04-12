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

#include "particlelevelset.h"

#include "levelsetutils.h"
#include "interpolation.h"
#include "polygonizer3d.h"
#include "gridutils.h"
#include "threadutils.h"
#include "markerparticle.h"
#include "grid3d.h"
#include "meshlevelset.h"
#include "scalarfield.h"
#include "levelsetsolver.h"


ParticleLevelSet::ParticleLevelSet() {
}

ParticleLevelSet::ParticleLevelSet(int i, int j, int k, double dx) : 
                    _isize(i), _jsize(j), _ksize(k), _dx(dx) {
    _phi = Array3d<float>(i, j, k, _getMaxDistance());
}

ParticleLevelSet::~ParticleLevelSet() {
}

float ParticleLevelSet::operator()(int i, int j, int k) {
    return get(i, j, k);
}

float ParticleLevelSet::operator()(GridIndex g) {
    return get(g);
}

float ParticleLevelSet::get(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));
    return _phi(i, j, k);
}

float ParticleLevelSet::get(GridIndex g) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize));
    return _phi(g);
}

float ParticleLevelSet::getFaceWeightU(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize, _ksize));
    return LevelsetUtils::fractionInside(_phi(i - 1, j, k), _phi(i, j, k));
}

float ParticleLevelSet::getFaceWeightU(GridIndex g) {
    return getFaceWeightU(g.i, g.j, g.k);
}

float ParticleLevelSet::getFaceWeightV(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize + 1, _ksize));
    return LevelsetUtils::fractionInside(_phi(i, j - 1, k), _phi(i, j, k));
}

float ParticleLevelSet::getFaceWeightV(GridIndex g) {
    return getFaceWeightV(g.i, g.j, g.k);
}

float ParticleLevelSet::getFaceWeightW(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize + 1));
    return LevelsetUtils::fractionInside(_phi(i, j, k - 1), _phi(i, j, k));
}

float ParticleLevelSet::getFaceWeightW(GridIndex g) {
    return getFaceWeightW(g.i, g.j, g.k);
}

void ParticleLevelSet::getNodalPhi(Array3d<float> &nodalPhi) {
    FLUIDSIM_ASSERT(nodalPhi.width == _isize + 1 && 
                    nodalPhi.height == _jsize + 1 && 
                    nodalPhi.depth == _ksize + 1);

    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {

                float sum = 0.0;
                if (Grid3d::isGridIndexInRange(i - 1, j - 1, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j - 1, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i, j - 1, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j - 1, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i - 1, j, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i, j, k - 1, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j, k - 1);
                }
                if (Grid3d::isGridIndexInRange(i - 1, j - 1, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j - 1, k);
                }
                if (Grid3d::isGridIndexInRange(i, j - 1, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j - 1, k);
                }
                if (Grid3d::isGridIndexInRange(i - 1, j, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i - 1, j, k);
                }
                if (Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize)) {
                    sum += _phi(i, j, k);
                }

                nodalPhi.set(i, j, k, 0.125f * sum);
            }
        }
    }
}

float ParticleLevelSet::trilinearInterpolate(vmath::vec3 pos) {
    return Interpolation::trilinearInterpolate(pos - vmath::vec3(0.5*_dx, 0.5*_dx, 0.5*_dx), _dx, _phi);
}

float ParticleLevelSet::getDistanceAtNode(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize + 1, _ksize + 1));

    if (Grid3d::isGridIndexOnBorder(i, j, k, _isize + 1, _jsize + 1, _ksize + 1)) {
        return _getMaxDistance();
    }

    return 0.125f * (_phi(i - 1, j - 1, k - 1) + 
                     _phi(i    , j - 1, k - 1) + 
                     _phi(i - 1, j    , k - 1) + 
                     _phi(i    , j    , k - 1) +
                     _phi(i - 1, j - 1, k    ) + 
                     _phi(i    , j - 1, k    ) + 
                     _phi(i - 1, j    , k    ) + 
                     _phi(i    , j    , k    ));
}

float ParticleLevelSet::getDistanceAtNode(GridIndex g) {
    return getDistanceAtNode(g.i, g.j, g.k);
}

void ParticleLevelSet::calculateSignedDistanceField(ParticleSystem &particles, 
                                                    double radius) {
    std::vector<vmath::vec3> *positions;
    particles.getAttributeValues("POSITION", positions);

    std::vector<vmath::vec3> points = *positions;
    _computeSignedDistanceFromParticles(points, radius);
}

void ParticleLevelSet::postProcessSignedDistanceField(MeshLevelSet &solidPhi) {
    // Extrapolate SDF into solids and enforce that distance values at nodes are not too small

    int si, sj, sk;
    solidPhi.getGridDimensions(&si, &sj, &sk);
    FLUIDSIM_ASSERT(si == _isize && sj == _jsize && sk == _ksize);

    float eps = 0.005 * _dx;
    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize; i++) {
                if(_phi(i, j, k) < 0.5 * _dx) {
                    if (solidPhi.getDistanceAtCellCenter(i, j, k) < 0) {
                        _phi.set(i, j, k, -0.5f * _dx);
                    }
                }

                float val = _phi(i, j, k);
                if (std::abs(val) < eps) {
                    _phi.set(i, j, k, val > 0 ? eps : -eps);
                }
            }
        }
    }
}

void ParticleLevelSet::calculateCurvatureGrid(Array3d<float> &surfacePhi, 
                                              Array3d<float> &kgrid) {

    FLUIDSIM_ASSERT(surfacePhi.width == _isize && 
                    surfacePhi.height == _jsize && 
                    surfacePhi.depth == _ksize);
    FLUIDSIM_ASSERT(kgrid.width == _isize && 
                    kgrid.height == _jsize && 
                    kgrid.depth == _ksize);

    float maxSurfaceCellDist = 2.0f * _dx;
    Array3d<bool> validNodes(_isize, _jsize, _ksize, false);
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (std::abs(_phi(i, j, k)) < maxSurfaceCellDist) {
                    validNodes.set(i, j, k, true);
                }
            }
        }
    }

    int blockWidth = 2 * _curvatureGridExactBand;
    int bisize = (_isize + blockWidth - 1) / blockWidth;
    int bjsize = (_jsize + blockWidth - 1) / blockWidth;
    int bksize = (_ksize + blockWidth - 1) / blockWidth;
    Array3d<bool> validBlocks(bisize, bjsize, bksize, false);

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (validNodes(i, j, k)) {
                    validBlocks.set(i / blockWidth, j / blockWidth, k / blockWidth, true);
                }
            }
        }
    }
    GridUtils::featherGrid6(&validBlocks, ThreadUtils::getMaxThreadCount());

    int numValid = 0;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                int bi = i / blockWidth;
                int bj = j / blockWidth;
                int bk = k / blockWidth;
                if (validBlocks(bi, bj, bk)) {
                    validNodes.set(i, j, k, true);
                    numValid++;
                }
            }
        }
    }

    std::vector<GridIndex> solverGridCells(numValid);
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (validNodes(i, j, k)) {
                    solverGridCells.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    float width = _curvatureGridExactBand * _dx;
    LevelSetSolver solver;
    solver.reinitializeUpwind(_phi, _dx, width, solverGridCells, surfacePhi);

    float outOfRangeDist = _outOfRangeDistance * _dx;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (!validNodes(i, j, k)) {
                    surfacePhi.set(i, j, k, outOfRangeDist);
                }
            }
        }
    }

    validNodes.fill(false);
    _getValidCurvatureNodes(surfacePhi, validNodes);

    kgrid.fill(0.0f);
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (validNodes(i, j, k)) {
                    kgrid.set(i, j, k, _getCurvature(i, j, k, surfacePhi));
                }
            }
        }
    }

    GridUtils::extrapolateGrid(&kgrid, &validNodes, _curvatureGridExtrapolationLayers);
}

float ParticleLevelSet::_getMaxDistance() {
    return 3.0 * _dx;
}

void ParticleLevelSet::_computeSignedDistanceFromParticles(std::vector<vmath::vec3> &particles, 
                                                           double radius) {
    _phi.fill(_getMaxDistance());

    if (particles.empty()) {
        return;
    }

    BlockArray3d<float> blockphi;
    _initializeBlockGrid(particles, blockphi);

    ParticleGridCountData gridCountData;
    _computeGridCountData(particles, radius, blockphi, gridCountData);

    std::vector<vmath::vec3> sortedParticleData;
    std::vector<int> blockToParticleDataIndex;
    _sortParticlesIntoBlocks(particles, gridCountData, sortedParticleData, blockToParticleDataIndex);

    std::vector<GridBlock<float> > gridBlocks;
    blockphi.getActiveGridBlocks(gridBlocks);
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
        computeBlock.particleData = &(sortedParticleData[blockToParticleDataIndex[b.id]]);
        computeBlock.numParticles = gridCountData.totalGridCount[b.id];
        computeBlock.radius = radius;
        computeBlockQueue.push(computeBlock);
        numComputeBlocks++;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, computeBlockQueue.size());
    std::vector<std::thread> producerThreads(numthreads);
    for (int i = 0; i < numthreads; i++) {
        producerThreads[i] = std::thread(&ParticleLevelSet::_computeExactBandProducerThread, this,
                                         &computeBlockQueue, &finishedComputeBlockQueue);
    }

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
                GridIndex phiidx = GridIndex(localidx.i + gridOffset.i,
                                             localidx.j + gridOffset.j,
                                             localidx.k + gridOffset.k);
                if (_phi.isIndexInRange(phiidx)) {
                    _phi.set(phiidx, block.gridBlock.data[vidx]);
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

void ParticleLevelSet::_initializeBlockGrid(std::vector<vmath::vec3> &particles,
                                            BlockArray3d<float> &blockphi) {
    BlockArray3dParameters params;
    params.isize = _isize;
    params.jsize = _jsize;
    params.ksize = _ksize;
    params.blockwidth = _blockwidth;
    Dims3d dims = BlockArray3d<float>::getBlockDimensions(params);

    Array3d<bool> activeBlocks(dims.i, dims.j, dims.k, false);

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, particles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, particles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleLevelSet::_initializeActiveBlocksThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &particles, &activeBlocks);
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

    blockphi = BlockArray3d<float>(params);
    blockphi.fill(_getMaxDistance());
}

void ParticleLevelSet::_initializeActiveBlocksThread(int startidx, int endidx, 
                                                     std::vector<vmath::vec3> *particles,
                                                     Array3d<bool> *activeBlocks) {
    float blockdx = _blockwidth * _dx;
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = particles->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, blockdx);
        if (activeBlocks->isIndexInRange(g)) {
            activeBlocks->set(g, true);
        }
    }
}

void ParticleLevelSet::_computeGridCountData(std::vector<vmath::vec3> &particles,
                                             double radius,
                                             BlockArray3d<float> &blockphi, 
                                             ParticleGridCountData &countdata) {

    _initializeGridCountData(particles, blockphi, countdata);

    int numthreads = countdata.numthreads;
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, particles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleLevelSet::_computeGridCountDataThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &particles,
                                 radius, 
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

void ParticleLevelSet::_initializeGridCountData(std::vector<vmath::vec3> &particles,
                                                BlockArray3d<float> &blockphi, 
                                                ParticleGridCountData &countdata) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, particles.size());
    int numblocks = blockphi.getNumActiveGridBlocks();
    countdata.numthreads = numthreads;
    countdata.gridsize = numblocks;
    countdata.threadGridCountData = std::vector<GridCountData>(numthreads);
    for (int i = 0; i < numthreads; i++) {
        countdata.threadGridCountData[i].gridCount = std::vector<int>(numblocks, 0);
    }
    countdata.totalGridCount = std::vector<int>(numblocks, 0);
}

void ParticleLevelSet::_computeGridCountDataThread(int startidx, int endidx, 
                                                   std::vector<vmath::vec3> *particles,
                                                   double radius,
                                                   BlockArray3d<float> *blockphi, 
                                                   GridCountData *countdata) {
    
    countdata->simpleGridIndices = std::vector<int>(endidx - startidx, -1);
    countdata->invalidPoints = std::vector<bool>(endidx - startidx, false);
    countdata->startidx = startidx;
    countdata->endidx = endidx;

    float sr = _searchRadiusFactor * (float)radius;
    float blockdx = _blockwidth * _dx;
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = particles->at(i);
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

void ParticleLevelSet::_sortParticlesIntoBlocks(std::vector<vmath::vec3> &particles,
                                                ParticleGridCountData &countdata, 
                                                std::vector<vmath::vec3> &sortedParticleData, 
                                                std::vector<int> &blockToParticleIndex) {

    blockToParticleIndex = std::vector<int>(countdata.gridsize, 0);
    int currentIndex = 0;
    for (size_t i = 0; i < blockToParticleIndex.size(); i++) {
        blockToParticleIndex[i] = currentIndex;
        currentIndex += countdata.totalGridCount[i];
    }
    std::vector<int> blockToParticleIndexCurrent = blockToParticleIndex;
    int totalParticleCount = currentIndex;

    sortedParticleData = std::vector<vmath::vec3>(totalParticleCount);
    for (int tidx = 0; tidx < countdata.numthreads; tidx++) {
        GridCountData *countData = &(countdata.threadGridCountData[tidx]);

        int indexOffset = countData->startidx;
        int currentOverlappingIndex = 0;
        for (size_t i = 0; i < countData->simpleGridIndices.size(); i++) {
            if (countData->invalidPoints[i]) {
                continue;
            }

            vmath::vec3 p = particles[i + indexOffset];
            if (countData->simpleGridIndices[i] >= 0) {
                int blockid = countData->simpleGridIndices[i];
                int sortedIndex = blockToParticleIndexCurrent[blockid];
                sortedParticleData[sortedIndex] = p;
                blockToParticleIndexCurrent[blockid]++;
            } else {
                int numblocks = -(countData->simpleGridIndices[i]);
                for (int blockidx = 0; blockidx < numblocks; blockidx++) {
                    int blockid = countData->overlappingGridIndices[currentOverlappingIndex];
                    currentOverlappingIndex++;

                    int sortedIndex = blockToParticleIndexCurrent[blockid];
                    sortedParticleData[sortedIndex] = p;
                    blockToParticleIndexCurrent[blockid]++;
                }
            }
        }
    }

}

void ParticleLevelSet::_computeExactBandProducerThread(BoundedBuffer<ComputeBlock> *computeBlockQueue,
                                                       BoundedBuffer<ComputeBlock> *finishedComputeBlockQueue) {
    while (computeBlockQueue->size() > 0) {
        std::vector<ComputeBlock> computeBlocks;
        int numBlocks = computeBlockQueue->pop(_numComputeBlocksPerJob, computeBlocks);
        if (numBlocks == 0) {
            continue;
        }

        for (size_t bidx = 0; bidx < computeBlocks.size(); bidx++) {
            ComputeBlock block = computeBlocks[bidx];
            float r = block.radius;
            float sr = _searchRadiusFactor * r;
            GridIndex blockIndex = block.gridBlock.index;
            vmath::vec3 blockPositionOffset = Grid3d::GridIndexToPosition(blockIndex, _blockwidth * _dx);

            for (int pidx = 0; pidx < block.numParticles; pidx++) {
                vmath::vec3 p = block.particleData[pidx];
                p -= blockPositionOffset;

                vmath::vec3 pmin(p.x - sr, p.y - sr, p.z - sr);
                vmath::vec3 pmax(p.x + sr, p.y + sr, p.z + sr);
                GridIndex gmin = Grid3d::positionToGridIndex(pmin, _dx);
                GridIndex gmax = Grid3d::positionToGridIndex(pmax, _dx);
                gmin.i = std::max(gmin.i, 0);
                gmin.j = std::max(gmin.j, 0);
                gmin.k = std::max(gmin.k, 0);
                gmax.i = std::min(gmax.i, _blockwidth - 1);
                gmax.j = std::min(gmax.j, _blockwidth - 1);
                gmax.k = std::min(gmax.k, _blockwidth - 1);

                for (int k = gmin.k; k <= gmax.k; k++) {
                    for (int j = gmin.j; j <= gmax.j; j++) {
                        for (int i = gmin.i; i <= gmax.i; i++) {
                            vmath::vec3 gpos = Grid3d::GridIndexToCellCenter(i, j, k, _dx);
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

void ParticleLevelSet::_initializeCurvatureGridScalarField(ScalarField &field) {
    int gridsize = (_isize + 1) * (_jsize + 1) * (_ksize + 1);
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleLevelSet::_initializeCurvatureGridScalarFieldThread, this,
                                 intervals[i], intervals[i + 1], &field);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void ParticleLevelSet::_initializeCurvatureGridScalarFieldThread(int startidx, int endidx, 
                                                                 ScalarField *field) {
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize + 1);
        field->setScalarFieldValue(g, -getDistanceAtNode(g));
    }
}

void ParticleLevelSet::_getValidCurvatureNodes(Array3d<float> &surfacePhi, 
                                               Array3d<bool> &validNodes) {

    float distUpperBound = (_curvatureGridExactBand - 1) * _dx;
    Array3d<bool> tempValid(_isize, _jsize, _ksize, false);

    float *rawphi = surfacePhi.getRawArray();
    int size = surfacePhi.getNumElements();
    for (int i = 0; i < size; i++) {
        if (std::abs(rawphi[i]) < distUpperBound) {
            tempValid.set(i, true);
        }
    }

    validNodes.fill(false);
    for (int k = 1; k < _ksize - 1; k++) {
        for (int j = 1; j < _jsize - 1; j++) {
            for (int i = 1; i < _isize - 1; i++) {
                if (!tempValid(i, j, k)) {
                    continue;
                }

                bool isValid = tempValid(i + 1, j, k) &&
                               tempValid(i - 1, j, k) &&
                               tempValid(i, j + 1, k) &&
                               tempValid(i, j - 1, k) &&
                               tempValid(i, j, k + 1) &&
                               tempValid(i, j, k - 1);
                if (isValid) {
                    validNodes.set(i, j, k, true);
                }
            }
        }
    }
}

float ParticleLevelSet::_getCurvature(int i, int j, int k, Array3d<float> &phi) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize + 1, _ksize + 1));
    
    // Alternate method for calculating curvature
    /*
    float center = phi(i, j, k);
    float left = 0.0f;
    float right = 0.0f;
    float down = 0.0f;
    float up = 0.0f;
    float back = 0.0f;
    float front = 0.0f;

    if (i > 0) {
        left = center - phi(i - 1, j, k);
    }
    if (i + 1 < _isize) {
        right = phi(i + 1, j, k) - center;
    }

    if (j > 0) {
        down = center - phi(i, j - 1, k);
    }
    if (j + 1 < _jsize) {
        up = phi(i, j + 1, k) - center;
    }

    if (k > 0) {
        back = center - phi(i, j, k - 1);
    }
    if (k + 1 < _ksize) {
        front = phi(i, j, k + 1) - center;
    }

    float numerator = (right - left + up - down + front - back) / (_dx * _dx);

    left = phi((i > 0) ? i - 1 : i, j, k);
    right = phi((i + 1 < _isize) ? i + 1 : i, j, k);
    down = phi(i, (j > 0) ? j - 1 : j, k);
    up = phi(i, (j + 1 < _jsize) ? j + 1 : j, k);
    back = phi(i, j, (k > 0) ? k - 1 : k);
    front = phi(i, j, (k + 1 < _ksize) ? k + 1 : k);

    float gradx = (right - left) / (2 * _dx);
    float grady = (up - down) / (2 * _dx);
    float gradz = (front - back) / (2 * _dx);

    float denominator = sqrt(gradx*gradx + grady*grady + gradz*gradz);
    float eps = 1e-9f;
    if (denominator < eps) {
        return 0.0f;
    }

    float curvature = (numerator / denominator);
    curvature = std::min(curvature, 1.0f / (float)_dx);
    curvature = std::max(curvature, -1.0f / (float)_dx);
    */
    
    if (Grid3d::isGridIndexOnBorder(i, j, k, _isize, _jsize, _ksize)) {
        return 0.0f;
    }

    float x = 0.5f * (phi(i + 1, j, k) - phi(i - 1, j, k));
    float y = 0.5f * (phi(i, j + 1, k) - phi(i, j - 1, k));
    float z = 0.5f * (phi(i, j, k + 1) - phi(i, j, k - 1));

    float xx = phi(i + 1, j, k) - 2.0f * phi(i, j, k) + phi(i - 1, j, k);
    float yy = phi(i, j + 1, k) - 2.0f * phi(i, j, k) + phi(i, j - 1, k);
    float zz = phi(i, j, k + 1) - 2.0f * phi(i, j, k) + phi(i, j, k - 1);

    float xy = 0.25f * (phi(i + 1, j + 1, k) - 
                        phi(i - 1, j + 1, k) - 
                        phi(i + 1, j - 1, k) + 
                        phi(i - 1, j - 1, k));

    float xz = 0.25f * (phi(i + 1, j, k + 1) - 
                        phi(i - 1, j, k + 1) - 
                        phi(i + 1, j, k - 1) + 
                        phi(i - 1, j, k - 1));

    float yz = 0.25f * (phi(i, j + 1, k + 1) - 
                        phi(i, j - 1, k + 1) - 
                        phi(i, j + 1, k - 1) + 
                        phi(i, j - 1, k - 1));

    float denominator = x*x + y*y + z*z;
    denominator = sqrt(denominator * denominator * denominator);

    float eps = 1e-9f;
    if (denominator < eps) {
        return 0.0f;
    }

    float curvature = ((xx * (y*y + z*z) + yy * (x*x + z*z) + zz * (x*x + y*y) -
                       2*xy*x*y - 2*xz*x*z - 2*yz*y*z) / denominator) / _dx;
    curvature = std::min(curvature, 1.0f / (float)_dx);
    curvature = std::max(curvature, -1.0f / (float)_dx);
    
    return curvature;
}