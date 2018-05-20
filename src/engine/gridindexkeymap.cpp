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

#include "gridindexkeymap.h"

#include "grid3d.h"

GridIndexKeyMap::GridIndexKeyMap() {
}

GridIndexKeyMap::GridIndexKeyMap(int i, int j, int k) : _isize(i), _jsize(j), _ksize(k) {
    _indices = std::vector<int>(i*j*k, _notFoundValue);
}

GridIndexKeyMap::~GridIndexKeyMap() {
}

void GridIndexKeyMap::clear() {
    for (unsigned int i = 0; i < _indices.size(); i++) {
        _indices[i] = _notFoundValue;
    }
}

void GridIndexKeyMap::insert(GridIndex g, int key) {
    insert(g.i, g.j, g.k, key);
}

void GridIndexKeyMap::insert(int i, int j, int k, int key) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));

    int flatidx = _getFlatIndex(i, j, k);
    _indices[flatidx] = key;
}

int GridIndexKeyMap::find(GridIndex g) {
    return find(g.i, g.j, g.k);
}

int GridIndexKeyMap::find(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));

    if (_indices.size() == 0) {
        return _notFoundValue;
    }

    int flatidx = _getFlatIndex(i, j, k);
    return _indices[flatidx];
}
