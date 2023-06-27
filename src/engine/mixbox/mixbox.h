// MIXBOX v1.2 (c) 2022 Secret Weapons
// This is for non-commercial use only.
// Contact: mixbox@scrtwpns.com

/*
1206018 B.C. LTD. has been granted a certificate to distribute Mixbox with the FLIP Fluids addon for commercial use.
This certificate allows users of the FLIP Fluids addon to use the Mixbox features for commerical use.
Learn more about Mixbox here: https://scrtwpns.com/mixbox/

The Mixbox plugin is distributed separately from the FLIP Fluids addon installation file as "Mixbox.plugin".
This plugin contains data that is required for using the FLIP Fluids addon Mixbox feature set and can be installed
in the FLIP Fluids addon preferences menu.

Certificate transcription:

--------------------
SECRET WEAPONS, INC.

Certificate of License

THIS IS TO CERTIFY THAT

1206018 B.C. LTD.

IS GRANTED A LICENSE TO USE THE MIXBOX SOFTWARE LIBRARY FOR COMMERCIAL PURPOSES

LICENSE PERIOD: 6/13/2023 - 6/13/2024
LICENSE NUMBER: 385-0012

Signed:

ŠÁRKA SOCHOROVÁ, Founder
ONDŘEJ JAMRIŠKA, Founder
--------------------
*/

#ifndef MIXBOX_H_
#define MIXBOX_H_

#define MIXBOX_NUMLATENTS 7

void mixbox_initialize(char *lut_data, size_t length);
bool mixbox_is_initialized();

void mixbox_lerp_srgb8(unsigned char r1,unsigned char g1,unsigned char b1,
                       unsigned char r2,unsigned char g2,unsigned char b2,
                       float t,
                       unsigned char* out_r,unsigned char* out_g,unsigned char* out_b);

void mixbox_lerp_srgb32f(float r1,float g1,float b1,
                         float r2,float g2,float b2,
                         float t,
                         float* out_r,float* out_g,float* out_b);

void mixbox_srgb8_to_latent(unsigned char r,unsigned char g,unsigned char b,float* out_latent);
void mixbox_latent_to_srgb8(float* latent,unsigned char* out_r,unsigned char* out_g,unsigned char* out_b);

void mixbox_srgb32f_to_latent(float r,float g,float b,float* out_latent);
void mixbox_latent_to_srgb32f(float* latent,float* out_r,float* out_g,float* out_b);


void mixbox_lerp_srgb8_dither(unsigned char r1,unsigned char g1,unsigned char b1,
                              unsigned char r2,unsigned char g2,unsigned char b2,
                              float t,
                              float dither_r,float dither_g,float dither_b,
                              unsigned char* out_r,unsigned char* out_g,unsigned char* out_b);

void mixbox_latent_to_srgb8_dither(float* latent,float dither_r,float dither_g,float dither_b,unsigned char* out_r,unsigned char* out_g,unsigned char* out_b);

#endif
// END ifndef MIXBOX_H_
