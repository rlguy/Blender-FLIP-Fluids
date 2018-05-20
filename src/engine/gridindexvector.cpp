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

#include "gridindexvector.h"

GridIndexVector::GridIndexVector() {
}

GridIndexVector::GridIndexVector(int i, int j, int k) : 
                                    width(i), height(j), depth(k) {
}

GridIndexVector::~GridIndexVector() {
}


GridIndex GridIndexVector::operator[](int i) {
    FLUIDSIM_ASSERT(i >= 0 && i < (int)_indices.size());
    return _getUnflattenedIndex(_indices[i]);
}

void GridIndexVector::insert(std::vector<GridIndex> &indices) {
    reserve(_indices.size() + indices.size());
    for (unsigned int i = 0; i < indices.size(); i++) {
        push_back(indices[i]);
    }
}

void GridIndexVector::insert(GridIndexVector &indices) {
    FLUIDSIM_ASSERT(width == indices.width && height == indices.height && depth == indices.depth);

    reserve(_indices.size() + indices.size());
    int maxidx = width*height*depth - 1;
    for (unsigned int i = 0; i < indices.size(); i++) {
        int flatidx = indices.getFlatIndex(i);
        FLUIDSIM_ASSERT(flatidx >= 0 && flatidx <= maxidx);
        _indices.push_back(flatidx);
    }
}

std::vector<GridIndex> GridIndexVector::getVector() {
    std::vector<GridIndex> vector;
    vector.reserve(size());
    
    for (unsigned int i = 0; i < size(); i++) {
        vector.push_back((*this)[i]);
    }

    return vector;
}

void GridIndexVector::getVector(std::vector<GridIndex> &vector) {
    vector.reserve(size());
    
    for (unsigned int i = 0; i < size(); i++) {
        vector.push_back((*this)[i]);
    }
}