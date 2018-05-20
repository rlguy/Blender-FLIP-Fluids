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

#include "velocityadvector.h"

#include "macvelocityfield.h"
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
    _dx = _vfield->getGridCellSize();
    _chunkdx = _dx * _chunkWidth;
    _particleRadius = _dx * 1.01*sqrt(3.0)/2.0;

    _points.clear();
    _points.reserve(_particles->size());
    _velocities.clear();
    _velocities.reserve(_particles->size());
    for (size_t i = 0; i < _particles->size(); i++) {
        _points.push_back((*_particles)[i].position);
        _velocities.push_back((*_particles)[i].velocity);
    }
}

void VelocityAdvector::_advectGrid(Direction dir) {
    vmath::vec3 offset;
    int diridx = 0;
    int isize, jsize, ksize;
    _vfield->getGridDimensions(&isize, &jsize, &ksize);
    if (dir == Direction::U) {
        offset = vmath::vec3(0.0, 0.5*_dx, 0.5*_dx);
        diridx = 0;
        isize += 1;
    } else if (dir == Direction::V) {
        offset = vmath::vec3(0.5*_dx, 0.0, 0.5*_dx);
        diridx = 1;
        jsize += 1;
    } else if (dir == Direction::W) {
        offset = vmath::vec3(0.5*_dx, 0.5*_dx, 0.0);
        diridx = 2;
        ksize += 1;
    }

    int ichunks = (int)ceil((float)isize / (float)_chunkWidth);
    int jchunks = (int)ceil((float)jsize / (float)_chunkWidth);
    int kchunks = (int)ceil((float)ksize / (float)_chunkWidth);

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _particles->size());

    std::vector<CountGridData> countData(numthreads);
    for (int i = 0; i < numthreads; i++) {
        countData[i] = CountGridData(ichunks, jchunks, kchunks);
    }

    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _particles->size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&VelocityAdvector::_computeCountGridDataThread, this,
                                 intervals[i], intervals[i + 1], dir, &(countData[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    Array3d<int> countGrid(ichunks, jchunks, kchunks, 0);
    for (size_t dataidx = 0; dataidx < countData.size(); dataidx++) {
        for (int k = 0; k < kchunks; k++) {
            for (int j = 0; j < jchunks; j++) {
                for (int i = 0; i < ichunks; i++) {
                    countGrid.add(i, j, k, countData[dataidx].countGrid(i, j, k));
                }
            }
        }
    }

    Array3d<int> indexGrid(ichunks, jchunks, kchunks);
    int currentIndex = 0;
    for (int k = 0; k < kchunks; k++) {
        for (int j = 0; j < jchunks; j++) {
            for (int i = 0; i < ichunks; i++) {
                indexGrid.set(i, j, k, currentIndex);
                currentIndex += countGrid(i, j, k);
            }
        }
    }
    Array3d<int> currentIndexGrid = indexGrid;
    int totalCount = currentIndex;

    std::vector<PointData> sortedPoints(totalCount);
    for (size_t dataidx = 0; dataidx < countData.size(); dataidx++) {
        CountGridData *d = &(countData[dataidx]);

        int idxoffset = d->startidx;
        int currentOverlappingIndex = 0;
        for (size_t i = 0; i < d->simpleGridIndices.size(); i++) {
            vmath::vec3 p = _points[i + idxoffset] - offset;
            float vel = _velocities[i + idxoffset][diridx];
            PointData pd(p.x, p.y, p.z, vel);

            if (d->simpleGridIndices[i] >= 0) {
                int flatidx = d->simpleGridIndices[i];
                GridIndex g = Grid3d::getUnflattenedIndex(flatidx, ichunks, jchunks);
                int sortedidx = currentIndexGrid(g);
                sortedPoints[sortedidx] = pd;
                currentIndexGrid.add(g, 1);
            } else {
                int numcells = -(d->simpleGridIndices[i]);
                for (int cellidx = 0; cellidx < numcells; cellidx++) {
                    int flatidx = d->overlappingGridIndices[currentOverlappingIndex];
                    currentOverlappingIndex++;

                    GridIndex g = Grid3d::getUnflattenedIndex(flatidx, ichunks, jchunks);
                    int sortedidx = currentIndexGrid(g);
                    sortedPoints[sortedidx] = pd;
                    currentIndexGrid.add(g, 1);
                }
            }
        }
    }

    int numBlocks = 0;
    for (int k = 0; k < kchunks; k++) {
        for (int j = 0; j < jchunks; j++) {
            for (int i = 0; i < ichunks; i++) {
                if (countGrid(i, j, k) > 0) {
                    numBlocks++;
                }
            }
        }
    }

    int currentBlockIndex = 0;
    int floatsPerBlock = 2 * _chunkWidth * _chunkWidth * _chunkWidth;
    int weightOffset = _chunkWidth * _chunkWidth * _chunkWidth;
    std::vector<float> scalarData(numBlocks * floatsPerBlock, 0.0f);

    BoundedBuffer<BlockData> blockQueue(numBlocks);
    BoundedBuffer<BlockData> finishedBlockQueue(numBlocks);
    for (int k = 0; k < kchunks; k++) {
        for (int j = 0; j < jchunks; j++) {
            for (int i = 0; i < ichunks; i++) {
                if (countGrid(i, j, k) == 0) {
                    continue;
                }

                BlockData bd;
                bd.blockID = currentBlockIndex;
                bd.blockIndex = GridIndex(i, j, k);
                bd.pointData = &(sortedPoints[indexGrid(i, j, k)]);
                bd.numPoints = countGrid(i, j, k);
                bd.velocityData = &(scalarData[floatsPerBlock * bd.blockID]);
                bd.weightData = &(scalarData[floatsPerBlock * bd.blockID + weightOffset]);
                blockQueue.push(bd);

                currentBlockIndex++;
            }
        }
    }

    threads = std::vector<std::thread>(numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&VelocityAdvector::_advectionProducerThread, this,
                                 &blockQueue, &finishedBlockQueue, dir);
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

    int numBlocksProcessed = 0;
    int numvals = _chunkWidth * _chunkWidth * _chunkWidth;
    while (numBlocksProcessed < numBlocks) {
        std::vector<BlockData> finishedBlocks;
        finishedBlockQueue.popAll(finishedBlocks);
        for (size_t i = 0; i < finishedBlocks.size(); i++) {
            BlockData data = finishedBlocks[i];
            GridIndex gridOffset(data.blockIndex.i * _chunkWidth,
                                 data.blockIndex.j * _chunkWidth,
                                 data.blockIndex.k * _chunkWidth);

            float eps = 1e-6;
            for (int vidx = 0; vidx < numvals; vidx++) {
                GridIndex localidx = Grid3d::getUnflattenedIndex(vidx, _chunkWidth, _chunkWidth);
                GridIndex vfieldidx = GridIndex(localidx.i + gridOffset.i,
                                                localidx.j + gridOffset.j,
                                                localidx.k + gridOffset.k);
                if (vfieldgrid->isIndexInRange(vfieldidx)) {
                    vfieldgrid->set(vfieldidx, data.velocityData[vidx]);
                    if (data.weightData[vidx] > eps) {
                        validgrid->set(vfieldidx, true);
                    }
                }
            }
        }
        numBlocksProcessed += finishedBlocks.size();
    }

    blockQueue.notifyFinished();
    for (size_t i = 0; i < threads.size(); i++) {
        threads[i].join();
    }
}

void VelocityAdvector::_computeCountGridDataThread(int startidx, int endidx,
                                                   Direction dir, CountGridData *data) {
    vmath::vec3 offset;
    if (dir == Direction::U) {
        offset = vmath::vec3(0.0, 0.5*_dx, 0.5*_dx);
    } else if (dir == Direction::V) {
        offset = vmath::vec3(0.5*_dx, 0.0, 0.5*_dx);
    } else if (dir == Direction::W) {
        offset = vmath::vec3(0.5*_dx, 0.5*_dx, 0.0);
    }

    data->simpleGridIndices = std::vector<int>(endidx - startidx, -1);
    data->startidx = startidx;
    data->endidx = endidx;

    float r = (float)_particleRadius;
    float cdx = _chunkdx;
    int igridsize = data->countGrid.width;
    int jgridsize = data->countGrid.height;
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = _points[i] - offset;
        GridIndex g = Grid3d::positionToGridIndex(p, _chunkdx);

        vmath::vec3 gp = Grid3d::GridIndexToPosition(g, _chunkdx);
        if (p.x - r > gp.x && p.y - r > gp.y && p.z - r > gp.z && 
                p.x + r < gp.x + cdx && p.y + r < gp.y + cdx && p.z + r < gp.z + cdx) {
            data->simpleGridIndices[i - startidx] = Grid3d::getFlatIndex(g, igridsize, jgridsize);
            data->countGrid.add(g, 1);
        } else {
            GridIndex gmin = Grid3d::positionToGridIndex(p.x - r, p.y - r, p.z - r, _chunkdx);
            GridIndex gmax = Grid3d::positionToGridIndex(p.x + r, p.y + r, p.z + r, _chunkdx);

            int overlapCount = 0;
            for (int gk = gmin.k; gk <= gmax.k; gk++) {
                for (int gj = gmin.j; gj <= gmax.j; gj++) {
                    for (int gi = gmin.i; gi <= gmax.i; gi++) {
                        if (data->countGrid.isIndexInRange(gi, gj, gk)) {
                            data->countGrid.add(gi, gj, gk, 1);
                            overlapCount++;

                            int flatidx = Grid3d::getFlatIndex(gi, gj, gk, igridsize, jgridsize);
                            data->overlappingGridIndices.push_back(flatidx);
                        }
                    }
                }
            }

            data->simpleGridIndices[i - startidx] = -overlapCount;
        }
    }
}

void VelocityAdvector::_advectionProducerThread(BoundedBuffer<BlockData> *blockQueue, 
                                                BoundedBuffer<BlockData> *finishedBlockQueue, 
                                                Direction dir) {
    double r = _particleRadius;
    float rsq = r * r;
    float coef1 = (4.0f / 9.0f) * (1.0f / (r*r*r*r*r*r));
    float coef2 = (17.0f / 9.0f) * (1.0f / (r*r*r*r));
    float coef3 = (22.0f / 9.0f) * (1.0f / (r*r));

    while (blockQueue->size() > 0) {
        std::vector<BlockData> blocks;
        int numBlocks = blockQueue->pop(_numBlocksPerJob, blocks);
        if (numBlocks == 0) {
            continue;
        }

        for (size_t bidx = 0; bidx < blocks.size(); bidx++) {
            BlockData data = blocks[bidx];
            vmath::vec3 blockPositionOffset = Grid3d::GridIndexToPosition(data.blockIndex, _chunkdx);
            for (int pidx = 0; pidx < data.numPoints; pidx++) {
                PointData pd = *(data.pointData + pidx);
                vmath::vec3 p(pd.x, pd.y, pd.z);
                p -= blockPositionOffset;

                vmath::vec3 pmin(p.x - r, p.y - r, p.z - r);
                vmath::vec3 pmax(p.x + r, p.y + r, p.z + r);
                GridIndex gmin = Grid3d::positionToGridIndex(pmin, _dx);
                GridIndex gmax = Grid3d::positionToGridIndex(pmax, _dx);

                for (int k = gmin.k; k <= gmax.k; k++) {
                    for (int j = gmin.j; j <= gmax.j; j++) {
                        for (int i = gmin.i; i <= gmax.i; i++) {
                            if (i < 0 || j < 0 || k < 0 ||
                                    i >= _chunkWidth || j >= _chunkWidth || k >= _chunkWidth) {
                                continue;
                            }

                            vmath::vec3 gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                            vmath::vec3 v = gpos - p;
                            float d2 = vmath::dot(v, v);
                            if (d2 < rsq) {
                                float weight = 1.0f - coef1*d2*d2*d2 + coef2*d2*d2 - coef3*d2;

                                int flatidx = Grid3d::getFlatIndex(i, j, k, _chunkWidth, _chunkWidth);
                                data.velocityData[flatidx] += weight * pd.v;
                                data.weightData[flatidx] += weight;
                            }
                        }
                    }
                }
            }

            int numVals = _chunkWidth * _chunkWidth * _chunkWidth;
            float eps = 1e-6;
            for (int i = 0; i < numVals; i++) {
                if (data.weightData[i] > eps) {
                    data.velocityData[i] /= data.weightData[i];
                }
            }

            finishedBlockQueue->push(data);
        }
    }
}