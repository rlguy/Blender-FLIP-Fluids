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

#ifndef FLUIDENGINE_SPATIALPOINTGRID_H
#define FLUIDENGINE_SPATIALPOINTGRID_H

#include <vector>

#include "vmath.h"
#include "fragmentedvector.h"
#include "aabb.h"
#include "array3d.h"

struct GridPointReference {
    int id;

    GridPointReference() : id(-1) {}
    GridPointReference(int n) : id(n) {}

    bool operator==(const GridPointReference &other) const { 
        return id == other.id;
    }
};

struct GridPoint {
    vmath::vec3 position;
    GridPointReference ref;

    GridPoint() {}
    GridPoint(vmath::vec3 p, GridPointReference r) : position(p), ref(r) {} 
    GridPoint(vmath::vec3 p, unsigned int id) : position(p), ref(id) {}
};

class SpatialPointGrid
{
public:
    SpatialPointGrid();
    SpatialPointGrid(int isize, int jsize, int ksize, double _dx);
    ~SpatialPointGrid();

    void clear();
    std::vector<GridPointReference> insert(std::vector<vmath::vec3> &points);
    std::vector<GridPointReference> insert(FragmentedVector<vmath::vec3> &points);
    void queryPointsInsideSphere(vmath::vec3 p, double r, std::vector<vmath::vec3> &points);
    void queryPointsInsideSphere(GridPointReference ref, double r, std::vector<vmath::vec3> &points);
    void queryPointsInsideSphere(vmath::vec3 p, double r, std::vector<bool> &exclusions, 
                                                        std::vector<vmath::vec3> &points);
    void queryPointsInsideSphere(GridPointReference ref, double r, 
                                 std::vector<bool> &exclusions, std::vector<vmath::vec3> &points);
    void queryPointReferencesInsideSphere(vmath::vec3 p, double r, 
                                          std::vector<GridPointReference> &refs);
    void queryPointReferencesInsideSphere(GridPointReference ref, double r, 
                                          std::vector<GridPointReference> &refs);
    void queryPointReferencesInsideSphere(vmath::vec3 p, double r, 
                                          std::vector<bool> &exclusions, 
                                          std::vector<GridPointReference> &refs);
    void queryPointReferencesInsideSphere(GridPointReference ref, double r, 
                                          std::vector<bool> &exclusions,
                                          std::vector<GridPointReference> &refs);

    void queryPointsInsideAABB(AABB bbox, std::vector<vmath::vec3> &points);
    void queryPointReferencesInsideAABB(AABB bbox, std::vector<GridPointReference> &refs);

    void getConnectedPoints(vmath::vec3 seed, double radius, std::vector<vmath::vec3> &points);
    void getConnectedPointReferences(vmath::vec3 seed, double radius, std::vector<GridPointReference> &refs);
    void getConnectedPoints(GridPointReference seed, double radius, std::vector<vmath::vec3> &points);
    void getConnectedPointReferences(GridPointReference seed, double radius, std::vector<GridPointReference> &refs);
    void getConnectedPointComponents(double radius, std::vector<std::vector<vmath::vec3> > &points);
    void getConnectedPointReferenceComponents(double radius, std::vector<std::vector<GridPointReference> > &refs);

    vmath::vec3 getPointFromReference(GridPointReference ref);

private:

    struct CellNode {
        int start;
        int count;

        CellNode() : start(-1), count(-1) {}
        CellNode(int startIndex, int numPoints) : start(startIndex), count(numPoints) {}
    };

    inline unsigned int _getFlatIndex(int i, int j, int k) {
        return (unsigned int)i + (unsigned int)_isize *
               ((unsigned int)j + (unsigned int)_jsize * (unsigned int)k);
    }

    inline unsigned int _getFlatIndex(GridIndex g) {
        return (unsigned int)g.i + (unsigned int)_isize *
               ((unsigned int)g.j + (unsigned int)_jsize * (unsigned int)g.k);
    }

    void _sortGridPointsByGridIndex(std::vector<vmath::vec3> &points,
                                    std::vector<GridPoint> &sortedPoints,
                                    std::vector<GridPointReference> &refList);
    void _updateRefIDToGridPointIndexTable();
    void _insertCellNodesIntoGrid();
    void _queryPointsInsideSphere(vmath::vec3 p, double r, int refID, std::vector<vmath::vec3> &points);
    void _queryPointsInsideSphere(vmath::vec3 p, double r, 
                                  std::vector<bool> &exclusions, 
                                  std::vector<vmath::vec3> &points);
    void _queryPointReferencesInsideSphere(vmath::vec3 p, double r, int refID, 
                                           std::vector<GridPointReference> &refs);
    void _queryPointReferencesInsideSphere(vmath::vec3 p, double r, std::vector<bool> &exclusions, 
                                           std::vector<GridPointReference> &refs);

    void _getConnectedPoints(GridPointReference seed, double radius, 
                             std::vector<vmath::vec3> &points);
    void _getConnectedPointReferences(GridPointReference seed, double radius, 
                                      std::vector<GridPointReference> &refs);

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    std::vector<GridPoint> _gridPoints;
    std::vector<int> _refIDToGridPointIndexTable;
    Array3d<CellNode> _grid;
    AABB _bbox;
};

#endif