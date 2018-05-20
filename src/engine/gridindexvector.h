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

#ifndef FLUIDENGINE_GRIDINDEXVECTOR_H
#define FLUIDENGINE_GRIDINDEXVECTOR_H

#include "fluidsimassert.h"
#include "array3d.h"

class GridIndexVector
{
public:
    GridIndexVector();
    GridIndexVector(int i, int j, int k);
    ~GridIndexVector();

    inline size_t size() {
        return _indices.size();
    }

    inline bool empty() {
        return _indices.empty();
    }

    inline void reserve(size_t n) {
        _indices.reserve(n);
    }

    inline void shrink_to_fit() {
        _indices.shrink_to_fit();
    }

    GridIndex operator[](int i);

    inline GridIndex at(int i) {
        FLUIDSIM_ASSERT(i >= 0 && i < (int)_indices.size());
        return _getUnflattenedIndex(_indices[i]);
    }

    inline GridIndex get(int i) {
        FLUIDSIM_ASSERT(i >= 0 && i < (int)_indices.size());
        return _getUnflattenedIndex(_indices[i]);
    }

    inline unsigned int getFlatIndex(int i) {
        FLUIDSIM_ASSERT(i >= 0 && i < (int)_indices.size());
        return _indices[i];
    }

    inline GridIndex front() {
        FLUIDSIM_ASSERT(!_indices.empty());
        return _getUnflattenedIndex(_indices.front());
    }

    inline GridIndex back() {
        FLUIDSIM_ASSERT(!_indices.empty());
        return _getUnflattenedIndex(_indices.back());
    }

    inline void push_back(GridIndex g) {
        FLUIDSIM_ASSERT(g.i >= 0 && g.j >= 0 && g.k >= 0 && g.i < width && g.j < height && g.k < depth);
        _indices.push_back(_getFlatIndex(g));
    }

    inline void push_back(int i, int j, int k) {
        FLUIDSIM_ASSERT(i >= 0 && j >= 0 && k >= 0 && i < width && j < height && k < depth);
        _indices.push_back(_getFlatIndex(i, j, k));
    }

    void insert(std::vector<GridIndex> &indices);
    void insert(GridIndexVector &indices);

    inline void pop_back() {
        FLUIDSIM_ASSERT(!_indices.empty());
        _indices.pop_back();
    }

    inline void clear() {
        _indices.clear();
    }

    std::vector<GridIndex> getVector();
    void getVector(std::vector<GridIndex> &vector);

    int width = 0;
    int height = 0;
    int depth = 0;

private:

    inline unsigned int _getFlatIndex(int i, int j, int k) {
        return (unsigned int)i + (unsigned int)width *
               ((unsigned int)j + (unsigned int)height * (unsigned int)k);
    }

    inline unsigned int _getFlatIndex(GridIndex g) {
        return (unsigned int)g.i + (unsigned int)width *
               ((unsigned int)g.j + (unsigned int)height * (unsigned int)g.k);
    }

    inline GridIndex _getUnflattenedIndex(unsigned int flatidx) {
        int i = flatidx % width;
        int j = (flatidx / width) % height;
        int k = flatidx / (width * height);

        return GridIndex(i, j, k);
    }

    std::vector<int> _indices;

};

#endif