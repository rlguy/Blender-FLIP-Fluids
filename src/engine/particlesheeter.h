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

#ifndef FLUIDENGINE_PARTICLESHEETER_H
#define FLUIDENGINE_PARTICLESHEETER_H

#include "markerparticle.h"
#include "fragmentedvector.h"
#include "meshlevelset.h"
#include "particlemaskgrid.h"
#include "vmath.h"
#include "particlesystem.h"


struct ParticleSheeterParameters {
    ParticleSystem *particles;
    Array3d<float> *fluidSurfaceLevelSet;

    int isize = 0;
    int jsize = 0;
    int ksize = 0;
    double dx = 0.0;
    float sheetFillThreshold = -0.95f;
};

class ParticleSheeter {

public:
    ParticleSheeter();
    ~ParticleSheeter();

    void generateSheetParticles(ParticleSheeterParameters params,
                                std::vector<vmath::vec3> &generatedParticles);
    
private:

    struct SortedParticleData {
        int particlesPerCell = 0;
        int isize = 0;
        int jsize = 0;
        int ksize = 0;
        double dx = 0.0;

        Array3d<bool> validCells;
        int numValidCells = 0;

        std::vector<vmath::vec3> particleData;
        Array3d<std::pair<int, int> > dataOffsets;
    };
    
    void _initializeParameters(ParticleSheeterParameters params);
    void _getMarkerParticleCellCounts(Array3d<unsigned char> &countGrid);
    void _identifySheetParticlesPhase1(Array3d<unsigned char> &countGrid, 
                                       std::vector<vmath::vec3> &sheetParticles);
    void _identifySheetParticlesPhase1Thread(int startidx, int endidx, 
                                             Array3d<unsigned char> *countGrid, 
                                             std::vector<vmath::vec3> *result);
    void _getSheetCells(std::vector<vmath::vec3> &sheetParticles, 
                        Array3d<bool> &sheetCells);
    void _getSheetCellsThread(int startidx, int endidx,
                              std::vector<vmath::vec3> *sheetParticles, 
                              Array3d<bool> *sheetCells);
    void _identifySheetParticlesPhase2(Array3d<bool> &sheetCells,
                                       Array3d<unsigned char> &countGrid, 
                                       std::vector<vmath::vec3> &sheetParticles);
    void _identifySheetParticlesPhase2Thread(int startidx, int endidx, 
                                             Array3d<bool> *sheetCells,
                                             Array3d<unsigned char> *countGrid, 
                                             std::vector<vmath::vec3> *result);
    void _initializeMaskGrid(ParticleMaskGrid &maskgrid);
    void _getSheetSeedCandidates(Array3d<bool> &sheetCells, 
                                 std::vector<vmath::vec3> &sheetSeedCandidates);
    void _getSheetSeedCandidatesThread(int startidx, int endidx, 
                                       std::vector<GridIndex> *sheetCellVector,
                                       std::vector<vmath::vec3> *result);
    void _sortSheetParticlesIntoGrid(std::vector<vmath::vec3> &sheetParticles, 
                                     SortedParticleData &sheetParticleData);
    void _sortSheetSeedCandidateParticlesIntoGrid(std::vector<vmath::vec3> &candidateParticles, 
                                                  SortedParticleData &candidateParticleData);
    
    void _sortParticlesIntoGrid(std::vector<vmath::vec3> &particles, 
                                SortedParticleData &sortData);
    void _initializeSortDataValidCells(std::vector<vmath::vec3> &particles, 
                                       SortedParticleData &sortData);
    void _initializeSortDataValidCellsThread(int startidx, int endidx, 
                                             std::vector<vmath::vec3> *particles, 
                                             SortedParticleData *sortData);

    void _selectSeedParticles(SortedParticleData &sheetCandidateParticleData, 
                              SortedParticleData &sheetParticleData,
                              ParticleMaskGrid &maskgrid,
                              std::vector<vmath::vec3> &generatedParticles);
    void _selectSeedParticlesThread(int startidx, int endidx,
                                    std::vector<GridIndex> *candidateCells,
                                    ParticleMaskGrid *maskgrid,
                                    SortedParticleData *sheetCandidateParticleData,
                                    SortedParticleData *sheetParticleData,
                                    std::vector<vmath::vec3> *result);

    // External parameters
    ParticleSystem *_particles;
    Array3d<float> *_fluidSurfaceLevelSet;

    int _isize = 0;
    int _jsize = 0;
    int _ksize = 0;
    double _dx = 0.0;
    float _sheetFillThreshold = -0.95f;

    // Internal parameters
    float _maxSheetDepth = 2.0f;
    float _depthTestDistance = 3.0f;
    float _depthTestStepDistance = 0.5f;
    int _maxParticlesPerCell = 6;
    int _maxSheetParticlesPerCell = 4;
    int _maxSheetSeedCandidatesPerCell = 8;
    float _maxSheedSeedCandidateDepth = 1.0f;
    float _sheetSearchRadius = 2.0f;
    float _projectionFactor = 0.75;
};

#endif
