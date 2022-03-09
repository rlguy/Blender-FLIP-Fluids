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

void FluidSimulation::upscaleOnInitialization(int isizePrev, int jsizePrev, int ksizePrev, double dxPrev) { 
    if (isizePrev <= 0 || jsizePrev <= 0 || ksizePrev <= 0 || dxPrev <= 0.0) {
        std::string msg = "Error: dimensions and cell size must be greater than 0.\n";
        msg += "grid: " + _toString(isizePrev) + _toString(jsizePrev) + _toString(ksizePrev) + " " + _toString(dxPrev) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " upscaleOnInitialization: " << isizePrev << " " << jsizePrev << " " << ksizePrev << " " << dxPrev << std::endl);

    _isUpscalingOnInitializationEnabled = true;
    _upscalingPreviousIsize = isizePrev;
    _upscalingPreviousJsize = jsizePrev;
    _upscalingPreviousKsize = ksizePrev;
    _upscalingPreviousCellSize = dxPrev;
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

void FluidSimulation::enableSurfaceVelocityAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceVelocityAttribute" << std::endl);

    _isSurfaceVelocityAttributeEnabled = true;
}

void FluidSimulation::disableSurfaceVelocityAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceVelocityAttribute" << std::endl);

    _isSurfaceVelocityAttributeEnabled = false;
}

bool FluidSimulation::isSurfaceVelocityAttributeEnabled() {
    return _isSurfaceVelocityAttributeEnabled;
}

void FluidSimulation::enableWhitewaterVelocityAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableWhitewaterVelocityAttribute" << std::endl);

    _isWhitewaterVelocityAttributeEnabled = true;
}

void FluidSimulation::disableWhitewaterVelocityAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableWhitewaterVelocityAttribute" << std::endl);

    _isWhitewaterVelocityAttributeEnabled = false;
}

bool FluidSimulation::isWhitewaterVelocityAttributeEnabled() {
    return _isWhitewaterVelocityAttributeEnabled;
}

void FluidSimulation::enableSurfaceVorticityAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceVorticityAttribute" << std::endl);

    _isSurfaceVorticityAttributeEnabled = true;
}

void FluidSimulation::disableSurfaceVorticityAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceVorticityAttribute" << std::endl);

    _isSurfaceVorticityAttributeEnabled = false;
}

bool FluidSimulation::isSurfaceVorticityAttributeEnabled() {
    return _isSurfaceVorticityAttributeEnabled;
}

void FluidSimulation::enableSurfaceSpeedAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceSpeedAttribute" << std::endl);

    _isSurfaceSpeedAttributeEnabled = true;
}

void FluidSimulation::disableSurfaceSpeedAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceSpeedAttribute" << std::endl);

    _isSurfaceSpeedAttributeEnabled = false;
}

bool FluidSimulation::isSurfaceSpeedAttributeEnabled() {
    return _isSurfaceSpeedAttributeEnabled;
}

void FluidSimulation::enableSurfaceAgeAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceAgeAttribute" << std::endl);

    _isSurfaceAgeAttributeEnabled = true;
}

void FluidSimulation::disableSurfaceAgeAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceAgeAttribute" << std::endl);

    _isSurfaceAgeAttributeEnabled = false;
}

bool FluidSimulation::isSurfaceAgeAttributeEnabled() {
    return _isSurfaceAgeAttributeEnabled;
}

void FluidSimulation::enableSurfaceColorAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceColorAttribute" << std::endl);

    _isSurfaceSourceColorAttributeEnabled = true;
}

void FluidSimulation::disableSurfaceColorAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceColorAttribute" << std::endl);

    _isSurfaceSourceColorAttributeEnabled = false;
}

bool FluidSimulation::isSurfaceColorAttributeEnabled() {
    return _isSurfaceSourceColorAttributeEnabled;
}

void FluidSimulation::enableSurfaceSourceIDAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSurfaceSourceIDAttribute" << std::endl);

    _isSurfaceSourceIDAttributeEnabled = true;
}

void FluidSimulation::disableSurfaceSourceIDAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSurfaceSourceIDAttribute" << std::endl);

    _isSurfaceSourceIDAttributeEnabled = false;
}

bool FluidSimulation::isSurfaceSourceIDAttributeEnabled() {
    return _isSurfaceSourceIDAttributeEnabled;
}

void FluidSimulation::enableWhitewaterIDAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableWhitewaterIDAttribute" << std::endl);

    _isWhitewaterIDAttributeEnabled = true;
}

void FluidSimulation::disableWhitewaterIDAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableWhitewaterIDAttribute" << std::endl);

    _isWhitewaterIDAttributeEnabled = false;
}

bool FluidSimulation::isWhitewaterIDAttributeEnabled() {
    return _isWhitewaterIDAttributeEnabled;
}

void FluidSimulation::enableWhitewaterLifetimeAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableWhitewaterLifetimeAttribute" << std::endl);

    _isWhitewaterLifetimeAttributeEnabled = true;
}

void FluidSimulation::disableWhitewaterLifetimeAttribute() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableWhitewaterLifetimeAttribute" << std::endl);

    _isWhitewaterLifetimeAttributeEnabled = false;
}

bool FluidSimulation::isWhitewaterLifetimeAttributeEnabled() {
    return _isWhitewaterLifetimeAttributeEnabled;
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

void FluidSimulation::enableForceFieldDebugOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableForceFieldDebugOutput" << std::endl);

    _isForceFieldDebugOutputEnabled = true;
}

void FluidSimulation::disableForceFieldDebugOutput() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableForceFieldDebugOutput" << std::endl);

    _isForceFieldDebugOutputEnabled = false;
}

bool FluidSimulation::isForceFieldDebugOutputEnabled() {
    return _isForceFieldDebugOutputEnabled;
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


void FluidSimulation::enableDiffuseDust() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableDiffuseDust" << std::endl);

    _diffuseMaterial.enableDust();
}

void FluidSimulation::disableDiffuseDust() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableDiffuseDust" << std::endl);

    _diffuseMaterial.disableDust();
}

bool FluidSimulation::isDiffuseDustEnabled() {
    return _diffuseMaterial.isDustEnabled();
}

void FluidSimulation::enableBoundaryDiffuseDustEmission() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableBoundaryDiffuseDustEmission" << std::endl);

    _diffuseMaterial.enableBoundaryDustEmission();
}

void FluidSimulation::disableBoundaryDiffuseDustEmission() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableBoundaryDiffuseDustEmission" << std::endl);

    _diffuseMaterial.disableBoundaryDustEmission();
}

bool FluidSimulation::isBoundaryDustDiffuseEmissionEnabled() {
    return _diffuseMaterial.isBoundaryDustEmissionEnabled();
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

double FluidSimulation::getDustParticleLifetimeModifier() {
    return _diffuseMaterial.getDustParticleLifetimeModifier();
}

void FluidSimulation::setDustParticleLifetimeModifier(double modifier) {
    if (modifier < 0) {
        std::string msg = "Error: dust lifetime modifier must be greater than or equal to 0.\n";
        msg += "modifier: " + _toString(modifier) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDustParticleLifetimeModifier: " << modifier << std::endl);

    _diffuseMaterial.setDustParticleLifetimeModifier(modifier);
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

double FluidSimulation::getDiffuseParticleDustEmissionRate() {
    return _diffuseMaterial.getDiffuseParticleDustEmissionRate();
}

void FluidSimulation::setDiffuseParticleDustEmissionRate(double r) {
    if (r < 0) {
        std::string msg = "Error: dust emission rate must be greater than or equal to 0.\n";
        msg += "rate: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseParticleDustEmissionRate: " << r << std::endl);

    _diffuseMaterial.setDiffuseParticleDustEmissionRate(r);
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

double FluidSimulation::getDiffuseDustDragCoefficient() {
    return _diffuseMaterial.getDustDragCoefficient();
}

void FluidSimulation::setDiffuseDustDragCoefficient(double d) {
    if (d < 0.0 || d > 1.0) {
        std::string msg = "Error: drag coefficient must be in range [0.0, 1.0].\n";
        msg += "coefficient: " + _toString(d) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseDustDragCoefficient: " << d << std::endl);

    _diffuseMaterial.setDustDragCoefficient(d);
}

double FluidSimulation::getDiffuseBubbleBouyancyCoefficient() {
    return _diffuseMaterial.getBubbleBouyancyCoefficient();
}

void FluidSimulation::setDiffuseBubbleBouyancyCoefficient(double b) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseBubbleBouyancyCoefficient: " << b << std::endl);

    _diffuseMaterial.setBubbleBouyancyCoefficient(b);
}

double FluidSimulation::getDiffuseDustBouyancyCoefficient() {
    return _diffuseMaterial.getDustBouyancyCoefficient();
}

void FluidSimulation::setDiffuseDustBouyancyCoefficient(double b) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseDustBouyancyCoefficient: " << b << std::endl);

    _diffuseMaterial.setDustBouyancyCoefficient(b);
}

double FluidSimulation::getDiffuseSprayDragCoefficient() {
    return _diffuseMaterial.getSprayDragCoefficient();
}

void FluidSimulation::setDiffuseSprayDragCoefficient(double d) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseSprayDragCoefficient: " << d << std::endl);

    _diffuseMaterial.setSprayDragCoefficient(d);
}

double FluidSimulation::getDiffuseSprayEmissionSpeed() {
    return _diffuseMaterial.getSprayEmissionSpeed();
}

void FluidSimulation::setDiffuseSprayEmissionSpeed(double d) {
    if (d < 1.0) {
        std::string msg = "Error: spray emission speed must be greater than or equal to 1.0.\n";
        msg += "speed: " + _toString(d) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseSprayEmissionSpeed: " << d << std::endl);

    _diffuseMaterial.setSprayEmissionSpeed(d);
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

LimitBehaviour FluidSimulation::getDiffuseDustLimitBehaviour() {
    return _diffuseMaterial.getDustLimitBehaviour();
}

void FluidSimulation::setDiffuseDustLimitBehaviour(LimitBehaviour b) {
    std::string typestr;
    if (b == LimitBehaviour::collide) {
        typestr = "collide";
    } else if (b == LimitBehaviour::ballistic) {
        typestr = "ballistic";
    } else if (b == LimitBehaviour::kill) {
        typestr = "kill";
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseDustLimitBehaviour: " << typestr << std::endl);

    _diffuseMaterial.setDustLimitBehavour(b);
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

std::vector<bool> FluidSimulation::getDiffuseDustActiveBoundarySides() {
    return _diffuseMaterial.getDustActiveBoundarySides();
}

void FluidSimulation::setDiffuseDustActiveBoundarySides(std::vector<bool> active) {
    if (active.size() != 6) {
        std::string msg = "Error: dust active boundary vector must be of length 6.\n";
        msg += "length: " + _toString(active.size()) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setDiffuseDustActiveBoundarySides: " << 
                 active[0] << " " << active[1] << " " << active[2] << " " << 
                 active[3] << " " << active[4] << " " << active[5] << std::endl);

    _diffuseMaterial.setDustActiveBoundarySides(active);
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

void FluidSimulation::enableForceFields() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableForceFields" << std::endl);

    _isForceFieldsEnabled = true;
}

void FluidSimulation::disableForceFields() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableForceFields" << std::endl);

    _isForceFieldsEnabled = false;
}

bool FluidSimulation::isForceFieldsEnabled() {
    return _isForceFieldsEnabled;
}

int FluidSimulation::getForceFieldReductionLevel() {
    return _currentFrame;
}

void FluidSimulation::setForceFieldReductionLevel(int level) {
    if (level < 1) {
        std::string msg = "Error: reduction level must be greater than or equal to 1.\n";
        msg += "reduction level: " + _toString(level) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setForceFieldReductionLevel: " << level << std::endl);

    _forceFieldReductionLevel = level;
}

ForceFieldGrid* FluidSimulation::getForceFieldGrid() {
    if (!_isForceFieldsEnabled) {
        std::string msg = "Error: force fields must be enabled before using this method.\n";
        msg += "is force fields enabled: " + _toString(_isForceFieldsEnabled) + "\n";
        throw std::domain_error(msg);
    }

    return &_forceFieldGrid;
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

double FluidSimulation::getViscositySolverErrorTolerance() {
    return _viscositySolverErrorTolerance;
}

void FluidSimulation::setViscositySolverErrorTolerance(double tol) {
    if (tol < 0.0) {
        std::string msg = "Error: viscosity solver error tolerance must be greater than or equal to 0.\n";
        msg += "error tolerance: " + _toString(tol) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setViscositySolverErrorTolerance: " << tol << std::endl);

    _viscositySolverErrorTolerance = tol;
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

bool FluidSimulation::isSmoothSurfaceTensionKernelEnabled() {
    return _isSmoothSurfaceTensionKernelEnabled;
}

void FluidSimulation::enableSmoothSurfaceTensionKernel() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableSmoothSurfaceTensionKernel" << std::endl);

    _isSmoothSurfaceTensionKernelEnabled = true;
}

void FluidSimulation::disableSmoothSurfaceTensionKernel() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableSmoothSurfaceTensionKernel" << std::endl);

    _isSmoothSurfaceTensionKernelEnabled = false;
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

void FluidSimulation::enableAdaptiveForceFieldTimeStepping() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " enableAdaptiveForceFieldTimeStepping" << std::endl);

    _isAdaptiveForceFieldTimeSteppingEnabled = true;
}

void FluidSimulation::disableAdaptiveForceFieldTimeStepping() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " disableAdaptiveForceFieldTimeStepping" << std::endl);

    _isAdaptiveForceFieldTimeSteppingEnabled = false;
}

bool FluidSimulation::isAdaptiveForceFieldTimeSteppingEnabled() {
    return _isAdaptiveForceFieldTimeSteppingEnabled;
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

void FluidSimulation::setVelocityTransferMethodFLIP() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setVelocityTransferMethodFLIP" << std::endl);

    _velocityTransferMethod = VelocityTransferMethod::FLIP;
}

void FluidSimulation::setVelocityTransferMethodAPIC() {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " setVelocityTransferMethodAPIC" << std::endl);

    _velocityTransferMethod = VelocityTransferMethod::APIC;
}

bool FluidSimulation::isVelocityTransferMethodFLIP() {
    return _velocityTransferMethod == VelocityTransferMethod::FLIP;
}

bool FluidSimulation::isVelocityTransferMethodAPIC() {
    return _velocityTransferMethod == VelocityTransferMethod::APIC;
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

double FluidSimulation::getPICAPICRatio() {
    return _ratioPICAPIC;
}

void FluidSimulation::setPICAPICRatio(double r) {
    if (r < 0.0 || r > 1.0) {
        std::string msg = "Error: PICAPIC ratio must be in range [0.0, 1.0].\n";
        msg += "ratio: " + _toString(r) + "\n";
        throw std::domain_error(msg);
    }

    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << 
                 " setPICAPICRatio: " << r << std::endl);

    _ratioPICAPIC = r;
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

    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    for (int i = startidx; i < endidx; i++) {
        MarkerParticle mp(positions->at(i), velocities->at(i));
        particles.push_back(mp);
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

    std::vector<vmath::vec3> *positions;
    _markerParticles.getAttributeValues("POSITION", positions);

    for (int i = startidx; i < endidx; i++) {
        particles.push_back(positions->at(i));
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

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("VELOCITY", values);

    for (int i = startidx; i < endidx; i++) {
        velocities.push_back(values->at(i));
    }

    return velocities;
}

unsigned int FluidSimulation::getNumDiffuseParticles() {
    return _diffuseMaterial.getNumDiffuseParticles();
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

    std::vector<vmath::vec3> *positions;
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("POSITION", positions);

    return *positions;
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

    std::vector<vmath::vec3> *velocities;
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("VELOCITY", velocities);
    
    return *velocities;
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

    std::vector<float> *lifetimes;
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("LIFETIME", lifetimes);
    
    return *lifetimes;
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

    std::vector<char> *types;
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("TYPE", types);
    
    return *types;
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

std::vector<char>* FluidSimulation::getSurfaceVelocityAttributeData() {
    return &_outputData.surfaceVelocityAttributeData;
}

std::vector<char>* FluidSimulation::getSurfaceVorticityAttributeData() {
    return &_outputData.surfaceVorticityAttributeData;
}

std::vector<char>* FluidSimulation::getSurfaceSpeedAttributeData() {
    return &_outputData.surfaceSpeedAttributeData;
}

std::vector<char>* FluidSimulation::getSurfaceAgeAttributeData() {
    return &_outputData.surfaceAgeAttributeData;
}

std::vector<char>* FluidSimulation::getSurfaceColorAttributeData() {
    return &_outputData.surfaceColorAttributeData;
}

std::vector<char>* FluidSimulation::getSurfaceSourceIDAttributeData() {
    return &_outputData.surfaceSourceIDAttributeData;
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

std::vector<char>* FluidSimulation::getDiffuseDustData() {
    return &_outputData.diffuseDustData;
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

std::vector<char>* FluidSimulation::getDiffuseDustBlurData() {
    return &_outputData.diffuseDustBlurData;
}

std::vector<char>* FluidSimulation::getWhitewaterFoamVelocityAttributeData() {
    return &_outputData.whitewaterFoamVelocityAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterBubbleVelocityAttributeData() {
    return &_outputData.whitewaterBubbleVelocityAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterSprayVelocityAttributeData() {
    return &_outputData.whitewaterSprayVelocityAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterDustVelocityAttributeData() {
    return &_outputData.whitewaterDustVelocityAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterFoamIDAttributeData() {
    return &_outputData.whitewaterFoamIDAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterBubbleIDAttributeData() {
    return &_outputData.whitewaterBubbleIDAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterSprayIDAttributeData() {
    return &_outputData.whitewaterSprayIDAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterDustIDAttributeData() {
    return &_outputData.whitewaterDustIDAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterFoamLifetimeAttributeData() {
    return &_outputData.whitewaterFoamLifetimeAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterBubbleLifetimeAttributeData() {
    return &_outputData.whitewaterBubbleLifetimeAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterSprayLifetimeAttributeData() {
    return &_outputData.whitewaterSprayLifetimeAttributeData;
}

std::vector<char>* FluidSimulation::getWhitewaterDustLifetimeAttributeData() {
    return &_outputData.whitewaterDustLifetimeAttributeData;
}

std::vector<char>* FluidSimulation::getFluidParticleData() {
    return &_outputData.fluidParticleData;
}

std::vector<char>* FluidSimulation::getInternalObstacleMeshData() {
    return &_outputData.internalObstacleMeshData;
}

std::vector<char>* FluidSimulation::getForceFieldDebugData() {
    return &_outputData.forceFieldDebugData;
}

std::vector<char>* FluidSimulation::getLogFileData() {
    return &_outputData.logfileData;
}

FluidSimulationFrameStats FluidSimulation::getFrameStatsData() {
    return _outputData.frameData;
}

void FluidSimulation::getMarkerParticlePositionDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("POSITION", values);

    vmath::vec3 *positions = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        positions[i - start_idx] = values->at(i) * _domainScale + _domainOffset;
    }
}

void FluidSimulation::getMarkerParticleVelocityDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("VELOCITY", values);

    vmath::vec3 *velocities = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        velocities[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getMarkerParticleAffineXDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("AFFINEX", values);

    vmath::vec3 *dataValues = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        dataValues[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getMarkerParticleAffineYDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("AFFINEY", values);

    vmath::vec3 *dataValues = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        dataValues[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getMarkerParticleAffineZDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("AFFINEZ", values);

    vmath::vec3 *dataValues = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        dataValues[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getMarkerParticleAgeDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<float> *values;
    _markerParticles.getAttributeValues("AGE", values);

    float *dataValues = (float*)data;
    for (int i = start_idx; i < end_idx; i++) {
        dataValues[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getMarkerParticleColorDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("COLOR", values);

    vmath::vec3 *dataValues = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        dataValues[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getMarkerParticleSourceIDDataRange(int start_idx, int end_idx, char *data) {
    if (start_idx < 0 || end_idx > (int)_markerParticles.size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<int> *values;
    _markerParticles.getAttributeValues("SOURCEID", values);

    int *dataValues = (int*)data;
    for (int i = start_idx; i < end_idx; i++) {
        dataValues[i - start_idx] = values->at(i);
    }
}

void FluidSimulation::getDiffuseParticlePositionDataRange(int start_idx, int end_idx, char *data) {
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    if (start_idx < 0 || end_idx > (int)dps->size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *particlePositions;
    dps->getAttributeValues("POSITION", particlePositions);

    vmath::vec3 *positions = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        positions[i - start_idx] = particlePositions->at(i) * _domainScale + _domainOffset;
    }
}

void FluidSimulation::getDiffuseParticleVelocityDataRange(int start_idx, int end_idx, char *data) {
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    if (start_idx < 0 || end_idx > (int)dps->size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<vmath::vec3> *particleVelocities;
    dps->getAttributeValues("VELOCITY", particleVelocities);

    vmath::vec3 *velocities = (vmath::vec3*)data;
    for (int i = start_idx; i < end_idx; i++) {
        velocities[i - start_idx] = particleVelocities->at(i);
    }
}

void FluidSimulation::getDiffuseParticleLifetimeDataRange(int start_idx, int end_idx, char *data) {
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    if (start_idx < 0 || end_idx > (int)dps->size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<float> *particleLifetimes;
    dps->getAttributeValues("LIFETIME", particleLifetimes);

    float *lifetimes = (float*)data;
    for (int i = start_idx; i < end_idx; i++) {
        lifetimes[i - start_idx] = particleLifetimes->at(i);
    }
}

void FluidSimulation::getDiffuseParticleTypeDataRange(int start_idx, int end_idx, char *data) {
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    if (start_idx < 0 || end_idx > (int)dps->size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<char> *particleTypes;
    dps->getAttributeValues("TYPE", particleTypes);

    for (int i = start_idx; i < end_idx; i++) {
        data[i - start_idx] = particleTypes->at(i);
    }
}

void FluidSimulation::getDiffuseParticleIdDataRange(int start_idx, int end_idx, char *data) {
    ParticleSystem *dps = _diffuseMaterial.getDiffuseParticles();
    if (start_idx < 0 || end_idx > (int)dps->size() || start_idx > end_idx) {
        std::string msg = "Error: invalid range.\n";
        msg += "range: [" + _toString(start_idx) + ", " + _toString(end_idx) + "]\n";
        throw std::domain_error(msg);
    }

    std::vector<unsigned char> *particleIds;
    dps->getAttributeValues("ID", particleIds);

    for (int i = start_idx; i < end_idx; i++) {
        data[i - start_idx] = (unsigned char)(particleIds->at(i));
    }
}

void FluidSimulation::getMarkerParticlePositionData(char *data) {
    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("POSITION", values);

    vmath::vec3 *positions = (vmath::vec3*)data;
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        positions[i] = values->at(i) * _domainScale + _domainOffset;
    }
}

void FluidSimulation::getMarkerParticleVelocityData(char *data) {
    std::vector<vmath::vec3> *values;
    _markerParticles.getAttributeValues("POSITION", values);

    vmath::vec3 *velocities = (vmath::vec3*)data;
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        velocities[i] = values->at(i);
    }
}

void FluidSimulation::getDiffuseParticlePositionData(char *data) {
    std::vector<vmath::vec3> *particlePositions;
    ParticleSystem* dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("POSITION", particlePositions);

    vmath::vec3 *positions = (vmath::vec3*)data;
    for (size_t i = 0; i < dps->size(); i++) {
        positions[i] = particlePositions->at(i) * _domainScale + _domainOffset;
    }
}

void FluidSimulation::getDiffuseParticleVelocityData(char *data) {
    std::vector<vmath::vec3> *particleVelocities;
    ParticleSystem* dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("VELOCITY", particleVelocities);

    vmath::vec3 *velocities = (vmath::vec3*)data;
    for (size_t i = 0; i < dps->size(); i++) {
        velocities[i] = particleVelocities->at(i);
    }
}

void FluidSimulation::getDiffuseParticleLifetimeData(char *data) {
    std::vector<float> *particleLifetimes;
    ParticleSystem* dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("LIFETIME", particleLifetimes);

    float *lifetimes = (float*)data;
    for (size_t i = 0; i < dps->size(); i++) {
        lifetimes[i] = particleLifetimes->at(i);
    }
}

void FluidSimulation::getDiffuseParticleTypeData(char *data) {
    std::vector<char> *particleTypes;
    ParticleSystem* dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("TYPE", particleTypes);

    for (size_t i = 0; i < dps->size(); i++) {
        data[i] = particleTypes->at(i);
    }
}

void FluidSimulation::getDiffuseParticleIdData(char *data) {
    std::vector<unsigned char> *particleIds;
    ParticleSystem* dps = _diffuseMaterial.getDiffuseParticles();
    dps->getAttributeValues("ID", particleIds);

    for (size_t i = 0; i < dps->size(); i++) {
        data[i] = (unsigned char)(particleIds->at(i));
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

void FluidSimulation::loadMarkerParticleAffineData(FluidSimulationMarkerParticleAffineData data) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " loadMarkerParticleAffineData: " << data.size << std::endl);

    if (data.size == 0) {
        return;
    }

    vmath::vec3 *affineX = (vmath::vec3*)(data.affineX);
    vmath::vec3 *affineY = (vmath::vec3*)(data.affineY);
    vmath::vec3 *affineZ = (vmath::vec3*)(data.affineZ);

    MarkerParticleAffineLoadData loadData;
    loadData.particles.reserve(data.size);

    for (unsigned int i = 0; i < (unsigned int)data.size; i++) {
        loadData.particles.push_back(MarkerParticleAffine(affineX[i], affineY[i], affineZ[i]));
    }

    _markerParticleAffineLoadQueue.push_back(loadData);

    _isMarkerParticleLoadPending = true;
}

void FluidSimulation::loadMarkerParticleAgeData(FluidSimulationMarkerParticleAgeData data) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " loadMarkerParticleAgeData: " << data.size << std::endl);

    if (data.size == 0) {
        return;
    }

    float *age = (float*)(data.age);

    MarkerParticleAgeLoadData loadData;
    loadData.particles.reserve(data.size);

    for (unsigned int i = 0; i < (unsigned int)data.size; i++) {
        loadData.particles.push_back(MarkerParticleAge(age[i]));
    }

    _markerParticleAgeLoadQueue.push_back(loadData);

    _isMarkerParticleLoadPending = true;
}

void FluidSimulation::loadMarkerParticleColorData(FluidSimulationMarkerParticleColorData data) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " loadMarkerParticleColorData: " << data.size << std::endl);

    if (data.size == 0) {
        return;
    }

    vmath::vec3 *colors = (vmath::vec3*)(data.color);

    MarkerParticleColorLoadData loadData;
    loadData.particles.reserve(data.size);

    for (unsigned int i = 0; i < (unsigned int)data.size; i++) {
        loadData.particles.push_back(MarkerParticleColor(colors[i]));
    }

    _markerParticleColorLoadQueue.push_back(loadData);

    _isMarkerParticleLoadPending = true;
}

void FluidSimulation::loadMarkerParticleSourceIDData(FluidSimulationMarkerParticleSourceIDData data) {
    _logfile.log(std::ostringstream().flush() << 
                 _logfile.getTime() << " loadMarkerParticleSourceIDData: " << data.size << std::endl);

    if (data.size == 0) {
        return;
    }

    float *sourceid = (float*)(data.sourceid);

    MarkerParticleSourceIDLoadData loadData;
    loadData.particles.reserve(data.size);

    for (unsigned int i = 0; i < (unsigned int)data.size; i++) {
        loadData.particles.push_back(MarkerParticleSourceID(sourceid[i]));
    }

    _markerParticleSourceIDLoadQueue.push_back(loadData);

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
    _domainMeshObject.setWhitewaterInfluence(1.0);
    _domainMeshObject.setDustEmissionStrength(1.0);
    _domainMeshObject.setAsDomainObject();
    t.stop();

    _logfile.log("Constructing Level Sets:       \t", t.getTime(), 4, 1);

    t.reset();
    t.start();
    _weightGrid = WeightGrid(_isize, _jsize, _ksize);
    t.stop();

    _logfile.log("Constructing Weight Grid:      \t", t.getTime(), 4, 1);

    if (_isForceFieldsEnabled) {
        t.reset();
        t.start();
        _initializeForceFieldGrid(isize, jsize, ksize, dx);
        t.stop();

        _logfile.log("Constructing Force Field Grid: \t", t.getTime(), 4, 1);
    }

    _vertx = std::vector<float>({1.912889757704761e-08, 0.4125114977359772, 0.025106651708483696, 1.89519298032792e-08, 0.4087001383304596, 0.02486945502460003, 1.8762891684787064e-08, 0.4050680696964264, 0.024176878854632378, 1.8564293213785277e-08, 0.40164390206336975, 0.023057622835040092, 1.8358651487915267e-08, 0.39845672249794006, 0.021540267392992973, 1.8148513802884736e-08, 0.3955360949039459, 0.01965351216495037, 1.7936381269123558e-08, 0.3929106295108795, 0.017425939440727234, 1.7724774536986843e-08, 0.39060941338539124, 0.014886184595525265, 1.7516201822331823e-08, 0.38866105675697327, 0.0120629221200943, 1.7313222855364074e-08, 0.3870956003665924, 0.008984759449958801, 1.711831920658824e-08, 0.38594117760658264, 0.005680307745933533, 1.693403639535518e-08, 0.38522735238075256, 0.0021782666444778442, 1.6762879084808446e-08, 0.38498273491859436, -0.0014927833108231425, 1.6602209385041533e-08, 0.3852182924747467, -0.0054040104150772095, 1.6470558250603062e-08, 0.38590875267982483, -0.009106293320655823, 1.6367973643127698e-08, 0.3870302736759186, -0.012574687600135803, 1.6294466220756476e-08, 0.3885580599308014, -0.0157841295003891, 1.62500857214809e-08, 0.3904682695865631, -0.018709644675254822, 1.6234842803442007e-08, 0.3927361071109772, -0.021326199173927307, 1.6248826284481765e-08, 0.39533868432044983, -0.023608850315213203, 1.6292009519247586e-08, 0.3982502520084381, -0.02553253062069416, 1.6364481325581437e-08, 0.40144792199134827, -0.02707223780453205, 1.6466250585267517e-08, 0.40490689873695374, -0.028202997520565987, 1.6597347496372095e-08, 0.40860286355018616, -0.02889980562031269, 1.675780403331828e-08, 0.4125114977359772, -0.0291376281529665, 1.6945687519864805e-08, 0.41658082604408264, -0.028908688575029373, 1.714251496309771e-08, 0.42041030526161194, -0.02823527529835701, 1.734646559725661e-08, 0.4239784777164459, -0.027137596160173416, 1.7555700893012727e-08, 0.42726340889930725, -0.025635767728090286, 1.7768401860962513e-08, 0.4302436411380768, -0.023749995976686478, 1.7982703326424598e-08, 0.43289676308631897, -0.02150045707821846, 1.819681294534803e-08, 0.4352017939090729, -0.018907267600297928, 1.8408861990337755e-08, 0.43713632225990295, -0.015990635380148888, 1.8617058117342822e-08, 0.43867936730384827, -0.012770702131092548, 1.8819520164470305e-08, 0.43980804085731506, -0.00926761794835329, 1.9014443353171373e-08, 0.4405013620853424, -0.005501618143171072, 1.9199990930474087e-08, 0.44073739647865295, -0.0014927882002666593, 1.935411475528781e-08, 0.44049468636512756, 0.0022758645936846733, 1.9478903823255678e-08, 0.4397837221622467, 0.005841622594743967, 1.9574439846792302e-08, 0.43863025307655334, 0.009180734865367413, 1.9640772563889186e-08, 0.43705907464027405, 0.012269417755305767, 1.9677981910604103e-08, 0.4350959360599518, 0.015083800069987774, 1.968613538849695e-08, 0.4327661097049713, 0.017600160092115402, 1.966531470998234e-08, 0.4300953447818756, 0.019794654101133347, 1.9615571389408615e-08, 0.42710843682289124, 0.02164353057742119, 1.9536983586476708e-08, 0.42383113503456116, 0.02312294766306877, 1.942963834267175e-08, 0.42028918862342834, 0.024209152907133102, 1.9293581843271568e-08, 0.41650739312171936, 0.024878334254026413, 1.871764965244438e-08, 0.4123956263065338, 0.015814287588000298, 1.8821298297666544e-08, 0.41491666436195374, 0.015664441511034966, 1.890634493406651e-08, 0.41730132699012756, 0.015225422568619251, 1.8972768245362204e-08, 0.4195334017276764, 0.014512968249619007, 1.9020591324192537e-08, 0.4215976297855377, 0.013542812317609787, 1.90497910779186e-08, 0.42347779870033264, 0.012330632656812668, 1.9060367506540388e-08, 0.42515817284584045, 0.010892223566770554, 1.9052320610057905e-08, 0.42662301659584045, 0.009243261069059372, 1.9025669928396383e-08, 0.42785707116127014, 0.007399510592222214, 1.898039414527375e-08, 0.4288441240787506, 0.005376677494496107, 1.8916516353328916e-08, 0.42956891655921936, 0.003190498799085617, 1.8834011683566132e-08, 0.4300152361392975, 0.0008567384211346507, 1.8732883688699076e-08, 0.4301673471927643, -0.0016089269192889333, 1.8607570595463585e-08, 0.43002620339393616, -0.004334617871791124, 1.847842234781183e-08, 0.4296089708805084, -0.006871927995234728, 1.8346282715242523e-08, 0.42892566323280334, -0.009211648255586624, 1.8211993690897543e-08, 0.4279862940311432, -0.011344421654939651, 1.8076336871786225e-08, 0.4267994463443756, -0.013261038810014725, 1.7940175567332517e-08, 0.4253756105899811, -0.01495223119854927, 1.7804353547035134e-08, 0.42372480034828186, -0.01640867069363594, 1.7669650631546574e-08, 0.4218555986881256, -0.01762108877301216, 1.7536931906647624e-08, 0.4197784960269928, -0.018580246716737747, 1.7407018049198086e-08, 0.4175030291080475, -0.019276846200227737, 1.7280736841485123e-08, 0.41503873467445374, -0.019701587036252022, 1.715892317122325e-08, 0.4123956263065338, -0.019845234230160713, 1.7059278434317093e-08, 0.4099656641483307, -0.01969488151371479, 1.6978688677227183e-08, 0.4076792299747467, -0.0192521084100008, 1.6917191203447146e-08, 0.40554967522621155, -0.018529431894421577, 1.6874784236620144e-08, 0.4035893976688385, -0.017539339140057564, 1.6851478434887213e-08, 0.40181127190589905, -0.01629437692463398, 1.6847293338173586e-08, 0.4002281725406647, -0.01480703242123127, 1.686226447361605e-08, 0.39885345101356506, -0.013089791871607304, 1.6896411381139842e-08, 0.3976999819278717, -0.011155144311487675, 1.6949705639035528e-08, 0.3967796862125397, -0.00901560578495264, 1.7022225407004044e-08, 0.39610686898231506, -0.006683723069727421, 1.7113949368763315e-08, 0.39569345116615295, -0.0041719237342476845, 1.7224930815018524e-08, 0.39555326104164124, -0.0014927842421457171, 1.733787868829495e-08, 0.395698219537735, 0.0009462080197408795, 1.7457489676075966e-08, 0.39612308144569397, 0.0032577356323599815, 1.7582392430881555e-08, 0.3968125879764557, 0.005425675772130489, 1.771121738158854e-08, 0.39775148034095764, 0.007433934602886438, 1.7842568311721152e-08, 0.3989240229129791, 0.009266330860555172, 1.7975093413724608e-08, 0.40031543374061584, 0.01090673916041851, 1.8107400023836817e-08, 0.4019099771976471, 0.012339038774371147, 1.8238118570934603e-08, 0.4036923944950104, 0.013547105714678764, 1.8365893694749502e-08, 0.4056479036808014, 0.014514787122607231, 1.848931852066471e-08, 0.40776029229164124, 0.015225989744067192, 1.8607011043059174e-08, 0.4100143015384674, 0.01566450111567974, 1.4082082167021781e-08, 0.29809918999671936, 0.024061284959316254, 1.1802380406322754e-08, 0.29809918999671936, -0.028092212975025177, 1.2254260717270427e-08, 0.3084370195865631, -0.028092212975025177, 1.3909454921190445e-08, 0.3084370195865631, 0.009774229489266872, 1.4007304649510388e-08, 0.30949607491493225, 0.01095371600240469, 1.4098180400878846e-08, 0.3105298578739166, 0.011998913250863552, 1.4182761631786889e-08, 0.3115479052066803, 0.012915871106088161, 1.4261666514414628e-08, 0.3125583231449127, 0.013710579834878445, 1.4335578946145233e-08, 0.31357064843177795, 0.014389178715646267, 1.4405116210980395e-08, 0.31459298729896545, 0.01495765708386898, 1.4470979969871678e-08, 0.3156353533267975, 0.015422066673636436, 1.4533768855073959e-08, 0.3167053759098053, 0.01578848622739315, 1.459418363936038e-08, 0.31781306862831116, 0.016062935814261436, 1.4652824731342662e-08, 0.3189660608768463, 0.016251495108008385, 1.4710392903793945e-08, 0.32017436623573303, 0.01636018417775631, 1.4767526756997995e-08, 0.32144656777381897, 0.016395052894949913, 1.4819219629202962e-08, 0.322704941034317, 0.01631929539144039, 1.4862181707542277e-08, 0.32391801476478577, 0.016089072450995445, 1.4895634059541862e-08, 0.32507243752479553, 0.015699943527579308, 1.4918903445959586e-08, 0.32615724205970764, 0.015147467143833637, 1.493121004614295e-08, 0.3271590769290924, 0.014427204616367817, 1.4931885061741923e-08, 0.32806697487831116, 0.013534744270145893, 1.4920189528311312e-08, 0.3288685381412506, 0.012465615756809711, 1.4895388922298025e-08, 0.3295513689517975, 0.011215408332645893, 1.4856768260074205e-08, 0.3301035463809967, 0.009779681451618671, 1.4803590353551499e-08, 0.330512672662735, 0.00815399456769228, 1.4735160647205703e-08, 0.33076730370521545, 0.006333877332508564, 1.4650745505662144e-08, 0.33085504174232483, 0.004314948804676533, 1.3234183526833476e-08, 0.33085504174232483, -0.028092216700315475, 1.3686044297855915e-08, 0.3411923944950104, -0.028092216700315475, 1.5341239389954353e-08, 0.3411923944950104, 0.009774226695299149, 1.5423538002323767e-08, 0.34213748574256897, 0.010711926966905594, 1.5505015937833377e-08, 0.34310975670814514, 0.011603672057390213, 1.5585042589805198e-08, 0.34410205483436584, 0.01244216039776802, 1.5662987351561242e-08, 0.34510722756385803, 0.013220150023698807, 1.573828356526974e-08, 0.34611955285072327, 0.013930398970842361, 1.581025799168856e-08, 0.3471309244632721, 0.014565604738891125, 1.5878322656703858e-08, 0.3481351435184479, 0.015118557028472424, 1.5941870046276563e-08, 0.34912553429603577, 0.015581953339278698, 1.6000271330085525e-08, 0.3500949442386627, 0.0159485824406147, 1.605289234873908e-08, 0.3510362207889557, 0.016211140900850296, 1.6099127364554988e-08, 0.35194268822669983, 0.0163623858243227, 1.6138383074348894e-08, 0.3528081476688385, 0.016395049169659615, 1.619816458742207e-08, 0.35426488518714905, 0.016305910423398018, 1.6247764023091804e-08, 0.3556653559207916, 0.01604013331234455, 1.628666268516099e-08, 0.35699525475502014, 0.015600131824612617, 1.6314402273565065e-08, 0.3582417070865631, 0.014988290145993233, 1.6330506724671068e-08, 0.35939136147499084, 0.014207081869244576, 1.633449642213236e-08, 0.36043086647987366, 0.013258861377835274, 1.6325898855029664e-08, 0.36134687066078186, 0.012146132066845894, 1.6304248617871053e-08, 0.36212649941444397, 0.010871248319745064, 1.6269055436168856e-08, 0.3627559244632721, 0.009436653926968575, 1.6219834364505914e-08, 0.36322179436683655, 0.00784476287662983, 1.615613420824502e-08, 0.36351123452186584, 0.0060980189591646194, 1.6077450482043787e-08, 0.3636104166507721, 0.00419880636036396, 1.4665965331062125e-08, 0.3636104166507721, -0.028092218562960625, 1.5117848306545056e-08, 0.37394824624061584, -0.028092220425605774, 1.654964165709316e-08, 0.37394824624061584, 0.004663423635065556, 1.667421578588346e-08, 0.37380948662757874, 0.007652119733393192, 1.6778757938595845e-08, 0.37340036034584045, 0.010452882386744022, 1.6863083374119014e-08, 0.37273040413856506, 0.013051972724497318, 1.6927053536619496e-08, 0.37181010842323303, 0.015435711480677128, 1.6970501448554387e-08, 0.3706494867801666, 0.01759033091366291, 1.699327079052182e-08, 0.3692585527896881, 0.019502179697155952, 1.6995199914049408e-08, 0.36764732003211975, 0.0211575198918581, 1.697612361795109e-08, 0.3658258020877838, 0.022542642429471016, 1.6935905122750228e-08, 0.36380448937416077, 0.023643838241696358, 1.687437745090392e-08, 0.3615933954715729, 0.0244473684579134, 1.679136296672823e-08, 0.3592020571231842, 0.024939553812146187, 1.6686740877958073e-08, 0.3566414415836334, 0.025106655433773994, 1.6603440400331237e-08, 0.3548232614994049, 0.02501915581524372, 1.6516278122935546e-08, 0.3530837595462799, 0.024764643982052803, 1.6425641291561988e-08, 0.351419597864151, 0.02435528114438057, 1.633189050664896e-08, 0.34982696175575256, 0.023803163319826126, 1.623536505235279e-08, 0.34830155968666077, 0.02312033250927925, 1.613647349074654e-08, 0.3468405306339264, 0.022318948060274124, 1.6035571093198087e-08, 0.3454400599002838, 0.021411079913377762, 1.5933027341930028e-08, 0.3440963327884674, 0.020408857613801956, 1.5829220600949157e-08, 0.34280601143836975, 0.019324321299791336, 1.572451324705071e-08, 0.3415652811527252, 0.01816963031888008, 1.5619288973311996e-08, 0.3403708040714264, 0.016956884413957596, 1.551386752396411e-08, 0.33921781182289124, 0.01569812372326851, 1.5538637043732706e-08, 0.33830609917640686, 0.017176467925310135, 1.5554583399080002e-08, 0.33731475472450256, 0.01853262260556221, 1.5561798960561646e-08, 0.33624711632728577, 0.01976536586880684, 1.5560317478957586e-08, 0.3351050913333893, 0.020873475819826126, 1.5550249088391865e-08, 0.33389249444007874, 0.021855730563402176, 1.5531647079569666e-08, 0.33261170983314514, 0.02271096780896187, 1.5504584283121403e-08, 0.3312655985355377, 0.02343793585896492, 1.5469129976963814e-08, 0.3298570215702057, 0.024035444483160973, 1.5425341004515758e-08, 0.32838836312294006, 0.02450229786336422, 1.5373304407262367e-08, 0.32686296105384827, 0.024837246164679527, 1.5313096568547735e-08, 0.3252836763858795, 0.025039127096533775, 1.524478498993176e-08, 0.32365337014198303, 0.025106659159064293, 1.5189030477813503e-08, 0.3224312365055084, 0.02505328319966793, 1.5128337693681715e-08, 0.3212033808231354, 0.024892648681998253, 1.506262670147862e-08, 0.3199688494205475, 0.024623891338706017, 1.4991865526781112e-08, 0.31872764229774475, 0.02424626611173153, 1.491593337732411e-08, 0.31747785210609436, 0.023758908733725548, 1.4834794725970823e-08, 0.3162194788455963, 0.02316107414662838, 1.4748352761273509e-08, 0.314951092004776, 0.022451898083090782, 1.4656573732452216e-08, 0.3136726915836334, 0.021630635485053062, 1.4559357275345519e-08, 0.31238284707069397, 0.020696422085165977, 1.4456626118430904e-08, 0.31108060479164124, 0.01964845322072506, 1.4348326971003189e-08, 0.309765487909317, 0.018485983833670616, 1.4234402101465093e-08, 0.3084370195865631, 0.017208151519298553, 1.4533962477969453e-08, 0.3084370195865631, 0.024061284959316254, 1.1954707446193424e-08, 0.28648391366004944, -0.012992090545594692, 1.1847121506036729e-08, 0.28497567772865295, -0.0139451390132308, 1.174277031168458e-08, 0.2834712564945221, -0.014827973209321499, 1.164165563949382e-08, 0.28196826577186584, -0.015638237819075584, 1.1543818345671752e-08, 0.2804652750492096, -0.016373490914702415, 1.144928418739255e-08, 0.27896037697792053, -0.017031287774443626, 1.1358114448967171e-08, 0.27745261788368225, -0.0176092442125082, 1.1270333111212949e-08, 0.27594009041786194, -0.01810491643846035, 1.1185962378590375e-08, 0.2744208872318268, -0.01851589046418667, 1.1105044883663595e-08, 0.2728935778141022, -0.018839752301573753, 1.1027625035353594e-08, 0.2713567316532135, -0.0190740879625082, 1.0953723261764026e-08, 0.26980844140052795, -0.019216453656554222, 1.0883383971815874e-08, 0.2682472765445709, -0.0192644651979208, 1.0782796877606415e-08, 0.2658349573612213, -0.019153330475091934, 1.0699326757901417e-08, 0.2635928690433502, -0.01882079616189003, 1.063294519099145e-08, 0.26152148842811584, -0.018268052488565445, 1.0583639742378637e-08, 0.2596217691898346, -0.017496321350336075, 1.0551420182025595e-08, 0.2578951418399811, -0.016506794840097427, 1.0536234107405562e-08, 0.2563416063785553, -0.01530066505074501, 1.0538090400302735e-08, 0.25496259331703186, -0.013879183679819107, 1.0556936658190352e-08, 0.25375810265541077, -0.012243542820215225, 1.0592803967313102e-08, 0.25273004174232483, -0.010394934564828873, 1.0645637260608964e-08, 0.25187841057777405, -0.008334610611200333, 1.0715428544472161e-08, 0.25120416283607483, -0.006063732784241438, 1.0802163608047977e-08, 0.2507082521915436, -0.0035835534799844027, 1.2406569993572703e-08, 0.2874127924442291, -0.003583556739613414, 1.2600357202074974e-08, 0.28723111748695374, 0.0010314520914107561, 1.2760745349282843e-08, 0.2866951525211334, 0.005236678756773472, 1.2888369482766393e-08, 0.2858177721500397, 0.009033762849867344, 1.2983883301842525e-08, 0.2846123278141022, 0.012424283660948277, 1.304796093393179e-08, 0.2830926477909088, 0.01540991012006998, 1.3081215222143783e-08, 0.2812711298465729, 0.01799219287931919, 1.3084341610181127e-08, 0.27916207909584045, 0.02017276920378208, 1.305797514561391e-08, 0.27677837014198303, 0.02195327915251255, 1.3002768639580609e-08, 0.2741333544254303, 0.023335302248597145, 1.2919355363294471e-08, 0.27123990654945374, 0.02432047761976719, 1.280840944417605e-08, 0.26811185479164124, 0.02491038478910923, 1.2670586357899083e-08, 0.2647625505924225, 0.02510666474699974, 1.2507777036319112e-08, 0.2612573206424713, 0.024887260049581528, 1.2335209298441896e-08, 0.25795474648475647, 0.02424195036292076, 1.2154626638505306e-08, 0.2548753321170807, 0.023190107196569443, 1.1967666857515269e-08, 0.2520371973514557, 0.021751102060079575, 1.1776070785174397e-08, 0.2494608461856842, 0.019944246858358383, 1.1581518855052764e-08, 0.24716535210609436, 0.01778891310095787, 1.138569327707728e-08, 0.24516978859901428, 0.015304503031075, 1.1190291360207993e-08, 0.2434937059879303, 0.012510326690971851, 1.0996997090728655e-08, 0.24215617775917053, 0.009425786323845387, 1.0807506889420893e-08, 0.2411767542362213, 0.00607019430026412, 1.062352517067211e-08, 0.24057498574256897, 0.002462951233610511, 1.0446751019799194e-08, 0.24037042260169983, -0.0013766310876235366, 1.0298809804965003e-08, 0.24055781960487366, -0.004948499146848917, 1.0170878361748237e-08, 0.24111667275428772, -0.008434089832007885, 1.0064512778740209e-08, 0.24203982949256897, -0.011790606193244457, 9.981330428843194e-09, 0.24332156777381897, -0.014975341968238354, 9.922890065183765e-09, 0.24495473504066467, -0.01794547028839588, 9.890785968025284e-09, 0.24693313241004944, -0.02065831795334816, 9.886598206776398e-09, 0.24925008416175842, -0.023071084171533585, 9.91194326616096e-09, 0.2518998682498932, -0.02514103427529335, 9.968357694845054e-09, 0.2548748552799225, -0.026825401932001114, 1.0057481070191443e-08, 0.2581698000431061, -0.02808145061135292, 1.0180867704434604e-08, 0.2617775499820709, -0.028866443783044815, 1.0340116318729997e-08, 0.2656919062137604, -0.029137615114450455, 1.0435631914162968e-08, 0.2678357660770416, -0.029096340760588646, 1.0529630500855092e-08, 0.2698618471622467, -0.028971975669264793, 1.0622709822882825e-08, 0.2717830240726471, -0.028763746842741966, 1.0715470288857887e-08, 0.2736121714115143, -0.02847079001367092, 1.0808506090143055e-08, 0.27536216378211975, -0.028092360123991966, 1.090244072798896e-08, 0.2770463526248932, -0.027627592906355858, 1.0997847077476308e-08, 0.2786771357059479, -0.027075713500380516, 1.1095324659038397e-08, 0.2802673876285553, -0.02643594704568386, 1.1195493421212177e-08, 0.28183045983314514, -0.02570742927491665, 1.1298929791792034e-08, 0.2833787500858307, -0.024889355525374413, 1.1406253719314918e-08, 0.2849256098270416, -0.02398095093667507, 1.1518060283322029e-08, 0.28648391366004944, -0.02298141084611416, 1.111187408753267e-08, 0.2509404718875885, 0.0032695799600332975, 1.1216969575400526e-08, 0.25135865807533264, 0.005255695898085833, 1.1321476200976122e-08, 0.2519170343875885, 0.007088151294738054, 1.1425153267907717e-08, 0.25261369347572327, 0.00876333937048912, 1.1527838239544508e-08, 0.25344863533973694, 0.010277565568685532, 1.1629315288530506e-08, 0.2544204294681549, 0.011627282947301865, 1.1729399673754415e-08, 0.25552859902381897, 0.012808796018362045, 1.182789510778548e-08, 0.2567721903324127, 0.013818498700857162, 1.1924618625869243e-08, 0.25815072655677795, 0.014652755111455917, 1.2019350847936039e-08, 0.25966277718544006, 0.015307929366827011, 1.211193456640558e-08, 0.26130834221839905, 0.015780415385961533, 1.2202145960316102e-08, 0.2630859911441803, 0.016066577285528183, 1.2289806505805245e-08, 0.2649952471256256, 0.016162749379873276, 1.2362701085066874e-08, 0.2667657434940338, 0.01605989970266819, 1.2421523365446774e-08, 0.2684151232242584, 0.015756214037537575, 1.2466402132815801e-08, 0.2699390947818756, 0.015258933417499065, 1.2497402224198595e-08, 0.27133193612098694, 0.014575297944247723, 1.251465597817969e-08, 0.2725893557071686, 0.013712609186768532, 1.2518272640704708e-08, 0.2737065851688385, 0.012678110972046852, 1.2508358793184016e-08, 0.2746788561344147, 0.011479044333100319, 1.248500591799484e-08, 0.27550092339515686, 0.010122710838913918, 1.2448297503908634e-08, 0.27616754174232483, 0.00861632265150547, 1.2398388093970425e-08, 0.27667489647865295, 0.006967151537537575, 1.2335364729665343e-08, 0.277017742395401, 0.005182499065995216, 1.2259334880582173e-08, 0.27719131112098694, 0.003269577631726861, 5.648713496952951e-09, 0.15731969475746155, -0.028092199936509132, 6.999269608343184e-09, 0.18821683526039124, -0.02809220366179943, 7.292519921264784e-09, 0.19453445076942444, -0.02770104818046093, 7.598630169525222e-09, 0.20040622353553772, -0.02656984142959118, 7.913980581975011e-09, 0.20581260323524475, -0.024761825799942017, 8.23492740664733e-09, 0.210733562707901, -0.022340387105941772, 8.557868191871876e-09, 0.21515002846717834, -0.01936882734298706, 8.879139201667385e-09, 0.21904149651527405, -0.015910476446151733, 9.195118444438322e-09, 0.22238841652870178, -0.01202863547950983, 9.502183040410728e-09, 0.22517123818397522, -0.007786632515490055, 9.796689681706994e-09, 0.22736993432044983, -0.0032477984204888344, 1.0075017264910002e-08, 0.22896495461463928, 0.0015245664399117231, 1.0333540245710537e-08, 0.22993674874305725, 0.006467102561146021, 1.0568600217197854e-08, 0.230264812707901, 0.011516569182276726, 1.0762566837740906e-08, 0.22999444603919983, 0.01622438244521618, 1.0933013605551878e-08, 0.22917428612709045, 0.020943908020853996, 1.1075931283244245e-08, 0.227792888879776, 0.025594888255000114, 1.1187269777224174e-08, 0.2258378565311432, 0.030097035691142082, 1.1263018961926718e-08, 0.22329774498939514, 0.034370094537734985, 1.129908877572916e-08, 0.22015920281410217, 0.03833380341529846, 1.1291489521170206e-08, 0.2164112627506256, 0.0419079065322876, 1.1236174657369702e-08, 0.21204152703285217, 0.04501217603683472, 1.1129090538020137e-08, 0.20703759789466858, 0.04756629467010498, 1.096620838580975e-08, 0.20138755440711975, 0.04949003458023071, 1.074347810714471e-08, 0.1950789988040924, 0.05070313811302185, 1.045689312917375e-08, 0.18810048699378967, 0.05112535133957863, 9.11142272741472e-09, 0.15731969475746155, 0.05112535133957863, 9.162190117706359e-09, 0.16870275139808655, 0.0409037210047245, 9.928865729591507e-09, 0.1862422525882721, 0.0409037210047245, 1.014835948609516e-08, 0.191538006067276, 0.04062939062714577, 1.0323291554925618e-08, 0.19633737206459045, 0.03983199596405029, 1.0455624810390418e-08, 0.2006470263004303, 0.03854978084564209, 1.054734877214969e-08, 0.20447412133216858, 0.03682109713554382, 1.0600431643581487e-08, 0.20782533288002014, 0.03468427062034607, 1.0616837187171768e-08, 0.21070733666419983, 0.03217759728431702, 1.059855492258066e-08, 0.2131272852420807, 0.02933940291404724, 1.0547529960547308e-08, 0.21509137749671936, 0.02620798349380493, 1.0465792676939145e-08, 0.2166077196598053, 0.022821694612503052, 1.0355265089856402e-08, 0.21768203377723694, 0.019218802452087402, 1.0217935830780789e-08, 0.21832147240638733, 0.015437662601470947, 1.0055794419372432e-08, 0.21853318810462952, 0.0115165701135993, 9.935173572728218e-09, 0.21840158104896545, 0.00888869073241949, 9.788147181666318e-09, 0.21797481179237366, 0.005951880943030119, 9.617087570745753e-09, 0.2172047197818756, 0.0028086004313081503, 9.424324431961395e-09, 0.2160421907901764, -0.00043877962161786854, 9.212254070689596e-09, 0.2144395411014557, -0.003687739372253418, 8.983226607028882e-09, 0.21234813332557678, -0.006835877895355225, 8.73959216107778e-09, 0.20971933007240295, -0.00978076457977295, 8.483707070183755e-09, 0.20650449395179749, -0.012419908307492733, 8.217980074221032e-09, 0.20265641808509827, -0.014650939963757992, 7.94472665432977e-09, 0.19812551140785217, -0.016371337696909904, 7.666318246890569e-09, 0.1928636133670807, -0.0174787025898695, 7.385145384120051e-09, 0.1868230402469635, -0.017870603129267693, 6.593082524375404e-09, 0.16870275139808655, -0.017870601266622543, 5.679167802696838e-09, 0.10911527276039124, 0.02080894447863102, 5.650293566361597e-09, 0.10776010155677795, 0.021503547206521034, 5.619476883822472e-09, 0.10642305016517639, 0.022135594859719276, 5.586675122515317e-09, 0.10510268807411194, 0.02270553447306156, 5.55186385753359e-09, 0.10379806160926819, 0.023213783279061317, 5.5150199962383795e-09, 0.10250821709632874, 0.023660728707909584, 5.476076481158998e-09, 0.10123124718666077, 0.02404678799211979, 5.4350297595817665e-09, 0.09996667504310608, 0.024372318759560585, 5.39183631076412e-09, 0.09871307015419006, 0.024637768045067787, 5.3464503935174434e-09, 0.09746900200843811, 0.024843523278832436, 5.298848027024405e-09, 0.09623351693153381, 0.024990001693367958, 5.248984802364021e-09, 0.09500518441200256, 0.025077592581510544, 5.196835406451328e-09, 0.09378305077552795, 0.025106679648160934, 5.081234544235258e-09, 0.09124866127967834, 0.02499644085764885, 4.9634172327728265e-09, 0.08887973427772522, 0.024670016020536423, 4.844125101044483e-09, 0.08668676018714905, 0.024133902043104172, 4.724074464945716e-09, 0.0846797525882721, 0.023394476622343063, 4.604050474199539e-09, 0.08287015557289124, 0.022458236664533615, 4.484751681133048e-09, 0.08126750588417053, 0.021331649273633957, 4.366918382459062e-09, 0.07988229393959045, 0.02002115175127983, 4.251332175186917e-09, 0.07872596383094788, 0.01853318139910698, 4.138692943911337e-09, 0.07780805230140686, 0.016874205321073532, 4.0297623016272155e-09, 0.07713952660560608, 0.015050691552460194, 3.9252805450473716e-09, 0.076730877161026, 0.013069075532257557, 3.825966654602553e-09, 0.07659211754798889, 0.010935795493423939, 3.7023115684320373e-09, 0.07707181572914124, 0.0076272012665867805, 3.6322498342400422e-09, 0.07839885354042053, 0.004697334486991167, 3.606295928548775e-09, 0.08040347695350647, 0.0020989596378058195, 3.614970767173986e-09, 0.08291593194007874, -0.00021504194592125714, 3.6488294608005845e-09, 0.08576741814613342, -0.002291936194524169, 3.698391592976691e-09, 0.08878818154335022, -0.004178841132670641, 3.754216493234708e-09, 0.09180942177772522, -0.005922962445765734, 3.806776671666512e-09, 0.0946604311466217, -0.007571537978947163, 3.846675866725491e-09, 0.09717336297035217, -0.0091716842725873, 3.8643883648603605e-09, 0.09917750954627991, -0.01077060867100954, 3.850492369394942e-09, 0.1005045473575592, -0.012415547855198383, 3.7955079079665666e-09, 0.10098472237586975, -0.014153619296848774, 3.753370947379153e-09, 0.10091367363929749, -0.015046556480228901, 3.7084861848057926e-09, 0.10070720314979553, -0.015866925939917564, 3.661273950683608e-09, 0.10037484765052795, -0.01661466620862484, 3.612149024334599e-09, 0.09992614388465881, -0.01728980801999569, 3.5615494997642827e-09, 0.09937110543251038, -0.017892351374030113, 3.509911694621337e-09, 0.09871974587440491, -0.0184223260730505, 3.4576133067787396e-09, 0.09798064827919006, -0.01887967251241207, 3.405110859944216e-09, 0.09716430306434631, -0.019264450296759605, 3.35282290819805e-09, 0.09628024697303772, -0.019576599821448326, 3.3011644529068462e-09, 0.09533801674842834, -0.01981617882847786, 3.250573810120727e-09, 0.09434762597084045, -0.019983161240816116, 3.201448883771718e-09, 0.09331813454627991, -0.02007751539349556, 3.1560252189422044e-09, 0.0922328531742096, -0.020031411200761795, 3.1112383780396158e-09, 0.09106937050819397, -0.019892532378435135, 3.067393450351119e-09, 0.08983388543128967, -0.0196601040661335, 3.0246949389578504e-09, 0.08853021264076233, -0.019333261996507645, 2.983404634449016e-09, 0.08716359734535217, -0.01891126111149788, 2.943787658082897e-09, 0.08573928475379944, -0.018393266946077347, 2.9060669426428376e-09, 0.08426156640052795, -0.017778504639863968, 2.8704876253726752e-09, 0.08273521065711975, -0.0170661099255085, 2.837333923366714e-09, 0.08116593956947327, -0.01625530794262886, 2.8067868029779675e-09, 0.07955709099769592, -0.01534529309719801, 2.7791524637166276e-09, 0.07791486382484436, -0.014335262589156628, 2.7546553926782735e-09, 0.07624354958534241, -0.013224381022155285, 2.2672355104447206e-09, 0.07624354958534241, -0.024375248700380325, 2.303258916924733e-09, 0.07789340615272522, -0.0252009816467762, 2.3404524984727004e-09, 0.07948127388954163, -0.025937963277101517, 2.379173968947157e-09, 0.0810185968875885, -0.026589442044496536, 2.4197399639547257e-09, 0.08251586556434631, -0.027158666402101517, 2.462490655830152e-09, 0.08398404717445374, -0.02764882519841194, 2.5077633303283164e-09, 0.08543410897254944, -0.02806316688656807, 2.555897271605545e-09, 0.0868770182132721, -0.02840491011738777, 2.6072299874613236e-09, 0.08832374215126038, -0.02867727354168892, 2.662079001680695e-09, 0.08978477120399475, -0.02888350561261177, 2.720782266152355e-09, 0.09127107262611389, -0.029026824980974197, 2.783679509121839e-09, 0.09279361367225647, -0.02911045029759407, 2.851129332626101e-09, 0.09436383843421936, -0.02913760021328926, 2.962103895498558e-09, 0.09677615761756897, -0.02901112101972103, 3.0784339521972015e-09, 0.09906545281410217, -0.02863909862935543, 3.198919351632412e-09, 0.10121503472328186, -0.028032293543219566, 3.322372377212446e-09, 0.10320869088172913, -0.02720167301595211, 3.4475879928663744e-09, 0.10502973198890686, -0.02615811489522457, 3.5733622727462944e-09, 0.10666146874427795, -0.02491246722638607, 3.6985088325280913e-09, 0.1080876886844635, -0.02347566746175289, 3.8218237463638616e-09, 0.10929170250892639, -0.021858563646674156, 3.942120407884886e-09, 0.11025729775428772, -0.02007209323346615, 4.05815336890214e-09, 0.11096683144569397, -0.01812710426747799, 4.168779987878679e-09, 0.11140504479408264, -0.016034474596381187, 4.272771025881639e-09, 0.11155477166175842, -0.013805171474814415, 4.326752289784963e-09, 0.11148801445960999, -0.012503465637564659, 4.37207692272068e-09, 0.11128249764442444, -0.01126103661954403, 4.408991394200257e-09, 0.11093059182167053, -0.010064622387290001, 4.437684442137879e-09, 0.11042323708534241, -0.008900841698050499, 4.458423852327087e-09, 0.10975328087806702, -0.007756432984024286, 4.471414349893621e-09, 0.1089121401309967, -0.006618103012442589, 4.476907733419466e-09, 0.10789218544960022, -0.005472471937537193, 4.475108728030364e-09, 0.10668483376502991, -0.004306277260184288, 4.4662646914162e-09, 0.10528245568275452, -0.0031062269117683172, 4.450584345505604e-09, 0.10367646813392639, -0.001858969684690237, 4.428335032002906e-09, 0.10185971856117249, -0.0005512138013727963, 4.399703268376243e-09, 0.09982314705848694, 0.000830332632176578, 4.360669159098052e-09, 0.09764638543128967, 0.002114097587764263, 4.3273225003304105e-09, 0.09569898247718811, 0.0032986209262162447, 4.299649525307814e-09, 0.093973308801651, 0.004391203634440899, 4.2776528985655204e-09, 0.0924622118473053, 0.005399088840931654, 4.261297981145162e-09, 0.09115758538246155, 0.006329547148197889, 4.250545249107063e-09, 0.0900513231754303, 0.007189820986241102, 4.245420903714603e-09, 0.0891367495059967, 0.00798715278506279, 4.245867657459712e-09, 0.08840528130531311, 0.008728843182325363, 4.251912155694981e-09, 0.08785024285316467, 0.009422164410352707, 4.263473574184218e-09, 0.08746257424354553, 0.010074328631162643, 4.280598986383666e-09, 0.08723607659339905, 0.01069260761141777, 4.303230660696045e-09, 0.08716216683387756, 0.011284273117780685, 4.33532143517823e-09, 0.08721700310707092, 0.011963587254285812, 4.370465767067344e-09, 0.08737960457801819, 0.012604992836713791, 4.408277742840028e-09, 0.08764520287513733, 0.013204436749219894, 4.448395873879463e-09, 0.08800950646400452, 0.013757925480604172, 4.490517291344531e-09, 0.08846965432167053, 0.014261405915021896, 4.534256525801084e-09, 0.08902087807655334, 0.014710824936628342, 4.579252088632302e-09, 0.08965888619422913, 0.015102189034223557, 4.625157590254503e-09, 0.09037986397743225, 0.015431415289640427, 4.671654174615014e-09, 0.0911804735660553, 0.015694510191679, 4.718354595922847e-09, 0.09205594658851624, 0.015887420624494553, 4.764897365561183e-09, 0.09300199151039124, 0.01600615307688713, 4.810958298406831e-09, 0.09401527047157288, 0.01604662463068962, 4.852795498777596e-09, 0.09500661492347717, 0.016012411564588547, 4.894354699302994e-09, 0.09606137871742249, 0.01590839959681034, 4.935360564672919e-09, 0.09717527031898499, 0.015732625499367714, 4.975497347459168e-09, 0.09834304451942444, 0.015483061783015728, 5.01452745993447e-09, 0.09956136345863342, 0.015157650224864483, 5.052135154670623e-09, 0.1008249819278717, 0.014754395000636578, 5.0880450963575186e-09, 0.10212960839271545, 0.014271298423409462, 5.121980617417421e-09, 0.10347095131874084, 0.013706305995583534, 5.1536677148078525e-09, 0.10484471917152405, 0.013057449832558632, 5.182828388683447e-09, 0.10624662041664124, 0.012322673574090004, 5.209146891616001e-09, 0.10767140984535217, 0.011499980464577675, 5.232367428220641e-09, 0.10911527276039124, 0.010587343946099281, 5.059752172797971e-09, 0.06462828069925308, 0.051125358790159225, 4.607871417761089e-09, 0.054290447384119034, 0.051125362515449524, 3.379167612393985e-09, 0.054290447384119034, 0.02301589958369732, 3.3499560903038628e-09, 0.053263816982507706, 0.023374244570732117, 3.320606456469477e-09, 0.052271518856287, 0.023695096373558044, 3.29102323171071e-09, 0.0513102151453495, 0.02397961914539337, 3.261074077443027e-09, 0.05037561431527138, 0.02422906458377838, 3.2306246566804475e-09, 0.0494634248316288, 0.02444465458393097, 3.199559284183806e-09, 0.04856983199715614, 0.024627551436424255, 3.1677447331901476e-09, 0.04769054427742958, 0.024779006838798523, 3.135085968608564e-09, 0.04682222381234169, 0.024900183081626892, 3.101430667840077e-09, 0.04596010223031044, 0.024992361664772034, 3.066661591333286e-09, 0.045100364834070206, 0.02505667507648468, 3.0306470666374707e-09, 0.04423872008919716, 0.025094404816627502, 2.9932909484386983e-09, 0.04337183013558388, 0.025106683373451233, 2.821520794782373e-09, 0.039663467556238174, 0.024885401129722595, 2.6400674979498717e-09, 0.03616109862923622, 0.024236604571342468, 2.4508983731408307e-09, 0.032887134701013565, 0.023182883858680725, 2.255958087005183e-09, 0.0298635084182024, 0.02174680121243, 2.0572157310994044e-09, 0.027112634852528572, 0.019950972869992256, 1.8566166382072424e-09, 0.024656446650624275, 0.017817990854382515, 1.6561257920599814e-09, 0.022517355158925056, 0.015370385721325874, 1.4576918561104435e-09, 0.02071729488670826, 0.012630807235836983, 1.2632805912460299e-09, 0.019278675317764282, 0.009621815755963326, 1.0748579803987468e-09, 0.01822391152381897, 0.006365972105413675, 8.943504825609239e-10, 0.017574459314346313, 0.0028858953155577183, 7.237461741027573e-10, 0.017353206872940063, -0.0007958238711580634, 5.554567916732367e-10, 0.01755395531654358, -0.00484658544883132, 4.1624492741476615e-10, 0.018148094415664673, -0.008625520393252373, 3.0613539481194607e-10, 0.0191208403557539, -0.012117279693484306, 2.2523372056326707e-10, 0.02045932225883007, -0.01530657522380352, 1.735868671026708e-10, 0.022149233147501945, -0.018178028985857964, 1.5127815666815536e-10, 0.024177221581339836, -0.020716382190585136, 1.5837653410955e-10, 0.026529459282755852, -0.0229062270373106, 1.9494461600544355e-10, 0.029192117974162102, -0.024732304736971855, 2.6106961037442034e-10, 0.03215184435248375, -0.026179268956184387, 3.5681668730802585e-10, 0.0353948138654232, -0.027231797575950623, 4.822525712100401e-10, 0.03890719637274742, -0.027874544262886047, 6.374212269122381e-10, 0.04267468675971031, -0.028092190623283386, 1.5970428313138996e-09, 0.06462827324867249, -0.028092192485928535, 1.5259582486493173e-09, 0.054290443658828735, -0.019380586221814156, 1.0689918950035349e-09, 0.04383626580238342, -0.019380584359169006, 9.51994927333999e-10, 0.0410100519657135, -0.019230946898460388, 8.615496649433396e-10, 0.03850331902503967, -0.018793359398841858, 7.963326109639013e-10, 0.03630271553993225, -0.018084749579429626, 7.549588176836153e-10, 0.03439345955848694, -0.017122015357017517, 7.360800302613768e-10, 0.032761722803115845, -0.015922173857688904, 7.383337274902146e-10, 0.031393200159072876, -0.014502092264592648, 7.603740415085269e-10, 0.030274061486124992, -0.012878729961812496, 8.008333440834292e-10, 0.0293900053948164, -0.011069073341786861, 8.583698751785107e-10, 0.028727203607559204, -0.009089990518987179, 9.316154514493746e-10, 0.028271347284317017, -0.006958468351513147, 1.0191844035389863e-09, 0.02800765633583069, -0.004691435489803553, 1.1197724969491674e-09, 0.027923256158828735, -0.0023058487568050623, 1.2416608852205968e-09, 0.02806153893470764, 0.00034435244742780924, 1.3680059307574766e-09, 0.02846875786781311, 0.002827571239322424, 1.4977159512596927e-09, 0.029132038354873657, 0.005131707992404699, 1.6297615479388128e-09, 0.030039936304092407, 0.007244662381708622, 1.7630734649998203e-09, 0.03118005394935608, 0.00915436539798975, 1.896600210216093e-09, 0.032540470361709595, 0.010848687030375004, 2.029272527792614e-09, 0.03410878777503967, 0.012315557338297367, 2.160059908717926e-09, 0.03587356209754944, 0.013542846776545048, 2.2878703376250087e-09, 0.03782191872596741, 0.014518454670906067, 2.411655763978615e-09, 0.0399419367313385, 0.015230312943458557, 2.5303852346780786e-09, 0.042222172021865845, 0.015666291117668152, 2.6429685107132173e-09, 0.044649749994277954, 0.015814319252967834, 2.6798048224918603e-09, 0.04550471901893616, 0.01580207049846649, 2.714320102015222e-09, 0.046331554651260376, 0.01576484739780426, 2.7467259577917957e-09, 0.04713597893714905, 0.015701785683631897, 2.7772182331631257e-09, 0.04792323708534241, 0.015612110495567322, 2.806032739499642e-09, 0.048699527978897095, 0.015495016239583492, 2.8333633217414445e-09, 0.049470096826553345, 0.01534970011562109, 2.8594029366502127e-09, 0.05024018883705139, 0.015175326727330685, 2.8844096000568697e-09, 0.05101647973060608, 0.014971121214330196, 2.9085551744856275e-09, 0.05180373787879944, 0.01473624911159277, 2.932076803574546e-09, 0.05260816216468811, 0.014469935558736324, 2.955166999996095e-09, 0.05343499779701233, 0.014171346090734005, 2.978062019209915e-09, 0.054290443658828735, 0.013839676044881344, 1.2568572849147586e-09, 0.0046922299079597, 0.024061311036348343, 8.049763633444229e-10, -0.00564559968188405, 0.024061311036348343, -1.4747256749103599e-09, -0.0056456043384969234, -0.028092186897993088, -1.0228448088511755e-09, 0.0046922252513468266, -0.028092186897993088, 1.9930563865955264e-09, 0.005737457890063524, 0.03985835984349251, 2.026801837473613e-09, 0.00568071473389864, 0.04068710282444954, 2.0544228540586573e-09, 0.005515729077160358, 0.041483987122774124, 2.0758978980239817e-09, 0.005249653942883015, 0.042241353541612625, 2.091224082789722e-09, 0.004890118725597858, 0.04295151308178902, 2.1004225025933465e-09, 0.004445229656994343, 0.04360683634877205, 2.1034904928995957e-09, 0.003922616131603718, 0.044199634343385696, 2.1004278316638647e-09, 0.003329907776787877, 0.04472227767109871, 2.091230522083265e-09, 0.0026747335214167833, 0.045167047530412674, 2.075879690366378e-09, 0.001964246155694127, 0.04552634432911873, 2.0544137502298554e-09, 0.0012070287484675646, 0.04579247906804085, 2.0268093869901804e-09, 0.0004102339153178036, 0.045957762748003006, 1.993067044736563e-09, -0.00041850906563922763, 0.04601456597447395, 1.954358452849192e-09, -0.001247251988388598, 0.045957762748003006, 1.912303426720996e-09, -0.0020440469961613417, 0.04579244926571846, 1.8675516688659854e-09, -0.0028017412405461073, 0.04552634432911873, 1.820810724417754e-09, -0.0035117517691105604, 0.045167047530412674, 1.7727295187341952e-09, -0.004166926257312298, 0.04472224786877632, 1.7239771832322504e-09, -0.004759634844958782, 0.044199634343385696, 1.6752197407043923e-09, -0.005282248370349407, 0.04360680654644966, 1.627129098125124e-09, -0.005727137438952923, 0.04295151308178902, 1.5803700570415913e-09, -0.006086672656238079, 0.04224132373929024, 1.535633953331228e-09, -0.006352747790515423, 0.041483957320451736, 1.493589252277161e-09, -0.006517733447253704, 0.04068707302212715, 1.4548637849998158e-09, -0.006574954371899366, 0.03985835984349251, 1.4211395393814996e-09, -0.006517733912914991, 0.03902961686253548, 1.3935170795065233e-09, -0.00635274825617671, 0.038232702761888504, 1.3720433678088284e-09, -0.006086673121899366, 0.03747536614537239, 1.3567158507754584e-09, -0.00572713790461421, 0.03676517680287361, 1.3475187632394636e-09, -0.0052822488360106945, 0.03610988333821297, 1.3444495516878874e-09, -0.0047596353106200695, 0.03551705554127693, 1.3475134341689454e-09, -0.004166926722973585, 0.03499444201588631, 1.3567093004596131e-09, -0.003511752700433135, 0.034549642354249954, 1.3720603542211052e-09, -0.0028012653347104788, 0.0341903455555439, 1.3935274045806523e-09, -0.0020440479274839163, 0.03392424061894417, 1.4211304355526977e-09, -0.0012472531525418162, 0.03375892713665962, 1.4548742210962473e-09, -0.00041851014248095453, 0.03370215371251106, 1.4935827019613157e-09, 0.0004102328384760767, 0.03375895693898201, 1.5356365068441846e-09, 0.0012070277007296681, 0.03392424061894417, 1.5803673925063322e-09, 0.0019642452243715525, 0.0341903455555439, 1.627129098125124e-09, 0.0026747325900942087, 0.034549642354249954, 1.6752104148309854e-09, 0.0033299068454653025, 0.03499444201588631, 1.7239627503329302e-09, 0.0039226156659424305, 0.03551705554127693, 1.7727203038830908e-09, 0.0044452291913330555, 0.03610988333821297, 1.8208108354400565e-09, 0.004890118259936571, 0.03676517680287361, 1.8675698765235893e-09, 0.005249653477221727, 0.03747536614537239, 1.912306091256255e-09, 0.005515728611499071, 0.03823273256421089, 1.9543506812880196e-09, 0.005680714268237352, 0.03902961686253548, -2.1246169268351878e-09, -0.020513387396931648, -0.02809218503534794, 1.550848893749901e-10, -0.02051338367164135, 0.024061312898993492, -2.9679603219534556e-10, -0.0308512132614851, 0.024061312898993492, -1.9266050976796123e-09, -0.030851216986775398, -0.013224371708929539, -2.0143549050999354e-09, -0.031714290380477905, -0.014368780888617039, -2.099846074798961e-09, -0.03261885046958923, -0.015420028008520603, -2.182837022246531e-09, -0.033560603857040405, -0.016376890242099762, -2.2632138385603184e-09, -0.03453812003135681, -0.017238177359104156, -2.340734939210165e-09, -0.035547107458114624, -0.018002666532993317, -2.415284638956905e-09, -0.03658613562583923, -0.018669135868549347, -2.486664874012945e-09, -0.03765186667442322, -0.01923639327287674, -2.554677580590692e-09, -0.038740962743759155, -0.019703246653079987, -2.6191637747530194e-09, -0.03985103964805603, -0.020068444311618805, -2.6799673591426654e-09, -0.04097971320152283, -0.020330794155597687, -2.7368693977791736e-09, -0.04212316870689392, -0.020489104092121124, -2.789731556873676e-09, -0.0432794988155365, -0.020542122423648834, -2.8602142876366088e-09, -0.04497846961021423, -0.020455606281757355, -2.9168623072450828e-09, -0.04653152823448181, -0.020198501646518707, -2.9598332673685945e-09, -0.04793867468833923, -0.019774414598941803, -2.9892650577068025e-09, -0.049199432134628296, -0.01918698102235794, -3.005296012048575e-09, -0.050313323736190796, -0.01843983680009842, -3.0080644641827803e-09, -0.05127987265586853, -0.017536617815494537, -2.99772873191273e-09, -0.0520990788936615, -0.016480959951877594, -2.974403834343775e-09, -0.052769988775253296, -0.015276438556611538, -2.938251419948301e-09, -0.05329260230064392, -0.013926750980317593, -2.889407824113732e-09, -0.05366644263267517, -0.012435502372682095, -2.828010270405912e-09, -0.05389103293418884, -0.010806298814713955, -2.754197758747523e-09, -0.05396589636802673, -0.00904280599206686, -1.3071705939893263e-09, -0.053965892642736435, 0.02406131662428379, -1.7590515710708132e-09, -0.06430372595787048, 0.02406131662428379, -3.1756151042117153e-09, -0.06430372595787048, -0.00834587775170803, -3.3084175399267224e-09, -0.06415113806724548, -0.011536633595824242, -3.4176905749916386e-09, -0.06370386481285095, -0.014483785256743431, -3.503820122929824e-09, -0.06297716498374939, -0.017180895432829857, -3.5671274822846044e-09, -0.061984866857528687, -0.01962149702012539, -3.6080178844599686e-09, -0.060742709785699844, -0.021799122914671898, -3.626856592831018e-09, -0.05926546826958656, -0.02370733581483364, -3.62400731646062e-09, -0.05756792798638344, -0.025339698418974876, -3.599854192515295e-09, -0.05566534772515297, -0.026689713820815086, -3.5547416121772812e-09, -0.05357203260064125, -0.027750974521040916, -3.489054378746914e-09, -0.05130324140191078, -0.028517015278339386, -3.403176407346109e-09, -0.04887423291802406, -0.028981365263462067, -3.2974725172607577e-09, -0.04629978910088539, -0.029137589037418365, -3.2381266557024446e-09, -0.0450042225420475, -0.02907548099756241, -3.1721998361433634e-09, -0.043679092079401016, -0.02889237552881241, -3.1003191125478224e-09, -0.04233393445611, -0.028593100607395172, -3.0230951075793655e-09, -0.04097780957818031, -0.02818254381418228, -2.9411526547562516e-09, -0.039620254188776016, -0.027665473520755768, -2.8551028208312346e-09, -0.03827032819390297, -0.0270468071103096, -2.7655704393225733e-09, -0.036937568336725235, -0.026331312954425812, -2.6731452607009487e-09, -0.03563055768609047, -0.025523878633975983, -2.578475433168137e-09, -0.03435930982232094, -0.02462933212518692, -2.482168026674003e-09, -0.0331328846514225, -0.02365250140428543, -2.384831443436042e-09, -0.031960342079401016, -0.02259824424982071, -2.2870925153739563e-09, -0.030851216986775398, -0.021471360698342323, -2.5764979039166747e-09, -0.030851216986775398, -0.02809218503534794, -1.210698874487548e-09, -0.07882293313741684, 0.05112537369132042, -1.66257962952443e-09, -0.08916076272726059, 0.05112537369132042, -5.125289526120014e-09, -0.08916077017784119, -0.02809217944741249, -4.673408326993922e-09, -0.07882294058799744, -0.02809217944741249, -2.1398476324208104e-09, -0.10007937997579575, 0.05112537369132042, -3.9879739510695345e-09, -0.14235958456993103, 0.05112537741661072, -7.450683625620513e-09, -0.14235958456993103, -0.028092173859477043, -6.953113640406627e-09, -0.13097652792930603, -0.028092175722122192, -5.343613551644921e-09, -0.13097652792930603, 0.008728891611099243, -3.993057440254688e-09, -0.10007938742637634, 0.00872888881713152, -3.546256843733886e-09, -0.10007938742637634, 0.018950490280985832, -4.896813177168724e-09, -0.13097652792930603, 0.01895049214363098, -3.937206116688685e-09, -0.13097652792930603, 0.04090374708175659, -2.586649561209242e-09, -0.10007938742637634, 0.04090374335646629, -8.019342523368778e-09, -0.23458656668663025, 0.05112538859248161, -1.1482051753830547e-08, -0.23458656668663025, -0.028092166408896446, -1.098448265679508e-08, -0.22320351004600525, -0.028092168271541595, -9.48668432698696e-09, -0.22320351004600525, 0.0061734700575470924, -8.968792819530336e-09, -0.2113555371761322, 0.006173469126224518, -8.768599180086767e-09, -0.2069748342037201, 0.006372667383402586, -8.569637444111322e-09, -0.20300421118736267, 0.006953752599656582, -8.37277180920637e-09, -0.1994388997554779, 0.00789219792932272, -8.178807853198578e-09, -0.19627270102500916, 0.0091633852571249, -7.98859201012192e-09, -0.1935003697872162, 0.010742699727416039, -7.802926305089386e-09, -0.19111570715904236, 0.01260555349290371, -7.622660724848629e-09, -0.18911346793174744, 0.014727329835295677, -7.448616390348661e-09, -0.18748793005943298, 0.017083441838622093, -7.281623748411903e-09, -0.18623337149620056, 0.019649242982268333, -7.1225239040018096e-09, -0.18534454703330994, 0.022400205954909325, -6.972124211301889e-09, -0.18481525778770447, 0.025311654433608055, -6.831248455796413e-09, -0.18463978171348572, 0.028359031304717064, -6.7037091433519436e-09, -0.1848052442073822, 0.03144225850701332, -6.596211576948008e-09, -0.18530496954917908, 0.034401241689920425, -6.510203043319507e-09, -0.18614467978477478, 0.037208590656518936, -6.447071321247222e-09, -0.18732866644859314, 0.039836857467889786, -6.408286346015757e-09, -0.1888631284236908, 0.042258623987436295, -6.395254548152707e-09, -0.19075283408164978, 0.04444647207856178, -6.40940278628932e-09, -0.19300302863121033, 0.04637298732995987, -6.4521610276813135e-09, -0.19561895728111267, 0.04801071435213089, -6.524957463227565e-09, -0.19860586524009705, 0.04933223873376846, -6.629218951559324e-09, -0.2019689977169037, 0.05031014233827591, -6.766394999857539e-09, -0.20571407675743103, 0.05091700702905655, -6.9378716105461535e-09, -0.2098453938961029, 0.051125384867191315, -7.968575133077138e-09, -0.22320351004600525, 0.04090375453233719, -7.38467331728998e-09, -0.2098453938961029, 0.04090375453233719, -7.2837065268061e-09, -0.20740875601768494, 0.04077697545289993, -7.205645857766285e-09, -0.20525822043418884, 0.04041225463151932, -7.14882464336597e-09, -0.20337900519371033, 0.039832957088947296, -7.1116366129331254e-09, -0.2017577588558197, 0.03906247764825821, -7.092432419142369e-09, -0.20038017630577087, 0.038124240934848785, -7.089564491025158e-09, -0.19923195242881775, 0.03704161196947098, -7.101407462073439e-09, -0.19829925894737244, 0.03583798557519913, -7.1263124290510405e-09, -0.19756779074668884, 0.034536756575107574, -7.162632709167838e-09, -0.19702324271202087, 0.03316131979227066, -7.208738495023681e-09, -0.19665178656578064, 0.031735070049762726, -7.2629857683637056e-09, -0.19643911719322205, 0.030281370505690575, -7.3237451658769714e-09, -0.1963714063167572, 0.028823649510741234, -7.411880886820654e-09, -0.19648393988609314, 0.026919877156615257, -7.503272669850958e-09, -0.1968153417110443, 0.025160467252135277, -7.597368067990828e-09, -0.19735702872276306, 0.023549502715468407, -7.693637726902125e-09, -0.19810089468955994, 0.022090977057814598, -7.791529199607794e-09, -0.19903835654258728, 0.020788943395018578, -7.890512243591274e-09, -0.20016130805015564, 0.019647425040602684, -7.989992667489787e-09, -0.20146021246910095, 0.018670475110411644, -8.089484637707756e-09, -0.20292791724205017, 0.017862088978290558, -8.188390410168722e-09, -0.20455488562583923, 0.01722634583711624, -8.286203723173458e-09, -0.2063334882259369, 0.016767241060733795, -8.382352589819675e-09, -0.20825466513633728, 0.016488797962665558, -8.476303214877134e-09, -0.21031031012535095, 0.016395099461078644, -9.039882620243134e-09, -0.22320351004600525, 0.016395099461078644, -8.760631331483637e-09, -0.2515452802181244, 0.05112538859248161, -9.258201316697523e-09, -0.2629283368587494, 0.05112538859248161, -1.2720910547159292e-08, -0.2629283368587494, -0.028092164546251297, -1.2223340561945406e-08, -0.2515452802181244, -0.028092164546251297, -1.1258649124101794e-08, -0.3086932599544525, 0.05112539231777191, -1.175621822113726e-08, -0.3200763165950775, 0.05112539604306221, -1.521892656342061e-08, -0.3200763165950775, -0.02809215895831585, -1.3157555045495428e-08, -0.27291759848594666, -0.028092162683606148, -1.2710754226930021e-08, -0.27291759848594666, -0.01787056215107441, -1.4274557535998156e-08, -0.3086932599544525, -0.01787056028842926, -1.2279175010121435e-08, -0.3320401608943939, 0.05112539604306221, -1.4127321534829207e-08, -0.3743208348751068, 0.05112539976835251, -1.7590030765290976e-08, -0.3743208348751068, -0.0280921533703804, -1.709246255643393e-08, -0.3629377782344818, -0.02809215523302555, -1.5482962467672223e-08, -0.3629377782344818, 0.008728912100195885, -1.4132384151821498e-08, -0.3320401608943939, 0.00872890930622816, -1.368558333325609e-08, -0.3320401608943939, 0.018950510770082474, -1.5036162537285236e-08, -0.3629377782344818, 0.018950512632727623, -1.4076554144537567e-08, -0.3629377782344818, 0.04090376943349838, -1.2725976716865262e-08, -0.3320401608943939, 0.040903765708208084});
    _trix = std::vector<int>({1, 47, 0, 1, 46, 47, 2, 46, 1, 2, 45, 46, 3, 45, 2, 3, 44, 45, 4, 44, 3, 4, 43, 44, 5, 43, 4, 5, 42, 43, 6, 42, 5, 6, 41, 42, 7, 48, 6, 48, 41, 6, 7, 95, 48, 49, 41, 48, 7, 94, 95, 50, 41, 49, 7, 93, 94, 51, 41, 50, 51, 40, 41, 8, 93, 7, 8, 92, 93, 52, 40, 51, 8, 91, 92, 53, 40, 52, 8, 90, 91, 54, 40, 53, 54, 39, 40, 9, 90, 8, 9, 89, 90, 55, 39, 54, 9, 88, 89, 56, 39, 55, 56, 38, 39, 10, 88, 9, 10, 87, 88, 57, 38, 56, 57, 37, 38, 11, 87, 10, 11, 86, 87, 58, 37, 57, 11, 85, 86, 59, 37, 58, 59, 36, 37, 12, 85, 11, 12, 84, 85, 60, 36, 59, 13, 84, 12, 13, 83, 84, 60, 35, 36, 61, 35, 60, 13, 82, 83, 62, 35, 61, 14, 82, 13, 62, 34, 35, 14, 81, 82, 63, 34, 62, 14, 80, 81, 15, 80, 14, 64, 34, 63, 64, 33, 34, 15, 79, 80, 65, 33, 64, 16, 79, 15, 65, 32, 33, 16, 78, 79, 66, 32, 65, 16, 77, 78, 67, 32, 66, 17, 77, 16, 67, 31, 32, 17, 76, 77, 68, 31, 67, 17, 75, 76, 69, 31, 68, 17, 74, 75, 70, 31, 69, 18, 74, 17, 70, 30, 31, 18, 73, 74, 71, 30, 70, 18, 72, 73, 72, 30, 71, 18, 30, 72, 19, 30, 18, 19, 29, 30, 20, 29, 19, 20, 28, 29, 21, 28, 20, 21, 27, 28, 22, 27, 21, 22, 26, 27, 23, 26, 22, 23, 25, 26, 24, 25, 23, 190, 188, 189, 166, 164, 165, 191, 188, 190, 191, 187, 188, 167, 164, 166, 167, 163, 164, 192, 187, 191, 192, 186, 187, 168, 163, 167, 193, 186, 192, 193, 185, 186, 168, 162, 163, 169, 162, 168, 194, 185, 193, 97, 202, 96, 97, 201, 202, 194, 184, 185, 170, 162, 169, 195, 184, 194, 170, 161, 162, 195, 183, 184, 196, 183, 195, 171, 161, 170, 196, 182, 183, 171, 160, 161, 197, 182, 196, 172, 160, 171, 197, 181, 182, 198, 181, 197, 173, 160, 172, 173, 159, 160, 198, 180, 181, 199, 180, 198, 174, 159, 173, 199, 179, 180, 200, 179, 199, 174, 158, 159, 175, 158, 174, 200, 178, 179, 201, 178, 200, 176, 158, 175, 176, 138, 158, 138, 157, 158, 97, 99, 201, 99, 100, 201, 100, 101, 201, 101, 102, 201, 102, 103, 201, 103, 104, 201, 104, 105, 201, 105, 106, 201, 106, 107, 201, 107, 108, 201, 108, 109, 201, 109, 110, 201, 110, 178, 201, 110, 111, 178, 111, 177, 178, 177, 137, 176, 137, 138, 176, 112, 177, 111, 139, 157, 138, 177, 136, 137, 113, 177, 112, 140, 157, 139, 177, 135, 136, 114, 177, 113, 141, 157, 140, 177, 134, 135, 115, 177, 114, 115, 134, 177, 142, 157, 141, 115, 133, 134, 142, 156, 157, 116, 133, 115, 116, 132, 133, 143, 156, 142, 116, 131, 132, 117, 131, 116, 144, 156, 143, 117, 130, 131, 118, 130, 117, 145, 156, 144, 118, 129, 130, 145, 155, 156, 119, 129, 118, 119, 128, 129, 146, 155, 145, 119, 127, 128, 120, 127, 119, 147, 155, 146, 120, 126, 127, 147, 154, 155, 121, 126, 120, 97, 98, 99, 121, 125, 126, 148, 154, 147, 122, 125, 121, 149, 154, 148, 149, 153, 154, 123, 125, 122, 150, 153, 149, 150, 152, 153, 124, 125, 123, 151, 152, 150, 241, 239, 240, 241, 238, 239, 242, 238, 241, 242, 237, 238, 243, 237, 242, 243, 236, 237, 244, 236, 243, 244, 235, 236, 245, 235, 244, 245, 234, 235, 246, 234, 245, 246, 233, 234, 247, 289, 246, 289, 233, 246, 247, 288, 289, 290, 233, 289, 247, 287, 288, 291, 233, 290, 247, 286, 287, 292, 233, 291, 292, 232, 233, 247, 285, 286, 248, 285, 247, 293, 232, 292, 248, 284, 285, 294, 232, 293, 248, 283, 284, 295, 232, 294, 248, 282, 283, 296, 232, 295, 249, 282, 248, 296, 231, 232, 249, 281, 282, 297, 231, 296, 249, 280, 281, 298, 231, 297, 250, 280, 249, 298, 230, 231, 250, 279, 280, 299, 230, 298, 250, 278, 279, 300, 230, 299, 251, 278, 250, 251, 277, 278, 300, 229, 230, 301, 229, 300, 251, 301, 277, 251, 229, 301, 252, 229, 251, 252, 228, 229, 253, 227, 252, 227, 228, 252, 253, 226, 227, 254, 226, 253, 254, 225, 226, 254, 224, 225, 255, 224, 254, 255, 223, 224, 256, 223, 255, 256, 222, 223, 204, 276, 203, 256, 221, 222, 205, 276, 204, 206, 276, 205, 257, 221, 256, 257, 220, 221, 207, 276, 206, 208, 276, 207, 257, 219, 220, 209, 276, 208, 257, 218, 219, 210, 276, 209, 258, 218, 257, 211, 276, 210, 258, 217, 218, 212, 276, 211, 258, 216, 217, 213, 276, 212, 214, 276, 213, 258, 215, 216, 215, 276, 214, 258, 276, 215, 259, 276, 258, 259, 275, 276, 260, 275, 259, 260, 274, 275, 260, 273, 274, 261, 273, 260, 261, 272, 273, 261, 271, 272, 262, 271, 261, 262, 270, 271, 262, 269, 270, 263, 269, 262, 263, 268, 269, 263, 267, 268, 263, 266, 267, 264, 266, 263, 264, 265, 266, 302, 329, 328, 329, 327, 328, 329, 326, 327, 329, 325, 326, 329, 324, 325, 329, 323, 324, 329, 322, 323, 329, 330, 322, 330, 331, 322, 331, 321, 322, 302, 355, 329, 332, 321, 331, 333, 321, 332, 334, 321, 333, 334, 320, 321, 335, 320, 334, 336, 320, 335, 336, 319, 320, 337, 319, 336, 337, 318, 319, 338, 318, 337, 339, 318, 338, 339, 317, 318, 340, 317, 339, 340, 316, 317, 341, 316, 340, 341, 315, 316, 342, 315, 341, 343, 315, 342, 343, 314, 315, 344, 314, 343, 344, 313, 314, 345, 313, 344, 346, 313, 345, 346, 312, 313, 347, 312, 346, 347, 311, 312, 348, 311, 347, 349, 311, 348, 349, 310, 311, 350, 310, 349, 350, 309, 310, 351, 309, 350, 352, 309, 351, 352, 308, 309, 353, 308, 352, 354, 308, 353, 302, 354, 355, 302, 308, 354, 302, 307, 308, 302, 306, 307, 302, 305, 306, 302, 304, 305, 302, 303, 304, 369, 367, 368, 369, 366, 367, 370, 366, 369, 370, 365, 366, 370, 364, 365, 371, 364, 370, 371, 363, 364, 371, 362, 363, 372, 362, 371, 372, 361, 362, 372, 360, 361, 373, 360, 372, 373, 359, 360, 373, 358, 359, 374, 358, 373, 374, 357, 358, 374, 356, 357, 375, 356, 374, 375, 481, 356, 481, 482, 356, 482, 483, 356, 483, 484, 356, 484, 485, 356, 485, 486, 356, 486, 487, 356, 487, 488, 356, 488, 489, 356, 376, 479, 375, 479, 480, 375, 480, 481, 375, 377, 478, 376, 478, 479, 376, 378, 476, 377, 476, 477, 377, 477, 478, 377, 378, 475, 476, 378, 474, 475, 378, 473, 474, 378, 472, 473, 378, 471, 472, 379, 471, 378, 379, 470, 471, 379, 469, 470, 379, 468, 469, 379, 467, 468, 380, 467, 379, 380, 466, 467, 380, 465, 466, 380, 464, 465, 381, 464, 380, 381, 463, 464, 381, 462, 463, 381, 461, 462, 381, 460, 461, 381, 459, 460, 382, 459, 381, 382, 458, 459, 382, 457, 458, 382, 456, 457, 383, 456, 382, 383, 455, 456, 383, 454, 455, 383, 453, 454, 384, 453, 383, 384, 452, 453, 385, 452, 384, 385, 451, 452, 385, 450, 451, 386, 450, 385, 386, 449, 450, 387, 449, 386, 387, 448, 449, 387, 447, 448, 388, 447, 387, 388, 446, 447, 389, 446, 388, 389, 445, 446, 389, 444, 445, 390, 444, 389, 390, 443, 444, 391, 443, 390, 391, 442, 443, 392, 442, 391, 392, 441, 442, 417, 415, 416, 392, 440, 441, 393, 440, 392, 417, 414, 415, 394, 440, 393, 417, 413, 414, 395, 440, 394, 395, 439, 440, 417, 412, 413, 396, 439, 395, 417, 411, 412, 397, 439, 396, 417, 410, 411, 398, 439, 397, 398, 438, 439, 417, 409, 410, 399, 438, 398, 400, 438, 399, 417, 408, 409, 401, 438, 400, 417, 407, 408, 402, 438, 401, 417, 406, 407, 403, 438, 402, 417, 405, 406, 404, 438, 403, 417, 404, 405, 404, 437, 438, 417, 437, 404, 417, 436, 437, 417, 435, 436, 418, 435, 417, 418, 434, 435, 419, 434, 418, 420, 434, 419, 420, 433, 434, 421, 433, 420, 422, 433, 421, 422, 432, 433, 423, 432, 422, 423, 431, 432, 424, 431, 423, 425, 431, 424, 425, 430, 431, 426, 430, 425, 427, 430, 426, 427, 429, 430, 428, 429, 427, 492, 490, 491, 492, 529, 490, 505, 503, 504, 505, 502, 503, 505, 501, 502, 505, 500, 501, 505, 499, 500, 506, 499, 505, 506, 498, 499, 506, 497, 498, 506, 496, 497, 507, 496, 506, 507, 495, 496, 507, 494, 495, 507, 493, 494, 507, 492, 493, 508, 492, 507, 508, 564, 492, 564, 565, 492, 565, 566, 492, 566, 567, 492, 567, 529, 492, 509, 561, 508, 561, 562, 508, 562, 563, 508, 563, 564, 508, 510, 558, 509, 558, 559, 509, 559, 560, 509, 560, 561, 509, 511, 555, 510, 555, 556, 510, 556, 557, 510, 557, 558, 510, 511, 554, 555, 511, 553, 554, 512, 553, 511, 512, 552, 553, 512, 551, 552, 530, 529, 567, 512, 550, 551, 513, 550, 512, 513, 549, 550, 513, 548, 549, 514, 548, 513, 514, 547, 548, 514, 546, 547, 515, 546, 514, 515, 545, 546, 516, 545, 515, 516, 544, 545, 516, 543, 544, 517, 543, 516, 517, 542, 543, 517, 541, 542, 518, 541, 517, 518, 540, 541, 519, 540, 518, 519, 539, 540, 519, 538, 539, 520, 538, 519, 520, 537, 538, 520, 536, 537, 521, 536, 520, 521, 535, 536, 521, 534, 535, 521, 533, 534, 522, 533, 521, 522, 532, 533, 522, 531, 532, 522, 530, 531, 522, 529, 530, 523, 529, 522, 524, 529, 523, 525, 529, 524, 526, 529, 525, 527, 529, 526, 528, 529, 527, 585, 583, 584, 585, 582, 583, 586, 582, 585, 586, 581, 582, 587, 581, 586, 587, 580, 581, 588, 580, 587, 588, 579, 580, 589, 579, 588, 589, 578, 579, 590, 578, 589, 590, 577, 578, 591, 577, 590, 591, 576, 577, 592, 576, 591, 592, 575, 576, 593, 575, 592, 593, 574, 575, 594, 574, 593, 594, 573, 574, 595, 573, 594, 595, 572, 573, 596, 572, 595, 597, 572, 596, 597, 619, 572, 597, 618, 619, 598, 618, 597, 598, 617, 618, 599, 617, 598, 599, 616, 617, 600, 616, 599, 600, 615, 616, 601, 615, 600, 601, 614, 615, 602, 614, 601, 602, 613, 614, 603, 613, 602, 603, 612, 613, 604, 612, 603, 604, 611, 612, 605, 611, 604, 605, 610, 611, 606, 610, 605, 606, 609, 610, 607, 609, 606, 607, 608, 609, 570, 568, 569, 570, 571, 568, 650, 648, 649, 650, 647, 648, 623, 621, 622, 623, 620, 621, 651, 647, 650, 651, 646, 647, 651, 645, 646, 652, 645, 651, 652, 644, 645, 624, 620, 623, 652, 643, 644, 625, 620, 624, 653, 643, 652, 653, 642, 643, 626, 620, 625, 627, 620, 626, 653, 641, 642, 654, 641, 653, 628, 620, 627, 654, 640, 641, 629, 674, 628, 674, 620, 628, 654, 639, 640, 630, 674, 629, 654, 638, 639, 631, 674, 630, 655, 638, 654, 632, 674, 631, 655, 637, 638, 633, 674, 632, 655, 636, 637, 634, 674, 633, 655, 635, 636, 635, 674, 634, 655, 674, 635, 655, 673, 674, 675, 620, 674, 656, 673, 655, 656, 672, 673, 656, 671, 672, 657, 671, 656, 657, 670, 671, 658, 670, 657, 658, 669, 670, 658, 668, 669, 659, 668, 658, 659, 667, 668, 659, 666, 667, 660, 666, 659, 660, 665, 666, 661, 665, 660, 661, 664, 665, 661, 663, 664, 662, 663, 661, 678, 676, 677, 678, 679, 676, 682, 688, 681, 688, 680, 681, 688, 689, 680, 682, 687, 688, 682, 684, 687, 684, 686, 687, 684, 685, 686, 682, 683, 684, 691, 719, 690, 719, 718, 690, 719, 717, 718, 719, 716, 717, 719, 715, 716, 719, 714, 715, 719, 713, 714, 719, 712, 713, 719, 711, 712, 719, 720, 711, 720, 710, 711, 691, 745, 719, 721, 710, 720, 722, 710, 721, 723, 710, 722, 723, 709, 710, 724, 709, 723, 725, 709, 724, 726, 709, 725, 726, 708, 709, 727, 708, 726, 728, 708, 727, 729, 708, 728, 729, 707, 708, 730, 707, 729, 731, 707, 730, 731, 706, 707, 732, 706, 731, 733, 706, 732, 733, 705, 706, 734, 705, 733, 734, 704, 705, 735, 704, 734, 736, 704, 735, 736, 703, 704, 737, 703, 736, 738, 703, 737, 738, 702, 703, 739, 702, 738, 740, 702, 739, 741, 702, 740, 742, 702, 741, 742, 701, 702, 743, 701, 742, 744, 701, 743, 691, 693, 745, 693, 744, 745, 693, 701, 744, 693, 700, 701, 693, 699, 700, 693, 698, 699, 693, 697, 698, 693, 696, 697, 693, 695, 696, 693, 694, 695, 691, 692, 693, 748, 746, 747, 748, 749, 746, 752, 750, 751, 752, 755, 750, 752, 754, 755, 752, 753, 754, 758, 764, 757, 764, 756, 757, 764, 765, 756, 758, 763, 764, 758, 760, 763, 760, 762, 763, 760, 761, 762, 758, 759, 760});

    _verty = std::vector<float>({-0.4125114977359772, 1.0974465780577702e-09, 0.025106651708483696, -0.4087001383304596, 1.0870784272754008e-09, 0.02486945502460003, -0.4050680696964264, 1.0568049768622245e-09, 0.024176878854632378, -0.40164390206336975, 1.0078806678137653e-09, 0.023057622835040092, -0.39845672249794006, 9.415549451219363e-10, 0.021540267392992973, -0.3955360949039459, 8.590823052934127e-10, 0.01965351216495037, -0.3929106295108795, 7.61712026786654e-10, 0.017425939440727234, -0.39060941338539124, 6.506957750396225e-10, 0.014886184595525265, -0.38866105675697327, 5.272870473582714e-10, 0.0120629221200943, -0.3870956003665924, 3.9273631569081147e-10, 0.008984759449958801, -0.38594117760658264, 2.482941352521806e-10, 0.005680307745933533, -0.38522735238075256, 9.521505806020514e-11, 0.0021782666444778442, -0.38498273491859436, -6.52516304877615e-11, -0.0014927833108231425, -0.3852182924747467, -2.3621679612340074e-10, -0.0054040104150772095, -0.38590875267982483, -3.9804873286364284e-10, -0.009106293320655823, -0.3870302736759186, -5.496570421037461e-10, -0.012574687600135803, -0.3885580599308014, -6.899462112741617e-10, -0.0157841295003891, -0.3904682695865631, -8.178245303192e-10, -0.018709644675254822, -0.3927361071109772, -9.321977634257905e-10, -0.021326199173927307, -0.39533868432044983, -1.0319756160726001e-09, -0.023608850315213203, -0.3982502520084381, -1.116062353645475e-09, -0.02553253062069416, -0.40144792199134827, -1.1833650725989742e-09, -0.02707223780453205, -0.40490689873695374, -1.2327922016552861e-09, -0.028202997520565987, -0.40860286355018616, -1.263250615224365e-09, -0.02889980562031269, -0.4125114977359772, -1.2736461885154426e-09, -0.0291376281529665, -0.41658082604408264, -1.2636388602160764e-09, -0.028908688575029373, -0.42041030526161194, -1.2342030730749798e-09, -0.02823527529835701, -0.4239784777164459, -1.186222009508242e-09, -0.027137596160173416, -0.42726340889930725, -1.1205749661513664e-09, -0.025635767728090286, -0.4302436411380768, -1.038145347465047e-09, -0.023749995976686478, -0.43289676308631897, -9.398147815531388e-10, -0.02150045707821846, -0.4352017939090729, -8.264628981180522e-10, -0.018907267600297928, -0.43713632225990295, -6.989728795758765e-10, -0.015990635380148888, -0.43867936730384827, -5.582251327851395e-10, -0.012770702131092548, -0.43980804085731506, -4.051004531824276e-10, -0.00926761794835329, -0.4405013620853424, -2.404833554514596e-10, -0.005501618143171072, -0.44073739647865295, -6.525184559347252e-11, -0.0014927882002666593, -0.44049468636512756, 9.948120105462976e-11, 0.0022758645936846733, -0.4397837221622467, 2.553454392373311e-10, 0.005841622594743967, -0.43863025307655334, 4.013026577709411e-10, 0.009180734865367413, -0.43705907464027405, 5.363132715707764e-10, 0.012269417755305767, -0.4350959360599518, 6.593338652827185e-10, 0.015083800069987774, -0.4327661097049713, 7.693274350906165e-10, 0.017600160092115402, -0.4300953447818756, 8.652518146412547e-10, 0.019794654101133347, -0.42710843682289124, 9.460687788731548e-10, 0.02164353057742119, -0.42383113503456116, 1.0107361614331012e-09, 0.02312294766306877, -0.42028918862342834, 1.0582157372596157e-09, 0.024209152907133102, -0.41650739312171936, 1.0874665612448098e-09, 0.024878334254026413, -0.4123956263065338, 6.912644900936016e-10, 0.015814287588000298, -0.41491666436195374, 6.847145073152205e-10, 0.015664441511034966, -0.41730132699012756, 6.655243578457259e-10, 0.015225422568619251, -0.4195334017276764, 6.343819913823268e-10, 0.014512968249619007, -0.4215976297855377, 5.91975135577627e-10, 0.013542812317609787, -0.42347779870033264, 5.389890755935767e-10, 0.012330632656812668, -0.42515817284584045, 4.761142036180388e-10, 0.010892223566770554, -0.42662301659584045, 4.040357770573877e-10, 0.009243261069059372, -0.42785707116127014, 3.2344288358743256e-10, 0.007399510592222214, -0.4288441240787506, 2.350220296154504e-10, 0.005376677494496107, -0.42956891655921936, 1.394611370830745e-10, 0.003190498799085617, -0.4300152361392975, 3.744922427717512e-11, 0.0008567384211346507, -0.4301673471927643, -7.03284305791918e-11, -0.0016089269192889333, -0.43002620339393616, -1.8947216018361246e-10, -0.004334617871791124, -0.4296089708805084, -3.003815252089481e-10, -0.006871927995234728, -0.42892566323280334, -4.02653937969788e-10, -0.009211648255586624, -0.4279862940311432, -4.958803923038602e-10, -0.011344421654939651, -0.4267994463443756, -5.79658432364738e-10, -0.013261038810014725, -0.4253756105899811, -6.535827989928578e-10, -0.01495223119854927, -0.42372480034828186, -7.172457627824258e-10, -0.01640867069363594, -0.4218555986881256, -7.702422588629076e-10, -0.01762108877301216, -0.4197784960269928, -8.121683880979447e-10, -0.018580246716737747, -0.4175030291080475, -8.426176978382216e-10, -0.019276846200227737, -0.41503873467445374, -8.611837354344232e-10, -0.019701587036252022, -0.4123956263065338, -8.674627127724932e-10, -0.019845234230160713, -0.4099656641483307, -8.608906365559221e-10, -0.01969488151371479, -0.4076792299747467, -8.415363961233879e-10, -0.0192521084100008, -0.40554967522621155, -8.099471648925771e-10, -0.018529431894421577, -0.4035893976688385, -7.666688395246979e-10, -0.017539339140057564, -0.40181127190589905, -7.122498146827638e-10, -0.01629437692463398, -0.4002281725406647, -6.472359315168319e-10, -0.01480703242123127, -0.39885345101356506, -5.721729756658078e-10, -0.013089791871607304, -0.3976999819278717, -4.876068437908998e-10, -0.011155144311487675, -0.3967796862125397, -3.940846537986431e-10, -0.00901560578495264, -0.39610686898231506, -2.9215482810762694e-10, -0.006683723069727421, -0.39569345116615295, -1.823605849660126e-10, -0.0041719237342476845, -0.39555326104164124, -6.525167212112493e-11, -0.0014927842421457171, -0.395698219537735, 4.136006467869713e-11, 0.0009462080197408795, -0.39612308144569397, 1.4240014722943783e-10, 0.0032577356323599815, -0.3968125879764557, 2.37163816363406e-10, 0.005425675772130489, -0.39775148034095764, 3.2494759660828265e-10, 0.007433934602886438, -0.3989240229129791, 4.050441926306547e-10, 0.009266330860555172, -0.40031543374061584, 4.767486960766121e-10, 0.01090673916041851, -0.4019099771976471, 5.393565039035764e-10, 0.012339038774371147, -0.4036923944950104, 5.921628187799399e-10, 0.013547105714678764, -0.4056479036808014, 6.344614833508899e-10, 0.014514787122607231, -0.40776029229164124, 6.655491713303263e-10, 0.015225989744067192, -0.4100143015384674, 6.847171163393284e-10, 0.01566450111567974, -0.29809918999671936, 1.0517521298325505e-09, 0.024061284959316254, -0.29809918999671936, -1.2279496308664761e-09, -0.028092212975025177, -0.3084370195865631, -1.2279496308664761e-09, -0.028092212975025177, -0.3084370195865631, 4.2724512816505467e-10, 0.009774229489266872, -0.30949607491493225, 4.788021090718075e-10, 0.01095371600240469, -0.3105298578739166, 5.244891743139135e-10, 0.011998913250863552, -0.3115479052066803, 5.645706679935358e-10, 0.012915871106088161, -0.3125583231449127, 5.993084917221836e-10, 0.013710579834878445, -0.31357064843177795, 6.289709864049087e-10, 0.014389178715646267, -0.31459298729896545, 6.538199426309177e-10, 0.01495765708386898, -0.3156353533267975, 6.741199265469788e-10, 0.015422066673636436, -0.3167053759098053, 6.901366700340361e-10, 0.01578848622739315, -0.31781306862831116, 7.021332404377745e-10, 0.016062935814261436, -0.3189660608768463, 7.103754251502892e-10, 0.016251495108008385, -0.32017436623573303, 7.151263470284164e-10, 0.01636018417775631, -0.32144656777381897, 7.16650516707773e-10, 0.016395052894949913, -0.322704941034317, 7.133390544922236e-10, 0.01631929539144039, -0.32391801476478577, 7.03275715441265e-10, 0.016089072450995445, -0.32507243752479553, 6.862663215478904e-10, 0.015699943527579308, -0.32615724205970764, 6.621168058273952e-10, 0.015147467143833637, -0.3271590769290924, 6.306331568062262e-10, 0.014427204616367817, -0.32806697487831116, 5.916224732338549e-10, 0.013534744270145893, -0.3288685381412506, 5.448893558579471e-10, 0.012465615756809711, -0.3295513689517975, 4.902410699614279e-10, 0.011215408332645893, -0.3301035463809967, 4.2748346529286607e-10, 0.009779681451618671, -0.330512672662735, 3.5642241935640584e-10, 0.00815399456769228, -0.33076730370521545, 2.768625606552888e-10, 0.006333877332508564, -0.33085504174232483, 1.8861240347334274e-10, 0.004314948804676533, -0.33085504174232483, -1.2279497418887786e-09, -0.028092216700315475, -0.3411923944950104, -1.2279497418887786e-09, -0.028092216700315475, -0.3411923944950104, 4.272450171427522e-10, 0.009774226695299149, -0.34213748574256897, 4.682331744554347e-10, 0.010711926966905594, -0.34310975670814514, 5.072126052496628e-10, 0.011603672057390213, -0.34410205483436584, 5.43864120405857e-10, 0.01244216039776802, -0.34510722756385803, 5.77871084317394e-10, 0.013220150023698807, -0.34611955285072327, 6.089170834222557e-10, 0.013930398970842361, -0.3471309244632721, 6.366828175785599e-10, 0.014565604738891125, -0.3481351435184479, 6.608530944696156e-10, 0.015118557028472424, -0.34912553429603577, 6.811088359981454e-10, 0.015581953339278698, -0.3500949442386627, 6.971346833140046e-10, 0.0159485824406147, -0.3510362207889557, 7.086114472976135e-10, 0.016211140900850296, -0.35194268822669983, 7.152226033646514e-10, 0.0163623858243227, -0.3528081476688385, 7.166503501743193e-10, 0.016395049169659615, -0.35426488518714905, 7.127539669582461e-10, 0.016305910423398018, -0.3556653559207916, 7.01136482206266e-10, 0.01604013331234455, -0.35699525475502014, 6.819034226168696e-10, 0.015600131824612617, -0.3582417070865631, 6.551589826209181e-10, 0.014988290145993233, -0.35939136147499084, 6.210112979410098e-10, 0.014207081869244576, -0.36043086647987366, 5.795632307403764e-10, 0.013258861377835274, -0.36134687066078186, 5.309243045203971e-10, 0.012146132066845894, -0.36212649941444397, 4.751973814443033e-10, 0.010871248319745064, -0.3627559244632721, 4.1248923721148856e-10, 0.009436653926968575, -0.36322179436683655, 3.429054817871702e-10, 0.00784476287662983, -0.36351123452186584, 2.665528631151659e-10, 0.0060980189591646194, -0.3636104166507721, 1.8353565889306367e-10, 0.00419880636036396, -0.3636104166507721, -1.227949852911081e-09, -0.028092218562960625, -0.37394824624061584, -1.2279499639333835e-09, -0.028092220425605774, -0.37394824624061584, 2.0384471888235112e-10, 0.004663423635065556, -0.37380948662757874, 3.3448477321229575e-10, 0.007652119733393192, -0.37340036034584045, 4.569100098272827e-10, 0.010452882386744022, -0.37273040413856506, 5.70519853582141e-10, 0.013051972724497318, -0.37181010842323303, 6.747163938669587e-10, 0.015435711480677128, -0.3706494867801666, 7.688977787800866e-10, 0.01759033091366291, -0.3692585527896881, 8.524673744680911e-10, 0.019502179697155952, -0.36764732003211975, 9.248245502746499e-10, 0.0211575198918581, -0.3658258020877838, 9.853702298556755e-10, 0.022542642429471016, -0.36380448937416077, 1.0335049482890213e-09, 0.023643838241696358, -0.3615933954715729, 1.0686284079852726e-09, 0.0244473684579134, -0.3592020571231842, 1.0901425318010638e-09, 0.024939553812146187, -0.3566414415836334, 1.0974468001023752e-09, 0.025106655433773994, -0.3548232614994049, 1.0936220817825415e-09, 0.02501915581524372, -0.3530837595462799, 1.0824969809419827e-09, 0.024764643982052803, -0.351419597864151, 1.0646031833871916e-09, 0.02435528114438057, -0.34982696175575256, 1.0404692663001924e-09, 0.023803163319826126, -0.34830155968666077, 1.0106218084615648e-09, 0.02312033250927925, -0.3468405306339264, 9.755921626108943e-10, 0.022318948060274124, -0.3454400599002838, 9.359080177517853e-10, 0.021411079913377762, -0.3440963327884674, 8.920995053784964e-10, 0.020408857613801956, -0.34280601143836975, 8.446929267158509e-10, 0.019324321299791336, -0.3415652811527252, 7.942197455257372e-10, 0.01816963031888008, -0.3403708040714264, 7.412089830793889e-10, 0.016956884413957596, -0.33921781182289124, 6.86186774068176e-10, 0.01569812372326851, -0.33830609917640686, 7.50807249705332e-10, 0.017176467925310135, -0.33731475472450256, 8.100866644156213e-10, 0.01853262260556221, -0.33624711632728577, 8.639715609604082e-10, 0.01976536586880684, -0.3351050913333893, 9.124085931233594e-10, 0.020873475819826126, -0.33389249444007874, 9.553443591769906e-10, 0.021855730563402176, -0.33261170983314514, 9.927278998844713e-10, 0.02271096780896187, -0.3312655985355377, 1.0245047032952925e-09, 0.02343793585896492, -0.3298570215702057, 1.0506226999495993e-09, 0.024035444483160973, -0.32838836312294006, 1.0710294873206294e-09, 0.02450229786336422, -0.32686296105384827, 1.0856705534578737e-09, 0.024837246164679527, -0.3252836763858795, 1.0944950501468043e-09, 0.025039127096533775, -0.32365337014198303, 1.0974469111246776e-09, 0.025106659159064293, -0.3224312365055084, 1.0951137774384279e-09, 0.02505328319966793, -0.3212033808231354, 1.0880922829414885e-09, 0.024892648681998253, -0.3199688494205475, 1.0763444580064174e-09, 0.024623891338706017, -0.31872764229774475, 1.059837995143198e-09, 0.02424626611173153, -0.31747785210609436, 1.038534924724388e-09, 0.023758908733725548, -0.3162194788455963, 1.012402717215366e-09, 0.02316107414662838, -0.314951092004776, 9.814036250332947e-10, 0.022451898083090782, -0.3136726915836334, 9.455051186435526e-10, 0.021630635485053062, -0.31238284707069397, 9.046693394409999e-10, 0.020696422085165977, -0.31108060479164124, 8.588611488669073e-10, 0.01964845322072506, -0.309765487909317, 8.080480173866533e-10, 0.018485983833670616, -0.3084370195865631, 7.521921974174006e-10, 0.017208151519298553, -0.3084370195865631, 1.0517521298325505e-09, 0.024061284959316254, -0.28648391366004944, -5.679023362681335e-10, -0.012992090545594692, -0.28497567772865295, -6.095614013545969e-10, -0.0139451390132308, -0.2834712564945221, -6.481513104006353e-10, -0.014827973209321499, -0.28196826577186584, -6.835690902207148e-10, -0.015638237819075584, -0.2804652750492096, -7.157079928710175e-10, -0.016373490914702415, -0.27896037697792053, -7.444612148965746e-10, -0.017031287774443626, -0.27745261788368225, -7.697245063553737e-10, -0.0176092442125082, -0.27594009041786194, -7.913910082812947e-10, -0.01810491643846035, -0.2744208872318268, -8.093553049981494e-10, -0.01851589046418667, -0.2728935778141022, -8.235117032739936e-10, -0.018839752301573753, -0.2713567316532135, -8.337548429437902e-10, -0.0190740879625082, -0.26980844140052795, -8.399778650414191e-10, -0.019216453656554222, -0.2682472765445709, -8.420765196248681e-10, -0.0192644651979208, -0.2658349573612213, -8.372186832694695e-10, -0.019153330475091934, -0.2635928690433502, -8.226831438307158e-10, -0.01882079616189003, -0.26152148842811584, -7.985219152573109e-10, -0.018268052488565445, -0.2596217691898346, -7.647885102990415e-10, -0.017496321350336075, -0.2578951418399811, -7.215349429046114e-10, -0.016506794840097427, -0.2563416063785553, -6.688133380450267e-10, -0.01530066505074501, -0.25496259331703186, -6.066783742042503e-10, -0.013879183679819107, -0.25375810265541077, -5.351822318644395e-10, -0.012243542820215225, -0.25273004174232483, -4.543770082410248e-10, -0.010394934564828873, -0.25187841057777405, -3.6431740957354464e-10, -0.008334610611200333, -0.25120416283607483, -2.650541730542244e-10, -0.006063732784241438, -0.2507082521915436, -1.5664210206711715e-10, -0.0035835534799844027, -0.2874127924442291, -1.5664224084499523e-10, -0.003583556739613414, -0.28723111748695374, 4.508620213283798e-11, 0.0010314520914107561, -0.2866951525211334, 2.2890249418150432e-10, 0.005236678756773472, -0.2858177721500397, 3.94878324483372e-10, 0.009033762849867344, -0.2846123278141022, 5.430826899299745e-10, 0.012424283660948277, -0.2830926477909088, 6.735885738073932e-10, 0.01540991012006998, -0.2812711298465729, 7.864637274757058e-10, 0.01799219287931919, -0.27916207909584045, 8.817797603200006e-10, 0.02017276920378208, -0.27677837014198303, 9.59608281725366e-10, 0.02195327915251255, -0.2741333544254303, 1.0200184030750847e-09, 0.023335302248597145, -0.27123990654945374, 1.0630818447765478e-09, 0.02432047761976719, -0.26811185479164124, 1.0888675516795843e-09, 0.02491038478910923, -0.2647625505924225, 1.0974471331692826e-09, 0.02510666474699974, -0.2612573206424713, 1.087856693615663e-09, 0.024887260049581528, -0.25795474648475647, 1.0596492572290117e-09, 0.02424195036292076, -0.2548753321170807, 1.013671813154815e-09, 0.023190107196569443, -0.2520371973514557, 9.507709064493497e-10, 0.021751102060079575, -0.2494608461856842, 8.717906951893895e-10, 0.019944246858358383, -0.24716535210609436, 7.775781130092696e-10, 0.01778891310095787, -0.24516978859901428, 6.689810927440476e-10, 0.015304503031075, -0.2434937059879303, 5.46843736959346e-10, 0.012510326690971851, -0.24215617775917053, 4.1201420053482707e-10, 0.009425786323845387, -0.2411767542362213, 2.6533661379168905e-10, 0.00607019430026412, -0.24057498574256897, 1.0765902058729182e-10, 0.002462951233610511, -0.24037042260169983, -6.017445569606039e-11, -0.0013766310876235366, -0.24055781960487366, -2.1630576496622922e-10, -0.004948499146848917, -0.24111667275428772, -3.6866576458294276e-10, -0.008434089832007885, -0.24203982949256897, -5.153837911997527e-10, -0.011790606193244457, -0.24332156777381897, -6.545929909229642e-10, -0.014975341968238354, -0.24495473504066467, -7.844214167107566e-10, -0.01794547028839588, -0.24693313241004944, -9.030037828594573e-10, -0.02065831795334816, -0.24925008416175842, -1.0084690860168166e-09, -0.023071084171533585, -0.2518998682498932, -1.0989494869662053e-09, -0.02514103427529335, -0.2548748552799225, -1.1725755921787595e-09, -0.026825401932001114, -0.2581698000431061, -1.2274792293709424e-09, -0.02808145061135292, -0.2617775499820709, -1.2617923372815198e-09, -0.028866443783044815, -0.2656919062137604, -1.2736456334039303e-09, -0.029137615114450455, -0.2678357660770416, -1.271841409966612e-09, -0.029096340760588646, -0.2698618471622467, -1.2664053139488374e-09, -0.028971975669264793, -0.2717830240726471, -1.2573032615037505e-09, -0.028763746842741966, -0.2736121714115143, -1.244497727093119e-09, -0.02847079001367092, -0.27536216378211975, -1.227956070160019e-09, -0.028092360123991966, -0.2770463526248932, -1.2076404320993106e-09, -0.027627592906355858, -0.2786771357059479, -1.1835170621310453e-09, -0.027075713500380516, -0.2802673876285553, -1.1555519874306697e-09, -0.02643594704568386, -0.28183045983314514, -1.1237074604153463e-09, -0.02570742927491665, -0.2833787500858307, -1.0879482870151946e-09, -0.024889355525374413, -0.2849256098270416, -1.0482406054279636e-09, -0.02398095093667507, -0.28648391366004944, -1.004549332606075e-09, -0.02298141084611416, -0.2509404718875885, 1.4291788585918397e-10, 0.0032695799600332975, -0.25135865807533264, 2.297337597934046e-10, 0.005255695898085833, -0.2519170343875885, 3.098329370843089e-10, 0.007088151294738054, -0.25261369347572327, 3.8305772442903674e-10, 0.00876333937048912, -0.25344863533973694, 4.4924666764423193e-10, 0.010277565568685532, -0.2544204294681549, 5.082446685733544e-10, 0.011627282947301865, -0.25552859902381897, 5.598902452774723e-10, 0.012808796018362045, -0.2567721903324127, 6.040257738426646e-10, 0.013818498700857162, -0.25815072655677795, 6.40492270331805e-10, 0.014652755111455917, -0.25966277718544006, 6.691308618300695e-10, 0.015307929366827011, -0.26130834221839905, 6.897838411568102e-10, 0.015780415385961533, -0.2630859911441803, 7.022923909083545e-10, 0.016066577285528183, -0.2649952471256256, 7.064961948799464e-10, 0.016162749379873276, -0.2667657434940338, 7.020005132751805e-10, 0.01605989970266819, -0.2684151232242584, 6.887259651477962e-10, 0.015756214037537575, -0.2699390947818756, 6.669891861044164e-10, 0.015258933417499065, -0.27133193612098694, 6.371065341959081e-10, 0.014575297944247723, -0.2725893557071686, 5.993971985418511e-10, 0.013712609186768532, -0.2737065851688385, 5.541778147488685e-10, 0.012678110972046852, -0.2746788561344147, 5.017649629124321e-10, 0.011479044333100319, -0.27550092339515686, 4.424777488853948e-10, 0.010122710838913918, -0.27616754174232483, 3.7663142049559895e-10, 0.00861632265150547, -0.27667489647865295, 3.045438623505703e-10, 0.006967151537537575, -0.277017742395401, 2.2653423581431298e-10, 0.005182499065995216, -0.27719131112098694, 1.429177748368815e-10, 0.003269577631726861, -0.15731969475746155, -1.2279490757549638e-09, -0.028092199936509132, -0.18821683526039124, -1.2279491867772663e-09, -0.02809220366179943, -0.19453445076942444, -1.210851308108829e-09, -0.02770104818046093, -0.20040622353553772, -1.1614046391272836e-09, -0.02656984142959118, -0.20581260323524475, -1.0823737461862493e-09, -0.024761825799942017, -0.210733562707901, -9.765293018659804e-10, -0.022340387105941772, -0.21515002846717834, -8.466383150107504e-10, -0.01936882734298706, -0.21904149651527405, -6.954690157101595e-10, -0.015910476446151733, -0.22238841652870178, -5.257883572973299e-10, -0.01202863547950983, -0.22517123818397522, -3.403645143507106e-10, -0.007786632515490055, -0.22736993432044983, -1.4196577247105324e-10, -0.0032477984204888344, -0.22896495461463928, 6.66409150085201e-11, 0.0015245664399117231, -0.22993674874305725, 2.8268604124193075e-10, 0.006467102561146021, -0.230264812707901, 5.034052064090133e-10, 0.011516569182276726, -0.22999444603919983, 7.091902620715018e-10, 0.01622438244521618, -0.22917428612709045, 9.154872970817962e-10, 0.020943908020853996, -0.227792888879776, 1.1187880621932322e-09, 0.025594888255000114, -0.2258378565311432, 1.315583197936121e-09, 0.030097035691142082, -0.22329774498939514, 1.5023645660861007e-09, 0.034370094537734985, -0.22015920281410217, 1.6756237508630534e-09, 0.03833380341529846, -0.2164112627506256, 1.831852780576071e-09, 0.0419079065322876, -0.21204152703285217, 1.96754479375727e-09, 0.04501217603683472, -0.20703759789466858, 2.0791888211135756e-09, 0.04756629467010498, -0.20138755440711975, 2.1632782232217096e-09, 0.04949003458023071, -0.1950789988040924, 2.2163044732792514e-09, 0.05070313811302185, -0.18810048699378967, 2.2347601547068052e-09, 0.05112535133957863, -0.15731969475746155, 2.2347601547068052e-09, 0.05112535133957863, -0.16870275139808655, 1.7879584479629784e-09, 0.0409037210047245, -0.1862422525882721, 1.7879584479629784e-09, 0.0409037210047245, -0.191538006067276, 1.7759670400963046e-09, 0.04062939062714577, -0.19633737206459045, 1.7411118102828027e-09, 0.03983199596405029, -0.2006470263004303, 1.685064421330651e-09, 0.03854978084564209, -0.20447412133216858, 1.6095013100070332e-09, 0.03682109713554382, -0.20782533288002014, 1.516097580811504e-09, 0.03468427062034607, -0.21070733666419983, 1.406527450065198e-09, 0.03217759728431702, -0.2131272852420807, 1.2824660222676698e-09, 0.02933940291404724, -0.21509137749671936, 1.145587291695449e-09, 0.02620798349380493, -0.2166077196598053, 9.975679171603247e-10, 0.022821694612503052, -0.21768203377723694, 8.40080560671197e-10, 0.019218802452087402, -0.21832147240638733, 6.748016589952499e-10, 0.015437662601470947, -0.21853318810462952, 5.034052619201645e-10, 0.0115165701135993, -0.21840158104896545, 3.8853700812246927e-10, 0.00888869073241949, -0.21797481179237366, 2.6016497289838014e-10, 0.005951880943030119, -0.2172047197818756, 1.2276782368481065e-10, 0.0028086004313081503, -0.2160421907901764, -1.9179666535529272e-11, -0.00043877962161786854, -0.2144395411014557, -1.6119620915855393e-10, -0.003687739372253418, -0.21234813332557678, -2.988057024033708e-10, -0.006835877895355225, -0.20971933007240295, -4.275307885492907e-10, -0.00978076457977295, -0.20650449395179749, -5.428914540139829e-10, -0.012419908307492733, -0.20265641808509827, -6.404129448966955e-10, -0.014650939963757992, -0.19812551140785217, -7.156139014696805e-10, -0.016371337696909904, -0.1928636133670807, -7.64018348586859e-10, -0.0174787025898695, -0.1868230402469635, -7.811488678122203e-10, -0.017870603129267693, -0.16870275139808655, -7.81148812301069e-10, -0.017870601266622543, -0.10911527276039124, 9.095878494846943e-10, 0.02080894447863102, -0.10776010155677795, 9.399498956952357e-10, 0.021503547206521034, -0.10642305016517639, 9.675775736184278e-10, 0.022135594859719276, -0.10510268807411194, 9.92490423179504e-10, 0.02270553447306156, -0.10379806160926819, 1.0147066520360681e-09, 0.023213783279061317, -0.10250821709632874, 1.034243246600397e-09, 0.023660728707909584, -0.10123124718666077, 1.051118525552397e-09, 0.02404678799211979, -0.09996667504310608, 1.0653479209921102e-09, 0.024372318759560585, -0.09871307015419006, 1.0769510838670726e-09, 0.024637768045067787, -0.09746900200843811, 1.0859448895672585e-09, 0.024843523278832436, -0.09623351693153381, 1.0923476567725743e-09, 0.024990001693367958, -0.09500518441200256, 1.0961763718952966e-09, 0.025077592581510544, -0.09378305077552795, 1.0974477993030973e-09, 0.025106679648160934, -0.09124866127967834, 1.0926290983093168e-09, 0.02499644085764885, -0.08887973427772522, 1.0783606230191367e-09, 0.024670016020536423, -0.08668676018714905, 1.0549263684822563e-09, 0.024133902043104172, -0.0846797525882721, 1.0226050006778564e-09, 0.023394476622343063, -0.08287015557289124, 9.816807367002411e-10, 0.022458236664533615, -0.08126750588417053, 9.32436017286875e-10, 0.021331649273633957, -0.07988229393959045, 8.75152339485652e-10, 0.02002115175127983, -0.07872596383094788, 8.10111089322163e-10, 0.01853318139910698, -0.07780805230140686, 7.375949295784778e-10, 0.016874205321073532, -0.07713952660560608, 6.578866340589684e-10, 0.015050691552460194, -0.076730877161026, 5.712674222557723e-10, 0.013069075532257557, -0.07659211754798889, 4.780187912167833e-10, 0.010935795493423939, -0.07707181572914124, 3.333955611584116e-10, 0.0076272012665867805, -0.07839885354042053, 2.0532700539810378e-10, 0.004697334486991167, -0.08040347695350647, 9.174844217696432e-11, 0.0020989596378058195, -0.08291593194007874, -9.399782167907045e-12, -0.00021504194592125714, -0.08576741814613342, -1.0018371549014304e-10, -0.002291936194524169, -0.08878818154335022, -1.8266295420676926e-10, -0.004178841132670641, -0.09180942177772522, -2.5890090071811755e-10, -0.005922962445765734, -0.0946604311466217, -3.3096242413321875e-10, -0.007571537978947163, -0.09717336297035217, -4.0090705755169154e-10, -0.0091716842725873, -0.09917750954627991, -4.707982337315286e-10, -0.01077060867100954, -0.1005045473575592, -5.427008287206547e-10, -0.012415547855198383, -0.10098472237586975, -6.186743339853251e-10, -0.014153619296848774, -0.10091367363929749, -6.577058897505594e-10, -0.015046556480228901, -0.10070720314979553, -6.93565371800986e-10, -0.015866925939917564, -0.10037484765052795, -7.262501156013457e-10, -0.01661466620862484, -0.09992614388465881, -7.557615089304193e-10, -0.01728980801999569, -0.09937110543251038, -7.820994962770556e-10, -0.017892351374030113, -0.09871974587440491, -8.052654654200353e-10, -0.0184223260730505, -0.09798064827919006, -8.252566963129482e-10, -0.01887967251241207, -0.09716430306434631, -8.420758534910533e-10, -0.019264450296759605, -0.09628024697303772, -8.55720383441394e-10, -0.019576599821448326, -0.09533801674842834, -8.661926731434733e-10, -0.01981617882847786, -0.09434762597084045, -8.734917233965689e-10, -0.019983161240816116, -0.09331813454627991, -8.776160909107489e-10, -0.02007751539349556, -0.0922328531742096, -8.756008140764493e-10, -0.020031411200761795, -0.09106937050819397, -8.695302256001014e-10, -0.019892532378435135, -0.08983388543128967, -8.593704636794541e-10, -0.0196601040661335, -0.08853021264076233, -8.45083725220519e-10, -0.019333261996507645, -0.08716359734535217, -8.266374806886745e-10, -0.01891126111149788, -0.08573928475379944, -8.039952592575617e-10, -0.018393266946077347, -0.08426156640052795, -7.771231436137782e-10, -0.017778504639863968, -0.08273521065711975, -7.459833306633357e-10, -0.0170661099255085, -0.08116593956947327, -7.105420696262854e-10, -0.01625530794262886, -0.07955709099769592, -6.707640554104444e-10, -0.01534529309719801, -0.07791486382484436, -6.266142049682344e-10, -0.014335262589156628, -0.07624354958534241, -5.780560474732965e-10, -0.013224381022155285, -0.07624354958534241, -1.0654759297068495e-09, -0.024375248700380325, -0.07789340615272522, -1.101569946371228e-09, -0.0252009816467762, -0.07948127388954163, -1.1337843996983565e-09, -0.025937963277101517, -0.0810185968875885, -1.1622613982353869e-09, -0.026589442044496536, -0.08251586556434631, -1.1871430505294711e-09, -0.027158666402101517, -0.08398404717445374, -1.2085685785478972e-09, -0.02764882519841194, -0.08543410897254944, -1.2266799798155148e-09, -0.02806316688656807, -0.0868770182132721, -1.2416180306118463e-09, -0.02840491011738777, -0.08832374215126038, -1.2535233961941117e-09, -0.02867727354168892, -0.08978477120399475, -1.2625380740871606e-09, -0.02888350561261177, -0.09127107262611389, -1.2688028405705154e-09, -0.029026824980974197, -0.09279361367225647, -1.2724582498790937e-09, -0.02911045029759407, -0.09436383843421936, -1.2736449672701156e-09, -0.02913760021328926, -0.09677615761756897, -1.2681163896743897e-09, -0.02901112101972103, -0.09906545281410217, -1.2518547309881e-09, -0.02863909862935543, -0.10121503472328186, -1.225330503729083e-09, -0.028032293543219566, -0.10320869088172913, -1.1890228801547664e-09, -0.02720167301595211, -0.10502973198890686, -1.1434074798089e-09, -0.02615811489522457, -0.10666146874427795, -1.088958478945301e-09, -0.02491246722638607, -0.1080876886844635, -1.0261540506206757e-09, -0.02347566746175289, -0.10929170250892639, -9.554681490442363e-10, -0.021858563646674156, -0.11025729775428772, -8.773790582949914e-10, -0.02007209323346615, -0.11096683144569397, -7.923608991156073e-10, -0.01812710426747799, -0.11140504479408264, -7.008891245163795e-10, -0.016034474596381187, -0.11155477166175842, -6.034431843104926e-10, -0.013805171474814415, -0.11148801445960999, -5.465438657203947e-10, -0.012503465637564659, -0.11128249764442444, -4.922355301140158e-10, -0.01126103661954403, -0.11093059182167053, -4.3993861331692585e-10, -0.010064622387290001, -0.11042323708534241, -3.8906813881744995e-10, -0.008900841698050499, -0.10975328087806702, -3.3904445917443127e-10, -0.007756432984024286, -0.1089121401309967, -2.89286483656781e-10, -0.006618103012442589, -0.10789218544960022, -2.392093467751266e-10, -0.005472471937537193, -0.10668483376502991, -1.882333594549479e-10, -0.004306277260184288, -0.10528245568275452, -1.3577748647630727e-10, -0.0031062269117683172, -0.10367646813392639, -8.125814604520443e-11, -0.001858969684690237, -0.10185971856117249, -2.4094320288936544e-11, -0.0005512138013727963, -0.09982314705848694, 3.629499131796443e-11, 0.000830332632176578, -0.09764638543128967, 9.241014203853481e-11, 0.002114097587764263, -0.09569898247718811, 1.4418730098775256e-10, 0.0032986209262162447, -0.093973308801651, 1.9194561218238704e-10, 0.004391203634440899, -0.0924622118473053, 2.36001662656804e-10, 0.005399088840931654, -0.09115758538246155, 2.7667329538516583e-10, 0.006329547148197889, -0.0900513231754303, 3.1427704882958096e-10, 0.007189820986241102, -0.0891367495059967, 3.491295308410969e-10, 0.00798715278506279, -0.08840528130531311, 3.8154984727256647e-10, 0.008728843182325363, -0.08785024285316467, 4.118558827315155e-10, 0.009422164410352707, -0.08746257424354553, 4.4036288504578636e-10, 0.010074328631162643, -0.08723607659339905, 4.673887388229048e-10, 0.01069260761141777, -0.08716216683387756, 4.932512176480941e-10, 0.011284273117780685, -0.08721700310707092, 5.229450206201136e-10, 0.011963587254285812, -0.08737960457801819, 5.509817602167288e-10, 0.012604992836713791, -0.08764520287513733, 5.771842448432096e-10, 0.013204436749219894, -0.08800950646400452, 6.013780029512361e-10, 0.013757925480604172, -0.08846965432167053, 6.233858429460781e-10, 0.014261405915021896, -0.08902087807655334, 6.430305732330055e-10, 0.014710824936628342, -0.08965888619422913, 6.601376667525471e-10, 0.015102189034223557, -0.09037986397743225, 6.745285996423434e-10, 0.015431415289640427, -0.0911804735660553, 6.86028844842923e-10, 0.015694510191679, -0.09205594658851624, 6.94461210759556e-10, 0.015887420624494553, -0.09300199151039124, 6.996511703327712e-10, 0.01600615307688713, -0.09401527047157288, 7.014202552113602e-10, 0.01604662463068962, -0.09500661492347717, 6.999247292860389e-10, 0.016012411564588547, -0.09606137871742249, 6.953782549778964e-10, 0.01590839959681034, -0.09717527031898499, 6.876949010248268e-10, 0.015732625499367714, -0.09834304451942444, 6.767861271406161e-10, 0.015483061783015728, -0.09956136345863342, 6.625619497491186e-10, 0.015157650224864483, -0.1008249819278717, 6.449351053205987e-10, 0.014754395000636578, -0.10212960839271545, 6.238182748141696e-10, 0.014271298423409462, -0.10347095131874084, 5.991216411871392e-10, 0.013706305995583534, -0.10484471917152405, 5.707592731774014e-10, 0.013057449832558632, -0.10624662041664124, 5.386411872088104e-10, 0.012322673574090004, -0.10767140984535217, 5.026801197516306e-10, 0.011499980464577675, -0.10911527276039124, 4.6278750276407266e-10, 0.010587343946099281, -0.06462828069925308, 2.23476037675141e-09, 0.051125358790159225, -0.054290447384119034, 2.234760598796015e-09, 0.051125362515449524, -0.054290447384119034, 1.0060569044512135e-09, 0.02301589958369732, -0.053263816982507706, 1.0217207080387425e-09, 0.023374244570732117, -0.052271518856287, 1.0357456003973198e-09, 0.023695096373558044, -0.0513102151453495, 1.0481824297414732e-09, 0.02397961914539337, -0.05037561431527138, 1.0590860410886194e-09, 0.02422906458377838, -0.0494634248316288, 1.0685098361662426e-09, 0.02444465458393097, -0.04856983199715614, 1.076504441144266e-09, 0.024627551436424255, -0.04769054427742958, 1.0831248120624082e-09, 0.024779006838798523, -0.04682222381234169, 1.0884215750905923e-09, 0.024900183081626892, -0.04596010223031044, 1.092450796491562e-09, 0.024992361664772034, -0.045100364834070206, 1.0952621032345178e-09, 0.02505667507648468, -0.04423872008919716, 1.096911228515296e-09, 0.025094404816627502, -0.04337183013558388, 1.0974480213477023e-09, 0.025106683373451233, -0.039663467556238174, 1.0877754252902605e-09, 0.024885401129722595, -0.03616109862923622, 1.0594156663046306e-09, 0.024236604571342468, -0.032887134701013565, 1.0133560657266116e-09, 0.023182883858680725, -0.0298635084182024, 9.505828346689782e-10, 0.02174680121243, -0.027112634852528572, 8.720847377574614e-10, 0.019950972869992256, -0.024656446650624275, 7.788490963278605e-10, 0.017817990854382515, -0.022517355158925056, 6.718609002476228e-10, 0.015370385721325874, -0.02071729488670826, 5.521101353878066e-10, 0.012630807235836983, -0.019278675317764282, 4.2058292959445964e-10, 0.009621815755963326, -0.01822391152381897, 2.7826546622478077e-10, 0.006365972105413675, -0.017574459314346313, 1.2614649602671335e-10, 0.0028858953155577183, -0.017353206872940063, -3.478656598887575e-11, -0.0007958238711580634, -0.01755395531654358, -2.1185098120213297e-10, -0.00484658544883132, -0.018148094415664673, -3.7703346000839133e-10, -0.008625520393252373, -0.0191208403557539, -5.296630911644229e-10, -0.012117279693484306, -0.02045932225883007, -6.690716314317058e-10, -0.01530657522380352, -0.022149233147501945, -7.945868962799807e-10, -0.018178028985857964, -0.024177221581339836, -9.055418082049016e-10, -0.020716382190585136, -0.026529459282755852, -1.0012629614308821e-09, -0.0229062270373106, -0.029192117974162102, -1.0810833339647274e-09, -0.024732304736971855, -0.03215184435248375, -1.1443321845661103e-09, -0.026179268956184387, -0.0353948138654232, -1.1903397156842743e-09, -0.027231797575950623, -0.03890719637274742, -1.2184350195454385e-09, -0.027874544262886047, -0.04267468675971031, -1.227948631665754e-09, -0.028092190623283386, -0.06462827324867249, -1.2279487426880564e-09, -0.028092192485928535, -0.054290443658828735, -8.471523482711518e-10, -0.019380586221814156, -0.04383626580238342, -8.471522372488494e-10, -0.019380584359169006, -0.0410100519657135, -8.406114138104215e-10, -0.019230946898460388, -0.03850331902503967, -8.214838254083645e-10, -0.018793359398841858, -0.03630271553993225, -7.905094911997423e-10, -0.018084749579429626, -0.03439345955848694, -7.484270425628381e-10, -0.017122015357017517, -0.032761722803115845, -6.959803289241506e-10, -0.015922173857688904, -0.031393200159072876, -6.339065938831823e-10, -0.014502092264592648, -0.030274061486124992, -5.629471888646265e-10, -0.012878729961812496, -0.0293900053948164, -4.838445755162013e-10, -0.011069073341786861, -0.028727203607559204, -3.9733610845971157e-10, -0.009089990518987179, -0.028271347284317017, -3.0416430485402657e-10, -0.006958468351513147, -0.02800765633583069, -2.0506915610063459e-10, -0.004691435489803553, -0.027923256158828735, -1.0079184709077538e-10, -0.0023058487568050623, -0.02806153893470764, 1.5052122742664764e-11, 0.00034435244742780924, -0.02846875786781311, 1.23597063139691e-10, 0.002827571239322424, -0.029132038354873657, 2.2431408119860663e-10, 0.005131707992404699, -0.030039936304092407, 3.166742423843516e-10, 0.007244662381708622, -0.03118005394935608, 4.0015002422677526e-10, 0.00915436539798975, -0.032540470361709595, 4.742111703315288e-10, 0.010848687030375004, -0.03410878777503967, 5.383301027173104e-10, 0.012315557338297367, -0.03587356209754944, 5.919766343787103e-10, 0.013542846776545048, -0.03782191872596741, 6.346217995556458e-10, 0.014518454670906067, -0.0399419367313385, 6.657381312891175e-10, 0.015230312943458557, -0.042222172021865845, 6.847953315514133e-10, 0.015666291117668152, -0.044649749994277954, 6.912658223612311e-10, 0.015814319252967834, -0.04550471901893616, 6.907304173076056e-10, 0.01580207049846649, -0.046331554651260376, 6.891033854650175e-10, 0.01576484739780426, -0.04713597893714905, 6.863468682283269e-10, 0.015701785683631897, -0.04792323708534241, 6.824270037952829e-10, 0.015612110495567322, -0.048699527978897095, 6.77308653607156e-10, 0.015495016239583492, -0.049470096826553345, 6.709566791052168e-10, 0.01534970011562109, -0.05024018883705139, 6.633346094631065e-10, 0.015175326727330685, -0.05101647973060608, 6.544084718562715e-10, 0.014971121214330196, -0.05180373787879944, 6.441419064806553e-10, 0.01473624911159277, -0.05260816216468811, 6.325009960228556e-10, 0.014469935558736324, -0.05343499779701233, 6.194492141453622e-10, 0.014171346090734005, -0.054290443658828735, 6.049514778005971e-10, 0.013839676044881344, -0.0046922299079597, 1.0517533510778776e-09, 0.024061311036348343, 0.00564559968188405, 1.0517533510778776e-09, 0.024061311036348343, 0.0056456043384969234, -1.2279485206434515e-09, -0.028092186897993088, -0.0046922252513468266, -1.2279485206434515e-09, -0.028092186897993088, -0.005737457890063524, 1.7422642217823636e-09, 0.03985835984349251, -0.00568071473389864, 1.7784897998751603e-09, 0.04068710282444954, -0.005515729077160358, 1.8133227142058672e-09, 0.041483987122774124, -0.005249653942883015, 1.8464282325325598e-09, 0.042241353541612625, -0.004890118725597858, 1.8774701793233817e-09, 0.04295151308178902, -0.004445229656994343, 1.9061152656263403e-09, 0.04360683634877205, -0.003922616131603718, 1.9320274269318816e-09, 0.044199634343385696, -0.003329907776787877, 1.9548729301988033e-09, 0.04472227767109871, -0.0026747335214167833, 1.9743142676276193e-09, 0.045167047530412674, -0.001964246155694127, 1.9900197045785717e-09, 0.04552634432911873, -0.0012070287484675646, 2.001652843475199e-09, 0.04579247906804085, -0.0004102339153178036, 2.0088775087856447e-09, 0.045957762748003006, 0.00041850906563922763, 2.0113606336025214e-09, 0.04601456597447395, 0.001247251988388598, 2.0088775087856447e-09, 0.045957762748003006, 0.0020440469961613417, 2.0016515112075695e-09, 0.04579244926571846, 0.0028017412405461073, 1.9900197045785717e-09, 0.04552634432911873, 0.0035117517691105604, 1.9743142676276193e-09, 0.045167047530412674, 0.004166926257312298, 1.9548715979311737e-09, 0.04472224786877632, 0.004759634844958782, 1.9320274269318816e-09, 0.044199634343385696, 0.005282248370349407, 1.9061141554033156e-09, 0.04360680654644966, 0.005727137438952923, 1.8774701793233817e-09, 0.04295151308178902, 0.006086672656238079, 1.8464269002649303e-09, 0.04224132373929024, 0.006352747790515423, 1.8133213819382377e-09, 0.041483957320451736, 0.006517733447253704, 1.7784884676075308e-09, 0.04068707302212715, 0.006574954371899366, 1.7422642217823636e-09, 0.03985835984349251, 0.006517733912914991, 1.7060387547118694e-09, 0.03902961686253548, 0.00635274825617671, 1.671204508113533e-09, 0.038232702761888504, 0.006086673121899366, 1.6381003220544699e-09, 0.03747536614537239, 0.00572713790461421, 1.607056931973716e-09, 0.03676517680287361, 0.0052822488360106945, 1.578413177938387e-09, 0.03610988333821297, 0.0047596353106200695, 1.5524997953875186e-09, 0.03551705554127693, 0.004166926722973585, 1.5296556243882264e-09, 0.03499444201588631, 0.003511752700433135, 1.5102128436694784e-09, 0.034549642354249954, 0.0028012653347104788, 1.4945075177408285e-09, 0.0341903455555439, 0.0020440479274839163, 1.4828756000895282e-09, 0.03392424061894417, 0.0012472531525418162, 1.475649602511453e-09, 0.03375892713665962, 0.00041851014248095453, 1.4731679209845083e-09, 0.03370215371251106, -0.0004102328384760767, 1.47565082375678e-09, 0.03375895693898201, -0.0012070277007296681, 1.4828756000895282e-09, 0.03392424061894417, -0.0019642452243715525, 1.4945075177408285e-09, 0.0341903455555439, -0.0026747325900942087, 1.5102128436694784e-09, 0.034549642354249954, -0.0033299068454653025, 1.5296556243882264e-09, 0.03499444201588631, -0.0039226156659424305, 1.5524997953875186e-09, 0.03551705554127693, -0.0044452291913330555, 1.578413177938387e-09, 0.03610988333821297, -0.004890118259936571, 1.607056931973716e-09, 0.03676517680287361, -0.005249653477221727, 1.6381003220544699e-09, 0.03747536614537239, -0.005515728611499071, 1.6712058403811625e-09, 0.03823273256421089, -0.005680714268237352, 1.7060387547118694e-09, 0.03902961686253548, 0.020513387396931648, -1.227948409621149e-09, -0.02809218503534794, 0.02051338367164135, 1.0517533510778776e-09, 0.024061312898993492, 0.0308512132614851, 1.0517533510778776e-09, 0.024061312898993492, 0.030851216986775398, -5.780556588952379e-10, -0.013224371708929539, 0.031714290380477905, -6.280793662938322e-10, -0.014368780888617039, 0.03261885046958923, -6.740308311492527e-10, -0.015420028008520603, 0.033560603857040405, -7.158565962228636e-10, -0.016376890242099762, 0.03453812003135681, -7.535046475659612e-10, -0.017238177359104156, 0.035547107458114624, -7.8692152793991e-10, -0.018002666532993317, 0.03658613562583923, -8.160538356172253e-10, -0.018669135868549347, 0.03765186667442322, -8.408494456269011e-10, -0.01923639327287674, 0.038740962743759155, -8.612562885090824e-10, -0.019703246653079987, 0.03985103964805603, -8.77219574757504e-10, -0.020068444311618805, 0.04097971320152283, -8.886872349123109e-10, -0.020330794155597687, 0.04212316870689392, -8.956071995136483e-10, -0.020489104092121124, 0.0432794988155365, -8.979246790552509e-10, -0.020542122423648834, 0.04497846961021423, -8.941429263664702e-10, -0.020455606281757355, 0.04653152823448181, -8.829045272662484e-10, -0.020198501646518707, 0.04793867468833923, -8.643671334240821e-10, -0.019774414598941803, 0.049199432134628296, -8.386895622436441e-10, -0.01918698102235794, 0.050313323736190796, -8.060308531732119e-10, -0.01843983680009842, 0.05127987265586853, -7.665499346387605e-10, -0.017536617815494537, 0.0520990788936615, -7.204056240439627e-10, -0.016480959951877594, 0.052769988775253296, -6.67754351812988e-10, -0.015276438556611538, 0.05329260230064392, -6.087575998847683e-10, -0.013926750980317593, 0.05366644263267517, -5.435730754399515e-10, -0.012435502372682095, 0.05389103293418884, -4.723583191257319e-10, -0.010806298814713955, 0.05396589636802673, -3.952735916357142e-10, -0.00904280599206686, 0.053965892642736435, 1.0517535731224825e-09, 0.02406131662428379, 0.06430372595787048, 1.0517535731224825e-09, 0.02406131662428379, 0.06430372595787048, -3.6480990450726836e-10, -0.00834587775170803, 0.06415113806724548, -5.042822825984672e-10, -0.011536633595824242, 0.06370386481285095, -6.331063451270325e-10, -0.014483785256743431, 0.06297716498374939, -7.510008170896754e-10, -0.017180895432829857, 0.061984866857528687, -8.576828691708727e-10, -0.01962149702012539, 0.060742709785699844, -9.52869894099706e-10, -0.021799122914671898, 0.05926546826958656, -1.0362805058505842e-09, -0.02370733581483364, 0.05756792798638344, -1.1076334294202184e-09, -0.025339698418974876, 0.05566534772515297, -1.1666444477143045e-09, -0.026689713820815086, 0.05357203260064125, -1.2130336735083347e-09, -0.027750974521040916, 0.05130324140191078, -1.2465183329979368e-09, -0.028517015278339386, 0.04887423291802406, -1.2668157634010413e-09, -0.028981365263462067, 0.04629978910088539, -1.2736445231809057e-09, -0.029137589037418365, 0.0450042225420475, -1.2709296948187898e-09, -0.02907548099756241, 0.043679092079401016, -1.2629258749896621e-09, -0.02889237552881241, 0.04233393445611, -1.249844117090504e-09, -0.028593100607395172, 0.04097780957818031, -1.2318981390535555e-09, -0.02818254381418228, 0.039620254188776016, -1.2092962187182366e-09, -0.027665473520755768, 0.03827032819390297, -1.1822535173067195e-09, -0.0270468071103096, 0.036937568336725235, -1.1509782016361214e-09, -0.026331312954425812, 0.03563055768609047, -1.1156842116832877e-09, -0.025523878633975983, 0.03435930982232094, -1.0765822677782921e-09, -0.02462933212518692, 0.0331328846514225, -1.033883645362721e-09, -0.02365250140428543, 0.031960342079401016, -9.878006190788824e-10, -0.02259824424982071, 0.030851216986775398, -9.385430210784307e-10, -0.021471360698342323, 0.030851216986775398, -1.227948409621149e-09, -0.02809218503534794, 0.07882293313741684, 2.234761042885225e-09, 0.05112537369132042, 0.08916076272726059, 2.234761042885225e-09, 0.05112537369132042, 0.08916077017784119, -1.2279481875765441e-09, -0.02809217944741249, 0.07882294058799744, -1.2279481875765441e-09, -0.02809217944741249, 0.10007937997579575, 2.234761042885225e-09, 0.05112537369132042, 0.14235958456993103, 2.23476126492983e-09, 0.05112537741661072, 0.14235958456993103, -1.2279479655319392e-09, -0.028092173859477043, 0.13097652792930603, -1.2279479655319392e-09, -0.028092175722122192, 0.13097652792930603, 3.8155195669631325e-10, 0.008728891611099243, 0.10007938742637634, 3.815518456740108e-10, 0.00872888881713152, 0.10007938742637634, 8.28352220150208e-10, 0.018950490280985832, 0.13097652792930603, 8.283523311725105e-10, 0.01895049214363098, 0.13097652792930603, 1.787959558186003e-09, 0.04090374708175659, 0.10007938742637634, 1.7879594471637006e-09, 0.04090374335646629, 0.23458656668663025, 2.2347617090190397e-09, 0.05112538859248161, 0.23458656668663025, -1.2279476324650318e-09, -0.028092166408896446, 0.22320351004600525, -1.2279476324650318e-09, -0.028092168271541595, 0.22320351004600525, 2.6985094714326863e-10, 0.0061734700575470924, 0.2113555371761322, 2.69850919387693e-10, 0.006173469126224518, 0.2069748342037201, 2.7855814876964757e-10, 0.006372667383402586, 0.20300421118736267, 3.039581919495049e-10, 0.006953752599656582, 0.1994388997554779, 3.449789343079601e-10, 0.00789219792932272, 0.19627270102500916, 4.0054429217839527e-10, 0.0091633852571249, 0.1935003697872162, 4.695783206720705e-10, 0.010742699727416039, 0.19111570715904236, 5.510062406344218e-10, 0.01260555349290371, 0.18911346793174744, 6.437520516655582e-10, 0.014727329835295677, 0.18748793005943298, 7.467409468553399e-10, 0.017083441838622093, 0.18623337149620056, 8.588956768029732e-10, 0.019649242982268333, 0.18534454703330994, 9.791440991335776e-10, 0.022400205954909325, 0.18481525778770447, 1.1064075211564273e-09, 0.025311654433608055, 0.18463978171348572, 1.2396126347624659e-09, 0.028359031304717064, 0.1848052442073822, 1.3743847171454604e-09, 0.03144225850701332, 0.18530496954917908, 1.5037260325811985e-09, 0.034401241689920425, 0.18614467978477478, 1.626439205537622e-09, 0.037208590656518936, 0.18732866644859314, 1.741324306969716e-09, 0.039836857467889786, 0.1888631284236908, 1.8471830731670025e-09, 0.042258623987436295, 0.19075283408164978, 1.9428170183743987e-09, 0.04444647207856178, 0.19300302863121033, 2.0270276568368217e-09, 0.04637298732995987, 0.19561895728111267, 2.0986150595092568e-09, 0.04801071435213089, 0.19860586524009705, 2.1563806296143184e-09, 0.04933223873376846, 0.2019689977169037, 2.1991262144638313e-09, 0.05031014233827591, 0.20571407675743103, 2.225652995235805e-09, 0.05091700702905655, 0.2098453938961029, 2.2347614869744348e-09, 0.051125384867191315, 0.22320351004600525, 1.7879598912529104e-09, 0.04090375453233719, 0.2098453938961029, 1.7879598912529104e-09, 0.04090375453233719, 0.20740875601768494, 1.782418213025494e-09, 0.04077697545289993, 0.20525822043418884, 1.7664757434587841e-09, 0.04041225463151932, 0.20337900519371033, 1.741153887735436e-09, 0.039832957088947296, 0.2017577588558197, 1.7074751612611294e-09, 0.03906247764825821, 0.20038017630577087, 1.6664635227314761e-09, 0.038124240934848785, 0.19923195242881775, 1.6191402663068288e-09, 0.03704161196947098, 0.19829925894737244, 1.5665281294374722e-09, 0.03583798557519913, 0.19756779074668884, 1.509649627529086e-09, 0.034536756575107574, 0.19702324271202087, 1.44952727598735e-09, 0.03316131979227066, 0.19665178656578064, 1.3871839232848515e-09, 0.031735070049762726, 0.19643911719322205, 1.3236407525596405e-09, 0.030281370505690575, 0.1963714063167572, 1.259921722507329e-09, 0.028823649510741234, 0.19648393988609314, 1.1767051777411552e-09, 0.026919877156615257, 0.1968153417110443, 1.099798918602346e-09, 0.025160467252135277, 0.19735702872276306, 1.029381468953261e-09, 0.023549502715468407, 0.19810089468955994, 9.656272448310688e-10, 0.022090977057814598, 0.19903835654258728, 9.087136043639532e-10, 0.020788943395018578, 0.20016130805015564, 8.588162403455613e-10, 0.019647425040602684, 0.20146021246910095, 8.161123998817743e-10, 0.018670475110411644, 0.20292791724205017, 7.807767210543659e-10, 0.017862088978290558, 0.20455488562583923, 7.529875056810909e-10, 0.01722634583711624, 0.2063334882259369, 7.329193918437227e-10, 0.016767241060733795, 0.20825466513633728, 7.20748238869362e-10, 0.016488797962665558, 0.21031031012535095, 7.166525706203686e-10, 0.016395099461078644, 0.22320351004600525, 7.166525706203686e-10, 0.016395099461078644, 0.2515452802181244, 2.2347617090190397e-09, 0.05112538859248161, 0.2629283368587494, 2.2347617090190397e-09, 0.05112538859248161, 0.2629283368587494, -1.2279475214427293e-09, -0.028092164546251297, 0.2515452802181244, -1.2279475214427293e-09, -0.028092164546251297, 0.3086932599544525, 2.2347619310636446e-09, 0.05112539231777191, 0.3200763165950775, 2.2347619310636446e-09, 0.05112539604306221, 0.3200763165950775, -1.2279472993981244e-09, -0.02809215895831585, 0.27291759848594666, -1.2279474104204269e-09, -0.028092162683606148, 0.27291759848594666, -7.811470914553809e-10, -0.01787056215107441, 0.3086932599544525, -7.811469804330784e-10, -0.01787056028842926, 0.3320401608943939, 2.2347619310636446e-09, 0.05112539604306221, 0.3743208348751068, 2.2347621531082495e-09, 0.05112539976835251, 0.3743208348751068, -1.2279470773535195e-09, -0.0280921533703804, 0.3629377782344818, -1.2279470773535195e-09, -0.02809215523302555, 0.3629377782344818, 3.8155287263030857e-10, 0.008728912100195885, 0.3320401608943939, 3.815527338524305e-10, 0.00872890930622816, 0.3320401608943939, 8.283531083286277e-10, 0.018950510770082474, 0.3629377782344818, 8.283532193509302e-10, 0.018950512632727623, 0.3629377782344818, 1.7879605573867252e-09, 0.04090376943349838, 0.3320401608943939, 1.7879603353421203e-09, 0.040903765708208084});
    _triy = std::vector<int>({1, 47, 0, 1, 46, 47, 2, 46, 1, 2, 45, 46, 3, 45, 2, 3, 44, 45, 4, 44, 3, 4, 43, 44, 5, 43, 4, 5, 42, 43, 6, 42, 5, 6, 41, 42, 7, 48, 6, 48, 41, 6, 7, 95, 48, 49, 41, 48, 7, 94, 95, 50, 41, 49, 7, 93, 94, 51, 41, 50, 51, 40, 41, 8, 93, 7, 8, 92, 93, 52, 40, 51, 8, 91, 92, 53, 40, 52, 8, 90, 91, 54, 40, 53, 54, 39, 40, 9, 90, 8, 9, 89, 90, 55, 39, 54, 9, 88, 89, 56, 39, 55, 56, 38, 39, 10, 88, 9, 10, 87, 88, 57, 38, 56, 57, 37, 38, 11, 87, 10, 11, 86, 87, 58, 37, 57, 11, 85, 86, 59, 37, 58, 59, 36, 37, 12, 85, 11, 12, 84, 85, 60, 36, 59, 13, 84, 12, 13, 83, 84, 60, 35, 36, 61, 35, 60, 13, 82, 83, 62, 35, 61, 14, 82, 13, 62, 34, 35, 14, 81, 82, 63, 34, 62, 14, 80, 81, 15, 80, 14, 64, 34, 63, 64, 33, 34, 15, 79, 80, 65, 33, 64, 16, 79, 15, 65, 32, 33, 16, 78, 79, 66, 32, 65, 16, 77, 78, 67, 32, 66, 17, 77, 16, 67, 31, 32, 17, 76, 77, 68, 31, 67, 17, 75, 76, 69, 31, 68, 17, 74, 75, 70, 31, 69, 18, 74, 17, 70, 30, 31, 18, 73, 74, 71, 30, 70, 18, 72, 73, 72, 30, 71, 18, 30, 72, 19, 30, 18, 19, 29, 30, 20, 29, 19, 20, 28, 29, 21, 28, 20, 21, 27, 28, 22, 27, 21, 22, 26, 27, 23, 26, 22, 23, 25, 26, 24, 25, 23, 190, 188, 189, 166, 164, 165, 191, 188, 190, 191, 187, 188, 167, 164, 166, 167, 163, 164, 192, 187, 191, 192, 186, 187, 168, 163, 167, 193, 186, 192, 193, 185, 186, 168, 162, 163, 169, 162, 168, 194, 185, 193, 97, 202, 96, 97, 201, 202, 194, 184, 185, 170, 162, 169, 195, 184, 194, 170, 161, 162, 195, 183, 184, 196, 183, 195, 171, 161, 170, 196, 182, 183, 171, 160, 161, 197, 182, 196, 172, 160, 171, 197, 181, 182, 198, 181, 197, 173, 160, 172, 173, 159, 160, 198, 180, 181, 199, 180, 198, 174, 159, 173, 199, 179, 180, 200, 179, 199, 174, 158, 159, 175, 158, 174, 200, 178, 179, 201, 178, 200, 176, 158, 175, 176, 138, 158, 138, 157, 158, 97, 99, 201, 99, 100, 201, 100, 101, 201, 101, 102, 201, 102, 103, 201, 103, 104, 201, 104, 105, 201, 105, 106, 201, 106, 107, 201, 107, 108, 201, 108, 109, 201, 109, 110, 201, 110, 178, 201, 110, 111, 178, 111, 177, 178, 177, 137, 176, 137, 138, 176, 112, 177, 111, 139, 157, 138, 177, 136, 137, 113, 177, 112, 140, 157, 139, 177, 135, 136, 114, 177, 113, 141, 157, 140, 177, 134, 135, 115, 177, 114, 115, 134, 177, 142, 157, 141, 115, 133, 134, 142, 156, 157, 116, 133, 115, 116, 132, 133, 143, 156, 142, 116, 131, 132, 117, 131, 116, 144, 156, 143, 117, 130, 131, 118, 130, 117, 145, 156, 144, 118, 129, 130, 145, 155, 156, 119, 129, 118, 119, 128, 129, 146, 155, 145, 119, 127, 128, 120, 127, 119, 147, 155, 146, 120, 126, 127, 147, 154, 155, 121, 126, 120, 97, 98, 99, 121, 125, 126, 148, 154, 147, 122, 125, 121, 149, 154, 148, 149, 153, 154, 123, 125, 122, 150, 153, 149, 150, 152, 153, 124, 125, 123, 151, 152, 150, 241, 239, 240, 241, 238, 239, 242, 238, 241, 242, 237, 238, 243, 237, 242, 243, 236, 237, 244, 236, 243, 244, 235, 236, 245, 235, 244, 245, 234, 235, 246, 234, 245, 246, 233, 234, 247, 289, 246, 289, 233, 246, 247, 288, 289, 290, 233, 289, 247, 287, 288, 291, 233, 290, 247, 286, 287, 292, 233, 291, 292, 232, 233, 247, 285, 286, 248, 285, 247, 293, 232, 292, 248, 284, 285, 294, 232, 293, 248, 283, 284, 295, 232, 294, 248, 282, 283, 296, 232, 295, 249, 282, 248, 296, 231, 232, 249, 281, 282, 297, 231, 296, 249, 280, 281, 298, 231, 297, 250, 280, 249, 298, 230, 231, 250, 279, 280, 299, 230, 298, 250, 278, 279, 300, 230, 299, 251, 278, 250, 251, 277, 278, 300, 229, 230, 301, 229, 300, 251, 301, 277, 251, 229, 301, 252, 229, 251, 252, 228, 229, 253, 227, 252, 227, 228, 252, 253, 226, 227, 254, 226, 253, 254, 225, 226, 254, 224, 225, 255, 224, 254, 255, 223, 224, 256, 223, 255, 256, 222, 223, 204, 276, 203, 256, 221, 222, 205, 276, 204, 206, 276, 205, 257, 221, 256, 257, 220, 221, 207, 276, 206, 208, 276, 207, 257, 219, 220, 209, 276, 208, 257, 218, 219, 210, 276, 209, 258, 218, 257, 211, 276, 210, 258, 217, 218, 212, 276, 211, 258, 216, 217, 213, 276, 212, 214, 276, 213, 258, 215, 216, 215, 276, 214, 258, 276, 215, 259, 276, 258, 259, 275, 276, 260, 275, 259, 260, 274, 275, 260, 273, 274, 261, 273, 260, 261, 272, 273, 261, 271, 272, 262, 271, 261, 262, 270, 271, 262, 269, 270, 263, 269, 262, 263, 268, 269, 263, 267, 268, 263, 266, 267, 264, 266, 263, 264, 265, 266, 302, 329, 328, 329, 327, 328, 329, 326, 327, 329, 325, 326, 329, 324, 325, 329, 323, 324, 329, 322, 323, 329, 330, 322, 330, 331, 322, 331, 321, 322, 302, 355, 329, 332, 321, 331, 333, 321, 332, 334, 321, 333, 334, 320, 321, 335, 320, 334, 336, 320, 335, 336, 319, 320, 337, 319, 336, 337, 318, 319, 338, 318, 337, 339, 318, 338, 339, 317, 318, 340, 317, 339, 340, 316, 317, 341, 316, 340, 341, 315, 316, 342, 315, 341, 343, 315, 342, 343, 314, 315, 344, 314, 343, 344, 313, 314, 345, 313, 344, 346, 313, 345, 346, 312, 313, 347, 312, 346, 347, 311, 312, 348, 311, 347, 349, 311, 348, 349, 310, 311, 350, 310, 349, 350, 309, 310, 351, 309, 350, 352, 309, 351, 352, 308, 309, 353, 308, 352, 354, 308, 353, 302, 354, 355, 302, 308, 354, 302, 307, 308, 302, 306, 307, 302, 305, 306, 302, 304, 305, 302, 303, 304, 369, 367, 368, 369, 366, 367, 370, 366, 369, 370, 365, 366, 370, 364, 365, 371, 364, 370, 371, 363, 364, 371, 362, 363, 372, 362, 371, 372, 361, 362, 372, 360, 361, 373, 360, 372, 373, 359, 360, 373, 358, 359, 374, 358, 373, 374, 357, 358, 374, 356, 357, 375, 356, 374, 375, 481, 356, 481, 482, 356, 482, 483, 356, 483, 484, 356, 484, 485, 356, 485, 486, 356, 486, 487, 356, 487, 488, 356, 488, 489, 356, 376, 479, 375, 479, 480, 375, 480, 481, 375, 377, 478, 376, 478, 479, 376, 378, 476, 377, 476, 477, 377, 477, 478, 377, 378, 475, 476, 378, 474, 475, 378, 473, 474, 378, 472, 473, 378, 471, 472, 379, 471, 378, 379, 470, 471, 379, 469, 470, 379, 468, 469, 379, 467, 468, 380, 467, 379, 380, 466, 467, 380, 465, 466, 380, 464, 465, 381, 464, 380, 381, 463, 464, 381, 462, 463, 381, 461, 462, 381, 460, 461, 381, 459, 460, 382, 459, 381, 382, 458, 459, 382, 457, 458, 382, 456, 457, 383, 456, 382, 383, 455, 456, 383, 454, 455, 383, 453, 454, 384, 453, 383, 384, 452, 453, 385, 452, 384, 385, 451, 452, 385, 450, 451, 386, 450, 385, 386, 449, 450, 387, 449, 386, 387, 448, 449, 387, 447, 448, 388, 447, 387, 388, 446, 447, 389, 446, 388, 389, 445, 446, 389, 444, 445, 390, 444, 389, 390, 443, 444, 391, 443, 390, 391, 442, 443, 392, 442, 391, 392, 441, 442, 417, 415, 416, 392, 440, 441, 393, 440, 392, 417, 414, 415, 394, 440, 393, 417, 413, 414, 395, 440, 394, 395, 439, 440, 417, 412, 413, 396, 439, 395, 417, 411, 412, 397, 439, 396, 417, 410, 411, 398, 439, 397, 398, 438, 439, 417, 409, 410, 399, 438, 398, 400, 438, 399, 417, 408, 409, 401, 438, 400, 417, 407, 408, 402, 438, 401, 417, 406, 407, 403, 438, 402, 417, 405, 406, 404, 438, 403, 417, 404, 405, 404, 437, 438, 417, 437, 404, 417, 436, 437, 417, 435, 436, 418, 435, 417, 418, 434, 435, 419, 434, 418, 420, 434, 419, 420, 433, 434, 421, 433, 420, 422, 433, 421, 422, 432, 433, 423, 432, 422, 423, 431, 432, 424, 431, 423, 425, 431, 424, 425, 430, 431, 426, 430, 425, 427, 430, 426, 427, 429, 430, 428, 429, 427, 492, 490, 491, 492, 529, 490, 505, 503, 504, 505, 502, 503, 505, 501, 502, 505, 500, 501, 505, 499, 500, 506, 499, 505, 506, 498, 499, 506, 497, 498, 506, 496, 497, 507, 496, 506, 507, 495, 496, 507, 494, 495, 507, 493, 494, 507, 492, 493, 508, 492, 507, 508, 564, 492, 564, 565, 492, 565, 566, 492, 566, 567, 492, 567, 529, 492, 509, 561, 508, 561, 562, 508, 562, 563, 508, 563, 564, 508, 510, 558, 509, 558, 559, 509, 559, 560, 509, 560, 561, 509, 511, 555, 510, 555, 556, 510, 556, 557, 510, 557, 558, 510, 511, 554, 555, 511, 553, 554, 512, 553, 511, 512, 552, 553, 512, 551, 552, 530, 529, 567, 512, 550, 551, 513, 550, 512, 513, 549, 550, 513, 548, 549, 514, 548, 513, 514, 547, 548, 514, 546, 547, 515, 546, 514, 515, 545, 546, 516, 545, 515, 516, 544, 545, 516, 543, 544, 517, 543, 516, 517, 542, 543, 517, 541, 542, 518, 541, 517, 518, 540, 541, 519, 540, 518, 519, 539, 540, 519, 538, 539, 520, 538, 519, 520, 537, 538, 520, 536, 537, 521, 536, 520, 521, 535, 536, 521, 534, 535, 521, 533, 534, 522, 533, 521, 522, 532, 533, 522, 531, 532, 522, 530, 531, 522, 529, 530, 523, 529, 522, 524, 529, 523, 525, 529, 524, 526, 529, 525, 527, 529, 526, 528, 529, 527, 585, 583, 584, 585, 582, 583, 586, 582, 585, 586, 581, 582, 587, 581, 586, 587, 580, 581, 588, 580, 587, 588, 579, 580, 589, 579, 588, 589, 578, 579, 590, 578, 589, 590, 577, 578, 591, 577, 590, 591, 576, 577, 592, 576, 591, 592, 575, 576, 593, 575, 592, 593, 574, 575, 594, 574, 593, 594, 573, 574, 595, 573, 594, 595, 572, 573, 596, 572, 595, 597, 572, 596, 597, 619, 572, 597, 618, 619, 598, 618, 597, 598, 617, 618, 599, 617, 598, 599, 616, 617, 600, 616, 599, 600, 615, 616, 601, 615, 600, 601, 614, 615, 602, 614, 601, 602, 613, 614, 603, 613, 602, 603, 612, 613, 604, 612, 603, 604, 611, 612, 605, 611, 604, 605, 610, 611, 606, 610, 605, 606, 609, 610, 607, 609, 606, 607, 608, 609, 570, 568, 569, 570, 571, 568, 650, 648, 649, 650, 647, 648, 623, 621, 622, 623, 620, 621, 651, 647, 650, 651, 646, 647, 651, 645, 646, 652, 645, 651, 652, 644, 645, 624, 620, 623, 652, 643, 644, 625, 620, 624, 653, 643, 652, 653, 642, 643, 626, 620, 625, 627, 620, 626, 653, 641, 642, 654, 641, 653, 628, 620, 627, 654, 640, 641, 629, 674, 628, 674, 620, 628, 654, 639, 640, 630, 674, 629, 654, 638, 639, 631, 674, 630, 655, 638, 654, 632, 674, 631, 655, 637, 638, 633, 674, 632, 655, 636, 637, 634, 674, 633, 655, 635, 636, 635, 674, 634, 655, 674, 635, 655, 673, 674, 675, 620, 674, 656, 673, 655, 656, 672, 673, 656, 671, 672, 657, 671, 656, 657, 670, 671, 658, 670, 657, 658, 669, 670, 658, 668, 669, 659, 668, 658, 659, 667, 668, 659, 666, 667, 660, 666, 659, 660, 665, 666, 661, 665, 660, 661, 664, 665, 661, 663, 664, 662, 663, 661, 678, 676, 677, 678, 679, 676, 682, 688, 681, 688, 680, 681, 688, 689, 680, 682, 687, 688, 682, 684, 687, 684, 686, 687, 684, 685, 686, 682, 683, 684, 691, 719, 690, 719, 718, 690, 719, 717, 718, 719, 716, 717, 719, 715, 716, 719, 714, 715, 719, 713, 714, 719, 712, 713, 719, 711, 712, 719, 720, 711, 720, 710, 711, 691, 745, 719, 721, 710, 720, 722, 710, 721, 723, 710, 722, 723, 709, 710, 724, 709, 723, 725, 709, 724, 726, 709, 725, 726, 708, 709, 727, 708, 726, 728, 708, 727, 729, 708, 728, 729, 707, 708, 730, 707, 729, 731, 707, 730, 731, 706, 707, 732, 706, 731, 733, 706, 732, 733, 705, 706, 734, 705, 733, 734, 704, 705, 735, 704, 734, 736, 704, 735, 736, 703, 704, 737, 703, 736, 738, 703, 737, 738, 702, 703, 739, 702, 738, 740, 702, 739, 741, 702, 740, 742, 702, 741, 742, 701, 702, 743, 701, 742, 744, 701, 743, 691, 693, 745, 693, 744, 745, 693, 701, 744, 693, 700, 701, 693, 699, 700, 693, 698, 699, 693, 697, 698, 693, 696, 697, 693, 695, 696, 693, 694, 695, 691, 692, 693, 748, 746, 747, 748, 749, 746, 752, 750, 751, 752, 755, 750, 752, 754, 755, 752, 753, 754, 758, 764, 757, 764, 756, 757, 764, 765, 756, 758, 763, 764, 758, 760, 763, 760, 762, 763, 760, 761, 762, 758, 759, 760});

    _vertz = std::vector<float>({-0.4125114977359772, -0.025106651708483696, 0.0, -0.4087001383304596, -0.02486945502460003, 0.0, -0.4050680696964264, -0.024176878854632378, 0.0, -0.40164390206336975, -0.023057622835040092, 0.0, -0.39845672249794006, -0.021540267392992973, 0.0, -0.3955360949039459, -0.01965351216495037, 0.0, -0.3929106295108795, -0.017425939440727234, 0.0, -0.39060941338539124, -0.014886184595525265, 0.0, -0.38866105675697327, -0.0120629221200943, 0.0, -0.3870956003665924, -0.008984759449958801, 0.0, -0.38594117760658264, -0.005680307745933533, 0.0, -0.38522735238075256, -0.0021782666444778442, 0.0, -0.38498273491859436, 0.0014927833108231425, 0.0, -0.3852182924747467, 0.0054040104150772095, 0.0, -0.38590875267982483, 0.009106293320655823, 0.0, -0.3870302736759186, 0.012574687600135803, 0.0, -0.3885580599308014, 0.0157841295003891, 0.0, -0.3904682695865631, 0.018709644675254822, 0.0, -0.3927361071109772, 0.021326199173927307, 0.0, -0.39533868432044983, 0.023608850315213203, 0.0, -0.3982502520084381, 0.02553253062069416, 0.0, -0.40144792199134827, 0.02707223780453205, 0.0, -0.40490689873695374, 0.028202997520565987, 0.0, -0.40860286355018616, 0.02889980562031269, 0.0, -0.4125114977359772, 0.0291376281529665, 0.0, -0.41658082604408264, 0.028908688575029373, 0.0, -0.42041030526161194, 0.02823527529835701, 0.0, -0.4239784777164459, 0.027137596160173416, 0.0, -0.42726340889930725, 0.025635767728090286, 0.0, -0.4302436411380768, 0.023749995976686478, 0.0, -0.43289676308631897, 0.02150045707821846, 0.0, -0.4352017939090729, 0.018907267600297928, 0.0, -0.43713632225990295, 0.015990635380148888, 0.0, -0.43867936730384827, 0.012770702131092548, 0.0, -0.43980804085731506, 0.00926761794835329, 0.0, -0.4405013620853424, 0.005501618143171072, 0.0, -0.44073739647865295, 0.0014927882002666593, 0.0, -0.44049468636512756, -0.0022758645936846733, 0.0, -0.4397837221622467, -0.005841622594743967, 0.0, -0.43863025307655334, -0.009180734865367413, 0.0, -0.43705907464027405, -0.012269417755305767, 0.0, -0.4350959360599518, -0.015083800069987774, 0.0, -0.4327661097049713, -0.017600160092115402, 0.0, -0.4300953447818756, -0.019794654101133347, 0.0, -0.42710843682289124, -0.02164353057742119, 0.0, -0.42383113503456116, -0.02312294766306877, 0.0, -0.42028918862342834, -0.024209152907133102, 0.0, -0.41650739312171936, -0.024878334254026413, 0.0, -0.4123956263065338, -0.015814287588000298, 0.0, -0.41491666436195374, -0.015664441511034966, 0.0, -0.41730132699012756, -0.015225422568619251, 0.0, -0.4195334017276764, -0.014512968249619007, 0.0, -0.4215976297855377, -0.013542812317609787, 0.0, -0.42347779870033264, -0.012330632656812668, 0.0, -0.42515817284584045, -0.010892223566770554, 0.0, -0.42662301659584045, -0.009243261069059372, 0.0, -0.42785707116127014, -0.007399510592222214, 0.0, -0.4288441240787506, -0.005376677494496107, 0.0, -0.42956891655921936, -0.003190498799085617, 0.0, -0.4300152361392975, -0.0008567384211346507, 0.0, -0.4301673471927643, 0.0016089269192889333, 0.0, -0.43002620339393616, 0.004334617871791124, 0.0, -0.4296089708805084, 0.006871927995234728, 0.0, -0.42892566323280334, 0.009211648255586624, 0.0, -0.4279862940311432, 0.011344421654939651, 0.0, -0.4267994463443756, 0.013261038810014725, 0.0, -0.4253756105899811, 0.01495223119854927, 0.0, -0.42372480034828186, 0.01640867069363594, 0.0, -0.4218555986881256, 0.01762108877301216, 0.0, -0.4197784960269928, 0.018580246716737747, 0.0, -0.4175030291080475, 0.019276846200227737, 0.0, -0.41503873467445374, 0.019701587036252022, 0.0, -0.4123956263065338, 0.019845234230160713, 0.0, -0.4099656641483307, 0.01969488151371479, 0.0, -0.4076792299747467, 0.0192521084100008, 0.0, -0.40554967522621155, 0.018529431894421577, 0.0, -0.4035893976688385, 0.017539339140057564, 0.0, -0.40181127190589905, 0.01629437692463398, 0.0, -0.4002281725406647, 0.01480703242123127, 0.0, -0.39885345101356506, 0.013089791871607304, 0.0, -0.3976999819278717, 0.011155144311487675, 0.0, -0.3967796862125397, 0.00901560578495264, 0.0, -0.39610686898231506, 0.006683723069727421, 0.0, -0.39569345116615295, 0.0041719237342476845, 0.0, -0.39555326104164124, 0.0014927842421457171, 0.0, -0.395698219537735, -0.0009462080197408795, 0.0, -0.39612308144569397, -0.0032577356323599815, 0.0, -0.3968125879764557, -0.005425675772130489, 0.0, -0.39775148034095764, -0.007433934602886438, 0.0, -0.3989240229129791, -0.009266330860555172, 0.0, -0.40031543374061584, -0.01090673916041851, 0.0, -0.4019099771976471, -0.012339038774371147, 0.0, -0.4036923944950104, -0.013547105714678764, 0.0, -0.4056479036808014, -0.014514787122607231, 0.0, -0.40776029229164124, -0.015225989744067192, 0.0, -0.4100143015384674, -0.01566450111567974, 0.0, -0.29809918999671936, -0.024061284959316254, 0.0, -0.29809918999671936, 0.028092212975025177, 0.0, -0.3084370195865631, 0.028092212975025177, 0.0, -0.3084370195865631, -0.009774229489266872, 0.0, -0.30949607491493225, -0.01095371600240469, 0.0, -0.3105298578739166, -0.011998913250863552, 0.0, -0.3115479052066803, -0.012915871106088161, 0.0, -0.3125583231449127, -0.013710579834878445, 0.0, -0.31357064843177795, -0.014389178715646267, 0.0, -0.31459298729896545, -0.01495765708386898, 0.0, -0.3156353533267975, -0.015422066673636436, 0.0, -0.3167053759098053, -0.01578848622739315, 0.0, -0.31781306862831116, -0.016062935814261436, 0.0, -0.3189660608768463, -0.016251495108008385, 0.0, -0.32017436623573303, -0.01636018417775631, 0.0, -0.32144656777381897, -0.016395052894949913, 0.0, -0.322704941034317, -0.01631929539144039, 0.0, -0.32391801476478577, -0.016089072450995445, 0.0, -0.32507243752479553, -0.015699943527579308, 0.0, -0.32615724205970764, -0.015147467143833637, 0.0, -0.3271590769290924, -0.014427204616367817, 0.0, -0.32806697487831116, -0.013534744270145893, 0.0, -0.3288685381412506, -0.012465615756809711, 0.0, -0.3295513689517975, -0.011215408332645893, 0.0, -0.3301035463809967, -0.009779681451618671, 0.0, -0.330512672662735, -0.00815399456769228, 0.0, -0.33076730370521545, -0.006333877332508564, 0.0, -0.33085504174232483, -0.004314948804676533, 0.0, -0.33085504174232483, 0.028092216700315475, 0.0, -0.3411923944950104, 0.028092216700315475, 0.0, -0.3411923944950104, -0.009774226695299149, 0.0, -0.34213748574256897, -0.010711926966905594, 0.0, -0.34310975670814514, -0.011603672057390213, 0.0, -0.34410205483436584, -0.01244216039776802, 0.0, -0.34510722756385803, -0.013220150023698807, 0.0, -0.34611955285072327, -0.013930398970842361, 0.0, -0.3471309244632721, -0.014565604738891125, 0.0, -0.3481351435184479, -0.015118557028472424, 0.0, -0.34912553429603577, -0.015581953339278698, 0.0, -0.3500949442386627, -0.0159485824406147, 0.0, -0.3510362207889557, -0.016211140900850296, 0.0, -0.35194268822669983, -0.0163623858243227, 0.0, -0.3528081476688385, -0.016395049169659615, 0.0, -0.35426488518714905, -0.016305910423398018, 0.0, -0.3556653559207916, -0.01604013331234455, 0.0, -0.35699525475502014, -0.015600131824612617, 0.0, -0.3582417070865631, -0.014988290145993233, 0.0, -0.35939136147499084, -0.014207081869244576, 0.0, -0.36043086647987366, -0.013258861377835274, 0.0, -0.36134687066078186, -0.012146132066845894, 0.0, -0.36212649941444397, -0.010871248319745064, 0.0, -0.3627559244632721, -0.009436653926968575, 0.0, -0.36322179436683655, -0.00784476287662983, 0.0, -0.36351123452186584, -0.0060980189591646194, 0.0, -0.3636104166507721, -0.00419880636036396, 0.0, -0.3636104166507721, 0.028092218562960625, 0.0, -0.37394824624061584, 0.028092220425605774, 0.0, -0.37394824624061584, -0.004663423635065556, 0.0, -0.37380948662757874, -0.007652119733393192, 0.0, -0.37340036034584045, -0.010452882386744022, 0.0, -0.37273040413856506, -0.013051972724497318, 0.0, -0.37181010842323303, -0.015435711480677128, 0.0, -0.3706494867801666, -0.01759033091366291, 0.0, -0.3692585527896881, -0.019502179697155952, 0.0, -0.36764732003211975, -0.0211575198918581, 0.0, -0.3658258020877838, -0.022542642429471016, 0.0, -0.36380448937416077, -0.023643838241696358, 0.0, -0.3615933954715729, -0.0244473684579134, 0.0, -0.3592020571231842, -0.024939553812146187, 0.0, -0.3566414415836334, -0.025106655433773994, 0.0, -0.3548232614994049, -0.02501915581524372, 0.0, -0.3530837595462799, -0.024764643982052803, 0.0, -0.351419597864151, -0.02435528114438057, 0.0, -0.34982696175575256, -0.023803163319826126, 0.0, -0.34830155968666077, -0.02312033250927925, 0.0, -0.3468405306339264, -0.022318948060274124, 0.0, -0.3454400599002838, -0.021411079913377762, 0.0, -0.3440963327884674, -0.020408857613801956, 0.0, -0.34280601143836975, -0.019324321299791336, 0.0, -0.3415652811527252, -0.01816963031888008, 0.0, -0.3403708040714264, -0.016956884413957596, 0.0, -0.33921781182289124, -0.01569812372326851, 0.0, -0.33830609917640686, -0.017176467925310135, 0.0, -0.33731475472450256, -0.01853262260556221, 0.0, -0.33624711632728577, -0.01976536586880684, 0.0, -0.3351050913333893, -0.020873475819826126, 0.0, -0.33389249444007874, -0.021855730563402176, 0.0, -0.33261170983314514, -0.02271096780896187, 0.0, -0.3312655985355377, -0.02343793585896492, 0.0, -0.3298570215702057, -0.024035444483160973, 0.0, -0.32838836312294006, -0.02450229786336422, 0.0, -0.32686296105384827, -0.024837246164679527, 0.0, -0.3252836763858795, -0.025039127096533775, 0.0, -0.32365337014198303, -0.025106659159064293, 0.0, -0.3224312365055084, -0.02505328319966793, 0.0, -0.3212033808231354, -0.024892648681998253, 0.0, -0.3199688494205475, -0.024623891338706017, 0.0, -0.31872764229774475, -0.02424626611173153, 0.0, -0.31747785210609436, -0.023758908733725548, 0.0, -0.3162194788455963, -0.02316107414662838, 0.0, -0.314951092004776, -0.022451898083090782, 0.0, -0.3136726915836334, -0.021630635485053062, 0.0, -0.31238284707069397, -0.020696422085165977, 0.0, -0.31108060479164124, -0.01964845322072506, 0.0, -0.309765487909317, -0.018485983833670616, 0.0, -0.3084370195865631, -0.017208151519298553, 0.0, -0.3084370195865631, -0.024061284959316254, 0.0, -0.28648391366004944, 0.012992090545594692, 0.0, -0.28497567772865295, 0.0139451390132308, 0.0, -0.2834712564945221, 0.014827973209321499, 0.0, -0.28196826577186584, 0.015638237819075584, 0.0, -0.2804652750492096, 0.016373490914702415, 0.0, -0.27896037697792053, 0.017031287774443626, 0.0, -0.27745261788368225, 0.0176092442125082, 0.0, -0.27594009041786194, 0.01810491643846035, 0.0, -0.2744208872318268, 0.01851589046418667, 0.0, -0.2728935778141022, 0.018839752301573753, 0.0, -0.2713567316532135, 0.0190740879625082, 0.0, -0.26980844140052795, 0.019216453656554222, 0.0, -0.2682472765445709, 0.0192644651979208, 0.0, -0.2658349573612213, 0.019153330475091934, 0.0, -0.2635928690433502, 0.01882079616189003, 0.0, -0.26152148842811584, 0.018268052488565445, 0.0, -0.2596217691898346, 0.017496321350336075, 0.0, -0.2578951418399811, 0.016506794840097427, 0.0, -0.2563416063785553, 0.01530066505074501, 0.0, -0.25496259331703186, 0.013879183679819107, 0.0, -0.25375810265541077, 0.012243542820215225, 0.0, -0.25273004174232483, 0.010394934564828873, 0.0, -0.25187841057777405, 0.008334610611200333, 0.0, -0.25120416283607483, 0.006063732784241438, 0.0, -0.2507082521915436, 0.0035835534799844027, 0.0, -0.2874127924442291, 0.003583556739613414, 0.0, -0.28723111748695374, -0.0010314520914107561, 0.0, -0.2866951525211334, -0.005236678756773472, 0.0, -0.2858177721500397, -0.009033762849867344, 0.0, -0.2846123278141022, -0.012424283660948277, 0.0, -0.2830926477909088, -0.01540991012006998, 0.0, -0.2812711298465729, -0.01799219287931919, 0.0, -0.27916207909584045, -0.02017276920378208, 0.0, -0.27677837014198303, -0.02195327915251255, 0.0, -0.2741333544254303, -0.023335302248597145, 0.0, -0.27123990654945374, -0.02432047761976719, 0.0, -0.26811185479164124, -0.02491038478910923, 0.0, -0.2647625505924225, -0.02510666474699974, 0.0, -0.2612573206424713, -0.024887260049581528, 0.0, -0.25795474648475647, -0.02424195036292076, 0.0, -0.2548753321170807, -0.023190107196569443, 0.0, -0.2520371973514557, -0.021751102060079575, 0.0, -0.2494608461856842, -0.019944246858358383, 0.0, -0.24716535210609436, -0.01778891310095787, 0.0, -0.24516978859901428, -0.015304503031075, 0.0, -0.2434937059879303, -0.012510326690971851, 0.0, -0.24215617775917053, -0.009425786323845387, 0.0, -0.2411767542362213, -0.00607019430026412, 0.0, -0.24057498574256897, -0.002462951233610511, 0.0, -0.24037042260169983, 0.0013766310876235366, 0.0, -0.24055781960487366, 0.004948499146848917, 0.0, -0.24111667275428772, 0.008434089832007885, 0.0, -0.24203982949256897, 0.011790606193244457, 0.0, -0.24332156777381897, 0.014975341968238354, 0.0, -0.24495473504066467, 0.01794547028839588, 0.0, -0.24693313241004944, 0.02065831795334816, 0.0, -0.24925008416175842, 0.023071084171533585, 0.0, -0.2518998682498932, 0.02514103427529335, 0.0, -0.2548748552799225, 0.026825401932001114, 0.0, -0.2581698000431061, 0.02808145061135292, 0.0, -0.2617775499820709, 0.028866443783044815, 0.0, -0.2656919062137604, 0.029137615114450455, 0.0, -0.2678357660770416, 0.029096340760588646, 0.0, -0.2698618471622467, 0.028971975669264793, 0.0, -0.2717830240726471, 0.028763746842741966, 0.0, -0.2736121714115143, 0.02847079001367092, 0.0, -0.27536216378211975, 0.028092360123991966, 0.0, -0.2770463526248932, 0.027627592906355858, 0.0, -0.2786771357059479, 0.027075713500380516, 0.0, -0.2802673876285553, 0.02643594704568386, 0.0, -0.28183045983314514, 0.02570742927491665, 0.0, -0.2833787500858307, 0.024889355525374413, 0.0, -0.2849256098270416, 0.02398095093667507, 0.0, -0.28648391366004944, 0.02298141084611416, 0.0, -0.2509404718875885, -0.0032695799600332975, 0.0, -0.25135865807533264, -0.005255695898085833, 0.0, -0.2519170343875885, -0.007088151294738054, 0.0, -0.25261369347572327, -0.00876333937048912, 0.0, -0.25344863533973694, -0.010277565568685532, 0.0, -0.2544204294681549, -0.011627282947301865, 0.0, -0.25552859902381897, -0.012808796018362045, 0.0, -0.2567721903324127, -0.013818498700857162, 0.0, -0.25815072655677795, -0.014652755111455917, 0.0, -0.25966277718544006, -0.015307929366827011, 0.0, -0.26130834221839905, -0.015780415385961533, 0.0, -0.2630859911441803, -0.016066577285528183, 0.0, -0.2649952471256256, -0.016162749379873276, 0.0, -0.2667657434940338, -0.01605989970266819, 0.0, -0.2684151232242584, -0.015756214037537575, 0.0, -0.2699390947818756, -0.015258933417499065, 0.0, -0.27133193612098694, -0.014575297944247723, 0.0, -0.2725893557071686, -0.013712609186768532, 0.0, -0.2737065851688385, -0.012678110972046852, 0.0, -0.2746788561344147, -0.011479044333100319, 0.0, -0.27550092339515686, -0.010122710838913918, 0.0, -0.27616754174232483, -0.00861632265150547, 0.0, -0.27667489647865295, -0.006967151537537575, 0.0, -0.277017742395401, -0.005182499065995216, 0.0, -0.27719131112098694, -0.003269577631726861, 0.0, -0.15731969475746155, 0.028092199936509132, 0.0, -0.18821683526039124, 0.02809220366179943, 0.0, -0.19453445076942444, 0.02770104818046093, 0.0, -0.20040622353553772, 0.02656984142959118, 0.0, -0.20581260323524475, 0.024761825799942017, 0.0, -0.210733562707901, 0.022340387105941772, 0.0, -0.21515002846717834, 0.01936882734298706, 0.0, -0.21904149651527405, 0.015910476446151733, 0.0, -0.22238841652870178, 0.01202863547950983, 0.0, -0.22517123818397522, 0.007786632515490055, 0.0, -0.22736993432044983, 0.0032477984204888344, 0.0, -0.22896495461463928, -0.0015245664399117231, 0.0, -0.22993674874305725, -0.006467102561146021, 0.0, -0.230264812707901, -0.011516569182276726, 0.0, -0.22999444603919983, -0.01622438244521618, 0.0, -0.22917428612709045, -0.020943908020853996, 0.0, -0.227792888879776, -0.025594888255000114, 0.0, -0.2258378565311432, -0.030097035691142082, 0.0, -0.22329774498939514, -0.034370094537734985, 0.0, -0.22015920281410217, -0.03833380341529846, 0.0, -0.2164112627506256, -0.0419079065322876, 0.0, -0.21204152703285217, -0.04501217603683472, 0.0, -0.20703759789466858, -0.04756629467010498, 0.0, -0.20138755440711975, -0.04949003458023071, 0.0, -0.1950789988040924, -0.05070313811302185, 0.0, -0.18810048699378967, -0.05112535133957863, 0.0, -0.15731969475746155, -0.05112535133957863, 0.0, -0.16870275139808655, -0.0409037210047245, 0.0, -0.1862422525882721, -0.0409037210047245, 0.0, -0.191538006067276, -0.04062939062714577, 0.0, -0.19633737206459045, -0.03983199596405029, 0.0, -0.2006470263004303, -0.03854978084564209, 0.0, -0.20447412133216858, -0.03682109713554382, 0.0, -0.20782533288002014, -0.03468427062034607, 0.0, -0.21070733666419983, -0.03217759728431702, 0.0, -0.2131272852420807, -0.02933940291404724, 0.0, -0.21509137749671936, -0.02620798349380493, 0.0, -0.2166077196598053, -0.022821694612503052, 0.0, -0.21768203377723694, -0.019218802452087402, 0.0, -0.21832147240638733, -0.015437662601470947, 0.0, -0.21853318810462952, -0.0115165701135993, 0.0, -0.21840158104896545, -0.00888869073241949, 0.0, -0.21797481179237366, -0.005951880943030119, 0.0, -0.2172047197818756, -0.0028086004313081503, 0.0, -0.2160421907901764, 0.00043877962161786854, 0.0, -0.2144395411014557, 0.003687739372253418, 0.0, -0.21234813332557678, 0.006835877895355225, 0.0, -0.20971933007240295, 0.00978076457977295, 0.0, -0.20650449395179749, 0.012419908307492733, 0.0, -0.20265641808509827, 0.014650939963757992, 0.0, -0.19812551140785217, 0.016371337696909904, 0.0, -0.1928636133670807, 0.0174787025898695, 0.0, -0.1868230402469635, 0.017870603129267693, 0.0, -0.16870275139808655, 0.017870601266622543, 0.0, -0.10911527276039124, -0.02080894447863102, 0.0, -0.10776010155677795, -0.021503547206521034, 0.0, -0.10642305016517639, -0.022135594859719276, 0.0, -0.10510268807411194, -0.02270553447306156, 0.0, -0.10379806160926819, -0.023213783279061317, 0.0, -0.10250821709632874, -0.023660728707909584, 0.0, -0.10123124718666077, -0.02404678799211979, 0.0, -0.09996667504310608, -0.024372318759560585, 0.0, -0.09871307015419006, -0.024637768045067787, 0.0, -0.09746900200843811, -0.024843523278832436, 0.0, -0.09623351693153381, -0.024990001693367958, 0.0, -0.09500518441200256, -0.025077592581510544, 0.0, -0.09378305077552795, -0.025106679648160934, 0.0, -0.09124866127967834, -0.02499644085764885, 0.0, -0.08887973427772522, -0.024670016020536423, 0.0, -0.08668676018714905, -0.024133902043104172, 0.0, -0.0846797525882721, -0.023394476622343063, 0.0, -0.08287015557289124, -0.022458236664533615, 0.0, -0.08126750588417053, -0.021331649273633957, 0.0, -0.07988229393959045, -0.02002115175127983, 0.0, -0.07872596383094788, -0.01853318139910698, 0.0, -0.07780805230140686, -0.016874205321073532, 0.0, -0.07713952660560608, -0.015050691552460194, 0.0, -0.076730877161026, -0.013069075532257557, 0.0, -0.07659211754798889, -0.010935795493423939, 0.0, -0.07707181572914124, -0.0076272012665867805, 0.0, -0.07839885354042053, -0.004697334486991167, 0.0, -0.08040347695350647, -0.0020989596378058195, 0.0, -0.08291593194007874, 0.00021504194592125714, 0.0, -0.08576741814613342, 0.002291936194524169, 0.0, -0.08878818154335022, 0.004178841132670641, 0.0, -0.09180942177772522, 0.005922962445765734, 0.0, -0.0946604311466217, 0.007571537978947163, 0.0, -0.09717336297035217, 0.0091716842725873, 0.0, -0.09917750954627991, 0.01077060867100954, 0.0, -0.1005045473575592, 0.012415547855198383, 0.0, -0.10098472237586975, 0.014153619296848774, 0.0, -0.10091367363929749, 0.015046556480228901, 0.0, -0.10070720314979553, 0.015866925939917564, 0.0, -0.10037484765052795, 0.01661466620862484, 0.0, -0.09992614388465881, 0.01728980801999569, 0.0, -0.09937110543251038, 0.017892351374030113, 0.0, -0.09871974587440491, 0.0184223260730505, 0.0, -0.09798064827919006, 0.01887967251241207, 0.0, -0.09716430306434631, 0.019264450296759605, 0.0, -0.09628024697303772, 0.019576599821448326, 0.0, -0.09533801674842834, 0.01981617882847786, 0.0, -0.09434762597084045, 0.019983161240816116, 0.0, -0.09331813454627991, 0.02007751539349556, 0.0, -0.0922328531742096, 0.020031411200761795, 0.0, -0.09106937050819397, 0.019892532378435135, 0.0, -0.08983388543128967, 0.0196601040661335, 0.0, -0.08853021264076233, 0.019333261996507645, 0.0, -0.08716359734535217, 0.01891126111149788, 0.0, -0.08573928475379944, 0.018393266946077347, 0.0, -0.08426156640052795, 0.017778504639863968, 0.0, -0.08273521065711975, 0.0170661099255085, 0.0, -0.08116593956947327, 0.01625530794262886, 0.0, -0.07955709099769592, 0.01534529309719801, 0.0, -0.07791486382484436, 0.014335262589156628, 0.0, -0.07624354958534241, 0.013224381022155285, 0.0, -0.07624354958534241, 0.024375248700380325, 0.0, -0.07789340615272522, 0.0252009816467762, 0.0, -0.07948127388954163, 0.025937963277101517, 0.0, -0.0810185968875885, 0.026589442044496536, 0.0, -0.08251586556434631, 0.027158666402101517, 0.0, -0.08398404717445374, 0.02764882519841194, 0.0, -0.08543410897254944, 0.02806316688656807, 0.0, -0.0868770182132721, 0.02840491011738777, 0.0, -0.08832374215126038, 0.02867727354168892, 0.0, -0.08978477120399475, 0.02888350561261177, 0.0, -0.09127107262611389, 0.029026824980974197, 0.0, -0.09279361367225647, 0.02911045029759407, 0.0, -0.09436383843421936, 0.02913760021328926, 0.0, -0.09677615761756897, 0.02901112101972103, 0.0, -0.09906545281410217, 0.02863909862935543, 0.0, -0.10121503472328186, 0.028032293543219566, 0.0, -0.10320869088172913, 0.02720167301595211, 0.0, -0.10502973198890686, 0.02615811489522457, 0.0, -0.10666146874427795, 0.02491246722638607, 0.0, -0.1080876886844635, 0.02347566746175289, 0.0, -0.10929170250892639, 0.021858563646674156, 0.0, -0.11025729775428772, 0.02007209323346615, 0.0, -0.11096683144569397, 0.01812710426747799, 0.0, -0.11140504479408264, 0.016034474596381187, 0.0, -0.11155477166175842, 0.013805171474814415, 0.0, -0.11148801445960999, 0.012503465637564659, 0.0, -0.11128249764442444, 0.01126103661954403, 0.0, -0.11093059182167053, 0.010064622387290001, 0.0, -0.11042323708534241, 0.008900841698050499, 0.0, -0.10975328087806702, 0.007756432984024286, 0.0, -0.1089121401309967, 0.006618103012442589, 0.0, -0.10789218544960022, 0.005472471937537193, 0.0, -0.10668483376502991, 0.004306277260184288, 0.0, -0.10528245568275452, 0.0031062269117683172, 0.0, -0.10367646813392639, 0.001858969684690237, 0.0, -0.10185971856117249, 0.0005512138013727963, 0.0, -0.09982314705848694, -0.000830332632176578, 0.0, -0.09764638543128967, -0.002114097587764263, 0.0, -0.09569898247718811, -0.0032986209262162447, 0.0, -0.093973308801651, -0.004391203634440899, 0.0, -0.0924622118473053, -0.005399088840931654, 0.0, -0.09115758538246155, -0.006329547148197889, 0.0, -0.0900513231754303, -0.007189820986241102, 0.0, -0.0891367495059967, -0.00798715278506279, 0.0, -0.08840528130531311, -0.008728843182325363, 0.0, -0.08785024285316467, -0.009422164410352707, 0.0, -0.08746257424354553, -0.010074328631162643, 0.0, -0.08723607659339905, -0.01069260761141777, 0.0, -0.08716216683387756, -0.011284273117780685, 0.0, -0.08721700310707092, -0.011963587254285812, 0.0, -0.08737960457801819, -0.012604992836713791, 0.0, -0.08764520287513733, -0.013204436749219894, 0.0, -0.08800950646400452, -0.013757925480604172, 0.0, -0.08846965432167053, -0.014261405915021896, 0.0, -0.08902087807655334, -0.014710824936628342, 0.0, -0.08965888619422913, -0.015102189034223557, 0.0, -0.09037986397743225, -0.015431415289640427, 0.0, -0.0911804735660553, -0.015694510191679, 0.0, -0.09205594658851624, -0.015887420624494553, 0.0, -0.09300199151039124, -0.01600615307688713, 0.0, -0.09401527047157288, -0.01604662463068962, 0.0, -0.09500661492347717, -0.016012411564588547, 0.0, -0.09606137871742249, -0.01590839959681034, 0.0, -0.09717527031898499, -0.015732625499367714, 0.0, -0.09834304451942444, -0.015483061783015728, 0.0, -0.09956136345863342, -0.015157650224864483, 0.0, -0.1008249819278717, -0.014754395000636578, 0.0, -0.10212960839271545, -0.014271298423409462, 0.0, -0.10347095131874084, -0.013706305995583534, 0.0, -0.10484471917152405, -0.013057449832558632, 0.0, -0.10624662041664124, -0.012322673574090004, 0.0, -0.10767140984535217, -0.011499980464577675, 0.0, -0.10911527276039124, -0.010587343946099281, 0.0, -0.06462828069925308, -0.051125358790159225, 0.0, -0.054290447384119034, -0.051125362515449524, 0.0, -0.054290447384119034, -0.02301589958369732, 0.0, -0.053263816982507706, -0.023374244570732117, 0.0, -0.052271518856287, -0.023695096373558044, 0.0, -0.0513102151453495, -0.02397961914539337, 0.0, -0.05037561431527138, -0.02422906458377838, 0.0, -0.0494634248316288, -0.02444465458393097, 0.0, -0.04856983199715614, -0.024627551436424255, 0.0, -0.04769054427742958, -0.024779006838798523, 0.0, -0.04682222381234169, -0.024900183081626892, 0.0, -0.04596010223031044, -0.024992361664772034, 0.0, -0.045100364834070206, -0.02505667507648468, 0.0, -0.04423872008919716, -0.025094404816627502, 0.0, -0.04337183013558388, -0.025106683373451233, 0.0, -0.039663467556238174, -0.024885401129722595, 0.0, -0.03616109862923622, -0.024236604571342468, 0.0, -0.032887134701013565, -0.023182883858680725, 0.0, -0.0298635084182024, -0.02174680121243, 0.0, -0.027112634852528572, -0.019950972869992256, 0.0, -0.024656446650624275, -0.017817990854382515, 0.0, -0.022517355158925056, -0.015370385721325874, 0.0, -0.02071729488670826, -0.012630807235836983, 0.0, -0.019278675317764282, -0.009621815755963326, 0.0, -0.01822391152381897, -0.006365972105413675, 0.0, -0.017574459314346313, -0.0028858953155577183, 0.0, -0.017353206872940063, 0.0007958238711580634, 0.0, -0.01755395531654358, 0.00484658544883132, 0.0, -0.018148094415664673, 0.008625520393252373, 0.0, -0.0191208403557539, 0.012117279693484306, 0.0, -0.02045932225883007, 0.01530657522380352, 0.0, -0.022149233147501945, 0.018178028985857964, 0.0, -0.024177221581339836, 0.020716382190585136, 0.0, -0.026529459282755852, 0.0229062270373106, 0.0, -0.029192117974162102, 0.024732304736971855, 0.0, -0.03215184435248375, 0.026179268956184387, 0.0, -0.0353948138654232, 0.027231797575950623, 0.0, -0.03890719637274742, 0.027874544262886047, 0.0, -0.04267468675971031, 0.028092190623283386, 0.0, -0.06462827324867249, 0.028092192485928535, 0.0, -0.054290443658828735, 0.019380586221814156, 0.0, -0.04383626580238342, 0.019380584359169006, 0.0, -0.0410100519657135, 0.019230946898460388, 0.0, -0.03850331902503967, 0.018793359398841858, 0.0, -0.03630271553993225, 0.018084749579429626, 0.0, -0.03439345955848694, 0.017122015357017517, 0.0, -0.032761722803115845, 0.015922173857688904, 0.0, -0.031393200159072876, 0.014502092264592648, 0.0, -0.030274061486124992, 0.012878729961812496, 0.0, -0.0293900053948164, 0.011069073341786861, 0.0, -0.028727203607559204, 0.009089990518987179, 0.0, -0.028271347284317017, 0.006958468351513147, 0.0, -0.02800765633583069, 0.004691435489803553, 0.0, -0.027923256158828735, 0.0023058487568050623, 0.0, -0.02806153893470764, -0.00034435244742780924, 0.0, -0.02846875786781311, -0.002827571239322424, 0.0, -0.029132038354873657, -0.005131707992404699, 0.0, -0.030039936304092407, -0.007244662381708622, 0.0, -0.03118005394935608, -0.00915436539798975, 0.0, -0.032540470361709595, -0.010848687030375004, 0.0, -0.03410878777503967, -0.012315557338297367, 0.0, -0.03587356209754944, -0.013542846776545048, 0.0, -0.03782191872596741, -0.014518454670906067, 0.0, -0.0399419367313385, -0.015230312943458557, 0.0, -0.042222172021865845, -0.015666291117668152, 0.0, -0.044649749994277954, -0.015814319252967834, 0.0, -0.04550471901893616, -0.01580207049846649, 0.0, -0.046331554651260376, -0.01576484739780426, 0.0, -0.04713597893714905, -0.015701785683631897, 0.0, -0.04792323708534241, -0.015612110495567322, 0.0, -0.048699527978897095, -0.015495016239583492, 0.0, -0.049470096826553345, -0.01534970011562109, 0.0, -0.05024018883705139, -0.015175326727330685, 0.0, -0.05101647973060608, -0.014971121214330196, 0.0, -0.05180373787879944, -0.01473624911159277, 0.0, -0.05260816216468811, -0.014469935558736324, 0.0, -0.05343499779701233, -0.014171346090734005, 0.0, -0.054290443658828735, -0.013839676044881344, 0.0, -0.0046922299079597, -0.024061311036348343, 0.0, 0.00564559968188405, -0.024061311036348343, 0.0, 0.0056456043384969234, 0.028092186897993088, 0.0, -0.0046922252513468266, 0.028092186897993088, 0.0, -0.005737457890063524, -0.03985835984349251, 0.0, -0.00568071473389864, -0.04068710282444954, 0.0, -0.005515729077160358, -0.041483987122774124, 0.0, -0.005249653942883015, -0.042241353541612625, 0.0, -0.004890118725597858, -0.04295151308178902, 0.0, -0.004445229656994343, -0.04360683634877205, 0.0, -0.003922616131603718, -0.044199634343385696, 0.0, -0.003329907776787877, -0.04472227767109871, 0.0, -0.0026747335214167833, -0.045167047530412674, 0.0, -0.001964246155694127, -0.04552634432911873, 0.0, -0.0012070287484675646, -0.04579247906804085, 0.0, -0.0004102339153178036, -0.045957762748003006, 0.0, 0.00041850906563922763, -0.04601456597447395, 0.0, 0.001247251988388598, -0.045957762748003006, 0.0, 0.0020440469961613417, -0.04579244926571846, 0.0, 0.0028017412405461073, -0.04552634432911873, 0.0, 0.0035117517691105604, -0.045167047530412674, 0.0, 0.004166926257312298, -0.04472224786877632, 0.0, 0.004759634844958782, -0.044199634343385696, 0.0, 0.005282248370349407, -0.04360680654644966, 0.0, 0.005727137438952923, -0.04295151308178902, 0.0, 0.006086672656238079, -0.04224132373929024, 0.0, 0.006352747790515423, -0.041483957320451736, 0.0, 0.006517733447253704, -0.04068707302212715, 0.0, 0.006574954371899366, -0.03985835984349251, 0.0, 0.006517733912914991, -0.03902961686253548, 0.0, 0.00635274825617671, -0.038232702761888504, 0.0, 0.006086673121899366, -0.03747536614537239, 0.0, 0.00572713790461421, -0.03676517680287361, 0.0, 0.0052822488360106945, -0.03610988333821297, 0.0, 0.0047596353106200695, -0.03551705554127693, 0.0, 0.004166926722973585, -0.03499444201588631, 0.0, 0.003511752700433135, -0.034549642354249954, 0.0, 0.0028012653347104788, -0.0341903455555439, 0.0, 0.0020440479274839163, -0.03392424061894417, 0.0, 0.0012472531525418162, -0.03375892713665962, 0.0, 0.00041851014248095453, -0.03370215371251106, 0.0, -0.0004102328384760767, -0.03375895693898201, 0.0, -0.0012070277007296681, -0.03392424061894417, 0.0, -0.0019642452243715525, -0.0341903455555439, 0.0, -0.0026747325900942087, -0.034549642354249954, 0.0, -0.0033299068454653025, -0.03499444201588631, 0.0, -0.0039226156659424305, -0.03551705554127693, 0.0, -0.0044452291913330555, -0.03610988333821297, 0.0, -0.004890118259936571, -0.03676517680287361, 0.0, -0.005249653477221727, -0.03747536614537239, 0.0, -0.005515728611499071, -0.03823273256421089, 0.0, -0.005680714268237352, -0.03902961686253548, 0.0, 0.020513387396931648, 0.02809218503534794, 0.0, 0.02051338367164135, -0.024061312898993492, 0.0, 0.0308512132614851, -0.024061312898993492, 0.0, 0.030851216986775398, 0.013224371708929539, 0.0, 0.031714290380477905, 0.014368780888617039, 0.0, 0.03261885046958923, 0.015420028008520603, 0.0, 0.033560603857040405, 0.016376890242099762, 0.0, 0.03453812003135681, 0.017238177359104156, 0.0, 0.035547107458114624, 0.018002666532993317, 0.0, 0.03658613562583923, 0.018669135868549347, 0.0, 0.03765186667442322, 0.01923639327287674, 0.0, 0.038740962743759155, 0.019703246653079987, 0.0, 0.03985103964805603, 0.020068444311618805, 0.0, 0.04097971320152283, 0.020330794155597687, 0.0, 0.04212316870689392, 0.020489104092121124, 0.0, 0.0432794988155365, 0.020542122423648834, 0.0, 0.04497846961021423, 0.020455606281757355, 0.0, 0.04653152823448181, 0.020198501646518707, 0.0, 0.04793867468833923, 0.019774414598941803, 0.0, 0.049199432134628296, 0.01918698102235794, 0.0, 0.050313323736190796, 0.01843983680009842, 0.0, 0.05127987265586853, 0.017536617815494537, 0.0, 0.0520990788936615, 0.016480959951877594, 0.0, 0.052769988775253296, 0.015276438556611538, 0.0, 0.05329260230064392, 0.013926750980317593, 0.0, 0.05366644263267517, 0.012435502372682095, 0.0, 0.05389103293418884, 0.010806298814713955, 0.0, 0.05396589636802673, 0.00904280599206686, 0.0, 0.053965892642736435, -0.02406131662428379, 0.0, 0.06430372595787048, -0.02406131662428379, 0.0, 0.06430372595787048, 0.00834587775170803, 0.0, 0.06415113806724548, 0.011536633595824242, 0.0, 0.06370386481285095, 0.014483785256743431, 0.0, 0.06297716498374939, 0.017180895432829857, 0.0, 0.061984866857528687, 0.01962149702012539, 0.0, 0.060742709785699844, 0.021799122914671898, 0.0, 0.05926546826958656, 0.02370733581483364, 0.0, 0.05756792798638344, 0.025339698418974876, 0.0, 0.05566534772515297, 0.026689713820815086, 0.0, 0.05357203260064125, 0.027750974521040916, 0.0, 0.05130324140191078, 0.028517015278339386, 0.0, 0.04887423291802406, 0.028981365263462067, 0.0, 0.04629978910088539, 0.029137589037418365, 0.0, 0.0450042225420475, 0.02907548099756241, 0.0, 0.043679092079401016, 0.02889237552881241, 0.0, 0.04233393445611, 0.028593100607395172, 0.0, 0.04097780957818031, 0.02818254381418228, 0.0, 0.039620254188776016, 0.027665473520755768, 0.0, 0.03827032819390297, 0.0270468071103096, 0.0, 0.036937568336725235, 0.026331312954425812, 0.0, 0.03563055768609047, 0.025523878633975983, 0.0, 0.03435930982232094, 0.02462933212518692, 0.0, 0.0331328846514225, 0.02365250140428543, 0.0, 0.031960342079401016, 0.02259824424982071, 0.0, 0.030851216986775398, 0.021471360698342323, 0.0, 0.030851216986775398, 0.02809218503534794, 0.0, 0.07882293313741684, -0.05112537369132042, 0.0, 0.08916076272726059, -0.05112537369132042, 0.0, 0.08916077017784119, 0.02809217944741249, 0.0, 0.07882294058799744, 0.02809217944741249, 0.0, 0.10007937997579575, -0.05112537369132042, 0.0, 0.14235958456993103, -0.05112537741661072, 0.0, 0.14235958456993103, 0.028092173859477043, 0.0, 0.13097652792930603, 0.028092175722122192, 0.0, 0.13097652792930603, -0.008728891611099243, 0.0, 0.10007938742637634, -0.00872888881713152, 0.0, 0.10007938742637634, -0.018950490280985832, 0.0, 0.13097652792930603, -0.01895049214363098, 0.0, 0.13097652792930603, -0.04090374708175659, 0.0, 0.10007938742637634, -0.04090374335646629, 0.0, 0.23458656668663025, -0.05112538859248161, 0.0, 0.23458656668663025, 0.028092166408896446, 0.0, 0.22320351004600525, 0.028092168271541595, 0.0, 0.22320351004600525, -0.0061734700575470924, 0.0, 0.2113555371761322, -0.006173469126224518, 0.0, 0.2069748342037201, -0.006372667383402586, 0.0, 0.20300421118736267, -0.006953752599656582, 0.0, 0.1994388997554779, -0.00789219792932272, 0.0, 0.19627270102500916, -0.0091633852571249, 0.0, 0.1935003697872162, -0.010742699727416039, 0.0, 0.19111570715904236, -0.01260555349290371, 0.0, 0.18911346793174744, -0.014727329835295677, 0.0, 0.18748793005943298, -0.017083441838622093, 0.0, 0.18623337149620056, -0.019649242982268333, 0.0, 0.18534454703330994, -0.022400205954909325, 0.0, 0.18481525778770447, -0.025311654433608055, 0.0, 0.18463978171348572, -0.028359031304717064, 0.0, 0.1848052442073822, -0.03144225850701332, 0.0, 0.18530496954917908, -0.034401241689920425, 0.0, 0.18614467978477478, -0.037208590656518936, 0.0, 0.18732866644859314, -0.039836857467889786, 0.0, 0.1888631284236908, -0.042258623987436295, 0.0, 0.19075283408164978, -0.04444647207856178, 0.0, 0.19300302863121033, -0.04637298732995987, 0.0, 0.19561895728111267, -0.04801071435213089, 0.0, 0.19860586524009705, -0.04933223873376846, 0.0, 0.2019689977169037, -0.05031014233827591, 0.0, 0.20571407675743103, -0.05091700702905655, 0.0, 0.2098453938961029, -0.051125384867191315, 0.0, 0.22320351004600525, -0.04090375453233719, 0.0, 0.2098453938961029, -0.04090375453233719, 0.0, 0.20740875601768494, -0.04077697545289993, 0.0, 0.20525822043418884, -0.04041225463151932, 0.0, 0.20337900519371033, -0.039832957088947296, 0.0, 0.2017577588558197, -0.03906247764825821, 0.0, 0.20038017630577087, -0.038124240934848785, 0.0, 0.19923195242881775, -0.03704161196947098, 0.0, 0.19829925894737244, -0.03583798557519913, 0.0, 0.19756779074668884, -0.034536756575107574, 0.0, 0.19702324271202087, -0.03316131979227066, 0.0, 0.19665178656578064, -0.031735070049762726, 0.0, 0.19643911719322205, -0.030281370505690575, 0.0, 0.1963714063167572, -0.028823649510741234, 0.0, 0.19648393988609314, -0.026919877156615257, 0.0, 0.1968153417110443, -0.025160467252135277, 0.0, 0.19735702872276306, -0.023549502715468407, 0.0, 0.19810089468955994, -0.022090977057814598, 0.0, 0.19903835654258728, -0.020788943395018578, 0.0, 0.20016130805015564, -0.019647425040602684, 0.0, 0.20146021246910095, -0.018670475110411644, 0.0, 0.20292791724205017, -0.017862088978290558, 0.0, 0.20455488562583923, -0.01722634583711624, 0.0, 0.2063334882259369, -0.016767241060733795, 0.0, 0.20825466513633728, -0.016488797962665558, 0.0, 0.21031031012535095, -0.016395099461078644, 0.0, 0.22320351004600525, -0.016395099461078644, 0.0, 0.2515452802181244, -0.05112538859248161, 0.0, 0.2629283368587494, -0.05112538859248161, 0.0, 0.2629283368587494, 0.028092164546251297, 0.0, 0.2515452802181244, 0.028092164546251297, 0.0, 0.3086932599544525, -0.05112539231777191, 0.0, 0.3200763165950775, -0.05112539604306221, 0.0, 0.3200763165950775, 0.02809215895831585, 0.0, 0.27291759848594666, 0.028092162683606148, 0.0, 0.27291759848594666, 0.01787056215107441, 0.0, 0.3086932599544525, 0.01787056028842926, 0.0, 0.3320401608943939, -0.05112539604306221, 0.0, 0.3743208348751068, -0.05112539976835251, 0.0, 0.3743208348751068, 0.0280921533703804, 0.0, 0.3629377782344818, 0.02809215523302555, 0.0, 0.3629377782344818, -0.008728912100195885, 0.0, 0.3320401608943939, -0.00872890930622816, 0.0, 0.3320401608943939, -0.018950510770082474, 0.0, 0.3629377782344818, -0.018950512632727623, 0.0, 0.3629377782344818, -0.04090376943349838, 0.0, 0.3320401608943939, -0.040903765708208084, 0.0});
    _triz = std::vector<int>({1, 47, 0, 1, 46, 47, 2, 46, 1, 2, 45, 46, 3, 45, 2, 3, 44, 45, 4, 44, 3, 4, 43, 44, 5, 43, 4, 5, 42, 43, 6, 42, 5, 6, 41, 42, 7, 48, 6, 48, 41, 6, 7, 95, 48, 49, 41, 48, 7, 94, 95, 50, 41, 49, 7, 93, 94, 51, 41, 50, 51, 40, 41, 8, 93, 7, 8, 92, 93, 52, 40, 51, 8, 91, 92, 53, 40, 52, 8, 90, 91, 54, 40, 53, 54, 39, 40, 9, 90, 8, 9, 89, 90, 55, 39, 54, 9, 88, 89, 56, 39, 55, 56, 38, 39, 10, 88, 9, 10, 87, 88, 57, 38, 56, 57, 37, 38, 11, 87, 10, 11, 86, 87, 58, 37, 57, 11, 85, 86, 59, 37, 58, 59, 36, 37, 12, 85, 11, 12, 84, 85, 60, 36, 59, 13, 84, 12, 13, 83, 84, 60, 35, 36, 61, 35, 60, 13, 82, 83, 62, 35, 61, 14, 82, 13, 62, 34, 35, 14, 81, 82, 63, 34, 62, 14, 80, 81, 15, 80, 14, 64, 34, 63, 64, 33, 34, 15, 79, 80, 65, 33, 64, 16, 79, 15, 65, 32, 33, 16, 78, 79, 66, 32, 65, 16, 77, 78, 67, 32, 66, 17, 77, 16, 67, 31, 32, 17, 76, 77, 68, 31, 67, 17, 75, 76, 69, 31, 68, 17, 74, 75, 70, 31, 69, 18, 74, 17, 70, 30, 31, 18, 73, 74, 71, 30, 70, 18, 72, 73, 72, 30, 71, 18, 30, 72, 19, 30, 18, 19, 29, 30, 20, 29, 19, 20, 28, 29, 21, 28, 20, 21, 27, 28, 22, 27, 21, 22, 26, 27, 23, 26, 22, 23, 25, 26, 24, 25, 23, 190, 188, 189, 166, 164, 165, 191, 188, 190, 191, 187, 188, 167, 164, 166, 167, 163, 164, 192, 187, 191, 192, 186, 187, 168, 163, 167, 193, 186, 192, 193, 185, 186, 168, 162, 163, 169, 162, 168, 194, 185, 193, 97, 202, 96, 97, 201, 202, 194, 184, 185, 170, 162, 169, 195, 184, 194, 170, 161, 162, 195, 183, 184, 196, 183, 195, 171, 161, 170, 196, 182, 183, 171, 160, 161, 197, 182, 196, 172, 160, 171, 197, 181, 182, 198, 181, 197, 173, 160, 172, 173, 159, 160, 198, 180, 181, 199, 180, 198, 174, 159, 173, 199, 179, 180, 200, 179, 199, 174, 158, 159, 175, 158, 174, 200, 178, 179, 201, 178, 200, 176, 158, 175, 176, 138, 158, 138, 157, 158, 97, 99, 201, 99, 100, 201, 100, 101, 201, 101, 102, 201, 102, 103, 201, 103, 104, 201, 104, 105, 201, 105, 106, 201, 106, 107, 201, 107, 108, 201, 108, 109, 201, 109, 110, 201, 110, 178, 201, 110, 111, 178, 111, 177, 178, 177, 137, 176, 137, 138, 176, 112, 177, 111, 139, 157, 138, 177, 136, 137, 113, 177, 112, 140, 157, 139, 177, 135, 136, 114, 177, 113, 141, 157, 140, 177, 134, 135, 115, 177, 114, 115, 134, 177, 142, 157, 141, 115, 133, 134, 142, 156, 157, 116, 133, 115, 116, 132, 133, 143, 156, 142, 116, 131, 132, 117, 131, 116, 144, 156, 143, 117, 130, 131, 118, 130, 117, 145, 156, 144, 118, 129, 130, 145, 155, 156, 119, 129, 118, 119, 128, 129, 146, 155, 145, 119, 127, 128, 120, 127, 119, 147, 155, 146, 120, 126, 127, 147, 154, 155, 121, 126, 120, 97, 98, 99, 121, 125, 126, 148, 154, 147, 122, 125, 121, 149, 154, 148, 149, 153, 154, 123, 125, 122, 150, 153, 149, 150, 152, 153, 124, 125, 123, 151, 152, 150, 241, 239, 240, 241, 238, 239, 242, 238, 241, 242, 237, 238, 243, 237, 242, 243, 236, 237, 244, 236, 243, 244, 235, 236, 245, 235, 244, 245, 234, 235, 246, 234, 245, 246, 233, 234, 247, 289, 246, 289, 233, 246, 247, 288, 289, 290, 233, 289, 247, 287, 288, 291, 233, 290, 247, 286, 287, 292, 233, 291, 292, 232, 233, 247, 285, 286, 248, 285, 247, 293, 232, 292, 248, 284, 285, 294, 232, 293, 248, 283, 284, 295, 232, 294, 248, 282, 283, 296, 232, 295, 249, 282, 248, 296, 231, 232, 249, 281, 282, 297, 231, 296, 249, 280, 281, 298, 231, 297, 250, 280, 249, 298, 230, 231, 250, 279, 280, 299, 230, 298, 250, 278, 279, 300, 230, 299, 251, 278, 250, 251, 277, 278, 300, 229, 230, 301, 229, 300, 251, 301, 277, 251, 229, 301, 252, 229, 251, 252, 228, 229, 253, 227, 252, 227, 228, 252, 253, 226, 227, 254, 226, 253, 254, 225, 226, 254, 224, 225, 255, 224, 254, 255, 223, 224, 256, 223, 255, 256, 222, 223, 204, 276, 203, 256, 221, 222, 205, 276, 204, 206, 276, 205, 257, 221, 256, 257, 220, 221, 207, 276, 206, 208, 276, 207, 257, 219, 220, 209, 276, 208, 257, 218, 219, 210, 276, 209, 258, 218, 257, 211, 276, 210, 258, 217, 218, 212, 276, 211, 258, 216, 217, 213, 276, 212, 214, 276, 213, 258, 215, 216, 215, 276, 214, 258, 276, 215, 259, 276, 258, 259, 275, 276, 260, 275, 259, 260, 274, 275, 260, 273, 274, 261, 273, 260, 261, 272, 273, 261, 271, 272, 262, 271, 261, 262, 270, 271, 262, 269, 270, 263, 269, 262, 263, 268, 269, 263, 267, 268, 263, 266, 267, 264, 266, 263, 264, 265, 266, 302, 329, 328, 329, 327, 328, 329, 326, 327, 329, 325, 326, 329, 324, 325, 329, 323, 324, 329, 322, 323, 329, 330, 322, 330, 331, 322, 331, 321, 322, 302, 355, 329, 332, 321, 331, 333, 321, 332, 334, 321, 333, 334, 320, 321, 335, 320, 334, 336, 320, 335, 336, 319, 320, 337, 319, 336, 337, 318, 319, 338, 318, 337, 339, 318, 338, 339, 317, 318, 340, 317, 339, 340, 316, 317, 341, 316, 340, 341, 315, 316, 342, 315, 341, 343, 315, 342, 343, 314, 315, 344, 314, 343, 344, 313, 314, 345, 313, 344, 346, 313, 345, 346, 312, 313, 347, 312, 346, 347, 311, 312, 348, 311, 347, 349, 311, 348, 349, 310, 311, 350, 310, 349, 350, 309, 310, 351, 309, 350, 352, 309, 351, 352, 308, 309, 353, 308, 352, 354, 308, 353, 302, 354, 355, 302, 308, 354, 302, 307, 308, 302, 306, 307, 302, 305, 306, 302, 304, 305, 302, 303, 304, 369, 367, 368, 369, 366, 367, 370, 366, 369, 370, 365, 366, 370, 364, 365, 371, 364, 370, 371, 363, 364, 371, 362, 363, 372, 362, 371, 372, 361, 362, 372, 360, 361, 373, 360, 372, 373, 359, 360, 373, 358, 359, 374, 358, 373, 374, 357, 358, 374, 356, 357, 375, 356, 374, 375, 481, 356, 481, 482, 356, 482, 483, 356, 483, 484, 356, 484, 485, 356, 485, 486, 356, 486, 487, 356, 487, 488, 356, 488, 489, 356, 376, 479, 375, 479, 480, 375, 480, 481, 375, 377, 478, 376, 478, 479, 376, 378, 476, 377, 476, 477, 377, 477, 478, 377, 378, 475, 476, 378, 474, 475, 378, 473, 474, 378, 472, 473, 378, 471, 472, 379, 471, 378, 379, 470, 471, 379, 469, 470, 379, 468, 469, 379, 467, 468, 380, 467, 379, 380, 466, 467, 380, 465, 466, 380, 464, 465, 381, 464, 380, 381, 463, 464, 381, 462, 463, 381, 461, 462, 381, 460, 461, 381, 459, 460, 382, 459, 381, 382, 458, 459, 382, 457, 458, 382, 456, 457, 383, 456, 382, 383, 455, 456, 383, 454, 455, 383, 453, 454, 384, 453, 383, 384, 452, 453, 385, 452, 384, 385, 451, 452, 385, 450, 451, 386, 450, 385, 386, 449, 450, 387, 449, 386, 387, 448, 449, 387, 447, 448, 388, 447, 387, 388, 446, 447, 389, 446, 388, 389, 445, 446, 389, 444, 445, 390, 444, 389, 390, 443, 444, 391, 443, 390, 391, 442, 443, 392, 442, 391, 392, 441, 442, 417, 415, 416, 392, 440, 441, 393, 440, 392, 417, 414, 415, 394, 440, 393, 417, 413, 414, 395, 440, 394, 395, 439, 440, 417, 412, 413, 396, 439, 395, 417, 411, 412, 397, 439, 396, 417, 410, 411, 398, 439, 397, 398, 438, 439, 417, 409, 410, 399, 438, 398, 400, 438, 399, 417, 408, 409, 401, 438, 400, 417, 407, 408, 402, 438, 401, 417, 406, 407, 403, 438, 402, 417, 405, 406, 404, 438, 403, 417, 404, 405, 404, 437, 438, 417, 437, 404, 417, 436, 437, 417, 435, 436, 418, 435, 417, 418, 434, 435, 419, 434, 418, 420, 434, 419, 420, 433, 434, 421, 433, 420, 422, 433, 421, 422, 432, 433, 423, 432, 422, 423, 431, 432, 424, 431, 423, 425, 431, 424, 425, 430, 431, 426, 430, 425, 427, 430, 426, 427, 429, 430, 428, 429, 427, 492, 490, 491, 492, 529, 490, 505, 503, 504, 505, 502, 503, 505, 501, 502, 505, 500, 501, 505, 499, 500, 506, 499, 505, 506, 498, 499, 506, 497, 498, 506, 496, 497, 507, 496, 506, 507, 495, 496, 507, 494, 495, 507, 493, 494, 507, 492, 493, 508, 492, 507, 508, 564, 492, 564, 565, 492, 565, 566, 492, 566, 567, 492, 567, 529, 492, 509, 561, 508, 561, 562, 508, 562, 563, 508, 563, 564, 508, 510, 558, 509, 558, 559, 509, 559, 560, 509, 560, 561, 509, 511, 555, 510, 555, 556, 510, 556, 557, 510, 557, 558, 510, 511, 554, 555, 511, 553, 554, 512, 553, 511, 512, 552, 553, 512, 551, 552, 530, 529, 567, 512, 550, 551, 513, 550, 512, 513, 549, 550, 513, 548, 549, 514, 548, 513, 514, 547, 548, 514, 546, 547, 515, 546, 514, 515, 545, 546, 516, 545, 515, 516, 544, 545, 516, 543, 544, 517, 543, 516, 517, 542, 543, 517, 541, 542, 518, 541, 517, 518, 540, 541, 519, 540, 518, 519, 539, 540, 519, 538, 539, 520, 538, 519, 520, 537, 538, 520, 536, 537, 521, 536, 520, 521, 535, 536, 521, 534, 535, 521, 533, 534, 522, 533, 521, 522, 532, 533, 522, 531, 532, 522, 530, 531, 522, 529, 530, 523, 529, 522, 524, 529, 523, 525, 529, 524, 526, 529, 525, 527, 529, 526, 528, 529, 527, 585, 583, 584, 585, 582, 583, 586, 582, 585, 586, 581, 582, 587, 581, 586, 587, 580, 581, 588, 580, 587, 588, 579, 580, 589, 579, 588, 589, 578, 579, 590, 578, 589, 590, 577, 578, 591, 577, 590, 591, 576, 577, 592, 576, 591, 592, 575, 576, 593, 575, 592, 593, 574, 575, 594, 574, 593, 594, 573, 574, 595, 573, 594, 595, 572, 573, 596, 572, 595, 597, 572, 596, 597, 619, 572, 597, 618, 619, 598, 618, 597, 598, 617, 618, 599, 617, 598, 599, 616, 617, 600, 616, 599, 600, 615, 616, 601, 615, 600, 601, 614, 615, 602, 614, 601, 602, 613, 614, 603, 613, 602, 603, 612, 613, 604, 612, 603, 604, 611, 612, 605, 611, 604, 605, 610, 611, 606, 610, 605, 606, 609, 610, 607, 609, 606, 607, 608, 609, 570, 568, 569, 570, 571, 568, 650, 648, 649, 650, 647, 648, 623, 621, 622, 623, 620, 621, 651, 647, 650, 651, 646, 647, 651, 645, 646, 652, 645, 651, 652, 644, 645, 624, 620, 623, 652, 643, 644, 625, 620, 624, 653, 643, 652, 653, 642, 643, 626, 620, 625, 627, 620, 626, 653, 641, 642, 654, 641, 653, 628, 620, 627, 654, 640, 641, 629, 674, 628, 674, 620, 628, 654, 639, 640, 630, 674, 629, 654, 638, 639, 631, 674, 630, 655, 638, 654, 632, 674, 631, 655, 637, 638, 633, 674, 632, 655, 636, 637, 634, 674, 633, 655, 635, 636, 635, 674, 634, 655, 674, 635, 655, 673, 674, 675, 620, 674, 656, 673, 655, 656, 672, 673, 656, 671, 672, 657, 671, 656, 657, 670, 671, 658, 670, 657, 658, 669, 670, 658, 668, 669, 659, 668, 658, 659, 667, 668, 659, 666, 667, 660, 666, 659, 660, 665, 666, 661, 665, 660, 661, 664, 665, 661, 663, 664, 662, 663, 661, 678, 676, 677, 678, 679, 676, 682, 688, 681, 688, 680, 681, 688, 689, 680, 682, 687, 688, 682, 684, 687, 684, 686, 687, 684, 685, 686, 682, 683, 684, 691, 719, 690, 719, 718, 690, 719, 717, 718, 719, 716, 717, 719, 715, 716, 719, 714, 715, 719, 713, 714, 719, 712, 713, 719, 711, 712, 719, 720, 711, 720, 710, 711, 691, 745, 719, 721, 710, 720, 722, 710, 721, 723, 710, 722, 723, 709, 710, 724, 709, 723, 725, 709, 724, 726, 709, 725, 726, 708, 709, 727, 708, 726, 728, 708, 727, 729, 708, 728, 729, 707, 708, 730, 707, 729, 731, 707, 730, 731, 706, 707, 732, 706, 731, 733, 706, 732, 733, 705, 706, 734, 705, 733, 734, 704, 705, 735, 704, 734, 736, 704, 735, 736, 703, 704, 737, 703, 736, 738, 703, 737, 738, 702, 703, 739, 702, 738, 740, 702, 739, 741, 702, 740, 742, 702, 741, 742, 701, 702, 743, 701, 742, 744, 701, 743, 691, 693, 745, 693, 744, 745, 693, 701, 744, 693, 700, 701, 693, 699, 700, 693, 698, 699, 693, 697, 698, 693, 696, 697, 693, 695, 696, 693, 694, 695, 691, 692, 693, 748, 746, 747, 748, 749, 746, 752, 750, 751, 752, 755, 750, 752, 754, 755, 752, 753, 754, 758, 764, 757, 764, 756, 757, 764, 765, 756, 758, 763, 764, 758, 760, 763, 760, 762, 763, 760, 761, 762, 758, 759, 760});

    t.reset();
    t.start();
    _initializeAttributeGrids(isize, jsize, ksize);
    t.stop();

    _logfile.log("Constructing Attribute Grids:      \t", t.getTime(), 4, 1);
}

void FluidSimulation::_initializeParticleSystems() {
    _markerParticles.addAttributeVector3("POSITION");
    _markerParticles.addAttributeVector3("VELOCITY");

    if (_velocityTransferMethod == VelocityTransferMethod::APIC) {
        _markerParticles.addAttributeVector3("AFFINEX");
        _markerParticles.addAttributeVector3("AFFINEY");
        _markerParticles.addAttributeVector3("AFFINEZ");
    }

    if (_isSurfaceAgeAttributeEnabled) {
        _markerParticles.addAttributeFloat("AGE");
    }

    if (_isSurfaceSourceColorAttributeEnabled) {
        _markerParticles.addAttributeVector3("COLOR");
    }

    if (_isSurfaceSourceIDAttributeEnabled) {
        _markerParticles.addAttributeInt("SOURCEID");
    }
}

void FluidSimulation::_initializeForceFieldGrid(int isize, int jsize, int ksize, double dx) {
    int reduction = _forceFieldReductionLevel;
    int isizeff = (int)std::ceil((double)isize / (double)reduction);
    int jsizeff = (int)std::ceil((double)jsize / (double)reduction); ;
    int ksizeff = (int)std::ceil((double)ksize / (double)reduction); ;
    double dxff = dx * reduction;
    _forceFieldGrid.initialize(isizeff, jsizeff, ksizeff, dxff);
}

void FluidSimulation::_initializeAttributeGrids(int isize, int jsize, int ksize) {
    if (_isSurfaceVorticityAttributeEnabled) {
        _vorticityAttributeGrid = Array3d<vmath::vec3>(isize, jsize, ksize);
    }

    if (_isSurfaceAgeAttributeEnabled) {
        _ageAttributeGrid = Array3d<float>(isize, jsize, ksize, 0.0f);
        _ageAttributeCountGrid = Array3d<int>(isize, jsize, ksize, 0);
        _ageAttributeValidGrid = Array3d<bool>(isize, jsize, ksize, false);
    }

    if (_isSurfaceSourceColorAttributeEnabled) {
        _colorAttributeGridR = Array3d<float>(isize, jsize, ksize, 0.0f);
        _colorAttributeGridG = Array3d<float>(isize, jsize, ksize, 0.0f);
        _colorAttributeGridB = Array3d<float>(isize, jsize, ksize, 0.0f);
        _colorAttributeCountGrid = Array3d<int>(isize, jsize, ksize, 0);
        _colorAttributeValidGrid = Array3d<bool>(isize, jsize, ksize, false);
    }
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

void FluidSimulation::_addMarkerParticles(std::vector<MarkerParticle> &particles, MarkerParticleAttributes attributes) {
    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    std::vector<int> *sourceids = nullptr;
    if (_isSurfaceSourceIDAttributeEnabled) {
        _markerParticles.getAttributeValues("SOURCEID", sourceids);
    }

    std::vector<vmath::vec3> *sourcecolors = nullptr;
    if (_isSurfaceSourceColorAttributeEnabled) {
        _markerParticles.getAttributeValues("COLOR", sourcecolors);
    }

    for (size_t i = 0; i < particles.size(); i++) {
        MarkerParticle mp = particles[i];
        GridIndex g = Grid3d::positionToGridIndex(mp.position, _dx);
        if (Grid3d::isGridIndexInRange(g, _isize, _jsize, _ksize)) {
            positions->push_back(mp.position);
            velocities->push_back(mp.velocity);

            if (_isSurfaceSourceIDAttributeEnabled) {
                sourceids->push_back(attributes.sourceID);
            }

            if (_isSurfaceSourceColorAttributeEnabled) {
                sourcecolors->push_back(attributes.sourceColor);
            }
        }
    }

    _markerParticles.update();
}

void FluidSimulation::_initializeParticleRadii() {
    double volume = _dx*_dx*_dx / 8.0;
    double pi = 3.141592653;
    _markerParticleRadius = pow(3*volume / (4*pi), 1.0/3.0);

    _liquidSDFParticleRadius = 0.5 * _liquidSDFParticleScale * _dx * sqrt(3.0); 
}

void FluidSimulation::_initializeRandomGenerator() {
    _randomSeed = std::mt19937(_randomDevice());
    _random = std::uniform_real_distribution<>(0, 1); 
}

void FluidSimulation::_initializeSimulation() {
    _logfile.newline();
    _logfile.log(std::ostringstream().flush() << 
                 "Initializing Simulation:" << std::endl);

    _initializeSimulationGrids(_isize, _jsize, _ksize, _dx);
    _initializeParticleSystems();

    _initializeParticleRadii();
    _initializeRandomGenerator();

    if (_upscalingPreviousCellSize) {
        StopWatch upscaleTimer;
        upscaleTimer.start();
        _upscaleParticleData();
        upscaleTimer.stop();
        _logfile.log("Upscaling Particle Data:     \t", upscaleTimer.getTime(), 4, 1);
    }

    if (_isMarkerParticleLoadPending || _isDiffuseParticleLoadPending) {
        StopWatch loadTimer;
        loadTimer.start();
        _loadParticles();
        loadTimer.stop();
        _logfile.log("Loading Particle Data:       \t", loadTimer.getTime(), 4, 1);
    }

    _isSimulationInitialized = true;
}

void FluidSimulation::_upscaleParticleData() {
    int isize = _upscalingPreviousIsize;
    int jsize = _upscalingPreviousJsize;
    int ksize = _upscalingPreviousKsize;
    double dx = _upscalingPreviousCellSize;
    double particleRadius = 0.5 * _liquidSDFParticleScale * dx * sqrt(3.0);

    ParticleSystem markerParticles;
    markerParticles.addAttributeVector3("POSITION");
    markerParticles.addAttributeVector3("VELOCITY");

    std::vector<vmath::vec3> *positions, *velocities;
    markerParticles.getAttributeValues("POSITION", positions);
    markerParticles.getAttributeValues("VELOCITY", velocities);

    AABB bounds(0.0, 0.0, 0.0, isize * dx, jsize * dx, ksize * dx);
    for (size_t j = 0; j < _markerParticleLoadQueue.size(); j++) {
        for (size_t i = 0; i < _markerParticleLoadQueue[j].particles.size(); i++) {
            MarkerParticle mp = _markerParticleLoadQueue[j].particles[i];
            mp.position = (mp.position - _domainOffset) / _domainScale;
            if (bounds.isPointInside(mp.position)) {
                positions->push_back(mp.position);
                velocities->push_back(mp.velocity);
            }
        }
    }

    markerParticles.update();

    if (markerParticles.empty()) {
        return;
    }

    ParticleLevelSet liquidSDF(isize, jsize, ksize, dx);
    liquidSDF.calculateSignedDistanceField(markerParticles, particleRadius);

    MACVelocityField vfield(isize, jsize, ksize, dx);
    ValidVelocityComponentGrid validVelocities(isize, jsize, ksize);
    VelocityAdvector velocityAdvector;

    VelocityAdvectorParameters params;
    params.particles = &markerParticles;
    params.vfield = &vfield;
    params.validVelocities = &validVelocities;
    params.particleRadius = particleRadius;

    velocityAdvector.advect(params);
    int extrapolationLayers = (int)ceil(_CFLConditionNumber) + 2;
    vfield.extrapolateVelocityField(validVelocities, extrapolationLayers);

    ParticleMaskGrid maskgrid(_isize, _jsize, _ksize, _dx);
    for (unsigned int i = 0; i < positions->size(); i++) {
        maskgrid.addParticle(positions->at(i));
    }

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
    double currentParticleRadius = 0.5 * _liquidSDFParticleScale * _dx * sqrt(3.0); 
    MarkerParticleLoadData loadData;
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                vmath::vec3 c = Grid3d::GridIndexToCellCenter(i, j, k, _dx);
                if (liquidSDF.trilinearInterpolate(c) > 0.0f) {
                    continue;
                }

                for (int oidx = 0; oidx < 8; oidx++) {
                    vmath::vec3 p = c + particleOffsets[oidx];
                    if (maskgrid.isSubCellSet(p)) {
                        continue;
                    }

                    if (_isJitterSurfaceMarkerParticlesEnabled) {
                        p = _jitterMarkerParticlePosition(p, jitter);
                    }

                    if (liquidSDF.trilinearInterpolate(p) < -currentParticleRadius) {
                        vmath::vec3 v = vfield.evaluateVelocityAtPosition(p);
                        p = p * _domainScale + _domainOffset;
                        MarkerParticle mp(p, v);
                        loadData.particles.push_back(mp);
                    }
                }
            }
        }
    }

    _markerParticleLoadQueue.push_back(loadData);
    _isMarkerParticleLoadPending = true;
}

void FluidSimulation::_loadMarkerParticles(MarkerParticleLoadData &particleData,
                                           MarkerParticleAffineLoadData &affineData,
                                           MarkerParticleAgeLoadData &ageData,
                                           MarkerParticleColorLoadData &colorData,
                                           MarkerParticleSourceIDLoadData &sourceIDData) {

    if (particleData.particles.empty()) {
        return;
    }

    bool loadAffineData = _velocityTransferMethod == VelocityTransferMethod::APIC &&
                          affineData.particles.size() == particleData.particles.size();

    bool loadAgeData = _isSurfaceAgeAttributeEnabled && 
                       ageData.particles.size() == particleData.particles.size();

    bool loadColorData = _isSurfaceSourceColorAttributeEnabled && 
                         colorData.particles.size() == particleData.particles.size();

    bool loadSourceIDData = _isSurfaceSourceIDAttributeEnabled && 
                            sourceIDData.particles.size() == particleData.particles.size();

    _markerParticles.reserve(_markerParticles.size() + particleData.particles.size());

    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    std::vector<vmath::vec3> *affineX = nullptr;
    std::vector<vmath::vec3> *affineY = nullptr;
    std::vector<vmath::vec3> *affineZ = nullptr;
    if (loadAffineData) {
        _markerParticles.getAttributeValues("AFFINEX", affineX);
        _markerParticles.getAttributeValues("AFFINEY", affineY);
        _markerParticles.getAttributeValues("AFFINEZ", affineZ);
    }

    std::vector<float> *age = nullptr;
    if (loadAgeData) {
        _markerParticles.getAttributeValues("AGE", age);
    }

    std::vector<vmath::vec3> *color = nullptr;
    if (loadColorData) {
        _markerParticles.getAttributeValues("COLOR", color);
    }

    std::vector<int> *sourceid = nullptr;
    if (loadSourceIDData) {
        _markerParticles.getAttributeValues("SOURCEID", sourceid);
    }

    AABB bounds(0.0, 0.0, 0.0, _isize * _dx, _jsize * _dx, _ksize * _dx);
    for (size_t i = 0; i < particleData.particles.size(); i++) {
        MarkerParticle mp = particleData.particles[i];
        mp.position = (mp.position - _domainOffset) / _domainScale;
        if (bounds.isPointInside(mp.position)) {
            positions->push_back(mp.position);
            velocities->push_back(mp.velocity);

            if (loadAffineData) {
                MarkerParticleAffine ap = affineData.particles[i];
                affineX->push_back(ap.affineX);
                affineY->push_back(ap.affineY);
                affineZ->push_back(ap.affineZ);
            }

            if (loadAgeData) {
                MarkerParticleAge ap = ageData.particles[i];
                age->push_back(ap.age);
            }

            if (loadColorData) {
                MarkerParticleColor c = colorData.particles[i];
                color->push_back(c.color);
            }

            if (loadSourceIDData) {
                MarkerParticleSourceID sid = sourceIDData.particles[i];
                sourceid->push_back(sid.sourceid);
            }
        }
    }

    _markerParticles.update();
}

void FluidSimulation::_loadDiffuseParticles(DiffuseParticleLoadData &data) {
    _diffuseMaterial.loadDiffuseParticles(data.particles);
}

void FluidSimulation::_loadParticles() {
    bool isAffineDataAvailable = _markerParticleAffineLoadQueue.size() == _markerParticleLoadQueue.size();
    bool isAgeDataAvailable = _markerParticleAgeLoadQueue.size() == _markerParticleLoadQueue.size();
    bool isColorDataAvailable = _markerParticleColorLoadQueue.size() == _markerParticleLoadQueue.size();
    bool isSourceIDDataAvailable = _markerParticleSourceIDLoadQueue.size() == _markerParticleLoadQueue.size();

    MarkerParticleAffineLoadData emptyAffineData;
    MarkerParticleAgeLoadData emptyAgeData;
    MarkerParticleColorLoadData emptyColorData;
    MarkerParticleSourceIDLoadData emptySourceIDData;
    for (size_t i = 0; i < _markerParticleLoadQueue.size(); i++) {
        MarkerParticleAffineLoadData affineData = isAffineDataAvailable ? _markerParticleAffineLoadQueue[i] : emptyAffineData;
        MarkerParticleAgeLoadData ageData = isAgeDataAvailable ? _markerParticleAgeLoadQueue[i] : emptyAgeData;
        MarkerParticleColorLoadData colorData = isColorDataAvailable ? _markerParticleColorLoadQueue[i] : emptyColorData;
        MarkerParticleSourceIDLoadData sourceIDData = isSourceIDDataAvailable ? _markerParticleSourceIDLoadQueue[i] : emptySourceIDData;
        _loadMarkerParticles(_markerParticleLoadQueue[i], affineData, ageData, colorData, sourceIDData);
    }
    _markerParticleLoadQueue.clear();
    _markerParticleAffineLoadQueue.clear();
    _markerParticleAgeLoadQueue.clear();
    _markerParticleColorLoadQueue.clear();
    _markerParticleSourceIDLoadQueue.clear();
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

        _tempSolidSDF.enableVelocityData();
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

        _tempSolidSDF.enableVelocityData();
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

    double radius = _liquidSDFParticleRadius;
    if (_isSurfaceTensionEnabled && _isSmoothSurfaceTensionKernelEnabled) {
        radius = _liquidSDFSurfaceTensionParticleScale * _liquidSDFParticleRadius;
    }

    _liquidSDF.calculateSignedDistanceField(_markerParticles, radius);

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
        double radius = _liquidSDFParticleRadius;
        if (_isSurfaceTensionEnabled && _isSmoothSurfaceTensionKernelEnabled) {
            radius = _liquidSDFSurfaceTensionParticleScale * _liquidSDFParticleRadius;
        }

        VelocityAdvectorParameters params;
        params.particles = &_markerParticles;
        params.vfield = &_MACVelocity;
        params.validVelocities = &_validVelocities;
        params.particleRadius = radius;

        if (_velocityTransferMethod == VelocityTransferMethod::FLIP) {
            params.velocityTransferMethod = VelocityAdvectorTransferMethod::FLIP;
        } else if (_velocityTransferMethod == VelocityTransferMethod::APIC) {
            params.velocityTransferMethod = VelocityAdvectorTransferMethod::APIC;
        }
        
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

        float frameProgress = _getFrameInterpolation();
        int numSubsteps = inflow->getSubstepEmissions();

        if (numSubsteps == 0) {
            numSubsteps = 1;
        }

        float substepFactor = (_currentFrameTimeStep / _currentFrameDeltaTime) / (float)numSubsteps;

        for (int subidx = 0; subidx < numSubsteps; subidx++) {
            float frameInterpolation = frameProgress + (float)subidx * substepFactor;
            inflow->setFrame(_currentFrame, frameInterpolation);
            inflow->update(_currentFrameDeltaTime);
            
            for (int k = 0; k < _ksize; k++) {
                for (int j = 0; j < _jsize; j++) {
                    for (int i = 0; i < _isize + 1; i++) {
                        if (!_validVelocities.validU(i, j, k)) {
                            continue;
                        }
                        vmath::vec3 p = Grid3d::FaceIndexToPositionU(i, j, k, _dx);
                        if (inflow->trilinearInterpolate(p) < 0.0f) {
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
                        if (inflow->trilinearInterpolate(p) < 0.0f) {
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
                        if (inflow->trilinearInterpolate(p) < 0.0f) {
                            ex.validW.set(i, j, k, true);
                        }
                    }
                }
            }
        }
    }
}

void FluidSimulation::_updateForceFieldGrid(double dt) {
    if (!_isAdaptiveForceFieldTimeSteppingEnabled && _currentFrameTimeStepNumber != 0) {
        return;
    }

    float frameProgress = _getFrameInterpolation();
    _forceFieldGrid.setGravityVector(_getConstantBodyForce());
    _forceFieldGrid.update(dt, frameProgress);
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

void FluidSimulation::_applyForceFieldGridForces(ValidVelocityComponentGrid &ex, double dt) {
    int U = 0; int V = 1; int W = 2;
    _applyForceFieldGridForcesMT(ex, dt, U);
    _applyForceFieldGridForcesMT(ex, dt, V);
    _applyForceFieldGridForcesMT(ex, dt, W);

}

void FluidSimulation::_applyForceFieldGridForcesMT(ValidVelocityComponentGrid &ex, double dt, int dir) {

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
        threads[i] = std::thread(&FluidSimulation::_applyForceFieldGridForcesThread, this,
                                 intervals[i], intervals[i + 1], &ex, dt, dir);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void FluidSimulation::_applyForceFieldGridForcesThread(int startidx, int endidx, 
                                                       ValidVelocityComponentGrid *ex, double dt, int dir) {
    int U = 0; int V = 1; int W = 2;

    if (dir == U) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize + 1, _jsize);
            if (!ex->validU(g)) {
                vmath::vec3 p = Grid3d::FaceIndexToPositionU(g, _dx);
                float xvel = _forceFieldGrid.evaluateForceAtPositionU(p);
                _MACVelocity.addU(g, xvel * dt);
            }
        }

    } else if (dir == V) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize + 1);
            if (!ex->validV(g)) {
                vmath::vec3 p = Grid3d::FaceIndexToPositionV(g, _dx);
                float yvel = _forceFieldGrid.evaluateForceAtPositionV(p);
                _MACVelocity.addV(g, yvel * dt);
            }
        }

    } else if (dir == W) {

        for (int idx = startidx; idx < endidx; idx++) {
            GridIndex g = Grid3d::getUnflattenedIndex(idx, _isize, _jsize);
            if (!ex->validW(g)) {
                vmath::vec3 p = Grid3d::FaceIndexToPositionW(g, _dx);
                float zvel = _forceFieldGrid.evaluateForceAtPositionW(p);
                _MACVelocity.addW(g, zvel * dt);
            }
        }

    }
}

void FluidSimulation::_applyBodyForcesToVelocityField(double dt) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Apply Force Fields");

    StopWatch t;
    t.start();

    ValidVelocityComponentGrid ex(_isize, _jsize, _ksize);
    _getInflowConstrainedVelocityComponents(ex);

    if (_isForceFieldsEnabled) {
        _updateForceFieldGrid(dt);
        _applyForceFieldGridForces(ex, dt);
    } else {
        _applyConstantBodyForces(ex, dt);
    }

    t.stop();
    _timingData.applyBodyForcesToVelocityField += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Apply Force Fields");
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
    params.errorTolerance = _viscositySolverErrorTolerance;

    _viscositySolver = ViscositySolver();
    _viscositySolver.applyViscosityToVelocityField(params);
    _viscositySolverStatus = _viscositySolver.getSolverStatus();

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

    params.bodyForce = _getConstantBodyForce();
    if (_isForceFieldsEnabled) {
        params.forceFieldGrid = &_forceFieldGrid;
        params.isForceFieldGridSet = true;
    }

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

    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

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
        positions->push_back(p);
        velocities->push_back(v);
    }

    _markerParticles.update();

    t.stop();

    _timingData.updateSheetSeeding += t.getTime();
    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Sheet Seeding");
}

/********************************************************************************
    #. Update MarkerParticle Velocities
********************************************************************************/

void FluidSimulation::_getIndicesAndGradientWeights(vmath::vec3 p, GridIndex indices[8], vmath::vec3 weights[8], int dir) {
    int U = 0; int V = 1; int W = 2;

    vmath::vec3 offset;
    float h = 0.5f * _dx;
    if (dir == U) {
        offset = vmath::vec3(0.0f, h, h);
    } else if (dir == V) {
        offset = vmath::vec3(h, 0.0f, h);
    } else if (dir == W) {
        offset = vmath::vec3(h, h, 0.0f);
    }

    p -= offset;
    GridIndex g = Grid3d::positionToGridIndex(p, _dx);
    vmath::vec3 gpos = Grid3d::GridIndexToPosition(g, _dx);
    vmath::vec3 ipos = (p - gpos) / _dx;

    indices[0] = GridIndex(g.i,     g.j,     g.k);
    indices[1] = GridIndex(g.i + 1, g.j,     g.k);
    indices[2] = GridIndex(g.i,     g.j + 1, g.k);
    indices[3] = GridIndex(g.i + 1, g.j + 1, g.k);
    indices[4] = GridIndex(g.i,     g.j,     g.k + 1);
    indices[5] = GridIndex(g.i + 1, g.j,     g.k + 1);
    indices[6] = GridIndex(g.i,     g.j + 1, g.k + 1);
    indices[7] = GridIndex(g.i + 1, g.j + 1, g.k + 1);

    float invdx = 1.0f / _dx;
    weights[0] = vmath::vec3(
        -invdx * (1.0f - ipos.y) * (1.0f - ipos.z),
        -invdx * (1.0f - ipos.x) * (1.0f - ipos.z),
        -invdx * (1.0f - ipos.x) * (1.0f - ipos.y));
    weights[1] = vmath::vec3(
        invdx * (1.0f - ipos.y) * (1.0f - ipos.z),
        ipos.x * (-invdx) * (1.0f - ipos.z),
        ipos.x * (1.0f - ipos.y) * (-invdx));
    weights[2] = vmath::vec3(
        (-invdx) * ipos.y * (1.0f - ipos.z),
        (1.0f - ipos.x) * invdx * (1.0f - ipos.z),
        (1.0f - ipos.x) * ipos.y * (-invdx));
    weights[3] = vmath::vec3(
        invdx * ipos.y * (1.0f - ipos.z),
        ipos.x * invdx * (1.0f - ipos.z),
        ipos.x * ipos.y * (-invdx));
    weights[4] = vmath::vec3(
        (-invdx) * (1.0f - ipos.y) * ipos.z,
        (1.0f - ipos.x) * (-invdx) * ipos.z,
        (1.0f - ipos.x) * (1.0f - ipos.y) * invdx);
    weights[5] = vmath::vec3(
        invdx * (1.0f - ipos.y) * ipos.z,
        ipos.x * (-invdx) * ipos.z,
        ipos.x * (1.0f - ipos.y) * invdx);
    weights[6] = vmath::vec3(
        (-invdx) * ipos.y * ipos.z,
        (1.0f - ipos.x) * invdx * ipos.z,
        (1.0f - ipos.x) * ipos.y * invdx);
    weights[7] = vmath::vec3(
        invdx * ipos.y * ipos.z,
        ipos.x * invdx * ipos.z,
        ipos.x * ipos.y * invdx);
}

void FluidSimulation::_updatePICFLIPMarkerParticleVelocitiesThread(int startidx, int endidx) {
    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 pos = positions->at(i);
        vmath::vec3 vel = velocities->at(i);
        vmath::vec3 vPIC = _MACVelocity.evaluateVelocityAtPositionLinear(pos);
        vmath::vec3 vFLIP = vel + vPIC - _savedVelocityField.evaluateVelocityAtPositionLinear(pos);
        vmath::vec3 v = (float)_ratioPICFLIP * vPIC + (float)(1 - _ratioPICFLIP) * vFLIP;
        velocities->at(i) = v;
    }
}

/*
    The APIC (Affine Particle-In-Cell) velocity transfer method was adapted from
    Doyub Kim's 'Fluid Engine Dev' repository:
        https://github.com/doyubkim/fluid-engine-dev
*/
void FluidSimulation::_updatePICAPICMarkerParticleVelocitiesThread(int startidx, int endidx) {
    std::vector<vmath::vec3> *positions, *velocities;
    std::vector<vmath::vec3> *affineValuesX, *affineValuesY, *affineValuesZ;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);
    _markerParticles.getAttributeValues("AFFINEX", affineValuesX);
    _markerParticles.getAttributeValues("AFFINEY", affineValuesY);
    _markerParticles.getAttributeValues("AFFINEZ", affineValuesZ);

    int U = 0; int V = 1; int W = 2; 

    GridIndex indices[8];
    vmath::vec3 weights[8];
    for (int i = startidx; i < endidx; i++) {
        vmath::vec3 pos = positions->at(i);

        vmath::vec3 affineX;
        vmath::vec3 affineY;
        vmath::vec3 affineZ;
        
        _getIndicesAndGradientWeights(pos, indices, weights, U);
        for (int gidx = 0; gidx < 8; gidx++) {
            GridIndex g = indices[gidx];
            if (!_MACVelocity.isIndexInRangeU(g)) {
                continue;
            }
            affineX += weights[gidx] * _MACVelocity.U(g);
        }

        _getIndicesAndGradientWeights(pos, indices, weights, V);
        for (int gidx = 0; gidx < 8; gidx++) {
            GridIndex g = indices[gidx];
            if (!_MACVelocity.isIndexInRangeV(g)) {
                continue;
            }
            affineY += weights[gidx] * _MACVelocity.V(g);
        }

        _getIndicesAndGradientWeights(pos, indices, weights, W);
        for (int gidx = 0; gidx < 8; gidx++) {
            GridIndex g = indices[gidx];
            if (!_MACVelocity.isIndexInRangeW(g)) {
                continue;
            }
            affineZ += weights[gidx] * _MACVelocity.W(g);
        }

        velocities->at(i) = _MACVelocity.evaluateVelocityAtPositionLinear(pos);
        affineValuesX->at(i) = affineX;
        affineValuesY->at(i) = affineY;
        affineValuesZ->at(i) = affineZ;
    }
}

void FluidSimulation::_updateMarkerParticleVelocitiesThread() {
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, _markerParticles.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, _markerParticles.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        if (_velocityTransferMethod == VelocityTransferMethod::FLIP) {
            threads[i] = std::thread(&FluidSimulation::_updatePICFLIPMarkerParticleVelocitiesThread, this,
                                     intervals[i], intervals[i + 1]);
        } else if (_velocityTransferMethod == VelocityTransferMethod::APIC) {
            threads[i] = std::thread(&FluidSimulation::_updatePICAPICMarkerParticleVelocitiesThread, this,
                                     intervals[i], intervals[i + 1]);
        }
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

void FluidSimulation::_constrainMarkerParticleVelocities(MeshFluidSource *inflow) {
    float frameProgress = _getFrameInterpolation();
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

        std::vector<vmath::vec3> *positions, *velocities;
        _markerParticles.getAttributeValues("POSITION", positions);
        _markerParticles.getAttributeValues("VELOCITY", velocities);

        MeshLevelSet *inflowSDF = inflow->getMeshLevelSet();
        vmath::vec3 v = inflow->getVelocity();
        RigidBodyVelocity rv = inflow->getRigidBodyVelocity(_currentFrameDeltaTime);
        VelocityFieldData *vdata = inflow->getVelocityFieldData();
        for (size_t i = 0; i < positions->size(); i++) {
            vmath::vec3 p = positions->at(i);
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (!isInflowCell(g)) {
                continue;
            }

            if (inflowSDF->trilinearInterpolate(p) > 0.0f) {
                continue;
            }

            if (inflow->isAppendObjectVelocityEnabled()) {
                if (inflow->isRigidBody()) {
                    vmath::vec3 tv = vmath::cross(rv.angular * rv.axis, p - rv.centroid);
                    velocities->at(i) = v + rv.linear + tv;
                } else {
                    vmath::vec3 datap = p - vdata->offset;
                    vmath::vec3 fv = vdata->vfield.evaluateVelocityAtPositionLinear(datap);
                    velocities->at(i) = v + fv;
                }
            } else {
                velocities->at(i) = v;
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

    _updateMarkerParticleVelocitiesThread();
    _constrainMarkerParticleVelocities();

    t.stop();
    _timingData.updateMarkerParticleVelocities += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Marker Particle Velocities");
}

/********************************************************************************
    #. Update Marker Particle Attributes
********************************************************************************/

void FluidSimulation::_updateMarkerParticleVorticityAttributeGrid() {
    _MACVelocity.generateCurlAtCellCenter(_vorticityAttributeGrid);
}

void FluidSimulation::_updateMarkerParticleAgeAttributeGrid(double dt) {
    _ageAttributeGrid.fill(0.0f);
    _ageAttributeCountGrid.fill(0);
    _ageAttributeValidGrid.fill(false);

    std::vector<vmath::vec3> *positions;
    std::vector<float> *ages;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("AGE", ages);
    for (size_t i = 0; i < positions->size(); i++) {
        vmath::vec3 p = positions->at(i);
        float age = ages->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        _ageAttributeGrid.add(g, age);
        _ageAttributeCountGrid.add(g, 1);
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                int count = _ageAttributeCountGrid(i, j, k);
                if (count > 1) {
                   _ageAttributeGrid.set(i, j, k, _ageAttributeGrid(i, j, k) / count);
                   _ageAttributeValidGrid.set(i, j, k, true);
                }
            }
        }
    }

    GridUtils::extrapolateGrid(&_ageAttributeGrid, &_ageAttributeValidGrid, _CFLConditionNumber);
}

void FluidSimulation::_updateMarkerParticleColorAttributeGrid() {
    _colorAttributeGridR.fill(0.0f);
    _colorAttributeGridG.fill(0.0f);
    _colorAttributeGridB.fill(0.0f);
    _colorAttributeCountGrid.fill(0);
    _colorAttributeValidGrid.fill(false);

    std::vector<vmath::vec3> *positions;
    std::vector<vmath::vec3> *colors;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("COLOR", colors);
    for (size_t i = 0; i < positions->size(); i++) {
        vmath::vec3 p = positions->at(i);
        vmath::vec3 color = colors->at(i);
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        _colorAttributeGridR.add(g, color.x);
        _colorAttributeGridG.add(g, color.y);
        _colorAttributeGridB.add(g, color.z);
        _colorAttributeCountGrid.add(g, 1);
    }

    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                int count = _colorAttributeCountGrid(i, j, k);
                if (count > 1) {
                    float rval = _clamp(_colorAttributeGridR(i, j, k) / count, 0.0f, 1.0f);
                    float gval = _clamp(_colorAttributeGridG(i, j, k) / count, 0.0f, 1.0f);
                    float bval = _clamp(_colorAttributeGridB(i, j, k) / count, 0.0f, 1.0f);

                   _colorAttributeGridR.set(i, j, k, rval);
                   _colorAttributeGridG.set(i, j, k, gval);
                   _colorAttributeGridB.set(i, j, k, bval);
                   _colorAttributeValidGrid.set(i, j, k, true);
                }
            }
        }
    }

    GridUtils::extrapolateGrid(&_colorAttributeGridR, &_colorAttributeValidGrid, 1.5 * _CFLConditionNumber);
    GridUtils::extrapolateGrid(&_colorAttributeGridG, &_colorAttributeValidGrid, 1.5 * _CFLConditionNumber);
    GridUtils::extrapolateGrid(&_colorAttributeGridB, &_colorAttributeValidGrid, 1.5 * _CFLConditionNumber);
}

void FluidSimulation::_updateMarkerParticleVorticityAttribute() {
    if (!_isSurfaceVorticityAttributeEnabled) {
        return;
    }

    if (_currentFrameTimeStepNumber == 0) {
        _updateMarkerParticleVorticityAttributeGrid();
    }
}

void FluidSimulation::_updateMarkerParticleAgeAttribute(double dt) {
    if (!_isSurfaceAgeAttributeEnabled) {
        return;
    }

    if (_currentFrameTimeStepNumber == 0) {
        _updateMarkerParticleAgeAttributeGrid(dt);
    }

    std::vector<float> *ages;
    _markerParticles.getAttributeValues("AGE", ages);
    for (size_t i = 0; i < ages->size(); i++) {
        ages->at(i) += dt;
    }
}

void FluidSimulation::_updateMarkerParticleColorAttribute() {
    if (!_isSurfaceSourceColorAttributeEnabled) {
        return;
    }

    if (_currentFrameTimeStepNumber == 0) {
        _updateMarkerParticleColorAttributeGrid();
    }
}

void FluidSimulation::_updateMarkerParticleAttributes(double dt) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Update Marker Particle Attributes");

    StopWatch t;
    t.start();

    _updateMarkerParticleVorticityAttribute();
    _updateMarkerParticleAgeAttribute(dt);
    _updateMarkerParticleColorAttribute();

    t.stop();
    _timingData.updateMarkerParticleVelocities += t.getTime();

    _logfile.logString(_logfile.getTime() + " COMPLETE    Update Marker Particle Attributes");
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
    std::vector<vmath::vec3> *velocities;
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    double speedLimitStep = _CFLConditionNumber * _dx / dt;
    std::vector<int> speedLimitCounts(_maxFrameTimeSteps, 0);
    for (unsigned int i = 0; i < velocities->size(); i++) {
        double speed = (double)velocities->at(i).length();
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
        maxspeed = std::max(i + _minTimeStepIncreaseForRemoval, _maxFrameTimeSteps) * speedLimitStep;
    }

    return maxspeed;
}

void FluidSimulation::_removeMarkerParticles(double dt) {
    Array3d<int> countGrid = Array3d<int>(_isize, _jsize, _ksize, 0);

    float maxspeed = _getMarkerParticleSpeedLimit(dt);
    double maxspeedsq = maxspeed * maxspeed;

    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    std::vector<bool> isRemoved;
    _solidSDF.trilinearInterpolateSolidPoints(*positions, isRemoved);
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        if (isRemoved[i]) {
            continue;
        }

        vmath::vec3 position = positions->at(i);
        vmath::vec3 velocity = velocities->at(i);

        GridIndex g = Grid3d::positionToGridIndex(position, _dx);
        if (countGrid(g) >= _maxMarkerParticlesPerCell) {
            isRemoved[i] = true;
            continue;
        }
        countGrid.add(g, 1);

        if (_isExtremeVelocityRemovalEnabled && 
                vmath::dot(velocity, velocity) > maxspeedsq) {
            isRemoved[i] = true;
            continue;
        }
    }

    _markerParticles.removeParticles(isRemoved);
}

void FluidSimulation::_advanceMarkerParticles(double dt) {
    _logfile.logString(_logfile.getTime() + " BEGIN       Advect Marker Particles");

    StopWatch t;
    t.start();

    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);
    
    std::vector<vmath::vec3> positionsCopy = *positions;

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, positionsCopy.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<vmath::vec3> output(positionsCopy.size());
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, positionsCopy.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_advanceMarkerParticlesThread, this,
                                 dt, intervals[i], intervals[i + 1], &positionsCopy, &output);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    for (size_t i = 0; i < _markerParticles.size(); i++) {
        float distanceTravelled = vmath::length(positions->at(i) - output[i]);
        if (distanceTravelled < 1e-6) {
            // In the rare case that a particle did not move, it could be
            // that this particle is stuck. Velocity should be set to 0.0
            // which helps the particle 'reset' and become unstuck.
            //velocities->at(i) = vmath::vec3();
        }
        positions->at(i) = output[i];
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
                                        vmath::vec3 sdfoffset,
                                        MarkerParticleAttributes attributes,
                                        ParticleMaskGrid &maskgrid) {

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, cells.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<std::vector<vmath::vec3> > particleVectors(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, cells.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_addNewFluidCellsThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &cells, &meshSDF, sdfoffset, 
                                 &(particleVectors[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    std::vector<MarkerParticle> newParticles;
    for (size_t vidx = 0; vidx < particleVectors.size(); vidx++) {
        for (size_t i = 0; i < particleVectors[vidx].size(); i++) {
            vmath::vec3 p = particleVectors[vidx][i];
            if (maskgrid.isSubCellSet(p)) {
                continue;
            }

            newParticles.push_back(MarkerParticle(p, velocity));
            maskgrid.addParticle(p);
        }
    }

    _addMarkerParticles(newParticles, attributes);
}

void FluidSimulation::_addNewFluidCells(std::vector<GridIndex> &cells, 
                                        vmath::vec3 velocity,
                                        RigidBodyVelocity rvelocity,
                                        MeshLevelSet &meshSDF,
                                        vmath::vec3 sdfoffset,
                                        MarkerParticleAttributes attributes,
                                        ParticleMaskGrid &maskgrid) {

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, cells.size());
    std::vector<std::thread> threads(numthreads);
    std::vector<std::vector<vmath::vec3> > particleVectors(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, cells.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&FluidSimulation::_addNewFluidCellsThread, this,
                                 intervals[i], intervals[i + 1], 
                                 &cells, &meshSDF, sdfoffset, 
                                 &(particleVectors[i]));
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }

    std::vector<MarkerParticle> newParticles;
    for (size_t vidx = 0; vidx < particleVectors.size(); vidx++) {
        for (size_t i = 0; i < particleVectors[vidx].size(); i++) {
            vmath::vec3 p = particleVectors[vidx][i];
            if (maskgrid.isSubCellSet(p)) {
                continue;
            }

            vmath::vec3 rotv = vmath::cross(rvelocity.angular * rvelocity.axis, p - rvelocity.centroid);
            vmath::vec3 totv = velocity + rvelocity.linear + rotv;
            newParticles.push_back(MarkerParticle(p, totv));
            maskgrid.addParticle(p);
        }
    }

    _addMarkerParticles(newParticles, attributes);
}

void FluidSimulation::_addNewFluidCells(std::vector<GridIndex> &cells, 
                                        vmath::vec3 velocity,
                                        VelocityFieldData *vdata,
                                        MeshLevelSet &meshSDF,
                                        vmath::vec3 sdfoffset,
                                        MarkerParticleAttributes attributes,
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
    std::vector<MarkerParticle> newParticles;
    for (size_t i = 0; i < cells.size(); i++) {
        GridIndex g = cells[i];
        vmath::vec3 c = Grid3d::GridIndexToCellCenter(g, _dx);

        for (unsigned int oidx = 0; oidx < 8; oidx++) {
            vmath::vec3 p = c + particleOffsets[oidx];
            if (maskgrid.isSubCellSet(p)) {
                continue;
            }

            double d = meshSDF.trilinearInterpolate(p - sdfoffset);
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

                newParticles.push_back(MarkerParticle(p, v));
                maskgrid.addParticle(p);
            }
        }
    }

    _addMarkerParticles(newParticles, attributes);
}

void FluidSimulation::_addNewFluidCellsAABB(AABB bbox, 
                                            vmath::vec3 velocity,
                                            MarkerParticleAttributes attributes,
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

    vmath::vec3 p1 = bbox.getMinPoint();
    vmath::vec3 p2 = bbox.getMaxPoint();
    GridIndex g1 = Grid3d::positionToGridIndex(p1, _dx);
    GridIndex g2 = Grid3d::positionToGridIndex(p2, _dx);

    g1.i = std::max(g1.i, 1);
    g1.j = std::max(g1.j, 1);
    g1.k = std::max(g1.k, 1);
    g2.i = std::min(g2.i, _isize - 2);
    g2.j = std::min(g2.j, _jsize - 2);
    g2.k = std::min(g2.k, _ksize - 2);

    std::vector<MarkerParticle> newParticles;
    for (int k = g1.k; k <= g2.k; k++) {
        for (int j = g1.j; j <= g2.j; j++) {
            for (int i = g1.i; i <= g2.i; i++) {
                GridIndex g(i, j, k);
                vmath::vec3 c = Grid3d::GridIndexToCellCenter(g, _dx);

                bool isSurfaceParticle = i == g1.i || j == g1.j || k == g1.k || 
                                         i == g2.i || j == g2.j || k == g2.k;
                for (unsigned int oidx = 0; oidx < 8; oidx++) {
                    vmath::vec3 p = c + particleOffsets[oidx];
                    if (maskgrid.isSubCellSet(p)) {
                        continue;
                    }

                    if (_isJitterSurfaceMarkerParticlesEnabled || !isSurfaceParticle) {
                        p = _jitterMarkerParticlePosition(p, jitter);
                    }

                    if (_solidSDF.trilinearInterpolate(p) > 0) {
                        newParticles.push_back(MarkerParticle(p, velocity));
                        maskgrid.addParticle(p);
                    }
                }

            }
        }
    }

    _addMarkerParticles(newParticles, attributes);
}

void FluidSimulation::_addNewFluidCellsThread(int startidx, int endidx,
                                              std::vector<GridIndex> *cells, 
                                              MeshLevelSet *meshSDF,
                                              vmath::vec3 sdfoffset,
                                              std::vector<vmath::vec3> *particles) {

    double q = 0.25 * _dx;
    double jitter = _getMarkerParticleJitter();
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

    for (int i = startidx; i < endidx; i++) {
        GridIndex g = cells->at(i);
        vmath::vec3 c = Grid3d::GridIndexToCellCenter(g, _dx);

        for (int oidx = 0; oidx < 8; oidx++) {
            vmath::vec3 p = c + particleOffsets[oidx];

            double d = meshSDF->trilinearInterpolate(p - sdfoffset);
            if (d > 0) {
                continue;
            }

            if (_isJitterSurfaceMarkerParticlesEnabled || d < -_dx) {
                p = _jitterMarkerParticlePosition(p, jitter);
            }

            if (_solidSDF.trilinearInterpolate(p) > 0) {
                particles->push_back(p);
            }
        }
    }
}

void FluidSimulation::_updateInflowMeshFluidSource(MeshFluidSource *source,
                                                   ParticleMaskGrid &maskgrid) {
    if (!source->isEnabled()) {
        return;
    }

    float frameProgress = _getFrameInterpolation();
    int numSubsteps = source->getSubstepEmissions();

    if (numSubsteps == 0) {
        numSubsteps = 1;
        if (_currentFrameTimeStepNumber != 0) {
            return;
        }
    }

    float substepFactor = (_currentFrameTimeStep / _currentFrameDeltaTime) / (float)numSubsteps;

    MarkerParticleAttributes attributes;
    attributes.sourceID = source->getSourceID();
    attributes.sourceColor = source->getSourceColor();

    for (int i = 0; i < numSubsteps; i++) {
        float frameInterpolation = frameProgress + (float)i * substepFactor;
        source->setFrame(_currentFrame, frameInterpolation);
        source->update(_currentFrameDeltaTime);

        std::vector<GridIndex> sourceCells;
        source->getCells(frameInterpolation, sourceCells);

        MeshLevelSet *sourceSDF = source->getMeshLevelSet();
        vmath::vec3 sourceSDFOffset = source->getMeshLevelSetOffset(); 
        vmath::vec3 velocity = source->getVelocity();

        if (source->isAppendObjectVelocityEnabled()) {
            if (source->isRigidBody()) {
                RigidBodyVelocity rv = source->getRigidBodyVelocity(_currentFrameDeltaTime);
                _addNewFluidCells(sourceCells, velocity, rv, *sourceSDF, sourceSDFOffset, attributes,  maskgrid);
            } else {
                VelocityFieldData *vdata = source->getVelocityFieldData();
                _addNewFluidCells(sourceCells, velocity, vdata, *sourceSDF, sourceSDFOffset, attributes, maskgrid);
            }
        } else {
            _addNewFluidCells(sourceCells, velocity, *sourceSDF, sourceSDFOffset, attributes, maskgrid);
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

    float frameProgress = _getFrameInterpolation();

    source->setFrame(_currentFrame, frameProgress);
    source->update(_currentFrameDeltaTime);

    std::vector<GridIndex> sourceCells;
    source->getCells(frameProgress, sourceCells);
    MeshLevelSet *sourceSDF = source->getMeshLevelSet();
    vmath::vec3 offset = source->getMeshLevelSetOffset();

    Array3d<bool> isOutflowCell(_isize, _jsize, _ksize);
    if (source->isOutflowInversed()) {
        isOutflowCell.fill(true);
        isOutflowCell.set(sourceCells, false);
    } else {
        isOutflowCell.fill(false);
        isOutflowCell.set(sourceCells, true);
    }

    std::vector<vmath::vec3> *positions;
    _markerParticles.getAttributeValues("POSITION", positions);

    if (source->isFluidOutflowEnabled()) {
        std::vector<bool> isRemoved(_markerParticles.size(), false);
        for (size_t i = 0; i < _markerParticles.size(); i++) {
            vmath::vec3 p = positions->at(i);
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (isOutflowCell(g)) {
                float d = sourceSDF->trilinearInterpolate(p - offset);
                if (source->isOutflowInversed() && d >= 0.0f) {
                    isRemoved[i] = true;
                } else if (!source->isOutflowInversed() && d < 0.0f) {
                    isRemoved[i] = true;
                }
            }
        }
        _markerParticles.removeParticles(isRemoved);
    }
    
    if (source->isDiffuseOutflowEnabled()) {
        std::vector<vmath::vec3> *positions;
        ParticleSystem* dps = _diffuseMaterial.getDiffuseParticles();
        dps->getAttributeValues("POSITION", positions);

        std::vector<bool> isRemoved(dps->size(), false);
        for (size_t i = 0; i < dps->size(); i++) {
            vmath::vec3 p = positions->at(i);
            GridIndex g = Grid3d::positionToGridIndex(p, _dx);
            if (!isOutflowCell.isIndexInRange(g)) {
                continue;
            }

            if (isOutflowCell(g)) {
                float d = sourceSDF->trilinearInterpolate(p - offset);
                if (source->isOutflowInversed() && d >= 0.0f) {
                    isRemoved[i] = true;
                } else if (!source->isOutflowInversed() && d < 0.0f) {
                    isRemoved[i] = true;
                }
            }
        }
        dps->removeParticles(isRemoved);
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

    std::vector<vmath::vec3> *positions;
    _markerParticles.getAttributeValues("POSITION", positions);

    ParticleMaskGrid maskgrid(_isize, _jsize, _ksize, _dx);
    for (unsigned int i = 0; i < _markerParticles.size(); i++) {
        maskgrid.addParticle(positions->at(i));
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

    std::vector<vmath::vec3> *positions;
    _markerParticles.getAttributeValues("POSITION", positions);

    ParticleMaskGrid maskgrid(_isize, _jsize, _ksize, _dx);
    for (unsigned int i = 0; i < positions->size(); i++) {
        maskgrid.addParticle(positions->at(i));
    }

    MeshLevelSet meshSDF(_isize, _jsize, _ksize, _dx);
    meshSDF.disableVelocityData();

    std::vector<GridIndex> objectCells;
    for (unsigned int i = 0; i < _addedFluidMeshObjectQueue.size(); i++) {
        MeshObject object = _addedFluidMeshObjectQueue[i].object;
        vmath::vec3 velocity = _addedFluidMeshObjectQueue[i].velocity;

        MarkerParticleAttributes attributes;
        attributes.sourceID = object.getSourceID();
        attributes.sourceColor = object.getSourceColor();

        bool isAABB = object.isGeometryAABB();
        if (isAABB && !object.isAnimated()) {
            // Optimization for static AABB shaped geometry
            TriangleMesh m = object.getMesh();
            AABB bbox(m.vertices);
            _addNewFluidCellsAABB(bbox, velocity, attributes, maskgrid);
        } else {
            objectCells.clear();
            object.getCells(objectCells);

            TriangleMesh mesh = object.getMesh();
            meshSDF.reset();
            meshSDF.fastCalculateSignedDistanceField(mesh, _liquidLevelSetExactBand);
            vmath::vec3 offset(0.0f, 0.0f, 0.0f);

            if (object.isAppendObjectVelocityEnabled()) {
                RigidBodyVelocity rv = object.getRigidBodyVelocity(_currentFrameDeltaTime);
                _addNewFluidCells(objectCells, velocity, rv, meshSDF, offset, attributes, maskgrid);
            } else {
                _addNewFluidCells(objectCells, velocity, meshSDF, offset, attributes, maskgrid);
            }
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

    std::vector<vmath::vec3> *positions;
    _markerParticles.getAttributeValues("POSITION", positions);

    if (count == 0 && !_markerParticles.empty()) {
        Array3d<bool> isFluidCell(_isize, _jsize, _ksize, false);
        for (unsigned int i = 0; i < positions->size(); i++) {
            GridIndex g = Grid3d::positionToGridIndex(positions->at(i), _dx);
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

void FluidSimulation::_getForceFieldDebugFileData(std::vector<ForceFieldDebugNode> &debugNodes, 
                                                  std::vector<char> &data) {

    std::vector<float> values;
    for (size_t i = 0; i < debugNodes.size(); i++) {
        values.push_back(debugNodes[i].x);
        values.push_back(debugNodes[i].y);
        values.push_back(debugNodes[i].z);
        values.push_back(debugNodes[i].strength);
    }

    int numVertices = (int)debugNodes.size();
    int vertexDataSize = 4 * numVertices * sizeof(float);
    int dataSize = sizeof(int) + vertexDataSize;

    data.clear();
    data.resize(dataSize);
    data.shrink_to_fit();

    int byteOffset = 0;
    std::memcpy(data.data() + byteOffset, &numVertices, sizeof(int));
    byteOffset += sizeof(int);

    std::memcpy(data.data() + byteOffset, (char *)values.data(), vertexDataSize);
    byteOffset += vertexDataSize;
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
        if (!validCells.isIndexInRange(g) || !validCells(g)) {
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
                float d = std::max(bbox.getSignedDistance(p), 0.0f);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // +X side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = gmax.i; i <= gmax.i + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = std::max(bbox.getSignedDistance(p), 0.0f);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // -Y side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = gmin.j; j <= gmin.j + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = std::max(bbox.getSignedDistance(p), 0.0f);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // +Y side
    for (int k = 0; k < _ksize + 1; k++) {
        for (int j = gmax.j; j <= gmax.j + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = std::max(bbox.getSignedDistance(p), 0.0f);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // -Z side
    for (int k = gmin.k; k <= gmin.k + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = std::max(bbox.getSignedDistance(p), 0.0f);
                sdf->set(i, j, k, d);
            }   
        }
    }

    // +Z side
    for (int k = gmax.k; k <= gmax.k + 1; k++) {
        for (int j = 0; j < _jsize + 1; j++) {
            for (int i = 0; i < _isize + 1; i++) {
                vmath::vec3 p = Grid3d::GridIndexToPosition(i, j, k, _dx);
                float d = std::max(bbox.getSignedDistance(p), 0.0f);
                sdf->set(i, j, k, d);
            }   
        }
    }
}

void FluidSimulation::_generateOutputSurface(TriangleMesh &surface, TriangleMesh &preview,
                                               std::vector<vmath::vec3> *particles,
                                               MeshLevelSet *solidSDF) {
    
    _applyMeshingVolumeToSDF(solidSDF);
    _filterParticlesOutsideMeshingVolume(particles);

    if (_markerParticles.empty()) {
        surface = TriangleMesh();
        preview = TriangleMesh();
        return;
    }

    if (_isObstacleMeshingOffsetEnabled) {
        float eps = 1e-9;
        float offset = (float)(_obstacleMeshingOffset * _dx);
        if (std::abs(offset) > eps) {
            // Values near boundary are unchanged so that the mesh is generated
            // directly against domain boundary
            for (int k = 3; k < _ksize - 2; k++) {
                for (int j = 3; j < _jsize - 2; j++) {
                    for (int i = 3; i < _isize - 2; i++) {
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

    surface.removeMinimumTriangleCountPolyhedra(_minimumSurfacePolyhedronTriangleCount);
    _removeMeshNearDomain(surface);
    _removeMeshNearDomain(preview);
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

void FluidSimulation::_generateSurfaceMotionBlurData(TriangleMesh &surface, MACVelocityField *vfield) {
    if (!_isSurfaceMotionBlurEnabled) {
        return;
    }

    TriangleMesh blurData;
    blurData.vertices.reserve(surface.vertices.size());
    double dt = _currentFrameDeltaTime;
    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 p = surface.vertices[i];
        vmath::vec3 t = vfield->evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
        blurData.vertices.push_back(t);
    }

    _getTriangleMeshFileData(blurData, _outputData.surfaceBlurData);
    _outputData.frameData.surfaceblur.enabled = 1;
    _outputData.frameData.surfaceblur.vertices = (int)blurData.vertices.size();
    _outputData.frameData.surfaceblur.triangles = (int)blurData.triangles.size();
    _outputData.frameData.surfaceblur.bytes = (unsigned int)_outputData.surfaceBlurData.size();

}

void FluidSimulation::_generateSurfaceVelocityAttributeData(TriangleMesh &surface, MACVelocityField *vfield) {
    if (!_isSurfaceVelocityAttributeEnabled && !_isSurfaceSpeedAttributeEnabled) {
        return;
    }

    TriangleMesh velocityData;
    if (_isSurfaceVelocityAttributeEnabled) {
        velocityData.vertices.reserve(surface.vertices.size());
    }

    std::vector<float> speedData;
    if (_isSurfaceSpeedAttributeEnabled) {
        speedData.reserve(surface.vertices.size());
    }

    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 p = surface.vertices[i];
        vmath::vec3 v = vfield->evaluateVelocityAtPositionLinear(p);

        if (_isSurfaceVelocityAttributeEnabled) {
            velocityData.vertices.push_back(v);
        }

        if (_isSurfaceSpeedAttributeEnabled) {
            speedData.push_back(v.length());
        }
    }

    if (_isSurfaceVelocityAttributeEnabled) {
        _getTriangleMeshFileData(velocityData, _outputData.surfaceVelocityAttributeData);
        _outputData.frameData.surfacevelocity.enabled = 1;
        _outputData.frameData.surfacevelocity.vertices = (int)velocityData.vertices.size();
        _outputData.frameData.surfacevelocity.triangles = (int)velocityData.triangles.size();
        _outputData.frameData.surfacevelocity.bytes = (unsigned int)_outputData.surfaceVelocityAttributeData.size();
    }

    if (_isSurfaceSpeedAttributeEnabled) {
        size_t datasize = speedData.size() * sizeof(float);
        _outputData.surfaceSpeedAttributeData = std::vector<char>(datasize);
        std::memcpy(_outputData.surfaceSpeedAttributeData.data(), (char *)speedData.data(), datasize);

        _outputData.frameData.surfacespeed.enabled = 1;
        _outputData.frameData.surfacespeed.vertices = speedData.size();
        _outputData.frameData.surfacespeed.triangles = 0;
        _outputData.frameData.surfacespeed.bytes = (unsigned int)_outputData.surfaceSpeedAttributeData.size();
    }
}

void FluidSimulation::_generateSurfaceVorticityAttributeData(TriangleMesh &surface) {
    if (!_isSurfaceVorticityAttributeEnabled) {
        return;
    }

    TriangleMesh vorticityData;
    vorticityData.vertices.reserve(surface.vertices.size());

    vmath::vec3 offset(0.5 * _dx, 0.5 * _dx, 0.5 * _dx);
    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 p = surface.vertices[i] - offset;
        vmath::vec3 curl = Interpolation::trilinearInterpolate(p, _dx, _vorticityAttributeGrid);
        vorticityData.vertices.push_back(curl);
    }

    _getTriangleMeshFileData(vorticityData, _outputData.surfaceVorticityAttributeData);
    _outputData.frameData.surfacevorticity.enabled = 1;
    _outputData.frameData.surfacevorticity.vertices = (int)vorticityData.vertices.size();
    _outputData.frameData.surfacevorticity.triangles = (int)vorticityData.triangles.size();
    _outputData.frameData.surfacevorticity.bytes = (unsigned int)_outputData.surfaceVorticityAttributeData.size();
}

void FluidSimulation::_generateSurfaceAgeAttributeData(TriangleMesh &surface) {
    if (!_isSurfaceAgeAttributeEnabled) {
        return;
    }

    vmath::vec3 goffset(0.5f * _dx, 0.5f * _dx, 0.5f * _dx);

    std::vector<float> ageData;
    ageData.reserve(surface.vertices.size());
    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 p = surface.vertices[i];
        float age = Interpolation::trilinearInterpolate(p - goffset, _dx, _ageAttributeGrid);
        ageData.push_back(age);
    }

    size_t datasize = ageData.size() * sizeof(float);
    _outputData.surfaceAgeAttributeData = std::vector<char>(datasize);
    std::memcpy(_outputData.surfaceAgeAttributeData.data(), (char *)ageData.data(), datasize);

    _outputData.frameData.surfaceage.enabled = 1;
    _outputData.frameData.surfaceage.vertices = ageData.size();
    _outputData.frameData.surfaceage.triangles = 0;
    _outputData.frameData.surfaceage.bytes = (unsigned int)_outputData.surfaceAgeAttributeData.size();
}

void FluidSimulation::_generateSurfaceColorAttributeData(TriangleMesh &surface) {
    if (!_isSurfaceSourceColorAttributeEnabled) {
        return;
    }

    vmath::vec3 goffset(0.5f * _dx, 0.5f * _dx, 0.5f * _dx);

    TriangleMesh colorData;
    colorData.vertices.reserve(surface.vertices.size());
    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 p = surface.vertices[i];
        float r = Interpolation::trilinearInterpolate(p - goffset, _dx, _colorAttributeGridR);
        float g = Interpolation::trilinearInterpolate(p - goffset, _dx, _colorAttributeGridG);
        float b = Interpolation::trilinearInterpolate(p - goffset, _dx, _colorAttributeGridB);
        vmath::vec3 color(r, g, b);
        colorData.vertices.push_back(color);
    }

    _getTriangleMeshFileData(colorData, _outputData.surfaceColorAttributeData);
    _outputData.frameData.surfacecolor.enabled = 1;
    _outputData.frameData.surfacecolor.vertices = (int)colorData.vertices.size();
    _outputData.frameData.surfacecolor.triangles = (int)colorData.triangles.size();
    _outputData.frameData.surfacecolor.bytes = (unsigned int)_outputData.surfaceColorAttributeData.size();
}

void FluidSimulation::_generateSurfaceSourceIDAttributeData(TriangleMesh &surface, 
                                                            std::vector<vmath::vec3> &positions, 
                                                            std::vector<int> *sourceID) {
    if (!_isSurfaceSourceIDAttributeEnabled) {
        return;
    }

    Array3d<bool> validGrid(_isize, _jsize, _ksize, false);
    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 v = surface.vertices[i];
        GridIndex g = Grid3d::positionToGridIndex(v, _dx);
        validGrid.set(g, true);
    }

    GridUtils::featherGrid26(&validGrid, ThreadUtils::getMaxThreadCount());

    int maxCellCount = 16;
    Array3d<char> cellCounts(_isize, _jsize, _ksize, (char)0);
    for (size_t i = 0; i < positions.size(); i++) {
        vmath::vec3 p = positions[i];
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        int count = (int)cellCounts(g);
        if (!validGrid(g) || count >= maxCellCount) {
            continue;
        }

        count++;
        cellCounts.set(g, count);
    }

    int totalCount = 0;
    Array3d<int> startIndexGrid(_isize, _jsize, _ksize, -1);
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                int count = (int)cellCounts(i, j, k);
                if (count == 0) {
                    continue;
                }

                startIndexGrid.set(i, j, k, totalCount);
                totalCount += count;
            }
        }
    }

    struct PointData {
        vmath::vec3 position;
        int sourceID = 0;
    };

    std::vector<PointData> data(totalCount);
    Array3d<int> startIndexGridCopy = startIndexGrid;
    Array3d<char> cellCountsCopy = cellCounts;
    for (size_t i = 0; i < positions.size(); i++) {
        vmath::vec3 p = positions[i];
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        int count = (int)cellCountsCopy(g);
        if (!validGrid(g) || count == 0) {
            continue;
        }

        PointData pd;
        pd.position = p;
        pd.sourceID = sourceID->at(i);
        data[startIndexGridCopy(g)] = pd;
        startIndexGridCopy.add(g, 1);

        count--;
        cellCountsCopy.set(g, count);
    }

    std::vector<int> sourceIDData;
    sourceIDData.reserve(surface.vertices.size());
    for (size_t vidx = 0; vidx < surface.vertices.size(); vidx++) {
        vmath::vec3 v = surface.vertices[vidx];
        GridIndex g = Grid3d::positionToGridIndex(v, _dx);
        
        int imin = std::max(g.i - 1, 0);
        int jmin = std::max(g.j - 1, 0);
        int kmin = std::max(g.k - 1, 0);
        int imax = std::min(g.i + 1, _isize - 1);
        int jmax = std::min(g.j + 1, _jsize - 1);
        int kmax = std::min(g.k + 1, _ksize - 1);

        float minDistance = std::numeric_limits<float>::infinity();
        int minSourceID = -1;
        for (int k = kmin; k <= kmax; k++) {
            for (int j = jmin; j <= jmax; j++) {
                for (int i = imin; i <= imax; i++) {

                    int count = (int)cellCounts(i, j, k);
                    if (!validGrid(i, j, k) || count == 0) {
                        continue;
                    }
                    int startidx = startIndexGrid(i, j, k);
                    int endidx = startidx + count;

                    for (int pidx = startidx; pidx < endidx; pidx++) {
                        vmath::vec3 p = data[pidx].position;
                        float d = vmath::length(v - p);
                        if (d < minDistance) {
                            minDistance = d;
                            minSourceID = data[pidx].sourceID;
                        }
                    }

                }
            }
        }

        sourceIDData.push_back(minSourceID);
    }

    size_t datasize = sourceIDData.size() * sizeof(int);
    _outputData.surfaceSourceIDAttributeData = std::vector<char>(datasize);
    std::memcpy(_outputData.surfaceSourceIDAttributeData.data(), (char *)sourceIDData.data(), datasize);

    _outputData.frameData.surfacesourceid.enabled = 1;
    _outputData.frameData.surfacesourceid.vertices = sourceIDData.size();
    _outputData.frameData.surfacesourceid.triangles = 0;
    _outputData.frameData.surfacesourceid.bytes = (unsigned int)_outputData.surfaceSourceIDAttributeData.size();
}

void FluidSimulation::_generateSurfaceSourceColorAttributeData(TriangleMesh &surface, 
                                                               std::vector<vmath::vec3> &positions, 
                                                               std::vector<vmath::vec3> *colors) {

    if (!_isSurfaceSourceColorAttributeEnabled) {
        return;
    }

    Array3d<bool> validGrid(_isize, _jsize, _ksize, false);
    for (size_t i = 0; i < surface.vertices.size(); i++) {
        vmath::vec3 v = surface.vertices[i];
        GridIndex g = Grid3d::positionToGridIndex(v, _dx);
        validGrid.set(g, true);
    }

    GridUtils::featherGrid26(&validGrid, ThreadUtils::getMaxThreadCount());

    int maxCellCount = 16;
    Array3d<char> cellCounts(_isize, _jsize, _ksize, (char)0);
    for (size_t i = 0; i < positions.size(); i++) {
        vmath::vec3 p = positions[i];
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        int count = (int)cellCounts(g);
        if (!validGrid(g) || count >= maxCellCount) {
            continue;
        }

        count++;
        cellCounts.set(g, count);
    }

    int totalCount = 0;
    Array3d<int> startIndexGrid(_isize, _jsize, _ksize, -1);
    for (int k = 0; k < _ksize; k++) {
        for (int j = 0; j < _jsize; j++) {
            for (int i = 0; i < _isize; i++) {
                int count = (int)cellCounts(i, j, k);
                if (count == 0) {
                    continue;
                }

                startIndexGrid.set(i, j, k, totalCount);
                totalCount += count;
            }
        }
    }

    struct PointData {
        vmath::vec3 position;
        vmath::vec3 color;
    };

    std::vector<PointData> data(totalCount);
    Array3d<int> startIndexGridCopy = startIndexGrid;
    Array3d<char> cellCountsCopy = cellCounts;
    for (size_t i = 0; i < positions.size(); i++) {
        vmath::vec3 p = positions[i];
        GridIndex g = Grid3d::positionToGridIndex(p, _dx);
        int count = (int)cellCountsCopy(g);
        if (!validGrid(g) || count == 0) {
            continue;
        }

        PointData pd;
        pd.position = p;
        pd.color = colors->at(i);
        data[startIndexGridCopy(g)] = pd;
        startIndexGridCopy.add(g, 1);

        count--;
        cellCountsCopy.set(g, count);
    }

    std::vector<vmath::vec3> sourceColorData;
    sourceColorData.reserve(surface.vertices.size());
    for (size_t vidx = 0; vidx < surface.vertices.size(); vidx++) {
        vmath::vec3 v = surface.vertices[vidx];
        GridIndex g = Grid3d::positionToGridIndex(v, _dx);
        
        int imin = std::max(g.i - 1, 0);
        int jmin = std::max(g.j - 1, 0);
        int kmin = std::max(g.k - 1, 0);
        int imax = std::min(g.i + 1, _isize - 1);
        int jmax = std::min(g.j + 1, _jsize - 1);
        int kmax = std::min(g.k + 1, _ksize - 1);

        float minDistance = std::numeric_limits<float>::infinity();
        vmath::vec3 minSourceColor;
        for (int k = kmin; k <= kmax; k++) {
            for (int j = jmin; j <= jmax; j++) {
                for (int i = imin; i <= imax; i++) {

                    int count = (int)cellCounts(i, j, k);
                    if (!validGrid(i, j, k) || count == 0) {
                        continue;
                    }
                    int startidx = startIndexGrid(i, j, k);
                    int endidx = startidx + count;

                    for (int pidx = startidx; pidx < endidx; pidx++) {
                        vmath::vec3 p = data[pidx].position;
                        float d = vmath::length(v - p);
                        if (d < minDistance) {
                            minDistance = d;
                            minSourceColor = data[pidx].color;
                        }
                    }

                }
            }
        }

        sourceColorData.push_back(minSourceColor);
    }

    sourceColorData = surface.smoothColors(0.5, 2, sourceColorData);

    TriangleMesh m;
    m.vertices = sourceColorData;
    _getTriangleMeshFileData(m, _outputData.surfaceColorAttributeData);
    _outputData.frameData.surfacecolor.enabled = 1;
    _outputData.frameData.surfacecolor.vertices = (int)m.vertices.size();
    _outputData.frameData.surfacecolor.triangles = (int)m.triangles.size();
    _outputData.frameData.surfacecolor.bytes = (unsigned int)_outputData.surfaceColorAttributeData.size();

}

void FluidSimulation::_outputSurfaceMeshThread(std::vector<vmath::vec3> *particles,
                                               MeshLevelSet *solidSDF, 
                                               MACVelocityField *vfield,
                                               std::vector<int> *sourceID,
                                               std::vector<vmath::vec3> *colors) {
    if (!_isSurfaceMeshReconstructionEnabled) { return; }

    _logfile.logString(_logfile.getTime() + " BEGIN       Generate Surface Mesh");

    StopWatch t;
    t.start();

    std::vector<vmath::vec3> particlesCopy;
    if (_isSurfaceSourceIDAttributeEnabled || _isSurfaceSourceColorAttributeEnabled) {
        particlesCopy = *particles;
    }

    TriangleMesh surfacemesh, previewmesh;
    _generateOutputSurface(surfacemesh, previewmesh, particles, solidSDF);
    delete particles;
    delete solidSDF;

    surfacemesh.removeMinimumTriangleCountPolyhedra(_minimumSurfacePolyhedronTriangleCount);

    _removeMeshNearDomain(surfacemesh);
    _smoothSurfaceMesh(surfacemesh);
    _smoothSurfaceMesh(previewmesh);
    _invertContactNormals(surfacemesh);

    AABB bbox = _getBoundaryAABB();
    bbox.expand(-8.0f * _dx);
    vmath::vec3 bboxcenter = bbox.position + 0.5 * vmath::vec3(bbox.width, bbox.height, bbox.depth);

    TriangleMesh addmesh;
    for (size_t i = 0; i < _vertx.size(); i += 3) {
        vmath::vec3 v(_vertx[i+0], _vertx[i+1], _vertx[i+2]);
        addmesh.vertices.push_back(v);
    }
    for (size_t i = 0; i < _trix.size(); i += 3) {
        Triangle t;
        t.tri[0] = _trix[i+0];
        t.tri[1] = _trix[i+1];
        t.tri[2] = _trix[i+2];
        addmesh.triangles.push_back(t);
    }

    float width = 0.75 * std::min(bbox.height, bbox.depth);
    addmesh.scale(vmath::vec3(width, width, width));

    AABB bboxx(addmesh.vertices);
    vmath::vec3 bboxxcenter = bboxx.position + 0.5 * vmath::vec3(bboxx.width, bboxx.height, bboxx.depth);
    vmath::vec3 translate(bbox.position.x, bboxcenter.y - bboxxcenter.y, bboxcenter.z - bboxxcenter.z);
    addmesh.translate(translate);
    surfacemesh.append(addmesh);
    previewmesh.append(addmesh);
    addmesh.translate(vmath::vec3(bbox.width, 0.0, 0.0));
    surfacemesh.append(addmesh);
    previewmesh.append(addmesh);

    addmesh = TriangleMesh();
    for (size_t i = 0; i < _verty.size(); i += 3) {
        vmath::vec3 v(_verty[i+0], _verty[i+1], _verty[i+2]);
        addmesh.vertices.push_back(v);
    }
    for (size_t i = 0; i < _triy.size(); i += 3) {
        Triangle t;
        t.tri[0] = _triy[i+0];
        t.tri[1] = _triy[i+1];
        t.tri[2] = _triy[i+2];
        addmesh.triangles.push_back(t);
    }

    width = 0.75 * std::min(bbox.width, bbox.depth);
    addmesh.scale(vmath::vec3(width, width, width));

    bboxx = AABB(addmesh.vertices);
    bboxxcenter = bboxx.position + 0.5 * vmath::vec3(bboxx.width, bboxx.height, bboxx.depth);
    translate = vmath::vec3(bboxcenter.x - bboxxcenter.x, bbox.position.y, bboxcenter.z - bboxxcenter.z);
    addmesh.translate(translate);
    surfacemesh.append(addmesh);
    previewmesh.append(addmesh);
    addmesh.translate(vmath::vec3(0.0, bbox.height, 0.0));
    surfacemesh.append(addmesh);
    previewmesh.append(addmesh);

    addmesh = TriangleMesh();
    for (size_t i = 0; i < _vertz.size(); i += 3) {
        vmath::vec3 v(_vertz[i+0], _vertz[i+1], _vertz[i+2]);
        addmesh.vertices.push_back(v);
    }
    for (size_t i = 0; i < _triz.size(); i += 3) {
        Triangle t;
        t.tri[0] = _triz[i+0];
        t.tri[1] = _triz[i+1];
        t.tri[2] = _triz[i+2];
        addmesh.triangles.push_back(t);
    }

    width = 0.75 * std::min(bbox.width, bbox.height);
    addmesh.scale(vmath::vec3(width, width, width));

    bboxx = AABB(addmesh.vertices);
    bboxxcenter = bboxx.position + 0.5 * vmath::vec3(bboxx.width, bboxx.height, bboxx.depth);
    translate = vmath::vec3(bboxcenter.x - bboxxcenter.x, bboxcenter.y - bboxxcenter.y, bbox.position.z);
    addmesh.translate(translate);
    surfacemesh.append(addmesh);
    previewmesh.append(addmesh);
    addmesh.translate(vmath::vec3(0.0, 0.0, bbox.depth));
    surfacemesh.append(addmesh);
    previewmesh.append(addmesh);

    if (_isSurfaceMotionBlurEnabled) {
        TriangleMesh blurData;
        blurData.vertices.reserve(surfacemesh.vertices.size());
        double dt = _currentFrameDeltaTime;
        for (size_t i = 0; i < surfacemesh.vertices.size(); i++) {
            vmath::vec3 p = surfacemesh.vertices[i];
            vmath::vec3 t = _MACVelocity.evaluateVelocityAtPositionLinear(p) * _domainScale * dt;
            blurData.vertices.push_back(t);
        }
    }

    _generateSurfaceMotionBlurData(surfacemesh, vfield);
    _generateSurfaceVelocityAttributeData(surfacemesh, vfield);
    delete vfield;

    _generateSurfaceVorticityAttributeData(surfacemesh);

    _generateSurfaceSourceIDAttributeData(surfacemesh, particlesCopy, sourceID);
    delete sourceID;

    _generateSurfaceSourceColorAttributeData(surfacemesh, particlesCopy, colors);
    delete colors;

    particlesCopy.clear();
    particlesCopy.shrink_to_fit();

    _generateSurfaceAgeAttributeData(surfacemesh);
    //_generateSurfaceColorAttributeData(surfacemesh);
    
    _invertContactNormals(surfacemesh);

    vmath::vec3 scale(_domainScale, _domainScale, _domainScale);
    surfacemesh.scale(scale);
    surfacemesh.translate(_domainOffset);

    _getTriangleMeshFileData(surfacemesh, _outputData.surfaceData);
    _outputData.frameData.surface.enabled = 1;
    _outputData.frameData.surface.vertices = (int)surfacemesh.vertices.size();
    _outputData.frameData.surface.triangles = (int)surfacemesh.triangles.size();
    _outputData.frameData.surface.bytes = (unsigned int)_outputData.surfaceData.size();

    if (_isPreviewSurfaceMeshEnabled) {
        _smoothSurfaceMesh(previewmesh);
        previewmesh.scale(scale);
        previewmesh.translate(_domainOffset);

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
    std::vector<vmath::vec3> *positions;
    _markerParticles.getAttributeValues("POSITION", positions);

    // Particles will be deleted within the thread after use
    std::vector<vmath::vec3> *particles = new std::vector<vmath::vec3>();
    particles->reserve(positions->size());
    for (size_t i = 0; i < positions->size(); i++) {
        particles->push_back(positions->at(i));
    }

    // solidSDF will be deleted within the thread after use
    MeshLevelSet *tempSolidSDF = new MeshLevelSet();
    tempSolidSDF->constructMinimalSignedDistanceField(_solidSDF);

    // Velocity Field will be deleted within the thread after use
    MACVelocityField *vfield = new MACVelocityField();
    if (_isSurfaceMotionBlurEnabled || _isSurfaceVelocityAttributeEnabled || _isSurfaceSpeedAttributeEnabled) {
        *vfield = _MACVelocity;
    }

    // SourceID will be deleted within the thread after use
    std::vector<int> *sourceID = new std::vector<int>();
    if (_isSurfaceSourceIDAttributeEnabled) {
        std::vector<int> *ids = nullptr;
        _markerParticles.getAttributeValues("SOURCEID", ids);

        sourceID->reserve(ids->size());
        for (size_t i = 0; i < ids->size(); i++) {
            sourceID->push_back(ids->at(i));
        }
    }

    // SourceColors will be deleted within the thread after use
    std::vector<vmath::vec3> *sourceColors = new std::vector<vmath::vec3>();
    if (_isSurfaceSourceColorAttributeEnabled) {
        std::vector<vmath::vec3> *colors = nullptr;
        _markerParticles.getAttributeValues("COLOR", colors);

        sourceColors->reserve(colors->size());
        for (size_t i = 0; i < colors->size(); i++) {
            sourceColors->push_back(colors->at(i));
        }
    }

    _mesherThread = std::thread(&FluidSimulation::_outputSurfaceMeshThread, this,
                                particles, tempSolidSDF, vfield, sourceID, sourceColors);

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
        _diffuseMaterial.getDustParticleFileDataWWP(_outputData.diffuseDustData);

        int nspray, nbubble, nfoam, ndust;
        _diffuseMaterial.getDiffuseParticleTypeCounts(&nfoam, 
                                                      &nbubble, 
                                                      &nspray,
                                                      &ndust);

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

        _outputData.frameData.dust.enabled = 1;
        _outputData.frameData.dust.vertices = ndust;
        _outputData.frameData.dust.triangles = 0;
        _outputData.frameData.dust.bytes = _outputData.diffuseDustData.size();

        if (_isWhitewaterMotionBlurEnabled) {
            double dt = _currentFrameDeltaTime;
            _diffuseMaterial.getFoamParticleBlurFileDataWWP(_outputData.diffuseFoamBlurData, dt);
            _diffuseMaterial.getBubbleParticleBlurFileDataWWP(_outputData.diffuseBubbleBlurData, dt);
            _diffuseMaterial.getSprayParticleBlurFileDataWWP(_outputData.diffuseSprayBlurData, dt);
            _diffuseMaterial.getDustParticleBlurFileDataWWP(_outputData.diffuseDustBlurData, dt);

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

            _outputData.frameData.dustblur.enabled = 1;
            _outputData.frameData.dustblur.vertices = ndust;
            _outputData.frameData.dustblur.triangles = 0;
            _outputData.frameData.dustblur.bytes = (unsigned int)_outputData.diffuseDustBlurData.size();
        }

        if (_isWhitewaterVelocityAttributeEnabled) {
            _diffuseMaterial.getFoamParticleVelocityAttributeFileDataWWP(_outputData.whitewaterFoamVelocityAttributeData);
            _diffuseMaterial.getBubbleParticleVelocityAttributeFileDataWWP(_outputData.whitewaterBubbleVelocityAttributeData);
            _diffuseMaterial.getSprayParticleVelocityAttributeFileDataWWP(_outputData.whitewaterSprayVelocityAttributeData);
            _diffuseMaterial.getDustParticleVelocityAttributeFileDataWWP(_outputData.whitewaterDustVelocityAttributeData);

            _outputData.frameData.foamvelocity.enabled = 1;
            _outputData.frameData.foamvelocity.vertices = nfoam;
            _outputData.frameData.foamvelocity.triangles = 0;
            _outputData.frameData.foamvelocity.bytes = (unsigned int)_outputData.whitewaterFoamVelocityAttributeData.size();

            _outputData.frameData.bubblevelocity.enabled = 1;
            _outputData.frameData.bubblevelocity.vertices = nbubble;
            _outputData.frameData.bubblevelocity.triangles = 0;
            _outputData.frameData.bubblevelocity.bytes = (unsigned int)_outputData.whitewaterBubbleVelocityAttributeData.size();

            _outputData.frameData.sprayvelocity.enabled = 1;
            _outputData.frameData.sprayvelocity.vertices = nspray;
            _outputData.frameData.sprayvelocity.triangles = 0;
            _outputData.frameData.sprayvelocity.bytes = (unsigned int)_outputData.whitewaterSprayVelocityAttributeData.size();

            _outputData.frameData.dustvelocity.enabled = 1;
            _outputData.frameData.dustvelocity.vertices = ndust;
            _outputData.frameData.dustvelocity.triangles = 0;
            _outputData.frameData.dustvelocity.bytes = (unsigned int)_outputData.whitewaterDustVelocityAttributeData.size();
        }

        if (_isWhitewaterIDAttributeEnabled) {
            _diffuseMaterial.getFoamParticleIDAttributeFileDataWWI(_outputData.whitewaterFoamIDAttributeData);
            _diffuseMaterial.getBubbleParticleIDAttributeFileDataWWI(_outputData.whitewaterBubbleIDAttributeData);
            _diffuseMaterial.getSprayParticleIDAttributeFileDataWWI(_outputData.whitewaterSprayIDAttributeData);
            _diffuseMaterial.getDustParticleIDAttributeFileDataWWI(_outputData.whitewaterDustIDAttributeData);

            _outputData.frameData.foamid.enabled = 1;
            _outputData.frameData.foamid.vertices = nfoam;
            _outputData.frameData.foamid.triangles = 0;
            _outputData.frameData.foamid.bytes = (unsigned int)_outputData.whitewaterFoamIDAttributeData.size();

            _outputData.frameData.bubbleid.enabled = 1;
            _outputData.frameData.bubbleid.vertices = nbubble;
            _outputData.frameData.bubbleid.triangles = 0;
            _outputData.frameData.bubbleid.bytes = (unsigned int)_outputData.whitewaterBubbleIDAttributeData.size();

            _outputData.frameData.sprayid.enabled = 1;
            _outputData.frameData.sprayid.vertices = nspray;
            _outputData.frameData.sprayid.triangles = 0;
            _outputData.frameData.sprayid.bytes = (unsigned int)_outputData.whitewaterSprayIDAttributeData.size();

            _outputData.frameData.dustid.enabled = 1;
            _outputData.frameData.dustid.vertices = ndust;
            _outputData.frameData.dustid.triangles = 0;
            _outputData.frameData.dustid.bytes = (unsigned int)_outputData.whitewaterDustIDAttributeData.size();
        }

        if (_isWhitewaterLifetimeAttributeEnabled) {
            _diffuseMaterial.getFoamParticleLifetimeAttributeFileDataWWF(_outputData.whitewaterFoamLifetimeAttributeData);
            _diffuseMaterial.getBubbleParticleLifetimeAttributeFileDataWWF(_outputData.whitewaterBubbleLifetimeAttributeData);
            _diffuseMaterial.getSprayParticleLifetimeAttributeFileDataWWF(_outputData.whitewaterSprayLifetimeAttributeData);
            _diffuseMaterial.getDustParticleLifetimeAttributeFileDataWWF(_outputData.whitewaterDustLifetimeAttributeData);

            _outputData.frameData.foamlifetime.enabled = 1;
            _outputData.frameData.foamlifetime.vertices = nfoam;
            _outputData.frameData.foamlifetime.triangles = 0;
            _outputData.frameData.foamlifetime.bytes = (unsigned int)_outputData.whitewaterFoamLifetimeAttributeData.size();

            _outputData.frameData.bubblelifetime.enabled = 1;
            _outputData.frameData.bubblelifetime.vertices = nbubble;
            _outputData.frameData.bubblelifetime.triangles = 0;
            _outputData.frameData.bubblelifetime.bytes = (unsigned int)_outputData.whitewaterBubbleLifetimeAttributeData.size();

            _outputData.frameData.spraylifetime.enabled = 1;
            _outputData.frameData.spraylifetime.vertices = nspray;
            _outputData.frameData.spraylifetime.triangles = 0;
            _outputData.frameData.spraylifetime.bytes = (unsigned int)_outputData.whitewaterSprayLifetimeAttributeData.size();

            _outputData.frameData.dustlifetime.enabled = 1;
            _outputData.frameData.dustlifetime.vertices = ndust;
            _outputData.frameData.dustlifetime.triangles = 0;
            _outputData.frameData.dustlifetime.bytes = (unsigned int)_outputData.whitewaterDustLifetimeAttributeData.size();
        }

    } else {
        _diffuseMaterial.getDiffuseParticleFileDataWWP(_outputData.diffuseData);
    }
}

float FluidSimulation::_calculateParticleSpeedPercentileThreshold(float pct) {
    std::vector<vmath::vec3> *velocities;
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    float eps = 1e-3;
    float maxs = fmax(_getMaximumMarkerParticleSpeed(), eps);
    float invmax = 1.0f / maxs;
    int nbins = 10000;
    std::vector<int> binCounts(nbins, 0);
    for (size_t i = 0; i < _markerParticles.size(); i++) {
        float s = vmath::length(velocities->at(i));
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

    std::vector<vmath::vec3> *positions, *velocities;
    _markerParticles.getAttributeValues("POSITION", positions);
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    float maxSpeed = _calculateParticleSpeedPercentileThreshold(0.995);
    float invmax = 1.0f / maxSpeed;
    int nbins = 1024;
    std::vector<int> binCounts(nbins, 0);
    for (size_t i = 0; i < velocities->size(); i++) {
        float s = vmath::length(velocities->at(i));
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
    for (size_t i = 0; i < velocities->size(); i++) {
        float s = vmath::length(velocities->at(i));
        int binidx = (int)fmin(floor(s * invmax * (nbins - 1)), nbins - 1);
        int vidx = binStartsCopy[binidx];
        binStartsCopy[binidx]++;

        vmath::vec3 p = positions->at(i);
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

void FluidSimulation::_outputForceFieldDebugData() {
    if (!_isForceFieldDebugOutputEnabled) { 
        return; 
    }

    std::vector<ForceFieldDebugNode> debugNodes;
    _forceFieldGrid.generateDebugNodes(debugNodes);

    for (size_t i = 0; i < debugNodes.size(); i++) {
        ForceFieldDebugNode n = debugNodes[i];
        n.x = n.x * _domainScale + _domainOffset.x;
        n.y = n.y * _domainScale + _domainOffset.y;
        n.z = n.z * _domainScale + _domainOffset.z;
        debugNodes[i] = n;
    }

    _getForceFieldDebugFileData(debugNodes, _outputData.forceFieldDebugData);

    _outputData.frameData.obstacle.enabled = 1;
    _outputData.frameData.obstacle.vertices = (int)debugNodes.size();
    _outputData.frameData.obstacle.triangles = 0;
    _outputData.frameData.forcefield.bytes = _outputData.forceFieldDebugData.size();
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
        _outputForceFieldDebugData();
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
    srand(_currentFrame + _currentFrameTimeStepNumber);
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
        _updateMarkerParticleAttributes(dt);
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
    std::vector<vmath::vec3> *velocities;
    _markerParticles.getAttributeValues("VELOCITY", velocities);

    double maxsq = 0.0;
    for (unsigned int i = 0; i < velocities->size(); i++) {
        vmath::vec3 v = velocities->at(i);
        double distsq = vmath::dot(v, v);
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

double FluidSimulation::_getFrameInterpolation() {
    double frameTime = _currentFrameDeltaTimeRemaining + _currentFrameTimeStep;
    return 1.0 - (frameTime / _currentFrameDeltaTime);
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
        PrintData("Apply Force Fields                   ", tdata.applyBodyForcesToVelocityField),
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
        int spraycount, bubblecount, foamcount, dustcount;
        _diffuseMaterial.getDiffuseParticleTypeCounts(&foamcount, 
                                                      &bubblecount, 
                                                      &spraycount,
                                                      &dustcount);
        std::stringstream dss;
        dss << "Diffuse Particles: " << getNumDiffuseParticles() << std::endl << 
          "    Foam:          " << foamcount << std::endl << 
          "    Bubble:        " << bubblecount << std::endl << 
          "    Spray:         " << spraycount << std::endl << 
          "    Dust:          " << dustcount;
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
    bool isDebuggingEnabled = _isFluidParticleOutputEnabled || _isInternalObstacleMeshOutputEnabled || _isForceFieldDebugOutputEnabled;
    _isSkippedFrame = _isZeroLengthDeltaTime && _outputData.isInitialized && !isDebuggingEnabled;
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