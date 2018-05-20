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

#ifndef FLUIDENGINE_BOUNDED_BUFFER_H
#define FLUIDENGINE_BOUNDED_BUFFER_H

#include "threadutils.h"
#include "fluidsimassert.h"

template <class T>
class BoundedBuffer 
{ 
public:

    BoundedBuffer() {}

    BoundedBuffer(size_t size) {
        _bufferSize = size;
        _buffer.reserve(size);
    }

    ~BoundedBuffer() {
    }

    void push(T item) {
        std::unique_lock<std::mutex> lock(_mutex);
        while (_buffer.size() == _bufferSize) {
            _notFull.wait(lock);
        }
        
        FLUIDSIM_ASSERT(_buffer.size() < _bufferSize);
        _buffer.push_back(item);
        _notEmpty.notify_all();
    }

    int push(std::vector<int> &items) {
        std::unique_lock<std::mutex> lock(_mutex);
        while (_buffer.size() == _bufferSize) {
            _notFull.wait(lock);
        }
        
        int remaining = _bufferSize - _buffer.size();
        int numPushed = items.size() <= remaining ? items.size() : remaining;
        for (size_t i = 0; i < numPushed; i++) {
            _buffer.push_back(items[i]);
        }

        _notEmpty.notify_all();

        return numPushed;
    }

    int push(std::vector<T> &items, size_t startindex, size_t endindex) {
        FLUIDSIM_ASSERT(startindex >= 0 && startindex < items.size());
        FLUIDSIM_ASSERT(endindex >= 0 && endindex <= items.size());
        FLUIDSIM_ASSERT(startindex < endindex);

        int numItems = endindex - startindex;

        std::unique_lock<std::mutex> lock(_mutex);
        while (_buffer.size() == _bufferSize) {
            _notFull.wait(lock);
        }
        
        int remaining = _bufferSize - _buffer.size();
        int numPushed = numItems <= remaining ? numItems : remaining;
        for (int i = 0; i < numPushed; i++) {
            _buffer.push_back(items[startindex + i]);
        }

        _notEmpty.notify_all();

        return numPushed;
    }

    void pushAll(std::vector<T> &items) {
        int itemsleft = items.size();
        while (itemsleft > 0) {
            int numPushed = push(items, items.size() - itemsleft, items.size());
            itemsleft -= numPushed;
        }
    }

    T pop() {
        std::unique_lock<std::mutex> lock(_mutex);
        while (_buffer.size() == 0) {
            _notEmpty.wait(lock);
            if (_buffer.size() == 0) {
                return T();
            }
        }
        
        FLUIDSIM_ASSERT(_buffer.size() != 0);
        T item = _buffer.back();
        _buffer.pop_back();
        _notFull.notify_all();

        return item;
    }

    int pop(int numItems, std::vector<T> &items) {
        std::unique_lock<std::mutex> lock(_mutex);
        while (_buffer.size() == 0) {
            _notEmpty.wait(lock);
            if (_buffer.size() == 0) {
                return 0;
            }
        }
        
        int numPopped = numItems <= (int)_buffer.size() ? numItems : (int)_buffer.size();
        items.reserve(items.size() + numPopped);
        for (int i = 0; i < numPopped; i++) {
            items.push_back(_buffer.back());
            _buffer.pop_back();
        }

        _notFull.notify_all();

        return numPopped;
    }

    void popAll(std::vector<T> &items) {
        pop(_bufferSize, items);
    }

    size_t size() {
        std::unique_lock<std::mutex> lock(_mutex);
        return _buffer.size();
    }

    void notifyFinished() {
        _notEmpty.notify_all();
    }

private:
    size_t _bufferSize = 0;
    std::vector<T> _buffer;

    std::mutex _mutex;
    std::condition_variable _notFull;
    std::condition_variable _notEmpty;
};

#endif
