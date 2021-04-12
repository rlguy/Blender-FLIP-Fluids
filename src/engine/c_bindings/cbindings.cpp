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

#include "cbindings.h"

#ifdef _WIN32
    #define EXPORTDLL __declspec(dllexport)
#else
    #define EXPORTDLL
#endif

namespace CBindings {

int SUCCESS = 1;
int FAIL = 0;
char CBINDINGS_ERROR_MESSAGE[4096];

void set_error_message(std::exception &ex) {
    std::string msg = ex.what();
    msg.copy(CBINDINGS_ERROR_MESSAGE, msg.length(), 0);
    CBINDINGS_ERROR_MESSAGE[msg.length()] = '\0';
}

char* get_error_message() {
	return CBINDINGS_ERROR_MESSAGE;
}

Vector3_t to_struct(vmath::vec3 v) {
	return Vector3_t{ v.x, v.y, v.z};
}

vmath::vec3 to_class(Vector3_t v) {
	return vmath::vec3(v.x, v.y, v.z);
}

AABB_t to_struct(AABB b) {
	Vector3_t cpos = to_struct(b.position);
    return AABB_t{ cpos,
                   (float)b.width, 
                   (float)b.height, 
                   (float)b.depth };
}

AABB to_class(AABB_t b) {
	return AABB(b.position.x, b.position.y, b.position.z,
                b.width, b.height, b.depth);
}

MarkerParticle_t to_struct(MarkerParticle p) {
    Vector3_t pos = to_struct(p.position);
    Vector3_t vel = to_struct(p.velocity);
    return MarkerParticle_t{ pos, vel };
}

MarkerParticle to_class(MarkerParticle_t p) {
    vmath::vec3 pos = to_class(p.position);
    vmath::vec3 vel = to_class(p.velocity);
    return MarkerParticle(pos, vel);
}

DiffuseParticle_t to_struct(DiffuseParticle p) {
    Vector3_t pos = to_struct(p.position);
    Vector3_t vel = to_struct(p.velocity);
    return DiffuseParticle_t{ pos, vel, p.lifetime, (char)p.type, p.id };
}

DiffuseParticle to_class(DiffuseParticle_t p) {
    vmath::vec3 pos = to_class(p.position);
    vmath::vec3 vel = to_class(p.velocity);
    
    DiffuseParticle dp(pos, vel, p.lifetime, p.id);
    dp.type = (DiffuseParticleType)p.type;
    return dp;
}


}

extern "C" {
	EXPORTDLL char* CBindings_get_error_message() {
        return CBindings::get_error_message();
    }
}