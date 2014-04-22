#!/usr/bin/python

import sys
import argparse

from volume_render import *
from scipy.misc import toimage


from PIL import Image

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



def read3dTiff(fName, depth = -1, dtype = np.uint16):

    if not depth>0:
        depth = getTiffSize(fName)[0]

    img = Image.open(fName, 'r')
    stackSize = (depth,) + img.size[::-1]

    data = np.empty(stackSize,dtype=dtype)

    for i in range(stackSize[0]):
        img.seek(i)
        data[i,...] = np.asarray(img, dtype= dtype)

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="3d max projects a file renders a file")

    parser.add_argument("-i","--input",dest="input",metavar="infile",
                        help = "name of the input file to render, currentlty only 3d Tiff is supported",
                        type=str,default = None, required = True)

    parser.add_argument("-o","--output",dest="output",metavar="outfile",
                        help = "name of the output file,  png extension is recommended",
                        type=str,default = None, required = True)

    parser.add_argument("-w","--width",dest="width",metavar="width",
                        help = "pixelwidth of the rendered output ",
                        type=int,nargs=1,default = 400)

    parser.add_argument("-s","--scale",dest="scale",metavar="scale",
                        type=float,nargs=1 ,default = [1.])

    parser.add_argument("-t","--translate",dest="translate",
                        type = float, nargs=3,default = [0,0,-4],
                        metavar=("x","y","z"))

    parser.add_argument("-r","--rotation",dest="rotation", type =
                        float, nargs=4,default = [0,1,0,0],
                        metavar=("w","x","y","z"))

    parser.add_argument("-R","--range",dest="range", type =
                        float, nargs=2,default = None,
                        help = "the range of the data values to consider",
                        metavar=("min","max"))


    parser.add_argument("-OV","--Orthoview",dest="ortho",action="store_true")

    parser.add_argument("-16","--16bit",dest="is16Bit",action="store_true")

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()


    for k,v in vars(args).iteritems():
        print k,v

    rend = VolumeRenderer2((args.width,args.width))

    data = read3dTiff(args.input)

    rend.set_data(data)
    rend.set_units([1.,1.,4.])

    M = scaleMat(*(args.scale*3))
    M = dot(M,rotMat(*args.rotation))
    M = dot(M,transMatReal(*args.translate))

    rend.set_modelView(M)

    out = rend.render(isPerspective = not args.ortho)


    if not args.is16Bit:
        if not args.range:
            imsave(args.output,out)
        else:
            img = toimage(out, low = args.range[0], high  = args.range[0])
            img.save(args.output)

    else:
        if not args.range:
            img = toimage(out, low = amin(out), high  = amax(out),mode = "I")
        else:
            print args.range
            img = toimage(out, low = args.range[0], high  = args.range[1], mode = "I")
        img.save(args.output)

    # # import pylab

    # # pylab.imshow(out)

    # # pylab.show()
