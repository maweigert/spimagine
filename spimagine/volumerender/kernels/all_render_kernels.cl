/*
  adapted from the Nvidia sdk sample
  http://developer.download.nvidia.com/compute/cuda/4_2/rel/sdk/website/OpenCL/html/samples.html


  mweigert@mpi-cbg.de
 */

#ifndef maxSteps
#define maxSteps 505
#endif

#ifdef QUALIFIER_CONSTANT_TO_GLOBAL
#define __QUALIFIER_CONSTANT __global
#else
#define __QUALIFIER_CONSTANT __constant
#endif

#ifndef SAMPLER_FILTER
#define SAMPLER_FILTER CLK_FILTER_LINEAR
#endif


#include<volume_kernel.cl>

#include<iso_kernel.cl>



