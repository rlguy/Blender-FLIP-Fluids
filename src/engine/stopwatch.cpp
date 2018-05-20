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

#include "stopwatch.h"

StopWatch::StopWatch()
{
}

void StopWatch::start() {
    
    #if defined(__linux__) || defined(__APPLE__) || defined(__MACOSX)
        struct timeval tp;
        gettimeofday(&tp, nullptr);
        _tbegin = (double)tp.tv_sec + (double)tp.tv_usec / 1000000.0;
    #elif defined(_WIN32)
        _tbegin = (double)GetTickCount() / 1000.0;
    #else
    #endif
    
    _isStarted = true;
}


void StopWatch::stop() {
    if (!_isStarted) {
        return;
    }

    #if defined(__linux__) || defined(__APPLE__) || defined(__MACOSX)
        struct timeval tp;
        gettimeofday(&tp, nullptr);
        _tend = (double)tp.tv_sec + (double)tp.tv_usec / 1000000.0;
    #elif defined(_WIN32)
        _tend = (double)GetTickCount() / 1000.0;
    #else
    #endif
    
    double time = _tend - _tbegin;
    _timeRunning += time;
}

void StopWatch::reset() {
    _isStarted = false;
    _timeRunning = 0.0;
}

double StopWatch::getTime() {
    return _timeRunning >= 0.0 ? _timeRunning : 0.0;
}

void StopWatch::setTime(double value) {
    _timeRunning = value;
}