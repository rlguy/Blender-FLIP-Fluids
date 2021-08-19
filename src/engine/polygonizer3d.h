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

#ifndef FLUIDENGINE_POLYGONIZER3D_H
#define FLUIDENGINE_POLYGONIZER3D_H

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include "threadutils.h"
#include "array3d.h"
#include "vmath.h"

class ScalarField;
class TriangleMesh;
class MeshLevelSet;

class Polygonizer3d
{
public:
    Polygonizer3d();
    Polygonizer3d(ScalarField *scalarField);
    Polygonizer3d(ScalarField *scalarField, MeshLevelSet *solidSDF);

    ~Polygonizer3d();

    void setSurfaceCellMask(Array3d<bool> *mask);
    TriangleMesh polygonizeSurface();

private:
    struct EdgeGrid {
        Array3d<int> U;         // store index to vertex
        Array3d<int> V;
        Array3d<int> W;

        EdgeGrid() : U(Array3d<int>(0, 0, 0)),
                     V(Array3d<int>(0, 0, 0)),
                     W(Array3d<int>(0, 0, 0)) {}

        EdgeGrid(int i, int j, int k) : 
                     U(Array3d<int>(i, j + 1, k + 1, -1)),
                     V(Array3d<int>(i + 1, j, k + 1, -1)),
                     W(Array3d<int>(i + 1, j + 1, k, -1)) {}
    };

    vmath::vec3 _getVertexPosition(GridIndex v);
    double _getVertexFieldValue(GridIndex v);
    void _polygonizeCell(GridIndex g, EdgeGrid &edges, TriangleMesh &mesh);
    int _calculateCubeIndex(GridIndex g);
    void _calculateVertexList(GridIndex g,
                              int cubeIndex, 
                              EdgeGrid &edges, 
                              std::vector<vmath::vec3> &meshVertices, 
                              int vertList[12]);
    vmath::vec3 _vertexInterp(vmath::vec3 p1, vmath::vec3 p2, double valp1, double valp2);
    void _calculateSurfaceTriangles(Array3d<bool> &isSurfaceCell, TriangleMesh &mesh);
    void _findSurfaceCells(Array3d<bool> &isSurfaceCell);
    void _getCellNodeStatusThread(GridIndex gridOffset, 
                                  Array3d<bool> *hasInsideNode, 
                                  Array3d<bool> *hasOutsideNode);


    static const int _edgeTable[256];
    static const int _triTable[256][16];

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    double _surfaceThreshold = 0.5;

    ScalarField *_scalarField;
    bool _isScalarFieldSet = false;

    MeshLevelSet *_solidSDF;
    bool _isSolidSDFSet = false;

    Array3d<bool> *_surfaceCellMask;
    bool _isSurfaceCellMaskSet = false;

};

#endif
