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

#ifndef FLUIDENGINE_MESHUTILS_H
#define FLUIDENGINE_MESHUTILS_H

#include "array3d.h"
#include "vmath.h"

class TriangleMesh;
class AABB;

namespace MeshUtils {
    typedef struct TriangleMesh_t {
        float *vertices;
        int *triangles;
        int numVertices;
        int numTriangles;
    } TriangleMesh_t;

    void structToTriangleMesh(TriangleMesh_t &mesh_data, TriangleMesh &mesh);

    void _getTriangleGridZ(
        TriangleMesh &m, double dx, Array3d<std::vector<int> > &ztrigrid);

    void _getTriangleCollisionsZ(
        vmath::vec3 origin, std::vector<int> &indices, TriangleMesh &m,
        std::vector<double> &collisions);

    double _randomDouble(double min, double max);

    void _getCollisionGridZ(
        TriangleMesh &m, double dx, Array3d<std::vector<double> > &zcollisions);

    void getCellsInsideTriangleMesh(
        TriangleMesh &m, int isize, int jsize, int ksize, double dx,
        std::vector<GridIndex> &cells);

    void _getCollisionGridZSubd2(
        TriangleMesh &m, double dx, 
        Array3d<std::vector<double> > &zcollisions,
        Array3d<std::vector<double> > &zsubcollisions);

    bool isCellInside(double z, std::vector<double> *zvals);

    bool isCellInside(int i, int j, int k, double dx, std::vector<double> *zvals);

    void sortInsideBorderCells(
        Array3d<bool> &cellgrid, 
        std::vector<GridIndex> &insideCells, 
        std::vector<GridIndex> &borderCells);

    unsigned char getCellFillMask(
        GridIndex g, double dx, Array3d<std::vector<double> > &zsubcollisions);


    void getCellsInsideTriangleMeshSubd2(
        TriangleMesh &m, int isize, int jsize, int ksize, double dx,
        std::vector<GridIndex> &cells, std::vector<unsigned char> &cell_masks);

    void getCellsInsideTriangleMeshSubd2(
        TriangleMesh mesh, double dx,
        std::vector<GridIndex> &cells, std::vector<unsigned char> &cell_masks);

    void getGridNodesInsideTriangleMesh(TriangleMesh mesh, double dx, 
                                        Array3d<bool> &nodes);

    void getGridNodesInsideTriangleMesh(TriangleMesh mesh, double dx, 
                                        std::vector<GridIndex> &nodes);

    void _splitInsideOutsideMesh(TriangleMesh &mesh, AABB bbox, 
                                 TriangleMesh &insideMesh, 
                                 std::vector<TriangleMesh> &outsideMeshes);

    void _splitIntoMeshIslands(TriangleMesh &mesh, 
                               std::vector<TriangleMesh> &islands,
                               std::vector<int> &vertexToGroupID,
                               std::vector<int> &vertexTranslationTable);

    void splitIntoMeshIslands(TriangleMesh &mesh, 
                              std::vector<vmath::vec3> &vertexVelocities,
                              std::vector<TriangleMesh> &islands, 
                              std::vector<std::vector<vmath::vec3> > &islandVertexVelocities);

    void extrapolateGrid(Array3d<float> *grid, Array3d<bool> *valid, int numLayers);

}

#endif