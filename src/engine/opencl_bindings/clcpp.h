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

#ifndef FLUIDENGINE_CLCPP_H
#define FLUIDENGINE_CLCPP_H

#if WITH_OPENCL
    #if defined(__APPLE__) || defined(__MACOSX)
        #include <OpenCL/cl.h>
    #else
        #include <CL/cl.h>
    #endif
#endif

#include <vector>
#include <string>

#include "../array3d.h"

namespace clcpp {
#if WITH_OPENCL

/********************************************************************************
    PLATFORM
********************************************************************************/
class Device;
struct ContextProperties;

class Platform
{
public:
    Platform();
    Platform(cl_platform_id pid);

    cl_platform_id operator()();
    bool isDeviceTypeEnabled(cl_device_type dtype);
    void getDevices(cl_device_type dtype, std::vector<Device> &devices);
    void getDevices(cl_device_type dtype, std::string deviceName, std::vector<Device> &devices);
    ContextProperties getContextProperties();
    float getComputeScore(cl_device_type dtype);
    static void get(std::vector<Platform> &platforms);
    static void get(cl_device_type dtype, std::vector<Platform> &platforms);
    static void get(cl_device_type dtype, std::string deviceName, std::vector<Platform> &platforms);

private:
    cl_platform_id _id;
    bool _isInitialized = false;
};

/********************************************************************************
    DEVICE
********************************************************************************/
    
struct DeviceInfo {
    std::string toString() {
        std::ostringstream ss;

        ss << "CL_DEVICE_NAME:                " << cl_device_name << std::endl;
        ss << "CL_DEVICE_VENDOR:              " << cl_device_vendor << std::endl;
        ss << "CL_DEVICE_VERSION:             " << cl_device_version << std::endl;
        ss << "CL_DRIVER_VERSION:             " << cl_driver_version << std::endl;
        ss << "CL_DEVICE_OPENCL_C_VERSION:    " << cl_device_opencl_c_version << std::endl;

        std::string type;
        switch (device_type) {
            case CL_DEVICE_TYPE_CPU:
                type = "CPU";
                break;
            case CL_DEVICE_TYPE_GPU:
                type = "GPU";
                break;
            case CL_DEVICE_TYPE_ACCELERATOR:
                type = "ACCELERATOR";
                break;
            case CL_DEVICE_TYPE_DEFAULT:
                type = "DEFAULT";
                break;
            default:
                break;
        }
        ss << "CL_DEVICE_TYPE:                " << type << std::endl;
        ss << "CL_DEVICE_MAX_CLOCK_FREQUENCY: " << cl_device_max_clock_frequency << "MHz" << std::endl;
        ss << "CL_DEVICE_MAX_COMPUTE_UNITS:   " << cl_device_max_compute_units << std::endl;
        ss << "CL_DEVICE_GLOBAL_MEM_SIZE:     " << cl_device_global_mem_size << std::endl;
        ss << "CL_DEVICE_LOCAL_MEM_SIZE:      " << cl_device_local_mem_size << std::endl;
        ss << "CL_DEVICE_MAX_MEM_ALLOC_SIZE:  " << cl_device_max_mem_alloc_size << std::endl;
        ss << "CL_DEVICE_MAX_WORK_GROUP_SIZE: " << cl_device_max_work_group_size << std::endl;

        GridIndex g = cl_device_max_work_item_sizes;
        ss << "CL_DEVICE_MAX_WORK_ITEM_SIZES: " << g.i << " x " << g.j << " x " << g.k << std::endl;
        return ss.str();
    }

    std::string cl_device_name;
    std::string cl_device_vendor;
    std::string cl_device_version;
    std::string cl_driver_version;
    std::string cl_device_opencl_c_version;

    cl_device_type device_type;
    cl_uint cl_device_max_clock_frequency;
    cl_uint cl_device_max_compute_units;
    cl_ulong cl_device_global_mem_size;
    cl_ulong cl_device_local_mem_size;
    cl_ulong cl_device_max_mem_alloc_size;
    size_t cl_device_max_work_group_size;
    GridIndex cl_device_max_work_item_sizes;
};

class Device
{
public:
    Device();
    Device(cl_device_id did);

    cl_device_id operator()();
    DeviceInfo getDeviceInfo();
    std::string getDeviceInfoString();
    float getComputeScore();

private:
    cl_device_id _id;
    bool _isInitialized = false;
};

/********************************************************************************
    CONTEXT
********************************************************************************/

struct ContextProperties {
    ContextProperties(cl_context_properties p1, 
                    cl_context_properties p2, 
                    cl_context_properties p3) {
    properties[0] = p1;
    properties[1] = p2;
    properties[2] = p3;
    }

    cl_context_properties* operator()() {
        return properties;
    }

    Platform getPlatform() {
        return Platform((cl_platform_id)properties[1]);
    }

    cl_context_properties properties[3];
};

class Context
{
public:
    Context();
    ~Context();
    cl_int createContext(cl_device_type dtype, ContextProperties cprops);

    std::vector<Device> getDevices();
    std::vector<Device> getDevices(std::string deviceName);
    cl_context operator()();

private:
    Context(const Context& src);
    Context& operator=(const Context& src);
    void _release();

    cl_context _context;
    Platform _contextPlatform;
    cl_device_type _deviceType;
    bool _isInitialized = false;
};

/********************************************************************************
    PROGRAM
********************************************************************************/

class Program
{
public:
    Program();
    ~Program();
    cl_int createProgram(Context &ctx, std::string &source);
    cl_int build(Device &device);

    cl_program operator()();

private:
    Program(const Program& src);
    Program& operator=(const Program& src);
    void _release();

    cl_program _program;
    bool _isInitialized = false;
};

/********************************************************************************
    KERNEL
********************************************************************************/

struct KernelInfo {
    std::string toString() {
        std::ostringstream ss;
        ss << "CL_KERNEL_FUNCTION_NAME:                      " << 
              cl_kernel_function_name << std::endl;

        ss << "CL_KERNEL_NUM_ARGS:                           " << 
              cl_kernel_num_args << std::endl;
        ss << "CL_KERNEL_WORK_GROUP_SIZE:                    " << 
              cl_kernel_work_group_size << std::endl;
        ss << "CL_KERNEL_LOCAL_MEM_SIZE:                     " << 
              cl_kernel_local_mem_size << std::endl;
        ss << "CL_KERNEL_PRIVATE_MEM_SIZE:                   " << 
              cl_kernel_private_mem_size << std::endl;
        ss << "CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE: " << 
              cl_kernel_preferred_work_group_size_multiple << std::endl;
        return ss.str();
    }

    std::string cl_kernel_function_name;
    cl_uint cl_kernel_num_args;
    size_t cl_kernel_work_group_size;
    cl_ulong cl_kernel_local_mem_size;
    cl_ulong cl_kernel_private_mem_size;
    size_t cl_kernel_preferred_work_group_size_multiple;
};

class Buffer;

class Kernel
{
public:
    Kernel();
    ~Kernel();
    cl_int createKernel(Program &program, std::string kernelName);

    KernelInfo getKernelInfo();
    std::string getKernelInfoString();
    cl_int setArg(cl_uint idx, size_t bytes, void *arg);
    cl_int setArg(cl_uint idx, Buffer &buffer);
    cl_kernel operator()();

private:
    Kernel(const Kernel& src);
    Kernel& operator=(const Kernel& src);
    void _release();

    cl_kernel _kernel;
    bool _isInitialized = false;
};

/********************************************************************************
    COMMAND QUEUE
********************************************************************************/

class NDRange;
class Event;

class CommandQueue
{
public:
    CommandQueue();
    ~CommandQueue();
    cl_int createCommandQueue(Context &ctx, Device &device);

    cl_int enqueueNDRangeKernel(Kernel &kernel, 
                                NDRange globalWorkOffset,
                                NDRange globalWorkSize,
                                NDRange localWorkOffset,
                                Event &event);
    cl_int enqueueReadBuffer(Buffer &src, size_t bytes, void *dst);
    cl_command_queue operator()();

private:
    CommandQueue(const CommandQueue& src);
    CommandQueue& operator=(const CommandQueue& src);
    void _release();

    cl_command_queue _commandQueue;
    bool _isInitialized = false;
};

/********************************************************************************
    BUFFER
********************************************************************************/

class Buffer
{
public:
    Buffer();
    ~Buffer();
    cl_int createBuffer(Context &ctx, cl_mem_flags flags, size_t bytes, void *hostptr);

    cl_mem* operator()();

private:
    Buffer(const Buffer& src);
    Buffer& operator=(const Buffer& src);
    void _release();

    cl_mem _buffer;
    bool _isInitialized = false;
};


/********************************************************************************
    EVENT
********************************************************************************/

class Event
{
public:
    Event();
    ~Event();
    cl_int createEvent(Context &ctx);

    cl_int wait();
    cl_event* operator()();

private:
    Event(const Event& src);
    Event& operator=(const Event& src);
    void _release();

    cl_event _event;
    bool _isInitialized = false;
};

/********************************************************************************
    NDRange
********************************************************************************/

class NDRange
{
public:
    NDRange(size_t d1);
    NDRange(size_t d1, size_t d2);
    NDRange(size_t d1, size_t d2, size_t d3);

    cl_uint size();
    size_t* operator()();
    
private:
    std::vector<size_t> _dims;
};


#endif 
// ENDIF WITH_OPENCL
}

#endif