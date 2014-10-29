


import logging
logger = logging.getLogger(__name__)



import numpy as np
import bisect
from PyQt4 import QtCore
from spimagine.quaternion import *

class TransformData(object):
    def __init__(self,quatRot = Quaternion(), zoom = 1, dataPos = 0, bounds = [-1,1,-1,1,-1,1]):
        self.setData(quatRot,zoom,dataPos,bounds)


    def __repr__(self):
        return " %s \t %s \t %s \t%s: "%(str(self.quatRot),self.zoom,self.dataPos, self.bounds)

    def setData(self,quatRot,zoom, dataPos, bounds):
        self.quatRot = Quaternion.copy(quatRot)
        self.zoom = zoom
        self.dataPos = dataPos
        self.bounds  = np.array(bounds)

    @classmethod
    def interp(cls,x1,x2,t):
        newQuat = quaternion_slerp(x1.quatRot, x2.quatRot, t)
        newZoom = (1.-t)*x1.zoom + t*x2.zoom
        newPos = int((1.-t)*x1.dataPos + t*x2.dataPos)
        newBounds = (1.-t)*x1.bounds + t*x2.bounds
        return TransformData(quatRot = newQuat,zoom = newZoom,
                             dataPos= newPos, bounds= newBounds)


class KeyFrame(object):
    def __init__(self,tFrame = 0, transformData = TransformData()):
        self.tFrame = tFrame
        self.transformData = transformData

    def __repr__(self):
        return "t = %.3f \t %s"%(self.tFrame,self.transformData)

    def __cmp__(self,rhs):
        return cmp(self.tFrame,rhs.tFrame)


class KeyFrameList(QtCore.QObject):

    _modelChanged = QtCore.pyqtSignal()
    _itemChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super(KeyFrameList,self).__init__()
        self._countID = 0
        self.keyDict = dict()
        self.tFrames = list()
        self.addItem(KeyFrame(0),)
        self.addItem(KeyFrame(1))
        self._modelChanged.emit()

    def __repr__(self):
        return "\n".join("%s \t %s"%(self.keyDict[k[1]],k[1]) for k in self.tFrames)

    def addItem(self, keyFrame = KeyFrame()):
        logger.debug("KeyFrameList.addItem: %s",keyFrame)
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
        logger.debug("getTransform")
        ind = bisect.bisect(self.tFrames,[tFrame,-1])

        # clamping
        left = max(ind-1,0)
        right = min(ind,len(self.tFrames)-1)

        leftID, rightID = self._NToID(left),self._NToID(right)

        # linear interpolating
        frameLeft, frameRight = self.keyDict[leftID], self.keyDict[rightID]
        if np.abs(frameRight.tFrame-frameLeft.tFrame)<1.e-7:
            lam = 0.
        else:
            lam = (1.*tFrame-frameLeft.tFrame)/(frameRight.tFrame-frameLeft.tFrame)

        #transforms:

        newTrans = TransformData.interp(frameLeft.transformData,frameRight.transformData,lam)

        return newTrans




def test_interpolation():
    k = KeyFrameList()
    k.addItem(KeyFrame(.5,0,TransformData(quatRot=Quaternion(.71,.71,0,0))))

    for t in np.linspace(0,1,10):
        print t, k.getTransform(t)


if __name__ == '__main__':


    k = KeyFrameList()

    k.addItem(KeyFrame(.5,TransformData(quatRot = Quaternion(.71,.71,0,0))))

    print k

    for t in np.linspace(0,1,11):
        print t, k.getTransform(t)
