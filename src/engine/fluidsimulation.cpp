/*
MIT License

Copyright (c) 2019 Ryan L. Guy

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

#include "fluidsimulation.h"

#include <cstring>
#include <iomanip>

#include "threadutils.h"
#include "stopwatch.h"
#include "openclutils.h"
#include "viscositysolver.h"
#include "particlemesher.h"
#include "polygonizer3d.h"
#include "diffuseparticle.h"
#include "markerparticle.h"
#include "particlemaskgrid.h"
#include "triangle.h"
#include "scalarfield.h"
#include "particlesheeter.h"
#include "versionutils.h"
#include "interpolation.h"
#include "gridutils.h"

FluidSimulation::FluidSimulation() {
}

FluidSimulation::FluidSimulation(int isize, int jsize, int ksize, double dx) :
                                _isize(isize), _jsize(jsize), _ksize(ksize), _dx(dx) {
    _logGreeting();
}

FluidSimulation::~FluidSimulation() {
}

/*******************************************************************************
    PUBLIC
********************************************************************************/

void FluidSimulation::getVersion(int *major, int *minor, int *revision) { 
    VersionUtils::getVersion(major, minor, revision);
}

void FluidSimulation::initialize() {
    if (!_isSimulationInitialized) {
        _logfile.log(std::ostringstream().flush() << 
                     _logfile.getTime() << " initialize" << std::endl);
        _initializeSimulation();
    }
}

bool FluidSimulation::isInitialized() {
    return _isSimulationInitialized;
}

int FluidSimulation::getCurrentFrame() {
    return _currentFrame;
}

void FluidSimulation::setCurrentFrame(int frameno) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setCurrentFrame: " << frameno << std::endl);

    _currentFrame = frameno;
}

bool FluidSimulation::isCurrentFrameFinished() { 
    return _isCurrentFrameFinished; 
}

double FluidSimulation::getCellSize() { 
    return _dx; 
}

void FluidSimulation::getGridDimensions(int *i, int *j, int *k) { 
    *i = _isize; *j = _jsize; *k = _ksize; 
}

int FluidSimulation::getGridWidth() {
    return _isize;
}

int FluidSimulation::getGridHeight() {
    return _jsize;
}

int FluidSimulation::getGridDepth() {
    return _ksize;
}

void FluidSimulation::getSimulationDimensions(double *w, double *h, double *d) { 
    *w = (double)_isize*_dx;
    *h = (double)_jsize*_dx;
    *d = (double)_ksize*_dx;
}

double FluidSimulation::getSimulationWidth() {  
    return (double)_isize*_dx; 
}

double FluidSimulation::getSimulationHeight() { 
    return (double)_jsize*_dx; 
}

double FluidSimulation::getSimulationDepth() {  
    return (double)_ksize*_dx; 
}

double FluidSimulation::getDensity() { 
    return _density; 
}

void FluidSimulation::setDensity(double p) { 
    if (p <= 0.0) {
        std::string msg = "Error: density must be greater than 0.\n";
        msg += "density: " + _toString(p) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDensity: " << p << std::endl);

    _density = p; 
}

double FluidSimulation::getMarkerParticleScale() {
    return _markerParticleScale;
}

void FluidSimulation::setMarkerParticleScale(double s) { 
    if (s < 0.0) {
        std::string msg = "Error: marker particle scale must be greater than or equal to 0.\n";
        msg += "scale: " + _toString(s) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMarkerParticleScale: " << s << std::endl);

    _markerParticleScale = s; 
}

double FluidSimulation::getMarkerParticleJitterFactor() {
    return _markerParticleJitterFactor;
}

void FluidSimulation::setMarkerParticleJitterFactor(double jit) { 
    if (jit < 0.0) {
        std::string msg = "Error: marker particle jitter must be greater than or equal to 0.\n";
        msg += "jitter: " + _toString(jit) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMarkerParticleJitterFactor: " << jit << std::endl);

    _markerParticleJitterFactor = jit; 
}

void FluidSimulation::enableJitterSurfaceMarkerParticles() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableJitterSurfaceMarkerParticles" << std::endl);

    _isJitterSurfaceMarkerParticlesEnabled = true;
}

void FluidSimulation::disableJitterSurfaceMarkerParticles() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableJitterSurfaceMarkerParticles" << std::endl);

    _isJitterSurfaceMarkerParticlesEnabled = false;
}

bool FluidSimulation::isJitterSurfaceMarkerParticlesEnabled() {
    return _isJitterSurfaceMarkerParticlesEnabled;
}

int FluidSimulation::getSurfaceSubdivisionLevel() {
    return _outputFluidSurfaceSubdivisionLevel;
}

void FluidSimulation::setSurfaceSubdivisionLevel(int n) {
    if (n < 1) {
        std::string msg = "Error: subdivision level must be greater than or equal to 1.\n";
        msg += "subdivision level: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSurfaceSubdivisionLevel: " << n << std::endl);

    _outputFluidSurfaceSubdivisionLevel = n;
}

int FluidSimulation::getNumPolygonizerSlices() {
    return _numSurfaceReconstructionPolygonizerSlices;
}

void FluidSimulation::setNumPolygonizerSlices(int n) {
    if (n < 1) {
        std::string msg = "Error: number of polygonizer slices must be greater than or equal to 1.\n";
        msg += "polygonizer slices: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setNumPolygonizerSlices: " << n << std::endl);

    _numSurfaceReconstructionPolygonizerSlices = n;
}

double FluidSimulation::getSurfaceSmoothingValue() {
    return _surfaceReconstructionSmoothingValue;
}

void FluidSimulation::setSurfaceSmoothingValue(double s) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSurfaceSmoothingValue: " << s << std::endl);

    _surfaceReconstructionSmoothingValue = s;
}

int FluidSimulation::getSurfaceSmoothingIterations() {
    return _surfaceReconstructionSmoothingIterations;
}

void FluidSimulation::setSurfaceSmoothingIterations(int n) {
    if (n < 0) {
        std::string msg = "Error: number of smoothing iterations must be positive.\n";
        msg += "smoothing iterations: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSurfaceSmoothingIterations: " << n << std::endl);

    _surfaceReconstructionSmoothingIterations = n;
}

void FluidSimulation::setMeshingVolume(MeshObject *volumeObject) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMeshingVolume: " << volumeObject << std::endl);

    _meshingVolume = volumeObject;
    _isMeshingVolumeSet = true;
}

int FluidSimulation::getMinPolyhedronTriangleCount() {
    return _minimumSurfacePolyhedronTriangleCount;
}

void FluidSimulation::setMinPolyhedronTriangleCount(int n) {
    if (n < 0) {
        std::string msg = "Error: minimum polyhedron triangle count must be greater than or equal to 0.\n";
        msg += "triangle count: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMinPolyhedronTriangleCount: " << n << std::endl);

    _minimumSurfacePolyhedronTriangleCount = n;
}

vmath::vec3 FluidSimulation::getDomainOffset() {
    return _domainOffset;
}

void FluidSimulation::setDomainOffset(double x, double y, double z) {
    setDomainOffset(vmath::vec3(x, y, z));
}

void FluidSimulation::setDomainOffset(vmath::vec3 offset) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDomainOffset: " << 
                 offset.x << " " << offset.y << " " << offset.z << std::endl);

    _domainOffset = offset;
    _diffuseMaterial.setDomainOffset(offset);
}

double FluidSimulation::getDomainScale() {
    return _domainScale;
}

void FluidSimulation::setDomainScale(double scale) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDomainScale: " << scale << std::endl);

    _domainScale = scale;
    _diffuseMaterial.setDomainScale(scale);
}

void FluidSimulation::setMeshOutputFormatAsPLY() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMeshOutputFormatAsPLY" << std::endl);

    _meshOutputFormat = TriangleMeshFormat::ply;
}

void FluidSimulation::setMeshOutputFormatAsBOBJ() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMeshOutputFormatAsBOBJ" << std::endl);

    _meshOutputFormat = TriangleMeshFormat::bobj;
}

void FluidSimulation::enableConsoleOutput() {
    _logfile.enableConsole();

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableConsoleOutput" << std::endl);
}

void FluidSimulation::disableConsoleOutput() {
    _logfile.disableConsole();

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableConsoleOutput" << std::endl);
}

bool FluidSimulation::isConsoleOutputEnabled() {
    return _logfile.isConsoleEnabled();
}

void FluidSimulation::enableSurfaceReconstruction() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceReconstruction" << std::endl);

    _isSurfaceMeshReconstructionEnabled = true;
}

void FluidSimulation::disableSurfaceReconstruction() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceReconstruction" << std::endl);

    _isSurfaceMeshReconstructionEnabled = false;
}

bool FluidSimulation::isSurfaceReconstructionEnabled() {
    return _isSurfaceMeshReconstructionEnabled;
}

void FluidSimulation::enableAsynchronousMeshing() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableAsynchronousMeshing" << std::endl);

    _isAsynchronousMeshingEnabled = true;
}

void FluidSimulation::disableAsynchronousMeshing() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableAsynchronousMeshing" << std::endl);

    _isAsynchronousMeshingEnabled = false;
}

bool FluidSimulation::isAsynchronousMeshingEnabled() {
    return _isAsynchronousMeshingEnabled;
}

void FluidSimulation::enablePreviewMeshOutput(double cellsize) {
    if (cellsize <= 0.0) {
        std::string msg = "Error: cell size must be greater than 0.0.\n";
        msg += "cellsize: " + _toString(cellsize) + "\n";
        throw std::domain_error(msg);
    }

     _logfile.log(std::ostringstream().flush() << 
             _logfile.getTime() << " enablePreviewMeshOutput: " << cellsize << std::endl);

    _isPreviewSurfaceMeshEnabled = true;
    _previewdx = cellsize;
}

void FluidSimulation::disablePreviewMeshOutput() {
     _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disablePreviewMeshOutput" << std::endl);

    _isPreviewSurfaceMeshEnabled = false;
}

bool FluidSimulation::isPreviewMeshOutputEnabled() {
    return _isPreviewSurfaceMeshEnabled;
}

void FluidSimulation::enableObstacleMeshingOffset() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableObstacleMeshingOffset" << std::endl);

    _isObstacleMeshingOffsetEnabled = true;
}

void FluidSimulation::disableObstacleMeshingOffset() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableObstacleMeshingOffset" << std::endl);

    _isObstacleMeshingOffsetEnabled = false;
}

bool FluidSimulation::isObstacleMeshingOffsetEnabled() {
    return _isObstacleMeshingOffsetEnabled;
}

double FluidSimulation::getObstacleMeshingOffset() {
    return _obstacleMeshingOffset;
}

void FluidSimulation::setObstacleMeshingOffset(double s) { 
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setObstacleMeshingOffset: " << s << std::endl);

    _obstacleMeshingOffset = s; 
}

void FluidSimulation::enableInvertedContactNormals() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableInvertedContactNormals" << std::endl);

    _isInvertedContactNormalsEnabled = true;
}

void FluidSimulation::disableInvertedContactNormals() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableInvertedContactNormals" << std::endl);

    _isInvertedContactNormalsEnabled = false;
}

bool FluidSimulation::isInvertedContactNormalsEnabled() {
    return _isInvertedContactNormalsEnabled;
}

void FluidSimulation::enableSurfaceMotionBlur() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceMotionBlur" << std::endl);

    _isSurfaceMotionBlurEnabled = true;
}

void FluidSimulation::disableSurfaceMotionBlur() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceMotionBlur" << std::endl);

    _isSurfaceMotionBlurEnabled = false;
}

bool FluidSimulation::isSurfaceMotionBlurEnabled() {
    return _isSurfaceMotionBlurEnabled;
}

void FluidSimulation::enableWhitewaterMotionBlur() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableWhitewaterMotionBlur" << std::endl);

    _isWhitewaterMotionBlurEnabled = true;
}

void FluidSimulation::disableWhitewaterMotionBlur() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableWhitewaterMotionBlur" << std::endl);

    _isWhitewaterMotionBlurEnabled = false;
}

bool FluidSimulation::isWhitewaterMotionBlurEnabled() {
    return _isWhitewaterMotionBlurEnabled;
}

void FluidSimulation::enableRemoveSurfaceNearDomain() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableRemoveSurfaceNearDomain" << std::endl);

    _isRemoveSurfaceNearDomainEnabled = true;
}

void FluidSimulation::disableRemoveSurfaceNearDomain() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableRemoveSurfaceNearDomain" << std::endl);

    _isRemoveSurfaceNearDomainEnabled = false;
}

bool FluidSimulation::isRemoveSurfaceNearDomainEnabled() {
    return _isRemoveSurfaceNearDomainEnabled;
}

int FluidSimulation::getRemoveSurfaceNearDomainDistance() {
    return _removeSurfaceNearDomainDistance;
}

void FluidSimulation::setRemoveSurfaceNearDomainDistance(int n) {
    if (n < 0) {
        std::string msg = "Error: distance must be greater than or equal to zero.\n";
        msg += "distance: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setRemoveSurfaceNearDomainDistance: " << n << std::endl);

    _removeSurfaceNearDomainDistance = n;
}

void FluidSimulation::enableFluidParticleOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableFluidParticleOutput" << std::endl);

    _isFluidParticleOutputEnabled = true;
}

void FluidSimulation::disableFluidParticleOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableFluidParticleOutput" << std::endl);

    _isFluidParticleOutputEnabled = false;
}

bool FluidSimulation::isFluidParticleOutputEnabled() {
    return _isFluidParticleOutputEnabled;
}

void FluidSimulation::enableInternalObstacleMeshOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableInternalObstacleMeshOutput" << std::endl);

    _isInternalObstacleMeshOutputEnabled = true;
}

void FluidSimulation::disableInternalObstacleMeshOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableInternalObstacleMeshOutput" << std::endl);

    _isInternalObstacleMeshOutputEnabled = false;
}

bool FluidSimulation::isInternalObstacleMeshOutputEnabled() {
    return _isInternalObstacleMeshOutputEnabled;
}

void FluidSimulation::enableDiffuseMaterialOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffuseMaterialOutput" << std::endl);

    _isDiffuseMaterialOutputEnabled = true;
}

void FluidSimulation::disableDiffuseMaterialOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffuseMaterialOutput" << std::endl);

    _isDiffuseMaterialOutputEnabled = false;
}

bool FluidSimulation::isDiffuseMaterialOutputEnabled() {
    return _isDiffuseMaterialOutputEnabled;
}

void FluidSimulation::enableDiffuseParticleEmission() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffuseParticleEmission" << std::endl);

    _diffuseMaterial.enableDiffuseParticleEmission();
}

void FluidSimulation::disableDiffuseParticleEmission() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffuseParticleEmission" << std::endl);

    _diffuseMaterial.disableDiffuseParticleEmission();
}

bool FluidSimulation::isDiffuseParticleEmissionEnabled() {
    return _diffuseMaterial.isDiffuseParticleEmissionEnabled();
}

void FluidSimulation::enableDiffuseFoam() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffuseFoam" << std::endl);

    _diffuseMaterial.enableFoam();
}

void FluidSimulation::disableDiffuseFoam() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffuseFoam" << std::endl);

    _diffuseMaterial.disableFoam();
}

bool FluidSimulation::isDiffuseFoamEnabled() {
    return _diffuseMaterial.isFoamEnabled();
}

void FluidSimulation::enableDiffuseBubbles() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffuseBubbles" << std::endl);

    _diffuseMaterial.enableBubbles();
}

void FluidSimulation::disableDiffuseBubbles() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffuseBubbles" << std::endl);

    _diffuseMaterial.disableBubbles();
}

bool FluidSimulation::isDiffuseBubblesEnabled() {
    return _diffuseMaterial.isBubblesEnabled();
}

void FluidSimulation::enableDiffuseSpray() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffuseSpray" << std::endl);

    _diffuseMaterial.enableSpray();
}

void FluidSimulation::disableDiffuseSpray() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffuseSpray" << std::endl);

    _diffuseMaterial.disableSpray();
}

bool FluidSimulation::isDiffuseSprayEnabled() {
    return _diffuseMaterial.isSprayEnabled();
}

void FluidSimulation::enableBubbleDiffuseMaterial() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableBubbleDiffuseMaterial" << std::endl);

    _isBubbleDiffuseMaterialEnabled = true;
}

void FluidSimulation::enableSprayDiffuseMaterial() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSprayDiffuseMaterial" << std::endl);

    _isSprayDiffuseMaterialEnabled = true;
}

void FluidSimulation::enableFoamDiffuseMaterial() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableFoamDiffuseMaterial" << std::endl);

    _isFoamDiffuseMaterialEnabled = true;
}

void FluidSimulation::disableBubbleDiffuseMaterial() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableBubbleDiffuseMaterial" << std::endl);

    _isBubbleDiffuseMaterialEnabled = false;
}

void FluidSimulation::disableSprayDiffuseMaterial() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSprayDiffuseMaterial" << std::endl);

    _isSprayDiffuseMaterialEnabled = false;
}

void FluidSimulation::disableFoamDiffuseMaterial() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableFoamDiffuseMaterial" << std::endl);

    _isFoamDiffuseMaterialEnabled = false;
}

bool FluidSimulation::isBubbleDiffuseMaterialEnabled() {
    return _isBubbleDiffuseMaterialEnabled;
}

bool FluidSimulation::isSprayDiffuseMaterialEnabled() {
    return _isSprayDiffuseMaterialEnabled;
}

bool FluidSimulation::isFoamDiffuseMaterialEnabled() {
    return _isFoamDiffuseMaterialEnabled;
}

void FluidSimulation::outputDiffuseMaterialAsSeparateFiles() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " outputDiffuseMaterialAsSeparateFiles" << std::endl);

    _isDiffuseMaterialFilesSeparated = true;
}

void FluidSimulation::outputDiffuseMaterialAsSingleFile() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " outputDiffuseMaterialAsSingleFile" << std::endl);

    _isDiffuseMaterialFilesSeparated = false;
}

bool FluidSimulation::isDiffuseMaterialOutputAsSeparateFiles() {
    return _isDiffuseMaterialFilesSeparated;
}

double FluidSimulation::getDiffuseEmitterGenerationRate() {
    return _diffuseMaterial.getEmitterGenerationRate();
}

void FluidSimulation::setDiffuseEmitterGenerationRate(double rate) {
    if (rate < 0.0 || rate > 1.0) {
        std::string msg = "Error: emitter generation rate must be in range [0.0, 1.0].\n";
        msg += "rate: " + _toString(rate) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseEmitterGenerationRate: " << rate << std::endl);

    _diffuseMaterial.setEmitterGenerationRate(rate);
}

double FluidSimulation::getMinDiffuseEmitterEnergy() {
    return _diffuseMaterial.getMinEmitterEnergy();
}

void FluidSimulation::setMinDiffuseEmitterEnergy(double e) {
    if (e < 0) {
        std::string msg = "Error: min diffuse emitter energy must be greater than or equal to 0.\n";
        msg += "energy: " + _toString(e) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMinDiffuseEmitterEnergy: " << e << std::endl);

    _diffuseMaterial.setMinEmitterEnergy(e);
}

double FluidSimulation::getMaxDiffuseEmitterEnergy() {
    return _diffuseMaterial.getMaxEmitterEnergy();
}

void FluidSimulation::setMaxDiffuseEmitterEnergy(double e) {
    if (e < 0) {
        std::string msg = "Error: max diffuse emitter energy must be greater than or equal to 0.\n";
        msg += "energy: " + _toString(e) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMaxDiffuseEmitterEnergy: " << e << std::endl);

    _diffuseMaterial.setMaxEmitterEnergy(e);
}

double FluidSimulation::getMinDiffuseWavecrestCurvature() {
    return _diffuseMaterial.getMinWavecrestCurvature();
}

void FluidSimulation::setMinDiffuseWavecrestCurvature(double k) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMinDiffuseWavecrestCurvature: " << k << std::endl);

    _diffuseMaterial.setMinWavecrestCurvature(k);
}

double FluidSimulation::getMaxDiffuseWavecrestCurvature() {
    return _diffuseMaterial.getMaxWavecrestCurvature();
}

void FluidSimulation::setMaxDiffuseWavecrestCurvature(double k) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMaxDiffuseWavecrestCurvature: " << k << std::endl);

    _diffuseMaterial.setMaxWavecrestCurvature(k);
}

double FluidSimulation::getMinDiffuseTurbulence() {
    return _diffuseMaterial.getMinTurbulence();
}

void FluidSimulation::setMinDiffuseTurbulence(double t) {
    if (t < 0) {
        std::string msg = "Error: min diffuse turbulence must be greater than or equal to 0.\n";
        msg += "turbulence: " + _toString(t) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMinDiffuseTurbulence: " << t << std::endl);

    _diffuseMaterial.setMinTurbulence(t);
}

double FluidSimulation::getMaxDiffuseTurbulence() {
    return _diffuseMaterial.getMaxTurbulence();
}

void FluidSimulation::setMaxDiffuseTurbulence(double t) {
    if (t < 0) {
        std::string msg = "Error: max diffuse turbulence must be greater than or equal to 0.\n";
        msg += "turbulence: " + _toString(t) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMaxDiffuseTurbulence: " << t << std::endl);

    _diffuseMaterial.setMaxTurbulence(t);
}

int FluidSimulation::getMaxNumDiffuseParticles() {
    return _diffuseMaterial.getMaxNumDiffuseParticles();
}

void FluidSimulation::setMaxNumDiffuseParticles(int n) {
    if (n < 0) {
        std::string msg = "Error: maxNumDiffuseParticles must be greater than or equal to 0.\n";
        msg += "n: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMaxNumDiffuseParticles: " << n << std::endl);

    _diffuseMaterial.setMaxNumDiffuseParticles(n);
}

AABB FluidSimulation::getDiffuseEmitterGenerationBounds() {
    return _diffuseMaterial.getEmitterGenerationBounds();
}

void FluidSimulation::setDiffuseEmitterGenerationBounds(AABB bbox) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseEmitterGenerationBounds: " << 
                 bbox.position.x << " " << bbox.position.y << " " << bbox.position.z << " " <<
                 bbox.width << " " << bbox.height << " " << bbox.depth << std::endl);

    _diffuseMaterial.setEmitterGenerationBounds(bbox);
}

double FluidSimulation::getMinDiffuseParticleLifetime() {
    return _diffuseMaterial.getMinDiffuseParticleLifetime();
}   

void FluidSimulation::setMinDiffuseParticleLifetime(double lifetime) {
    if (lifetime < 0) {
        std::string msg = "Error: min lifetime must be greater than or equal to 0.\n";
        msg += "lifetime: " + _toString(lifetime) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMinDiffuseParticleLifetime: " << lifetime << std::endl);

    _diffuseMaterial.setMinDiffuseParticleLifetime(lifetime);
}

double FluidSimulation::getMaxDiffuseParticleLifetime() {
    return _diffuseMaterial.getMaxDiffuseParticleLifetime();
}   

void FluidSimulation::setMaxDiffuseParticleLifetime(double lifetime) {
    if (lifetime < 0) {
        std::string msg = "Error: max lifetime must be greater than or equal to 0.\n";
        msg += "lifetime: " + _toString(lifetime) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMaxDiffuseParticleLifetime: " << lifetime << std::endl);

    _diffuseMaterial.setMaxDiffuseParticleLifetime(lifetime);
}

double FluidSimulation::getDiffuseParticleLifetimeVariance() {
    return _diffuseMaterial.getDiffuseParticleLifetimeVariance();
}

void FluidSimulation::setDiffuseParticleLifetimeVariance(double variance) {
    if (variance < 0) {
        std::string msg = "Error: lifetime variance must be greater than or equal to 0.\n";
        msg += "variance: " + _toString(variance) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseParticleLifetimeVariance: " << variance << std::endl);

    _diffuseMaterial.setDiffuseParticleLifetimeVariance(variance);
}

double FluidSimulation::getFoamParticleLifetimeModifier() {
    return _diffuseMaterial.getFoamParticleLifetimeModifier();
}

void FluidSimulation::setFoamParticleLifetimeModifier(double modifier) {
    if (modifier < 0) {
        std::string msg = "Error: foam lifetime modifier must be greater than or equal to 0.\n";
        msg += "modifier: " + _toString(modifier) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setFoamParticleLifetimeModifier: " << modifier << std::endl);

    _diffuseMaterial.setFoamParticleLifetimeModifier(modifier);
}

double FluidSimulation::getBubbleParticleLifetimeModifier() {
    return _diffuseMaterial.getBubbleParticleLifetimeModifier();
}

void FluidSimulation::setBubbleParticleLifetimeModifier(double modifier) {
    if (modifier < 0) {
        std::string msg = "Error: bubble lifetime modifier must be greater than or equal to 0.\n";
        msg += "modifier: " + _toString(modifier) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setBubbleParticleLifetimeModifier: " << modifier << std::endl);

    _diffuseMaterial.setBubbleParticleLifetimeModifier(modifier);
}

double FluidSimulation::getSprayParticleLifetimeModifier() {
    return _diffuseMaterial.getSprayParticleLifetimeModifier();
}

void FluidSimulation::setSprayParticleLifetimeModifier(double modifier) {
    if (modifier < 0) {
        std::string msg = "Error: spray lifetime modifier must be greater than or equal to 0.\n";
        msg += "modifier: " + _toString(modifier) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSprayParticleLifetimeModifier: " << modifier << std::endl);

    _diffuseMaterial.setSprayParticleLifetimeModifier(modifier);
}

double FluidSimulation::getDiffuseParticleWavecrestEmissionRate() {
    return _diffuseMaterial.getDiffuseParticleWavecrestEmissionRate();
}

void FluidSimulation::setDiffuseParticleWavecrestEmissionRate(double r) {
    if (r < 0) {
        std::string msg = "Error: wavecrest emission rate must be greater than or equal to 0.\n";
        msg += "rate: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseParticleWavecrestEmissionRate: " << r << std::endl);

    _diffuseMaterial.setDiffuseParticleWavecrestEmissionRate(r);
}

double FluidSimulation::getDiffuseParticleTurbulenceEmissionRate() {
    return _diffuseMaterial.getDiffuseParticleTurbulenceEmissionRate();
}

void FluidSimulation::setDiffuseParticleTurbulenceEmissionRate(double r) {
    if (r < 0) {
        std::string msg = "Error: turbulence emission rate must be greater than or equal to 0.\n";
        msg += "rate: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseParticleTurbulenceEmissionRate: " << r << std::endl);

    _diffuseMaterial.setDiffuseParticleTurbulenceEmissionRate(r);
}

void FluidSimulation::getDiffuseParticleEmissionRates(double *rwc, 
                                                      double *rt) {
    _diffuseMaterial.getDiffuseParticleEmissionRates(rwc, rt);
}

void FluidSimulation::setDiffuseParticleEmissionRates(double r) {
    if (r < 0) {
        std::string msg = "Error: emission rate must be greater than or equal to 0.\n";
        msg += "rate: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseParticleEmissionRates: " << r << std::endl);

    _diffuseMaterial.setDiffuseParticleEmissionRates(r);
}

void FluidSimulation::setDiffuseParticleEmissionRates(double rwc, 
                                                      double rt) {
    if (rwc < 0 || rt < 0) {
        std::string msg = "Error: emission rates must be greater than or equal to 0.\n";
        msg += "wavecrest emission rate: " + _toString(rwc) + "\n";
        msg += "turbulence emission rate: " + _toString(rt) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseParticleEmissionRates: " << 
                 rwc << " " << rt << std::endl);

    _diffuseMaterial.setDiffuseParticleEmissionRates(rwc, rt);
}

double FluidSimulation::getDiffuseFoamAdvectionStrength() {
    return _diffuseMaterial.getFoamAdvectionStrength();
}

void FluidSimulation::setDiffuseFoamAdvectionStrength(double s) {
    if (s < 0.0 || s > 1.0) {
        std::string msg = "Error: advection strength must be in range [0.0, 1.0].\n";
        msg += "strendth: " + _toString(s) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseFoamAdvectionStrength: " << s << std::endl);

    _diffuseMaterial.setFoamAdvectionStrength(s);
}

double FluidSimulation::getDiffuseFoamLayerDepth() {
    return _diffuseMaterial.getFoamLayerDepth();
}

void FluidSimulation::setDiffuseFoamLayerDepth(double depth) {
    if (depth < 0.0 || depth > 1.0) {
        std::string msg = "Error: foam layer depth must be in range [0.0, 1.0].\n";
        msg += "depth: " + _toString(depth) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseFoamLayerDepth: " << depth << std::endl);

    _diffuseMaterial.setFoamLayerDepth(depth);
}

double FluidSimulation::getDiffuseFoamLayerOffset() {
    return _diffuseMaterial.getFoamLayerOffset();
}

void FluidSimulation::setDiffuseFoamLayerOffset(double offset) {
    if (offset < -1.0 || offset > 1.0) {
        std::string msg = "Error: foam layer offset must be in range [-1.0, 1.0].\n";
        msg += "offset: " + _toString(offset) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseFoamLayerOffset: " << offset << std::endl);

    _diffuseMaterial.setFoamLayerOffset(offset);

}

void FluidSimulation::enableDiffusePreserveFoam() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffusePreserveFoam" << std::endl);

    _diffuseMaterial.enablePreserveFoam();
}

void FluidSimulation::disableDiffusePreserveFoam() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffusePreserveFoam" << std::endl);

    _diffuseMaterial.disablePreserveFoam();
}

bool FluidSimulation::isDiffusePreserveFoamEnabled() {
    return _diffuseMaterial.isPreserveFoamEnabled();
}

double FluidSimulation::getDiffuseFoamPreservationRate() {
    return _diffuseMaterial.getFoamPreservationRate();
}

void FluidSimulation::setDiffuseFoamPreservationRate(double rate) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseFoamPreservationRate: " << rate << std::endl);

    _diffuseMaterial.setFoamPreservationRate(rate);
}

double FluidSimulation::getMinDiffuseFoamDensity() {
    return _diffuseMaterial.getMinFoamDensity();
}

void FluidSimulation::setMinDiffuseFoamDensity(double d) {
    if (d < 0) {
        std::string msg = "Error: min density must be greater than or equal to 0.\n";
        msg += "density: " + _toString(d) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMinDiffuseFoamDensity: " << d << std::endl);

    _diffuseMaterial.setMinFoamDensity(d);
}

double FluidSimulation::getMaxDiffuseFoamDensity() {
    return _diffuseMaterial.getMaxFoamDensity();
}

void FluidSimulation::setMaxDiffuseFoamDensity(double d) {
    if (d < 0) {
        std::string msg = "Error: max density must be greater than or equal to 0.\n";
        msg += "density: " + _toString(d) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setMaxDiffuseFoamDensity: " << d << std::endl);

    _diffuseMaterial.setMaxFoamDensity(d);
}

double FluidSimulation::getDiffuseBubbleDragCoefficient() {
    return _diffuseMaterial.getBubbleDragCoefficient();
}

void FluidSimulation::setDiffuseBubbleDragCoefficient(double d) {
    if (d < 0.0 || d > 1.0) {
        std::string msg = "Error: drag coefficient must be in range [0.0, 1.0].\n";
        msg += "coefficient: " + _toString(d) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseBubbleDragCoefficient: " << d << std::endl);

    _diffuseMaterial.setBubbleDragCoefficient(d);
}

double FluidSimulation::getDiffuseBubbleBouyancyCoefficient() {
    return _diffuseMaterial.getBubbleBouyancyCoefficient();
}

void FluidSimulation::setDiffuseBubbleBouyancyCoefficient(double b) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseBubbleBouyancyCoefficient: " << b << std::endl);

    _diffuseMaterial.setBubbleBouyancyCoefficient(b);
}

double FluidSimulation::getDiffuseSprayDragCoefficient() {
    return _diffuseMaterial.getSprayDragCoefficient();
}

void FluidSimulation::setDiffuseSprayDragCoefficient(double d) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseSprayDragCoefficient: " << d << std::endl);

    _diffuseMaterial.setSprayDragCoefficient(d);
}

LimitBehaviour FluidSimulation::getDiffuseFoamLimitBehaviour() {
    return _diffuseMaterial.getFoamLimitBehaviour();
}

void FluidSimulation::setDiffuseFoamLimitBehaviour(LimitBehaviour b) {
    std::string typestr;
    if (b == LimitBehaviour::collide) {
        typestr = "collide";
    } else if (b == LimitBehaviour::ballistic) {
        typestr = "ballistic";
    } else if (b == LimitBehaviour::kill) {
        typestr = "kill";
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseFoamLimitBehavour: " << typestr << std::endl);

    _diffuseMaterial.setFoamLimitBehavour(b);
}

LimitBehaviour FluidSimulation::getDiffuseBubbleLimitBehaviour() {
    return _diffuseMaterial.getBubbleLimitBehaviour();
}

void FluidSimulation::setDiffuseBubbleLimitBehaviour(LimitBehaviour b) {
    std::string typestr;
    if (b == LimitBehaviour::collide) {
        typestr = "collide";
    } else if (b == LimitBehaviour::ballistic) {
        typestr = "ballistic";
    } else if (b == LimitBehaviour::kill) {
        typestr = "kill";
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseBubbleLimitBehavour: " << typestr << std::endl);

    _diffuseMaterial.setBubbleLimitBehavour(b);
}

LimitBehaviour FluidSimulation::getDiffuseSprayLimitBehaviour() {
    return _diffuseMaterial.getSprayLimitBehaviour();
}

void FluidSimulation::setDiffuseSprayLimitBehaviour(LimitBehaviour b) {
    std::string typestr;
    if (b == LimitBehaviour::collide) {
        typestr = "collide";
    } else if (b == LimitBehaviour::ballistic) {
        typestr = "ballistic";
    } else if (b == LimitBehaviour::kill) {
        typestr = "kill";
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseSprayLimitBehavour: " << typestr << std::endl);

    _diffuseMaterial.setSprayLimitBehavour(b);
}

std::vector<bool> FluidSimulation::getDiffuseFoamActiveBoundarySides() {
    return _diffuseMaterial.getFoamActiveBoundarySides();
}

void FluidSimulation::setDiffuseFoamActiveBoundarySides(std::vector<bool> active) {
    if (active.size() != 6) {
        std::string msg = "Error: foam active boundary vector must be of length 6.\n";
        msg += "length: " + _toString(active.size()) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseFoamActiveBoundarySides: " << 
                 active[0] << " " << active[1] << " " << active[2] << " " << 
                 active[3] << " " << active[4] << " " << active[5] << std::endl);

    _diffuseMaterial.setFoamActiveBoundarySides(active);
}

std::vector<bool> FluidSimulation::getDiffuseBubbleActiveBoundarySides() {
    return _diffuseMaterial.getBubbleActiveBoundarySides();
}

void FluidSimulation::setDiffuseBubbleActiveBoundarySides(std::vector<bool> active) {
    if (active.size() != 6) {
        std::string msg = "Error: bubble active boundary vector must be of length 6.\n";
        msg += "length: " + _toString(active.size()) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseBubbleActiveBoundarySides: " << 
                 active[0] << " " << active[1] << " " << active[2] << " " << 
                 active[3] << " " << active[4] << " " << active[5] << std::endl);

    _diffuseMaterial.setBubbleActiveBoundarySides(active);
}

std::vector<bool> FluidSimulation::getDiffuseSprayActiveBoundarySides() {
    return _diffuseMaterial.getSprayActiveBoundarySides();
}

void FluidSimulation::setDiffuseSprayActiveBoundarySides(std::vector<bool> active) {
    if (active.size() != 6) {
        std::string msg = "Error: spray active boundary vector must be of length 6.\n";
        msg += "length: " + _toString(active.size()) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseSprayActiveBoundarySides: " << 
                 active[0] << " " << active[1] << " " << active[2] << " " << 
                 active[3] << " " << active[4] << " " << active[5] << std::endl);

    _diffuseMaterial.setSprayActiveBoundarySides(active);
}

double FluidSimulation::getDiffuseObstacleInfluenceBaseLevel() {
    return _diffuseObstacleInfluenceBaseLevel;
}

void FluidSimulation::setDiffuseObstacleInfluenceBaseLevel(double level) {
    if (level < 0.0) {
        std::string msg = "Error: base level must be greater than or equal to 0.0.\n";
        msg += "base level: " + _toString(level) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseObstacleInfluenceBaseLevel: " << level << std::endl);

    _diffuseObstacleInfluenceBaseLevel = level;
}

double FluidSimulation::getDiffuseObstacleInfluenceDecayRate() {
    return _diffuseObstacleInfluenceDecayRate;
}

void FluidSimulation::setDiffuseObstacleInfluenceDecayRate(double decay) {
    if (decay < 0.0) {
        std::string msg = "Error: decay rate must be greater than or equal to 0.0.\n";
        msg += "decay rate: " + _toString(decay) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseObstacleInfluenceDecayRate: " << decay << std::endl);

    _diffuseObstacleInfluenceDecayRate = decay;
}

void FluidSimulation::enableOpenCLParticleAdvection() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableOpenCLParticleAdvection" << std::endl);

    _particleAdvector.enableOpenCL();
}

void FluidSimulation::disableOpenCLParticleAdvection() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableOpenCLParticleAdvection" << std::endl);

    _particleAdvector.disableOpenCL();
}

bool FluidSimulation::isOpenCLParticleAdvectionEnabled() {
    return _particleAdvector.isOpenCLEnabled();
}

void FluidSimulation::enableOpenCLScalarField() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableOpenCLScalarField" << std::endl);

    _mesherScalarFieldAccelerator.enableOpenCL();
}

void FluidSimulation::disableOpenCLScalarField() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableOpenCLScalarField" << std::endl);

    _mesherScalarFieldAccelerator.disableOpenCL();
}

bool FluidSimulation::isOpenCLScalarFieldEnabled() {
    return _mesherScalarFieldAccelerator.isOpenCLEnabled();
}

int FluidSimulation::getParticleAdvectionKernelWorkLoadSize() {
    return _particleAdvector.getKernelWorkLoadSize();
}

void FluidSimulation::setParticleAdvectionKernelWorkLoadSize(int n) {
    if (n < 1) {
        std::string msg = "Error: work load size must be greater than or equal to 1.\n";
        msg += "size: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setParticleAdvectionKernelWorkLoadSize: " << n << std::endl);

    _particleAdvector.setKernelWorkLoadSize(n);
}

int FluidSimulation::getScalarFieldKernelWorkLoadSize() {
    return _mesherScalarFieldAccelerator.getKernelWorkLoadSize();
}

void FluidSimulation::setScalarFieldKernelWorkLoadSize(int n) {
    if (n < 1) {
        std::string msg = "Error: work load size must be greater than or equal to 1.\n";
        msg += "size: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setScalarFieldKernelWorkLoadSize: " << n << std::endl);

    _mesherScalarFieldAccelerator.setKernelWorkLoadSize(n);
}

int FluidSimulation::getMaxThreadCount() {
    return ThreadUtils::getMaxThreadCount();
}

void FluidSimulation::setMaxThreadCount(int n) {
    if (n < 1) {
        std::string msg = "Error: thread count must be greater than or equal to 1.\n";
        msg += "thread count: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setMaxThreadCount: " << n << std::endl);

    ThreadUtils::setMaxThreadCount(n);
}

void FluidSimulation::addBodyForce(double fx, double fy, double fz) { 
    addBodyForce(vmath::vec3(fx, fy, fz)); 
}

void FluidSimulation::addBodyForce(vmath::vec3 f) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " addBodyForce: " <<
                 f.x << " " << f.y << " " << f.z << std::endl);

    _constantBodyForces.push_back(f);
}

vmath::vec3 FluidSimulation::getConstantBodyForce() {
    return _getConstantBodyForce();
}

void FluidSimulation::resetBodyForce() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " resetBodyForce" << std::endl);

    _constantBodyForces.clear();
}

double FluidSimulation::getViscosity() {
    return _constantViscosityValue;
}

void FluidSimulation::setViscosity(double v) {
    if (v < 0.0) {
        std::string msg = "Error: viscosity must be greater than or equal to 0.\n";
        msg += "viscosity: " + _toString(v) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setViscosity: " << v << std::endl);

    if (!_isViscosityEnabled) {
        _viscosity = Array3d<float>(_isize + 1, _jsize + 1, _ksize + 1);
        _isViscosityEnabled = true;
    }
    _viscosity.fill(v);
    _constantViscosityValue = v;
}

double FluidSimulation::getSurfaceTension() {
    return _surfaceTensionConstant;
}

void FluidSimulation::setSurfaceTension(double k) {
    if (k < 0.0) {
        std::string msg = "Error: surface tension must be greater than or equal to 0.\n";
        msg += "surface tension: " + _toString(k) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSurfaceTension: " << k << std::endl);

    double eps = 1e-6;
    _isSurfaceTensionEnabled = k > eps;
    _surfaceTensionConstant = k;
}

void FluidSimulation::enableSheetSeeding() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSheetSeeding" << std::endl);

    _isSheetSeedingEnabled = true;
}

void FluidSimulation::disableSheetSeeding() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSheetSeeding" << std::endl);

    _isSheetSeedingEnabled = false;
}

bool FluidSimulation::isSheetSeedingEnabled() {
    return _isSheetSeedingEnabled;
}

double FluidSimulation::getSheetFillThreshold() {
    return _sheetFillThreshold;
}

void FluidSimulation::setSheetFillThreshold(double f) {
    if (f < -1.0 || f > 0.0) {
        std::string msg = "Error: sheet fill threshold must be in range [-1.0, 0.0].\n";
        msg += "threshold: " + _toString(f) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSheetFillThreshold: " << f << std::endl);

    _sheetFillThreshold = f;
}

double FluidSimulation::getSheetFillRate() {
    return _sheetFillRate;
}

void FluidSimulation::setSheetFillRate(double r) {
    if (r < 0.0 || r > 1.0) {
        std::string msg = "Error: sheet fill rate must be in range [0.0, 1.0].\n";
        msg += "threshold: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setSheetFillRate: " << r << std::endl);

    _sheetFillRate = r;
}

double FluidSimulation::getBoundaryFriction() {
    return _domainBoundaryFriction;
}

void FluidSimulation::setBoundaryFriction(double f) {
    if (f < 0.0 || f > 1.0) {
        std::string msg = "Error: boundary friction must be in range [0.0, 1.0].\n";
        msg += "friction: " + _toString(f) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setBoundaryFriction: " << f << std::endl);

    _domainMeshObject.setFriction(f);
    _domainBoundaryFriction = f;
}

int FluidSimulation::getCFLConditionNumber() {
    return _CFLConditionNumber;
}

void FluidSimulation::setCFLConditionNumber(int n) {
    if (n < 1) {
        std::string msg = "Error: CFL must be greater than or equal to 1.\n";
        msg += "CFL: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setCFLConditionNumber: " << n << std::endl);

    _CFLConditionNumber = n;
}

double FluidSimulation::getSurfaceTensionConditionNumber() {
    return _surfaceTensionConditionNumber;
}

void FluidSimulation::setSurfaceTensionConditionNumber(double n) {
    if (n <= 0.0) {
        std::string msg = "Error: condition number must be greater than 0.0.\n";
        msg += "number: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setSurfaceTensionConditionNumber: " << n << std::endl);

    _surfaceTensionConditionNumber = n;
}

int FluidSimulation::getMinTimeStepsPerFrame() {
    return _minFrameTimeSteps;
}

void FluidSimulation::setMinTimeStepsPerFrame(int n) {
    if (n < 1) {
        std::string msg = "Error: min step count must be greater than or equal to 1.\n";
        msg += "Step count: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setMinTimeStepsPerFrame: " << n << std::endl);

    _minFrameTimeSteps = n;
}

int FluidSimulation::getMaxTimeStepsPerFrame() {
    return _maxFrameTimeSteps;
}

void FluidSimulation::setMaxTimeStepsPerFrame(int n) {
    if (n < 1) {
        std::string msg = "Error: max step count must be greater than or equal to 1.\n";
        msg += "Step count: " + _toString(n) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setMaxTimeStepsPerFrame: " << n << std::endl);

    _maxFrameTimeSteps = n;
}

void FluidSimulation::enableAdaptiveObstacleTimeStepping() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableAdaptiveObstacleTimeStepping" << std::endl);

    _isAdaptiveObstacleTimeSteppingEnabled = true;
}

void FluidSimulation::disableAdaptiveObstacleTimeStepping() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableAdaptiveObstacleTimeStepping" << std::endl);

    _isAdaptiveObstacleTimeSteppingEnabled = false;
}

bool FluidSimulation::isAdaptiveObstacleTimeSteppingEnabled() {
    return _isAdaptiveObstacleTimeSteppingEnabled;
}

void FluidSimulation::enableExtremeVelocityRemoval() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableExtremeVelocityRemoval" << std::endl);

    _isExtremeVelocityRemovalEnabled = true;
}

void FluidSimulation::disableExtremeVelocityRemoval() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableExtremeVelocityRemoval" << std::endl);

    _isExtremeVelocityRemovalEnabled = false;
}

bool FluidSimulation::isExtremeVelocityRemovalEnabled() {
    return _isExtremeVelocityRemovalEnabled;
}

double FluidSimulation::getPICFLIPRatio() {
    return _ratioPICFLIP;
}

void FluidSimulation::setPICFLIPRatio(double r) {
    if (r < 0.0 || r > 1.0) {
        std::string msg = "Error: PICFLIP ratio must be in range [0.0, 1.0].\n";
        msg += "ratio: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setPICFLIPRatio: " << r << std::endl);

    _ratioPICFLIP = r;
}

void FluidSimulation::setPreferredGPUDevice(std::string deviceName) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setPreferredGPUDevice: " << deviceName << std::endl);

    OpenCLUtils::setPreferredGPUDevice(deviceName);
}

std::string FluidSimulation::getPreferredGPUDevice() {
    return OpenCLUtils::getPreferredGPUDevice();
}

void FluidSimulation::enableStaticSolidLevelSetPrecomputation() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableStaticSolidLevelSetPrecomputation" << std::endl);

    _isStaticSolidLevelSetPrecomputed = true;
}

void FluidSimulation::disableStaticSolidLevelSetPrecomputation() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableStaticSolidLevelSetPrecomputation" << std::endl);

    _isStaticSolidLevelSetPrecomputed = false;
}

bool FluidSimulation::isStaticSolidLevelSetPrecomputationEnabled() {
    return _isStaticSolidLevelSetPrecomputed;
}

void FluidSimulation::enableTemporaryMeshLevelSet() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableTemporaryMeshLevelSet" << std::endl);

    _isTempSolidLevelSetEnabled = true;
}

void FluidSimulation::disableTemporaryMeshLevelSet() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableTemporaryMeshLevelSet" << std::endl);

    _isTempSolidLevelSetEnabled = false;
}

bool FluidSimulation::isTemporaryMeshLevelSetEnabled() {
    return _isTempSolidLevelSetEnabled;
}

void FluidSimulation::addMeshFluidSource(MeshFluidSource *source) {
    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        if (source->getID() == _meshFluidSources[i]->getID()) {
            std::string msg = "Error: Mesh fluid source has already been added.\n";
            throw std::runtime_error(msg);
        }
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " addMeshFluidSource: " << source << std::endl);

    _meshFluidSources.push_back(source);
}

void FluidSimulation::removeMeshFluidSource(MeshFluidSource *source) {
    bool isFound = false;
    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        if (source->getID() == _meshFluidSources[i]->getID()) {
            _meshFluidSources.erase(_meshFluidSources.begin() + i);
            isFound = true;
            break;
        }
    }

    if (!isFound) {
        std::string msg = "Error: could not find mesh fluid source to remove.\n";
        msg += "mesh fluid source: " + _toString(source) + "\n";
        throw std::invalid_argument(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " removeMeshFluidSource: " << source << std::endl);
}

void FluidSimulation::removeMeshFluidSources() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " removeMeshFluidSources" << std::endl);

    _meshFluidSources.clear();
}

void FluidSimulation::addMeshObstacle(MeshObject *obstacle) {
    for (unsigned int i = 0; i < _obstacles.size(); i++) {
        if (obstacle == _obstacles[i]) {
            std::string msg = "Error: mesh obstacle has already been added.\n";
            throw std::runtime_error(msg);
        }
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " addMeshObstacle: " << obstacle << std::endl);

    _obstacles.push_back(obstacle);

    _isSolidLevelSetUpToDate = false;
}

void FluidSimulation::removeMeshObstacle(MeshObject *obstacle) {
    bool isFound = false;
    for (unsigned int i = 0; i < _obstacles.size(); i++) {
        if (obstacle == _obstacles[i]) {
            _obstacles.erase(_obstacles.begin() + i);
            isFound = true;
            break;
        }
    }

    if (!isFound) {
        std::string msg = "Error: could not find mesh obstacle to remove.\n";
        msg += "mesh obstacle: " + _toString(obstacle) + "\n";
        throw std::invalid_argument(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " removeMeshObstacle: " << obstacle << std::endl);

    _isSolidLevelSetUpToDate = false;
}

void FluidSimulation::removeMeshObstacles() {
    _obstacles.clear();

    _isSolidLevelSetUpToDate = false;
}

void FluidSimulation::addMeshFluid(MeshObject fluid) {
    addMeshFluid(fluid, vmath::vec3(0.0, 0.0, 0.0));
}

void FluidSimulation::addMeshFluid(MeshObject fluid, vmath::vec3 velocity) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " addMeshFluid: " << velocity << std::endl);

    _addedFluidMeshObjectQueue.push_back(FluidMeshObject(fluid, velocity));
}

unsigned int FluidSimulation::getNumMarkerParticles() {
    return _markerParticles.size();
}

std::vector<MarkerParticle> FluidSimulation::getMarkerParticles() {
    return getMarkerParticles(0, _markerParticles.size());
}

std::vector<MarkerParticle> FluidSimulation::getMarkerParticles(int startidx, int endidx) {
    int size = _markerParticles.size();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<MarkerParticle> particles;
    particles.reserve(endidx - startidx);

    for (int i = startidx; i < endidx; i++) {
        particles.push_back(_markerParticles[i]);
    }

    return particles;
}

std::vector<vmath::vec3> FluidSimulation::getMarkerParticlePositions() {
    return getMarkerParticlePositions(0, _markerParticles.size());
}

std::vector<vmath::vec3> FluidSimulation::getMarkerParticlePositions(int startidx, int endidx) {
    int size = _markerParticles.size();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<vmath::vec3> particles;
    particles.reserve(endidx - startidx);

    for (int i = startidx; i < endidx; i++) {
        particles.push_back(_markerParticles[i].position);
    }

    return particles;
}

std::vector<vmath::vec3> FluidSimulation::getMarkerParticleVelocities() {
    return getMarkerParticleVelocities(0, _markerParticles.size());
}

std::vector<vmath::vec3> FluidSimulation::getMarkerParticleVelocities(int startidx, int endidx) {
    int size = _markerParticles.size();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<vmath::vec3> velocities;
    velocities.reserve(endidx - startidx);

    for (int i = startidx; i < endidx; i++) {
        velocities.push_back(_markerParticles[i].velocity);
    }

    return velocities;
}

unsigned int FluidSimulation::getNumDiffuseParticles() {
    return _diffuseMaterial.getNumDiffuseParticles();
}

std::vector<DiffuseParticle> FluidSimulation::getDiffuseParticles() {
    return getDiffuseParticles(0, _markerParticles.size());
}

std::vector<DiffuseParticle> FluidSimulation::getDiffuseParticles(int startidx, int endidx) {
    int size = getNumDiffuseParticles();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<DiffuseParticle> particles;
    particles.reserve(endidx - startidx);

    FragmentedVector<DiffuseParticle> *dps = _diffuseMaterial.getDiffuseParticles();
    for (int i = startidx; i < endidx; i++) {
        particles.push_back(dps->at(i));
    }

    return particles;
}

std::vector<vmath::vec3> FluidSimulation::getDiffuseParticlePositions() {
    int size = getNumDiffuseParticles();
    return getDiffuseParticlePositions(0, size);
}

std::vector<vmath::vec3> FluidSimulation::getDiffuseParticlePositions(int startidx, int endidx) {
    int size = getNumDiffuseParticles();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<vmath::vec3> particles;
    particles.reserve(endidx - startidx);

    FragmentedVector<DiffuseParticle> *dps = _diffuseMaterial.getDiffuseParticles();
    for (int i = startidx; i < endidx; i++) {
        particles.push_back(dps->at(i).position);
    }

    return particles;
}

std::vector<vmath::vec3> FluidSimulation::getDiffuseParticleVelocities() {
    int size = getNumDiffuseParticles();
    return getDiffuseParticleVelocities(0, size);
}

std::vector<vmath::vec3> FluidSimulation::getDiffuseParticleVelocities(int startidx, int endidx) {
    int size = getNumDiffuseParticles();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<vmath::vec3> velocities;
    velocities.reserve(endidx - startidx);

    FragmentedVector<DiffuseParticle> *dps = _diffuseMaterial.getDiffuseParticles();
    for (int i = startidx; i < endidx; i++) {
        velocities.push_back(dps->at(i).velocity);
    }

    return velocities;
}

std::vector<float> FluidSimulation::getDiffuseParticleLifetimes() {
    int size = getNumDiffuseParticles();
    return getDiffuseParticleLifetimes(0, size);
}

std::vector<float> FluidSimulation::getDiffuseParticleLifetimes(int startidx, int endidx) {
    int size = getNumDiffuseParticles();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<float> lifetimes;
    lifetimes.reserve(endidx - startidx);

    FragmentedVector<DiffuseParticle> *dps = _diffuseMaterial.getDiffuseParticles();
    for (int i = startidx; i < endidx; i++) {
        lifetimes.push_back(dps->at(i).lifetime);
    }

    return lifetimes;
}

std::vector<char> FluidSimulation::getDiffuseParticleTypes() {
    int size = getNumDiffuseParticles();
    return getDiffuseParticleTypes(0, size);
}

std::vector<char> FluidSimulation::getDiffuseParticleTypes(int startidx, int endidx) {
    int size = getNumDiffuseParticles();
    if (!(startidx >= 0 && startidx <= size) || !(endidx >= 0 && endidx <= size)) {
        std::string msg = "Error: invalid index range.\n";
        msg += "start index: " + _toString(startidx) + " end index: " + _toString(endidx) + "\n";
        throw std::out_of_range(msg);
    }

    std::vector<char> types;
    types.reserve(endidx - startidx);

    FragmentedVector<DiffuseParticle> *dps = _diffuseMaterial.getDiffuseParticles();
    for (int i = startidx; i < endidx; i++) {
        types.push_back((char)(dps->at(i).type));
    }

    return types;
}

MACVelocityField* FluidSimulation::getVelocityField() { 
    return &_MACVelocity; 
}

std::vector<char>* FluidSimulation::getSurfaceData() {
    return &_outputData.surfaceData;
}

std::vector<char>* FluidSimulation::getSurfaceBlurData() {
    return &_outputData.surfaceBlurData;
}

std::vector<char>* FluidSimulation::getSurfacePreviewData() {
    return &_outputData.surfacePreviewData;
}

std::vector<char>* FluidSimulation::getDiffuseData() {
    return &_outputData.diffuseData;
}

std::vector<char>* FluidSimulation::getDiffuseFoamData() {
    return &_outputData.diffuseFoamData;
}

std::vector<char>* FluidSimulation::getDiffuseBubbleData() {
    return &_outputData.diffuseBubbleData;
}

std::vector<char>* FluidSimulation::getDiffuseSprayData() {
    return &_outputData.diffuseSprayData;
}

std::vector<char>* FluidSimulation::getDiffuseFoamBlurData() {
    return &_outputData.diffuseFoamBlurData;
}

std::vector<char>* FluidSimulation::getDiffuseBubbleBlurData() {
    return &_outputData.diffuseBubbleBlurData;
}

std::vector<char>* FluidSimulation::getDiffuseSprayBlurData() {
    return &_outputData.diffuseSprayBlurData;
}

std::vector<char>* FluidSimulation::getFluidParticleData() {
    return &_outputData.fluidParticleData;
}

std::vector<char>* FluidSimulation::getInternalObstacleMeshData() {
    return &_outputData.internalObstacleMeshData;
}

std::vector<char>* FluidSimulation::getLogFileData() {
    return &_outputData.logfileData;
}

FluidSimulationFrameStats FluidSimulation::getFrameStatsData() {
    return _outputData.frameData;
}

void FluidSimulation::getMarkerParticlePositionData(char *data) {
    vmath::vec3 *positions = (vmath::vec3*)data;
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        positions[i] = _markerParticles[i].position * _domainScale + _domainOffset;
    }
}

void FluidSimulation::getMarkerParticleVelocityData(char *data) {
    vmath::vec3 *velocities = (vmath::vec3*)data;
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        velocities[i] = _markerParticles[i].velocity;
    }
}

void FluidSimulation::getDiffuseParticlePositionData(char *data) {
    FragmentedVector<DiffuseParticle>* dps = _diffuseMaterial.getDiffuseParticles();
    vmath::vec3 *positions = (vmath::vec3*)data;
    for (size_t i = 0; i < dps->size(); i++) {
        positions[i] = dps->at(i).position * _domainScale + _domainOffset;
    }
}

void FluidSimulation::getDiffuseParticleVelocityData(char *data) {
    FragmentedVector<DiffuseParticle>* dps = _diffuseMaterial.getDiffuseParticles();
    vmath::vec3 *velocities = (vmath::vec3*)data;
    for (size_t i = 0; i < dps->size(); i++) {
        velocities[i] = dps->at(i).velocity;
    }
}

void FluidSimulation::getDiffuseParticleLifetimeData(char *data) {
    FragmentedVector<DiffuseParticle>* dps = _diffuseMaterial.getDiffuseParticles();
    float *lifetimes = (float*)data;
    for (size_t i = 0; i < dps->size(); i++) {
        lifetimes[i] = dps->at(i).lifetime;
    }
}

void FluidSimulation::getDiffuseParticleTypeData(char *data) {
    FragmentedVector<DiffuseParticle>* dps = _diffuseMaterial.getDiffuseParticles();
    for (size_t i = 0; i < dps->size(); i++) {
        data[i] = (char)(dps->at(i).type);
    }
}

void FluidSimulation::getDiffuseParticleIdData(char *data) {
    FragmentedVector<DiffuseParticle>* dps = _diffuseMaterial.getDiffuseParticles();
    for (size_t i = 0; i < dps->size(); i++) {
        data[i] = (char)(dps->at(i).id);
    }
}

unsigned int FluidSimulation::getMarkerParticlePositionDataSize() {
    return (unsigned int)(getNumMarkerParticles() * sizeof(vmath::vec3));
}

unsigned int FluidSimulation::getMarkerParticleVelocityDataSize() {
    return getMarkerParticlePositionDataSize();
}

unsigned int FluidSimulation::getDiffuseParticlePositionDataSize() {
    return (unsigned int)(getNumDiffuseParticles() * sizeof(vmath::vec3));
}

unsigned int FluidSimulation::getDiffuseParticleVelocityDataSize() {
    return getDiffuseParticlePositionDataSize();
}

unsigned int FluidSimulation::getDiffuseParticleLifetimeDataSize() {
    return (unsigned int)(getNumDiffuseParticles() * sizeof(float));
}

unsigned int FluidSimulation::getDiffuseParticleTypeDataSize() {
    return (unsigned int)(getNumDiffuseParticles() * sizeof(char));
}

unsigned int FluidSimulation::getDiffuseParticleIdDataSize() {
    return (unsigned int)(getNumDiffuseParticles() * sizeof(char));
}

void FluidSimulation::loadMarkerParticleData(FluidSimulationMarkerParticleData data) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " loadMarkerParticleData: " << data.size << std::endl);

    if (data.size == 0) {
        return;
    }

    vmath::vec3 *positions = (vmath::vec3*)(data.positions);
    vmath::vec3 *velocities = (vmath::vec3*)(data.velocities);

    MarkerParticleLoadData loadData;
    loadData.particles.reserve(data.size);

    for (unsigned int i = 0; i < (unsigned int)data.size; i++) {
        loadData.particles.push_back(MarkerParticle(positions[i], velocities[i]));
    }

    _markerParticleLoadQueue.push_back(loadData);

    _isMarkerParticleLoadPending = true;
}

void FluidSimulation::loadDiffuseParticleData(FluidSimulationDiffuseParticleData data) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " loadDiffuseParticleData: " << data.size << std::endl);

    if (data.size == 0) {
        return;
    }

    vmath::vec3 *positions = (vmath::vec3*)(data.positions);
    vmath::vec3 *velocities = (vmath::vec3*)(data.velocities);
    float *lifetimes = (float*)(data.lifetimes);
    DiffuseParticleType *types = (DiffuseParticleType*)(data.types);
    unsigned char *ids = (unsigned char*)(data.ids);

    DiffuseParticleLoadData loadData;
    loadData.particles.reserve(data.size);

    for (unsigned int i = 0; i < (unsigned int)data.size; i++) {
        DiffuseParticle dp;
        dp.position = positions[i];
        dp.velocity = velocities[i];
        dp.lifetime = lifetimes[i];
        dp.type = types[i];
        dp.id = ids[i];
        loadData.particles.push_back(dp);
    }

    _diffuseParticleLoadQueue.push_back(loadData);

    _isDiffuseParticleLoadPending = true;
}


/********************************************************************************
    Initializing the Fluid Simulator
********************************************************************************/

void FluidSimulation::_initializeSimulationGrids(int isize, int jsize, int ksize, double dx) {
    _logfile.separator();
    _logfile.timestamp();
    _logfile.newline();
    _logfile.log(std::ostringstream().flush() << 
                 "Initializing Simulation Grids:" << std::endl <<
                 "\tGrid Dimensions: " << isize << " x " << 
                                        jsize << " x " << 
                                        ksize << std::endl <<
                 "\tCell Size:       " << dx << std::endl);

    StopWatch t;
    t.start();
    _MACVelocity = MACVelocityField(isize, jsize, ksize, dx);
    _validVelocities = ValidVelocityComponentGrid(_isize, _jsize, _ksize);
    t.stop();

    _logfile.log("Constructing MACVelocityField: \t", t.getTime(), 4, 1);

    t.reset();
    t.start();
    _solidSDF = MeshLevelSet(isize, jsize, ksize, dx);
    if (_isStaticSolidLevelSetPrecomputed) {
        _staticSolidSDF = MeshLevelSet(isize, jsize, ksize, dx);
    }
    if (_isTempSolidLevelSetEnabled) {
        _tempSolidSDF = MeshLevelSet(isize, jsize, ksize, dx);
    }
    if (_isMeshingVolumeSet) {
        _meshingVolumeSDF = MeshLevelSet(isize, jsize, ksize, dx);
    }
    _liquidSDF = ParticleLevelSet(isize, jsize, ksize, dx);

    TriangleMesh domainBoundaryMesh = _getBoundaryTriangleMesh();
    _domainMeshObject = MeshObject(isize, jsize, ksize, dx);
    _domainMeshObject.updateMeshStatic(domainBoundaryMesh);
    _domainMeshObject.setFriction(_domainBoundaryFriction);
    t.stop();

    _logfile.log("Constructing Level Sets:       \t", t.getTime(), 4, 1);

    t.reset();
    t.start();
    _weightGrid = WeightGrid(_isize, _jsize, _ksize);
    t.stop();

    _logfile.log("Constructing Weight Grid:      \t", t.getTime(), 4, 1);
}

double FluidSimulation::_getMarkerParticleJitter() {
    double eps = 1e-3;
    return 0.25 * (_markerParticleJitterFactor - eps) * _dx;
}

vmath::vec3 FluidSimulation::_jitterMarkerParticlePosition(vmath::vec3 p, 
                                                           double jitter) {
    p.x += _randomDouble(-jitter, jitter);
    p.y += _randomDouble(-jitter, jitter);
    p.z += _randomDouble(-jitter, jitter);

    return p;
}

void FluidSimulation::_addMarkerParticle(vmath::vec3 p, vmath::vec3 velocity) {
    GridIndex g = Grid3d::positionToGridIndex(p, _dx);
    if (Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize)) {
        _markerParticles.push_back(MarkerParticle(p, velocity));
    }
}

void FluidSimulation::_initializeParticleRadii() {
    double volume = _dx*_dx*_dx / 8.0;
    double pi = 3.141592653;
    _markerParticleRadius = pow(3*volume / (4*pi), 1.0/3.0);

    _liquidSDFParticleRadius = 0.5 * _liquidSDFParticleScale * _dx * sqrt(3.0); 
}

void FluidSimulation::_initializeSimulation() {
    _logfile.newline();
    _logfile.log(std::ostringstream().flush() << 
                 "Initializing Simulation:" << std::endl);

    _initializeSimulationGrids(_isize, _jsize, _ksize, _dx);

    _initializeParticleRadii();

    if (_isMarkerParticleLoadPending || _isDiffuseParticleLoadPending) {
        StopWatch loadTimer;
        loadTimer.start();
        _loadParticles();
        loadTimer.stop();
        _logfile.log("Loading Particle Data:       \t", loadTimer.getTime(), 4, 1);
    }

    _isSimulationInitialized = true;
}

void FluidSimulation::_loadMarkerParticles(MarkerParticleLoadData &data) {

    _markerParticles.reserve(_markerParticles.size() + data.particles.size());

    AABB bounds(0.0, 0.0, 0.0, _isize * _dx, _jsize * _dx, _ksize * _dx);
    for (size_t i = 0; i < data.particles.size(); i++) {
        MarkerParticle mp = data.particles[i];
        mp.position = (mp.position - _domainOffset) / _domainScale;
        if (bounds.isPointInside(mp.position)) {
            _markerParticles.push_back(mp);
        }
    }
}

void FluidSimulation::_loadDiffuseParticles(DiffuseParticleLoadData &data) {
    _diffuseMaterial.loadDiffuseParticles(data.particles);
}

void FluidSimulation::_loadParticles() {
    for (size_t i = 0; i < _markerParticleLoadQueue.size(); i++) {
        _loadMarkerParticles(_markerParticleLoadQueue[i]);
    }
    _markerParticleLoadQueue.clear();
    _isMarkerParticleLoadPending = false;
    
    for (size_t i = 0; i < _diffuseParticleLoadQueue.size(); i++) {
        _loadDiffuseParticles(_diffuseParticleLoadQueue[i]);
    }
    _diffuseParticleLoadQueue.clear();
    _isDiffuseParticleLoadPending = false;
}

/********************************************************************************
    #. Update Solid Material
********************************************************************************/
TriangleMesh FluidSimulation::_getTriangleMeshFromAABB(AABB bbox) {
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

AABB FluidSimulation::_getBoundaryAABB() {
    double eps = 1e-4;
    AABB domainAABB(0.0, 0.0, 0.0, _isize * _dx, _jsize * _dx, _ksize * _dx);
    domainAABB.expand(-3 * _dx - eps);
    return domainAABB;
}

TriangleMesh FluidSimulation::_getBoundaryTriangleMesh() {
    AABB boundaryAABB = _getBoundaryAABB();
    TriangleMesh boundaryMesh = _getTriangleMeshFromAABB(boundaryAABB);
    return boundaryMesh;
}

void FluidSimulation::_updatePrecomputedSolidLevelSet(double dt, 
                                                      std::vector<MeshObjectStatus> &objectStatus) {

    if (!_isStaticSolidLevelSetPrecomputed) {
        int pi, pj, pk;
        _staticSolidSDF.getGridDimensions(&pi, &pj, &pk);
        if (pi > 0 || pj  > 0 || pk > 0) {
            _staticSolidSDF = MeshLevelSet();
        }
        return;
    }

    if (_isStaticSolidStateChanged(objectStatus)) {
        _isPrecomputedSolidLevelSetUpToDate = false;
    }

    if (_isPrecomputedSolidLevelSetUpToDate) {
        return;
    }

    int pi, pj, pk;
    _staticSolidSDF.getGridDimensions(&pi, &pj, &pk);
    if (pi != _isize || pj != _jsize || pk != _ksize) {
        _staticSolidSDF = MeshLevelSet(_isize, _jsize, _ksize, _dx);
    }

    _addStaticObjectsToSDF(dt, _staticSolidSDF);

    _isPrecomputedSolidLevelSetUpToDate = true;
}

void FluidSimulation::_addAnimatedObjectsToSolidSDF(double dt) {
    std::vector<MeshObject*> inversedObstacles;
    std::vector<MeshObject*> normalObstacles;
    for (size_t i = 0; i < _obstacles.size(); i++) {
        if (_obstacles[i]->isEnabled() && _obstacles[i]->isAnimated()) {
            if (_obstacles[i]->isInversed()) {
                inversedObstacles.push_back(_obstacles[i]);
            } else {
                normalObstacles.push_back(_obstacles[i]);
            }
        }
    }

    float frameTime = (float)(_currentFrameDeltaTimeRemaining + _currentFrameTimeStep);
    float frameProgress = 1.0f - frameTime / (float)_currentFrameDeltaTime;

    if (!_isTempSolidLevelSetEnabled && (!normalObstacles.empty() || !inversedObstacles.empty())) {
        _tempSolidSDF = MeshLevelSet(_isize, _jsize, _ksize, _dx);
    }

    for (size_t i = 0; i < normalObstacles.size(); i++) {
        _tempSolidSDF.reset();
        normalObstacles[i]->getMeshLevelSet(dt, frameProgress, _solidLevelSetExactBand, _tempSolidSDF);
        _solidSDF.calculateUnion(_tempSolidSDF);
    }

    if (!inversedObstacles.empty()) {
        MeshLevelSet tempSolidInversedSDF(_isize, _jsize, _ksize, _dx);
        tempSolidInversedSDF.disableVelocityData();

        for (size_t i = 0; i < inversedObstacles.size(); i++) {
            _tempSolidSDF.reset();
            _tempSolidSDF.disableVelocityData();
            inversedObstacles[i]->getMeshLevelSet(dt, frameProgress, _solidLevelSetExactBand, _tempSolidSDF);
            tempSolidInversedSDF.calculateUnion(_tempSolidSDF);
        }

        tempSolidInversedSDF.enableVelocityData();
        tempSolidInversedSDF.negate();
        _solidSDF.calculateUnion(tempSolidInversedSDF);
    }

    if (!_isTempSolidLevelSetEnabled) {
        _tempSolidSDF = MeshLevelSet();
    }
}

void FluidSimulation::_addStaticObjectsToSDF(double dt, MeshLevelSet &sdf){
    TriangleMesh boundaryMesh = _domainMeshObject.getMesh();
    sdf.reset();
    sdf.pushMeshObject(&_domainMeshObject);
    sdf.disableVelocityData();    // Stops velocity data from being calculated 
                                  // twice (once during sdf calculations, and
                                  // once when sdf is negated
    sdf.fastCalculateSignedDistanceField(boundaryMesh, _solidLevelSetExactBand);
    sdf.enableVelocityData();
    sdf.negate();

    std::vector<MeshObject*> inversedObstacles;
    std::vector<MeshObject*> normalObstacles;
    for (size_t i = 0; i < _obstacles.size(); i++) {
        if (_obstacles[i]->isEnabled() && !_obstacles[i]->isAnimated()) {
            if (_obstacles[i]->isInversed()) {
                inversedObstacles.push_back(_obstacles[i]);
            } else {
                normalObstacles.push_back(_obstacles[i]);
            }
        }
    }

    float frameTime = (float)(_currentFrameDeltaTimeRemaining + _currentFrameTimeStep);
    float frameProgress = 1.0f - frameTime / (float)_currentFrameDeltaTime;

    if (!_isTempSolidLevelSetEnabled && (!normalObstacles.empty() || !inversedObstacles.empty())) {
        _tempSolidSDF = MeshLevelSet(_isize, _jsize, _ksize, _dx);
    }

    for (size_t i = 0; i < normalObstacles.size(); i++) {
        _tempSolidSDF.reset();
        normalObstacles[i]->getMeshLevelSet(dt, frameProgress, _solidLevelSetExactBand, _tempSolidSDF);
        sdf.calculateUnion(_tempSolidSDF);
    }

    if (!inversedObstacles.empty()) {
        MeshLevelSet tempSolidInversedSDF(_isize, _jsize, _ksize, _dx);
        tempSolidInversedSDF.disableVelocityData();

        for (size_t i = 0; i < inversedObstacles.size(); i++) {
            _tempSolidSDF.reset();
            _tempSolidSDF.disableVelocityData();
            inversedObstacles[i]->getMeshLevelSet(dt, frameProgress, _solidLevelSetExactBand, _tempSolidSDF);
            tempSolidInversedSDF.calculateUnion(_tempSolidSDF);
        }

        tempSolidInversedSDF.enableVelocityData();
        tempSolidInversedSDF.negate();
        sdf.calculateUnion(tempSolidInversedSDF);
    }
}

void FluidSimulation::_addStaticObjectsToSolidSDF(double dt, std::vector<MeshObjectStatus> &objectStatus) {
    StopWatch t;
    t.start();

    _updatePrecomputedSolidLevelSet(dt, objectStatus);

    if (_isStaticSolidLevelSetPrecomputed) {
        if (_isPrecomputedSolidLevelSetUpToDate) {
            _solidSDF.calculateUnion(_staticSolidSDF);
        }

        return;
    }

    _addStaticObjectsToSDF(dt, _solidSDF);
}

bool FluidSimulation::_isSolidStateChanged(std::vector<MeshObjectStatus> &objectStatus) {
    for (size_t i = 0; i < objectStatus.size(); i++) {
        MeshObjectStatus s = objectStatus[i];
        if (s.isStateChanged || (s.isEnabled && s.isAnimated && s.isMeshChanged)) {
            return true;
        }
    }
    return false;
}

bool FluidSimulation::_isStaticSolidStateChanged(std::vector<MeshObjectStatus> &objectStatus) {
    for (size_t i = 0; i < objectStatus.size(); i++) {
        MeshObjectStatus s = objectStatus[i];
        if (!s.isAnimated && s.isStateChanged) {
            return true;
        }
    }
    return false;
}

std::vector<MeshObjectStatus> FluidSimulation::_getSolidObjectStatus() {
    std::vector<MeshObjectStatus> objectData;
    for (size_t i = 0; i < _obstacles.size(); i++) {
        objectData.push_back(_obstacles[i]->getStatus());
        _obstacles[i]->clearObjectStatus();
    }
    return objectData;
}

void FluidSimulation::_updateSolidLevelSet(double dt) {
    std::vector<MeshObjectStatus> objectStatus = _getSolidObjectStatus();
    if (_isSolidStateChanged(objectStatus)) {
        _isSolidLevelSetUpToDate = false;
    }

    if (_isSolidLevelSetUpToDate) {
        return;
    }

    if (_markerParticles.empty() && 
            _addedFluidMeshObjectQueue.empty() && 
            _meshFluidSources.empty() && 
            !_isInternalObstacleMeshOutputEnabled) {
        return;
    }

    _solidSDF.reset();

    StopWatch t;
    t.start();

    int pi, pj, pk;
    _tempSolidSDF.getGridDimensions(&pi, &pj, &pk);
    if (_isTempSolidLevelSetEnabled) {
        if (pi != _isize || pj != _jsize || pk != _ksize) {
            _tempSolidSDF = MeshLevelSet(_isize, _jsize, _ksize, _dx);
        }
    } else {
        if (pi > 0 || pj  > 0 || pk > 0) {
            _tempSolidSDF = MeshLevelSet();
        }
    }

    _addStaticObjectsToSolidSDF(dt, objectStatus);
    _addAnimatedObjectsToSolidSDF(dt);

    _solidSDF.normalizeVelocityGrid();

    _resolveSolidLevelSetUpdateCollisions();

    _isSolidLevelSetUpToDate = true;
    _isWeightGridUpToDate = false;

}

void FluidSimulation::_updateObstacles(double) {
    // Currently, nothing needs to be updated
    /*
    for (size_t i = 0; i < _obstacles.size(); i++) {
        
    }
    */
}

void FluidSimulation::_initializeNearSolidGridThread(int startidx, int endidx) {
    float maxd = _solidLevelSetExactBand * _dx;
    int gridfactor = _nearSolidGridCellSizeFactor;
    for (int idx = startidx; idx < endidx; idx++) {
        GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
        if (std::abs(_solidSDF(g)) < maxd) {
            _nearSolidGrid.set(g.i / gridfactor, g.j / gridfactor, g.k / gridfactor, true);
        }
    }
}

void FluidSimulation::_updateNearSolidGrid() {
    _nearSolidGridCellSize = _nearSolidGridCellSizeFactor * _dx;
    int gridi = (int)std::ceil(getSimulationWidth() / _nearSolidGridCellSize);
    int gridj = (int)std::ceil(getSimulationHeight() / _nearSolidGridCellSize);
    int gridk = (int)std::ceil(getSimulationDepth() / _nearSolidGridCellSize);

    if (_nearSolidGrid.width != gridi || 
            _nearSolidGrid.height != gridj ||
            _nearSolidGrid.depth != gridk) {
        _nearSolidGrid = Array3d<bool>(gridi, gridj, gridk, false);
    } else {
        _nearSolidGrid.fill(false);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int gridsize = _isize * _jsize * _ksize;
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_initializeNearSolidGridThread, this,
                                 intervals[i], intervals[i + 1]);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    int numlayers = (int)std::ceil((float)_CFLConditionNumber / (float)_nearSolidGridCellSizeFactor);
    for (int i = 0; i < numlayers; i++) {
        GridUtils::featherGrid6(&_nearSolidGrid, ThreadUtils::getMaxThreadCount());
    }
}

void FluidSimulation::_resolveSolidLevelSetUpdateCollisionsThread(int startidx, int endidx) {
    /*
    AABB boundary = _getBoundaryAABB();
    float maxResolvedDistance = _CFLConditionNumber * _dx;
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 p = _markerParticles[i].position;

        GridIndex n = Grid3d::positionToGridIndex(p, _nearSolidGridCellSize);
        if (!_nearSolidGrid(n)) {
            continue;
        }

        float phi = _solidSDF.trilinearInterpolate(p);
        if (phi >= 0.0f) {
            continue;
        }

        float eps = 1e-5;
        vmath::vec3 grad = _solidSDF.trilinearInterpolateGradient(p);
        if (vmath::length(grad) < eps) {
            continue;
        }

        grad = vmath::normalize(grad);
        vmath::vec3 resolvedPosition = p - (phi - _solidBufferWidth * _dx) * grad;
        float resolvedPhi = _solidSDF.trilinearInterpolate(resolvedPosition);
        float resolvedDistance = vmath::length(resolvedPosition - p);
        if (resolvedPhi < 0 || resolvedDistance > maxResolvedDistance) {
            continue;
        }

        if (!boundary.isPointInside(resolvedPosition)) {
            continue;
        }

        _markerParticles[i].position = resolvedPosition;
    }
    */
}

void FluidSimulation::_resolveSolidLevelSetUpdateCollisions() {
    _nearSolidGridCellSize = _nearSolidGridCellSizeFactor * _dx;
    int gridi = (int)std::ceil(getSimulationWidth() / _nearSolidGridCellSize);
    int gridj = (int)std::ceil(getSimulationHeight() / _nearSolidGridCellSize);
    int gridk = (int)std::ceil(getSimulationDepth() / _nearSolidGridCellSize);

    if (_nearSolidGrid.width != gridi || 
            _nearSolidGrid.height != gridj ||
            _nearSolidGrid.depth != gridk) {
        _nearSolidGrid = Array3d<bool>(gridi, gridj, gridk, false);
    } else {
        _nearSolidGrid.fill(false);
    }
    
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _markerParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _markerParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_resolveSolidLevelSetUpdateCollisionsThread, this,
                                 intervals[i], intervals[i + 1]);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void FluidSimulation::_updateObstacleObjects(double) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Update Obstacle Objects");

    StopWatch t;
    t.start();
    _updateObstacles(_currentFrameDeltaTime);
    _updateSolidLevelSet(_currentFrameDeltaTime);
    _updateNearSolidGrid();
    _updateMeshingVolumeSDF();
    t.stop();

    _timingData.updateObstacleObjects += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Obstacle Objects");
}

void FluidSimulation::_launchUpdateObstacleObjectsThread(double dt) {
    _updateObstacleObjectsThread = std::thread(&FluidSimulation::_updateObstacleObjects, 
                                               this, dt);
}
    
void FluidSimulation::_joinUpdateObstacleObjectsThread() {
    _updateObstacleObjectsThread.join();
}

/********************************************************************************
    #. Update Fluid Material
********************************************************************************/

void FluidSimulation::_updateLiquidLevelSet() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Update Liquid Level Set");

    StopWatch t;
    t.start();

    _liquidSDF.calculateSignedDistanceField(_markerParticles, _liquidSDFParticleRadius);

    t.stop();

    _timingData.updateLiquidLevelSet += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Liquid Level Set");
}

void FluidSimulation::_launchUpdateLiquidLevelSetThread() {
    _updateLiquidLevelSetThread = std::thread(&FluidSimulation::_updateLiquidLevelSet, this);
}

void FluidSimulation::_joinUpdateLiquidLevelSetThread() {
    _updateLiquidLevelSetThread.join();
    _liquidSDF.postProcessSignedDistanceField(_solidSDF);
}

/********************************************************************************
    #.  Advect Velocity Field
********************************************************************************/

void FluidSimulation::_advectVelocityField() {
_logfile.logString(_logfile.getTime() + " BEGIN       Advect Velocity Field");

    StopWatch t;
    t.start();

    _validVelocities.reset();
    _MACVelocity.clear();
    if (!_markerParticles.empty()) {
        VelocityAdvectorParameters params;
        params.particles = &_markerParticles;
        params.vfield = &_MACVelocity;
        params.validVelocities = &_validVelocities;
        params.particleRadius = _liquidSDFParticleRadius;
        
        _velocityAdvector.advect(params);

        _extrapolateFluidVelocities(_MACVelocity, _validVelocities);
    }

    t.stop();
    _timingData.advectVelocityField += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Advect Velocity Field");
}

void FluidSimulation::_launchAdvectVelocityFieldThread() {
    _advectVelocityFieldThread = std::thread(&FluidSimulation::_advectVelocityField, this);
}

void FluidSimulation::_joinAdvectVelocityFieldThread() {
    _advectVelocityFieldThread.join();
}

void FluidSimulation::_saveVelocityField() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Save Velocity Field");

    StopWatch t;
    t.start();
    _savedVelocityField = _MACVelocity;
    t.stop();
    _timingData.saveVelocityField += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Save Velocity Field");
}

void FluidSimulation::_deleteSavedVelocityField() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Delete Saved Velocity Field");

    StopWatch t;
    t.start();
    _savedVelocityField = MACVelocityField();
    t.stop();
    _timingData.deleteSavedVelocityField += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Delete Saved Velocity Field");
}


/********************************************************************************
    #.  Calculate Fluid Curvature
********************************************************************************/

void FluidSimulation::_calculateFluidCurvatureGridThread() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Calculate Surface Curvature");

    StopWatch t;
    t.start();

    if (_fluidCurvatureGrid.width == _isize && 
            _fluidCurvatureGrid.height == _jsize && 
            _fluidCurvatureGrid.depth == _ksize) {
        _fluidSurfaceLevelSet.fill(0.0f);
        _fluidCurvatureGrid.fill(0.0f);
    } else {
        _fluidSurfaceLevelSet = Array3d<float>(_isize, _jsize, _ksize, 0.0f);
        _fluidCurvatureGrid = Array3d<float>(_isize, _jsize, _ksize, 0.0f);
    }

    _liquidSDF.calculateCurvatureGrid(_fluidSurfaceLevelSet, _fluidCurvatureGrid);

    t.stop();
    _timingData.calculateFluidCurvatureGrid += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Calculate Surface Curvature");
}

void FluidSimulation::_launchCalculateFluidCurvatureGridThread() {
    if (!_isSurfaceTensionEnabled && !_isSheetSeedingEnabled && !_isDiffuseMaterialOutputEnabled) {
        return;
    }

    _fluidCurvatureThread = std::thread(&FluidSimulation::_calculateFluidCurvatureGridThread, 
                                        this);
    _isCalculateFluidCurvatureGridThreadRunning = true;
}

void FluidSimulation::_joinCalculateFluidCurvatureGridThread() {
    if (!_isCalculateFluidCurvatureGridThreadRunning) {
        return;
    }

    _fluidCurvatureThread.join();
    _isCalculateFluidCurvatureGridThreadRunning = false;
}

/********************************************************************************
    #. Apply Body Forces
********************************************************************************/

vmath::vec3 FluidSimulation::_getConstantBodyForce() {
    vmath::vec3 bf;
    for (unsigned int i = 0; i < _constantBodyForces.size(); i++) {
        bf += _constantBodyForces[i];
    }

    return bf;
}

void FluidSimulation::_getInflowConstrainedVelocityComponents(ValidVelocityComponentGrid &ex) {
    for (size_t sidx = 0; sidx < _meshFluidSources.size(); sidx++) {
        MeshFluidSource *inflow = _meshFluidSources[sidx];
        if (!inflow->isEnabled() || !inflow->isInflow() || 
                !inflow->isConstrainedFluidVelocityEnabled()) {
            continue;
        }

        float frameTime = (float)(_currentFrameDeltaTimeRemaining + _currentFrameTimeStep);
        float frameProgress = 1.0f - frameTime / (float)_currentFrameDeltaTime;
        int numSubsteps = inflow->getSubstepEmissions();

        if (numSubsteps == 0) {
            numSubsteps = 1;
        }

        float substepFactor = (_currentFrameTimeStep / _currentFrameDeltaTime) / (float)numSubsteps;

        for (int subidx = 0; subidx < numSubsteps; subidx++) {
            float frameInterpolation = frameProgress + (float)subidx * substepFactor;
            inflow->setFrame(_currentFrame, frameInterpolation);
            inflow->update(_currentFrameDeltaTime);
            MeshLevelSet *inflowSDF = inflow->getMeshLevelSet();
            
            for (int k = 0; k < _ksize; k++) {
                for (int j = 0; j < _jsize; j++) {
                    for (int i = 0; i < _isize + 1; i++) {
                        if (!_validVelocities.validU(i, j, k)) {
                            continue;
                        }
                        vmath::vec3 p = Grid3d::FaceIndexToPositionU(i, j, k, _dx);
                        if (inflowSDF->trilinearInterpolate(p) < 0.0f) {
                            ex.validU.set(i, j, k, true);
                        }
                    }
                }
            }

            for (int k = 0; k < _ksize; k++) {
                for (int j = 0; j < _jsize + 1; j++) {
                    for (int i = 0; i < _isize; i++) {
                        if (!_validVelocities.validV(i, j, k)) {
                            continue;
                        }
                        vmath::vec3 p = Grid3d::FaceIndexToPositionV(i, j, k, _dx);
                        if (inflowSDF->trilinearInterpolate(p) < 0.0f) {
                            ex.validV.set(i, j, k, true);
                        }
                    }
                }
            }

            for (int k = 0; k < _ksize + 1; k++) {
                for (int j = 0; j < _jsize; j++) {
                    for (int i = 0; i < _isize; i++) {
                        if (!_validVelocities.validW(i, j, k)) {
                            continue;
                        }
                        vmath::vec3 p = Grid3d::FaceIndexToPositionW(i, j, k, _dx);
                        if (inflowSDF->trilinearInterpolate(p) < 0.0f) {
                            ex.validW.set(i, j, k, true);
                        }
                    }
                }
            }
        }
    }
}

void FluidSimulation::_applyConstantBodyForces(ValidVelocityComponentGrid &ex, double dt) {
    vmath::vec3 bodyForce = _getConstantBodyForce();
    float eps = 1e-6;

    if (fabs(bodyForce.x) > eps) {
        for (int k = 0; k < _ksize; k++) {
            for (int j = 0; j < _jsize; j++) {
                for (int i = 0; i < _isize + 1; i++) {
                    if (!ex.validU(i, j, k)) {
                        _MACVelocity.addU(i, j, k, bodyForce.x * dt);
                    }
                }
            }
        }
    }

    if (fabs(bodyForce.y) > eps) {
        for (int k = 0; k < _ksize; k++) {
            for (int j = 0; j < _jsize + 1; j++) {
                for (int i = 0; i < _isize; i++) {
                    if (!ex.validV(i, j, k)) {
                        _MACVelocity.addV(i, j, k, bodyForce.y * dt);
                    }
                }
            }
        }
    }

    if (fabs(bodyForce.z) > eps) {
        for (int k = 0; k < _ksize + 1; k++) {
            for (int j = 0; j < _jsize; j++) {
                for (int i = 0; i < _isize; i++) {
                    if (!ex.validW(i, j, k)) {
                        _MACVelocity.addW(i, j, k, bodyForce.z * dt);
                    }
                }
            }
        }
    }
}

void FluidSimulation::_applyBodyForcesToVelocityField(double dt) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Apply Body Forces");

    StopWatch t;
    t.start();
    ValidVelocityComponentGrid ex(_isize, _jsize, _ksize);
    _getInflowConstrainedVelocityComponents(ex);
    _applyConstantBodyForces(ex, dt);
    t.stop();
    _timingData.applyBodyForcesToVelocityField += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Apply Body Forces");
}

/********************************************************************************
    #. Viscosity Solve
********************************************************************************/

void FluidSimulation::_applyViscosityToVelocityField(double dt) {
    _viscositySolverStatus = "";

    if (!_isViscosityEnabled || _markerParticles.empty()) {
        return;
    }

    bool isViscosityNonZero = false;
    for (int k = 0; k < _viscosity.depth; k++) {
        for (int j = 0; j < _viscosity.height; j++) {
            for (int i = 0; i < _viscosity.width; i++) {
                if (_viscosity(i, j, k) > 0.0) {
                    isViscosityNonZero = true;
                    break;
                }
            }
            if (isViscosityNonZero) { break; }
        }
        if (isViscosityNonZero) { break; }
    }

    if (!isViscosityNonZero) {
        return;
    }

    _logfile.logString(_logfile.getTime() + " BEGIN       Apply Viscosity");

    StopWatch t;
    t.start();

    _constrainVelocityField(_MACVelocity);

    ViscositySolverParameters params;
    params.cellwidth = _dx;
    params.deltaTime = dt;
    params.velocityField = &_MACVelocity;
    params.liquidSDF = &_liquidSDF;
    params.solidSDF = &_solidSDF;
    params.viscosity = &_viscosity;

    ViscositySolver vsolver;
    vsolver.applyViscosityToVelocityField(params);
    _viscositySolverStatus = vsolver.getSolverStatus();

    t.stop();
    _timingData.applyViscosityToVelocityField += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Apply Viscosity");
}

/********************************************************************************
    #. Pressure Solve
********************************************************************************/

void FluidSimulation::_updateWeightGrid() {
    if (_isWeightGridUpToDate) {
        return;
    }

    int U = 0; int V = 1; int W = 2; int CENTER = 3;
    
    _updateWeightGridMT(U);
    _updateWeightGridMT(V);
    _updateWeightGridMT(W);
    _updateWeightGridMT(CENTER);

    _isWeightGridUpToDate = true;
}

void FluidSimulation::_updateWeightGridMT(int dir) {

    int U = 0; int V = 1; int W = 2; int CENTER = 3;

    int gridsize = 0;
    if (dir == U) {
        gridsize = (_isize + 1) * _jsize * _ksize;
    } else if (dir == V) {
        gridsize = _isize * (_jsize + 1) * _ksize;
    } else if (dir == W) {
        gridsize = _isize * _jsize * (_ksize + 1);
    } else if (dir == CENTER) {
        gridsize = _isize * _jsize * _ksize;
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_updateWeightGridThread, this,
                                 intervals[i], intervals[i + 1], dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void FluidSimulation::_updateWeightGridThread(int startidx, int endidx, int dir) {
    int U = 0; int V = 1; int W = 2; int CENTER = 3;

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            float weight = 1.0f - _solidSDF.getFaceWeightU(g);
            weight = _clamp(weight, 0.0f, 1.0f);
            _weightGrid.U.set(g, weight);
        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            float weight = 1.0f - _solidSDF.getFaceWeightV(g);
            weight = _clamp(weight, 0.0f, 1.0f);
            _weightGrid.V.set(g, weight);
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            float weight = 1.0f - _solidSDF.getFaceWeightW(g);
            weight = _clamp(weight, 0.0f, 1.0f);
            _weightGrid.W.set(g, weight);
        }

    } else if (dir == CENTER) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            float weight = 1.0f - _solidSDF.getCellWeight(g);
            weight = _clamp(weight, 0.0f, 1.0f);
            _weightGrid.center.set(g, weight);
        }

    }
}

void FluidSimulation::_pressureSolve(double dt) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Solve Pressure System");

    StopWatch t;
    t.start();

    _updateWeightGrid();

    PressureSolverParameters params;
    params.cellwidth = _dx;
    params.deltaTime = dt;
    params.tolerance = _pressureSolveTolerance;
    params.acceptableTolerance = _pressureSolveAcceptableTolerance;
    params.maxIterations = _maxPressureSolveIterations;

    params.velocityField = &_MACVelocity;
    params.validVelocities = &_validVelocities;
    params.liquidSDF = &_liquidSDF;
    params.solidSDF = &_solidSDF;
    params.weightGrid = &_weightGrid;

    params.isSurfaceTensionEnabled = _isSurfaceTensionEnabled;
    if (_isSurfaceTensionEnabled) {
        params.surfaceTensionConstant = _surfaceTensionConstant;
        params.curvatureGrid = &_fluidCurvatureGrid;
    }

    PressureSolver psolver;
    psolver.solve(params);
    _pressureSolverStatus = psolver.getSolverStatus();

    _extrapolateFluidVelocities(_MACVelocity, _validVelocities);
    
    t.stop();
    _timingData.pressureSolve += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Solve Pressure System");
}

/********************************************************************************
    #. Extrapolate Velocity Field
********************************************************************************/

void FluidSimulation::_extrapolateFluidVelocities(MACVelocityField &MACGrid, 
                                                  ValidVelocityComponentGrid &validVelocities) {
    int numLayers = (int)ceil(_CFLConditionNumber) + 2;
    MACGrid.extrapolateVelocityField(validVelocities, numLayers);
}

/********************************************************************************
    #. Constrain Velocity Field
********************************************************************************/

float FluidSimulation::_getFaceFrictionU(GridIndex g) {
    int i = g.i;
    int j = g.j;
    int k = g.k;

    float friction = 0.0f;
    MeshObject *m = _solidSDF.getClosestMeshObject(i, j, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i, j + 1, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i, j, k + 1);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i, j + 1, k + 1);
    friction += m == nullptr ? 0.0f : m->getFriction();

    return 0.25f * friction;
}

float FluidSimulation::_getFaceFrictionV(GridIndex g) {
    int i = g.i;
    int j = g.j;
    int k = g.k;

    float friction = 0.0f;
    MeshObject *m = _solidSDF.getClosestMeshObject(i, j, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i + 1, j, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i, j, k + 1);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i + 1, j, k + 1);
    friction += m == nullptr ? 0.0f : m->getFriction();

    return 0.25f * friction;
}

float FluidSimulation::_getFaceFrictionW(GridIndex g) {
    int i = g.i;
    int j = g.j;
    int k = g.k;

    float friction = 0.0f;
    MeshObject *m = _solidSDF.getClosestMeshObject(i, j, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i + 1, j, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i, j + 1, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    m = _solidSDF.getClosestMeshObject(i + 1, j + 1, k);
    friction += m == nullptr ? 0.0f : m->getFriction();

    return 0.25f * friction;
}

void FluidSimulation::_constrainVelocityField(MACVelocityField &MACGrid) {
    _updateWeightGrid();

    int U = 0; int V = 1; int W = 2;
    _constrainVelocityFieldMT(MACGrid, U);
    _constrainVelocityFieldMT(MACGrid, V);
    _constrainVelocityFieldMT(MACGrid, W);
}

void FluidSimulation::_constrainVelocityFieldMT(MACVelocityField &MACGrid, int dir) {

    int U = 0; int V = 1; int W = 2;

    int gridsize = 0;
    if (dir == U) {
        gridsize = (_isize + 1) * _jsize * _ksize;
    } else if (dir == V) {
        gridsize = _isize * (_jsize + 1) * _ksize;
    } else if (dir == W) {
        gridsize = _isize * _jsize * (_ksize + 1);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, gridsize);
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, gridsize, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_constrainVelocityFieldThread, this,
                                 intervals[i], intervals[i + 1], &MACGrid, dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void FluidSimulation::_constrainVelocityFieldThread(int startidx, int endidx, 
                                                    MACVelocityField *vfield, int dir) {

    int U = 0; int V = 1; int W = 2;

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            if(_weightGrid.U(g) == 0) {
                vfield->setU(g, _solidSDF.getFaceVelocityU(g));
            } else if (_weightGrid.U(g) < 1.0f) {
                float f = _getFaceFrictionU(g);
                float uface = _solidSDF.getFaceVelocityU(g);
                float umac = vfield->U(g);
                float uf = f * uface + (1.0f - f) * umac;
                vfield->setU(g, uf);
            }
        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            if(_weightGrid.V(g) == 0) {
                vfield->setV(g, _solidSDF.getFaceVelocityV(g));
            } else if (_weightGrid.V(g) < 1.0f) {
                float f = _getFaceFrictionV(g);
                float vface = _solidSDF.getFaceVelocityV(g);
                float vmac = vfield->V(g);
                float vf = f * vface + (1.0f - f) * vmac;
                vfield->setV(g, vf);
            }
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            if(_weightGrid.W(g) == 0) {
                vfield->setW(g, _solidSDF.getFaceVelocityW(g));
            } else if (_weightGrid.W(g) < 1.0f) {
                float f = _getFaceFrictionW(g);
                float wface = _solidSDF.getFaceVelocityW(g);
                float wmac = vfield->W(g);
                float wf = f * wface + (1.0f - f) * wmac;
                vfield->setW(g, wf);
            }
        }

    }
}

void FluidSimulation::_constrainVelocityFields() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Constrain Velocity Field");

    StopWatch t;
    t.start();
    _constrainVelocityField(_savedVelocityField);
    _constrainVelocityField(_MACVelocity);
    t.stop();
    _timingData.constrainVelocityFields += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Constrain Velocity Field");
}

/********************************************************************************
    #. Update Diffuse Particle Simulation
********************************************************************************/

void FluidSimulation::_updateDiffuseMaterial(double dt) {
    if (!_isDiffuseMaterialOutputEnabled) {
        return;
    }

    _logfile.logString(_logfile.getTime() + " BEGIN       Simulate Diffuse Material");

    StopWatch t;
    t.start();

    _updateDiffuseInfluenceGrid(dt);

    DiffuseParticleSimulationParameters params;
    params.isize = _isize;
    params.jsize = _jsize;
    params.ksize = _ksize;
    params.dx = _dx;
    params.deltaTime = dt;
    params.CFLConditionNumber = _CFLConditionNumber;
    params.markerParticleRadius = _markerParticleRadius;
    params.bodyForce = _getConstantBodyForce();

    params.markerParticles = &_markerParticles;
    params.vfield = &_MACVelocity;
    params.liquidSDF = &_liquidSDF;
    params.solidSDF = &_solidSDF;

    params.meshingVolumeSDF = NULL;
    params.isMeshingVolumeSet = false;
    if (_isMeshingVolumeSet) {
        params.meshingVolumeSDF = &_meshingVolumeSDF;
        params.isMeshingVolumeSet = true;
    }

    params.surfaceSDF = &_fluidSurfaceLevelSet;
    params.curvatureGrid = &_fluidCurvatureGrid;
    params.influenceGrid = _obstacleInfluenceGrid.getInfluenceGrid();
    params.nearSolidGrid = &_nearSolidGrid;
    params.nearSolidGridCellSize = _nearSolidGridCellSize;

    _diffuseMaterial.update(params);

    t.stop();
    _timingData.updateDiffuseMaterial += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Simulate Diffuse Material");
}

void FluidSimulation::_updateDiffuseInfluenceGrid(double dt) {
    int infi, infj, infk;
    _obstacleInfluenceGrid.getGridDimensions(&infi, &infj, &infk);
    if (infi != _isize + 1 || infj != _jsize + 1 || infk != _ksize + 1) {
        _obstacleInfluenceGrid = InfluenceGrid(_isize + 1, _jsize + 1, _ksize + 1, _dx, 
                                               _diffuseObstacleInfluenceBaseLevel);
    }

    _domainMeshObject.setWhitewaterInfluence(_diffuseObstacleInfluenceBaseLevel);
    _obstacleInfluenceGrid.setBaseLevel(_diffuseObstacleInfluenceBaseLevel);
    _obstacleInfluenceGrid.setDecayRate(_diffuseObstacleInfluenceDecayRate);
    _obstacleInfluenceGrid.update(&_solidSDF, dt);
}

/********************************************************************************
    #. Update Sheeting
********************************************************************************/

void FluidSimulation::_updateSheetSeeding() {
    if (!_isSheetSeedingEnabled) {
        return;
    }

    _logfile.logString(_logfile.getTime() + " BEGIN       Update Sheet Seeding");

    StopWatch t;
    t.start();


    ParticleSheeterParameters params;
    params.particles = &_markerParticles;
    params.fluidSurfaceLevelSet = &_fluidSurfaceLevelSet;
    params.isize = _isize;
    params.jsize = _jsize;
    params.ksize = _ksize;
    params.dx = _dx;
    params.sheetFillThreshold = _sheetFillThreshold;

    std::vector<vmath::vec3> sheetParticles;
    ParticleSheeter sheeter;
    sheeter.generateSheetParticles(params, sheetParticles);

    float solidSheetingWidth = 2.0f * _dx;
    for (size_t i = 0; i < sheetParticles.size(); i++) {
        vmath::vec3 p = sheetParticles[i];
        float sheetFillRate = _sheetFillRate;
        if (_solidSDF.trilinearInterpolate(p) < solidSheetingWidth) {
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize)) {
                MeshObject *obj = _solidSDF.getClosestMeshObject(g);
                if (obj != nullptr) {
                    sheetFillRate = _clamp(sheetFillRate * obj->getSheetingStrength(), 0.0f, 1.0f);
                }
            }
        }

        if (_randomDouble(0.0, 1.0) > sheetFillRate) {
            continue;
        }

        vmath::vec3 v = _savedVelocityField.evaluateVelocityAtPositionLinear(p);
        MarkerParticle m(p, v);
        _markerParticles.push_back(m);
    }

    t.stop();

    _timingData.updateSheetSeeding += t.getTime();
    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Sheet Seeding");
}

/********************************************************************************
    #. Update MarkerParticle Velocities
********************************************************************************/

void FluidSimulation::_updatePICFLIPMarkerParticleVelocitiesThread(int startidx, int endidx) {
    for (int i = startidx; i < endidx; i++) {
        MarkerParticle mp = _markerParticles[i];
        vmath::vec3 vPIC = _MACVelocity.evaluateVelocityAtPositionLinear(mp.position);
        vmath::vec3 vFLIP = mp.velocity + vPIC - 
                            _savedVelocityField.evaluateVelocityAtPositionLinear(mp.position);
        vmath::vec3 v = (float)_ratioPICFLIP * vPIC + (float)(1 - _ratioPICFLIP) * vFLIP;

        _markerParticles[i].velocity = v;
    }
}

void FluidSimulation::_updatePICFLIPMarkerParticleVelocities() {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _markerParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _markerParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_updatePICFLIPMarkerParticleVelocitiesThread, this,
                                 intervals[i], intervals[i + 1]);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void FluidSimulation::_constrainMarkerParticleVelocities(MeshFluidSource *inflow) {
    float frameTime = (float)(_currentFrameDeltaTimeRemaining + _currentFrameTimeStep);
    float frameProgress = 1.0f - frameTime / (float)_currentFrameDeltaTime;
    int numSubsteps = inflow->getSubstepEmissions();

    if (numSubsteps == 0) {
        numSubsteps = 1;
    }

    float substepFactor = (_currentFrameTimeStep / _currentFrameDeltaTime) / (float)numSubsteps;

    Array3d<bool> isInflowCell(_isize, _jsize, _ksize, false);
    for (int subidx = 0; subidx < numSubsteps; subidx++) {
        float frameInterpolation = frameProgress + (float)subidx * substepFactor;
        inflow->setFrame(_currentFrame, frameInterpolation);
        inflow->update(_currentFrameDeltaTime);

        std::vector<GridIndex> inflowCells;
        inflow->getCells(frameInterpolation, inflowCells);
        isInflowCell.fill(false);
        isInflowCell.set(inflowCells, true);

        MeshLevelSet *inflowSDF = inflow->getMeshLevelSet();
        vmath::vec3 v = inflow->getVelocity();
        RigidBodyVelocity rv = inflow->getRigidBodyVelocity(_currentFrameDeltaTime);
        VelocityFieldData *vdata = inflow->getVelocityFieldData();
        for (size_t i = 0; i < _markerParticles.size(); i++) {
            vmath::vec3 p = _markerParticles[i].position;
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (!isInflowCell(g)) {
                continue;
            }

            if (inflowSDF->trilinearInterpolate(p) > 0.0f) {
                continue;
            }

            if (inflow->isAppendObjectVelocityEnabled()) {
                if (inflow->isRigidMeshEnabled()) {
                    vmath::vec3 tv = vmath::cross(rv.angular * rv.axis, p - rv.centroid);
                    _markerParticles[i].velocity = v + rv.linear + tv;
                } else {
                    vmath::vec3 datap = p - vdata->offset;
                    vmath::vec3 fv = vdata->vfield.evaluateVelocityAtPositionLinear(datap);
                    _markerParticles[i].velocity = v + fv;
                }
            } else {
                _markerParticles[i].velocity = v;
            }
        }
    }
}

void FluidSimulation::_constrainMarkerParticleVelocities() {
    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        MeshFluidSource *source = _meshFluidSources[i];
        if (!source->isEnabled() || !source->isInflow() || 
                !source->isConstrainedFluidVelocityEnabled()) {
            continue;
        }
        _constrainMarkerParticleVelocities(source);
    }
}

void FluidSimulation::_updateMarkerParticleVelocities() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Update Marker Particle Velocities");

    StopWatch t;
    t.start();

    _updatePICFLIPMarkerParticleVelocities();
    _constrainMarkerParticleVelocities();

    t.stop();
    _timingData.updateMarkerParticleVelocities += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Marker Particle Velocities");
}

/********************************************************************************
    #. Advance MarkerParticles
********************************************************************************/

vmath::vec3 FluidSimulation::_RK3(vmath::vec3 p0, double dt) {
    vmath::vec3 k1 = _MACVelocity.evaluateVelocityAtPositionLinear(p0);
    vmath::vec3 k2 = _MACVelocity.evaluateVelocityAtPositionLinear(p0 + (float)(0.5*dt)*k1);
    vmath::vec3 k3 = _MACVelocity.evaluateVelocityAtPositionLinear(p0 + (float)(0.75*dt)*k2);
    vmath::vec3 p1 = p0 + (float)(dt/9.0f)*(2.0f*k1 + 3.0f*k2 + 4.0f*k3);

    return p1;
}

void FluidSimulation::_advanceMarkerParticlesThread(double dt, int startidx, int endidx,
                                                    std::vector<vmath::vec3> *positions,
                                                    std::vector<vmath::vec3> *output) {
    for (int i = startidx; i < endidx; i++) {
        (*output)[i] = _RK3(positions->at(i), dt);
    }

    _resolveMarkerParticleCollisions(startidx, endidx, *positions, *output);
}


void FluidSimulation::_resolveMarkerParticleCollisions(int startidx, int endidx,
                                                       std::vector<vmath::vec3> &positionsOld, 
                                                       std::vector<vmath::vec3> &positionsNew) {
    AABB boundary = _getBoundaryAABB();
    boundary.expand(-_solidBufferWidth * _dx);
    for (int i = startidx; i < endidx; i++) {
        positionsNew[i] = _resolveCollision(positionsOld[i], positionsNew[i], boundary);
    }
}

vmath::vec3 FluidSimulation::_resolveCollision(vmath::vec3 oldp, vmath::vec3 newp,
                                               AABB &boundary) {

    GridIndex gridg = Grid3d::positionToGridIndex(newp, _dx);
    if (!Grid3d::isGridIndexInRange(gridg, _isize, _jsize, _ksize)) {
        newp = boundary.getNearestPointInsideAABB(newp);
    }

    GridIndex oldg = Grid3d::positionToGridIndex(oldp, _nearSolidGridCellSize);
    GridIndex newg = Grid3d::positionToGridIndex(newp, _nearSolidGridCellSize);
    if (!_nearSolidGrid(oldg) && !_nearSolidGrid(newg)) {
        return newp;
    }

    float eps = 1e-6;
    float stepDistance = _markerParticleStepDistanceFactor * (float)_dx;
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

        float phi = _solidSDF.trilinearInterpolate(currentPosition);
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
    vmath::vec3 grad = _solidSDF.trilinearInterpolateGradient(currentPosition);
    if (vmath::length(grad) > eps) {
        grad = vmath::normalize(grad);
        resolvedPosition = currentPosition - (collisionPhi - _solidBufferWidth * _dx) * grad;
        float resolvedPhi = _solidSDF.trilinearInterpolate(resolvedPosition);
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
        float resolvedPhi = _solidSDF.trilinearInterpolate(resolvedPosition);
        float resolvedDistance = vmath::length(resolvedPosition - origPosition);
        if (resolvedPhi < 0.0f || resolvedDistance > maxResolvedDistance) {
            resolvedPosition = lastPosition;
        }
    }

    return resolvedPosition;
}

float FluidSimulation::_getMarkerParticleSpeedLimit(double dt) {
    double speedLimitStep = _CFLConditionNumber * _dx / dt;
    std::vector<int> speedLimitCounts(_maxFrameTimeSteps, 0);
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        double speed = (double)_markerParticles[i].velocity.length();
        int speedLimitIndex = fmin(floor(speed / speedLimitStep), _maxFrameTimeSteps - 1);
        speedLimitCounts[speedLimitIndex]++;
    }

    double maxpct = _maxExtremeVelocityRemovalPercent;
    int maxabs = _maxExtremeVelocityRemovalAbsolute;
    int maxRemovalCount = fmin((int)((double)_markerParticles.size() * maxpct), maxabs);
    double maxspeed = _maxFrameTimeSteps * speedLimitStep;
    int currentRemovalCount = 0;
    for (int i = (int)speedLimitCounts.size() - 1; i > 0; i--) {
        if (currentRemovalCount + speedLimitCounts[i] > maxRemovalCount) {
            break;
        }

        currentRemovalCount += speedLimitCounts[i];
        maxspeed = i * speedLimitStep;
    }

    return maxspeed;
}

void FluidSimulation::_removeMarkerParticles(double dt) {
    Array3d<int> countGrid = Array3d<int>(_isize, _jsize, _ksize, 0);

    float maxspeed = _getMarkerParticleSpeedLimit(dt);
    double maxspeedsq = maxspeed * maxspeed;

    std::vector<bool> isRemoved;
    _solidSDF.trilinearInterpolateSolidPoints(_markerParticles, isRemoved);
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        if (isRemoved[i]) {
            continue;
        }

        MarkerParticle mp = _markerParticles[i];
        GridIndex g = Grid3d::positionToGridIndex(mp.position, _dx);
        if (countGrid(g) >= _maxMarkerParticlesPerCell) {
            isRemoved[i] = true;
            continue;
        }
        countGrid.add(g, 1);

        if (_isExtremeVelocityRemovalEnabled && 
                vmath::dot(mp.velocity, mp.velocity) > maxspeedsq) {
            isRemoved[i] = true;
            continue;
        }
    }

    _removeItemsFromVector(_markerParticles, isRemoved);
}

void FluidSimulation::_advanceMarkerParticles(double dt) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Advect Marker Particles");

    StopWatch t;
    t.start();
    
    std::vector<vmath::vec3> positions;
    positions.reserve(_markerParticles.size());
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        positions.push_back(_markerParticles[i].position);
    }

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, positions.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<vmath::vec3> output(positions.size());
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, positions.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_advanceMarkerParticlesThread, this,
                                 dt, intervals[i], intervals[i + 1], &positions, &output);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    for (size_t i = 0; i < _markerParticles.size(); i++) {
        _markerParticles[i].position = output[i];
    }

    _removeMarkerParticles(_currentFrameDeltaTime);

    t.stop();
    _timingData.advanceMarkerParticles += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Advect Marker Particles");
}

/********************************************************************************
    #. Update Fluid Objects
********************************************************************************/

void FluidSimulation::_addNewFluidCells(std::vector<GridIndex> &cells, 
                                        vmath::vec3 velocity,
                                        MeshLevelSet &meshSDF,
                                        ParticleMaskGrid &maskgrid) {
    double q = 0.25 * _dx;
    vmath::vec3 particleOffsets[8] = {
        vmath::vec3(-q, -q, -q),
        vmath::vec3( q, -q, -q),
        vmath::vec3(-q,  q, -q),
        vmath::vec3( q,  q, -q),
        vmath::vec3(-q, -q,  q),
        vmath::vec3( q, -q,  q),
        vmath::vec3(-q,  q,  q),
        vmath::vec3( q,  q,  q)
    };

    double jitter = _getMarkerParticleJitter();
    GridIndex g;
    vmath::vec3 p;
    for (size_t i = 0; i < cells.size(); i++) {
        g = cells[i];
        vmath::vec3 c = Grid3d::GridIndexToCellCenter(g, _dx);

        for (unsigned int oidx = 0; oidx < 8; oidx++) {
            p = c + particleOffsets[oidx];
            if (maskgrid.isSubCellSet(p)) {
                continue;
            }

            double d = meshSDF.trilinearInterpolate(p);
            if (d > 0) {
                continue;
            }

            if (_isJitterSurfaceMarkerParticlesEnabled || d < -_dx) {
                p = _jitterMarkerParticlePosition(p, jitter);
            }

            if (_solidSDF.trilinearInterpolate(p) > 0) {
                _addMarkerParticle(p, velocity);
                maskgrid.addParticle(p);
            }
        }
    }
}

void FluidSimulation::_addNewFluidCells(std::vector<GridIndex> &cells, 
                                        vmath::vec3 velocity,
                                        RigidBodyVelocity rvelocity,
                                        MeshLevelSet &meshSDF,
                                        ParticleMaskGrid &maskgrid) {
    double q = 0.25 * _dx;
    vmath::vec3 particleOffsets[8] = {
        vmath::vec3(-q, -q, -q),
        vmath::vec3( q, -q, -q),
        vmath::vec3(-q,  q, -q),
        vmath::vec3( q,  q, -q),
        vmath::vec3(-q, -q,  q),
        vmath::vec3( q, -q,  q),
        vmath::vec3(-q,  q,  q),
        vmath::vec3( q,  q,  q)
    };

    double jitter = _getMarkerParticleJitter();
    GridIndex g;
    vmath::vec3 p;
    for (size_t i = 0; i < cells.size(); i++) {
        g = cells[i];
        vmath::vec3 c = Grid3d::GridIndexToCellCenter(g, _dx);

        for (unsigned int oidx = 0; oidx < 8; oidx++) {
            p = c + particleOffsets[oidx];
            if (maskgrid.isSubCellSet(p)) {
                continue;
            }

            double d = meshSDF.trilinearInterpolate(p);
            if (d > 0) {
                continue;
            }

            if (_isJitterSurfaceMarkerParticlesEnabled || d < -_dx) {
                p = _jitterMarkerParticlePosition(p, jitter);
            }

            if (_solidSDF.trilinearInterpolate(p) > 0) {
                vmath::vec3 tv = vmath::cross(rvelocity.angular * rvelocity.axis, 
                                              p - rvelocity.centroid);
                vmath::vec3 v = velocity + rvelocity.linear + tv;
                _addMarkerParticle(p, v);
                maskgrid.addParticle(p);
            }
        }
    }
}

void FluidSimulation::_addNewFluidCells(std::vector<GridIndex> &cells, 
                                        vmath::vec3 velocity,
                                        VelocityFieldData *vdata,
                                        MeshLevelSet &meshSDF,
                                        ParticleMaskGrid &maskgrid) {
    double q = 0.25 * _dx;
    vmath::vec3 particleOffsets[8] = {
        vmath::vec3(-q, -q, -q),
        vmath::vec3( q, -q, -q),
        vmath::vec3(-q,  q, -q),
        vmath::vec3( q,  q, -q),
        vmath::vec3(-q, -q,  q),
        vmath::vec3( q, -q,  q),
        vmath::vec3(-q,  q,  q),
        vmath::vec3( q,  q,  q)
    };

    double jitter = _getMarkerParticleJitter();
    GridIndex g;
    vmath::vec3 p;
    for (size_t i = 0; i < cells.size(); i++) {
        g = cells[i];
        vmath::vec3 c = Grid3d::GridIndexToCellCenter(g, _dx);

        for (unsigned int oidx = 0; oidx < 8; oidx++) {
            p = c + particleOffsets[oidx];
            if (maskgrid.isSubCellSet(p)) {
                continue;
            }

            double d = meshSDF.trilinearInterpolate(p);
            if (d > 0) {
                continue;
            }

            if (_isJitterSurfaceMarkerParticlesEnabled || d < -_dx) {
                p = _jitterMarkerParticlePosition(p, jitter);
            }

            if (_solidSDF.trilinearInterpolate(p) > 0) {
                vmath::vec3 datap = p - vdata->offset;
                vmath::vec3 fv = vdata->vfield.evaluateVelocityAtPositionLinear(datap);
                vmath::vec3 v = velocity + fv;

                _addMarkerParticle(p, v);
                maskgrid.addParticle(p);
            }
        }
    }
}

void FluidSimulation::_updateInflowMeshFluidSource(MeshFluidSource *source,
                                                   ParticleMaskGrid &maskgrid) {
    if (!source->isEnabled()) {
        return;
    }

    float frameTime = (float)(_currentFrameDeltaTimeRemaining + _currentFrameTimeStep);
    float frameProgress = 1.0f - frameTime / (float)_currentFrameDeltaTime;
    int numSubsteps = source->getSubstepEmissions();

    if (numSubsteps == 0) {
        numSubsteps = 1;
        if (_currentFrameTimeStepNumber != 0) {
            return;
        }
    }

    float substepFactor = (_currentFrameTimeStep / _currentFrameDeltaTime) / (float)numSubsteps;

    for (int i = 0; i < numSubsteps; i++) {
        float frameInterpolation = frameProgress + (float)i * substepFactor;
        source->setFrame(_currentFrame, frameInterpolation);
        source->update(_currentFrameDeltaTime);

        std::vector<GridIndex> sourceCells;
        source->getCells(frameInterpolation, sourceCells);

        MeshLevelSet *sourceSDF = source->getMeshLevelSet();
        vmath::vec3 velocity = source->getVelocity();

        if (source->isAppendObjectVelocityEnabled()) {
            if (source->isRigidMeshEnabled()) {
                RigidBodyVelocity rv = source->getRigidBodyVelocity(_currentFrameDeltaTime);
                _addNewFluidCells(sourceCells, velocity, rv, *sourceSDF, maskgrid);
            } else {
                VelocityFieldData *vdata = source->getVelocityFieldData();
                _addNewFluidCells(sourceCells, velocity, vdata, *sourceSDF, maskgrid);
            }
        } else {
            _addNewFluidCells(sourceCells, velocity, *sourceSDF, maskgrid);
        }
    }
}

void FluidSimulation::_updateOutflowMeshFluidSource(MeshFluidSource *source) {
    if (!source->isEnabled()) {
        return;
    }

    if (!source->isFluidOutflowEnabled() && !source->isDiffuseOutflowEnabled()) {
        return;
    }

    float frameTime = (float)(_currentFrameDeltaTimeRemaining + _currentFrameTimeStep);
    float frameProgress = 1.0f - frameTime / (float)_currentFrameDeltaTime;

    source->setFrame(_currentFrame, frameProgress);
    source->update(_currentFrameDeltaTime);

    std::vector<GridIndex> sourceCells;
    source->getCells(frameProgress, sourceCells);
    MeshLevelSet *sourceSDF = source->getMeshLevelSet();

    Array3d<bool> isOutflowCell(_isize, _jsize, _ksize);
    if (source->isOutflowInversed()) {
        isOutflowCell.fill(true);
        isOutflowCell.set(sourceCells, false);
    } else {
        isOutflowCell.fill(false);
        isOutflowCell.set(sourceCells, true);
    }

    if (source->isFluidOutflowEnabled()) {
        std::vector<bool> isRemoved(_markerParticles.size(), false);
        for (int i = 0; i < (int)_markerParticles.size(); i++) {
            vmath::vec3 p = _markerParticles[i].position;
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (isOutflowCell(g)) {
                float d = sourceSDF->trilinearInterpolate(p);
                if (source->isOutflowInversed() && d >= 0.0f) {
                    isRemoved[i] = true;
                } else if (!source->isOutflowInversed() && d < 0.0f) {
                    isRemoved[i] = true;
                }
            }
        }
        _removeItemsFromVector(_markerParticles, isRemoved);
    }
    
    if (source->isDiffuseOutflowEnabled()) {
        FragmentedVector<DiffuseParticle>* dps = _diffuseMaterial.getDiffuseParticles();
        std::vector<bool> isRemoved(dps->size(), false);
        for (int i = 0; i < (int)dps->size(); i++) {
            vmath::vec3 p = dps->at(i).position;
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (!isOutflowCell.isIndexInRange(g)) {
                continue;
            }

            if (isOutflowCell(g)) {
                float d = sourceSDF->trilinearInterpolate(p);
                if (source->isOutflowInversed() && d >= 0.0f) {
                    isRemoved[i] = true;
                } else if (!source->isOutflowInversed() && d < 0.0f) {
                    isRemoved[i] = true;
                }
            }
        }
        _removeItemsFromVector(*dps, isRemoved);
    }
}

void FluidSimulation::_updateInflowMeshFluidSources() {
    int numInflowSources = 0;
    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        if (_meshFluidSources[i]->isInflow() && _meshFluidSources[i]->isEnabled()) {
            numInflowSources++;
        }
    }

    if (numInflowSources == 0) {
        return;
    }

    ParticleMaskGrid maskgrid(_isize, _jsize, _ksize, _dx);
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        maskgrid.addParticle(_markerParticles[i].position);
    }

    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        if (_meshFluidSources[i]->isInflow()) {
            _updateInflowMeshFluidSource(_meshFluidSources[i], maskgrid);
        }
    }
}

void FluidSimulation::_updateOutflowMeshFluidSources() {
    int numOutflowSources = 0;
    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        if (_meshFluidSources[i]->isOutflow() && _meshFluidSources[i]->isEnabled()) {
            numOutflowSources++;
        }
    }

    if (numOutflowSources == 0) {
        return;
    }

    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        if (_meshFluidSources[i]->isOutflow()) {
            _updateOutflowMeshFluidSource(_meshFluidSources[i]);
        }
    }
}

void FluidSimulation::_updateMeshFluidSources() {
    _updateInflowMeshFluidSources();
    _updateOutflowMeshFluidSources();
}

void FluidSimulation::_updateAddedFluidMeshObjectQueue() {
    if (_addedFluidMeshObjectQueue.empty()) {
        return;
    }

    ParticleMaskGrid maskgrid(_isize, _jsize, _ksize, _dx);
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        maskgrid.addParticle(_markerParticles[i].position);
    }

    MeshLevelSet meshSDF(_isize, _jsize, _ksize, _dx);
    meshSDF.disableVelocityData();

    std::vector<GridIndex> objectCells;
    for (unsigned int i = 0; i < _addedFluidMeshObjectQueue.size(); i++) {
        MeshObject object = _addedFluidMeshObjectQueue[i].object;
        vmath::vec3 velocity = _addedFluidMeshObjectQueue[i].velocity;

        objectCells.clear();
        object.getCells(objectCells);

        TriangleMesh mesh = object.getMesh();
        meshSDF.reset();
        meshSDF.fastCalculateSignedDistanceField(mesh, _liquidLevelSetExactBand);

        if (object.isAppendObjectVelocityEnabled()) {
            RigidBodyVelocity rv = object.getRigidBodyVelocity(_currentFrameDeltaTime);
            _addNewFluidCells(objectCells, velocity, rv, meshSDF, maskgrid);
        } else {
            _addNewFluidCells(objectCells, velocity, meshSDF, maskgrid);
        }
    }

    _addedFluidMeshObjectQueue.clear();
}

int FluidSimulation::_getNumFluidCells() {
    int count = 0;
    for (int k = 1; k < _ksize - 1; k++) {
        for (int j = 1; j < _jsize - 1; j++) {
            for (int i = 1; i < _isize - 1; i++) {
                if (_liquidSDF.get(i, j, k) < 0.0f) {
                   count++;
                }
            }
        }
    }

    if (count == 0 && !_markerParticles.empty()) {
        Array3d<bool> isFluidCell(_isize, _jsize, _ksize, false);
        for (unsigned int i = 0; i < _markerParticles.size(); i++) {
            GridIndex g = Grid3d::positionToGridIndex(_markerParticles[i].position, _dx);
            isFluidCell.set(g, true);
        }

        for (int k = 0; k < _ksize; k++) {
            for (int j = 0; j < _jsize; j++) {
                for (int i = 0; i < _isize; i++) {
                    if (isFluidCell(i, j, k)) {
                       count++;
                    }
                }
            }
        }
    }

    return count;
}

void FluidSimulation::_updateFluidObjects() {
    _logfile.logString(_logfile.getTime() + " BEGIN       Update Fluid Objects");

    StopWatch t;
    t.start();
    _updateAddedFluidMeshObjectQueue();
    _updateMeshFluidSources();
    t.stop();

    _timingData.updateFluidObjects += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Fluid Objects");
}

/********************************************************************************
    4.  Reconstruct Output Fluid Surface
********************************************************************************/

void FluidSimulation::_getTriangleMeshFileData(TriangleMesh &mesh, std::vector<char> &data) {
    if (_meshOutputFormat == TriangleMeshFormat::ply) {
        mesh.getMeshFileDataPLY(data);
    } else if (_meshOutputFormat == TriangleMeshFormat::bobj) {
        mesh.getMeshFileDataBOBJ(data);
    }
}

void FluidSimulation::_getFluidParticleFileData(std::vector<vmath::vec3> &particles, 
                                                std::vector<int> &binStarts, 
                                                std::vector<float> &binSpeeds, 
                                                std::vector<char> &outdata) {
    int numParticles = (int)particles.size();
    int numBins = (int)binStarts.size();
    int particleDataSize = 3 * numParticles * sizeof(float);
    int binStartsDataSize = numBins * sizeof(float);
    int binSpeedsDataSize = numBins * sizeof(float);
    int binDataSize = binStartsDataSize + binSpeedsDataSize;
    int dataSize = sizeof(int) + particleDataSize + sizeof(int) + binDataSize;

    outdata.clear();
    outdata.resize(dataSize);
    outdata.shrink_to_fit();

    int byteOffset = 0;
    std::memcpy(outdata.data() + byteOffset, &numParticles, sizeof(int));
    byteOffset += sizeof(int);

    std::memcpy(outdata.data() + byteOffset, (char*)particles.data(), particleDataSize);
    byteOffset += particleDataSize;

    std::memcpy(outdata.data() + byteOffset, &numBins, sizeof(int));
    byteOffset += sizeof(int);

    std::memcpy(outdata.data() + byteOffset, (char*)binStarts.data(), binStartsDataSize);
    byteOffset += binStartsDataSize;

    std::memcpy(outdata.data() + byteOffset, (char*)binSpeeds.data(), binSpeedsDataSize);
    byteOffset += binSpeedsDataSize;
}

std::string FluidSimulation::_numberToString(int number) {
    std::ostringstream ss;
    ss << number;
    return ss.str();
}

std::string FluidSimulation::_getFrameString(int number) {
    std::string currentFrame = _numberToString(number);
    currentFrame.insert(currentFrame.begin(), 6 - currentFrame.size(), '0');
    return currentFrame;
}

void FluidSimulation::_smoothSurfaceMesh(TriangleMesh &mesh) {
    mesh.smooth(_surfaceReconstructionSmoothingValue, 
                _surfaceReconstructionSmoothingIterations);
}

void FluidSimulation::_invertContactNormals(TriangleMesh &mesh) {
    if (!_isInvertedContactNormalsEnabled) {
        return;
    }

    float eps = _contactThresholdDistance * _dx;
    std::vector<bool> contactVertices(mesh.vertices.size(), false);
    for (size_t i = 0; i < mesh.vertices.size(); i++) {
        if (_solidSDF.trilinearInterpolate(mesh.vertices[i]) < eps) {
            contactVertices[i] = true;
        }
    }

    for (size_t i = 0; i < mesh.triangles.size(); i++) {
        Triangle t = mesh.triangles[i];
        if (contactVertices[t.tri[0]] || contactVertices[t.tri[1]] || contactVertices[t.tri[2]]) {
            int temp = t.tri[1];
            t.tri[1] = t.tri[2];
            t.tri[2] = temp;
            mesh.triangles[i] = t;
        }
    }
}

void FluidSimulation::_removeMeshNearDomain(TriangleMesh &mesh) {
    if (!_isRemoveSurfaceNearDomainEnabled) {
        return;
    }

    Array3d<bool> validCells(_isize, _jsize, _ksize, false);
    int width = 2 + _removeSurfaceNearDomainDistance;
    for (int k = 0 + width; k < _ksize - width; k++) {
        for (int j = 0 + width; j < _jsize - width; j++) {
            for (int i = 0 + width; i < _isize - width; i++) {
                validCells.set(i, j, k, true);
            }
        }
    }

    std::vector<int> removalTriangles;
    for (size_t tidx = 0; tidx < mesh.triangles.size(); tidx++) {
        Triangle t = mesh.triangles[tidx];
        vmath::vec3 centroid = (mesh.vertices[t.tri[0]] + 
                                mesh.vertices[t.tri[1]] + 
                                mesh.vertices[t.tri[2]]) / 3.0;
        GridIndex g = Grid3d::positionToGridIndex(centroid, _dx);
        if (!validCells(g)) {
            removalTriangles.push_back(tidx);
        } else {
            if (_isMeshingVolumeSet) {
                float d = _meshingVolumeSDF.trilinearInterpolate(centroid);
                if (d < _dx) {
                    removalTriangles.push_back(tidx);
                }
            }
        }
    }

    mesh.removeTriangles(removalTriangles);
    mesh.removeExtraneousVertices();
}

void FluidSimulation::_computeDomainBoundarySDF(MeshLevelSet *sdf) {
    AABB bbox = _getBoundaryAABB();
    vmath::vec3 minp = bbox.getMinPoint();
    vmath::vec3 maxp = bbox.getMaxPoint();
    GridIndex gmin = Grid3d::positionToGridIndex(minp, _dx);
    GridIndex gmax = Grid3d::positionToGridIndex(maxp, _dx);

    /*
    for (int k = gmin.k + 1; k <= gmax.k; k++) {
        for (int j = gmin.j + 1; j <= gmax.j; j++) {
            for (int i = gmin.i + 1; i <= gmax.i; i++) {
                sdf->set(i, j, k, -sdf->get(i, j, k));
            }
        }
    }
    */

    // -X side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = gmin.i; i <= gmin.i + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = bbox.getSignedDistance(p);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // +X side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = gmax.i; i <= gmax.i + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = bbox.getSignedDistance(p);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // -Y side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = gmin.j; j <= gmin.j + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = bbox.getSignedDistance(p);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // +Y side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = gmax.j; j <= gmax.j + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = bbox.getSignedDistance(p);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // -Z side
    for (int k = gmin.k; k <= gmin.k + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = bbox.getSignedDistance(p);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // +Z side
    for (int k = gmax.k; k <= gmax.k + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = bbox.getSignedDistance(p);
                sdf->set(i, j, k, d);
            }   
        }
    }
}

void FluidSimulation::_polygonizeOutputSurface(TriangleMesh &surface, TriangleMesh &preview,
                                               std::vector<vmath::vec3> *particles,
                                               MeshLevelSet *solidSDF) {
    if (_markerParticles.empty()) {
        surface = TriangleMesh();
        preview = TriangleMesh();
        return;
    }

    if (_isObstacleMeshingOffsetEnabled) {
        float eps = 1e-9;
        float offset = (float)(_obstacleMeshingOffset * _dx);
        if (std::abs(offset) > eps) {
            for (int k = 2; k < _ksize - 1; k++) {
                for (int j = 2; j < _jsize - 1; j++) {
                    for (int i = 2; i < _isize - 1; i++) {
                        solidSDF->set(i, j, k, solidSDF->get(i, j, k) + offset);
                    }
                }
            }
        }
    } else {
        float fillval = 3.0 * _dx;
        for (int k = 0; k < _ksize + 1; k++) {
            for (int j = 0; j < _jsize + 1; j++) {
                for (int i = 0; i < _isize + 1; i++) {
                    solidSDF->set(i, j, k, fillval);
                }
            }
        }
        _computeDomainBoundarySDF(solidSDF);
    }

    ParticleMesherParameters params;
    params.isize = _isize;
    params.jsize = _jsize;
    params.ksize = _ksize;
    params.dx = _dx;
    params.subdivisions = _outputFluidSurfaceSubdivisionLevel;
    params.computechunks = _numSurfaceReconstructionPolygonizerSlices;
    params.radius = _markerParticleRadius*_markerParticleScale;
    params.particles = particles;
    params.solidSDF = solidSDF;
    params.isPreviewMesherEnabled = _isPreviewSurfaceMeshEnabled;
    if (_isPreviewSurfaceMeshEnabled) {
        params.previewdx = _previewdx;
    }

    ParticleMesher mesher;
    surface = mesher.meshParticles(params);
    if (_isPreviewSurfaceMeshEnabled) {
        preview = mesher.getPreviewMesh();
    }
}

void FluidSimulation::_updateMeshingVolumeSDF() {
    if (!_isMeshingVolumeSet || _currentFrameTimeStepNumber != 0) {
        return;
    }

    MeshObjectStatus s = _meshingVolume->getStatus();
    _meshingVolume->clearObjectStatus();
    if (s.isStateChanged || (s.isEnabled && s.isAnimated && s.isMeshChanged)) {
        _isMeshingVolumeLevelSetUpToDate = false;
    }

    if (_isMeshingVolumeLevelSetUpToDate) {
        return;
    }

    _meshingVolumeSDF.reset();
    _meshingVolumeSDF.disableVelocityData();
    _meshingVolume->getMeshLevelSet(_currentFrameDeltaTime, 0.0, _solidLevelSetExactBand, _meshingVolumeSDF);
    _meshingVolumeSDF.negate();

    _isMeshingVolumeLevelSetUpToDate = true;
}

void FluidSimulation::_applyMeshingVolumeToSDF(MeshLevelSet *sdf) {
    if (!_isMeshingVolumeSet) {
        return;
    }

    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                float d1 = sdf->get(i, j, k);
                float d2 = _meshingVolumeSDF(i, j, k);
                if (d2 < d1) {
                    sdf->set(i, j, k, d2);
                }
            }
        }
    }
}

void FluidSimulation::_filterParticlesOutsideMeshingVolume(std::vector<vmath::vec3> *particles) {
    if (!_isMeshingVolumeSet) {
        return;
    }

    std::vector<bool> isSolid;
    _meshingVolumeSDF.trilinearInterpolateSolidPoints(*particles, isSolid);
    _removeItemsFromVector(*particles, isSolid);
}

void FluidSimulation::_outputSurfaceMeshThread(std::vector<vmath::vec3> *particles,
                                               MeshLevelSet *solidSDF) {
    if (!_isSurfaceMeshReconstructionEnabled) { return; }

    _logfile.logString(_logfile.getTime() + " BEGIN       Generate Surface Mesh");

    StopWatch t;
    t.start();

    _applyMeshingVolumeToSDF(solidSDF);
    _filterParticlesOutsideMeshingVolume(particles);

    TriangleMesh isomesh, previewmesh;
    _polygonizeOutputSurface(isomesh, previewmesh, particles, solidSDF);
    delete particles;
    delete solidSDF;

    isomesh.removeMinimumTriangleCountPolyhedra(_minimumSurfacePolyhedronTriangleCount);

    _removeMeshNearDomain(isomesh);
    _smoothSurfaceMesh(isomesh);
    _smoothSurfaceMesh(previewmesh);
    _invertContactNormals(isomesh);

    if (_isSurfaceMotionBlurEnabled) {
        TriangleMesh blurData;
        blurData.vertices.reserve(isomesh.vertices.size());
        double dt = _currentFrameDeltaTime;
        for (size_t i = 0; i < isomesh.vertices.size(); i++) {
            vmath::vec3 p = isomesh.vertices[i];
            vmath::vec3 t = _MACVelocity.evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
            blurData.vertices.push_back(t);
        }

        _getTriangleMeshFileData(blurData, _outputData.surfaceBlurData);
        _outputData.frameData.surfaceblur.enabled = 1;
        _outputData.frameData.surfaceblur.vertices = (int)blurData.vertices.size();
        _outputData.frameData.surfaceblur.triangles = (int)blurData.triangles.size();
        _outputData.frameData.surfaceblur.bytes = (unsigned int)_outputData.surfaceBlurData.size();
    }

    vmath::vec3 scale(_domainScale, _domainScale, _domainScale);
    isomesh.scale(scale);
    isomesh.translate(_domainOffset);
    previewmesh.scale(scale);
    previewmesh.translate(_domainOffset);

    _getTriangleMeshFileData(isomesh, _outputData.surfaceData);

    _outputData.frameData.surface.enabled = 1;
    _outputData.frameData.surface.vertices = (int)isomesh.vertices.size();
    _outputData.frameData.surface.triangles = (int)isomesh.triangles.size();
    _outputData.frameData.surface.bytes = (unsigned int)_outputData.surfaceData.size();

    if (_isPreviewSurfaceMeshEnabled) {
        _getTriangleMeshFileData(previewmesh, _outputData.surfacePreviewData);
        _outputData.frameData.preview.enabled = 1;
        _outputData.frameData.preview.vertices = (int)previewmesh.vertices.size();
        _outputData.frameData.preview.triangles = (int)previewmesh.triangles.size();
        _outputData.frameData.preview.bytes = (unsigned int)_outputData.surfacePreviewData.size();
    }

    t.stop();
    _timingData.outputMeshSimulationData += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Generate Surface Mesh");
}

void FluidSimulation::_launchOutputSurfaceMeshThread() {
    // Particles will be deleted within the thread after use
    std::vector<vmath::vec3> *particles = new std::vector<vmath::vec3>();
    particles->reserve(_markerParticles.size());
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        particles->push_back(_markerParticles[i].position);
    }

    // solidSDF will be deleted within the thread after use
    MeshLevelSet *tempSolidSDF = new MeshLevelSet();
    tempSolidSDF->constructMinimalSignedDistanceField(_solidSDF);

    _mesherThread = std::thread(&FluidSimulation::_outputSurfaceMeshThread, this,
                                particles, tempSolidSDF);

    if (!_isAsynchronousMeshingEnabled) {
        _mesherThread.join();
    }
}

void FluidSimulation::_joinOutputSurfaceMeshThread() {
    _mesherThread.join();
}

void FluidSimulation::_outputDiffuseMaterial() {
    if (!_isDiffuseMaterialOutputEnabled) { return; }

    if (_isDiffuseMaterialFilesSeparated) {
        _diffuseMaterial.getFoamParticleFileDataWWP(_outputData.diffuseFoamData);
        _diffuseMaterial.getBubbleParticleFileDataWWP(_outputData.diffuseBubbleData);
        _diffuseMaterial.getSprayParticleFileDataWWP(_outputData.diffuseSprayData);

        int nspray, nbubble, nfoam;
        _diffuseMaterial.getDiffuseParticleTypeCounts(&nfoam, 
                                                      &nbubble, 
                                                      &nspray);
        _outputData.frameData.foam.enabled = 1;
        _outputData.frameData.foam.vertices = nfoam;
        _outputData.frameData.foam.triangles = 0;
        _outputData.frameData.foam.bytes = _outputData.diffuseFoamData.size();

        _outputData.frameData.bubble.enabled = 1;
        _outputData.frameData.bubble.vertices = nbubble;
        _outputData.frameData.bubble.triangles = 0;
        _outputData.frameData.bubble.bytes = _outputData.diffuseBubbleData.size();

        _outputData.frameData.spray.enabled = 1;
        _outputData.frameData.spray.vertices = nspray;
        _outputData.frameData.spray.triangles = 0;
        _outputData.frameData.spray.bytes = _outputData.diffuseSprayData.size();

        if (_isWhitewaterMotionBlurEnabled) {
            double dt = _currentFrameDeltaTime;
            _diffuseMaterial.getFoamParticleBlurFileDataWWP(_outputData.diffuseFoamBlurData, dt);
            _diffuseMaterial.getBubbleParticleBlurFileDataWWP(_outputData.diffuseBubbleBlurData, dt);
            _diffuseMaterial.getSprayParticleBlurFileDataWWP(_outputData.diffuseSprayBlurData, dt);

            _outputData.frameData.foamblur.enabled = 1;
            _outputData.frameData.foamblur.vertices = nfoam;
            _outputData.frameData.foamblur.triangles = 0;
            _outputData.frameData.foamblur.bytes = (unsigned int)_outputData.diffuseFoamBlurData.size();

            _outputData.frameData.bubbleblur.enabled = 1;
            _outputData.frameData.bubbleblur.vertices = nbubble;
            _outputData.frameData.bubbleblur.triangles = 0;
            _outputData.frameData.bubbleblur.bytes = (unsigned int)_outputData.diffuseBubbleBlurData.size();

            _outputData.frameData.sprayblur.enabled = 1;
            _outputData.frameData.sprayblur.vertices = nspray;
            _outputData.frameData.sprayblur.triangles = 0;
            _outputData.frameData.sprayblur.bytes = (unsigned int)_outputData.diffuseSprayBlurData.size();
        }

    } else {
        _diffuseMaterial.getDiffuseParticleFileDataWWP(_outputData.diffuseData);
    }
}

float FluidSimulation::_calculateParticleSpeedPercentileThreshold(float pct) {
    float eps = 1e-3;
    float maxs = fmax(_getMaximumMarkerParticleSpeed(), eps);
    float invmax = 1.0f / maxs;
    int nbins = 10000;
    std::vector<int> binCounts(nbins, 0);
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        float s = vmath::length(_markerParticles[i].velocity);
        int binidx = (int)fmin(floor(s * invmax * (nbins - 1)), nbins - 1);
        binCounts[binidx]++;
    }

    float pthresh = 0.995;
    int threshCount = floor(pthresh * _markerParticles.size());
    int currentCount = 0;
    float slimit = maxs;
    for (size_t i = 0; i < binCounts.size(); i++) {
        currentCount += binCounts[i];
        if (currentCount >= threshCount) {
            slimit = ((float)i / (float)(nbins - 1)) * maxs;
            break;
        }
    }

    return fmax(slimit, eps);
}

void FluidSimulation::_outputFluidParticles() {
    if (!_isFluidParticleOutputEnabled) { return; }

    float maxSpeed = _calculateParticleSpeedPercentileThreshold(0.995);
    float invmax = 1.0f / maxSpeed;
    int nbins = 1024;
    std::vector<int> binCounts(nbins, 0);
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        float s = vmath::length(_markerParticles[i].velocity);
        int binidx = (int)fmin(floor(s * invmax * (nbins - 1)), nbins - 1);
        binCounts[binidx]++;
    }

    std::vector<int> binStarts(nbins, 0);
    std::vector<float> binSpeeds(nbins, 0);
    int currentIdx = 0;
    for (size_t i = 0; i < binCounts.size(); i++) {
        binStarts[i] = currentIdx;
        currentIdx += binCounts[i];

        binSpeeds[i] = ((float)i / (float)(nbins - 1)) * maxSpeed;
    }

    std::vector<vmath::vec3> sortedParticles(_markerParticles.size());
    std::vector<int> binStartsCopy = binStarts;
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        float s = vmath::length(_markerParticles[i].velocity);
        int binidx = (int)fmin(floor(s * invmax * (nbins - 1)), nbins - 1);
        int vidx = binStartsCopy[binidx];
        binStartsCopy[binidx]++;

        vmath::vec3 p = _markerParticles[i].position;
        p *= _domainScale;
        p += _domainOffset;
        sortedParticles[vidx] = p;
    }

    _getFluidParticleFileData(sortedParticles, binStarts, binSpeeds, 
                              _outputData.fluidParticleData);

    _outputData.frameData.particles.enabled = 1;
    _outputData.frameData.particles.vertices = (int)sortedParticles.size();
    _outputData.frameData.particles.triangles = 0;
    _outputData.frameData.particles.bytes = _outputData.fluidParticleData.size();
}

void FluidSimulation::_outputInternalObstacleMesh() {
    if (!_isInternalObstacleMeshOutputEnabled) { return; }

    ScalarField field = ScalarField(_isize + 1, _jsize + 1, _ksize + 1, _dx);
    field.setSurfaceThreshold(0.0);
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                field.setScalarFieldValue(i, j, k, -_solidSDF(i, j, k));
                if (i <= 1 || j <= 1 || k <= 1 || 
                    i >= _isize - 1 || j >= _jsize - 1 || k >= _ksize - 1) {
                    field.setScalarFieldValue(i, j, k, _solidSDF(i, j, k));
                }
            }
        }
    }

    Polygonizer3d polygonizer(&field);
    TriangleMesh sdfmesh = polygonizer.polygonizeSurface();
    
    vmath::vec3 scale(_domainScale, _domainScale, _domainScale);
    sdfmesh.scale(scale);
    sdfmesh.translate(_domainOffset);

    _getTriangleMeshFileData(sdfmesh, _outputData.internalObstacleMeshData);

    _outputData.frameData.obstacle.enabled = 1;
    _outputData.frameData.obstacle.vertices = (int)sdfmesh.vertices.size();
    _outputData.frameData.obstacle.triangles = (int)sdfmesh.triangles.size();
    _outputData.frameData.obstacle.bytes = _outputData.internalObstacleMeshData.size();
}

void FluidSimulation::_outputSimulationLogFile() {
    _outputData.logfileData = _logfile.flush();
}

void FluidSimulation::_outputSimulationData() {
    if (_currentFrameTimeStepNumber == 0) {
        _logfile.logString(_logfile.getTime() + " BEGIN       Generate Output Data");

        StopWatch t;
        t.start();
        _launchOutputSurfaceMeshThread();
        _outputDiffuseMaterial();
        _outputFluidParticles();
        _outputInternalObstacleMesh();
        t.stop();

        _timingData.outputNonMeshSimulationData += t.getTime();
        _logfile.logString(_logfile.getTime() + " COMPLETE    Generate Output Data");
    }

    if (_isLastFrameTimeStep && _isAsynchronousMeshingEnabled) {
        _joinOutputSurfaceMeshThread();
    }
}

/********************************************************************************
    TIME STEP
********************************************************************************/

void FluidSimulation::_stepFluid(double dt) {
    if (!_isSkippedFrame) {
        _launchUpdateObstacleObjectsThread(dt);
        _joinUpdateObstacleObjectsThread();
        _launchUpdateLiquidLevelSetThread();
        _joinUpdateLiquidLevelSetThread();
        _launchAdvectVelocityFieldThread();
        _joinAdvectVelocityFieldThread();
        _launchCalculateFluidCurvatureGridThread();
        _saveVelocityField();
        _applyBodyForcesToVelocityField(dt);
        _applyViscosityToVelocityField(dt);

        if (_isSurfaceTensionEnabled) {
            _joinCalculateFluidCurvatureGridThread();
        }

        _pressureSolve(dt);
        _constrainVelocityFields();

        if (_isDiffuseMaterialOutputEnabled) {
            _joinCalculateFluidCurvatureGridThread();
        }

        _updateDiffuseMaterial(dt);

        if (_isSheetSeedingEnabled) {
            _joinCalculateFluidCurvatureGridThread();
        }

        _updateSheetSeeding();
        _updateMarkerParticleVelocities();
        _deleteSavedVelocityField();
        _advanceMarkerParticles(dt);
        _updateFluidObjects();
        _outputSimulationData();
    }
}

double FluidSimulation::_getMaximumMeshObjectFluidVelocity(MeshObject *object, 
                                                           vmath::vec3 fluidVelocity) {
    double maxu = 0.0;
    if (object->isAppendObjectVelocityEnabled()) {
        RigidBodyVelocity rv = object->getRigidBodyVelocity(_currentFrameDeltaTime);
        TriangleMesh m = object->getMesh();
        for (size_t vidx = 0; vidx < m.vertices.size(); vidx++) {
            vmath::vec3 vert = m.vertices[vidx];
            vmath::vec3 rotv = vmath::cross(rv.angular * rv.axis, vert - rv.centroid);
            vmath::vec3 v = fluidVelocity + rv.linear + rotv;
            maxu = fmax(v.length(), maxu);
        }
    } else {
        maxu = fmax(fluidVelocity.length(), maxu);
    }

    return maxu;
}

double FluidSimulation::_predictMaximumMarkerParticleSpeed(double dt) {
    double maxu = 0.0;
    for (size_t i = 0; i < _addedFluidMeshObjectQueue.size(); i++) {
        MeshObject object = _addedFluidMeshObjectQueue[i].object;
        vmath::vec3 fluidVelocity = _addedFluidMeshObjectQueue[i].velocity;
        maxu = fmax(_getMaximumMeshObjectFluidVelocity(&object, fluidVelocity), maxu);
    }

    for (size_t i = 0; i < _meshFluidSources.size(); i++) {
        MeshFluidSource *source = _meshFluidSources[i];
        if (!source->isEnabled() || !source->isInflow()) {
            continue;
        }

        MeshObject *object = source->getMeshObject();
        vmath::vec3 fluidVelocity = source->getVelocity();
        maxu = fmax(_getMaximumMeshObjectFluidVelocity(object, fluidVelocity), maxu);
    }

    maxu += vmath::length(_getConstantBodyForce()) * dt;

    return maxu;
}

double FluidSimulation::_getMaximumMarkerParticleSpeed() {
    double maxsq = 0.0;
    MarkerParticle mp;
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        mp = _markerParticles[i];
        double distsq = vmath::dot(mp.velocity, mp.velocity);
        if (distsq > maxsq) {
            maxsq = distsq;
        }
    }

    return sqrt(maxsq);
}

double FluidSimulation::_getMaximumObstacleSpeed(double dt) {
    if (!_isAdaptiveObstacleTimeSteppingEnabled) {
        return 0.0;
    }

    AABB domainBounds(0.0, 0.0, 0.0, _isize * _dx, _jsize * _dx, _ksize * _dx);

    double maxu = 0.0;
    for (size_t i = 0; i < _obstacles.size(); i++) {
        MeshObject *obj = _obstacles[i];
        if (!obj->isEnabled()) {
            continue;
        }

        TriangleMesh m = obj->getMesh();
        std::vector<vmath::vec3> vels = obj->getFrameVertexVelocities(_currentFrame, dt);
        for (size_t vidx = 0; vidx < vels.size(); vidx++) {
            if (domainBounds.isPointInside(m.vertices[vidx])) {
                maxu = fmax(vels[vidx].length(), maxu);
            }
        }
    }

    return maxu;
}

double FluidSimulation::_calculateNextTimeStep(double dt) {
    double maxu = 0.0;
    if (_currentFrame == 0 && _currentFrameTimeStepNumber == 0) {
        // Fluid has not yet been added to the simulation, so estimate the
        // fluid speed
        maxu = _predictMaximumMarkerParticleSpeed(dt);
    } else {
        maxu = _getMaximumMarkerParticleSpeed();
    }
    maxu = fmax(_getMaximumObstacleSpeed(dt), maxu);

    double eps = 1e-6;
    double timeStep = _CFLConditionNumber * _dx / (maxu + eps);

    if (_isSurfaceTensionEnabled) {
        double restriction = sqrt(_dx * _dx * _dx) * sqrt(1.0 / (_surfaceTensionConstant + eps));
        timeStep = fmin(timeStep, _surfaceTensionConditionNumber * restriction);
    }

    return timeStep;
}

void FluidSimulation::_updateTimingData() {
    double diffuseCurvatureTimeFactor = 0.0;
    if (_isSurfaceTensionEnabled && _isDiffuseMaterialOutputEnabled) {
        diffuseCurvatureTimeFactor = 0.5;
    } else if (_isSurfaceTensionEnabled) {
        diffuseCurvatureTimeFactor = 0.0;
    } else if (_isDiffuseMaterialOutputEnabled) {
        diffuseCurvatureTimeFactor = 1.0;
    }

    _timingData.normalizeTimes();
    TimingData tdata = _timingData;
    FluidSimulationTimingStats tstats;
    tstats.total = tdata.frameTime;
    tstats.mesh = tdata.outputNonMeshSimulationData + tdata.outputMeshSimulationData;
    tstats.advection = tdata.advectVelocityField;
    tstats.particles = tdata.updateSheetSeeding + 
                       tdata.updateMarkerParticleVelocities + 
                       tdata.advanceMarkerParticles + 
                       tdata.updateLiquidLevelSet;
    tstats.pressure = tdata.pressureSolve;
    tstats.diffuse = diffuseCurvatureTimeFactor * tdata.calculateFluidCurvatureGrid + tdata.updateDiffuseMaterial;
    tstats.viscosity = tdata.applyViscosityToVelocityField;
    tstats.objects = tdata.updateObstacleObjects + tdata.updateFluidObjects;
    _outputData.frameData.timing = tstats;
}

void FluidSimulation::_logFrameInfo() {
    struct PrintData {
        PrintData() {}
        PrintData(std::string s, double t) : str(s), time(t) {}
        std::string str;
        double time = 0.0;
    };

    TimingData tdata = _timingData;
    std::vector<PrintData> data({
        PrintData("Update Obstacle Objects              ", tdata.updateObstacleObjects),
        PrintData("Update Liquid Level Set              ", tdata.updateLiquidLevelSet),
        PrintData("Advect Velocity Field                ", tdata.advectVelocityField),
        PrintData("Save Velocity Field                  ", tdata.saveVelocityField),
        PrintData("Calculate Surface Curvature          ", tdata.calculateFluidCurvatureGrid),
        PrintData("Apply Body Forces                    ", tdata.applyBodyForcesToVelocityField),
        PrintData("Apply Viscosity                      ", tdata.applyViscosityToVelocityField),
        PrintData("Solve Pressure System                ", tdata.pressureSolve),
        PrintData("Constrain Velocity Fields            ", tdata.constrainVelocityFields),
        PrintData("Simulate Diffuse Material            ", tdata.updateDiffuseMaterial),
        PrintData("Update Sheet Seeding                 ", tdata.updateSheetSeeding),
        PrintData("Update Marker Particle Velocities    ", tdata.updateMarkerParticleVelocities),
        PrintData("Delete Saved Velocity Field          ", tdata.deleteSavedVelocityField),
        PrintData("Advance Marker Particles             ", tdata.advanceMarkerParticles),
        PrintData("Update Fluid Objects                 ", tdata.updateFluidObjects),
        PrintData("Output Simulation Data               ", tdata.outputNonMeshSimulationData),
        PrintData("Generate Surface Mesh                ", tdata.outputMeshSimulationData)
    });

    _logfile.logString("*** Frame Timing Stats ***");
    _logfile.newline();

    for (size_t i = 0; i < data.size(); i++) {
        std::stringstream ss;
        ss << std::fixed << std::setw(8) << std::setprecision(3) << data[i].time;
        std::string timestr = ss.str();

        ss.str("");
        double percentval = (data[i].time / tdata.frameTime) * 100;
        ss << std::fixed << std::setprecision(1) << percentval;
        std::string pctstr = ss.str();
        if (pctstr.size() == 3) {
            pctstr.insert(0, " ");
        }

        float eps = 1e-5;
        int n = 60;
        int progress = 0;
        if (tdata.frameTime > eps) {
            progress = (data[i].time / tdata.frameTime) * n;
        }
        std::string progressBar(progress, '|');

        std::string pstring = data[i].str + timestr + "s    " + pctstr + "%  |" + progressBar;
        _logfile.logString(pstring);
    }

    _logfile.newline();
    _logfile.log("Frame Time:   ", tdata.frameTime, 3);
    _logfile.log("Total Time:   ", _totalSimulationTime, 3);
    _logfile.newline();
}

void FluidSimulation::_logStepInfo() {
    _logfile.newline();
    _logfile.logString("*** Time Step Stats ***");
    _logfile.newline();

    std::stringstream ss;
    ss << "Fluid Particles:   " << _markerParticles.size() << std::endl << 
          "Fluid Cells:       " << _getNumFluidCells();
    _logfile.logString(ss.str());

    if (_isDiffuseMaterialOutputEnabled) {
        int spraycount, bubblecount, foamcount;
        _diffuseMaterial.getDiffuseParticleTypeCounts(&foamcount, 
                                                      &bubblecount, 
                                                      &spraycount);
        std::stringstream dss;
        dss << "Diffuse Particles: " << getNumDiffuseParticles() << std::endl << 
          "    Foam:          " << foamcount << std::endl << 
          "    Bubble:        " << bubblecount << std::endl << 
          "    Spray:         " << spraycount;
        _logfile.newline();
        _logfile.logString(dss.str());
    }

    if (_pressureSolverStatus.size() > 0) {
        _logfile.newline();
        _logfile.logString(_pressureSolverStatus);
    }
    if (_isViscosityEnabled && _viscositySolverStatus.size() > 0) {
        _logfile.newline();
        _logfile.logString(_viscositySolverStatus);
    }
    _logfile.newline();
}

void FluidSimulation::_logGreeting() {
    _logfile.separator();
    std::stringstream ss;
    ss << "Fluid Engine Version " << VersionUtils::getLabel();
    _logfile.logString(ss.str());
    _logfile.separator();
}

void FluidSimulation::update(double dt) {
    if (!_isSimulationInitialized) {
        std::string msg = "Error: FluidSimulation must be initialized before update.\n";
        throw std::runtime_error(msg);
    }

    if (dt < 0.0) {
        std::string msg = "Error: delta time must be greater than or equal to 0.\n";
        msg += "delta time: " + _toString(dt) + "\n";
        throw std::domain_error(msg);
    }

    _timingData = TimingData();

    StopWatch frameTimer;
    frameTimer.start();

    double epsdt = 1e-6;
    _isZeroLengthDeltaTime = dt < epsdt;
    dt = std::max(dt, epsdt);

    _isCurrentFrameFinished = false;

    _currentFrameDeltaTime = dt;
    _currentFrameDeltaTimeRemaining = dt;
    _currentFrameTimeStepNumber = 0;
    _isSkippedFrame = _isZeroLengthDeltaTime && _outputData.isInitialized;
    double substepTime = _currentFrameDeltaTime / (double)_minFrameTimeSteps;

    double eps = 1e-9;
    do {
        StopWatch stepTimer;
        stepTimer.start();

        _currentFrameTimeStep = fmin(_calculateNextTimeStep(dt), 
                                     _currentFrameDeltaTimeRemaining);

        double timeCompleted = _currentFrameDeltaTime - _currentFrameDeltaTimeRemaining;
        double stepLimit = (_currentFrameTimeStepNumber + 1) * substepTime;
        if (timeCompleted + _currentFrameTimeStep > stepLimit) {
            _currentFrameTimeStep = fmin(substepTime, _currentFrameDeltaTimeRemaining);
        }

        if (_currentFrameTimeStepNumber == _maxFrameTimeSteps - 1) {
            _currentFrameTimeStep = _currentFrameDeltaTimeRemaining;
        }

        _currentFrameDeltaTimeRemaining -= _currentFrameTimeStep;
        _isLastFrameTimeStep = fabs(_currentFrameDeltaTimeRemaining) < eps;

        double frameProgress = 100 * (1.0 - _currentFrameDeltaTimeRemaining/dt);
        std::ostringstream ss;
        ss << "Frame: " << _currentFrame << " (Step " << _currentFrameTimeStepNumber + 1 << ")\n" <<
              "Step time: " << _currentFrameTimeStep << " (" << frameProgress << "% of frame)\n";

        _logfile.separator();
        _logfile.timestamp();
        _logfile.newline();
        _logfile.log(ss);
        _logfile.newline();

        _stepFluid(_currentFrameTimeStep);
        _logStepInfo();

        stepTimer.stop();
        _logfile.log("Step Update Time:   ", stepTimer.getTime(), 3);
        _logfile.newline();

        _currentFrameTimeStepNumber++;
    } while (_currentFrameDeltaTimeRemaining > eps);

    frameTimer.stop();
    _timingData.frameTime = frameTimer.getTime();
    _totalSimulationTime += frameTimer.getTime();

    _updateTimingData();
    _logFrameInfo();

    _outputData.frameData.frame = _currentFrame;
    _outputData.frameData.substeps = _currentFrameTimeStepNumber;
    _outputData.frameData.deltaTime = dt;
    _outputData.frameData.timing.total = frameTimer.getTime();
    _outputData.frameData.fluidParticles = (int)_markerParticles.size();
    _outputData.frameData.diffuseParticles = (int)(_diffuseMaterial.getDiffuseParticles()->size());
    _outputData.isInitialized = true;

    _outputSimulationLogFile();

    _currentFrame++;

    _isCurrentFrameFinished = true;
}