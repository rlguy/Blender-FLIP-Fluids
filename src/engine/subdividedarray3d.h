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

#ifndef FLUIDENGINE_SUBDIVIDEDARRAY3D_H
#define FLUIDENGINE_SUBDIVIDEDARRAY3D_H

template <class T>
class SubdividedArray3d
{
public:

    SubdividedArray3d() {
    }

    SubdividedArray3d(int i, int j, int k) : width(i), height(j), depth(k),
                                             _isize(i), _jsize(j), _ksize(k),
                                             _grid(i, j, k) {
    }

    SubdividedArray3d(int i, int j, int k, T fillValue) : width(i), height(j), depth(k),
                                                          _isize(i), _jsize(j), _ksize(k),
                                                          _grid(i, j, k, fillValue) {
    }

    ~SubdividedArray3d() {
    }

    void setSubdivisionLevel(int level) {
        if (level <= 0) {
            std::string msg = "Error: subdivision level must be greater than or equal to 1.\n";
            msg += "level: " + _toString(level) + "\n";
            throw std::domain_error(msg);
        }

        width  = level * _isize;
        height = level * _jsize;
        depth  = level * _ksize;

        _sublevel = level;
        _invsublevel = 1.0 / level;
    }

    int getSubdivisionLevel() {
        return _sublevel;
    }

    int getUnsubdividedWidth() { return _isize; }
    int getUnsubdividedHeight() { return _ksize; }
    int getUnsubdividedDepth() { return _jsize; }

    void getUnsubdividedDimensions(int *i, int *j, int *k) {
        *i = _isize; *j = _jsize; *k = _ksize;
    }

    void fill(T value) {
        _grid.fill(value);
    }

    T operator()(int i, int j, int k) {
        i = (int)(i * _invsublevel);
        j = (int)(j * _invsublevel);
        k = (int)(k * _invsublevel);

        return _grid(i, j, k);
    }

    T operator()(GridIndex g) {
        g.i = (int)(g.i * _invsublevel);
        g.j = (int)(g.j * _invsublevel);
        g.k = (int)(g.k * _invsublevel);

        return _grid(g);
    }

    T get(int i, int j, int k) {
        i = (int)(i * _invsublevel);
        j = (int)(j * _invsublevel);
        k = (int)(k * _invsublevel);

        return _grid(i, j, k);
    }

    T get(GridIndex g) {
        g.i = (int)(g.i * _invsublevel);
        g.j = (int)(g.j * _invsublevel);
        g.k = (int)(g.k * _invsublevel);

        return _grid(g);
    }

    void set(int i, int j, int k, T value) {
        _grid.set(i, j, k, value);
    }

    void set(GridIndex g, T value) {
        _grid.set(g, value);
    }

    void set(std::vector<GridIndex> &cells, T value) {
        for (unsigned int i = 0; i < cells.size(); i++) {
            _grid.set(cells[i], value);
        }
    }

    void set(GridIndexVector &cells, T value) {
        for (unsigned int i = 0; i < cells.size(); i++) {
            _grid.set(cells[i], value);
        }
    }

    void add(int i, int j, int k, T value) {
        _grid.add(i, j, k, value);
    }

    void add(GridIndex g, T value) {
        _grid.add(g, value);
    }

    T *getPointer(int i, int j, int k) {
        return _grid.getPointer(i, j, k);
    }

    T *getPointer(GridIndex g) {
        return _grid.getPointer(g);
    }

    T *getRawArray() {
        return _grid.getRawArray();
    }

    void setOutOfRangeValue() {
        _grid.setOutOfRangeValue();
    }

    void setOutOfRangeValue(T val) {
        _grid.setOutOfRangeValue(val);
    }

    bool isOutOfRangeValueSet() {
        return _grid.isOutOfRangeValueSet;
    }
    T getOutOfRangeValue() {
        return _grid.getOutOfRangeValue();
    }

    int width = 0;
    int height = 0;
    int depth = 0;

private:

    template<class S>
    std::string _toString(S item) {
        std::ostringstream sstream;
        sstream << item;

        return sstream.str();
    }

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;

    Array3d<T> _grid;
    unsigned int _sublevel = 1;
     double _invsublevel = 1;

};

#endif
