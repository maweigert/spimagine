/*

  Iso surface rendering kernels

  mweigert@mpi-cbg.de
 */

#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable


#include<utils.cl>

#include<convolve_2d.cl>
#include<occlusion.cl>


__kernel void iso_surface(
						  __global float *d_output,
						  __global float *d_alpha_output,
						  __global float *d_depth_output,
						  __global float *d_normals_output,
						  uint Nx, uint Ny,
						  float boxMin_x,
						  float boxMax_x,
						  float boxMin_y,
						  float boxMax_y,
						  float boxMin_z,
						  float boxMax_z,
						  float isoVal,
						  float gamma,
						  __QUALIFIER_CONSTANT float* invP,
						  __QUALIFIER_CONSTANT float* invM,
						  __read_only image3d_t volume,
						  int isShortType)
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
  float4 direc;
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
	d_output[x+Nx*y] = 0.f;
	d_alpha_output[x+Nx*y] = 0.f;
	d_depth_output[x+Nx*y] = INFINITY;
	d_normals_output[3*x+3*Nx*y+0] = 0.f;
	d_normals_output[3*x+3*Nx*y+1] = 0.f;
	d_normals_output[3*x+3*Nx*y+2] = 0.f;
	return;
  }


  if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

  float colVal = 0;
  float alphaVal = 0;


  float dt = 1.f*(tfar-tnear)/(maxSteps-1.f);

  //uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
  //orig += dt*random(entropy+x,entropy+y)*direc;


  float4 delta_pos = .5f*dt*direc;
  float4 pos = 0.5f *(1.f + orig + tnear*direc);

  float newVal = read_imagef(volume, volumeSampler, pos).x;
  int isGreater = newVal>isoVal;
  int hitIso = 0;

  float t_hit = INFINITY;


  int i = 1;

  //search for the intersection
  for(i=1; i<maxSteps; i++) {
  	pos += delta_pos;
	t_hit = tnear +i*dt;

    //newVal = read_imagef(volume, volumeSampler, pos).x;
	newVal = read_image(volume, volumeSampler, pos, isShortType);


    if ((newVal>isoVal) != isGreater){
	  hitIso = 1;
	  
	  break;
	}
	
  }

  if (!hitIso){
  	  d_output[x+Nx*y] = 0.f;
  	  d_alpha_output[x+Nx*y] = 0.f;
  	  d_depth_output[x+Nx*y] = INFINITY;
  	  d_normals_output[3*x+3*Nx*y] = 0.f;
  	  d_normals_output[1+3*x+3*Nx*y] = 0.f;
  	  d_normals_output[2+3*x+3*Nx*y] = 0.f;
  	  return;
  }



  //if intersection found bisect, TODO!
  const int maxBisect = 10;
  hitIso = 0;

  float4 delta_pos2 = delta_pos/maxBisect;
  float dt2 = dt/maxBisect;

  pos = 0.5f *(1.f + orig + tnear*direc)+(i-1)*delta_pos;

  int j = 1;
  for(j=1; j<=maxBisect; j++) {
  	newVal = read_image(volume, volumeSampler, pos, isShortType);
    pos += delta_pos2;
	t_hit += dt2;
	if ((newVal>isoVal) != isGreater){
	  hitIso = 1;
	  break;
	}
  }

  // compute the normals and shading

  // phong shading
  float4 light = (float4)(2,-1,-2,0);
  float c_ambient = .3f;
  float c_diffuse = .4f;
  float c_specular = .3f;

  light = mult(invM,light);
  light = normalize(light);

  // the normal
  float4 normal;
  float4 reflect;
  float h = dt;

  h*= pow(gamma,2);

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

  colVal = c_ambient
	+ c_diffuse*diffuse
	+ (diffuse>0)*c_specular*specular;

  // for depth test...
  alphaVal = tnear;

  d_output[x+Nx*y] = colVal;
  d_alpha_output[x+Nx*y] = alphaVal;
  d_depth_output[x+Nx*y] = t_hit;


  
  d_normals_output[3*x+3*Nx*y] = normal.x;
  d_normals_output[1+3*x+3*Nx*y] = normal.y;
  d_normals_output[2+3*x+3*Nx*y] = normal.z;

}


// __kernel void iso_surface2(
// 						  __global float *d_output,
// 						  __global float *d_alpha_output,
// 						  __global float *d_depth_output,
// 						  __global float *d_normals_output,
// 						  uint Nx, uint Ny,
// 						  float boxMin_x,
// 						  float boxMax_x,
// 						  float boxMin_y,
// 						  float boxMax_y,
// 						  float boxMin_z,
// 						  float boxMax_z,
// 						  float isoVal,
// 						  float gamma,
// 						  __QUALIFIER_CONSTANT float* invP,
// 						  __QUALIFIER_CONSTANT float* invM,
// 						  __read_only image3d_t volume,
// 						  int isShortType)
// {
//   const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
// 	CLK_ADDRESS_CLAMP_TO_EDGE | SAMPLER_FILTER;

//   uint x = get_global_id(0);
//   uint y = get_global_id(1);

//   float u = (x / (float) Nx)*2.0f-1.0f;
//   float v = (y / (float) Ny)*2.0f-1.0f;

//   float4 boxMin = (float4)(boxMin_x,boxMin_y,boxMin_z,1.f);
//   float4 boxMax = (float4)(boxMax_x,boxMax_y,boxMax_z,1.f);



//   // calculate eye ray in world space
//   float4 orig0, orig;
//   float4 direc0, direc;
//   float4 temp;
//   float4 back,front;


//   front = (float4)(u,v,-1,1);
//   back = (float4)(u,v,1,1);


//   orig0 = mult(invP,front);
//   orig0 *= 1.f/orig0.w;


//   orig = mult(invM,orig0);
//   orig *= 1.f/orig.w;

//   temp = mult(invP,back);

//   temp *= 1.f/temp.w;

//   direc = mult(invM,normalize(temp-orig0));
//   direc.w = 0.0f;


//   // find intersection with box
//   float tnear, tfar;
//   int hit = intersectBox(orig,direc, boxMin, boxMax, &tnear, &tfar);




//   if (!hit) {
//   	if ((x < Nx) && (y < Ny)) {
//   	  d_output[x+Nx*y] = 0.f;

// 	  d_alpha_output[x+Nx*y] = 0.f;
// 	  d_depth_output[x+Nx*y] = INFINITY;
// 	  d_normals_output[3*x+3*Nx*y] = 0.f;
// 	  d_normals_output[1+3*x+3*Nx*y] = 0.f;
// 	  d_normals_output[2+3*x+3*Nx*y] = 0.f;
//   	}
//   	return;
//   }


//   if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

//   float colVal = 0;
//   float alphaVal = 0;


//   float dt = 1.f*(tfar-tnear)/maxSteps;




//   // uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
//   // orig += dt*random(entropy+x,entropy+y)*direc;


//   float4 delta_pos = .5f*dt*direc;
//   float4 pos = 0.5f *(1.f + orig + tnear*direc);

//   float newVal = read_image(volume, volumeSampler, pos,isShortType);
//   bool isGreater = newVal>isoVal;
//   bool hitIso = false;


//   float t_hit = -1.f;

//   float t1 = tnear, t2 = tfar;

//   //bracket the isoval between t1 and t2
//   for(uint i=1; i<maxSteps; i++) {
//   	pos += delta_pos;

//     //if ((x == Nx/2) && (y == Ny/2))
//     //printf("loop1:  %.5f %.6f %.6f \n",newVal,pos.z,delta_pos.z);

// 	newVal = read_image(volume, volumeSampler, pos, isShortType);


// //if (x+y==0)
//   //  printf("kern: %.8f %.8f %d\n",newVal, tnear+i*dt,(newVal>isoVal) != isGreater);

//     t_hit = tnear+i*dt;
//     hitIso = true;

// 	if ((newVal>isoVal) != isGreater){

//         d_output[x+Nx*y] = 123.f;

// 	  hitIso = true;
// 	  t_hit = tnear+i*dt;
// 	  t1 = tnear+(i-1)*dt;
// 	  t2 = tnear+i*dt;
// 	  break;
// 	}

//   }


// if (x+y==0)
//     printf("kern: %.8f %.8f %d\n",newVal, t_hit, hitIso);

//   //if no intersection  found return
//   if (!hitIso) {
//   	if ((x < Nx) && (y < Ny)) {
//   	  d_output[x+Nx*y] = 0.f;
// 	  d_alpha_output[x+Nx*y] = 0.f;
// 	  d_depth_output[x+Nx*y] = INFINITY;
// 	  d_normals_output[3*x+3*Nx*y] = 0.f;
// 	  d_normals_output[1+3*x+3*Nx*y] = 0.f;
// 	  d_normals_output[2+3*x+3*Nx*y] = 0.f;
//   	}

//   	return;
//   }

//   //if intersection found bisect, TODO!

//   int maxBisect = 10;


//   t_hit -= dt;
//   hitIso = false;

//   float dt2 = dt/maxBisect;
//   float4 delta_pos2 = .5f*dt2*direc;
//   pos -= delta_pos;

//   for(uint i=0; i<=maxBisect; i++) {

// 	newVal = read_image(volume, volumeSampler, pos, isShortType);
//     pos += delta_pos2;

// 	if ((newVal>isoVal) != isGreater){
// 	  hitIso = true;
// 	  t_hit += i*dt2;
// 	  break;
// 	}
//   }



//   // find real intersection point
//   // still broken
// //  float oldVal = read_image(volume, volumeSampler, pos-1*delta_pos, isShortType);
// //  float lam = .5f;

// //  if (newVal!=oldVal)
// //	lam = 1.f-(newVal - isoVal)/(newVal-oldVal);

// //  pos -= lam*delta_pos;
// //  t_hit -= lam*dt;




//   // now phong shading
//   float4 light = (float4)(2,-1,-2,0);

//   float c_ambient = .3f;
//   float c_diffuse = .4f;
//   float c_specular = .3f;


//   // c_ambient = 0.;
//   // c_diffuse = 1.;
//   // c_specular = .0;


//   light = mult(invM,light);
//   light = normalize(light);

//   // the normal


//   float4 normal;
//   float4 reflect;
//   float h = dt;

//   h*= pow(gamma,2);


//   // normal.x = read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
//   // 	read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType);
//   // normal.y = read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
//   // 	read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType);
//   // normal.z = read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
//   // 	read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType);

//   // robust 2nd order
//   normal.x = 2.f*read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
//   	2.f*read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType)+
// 	read_image(volume,volumeSampler,pos+(float4)(2.f*h,0,0,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(-2.f*h,0,0,0), isShortType);

//   normal.y = 2.f*read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
//   	2.f*read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType)+
// 	read_image(volume,volumeSampler,pos+(float4)(0,2.f*h,0,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(0,-2.f*h,0,0), isShortType);

//   normal.z = read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType)+
// 	read_image(volume,volumeSampler,pos+(float4)(0,0,2.f*h,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(0,0,-2.f*h,0), isShortType);

//   normal.w = 0;

//   //flip normal if we are comming from values greater than isoVal...
//   normal = (1.f-2*isGreater)*normalize(normal);

//   reflect = 2*dot(light,normal)*normal-light;

//   float diffuse = fmax(0.f,dot(light,normal));
//   float specular = pow(fmax(0.f,dot(normalize(reflect),normalize(direc))),10);

//   // phong shading
//   if (hitIso){
// 	colVal = c_ambient
// 	  + c_diffuse*diffuse
// 	  + (diffuse>0)*c_specular*specular;

//   }


//   // for depth test...
//   alphaVal = tnear;


//   if ((x < Nx) && (y < Ny)){
// 	d_output[x+Nx*y] = colVal;
// 	d_alpha_output[x+Nx*y] = alphaVal;
// 	d_depth_output[x+Nx*y] = t_hit;
// 	d_normals_output[3*x+3*Nx*y] = normal.x;
//     d_normals_output[1+3*x+3*Nx*y] = normal.y;
//     d_normals_output[2+3*x+3*Nx*y] = normal.z;
//   }

// }

__kernel void shading(
						  __global float *d_output,
						  __global float *d_alpha_output,
						  uint Nx, uint Ny,
						  __QUALIFIER_CONSTANT float* invP,
						  __QUALIFIER_CONSTANT float* invM,
                           float occ_strength,
						  __global float* input_normals,
						  __global float* input_depth,
						    __global float *input_occlusion)
{

  uint x = get_global_id(0);
  uint y = get_global_id(1);

  float u = (x / (float) Nx)*2.0f-1.0f;
  float v = (y / (float) Ny)*2.0f-1.0f;

  // calculate eye ray in world space
  float4 orig0, orig;
  float4 direc;
  float4 temp;
  float4 front, back;
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

  // now phong shading
  float4 light = (float4)(2,-1,-2,0);

  float c_ambient = .5f;
  float c_diffuse = .3f;
  float c_specular = .2f;


  light = mult(invM,light);
  light = normalize(light);

  float4 normal = (float4)(input_normals[3*(x+Nx*y)],
                            input_normals[1+3*(x+Nx*y)],
                            input_normals[2+3*(x+Nx*y)],0.f);

  float occ = input_occlusion[x+Nx*y];
  float depth = input_depth[x+Nx*y];

  normal = normalize(normal);
  float4 reflect = 2.f*dot(light,normal)*normal-light;

  float diffuse = fmax(0.f,dot(light,normal));
  float specular = pow(fmax(0.f,dot(normalize(reflect),normalize(direc))),10);

  // phong shading

  float colVal = c_ambient
	  + c_diffuse*diffuse
	  + (diffuse>0)*c_specular*specular;

  //colVal *= (1.f+occ_strength)*(1.f+occ_strength)*(1.f-occ_strength+occ_strength*occ);

  colVal = (1.f-occ_strength)*colVal+occ_strength*colVal*(1.f-occ);

  colVal = (1.f-occ_strength)*colVal+1.0*occ_strength*colVal;

  
  
  colVal *= ((depth<INFINITY)?1.f:0.f);

  if ((x < Nx) && (y < Ny)){
	d_output[x+Nx*y] = colVal;
 }

}
