/*
MIT License

Copyright (C) 2025 Ryan L. Guy & Dennis Fassbaender

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

#pragma once

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include <vector>
#include <random>
#include <cstring>

#include "vmath.h"
#include "array3d.h"
#include "meshobject.h"
#include "fragmentedvector.h"
#include "logfile.h"
#include "particlelevelset.h"
#include "pressuresolver.h"
#include "diffuseparticlesimulation.h"
#include "velocityadvector.h"
#include "meshfluidsource.h"
#include "influencegrid.h"
#include "forcefieldgrid.h"
#include "particlesystem.h"
#include "markerparticle.h"
#include "viscositysolver.h"
#include "spatialpointgrid.h"

class AABB;
class MeshFluidSource;
class ParticleMaskGrid;
class MACVelocityField;
class FluidMaterialGrid;
struct DiffuseParticle;
enum class LimitBehaviour : char;

struct FluidSimulationMeshStats {
    int enabled = 0;
    int vertices = -1;
    int triangles = -1;
    unsigned int bytes = 0;
};

struct FluidSimulationTimingStats {
    double total = 0.0;
    double mesh = 0.0;
    double advection = 0.0;
    double particles = 0.0;
    double pressure = 0.0;
    double diffuse = 0.0;
    double viscosity = 0.0;
    double objects = 0.0;
};

struct FluidSimulationFrameStats {
    int frame = 0;
    int substeps = 0;
    double deltaTime = 0.0;
    int fluidParticles = 0;
    int diffuseParticles = 0;
    int performanceScore = 0;

    int pressureSolverEnabled = 1;
    int pressureSolverSuccess = 0;
    double pressureSolverError = 0.0;
    int pressureSolverIterations = 0;
    int pressureSolverMaxIterations = 0;

    int viscositySolverEnabled = 1;
    int viscositySolverSuccess = 0;
    double viscositySolverError = 0.0;
    int viscositySolverIterations = 0;
    int viscositySolverMaxIterations = 0;

    FluidSimulationMeshStats surface;
    FluidSimulationMeshStats preview;
    FluidSimulationMeshStats surfaceblur;
    FluidSimulationMeshStats surfacevelocity;
    FluidSimulationMeshStats surfacevorticity;
    FluidSimulationMeshStats surfacespeed;
    FluidSimulationMeshStats surfaceage;
    FluidSimulationMeshStats surfacelifetime;
    FluidSimulationMeshStats surfacewhitewaterproximity;
    FluidSimulationMeshStats surfacecolor;
    FluidSimulationMeshStats surfacesourceid;
    FluidSimulationMeshStats surfaceviscosity;
    FluidSimulationMeshStats surfacedensity;
    FluidSimulationMeshStats foam;
    FluidSimulationMeshStats bubble;
    FluidSimulationMeshStats spray;
    FluidSimulationMeshStats dust;
    FluidSimulationMeshStats foamblur;
    FluidSimulationMeshStats bubbleblur;
    FluidSimulationMeshStats sprayblur;
    FluidSimulationMeshStats dustblur;
    FluidSimulationMeshStats foamvelocity;
    FluidSimulationMeshStats bubblevelocity;
    FluidSimulationMeshStats sprayvelocity;
    FluidSimulationMeshStats dustvelocity;
    FluidSimulationMeshStats foamid;
    FluidSimulationMeshStats bubbleid;
    FluidSimulationMeshStats sprayid;
    FluidSimulationMeshStats dustid;
    FluidSimulationMeshStats foamlifetime;
    FluidSimulationMeshStats bubblelifetime;
    FluidSimulationMeshStats spraylifetime;
    FluidSimulationMeshStats dustlifetime;
    FluidSimulationMeshStats fluidparticles;
    FluidSimulationMeshStats fluidparticlesid;
    FluidSimulationMeshStats fluidparticlesuid;
    FluidSimulationMeshStats fluidparticlesvelocity;
    FluidSimulationMeshStats fluidparticlesspeed;
    FluidSimulationMeshStats fluidparticlesvorticity;
    FluidSimulationMeshStats fluidparticlescolor;
    FluidSimulationMeshStats fluidparticlesage;
    FluidSimulationMeshStats fluidparticleslifetime;
    FluidSimulationMeshStats fluidparticlesviscosity;
    FluidSimulationMeshStats fluidparticlesdensity;
    FluidSimulationMeshStats fluidparticlesdensityaverage;
    FluidSimulationMeshStats fluidparticleswhitewaterproximity;
    FluidSimulationMeshStats fluidparticlessourceid;
    FluidSimulationMeshStats particles;
    FluidSimulationMeshStats obstacle;
    FluidSimulationMeshStats forcefield;
    FluidSimulationTimingStats timing;
};

struct FluidSimulationMarkerParticleData {
    int size = 0;
    char *positions;
    char *velocities;
};

struct FluidSimulationMarkerParticleAffineData {
    int size = 0;
    char *affineX;
    char *affineY;
    char *affineZ;
};

struct FluidSimulationMarkerParticleAgeData {
    int size = 0;
    char *age;
};

struct FluidSimulationMarkerParticleLifetimeData {
    int size = 0;
    char *lifetime;
};

struct FluidSimulationMarkerParticleColorData {
    int size = 0;
    char *color;
};

struct FluidSimulationMarkerParticleSourceIDData {
    int size = 0;
    char *sourceid;
};

struct FluidSimulationMarkerParticleUIDData {
    int size = 0;
    char *uid;
};

struct FluidSimulationMarkerParticleViscosityData {
    int size = 0;
    char *viscosity;
};

struct FluidSimulationMarkerParticleDensityData {
    int size = 0;
    char *density;
};

struct FluidSimulationMarkerParticleIDData {
    int size = 0;
    char *id;
};

struct FluidSimulationDiffuseParticleData {
    int size = 0;
    char *positions;
    char *velocities;
    char *lifetimes;
    char *types;
    char *ids;
};

struct FluidSimulationMixboxLutData {
    int size = 0;
    char *data;
};

class FluidSimulation
{
public:
    FluidSimulation();

    /*
        Constructs a FluidSimulation object with grid dimensions
        of width isize, height jsize, depth ksize, with each grid cell
        having width dx.
    */
    FluidSimulation(int isize, int jsize, int ksize, double dx);

    ~FluidSimulation();

    /*
        Retrieve the simulator version
    */
    void getVersion(int *major, int *minor, int *revision);

    /*
        Upscale (or downscale) the particle data from previousCellSize
        to the current cell size (dx)
    */
        void upscaleOnInitialization(int isizePrev, int jsizePrev, int ksizePrev, double dxPrev);

    /*
        Initializes the fluid simulation.

        Must be called before running update() method.
    */
    void initialize();
    bool isInitialized();

    /*
        Initialize Secret Weapons Mixbox LUT data
    */
    void initializeMixbox(FluidSimulationMixboxLutData data);

    /*
        Advance the fluid simulation for a single frame time of dt seconds.
    */
    void update(double dt);

    /*
        Get/Set current frame of the simulation. Frame numbering starts
        at zero.
    */
    int getCurrentFrame();
    void setCurrentFrame(int frameno);
    void setTimelineFrameStart(int frameno);
    void setTimelineFrameEnd(int frameno);

    /*
        Returns false only when the update() method is being executed. May be
        used if executing the update() method in seperate thread.
    */
    bool isCurrentFrameFinished();

    /* 
        returns the width of a simulation grid cell
    */
    double getCellSize();

    /*
        Retrieves the simulation grid dimensions.
            i   ->   width
            j   ->   height
            k   ->   depth
    */
    void getGridDimensions(int *i, int *j, int *k);
    int getGridWidth();
    int getGridHeight();
    int getGridDepth();

    /*  
        Retrieves the physical simulation dimensions. Values are equivalent
        to multiplying the grid dimension by the grid cell size.
    */
    void getSimulationDimensions(double *width, double *height, double *depth);
    double getSimulationWidth();
    double getSimulationHeight();
    double getSimulationDepth();

    /*
        Fluid particle collisions at boundary

        Closed boundary in order: [-x, +x, -y, +y, -z, +z]
    */
    std::vector<bool> getFluidBoundaryCollisions();
    void setFluidBoundaryCollisions(std::vector<bool> active);

    int getFluidOpenBoundaryWidth();
    void setFluidOpenBoundaryWidth(int width);  // width in # of voxels

    /*
        Density of the fluid. 
        Must be greater than zero. 
        Fluid density currently has no effect on the simulation.
    */
    double getDensity();
    void setDensity(double p);

    /*
        Marker particle scale determines how large a particle is when
        converting a set of particles to a triangle mesh. 

        A marker particle with a scale of 1.0 will have the radius of a 
        sphere that has a volume 1/8th of the volume of a grid cell.
    */
    double getMarkerParticleScale();
    void setMarkerParticleScale(double s);

    /*
        Amount of random jitter (in terms of (1/4)*cell_width) that is added
        to the x/y/z axis' of a newly spawned marker particle.

        Enable/disable jittering near mesh surface
    */
    double getMarkerParticleJitterFactor();
    void setMarkerParticleJitterFactor(double jit);
    void enableJitterSurfaceMarkerParticles();
    void disableJitterSurfaceMarkerParticles();
    bool isJitterSurfaceMarkerParticlesEnabled();

    /*
        Solver Parameters
    */
    int getPressureSolverMaxIterations();
    void setPressureSolverMaxIterations(int n);

    int getViscositySolverMaxIterations();
    void setViscositySolverMaxIterations(int n);

    /*
        Output fluid particle data to the simulation cache.
        Disabled by default.
    */
    void enableFluidParticleOutput();
    void disableFluidParticleOutput();
    bool isFluidParticleOutputEnabled();

    double getFluidParticleOutputAmount();
    void setFluidParticleOutputAmount(double amount);

    void enableFluidParticleSurfaceOutput();
    void disableFluidParticleSurfaceOutput();
    bool isFluidParticleSurfaceOutputEnabled();

    void enableFluidParticleBoundaryOutput();
    void disableFluidParticleBoundaryOutput();
    bool isFluidParticleBoundaryOutputEnabled();

    void enableFluidParticleInteriorOutput();
    void disableFluidParticleInteriorOutput();
    bool isFluidParticleInteriorOutputEnabled();

    int getFluidParticleSourceIDBlacklist();
    void setFluidParticleSourceIDBlacklist(int id);

    /*
        The surface subdivision level determines how many times the
        simulation grid is divided when converting marker particles
        to a triangle mesh

        For example, a simulation with dimensions 256 x 128 x 80 and
        a subdivision level of 2 will polygonize the surface on a grid
        with dimensions 512 x 256 x 160. With a subdivision of level 3,
        the polygonization grid will have dimensions 768 x 384 x 240.

        A higher subdivision level will produce a higher quality surface at
        the cost of longer simulation times and greater memory usage.
    */
    int getSurfaceSubdivisionLevel();
    void setSurfaceSubdivisionLevel(int n);

    /*
        How many slices the polygonizer will section the surface reconstruction
        grid into when computing the triangle mesh. The polygonizer will compute
        the triangle mesh one slice at a time before combining them into a
        single triangle mesh.

        A higher subdivision level may require a very large amount of memory to
        store the polygonization grid data. Setting the number of slices will 
        reduce the memory required at the cost of speed.
    */
    int getNumPolygonizerSlices();
    void setNumPolygonizerSlices(int n);


    /*
        Smoothing Value: Amount of smoothing in range of [0.0, 1.0], although
                         values outside of the range can be used to distort the 
                         mesh.
        Smoothing Iterations: number of smoothing repetitions.
    */
    double getSurfaceSmoothingValue();
    void setSurfaceSmoothingValue(double s);
    int getSurfaceSmoothingIterations();
    void setSurfaceSmoothingIterations(int n);

    /*
        If set, only fluid inside of this object will be meshed
    */
    void setMeshingVolume(MeshObject *volumeObject);

    /*
        Will ensure that the output triangle mesh only contains polyhedrons
        that contain a minimum number of triangles. Removing polyhedrons with
        a low triangle count will reduce the triangle mesh size when saved to 
        disk.
    */
    int getMinPolyhedronTriangleCount();
    void setMinPolyhedronTriangleCount(int n);

    /*
        Offset will be added to the position of the meshes output by the 
        simulator.
    */
    vmath::vec3 getDomainOffset();
    void setDomainOffset(double x, double y, double z);
    void setDomainOffset(vmath::vec3 offset);

    /*
        Output meshes will be scaled before translation
    */
    double getDomainScale();
    void setDomainScale(double scale);

    /*
        Specify file format that meshes will use. PLY by default.
    */
    void setMeshOutputFormatAsPLY();
    void setMeshOutputFormatAsBOBJ();

    /*
        Enable/disable simulation info to console.

        Enabled by default.
    */
    void enableConsoleOutput();
    void disableConsoleOutput();
    bool isConsoleOutputEnabled();

    /*
        Enable/disable the simulation from saving reconstructed triangle 
        meshes to disk.

        Enabled by default.
    */
    void enableSurfaceReconstruction();
    void disableSurfaceReconstruction();
    bool isSurfaceReconstructionEnabled();

    /*
        Enable/disable particle meshing in a background thread. Will use more
        memory if enabled.

        Enabled by default.
    */
    void enableAsynchronousMeshing();
    void disableAsynchronousMeshing();
    bool isAsynchronousMeshingEnabled();

    /*
        Enable/disable the simulation from saving preview triangle 
        meshes to disk.

        A preview mesh is reconstructed at a specified resolution seperate from
        the simulation resolution.

        Enabled by default.
    */
    void enablePreviewMeshOutput(double dx);
    void disablePreviewMeshOutput();
    bool isPreviewMeshOutputEnabled();

    /*
        isolevel offset for meshing against obstacles
    */
    void enableObstacleMeshingOffset();
    void disableObstacleMeshingOffset();
    bool isObstacleMeshingOffsetEnabled();
    double getObstacleMeshingOffset();
    void setObstacleMeshingOffset(double s);

    /*
        Invert surface mesh normals that contact obstacle surfaces. Used for 
        correct refraction rendering with water-glass interfaces.
    */
    void enableInvertedContactNormals();
    void disableInvertedContactNormals();
    bool isInvertedContactNormalsEnabled();

    /*
        Generate motion blur vector data at fluid surface mesh vertices
    */
    void enableSurfaceMotionBlur();
    void disableSurfaceMotionBlur();
    bool isSurfaceMotionBlurEnabled();

    /*
        Generate motion blur vector data at whitewater mesh vertices
    */
    void enableWhitewaterMotionBlur();
    void disableWhitewaterMotionBlur();
    bool isWhitewaterMotionBlurEnabled();

    /*
        Generate velocity vector, speed, and vorticity vector attributes at fluid mesh vertices
    */
    void enableSurfaceVelocityAttribute();
    void disableSurfaceVelocityAttribute();
    bool isSurfaceVelocityAttributeEnabled();

    void enableSurfaceVelocityAttributeAgainstObstacles();
    void disableSurfaceVelocityAttributeAgainstObstacles();
    bool isSurfaceVelocityAttributeAgainstObstaclesEnabled();

    void enableSurfaceSpeedAttribute();
    void disableSurfaceSpeedAttribute();
    bool isSurfaceSpeedAttributeEnabled();

    void enableSurfaceVorticityAttribute();
    void disableSurfaceVorticityAttribute();
    bool isSurfaceVorticityAttributeEnabled();

    /*
        Generate age attributes (in seconds) at fluid surface mesh vertices
    */
    void enableSurfaceAgeAttribute();
    void disableSurfaceAgeAttribute();
    bool isSurfaceAgeAttributeEnabled();
    double getSurfaceAgeAttributeRadius();
    void setSurfaceAgeAttributeRadius(double r);

    /*
        Generate lifetime remaining attributes (in seconds) at fluid surface mesh vertices
    */
    void enableSurfaceLifetimeAttribute();
    void disableSurfaceLifetimeAttribute();
    bool isSurfaceLifetimeAttributeEnabled();
    double getSurfaceLifetimeAttributeRadius();
    void setSurfaceLifetimeAttributeRadius(double r);
    double getSurfaceLifetimeAttributeDeathTime();
    void setSurfaceLifetimeAttributeDeathTime(double t);

    /*
        Generate whitewater proximity attributes (in number of local foam/bubble/spray particles) 
        at fluid surface mesh vertices. Dust particles are considered bubble particles in this attribute.
    */
    void enableSurfaceWhitewaterProximityAttribute();
    void disableSurfaceWhitewaterProximityAttribute();
    bool isSurfaceWhitewaterProximityAttributeEnabled();
    double getSurfaceWhitewaterProximityAttributeRadius();
    void setSurfaceWhitewaterProximityAttributeRadius(double r);

    /*
        Generate color attributes (in rgb) at fluid surface mesh vertices
    */
    void enableSurfaceColorAttribute();
    void disableSurfaceColorAttribute();
    bool isSurfaceColorAttributeEnabled();
    double getSurfaceColorAttributeRadius();
    void setSurfaceColorAttributeRadius(double r);

    void enableSurfaceColorAttributeMixing();
    void disableSurfaceColorAttributeMixing();
    bool isSurfaceColorAttributeMixingEnabled();
    double getSurfaceColorAttributeMixingRate();
    void setSurfaceColorAttributeMixingRate(double r);
    double getSurfaceColorAttributeMixingRadius();
    void setSurfaceColorAttributeMixingRadius(double r);
    void enableMixbox();
    void disableMixbox();
    bool isMixboxEnabled();

    /*
        Generate source ID attributes at fluid surface mesh vertices
    */
    void enableSurfaceSourceIDAttribute();
    void disableSurfaceSourceIDAttribute();
    bool isSurfaceSourceIDAttributeEnabled();

    /*
        Generate viscosity attributes at fluid surface mesh vertices
        Attributes for fluid particles will also be generated if 
        surface viscosity attributes are enabled.
    */
    void enableSurfaceViscosityAttribute();
    void disableSurfaceViscosityAttribute();
    bool isSurfaceViscosityAttributeEnabled();

    /*
        Generate density attributes at fluid surface mesh vertices
    */
    void enableSurfaceDensityAttribute();
    void disableSurfaceDensityAttribute();
    bool isSurfaceDensityAttributeEnabled();

    /*
        Generate velocity vector attributes at whitewater particles
    */
    void enableWhitewaterVelocityAttribute();
    void disableWhitewaterVelocityAttribute();
    bool isWhitewaterVelocityAttributeEnabled();

    /*
        Generate stable ID attributes at whitewater particles
    */
    void enableWhitewaterIDAttribute();
    void disableWhitewaterIDAttribute();
    bool isWhitewaterIDAttributeEnabled();

    /*
        Generate remaining lifetime attributes at whitewater particles
    */
    void enableWhitewaterLifetimeAttribute();
    void disableWhitewaterLifetimeAttribute();
    bool isWhitewaterLifetimeAttributeEnabled();

    /*
        Generate velocity vector, speed, vorticity vector,
        color, age, lifetime, whitewater proximity 
        attributes at fluid particles

    */
    void enableFluidParticleVelocityAttribute();
    void disableFluidParticleVelocityAttribute();
    bool isFluidParticleVelocityAttributeEnabled();

    void enableFluidParticleSpeedAttribute();
    void disableFluidParticleSpeedAttribute();
    bool isFluidParticleSpeedAttributeEnabled();

    void enableFluidParticleVorticityAttribute();
    void disableFluidParticleVorticityAttribute();
    bool isFluidParticleVorticityAttributeEnabled();

    void enableFluidParticleColorAttribute();
    void disableFluidParticleColorAttribute();
    bool isFluidParticleColorAttributeEnabled();

    void enableFluidParticleAgeAttribute();
    void disableFluidParticleAgeAttribute();
    bool isFluidParticleAgeAttributeEnabled();

    void enableFluidParticleLifetimeAttribute();
    void disableFluidParticleLifetimeAttribute();
    bool isFluidParticleLifetimeAttributeEnabled();

    void enableFluidParticleWhitewaterProximityAttribute();
    void disableFluidParticleWhitewaterProximityAttribute();
    bool isFluidParticleWhitewaterProximityAttributeEnabled();

    void enableFluidParticleSourceIDAttribute();
    void disableFluidParticleSourceIDAttribute();
    bool isFluidParticleSourceIDAttributeEnabled();

    void enableFluidParticleDensityAttribute();
    void disableFluidParticleDensityAttribute();
    bool isFluidParticleDensityAttributeEnabled();

    void enableFluidParticleUIDAttribute();
    void disableFluidParticleUIDAttribute();
    bool isFluidParticleUIDAttributeEnabled();

    void enableFluidParticleUIDAttributeReuse();
    void disableFluidParticleUIDAttributeReuse();
    bool isFluidParticleUIDAttributeReuseEnabled();


    int getCurrentFluidParticleUID();
    void setCurrentFluidParticleUID(int uid);

    /*
        Remove parts of mesh that are near the domain boundary

        Sides to remove in order: [-x, +x, -y, +y, -z, +z]
    */
    std::vector<bool> getRemoveSurfaceNearDomainSides();
    void setRemoveSurfaceNearDomainSides(std::vector<bool> active);

    void enableRemoveSurfaceNearDomain();
    void disableRemoveSurfaceNearDomain();
    bool isRemoveSurfaceNearDomainEnabled();
    int getRemoveSurfaceNearDomainDistance();
    void setRemoveSurfaceNearDomainDistance(int n);

    /*
        Enable/disable the simulation from saving fluid particles

        Disabled by default.
    */
    void enableFluidParticleDebugOutput();
    void disableFluidParticleDebugOutput();
    bool isFluidParticleDebugOutputEnabled();

    /*
        Enable/disable the simulation from saving internal obstacle mesh

        Disabled by default.
    */
    void enableInternalObstacleMeshOutput();
    void disableInternalObstacleMeshOutput();
    bool isInternalObstacleMeshOutputEnabled();

    /*
        Enable/disable the simulation from saving internal force field data

        Disabled by default.
    */
    void enableForceFieldDebugOutput();
    void disableForceFieldDebugOutput();
    bool isForceFieldDebugOutputEnabled();

    /*
        Enable/disable the simulation from simulating diffuse 
        material (spray/bubble/foam particles), and saving diffuse mesh data to disk.

        Diffuse material mesh data consists of triangle meshes containing only vertices.

        Disabled by default.
    */
    void enableDiffuseMaterialOutput();
    void disableDiffuseMaterialOutput();
    bool isDiffuseMaterialOutputEnabled();

    /*
        Enable/disable generation of new diffuse particles

        Enabled by default.
    */
    void enableDiffuseParticleEmission();
    void disableDiffuseParticleEmission();
    bool isDiffuseParticleEmissionEnabled();

    /*
        Enable/disable diffuse particle types

        All Enabled by default.
    */
    void enableDiffuseFoam();
    void disableDiffuseFoam();
    bool isDiffuseFoamEnabled();

    void enableDiffuseBubbles();
    void disableDiffuseBubbles();
    bool isDiffuseBubblesEnabled();

    void enableDiffuseSpray();
    void disableDiffuseSpray();
    bool isDiffuseSprayEnabled();

    void enableDiffuseDust();
    void disableDiffuseDust();
    bool isDiffuseDustEnabled();

    void enableBoundaryDiffuseDustEmission();
    void disableBoundaryDiffuseDustEmission();
    bool isBoundaryDustDiffuseEmissionEnabled();

    /*
        TODO: rename methods to clarify enabling/disabling output

        Enable/disable the simulation from saving diffuse bubble mesh data to disk.

        Enabled by default if diffuse material output is enabled
    */
    void enableBubbleDiffuseMaterial();
    void disableBubbleDiffuseMaterial();
    bool isBubbleDiffuseMaterialEnabled();

    /*
        Enable/disable the simulation from saving diffuse spray mesh data to disk.

        Enabled by default if diffuse material output is enabled
    */
    void enableSprayDiffuseMaterial();
    void disableSprayDiffuseMaterial();
    bool isSprayDiffuseMaterialEnabled();

    /*
        Enable/disable the simulation from saving diffuse foam mesh data to disk.

        Enabled by default if diffuse material output is enabled
    */
    void enableFoamDiffuseMaterial();
    void disableFoamDiffuseMaterial();
    bool isFoamDiffuseMaterialEnabled();

    /*
        Save diffuse material to disk as a single file per frame.

        Enabled by default.
    */
    void outputDiffuseMaterialAsSingleFile();

    /*
        Save diffuse material to disk as a multiple files per frame. Files
        will be separated by diffuse particle type (spray, bubble, foam).

        Disabled by default.
    */
    void outputDiffuseMaterialAsSeparateFiles();
    bool isDiffuseMaterialOutputAsSeparateFiles();

    /*
        Proportion of generated diffuse particle emitters (in range [0, 1])
    */
    double getDiffuseEmitterGenerationRate();
    void setDiffuseEmitterGenerationRate(double rate);

    /*
        Min/max emitter energy range
    */
    double getMinDiffuseEmitterEnergy();
    void setMinDiffuseEmitterEnergy(double e);
    double getMaxDiffuseEmitterEnergy();
    void setMaxDiffuseEmitterEnergy(double e);

    /*
        Min/max wavecrest curvature range
    */
    double getMinDiffuseWavecrestCurvature();
    void setMinDiffuseWavecrestCurvature(double k);
    double getMaxDiffuseWavecrestCurvature();
    void setMaxDiffuseWavecrestCurvature(double k);

    /*
        Min/max turbulence range
    */
    double getMinDiffuseTurbulence();
    void setMinDiffuseTurbulence(double e);
    double getMaxDiffuseTurbulence();
    void setMaxDiffuseTurbulence(double e);

    /*
        The number of diffuse particles simulated in the diffuse particle
        simulation will be limited by this number.
    */
    int getMaxNumDiffuseParticles();
    void setMaxNumDiffuseParticles(int n);

    /*
        Bounding box where diffuse particle emitters are allowed to be generated
    */
    AABB getDiffuseEmitterGenerationBounds();
    void setDiffuseEmitterGenerationBounds(AABB bbox);

    /*
        The minimum/maximum lifetime of a diffuse particle is spawned for in 
        seconds. Set this value to control how quickly/slowly diffuse
        particles fade from the simulation.
    */
    double getMinDiffuseParticleLifetime();
    void setMinDiffuseParticleLifetime(double lifetime);
    double getMaxDiffuseParticleLifetime();
    void setMaxDiffuseParticleLifetime(double lifetime);

    /*
        A random number of seconds in this range will be added or subtracted
        from the particle lifespan.
    */
    double getDiffuseParticleLifetimeVariance();
    void setDiffuseParticleLifetimeVariance(double variance);

    /*
        Lifetime modifiers for foam/bubble/spray/dust particle.
    */
    double getFoamParticleLifetimeModifier();
    void setFoamParticleLifetimeModifier(double modifier);
    double getBubbleParticleLifetimeModifier();
    void setBubbleParticleLifetimeModifier(double modifier);
    double getSprayParticleLifetimeModifier();
    void setSprayParticleLifetimeModifier(double modifier);
    double getDustParticleLifetimeModifier();
    void setDustParticleLifetimeModifier(double modifier);

    /*
        Diffuse particle emission rates.

        The diffuse particle simulator spawns particle emitters in areas
        where the fluid is likely to be aerated such as at wavecrests and
        in areas of high turbulence. The number of emitters spawned in an
        area is proportional to how sharp a wavecrest is, how turbulent
        the fluid is at a location, and how many MarkerParticles are in
        the simulation.
        
        The number of particles generated by an emitter is controlled by two 
        rates: wavecrest emission rate, and turbulence emission rate. An 
        emission rate is the number of particles generated by an emitter 
        per second. The wavecrest emission rate controls how many particles
        are generated by wavecrest emitters. The turbulence emission rate
        controls how many particles are generated by turbulence emitters.

        An important note to make about emission rates is that the number
        of particles generated scales as the simulator dimensions scale. 
        This means that a simulation with dimensions 128x128x128 will 
        generate about eight times as many diffuse particles than a
        simulation with a dimension of 64x64x64 when using the same rate
        values.
    */
    double getDiffuseParticleWavecrestEmissionRate();
    void setDiffuseParticleWavecrestEmissionRate(double r);
    double getDiffuseParticleTurbulenceEmissionRate();
    void setDiffuseParticleTurbulenceEmissionRate(double r);
    double getDiffuseParticleDustEmissionRate();
    void setDiffuseParticleDustEmissionRate(double r);

    /*
        Advection strength in range [0.0, 1.0] controls how much the foam moves 
        along with the motion of the fluid surface. High values cause tighter 
        streaks of foam that closely follow the fluid motion. Lower values will 
        cause more diffuse and spread out foam.
    */
    double getDiffuseFoamAdvectionStrength();
    void setDiffuseFoamAdvectionStrength(double s);

    /*
        Distance, in gridcells, from the middle to the top/bottom of the foam 
        layer, in range [0.0, 1.0]
    */
    double getDiffuseFoamLayerDepth();
    void setDiffuseFoamLayerDepth(double depth);

    /*
        Offset, in gridcells, of the foam layer in range [-1.0, 1.0]. A value
        of 1.0 will have the foam layer entirely above the fluid surface while
        a value of -1.0 will have the foam layer entirely below the fluid surface.
    */
    double getDiffuseFoamLayerOffset();
    void setDiffuseFoamLayerOffset(double offset);

    /*
        Preserve Foam

        Increase the lifespan of foam particles based on the local density of 
        foam particles, which can help create clumps and streaks of foam on the 
        liquid surface over time.
    */
    void enableDiffusePreserveFoam();
    void disableDiffusePreserveFoam();
    bool isDiffusePreserveFoamEnabled();
    double getDiffuseFoamPreservationRate();
    void setDiffuseFoamPreservationRate(double rate);
    double getMinDiffuseFoamDensity();
    void setMinDiffuseFoamDensity(double d);
    double getMaxDiffuseFoamDensity();
    void setMaxDiffuseFoamDensity(double d);

    /*
        Drag coefficient in range [0.0, 1.0] controls how quickly bubble/dust particles 
        are dragged with the fluid velocity. If set to 1, bubble particles will
        be immediately dragged into the flow direction of the fluid.
    */
    double getDiffuseBubbleDragCoefficient();
    void setDiffuseBubbleDragCoefficient(double d);

    double getDiffuseDustDragCoefficient();
    void setDiffuseDustDragCoefficient(double d);

    /*
        Bouyancy coefficient controls how quickly bubble/dust particles float towards
        the fluid surface. If set to a negative value, bubbles will sink away 
        from the fluid surface.
    */
    double getDiffuseBubbleBouyancyCoefficient();
    void setDiffuseBubbleBouyancyCoefficient(double b);

    double getDiffuseDustBouyancyCoefficient();
    void setDiffuseDustBouyancyCoefficient(double b);

    /*
        Amount of air resistance acting on a diffuse spray particle
    */
    double getDiffuseSprayDragCoefficient();
    void setDiffuseSprayDragCoefficient(double d);

    /*
        Scaling factor for spray velocity during emission
    */
    double getDiffuseSprayEmissionSpeed();
    void setDiffuseSprayEmissionSpeed(double value);

    /*
        Diffuse particle behaviour at limits

        LimitBehaviour::collide   - Collide with boundary limits
        LimitBehaviour::ballistic - Make particles follow ballistic trajectory
        LimitBehaviour::kill      - Kill any particles when outside boundary limits

        Active sides in order: [-x, +x, -y, +y, -z, +z]
    */

    LimitBehaviour getDiffuseFoamLimitBehaviour();
    void setDiffuseFoamLimitBehaviour(LimitBehaviour b);

    LimitBehaviour getDiffuseBubbleLimitBehaviour();
    void setDiffuseBubbleLimitBehaviour(LimitBehaviour b);

    LimitBehaviour getDiffuseSprayLimitBehaviour();
    void setDiffuseSprayLimitBehaviour(LimitBehaviour b);

    LimitBehaviour getDiffuseDustLimitBehaviour();
    void setDiffuseDustLimitBehaviour(LimitBehaviour b);

    std::vector<bool> getDiffuseFoamActiveBoundarySides();
    void setDiffuseFoamActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getDiffuseBubbleActiveBoundarySides();
    void setDiffuseBubbleActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getDiffuseSprayActiveBoundarySides();
    void setDiffuseSprayActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getDiffuseDustActiveBoundarySides();
    void setDiffuseDustActiveBoundarySides(std::vector<bool> active);

    /*
        Whitewater particle collisions at boundary

        Closed boundary in order: [-x, +x, -y, +y, -z, +z]
    */
    std::vector<bool> getFoamBoundaryCollisions();
    void setFoamBoundaryCollisions(std::vector<bool> active);

    std::vector<bool> getBubbleBoundaryCollisions();
    void setBubbleBoundaryCollisions(std::vector<bool> active);

    std::vector<bool> getSprayBoundaryCollisions();
    void setSprayBoundaryCollisions(std::vector<bool> active);

    std::vector<bool> getDustBoundaryCollisions();
    void setDustBoundaryCollisions(std::vector<bool> active);

    /*
        Default value of diffue particle influence. If influence at a location
        is not affected by an obstacle's influence, the amount of diffuse
        particles generated at the location will be scaled by this value
    */
    double getDiffuseObstacleInfluenceBaseLevel();
    void setDiffuseObstacleInfluenceBaseLevel(double level);

    /*
        Rate at which influence adjust towards the base level in amount of influence
        per second.
    */
    double getDiffuseObstacleInfluenceDecayRate();
    void setDiffuseObstacleInfluenceDecayRate(double decay);

    /*
        Maximum number of compute threads that can be launched
    */
    int getMaxThreadCount();
    void setMaxThreadCount(int n);

    /*
        Add a constant force such as gravity to the simulation.
    */
    void addBodyForce(double fx, double fy, double fz);
    void addBodyForce(vmath::vec3 f);
    vmath::vec3 getConstantBodyForce();

    /*
        Set force field weights depending on particle type.
    */
    double getForceFieldWeightFluidParticles();
    void setForceFieldWeightFluidParticles(double v);
    double getForceFieldWeightWhitewaterFoam();
    void setForceFieldWeightWhitewaterFoam(double v);
    double getForceFieldWeightWhitewaterBubble();
    void setForceFieldWeightWhitewaterBubble(double v);
    double getForceFieldWeightWhitewaterSpray();
    void setForceFieldWeightWhitewaterSpray(double v);
    double getForceFieldWeightWhitewaterDust();
    void setForceFieldWeightWhitewaterDust(double v);

    /*
        Remove all added body forces.
    */
    void resetBodyForce();

    /*
        Enable/Disable force field features
    */
    void enableForceFields();
    void disableForceFields();
    bool isForceFieldsEnabled();

    /*
        Get/Set reduction level for force field grid. Force field
        grid resolution is ceil(domain_resolution / reduction_level).
        Value must be >= 1.
    */
    int getForceFieldReductionLevel();
    void setForceFieldReductionLevel(int level);

    /*
        Return pointer to ForceFieldGrid object
    */
    ForceFieldGrid* getForceFieldGrid();

    /*
        Viscosity of the fluid. 
        Must be greater than or equal to zero. 
    */
    double getViscosity();
    void setViscosity(double v);

    /*
        Error tolerance of the viscosity solver.
        Recommended range around [1e-1, 1e-6].
    */
    double getViscositySolverErrorTolerance();
    void setViscositySolverErrorTolerance(double tol);

    /*
        Surface tension constant of the fluid.
        Must be greater than or equal to zero. 
    */
    double getSurfaceTension();
    void setSurfaceTension(double v);

    /*
        Sheet seeding fills in gaps between fluid particles
        with new particles to preserve thin sheets and splashes
    */
    void enableSheetSeeding();
    void disableSheetSeeding();
    bool isSheetSeedingEnabled();

    /*
        Controls how aggressively gaps between particles are filled.
        Must be in range [-1.0, 0.0].
    */
    double getSheetFillThreshold();
    void setSheetFillThreshold(double f);

    /*
        Controls rate at which new sheet particles are generated.
        Must be in range [0.0, 1.0].
    */
    double getSheetFillRate();
    void setSheetFillRate(double r);

    /*
        Friction on the domain boundary walls. 
        Must be in range [0.0,1.0]. 
    */
    double getBoundaryFriction();
    void setBoundaryFriction(double f);

    /*
        Courant Safety Factor - Maximum number of grid cells a particle can 
                                travel in a single time step. Faster particles
                                will cause multiple time steps to be taken to
                                limit distance.
    */
    int getCFLConditionNumber();
    void setCFLConditionNumber(int n);
    double getSurfaceTensionConditionNumber();
    void setSurfaceTensionConditionNumber(double n);

    /*
        If enabled, uses a larger particle kernel radius. Good for surface tension stability
        in thin strands on liquid or for high surface tension effects. Not good for chaotic
        fluid motion as this can lead to volume increase.
    */
    void enableSmoothSurfaceTensionKernel();
    void disableSmoothSurfaceTensionKernel();
    bool isSmoothSurfaceTensionKernelEnabled();

    /*
        Min/max time step calculations per frame update
    */
    int getMinTimeStepsPerFrame();
    void setMinTimeStepsPerFrame(int n);
    int getMaxTimeStepsPerFrame();
    void setMaxTimeStepsPerFrame(int n);

    /*
        Enable/Disable adaptive time stepping for obstacles/forcefields

        If enabled, obstacle/forcefield velocities are included in time step calculation.
        May improve the accuracy of fluid-solid/forcefield interaction for fast moving
        obstacles/forcefields.
    */
    void enableAdaptiveObstacleTimeStepping();
    void disableAdaptiveObstacleTimeStepping();
    bool isAdaptiveObstacleTimeSteppingEnabled();
    void enableAdaptiveForceFieldTimeStepping();
    void disableAdaptiveForceFieldTimeStepping();
    bool isAdaptiveForceFieldTimeSteppingEnabled();

    /*
        Enable/Disable removal of extreme velocities

        If enabled, the simulator will attempt to remove particles that cause
        the frame update to require more than the maximum number of allowed
        time steps.
    */
    void enableExtremeVelocityRemoval();
    void disableExtremeVelocityRemoval();
    bool isExtremeVelocityRemovalEnabled();

    /*
        Set FLIP (splashy) or APIC (swirly) velocity transfer method
    */
    void setVelocityTransferMethodFLIP();
    void setVelocityTransferMethodAPIC();
    bool isVelocityTransferMethodFLIP();
    bool isVelocityTransferMethodAPIC();

    /*
        Ratio of PIC to FLIP or PIC to APIC velocity update
    */
    double getPICFLIPRatio();
    void setPICFLIPRatio(double r);
    double getPICAPICRatio();
    void setPICAPICRatio(double r);

    /*
        Enable/Disable experimental optimization features
    */
    void enableExperimentalOptimizationFeatures();
    void disableExperimentalOptimizationFeatures();
    bool isExperimentalOptimizationFeaturesEnabled();

    /*
        Enable/Disable fracture obstacle optimization features
    */
    void enableFractureOptimization();
    void disableFractureOptimization();
    bool isFractureOptimizationEnabled();

    /*
        Enable/Disable precomputation of static obstacle MeshLevelSet
    */
    void enableStaticSolidLevelSetPrecomputation();
    void disableStaticSolidLevelSetPrecomputation();
    bool isStaticSolidLevelSetPrecomputationEnabled();

    /*
        Enable/Disable pre-allocation of temporary MeshLevelSet object
    */
    void enableTemporaryMeshLevelSet();
    void disableTemporaryMeshLevelSet();
    bool isTemporaryMeshLevelSetEnabled();

    /*
        Add a mesh shaped fluid source to the fluid domain. 
        See meshfluidsource.h header for more information.
    */
    void addMeshFluidSource(MeshFluidSource *source);

    /*
        Remove a mesh fluid source from the simulation.
    */
    void removeMeshFluidSource(MeshFluidSource *source);

    /*
        Remove all mesh fluid sources from the simulation.
    */
    void removeMeshFluidSources();

    /*
        Add a mesh obstacle to the simulation domain. 
        See meshobject.h header for more information.
    */
    void addMeshObstacle(MeshObject *obstacle);

    /*
        Remove a mesh obstacle from the simulation domain.
    */
    void removeMeshObstacle(MeshObject *obstacle);

    /*
        Remove all mesh obstacles from the simulation domain.
    */
    void removeMeshObstacles();

    /*
        Add a mesh fluid to the simulation domain. 
        See meshobject.h header for more information.
    */
    void addMeshFluid(MeshObject fluid);
    void addMeshFluid(MeshObject fluid, vmath::vec3 velocity);

    /*
        Add fluid cells to the simulation grid. Fluid cells will only be
        added if the current cell material is of type air.
    */
    void addFluidCells(std::vector<GridIndex> &indices);
    void addFluidCells(std::vector<GridIndex> &indices, vmath::vec3 velocity);
    void addFluidCells(std::vector<GridIndex> &indices, 
                       double vx, double vy, double vz);

    /*
        Add fluid cells with mask values that determine which subcell indices
        contain fluid to the simulation grid. Fluid cells will only be added if 
        the current cell material is of type air.

        if mask & 1   -> subcell(0, 0, 0) is fluid
        if mask & 2   -> subcell(1, 0, 0) is fluid
        if mask & 4   -> subcell(0, 1, 0) is fluid
        if mask & 8   -> subcell(1, 1, 0) is fluid
        if mask & 16  -> subcell(0, 0, 1) is fluid
        if mask & 32  -> subcell(1, 0, 1) is fluid
        if mask & 64  -> subcell(0, 1, 1) is fluid
        if mask & 128 -> subcell(1, 1, 1) is fluid
    */
    void addMaskedFluidCells(std::vector<GridIndex> &indices, 
                             std::vector<unsigned char> &masks);
    void addMaskedFluidCells(std::vector<GridIndex> &indices, 
                             std::vector<unsigned char> &masks, 
                             vmath::vec3 velocity);
    void addMaskedFluidCells(std::vector<GridIndex> &indices, 
                             std::vector<unsigned char> &masks,
                             double vx, double vy, double vz);

    /*
        Remove fluid cells from the simulation grid. When a fluid cell is
        removed, all marker particles within the fluid cell will be removed
        and the material will be replaced by air.
    */
    void removeFluidCells(std::vector<GridIndex> &indices);

    /*
        Returns the number of marker particles in the simulation. Marker particles
        track where the fluid is and carry velocity data.
    */
    unsigned int getNumMarkerParticles();

    /*
        Returns a vector of all marker particles in the simulation. Marker
        particles store position and velocity vectors.
    */
    std::vector<MarkerParticle> getMarkerParticles();
    std::vector<MarkerParticle> getMarkerParticles(int startidx, int endidx);

    /*
        Returns a vector of marker particle positions. If range indices
        are specified, the vector will contain positions ranging from 
        [startidx, endidx).
    */
    std::vector<vmath::vec3> getMarkerParticlePositions();
    std::vector<vmath::vec3> getMarkerParticlePositions(int startidx, int endidx);

    /*
        Returns a vector of marker particle velocities. If range indices
        are specified, the vector will contain velocities ranging from 
        [startidx, endidx).
    */
    std::vector<vmath::vec3> getMarkerParticleVelocities();
    std::vector<vmath::vec3> getMarkerParticleVelocities(int startidx, int endidx);

    /*
        Returns the number of diffuse particles in the simulation.
    */
    unsigned int getNumDiffuseParticles();

    /*
        Returns a vector of diffuse particle positions. If range indices
        are specified, the vector will contain positions ranging from 
        [startidx, endidx).
    */
    std::vector<vmath::vec3> getDiffuseParticlePositions();
    std::vector<vmath::vec3> getDiffuseParticlePositions(int startidx, int endidx);

    /*
        Returns a vector of diffuse particle velocities. If range indices
        are specified, the vector will contain velocities ranging from 
        [startidx, endidx).
    */
    std::vector<vmath::vec3> getDiffuseParticleVelocities();
    std::vector<vmath::vec3> getDiffuseParticleVelocities(int startidx, int endidx);

    /*
        Returns a vector of diffuse particle lifetimes. If range indices
        are specified, the vector will contain remaining lifetimes (in seconds) 
        ranging from [startidx, endidx).
    */
    std::vector<float> getDiffuseParticleLifetimes();
    std::vector<float> getDiffuseParticleLifetimes(int startidx, int endidx);

    /*
        Returns a vector of diffuse particle types. If range indices
        are specified, the vector will contain types ranging from 
        [startidx, endidx).

        Char value and corresponding diffuse particle type:

            0x00    Bubble
            0x01    Foam
            0x02    Spray
    */
    std::vector<char> getDiffuseParticleTypes();
    std::vector<char> getDiffuseParticleTypes(int startidx, int endidx);

    /*
        Returns a pointer to the MACVelocityField data structure.
        The MAC velocity field is a staggered velocity field that
        stores velocity components at the location of face centers.
    */
    MACVelocityField* getVelocityField();

    /*
        Retrieve output file data
    */
    std::vector<char>* getSurfaceData();
    std::vector<char>* getSurfacePreviewData();
    std::vector<char>* getSurfaceBlurData();
    std::vector<char>* getSurfaceVelocityAttributeData();
    std::vector<char>* getSurfaceVorticityAttributeData();
    std::vector<char>* getSurfaceSpeedAttributeData();
    std::vector<char>* getSurfaceAgeAttributeData();
    std::vector<char>* getSurfaceLifetimeAttributeData();
    std::vector<char>* getSurfaceWhitewaterProximityAttributeData();
    std::vector<char>* getSurfaceColorAttributeData();
    std::vector<char>* getSurfaceSourceIDAttributeData();
    std::vector<char>* getSurfaceViscosityAttributeData();
    std::vector<char>* getSurfaceDensityAttributeData();
    std::vector<char>* getDiffuseData();
    std::vector<char>* getDiffuseFoamData();
    std::vector<char>* getDiffuseBubbleData();
    std::vector<char>* getDiffuseSprayData();
    std::vector<char>* getDiffuseDustData();
    std::vector<char>* getDiffuseFoamBlurData();
    std::vector<char>* getDiffuseBubbleBlurData();
    std::vector<char>* getDiffuseSprayBlurData();
    std::vector<char>* getDiffuseDustBlurData();
    std::vector<char>* getWhitewaterFoamVelocityAttributeData();
    std::vector<char>* getWhitewaterBubbleVelocityAttributeData();
    std::vector<char>* getWhitewaterSprayVelocityAttributeData();
    std::vector<char>* getWhitewaterDustVelocityAttributeData();
    std::vector<char>* getWhitewaterFoamIDAttributeData();
    std::vector<char>* getWhitewaterBubbleIDAttributeData();
    std::vector<char>* getWhitewaterSprayIDAttributeData();
    std::vector<char>* getWhitewaterDustIDAttributeData();
    std::vector<char>* getWhitewaterFoamLifetimeAttributeData();
    std::vector<char>* getWhitewaterBubbleLifetimeAttributeData();
    std::vector<char>* getWhitewaterSprayLifetimeAttributeData();
    std::vector<char>* getWhitewaterDustLifetimeAttributeData();
    std::vector<char>* getFluidParticleData();
    std::vector<char>* getFluidParticleIDAttributeData();
    std::vector<char>* getFluidParticleVelocityAttributeData();
    std::vector<char>* getFluidParticleSpeedAttributeData();
    std::vector<char>* getFluidParticleVorticityAttributeData();
    std::vector<char>* getFluidParticleColorAttributeData();
    std::vector<char>* getFluidParticleAgeAttributeData();
    std::vector<char>* getFluidParticleLifetimeAttributeData();
    std::vector<char>* getFluidParticleViscosityAttributeData();
    std::vector<char>* getFluidParticleDensityAttributeData();
    std::vector<char>* getFluidParticleDensityAverageAttributeData();
    std::vector<char>* getFluidParticleWhitewaterProximityAttributeData();
    std::vector<char>* getFluidParticleSourceIDAttributeData();
    std::vector<char>* getFluidParticleUIDAttributeData();
    std::vector<char>* getFluidParticleDebugData();
    std::vector<char>* getInternalObstacleMeshData();
    std::vector<char>* getForceFieldDebugData();
    std::vector<char>* getLogFileData();
    FluidSimulationFrameStats getFrameStatsData();

    void getMarkerParticlePositionDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleVelocityDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleAffineXDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleAffineYDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleAffineZDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleAgeDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleLifetimeDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleColorDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleSourceIDDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleUIDDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleViscosityDataRange(int start_idx, int end_idx, char *data);
    void getMarkerParticleDensityDataRange(int start_idx, int end_idx, char *data);    void getMarkerParticleIDDataRange(int start_idx, int end_idx, char *data);
    void getDiffuseParticlePositionDataRange(int start_idx, int end_idx, char *data);
    void getDiffuseParticleVelocityDataRange(int start_idx, int end_idx, char *data);
    void getDiffuseParticleLifetimeDataRange(int start_idx, int end_idx, char *data);
    void getDiffuseParticleTypeDataRange(int start_idx, int end_idx, char *data);
    void getDiffuseParticleIdDataRange(int start_idx, int end_idx, char *data);

    void getMarkerParticlePositionData(char *data);
    void getMarkerParticleVelocityData(char *data);
    void getDiffuseParticlePositionData(char *data);
    void getDiffuseParticleVelocityData(char *data);
    void getDiffuseParticleLifetimeData(char *data);
    void getDiffuseParticleTypeData(char *data);
    void getDiffuseParticleIdData(char *data);
    unsigned int getMarkerParticlePositionDataSize();
    unsigned int getMarkerParticleVelocityDataSize();
    unsigned int getDiffuseParticlePositionDataSize();
    unsigned int getDiffuseParticleVelocityDataSize();
    unsigned int getDiffuseParticleLifetimeDataSize();
    unsigned int getDiffuseParticleTypeDataSize();
    unsigned int getDiffuseParticleIdDataSize();

    /*
        Load char data representing marker/diffuse particles into the simulator
    */
    void loadMarkerParticleData(FluidSimulationMarkerParticleData data);
    void loadMarkerParticleAffineData(FluidSimulationMarkerParticleAffineData data);
    void loadMarkerParticleAgeData(FluidSimulationMarkerParticleAgeData data);
    void loadMarkerParticleLifetimeData(FluidSimulationMarkerParticleLifetimeData data);
    void loadMarkerParticleColorData(FluidSimulationMarkerParticleColorData data);
    void loadMarkerParticleSourceIDData(FluidSimulationMarkerParticleSourceIDData data);
    void loadMarkerParticleUIDData(FluidSimulationMarkerParticleUIDData data);
    void loadMarkerParticleViscosityData(FluidSimulationMarkerParticleViscosityData data);
    void loadMarkerParticleDensityData(FluidSimulationMarkerParticleDensityData data);
    void loadMarkerParticleIDData(FluidSimulationMarkerParticleIDData data);
    void loadDiffuseParticleData(FluidSimulationDiffuseParticleData data);

private:   

    enum class VelocityTransferMethod : char { 
        FLIP = 0x00, 
        APIC = 0x01
    };

    enum class UIDAttribute : int { 
        ignore  = -2, 
        unset   = -1,
        invalid =  0
    };

    enum class UIDAttributeStatus : char { 
        unused   = 0x00, 
        reserved = 0x01,
        waiting  = 0x02,
        invalid  = 0x03
    };

    struct FluidMeshObject {
        MeshObject object;
        vmath::vec3 velocity;


        bool operator < (const FluidMeshObject& other) const
        {
            return (object._priority < other.object._priority);
        }

        bool operator > (const FluidMeshObject& other) const
        {
            return (object._priority > other.object._priority);
        }

        FluidMeshObject() {}
        FluidMeshObject(MeshObject obj, vmath::vec3 v) : 
                        object(obj), velocity(v) {}
    };

    struct FluidSimulationOutputData {
        std::vector<char> surfaceData;
        std::vector<char> surfacePreviewData;
        std::vector<char> surfaceBlurData;
        std::vector<char> surfaceVelocityAttributeData;
        std::vector<char> surfaceVorticityAttributeData;
        std::vector<char> surfaceSpeedAttributeData;
        std::vector<char> surfaceAgeAttributeData;
        std::vector<char> surfaceLifetimeAttributeData;
        std::vector<char> surfaceWhitewaterProximityAttributeData;
        std::vector<char> surfaceColorAttributeData;
        std::vector<char> surfaceSourceIDAttributeData;
        std::vector<char> surfaceViscosityAttributeData;
        std::vector<char> surfaceDensityAttributeData;
        std::vector<char> diffuseData;
        std::vector<char> diffuseFoamData;
        std::vector<char> diffuseBubbleData;
        std::vector<char> diffuseSprayData;
        std::vector<char> diffuseDustData;
        std::vector<char> diffuseFoamBlurData;
        std::vector<char> diffuseBubbleBlurData;
        std::vector<char> diffuseSprayBlurData;
        std::vector<char> diffuseDustBlurData;
        std::vector<char> whitewaterFoamVelocityAttributeData;
        std::vector<char> whitewaterBubbleVelocityAttributeData;
        std::vector<char> whitewaterSprayVelocityAttributeData;
        std::vector<char> whitewaterDustVelocityAttributeData;
        std::vector<char> whitewaterFoamIDAttributeData;
        std::vector<char> whitewaterBubbleIDAttributeData;
        std::vector<char> whitewaterSprayIDAttributeData;
        std::vector<char> whitewaterDustIDAttributeData;
        std::vector<char> whitewaterFoamLifetimeAttributeData;
        std::vector<char> whitewaterBubbleLifetimeAttributeData;
        std::vector<char> whitewaterSprayLifetimeAttributeData;
        std::vector<char> whitewaterDustLifetimeAttributeData;
        std::vector<char> fluidParticleData;
        std::vector<char> fluidParticleIDAttributeData;
        std::vector<char> fluidParticleVelocityAttributeData;
        std::vector<char> fluidParticleSpeedAttributeData;
        std::vector<char> fluidParticleVorticityAttributeData;
        std::vector<char> fluidParticleColorAttributeData;
        std::vector<char> fluidParticleAgeAttributeData;
        std::vector<char> fluidParticleLifetimeAttributeData;
        std::vector<char> fluidParticleViscosityAttributeData;
        std::vector<char> fluidParticleDensityAttributeData;
        std::vector<char> fluidParticleDensityAverageAttributeData;
        std::vector<char> fluidParticleWhitewaterProximityAttributeData;
        std::vector<char> fluidParticleSourceIDAttributeData;
        std::vector<char> fluidParticleUIDAttributeData;
        std::vector<char> fluidParticleDebugData;
        std::vector<char> internalObstacleMeshData;
        std::vector<char> forceFieldDebugData;
        std::vector<char> logfileData;
        FluidSimulationFrameStats frameData;
        bool isInitialized = false;
    };

    struct MarkerParticleLoadData {
        FragmentedVector<MarkerParticle> particles;
    };

    struct MarkerParticleAffineLoadData {
        FragmentedVector<MarkerParticleAffine> particles;
    };

    struct MarkerParticleAgeLoadData {
        FragmentedVector<MarkerParticleAge> particles;
    };

    struct MarkerParticleLifetimeLoadData {
        FragmentedVector<MarkerParticleLifetime> particles;
    };

    struct MarkerParticleColorLoadData {
        FragmentedVector<MarkerParticleColor> particles;
    };

    struct MarkerParticleSourceIDLoadData {
        FragmentedVector<MarkerParticleSourceID> particles;
    };

    struct MarkerParticleUIDLoadData {
        FragmentedVector<MarkerParticleUID> particles;
    };

    struct MarkerParticleViscosityLoadData {
        FragmentedVector<MarkerParticleViscosity> particles;
    };

    struct MarkerParticleDensityLoadData {
        FragmentedVector<MarkerParticleDensity> particles;
    };

    struct MarkerParticleIDLoadData {
        FragmentedVector<MarkerParticleID> particles;
    };


    struct MarkerParticleAttributes {
        int sourceID = 0;
        float sourceViscosity = 0.0f;
        float sourceDensity = 0.0f;
        float sourceLifetime = 0.0f;
        float sourceLifetimeVariance = 0.0f;
        vmath::vec3 sourceColor;
    };

    struct DiffuseParticleLoadData {
        FragmentedVector<DiffuseParticle> particles;
    };

    struct TimingData {
        double updateObstacleObjects = 0.0;
        double updateLiquidLevelSet = 0.0;
        double advectVelocityField = 0.0;
        double saveVelocityField = 0.0;
        double calculateFluidCurvatureGrid = 0.0;
        double applyBodyForcesToVelocityField = 0.0;
        double applyViscosityToVelocityField = 0.0;
        double pressureSolve = 0.0;
        double constrainVelocityFields = 0.0;
        double updateDiffuseMaterial = 0.0;
        double updateSheetSeeding = 0.0;
        double updateMarkerParticleVelocities = 0.0;
        double deleteSavedVelocityField = 0.0;
        double advanceMarkerParticles = 0.0;
        double updateFluidObjects = 0.0;
        double outputNonMeshSimulationData = 0.0;
        double outputMeshSimulationData = 0.0;
        double frameTime = 0.0;

        void normalizeTimes() {
            double total = updateObstacleObjects +
                           updateLiquidLevelSet +
                           advectVelocityField +
                           saveVelocityField +
                           calculateFluidCurvatureGrid +
                           applyBodyForcesToVelocityField +
                           applyViscosityToVelocityField +
                           pressureSolve +
                           constrainVelocityFields +
                           updateDiffuseMaterial +
                           updateSheetSeeding +
                           updateMarkerParticleVelocities +
                           deleteSavedVelocityField +
                           advanceMarkerParticles +
                           updateFluidObjects +
                           outputNonMeshSimulationData +
                           outputMeshSimulationData;
            double factor = 1.0;
            if (total > 1e-6) {
                factor = frameTime / total;
            }

            updateObstacleObjects          *= factor;
            updateLiquidLevelSet           *= factor;
            advectVelocityField            *= factor;
            saveVelocityField              *= factor;
            calculateFluidCurvatureGrid    *= factor;
            applyBodyForcesToVelocityField *= factor;
            applyViscosityToVelocityField  *= factor;
            pressureSolve                  *= factor;
            constrainVelocityFields        *= factor;
            updateDiffuseMaterial          *= factor;
            updateSheetSeeding             *= factor;
            updateMarkerParticleVelocities *= factor;
            deleteSavedVelocityField       *= factor;
            advanceMarkerParticles         *= factor;
            updateFluidObjects             *= factor;
            outputNonMeshSimulationData    *= factor;
            outputMeshSimulationData       *= factor;
        }
    };

    struct FluidParticleDataFFP3 {
        size_t numFluidParticles = 0;
        size_t numFluidParticlesSurface = 0;
        size_t numFluidParticlesBoundary = 0;
        size_t numFluidParticlesInterior = 0;
        size_t idLimit = 0;
        std::vector<unsigned int> idHeaderDataSurface;
        std::vector<unsigned int> idHeaderDataBoundary;
        std::vector<unsigned int> idHeaderDataInterior;
        std::vector<int> sortedFluidParticleIndexTable;
    };

    /*
        Initializing the Fluid Simulator
    */
    void _initializeLogFile();
    void _initializeSimulationGrids(int isize, int jsize, int ksize, double dx);
    void _initializeForceFieldGrid(int isize, int jsize, int ksize, double dx);
    void _initializeAttributeGrids(int isize, int jsize, int ksize);
    void _initializeParticleSystems();
    void _initializeSimulation();
    void _initializeParticleRadii();
    void _initializeRandomGenerator();
    double _getMarkerParticleJitter();
    vmath::vec3 _jitterMarkerParticlePosition(vmath::vec3 p, double jitter);
    void _addMarkerParticles(std::vector<MarkerParticle> &particles, MarkerParticleAttributes attributes);
    void _upscaleParticleData();
    void _loadParticles();
    void _loadMarkerParticles(MarkerParticleLoadData &particleData,
                              MarkerParticleAffineLoadData &affineData,
                              MarkerParticleAgeLoadData &ageData,
                              MarkerParticleLifetimeLoadData &lifetimeData,
                              MarkerParticleColorLoadData &colorData,
                              MarkerParticleSourceIDLoadData &sourceIDData,
                              MarkerParticleViscosityLoadData &viscosityData,
                              MarkerParticleDensityLoadData &vdensityData,
                              MarkerParticleIDLoadData &idData,
                              MarkerParticleUIDLoadData &UIDData);
    void _loadDiffuseParticles(DiffuseParticleLoadData &data);
    void _initializeFluidParticleUIDAttributeReuseData();

    /*
        Advancing the State of the Fluid Simulation
    */
    double _calculateNextTimeStep(double dt);
    double _getFrameInterpolation();
    double _getMaximumMeshObjectFluidVelocity(MeshObject *object, 
                                              vmath::vec3 fluidVelocity);
    double _predictMaximumMarkerParticleSpeed(double dt);
    double _getMaximumMarkerParticleSpeed();
    double _getMaximumObstacleSpeed(double dt);
    void _updateTimingData();
    void _logStepInfo();
    void _logFrameInfo();
    void _logGreeting();
    bool _isFluidGeneratingThisFrame();
    bool _isFluidOrWhitewaterInSimulation();
    bool _isFluidInSimulation();
    void _stepFluid(double dt);

    /*
        Update Solid Material
    */
    TriangleMesh _getTriangleMeshFromAABB(AABB bbox);
    AABB _getBoundaryAABB();
    TriangleMesh _getBoundaryTriangleMesh();
    void _addAnimatedObjectsToSolidSDF(double dt);
    void _updatePrecomputedSolidLevelSet(double dt, std::vector<MeshObjectStatus> &objectStatus);
    void _addStaticObjectsToSolidSDF(double dt, std::vector<MeshObjectStatus> &objectStatus);
    void _addStaticObjectsToSDF(double dt, MeshLevelSet &sdf);
    bool _isSolidStateChanged(std::vector<MeshObjectStatus> &objectStatus);
    bool _isStaticSolidStateChanged(std::vector<MeshObjectStatus> &objectStatus);
    std::vector<MeshObjectStatus> _getSolidObjectStatus();
    void _updateSolidLevelSet(double dt);
    void _updateObstacles(double dt);
    void _updateNearSolidGrid();
    void _initializeNearSolidGridThread(int startidx, int endidx);
    void _resolveSolidLevelSetUpdateCollisionsThread(int startidx, int endidx);
    void _resolveSolidLevelSetUpdateCollisions();
    void _updateObstacleObjects(double dt);
    void _launchUpdateObstacleObjectsThread(double dt);
    void _joinUpdateObstacleObjectsThread();

    /*
        Update Fluid Levelset
    */
    void _launchUpdateLiquidLevelSetThread();
    void _joinUpdateLiquidLevelSetThread();
    void _updateLiquidLevelSet();

    /*
        Advect Velocity Field
    */
    void _launchAdvectVelocityFieldThread();
    void _joinAdvectVelocityFieldThread();
    void _advectVelocityField();
    void _saveVelocityField();
    void _deleteSavedVelocityField();

    /*
        Calculate Fluid Curvature
    */
    void _calculateFluidCurvatureGridThread();
    void _launchCalculateFluidCurvatureGridThread();
    void _joinCalculateFluidCurvatureGridThread();

    /*
        Apply Body Forces
    */
    void _applyBodyForcesToVelocityField(double dt);
    vmath::vec3 _getConstantBodyForce();
    void _getInflowConstrainedVelocityComponents(ValidVelocityComponentGrid &ex);
    void _updateForceFieldGrid(double dt);
    void _applyConstantBodyForces(ValidVelocityComponentGrid &ex, double dt);
    void _applyForceFieldGridForces(ValidVelocityComponentGrid &ex, double dt);
    void _applyForceFieldGridForcesMT(ValidVelocityComponentGrid &ex, double dt, int dir);
    void _applyForceFieldGridForcesThread(int startidx, int endidx, 
                                          ValidVelocityComponentGrid *ex, double dt, int dir);

    /*
        Viscosity Solve
    */
    void _applyViscosityToVelocityField(double dt);

    /*
        Pressure Solve
    */
    void _updateWeightGrid();
    void _updateWeightGridMT(int dir);
    void _updateWeightGridThread(int startidx, int endidx, int dir);
    void _pressureSolve(double dt);

    /*
        Extrapolate Velocity Field
    */
    void _extrapolateFluidVelocities(MACVelocityField &MACGrid,
                                     ValidVelocityComponentGrid &validVelocities);

    /*
        Constrain Velocity Field
    */
    float _getFaceFrictionU(GridIndex g);
    float _getFaceFrictionV(GridIndex g);
    float _getFaceFrictionW(GridIndex g);
    void _constrainVelocityField(MACVelocityField &MACGrid);
    void _constrainVelocityFieldMT(MACVelocityField &MACGrid, int dir);
    void _constrainVelocityFieldThread(int startidx, int endidx, 
                                       MACVelocityField *vfield, int dir);
    void _constrainVelocityFields();

    /*
        Update Diffuse Particle Simulation
    */
    void _updateDiffuseMaterial(double dt);
    void _updateDiffuseInfluenceGrid(double dt);

    /*
        Update MarkerParticle Velocities
    */
    void _updateMarkerParticleVelocities();
    void _updateMarkerParticleVelocitiesThread();
    void _updatePICFLIPMarkerParticleVelocitiesThread(int startidx, int endidx);
    void _updatePICAPICMarkerParticleVelocitiesThread(int startidx, int endidx);
    void _getIndicesAndGradientWeights(vmath::vec3 p, GridIndex indices[8], vmath::vec3 weights[8], int dir);
    void _constrainMarkerParticleVelocities();
    void _constrainMarkerParticleVelocities(MeshFluidSource *inflow);

    /*
        Update Marker Particle Attributes
    */

    void _updateMarkerParticleVelocityAttributeGrid();
    void _updateMarkerParticleVelocityBasedAttributes();
    void _updateMarkerParticleVorticityAttributeGrid();
    void _updateMarkerParticleAgeAttributeGrid(Array3d<float> &ageAttributeGrid,
                                               Array3d<bool> &ageAttributeValidGrid);
    void _updateMarkerParticleAgeAttribute(double dt);
    void _updateMarkerParticleLifetimeAttributeGrid(Array3d<float> &lifetimeAttributeGrid,
                                               Array3d<bool> &lifetimeAttributeValidGrid);
    void _updateMarkerParticleLifetimeAttribute(double dt);
    void _updateMarkerParticleWhitewaterProximityAttributeGrid(Array3d<vmath::vec3> &whitewaterProximityAttributeGrid,
                                                               Array3d<bool> &whitewaterProximityAttributeValidGrid);
    void _updateMarkerParticleWhitewaterProximityAttribute();
    void _updateMarkerParticleViscosityAttributeGrid(Array3d<float> &viscosityAttributeGrid,
                                                     Array3d<bool> &viscosityAttributeValidGrid);
    void _updateMarkerParticleViscosityAttribute();
    void _updateMarkerParticleDensityAttributeGrid(Array3d<float> &densityAttributeGrid,
                                                     Array3d<bool> &densityAttributeValidGrid);
    void _updateMarkerParticleDensityAttribute();
    void _updateMarkerParticleColorAttributeGrid(Array3d<float> &colorAttributeGridR,
                                                 Array3d<float> &colorAttributeGridG,
                                                 Array3d<float> &colorAttributeGridB,
                                                 Array3d<bool> &colorAttributeValidGrid);
    void _updateMarkerParticleColorAttributeMixing(double dt);
    vmath::vec3 _RGBToHSV(vmath::vec3 in);
    vmath::vec3 _HSVToRGB(vmath::vec3 in);
    void _updateMarkerParticleColorAttributeMixingThread(int startidx, int endidx, double dt,
                                                         SpatialPointGrid *pointGrid,
                                                         std::vector<vmath::vec3> *colors,
                                                         std::vector<vmath::vec3> *colorsNew,
                                                         std::vector<bool> *colorsNewValid);
    void _updateMarkerParticleColorAttribute(double dt);
    void _updateMarkerParticleUIDAttribute();
    void _updateMarkerParticleAttributes(double dt);

    /*
        Advance MarkerParticles
    */
    void _advanceMarkerParticles(double dt);
    void _advanceMarkerParticlesThread(double dt, int startidx, int endidx,
                                       std::vector<vmath::vec3> *positions,
                                       std::vector<vmath::vec3> *output);
    vmath::vec3 _RK3(vmath::vec3 p0, double dt);

    void _resolveMarkerParticleCollisions(int startidx, int endidx,
                                          std::vector<vmath::vec3> &positionsOld, 
                                          std::vector<vmath::vec3> &positionsNew);
    vmath::vec3 _resolveCollision(vmath::vec3 oldp, vmath::vec3 newp,
                                  AABB &boundary);
    float _getMarkerParticleSpeedLimit(double dt);
    void _removeMarkerParticles(double dt);

    /*
        #. Update Fluid Objects
    */
    void _updateFluidObjects();
    void _updateAddedFluidMeshObjectQueue();
    void _addNewFluidCells(std::vector<GridIndex> &cells, 
                           vmath::vec3 velocity,
                           MeshLevelSet &meshsdf,
                           vmath::vec3 sdfoffset,
                           MarkerParticleAttributes attributes,
                           ParticleMaskGrid &maskgrid);
    void _addNewFluidCells(std::vector<GridIndex> &cells, 
                           vmath::vec3 velocity,
                           RigidBodyVelocity rvelocity,
                           MeshLevelSet &meshsdf,
                           vmath::vec3 sdfoffset,
                           MarkerParticleAttributes attributes,
                           ParticleMaskGrid &maskgrid);
    void _addNewFluidCells(std::vector<GridIndex> &cells, 
                           vmath::vec3 velocity,
                           VelocityFieldData *vdata,
                           MeshLevelSet &meshsdf,
                           vmath::vec3 sdfoffset,
                           MarkerParticleAttributes attributes,
                           ParticleMaskGrid &maskgrid);
    void _addNewFluidCellsAABB(AABB bbox, 
                               vmath::vec3 velocity,
                               MarkerParticleAttributes attributes,
                               ParticleMaskGrid &maskgrid);
    void _addNewFluidCellsThread(int startidx, int endidx,
                                 std::vector<GridIndex> *cells, 
                                 MeshLevelSet *meshSDF,
                                 vmath::vec3 sdfoffset,
                                 std::vector<vmath::vec3> *particles);
        
    void _updateMeshFluidSources();
    void _updateInflowMeshFluidSources();
    void _updateOutflowMeshFluidSources();
    void _updateOutflowBoundary();
    void _updateInflowMeshFluidSource(MeshFluidSource *source, ParticleMaskGrid &maskgrid);
    void _updateOutflowMeshFluidSource(MeshFluidSource *source);
    int _getNumFluidCells();
    void _updateSheetSeeding();

    /*
        Output Simulation Data
    */
    void _outputSimulationData();
    void _generateSurfaceMotionBlurData(TriangleMesh &surface, MACVelocityField *vfield);
    void _generateSurfaceVelocityAttributeData(TriangleMesh &surface, MACVelocityField *vfield);
    void _generateSurfaceVorticityAttributeData(TriangleMesh &surface);
    void _generateSurfaceAgeAttributeData(TriangleMesh &surface);
    void _generateSurfaceLifetimeAttributeData(TriangleMesh &surface);
    void _generateSurfaceWhitewaterProximityAttributeData(TriangleMesh &surface);
    void _generateSurfaceColorAttributeData(TriangleMesh &surface);
    void _generateSurfaceSourceIDAttributeData(TriangleMesh &surface, std::vector<vmath::vec3> &positions, std::vector<int> *sourceID);
    void _generateSurfaceViscosityAttributeData(TriangleMesh &surface);
    void _generateSurfaceDensityAttributeData(TriangleMesh &surface);
    void _outputSurfaceMeshThread(std::vector<vmath::vec3> *particles,
                                  MeshLevelSet *solidSDF,
                                  MACVelocityField *vfield,
                                  std::vector<int> *sourceID);
    void _updateMeshingVolumeSDF();
    void _applyMeshingVolumeToSDF(MeshLevelSet *sdf);
    void _filterParticlesOutsideMeshingVolume(std::vector<vmath::vec3> *particles);
    void _launchOutputSurfaceMeshThread();
    void _joinOutputSurfaceMeshThread();
    void _outputDiffuseMaterial();

    template<class T>
    void _generateFluidParticleFFP3FileData(std::vector<T> *attribute, FluidParticleDataFFP3 &dataFFP3, 
                                            std::vector<char> &filedata) {

        std::vector<T> attributeSorted(dataFFP3.numFluidParticles);
        for (size_t i = 0; i < dataFFP3.sortedFluidParticleIndexTable.size(); i++) {
            int index = dataFFP3.sortedFluidParticleIndexTable[i];
            if (index == -1) {
                continue;
            }
            attributeSorted[index] = attribute->at(i);
        }

        size_t infoHeaderBytes = 4 * sizeof(unsigned int);
        size_t idDataHeaderBytes = dataFFP3.idLimit * 3 * sizeof(unsigned int);
        size_t headerBytes = infoHeaderBytes + idDataHeaderBytes;
        size_t attributeDataBytes = dataFFP3.numFluidParticles * sizeof(T);
        size_t fileBytes = headerBytes + attributeDataBytes;

        filedata = std::vector<char>(fileBytes, 0);
        unsigned int *uintData = (unsigned int*)filedata.data();

        uintData[0] = dataFFP3.numFluidParticlesSurface;
        uintData[1] = dataFFP3.numFluidParticlesBoundary;
        uintData[2] = dataFFP3.numFluidParticlesInterior;
        uintData[3] = dataFFP3.idLimit;
        size_t idHeaderDataOffset = 4;

        for (size_t i = 0; i < dataFFP3.idLimit; i++) {
            uintData[idHeaderDataOffset + 3 * i + 0] = dataFFP3.idHeaderDataSurface[i];
            uintData[idHeaderDataOffset + 3 * i + 1] = dataFFP3.idHeaderDataBoundary[i];
            uintData[idHeaderDataOffset + 3 * i + 2] = dataFFP3.idHeaderDataInterior[i];
        }

        std::memcpy(filedata.data() + headerBytes, (char *)attributeSorted.data(), attributeDataBytes);
    }

    void _classifyFluidParticleTypes(ParticleSystem &fluidParticles, 
                                     std::vector<MarkerParticleType> &fluidParticleTypes);
    void _classifyFluidParticleTypesThread(int startidx, int endidx,
                                           std::vector<vmath::vec3> *positions,
                                           Array3d<bool> *isBoundaryCell,
                                           std::vector<MarkerParticleType> *fluidParticleTypes);
    void _generateFluidParticleDataFFP3(ParticleSystem &fluidParticles, FluidParticleDataFFP3 &dataFFP3);
    void _outputFluidParticles();

    float _calculateParticleSpeedPercentileThreshold(float pct);
    void _outputFluidParticleDebug();
    void _outputInternalObstacleMesh();
    void _outputForceFieldDebugData();
    std::string _numberToString(int number);
    std::string _getFrameString(int number);
    void _getTriangleMeshFileData(TriangleMesh &mesh, std::vector<char> &data);
    void _getForceFieldDebugFileData(std::vector<ForceFieldDebugNode> &debugNodes, 
                                     std::vector<char> &data);
    void _getFluidParticleDebugFileData(std::vector<vmath::vec3> &particles, 
                                        std::vector<int> &binStarts, 
                                        std::vector<float> &binSpeeds, 
                                        std::vector<char> &outdata);
    void _smoothSurfaceMesh(TriangleMesh &mesh);
    void _invertContactNormals(TriangleMesh &mesh);
    void _removeMeshNearDomain(TriangleMesh &mesh);
    void _computeDomainBoundarySDF(MeshLevelSet *sdf);
    void _generateOutputSurface(TriangleMesh &surface, TriangleMesh &preview,
                                  std::vector<vmath::vec3> *particles,
                                  MeshLevelSet *soldSDF);
    void _outputSimulationLogFile();


    /*
        Misc Methods
    */
    template<class T>
    void _removeItemsFromVector(T &items, std::vector<bool> &isRemoved) {
        FLUIDSIM_ASSERT(items.size() == isRemoved.size());

        int currentidx = 0;
        for (unsigned int i = 0; i < items.size(); i++) {
            if (!isRemoved[i]) {
                items[currentidx] = items[i];
                currentidx++;
            }
        }

        int numRemoved = items.size() - currentidx;
        for (int i = 0; i < numRemoved; i++) {
            items.pop_back();
        }
        items.shrink_to_fit();
    }

    inline double _randomDouble(double min, double max) {
        return min + _random(_randomSeed) * (max - min);
    }

    int _getFluidParticleOutputIDLimit() {
        return (int)std::round(_fluidParticleIDLimit * _fluidParticleOutputAmount);
    }

    inline uint16_t _generateRandomFluidParticleID() {
        return (uint16_t)_fluidParticleRandomID(_fluidParticleRandomSeed);
    }

    inline int _generateFluidParticleUID() {
        int id = _currentFluidParticleUID;
        _currentFluidParticleUID++;
        return id;
    }

    template<class T>
    std::string _toString(T item) {
        std::ostringstream sstream;
        sstream << item;

        return sstream.str();
    }

    template <typename T>
    T _clamp(const T& n, const T& lower, const T& upper) {
        return std::max(lower, std::min(n, upper));
    }

    // Simulator grid dimensions and cell size
    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    // Initialization
    bool _isSimulationInitialized = false;
    bool _isUpscalingOnInitializationEnabled = false;
    int _upscalingPreviousIsize = 0.0;
    int _upscalingPreviousJsize = 0.0;
    int _upscalingPreviousKsize = 0.0;
    double _upscalingPreviousCellSize = 0.0;

    // Update
    int _currentFrame = 0;
    int _timelineFrameStart = 0;
    int _timelineFrameEnd = 0;
    int _currentFrameTimeStepNumber = 0;
    double _currentFrameTimeStep = 0.0;
    double _currentFrameDeltaTime = 0.0;
    double _currentFrameDeltaTimeRemaining = 0.0;
    int _currentNumFluidCells = 0;
    int _currentPerformanceScore = 0;
    int _currentExtremeVelocityParticlesRemoved = 0;
    bool _isLastFrameTimeStep = false;
    bool _isZeroLengthDeltaTime = false;
    bool _isSkippedFrame = false;
    int _minFrameTimeSteps = 1;
    int _maxFrameTimeSteps = 6;
    double _totalSimulationTime = 0;
    bool _isCurrentFrameFinished = true;
    double _CFLConditionNumber = 5.0;
    double _surfaceTensionConditionNumber = 10.0;
    LogFile _logfile;

    // Update fluid material
    ParticleLevelSet _liquidSDF;
    std::vector<MeshFluidSource*> _meshFluidSources;
    ParticleSystem _markerParticles;
    std::vector<FluidMeshObject> _addedFluidMeshObjectQueue;
    double _markerParticleJitterFactor = 0.0;
    bool _isJitterSurfaceMarkerParticlesEnabled = false;
    int _liquidLevelSetExactBand = 3;

    bool _isMarkerParticleLoadPending = false;
    bool _isDiffuseParticleLoadPending = false;
    std::vector<MarkerParticleLoadData> _markerParticleLoadQueue;
    std::vector<MarkerParticleAffineLoadData> _markerParticleAffineLoadQueue;
    std::vector<MarkerParticleAgeLoadData> _markerParticleAgeLoadQueue;
    std::vector<MarkerParticleLifetimeLoadData> _markerParticleLifetimeLoadQueue;
    std::vector<MarkerParticleColorLoadData> _markerParticleColorLoadQueue;
    std::vector<MarkerParticleSourceIDLoadData> _markerParticleSourceIDLoadQueue;
    std::vector<MarkerParticleUIDLoadData> _markerParticleUIDLoadQueue;
    std::vector<MarkerParticleViscosityLoadData> _markerParticleViscosityLoadQueue;
    std::vector<MarkerParticleDensityLoadData> _markerParticleDensityLoadQueue;
    std::vector<MarkerParticleIDLoadData> _markerParticleIDLoadQueue;
    std::vector<DiffuseParticleLoadData> _diffuseParticleLoadQueue;

    // Update obstacles
    std::vector<MeshObject*> _obstacles;
    std::thread _updateObstacleObjectsThread;
    Array3d<bool> _nearSolidGrid;
    int _nearSolidGridCellSizeFactor = 3;
    double _nearSolidGridCellSize = 0.0f;
    bool _isFractureOptimizationEnabled = false;

    // Compute levelset signed distance field
    MeshLevelSet _solidSDF;
    MeshLevelSet _staticSolidSDF;
    MeshLevelSet _tempSolidSDF;
    MeshObject _domainMeshObject;
    float _domainBoundaryFriction = 0.0f;
    bool _isStaticSolidLevelSetPrecomputed = false;
    bool _isTempSolidLevelSetEnabled = true;
    bool _isSolidLevelSetUpToDate = false;
    bool _isPrecomputedSolidLevelSetUpToDate = false;
    int _solidLevelSetExactBand = 3;
    bool _isSmoothSurfaceTensionKernelEnabled = false;
    double _liquidSDFParticleScale = 1.0;
    double _liquidSDFParticleRadius = 0.0;
    double _liquidSDFSurfaceTensionParticleScale = 2.0;
    std::thread _updateLiquidLevelSetThread;

    // Fluid particle output
    bool _isFluidParticleOutputEnabled = false;
    bool _isFluidParticleIDAttributeEnabled = false;
    bool _isFluidParticleSurfaceOutputEnabled = true;
    double _fluidParticleOutputAmount = 1.0;
    bool _isFluidParticleBoundaryOutputEnabled = true;
    bool _isFluidParticleInteriorOutputEnabled = true;
    int _fluidParticleSourceIDBlacklist = true;

    bool _isFluidParticleVelocityAttributeEnabled = false;
    bool _isFluidParticleSpeedAttributeEnabled = false;
    bool _isFluidParticleVorticityAttributeEnabled = false;
    bool _isFluidParticleSourceColorAttributeEnabled = false;
    bool _isFluidParticleAgeAttributeEnabled = false;
    bool _isFluidParticleLifetimeAttributeEnabled = false;
    bool _isFluidParticleWhitewaterProximityAttributeEnabled = false;
    bool _isFluidParticleSourceIDAttributeEnabled = false;
    bool _isFluidParticleDensityAttributeEnabled = false;
    bool _isFluidParticleUIDAttributeEnabled = false;
    bool _isFluidParticleUIDAttributeReuseEnabled = false;

    float _fluidParticleSurfaceWidth = 0.90f;    // In # of voxels
    int _fluidParticleBoundaryWidth = 1;        // In # of voxels

    int _fluidParticleIDLimit = 65536;    // max uint16_t (2^16 = 65536)
    std::random_device _fluidParticleRandomDevice;
    std::mt19937 _fluidParticleRandomSeed;
    std::uniform_int_distribution<> _fluidParticleRandomID;

    int _currentFluidParticleUID = 1;
    std::vector<UIDAttributeStatus> _uidStatusFramePrevious;
    std::vector<UIDAttributeStatus> _uidStatusFrameCurrent;

    // Reconstruct output fluid surface
    bool _isSurfaceMeshReconstructionEnabled = true;
    bool _isPreviewSurfaceMeshEnabled = false;
    bool _isInvertedContactNormalsEnabled = false;
    bool _isSurfaceMotionBlurEnabled = false;
    bool _isWhitewaterMotionBlurEnabled = false;
    bool _isSurfaceVelocityAttributeEnabled = false;
    bool _isWhitewaterVelocityAttributeEnabled = false;
    bool _isSurfaceVorticityAttributeEnabled = false;
    bool _isSurfaceSpeedAttributeEnabled = false;
    bool _isSurfaceAgeAttributeEnabled = false;
    bool _isSurfaceLifetimeAttributeEnabled = false;
    float _surfaceLifetimeAttributeDeathTime = 0.0f;
    bool _isSurfaceWhitewaterProximityAttributeEnabled = false;
    bool _isSurfaceSourceColorAttributeEnabled = false;
    bool _isSurfaceSourceColorAttributeMixingEnabled = false;
    bool _isSurfaceSourceIDAttributeEnabled = false;
    bool _isSurfaceSourceViscosityAttributeEnabled = false;
    bool _isSurfaceDensityAttributeEnabled = false;
    bool _isWhitewaterIDAttributeEnabled = false;
    bool _isWhitewaterLifetimeAttributeEnabled = false;
    double _contactThresholdDistance = 0.08;          // in # of grid cells
    bool _isObstacleMeshingOffsetEnabled = true;
    double _obstacleMeshingOffset = 0.0;                 // in # of grid cells
    
    bool _isRemoveSurfaceNearDomainEnabled = false;
    int _removeSurfaceNearDomainDistance = 0;         // in # of grid cells
    bool _removeSurfaceNearDomainXNeg = true;
    bool _removeSurfaceNearDomainXPos = true;
    bool _removeSurfaceNearDomainYNeg = true;
    bool _removeSurfaceNearDomainYPos = true;
    bool _removeSurfaceNearDomainZNeg = true;
    bool _removeSurfaceNearDomainZPos = true;

    double _previewdx = 0.0;
    bool _isFluidParticleDebugOutputEnabled = false;
    bool _isInternalObstacleMeshOutputEnabled = false;
    bool _isForceFieldDebugOutputEnabled = false;
    bool _isDiffuseMaterialOutputEnabled = false;
    bool _isBubbleDiffuseMaterialEnabled = true;
    bool _isSprayDiffuseMaterialEnabled = true;
    bool _isFoamDiffuseMaterialEnabled = true;
    bool _isDiffuseMaterialFilesSeparated = false;
    int _outputFluidSurfaceSubdivisionLevel = 1;
    int _numSurfaceReconstructionPolygonizerSlices = 1;
    double _surfaceReconstructionSmoothingValue = 0.5;
    int _surfaceReconstructionSmoothingIterations = 2;
    int _minimumSurfacePolyhedronTriangleCount = 0;
    double _markerParticleRadius = 0.0;
    double _markerParticleScale = 3.0;
    vmath::vec3 _domainOffset;
    double _domainScale = 1.0;
    TriangleMeshFormat _meshOutputFormat = TriangleMeshFormat::ply;
    FluidSimulationOutputData _outputData;
    TimingData _timingData;

    MeshObject *_meshingVolume = NULL;
    MeshLevelSet _meshingVolumeSDF;
    bool _isMeshingVolumeSet = false;
    bool _isMeshingVolumeLevelSetUpToDate = false;

    bool _isAsynchronousMeshingEnabled = true;
    std::thread _mesherThread;

    // Advect velocity field
    VelocityAdvector _velocityAdvector;
    int _maxParticlesPerVelocityAdvection = 5e6;
    std::thread _advectVelocityFieldThread;
    VelocityTransferMethod _velocityTransferMethod = VelocityTransferMethod::FLIP;

    // Calculate fluid curvature
    Array3d<float> _fluidSurfaceLevelSet;
    Array3d<float> _fluidCurvatureGrid;
    std::thread _fluidCurvatureThread;
    bool _isCalculateFluidCurvatureGridThreadRunning = false;

    // Apply body forces
    std::vector<vmath::vec3> _constantBodyForces;

    bool _isForceFieldsEnabled = false;
    int _forceFieldReductionLevel = 1;
    ForceFieldGrid _forceFieldGrid;
    float _forceFieldWeightFluidParticles = 1.0f;

    // Viscosity solve
    ViscositySolver _viscositySolver;
    Array3d<float> _viscosity;
    bool _isViscosityEnabled = false;
    double _constantViscosityValue = 0.0;
    double _viscositySolverErrorTolerance = 1e-4;
    double _maxViscositySolveIterations = 900;
    std::string _viscositySolverStatus;
    bool _pressureSolverSuccess = true;
    int _pressureSolverIterations = 0;
    float _pressureSolverError = 0.0f;

    // Pressure solve
    WeightGrid _weightGrid;
    bool _isWeightGridUpToDate = false;
    bool _isSurfaceTensionEnabled = false;
    double _surfaceTensionConstant = 0.0;
    double _density = 20.0;
    double _minfrac = 0.01;
    double _pressureSolveTolerance = 1e-9;
    double _pressureSolveAcceptableTolerance = 1.0;
    double _maxPressureSolveIterations = 900;
    std::string _pressureSolverStatus;
    bool _viscositySolverSuccess = true;
    int _viscositySolverIterations = 0;
    float _viscositySolverError = 0.0f;

    // Extrapolate fluid velocities
    ValidVelocityComponentGrid _validVelocities;

    // Update diffuse particle simulation
    DiffuseParticleSimulation _diffuseMaterial;
    double _diffuseObstacleInfluenceBaseLevel = 1.0;
    double _diffuseObstacleInfluenceDecayRate = 2.0;
    InfluenceGrid _obstacleInfluenceGrid;

    // Sheeting
    bool _isSheetSeedingEnabled = false;
    float _sheetFillThreshold = -0.95f;
    float _sheetFillRate = 0.5f;

    // Update MarkerParticle velocities
    int _maxParticlesPerPICFLIPUpdate = 10e6;
    double _ratioPICFLIP = 0.05;
    double _ratioPICAPIC = 0.00;
    MACVelocityField _MACVelocity;
    MACVelocityField _savedVelocityField;

    // Update Attributes
    bool _isSurfaceVelocityAttributeAgainstObstaclesEnabled = false;
    MACVelocityField _velocityAttributeGrid;
    ValidVelocityComponentGrid _velocityAttributeValidGrid;

    Array3d<vmath::vec3> _vorticityAttributeGrid;

    Array3d<float> _ageAttributeGrid;
    Array3d<bool> _ageAttributeValidGrid;
    float _ageAttributeRadius = 1.0f;   // In # of voxels

    Array3d<float> _lifetimeAttributeGrid;
    Array3d<bool> _lifetimeAttributeValidGrid;
    float _lifetimeAttributeRadius = 1.0f;   // In # of voxels

    Array3d<vmath::vec3> _whitewaterProximityAttributeGrid;
    Array3d<bool> _whitewaterProximityAttributeValidGrid;
    float _whitewaterProximityAttributeRadius = 2.0f;   // In # of voxels

    Array3d<float> _viscosityAttributeGrid;
    Array3d<bool> _viscosityAttributeValidGrid;
    float _viscosityAttributeRadius = 3.0f;        // In # of voxels
    float _viscositySolverAttributeRadius = 2.0f;  // In # of voxels

    Array3d<float> _densityAttributeGrid;
    Array3d<bool> _densityAttributeValidGrid;
    float _densityAttributeRadius = 1.0f;   // In # of voxels

    Array3d<float> _colorAttributeGridR;
    Array3d<float> _colorAttributeGridG;
    Array3d<float> _colorAttributeGridB;
    Array3d<bool> _colorAttributeValidGrid;
    float _colorAttributeRadius = 1.0f;   // In # of voxels
    float _colorAttributeMixingRate = 1.0f;
    float _colorAttributeMixingRadius = 1.0f;   // In # of voxels
    bool _isMixboxEnabled = false;
    float _mixboxSaturationFactor = 1.2f;

    // Advance MarkerParticles
    int _maxParticlesPerParticleAdvection = 10e6;
    int _maxMarkerParticlesPerCell = 250;
    float _solidBufferWidth = 0.2f;
    bool _isAdaptiveObstacleTimeSteppingEnabled = false;
    bool _isAdaptiveForceFieldTimeSteppingEnabled = false;
    bool _isExtremeVelocityRemovalEnabled = true;
    double _extremeParticleVelocityThreshold = 0.99999;
    double _extremeParticleVelocityThresholdLower = 0.90;
    double _maxExtremeVelocityRemovalPercent = 0.0005;
    int _maxExtremeVelocityRemovalAbsolute = 35;
    int _maxExtremeVelocityOutlierRemovalAbsolute = 6;
    int _minTimeStepIncreaseForRemoval = 4;
    float _markerParticleStepDistanceFactor = 0.1f;

    bool _openBoundaryXNeg = false;
    bool _openBoundaryXPos = false;
    bool _openBoundaryYNeg = false;
    bool _openBoundaryYPos = false;
    bool _openBoundaryZNeg = false;
    bool _openBoundaryZPos = false;
    int _openBoundaryWidth = 2;    // In # of voxels

    std::random_device _randomDevice;
    std::mt19937 _randomSeed;
    std::uniform_real_distribution<> _random;

};
