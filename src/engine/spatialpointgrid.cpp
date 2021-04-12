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

#include "spatialpointgrid.h"

#include <algorithm>

#include "grid3d.h"

SpatialPointGrid::SpatialPointGrid() {
}

SpatialPointGrid::SpatialPointGrid(int isize, int jsize, int ksize, double dx) :
                                        _isize(isize), _jsize(jsize), _ksize(ksize), _dx(dx),
                                        _grid(_isize, _jsize, _ksize),
                                        _bbox(vmath::vec3(), _dx*_isize, _dx*_jsize, _dx*_ksize) {
}

SpatialPointGrid::~SpatialPointGrid() {
}

void SpatialPointGrid::clear() {
    _gridPoints.clear();
    _gridPoints.shrink_to_fit();

    _refIDToGridPointIndexTable.clear();
    _refIDToGridPointIndexTable.shrink_to_fit();

    _grid.fill(CellNode());
}

std::vector<GridPointReference> SpatialPointGrid::insert(std::vector<vmath::vec3> &points) {
    clear();

    std::vector<GridPointReference> referenceList;
    _sortGridPointsByGridIndex(points, _gridPoints, referenceList);
    _updateRefIDToGridPointIndexTable();
    _insertCellNodesIntoGrid();

    return referenceList;
}

std::vector<GridPointReference> SpatialPointGrid::insert(FragmentedVector<vmath::vec3> &points) {
    std::vector<vmath::vec3> vps;
    vps.reserve(points.size());

    for (unsigned int i = 0; i < points.size(); i++) {
        vps.push_back(points[i]);
    }

    return insert(vps);
}

bool compareByFlatGridIndex(const std::pair<GridPoint, unsigned int> p1, const std::pair<GridPoint, unsigned int> p2) {
    return p1.second < p2.second;
}

void SpatialPointGrid::queryPointsInsideSphere(vmath::vec3 p, double r, std::vector<vmath::vec3> &points) {
    _queryPointsInsideSphere(p, r, -1, points);
}

void SpatialPointGrid::queryPointsInsideSphere(GridPointReference ref, double r, std::vector<vmath::vec3> &points) {
    FLUIDSIM_ASSERT(ref.id >= 0 && ref.id < (int)_gridPoints.size());

    GridPoint gp = _gridPoints[_refIDToGridPointIndexTable[ref.id]];
    _queryPointsInsideSphere(gp.position, r, gp.ref.id, points);
}

void SpatialPointGrid::queryPointsInsideSphere(vmath::vec3 p, double r, 
                                               std::vector<bool> &exclusions, 
                                               std::vector<vmath::vec3> &points) {
    _queryPointsInsideSphere(p, r, exclusions, points);
}

void SpatialPointGrid::queryPointsInsideSphere(GridPointReference ref, double r, 
                                               std::vector<bool> &exclusions, 
                                               std::vector<vmath::vec3> &points) {
    FLUIDSIM_ASSERT(ref.id >= 0 && ref.id < (int)_gridPoints.size());
    FLUIDSIM_ASSERT(exclusions.size() == _gridPoints.size());

    GridPoint gp = _gridPoints[_refIDToGridPointIndexTable[ref.id]];
    _queryPointsInsideSphere(gp.position, r, exclusions, points);
}

void SpatialPointGrid::queryPointReferencesInsideSphere(vmath::vec3 p, double r, 
                                                        std::vector<GridPointReference> &refs) {
    _queryPointReferencesInsideSphere(p, r, -1, refs);
}

void SpatialPointGrid::queryPointReferencesInsideSphere(GridPointReference ref, double r, 
                                                        std::vector<GridPointReference> &refs) {
    FLUIDSIM_ASSERT(ref.id >= 0 && ref.id < (int)_gridPoints.size());

    GridPoint gp = _gridPoints[_refIDToGridPointIndexTable[ref.id]];
    _queryPointReferencesInsideSphere(gp.position, r, gp.ref.id, refs);
}

void SpatialPointGrid::queryPointReferencesInsideSphere(vmath::vec3 p, double r, 
                                                        std::vector<bool> &exclusions, 
                                                        std::vector<GridPointReference> &refs) {
    _queryPointReferencesInsideSphere(p, r, exclusions, refs);
}

void SpatialPointGrid::queryPointReferencesInsideSphere(GridPointReference ref, double r, 
                                        std::vector<bool> &exclusions,
                                        std::vector<GridPointReference> &refs) {
    FLUIDSIM_ASSERT(ref.id >= 0 && ref.id < (int)_gridPoints.size());
    FLUIDSIM_ASSERT(exclusions.size() == _gridPoints.size());

    GridPoint gp = _gridPoints[_refIDToGridPointIndexTable[ref.id]];
    _queryPointReferencesInsideSphere(gp.position, r, exclusions, refs);
}

void SpatialPointGrid::queryPointsInsideAABB(AABB bbox, std::vector<vmath::vec3> &points) {
    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(bbox, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    vmath::vec3 v;
    GridPoint gp;
    CellNode node;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_grid(i, j, k).count > 0) {
                    node = _grid(i, j, k);
                    for (int idx = node.start; idx < node.start + node.count; idx++) {
                        gp = _gridPoints[idx];
                        if (bbox.isPointInside(gp.position)) {
                            points.push_back(gp.position);
                        }
                    }
                }
            }
        }
    }
}

void SpatialPointGrid::queryPointReferencesInsideAABB(AABB bbox, std::vector<GridPointReference> &refs) {
    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(bbox, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    vmath::vec3 v;
    GridPoint gp;
    CellNode node;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_grid(i, j, k).count > 0) {
                    node = _grid(i, j, k);
                    for (int idx = node.start; idx < node.start + node.count; idx++) {
                        gp = _gridPoints[idx];
                        if (bbox.isPointInside(gp.position)) {
                            refs.push_back(gp.ref);
                        }
                    }
                }
            }
        }
    }
}

void SpatialPointGrid::getConnectedPoints(vmath::vec3 seed, double radius, 
                                          std::vector<vmath::vec3> &points) {
    std::vector<GridPointReference> nearestRefs;
    queryPointReferencesInsideSphere(seed, radius, nearestRefs);

    if (nearestRefs.size() == 0) {
        return;
    }

    _getConnectedPoints(nearestRefs[0], radius, points);
}

void SpatialPointGrid::getConnectedPointReferences(vmath::vec3 seed, double radius, 
                                                   std::vector<GridPointReference> &refs) {
    std::vector<GridPointReference> nearestRefs;
    queryPointReferencesInsideSphere(seed, radius, nearestRefs);

    if (nearestRefs.size() == 0) {
        return;
    }

    _getConnectedPointReferences(nearestRefs[0], radius, refs);

}

void SpatialPointGrid::getConnectedPoints(GridPointReference seed, double radius, 
                                          std::vector<vmath::vec3> &points) {
    _getConnectedPoints(seed, radius, points);
}

void SpatialPointGrid::getConnectedPointReferences(GridPointReference seed, double radius, 
                                                   std::vector<GridPointReference> &refs) {
    _getConnectedPointReferences(seed, radius, refs);
}

vmath::vec3 SpatialPointGrid::getPointFromReference(GridPointReference ref) {
    FLUIDSIM_ASSERT(ref.id >= 0 && ref.id < (int)_refIDToGridPointIndexTable.size());
    GridPoint gp = _gridPoints[_refIDToGridPointIndexTable[ref.id]];
    return gp.position;
}

void SpatialPointGrid::getConnectedPointComponents(double radius, 
                                                   std::vector<std::vector<vmath::vec3> > &pointsList) {

    std::vector<std::vector<GridPointReference> > refsList;
    getConnectedPointReferenceComponents(radius, refsList);

    GridPoint gp;
    for (unsigned int i = 0; i < refsList.size(); i++) {
        std::vector<vmath::vec3> points;
        points.reserve(refsList[i].size());
        for (unsigned int idx = 0; idx < refsList[i].size(); idx++) {
            int id = refsList[i][idx].id;
            gp = _gridPoints[_refIDToGridPointIndexTable[id]];
            points.push_back(gp.position);
        }

        pointsList.push_back(points);
    }
}

void SpatialPointGrid::getConnectedPointReferenceComponents(double radius, 
                                                            std::vector<std::vector<GridPointReference> > &refsList) {

    std::vector<bool> visitedRefs(_gridPoints.size(), false);
    for (unsigned int refid = 0; refid < _gridPoints.size(); refid++) {
        if (!visitedRefs[refid]) {
            GridPointReference ref = GridPointReference(refid);
            std::vector<GridPointReference> connectedRefs;
            getConnectedPointReferences(ref, radius, connectedRefs);
            refsList.push_back(connectedRefs);

            for (unsigned int idx = 0; idx < connectedRefs.size(); idx++) {
                visitedRefs[connectedRefs[idx].id] = true;
            }
        }
    }

}


void SpatialPointGrid::_sortGridPointsByGridIndex(std::vector<vmath::vec3> &points,
                                                  std::vector<GridPoint> &sortedPoints,
                                                  std::vector<GridPointReference> &refList) {

    std::pair<GridPoint, unsigned int> pair;
    std::vector<std::pair<GridPoint, unsigned int> > pointIndexPairs;
    pointIndexPairs.reserve(points.size());
    refList.reserve(points.size());

    GridPoint gp;
    GridPointReference ref;
    unsigned int flatIndex;
    for (unsigned int i = 0; i < points.size(); i++) {
        FLUIDSIM_ASSERT(_bbox.isPointInside(points[i]));

        ref = GridPointReference(i);
        gp = GridPoint(points[i], ref);
        flatIndex = _getFlatIndex(Grid3d::positionToGridIndex(points[i], _dx));
        pair = std::pair<GridPoint, unsigned int>(gp, flatIndex);

        pointIndexPairs.push_back(pair);
        refList.push_back(ref);
    }

    std::sort(pointIndexPairs.begin(), pointIndexPairs.end(), compareByFlatGridIndex);

    sortedPoints.reserve(points.size());
    for (unsigned int i = 0; i < pointIndexPairs.size(); i++) {
        sortedPoints.push_back(pointIndexPairs[i].first);
    }
}

void SpatialPointGrid::_updateRefIDToGridPointIndexTable() {
    _refIDToGridPointIndexTable.clear();
    _refIDToGridPointIndexTable.shrink_to_fit();
    _refIDToGridPointIndexTable = std::vector<int>(_gridPoints.size(), -1);

    GridPoint gp;
    for (unsigned int i = 0; i < _gridPoints.size(); i++) {
        gp = _gridPoints[i];
        FLUIDSIM_ASSERT(gp.ref.id >= 0 && gp.ref.id < (int)_gridPoints.size());
        _refIDToGridPointIndexTable[gp.ref.id] = i;
    }
}

void SpatialPointGrid::_insertCellNodesIntoGrid() {
    GridPoint gp;
    GridIndex g;
    for (unsigned int idx = 0; idx < _gridPoints.size(); idx++) {
        gp = _gridPoints[idx];
        g = Grid3d::positionToGridIndex(gp.position, _dx);

        if (_grid(g).start == -1) {
            int start = idx;
            int count = 0;

            while (idx < _gridPoints.size()) {
                count++;
                idx++;

                if (idx == _gridPoints.size()) {
                    break;
                }

                gp = _gridPoints[idx];
                if (Grid3d::positionToGridIndex(gp.position, _dx) != g) {
                    idx--;
                    break;
                }
            }

            _grid.set(g, CellNode(start, count));
        }
    }
}

void SpatialPointGrid::_queryPointsInsideSphere(vmath::vec3 p, double r, int refID, 
                                                std::vector<vmath::vec3> &points) {
    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, r, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    double maxdistsq = r*r;
    double distsq;
    vmath::vec3 v;
    GridPoint gp;
    CellNode node;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_grid(i, j, k).count > 0) {
                    node = _grid(i, j, k);
                    for (int idx = node.start; idx < node.start + node.count; idx++) {
                        gp = _gridPoints[idx];
                        if (gp.ref.id != refID) {
                            v = gp.position - p;
                            distsq = vmath::dot(v, v);
                            if (distsq < maxdistsq) {
                                points.push_back(gp.position);
                            }
                        }
                    }
                }
            }
        }
    }
}

void SpatialPointGrid::_queryPointsInsideSphere(vmath::vec3 p, double r, 
                                                std::vector<bool> &exclusions, 
                                                std::vector<vmath::vec3> &points) {
    FLUIDSIM_ASSERT(exclusions.size() == _gridPoints.size());

    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, r, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    double maxdistsq = r*r;
    double distsq;
    vmath::vec3 v;
    GridPoint gp;
    CellNode node;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_grid(i, j, k).count > 0) {
                    node = _grid(i, j, k);
                    for (int idx = node.start; idx < node.start + node.count; idx++) {
                        gp = _gridPoints[idx];
                        if (!exclusions[gp.ref.id]) {
                            v = gp.position - p;
                            distsq = vmath::dot(v, v);
                            if (distsq < maxdistsq) {
                                points.push_back(gp.position);
                            }
                        }
                    }
                }
            }
        }
    }
}

void SpatialPointGrid::_queryPointReferencesInsideSphere(vmath::vec3 p, double r, int refID, 
                                                         std::vector<GridPointReference> &refs) {
    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, r, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    double maxdistsq = r*r;
    double distsq;
    vmath::vec3 v;
    GridPoint gp;
    CellNode node;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_grid(i, j, k).count > 0) {
                    node = _grid(i, j, k);
                    for (int idx = node.start; idx < node.start + node.count; idx++) {
                        gp = _gridPoints[idx];
                        if (gp.ref.id != refID) {
                            v = gp.position - p;
                            distsq = vmath::dot(v, v);
                            if (distsq < maxdistsq) {
                                refs.push_back(gp.ref);
                            }
                        }
                    }
                }
            }
        }
    }
}

void SpatialPointGrid::_queryPointReferencesInsideSphere(vmath::vec3 p, double r, 
                                                         std::vector<bool> &exclusions, 
                                                         std::vector<GridPointReference> &refs) {
    FLUIDSIM_ASSERT(exclusions.size() == _gridPoints.size());

    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(p, r, _dx, _isize, _jsize, _ksize, &gmin, &gmax);

    double maxdistsq = r*r;
    double distsq;
    vmath::vec3 v;
    GridPoint gp;
    CellNode node;
    for (int k = gmin.k; k <= gmax.k; k++) {
        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                if (_grid(i, j, k).count > 0) {
                    node = _grid(i, j, k);
                    for (int idx = node.start; idx < node.start + node.count; idx++) {
                        gp = _gridPoints[idx];
                        if (!exclusions[gp.ref.id]) {
                            v = gp.position - p;
                            distsq = vmath::dot(v, v);
                            if (distsq < maxdistsq) {
                                refs.push_back(gp.ref);
                            }
                        }
                    }
                }
            }
        }
    }
}

void SpatialPointGrid::_getConnectedPoints(GridPointReference seed, double radius, 
                                           std::vector<vmath::vec3> &points) {

    std::vector<bool> visitedRefs(_gridPoints.size(), false);
    std::vector<GridPointReference> queue;
    queue.push_back(seed);
    visitedRefs[seed.id] = true;

    GridPointReference n;
    GridPoint gp;
    std::vector<GridPointReference> nearest;
    while (!queue.empty()) {
        seed = queue.back();
        queue.pop_back();

        nearest.clear();
        queryPointReferencesInsideSphere(seed, radius, visitedRefs, nearest);
        for (unsigned int i = 0; i < nearest.size(); i++) {
            n = nearest[i];
            if (!visitedRefs[n.id]) {
                queue.push_back(n);
                visitedRefs[n.id] = true;
            }
        }

        points.push_back(getPointFromReference(seed));
    }
}

void SpatialPointGrid::_getConnectedPointReferences(GridPointReference seed, double radius, 
                                                    std::vector<GridPointReference> &refs) {
    std::vector<bool> visitedRefs(_gridPoints.size(), false);
    std::vector<GridPointReference> queue;
    queue.push_back(seed);
    visitedRefs[seed.id] = true;

    GridPointReference n;
    GridPoint gp;
    std::vector<GridPointReference> nearest;
    while (!queue.empty()) {
        seed = queue.back();
        queue.pop_back();

        nearest.clear();
        queryPointReferencesInsideSphere(seed, radius, visitedRefs, nearest);
        for (unsigned int i = 0; i < nearest.size(); i++) {
            n = nearest[i];
            if (!visitedRefs[n.id]) {
                queue.push_back(n);
                visitedRefs[n.id] = true;
            }
        }

        refs.push_back(seed);
    }
}