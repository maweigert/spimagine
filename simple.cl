__kernel void run( __read_only image3d_t input,__global float* output, const int Nx)
{
  const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE |	CLK_ADDRESS_CLAMP_TO_EDGE |	CLK_FILTER_NEAREST ;

  uint i = get_global_id(0);
  uint j = get_global_id(1);

  float pix = read_imagef(input,sampler,(int4)(i/2,j/2,10,0)).x;

  output[i+Nx*j] = pix;
  
}

