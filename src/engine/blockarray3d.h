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

#ifndef FLUIDENGINE_BLOCKARRAY3D_H
#define FLUIDENGINE_BLOCKARRAY3D_H

#include "array3d.h"
#include "grid3d.h"


struct BlockArray3dParameters {
    int isize = 0;
    int jsize = 0;
    int ksize = 0;
    int blockwidth = 1;
    std::vector<GridIndex> activeblocks;
};

struct Dims3d {
    Dims3d() {}
    Dims3d(int isize, int jsize, int ksize) : i(isize), j(jsize), k(ksize) {}

    int i = 0;
    int j = 0;
    int k = 0;
};

template <class T>
struct GridBlock {
    int id = -1;
    GridIndex index;
    T *data = NULL;
};

template <class T>
class BlockArray3d
{
public:
    BlockArray3d() {
    }

    BlockArray3d(BlockArray3dParameters &params) {
        _initialize(params);
    }

    static Dims3d getBlockDimensions(BlockArray3dParameters &params) {
        return Dims3d((params.isize + params.blockwidth - 1) / params.blockwidth,
                      (params.jsize + params.blockwidth - 1) / params.blockwidth,
                      (params.ksize + params.blockwidth - 1) / params.blockwidth);
    }

    void fill(T value) {
        std::fill(_arraydata.begin(), _arraydata.end(), value);
        setBackgroundValue(value);
    }

    void setBackgroundValue(T value) {
        _backgroundValue = value;
    }

    T getBackgroundValue() {
        return _backgroundValue;
    }

    T operator()(int i, int j, int k) {
        return get(i, j, k);
    }

    T operator()(GridIndex g) {
        return get(g.i, g.j, g.k);
    }

    T get(int i, int j, int k) {
        if (!_isIndexInRange(i, j, k)) {
            return _backgroundValue;
        }

        GridIndex bg = GridIndexToBlockIndex(i, j, k);
        int id = _blockDataGrid(bg).id;
        if (id == -1) {
            return _backgroundValue;
        }

        return _arraydata[_getDataOffset(bg, id, i, j, k)];
    }

    T get(GridIndex g) {
        return get(g.i, g.j, g.k);
    }

    void set(int i, int j, int k, T value) {
        if (!_isIndexInRange(i, j, k)) {
            return;
        }

        GridIndex bg = GridIndexToBlockIndex(i, j, k);
        int id = _blockDataGrid(bg).id;
        if (id == -1) {
            return;
        }

        _arraydata[_getDataOffset(bg, id, i, j, k)] = value;
    }

    void set(GridIndex g, T value) {
        set(g.i, g.j, g.k, value);
    }

    GridBlock<T> getGridBlock(int i, int j, int k) {
        #if defined(BUILD_DEBUG)
            if (!_isBlockIndexInRange(i, j, k)) {
                std::string msg = "Error: index out of range.\n";
                msg += "i: " + _toString(i) + " j: " + _toString(j) + " k: " + _toString(k) + "\n";
                throw std::out_of_range(msg);
            }
        #endif

        int id = _blockDataGrid(i, j, k).id;
        GridBlock<T> gb;
        gb.id = id;
        gb.index = GridIndex(i, j, k);
        if (id != -1) {
            gb.data = _arraydata.data() + id * _blocksize;
        }

        return gb;
    }

    GridBlock<T> getGridBlock(GridIndex g) {
        return getGridBlock(g.i, g.j, g.k);
    }

    void getActiveGridBlocks(std::vector<GridBlock<T> > &activeBlocks) {
        activeBlocks.reserve(getNumActiveGridBlocks());
        for (int k = 0; k < _blockDataGrid.depth; k++) {
            for (int j = 0; j < _blockDataGrid.height; j++) {
                for (int i = 0; i < _blockDataGrid.width; i++) {
                    int id = _blockDataGrid(i, j, k).id;
                    if (id == -1) {
                        continue;
                    }

                    GridBlock<T> gb;
                    gb.id = id;
                    gb.index = GridIndex(i, j, k);
                    gb.data = _arraydata.data() + id * _blocksize;
                    activeBlocks.push_back(gb);
                }
            }
        }
    }

    int getBlockID(int i, int j, int k) {
        if (!_isBlockIndexInRange(i, j, k)) {
            return -1;
        }
        return _blockDataGrid(i, j, k).id;
    }

    int getBlockID(GridIndex g) {
        return getBlockID(g.i, g.j, g.k);
    }

    GridIndex GridIndexToBlockIndex(int i, int j, int k) {
        return GridIndex(i / blockwidth, j / blockwidth, k / blockwidth);
    }

    GridIndex GridIndexToBlockIndex(GridIndex g) {
        return GridIndex(g.i / blockwidth, g.j / blockwidth, g.k / blockwidth);
    }

    int getNumActiveGridBlocks() {
        return _arraydata.size() / _blocksize;
    }

    int width = 0;
    int height = 0;
    int depth = 0;
    int blockwidth = 1;
    Dims3d blockdims;

private:

    struct BlockData {
        int id = -1;
    };

    void _initialize(BlockArray3dParameters params) {
        width = params.isize;
        height = params.jsize;
        depth = params.ksize;
        blockwidth = params.blockwidth;
        blockdims = getBlockDimensions(params);

        _blockDataGrid = Array3d<BlockData>(blockdims.i, blockdims.j, blockdims.k);
        Array3d<bool> activeGrid(blockdims.i, blockdims.j, blockdims.k, false);
        activeGrid.set(params.activeblocks, true);
        int idcounter = 0;
        for (int k = 0; k < activeGrid.depth; k++) {
            for (int j = 0; j < activeGrid.height; j++) {
                for (int i = 0; i < activeGrid.width; i++) {
                    if (activeGrid(i, j, k)) {
                        BlockData *bd = _blockDataGrid.getPointer(i, j, k);
                        bd->id = idcounter;
                        idcounter++;
                    }
                }
            }
        }

        _blocksize = blockwidth * blockwidth * blockwidth;
        _arraydata = std::vector<T>(_blocksize * idcounter);
        fill(T());
    }

    bool _isIndexInRange(int i, int j, int k) {
        return Grid3d::isGridIndexInRange(i, j, k, width, height, depth);
    }

    bool _isBlockIndexInRange(int i, int j, int k) {
        return Grid3d::isGridIndexInRange(i, j, k, blockdims.i, blockdims.j, blockdims.k);
    }

    int _getDataOffset(GridIndex blockIndex, int blockid, int i, int j, int k) {
        int bi = i - blockIndex.i * blockwidth;
        int bj = j - blockIndex.j * blockwidth;
        int bk = k - blockIndex.k * blockwidth;
        return _blocksize * blockid + bi + blockwidth * (bj + blockwidth * bk);
    }

    template<class S>
    std::string _toString(S item) {
        std::ostringstream sstream;
        sstream << item;

        return sstream.str();
    }


    int _blocksize = 1;
    T _backgroundValue;

    Array3d<BlockData> _blockDataGrid;
    std::vector<T> _arraydata;
};

#endif
