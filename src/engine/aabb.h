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

#ifndef FLUIDENGINE_AABB_H
#define FLUIDENGINE_AABB_H

#include <vector>

#include "vmath.h"

struct Triangle;
struct GridIndex;

class AABB
{
public:
    AABB();
    AABB(double x, double y, double z, double width, double height, double depth);
    AABB(vmath::vec3 p, double width, double height, double depth);
    AABB(vmath::vec3 p1, vmath::vec3 p2);
    AABB(std::vector<vmath::vec3> &points);
    AABB(Triangle t, std::vector<vmath::vec3> &vertices);
    AABB(GridIndex g, double dx);
    ~AABB();

    void expand(double v);
    bool isPointInside(vmath::vec3 p);
    bool isOverlappingTriangle(Triangle t, std::vector<vmath::vec3> &vertices);
    bool isLineIntersecting(vmath::vec3 p1, vmath::vec3 p2);
    AABB getIntersection(AABB bbox);
    AABB getUnion(AABB bbox);
    bool isIntersecting(AABB bbox, double eps = 1e-6);

    vmath::vec3 getMinPoint();
    vmath::vec3 getMaxPoint();
    vmath::vec3 getNearestPointInsideAABB(vmath::vec3 p, double eps);
    vmath::vec3 getNearestPointInsideAABB(vmath::vec3 p);
    float getSignedDistance(vmath::vec3 p);

    vmath::vec3 position;
    double width = 0.0;
    double height = 0.0;
    double depth = 0.0;

private:
    bool _axisTestX01(vmath::vec3 v0, vmath::vec3 v2,
        double a, double b, double fa, double fb);
    bool _axisTestX2(vmath::vec3 v0, vmath::vec3 v1,
        double a, double b, double fa, double fb);
    bool _axisTestY02(vmath::vec3 v0, vmath::vec3 v2,
        double a, double b, double fa, double fb);
    bool _axisTestY1(vmath::vec3 v0, vmath::vec3 v1,
        double a, double b, double fa, double fb);
    bool _axisTestZ12(vmath::vec3 v1, vmath::vec3 v2,
        double a, double b, double fa, double fb);
    bool _axisTestZ0(vmath::vec3 v0, vmath::vec3 v1,
        double a, double b, double fa, double fb);
    void _findminmax(double v0, double v1, double v2, double *min, double *max);
    bool _planeBoxOverlap(vmath::vec3 normal, vmath::vec3 vert);
};

#endif
