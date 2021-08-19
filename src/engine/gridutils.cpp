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

#include "gridutils.h"

#include "grid3d.h"
#include "threadutils.h"

namespace GridUtils {

void extrapolateGrid(Array3d<float> *grid, Array3d<bool> *valid, int numLayers) {
    /*
    char UNKNOWN = 0x00;
    char WAITING = 0x01;
    char KNOWN = 0x02;
    char DONE = 0x03;
    */

    char UNKNOWN = 0x00;
    char KNOWN = 0x02;
    Array3d<char> status(grid->width, grid->height, grid->depth, UNKNOWN);

    int gridsize = grid->width * grid->height * grid->depth;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&_initializeStatusGridThread,
                                 intervals[i], intervals[i + 1], valid, &status);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    std::vector<std::vector<GridIndex> > threadResults(numthreads);
    std::vector<GridIndex> extrapolationCells;
    for (int layers = 0; layers < numLayers; layers++) {
        extrapolationCells.clear();
        for (size_t i = 0; i < threadResults.size(); i++) {
            threadResults[i].clear();
        }

        threads = std::vector<std::thread>(numthreads);
        for (int i = 0; i < numthreads; i++) {
            threads[i] = std::thread(&_findExtrapolationCells,
                                     intervals[i], intervals[i + 1], &status, &(threadResults[i]));
        }

        int cellcount = 0;
        for (int i = 0; i < numthreads; i++) {
            threads[i].join();
            cellcount += threadResults[i].size();
        }
        
        extrapolationCells.reserve(cellcount);
        for (size_t i = 0; i < threadResults.size(); i++) {
            extrapolationCells.insert(extrapolationCells.end(), threadResults[i].begin(), threadResults[i].end());
        }

        int extrapolationThreads = (int)fmin(numCPU, extrapolationCells.size());
        threads = std::vector<std::thread>(extrapolationThreads);
        std::vector<int> extrapolationIntervals = ThreadUtils::splitRangeIntoIntervals(0, extrapolationCells.size(), extrapolationThreads);
        for (int i = 0; i < extrapolationThreads; i++) {
            threads[i] = std::thread(&_extrapolateCellsThread,
                                     extrapolationIntervals[i], extrapolationIntervals[i + 1], 
                                     &extrapolationCells, &status, grid);
        }

        for (int i = 0; i < extrapolationThreads; i++) {
            threads[i].join();
        }

        if (layers != numLayers - 1) {
            status.set(extrapolationCells, KNOWN);
        }
    }
}

void _initializeStatusGridThread(int startidx, int endidx, Array3d<bool> *valid, Array3d<char> *status) {
    char KNOWN = 0x02;
    char DONE = 0x03;

    int isize = status->width;
    int jsize = status->height;
    int ksize = status->depth;
    char *rawstatus = status->getRawArray();
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        if (Grid3d::isGridIndexOnBorder(g, isize, jsize, ksize)) {
            rawstatus[idx] = DONE;
            continue;
        }

        if (valid->get(g)) {
            rawstatus[idx] = KNOWN;
        }
    }
}

void _findExtrapolationCells(int startidx, int endidx, Array3d<char> *status, std::vector<GridIndex> *cells) {
    char UNKNOWN = 0x00;
    char WAITING = 0x01;
    char KNOWN = 0x02;
    char DONE = 0x03;

    int isize = status->width;
    int jsize = status->height;

    char *rawstatus = status->getRawArray();
    for (int idx = startidx; idx < endidx; idx++) {
        if (rawstatus[idx] != KNOWN) { 
            continue; 
        }

        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        GridIndex n(g.i + 1, g.j, g.k);
        if (status->get(n) == UNKNOWN) {
            status->set(n, WAITING);
            cells->push_back(n);
        }

        n = GridIndex(g.i - 1, g.j, g.k);
        if (status->get(n) == UNKNOWN) {
            status->set(n, WAITING);
            cells->push_back(n);
        }

        n = GridIndex(g.i, g.j + 1, g.k);
        if (status->get(n) == UNKNOWN) {
            status->set(n, WAITING);
            cells->push_back(n);
        }

        n = GridIndex(g.i, g.j - 1, g.k);
        if (status->get(n) == UNKNOWN) {
            status->set(n, WAITING);
            cells->push_back(n);
        }

        n = GridIndex(g.i, g.j, g.k + 1);
        if (status->get(n) == UNKNOWN) {
            status->set(n, WAITING);
            cells->push_back(n);
        }

        n = GridIndex(g.i, g.j, g.k - 1);
        if (status->get(n) == UNKNOWN) {
            status->set(n, WAITING);
            cells->push_back(n);
        }

        rawstatus[idx] = DONE;
    }
}

void _extrapolateCellsThread(int startidx, int endidx, 
                             std::vector<GridIndex> *cells, 
                             Array3d<char> *status, 
                             Array3d<float> *grid) {
    char DONE = 0x03;

    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = cells->at(idx);
        float sum = 0.0f;
        int count = 0;

        GridIndex n(g.i + 1, g.j, g.k);
        if (status->get(n) == DONE) {
            sum += grid->get(n);
            count++;
        }

        n = GridIndex(g.i - 1, g.j, g.k);
        if (status->get(n) == DONE) {
            sum += grid->get(n);
            count++;
        }

        n = GridIndex(g.i, g.j + 1, g.k);
        if (status->get(n) == DONE) {
            sum += grid->get(n);
            count++;
        }

        n = GridIndex(g.i, g.j - 1, g.k);
        if (status->get(n) == DONE) {
            sum += grid->get(n);
            count++;
        }

        n = GridIndex(g.i, g.j, g.k + 1);
        if (status->get(n) == DONE) {
            sum += grid->get(n);
            count++;
        }

        n = GridIndex(g.i, g.j, g.k - 1);
        if (status->get(n) == DONE) {
            sum += grid->get(n);
            count++;
        }

        grid->set(g, sum /(float)count);
    }
}

void featherGrid6(Array3d<bool> *grid, int numthreads) {
    Array3d<bool> tempgrid = *grid;

    int gridsize = grid->width * grid->height * grid->depth;
    numthreads = (int)fmin(numthreads, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&_featherGrid6Thread, grid, &tempgrid, intervals[i], intervals[i + 1]);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void _featherGrid6Thread(Array3d<bool> *grid, Array3d<bool> *valid, int startidx, int endidx) {
    int isize = grid->width;
    int jsize = grid->height;
    GridIndex nbs[6];
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        if (!valid->get(g)) {
            continue;
        }

        Grid3d::getNeighbourGridIndices6(g, nbs);
        for (int nidx = 0; nidx < 6; nidx++) {
            if (grid->isIndexInRange(nbs[nidx])) {
                grid->set(nbs[nidx], true);
            }
        }
    }
}

void featherGrid26(Array3d<bool> *grid, int numthreads) {
    Array3d<bool> tempgrid = *grid;

    int gridsize = grid->width * grid->height * grid->depth;
    numthreads = (int)fmin(numthreads, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&_featherGrid26Thread, grid, &tempgrid, intervals[i], intervals[i + 1]);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void _featherGrid26Thread(Array3d<bool> *grid, Array3d<bool> *valid, int startidx, int endidx) {
    int isize = grid->width;
    int jsize = grid->height;
    GridIndex nbs[26];
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        if (!valid->get(g)) {
            continue;
        }

        Grid3d::getNeighbourGridIndices26(g, nbs);
        for (int nidx = 0; nidx < 26; nidx++) {
            if (grid->isIndexInRange(nbs[nidx])) {
                grid->set(nbs[nidx], true);
            }
        }
    }
}

}