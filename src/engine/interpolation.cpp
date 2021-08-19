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

#include "interpolation.h"

#include "grid3d.h"

/* 
    Cubic interpolation methods from http://www.paulinternet.nl/?page=bicubic

    - p is indexed in order by p[k][j][i]
    - x, y, z are in [0,1]
    - this function will interpolate the volume between point Index 1 and 2
*/
double Interpolation::tricubicInterpolate(double p[4][4][4], double x, double y, double z) {
    double arr[4];
    arr[0] = bicubicInterpolate(p[0], x, y);
    arr[1] = bicubicInterpolate(p[1], x, y);
    arr[2] = bicubicInterpolate(p[2], x, y);
    arr[3] = bicubicInterpolate(p[3], x, y);
    return cubicInterpolate(arr, z);
}

double Interpolation::bicubicInterpolate(double p[4][4], double x, double y) {
    double arr[4];
    arr[0] = cubicInterpolate(p[0], x);
    arr[1] = cubicInterpolate(p[1], x);
    arr[2] = cubicInterpolate(p[2], x);
    arr[3] = cubicInterpolate(p[3], x);
    return cubicInterpolate(arr, y);
}

double Interpolation::cubicInterpolate(double p[4], double x) {
    return p[1] + 0.5 * x*(p[2] - p[0] + x*(2.0*p[0] - 5.0*p[1] + 4.0*p[2] - p[3] + x*(3.0*(p[1] - p[2]) + p[3] - p[0])));
}

// vertices p are ordered {(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), 
//                         (1, 0, 1), (0, 1, 1), (1, 1, 0), (1, 1, 1)}
// x, y, z, in range [0,1]
double Interpolation::trilinearInterpolate(double p[8], double x, double y, double z) {
    return p[0] * (1 - x) * (1 - y) * (1 - z) +
           p[1] * x * (1 - y) * (1 - z) + 
           p[2] * (1 - x) * y * (1 - z) + 
           p[3] * (1 - x) * (1 - y) * z +
           p[4] * x * (1 - y) * z + 
           p[5] * (1 - x) * y * z + 
           p[6] * x * y * (1 - z) + 
           p[7] * x * y * z;
}

double Interpolation::trilinearInterpolate(vmath::vec3 p, double dx, Array3d<float> &grid) {

    GridIndex g = Grid3d::positionToGridIndex(p, dx);
    vmath::vec3 gpos = Grid3d::GridIndexToPosition(g, dx);

    double inv_dx = 1.0 / dx;
    double ix = (p.x - gpos.x)*inv_dx;
    double iy = (p.y - gpos.y)*inv_dx;
    double iz = (p.z - gpos.z)*inv_dx;

    double points[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    int isize = grid.width;
    int jsize = grid.height;
    int ksize = grid.depth;
    if (Grid3d::isGridIndexInRange(g.i,   g.j,   g.k, isize, jsize, ksize))   { 
        points[0] = grid(g.i,   g.j,   g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j,   g.k, isize, jsize, ksize))   { 
        points[1] = grid(g.i+1, g.j,   g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j+1, g.k, isize, jsize, ksize))   { 
        points[2] = grid(g.i,   g.j+1, g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j,   g.k+1, isize, jsize, ksize)) {
        points[3] = grid(g.i,   g.j,   g.k+1); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j,   g.k+1, isize, jsize, ksize)) { 
        points[4] = grid(g.i+1, g.j,   g.k+1); 
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j+1, g.k+1, isize, jsize, ksize)) { 
        points[5] = grid(g.i,   g.j+1, g.k+1); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j+1, g.k, isize, jsize, ksize))   { 
        points[6] = grid(g.i+1, g.j+1, g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j+1, g.k+1, isize, jsize, ksize)) { 
        points[7] = grid(g.i+1, g.j+1, g.k+1); 
    }

    return trilinearInterpolate(points, ix, iy, iz);
}

vmath::vec3 Interpolation::trilinearInterpolate(vmath::vec3 p, double dx, Array3d<vmath::vec3> &grid) {

    GridIndex g = Grid3d::positionToGridIndex(p, dx);
    vmath::vec3 gpos = Grid3d::GridIndexToPosition(g, dx);

    double inv_dx = 1.0 / dx;
    double ix = (p.x - gpos.x)*inv_dx;
    double iy = (p.y - gpos.y)*inv_dx;
    double iz = (p.z - gpos.z)*inv_dx;

    double pointsX[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    double pointsY[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    double pointsZ[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    int isize = grid.width;
    int jsize = grid.height;
    int ksize = grid.depth;
    if (Grid3d::isGridIndexInRange(g.i,   g.j,   g.k, isize, jsize, ksize))   { 
        vmath::vec3 point = grid(g.i,   g.j,   g.k);
        pointsX[0] = point.x;
        pointsY[0] = point.y;
        pointsZ[0] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j,   g.k, isize, jsize, ksize))   { 
        vmath::vec3 point = grid(g.i+1, g.j,   g.k); 
        pointsX[1] = point.x;
        pointsY[1] = point.y;
        pointsZ[1] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j+1, g.k, isize, jsize, ksize))   { 
        vmath::vec3 point = grid(g.i,   g.j+1, g.k); 
        pointsX[2] = point.x;
        pointsY[2] = point.y;
        pointsZ[2] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j,   g.k+1, isize, jsize, ksize)) {
        vmath::vec3 point = grid(g.i,   g.j,   g.k+1); 
        pointsX[3] = point.x;
        pointsY[3] = point.y;
        pointsZ[3] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j,   g.k+1, isize, jsize, ksize)) { 
        vmath::vec3 point = grid(g.i+1, g.j,   g.k+1); 
        pointsX[4] = point.x;
        pointsY[4] = point.y;
        pointsZ[4] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j+1, g.k+1, isize, jsize, ksize)) { 
        vmath::vec3 point = grid(g.i,   g.j+1, g.k+1); 
        pointsX[5] = point.x;
        pointsY[5] = point.y;
        pointsZ[5] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j+1, g.k, isize, jsize, ksize))   { 
        vmath::vec3 point = grid(g.i+1, g.j+1, g.k); 
        pointsX[6] = point.x;
        pointsY[6] = point.y;
        pointsZ[6] = point.z;
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j+1, g.k+1, isize, jsize, ksize)) { 
        vmath::vec3 point = grid(g.i+1, g.j+1, g.k+1); 
        pointsX[7] = point.x;
        pointsY[7] = point.y;
        pointsZ[7] = point.z;
    }

    vmath::vec3 result(trilinearInterpolate(pointsX, ix, iy, iz),
                       trilinearInterpolate(pointsY, ix, iy, iz),
                       trilinearInterpolate(pointsZ, ix, iy, iz));
    return result;
}

/* 
    Trilinear gradient interpolation methods adapted from:
    https://github.com/christopherbatty/VariationalViscosity3D/blob/master/array3_utils.h
*/
double Interpolation::bilinearInterpolate(
        double v00, double v10, double v01, double v11, double ix, double iy) { 
    double lerp1 = (1 - ix) * v00 + ix * v10;
    double lerp2 = (1 - ix) * v01 + ix * v11;

    return (1 - iy) * lerp1 + iy * lerp2;
}

void Interpolation::trilinearInterpolateGradient(
            vmath::vec3 p, double dx, Array3d<float> &grid, vmath::vec3 *grad) {

    GridIndex g = Grid3d::positionToGridIndex(p, dx);
    vmath::vec3 gpos = Grid3d::GridIndexToPosition(g, dx);

    double inv_dx = 1.0 / dx;
    double ix = (p.x - gpos.x)*inv_dx;
    double iy = (p.y - gpos.y)*inv_dx;
    double iz = (p.z - gpos.z)*inv_dx;
   
    int isize = grid.width;
    int jsize = grid.height;
    int ksize = grid.depth;

    float v000 = 0, v001 = 0, v010 = 0, v011 = 0, v100 = 0, v101 = 0, v110 = 0, v111 = 0;
    if (Grid3d::isGridIndexInRange(g.i,   g.j,   g.k, isize, jsize, ksize))   { 
        v000 = grid(g.i, g.j, g.k);
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j,   g.k, isize, jsize, ksize))   { 
        v100 = grid(g.i+1, g.j,   g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j+1, g.k, isize, jsize, ksize))   { 
        v010 = grid(g.i,   g.j+1, g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j,   g.k+1, isize, jsize, ksize)) {
        v001 = grid(g.i,   g.j,   g.k+1); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j,   g.k+1, isize, jsize, ksize)) { 
        v101 = grid(g.i+1, g.j,   g.k+1); 
    }
    if (Grid3d::isGridIndexInRange(g.i,   g.j+1, g.k+1, isize, jsize, ksize)) { 
        v011 = grid(g.i,   g.j+1, g.k+1); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j+1, g.k, isize, jsize, ksize))   { 
        v110 = grid(g.i+1, g.j+1, g.k); 
    }
    if (Grid3d::isGridIndexInRange(g.i+1, g.j+1, g.k+1, isize, jsize, ksize)) { 
        v111 = grid(g.i+1, g.j+1, g.k+1); 
    }

    float ddx00 = v100 - v000;
    float ddx10 = v110 - v010;
    float ddx01 = v101 - v001;
    float ddx11 = v111 - v011;
    float dv_dx = bilinearInterpolate(ddx00, ddx10, ddx01, ddx11, iy, iz);

    float ddy00 = v010 - v000;
    float ddy10 = v110 - v100;
    float ddy01 = v011 - v001;
    float ddy11 = v111 - v101;
    float dv_dy = bilinearInterpolate(ddy00, ddy10, ddy01, ddy11, ix, iz);

    float ddz00 = v001 - v000;
    float ddz10 = v101 - v100;
    float ddz01 = v011 - v010;
    float ddz11 = v111 - v110;
    float dv_dz = bilinearInterpolate(ddz00, ddz10, ddz01, ddz11, ix, iy);

    grad->x = dv_dx;
    grad->y = dv_dy;
    grad->z = dv_dz;
}