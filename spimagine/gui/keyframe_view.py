
from __future__ import absolute_import, print_function, division

import logging
import six
logger = logging.getLogger(__name__)



from numpy import *
import numpy as np
import os
import functools
import math

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


from time import sleep, time

from collections import OrderedDict 


from spimagine.models.keyframe_model import KeyFrame, KeyFrameList
from spimagine.models.data_model import DataModel, DemoData


from spimagine.gui.gui_utils import  createImageCheckbox,createStandardButton

from spimagine.models.transform_model import TransformModel


import spimagine




def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:

        base_path = os.path.abspath(os.path.dirname(__file__))
        logger.debug("didnt found MEIPASS...: %s "%os.path.join(base_path, myPath))

        return os.path.join(base_path, myPath)



class KeyEdge(QGraphicsItem):
    def __init__(self, sourceKeyNode, destKeyNode):
        super(KeyEdge, self).__init__()

        self.sourcePoint = QPointF()
        self.destPoint = QPointF()

        # self.setAcceptedMouseButtons(Qt.NoButton)
        # self.setFlag(QGraphicsItem.ItemIsMovable)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        # self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(0)


        self.source = sourceKeyNode
        self.dest = destKeyNode
        self.source.addKeyEdge(self)
        self.dest.addKeyEdge(self)
        self.adjust()


    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            logger.debug("changed")
        if change == QGraphicsItem.ItemSelectedChange:
            logger.debug("selected")

        return super(KeyEdge, self).itemChange(change, value)


    def adjust(self):
        if not self.source or not self.dest:
            return

        line = QLineF(self.mapFromItem(self.source, 0, 0),
                self.mapFromItem(self.dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()
        self.sourcePoint = line.p1()
        self.destPoint = line.p2()

    def boundingRect(self):
        if not self.source or not self.dest:
            return QRectF()

        penWidth = 1.0
        extra = 5

        return QRectF(self.sourcePoint,
                QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                        self.destPoint.y() - self.sourcePoint.y()+10)).normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        # Draw the line itself.
        line = QLineF(self.sourcePoint, self.destPoint)

        if line.length() == 0.0:
            return

        if option.state & QStyle.State_Sunken:
            painter.setPen(QPen(Qt.lightGray, 2, Qt.SolidLine))
        else:
            painter.setPen(QPen(Qt.gray, 2, Qt.SolidLine))

        painter.drawLine(line)


class KeyNode(QGraphicsItem):
    def __init__(self,graphWidget, transform,keyList, ID,fixed = False):
        super(KeyNode, self).__init__()
        self.graph = graphWidget

        self.shapeSize = 8*array([-1,-1.,2,2])
        self.edgeList = []
        self.keyList = keyList
        self.transformModel = transform
        self.ID = ID
        pos = self.keyList[self.ID].pos*KeyFrameScene.WIDTH

        self.setPos(QPointF(pos,0))

        self.fixed = fixed

        if not self.fixed:
            self.setFlag(QGraphicsItem.ItemIsMovable)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        # self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        if fixed:
            self.setZValue(0.5)
        else:
            self.setZValue(1)
        self.setToolTip("Keynode")
        # self.updateTransformData()

    def addKeyEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList


    def boundingRect(self):
        return QRectF(*self.shapeSize)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(*self.shapeSize)
        return path

    def paint(self, painter, option, widget):
        gradient = QRadialGradient(.2*self.shapeSize[0],
                                         .2*self.shapeSize[1], .3*self.shapeSize[2])
        if option.state & (QStyle.State_Sunken | QStyle.State_Selected) :
            gradient.setColorAt(1, QColor(51, 153, 204,255))
            gradient.setColorAt(0, QColor(255,255,255,255))

        else:
            gradient.setColorAt(0, Qt.gray)
            gradient.setColorAt(1, Qt.darkGray)

        painter.setBrush(QBrush(gradient))

        painter.setPen(QPen(Qt.black, 0))
        painter.setPen(QPen(Qt.transparent, 0))

        # painter.drawEllipse(*self.shapeSize)
        rect = QRect(*self.shapeSize)
        # painter.drawRect(rect)
        painter.drawRoundedRect(rect,70.,70.,mode=Qt.RelativeSize)

        # painter.drawPie(*(list(self.shapeSize)+[0,180*16]))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            sceneRect = self.graph.scene.sceneRect()
            x = value.toPoint().x()
            x1, x2 = sceneRect.x(),sceneRect.x()+sceneRect.width()
            pos = QPointF(clip(x,x1,x2),0)
            tpos = clip(1.*pos.x()/KeyFrameScene.WIDTH,0.,1.)
            # self.keyList[self.ID].tFrame = tFrame

            self.keyList.update_pos(self.ID, tpos)
            self.setPos(pos)
            for edge in self.edgeList:
                edge.adjust()
            self.setToolTip("KeyNode: t= %.2f"%self.pos().x())

            self.graph.itemMoved()
            # print self.graph.keyList


        elif change == QGraphicsItem.ItemSelectedChange:
            logger.debug("keynode selected")

        return super(KeyNode, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(KeyNode, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(KeyNode, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self,event):
        super(KeyNode,self).mouseDoubleClickEvent(event)
        self.setTransformData()

    def delete(self):
        self.keyList.removeItem(self.ID)
        # self.graph.resetScene()

    def changeElasticity(self):
        old_val  = self.keyList[self.ID].interp_elasticity
        new_val ,success = QInputDialog.getDouble(None,"new elasticity",
                                              "elasticity = 0: linear interpolation\nelasticity > 0 (e.g. 10): sigmoid interpolation ",
                                              value = old_val,
                                              min = 0, max = 30)
        if success:
            self.keyList[self.ID].interp_elasticity = new_val


    def showProperties(self):
        QMessageBox.about(None, "KeyFrame", str(self.keyList[self.ID]))

    def updateTransformData(self):
        if self.transformModel is None:
            self.keyList[self.ID].transformData = TransformData()
        else:
            self.keyList[self.ID].transformData = self.transformModel.toTransformData()

    def setTransformData(self):
        self.transformModel.fromTransformData(self.keyList[self.ID].transformData)

    def contextMenuEvent(self, contextEvent):
        actionMethods = OrderedDict((("update",self.updateTransformData),
                                     ("delete",self.delete),
                                     ("elasticity",self.changeElasticity),
                                     ("properties" ,self.showProperties)))

        actions = OrderedDict()

        object_cntext_Menu = QMenu()
        for k, meth in six.iteritems(actionMethods):
            actions[k] = object_cntext_Menu.addAction(k,meth)

        if self.fixed:
            actions["delete"].setEnabled(False)

        position=QCursor.pos()
        object_cntext_Menu.exec_(position)


class KeyFrameScene(QGraphicsScene):
    WIDTH = 100
    HEIGHT = 10

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()


    # def __init__(self, parent):
    #     super(KeyFrameScene, self).__init__(parent)



class KeyListView(QGraphicsView):
    def __init__(self):
        super(KeyListView, self).__init__()

        self.setVerticalScrollBarPolicy (Qt.ScrollBarAlwaysOff)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Fixed)

        self.scene = KeyFrameScene(self)

        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.setSceneRect(0, -KeyFrameScene.HEIGHT//2, KeyFrameScene.WIDTH, KeyFrameScene.HEIGHT)

        self.setScene(self.scene)

        # self.scale(1,.1)

        # self.setMinimumSize(300,20)
        self.setWindowTitle("KeyFrameView")
        self.zoom = 1.
        self.relativeAspect = 1.
        self.isListening = True

        self.connect_to_transform(None)
        self.setModel(KeyFrameList())

    def connect_to_transform(self,transformModel):
        self.transformModel = transformModel

    # def reset(self,transformModel):
    #     self.keyList = KeyFrameList()

    #     self.keyList.addItem(KeyFrame(0.))
    #     self.keyList.addItem(KeyFrame(1.))

    #     print self.keyList

    #     logger.debug("reset, : keyList = %s"%self.keyList)
    #     self.transformModel = transformModel
    #     self.resetScene()
    #     self.keyList._modelChanged.connect(self.modelChanged)


    # def resetModels(self,transformModel,keyList= KeyFrameList):
    #     self.keyList = keyList
    #     logger.debug("resetModels, : keyList = %s"%self.keyList)
    #     self.transformModel = transformModel
    #     self.resetScene()
    #     self.keyList._modelChanged.connect(self.modelChanged)

    def setModel(self,keyList = KeyFrameList()):
        logger.debug("setModel: %s",keyList)
        self.keyList = keyList
        self.resetScene()
        # for it in self.scene.items():
        #     it.updateTransformData()

        self.keyList._modelChanged.connect(self.modelChanged)

    # def setKeyListModel(self,keyList):
    #     self.keyList = keyList
    #     self.resetScene()
    #     self.keyList._modelChanged.connect(self.modelChanged)
        # self.keyList._itemChanged.connect(self.itemChanged)


    # def setTransformModel(self,transformModel):
    #     self.transformModel = transformModel
    #     self.resetScene()
    #     # self.keyList._modelChanged.connect(self.modelChanged)
    #     # self.keyList._itemChanged.connect(self.itemChanged)

    def resetScene(self):
        logger.debug("resetScene: %s",self.keyList)
        self.scene.clear()
        for i, (pos,ID) in enumerate(six.iteritems(self.keyList.posdict)):
            fixed = ( i == 0 or i == len(self.keyList.posdict)-1)
            self.scene.addItem(KeyNode(self,self.transformModel,self.keyList,ID,fixed))


    def modelChanged(self):
        logger.debug("model Changed")
        self.resetScene()


    def addKey(self,keyFrame, fixed = False):
        pass

    def itemMoved(self):
        pass

    def keyPressEvent(self, event):
        key = event.key()

        super(KeyListView, self).keyPressEvent(event)

    def resizeEvent(self,event):
        self.relativeAspect = 1.*event.size().width()/KeyFrameScene.WIDTH
        self.setTransform(QTransform.fromScale(self.relativeAspect*self.zoom, 1.))

    def wheelEvent(self, event):
        factor = 1.41 ** (-event.angleDelta().y()/200.0)
        self.zoom = clip(self.zoom*factor,1.,1.e3)

        self.setTransform(QTransform.fromScale(self.relativeAspect*self.zoom, 1.))

    def drawBackground(self,painter, rect):
        sceneRect = self.sceneRect()
        # painter.setBrush(Qt.black)
        painter.setBrush(QColor(50,50,50))
        painter.drawRect(sceneRect)


    def contextMenuEvent(self, event):

        item = self.scene.itemAt(self.mapToScene(event.pos()), self.transform())

        if type(item) == KeyNode:
            super(KeyListView,self).contextMenuEvent(event)
            return

        else:
            posScene = self.mapToScene(event.pos())

            actionMethods = {"insert keyframe" : functools.partial(self.keyList.addItem,KeyFrame(1.*posScene.x()/KeyFrameScene.WIDTH,self.transformModel.toTransformData()))}
            actions = {}

            object_cntext_Menu = QMenu()
            for k, meth in six.iteritems(actionMethods):
                actions[k] = object_cntext_Menu.addAction(k,meth)

                object_cntext_Menu.exec_(self.mapToGlobal(event.pos()))


    def load_from_JSON(self,fName):
        with open(fName,"r") as f:
            try:
                k = KeyFrameList._from_JSON(f.read())
                self.setModel(k)
                
            except Exception as e:
                print(e)
                print("not a valid keyframe json file: %s"%fName)
                

    def dropEvent(self, event):
        logger.debug("dropping...")
        for url in event.mimeData().urls():
            event.accept()
            path = url.toLocalFile().toLocal8Bit().data()

            if spimagine.config.__SYSTEM_DARWIN__:
                path = spimagine.config._parseFileNameFix(path)

            self.load_from_JSON(path)



class KeyFramePanel(QWidget):
    _keyTimeChanged = pyqtSignal(float)


    def __init__(self, glWidget):
        super(KeyFramePanel,self).__init__()
        self.glWidget = glWidget
        self.resize(500, 30)
        self.initUI()


    def initUI(self):
        self.keyView =  KeyListView()

        self.setAcceptDrops(True)

        self.playTimer = QTimer(self)
        self.playTimer.setInterval(30)
        self.playTimer.timeout.connect(self.onPlayTimer)
        self.recordTimer = QTimer(self)
        self.recordTimer.setInterval(30)
        self.recordTimer.timeout.connect(self.onRecordTimer)


        self.playButton = createStandardButton(self,
                        fName = absPath("images/icon_start.png"),
                        method = self.onPlay,
                        tooltip = "play animation")
        self.playButton.setMaximumWidth(24)
        self.playButton.setMaximumHeight(24)


        self.recordButton = createStandardButton(self,
                        fName = absPath("images/icon_record.png"),
                        method = self.onRecord,
                        tooltip = "render images to folder")

        self.recordButton.setMaximumWidth(24)
        self.recordButton.setMaximumHeight(24)


        self.distributeButton  = createStandardButton(self,
                        fName = absPath("images/icon_distribute.png"),
                        method = self.onDistribute,
                        tooltip = "sync data timepoints to data keyframe position")

        self.distributeButton.setMaximumWidth(24)
        self.distributeButton.setMaximumHeight(24)

        self.saveButton = createStandardButton(self,
                        fName = absPath("images/icon_save.png"),
                        method = self.onSave,
                        tooltip = "save keyframes as json")


        self.saveButton.setMaximumWidth(24)
        self.saveButton.setMaximumHeight(24)

        self.trashButton =createStandardButton(self,
                        fName = absPath("images/icon_trash.png"),
                        method = self.onTrash,
                        tooltip = "delet all keyframes")

        self.trashButton.setMaximumWidth(24)
        self.trashButton.setMaximumHeight(24)


        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        self.slider.setFocusPolicy(Qt.ClickFocus)
        self.slider.setTracking(False)

        self.slider.setRange(0,100)
        self.slider.setStyleSheet("height: 12px; border = 0px;")


        hbox = QHBoxLayout()


        hbox.addWidget(self.playButton)
        hbox.addWidget(self.recordButton)
        hbox.addWidget(self.distributeButton)
        hbox.addWidget(self.saveButton)

        hbox.addWidget(self.trashButton)
        hbox.addWidget(self.keyView)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.slider)

        def _set_value_without_emitting(val):
            old = self.slider.blockSignals(True)
            self.slider.setValue(int(100*val))
            self.slider.blockSignals(old)
            
        self._keyTimeChanged.connect(_set_value_without_emitting)
        
        self.slider.valueChanged.connect(lambda x:self.setKeyTime(x/100.))

        self.setLayout(vbox)
        self.setFrameNumber(100)

        self.setDirName("./")
        self.t = 0


    def connect_to_transform(self, transform = None ):
        if not transform:
            transform = TransformModel()
            
        logger.debug("keyPanel.connect_to_transform\n")
        self.keyView.connect_to_transform(transform)

    def setModel(self,keyList = None):
        if not keyList:
            keyList=KeyFrameList()
            
        logger.debug("keyPanel.setModel: keyList = %s\n"%keyList)
        self.keyView.setModel(keyList)

    # def resetModels(self,transformModel,keyList=KeyFrameList()):
    #     logger.debug("keyPanel.resetModel: keyList = %s\n"%keyList)
    #     self.transformModel = transformModel
    #     self.keyView.resetModels(transformModel,keyList)

    # def reset(self,transformModel):
    #     self.transformModel = transformModel
    #     self.keyView.reset(transformModel)

    def onPlay(self,evt):
        if self.playTimer.isActive():
            self.playTimer.stop()
            self.playButton.setIcon(QIcon(absPath("images/icon_start.png")))

        else:
            self.playTimer.start()
            self.playButton.setIcon(QIcon(absPath("images/icon_pause.png")))


    def onDistribute(self,e):
        if self.keyView.transformModel:
            pos1 = self.keyView.keyList.getTransform(0).dataPos
            pos2 = self.keyView.keyList.getTransform(1.).dataPos
            self.keyView.keyList.distribute(pos1, pos2)
            # self.keyView.keyList.distribute()

            
    def onRecord(self,evt):
        if self.recordTimer.isActive():
            self.recordTimer.stop()
            self.recordButton.setIcon(QIcon(absPath("images/icon_record.png")))
        else:
            self.recordPos = 0
            self.recordButton.setIcon(QIcon(absPath("images/icon_record_on.png")))
            self.recordTimer.start()


    def setFrameNumber(self,nFrames):
        self.nFrames = nFrames

    def setDirName(self,dirName):
        logger.debug("setDirName %s"%dirName)
        self.dirName = str(dirName)

    def onRecordTimer(self):
        self.recordPos  += 1
        if self.recordPos > self.nFrames:
            self.recordTimer.stop()
            self.recordButton.setIcon(QIcon(absPath("images/icon_record.png")))
            return

        self.setKeyTime(1.*self.recordPos/self.nFrames)

        self.glWidget.saveFrame(os.path.join(self.dirName,"output_%s.png"%(str(self.recordPos).zfill(int(log10(self.nFrames)+1)))))



    def setKeyTime(self,newTime):
        self.t = np.clip(newTime,0,1.)
        logger.debug("set key time to %s"%self.t)

        if self.keyView.transformModel:
            self.keyView.transformModel.fromTransformData(self.keyView.keyList.getTransform(newTime))


        self._keyTimeChanged.emit(self.t)


    def onPlayTimer(self):
        self.setKeyTime((self.t+0.01)%1.)

    def onSave(self):

        fName = QFileDialog.getSaveFileName(self, "save as json file", "", "json files (*.json)")
        if fName:
            self.save_to_JSON(fName)


    def onTrash(self):
        self.keyView.setModel(KeyFrameList())

    def save_to_JSON(self,fName):
        with open(fName,"w") as f:
            f.write(self.keyView.keyList._to_JSON())

    def load_from_JSON(self,fName):
        self.keyView.load_from_JSON(fName)
            

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(500, 40)
        self.setWindowTitle("Key Frame View")



        self.keyPanel = KeyFramePanel(None)

        dataModel = DataModel(dataContainer = DemoData(50),prefetchSize = 0)
        transModel = TransformModel()
        transModel.setModel(dataModel)

        transModel.setValueScale(0,200)
        dataModel.setPos(2)
        self.keyPanel.connect_to_transform(transModel)


        k = KeyFrameList()
        k.addItem(KeyFrame(0.))
        k.addItem(KeyFrame(1.))

        self.keyPanel.setModel(k)


        self.setCentralWidget(self.keyPanel)

        self.setStyleSheet("background-color:black;")


    # def resizeEvent(self,event):
    #     newSize = event.size()
    #     newSize.setHeight(10)
    #     self.resize(newSize)



class FooWidget(QWidget):
    def __init__(self):
        super(FooWidget,self).__init__()

        foo = KeyListView()


        slider = QSlider(Qt.Horizontal)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setTickInterval(1)
        slider.setFocusPolicy(Qt.ClickFocus)
        slider.setTracking(True)

        vbox = QVBoxLayout()
        vbox.addWidget(foo)
        vbox.addWidget(slider)

        self.setLayout(vbox)

class MainWindowEmpty(QMainWindow):

    def __init__(self):
        super(MainWindowEmpty,self).__init__()

        self.setWindowTitle("Key Frame View")

        self.foo = FooWidget()



        self.setCentralWidget(self.foo)
        self.resize(500,60)
        self.setStyleSheet("background-color:black;")

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = MainWindow()

    # win = MainWindowEmpty()

    win.show()
    win.raise_()

    app.exec_()
