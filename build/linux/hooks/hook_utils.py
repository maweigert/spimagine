import os
import sys
import re

def _get_toc_objects(root ,
                     filter_str = ".*",
                     dir_prefix = "",
                     flatten_dir = False,
                     ):

    reg = re.compile(filter_str)
    res = []
    for fold, subs, files in os.walk(root):

        rel_dir = os.path.relpath(fold,root)
        for fName in files:
            if reg.match(fName):
                if not flatten_dir:
                    name = os.path.join(dir_prefix,rel_dir, fName)
                else:
                    name = os.path.join(dir_prefix, fName)
                res += [(os.path.join(fold,fName), name)]
    return res

if __name__ == '__main__':

    import pyopencl

    __PATH__ = os.path.dirname(pyopencl.__file__)


    print _get_toc_objects(os.path.join(__PATH__, "cl"),
                       dir_prefix = "pyopencl/cl")

    # print _get_toc_objects(os.path.join(__PATH__, "cl/"),
    #                    dir_prefix = "pyopencl/cl")

