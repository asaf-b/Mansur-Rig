"""=== Author: Assaf Ben Zur ===
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
import maya.OpenMaya as OpenMaya

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core.UIUtils import CollapsibleFrameWidget
from ...core import string as mnsString
from ...core import nodes as mnsNodes
from ...core.globals import *
from ..core import blockUtility as blkUtils
from ...gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore, QtWidgets
	from PySide6.QtWidgets import QFrame
else:
	from PySide2 import QtGui, QtCore, QtWidgets
	from PySide2.QtWidgets import QFrame

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "volumeJointsUI.ui")

class DragDoubleSpinBox(QtWidgets.QDoubleSpinBox):
	def __init__(self, parent = None):
		super(DragDoubleSpinBox, self).__init__(parent)

		self.mouseStartPosX = 0
		self.startValue = 0
		self.inDrag = False
		self.installEventFilter(self)

		self.le = self.findChild(QtWidgets.QLineEdit)
		if self.le:
			self.le.installEventFilter(self)

	def eventFilter(self, source, event):
		"""Override event filter to catch the close trigger to delete the callback
		"""

		if source is self.le:
			if event.type() == QtCore.QEvent.MouseButtonPress:
				if event.buttons() == QtCore.Qt.MidButton:
					self.mouseDragStart(event)
			elif event.type() == QtCore.QEvent.MouseButtonRelease and self.inDrag:
				self.mouseDragEnd(event)
		if self.inDrag and event.type() == QtCore.QEvent.HoverMove:
			self.mouseDrag(event)

		return super(QtWidgets.QWidget, self).eventFilter(source, event)

	def mouseDragStart(self, event):
		self.inDrag = True
		QtGui.QCursor().setShape(QtCore.Qt.SplitHCursor)
		self.mouseStartPosX = event.pos().x()
		self.startValue = self.value()

	def mouseDrag(self, event):
		multiplier = 0.1
		if event.modifiers() == QtCore.Qt.ControlModifier: multiplier /= 10
		valueOffset = (self.mouseStartPosX + event.pos().x()) * multiplier
		self.setValue(self.startValue + valueOffset)

	def mouseDragEnd(self, event):
		self.inDrag = False

class MnsVolumeJointsUI(form_class, base_class):
	"""Main UI Class
	"""

	###INIT
	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		#initialize UI
		super(MnsVolumeJointsUI, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsVolumeJointsUI") 
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		#locals
		self.installEventFilter(self)
		self.allCollapsible = []
		self.allEditableWidgets = []
		self.mayaSelectCallBack = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.sceneSelectionChangedTrigger)
		self.blockSceneSelectCallback = False
		self.cbxSBRelations = {}
		self.currentVJnt = None
		self.currentVJntNode = None
		self.currentIndex = None
		self.currentVJntSym = None
		self.currentVJntNodeSym = None
		self.currentIndexSym = None
		self.symmetryDelta = None
		self.attrMapping = None

		#methods
		self.initializeUI()
		mnsGui.setGuiStyle(self, "Volume Joints")
		self.updateAllEditValues()
		self.connectSignals()
		self.refreshView()

	def connectSignals(self):
		"""Connect all UI signals
		"""
		self.create_btn.released.connect(self.createVJnt)
		self.delete_btn.released.connect(self.deleteVJnt)
		self.volumeJoints_trv.itemSelectionChanged.connect(self.selectionChangedTrigger)
		self.symmetrize_btn.released.connect(self.symmetrizeVJTrigger)
		self.symmetrizeAll_btn.released.connect(self.symmetrizeAllTrigger)
		self.refresh_btn.released.connect(self.refreshView)
		self.duplicateVJnt_btn.released.connect(self.duplicateVJnt)
		self.restPoseAll_btn.released.connect(self.setRestPoseForAll)

	def refreshView(self, **kwargs):
		pm.select(d = True)
		previousSelection = None
		if self.currentVJnt:
			previousSelection = self.currentVJnt.nodeName()
		self.volumeJoints_trv.clear()
		self.currentVJnt = None
		self.currentVJntNode = None
		self.currentIndex = None
		self.currentVJntSym = None
		self.currentVJntNodeSym = None
		self.currentIndexSym = None

		allVJnts = pm.ls("*_vJnt", type = "joint")
		for vJnt in allVJnts:
			vJntName = vJnt.nodeName()
			vJntItem = QtWidgets.QTreeWidgetItem(self.volumeJoints_trv, [vJntName])
		self.selectionChangedTrigger()

		if previousSelection:
			for childItemIdx in range(self.volumeJoints_trv.invisibleRootItem().childCount()):
				childItem = self.volumeJoints_trv.invisibleRootItem().child(childItemIdx)
				if childItem.text(0) == previousSelection:
					childItem.setSelected(True)
					self.volumeJoints_trv.setCurrentItem(childItem)
					break

	def eventFilter(self, source, event):
		"""Override event filter to catch the close trigger to delete the callback
		"""

		if event.type() == QtCore.QEvent.Close:
			try: OpenMaya.MMessage.removeCallback(self.mayaSelectCallBack)
			except: pass
			try: OpenMaya.MMessage.removeCallback(self.vJointNodeStateChangeCallback)
			except: pass
				
		return super(QtWidgets.QWidget, self).eventFilter(source, event)

	def setCollapsibleWidgetsBehaviour(self):
		for colWid in self.allCollapsible:
			if colWid:
				QtCore.QObject.connect(colWid._title_frame, QtCore.SIGNAL('clicked()'), partial(self.toggleAllCollapsed, colWid))

	###DRAW
	def drawGeneralSection(self, **kwargs):
		sectionWidget = CollapsibleFrameWidget(title="General")
		sectionWidget.setObjectName("General" + "Section")
		self.mainHBox_lo.addWidget(sectionWidget)
		sectionLayout = sectionWidget._content_layout
		self.allCollapsible.append(sectionWidget)

		groupBox = QtWidgets.QGroupBox()
		#groupBox.setStyleSheet("QGroupBox{\nborder: 1px ; \npadding: 0px 0px 0px 0px;\nborder-style: solid;\nborder-color: #292929;\nborder-radius: 4px;\n}\n\nQGroupBox::title {\n    subcontrol-origin:  margin;\n	subcontrol-position: top left; \n   padding: 0 12px 0 12px;\n}")
		contentLayout = QtWidgets.QGridLayout()
		contentLayout.setContentsMargins(6, 6, 6, 6)
		contentLayout.setSpacing(10)
		groupBox.setLayout(contentLayout)

		rowLbl = QtWidgets.QLabel("Rotation-Blend")
		rowLbl.setFixedWidth(120)
		contentLayout.addWidget(rowLbl, 0, 0)

		rotBlendSB = QtWidgets.QDoubleSpinBox()
		self.allEditableWidgets.append(rotBlendSB)
		rotBlendSB.valueChanged.connect(partial(self.allEditTriggers, rotBlendSB))
		rotBlendSB.setObjectName("rotationBlend")
		rotBlendSB.setRange(0.0, 1.0)
		rotBlendSB.setSingleStep(0.1)
		rotBlendSB.setFixedWidth(60)
		rotBlendSB.setValue(0.5)
		contentLayout.addWidget(rotBlendSB, 0, 1)
		
		spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		contentLayout.addItem(spacer, 0, 2)

		restSetBtn = QtWidgets.QPushButton("Set current State as rest pose")
		self.allEditableWidgets.append(restSetBtn)
		restSetBtn.released.connect(self.setCurrentStateAsRestPose)
		restSetBtn.setAccessibleName("minorAction")
		#restSetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
		restSetBtn.setFixedHeight(23)
		restSetBtn.setFixedWidth(200)
		restSetBtn.setObjectName("setCurrentStateAsRest")
		contentLayout.addWidget(restSetBtn, 0, 3)

		spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
		contentLayout.addItem(spacer, 0, 4)

		sectionLayout.addWidget(groupBox)

	def setCurrentSBToMinOrMax(self, sourceWidget, targetWidget):
		targetWidget.setValue(sourceWidget.value())
		#

	def drawAngleSection(self, **kwargs):
		angle = kwargs.get("angle", "posX")
		channels = kwargs.get("channels", ["translate", "scale"])

		sectionWidget = CollapsibleFrameWidget(title=angle)
		sectionWidget.setObjectName(angle + "Section")
		self.mainHBox_lo.addWidget(sectionWidget)
		sectionLayout = sectionWidget._content_layout
		self.allCollapsible.append(sectionWidget)

		groupBox = QtWidgets.QGroupBox()
		#groupBox.setStyleSheet("QGroupBox{\nborder: 1px ; \npadding: 0px 0px 0px 0px;\nborder-style: solid;\nborder-color: #292929;\nborder-radius: 4px;\n}\n\nQGroupBox::title {\n    subcontrol-origin:  margin;\n	subcontrol-position: top left; \n   padding: 0 12px 0 12px;\n}")
		contentLayout = QtWidgets.QGridLayout()
		contentLayout.setContentsMargins(4, 4, 4, 4)
		groupBox.setLayout(contentLayout)

		###divider
		HLine = QFrame()
		HLine.setGeometry(QtCore.QRect(320, 150, 118, 3))
		HLine.setFrameShape(QFrame.HLine)
		HLine.setFrameShadow(QFrame.Sunken)
		HLine.setAccessibleName("HLine")
		contentLayout.addWidget(HLine, 1, 0, 1, 11)

		row = 2
		for channelName in channels:
			for axis in "xyz":
				col = 0
				spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
				contentLayout.addItem(spacer)
				col += 1
				rowLbl = QtWidgets.QLabel(channelName + axis.capitalize())
				rowLbl.setFixedWidth(75)
				contentLayout.addWidget(rowLbl, row, col)
				col += 1
				targetValueSB = DragDoubleSpinBox()
				self.allEditableWidgets.append(targetValueSB)
				targetValueSB.valueChanged.connect(partial(self.allEditTriggers, targetValueSB))
				targetValueSB.setMinimum(-1000)
				targetValueSB.setMaximum(1000)
				#targetValueSB.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
				targetValueSB.setObjectName(angle + channelName.capitalize() + axis.capitalize())
				contentLayout.addWidget(targetValueSB, row, col)
				col += 1
				if not angle == "rest":
					spacer = QtWidgets.QSpacerItem(200, 200, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
					contentLayout.addItem(spacer)
					col += 1
					if axis == "x":
						doMinLimitCbx = QtWidgets.QCheckBox()
						self.allEditableWidgets.append(doMinLimitCbx)
						doMinLimitCbx.toggled.connect(partial(self.allEditTriggers, doMinLimitCbx))
						doMinLimitCbx.setObjectName(angle + channelName.capitalize() + "DoLimitMin")
						contentLayout.addWidget(doMinLimitCbx, row, col)
						self.cbxSBRelations.update({doMinLimitCbx: []})
					col += 1
					minValueSB = QtWidgets.QDoubleSpinBox()
					self.allEditableWidgets.append(minValueSB)
					minValueSB.valueChanged.connect(partial(self.allEditTriggers, minValueSB))
					minValueSB.setMinimum(-1000)
					minValueSB.setMaximum(1000)
					minValueSB.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
					minValueSB.setEnabled(False)
					minValueSB.setObjectName(angle + channelName.capitalize() + "LimitMin" +  axis.capitalize())
					contentLayout.addWidget(minValueSB, row, col)
					col += 1
					setCurrentAsMinPB = QtWidgets.QPushButton("<")
					#setCurrentAsMinPB.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
					setCurrentAsMinPB.setFixedHeight(22)
					setCurrentAsMinPB.setFixedWidth(20)
					setCurrentAsMinPB.setObjectName(angle + channelName.capitalize() + axis.capitalize() + "SetCurrentMin")
					contentLayout.addWidget(setCurrentAsMinPB, row, col)
					col += 1
					currentValueSB = QtWidgets.QDoubleSpinBox()
					self.allEditableWidgets.append(currentValueSB)
					currentValueSB.setMinimum(-1000)
					currentValueSB.setMaximum(1000)
					currentValueSB.setReadOnly(True)
					currentValueSB.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
					currentValueSB.setObjectName(angle + channelName.capitalize() + axis.capitalize() + "Current")
					contentLayout.addWidget(currentValueSB, row, col)
					col += 1
					setCurrentAsMaxPB = QtWidgets.QPushButton(">")
					setCurrentAsMaxPB.setObjectName(angle + channelName.capitalize() + axis.capitalize() + "SetCurrentMax")
					#setCurrentAsMaxPB.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
					setCurrentAsMaxPB.setFixedHeight(22)
					setCurrentAsMaxPB.setFixedWidth(20)
					contentLayout.addWidget(setCurrentAsMaxPB, row, col)
					col += 1
					maxValueSB = QtWidgets.QDoubleSpinBox()
					self.allEditableWidgets.append(maxValueSB)
					maxValueSB.valueChanged.connect(partial(self.allEditTriggers, maxValueSB))
					maxValueSB.setMinimum(-1000)
					maxValueSB.setMaximum(1000)
					maxValueSB.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
					maxValueSB.setEnabled(False)
					maxValueSB.setObjectName(angle + channelName.capitalize() + "LimitMax" + axis.capitalize())
					contentLayout.addWidget(maxValueSB, row, col)
					col += 1
					if axis == "x":
						doMaxLimitCbx = QtWidgets.QCheckBox()
						self.allEditableWidgets.append(doMaxLimitCbx)
						doMaxLimitCbx.toggled.connect(partial(self.allEditTriggers, doMaxLimitCbx))
						doMaxLimitCbx.setObjectName(angle + channelName.capitalize() + "DoLimitMax")
						contentLayout.addWidget(doMaxLimitCbx, row, col)
						self.cbxSBRelations.update({doMaxLimitCbx: []})
					col += 1
					
					self.cbxSBRelations[doMinLimitCbx].append(minValueSB)
					self.cbxSBRelations[doMaxLimitCbx].append(maxValueSB)

					doMinLimitCbx.toggled.connect(partial(minValueSB.setEnabled))
					doMaxLimitCbx.toggled.connect(partial(maxValueSB.setEnabled))
					setCurrentAsMinPB.released.connect(partial(self.setCurrentSBToMinOrMax, currentValueSB, minValueSB))
					setCurrentAsMaxPB.released.connect(partial(self.setCurrentSBToMinOrMax, currentValueSB, maxValueSB))
				row += 1

		targetValueLbl = QtWidgets.QLabel("Target-Value")
		targetValueLbl.setAlignment(QtCore.Qt.AlignCenter)
		contentLayout.addWidget(targetValueLbl, 0, 0, 1, 4)
		if angle == "rest": 
			targetValueLbl.setText("Rest Translate")
			spacer = QtWidgets.QSpacerItem(20, 200, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			contentLayout.addItem(spacer, 5, 0)
		else:
			minLbl = QtWidgets.QLabel("Min")
			minLbl.setAlignment(QtCore.Qt.AlignCenter)
			contentLayout.addWidget(minLbl, 0, 5)
			currentLbl = QtWidgets.QLabel("Current")
			currentLbl.setAlignment(QtCore.Qt.AlignCenter)
			contentLayout.addWidget(currentLbl, 0, 7)
			maxLbl = QtWidgets.QLabel("Max")
			maxLbl.setAlignment(QtCore.Qt.AlignCenter)
			contentLayout.addWidget(maxLbl, 0, 9)
		sectionLayout.addWidget(groupBox)

	def initializeUI(self):
		#setIcons
		self.create_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png"))
		self.delete_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeRenderable.png"))
		self.refresh_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/refresh.png"))
		self.duplicateVJnt_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/duplicateReference.png"))
		self.restPoseAll_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/orientJoint.png"))
		self.symmetrize_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/polySymmetrizeUV.png"))
		self.symmetrizeAll_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/symmetrize.png"))

		self.drawGeneralSection()
		self.drawAngleSection(angle = "rest", channels = ["translate"])
		for angleName in ["posX", "negX", "posY", "negY", "posZ", "negZ"]:
			self.drawAngleSection(angle = angleName)
		self.setCollapsibleWidgetsBehaviour()
		self.volumeJoints_trv.setColumnWidth(0, 142)
		self.volumeJoints_trv.setColumnWidth(1, 142)

	###CALLBACKS
	def updateAnglesState(self):
		posXState = 0
		negXState = 0
		posYState = 0
		negYState = 0
		posZState = 0
		negZState = 0

		if self.currentVJntNode:
			posXState = int(round(self.currentVJntNode.posXState.get(), 2) * 100)
			negXState = int(round(self.currentVJntNode.negXState.get(), 2) * 100)
			posYState = int(round(self.currentVJntNode.posYState.get(), 2) * 100)
			negYState = int(round(self.currentVJntNode.negYState.get(), 2) * 100)
			posZState = int(round(self.currentVJntNode.posZState.get(), 2) * 100)
			negZState = int(round(self.currentVJntNode.negZState.get(), 2) * 100)

		self.posXState_pb.setValue(posXState)
		self.negXState_pb.setValue(negXState)
		self.posYState_pb.setValue(posYState)
		self.negYState_pb.setValue(negYState)
		self.posZState_pb.setValue(posZState)
		self.negZState_pb.setValue(negZState)

		if self.currentVJnt:
			currentValuesT = self.currentVJntNode.result[self.currentIndex].t.get()
			currentValuesS = self.currentVJntNode.result[self.currentIndex].s.get()

			for editWidgetCurrent in self.allEditableWidgets:
				attrName = editWidgetCurrent.objectName()
				if "current" in attrName.lower():
					if "TranslateX" in attrName: editWidgetCurrent.setValue(currentValuesT[0])
					elif "TranslateY" in attrName: editWidgetCurrent.setValue(currentValuesT[1])
					elif "TranslateZ" in attrName: editWidgetCurrent.setValue(currentValuesT[2])
					elif "ScaleX" in attrName: editWidgetCurrent.setValue(currentValuesS[0])
					elif "ScaleY" in attrName: editWidgetCurrent.setValue(currentValuesS[1])
					elif "ScaleZ" in attrName: editWidgetCurrent.setValue(currentValuesS[2])

	def sceneSelectionChangedTrigger(self, dummy = None):
		if not self.blockSceneSelectCallback:
			sel = pm.ls(sl=True)
			vJnt = blkUtils.getRelatedVolJntSourcesForSelection()
			if vJnt:
				nodeN = vJnt.name

				#block signals
				self.volumeJoints_trv.blockSignals(True)

				for childItemIdx in range(self.volumeJoints_trv.invisibleRootItem().childCount()):
					childItem = self.volumeJoints_trv.invisibleRootItem().child(childItemIdx)
					if childItem.text(0) == nodeN:
						childItem.setSelected(True)
						self.volumeJoints_trv.setCurrentItem(childItem)
						self.selectionChangedTrigger(skipSelection = True)
						pm.select(sel, r = True)
						break
				
				self.volumeJoints_trv.blockSignals(False)

	###TRIGGERS
	def deleteVJnt(self):
		if self.currentVJnt:
			try: OpenMaya.MMessage.removeCallback(self.vJointNodeStateChangeCallback)
			except: pass

			pm.delete(self.currentVJnt)
			if self.currentVJntSym and self.autoSym_cbx.isChecked():
				pm.delete(self.currentVJntSym.node)

			self.refreshView()

	def createVJnt(self):
		try: OpenMaya.MMessage.removeCallback(self.vJointNodeStateChangeCallback)
		except: pass

		vj = blkUtils.createVolumeJointForSelection()
		if vj: self.currentVJnt = vj.node
		self.setSymmetryVars()
		self.refreshView()

	def symmetrizeVJTrigger(self):
		if self.currentVJnt:
			blkUtils.symmetrizeVJ(self.currentVJnt)
		self.refreshView()

	def symmetrizeAllTrigger(self):
		#need to extent to R>L or L>R
		for childItemIdx in range(self.volumeJoints_trv.invisibleRootItem().childCount()):
			childItem = self.volumeJoints_trv.invisibleRootItem().child(childItemIdx)
			blkUtils.symmetrizeVJ(childItem.text(0))
		self.refreshView()

	def updateAllEditValues(self):
		if self.currentVJnt and self.currentVJntNode:
			for editWidget in self.allEditableWidgets:
				attrName = editWidget.objectName()

				enabled = True
				if type(editWidget) is QtWidgets.QDoubleSpinBox or type(editWidget) is DragDoubleSpinBox:
					if "Min" in attrName or "Max" in attrName:
						enabled = False
				if enabled:
					editWidget.setEnabled(enabled)
				
				if type(editWidget) != QtWidgets.QPushButton and not "current" in attrName.lower():
					value = "nan"
					if attrName.endswith("X") or attrName.endswith("Y") or attrName.endswith("Z"):
						value = self.currentVJntNode.volumeJoint[self.currentIndex].attr(attrName[:-1]).attr(attrName).get()
					else:
						value = self.currentVJntNode.volumeJoint[self.currentIndex].attr(attrName).get()
					if value != "nan":
						if type(editWidget) is QtWidgets.QCheckBox:
							editWidget.blockSignals(True)
							editWidget.setChecked(value)
							if value and editWidget in self.cbxSBRelations.keys():
								for relatedWidget in self.cbxSBRelations[editWidget]:
									relatedWidget.setEnabled(True)
							elif editWidget in self.cbxSBRelations.keys():
								for relatedWidget in self.cbxSBRelations[editWidget]:
									relatedWidget.setEnabled(False)
							editWidget.blockSignals(False)
						elif type(editWidget) is QtWidgets.QDoubleSpinBox or type(editWidget) is DragDoubleSpinBox:
							editWidget.blockSignals(True)
							editWidget.setValue(value)
							editWidget.blockSignals(False)
		else:
			#disable all edits
			for editWidget in self.allEditableWidgets:
				editWidget.setEnabled(False)
				if type(editWidget) is QtWidgets.QCheckBox:
					editWidget.blockSignals(True)
					editWidget.setChecked(False)
					editWidget.blockSignals(False)

	def setSymmetryVars(self, **kwargs):
		skipSymCreation = kwargs.get("skipSymCreation", False)
		createSym = False
		if not skipSymCreation and self.autoSym_cbx.isChecked():
			createSym = True


		self.currentVJntSym = None
		self.currentVJntNodeSym = None
		self.currentIndexSym = None
		self.symmetryDelta = None
		self.attrMapping = None

		if self.currentVJnt:
			self.currentVJntSym = blkUtils.getSymmetricalVolumeJoint(self.currentVJnt, supressMessages = True, createIfMissing = createSym)
			if self.currentVJntSym:
				vJntParent, vJntChild, vJntMaster = blkUtils.getVJointData(self.currentVJnt)
				symVJntParent, symVJntChild, symVJntMaster = blkUtils.getVJointData(self.currentVJntSym)
				if vJntMaster and symVJntMaster:
					self.symmetryDelta = blkUtils.detrmineSymmetryDelta(vJntMaster.node, symVJntMaster.node)
					self.attrMapping = blkUtils.volumeJointAngleSymmetryMapping(self.symmetryDelta)
				self.currentVJntNodeSym, self.currentIndexSym  = blkUtils.getExistingVolumeJointNodeForVolumeJoint(self.currentVJntSym)

	def selectionChangedTrigger(self, **kwargs):
		self.blockSceneSelectCallback = True
		skipSelection = kwargs.get("skipSelection", False)

		self.currentVJnt = None
		self.currentVJntNode = None
		self.currentIndex = None
		
		try: OpenMaya.MMessage.removeCallback(self.vJointNodeStateChangeCallback)
		except: pass
		self.updateAnglesState()

		if self.volumeJoints_trv.selectedItems():
			vJntSelection = self.volumeJoints_trv.selectedItems()[0].text(0)
			if vJntSelection:
				vJntSelection = mnsUtils.checkIfObjExistsAndSet(vJntSelection)
				if vJntSelection:
					self.currentVJnt = vJntSelection

					outCons = self.currentVJnt.parentInverseMatrix[0].listConnections(d = True, s = False, p = True)
					if outCons:
						for o in outCons:
							if type(o.node()) == pm.nodetypes.MnsVolumeJoint:
								self.currentIndex = o.parent().index()
								self.currentVJntNode = o.node()
								self.vJointNodeStateChangeCallback = OpenMaya.MNodeMessage.addAttributeChangedCallback(mnsUtils.getMObjectFromObjName(self.currentVJntNode.nodeName()), volJointStateChangedCB, {"volJointUI": self})
								self.updateAnglesState()

		self.setSymmetryVars(skipSymCreation = True)

		for childItemIdx in range(self.volumeJoints_trv.invisibleRootItem().childCount()):
			childItem = self.volumeJoints_trv.invisibleRootItem().child(childItemIdx)
			if self.currentVJntSym and childItem.text(0) == self.currentVJntSym.name:
				childItem.setForeground(0, QtGui.QColor('lightgreen'))
			else:
				childItem.setForeground(0, QtGui.QColor('lightgray'))

		self.updateAllEditValues()
		if not skipSelection and self.currentVJnt:
			pm.select(self.currentVJnt)
			if self.currentVJntSym:
				pm.select(self.currentVJntSym.node, add = True)
		
		self.blockSceneSelectCallback = False

	def allEditTriggers(self, widget = None, value = None):
		if widget and self.currentVJnt and self.currentVJntNode:
			attrName = widget.objectName()
			if attrName.endswith("X") or attrName.endswith("Y") or attrName.endswith("Z"):
				self.currentVJntNode.volumeJoint[self.currentIndex].attr(attrName[:-1]).attr(attrName).set(value)
				if self.autoSym_cbx.isChecked() and self.currentVJntSym:
					symAttr = blkUtils.getSymAttrBasedOnSymMapping(self.currentVJntNodeSym.volumeJoint[self.currentIndexSym].attr(attrName[:-1]).attr(attrName), self.attrMapping)
					if attrName.endswith("X"): value *= self.symmetryDelta.x 
					if attrName.endswith("Y"): value *= self.symmetryDelta.y 
					if attrName.endswith("Z"): value *= self.symmetryDelta.z 
					symAttr.set(value)
			else:
				self.currentVJntNode.volumeJoint[self.currentIndex].attr(attrName).set(value)
				if self.autoSym_cbx.isChecked() and self.currentVJntSym:
					self.currentVJntNodeSym.volumeJoint[self.currentIndexSym].attr(attrName).set(value)

	def setCurrentStateAsRestPose(self, **kwargs):
		try: OpenMaya.MMessage.removeCallback(self.vJointNodeStateChangeCallback)
		except: pass

		targetJointNodes = kwargs.get("targetNodes", [self.currentVJntNode])
		skipSym = kwargs.get("skipSym", False)

		if targetJointNodes:
			for vJntNode in targetJointNodes:
				inputs = vJntNode.childJointWorldMatrix.listConnections(s = True, d = False)
				if inputs:
					childJoint = inputs[0]
					vJntNode.childJointRestWorldMatrix.set(childJoint.worldMatrix[0].get())
					if not skipSym:
						if self.currentVJntSym and self.autoSym_cbx.isChecked():
							inputs = self.currentVJntNodeSym.childJointWorldMatrix.listConnections(s = True, d = False)
							if inputs:
								childJoint = inputs[0]
								self.currentVJntNodeSym.childJointRestWorldMatrix.set(childJoint.worldMatrix[0].get())
			
			if self.currentVJntNode:
				self.vJointNodeStateChangeCallback = OpenMaya.MNodeMessage.addAttributeChangedCallback(mnsUtils.getMObjectFromObjName(self.currentVJntNode.nodeName()), volJointStateChangedCB, {"volJointUI": self})


	def toggleAllCollapsed(self, pressedColWid):
		if pressedColWid:
			for colWid in self.allCollapsible:
				if colWid:
					if not colWid is pressedColWid:
						if not colWid._is_collasped:
							colWid.toggleCollapsed()

	def duplicateVJnt(self):
		if self.currentVJnt:
			sourceA, sourceB = blkUtils.getVJntSources(self.currentVJnt)
			sourceA = mnsUtils.checkIfObjExistsAndSet(sourceA)
			sourceB = mnsUtils.checkIfObjExistsAndSet(sourceB)

			if sourceA and sourceB:
				origVJnt = self.currentVJnt
				origVJntNode = self.currentVJntNode
				origIndex = self.currentIndex

				#block signals
				self.volumeJoints_trv.blockSignals(True)
				
				#flow
				dupVJnt = blkUtils.createVolumeJoint(sourceA, sourceB)
				self.refreshView()

				for childItemIdx in range(self.volumeJoints_trv.invisibleRootItem().childCount()):
					childItem = self.volumeJoints_trv.invisibleRootItem().child(childItemIdx)
					if childItem.text(0) == dupVJnt.node.nodeName():
						childItem.setSelected(True)
						self.volumeJoints_trv.setCurrentItem(childItem)
						break
				self.selectionChangedTrigger()
				self.setSymmetryVars()

				#match attrs
				for origAttr in origVJntNode.volumeJoint[origIndex].getChildren():
					if not "matrix" in origAttr.attrName().lower():
						self.currentVJntNode.volumeJoint[self.currentIndex].attr(origAttr.attrName()).set(origAttr.get())

				self.volumeJoints_trv.blockSignals(False)
				self.refreshView()

	def setRestPoseForAll(self):
		vJntNodesCollect = []

		for childItemIdx in range(self.volumeJoints_trv.invisibleRootItem().childCount()):
			childItem = self.volumeJoints_trv.invisibleRootItem().child(childItemIdx)
			vJnt = mnsUtils.checkIfObjExistsAndSet(childItem.text(0))
			if vJnt:
				vJntNode, index = blkUtils.getExistingVolumeJointNodeForVolumeJoint(vJnt) 
				if vJntNode:
					vJntNodesCollect.append(vJntNode)
		
		if vJntNodesCollect:
			pm.undoInfo(openChunk=True)
			self.setCurrentStateAsRestPose(targetNodes = vJntNodesCollect, skipSym = True)
			pm.undoInfo(closeChunk=True)

	###LOAD WIN
	def loadWindow(self):
		"""Main UI load
		"""
		self.show()
		
def loadVolumeJointsUI():
	"""Load the cns tool UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsVolumeJointsUI")

	mnsVJWin = MnsVolumeJointsUI()
	mnsVJWin.loadWindow()
	if previousPosition: mnsVJWin.move(previousPosition)

###CBs
def volJointStateChangedCB(msg, plug, otherPlug, clientData, **kwargs):
	volJointUI = clientData["volJointUI"]
	volJointUI.updateAnglesState()