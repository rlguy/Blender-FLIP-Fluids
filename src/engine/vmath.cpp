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

#include "vmath.h"

#include "fluidsimassert.h"

/********************************************************************************
    VECTOR 3
********************************************************************************/

vmath::vec3::vec3() : x(0.0), y(0.0), z(0.0) {
}

vmath::vec3::vec3(float xx, float yy, float zz) : x(xx), y(yy), z(zz) {
}

vmath::vec3::~vec3() { 
}

std::ostream& vmath::operator<<(std::ostream& os, const vmath::vec3& v){
    os << v.x << "\t" << v.y << "\t" << v.z;
    return os;
}

vmath::vec3 vmath::vec3::add(const vmath::vec3 &v) {
    return *this + v;
}

vmath::vec3 vmath::operator+(const vmath::vec3 &v1, const vmath::vec3 &v2) {
    return vmath::vec3(v1.x + v2.x, v1.y + v2.y, v1.z + v2.z);
}

vmath::vec3& vmath::operator+=(vmath::vec3 &v1, const vmath::vec3 &v2) {
    v1.x += v2.x;
    v1.y += v2.y;
    v1.z += v2.z;
    return v1;
}

vmath::vec3  vmath::vec3::subtract(const vmath::vec3 &v) {
    return *this - v;
}

vmath::vec3 vmath::operator-(const vmath::vec3 &v1, const vmath::vec3 &v2) {
    return vmath::vec3(v1.x - v2.x, v1.y - v2.y, v1.z - v2.z);
}

vmath::vec3& vmath::operator-=(vmath::vec3 &v1, const vmath::vec3 &v2) {
    v1.x -= v2.x;
    v1.y -= v2.y;
    v1.z -= v2.z;
    return v1;
}

vmath::vec3  vmath::vec3::mult(float s) {
    return *this * s;
}

vmath::vec3 vmath::operator*(float s, const vmath::vec3 &v) {
    return vmath::vec3(v.x*s, v.y*s, v.z*s);
}

vmath::vec3 vmath::operator*(const vmath::vec3 &v, float s) {
    return vmath::vec3(v.x*s, v.y*s, v.z*s);
}

vmath::vec3& vmath::operator*=(vmath::vec3 &v, float s) {
    v.x *= s;
    v.y *= s;
    v.z *= s;
    return v;
}

vmath::vec3  vmath::vec3::divide(float s) {
    return *this / s;
}

vmath::vec3 vmath::operator/(const vmath::vec3 &v, float s) {
    float inv = 1.0 / s;
    return vmath::vec3(v.x*inv, v.y*inv, v.z*inv);
}

vmath::vec3& vmath::operator/=(vmath::vec3 &v1, float s) {
    float inv = 1.0 / s;
    v1.x *= inv;
    v1.y *= inv;
    v1.z *= inv;
    return v1;
}

vmath::vec3 vmath::vec3::negate() {
    return -(*this);
}

vmath::vec3 vmath::operator-(const vmath::vec3 &v) {
    return vmath::vec3(-v.x, -v.y, -v.z);
}

float vmath::vec3::get(int i) {
    FLUIDSIM_ASSERT(i >= 0 && i <= 2);
    return (&x)[i];
}

float vmath::vec3::operator[](int i) {
    FLUIDSIM_ASSERT(i >= 0 && i <= 2);
    return (&x)[i];
}

float vmath::vec3::dot(const vmath::vec3 &v) {
    return vmath::dot(*this, v);
}

vmath::vec3 vmath::vec3::cross(const vmath::vec3 &v) {
    return vmath::cross(*this, v);
}

float vmath::vec3::lengthsq() {
    return vmath::lengthsq(*this);
}

float vmath::vec3::length() {
    return vmath::length(*this);
}

vmath::vec3 vmath::vec3::normalize() {
    return vmath::normalize(*this);
}

/********************************************************************************
    MATRIX 3
********************************************************************************/

vmath::mat3::mat3() {
    m[0] = 1.0; m[1] = 0.0; m[2] = 0.0; 
    m[3] = 0.0; m[4] = 1.0; m[5] = 0.0; 
    m[6] = 0.0; m[7] = 0.0; m[8] = 1.0;
}

vmath::mat3::mat3(const vmath::vec3 &v1, const vmath::vec3 &v2, const vmath::vec3 &v3) {
    m[0] = v1.x; m[1] = v1.y; m[2] = v1.z; 
    m[3] = v2.x; m[4] = v2.y; m[5] = v2.z; 
    m[6] = v3.x; m[7] = v3.y; m[8] = v3.z;
}

vmath::mat3::mat3(const float vals[9]) {
    m[0] = vals[0]; m[1] = vals[1]; m[2] = vals[2]; 
    m[3] = vals[3]; m[4] = vals[4]; m[5] = vals[5]; 
    m[6] = vals[6]; m[7] = vals[7]; m[8] = vals[8];
}

vmath::mat3::mat3(float v0, float v1, float v2, 
                  float v3, float v4, float v5, 
                  float v6, float v7, float v8) {
    m[0] = v0; m[1] = v1; m[2] = v2; 
    m[3] = v3; m[4] = v4; m[5] = v5; 
    m[6] = v6; m[7] = v7; m[8] = v8;
}

vmath::mat3::mat3(float fillval) {
    m[0] = fillval; m[1] = fillval; m[2] = fillval; 
    m[3] = fillval; m[4] = fillval; m[5] = fillval; 
    m[6] = fillval; m[7] = fillval; m[8] = fillval;
}

vmath::mat3::~mat3() { 
}

std::ostream& vmath::operator<<(std::ostream& os, const vmath::mat3& m){
    os << m.m[0] << "\t" << m.m[3] << "\t" << m.m[6] << std::endl <<
          m.m[1] << "\t" << m.m[4] << "\t" << m.m[7] << std::endl <<
          m.m[2] << "\t" << m.m[5] << "\t" << m.m[8];
    return os;
}

vmath::mat3 vmath::mat3::add(const mat3 &m) {
    return *this + m;
}

vmath::mat3 vmath::operator+(const vmath::mat3 &m1, const vmath::mat3 &m2) {
    return vmath::mat3(m1.m[0] + m2.m[0], m1.m[1] + m2.m[1], m1.m[2] + m2.m[2],
                       m1.m[3] + m2.m[3], m1.m[4] + m2.m[4], m1.m[5] + m2.m[5], 
                       m1.m[6] + m2.m[6], m1.m[7] + m2.m[7], m1.m[8] + m2.m[8]);
}

vmath::mat3 &vmath::operator+=(vmath::mat3 &m1, const vmath::mat3 &m2) {
    m1.m[0] += m2.m[0]; m1.m[1] += m2.m[1]; m1.m[2] += m2.m[2];
    m1.m[3] += m2.m[3]; m1.m[4] += m2.m[4]; m1.m[5] += m2.m[5];
    m1.m[6] += m2.m[6]; m1.m[7] += m2.m[7]; m1.m[8] += m2.m[8];
    return m1;
}

vmath::mat3 vmath::mat3::subtract(const mat3 &m) {
    return *this - m;
}

vmath::mat3 vmath::operator-(const vmath::mat3 &m1, const vmath::mat3 &m2) {
    return vmath::mat3(m1.m[0] - m2.m[0], m1.m[1] - m2.m[1], m1.m[2] - m2.m[2],
                       m1.m[3] - m2.m[3], m1.m[4] - m2.m[4], m1.m[5] - m2.m[5], 
                       m1.m[6] - m2.m[6], m1.m[7] - m2.m[7], m1.m[8] - m2.m[8]);
}

vmath::mat3 &vmath::operator-=(vmath::mat3 &m1, const vmath::mat3 &m2) {
    m1.m[0] -= m2.m[0]; m1.m[1] -= m2.m[1]; m1.m[2] -= m2.m[2];
    m1.m[3] -= m2.m[3]; m1.m[4] -= m2.m[4]; m1.m[5] -= m2.m[5];
    m1.m[6] -= m2.m[6]; m1.m[7] -= m2.m[7]; m1.m[8] -= m2.m[8];
    return m1;
}

vmath::mat3 vmath::mat3::mult(float s) {
    return *this * s;
}

vmath::mat3 vmath::mat3::mult(const vmath::mat3 &m) {
    return *this * m;
}

vmath::vec3 vmath::mat3::mult(const vmath::vec3 &v) {
    return *this * v;
}

vmath::mat3 vmath::operator*(float s, const vmath::mat3 &m) {
    return vmath::mat3(m.m[0]*s, m.m[1]*s, m.m[2]*s, 
                       m.m[3]*s, m.m[4]*s, m.m[5]*s, 
                       m.m[6]*s, m.m[7]*s, m.m[8]*s);
}

vmath::mat3 vmath::operator*(const vmath::mat3 &m, float s) {
    return vmath::mat3(m.m[0]*s, m.m[1]*s, m.m[2]*s, 
                       m.m[3]*s, m.m[4]*s, m.m[5]*s, 
                       m.m[6]*s, m.m[7]*s, m.m[8]*s);
}

vmath::mat3 vmath::operator*(const vmath::mat3 &m1, const vmath::mat3 &m2) {
    return vmath::mat3(m1.m[0]*m2.m[0] + m1.m[3]*m2.m[1] + m1.m[6]*m2.m[2],
                       m1.m[1]*m2.m[0] + m1.m[4]*m2.m[1] + m1.m[7]*m2.m[2],
                       m1.m[2]*m2.m[0] + m1.m[5]*m2.m[1] + m1.m[8]*m2.m[2],
                       m1.m[0]*m2.m[3] + m1.m[3]*m2.m[4] + m1.m[6]*m2.m[5],
                       m1.m[1]*m2.m[3] + m1.m[4]*m2.m[4] + m1.m[7]*m2.m[5],
                       m1.m[2]*m2.m[3] + m1.m[5]*m2.m[4] + m1.m[8]*m2.m[5],
                       m1.m[0]*m2.m[6] + m1.m[3]*m2.m[7] + m1.m[6]*m2.m[8],
                       m1.m[1]*m2.m[6] + m1.m[4]*m2.m[7] + m1.m[7]*m2.m[8],
                       m1.m[2]*m2.m[6] + m1.m[5]*m2.m[7] + m1.m[8]*m2.m[8]);
}

vmath::vec3 vmath::operator*(const vmath::mat3 &m, const vmath::vec3 &v) {
    return vmath::vec3(m.m[0]*v.x + m.m[3]*v.y + m.m[6]*v.z,
                       m.m[1]*v.x + m.m[4]*v.y + m.m[7]*v.z,
                       m.m[2]*v.x + m.m[5]*v.y + m.m[8]*v.z);
}

vmath::mat3 &vmath::operator*=(vmath::mat3 &m, float s) {
    m.m[0] *= s; m.m[1] *= s; m.m[2] *= s; 
    m.m[3] *= s; m.m[4] *= s; m.m[5] *= s; 
    m.m[6] *= s; m.m[7] *= s; m.m[8] *= s; 
    return m;
}

vmath::mat3 vmath::mat3::divide(float s) {
    return *this / s;
}

vmath::mat3 vmath::operator/(const vmath::mat3 &m, float s) {
    float inv = 1.0 / s;
    return vmath::mat3(m.m[0]*inv, m.m[1]*inv, m.m[2]*inv,
                       m.m[3]*inv, m.m[4]*inv, m.m[5]*inv, 
                       m.m[6]*inv, m.m[7]*inv, m.m[8]*inv);
}

vmath::mat3 &vmath::operator/=(vmath::mat3 &m, float s) {
    float inv = 1.0 / s;
    m.m[0] *= inv; m.m[1] *= inv; m.m[2] *= inv; 
    m.m[3] *= inv; m.m[4] *= inv; m.m[5] *= inv; 
    m.m[6] *= inv; m.m[7] *= inv; m.m[8] *= inv; 
    return m;
}

vmath::mat3 vmath::mat3::negate() {
    return -(*this);
}

vmath::mat3 vmath::operator-(const vmath::mat3 &m) {
    return vmath::mat3(-m.m[0], -m.m[1], -m.m[2],
                     -m.m[3], -m.m[4], -m.m[5], 
                     -m.m[6], -m.m[7], -m.m[8]);
}

vmath::vec3 vmath::mat3::get(int i) {
    FLUIDSIM_ASSERT(i >= 0 && i <= 2);
    return vec3(m[3*i], m[3*i + 1], m[3*i + 2]);
}

vmath::vec3 vmath::mat3::operator[](int i) {
    FLUIDSIM_ASSERT(i >= 0 && i <= 2);
    return vec3(m[3*i], m[3*i + 1], m[3*i + 2]);
}

vmath::mat3 vmath::mat3::transpose() {
    return vmath::transpose(*this);
}

/********************************************************************************
    QUATERNION
********************************************************************************/

vmath::quat::quat() : w(0.0), x(0.0), y(0.0), z(0.0) { 
}

vmath::quat::quat(float rads, const vec3 &v) :
                    w(rads), x(v.x), y(v.y), z(v.z) { 
}

vmath::quat::~quat() { 
}

std::ostream& vmath::operator<<(std::ostream& os, const vmath::quat& q){
    os << q.w << "\t" << q.x << "\t" << q.y << "\t" << q.z;
    return os;
}

vmath::mat3 vmath::quat::mat3_cast() {
    return vmath::mat3_cast(*this);
}

vmath::quat vmath::quat::normalize() {
    return vmath::normalize(*this);
}