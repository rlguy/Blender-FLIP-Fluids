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

#ifndef FLUIDENGINE_THREADUTILS_H
#define FLUIDENGINE_THREADUTILS_H

#if __MINGW32__ && !_WIN64
    #include <mutex>
    #include "mingw32_threads/mingw.thread.h"
    #include "mingw32_threads/mingw.condition_variable.h"
    #include "mingw32_threads/mingw.mutex.h"
#else
    #include <thread>
    #include <mutex>
    #include <condition_variable>
#endif

#include <vector>

namespace ThreadUtils {

    extern int _maxThreadCount;
    extern bool _isMaxThreadCountInitialized;

    extern void _initializeMaxThreadCount();
    extern int getMaxThreadCount();
    extern void setMaxThreadCount(int n);
    extern std::vector<int> splitRangeIntoIntervals(int rangeBegin, 
                                                    int rangeEnd, 
                                                    int numIntervals);
}

#endif