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

#include "particlemaskgrid.h"

#include "grid3d.h"

ParticleMaskGrid::ParticleMaskGrid() {
}

ParticleMaskGrid::ParticleMaskGrid(int i, int j, int k, double dx) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), _subdx(0.5 * dx),
        _maskGrid(i, j, k, 0x00) {
}

ParticleMaskGrid::~ParticleMaskGrid() {
}


void ParticleMaskGrid::clear() {
    _maskGrid.fill(0x00);
}

unsigned char ParticleMaskGrid::operator()(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));
    return _maskGrid(i, j, k);
}

unsigned char ParticleMaskGrid::operator()(GridIndex g) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize));
    return _maskGrid(g);
}

void ParticleMaskGrid::addParticle(vmath::vec3 p) {
    FLUIDSIM_ASSERT(Grid3d::isPositionInGrid(p, _dx, _isize, _jsize, _ksize));

    unsigned char maskcase = 0x00;
    GridIndex subg = Grid3d::positionToGridIndex(p, _subdx);
    if (subg.i % 2 == 1) {
        maskcase |= 1;
    }
    if (subg.j % 2 == 1) {
        maskcase |= 2;
    }
    if (subg.k % 2 == 1) {
        maskcase |= 4;
    }
    unsigned char maskval = 1 << maskcase;

    GridIndex g = Grid3d::positionToGridIndex(p, _dx);
    _maskGrid.set(g, _maskGrid(g) | maskval);
}

void ParticleMaskGrid::addParticles(std::vector<vmath::vec3> &particles) {
    for (size_t i = 0; i < particles.size(); i++) {
        addParticle(particles[i]);
    }
}

bool ParticleMaskGrid::isSubCellSet(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, 2*_isize, 2*_jsize, 2*_ksize));

    unsigned char maskcase = 0x00;
    if (i % 2 == 1) {
        maskcase |= 1;
    }
    if (j % 2 == 1) {
        maskcase |= 2;
    }
    if (k % 2 == 1) {
        maskcase |= 4;
    }
    unsigned char maskval = 1 << maskcase;

    int gi = (int)(i / 2);
    int gj = (int)(j / 2);
    int gk = (int)(k / 2);

    return (_maskGrid(gi, gj, gk) & maskval) != 0;
}

bool ParticleMaskGrid::isSubCellSet(GridIndex g) {
    return isSubCellSet(g.i, g.j, g.k);
}

bool ParticleMaskGrid::isSubCellSet(vmath::vec3 p) {
    FLUIDSIM_ASSERT(Grid3d::isPositionInGrid(p, _dx, _isize, _jsize, _ksize));

    GridIndex g = Grid3d::positionToGridIndex(p, _subdx);
    return isSubCellSet(g.i, g.j, g.k);
}