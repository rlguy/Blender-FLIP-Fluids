/*
CC0 1.0 Public Domain License

The person who associated a work with this deed has dedicated the work to the 
public domain by waiving all of his or her rights to the work worldwide under 
copyright law, including all related and neighboring rights, to the extent 
allowed by law.

You can copy, modify, distribute and perform the work, even for commercial 
purposes, all without asking permission. See Other Information below.
*/

#ifndef FLUIDENGINE_BLAS_WRAPPER_H
#define FLUIDENGINE_BLAS_WRAPPER_H

// Simple placeholder code for BLAS calls - replace with calls to a real BLAS library

#include <vector>

#include "../threadutils.h"

#define ELEMENTS_PER_THREAD 500000

namespace BLAS{

// dot products ==============================================================

template<class T>
void dotThread(int startidx, int endidx, std::vector<T> *x, std::vector<T> *y, T *result) {
    for (int i = startidx; i < endidx; i++) {
        *result += x->at(i) * y->at(i);
    }
}

template<class T>
inline T dot(std::vector<T> &x, std::vector<T> &y) { 
    //return cblas_ddot((int)x.size(), &x[0], 1, &y[0], 1); 

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, std::ceil((float)x.size() / (float)ELEMENTS_PER_THREAD));
    if (numthreads == 1) {
        T sum = 0;
        for(size_t i = 0; i < x.size(); i++) {
            sum += x[i] * y[i];
        }
        return sum;
    }

    std::vector<std::thread> threads(numthreads);
    std::vector<T> results(numthreads, 0);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, x.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&dotThread<T>,
                                 intervals[i], intervals[i + 1], &x, &y, &(results[i]));
    }

    T sum = 0;
    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
        sum += results[i];
    }

    return sum;
}

// inf-norm (maximum absolute value: index of max returned) ==================

template<class T>
void indexAbsMaxThread(int startidx, int endidx, std::vector<T> *x, T *maxval, int *maxidx) {
    for (int i = startidx; i < endidx; i++) {
        if (std::abs(x->at(i)) > *maxval) {
            *maxval = std::abs(x->at(i));
            *maxidx = i;
        }
    }
}

template<class T>
inline int indexAbsMax(std::vector<T> &x) { 
    //return cblas_idamax((int)x.size(), &x[0], 1); 

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, std::ceil((float)x.size() / (float)ELEMENTS_PER_THREAD));
    if (numthreads == 1) {
        int maxind = 0;
        T maxvalue = 0;
        for(size_t i = 0; i < x.size(); i++) {
            if (fabs(x[i]) > maxvalue) {
                maxvalue = fabs(x[i]);
                maxind = (int)i;
            }
        }
        return maxind;
    }

    std::vector<std::thread> threads(numthreads);
    std::vector<T> maxvals(numthreads, 0);
    std::vector<int> maxinds(numthreads, -1);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, x.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&indexAbsMaxThread<T>,
                                 intervals[i], intervals[i + 1], &x, &(maxvals[i]), &(maxinds[i]));
    }

    int maxindex = 0;
    T maxvalue = 0;
    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
        if (maxvals[i] > maxvalue) {
            maxvalue = maxvals[i];
            maxindex = maxinds[i];
        }
    }

    return maxindex;
}

// inf-norm (maximum absolute value) =========================================
// technically not part of BLAS, but useful

template<class T>
inline T absMax(std::vector<T> &x) { 
    return std::fabs(x[indexAbsMax(x)]); 
}

// saxpy (y=alpha*x+y) =======================================================

template<class T>
void addScaledThread(int startidx, int endidx, float alpha, std::vector<T> *x, std::vector<T> *y) {
    for (int i = startidx; i < endidx; i++) {
        (*y)[i] += alpha * x->at(i);
    }
}

template<class T>
inline void addScaled(float alpha, std::vector<T> &x, std::vector<T> &y) { 
    //cblas_daxpy((int)x.size(), alpha, &x[0], 1, &y[0], 1); 

    int numCPU = ThreadUtils::getMaxThreadCount();
    int numthreads = (int)fmin(numCPU, std::ceil((float)x.size() / (float)ELEMENTS_PER_THREAD));
    if (numthreads == 1) {
        for (size_t i = 0; i < x.size(); i++) {
            y[i] += alpha * x[i];
        }
        return;
    }

    std::vector<std::thread> threads(numthreads);
    std::vector<int> intervals = ThreadUtils::splitRangeIntoIntervals(0, x.size(), numthreads);
    for (int i = 0; i < numthreads; i++) {
        threads[i] = std::thread(&addScaledThread<T>,
                                 intervals[i], intervals[i + 1], alpha, &x, &y);
    }

    for (int i = 0; i < numthreads; i++) {
        threads[i].join();
    }
}

}
#endif
