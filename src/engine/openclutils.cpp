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

#include "openclutils.h"

#if WITH_OPENCL
bool OpenCLUtils::_isOpenCLEnabled = true;
#else
bool OpenCLUtils::_isOpenCLEnabled = false;
#endif

std::string OpenCLUtils::_preferredGPUDevice;

bool OpenCLUtils::isOpenCLEnabled() {
    return _isOpenCLEnabled;
}

int OpenCLUtils::getNumGPUDevices() {
    int numDevices = 0;

#if WITH_OPENCL

    std::vector<clcpp::Platform> platforms;
    clcpp::Platform::get(CL_DEVICE_TYPE_GPU, platforms);

    for (size_t i = 0; i < platforms.size(); i++) {
        std::vector<clcpp::Device> devices;
        platforms[i].getDevices(CL_DEVICE_TYPE_GPU, devices);
        numDevices += (int)devices.size();
    }

    return numDevices;

#endif
// ENDIF WITH_OPENCL

    return numDevices;

}

std::vector<clcpp::DeviceInfo> OpenCLUtils::getGPUDevices() {
    std::vector<clcpp::DeviceInfo> info;

#if WITH_OPENCL

    std::vector<clcpp::Platform> platforms;
    clcpp::Platform::get(CL_DEVICE_TYPE_GPU, platforms);

    for (size_t i = 0; i < platforms.size(); i++) {
        std::vector<clcpp::Device> devices;
        platforms[i].getDevices(CL_DEVICE_TYPE_GPU, devices);
        for (size_t j = 0; j < devices.size(); j++) {
            info.push_back(devices[j].getDeviceInfo());
        }
    }

#endif
// ENDIF WITH_OPENCL

    return info;
}

std::string OpenCLUtils::getPreferredGPUDevice() {
    return _preferredGPUDevice;
}

void OpenCLUtils::setPreferredGPUDevice(std::string device_name) {
    _preferredGPUDevice = device_name;
}
