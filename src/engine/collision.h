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

#ifndef FLUIDENGINE_COLLISION_H
#define FLUIDENGINE_COLLISION_H

#include "vmath.h"

class AABB;

namespace Collision {

    double _clamp(double v, double min, double max);

    // method adapted from:
    // http://www.lighthouse3d.com/tutorials/maths/ray-triangle-intersection/
    extern bool rayIntersectsTriangle(vmath::vec3 p, vmath::vec3 dir,
                                      vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2, 
                                      vmath::vec3 *collision, double *u, double *v);

    extern bool lineIntersectsTriangle(vmath::vec3 p, vmath::vec3 dir,
                                       vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2,
                                       vmath::vec3 *collision, double *u, double *v);

    extern bool rayIntersectsPlane(vmath::vec3 p0, vmath::vec3 dir,
                                   vmath::vec3 planePoint, vmath::vec3 planeNormal,
                                   vmath::vec3 *collision);

    extern bool lineIntersectsPlane(vmath::vec3 p0, vmath::vec3 dir,
                                    vmath::vec3 planePoint, vmath::vec3 planeNormal,
                                    vmath::vec3 *collision);


    // method adapted from:
    // http://www.geometrictools.com/Documentation/DistancePoint3Triangle3.pdf
    extern vmath::vec3 findClosestPointOnTriangle(vmath::vec3 p0, vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2);


    extern bool rayIntersectsTriangle(vmath::vec3 p, vmath::vec3 dir,
                                             vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2);

    extern bool rayIntersectsTriangle(vmath::vec3 p, vmath::vec3 dir,
                                             vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2, vmath::vec3 *collision);

    extern bool lineIntersectsTriangle(vmath::vec3 p, vmath::vec3 dir,
                                              vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2);

    extern bool lineIntersectsTriangle(vmath::vec3 p, vmath::vec3 dir,
                                              vmath::vec3 v0, vmath::vec3 v1, vmath::vec3 v2, vmath::vec3 *collision);

    extern bool rayIntersectsPlane(vmath::vec3 p0, vmath::vec3 dir,
                                   vmath::vec3 planePoint, vmath::vec3 planeNormal);

    extern bool lineIntersectsPlane(vmath::vec3 p0, vmath::vec3 dir,
                                    vmath::vec3 planePoint, vmath::vec3 planeNormal);
   
    extern vmath::vec3 getTriangleCentroid(vmath::vec3 p0, vmath::vec3 p1, vmath::vec3 p2);
    extern vmath::vec3 getTriangleNormal(vmath::vec3 p0, vmath::vec3 p1, vmath::vec3 p2);

    extern bool rayIntersectsAABB(vmath::vec3 p0, vmath::vec3 dir,
                                  AABB &bbox, vmath::vec3 *collision);

    extern bool sphereIntersectsAABB(vmath::vec3 p, double r, AABB bbox);
}

#endif
