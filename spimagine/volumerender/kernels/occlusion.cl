#ifndef OCCLUSION_H
#define OCCLUSION_H

#include<utils.cl>

__kernel void occlusion_depth(__global float *d_output,
						  uint Nx, uint Ny,
						  uint radius,
						  uint number_points,
						  __global float *input_depth

						){

  int x = get_global_id(0);
  int y = get_global_id(1);

  float depth0 = input_depth[x+y*Nx];

  float occ = 0.f;

  for(uint i = 0;i<number_points;++i){

    //sample point

    float r = radius*native_sqrt((float)(random(x+rand_int(i,i,0,1000),y+rand_int(i,i,0,10000))));
    float phi = MPI_2*random(x+rand_int(i,i,0,1000),y+rand_int(i,i,0,10000));

    int x2 = clamp((int)(x+r*cos(phi)),(int)0,(int)Nx-1);
    int y2 = clamp((int)(y+r*sin(phi)),(int)0,(int)Ny-1);

    float depth = input_depth[x2+y2*Nx];

    occ += (depth>depth0?1.f:0.f);

  }

  d_output[x+Nx*y]  = occ/number_points;

}

__kernel void occlusion(__global float *d_output,
						  uint Nx, uint Ny,
						  uint radius,
						  uint number_points,
						  __global float *input_depth,
						  __global float *input_normal
						){

  int x = get_global_id(0);
  int y = get_global_id(1);

  float depth0 = input_depth[x+y*Nx];

  float occ = 0.f;

  for(uint i = 0;i<number_points;++i){

    //sample point uniformly
    // float r = radius*native_sqrt((float)(random(x+rand_int(i,i*i,0,1000),y+rand_int(i*i,i,294,97701))));

	//sample point non-uniformly

	float r = radius*(float)(random(x+rand_int(i,i*i,0,1000),y+rand_int(i*i,i,294,97701)));

    float phi = MPI_2*random(x+rand_int(i*i,i,0,1997),y+rand_int(i,i*i,569,17633));

    int x2 = clamp((int)(x+r*cos(phi)),(int)0,(int)Nx-1);
    int y2 = clamp((int)(y+r*sin(phi)),(int)0,(int)Ny-1);

    float depth = input_depth[x2+y2*Nx];

    occ += (depth<depth0?1.f:0.f);

	// if ((x==200)&&(y==200)){
	//   printf("%d \n",i);
	// }
	
  }

  d_output[x+Nx*y]  = occ/number_points;

}



#endif
