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

#ifndef FLUIDENGINE_FLUIDMATERIALGRID_H
#define FLUIDENGINE_FLUIDMATERIALGRID_H

#include "gridindexvector.h"
#include "subdividedarray3d.h"

enum class Material : char { 
    air   = 0x00, 
    fluid = 0x01, 
    solid = 0x02
};

class FluidMaterialGrid {

public:

    FluidMaterialGrid();
    FluidMaterialGrid(int i, int j, int k);
    ~FluidMaterialGrid();

    Material operator()(int i, int j, int k);
    Material operator()(GridIndex g);

    void fill(Material m);

    void set(int i, int j, int k, Material m);
    void set(GridIndex g, Material m);
    void set(GridIndexVector &cells, Material m);
    void setAir(int i, int j, int k);
    void setAir(GridIndex g);
    void setAir(GridIndexVector &cells);
    void setFluid(int i, int j, int k);
    void setFluid(GridIndex g);
    void setFluid(GridIndexVector &cells);
    void setSolid(int i, int j, int k);
    void setSolid(GridIndex g);
    void setSolid(GridIndexVector &cells);

    bool isCellAir(int i, int j, int k);
    bool isCellAir(GridIndex g);
    bool isCellFluid(int i, int j, int k);
    bool isCellFluid(GridIndex g);
    bool isCellSolid(int i, int j, int k);
    bool isCellSolid(GridIndex g);

    bool isFaceBorderingMaterialU(int i, int j, int k, Material m);
    bool isFaceBorderingMaterialU(GridIndex g, Material m);
    bool isFaceBorderingMaterialV(int i, int j, int k, Material m);
    bool isFaceBorderingMaterialV(GridIndex g, Material m);
    bool isFaceBorderingMaterialW(int i, int j, int k, Material m);
    bool isFaceBorderingMaterialW(GridIndex g, Material m);
    bool isFaceBorderingAirU(int i, int j, int k);
    bool isFaceBorderingAirU(GridIndex g);
    bool isFaceBorderingFluidU(int i, int j, int k);
    bool isFaceBorderingFluidU(GridIndex g);
    bool isFaceBorderingSolidU(int i, int j, int k);
    bool isFaceBorderingSolidU(GridIndex g);
    bool isFaceBorderingAirV(int i, int j, int k);
    bool isFaceBorderingAirV(GridIndex g);
    bool isFaceBorderingFluidV(int i, int j, int k);
    bool isFaceBorderingFluidV(GridIndex g);
    bool isFaceBorderingSolidV(int i, int j, int k);
    bool isFaceBorderingSolidV(GridIndex g);
    bool isFaceBorderingAirW(int i, int j, int k);
    bool isFaceBorderingAirW(GridIndex g);
    bool isFaceBorderingFluidW(int i, int j, int k);
    bool isFaceBorderingFluidW(GridIndex g);
    bool isFaceBorderingSolidW(int i, int j, int k);
    bool isFaceBorderingSolidW(GridIndex g);

    bool isCellNeighbouringMaterial(int i, int j, int k, Material m);
    bool isCellNeighbouringMaterial(GridIndex g, Material m);
    bool isCellNeighbouringAir(int i, int j, int k);
    bool isCellNeighbouringAir(GridIndex g);
    bool isCellNeighbouringFluid(int i, int j, int k);
    bool isCellNeighbouringFluid(GridIndex g);
    bool isCellNeighbouringSolid(int i, int j, int k);
    bool isCellNeighbouringSolid(GridIndex g);

    void setSubdivisionLevel(int n);
    int getSubdivisionLevel();

    int width = 0;
    int height = 0;
    int depth = 0;

private: 

    SubdividedArray3d<Material> _grid;


};

#endif
