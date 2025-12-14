"""=== Author: Assaf Ben Zur ===
mnsPicker UI Class
This is the UI defenition for the dynamic picker UI build.
The picker is essentially defined by the user using scene guides and attributes, 
this class handles the dynamic drawing of the picker into an actual live UI.
- The global width and height attributes of the window is read from the "Picker Layout Base"
- The picker buttons positions are read and interperted from the rig's 'Picker Layout Guides'
- The buttons display settings and actions are drawen from each PLG attributes, which can be editted using the PLG Setting tool.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
from pymel.core import datatypes as pmDt
import os

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import arguments as mnsArgs
from ...core import nodes as mnsNodes
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ..core import buildModules as mnsBuildModules
from ..core import controlShapes as blkCtrlShps
from ..core import blockUtility as blkUtils
from ...gui import gui as mnsGui
from ...core.globals import *

from maya import cmds
import maya.OpenMaya as OpenMaya

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui, QtOpenGL
	from PySide6.QtGui import QSurfaceFormat as QGLFormat
else:
	from PySide2 import QtCore, QtWidgets, QtGui, QtOpenGL
	from PySide2 import QtCore, QtWidgets, QtGui, QtOpenGL
	from PySide2.QtOpenGL import QGLFormat

windowBaseName = "mnsPicker2"
globalsVarName = "mnsPickerInstances"

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsPicker2.ui")
class picker2QPushButton(QtWidgets.QPushButton):
	"""A simple QPushButton re-implementation.
	This reimplementation is used to control the button's mouse events, used in 'Edit' mode.
	"""

	def __init__(self, parent = None, plgNode = None, **kwargs):
		super(picker2QPushButton, self).__init__()
		self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

		##locals
		self.pickerWin = kwargs.get("pickerWin", None)
		self.plgNode = plgNode
		self.connectedControls = []
		self.directConnectedCtrl = None
		self.filterConnectedControls()
		self.isFacial = kwargs.get("isFacial", False)
		self.last = ""

		#style
		self.plgColor = kwargs.get("plgColor", [255,255,255])
		self.textColor = kwargs.get("textColor", [255,255,255])
		self.text = kwargs.get("text", "")
		self.isBold = kwargs.get("isBold", False)
		self.isItalic = kwargs.get("isItalic", False)
		self.isUnderline = kwargs.get("isUnderline", False)
		self.fontSize = kwargs.get("fontSize", 5)
		self.positionH = kwargs.get("positionH", 0.0)
		self.positionV = kwargs.get("positionV", 0.0)
		self.scaleH = kwargs.get("scaleH", 1.0)
		self.scaleV = kwargs.get("scaleV", 1.0)

		self.setButtonStyle()
		self.setPositionAndScale()
		self.connectSignals()
		#self.setButtonVis()

	def filterConnectedControls(self):
		self.connectedControls = []

		if self.plgNode: 
			if self.plgNode.hasAttr("selectControls"):
				connectedControls = mnsUtils.splitEnumToStringList("selectControls", self.plgNode)  
				
				if connectedControls:
					plgStd = mnsUtils.validateNameStd(self.plgNode)
					if plgStd:
						for ctrlName in connectedControls:
							ctrl = mnsUtils.checkIfObjExistsAndSet(obj = ctrlName, namespace = plgStd.namespace, childOf = self.pickerWin.rigTop.node)
							if ctrl: 
								status, cnsMaster = mnsUtils.validateAttrAndGet(ctrl, "cnsMaster", None)
								if cnsMaster:
									self.connectedControls.append(cnsMaster)
								else:
									self.connectedControls.append(ctrl)
				if len(self.connectedControls) == 1 and not self.plgNode.isFree.get():
					self.directConnectedCtrl = self.connectedControls[0]

	def mouseDoubleClickEvent(self, QMouseEvent):
		self.last = "double"

		clickMode = "select"
		if QMouseEvent.buttons() == QtCore.Qt.RightButton:
			clickMode = "reset"

		self.btnDoubleClickedTrigger(clickMode = clickMode)
		return True
		#return super(picker2QPushButton, self).mouseDoubleClickEvent(QMouseEvent)

	def connectSignals(self):
		self.released.connect(self.pickerButtonClickAction)
		self.customContextMenuRequested.connect(self.rightClickedTrigger)

	def setButtonVis(self):
		if self.directConnectedCtrl:
			if not self.directConnectedCtrl.v.get():
				self.setHidden(True)

	def updateButtonVis(self):
		if self.directConnectedCtrl:
			self.setHidden(not self.directConnectedCtrl.isVisible())

	def setButtonStyle(self):
		#color and behaviour
		self.setStyleSheet("\
							QPushButton{\
										background-color: rgb(" + str(self.plgColor[0]) + "," + str(self.plgColor[1]) + "," + str(self.plgColor[2]) +"); \n\
										color: rgb(" + str(self.textColor[0]) + "," + str(self.textColor[1]) + "," + str(self.textColor[2]) + ");\n\
										border-radius:3px;\n\
										border-style:solid;\n\
										border-width:1;\n\
										border-color:#000000\
										}\n\
							QPushButton:hover{background-color:#eaeaea;}\n\
							QPushButton:pressed{background-color:#616161;border-color:#0084ff;border-width:2;}\n\
							QPushButton:checked{background-color:#616161;border-color:#0084ff;border-width:2;}"
							)

		#text
		self.setText(self.text) 
		textFont=QtGui.QFont()
		textFont.setBold(self.isBold)
		textFont.setItalic(self.isItalic)
		textFont.setUnderline(self.isUnderline)
		textFont.setPointSize(self.fontSize)
		self.setFont(textFont)
		self.setCheckable(True)

	def setPositionAndScale(self):
		self.move(self.positionH, self.positionV)
		self.resize(self.scaleH, self.scaleV)

	def pickerButtonClickAction(self):
		"""The global action trigger for any picker UI button click trigger.
		   This method will trigger the "controls selection" and the "action script" for the passed in QPushButton passed in.
		"""

		if self.last == "double":
			self.last = ""
		else:
			mode = blkUtils.getKeyboardModifiersState()
			if self.plgNode:
				if not self.plgNode.pre.get():
					blkUtils.selectRelatedControls(self.connectedControls, mode)
					blkUtils.executeActionScript(self.plgNode)
				else:
					blkUtils.executeActionScript(self.plgNode)
					blkUtils.selectRelatedControls(self.connectedControls, mode)

	def btnDoubleClickedTrigger(self, clickMode = "select"):
		"""The global action trigger for any picker UI button double click trigger.
		   This method will trigger the "hierarchy selection" and the "action script" for the passed in QPushButton passed in.
		"""

		def getControlHierarchy(control = None):
			if control:
				return [control] + [ctrl for ctrl in control.listRelatives(ad = True, type = "transform") if ctrl.nodeName().endswith("_ctrl") and ctrl.v.get() and ctrl.getShape()]

		if self.plgNode:
			plgStd = mnsUtils.validateNameStd(self.plgNode)
			controlsToSelect = []

			for ctrl in self.connectedControls:
				controlsToSelect += getControlHierarchy(ctrl)

			mode = blkUtils.getKeyboardModifiersState()
			blkUtils.selectRelatedControls(controlsToSelect, mode)
			if clickMode == "reset":
				blkUtils.resetControls(controlsToSelect)

	def rightClickedTrigger(self):
		blkUtils.resetControls(self.connectedControls)

class MnsPickerGraphicsScene(QtWidgets.QGraphicsScene):
	def __init__(self, parent=mnsUIUtils.get_maya_window(), **kwargs):
		QtWidgets.QGraphicsScene.__init__(self, parent=parent)
		
		self.sceneWidth = kwargs.get("sceneWidth", 6000)
		self.sceneHeight = kwargs.get("sceneHeight", 6000)

		self.setSceneRect(-self.sceneWidth / 2, -self.sceneHeight / 2, self.sceneWidth, self.sceneHeight)	

class MnsPickerGraphicViewWidget(QtWidgets.QGraphicsView):
	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		QtWidgets.QGraphicsView.__init__(self)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

		self.setParent(parent)
		self.bgImage = None
		self.graphicsPixmapItem = None
		self.pickerWindowObj = None

		### LOCALS
		self.sceneWidth = 60
		self.sceneHeight = 800
		self.mousePosition = QtCore.QPointF()
		self.isPanActive = False
		self.isZoomActive = False
		self.isRubberBandActive = False
		self.topLeftPosition = QtGui.QVector2D()
		self.zoomDelta = 1.0
		self.rubberBandGeometry = None
		self.currentContentRect = None
		self.tabWidget = None
		self.tnPath = None

		#INIT
		self.connectSignals()
		self.initializeGraphicsView()
		self.setCurrentStateRect()

	def connectSignals(self):
		"""Connect all UI Signals.
		"""
		pass

	def initializeGraphicsView(self):
		self.setScene(MnsPickerGraphicsScene(parent = self))
		glFormat = QGLFormat()
		
		if not int(cmds.about(version = True)) > 2024:
			glFormat.setSampleBuffers(False)
			glFormat.setDepth(True)
		
		if int(pm.about(version=True)) < 2022:
			glWidget = QtOpenGL.QGLWidget(glFormat)
			self.setViewport(glWidget)
		
		if int(cmds.about(version = True)) > 2024:
			self.setResizeAnchor(self.ViewportAnchor.AnchorViewCenter)
			self.setDragMode(self.DragMode.RubberBandDrag)
		else:
			self.setDragMode(self.RubberBandDrag)
			self.setResizeAnchor(self.AnchorViewCenter)
			
		
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(70, 70, 70, 255)))


	def getSelectedItems(self):
		return [btnProxy for btnProxy in self.scene().items() if not type(btnProxy) is QtWidgets.QGraphicsPixmapItem and btnProxy.widget().isChecked()]
		#

	def getControllersInView(self):
		if self.pickerWindowObj.visibleOnly_cbx.isChecked():
			return [btnProxy.widget().directConnectedCtrl for btnProxy in self.scene().items() if not type(btnProxy) is QtWidgets.QGraphicsPixmapItem and btnProxy.widget().isVisible() and btnProxy.widget().directConnectedCtrl]
		else:
			return [btnProxy.widget().directConnectedCtrl for btnProxy in self.scene().items() if not type(btnProxy) is QtWidgets.QGraphicsPixmapItem  and btnProxy.widget().directConnectedCtrl]

	def getContentBoundingRect(self, fromSel = False):
		returnRect = QtCore.QRect()

		if fromSel:
			selectedItems = self.getSelectedItems()
			if selectedItems:
				rec = selectedItems[0].boundingRect().getCoords()
				x1 = (rec[0] + selectedItems[0].x())
				y1 = (rec[1] + selectedItems[0].y())
				x2 = (rec[2] + selectedItems[0].x())
				y2 = (rec[3] + selectedItems[0].y())

				for item in selectedItems[1:]:
					rec = item.boundingRect().getCoords()
					if (rec[0] + item.x()) < x1: x1 = (rec[0] + item.x())
					if (rec[1] + item.y()) < y1: y1 = (rec[1] + item.y())
					if (rec[2] + item.x()) > x2: x2 = (rec[2] + item.x())
					if (rec[3] + item.y()) > y2: y2 = (rec[3] + item.y())
				returnRect.setCoords(x1, y1, x2, y2)
			else:
				returnRect = self.scene().itemsBoundingRect()
		else:
			returnRect = self.scene().itemsBoundingRect()

		return returnRect

	def getSceneCenterPosition(self):
		return self.mapToScene(QtCore.QPoint(self.width() / 2,
											 self.height() / 2))

	def setCurrentStateRect(self):
		self.currentContentRect = self.mapToScene(self.viewport().contentsRect()).boundingRect()

	def mousePressEvent(self, event):
		#first run default trigger
		QtWidgets.QGraphicsView.mousePressEvent(self, event)
		
		#set custom behaviour
		isMidMouse = False
		if int(cmds.about(version = True)) > 2024:
			if event.buttons() == QtCore.Qt.MiddleButton:
				isMidMouse = True
		else:
			if event.buttons() == QtCore.Qt.MidButton:
				isMidMouse = True
		
		###Mid-Click Pan
		if isMidMouse:
			#set local flag
			self.isPanActive = True

			#set drag mode
			if int(cmds.about(version = True)) > 2024:
				self.setDragMode(self.DragMode.ScrollHandDrag)
			else:
				self.setDragMode(self.ScrollHandDrag)

			#store mouse position
			self.mousePosition = self.mapToScene(event.pos())
		
		###Right-Click + Alt Zoom
		elif event.buttons() == QtCore.Qt.RightButton and event.modifiers() == QtCore.Qt.AltModifier:
			#set local flag
			self.isZoomActive = True

			#set drag mode
			if int(cmds.about(version = True)) > 2024:
				self.setDragMode(self.DragMode.ScrollHandDrag)
			else:
				self.setDragMode(self.ScrollHandDrag)

			#store mouse position
			self.mousePosition = self.mapToGlobal(event.pos())

			#Transform the scene based on collected data
			mousePosition2DV = QtGui.QVector2D(self.mapToGlobal(self.mousePosition))
			sceneRect = QtWidgets.QApplication.instance().primaryScreen().availableGeometry()
			self.topLeftPosition = QtGui.QVector2D(sceneRect.topLeft())
			self.zoomDelta = -self.topLeftPosition.distanceToPoint(mousePosition2DV)
			
			if int(cmds.about(version = True)) > 2024:
				self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
			else:
				self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
		
		elif event.button() == QtCore.Qt.LeftButton or event.button() == QtCore.Qt.RightButton:
			mousePosition = self.mapToScene(event.pos())
			itemUnderMouse = self.scene().itemAt(mousePosition, self.viewportTransform())
			if type(itemUnderMouse) is QtWidgets.QGraphicsPixmapItem: itemUnderMouse = None
			if not itemUnderMouse: self.isRubberBandActive = True
			else: self.isRubberBandActive = False

	def mouseMoveEvent(self, event):
		#first run default trigger
		result = QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

		#set custom behaviour
		###Left click rubber band flag
		if event.buttons() == QtCore.Qt.LeftButton:
			self.isRubberBandActive = True

		###Scene Pan case- middle mouse is clicked and moved
		if self.isPanActive:
			#calculate new center
			newSceneCenter = self.getSceneCenterPosition() - (self.mapToScene(event.pos()) - self.mousePosition)
			#center scene
			self.centerOn(newSceneCenter)

		###Scene Zoom case - Right-Click + Alt is active and mouse is moved
		if self.isZoomActive:
			mousePosition2DV = QtGui.QVector2D(self.mapToGlobal(event.pos()))
			currentZoomDelta = self.topLeftPosition.distanceToPoint(mousePosition2DV)

			zoomFactor = 1.05
			if currentZoomDelta < self.zoomDelta:
				zoomFactor = 0.95

			# Apply zoom
			self.scale(zoomFactor, zoomFactor)
			self.zoomDelta = currentZoomDelta

		self.rubberBandGeometry = self.rubberBandRect()

		return result

	def mouseReleaseEvent(self, event):
		#first run default trigger
		result = QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)
		
		#set custom behaviour
		isMidMouse = False
		if int(cmds.about(version = True)) > 2024:
			if event.buttons() == QtCore.Qt.MiddleButton:
				isMidMouse = True
		else:
			if event.buttons() == QtCore.Qt.MidButton:
				isMidMouse = True
		
		###Middle Mouse Pan released
		if self.isPanActive:
			#finalize the transform- calculate final center
			newSceneCenter = self.getSceneCenterPosition() - (self.mapToScene(event.pos()) -
										   self.mousePosition)
			self.centerOn(newSceneCenter)

			#set drag mode
			if int(cmds.about(version = True)) > 2024:
				self.setDragMode(self.DragMode.RubberBandDrag)
			else:
				self.setDragMode(self.RubberBandDrag)
				
			#release local flag
			self.isPanActive = False
			self.setCurrentStateRect()

		###Middle Mouse Zoom released
		elif self.isZoomActive and event.button() == QtCore.Qt.RightButton:
			#set drag mode
			if int(cmds.about(version = True)) > 2024:
				self.setDragMode(self.DragMode.RubberBandDrag)
			else:
				self.setDragMode(self.RubberBandDrag)

			#release local flag
			self.isZoomActive = False
			self.setCurrentStateRect()

		###left button released
		elif event.button() == QtCore.Qt.LeftButton:
			if self.isRubberBandActive:
				self.determaineSelection()
				self.isRubberBandActive = False

		###right button released
		elif event.button() == QtCore.Qt.RightButton:
			if self.isRubberBandActive:
				self.determaineSelection()
				blkUtils.resetControls(pm.ls(sl=True))
				self.isRubberBandActive = False	
			
		return result

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_A:
			self.fitContent()
		elif event.key() == QtCore.Qt.Key_F:
			self.fitContent(fromSel = True)
		elif event.key() == QtCore.Qt.Key_1 or event.key() == QtCore.Qt.Key_Left:
			if self.tabWidget: self.tabWidget.setCurrentIndex(0)
		elif event.key() == QtCore.Qt.Key_2 or event.key() == QtCore.Qt.Key_Right:
			if self.tabWidget: self.tabWidget.setCurrentIndex(1)
		elif event.key() == QtCore.Qt.Key_R:
			if self.pickerWindowObj:
				self.pickerWindowObj.setWindowSize()

		return True
		#return QtWidgets.QGraphicsView.keyPressEvent(self, event)

	def wheelEvent(self, event):
		#scale the scene based on a pre-defined zoom factor when the wheel is active
		self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
		zoomFactor = 1.1

		if int(cmds.about(version = True)) > 2024:
			if event.angleDelta().y() < 0:
				zoomFactor = 0.9
		else:
			if event.delta() < 0:
				zoomFactor = 0.9

		# Apply zoom
		self.scale(zoomFactor, zoomFactor)
		self.setCurrentStateRect()

	def resizeEvent(self, event): 
		self.fitInView(self.currentContentRect, QtCore.Qt.KeepAspectRatio);

		return QtWidgets.QGraphicsView.resizeEvent(self, event)

	def determaineSelection(self):
		controls = []
		if self.rubberBandGeometry.isValid():
			for btnProxy in self.scene().items():
				if btnProxy.isVisible() and type(btnProxy) != QtWidgets.QGraphicsPixmapItem:
					btn = btnProxy.widget()
					if self.rubberBandGeometry.intersects(self.mapFromScene(btn.geometry()).boundingRect()):
						controls += btn.connectedControls

		mode = blkUtils.getKeyboardModifiersState()
		blkUtils.selectRelatedControls(controls, mode)

	def setBGImage(self):
		if not self.graphicsPixmapItem is None:
			self.graphicsPixmapItem = None

		if self.bgImage:
			tempImg = QtGui.QPixmap(self.bgImage)

			self.graphicsPixmapItem = QtWidgets.QGraphicsPixmapItem(tempImg)
			self.graphicsPixmapItem.setOffset(-(self.sceneWidth/2.0), -(self.sceneHeight/2.0))
			self.graphicsPixmapItem.setZValue(-10)
			self.graphicsPixmapItem.setAcceptedMouseButtons(QtCore.Qt.NoButton)
			self.scene().addItem(self.graphicsPixmapItem)

	def fitContent(self, fromSel = False):
		contentRect = self.getContentBoundingRect(fromSel = fromSel)
		self.fitInView(contentRect, QtCore.Qt.KeepAspectRatio)
		self.setCurrentStateRect()

	def drawForeground(self, painter, rect):
		#first run default trigger
		result = QtWidgets.QGraphicsView.drawForeground(self, painter, rect)
		#now draw the custom scene orientation FG
		self.drawConstantFG(painter, rect)

		return result

	def drawConstantFG(self, painter, rect, **kwargs):
		if self.pickerWindowObj.bgToggle_btn.isChecked():
			bgImage = QtGui.QImage(GLOB_guiIconsDir + "/picker/pickerOrientationMarkerBG.png").mirrored(False, True).scaled(50, 50)
			self.setBackgroundBrush(QtGui.QBrush(bgImage))
		else:
			self.setBackgroundBrush(QtGui.QBrush())

		if self.pickerWindowObj.gridToggle_btn.isChecked():
			# Set Pen
			pen = QtGui.QPen(QtGui.QColor(160, 160, 160, 120), 2)
			painter.setPen(pen)

			# Draw grid lines
			if rect.y() < 0 and (rect.height() - rect.y()) > 0:
				x_line = QtCore.QLine(rect.x(), 0, rect.width() + rect.x(), 0)
				painter.drawLine(x_line)
			if rect.x() < 0 and (rect.width() - rect.x()) > 0:
				y_line = QtCore.QLineF(0, rect.y(), 0, rect.height() + rect.y())
				painter.drawLine(y_line)

class MnsPicker2(form_class, base_class):
	"""Picker UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsPicker2, self).__init__(parent)
		pm.select(d = True)
		self.setupUi( self )
		self.setWindowIcon(QtGui.QIcon(GLOB_guiIconsDir + "/picker/mansur_logo_noText_picker.png"))
		self.recSetInstanceName()
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)

		# locals
		self.puppetPickersDict = {}
		self.currentTabWidget = None
		self.bodyQGV = None
		self.faceQGV = None
		self.pickerWidth = 600
		self.pickerHeight = 800
		self.rigTops = {}
		self.rigTop = None
		self.puppetRoot = None
		self.pickerBase = None
		self.namespace = ""
		self.tnPath = GLOB_guiIconsDir + "/picker/user-profile.png"
		self.visRelationMapByRigTopKey = {}

		#callbacks
		self.mayaSelectCallBack = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.refreshBtnState)
		self.newSceneCallback = OpenMaya.MEventMessage.addEventCallback("NewSceneOpened", self.destroyAction)
		self.sceneOpenedCallback = OpenMaya.MEventMessage.addEventCallback("SceneOpened", self.destroyAction)

		#methods
		self.installEventFilter(self)
		self.initializeUI()	
		self.refreshBtnState()
		self.connectSignals()

	def recSetInstanceName(self, idx = 0):
		baseName = windowBaseName + "_" + str(idx)
		
		from ...core import globals as mnsGlobals
		if baseName in mnsGlobals.GLOB_mnsPickerInstances.keys():
			self.recSetInstanceName(idx + 1)
		else:
			self.setObjectName(baseName)
			from ...core import globals as mnsGlobals
			mnsGlobals.GLOB_mnsPickerInstances[baseName] = self

	def initializeUI(self):
		#set thumbnail size policy and default
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		sizePolicy.setHeightForWidth(True)
		self.thumbail_lbl.setSizePolicy(sizePolicy)
		self.setThumbnail()

		#grid toggle icon
		self.gridToggle_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/picker/Grid.png"))
		self.bgToggle_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/picker/dot.png"))

		#new instance
		self.newInstance_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png"))

		#init rigTops
		self.rigTops = blkUtils.getRigTopAssemblies()
		if self.rigTops: self.rigName_cb.addItems(self.rigTops.keys())
		
		mnsGui.setGuiStyle(self, "Picker")
		self.setRigTop()

	def connectSignals(self):
		"""Connect all UI Signals.
		"""
		self.rigName_cb.currentIndexChanged.connect(self.setRigTop)

		#grid toggle
		self.gridToggle_btn.toggled.connect(self.gridToggleTrigger)
		self.bgToggle_btn.toggled.connect(self.gridToggleTrigger)

		#new instance
		self.newInstance_btn.released.connect(self.newInstance)

		#global btns
		###select
		self.selectIV_btn.released.connect(lambda: pm.select(self.getControllersInView(), r = 1))
		self.deselect_btn.released.connect(lambda: pm.select(clear = True))
		self.selectAll_btn.released.connect(lambda: blkUtils.selectAllCtrls(self.rigTop))
		###reset
		self.resetAll_btn.released.connect(lambda: blkUtils.resetAllControlForRigTop(self.rigTop, skipModuleVis = True))
		self.resetSelected_btn.released.connect(lambda: blkUtils.resetControls([ctrl for ctrl in pm.ls(sl = True, type = "transform") if ctrl.nodeName().endswith("_ctrl")], skipModuleVis = True))
		self.resetIV_btn.released.connect(lambda: blkUtils.resetControls(self.getControllersInView(), skipModuleVis = True))
		###key
		self.keySelected_btn.released.connect(lambda: pm.setKeyframe([ctrl for ctrl in pm.ls(sl=True) if ctrl.nodeName().endswith("_ctrl")], shape = False, controlPoints = False, breakdown = 0))
		self.keyAll_btn.released.connect(lambda: pm.setKeyframe(blkUtils.selectAllCtrls(self.rigTop)))
		self.keyIV_btn.released.connect(lambda: pm.setKeyframe(self.getControllersInView()))
		###mirror
		self.mirrorSelected_btn.released.connect(lambda: blkUtils.mirrorCtrls([ctrl for ctrl in pm.ls(sl=True) if ctrl.nodeName().endswith("_ctrl")], int(self.lrMirrorDirection_cbx.isChecked())))
		self.mirrorAll_btn.released.connect(lambda: blkUtils.mirrorCtrls(blkUtils.selectAllCtrls(self.rigTop), int(self.lrMirrorDirection_cbx.isChecked())))
		self.mirrorIV_btn.released.connect(lambda: blkUtils.mirrorCtrls(self.getControllersInView(), int(self.lrMirrorDirection_cbx.isChecked())))
		#guide
		self.howToUse_btn.released.connect(self.displayHowToUseGuide)

	def setThumbnail(self):
		#set default thumbnail
		self.thumbail_lbl.setPixmap(QtGui.QPixmap(self.tnPath).scaled(50,50, QtCore.Qt.KeepAspectRatio))

	def displayHowToUseGuide(self):
		if pm.window("pickerLegend", exists=True):
			try:
				pm.deleteUI("pickerLegend")
			except:
				pass

		legendWindow = QtWidgets.QMainWindow(self)
		legendWindow.setObjectName("pickerLegend")
		legendWindow.setWindowTitle("Mansur- Picker Legend")
		legendWindow.resize(1500,700)
		mainLayout = QtWidgets.QVBoxLayout()
		legendWindow.setLayout(mainLayout)

		label = QtWidgets.QLabel()
		label.resize(1500, 700)
		label.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/picker/howToUseThePicker.png"))
		legendWindow.layout().addWidget(label)
		legendWindow.show()

	def gridToggleTrigger(self):
		self.bodyQGV.update()
		self.faceQGV.update()

	def setRigTop(self):
		self.rigTop = None

		currentRig = self.rigName_cb.currentText()
		if currentRig:
			if currentRig in self.rigTops.keys():
				self.rigTop = self.rigTops[self.rigName_cb.currentText()]
		
		self.puppetRoot = None
		if self.rigTop: self.puppetRoot = blkUtils.getPuppetRootFromRigTop(self.rigTop)
		self.pickerBase = None
		self.namespace = ""

		if self.rigTop: 
			self.namespace = self.rigTop.namespace
			self.pickerBase = blkUtils.getPickerLayoutBaseFromRigTop(self.rigTop)
			if self.pickerBase:
				self.pickerWidth = self.pickerBase.node.width.get()
				self.pickerHeight = self.pickerBase.node.height.get()

		self.initializePuppetPicker()

	def validateVisCtrl(self, node):
		if node:
			if type(node) == pm.nodetypes.NurbsCurve:
				return node.getParent()
			else:
				return node

	def createVisRelationMapForRigTop(self):
		if self.rigTop:
			puppetName = self.rigName_cb.currentText()
			visRelationMap = {}

			if self.puppetRoot:
				#map puppet root
				puppetRootMap = {}
				for udAttr in self.puppetRoot.node.listAttr(ud = True, unlocked = True):
					udAttrBtnRelatedControls = {}

					splitNameArray = udAttr.attrName().split("_")
					if len(splitNameArray) == 3 and len(splitNameArray[0]) == 1:
						#module vis attrs only
						#find animCurvesCC nodes in front
						outAcUUNodes = udAttr.listConnections(d = True, s = False, t = pm.nodetypes.AnimCurveUU)
						if outAcUUNodes:
							outAcUUNode = outAcUUNodes[0]
							outModuleRoots = outAcUUNode.listConnections(d = True, s = False, t = "transform")
						elif mnsUtils.isPluginLoaded("mnsModuleVis"):
							outModVisNodes = udAttr.listConnections(d = True, s = False, t = pm.nodetypes.MnsModuleVis)
							if outModVisNodes:
								outModVisNode = outModVisNodes[0]
								outModuleRoots = outModVisNode.listConnections(d = True, s = False, t = "transform")

						if outModuleRoots:
							outModuleRoot = outModuleRoots[0]
							visAttrNames = ["primaryVis", "secondaryVis", "tertiaryVis"]
							
							for visAttrName in visAttrNames:
								visAttrNameRelated = []
								if outModuleRoot.hasAttr(visAttrName):
									for visSlaveCtrl in outModuleRoot.attr(visAttrName).listConnections(d = True, s = False):
										if type(visSlaveCtrl) == (pm.nodetypes.multDL if cmds.about(v=True) >= "2026" else pm.nodetypes.MultDoubleLinear):
											outMdlCons = visSlaveCtrl.listConnections(d = True, s = False)
											for outMdlCon in outMdlCons:
												visSlaveCtrlA = self.validateVisCtrl(outMdlCon)
												if visSlaveCtrlA in self.puppetPickersDict[puppetName]["ctrlToButtonMap"]:
													visAttrNameRelated.append(self.puppetPickersDict[puppetName]["ctrlToButtonMap"][visSlaveCtrlA])
										else:
											visSlaveCtrl = self.validateVisCtrl(visSlaveCtrl)
											if visSlaveCtrl in self.puppetPickersDict[puppetName]["ctrlToButtonMap"]:
												visAttrNameRelated.append(self.puppetPickersDict[puppetName]["ctrlToButtonMap"][visSlaveCtrl])

								udAttrBtnRelatedControls[visAttrName] = visAttrNameRelated
						
					puppetRootMap[udAttr.name()] = udAttrBtnRelatedControls
				visRelationMap["puppetRootMap"] = puppetRootMap
			
			return visRelationMap
	
	def createVisMap(self):
		if self.rigTop:
			puppetName = self.rigName_cb.currentText()

			if not puppetName in self.visRelationMapByRigTopKey.keys():
				self.visRelationMapByRigTopKey[puppetName] = self.createVisRelationMapForRigTop()

	def setBtnVisStateBasedOnPupetRootAttr(self, visAttr):
		if self.rigTop and self.puppetRoot:
			puppetName = self.rigName_cb.currentText()
			
			if puppetName in self.visRelationMapByRigTopKey.keys():
				puppetVisMap = self.visRelationMapByRigTopKey[puppetName]["puppetRootMap"]
				
				splitNameArray = visAttr.attrName().split("_")
				if len(splitNameArray) == 3 and len(splitNameArray[0]) == 1:
					if visAttr.name() in puppetVisMap.keys():
						attrState = visAttr.get()
						
						btnStates = {"primaryVis": False, "secondaryVis": False, "tertiaryVis": False}
						if attrState == 1: btnStates = {"primaryVis": True, "secondaryVis": False, "tertiaryVis": False}
						elif attrState == 2: btnStates = {"primaryVis": True, "secondaryVis": True, "tertiaryVis": False}
						elif attrState == 3: btnStates = {"primaryVis": True, "secondaryVis": True, "tertiaryVis": True}
						elif attrState == 4: btnStates = {"primaryVis": False, "secondaryVis": True, "tertiaryVis": False}
						elif attrState == 5: btnStates = {"primaryVis": False, "secondaryVis": False, "tertiaryVis": True}
						elif attrState == 6: btnStates = {"primaryVis": False, "secondaryVis": True, "tertiaryVis": True}
						elif attrState == 7: btnStates = {"primaryVis": True, "secondaryVis": False, "tertiaryVis": True}

						for grpKey in btnStates.keys():
							btnState = btnStates[grpKey]
							for btn in puppetVisMap[visAttr.name()][grpKey]:
								btn.setHidden(not btnState)

	def setBtnVisStateBasedOnPupetRoot(self):
		if self.rigTop and self.puppetRoot:
			puppetName = self.rigName_cb.currentText()
			
			if puppetName in self.visRelationMapByRigTopKey.keys():
				puppetVisMap = self.visRelationMapByRigTopKey[puppetName]["puppetRootMap"]

				puppetRootVisAttrs = self.puppetRoot.node.listAttr(ud = True, unlocked = True)
				for visAttr in puppetRootVisAttrs:
					self.setBtnVisStateBasedOnPupetRootAttr(visAttr)

	def initializePuppetPicker(self):
		"""Main method for the global UI draw.
		The UI is initialy destroyed, then re-drawen.
		"""

		if self.rigTop:
			initialRun = False
			puppetName = self.rigName_cb.currentText()

			#check if it is a new puppet selection, 
			#if so create a new display, if not, simply switch all variables to it
			if not puppetName in self.puppetPickersDict.keys():
				initialRun = True

				#first create a new tab widget
				mainTabWidget = QtWidgets.QTabWidget()
				mainTabWidget.setObjectName(puppetName)

				#start defining the stored variable for this rigTop
				newPickerDefinition = {"tabWidget": mainTabWidget}
				
				#initialize new scene
				bodyQGV = MnsPickerGraphicViewWidget(parent=self)
				faceQGV = MnsPickerGraphicViewWidget(parent=self)
				
				#store it
				newPickerDefinition.update({"bodyQGV": bodyQGV, "faceQGV": faceQGV})

				#insert the scenes into the tabWidget
				mainTabWidget.insertTab(0, bodyQGV, "Body")
				mainTabWidget.insertTab(1, faceQGV, "Face")

				#draw all buttons
				plgs = blkUtils.getAllPlgsForRigTop(self.rigTop)
				ctrlToButtonMap = {}
				if plgs:
					for plg in plgs: 
						plgBtn = self.drawPlgButton(plg, bodyQGV, faceQGV)
						if plgBtn and plgBtn.directConnectedCtrl:
							ctrlToButtonMap[plgBtn.directConnectedCtrl] = plgBtn
				newPickerDefinition.update({"ctrlToButtonMap": ctrlToButtonMap})
				
				#set a new index to the new def
				newPickerDefinition.update({"index": self.mainStack_sw.count()})

				#set the bg images
				bodyQGV.sceneWidth = self.pickerWidth
				bodyQGV.sceneHeight = self.pickerHeight
				faceQGV.sceneWidth = self.pickerWidth
				faceQGV.sceneHeight = self.pickerHeight
				self.setBGImages(bodyQGV, faceQGV)

				#set window var for accesibility
				bodyQGV.pickerWindowObj = self
				faceQGV.pickerWindowObj = self

				#add the new definiion widget into the store dict
				self.puppetPickersDict.update({puppetName: newPickerDefinition})

				#finally insert the new tab widget into the main stacked widget
				self.mainStack_sw.insertWidget(self.mainStack_sw.count(), mainTabWidget)

			#createVisMap
			self.createVisMap()

			self.setLocalVarsBasedOnCurrentRigTop()
			self.mainStack_sw.setCurrentIndex(self.puppetPickersDict[puppetName]["index"])
			self.setThumbnail()

			self.setBtnVisStateBasedOnPupetRoot()
			
			#resize window if initial run
			if initialRun:
				self.setWindowSize()

	def attemptToGetImages(self, originPath, bodyBgImage, faceBgImage, tn, **kwargs):
		rigTop = kwargs.get("basedOnRigTopName", False)
		nameCheck = None
		if rigTop:
			nameCheck = rigTop.body

		if os.path.isdir(originPath):
			for file in os.listdir(originPath):
				if file.endswith(".png") or file.endswith(".jpg"):
					if "_pickerBody" in file and not bodyBgImage:
						if nameCheck:
							if file.split("_pickerBody")[0] == nameCheck in file:
								bodyBgImage = originPath + "/" + file
						else:
							bodyBgImage = originPath + "/" + file
					elif "_pickerFace" in file and not faceBgImage: 
						if nameCheck:
							if file.split("_pickerBody")[0] == nameCheck in file:
								faceBgImage = originPath + "/" + file
						else:
							faceBgImage = originPath + "/" + file
					elif "_pickerThumbnail" in file and not tn: 
						if nameCheck:
							if file.split("_pickerBody")[0] == nameCheck in file:
								tn = originPath + "/" + file
						else:
							tn = originPath + "/" + file
		return bodyBgImage, faceBgImage, tn

	def setBGImages(self, bodyQGV = None, faceQGV = None):
		"""Sets the bg image for the UI, in case there is one within the rig-top's attributes.
		The bg cannot be set to multiple layouts, hence, a 'tab changed' trigger is connected to this method,
		in order to toggle between the body and facial background images.
		"""

		bodyBgImage, faceBgImage, tn = None, None, None
		self.tnPath = GLOB_guiIconsDir + "/picker/user-profile.png"

		if self.rigTop: 
			bodyBgImage, faceBgImage, tn = self.attemptToGetImages(os.path.dirname(cmds.file(q=True, sn=True)), bodyBgImage, faceBgImage, tn)
			if not bodyBgImage or not faceBgImage or not tn:
				if pm.referenceQuery(self.rigTop.node, isNodeReferenced = True):
					bodyBgImage, faceBgImage, tn = self.attemptToGetImages(os.path.dirname(pm.referenceQuery(self.rigTop.node, filename = True)), bodyBgImage, faceBgImage, tn)
			if not bodyBgImage or not faceBgImage or not tn:
				if self.rigTop:
					mansurPrefs = mnsUtils.getMansurPrefs()
					if "Picker" in mansurPrefs.keys():
						if "pickerImagesFallbackPath" in mansurPrefs["Picker"].keys():
							pickerImagesFallbackPath = mnsUIUtils.convertRelativePathToAbs(mansurPrefs["Picker"]["pickerImagesFallbackPath"])
							if pickerImagesFallbackPath and os.path.isdir(pickerImagesFallbackPath):
								bodyBgImage, faceBgImage, tn = self.attemptToGetImages(pickerImagesFallbackPath, bodyBgImage, faceBgImage, tn, basedOnRigTopName = self.rigTop)

			if not bodyBgImage or not faceBgImage:
				if self.rigTop.node.hasAttr("bodyPickerImagePath"):
					bodyBgFile = self.rigTop.node.bodyPickerImagePath.get()
					if bodyBgFile and os.path.isfile(bodyBgFile):
						bodyBgImage = bodyBgFile
					if self.rigTop.node.hasAttr("facialPickerImagePath"):
						facialBgImage = self.rigTop.node.facialPickerImagePath.get()
						if facialBgImage and os.path.isfile(facialBgImage):
							faceBgImage = facialBgImage

		if bodyQGV and bodyBgImage:
			bodyQGV.bgImage = bodyBgImage
			bodyQGV.setBGImage()
		if faceQGV and faceBgImage:
			faceQGV.bgImage = faceBgImage
			faceQGV.setBGImage()
		if bodyQGV and tn:
			bodyQGV.tnPath = tn

	def setWindowSize(self):
		if self.bodyQGV and self.faceQGV:
			sceneHMargin = abs(self.width() - self.bodyQGV.width())
			sceneVMargin = abs(self.height() - self.bodyQGV.height())
			self.resize(self.pickerWidth + sceneHMargin, self.pickerHeight + sceneVMargin)
			self.bodyQGV.fitContent()
			if self.currentTabWidget: self.currentTabWidget.setCurrentIndex(1)
			self.faceQGV.fitContent()
			if self.currentTabWidget: self.currentTabWidget.setCurrentIndex(0)

	def setLocalVarsBasedOnCurrentRigTop(self):
		self.bodyQGV = None
		self.faceQGV = None
		self.tnPath = GLOB_guiIconsDir + "/picker/user-profile.png"

		puppetName = self.rigName_cb.currentText()
		if puppetName in self.puppetPickersDict.keys():
			displayComponentDict = self.puppetPickersDict[puppetName]
			self.bodyQGV = displayComponentDict["bodyQGV"]
			self.faceQGV = displayComponentDict["faceQGV"]
			self.currentTabWidget = displayComponentDict["tabWidget"]
			self.bodyQGV.tabWidget = displayComponentDict["tabWidget"]
			self.faceQGV.tabWidget = displayComponentDict["tabWidget"]
			if self.bodyQGV.tnPath:
				self.tnPath = self.bodyQGV.tnPath

	def getPlgPositionandSize(self, plg):
		"""Maps a PLG scene position to the UI's local layout position.
		Since the positions of the PLG within the scene doesn't match the settings of QT,
		this method maps the passed in plg position, in relation to the main 'Picker Layout Base',
		and returns the new relative position to the UI layout.
		This method also retunes the bounding box size of the given plg.
		"""

		width = self.pickerBase.node.width.get()
		height = self.pickerBase.node.height.get()

		plg = mnsUtils.validateNameStd(plg)
		if plg and self.pickerBase:
			plgDup = pm.duplicate(plg.node)[0]
			mnsUtils.setAttr(plgDup.v, True)
			plgPositionBBWS = pm.xform(plgDup, q = True, bb = True, ws = True)
			plgWidth = (plgPositionBBWS[3] - plgPositionBBWS[0]) * 5
			plgHeight = (plgPositionBBWS[4] -  plgPositionBBWS[1]) * 5

			plgPositionWS = pmDt.Vector(plgPositionBBWS[0], plgPositionBBWS[4], 0)
			plgPosX = ((plgPositionWS.x- (-width / 10))/((width / 10) - (-width / 10))) * width
			plgPosY = ((plgPositionWS.y - (-3000 + height / 10))/((-3000 - height / 10) - (-3000 + height / 10))) * height

			pm.delete(plgDup)
			#return; list, list (plgPosition(x,y), plgSize (width, height))
			return [plgPosX, plgPosY], [plgWidth, plgHeight]

	def drawPlgButton(self, plg, bodyQGV, faceQGV):
		"""This is the main dynamic button draw method.
		Flow:
			- Acquire PLG
			- calculate local space position
			- gather all relevant settings
			- draw the button based on the gathered settings and position, and connect it's click signal.
			"""

		if plg:
			#validate
			plgStd = mnsUtils.validateNameStd(plg)
			plg = mnsUtils.checkIfObjExistsAndSet(obj = plg, namespace = plgStd.namespace)
			if plg:
				### gather data
				plgPosition, plgSize = self.getPlgPositionandSize(plg)
				plgColor = plg.getShape().overrideColorRGB.get()
				status, isFacial = mnsUtils.validateAttrAndGet(plg, "isFacial", False)

				### create
				plgBtn = picker2QPushButton(pickerWin = self,
											plgNode = plg, 
											plgColor = [(plgColor[0] * 255), (plgColor[1] * 255), (plgColor[2] * 255)],
											textColor = [plg.textColorR.get(), plg.textColorG.get(), plg.textColorB.get()],
											text = plg.buttonText.get(),
											isBold = plg.bold.get(),
											isItalic = plg.italic.get(),
											isUnderline = plg.underline.get(),
											fontSize = plg.fontSize.get(),
											positionH = plgPosition[0] - (self.pickerWidth / 2),
											positionV = plgPosition[1] - (self.pickerHeight / 2),
											scaleH = plgSize[0],
											scaleV = plgSize[1],
											isFacial = isFacial)
				#add to view
				if isFacial: proxyItem = faceQGV.scene().addWidget(plgBtn)
				else: proxyItem = bodyQGV.scene().addWidget(plgBtn)
				return plgBtn

	def destroyAction(self, dummy = None):
		self.deleteCallBacks()
		self.destroy()

	def deleteCallBacks(self):
		#close event- delete all callbacks
		try: OpenMaya.MMessage.removeCallback(self.mayaSelectCallBack)
		except: pass
		
		try: OpenMaya.MMessage.removeCallback(self.newSceneCallback)
		except: pass

		try: OpenMaya.MMessage.removeCallback(self.sceneOpenedCallback)
		except: pass

	def eventFilter(self, source, event):
		"""Override event filter to catch the close trigger to delete the callback
		"""
		if event.type() == QtCore.QEvent.Close:
			self.deleteCallBacks()
			
		if event.type() == QtCore.QEvent.HoverEnter:
			if self.currentTabWidget:
				self.currentTabWidget.activateWindow()
				if self.currentTabWidget.currentIndex() == 0:
					self.bodyQGV.setFocus()
				else:
					self.faceQGV.setFocus()

		if event.type() == QtCore.QEvent.HoverLeave:
			mnsUIUtils.get_maya_window().activateWindow()

		return super(QtWidgets.QWidget, self).eventFilter(source, event)

	def refreshButtonVisibility(self):
		for btnProxy in (self.bodyQGV.scene().items() + self.faceQGV.scene().items()):
			if not type(btnProxy) is QtWidgets.QGraphicsPixmapItem:
				btn =  btnProxy.widget()
				
				if btn.directConnectedCtrl:
					shp = btn.directConnectedCtrl.getShape()
					if shp and shp.isVisible():
						btn.setHidden(False)
					else:
						btn.setHidden(True)
				else: 
					btn.setHidden(False)

	def refreshBtnState(self, dummy = None):
		try:
			sel = []
			if not self.namespace:
				selA = cmds.ls("*_ctrl", sl = True, type = "transform")
				
				sel = []
				rigTopBodyName = self.rigTop.body
				for s in selA:
					if "|" in s:
						if rigTopBodyName in s:
							sel.append(s.split("|")[-1])
					else:
						sel.append(s)
			else: 
				sel = cmds.ls(self.namespace + ":*_ctrl", sl = True, type = "transform")

			for s in cmds.ls("*_cnsCtrl", sl = True, type = "transform"):
				sel.append(blkUtils.locateCnsForCtrl(s, slaveOnly = True))

			for btnProxy in (self.bodyQGV.scene().items() + self.faceQGV.scene().items()):
				if not type(btnProxy) is QtWidgets.QGraphicsPixmapItem:
					btn =  btnProxy.widget()
					
					if btn.directConnectedCtrl:
						if btn.directConnectedCtrl.nodeName() in sel: 
							btn.setChecked(True)
						else: 
							btn.setChecked(False)
					else: 
						btn.setChecked(False)
		except:
			pass

	def getControllersInView(self):
		if self.currentTabWidget.currentIndex() == 0:
			return self.bodyQGV.getControllersInView()
		else:
			return self.faceQGV.getControllersInView()

	def newInstance(self):
		previousPosition = self.pos()
		offset = QtCore.QPoint(30,30)
		previousPosition += offset

		mnsPicker2Win = MnsPicker2()
		mnsPicker2Win.loadWindow()
		mnsPicker2Win.move(previousPosition)
		mnsPicker2Win.setWindowSize()
		
	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsPicker2", svr = 0)
		self.show()
	
def closeAllInstances(idx = 0):
	previousPosition = None

	from ...core.globals import GLOB_mnsPickerInstances

	for pickerInstanceName in GLOB_mnsPickerInstances.keys():
		pickerInstance = GLOB_mnsPickerInstances[pickerInstanceName]
		
		if pickerInstance:
			previousPosition = pickerInstance.pos()
		
		try: pm.deleteUI(pickerInstance.objectName)
		except: 
			try: pickerInstance.destroy()
			except: pass
	
	from ...core import globals as mnsGlobals
	mnsGlobals.GLOB_mnsPickerInstances = {}
	
	return previousPosition

def loadPicker(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("Picker Load Pressed.")
	
	previousPosition = closeAllInstances()

	mnsPicker2Win = MnsPicker2()
	mnsPicker2Win.loadWindow()
	if previousPosition: mnsPicker2Win.move(previousPosition)
	mnsPicker2Win.setWindowSize()
	return mnsPicker2Win
