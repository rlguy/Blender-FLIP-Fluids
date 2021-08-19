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

#include "fluidmaterialgrid.h"

#include "grid3d.h"

FluidMaterialGrid::FluidMaterialGrid() {
}

FluidMaterialGrid::FluidMaterialGrid(int i, int j, int k) : 
                                        width(i), height(j), depth(k),
                                        _grid(i, j, k, Material::air) {
    _grid.setOutOfRangeValue(Material::solid);
}

FluidMaterialGrid::~FluidMaterialGrid() {
}

Material FluidMaterialGrid::operator()(int i, int j, int k) {
    return _grid(i, j, k);
}

Material FluidMaterialGrid::operator()(GridIndex g) {
    return _grid(g);
}

void FluidMaterialGrid::fill(Material m) {
    _grid.fill(m);
}

void FluidMaterialGrid::set(int i, int j, int k, Material m) {
    _grid.set(i, j, k, m);
}

void FluidMaterialGrid::set(GridIndex g, Material m) {
    _grid.set(g, m);
}

void FluidMaterialGrid::set(GridIndexVector &cells, Material m) {
    _grid.set(cells, m);
}

void FluidMaterialGrid::setAir(int i, int j, int k) {
    set(i, j, k, Material::air);
}

void FluidMaterialGrid::setAir(GridIndex g) {
    set(g, Material::air);
}

void FluidMaterialGrid::setAir(GridIndexVector &cells) {
    set(cells, Material::air);
}

void FluidMaterialGrid::setFluid(int i, int j, int k) {
    set(i, j, k, Material::fluid);
}

void FluidMaterialGrid::setFluid(GridIndex g) {
    set(g, Material::fluid);
}

void FluidMaterialGrid::setFluid(GridIndexVector &cells) {
    set(cells, Material::fluid);
}

void FluidMaterialGrid::setSolid(int i, int j, int k) {
    set(i, j, k, Material::solid);
}

void FluidMaterialGrid::setSolid(GridIndex g) {
    set(g, Material::solid);
}

void FluidMaterialGrid::setSolid(GridIndexVector &cells) {
    set(cells, Material::solid);
}


bool FluidMaterialGrid::isCellAir(int i, int j, int k) {
    return _grid(i, j, k) == Material::air;
}

bool FluidMaterialGrid::isCellAir(GridIndex g) {
    return _grid(g) == Material::air;
}

bool FluidMaterialGrid::isCellFluid(int i, int j, int k) {
    return _grid(i, j, k) == Material::fluid;
}

bool FluidMaterialGrid::isCellFluid(GridIndex g) {
    return _grid(g) == Material::fluid;
}

bool FluidMaterialGrid::isCellSolid(int i, int j, int k) {
    return _grid(i, j, k) == Material::solid;
}

bool FluidMaterialGrid::isCellSolid(GridIndex g) {
    return _grid(g) == Material::solid;
}

bool FluidMaterialGrid::isFaceBorderingMaterialU(int i, int j, int k, Material m) {
    if (i == _grid.width) { return _grid(i - 1, j, k) == m; }
    else if (i > 0) { return _grid(i, j, k) == m || _grid(i - 1, j, k) == m; }
    else { return _grid(i, j, k) == m; }
}

bool FluidMaterialGrid::isFaceBorderingMaterialU(GridIndex g, Material m) {
    return isFaceBorderingMaterialU(g.i, g.j, g.k, m);
}

bool FluidMaterialGrid::isFaceBorderingMaterialV(int i, int j, int k, Material m) {
    if (j == _grid.height) { return _grid(i, j - 1, k) == m; }
    else if (j > 0) { return _grid(i, j, k) == m || _grid(i, j - 1, k) == m; }
    else { return _grid(i, j, k) == m; }
}

bool FluidMaterialGrid::isFaceBorderingMaterialV(GridIndex g, Material m) {
    return isFaceBorderingMaterialV(g.i, g.j, g.k, m);
}

bool FluidMaterialGrid::isFaceBorderingMaterialW(int i, int j, int k, Material m) {
    if (k == _grid.depth) { return _grid(i, j, k - 1) == m; }
    else if (k > 0) { return _grid(i, j, k) == m || _grid(i, j, k - 1) == m; }
    else { return _grid(i, j, k) == m; }
}

bool FluidMaterialGrid::isFaceBorderingMaterialW(GridIndex g, Material m) {
    return isFaceBorderingMaterialW(g.i, g.j, g.k, m);
}

bool FluidMaterialGrid::isFaceBorderingAirU(int i, int j, int k) {
    return isFaceBorderingMaterialU(i, j, k, Material::air);
}

bool FluidMaterialGrid::isFaceBorderingAirU(GridIndex g) {
    return isFaceBorderingMaterialU(g, Material::air);
}

bool FluidMaterialGrid::isFaceBorderingFluidU(int i, int j, int k) {
    return isFaceBorderingMaterialU(i, j, k, Material::fluid);
}

bool FluidMaterialGrid::isFaceBorderingFluidU(GridIndex g) {
    return isFaceBorderingMaterialU(g, Material::fluid);
}

bool FluidMaterialGrid::isFaceBorderingSolidU(int i, int j, int k) {
    return isFaceBorderingMaterialU(i, j, k, Material::solid);
}

bool FluidMaterialGrid::isFaceBorderingSolidU(GridIndex g) {
    return isFaceBorderingMaterialU(g, Material::solid);
}

bool FluidMaterialGrid::isFaceBorderingAirV(int i, int j, int k) {
    return isFaceBorderingMaterialV(i, j, k, Material::air);
}

bool FluidMaterialGrid::isFaceBorderingAirV(GridIndex g) {
    return isFaceBorderingMaterialV(g, Material::air);
}

bool FluidMaterialGrid::isFaceBorderingFluidV(int i, int j, int k) {
    return isFaceBorderingMaterialV(i, j, k, Material::fluid);
}

bool FluidMaterialGrid::isFaceBorderingFluidV(GridIndex g) {
    return isFaceBorderingMaterialV(g, Material::fluid);
}

bool FluidMaterialGrid::isFaceBorderingSolidV(int i, int j, int k) {
    return isFaceBorderingMaterialV(i, j, k, Material::solid);
}

bool FluidMaterialGrid::isFaceBorderingSolidV(GridIndex g) {
    return isFaceBorderingMaterialV(g, Material::solid);
}

bool FluidMaterialGrid::isFaceBorderingAirW(int i, int j, int k) {
    return isFaceBorderingMaterialW(i, j, k, Material::air);
}

bool FluidMaterialGrid::isFaceBorderingAirW(GridIndex g) {
    return isFaceBorderingMaterialW(g, Material::air);
}

bool FluidMaterialGrid::isFaceBorderingFluidW(int i, int j, int k) {
    return isFaceBorderingMaterialW(i, j, k, Material::fluid);
}

bool FluidMaterialGrid::isFaceBorderingFluidW(GridIndex g) {
    return isFaceBorderingMaterialW(g, Material::fluid);
}

bool FluidMaterialGrid::isFaceBorderingSolidW(int i, int j, int k) {
    return isFaceBorderingMaterialW(i, j, k, Material::solid);
}

bool FluidMaterialGrid::isFaceBorderingSolidW(GridIndex g) {
    return isFaceBorderingMaterialW(g, Material::solid);
}

bool FluidMaterialGrid::isCellNeighbouringMaterial(int i, int j, int k, Material m) {
    GridIndex nbs[26];
    Grid3d::getNeighbourGridIndices26(i, j, k, nbs);
    for (int i = 0; i < 26; i++) {
        if (_grid(nbs[i]) == m) {
            return true;
        }
    }

    return false;
}

bool FluidMaterialGrid::isCellNeighbouringMaterial(GridIndex g, Material m) {
    return isCellNeighbouringMaterial(g.i, g.j, g.k, m);
}

bool FluidMaterialGrid::isCellNeighbouringAir(int i, int j, int k) {
    return isCellNeighbouringMaterial(i, j, k, Material::air);
}

bool FluidMaterialGrid::isCellNeighbouringAir(GridIndex g) {
    return isCellNeighbouringMaterial(g, Material::air);
}

bool FluidMaterialGrid::isCellNeighbouringFluid(int i, int j, int k) {
    return isCellNeighbouringMaterial(i, j, k, Material::fluid);
}

bool FluidMaterialGrid::isCellNeighbouringFluid(GridIndex g) {
    return isCellNeighbouringMaterial(g, Material::fluid);
}

bool FluidMaterialGrid::isCellNeighbouringSolid(int i, int j, int k) {
    return isCellNeighbouringMaterial(i, j, k, Material::solid);
}

bool FluidMaterialGrid::isCellNeighbouringSolid(GridIndex g) {
    return isCellNeighbouringMaterial(g, Material::solid);
}

void FluidMaterialGrid::setSubdivisionLevel(int n) {
    _grid.setSubdivisionLevel(n);
    width  = _grid.width;
    height = _grid.height;
    depth  = _grid.depth;
}

int FluidMaterialGrid::getSubdivisionLevel() {
    return _grid.getSubdivisionLevel();
}
