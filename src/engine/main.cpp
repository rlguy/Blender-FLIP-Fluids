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

#include <fstream>

#include "fluidsimulation.h"
#include "triangle.h"

void writeSurfaceMesh(int frameno, FluidSimulation &fluidsim) {
    std::ostringstream ss;
    ss << frameno;
    std::string frameString = ss.str();
    frameString.insert(frameString.begin(), 6 - frameString.size(), '0');
    std::string filepath = "C:/tmp/" + frameString + ".ply";

    std::vector<char> *data = fluidsim.getSurfaceData();
    std::ofstream ply(filepath.c_str(), std::ios::out | std::ios::binary);
    ply.write(data->data(), data->size());
    ply.close();
}

TriangleMesh getTriangleMeshFromAABB(AABB bbox) {
    vmath::vec3 p = bbox.position;
    std::vector<vmath::vec3> verts{
        vmath::vec3(p.x, p.y, p.z),
        vmath::vec3(p.x + bbox.width, p.y, p.z),
        vmath::vec3(p.x + bbox.width, p.y, p.z + bbox.depth),
        vmath::vec3(p.x, p.y, p.z + bbox.depth),
        vmath::vec3(p.x, p.y + bbox.height, p.z),
        vmath::vec3(p.x + bbox.width, p.y + bbox.height, p.z),
        vmath::vec3(p.x + bbox.width, p.y + bbox.height, p.z + bbox.depth),
        vmath::vec3(p.x, p.y + bbox.height, p.z + bbox.depth)
    };

    std::vector<Triangle> tris{
        Triangle(0, 1, 2), Triangle(0, 2, 3), Triangle(4, 7, 6), Triangle(4, 6, 5),
        Triangle(0, 3, 7), Triangle(0, 7, 4), Triangle(1, 5, 6), Triangle(1, 6, 2),
        Triangle(0, 4, 5), Triangle(0, 5, 1), Triangle(3, 2, 6), Triangle(3, 6, 7)
    };

    TriangleMesh m;
    m.vertices = verts;
    m.triangles = tris;

    return m;
}

int main() {

    // This example will drop a box of fluid in the center
    // of the fluid simulation domain.
    int isize = 64;
    int jsize = 64;
    int ksize = 64;
    double dx = 0.125;
    FluidSimulation fluidsim(isize, jsize, ksize, dx);
    
    fluidsim.setSurfaceSubdivisionLevel(2);
    
    double x, y, z;
    fluidsim.getSimulationDimensions(&x, &y, &z);

    double boxWidth = (1.0 / 3.0) * x;
    double boxHeight = (1.0 / 3.0) * y;
    double boxDepth = (1.0 / 3.0) * z;
    vmath::vec3 boxPosition(0.5 * (x - boxWidth), 0.5 * (y - boxHeight), 0.5 * (z - boxDepth));
    AABB box(boxPosition, boxWidth, boxHeight, boxDepth);
    TriangleMesh boxMesh = getTriangleMeshFromAABB(box);
    MeshObject boxFluidObject(isize, jsize, ksize, dx);
    boxFluidObject.updateMeshStatic(boxMesh);
    fluidsim.addMeshFluid(boxFluidObject);
    
    fluidsim.addBodyForce(0.0, -25.0, 0.0);
    fluidsim.initialize();
    double timestep = 1.0 / 30.0;
    for (;;) {
        int frameno = fluidsim.getCurrentFrame();
        fluidsim.update(timestep);
        writeSurfaceMesh(frameno, fluidsim);
    }
    
    return 0;
}