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

#ifndef FLUIDENGINE_TRIANGLEMESH_H
#define FLUIDENGINE_TRIANGLEMESH_H

#include <string>
#include <vector>
#include <sstream>

#include "vmath.h"
#include "triangle.h"

class AABB;

enum class TriangleMeshFormat : char { 
    ply   = 0x00, 
    bobj  = 0x01
};

class TriangleMesh
{
public:
    TriangleMesh();
    ~TriangleMesh();

    bool loadPLY(std::string PLYFilename);
    bool loadBOBJ(std::string BOBJFilename);
    void writeMeshToPLY(std::string filename);
    void writeMeshToBOBJ(std::string filename);
    void getMeshFileDataPLY(std::vector<char> &data);
    void getMeshFileDataBOBJ(std::vector<char> &data);
    static std::string getFileExtension(TriangleMeshFormat fmt);

    int numVertices();
    int numTriangles();
    void clear();
    void removeDuplicateTriangles();
    void updateVertexTriangles();
    void clearVertexTriangles();
    void smooth(double value, int iterations);
    std::vector<vmath::vec3> smoothColors(double value, int iterations, std::vector<vmath::vec3> colors);
    void getFaceNeighbours(unsigned int tidx, std::vector<int> &n);
    void getFaceNeighbours(Triangle t, std::vector<int> &n);
    void getVertexNeighbours(unsigned int vidx, std::vector<int> &n);
    void getTrianglePosition(unsigned int index, vmath::vec3 tri[3]);
    vmath::vec3 getTriangleCenter(unsigned int index);
    vmath::vec3 getCentroid();
    void removeMinimumTriangleCountPolyhedra(int count);
    void removeTriangles(std::vector<int> &triangles);
    std::vector<int> removeExtraneousVertices();
    void translate(vmath::vec3 trans);
    void scale(vmath::vec3 scale);
    void append(TriangleMesh &mesh);
    void join(TriangleMesh &mesh);
    void join(TriangleMesh &mesh, double tolerance);
    void removeDuplicateVertices(int i, int j, int k, double dx);

    std::vector<vmath::vec3> vertices;
    std::vector<Triangle> triangles;

private:
    bool _getPLYHeader(std::ifstream *file, std::string *header);
    bool _getElementNumberInPlyHeader(std::string &header, 
                                      std::string &element, int *n);
    bool _getNumVerticesInPLYHeader(std::string &header, int *n);
    bool _getNumFacesInPLYHeader(std::string &header, int *n);
    bool _loadPLYVertexData(std::ifstream *file, std::string &header);
    bool _loadPLYTriangleData(std::ifstream *file, std::string &header);

    void _updateVertexTriangles();
    bool _trianglesEqual(Triangle &t1, Triangle &t2);
    void _smoothTriangleMesh(double value);
    std::vector<vmath::vec3> _smoothTriangleMeshColors(double value, std::vector<vmath::vec3> &colors);

    void _getPolyhedra(std::vector<std::vector<int> > &polyList);
    void _getPolyhedronFromTriangle(int triangle, 
                                    std::vector<bool> &visitedTriangles,
                                    std::vector<int> &polyhedron);
    AABB _getMeshVertexIntersectionAABB(std::vector<vmath::vec3> verts1,
                                        std::vector<vmath::vec3> verts2, 
                                        double tolerance);
    void _findDuplicateVertexPairs(int i, int j, int k, double dx, 
                                   std::vector<std::pair<int, int> > &pairs);
    void _findDuplicateVertexPairs(std::vector<int> &verts1, 
                                   std::vector<int> &verts2, 
                                   AABB bbox,
                                   double tolerance, 
                                   std::vector<std::pair<int, int> > &pairs);

    template<class T>
    std::string _toString(T item) {
        std::ostringstream sstream;
        sstream << item;

        return sstream.str();
    }

    std::vector<std::vector<int> > _vertexTriangles;
};

#endif
