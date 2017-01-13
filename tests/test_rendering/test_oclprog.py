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
    uint x = get_global_id(0);
    uint y = get_global_id(1);


    d_output[x+Nx*y] = invM[x+Nx*y];
}

"""
#
# if __name__ == '__main__':
#     im = OCLImage.from_array((np.eye(4)).astype(np.float32))
#     d = OCLArray.from_array((123*np.eye(4)).astype(np.float32))
#     out = OCLArray.from_array(np.ones((4,4), np.float32))
#
#     prog = OCLProgram(src_str=src_str)
#
#     prog.run_kernel("foo",d.shape,None,out.data, out.data, out.data,
#                     np.int32(4),
#                     np.int32(4),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.float32(1),
#                     np.int32(1),
#                     np.int32(1),
#                     d.data,
#                     d.data,
#                     im)
#
#     print(out.get())


if __name__ == '__main__':
    from spimagine.volumerender.volumerender import VolumeRenderer
    from gputools.utils.utils import remove_cache_dir, get_cache_dir
    remove_cache_dir()

    data = (123 * np.ones((10, 10, 10))).astype(np.float32)

    rend = VolumeRenderer((4, 4))

    rend.proc = OCLProgram("/Users/mweigert/python/spimagine/spimagine/volumerender/kernels/all_render_kernels.cl",
                           build_options=
                           ["-I", "/Users/mweigert/python/spimagine/spimagine/volumerender/kernels",
                            "-D", "maxSteps=100",
                                "-D","QUALIFIER_CONSTANT_TO_GLOBAL"
                                "-cl-finite-math-only",
                                    "-cl-fast-relaxed-math",
                                    "-cl-unsafe-math-optimizations",
                                    "-cl-mad-enable"])

    rend.set_data(data)
    rend.proc.run_kernel("max_project_float",
                         (rend.width, rend.height),
                         None,
                         rend.buf.data,
                         rend.buf_alpha.data,
                         rend.buf_depth.data,
                         np.int32(rend.width),
                         np.int32(rend.height),
                         np.float32(rend.boxBounds[0]),
                         np.float32(rend.boxBounds[1]),
                         np.float32(rend.boxBounds[2]),
                         np.float32(rend.boxBounds[3]),
                         np.float32(rend.boxBounds[4]),
                         np.float32(rend.boxBounds[5]),
                         np.float32(rend.minVal),
                         np.float32(rend.maxVal),
                         np.float32(rend.gamma),
                         np.float32(rend.alphaPow),
                         np.int32(1),
                         np.int32(0),
                         rend.invPBuf.data,
                         rend.invMBuf.data,
                         rend.dataImg
                         )

    out = rend.buf.get()

    print(out)