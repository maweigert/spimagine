/*
  adapted from the Nvidia sdk sample
  http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/website/OpenCL/html/samples.html
 

  mweigert@mpi-cbg.de
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




__kernel void
max_project_Short(__global short *d_output, 
			uint Nx, uint Ny,
			__constant float* invP,
			__constant float* invM,
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
  float4 orig0, orig;
  float4 direc0, direc;
  float4 temp;
  float4 back,front;


  front = (float4)(u,v,-1,1);
  back = (float4)(u,v,1,1);
  
  orig0.x = dot(front, ((float4)(invP[0],invP[1],invP[2],invP[3])));
  orig0.y = dot(front, ((float4)(invP[4],invP[5],invP[6],invP[7])));
  orig0.z = dot(front, ((float4)(invP[8],invP[9],invP[10],invP[11])));
  orig0.w = dot(front, ((float4)(invP[12],invP[13],invP[14],invP[15])));

  orig0 *= 1.f/orig0.w;
  
  orig.x = dot(orig0, ((float4)(invM[0],invM[1],invM[2],invM[3])));
  orig.y = dot(orig0, ((float4)(invM[4],invM[5],invM[6],invM[7])));
  orig.z = dot(orig0, ((float4)(invM[8],invM[9],invM[10],invM[11])));
  orig.w = dot(orig0, ((float4)(invM[12],invM[13],invM[14],invM[15])));

  orig *= 1.f/orig.w;
  
  direc0.x = dot(back, ((float4)(invP[0],invP[1],invP[2],invP[3])));
  direc0.y = dot(back, ((float4)(invP[4],invP[5],invP[6],invP[7])));
  direc0.z = dot(back, ((float4)(invP[8],invP[9],invP[10],invP[11])));
  direc0.w = dot(back, ((float4)(invP[12],invP[13],invP[14],invP[15])));

  direc0 *= 1.f/direc0.w;

  direc0 = normalize(direc0-orig0);

  direc.x = dot(direc0, ((float4)(invM[0],invM[1],invM[2],invM[3])));
  direc.y = dot(direc0, ((float4)(invM[4],invM[5],invM[6],invM[7])));
  direc.z = dot(direc0, ((float4)(invM[8],invM[9],invM[10],invM[11])));
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



__kernel void
max_project_Float(__global float *d_output, 
			uint Nx, uint Ny,
			__constant float* invP,
			__constant float* invM,
			__read_only image3d_t volume)
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_LINEAR ;

  uint xId = get_global_id(0);
  uint yId = get_global_id(1);

  uint workX = get_global_size(0);
  uint workY = get_global_size(1);

  uint strideX = Nx/workX;
  uint strideY = Ny/workY;

  // printf("%i\n",strideY);

  uint iX,iY;
  for (iX = 0; iX < strideX; ++iX){
  	for ( iY = 0; iY < strideY; ++iY){
    
  
  	  uint x = xId+iX*workX;
  	  uint y = yId+iY*workY;

		  
  	  float u = (x / (float) Nx)*2.0f-1.0f;
  	  float v = (y / (float) Ny)*2.0f-1.0f;

  	  float4 boxMin = (float4)(-1.0f, -1.0f, -1.0f,-1.0f);
  	  float4 boxMax = (float4)(1.0f, 1.0f, 1.0f,1.0f);

  	  // calculate eye ray in world space
  	  float4 orig0, orig;
  	  float4 direc0, direc;
  	  float4 temp;
  	  float4 back,front;


  	  front = (float4)(u,v,-1,1);
  	  back = (float4)(u,v,1,1);
  
  	  orig0.x = dot(front, ((float4)(invP[0],invP[1],invP[2],invP[3])));
  	  orig0.y = dot(front, ((float4)(invP[4],invP[5],invP[6],invP[7])));
  	  orig0.z = dot(front, ((float4)(invP[8],invP[9],invP[10],invP[11])));
  	  orig0.w = dot(front, ((float4)(invP[12],invP[13],invP[14],invP[15])));

  	  orig0 *= 1.f/orig0.w;
  
  	  orig.x = dot(orig0, ((float4)(invM[0],invM[1],invM[2],invM[3])));
  	  orig.y = dot(orig0, ((float4)(invM[4],invM[5],invM[6],invM[7])));
  	  orig.z = dot(orig0, ((float4)(invM[8],invM[9],invM[10],invM[11])));
  	  orig.w = dot(orig0, ((float4)(invM[12],invM[13],invM[14],invM[15])));

  	  orig *= 1.f/orig.w;
  
  	  direc0.x = dot(back, ((float4)(invP[0],invP[1],invP[2],invP[3])));
  	  direc0.y = dot(back, ((float4)(invP[4],invP[5],invP[6],invP[7])));
  	  direc0.z = dot(back, ((float4)(invP[8],invP[9],invP[10],invP[11])));
  	  direc0.w = dot(back, ((float4)(invP[12],invP[13],invP[14],invP[15])));

  	  direc0 *= 1.f/direc0.w;

  	  direc0 = normalize(direc0-orig0);

  	  direc.x = dot(direc0, ((float4)(invM[0],invM[1],invM[2],invM[3])));
  	  direc.y = dot(direc0, ((float4)(invM[4],invM[5],invM[6],invM[7])));
  	  direc.z = dot(direc0, ((float4)(invM[8],invM[9],invM[10],invM[11])));
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
  
  	  float t = tfar;

  	  float4 pos;
  
  	  for(uint i=0; i<maxSteps; i++) {		
  	  	pos = orig + t*direc;


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
  }
}

