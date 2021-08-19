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

#ifndef FLUIDENGINE_VMATH_H
#define FLUIDENGINE_VMATH_H

#include <iostream>
#include <cmath>

namespace vmath {

/********************************************************************************
    VECTOR 3
********************************************************************************/

// 3 component column vector
class vec3
{
public:
    vec3();
    vec3(float xx, float yy, float zz);
    ~vec3();

    vec3 add(const vec3 &v);
    vec3 subtract(const vec3 &v);
    vec3 mult(float s);
    vec3 divide(float s);
    vec3 negate();
    float get(int i);
    float operator[](int i);
    float dot(const vec3 &v);
    vec3 cross(const vec3 &v);
    float lengthsq();
    float length();
    vec3 normalize();

    float x;
    float y;
    float z;
    
};

std::ostream& operator<<(std::ostream& os, const vec3& v);
vec3 operator+(const vec3 &v1, const vec3 &v2);
vec3 &operator+=(vec3 &v1, const vec3 &v2);
vec3 operator-(const vec3 &v1, const vec3 &v2);
vec3 &operator-=(vec3 &v1, const vec3 &v2);
vec3 operator*(float s, const vec3 &v);
vec3 operator*(const vec3 &v, float s);
vec3 &operator*=(vec3 &v, float s);
vec3 operator/(const vec3 &v, float s);
vec3 &operator/=(vec3 &v1, float s);
vec3 operator-(const vec3 &v);

inline float dot(const vec3 &v1, const vec3 &v2) {
    return v1.x*v2.x + v1.y*v2.y + v1.z*v2.z;
}

inline vec3 cross(const vec3 &v1, const vec3 &v2) {
    return vec3(v1.y*v2.z - v1.z*v2.y,
                       v1.z*v2.x - v1.x*v2.z,
                       v1.x*v2.y - v1.y*v2.x);
}

inline float lengthsq(const vec3 &v) {
    return v.x*v.x + v.y*v.y + v.z*v.z;
}

inline float length(const vec3 &v) {
    return sqrt(vmath::lengthsq(v));
}

inline vec3 normalize(const vec3 &v) {
    float len = vmath::length(v);
    return v / len;
}

inline bool equals(const vec3 &v1, const vec3 &v2, double eps) {
    return std::abs((double)v1.x - (double)v2.x) < eps && 
           std::abs((double)v1.y - (double)v2.y) < eps && 
           std::abs((double)v1.z - (double)v2.z) < eps;
}

inline bool isCollinear(const vec3 &v1, const vec3 &v2, double eps) {
    double len1 = sqrt((double)v1.x * (double)v1.x + (double)v1.y * (double)v1.y + (double)v1.z * (double)v1.z);
    double len2 = sqrt((double)v2.x * (double)v2.x + (double)v2.y * (double)v2.y + (double)v2.z * (double)v2.z);
    double n1x = (double)v1.x / len1;
    double n1y = (double)v1.y / len1;
    double n1z = (double)v1.z / len1;
    double n2x = (double)v2.x / len2;
    double n2y = (double)v2.y / len2;
    double n2z = (double)v2.z / len2;
    double absdot = std::abs(n1x * n2x + n1y * n2y + n1z * n2z);
    return std::abs(absdot - 1.0) < eps;
}

inline void generateBasisVectors(const vec3 &basisX, const vec3 &v, vec3 &b1, vec3 &b2, vec3 &b3) {
    b1 = normalize(basisX);
    b2 = cross(b1, v).normalize();
    b3 = cross(b1, b2).normalize();
}

/********************************************************************************
    MATRIX 3
********************************************************************************/

// 3x3 matrix stored in column major order
class mat3
{
public:
    mat3();
    mat3(const vec3 &v1, const vec3 &v2, const vec3 &v3);
    mat3(const float vals[9]);
    mat3(float v0, float v1, float v2, 
         float v3, float v4, float v5, 
         float v6, float v7, float v8);
    mat3(float fillval);
    ~mat3();

    mat3 add(const mat3 &m);
    mat3 subtract(const mat3 &m);
    mat3 mult(float s);
    mat3 mult(const mat3 &m);
    vec3 mult(const vec3 &v);
    mat3 divide(float s);
    mat3 negate();
    vec3 get(int i);
    vec3 operator[](int i);
    mat3 transpose();

    float m[9];
    
};

std::ostream& operator<<(std::ostream& os, const mat3& m);
mat3 operator+(const mat3 &m1, const mat3 &m2);
mat3 &operator+=(mat3 &m1, const mat3 &m2);
mat3 operator-(const mat3 &m1, const mat3 &m2);
mat3 &operator-=(mat3 &m1, const mat3 &m2);
mat3 operator*(float s, const mat3 &m);
mat3 operator*(const mat3 &m, float s);
mat3 operator*(const mat3 &m1, const mat3 &m2);
vec3 operator*(const mat3 &m, const vec3 &v);
mat3 &operator*=(mat3 &m, float s);
mat3 operator/(const mat3 &m, float s);
mat3 &operator/=(mat3 &m, float s);
mat3 operator-(const mat3 &m);

inline mat3 transpose(const mat3 &m) {
    return mat3(m.m[0], m.m[3], m.m[6], 
                m.m[1], m.m[4], m.m[7], 
                m.m[2], m.m[5], m.m[8]);
}

inline mat3 localToWorldTransform(const vec3 &basisX, const vec3 &basisY, const vec3 &basisZ) {
    vmath::vec3 worldX(1, 0, 0);
    vmath::vec3 worldY(0, 1, 0);
    vmath::vec3 worldZ(0, 0, 1);

    vmath::vec3 x1p = normalize(basisX);
    vmath::vec3 x2p = normalize(basisY);
    vmath::vec3 x3p = normalize(basisZ);

    return vmath::mat3(
            vmath::dot(worldX, x1p), vmath::dot(worldX, x2p), vmath::dot(worldX, x3p),
            vmath::dot(worldY, x1p), vmath::dot(worldY, x2p), vmath::dot(worldY, x3p),
            vmath::dot(worldZ, x1p), vmath::dot(worldZ, x2p), vmath::dot(worldZ, x3p)
            );
}

/********************************************************************************
    QUATERNION
********************************************************************************/

class quat
{
public:
    
    quat();
    quat(float rads, const vec3 &v);
    ~quat();

    mat3 mat3_cast();
    quat normalize();

    float w;
    float x;
    float y;
    float z;
    
};

std::ostream& operator<<(std::ostream& os, const quat& q);

inline mat3 mat3_cast(const quat &q) {
    return mat3(1.0f - 2.0f*q.y*q.y - 2.0f*q.z*q.z,
                2.0f*q.x*q.y + 2.0f*q.z*q.w,
                2.0f*q.x*q.z - 2.0f*q.y*q.w,
                2.0f*q.x*q.y - 2.0f*q.z*q.w,
                1.0f - 2.0f*q.x*q.x - 2.0f*q.z*q.z,
                2.0f*q.y*q.z + 2.0f*q.x*q.w,
                2.0f*q.x*q.z + 2.0f*q.y*q.w,
                2.0f*q.y*q.z - 2.0f*q.x*q.w,
                1.0f - 2.0f*q.x*q.x - 2.0f*q.y*q.y);
}

inline quat normalize(const vmath::quat &q) {
    float lensq = q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z;

    float inv = 1.0f / sqrt(lensq);
    vmath::quat nq;
    nq.w = q.w*inv;
    nq.x = q.x*inv;
    nq.y = q.y*inv;
    nq.z = q.z*inv;

    return nq;
}

inline quat cross(const vmath::quat &q1, const vmath::quat &q2) {
    float s1 = q1.w;
    float s2 = q2.w;
    vmath::vec3 v1 = vmath::vec3(q1.x, q1.y, q1.z);
    vmath::vec3 v2 = vmath::vec3(q2.x, q2.y, q2.z);

    float scalar = s1*s2 - vmath::dot(v1, v2);
    vmath::vec3 vect = s1*v2 + s2*v1 + vmath::cross(v1, v2);

    vmath::quat newq;
    newq.w = scalar;
    newq.x = vect.x;
    newq.y = vect.y;
    newq.z = vect.z;

    return newq;
}

}

#endif