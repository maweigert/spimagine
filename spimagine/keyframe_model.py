from numpy import *
import bisect
from PyQt4 import QtCore


class TransformData(object):
    def __init__(self,*args):
        if args:
            self.setData(*args)
        else:
            self.setData(0,0,0)

    def __repr__(self):
        return str(self.data)

    def setData(self,*args):
        self.data = array(args)



class KeyFrame(object):
    def __init__(self,tFrame = 0,data = TransformData()):
        self.tFrame = tFrame
        self.data = data

    def __repr__(self):
        return "t = %.3f \t %s"%(self.tFrame,self.data)

    def __cmp__(self,rhs):
        return cmp(self.tFrame,rhs.tFrame)


class KeyFrameList(QtCore.QObject):
    _modelChanged = QtCore.pyqtSignal()

    def __init__(self):
        super(KeyFrameList,self).__init__()
        self.keyFrames = [KeyFrame(0),KeyFrame(1.)]
        self._modelChanged.emit()

    def __repr__(self):
        return "\n".join(str(k) for k in self.keyFrames)

    def addKeyFrame(self, tFrame, transformData = TransformData()):
        bisect.insort(self.keyFrames,KeyFrame(tFrame,transformData))
        self._modelChanged.emit()

    def removeKeyFrame(self, index):
        if index<0 or index>len(self.keyFrames)-2:
            raise KeyError()
        self.keyFrames.pop(index)
        self._modelChanged.emit()

    def interpolate(self,x,y, lam):
        return  (1.-lam)*x.data.data + lam*y.data.data

    def getTransform(self,tFrame):
        #TODO: creating a instance of KeyFrame() just for comparing... not good
        ind = bisect.bisect(self.keyFrames,KeyFrame(tFrame))

        # clamping
        left = max(ind-1,0)
        right = min(ind,len(self.keyFrames)-1)

        if left==right:
            return self.keyFrames[left].data

        # linear interpolating
        frameLeft, frameRight = self.keyFrames[left], self.keyFrames[right]
        lam = (1.*tFrame-frameLeft.tFrame)/(frameRight.tFrame-frameLeft.tFrame)
        return self.interpolate(self.keyFrames[left], self.keyFrames[right],lam)




def test_interpolation():
    k = KeyFrameList()
    k.addKeyFrame(.5,TransformData(.5,.4,.3))

    for t in linspace(0,1,10):
        print t, k.getTransform(t)


if __name__ == '__main__':


    k = KeyFrameList()
    k.addKeyFrame(.5,TransformData(.5,.4,.3))

    for t in linspace(0,1,10):
        print t, k.getTransform(t)
