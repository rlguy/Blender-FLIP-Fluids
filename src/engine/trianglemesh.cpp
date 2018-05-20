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

#include "trianglemesh.h"

#include <fstream>
#include <cstring>
#include <algorithm>

#include "fluidsimassert.h"
#include "spatialpointgrid.h"

TriangleMesh::TriangleMesh() {
}

TriangleMesh::~TriangleMesh() {
}

int TriangleMesh::numVertices() {
    return (int)vertices.size();
}

int TriangleMesh::numTriangles() {
    return (int)triangles.size();
}

void TriangleMesh::clear() {
    vertices.clear();
    triangles.clear();
    _vertexTriangles.clear();
}

bool TriangleMesh::loadPLY(std::string PLYFilename) {
    clear();

    std::ifstream file(PLYFilename.c_str(), std::ios::in | std::ios::binary);
    if (!file.is_open()) {
        return false;
    }

    std::string header;
    bool success = _getPLYHeader(&file, &header);
    if (!success) {
        return false;
    }

    success = _loadPLYVertexData(&file, header);
    if (!success) {
        return false;
    }

    success = _loadPLYTriangleData(&file, header);
    if (!success) {
        return false;
    }

    return true;
}

bool TriangleMesh::loadBOBJ(std::string BOBJFilename) {
    std::ifstream file(BOBJFilename.c_str(), std::ios::in | std::ios::binary);
    if (!file.is_open()) {
        return false;
    }

    int numverts;
    file.read((char *)&numverts, sizeof(int));
    if (!file.good() || numverts < 0) {
        return false;
    }
    
    int binsize = 3 * numverts * sizeof(float);
    std::vector<vmath::vec3> vertices(numverts);
    if (numverts > 0) {
        file.read((char *)vertices.data(), binsize);
        if (!file.good()) {
            return false;
        }
    }

    int numfaces;
    file.read((char *)&numfaces, sizeof(int));
    if (!file.good() || numfaces < 0) {
        return false;
    }

    binsize = 3 * numfaces * sizeof(int);
    std::vector<Triangle> triangles(numfaces);
    if (numfaces > 0) {
        file.read((char *)triangles.data(), binsize);
        if (!file.good()) {
            return false;
        }
    }

    this->vertices = vertices;
    this->triangles = triangles;

    return true;
}

void TriangleMesh::writeMeshToPLY(std::string filename) {
    std::vector<char> data;
    getMeshFileDataPLY(data);

    std::ofstream erasefile;
    erasefile.open(filename, std::ofstream::out | std::ofstream::trunc);
    erasefile.close();

    std::ofstream ply(filename.c_str(), std::ios::out | std::ios::binary);
    ply.write(data.data(), data.size());
    ply.close();
}

void TriangleMesh::writeMeshToBOBJ(std::string filename) {
    std::vector<char> data;
    getMeshFileDataBOBJ(data);

    std::ofstream erasefile;
    erasefile.open(filename, std::ofstream::out | std::ofstream::trunc);
    erasefile.close();

    std::ofstream bobj(filename.c_str(), std::ios::out | std::ios::binary);
    bobj.write(data.data(), data.size());
    bobj.close();
}

void TriangleMesh::getMeshFileDataPLY(std::vector<char> &data) {
    // Header format:
    /*
        ply
        format binary_little_endian 1.0
        element vertex FILL_IN_NUMBER_OF_VERTICES
        property float x
        property float y
        property float z
        element face FILL_IN_NUMBER_OF_FACES
        property list uchar int vertex_index
        end_header
    */
    
    char header1[51] = {'p', 'l', 'y', '\n', 
                        'f', 'o', 'r', 'm', 'a', 't', ' ', 'b', 'i', 'n', 'a', 'r', 'y', '_', 'l', 
                        'i', 't', 't', 'l', 'e', '_', 'e', 'n', 'd', 'i', 'a', 'n', ' ', '1', '.', '0', '\n',
                        'e', 'l', 'e', 'm', 'e', 'n', 't', ' ', 'v', 'e', 'r', 't', 'e', 'x', ' '};
                    
    char header2[65] = {'\n', 'p', 'r', 'o', 'p', 'e', 'r', 't', 'y', ' ', 'f', 'l', 'o', 'a', 't', ' ', 'x', '\n',
                              'p', 'r', 'o', 'p', 'e', 'r', 't', 'y', ' ', 'f', 'l', 'o', 'a', 't', ' ', 'y', '\n',
                              'p', 'r', 'o', 'p', 'e', 'r', 't', 'y', ' ', 'f', 'l', 'o', 'a', 't', ' ', 'z', '\n',
                              'e', 'l', 'e', 'm', 'e', 'n', 't', ' ', 'f', 'a', 'c', 'e', ' '};
                          
    char header3[49] = {'\n', 'p', 'r', 'o', 'p', 'e', 'r', 't', 'y', ' ', 'l', 'i', 's', 't', ' ', 
                              'u', 'c', 'h', 'a', 'r', ' ', 'i', 'n', 't', ' ', 
                              'v', 'e', 'r', 't', 'e', 'x', '_', 'i', 'n', 'd', 'e', 'x', '\n',
                              'e', 'n', 'd', '_', 'h', 'e', 'a', 'd', 'e', 'r', '\n'};

    std::string vertstring = _toString(vertices.size());
    std::string facestring = _toString(triangles.size());
    int vertdigits = (int)vertstring.length();
    int facedigits = (int)facestring.length();

    int offset = 0;
    int headersize = 51 + vertdigits + 65 + facedigits + 49;

    int dataSize = headersize + 3*sizeof(float)*(int)vertices.size()
                   + (sizeof(unsigned char) + 3*sizeof(int))*(int)triangles.size();

    data.clear();
    data.resize(dataSize);
    data.shrink_to_fit();

    std::memcpy(data.data() + offset, &header1, 51);
    offset += 51;
    std::memcpy(data.data() + offset, vertstring.c_str(), vertdigits*sizeof(char));
    offset += vertdigits*sizeof(char);

    std::memcpy(data.data() + offset, header2, 65);
    offset += 65;

    std::memcpy(data.data() + offset, facestring.c_str(), facedigits*sizeof(char));
    offset += facedigits*sizeof(char);
    std::memcpy(data.data() + offset, header3, 49);
    offset += 49;

    float *vertdata = new float[3*vertices.size()];
    vmath::vec3 v;
    for (unsigned int i = 0; i < vertices.size(); i++) {
        v = vertices[i];
        vertdata[3*i] = v.x;
        vertdata[3*i + 1] = v.y;
        vertdata[3*i + 2] = v.z;
    }
    std::memcpy(data.data() + offset, vertdata, 3*sizeof(float)*vertices.size());
    offset += 3*sizeof(float)*(int)vertices.size();
    delete[] vertdata;

    Triangle t;
    int verts[3];
    for (unsigned int i = 0; i < triangles.size(); i++) {
        t = triangles[i];
        verts[0] = t.tri[0];
        verts[1] = t.tri[1];
        verts[2] = t.tri[2];

        data[offset] = 0x03;
        offset += sizeof(unsigned char);

        std::memcpy(data.data() + offset, verts, 3*sizeof(int));
        offset += 3*sizeof(int);
    }
}

void TriangleMesh::getMeshFileDataBOBJ(std::vector<char> &data) {
    int numVertices = (int)vertices.size();
    int numTriangles = (int)triangles.size();
    int vertexDataSize = 3 * numVertices * sizeof(float);
    int triangleDataSize = 3 * numTriangles * sizeof(int);
    int dataSize = sizeof(int) + vertexDataSize + sizeof(int) + triangleDataSize;

    data.clear();
    data.resize(dataSize);
    data.shrink_to_fit();

    int byteOffset = 0;
    std::memcpy(data.data() + byteOffset, &numVertices, sizeof(int));
    byteOffset += sizeof(int);

    std::memcpy(data.data() + byteOffset, (char *)vertices.data(), vertexDataSize);
    byteOffset += vertexDataSize;

    std::memcpy(data.data() + byteOffset, &numTriangles, sizeof(int));
    byteOffset += sizeof(int);

    std::memcpy(data.data() + byteOffset, (char *)triangles.data(), triangleDataSize);
    byteOffset += triangleDataSize;
}

std::string TriangleMesh::getFileExtension(TriangleMeshFormat fmt) {
    if (fmt == TriangleMeshFormat::ply) {
        return "ply";
    } else {
        return "bobj";
    }
}

bool triangleSort(const Triangle &a, const Triangle &b)
{
    if (a.tri[0]==b.tri[0]) {
        if (a.tri[1]==b.tri[1]) {
            return a.tri[2] < b.tri[2];
        } else {
            return a.tri[1] < b.tri[1];
        }
    } else {
        return a.tri[0] < b.tri[0];
    }
}

void TriangleMesh::removeDuplicateTriangles() {
    std::vector<Triangle> uniqueTriangles;

    std::sort(triangles.begin(), triangles.end(), triangleSort);
    Triangle last;
    for (unsigned int i = 0; i < triangles.size(); i++) {
        Triangle t = triangles[i];

        if (!_trianglesEqual(t, last)) {
            uniqueTriangles.push_back(t);
        }
        last = t;
    }

    triangles.clear();
    triangles.insert(triangles.end(), uniqueTriangles.begin(), uniqueTriangles.end());
}

void TriangleMesh::getFaceNeighbours(unsigned int tidx, std::vector<int> &n) {
    FLUIDSIM_ASSERT(tidx < triangles.size());
    getFaceNeighbours(triangles[tidx], n);
}

void TriangleMesh::getFaceNeighbours(Triangle t, std::vector<int> &n) {
    FLUIDSIM_ASSERT(vertices.size() == _vertexTriangles.size());

    std::vector<int> vn;
    for (int i = 1; i < 3; i++) {
        vn = _vertexTriangles[t.tri[i]];
        n.insert(n.end(), vn.begin(), vn.end());
    }
}

void TriangleMesh::getVertexNeighbours(unsigned int vidx, std::vector<int> &n) {
    FLUIDSIM_ASSERT(vertices.size() == _vertexTriangles.size());
    FLUIDSIM_ASSERT(vidx < vertices.size());
    std::vector<int> vn = _vertexTriangles[vidx];
    n.insert(n.end(), vn.begin(), vn.end());
}

bool TriangleMesh::_trianglesEqual(Triangle &t1, Triangle &t2) {
    return t1.tri[0] == t2.tri[0] &&
           t1.tri[1] == t2.tri[1] &&
           t1.tri[2] == t2.tri[2];
}

bool TriangleMesh::_getPLYHeader(std::ifstream *file, std::string *header) {
    file->seekg(0, std::ios_base::beg);

    int maxHeaderSize = 2048;
    char headerBufferChars[2048];
    file->read(headerBufferChars, maxHeaderSize);
    std::string headerBufferString(headerBufferChars, 2048);

    std::string endHeaderString("end_header\n");

    std::size_t match = headerBufferString.find(endHeaderString);
    if (match == std::string::npos) {
        return false;
    }

    *header = headerBufferString.substr(0, match + endHeaderString.size());

    return true;
}

bool TriangleMesh::_getElementNumberInPlyHeader(std::string &header, 
                                                std::string &element, int *n) {
    std::size_t match = header.find(element);
    if (match == std::string::npos) {
        return false;
    }

    int startidx = (int)match + (int)element.size();
    int endidx = 0;
    bool numberFound = false;

    for (unsigned int i = startidx; i < header.size(); i++) {
        if (header[i] == '\n') {
            endidx = i - 1;
            numberFound = true;
            break;
        }
    }

    if (!numberFound) {
        return false;
    }

    std::string numberString = header.substr(startidx, endidx - startidx + 1);
    std::istringstream ss(numberString);
    ss >> *n;

    if (ss.fail()) {
        return false;
    }

    return true;
}

bool TriangleMesh::_getNumVerticesInPLYHeader(std::string &header, int *n) {
    std::string vertexString("element vertex ");
    bool success = _getElementNumberInPlyHeader(header, vertexString, n);

    return success;
}

bool TriangleMesh::_getNumFacesInPLYHeader(std::string &header, int *n) {
    std::string faceString("element face ");
    bool success = _getElementNumberInPlyHeader(header, faceString, n);

    return success;
}

bool TriangleMesh::_loadPLYVertexData(std::ifstream *file, std::string &header) {
    int numVertices;
    bool success = _getNumVerticesInPLYHeader(header, &numVertices);
    if (!success) {
        return false;
    }

    if (numVertices == 0) {
        return true;
    }

    int vertexSize = 3*sizeof(float);
    int vertexDataSize = numVertices*vertexSize;
    int vertexDataOffset = (int)header.size();

    file->seekg(vertexDataOffset, std::ios_base::beg);
    char *vertexData = new char[vertexDataSize];
    if (!file->read(vertexData, vertexDataSize)) {
        return false;
    }

    vertices.reserve(numVertices);
    vertices.assign((vmath::vec3*)vertexData, (vmath::vec3*)vertexData + numVertices);
    delete[] vertexData;

    return true;
}

bool TriangleMesh::_loadPLYTriangleData(std::ifstream *file, std::string &header) {
    int numVertices;
    bool success = _getNumVerticesInPLYHeader(header, &numVertices);
    if (!success) {
        return false;
    }

    int vertexSize = 3*sizeof(float);

    int vertexDataSize = numVertices*vertexSize;
    int vertexDataOffset = (int)header.size();

    int numFaces;
    success = _getNumFacesInPLYHeader(header, &numFaces);
    if (!success) {
        return false;
    }

    if (numFaces == 0) {
        return true;
    }

    int faceSize = sizeof(char) + 3*sizeof(int);
    int faceDataSize = numFaces*faceSize;
    int faceDataOffset = vertexDataOffset + vertexDataSize;

    file->seekg(faceDataOffset, std::ios_base::beg);
    char *faceData = new char[faceDataSize];
    if (!file->read(faceData, faceDataSize)) {
        return false;
    }

    int offset = 0;
    Triangle t;
    triangles.reserve(numFaces);
    for (int i = 0; i < numFaces; i++) {
        unsigned int faceverts = faceData[offset];
        offset += sizeof(char);

        if (faceverts != 0x03) {
            return false;
        }

        memcpy(&(t.tri), faceData + offset, 3*sizeof(int));
        offset += 3*sizeof(int);

        if (t.tri[0] < 0 || t.tri[0] >= numVertices || 
            t.tri[1] < 0 || t.tri[1] >= numVertices || 
            t.tri[2] < 0 || t.tri[2] >= numVertices) {
            return false;
        }
        triangles.push_back(t);
    }

    delete[] faceData;

    return true;
}

void TriangleMesh::_updateVertexTriangles() {
    _vertexTriangles.clear();
    _vertexTriangles.reserve(vertices.size());

    for (unsigned int i = 0; i < vertices.size(); i++) {
        std::vector<int> triangles;
        triangles.reserve(14);  // 14 is the maximum number of adjacent triangles
                                // to a vertex
        _vertexTriangles.push_back(triangles);
    }

    Triangle t;
    for (unsigned int i = 0; i < triangles.size(); i++) {
        t = triangles[i];
        _vertexTriangles[t.tri[0]].push_back(i);
        _vertexTriangles[t.tri[1]].push_back(i);
        _vertexTriangles[t.tri[2]].push_back(i);
    }
}

void TriangleMesh::getTrianglePosition(unsigned int index, vmath::vec3 tri[3]) {
    FLUIDSIM_ASSERT(index < triangles.size());

    Triangle t = triangles[index];
    int size = (int)vertices.size();
    FLUIDSIM_ASSERT(t.tri[0] < size && t.tri[1] < size && t.tri[2] < size);

    tri[0] = vertices[t.tri[0]];
    tri[1] = vertices[t.tri[1]];
    tri[2] = vertices[t.tri[2]];
}

vmath::vec3 TriangleMesh::getTriangleCenter(unsigned int index) {
    FLUIDSIM_ASSERT(index < triangles.size());

    Triangle t = triangles[index];
    int size = (int)vertices.size();
    FLUIDSIM_ASSERT(t.tri[0] < size && t.tri[1] < size && t.tri[2] < size);

    return (vertices[t.tri[0]] + vertices[t.tri[1]] + vertices[t.tri[2]]) / 3.0f;
}

vmath::vec3 TriangleMesh::getCentroid() {
    vmath::vec3 c;
    for (size_t i = 0; i < vertices.size(); i++) {
        c += vertices[i];
    }

    if (!vertices.empty()) {
        c /= vertices.size();
    }

    return c;
}

void TriangleMesh::_smoothTriangleMesh(double value) {
    std::vector<vmath::vec3> newvertices;
    newvertices.reserve(vertices.size());

    vmath::vec3 v;
    vmath::vec3 nv;
    vmath::vec3 avg;
    Triangle t;
    for (unsigned int i = 0; i < vertices.size(); i++) {
        int count = 0;
        avg = vmath::vec3();
        for (unsigned int j = 0; j < _vertexTriangles[i].size(); j++) {
            t = triangles[_vertexTriangles[i][j]];
            if (t.tri[0] != (int)i) {
                avg += vertices[t.tri[0]];
                count++;
            }
            if (t.tri[1] != (int)i) {
                avg += vertices[t.tri[1]];
                count++;
            }
            if (t.tri[2] != (int)i) {
                avg += vertices[t.tri[2]];
                count++;
            }
        }

        avg /= (float)count;
        v = vertices[i];
        nv = v + (float)value * (avg - v);
        newvertices.push_back(nv);
    }

    vertices = newvertices;
}

void TriangleMesh::smooth(double value, int iterations) {
    _vertexTriangles.clear();
    _updateVertexTriangles();
    for (int i = 0; i < iterations; i++) {
        _smoothTriangleMesh(value);
    }
    _vertexTriangles.clear();
}

void TriangleMesh::updateVertexTriangles() {
    _updateVertexTriangles();
}

void TriangleMesh::clearVertexTriangles() {
    _vertexTriangles.clear();
}

void TriangleMesh::_getPolyhedronFromTriangle(int tidx, 
                                              std::vector<bool> &visitedTriangles,
                                              std::vector<int> &polyhedron) {

    FLUIDSIM_ASSERT(!visitedTriangles[tidx]);

    std::vector<int> queue;
    queue.push_back(tidx);
    visitedTriangles[tidx] = true;

    std::vector<int> neighbours;
    while (!queue.empty()) {
        int t = queue.back();
        queue.pop_back();

        neighbours.clear();
        getFaceNeighbours(t, neighbours);
        for (unsigned int i = 0; i < neighbours.size(); i++) {
            int n = neighbours[i];

            if (!visitedTriangles[n]) {
                queue.push_back(n);
                visitedTriangles[n] = true;
            }
        }

        polyhedron.push_back(t);
    }
}

void TriangleMesh:: _getPolyhedra(std::vector<std::vector<int> > &polyList) {
    updateVertexTriangles();

    std::vector<bool> visitedTriangles = std::vector<bool>(triangles.size(), false);
    for (unsigned int i = 0; i < visitedTriangles.size(); i++) {
        if (!visitedTriangles[i]) {
            std::vector<int> polyhedron;
            _getPolyhedronFromTriangle(i, visitedTriangles, polyhedron);
            polyList.push_back(polyhedron);
        }
    }

    clearVertexTriangles();
}

std::vector<int> TriangleMesh::removeExtraneousVertices() {

    std::vector<bool> unusedVertices = std::vector<bool>(vertices.size(), true);
    Triangle t;
    for (unsigned int i = 0; i < triangles.size(); i++) {
        t = triangles[i];
        unusedVertices[t.tri[0]] = false;
        unusedVertices[t.tri[1]] = false;
        unusedVertices[t.tri[2]] = false;
    }

    int unusedCount = 0;
    std::vector<int> unusedindices;
    for (unsigned int i = 0; i < unusedVertices.size(); i++) {
        if (unusedVertices[i]) {
            unusedCount++;
            unusedindices.push_back(i);
        }
    }

    if (unusedCount == 0) {
        return unusedindices;
    }

    std::vector<int> indexTranslationTable = std::vector<int>(vertices.size(), -1);
    std::vector<vmath::vec3> newVertexList;
    newVertexList.reserve(vertices.size() - unusedCount);

    int vidx = 0;
    for (unsigned int i = 0; i < unusedVertices.size(); i++) {
        if (!unusedVertices[i]) {
            newVertexList.push_back(vertices[i]);
            indexTranslationTable[i] = vidx;
            vidx++;
        }
    }
    newVertexList.shrink_to_fit();
    vertices = newVertexList;

    for (unsigned int i = 0; i < triangles.size(); i++) {
        t = triangles[i];
        t.tri[0] = indexTranslationTable[t.tri[0]];
        t.tri[1] = indexTranslationTable[t.tri[1]];
        t.tri[2] = indexTranslationTable[t.tri[2]];
        FLUIDSIM_ASSERT(t.tri[0] != -1 && t.tri[1] != -1 && t.tri[2] != -1);

        triangles[i] = t;
    }

    return unusedindices;
}

void TriangleMesh::removeTriangles(std::vector<int> &removalTriangles) {
    std::vector<bool> invalidTriangles = std::vector<bool>(triangles.size(), false);
    for (unsigned int i = 0; i < removalTriangles.size(); i++) {
        int tidx = removalTriangles[i];
        invalidTriangles[tidx] = true;
    }

    std::vector<Triangle> newTriangleList;
    for (unsigned int i = 0; i < triangles.size(); i++) {
        if (!invalidTriangles[i]) {
            newTriangleList.push_back(triangles[i]);
        }
    }

    triangles = newTriangleList;
}

void TriangleMesh::removeMinimumTriangleCountPolyhedra(int count) {
    if (count <= 0) {
        return;
    }

    std::vector<std::vector<int> > polyList;
    _getPolyhedra(polyList);

    std::vector<int> removalTriangles;
    for (unsigned int i = 0; i < polyList.size(); i++) {
        if ((int)polyList[i].size() <= count) {
            for (unsigned int j = 0; j < polyList[i].size(); j++) {
                removalTriangles.push_back(polyList[i][j]);
            }
        }
    }

    if (removalTriangles.size() == 0) {
        return;
    }

    removeTriangles(removalTriangles);
    removeExtraneousVertices();
}

void TriangleMesh::translate(vmath::vec3 trans) {
    for (size_t i = 0; i < vertices.size(); i++) {
        vertices[i] += trans;
    }
}

void TriangleMesh::scale(vmath::vec3 scale) {
    for (size_t i = 0; i < vertices.size(); i++) {
        vertices[i].x *= scale.x;
        vertices[i].y *= scale.y;
        vertices[i].z *= scale.z;
    }
}

void TriangleMesh::append(TriangleMesh &mesh) {
    vertices.reserve(vertices.size() + mesh.vertices.size());
    triangles.reserve(triangles.size() + mesh.triangles.size());

    int indexOffset = (int)vertices.size();

    vertices.insert(vertices.end(), mesh.vertices.begin(), mesh.vertices.end());

    Triangle t;
    for (unsigned int i = 0; i < mesh.triangles.size(); i++) {
        t = mesh.triangles[i];
        t.tri[0] += indexOffset;
        t.tri[1] += indexOffset;
        t.tri[2] += indexOffset;

        triangles.push_back(t);
    }
}

void TriangleMesh::join(TriangleMesh &mesh) {
    double tol = 10e-5;
    join(mesh, tol);
}

void TriangleMesh::join(TriangleMesh &mesh, double tolerance) {
    if (mesh.vertices.size() == 0) {
        return;
    }

    if (vertices.size() == 0) {
        append(mesh);
        return;
    }

    AABB bbox = _getMeshVertexIntersectionAABB(vertices, mesh.vertices, tolerance);

    unsigned int indexOffset = (unsigned int)vertices.size();
    append(mesh);

    std::vector<int> verts1;
    for (unsigned int i = 0; i < indexOffset; i++) {
        if (bbox.isPointInside(vertices[i])) {
            verts1.push_back(i);
        }
    }

    std::vector<int> verts2;
    for (unsigned int i = indexOffset; i < vertices.size(); i++) {
        if (bbox.isPointInside(vertices[i])) {
            verts2.push_back(i);
        }
    }

    std::vector<std::pair<int, int> > vertexPairs;
    _findDuplicateVertexPairs(verts1, verts2, bbox, tolerance, vertexPairs);

    std::vector<int> indexTable;
    indexTable.reserve(vertices.size());
    for (unsigned int i = 0; i < vertices.size(); i++) {
        indexTable.push_back(i);
    }

    for (unsigned int i = 0; i < vertexPairs.size(); i++) {
        indexTable[vertexPairs[i].second] = vertexPairs[i].first;
    }

    Triangle t;
    for (unsigned int i = 0; i < triangles.size(); i++) {
        t = triangles[i];
        t.tri[0] = indexTable[t.tri[0]];
        t.tri[1] = indexTable[t.tri[1]];
        t.tri[2] = indexTable[t.tri[2]];

        if (t.tri[0] == t.tri[1] || t.tri[1] == t.tri[2] || t.tri[2] == t.tri[0]) {
            // Don't collapse triangles
            continue;
        }

        triangles[i] = t;
    }

    removeExtraneousVertices();
}

AABB TriangleMesh::_getMeshVertexIntersectionAABB(std::vector<vmath::vec3> verts1,
                                                  std::vector<vmath::vec3> verts2, 
                                                  double tolerance) {
    AABB bbox1(verts1);
    AABB bbox2(verts2);

    bbox1.expand(2.0*tolerance);
    bbox2.expand(2.0*tolerance);

    AABB inter = bbox1.getIntersection(bbox2);

    return inter;
}

bool sortVertexPairByFirstIndex(const std::pair<int, int> &a,
                                const std::pair<int, int> &b) { 
    return a.first < b.first;
}

// Unique list of vertex pair indices sorted in order of first index.
// For each pair, first < second
void TriangleMesh::_findDuplicateVertexPairs(int i, int j, int k, double dx, 
                                             std::vector<std::pair<int, int> > &vertexPairs) {
    SpatialPointGrid grid(i, j, k, dx);
    std::vector<GridPointReference> refs = grid.insert(vertices);

    std::vector<bool> isPaired(vertices.size(), false);

    double eps = 10e-6;
    std::vector<GridPointReference> query;
    for (unsigned int i = 0; i < vertices.size(); i++) {

        if (isPaired[i]) {
            continue;
        }

        query.clear();
        grid.queryPointReferencesInsideSphere(refs[i], eps, query);

        if (query.size() == 0) {
            continue;
        }

        GridPointReference closestRef;
        if (query.size() == 1) {
            closestRef = query[0];
        } else {
            double mindist = std::numeric_limits<double>::infinity();

            for (unsigned int idx = 0; idx < query.size(); idx++) {
                vmath::vec3 v = vertices[i] - vertices[query[idx].id];
                double distsq = vmath::lengthsq(v);
                if (distsq < mindist) {
                    mindist = distsq;
                    closestRef = query[idx];
                }
            }
        }

        int pair1 = i;
        int pair2 = closestRef.id;
        if (pair2 < pair1) {
            pair1 = closestRef.id;
            pair2 = i;
        }

        vertexPairs.push_back(std::pair<int, int>(pair1, pair2));
        isPaired[closestRef.id] = true;
    }

    std::sort(vertexPairs.begin(), vertexPairs.end(), sortVertexPairByFirstIndex);
}

// matches vertex pairs between verts1 and verts2
// AABB bbox bounds verts1 and verts2
void TriangleMesh::_findDuplicateVertexPairs(std::vector<int> &verts1, 
                                             std::vector<int> &verts2, 
                                             AABB bbox,
                                             double tolerance, 
                                             std::vector<std::pair<int, int> > &vertexPairs) {

    double dx = 0.0625;
    int isize = (int)ceil(bbox.width / dx);
    int jsize = (int)ceil(bbox.height / dx);
    int ksize = (int)ceil(bbox.depth / dx);

    vmath::vec3 offset = bbox.position;
    std::vector<vmath::vec3> gridpoints;
    gridpoints.reserve(verts2.size());
    for (unsigned int i = 0; i < verts2.size(); i++) {
        gridpoints.push_back(vertices[verts2[i]] - offset);
    }

    SpatialPointGrid grid(isize, jsize, ksize, dx);
    grid.insert(gridpoints);

    double eps = tolerance;
    std::vector<GridPointReference> query;
    for (unsigned int i = 0; i < verts1.size(); i++) {

        vmath::vec3 v1 = vertices[verts1[i]] - offset;
        query.clear();
        grid.queryPointReferencesInsideSphere(v1, eps, query);

        if (query.size() == 0) {
            continue;
        }

        GridPointReference closestRef;
        if (query.size() == 1) {
            closestRef = query[0];
        } else {
            double mindist = std::numeric_limits<double>::infinity();

            for (unsigned int idx = 0; idx < query.size(); idx++) {
                vmath::vec3 v = vertices[i] - vertices[query[idx].id];
                double distsq = vmath::lengthsq(v);
                if (distsq < mindist) {
                    mindist = distsq;
                    closestRef = query[idx];
                }
            }
        }

        int pair1 = verts1[i];
        int pair2 = verts2[closestRef.id];

        vertexPairs.push_back(std::pair<int, int>(pair1, pair2));
    }
}

void TriangleMesh::removeDuplicateVertices(int i, int j, int k, double dx) {

    std::vector<std::pair<int, int> > vertexPairs;
    _findDuplicateVertexPairs(i, j, k, dx, vertexPairs);

    std::vector<int> indexTable;
    indexTable.reserve(vertices.size());
    for (unsigned int i = 0; i < vertices.size(); i++) {
        indexTable.push_back(i);
    }

    for (unsigned int i = 1; i < vertexPairs.size(); i++) {
        indexTable[vertexPairs[i].second] = vertexPairs[i].first;
    }

    Triangle t;
    for (unsigned int i = 0; i < triangles.size(); i++) {
        t = triangles[i];
        t.tri[0] = indexTable[t.tri[0]];
        t.tri[1] = indexTable[t.tri[1]];
        t.tri[2] = indexTable[t.tri[2]];

        if (t.tri[0] == t.tri[1] || t.tri[1] == t.tri[2] || t.tri[2] == t.tri[0]) {
            // Don't collapse triangles
            continue;
        }

        triangles[i] = t;
    }

    removeExtraneousVertices();
}