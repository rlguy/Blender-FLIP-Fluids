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

#ifndef FLUIDENGINE_ARRAYVIEW3D_H
#define FLUIDENGINE_ARRAYVIEW3D_H

#include "array3d.h"

template <class T>
class ArrayView3d
{
public:

    ArrayView3d() {
        setDimensions(0, 0, 0);
        setOffset(0, 0, 0);
        setArray3d(&_dummyGrid);
    }

    ArrayView3d(Array3d<T> *grid) {
        setDimensions(0, 0, 0);
        setOffset(0, 0, 0);
        setArray3d(grid);
    }

    ArrayView3d(int isize, int jsize, int ksize, Array3d<T> *grid) {
        setDimensions(isize, jsize, ksize);
        setOffset(0, 0, 0);
        setArray3d(grid);
    }

    ArrayView3d(int isize, int jsize, int ksize, 
                int offi, int offj, int offk, Array3d<T> *grid) {
        setDimensions(isize, jsize, ksize);
        setOffset(offi, offj, offk);
        setArray3d(grid);
    }

    ArrayView3d(int isize, int jsize, int ksize, 
                GridIndex offset, Array3d<T> *grid) {
        setDimensions(isize, jsize, ksize);
        setOffset(offset);
        setArray3d(grid);
    }

    ArrayView3d(const ArrayView3d &obj) {
        width = obj.width;
        height = obj.height;
        depth = obj.depth;

        _ioffset = obj._ioffset;
        _joffset = obj._joffset;
        _koffset = obj._koffset;

        _dummyGrid = Array3d<T>();

        if (obj._parent == &obj._dummyGrid) {
            _parent = &_dummyGrid;
        } else {
            _parent = obj._parent;
        }
    }

    ArrayView3d operator=(const ArrayView3d &rhs) {
        width = rhs.width;
        height = rhs.height;
        depth = rhs.depth;

        _ioffset = rhs._ioffset;
        _joffset = rhs._joffset;
        _koffset = rhs._koffset;

        _dummyGrid = Array3d<T>();

        if (rhs._parent == &rhs._dummyGrid) {
            _parent = &_dummyGrid;
        } else {
            _parent = rhs._parent;
        }

        return *this;
    }

    ~ArrayView3d() {
    }

    void setDimensions(int isize, int jsize, int ksize) {
        if (!_isDimensionsValid(isize, jsize, ksize)) {
            std::string msg = "Error: dimensions cannot be negative.\n";
            msg += "width: " + _toString(isize) + 
                   " height: " + _toString(jsize) + 
                   " depth: " + _toString(ksize) + "\n";
            throw std::domain_error(msg);
        }

        width = isize;
        height = jsize;
        depth = ksize;
    }

    void getDimensions(int *isize, int *jsize, int *ksize) {
        *isize = width;
        *ksize = height;
        *jsize = depth;
    }

    GridIndex getDimensions() {
        return GridIndex(width, height, depth);
    }

    void setOffset(int offi, int offj, int offk) {
        _ioffset = offi;
        _joffset = offj;
        _koffset = offk;
    }

    void setOffset(GridIndex offset) {
        _ioffset = offset.i;
        _joffset = offset.j;
        _koffset = offset.k;
    }

    void getOffset(int *offi, int *offj, int *offk) {
        *offi = _ioffset;
        *offj = _joffset;
        *offk = _koffset;
    }

    GridIndex getOffset() {
        return GridIndex(_ioffset, _joffset, _koffset);
    }

    void setArray3d(Array3d<T> *grid) {
        _parent = grid;
    }

    Array3d<T> *getArray3d() {
        return _parent;
    }

    Array3d<T> getViewAsArray3d() {
        Array3d<T> view(width, height, depth);

        for (int k = 0; k < depth; k++) {
            for (int j = 0; j < height; j++) {
                for (int i = 0; i < width; i++) {
                    view.set(i, j, k, get(i, j, k));
                }
            }
        }

        return view;
    }

    void getViewAsArray3d(Array3d<T> &view) {
        if (!(view.width == width && view.height == height && view.depth = depth)) {
            std::string msg = "Error: array dimensions must be equal to view dimensions.\n";
            msg += "width: " + _toString(width) + 
                   " height: " + _toString(height) + 
                   " depth: " + _toString(depth) + "\n";
            throw std::domain_error(msg);
        }

        for (int k = 0; k < depth; k++) {
            for (int j = 0; j < height; j++) {
                for (int i = 0; i < width; i++) {
                    view.set(i, j, k, get(i, j, k));
                }
            }
        }

        return view;
    }

    void fill(T value) {
        for (int k = 0; k < depth; k++) {
            for (int j = 0; j < height; j++) {
                for (int i = 0; i < width; i++) {
                    set(i, j, k, value);
                }
            }
        }
    }

    T get(int i, int j, int k) {
        if (!_isIndexInView(i, j, k)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        GridIndex pidx = _viewToParentIndex(i, j, k);
        bool isInRange = _parent->isIndexInRange(pidx);
        if (!isInRange && _parent->isOutOfRangeValueSet()) {
            return _parent->getOutOfRangeValue();
        }

        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        return _parent->get(pidx);
    }

    T get(GridIndex g) {
        if (!_isIndexInView(g)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }
        
        GridIndex pidx = _viewToParentIndex(g);
        bool isInRange = _parent->isIndexInRange(pidx);
        if (!isInRange && _parent->isOutOfRangeValueSet()) {
            return _parent->getOutOfRangeValue();
        }
        
        if (!isInRange) {
            std::string msg = "Error: index out of range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        return _parent->get(pidx);   
    }

    T operator()(int i, int j, int k) {
        return get(i, j, k);
    }

    T operator()(GridIndex g) {
        return get(g);  
    }

    void set(int i, int j, int k, T value) {
        if (!_isIndexInView(i, j, k)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        GridIndex pidx = _viewToParentIndex(i, j, k);
        if (_parent->isIndexInRange(pidx)) {
            _parent->set(pidx, value);
        }
    }

    void set(GridIndex g, T value) {
        if (!_isIndexInView(g)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        GridIndex pidx = _viewToParentIndex(g);
        if (_parent->isIndexInRange(pidx)) {
            _parent->set(pidx, value);
        }
    }

    void set(std::vector<GridIndex> &cells, T value) {
        for (unsigned int i = 0; i < cells.size(); i++) {
            set(cells[i], value);
        }
    }

    void add(int i, int j, int k, T value) {
        if (!_isIndexInView(i, j, k)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }

        GridIndex pidx = _viewToParentIndex(i, j, k);
        if (_parent->isIndexInRange(pidx)) {
            _parent->add(pidx, value);
        }   
    }

    void add(GridIndex g, T value) {
       if (!_isIndexInView(g)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }

        GridIndex pidx = _viewToParentIndex(g);
        if (_parent->isIndexInRange(pidx)) {
            _parent->add(pidx, value);
        }   
    }

    T *getPointer(int i, int j, int k) {
        if (!_isIndexInView(i, j, k)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
            throw std::out_of_range(msg);
        }
        _parent->getPointer(_viewToParentIndex(i, j, k));
    }

    T *getPointer(GridIndex g) {
        if (!_isIndexInView(g)) {
            std::string msg = "Error: index out of view range.\n";
            msg += "i: " + _toString(g.i) + " j: " + _toString(g.j) + " k: " + _toString(g.k) + "\n";
            throw std::out_of_range(msg);
        }
        _parent->getPointer(_viewToParentIndex(g));
    }

    inline bool isIndexInView(int i, int j, int k) {
        return _isIndexInView(i, j, k);
    }

    inline bool isIndexInView(GridIndex g) {
        return _isIndexInView(g);
    }

    bool isIndexInParent(int i, int j, int k) {
        GridIndex pidx = _viewToParentIndex(i, j, k);
        return _parent->isIndexInRange(pidx);
    }

    bool isIndexInParent(GridIndex g) {
        GridIndex pidx = _viewToParentIndex(g);
        return _parent->isIndexInRange(pidx);
    }

    int width = 0;
    int height = 0;
    int depth = 0;

private:

    inline bool _isDimensionsValid(int isize, int jsize, int ksize) {
        return isize >= 0 && jsize >= 0 && ksize >= 0;
    }

    inline bool _isIndexInView(int i, int j, int k) {
        return i >= 0 && j >= 0 && k >= 0 && i < width && j < height && k < depth;
    }

    inline bool _isIndexInView(GridIndex g) {
        return g.i >= 0 && g.j >= 0 && g.k >= 0 && g.i < width && g.j < height && g.k < depth;
    }

    inline GridIndex _viewToParentIndex(int i, int j, int k) {
        return GridIndex(i + _ioffset, j + _joffset, k + _koffset);
    }

    inline GridIndex _viewToParentIndex(GridIndex g) {
        return GridIndex(g.i + _ioffset, g.j + _joffset, g.k + _koffset);
    }

    template<class S>
    std::string _toString(S item) {
        std::ostringstream sstream;
        sstream << item;

        return sstream.str();
    }

    int _ioffset = 0;
    int _joffset = 0;
    int _koffset = 0;

    Array3d<T> *_parent;
    Array3d<T> _dummyGrid;

};

#endif
