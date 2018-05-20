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

#include "particleadvector.h"

#include "openclutils.h"
#include "kernels/kernels.h"
#include "macvelocityfield.h"

ParticleAdvector::ParticleAdvector() {
}

bool ParticleAdvector::initialize() {
    #if WITH_OPENCL

    std::ostringstream ss;
    cl_int err = _initializeCLContext();
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL context. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err;
    }

    err = _initializeCLDevice();
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL device. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return false;
    }
    
    err = _initializeCLKernel();
    if (err != CL_SUCCESS) {
        // error message set inside of _initializeCLKernel method
        return false;
    }

    err = _initializeCLCommandQueue();
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL command queue. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return false;
    }

    _isInitialized = true;
    return true;

    #else

    return false;

    #endif
    // ENDIF WITH_OPENCL
}

bool ParticleAdvector::isInitialized() {
    return _isInitialized;
}

std::string ParticleAdvector::getInitializationErrorMessage() {
    return _initializationErrorMessage;
}


std::string ParticleAdvector::getDeviceInfo() {
    std::ostringstream ss;
    if (!_isInitialized) {
        return ss.str();
    }

    #if WITH_OPENCL

    return _CLDevice.getDeviceInfoString();

    #endif
    // ENDIF WITH_OPENCL

    return ss.str();
}

std::string ParticleAdvector::getKernelInfo() {
    std::ostringstream ss;
    if (!_isInitialized) {
        return ss.str();
    }

    #if WITH_OPENCL

    return _CLKernel.getKernelInfoString();

    #endif
    // ENDIF WITH_OPENCL

    return ss.str();
}

void ParticleAdvector::disableOpenCL() {
    _isOpenCLEnabled = false;
}

void ParticleAdvector::enableOpenCL() {
    _isOpenCLEnabled = true;
}

bool ParticleAdvector::isOpenCLEnabled() {
    return _isOpenCLEnabled;
}

int ParticleAdvector::getKernelWorkLoadSize() {
    return _kernelWorkLoadSize;
}

void ParticleAdvector::setKernelWorkLoadSize(int n) {
    _kernelWorkLoadSize = n;
}

void ParticleAdvector::advectParticlesRK4(std::vector<vmath::vec3> &particles,
                                          MACVelocityField *vfield, 
                                          double dt,
                                          std::vector<vmath::vec3> &output) {
    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _advectParticlesRK4NoCL(particles, vfield, dt, output);
        return;
    }

    #if WITH_OPENCL

    /*
        // Classic fourth-order method
        vmath::vec3 RK4(vmath::vec3 p0, double dt) {
            vmath::vec3 k1 = getVelocityAtPosition(p0);
            vmath::vec3 k2 = getVelocityAtPosition(p0 + (float)(0.5*dt)*k1);
            vmath::vec3 k3 = getVelocityAtPosition(p0 + (float)(0.5*dt)*k2);
            vmath::vec3 k4 = getVelocityAtPosition(p0 + (float)dt*k3);
            
            vmath::vec3 p1 = p0 + (float)(dt/6.0f)*(k1 + 2.0f*k2 + 2.0f*k3 + k4);

            return p1;
        }
    */
    // The following code is a vectorized version of the above code.

    output.clear();
    output.reserve(particles.size());
    for (unsigned int i = 0; i < particles.size(); i++) {
        output.push_back(particles[i]);
    }

    std::vector<vmath::vec3> tempdata;
    tempdata.reserve(particles.size());

    trilinearInterpolate(particles, vfield, tempdata);

    float scale = (float)dt / 6.0f;
    vmath::vec3 v;
    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * tempdata[i];
        tempdata[i] = particles[i] + (float)(0.5*dt) * tempdata[i];
    }

    trilinearInterpolate(tempdata, vfield);

    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * 2.0f * tempdata[i];
        tempdata[i] = particles[i] + (float)(0.5*dt) * tempdata[i];
    }

    trilinearInterpolate(tempdata, vfield);

    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * 2.0f * tempdata[i];
        tempdata[i] = particles[i] + (float)dt * tempdata[i];
    }

    trilinearInterpolate(tempdata, vfield);

    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * tempdata[i];
    }

    #endif
    // ENDIF WITH_OPENCL
}

void ParticleAdvector::advectParticlesRK3(std::vector<vmath::vec3> &particles,
                                          MACVelocityField *vfield, 
                                          double dt,
                                          std::vector<vmath::vec3> &output) {
    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _advectParticlesRK3NoCL(particles, vfield, dt, output);
        return;
    }

    #if WITH_OPENCL

    /*
        // Ralston's third order method (Ralston 62)
        vmath::vec3 RK3(vmath::vec3 p0, double dt) {
            vmath::vec3 k1 = getVelocityAtPosition(p0);
            vmath::vec3 k2 = getVelocityAtPosition(p0 + (float)(0.5*dt)*k1);
            vmath::vec3 k3 = getVelocityAtPosition(p0 + (float)(0.75*dt)*k2);
            vmath::vec3 p1 = p0 + (float)(dt/9.0f)*(2.0f*k1 + 3.0f*k2 + 4.0f*k3);

            return p1;
        }
    */
    // The following code is a vectorized version of the above code.

    output.clear();
    output.reserve(particles.size());
    for (unsigned int i = 0; i < particles.size(); i++) {
        output.push_back(particles[i]);
    }

    std::vector<vmath::vec3> tempdata;
    tempdata.reserve(particles.size());

    trilinearInterpolate(particles, vfield, tempdata);

    float scale = (float)dt / 9.0f;
    vmath::vec3 v;
    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * 2.0f * tempdata[i];
        tempdata[i] = particles[i] + (float)(0.5*dt) * tempdata[i];
    }

    trilinearInterpolate(tempdata, vfield);

    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * 3.0f * tempdata[i];
        tempdata[i] = particles[i] + (float)(0.75*dt) * tempdata[i];
    }

    trilinearInterpolate(tempdata, vfield);

    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output[i] += scale * 4.0f * tempdata[i];
    }

    #endif
    // ENDIF WITH_OPENCL
}

void ParticleAdvector::advectParticlesRK2(std::vector<vmath::vec3> &particles,
                                          MACVelocityField *vfield, 
                                          double dt,
                                          std::vector<vmath::vec3> &output) {
    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _advectParticlesRK2NoCL(particles, vfield, dt, output);
        return;
    }

    #if WITH_OPENCL

    /*
        // Midpoint method
        vmath::vec3 RK2(vmath::vec3 p0, double dt) {
            vmath::vec3 k1 = getVelocityAtPosition(p0);
            vmath::vec3 k2 = getVelocityAtPosition(p0 + (float)(0.5*dt)*k1);
            vmath::vec3 p1 = p0 + (float)dt*k2;

            return p1;
        }
    */
    // The following code is a vectorized version of the above code.

    std::vector<vmath::vec3> tempdata;
    tempdata.reserve(particles.size());

    trilinearInterpolate(particles, vfield, tempdata);

    for (unsigned int i = 0; i < tempdata.size(); i++) {
        tempdata[i] = particles[i] + (float)(0.5*dt) * tempdata[i];
    }

    trilinearInterpolate(tempdata, vfield);

    output.clear();
    output.reserve(particles.size());
    for (unsigned int i = 0; i < tempdata.size(); i++) {
        output.push_back(particles[i] + (float)dt * tempdata[i]);
    }

    #endif
    // ENDIF WITH_OPENCL
}

void ParticleAdvector::advectParticlesRK1(std::vector<vmath::vec3> &particles,
                                          MACVelocityField *vfield, 
                                          double dt,
                                          std::vector<vmath::vec3> &output) {
    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _advectParticlesRK1NoCL(particles, vfield, dt, output);
        return;
    }

    #if WITH_OPENCL

    /*  // Forward Euler
        vmath::vec3 RK1(vmath::vec3 p0, double dt) {
            vmath::vec3 k1 = getVelocityAtPosition(p0);
            vmath::vec3 p1 = p0 + (float)dt*k1;

            return p1;
        }
    */
    // The following code is a vectorized version of the above code.

    trilinearInterpolate(particles, vfield, output);

    for (unsigned int i = 0; i < output.size(); i++) {
        output[i] = particles[i] + (float)dt * output[i];
    }

    #endif
}

void ParticleAdvector::trilinearInterpolate(std::vector<vmath::vec3> &particles,
                                           MACVelocityField *vfield,
                                           std::vector<vmath::vec3> &output) {
    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _trilinearInterpolateNoCL(particles, vfield, output);
        return;
    }

    #if WITH_OPENCL

    vfield->getGridDimensions(&_isize, &_jsize, &_ksize);
    _dx = vfield->getGridCellSize();

    int chunki = _dataChunkWidth;
    int chunkj = _dataChunkHeight;
    int chunkk = _dataChunkDepth;
    int chunkgridi = ceil((double)_isize / (double)(chunki));
    int chunkgridj = ceil((double)_jsize / (double)(chunkj));
    int chunkgridk = ceil((double)_ksize / (double)(chunkk));

    Array3d<ParticleChunk> particleGrid(chunkgridi, chunkgridj, chunkgridk);

    _getParticleChunkGrid(chunki*_dx, chunkj*_dx, chunkk*_dx, 
                          particles, particleGrid);

    std::vector<DataChunkParameters> chunkParams;
    _getDataChunkParameters(vfield, particleGrid, chunkParams);

    int maxChunks = _getMaxChunksPerComputation();
    int numComputations = ceil((double)chunkParams.size() / (double) maxChunks);

    output.reserve(particles.size());
    for (size_t i = output.size(); i < particles.size(); i++) {
        output.push_back(vmath::vec3());
    }

    std::vector<DataChunkParameters> chunks;
    for (int i = 0; i < numComputations; i++) {
        int begidx = i*maxChunks;
        int endidx = begidx + maxChunks;
        if (endidx > (int)chunkParams.size()) {
            endidx = (int)chunkParams.size();
        }

        std::vector<DataChunkParameters>::iterator beg = chunkParams.begin() + begidx;
        std::vector<DataChunkParameters>::iterator end = chunkParams.begin() + endidx;

        chunks.clear();
        chunks.insert(chunks.begin(), beg, end);

        _trilinearInterpolateChunks(chunks, output);
    }

    _validateOutput(output);

    #endif
    // ENDIF WITH_OPENCL
}

void ParticleAdvector::trilinearInterpolate(std::vector<vmath::vec3> &particles,
                                           MACVelocityField *vfield) {
    if (!_isOpenCLEnabled || !OpenCLUtils::isOpenCLEnabled()) {
        _trilinearInterpolateNoCL(particles, vfield, particles);
        return;
    }

    #if WITH_OPENCL

    trilinearInterpolate(particles, vfield, particles);

    #endif
    // ENDIF WITH_OPENCL
}

vmath::vec3 ParticleAdvector::_RK4(vmath::vec3 p0, double dt, MACVelocityField *vfield) {
    vmath::vec3 k1 = vfield->evaluateVelocityAtPositionLinear(p0);
    vmath::vec3 k2 = vfield->evaluateVelocityAtPositionLinear(p0 + (float)(0.5*dt)*k1);
    vmath::vec3 k3 = vfield->evaluateVelocityAtPositionLinear(p0 + (float)(0.5*dt)*k2);
    vmath::vec3 k4 = vfield->evaluateVelocityAtPositionLinear(p0 + (float)dt*k3);
    
    vmath::vec3 p1 = p0 + (float)(dt/6.0f)*(k1 + 2.0f*k2 + 2.0f*k3 + k4);

    return p1;
}

vmath::vec3 ParticleAdvector::_RK3(vmath::vec3 p0, double dt, MACVelocityField *vfield) {
    vmath::vec3 k1 = vfield->evaluateVelocityAtPositionLinear(p0);
    vmath::vec3 k2 = vfield->evaluateVelocityAtPositionLinear(p0 + (float)(0.5*dt)*k1);
    vmath::vec3 k3 = vfield->evaluateVelocityAtPositionLinear(p0 + (float)(0.75*dt)*k2);
    vmath::vec3 p1 = p0 + (float)(dt/9.0f)*(2.0f*k1 + 3.0f*k2 + 4.0f*k3);

    return p1;
}

vmath::vec3 ParticleAdvector::_RK2(vmath::vec3 p0, double dt, MACVelocityField *vfield) {
    vmath::vec3 k1 = vfield->evaluateVelocityAtPositionLinear(p0);
    vmath::vec3 k2 = vfield->evaluateVelocityAtPositionLinear(p0 + (float)(0.5*dt)*k1);
    vmath::vec3 p1 = p0 + (float)dt*k2;

    return p1;
}

vmath::vec3 ParticleAdvector::_RK1(vmath::vec3 p0, double dt, MACVelocityField *vfield) {
    vmath::vec3 k1 = vfield->evaluateVelocityAtPositionLinear(p0);
    vmath::vec3 p1 = p0 + (float)dt*k1;

    return p1;
}

void ParticleAdvector::_advectParticlesRK4NoCL(std::vector<vmath::vec3> &particles,
                             MACVelocityField *vfield, 
                             double dt,
                             std::vector<vmath::vec3> &output) {
    output.clear();
    output.reserve(particles.size());
    for (size_t i = 0; i < particles.size(); i++) {
        output.push_back(_RK4(particles[i], dt, vfield));
    }
}

void ParticleAdvector::_advectParticlesRK3NoCL(std::vector<vmath::vec3> &particles,
                             MACVelocityField *vfield, 
                             double dt,
                             std::vector<vmath::vec3> &output) {
    output.clear();
    output.reserve(particles.size());
    for (size_t i = 0; i < particles.size(); i++) {
        output.push_back(_RK3(particles[i], dt, vfield));
    }
}

void ParticleAdvector::_advectParticlesRK2NoCL(std::vector<vmath::vec3> &particles,
                             MACVelocityField *vfield, 
                             double dt,
                             std::vector<vmath::vec3> &output) {
    output.clear();
    output.reserve(particles.size());
    for (size_t i = 0; i < particles.size(); i++) {
        output.push_back(_RK2(particles[i], dt, vfield));
    }
}

void ParticleAdvector::_advectParticlesRK1NoCL(std::vector<vmath::vec3> &particles,
                             MACVelocityField *vfield, 
                             double dt,
                             std::vector<vmath::vec3> &output) {
    output.clear();
    output.reserve(particles.size());
    for (size_t i = 0; i < particles.size(); i++) {
        output.push_back(_RK1(particles[i], dt, vfield));
    }
}

void ParticleAdvector::_trilinearInterpolateNoCL(std::vector<vmath::vec3> &particles,
                                                 MACVelocityField *vfield, 
                                                 std::vector<vmath::vec3> &output) {
    output.reserve(particles.size());
    for (size_t i = output.size(); i < particles.size(); i++) {
        output.push_back(vmath::vec3());
    }

    for (size_t i = 0; i < particles.size(); i++) {
        output[i] = vfield->evaluateVelocityAtPositionLinear(particles[i]);
    }

    _validateOutput(output);
}

void ParticleAdvector::_validateOutput(std::vector<vmath::vec3> &output) {
    vmath::vec3 v;
    for (unsigned int i = 0; i < output.size(); i++) {
        v = output[i];
        if (std::isinf(v.x) || std::isnan(v.x) || 
                std::isinf(v.y) || std::isnan(v.y) ||
                std::isinf(v.z) || std::isnan(v.z)) {
            output[i] = vmath::vec3(0.0, 0.0, 0.0);
        }
    }
}

#if WITH_OPENCL

void ParticleAdvector::_checkError(cl_int err, const char * name) {
    if (err != CL_SUCCESS) {
        std::cerr << "ERROR: " << name  << " (" << err << ")" << std::endl;
        FLUIDSIM_ASSERT(err == CL_SUCCESS);
    }
}

cl_int ParticleAdvector::_initializeCLContext() {
    std::string deviceName = OpenCLUtils::getPreferredGPUDevice();
    std::vector<clcpp::Platform> platforms;
    clcpp::Platform::get(CL_DEVICE_TYPE_GPU, deviceName, platforms);

    clcpp::Platform platform;
    if (platforms.size() > 0) {
        platform = platforms[0];
    } else {
        clcpp::Platform::get(CL_DEVICE_TYPE_GPU, platforms);
        if (platforms.size() == 0) {
            return CL_DEVICE_NOT_FOUND;
        }

        int maxidx = -1;
        float maxscore = -1;
        for (size_t i = 0; i < platforms.size(); i++) {
            float score = platforms[i].getComputeScore(CL_DEVICE_TYPE_GPU);
            if (score > maxscore) {
                maxscore = score;
                maxidx = i;
            }
        }

        platform = platforms[maxidx];
    }

    clcpp::ContextProperties cprops = platform.getContextProperties();
    cl_int err = _CLContext.createContext(CL_DEVICE_TYPE_GPU, cprops);
    return err;
}

cl_int ParticleAdvector::_initializeCLDevice() {
    std::string deviceName = OpenCLUtils::getPreferredGPUDevice();
    std::vector<clcpp::Device> devices = _CLContext.getDevices(deviceName);

    if (devices.size() > 0) {
        _CLDevice = devices[0];
    } else {
        devices = _CLContext.getDevices();
        if (devices.empty()) {
            return CL_DEVICE_NOT_FOUND;
        }

        int maxidx = -1;
        float maxscore = -1;
        for (size_t i = 0; i < devices.size(); i++) {
            float score = devices[i].getComputeScore();
            if (score > maxscore) {
                maxscore = score;
                maxidx = i;
            }
        }

        _CLDevice = devices[maxidx];
    }

    return CL_SUCCESS;
}

cl_int ParticleAdvector::_initializeCLKernel() {
    std::ostringstream ss;
    cl_int err = _CLProgram.createProgram(_CLContext, Kernels::trilinearinterpolateCL);
    if (err != CL_SUCCESS) { 
        ss << "Unable to initialize OpenCL program. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err; 
    }

    err = _CLProgram.build(_CLDevice);
    if (err != CL_SUCCESS) { 
        ss << "Unable to build OpenCL program. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err; 
    }

    err = _CLKernel.createKernel(_CLProgram, "trilinear_interpolate_kernel");
    if (err != CL_SUCCESS) { 
        ss << "Unable to initialize OpenCL kernel (trilinear_interpolate_kernel). Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err; 
    }

    return CL_SUCCESS;
}

cl_int ParticleAdvector::_initializeCLCommandQueue() {
    return _CLQueue.createCommandQueue(_CLContext, _CLDevice);
}

void ParticleAdvector::_getParticleChunkGrid(double cwidth, double cheight, double cdepth,
                                             std::vector<vmath::vec3> &particles,
                                             Array3d<ParticleChunk> &grid) {

    double bwidth = grid.width * cwidth;
    double bheight = grid.height * cheight;
    double bdepth = grid.depth * cdepth;

    double eps = 1e-6;
    double bboxeps = 0.01 * _dx;

    // The grid boundary dimensions are reduced to keep particles away from
    // the edge. Numerical error may cause particle locations to be calculated
    // to be outside of the grid if they lie on the grid boundary.
    AABB bbox(vmath::vec3(0.0, 0.0, 0.0), bwidth, bheight, bdepth);
    bbox.expand(-bboxeps);

    Array3d<int> countGrid(grid.width, grid.height, grid.depth, 0);
    vmath::vec3 p;
    for (unsigned int i = 0; i < particles.size(); i++) {
        p = particles[i];

        if (!bbox.isPointInside(p)) {
            p = bbox.getNearestPointInsideAABB(p, eps);
        }

        int pi = (int)(p.x / cwidth);
        int pj = (int)(p.y / cheight);
        int pk = (int)(p.z / cdepth);

        FLUIDSIM_ASSERT(Grid3d::isGridIndexInRange(pi, pj, pk, grid.width, grid.height, grid.depth));

        countGrid.add(pi, pj, pk, 1);
    }

    ParticleChunk *pc;
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                pc = grid.getPointer(i, j, k);
                pc->particles.reserve(countGrid(i, j, k));
            }
        }
    }

    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                pc = grid.getPointer(i, j, k);
                pc->references.reserve(countGrid(i, j, k));
            }
        }
    }

    for (unsigned int i = 0; i < particles.size(); i++) {
        p = particles[i];

        if (!bbox.isPointInside(p)) {
            p = bbox.getNearestPointInsideAABB(p, eps);
        }

        int pi = (int)(p.x / cwidth);
        int pj = (int)(p.y / cheight);
        int pk = (int)(p.z / cdepth);

        pc = grid.getPointer(pi, pj, pk);
        pc->particles.push_back(p);
        pc->references.push_back(i);
    }

    /*
       Move particles away from the boundaries of a chunk. Due to reduced
       precision by using float32 in the OpenCL kernel, if a particle is very 
       close to the boundary of a chunk, its location could be calculated to be 
       in a different chunk from what is calculated in this method.
    */
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                bbox = AABB(i*cwidth, j*cheight, k*cdepth, cwidth, cheight, cdepth);
                bbox.expand(-bboxeps);

                pc = grid.getPointer(i, j, k);
                for (unsigned int pidx = 0; pidx < pc->particles.size(); pidx++) {
                    p = pc->particles[pidx];
                    if (!bbox.isPointInside(p)) {
                        p = bbox.getNearestPointInsideAABB(p, eps);
                        pc->particles[pidx] = p;
                    }
                }
            }
        }
    }
}

void ParticleAdvector::_getDataChunkParametersForChunkIndex(GridIndex cindex,
                                                            MACVelocityField *vfield,
                                                            ParticleChunk *particleChunk,
                                                            std::vector<DataChunkParameters> &chunkParameters) {

    if (particleChunk->particles.size() == 0) {
        return;
    }

    GridIndex indexOffset = GridIndex(cindex.i*_dataChunkWidth, 
                                      cindex.j*_dataChunkHeight, 
                                      cindex.k*_dataChunkDepth);

    double dx = vfield->getGridCellSize();
    vmath::vec3 positionOffset = Grid3d::GridIndexToPosition(indexOffset.i,
                                                             indexOffset.j,
                                                             indexOffset.k, dx);

    Array3d<float> *ugrid = vfield->getArray3dU();
    Array3d<float> *vgrid = vfield->getArray3dV();
    Array3d<float> *wgrid = vfield->getArray3dW();

    GridIndex ugridOffset(indexOffset.i - 0, indexOffset.j - 1, indexOffset.k - 1);
    GridIndex vgridOffset(indexOffset.i - 1, indexOffset.j - 0, indexOffset.k - 1);
    GridIndex wgridOffset(indexOffset.i - 1, indexOffset.j - 1, indexOffset.k - 0);

    ArrayView3d<float> ugridview(_dataChunkWidth + 1, _dataChunkHeight + 2, _dataChunkDepth + 2,
                                 ugridOffset, ugrid);
    ArrayView3d<float> vgridview(_dataChunkWidth + 2, _dataChunkHeight + 1, _dataChunkDepth + 2,
                                 vgridOffset, vgrid);
    ArrayView3d<float> wgridview(_dataChunkWidth + 2, _dataChunkHeight + 2, _dataChunkDepth + 1,
                                 wgridOffset, wgrid);

    int groupSize = _getWorkGroupSize();
    int numDataChunks = ceil((double)particleChunk->particles.size() / (double)groupSize);

    for (int i = 0; i < numDataChunks; i++) {
        DataChunkParameters params;

        int begidx = i*groupSize;
        int endidx = begidx + groupSize;
        if (endidx > (int)particleChunk->particles.size()) {
            endidx = (int)particleChunk->particles.size();
        }

        params.particlesBegin = particleChunk->particles.begin() + begidx;
        params.referencesBegin = particleChunk->references.begin() + begidx;

        params.particlesEnd = particleChunk->particles.begin() + endidx;
        params.referencesEnd = particleChunk->references.begin() + endidx;

        params.ufieldview = ugridview;
        params.vfieldview = vgridview;
        params.wfieldview = wgridview;

        params.chunkOffset = cindex;
        params.indexOffset = indexOffset;
        params.positionOffset = positionOffset;

        chunkParameters.push_back(params);
    }
}

void ParticleAdvector::_getDataChunkParameters(MACVelocityField *vfield,
                                               Array3d<ParticleChunk> &particleGrid,
                                               std::vector<DataChunkParameters> &chunkParameters) {

    GridIndex cindex;
    ParticleChunk *pc;
    for (int k = 0; k < particleGrid.depth; k++) {
        for (int j = 0; j < particleGrid.height; j++) {
            for (int i = 0; i < particleGrid.width; i++) {
                cindex = GridIndex(i, j, k);
                pc = particleGrid.getPointer(cindex);
                _getDataChunkParametersForChunkIndex(cindex, vfield, pc, chunkParameters);
            }
        }
    }
}

int ParticleAdvector::_getWorkGroupSize() {
    clcpp::DeviceInfo info = _CLDevice.getDeviceInfo();
    return fmin(info.cl_device_max_work_group_size, _maxItemsPerWorkGroup);
}

int ParticleAdvector::_getChunkPositionDataSize() {
    // <x, y, z> position data size
    return 3*sizeof(float)*_getWorkGroupSize();
}

int ParticleAdvector::_getChunkVelocityDataSize() {
    // u, v, w Velocity field data size
    int cw = _dataChunkWidth;
    int ch = _dataChunkHeight;
    int cd = _dataChunkDepth;

    int usize = sizeof(float)*(cw + 1)*(ch + 2)*(cd + 2);
    int vsize = sizeof(float)*(cw + 2)*(ch + 1)*(cd + 2);
    int wsize = sizeof(float)*(cw + 2)*(ch + 2)*(cd + 1);

    return usize + vsize + wsize;
}

int ParticleAdvector::_getChunkOffsetDataSize() {
    // <i, j, k> chunk index offset data size
    return 3*sizeof(int);
}

int ParticleAdvector::_getChunkTotalDataSize() {
    return _getChunkPositionDataSize() + 
           _getChunkVelocityDataSize() + 
           _getChunkOffsetDataSize();
}

int ParticleAdvector::_getMaxChunksPerComputation() {
    int positionSize = _getChunkPositionDataSize();
    int vfieldSize = _getChunkVelocityDataSize();
    int offsetSize = _getChunkOffsetDataSize();
    int totalSize = _getChunkTotalDataSize();

    clcpp::DeviceInfo info = _CLDevice.getDeviceInfo();
    cl_ulong maxGlobalMem = info.cl_device_global_mem_size;
    cl_ulong maxAlloc = info.cl_device_max_mem_alloc_size;

    int numPositionAllocItems = floor((double)maxAlloc / (double)positionSize);
    int numVelocityAllocItems = floor((double)maxAlloc / (double)vfieldSize);
    int numOffsetAllocItems = floor((double)maxAlloc / (double)offsetSize);

    int allocLimitCount = fmin(fmin(numPositionAllocItems, 
                                    numVelocityAllocItems),
                                    numOffsetAllocItems);

    int globalMemLimitCount = floor((double)maxGlobalMem / (double)totalSize);

    int hardwareLimit = fmin(allocLimitCount, globalMemLimitCount);
    int softwareLimit = _maxChunksPerComputation;

    return fmin(hardwareLimit, softwareLimit);
}

void ParticleAdvector::_trilinearInterpolateChunks(std::vector<DataChunkParameters> &chunks,
                                                   std::vector<vmath::vec3> &output) {
    DataBuffer buffer;
    _initializeDataBuffer(chunks, buffer);
    _setCLKernelArgs(buffer, _dx);

    int loadSize = _kernelWorkLoadSize;
    int workGroupSize = _getWorkGroupSize();
    int numWorkItems = (int)chunks.size()*workGroupSize;
    int numComputations = ceil((double)chunks.size() / (double)loadSize);

    clcpp::Event event;
    cl_int err = event.createEvent(_CLContext);
    _checkError(err, "Event::createEvent()");

    for (int i = 0; i < numComputations; i++) {
        int offset = i * loadSize * workGroupSize;
        int items = (int)fmin(numWorkItems - offset, loadSize * workGroupSize);
        
        err = _CLQueue.enqueueNDRangeKernel(_CLKernel, 
                                            clcpp::NDRange(offset), 
                                            clcpp::NDRange(items), 
                                            clcpp::NDRange(workGroupSize),
                                            event);    
        _checkError(err, "CommandQueue::enqueueNDRangeKernel()");
    }

    err = event.wait();
    _checkError(err, "Event::wait()");

    int dataSize = (int)chunks.size() * _getChunkPositionDataSize();
    err = _CLQueue.enqueueReadBuffer(buffer.positionDataCL, dataSize, buffer.positionDataH.data());
    _checkError(err, "CommandQueue::enqueueReadBuffer()");

    _setOutputData(chunks, buffer, output);
}

void ParticleAdvector::_initializeDataBuffer(std::vector<DataChunkParameters> &chunks,
                                             DataBuffer &buffer) {

    _getHostPositionDataBuffer(chunks, buffer.positionDataH);
    _getHostVelocityDataBuffer(chunks, buffer.vfieldDataH);
    _getHostChunkOffsetDataBuffer(chunks, buffer.offsetDataH);

    size_t positionDataBytes = buffer.positionDataH.size()*sizeof(vmath::vec3);
    size_t vfieldDataBytes = buffer.vfieldDataH.size()*sizeof(float);
    size_t offsetDataBytes = buffer.offsetDataH.size()*sizeof(GridIndex);

    cl_int err = buffer.positionDataCL.createBuffer(
                    _CLContext, CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR,
                    positionDataBytes, buffer.positionDataH.data()
                    );
    _checkError(err, "Creating position data buffer");

    err = buffer.vfieldDataCL.createBuffer(
                    _CLContext, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR,
                    vfieldDataBytes, buffer.vfieldDataH.data()
                    );
    _checkError(err, "Creating velocity field data buffer");

    err = buffer.offsetDataCL.createBuffer(
                    _CLContext, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR,
                    offsetDataBytes, buffer.offsetDataH.data()
                    );
    _checkError(err, "Creating chunk offset data buffer");
}

void ParticleAdvector::_getHostPositionDataBuffer(std::vector<DataChunkParameters> &chunks,
                                                  std::vector<vmath::vec3> &buffer) {

    int groupSize = _getWorkGroupSize();
    int numElements = (int)chunks.size()*groupSize;
    buffer.reserve(numElements);

    DataChunkParameters c;
    vmath::vec3 p;
    for (unsigned int i = 0; i < chunks.size(); i++) {
        c = chunks[i];

        int numPoints = c.particlesEnd - c.particlesBegin;
        int numPad = groupSize - numPoints;
        vmath::vec3 defaultPosition = c.positionOffset;

        buffer.insert(buffer.end(), c.particlesBegin, c.particlesEnd);
        for (int i = 0; i < numPad; i++) {
            buffer.push_back(defaultPosition);
        }
    }
}

void ParticleAdvector::_getHostVelocityDataBuffer(std::vector<DataChunkParameters> &chunks,
                                                  std::vector<float> &buffer) {

    int numElements = _getChunkVelocityDataSize() / sizeof(float);
    buffer.reserve(numElements);
    for (unsigned int i = 0; i < chunks.size(); i++) {
        _appendChunkVelocityDataToBuffer(chunks[i], buffer);
    }
}

void ParticleAdvector::_appendChunkVelocityDataToBuffer(DataChunkParameters &chunk, 
                                                        std::vector<float> &buffer) {

    for (int k = 0; k < chunk.ufieldview.depth; k++) {
        for (int j = 0; j < chunk.ufieldview.height; j++) {
            for (int i = 0; i < chunk.ufieldview.width; i++) {
                buffer.push_back(chunk.ufieldview(i, j, k));
            }
        }
    }

    for (int k = 0; k < chunk.vfieldview.depth; k++) {
        for (int j = 0; j < chunk.vfieldview.height; j++) {
            for (int i = 0; i < chunk.vfieldview.width; i++) {
                buffer.push_back(chunk.vfieldview(i, j, k));
            }
        }
    }

    for (int k = 0; k < chunk.wfieldview.depth; k++) {
        for (int j = 0; j < chunk.wfieldview.height; j++) {
            for (int i = 0; i < chunk.wfieldview.width; i++) {
                buffer.push_back(chunk.wfieldview(i, j, k));
            }
        }
    }
}

void ParticleAdvector::_getHostChunkOffsetDataBuffer(std::vector<DataChunkParameters> &chunks,
                                                     std::vector<GridIndex> &buffer) {
    buffer.reserve(chunks.size());
    for (unsigned int i = 0; i < chunks.size(); i++) {
        buffer.push_back(chunks[i].chunkOffset);
    }
}

void ParticleAdvector::_setCLKernelArgs(DataBuffer &buffer, float dx) {
    cl_int err = _CLKernel.setArg(0, buffer.positionDataCL);
    _checkError(err, "Kernel::setArg() - position data");

    err = _CLKernel.setArg(1, buffer.vfieldDataCL);
    _checkError(err, "Kernel::setArg() - velocity field data");

    err = _CLKernel.setArg(2, buffer.offsetDataCL);
    _checkError(err, "Kernel::setArg() - chunk offset data");

    clcpp::DeviceInfo deviceInfo = _CLDevice.getDeviceInfo();
    int vfieldLocalBytes = _getChunkVelocityDataSize();
    FLUIDSIM_ASSERT((unsigned int)vfieldLocalBytes <= deviceInfo.cl_device_local_mem_size);

    err = _CLKernel.setArg(3, vfieldLocalBytes, NULL);
    _checkError(err, "Kernel::setArg() - local vfield data");

    err = _CLKernel.setArg(4, sizeof(float), &dx);
    _checkError(err, "Kernel::setArg() - dx");
}

void ParticleAdvector::_setOutputData(std::vector<DataChunkParameters> &chunks,
                                      DataBuffer &buffer,
                                      std::vector<vmath::vec3> &output) {

    int workGroupSize = _getWorkGroupSize();

    DataChunkParameters chunk;
    for (unsigned int gidx = 0; gidx < chunks.size(); gidx++) {
        int hostOffset = gidx*workGroupSize;
        int dataOffset = 0;

        chunk = chunks[gidx];
        std::vector<int>::iterator begin = chunk.referencesBegin;
        std::vector<int>::iterator end = chunk.referencesEnd;
        for (std::vector<int>::iterator it = begin; it != end; ++it) {
            output[*it] = buffer.positionDataH[hostOffset + dataOffset];
            dataOffset++;
        }
    }
}

#endif
// ENDIF WITH_OPENCL
