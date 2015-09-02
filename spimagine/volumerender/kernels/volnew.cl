/*

  Volume ray casting kernel
  
  adapted from the Nvidia sdk sample
  http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/website/OpenCL/html/samples.html
 

  mweigert@mpi-cbg.de
 */


#include<utils.cl>

#define read_image(volume,sampler, pos,isShortType) (isShortType?1.f*read_imageui(volume, sampler, pos).x:read_imagef(volume, sampler, pos).x)


__kernel void
max_project_part_float(__global float *d_output, __global float *d_alpha_output, 
				 uint Nx, uint Ny,
				 float boxMin_x,
				 float boxMax_x,
				 float boxMin_y,
				 float boxMax_y,
				 float boxMin_z,
				 float boxMax_z,
				 float minVal,
				 float maxVal,
				 float gamma,
				 float alpha_pow,
				 int numParts,
				 int currentPart,
				 __constant float* invP,
				 __constant float* invM,
				 __read_only image3d_t volume
				 )
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

  // dt = tstep;


  float colVal = 0;
  float alphaVal = 0;
  
  float dt = (tfar-tnear)/maxSteps*numParts;
  float t0 = tnear + dt*currentPart/numParts;


  //  dither the original
  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  orig += dt*random(entropy+x,entropy+y)*direc;

  float4 delta_pos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + t0*direc);

  uint i;

  float cumsum = 1;
  float newVal;
  int iMax = 0;
  
  for(i=0; i<=maxSteps/numParts; i++) {
	// colVal = max(colVal, read_imagef(volume, volumeSampler, pos+i*delta_pos).x);
	newVal = read_imagef(volume, volumeSampler, pos+i*delta_pos).x;
	newVal = (maxVal == 0)?newVal:(newVal-minVal)/(maxVal-minVal);

	// colVal = max(colVal,cumsum*newVal);
	iMax = (cumsum*newVal)>colVal?i:iMax;

	colVal = (cumsum*newVal)>colVal?cumsum*newVal:colVal;
	
	cumsum *= (1.f-.1f*alpha_pow*newVal);

  }

  alphaVal = colVal;
  
  colVal = pow(colVal,gamma);	

  colVal = clamp(colVal,0.f,1.f);

  //some shading

  pos = pos + iMax*delta_pos;



  float4 normal;
  float4 reflect;
  float h = 0.01;
  int isShortType = 0;
  
  // robust 2nd order
  normal.x = 2.f*read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
  	2.f*read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType)+
	read_image(volume,volumeSampler,pos+(float4)(2.f*h,0,0,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(-2.f*h,0,0,0), isShortType);

  normal.y = 2.f*read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
  	2.f*read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType)+
	read_image(volume,volumeSampler,pos+(float4)(0,2.f*h,0,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,-2.f*h,0,0), isShortType);

  normal.z = read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType)+
	read_image(volume,volumeSampler,pos+(float4)(0,0,2.f*h,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,0,-2.f*h,0), isShortType);

  normal.w = 0;

  //flip normal if we are comming from values greater than isoVal... 
  // normal = (1.f-2.f)*normalize(normal);

  float4 light = (float4)(2.f,-1.f,-2.f,0.f);

  reflect = 2.f*dot(light,normal)*normal-light;

  float diffuse = fmax(0.f,dot(light,normal));
  float specular = pow(fmax(0.f,dot(normalize(reflect),normalize(direc))),10.f);

  float c_ambient = .3f;
  float c_diffuse = .4f;
  float c_specular = .3f;

	
  colVal += .8*(c_ambient+c_diffuse*diffuse + (diffuse>0)*c_specular*specular);

  if ((x==400) &&(y==400))
	printf("\nkernel: %d %.4f \n",iMax,colVal);

  // colVal = (c_ambient+c_diffuse*diffuse + (diffuse>0)*c_specular*specular);


  // colVal = iMax/maxSteps;
	
  alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;

  
  if ((x < Nx) && (y < Ny)){
	if (currentPart==0){
	  d_output[x+Nx*y] = colVal;
	  d_alpha_output[x+Nx*y] = alphaVal;
	}
	else{
	  d_output[x+Nx*y] = max(colVal,d_output[x+Nx*y]);
	  d_alpha_output[x+Nx*y] = max(alphaVal,d_alpha_output[x+Nx*y]);
	}
	
  }


}


