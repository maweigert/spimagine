/*

  Volume ray casting kernel
  
  adapted from the Nvidia sdk sample
  http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/website/OpenCL/html/samples.html
 

  mweigert@mpi-cbg.de
 */


#include<utils.cl>


#define LOOPUNROLL 16


// the basic max_project ray casting
__kernel void
max_project_float(__global float *d_output, __global float *d_alpha_output, 
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
  float4  direc;
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
  // clamp to near plane
  if (tnear < 0.0f) tnear = 0.0f;  


  // the color values we want 
  float colVal = 0;
  float alphaVal = 0;

  const int reducedSteps = maxSteps/numParts;
  
  const float dt = fabs(tfar-tnear)/((reducedSteps/LOOPUNROLL)*LOOPUNROLL);

  //apply the shift if mulitpass
  
  orig += currentPart*dt*direc;

  //  dither the original
  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  // orig += dt*random(entropy+x,entropy+y)*direc;

  float4 delta_pos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);

  float newVal = 0.f;

  int maxInd = 0;
  
  if (alpha_pow==0){
  	for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	  for (int j = 0; j < LOOPUNROLL; ++j){
		newVal = read_imagef(volume, volumeSampler, pos).x;
		maxInd = newVal>colVal?i*LOOPUNROLL+j:maxInd;
		colVal = fmax(colVal,newVal);

		
  		// colVal = fmax(colVal,read_imagef(volume, volumeSampler, pos).x);
		pos += delta_pos;
  	  }
  	}
  	colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  	alphaVal = colVal;
  
  }
  else	{
  	for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	  for (int j = 0; j < LOOPUNROLL; ++j){
  		newVal = read_imagef(volume, volumeSampler, pos).x;
  		newVal = (newVal-minVal)/(maxVal-minVal);
  		colVal += (1.f-alphaVal)*newVal;
  		alphaVal += alpha_pow*(1.f-alphaVal)*newVal; 
  		pos += delta_pos;
  		if (alphaVal>=1.f)
  		  break;
  	  }
  	}
  } 

  
  colVal = clamp(pow(colVal,gamma),0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);



  // now phong shading
  pos = 0.5f *(1.f + orig + tnear*direc) +  delta_pos*maxInd;
  
  float4 light = (float4)(2,-1,-2,0);

  float c_diffuse = .5;
  float c_specular = .5;

  light = mult(invM,light);
  light = normalize(light);

  // the normal

  
  float4 normal;
  float4 reflect;
  float h = dt;

  h*= pow(gamma,2);

  
  const int isShortType = 0;
  // robust 2nd order
  normal.x = 2.f*read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
  	2.f*read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType)+
	read_image(volume,volumeSampler,pos+(float4)(2.f*h,0,0,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(-2.f*h,0,0,0), isShortType);

  normal.y = 2.f*read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
  	2.f*read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType)+
	read_image(volume,volumeSampler,pos+(float4)(0,2.f*h,0,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,-2.f*h,0,0), isShortType);

  normal.z = 2.f*read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
  	2.f*read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType)+
	read_image(volume,volumeSampler,pos+(float4)(0,0,2.f*h,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,0,-2.f*h,0), isShortType);

  normal.w = 0;

  normal *= 1./8./h;

  float gradFac = 1.-exp(-length(normal)/maxVal);

  if ((x==Nx/2-100) &&(y==Ny/2))
	printf("hello: %.10f  \n",length(normal)/maxVal);

  //flip normal if we are coming from values greater than isoVal... 
  // normal = (1.f-2*isGreater)*normalize(normal);


  normal = normalize(normal);

  reflect = 2*dot(light,normal)*normal-light;

  float diffuse = fmax(0.f,dot(light,normal));
  float specular = pow(fmax(0.f,dot(normalize(reflect),normalize(direc))),10);


  colVal *= (1.+ 0*gradFac*(c_diffuse*diffuse));

  // for depth test...
  alphaVal = tnear;


  if ((x < Nx) && (y < Ny)){
	if (currentPart==0){
	  d_output[x+Nx*y] = colVal;
	  d_alpha_output[x+Nx*y] = alphaVal;
	}
	else{
	  d_output[x+Nx*y] = fmax(colVal,d_output[x+Nx*y]);
	  d_alpha_output[x+Nx*y] = fmax(alphaVal,d_alpha_output[x+Nx*y]);
	}
	
  }


}


__kernel void
max_project_float2(__global float *d_output, __global float *d_alpha_output, 
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
  float4  direc;
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
  // clamp to near plane
  if (tnear < 0.0f) tnear = 0.0f;  


  // the color values we want 
  float colVal = 0;
  float alphaVal = 0;

  const int reducedSteps = maxSteps/numParts;
  
  const float dt = fabs(tfar-tnear)/(reducedSteps/LOOPUNROLL)*LOOPUNROLL;

  //apply the shift if mulitpass
  
  orig += currentPart*dt*direc;

  //  dither the original
  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  // orig += dt*random(entropy+x,entropy+y)*direc;

  float4 delta_pos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);


  for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	for (int j = 0; j < LOOPUNROLL; ++j){
  	  colVal = fmax(colVal,read_imagef(volume, volumeSampler, pos).x);
  	  pos += delta_pos;
  	}
  }

  colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  
  alphaVal = colVal;
  
  colVal = clamp(pow(colVal,gamma),0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);


  if ((x==200) &&(y==200))
	printf("hello from here!  \n");

  
  // for depth test...
  alphaVal = tnear;


  if ((x < Nx) && (y < Ny)){
	if (currentPart==0){
	  d_output[x+Nx*y] = colVal;
	  d_alpha_output[x+Nx*y] = alphaVal;
	}
	else{
	  d_output[x+Nx*y] = fmax(colVal,d_output[x+Nx*y]);
	  d_alpha_output[x+Nx*y] = fmax(alphaVal,d_alpha_output[x+Nx*y]);
	}
	
  }


}


__kernel void
max_project_short(__global float *d_output, __global float *d_alpha_output, 
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
  float4  direc;
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
  // clamp to near plane
  if (tnear < 0.0f) tnear = 0.0f;  


  // the color values we want 
  float colVal = 0;
  float alphaVal = 0;

  const int reducedSteps = maxSteps/numParts;
  
  const float dt = fabs(tfar-tnear)/((reducedSteps/LOOPUNROLL)*LOOPUNROLL);

  //apply the shift if mulitpass
  
  orig += currentPart*dt*direc;

  //  dither the original
  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  // orig += dt*random(entropy+x,entropy+y)*direc;

  float4 delta_pos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);

  float newval = 0.f;

  if (alpha_pow==0){
  	for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	  for (int j = 0; j < LOOPUNROLL; ++j){
  		colVal = fmax(colVal,1.f*read_imageui(volume, volumeSampler, pos).x);
		pos += delta_pos;
  	  }
  	}
  	colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  	alphaVal = colVal;
  
  }
  else	{
  	for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	  for (int j = 0; j < LOOPUNROLL; ++j){
  		newval = 1.f*read_imageui(volume, volumeSampler, pos).x;
  		newval = (newval-minVal)/(maxVal-minVal);
  		colVal += (1.f-alphaVal)*newval;
  		alphaVal += alpha_pow*(1.f-alphaVal)*newval; 
  		pos += delta_pos;
  		if (alphaVal>=1.f)
  		  break;
  	  }
  	}
  } 

  if ((x==250) &&(y==250))
	printf("kern: %.20f\n",pos.z);
  
  
  colVal = clamp(pow(colVal,gamma),0.f,1.f);

  // alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;


  if ((x < Nx) && (y < Ny)){
	if (currentPart==0){
	  d_output[x+Nx*y] = colVal;
	  d_alpha_output[x+Nx*y] = alphaVal;
	}
	else{
	  d_output[x+Nx*y] = fmax(colVal,d_output[x+Nx*y]);
	  d_alpha_output[x+Nx*y] = fmax(alphaVal,d_alpha_output[x+Nx*y]);
	}
	
  }


}
