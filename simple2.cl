
#define maxSteps 500
#define tstep 0.02f

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

uint rgbaFloatToInt(float4 rgba)
{
    rgba.x = clamp(rgba.x,0.0f,1.0f);  
    rgba.y = clamp(rgba.y,0.0f,1.0f);  
    rgba.z = clamp(rgba.z,0.0f,1.0f);  
    rgba.w = clamp(rgba.w,0.0f,1.0f);  
    return ((uint)(rgba.w*255.0f)<<24) | ((uint)(rgba.z*255.0f)<<16) | ((uint)(rgba.y*255.0f)<<8) | (uint)(rgba.x*255.0f);
}

__kernel void
d_render(__global float *d_output, 
         uint Nx, uint Ny,
         float density, float gamma,
         float transferOffset, float transferScale,
         __constant float* invViewMatrix
          ,__read_only image3d_t volume      )
{

  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_NEAREST ;

  const sampler_t transferFuncSampler  = CLK_NORMALIZED_COORDS_TRUE |	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_NEAREST ;


  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  //float tstep = 0.01f;
  float4 boxMin = (float4)(-1.0f, -1.0f, -1.0f,1.0f);
  float4 boxMax = (float4)(1.0f, 1.0f, 1.0f,1.0f);

  // calculate eye ray in world space
  float4 eyeRay_o;
  float4 eyeRay_d;

  eyeRay_o = (float4)(invViewMatrix[3], invViewMatrix[7], invViewMatrix[11], 1.0f);   

  float4 temp = normalize(((float4)(u, v, -2.0f,0.0f)));
  eyeRay_d.x = dot(temp, ((float4)(invViewMatrix[0],invViewMatrix[1],invViewMatrix[2],invViewMatrix[3])));
  eyeRay_d.y = dot(temp, ((float4)(invViewMatrix[4],invViewMatrix[5],invViewMatrix[6],invViewMatrix[7])));
  eyeRay_d.z = dot(temp, ((float4)(invViewMatrix[8],invViewMatrix[9],invViewMatrix[10],invViewMatrix[11])));
  eyeRay_d.w = 0.0f;

  // find intersection with box
  float tnear, tfar;
  int hit = intersectBox(eyeRay_o, eyeRay_d, boxMin, boxMax, &tnear, &tfar);
  if (!hit) {
  	if ((x < Nx) && (y < Ny)) {
  	  // write output color
  	  d_output[x+Nx*y] = 0.f;
  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  // march along ray from back to front, accumulating color
  float colVal = 0;
  
  float t = tfar;

  float4 sample;
  float4 pos;

  for(uint i=0; i<maxSteps; i++) {		
  	pos = eyeRay_o + eyeRay_d*t;
  	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture        
  	sample = read_imagef(volume, volumeSampler, pos);

	float newVal = clamp(1.f*sample.x/transferScale,0.f,1.f);

  	float a = newVal*density;

  	colVal = mix(colVal, newVal, a);

  	t -= tstep;
  	if (t < tnear) break;
  }

  colVal = powr(colVal,gamma);

  if ((x < Nx) && (y < Ny)) {

	d_output[x+Nx*y] = 30*transferScale*colVal;

  }

}


__kernel void
max_project(__global float *d_output, 
         uint Nx, uint Ny,
         __constant float* invViewMatrix
          ,__read_only image3d_t volume      )
{

  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_LINEAR ;

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  //float tstep = 0.01f;
  float4 boxMin = (float4)(-1.0f, -1.0f, -1.0f,-1.0f);
  float4 boxMax = (float4)(1.0f, 1.0f, 1.0f,1.0f);

  // calculate eye ray in world space
  float4 eyeRay_o;
  float4 eyeRay_d;

  eyeRay_o = (float4)(invViewMatrix[3], invViewMatrix[7], invViewMatrix[11], 1.0f);

  // eyeRay_o = (float4)(invViewMatrix[3], invViewMatrix[7], invViewMatrix[11], 1.0f);  

  float4 temp = normalize(((float4)(u, v, -2.0f,0.0f)));
  eyeRay_d.x = dot(temp, ((float4)(invViewMatrix[0],invViewMatrix[1],invViewMatrix[2],invViewMatrix[3])));
  eyeRay_d.y = dot(temp, ((float4)(invViewMatrix[4],invViewMatrix[5],invViewMatrix[6],invViewMatrix[7])));
  eyeRay_d.z = dot(temp, ((float4)(invViewMatrix[8],invViewMatrix[9],invViewMatrix[10],invViewMatrix[11])));
  eyeRay_d.w = 0.0f;

  // find intersection with box
  float tnear, tfar;
  int hit = intersectBox(eyeRay_o, eyeRay_d, boxMin, boxMax, &tnear, &tfar);
  if (!hit) {
  	if ((x < Nx) && (y < Ny)) {
  	  // write output color
  	  d_output[x+Nx*y] = 0.f;
  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  float colVal = 0;
  
  float t = tfar;

  float4 pos;
  
  for(uint i=0; i<maxSteps; i++) {		
  	pos = eyeRay_o + eyeRay_d*t;


	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture        
  	float newVal = read_imagef(volume, volumeSampler, pos).x;

  	colVal = max(colVal, newVal);

  	t -= tstep;
  	if (t < tnear) break;
  }

  if ((x < Nx) && (y < Ny)) {

	d_output[x+Nx*y] = colVal;

  }

}



__kernel void
max_projectShort(__global short *d_output, 
         uint Nx, uint Ny,
         __constant float* invViewMatrix
          ,__read_only image3d_t volume      )
{

  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_LINEAR ;

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  //float tstep = 0.01f;
  float4 boxMin = (float4)(-1.0f, -1.0f, -1.0f,-1.0f);
  float4 boxMax = (float4)(1.0f, 1.0f, 1.0f,1.0f);

  // calculate eye ray in world space
  float4 eyeRay_o;
  float4 eyeRay_d;

  eyeRay_o = (float4)(invViewMatrix[3], invViewMatrix[7], invViewMatrix[11], 1.0f);

  // eyeRay_o = (float4)(invViewMatrix[3], invViewMatrix[7], invViewMatrix[11], 1.0f);  

  float4 temp = normalize(((float4)(u, v, -2.0f,0.0f)));
  eyeRay_d.x = dot(temp, ((float4)(invViewMatrix[0],invViewMatrix[1],invViewMatrix[2],invViewMatrix[3])));
  eyeRay_d.y = dot(temp, ((float4)(invViewMatrix[4],invViewMatrix[5],invViewMatrix[6],invViewMatrix[7])));
  eyeRay_d.z = dot(temp, ((float4)(invViewMatrix[8],invViewMatrix[9],invViewMatrix[10],invViewMatrix[11])));
  eyeRay_d.w = 0.0f;

  // find intersection with box
  float tnear, tfar;
  int hit = intersectBox(eyeRay_o, eyeRay_d, boxMin, boxMax, &tnear, &tfar);
  if (!hit) {
  	if ((x < Nx) && (y < Ny)) {
  	  // write output color
  	  d_output[x+Nx*y] = 0.f;
  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  uint colVal = 0;
  
  float t = tfar;

  float4 pos;
  
  for(uint i=0; i<maxSteps; i++) {		
  	pos = eyeRay_o + eyeRay_d*t;


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


__kernel void foo( __global uint* output,
				   __read_only image3d_t input, const int Nx)
{

  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_FALSE |
	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_LINEAR ;



  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float pix = read_imagef(input,volumeSampler,(int4)(x,y,1,0)).x;

  uint i =(y * Nx) + x;
  

  output[i] = uint(pix);
  
}
