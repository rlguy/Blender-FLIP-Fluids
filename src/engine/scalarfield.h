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

#ifndef FLUIDENGINE_SCALARFIELD_H
#define FLUIDENGINE_SCALARFIELD_H

#include "vmath.h"
#include "array3d.h"

class FluidMaterialGrid;
class MeshLevelSet;
class GridIndexVector;

class ScalarField
{
public:
    ScalarField();
    ScalarField(int i, int j, int k, double dx);
    ~ScalarField();

    void getGridDimensions(int *i, int *j, int *k) { *i = _isize; *j = _jsize; *k = _ksize; }
    double getCellSize() { return _dx; }

    void clear();
    void fill(float val);
    void setPointRadius(double r);
    double getPointRadius();
    void setSurfaceThreshold(double t);
    double getSurfaceThreshold();
    void setMaxScalarFieldThreshold(double t);
    void setMaxScalarFieldThreshold();
    double getMaxScalarFieldThreshold();
    bool isMaxScalarFieldThresholdSet();
    void enableWeightField();
    bool isWeightFieldEnabled();
    void applyWeightField();
    void addPoint(vmath::vec3 pos, double radius);
    void addPoint(vmath::vec3 pos);
    void addPointValue(vmath::vec3 pos, double radius, double value);
    void addPointValue(vmath::vec3 pos, double value);
    void addCuboid(vmath::vec3 pos, double w, double h, double d);
    void addEllipsoid(vmath::vec3 p, vmath::mat3 G, double r);
    void addEllipsoid(vmath::vec3 p, vmath::mat3 G);
    void addEllipsoidValue(vmath::vec3 p, vmath::mat3 G, double r, double value);
    void addEllipsoidValue(vmath::vec3 p, vmath::mat3 G, double value);
    void setMaterialGrid(FluidMaterialGrid &matGrid);
    void setMaterialGrid(GridIndexVector &solidCells);
    void setSolidSDF(MeshLevelSet &solidSDF);
    void setSolidCells(GridIndexVector &solidCells);
    void getScalarField(Array3d<float> &field);
    double getScalarFieldValue(GridIndex g);
    double getScalarFieldValue(int i, int j, int k);
    double getScalarFieldValueAtCellCenter(GridIndex g);
    double getScalarFieldValueAtCellCenter(int i, int j, int k);
    void getSetScalarFieldValues(Array3d<bool> &field);
    bool isScalarFieldValueSet(GridIndex g);
    bool isScalarFieldValueSet(int i, int j, int k);
    double getRawScalarFieldValue(GridIndex g);
    double getRawScalarFieldValue(int i, int j, int k);
    bool isCellInsideSurface(int i, int j, int k);
    double getWeight(int i, int j, int k);
    double getWeight(GridIndex g);
    void getWeightField(Array3d<float> &field);
    void setScalarFieldValue(int i, int j, int k, double value);
    void setScalarFieldValue(GridIndex g, double value);
    void setCellFieldValues(int i, int j, int k, double value);
    void setCellFieldValues(GridIndex g, double value);
    void addScalarFieldValue(int i, int j, int k, double value);
    void addScalarFieldValue(GridIndex g, double value);
    void addCellFieldValues(int i, int j, int k, double value);
    void addCellFieldValues(GridIndex g, double value);
    double tricubicInterpolation(vmath::vec3 p);
    double trilinearInterpolation(vmath::vec3 p);
    void setOffset(vmath::vec3 offset);
    vmath::vec3 getOffset();
    bool isPointInside(vmath::vec3 p);

    Array3d<float>* getPointerToScalarField();
    Array3d<float>* getPointerToWeightField();

private:

    double _evaluateTricubicFieldFunctionForRadiusSquared(double rsq);

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    double _radius = 0.0;
    double _invRadius = 1.0;
    double _coef1 = 0.0;
    double _coef2 = 0.0;
    double _coef3 = 0.0;

    double _surfaceThreshold = 0.5;
    double _maxScalarFieldThreshold = 0.0;
    bool _isMaxScalarFieldThresholdSet = false;

    Array3d<float> _field;
    Array3d<bool> _isVertexSolid;
    Array3d<float> _weightField;
    Array3d<bool> _isVertexSet;

    bool _isWeightFieldEnabled = false;

    vmath::vec3 _gridOffset;
};

#endif
