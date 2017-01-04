from __future__ import absolute_import, print_function

import logging
import six
from six.moves import range

logger = logging.getLogger(__name__)

import numpy as np
import bisect
from PyQt5 import QtCore
import json
import sortedcontainers
from spimagine.utils.quaternion import *
import spimagine


def create_interp_func(a):
    """ an elastic interpolation function on the interval [0,1]

    f(0) = 0.
    f(1) = 1.

    the bigger a, the more elastic 
    when a==0, its the usual hard linear interpolation 
    """

    def atan_func(x):
        return .5*(1+np.arctan(2*a*(x-.5))/np.arctan(a))

    def linear_func(x):
        return x

    if a==0:
        return linear_func
    else:
        return atan_func


class KeyableParameter(object):
    def __init__(self):
        self.val_dict = {}

    def register_value(self, name, default=0.):
        self.val_dict[name] = default

    def __getattr__(self, name):
        return self.val_dict[name]


class TransformData(object):
    def __init__(self, quatRot=Quaternion(),
                 zoom=1,
                 dataPos=0,
                 minVal=0.,
                 maxVal=100.,
                 gamma=1.,
                 translate=[0, 0, 0],
                 bounds=[-1, 1, -1, 1, -1, 1],
                 isBox=True,
                 isIso=False,
                 alphaPow=0.):
        self.setData(quatRot=quatRot,
                     zoom=zoom,
                     dataPos=dataPos,
                     minVal=minVal,
                     maxVal=maxVal,
                     gamma=gamma,
                     translate=translate,
                     bounds=bounds,
                     isBox=isBox,
                     isIso=isIso,
                     alphaPow=alphaPow)

    def __repr__(self):
        return """TransformData(quatRot = %s, zoom = %s,
                             dataPos = %s,
                             minVal = %s,
                             maxVal = %s,
                             gamma= %s,
                             translate = %s,
                             bounds = %s,
                             isBox = %s,
                             isIso = %s,
                             alphaPow = %s)"""%(str(self.quatRot),
                                                           self.zoom,
                                                           self.dataPos,
                                                           self.minVal,
                                                           self.maxVal,
                                                           self.gamma,
                                                           self.translate.__repr__(),
                                                           self.bounds.__repr__(),
                                                           self.isBox,
                                                           self.isIso,
                                                           self.alphaPow)

    def setData(self, quatRot, zoom, dataPos, minVal, maxVal,
                gamma, translate, bounds, isBox, isIso, alphaPow):
        self.quatRot = Quaternion.copy(quatRot)
        self.zoom = zoom
        self.dataPos = dataPos
        self.minVal = minVal

        self.maxVal = maxVal
        self.gamma = gamma
        self.bounds = np.array(bounds)
        self.isBox = isBox
        self.isIso = isIso
        self.alphaPow = alphaPow
        self.translate = np.array(translate)

    @classmethod
    def interp(cls, x1, x2, lam, f=create_interp_func(0.)):
        """
        f should be a function [0...1] - [0...1]
        """
        t = f(lam)
        newQuat = quaternion_slerp(x1.quatRot, x2.quatRot, t)
        newZoom = (1.-t)*x1.zoom+t*x2.zoom
        newPos = int((1.-t)*x1.dataPos+t*x2.dataPos)
        newMinVal = (1.-t)*x1.minVal+t*x2.minVal

        newMaxVal = (1.-t)*x1.maxVal+t*x2.maxVal
        newGamma = (1.-t)*x1.gamma+t*x2.gamma

        newBounds = (1.-t)*x1.bounds+t*x2.bounds

        newAlphaPow = (1.-t)*x1.alphaPow+t*x2.alphaPow
        newTranslate = (1.-t)*x1.translate+t*x2.translate

        # some things should not be interpolated...
        newBox = x1.isBox
        newIso = x1.isIso

        return TransformData(quatRot=newQuat, zoom=newZoom,
                             dataPos=newPos,
                             minVal=newMinVal,
                             maxVal=newMaxVal,
                             gamma=newGamma,
                             translate=newTranslate,
                             bounds=newBounds,
                             isBox=newBox,
                             isIso=newIso,
                             alphaPow=newAlphaPow)


class KeyFrame(object):
    def __init__(self, pos=0,
                 transformData=TransformData(),
                 interp_elasticity=0.):
        self.pos = pos
        self.transformData = transformData
        self.interp_elasticity = interp_elasticity

    def __repr__(self):
        return "Keyframe at t = %.3f (elasticity = %s) \n%s"%(self.pos, self.interp_elasticity, self.transformData)


""" the keyframe model """


class KeyFrameList(QtCore.QObject):
    _modelChanged = QtCore.pyqtSignal()
    _itemChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super(KeyFrameList, self).__init__()
        self._countID = 0
        self.posdict = sortedcontainers.SortedDict()
        self.items = dict()
        # self.addItem(KeyFrame(0.))
        # self.addItem(KeyFrame(1.))
        self._modelChanged.emit()

    def __repr__(self):
        s = "\n".join([str(self.items[ID]) for ID in self.posdict.values()])
        s += "\n%s\n%s\n"%(str(self.posdict), str(list(self.items.keys())))
        return s

    def dump_to_file(self, fName):
        print(json.dumps(self._to_dict))

    def addItem(self, frame=KeyFrame()):
        logger.debug("KeyFrameList.addItem: %s"%frame)

        newID = self._getNewID()
        if newID in self.items:
            raise KeyError()

        if newID in list(self.posdict.values()):
            raise KeyError()

        self.items[newID] = frame
        self.posdict[frame.pos] = newID

        # print "AFTER"
        # print self

        self._modelChanged.emit()

    def removeItem(self, ID):
        logger.debug("KeyFrameList.removeItem: %s"%ID)
        # print "REMOVE\nBEFORE"
        # print self

        self.posdict.pop(list(self.posdict.keys())[list(self.posdict.values()).index(ID)])
        self.items.pop(ID)

        # print "AFTER"
        # print self

        self._modelChanged.emit()

    def __getitem__(self, ID):
        return self.items[ID]

    def _getNewID(self):
        newID = self._countID
        self._countID += 1
        return newID

    def item_at(self, index):
        """"returns keyframe in order 0...len(items)"""
        return self.items[self.item_id_at(index)]

    def item_id_at(self, index):
        """"returns keyframe id in order 0...len(items)"""
        return list(self.posdict.values())[index]

    def pos_at(self, index):
        return list(self.posdict.keys())[index]

    def pos_at_id(self, ID):
        return list(self.posdict.keys())[list(self.posdict.values()).index(ID)]

    def update_pos(self, ID, pos):
        if pos in self.posdict:
            print("pos already there:", pos)
            return
        frame = self.items[ID]

        self.posdict.pop(self.pos_at_id(ID))
        frame.pos = pos
        self.posdict[pos] = ID

    def distribute(self, pos_start, pos_end):
        """distributes the internal data positions linearly according to their nodes position"""
        for it in self.items.values():
            print(it.pos, it.transformData.dataPos)
            it.transformData.dataPos = int(pos_start+(pos_end-pos_start)*it.pos)
            # it.transformData.dataPos = pos_start+(pos_end-pos_start)*it.pos

    def getTransform(self, pos):
        logger.debug("getTransform")

        if pos<self.pos_at(0):
            return self.item_at(0).transformData
        if pos>self.pos_at(-1):
            return self.item_at(-1).transformData

        if pos in self.posdict:
            return self.items[self.posdict[pos]].transformData

        ind = self.posdict.bisect(pos)
        frameLeft, frameRight = self.item_at(ind-1), self.item_at(ind)

        # linear interpolating
        if np.abs(frameRight.pos-frameLeft.pos)<1.e-7:
            lam = 0.
        else:
            lam = (1.*pos-frameLeft.pos)/(frameRight.pos-frameLeft.pos)

        newTrans = TransformData.interp(frameLeft.transformData,
                                        frameRight.transformData,
                                        lam,
                                        create_interp_func(frameLeft.interp_elasticity))

        return newTrans

    def _to_JSON(self):
        return json.dumps(self, cls=KeyFrameEncoder)

    @classmethod
    def _from_JSON(self, jsonStr):
        return json.loads(jsonStr, cls=KeyFrameDecoder)


"""JSON routines to save and load from file"""


class KeyFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray) and obj.ndim==1:
            return obj.tolist()

        elif isinstance(obj, Quaternion):
            return obj.data.tolist()

        elif isinstance(obj, sortedcontainers.SortedDict):
            return dict(obj)

        elif isinstance(obj, (
                KeyFrame,
                KeyFrameList,
                TransformData,
                spimagine.models.transform_model.TransformData)):
            return obj.__dict__

        elif isinstance(obj, np.generic):
            return np.asscalar(obj)

        return json.JSONEncoder.default(self, obj)


"""
OLD

    {"keyDict": {"1": {"transformData": {"dataPos": 0, "quatRot": [1.0, 0.0, 0.0, 0.0], "zoom": 1, "bounds": [-1, 1, -1, 1, -1, 1]}, "tFrame": 0}, "2": {"transformData": {"dataPos": 0, "quatRot": [1.0, 0.0, 0.0, 0.0], "isBox":true,"zoom": 1, "bounds": [-1, 1, -1, 1, -1, 1]}, "tFrame": 1}}, "_countID": 2, "tFrames": [[0, 1], [1, 2]]}


NEW

{"items": {"0": {"transformData": {"dataPos": 0, "quatRot": [1.0, 0.0, 0.0, 0.0], "maxVal": 100.0, "isIso": false, "minVal": 0.0, "zoom": 1, "bounds": [-1, 1, -1, 1, -1, 1], "isBox": true, "alphaPow": 0.0, "translate": [0, 0, 0], "gamma": 1.0}, "pos": 0}}, "_countID": 1, "posdict": {"0": 0}}
"""


class KeyFrameDecoder(json.JSONDecoder):
    def decode(self, s, classname=""):
        # print classname," XXXX\n" ,s
        if classname=="":

            dec = json.JSONDecoder.decode(self, s)
            ret = KeyFrameList()
            ret._countID = dec["_countID"]
            ret.posdict = self.decode(dec["posdict"], "posdict")
            ret.items = self.decode(dec["items"], "items")
            return ret

        elif classname=="posdict":
            return sortedcontainers.SortedDict((float(k), int(v)) for k, v in six.iteritems(s))

        elif classname=="items":
            return dict((int(k), KeyFrame(v["pos"], self.decode(v["transformData"], "transformData"))) for k, v in
                        six.iteritems(s))

        elif classname=="transformData":
            t = TransformData()
            t.__dict__.update(s)

            t.quatRot = Quaternion(*t.quatRot)
            t.bounds = np.array(t.bounds)
            t.translate = np.array(t.translate)

            return t


def test_interpolation():
    k = KeyFrameList()
    k.addItem(KeyFrame(.5, TransformData(quatRot=Quaternion(.71, .71, 0, 0))))

    for t in np.linspace(0, 1, 10):
        print(t, k.getTransform(t))


def test_shuffle():
    k = KeyFrameList()

    k.addItem(KeyFrame(.5, TransformData(zoom=.5, quatRot=Quaternion(.71, .71, 0, 0), bounds=[0]*6)))

    # print k
    # for t in np.linspace(-.1,1.2,11):
    #     print t, k.getTransform(t).zoom

    np.random.seed(0)

    def rand_ID(k):
        # just pick from within the border...
        return k.item_id_at(np.random.randint(1, len(k.items)-1))

    # adding some
    for i in range(4):
        k.addItem(KeyFrame(np.random.uniform(0, 1)))

    print(k)
    # shuffle them
    for i in range(100):
        print("+++++++++++++++++")
        k.addItem(KeyFrame(np.random.uniform(0, 1)))

        ID = rand_ID(k)
        print("moving %s"%ID)
        k.update_pos(ID, np.random.uniform(0, 1.))

        ID = rand_ID(k)
        print("removing %s"%ID)
        k.removeItem(ID)


if __name__=='__main__':
    k = KeyFrameList()

    k.addItem(KeyFrame(0, TransformData()))

    k.addItem(KeyFrame(1, TransformData(zoom=.0, quatRot=Quaternion(.71, .71, 0, 0), bounds=[0]*6)))

    print(k.getTransform(0.2))
    #
    #
    # s = k._to_JSON()
    #
    # print s
    #
    # k2 = KeyFrameList._from_JSON(s)
    #
    #
    # print k2.getTransform(.1)
    #
    #
    # k3 = KeyFrameList._from_JSON(open("test.json","r").read())
