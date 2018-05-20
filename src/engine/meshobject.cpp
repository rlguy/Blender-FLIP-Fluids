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

#include "meshobject.h"

#include "meshutils.h"

MeshObject::MeshObject() {
}

MeshObject::MeshObject(int i, int j, int k, double dx, TriangleMesh mesh) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx) {

    _meshes.push_back(mesh);

    std::vector<vmath::vec3> trans(mesh.vertices.size());
    _vertexTranslations.push_back(trans);
}

MeshObject::MeshObject(int i, int j, int k, double dx, 
                       std::vector<TriangleMesh> meshes) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), _meshes(meshes) {

    for (size_t i = 0; i < meshes.size(); i++) {
        std::vector<vmath::vec3> trans(meshes[i].vertices.size());
        _vertexTranslations.push_back(trans);
    }
}

MeshObject::MeshObject(int i, int j, int k, double dx,
                       std::vector<TriangleMesh> meshes,
                       std::vector<TriangleMesh> translations) :
        _isize(i), _jsize(j), _ksize(k), _dx(dx), _meshes(meshes) {

    FLUIDSIM_ASSERT(meshes.size() == translations.size());
    for (size_t i = 0; i < translations.size(); i++) {
        FLUIDSIM_ASSERT(translations[i].vertices.size() == meshes[i].vertices.size())
        _vertexTranslations.push_back(translations[i].vertices);
    }
}

MeshObject::~MeshObject() {
}

void MeshObject::getGridDimensions(int *i, int *j, int *k) { 
    *i = _isize; *j = _jsize; *k = _ksize; 
}

void MeshObject::setFrame(int f) {
    _currentFrame = f;
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
    return _meshes.size() > 1;
}

void MeshObject::clearObjectStatus() {
    _isObjectStateChanged = false;
}

TriangleMesh MeshObject::getMesh() {
    if (_meshes.empty()) {
        return TriangleMesh();
    }

    return _meshes[_currentFrame % _meshes.size()];
}

TriangleMesh MeshObject::getMesh(float frameInterpolation) {
    frameInterpolation = fmax(0.0f, frameInterpolation);
    frameInterpolation = fmin(1.0f, frameInterpolation);

    if (_meshes.size() < 2) {
        return getMesh();
    }

    if (_currentFrame == (int)_meshes.size() - 1 || frameInterpolation == 0.0f) {
        return getMesh();
    }

    TriangleMesh m1 = _meshes[_currentFrame];
    TriangleMesh m2 = _meshes[_currentFrame + 1];

    TriangleMesh outmesh = m1;
    for (size_t i = 0; i < m1.vertices.size(); i++) {
        vmath::vec3 v1 = m1.vertices[i];
        vmath::vec3 v2 = m2.vertices[i];
        outmesh.vertices[i] = v1 + frameInterpolation * (v2 - v1);
    }

    return outmesh;
}

TriangleMesh MeshObject::getFrameMesh(int frameno) {
    return _meshes[frameno % _meshes.size()];
}

std::vector<vmath::vec3> MeshObject::getVertexTranslations() {
    return _vertexTranslations[_currentFrame % _meshes.size()];
}

std::vector<vmath::vec3> MeshObject::getVertexTranslations(float frameInterpolation) {
    frameInterpolation = fmax(0.0f, frameInterpolation);
    frameInterpolation = fmin(1.0f, frameInterpolation);

    if (_meshes.size() < 2) {
        return getVertexTranslations();
    }

    if (_currentFrame == (int)_meshes.size() - 1 || frameInterpolation == 0.0f) {
        return getVertexTranslations();
    }

    std::vector<vmath::vec3> t1 = _vertexTranslations[_currentFrame];
    std::vector<vmath::vec3> t2 = _vertexTranslations[_currentFrame + 1];

    std::vector<vmath::vec3> transout(t1.size(), vmath::vec3());
    for (size_t i = 0; i < t1.size(); i++) {
        vmath::vec3 p1 = t1[i];
        vmath::vec3 p2 = t2[i];
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
    std::vector<vmath::vec3> velocities = _vertexTranslations[frameno % _meshes.size()];

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
        _addMeshIslandsToLevelSet(islands, islandVertexVelocities, exactBand, levelset);
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

void MeshObject::inverse() {
    _isInversed = !_isInversed;
}

bool MeshObject::isInversed() {
    return _isInversed;
}

void MeshObject::setMeshExpansion(float ex) {
    _meshExpansion = ex;
}

float MeshObject::getMeshExpansion() {
    return _meshExpansion;
}

void MeshObject::setFriction(float f) {
    f = fmin(f, 1.0f);
    f = fmax(f, 0.0f);
    _friction = f;
}

float MeshObject::getFriction() {
    return _friction;
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
    return getRigidBodyVelocity(framedt, _currentFrame);
}

RigidBodyVelocity MeshObject::getRigidBodyVelocity(double framedt, int frameno) {
    framedt = fmax(framedt, 1e-6);

    float vscale = _objectVelocityInfluence;
    float eps = 1e-5;
    RigidBodyVelocity rv;
    if (_meshes.size() <= 1) {
        TriangleMesh m = getMesh();
        rv.centroid = m.getCentroid();
        rv.axis = vmath::vec3(1.0, 0.0, 0.0);
        return rv;
    }

    TriangleMesh m1, m2;
    if (frameno == (int)_meshes.size() - 1) {
        m1 = _meshes[frameno - 1];
        m2 = _meshes[frameno];
        rv.centroid = m2.getCentroid();
    } else {
        m1 = _meshes[frameno];
        m2 = _meshes[frameno + 1];
        rv.centroid = m1.getCentroid();
    }

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

void MeshObject::setObjectVelocityInfluence(float value) {
    _objectVelocityInfluence = value;
}

float MeshObject::getObjectVelocityInfluence() {
    return _objectVelocityInfluence;
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
                                                int exactBand) {
    
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

    MeshLevelSet islandLevelSet(gwidth, gheight, gdepth, dx, this);
    islandLevelSet.setGridOffset(gmin);
    islandLevelSet.fastCalculateSignedDistanceField(m, velocities, exactBand);

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
        MeshLevelSet islandLevelSet = _getMeshIslandLevelSet(
                islands[i], islandVertexVelocities[i], levelset, exactBand
        );

        levelset.calculateUnion(islandLevelSet);
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

    if (_currentFrame == 0) {
        return true;
    }

    TriangleMesh m1 = _meshes[_currentFrame - 1];
    TriangleMesh m2 = _meshes[_currentFrame];
    float eps = 1e-5;
    bool isMeshChanged = false;
    for (size_t i = 0; i < m1.vertices.size(); i++) {
        if (vmath::length(m1.vertices[i] - m2.vertices[i]) > eps) {
            isMeshChanged = true;
            break;
        }
    }

    return isMeshChanged;
}