"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division

import  numpy as np
from gputools import OCLArray, OCLProgram, OCLImage

src_str = """
__kernel void foo(__constant float *input, __global float * output)
{

int i = get_global_id(0);
int j = get_global_id(1);
int Nx = get_global_size(0);

output[i+j*Nx] = input[i+j*Nx];

}
"""

src_str = """
__kernel void
foo(__global float *d_output, __global float *d_alpha_output,
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
				 __constant float* invP,
				 __constant float* invM,
				 __read_only image3d_t volume
				 )

{

    d_output[0] = invM[0];
}

"""

if __name__ == '__main__':
    im = OCLImage.from_array((np.eye(10)).astype(np.float32))
    d = OCLArray.from_array((123*np.eye(10)).astype(np.float32))
    out = OCLArray.from_array(np.ones((10,10), np.float32))

    prog = OCLProgram(src_str=src_str)

    prog.run_kernel("foo",d.shape,None,out.data, out.data, out.data,
                    np.int32(1),
                    np.int32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.float32(1),
                    np.int32(1),
                    np.int32(1),
                    d.data,
                    d.data,
                    im)

    print(out.get())





