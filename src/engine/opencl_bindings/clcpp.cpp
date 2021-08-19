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

#include "clcpp.h"

#if WITH_OPENCL

/********************************************************************************
    PLATFORM
********************************************************************************/

clcpp::Platform::Platform() {
}

clcpp::Platform::Platform(cl_platform_id pid) {
    _id = pid;
    _isInitialized = true;
}

cl_platform_id clcpp::Platform::operator()() {
    return _id;
}

bool clcpp::Platform::isDeviceTypeEnabled(cl_device_type dtype) {
    cl_uint numDevices = 0;
    cl_int err = clGetDeviceIDs(_id, dtype, 0, NULL, &numDevices);
    if (err != CL_SUCCESS) {
        return false;
    }

    return numDevices > 0;
}

void clcpp::Platform::getDevices(cl_device_type dtype, std::vector<Device> &devices) {
    cl_uint numDevices = 0;
    cl_int err = clGetDeviceIDs(_id, dtype, 0, NULL, &numDevices);
    if (err != CL_SUCCESS || numDevices == 0) {
        return;
    }

    std::vector<cl_device_id> deviceIDs(numDevices);
    err = clGetDeviceIDs(_id, dtype, deviceIDs.size(), deviceIDs.data(), NULL);
    if (err != CL_SUCCESS) {
        return;
    }

    devices.reserve(deviceIDs.size());
    for (size_t i = 0; i < deviceIDs.size(); i++) {
        Device d(deviceIDs[i]);
        devices.push_back(d);
    }
}

void clcpp::Platform::getDevices(cl_device_type dtype, 
                                 std::string deviceName, 
                                 std::vector<Device> &devices) {
    std::vector<Device> allDevices;
    getDevices(dtype, allDevices);
    for (size_t i = 0; i < allDevices.size(); i++) {
        DeviceInfo info = allDevices[i].getDeviceInfo();
        if (info.cl_device_name == deviceName) {
            devices.push_back(allDevices[i]);
        }
    }
}

clcpp::ContextProperties clcpp::Platform::getContextProperties() {
    return ContextProperties(CL_CONTEXT_PLATFORM, (cl_context_properties)_id, 0);
}

float clcpp::Platform::getComputeScore(cl_device_type dtype) {
    std::vector<Device> devices;
    getDevices(dtype, devices);

    float maxScore = 0.0f;
    for (size_t i = 0; i < devices.size(); i++) {
        maxScore = std::max(maxScore, devices[i].getComputeScore());
    }

    return maxScore;
}

void clcpp::Platform::get(std::vector<clcpp::Platform> &platforms) {
    cl_uint numPlatforms = 0;
    cl_int err = clGetPlatformIDs(0, NULL, &numPlatforms);
    if (err != CL_SUCCESS || numPlatforms == 0) {
        return;
    }

    std::vector<cl_platform_id> platformIDs(numPlatforms);
    err = clGetPlatformIDs(platformIDs.size(), platformIDs.data(), NULL);
    if (err != CL_SUCCESS) {
        return;
    }

    platforms.reserve(platformIDs.size());
    for (size_t i = 0; i < platformIDs.size(); i++) {
        Platform p(platformIDs[i]);
        platforms.push_back(p);
    }
}

void clcpp::Platform::get(cl_device_type dtype, std::vector<Platform> &platforms) {
    std::vector<Platform> allPlatforms;
    get(allPlatforms);
    for (size_t i = 0; i < allPlatforms.size(); i++) {
        if (allPlatforms[i].isDeviceTypeEnabled(dtype)) {
            platforms.push_back(allPlatforms[i]);
        }
    }
}

void clcpp::Platform::get(cl_device_type dtype, std::string deviceName, std::vector<Platform> &platforms) {
    std::vector<Platform> allPlatforms;
    get(allPlatforms);
    for (size_t i = 0; i < allPlatforms.size(); i++) {
        if (allPlatforms[i].isDeviceTypeEnabled(dtype)) {
            std::vector<Device> devices;
            allPlatforms[i].getDevices(dtype, deviceName, devices);
            if (devices.size() > 0) {
                platforms.push_back(allPlatforms[i]);
            }
        }
    }
}

/********************************************************************************
    DEVICE
********************************************************************************/

clcpp::Device::Device() {
}

clcpp::Device::Device(cl_device_id did) {
    _id = did;
    _isInitialized = true;
}

cl_device_id clcpp::Device::operator()() {
    return _id;
}

clcpp::DeviceInfo clcpp::Device::getDeviceInfo() {
    DeviceInfo info;
    if (!_isInitialized) {
        return info;
    }

    char tempstr[4096];
    clGetDeviceInfo(_id, CL_DEVICE_NAME, 4096, &tempstr, NULL);
    info.cl_device_name = std::string(tempstr);
    clGetDeviceInfo(_id, CL_DEVICE_VENDOR, 4096, &tempstr, NULL);
    info.cl_device_vendor = std::string(tempstr);
    clGetDeviceInfo(_id, CL_DEVICE_VERSION, 4096, &tempstr, NULL);
    info.cl_device_version = std::string(tempstr);
    clGetDeviceInfo(_id, CL_DRIVER_VERSION, 4096, &tempstr, NULL);
    info.cl_driver_version = std::string(tempstr);
    clGetDeviceInfo(_id, CL_DEVICE_OPENCL_C_VERSION, 4096, &tempstr, NULL);
    info.cl_device_opencl_c_version = std::string(tempstr);
    
    clGetDeviceInfo(_id, CL_DEVICE_TYPE, 
                    sizeof(cl_device_type), &(info.device_type), NULL);
    clGetDeviceInfo(_id, CL_DEVICE_MAX_CLOCK_FREQUENCY, 
                    sizeof(cl_uint), &(info.cl_device_max_clock_frequency), NULL);
    clGetDeviceInfo(_id, CL_DEVICE_MAX_COMPUTE_UNITS, 
                    sizeof(cl_uint), &(info.cl_device_max_compute_units), NULL);
    clGetDeviceInfo(_id, CL_DEVICE_GLOBAL_MEM_SIZE, 
                    sizeof(cl_ulong), &(info.cl_device_global_mem_size), NULL);
    clGetDeviceInfo(_id, CL_DEVICE_LOCAL_MEM_SIZE, 
                    sizeof(cl_ulong), &(info.cl_device_local_mem_size), NULL);
    clGetDeviceInfo(_id, CL_DEVICE_MAX_MEM_ALLOC_SIZE, 
                    sizeof(cl_ulong), &(info.cl_device_max_mem_alloc_size), NULL);
    clGetDeviceInfo(_id, CL_DEVICE_MAX_WORK_GROUP_SIZE, 
                    sizeof(size_t), &(info.cl_device_max_work_group_size), NULL);

    cl_uint dimsize = 0;
    clGetDeviceInfo(_id, CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS, sizeof(cl_uint), &dimsize, NULL);
    std::vector<size_t> dims(dimsize);
    clGetDeviceInfo(_id, CL_DEVICE_MAX_WORK_ITEM_SIZES, dims.size()*sizeof(size_t), dims.data(), NULL);
    
    GridIndex groupdims(1, 1, 1);
    if (dims.size() >= 1) {
        groupdims.i = (int)dims[0];
    }
    if (dims.size() >= 2) {
        groupdims.j = (int)dims[1];
    }
    if (dims.size() >= 3) {
        groupdims.k = (int)dims[2];
    }
    info.cl_device_max_work_item_sizes = groupdims;

    return info;
}

std::string clcpp::Device::getDeviceInfoString() {
    return getDeviceInfo().toString();
}

float clcpp::Device::getComputeScore() {
    if (!_isInitialized) {
        return 0.0f;
    }

    DeviceInfo info = getDeviceInfo();
    return (float)(info.cl_device_max_clock_frequency) * (float)(info.cl_device_max_compute_units);
}

/********************************************************************************
    CONTEXT
********************************************************************************/

clcpp::Context::Context() {
}

clcpp::Context::~Context() {
    if (_isInitialized) {
        _release();
    }
}

cl_int clcpp::Context::createContext(cl_device_type dtype, ContextProperties cprops) {
    if (_isInitialized) {
        _release();
    }

    std::vector<Device> devices;
    Platform platform = cprops.getPlatform();
    platform.getDevices(dtype, devices);
    if (devices.empty()) {
        return CL_DEVICE_NOT_AVAILABLE;
    }

    std::vector<cl_device_id> deviceIDs(devices.size());
    for (size_t i = 0; i < devices.size(); i++) {
        deviceIDs[i] = devices[i]();
    }

    cl_int err;
    cl_context ctx = clCreateContext(
            cprops(), deviceIDs.size(), deviceIDs.data(), NULL, NULL, &err);
    if (err != CL_SUCCESS) {
        return err;
    }

    _context = ctx;
    _contextPlatform = platform;
    _deviceType = dtype;
    _isInitialized = true;

    return CL_SUCCESS;
}

std::vector<clcpp::Device> clcpp::Context::getDevices() {
    std::vector<Device> devices;
    _contextPlatform.getDevices(_deviceType, devices);
    return devices;
}

std::vector<clcpp::Device> clcpp::Context::getDevices(std::string deviceName) {
    std::vector<Device> devices;
    _contextPlatform.getDevices(_deviceType, deviceName, devices);
    return devices;
}

cl_context clcpp::Context::operator()() {
    return _context;
}

void clcpp::Context::_release() {
    if (_isInitialized) {
        clReleaseContext(_context);
        _isInitialized = false;
    }
}

/********************************************************************************
    PROGRAM
********************************************************************************/

clcpp::Program::Program() {
}

clcpp::Program::~Program() {
    if (_isInitialized) {
        _release();
    }
}

cl_int clcpp::Program::createProgram(Context &ctx, std::string &source) {
    if (_isInitialized) {
        _release();
    }

    const char *csource[] = {source.c_str()};
    cl_int err;
    cl_program prog = clCreateProgramWithSource(ctx(), 1, csource, NULL, &err);
    if (err != CL_SUCCESS) {
        return err;
    }
    
    _program = prog;
    _isInitialized = true;

    return CL_SUCCESS;
}

cl_int clcpp::Program::build(Device &device) {
    cl_device_id deviceIDs[] = {device()};
    return clBuildProgram(_program, 1, deviceIDs, NULL, NULL, NULL);
}

cl_program clcpp::Program::operator()() {
    return _program;
}

void clcpp::Program::_release() {
    if (_isInitialized) {
        clReleaseProgram(_program);
        _isInitialized = false;
    }
}

/********************************************************************************
    KERNEL
********************************************************************************/
    
clcpp::Kernel::Kernel() {
}

clcpp::Kernel::~Kernel() {
    if (_isInitialized) {
        _release();
    }
}

cl_int clcpp::Kernel::createKernel(Program &program, std::string kernelName) {
    if (_isInitialized) {
        _release();
    }

    cl_int err;
    cl_kernel k = clCreateKernel(program(), kernelName.c_str(), &err);
    if (err != CL_SUCCESS) {
        return err;
    }

    _kernel = k;
    _isInitialized = true;

    return CL_SUCCESS;
}

clcpp::KernelInfo clcpp::Kernel::getKernelInfo() {
    KernelInfo info;
    if (!_isInitialized) {
        return info;
    }

    cl_program program;
    clGetKernelInfo(_kernel, CL_KERNEL_PROGRAM, sizeof(cl_program), &program, NULL);
    cl_device_id deviceID;
    clGetProgramInfo(program, CL_PROGRAM_DEVICES, sizeof(cl_device_id), &deviceID, NULL);

    char tempstr[4096];
    clGetKernelInfo(_kernel, CL_KERNEL_FUNCTION_NAME, 4096, &tempstr, NULL);
    info.cl_kernel_function_name = std::string(tempstr);

    clGetKernelInfo(_kernel, CL_KERNEL_NUM_ARGS,
                    sizeof(cl_uint), &(info.cl_kernel_num_args), NULL);
    clGetKernelWorkGroupInfo(_kernel, deviceID, CL_KERNEL_WORK_GROUP_SIZE,
                             sizeof(size_t), &(info.cl_kernel_work_group_size), NULL);
    clGetKernelWorkGroupInfo(_kernel, deviceID, CL_KERNEL_LOCAL_MEM_SIZE,
                             sizeof(cl_ulong), &(info.cl_kernel_local_mem_size), NULL);
    clGetKernelWorkGroupInfo(_kernel, deviceID, CL_KERNEL_PRIVATE_MEM_SIZE,
                             sizeof(cl_ulong), &(info.cl_kernel_private_mem_size), NULL);
    clGetKernelWorkGroupInfo(_kernel, deviceID, CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE,
                             sizeof(size_t), &(info.cl_kernel_preferred_work_group_size_multiple), NULL);

    return info;
}

std::string clcpp::Kernel::getKernelInfoString() {
    return getKernelInfo().toString();
}

cl_int clcpp::Kernel::setArg(cl_uint idx, size_t bytes, void *arg) {
    return clSetKernelArg(_kernel, idx, bytes, arg);
}

cl_int clcpp::Kernel::setArg(cl_uint idx, Buffer &buffer) {
    return clSetKernelArg(_kernel, idx, sizeof(cl_mem), buffer());
}

cl_kernel clcpp::Kernel::operator()() {
    return _kernel;
}

void clcpp::Kernel::_release() {
    if (_isInitialized) {
        clReleaseKernel(_kernel);
        _isInitialized = false;
    }
}


/********************************************************************************
    COMMAND QUEUE
********************************************************************************/

clcpp::CommandQueue::CommandQueue() {
}

clcpp::CommandQueue::~CommandQueue() {
    if (_isInitialized) {
        _release();
    }
}

cl_int clcpp::CommandQueue::createCommandQueue(Context &ctx, Device &device) {
    if (_isInitialized) {
        _release();
    }

    cl_int err;
    cl_command_queue queue = clCreateCommandQueue(ctx(), device(), 0, &err);
    if (err != CL_SUCCESS) {
        return err;
    }

    _commandQueue = queue;
    _isInitialized = true;

    return CL_SUCCESS;
}

cl_int clcpp::CommandQueue::enqueueNDRangeKernel(Kernel &kernel, 
                                                 NDRange globalWorkOffset,
                                                 NDRange globalWorkSize,
                                                 NDRange localWorkOffset,
                                                 Event &event) {
    return clEnqueueNDRangeKernel(
                _commandQueue, kernel(),
                globalWorkOffset.size(),
                globalWorkOffset(), globalWorkSize(), localWorkOffset(),
                0, NULL, event()
                );
}

cl_int clcpp::CommandQueue::enqueueReadBuffer(Buffer &src, size_t bytes, void *dst) {
    return clEnqueueReadBuffer(_commandQueue, *(src()), CL_TRUE, 0, bytes, dst,  0, NULL, NULL);
}

cl_command_queue clcpp::CommandQueue::operator()() {
    return _commandQueue;
}

void clcpp::CommandQueue::_release() {
    if (_isInitialized) {
        clReleaseCommandQueue(_commandQueue);
        _isInitialized = false;
    }
}

/********************************************************************************
    BUFFER
********************************************************************************/

clcpp::Buffer::Buffer() {
}

clcpp::Buffer::~Buffer() {
    if (_isInitialized) {
        _release();
    }
}

cl_int clcpp::Buffer::createBuffer(Context &ctx, cl_mem_flags flags, size_t bytes, void *hostptr) {
    if (_isInitialized) {
        _release();
    }

    cl_int err;
    cl_mem b = clCreateBuffer(ctx(), flags, bytes, hostptr, &err);
    if (err != CL_SUCCESS) {
        return err;
    }

    _buffer = b;
    _isInitialized = true;

    return CL_SUCCESS;
}

cl_mem* clcpp::Buffer::operator()() {
    return &_buffer;
}

void clcpp::Buffer::_release() {
    if (_isInitialized) {
        clReleaseMemObject(_buffer);
        _isInitialized = false;
    }
}

/********************************************************************************
    EVENT
********************************************************************************/

clcpp::Event::Event() {
}

clcpp::Event::~Event() {
    if (_isInitialized) {
        _release();
    }
}

cl_int clcpp::Event::createEvent(Context &ctx) {
    if (_isInitialized) {
        _release();
    }

    cl_int err;
    cl_event e = clCreateUserEvent(ctx(), &err);
    if (err != CL_SUCCESS) {
        return err;
    }

    _event = e;
    _isInitialized = true;

    return CL_SUCCESS;
}

cl_int clcpp::Event::wait() {
    return clWaitForEvents(1, &_event);
}

cl_event* clcpp::Event::operator()() {
    return &_event;
}

void clcpp::Event::_release() {
    if (_isInitialized) {
        clReleaseEvent(_event);
        _isInitialized = false;
    }
}

/********************************************************************************
    EVENT
********************************************************************************/

clcpp::NDRange::NDRange(size_t d1) {
    _dims = std::vector<size_t>({d1});
}

clcpp::NDRange::NDRange(size_t d1, size_t d2) {
    _dims = std::vector<size_t>({d1, d2});
}

clcpp::NDRange::NDRange(size_t d1, size_t d2, size_t d3) {
    _dims = std::vector<size_t>({d1, d2, d3});
}

cl_uint clcpp::NDRange::size() {
    return (cl_uint)(_dims.size());
}

size_t* clcpp::NDRange::operator()() {
    return _dims.data();
}

#endif
// ENDIF WITH_OPENCL