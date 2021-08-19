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

#ifndef FLUIDENGINE_PARTICLEADVECTOR_H
#define FLUIDENGINE_PARTICLEADVECTOR_H

#include <algorithm>

#include "arrayview3d.h"
#include "vmath.h"
#include "opencl_bindings/clcpp.h"

class MACVelocityField;

class ParticleAdvector
{
public:
    ParticleAdvector();

    bool initialize();
    bool isInitialized();
    std::string getInitializationErrorMessage();

    std::string getDeviceInfo();
    std::string getKernelInfo();
    void disableOpenCL();
    void enableOpenCL();
    bool isOpenCLEnabled();
    int getKernelWorkLoadSize();
    void setKernelWorkLoadSize(int n);

    void advectParticlesRK4(std::vector<vmath::vec3> &particles,
                            MACVelocityField *vfield,
                            double dt,
                            std::vector<vmath::vec3> &output);

    void advectParticlesRK3(std::vector<vmath::vec3> &particles,
                            MACVelocityField *vfield,
                            double dt,
                            std::vector<vmath::vec3> &output);

    void advectParticlesRK2(std::vector<vmath::vec3> &particles,
                            MACVelocityField *vfield,
                            double dt,
                            std::vector<vmath::vec3> &output);

    void advectParticlesRK1(std::vector<vmath::vec3> &particles,
                            MACVelocityField *vfield,
                            double dt,
                            std::vector<vmath::vec3> &output);

    void trilinearInterpolate(std::vector<vmath::vec3> &particles,
                             MACVelocityField *vfield,
                             std::vector<vmath::vec3> &output);

    // method will overwrite particles with output data
    void trilinearInterpolate(std::vector<vmath::vec3> &particles,
                             MACVelocityField *vfield);

private:

    #if WITH_OPENCL

    struct CLDeviceInfo {
        char cl_device_name[4096];
        char cl_device_vendor[4096];
        char cl_device_version[4096];
        char cl_driver_version[4096];
        char cl_device_opencl_c_version[4096];

        cl_device_type device_type;
        cl_uint cl_device_max_clock_frequency;
        cl_ulong cl_device_global_mem_size;
        cl_ulong cl_device_local_mem_size;
        cl_ulong cl_device_max_mem_alloc_size;
        size_t cl_device_max_work_group_size;
        GridIndex cl_device_max_work_item_sizes;
    };

    struct CLKernelInfo {
        char cl_kernel_function_name[4096];
        char cl_kernel_attributes[4096];

        cl_ulong cl_kernel_num_args;
        size_t cl_kernel_work_group_size;
        cl_ulong cl_kernel_local_mem_size;
        cl_ulong cl_kernel_private_mem_size;
        size_t cl_kernel_preferred_work_group_size_multiple;
    };

    struct ParticleChunk {
        std::vector<vmath::vec3> particles;
        std::vector<int> references;
    };

    struct DataChunkParameters {
        std::vector<vmath::vec3>::iterator particlesBegin;
        std::vector<vmath::vec3>::iterator particlesEnd;
        std::vector<int>::iterator referencesBegin;
        std::vector<int>::iterator referencesEnd;

        ArrayView3d<float> ufieldview;
        ArrayView3d<float> vfieldview;
        ArrayView3d<float> wfieldview;

        GridIndex chunkOffset;
        GridIndex indexOffset;
        vmath::vec3 positionOffset;
    };

    struct DataBuffer {
        std::vector<vmath::vec3> positionDataH;
        std::vector<float> vfieldDataH;
        std::vector<GridIndex> offsetDataH;

        clcpp::Buffer positionDataCL;
        clcpp::Buffer vfieldDataCL;
        clcpp::Buffer offsetDataCL;
    };

    void _checkError(cl_int err, const char * name);
    cl_int _initializeCLContext();
    cl_int _initializeCLDevice();
    cl_int _initializeCLKernel();
    cl_int _initializeCLCommandQueue();

    void _getParticleChunkGrid(double cwidth, double cheight, double cdepth,
                               std::vector<vmath::vec3> &particles,
                               Array3d<ParticleChunk> &grid);
    void _getDataChunkParameters(MACVelocityField *vfield,
                                 Array3d<ParticleChunk> &particleChunkGrid,
                                 std::vector<DataChunkParameters> &chunkParameters);
    void _getDataChunkParametersForChunkIndex(GridIndex index,
                                              MACVelocityField *vfield,
                                              ParticleChunk *particleChunk,
                                              std::vector<DataChunkParameters> &chunkParameters);
    
    int _getWorkGroupSize();
    int _getChunkPositionDataSize();
    int _getChunkVelocityDataSize();
    int _getChunkOffsetDataSize();
    int _getChunkTotalDataSize();
    int _getMaxChunksPerComputation();

    void _trilinearInterpolateChunks(std::vector<DataChunkParameters> &chunks,
                                    std::vector<vmath::vec3> &output);
    void _initializeDataBuffer(std::vector<DataChunkParameters> &chunks,
                               DataBuffer &buffer);
    void _getHostPositionDataBuffer(std::vector<DataChunkParameters> &chunks,
                                    std::vector<vmath::vec3> &buffer);
    void _getHostVelocityDataBuffer(std::vector<DataChunkParameters> &chunks,
                                    std::vector<float> &buffer);
    void _appendChunkVelocityDataToBuffer(DataChunkParameters &chunk, 
                                          std::vector<float> &buffer);
    void _getHostChunkOffsetDataBuffer(std::vector<DataChunkParameters> &chunks,
                                       std::vector<GridIndex> &buffer);
    void _setCLKernelArgs(DataBuffer &buffer, float dx);
    void _setOutputData(std::vector<DataChunkParameters> &chunks,
                        DataBuffer &buffer,
                        std::vector<vmath::vec3> &output);

    clcpp::Context _CLContext;
    clcpp::Device _CLDevice;
    clcpp::Program _CLProgram;
    clcpp::Kernel _CLKernel;
    clcpp::CommandQueue _CLQueue;

    #endif
    // ENDIF WITH_OPENCL
    
    vmath::vec3 _RK4(vmath::vec3 p0, double dt, MACVelocityField *vfield);
    vmath::vec3 _RK3(vmath::vec3 p0, double dt, MACVelocityField *vfield);
    vmath::vec3 _RK2(vmath::vec3 p0, double dt, MACVelocityField *vfield);
    vmath::vec3 _RK1(vmath::vec3 p0, double dt, MACVelocityField *vfield);
    void _advectParticlesRK4NoCL(std::vector<vmath::vec3> &particles,
                                 MACVelocityField *vfield, 
                                 double dt,
                                 std::vector<vmath::vec3> &output);
    void _advectParticlesRK3NoCL(std::vector<vmath::vec3> &particles,
                                 MACVelocityField *vfield, 
                                 double dt,
                                 std::vector<vmath::vec3> &output);
    void _advectParticlesRK2NoCL(std::vector<vmath::vec3> &particles,
                                 MACVelocityField *vfield, 
                                 double dt,
                                 std::vector<vmath::vec3> &output);
    void _advectParticlesRK1NoCL(std::vector<vmath::vec3> &particles,
                                 MACVelocityField *vfield, 
                                 double dt,
                                 std::vector<vmath::vec3> &output);
    void _trilinearInterpolateNoCL(std::vector<vmath::vec3> &particles,
                                 MACVelocityField *vfield, 
                                 std::vector<vmath::vec3> &output);
    void _validateOutput(std::vector<vmath::vec3> &output);


    #if WITH_OPENCL

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;

    int _maxItemsPerWorkGroup = 512;
    int _dataChunkWidth = 8;
    int _dataChunkHeight = 8;
    int _dataChunkDepth = 8;
    int _maxChunksPerComputation = 15000;

    #endif
    // ENDIF WITH_OPENCL

    bool _isInitialized = false;
    std::string _initializationErrorMessage;
    int _kernelWorkLoadSize = 1000;
    bool _isOpenCLEnabled = true;
    
};

#endif
