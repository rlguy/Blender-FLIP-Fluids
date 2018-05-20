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

#include "gridutils.h"

#include "grid3d.h"

namespace GridUtils {

void extrapolateGrid(Array3d<float> *grid, Array3d<bool> *valid, int numLayers) {
    char UNKNOWN = 0x00;
    char WAITING = 0x01;
    char KNOWN = 0x02;
    char DONE = 0x03;

    Array3d<char> status(grid->width, grid->height, grid->depth);
    for(int k = 0; k < grid->depth; k++) {
        for(int j = 0; j < grid->height; j++) {
            for(int i = 0; i < grid->width; i++) {
                status.set(i, j, k, valid->get(i, j, k) ? KNOWN : UNKNOWN);
                if (status(i, j, k) == UNKNOWN && 
                        Grid3d::isGridIndexOnBorder(i, j, k, grid->width, grid->height, grid->depth)) {
                    status.set(i, j, k, DONE);
                }
            }
        }
    }

    std::vector<GridIndex> extrapolationCells;
    for (int layers = 0; layers < numLayers; layers++) {

        extrapolationCells.clear();
        for(int k = 1; k < grid->depth - 1; k++) {
            for(int j = 1; j < grid->height - 1; j++) {
                for(int i = 1; i < grid->width - 1; i++) {
                    if (status(i, j, k) != KNOWN) { 
                        continue; 
                    }

                    int count = 0;
                    if (status(i - 1, j, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i - 1, j, k));
                        status.set(i - 1, j, k, WAITING);
                        count++;
                    } else if (status(i - 1, j, k) == WAITING) {
                        count++;
                    }

                    if (status(i + 1, j, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i + 1, j, k));
                        status.set(i + 1, j, k, WAITING);
                        count++;
                    } else if (status(i + 1, j, k) == WAITING) {
                        count++;
                    }

                    if (status(i, j - 1, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j - 1, k));
                        status.set(i, j - 1, k, WAITING);
                        count++;
                    } else if (status(i, j - 1, k) == WAITING) {
                        count++;
                    }

                    if (status(i, j + 1, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j + 1, k));
                        status.set(i, j + 1, k, WAITING);
                        count++;
                    } else if (status(i, j + 1, k) == WAITING) {
                        count++;
                    }

                    if (status(i, j, k - 1) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j, k - 1));
                        status.set(i, j, k - 1, WAITING);
                        count++;
                    } else if (status(i, j, k - 1) == WAITING) {
                        count++;
                    }

                    if (status(i, j, k + 1) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j, k + 1));
                        status.set(i, j, k + 1, WAITING);
                        count++;
                    } else if (status(i, j, k + 1) == WAITING) {
                        count++;
                    }

                    if (count == 0) {
                        status.set(i, j, k, DONE);
                    }
                }
            }
        }

        if (extrapolationCells.empty()) {
            return;
        }

        GridIndex g;
        for (size_t i = 0; i < extrapolationCells.size(); i++) {
            g = extrapolationCells[i];

            float sum = 0;
            int count = 0;
            if(status(g.i - 1, g.j, g.k) == KNOWN) { sum += grid->get(g.i - 1, g.j, g.k); count++; }
            if(status(g.i + 1, g.j, g.k) == KNOWN) { sum += grid->get(g.i + 1, g.j, g.k); count++; }
            if(status(g.i, g.j - 1, g.k) == KNOWN) { sum += grid->get(g.i, g.j - 1, g.k); count++; }
            if(status(g.i, g.j + 1, g.k) == KNOWN) { sum += grid->get(g.i, g.j + 1, g.k); count++; }
            if(status(g.i, g.j, g.k - 1) == KNOWN) { sum += grid->get(g.i, g.j, g.k - 1); count++; }
            if(status(g.i, g.j, g.k + 1) == KNOWN) { sum += grid->get(g.i, g.j, g.k + 1); count++; }

            FLUIDSIM_ASSERT(count != 0)
            grid->set(g, sum /(float)count);
        }
        status.set(extrapolationCells, KNOWN);

    }

}

}