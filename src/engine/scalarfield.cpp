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

#include "scalarfield.h"

#include "interpolation.h"
#include "fluidsimassert.h"
#include "grid3d.h"
#include "fluidmaterialgrid.h"
#include "meshlevelset.h"

ScalarField::ScalarField() {
}


ScalarField::ScalarField(int i, int j, int k, double dx) :
                                                       _isize(i), _jsize(j), _ksize(k), _dx(dx),
                                                       _field(i, j, k, 0.0),
                                                       _isVertexSolid(i, j, k, false),
                                                       _isVertexSet(i, j, k, false) {
}

ScalarField::~ScalarField() {
}

void ScalarField::clear() {
    _field.fill(0.0);
}

void ScalarField::fill(float val) {
    _field.fill(val);
}

void ScalarField::setPointRadius(double r) {
    _radius = r;
    _invRadius = 1 / r;
    _coef1 = (4.0 / 9.0)*(1.0 / (r*r*r*r*r*r));
    _coef2 = (17.0 / 9.0)*(1.0 / (r*r*r*r));
    _coef3 = (22.0 / 9.0)*(1.0 / (r*r));
}

double ScalarField::getPointRadius() {
    return _radius;
}

void ScalarField::setSurfaceThreshold(double t) { 
    _surfaceThreshold = t; 
}

double ScalarField::getSurfaceThreshold() { 
    return _surfaceThreshold; 
}

void ScalarField::setMaxScalarFieldThreshold(double t) { 
    _isMaxScalarFieldThresholdSet = true;
    _maxScalarFieldThreshold = t; 
}

void ScalarField::setMaxScalarFieldThreshold() { 
    _isMaxScalarFieldThresholdSet = false;
}

double ScalarField::getMaxScalarFieldThreshold() { 
    return _maxScalarFieldThreshold; 
}

bool ScalarField::isMaxScalarFieldThresholdSet() {
    return _isMaxScalarFieldThresholdSet;
}

void ScalarField::enableWeightField() {
    if (_isWeightFieldEnabled) {
        return;
    }

    _weightField = Array3d<float>(_isize, _jsize, _ksize, 0.0f);
    _isWeightFieldEnabled = true;
}

bool ScalarField::isWeightFieldEnabled() {
    return _isWeightFieldEnabled;
}

void ScalarField::applyWeightField() {
    if (!_isWeightFieldEnabled) {
        return;
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                float weight = _weightField(i, j, k);
                if (weight > 0.0) {
                    float v = _field(i, j, k) / weight;
                    setScalarFieldValue(i, j, k, v);
                }
            }
        }
    }
}

double ScalarField::getWeight(GridIndex g) {
    return getWeight(g.i, g.j, g.k);
}

double ScalarField::getWeight(int i, int j, int k) {
    if (!_isWeightFieldEnabled) {
        return 0.0;
    }

    FLUIDSIM_ASSERT(_weightField.isIndexInRange(i, j, k));
    return _weightField(i, j, k);
}

void ScalarField::addPoint(vmath::vec3 p, double r) {
    setPointRadius(r);
    addPoint(p);
}

void ScalarField::addPoint(vmath::vec3 p) {
    p -= _gridOffset;

    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, _radius, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    vmath::vec3 gpos;
    vmath::vec3 v;
    double rsq = _radius*_radius;
    double distsq;
    double weight;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {

                if (_isMaxScalarFieldThresholdSet && _field(i, j, k) > _maxScalarFieldThreshold) {
                    continue;
                }

                gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                v = gpos - p;
                distsq = vmath::dot(v, v);
                if (distsq < rsq) {
                    weight = _evaluateTricubicFieldFunctionForRadiusSquared(distsq);
                    addScalarFieldValue(i, j, k, weight);

                    if (_isWeightFieldEnabled) {
                        _weightField.add(i, j, k, (float)weight);
                    }
                }
            }
        }
    }

}

void ScalarField::addPointValue(vmath::vec3 p, double r, double value) {
    setPointRadius(r);
    addPointValue(p, value);
}

void ScalarField::addPointValue(vmath::vec3 p, double scale) {
    p -= _gridOffset;

    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, _radius, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    vmath::vec3 gpos;
    vmath::vec3 v;
    double rsq = _radius*_radius;
    double distsq;
    double weight;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {

                if (_isMaxScalarFieldThresholdSet && _field(i, j, k) > _maxScalarFieldThreshold) {
                    continue;
                }

                gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                v = gpos - p;
                distsq = vmath::dot(v, v);
                if (distsq < rsq) {
                    weight = _evaluateTricubicFieldFunctionForRadiusSquared(distsq);
                    addScalarFieldValue(i, j, k, weight*scale);

                    if (_isWeightFieldEnabled) {
                        _weightField.add(i, j, k, (float)weight);
                    }
                }
            }
        }
    }

}

void ScalarField::addCuboid(vmath::vec3 pos, double w, double h, double d) {
    pos -= _gridOffset;

    GridIndex gmin, gmax;
    AABB bbox = AABB(pos, w, h, d);
    Grid3d::getGridIndexBounds(bbox, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    double eps = 10e-6;
    vmath::vec3 gpos;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {

                if (_isMaxScalarFieldThresholdSet && _field(i, j, k) > _maxScalarFieldThreshold) {
                    continue;
                }

                gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                if (bbox.isPointInside(gpos)) {
                    addScalarFieldValue(i, j, k, _surfaceThreshold + eps);

                    if (_isWeightFieldEnabled) {
                        _weightField.add(i, j, k, (float)(_surfaceThreshold + eps));
                    }
                }
            }
        }
    }
}

void ScalarField::addEllipsoid(vmath::vec3 p, vmath::mat3 G, double r) {
    setPointRadius(r);
    addEllipsoid(p, G);
}

void ScalarField::addEllipsoid(vmath::vec3 p, vmath::mat3 G) {
    p -= _gridOffset;

    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, _radius, G, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    vmath::vec3 gpos;
    vmath::vec3 v;
    double rsq = _radius*_radius;
    double distsq;
    double weight;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {

                if (_isMaxScalarFieldThresholdSet && _field(i, j, k) > _maxScalarFieldThreshold) {
                    continue;
                }

                gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                v = (gpos - p);
                v = G*v;

                distsq = vmath::dot(v, v);

                if (distsq < rsq) {
                    weight = _evaluateTricubicFieldFunctionForRadiusSquared(distsq);
                    addScalarFieldValue(i, j, k, weight);

                    if (_isWeightFieldEnabled) {
                        _weightField.add(i, j, k, (float)weight);
                    }
                }
            }
        }
    }
}

void ScalarField::addEllipsoidValue(vmath::vec3 p, vmath::mat3 G, double r, double value) {
    setPointRadius(r);
    addEllipsoidValue(p, G, value);
}

void ScalarField::addEllipsoidValue(vmath::vec3 p, vmath::mat3 G, double scale) {
    p -= _gridOffset;

    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, _radius, G, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    vmath::vec3 gpos;
    vmath::vec3 v;
    double rsq = _radius*_radius;
    double distsq;
    double weight;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_isMaxScalarFieldThresholdSet && _field(i, j, k) > _maxScalarFieldThreshold) {
                    continue;
                }

                gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                v = (gpos - p);
                v = G*v;

                distsq = vmath::dot(v, v);

                if (distsq < rsq) {

                    weight = _evaluateTricubicFieldFunctionForRadiusSquared(distsq);
                    addScalarFieldValue(i, j, k, weight*scale);

                    if (_isWeightFieldEnabled) {
                        _weightField.add(i, j, k, (float)weight);
                    }
                }
            }
        }
    }
}

void ScalarField::setSolidCells(GridIndexVector &solidCells) {
    setMaterialGrid(solidCells);
}

void ScalarField::setMaterialGrid(GridIndexVector &solidCells) {
    GridIndex vertices[8];
    GridIndex g;
    for (unsigned int i = 0; i < solidCells.size(); i++) {
        g = solidCells[i];

        FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(g, _isize-1, _jsize-1, _ksize-1));
        Grid3d::getGridIndexVertices(g, vertices);
        for (int idx = 0; idx < 8; idx++) {
            _isVertexSolid.set(vertices[idx], true);
        }
    }
}

void ScalarField::setMaterialGrid(FluidMaterialGrid &matGrid) {
    FLUIDSIM_ASSERT(matGrid.width == _isize-1 && 
           matGrid.height == _jsize-1 && 
           matGrid.depth == _ksize-1);

    GridIndex vertices[8];
    for (int k = 0; k < _ksize-1; k++) {
        for (int j = 0; j < _jsize-1; j++) {
            for (int i = 0; i < _isize-1; i++) {
                if (matGrid.isCellSolid(i, j, k)) {
                    Grid3d::getGridIndexVertices(i, j, k, vertices);
                    for (int idx = 0; idx < 8; idx++) {
                        _isVertexSolid.set(vertices[idx], true);
                    }
                }
            }
        }
    }
}

void ScalarField::setSolidSDF(MeshLevelSet &solidSDF) {
    int si, sj, sk;
    solidSDF.getGridDimensions(&si, &sj, &sk);
    double sdx = solidSDF.getCellSize();

    double eps = 1e-12;
    bool isMatchingGrid = _isize == si + 1 && _jsize == sj + 1 && _ksize == sk + 1 &&
                          fabs(_dx - sdx) < eps;

    if (isMatchingGrid) {
        for (int k = 0; k < _ksize; k++) {
            for (int j = 0; j < _jsize; j++) {
                for (int i = 0; i < _isize; i++) {
                    if (solidSDF(i, j, k) < 0) {
                        _isVertexSolid.set(i, j, k, true);
                    }
                }
            }
        }
    } else {
        _isVertexSolid.fill(false);
        solidSDF.trilinearInterpolateSolidGridPoints(_gridOffset, _dx, _isVertexSolid);
    }
}

void ScalarField::getWeightField(Array3d<float> &field) {
    if (!_isWeightFieldEnabled) {
        return;
    }

    FLUIDSIM_ASSERT(field.width == _field.width && 
           field.height == _field.height && 
           field.depth == _field.depth);

    for (int k = 0; k < field.depth; k++) {
        for (int j = 0; j < field.height; j++) {
            for (int i = 0; i < field.width; i++) {
                field.set(i, j, k, _weightField(i, j, k));
            }
        }
    }
}

void ScalarField::getScalarField(Array3d<float> &field) {
    FLUIDSIM_ASSERT(field.width == _field.width && 
           field.height == _field.height && 
           field.depth == _field.depth);

    double val;
    for (int k = 0; k < field.depth; k++) {
        for (int j = 0; j < field.height; j++) {
            for (int i = 0; i < field.width; i++) {
                val = _field(i, j, k);
                if (_isVertexSolid(i, j, k) && val > _surfaceThreshold) {
                    val = _surfaceThreshold;
                } 

                field.set(i, j, k, (float)val);
            }
        }
    }
}

double ScalarField::getScalarFieldValue(GridIndex g) {
    return getScalarFieldValue(g.i, g.j, g.k);
}

double ScalarField::getScalarFieldValue(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width, _field.height, _field.depth));

    double val = _field(i, j, k);
    if (_isVertexSolid(i, j, k) && val > _surfaceThreshold) {
        val = _surfaceThreshold;
    } 

    return val;
}

double ScalarField::getScalarFieldValueAtCellCenter(GridIndex g) {
    return getScalarFieldValueAtCellCenter(g.i, g.j, g.k);
}

double ScalarField::getScalarFieldValueAtCellCenter(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width - 1, 
                                                        _field.height - 1, 
                                                        _field.depth - 1));
    double sum = 0.0;
    sum += getScalarFieldValue(i,     j,     k);
    sum += getScalarFieldValue(i + 1, j,     k);
    sum += getScalarFieldValue(i,     j + 1, k);
    sum += getScalarFieldValue(i + 1, j + 1, k);
    sum += getScalarFieldValue(i    , j    , k + 1);
    sum += getScalarFieldValue(i + 1, j    , k + 1);
    sum += getScalarFieldValue(i    , j + 1, k + 1);
    sum += getScalarFieldValue(i + 1, j + 1, k + 1);

    return 0.125*sum;
}

double ScalarField::getRawScalarFieldValue(GridIndex g) {
    return getRawScalarFieldValue(g.i, g.j, g.k);
}

double ScalarField::getRawScalarFieldValue(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width, _field.height, _field.depth));
    return _field(i, j, k);
}

void ScalarField::getSetScalarFieldValues(Array3d<bool> &isVertexSet) {
    FLUIDSIM_ASSERT(isVertexSet.width == _isVertexSet.width && 
           isVertexSet.height == _isVertexSet.height && 
           isVertexSet.depth == _isVertexSet.depth);

    for (int k = 0; k < isVertexSet.depth; k++) {
        for (int j = 0; j < isVertexSet.height; j++) {
            for (int i = 0; i < isVertexSet.width; i++) {
                isVertexSet.set(i, j, k, _isVertexSet(i, j, k));
            }
        }
    }
}

bool ScalarField::isScalarFieldValueSet(GridIndex g) {
    return isScalarFieldValueSet(g.i, g.j, g.k);
}

bool ScalarField::isScalarFieldValueSet(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width, _field.height, _field.depth));
    return _isVertexSet(i, j, k);
}

void ScalarField::setScalarFieldValue(int i, int j, int k, double value) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width, _field.height, _field.depth));
    _field.set(i, j, k, value);
    _isVertexSet.set(i, j, k, true);
}

void ScalarField::setScalarFieldValue(GridIndex g, double value) {
    setScalarFieldValue(g.i, g.j, g.k, value);
}

void ScalarField::addScalarFieldValue(int i, int j, int k, double value) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width, _field.height, _field.depth));
    _field.add(i, j, k, value);
    _isVertexSet.set(i, j, k, true);
}

void ScalarField::addScalarFieldValue(GridIndex g, double value) {
    addScalarFieldValue(g.i, g.j, g.k, value);
}

void ScalarField::addCellFieldValues(int i, int j, int k, double value) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _field.width-1, _field.height-1, _field.depth-1));
    GridIndex vertices[8];
    Grid3d::getGridIndexVertices(i, j, k, vertices);
    for (int i = 0; i < 8; i++) {
        _field.set(vertices[i], value);
        _isVertexSet.set(i, j, k, true);
    }
}

void ScalarField::addCellFieldValues(GridIndex g, double value) {
    addCellFieldValues(g.i, g.j, g.k, value);
}

double ScalarField::tricubicInterpolation(vmath::vec3 p) {
    if (!Grid3d::isPositionInGrid(p.x, p.y, p.z, _dx, _isize, _jsize, _ksize)) {
        return 0.0;
    }

    int i, j, k;
    double gx, gy, gz;
    Grid3d::positionToGridIndex(p.x, p.y, p.z, _dx, &i, &j, &k);
    Grid3d::GridIndexToPosition(i, j, k, _dx, &gx, &gy, &gz);

    double inv_dx = 1 / _dx;
    double ix = (p.x - gx)*inv_dx;
    double iy = (p.y - gy)*inv_dx;
    double iz = (p.z - gz)*inv_dx;

    int refi = i - 1;
    int refj = j - 1;
    int refk = k - 1;

    double min = std::numeric_limits<double>::infinity();
    double max = -std::numeric_limits<double>::infinity();
    double points[4][4][4];
    for (int pk = 0; pk < 4; pk++) {
        for (int pj = 0; pj < 4; pj++) {
            for (int pi = 0; pi < 4; pi++) {
                if (_field.isIndexInRange(pi + refi, pj + refj, pk + refk)) {
                    points[pi][pj][pk] = _field(pi + refi, pj + refj, pk + refk);

                    if (points[pi][pj][pk] < min) {
                        min = points[pi][pj][pk];
                    } else if (points[pi][pj][pk] > max) {
                        max = points[pi][pj][pk];
                    }
                } else {
                    points[pi][pj][pk] = 0;
                }
            }
        }
    }

    double val = Interpolation::tricubicInterpolate(points, ix, iy, iz);
    if (val < min) {
        val = min;
    } else if (val > max) {
        val = max;
    }

    return val;
}

double ScalarField::trilinearInterpolation(vmath::vec3 p) {
    return Interpolation::trilinearInterpolate(p, _dx, _field);
}

bool ScalarField::isPointInside(vmath::vec3 p) {
    double val = tricubicInterpolation(p);
    return val > _surfaceThreshold;
}

void ScalarField::setOffset(vmath::vec3 offset) {
    _gridOffset = offset;
}

vmath::vec3 ScalarField::getOffset() {
    return _gridOffset;
}

Array3d<float>* ScalarField::getPointerToScalarField() {
    return &_field;
}

Array3d<float>* ScalarField::getPointerToWeightField() {
    FLUIDSIM_ASSERT(_isWeightFieldEnabled);
    return &_weightField;
}

double ScalarField::_evaluateTricubicFieldFunctionForRadiusSquared(double rsq) {
    return 1.0 - _coef1*rsq*rsq*rsq + _coef2*rsq*rsq - _coef3*rsq;
}
