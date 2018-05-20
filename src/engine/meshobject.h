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

#ifndef FLUIDENGINE_MESHOBJECT_H
#define FLUIDENGINE_MESHOBJECT_H

#include <vector>

#include "meshlevelset.h"
#include "boundedbuffer.h"
#include "vmath.h"

class TriangleMesh;
struct GridIndex;

struct RigidBodyVelocity {
    vmath::vec3 linear;
    vmath::vec3 centroid;
    vmath::vec3 axis;
    double angular = 0.0;
};

struct MeshObjectStatus {
    bool isEnabled = false;
    bool isAnimated = false;
    bool isInversed = false;
    bool isStateChanged = false;
    bool isMeshChanged = false;
};

struct MeshIslandWorkItem {
    MeshIslandWorkItem() {}
    MeshIslandWorkItem(TriangleMesh m, std::vector<vmath::vec3> velocities) :
        mesh(m), vertexVelocities(velocities) {}

    TriangleMesh mesh;
    std::vector<vmath::vec3> vertexVelocities;
};

class MeshObject
{
public:
    MeshObject();
    MeshObject(int i, int j, int k, double dx, TriangleMesh mesh);
    MeshObject(int i, int j, int k, double dx, std::vector<TriangleMesh> meshes);
    MeshObject(int i, int j, int k, double dx, std::vector<TriangleMesh> meshes,
                                               std::vector<TriangleMesh> translations);
    ~MeshObject();
    
    void getGridDimensions(int *i, int *j, int *k);
    void setFrame(int f);
    void getCells(std::vector<GridIndex> &cells);
    void getCells(float frameInterpolation, 
                  std::vector<GridIndex> &cells);
    bool isAnimated();
    void clearObjectStatus();
    TriangleMesh getMesh();
    TriangleMesh getMesh(float frameInterpolation);
    TriangleMesh getFrameMesh(int frameno);
    std::vector<vmath::vec3> getVertexTranslations();
    std::vector<vmath::vec3> getVertexTranslations(float frameInterpolation);
    std::vector<vmath::vec3> getVertexVelocities(double dt);
    std::vector<vmath::vec3> getVertexVelocities(double dt, float frameInterpolation);
    std::vector<vmath::vec3> getFrameVertexVelocities(int frameno, double dt);
    void getMeshLevelSet(double dt, float frameInterpolation, int exactBand, 
                         MeshLevelSet &levelset);

    void enable();
    void disable();
    bool isEnabled();

    void inverse();
    bool isInversed();
    void setMeshExpansion(float exp);
    float getMeshExpansion();
    void setFriction(float f);
    float getFriction();

    void enableAppendObjectVelocity();
    void disableAppendObjectVelocity();
    bool isAppendObjectVelocityEnabled();
    RigidBodyVelocity getRigidBodyVelocity(double framedt);
    RigidBodyVelocity getRigidBodyVelocity(double framedt, int frameno);
    void setObjectVelocityInfluence(float value);
    float getObjectVelocityInfluence();

    MeshObjectStatus getStatus();

private:

    void _getInversedCells(float frameInterpolation, std::vector<GridIndex> &cells);
    void _getMeshIslands(TriangleMesh &m,
                         std::vector<vmath::vec3> &vertexVelocities,
                         MeshLevelSet &levelset, 
                         std::vector<TriangleMesh> &islands,
                         std::vector<std::vector<vmath::vec3> > &islandVertexVelocities);
    MeshLevelSet _getMeshIslandLevelSet(TriangleMesh &m, 
                                        std::vector<vmath::vec3> &velocities, 
                                        MeshLevelSet &domainLevelSet,
                                        int exactBand);
    void _expandMeshIslands(std::vector<TriangleMesh> &islands);
    void _expandMeshIsland(TriangleMesh &m);
    void _addMeshIslandsToLevelSet(std::vector<TriangleMesh> &islands,
                                   std::vector<std::vector<vmath::vec3> > &islandVertexVelocities,
                                   int exactBand,
                                   MeshLevelSet &levelset);
    void _addMeshIslandsToLevelSetFractureOptimization(
                                   std::vector<TriangleMesh> &islands,
                                   std::vector<std::vector<vmath::vec3> > &islandVertexVelocities,
                                   int exactBand,
                                   MeshLevelSet &levelset);
    void _islandMeshLevelSetProducerThread(BoundedBuffer<MeshIslandWorkItem> *workQueue,
                                           BoundedBuffer<MeshLevelSet*> *finishedWorkQueue,
                                           MeshLevelSet *domainLevelSet,
                                           int exactBand);
    bool _isMeshChanged();

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;
    std::vector<TriangleMesh> _meshes;

    int _currentFrame = 0;
    bool _isEnabled = true;
    bool _isInversed = false;
    float _meshExpansion = 0.0f;
    float _friction = 0.0f;
    bool _isAppendObjectVelocityEnabled = false;
    float _objectVelocityInfluence = 1.0f;
    bool _isObjectStateChanged = false;

    std::vector<std::vector<vmath::vec3> > _vertexTranslations;

    int _numIslandsForFractureOptimizationTrigger = 25;
    int _finishedWorkQueueSize = 10;
};

#endif
