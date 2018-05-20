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

#ifndef FLUIDENGINE_DIFFUSEPARTICLESIMULATION_H
#define FLUIDENGINE_DIFFUSEPARTICLESIMULATION_H

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include "vmath.h"
#include "fragmentedvector.h"
#include "array3d.h"
#include "aabb.h"
#include "fluidmaterialgrid.h"
#include "turbulencefield.h"

struct MarkerParticle;
struct DiffuseParticle;
enum class DiffuseParticleType : char;
class MeshLevelSet;
class MACVelocityField;
class ParticleLevelSet;
class ParticleAdvector;

struct DiffuseParticleSimulationParameters {
    int isize;
    int jsize;
    int ksize;
    double dx;
    double deltaTime;
    double CFLConditionNumber;
    double markerParticleRadius;
    vmath::vec3 bodyForce;

    FragmentedVector<MarkerParticle> *markerParticles;
    MACVelocityField *vfield;
    ParticleLevelSet *liquidSDF;
    MeshLevelSet *solidSDF;
    MeshLevelSet *surfaceSDF;
    Array3d<float> *curvatureGrid;
};

enum class LimitBehaviour : char { 
    collide   = 0x00, 
    ballistic = 0x01, 
    kill = 0x02
};

class DiffuseParticleSimulation
{

public:
    DiffuseParticleSimulation();
    ~DiffuseParticleSimulation();

    void update(DiffuseParticleSimulationParameters params);

    void getDiffuseParticleTypeCounts(int *numfoam, 
                                    int *numbubble, 
                                    int *numspray);
    int getNumSprayParticles();
    int getNumBubbleParticles();
    int getNumFoamParticles();

    void enableDiffuseParticleEmission();
    void disableDiffuseParticleEmission();
    bool isDiffuseParticleEmissionEnabled();

    void enableFoam();
    void disableFoam();
    bool isFoamEnabled();

    void enableBubbles();
    void disableBubbles();
    bool isBubblesEnabled();

    void enableSpray();
    void disableSpray();
    bool isSprayEnabled();

    FragmentedVector<DiffuseParticle>* getDiffuseParticles();
    int getNumDiffuseParticles();
    void setDiffuseParticles(std::vector<DiffuseParticle> &particles);
    void setDiffuseParticles(FragmentedVector<DiffuseParticle> &particles);
    void addDiffuseParticles(std::vector<DiffuseParticle> &particles);
    void addDiffuseParticles(FragmentedVector<DiffuseParticle> &particles);

    double getEmitterGenerationRate();
    void setEmitterGenerationRate(double rate);

    double getMinEmitterEnergy();
    void setMinEmitterEnergy(double e);
    double getMaxEmitterEnergy();
    void setMaxEmitterEnergy(double e);

    double getMinWavecrestCurvature();
    void setMinWavecrestCurvature(double k);
    double getMaxWavecrestCurvature();
    void setMaxWavecrestCurvature(double k);

    double getMinTurbulence();
    void setMinTurbulence(double t);
    double getMaxTurbulence();
    void setMaxTurbulence(double t);

    int getMaxNumDiffuseParticles();
    void setMaxNumDiffuseParticles(int n);
    AABB getEmitterGenerationBounds();
    void setEmitterGenerationBounds(AABB bbox);

    double getMinDiffuseParticleLifetime();
    void setMinDiffuseParticleLifetime(double lifetime);
    double getMaxDiffuseParticleLifetime();
    void setMaxDiffuseParticleLifetime(double lifetime);
    double getDiffuseParticleLifetimeVariance();
    void setDiffuseParticleLifetimeVariance(double variance);
    double getFoamParticleLifetimeModifier();
    void setFoamParticleLifetimeModifier(double modifier);
    double getBubbleParticleLifetimeModifier();
    void setBubbleParticleLifetimeModifier(double modifier);
    double getSprayParticleLifetimeModifier();
    void setSprayParticleLifetimeModifier(double modifier);

    double getDiffuseParticleWavecrestEmissionRate();
    void setDiffuseParticleWavecrestEmissionRate(double r);
    double getDiffuseParticleTurbulenceEmissionRate();
    void setDiffuseParticleTurbulenceEmissionRate(double r);
    void getDiffuseParticleEmissionRates(double *rwc, double *rt);
    void setDiffuseParticleEmissionRates(double r);
    void setDiffuseParticleEmissionRates(double rwc, double rt);

    double getFoamAdvectionStrength();
    void setFoamAdvectionStrength(double s);
    double getFoamLayerDepth();
    void setFoamLayerDepth(double depth);
    double getFoamLayerOffset();
    void setFoamLayerOffset(double offset);

    void enablePreserveFoam();
    void disablePreserveFoam();
    bool isPreserveFoamEnabled();
    double getFoamPreservationRate();
    void setFoamPreservationRate(double rate);
    double getMinFoamDensity();
    void setMinFoamDensity(double d);
    double getMaxFoamDensity();
    void setMaxFoamDensity(double d);

    double getBubbleDragCoefficient();
    void setBubbleDragCoefficient(double d);
    double getBubbleBouyancyCoefficient();
    void setBubbleBouyancyCoefficient(double b);

    double getSprayDragCoefficient();
    void setSprayDragCoefficient(double d);

    LimitBehaviour getFoamLimitBehaviour();
    void setFoamLimitBehavour(LimitBehaviour b);

    LimitBehaviour getBubbleLimitBehaviour();
    void setBubbleLimitBehavour(LimitBehaviour b);

    LimitBehaviour getSprayLimitBehaviour();
    void setSprayLimitBehavour(LimitBehaviour b);

    std::vector<bool> getFoamActiveBoundarySides();
    void setFoamActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getBubbleActiveBoundarySides();
    void setBubbleActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getSprayActiveBoundarySides();
    void setSprayActiveBoundarySides(std::vector<bool> active);

    void setDomainOffset(vmath::vec3 offset);
    vmath::vec3 getDomainOffset();
    void setDomainScale(double scale);
    double getDomainScale();
    void getDiffuseParticleFileDataWWP(std::vector<char> &data);
    void getFoamParticleFileDataWWP(std::vector<char> &data);
    void getBubbleParticleFileDataWWP(std::vector<char> &data);
    void getSprayParticleFileDataWWP(std::vector<char> &data);

    void loadDiffuseParticles(FragmentedVector<DiffuseParticle> &particles);

private:

    struct DiffuseParticleEmitter {
        vmath::vec3 position;
        vmath::vec3 velocity;
        double energyPotential;
        double wavecrestPotential;
        double turbulencePotential;

        DiffuseParticleEmitter() : energyPotential(0.0),
                                   wavecrestPotential(0.0),
                                   turbulencePotential(0.0) {}

        DiffuseParticleEmitter(vmath::vec3 p, vmath::vec3 v, 
                               double e, double wc, double t) : 
                                   position(p),
                                   velocity(v),
                                   energyPotential(e),
                                   wavecrestPotential(wc),
                                   turbulencePotential(t) {}
    };    

    void _trilinearInterpolate(std::vector<vmath::vec3> &input, MACVelocityField *vfield, 
                               std::vector<vmath::vec3> &output);
    void _trilinearInterpolateThread(int startidx, int endidx, 
                                     std::vector<vmath::vec3> *input, MACVelocityField *vfield, 
                                     std::vector<vmath::vec3> *output);
    void _getDiffuseParticleEmitters(std::vector<DiffuseParticleEmitter> &emitters);
    void _sortMarkerParticlePositions(std::vector<vmath::vec3> &surface, 
                                      std::vector<vmath::vec3> &inside);
    double _getParticleJitter();
    vmath::vec3 _jitterParticlePosition(vmath::vec3 p, double jitter);
    void _initializeMaterialGrid();
    void _initializeMaterialGridThread(int startidx, int endidx);
    void _shrinkMaterialGridFluidThread(int startidx, int endidx, 
                                        FluidMaterialGrid *mgridtemp);
    void _getSurfaceDiffuseParticleEmitters(std::vector<vmath::vec3> &surface, 
                                            std::vector<DiffuseParticleEmitter> &emitters);
    double _getWavecrestPotential(vmath::vec3 p, vmath::vec3 v);
    double _getTurbulencePotential(vmath::vec3 p, TurbulenceField &tfield);
    double _getEnergyPotential(vmath::vec3 velocity);
    void _getInsideDiffuseParticleEmitters(std::vector<vmath::vec3> &inside, 
                                           std::vector<DiffuseParticleEmitter> &emitters);
    void _shuffleDiffuseParticleEmitters(std::vector<DiffuseParticleEmitter> &emitters);

    void _emitDiffuseParticles(std::vector<DiffuseParticleEmitter> &emitters, double dt);
    void _emitDiffuseParticles(DiffuseParticleEmitter &emitter, 
                               double dt,
                               std::vector<DiffuseParticle> &particles);
    int _getNumberOfEmissionParticles(DiffuseParticleEmitter &emitter,
                                      double dt);
    unsigned char _getDiffuseParticleID();
    void _computeNewDiffuseParticleVelocities(std::vector<DiffuseParticle> &particles);

    void _updateDiffuseParticleTypes();
    DiffuseParticleType _getDiffuseParticleType(DiffuseParticle &p, AABB &boundary);

    void _updateDiffuseParticleLifetimes(double dt);
    void _updateFoamPreservation(double dt);

    void _advanceDiffuseParticles(double dt);
    AABB _getBoundaryAABB();
    void _advanceSprayParticles(double dt);
    void _advanceBubbleParticles(double dt);
    void _advanceFoamParticles(double dt);
    vmath::vec3 _resolveCollision(vmath::vec3 oldp, vmath::vec3 newp, 
                                  DiffuseParticle &dp, AABB &boundary);
    LimitBehaviour _getLimitBehaviour(DiffuseParticle &dp);
    std::vector<bool>* _getActiveSides(DiffuseParticle &dp);
    int _getNearestSideIndex(vmath::vec3 p, AABB &boundary);
    void _markParticleForRemoval(unsigned int index);
    void _getDiffuseParticleTypeCounts(int *numfoam, 
                                      int *numbubble, 
                                      int *numspray);
    int _getNumSprayParticles();
    int _getNumBubbleParticles();
    int _getNumFoamParticles();

    void _removeDiffuseParticles();

    void _getDiffuseParticleFileDataWWP(std::vector<vmath::vec3> &positions, 
                                        std::vector<unsigned char> &ids,
                                        std::vector<char> &data);

    template<class T>
    void _removeItemsFromVector(FragmentedVector<T> &items, std::vector<bool> &isRemoved) {
        FLUIDSIM_ASSERT(items.size() == isRemoved.size());

        int currentidx = 0;
        for (unsigned int i = 0; i < items.size(); i++) {
            if (!isRemoved[i]) {
                items[currentidx] = items[i];
                currentidx++;
            }
        }

        int numRemoved = (int)items.size() - currentidx;
        for (int i = 0; i < numRemoved; i++) {
            items.pop_back();
        }
        items.shrink_to_fit();
    }

    inline double _randomDouble(double min, double max) {
        return min + (double)rand() / ((double)RAND_MAX / (max - min));
    }

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx;
    double _CFLConditionNumber = 5;
    double _markerParticleRadius = 0;
    vmath::vec3 _bodyForce;
    vmath::vec3 _domainOffset;
    double _domainScale = 1.0;

    bool _isDiffuseParticleEmissionEnabled = true;
    bool _isFoamEnabled = true;
    bool _isBubblesEnabled = true;
    bool _isSprayEnabled = true;
    double _diffuseSurfaceNarrowBandSize = 1.5;  // in number of grid cells
    double _solidBufferWidth = 0.25;             // in number of grid cells
    double _maxVelocityFactor = 1.1;
    double _wavecrestSharpness = 0.4;
    double _minWavecrestCurvature = 0.4;
    double _maxWavecrestCurvature = 1.0;
    double _minParticleEnergy = 0.1;
    double _maxParticleEnergy = 60.0;
    double _minTurbulence = 100.0;
    double _maxTurbulence = 200.0;
    double _emitterGenerationRate = 1.0;
    unsigned int _maxNumDiffuseParticles = 10e6;
    double _minDiffuseParticleLifetime = 0.0;
    double _maxDiffuseParticleLifetime = 7.0;
    double _lifetimeVariance = 3.0;
    double _wavecrestEmissionRate = 175;
    double _turbulenceEmissionRate = 175;
    double _foamLayerOffset = 0.0;                // in number of grid cells
    double _maxFoamToSurfaceDistance = 1.0;       // in number of grid cells
    double _foamBufferWidth = 1.0;                // in number of grid cells
    double _sprayParticleLifetimeModifier = 2.0;
    double _bubbleParticleLifetimeModifier = 0.333;
    double _foamParticleLifetimeModifier = 1.0;
    double _foamAdvectionStrength = 1.0;
    double _bubbleBouyancyCoefficient = 4.0;
    double _bubbleDragCoefficient = 1.0;
    double _sprayDragCoefficient = 0.0;
    double _maxDiffuseParticlesPerCell = 5000;
    double _emitterRadiusFactor = 8.0;            // in multiples of _markerParticleRadius
    double _particleJitterFactor = 1.0;

    bool _isPreserveFoamEnabled = false;
    double _foamPreservationRate = 0.75;
    double _minFoamDensity = 20;
    double _maxFoamDensity = 45;

    LimitBehaviour _foamLimitBehaviour = LimitBehaviour::collide;
    LimitBehaviour _bubbleLimitBehaviour = LimitBehaviour::collide;
    LimitBehaviour _sprayLimitBehaviour = LimitBehaviour::collide;
    std::vector<bool> _foamActiveSides;
    std::vector<bool> _bubbleActiveSides;
    std::vector<bool> _sprayActiveSides;
    AABB _emitterGenerationBounds;

    FragmentedVector<MarkerParticle> *_markerParticles;
    MACVelocityField *_vfield;
    ParticleLevelSet *_liquidSDF;
    MeshLevelSet *_solidSDF;
    MeshLevelSet *_surfaceSDF;
    Array3d<float> *_kgrid;

    FluidMaterialGrid _mgrid;
    Array3d<bool> _borderingAirGrid;
    Array3d<bool> _isBorderingAirGridSet;
    TurbulenceField _turbulenceField;
    FragmentedVector<DiffuseParticle> _diffuseParticles;

    int _currentDiffuseParticleID = 0;
    int _diffuseParticleIDLimit = 256;
};

#endif