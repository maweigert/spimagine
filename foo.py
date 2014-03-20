from volume_render import *
from pylab import *


def transMat(x=0,y=0,z=0):
    return np.array([1.0, 0.0, 0.0, x,
                          0.0, 1.0, 0.0, y,
                          0.0, 0.0, 1.0, z,
                          0, 0, 0, 1.0]).reshape(4,4)


class volrend(VolumeRenderer):
    def render(self,data, matM = transMat(), matP = projMatOrtho(-1,1,-1,1,-1,1)):


        # matM

        # invViewMatrix = modelView.transpose()[:-1,:]

        self.proc = OCLProcessor(self.dev,absPath("volume_render.cl"))

        self.set_data(data)

        self.matMBuf = self.dev.createBuffer(16,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)
        self.matPBuf = self.dev.createBuffer(16,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)

        self.invPMBuf = self.dev.createBuffer(16,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)

        matM = inv(matM)
        self.invPM = inv(dot(matP,matM))
        print self.invPM

        
        self.dev.writeBuffer(self.matMBuf,matM.flatten().astype(float32))
        self.dev.writeBuffer(self.matPBuf,matP.flatten().astype(float32))
        self.dev.writeBuffer(self.invPMBuf,self.invPM.flatten().astype(float32))

        self.proc.runKernel("test",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   self.matMBuf,
                   self.matPBuf,
                   self.invPMBuf,
                   self.dataImg)


        return self.dev.readBuffer(self.buf,dtype = uint16).reshape(self.width,self.height)


if __name__ == '__main__':


    rend = volrend((400,400))

    N = 100
    tmp = arange(N)
    Y,Z,X = np.meshgrid(tmp,tmp,tmp)

    d = bitwise_xor(X,bitwise_xor(Y,Z))

    matM = transMat(0,0,-4.)
    matP = projMatOrtho()
    matP = projMatPerspective()

    out = rend.render(d,matM,matP)


    ion()
    imshow(out)
