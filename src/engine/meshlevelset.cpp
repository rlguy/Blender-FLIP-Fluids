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

#include "meshlevelset.h"

#include "interpolation.h"
#include "levelsetutils.h"
#include "meshutils.h"

MeshLevelSet::MeshLevelSet() {
}

MeshLevelSet::MeshLevelSet(int isize, int jsize, int ksize, double dx) :
                _isize(isize), _jsize(jsize), _ksize(ksize), _dx(dx),
                _phi(isize + 1, jsize + 1, ksize + 1), 
                _closestTriangles(isize + 1, jsize + 1, ksize + 1, -1),
                _velocityData(isize, jsize, ksize),
                _closestMeshObjects(isize + 1, jsize + 1, ksize + 1, -1) {
    _phi.fill(getDistanceUpperBound());
}

MeshLevelSet::MeshLevelSet(int isize, int jsize, int ksize, double dx, 
                           MeshObject *meshObject) :
                _isize(isize), _jsize(jsize), _ksize(ksize), _dx(dx),
                _phi(isize + 1, jsize + 1, ksize + 1), 
                _closestTriangles(isize + 1, jsize + 1, ksize + 1, -1),
                _velocityData(isize, jsize, ksize),
                _closestMeshObjects(isize + 1, jsize + 1, ksize + 1, -1) {
    _phi.fill(getDistanceUpperBound());
    _meshObjects.push_back(meshObject);
}

MeshLevelSet::~MeshLevelSet() {
}

void MeshLevelSet::constructMinimalLevelSet(int isize, int jsize, int ksize, double dx) {
    _isize = isize;
    _jsize = jsize;
    _ksize = ksize;
    _dx = dx;
    _phi = Array3d<float>(_isize + 1, _jsize + 1, _ksize + 1, getDistanceUpperBound());
    _isMinimalLevelSet = true;
    _isVelocityDataEnabled = false;
}

void MeshLevelSet::constructMinimalSignedDistanceField(MeshLevelSet &levelset) {
    levelset.getGridDimensions(&_isize, &_jsize, &_ksize);
    _dx = levelset.getCellSize();
    _phi = Array3d<float>(_isize + 1, _jsize + 1, _ksize + 1);
    _isMinimalLevelSet = true;
    _isVelocityDataEnabled = false;

    for (int k = 0; k < _phi.depth; k++) {
        for (int j = 0; j < _phi.height; j++) {
            for (int i = 0; i < _phi.width; i++) {
                _phi.set(i, j, k, levelset(i, j, k));
            }
        }
    }
}

float MeshLevelSet::operator()(int i, int j, int k) {
    return get(i, j, k);
}

float MeshLevelSet::operator()(GridIndex g) {
    return get(g);
}

float MeshLevelSet::get(int i, int j, int k) {
    FLUIDSIM_ASSERT(_phi.isIndexInRange(i, j, k));
    return _phi(i, j, k);
}

float MeshLevelSet::get(GridIndex g) {
    FLUIDSIM_ASSERT(_phi.isIndexInRange(g));
    return _phi(g);
}

void MeshLevelSet::set(int i, int j, int k, float d) {
    FLUIDSIM_ASSERT(_phi.isIndexInRange(i, j, k));
    _phi.set(i, j, k, d);
}

void MeshLevelSet::set(GridIndex g, float d) {
    FLUIDSIM_ASSERT(_phi.isIndexInRange(g));
    _phi.set(g, d);
}

int MeshLevelSet::getClosestTriangleIndex(int i, int j, int k) {
    FLUIDSIM_ASSERT(_closestTriangles.isIndexInRange(i, j, k));
    return _closestTriangles(i, j, k);
}

int MeshLevelSet::getClosestTriangleIndex(GridIndex g) {
    FLUIDSIM_ASSERT(_closestTriangles.isIndexInRange(g));
    return _closestTriangles(g);
}

int MeshLevelSet::getClosestMeshObjectIndex(int i, int j, int k) {
    FLUIDSIM_ASSERT(_closestMeshObjects.isIndexInRange(i, j, k));
    return _closestMeshObjects(i, j, k);
}

int MeshLevelSet::getClosestMeshObjectIndex(GridIndex g) {
    FLUIDSIM_ASSERT(_closestMeshObjects.isIndexInRange(g));
    return _closestMeshObjects(g);
}

MeshObject* MeshLevelSet::getClosestMeshObject(GridIndex g) {
    return getClosestMeshObject(g.i, g.j, g.k);
}

MeshObject* MeshLevelSet::getClosestMeshObject(int i, int j, int k) {
    FLUIDSIM_ASSERT(_closestMeshObjects.isIndexInRange(i, j, k));
    int idx = _closestMeshObjects(i, j, k);
    if (idx == -1) {
        return nullptr;
    }

    FLUIDSIM_ASSERT(idx >= 0 && idx < (int)_meshObjects.size());

    return _meshObjects[idx];
}

float MeshLevelSet::getDistanceAtCellCenter(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));
    return 0.125f * (_phi(i, j, k) + 
                     _phi(i + 1, j, k) + 
                     _phi(i, j + 1, k) + 
                     _phi(i + 1, j + 1, k) +
                     _phi(i, j, k + 1) + 
                     _phi(i + 1, j, k + 1) + 
                     _phi(i, j + 1, k + 1) + 
                     _phi(i + 1, j + 1, k + 1));
}

float MeshLevelSet::getDistanceAtCellCenter(GridIndex g) {
    return getDistanceAtCellCenter(g.i, g.j, g.k);
}

vmath::vec3 MeshLevelSet::getNearestVelocity(vmath::vec3 p) {
    FLUIDSIM_ASSERT(_isVelocityDataEnabled);

    p -= _positionOffset;

    GridIndex g = Grid3d::positionToGridIndex(p, _dx);
    GridIndex nodes[8];
    Grid3d::getGridIndexVertices(g, nodes);

    int nearestTri = -1;
    float nearestDist = getDistanceUpperBound();
    for (int nidx = 0; nidx < 8; nidx++) {
        GridIndex n = nodes[nidx];
        if (!Grid3d::isGridIndexInRange(n, _isize + 1, _jsize + 1, _ksize + 1)) {
            continue;
        }

        if (_closestTriangles(n) == -1) {
            continue;
        }

        Triangle t = _mesh.triangles[_closestTriangles(n)];
        vmath::vec3 v0 = _mesh.vertices[t.tri[0]] - _positionOffset;
        vmath::vec3 v1 = _mesh.vertices[t.tri[1]] - _positionOffset;
        vmath::vec3 v2 = _mesh.vertices[t.tri[2]] - _positionOffset;
        float d = _pointToTriangleDistance(p, v0, v1, v2);
        if (d < nearestDist) {
            nearestDist = d;
            nearestTri = _closestTriangles(n);
        }
    }

    if (nearestTri == -1) {
        return vmath::vec3(0.0, 0.0, 0.0);
    }

    return _pointToTriangleVelocity(p, nearestTri);
}

float MeshLevelSet::getFaceVelocityU(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize, _ksize));
    return _velocityData.field.U(i, j, k);
}

float MeshLevelSet::getFaceVelocityU(GridIndex g) {
    return getFaceVelocityU(g.i, g.j, g.k);
}

float MeshLevelSet::getFaceVelocityV(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize + 1, _ksize));
    return _velocityData.field.V(i, j, k);
}

float MeshLevelSet::getFaceVelocityV(GridIndex g) {
    return getFaceVelocityV(g.i, g.j, g.k);
}

float MeshLevelSet::getFaceVelocityW(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize + 1));
    return _velocityData.field.W(i, j, k);
}

float MeshLevelSet::getFaceVelocityW(GridIndex g) {
    return getFaceVelocityW(g.i, g.j, g.k);
}

void MeshLevelSet::setFaceVelocityU(int i, int j, int k, float v) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize, _ksize));
    _velocityData.field.setU(i, j, k, v);
}

void MeshLevelSet::setFaceVelocityU(GridIndex g, float v) {
    setFaceVelocityU(g.i, g.j, g.k, v);
}

void MeshLevelSet::setFaceVelocityV(int i, int j, int k, float v) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize + 1, _ksize));
    _velocityData.field.setV(i, j, k, v);
}

void MeshLevelSet::setFaceVelocityV(GridIndex g, float v) {
    setFaceVelocityV(g.i, g.j, g.k, v);
}

void MeshLevelSet::setFaceVelocityW(int i, int j, int k, float v) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize + 1));
    _velocityData.field.setW(i, j, k, v);
}

void MeshLevelSet::setFaceVelocityW(GridIndex g, float v) {
    setFaceVelocityW(g.i, g.j, g.k, v);
}

float MeshLevelSet::trilinearInterpolate(vmath::vec3 pos) {
    return Interpolation::trilinearInterpolate(pos, _dx, _phi);
}

void MeshLevelSet::trilinearInterpolateSolidGridPoints(vmath::vec3 offset, double dx, 
                                                       Array3d<bool> &grid) {

    int gridsize = grid.width * grid.height * grid.depth;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&MeshLevelSet::_trilinearInterpolateSolidGridPointsThread, this,
                                 intervals[i], intervals[i + 1], offset, dx, &grid);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void MeshLevelSet::_trilinearInterpolateSolidGridPointsThread(int startidx, int endidx, 
                                                              vmath::vec3 offset, double dx, 
                                                              Array3d<bool> *grid) {
    double eps = 1e-6;
    bool isAlignedSubd2 = fabs(2*dx - _dx) < eps && vmath::length(offset) < eps;

    int isize = grid->width;
    int jsize = grid->height;

    if (isAlignedSubd2) {
        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);

            float d;
            if (g.i % 2 == 0 && g.j % 2 == 0 && g.k % 2 == 0) {
                d = _phi(g.i >> 1, g.j >> 1, g.k >> 1);
            } else {
                vmath::vec3 p = Grid3d::GridIndexToPosition(g, dx);
                d = Interpolation::trilinearInterpolate(p + offset, _dx, _phi);
            }
            grid->set(g, d < 0);
        }
    } else {
        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
            vmath::vec3 p = Grid3d::GridIndexToPosition(g, dx);
            if (Interpolation::trilinearInterpolate(p + offset, _dx, _phi) < 0) {
                grid->set(g, true);
            }
        }
    }
}

vmath::vec3 MeshLevelSet::trilinearInterpolateGradient(vmath::vec3 pos) {
    vmath::vec3 grad;
    Interpolation::trilinearInterpolateGradient(pos, _dx, _phi, &grad);
    return grad;
}

float MeshLevelSet::getCellWeight(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize));
    return _getCellWeight(i, j, k);
}

float MeshLevelSet::getCellWeight(GridIndex g) {
    return getCellWeight(g.i, g.j, g.k);
}

float MeshLevelSet::getFaceWeightU(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize, _ksize));
    return LevelsetUtils::fractionInside(_phi(i, j, k), 
                                         _phi(i, j + 1, k),
                                         _phi(i, j, k + 1), 
                                         _phi(i, j + 1, k + 1));
}

float MeshLevelSet::getFaceWeightU(GridIndex g) {
    return getFaceWeightU(g.i, g.j, g.k);
}

float MeshLevelSet::getFaceWeightV(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize + 1, _ksize));
    return LevelsetUtils::fractionInside(_phi(i, j, k),
                                         _phi(i, j, k + 1),
                                         _phi(i + 1, j, k),
                                         _phi(i + 1, j, k + 1));
}

float MeshLevelSet::getFaceWeightV(GridIndex g) {
    return getFaceWeightV(g.i, g.j, g.k);
}

float MeshLevelSet::getFaceWeightW(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize, _jsize, _ksize + 1));
    return LevelsetUtils::fractionInside(_phi(i, j, k),
                                         _phi(i, j + 1, k),
                                         _phi(i + 1, j, k),
                                         _phi(i + 1, j + 1, k));
}

float MeshLevelSet::getFaceWeightW(GridIndex g) {
    return getFaceWeightW(g.i, g.j, g.k);
}

/*
    Curvature from levelset formula adapted from: 
        "Level set method: Explanation" - http://profs.etsmtl.ca/hlombaert/levelset/
*/
float MeshLevelSet::getCurvature(int i, int j, int k) {
    FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(i, j, k, _isize + 1, _jsize + 1, _ksize + 1));

    if (Grid3d::isGridIndexOnBorder(i, j, k, _isize + 1, _jsize + 1, _ksize + 1)) {
        return 0.0f;
    }

    float x = 0.5f * (_phi(i + 1, j, k) - _phi(i - 1, j, k));
    float y = 0.5f * (_phi(i, j + 1, k) - _phi(i, j - 1, k));
    float z = 0.5f * (_phi(i, j, k + 1) - _phi(i, j, k - 1));

    float xx = _phi(i + 1, j, k) - 2.0f * _phi(i, j, k) + _phi(i - 1, j, k);
    float yy = _phi(i, j + 1, k) - 2.0f * _phi(i, j, k) + _phi(i, j - 1, k);
    float zz = _phi(i, j, k + 1) - 2.0f * _phi(i, j, k) + _phi(i, j, k - 1);

    float xy = 0.25f * (_phi(i + 1, j + 1, k) - 
                        _phi(i - 1, j + 1, k) - 
                        _phi(i + 1, j - 1, k) + 
                        _phi(i - 1, j - 1, k));

    float xz = 0.25f * (_phi(i + 1, j, k + 1) - 
                        _phi(i - 1, j, k + 1) - 
                        _phi(i + 1, j, k - 1) + 
                        _phi(i - 1, j, k - 1));

    float yz = 0.25f * (_phi(i, j + 1, k + 1) - 
                        _phi(i, j - 1, k + 1) - 
                        _phi(i, j + 1, k - 1) + 
                        _phi(i, j - 1, k - 1));

    float denominator = x*x + y*y + z*z;
    denominator = sqrt(denominator * denominator * denominator);

    float eps = 1e-9f;
    if (denominator < eps) {
        return 0.0f;
    }

    float curvature = (xx * (y*y + z*z) + yy * (x*x + z*z) + zz * (x*x + y*y) -
                       2*xy*x*y - 2*xz*x*z - 2*yz*y*z) / denominator;

    return curvature;
}

float MeshLevelSet::getCurvature(GridIndex g) {
    return getCurvature(g.i, g.j, g.k);
}

void MeshLevelSet::getGridDimensions(int *i, int *j, int *k) {
    *i = _isize;
    *j = _jsize;
    *k = _ksize;
}

double MeshLevelSet::getCellSize() {
    return _dx;
}

TriangleMesh *MeshLevelSet::getTriangleMesh() {
    return &_mesh;
}

std::vector<MeshObject*> MeshLevelSet::getMeshObjects() {
    return _meshObjects;
}

std::vector<vmath::vec3> MeshLevelSet::getVertexVelocities() {
    return _vertexVelocities;
}

VelocityDataGrid* MeshLevelSet::getVelocityDataGrid() {
    return &_velocityData;
}

void MeshLevelSet::pushMeshObject(MeshObject *object) {
    _meshObjects.push_back(object);
}

void MeshLevelSet::calculateSignedDistanceField(TriangleMesh &m, int bandwidth) {
    std::vector<vmath::vec3> vertexVelocities(m.vertices.size());
    calculateSignedDistanceField(m, vertexVelocities, bandwidth);
}

void MeshLevelSet::calculateSignedDistanceField(TriangleMesh &m, 
                                                std::vector<vmath::vec3> &vertexVelocities, 
                                                int bandwidth) {
    FLUIDSIM_ASSERT(vertexVelocities.size() == m.vertices.size());

    _mesh = m;
    _vertexVelocities = vertexVelocities;

    // we begin by initializing distances near the mesh, and figuring out intersection counts
    _computeExactBandDistanceField(bandwidth);

    // then propagate distances outwards to the rest of the grid
    _propagateDistanceField();

    // then figure out signs (inside/outside) from intersection counts
    if (_isSignCalculationEnabled) {
        _computeDistanceFieldSigns();
    }

    // then calculate other useful data from phi grid
    if (_isVelocityDataEnabled && !_isMinimalLevelSet) {
        _computeVelocityGrids();
    }
}

void MeshLevelSet::fastCalculateSignedDistanceField(TriangleMesh &m, int bandwidth) {
    std::vector<vmath::vec3> vertexVelocities(m.vertices.size());
    fastCalculateSignedDistanceField(m, vertexVelocities, bandwidth);
}

void MeshLevelSet::fastCalculateSignedDistanceField(TriangleMesh &m, 
                                                    std::vector<vmath::vec3> &vertexVelocities, 
                                                    int bandwidth) {
    FLUIDSIM_ASSERT(vertexVelocities.size() == m.vertices.size());

    _mesh = m;
    _vertexVelocities = vertexVelocities;

    // we begin by initializing distances near the mesh, and figuring out intersection counts
    _computeExactBandDistanceField(bandwidth);

    // this method skips propagating distances outside of exact band to speed up
    // calculation. Closest triangles will not be set for locations outside of
    // exact band.

    // then figure out signs (inside/outside) from intersection counts
    if (_isSignCalculationEnabled) {
        _computeDistanceFieldSigns();
    }

    // then calculate other useful data from phi grid
    if (_isVelocityDataEnabled && !_isMinimalLevelSet) {
        _computeVelocityGrids();
    }
}

void MeshLevelSet::calculateUnion(MeshLevelSet &levelset) {
    int isizeOther, jsizeOther, ksizeOther;
    levelset.getGridDimensions(&isizeOther, &jsizeOther, &ksizeOther);
    GridIndex gridOffsetOther = levelset.getGridOffset();

    // Merge mesh data
    TriangleMesh *meshOther = levelset.getTriangleMesh();
    int triIndexOffset = (int)_mesh.triangles.size();
    _mesh.append(*meshOther);

    std::vector<vmath::vec3> vertexVelocitiesOther = levelset.getVertexVelocities();
    FLUIDSIM_ASSERT(vertexVelocitiesOther.size() == meshOther->vertices.size());
    _vertexVelocities.insert(_vertexVelocities.end(), 
                             vertexVelocitiesOther.begin(), vertexVelocitiesOther.end());

    // Merge phi, closest triangle data, and mesh object data
    std::vector<MeshObject*> meshObjectsOther = levelset.getMeshObjects();
    int meshObjectIndexOffset = (int)_meshObjects.size();
    _meshObjects.insert(_meshObjects.end(), meshObjectsOther.begin(), 
                                            meshObjectsOther.end());

    VelocityDataGrid *otherData = levelset.getVelocityDataGrid();
    for(int k = 0; k < ksizeOther + 1; k++) {
        for(int j = 0; j < jsizeOther + 1; j++) {
            for(int i = 0; i < isizeOther + 1; i++) {
                GridIndex thisIndex(i + gridOffsetOther.i - _gridOffset.i,
                                    j + gridOffsetOther.j - _gridOffset.j,
                                    k + gridOffsetOther.k - _gridOffset.k);

                if (!Grid3d::isGridIndexInRange(thisIndex, _isize + 1, _jsize + 1, _ksize + 1)) {
                    continue;
                }

                if (levelset(i, j, k) < _phi(thisIndex)) {
                    if (fabs(levelset(i, j, k)) < fabs(_phi(thisIndex))) {
                        int tidx = levelset.getClosestTriangleIndex(i, j, k);
                        int midx = levelset.getClosestMeshObjectIndex(i, j, k);
                        if (tidx != -1) {
                            _closestTriangles.set(thisIndex, tidx + triIndexOffset);

                            if (midx != -1) {
                                _closestMeshObjects.set(thisIndex, midx + meshObjectIndexOffset);
                            }
                        }
                    }

                    _phi.set(thisIndex, levelset(i, j, k));
                }

                if (!isVelocityDataEnabled()) {
                    continue;
                }

                bool isBorder = Grid3d::isGridIndexOnBorder(thisIndex, _isize + 1, _jsize + 1, _ksize + 1) ||
                                Grid3d::isGridIndexOnBorder(i, j, k, isizeOther + 1, jsizeOther + 1, ksizeOther + 1);

                if (isBorder) {
                    if (Grid3d::isGridIndexInRange(thisIndex, _isize + 1, _jsize, _ksize) &&
                            Grid3d::isGridIndexInRange(i, j, k, isizeOther + 1, jsizeOther, ksizeOther)) {
                        _velocityData.field.addU(thisIndex, otherData->field.U(i, j, k));
                        _velocityData.weightU.add(thisIndex, otherData->weightU(i, j, k));
                    }

                    if (Grid3d::isGridIndexInRange(thisIndex, _isize, _jsize + 1, _ksize) &&
                            Grid3d::isGridIndexInRange(i, j, k, isizeOther, jsizeOther + 1, ksizeOther)) {
                        _velocityData.field.addV(thisIndex, otherData->field.V(i, j, k));
                        _velocityData.weightV.add(thisIndex, otherData->weightV(i, j, k));
                    }

                    if (Grid3d::isGridIndexInRange(thisIndex, _isize, _jsize, _ksize + 1) &&
                            Grid3d::isGridIndexInRange(i, j, k, isizeOther, jsizeOther, ksizeOther + 1)) {
                        _velocityData.field.addW(thisIndex, otherData->field.W(i, j, k));
                        _velocityData.weightW.add(thisIndex, otherData->weightW(i, j, k));
                    }
                } else {
                    _velocityData.field.addU(thisIndex, otherData->field.U(i, j, k));
                    _velocityData.weightU.add(thisIndex, otherData->weightU(i, j, k));
                    _velocityData.field.addV(thisIndex, otherData->field.V(i, j, k));
                    _velocityData.weightV.add(thisIndex, otherData->weightV(i, j, k));
                    _velocityData.field.addW(thisIndex, otherData->field.W(i, j, k));
                    _velocityData.weightW.add(thisIndex, otherData->weightW(i, j, k));
                }

            }
        }
    }
}

void MeshLevelSet::normalizeVelocityGrid() {
    FLUIDSIM_ASSERT(_isVelocityDataEnabled);

    ValidVelocityComponentGrid validVelocities(_isize, _jsize, _ksize);

    float eps = 1e-6f;
    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize + 1; i++) {
                float u = 0.0f;
                float uweight = _velocityData.weightU(i, j, k);
                if (uweight > eps) {
                    u = _velocityData.field.U(i, j, k) / uweight;
                    validVelocities.validU.set(i, j, k, true);
                }

                _velocityData.field.setU(i, j, k, u);
                _velocityData.weightU.set(i, j, k, 1.0f);
            }
        }
    }

    for(int k = 0; k < _ksize; k++) {
        for(int j = 0; j < _jsize + 1; j++) {
            for(int i = 0; i < _isize; i++) {
                float v = 0.0f;
                float vweight = _velocityData.weightV(i, j, k);
                if (vweight > eps) {
                    v = _velocityData.field.V(i, j, k) / vweight;
                    validVelocities.validV.set(i, j, k, true);
                }

                _velocityData.field.setV(i, j, k, v);
                _velocityData.weightV.set(i, j, k, 1.0f);
            }
        }
    }

    for(int k = 0; k < _ksize + 1; k++) {
        for(int j = 0; j < _jsize; j++) {
            for(int i = 0; i < _isize; i++) {
                float w = 0.0f;
                float wweight = _velocityData.weightW(i, j, k);
                if (wweight > eps) {
                    w = _velocityData.field.W(i, j, k) / wweight;
                    validVelocities.validW.set(i, j, k, true);
                }

                _velocityData.field.setW(i, j, k, w);
                _velocityData.weightW.set(i, j, k, 1.0f);
            }
        }
    }

    _velocityData.field.extrapolateVelocityField(
            validVelocities, _numVelocityExtrapolationLayers
    );
}

void MeshLevelSet::negate() {
    for(int k = 0; k < _phi.depth; k++) {
        for(int j = 0; j < _phi.height; j++) {
            for(int i = 0; i < _phi.width; i++) {
                _phi.set(i, j, k, -_phi(i, j, k));
            }
        }
    }

    if (_isVelocityDataEnabled) {
        _computeVelocityGrids();
    }
}

void MeshLevelSet::reset() {
    _mesh = TriangleMesh();
    _vertexVelocities.clear();
    _phi.fill(getDistanceUpperBound());
    _closestTriangles.fill(-1);
    _velocityData.reset();
    _closestMeshObjects.fill(-1);
    _meshObjects.clear();
}

void MeshLevelSet::setGridOffset(GridIndex g) {
    _gridOffset = g;
    _positionOffset = Grid3d::GridIndexToPosition(g, _dx);
}

GridIndex MeshLevelSet::getGridOffset() {
    return _gridOffset;
}

vmath::vec3 MeshLevelSet::getPositionOffset() {
    return _positionOffset;
}

void MeshLevelSet::enableVelocityData() {
    _isVelocityDataEnabled = true;
}

void MeshLevelSet::disableVelocityData() {
    _isVelocityDataEnabled = false;
}

bool MeshLevelSet::isVelocityDataEnabled() {
    return _isVelocityDataEnabled;
}

void MeshLevelSet::enableMultiThreading() {
    _isMultiThreadingEnabled = true;
}

void MeshLevelSet::disableMultiThreading() {
    _isMultiThreadingEnabled = false;
}

bool MeshLevelSet::isMultiThreadingEnabled() {
    return _isMultiThreadingEnabled;
}

void MeshLevelSet::enableSignCalculation() {
    _isSignCalculationEnabled = true;
}

void MeshLevelSet::disableSignCalculation() {
    _isSignCalculationEnabled = false;
}

bool MeshLevelSet::isSignCaclulationEnabled() {
    return _isSignCalculationEnabled;
}

float MeshLevelSet::getDistanceUpperBound() {
    return (_phi.width + _phi.height + _phi.depth) * _dx;
}

void MeshLevelSet::_computeExactBandDistanceFieldThread(int startidx, int endidx, 
                                                        int bandwidth, int splitdir) {

    int isize = _phi.width;
    int jsize = _phi.height;
    int ksize = _phi.depth;

    int U = 0; int V = 1; int W = 2;

    vmath::vec3 minp, maxp;
    if (splitdir == U) {
        minp = vmath::vec3(startidx * _dx, 0.0, 0.0);
        maxp = vmath::vec3((endidx - 1) * _dx, jsize * _dx, ksize * _dx);
    } else if (splitdir == V) {
        minp = vmath::vec3(0.0, startidx * _dx, 0.0);
        maxp = vmath::vec3(isize * _dx, (endidx - 1) * _dx, ksize * _dx);
    } else if (splitdir == W) {
        minp = vmath::vec3(0.0, 0.0, startidx * _dx);
        maxp = vmath::vec3(isize * _dx, jsize * _dx, (endidx - 1) * _dx);
    }
    float eps = 1e-6;
    AABB bbox(minp, maxp);
    bbox.expand(2 * (bandwidth * _dx + eps));
    minp = bbox.getMinPoint();
    maxp = bbox.getMaxPoint();

    Triangle t;
    double invdx = 1.0 / _dx;
    for(size_t tidx = 0; tidx < _mesh.triangles.size(); tidx++) {
        t = _mesh.triangles[tidx];
        vmath::vec3 p = _mesh.vertices[t.tri[0]] - _positionOffset;
        vmath::vec3 q = _mesh.vertices[t.tri[1]] - _positionOffset;
        vmath::vec3 r = _mesh.vertices[t.tri[2]] - _positionOffset;

        if (splitdir == U) {
            if ((p.x < minp.x && q.x < minp.x && r.x < minp.x) || 
                    (p.x > maxp.x && q.x > maxp.x && r.x > maxp.x)) {
                continue;
            }
        } else if (splitdir == V) {
            if ((p.y < minp.z && q.z < minp.z && r.z < minp.z) || 
                    (p.z > maxp.z && q.z > maxp.z && r.z > maxp.z)) {
                continue;
            }
        } else if (splitdir == W) {
            if ((p.x < minp.x && q.x < minp.x && r.x < minp.x) || 
                    (p.x > maxp.x && q.x > maxp.x && r.x > maxp.x)) {
                continue;
            }
        }

        double fip = (double)p.x * invdx;
        double fjp = (double)p.y * invdx; 
        double fkp = (double)p.z * invdx;

        double fiq = (double)q.x * invdx;
        double fjq = (double)q.y * invdx;
        double fkq = (double)q.z * invdx;

        double fir = (double)r.x * invdx;
        double fjr = (double)r.y * invdx;
        double fkr = (double)r.z * invdx;

        int i0 = _clamp(int(fmin(fip, fmin(fiq, fir))) - bandwidth, 0, isize - 1);
        int j0 = _clamp(int(fmin(fjp, fmin(fjq, fjr))) - bandwidth, 0, jsize - 1);
        int k0 = _clamp(int(fmin(fkp, fmin(fkq, fkr))) - bandwidth, 0, ksize - 1);

        int i1 = _clamp(int(fmax(fip, fmax(fiq, fir))) + bandwidth + 1, 0, isize - 1);
        int j1 = _clamp(int(fmax(fjp, fmax(fjq, fjr))) + bandwidth + 1, 0, jsize - 1);
        int k1 = _clamp(int(fmax(fkp, fmax(fkq, fkr))) + bandwidth + 1, 0, ksize - 1);

        if (splitdir == U) {
            i0 = fmax(i0, startidx);
            i1 = fmin(i1, endidx - 1);
        } else if (splitdir == V) {
            j0 = fmax(j0, startidx);
            j1 = fmin(j1, endidx - 1);
        } else if (splitdir == W) {
            k0 = fmax(k0, startidx);
            k1 = fmin(k1, endidx - 1);
        }

        for(int k = k0; k <= k1; k++) {
            for(int j = j0; j <= j1; j++) { 
                for(int i = i0; i <= i1; i++){
                    vmath::vec3 gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                    float d = _pointToTriangleDistance(gpos, p, q, r);
                    if (d < _phi(i, j, k)) {
                        if (!_isMinimalLevelSet && fabs(d) < fabs(_phi(i, j, k))) {
                            _closestTriangles.set(i, j, k, (int)tidx);
                        }
                        _phi.set(i, j, k, d);
                    }
                }
            }
        }
    }

}

void MeshLevelSet::_computeExactBandDistanceField(int bandwidth) {
    if (_isMultiThreadingEnabled) {
        _computeExactBandDistanceFieldMultiThreaded(bandwidth);
    } else {
        _computeExactBandDistanceFieldSingleThreaded(bandwidth);
    }
}

void MeshLevelSet::_computeExactBandDistanceFieldMultiThreaded(int bandwidth) {
    _phi.fill(getDistanceUpperBound());
    _closestTriangles.fill(-1);
    _closestMeshObjects.fill(-1);

    if (_mesh.vertices.empty()) {
        return;
    }

    int isize = _phi.width;
    int jsize = _phi.height;
    int ksize = _phi.depth;
    int meshObjectIdx = (int)_meshObjects.size() - 1;

    vmath::vec3 minp = _mesh.vertices[0] - _positionOffset;
    vmath::vec3 maxp = _mesh.vertices[0] - _positionOffset;
    for (size_t i = 0; i < _mesh.vertices.size(); i++) {
        vmath::vec3 p = _mesh.vertices[i] - _positionOffset;
        minp.x = fmin(minp.x, p.x);
        minp.y = fmin(minp.y, p.y);
        minp.z = fmin(minp.z, p.z);
        maxp.x = fmax(maxp.x, p.x);
        maxp.y = fmax(maxp.y, p.y);
        maxp.z = fmax(maxp.z, p.z);
    }
    vmath::vec3 diff = maxp - minp;

    int U = 0; int V = 1; int W = 2;
    int splitdir = U;
    if (diff.x > diff.y) {
        if (diff.x > diff.z) {
            splitdir = U;
        } else {
            splitdir = W;
        }
    } else {
        if (diff.y > diff.z) {
            splitdir = V;
        } else {
            splitdir = W;
        }
    }

    int i1 = 0;
    int i2 = 0;
    GridIndex gmin = Grid3d::positionToGridIndex(minp, _dx);
    GridIndex gmax = Grid3d::positionToGridIndex(maxp, _dx);
    if (splitdir == U) {
        i1 = fmax(gmin.i - bandwidth, 0);
        i2 = fmin(gmax.i + 1 + bandwidth, _phi.width);
    } else if (splitdir == V) {
        i1 = fmax(gmin.j - bandwidth, 0);
        i2 = fmin(gmax.j + 1 + bandwidth, _phi.height);
    } else if (splitdir == W) {
        i1 = fmax(gmin.k - bandwidth, 0);
        i2 = fmin(gmax.k + 1 + bandwidth, _phi.depth);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, i2 - i1);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(i1, i2, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&MeshLevelSet::_computeExactBandDistanceFieldThread, this,
                                 intervals[i], intervals[i + 1], bandwidth, splitdir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    if (!_isMinimalLevelSet) { 
        for(int k = 0; k < ksize; k++) {
            for(int j = 0; j < jsize; j++) {
                for(int i = 0; i < isize; i++) {
                    if (_closestTriangles(i, j, k) != -1) {
                        _closestMeshObjects.set(i, j, k, meshObjectIdx);
                    }
                }
            }
        }
    }
}

void MeshLevelSet::_computeExactBandDistanceFieldSingleThreaded(int bandwidth) {
    _phi.fill(getDistanceUpperBound());
    _closestTriangles.fill(-1);
    _closestMeshObjects.fill(-1);

    if (_mesh.vertices.empty()) {
        return;
    }

    int isize = _phi.width;
    int jsize = _phi.height;
    int ksize = _phi.depth;
    int meshObjectIdx = (int)_meshObjects.size() - 1;

    Triangle t;
    double invdx = 1.0 / _dx;
    for(size_t tidx = 0; tidx < _mesh.triangles.size(); tidx++) {
        t = _mesh.triangles[tidx];
        vmath::vec3 p = _mesh.vertices[t.tri[0]] - _positionOffset;
        vmath::vec3 q = _mesh.vertices[t.tri[1]] - _positionOffset;
        vmath::vec3 r = _mesh.vertices[t.tri[2]] - _positionOffset;

        double fip = (double)p.x * invdx;
        double fjp = (double)p.y * invdx; 
        double fkp = (double)p.z * invdx;

        double fiq = (double)q.x * invdx;
        double fjq = (double)q.y * invdx;
        double fkq = (double)q.z * invdx;

        double fir = (double)r.x * invdx;
        double fjr = (double)r.y * invdx;
        double fkr = (double)r.z * invdx;

        int i0 = _clamp(int(fmin(fip, fmin(fiq, fir))) - bandwidth, 0, isize - 1);
        int j0 = _clamp(int(fmin(fjp, fmin(fjq, fjr))) - bandwidth, 0, jsize - 1);
        int k0 = _clamp(int(fmin(fkp, fmin(fkq, fkr))) - bandwidth, 0, ksize - 1);

        int i1 = _clamp(int(fmax(fip, fmax(fiq, fir))) + bandwidth + 1, 0, isize - 1);
        int j1 = _clamp(int(fmax(fjp, fmax(fjq, fjr))) + bandwidth + 1, 0, jsize - 1);
        int k1 = _clamp(int(fmax(fkp, fmax(fkq, fkr))) + bandwidth + 1, 0, ksize - 1);

        for(int k = k0; k <= k1; k++) {
            for(int j = j0; j <= j1; j++) { 
                for(int i = i0; i <= i1; i++){
                    vmath::vec3 gpos = Grid3d::GridIndexToPosition(i, j, k, _dx);
                    float d = _pointToTriangleDistance(gpos, p, q, r);
                    if (d < _phi(i, j, k)) {
                        if (!_isMinimalLevelSet && fabs(d) < fabs(_phi(i, j, k))) {
                            _closestTriangles.set(i, j, k, (int)tidx);
                        }
                        _phi.set(i, j, k, d);
                    }
                }
            }
        }
    }

    if (!_isMinimalLevelSet) { 
        for(int k = 0; k < ksize; k++) {
            for(int j = 0; j < jsize; j++) {
                for(int i = 0; i < isize; i++) {
                    if (_closestTriangles(i, j, k) != -1) {
                        _closestMeshObjects.set(i, j, k, meshObjectIdx);
                    }
                }
            }
        }
    }
}

void MeshLevelSet::_propagateDistanceField() {
    int isize = _phi.width;
    int jsize = _phi.height;
    int ksize = _phi.depth;

    std::vector<GridIndex> queue;
    queue.reserve(isize * jsize * ksize);
    Array3d<bool> searchGrid(isize, jsize, ksize, false);
    for(int k = 0; k < ksize; k++) {
        for(int j = 0; j < jsize; j++) {
            for(int i = 0; i < isize; i++) {
                if (_closestTriangles(i, j, k) != -1) {
                    searchGrid.set(i, j, k, true);
                    queue.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    int unknownidx = (int)queue.size();
    int startidx = 0;
    GridIndex g, n, nbs[6];
    while (startidx < (int)queue.size()) {
        g = queue[startidx];
        startidx++;

        Grid3d::getNeighbourGridIndices6(g, nbs);
        for (int nidx = 0; nidx < 6; nidx++) {
            n = nbs[nidx];
            if (Grid3d::isGridIndexInRange(n, isize, jsize, ksize) && !searchGrid(n)) {
                searchGrid.set(n, true);
                queue.push_back(n);
            }
        }
    }

    vmath::vec3 gpos;
    Triangle t;
    startidx = unknownidx;
    while (startidx < (int)queue.size()) {
        g = queue[startidx];
        startidx++;

        gpos = Grid3d::GridIndexToPosition(g, _dx);
        Grid3d::getNeighbourGridIndices6(g, nbs);
        for (int nidx = 0; nidx < 6; nidx++) {
            n = nbs[nidx];
            if (Grid3d::isGridIndexInRange(n, isize, jsize, ksize) && _closestTriangles(n) != -1) {
                t = _mesh.triangles[_closestTriangles(n)];
                double dist = _pointToTriangleDistance(gpos, _mesh.vertices[t.tri[0]] - _positionOffset, 
                                                             _mesh.vertices[t.tri[1]] - _positionOffset, 
                                                             _mesh.vertices[t.tri[2]] - _positionOffset);
                if (dist < _phi(g)) {
                    _phi.set(g, dist);
                    _closestTriangles.set(g, _closestTriangles(n));
                    _closestTriangles.set(g, _closestMeshObjects(n));
                }
            }
        }
    }
}

void MeshLevelSet::_computeDistanceFieldSigns() {
    int isize = _phi.width;
    int jsize = _phi.height;
    int ksize = _phi.depth;
    Array3d<bool> nodes(isize, jsize, ksize, false);

    TriangleMesh tempMesh = _mesh;
    tempMesh.translate(-_positionOffset);
    MeshUtils::getGridNodesInsideTriangleMesh(tempMesh, _dx, nodes);

    for(int k = 0; k < ksize; k++) {
        for(int j = 0; j < jsize; j++) {
            for(int i = 0; i < isize; i++) {
                if (nodes(i, j, k)) {
                    _phi.set(i, j, k, -_phi(i, j, k));
                }
            }
        }
    }
}

void MeshLevelSet::_computeVelocityGridThread(int startidx, int endidx, 
                                              bool isStatic, int dir) {
    int U = 0; int V = 1; int W = 2;

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            float weight = getFaceWeightU(g);
            if (weight > 0.0f) {
                vmath::vec3 v;
                if (!isStatic) {
                    vmath::vec3 p = Grid3d::FaceIndexToPositionU(g, _dx);
                    v = getNearestVelocity(p + _positionOffset);
                }
                _velocityData.field.setU(g, weight * v.x);
                _velocityData.weightU.set(g, weight);
            }
        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            float weight = getFaceWeightV(g);
            if (weight > 0.0f) {
                vmath::vec3 v;
                if (!isStatic) {
                    vmath::vec3 p = Grid3d::FaceIndexToPositionV(g, _dx);
                    v = getNearestVelocity(p + _positionOffset);
                }
                _velocityData.field.setV(g, weight * v.y);
                _velocityData.weightV.set(g, weight);
            }
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            float weight = getFaceWeightW(g);
            if (weight > 0.0f) {
                vmath::vec3 v;
                if (!isStatic) {
                    vmath::vec3 p = Grid3d::FaceIndexToPositionW(g, _dx);
                    v = getNearestVelocity(p + _positionOffset);
                }
                _velocityData.field.setW(g, weight * v.z);
                _velocityData.weightW.set(g, weight);
            }
        }

    }

}

void MeshLevelSet::_computeVelocityGridMT(bool isStatic, int dir) {
    int U = 0; int V = 1; int W = 2;
    int gridsize = 0;
    if (dir == U) {
        gridsize = (_isize + 1) * _jsize * _ksize;
    } else if (dir == V) {
        gridsize = _isize * (_jsize + 1) * _ksize;
    } else if (dir == W) {
        gridsize = _isize * _jsize * (_ksize + 1);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&MeshLevelSet::_computeVelocityGridThread, this,
                                 intervals[i], intervals[i + 1], isStatic, dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void MeshLevelSet::_computeVelocityGrids() {
    if (_isMultiThreadingEnabled) {
        _computeVelocityGridsMultiThreaded();
    } else {
        _computeVelocityGridsSingleThreaded();
    }
}

void MeshLevelSet::_computeVelocityGridsMultiThreaded() {
    _velocityData.reset();

    bool isStatic = true;
    for (size_t i = 0; i < _vertexVelocities.size(); i++) {
        vmath::vec3 v = _vertexVelocities[i];
        if (fabs(v.x) > 0.0f || fabs(v.y) > 0.0f || fabs(v.z) > 0.0f) {
            isStatic = false;
            break;
        }
    }

    int U = 0; int V = 1; int W = 2;
    _computeVelocityGridMT(isStatic, U);
    _computeVelocityGridMT(isStatic, V);
    _computeVelocityGridMT(isStatic, W);
}

void MeshLevelSet::_computeVelocityGridsSingleThreaded() {
    _velocityData.reset();

    bool isStatic = true;
    for (size_t i = 0; i < _vertexVelocities.size(); i++) {
        vmath::vec3 v = _vertexVelocities[i];
        if (fabs(v.x) > 0.0f || fabs(v.y) > 0.0f || fabs(v.z) > 0.0f) {
            isStatic = false;
            break;
        }
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                float weight = getFaceWeightU(i, j, k);
                if (weight > 0.0f) {
                    vmath::vec3 v;
                    if (!isStatic) {
                        vmath::vec3 p = Grid3d::FaceIndexToPositionU(i, j, k, _dx);
                        v = getNearestVelocity(p + _positionOffset);
                    }
                    _velocityData.field.setU(i, j, k, weight * v.x);
                    _velocityData.weightU.set(i, j, k, weight);
                }
            }
        }
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize; i++) {
                float weight = getFaceWeightV(i, j, k);
                if (weight > 0.0f) {
                    vmath::vec3 v;
                    if (!isStatic) {
                        vmath::vec3 p = Grid3d::FaceIndexToPositionV(i, j, k, _dx);
                        v = getNearestVelocity(p + _positionOffset);
                    }
                    _velocityData.field.setV(i, j, k, weight * v.y);
                    _velocityData.weightV.set(i, j, k, weight);
                }
            }
        }
    }

    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                float weight = getFaceWeightW(i, j, k);
                if (weight > 0.0f) {
                    vmath::vec3 v;
                    if (!isStatic) {
                        vmath::vec3 p = Grid3d::FaceIndexToPositionW(i, j, k, _dx);
                        v = getNearestVelocity(p + _positionOffset);
                    }
                    _velocityData.field.setW(i, j, k, weight * v.z);
                    _velocityData.weightW.set(i, j, k, weight);
                }
            }
        }
    }
}

float MeshLevelSet::_getCellWeight(int i, int j, int k) {
    float phi000 = _phi(i, j, k);
    float phi001 = _phi(i, j, k + 1);
    float phi010 = _phi(i, j + 1, k);
    float phi011 = _phi(i, j + 1, k + 1);
    float phi100 = _phi(i + 1, j, k);
    float phi101 = _phi(i + 1, j, k + 1);
    float phi110 = _phi(i + 1, j + 1, k);
    float phi111 = _phi(i + 1, j + 1, k + 1);

    float weight = 0.0f;
    if (phi000 < 0 && phi001 < 0 && phi010 < 0 && phi011 < 0 &&
            phi100 < 0 && phi101 < 0 && phi110 < 0 && phi111 < 0) {
        weight = 1.0f;
    } else if (phi000 >= 0 && phi001 >= 0 && phi010 >= 0 && phi011 >= 0 &&
               phi100 >= 0 && phi101 >= 0 && phi110 >= 0 && phi111 >= 0) {
        weight = 0.0f;
    } else {
        weight = LevelsetUtils::volumeFraction(phi000, phi100, phi010, phi110, 
                                               phi001, phi101, phi011, phi111);
    }

    return weight;
}

// find distance x0 is from triangle x1-x2-x3
float MeshLevelSet::_pointToTriangleDistance(vmath::vec3 x0, vmath::vec3 x1, 
                                                             vmath::vec3 x2, 
                                                             vmath::vec3 x3) {
    // first find barycentric coordinates of closest point on infinite plane
    vmath::vec3 x13 = x1 - x3;
    vmath::vec3 x23 = x2 - x3;
    vmath::vec3 x03 = x0 - x3;

    float m13 = vmath::lengthsq(x13);
    float m23 = vmath::lengthsq(x23); 
    float d = vmath::dot(x13, x23);
    float invdet = 1.0f / fmax(m13 * m23 - d * d, 1e-30f);
    float a = vmath::dot(x13, x03);
    float b = vmath::dot(x23, x03);

    // the barycentric coordinates themselves
    float w23 = invdet * (m23 * a - d * b);
    float w31 = invdet * (m13 * b - d * a);
    float w12 = 1 - w23 - w31;
    if (w23 >= 0 && w31 >= 0 && w12 >= 0) { // if we're inside the triangle
        return vmath::length(x0 - (w23 * x1 + w31 * x2 + w12 * x3)); 
    } else { 
        // we have to clamp to one of the edges
        if (w23 > 0) { 
            // this rules out edge 2-3 for us
            float d1 = _pointToSegmentDistance(x0, x1, x2);
            float d2 = _pointToSegmentDistance(x0, x1, x3);
            return fmin(d1, d2);
        } else if(w31>0) { 
            // this rules out edge 1-3
            float d1 = _pointToSegmentDistance(x0, x1, x2);
            float d2 = _pointToSegmentDistance(x0, x2, x3);
            return fmin(d1, d2);
        } else { 
            // w12 must be >0, ruling out edge 1-2
            float d1 = _pointToSegmentDistance(x0, x1, x3);
            float d2 = _pointToSegmentDistance(x0, x2, x3);
            return fmin(d1, d2);
        }
    }
}

vmath::vec3 MeshLevelSet::_pointToTriangleVelocity(vmath::vec3 x0, int triangleIdx) {
    Triangle t = _mesh.triangles[triangleIdx];
    vmath::vec3 v1 = _vertexVelocities[t.tri[0]];
    vmath::vec3 v2 = _vertexVelocities[t.tri[1]];
    vmath::vec3 v3 = _vertexVelocities[t.tri[2]];

    float eps = 1e-6f;
    if (fabs(v1.x) < eps && fabs(v1.y) < eps && fabs(v1.z) < eps &&
            fabs(v2.x) < eps && fabs(v2.y) < eps && fabs(v2.z) < eps &&
            fabs(v3.x) < eps && fabs(v3.y) < eps && fabs(v3.z) < eps) {
        return vmath::vec3(0.0, 0.0, 0.0);
    }

    vmath::vec3 x1 = _mesh.vertices[t.tri[0]] - _positionOffset;
    vmath::vec3 x2 = _mesh.vertices[t.tri[1]] - _positionOffset;
    vmath::vec3 x3 = _mesh.vertices[t.tri[2]] - _positionOffset;

    // first find barycentric coordinates of closest point on infinite plane
    vmath::vec3 x13 = x1 - x3;
    vmath::vec3 x23 = x2 - x3;
    vmath::vec3 x03 = x0 - x3;

    float m13 = vmath::lengthsq(x13);
    float m23 = vmath::lengthsq(x23); 
    float d = vmath::dot(x13, x23);
    float invdet = 1.0f / fmax(m13 * m23 - d * d, 1e-30f);
    float a = vmath::dot(x13, x03);
    float b = vmath::dot(x23, x03);

    // the barycentric coordinates themselves
    float w23 = invdet * (m23 * a - d * b);
    float w31 = invdet * (m13 * b - d * a);
    float w12 = 1 - w23 - w31;
    if (w23 >= 0 && w31 >= 0 && w12 >= 0) { // if we're inside the triangle
        return w23 * v1 + w31 * v2 + w12 * v3; 
    } else { 
        // we have to clamp to one of the edges
        if (w23 > 0) { 
            // this rules out edge 2-3 for us
            float d1, d2;
            vmath::vec3 vel1 = _pointToSegmentVelocity(x0, x1, x2, v1, v2, &d1);
            vmath::vec3 vel2 = _pointToSegmentVelocity(x0, x1, x3, v1, v3, &d2);
            if (d1 < d2) {
                return vel1;
            } else {
                return vel2;
            }
        } else if(w31>0) { 
            // this rules out edge 1-3
            float d1, d2;
            vmath::vec3 vel1 = _pointToSegmentVelocity(x0, x1, x2, v1, v2, &d1);
            vmath::vec3 vel2 = _pointToSegmentVelocity(x0, x2, x3, v2, v3, &d2);
            if (d1 < d2) {
                return vel1;
            } else {
                return vel2;
            }
        } else { 
            // w12 must be >0, ruling out edge 1-2
            float d1, d2;
            vmath::vec3 vel1 = _pointToSegmentVelocity(x0, x1, x3, v1, v3, &d1);
            vmath::vec3 vel2 = _pointToSegmentVelocity(x0, x2, x3, v2, v3, &d2);
            if (d1 < d2) {
                return vel1;
            } else {
                return vel2;
            }
        }
    }
}

// robust test of (x0,y0) in the triangle (x1,y1)-(x2,y2)-(x3,y3)
// if true is returned, the barycentric coordinates are set in a,b,c.
bool MeshLevelSet::_getBarycentricCoordinates(
            double x0, double y0, 
            double x1, double y1, double x2, double y2, double x3, double y3,
            double *a, double *b, double *c) {
    x1 -= x0; 
    x2 -= x0; 
    x3 -= x0;
    y1 -= y0; 
    y2 -= y0; 
    y3 -= y0;

    double oa;
    int signa = _orientation(x2, y2, x3, y3, &oa);
    if (signa == 0) {
        return false;
    }

    double ob;
    int signb = _orientation(x3, y3, x1, y1, &ob);
    if(signb != signa) {
        return false;
    }

    double oc;
    int signc = _orientation(x1, y1, x2, y2, &oc);
    if(signc != signa) {
        return false;
    }

    double sum = oa + ob + oc;
    FLUIDSIM_ASSERT(sum != 0); // if the SOS signs match and are nonkero, there's no way all of a, b, and c are zero.
    double invsum = 1.0 / sum;

    *a = oa * invsum;
    *b = ob * invsum;
    *c = oc * invsum;

    return true;
}

// find distance x0 is from segment x1-x2
float MeshLevelSet::_pointToSegmentDistance(vmath::vec3 x0, vmath::vec3 x1, vmath::vec3 x2) {
    vmath::vec3 dx = x2 - x1;
    double m2 = vmath::lengthsq(dx);
    // find parameter value of closest point on segment
    float s12 = (float)(vmath::dot(x2 - x0, dx) / m2);
    if (s12 < 0) {
        s12 = 0;
    } else if (s12 > 1) {
        s12 = 1;
    }

    // and find the distance
    return vmath::length(x0 - (s12 * x1 + (1 - s12) * x2));
}

vmath::vec3 MeshLevelSet::_pointToSegmentVelocity(vmath::vec3 x0, 
                                                  vmath::vec3 x1, vmath::vec3 x2, 
                                                  vmath::vec3 v1, vmath::vec3 v2, 
                                                  float *distance) {
    vmath::vec3 dx = x2 - x1;
    double m2 = vmath::lengthsq(dx);
    // find parameter value of closest point on segment
    float s12 = (float)(vmath::dot(x2 - x0, dx) / m2);
    if (s12 < 0) {
        s12 = 0;
    } else if (s12 > 1) {
        s12 = 1;
    }

    *distance = vmath::length(x0 - (s12 * x1 + (1 - s12) * x2));
    vmath::vec3 velocity = s12 * v1 + (1 - s12) * v2;

    return velocity;
}

// calculate twice signed area of triangle (0,0)-(x1,y1)-(x2,y2)
// return an SOS-determined sign (-1, +1, or 0 only if it's a truly degenerate triangle)
int MeshLevelSet::_orientation(double x1, double y1, double x2, double y2, 
                              double *twiceSignedArea) {
    *twiceSignedArea = y1 * x2 - x1 * y2;
    if(*twiceSignedArea > 0) {
        return 1;
    } else if (*twiceSignedArea < 0) {
        return -1;
    } else if (y2 > y1) {
        return 1;
    } else if (y2 < y1) {
        return -1;
    } else if (x1 > x2) {
        return 1;
    } else if (x1 < x2) {
        return -1; 
    } else { 
        return 0; // only true when x1==x2 and y1==y2
    }
}
