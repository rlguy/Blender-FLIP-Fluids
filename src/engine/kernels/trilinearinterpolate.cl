/*
MIT License

Copyright (c) 2018 Ryan L. Guy

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

#define CHUNK_WIDTH 8
#define CHUNK_HEIGHT 8
#define CHUNK_DEPTH 8

#define U_OFFSET 0
#define V_OFFSET 900        // U_OFFSET + (CHUNK_WIDTH + 1) * (CHUNK_HEIGHT + 2) * (CHUNK_DEPTH + 2)
#define W_OFFSET 1800       // V_OFFSET + (CHUNK_WIDTH + 2) * (CHUNK_HEIGHT + 1) * (CHUNK_DEPTH + 2)
#define VFIELD_SIZE 2700    // W_OFFSET + (CHUNK_WIDTH + 2) * (CHUNK_HEIGHT + 2) * (CHUNK_DEPTH + 1)

// VFIELD_SIZE / 6
#define MAX_VFIELD_LOAD_LOCAL_ID 450


float trilinear_interpolate(float p[8], float x, float y, float z) {
    return p[0] * (1 - x) * (1 - y) * (1 - z) +
           p[1] * x * (1 - y) * (1 - z) + 
           p[2] * (1 - x) * y * (1 - z) + 
           p[3] * (1 - x) * (1 - y) * z +
           p[4] * x * (1 - y) * z + 
           p[5] * (1 - x) * y * z + 
           p[6] * x * y * (1 - z) + 
           p[7] * x * y * z;
}

int flatten_index(int i, int j, int k, int isize, int jsize) {
    return i + isize * (j + jsize * k);
}

void fill_interpolation_data(__local float *vfield, 
                             int3 voffset, int vwidth, int vheight,
                             float points[8]) {

    points[0] = vfield[flatten_index(voffset.x,     voffset.y,     voffset.z,     vwidth, vheight)];
    points[1] = vfield[flatten_index(voffset.x + 1, voffset.y,     voffset.z,     vwidth, vheight)];
    points[2] = vfield[flatten_index(voffset.x,     voffset.y + 1, voffset.z,     vwidth, vheight)];
    points[3] = vfield[flatten_index(voffset.x,     voffset.y,     voffset.z + 1, vwidth, vheight)];
    points[4] = vfield[flatten_index(voffset.x + 1, voffset.y,     voffset.z + 1, vwidth, vheight)];
    points[5] = vfield[flatten_index(voffset.x,     voffset.y + 1, voffset.z + 1, vwidth, vheight)];
    points[6] = vfield[flatten_index(voffset.x + 1, voffset.y + 1, voffset.z,     vwidth, vheight)];
    points[7] = vfield[flatten_index(voffset.x + 1, voffset.y + 1, voffset.z + 1, vwidth, vheight)];
}

float interpolate_U(float3 pos, float dx, float invdx, __local float *ufield) {

    pos.y -= 0.5*dx;
    pos.z -= 0.5*dx;

    int3 index = (int3)(floor(pos.x * invdx),
                        floor(pos.y * invdx),
                        floor(pos.z * invdx));

    float3 index_offset = (float3)(index.x * dx,
                                   index.y * dx,
                                   index.z * dx);

    float3 interp_pos = invdx * (pos - index_offset);

    int3 vfield_index_offset = (int3)(index.x + 0,
                                      index.y + 1,
                                      index.z + 1);

    float points[8];
    int vwidth = CHUNK_WIDTH + 1;
    int vheight = CHUNK_HEIGHT + 2;

    fill_interpolation_data(ufield, vfield_index_offset, vwidth, vheight, points);

    return trilinear_interpolate(points, interp_pos.x,
                                         interp_pos.y,
                                         interp_pos.z);
}

float interpolate_V(float3 pos, float dx, float invdx, __local float *vfield) {

    pos.x -= 0.5*dx;
    pos.z -= 0.5*dx;

    int3 index = (int3)(floor(pos.x * invdx),
                        floor(pos.y * invdx),
                        floor(pos.z * invdx));

    float3 index_offset = (float3)(index.x * dx,
                                   index.y * dx,
                                   index.z * dx);

    float3 interp_pos = invdx * (pos - index_offset);

    int3 vfield_index_offset = (int3)(index.x + 1,
                                      index.y + 0,
                                      index.z + 1);

    float points[8];
    int vwidth = CHUNK_WIDTH + 2;
    int vheight = CHUNK_HEIGHT + 1;

    fill_interpolation_data(vfield, vfield_index_offset, vwidth, vheight, points);

    return trilinear_interpolate(points, interp_pos.x,
                                        interp_pos.y,
                                        interp_pos.z);
}

float interpolate_W(float3 pos, float dx, float invdx, __local float *wfield) {

    pos.x -= 0.5*dx;
    pos.y -= 0.5*dx;

    int3 index = (int3)(floor(pos.x * invdx),
                        floor(pos.y * invdx),
                        floor(pos.z * invdx));

    float3 index_offset = (float3)(index.x * dx,
                                   index.y * dx,
                                   index.z * dx);

    int3 vfield_index_offset = (int3)(index.x + 1,
                                      index.y + 1,
                                      index.z + 0);

    float3 interp_pos = invdx * (pos - index_offset);

    float points[8];
    int vwidth = CHUNK_WIDTH + 2;
    int vheight = CHUNK_HEIGHT + 2;

    fill_interpolation_data(wfield, vfield_index_offset, vwidth, vheight, points);

    return trilinear_interpolate(points, interp_pos.x,
                                         interp_pos.y,
                                         interp_pos.z);
}

__kernel void trilinear_interpolate_kernel(__global float *particles,
                                           __global float *vfield_data,
                                           __global int *chunk_offsets,
                                           __local  float *vfield,
                                           float dx) {

    size_t tid = get_global_id(0);
	size_t lid = get_local_id(0);
	size_t gid = tid / get_local_size(0);

    // Load fvield_data into local memory
    if (lid < MAX_VFIELD_LOAD_LOCAL_ID) {
        int local_offset = 6*lid;
        int vfield_data_offset = gid * VFIELD_SIZE + local_offset;

        vfield[local_offset + 0] = vfield_data[vfield_data_offset + 0];
        vfield[local_offset + 1] = vfield_data[vfield_data_offset + 1];
        vfield[local_offset + 2] = vfield_data[vfield_data_offset + 2];
        vfield[local_offset + 3] = vfield_data[vfield_data_offset + 3];
        vfield[local_offset + 4] = vfield_data[vfield_data_offset + 4];
        vfield[local_offset + 5] = vfield_data[vfield_data_offset + 5];
    }

    barrier(CLK_LOCAL_MEM_FENCE);
    
    float3 pos = (float3)(particles[3*tid + 0], 
                          particles[3*tid + 1], 
                          particles[3*tid + 2]);

    int3 chunk_offset = (int3)(chunk_offsets[3*gid + 0],
                               chunk_offsets[3*gid + 1],
                               chunk_offsets[3*gid + 2]);

    int3 index_offset = (int3)(chunk_offset.x * CHUNK_WIDTH,
                               chunk_offset.y * CHUNK_HEIGHT,
                               chunk_offset.z * CHUNK_DEPTH);

    float3 pos_offset = (float3)(index_offset.x * dx,
                                 index_offset.y * dx,
                                 index_offset.z * dx);

    float3 local_pos = pos - pos_offset;

    float invdx = 1.0 / dx;
    float result1 = interpolate_U(local_pos, dx, invdx, &(vfield[U_OFFSET]));
    float result2 = interpolate_V(local_pos, dx, invdx, &(vfield[V_OFFSET]));
    float result3 = interpolate_W(local_pos, dx, invdx, &(vfield[W_OFFSET]));

	particles[3*tid] = result1;
	particles[3*tid + 1] = result2;
	particles[3*tid + 2] = result3;
}