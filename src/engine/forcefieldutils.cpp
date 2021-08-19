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
    Fast sweeping method for propagating signed distance field adapted from 
    Robert Bridon's SDFGen makelevelset3.cpp:
        https://github.com/christopherbatty/SDFGen/blob/master/makelevelset3.cpp
*/

#include <chrono>

#include "forcefieldutils.h"
#include "collision.h"

namespace ForceFieldUtils {

int _bandwidth = 3;
float _sleepTimeFactor = 0.25;

void generateSurfaceVectorField(MeshLevelSet &sdf, TriangleMesh &mesh, Array3d<vmath::vec3> &vectorField) {
    Array3d<float> *phiptr = sdf.getPhiArray3d();
    int isize = phiptr->width;
    int jsize = phiptr->height;
    int ksize = phiptr->depth;
    double dx = sdf.getCellSize();
    float distUpperBound = (isize + jsize + ksize) * dx;

    sdf.fastCalculateSignedDistanceField(mesh, _bandwidth);

    VectorFieldGenerationData data;
    data.phi = Array3d<float>(isize, jsize, ksize, distUpperBound);
    data.closestPoint = Array3d<vmath::vec3>(isize, jsize, ksize);
    data.isClosestPointSet = Array3d<bool>(isize, jsize, ksize, false);
    data.dx = dx;

    float *phirawsrc = phiptr->getRawArray();
    float *phirawdst = data.phi.getRawArray();
    float maxdist = _bandwidth * dx;
    for (int i = 0; i < phiptr->getNumElements(); i++) {
        if (phirawsrc[i] <= maxdist) {
            phirawdst[i] = std::abs(phirawsrc[i]);
        }
    }

    _initializeNarrowBandClosestPoint(sdf, mesh, data);
    _fastSweepingMethod(data);

    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                vmath::vec3 gp = Grid3d::GridIndexToPosition(i, j, k, dx);
                vmath::vec3 cp = data.closestPoint(i, j, k);
                vectorField.set(i, j, k, cp - gp);
            }
        }
    }
}

void _initializeNarrowBandClosestPoint(MeshLevelSet &sdf, TriangleMesh &mesh, 
                                       VectorFieldGenerationData &data) {
    int isize = data.phi.width;
    int jsize = data.phi.height;
    int ksize = data.phi.depth;

    int gridsize = isize * jsize * ksize;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&_initializeNarrowBandClosestPointThread,
                                 intervals[i], intervals[i + 1], &sdf, &mesh, &data);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void _initializeNarrowBandClosestPointThread(int startidx, int endidx, 
                                             MeshLevelSet *sdf, TriangleMesh *mesh, 
                                             VectorFieldGenerationData *data) {

    int isize = data->phi.width;
    int jsize = data->phi.height;
    double dx = data->dx;
    float maxdist = _bandwidth * dx;

    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        if (data->phi.get(g) > maxdist) {
            continue;
        }

        int tidx = sdf->getClosestTriangleIndex(g);
        if (tidx == -1) {
            continue;
        }

        Triangle t = mesh->triangles[tidx];
        vmath::vec3 v1 = mesh->vertices[t.tri[0]];
        vmath::vec3 v2 = mesh->vertices[t.tri[1]];
        vmath::vec3 v3 = mesh->vertices[t.tri[2]];
        vmath::vec3 gp = Grid3d::GridIndexToPosition(g, dx);
        vmath::vec3 cp = Collision::findClosestPointOnTriangle(gp, v1, v2, v3);

        data->closestPoint.set(g, cp);
        data->isClosestPointSet.set(g, true);
    }
}

void _fastSweepingMethod(VectorFieldGenerationData &data) {
    Array3d<bool> isFrozen = data.isClosestPointSet;

    std::vector<GridIndex> gridDirections({
        GridIndex(+1, +1, +1),
        GridIndex(-1, -1, -1),
        GridIndex(+1, +1, -1),
        GridIndex(-1, -1, +1),
        GridIndex(+1, -1, +1),
        GridIndex(-1, +1, -1),
        GridIndex(+1, -1, -1),
        GridIndex(-1, +1, +1)
    });

    int sleeptime = std::cbrt(data.phi.getNumElements()) * _sleepTimeFactor;
    std::chrono::duration<int, std::milli> sleepdur = std::chrono::milliseconds(sleeptime);

    int numpasses = 1;
    for (int pass = 0; pass < numpasses; pass++) {
        int numthreads = 8;
        std::vector<std::thread> threads(numthreads);

        for (size_t tidx = 0; tidx < threads.size(); tidx++) {
            threads[tidx] = std::thread(&_sweepThread, &data, &isFrozen, gridDirections[tidx]);
            if ((int)tidx < numthreads - 1) {
                std::this_thread::sleep_for(sleepdur);
            }
        }

        for (size_t tidx = 0; tidx < threads.size(); tidx++) {
            threads[tidx].join();
        }
    }
}

void _sweepThread(VectorFieldGenerationData *data, Array3d<bool> *isFrozen, GridIndex sweepdir) {
    int isize = data->phi.width;
    int jsize = data->phi.height;
    int ksize = data->phi.depth;
    double dx = data->dx;
    GridIndex sd = sweepdir;

    int i0, i1;
    if (sd.i > 0) {
        i0 = 1; 
        i1 = isize; 
    } else { 
        i0 = isize - 2; 
        i1 = -1; 
    }

    int j0, j1;
    if (sd.j > 0) {
        j0 = 1;
        j1 = jsize; 
    } else {
        j0 = jsize - 2; 
        j1 = -1; 
    }

    int k0, k1;
    if (sd.k > 0) {
        k0 = 1;
        k1 = ksize;
    } else { 
        k0 = ksize - 2; 
        k1 = -1; 
    }

    for (int k = k0; k != k1; k += sd.k) { 
        for (int j = j0; j != j1; j += sd.j) { 
            for (int i = i0; i != i1; i += sd.i) {
                vmath::vec3 gx = Grid3d::GridIndexToPosition(i, j, k, dx);
                GridIndex g(i, j, k);
                _checkNeighbour(data, isFrozen, gx, g, i - sd.i, j       , k       );
                _checkNeighbour(data, isFrozen, gx, g, i       , j - sd.j, k       );
                _checkNeighbour(data, isFrozen, gx, g, i - sd.i, j - sd.j, k       );
                _checkNeighbour(data, isFrozen, gx, g, i       , j       , k - sd.k);
                _checkNeighbour(data, isFrozen, gx, g, i - sd.i, j       , k - sd.k);
                _checkNeighbour(data, isFrozen, gx, g, i       , j - sd.j, k - sd.k);
                _checkNeighbour(data, isFrozen, gx, g, i - sd.i, j - sd.j, k - sd.k);
            }
        }
    }
}

void _checkNeighbour(VectorFieldGenerationData *data, Array3d<bool> *isFrozen, 
                     vmath::vec3 gx, GridIndex g, int di, int dj, int dk) {

    if (isFrozen->get(g) || !data->isClosestPointSet(di, dj, dk)) {
        return;
    }

    vmath::vec3 p = data->closestPoint(di, dj, dk);
    float d = vmath::length(p - gx);
    if (d < data->phi(g)) {
        data->phi.set(g, d);
        data->closestPoint.set(g, p);
        data->isClosestPointSet.set(g, true);
    }
}

}