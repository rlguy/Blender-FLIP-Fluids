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

#include "clscalarfield.h"

#include <algorithm>

#include "openclutils.h"
#include "kernels/kernels.h"
#include "scalarfield.h"
#include "fluidsimassert.h"
#include "grid3d.h"

CLScalarField::CLScalarField() {
}

bool CLScalarField::initialize() {
    #if WITH_OPENCL

    std::ostringstream ss;
    cl_int err = _initializeCLContext();
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL context. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return false;
    }

    err = _initializeCLDevice();
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL device. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return false;
    }

    err = _initializeChunkDimensions();
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL work group size. Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return false;
    }
    
    err = _initializeCLKernels();
    if (err != CL_SUCCESS) {
        // error message set inside of _initializeCLKernels method
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

bool CLScalarField::isInitialized() {
    return _isInitialized;
}

std::string CLScalarField::getInitializationErrorMessage() {
    return _initializationErrorMessage;
}

void CLScalarField::addPoints(std::vector<vmath::vec3> &points, 
                              double radius,
                              vmath::vec3 offset,
                              double dx,
                              Array3d<float> *field) {
    if (points.empty()) {
        return;
    }

    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _addPointsNoCL(points, radius, offset, dx, field);
        return;
    }

    #if WITH_OPENCL

    _isize = field->width;
    _jsize = field->height;
    _ksize = field->depth;
    _dx = dx;
    _radius = radius;
    _offset = offset;

    bool isOutOfRangeValueSet = field->isOutOfRangeValueSet();
    if (!isOutOfRangeValueSet) {
        field->setOutOfRangeValue(0.0);
    }

    std::vector<PointValue> pointValues;
    _initializePointValues(points, pointValues);

    GridIndex workGroupDims = _getWorkGroupGridDimensions();
    Array3d<WorkGroup> workGroupGrid(workGroupDims.i, workGroupDims.j, workGroupDims.k);

    _initializeWorkGroupGrid(pointValues, field, workGroupGrid);

    std::vector<WorkChunk> workChunkQueue;
    _initializeWorkChunks(workGroupGrid, workChunkQueue);

    int maxChunks = _getMaxChunksPerPointValueComputation();
    
    std::vector<WorkChunk> chunks;
    while (!workChunkQueue.empty()) {
        _updateWorkGroupMinimumValues(workGroupGrid);

        chunks.clear();

        _getNextWorkChunksToProcess(workChunkQueue, 
                                    workGroupGrid, 
                                    chunks, 
                                    maxChunks);

        _computePointScalarField(chunks, workGroupGrid);
    }

    if (!isOutOfRangeValueSet) {
        field->setOutOfRangeValue();
    }

    #endif
    // ENDIF WITH_OPENCL
    
}

void CLScalarField::addPoints(std::vector<vmath::vec3> &points, 
                              double radius,
                              vmath::vec3 offset,
                              double dx,
                              ScalarField &isfield) {

    Array3d<float> *field = isfield.getPointerToScalarField();
    addPoints(points, radius, offset, dx, field);
}

void CLScalarField::addPoints(std::vector<vmath::vec3> &points,
                              ScalarField &isfield) {

    double r = isfield.getPointRadius();
    vmath::vec3 offset = isfield.getOffset();
    double dx = isfield.getCellSize();
    Array3d<float> *field = isfield.getPointerToScalarField();
    addPoints(points, r, offset, dx, field);
}

void CLScalarField::addPointValues(std::vector<vmath::vec3> &points, 
                                   std::vector<float> &values,
                                   double radius,
                                   vmath::vec3 offset,
                                   double dx,
                                   Array3d<float> *field) {

    FLUIDSIM_ASSERT(points.size() == values.size());

    if (points.empty()) {
        return;
    }

    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _addPointValuesNoCL(points, values, radius, offset, dx, field);
        return;
    }

    #if WITH_OPENCL

    _isize = field->width;
    _jsize = field->height;
    _ksize = field->depth;
    _dx = dx;
    _radius = radius;
    _offset = offset;

    bool isOutOfRangeValueSet = field->isOutOfRangeValueSet();
    if (!isOutOfRangeValueSet) {
        field->setOutOfRangeValue(0.0);
    }

    std::vector<PointValue> pointValues;
    _initializePointValues(points, values, pointValues);

    GridIndex workGroupDims = _getWorkGroupGridDimensions();
    Array3d<WorkGroup> workGroupGrid(workGroupDims.i, workGroupDims.j, workGroupDims.k);
    _initializeWorkGroupGrid(pointValues, field, workGroupGrid);
    
    std::vector<WorkChunk> workChunkQueue;
    _initializeWorkChunks(workGroupGrid, workChunkQueue);

    int maxChunks = _getMaxChunksPerPointValueComputation();

    std::vector<WorkChunk> chunks;
    while (!workChunkQueue.empty()) {
        _updateWorkGroupMinimumValues(workGroupGrid);

        chunks.clear();
        _getNextWorkChunksToProcess(workChunkQueue, 
                                    workGroupGrid, 
                                    chunks, 
                                    maxChunks);
        _computePointValueScalarField(chunks, workGroupGrid);
    }

    if (!isOutOfRangeValueSet) {
        field->setOutOfRangeValue();
    }

    #endif
    // ENDIF WITH_OPENCL
}

void CLScalarField::addPointValues(std::vector<vmath::vec3> &points, 
                                   std::vector<float> &values,
                                   double radius,
                                   vmath::vec3 offset,
                                   double dx,
                                   Array3d<float> *scalarfield,
                                   Array3d<float> *weightfield) {
    FLUIDSIM_ASSERT(points.size() == values.size());
    FLUIDSIM_ASSERT(scalarfield->width == weightfield->width &&
                    scalarfield->height == weightfield->height &&
                    scalarfield->depth == weightfield->depth);

    if (points.empty()) {
        return;
    }

    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _addPointValuesNoCL(points, values, radius, offset, dx, 
                            scalarfield, weightfield);
        return;
    }

    #if WITH_OPENCL

    _isize = scalarfield->width;
    _jsize = scalarfield->height;
    _ksize = scalarfield->depth;
    _dx = dx;
    _radius = radius;
    _offset = offset;

    bool isScalarFieldOutOfRangeValueSet = scalarfield->isOutOfRangeValueSet();
    bool isWeightFieldOutOfRangeValueSet = weightfield->isOutOfRangeValueSet();
    if (!isScalarFieldOutOfRangeValueSet) {
        scalarfield->setOutOfRangeValue(0.0);
    }
    if (!isWeightFieldOutOfRangeValueSet) {
        weightfield->setOutOfRangeValue(0.0);
    }

    std::vector<PointValue> pointValues;
    _initializePointValues(points, values, pointValues);

    GridIndex workGroupDims = _getWorkGroupGridDimensions();
    Array3d<WorkGroup> workGroupGrid(workGroupDims.i, workGroupDims.j, workGroupDims.k);

    _initializeWorkGroupGrid(pointValues, scalarfield, weightfield, workGroupGrid);
    
    std::vector<WorkChunk> workChunkQueue;
    _initializeWorkChunks(workGroupGrid, workChunkQueue);

    int maxChunks = _getMaxChunksPerWeightPointValueComputation();

    std::vector<WorkChunk> chunks;
    while (!workChunkQueue.empty()) {
        _updateWorkGroupMinimumValues(workGroupGrid);

        chunks.clear();
        _getNextWorkChunksToProcess(workChunkQueue, 
                                    workGroupGrid, 
                                    chunks, 
                                    maxChunks);
        _computePointValueScalarWeightField(chunks, workGroupGrid);
    }

    if (!isScalarFieldOutOfRangeValueSet) {
        scalarfield->setOutOfRangeValue();
    }
    if (!isWeightFieldOutOfRangeValueSet) {
        weightfield->setOutOfRangeValue();
    }
    
    #endif
    // ENDIF WITH_OPENCL
}

void CLScalarField::addPointValues(std::vector<vmath::vec3> &points, 
                                   std::vector<float> &values,
                                   double radius,
                                   vmath::vec3 offset,
                                   double dx,
                                   ScalarField &isfield) {

    Array3d<float> *field = isfield.getPointerToScalarField();

    if (isfield.isWeightFieldEnabled()) {
        Array3d<float> *weightfield = isfield.getPointerToWeightField();
        addPointValues(points, values, radius, offset, dx, field, weightfield);
    } else {
        addPointValues(points, values, radius, offset, dx, field);
    }
}

void CLScalarField::addPointValues(std::vector<vmath::vec3> &points, 
                                   std::vector<float> &values,
                                   ScalarField &isfield) {

    double r = isfield.getPointRadius();
    vmath::vec3 offset = isfield.getOffset();
    double dx = isfield.getCellSize();
    Array3d<float> *field = isfield.getPointerToScalarField();

    if (isfield.isWeightFieldEnabled()) {
        Array3d<float> *weightfield = isfield.getPointerToWeightField();
        addPointValues(points, values, r, offset, dx, field, weightfield);
    } else {
        addPointValues(points, values, r, offset, dx, field);
    }
}

void CLScalarField::addLevelSetPoints(std::vector<vmath::vec3> &points, 
                                      double radius,
                                      vmath::vec3 offset,
                                      double dx,
                                      Array3d<float> *field) {
    if (points.empty()) {
        return;
    }

    if (!_isOpenCLEnabled || !_isInitialized || !OpenCLUtils::isOpenCLEnabled()) {
        _addLevelSetPointsNoCL(points, radius, offset, dx, field);
        return;
    }

    #if WITH_OPENCL

    _isize = field->width;
    _jsize = field->height;
    _ksize = field->depth;
    _dx = dx;
    _radius = radius;
    _offset = offset;

    bool isOutOfRangeValueSet = field->isOutOfRangeValueSet();
    if (!isOutOfRangeValueSet) {
        field->setOutOfRangeValue(3.0f * radius);
    }

    std::vector<PointValue> pointValues;
    _initializePointValues(points, pointValues);

    GridIndex workGroupDims = _getWorkGroupGridDimensions();
    Array3d<WorkGroup> workGroupGrid(workGroupDims.i, workGroupDims.j, workGroupDims.k);

    _initializeWorkGroupGrid(pointValues, field, workGroupGrid);

    std::vector<WorkChunk> workChunkQueue;
    _initializeWorkChunks(workGroupGrid, workChunkQueue);

    int maxChunks = _getMaxChunksPerLevelSetPointComputation();
    
    std::vector<WorkChunk> chunks;
    while (!workChunkQueue.empty()) {
        _updateWorkGroupMinimumValues(workGroupGrid);

        chunks.clear();

        _getNextWorkChunksToProcess(workChunkQueue, 
                                    workGroupGrid, 
                                    chunks, 
                                    maxChunks);

        _computeLevelSetPointScalarField(chunks, workGroupGrid);
    }

    if (!isOutOfRangeValueSet) {
        field->setOutOfRangeValue();
    }

    #endif
    // ENDIF WITH_OPENCL
}

void CLScalarField::addLevelSetPoints(std::vector<vmath::vec3> &points, 
                                      double radius,
                                      vmath::vec3 offset,
                                      double dx,
                                      ScalarField &isfield) {

    Array3d<float> *field = isfield.getPointerToScalarField();
    addLevelSetPoints(points, radius, offset, dx, field);
}

void CLScalarField::addLevelSetPoints(std::vector<vmath::vec3> &points,
                                      ScalarField &isfield) {

    double r = isfield.getPointRadius();
    vmath::vec3 offset = isfield.getOffset();
    double dx = isfield.getCellSize();
    Array3d<float> *field = isfield.getPointerToScalarField();
    addLevelSetPoints(points, r, offset, dx, field);
}

void CLScalarField::setMaxScalarFieldValueThreshold(float val) {
    _isMaxScalarFieldValueThresholdSet = true;
    _maxScalarFieldValueThreshold = val;
}

void CLScalarField::setMaxScalarFieldValueThreshold() {
    _isMaxScalarFieldValueThresholdSet = false;
}

bool CLScalarField::isMaxScalarFieldValueThresholdSet() {
    return _isMaxScalarFieldValueThresholdSet;
}

double CLScalarField::getMaxScalarFieldValueThreshold() {
    return _maxScalarFieldValueThreshold;
}

std::string CLScalarField::getDeviceInfo() {
    #if WITH_OPENCL

    return _CLDevice.getDeviceInfoString();

    #else

    return std::string();

    #endif
}

std::string CLScalarField::getKernelInfo() {
    #if WITH_OPENCL

    std::string k1 = _CLKernelPoints.getKernelInfoString();
    std::string k2 = _CLKernelPointValues.getKernelInfoString();
    std::string k3 = _CLKernelWeightPointValues.getKernelInfoString();
    std::string k4 = _CLKernelLevelSetPoints.getKernelInfoString();

    return k1 + "\n" + k2 + "\n" + k3 + "\n" + k4;

    #else

    return std::string();

    #endif
    // ENDIF WITH_OPENCL
}

void CLScalarField::disableOpenCL() {
    _isOpenCLEnabled = false;
}

void CLScalarField::enableOpenCL() {
    _isOpenCLEnabled = true;
}

bool CLScalarField::isOpenCLEnabled() {
    return _isOpenCLEnabled;
}

int CLScalarField::getKernelWorkLoadSize() {
    return _kernelWorkLoadSize;
}

void CLScalarField::setKernelWorkLoadSize(int n) {
    _kernelWorkLoadSize = n;
}

void CLScalarField::_addPointsNoCL(std::vector<vmath::vec3> &points, 
                                   double radius,
                                   vmath::vec3 offset,
                                   double dx,
                                   Array3d<float> *field) {

    ScalarField calcfield(field->width, field->height, field->depth, dx);
    calcfield.setPointRadius(radius);
    calcfield.setOffset(offset);
    for (unsigned int i = 0; i < points.size(); i++) {
        calcfield.addPoint(points[i]);
    }

    Array3d<float>* calcfieldp = calcfield.getPointerToScalarField();
    _addField(calcfieldp, field);

}

void CLScalarField::_addPointValuesNoCL(std::vector<vmath::vec3> &points, 
                                        std::vector<float> &values,
                                        double radius,
                                        vmath::vec3 offset,
                                        double dx,
                                        Array3d<float> *field) {

    ScalarField calcfield(field->width, field->height, field->depth, dx);
    calcfield.setPointRadius(radius);
    calcfield.setOffset(offset);
    for (unsigned int i = 0; i < points.size(); i++) {
        calcfield.addPointValue(points[i], values[i]);
    }

    Array3d<float>* calcfieldp = calcfield.getPointerToScalarField();
    _addField(calcfieldp, field);
}

void CLScalarField::_addPointValuesNoCL(std::vector<vmath::vec3> &points, 
                                        std::vector<float> &values,
                                        double radius,
                                        vmath::vec3 offset,
                                        double dx,
                                        Array3d<float> *scalarfield,
                                        Array3d<float> *weightfield) {

    ScalarField calcfield(scalarfield->width, scalarfield->height, scalarfield->depth, dx);
    calcfield.enableWeightField();
    calcfield.setPointRadius(radius);
    calcfield.setOffset(offset);
    for (unsigned int i = 0; i < points.size(); i++) {
        calcfield.addPointValue(points[i], values[i]);
    }

    Array3d<float>* calcfieldp = calcfield.getPointerToScalarField();
    Array3d<float>* calcweightfieldp = calcfield.getPointerToWeightField();
    _addField(calcfieldp, scalarfield);
    _addField(calcweightfieldp, weightfield);
}

void CLScalarField::_addLevelSetPointsNoCL(std::vector<vmath::vec3> &points, 
                                           double r,
                                           vmath::vec3 offset,
                                           double dx,
                                           Array3d<float> *nodes) {

    GridIndex g, gmin, gmax;
    vmath::vec3 p;
    vmath::vec3 pminOffset(-r, -r, -r);
    vmath::vec3 pmaxOffset(r, r, r);
    for(size_t pidx = 0; pidx < points.size(); pidx++) {
        p = points[pidx] - offset;

        gmin = Grid3d::positionToGridIndex(p + pminOffset, dx);
        gmax = Grid3d::positionToGridIndex(p + pmaxOffset, dx);
        if (!nodes->isIndexInRange(gmin) && !nodes->isIndexInRange(gmax)) {
            continue;
        }

        gmin.i = fmax(0, gmin.i);
        gmin.j = fmax(0, gmin.j);
        gmin.k = fmax(0, gmin.k);
        gmax.i = fmin(nodes->width - 1, gmax.i);
        gmax.j = fmin(nodes->height - 1, gmax.j);
        gmax.k = fmin(nodes->depth - 1, gmax.k);

        for(int k = gmin.k; k <= gmax.k; k++) {
            for(int j = gmin.j; j <= gmax.j; j++) {
                for(int i = gmin.i; i <= gmax.i; i++) {
                    vmath::vec3 cpos = Grid3d::GridIndexToPosition(i, j, k, dx);
                    float dist = vmath::length(cpos - p) - r;
                    if (dist < nodes->get(i, j, k)) {
                        nodes->set(i, j, k, dist);
                    }
                }
            }
        }
    }
}

void CLScalarField::_addField(Array3d<float> *src, Array3d<float> *dest) {
    for (int k = 0; k < dest->depth; k++) {
        for (int j = 0; j < dest->height; j++) {
            for (int i = 0; i < dest->width; i++) {
                dest->add(i, j, k, src->get(i, j, k));
            }
        }
    }
}

#if WITH_OPENCL

cl_int CLScalarField::_initializeChunkDimensions() {
    clcpp::DeviceInfo info = _CLDevice.getDeviceInfo();

    unsigned int groupsize = (unsigned int)info.cl_device_max_work_group_size;
    groupsize = fmin(groupsize, _maxWorkGroupSize);

    if (groupsize < (unsigned int)_minWorkGroupSize) {
        return CL_INVALID_WORK_GROUP_SIZE;
    }

    std::vector<unsigned int> validsizes;
    int size = _minWorkGroupSize;
    while (size <= _maxWorkGroupSize) {
        validsizes.push_back(size);
        size *= 2;
    }

    bool isValidSize = false;
    for (unsigned int i = 0; i < validsizes.size(); i++) {
        if (groupsize == validsizes[i]) {
            isValidSize = true;
            break;
        }
    }

    if (!isValidSize) {
        for (int i = (int)validsizes.size() - 1; i >= 0; i--) {
            if (groupsize > validsizes[i]) {
                groupsize = validsizes[i];
                break;
            }
        }
    }

    int chunksize = floor(cbrt(groupsize));

    _workGroupSize = groupsize;
    _chunkWidth = chunksize;
    _chunkHeight = chunksize;
    _chunkDepth = chunksize;

    return CL_SUCCESS;
}

void CLScalarField::_checkError(cl_int err, const char * name) {
    if (err != CL_SUCCESS) {
        std::cerr << "ERROR: " << name  << " (" << err << ")" << std::endl;
        FLUIDSIM_ASSERT(err == CL_SUCCESS);
    }
}

cl_int CLScalarField::_initializeCLContext() {
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

cl_int CLScalarField::_initializeCLDevice() {
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

cl_int CLScalarField::_initializeCLKernels() {
    std::ostringstream ss;
    cl_int err = _CLProgram.createProgram(_CLContext, Kernels::scalarfieldCL);
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

    err = _CLKernelPoints.createKernel(_CLProgram, "compute_scalar_field_points");
    if (err != CL_SUCCESS) { 
        ss << "Unable to initialize OpenCL kernel (compute_scalar_field_points). Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err; 
    }

    err = _CLKernelPointValues.createKernel(_CLProgram, "compute_scalar_field_point_values");
    if (err != CL_SUCCESS) { 
        ss << "Unable to initialize OpenCL kernel (compute_scalar_field_point_values). Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err; 
    }

    err = _CLKernelWeightPointValues.createKernel(_CLProgram, "compute_scalar_weight_field_point_values");
    if (err != CL_SUCCESS) { 
        ss << "Unable to initialize OpenCL kernel (compute_scalar_weight_field_point_values). Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
        return err; 
    }

    err = _CLKernelLevelSetPoints.createKernel(_CLProgram, "compute_scalar_field_levelset_points");
    if (err != CL_SUCCESS) {
        ss << "Unable to initialize OpenCL kernel (compute_scalar_field_levelset_points). Error code: " << err << std::endl;
        _initializationErrorMessage = ss.str();
         return err; 
    }

    return CL_SUCCESS;
}

cl_int CLScalarField::_initializeCLCommandQueue() {
    return _CLQueue.createCommandQueue(_CLContext, _CLDevice);
}

/*  
    The scalarfield.cl kernels calculate field values at cell centers. We want
    values to be calculated at minimal cell corners to match the convention of
    the ScalarField class. To do this, <0.5dx, 0.5dx, 0.5dx> is
    subtracted from the offset that the user sets.
*/ 
vmath::vec3 CLScalarField::_getInternalOffset() {
    return _offset - vmath::vec3(0.5*_dx, 0.5*_dx, 0.5*_dx);
}

void CLScalarField::_initializePointValues(std::vector<vmath::vec3> &points,
                                           std::vector<PointValue> &pvs) {
    pvs.reserve(points.size());
    float defaultValue = 0.0;
    vmath::vec3 offset = _getInternalOffset();
    for (unsigned int i = 0; i < points.size(); i++) {
        pvs.push_back(PointValue(points[i] - offset, defaultValue));
    }
}

void CLScalarField::_initializePointValues(std::vector<vmath::vec3> &points,
                                           std::vector<float> &values,
                                           std::vector<PointValue> &pvs) {
    FLUIDSIM_ASSERT(points.size() == values.size());

    vmath::vec3 offset = _getInternalOffset();
    pvs.reserve(points.size());
    for (unsigned int i = 0; i < points.size(); i++) {
        pvs.push_back(PointValue(points[i] - offset, values[i]));
    }
}

GridIndex CLScalarField::_getWorkGroupGridDimensions() {
    int igrid = ceil((double)_isize / (double)_chunkWidth);
    int jgrid = ceil((double)_jsize / (double)_chunkHeight);
    int kgrid = ceil((double)_ksize / (double)_chunkDepth);
    return GridIndex(igrid, jgrid, kgrid);
}

void CLScalarField::_initializeWorkGroupGrid(std::vector<PointValue> &points,
                                             Array3d<float> *scalarfield,
                                             Array3d<WorkGroup> &grid) {
    _initializeWorkGroupParameters(grid, scalarfield);
    Array3d<int> countGrid(grid.width, grid.height, grid.depth, 0);
    //_getWorkGroupParticleCounts(points, countGrid);       // Uses less memory at the cost
                                                            // of speed if uncommented
    _reserveWorkGroupGridParticleMemory(grid, countGrid);
    _insertParticlesIntoWorkGroupGrid(points, grid);
}

void CLScalarField::_initializeWorkGroupGrid(std::vector<PointValue> &points,
                                             Array3d<float> *scalarfield,
                                             Array3d<float> *weightfield,
                                             Array3d<WorkGroup> &grid) {
    _initializeWorkGroupParameters(grid, scalarfield, weightfield);
    Array3d<int> countGrid(grid.width, grid.height, grid.depth, 0);
    //_getWorkGroupParticleCounts(points, countGrid);       // Uses less memory at the cost
                                                            // of speed if uncommented
    _reserveWorkGroupGridParticleMemory(grid, countGrid);
    _insertParticlesIntoWorkGroupGrid(points, grid);
}

void CLScalarField::_initializeWorkGroupParameters(Array3d<WorkGroup> &grid,
                                                   Array3d<float> *scalarfield) {
    GridIndex chunkOffset, indexOffset;
    vmath::vec3 positionOffset;
    WorkGroup *group;
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                group = grid.getPointer(i, j, k);

                chunkOffset = GridIndex(i, j, k);
                indexOffset = GridIndex(i*_chunkWidth, 
                                        j*_chunkHeight,
                                        k*_chunkDepth);
                positionOffset = Grid3d::GridIndexToPosition(indexOffset, _dx);

                group->fieldview = ArrayView3d<float>(_chunkWidth, _chunkHeight, _chunkDepth,
                                                      indexOffset,
                                                      scalarfield);
                group->chunkOffset = chunkOffset;
                group->indexOffset = indexOffset;
                group->positionOffset = positionOffset;
            }
        }
    }
}

void CLScalarField::_initializeWorkGroupParameters(Array3d<WorkGroup> &grid,
                                                   Array3d<float> *scalarfield,
                                                   Array3d<float> *weightfield) {
    GridIndex chunkOffset, indexOffset;
    vmath::vec3 positionOffset;
    WorkGroup *group;
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                group = grid.getPointer(i, j, k);

                chunkOffset = GridIndex(i, j, k);
                indexOffset = GridIndex(i*_chunkWidth, 
                                        j*_chunkHeight,
                                        k*_chunkDepth);
                positionOffset = Grid3d::GridIndexToPosition(indexOffset, _dx);

                group->fieldview = ArrayView3d<float>(_chunkWidth, _chunkHeight, _chunkDepth,
                                                      indexOffset,
                                                      scalarfield);
                group->weightfieldview = ArrayView3d<float>(_chunkWidth, _chunkHeight, _chunkDepth,
                                                            indexOffset,
                                                            weightfield);
                group->chunkOffset = chunkOffset;
                group->indexOffset = indexOffset;
                group->positionOffset = positionOffset;
            }
        }
    }
}

void CLScalarField::_reserveWorkGroupGridParticleMemory(Array3d<WorkGroup> &grid,
                                                        Array3d<int> &countGrid) {
    WorkGroup *group;
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                group = grid.getPointer(i, j, k);
                group->particles.reserve(countGrid(i, j, k));
            }
        }
    }
}

void CLScalarField::_getWorkGroupParticleCounts(std::vector<PointValue> &points,
                                                Array3d<int> &countGrid) {
    double chunkdx = _chunkWidth * _dx;
    double chunkdy = _chunkHeight * _dx;
    double chunkdz = _chunkDepth * _dx;
    double invchunkdx = 1.0 / chunkdx;
    double invchunkdy = 1.0 / chunkdy;
    double invchunkdz = 1.0 / chunkdz;

    GridIndex gmax(countGrid.width, countGrid.height, countGrid.depth);

    AABB cbbox(vmath::vec3(), chunkdx - 2 * _radius, 
                              chunkdy - 2 * _radius, 
                              chunkdz - 2 * _radius);

    AABB pbbox(vmath::vec3(), 2 * _radius, 2 * _radius, 2 * _radius);

    vmath::vec3 p, minp, maxp;
    int mini, minj, mink, maxi, maxj, maxk;
    for (unsigned int i = 0; i < points.size(); i++) {
        p = points[i].position;

        int ci = floor(p.x * invchunkdx);
        int cj = floor(p.y * invchunkdy);
        int ck = floor(p.z * invchunkdz);
        double cx = (double)ci * chunkdx;
        double cy = (double)cj * chunkdy;
        double cz = (double)ck * chunkdz;

        cbbox.position = vmath::vec3(cx + _radius, cy + _radius, cz + _radius);
        if (cbbox.isPointInside(p) && Grid3d::isGridIndexInRange(ci, cj, ck, gmax)) {
            // sphere is contained within one grid cell
            countGrid.add(ci, cj, ck, 1);
            continue;
        }

        // sphere is contained within at least 2 grid cells
        minp = vmath::vec3(p.x - _radius, p.y - _radius, p.z - _radius);
        maxp = vmath::vec3(p.x + _radius, p.y + _radius, p.z + _radius);
        mini = fmax(floor(minp.x * invchunkdx), 0);
        minj = fmax(floor(minp.y * invchunkdy), 0);
        mink = fmax(floor(minp.z * invchunkdz), 0);
        maxi = fmin(floor(maxp.x * invchunkdx), gmax.i - 1);
        maxj = fmin(floor(maxp.y * invchunkdy), gmax.j - 1);
        maxk = fmin(floor(maxp.z * invchunkdz), gmax.k - 1);

        for (int ck = mink; ck <= maxk; ck++) {
            for (int cj = minj; cj <= maxj; cj++) {
                for (int ci = mini; ci <= maxi; ci++) {
                    countGrid.add(ci, cj, ck, 1);
                }
            }
        }
    }
}

void CLScalarField::_insertParticlesIntoWorkGroupGrid(std::vector<PointValue> &points,
                                                      Array3d<WorkGroup> &grid) {

    double chunkdx = _chunkWidth * _dx;
    double chunkdy = _chunkHeight * _dx;
    double chunkdz = _chunkDepth * _dx;
    double invchunkdx = 1.0 / chunkdx;
    double invchunkdy = 1.0 / chunkdy;
    double invchunkdz = 1.0 / chunkdz;

    GridIndex gmax(grid.width, grid.height, grid.depth);

    AABB cbbox(vmath::vec3(), chunkdx - 2 * _radius, 
                              chunkdy - 2 * _radius, 
                              chunkdz - 2 * _radius);

    AABB pbbox(vmath::vec3(), 2 * _radius, 2 * _radius, 2 * _radius);

    PointValue pv;
    vmath::vec3 p, minp, maxp;
    int mini, minj, mink, maxi, maxj, maxk;
    WorkGroup *group;
    for (unsigned int i = 0; i < points.size(); i++) {
        pv = points[i];
        p = pv.position;

        int ci = floor(p.x * invchunkdx);
        int cj = floor(p.y * invchunkdy);
        int ck = floor(p.z * invchunkdz);
        double cx = (double)ci * chunkdx;
        double cy = (double)cj * chunkdy;
        double cz = (double)ck * chunkdz;

        cbbox.position = vmath::vec3(cx + _radius, cy + _radius, cz + _radius);
        if (cbbox.isPointInside(p) && Grid3d::isGridIndexInRange(ci, cj, ck, gmax)) {
            // sphere is contained within one grid cell
            group = grid.getPointer(ci, cj, ck);
            group->particles.push_back(pv);
            continue;
        }

        // sphere is contained within at least 2 grid cells
        minp = vmath::vec3(p.x - _radius, p.y - _radius, p.z - _radius);
        maxp = vmath::vec3(p.x + _radius, p.y + _radius, p.z + _radius);
        mini = fmax(floor(minp.x * invchunkdx), 0);
        minj = fmax(floor(minp.y * invchunkdy), 0);
        mink = fmax(floor(minp.z * invchunkdz), 0);
        maxi = fmin(floor(maxp.x * invchunkdx), gmax.i - 1);
        maxj = fmin(floor(maxp.y * invchunkdy), gmax.j - 1);
        maxk = fmin(floor(maxp.z * invchunkdz), gmax.k - 1);

        for (int ck = mink; ck <= maxk; ck++) {
            for (int cj = minj; cj <= maxj; cj++) {
                for (int ci = mini; ci <= maxi; ci++) {
                    group = grid.getPointer(ci, cj, ck);
                    group->particles.push_back(pv);
                }
            }
        }
    }
}


bool CLScalarField::_compareWorkChunkByNumParticles(const WorkChunk &c1, const WorkChunk &c2) {
    return c1.particlesEnd - c1.particlesBegin < c2.particlesEnd - c2.particlesBegin;
}

void CLScalarField::_initializeWorkChunks(Array3d<WorkGroup> &grid,
                                          std::vector<WorkChunk> &chunks) {
    WorkGroup *group;
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                group = grid.getPointer(i, j, k);
                _getWorkChunksFromWorkGroup(group, chunks);
            }
        }
    }
    chunks.shrink_to_fit();

    std::sort(chunks.begin(), chunks.end(), _compareWorkChunkByNumParticles);
}

void CLScalarField::_getWorkChunksFromWorkGroup(WorkGroup *group, 
                                                std::vector<WorkChunk> &chunks) {
    if (group->particles.size() == 0) {
        return;
    }

    GridIndex groupidx = group->chunkOffset; 
    int size = (int)group->particles.size();
    int chunksize = _maxParticlesPerChunk;

    for (int i = 0; i < size; i += chunksize) {
        WorkChunk c;
        c.workGroupIndex = groupidx;

        int begidx = i;
        int endidx = begidx + chunksize;
        if (endidx > size) {
            endidx = size;
        }

        c.particlesBegin = group->particles.begin() + begidx;
        c.particlesEnd = group->particles.begin() + endidx;

        chunks.push_back(c);
    }
}

void CLScalarField::_getNextWorkChunksToProcess(std::vector<WorkChunk> &queue,
                                                Array3d<WorkGroup> &grid,
                                                std::vector<WorkChunk> &chunks,
                                                int n) {
    WorkChunk c;
    WorkGroup *g;
    while ((int)chunks.size() < n && !queue.empty()) {
        c = queue.back();
        queue.pop_back();

        if (_isMaxScalarFieldValueThresholdSet) {
            g = grid.getPointer(c.workGroupIndex);
            float minval = g->minScalarFieldValue;

            if (minval < _maxScalarFieldValueThreshold) {
                chunks.push_back(c);
            }
        } else {
            chunks.push_back(c);
        }
    }
}

int CLScalarField::_getChunkPointDataSize() {
    return 3*_maxParticlesPerChunk*sizeof(float);
}

int CLScalarField::_getChunkPointValueDataSize() {
    return 4*_maxParticlesPerChunk*sizeof(float);
}

int CLScalarField::_getChunkScalarFieldDataSize() {
    return _chunkWidth * _chunkHeight * _chunkDepth * sizeof(float);
}

int CLScalarField::_getChunkScalarWeightFieldDataSize() {
    return 2 * _getChunkScalarFieldDataSize();
}

int CLScalarField::_getChunkOffsetDataSize() {
    return 3*sizeof(int);
}

int CLScalarField::_getMaxChunksPerPointComputation() {
    int pointDataSize = _getChunkPointDataSize();
    int fieldDataSize = _getChunkScalarFieldDataSize();
    int offsetDataSize = _getChunkOffsetDataSize();

    return _getMaxChunkLimit(pointDataSize, fieldDataSize, offsetDataSize);
}

int CLScalarField::_getMaxChunksPerPointValueComputation() {
    int pointDataSize = _getChunkPointValueDataSize();
    int fieldDataSize = _getChunkScalarFieldDataSize();
    int offsetDataSize = _getChunkOffsetDataSize();

    return _getMaxChunkLimit(pointDataSize, fieldDataSize, offsetDataSize);
}

int CLScalarField::_getMaxChunksPerWeightPointValueComputation() {
    int pointDataSize = _getChunkPointValueDataSize();
    int fieldDataSize = _getChunkScalarWeightFieldDataSize();
    int offsetDataSize = _getChunkOffsetDataSize();

    return _getMaxChunkLimit(pointDataSize, fieldDataSize, offsetDataSize);
}

int CLScalarField::_getMaxChunksPerLevelSetPointComputation() {
    int pointDataSize = _getChunkPointDataSize();
    int fieldDataSize = _getChunkScalarFieldDataSize();
    int offsetDataSize = _getChunkOffsetDataSize();

    return _getMaxChunkLimit(pointDataSize, fieldDataSize, offsetDataSize);
}

int CLScalarField::_getMaxChunkLimit(int pointDataSize, int fieldDataSize, int offsetDataSize) {
    clcpp::DeviceInfo info = _CLDevice.getDeviceInfo();
    cl_ulong maxGlobalMem = info.cl_device_global_mem_size;
    cl_ulong maxAlloc = info.cl_device_max_mem_alloc_size;

    int numPositionAllocItems = floor((double)maxAlloc / (double)pointDataSize);
    int numFieldAllocItems = floor((double)maxAlloc / (double)fieldDataSize);
    int numOffsetAllocItems = floor((double)maxAlloc / (double)offsetDataSize);

    int allocLimitCount = fmin(fmin(numPositionAllocItems, 
                                    numFieldAllocItems),
                                    numOffsetAllocItems);

    int totalDataSize = pointDataSize + fieldDataSize + offsetDataSize;
    int globalMemLimitCount = floor((double)maxGlobalMem / (double)totalDataSize);

    int hardwareLimit = fmin(allocLimitCount, globalMemLimitCount);
    int softwareLimit = _maxChunksPerComputation;

    return fmin(hardwareLimit, softwareLimit);
}

void CLScalarField::_computePointScalarField(std::vector<WorkChunk> &chunks,
                                             Array3d<WorkGroup> &workGroupGrid) {
    if (chunks.empty()) {
        return;
    }
    
    int numParticles = _getMaxNumParticlesInChunk(chunks);

    DataBuffer buffer;
    _initializePointComputationDataBuffer(chunks, workGroupGrid, numParticles, buffer);
    _setPointComputationCLKernelArgs(buffer, numParticles);

    int numWorkItems = (int)chunks.size() * _workGroupSize;
    _launchKernel(_CLKernelPoints, numWorkItems, _workGroupSize);

    int dataSize = (int)chunks.size() * _getChunkScalarFieldDataSize();
    _readCLBuffer(buffer.scalarFieldDataCL, buffer.scalarFieldDataH, dataSize);
    _setPointComputationOutputFieldData(buffer.scalarFieldDataH, chunks, workGroupGrid);
}

void CLScalarField::_computePointValueScalarField(std::vector<WorkChunk> &chunks,
                                                  Array3d<WorkGroup> &workGroupGrid) {
    if (chunks.empty()) {
        return;
    }
    
    int numParticles = _getMaxNumParticlesInChunk(chunks);

    DataBuffer buffer;
    _initializePointValueComputationDataBuffer(chunks, workGroupGrid, numParticles, buffer);
    _setPointValueComputationCLKernelArgs(buffer, numParticles);

    int numWorkItems = (int)chunks.size() * _workGroupSize;
    _launchKernel(_CLKernelPointValues, numWorkItems, _workGroupSize);

    int dataSize = (int)chunks.size() * _getChunkScalarFieldDataSize();
    _readCLBuffer(buffer.scalarFieldDataCL, buffer.scalarFieldDataH, dataSize);
    _setPointValueComputationOutputFieldData(buffer.scalarFieldDataH, chunks, workGroupGrid);
}

void CLScalarField::_computePointValueScalarWeightField(std::vector<WorkChunk> &chunks,
                                                        Array3d<WorkGroup> &workGroupGrid) {
    if (chunks.empty()) {
        return;
    }

    int numParticles = _getMaxNumParticlesInChunk(chunks);

    DataBuffer buffer;
    _initializeWeightPointValueComputationDataBuffer(chunks, workGroupGrid, numParticles, buffer);
    _setWeightPointValueComputationCLKernelArgs(buffer, numParticles);

    int numWorkItems = (int)chunks.size() * _workGroupSize;
    _launchKernel(_CLKernelWeightPointValues, numWorkItems, _workGroupSize);

    int dataSize = (int)chunks.size() * _getChunkScalarWeightFieldDataSize();
    _readCLBuffer(buffer.scalarFieldDataCL, buffer.scalarFieldDataH, dataSize);
    _setWeightPointValueComputationOutputFieldData(buffer.scalarFieldDataH, 
                                                   chunks, 
                                                   workGroupGrid);
}

void CLScalarField::_computeLevelSetPointScalarField(std::vector<WorkChunk> &chunks,
                                                     Array3d<WorkGroup> &workGroupGrid) {
    if (chunks.empty()) {
        return;
    }

    int numParticles = _getMaxNumParticlesInChunk(chunks);

    DataBuffer buffer;
    _initializeLevelSetPointComputationDataBuffer(chunks, workGroupGrid, numParticles, buffer);
    _setLevelSetPointComputationCLKernelArgs(buffer, numParticles);

    int numWorkItems = (int)chunks.size() * _workGroupSize;
    _launchKernel(_CLKernelLevelSetPoints, numWorkItems, _workGroupSize);

    int dataSize = (int)chunks.size() * _getChunkScalarFieldDataSize();
    _readCLBuffer(buffer.scalarFieldDataCL, buffer.scalarFieldDataH, dataSize);
    _setLevelSetPointComputationOutputFieldData(buffer.scalarFieldDataH, chunks, workGroupGrid);
}

int CLScalarField::_getMaxNumParticlesInChunk(std::vector<WorkChunk> &chunks) {
    int maxParticles = 0;
    for (unsigned int i = 0; i < chunks.size(); i++) {
        int n = chunks[i].particlesEnd - chunks[i].particlesBegin;
        if (n > maxParticles) {
            maxParticles = n;
        }
    }

    return maxParticles;
}

void CLScalarField::_initializePointComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                          Array3d<WorkGroup> &workGroupGrid,
                                                          int numParticles,
                                                          DataBuffer &buffer) {
    _getHostPointDataBuffer(chunks, workGroupGrid, numParticles, buffer.pointDataH);
    _getHostScalarFieldDataBuffer(chunks, buffer.scalarFieldDataH);
    _getHostChunkOffsetDataBuffer(chunks, buffer.offsetDataH);
    _initializeCLDataBuffers(buffer);
}

void CLScalarField::_initializePointValueComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                               Array3d<WorkGroup> &workGroupGrid,
                                                               int numParticles,
                                                               DataBuffer &buffer) {
    _getHostPointValueDataBuffer(chunks, workGroupGrid, numParticles, buffer.pointDataH);
    _getHostScalarFieldDataBuffer(chunks, buffer.scalarFieldDataH);
    _getHostChunkOffsetDataBuffer(chunks, buffer.offsetDataH);
    _initializeCLDataBuffers(buffer);
}

void CLScalarField::_initializeWeightPointValueComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                                     Array3d<WorkGroup> &workGroupGrid,
                                                                     int numParticles,
                                                                     DataBuffer &buffer) {
    _getHostPointValueDataBuffer(chunks, workGroupGrid, numParticles, buffer.pointDataH);
    _getHostScalarWeightFieldDataBuffer(chunks, buffer.scalarFieldDataH);
    _getHostChunkOffsetDataBuffer(chunks, buffer.offsetDataH);
    _initializeCLDataBuffers(buffer);
}

void CLScalarField::_initializeLevelSetPointComputationDataBuffer(std::vector<WorkChunk> &chunks,
                                                                  Array3d<WorkGroup> &workGroupGrid,
                                                                  int numParticles,
                                                                  DataBuffer &buffer) {
    _getHostPointDataBuffer(chunks, workGroupGrid, numParticles, buffer.pointDataH);
    _getHostScalarFieldDataBuffer(chunks, buffer.scalarFieldDataH);
    _getHostChunkOffsetDataBuffer(chunks, buffer.offsetDataH);
    _initializeCLDataBuffers(buffer);
}

void CLScalarField::_initializeCLDataBuffers(DataBuffer &buffer) {
    size_t pointDataBytes = buffer.pointDataH.size() * sizeof(float);
    size_t scalarFieldDataBytes = buffer.scalarFieldDataH.size() * sizeof(float);
    size_t offsetDataBytes = buffer.offsetDataH.size() * sizeof(GridIndex);

    cl_int err = buffer.positionDataCL.createBuffer(
                    _CLContext, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR,
                    pointDataBytes, buffer.pointDataH.data()
                    );
    _checkError(err, "Creating position data buffer");

    err = buffer.scalarFieldDataCL.createBuffer(
                    _CLContext, CL_MEM_WRITE_ONLY | CL_MEM_USE_HOST_PTR,
                    scalarFieldDataBytes, buffer.scalarFieldDataH.data()
                    );
    _checkError(err, "Creating scalar field data buffer");

    err = buffer.offsetDataCL.createBuffer(
                    _CLContext, CL_MEM_READ_ONLY | CL_MEM_USE_HOST_PTR,
                    offsetDataBytes, buffer.offsetDataH.data()
                    );
    _checkError(err, "Creating chunk offset data buffer");
}

void CLScalarField::_getHostPointDataBuffer(std::vector<WorkChunk> &chunks,
                                            Array3d<WorkGroup> &grid,
                                            int numParticles,
                                            std::vector<float> &buffer) {
    int numElements = (int)chunks.size() * 3 * numParticles;
    buffer.reserve(numElements);

    // Dummy position that is far away enough from the scalar field that it
    // will not affect any scalar field values
    vmath::vec3 outOfRangePos(grid.width * _chunkWidth * _dx + 2 * _radius,
                              grid.height * _chunkHeight * _dx + 2 * _radius,
                              grid.depth * _chunkDepth * _dx + 2 * _radius);
    WorkChunk c;
    vmath::vec3 p;
    std::vector<PointValue>::iterator beg;
    std::vector<PointValue>::iterator end;
    for (unsigned int i = 0; i < chunks.size(); i++) {
        c = chunks[i];

        int numPoints = c.particlesEnd - c.particlesBegin;
        int numPad = numParticles - numPoints;

        beg = c.particlesBegin;
        end = c.particlesEnd;
        for (std::vector<PointValue>::iterator it = beg; it != end; ++it) {
            p = (*it).position;
            buffer.push_back(p.x);
            buffer.push_back(p.y);
            buffer.push_back(p.z);
        }

        for (int i = 0; i < numPad; i++) {
            buffer.push_back(outOfRangePos.x);
            buffer.push_back(outOfRangePos.y);
            buffer.push_back(outOfRangePos.z);
        }
    }
}

void CLScalarField::_getHostPointValueDataBuffer(std::vector<WorkChunk> &chunks,
                                                 Array3d<WorkGroup> &grid,
                                                 int numParticles,
                                                 std::vector<float> &buffer) {
    int numElements = (int)chunks.size() * 4 * numParticles;
    buffer.reserve(numElements);

    // Dummy position that is far away enough from the scalar field that it
    // will not affect any scalar field values
    vmath::vec3 outOfRangePos(grid.width * _chunkWidth * _dx + 2 * _radius,
                              grid.height * _chunkHeight * _dx + 2 * _radius,
                              grid.depth * _chunkDepth * _dx + 2 * _radius);
    float outOfRangeValue = 0.0f;

    WorkChunk c;
    vmath::vec3 p;
    float v;
    std::vector<PointValue>::iterator beg;
    std::vector<PointValue>::iterator end;
    for (unsigned int i = 0; i < chunks.size(); i++) {
        c = chunks[i];

        int numPoints = c.particlesEnd - c.particlesBegin;
        int numPad = numParticles - numPoints;

        beg = c.particlesBegin;
        end = c.particlesEnd;
        for (std::vector<PointValue>::iterator it = beg; it != end; ++it) {
            p = (*it).position;
            v = (*it).value;
            buffer.push_back(p.x);
            buffer.push_back(p.y);
            buffer.push_back(p.z);
            buffer.push_back(v);
        }

        for (int i = 0; i < numPad; i++) {
            buffer.push_back(outOfRangePos.x);
            buffer.push_back(outOfRangePos.y);
            buffer.push_back(outOfRangePos.z);
            buffer.push_back(outOfRangeValue);
        }
    }
}

void CLScalarField::_getHostScalarFieldDataBuffer(std::vector<WorkChunk> &chunks,
                                                  std::vector<float> &buffer) {
    int numElements = (int)chunks.size() * _chunkWidth * _chunkHeight * _chunkWidth;
    buffer.reserve(numElements);
    for (int i = 0; i < numElements; i++) {
        buffer.push_back(0.0);
    }
}

void CLScalarField::_getHostScalarWeightFieldDataBuffer(std::vector<WorkChunk> &chunks,
                                                        std::vector<float> &buffer) {
    int numElements = 2 * (int)chunks.size() * _chunkWidth * _chunkHeight * _chunkWidth;
    buffer.reserve(numElements);
    for (int i = 0; i < numElements; i++) {
        buffer.push_back(0.0);
    }
}

void CLScalarField::_getHostChunkOffsetDataBuffer(std::vector<WorkChunk> &chunks,
                                                  std::vector<GridIndex> &buffer) {
    buffer.reserve(chunks.size());
    for (unsigned int i = 0; i < chunks.size(); i++) {
        buffer.push_back(chunks[i].workGroupIndex);
    }
}

void CLScalarField::_setPointComputationCLKernelArgs(DataBuffer &buffer, 
                                                     int numParticles) {
    int localDataBytes = numParticles * 3 * sizeof(float);
    _setKernelArgs(_CLKernelPoints, 
                   buffer, localDataBytes, numParticles, _radius, _dx);
}

void CLScalarField::_setPointValueComputationCLKernelArgs(DataBuffer &buffer, 
                                                          int numParticles) {
    int localDataBytes = numParticles * 4 * sizeof(float);
    _setKernelArgs(_CLKernelPointValues, 
                   buffer, localDataBytes, numParticles, _radius, _dx);
}

void CLScalarField::_setWeightPointValueComputationCLKernelArgs(DataBuffer &buffer, 
                                                                int numParticles) {
    int localDataBytes = numParticles * 4 * sizeof(float);
    _setKernelArgs(_CLKernelWeightPointValues, 
                   buffer, localDataBytes, numParticles, _radius, _dx);
}

void CLScalarField::_setLevelSetPointComputationCLKernelArgs(DataBuffer &buffer, 
                                                             int numParticles) {
    int localDataBytes = numParticles * 3 * sizeof(float);
    _setKernelArgs(_CLKernelLevelSetPoints, 
                   buffer, localDataBytes, numParticles, _radius, _dx);
}

void CLScalarField::_setKernelArgs(clcpp::Kernel &kernel, 
                                   DataBuffer &buffer, 
                                   int localDataBytes,
                                   int numParticles, 
                                   float radius, 
                                   float dx) {

    cl_int err = kernel.setArg(0, buffer.positionDataCL);
    _checkError(err, "Kernel::setArg() - position data");

    err = kernel.setArg(1, buffer.scalarFieldDataCL);
    _checkError(err, "Kernel::setArg() - scalar field data");

    err = kernel.setArg(2, buffer.offsetDataCL);
    _checkError(err, "Kernel::setArg() - chunk offset data");

    clcpp::DeviceInfo deviceInfo = _CLDevice.getDeviceInfo();
    FLUIDSIM_ASSERT((unsigned int)localDataBytes <= deviceInfo.cl_device_local_mem_size);
    err = kernel.setArg(3, localDataBytes, NULL);
    _checkError(err, "Kernel::setArg() - local position data");

    err = kernel.setArg(4, sizeof(int), &numParticles);
    _checkError(err, "Kernel::setArg() - num particles");

    int numGroups = (int)buffer.offsetDataH.size();
    err = kernel.setArg(5, sizeof(int), &numGroups);
    _checkError(err, "Kernel::setArg() - num groups");

    err = kernel.setArg(6, sizeof(float), &radius);
    _checkError(err, "Kernel::setArg() - radius");

    err = kernel.setArg(7, sizeof(float), &dx);
    _checkError(err, "Kernel::setArg() - dx");
}

void CLScalarField::_launchKernel(clcpp::Kernel &kernel, int numWorkItems, int workGroupSize) {
    int numChunks = numWorkItems / workGroupSize;
    int loadSize = _kernelWorkLoadSize;
    int numComputations = ceil((double)numChunks / (double)loadSize);

    clcpp::Event event;
    cl_int err = event.createEvent(_CLContext);
    _checkError(err, "Event::createEvent()");

    for (int i = 0; i < numComputations; i++) {
        int offset = i * loadSize * workGroupSize;
        int items = (int)fmin(numWorkItems - offset, loadSize * workGroupSize);
        
        err = _CLQueue.enqueueNDRangeKernel(kernel, 
                                            clcpp::NDRange(offset), 
                                            clcpp::NDRange(items), 
                                            clcpp::NDRange(workGroupSize),
                                            event);    
        _checkError(err, "CommandQueue::enqueueNDRangeKernel()");
    }

    err = event.wait();
    _checkError(err, "Event::wait()");
}

void CLScalarField::_readCLBuffer(clcpp::Buffer &sourceCL, std::vector<float> &destH, int dataSize) {
    FLUIDSIM_ASSERT((int)(destH.size() * sizeof(float)) >= dataSize);
    cl_int err = _CLQueue.enqueueReadBuffer(sourceCL, dataSize, destH.data());
    _checkError(err, "CommandQueue::enqueueReadBuffer()");
}

void CLScalarField::_setPointComputationOutputFieldData(std::vector<float> &buffer, 
                                                        std::vector<WorkChunk> &chunks,
                                                        Array3d<WorkGroup> &workGroupGrid) {
    int elementsPerChunk = _chunkWidth * _chunkHeight * _chunkDepth;
    FLUIDSIM_ASSERT(buffer.size() == chunks.size() * elementsPerChunk);

    GridIndex cg;
    ArrayView3d<float> fieldview;
    int bufferidx = 0;
    for (unsigned int cidx = 0; cidx < chunks.size(); cidx++) {
        cg = chunks[cidx].workGroupIndex;
        fieldview = workGroupGrid(cg).fieldview;

        for (int k = 0; k < fieldview.depth; k++) {
            for (int j = 0; j < fieldview.height; j++) {
                for (int i = 0; i < fieldview.width; i++) {
                    fieldview.add(i, j, k, buffer[bufferidx]);
                    bufferidx++;
                }
            }
        }
    }
}

void CLScalarField::_setPointValueComputationOutputFieldData(std::vector<float> &buffer, 
                                                             std::vector<WorkChunk> &chunks,
                                                             Array3d<WorkGroup> &workGroupGrid) {
    _setPointComputationOutputFieldData(buffer, chunks, workGroupGrid);
}

void CLScalarField::_setWeightPointValueComputationOutputFieldData(std::vector<float> &buffer, 
                                                                   std::vector<WorkChunk> &chunks,
                                                                   Array3d<WorkGroup> &workGroupGrid) {
    int elementsPerChunk = _chunkWidth * _chunkHeight * _chunkDepth;
    FLUIDSIM_ASSERT(buffer.size() == 2 * chunks.size() * elementsPerChunk);

    GridIndex cg;
    WorkGroup *group;
    ArrayView3d<float> scalarfieldview;
    ArrayView3d<float> weightfieldview;
    int bufferidx = 0;
    int weightfieldoffset = (int)chunks.size() * elementsPerChunk;
    for (unsigned int cidx = 0; cidx < chunks.size(); cidx++) {
        cg = chunks[cidx].workGroupIndex;
        group = workGroupGrid.getPointer(cg);
        scalarfieldview = group->fieldview;
        weightfieldview = group->weightfieldview;

        for (int k = 0; k < scalarfieldview.depth; k++) {
            for (int j = 0; j < scalarfieldview.height; j++) {
                for (int i = 0; i < scalarfieldview.width; i++) {
                    scalarfieldview.add(i, j, k, buffer[bufferidx]);
                    weightfieldview.add(i, j, k, buffer[bufferidx + weightfieldoffset]);
                    bufferidx++;
                }
            }
        }
    }
}

void CLScalarField::_setLevelSetPointComputationOutputFieldData(std::vector<float> &buffer, 
                                                                std::vector<WorkChunk> &chunks,
                                                                Array3d<WorkGroup> &workGroupGrid) {
    int elementsPerChunk = _chunkWidth * _chunkHeight * _chunkDepth;
    FLUIDSIM_ASSERT(buffer.size() == chunks.size() * elementsPerChunk);

    GridIndex cg;
    ArrayView3d<float> fieldview;
    int bufferidx = 0;
    for (unsigned int cidx = 0; cidx < chunks.size(); cidx++) {
        cg = chunks[cidx].workGroupIndex;
        fieldview = workGroupGrid(cg).fieldview;

        for (int k = 0; k < fieldview.depth; k++) {
            for (int j = 0; j < fieldview.height; j++) {
                for (int i = 0; i < fieldview.width; i++) {
                    float bval = buffer[bufferidx];
                    if (bval < fieldview(i, j, k)) {
                        fieldview.set(i, j, k, bval);
                    }
                    bufferidx++;
                }
            }
        }
    }
}

void CLScalarField::_updateWorkGroupMinimumValues(Array3d<WorkGroup> &grid) {
    WorkGroup *g;
    for (int k = 0; k < grid.depth; k++) {
        for (int j = 0; j < grid.height; j++) {
            for (int i = 0; i < grid.width; i++) {
                g = grid.getPointer(i, j, k);
                g->minScalarFieldValue = _getWorkGroupMinimumValue(g);
            }
        }
    }
}

float CLScalarField::_getWorkGroupMinimumValue(WorkGroup *g) {
    float minval = std::numeric_limits<float>::infinity();
    ArrayView3d<float> view = g->fieldview;
    for (int k = 0; k < view.depth; k++) {
        for (int j = 0; j < view.height; j++) {
            for (int i = 0; i < view.width; i++) {
                if (view.isIndexInParent(i, j, k) && view(i, j, k) < minval) {
                    minval = view(i, j, k);
                }
            }
        }
    }

    return minval;
}

#endif
// ENDIF WITH_OPENCL
