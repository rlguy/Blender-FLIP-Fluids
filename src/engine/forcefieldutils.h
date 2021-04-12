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


#ifndef FLUIDENGINE_FORCEFIELDUTILS_H
#define FLUIDENGINE_FORCEFIELDUTILS_H

#include "meshlevelset.h"

namespace ForceFieldUtils {

struct VectorFieldGenerationData {
  Array3d<float> phi;
  Array3d<vmath::vec3> closestPoint;
  Array3d<bool> isClosestPointSet;
  double dx;
};

extern int _bandwidth;
extern float _sleepTimeFactor;

extern void generateSurfaceVectorField(MeshLevelSet &sdf, TriangleMesh &mesh, Array3d<vmath::vec3> &vectorField);
extern void _initializeNarrowBandClosestPoint(MeshLevelSet &sdf, TriangleMesh &mesh, 
                                              VectorFieldGenerationData &data);
extern void _initializeNarrowBandClosestPointThread(int startidx, int endidx, 
                                                    MeshLevelSet *sdf, TriangleMesh *mesh, 
                                                    VectorFieldGenerationData *data);
extern void _fastSweepingMethod(VectorFieldGenerationData &data);
extern void _sweepThread(VectorFieldGenerationData *data, Array3d<bool> *isFrozen, GridIndex sweepdir);
extern void _checkNeighbour(VectorFieldGenerationData *data, Array3d<bool> *isFrozen, 
                           vmath::vec3 gx, GridIndex g, int di, int dj, int dk);

}

#endif