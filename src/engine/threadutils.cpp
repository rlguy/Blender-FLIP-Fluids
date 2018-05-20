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

#include "threadutils.h"

#include <cmath>

#include "fluidsimassert.h"

int ThreadUtils::_maxThreadCount = 0;
bool ThreadUtils::_isMaxThreadCountInitialized = false;

void ThreadUtils::_initializeMaxThreadCount() {
	if (_isMaxThreadCountInitialized) {
		return;
	}

	_maxThreadCount = std::thread::hardware_concurrency();
	_isMaxThreadCountInitialized = true;
}

int ThreadUtils::getMaxThreadCount(){
	_initializeMaxThreadCount();
	return _maxThreadCount;
}

void ThreadUtils::setMaxThreadCount(int n) {
	FLUIDSIM_ASSERT(n > 0);
	_maxThreadCount = n;
	_isMaxThreadCountInitialized = true;
}

std::vector<int> ThreadUtils::splitRangeIntoIntervals(int rangeBegin, int rangeEnd, 
	                                                  int numIntervals) {
    int intervalSize = floor((double)(rangeEnd - rangeBegin) / (double)numIntervals);
    int intervalRemainder = (rangeEnd - rangeBegin) - intervalSize * numIntervals;
    std::vector<int> intervals;
    intervals.reserve(numIntervals + 1);
    intervals.push_back(rangeBegin);

    int intervalBegin = rangeBegin;
    for (int i = 0; i < numIntervals; i++) {
        int intervalEnd = intervalBegin + intervalSize;
        if (i < intervalRemainder) {
            intervalEnd++;
        }
        intervals.push_back(intervalEnd);
        intervalBegin = intervalEnd;
    }

    return intervals;
}