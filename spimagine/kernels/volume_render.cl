/*
  adapted from the Nvidia sdk sample
  http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/website/OpenCL/html/samples.html
 

  mweigert@mpi-cbg.de
 */


// #define maxSteps 700
// #define tstep 0.005f

// #define maxSteps 400
// #define tstep 0.01f

#define maxSteps 400/1
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

void printf4(const float4 v)
{
  printf("kernel: %.2f  %.2f  %.2f  %.2f\n",v.x,v.y,v.z,v.w); 
}

float4 mult(__constant float* M, float4 v){
  float4 res;
  res.x = dot(v, (float4)(M[0],M[1],M[2],M[3]));
  res.y = dot(v, (float4)(M[4],M[5],M[6],M[7]));
  res.z = dot(v, (float4)(M[8],M[9],M[10],M[11]));
  res.w = dot(v, (float4)(M[12],M[13],M[14],M[15]));
  return res;
}


__kernel void
max_project(__global float *d_output, 
			uint Nx, uint Ny,
			float boxMin_x,
			float boxMax_x,
			float boxMin_y,
			float boxMax_y,
			float boxMin_z,
			float boxMax_z,
			float maxVal,
			float gamma,				  
			__constant float* invP,
			__constant float* invM,
			__read_only image3d_t volume,
			int isShortType)
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |
	// CLK_FILTER_NEAREST ;
	CLK_FILTER_LINEAR ;

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  float4 boxMin = (float4)(boxMin_x,boxMin_y,boxMin_z,1.f);
  float4 boxMax = (float4)(boxMax_x,boxMax_y,boxMax_z,1.f);


  // calculate eye ray in world space
  float4 orig0, orig;
  float4 direc0, direc;
  float4 temp;
  float4 back,front;


  front = (float4)(u,v,-1,1);
  back = (float4)(u,v,1,1);
  

  orig0 = mult(invP,front);  
  orig0 *= 1.f/orig0.w;


  orig = mult(invM,orig0);
  orig *= 1.f/orig.w;
  
  temp = mult(invP,back);

  temp *= 1.f/temp.w;

  direc = mult(invM,normalize(temp-orig0));
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

  float colVal = 0;
  
  float t = tnear;

  float4 pos;
  uint i;
  for(i=0; i<maxSteps; i++) {		
  	pos = orig + t*direc;
	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture
	float newVal;
	if (isShortType)
	  newVal = 1.f*read_imageui(volume, volumeSampler, pos).x;
	else
	  newVal = read_imagef(volume, volumeSampler, pos).x;

	// newVal *= (1+2*exp(-10.f*i/maxSteps));
	// newVal *= exp(-2.f*i/maxSteps);
	
  	colVal = max(colVal, newVal);

  	t += tstep;
  	if (t > tfar) break;
  }

  colVal = (maxVal == 0)?colVal:colVal/maxVal;
  colVal = pow(colVal,gamma);


  if ((x < Nx) && (y < Ny))
	d_output[x+Nx*y] = colVal;

  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf4((float4)(tnear,tfar,0,0));

}


/*
  maximum projection with an exponential "surface" attenuation surface_tau
  equals normal max projection for surface_tau=0
 */
__kernel void
max_project_exp(__global float *d_output, 
			uint Nx, uint Ny,
			float boxMin_x,
			float boxMax_x,
			float boxMin_y,
			float boxMax_y,
			float boxMin_z,
			float boxMax_z,
			float maxVal,
			float gamma,
			float surface_tau,				  				
			__constant float* invP,
			__constant float* invM,
			__read_only image3d_t volume,
			int isShortType)
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |
	// CLK_FILTER_NEAREST ;
	CLK_FILTER_LINEAR ;

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  float4 boxMin = (float4)(boxMin_x,boxMin_y,boxMin_z,1.f);
  float4 boxMax = (float4)(boxMax_x,boxMax_y,boxMax_z,1.f);


  // calculate eye ray in world space
  float4 orig0, orig;
  float4 direc0, direc;
  float4 temp;
  float4 back,front;


  front = (float4)(u,v,-1,1);
  back = (float4)(u,v,1,1);
  

  orig0 = mult(invP,front);  
  orig0 *= 1.f/orig0.w;


  orig = mult(invM,orig0);
  orig *= 1.f/orig.w;
  
  temp = mult(invP,back);

  temp *= 1.f/temp.w;

  direc = mult(invM,normalize(temp-orig0));
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

  float colVal = 0;
  
  float t = tnear;

  float4 pos;
  uint i;
  for(i=0; i<maxSteps; i++) {		
  	pos = orig + t*direc;
	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture
	float newVal;
	if (isShortType)
	  newVal = 1.f*read_imageui(volume, volumeSampler, pos).x;
	else
	  newVal = read_imagef(volume, volumeSampler, pos).x;

	newVal *= exp(-surface_tau*i);
	
	// newVal *= (1+2*exp(-10.f*i/maxSteps));
	// newVal *= exp(-2.f*i/maxSteps);
	
  	colVal = max(colVal, newVal);

  	t += tstep;
  	if (t > tfar) break;
  }

  colVal = (maxVal == 0)?colVal:colVal/maxVal;
  colVal = pow(colVal,gamma);


  if ((x < Nx) && (y < Ny))
	d_output[x+Nx*y] = colVal;

  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf4((float4)(tnear,tfar,0,0));

}


__kernel void
max_project_test(__global float *d_output, __global float *d_alpha_output, 
				 uint Nx, uint Ny,
				 float boxMin_x,
				 float boxMax_x,
				 float boxMin_y,
				 float boxMax_y,
				 float boxMin_z,
				 float boxMax_z,
				 float maxVal,
				 float gamma,
				 float alpha_pow,

				 __constant float* invP,
				 __constant float* invM,
				 __read_only image3d_t volume,
				 int isShortType)
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |
	// CLK_FILTER_NEAREST ;
	CLK_FILTER_LINEAR ;
  
  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  float4 boxMin = (float4)(boxMin_x,boxMin_y,boxMin_z,1.f);
  float4 boxMax = (float4)(boxMax_x,boxMax_y,boxMax_z,1.f);


  // calculate eye ray in world space
  float4 orig0, orig;
  float4 direc0, direc;
  float4 temp;
  float4 back,front;


  front = (float4)(u,v,-1,1);
  back = (float4)(u,v,1,1);
  

  orig0 = mult(invP,front);  
  orig0 *= 1.f/orig0.w;


  orig = mult(invM,orig0);
  orig *= 1.f/orig.w;
  
  temp = mult(invP,back);

  temp *= 1.f/temp.w;

  direc = mult(invM,normalize(temp-orig0));
  direc.w = 0.0f;
  

  // find intersection with box
  float tnear, tfar;
  int hit = intersectBox(orig,direc, boxMin, boxMax, &tnear, &tfar);
  if (!hit) {
  	if ((x < Nx) && (y < Ny)) {
  	  d_output[x+Nx*y] = 0.f;
	  d_alpha_output[x+Nx*y] = 0.f;

  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  float colVal = 0;
  float alphaVal = 0;
  
  float t = tnear;

  float4 pos;
  uint i;


  for(i=0; i<maxSteps; i++) {		
  	pos = orig + t*direc;
	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture
	float newVal;
	if (isShortType)
	  newVal = 1.f*read_imageui(volume, volumeSampler, pos).x;
	else
	  newVal = read_imagef(volume, volumeSampler, pos).x;

	// if ((x==300 & y==300))
	//   printf("VAL:  %.4f  %.4f\n",newVal,alphaVal);
 	
	newVal = (maxVal == 0)?newVal:newVal/maxVal;


	colVal = max(colVal, newVal*(1-alphaVal));

	
	alphaVal += (1.f-alphaVal)*pow(newVal,alpha_pow);
	
  	t += tstep;
  	if ((t > tfar) || (alphaVal >=1.f))
	  break;
  }


  colVal = pow(colVal,gamma);

  colVal = clamp(colVal,0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);

  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = colVal;
	
  	d_alpha_output[x+Nx*y] = alphaVal*alphaVal+(1-alphaVal)*colVal;
	d_alpha_output[x+Nx*y] = colVal+(1.-colVal)*exp(-alpha_pow);

  }

  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf4((float4)(tnear,tfar,0,0));

}


