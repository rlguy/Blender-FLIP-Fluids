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

#pragma once

#include "array3d.h"
#include "grid3d.h"
#include "threadutils.h"

namespace GridUtils {

    void _initializeStatusGridThread(int startidx, int endidx, Array3d<bool> *valid, Array3d<char> *status);
    void _findExtrapolationCells(int startidx, int endidx, Array3d<char> *status, std::vector<GridIndex> *cells);

    void featherGrid6(Array3d<bool> *grid, int numthreads);
    void _featherGrid6Thread(Array3d<bool> *grid, Array3d<bool> *valid, int startidx, int endidx);

    void featherGrid26(Array3d<bool> *grid, int numthreads);
    void _featherGrid26Thread(Array3d<bool> *grid, Array3d<bool> *valid, int startidx, int endidx);

    template <class T>
    void _extrapolateCellsThread(int startidx, int endidx, 
                                 std::vector<GridIndex> *cells, 
                                 Array3d<char> *status, 
                                 Array3d<T> *grid) {
        char DONE = 0x03;

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = cells->at(idx);
            T sum = T();
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

    template <class T>
    void extrapolateGrid(Array3d<T> *grid, Array3d<bool> *valid, int numLayers) {
        // char UNKNOWN = 0x00;
        // char WAITING = 0x01;
        // char KNOWN = 0x02;
        // char DONE = 0x03;

        char UNKNOWN = 0x00;
        char KNOWN = 0x02;
        Array3d<char> status(grid->width, grid->height, grid->depth, UNKNOWN);

        size_t voxelsPerThread = 100000;
        size_t gridsize = grid->width * grid->height * grid->depth;
        size_t recommendedThreads = (size_t)std::ceil((double)gridsize / (double)voxelsPerThread);
        size_t numCPU = ThreadUtils::getMaxThreadCount();
        size_t numthreads = (int)std::min(std::min(numCPU, recommendedThreads), gridsize);
        std::vector<std::thread> threads(numthreads);
        std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
        for (size_t i = 0; i < numthreads; i++) {
            threads[i] = std::thread(&_initializeStatusGridThread,
                                     intervals[i], intervals[i + 1], valid, &status);
        }

        for (size_t i = 0; i < numthreads; i++) {
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
            for (size_t i = 0; i < numthreads; i++) {
                threads[i] = std::thread(&_findExtrapolationCells,
                                         intervals[i], intervals[i + 1], &status, &(threadResults[i]));
            }

            int cellcount = 0;
            for (size_t i = 0; i < numthreads; i++) {
                threads[i].join();
                cellcount += threadResults[i].size();
            }
            
            extrapolationCells.reserve(cellcount);
            for (size_t i = 0; i < threadResults.size(); i++) {
                extrapolationCells.insert(extrapolationCells.end(), threadResults[i].begin(), threadResults[i].end());
            }

            size_t extrapolationThreads = (size_t)std::min(numthreads, extrapolationCells.size());
            threads = std::vector<std::thread>(extrapolationThreads);
            std::vector<int> extrapolationIntervals = ThreadUtils::splitRangeIntoIntervals(0, extrapolationCells.size(), extrapolationThreads);
            for (size_t i = 0; i < extrapolationThreads; i++) {
                threads[i] = std::thread(&_extrapolateCellsThread<T>,
                                         extrapolationIntervals[i], extrapolationIntervals[i + 1], 
                                         &extrapolationCells, &status, grid);
            }

            for (size_t i = 0; i < extrapolationThreads; i++) {
                threads[i].join();
            }

            if (layers != numLayers - 1) {
                status.set(extrapolationCells, KNOWN);
            }
        }
    }
}
