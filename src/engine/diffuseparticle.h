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

#ifndef FLUIDENGINE_DIFFUSEPARTICLE_H
#define FLUIDENGINE_DIFFUSEPARTICLE_H

enum class DiffuseParticleType : char { 
    bubble = 0x00, 
    foam = 0x01, 
    spray = 0x02,
    dust = 0x03,
    notset = 0x04
};

struct DiffuseParticle {
    vmath::vec3 position;
    vmath::vec3 velocity;
    float lifetime;
    DiffuseParticleType type;
    unsigned char id;

    DiffuseParticle() : lifetime(0.0),
                        type(DiffuseParticleType::notset) {}

    DiffuseParticle(vmath::vec3 p, vmath::vec3 v, float time, unsigned char ident) : 
                        position(p),
                        velocity(v),
                        lifetime(time),
                        type(DiffuseParticleType::notset),
                        id(ident) {}
};

#endif
