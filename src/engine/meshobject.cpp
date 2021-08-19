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

#include "meshobject.h"

#include "meshutils.h"

MeshObject::MeshObject() {
}

MeshObject::MeshObject(int i, int j, int k, double dx) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx) {
}

MeshObject::~MeshObject() {
}

void MeshObject::resizeGrid(int isize, int jsize, int ksize, double dx) {
    _isize = isize;
    _jsize = jsize;
    _ksize = ksize;
    _dx = dx;
}

void MeshObject::getGridDimensions(int *i, int *j, int *k) { 
    *i = _isize; *j = _jsize; *k = _ksize; 
}

void MeshObject::updateMeshStatic(TriangleMesh meshCurrent) {
    _meshPrevious = meshCurrent;
    _meshCurrent = meshCurrent;
    _meshNext = meshCurrent;
    _vertexTranslationsCurrent = std::vector<vmath::vec3>(meshCurrent.vertices.size());
    _vertexTranslationsNext = std::vector<vmath::vec3>(meshCurrent.vertices.size());
    _isAnimated = false;
    _isChangingTopology = false;
    _isRigid = true;
}

void MeshObject::updateMeshAnimated(TriangleMesh meshPrevious, 
                                    TriangleMesh meshCurrent, 
                                    TriangleMesh meshNext) {

    _meshPrevious = meshPrevious;
    _meshCurrent = meshCurrent;
    _meshNext = meshNext;
    _isChangingTopology = false;

    _vertexTranslationsCurrent = std::vector<vmath::vec3>(meshCurrent.vertices.size());
    if (_isTopologyConsistent(meshPrevious, meshCurrent)) {
        for (size_t i = 0; i < meshCurrent.vertices.size(); i++) {
            _vertexTranslationsCurrent[i] = _meshCurrent.vertices[i] - _meshPrevious.vertices[i];
        }
    } else {
        _isChangingTopology = true;
    }

    _vertexTranslationsNext = std::vector<vmath::vec3>(meshNext.vertices.size());
    if (_isTopologyConsistent(meshNext, meshCurrent)) {
        for (size_t i = 0; i < meshCurrent.vertices.size(); i++) {
            _vertexTranslationsNext[i] = _meshNext.vertices[i] - _meshCurrent.vertices[i];
        }
    } else {
        _isChangingTopology = true;
    }

    if (_isChangingTopology) {
        _isRigid = false;
    } else {
        _isRigid = _isRigidBody(meshPrevious, meshCurrent) && _isRigidBody(meshNext, meshCurrent);
    }

    _isAnimated = true;
}

void MeshObject::getCells(std::vector<GridIndex> &cells) {
        getCells(0.0f, cells);
}

void MeshObject::getCells(float frameInterpolation, std::vector<GridIndex> &cells) {
    if (_isInversed) {
        _getInversedCells(frameInterpolation, cells);
    }

    TriangleMesh m = getMesh(frameInterpolation);
    Array3d<bool> nodes(_isize + 1, _jsize + 1, _ksize + 1, false);
    MeshUtils::getGridNodesInsideTriangleMesh(m, _dx, nodes);

    Array3d<bool> cellGrid(_isize, _jsize, _ksize, false);
    GridIndex nodeCells[8];
    for (int k = 0; k < nodes.depth; k++) {
        for (int j = 0; j < nodes.height; j++) {
            for (int i = 0; i < nodes.width; i++) {
                if (!nodes(i, j, k)) {
                    continue;
                }

                Grid3d::getVertexGridIndexNeighbours(i, j, k, nodeCells);
                for (int nidx = 0; nidx < 8; nidx++) {
                    if (cellGrid.isIndexInRange(nodeCells[nidx])) {
                        cellGrid.set(nodeCells[nidx], true);
                    }
                }
            }
        }
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (cellGrid(i, j, k)) {
                    cells.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    cells.shrink_to_fit();
}

bool MeshObject::isAnimated() {
    return _isAnimated;
}

bool MeshObject::isRigidBody() {
    return _isRigid;
}

void MeshObject::clearObjectStatus() {
    _isObjectStateChanged = false;
}

TriangleMesh MeshObject::getMesh() {
    return _meshCurrent;
}

TriangleMesh MeshObject::getMesh(float frameInterpolation) {
    // TODO: update this method to improve/handle rigid, deformable, or
    // topology-changing meshes

    if (_isChangingTopology) {
        return getMesh();
    }

    frameInterpolation = fmax(0.0f, frameInterpolation);
    frameInterpolation = fmin(1.0f, frameInterpolation);

    TriangleMesh outmesh = _meshCurrent;
    for (size_t i = 0; i < _meshCurrent.vertices.size(); i++) {
        vmath::vec3 v1 = _meshCurrent.vertices[i];
        vmath::vec3 v2 = _meshNext.vertices[i];
        outmesh.vertices[i] = v1 + frameInterpolation * (v2 - v1);
    }

    return outmesh;
}

std::vector<vmath::vec3> MeshObject::getVertexTranslations() {
    return _vertexTranslationsCurrent;
}

std::vector<vmath::vec3> MeshObject::getVertexTranslations(float frameInterpolation) {
    if (_isChangingTopology) {
        return getVertexTranslations();
    }

    frameInterpolation = fmax(0.0f, frameInterpolation);
    frameInterpolation = fmin(1.0f, frameInterpolation);

    std::vector<vmath::vec3> transout(_vertexTranslationsCurrent.size(), vmath::vec3());
    for (size_t i = 0; i < _vertexTranslationsCurrent.size(); i++) {
        vmath::vec3 p1 = _vertexTranslationsCurrent[i];
        vmath::vec3 p2 = _vertexTranslationsNext[i];
        transout[i] = p1 + frameInterpolation * (p2 - p1);
    }

    return transout;
}

std::vector<vmath::vec3> MeshObject::getVertexVelocities(double dt) {
    return getVertexVelocities(dt, 0.0f);
}

std::vector<vmath::vec3> MeshObject::getVertexVelocities(double dt, float frameInterpolation) {
    std::vector<vmath::vec3> velocities = getVertexTranslations(frameInterpolation);

    double eps = 1e-10;
    if (dt < eps) {
        velocities = std::vector<vmath::vec3>(velocities.size());
        return velocities;
    }

    double invdt = 1.0 / dt;
    for (size_t i = 0; i < velocities.size(); i++) {
        velocities[i] *= invdt;
    }

    return velocities;
}

std::vector<vmath::vec3> MeshObject::getFrameVertexVelocities(int frameno, double dt) {
    std::vector<vmath::vec3> velocities = _vertexTranslationsCurrent;

    double eps = 1e-10;
    if (dt < eps) {
        velocities = std::vector<vmath::vec3>(velocities.size());
        return velocities;
    }

    double invdt = 1.0 / dt;
    for (size_t i = 0; i < velocities.size(); i++) {
        velocities[i] *= invdt;
    }

    return velocities;
}

void MeshObject::getMeshLevelSet(double dt, float frameInterpolation, int exactBand, 
                                 MeshLevelSet &levelset) {
    TriangleMesh m = getMesh(frameInterpolation);

    // Loose geometry will cause problems when splitting into mesh islands
    std::vector<int> removedVertices = m.removeExtraneousVertices();
    std::vector<vmath::vec3> vertexVelocities = getVertexVelocities(dt, frameInterpolation);
    for (int i = removedVertices.size() - 1; i >= 0; i--) {
        vertexVelocities.erase(vertexVelocities.begin() + removedVertices[i]);
    }

    std::vector<TriangleMesh> islands;
    std::vector<std::vector<vmath::vec3> > islandVertexVelocities;
    _getMeshIslands(m, vertexVelocities, levelset, islands, islandVertexVelocities);
    _expandMeshIslands(islands);

    if ((int)islands.size() < _numIslandsForFractureOptimizationTrigger) {
        std::vector<TriangleMesh> combinedIslands;
        std::vector<std::vector<vmath::vec3> > combinedIslandVertexVelocities;
        combinedIslands.push_back(m);
        combinedIslandVertexVelocities.push_back(vertexVelocities);
        _addMeshIslandsToLevelSet(combinedIslands, combinedIslandVertexVelocities, exactBand, levelset);
    } else {
        _addMeshIslandsToLevelSetFractureOptimization(
                                  islands, islandVertexVelocities, exactBand, levelset);
    }
}

void MeshObject::enable() {
    if (!_isEnabled) {
        _isObjectStateChanged = true;
    }
    _isEnabled = true;
}

void MeshObject::disable() {
    if (_isEnabled) {
        _isObjectStateChanged = true;
    }
    _isEnabled = false;
}

bool MeshObject::isEnabled() {
    return _isEnabled;
}

void MeshObject::setAsDomainObject() {
    _isDomainObject = true;
}

bool MeshObject::isDomainObject() {
    return _isDomainObject;
}

void MeshObject::inverse() {
    _isInversed = !_isInversed;
}

bool MeshObject::isInversed() {
    return _isInversed;
}

void MeshObject::setFriction(float f) {
    f = fmin(f, 1.0f);
    f = fmax(f, 0.0f);
    _friction = f;
}

float MeshObject::getFriction() {
    return _friction;
}

void MeshObject::setWhitewaterInfluence(float value) {
    value = fmax(value, 0.0f);
    _whitewaterInfluence = value;
}

float MeshObject::getWhitewaterInfluence() {
    return _whitewaterInfluence;
}

void MeshObject::setDustEmissionStrength(float value) {
    value = fmax(value, 0.0f);
    _dustEmissionStrength = value;
}

float MeshObject::getDustEmissionStrength() {
    return _dustEmissionStrength;
}

bool MeshObject::isDustEmissionEnabled() {
    return _dustEmissionStrength > 1e-6;
}

void MeshObject::setSheetingStrength(float value) {
    value = fmax(value, 0.0f);
    _sheetingStrength = value;
}

float MeshObject::getSheetingStrength() {
    return _sheetingStrength;
}

void MeshObject::setMeshExpansion(float ex) {
    _meshExpansion = ex;
}

float MeshObject::getMeshExpansion() {
    return _meshExpansion;
}

void MeshObject::enableAppendObjectVelocity() {
    _isAppendObjectVelocityEnabled = true;
}

void MeshObject::disableAppendObjectVelocity() {
     _isAppendObjectVelocityEnabled = false;
}

bool MeshObject::isAppendObjectVelocityEnabled() {
    return _isAppendObjectVelocityEnabled;
}

RigidBodyVelocity MeshObject::getRigidBodyVelocity(double framedt) {
    framedt = fmax(framedt, 1e-6);

    float vscale = _objectVelocityInfluence;
    float eps = 1e-5;
    RigidBodyVelocity rv;
    if (!_isAnimated || _isChangingTopology) {
        TriangleMesh m = getMesh();
        rv.centroid = m.getCentroid();
        rv.axis = vmath::vec3(1.0, 0.0, 0.0);
        return rv;
    }

    TriangleMesh m1 = _meshCurrent;
    TriangleMesh m2 = _meshNext;
    rv.centroid = m1.getCentroid();

    vmath::vec3 c1 = m1.getCentroid();
    vmath::vec3 c2 = m2.getCentroid();
    rv.linear = ((c2 - c1) / framedt) * vscale;

    vmath::vec3 vert1, vert2;
    bool referencePointFound = false;
    for (size_t i = 0; i < m1.vertices.size(); i++) {
        vert1 = m1.vertices[i];
        vert2 = m2.vertices[i];
        if (vmath::length(vert1 - rv.centroid) > eps && vmath::length(vert2 - rv.centroid)) {
            referencePointFound = true;
            break;
        }
    }

    if (!referencePointFound || vmath::length(vert1 - (vert2 - (c2 - c1))) < eps) {
        rv.axis = vmath::vec3(1.0, 0.0, 0.0);
        rv.angular = 0.0;
        return rv;
    }

    vmath::vec3 v1 = vert1 - rv.centroid;
    vmath::vec3 v2 = (vert2 - (c2 - c1)) - rv.centroid;
    if (vmath::length(v1) < eps || vmath::length(v2) < eps) {
        rv.axis = vmath::vec3(1.0, 0.0, 0.0);
        rv.angular = 0.0;
        return rv;
    }

    vmath::vec3 cross = vmath::cross(v1, v2);
    if (vmath::length(cross) < eps) {
        rv.axis = vmath::vec3(1.0, 0.0, 0.0);
        rv.angular = 0.0;
        return rv;
    }
    rv.axis = cross.normalize();

    v1 = v1.normalize();
    v2 = v2.normalize();
    double angle = acos(vmath::dot(v1, v2));
    rv.angular = (angle / framedt) * vscale;

    if (std::isinf(rv.axis.x) || std::isinf(rv.axis.y) || std::isinf(rv.axis.z) || std::isinf(rv.angular) || 
        std::isnan(rv.axis.x) || std::isnan(rv.axis.y) || std::isnan(rv.axis.z) || std::isnan(rv.angular)) {
        rv.axis = vmath::vec3(1.0, 0.0, 0.0);
        rv.angular = 0.0;
    }

    return rv;
}

bool MeshObject::isGeometryAABB() {
    TriangleMesh m = _meshCurrent;
    AABB bbox(m.vertices);

    bool isAABB = true;
    float eps = 1e-4;
    for (size_t i = 0; i < m.triangles.size(); i++) {
        Triangle t = m.triangles[i];
        vmath::vec3 v1 = m.vertices[t.tri[0]];
        vmath::vec3 v2 = m.vertices[t.tri[1]];
        vmath::vec3 v3 = m.vertices[t.tri[2]];

        if (std::abs(bbox.getSignedDistance(v1)) > eps ||
                std::abs(bbox.getSignedDistance(v2)) > eps ||
                std::abs(bbox.getSignedDistance(v3)) > eps) {
            isAABB = false;
            break;
        }

        bool isPlaneX = std::abs(v1.x - v2.x) < eps && std::abs(v1.x - v3.x) < eps;
        bool isPlaneY = std::abs(v1.y - v2.y) < eps && std::abs(v1.y - v3.y) < eps;
        bool isPlaneZ = std::abs(v1.z - v2.z) < eps && std::abs(v1.z - v3.z) < eps;

        if (!(isPlaneX || isPlaneY || isPlaneZ)) {
            isAABB = false;
            break;
        }
    }

    return isAABB;
}

void MeshObject::setObjectVelocityInfluence(float value) {
    _objectVelocityInfluence = value;
}

float MeshObject::getObjectVelocityInfluence() {
    return _objectVelocityInfluence;
}

void MeshObject::setSourceID(int id) {
    _sourceID = id;
}

int MeshObject::getSourceID() {
    return _sourceID;
}

void MeshObject::setSourceColor(vmath::vec3 c) {
    _sourceColor = c;
}

vmath::vec3 MeshObject::getSourceColor() {
    return _sourceColor;
}

MeshObjectStatus MeshObject::getStatus() {
    MeshObjectStatus s;
    s.isEnabled = isEnabled();
    s.isAnimated = isAnimated();
    s.isInversed = isInversed();
    s.isStateChanged = _isObjectStateChanged;
    s.isMeshChanged = _isMeshChanged();
    return s;
}

void MeshObject::_getInversedCells(float frameInterpolation, std::vector<GridIndex> &cells) {
    TriangleMesh m = getMesh(frameInterpolation);
    Array3d<bool> nodes(_isize + 1, _jsize + 1, _ksize + 1, false);
    MeshUtils::getGridNodesInsideTriangleMesh(m, _dx, nodes);

    Array3d<bool> cellGrid(_isize, _jsize, _ksize, false);
    GridIndex nodeCells[8];
    for (int k = 0; k < nodes.depth; k++) {
        for (int j = 0; j < nodes.height; j++) {
            for (int i = 0; i < nodes.width; i++) {
                if (nodes(i, j, k)) {
                    continue;
                }

                Grid3d::getVertexGridIndexNeighbours(i, j, k, nodeCells);
                for (int nidx = 0; nidx < 8; nidx++) {
                    if (cellGrid.isIndexInRange(nodeCells[nidx])) {
                        cellGrid.set(nodeCells[nidx], true);
                    }
                }
            }
        }
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                if (cellGrid(i, j, k)) {
                    cells.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

    cells.shrink_to_fit();
}

void MeshObject::_getMeshIslands(TriangleMesh &m,
                                 std::vector<vmath::vec3> &vertexVelocities,
                                 MeshLevelSet &levelset, 
                                 std::vector<TriangleMesh> &islands,
                                 std::vector<std::vector<vmath::vec3> > &islandVertexVelocities) {

    std::vector<TriangleMesh> tempIslands;
    std::vector<std::vector<vmath::vec3> > tempIslandVertexVelocities;
    MeshUtils::splitIntoMeshIslands(m, vertexVelocities, tempIslands, tempIslandVertexVelocities);

    int isize, jsize, ksize;
    levelset.getGridDimensions(&isize, &jsize, &ksize);
    double dx = levelset.getCellSize();
    AABB gridAABB(0.0, 0.0, 0.0, isize * dx, jsize * dx, ksize * dx);

    for (size_t i = 0; i < tempIslands.size(); i++) {
        AABB meshAABB(tempIslands[i].vertices);
        vmath::vec3 minp = meshAABB.getMinPoint();
        vmath::vec3 maxp = meshAABB.getMaxPoint();

        if (gridAABB.isPointInside(minp) && gridAABB.isPointInside(maxp)) {
            islands.push_back(tempIslands[i]);
            islandVertexVelocities.push_back(tempIslandVertexVelocities[i]);
        } else {
            AABB inter = gridAABB.getIntersection(meshAABB);
            if (inter.width > 0.0 || inter.height > 0.0 || inter.depth > 0.0) {
                islands.push_back(tempIslands[i]);
                islandVertexVelocities.push_back(tempIslandVertexVelocities[i]);
            }
        }
    }
}


MeshLevelSet MeshObject::_getMeshIslandLevelSet(TriangleMesh &m, 
                                                std::vector<vmath::vec3> &velocities, 
                                                MeshLevelSet &domainLevelSet,
                                                int exactBand, bool *success) {
    int isize, jsize, ksize;
    domainLevelSet.getGridDimensions(&isize, &jsize, &ksize);
    double dx = domainLevelSet.getCellSize();

    AABB islandAABB(m.vertices);
    GridIndex gmin = Grid3d::positionToGridIndex(islandAABB.getMinPoint(), dx);
    GridIndex gmax = Grid3d::positionToGridIndex(islandAABB.getMaxPoint(), dx);
    gmin.i = (int)fmax(gmin.i - exactBand, 0);
    gmin.j = (int)fmax(gmin.j - exactBand, 0);
    gmin.k = (int)fmax(gmin.k - exactBand, 0);
    gmax.i = (int)fmin(gmax.i + exactBand + 1, isize - 1);
    gmax.j = (int)fmin(gmax.j + exactBand + 1, jsize - 1);
    gmax.k = (int)fmin(gmax.k + exactBand + 1, ksize - 1);

    int gwidth = gmax.i - gmin.i;
    int gheight = gmax.j - gmin.j;
    int gdepth = gmax.k - gmin.k;

    if (gwidth <= 0 || gheight <= 0 || gdepth <= 0) {
        *success = false;
        MeshLevelSet emptylevelset;
        return emptylevelset;
    }

    MeshLevelSet islandLevelSet(gwidth, gheight, gdepth, dx, this);
    islandLevelSet.setGridOffset(gmin);
    islandLevelSet.fastCalculateSignedDistanceField(m, velocities, exactBand);

    *success = true;
    return islandLevelSet;
}

void MeshObject::_expandMeshIslands(std::vector<TriangleMesh> &islands) {
    float eps = 1e-9f;
    if (fabs(_meshExpansion) < eps) {
        return;
    }

    for (size_t i = 0; i < islands.size(); i++) {
        _expandMeshIsland(islands[i]);
    }
}

void MeshObject::_expandMeshIsland(TriangleMesh &m) {
    if (m.vertices.empty()) {
        return;
    }

    vmath::vec3 vsum(0.0f, 0.0f, 0.0f);
    for (size_t i = 0; i < m.vertices.size(); i++) {
        vsum += m.vertices[i];
    }

    vmath::vec3 centroid = vsum / (float)m.vertices.size();
    float expval = 0.5f * _meshExpansion;
    float eps = 1e-9f;
    for (size_t i = 0; i < m.vertices.size(); i++) {
        vmath::vec3 v = m.vertices[i] - centroid;
        if (fabs(v.x) < eps && fabs(v.y) < eps && fabs(v.z) < eps) {
            continue;
        }

        v = v.normalize();
        m.vertices[i] += expval * v;
    }
}

void MeshObject::_addMeshIslandsToLevelSet(std::vector<TriangleMesh> &islands,
                                           std::vector<std::vector<vmath::vec3> > &islandVertexVelocities,
                                           int exactBand,
                                           MeshLevelSet &levelset) {
    for (size_t i = 0; i < islands.size(); i++) {
        bool success = true;
        MeshLevelSet islandLevelSet = _getMeshIslandLevelSet(
                islands[i], islandVertexVelocities[i], levelset, exactBand, &success
        );

        // If not successful, this will be caused by the mesh island being outside of the
        // domain range and will not be computed, should not be unioned
        if (success) {
            levelset.calculateUnion(islandLevelSet);
        }
    }
}

void MeshObject::_addMeshIslandsToLevelSetFractureOptimization(
                                           std::vector<TriangleMesh> &islands,
                                           std::vector<std::vector<vmath::vec3> > &islandVertexVelocities,
                                           int exactBand,
                                           MeshLevelSet &levelset) {

    BoundedBuffer<MeshIslandWorkItem> workQueue(islands.size());
    for (size_t i = 0; i < islands.size(); i++) {
        MeshIslandWorkItem item(islands[i], islandVertexVelocities[i]);
        workQueue.push(item);
    }

    BoundedBuffer<MeshLevelSet*> finishedWorkQueue(_finishedWorkQueueSize);

    int numthreads = ThreadUtils::getMaxThreadCount();
    std::vector<std::thread> threads(numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&MeshObject::_islandMeshLevelSetProducerThread, this,
                                 &workQueue, &finishedWorkQueue, &levelset, exactBand);
    }

    int numItemsProcessed = 0;
    while (numItemsProcessed < (int)islands.size()) {
        std::vector<MeshLevelSet*> finishedItems;
        finishedWorkQueue.popAll(finishedItems);

        for (size_t i = 0; i < finishedItems.size(); i++) {
            levelset.calculateUnion(*(finishedItems[i]));
            delete (finishedItems[i]);
        }
        numItemsProcessed += finishedItems.size();
    }

    workQueue.notifyFinished();
    for (size_t i = 0; i < threads.size(); i++) {
        workQueue.notifyFinished();
        threads[i].join();
    }
}

void MeshObject::_islandMeshLevelSetProducerThread(BoundedBuffer<MeshIslandWorkItem> *workQueue,
                                                   BoundedBuffer<MeshLevelSet*> *finishedWorkQueue,
                                                   MeshLevelSet *domainLevelSet,
                                                   int exactBand) {
    int isize, jsize, ksize;
    domainLevelSet->getGridDimensions(&isize, &jsize, &ksize);
    double dx = domainLevelSet->getCellSize();

    while (workQueue->size() > 0) {
        std::vector<MeshIslandWorkItem> items;
        int numItems = workQueue->pop(1, items);
        if (numItems == 0) {
            continue;
        }
        MeshIslandWorkItem w = items[0];

        AABB islandAABB(w.mesh.vertices);
        GridIndex gmin = Grid3d::positionToGridIndex(islandAABB.getMinPoint(), dx);
        GridIndex gmax = Grid3d::positionToGridIndex(islandAABB.getMaxPoint(), dx);
        gmin.i = (int)fmax(gmin.i - exactBand, 0);
        gmin.j = (int)fmax(gmin.j - exactBand, 0);
        gmin.k = (int)fmax(gmin.k - exactBand, 0);
        gmax.i = (int)fmin(gmax.i + exactBand + 1, isize - 1);
        gmax.j = (int)fmin(gmax.j + exactBand + 1, jsize - 1);
        gmax.k = (int)fmin(gmax.k + exactBand + 1, ksize - 1);

        int gwidth = gmax.i - gmin.i;
        int gheight = gmax.j - gmin.j;
        int gdepth = gmax.k - gmin.k;

        MeshLevelSet *islandLevelSet = new MeshLevelSet(gwidth, gheight, gdepth, dx, this);
        islandLevelSet->setGridOffset(gmin);
        islandLevelSet->disableMultiThreading();
        islandLevelSet->fastCalculateSignedDistanceField(w.mesh, w.vertexVelocities, exactBand);

        finishedWorkQueue->push(islandLevelSet);
    }
}

bool MeshObject::_isMeshChanged() {
    if (!isAnimated()) {
        return false;
    }

    if (_meshPrevious.vertices.size() != _meshCurrent.vertices.size()) {
        return true;
    }

    float eps = 1e-5;
    bool isMeshChanged = false;
    for (size_t i = 0; i < _meshPrevious.vertices.size(); i++) {
        if (vmath::length(_meshPrevious.vertices[i] - _meshCurrent.vertices[i]) > eps) {
            isMeshChanged = true;
            break;
        }
    }

    return isMeshChanged;
}

void MeshObject::_sortTriangleIndices(Triangle &t) {
    if (t.tri[1] < t.tri[0]) {
       std::swap(t.tri[0], t.tri[1]); 
    }
  
    if (t.tri[2] < t.tri[1]) { 
        std::swap(t.tri[1], t.tri[2]); 
        if (t.tri[1] < t.tri[0]) {
            std::swap(t.tri[1], t.tri[0]); 
        } 
    }
}

bool MeshObject::_isTriangleEqual(Triangle &t1, Triangle &t2) {
    return t1.tri[0] == t2.tri[0] && t1.tri[1] == t2.tri[1] && t1.tri[2] == t2.tri[2];
}

bool MeshObject::_isTopologyConsistent(TriangleMesh &m1, TriangleMesh &m2) {
    if (m1.vertices.size() != m2.vertices.size()) {
        return false;
    }

    if (m1.triangles.size() != m2.triangles.size()) {
        return false;
    }

    // Ignore cases where topology changes due to changing face configurations.
    // The topology may not be consistent, but for many cases the calculated
    // vertex velocities could still make sense.

    /*
    TriangleMesh tempm1 = m1;
    TriangleMesh tempm2 = m2;
    std::vector<int> indexcounts1(tempm1.vertices.size(), 0);
    std::vector<int> indexcounts2(tempm2.vertices.size(), 0);
    for (size_t i = 0; i < tempm1.triangles.size(); i++) {
        Triangle t1 = tempm1.triangles[i];
        Triangle t2 = tempm2.triangles[i];
        _sortTriangleIndices(t1);
        _sortTriangleIndices(t2);
        tempm1.triangles[i] = t1;
        tempm2.triangles[i] = t2;
        indexcounts1[tempm1.triangles[i].tri[0]]++;
        indexcounts2[tempm2.triangles[i].tri[0]]++;
    }

    std::vector<int> binstarts1(indexcounts1.size());
    std::vector<int> binstarts2(indexcounts2.size());
    int currentcount1 = 0;
    int currentcount2 = 0;
    for (size_t i = 0; i < indexcounts1.size(); i++) {
        binstarts1[i] = currentcount1;
        binstarts2[i] = currentcount2;
        currentcount1 += indexcounts1[i];
        currentcount2 += indexcounts2[i];
    }

    std::vector<Triangle> sortedtris1(tempm1.triangles.size());
    std::vector<Triangle> sortedtris2(tempm2.triangles.size());
    std::vector<int> origbinstarts2 = binstarts2;
    for (size_t i = 0; i < tempm1.triangles.size(); i++) {
        Triangle t1 = tempm1.triangles[i];
        Triangle t2 = tempm2.triangles[i];
        sortedtris1[binstarts1[t1.tri[0]]] = t1;
        sortedtris2[binstarts2[t2.tri[0]]] = t2;
        binstarts1[t1.tri[0]]++;
        binstarts2[t2.tri[0]]++;
    }

    for (size_t i = 0; i < sortedtris1.size(); i++) {
        Triangle t1 = sortedtris1[i];
        int searchidx = t1.tri[0];
        int startidx = origbinstarts2[searchidx];
        for (size_t j = startidx; j < sortedtris2.size(); j++) {
            Triangle t2 = sortedtris2[j];
            if (t2.tri[0] != searchidx) {
                return false;
            }

            if (_isTriangleEqual(t1, t2)) {
                break;
            }
        }
    }
    */

    return true;
}

bool MeshObject::_isRigidBody(TriangleMesh m1, TriangleMesh m2) {
    double smalleps = 1e-6;
    double bigeps = 1e-4;

    vmath::vec3 c1 = m1.getCentroid();
    vmath::vec3 c2 = m2.getCentroid();
    m1.translate(-c1);
    m2.translate(-c2);
    vmath::vec3 centroid = vmath::vec3(0.0f, 0.0f, 0.0f);

    AABB bbox(m1.vertices);
    double width = std::max(bbox.width, std::max(bbox.height, bbox.depth));
    double widthNormalized = 4.0;
    double scaleFactor = widthNormalized / width;

    vmath::vec3 scale(scaleFactor, scaleFactor, scaleFactor);
    m1.scale(scale);
    m2.scale(scale);

    bool v1found = false;
    size_t v1idx = -1;
    for (size_t i = 0; i < m1.vertices.size(); i++) {
        vmath::vec3 p = m1.vertices[i];
        if (!vmath::equals(p, centroid, bigeps)) {
            v1found = true;
            v1idx = i;
            break;
        }
    }

    if (!v1found) {
        return false;
    }

    vmath::vec3 m1v1 = m1.vertices[v1idx];

    bool v2found = false;
    size_t v2idx = -1;
    for (int i = (int)m1.vertices.size() / 2; i >= 0; i--) {
        if ((size_t)i == v1idx) {
            continue;
        }

        vmath::vec3 p = m1.vertices[i];
        if (!vmath::equals(p, centroid, bigeps) && !vmath::isCollinear(p, m1v1, smalleps)) {
            v2found = true;
            v2idx = (size_t)i;
            break;
        }
    }

    if (!v2found) {
        return false;
    }

    vmath::vec3 m1v2 = m1.vertices[v2idx];

    if ((m1v1 - m1v2).length() < bigeps) {
        return false;
    }

    vmath::vec3 m2v1 = m2.vertices[v1idx];
    vmath::vec3 m2v2 = m2.vertices[v2idx];

    if (std::abs(m1v1.length() - m2v1.length()) > bigeps || std::abs(m1v2.length() - m2v2.length()) > bigeps) {
        return false;
    }

    vmath::vec3 m1bx, m1by, m1bz;
    vmath::vec3 m2bx, m2by, m2bz;
    vmath::generateBasisVectors(m1v1, m1v2, m1bx, m1by, m1bz);
    vmath::generateBasisVectors(m2v1, m2v2, m2bx, m2by, m2bz);

    vmath::mat3 m1rot = vmath::localToWorldTransform(m1bx, m1by, m1bz);
    vmath::mat3 m2rot = vmath::localToWorldTransform(m2bx, m2by, m2bz);

    for (size_t i = 0; i < m1.vertices.size(); i++) {
        vmath::vec3 r1 = m1rot.mult(m1.vertices[i]);
        vmath::vec3 r2 = m2rot.mult(m2.vertices[i]);
        if (!vmath::equals(r1, r2, bigeps)) {
            return false;
        }
    }

    return true;
}