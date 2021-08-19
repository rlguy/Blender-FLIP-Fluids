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

/*
    LevelSet methods adapted from Christopher Batty's levelset_util.cpp:
        https://github.com/christopherbatty/Fluid3D/blob/master/levelset_util.cpp

    and volume_fractions.cpp:
        https://github.com/christopherbatty/VariationalViscosity3D/blob/master/volume_fractions.cpp

*/

#include "levelsetutils.h"

namespace LevelsetUtils {

//Given two signed distance values (line endpoints), determine what fraction of a connecting segment is "inside"
float fractionInside(float phiLeft, float phiRight) {
    if(phiLeft < 0 && phiRight < 0) {
        return 1;
    }
    if (phiLeft < 0 && phiRight >= 0) {
        return phiLeft / (phiLeft - phiRight);
    }
    if(phiLeft >= 0 && phiRight < 0) {
        return phiRight / (phiRight - phiLeft);
    }
        
    return 0;
}

void _cycleArray(float* arr, int size) {
    float t = arr[0];
    for(int i = 0; i < size - 1; ++i) {
        arr[i] = arr[i + 1];
    }
    arr[size - 1] = t;
}

//Given four signed distance values (square corners), determine what fraction of the square is "inside"
float fractionInside(float phibl, float phibr, float phitl, float phitr) {
    
    int insideCount = (phibl < 0 ? 1 : 0) + 
                      (phitl < 0 ? 1 : 0) + 
                      (phibr < 0 ? 1 : 0) + 
                      (phitr < 0 ? 1 : 0);
    float list[] = { phibl, phibr, phitr, phitl };

    if(insideCount == 4) {
        return 1;
    } else if (insideCount == 3) {
        //rotate until the positive value is in the first position
        while(list[0] < 0) {
            _cycleArray(list, 4);
        }

        //Work out the area of the exterior triangle
        float side0 = 1 - fractionInside(list[0], list[3]);
        float side1 = 1 - fractionInside(list[0], list[1]);
        return 1.0f - 0.5f * side0 * side1;
    } else if(insideCount == 2) {
        
        //rotate until a negative value is in the first position, and the next negative is in either slot 1 or 2.
        while(list[0] >= 0 || !(list[1] < 0 || list[2] < 0)) {
            _cycleArray(list , 4);
        } 
        
        if(list[1] < 0) { //the matching signs are adjacent
            float sideLeft = fractionInside(list[0], list[3]);
            float sideRight = fractionInside(list[1], list[2]);
            return  0.5f * (sideLeft + sideRight);
        } else { 
            //matching signs are diagonally opposite
            //determine the centre point's sign to disambiguate this case
            float middlePoint = 0.25f * (list[0] + list[1] + list[2] + list[3]);
            if(middlePoint < 0) {
                float area = 0;

                //first triangle (top left)
                float side1 = 1 - fractionInside(list[0], list[3]);
                float side3 = 1 - fractionInside(list[2], list[3]);

                area += 0.5f * side1 * side3;

                //second triangle (top right)
                float side2 = 1 - fractionInside(list[2], list[1]);
                float side0 = 1 - fractionInside(list[0], list[1]);
                area += 0.5f * side0 * side2;
                
                return 1.0f - area;
            }
            else {
                float area = 0;

                //first triangle (bottom left)
                float side0 = fractionInside(list[0], list[1]);
                float side1 = fractionInside(list[0], list[3]);
                area += 0.5f * side0*side1;

                //second triangle (top right)
                float side2 = fractionInside(list[2], list[1]);
                float side3 = fractionInside(list[2], list[3]);
                area += 0.5f * side2 * side3;
                return area;
            }
            
        }
    } else if(insideCount == 1) {
        //rotate until the negative value is in the first position
        while(list[0] >= 0) {
            _cycleArray(list, 4);
        }

        //Work out the area of the interior triangle, and subtract from 1.
        float side0 = fractionInside(list[0], list[3]);
        float side1 = fractionInside(list[0], list[1]);
        return 0.5f * side0 * side1;
    } else {
        return 0;
    }

}

float areaFraction(float phi0, float phi1, float phi2) {
    if(phi0 < 0) {
        if (phi1 < 0) {
            if(phi2<0) {
                return 0;
            } else { 
                return 1 - _sortedTriangleFraction(phi2, phi0, phi1);
            }
        } else if (phi2 < 0) { 
            return 1 - _sortedTriangleFraction(phi1, phi2, phi0);
        } else {
            return _sortedTriangleFraction(phi0, phi1, phi2);
        }
    } else if(phi1 < 0) {
        if (phi2 < 0) {
            return 1 - _sortedTriangleFraction(phi0, phi1, phi2);
        } else {
            return _sortedTriangleFraction(phi1, phi2, phi0);
        }
    } else if (phi2 < 0) {
        return _sortedTriangleFraction(phi2, phi0, phi1);
    } else {
        return 0;
    }
}

double areaFraction(double phi0, double phi1, double phi2) {
     if(phi0 < 0) {
        if (phi1 < 0) {
            if(phi2<0) {
                return 0;
            } else { 
                return 1 - _sortedTriangleFraction(phi2, phi0, phi1);
            }
        } else if (phi2 < 0) { 
            return 1 - _sortedTriangleFraction(phi1, phi2, phi0);
        } else {
            return _sortedTriangleFraction(phi0, phi1, phi2);
        }
    } else if(phi1 < 0) {
        if (phi2 < 0) {
            return 1 - _sortedTriangleFraction(phi0, phi1, phi2);
        } else {
            return _sortedTriangleFraction(phi1, phi2, phi0);
        }
    } else if (phi2 < 0) {
        return _sortedTriangleFraction(phi2, phi0, phi1);
    } else {
        return 0;
    }
}

float areaFraction(float phi00, float phi10, float phi01, float phi11) {
    float phimid = 0.25f * (phi00 + phi10 + phi01 + phi11);
    return 0.25f * (areaFraction(phi00, phi10, phimid) +
                    areaFraction(phi10, phi11, phimid) +
                    areaFraction(phi11, phi01, phimid) +
                    areaFraction(phi01, phi00, phimid));
}

double areaFraction(double phi00, double phi10, double phi01, double phi11) {
    double phimid = 0.25 * (phi00 + phi10 + phi01 + phi11);
    return 0.25 * (areaFraction(phi00, phi10, phimid) +
                   areaFraction(phi10, phi11, phimid) +
                   areaFraction(phi11, phi01, phimid) +
                   areaFraction(phi01, phi00, phimid));
}

float volumeFraction(float phi0, float phi1, float phi2, float phi3) {
    _sort(phi0, phi1, phi2, phi3);
    if (phi3 <= 0) { 
        return 1;
    } else if (phi2 <= 0) { 
        return 1 - _sortedTetFraction(phi3, phi2, phi1, phi0);
    } else if (phi1 <= 0) { 
        return _sortedPrismFraction(phi0, phi1, phi2, phi3);
    } else if (phi0 <= 0) { 
        return _sortedTetFraction(phi0, phi1, phi2, phi3);
    } else {
        return 0;
    }
}

double volumeFraction(double phi0, double phi1, double phi2, double phi3) {
    _sort(phi0, phi1, phi2, phi3);
    if (phi3 <= 0) { 
        return 1;
    } else if (phi2 <= 0) { 
        return 1 - _sortedTetFraction(phi3, phi2, phi1, phi0);
    } else if (phi1 <= 0) { 
        return _sortedPrismFraction(phi0, phi1, phi2, phi3);
    } else if (phi0 <= 0) { 
        return _sortedTetFraction(phi0, phi1, phi2, phi3);
    } else {
        return 0;
    }
}

float volumeFraction(float phi000, float phi100,
                     float phi010, float phi110,
                     float phi001, float phi101,
                     float phi011, float phi111) {
    // This is the average of the two possible decompositions of the cube into
    // five tetrahedra.
    return (volumeFraction(phi000, phi001, phi101, phi011) +
            volumeFraction(phi000, phi101, phi100, phi110) +
            volumeFraction(phi000, phi010, phi011, phi110) +
            volumeFraction(phi101, phi011, phi111, phi110) +
            2 * volumeFraction(phi000, phi011, phi101, phi110) +
            volumeFraction(phi100, phi101, phi001, phi111) +
            volumeFraction(phi100, phi001, phi000, phi010) +
            volumeFraction(phi100, phi110, phi111, phi010) +
            volumeFraction(phi001, phi111, phi011, phi010) +
            2 * volumeFraction(phi100, phi111, phi001, phi010)) / 12.0f;
}

double volumeFraction(double phi000, double phi100,
                                             double phi010, double phi110,
                                             double phi001, double phi101,
                                             double phi011, double phi111) {
    return (volumeFraction(phi000, phi001, phi101, phi011) +
            volumeFraction(phi000, phi101, phi100, phi110) +
            volumeFraction(phi000, phi010, phi011, phi110) +
            volumeFraction(phi101, phi011, phi111, phi110) +
            2 * volumeFraction(phi000, phi011, phi101, phi110) +
            volumeFraction(phi100, phi101, phi001, phi111) +
            volumeFraction(phi100, phi001, phi000, phi010) +
            volumeFraction(phi100, phi110, phi111, phi010) +
            volumeFraction(phi001, phi111, phi011, phi010) +
            2 * volumeFraction(phi100, phi111, phi001, phi010)) / 12.0;
}


}