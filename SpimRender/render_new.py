from volume_render import *
from pylab import *
import time
import SpimUtils
from transform_matrices import *


class volrend(VolumeRenderer):
    def render(self,data, matM = transMat(), isPersp = False):

        self.proc = OCLProcessor(self.dev,absPath("volume_render.cl"))

        self.set_data(data)

        self.invMBuf = self.dev.createBuffer(16,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)

        print inv(matM)
        self.dev.writeBuffer(self.invMBuf,inv(matM).flatten().astype(float32))

        self.proc.runKernel("max_project",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   self.invMBuf,
                   bool8(isPersp),
                   self.dataImg)
        return self.dev.readBuffer(self.buf).reshape(self.width,self.height)



if __name__ == '__main__':


    rend = volrend((400,400))

    N = 100
    tmp = arange(N)
    Y,Z,X = np.meshgrid(tmp,tmp,tmp)

    d = bitwise_xor(X,bitwise_xor(Y,Z)).astype(uint16)

    # d = SpimUtils.fromSpimFolder("../Data/Drosophila_05",count=1)[0,...]


    matM = dot(transMatReal(0,0,-1.),dot(rotMatX(1.4),scaleMat(.4,1.,.4)))
    # # matM = dot(transMatReal(0,0,-2),scaleMat(1.,1.,1.))
    # matM = scaleMat(1.,1.,1.4)


    for t in linspace(0,2,10):
        matM = dot(transMatReal(0,0,-2.),dot(rotMatX(t),scaleMat(.4,.4,.4)))

        img1, img2 = None, None
        print matM
        out1 = rend.render(d,matM,isPersp = True)
        out2 = rend.render(d,matM)

        figure(1)
        subplot(121)
        axis("off")
        if not img1:
            img1 = imshow(out1)
        else:
            img1.set_data(out1)
        subplot(122)
        axis("off")

        if not img2:
            img2 = imshow(out2)
        else:
            img2.set_data(out2)

        draw()
        time.sleep(.1)
