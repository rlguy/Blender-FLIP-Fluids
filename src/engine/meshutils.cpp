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

#include "meshutils.h"

#include <limits>

#include "grid3d.h"
#include "collision.h"
#include "trianglemesh.h"

namespace MeshUtils {

void structToTriangleMesh(TriangleMesh_t &mesh_data, TriangleMesh &mesh) {
    mesh.vertices.reserve(mesh_data.numVertices);
    mesh.triangles.reserve(mesh_data.numTriangles);

    vmath::vec3 v;
    for (int i = 0; i < mesh_data.numVertices; i++) {
        v.x = mesh_data.vertices[3*i + 0];
        v.y = mesh_data.vertices[3*i + 1];
        v.z = mesh_data.vertices[3*i + 2];
        mesh.vertices.push_back(v);
    }

    Triangle t;
    for (int i = 0; i < mesh_data.numTriangles; i++) {
        t.tri[0] = mesh_data.triangles[3*i + 0];
        t.tri[1] = mesh_data.triangles[3*i + 1];
        t.tri[2] = mesh_data.triangles[3*i + 2];
        mesh.triangles.push_back(t);
    }
}

void _getTriangleGridZ(
        TriangleMesh &m, double dx, Array3d<std::vector<int> > &ztrigrid) {
    AABB tbbox;
    GridIndex gmin, gmax;
    std::vector<int> *tris;
    for (unsigned int tidx = 0; tidx < m.triangles.size(); tidx++) {
        tbbox = AABB(m.triangles[tidx], m.vertices);
        Grid3d::getGridIndexBounds(
            tbbox, dx, ztrigrid.width, ztrigrid.height, 1, &gmin, &gmax
        );

        for (int j = gmin.j; j <= gmax.j; j++) {
            for (int i = gmin.i; i <= gmax.i; i++) {
                tris = ztrigrid.getPointer(i, j, 0);
                tris->push_back(tidx);
            }
        }
    }
}

void _getTriangleCollisionsZ(
        vmath::vec3 origin, std::vector<int> &indices, TriangleMesh &m,
        std::vector<double> &collisions) {

    vmath::vec3 dir(0.0, 0.0, 1.0);
    vmath::vec3 v1, v2, v3, coll;
    Triangle t;
    for (unsigned int i = 0; i < indices.size(); i++) {
        t = m.triangles[indices[i]];
        v1 = m.vertices[t.tri[0]];
        v2 = m.vertices[t.tri[1]];
        v3 = m.vertices[t.tri[2]];
        if (Collision::lineIntersectsTriangle(origin, dir, v1, v2, v3, &coll)) {
            collisions.push_back(coll.z);
        }
    }
}

double _randomDouble(double min, double max) {
    return min + (double)rand() / ((double)RAND_MAX / (max - min));
}

void _getCollisionGridZ(
        TriangleMesh &m, double dx, Array3d<std::vector<double> > &zcollisions) {

    Array3d<std::vector<int> > ztrigrid(zcollisions.width, zcollisions.height, 1);
    _getTriangleGridZ(m, dx, ztrigrid);

    /* Triangles that align perfectly with grid cell centers may produce 
       imperfect collision results due to an edge case where a line-mesh 
       intersection can report two collisions when striking an edge that is 
       shared by two triangles. To reduce the chance of this occurring, a random
       jitter will be added to the position of the grid cell centers. 
    */
    double jit = 0.05*dx;
    vmath::vec3 jitter(_randomDouble(jit, -jit), 
                       _randomDouble(jit, -jit), 
                       _randomDouble(jit, -jit));

    std::vector<double> *zvals;
    vmath::vec3 gp;
    std::vector<int> *tris;
    for (int j = 0; j < ztrigrid.height; j++) {
        for (int i = 0; i < ztrigrid.width; i++) {
            tris = ztrigrid.getPointer(i, j, 0);
            if (tris->size() == 0) {
                continue;
            }

            zvals = zcollisions.getPointer(i, j, 0);
            zvals->reserve(tris->size());
            gp = Grid3d::GridIndexToCellCenter(i, j, -1, dx) + jitter;
            _getTriangleCollisionsZ(gp, *tris, m, *zvals);
        }
    }
}

void getCellsInsideTriangleMesh(
        TriangleMesh &m, int isize, int jsize, int ksize, double dx,
        std::vector<GridIndex> &cells) {

    Array3d<std::vector<double> > zcollisions(isize, jsize, 1);
    _getCollisionGridZ(m, dx, zcollisions);

    std::vector<double> *zvals;
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                zvals = zcollisions.getPointer(i, j, 0);
                if (zvals->size() % 2 != 0) {
                    continue;
                }

                double z = Grid3d::GridIndexToCellCenter(i, j, k, dx).z;
                int numless = 0;
                for (unsigned int zidx = 0; zidx < zvals->size(); zidx++) {
                    if (zvals->at(zidx) < z) {
                        numless++;
                    }
                }

                if (numless % 2 == 1) {
                    cells.push_back(GridIndex(i, j, k));
                }
            }
        }
    }

}

void _getCollisionGridZSubd2(TriangleMesh &m, double dx, 
                             Array3d<std::vector<double> > &zcollisions,
                             Array3d<std::vector<double> > &zsubcollisions) {

    Array3d<std::vector<int> > ztrigrid(zcollisions.width, zcollisions.height, 1);
    _getTriangleGridZ(m, dx, ztrigrid);

    /* Triangles that align perfectly with grid cell centers may produce 
       imperfect collision results due to an edge case where a line-mesh 
       intersection can report two collisions when striking an edge that is 
       shared by two triangles. To reduce the chance of this occurring, a random
       jitter will be added to the position of the grid cell centers. 
    */

    double jit = 0.05*dx;
    vmath::vec3 jitter(_randomDouble(jit, -jit), 
                       _randomDouble(jit, -jit), 
                       _randomDouble(jit, -jit));

    std::vector<double> *zvals;
    vmath::vec3 gp;
    std::vector<int> *tris;
    for (int j = 0; j < zcollisions.height; j++) {
        for (int i = 0; i < zcollisions.width; i++) {
            tris = ztrigrid.getPointer(i, j, 0);
            if (tris->size() == 0) {
                continue;
            }

            zvals = zcollisions.getPointer(i, j, 0);
            zvals->reserve(tris->size());
            gp = Grid3d::GridIndexToCellCenter(i, j, -1, dx) + jitter;
            _getTriangleCollisionsZ(gp, *tris, m, *zvals);
        }
    }

    jit = 0.05*0.5*dx;
    jitter = vmath::vec3(_randomDouble(jit, -jit), 
                         _randomDouble(jit, -jit), 
                         _randomDouble(jit, -jit));
    for (int j = 0; j < zsubcollisions.height; j++) {
        for (int i = 0; i < zsubcollisions.width; i++) {
            int trigridi = (int)floor(0.5*i);
            int trigridj = (int)floor(0.5*j);

            tris = ztrigrid.getPointer(trigridi, trigridj, 0);
            if (tris->size() == 0) {
                continue;
            }

            zvals = zsubcollisions.getPointer(i, j, 0);
            zvals->reserve(tris->size());
            gp = Grid3d::GridIndexToCellCenter(i, j, -1, 0.5*dx) + jitter;
            _getTriangleCollisionsZ(gp, *tris, m, *zvals);
        }
    }

}

bool isCellInside(double z, std::vector<double> *zvals) {
    if (zvals->size() % 2 != 0) {
        return false;
    }

    int numless = 0;
    for (unsigned int zidx = 0; zidx < zvals->size(); zidx++) {
        if (zvals->at(zidx) < z) {
            numless++;
        }
    }

    return numless % 2 == 1;
}

bool isCellInside(int i, int j, int k, double dx, std::vector<double> *zvals) {
    double z = Grid3d::GridIndexToCellCenter(i, j, k, dx).z;
    return isCellInside(z, zvals);
}

void sortInsideBorderCells(Array3d<bool> &cellgrid, 
                           std::vector<GridIndex> &insideCells, 
                           std::vector<GridIndex> &borderCells) {
    
    int isize = cellgrid.width;
    int jsize = cellgrid.height;
    int ksize = cellgrid.depth;
    Array3d<bool> isCellProcessed(isize, jsize, ksize, false);
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                if (cellgrid(i, j, k)) {
                    isCellProcessed.set(i, j, k, true);
                }
            }
        }
    }

    GridIndex nbs6[6];
    GridIndex nbs26[26];
    GridIndex g;
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                if (!cellgrid(i, j, k)) {
                    continue;
                }

                Grid3d::getNeighbourGridIndices6(i, j, k, nbs6);
                bool isInside = true;
                for (int nidx = 0; nidx < 6; nidx++) {
                    g = nbs6[nidx];
                    if (!Grid3d::isGridIndexInRange(g, isize, jsize, ksize) || 
                            !cellgrid(g)) {
                        isInside = false;
                        break;
                    }
                }

                if (isInside) {
                    insideCells.push_back(GridIndex(i, j, k));
                    continue;
                }

                borderCells.push_back(GridIndex(i, j, k));
                Grid3d::getNeighbourGridIndices26(i, j, k, nbs26);
                for (int nidx = 0; nidx < 26; nidx++) {
                    g = nbs26[nidx];
                    if (!Grid3d::isGridIndexInRange(g, isize, jsize, ksize) ||
                            isCellProcessed(g)) {
                        continue;
                    }

                    borderCells.push_back(g);
                    isCellProcessed.set(g, true);
                }
            }
        }
    }

}

unsigned char getCellFillMask(GridIndex g, double dx,
                              Array3d<std::vector<double> > &zsubcollisions) {
    unsigned char mask = 0;
    GridIndex subg(2 * g.i, 2 * g.j, 2 * g.k);

    std::vector<double> *zvals = zsubcollisions.getPointer(subg.i, subg.j, 0);
    if (isCellInside(subg.i, subg.j, subg.k, dx, zvals)) {
        mask |= 1;
    }

    zvals = zsubcollisions.getPointer(subg.i + 1, subg.j, 0);
    if (isCellInside(subg.i + 1, subg.j, subg.k, dx, zvals)) {
        mask |= 2;
    }

    zvals = zsubcollisions.getPointer(subg.i, subg.j + 1, 0);
    if (isCellInside(subg.i, subg.j + 1, subg.k, dx, zvals)) {
        mask |= 4;
    }

    zvals = zsubcollisions.getPointer(subg.i + 1, subg.j + 1, 0);
    if (isCellInside(subg.i + 1, subg.j + 1, subg.k, dx, zvals)) {
        mask |= 8;
    }

    zvals = zsubcollisions.getPointer(subg.i, subg.j, 0);
    if (isCellInside(subg.i, subg.j, subg.k + 1, dx, zvals)) {
        mask |= 16;
    }

    zvals = zsubcollisions.getPointer(subg.i + 1, subg.j, 0);
    if (isCellInside(subg.i + 1, subg.j, subg.k + 1, dx, zvals)) {
        mask |= 32;
    }

    zvals = zsubcollisions.getPointer(subg.i, subg.j + 1, 0);
    if (isCellInside(subg.i, subg.j + 1, subg.k + 1, dx, zvals)) {
        mask |= 64;
    }

    zvals = zsubcollisions.getPointer(subg.i + 1, subg.j + 1, 0);
    if (isCellInside(subg.i + 1, subg.j + 1, subg.k + 1, dx, zvals)) {
        mask |= 128;
    }

    return mask;
}

void getCellsInsideTriangleMeshSubd2(
        TriangleMesh &m, int isize, int jsize, int ksize, double dx,
        std::vector<GridIndex> &cells, std::vector<unsigned char> &cell_masks) {

    Array3d<std::vector<double> > zcollisions(isize, jsize, 1);
    Array3d<std::vector<double> > zsubcollisions(2*isize, 2*jsize, 1);
    _getCollisionGridZSubd2(m, dx, zcollisions, zsubcollisions);

    Array3d<bool> cellgrid(isize, jsize, ksize, false);
    std::vector<double> *zvals;
    int cellCount = 0;
    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                zvals = zcollisions.getPointer(i, j, 0);
                if (isCellInside(i, j, k, dx, zvals)) {
                    cellgrid.set(i, j, k, true);
                    cellCount++;
                }
            }
        }
    }

    std::vector<GridIndex> insideCells;
    std::vector<GridIndex> borderCells;
    insideCells.reserve(cellCount / 2);
    borderCells.reserve(cellCount / 2);
    sortInsideBorderCells(cellgrid, insideCells, borderCells);

    Array3d<unsigned char> maskGrid(isize, jsize, ksize, 0);
    for (unsigned int i = 0; i < insideCells.size(); i++) {
        maskGrid.set(insideCells[i], 255);
    }

    double hdx = 0.5 * dx;
    for (unsigned int i = 0; i < borderCells.size(); i++) {
        unsigned char mask = getCellFillMask(borderCells[i], hdx, zsubcollisions);
        maskGrid.set(borderCells[i], mask);
    }

    for (int k = 0; k < ksize; k++) {
        for (int j = 0; j < jsize; j++) {
            for (int i = 0; i < isize; i++) {
                if (maskGrid(i, j, k) != 0) {
                    cells.push_back(GridIndex(i, j, k));
                    cell_masks.push_back(maskGrid(i, j, k));
                }
            }
        }
    }

}

void getCellsInsideTriangleMeshSubd2(
        TriangleMesh mesh, double dx,
        std::vector<GridIndex> &cells, std::vector<unsigned char> &cell_masks) {

    AABB bbox(mesh.vertices);
    GridIndex goffset = Grid3d::positionToGridIndex(bbox.position, dx);
    vmath::vec3 offset = Grid3d::GridIndexToPosition(goffset, dx);
    mesh.translate(-offset);
    bbox.position -= offset;

    int inf = std::numeric_limits<int>::max();
    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(bbox, dx, inf, inf, inf, &gmin, &gmax);

    MeshUtils::getCellsInsideTriangleMeshSubd2(
        mesh, gmax.i + 1, gmax.j + 1, gmax.k + 1, dx, cells, cell_masks
    );

    for (unsigned int i = 0; i < cells.size(); i++) {
        cells[i].i = cells[i].i + goffset.i;
        cells[i].j = cells[i].j + goffset.j;
        cells[i].k = cells[i].k + goffset.k;
    }
}

void getGridNodesInsideTriangleMesh(TriangleMesh mesh, double dx, 
                                    std::vector<GridIndex> &nodes) {
    mesh.translate(vmath::vec3(0.5 * dx, 0.5 * dx, 0.5 * dx));
    AABB bbox(mesh.vertices);

    GridIndex goffset = Grid3d::positionToGridIndex(bbox.position, dx);
    vmath::vec3 offset = Grid3d::GridIndexToPosition(goffset, dx);
    mesh.translate(-offset);
    bbox.position -= offset;

    int inf = std::numeric_limits<int>::max();
    GridIndex gmin, gmax;
    Grid3d::getGridIndexBounds(bbox, dx, inf, inf, inf, &gmin, &gmax);

    nodes.clear();
    MeshUtils::getCellsInsideTriangleMesh(
        mesh, gmax.i + 1, gmax.j + 1, gmax.k + 1, dx, nodes
    );

    GridIndex g;
    for (unsigned int i = 0; i < nodes.size(); i++) {
        g = nodes[i];
        nodes[i] = GridIndex(g.i + goffset.i, g.j + goffset.j, g.k + goffset.k);
    }
}

void getGridNodesInsideTriangleMesh(TriangleMesh mesh, double dx, 
                                    Array3d<bool> &nodes) {
    nodes.fill(false);

    int isize = nodes.width - 1;
    int jsize = nodes.height - 1;
    int ksize = nodes.depth - 1;
    AABB gridAABB(0.0, 0.0, 0.0, isize * dx, jsize * dx, ksize * dx);

    bool isMeshContainedInGrid = true;
    for (size_t i = 0; i < mesh.vertices.size(); i++) {
        if (!gridAABB.isPointInside(mesh.vertices[i])) {
            isMeshContainedInGrid = false;
            break;
        }
    }

    std::vector<GridIndex> nodeVector;
    if (isMeshContainedInGrid) {
        getGridNodesInsideTriangleMesh(mesh, dx, nodeVector);

        GridIndex g;
        for (size_t i = 0; i < nodeVector.size(); i++) {
            if (nodes.isIndexInRange(nodeVector[i])) {
                nodes.set(nodeVector[i], true);
            }
        }

        return;
    }

    TriangleMesh insideMesh;
    std::vector<TriangleMesh> outsideMeshes;
    _splitInsideOutsideMesh(mesh, gridAABB, insideMesh, outsideMeshes);

    getGridNodesInsideTriangleMesh(insideMesh, dx, nodeVector);

    GridIndex g;
    for (size_t i = 0; i < nodeVector.size(); i++) {
        if (nodes.isIndexInRange(nodeVector[i])) {
            nodes.set(nodeVector[i], true);
        }
    }

    for (size_t i = 0; i < outsideMeshes.size(); i++) {
        nodeVector.clear();
        getGridNodesInsideTriangleMesh(outsideMeshes[i], dx, nodeVector);

        GridIndex g;
        for (size_t i = 0; i < nodeVector.size(); i++) {
            if (nodes.isIndexInRange(nodeVector[i])) {
                nodes.set(nodeVector[i], true);
            }
        }
    }

}

void _splitInsideOutsideMesh(TriangleMesh &mesh, AABB bbox, 
                             TriangleMesh &insideMesh, 
                             std::vector<TriangleMesh> &outsideMeshes) {

    std::vector<TriangleMesh> meshIslands;
    std::vector<int> vertexToGroupID;
    std::vector<int> vertexTranslationTable;
    _splitIntoMeshIslands(mesh, meshIslands, vertexToGroupID, vertexTranslationTable);

    for (size_t i = 0; i < meshIslands.size(); i++) {
        AABB meshAABB(meshIslands[i].vertices);
        vmath::vec3 minp = meshAABB.getMinPoint();
        vmath::vec3 maxp = meshAABB.getMaxPoint();

        if (bbox.isPointInside(minp) && bbox.isPointInside(maxp)) {
            insideMesh.append(meshIslands[i]);
        } else {
            AABB inter = bbox.getIntersection(meshAABB);
            if (inter.width > 0.0 || inter.height > 0.0 || inter.depth > 0.0) {
                outsideMeshes.push_back(meshIslands[i]);
            }
        }
    }
}

void _splitIntoMeshIslands(TriangleMesh &mesh, 
                           std::vector<TriangleMesh> &islands,
                           std::vector<int> &vertexToGroupID,
                           std::vector<int> &vertexTranslationTable) {

    std::vector<std::vector<int> > vertexNeighbours(mesh.vertices.size());
    for (size_t i = 0; i < vertexNeighbours.size(); i++) {
        vertexNeighbours[i].reserve(10);
    }

    for (size_t i = 0; i < mesh.triangles.size(); i++) {
        Triangle t = mesh.triangles[i];

        vertexNeighbours[t.tri[0]].push_back(t.tri[1]);
        vertexNeighbours[t.tri[0]].push_back(t.tri[2]);

        vertexNeighbours[t.tri[1]].push_back(t.tri[0]);
        vertexNeighbours[t.tri[1]].push_back(t.tri[2]);

        vertexNeighbours[t.tri[2]].push_back(t.tri[0]);
        vertexNeighbours[t.tri[2]].push_back(t.tri[1]);
    }

    vertexToGroupID = std::vector<int>(mesh.vertices.size(), -1);
    std::vector<bool> isVertexProcessed(mesh.vertices.size(), false);
    std::vector<int> vertexQueue;
    int groupID = 0;
    for (int vidx = 0; vidx < (int)mesh.vertices.size(); vidx++) {
        if (isVertexProcessed[vidx]) {
            continue;
        }

        vertexQueue.clear();
        vertexQueue.push_back(vidx);
        isVertexProcessed[vidx] = true;

        while (!vertexQueue.empty()) {
            int v = vertexQueue.back();
            vertexQueue.pop_back();

            for (size_t nidx = 0; nidx < vertexNeighbours[v].size(); nidx++) {
                if (!isVertexProcessed[vertexNeighbours[v][nidx]]) {
                    vertexQueue.push_back(vertexNeighbours[v][nidx]);
                    isVertexProcessed[vertexNeighbours[v][nidx]] = true;
                }
            }

            FLUIDSIM_ASSERT(vertexToGroupID[v] == -1);
            vertexToGroupID[v] = groupID;
        }

        groupID++;
    }
    vertexNeighbours.clear();
    vertexNeighbours.shrink_to_fit();

    int maxGroupID = 0;
    for (size_t i = 0; i < vertexToGroupID.size(); i++) {
        if (vertexToGroupID[i] > maxGroupID) {
            maxGroupID = vertexToGroupID[i];
        }
    }

    std::vector<int> vertexGroupCounts(maxGroupID + 1, 0);
    for (size_t i = 0; i < vertexToGroupID.size(); i++) {
        vertexGroupCounts[vertexToGroupID[i]]++;
    }

    std::vector<int> triangleGroupCounts(maxGroupID + 1, 0);
    for (size_t i = 0; i < mesh.triangles.size(); i++) {
        Triangle t = mesh.triangles[i];
        int tvert = t.tri[0];
        triangleGroupCounts[vertexToGroupID[tvert]]++;
    }

    islands.clear();
    islands.reserve(maxGroupID + 1);
    for (int i = 0; i < maxGroupID + 1; i++) {
        islands.push_back(TriangleMesh());
        islands[i].vertices.reserve(vertexGroupCounts[i]);
        islands[i].triangles.reserve(triangleGroupCounts[i]);
    }

    vertexTranslationTable = std::vector<int>(mesh.vertices.size(), -1);
    for (size_t i = 0; i < mesh.triangles.size(); i++) {
        Triangle t = mesh.triangles[i];
        int groupID = vertexToGroupID[t.tri[0]];
        islands[groupID].triangles.push_back(t);

        for (int tvidx = 0; tvidx < 3; tvidx++) {
            int vidx = t.tri[tvidx];
            if (vertexTranslationTable[vidx] == -1) {
                vertexTranslationTable[vidx] = (int)islands[groupID].vertices.size();
                islands[groupID].vertices.push_back(mesh.vertices[vidx]);
            }
        }
    }

    for (size_t i = 0; i < islands.size(); i++) {
        for (size_t tidx = 0; tidx < islands[i].triangles.size(); tidx++) {
            Triangle t = islands[i].triangles[tidx];
            t.tri[0] = vertexTranslationTable[t.tri[0]];
            t.tri[1] = vertexTranslationTable[t.tri[1]];
            t.tri[2] = vertexTranslationTable[t.tri[2]];
            islands[i].triangles[tidx] = t;
        }
    }

}

void splitIntoMeshIslands(TriangleMesh &mesh, 
                          std::vector<vmath::vec3> &vertexVelocities,
                          std::vector<TriangleMesh> &islands, 
                          std::vector<std::vector<vmath::vec3> > &islandVertexVelocities) {

    std::vector<int> vertexToIslandID;
    std::vector<int> vertexTranslationTable;
    _splitIntoMeshIslands(mesh, islands, vertexToIslandID, vertexTranslationTable);

    islandVertexVelocities.reserve(islands.size());
    for (size_t i = 0; i < islands.size(); i++) {
        std::vector<vmath::vec3> velocities(islands[i].vertices.size());
        islandVertexVelocities.push_back(velocities);
    }

    for (size_t vidx = 0; vidx < vertexVelocities.size(); vidx++) {
        int islandID = vertexToIslandID[vidx];
        int newvidx = vertexTranslationTable[vidx];
        islandVertexVelocities[islandID][newvidx] = vertexVelocities[vidx];
    }
}


void extrapolateGrid(Array3d<float> *grid, Array3d<bool> *valid, int numLayers) {
    char UNKNOWN = 0x00;
    char WAITING = 0x01;
    char KNOWN = 0x02;
    char DONE = 0x03;

    Array3d<char> status(grid->width, grid->height, grid->depth);
    for(int k = 0; k < grid->depth; k++) {
        for(int j = 0; j < grid->height; j++) {
            for(int i = 0; i < grid->width; i++) {
                status.set(i, j, k, valid->get(i, j, k) ? KNOWN : UNKNOWN);
                if (status(i, j, k) == UNKNOWN && 
                        Grid3d::isGridIndexOnBorder(i, j, k, grid->width, grid->height, grid->depth)) {
                    status.set(i, j, k, DONE);
                }
            }
        }
    }

    std::vector<GridIndex> extrapolationCells;
    for (int layers = 0; layers < numLayers; layers++) {

        extrapolationCells.clear();
        for(int k = 1; k < grid->depth - 1; k++) {
            for(int j = 1; j < grid->height - 1; j++) {
                for(int i = 1; i < grid->width - 1; i++) {
                    if (status(i, j, k) != KNOWN) { 
                        continue; 
                    }

                    int count = 0;
                    if (status(i - 1, j, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i - 1, j, k));
                        status.set(i - 1, j, k, WAITING);
                        count++;
                    } else if (status(i - 1, j, k) == WAITING) {
                        count++;
                    }

                    if (status(i + 1, j, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i + 1, j, k));
                        status.set(i + 1, j, k, WAITING);
                        count++;
                    } else if (status(i + 1, j, k) == WAITING) {
                        count++;
                    }

                    if (status(i, j - 1, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j - 1, k));
                        status.set(i, j - 1, k, WAITING);
                        count++;
                    } else if (status(i, j - 1, k) == WAITING) {
                        count++;
                    }

                    if (status(i, j + 1, k) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j + 1, k));
                        status.set(i, j + 1, k, WAITING);
                        count++;
                    } else if (status(i, j + 1, k) == WAITING) {
                        count++;
                    }

                    if (status(i, j, k - 1) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j, k - 1));
                        status.set(i, j, k - 1, WAITING);
                        count++;
                    } else if (status(i, j, k - 1) == WAITING) {
                        count++;
                    }

                    if (status(i, j, k + 1) == UNKNOWN) {
                        extrapolationCells.push_back(GridIndex(i, j, k + 1));
                        status.set(i, j, k + 1, WAITING);
                        count++;
                    } else if (status(i, j, k + 1) == WAITING) {
                        count++;
                    }

                    if (count == 0) {
                        status.set(i, j, k, DONE);
                    }
                }
            }
        }

        if (extrapolationCells.empty()) {
            return;
        }

        GridIndex g;
        for (size_t i = 0; i < extrapolationCells.size(); i++) {
            g = extrapolationCells[i];

            float sum = 0;
            int count = 0;
            if(status(g.i - 1, g.j, g.k) == KNOWN) { sum += grid->get(g.i - 1, g.j, g.k); count++; }
            if(status(g.i + 1, g.j, g.k) == KNOWN) { sum += grid->get(g.i + 1, g.j, g.k); count++; }
            if(status(g.i, g.j - 1, g.k) == KNOWN) { sum += grid->get(g.i, g.j - 1, g.k); count++; }
            if(status(g.i, g.j + 1, g.k) == KNOWN) { sum += grid->get(g.i, g.j + 1, g.k); count++; }
            if(status(g.i, g.j, g.k - 1) == KNOWN) { sum += grid->get(g.i, g.j, g.k - 1); count++; }
            if(status(g.i, g.j, g.k + 1) == KNOWN) { sum += grid->get(g.i, g.j, g.k + 1); count++; }

            FLUIDSIM_ASSERT(count != 0)
            grid->set(g, sum /(float)count);
        }
        status.set(extrapolationCells, KNOWN);

    }

}

}