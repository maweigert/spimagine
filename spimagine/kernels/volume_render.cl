/*
  adapted from the Nvidia sdk sample
  http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/website/OpenCL/html/samples.html
 

  mweigert@mpi-cbg.de
 */


#define maxSteps 200
#define tstep 0.01f



inline
float random(uint x, uint y)
{   
    uint a = 4421 +(1+x)*(1+y) +x +y;

    for(int i=0; i < 10; i++)
    {
        a = (1664525 * a + 1013904223) % 79197919;
    }

    float rnd = (a*1.0f)/(79197919);

    // return .5f*(rnd-.5f);
	return -rnd;

}


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

// void printf4(const float4 v)
// {
//   printf("kernel: %.2f  %.2f  %.2f  %.2f\n",v.x,v.y,v.z,v.w); 
// }

float4 mult(__constant float* M, float4 v){
  float4 res;
  res.x = dot(v, (float4)(M[0],M[1],M[2],M[3]));
  res.y = dot(v, (float4)(M[4],M[5],M[6],M[7]));
  res.z = dot(v, (float4)(M[8],M[9],M[10],M[11]));
  res.w = dot(v, (float4)(M[12],M[13],M[14],M[15]));
  return res;
}


__kernel void
max_project_old(__global float *d_output, 
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


__kernel void
max_project(__global float *d_output, __global float *d_alpha_output, 
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

  float dt = (tfar-tnear)/maxSteps;

  float tmax = tnear;


  //dither the original

  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  orig += dt*random(entropy+x,entropy+y)*direc;
	
  // dt = tstep;
  
  for(i=0; i<=maxSteps; i++) {		
  	pos = orig + t*direc;
	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

  	// read from 3D texture
	float newVal;
	if (isShortType)
	  newVal = 1.f*read_imageui(volume, volumeSampler, pos).x;
	else
	  newVal = read_imagef(volume, volumeSampler, pos).x;


	// // this is still slow as hell...

	// newVal = (maxVal == 0)?newVal:newVal/maxVal;
	// colVal = max(colVal, newVal*(1-alphaVal));

  	// alphaVal += (1.f-alphaVal)*pow(newVal,alpha_pow);

	// // this ist still slow as hell...
	// alphaVal += maxSteps*dt*(1.f-alphaVal)*pow(newVal,alpha_pow);

	if (alpha_pow>.02)
	  newVal *= 1./(1+alpha_pow*i);

	  
	colVal = max(colVal, newVal);

	t += dt;

  	// if ((t > tfar) || (alphaVal >=1.f))
	//   break;

	// if (t > tfar)
	//   break;

  }

  colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  
  alphaVal = colVal;

  
  // alphaVal = .3f*(tfar-tnear);


  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("start:  %.2f %.2f %.2f %.2f\n",tnear,tfar,tmax,alphaVal);

  colVal = pow(colVal,gamma);	

  colVal = clamp(colVal,0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;


  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("%.5f %.5f\n",tnear,tfar);
  

  
  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = colVal;
	
  	// d_alpha_output[x+Nx*y] = alphaVal*alphaVal+(1-alphaVal)*colVal;
	// d_alpha_output[x+Nx*y] = colVal+(1.-colVal)*exp(-alpha_pow);
	d_alpha_output[x+Nx*y] = alphaVal;
  }


}

#define read_image(volume,sampler, pos,isShortType) (isShortType?1.f*read_imageui(volume, sampler, pos).x:read_imagef(volume, sampler, pos).x)




__kernel void iso_surface(
						  __global float *d_output,
						  __global float *d_alpha_output, 
						  uint Nx, uint Ny,
						  float boxMin_x,
						  float boxMax_x,
						  float boxMin_y,
						  float boxMax_y,
						  float boxMin_z,
						  float boxMax_z,
						  float isoVal,
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
	  d_alpha_output[x+Nx*y] = 0.f;
  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  float colVal = 0;
  float alphaVal = 0;

  float4 light = (float4)(2,-1,-2,0);

  float c_ambient = .3;
  float c_diffuse = .4;
  float c_specular = .3;


  // c_ambient = 0.;
  // c_diffuse = 1.;
  // c_specular = .0;
  

  light = mult(invM,light);
  light = normalize(light);
  
  float t = tnear;




  float4 pos = orig + tnear*direc;;
  uint i;

  
  float dt = (tfar-tnear)/maxSteps;
  
  float newVal = read_image(volume, volumeSampler, pos*0.5f+0.5f, isShortType);
  bool isGreater = newVal>isoVal;
  bool hitIso = false;

  
  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("start:  %.2f %.2f %d\n",newVal,isoVal,isGreater);

  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  // orig += dt*random(entropy+x,entropy+y)*direc;


  
  for(i=1; i<maxSteps; i++) {		
  	pos = orig + (t+dt*i)*direc;
	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

	// newVal = read_imagef(volume, volumeSampler, pos).x;
	newVal = read_image(volume, volumeSampler, pos, isShortType);

	// if ((x == Nx/2) && (y == Ny/2))
	//   printf("%.3f %d %d %d \n",newVal,i,newVal>isoVal,hitIso);
	
	if ((newVal>isoVal) != isGreater){
	  hitIso = true;
	  break;
	}
  }

  // find real intersection point
  // still broken
  // float oldVal = read_image(volume, volumeSampler, .5f*(orig + (t+dt*(i-1))*direc)+.5f, isShortType);
  // float lam = (newVal - isoVal)/(newVal-oldVal);
  // pos = .5f*(orig + (t+dt*((i-1)*(1-lam)+i*lam) )*direc)+.5f;


  // now phong shading

  // the normal

  
  float4 normal;
  float4 reflect;
  float h = dt;

  h*= pow(gamma,2);

  
  // normal.x = read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
  // 	read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType);
  // normal.y = read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
  // 	read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType);
  // normal.z = read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
  // 	read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType);

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
  normal = (1.f-2*isGreater)*normalize(normal);

  reflect = 2*dot(light,normal)*normal-light;

  float diffuse = fmax(0.f,dot(light,normal));
  float specular = pow(fmax(0.f,dot(normalize(reflect),normalize(direc))),10);
  
  // phong shading
  if (hitIso){
	colVal = c_ambient
	  + c_diffuse*diffuse
	  + (diffuse>0)*c_specular*specular;
	
  }

  // for depth test...
  alphaVal = tnear;

  
  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = colVal;
	d_alpha_output[x+Nx*y] = alphaVal;

  }

}





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
			__constant float* invP,
			__constant float* invM,
			__read_only image3d_t volume)
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

  // if (x==300 && y == 300)
  // 	printf("%.2f  %.2f %.2f  %.2f \n",invP[0],invP[1],invP[2],invP[3]);

  
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
  float dt = (tfar-tnear)/maxSteps;


  
  //dither the original
  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  orig += dt*random(entropy+x,entropy+y)*direc;

  float4 dpos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);

  uint i;

  for(i=0; i<=maxSteps; i++) {
	colVal = max(colVal, read_imagef(volume, volumeSampler, pos+i*dpos).x);
  }
  
  colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  
  alphaVal = colVal;
  
  colVal = pow(colVal,gamma);	

  colVal = clamp(colVal,0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;

  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = colVal;	
	d_alpha_output[x+Nx*y] = alphaVal;
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
			__constant float* invP,
			__constant float* invM,
			__read_only image3d_t volume)
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
  float dt = (tfar-tnear)/maxSteps;


  //dither the original
  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  orig += dt*random(entropy+x,entropy+y)*direc;

  float4 dpos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);

  uint i;

  for(i=0; i<=maxSteps; i++) {
	colVal = max(colVal, 1.f*read_imageui(volume, volumeSampler, pos+i*dpos).x);
  }
  
  colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  
  alphaVal = colVal;
  
  colVal = pow(colVal,gamma);	

  colVal = clamp(colVal,0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;

  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = colVal;	
	d_alpha_output[x+Nx*y] = alphaVal;
  }
}


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
  
  for(i=0; i<=maxSteps/numParts; i++) {
	// colVal = max(colVal, read_imagef(volume, volumeSampler, pos+i*delta_pos).x);
	newVal = read_imagef(volume, volumeSampler, pos+i*delta_pos).x;
	newVal = (maxVal == 0)?newVal:(newVal-minVal)/(maxVal-minVal);
	colVal = max(colVal,cumsum*newVal);
	cumsum *= (1.f-.1f*alpha_pow*newVal);

  }

  // colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  
  alphaVal = colVal;

  
  colVal = pow(colVal,gamma);	

  colVal = clamp(colVal,0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;


  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("%.5f %.5f\n",tnear,tfar);
  

  
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
__kernel void
max_project_part_short(__global float *d_output, __global float *d_alpha_output, 
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

  float4 dpos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + t0*direc);

  uint i;

  float newVal;
  float cumsum = 1.f;

  for(i=0; i<=maxSteps/numParts; i++) {
	// colVal = max(colVal, 1.f*read_imageui(volume, volumeSampler, pos+i*dpos).x);
	newVal = 1.f*read_imageui(volume, volumeSampler, pos+i*dpos).x;
	newVal = (maxVal == 0)?newVal:(newVal-minVal)/(maxVal-minVal);
	colVal = max(colVal,cumsum*newVal);
	cumsum *= (1.f-.1f*alpha_pow*newVal);

	
  }

  // colVal = (maxVal == 0)?colVal:(colVal-minVal)/(maxVal-minVal);
  
  alphaVal = colVal;

  
  // alphaVal = .3f*(tfar-tnear);


  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("start:  %.2f %.2f %.2f %.2f\n",tnear,tfar,tmax,alphaVal);

  colVal = pow(colVal,gamma);	

  colVal = clamp(colVal,0.f,1.f);

  alphaVal = clamp(alphaVal,0.f,1.f);

  // for depth test...
  alphaVal = tnear;


  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("%.5f %.5f\n",tnear,tfar);
  

  
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


__kernel void iso_surface_new(
						  __global float *d_normals,
						  __global float *d_alpha,
						  uint Nx, uint Ny,
						  float boxMin_x,
						  float boxMax_x,
						  float boxMin_y,
						  float boxMax_y,
						  float boxMin_z,
						  float boxMax_z,
						  float isoVal,
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
  	  d_normals[0+3*x+3*Nx*y] = 0.f;
	  d_normals[1+3*x+3*Nx*y] = 0.f;
	  d_normals[2+3*x+3*Nx*y] = 0.f;
	  d_alpha[x+Nx*y] = 0.f;
  	}
  	return;
  }
  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  float t = tnear;

  float4 pos = orig + tnear*direc;;

  uint i;

  float dt = (tfar-tnear)/maxSteps;

  
  float newVal = read_image(volume, volumeSampler, pos*0.5f+0.5f, isShortType);
  bool isGreater = newVal>isoVal;
  bool hitIso = false;

  
  // if ((x == Nx/2) && (y == Ny/2))
  // 	printf("start:  %.2f %.2f %d\n",newVal,isoVal,isGreater);

  uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  // orig += dt*random(entropy+x,entropy+y)*direc;


  
  for(t=tnear; t<tfar; t+=dt) {		
  	pos = orig + t*direc;
	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

	newVal = read_image(volume, volumeSampler, pos, isShortType);

	if ((newVal>isoVal) != isGreater){
	  hitIso = true;
	  break;
	}
  }

  if (!hitIso) {
  	if ((x < Nx) && (y < Ny)) {
  	  d_normals[0+3*x+3*Nx*y] = 0.f;
	  d_normals[1+3*x+3*Nx*y] = 0.f;
	  d_normals[2+3*x+3*Nx*y] = 0.f;
	  d_alpha[x+Nx*y] = 0.f;   
  	}
  	return;
  }
  
  // the normal

  // if (x==300 &&y ==300)
  // 	printf("diffuse: %.4f \n",tnear);
  
  float4 normal;
  float h = dt;

  h*= pow(gamma,2);

  normal.x = read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType);
  normal.y = read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType);
  normal.z = read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
  	read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType);
 
  normal.w = 0;

  //flip normal if we are comming from values greater than isoVal... 
  normal = (1.f-2*isGreater)*normalize(normal);


  
  if ((x < Nx) && (y < Ny)){
	  d_normals[0+3*x+3*Nx*y] = normal.x;
	  d_normals[1+3*x+3*Nx*y] = normal.y;
	  d_normals[2+3*x+3*Nx*y] = normal.z;
	  d_alpha[x+Nx*y] = t;
  }

}


__kernel void blur_normals_x(__global float *d_input,
							 __global float *d_output,
							 int N)

{

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  uint Nx = get_global_size(0);
  uint Ny = get_global_size(1);
	
  float4 res = (float4)(0.f,0.f,0.f,0.f);
  float hsum = 0.f;

  float fac = -.1f/N/N;
  
  for (int i = -N; i <= N; ++i){
	float h = exp(fac*i*i);
	hsum += h;
	
	res.x += h*d_input[0+3*(x+i)+3*Nx*y];
	res.y += h*d_input[1+3*(x+i)+3*Nx*y];
	res.z += h*d_input[2+3*(x+i)+3*Nx*y];

  }

  // if (x==300 &&y ==300)
  // 	  printf("%.2f \n",hsum);


  res *= 1./hsum;

  //res = normalize(res);

  d_output[0+3*x+3*Nx*y] = res.x;
  d_output[1+3*x+3*Nx*y] = res.y;
  d_output[2+3*x+3*Nx*y] = res.z;  

}


__kernel void blur_normals_y(__global float *d_input,
							 __global float *d_output,
							 int N)

{

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  uint Nx = get_global_size(0);
  uint Ny = get_global_size(1);
	
  float4 res = (float4)(0.f,0.f,0.f,0.f);
  float hsum = 0.f;

  float fac = -.1f/N/N;
  
  for (int i = -N; i <= N; ++i){
	float h = exp(fac*i*i);
	hsum += h;
	
	res.x += h*d_input[0+3*x+3*Nx*(y+i)];
	res.y += h*d_input[1+3*x+3*Nx*(y+i)];
	res.z += h*d_input[2+3*x+3*Nx*(y+i)];

  }

  // if (x==300 &&y ==300)
  // 	  printf("%.2f \n",hsum);


  res *= 1./hsum;

  //res = normalize(res);

  d_output[0+3*x+3*Nx*y] = res.x;
  d_output[1+3*x+3*Nx*y] = res.y;
  d_output[2+3*x+3*Nx*y] = res.z;  

}



__kernel void iso_shading(__global float *d_normals,
						  __global float *d_alpha,
						  __constant float *invM,
						  __constant float *invP,
						  __global float *d_output)
{
  const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
	CLK_ADDRESS_CLAMP_TO_EDGE |
	// CLK_FILTER_NEAREST ;
	CLK_FILTER_LINEAR ;
  
  uint x = get_global_id(0);
  uint y = get_global_id(1);
  uint Nx = get_global_size(0);
  uint Ny = get_global_size(1);


  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;


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
  

  
  float4 normal;
  normal.x = d_normals[0+3*x+3*Nx*y];
  normal.y = d_normals[1+3*x+3*Nx*y];
  normal.z = d_normals[2+3*x+3*Nx*y];
  normal.w = 0.f;

  normal = normalize(normal);

  float4 reflect;


  float colVal = 0;
  float alphaVal = 0;

  float4 light = (float4)(2,-1,-2,0);

  float c_ambient = .3;
  float c_diffuse = .4;
  float c_specular = .3;


  light = mult(invM,light);
  light = normalize(light);


  reflect = 2*dot(light,normal)*normal-light;

  float diffuse = fmax(0.f,-dot(light,normal));
  float specular = pow(fmax(0.f,-dot(normalize(reflect),normalize(direc))),10);
  
  colVal = c_ambient
	+ c_diffuse*diffuse
	+ (diffuse>0)*c_specular*specular;
	
  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = (d_alpha[x+Nx*y]>0)?colVal:0.f;
  }


  // if (x==300 &&y ==300)
  // 	printf("diffuse: %.4f \n",dot(light,normal));


}

