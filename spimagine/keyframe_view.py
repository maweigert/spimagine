from numpy import *
import os
import functools
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from keyframe_model import KeyFrame, KeyFrameList, TransformData

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
            print "changed"
        if change == QGraphicsItem.ItemSelectedChange:
            print "selected!"

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
    def __init__(self,graphWidget, pos,fixed = False):
        super(KeyNode, self).__init__()
        self.graph = graphWidget

        self.shapeSize = 6*array([-1,-1.,2,2])
        self.edgeList = []
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
            newPos = QPointF(clip(x,x1,x2),0)
            self.setPos(newPos)
            for edge in self.edgeList:
                edge.adjust()
            self.setToolTip("KeyNode: t= %.2f"%self.pos().x())

            self.graph.itemMoved()
            print "#####"
            print self.graph.keyList


        elif change == QGraphicsItem.ItemSelectedChange:
            print "selected!"


        return super(KeyNode, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(KeyNode, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(KeyNode, self).mouseReleaseEvent(event)


    def delete(self):
        self.graph.scene.removeItem(self)

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

    def mousePressEvent(self, event):
        print "Scene"
        super(KeyFrameScene, self).mousePressEvent(event)
        item = self.itemAt(event.scenePos())
        if event.button() == Qt.RightButton and  type(item) != KeyNode:
            print "Hurray"


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

        self.setMinimumSize(500,KeyFrameScene.HEIGHT)
        self.setWindowTitle("KeyFrameView")
        self.zoom = 1.
        self.relativeAspect = 1.




    def setModel(self,keyList):

        self.keyList = keyList
        self.resetScene()
        self.keyList._modelChanged.connect(self.modelChanged)

    def resetScene(self):
        print "reset!"
        self.scene.clear()
        self.addKey(self.keyList.keyFrames[0], fixed = True)
        self.addKey(self.keyList.keyFrames[-1], fixed = True)
        for k in self.keyList.keyFrames[1:-1]:
            self.addKey(k)


    def modelChanged(self):
        self.resetScene()


    def addKey(self,keyFrame, fixed = False):
        self.scene.addItem(KeyNode(self,keyFrame.tFrame*KeyFrameScene.WIDTH,fixed))


    def itemMoved(self):
        pass

    def keyPressEvent(self, event):
        key = event.key()

        super(KeyListView, self).keyPressEvent(event)

    def resizeEvent(self,event):
        print "resize"
        super(KeyListView, self).resizeEvent(event)

        self.relativeAspect = 1.*event.size().width()/KeyFrameScene.WIDTH
        print self.relativeAspect*self.zoom
        self.setTransform(QTransform.fromScale(self.relativeAspect*self.zoom, 1.))

        # self.scale(self.relativeAspect*self.zoom,1.)
        # self.fitInView(self.scene.sceneRect())


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

        actionMethods = {"insert keyframe" : functools.partial(self.keyList.addKeyFrame,1.*posScene.x()/KeyFrameScene.WIDTH)}
        actions = {}

        object_cntext_Menu = QMenu()
        for k, meth in actionMethods.iteritems():
            actions[k] = object_cntext_Menu.addAction(k,meth)

        object_cntext_Menu.exec_(self.mapToGlobal(event.pos()))




class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(300, 100)
        self.setWindowTitle("Key Frame View")

        self.keyView =  KeyListView()


        k = KeyFrameList()
        k.addKeyFrame(.5,TransformData(.5,.4,.3))
        k.addKeyFrame(.9,TransformData(.5,.4,.3))

        self.keyView.setModel(k)


        self.setCentralWidget(self.keyView)




if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
