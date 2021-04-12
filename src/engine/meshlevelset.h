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

/*
Part of this levelset implementation was adapted from Christopher Batty's 
signed distance field generator: https://github.com/christopherbatty/SDFGen

The MIT License (MIT)

Copyright (c) 2015, Christopher Batty

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to 
deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO 
EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE 
USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#ifndef FLUIDENGINE_MESHLEVELSET_H
#define FLUIDENGINE_MESHLEVELSET_H

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include "macvelocityfield.h"
#include "trianglemesh.h"
#include "fragmentedvector.h"
#include "markerparticle.h"
#include "threadutils.h"
#include "blockarray3d.h"
#include "boundedbuffer.h"

struct VelocityDataGrid {
    MACVelocityField field;
    Array3d<float> weightU;
    Array3d<float> weightV;
    Array3d<float> weightW;

    VelocityDataGrid() {}
    VelocityDataGrid(int i, int j, int k) :
                               field(i, j, k, 0.0f),
                               weightU(i + 1, j, k, 0.0f), 
                               weightV(i, j + 1, k, 0.0f), 
                               weightW(i, j, k + 1, 0.0f) {}
    void reset() {
        field.clear();
        weightU.fill(0.0f);
        weightV.fill(0.0f);
        weightW.fill(0.0f);
    }
};

class MeshObject;

class MeshLevelSet {

public:
    MeshLevelSet();
    MeshLevelSet(int isize, int jsize, int ksize, double dx);
    MeshLevelSet(int isize, int jsize, int ksize, double dx,
                 MeshObject *meshObject);
    ~MeshLevelSet();

    void constructMinimalLevelSet(int isize, int jsize, int ksize, double dx);
    void constructMinimalSignedDistanceField(MeshLevelSet &levelset);

    float operator()(int i, int j, int k);
    float operator()(GridIndex g);
    float get(int i, int j, int k);
    float get(GridIndex g);
    void set(int i, int j, int k, float d);
    void set(GridIndex g, float d);
    int getClosestTriangleIndex(int i, int j, int k);
    int getClosestTriangleIndex(GridIndex g);
    int getClosestMeshObjectIndex(int i, int j, int k);
    int getClosestMeshObjectIndex(GridIndex g);
    MeshObject* getClosestMeshObject(int i, int j, int k);
    MeshObject* getClosestMeshObject(GridIndex g);
    float getDistanceAtCellCenter(int i, int j, int k);
    float getDistanceAtCellCenter(GridIndex g);
    vmath::vec3 getNearestVelocity(vmath::vec3 p);
    float getFaceVelocityU(int i, int j, int k);
    float getFaceVelocityU(GridIndex g);
    float getFaceVelocityV(int i, int j, int k);
    float getFaceVelocityV(GridIndex g);
    float getFaceVelocityW(int i, int j, int k);
    float getFaceVelocityW(GridIndex g);
    void setFaceVelocityU(int i, int j, int k, float v);
    void setFaceVelocityU(GridIndex g, float v);
    void setFaceVelocityV(int i, int j, int k, float v);
    void setFaceVelocityV(GridIndex g, float v);
    void setFaceVelocityW(int i, int j, int k, float v);
    void setFaceVelocityW(GridIndex g, float v);
    float trilinearInterpolate(vmath::vec3 pos);
    void trilinearInterpolatePoints(std::vector<vmath::vec3> &points, std::vector<float> &results);
    void trilinearInterpolateSolidGridPoints(vmath::vec3 offset, double dx, 
                                             Array3d<bool> &grid);
    vmath::vec3 trilinearInterpolateGradient(vmath::vec3 pos);
    float getCellWeight(int i, int j, int k);
    float getCellWeight(GridIndex g);
    float getFaceWeightU(int i, int j, int k);
    float getFaceWeightU(GridIndex g);
    float getFaceWeightV(int i, int j, int k);
    float getFaceWeightV(GridIndex g);
    float getFaceWeightW(int i, int j, int k);
    float getFaceWeightW(GridIndex g);
    float getCurvature(int i, int j, int k);
    float getCurvature(GridIndex g);

    void pushMeshObject(MeshObject *object);

    void getGridDimensions(int *i, int *j, int *k);
    double getCellSize();
    TriangleMesh* getTriangleMesh();
    std::vector<MeshObject*> getMeshObjects();
    std::vector<vmath::vec3> getVertexVelocities();
    VelocityDataGrid* getVelocityDataGrid();
    Array3d<float>* getPhiArray3d();

    void calculateSignedDistanceField(TriangleMesh &m, int bandwidth = 1);
    void calculateSignedDistanceField(TriangleMesh &m, 
                                      std::vector<vmath::vec3> &vertexVelocities, 
                                      int bandwidth = 1);
    void fastCalculateSignedDistanceField(TriangleMesh &m, int bandwidth = 1);
    void fastCalculateSignedDistanceField(TriangleMesh &m, 
                                          std::vector<vmath::vec3> &vertexVelocities, 
                                          int bandwidth = 1);
    void calculateUnion(MeshLevelSet &levelset);
    void normalizeVelocityGrid();
    void negate();
    void reset();

    void setGridOffset(GridIndex g);
    GridIndex getGridOffset();
    vmath::vec3 getPositionOffset();

    void enableVelocityData();
    void disableVelocityData();
    bool isVelocityDataEnabled();
    void enableMultiThreading();
    void disableMultiThreading();
    bool isMultiThreadingEnabled();
    void enableSignCalculation();
    void disableSignCalculation();
    bool isSignCaclulationEnabled();
    float getDistanceUpperBound();


    template<class T>
    void trilinearInterpolateSolidPoints(FragmentedVector<T> &points, 
                                         std::vector<bool> &isSolid) {
        isSolid = std::vector<bool>(points.size());
        int numCPU = ThreadUtils::getMaxThreadCount();
        int numthreads = (int)fmin(numCPU, points.size());
        std::vector<std::thread> threads(numthreads);
        std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, points.size(), numthreads);
        for (int i = 0; i < numthreads; i++) {
            threads[i] = std::thread(&MeshLevelSet::_trilinearInterpolateSolidPointsThread<T>, this,
                                     intervals[i], intervals[i + 1], &points, &isSolid);
        }

        for (int i = 0; i < numthreads; i++) {
            threads[i].join();
        }
    }

    template<class T>
    void trilinearInterpolateSolidPoints(std::vector<T> &points, 
                                         std::vector<bool> &isSolid) {
        isSolid = std::vector<bool>(points.size());
        int numCPU = ThreadUtils::getMaxThreadCount();
        int numthreads = (int)fmin(numCPU, points.size());
        std::vector<std::thread> threads(numthreads);
        std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, points.size(), numthreads);
        for (int i = 0; i < numthreads; i++) {
            threads[i] = std::thread(&MeshLevelSet::_trilinearInterpolateSolidPointsVectorThread<T>, this,
                                     intervals[i], intervals[i + 1], &points, &isSolid);
        }

        for (int i = 0; i < numthreads; i++) {
            threads[i].join();
        }
    }
    
private:

    struct TriangleData {
        vmath::vec3 vertices[3];
        GridIndex gmin;
        GridIndex gmax;
        int id = -1;
    };

    struct SDFData {
        float phi = 0.0f;
        float triangle = -1;
    };

    struct GridCountData {
        std::vector<int> gridCount;
        std::vector<int> simpleGridIndices;
        std::vector<int> overlappingGridIndices;
        int startidx = 0;
        int endidx = 0;
    };

    struct TriangleGridCountData {
        int numthreads = 1;
        int gridsize = 1;
        std::vector<int> totalGridCount;
        std::vector<GridCountData> threadGridCountData;
    };

    struct ComputeBlock {
        GridBlock<SDFData> gridBlock;
        TriangleData *triangleData;
        int numTriangles = 0;
    };

    void _computeExactBandDistanceField(int bandwidth);

    void _computeExactBandDistanceFieldMultiThreaded(int bandwidth);
    void _initializeTriangleData(int bandwidth, std::vector<TriangleData> &data);
    void _initializeBlockGrid(std::vector<TriangleData> &triangleData, 
                              int bandwidth,
                              BlockArray3d<SDFData> &blockphi);
    void _initializeActiveBlocksThread(int startidx, int endidx,
                                       std::vector<TriangleData> *triangleData, 
                                       int bandwidth,
                                       Array3d<bool> *activeBlocks);
    void _computeGridCountData(std::vector<TriangleData> &triangleData, 
                               BlockArray3d<SDFData> &blockphi,
                               TriangleGridCountData &countData);
    void _initializeGridCountData(std::vector<TriangleData> &triangleData, 
                                  BlockArray3d<SDFData> &blockphi, 
                                  TriangleGridCountData &gridCountData);
    void _computeGridCountDataThread(int startidx, int endidx,
                                     std::vector<TriangleData> *triangledata,
                                     BlockArray3d<SDFData> *blockphi,
                                     GridCountData *countdata);
    void _sortTrianglesIntoBlocks(std::vector<TriangleData> &triangleData, 
                                  TriangleGridCountData &gridCountData, 
                                  std::vector<TriangleData> &sortedTriangleData, 
                                  std::vector<int> &blockToTriangleDataIndex);
    void _computeExactBandProducerThread(BoundedBuffer<ComputeBlock> *computeBlockQueue,
                                         BoundedBuffer<ComputeBlock> *finishedComputeBlockQueue);

    void _computeExactBandDistanceFieldSingleThreaded(int bandwidth);

    void _propagateDistanceField();
    void _computeDistanceFieldSigns();
    void _computeVelocityGrids();
    void _computeVelocityGridsMultiThreaded();
    void _computeVelocityGridsSingleThreaded();
    void _computeVelocityGridMT(bool isStatic, int dir);
    void _computeVelocityGridThread(int startidx, int endidx, bool isStatic, int dir);
    float _getCellWeight(int i, int j, int k);
    float _pointToTriangleDistance(vmath::vec3 x0, vmath::vec3 x1, 
                                     vmath::vec3 x2, 
                                     vmath::vec3 x3);
    vmath::vec3 _pointToTriangleVelocity(vmath::vec3 x0, int triangleIdx);
    bool _getBarycentricCoordinates(
              double x0, double y0, 
              double x1, double y1, double x2, double y2, double x3, double y3,
              double *a, double *b, double *c);
    float _pointToSegmentDistance(vmath::vec3 x0, vmath::vec3 x1, vmath::vec3 x2);
    vmath::vec3 _pointToSegmentVelocity(vmath::vec3 x0, 
                                        vmath::vec3 x1, vmath::vec3 x2, 
                                        vmath::vec3 v1, vmath::vec3 v2, float *distance);
    int _orientation(double x1, double y1, double x2, double y2, double *twiceSignedArea);

    void _trilinearInterpolateSolidGridPointsThread(int startidx, int endidx, vmath::vec3 offset, double dx, 
                                                    Array3d<bool> *grid);

    void _normalizeVelocityGridThread(int startidx, int endidx, 
                                      Array3d<float> *vfield,
                                      Array3d<float> *vweight,
                                      Array3d<bool> *valid);

    void _calculateUnionThread(int startidx, int endidx, 
                               int triIndexOffset, int meshObjectIndexOffset, 
                               MeshLevelSet *levelset);

    void _trilinearInterpolatePointsThread(int startidx, int endidx,
                                           std::vector<vmath::vec3> *points, 
                                           std::vector<float> *results);
    
    template<class T>
    void _trilinearInterpolateSolidPointsThread(int startidx, int endidx, 
                                                FragmentedVector<T> *points, 
                                                std::vector<bool> *isSolid) {
        for (int i = startidx; i < endidx; i++) {
            (*isSolid)[i] = trilinearInterpolate((*points)[i].position) < 0.0f;
        }
    }

    template<class T>
    void _trilinearInterpolateSolidPointsVectorThread(int startidx, int endidx, 
                                                      std::vector<T> *points, 
                                                      std::vector<bool> *isSolid) {
        for (int i = startidx; i < endidx; i++) {
            (*isSolid)[i] = trilinearInterpolate((*points)[i]) < 0.0f;
        }
    }

    template <typename T>
    T _clamp(const T& n, const T& lower, const T& upper) {
      	return std::max(lower, std::min(n, upper));
    }

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    TriangleMesh _mesh;
    std::vector<vmath::vec3> _vertexVelocities;
    Array3d<float> _phi;
    Array3d<int> _closestTriangles;
    VelocityDataGrid _velocityData;

    Array3d<int> _closestMeshObjects;
    std::vector<MeshObject*> _meshObjects;

    GridIndex _gridOffset;
    vmath::vec3 _positionOffset;

    int _numVelocityExtrapolationLayers = 5;
    bool _isVelocityDataEnabled = true;
    bool _isMultiThreadingEnabled = true;
    bool _isSignCalculationEnabled = true;
    bool _isMinimalLevelSet = false;

    int _blockwidth = 10;
    int _numComputeBlocksPerJob = 10;
};

#endif
