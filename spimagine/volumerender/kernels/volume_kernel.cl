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
max_project_float(__global float *d_output,
                  __global float *d_alpha_output,
                  __global float *d_depth_output,
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
                  __QUALIFIER_CONSTANT float* invP,
                  __QUALIFIER_CONSTANT float* invM,
                  __read_only image3d_t volume
				 )
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE | SAMPLER_FILTER;

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
	  d_alpha_output[x+Nx*y] = -1.f;
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
  // uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
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
    float cumsum = 1.f;
  	for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	  for (int j = 0; j < LOOPUNROLL; ++j){
  		newVal = read_imagef(volume, volumeSampler, pos).x;
  		newVal = (maxVal == 0)?newVal:(newVal-minVal)/(maxVal-minVal);
  		maxInd = cumsum*newVal>colVal?i*LOOPUNROLL+j:maxInd;
  		colVal = fmax(colVal,cumsum*newVal);
  		//colVal = fmax(colVal,newVal);

  		cumsum  *= (1.f-alpha_pow*alpha_pow*clamp(newVal,0.f,1.f));
  		pos += delta_pos;
  		if (cumsum<=0.01f)
  		  break;

          //if((x==400)&&(y==400))
          //   printf("cumsum (it %d): %.5f\n",j,alpha_pow);


  	  }
  	}

  }



  colVal = clamp(pow(colVal,gamma),0.f,1.f);

  //alphaVal = clamp(colVal,0.f,1.f);
  // for depth test...
  //alphaVal = tnear;

  alphaVal = 1.f;



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
max_project_short(__global float *d_output,
                __global float *d_alpha_output,
                  __global float *d_depth_output,
                  uint Nx,
                  uint Ny,
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
                  __QUALIFIER_CONSTANT float* invP,
                  __QUALIFIER_CONSTANT float* invM,
                  __read_only image3d_t volume
                  )

{

  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE | SAMPLER_FILTER;

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
  // uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  // orig += dt*random(entropy+x,entropy+y)*direc;

  float4 delta_pos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);

  float newVal = 0.f;



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
  	float cumsum = 1.f;
  	for(int i=0; i<=reducedSteps/LOOPUNROLL; ++i){
  	  for (int j = 0; j < LOOPUNROLL; ++j){
  		newVal = 1.f*read_imageui(volume, volumeSampler, pos).x;
  		newVal = (maxVal == 0)?newVal:(newVal-minVal)/(maxVal-minVal);
  		colVal = fmax(colVal,cumsum*newVal);
        //colVal = fmax(colVal,newVal);

  		cumsum  *= (1.f-.1f*alpha_pow*alpha_pow*newVal);
  		pos += delta_pos;
  		if (cumsum<=0.01f)
  		  break;
      }
  	}
  }

 // if ((x==250) &&(y==250))
//	printf("kern: %.20f\n",pos.z);


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
