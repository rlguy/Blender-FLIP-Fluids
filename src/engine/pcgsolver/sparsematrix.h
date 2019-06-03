/*
CC0 1.0 Public Domain License

The person who associated a work with this deed has dedicated the work to the 
public domain by waiving all of his or her rights to the work worldwide under 
copyright law, including all related and neighboring rights, to the extent 
allowed by law.

You can copy, modify, distribute and perform the work, even for commercial 
purposes, all without asking permission. See Other Information below.
*/

#ifndef FLUIDENGINE_SPARSE_MATRIX_H
#define FLUIDENGINE_SPARSE_MATRIX_H

#include <iostream>
#include <vector>
#include <cmath>

#include "../threadutils.h"
#include "../fluidsimassert.h"

//============================================================================
// Dynamic compressed sparse row matrix.

template<class T>
struct SparseMatrix {

    unsigned int n;                                    // dimension
    std::vector<std::vector<unsigned int> > index;     // for each row, a list of all column indices (sorted)
    std::vector<std::vector<T> > value;                // values corresponding to index

    SparseMatrix(unsigned int size = 0, unsigned int expectedNonZeros = 7) : 
                    n(size), index(size), value(size) {

        for (unsigned int i = 0; i < n; i++) {
            index[i].reserve(expectedNonZeros);
            value[i].reserve(expectedNonZeros);
        }
    }

    void clear(void) {
        n = 0;
        index.clear();
        value.clear();
    }

    void zero(void) {
        for(unsigned int i = 0; i < n; i++){
            index[i].resize(0);
            value[i].resize(0);
        }
    }

    void resize(int size) {
        n = size;
        index.resize(size);
        value.resize(size);
    }

    T operator()(int i, int j) const {
        FLUIDSIM_ASSERT(i >= 0 && i < n && j >= 0 && j < n);
        for (size_t k = 0; k < index[i].size(); k++) {
            if (index[i][k] == j) {
                return value[i][k];
            } else if (index[i][k] > j) {
                return 0;
            }
        }
        return 0;
    }

    void set(int i, int j, T newValue) {
        if (i == -1 || j == -1) {
            return;
        }
        FLUIDSIM_ASSERT(i >= 0 && i < (int)n && j >= 0 && j < (int)n);

        for(size_t k = 0; k < index[i].size(); k++){
            if (index[i][k] == (unsigned int)j) {
                value[i][k] = newValue;
                return;
            } else if (index[i][k] > (unsigned int)j) {
                index[i].insert(index[i].begin() + k, j);
                value[i].insert(value[i].begin() + k, newValue);
                return;
            }
        }
        index[i].push_back(j);
        value[i].push_back(newValue);
    }

    void add(int i, int j, T inc)
    {
        if (i == -1 || j == -1) {
            return;
        }
        FLUIDSIM_ASSERT(i >= 0 && i < (int)n && j >= 0 && j < (int)n);

        for(size_t k = 0; k < index[i].size(); k++){
            if (index[i][k] == (unsigned int)j) {
                value[i][k] += inc;
                return;
            } else if (index[i][k] > (unsigned int)j){
                index[i].insert(index[i].begin() + k, j);
                value[i].insert(value[i].begin() + k, inc);
                return;
            }
        }
        index[i].push_back(j);
        value[i].push_back(inc);
    }
};

typedef SparseMatrix<float> SparseMatrixf;
typedef SparseMatrix<double> SparseMatrixd;

//============================================================================
// Fixed version of SparseMatrix. This is not a good structure for dynamically
// modifying the matrix, but can be significantly faster for matrix-vector
// multiplies due to better data locality.

template<class T>
struct FixedSparseMatrix {

    unsigned int n;                         // dimension
    std::vector<T> value;                   // nonzero values row by row
    std::vector<unsigned int> colindex;     // corresponding column indices
    std::vector<unsigned int> rowstart;     // where each row starts in value and colindex (and last entry is one past the end, the number of nonzeros)

    explicit FixedSparseMatrix(unsigned int size = 0)
        : n(size), value(0), colindex(0), rowstart(size + 1)
    {}

    void clear(void)
    {
        n = 0;
        value.clear();
        colindex.clear();
        rowstart.clear();
    }

    void resize(int size)
    {
        n = size;
        rowstart.resize(n + 1);
    }

    void fromMatrix(const SparseMatrix<T> &matrix)
    {
        resize(matrix.n);
        rowstart[0] = 0;
        for (unsigned int i = 0; i < n; i++) {
            rowstart[i + 1] = rowstart[i] + (unsigned int)matrix.index[i].size();
        }

        value.resize(rowstart[n]);
        colindex.resize(rowstart[n]);

        size_t j = 0;
        for (size_t i = 0; i < n; i++) {
            for (size_t k = 0; k < matrix.index[i].size(); k++) {
                value[j] = matrix.value[i][k];
                colindex[j] = matrix.index[i][k];
                j++;
            }
        }
    }
};

typedef FixedSparseMatrix<float> FixedSparseMatrixf;
typedef FixedSparseMatrix<double> FixedSparseMatrixd;

// perform result=matrix*x
template<class T>
void _multiplyThread(int startidx, int endidx, 
                     FixedSparseMatrix<T> *matrix, 
                     std::vector<T> *x, std::vector<T> *result) {
    for(int i = startidx; i < endidx; i++){
        (*result)[i] = 0;
        for (size_t j = matrix->rowstart[i]; j < matrix->rowstart[i + 1]; j++){
            (*result)[i] += matrix->value[j] * (*x)[matrix->colindex[j]];
        }
    }
}

template<class T>
void multiply(FixedSparseMatrix<T> &matrix, std::vector<T> &x, std::vector<T> &result) {
    FLUIDSIM_ASSERT(matrix.n == x.size());
    result.resize(matrix.n);

    int elementsPerThread = 500000;
    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, std::ceil((float)matrix.n / (float)elementsPerThread));
    if (numthreads == 1) {
        for(size_t i = 0; i < result.size(); i++){
            result[i] = 0;
            for (size_t j = matrix.rowstart[i]; j < matrix.rowstart[i + 1]; j++){
                result[i] += matrix.value[j] * x[matrix.colindex[j]];
            }
        }

        return;
    }

    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, matrix.n, numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&_multiplyThread<T>,
                                 intervals[i], intervals[i + 1], &matrix, &x, &result);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

#endif
