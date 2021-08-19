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


#ifndef FLUIDENGINE_LEVELSETUTILS_H
#define FLUIDENGINE_LEVELSETUTILS_H

namespace LevelsetUtils {

extern float fractionInside(float phi_left, float phi_right);
extern float fractionInside(float phi_bl, float phi_br, float phi_tl, float phi_tr);

extern void _cycleArray(float* arr, int size);

// Given a triangle with level set values, use linear interpolation to
// estimate the fraction of the triangle occupied by the phi<0 part
extern float areaFraction(float phi0, float phi1, float phi2);
extern double areaFraction(double phi0, double phi1, double phi2);

// Given a rectangle with level set values, estimate fraction occupied
// by the phi<0 part
extern float areaFraction(float phi00, float phi10, float phi01, float phi11);
extern double areaFraction(double phi00, double phi10, double phi01, double phi11);

// Given a tetrahedron with level set values, use linear interpolation to
// estimate the fraction of the tetrahedron occupied by the phi<0 part
extern float volumeFraction(float phi0, float phi1, float phi2, float phi3);
extern double volumeFraction(double phi0, double phi1, double phi2, double phi3);

// Given a parallelepiped (e.g. cube) with level set values, estimate
// fraction occupied by the phi<0 part
extern float volumeFraction(float phi000, float phi100,
                            float phi010, float phi110,
                            float phi001, float phi101,
                            float phi011, float phi111);
extern double volumeFraction(double phi000, double phi100,
                             double phi010, double phi110,
                             double phi001, double phi101,
                             double phi011, double phi111);

// Assumes phi0<0 and phi1>=0, phi2>=0, or vice versa.
// In particular, phi0 must not equal either of phi1 or phi2.
template<class T>
static T _sortedTriangleFraction(T phi0, T phi1, T phi2) {
    return phi0 * phi0 / (2 * (phi0 - phi1) * (phi0 - phi2));
}

// Assumes phi0<0 and phi1>=0, phi2>=0, and phi3>=0 or vice versa.
// In particular, phi0 must not equal any of phi1, phi2 or phi3.
template<class T>
static T _sortedTetFraction(T phi0, T phi1, T phi2, T phi3) {
    return phi0 * phi0 * phi0 / ((phi0 - phi1) * (phi0 - phi2) * (phi0 - phi3));
}

// Assumes phi0<0, phi1<0, and phi2>=0, and phi3>=0 or vice versa.
// In particular, phi0 and phi1 must not equal any of phi2 and phi3.
template<class T>
static T _sortedPrismFraction(T phi0, T phi1, T phi2, T phi3) {
    T a = phi0 / (phi0 - phi2);
    T b = phi0 / (phi0 - phi3);
    T c = phi1 / (phi1 - phi3);
    T d = phi1 / (phi1 - phi2);
    return a * b * (1 - d) + b * (1 - c) * d + c * d;
}

template <class T> 
void _swap (T &a, T &b) {
    T c(a); 
    a = b; 
    b = c;
}

template<class T>
inline void _sort(T &a, T &b, T &c, T &d)
{
    if(a>b) { _swap(a,b); }
    if(c>d) { _swap(c,d); }
    if(a>c) { _swap(a,c); }
    if(b>d) { _swap(b,d); }
    if(b>c) { _swap(b,c); }
}

}

#endif