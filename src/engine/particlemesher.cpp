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

#include "particlemesher.h"

#include "polygonizer3d.h"
#include "clscalarfield.h"
#include "fluidmaterialgrid.h"
#include "aabb.h"
#include "meshlevelset.h"

ParticleMesher::ParticleMesher() {
}

ParticleMesher::ParticleMesher(int isize, int jsize, int ksize, double dx) :
                                                    _isize(isize), _jsize(jsize), _ksize(ksize), _dx(dx) {

}

ParticleMesher::~ParticleMesher() {

}

void ParticleMesher::setSubdivisionLevel(int n) {
    FLUIDSIM_ASSERT(n >= 1);
    _subdivisionLevel = n;
}

void ParticleMesher::setNumPolygonizationSlices(int n) {
    FLUIDSIM_ASSERT(n >= 1);

    if (n > _isize) {
        n = _isize;
    }

    _numPolygonizationSlices = n;
}

TriangleMesh ParticleMesher::meshParticles(FragmentedVector<vmath::vec3> &particles,
                                           double particleRadius,
                                           MeshLevelSet &solidSDF) {
    FLUIDSIM_ASSERT(particleRadius > 0.0);

    _particleRadius = particleRadius;

    if (_numPolygonizationSlices == 1) {
        return _polygonizeAll(particles, solidSDF);
    }

    return _polygonizeSlices(particles, solidSDF);
}

void ParticleMesher::setScalarFieldAccelerator(CLScalarField *accelerator) {
    _scalarFieldAccelerator = accelerator;
    _isScalarFieldAcceleratorSet = true;
}

void ParticleMesher::setScalarFieldAccelerator() {
    _isScalarFieldAcceleratorSet = false;
}

void ParticleMesher::enablePreviewMesher(double dx) {
    _initializePreviewMesher(dx);
    _isPreviewMesherEnabled = true;
}

void ParticleMesher::disablePreviewMesher() {
    _isPreviewMesherEnabled = false;
}

TriangleMesh ParticleMesher::getPreviewMesh(FluidMaterialGrid &materialGrid) {
    if (!_isPreviewMesherEnabled) {
        return TriangleMesh();
    }

    FluidMaterialGrid pmgrid(_pisize, _pjsize, _pksize);
    _getPreviewMaterialGrid(materialGrid, pmgrid);
    _pfield.setMaterialGrid(pmgrid);

    Polygonizer3d polygonizer(&_pfield);
    return polygonizer.polygonizeSurface();
}

TriangleMesh ParticleMesher::getPreviewMesh() {
    if (!_isPreviewMesherEnabled) {
        return TriangleMesh();
    }

    ScalarField field = _pfield;
    _setScalarFieldSolidBorders(field);

    Polygonizer3d polygonizer(&field);
    return polygonizer.polygonizeSurface();
}

TriangleMesh ParticleMesher::_polygonizeAll(FragmentedVector<vmath::vec3> &particles,
                                            MeshLevelSet &solidSDF) {
    int subd = _subdivisionLevel;
    int width = _isize*subd;
    int height = _jsize*subd;
    int depth = _ksize*subd;
    double dx = _dx / (double)subd;

    ScalarField field(width + 1, height + 1, depth + 1, dx);

    FluidMaterialGrid mgrid(_isize, _jsize, _ksize);
    _getMaterialGrid(mgrid);
    mgrid.setSubdivisionLevel(subd);

    field.setSolidSDF(solidSDF);
    field.setMaterialGrid(mgrid);
    field.setPointRadius(_particleRadius);
    field.setSurfaceThreshold(0.0);
    field.fill(_getMaxDistanceValue());
    _addPointsToScalarField(particles, field);

    if (_isPreviewMesherEnabled) {
        _addScalarFieldToPreviewField(field);
    }

    Polygonizer3d polygonizer(&field, &solidSDF);

    return polygonizer.polygonizeSurface();
}

TriangleMesh ParticleMesher::_polygonizeSlices(FragmentedVector<vmath::vec3> &particles,
                                               MeshLevelSet &solidSDF) {
    int width, height, depth;
    double dx;
    _getSubdividedGridDimensions(&width, &height, &depth, &dx);

    int sliceWidth = ceil((double)width / (double)_numPolygonizationSlices);
    int numSlices = ceil((double)width / (double)sliceWidth);

    if (numSlices == 1) {
        return _polygonizeAll(particles, solidSDF);
    }

    TriangleMesh mesh;
    for (int i = 0; i < numSlices; i++) {
        int startidx = i*sliceWidth;
        int endidx = startidx + sliceWidth - 1;
        endidx = endidx < width ? endidx : width - 1;

        TriangleMesh sliceMesh = _polygonizeSlice(startidx, endidx, 
                                                  particles,
                                                  solidSDF);

        vmath::vec3 offset = _getSliceGridPositionOffset(startidx, endidx);
        sliceMesh.translate(offset);
        mesh.join(sliceMesh);
    }

    return mesh;
}

TriangleMesh ParticleMesher::_polygonizeSlice(int startidx, int endidx, 
                                              FragmentedVector<vmath::vec3> &particles,
                                              MeshLevelSet &solidSDF) {

    int width, height, depth;
    double dx;
    _getSubdividedGridDimensions(&width, &height, &depth, &dx);

    bool isStartSlice = startidx == 0;
    bool isEndSlice = endidx == width - 1;
    bool isMiddleSlice = !isStartSlice && !isEndSlice;

    int gridWidth = endidx - startidx + 1;
    int gridHeight = height;
    int gridDepth = depth;
    if (isStartSlice || isEndSlice) {
        gridWidth++;
    } else if (isMiddleSlice) {
        gridWidth += 2;
    }

    ScalarField field(gridWidth + 1, gridHeight + 1, gridDepth + 1, dx);
    _computeSliceScalarField(startidx, endidx, particles, solidSDF, field);

    if (_isPreviewMesherEnabled) {
        _addScalarFieldSliceToPreviewField(startidx, endidx, field);
    }

    Array3d<bool> mask(gridWidth, gridHeight, gridDepth);
    _getSliceMask(startidx, endidx, mask);

    Polygonizer3d polygonizer(&field, &solidSDF);
    polygonizer.setSurfaceCellMask(&mask);

    return polygonizer.polygonizeSurface();
}

void ParticleMesher::_getSubdividedGridDimensions(int *i, int *j, int *k, double *dx) {
    *i = _isize*_subdivisionLevel;
    *j = _jsize*_subdivisionLevel;
    *k = _ksize*_subdivisionLevel;
    *dx = _dx / (double)_subdivisionLevel;
}

void ParticleMesher::_computeSliceScalarField(int startidx, int endidx, 
                                                       FragmentedVector<vmath::vec3> &particles,
                                                       MeshLevelSet &solidSDF,
                                                       ScalarField &field) {
    int width, height, depth;
    field.getGridDimensions(&width, &height, &depth);

    FluidMaterialGrid sliceMaterialGrid(width - 1, height - 1, depth - 1);
    _getSliceMaterialGrid(startidx, endidx, sliceMaterialGrid);

    vmath::vec3 fieldOffset = _getSliceGridPositionOffset(startidx, endidx);
    field.setOffset(fieldOffset);
    field.setSolidSDF(solidSDF);
    field.setMaterialGrid(sliceMaterialGrid);
    field.setPointRadius(_particleRadius);
    field.setSurfaceThreshold(0.0);
    field.fill(_getMaxDistanceValue());

    _addPointsToScalarField(particles, field);
    _updateScalarFieldSeam(startidx, endidx, field);
}

vmath::vec3 ParticleMesher::_getSliceGridPositionOffset(int startidx, int endidx) {
    (void)endidx;
    int width, height, depth;
    double dx;
    _getSubdividedGridDimensions(&width, &height, &depth, &dx);

    bool isStartSlice = startidx == 0;

    double offx;
    if (isStartSlice) {
        offx = startidx*dx;
    } else {
        offx = (startidx - 1)*dx;
    }

    return vmath::vec3(offx, 0.0, 0.0); 
}

void ParticleMesher::_getSliceParticles(int startidx, int endidx, 
                                                 FragmentedVector<vmath::vec3> &particles,
                                                 FragmentedVector<vmath::vec3> &sliceParticles) {
    AABB bbox = _getSliceAABB(startidx, endidx);
    for (unsigned int i = 0; i < particles.size(); i++) {
        if (bbox.isPointInside(particles[i])) {
            sliceParticles.push_back(particles[i]);
        }
    }
}


void ParticleMesher::_getSliceMaterialGrid(int startidx, int endidx,
                                                    FluidMaterialGrid &sliceMaterialGrid) {
    (void)endidx;

    FluidMaterialGrid materialGrid(_isize, _jsize, _ksize);
    _getMaterialGrid(materialGrid);
    materialGrid.setSubdivisionLevel(_subdivisionLevel);
    
    Material m;
    for (int k = 0; k < sliceMaterialGrid.depth; k++) {
        for (int j = 0; j < sliceMaterialGrid.height; j++) {
            for (int i = 0; i < sliceMaterialGrid.width; i++) {
                m = materialGrid(startidx + i, j, k);
                sliceMaterialGrid.set(i, j, k, m);
            }
        }
    }
}

void ParticleMesher::_getMaterialGrid(FluidMaterialGrid &materialGrid) {
    int w = materialGrid.width;
    int h = materialGrid.height;
    int d = materialGrid.depth;
    for (int j = 0; j < h; j++) {
        for (int i = 0; i < w; i++) {
            materialGrid.setSolid(i, j, 0);
            materialGrid.setSolid(i, j, d-1);
        }
    }

    for (int k = 0; k < d; k++) {
        for (int i = 0; i < w; i++) {
            materialGrid.setSolid(i, 0, k);
            materialGrid.setSolid(i, h-1, k);
        }
    }

    for (int k = 0; k < d; k++) {
        for (int j = 0; j < h; j++) {
            materialGrid.setSolid(0, j, k);
            materialGrid.setSolid(w-1, j, k);
        }
    }

}

AABB ParticleMesher::_getSliceAABB(int startidx, int endidx) {
    int width, height, depth;
    double dx;
    _getSubdividedGridDimensions(&width, &height, &depth, &dx);

    bool isStartSlice = startidx == 0;
    bool isEndSlice = endidx == width - 1;
    bool isMiddleSlice = !isStartSlice && !isEndSlice;

    double gridWidth = (endidx - startidx + 1)*dx;
    double gridHeight = height*dx;
    double gridDepth = depth*dx;
    if (isStartSlice || isEndSlice) {
        gridWidth += dx;
    } else if (isMiddleSlice) {
        gridWidth += 2.0*dx;
    }

    vmath::vec3 offset = _getSliceGridPositionOffset(startidx, endidx);

    AABB bbox(offset, gridWidth, gridHeight, gridDepth);
    bbox.expand(2.0*_particleRadius);

    return bbox;
}

void ParticleMesher::_addPointsToScalarField(FragmentedVector<vmath::vec3> &points,
                                                      ScalarField &field) {
    
    if (_isScalarFieldAcceleratorSet) {
        _addPointsToScalarFieldAccelerator(points, field);
        return;
    }

    int subd = _subdivisionLevel;
    int width = _isize*subd;
    int height = _jsize*subd;
    int depth = _ksize*subd;
    double dx = _dx / (double)subd;
    double r = _particleRadius;
    vmath::vec3 offset = field.getOffset();

    Array3d<float>* nodes = field.getPointerToScalarField();
    nodes->fill(_getMaxDistanceValue());

    GridIndex g, gmin, gmax;
    vmath::vec3 p;
    vmath::vec3 pminOffset(-r, -r, -r);
    vmath::vec3 pmaxOffset(r, r, r);
    for(int pidx = 0; pidx < (int)points.size(); pidx++) {
        p = points[pidx] - offset;

        gmin = Grid3d::positionToGridIndex(p + pminOffset, dx);
        gmax = Grid3d::positionToGridIndex(p + pmaxOffset, dx);
        gmin.i = fmax(0, gmin.i);
        gmin.j = fmax(0, gmin.j);
        gmin.k = fmax(0, gmin.k);
        gmax.i = fmin(width, gmax.i + 1);
        gmax.j = fmin(height, gmax.j + 1);
        gmax.k = fmin(depth, gmax.k + 1);

        for(int k = gmin.k; k <= gmax.k; k++) {
            for(int j = gmin.j; j <= gmax.j; j++) {
                for(int i = gmin.i; i <= gmax.i; i++) {
                    vmath::vec3 cpos = Grid3d::GridIndexToPosition(i, j, k, dx);
                    float dist = vmath::length(cpos - p) - r;
                    if (dist < nodes->get(i, j, k)) {
                        nodes->set(i, j, k, dist);
                    }
                }
            }
        }
    }

    for (int k = 0; k < depth + 1; k++) {
        for (int j = 0; j < height + 1; j++) {
            for (int i = 0; i < width + 1; i++) {
                nodes->set(i, j, k, -nodes->get(i, j, k));
            }
        }
    }
}

void ParticleMesher::_addPointsToScalarFieldAccelerator(FragmentedVector<vmath::vec3> &points,
                                                        ScalarField &field) {
    bool isThresholdSet = _scalarFieldAccelerator->isMaxScalarFieldValueThresholdSet();
    double origThreshold = _scalarFieldAccelerator->getMaxScalarFieldValueThreshold();
    _scalarFieldAccelerator->setMaxScalarFieldValueThreshold();

    int n = _maxParticlesPerScalarFieldAddition;
    std::vector<vmath::vec3> positions;
    positions.reserve(fmin(n, points.size()));

    for (int startidx = 0; startidx < (int)points.size(); startidx += n) {
        int endidx = startidx + n - 1;
        if (endidx >= (int)points.size()) {
            endidx = points.size() - 1;
        }

        positions.clear();
        for (int i = startidx; i <= endidx; i++) {
            positions.push_back(points[i]);
        }

        _scalarFieldAccelerator->addLevelSetPoints(positions, field);
    }

    Array3d<float>* fieldvals = field.getPointerToScalarField();
    for (int k = 0; k < fieldvals->depth; k++) {
        for (int j = 0; j < fieldvals->height; j++) {
            for (int i = 0; i < fieldvals->width; i++) {
                fieldvals->set(i, j, k, -fieldvals->get(i, j, k));
            }
        }
    }

    if (!isThresholdSet) {
        _scalarFieldAccelerator->setMaxScalarFieldValueThreshold();
    } else {
        _scalarFieldAccelerator->setMaxScalarFieldValueThreshold(origThreshold);
    }
}

void ParticleMesher::_updateScalarFieldSeam(int startidx, int endidx,
                                                     ScalarField &field) {
    int width, height, depth;
    double dx;
    _getSubdividedGridDimensions(&width, &height, &depth, &dx);

    bool isStartSlice = startidx == 0;
    bool isEndSlice = endidx == width - 1;

    if (!isStartSlice) {
        _applyScalarFieldSliceSeamData(field);
    }
    if (!isEndSlice) {
        _saveScalarFieldSliceSeamData(field);
    }
}

void ParticleMesher::_applyScalarFieldSliceSeamData(ScalarField &field) {
    int width, height, depth;
    field.getGridDimensions(&width, &height, &depth);

    for (int k = 0; k < depth; k++) {
        for (int j = 0; j < height; j++) {
            for (int i = 0; i <= 2; i++) {
                field.setScalarFieldValue(i, j, k, _scalarFieldSeamData(i, j, k));
            }
        }
    }
}

void ParticleMesher::_saveScalarFieldSliceSeamData(ScalarField &field) {
    int width, height, depth;
    field.getGridDimensions(&width, &height, &depth);

    _scalarFieldSeamData = Array3d<float>(3, height, depth);
    for (int k = 0; k < depth; k++) {
        for (int j = 0; j < height; j++) {
            for (int i = 0; i <= 2; i++) {
                _scalarFieldSeamData.set(i, j, k, field.getRawScalarFieldValue(i + width - 3, j, k));
            }
        }
    }
}

void ParticleMesher::_getSliceMask(int startidx, int endidx, Array3d<bool> &mask) {
    mask.fill(true);

    int width, height, depth;
    double dx;
    _getSubdividedGridDimensions(&width, &height, &depth, &dx);

    bool isStartSlice = startidx == 0;
    bool isEndSlice = endidx == width - 1;

    if (!isStartSlice) {
        int idx = 0;
        for (int k = 0; k < mask.depth; k++) {
            for (int j = 0; j < mask.height; j++) {
                mask.set(idx, j, k, false);
            }
        }
    }

    if (!isEndSlice) {
        int idx = mask.width - 1;
        for (int k = 0; k < mask.depth; k++) {
            for (int j = 0; j < mask.height; j++) {
                mask.set(idx, j, k, false);
            }
        }
    }
}

void ParticleMesher::_initializePreviewMesher(double pdx) {
    double width = _isize * _dx;
    double height = _jsize * _dx;
    double depth = _ksize * _dx;

    _pisize = fmax(ceil(width / pdx), 1);
    _pjsize = fmax(ceil(height / pdx), 1);
    _pksize = fmax(ceil(depth / pdx), 1);
    _pdx = pdx;

    _pfield = ScalarField(_pisize + 1, _pjsize + 1, _pksize + 1, _pdx);
    _pfield.setSurfaceThreshold(0.0);
}

void ParticleMesher::_addScalarFieldToPreviewField(ScalarField &field) {
    vmath::vec3 pv;
    for (int k = 0; k < _pksize + 1; k++) {
        for (int j = 0; j < _pjsize + 1; j++) {
            for (int i = 0; i < _pisize + 1; i++) {
                pv = Grid3d::GridIndexToPosition(i, j, k, _pdx);
                double fval = field.trilinearInterpolation(pv);
                _pfield.setScalarFieldValue(i, j, k, fval);
            }
        }
    }
}

void ParticleMesher::_addScalarFieldSliceToPreviewField(
        int startidx, int endidx, ScalarField &field) {

    int isize, jsize, ksize;
    field.getGridDimensions(&isize, &jsize, &ksize);

    double width = isize * _dx;
    double height = jsize * _dx;
    double depth = ksize * _dx;
    vmath::vec3 offset = _getSliceGridPositionOffset(startidx, endidx);
    AABB bbox(offset, width, height, depth);

    vmath::vec3 pv;
    for (int k = 0; k < _pksize + 1; k++) {
        for (int j = 0; j < _pjsize + 1; j++) {
            for (int i = 0; i < _pisize + 1; i++) {
                pv = Grid3d::GridIndexToPosition(i, j, k, _pdx);
                if (!bbox.isPointInside(pv)) {
                    continue;
                }

                double fval = field.trilinearInterpolation(pv - offset);
                _pfield.setScalarFieldValue(i, j, k, fval);
            }
        }
    }
}

void ParticleMesher::_getPreviewMaterialGrid(
        FluidMaterialGrid &materialGrid, FluidMaterialGrid &previewGrid) {
    
    for (int j = 0; j < _pjsize; j++) {
        for (int i = 0; i < _pisize; i++) {
            previewGrid.setSolid(i, j, 0);
            previewGrid.setSolid(i, j, _pksize-1);
        }
    }

    for (int k = 0; k < _pksize; k++) {
        for (int i = 0; i < _pisize; i++) {
            previewGrid.setSolid(i, 0, k);
            previewGrid.setSolid(i, _pjsize-1, k);
        }
    }

    for (int k = 0; k < _pksize; k++) {
        for (int j = 0; j < _pjsize; j++) {
            previewGrid.setSolid(0, j, k);
            previewGrid.setSolid(_pisize-1, j, k);
        }
    }

    vmath::vec3 c;
    GridIndex g;
    for (int k = 0; k < _pksize; k++) {
        for (int j = 0; j < _pjsize; j++) {
            for (int i = 0; i < _pisize; i++) {
                c = Grid3d::GridIndexToCellCenter(i, j, k, _pdx);
                g = Grid3d::positionToGridIndex(c, _dx);

                if (!Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize)) {
                    continue;
                }

                if (materialGrid.isCellSolid(g)) {
                    previewGrid.setSolid(i, j, k);
                }
            }
        }
    }
}

void ParticleMesher::_setScalarFieldSolidBorders(ScalarField &field) {
    double eps = 1e-3;
    double thresh = field.getSurfaceThreshold() - eps;
    int si, sj, sk;
    field.getGridDimensions(&si, &sj, &sk);

    for (int j = 0; j < sj; j++) {
        for (int i = 0; i < si; i++) {
            field.setScalarFieldValue(i, j, 0, thresh);
            field.setScalarFieldValue(i, j, sk-1, thresh);
        }
    }

    for (int k = 0; k < sk; k++) {
        for (int i = 0; i < si; i++) {
            field.setScalarFieldValue(i, 0, k, thresh);
            field.setScalarFieldValue(i, sj-1, k, thresh);
        }
    }

    for (int k = 0; k < sk; k++) {
        for (int j = 0; j < sj; j++) {
            field.setScalarFieldValue(0, j, k, thresh);
            field.setScalarFieldValue(si-1, j, k, thresh);
        }
    }
}

float ParticleMesher::_getMaxDistanceValue() {
    return 3.0 * _particleRadius;
}