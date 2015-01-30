


import logging
logger = logging.getLogger(__name__)



import numpy as np
import bisect
from PyQt4 import QtCore
from spimagine.quaternion import *
import json

import spimagine


class TransformData(object):
    def __init__(self,quatRot = Quaternion(),
                 zoom = 1,
                 dataPos = 0,
                 translate = [0,0,0],
                 bounds = [-1,1,-1,1,-1,1],
                 isBox = True,
                 alphaPow = 100.):
        self.setData(quatRot,zoom,dataPos,translate,bounds,isBox,alphaPow)


    def __repr__(self):
        return "TransformData:\n%s \t %s \t %s \t%s\t%s\t%s: "%(str(self.quatRot),self.zoom,self.dataPos, self.bounds,self.isBox,self.alphaPow)

    def setData(self,quatRot,zoom, dataPos, translate, bounds,isBox,alphaPow):
        self.quatRot = Quaternion.copy(quatRot)
        self.zoom = zoom
        self.dataPos = dataPos
        self.bounds  = np.array(bounds)
        self.isBox = isBox
        self.alphaPow = alphaPow
        self.translate = np.array(translate)

    @classmethod
    def interp(cls,x1,x2,t):
        newQuat = quaternion_slerp(x1.quatRot, x2.quatRot, t)
        newZoom = (1.-t)*x1.zoom + t*x2.zoom
        newPos = int((1.-t)*x1.dataPos + t*x2.dataPos)
        newBounds = (1.-t)*x1.bounds + t*x2.bounds
        newBox = ((1.-t)*x1.isBox + t*x2.isBox)>.5
        newAlphaPow = (1.-t)*x1.alphaPow + t*x2.alphaPow
        newTranslate = (1.-t)*x1.translate + t*x2.translate

        return TransformData(quatRot = newQuat,zoom = newZoom,
                             dataPos= newPos, translate = newTranslate,
                             bounds= newBounds,
                             isBox = newBox, alphaPow = newAlphaPow)



class KeyFrame(object):
    def __init__(self,tFrame = 0, transformData = TransformData()):
        self.tFrame = tFrame
        self.transformData = transformData


    def __repr__(self):
        return "t = %.3f \t %s"%(self.tFrame,self.transformData)

    def __cmp__(self,rhs):
        return cmp(self.tFrame,rhs.tFrame)



""" the keyframe model """

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


    def dump_to_file(self,fName):
        print json.dumps(self._to_dict)

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

    def update_tFrame(self,myID, newTime):
        # print myID,self._IDToN(myID)
        # print self.tFrames
        # print self.tFrames[self._IDToN(myID)][0]
        #hACK!!!  please improve
        for i,t in enumerate(self.tFrames):
            if t[1] == myID:
                self.tFrames[i][0] = newTime

        self[myID].tFrame = newTime


    def getTransform(self,tFrame):
        logger.debug("getTransform")

        ind  = len(self.tFrames)
        for i,t in enumerate(self.tFrames):
            if t[0]>=tFrame:
                ind = i
                break

        # ind = bisect.bisect(self.tFrames,[tFrame,-1])

        # print ind
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

        # print lam, self.tFrames, self.keyDict
        # print frameLeft
        # print  frameRight
        #transforms:

        newTrans = TransformData.interp(frameLeft.transformData,frameRight.transformData,lam)

        return newTrans


    def _to_JSON(self):
        return json.dumps(self,cls = KeyFrameEncoder)

    @classmethod
    def _from_JSON(self,jsonStr):
        return json.loads(jsonStr,cls = KeyFrameDecoder)



"""JSON routines to save and load from file"""

class KeyFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray) and obj.ndim ==1:
            return obj.tolist()

        elif isinstance(obj, Quaternion):
            return obj.data.tolist()

        elif isinstance(obj, (
                KeyFrame,
                KeyFrameList,
                TransformData,
                spimagine.transform_model.TransformData)):
            return obj.__dict__

        return json.JSONEncoder.default(self, obj)


class KeyFrameDecoder(json.JSONDecoder):
    def decode(self, s, classname = ""):
        # print classname," XXXX\n" ,s
        if classname == "":

            dec = json.JSONDecoder.decode(self,s)
            ret = KeyFrameList()
            ret._countID = dec["_countID"]
            ret.tFrames = dec["tFrames"]
            ret.keyDict = self.decode(dec["keyDict"],"keyDict")
            return ret
        elif classname == "keyDict":
            return dict((int(k),KeyFrame(v["tFrame"],self.decode(v["transformData"],"transformData"))) for k,v in s.iteritems())

        elif classname == "transformData":
            t =  TransformData()
            t.__dict__.update(s)

            t.quatRot = Quaternion(*t.quatRot)
            t.bounds = np.array(t.bounds)
            return t


def test_interpolation():
    k = KeyFrameList()
    k.addItem(KeyFrame(.5,0,TransformData(quatRot=Quaternion(.71,.71,0,0))))

    for t in np.linspace(0,1,10):
        print t, k.getTransform(t)



if __name__ == '__main__':


    k = KeyFrameList()

    k.addItem(KeyFrame(.5,TransformData(zoom=.4,quatRot = Quaternion(.71,.71,0,0),bounds=[0]*6)))

    # print k

    # for t in np.linspace(0,1,6):
    #     print t, k.getTransform(t)



    s = k._to_JSON()

    print "\n\n\n"

    # k2 = json.loads(s,cls = KeyFrameDecoder)

    k2 = KeyFrameList._from_JSON(open("test.json").read())

    print k2
    # for t in np.linspace(0,1,6):
    #     print t, k2.getTransform(t)
