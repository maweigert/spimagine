#!/usr/bin/env python

"""
command line rendering program, currently supports just 3d tiff files

for all the options run
python spim_render.py -h



author: Martin Weigert
email: mweigert@mpi-cbg.de
"""



from __future__ import absolute_import
from __future__ import print_function
import sys
import argparse

from volume_render import *
from scipy.misc import toimage
from imgutils import read3dTiff, fromSpimFolder

from PIL import Image
import six

def getTiffSize(fName):
    img = Image.open(fName, 'r')
    depth = 0
    while True:
        try:
            img.seek(depth)
        except EOFError:
            break
        depth += 1

    return (depth,)+img.size[::-1]



# def read3dTiff(fName, depth = -1, dtype = np.uint16):

#     if not depth>0:
#         depth = getTiffSize(fName)[0]

#     img = Image.open(fName, 'r')
#     stackSize = (depth,) + img.size[::-1]

#     data = np.empty(stackSize,dtype=dtype)

#     for i in range(stackSize[0]):
#         img.seek(i)
#         data[i,...] = np.asarray(img, dtype= dtype)

#     return data


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
        description="""renders max projectios of 3d data

    example usage:

    Tif data: \t \tspim_render  -i mydata.tif -o myoutput.png -t 0 0 -4 -u 1 1 4
    Bscope data:  \tspim_render -f bscope -i mydataFolder -o myoutput.png -t 0 0 -4 -u 1 1 4
    """)

    parser.add_argument("-f","--format",dest="format",metavar="format",
                        help = """format currently supported:
    tif (default)
    bscope  """,
                        type=str,default = "tif", required = False)

    parser.add_argument("-i","--input",dest="input",metavar="infile",
                        help = "name of the input file to render, currently only 3d Tiff is supported",
                        type=str,default = None, required = True)

    parser.add_argument("-o","--output",dest="output",metavar="outfile",
                        help = "name of the output file,  png extension is recommended",
                        type=str,default = "out.png")

    parser.add_argument("-p","--pos",dest="pos",metavar="timepoint position",
                        help = "timepoint to render if format=='bscope' ",
                        type=int,default = 0)

    parser.add_argument("-w","--width",dest="width",metavar="width",
                        help = "pixelwidth of the rendered output ",
                        type=int,default = 400)

    parser.add_argument("-s","--scale",dest="scale",metavar="scale",
                        type=float,nargs=1 ,default = [1.])


    parser.add_argument("-u","--units",dest="units",metavar="units",
                        type=float,nargs= 3 ,default = [1.,1.,5.])


    parser.add_argument("-t","--translate",dest="translate",
                        type = float, nargs=3,default = [0,0,-4],
                        metavar=("x","y","z"))

    parser.add_argument("-r","--rotation",dest="rotation", type =
                        float, nargs=4,default = [0,1,0,0],
                        metavar=("w","x","y","z"))

    parser.add_argument("-R","--range",dest="range", type =
                        float, nargs=2,default = None,
                        help = "if --16bit is set, the range of the data values to consider, defaults to [min,max]",
                        metavar=("min","max"))


    parser.add_argument("-O","--Orthoview",help="use parallel projection (default: perspective)",
                        dest="ortho",action="store_true")

    parser.add_argument("--16bit",help="render into 16 bit png",
                        dest="is16Bit",action="store_true")

    if len(sys.argv)==1:
        parser.print_help()
        return

    args = parser.parse_args()


    for k,v in six.iteritems(vars(args)):
        print(k,v)

    rend = VolumeRenderer((args.width,args.width))

    if args.format=="tif":
        data = read3dTiff(args.input)
    elif args.format=="bscope":
        data = fromSpimFolder(args.input,pos=args.pos,count=1)[0,...]
    else:
        raise ValueError("format %s not supported (should be tif/bscope)" %args.format)

    rend.set_data(data)
    rend.set_units(args.units)

    M = scaleMat(*(args.scale*3))
    M = dot(rotMat(*args.rotation),M)
    M = dot(transMatReal(*args.translate),M)

    rend.set_modelView(M)

    if args.ortho:
        rend.set_projection(projMatOrtho(-1,1,-1,1,-1,1))
    else:
        rend.set_projection(projMatPerspective(60,1.,1,10))

    out = rend.render()

    # image is saved by scipy.misc.toimage(out,low,high,cmin,cmax)
    # p' = p * high/cmax

    if not args.is16Bit:
        imsave(args.output,out)
        # if not args.range:
        #     imsave(args.output,out)
        # else:
        #     img = toimage(out, low = args.range[0], high  = args.range[1])
        #     img.save(args.output)

    else:
        if not args.range:
            print("min/max: ", amin(out), amax(out))
            img = toimage(out, low = amin(out), high  = amax(out),mode = "I")
        else:
            img = toimage(out, low = args.range[0], high  = args.range[1], mode = "I")
        img.save(args.output)


if __name__ == '__main__':
    main()
