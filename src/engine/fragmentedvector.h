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

#ifndef FLUIDENGINE_FRAGMENTEDVECTOR_H
#define FLUIDENGINE_FRAGMENTEDVECTOR_H

#include <vector>

#include "fluidsimassert.h"

template <class T>
class FragmentedVector 
{
public:

	FragmentedVector() {
		_initializeElementsPerChunk();
	}

	FragmentedVector(int numElements) {
		_initializeElementsPerChunk();
		reserve(numElements);
		for (int i = 0; i < numElements; i++) {
			push_back(T());
		}
		_currentNodeIndex = (int)_nodes.size() - 1;
	}

	inline void setFragmentSize(size_t numElements) {
		if (_nodes.size() != 0) {
			return;
		}
		_bytesPerFragment = numElements*sizeof(T);
		_initializeElementsPerChunk();
	}

	inline void setFragmentByteSize(unsigned int numBytes) {
		if (_nodes.size() != 0) {
			return;
		}
		_bytesPerFragment = numBytes;
		_initializeElementsPerChunk();
	}

	inline unsigned int size() {
		return _size;
	}

	inline bool empty() {
		return _size == 0;
	}

	inline void reserve(unsigned int n) {
		int numFragments = n / _elementsPerFragment;
		int numNewFragments = numFragments - (int)_nodes.size();
		for (int i = 0; i < numNewFragments; i++) {
			_addNewVectorNode();
		}
	}

	inline void shrink_to_fit() {
		while (!_nodes.empty() && _nodes.back().size() == 0) {
			_nodes.pop_back();
		}
	}

	inline T front() {
		FLUIDSIM_ASSERT(_size > 0);
		return _nodes[0][0];
	}

	inline T back() {
		FLUIDSIM_ASSERT(_size > 0);
		return _nodes[_currentNodeIndex].back();
	}

	inline void push_back(T item) {
		if (_nodes.size() == 0) {
			_addNewVectorNode();
			_currentNodeIndex = 0;
		}

		if (!_isCurrentNodeFull()) {
			_nodes[_currentNodeIndex].push_back(item);
			_size++;
		} else {
			if (_isLastNode(_currentNodeIndex)) {
				_addNewVectorNode();
				_currentNodeIndex++;
			} else {
				_currentNodeIndex++;
			}

			_nodes[_currentNodeIndex].push_back(item);
			_size++;
		}
	}

	inline void pop_back() {
		if (_size == 0) {
			return;
		}

		_nodes[_currentNodeIndex].pop_back();
		_size--;

		if (_nodes[_currentNodeIndex].empty()) {
			_currentNodeIndex--;
		}
	}

	inline void clear() {
		for (unsigned int i = 0; i < _nodes.size(); i++) {
			_nodes[i].clear();
		}
		_currentNodeIndex = 0;
		_size = 0;
	}

	const T operator [](int i) const {
		FLUIDSIM_ASSERT(i >= 0 && i < (int)_size);
		int nodeIdx = i * _invElementsPerFragment;
		int itemIdx = i % _elementsPerFragment;
		return _nodes[nodeIdx][itemIdx];
	}

	T& operator[](int i) {
		FLUIDSIM_ASSERT(i >= 0 && i < (int)_size);
		int nodeIdx = i * _invElementsPerFragment;
		int itemIdx = i % _elementsPerFragment;
		return _nodes[nodeIdx][itemIdx];
	}

	const T at(int i) const {
		return (*this)[i];
	}

	T& at(int i) {
		return (*this)[i];
	}

	void sort() {
		sort(_defaultCompare);
	}

	//  This quicksort function is adapted from a public-domain C implementation 
	//  by Darel Rex Finley.
	//
	//  http://alienryderflex.com/quicksort/
	void sort(bool (*compare)(const T&, const T&)) {

		#define  MAX_LEVELS  300

		int elements = size();
		T piv;
		int beg[MAX_LEVELS];
		int end[MAX_LEVELS];
		int i = 0;
		int L;
		int R;
		int swap;

		beg[0] = 0; 
		end[0] = elements;

		while (i >= 0) {
			L = beg[i]; 
			R = end[i] - 1;

			if (L<R) {
				piv = (*this)[L];
				while (L < R) {
				    while (!compare((*this)[R], piv) && L < R) {
				    	R--;
				    }

				    if (L < R) { 
				    	(*this)[L++] = (*this)[R];
				    }


				    while (compare((*this)[L], piv) && L < R) {
				    	L++; 
				    }

				    if (L < R) {
				    	(*this)[R--] = (*this)[L]; 
				    }
				}

				(*this)[L] = piv; 
				beg[i + 1] = L + 1; 
				end[i + 1] = end[i]; 
				end[i++] = L;

				if (end[i] - beg[i] > end[i - 1] - beg[i - 1]) {
				    swap = beg[i]; beg[i] = beg[i - 1]; beg[i - 1] = swap;
				    swap = end[i]; end[i] = end[i - 1]; end[i - 1] = swap; 
				}
			} else {
			  	i--; 
			}
		}
	}

private:

	class VectorNode 
	{
		public:

			VectorNode() {
			}

			VectorNode(unsigned int maxsize) : _capacity(maxsize) {
				_vector.reserve(_capacity);
			}

			inline size_t size() {
				return _vector.size();
			}

			inline bool empty() {
				return _vector.size() == 0;
			}

			inline bool isFull() {
				return _vector.size() == _capacity;
			}

			inline T front() {
				FLUIDSIM_ASSERT(_vector.size() > 0);
				return _vector[0];
			}

			inline T back() {
				FLUIDSIM_ASSERT(_vector.size() > 0);
				return _vector.back();
			}

			inline void push_back(T item) {
				FLUIDSIM_ASSERT(_vector.size() < _capacity);
				_vector.push_back(item);
			}

			inline void pop_back() {
				if (_vector.size() == 0) {
					return;
				}
				_vector.pop_back();
			}

			inline void clear() {
				_vector.clear();
			}

			const T operator [](int i) const {
				FLUIDSIM_ASSERT(i >= 0 && i < (int)_vector.size());
				return _vector[i];
			}

    		T& operator[](int i) {
    			FLUIDSIM_ASSERT(i >= 0 && i < (int)_vector.size());
				return _vector[i];
    		}

		private:

			unsigned int _capacity = 0;
			std::vector<T> _vector;

	};

	void _initializeElementsPerChunk() {
		_elementsPerFragment = (int)(_bytesPerFragment / sizeof(T));
		if (_elementsPerFragment == 0) {
			_elementsPerFragment = 1;
		}

		_invElementsPerFragment = 1.0 / (double)_elementsPerFragment;
	}

	void _addNewVectorNode() {
		_nodes.push_back(VectorNode(_elementsPerFragment));
	}

	inline bool _isLastNode(int i) {
		return i == (int)_nodes.size() - 1;
	}

	inline bool _isCurrentNodeFull() {
		return _currentNodeIndex == -1 || _nodes[_currentNodeIndex].isFull();
	}

	inline static bool _defaultCompare(const T &p1, const T &p2) {
		return p1 < p2;
	}

	std::vector<VectorNode> _nodes;
	unsigned int _bytesPerFragment = 5e6;
	unsigned int _elementsPerFragment = 0;
	double _invElementsPerFragment = 0;
	int _currentNodeIndex = -1;
	unsigned int _size = 0;

};

#endif