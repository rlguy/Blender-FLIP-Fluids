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

namespace BLAS{

// dot products ==============================================================

template<class T>
inline T dot(const std::vector<T> &x, const std::vector<T> &y) { 
    //return cblas_ddot((int)x.size(), &x[0], 1, &y[0], 1); 

    T sum = 0;
    for(size_t i = 0; i < x.size(); i++) {
        sum += x[i] * y[i];
    }
    return sum;
}

// inf-norm (maximum absolute value: index of max returned) ==================

template<class T>
inline int indexAbsMax(const std::vector<T> &x) { 
    //return cblas_idamax((int)x.size(), &x[0], 1); 

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

// inf-norm (maximum absolute value) =========================================
// technically not part of BLAS, but useful

template<class T>
inline T absMax(const std::vector<T> &x) { 
    return std::fabs(x[indexAbsMax(x)]); 
}

// saxpy (y=alpha*x+y) =======================================================

template<class T>
inline void addScaled(float alpha, const std::vector<T> &x, std::vector<T> &y) { 
    //cblas_daxpy((int)x.size(), alpha, &x[0], 1, &y[0], 1); 

    for (size_t i = 0; i < x.size(); i++) {
        y[i] += alpha * x[i];
    }
}

}
#endif
