
import logging
logger = logging.getLogger(__name__)



from numpy import *
import os
import functools
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from keyframe_model import KeyFrame, KeyFrameList
from data_model import DataModel, DemoData
from transform_model import TransformModel

from time import sleep, time



#this should fix an annoying file url drag drop bug in mac yosemite
import platform
if platform.system() =="Darwin" and platform.release()[:2] == "14":
    try:
        import Foundation
    except ImportError:
        raise("PyObjc module not found!\nIt appears you are using Mac OSX Yosemite which need that package to fix a bug")

    _SYSTEM_DARWIN_14 = True
    def _parseFileNameFix(fpath):
        return Foundation.NSURL.URLWithString_("file://"+fpath).fileSystemRepresentation()
else:
    _SYSTEM_DARWIN_14 = False



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
        logger.debug("didnt found MEIPASS!: %s "%os.path.join(base_path, myPath))

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
        pos = self.keyList[self.ID].tFrame*KeyFrameScene.WIDTH

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

        painter.drawEllipse(*self.shapeSize)
        # painter.drawPie(*(list(self.shapeSize)+[0,180*16]))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            sceneRect = self.graph.scene.sceneRect()
            x = value.toPoint().x()
            x1, x2 = sceneRect.x(),sceneRect.x()+sceneRect.width()
            pos = QPointF(clip(x,x1,x2),0)
            tFrame = clip(1.*pos.x()/KeyFrameScene.WIDTH,0.,1.)
            self.keyList[self.ID].tFrame = tFrame
            self.setPos(pos)
            for edge in self.edgeList:
                edge.adjust()
            self.setToolTip("KeyNode: t= %.2f"%self.pos().x())

            self.graph.itemMoved()
            # print self.graph.keyList


        elif change == QGraphicsItem.ItemSelectedChange:
            logger.debug("selected")

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
        # self.graph.scene.removeItem(self)

    def updateTransformData(self):
        self.keyList[self.ID].transformData = self.transformModel.toTransformData()

    def setTransformData(self):
        self.transformModel.fromTransformData(self.keyList[self.ID].transformData)

    def contextMenuEvent(self, contextEvent):
        actionMethods = {"delete" : self.delete, "update" : self.updateTransformData}
        actions = {}

        object_cntext_Menu = QMenu()
        for k, meth in actionMethods.iteritems():
            actions[k] = object_cntext_Menu.addAction(k,meth)

        if self.fixed:
            actions["delete"].setEnabled(False)

        position=QCursor.pos()
        object_cntext_Menu.exec_(position)


class KeyFrameScene(QGraphicsScene):
    WIDTH = 100
    HEIGHT = 50

    # def mousePressEvent(self, event):
    #     print "Scene"
    #     super(KeyFrameScene, self).mousePressEvent(event)
    #     item = self.itemAt(event.scenePos())
    #     if event.button() == Qt.RightButton and  type(item) != KeyNode:
    #         print "Hurray"


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
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.setSceneRect(0, -KeyFrameScene.HEIGHT/2, KeyFrameScene.WIDTH, KeyFrameScene.HEIGHT)

        self.setScene(self.scene)

        # self.setMinimumSize(300,20)
        self.setWindowTitle("KeyFrameView")
        self.zoom = 1.
        self.relativeAspect = 1.
        self.isListening = True

        # self.setTransformModel(TransformModel())

        # self.setKeyListModel(KeyFrameList())

        self.resetModels(TransformModel(),KeyFrameList())

    def resetModels(self,transformModel,keyList= KeyFrameList):
        self.keyList = keyList
        logger.debug("resetModels, : keyList = %s"%self.keyList)
        self.transformModel = transformModel
        self.resetScene()
        self.keyList._modelChanged.connect(self.modelChanged)


    def setKeyListModel(self,keyList):

        self.keyList = keyList
        self.resetScene()
        self.keyList._modelChanged.connect(self.modelChanged)
        # self.keyList._itemChanged.connect(self.itemChanged)

    def setTransformModel(self,transformModel):
        self.transformModel = transformModel
        self.resetScene()
        # self.keyList._modelChanged.connect(self.modelChanged)
        # self.keyList._itemChanged.connect(self.itemChanged)

    def resetScene(self):
        logger.debug("resetScene: %s",self.keyList)
        self.scene.clear()
        for myID in self.keyList.keyDict.keys():
            n = self.keyList._IDToN(myID)
            fixed = ( n == 0 or n == len(self.keyList.tFrames)-1)
            self.scene.addItem(KeyNode(self,self.transformModel,self.keyList,myID,fixed))


    def modelChanged(self):
        self.resetScene()


    def addKey(self,keyFrame, fixed = False):
        pass

    def itemMoved(self):
        pass

    def keyPressEvent(self, event):
        key = event.key()

        super(KeyListView, self).keyPressEvent(event)

    def resizeEvent(self,event):
        # super(KeyListView, self).resizeEvent(event)

        self.relativeAspect = 1.*event.size().width()/KeyFrameScene.WIDTH
        # print event.size()
        self.setTransform(QTransform.fromScale(self.relativeAspect*self.zoom, 1.))
        # self.resize(event.size().width(),KeyFrameScene.HEIGHT)


    def wheelEvent(self, event):
        factor = 1.41 ** (-event.delta() / 240.0)
        self.zoom = clip(self.zoom*factor,1.,1.e3)

        self.setTransform(QTransform.fromScale(self.relativeAspect*self.zoom, 1.))

    def drawBackground(self,painter, rect):
        sceneRect = self.sceneRect()
        painter.setBrush(Qt.black)
        painter.drawRect(sceneRect)


    def contextMenuEvent(self, event):
        # super(KeyListView,self).contextMenuEvent(event)

        item = self.scene.itemAt(self.mapToScene(event.pos()))
        if type(item) == KeyNode:
            super(KeyListView,self).contextMenuEvent(event)
            return

        else:
            posScene = self.mapToScene(event.pos())

            actionMethods = {"insert keyframe" : functools.partial(self.keyList.addItem,KeyFrame(1.*posScene.x()/KeyFrameScene.WIDTH,self.transformModel.toTransformData()))}
            actions = {}

            object_cntext_Menu = QMenu()
            for k, meth in actionMethods.iteritems():
                actions[k] = object_cntext_Menu.addAction(k,meth)

                object_cntext_Menu.exec_(self.mapToGlobal(event.pos()))





class RecordThread(QThread):
    notifyProgress = pyqtSignal(int)
    def __init__(self,glWidget,keyView):
        super(RecordThread,self).__init__()
        self.glWidget = glWidget
        self.keyView = keyView

    def run(self):
        for i in range(100):
            logger.debug("thread: %s",i )
            trans = self.keyView.keyList.getTransform(1.*i/100.)
            self.keyView.transformModel.fromTransformData(trans)
            self.notifyProgress.emit(i)
            self.glWidget.saveFrame("output.png")
            sleep(0.1)

class KeyFramePanel(QWidget):
    def __init__(self, glWidget):
        super(QWidget,self).__init__()
        self.glWidget = glWidget
        self.resize(500, 50)
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


        self.playButton = QPushButton("",self)
        self.playButton.setStyleSheet("background-color: black")
        # logger.debug("absPATH: %s"%absPath("images/icon_play.png"))
        self.playButton.setIcon(QIcon(absPath("images/icon_start.png")))
        self.playButton.setIconSize(QSize(24,24))
        self.playButton.clicked.connect(self.onPlay)
        self.playButton.setMaximumWidth(24)
        self.playButton.setMaximumHeight(24)

        self.recordButton = QPushButton("",self)
        self.recordButton.setStyleSheet("background-color: black")
        # logger.debug("absPATH: %s"%absPath("images/icon_record.png"))
        self.recordButton.setIcon(QIcon(absPath("images/icon_record.png")))
        self.recordButton.setIconSize(QSize(24,24))
        self.recordButton.clicked.connect(self.onRecord)
        self.recordButton.setMaximumWidth(24)
        self.recordButton.setMaximumHeight(24)

        self.saveButton = QPushButton("",self)
        self.saveButton.setStyleSheet("background-color: black")
        # logger.debug("absPATH: %s"%absPath("images/icon_play.png"))
        self.saveButton.setIcon(QIcon(absPath("images/icon_save.png")))
        self.saveButton.setIconSize(QSize(24,24))
        self.saveButton.clicked.connect(self.onSave)
        self.saveButton.setMaximumWidth(24)
        self.saveButton.setMaximumHeight(24)

        self.trashButton = QPushButton("",self)
        self.trashButton.setStyleSheet("background-color: black")
        # logger.debug("absPATH: %s"%absPath("images/icon_play.png"))
        self.trashButton.setIcon(QIcon(absPath("images/icon_trash.png")))
        self.trashButton.setIconSize(QSize(24,24))
        self.trashButton.clicked.connect(self.onTrash)
        self.trashButton.setMaximumWidth(24)
        self.trashButton.setMaximumHeight(24)

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0,100)
        # self.recordThread = RecordThread(self.glWidget,self.keyView)
        # self.recordThread.notifyProgress.connect(self.onRecordProgress)



        hbox = QHBoxLayout()


        hbox.addWidget(self.playButton)
        hbox.addWidget(self.recordButton)
        hbox.addWidget(self.saveButton)
        hbox.addWidget(self.trashButton)

        vbox = QVBoxLayout()
        vbox.addWidget(self.keyView)
        vbox.addWidget(self.progressBar)

        hbox.addLayout(vbox)

        self.setLayout(hbox)
        self.setFrameNumber(100)

        self.setDirName("./")
        self.t = 0


    def resetModels(self,transformModel,keyList=KeyFrameList()):
        logger.debug("keyPanel.resetModel: keyList = %s\n"%keyList)
        self.transformModel = transformModel
        self.keyView.resetModels(transformModel,keyList)

    def setTransformModel(self,transformModel):
        self.transformModel = transformModel
        self.keyView.setTransformModel(transformModel)

    def onPlay(self,evt):
        if self.playTimer.isActive():
            self.playTimer.stop()
            self.playButton.setIcon(QIcon(absPath("images/icon_start.png")))

        else:
            self.playTimer.start()
            self.playButton.setIcon(QIcon(absPath("images/icon_pause.png")))

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


        trans = self.keyView.keyList.getTransform(1.*self.recordPos/self.nFrames)
        self.keyView.transformModel.fromTransformData(trans)
        self.glWidget.saveFrame(os.path.join(self.dirName,"output_%s.png"%(str(self.recordPos).zfill(int(log10(self.nFrames)+1)))))
        self.progressBar.setValue(100*self.recordPos/self.nFrames)


    def onPlayTimer(self):
        self.t = (self.t+0.01)%1.

        trans = self.keyView.keyList.getTransform(self.t)
        # print self.t,trans

        self.keyView.transformModel.fromTransformData(trans)


        # print "TIME to set ", time()-self.a

        # self.a = time()

        # if self.glWidget.dataModel.pos == self.glWidget.dataModel.sizeT()-1:
        #     self.playDir = 1-2*self.loopBounce
        # if self.glWidget.dataModel.pos == 0:
        #     self.playDir = 1

        # newpos = (self.glWidget.dataModel.pos+self.playDir)%self.glWidget.dataModel.sizeT()
        # self.glWidget.transform.setPos(newpos)
        # self.glWidget.dataModel.setPos(newpos)

    def onSave(self):
        fName = QFileDialog.getSaveFileName(self, "save as json file", "", "json files (*.json)")
        if fName:
            self.save_to_JSON(fName)


    def onTrash(self):
        self.keyView.setKeyListModel(KeyFrameList())
            
    def save_to_JSON(self,fName):
        with open(fName,"w") as f:
            f.write(self.keyView.keyList._to_JSON())

    def load_from_JSON(self,fName):
        with open(fName,"r") as f:
            try:
                newKeyList = KeyFrameList._from_JSON(f.read())
                self.keyView.setKeyListModel(newKeyList)
            except:
                print "not a valid keyframe json file: %s"%fName


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

        
    def dropEvent(self, event):

        for url in event.mimeData().urls():
            event.accept()
            path = url.toLocalFile().toLocal8Bit().data()

            if _SYSTEM_DARWIN_14:
                path = _parseFileNameFix(path)

            self.load_from_JSON(path)

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(500, 100)
        self.setWindowTitle("Key Frame View")



        self.keyPanel = KeyFramePanel(None)

        dataModel = DataModel(dataContainer = DemoData(50),prefetchSize = 0)
        transModel = TransformModel()
        transModel.setModel(dataModel)

        dataModel.setPos(2)

        self.keyPanel.keyView.setTransformModel(transModel)

        k = KeyFrameList()
        k.addItem(KeyFrame(0.4))
        # k.addItem(KeyFrame(0.9))



        self.keyPanel.keyView.setKeyListModel(k)


        self.setCentralWidget(self.keyPanel)

        self.setStyleSheet("background-color:black;")




if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    # win.keyPanel.load_from_JSON("test.json")


    app.exec_()
