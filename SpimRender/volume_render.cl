/*
 * Copyright 1993-2010 NVIDIA Corporation.  All rights reserved.
 *
 * Please refer to the NVIDIA end user license agreement (EULA) associated
 * with this source code for terms and conditions that govern your use of
 * this software. Any use, reproduction, disclosure, or distribution of
 * this software and related documentation outside the terms of the EULA
 * is strictly prohibited.
 *
 */

#define maxSteps 500
#define tstep 0.01f

// intersect ray with a box
// http://www.siggraph.org/education/materials/HyperGraph/raytrace/rtinter3.htm

int intersectBox(float4 r_o, float4 r_d, float4 boxmin, float4 boxmax, float *tnear, float *tfar)
{
    // compute intersection of ray with all six bbox planes
    float4 invR = (float4)(1.0f,1.0f,1.0f,1.0f) / r_d;
    float4 tbot = invR * (boxmin - r_o);
    float4 ttop = invR * (boxmax - r_o);

    // re-order intersections to find smallest and largest on each axis
    float4 tmin = min(ttop, tbot);
    float4 tmax = max(ttop, tbot);

    // find the largest tmin and the smallest tmax
    float largest_tmin = max(max(tmin.x, tmin.y), max(tmin.x, tmin.z));
    float smallest_tmax = min(min(tmax.x, tmax.y), min(tmax.x, tmax.z));

	*tnear = largest_tmin;
	*tfar = smallest_tmax;

	return smallest_tmax > largest_tmin;
}


// int intersectBox2(float4 x0, float4 xd, float4 boxmin, float4 boxmax, float *tnear, float *tfar)
// {

  
//   float eps = .0001f;
//   // compute intersection of ray with all six bbox planes
//   float4 tmp = (xd - boxmin * xd.w);

//   if (fabs(tmp.x)<eps)
//   	tmp.x = eps;
//   if (fabs(tmp.y)<eps)
//   	tmp.y = eps;
//   if (fabs(tmp.z)<eps)
//   	tmp.z = eps;
//   if (fabs(tmp.w)<eps)
//   	tmp.w = eps;
	  
//   float4 tbot = (boxmin*x0.w - x0);// /tmp;


//   tmp = (xd - boxmax * xd.w) ;

//   if (fabs(tmp.x)<eps)
//   	tmp.x = eps;
//   if (fabs(tmp.y)<eps)
//   	tmp.y = eps;
//   if (fabs(tmp.z)<eps)
//   	tmp.z = eps;
//   if (fabs(tmp.w)<eps)
//   	tmp.w = eps;

//   float4 ttop = (boxmax*x0.w - x0)/tmp;

//   // re-order intersections to find smallest and largest on each axis
//   float4 tmin = min(ttop, tbot);
//   float4 tmax = max(ttop, tbot);

//   // find the largest tmin and the smallest tmax
//   float largest_tmin = max(max(tmin.x, tmin.y), max(tmin.x, tmin.z));
//   float smallest_tmax = min(min(tmax.x, tmax.y), min(tmax.x, tmax.z));

//   *tnear = largest_tmin;
//   *tfar = smallest_tmax;

//   return smallest_tmax > largest_tmin;
// }


uint rgbaFloatToInt(float4 rgba)
{
  rgba.x = clamp(rgba.x,0.0f,1.0f);  
  rgba.y = clamp(rgba.y,0.0f,1.0f);  
  rgba.z = clamp(rgba.z,0.0f,1.0f);  
  rgba.w = clamp(rgba.w,0.0f,1.0f);  
  return ((uint)(rgba.w*255.0f)<<24) | ((uint)(rgba.z*255.0f)<<16) | ((uint)(rgba.y*255.0f)<<8) | (uint)(rgba.x*255.0f);
}


__kernel void
max_project(__global short *d_output, 
         uint Nx, uint Ny,
	 __constant float* invM,
	 const bool isPerspective,
	 __read_only image3d_t volume)
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_LINEAR ;

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  float4 boxMin = (float4)(-1.0f, -1.0f, -1.0f,-1.0f);
  float4 boxMax = (float4)(1.0f, 1.0f, 1.0f,1.0f);

  // calculate eye ray in world space
  float4 orig;
  float4 direc;
  float4 temp;

  if (isPerspective)
	temp = (float4)(0, 0, .0f,1.0f);
  else
	temp = (float4)(u, v, .0f,1.0f);

  orig.x = dot(temp, ((float4)(invM[0],invM[1],invM[2],invM[3])));
  orig.y = dot(temp, ((float4)(invM[4],invM[5],invM[6],invM[7])));
  orig.z = dot(temp, ((float4)(invM[8],invM[9],invM[10],invM[11])));
  orig.w = dot(temp, ((float4)(invM[12],invM[13],invM[14],invM[15])));

  orig *= 1.f/orig.w;

  if (isPerspective)
	temp = normalize(((float4)(u, v, -2.0f,0.0f)));
  else
	temp = normalize(((float4)(0, 0, -1.0f,0.0f)));

  direc.x = dot(temp, ((float4)(invM[0],invM[1],invM[2],invM[3])));
  direc.y = dot(temp, ((float4)(invM[4],invM[5],invM[6],invM[7])));
  direc.z = dot(temp, ((float4)(invM[8],invM[9],invM[10],invM[11])));
  direc.w = 0.0f;

  // find intersection with box
  float tnear, tfar;
  int hit = intersectBox(orig,direc, boxMin, boxMax, &tnear, &tfar);
  if (!hit) {
  	if ((x < Nx) && (y < Ny)) {
  	  d_output[x+Nx*y] = 0.f;
  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  uint colVal = 0;
  
  float t = tfar;

  float4 pos;
  
  for(uint i=0; i<maxSteps; i++) {		
  	pos = orig + t*direc;


	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture        
  	uint newVal = read_imageui(volume, volumeSampler, pos).x;

  	colVal = max(colVal, newVal);

  	t -= tstep;
  	if (t < tnear) break;
  }

  if ((x < Nx) && (y < Ny)) {

	d_output[x+Nx*y] = colVal;

  }

}

