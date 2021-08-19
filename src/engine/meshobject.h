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
    MeshObject(int i, int j, int k, double dx);
    ~MeshObject();
    
    void resizeGrid(int isize, int jsize, int ksize, double dx);

    void getGridDimensions(int *i, int *j, int *k);
    void updateMeshStatic(TriangleMesh meshCurrent);
    void updateMeshAnimated(TriangleMesh meshPrevious, 
                            TriangleMesh meshCurrent, 
                            TriangleMesh meshNext);
    void getCells(std::vector<GridIndex> &cells);
    void getCells(float frameInterpolation, 
                  std::vector<GridIndex> &cells);
    bool isAnimated();
    bool isRigidBody();
    void clearObjectStatus();
    TriangleMesh getMesh();
    TriangleMesh getMesh(float frameInterpolation);
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

    void setAsDomainObject();
    bool isDomainObject();


    void inverse();
    bool isInversed();
    void setFriction(float f);
    float getFriction();
    void setWhitewaterInfluence(float value);
    float getWhitewaterInfluence();
    void setDustEmissionStrength(float value);
    float getDustEmissionStrength();
    bool isDustEmissionEnabled();
    void setSheetingStrength(float value);
    float getSheetingStrength();
    void setMeshExpansion(float exp);
    float getMeshExpansion();

    void enableAppendObjectVelocity();
    void disableAppendObjectVelocity();
    bool isAppendObjectVelocityEnabled();
    RigidBodyVelocity getRigidBodyVelocity(double framedt);
    bool isGeometryAABB();
    void setObjectVelocityInfluence(float value);
    float getObjectVelocityInfluence();
    void setSourceID(int id);
    int getSourceID();
    void setSourceColor(vmath::vec3 c);
    vmath::vec3 getSourceColor();

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
                                        int exactBand,
                                        bool *success);
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

    void _sortTriangleIndices(Triangle &t);
    bool _isTriangleEqual(Triangle &t1, Triangle &t2);
    bool _isTopologyConsistent(TriangleMesh &m1, TriangleMesh &m2);
    bool _isRigidBody(TriangleMesh m1, TriangleMesh m2);

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    TriangleMesh _meshPrevious;
    TriangleMesh _meshCurrent;
    TriangleMesh _meshNext;
    std::vector<vmath::vec3> _vertexTranslationsCurrent;
    std::vector<vmath::vec3> _vertexTranslationsNext;

    /*
    std::vector<TriangleMesh> _meshes;
    std::vector<std::vector<vmath::vec3> > _vertexTranslations;
    int _currentFrame = 0;
    */

    bool _isEnabled = true;
    bool _isInversed = false;
    bool _isAnimated = false;
    bool _isChangingTopology = false;
    bool _isRigid = true;
    float _friction = 0.0f;
    float _whitewaterInfluence = 1.0f;
    float _dustEmissionStrength = 1.0f;
    float _sheetingStrength = 1.0f;
    float _meshExpansion = 0.0f;
    bool _isAppendObjectVelocityEnabled = false;
    float _objectVelocityInfluence = 1.0f;
    bool _isObjectStateChanged = false;
    bool _isDomainObject = false;
    int _sourceID = 0;
    vmath::vec3 _sourceColor;


    int _numIslandsForFractureOptimizationTrigger = 25;
    int _finishedWorkQueueSize = 10;
};

#endif
