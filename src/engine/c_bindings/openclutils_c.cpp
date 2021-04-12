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

#include "../openclutils.h"
#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

#define DEVICE_STRING_LEN 4096

extern "C" {

    typedef struct GPUDevice_t {
        char name[DEVICE_STRING_LEN];
        char description[DEVICE_STRING_LEN]; 
        float score;
    } GPUDevice_t;

    EXPORTDLL int OpenCLUtils_get_num_gpu_devices(int *err) {
        *err = CBindings::SUCCESS;
        int numDevices = 0;
        try {
            numDevices = OpenCLUtils::getNumGPUDevices();
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }

        return numDevices;
    }

    EXPORTDLL void OpenCLUtils_get_gpu_devices(GPUDevice_t *devices, int num_devices, int *err) {
        *err = CBindings::SUCCESS;
        try {

#if WITH_OPENCL

            std::vector<clcpp::DeviceInfo> info = OpenCLUtils::getGPUDevices();
            num_devices = std::min((int)info.size(), num_devices);
            for (int i = 0; i < num_devices; i++) {
                std::string name = info[i].cl_device_name;
                std::string description = info[i].cl_device_vendor + ", " + info[i].cl_device_version;
                float score = (float)(info[i].cl_device_max_clock_frequency) * (float)(info[i].cl_device_max_compute_units);

                name.copy(devices[i].name, DEVICE_STRING_LEN);
                description.copy(devices[i].description, DEVICE_STRING_LEN);
                devices[i].score = score;
            }

#endif
// ENDIF WITH_OPENCL
            
        } catch (std::exception &ex) {
            CBindings::set_error_message(ex);
            *err = CBindings::FAIL;
        }
    }
}
