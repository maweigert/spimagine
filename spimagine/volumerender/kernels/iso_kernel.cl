/*

  Iso surface rendering kernels 

  mweigert@mpi-cbg.de
 */


#include<utils.cl>


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
  
  float newVal = read_image(volume, volumeSampler, pos*0.5f+0.5f,isShortType);
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


// __kernel void iso_surface_new(
// 						  __global float *d_normals,
// 						  __global float *d_alpha,
// 						  uint Nx, uint Ny,
// 						  float boxMin_x,
// 						  float boxMax_x,
// 						  float boxMin_y,
// 						  float boxMax_y,
// 						  float boxMin_z,
// 						  float boxMax_z,
// 						  float isoVal,
// 						  float gamma,
// 						  __constant float* invP,
// 						  __constant float* invM,
// 						  __read_only image3d_t volume,
// 						  int isShortType)
// {
//   const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
// 	CLK_ADDRESS_CLAMP_TO_EDGE |
// 	// CLK_FILTER_NEAREST ;
// 	CLK_FILTER_LINEAR ;
  
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
//   	  d_normals[0+3*x+3*Nx*y] = 0.f;
// 	  d_normals[1+3*x+3*Nx*y] = 0.f;
// 	  d_normals[2+3*x+3*Nx*y] = 0.f;
// 	  d_alpha[x+Nx*y] = 0.f;
//   	}
//   	return;
//   }
//   if (tnear < 0.0f) tnear = 0.0f;     // clamp to near plane

//   float t = tnear;

//   float4 pos = orig + tnear*direc;;

//   uint i;

//   float dt = (tfar-tnear)/maxSteps;

  
//   float newVal = read_image(volume, volumeSampler, pos*0.5f+0.5f, isShortType);
//   bool isGreater = newVal>isoVal;
//   bool hitIso = false;

  
//   // if ((x == Nx/2) && (y == Ny/2))
//   // 	printf("start:  %.2f %.2f %d\n",newVal,isoVal,isGreater);

//   uint entropy = (uint)( 6779514*length(orig) + 6257327*length(direc) );
//   // orig += dt*random(entropy+x,entropy+y)*direc;


  
//   for(t=tnear; t<tfar; t+=dt) {		
//   	pos = orig + t*direc;
// 	pos = pos*0.5f+0.5f;    // map position to [0, 1] coordinates

// 	newVal = read_image(volume, volumeSampler, pos, isShortType);

// 	if ((newVal>isoVal) != isGreater){
// 	  hitIso = true;
// 	  break;
// 	}
//   }

//   if (!hitIso) {
//   	if ((x < Nx) && (y < Ny)) {
//   	  d_normals[0+3*x+3*Nx*y] = 0.f;
// 	  d_normals[1+3*x+3*Nx*y] = 0.f;
// 	  d_normals[2+3*x+3*Nx*y] = 0.f;
// 	  d_alpha[x+Nx*y] = 0.f;   
//   	}
//   	return;
//   }
  
//   // the normal

//   // if (x==300 &&y ==300)
//   // 	printf("diffuse: %.4f \n",tnear);
  
//   float4 normal;
//   float h = dt;

//   h*= pow(gamma,2);

//   normal.x = read_image(volume,volumeSampler,pos+(float4)(h,0,0,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(-h,0,0,0), isShortType);
//   normal.y = read_image(volume,volumeSampler,pos+(float4)(0,h,0,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(0,-h,0,0), isShortType);
//   normal.z = read_image(volume,volumeSampler,pos+(float4)(0,0,h,0), isShortType)-
//   	read_image(volume,volumeSampler,pos+(float4)(0,0,-h,0), isShortType);
 
//   normal.w = 0;

//   //flip normal if we are comming from values greater than isoVal... 
//   normal = (1.f-2*isGreater)*normalize(normal);


  
//   if ((x < Nx) && (y < Ny)){
// 	  d_normals[0+3*x+3*Nx*y] = normal.x;
// 	  d_normals[1+3*x+3*Nx*y] = normal.y;
// 	  d_normals[2+3*x+3*Nx*y] = normal.z;
// 	  d_alpha[x+Nx*y] = t;
//   }

// }


// __kernel void blur_normals_x(__global float *d_input,
// 							 __global float *d_output,
// 							 int N)

// {

//   uint x = get_global_id(0);
//   uint y = get_global_id(1);

//   uint Nx = get_global_size(0);
//   uint Ny = get_global_size(1);
	
//   float4 res = (float4)(0.f,0.f,0.f,0.f);
//   float hsum = 0.f;

//   float fac = -.1f/N/N;
  
//   for (int i = -N; i <= N; ++i){
// 	float h = exp(fac*i*i);
// 	hsum += h;
	
// 	res.x += h*d_input[0+3*(x+i)+3*Nx*y];
// 	res.y += h*d_input[1+3*(x+i)+3*Nx*y];
// 	res.z += h*d_input[2+3*(x+i)+3*Nx*y];

//   }

//   // if (x==300 &&y ==300)
//   // 	  printf("%.2f \n",hsum);


//   res *= 1.f/hsum;

//   //res = normalize(res);

//   d_output[0+3*x+3*Nx*y] = res.x;
//   d_output[1+3*x+3*Nx*y] = res.y;
//   d_output[2+3*x+3*Nx*y] = res.z;  

// }


// __kernel void blur_normals_y(__global float *d_input,
// 							 __global float *d_output,
// 							 int N)

// {

//   uint x = get_global_id(0);
//   uint y = get_global_id(1);

//   uint Nx = get_global_size(0);
//   uint Ny = get_global_size(1);
	
//   float4 res = (float4)(0.f,0.f,0.f,0.f);
//   float hsum = 0.f;

//   float fac = -.1f/N/N;
  
//   for (int i = -N; i <= N; ++i){
// 	float h = exp(fac*i*i);
// 	hsum += h;
	
// 	res.x += h*d_input[0+3*x+3*Nx*(y+i)];
// 	res.y += h*d_input[1+3*x+3*Nx*(y+i)];
// 	res.z += h*d_input[2+3*x+3*Nx*(y+i)];

//   }

//   // if (x==300 &&y ==300)
//   // 	  printf("%.2f \n",hsum);


//   res *= 1.f/hsum;

//   //res = normalize(res);

//   d_output[0+3*x+3*Nx*y] = res.x;
//   d_output[1+3*x+3*Nx*y] = res.y;
//   d_output[2+3*x+3*Nx*y] = res.z;  

// }



// __kernel void iso_shading(__global float *d_normals,
// 						  __global float *d_alpha,
// 						  __constant float *invM,
// 						  __constant float *invP,
// 						  __global float *d_output)
// {
//   const sampler_t volumeSampler =   CLK_NORMALIZED_COORDS_TRUE |
// 	CLK_ADDRESS_CLAMP_TO_EDGE |
// 	// CLK_FILTER_NEAREST ;
// 	CLK_FILTER_LINEAR ;
  
//   uint x = get_global_id(0);
//   uint y = get_global_id(1);
//   uint Nx = get_global_size(0);
//   uint Ny = get_global_size(1);


//   float u = (x / (float) Nx)*2.0f-1.0f;
//   float v = (y / (float) Ny)*2.0f-1.0f;


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
  

  
//   float4 normal;
//   normal.x = d_normals[0+3*x+3*Nx*y];
//   normal.y = d_normals[1+3*x+3*Nx*y];
//   normal.z = d_normals[2+3*x+3*Nx*y];
//   normal.w = 0.f;

//   normal = normalize(normal);

//   float4 reflect;


//   float colVal = 0;
//   float alphaVal = 0;

//   float4 light = (float4)(2,-1,-2,0);

//   float c_ambient = .3;
//   float c_diffuse = .4;
//   float c_specular = .3;


//   light = mult(invM,light);
//   light = normalize(light);


//   reflect = 2*dot(light,normal)*normal-light;

//   float diffuse = fmax(0.f,-dot(light,normal));
//   float specular = pow(fmax(0.f,-dot(normalize(reflect),normalize(direc))),10);
  
//   colVal = c_ambient
// 	+ c_diffuse*diffuse
// 	+ (diffuse>0)*c_specular*specular;
	
//   if ((x < Nx) && (y < Ny)){
// 	d_output[x+Nx*y] = (d_alpha[x+Nx*y]>0)?colVal:0.f;
//   }


//   // if (x==300 &&y ==300)
//   // 	printf("diffuse: %.4f \n",dot(light,normal));


// }

