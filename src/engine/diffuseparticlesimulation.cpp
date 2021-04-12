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

#include "diffuseparticlesimulation.h"

#include <cstring>

#include "threadutils.h"
#include "interpolation.h"
#include "markerparticle.h"
#include "meshlevelset.h"
#include "particlelevelset.h"
#include "meshobject.h"
#include "forcefieldgrid.h"

DiffuseParticleSimulation::DiffuseParticleSimulation() {
    double inf = std::numeric_limits<float>::infinity();
    _emitterGenerationBounds = AABB(-inf, -inf, -inf, inf, inf, inf);

    _diffuseParticles.addAttributeVector3("POSITION");
    _diffuseParticles.addAttributeVector3("VELOCITY");
    _diffuseParticles.addAttributeFloat("LIFETIME");
    _diffuseParticles.addAttributeChar("TYPE");
    _diffuseParticles.addAttributeUChar("ID");
}

DiffuseParticleSimulation::~DiffuseParticleSimulation() {
}

void DiffuseParticleSimulation::update(DiffuseParticleSimulationParameters params) {
    _isize = params.isize;
    _jsize = params.jsize;
    _ksize = params.ksize;
    _dx = params.dx;
    _markerParticleRadius = params.markerParticleRadius;
    _CFLConditionNumber = params.CFLConditionNumber;
    _bodyForce = params.bodyForce;

    _markerParticles = params.markerParticles;
    _vfield = params.vfield;
    _liquidSDF = params.liquidSDF;
    _solidSDF = params.solidSDF;
    _surfaceSDF = params.surfaceSDF;
    _meshingVolumeSDF = params.meshingVolumeSDF;
    _isMeshingVolumeSet = params.isMeshingVolumeSet;
    _kgrid = params.curvatureGrid;
    _influenceGrid = params.influenceGrid;
    _nearSolidGrid = params.nearSolidGrid;
    _nearSolidGridCellSize = params.nearSolidGridCellSize;
    _forceFieldGrid = params.forceFieldGrid;
    _isForceFieldGridSet = params.isForceFieldGridSet;


    bool isParticlesEnabled = _isFoamEnabled || _isBubblesEnabled || _isSprayEnabled || _isDustEnabled;
    bool emitParticles = _isDiffuseParticleEmissionEnabled && 
                         _diffuseParticles.size() < _maxNumDiffuseParticles &&
                         !_markerParticles->empty() &&
                         isParticlesEnabled;

    _initializeMaterialGrid();

    if (emitParticles) {
        std::vector<DiffuseParticleEmitter> normalEmitters;
        std::vector<DiffuseParticleEmitter> dustEmitters;
        _getDiffuseParticleEmitters(normalEmitters, dustEmitters);
        _emitNormalDiffuseParticles(normalEmitters, params.deltaTime);
        _emitDustDiffuseParticles(dustEmitters, params.deltaTime);
    }

    if (_diffuseParticles.size() == 0.0) {
        return;
    }

    _advanceDiffuseParticles(params.deltaTime);
    _updateDiffuseParticleTypes();
    _updateDiffuseParticleLifetimes(params.deltaTime);
    _removeDiffuseParticles();
}

void DiffuseParticleSimulation::
        getDiffuseParticleTypeCounts(int *numfoam, int *numbubble, int *numspray, int *numdust) {
    _getDiffuseParticleTypeCounts(numfoam, numbubble, numspray, numdust);
}

int DiffuseParticleSimulation::getNumSprayParticles() {
    return _getNumSprayParticles();
}

int DiffuseParticleSimulation::getNumBubbleParticles() {
    return _getNumBubbleParticles();
}

int DiffuseParticleSimulation::getNumFoamParticles() {
    return _getNumFoamParticles();
}

int DiffuseParticleSimulation::getNumDustParticles() {
    return _getNumDustParticles();
}

void DiffuseParticleSimulation::enableDiffuseParticleEmission() {
    _isDiffuseParticleEmissionEnabled = true;
}

void DiffuseParticleSimulation::disableDiffuseParticleEmission() {
    _isDiffuseParticleEmissionEnabled = false;
}

bool DiffuseParticleSimulation::isDiffuseParticleEmissionEnabled() {
    return _isDiffuseParticleEmissionEnabled;
}

void DiffuseParticleSimulation::enableFoam() {
    _isFoamEnabled = true;
}

void DiffuseParticleSimulation::disableFoam() {
    _isFoamEnabled = false;
}

bool DiffuseParticleSimulation::isFoamEnabled() {
    return _isFoamEnabled;
}

void DiffuseParticleSimulation::enableBubbles() {
    _isBubblesEnabled = true;
}

void DiffuseParticleSimulation::disableBubbles() {
    _isBubblesEnabled = false;
}

bool DiffuseParticleSimulation::isBubblesEnabled() {
    return _isBubblesEnabled;
}

void DiffuseParticleSimulation::enableSpray() {
    _isSprayEnabled = true;
}

void DiffuseParticleSimulation::disableSpray() {
    _isSprayEnabled = false;
}

bool DiffuseParticleSimulation::isSprayEnabled() {
    return _isSprayEnabled;
}

void DiffuseParticleSimulation::enableDust() {
    _isDustEnabled = true;
}

void DiffuseParticleSimulation::disableDust() {
    _isDustEnabled = false;
}

bool DiffuseParticleSimulation::isDustEnabled() {
    return _isDustEnabled;
}

void DiffuseParticleSimulation::enableBoundaryDustEmission() {
    _isBoundaryDustEmissionEnabled = true;
}

void DiffuseParticleSimulation::disableBoundaryDustEmission() {
    _isBoundaryDustEmissionEnabled = false;
}

bool DiffuseParticleSimulation::isBoundaryDustEmissionEnabled() {
    return _isBoundaryDustEmissionEnabled;
}

ParticleSystem* DiffuseParticleSimulation::getDiffuseParticles() {
    return &_diffuseParticles;
}

int DiffuseParticleSimulation::getNumDiffuseParticles() {
    return _diffuseParticles.size();
}

int DiffuseParticleSimulation::getMaxNumDiffuseParticles() {
    return _maxNumDiffuseParticles;
}

void DiffuseParticleSimulation::setMaxNumDiffuseParticles(int n) {
    FLUIDSIM_ASSERT(n >= 0);
    _maxNumDiffuseParticles = n;
}

AABB DiffuseParticleSimulation::getEmitterGenerationBounds() {
    return _emitterGenerationBounds;
}

void DiffuseParticleSimulation::setEmitterGenerationBounds(AABB bbox) {
    _emitterGenerationBounds = bbox;
}

double DiffuseParticleSimulation::getEmitterGenerationRate() {
    return _emitterGenerationRate;
}

void DiffuseParticleSimulation::setEmitterGenerationRate(double rate) {
    rate = fmin(rate, 1.0);
    rate = fmax(rate, 0.0);
    _emitterGenerationRate = rate;
}

double DiffuseParticleSimulation::getMinEmitterEnergy() {
    return _minParticleEnergy;
}

void DiffuseParticleSimulation::setMinEmitterEnergy(double e) {
    e = fmax(e, 0.0);
    _minParticleEnergy = e;
}

double DiffuseParticleSimulation::getMaxEmitterEnergy() {
    return _maxParticleEnergy;
}

void DiffuseParticleSimulation::setMaxEmitterEnergy(double e) {
    _maxParticleEnergy = e;
}

double DiffuseParticleSimulation::getMinWavecrestCurvature() {
    return _minWavecrestCurvature;
}

void DiffuseParticleSimulation::setMinWavecrestCurvature(double k) {
    _minWavecrestCurvature = k;
}

double DiffuseParticleSimulation::getMaxWavecrestCurvature() {
    return _maxWavecrestCurvature;
}

void DiffuseParticleSimulation::setMaxWavecrestCurvature(double k) {
    _maxWavecrestCurvature = k;
}

double DiffuseParticleSimulation::getMinTurbulence() {
    return _minTurbulence;
}

void DiffuseParticleSimulation::setMinTurbulence(double t) {
    _minTurbulence = t;
}

double DiffuseParticleSimulation::getMaxTurbulence() {
    return _maxTurbulence;
}

void DiffuseParticleSimulation::setMaxTurbulence(double t) {
    _maxTurbulence = t;
}

double DiffuseParticleSimulation::getMinDiffuseParticleLifetime() {
    return _minDiffuseParticleLifetime;
}

void DiffuseParticleSimulation::setMinDiffuseParticleLifetime(double lifetime) {
    FLUIDSIM_ASSERT(lifetime >= 0);
    _minDiffuseParticleLifetime = lifetime;
}

double DiffuseParticleSimulation::getMaxDiffuseParticleLifetime() {
    return _maxDiffuseParticleLifetime;
}

void DiffuseParticleSimulation::setMaxDiffuseParticleLifetime(double lifetime) {
    FLUIDSIM_ASSERT(lifetime >= 0);
    _maxDiffuseParticleLifetime = lifetime;
}

double DiffuseParticleSimulation::getDiffuseParticleLifetimeVariance() {
    return _lifetimeVariance;
}

void DiffuseParticleSimulation::setDiffuseParticleLifetimeVariance(double variance) {
    FLUIDSIM_ASSERT(variance >= 0);
    _lifetimeVariance = variance;
}

double DiffuseParticleSimulation::getFoamParticleLifetimeModifier() {
    return _foamParticleLifetimeModifier;
}

void DiffuseParticleSimulation::setFoamParticleLifetimeModifier(double modifier) {
    _foamParticleLifetimeModifier = modifier;
}

double DiffuseParticleSimulation::getBubbleParticleLifetimeModifier() {
    return _bubbleParticleLifetimeModifier;
}

void DiffuseParticleSimulation::setBubbleParticleLifetimeModifier(double modifier) {
    _bubbleParticleLifetimeModifier = modifier;
}

double DiffuseParticleSimulation::getSprayParticleLifetimeModifier() {
    return _sprayParticleLifetimeModifier;
}

void DiffuseParticleSimulation::setSprayParticleLifetimeModifier(double modifier) {
    _sprayParticleLifetimeModifier = modifier;
}

double DiffuseParticleSimulation::getDustParticleLifetimeModifier() {
    return _dustParticleLifetimeModifier;
}

void DiffuseParticleSimulation::setDustParticleLifetimeModifier(double modifier) {
    _dustParticleLifetimeModifier = modifier;
}

double DiffuseParticleSimulation::getDiffuseParticleWavecrestEmissionRate() {
    return _wavecrestEmissionRate;
}

void DiffuseParticleSimulation::setDiffuseParticleWavecrestEmissionRate(double r) {
    FLUIDSIM_ASSERT(r >= 0);
    _wavecrestEmissionRate = r;
}

double DiffuseParticleSimulation::getDiffuseParticleTurbulenceEmissionRate() {
    return _turbulenceEmissionRate;
}

void DiffuseParticleSimulation::setDiffuseParticleTurbulenceEmissionRate(double r) {
    FLUIDSIM_ASSERT(r >= 0);
    _turbulenceEmissionRate = r;
}

double DiffuseParticleSimulation::getDiffuseParticleDustEmissionRate() {
    return _dustEmissionRate;
}

void DiffuseParticleSimulation::setDiffuseParticleDustEmissionRate(double r) {
    FLUIDSIM_ASSERT(r >= 0);
    _dustEmissionRate = r;
}

double DiffuseParticleSimulation::getFoamAdvectionStrength() {
    return _foamAdvectionStrength;
}

void DiffuseParticleSimulation::setFoamAdvectionStrength(double s) {
    s = fmax(s, 0.0);
    s = fmin(s, 1.0);
    _foamAdvectionStrength = s;
}


double DiffuseParticleSimulation::getFoamLayerDepth() {
    return _maxFoamToSurfaceDistance;
}

void DiffuseParticleSimulation::setFoamLayerDepth(double depth) {
    depth = fmax(depth, 0.0);
    depth = fmin(depth, 1.0);
    _maxFoamToSurfaceDistance = depth;
}

double DiffuseParticleSimulation::getFoamLayerOffset() {
    return _foamLayerOffset;
}

void DiffuseParticleSimulation::setFoamLayerOffset(double offset) {
    offset = fmax(offset, -1.0);
    offset = fmin(offset, 1.0);
    _foamLayerOffset = offset;
}

void DiffuseParticleSimulation::enablePreserveFoam() {
    _isPreserveFoamEnabled = true;
}

void DiffuseParticleSimulation::disablePreserveFoam() {
    _isPreserveFoamEnabled = false;
}

bool DiffuseParticleSimulation::isPreserveFoamEnabled() {
    return _isPreserveFoamEnabled;
}

double DiffuseParticleSimulation::getFoamPreservationRate() {
    return _foamPreservationRate;
}

void DiffuseParticleSimulation::setFoamPreservationRate(double rate) {
    _foamPreservationRate = rate;
}

double DiffuseParticleSimulation::getMinFoamDensity() {
    return _minFoamDensity;
}

void DiffuseParticleSimulation::setMinFoamDensity(double d) {
    _minFoamDensity = d;
}

double DiffuseParticleSimulation::getMaxFoamDensity() {
    return _maxFoamDensity;
}

void DiffuseParticleSimulation::setMaxFoamDensity(double d) {
    _maxFoamDensity = d;
}


double DiffuseParticleSimulation::getBubbleDragCoefficient() {
    return _bubbleDragCoefficient;
}

void DiffuseParticleSimulation::setBubbleDragCoefficient(double d) {
    d = fmax(d, 0.0);
    d = fmin(d, 1.0);
    _bubbleDragCoefficient = d;
}

double DiffuseParticleSimulation::getBubbleBouyancyCoefficient() {
    return _bubbleBouyancyCoefficient;
}

void DiffuseParticleSimulation::setBubbleBouyancyCoefficient(double b) {
    _bubbleBouyancyCoefficient = b;
}


double DiffuseParticleSimulation::getDustDragCoefficient() {
    return _dustDragCoefficient;
}

void DiffuseParticleSimulation::setDustDragCoefficient(double d) {
    d = fmax(d, 0.0);
    d = fmin(d, 1.0);
    _dustDragCoefficient = d;
}

double DiffuseParticleSimulation::getDustBouyancyCoefficient() {
    return _dustBouyancyCoefficient;
}

void DiffuseParticleSimulation::setDustBouyancyCoefficient(double b) {
    _dustBouyancyCoefficient = b;
}


double DiffuseParticleSimulation::getSprayDragCoefficient() {
    return _sprayDragCoefficient;
}

void DiffuseParticleSimulation::setSprayDragCoefficient(double d) {
    _sprayDragCoefficient = d;
}

double DiffuseParticleSimulation::getSprayEmissionSpeed() {
    return _sprayEmissionSpeedFactor;
}

void DiffuseParticleSimulation::setSprayEmissionSpeed(double d) {
    _sprayEmissionSpeedFactor = d;
}

LimitBehaviour DiffuseParticleSimulation::getFoamLimitBehaviour() {
    return _foamLimitBehaviour;
}

void DiffuseParticleSimulation::setFoamLimitBehavour(LimitBehaviour b) {
    _foamLimitBehaviour = b;
}

LimitBehaviour DiffuseParticleSimulation::getBubbleLimitBehaviour() {
    return _bubbleLimitBehaviour;
}

void DiffuseParticleSimulation::setBubbleLimitBehavour(LimitBehaviour b) {
    _bubbleLimitBehaviour = b;
}

LimitBehaviour DiffuseParticleSimulation::getSprayLimitBehaviour() {
    return _sprayLimitBehaviour;
}

void DiffuseParticleSimulation::setSprayLimitBehavour(LimitBehaviour b) {
    _sprayLimitBehaviour = b;
}

LimitBehaviour DiffuseParticleSimulation::getDustLimitBehaviour() {
    return _dustLimitBehaviour;
}

void DiffuseParticleSimulation::setDustLimitBehavour(LimitBehaviour b) {
    _dustLimitBehaviour = b;
}

std::vector<bool> DiffuseParticleSimulation::getFoamActiveBoundarySides() {
    return _foamActiveSides;
}

void DiffuseParticleSimulation::setFoamActiveBoundarySides(std::vector<bool> active) {
    FLUIDSIM_ASSERT(active.size() == 6);
    _foamActiveSides = active;
}

std::vector<bool> DiffuseParticleSimulation::getBubbleActiveBoundarySides() {
    return _bubbleActiveSides;
}

void DiffuseParticleSimulation::setBubbleActiveBoundarySides(std::vector<bool> active) {
    FLUIDSIM_ASSERT(active.size() == 6);
    _bubbleActiveSides = active;
}

std::vector<bool> DiffuseParticleSimulation::getSprayActiveBoundarySides() {
    return _sprayActiveSides;
}

void DiffuseParticleSimulation::setSprayActiveBoundarySides(std::vector<bool> active) {
    FLUIDSIM_ASSERT(active.size() == 6);
    _sprayActiveSides = active;
}

std::vector<bool> DiffuseParticleSimulation::getDustActiveBoundarySides() {
    return _dustActiveSides;
}

void DiffuseParticleSimulation::setDustActiveBoundarySides(std::vector<bool> active) {
    FLUIDSIM_ASSERT(active.size() == 6);
    _dustActiveSides = active;
}

void DiffuseParticleSimulation::setDomainOffset(vmath::vec3 offset) {
    _domainOffset = offset;
}

vmath::vec3 DiffuseParticleSimulation::getDomainOffset() {
    return _domainOffset;
}

void DiffuseParticleSimulation::setDomainScale(double scale) {
    _domainScale = scale;
}

double DiffuseParticleSimulation::getDomainScale() {
    return _domainScale;
}

void DiffuseParticleSimulation::getDiffuseParticleFileDataWWP(std::vector<char> &data) {
    std::vector<vmath::vec3> positions;
    std::vector<unsigned char> ids;
    positions.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < particlePositions->size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
            ids.push_back(particleIds->at(i));
        }
    } else {
        for (int i = 0; i < (int)_diffuseParticles.size(); i++) {
            positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
            ids.push_back(particleIds->at(i));
        }
    }

    _getDiffuseParticleFileDataWWP(positions, ids, data);
}

void DiffuseParticleSimulation::getFoamParticleFileDataWWP(std::vector<char> &data) {
    std::vector<vmath::vec3> positions;
    std::vector<unsigned char> ids;
    positions.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (int i = 0; i < (int)_diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::foam) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (int i = 0; i < (int)_diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::foam) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(positions, ids, data);
}

void DiffuseParticleSimulation::getBubbleParticleFileDataWWP(std::vector<char> &data) {
    std::vector<vmath::vec3> positions;
    std::vector<unsigned char> ids;
    positions.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::bubble) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::bubble) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(positions, ids, data);
}

void DiffuseParticleSimulation::getSprayParticleFileDataWWP(std::vector<char> &data) {
    std::vector<vmath::vec3> positions;
    std::vector<unsigned char> ids;
    positions.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::spray) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::spray) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(positions, ids, data);
}

void DiffuseParticleSimulation::getDustParticleFileDataWWP(std::vector<char> &data) {
    std::vector<vmath::vec3> positions;
    std::vector<unsigned char> ids;
    positions.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::dust) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::dust) {
                positions.push_back(particlePositions->at(i) * _domainScale + _domainOffset);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(positions, ids, data);
}

void DiffuseParticleSimulation::getFoamParticleBlurFileDataWWP(std::vector<char> &data, double dt) {
    std::vector<vmath::vec3> translations;
    std::vector<unsigned char> ids;
    translations.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::foam) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::foam) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(translations, ids, data);
}

void DiffuseParticleSimulation::getBubbleParticleBlurFileDataWWP(std::vector<char> &data, double dt) {
    std::vector<vmath::vec3> translations;
    std::vector<unsigned char> ids;
    translations.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::bubble) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::bubble) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(translations, ids, data);
}

void DiffuseParticleSimulation::getSprayParticleBlurFileDataWWP(std::vector<char> &data, double dt) {
    std::vector<vmath::vec3> translations;
    std::vector<unsigned char> ids;
    translations.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::spray) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::spray) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(translations, ids, data);
}

void DiffuseParticleSimulation::getDustParticleBlurFileDataWWP(std::vector<char> &data, double dt) {
    std::vector<vmath::vec3> translations;
    std::vector<unsigned char> ids;
    translations.reserve(_diffuseParticles.size());
    ids.reserve(_diffuseParticles.size());

    std::vector<vmath::vec3> *particlePositions;
    std::vector<unsigned char> *particleIds;
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("POSITION", particlePositions);
    _diffuseParticles.getAttributeValues("ID", particleIds);
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    if (_isMeshingVolumeSet) {
        std::vector<bool> isSolid;
        _meshingVolumeSDF->trilinearInterpolateSolidPoints(*particlePositions, isSolid);
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if (isSolid[i]) {
                continue;
            }
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::dust) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    } else {
        for (size_t i = 0; i < _diffuseParticles.size(); i++) {
            if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::dust) {
                vmath::vec3 p = particlePositions->at(i);
                vmath::vec3 t = _vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
                translations.push_back(t);
                ids.push_back(particleIds->at(i));
            }
        }
    }

    _getDiffuseParticleFileDataWWP(translations, ids, data);
}

void DiffuseParticleSimulation::loadDiffuseParticles(FragmentedVector<DiffuseParticle> &particles) {
    _diffuseParticles.reserve(_diffuseParticles.size() + particles.size());

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    for (size_t i = 0; i < particles.size(); i++) {
        DiffuseParticle dp = particles[i];
        vmath::vec3 p = (dp.position - _domainOffset) / _domainScale;

        atts.positions->push_back(p);
        atts.velocities->push_back(dp.velocity);
        atts.lifetimes->push_back(dp.lifetime);
        atts.types->push_back((char)dp.type);
        atts.ids->push_back(dp.id);
    }
}

void DiffuseParticleSimulation::
        _getDiffuseParticleEmitters(std::vector<DiffuseParticleEmitter> &normalEmitters,
                                    std::vector<DiffuseParticleEmitter> &dustEmitters) {

    _turbulenceField.calculateTurbulenceField(_vfield, *_liquidSDF);

    std::vector<vmath::vec3> surfaceParticles;
    std::vector<vmath::vec3> insideParticles;
    std::vector<vmath::vec3> allParticles;
    _sortMarkerParticlePositions(surfaceParticles, insideParticles);

    allParticles.reserve(surfaceParticles.size() + insideParticles.size());
    allParticles.insert(allParticles.end(), surfaceParticles.begin(), surfaceParticles.end());
    allParticles.insert(allParticles.end(), insideParticles.begin(), insideParticles.end());

    _getSurfaceDiffuseParticleEmitters(surfaceParticles, normalEmitters);
    _getInsideDiffuseParticleEmitters(insideParticles, normalEmitters);
    _getDiffuseDustParticleEmitters(allParticles, dustEmitters);
    _shuffleDiffuseParticleEmitters(normalEmitters);
    _shuffleDiffuseParticleEmitters(dustEmitters);
}

DiffuseParticleSimulation::DiffuseParticleAttributes DiffuseParticleSimulation::_getDiffuseParticleAttributes() {
    DiffuseParticleAttributes atts;
    _diffuseParticles.getAttributeValues("POSITION", atts.positions);
    _diffuseParticles.getAttributeValues("VELOCITY", atts.velocities);
    _diffuseParticles.getAttributeValues("LIFETIME", atts.lifetimes);
    _diffuseParticles.getAttributeValues("TYPE", atts.types);
    _diffuseParticles.getAttributeValues("ID", atts.ids);
    return atts;
}

void DiffuseParticleSimulation::_trilinearInterpolate(std::vector<vmath::vec3> &input, 
                                                      MACVelocityField *vfield, 
                                                      std::vector<vmath::vec3> &output) {
    FLUIDSIM_ASSERT(output.size() == input.size());

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, input.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, input.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_trilinearInterpolateThread, this,
                                 intervals[i], intervals[i + 1], &input, vfield, &output);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void DiffuseParticleSimulation::_trilinearInterpolateThread(int startidx, int endidx, 
                                                            std::vector<vmath::vec3> *input, 
                                                            MACVelocityField *vfield, 
                                                            std::vector<vmath::vec3> *output) {
    for (int i = startidx; i < endidx; i++) {
        (*output)[i] = vfield->evaluateVelocityAtPositionLinear(input->at(i));
    }
}

double DiffuseParticleSimulation::_getParticleJitter() {
    double eps = 1e-3;
    return 0.25 * (_particleJitterFactor - eps) * _dx;
}

vmath::vec3 DiffuseParticleSimulation::_jitterParticlePosition(vmath::vec3 p, 
                                                               double jitter) {
    p.x += _randomDouble(-jitter, jitter);
    p.y += _randomDouble(-jitter, jitter);
    p.z += _randomDouble(-jitter, jitter);

    return p;
}

void DiffuseParticleSimulation::
        _sortMarkerParticlePositions(std::vector<vmath::vec3> &surface, 
                                     std::vector<vmath::vec3> &inside) {

    std::vector<vmath::vec3> *positions;
    _markerParticles->getAttributeValues("POSITION", positions);

    double jitter = _getParticleJitter();
    float width = (float)(_diffuseSurfaceNarrowBandSize * _dx);
    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    for (size_t i = 0; i < positions->size(); i++) {
        vmath::vec3 p = positions->at(i);
        p = _jitterParticlePosition(p, jitter);
        if (!_emitterGenerationBounds.isPointInside(p)) {
            continue;
        }

        float signedDistance = Interpolation::trilinearInterpolate(p - hdx, _dx, *_surfaceSDF);
        if (fabs(signedDistance) < width) {

            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (!_isBorderingAirGridSet(g)) {
                _borderingAirGrid.set(g, _mgrid.isCellNeighbouringAir(g));
                _isBorderingAirGridSet.set(g, true);
            }

            if (_borderingAirGrid(g)) {
                surface.push_back(p);
            } else {
                inside.push_back(p);
            }

        } else {
            inside.push_back(p);
        }
    }
}

void DiffuseParticleSimulation::_initializeMaterialGrid() {

    if (_mgrid.width == _isize && _mgrid.height == _jsize && _mgrid.depth == _ksize) {
        _mgrid.fill(Material::air);
    } else {
        _mgrid = FluidMaterialGrid(_isize, _jsize, _ksize);
    }

    int gridsize = _mgrid.width * _mgrid.height * _mgrid.depth;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_initializeMaterialGridThread, this,
                                 intervals[i], intervals[i + 1]);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    FluidMaterialGrid mgridtemp = _mgrid;
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_shrinkMaterialGridFluidThread, this,
                                 intervals[i], intervals[i + 1], &mgridtemp);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    _mgrid = mgridtemp;

    if (_borderingAirGrid.width == _isize && 
            _borderingAirGrid.height == _jsize && 
            _borderingAirGrid.depth == _ksize) {
        _borderingAirGrid.fill(false);
        _isBorderingAirGridSet.fill(false);
    } else {
        _borderingAirGrid = Array3d<bool>(_isize, _jsize, _ksize, false);
        _isBorderingAirGridSet = Array3d<bool>(_isize, _jsize, _ksize, false);
    }
}

void DiffuseParticleSimulation::_initializeMaterialGridThread(int startidx, int endidx) {
    int isize = _mgrid.width;
    int jsize = _mgrid.height;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        if (_solidSDF->getDistanceAtCellCenter(g) < 0.0f) {
            _mgrid.setSolid(g);
        } else if (_liquidSDF->get(g) < 0.0f) {
            _mgrid.setFluid(g);
        }
    }
}

void DiffuseParticleSimulation::_shrinkMaterialGridFluidThread(int startidx, int endidx, 
                                                               FluidMaterialGrid *mgridtemp) {
    int isize = _mgrid.width;
    int jsize = _mgrid.height;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, isize, jsize);
        int i = g.i;
        int j = g.j;
        int k = g.k;

        if (_mgrid.isCellAir(i, j, k)) {
            if (_mgrid.isCellFluid(i - 1, j, k)) { mgridtemp->setAir(i - 1, j, k); }
            if (_mgrid.isCellFluid(i + 1, j, k)) { mgridtemp->setAir(i + 1, j, k); }
            if (_mgrid.isCellFluid(i, j - 1, k)) { mgridtemp->setAir(i, j - 1, k); }
            if (_mgrid.isCellFluid(i, j + 1, k)) { mgridtemp->setAir(i, j + 1, k); }
            if (_mgrid.isCellFluid(i, j, k - 1)) { mgridtemp->setAir(i, j, k - 1); }
            if (_mgrid.isCellFluid(i, j, k + 1)) { mgridtemp->setAir(i, j, k + 1); }
        }
    }
}

void DiffuseParticleSimulation::
        _getSurfaceDiffuseParticleEmitters(std::vector<vmath::vec3> &surface, 
                                           std::vector<DiffuseParticleEmitter> &emitters) {
    
    std::vector<vmath::vec3> velocities(surface.size());
    _trilinearInterpolate(surface, _vfield, velocities);

    int count1 = 0;
    int count2 = 0;

    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    double eps = 1e-6;
    for (size_t i = 0; i < surface.size(); i++) {
        vmath::vec3 p = surface[i];
        vmath::vec3 v = velocities[i];

        count1++;

        double dist = Interpolation::trilinearInterpolate(p - hdx, _dx, *_surfaceSDF);
        if (dist > -0.75 * _dx) {
            v *= _randomDouble(1.0f, _sprayEmissionSpeedFactor);
            count2++;
        }

        double Ie = _getEnergyPotential(v);
        if (Ie < eps) {
            continue;
        }

        double Iwc = _getWavecrestPotential(p, v);
        if (Iwc > 0.0 && _randomDouble(0.0, 1.0) < _emitterGenerationRate) {
            emitters.push_back(DiffuseParticleEmitter(p, v, Ie, Iwc, 0.0, 0.0));
        }
    }
}

double DiffuseParticleSimulation::
        _getWavecrestPotential(vmath::vec3 p, vmath::vec3 v) {

    float eps = 1e-6f;
    if (fabs(v.x) < eps && fabs(v.y) < eps && fabs(v.z) < eps) {
        return 0.0;
    }

    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    float k = Interpolation::trilinearInterpolate(p - hdx, _dx, *_kgrid) * _dx;
    if (k < _minWavecrestCurvature) {
        return 0.0;
    }
    k = fmin(k, _maxWavecrestCurvature);

    vmath::vec3 grad;
    Interpolation::trilinearInterpolateGradient(p - hdx, _dx, *_surfaceSDF, &grad);
    if (fabs(grad.x) < eps && fabs(grad.y) < eps && fabs(grad.z) < eps) {
        return 0.0;
    }

    vmath::vec3 normal = grad.normalize();
    vmath::vec3 vn = v.normalize();
    if (vmath::dot(vn, normal) < _wavecrestSharpness) {
        return 0.0;
    }

    return (k - _minWavecrestCurvature) / (_maxWavecrestCurvature - _minWavecrestCurvature);
}

double DiffuseParticleSimulation::_getTurbulencePotential(vmath::vec3 p, TurbulenceField &tfield) {

    double t = tfield.evaluateTurbulenceAtPosition(p);
    t = fmax(t, _minTurbulence);
    t = fmin(t, _maxTurbulence);

    return (t - _minTurbulence) / (_maxTurbulence - _minTurbulence);
}

double DiffuseParticleSimulation::_getDustTurbulencePotential(vmath::vec3 p, double emissionStrength, TurbulenceField &tfield) {

    double t = tfield.evaluateTurbulenceAtPosition(p);
    double mint = _minDustTurbulenceFactor * _minTurbulence;
    double maxt = _maxDustTurbulenceFactor * _maxTurbulence;
    t = fmax(t, mint);
    t = fmin(t, maxt);

    return emissionStrength * ((t - mint) / (maxt - mint));
}

double DiffuseParticleSimulation::
        _getEnergyPotential(vmath::vec3 velocity) {

    double e = 0.5*vmath::dot(velocity, velocity);
    e = fmax(e, _minParticleEnergy);
    e = fmin(e, _maxParticleEnergy);

    return (e - _minParticleEnergy) / (_maxParticleEnergy - _minParticleEnergy);
}

void DiffuseParticleSimulation::_getInsideDiffuseParticleEmitters(std::vector<vmath::vec3> &inside, 
                                                                  std::vector<DiffuseParticleEmitter> &emitters) {

    std::vector<vmath::vec3> velocities(inside.size());
    _trilinearInterpolate(inside, _vfield, velocities);

    vmath::vec3 p, v;
    double eps = 1e-6;
    for (unsigned int i = 0; i < inside.size(); i++) {
        p = inside[i];
        v = velocities[i];

        double Ie = _getEnergyPotential(v);
        if (Ie < eps) {
            continue;
        }

        double It = _getTurbulencePotential(p, _turbulenceField);
        if (It > 0.0 && _randomDouble(0.0, 1.0) < _emitterGenerationRate) {
            emitters.push_back(DiffuseParticleEmitter(p, v, Ie, 0.0, It, 0.0));
        }
    }
}

void DiffuseParticleSimulation::_getDiffuseDustParticleEmitters(std::vector<vmath::vec3> &particles, 
                                                                std::vector<DiffuseParticleEmitter> &dustEmitters) {
    if (!_isDustEnabled) {
        return;
    }

    std::vector<vmath::vec3> velocities(particles.size());
    _trilinearInterpolate(particles, _vfield, velocities);

    std::vector<float> sdfDistances;
    _solidSDF->trilinearInterpolatePoints(particles, sdfDistances);

    AABB boundary = _getBoundaryAABB();

    double eps = 1e-6;
    double maxDist = _maxDustEmitterToObstacleDistance * _dx;
    double maxFloorDist = (_maxDustEmitterToObstacleDistance + 0.5) * _dx;
    for (unsigned int i = 0; i < particles.size(); i++) {
        float dist = sdfDistances[i];
        if (dist < 0.0f || dist > maxDist) {
            continue;
        }

        vmath::vec3 p = particles[i];
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        MeshObject *obj = _solidSDF->getClosestMeshObject(g);
        if (obj == nullptr || !obj->isDustEmissionEnabled()) {
            continue;
        }

        if (obj->isDomainObject() && !_isBoundaryDustEmissionEnabled) {
            continue;
        }

        if (obj->isDomainObject() && p.z > maxFloorDist) {
            continue;
        }

        vmath::vec3 v = velocities[i];
        double Ie = _getEnergyPotential(v);
        if (Ie < eps) {
            continue;
        }

        double dustEmissionStrength = obj->getDustEmissionStrength();
        double Id = _getDustTurbulencePotential(p, dustEmissionStrength, _turbulenceField);
        if (Id > 0.0 && _randomDouble(0.0, 1.0) < _emitterGenerationRate) {
            dustEmitters.push_back(DiffuseParticleEmitter(p, v, Ie, 0.0, 0.0, Id));
        }
    }
}

void DiffuseParticleSimulation::
        _shuffleDiffuseParticleEmitters(std::vector<DiffuseParticleEmitter> &emitters) {

    DiffuseParticleEmitter em;
    for (int i = (int)emitters.size() - 2; i >= 0; i--) {
        int j = (rand() % (int)(i - 0 + 1));
        em = emitters[i];
        emitters[i] = emitters[j];
        emitters[j] = em;
    }
}

void DiffuseParticleSimulation::_addNewDiffuseParticles(std::vector<DiffuseParticle> &newDiffuseParticles) {
    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();
    for (size_t i = 0; i < newDiffuseParticles.size(); i++) {
        DiffuseParticle dp = newDiffuseParticles[i];
        atts.positions->push_back(dp.position);
        atts.velocities->push_back(dp.velocity);
        atts.lifetimes->push_back(dp.lifetime);
        atts.types->push_back((char)dp.type);
        atts.ids->push_back(dp.id);
    }

    _diffuseParticles.update();
}

void DiffuseParticleSimulation::_emitNormalDiffuseParticles(std::vector<DiffuseParticleEmitter> &emitters, double dt) {
    std::vector<DiffuseParticle> newdps;
    for (size_t i = 0; i < emitters.size(); i++) {
        if (_diffuseParticles.size() >= _maxNumDiffuseParticles) {
            return;
        }

        _emitDiffuseParticles(emitters[i], dt, newdps);
    }

    _computeNewDiffuseParticleVelocities(newdps);
    _addNewDiffuseParticles(newdps);
}

void DiffuseParticleSimulation::_emitDustDiffuseParticles(std::vector<DiffuseParticleEmitter> &emitters, double dt) {
    std::vector<DiffuseParticle> newdps;
    for (size_t i = 0; i < emitters.size(); i++) {
        if (_diffuseParticles.size() >= _maxNumDiffuseParticles) {
            return;
        }

        _emitDiffuseParticles(emitters[i], dt, newdps);
    }

    for (size_t i = 0; i < newdps.size(); i++) {
        newdps[i].type = DiffuseParticleType::dust;
    }

    _computeNewDiffuseParticleVelocities(newdps);
    _addNewDiffuseParticles(newdps);
}

void DiffuseParticleSimulation::_emitDiffuseParticles(DiffuseParticleEmitter &emitter, 
                                                      double dt,
                                                      std::vector<DiffuseParticle> &particles) {

    int n = _getNumberOfEmissionParticles(emitter, dt);
    if (_diffuseParticles.size() + n >= _maxNumDiffuseParticles) {
        n = _maxNumDiffuseParticles - _diffuseParticles.size();
    }

    if (n <= 0) {
        return;
    }

    float eps = 10e-4f;
    if (vmath::length(emitter.velocity) < eps) {
        return;
    }

    float emitterRadius = _emitterRadiusFactor * (float)_markerParticleRadius;
    vmath::vec3 axis = vmath::normalize(emitter.velocity);

    vmath::vec3 e1;
    if (fabs(axis.x) - 1.0 < eps && fabs(axis.y) < eps && fabs(axis.z) < eps) {
        e1 = vmath::normalize(vmath::cross(axis, vmath::vec3(0.0, 1.0, 0.0)));
    } else {
        e1 = vmath::normalize(vmath::cross(axis, vmath::vec3(1.0, 0.0, 0.0)));
    }
    vmath::vec3 e2 = vmath::normalize(vmath::cross(axis, e1));

    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    float solidBuffer = (float)(_solidBufferWidth * _dx);
    float minLife = (float)_minDiffuseParticleLifetime;
    float maxLife = (float)_maxDiffuseParticleLifetime;
    float variance = (float)_lifetimeVariance;
    float twopi = 6.28318f;
    vmath::vec3 p;
    vmath::vec3 v(0.0, 0.0, 0.0); // velocities will computed in bulk later
    GridIndex g;
    for (int i = 0; i < n; i++) {
        float Xr = (float)(rand()) / (float)RAND_MAX;
        float Xt = (float)(rand()) / (float)RAND_MAX;
        float Xh = (float)(rand()) / (float)RAND_MAX;

        float r = emitterRadius * sqrt(Xr);
        float theta = Xt * twopi;
        float h = Xh * vmath::length((float)dt * emitter.velocity);
        float sinval = sin(theta);
        float cosval = cos(theta);

        p = emitter.position + r * cosval * e1 + r * sinval * e2 + h * axis;
        g = Grid3d::positionToGridIndex(p, _dx);
        if (!Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize)) {
            continue;
        }

        if (_solidSDF->trilinearInterpolate(p) < solidBuffer) {
            continue;
        }

        float lifetime = minLife + emitter.energyPotential * (maxLife - minLife);
        lifetime += _randomDouble(-variance, variance);
        if (lifetime <= 0.0f) {
            continue;
        }

        DiffuseParticle dp(p, v, lifetime, _getDiffuseParticleID());
        dp.type = _getDiffuseParticleType(dp, boundary);
        particles.push_back(dp);

        if (particles.size() >= _maxNumDiffuseParticles) {
            return;
        }
    }
}

int DiffuseParticleSimulation::
        _getNumberOfEmissionParticles(DiffuseParticleEmitter &emitter,
                                      double dt) {

    GridIndex g = Grid3d::positionToGridIndex(emitter.position, _dx);
    double iscale = _influenceGrid->get(g);
    double wc = _wavecrestEmissionRate * emitter.wavecrestPotential;
    double t = _turbulenceEmissionRate * emitter.turbulencePotential;
    double d = _dustEmissionRate * emitter.dustPotential;
    double n = iscale * emitter.energyPotential * (wc + t + d) * dt;

    if (n < 0.0) {
        return 0;
    }

    return (int)(n + 0.5);
}

unsigned char DiffuseParticleSimulation::_getDiffuseParticleID() {
    int id = _currentDiffuseParticleID;
    _currentDiffuseParticleID = (_currentDiffuseParticleID + 1) % _diffuseParticleIDLimit;
    return (unsigned char)id;
}

void DiffuseParticleSimulation::_computeNewDiffuseParticleVelocities(std::vector<DiffuseParticle> &particles) {

    std::vector<vmath::vec3> data;
    data.reserve(particles.size());
    for (size_t i = 0; i < particles.size(); i++) {
        data.push_back(particles[i].position);
    }

    _trilinearInterpolate(data, _vfield, data);

    int count = 0;

    for (size_t i = 0; i < particles.size(); i++) {
        vmath::vec3 v = data[i];
        if (particles[i].type == DiffuseParticleType::spray) {
            v *= _randomDouble(1.0, _sprayEmissionSpeedFactor);
            count++;
        }

        particles[i].velocity = v;
    }
}

void DiffuseParticleSimulation::_updateDiffuseParticleTypes() {
    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();
    for (size_t i = 0; i < _diffuseParticles.size(); i++) {
        if ((DiffuseParticleType)atts.types->at(i) == DiffuseParticleType::dust) {
            continue;
        }

        DiffuseParticle dp = atts.getDiffuseParticle(i);
        DiffuseParticleType oldtype = dp.type;
        DiffuseParticleType newtype = _getDiffuseParticleType(dp, boundary);
        atts.types->at(i) = (char)newtype;

        if (oldtype == DiffuseParticleType::bubble && 
                (newtype == DiffuseParticleType::foam || newtype == DiffuseParticleType::spray)) {
            vmath::vec3 newv = _vfield->evaluateVelocityAtPositionLinear(dp.position);
            atts.velocities->at(i) = newv;
        }
    }
}

DiffuseParticleType DiffuseParticleSimulation::_getDiffuseParticleType(DiffuseParticle &dp, AABB &boundary) {

    if (!boundary.isPointInside(dp.position)) {
        return DiffuseParticleType::spray;
    }

    double foamDist = _maxFoamToSurfaceDistance * _dx;
    double foamOffset = _foamLayerOffset * _dx;
    vmath::vec3 hdx(0.5*_dx, 0.5*_dx, 0.5*_dx);
    double dist = Interpolation::trilinearInterpolate(dp.position - hdx, _dx, *_surfaceSDF);

    DiffuseParticleType oldtype = dp.type;
    DiffuseParticleType type;
    if (dist > -foamDist + foamOffset && dist < foamDist + foamOffset) {
        type = DiffuseParticleType::foam;
    } else if (dist < -foamDist + foamOffset) {
        type = DiffuseParticleType::bubble;
    } else {
        type = DiffuseParticleType::spray;
    }

    if (oldtype == DiffuseParticleType::foam && type == DiffuseParticleType::bubble) {
        // Buffer zone for transitioning from foam to bubble. Reduces particles from
        // flickering between foam and bubble types at the foam-bubble interface.
        double buffer = _foamBufferWidth * _dx;
        if (dist > -foamDist - buffer + foamOffset) {
            type = oldtype;
        }
    }

    if (type == DiffuseParticleType::foam || type == DiffuseParticleType::spray) {
        GridIndex g = Grid3d::positionToGridIndex(dp.position, _dx);
        if (!_isBorderingAirGridSet(g)) {
            _borderingAirGrid.set(g, _mgrid.isCellNeighbouringAir(g));
            _isBorderingAirGridSet.set(g, true);
        }
        
        if (!_borderingAirGrid(g)) {
            type = DiffuseParticleType::bubble;
        }
    }

    return type;
}

void DiffuseParticleSimulation::_updateDiffuseParticleLifetimes(double dt) {
    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();
    for (int i = 0; i < (int)_diffuseParticles.size(); i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);

        double modifier = 0.0;
        if ((DiffuseParticleType)dp.type == DiffuseParticleType::spray) {
            modifier = _sprayParticleLifetimeModifier;
        } else if ((DiffuseParticleType)dp.type == DiffuseParticleType::bubble) {
            modifier = _bubbleParticleLifetimeModifier;
        } else if ((DiffuseParticleType)dp.type == DiffuseParticleType::foam) {
            modifier = _foamParticleLifetimeModifier;
        } else if ((DiffuseParticleType)dp.type == DiffuseParticleType::dust) {
            modifier = _dustParticleLifetimeModifier;
        }

        atts.lifetimes->at(i) = dp.lifetime - (float)(modifier * dt);
    }

    _updateFoamPreservation(dt);
}

void DiffuseParticleSimulation::_updateFoamPreservation(double dt) {
    if (!_isPreserveFoamEnabled) {
        return;
    }

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    Array3d<int> densityGrid(_isize, _jsize, _ksize, 0);
    for (size_t i = 0; i < _diffuseParticles.size(); i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if (dp.type == DiffuseParticleType::foam) {
            GridIndex g = Grid3d::positionToGridIndex(dp.position, _dx);
            densityGrid.add(g, 1);
        }
    }

    double invdiff = 1.0 / fmax(_maxFoamDensity - _minFoamDensity, 1e-6);
    for (size_t i = 0; i < _diffuseParticles.size(); i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if (dp.type == DiffuseParticleType::foam) {
            GridIndex g = Grid3d::positionToGridIndex(dp.position, _dx);
            double d = ((double)densityGrid(g) - _minFoamDensity) * invdiff;
            d = fmax(d, 0.0);
            d = fmin(d, 1.0);
            atts.lifetimes->at(i) = dp.lifetime + _foamPreservationRate * d * dt;
        }
    }
}

void DiffuseParticleSimulation::_advanceDiffuseParticles(double dt) {
    _advanceSprayParticles(dt);
    _advanceBubbleParticles(dt);
    _advanceFoamParticles(dt);
    _advanceDustParticles(dt);
}

AABB DiffuseParticleSimulation::_getBoundaryAABB() {
    double eps = 1e-6;
    AABB domainAABB(0.0, 0.0, 0.0, _isize * _dx, _jsize * _dx, _ksize * _dx);
    domainAABB.expand(-3 * _dx - eps);
    return domainAABB;
}

void DiffuseParticleSimulation::_advanceSprayParticles(double dt) {

    int spraycount = _getNumSprayParticles();
    if (spraycount == 0) {
        return;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _diffuseParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _diffuseParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_advanceSprayParticlesThread, this,
                                 intervals[i], intervals[i + 1], dt);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void DiffuseParticleSimulation::_advanceBubbleParticles(double dt) {

    int bubblecount = _getNumBubbleParticles();
    if (bubblecount == 0) {
        return;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _diffuseParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _diffuseParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_advanceBubbleParticlesThread, this,
                                 intervals[i], intervals[i + 1], dt);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void DiffuseParticleSimulation::_advanceFoamParticles(double dt) {

    int foamcount = _getNumFoamParticles();
    if (foamcount == 0) {
        return;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _diffuseParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _diffuseParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_advanceFoamParticlesThread, this,
                                 intervals[i], intervals[i + 1], dt);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void DiffuseParticleSimulation::_advanceDustParticles(double dt) {

    int dustcount = _getNumDustParticles();
    if (dustcount == 0) {
        return;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _diffuseParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _diffuseParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&DiffuseParticleSimulation::_advanceDustParticlesThread, this,
                                 intervals[i], intervals[i + 1], dt);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void DiffuseParticleSimulation::_advanceSprayParticlesThread(int startidx, int endidx, double dt) {
    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    float deadParticleLifetime = -1e6;
    float invdt = 1.0f / (float)dt;
    for (int i = startidx; i < endidx; i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if (dp.type != DiffuseParticleType::spray) {
            continue;
        }

        double factor = (double)dp.id / (double)(_diffuseParticleIDLimit - 1);
        double mind = std::max(_sprayDragCoefficient - _sprayDragCoefficient * _sprayDragVarianceFactor, 0.0);
        double maxd = _sprayDragCoefficient + _sprayDragCoefficient * _sprayDragVarianceFactor;
        double dragCoefficient = mind + (1.0 - factor) * (maxd - mind);

        vmath::vec3 bodyForce = _getGravityVector(dp.position);
        vmath::vec3 dragvec = -dragCoefficient * dp.velocity * (float)dt;
        vmath::vec3 nextv = dp.velocity + bodyForce * (float)dt + dragvec;
        vmath::vec3 nextp = dp.position + nextv * (float)dt;
        nextp = _resolveCollision(dp.position, nextp, dp, boundary);

        float maxv  = (float)_maxVelocityFactor * vmath::length(nextv);
        if (vmath::length(nextp - dp.position) * invdt > maxv) {
            atts.lifetimes->at(i) = deadParticleLifetime;
        } 

        atts.positions->at(i) = nextp;
        atts.velocities->at(i) = nextv;
    }
}

void DiffuseParticleSimulation::_advanceBubbleParticlesThread(int startidx, int endidx, double dt) {
    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    float deadParticleLifetime = -1e6;
    float invdt = 1.0f / (float)dt;
    for (int i = startidx; i < endidx; i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if (dp.type != DiffuseParticleType::bubble) {
            continue;
        }

        vmath::vec3 bodyForce = _getGravityVector(dp.position);
        vmath::vec3 vmac = _vfield->evaluateVelocityAtPositionLinear(dp.position);
        vmath::vec3 vbub = dp.velocity;
        vmath::vec3 bouyancyVelocity = (float)-_bubbleBouyancyCoefficient * bodyForce;
        vmath::vec3 dragVelocity = (float)_bubbleDragCoefficient*(vmac - vbub) / (float)dt;

        vmath::vec3 nextv = dp.velocity + (float)dt*(bouyancyVelocity + dragVelocity);
        vmath::vec3 nextp = dp.position + nextv * (float)dt;
        nextp = _resolveCollision(dp.position, nextp, dp, boundary);

        float maxv  = (float)_maxVelocityFactor * vmath::length(nextv);
        if (vmath::length(nextp - dp.position) * invdt > maxv) {
            atts.lifetimes->at(i) = deadParticleLifetime;
        } 

        atts.positions->at(i) = nextp;
        atts.velocities->at(i) = nextv;
    }
}

void DiffuseParticleSimulation::_advanceFoamParticlesThread(int startidx, int endidx, double dt) {
    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    float deadParticleLifetime = -1e6;
    float invdt = 1.0f / (float)dt;
    for (int i = startidx; i < endidx; i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if (dp.type != DiffuseParticleType::foam) {
            continue;
        }

        vmath::vec3 vmac = _vfield->evaluateVelocityAtPositionLinear(dp.position);
        vmath::vec3 nextv = _foamAdvectionStrength * vmac;
        vmath::vec3 nextp = dp.position + nextv * (float)dt;
        nextp = _resolveCollision(dp.position, nextp, dp, boundary);

        float maxv  = (float)_maxVelocityFactor * vmath::length(nextv);
        if (vmath::length(nextp - dp.position) * invdt > maxv) {
            atts.lifetimes->at(i) = deadParticleLifetime;
        } 

        atts.positions->at(i) = nextp;
        atts.velocities->at(i) = nextv;
    }
}

void DiffuseParticleSimulation::_advanceDustParticlesThread(int startidx, int endidx, double dt) {
    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    float deadParticleLifetime = -1e6;
    float invdt = 1.0f / (float)dt;
    for (int i = startidx; i < endidx; i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if (dp.type != DiffuseParticleType::dust) {
            continue;
        }

        double factor = (double)dp.id / (double)(_diffuseParticleIDLimit - 1);
        double minb = _dustBouyancyCoefficient - _dustBouyancyCoefficient * _dustBouyancyVarianceFactor;
        double maxb = _dustBouyancyCoefficient + _dustBouyancyCoefficient * _dustBouyancyVarianceFactor;
        double buoyancyCoefficient = minb + factor * (maxb - minb);

        double mind = std::max(_dustDragCoefficient - _dustDragCoefficient * _dustDragVarianceFactor, 0.0);
        double maxd = std::min(_dustDragCoefficient + _dustDragCoefficient * _dustDragVarianceFactor, 1.0);
        double dragCoefficient = mind + (1.0 - factor) * (maxd - mind);

        vmath::vec3 bodyForce = _getGravityVector(dp.position);
        vmath::vec3 vmac = _vfield->evaluateVelocityAtPositionLinear(dp.position);
        vmath::vec3 vbub = dp.velocity;
        vmath::vec3 bouyancyVelocity = (float)-buoyancyCoefficient * bodyForce;
        vmath::vec3 dragVelocity = (float)dragCoefficient * (vmac - vbub) / (float)dt;

        vmath::vec3 nextv = dp.velocity + (float)dt * (bouyancyVelocity + dragVelocity);
        vmath::vec3 nextp = dp.position + nextv * (float)dt;
        nextp = _resolveCollision(dp.position, nextp, dp, boundary);

        float maxv  = (float)_maxVelocityFactor * vmath::length(nextv);
        if (vmath::length(nextp - dp.position) * invdt > maxv) {
            atts.lifetimes->at(i) = deadParticleLifetime;
        } 

        atts.positions->at(i) = nextp;
        atts.velocities->at(i) = nextv;
    }
}

vmath::vec3 DiffuseParticleSimulation::_resolveCollision(vmath::vec3 oldp, 
                                                         vmath::vec3 newp,
                                                         DiffuseParticle &dp,
                                                         AABB &boundary) {
    vmath::vec3 origp = newp;
    LimitBehaviour b = _getLimitBehaviour(dp);
    if (b == LimitBehaviour::ballistic || b == LimitBehaviour::kill) {
        if (boundary.isPointInside(oldp) && !boundary.isPointInside(newp)) {
            std::vector<bool> *active = _getActiveSides(dp);
            int sideidx = _getNearestSideIndex(newp, boundary);
            if (active->at(sideidx)) {
                return newp;
            }
        } else if (!boundary.isPointInside(newp)) {
            return newp;
        }
    }

    GridIndex oldg = Grid3d::positionToGridIndex(oldp, _nearSolidGridCellSize);
    GridIndex newg = Grid3d::positionToGridIndex(newp, _nearSolidGridCellSize);
    if (!_nearSolidGrid->isIndexInRange(oldg) || !_nearSolidGrid->isIndexInRange(newg)) {
        return newp;
    }

    if (_nearSolidGrid->isIndexInRange(newg) && (!_nearSolidGrid->get(oldg) && !_nearSolidGrid->get(newg))) {
        return newp;
    }

    float eps = 1e-6;
    float stepDistance = _diffuseParticleStepDistanceFactor * (float)_dx;
    float travelDistance = (newp - oldp).length();
    if (travelDistance < eps) {
        return newp;
    }

    int numSteps = (int)std::ceil(travelDistance / stepDistance);
    vmath::vec3 stepdir = (newp - oldp).normalize();

    vmath::vec3 lastPosition = oldp;
    vmath::vec3 currentPosition;
    bool foundCollision = false;
    float collisionPhi = 0.0f;
    for (int stepidx = 0; stepidx < numSteps; stepidx++) {
        if (stepidx == numSteps - 1) {
            currentPosition = newp;
        } else {
            currentPosition = oldp + (float)(stepidx + 1) * stepDistance * stepdir;
        }

        float phi = _solidSDF->trilinearInterpolate(currentPosition);
        if (phi < 0.0f || !boundary.isPointInside(currentPosition)) {
            collisionPhi = phi;
            foundCollision = true;
            break;
        }

        lastPosition = currentPosition;
    }

    if (!foundCollision) {
        return newp;
    }

    vmath::vec3 resolvedPosition;
    float maxResolvedDistance = _CFLConditionNumber * _dx;
    vmath::vec3 grad = _solidSDF->trilinearInterpolateGradient(currentPosition);
    if (vmath::length(grad) > eps) {
        grad = vmath::normalize(grad);
        resolvedPosition = currentPosition - (collisionPhi - _solidBufferWidth * _dx) * grad;
        float resolvedPhi = _solidSDF->trilinearInterpolate(resolvedPosition);
        float resolvedDistance = vmath::length(resolvedPosition - currentPosition);
        if (resolvedPhi < 0 || resolvedDistance > maxResolvedDistance) {
            resolvedPosition = lastPosition;
        }
    } else {
        resolvedPosition = lastPosition;
    }

    if (!boundary.isPointInside(resolvedPosition)) {
        vmath::vec3 origPosition = resolvedPosition;
        resolvedPosition = boundary.getNearestPointInsideAABB(resolvedPosition);
        float resolvedPhi = _solidSDF->trilinearInterpolate(resolvedPosition);
        float resolvedDistance = vmath::length(resolvedPosition - origPosition);
        if (resolvedPhi < 0.0f || resolvedDistance > maxResolvedDistance) {
            resolvedPosition = lastPosition;
        }
    }

    return resolvedPosition;
}

LimitBehaviour DiffuseParticleSimulation::_getLimitBehaviour(DiffuseParticle &dp) {
    if (dp.type == DiffuseParticleType::foam) {
        return _foamLimitBehaviour;
    } else if (dp.type == DiffuseParticleType::bubble) {
        return _bubbleLimitBehaviour;
    } else if (dp.type == DiffuseParticleType::spray) {
        return _sprayLimitBehaviour;
    } else if (dp.type == DiffuseParticleType::dust) {
        return _dustLimitBehaviour;
    }

    return _sprayLimitBehaviour;
}

std::vector<bool>* DiffuseParticleSimulation::_getActiveSides(DiffuseParticle &dp) {
    if (dp.type == DiffuseParticleType::foam) {
        return &_foamActiveSides;
    } else if (dp.type == DiffuseParticleType::bubble) {
        return &_bubbleActiveSides;
    } else if (dp.type == DiffuseParticleType::spray) {
        return &_sprayActiveSides;
    } else if (dp.type == DiffuseParticleType::dust) {
        return &_dustActiveSides;
    }

    return &_sprayActiveSides;
}

int DiffuseParticleSimulation::_getNearestSideIndex(vmath::vec3 p, AABB &boundary) {
    p = boundary.getNearestPointInsideAABB(p);

    float eps = 1e-6f;
    if (fabs(p.x - boundary.position.x) < eps) {
        return 0;
    }
    if (fabs(p.x - (boundary.position.x + boundary.width)) < eps) {
        return 1;
    }

    if (fabs(p.y - boundary.position.y) < eps) {
        return 2;
    }
    if (fabs(p.y - (boundary.position.y + boundary.height)) < eps) {
        return 3;
    }

    if (fabs(p.z - boundary.position.z) < eps) {
        return 4;
    }
    if (fabs(p.z - (boundary.position.z + boundary.depth)) < eps) {
        return 5;
    }

    return 0;
}

vmath::vec3 DiffuseParticleSimulation::_getGravityVector(vmath::vec3 pos) {
    if (_isForceFieldGridSet) {
        return _forceFieldGrid->evaluateForceAtPosition(pos);
    }

    return _bodyForce;
}

void DiffuseParticleSimulation::
        _getDiffuseParticleTypeCounts(int *numfoam, int *numbubble, int *numspray, int *numdust) {

    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    int foam = 0;
    int bubble = 0;
    int spray = 0;
    int dust = 0;
    for (size_t i = 0; i < particleTypes->size(); i++) {
        DiffuseParticleType type = (DiffuseParticleType)(particleTypes->at(i));
        if (type == DiffuseParticleType::foam) {
            foam++;
        } else if (type == DiffuseParticleType::bubble) {
            bubble++;
        } else if (type == DiffuseParticleType::spray) {
            spray++;
        }else if (type == DiffuseParticleType::dust) {
            dust++;
        }
    }

    *numfoam = foam;
    *numbubble = bubble;
    *numspray = spray;
    *numdust = dust;
}

int DiffuseParticleSimulation::_getNumSprayParticles() {
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    int spraycount = 0;
    for (unsigned int i = 0; i < particleTypes->size(); i++) {
        if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::spray) {
            spraycount++;
        }
    }

    return spraycount;
}

int DiffuseParticleSimulation::_getNumBubbleParticles() {
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    int bubblecount = 0;
    for (unsigned int i = 0; i < particleTypes->size(); i++) {
        if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::bubble) {
            bubblecount++;
        }
    }

    return bubblecount;
}

int DiffuseParticleSimulation::_getNumFoamParticles() {
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    int foamcount = 0;
    for (unsigned int i = 0; i < particleTypes->size(); i++) {
        if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::foam) {
            foamcount++;
        }
    }

    return foamcount;
}

int DiffuseParticleSimulation::_getNumDustParticles() {
    std::vector<char> *particleTypes;
    _diffuseParticles.getAttributeValues("TYPE", particleTypes);

    int dustcount = 0;
    for (unsigned int i = 0; i < particleTypes->size(); i++) {
        if ((DiffuseParticleType)particleTypes->at(i) == DiffuseParticleType::dust) {
            dustcount++;
        }
    }

    return dustcount;
}

void DiffuseParticleSimulation::_removeDiffuseParticles() {

    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);

    DiffuseParticleAttributes atts = _getDiffuseParticleAttributes();

    std::vector<bool> isInsideSolid;
    _solidSDF->trilinearInterpolateSolidPoints(*(atts.positions), isInsideSolid);

    Array3d<int> countGrid = Array3d<int>(_isize, _jsize, _ksize, 0);
    std::vector<bool> isRemoved(_diffuseParticles.size(), false);
    for (size_t i = 0; i < _diffuseParticles.size(); i++) {
        DiffuseParticle dp = atts.getDiffuseParticle(i);
        if ((!_isFoamEnabled && dp.type == DiffuseParticleType::foam) ||
                (!_isBubblesEnabled && dp.type == DiffuseParticleType::bubble) ||
                (!_isSprayEnabled && dp.type == DiffuseParticleType::spray) ||
                (!_isDustEnabled && dp.type == DiffuseParticleType::dust) ) {
            isRemoved[i] = true;
            continue;
        }

        if (dp.lifetime <= 0.0) {
            isRemoved[i] = true;
            continue;
        }

        bool isInBoundary = boundary.isPointInside(dp.position);
        if (_getLimitBehaviour(dp) == LimitBehaviour::kill && !isInBoundary) {
            isRemoved[i] = true;
            continue;
        }

        if (_getLimitBehaviour(dp) != LimitBehaviour::ballistic && !isInBoundary) {
            isRemoved[i] = true;
            continue;
        }

        if (isInBoundary && isInsideSolid[i]) {
            isRemoved[i] = true;
            continue;
        }

        GridIndex g = Grid3d::positionToGridIndex(dp.position, _dx);
        if (countGrid.isIndexInRange(g) && countGrid(g) >= _maxDiffuseParticlesPerCell) {
            isRemoved[i] = true;
            continue;
        }

        if (countGrid.isIndexInRange(g)) {
            countGrid.add(g, 1);
        }
    }

    _diffuseParticles.removeParticles(isRemoved);

    if (_diffuseParticles.size() >= _maxNumDiffuseParticles) {
        _diffuseParticles.resize(_maxNumDiffuseParticles);
    }
}

void DiffuseParticleSimulation::_getDiffuseParticleFileDataWWP(std::vector<vmath::vec3> &positions, 
                                                               std::vector<unsigned char> &ids,
                                                               std::vector<char> &data) {
    FLUIDSIM_ASSERT(positions.size() == ids.size())

    std::vector<int> idcounts(_diffuseParticleIDLimit, 0);
    for (size_t i = 0; i < ids.size(); i++) {
        idcounts[(int)ids[i]]++;
    }

    std::vector<int> idBinIndices(_diffuseParticleIDLimit, 0);
    std::vector<int> idData(_diffuseParticleIDLimit, 0);
    int currentBinIndex = 0;
    for (size_t i = 0; i < idcounts.size(); i++) {
        idBinIndices[i] = currentBinIndex;
        currentBinIndex += idcounts[i];
        idData[i] = currentBinIndex - 1;
    }

    std::vector<vmath::vec3> positionData(positions.size(), vmath::vec3());
    for (size_t i = 0; i < positions.size(); i++) {
        positionData[idBinIndices[ids[i]]] = positions[i];
        idBinIndices[ids[i]]++;
    }

    int idDataSize = (int)idData.size() * sizeof(int);
    int numVertices = (int)positions.size();
    int vertexDataSize = 3 * numVertices * sizeof(float);
    int dataSize = idDataSize + vertexDataSize;

    data.clear();
    data.resize(dataSize);
    data.shrink_to_fit();

    int byteOffset = 0;
    std::memcpy(data.data() + byteOffset, (char *)idData.data(), idDataSize);
    byteOffset += idDataSize;

    std::memcpy(data.data() + byteOffset, (char *)positionData.data(), vertexDataSize);
    byteOffset += vertexDataSize;
}