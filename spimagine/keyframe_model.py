from numpy import *
import bisect
from PyQt4 import QtCore
from spimagine.quaternion import *

class TransformData(object):
    def __init__(self,quatRot = Quaternion()):
        self.setData(quatRot)

    def __repr__(self):
        return "Quaternion: %s "%str(self.quatRot)

    def setData(self,quatRot):
        self.quatRot = Quaternion.copy(quatRot)



class KeyFrame(object):
    def __init__(self,tFrame = 0, dataPos = 0, transformData = TransformData()):
        self.tFrame = tFrame
        self.transformData = transformData
        self.dataPos = dataPos

    def __repr__(self):
        return "t = %.3f \t %i \t %s"%(self.tFrame,self.dataPos,self.transformData)

    def __cmp__(self,rhs):
        return cmp(self.tFrame,rhs.tFrame)


class KeyFrameList(QtCore.QObject):
    _countID = 0
    _modelChanged = QtCore.pyqtSignal()
    _itemChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super(KeyFrameList,self).__init__()
        self.keyDict = dict()
        self.tFrames = list()
        self.addItem(KeyFrame(0),)
        self.addItem(KeyFrame(1))
        self._modelChanged.emit()

    def __repr__(self):
        return "\n".join("%s \t %s"%(self.keyDict[k[1]],k[1]) for k in self.tFrames)

    def addItem(self, keyFrame = KeyFrame()):
        newID = self._getNewID()
        self.keyDict[newID] = keyFrame
        bisect.insort(self.tFrames,[keyFrame.tFrame, newID])
        self._modelChanged.emit()
        # self._itemChanged.emit(newID)

    def removeItem(self, ID):
        self.tFrames = [t for t in self.tFrames if t[1]!=ID]
        self.keyDict.pop(ID)
        self._modelChanged.emit()
        # self._itemChanged.emit(ID)

    def __getitem__(self,myID):
        return self.keyDict[myID]

    # def interpolate(self,x,y, lam):
    #     return  (1.-lam)*x.transformData.data + lam*y.transformData.dat,(1.-lam)*x.transformData.data + lam*y.transformData.data

    def _getNewID(self):
        self._countID += 1
        return self._countID

    def _NToID(self,index):
        if index<0 or index >len(self.tFrames):
            raise IndexError()

        return self.tFrames[index][1]

    def _IDToN(self,ID):
        return bisect.bisect_left(self.tFrames,[self.keyDict[ID].tFrame,ID])


    def getTransform(self,tFrame):
        ind = bisect.bisect(self.tFrames,[tFrame,-1])

        # clamping
        left = max(ind-1,0)
        right = min(ind,len(self.tFrames)-1)

        leftID, rightID = self._NToID(left),self._NToID(right)
        if leftID == rightID:
            return self.keyDict[leftID]

        # linear interpolating
        frameLeft, frameRight = self.keyDict[leftID], self.keyDict[rightID]
        lam = (1.*tFrame-frameLeft.tFrame)/(frameRight.tFrame-frameLeft.tFrame)

        #transforms:
        newQuat = quaternion_slerp(frameLeft.transformData.quatRot, frameRight.transformData.quatRot, lam)
        newPos = (1.-lam)*frameLeft.dataPos + lam*frameRight.dataPos
        newPos = int(newPos)

        return KeyFrame(tFrame,newPos,TransformData(newQuat))




def test_interpolation():
    k = KeyFrameList()
    k.addItem(KeyFrame(.5,0,TransformData(Quaternion(.71,.71,0,0))))

    for t in linspace(0,1,10):
        print t, k.getTransform(t)


if __name__ == '__main__':


    k = KeyFrameList()

    k.addItem(KeyFrame(.5,0,TransformData(Quaternion(.71,.71,0,0))))

    print k

    for t in linspace(0,1,11):
        print t, k.getTransform(t)
