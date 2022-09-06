// Mixbox is not available in this version
// This is a stub implementation

#include <cstdlib>

void mixbox_initialize(char *lut_data, size_t length) {}
bool mixbox_is_initialized() { return false; }

void mixbox_lerp_srgb8(unsigned char r1,unsigned char g1,unsigned char b1,
                       unsigned char r2,unsigned char g2,unsigned char b2,
                       float t,
                       unsigned char* out_r,unsigned char* out_g,unsigned char* out_b) { *out_r=0; *out_g=0; *out_b=0; }

void mixbox_lerp_srgb32f(float r1,float g1,float b1,
                         float r2,float g2,float b2,
                         float t,
                         float* out_r,float* out_g,float* out_b) { *out_r=0; *out_g=0; *out_b=0; }

void mixbox_srgb8_to_latent(unsigned char r,unsigned char g,unsigned char b,float* out_latent) { *out_latent=0; }
void mixbox_latent_to_srgb8(float* latent,unsigned char* out_r,unsigned char* out_g,unsigned char* out_b) { *out_r=0; *out_g=0; *out_b=0; }

void mixbox_srgb32f_to_latent(float r,float g,float b,float* out_latent) { *out_latent=0; }
void mixbox_latent_to_srgb32f(float* latent,float* out_r,float* out_g,float* out_b) { *out_r=0; *out_g=0; *out_b=0; }


void mixbox_lerp_srgb8_dither(unsigned char r1,unsigned char g1,unsigned char b1,
                              unsigned char r2,unsigned char g2,unsigned char b2,
                              float t,
                              float dither_r,float dither_g,float dither_b,
                              unsigned char* out_r,unsigned char* out_g,unsigned char* out_b) { *out_r=0; *out_g=0; *out_b=0; }

void mixbox_latent_to_srgb8_dither(float* latent,float dither_r,float dither_g,float dither_b,unsigned char* out_r,unsigned char* out_g,unsigned char* out_b) { *out_r=0; *out_g=0; *out_b=0; }
