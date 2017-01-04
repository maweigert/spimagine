"""
author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

from __future__ import absolute_import
from __future__ import print_function
import logging
from six.moves import zip
logger = logging.getLogger(__name__)



from PyQt5 import QtCore

from spimagine.utils.transform_matrices import *
from spimagine.utils.quaternion import Quaternion

import numpy as np

from spimagine.models.keyframe_model import TransformData


class TransformModel(QtCore.QObject):
    _maxChanged = QtCore.pyqtSignal(float)
    _minChanged = QtCore.pyqtSignal(float)
    
    _gammaChanged = QtCore.pyqtSignal(float)
    _boxChanged = QtCore.pyqtSignal(int)

    _isoChanged = QtCore.pyqtSignal(bool)

    _perspectiveChanged = QtCore.pyqtSignal(int)
    # _rotationChanged = QtCore.pyqtSignal(float,float,float,float)
    _rotationChanged = QtCore.pyqtSignal()

    _translateChanged = QtCore.pyqtSignal(float,float,float)
    _slicePosChanged =  QtCore.pyqtSignal(int)
    _sliceDimChanged =  QtCore.pyqtSignal(int)
    _boundsChanged = QtCore.pyqtSignal(float,float,float,float,float,float)

    _transformChanged = QtCore.pyqtSignal()
    _stackUnitsChanged = QtCore.pyqtSignal(float,float,float)

    _alphaPowChanged = QtCore.pyqtSignal(float)

    def __init__(self):
        super(TransformModel,self).__init__()
        self.reset()

    def _update_value(self,name,newval):
        """update self.name to newval and returns True if the
        new value indeed was different than the new"""
        if not hasattr(self,name):
            setattr(self,name,newval)
            return True

        oldval = getattr(self,name)
        is_equal = True

        if isinstance(oldval,np.ndarray):
            is_equal = np.array_equal(oldval,newval)
        elif isinstance(oldval,Quaternion):
            is_equal = np.array_equal(oldval.data,newval.data)
        else:
            is_equal = (oldval == newval)

        if not is_equal:
            setattr(self,name,newval)

        return not is_equal


    def setModel(self,dataModel):
        self.dataModel = dataModel

    def reset(self,minVal = 0., maxVal = 256.,stackUnits=None):
        logger.debug("reset:  min = %s max = %s"%(minVal,maxVal))
        self.dataPos = 0
        self.slicePos = 0
        self.sliceDim = 0
        self.zoom = 1.
        self.setIso(False)
        self.isPerspective = True
        self.setPerspective()
        self.setValueScale(minVal,maxVal)
        self.setGamma(1.)
        self.setAlphaPow(0)
        self.setBox(True)

        self.setOccStrength()
        self.setOccRadius()
        self.setOccNPoints()

        self.eye_dist_proj = 0
        self.eye_dist_cam = 0
        if not hasattr(self,"isSlice"):
            self.setShowSlice(False)

        if not stackUnits:
            stackUnits = [.1,.1,.1]
        self.setStackUnits(*stackUnits)
        self.center()


    def setIso(self,isIso):
        logger.debug("setting Iso %s"%isIso)
        if self._update_value("isIso",isIso):
            self._isoChanged.emit(isIso)
            self._transformChanged.emit()

    def setOccStrength(self, occ_strength = .15):
        if self._update_value("occ_strength",occ_strength):
            self._transformChanged.emit()

    def setOccRadius(self, val = 21):
        if self._update_value("occ_radius",val):
            self._transformChanged.emit()

    def setOccNPoints(self, val = 31):
        if self._update_value("occ_n_points",val):
            self._transformChanged.emit()

    def center(self):
        self.quatRot = Quaternion()
        self.cameraZ = 5.
        self.zoom  = 1.
        self.scaleAll = 1.
        self.setBounds(-1,1.,-1,1,-1,1)
        self.setTranslate(0,0,0)

        self.update()
        self._transformChanged.emit()

    def setTranslate(self,x,y,z):
        newtrans = np.array([x,y,z])

        if self._update_value("translate",newtrans):
            self._translateChanged.emit(x,y,z)
            self._transformChanged.emit()

    def addTranslate(self,dx,dy,dz):
        self.translate = self.translate + np.array([dx,dy,dz])
        self._translateChanged.emit(*self.translate)
        self._transformChanged.emit()

    def setBounds(self,x1,x2,y1,y2,z1,z2):
        self.bounds = np.array([x1,x2,y1,y2,z1,z2])
        self._boundsChanged.emit(x1,x2,y1,y2,z1,z2)
        self._transformChanged.emit()

    def setShowSlice(self,isSlice=True):
        self.isSlice = isSlice
        self._transformChanged.emit()

    def setSliceDim(self,dim):
        logger.debug("setSliceDim(%s)",dim)
        if dim>= 0 and dim<3:
            self.sliceDim = dim
            self._sliceDimChanged.emit(dim)
            self._transformChanged.emit()
        else:
            raise ValueError("dim should be in [0,1,2]!")

    def setSlicePos(self,pos):
        logger.debug("setSlicePos(%s)",pos)
        self.slicePos = pos
        self._slicePosChanged.emit(pos)
        self._transformChanged.emit()

    def setPos(self,pos):
        logger.debug("setPos(%s)",pos)
        self.dataPos = pos
        self.dataModel.setPos(pos)
        self._transformChanged.emit()

    def setGamma(self, gamma):
        logger.debug("setGamma(%s)",gamma)

        self.gamma = gamma
        self._gammaChanged.emit(self.gamma)
        self._transformChanged.emit()


    def setAlphaPow(self, alphaPow):
        logger.debug("setAlphaPow(%s)",alphaPow)
        self.alphaPow = alphaPow
        self._alphaPowChanged.emit(self.alphaPow)
        self._transformChanged.emit()

    def setValueScale(self,minVal,maxVal):
        logger.debug("set scale to %s,%s"%(minVal, maxVal))

        self.setMin(minVal)
        self.setMax(maxVal)

    def setMin(self,minVal):
        self.minVal = max(1.e-6,minVal)
        logger.debug("set min to %s"%(self.minVal))

        self._minChanged.emit(self.minVal)
        self._transformChanged.emit()

    def setMax(self,maxVal):
        self.maxVal = maxVal
        
        logger.debug("set max to %s"%(self.maxVal))

        self._maxChanged.emit(self.maxVal)
        self._transformChanged.emit()

    def setStackUnits(self,px,py,pz):
        self.stackUnits = px,py,pz
        self._stackUnitsChanged.emit(px,py,pz)
        self._transformChanged.emit()

    def setBox(self,isBox = True):
        self.isBox = isBox
        self._boxChanged.emit(isBox)
        self._transformChanged.emit()

    def setZoom(self,zoom = 1.):
        self.zoom = np.clip(zoom,.5,2)
        self.update()
        self._transformChanged.emit()


    def addRotation(self, angle, x, y, z):
        q = Quaternion(np.cos(angle),np.sin(angle)*x,np.sin(angle)*y,np.sin(angle)*z)
        self.setQuaternion(self.quatRot * q)

    def setRotation(self,angle,x,y,z):
        self.setQuaternion(Quaternion(np.cos(angle),np.sin(angle)*x,np.sin(angle)*y,np.sin(angle)*z))

    def setQuaternion(self,quat):
        logger.debug("set quaternion to %s",quat.data)
        self.quatRot = Quaternion.copy(quat)
        self._rotationChanged.emit()
        self._transformChanged.emit()


    def setEyeDistProj(self,eye_dist_proj = 0):
        self.eye_dist_proj = eye_dist_proj
        self.update()
        print(self.eye_dist_proj)
        self._transformChanged.emit()

    def setEyeDistCam(self,eye_dist_cam = 0.):
        self.eye_dist_cam = eye_dist_cam
        print(self.eye_dist_cam)
        self.update()
        self._transformChanged.emit()

    def update(self):
        if self.isPerspective:
            self.cameraZ = 4*(1-np.log(self.zoom)/np.log(2.))
            self.scaleAll = 1.
        else:
            self.cameraZ = 0.
            self.scaleAll = 2.5**(self.zoom-1.)

    def setPerspective(self, isPerspective = True):
        self.isPerspective = isPerspective
        if isPerspective:
            self.projection = mat4_perspective(60.,1.,.1,10)
        else:
            self.projection = mat4_ortho(-2.,2.,-2.,2.,-1.5,1.5)

        self.update()
        self._perspectiveChanged.emit(isPerspective)
        self._transformChanged.emit()

    def getProjection(self):
        return self.projection

    def getModelView(self):
        """ returns the modelview with the added internal scale from the rendered volume
        this should be used when drawing standard opengl primitives with the same trasnformation as
        the rendered model"""

        modelView = self.getUnscaledModelView()

        #scale the interns
        if hasattr(self,"dataModel"):
            Nz,Ny,Nx = self.dataModel.size()[1:]
            dx,dy,dz = self.stackUnits
            maxDim = max(d*N for d,N in zip([dx,dy,dz],[Nx,Ny,Nz]))
            mScale =  mat4_scale(1.*dx*Nx/maxDim,1.*dy*Ny/maxDim,1.*dz*Nz/maxDim)
            modelView = np.dot(modelView,mScale)

        return modelView


    def getUnscaledModelView(self):
        view  = mat4_translate(0,0,-self.cameraZ)

        model = mat4_scale(*[self.scaleAll]*3)
        model = np.dot(model,self.quatRot.toRotation4())
        model = np.dot(model,mat4_translate(*self.translate))

        # return model
        return np.dot(view,model)

    def fromTransformData(self,transformData):
        self.setQuaternion(transformData.quatRot)
        self.setZoom(transformData.zoom)
        self.setPos(transformData.dataPos)
        self.setBounds(*transformData.bounds)
        self.setBox(transformData.isBox)
        self.setIso(transformData.isIso)

        self.setAlphaPow(transformData.alphaPow)
        self.setTranslate(*transformData.translate)
        self.setValueScale(transformData.minVal,transformData.maxVal)
        # self.setGamma(transformData.gamma)

    def toTransformData(self):
        return TransformData(quatRot = self.quatRot, zoom = self.zoom,
                             dataPos = self.dataPos,
                             minVal = self.minVal,
                             maxVal = self.maxVal,
                             gamma= self.gamma,
                             translate = self.translate,
                             bounds = self.bounds,
                             isBox = self.isBox,
                             isIso = self.isIso,
                             alphaPow = self.alphaPow)

