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

#ifndef FLUIDENGINE_CLSCALARFIELD_H
#define FLUIDENGINE_CLSCALARFIELD_H

#include "vmath.h"
#include "array3d.h"
#include "arrayview3d.h"
#include "opencl_bindings/clcpp.h"

class ScalarField;

class CLScalarField
{
public:
    CLScalarField();

    bool initialize();
    bool isInitialized();
    std::string getInitializationErrorMessage();
    void addPoints(std::vector<vmath::vec3> &points, 
                   double radius,
                   vmath::vec3 offset,
                   double dx,
                   Array3d<float> *field);
    void addPoints(std::vector<vmath::vec3> &points, 
                   double radius,
                   vmath::vec3 offset,
                   double dx,
                   ScalarField &field);
    void addPoints(std::vector<vmath::vec3> &points, 
                   ScalarField &field);

    void addPointValues(std::vector<vmath::vec3> &points, 
                        std::vector<float> &values,
                        double radius,
                        vmath::vec3 offset,
                        double dx,
                        Array3d<float> *field);
    void addPointValues(std::vector<vmath::vec3> &points, 
                        std::vector<float> &values,
                        double radius,
                        vmath::vec3 offset,
                        double dx,
                        Array3d<float> *scalarfield,
                        Array3d<float> *weightfield);
    void addPointValues(std::vector<vmath::vec3> &points, 
                        std::vector<float> &values,
                        double radius,
                        vmath::vec3 offset,
                        double dx,
                        ScalarField &field);
    void addPointValues(std::vector<vmath::vec3> &points, 
                        std::vector<float> &values,
                        ScalarField &field);

    void addLevelSetPoints(std::vector<vmath::vec3> &points, 
                           double radius,
                           vmath::vec3 offset,
                           double dx,
                           Array3d<float> *field);
    void addLevelSetPoints(std::vector<vmath::vec3> &points, 
                           double radius,
                           vmath::vec3 offset,
                           double dx,
                           ScalarField &field);
    void addLevelSetPoints(std::vector<vmath::vec3> &points, 
                           ScalarField &field);

    void setMaxScalarFieldValueThreshold(float val);
    void setMaxScalarFieldValueThreshold();
    bool isMaxScalarFieldValueThresholdSet();
    double getMaxScalarFieldValueThreshold();

    std::string getDeviceInfo();
    std::string getKernelInfo();
    void disableOpenCL();
    void enableOpenCL();
    bool isOpenCLEnabled();
    int getKernelWorkLoadSize();
    void setKernelWorkLoadSize(int n);

private:

    #if WITH_OPENCL

    struct DataBuffer {
        std::vector<float> pointDataH;
        std::vector<float> scalarFieldDataH;
        std::vector<GridIndex> offsetDataH;

        clcpp::Buffer positionDataCL;
        clcpp::Buffer scalarFieldDataCL;
        clcpp::Buffer offsetDataCL;
    };

    void _checkError(cl_int err, const char * name);
    cl_int _initializeCLContext();
    cl_int _initializeCLDevice();
    cl_int _initializeChunkDimensions();
    cl_int _initializeCLKernels();
    cl_int _initializeCLCommandQueue();

    struct PointValue {
        PointValue() {}
        PointValue(vmath::vec3 p, float v) : position(p), value(v) {}
        vmath::vec3 position;
        float value;
    };

    struct WorkGroup {
        std::vector<PointValue> particles;

        ArrayView3d<float> fieldview;
        ArrayView3d<float> weightfieldview;

        GridIndex chunkOffset;
        GridIndex indexOffset;
        vmath::vec3 positionOffset;

        float minScalarFieldValue = 0.0;
    };

    struct WorkChunk {
        GridIndex workGroupIndex;

        std::vector<PointValue>::iterator particlesBegin;
        std::vector<PointValue>::iterator particlesEnd;
    };

    vmath::vec3 _getInternalOffset();
    void _initializePointValues(std::vector<vmath::vec3> &points,
                                std::vector<PointValue> &pvs);
    void _initializePointValues(std::vector<vmath::vec3> &points,
                                std::vector<float> &values,
                                std::vector<PointValue> &pvs);
    GridIndex _getWorkGroupGridDimensions();
    void _initializeWorkGroupGrid(std::vector<PointValue> &points,
                                  Array3d<float> *scalarfield,
                                  Array3d<WorkGroup> &grid);
    void _initializeWorkGroupGrid(std::vector<PointValue> &points,
                                  Array3d<float> *scalarfield,
                                  Array3d<float> *weightfield,
                                  Array3d<WorkGroup> &grid);
    void _initializeWorkGroupParameters(Array3d<WorkGroup> &grid,
                                        Array3d<float> *scalarfield);
    void _initializeWorkGroupParameters(Array3d<WorkGroup> &grid,
                                        Array3d<float> *scalarfield,
                                        Array3d<float> *weightfield);
    void _reserveWorkGroupGridParticleMemory(Array3d<WorkGroup> &grid,
                                             Array3d<int> &countGrid);
    void _getWorkGroupParticleCounts(std::vector<PointValue> &points,
                                     Array3d<int> &countGrid);
    void _insertParticlesIntoWorkGroupGrid(std::vector<PointValue> &points,
                                           Array3d<WorkGroup> &grid);
    void _initializeWorkChunks(Array3d<WorkGroup> &grid,
                               std::vector<WorkChunk> &chunks);
    void _getWorkChunksFromWorkGroup(WorkGroup *group, 
                                     std::vector<WorkChunk> &chunks);
    static bool _compareWorkChunkByNumParticles(const WorkChunk &c1, 
                                                const WorkChunk &c2);
    void _getNextWorkChunksToProcess(std::vector<WorkChunk> &queue,
                                     Array3d<WorkGroup> &grid,
                                     std::vector<WorkChunk> &chunks,
                                     int n);

    int _getChunkPointDataSize();
    int _getChunkPointValueDataSize();
    int _getChunkScalarFieldDataSize();
    int _getChunkScalarWeightFieldDataSize();
    int _getChunkOffsetDataSize();
    int _getMaxChunksPerPointComputation();
    int _getMaxChunksPerPointValueComputation();
    int _getMaxChunksPerWeightPointValueComputation();
    int _getMaxChunksPerLevelSetPointComputation();
    int _getMaxChunkLimit(int pointDataSize, int fieldDataSize, int offsetDataSize);

    void _computePointScalarField(std::vector<WorkChunk> &chunks,
                                  Array3d<WorkGroup> &workGroupGrid);
    void _computePointValueScalarField(std::vector<WorkChunk> &chunks,
                                       Array3d<WorkGroup> &workGroupGrid);
    void _computePointValueScalarWeightField(std::vector<WorkChunk> &chunks,
                                             Array3d<WorkGroup> &workGroupGrid);
    void _computeLevelSetPointScalarField(std::vector<WorkChunk> &chunks,
                                          Array3d<WorkGroup> &workGroupGrid);
    int _getMaxNumParticlesInChunk(std::vector<WorkChunk> &chunks);
    void _initializePointComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                               Array3d<WorkGroup> &workGroupGrid,
                                               int numParticles,
                                               DataBuffer &buffer);
    void _initializePointValueComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                    Array3d<WorkGroup> &workGroupGrid,
                                                    int numParticles,
                                                    DataBuffer &buffer);
    void _initializeWeightPointValueComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                          Array3d<WorkGroup> &workGroupGrid,
                                                          int numParticles,
                                                          DataBuffer &buffer);
    void _initializeLevelSetPointComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                       Array3d<WorkGroup> &workGroupGrid,
                                                       int numParticles,
                                                       DataBuffer &buffer);
    void _getHostPointDataBuffer(std::vector<WorkChunk> &chunks,
                                 Array3d<WorkGroup> &grid,
                                 int numParticles,
                                 std::vector<float> &buffer);
    void _getHostPointValueDataBuffer(std::vector<WorkChunk> &chunks,
                                      Array3d<WorkGroup> &grid,
                                      int numParticles,
                                      std::vector<float> &buffer);
    void _getHostScalarFieldDataBuffer(std::vector<WorkChunk> &chunks,
                                       std::vector<float> &buffer);
    void _getHostScalarWeightFieldDataBuffer(std::vector<WorkChunk> &chunks,
                                             std::vector<float> &buffer);
    void _getHostChunkOffsetDataBuffer(std::vector<WorkChunk> &chunks,
                                       std::vector<GridIndex> &buffer);
    void _initializeCLDataBuffers(DataBuffer &buffer);
    void _setPointComputationCLKernelArgs(DataBuffer &buffer, int numParticles);
    void _setPointValueComputationCLKernelArgs(DataBuffer &buffer, int numParticles);
    void _setWeightPointValueComputationCLKernelArgs(DataBuffer &buffer, int numParticles);
    void _setLevelSetPointComputationCLKernelArgs(DataBuffer &buffer, int numParticles);
    void _setKernelArgs(clcpp::Kernel &kernel, 
                        DataBuffer &buffer, 
                        int localDataBytes,
                        int numParticles, 
                        float radius, 
                        float dx);
    void _launchKernel(clcpp::Kernel &kernel, int numWorkItems, int workGroupSize);
    void _readCLBuffer(clcpp::Buffer &sourceCL, std::vector<float> &destH, int dataSize);
    void _setPointComputationOutputFieldData(std::vector<float> &buffer, 
                                             std::vector<WorkChunk> &chunks,
                                             Array3d<WorkGroup> &workGroupGrid);
    void _setPointValueComputationOutputFieldData(std::vector<float> &buffer, 
                                                  std::vector<WorkChunk> &chunks,
                                                  Array3d<WorkGroup> &workGroupGrid);
    void _setWeightPointValueComputationOutputFieldData(std::vector<float> &buffer, 
                                                        std::vector<WorkChunk> &chunks,
                                                        Array3d<WorkGroup> &workGroupGrid);
    void _setLevelSetPointComputationOutputFieldData(std::vector<float> &buffer, 
                                                     std::vector<WorkChunk> &chunks,
                                                     Array3d<WorkGroup> &workGroupGrid);

    void _updateWorkGroupMinimumValues(Array3d<WorkGroup> &grid);
    float _getWorkGroupMinimumValue(WorkGroup *g);

    clcpp::Context _CLContext;
    clcpp::Device _CLDevice;
    clcpp::Program _CLProgram;
    clcpp::Kernel _CLKernelPoints;
    clcpp::Kernel _CLKernelPointValues;
    clcpp::Kernel _CLKernelWeightPointValues;
    clcpp::Kernel _CLKernelLevelSetPoints;
    clcpp::CommandQueue _CLQueue;

    #endif
    // ENDIF WITH_OPENCL

    void _addPointsNoCL(std::vector<vmath::vec3> &points, 
                        double radius,
                        vmath::vec3 offset,
                        double dx,
                        Array3d<float> *field);
    void _addPointValuesNoCL(std::vector<vmath::vec3> &points, 
                             std::vector<float> &values,
                             double radius,
                             vmath::vec3 offset,
                             double dx,
                             Array3d<float> *field);
    void _addPointValuesNoCL(std::vector<vmath::vec3> &points, 
                             std::vector<float> &values,
                             double radius,
                             vmath::vec3 offset,
                             double dx,
                             Array3d<float> *scalarfield,
                             Array3d<float> *weightfield);
    void _addLevelSetPointsNoCL(std::vector<vmath::vec3> &points, 
                                double radius,
                                vmath::vec3 offset,
                                double dx,
                                Array3d<float> *field);
    void _addField(Array3d<float> *src, Array3d<float> *dest);

    #if WITH_OPENCL

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;
    double _radius = 0.0;
    vmath::vec3 _offset;    // this offset value should not be used
                            // for internal calculations. Use 
                            // _getInternalOffset() for correct value.

    int _workGroupSize = 0;
    int _chunkWidth = 0;
    int _chunkHeight = 0;
    int _chunkDepth = 0;

    int _maxWorkGroupSize = 256;
    int _minWorkGroupSize = 32;
    int _maxParticlesPerChunk = 1024;
    int _maxChunksPerComputation = 100000;

    #endif
    // ENDIF WITH_OPENCL

    bool _isInitialized = false;
    std::string _initializationErrorMessage;

    int _kernelWorkLoadSize = 100000;
    bool _isMaxScalarFieldValueThresholdSet = false;
    float _maxScalarFieldValueThreshold = 1.0;
    bool _isOpenCLEnabled = true;
    
};

#endif
