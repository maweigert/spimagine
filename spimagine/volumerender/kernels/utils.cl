#ifndef UTILS_H
#define UTILS_H


#define MPI_2 6.2831853071795f
//#define INFINITY 1.e30f

// returns random value between [0,1]

inline float random(uint x, uint y)
{   
    uint a = 4421 +(1+x)*(1+y) +x +y;

    for(int i=0; i < 10; i++)
    {
        a = (1664525 * a + 1013904223) % 79197919;
    }

    float rnd = (a*1.0f)/(79197919);

    return rnd;

}

inline float rand_int(uint x, uint y, int start, int end)
{
    uint a = 4421 +(1+x)*(1+y) +x +y;

    for(int i=0; i < 10; i++)
    {
        a = (1664525 * a + 1013904223) % 79197919;
    }

    float rnd = (a*1.0f)/(79197919);

    return (int)(start+rnd*(end-start));

}


inline int intersectBox(float4 r_o, float4 r_d, float4 boxmin, float4 boxmax, float *tnear, float *tfar)
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


inline float4 mult(__QUALIFIER_CONSTANT float* M, float4 v){
  float4 res;
  res.x = dot(v, (float4)(M[0],M[1],M[2],M[3]));
  res.y = dot(v, (float4)(M[4],M[5],M[6],M[7]));
  res.z = dot(v, (float4)(M[8],M[9],M[10],M[11]));
  res.w = dot(v, (float4)(M[12],M[13],M[14],M[15]));
  return res;
}




#define read_image(volume,sampler, pos,isShortType) (isShortType?1.f*read_imageui(volume, sampler, pos).x:read_imagef(volume, sampler, pos).x)

#endif
