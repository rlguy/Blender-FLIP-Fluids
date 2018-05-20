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

#ifndef FLUIDENGINE_ARRAY3D_H
#define FLUIDENGINE_ARRAY3D_H

#include <stdexcept>
#include <sstream>
#include <vector>

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
        if (idx > 2) {
            std::string msg = "Error: index out of range.\n";
            throw std::out_of_range(msg);
        }

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

        T val;
        for (int k = 0; k < depth; k++) {
            for (int j = 0; j < height; j++) {
                for (int i = 0; i < width; i++) {
                    val = obj._grid[_getFlatIndex(i, j, k)];
                    set(i, j, k, val);
                }
            }
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

        T val;
        for (int k = 0; k < depth; k++) {
            for (int j = 0; j < height; j++) {
                for (int i = 0; i < width; i++) {
                    val = rhs._grid[_getFlatIndex(i, j, k)];
                    set(i, j, k, val);
                }
            }
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
        for (int idx = 0; idx < width*height*depth; idx++) {
            _grid[idx] = value;
        }
    }

    T operator()(int i, int j, int k) {
        bool isInRange = _isIndexInRange(i, j, k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }

        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        return _grid[_getFlatIndex(i, j, k)];
    }

    T operator()(GridIndex g) {
        bool isInRange = _isIndexInRange(g.i, g.j, g.k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        return _grid[_getFlatIndex(g)];;
    }

    T operator()(int flatidx) {
        bool isInRange = flatidx >= 0 && flatidx < _numElements;
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "index: " + _toString(flatidx) + "\n";
            throw std::out_of_range(msg);
        }

        return _grid[flatidx];
    }

    T get(int i, int j, int k) {
        bool isInRange = _isIndexInRange(i, j, k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        return _grid[_getFlatIndex(i, j, k)];
    }

    T get(GridIndex g) {
        bool isInRange = _isIndexInRange(g.i, g.j, g.k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        return _grid[_getFlatIndex(g)];;
    }

    T get(int flatidx) {
        bool isInRange = flatidx >= 0 && flatidx < _numElements;
        if (!isInRange && _isOutOfRangeValueSet) {
            return _outOfRangeValue;
        }
        
        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "index: " + _toString(flatidx) + "\n";
            throw std::out_of_range(msg);
        }

        return _grid[flatidx];
    }

    void set(int i, int j, int k, T value) {
        if (!_isIndexInRange(i, j, k)) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        _grid[_getFlatIndex(i, j, k)] = value;
    }

    void set(GridIndex g, T value) {
        if (!_isIndexInRange(g)) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        _grid[_getFlatIndex(g)] = value;
    }

    void set(std::vector<GridIndex> &cells, T value) {
        for (unsigned int i = 0; i < cells.size(); i++) {
            set(cells[i], value);
        }
    }

    void set(int flatidx, T value) {
        if (!(flatidx >= 0 && flatidx < _numElements)) {
            std::string msg = "Error: index out of range.\n";
            msg += "index: " + _toString(flatidx) + "\n";
            throw std::out_of_range(msg);
        }

        _grid[flatidx] = value;
    }

    void add(int i, int j, int k, T value) {
        if (!_isIndexInRange(i, j, k)) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        _grid[_getFlatIndex(i, j, k)] += value;
    }

    void add(GridIndex g, T value) {
        if (!_isIndexInRange(g)) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        _grid[_getFlatIndex(g)] += value;
    }

    void add(int flatidx, T value) {
        if (!(flatidx >= 0 && flatidx < _numElements)) {
            std::string msg = "Error: index out of range.\n";
            msg += "index: " + _toString(flatidx) + "\n";
            throw std::out_of_range(msg);
        }

        _grid[flatidx] += value;
    }

    T *getPointer(int i, int j, int k) {
        bool isInRange = _isIndexInRange(i, j, k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return &_outOfRangeValue;
        }

        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        return &_grid[_getFlatIndex(i, j, k)];
    }

    T *getPointer(GridIndex g) {
        bool isInRange = _isIndexInRange(g.i, g.j, g.k);
        if (!isInRange && _isOutOfRangeValueSet) {
            return &_outOfRangeValue;
        }

        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        return &_grid[_getFlatIndex(g)];
    }

    T *getPointer(int flatidx) {
        bool isInRange = flatidx >= 0 && flatidx < _numElements;
        if (!isInRange && _isOutOfRangeValueSet) {
            return &_outOfRangeValue;
        }

        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "index: " + _toString(flatidx) + "\n";
            throw std::out_of_range(msg);
        }

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

    inline bool isIndexInRange(int i, int j, int k) {
        return i >= 0 && j >= 0 && k >= 0 && i < width && j < height && k < depth;
    }

    inline bool isIndexInRange(GridIndex g) {
        return g.i >= 0 && g.j >= 0 && g.k >= 0 && g.i < width && g.j < height && g.k < depth;
    }

    int width = 0;
    int height = 0;
    int depth = 0;

private:
    void _initializeGrid() {
        if (width < 0 || height < 0 || depth < 0) {
            std::string msg = "Error: dimensions cannot be negative.\n";
            msg += "width: " + _toString(width) + 
                   " height: " + _toString(height) + 
                   " depth: " + _toString(depth) + "\n";
            throw std::domain_error(msg);
        }

        _grid = new T[width*height*depth];
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
