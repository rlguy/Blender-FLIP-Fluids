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

#ifndef FLUIDENGINE_ARRAY3D_H
#define FLUIDENGINE_ARRAY3D_H

#include <stdexcept>
#include <sstream>
#include <vector>
#include <cmath>

struct GridIndex {
    int i, j, k;

    GridIndex() : i(0), j(0), k(0) {}
    GridIndex(int ii, int jj, int kk) : i(ii), j(jj), k(kk) {}

    bool operator==(const GridIndex &other) const { 
        return i == other.i &&
               j == other.j &&
               k == other.k;
    }

    bool operator!=(const GridIndex &other) const { 
        return i != other.i ||
               j != other.j ||
               k != other.k;
    }

    int& operator[](unsigned int idx) {

        #if defined(BUILD_DEBUG)
            if (idx > 2) {
                std::string msg = "Error: index out of range.\n";
                throw std::out_of_range(msg);
            }
        #endif

        return (&i)[idx];
    }
};

template <class T>
class Array3d
{
public:
    Array3d() {
        _initializeGrid();
    }

    Array3d(int i, int j, int k) : width(i), height(j), depth(k), _numElements(i*j*k) {
        _initializeGrid();
    }

    Array3d(int i, int j, int k, T fillValue) : width(i), height(j), depth(k), _numElements(i*j*k) {
        _initializeGrid();
        fill(fillValue);
    }

    Array3d(const Array3d &obj) {
        width = obj.width;
        height = obj.height;
        depth = obj.depth;
        _numElements = obj._numElements;

        _initializeGrid();

        for (int i = 0; i < _numElements; i++) {
            _grid[i] = obj._grid[i];
        }

        if (obj._isOutOfRangeValueSet) {
            _outOfRangeValue = obj._outOfRangeValue;
            _isOutOfRangeValueSet = true;
        }
    }

    Array3d operator=(const Array3d &rhs) {
        delete[] _grid;

        width = rhs.width;
        height = rhs.height;
        depth = rhs.depth;
        _numElements = rhs._numElements;

        _initializeGrid();

        for (int i = 0; i < _numElements; i++) {
            _grid[i] = rhs._grid[i];
        }

        if (rhs._isOutOfRangeValueSet) {
            _outOfRangeValue = rhs._outOfRangeValue;
            _isOutOfRangeValueSet = true;
        }

        return *this;
    }

    ~Array3d() {
        delete[] _grid;
    }

    void fill(T value) {
        for (int idx = 0; idx < _numElements; idx++) {
            _grid[idx] = value;
        }
    }

    bool isZero() {
        for (int idx = 0; idx < _numElements; idx++) {
            if (_grid[idx] != 0) {
                return false;
            }
        }
        return true;
    }

    bool isNonZero() {
        for (int idx = 0; idx < _numElements; idx++) {
            if (_grid[idx] != 0) {
                return true;
            }
        }
        return false;
    }

    T operator()(int i, int j, int k) {
        bool isInRange = _isIndexInRange(i, j, k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }

        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return _grid[_getFlatIndex(i, j, k)];
    }

    T operator()(GridIndex g) {
        bool isInRange = _isIndexInRange(g.i, g.j, g.k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return _grid[_getFlatIndex(g)];;
    }

    T operator()(int flatidx) {
        bool isInRange = flatidx >= 0 && flatidx < _numElements;
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "index: " + _toString(flatidx) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return _grid[flatidx];
    }

    T get(int i, int j, int k) {
        bool isInRange = _isIndexInRange(i, j, k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return _grid[_getFlatIndex(i, j, k)];
    }

    T get(GridIndex g) {
        bool isInRange = _isIndexInRange(g.i, g.j, g.k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return _grid[_getFlatIndex(g)];;
    }

    T get(int flatidx) {
        bool isInRange = flatidx >= 0 && flatidx < _numElements;
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "index: " + _toString(flatidx) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return _grid[flatidx];
    }

    void set(int i, int j, int k, T value) {
        #if defined(BUILD_DEBUG)
            if (!_isIndexInRange(i, j, k)) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        _grid[_getFlatIndex(i, j, k)] = value;
    }

    void set(GridIndex g, T value) {
        #if defined(BUILD_DEBUG)
            if (!_isIndexInRange(g)) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        _grid[_getFlatIndex(g)] = value;
    }

    void set(std::vector<GridIndex> &cells, T value) {
        for (unsigned int i = 0; i < cells.size(); i++) {
            set(cells[i], value);
        }
    }

    void set(int flatidx, T value) {
        #if defined(BUILD_DEBUG)
            if (!(flatidx >= 0 && flatidx < _numElements)) {
                std::string msg = "Error: index out of range.\n";
                msg += "index: " + _toString(flatidx) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        _grid[flatidx] = value;
    }

    void add(int i, int j, int k, T value) {
        #if defined(BUILD_DEBUG)
            if (!_isIndexInRange(i, j, k)) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        _grid[_getFlatIndex(i, j, k)] += value;
    }

    void add(GridIndex g, T value) {
        #if defined(BUILD_DEBUG)
            if (!_isIndexInRange(g)) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        _grid[_getFlatIndex(g)] += value;
    }

    void add(int flatidx, T value) {
        #if defined(BUILD_DEBUG)
            if (!(flatidx >= 0 && flatidx < _numElements)) {
                std::string msg = "Error: index out of range.\n";
                msg += "index: " + _toString(flatidx) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        _grid[flatidx] += value;
    }

    void negate() {
        for (int i = 0; i < _numElements; i++) {
            _grid[i] = -_grid[i];
        }
    }

    T *getPointer(int i, int j, int k) {
        bool isInRange = _isIndexInRange(i, j, k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return &_outOfRangeValue;
        }

        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return &_grid[_getFlatIndex(i, j, k)];
    }

    T *getPointer(GridIndex g) {
        bool isInRange = _isIndexInRange(g.i, g.j, g.k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return &_outOfRangeValue;
        }

        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return &_grid[_getFlatIndex(g)];
    }

    T *getPointer(int flatidx) {
        bool isInRange = flatidx >= 0 && flatidx < _numElements;
        if (!isInRange && _isOutOfRangeValueSet) {
            return &_outOfRangeValue;
        }

        #if defined(BUILD_DEBUG)
            if (!isInRange) {
                std::string msg = "Error: index out of range.\n";
                msg += "index: " + _toString(flatidx) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        return &_grid[flatidx];
    }

    T *getRawArray() {
        return _grid;
    }

    int getNumElements() {
        return _numElements;
    }

    void setOutOfRangeValue() {
        _isOutOfRangeValueSet = false;
    }
    void setOutOfRangeValue(T val) {
        _outOfRangeValue = val;
        _isOutOfRangeValueSet = true;
    }

    bool isOutOfRangeValueSet() {
        return _isOutOfRangeValueSet;
    }
    T getOutOfRangeValue() {
        return _outOfRangeValue;
    }

    bool isDimensionsValidForCoarseGridGeneration() {
        return width % 2 == 0 || height % 2 == 0 || depth % 2 == 0;
    }

    bool isDimensionsValidForCoarseFaceGridGenerationU() {
        return (width - 1) % 2 == 0 || height % 2 == 0 || depth % 2 == 0;
    }

    bool isDimensionsValidForCoarseFaceGridGenerationV() {
        return width % 2 == 0 || (height - 1) % 2 == 0 || depth % 2 == 0;
    }

    bool isDimensionsValidForCoarseFaceGridGenerationW() {
        return width % 2 == 0 || height % 2 == 0 || (depth - 1) % 2 == 0;
    }

    bool isMatchingDimensionsForCoarseGrid(Array3d<T> &coarseGrid) {
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseGridDimensions(&icoarse, &jcoarse, &kcoarse);
        return coarseGrid.width == icoarse && coarseGrid.height == jcoarse && coarseGrid.depth == kcoarse;
    }

    bool isMatchingDimensionsForCoarseFaceGridU(Array3d<T> &coarseGridU) {
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseFaceGridDimensionsU(&icoarse, &jcoarse, &kcoarse);
        return coarseGridU.width == icoarse && coarseGridU.height == jcoarse && coarseGridU.depth == kcoarse;
    }

    bool isMatchingDimensionsForCoarseFaceGridV(Array3d<T> &coarseGridV) {
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseFaceGridDimensionsV(&icoarse, &jcoarse, &kcoarse);
        return coarseGridV.width == icoarse && coarseGridV.height == jcoarse && coarseGridV.depth == kcoarse;
    }

    bool isMatchingDimensionsForCoarseFaceGridW(Array3d<T> &coarseGridW) {
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseFaceGridDimensionsW(&icoarse, &jcoarse, &kcoarse);
        return coarseGridW.width == icoarse && coarseGridW.height == jcoarse && coarseGridW.depth == kcoarse;
    }

    bool isMatchingDimensionsForFineGrid(Array3d<T> &fineGrid) {
        int ifine = 0; int jfine = 0; int kfine = 0;
        getFineGridDimensions(&ifine, &jfine, &kfine);
        return fineGrid.width == ifine && fineGrid.height == jfine && fineGrid.depth == kfine;
    }

    void getGridDimensions(int *i, int *j, int *k) {
        *i = width;
        *j = height;
        *k = depth;
    }

    void getCoarseGridDimensions(int *i, int *j, int *k) {
        *i = width / 2;
        *j = height / 2;
        *k = depth / 2;
    }

    void getCoarseFaceGridDimensionsU(int *i, int *j, int *k) {
        *i = ((width - 1) / 2) + 1;
        *j = height / 2;
        *k = depth / 2;
    }

    void getCoarseFaceGridDimensionsV(int *i, int *j, int *k) {
        *i = width / 2;
        *j = ((height - 1) / 2) + 1;
        *k = depth / 2;
    }

    void getCoarseFaceGridDimensionsW(int *i, int *j, int *k) {
        *i = width / 2;
        *j = height / 2;
        *k = ((depth - 1) / 2) + 1;
    }

    void getFineGridDimensions(int *i, int *j, int *k) {
        *i = width * 2;
        *j = height * 2;
        *k = depth * 2;
    }

    Array3d<T> generateCoarseGrid() {
        if (!isDimensionsValidForCoarseGridGeneration()) {
            std::string msg = "Error: coarse grid can only be generated from dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }
        
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseGridDimensions(&icoarse, &jcoarse, &kcoarse);

        Array3d<T> coarseGrid(icoarse, jcoarse, kcoarse);
        generateCoarseGrid(coarseGrid);
        return coarseGrid;
    }

    Array3d<T> generateCoarseFaceGridU() {
        if (!isDimensionsValidForCoarseFaceGridGenerationU()) {
            std::string msg = "Error: U coarse grid can only be generated from cell dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }
        
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseFaceGridDimensionsU(&icoarse, &jcoarse, &kcoarse);

        Array3d<T> coarseGridU(icoarse, jcoarse, kcoarse);
        generateCoarseFaceGridU(coarseGridU);
        return coarseGridU;
    }

    Array3d<T> generateCoarseFaceGridV() {
        if (!isDimensionsValidForCoarseFaceGridGenerationV()) {
            std::string msg = "Error: V coarse grid can only be generated from cell dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }
        
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseFaceGridDimensionsV(&icoarse, &jcoarse, &kcoarse);

        Array3d<T> coarseGridV(icoarse, jcoarse, kcoarse);
        generateCoarseFaceGridV(coarseGridV);
        return coarseGridV;
    }

    Array3d<T> generateCoarseFaceGridW() {
        if (!isDimensionsValidForCoarseFaceGridGenerationW()) {
            std::string msg = "Error: W coarse grid can only be generated from cell dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }
        
        int icoarse = 0; int jcoarse = 0; int kcoarse = 0;
        getCoarseFaceGridDimensionsW(&icoarse, &jcoarse, &kcoarse);

        Array3d<T> coarseGridW(icoarse, jcoarse, kcoarse);
        generateCoarseFaceGridW(coarseGridW);
        return coarseGridW;
    }

    Array3d<T> generateFineGrid() {
        int ifine = 0; int jfine = 0; int kfine = 0;
        getFineGridDimensions(&ifine, &jfine, &kfine);

        Array3d<T> fineGrid(ifine, jfine, kfine);
        generateFineGrid(fineGrid);
        return fineGrid;
    }

    void generateCoarseGrid(Array3d<T> &coarseGrid) {
        if (!isDimensionsValidForCoarseGridGeneration()) {
            std::string msg = "Error: coarse grid can only be generated from dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }

        if (!isMatchingDimensionsForCoarseGrid(coarseGrid)) {
            std::string msg = "Error: coarse grid dimensions must be the halved dimensions of this grid.\n";
            throw std::runtime_error(msg);
        }

        for (int k = 0; k < coarseGrid.depth; k++) {
            for (int j = 0; j < coarseGrid.height; j++) {
                for (int i = 0; i < coarseGrid.width; i++) {
                    
                    T sum = 0;
                    int neighbours = 0;
                    for (int nk = 2*k - 1; nk <= 2*k + 1; nk++) {
                        for (int nj = 2*j - 1; nj <= 2*j + 1; nj++) {
                            for (int ni = 2*i - 1; ni <= 2*i + 1; ni++) {
                                if (isIndexInRange(ni, nj, nk)) {
                                    sum += get(ni, nj, nk);
                                    neighbours++;
                                }
                            }
                        }
                    }
                    coarseGrid.set(i, j, k, sum / (T)neighbours);

                }
            }
        }
    }

    void generateCoarseFaceGridU(Array3d<T> &coarseGrid) {
        if (!isDimensionsValidForCoarseFaceGridGenerationU()) {
            std::string msg = "Error: U coarse grid can only be generated from cell dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }

        if (!isMatchingDimensionsForCoarseFaceGridU(coarseGrid)) {
            std::string msg = "Error: U coarse grid dimensions must be the halved cell dimensions of this grid.\n";
            throw std::runtime_error(msg);
        }

        for (int k = 0; k < coarseGrid.depth; k++) {
            for (int j = 0; j < coarseGrid.height; j++) {
                for (int i = 0; i < coarseGrid.width; i++) {
                    float ucoarse = 0.25f * (get(2*i, 2*j,     2*k) + 
                                             get(2*i, 2*j + 1, 2*k) + 
                                             get(2*i, 2*j + 1, 2*k + 1) + 
                                             get(2*i, 2*j,     2*k + 1));
                    coarseGrid.set(i, j, k, ucoarse);
                }
            }
        }
    }

    void generateCoarseFaceGridV(Array3d<T> &coarseGrid) {
        if (!isDimensionsValidForCoarseFaceGridGenerationU()) {
            std::string msg = "Error: V coarse grid can only be generated from cell dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }

        if (!isMatchingDimensionsForCoarseFaceGridV(coarseGrid)) {
            std::string msg = "Error: V coarse grid dimensions must be the halved cell dimensions of this grid.\n";
            throw std::runtime_error(msg);
        }

        for (int k = 0; k < coarseGrid.depth; k++) {
            for (int j = 0; j < coarseGrid.height; j++) {
                for (int i = 0; i < coarseGrid.width; i++) {
                    float vcoarse = 0.25f * (get(2*i,     2*j, 2*k) + 
                                             get(2*i + 1, 2*j, 2*k) + 
                                             get(2*i + 1, 2*j, 2*k + 1) + 
                                             get(2*i,     2*j, 2*k + 1));
                    coarseGrid.set(i, j, k, vcoarse);
                }
            }
        }
    }

    void generateCoarseFaceGridW(Array3d<T> &coarseGrid) {
        if (!isDimensionsValidForCoarseFaceGridGenerationW()) {
            std::string msg = "Error: W coarse grid can only be generated from cell dimensions divisible by 2.\n";
            throw std::runtime_error(msg);
        }

        if (!isMatchingDimensionsForCoarseFaceGridW(coarseGrid)) {
            std::string msg = "Error: W coarse grid dimensions must be the halved cell dimensions of this grid.\n";
            throw std::runtime_error(msg);
        }

        for (int k = 0; k < coarseGrid.depth; k++) {
            for (int j = 0; j < coarseGrid.height; j++) {
                for (int i = 0; i < coarseGrid.width; i++) {
                    float wcoarse = 0.25f * (get(2*i,     2*j,     2*k) + 
                                             get(2*i + 1, 2*j,     2*k) + 
                                             get(2*i + 1, 2*j + 1, 2*k) + 
                                             get(2*i,     2*j + 1, 2*k));
                    coarseGrid.set(i, j, k, wcoarse);
                }
            }
        }
    }

    void generateFineGrid(Array3d<T> &fineGrid) {
        if (!isMatchingDimensionsForFineGrid(fineGrid)) {
            std::string msg = "Error: fine grid dimensions must be the doubled dimensions of this grid.\n";
            throw std::runtime_error(msg);
        }

        for (int k = 0; k < fineGrid.depth; k++) {
            for (int j = 0; j < fineGrid.height; j++) {
                for (int i = 0; i < fineGrid.width; i++) {
                    T value = 0;
                    if (i % 2 == 0 && j % 2 == 0 && k % 2 == 0) {
                        value = get(i >> 1, j >> 1, k >> 1);
                    } else {
                        value = _trilinearInterpolate(0.5f * i, 0.5f * j, 0.5f * k);
                    }
                    fineGrid.set(i, j, k, value);
                }
            }
        }
    }

    inline bool isIndexInRange(int i, int j, int k) {
        return i >= 0 && j >= 0 && k >= 0 && i < width && j < height && k < depth;
    }

    inline bool isIndexInRange(GridIndex g) {
        return g.i >= 0 && g.j >= 0 && g.k >= 0 && g.i < width && g.j < height && g.k < depth;
    }

    int width = 1;
    int height = 1;
    int depth = 1;

private:
    void _initializeGrid() {
        #if defined(BUILD_DEBUG)
            if (width < 0 || height < 0 || depth < 0) {
                std::string msg = "Error: dimensions cannot be negative.\n";
                msg += "width: " + _toString(width) + 
                       " height: " + _toString(height) + 
                       " depth: " + _toString(depth) + "\n";
                throw std::domain_error(msg);
            }
        #endif

        _grid = new T[width*height*depth];
    }

    // vertices p are ordered {(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), 
    //                         (1, 0, 1), (0, 1, 1), (1, 1, 0), (1, 1, 1)}
    // x, y, z, in range [0,1]
    double _trilinearInterpolate(T p[8], float x, float y, float z) {
        return p[0] * (1 - x) * (1 - y) * (1 - z) +
               p[1] * x * (1 - y) * (1 - z) + 
               p[2] * (1 - x) * y * (1 - z) + 
               p[3] * (1 - x) * (1 - y) * z +
               p[4] * x * (1 - y) * z + 
               p[5] * (1 - x) * y * z + 
               p[6] * x * y * (1 - z) + 
               p[7] * x * y * z;
    }

    T _trilinearInterpolate(float px, float py, float pz) {
        double dx = 1.0;
        double inv_dx = 1.0;
        GridIndex g = GridIndex((int)std::floor(px),
                                (int)std::floor(py),
                                (int)std::floor(pz));
        float gx = g.i * dx;
        float gy = g.j * dx;
        float gz = g.k * dx;

        float ix = (px - gx) * inv_dx;
        float iy = (py - gy) * inv_dx;
        float iz = (pz - gz) * inv_dx;

        T points[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
        if (isIndexInRange(g.i,   g.j,   g.k))   { 
            points[0] = get(g.i,   g.j,   g.k); 
        }
        if (isIndexInRange(g.i+1, g.j,   g.k))   { 
            points[1] = get(g.i+1, g.j,   g.k); 
        }
        if (isIndexInRange(g.i,   g.j+1, g.k))   { 
            points[2] = get(g.i,   g.j+1, g.k); 
        }
        if (isIndexInRange(g.i,   g.j,   g.k+1)) {
            points[3] = get(g.i,   g.j,   g.k+1); 
        }
        if (isIndexInRange(g.i+1, g.j,   g.k+1)) { 
            points[4] = get(g.i+1, g.j,   g.k+1); 
        }
        if (isIndexInRange(g.i,   g.j+1, g.k+1)) { 
            points[5] = get(g.i,   g.j+1, g.k+1); 
        }
        if (isIndexInRange(g.i+1, g.j+1, g.k))   { 
            points[6] = get(g.i+1, g.j+1, g.k); 
        }
        if (isIndexInRange(g.i+1, g.j+1, g.k+1)) { 
            points[7] = get(g.i+1, g.j+1, g.k+1); 
        }

        return _trilinearInterpolate(points, ix, iy, iz);
    }

    inline bool _isIndexInRange(int i, int j, int k) {
        return i >= 0 && j >= 0 && k >= 0 && i < width && j < height && k < depth;
    }

    inline bool _isIndexInRange(GridIndex g) {
        return g.i >= 0 && g.j >= 0 && g.k >= 0 && g.i < width && g.j < height && g.k < depth;
    }

    inline unsigned int _getFlatIndex(int i, int j, int k) {
        return (unsigned int)i + (unsigned int)width *
               ((unsigned int)j + (unsigned int)height * (unsigned int)k);
    }

    inline unsigned int _getFlatIndex(GridIndex g) {
        return (unsigned int)g.i + (unsigned int)width *
               ((unsigned int)g.j + (unsigned int)height * (unsigned int)g.k);
    }

    template<class S>
    std::string _toString(S item) {
        std::ostringstream sstream;
        sstream << item;

        return sstream.str();
    }

    T *_grid;

    bool _isOutOfRangeValueSet = false;
    T _outOfRangeValue;
    int _numElements = 0;
};

#endif
