/*
MIT License

Copyright (c) 2019 Ryan L. Guy

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

#ifndef FLUIDENGINE_FORCEFIELDSURFACE_H
#define FLUIDENGINE_FORCEFIELDSURFACE_H

#include "forcefield.h"
#include "meshlevelset.h"


class ForceFieldSurface : public ForceField
{
public:
    ForceFieldSurface();
    virtual ~ForceFieldSurface();

    virtual void update(double dt);
    virtual void addForceFieldToGrid(MACVelocityField &fieldGrid);
    virtual std::vector<vmath::vec3> generateDebugProbes();

protected:
    virtual void _initialize();

private:

	int _ioffsetSDF = 0;
	int _joffsetSDF = 0;
	int _koffsetSDF = 0;
	vmath::vec3 _offsetSDF;
	int _isizeSDF = 0;
	int _jsizeSDF = 0;
	int _ksizeSDF = 0;

	bool _isLevelsetUpToDate = false;
	float _minForceThreshold = 1e-4;
	float _lastMaxDistance = -1.0f;

	MeshLevelSet _sdf;
	int _exactBand = 3;

};

#endif
