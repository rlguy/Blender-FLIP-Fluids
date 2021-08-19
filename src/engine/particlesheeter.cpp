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

#include "particlesheeter.h"
#include "array3d.h"
#include "particlemaskgrid.h"
#include "grid3d.h"
#include "gridutils.h"
#include "interpolation.h"
#include "threadutils.h"


ParticleSheeter::ParticleSheeter() {
}

ParticleSheeter::~ParticleSheeter() {
}

void ParticleSheeter::generateSheetParticles(ParticleSheeterParameters params,
                                             std::vector<vmath::vec3> &generatedParticles) {
    _initializeParameters(params);
    
    Array3d<unsigned char> countGrid(_isize, _jsize, _ksize, (char)0);
    _getMarkerParticleCellCounts(countGrid);

    std::vector<vmath::vec3> sheetParticles;
    _identifySheetParticlesPhase1(countGrid, sheetParticles);

    Array3d<bool> sheetCells(_isize, _jsize, _ksize, false);
    _getSheetCells(sheetParticles, sheetCells);

    sheetParticles.clear();
    countGrid.fill(0);
    _identifySheetParticlesPhase2(sheetCells, countGrid, sheetParticles);

    if (sheetParticles.empty()) {
        return;
    }

    ParticleMaskGrid maskgrid(_isize, _jsize, _ksize, _dx);
    _initializeMaskGrid(maskgrid);

    std::vector<vmath::vec3> sheetSeedCandidates;
    _getSheetSeedCandidates(sheetCells, sheetSeedCandidates);

    SortedParticleData sheetParticleData;
    _sortSheetParticlesIntoGrid(sheetParticles, sheetParticleData);

    SortedParticleData sheetCandidateParticleData;
    _sortSheetSeedCandidateParticlesIntoGrid(sheetSeedCandidates, sheetCandidateParticleData);
    
    _selectSeedParticles(sheetCandidateParticleData, sheetParticleData, maskgrid, generatedParticles);
}

void ParticleSheeter::_initializeParameters(ParticleSheeterParameters params) {
   _particles = params.particles;
   _fluidSurfaceLevelSet = params.fluidSurfaceLevelSet;

   _isize = params.isize;
   _jsize = params.jsize;
   _ksize = params.ksize;
   _dx = params.dx;
   _sheetFillThreshold = params.sheetFillThreshold;
}

void ParticleSheeter::_getMarkerParticleCellCounts(Array3d<unsigned char> &countGrid) {
    std::vector<vmath::vec3> *positions;
    _particles->getAttributeValues("POSITION", positions);

    for (size_t i = 0; i < positions->size(); i++) {
        vmath::vec3 p = positions->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        if ((int)(countGrid(g)) == 255) {
            continue;
        }
        countGrid.add(g, (char)1);
    }
}

void ParticleSheeter::_identifySheetParticlesPhase1(Array3d<unsigned char> &countGrid, 
                                                    std::vector<vmath::vec3> &sheetParticles) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _particles->size());
    std::vector<std::vector<vmath::vec3> > threadResults(numthreads);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _particles->size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleSheeter::_identifySheetParticlesPhase1Thread, this,
                                 intervals[i], intervals[i + 1], &countGrid, &(threadResults[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
        sheetParticles.insert(sheetParticles.end(), threadResults[i].begin(), threadResults[i].end());
    }
}

void ParticleSheeter::_identifySheetParticlesPhase1Thread(int startidx, int endidx, 
                                                    Array3d<unsigned char> *countGrid, 
                                                    std::vector<vmath::vec3> *result) {
    float maxdepth = _maxSheetDepth * _dx;
    float depthTestDistance = _depthTestDistance * _dx;
    float depthTestStepDistance = _depthTestStepDistance * _dx;
    float eps = 1e-5;
    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);

    std::vector<vmath::vec3> *positions;
    _particles->getAttributeValues("POSITION", positions);

    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = positions->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        if ((int)(countGrid->get(g)) >= _maxParticlesPerCell) {
            // too dense to be a sheet that needs reseeding
            continue;
        }

        float phi = Interpolation::trilinearInterpolate(p - hdx, _dx, *_fluidSurfaceLevelSet);
        if (phi >= maxdepth || phi < -maxdepth) {
            // not near surface
            continue;
        }

        vmath::vec3 dir;
        Interpolation::trilinearInterpolateGradient(p - hdx, _dx, *_fluidSurfaceLevelSet, &dir);
        dir = -dir;
        if (vmath::length(dir) < eps) {
            // invalid gradient vector
            continue;
        }

        // If you travel inwards from the surface normal, does the depth increase?
        // If so, then the point is not part of a thin sheet
        dir = vmath::normalize(dir);
        int numSteps = (int)std::ceil(depthTestDistance / depthTestStepDistance);
        float currentPhi = phi;
        bool depthTestSuccess = false;
        for (int stepidx = 0; stepidx < numSteps; stepidx++) {
            vmath::vec3 nextp = p + stepidx * depthTestStepDistance * dir;
            float nextPhi = Interpolation::trilinearInterpolate(nextp - hdx, _dx, *_fluidSurfaceLevelSet);
            if (nextPhi > currentPhi || nextPhi >= 0.0f) {
                depthTestSuccess = true;
                break;
            }
            currentPhi = nextPhi;
        }

        if (!depthTestSuccess) {
            continue;
        }

        result->push_back(p);
    }
}

void ParticleSheeter::_getSheetCells(std::vector<vmath::vec3> &sheetParticles, 
                                     Array3d<bool> &sheetCells) {

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, sheetParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, sheetParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleSheeter::_getSheetCellsThread, this,
                                 intervals[i], intervals[i + 1], &sheetParticles, &sheetCells);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    GridUtils::featherGrid6(&sheetCells, ThreadUtils::getMaxThreadCount());
    GridUtils::featherGrid6(&sheetCells, ThreadUtils::getMaxThreadCount());

    int buffer = 3;
    for (int k = 0; k < sheetCells.depth; k++) {
        for (int j = 0; j < sheetCells.height; j++) {
            for (int i = 0; i < sheetCells.width; i++) {
                if (i < buffer || j < buffer || k < buffer || 
                        i >= sheetCells.width - buffer || 
                        j >= sheetCells.height - buffer || 
                        k >= sheetCells.depth - buffer) {
                    sheetCells.set(i, j, k, false);
                }
            }
        }
    }
}

void ParticleSheeter::_getSheetCellsThread(int startidx, int endidx,
                                           std::vector<vmath::vec3> *sheetParticles, 
                                           Array3d<bool> *sheetCells) {
    for (int i = startidx; i < endidx; i++) {
        GridIndex g = Grid3d::positionToGridIndex(sheetParticles->at(i), _dx);
        sheetCells->set(g, true);
    }
}

void ParticleSheeter::_identifySheetParticlesPhase2(Array3d<bool> &sheetCells,
                                                    Array3d<unsigned char> &countGrid, 
                                                    std::vector<vmath::vec3> &sheetParticles) {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _particles->size());
    std::vector<std::vector<vmath::vec3> > threadResults(numthreads);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _particles->size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleSheeter::_identifySheetParticlesPhase2Thread, this,
                                 intervals[i], intervals[i + 1], &sheetCells, &countGrid, &(threadResults[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    countGrid.fill((unsigned char)0);
    for (int i = 0; i < numthreads; i++) {
        for (size_t j = 0; j < threadResults[i].size(); j++) {
            vmath::vec3 p = threadResults[i][j];
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if ((int)(countGrid(g)) >= _maxSheetParticlesPerCell) {
                continue;
            }

            sheetParticles.push_back(p);
            countGrid.add(g, (char)1);
        }
    }
}

void ParticleSheeter::_identifySheetParticlesPhase2Thread(int startidx, int endidx, 
                                                          Array3d<bool> *sheetCells,
                                                          Array3d<unsigned char> *countGrid, 
                                                          std::vector<vmath::vec3> *result) {
    std::vector<vmath::vec3> *positions;
    _particles->getAttributeValues("POSITION", positions);

    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    float maxdepth = _maxSheetDepth * _dx;
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = positions->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        if (!sheetCells->get(g)) {
            continue;
        }

        if ((int)(countGrid->get(g)) >= _maxSheetParticlesPerCell) {
            continue;
        }

        float phi = Interpolation::trilinearInterpolate(p - hdx, _dx, *_fluidSurfaceLevelSet);
        if (phi >= maxdepth || phi < -maxdepth) {
            // not near surface
            continue;
        }

        result->push_back(p);

        // This is a threading race condition, but inaccuracies in the count will
        // be resolved in the method that spawns this thread
        countGrid->add(g, (char)1);
    }
}

void ParticleSheeter::_initializeMaskGrid(ParticleMaskGrid &maskgrid) {
    std::vector<vmath::vec3> *positions;
    _particles->getAttributeValues("POSITION", positions);

    for (size_t i = 0; i < positions->size(); i++) {
        maskgrid.addParticle(positions->at(i));
    }
}

void ParticleSheeter::_getSheetSeedCandidates(Array3d<bool> &sheetCells, 
                                              std::vector<vmath::vec3> &sheetSeedCandidates) {

    std::vector<GridIndex> sheetCellVector;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (sheetCells(i, j, k)) {
                    sheetCellVector.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, sheetCellVector.size());
    std::vector<std::vector<vmath::vec3> > threadResults(numthreads);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, sheetCellVector.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleSheeter::_getSheetSeedCandidatesThread, this,
                                 intervals[i], intervals[i + 1], &sheetCellVector, &(threadResults[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
        sheetSeedCandidates.insert(sheetSeedCandidates.end(), threadResults[i].begin(), threadResults[i].end());
    }

}

void ParticleSheeter::_getSheetSeedCandidatesThread(int startidx, int endidx, 
                                                   std::vector<GridIndex> *sheetCellVector,
                                                   std::vector<vmath::vec3> *result) {
    GridIndex indexOffsets[8] = {
        GridIndex(0, 0, 0),
        GridIndex(0, 0, 1),
        GridIndex(0, 1, 0),
        GridIndex(0, 1, 1),
        GridIndex(1, 0, 0),
        GridIndex(1, 0, 1),
        GridIndex(1, 1, 0),
        GridIndex(1, 1, 1)
    };

    float maxSeedDepth = _maxSheedSeedCandidateDepth * _dx;
    double subdx = 0.5 * _dx;
    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    for (int i = startidx; i < endidx; i++) {
        GridIndex cell = sheetCellVector->at(i);
        for (int gidx = 0; gidx < 8; gidx++) {
            GridIndex offset = indexOffsets[gidx];
            GridIndex subIndex(2*cell.i + offset.i, 
                               2*cell.j + offset.j, 
                               2*cell.k + offset.k);
            vmath::vec3 seed = Grid3d::GridIndexToCellCenter(subIndex, subdx);

            float phi = Interpolation::trilinearInterpolate(seed - hdx, _dx, *_fluidSurfaceLevelSet);
            if (phi >= 0.0f || phi < -maxSeedDepth) {
                continue;
            }

            result->push_back(seed);
        }
    }
}

void ParticleSheeter::_sortSheetParticlesIntoGrid(std::vector<vmath::vec3> &sheetParticles, 
                                                  SortedParticleData &sheetParticleData) {

    int spatialGridReduction = (int)std::ceil(_sheetSearchRadius);
    int sr = spatialGridReduction;
    sheetParticleData.particlesPerCell = sr * sr * sr * _maxSheetParticlesPerCell;

    sheetParticleData.dx = spatialGridReduction * _dx;
    sheetParticleData.isize = (int)std::ceil((float)_isize / (float)spatialGridReduction);
    sheetParticleData.jsize = (int)std::ceil((float)_jsize / (float)spatialGridReduction);
    sheetParticleData.ksize = (int)std::ceil((float)_ksize / (float)spatialGridReduction);

    _sortParticlesIntoGrid(sheetParticles, sheetParticleData);

}

void ParticleSheeter::_sortSheetSeedCandidateParticlesIntoGrid(std::vector<vmath::vec3> &candidateParticles, 
                                                               SortedParticleData &candidateParticleData) {
    int spatialGridReduction = (int)std::ceil(_sheetSearchRadius);
    int sr = spatialGridReduction;
    candidateParticleData.particlesPerCell = sr * sr * sr * _maxSheetSeedCandidatesPerCell;

    candidateParticleData.dx = spatialGridReduction * _dx;
    candidateParticleData.isize = (int)std::ceil((float)_isize / (float)spatialGridReduction);
    candidateParticleData.jsize = (int)std::ceil((float)_jsize / (float)spatialGridReduction);
    candidateParticleData.ksize = (int)std::ceil((float)_ksize / (float)spatialGridReduction);

    _sortParticlesIntoGrid(candidateParticles, candidateParticleData);
}

void ParticleSheeter::_sortParticlesIntoGrid(std::vector<vmath::vec3> &particles, 
                                             SortedParticleData &sortData) {

    _initializeSortDataValidCells(particles, sortData);

    sortData.particleData = std::vector<vmath::vec3>(sortData.numValidCells * sortData.particlesPerCell);
    sortData.dataOffsets  = Array3d<std::pair<int, int> >(
            sortData.isize, sortData.jsize, sortData.ksize, std::pair<int, int>(-1, -1)
            );

    int currentidx = 0;
    for (int k = 0; k < sortData.ksize; k++) {
        for (int j = 0; j < sortData.jsize; j++) {
            for (int i = 0; i < sortData.isize; i++) {
                if (sortData.validCells(i, j, k)) {
                    int dataidx = sortData.particlesPerCell * currentidx;
                    sortData.dataOffsets.set(i, j, k, std::pair<int, int>(dataidx, dataidx));
                    currentidx++;
                }
            }
        }
    }

    for (size_t i = 0; i < particles.size(); i++) {
        GridIndex g = Grid3d::positionToGridIndex(particles[i], sortData.dx);
        std::pair<int, int> offset = sortData.dataOffsets(g);
        sortData.particleData[offset.second] = particles[i];
        offset.second++;
        sortData.dataOffsets.set(g, offset);
    }
}

void ParticleSheeter::_initializeSortDataValidCells(std::vector<vmath::vec3> &particles, 
                                                    SortedParticleData &sortData) {
    sortData.validCells  = Array3d<bool>(
            sortData.isize, sortData.jsize, sortData.ksize, false
            );

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, particles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, particles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleSheeter::_initializeSortDataValidCellsThread, this,
                                 intervals[i], intervals[i + 1], &particles, &sortData);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    int numValidCells = 0;
    for (int k = 0; k < sortData.ksize; k++) {
        for (int j = 0; j < sortData.jsize; j++) {
            for (int i = 0; i < sortData.isize; i++) {
                if (sortData.validCells(i, j, k)) {
                    numValidCells++;
                }
            }
        }
    }

    sortData.numValidCells = numValidCells;
}

void ParticleSheeter::_initializeSortDataValidCellsThread(int startidx, int endidx, 
                                                          std::vector<vmath::vec3> *particles, 
                                                          SortedParticleData *sortData) {
    for (int i = startidx; i < endidx; i++) {
        GridIndex g = Grid3d::positionToGridIndex(particles->at(i), sortData->dx);
        sortData->validCells.set(g, true);
    }
}

void ParticleSheeter::_selectSeedParticles(SortedParticleData &sheetCandidateParticleData, 
                                           SortedParticleData &sheetParticleData,
                                           ParticleMaskGrid &maskgrid,
                                           std::vector<vmath::vec3> &generatedParticles) {

    std::vector<GridIndex> candidateCells;
    for (int k = 0; k < sheetCandidateParticleData.ksize; k++) {
        for (int j = 0; j < sheetCandidateParticleData.jsize; j++) {
            for (int i = 0; i < sheetCandidateParticleData.isize; i++) {
                if (sheetCandidateParticleData.validCells(i, j, k)) {
                    candidateCells.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, candidateCells.size());
    std::vector<std::vector<vmath::vec3> > threadResults(numthreads);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, candidateCells.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&ParticleSheeter::_selectSeedParticlesThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &candidateCells, &maskgrid, &sheetCandidateParticleData, &sheetParticleData, 
                                 &(threadResults[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
        generatedParticles.insert(generatedParticles.end(), threadResults[i].begin(), threadResults[i].end());
    }

}

void ParticleSheeter::_selectSeedParticlesThread(int startidx, int endidx,
                                                 std::vector<GridIndex> *candidateCells,
                                                 ParticleMaskGrid *maskgrid,
                                                 SortedParticleData *sheetCandidateParticleData,
                                                 SortedParticleData *sheetParticleData,
                                                 std::vector<vmath::vec3> *result) {

    float eps = 1e-5;
    float maxradius = _sheetSearchRadius * _dx;
    std::vector<vmath::vec3> candidateParticles;
    std::vector<vmath::vec3> neighbours;
    std::vector<vmath::vec3> nearestneighbours;
    for (int gidx = startidx; gidx < endidx; gidx++) {
        GridIndex candidateCell = candidateCells->at(gidx);

        neighbours.clear();
        for (int k = candidateCell.k - 1; k <= candidateCell.k + 1; k++) {
            for (int j = candidateCell.j - 1; j <= candidateCell.j + 1; j++) {
                for (int i = candidateCell.i - 1; i <= candidateCell.i + 1; i++) {
                    if (!sheetParticleData->dataOffsets.isIndexInRange(i, j, k)) {
                        continue;
                    }

                    std::pair<int, int> offset = sheetParticleData->dataOffsets(i, j, k);
                    if (offset.first == -1) {
                        continue;
                    }

                    for (int dataidx = offset.first; dataidx < offset.second; dataidx++) {
                        vmath::vec3 np = sheetParticleData->particleData[dataidx];
                        neighbours.push_back(sheetParticleData->particleData[dataidx]);
                    }
                }
            }
        }

        if (neighbours.size() < 3) {
            continue;
        }

        std::pair<int, int> candidateDataOffset = sheetCandidateParticleData->dataOffsets(candidateCell);
        candidateParticles.clear();
        for (int cdataidx = candidateDataOffset.first; cdataidx < candidateDataOffset.second; cdataidx++) {
            candidateParticles.push_back(sheetCandidateParticleData->particleData[cdataidx]);
        }

        for (size_t cidx = 0; cidx < candidateParticles.size(); cidx++) {
            vmath::vec3 p = candidateParticles[cidx];

            nearestneighbours.clear();
            for (size_t nidx = 0; nidx < neighbours.size(); nidx++) {
                vmath::vec3 np = neighbours[nidx];
                if (vmath::length(np - p) < maxradius) {
                    nearestneighbours.push_back(np);
                }
            }

            if (nearestneighbours.size() < 3) {
                continue;
            }

            vmath::vec3 centroid;
            for (size_t nidx = 0; nidx < nearestneighbours.size(); nidx++) {
                centroid += nearestneighbours[nidx];
            }
            centroid /= nearestneighbours.size();

            float len1 = 1e6;
            float len2 = 1e6;
            float len3 = 1e6;
            vmath::vec3 p1, p2, p3;
            for (size_t nidx = 0; nidx < nearestneighbours.size(); nidx++) {
                vmath::vec3 np = nearestneighbours[nidx];
                float len = vmath::length(np - p);
                if (len < len1) {
                    len3 = len2;
                    len2 = len1;
                    len1 = len;
                    p3 = p2;
                    p2 = p1;
                    p1 = np;
                } else if (len < len2) {
                    len3 = len2;
                    len2 = len;
                    p3 = p2;
                    p2 = np;
                } else if (len < len3) {
                    len3 = len;
                    p3 = np;
                }
            }

            vmath::vec3 vt1 = p2 - p1;
            vmath::vec3 vt2 = p3 - p1;
            vmath::vec3 cross = vmath::cross(vt1, vt2);
            if (vmath::length(vt1) < eps || vmath::length(vt2) < eps || vmath::length(cross) < eps) {
                continue;
            }

            vmath::vec3 normal = vmath::normalize(cross);
            float distance = -vmath::dot(normal, (p - p1));
            p = p + _projectionFactor * distance * normal;
            if (!Grid3d::isPositionInGrid(p, _dx, _isize, _jsize, _ksize) || maskgrid->isSubCellSet(p)) {
                continue;
            }

            vmath::vec3 cdir = centroid - p;
            if (vmath::length(cdir) < eps) {
                continue;
            }

            cdir = vmath::normalize(cdir);
            float mindot = 1.01f;
            for (size_t nidx = 0; nidx < nearestneighbours.size(); nidx++) {
                vmath::vec3 np = nearestneighbours[nidx];
                vmath::vec3 ndir = np - p;
                if (vmath::length(ndir) < eps) {
                    continue;
                }

                ndir = vmath::normalize(ndir);
                float dot = vmath::dot(cdir, ndir);
                if (dot < mindot) {
                    mindot = dot;
                }
            }

            if (mindot < _sheetFillThreshold) {
                result->push_back(p);
                maskgrid->addParticle(p);
            }
        }

    }
}