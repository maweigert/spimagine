
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



def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
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
    def __init__(self,graphWidget, keyList, ID,fixed = False):
        super(KeyNode, self).__init__()
        self.graph = graphWidget

        self.shapeSize = 6*array([-1,-1.,2,2])
        self.edgeList = []
        self.keyList = keyList
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
            print self.graph.keyList


        elif change == QGraphicsItem.ItemSelectedChange:
            logger.debug("selected")

        return super(KeyNode, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(KeyNode, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(KeyNode, self).mouseReleaseEvent(event)


    def delete(self):
        self.keyList.removeItem(self.ID)
        # self.graph.scene.removeItem(self)

    def contextMenuEvent(self, contextEvent):
        actionMethods = {"delete" : self.delete}
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
    HEIGHT = 100

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

        # self.setMinimumSize(300,KeyFrameScene.HEIGHT)
        self.setWindowTitle("KeyFrameView")
        self.zoom = 1.
        self.relativeAspect = 1.
        self.isListening = True


    def setDataTransformModel(self,dataModel, transformModel):
        self.dataModel, self.transformModel = dataModel, transformModel

    def setKeyListModel(self,keyList):

        self.keyList = keyList
        self.resetScene()
        self.keyList._modelChanged.connect(self.modelChanged)
        # self.keyList._itemChanged.connect(self.itemChanged)

    def setTransformModel(self,transformModel):
        self.transModel = transformModel
        self.resetScene()
        # self.keyList._modelChanged.connect(self.modelChanged)
        # self.keyList._itemChanged.connect(self.itemChanged)

    def resetScene(self):
        self.scene.clear()
        for myID in self.keyList.keyDict.keys():
            n = self.keyList._IDToN(myID)
            fixed = ( n == 0 or n == len(self.keyList.tFrames)-1)
            self.scene.addItem(KeyNode(self,self.keyList,myID,fixed))


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

        posScene = self.mapToScene(event.pos())

        if self.dataModel:
            actionMethods = {"insert keyframe" : functools.partial(self.keyList.addItem,KeyFrame(1.*posScene.x()/KeyFrameScene.WIDTH,self.dataModel.pos,self.transformModel.toTransformData()))}
            actions = {}

            object_cntext_Menu = QMenu()
            for k, meth in actionMethods.iteritems():
                actions[k] = object_cntext_Menu.addAction(k,meth)

                object_cntext_Menu.exec_(self.mapToGlobal(event.pos()))


class KeyFramePanel(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()

        self.resize(500, 50)
        self.initUI()


    def initUI(self):
        self.keyView =  KeyListView()



        self.startButton = QPushButton("",self)
        self.startButton.setStyleSheet("background-color: black")
        self.startButton.setIcon(QIcon(absPath("images/icon_start.png")))
        self.startButton.setIconSize(QSize(24,24))
        self.startButton.clicked.connect(self.startPlay)
        self.startButton.setMaximumWidth(24)
        self.startButton.setMaximumHeight(24)

        hbox = QHBoxLayout()
        hbox.addWidget(self.startButton)
        
        hbox.addWidget(self.keyView)

        self.setLayout(hbox)

    def startPlay(self,evt):
        pass



class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(500, 100)
        self.setWindowTitle("Key Frame View")   

        

        self.keyPanel = KeyFramePanel()

        dataModel = DataModel(dataContainer = DemoData(50),prefetchSize = 0)
        transModel = TransformModel()

        dataModel.setPos(2)
        self.keyPanel.keyView.setDataTransformModel(dataModel,transModel)

        k = KeyFrameList()
        k.addItem(KeyFrame(0.4))
        k.addItem(KeyFrame(0.9))

        self.keyPanel.keyView.setKeyListModel(k)

        self.keyPanel.keyView.setTransformModel(None)
        
        self.setCentralWidget(self.keyPanel)

        self.setStyleSheet("background-color:black;")




if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()


    app.exec_()
