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

#ifndef FLUIDENGINE_PARTICLEMESHER_H
#define FLUIDENGINE_PARTICLEMESHER_H

#include "fragmentedvector.h"
#include "scalarfield.h"

class TriangleMesh;
class CLScalarField;
class FluidMaterialGrid;
class AABB;
class MeshLevelSet;

class ParticleMesher {

public:
    ParticleMesher();
    ParticleMesher(int isize, int jsize, int ksize, double dx);
    ~ParticleMesher();

    void setSubdivisionLevel(int n);
    void setNumPolygonizationSlices(int n);

    TriangleMesh meshParticles(FragmentedVector<vmath::vec3> &particles,
                               double particleRadius,
                               MeshLevelSet &solidSDF);

    void setScalarFieldAccelerator(CLScalarField *accelerator);
    void setScalarFieldAccelerator();
    void enablePreviewMesher(double dx);
    void disablePreviewMesher();
    TriangleMesh getPreviewMesh(FluidMaterialGrid &materialGrid);
    TriangleMesh getPreviewMesh();

private:

    TriangleMesh _polygonizeAll(FragmentedVector<vmath::vec3> &particles,
                                MeshLevelSet &solidSDF);

    TriangleMesh _polygonizeSlices(FragmentedVector<vmath::vec3> &particles,
                                   MeshLevelSet &solidSDF);
    TriangleMesh _polygonizeSlice(int startidx, int endidx, 
                                  FragmentedVector<vmath::vec3> &particles,
                                  MeshLevelSet &solidSDF);
    void _getSubdividedGridDimensions(int *i, int *j, int *k, double *dx);
    void _computeSliceScalarField(int startidx, int endidx, 
                                  FragmentedVector<vmath::vec3> &particles,
                                  MeshLevelSet &solidSDF,
                                  ScalarField &field);
    vmath::vec3 _getSliceGridPositionOffset(int startidx, int endidx);
    void _getSliceParticles(int startidx, int endidx, 
                            FragmentedVector<vmath::vec3> &particles,
                            FragmentedVector<vmath::vec3> &sliceParticles);
    void _getMaterialGrid(FluidMaterialGrid &materialGrid);
    void _getSliceMaterialGrid(int startidx, int endidx,
                               FluidMaterialGrid &sliceMaterialGrid);
    AABB _getSliceAABB(int startidx, int endidx);
    void _addPointsToScalarField(FragmentedVector<vmath::vec3> &points,
                                 ScalarField &field);
    void _addPointsToScalarFieldAccelerator(FragmentedVector<vmath::vec3> &points,
                                            ScalarField &field);
    void _updateScalarFieldSeam(int startidx, int endidx, ScalarField &field);
    void _applyScalarFieldSliceSeamData(ScalarField &field);
    void _saveScalarFieldSliceSeamData(ScalarField &field);
    void _getSliceMask(int startidx, int endidx, Array3d<bool> &mask);

    void _initializePreviewMesher(double dx);
    void _addScalarFieldToPreviewField(ScalarField &field);
    void _addScalarFieldSliceToPreviewField(int startidx, int endidx, 
                                            ScalarField &field);
    void _getPreviewMaterialGrid(FluidMaterialGrid &materialGrid,
                                 FluidMaterialGrid &previewGrid);
    void _setScalarFieldSolidBorders(ScalarField &field);
    float _getMaxDistanceValue();

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    int _subdivisionLevel = 1;
    int _numPolygonizationSlices = 1;

    double _particleRadius = 0.0;

    Array3d<float> _scalarFieldSeamData;

    int _maxParticlesPerScalarFieldAddition = 1e7;
    bool _isScalarFieldAcceleratorSet = false;
    CLScalarField *_scalarFieldAccelerator;

    bool _isPreviewMesherEnabled = false;
    int _pisize = 0;
    int _pjsize = 0;
    int _pksize = 0;
    double _pdx = 0.0;
    ScalarField _pfield;


};

#endif