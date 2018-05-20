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

#ifndef FLUIDENGINE_FLUIDSIMULATION_H
#define FLUIDENGINE_FLUIDSIMULATION_H

#if __MINGW32__ && !_WIN64
    #include "mingw32_threads/mingw.thread.h"
#else
    #include <thread>
#endif

#include <vector>

#include "vmath.h"
#include "array3d.h"
#include "meshobject.h"
#include "fragmentedvector.h"
#include "logfile.h"
#include "particlelevelset.h"
#include "pressuresolver.h"
#include "diffuseparticlesimulation.h"
#include "clscalarfield.h"
#include "particleadvector.h"
#include "velocityadvector.h"
#include "meshfluidsource.h"

class AABB;
class MeshFluidSource;
class ParticleMaskGrid;
class MACVelocityField;
class FluidMaterialGrid;
struct MarkerParticle;
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

    FluidSimulationMeshStats surface;
    FluidSimulationMeshStats preview;
    FluidSimulationMeshStats foam;
    FluidSimulationMeshStats bubble;
    FluidSimulationMeshStats spray;
    FluidSimulationMeshStats particles;
    FluidSimulationMeshStats obstacle;
    FluidSimulationTimingStats timing;
};

struct FluidSimulationMarkerParticleData {
    int size = 0;
    char *positions;
    char *velocities;
};

struct FluidSimulationDiffuseParticleData {
    int size = 0;
    char *positions;
    char *velocities;
    char *lifetimes;
    char *types;
    char *ids;
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
        Initializes the fluid simulation.

        Must be called before running update() method.
    */
    void initialize();
    bool isInitialized();

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
    */
    double getMarkerParticleJitterFactor();
    void setMarkerParticleJitterFactor(double jit);

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
        Generate smooth interface between fluid and obstacle surface
    */
    void enableSmoothInterfaceMeshing();
    void disableSmoothInterfaceMeshing();
    bool isSmoothInterfaceMeshingEnabled();

    /*
        Invert surface mesh normals that contact obstacle surfaces. Used for 
        correct refraction rendering with water-glass interfaces.
    */
    void enableInvertedContactNormals();
    void disableInvertedContactNormals();
    bool isInvertedContactNormalsEnabled();

    /*
        Enable/disable the simulation from saving fluid particles

        Disabled by default.
    */
    void enableFluidParticleOutput();
    void disableFluidParticleOutput();
    bool isFluidParticleOutputEnabled();

    /*
        Enable/disable the simulation from saving internal obstacle mesh

        Disabled by default.
    */
    void enableInternalObstacleMeshOutput();
    void disableInternalObstacleMeshOutput();
    bool isInternalObstacleMeshOutputEnabled();

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
        Lifetime modifiers for foam/bubble/spray particle.
    */
    double getFoamParticleLifetimeModifier();
    void setFoamParticleLifetimeModifier(double modifier);
    double getBubbleParticleLifetimeModifier();
    void setBubbleParticleLifetimeModifier(double modifier);
    double getSprayParticleLifetimeModifier();
    void setSprayParticleLifetimeModifier(double modifier);

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
    void getDiffuseParticleEmissionRates(double *rwc, double *rt);
    void setDiffuseParticleEmissionRates(double r);
    void setDiffuseParticleEmissionRates(double rwc, double rt);

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
        Drag coefficient in range [0.0, 1.0] controls how quickly bubble particles 
        are dragged with the fluid velocity. If set to 1, bubble particles will
        be immediately dragged into the flow direction of the fluid.
    */
    double getDiffuseBubbleDragCoefficient();
    void setDiffuseBubbleDragCoefficient(double d);

    /*
        Bouyancy coefficient controls how quickly bubble particles float towards
        the fluid surface. If set to a negative value, bubbles will sink away 
        from the fluid surface.
    */
    double getDiffuseBubbleBouyancyCoefficient();
    void setDiffuseBubbleBouyancyCoefficient(double b);

    /*
        Amount of air resistance acting on a diffuse spray particle
    */
    double getDiffuseSprayDragCoefficient();
    void setDiffuseSprayDragCoefficient(double d);

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

    std::vector<bool> getDiffuseFoamActiveBoundarySides();
    void setDiffuseFoamActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getDiffuseBubbleActiveBoundarySides();
    void setDiffuseBubbleActiveBoundarySides(std::vector<bool> active);

    std::vector<bool> getDiffuseSprayActiveBoundarySides();
    void setDiffuseSprayActiveBoundarySides(std::vector<bool> active);

    /*
        Enable/disable use of OpenCL for particle advection.

        Enabled by default.
    */
    void enableOpenCLParticleAdvection();
    void disableOpenCLParticleAdvection();
    bool isOpenCLParticleAdvectionEnabled();

    /*
        Enable/disable use of OpenCL for scalar fields.

        Enabled by default.
    */
    void enableOpenCLScalarField();
    void disableOpenCLScalarField();
    bool isOpenCLScalarFieldEnabled();

    /*
        Maximum workload size for the ParticleAdvector OpenCL kernel
    */
    int getParticleAdvectionKernelWorkLoadSize();
    void setParticleAdvectionKernelWorkLoadSize(int n);


    /*
        Maximum workload size for the CLScalarField OpenCL kernels
    */
    int getScalarFieldKernelWorkLoadSize();
    void setScalarFieldKernelWorkLoadSize(int n);

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

    /*
        Add a variable body force field function to the simulation. 
        The force field function takes a 3d vector position as a parameter
        and returns a 3d vector force.

        Example field function:

            vmath::vec3 forceField(vmath::vec3 p) {
                vmath::vec3 forceVector(0.0, -9.8, 0.0);

                if (p.x < 4.0) {
                    forceVector.y = -forceVector.y;
                }
                
                return forceVector
            }
    */
    void addBodyForce(vmath::vec3 (*fieldFunction)(vmath::vec3));
    vmath::vec3 getConstantBodyForce();
    vmath::vec3 getVariableBodyForce(double x, double y, double z);
    vmath::vec3 getVariableBodyForce(vmath::vec3 p);
    vmath::vec3 getTotalBodyForce(double x, double y, double z);
    vmath::vec3 getTotalBodyForce(vmath::vec3 p);

    /*
        Remove all added body forces.
    */
    void resetBodyForce();

    /*
        Viscosity of the fluid. 
        Must be greater than or equal to zero. 
    */
    double getViscosity();
    void setViscosity(double v);

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

    /*
        Min/max time step calculations per frame update
    */
    int getMinTimeStepsPerFrame();
    void setMinTimeStepsPerFrame(int n);
    int getMaxTimeStepsPerFrame();
    void setMaxTimeStepsPerFrame(int n);

    /*
        Enable/Disable adaptive time stepping for obstacles

        If enabled, obstacle velocities are included in time step calculation.
        May improve the accuracy of fluid-solid interaction for fast moving
        obstacles.
    */
    void enableAdaptiveObstacleTimeStepping();
    void disableAdaptiveObstacleTimeStepping();
    bool isAdaptiveObstacleTimeSteppingEnabled();

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
        Ratio of PIC to FLIP velocity update
    */
    double getPICFLIPRatio();
    void setPICFLIPRatio(double r);

    /*
        Name of the preferred GPU device to use for GPU acceleration features
    */
    std::string getPreferredGPUDevice();
    void setPreferredGPUDevice(std::string deviceName);

    /*
        Enable/Disable experimental optimization features
    */
    void enableExperimentalOptimizationFeatures();
    void disableExperimentalOptimizationFeatures();
    bool isExperimentalOptimizationFeaturesEnabled();

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
        Returns a vector of all diffuse particles in the simulation. Diffuse particles
        store a position, velocity, lifetime, and and type (bubble, spray,
        or foam).
    */
    std::vector<DiffuseParticle> getDiffuseParticles();
    std::vector<DiffuseParticle> getDiffuseParticles(int startidx, int endidx);

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
    std::vector<char>* getDiffuseData();
    std::vector<char>* getDiffuseFoamData();
    std::vector<char>* getDiffuseBubbleData();
    std::vector<char>* getDiffuseSprayData();
    std::vector<char>* getFluidParticleData();
    std::vector<char>* getInternalObstacleMeshData();
    std::vector<char>* getLogFileData();
    FluidSimulationFrameStats getFrameStatsData();

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
    void loadDiffuseParticleData(FluidSimulationDiffuseParticleData data);

private:   

    struct FluidMeshObject {
        MeshObject object;
        vmath::vec3 velocity;

        FluidMeshObject() {}
        FluidMeshObject(MeshObject obj, vmath::vec3 v) : 
                        object(obj), velocity(v) {}
    };

    struct FluidSimulationOutputData {
        std::vector<char> surfaceData;
        std::vector<char> surfacePreviewData;
        std::vector<char> diffuseData;
        std::vector<char> diffuseFoamData;
        std::vector<char> diffuseBubbleData;
        std::vector<char> diffuseSprayData;
        std::vector<char> fluidParticleData;
        std::vector<char> internalObstacleMeshData;
        std::vector<char> logfileData;
        FluidSimulationFrameStats frameData;
    };

    struct MarkerParticleLoadData {
        FragmentedVector<MarkerParticle> particles;
    };

    struct DiffuseParticleLoadData {
        FragmentedVector<DiffuseParticle> particles;
    };

    struct TimingData {
        double updateObstacleObjects = 0.0;
        double updateLiquidLevelSet = 0.0;
        double advectVelocityField = 0.0;
        double saveVelocityField = 0.0;
        double calculateDiffuseCurvatureGrid = 0.0;
        double applyBodyForcesToVelocityField = 0.0;
        double applyViscosityToVelocityField = 0.0;
        double pressureSolve = 0.0;
        double constrainVelocityFields = 0.0;
        double updateDiffuseMaterial = 0.0;
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
                           calculateDiffuseCurvatureGrid +
                           applyBodyForcesToVelocityField +
                           applyViscosityToVelocityField +
                           pressureSolve +
                           constrainVelocityFields +
                           updateDiffuseMaterial +
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
            calculateDiffuseCurvatureGrid  *= factor;
            applyBodyForcesToVelocityField *= factor;
            applyViscosityToVelocityField  *= factor;
            pressureSolve                  *= factor;
            constrainVelocityFields        *= factor;
            updateDiffuseMaterial          *= factor;
            updateMarkerParticleVelocities *= factor;
            deleteSavedVelocityField       *= factor;
            advanceMarkerParticles         *= factor;
            updateFluidObjects             *= factor;
            outputNonMeshSimulationData    *= factor;
            outputMeshSimulationData       *= factor;
        }
    };

    /*
        Initializing the Fluid Simulator
    */
    void _initializeLogFile();
    void _initializeSimulationGrids(int isize, int jsize, int ksize, double dx);
    void _initializeSimulation();
    void _logOpenCLInfo();
    void _initializeParticleRadii();
    double _getMarkerParticleJitter();
    vmath::vec3 _jitterMarkerParticlePosition(vmath::vec3 p, double jitter);
    void _addMarkerParticle(vmath::vec3 p, vmath::vec3 velocity);
    void _initializeCLObjects();
    void _loadParticles();
    void _loadMarkerParticles(MarkerParticleLoadData &data);
    void _loadDiffuseParticles(DiffuseParticleLoadData &data);

    /*
        Advancing the State of the Fluid Simulation
    */
    double _calculateNextTimeStep(double dt);
    double _getMaximumMeshObjectFluidVelocity(MeshObject *object, 
                                              vmath::vec3 fluidVelocity);
    double _predictMaximumMarkerParticleSpeed();
    double _getMaximumMarkerParticleSpeed();
    double _getMaximumObstacleSpeed(double dt);
    void _updateTimingData();
    void _logStepInfo();
    void _logFrameInfo();
    void _logGreeting();
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
    void _advectVelocityFieldU();
    void _advectVelocityFieldV();
    void _advectVelocityFieldW();
    void _computeVelocityScalarField(Array3d<float> &field, 
                                     Array3d<bool> &isValueSet, 
                                     int dir);
    void _computeVelocityScalarFieldThread(int startidx, int endidx,
                                           FragmentedVector<MarkerParticle> *particles, 
                                           Array3d<float> *field, 
                                           Array3d<float> *weightfield,
                                           int dir, int splitdir);
    void _saveVelocityField();
    void _deleteSavedVelocityField();

    /*
        Apply Body Forces
    */
    void _applyBodyForcesToVelocityField(double dt);
    vmath::vec3 _getConstantBodyForce();
    vmath::vec3 _getVariableBodyForce(double px, double py, double pz);
    vmath::vec3 _getVariableBodyForce(vmath::vec3 p);
    void _applyConstantBodyForces(double dt);
    void _applyVariableBodyForces(double dt);
    void _applyVariableBodyForce(vmath::vec3 (*fieldFunction)(vmath::vec3),
                                 double dt);

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
    Array3d<float> _computePressureGrid(double dt, bool *success);
    void _applyPressureToVelocityField(Array3d<float> &pressureGrid, double dt);
    void _applyPressureToVelocityFieldMT(Array3d<float> &pressureGrid, 
                                         FluidMaterialGrid &mgrid,
                                         double dt, int dir);
    void _applyPressureToVelocityFieldThread(int startidx, int endidx, 
                                             Array3d<float> *pressureGrid, 
                                             FluidMaterialGrid *mgrid,
                                             double dt, int dir);
    void _pressureSolve(double dt);

    /*
        Extrapolate Velocity Field
    */
    void _extrapolateFluidVelocities(MACVelocityField &MACGrid,
                                     ValidVelocityComponentGrid &validVelocities);

    /*
        Constrain Velocity Field
    */
    float _getFaceFrictionU(int i, int j, int k);
    float _getFaceFrictionV(int i, int j, int k);
    float _getFaceFrictionW(int i, int j, int k);
    void _constrainVelocityField(MACVelocityField &MACGrid);
    void _constrainVelocityFields();

    /*
        Update Diffuse Particle Simulation
    */
    void _updateDiffuseMaterial(double dt);
    void _launchCalculateDiffuseCurvatureGridThread();
    void _joinCalculateDiffuseCurvatureGridThread();
    void _calculateDiffuseCurvatureGridThread();

    /*
        Update MarkerParticle Velocities
    */
    void _updateMarkerParticleVelocities();
    void _updateMarkerParticleVelocitiesThread(int startidx, int endidx);

    /*
        Advance MarkerParticles
    */
    void _advanceMarkerParticles(double dt);
    void _advanceMarkerParticlesThread(double dt, int startidx, int endidx,
                                       std::vector<vmath::vec3> *positions,
                                       std::vector<vmath::vec3> *output);
    vmath::vec3 _RK3(vmath::vec3 p0, double dt);

    void _resolveMarkerParticleCollisions(std::vector<vmath::vec3> &positionsOld, 
                                          std::vector<vmath::vec3> &positionsNew);
    void _resolveMarkerParticleCollisions(int startidx, int endidx,
                                          std::vector<vmath::vec3> &positionsOld, 
                                          std::vector<vmath::vec3> &positionsNew);
    vmath::vec3 _resolveCollision(vmath::vec3 oldp, vmath::vec3 newp, AABB &boundary);
    float _getMarkerParticleSpeedLimit(double dt);
    void _removeMarkerParticles(double dt);

    /*
        #. Update Fluid Objects
    */
    void _updateFluidObjects();
    void _updateAddedFluidMeshObjectQueue();
    void _addNewFluidCells(std::vector<GridIndex> &cells, vmath::vec3 velocity,
                           MeshLevelSet &liquidSDF);
    void _addNewFluidCells(std::vector<GridIndex> &cells, 
                           vmath::vec3 velocity,
                           MeshLevelSet &meshsdf,
                           ParticleMaskGrid &maskgrid);
    void _addNewFluidCells(std::vector<GridIndex> &cells, 
                           vmath::vec3 velocity,
                           RigidBodyVelocity rvelocity,
                           MeshLevelSet &meshsdf,
                           ParticleMaskGrid &maskgrid);
    void _addNewFluidCells(std::vector<GridIndex> &cells, 
                           vmath::vec3 velocity,
                           VelocityFieldData *vdata,
                           MeshLevelSet &meshsdf,
                           ParticleMaskGrid &maskgrid);
    void _updateMeshFluidSources();
    void _updateInflowMeshFluidSources();
    void _updateOutflowMeshFluidSources();
    void _updateInflowMeshFluidSource(MeshFluidSource *source, ParticleMaskGrid &maskgrid);
    void _updateOutflowMeshFluidSource(MeshFluidSource *source);
    int _getNumFluidCells();

    /*
        Output Simulation Data
    */
    void _outputSimulationData();
    void _outputSurfaceMeshThread(FragmentedVector<vmath::vec3> *particles,
                                  MeshLevelSet *soldSDF);
    void _computeDomainBoundarySDF(MeshLevelSet *sdf);
    void _launchOutputSurfaceMeshThread();
    void _joinOutputSurfaceMeshThread();
    void _outputDiffuseMaterial();
    float _calculateParticleSpeedPercentileThreshold(float pct);
    void _outputFluidParticles();
    void _outputInternalObstacleMesh();
    std::string _numberToString(int number);
    std::string _getFrameString(int number);
    void _getTriangleMeshFileData(TriangleMesh &mesh, std::vector<char> &data);
    void _getFluidParticleFileData(std::vector<vmath::vec3> &particles, 
                                   std::vector<int> &binStarts, 
                                   std::vector<float> &binSpeeds, 
                                   std::vector<char> &outdata);
    void _smoothSurfaceMesh(TriangleMesh &mesh);
    void _invertContactNormals(TriangleMesh &mesh);
    void _polygonizeOutputSurface(TriangleMesh &surface, TriangleMesh &preview,
                                  FragmentedVector<vmath::vec3> *particles,
                                  MeshLevelSet *soldSDF);
    void _outputSimulationLogFile();


    /*
        Misc Methods
    */
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

        int numRemoved = items.size() - currentidx;
        for (int i = 0; i < numRemoved; i++) {
            items.pop_back();
        }
        items.shrink_to_fit();
    }

    inline double _randomDouble(double min, double max) {
        return min + (double)rand() / ((double)RAND_MAX / (max - min));
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

    // Update
    int _currentFrame = 0;
    int _currentFrameTimeStepNumber = 0;
    double _currentFrameTimeStep = 0.0;
    double _currentFrameDeltaTime = 0.0;
    double _currentFrameDeltaTimeRemaining = 0.0;
    bool _isLastFrameTimeStep = false;
    int _minFrameTimeSteps = 1;
    int _maxFrameTimeSteps = 6;
    double _totalSimulationTime = 0;
    bool _isCurrentFrameFinished = true;
    double _CFLConditionNumber = 5.0;
    LogFile _logfile;

    // Update fluid material
    ParticleLevelSet _liquidSDF;
    std::vector<MeshFluidSource*> _meshFluidSources;
    FragmentedVector<MarkerParticle> _markerParticles;
    std::vector<FluidMeshObject> _addedFluidMeshObjectQueue;
    double _markerParticleJitterFactor = 0.0;
    int _liquidLevelSetExactBand = 3;

    bool _isMarkerParticleLoadPending = false;
    bool _isDiffuseParticleLoadPending = false;
    std::vector<MarkerParticleLoadData> _markerParticleLoadQueue;
    std::vector<DiffuseParticleLoadData> _diffuseParticleLoadQueue;

    // Update obstacles
    std::vector<MeshObject*> _obstacles;
    std::thread _updateObstacleObjectsThread;

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
    double _liquidSDFParticleRadius = 0.0;
    std::thread _updateLiquidLevelSetThread;

    // Reconstruct output fluid surface
    bool _isSurfaceMeshReconstructionEnabled = true;
    bool _isPreviewSurfaceMeshEnabled = false;
    bool _isSmoothInterfaceMeshingEnabled = true;
    bool _isInvertedContactNormalsEnabled = false;
    double _contactThresholdDistance = 0.08;          // in # of grid cells
    double _previewdx = 0.0;
    bool _isFluidParticleOutputEnabled = false;
    bool _isInternalObstacleMeshOutputEnabled = false;
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

    bool _isAsynchronousMeshingEnabled = true;
    std::thread _mesherThread;

    // Advect velocity field
    VelocityAdvector _velocityAdvector;
    int _maxParticlesPerVelocityAdvection = 5e6;
    std::thread _advectVelocityFieldThread;

    // Apply body forces
    typedef vmath::vec3 (*FieldFunction)(vmath::vec3);
    std::vector<FieldFunction> _variableBodyForces;
    std::vector<vmath::vec3> _constantBodyForces;

    // Viscosity solve
    Array3d<float> _viscosity;
    bool _isViscosityEnabled = false;
    double _constantViscosityValue = 0.0;
    std::string _viscositySolverStatus;

    // Pressure solve
    WeightGrid _weightGrid;
    bool _isWeightGridUpToDate = false;
    double _density = 20.0;
    double _minfrac = 0.01;
    double _pressureSolveTolerance = 1e-9;
    double _pressureSolveAcceptableTolerance = 1.0;
    double _maxPressureSolveIterations = 1000;
    std::string _pressureSolverStatus;

    // Extrapolate fluid velocities
    ValidVelocityComponentGrid _validVelocities;

    // Update diffuse particle simulation
    DiffuseParticleSimulation _diffuseMaterial;
    MeshLevelSet _diffuseSurfaceLevelSet;
    Array3d<float> _diffuseCurvatureGrid;
    std::thread _diffuseCurvatureThread;

    // Update MarkerParticle velocities
    int _maxParticlesPerPICFLIPUpdate = 10e6;
    double _ratioPICFLIP = 0.05;
    MACVelocityField _MACVelocity;
    MACVelocityField _savedVelocityField;

    // Advance MarkerParticles
    int _maxParticlesPerParticleAdvection = 10e6;
    int _maxMarkerParticlesPerCell = 250;
    float _solidBufferWidth = 0.01f;
    bool _isAdaptiveObstacleTimeSteppingEnabled = false;
    bool _isExtremeVelocityRemovalEnabled = true;
    double _maxExtremeVelocityRemovalPercent = 0.0005;
    int _maxExtremeVelocityRemovalAbsolute = 35;
    
    // OpenCL
    ParticleAdvector _particleAdvector;
    CLScalarField _scalarFieldAccelerator;
    CLScalarField _mesherScalarFieldAccelerator;

    bool _isExperimentalOptimizationEnabled = true;
};

#endif