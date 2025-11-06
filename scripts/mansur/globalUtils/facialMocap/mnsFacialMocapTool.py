"""=== Author: Assaf Ben Zur ===
This simple animation tool was created to allow animators to space switch and IK->FK switch easily.
This tool is selection based. Please select controls to enable relevant capabilities.
For spaces, simply select the controls you want to act upon, choose your target spaces, and press "switch". This will switch the space, while maintaining the controls's transforms, using keys created automatically.
For Limbs, simple select any control/s for the limbs that you wish to act upon, and press the relevant button- To-IK or To-FK.
This will switch the limb/controls to the selected state. 
This tool also includes Auto-Key switches, as well as a sequence and bake modes. 
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
import os
import maya.OpenMaya as OpenMaya
from maya import cmds

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import nodes as mnsNodes
from ...core.globals import *
from ...gui import gui as mnsGui
from . import facialMocapUtils as mnsFacialMocapUtils

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsFacialMocapTool.ui")
class MnsFacialMocapTool(form_class, base_class):
	"""Spaces Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsFacialMocapTool, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsFacialMocapTool") 
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		mnsUtils.updateMansurPrefs()
		
		# locals
		self.pbNodes = []
		self.col_sourceAttr = 0
		self.col_weight = 1
		self.col_min = 2
		self.col_max = 3
		self.col_isStored = 4
		self.col_sourceAttrName = 5
		self.col_index = 6
		self.poseStorage = None
		self.sbSliderPairing = {
								self.value_sb: self.value_sl,
								self.value_sl: self.value_sb,
								self.weight_sb: self.weight_sl,
								self.weight_sl: self.weight_sb,
								self.min_sb: self.min_sl,
								self.min_sl: self.min_sb,
								self.max_sb: self.max_sl,
								self.max_sl: self.max_sb
								}
		self.widgetAttrPairing = {
									self.value_sb: "poseValue",
									self.value_sl: "poseValue",
									self.weight_sb: "poseWeight", 
									self.weight_sl: "poseWeight",
									self.min_sb: "poseMinimum",
									self.min_sl: "poseMinimum",
									self.max_sb: "poseMaximum",
									self.max_sl: "poseMaximum"
								}
		#run
		self.initializeWidgets()
		self.connectSignals()
		self.initializeView()
		mnsGui.setGuiStyle(self, "Facial Mocap Tool")

	##################	
	###### INIT ######
	##################

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.poseBlends_lst.itemSelectionChanged.connect(self.initializeSelectedPb)
		self.newDef_btn.released.connect(self.createNewDefinition)
		self.sourceAttrs_lst.customContextMenuRequested.connect(self.sourceAttrsMenu)
		self.targetTransforms_lst.customContextMenuRequested.connect(self.targetTransformsMenu)
		self.poseBlends_lst.customContextMenuRequested.connect(self.pbNodesMenu)
		self.goToCreate_btn.released.connect(self.switchUIStates)
		self.reconnect_btn.released.connect(self.switchUIStates)
		self.create_trv.currentItemChanged.connect(self.setSourceValues)
		self.edit_btn.released.connect(self.switchEditUIState)
		self.save_btn.released.connect(self.switchEditUIState)
		self.discrad_btn.released.connect(self.switchEditUIState)
		self.toggle_btn.released.connect(self.toggleTrigger)
		self.create_trv.customContextMenuRequested.connect(self.createMenu)
		self.export_btn.released.connect(lambda: mnsFacialMocapUtils.exportPBData(self.getSelectedPbNode()))
		self.import_btn.released.connect(self.importFMData)
		self.doT_cbx.toggled.connect(self.toggleCbxFlagState)
		self.doR_cbx.toggled.connect(self.toggleCbxFlagState)
		self.doS_cbx.toggled.connect(self.toggleCbxFlagState)
		self.doCA_cbx.toggled.connect(self.toggleCbxFlagState)

		for widget in [self.value_sb, self.weight_sb, self.min_sb, self.max_sb, self.value_sl, self.weight_sl, self.min_sl, self.max_sl]:
			widget.valueChanged.connect(self.setSbSliderValue)

	##################	
	###### View ######
	##################

	def pbNodesMenu(self, position):
		currentLstWidget = self.sender()

		menu = QtWidgets.QMenu()
		selectAction = menu.addAction(self.tr("Select"))
		selectAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/selectByComponent.png")))
		selectAction.triggered.connect(self.selectPbNode)

		deleteAction = menu.addAction(self.tr("Delete"))
		deleteAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
		deleteAction.triggered.connect(self.deletePbNode)

		menu.exec_(currentLstWidget.viewport().mapToGlobal(position))

	def sourceAttrsMenu(self, position):
		currentLstWidget = self.sender()

		menu = QtWidgets.QMenu()
		addSelectedAction = menu.addAction(self.tr("Add Chennel-Box Selection"))
		addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
		addSelectedAction.triggered.connect(self.addSelectedCBSourceAttrs)

		replaceSelectedAction = menu.addAction(self.tr("Replace With Chennel-Box Selection"))
		replaceSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/refresh.png")))
		replaceSelectedAction.triggered.connect(lambda: self.addSelectedCBSourceAttrs(mode = 1))

		removeSelectedAction = menu.addAction(self.tr("Remove Selected"))  
		removeSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
		removeSelectedAction.triggered.connect(self.removeSelectedSourceAttrs)

		clearAction = menu.addAction(self.tr("Clear"))  
		clearAction.triggered.connect(lambda: self.removeSelectedSourceAttrs(mode = 1))

		menu.exec_(currentLstWidget.viewport().mapToGlobal(position))

	def createMenu(self, position):
		menu = QtWidgets.QMenu()
		
		if self.edit_sw.currentIndex() == 0:
			if self.poseStorage:
				clearStorageAction = menu.addAction(self.tr("Clear Pose Storage"))
				clearStorageAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/delete.png")))
				clearStorageAction.triggered.connect(self.clearPoseStorage)
		else:
			resetAction = menu.addAction(self.tr("Reset"))
			resetAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/refresh.png")))
			resetAction.triggered.connect(lambda: mnsFacialMocapUtils.resetPose(self.getSelectedPbNode()))

			storeAction = menu.addAction(self.tr("Store"))
			storeAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png")))
			storeAction.triggered.connect(self.copyPose)

			flipAndStoreAction = menu.addAction(self.tr("Flip And Store"))
			flipAndStoreAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/flipTubeSmall.png")))
			flipAndStoreAction.triggered.connect(lambda: self.copyPose(flip = True))

			if self.poseStorage:
				loadAction = menu.addAction(self.tr("Load From Storage"))
				loadAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/loadPreset.png")))
				loadAction.triggered.connect(lambda: mnsFacialMocapUtils.loadPose(self.getSelectedPbNode(), self.poseStorage))

		menu.exec_(self.create_trv.viewport().mapToGlobal(position))

	def clearPoseStorage(self):
		self.poseStorage = None

	def copyPose(self, flip = False):
		leftPrefix = self.leftPrefix_le.text()
		rightPrefix = self.rightPrefix_le.text()
		
		self.poseStorage = mnsFacialMocapUtils.copyPose(self.getSelectedPbNode(), flip = flip, leftPrefix = leftPrefix, rightPrefix = rightPrefix)

	def targetTransformsMenu(self, position):
		currentLstWidget = self.sender()

		menu = QtWidgets.QMenu()
		addSelectedAction = menu.addAction(self.tr("Add selected"))
		addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
		addSelectedAction.triggered.connect(self.addSelectedTransformsToPB)

		removeSelectedAction = menu.addAction(self.tr("Remove Selected"))  
		removeSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
		removeSelectedAction.triggered.connect(self.removeSelectedTransformsFromPB)

		selectAction = menu.addAction(self.tr("Select"))
		selectAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/selectByComponent.png")))
		selectAction.triggered.connect(self.selectTargetTransforms)

		clearAction = menu.addAction(self.tr("Clear"))  
		clearAction.triggered.connect(lambda: self.removeSelectedTransformsFromPB(mode = 1))

		menu.exec_(currentLstWidget.viewport().mapToGlobal(position))

	def initializeWidgets(self):
		self.main_sw.setCurrentIndex(0)
		self.edit_sw.setCurrentIndex(0)
		self.sourceAttrs_lst.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.targetTransforms_lst.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.poseBlends_lst.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.create_trv.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.edit_sw.setCurrentIndex(0)

	def getAllPoseBlendNodes(self):
		pbNodes = pm.ls("*", type = "mnsPoseBlend")
		return pbNodes

	def getCurrentPbSelection(self):
		currentItem = self.poseBlends_lst.currentItem()
		if currentItem:
			return self.poseBlends_lst.currentItem().text()

	def getSelectedPbNode(self):
		currentSelection = self.getCurrentPbSelection()
		if currentSelection:
			currentSelection = mnsUtils.checkIfObjExistsAndSet(currentSelection)
			if currentSelection:
				return currentSelection

	def initializeView(self, **kwargs):
		restoreSelection = kwargs.get("restoreSelection", "")
		
		self.pbNodes = []
		self.poseBlends_lst.clear()
		self.sourceAttrs_lst.clear()
		self.targetTransforms_lst.clear()
		self.create_trv.clear()
		self.setCreateWidgetsMode(0)

		self.pbNodes = self.getAllPoseBlendNodes()
		if self.pbNodes:
			self.poseBlends_lst.addItems([p.nodeName() for p in self.pbNodes])
			if restoreSelection:
				for i in range(self.poseBlends_lst.count()):
					item = self.poseBlends_lst.item(i)
					if item.text() == restoreSelection:
						self.poseBlends_lst.setCurrentItem(item)
						break

			if not self.getCurrentPbSelection():
				firstRowItem = self.poseBlends_lst.item(0)
				self.poseBlends_lst.setCurrentItem(firstRowItem)

		self.create_trv.setColumnWidth(self.col_sourceAttr, 170)
		for i in range(self.col_weight, self.col_isStored):
			self.create_trv.setColumnWidth(i, 70)
		self.create_trv.setColumnHidden(self.col_isStored, True)
		self.create_trv.setColumnHidden(self.col_sourceAttrName, True)
		self.create_trv.setColumnHidden(self.col_index, True)
		self.export_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.import_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.setFlagsForPbNode()

	def setFlagCbxStateNoSignal(self, cbx, state):
		if cbx:
			cbx.blockSignals(True)
			cbx.setChecked(state)
			cbx.blockSignals(False)

	def setFlagsForPbNode(self):
		self.flags_gbx.setEnabled(False)
		self.setFlagCbxStateNoSignal(self.doT_cbx, False)
		self.setFlagCbxStateNoSignal(self.doR_cbx, False)
		self.setFlagCbxStateNoSignal(self.doS_cbx, False)
		self.setFlagCbxStateNoSignal(self.doCA_cbx, False)

		pbNode = self.getSelectedPbNode()
		if pbNode:
			self.flags_gbx.setEnabled(True)
			doTState = pbNode.doTranslate.get()
			self.setFlagCbxStateNoSignal(self.doT_cbx, doTState)
			doRState = pbNode.doRotate.get()
			self.setFlagCbxStateNoSignal(self.doR_cbx, doRState)
			doSState = pbNode.doScale.get()
			self.setFlagCbxStateNoSignal(self.doS_cbx, doSState)
			doCAState = pbNode.doCustomAttrs.get()
			self.setFlagCbxStateNoSignal(self.doCA_cbx, doCAState)

	def toggleCbxFlagState(self, state):
		cbx = self.sender()
		pbNode = self.getSelectedPbNode()

		if pbNode and cbx:
			if cbx is self.doT_cbx:
				pbNode.doTranslate.set(cbx.isChecked())
			if cbx is self.doR_cbx:
				pbNode.doRotate.set(cbx.isChecked())
			if cbx is self.doS_cbx:
				pbNode.doScale.set(cbx.isChecked())
			if cbx is self.doCA_cbx:
				pbNode.doCustomAttrs.set(cbx.isChecked())

	def initializeSelectedPb(self):
		#clear widgets
		self.sourceAttrs_lst.clear()
		self.targetTransforms_lst.clear()

		pbNode = self.getSelectedPbNode()
		if pbNode:
			sourceAttrNames = []
			for attrIdx in range(pbNode.data.numElements()):
				inputAttr = pbNode.data[attrIdx].poseValue.listConnections(s = True, d = False, p = True)
				if inputAttr:
					inputAttr = inputAttr[0]
					inputAttrName = inputAttr.info().split(".")[-1]
					sourceAttrNames.append(inputAttrName)
			if sourceAttrNames:
				self.sourceAttrs_lst.addItems(sourceAttrNames)

			targetTransformsNames = []
			for attrIdx in range(pbNode.target.numElements()):
				inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False)
				if inputAttr:
					inputAttr = inputAttr[0]
					targetTransformsNames.append(inputAttr.nodeName())
			if targetTransformsNames:
				self.targetTransforms_lst.addItems(targetTransformsNames)
			self.setFlagsForPbNode()

	def createSourceRow(self, sourceAttr):
		inputAttr = sourceAttr.poseValue.listConnections(s = True, d = False, p = True)
		if inputAttr:
			inputAttr = inputAttr[0]
			poseName = inputAttr.info().split(".")[-1]
			rowItem = QtWidgets.QTreeWidgetItem(self.create_trv, [poseName])

			currentWeight = sourceAttr.poseWeight.get()
			rowItem.setText(self.col_weight, str(round(currentWeight,2)))

			currentMin = sourceAttr.poseMinimum.get()
			rowItem.setText(self.col_min, str(round(currentMin,2)))

			currentMax = sourceAttr.poseMaximum.get()
			rowItem.setText(self.col_max, str(round(currentMax,2)))

			inputAttr = sourceAttr.poseValue.listConnections(s = True, d = False, p = True)
			if inputAttr:
				inputAttr = inputAttr[0]
				rowItem.setText(self.col_sourceAttrName, inputAttr.name())

			rowItem.setText(self.col_index, str(sourceAttr.index()))

	def toggleTrigger(self):
		currentValue = self.value_sb.value()
		if currentValue <= 0.5:
			self.value_sb.setValue(1.0)
		else:
			self.value_sb.setValue(0.0)

	def setCreateWidgetsMode(self, mode = 0):
		# mode 0 = disable
		# mode 1 = enable
		# mode 2 = edit
		# mode 3 = stop edit

		if mode == 0:
			self.create_gbx.setEnabled(False)
			self.edit_btn.setStyleSheet("QPushButton{\ncolor:#8e8c8c;\nbackground-color:#7e7d7d;\nborder-style: solid;\nborder-color: #8e8c8c;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#7e7d7d;}\nQPushButton:pressed{background-color:#282828;}\n")
			self.value_sb.setValue(0.0)
			self.value_sl.setValue(0)
			self.weight_sb.setValue(0.0)
			self.weight_sl.setValue(0)
			self.min_sb.setValue(0.0)
			self.min_sl.setValue(0)
			self.max_sb.setValue(0.0)
			self.max_sl.setValue(0)
		elif mode == 1 or mode == 3:
			self.create_gbx.setEnabled(True)
			self.edit_btn.setStyleSheet("QPushButton{\ncolor:#000000;\nbackground-color:#7c964a;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#9ebf5f;}\nQPushButton:pressed{background-color:#282828;}\n")
			self.value_sb.setEnabled(True)
			self.value_sl.setEnabled(True)
			self.weight_sb.setEnabled(True)
			self.weight_sl.setEnabled(True)
			self.min_sb.setEnabled(True)
			self.min_sl.setEnabled(True)
			self.max_sb.setEnabled(True)
			self.max_sl.setEnabled(True)
			self.toggle_btn.setEnabled(True)
			if mode == 3:
				self.editTargetTransforms(mode = 0)
				mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
		elif mode == 2:
			self.value_sb.setValue(1.0)
			self.value_sl.setValue(100)

			self.value_sb.setEnabled(False)
			self.value_sl.setEnabled(False)
			self.weight_sb.setEnabled(False)
			self.weight_sl.setEnabled(False)
			self.min_sb.setEnabled(False)
			self.min_sl.setEnabled(False)
			self.max_sb.setEnabled(False)
			self.max_sl.setEnabled(False)
			self.toggle_btn.setEnabled(False)
			self.editTargetTransforms(mode = 1)

	def editTargetTransforms(self, mode = 0):
		pbNode = self.getSelectedPbNode()
		if pbNode:
			if mode == 0: #re-connect
				mnsFacialMocapUtils.connectOutputs(pbNode, mode = 1)
			elif mode == 1: #disconnect
				mnsFacialMocapUtils.connectOutputs(pbNode, mode = 0)

	def initCreateWidget(self):
		self.setCreateWidgetsMode(0)

		pbNode = self.getSelectedPbNode()
		if pbNode:
			for attrIdx in range(pbNode.data.numElements()):
				sourceAttr = pbNode.data[attrIdx]
				self.createSourceRow(sourceAttr)
			
	def switchUIStates(self):
		currentSelectedPBNode = self.getSelectedPbNode()
		if currentSelectedPBNode:
			currentIndex = self.main_sw.currentIndex()
			if currentIndex == 0: 
				self.main_sw.setCurrentIndex(1)
				mnsFacialMocapUtils.muteSourceAttrs(currentSelectedPBNode, mode = 0)
				self.initCreateWidget()
			elif currentIndex == 1: 
				self.main_sw.setCurrentIndex(0)
				mnsFacialMocapUtils.muteSourceAttrs(currentSelectedPBNode, mode = 1)
				self.create_trv.clear()

	def setSourceValues(self, currentItem, previousItem):
		if self.edit_sw.currentIndex() == 0:
			pbNode = self.getSelectedPbNode()
			if pbNode:
				self.setCreateWidgetsMode(mode = 1)

				poseWeight = 1.0
				poseMinimum = 0.0
				poseMaximum = 0.0

				if currentItem:
					poseWeight = float(currentItem.text(self.col_weight))
					poseMinimum = float(currentItem.text(self.col_min))
					poseMaximum = float(currentItem.text(self.col_max))

				self.value_sb.blockSignals(True)
				self.weight_sb.blockSignals(True)
				self.min_sb.blockSignals(True)
				self.max_sb.blockSignals(True)
				self.value_sb.setValue(1.0)
				self.value_sl.setValue(100)
				self.weight_sb.setValue(poseWeight)
				self.weight_sl.setValue(int(poseWeight * 100))
				self.min_sb.setValue(poseMinimum)
				self.min_sl.setValue(int(poseMinimum * 100))
				self.max_sb.setValue(poseMaximum)
				self.max_sl.setValue(int(poseMaximum * 100))
				self.value_sb.blockSignals(False)
				self.weight_sb.blockSignals(False)
				self.min_sb.blockSignals(False)
				self.max_sb.blockSignals(False)

				#disconnect and zero previous
				if previousItem:
					index = int(previousItem.text(self.col_index))
					inputAttr = pbNode.data[index].poseValue.listConnections(s = True, d = False, p = True)
					
					if inputAttr:
						inputAttr = inputAttr[0]
						inputAttr.set(0.0)

				#connect new and set to 1
				if currentItem:
					index = int(currentItem.text(self.col_index))
					inputAttr = pbNode.data[index].poseValue.listConnections(s = True, d = False, p = True)
					
					if inputAttr:
						inputAttr = inputAttr[0]
						inputAttr.set(1.0)

	def setSbSliderValue(self, newValue):
		sourceWidget = self.sender()
		
		if sourceWidget in self.sbSliderPairing:
			targetWidget = self.sbSliderPairing[sourceWidget]
			targetWidget.blockSignals(True)

			if type(sourceWidget) == QtWidgets.QSlider:
				targetWidget.setValue(float(sourceWidget.value()) / 100.0)
			elif type(sourceWidget) == QtWidgets.QDoubleSpinBox:
				targetWidget.setValue(sourceWidget.value() * 100)
			
			targetWidget.blockSignals(False)

		selectedSourceItems = self.create_trv.selectedItems()
		pbNode = self.getSelectedPbNode()

		if selectedSourceItems and pbNode and (sourceWidget in self.widgetAttrPairing.keys()):
			selectedSourceItem = selectedSourceItems[0]
			targetAttrName = self.widgetAttrPairing[sourceWidget]
			
			index = int(selectedSourceItem.text(self.col_index))
			if type(sourceWidget) == QtWidgets.QSlider:
				newValue = float(newValue) / 100.0

			if targetAttrName == "poseValue":
				inputAttr = pbNode.data[index].attr(targetAttrName).listConnections(s = True, d = False, p = True)
				if inputAttr:
						inputAttr = inputAttr[0]
						inputAttr.set(newValue)
			else:
				pbNode.data[index].attr(targetAttrName).set(newValue)

	def getSelectedTargetTransforms(self):
		currentItems = self.targetTransforms_lst.selectedItems()
		if currentItems:
			newSelection = [c.text() for c in currentItems]
			validatedSelection = []
			for nc in newSelection:
				validatedNode = mnsUtils.checkIfObjExistsAndSet(nc)
				if validatedNode:
					validatedSelection.append(validatedNode)

			if validatedSelection:
				pm.select(validatedSelection, r = True)

	def selectTargetTransforms(self):
		self.getSelectedTargetTransforms()

	def getAllTargetTransforms(self):
		targetTransforms = []
		for itemIdx in range(self.targetTransforms_lst.count()):
			targetTransforms.append(self.targetTransforms_lst.item(itemIdx).text())
		return targetTransforms

	def switchEditUIState(self):
		if self.edit_sw.currentIndex() == 0: #edit
			self.edit_sw.setCurrentIndex(1)
			self.setCreateWidgetsMode(mode = 2)
			self.create_trv.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		elif self.edit_sw.currentIndex() == 1: #save/cancel
			if self.sender() is self.save_btn: #save
				selectedItems = self.create_trv.selectedItems()
				pbNode = self.getSelectedPbNode()
				if selectedItems and pbNode:
					selectedItem = selectedItems[0]
					poseName = selectedItem.text(self.col_sourceAttr)
					mnsFacialMocapUtils.storePose(pbNode, poseName)
			self.create_trv.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

			self.edit_sw.setCurrentIndex(0)
			self.setCreateWidgetsMode(mode = 3)

	##################	
	##### Action #####
	##################

	def selectPbNode(self):
		currentSelectedPBNode = self.getSelectedPbNode()
		if currentSelectedPBNode:
			pm.select(currentSelectedPBNode, r = True)

	def deletePbNode(self):
		currentSelectedPBNode = self.getSelectedPbNode()
		if currentSelectedPBNode:
			reply = QtWidgets.QMessageBox.question(None, 'Are you sure?', "This action will delete the selected poseBlend Node, and all pose storage witthin.<br>Are you sure you want to continue?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
			if reply == QtWidgets.QMessageBox.Yes:
				pm.delete(currentSelectedPBNode)
				self.initializeView()

	#sources list
	def getSelectedSourceAttrs(self):
		selectedItems = self.sourceAttrs_lst.selectedItems()
		if selectedItems:
			return [s.text() for s in selectedItems]

	def addSelectedCBSourceAttrs(self, **kwargs):
		mode = kwargs.get("mode", 0) #0 - add, 1 - replace

		channelSelection = pm.channelBox ('mainChannelBox', query=True, selectedMainAttributes=True)
		sel = pm.ls(sl=1, ap=1)

		if sel and channelSelection:
			validatedAttrs = []
			for channelName in channelSelection:
				status, attr = mnsUtils.validateAttrAndGet(sel[0], channelName, None, returnAttrObject = True)
				if status:
					validatedAttrs.append(attr)
			
			if validatedAttrs:
				mnsFacialMocapUtils.connectSourceAttrsToPB(self.getSelectedPbNode(), validatedAttrs, mode = mode)
				mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
				self.initializeSelectedPb()
	
	def removeSelectedSourceAttrs(self, **kwargs):
		mode = kwargs.get("mode", 0) #0 - remove, 1 - clear

		if mode == 0:
			currentSelectedSourceAttrs = self.getSelectedSourceAttrs()
			if currentSelectedSourceAttrs:
				mnsFacialMocapUtils.removeSourceAttrsFromPbNode(self.getSelectedPbNode(), currentSelectedSourceAttrs)
				mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
				self.initializeSelectedPb()
		elif mode == 1:
			mnsFacialMocapUtils.removeSourceAttrsFromPbNode(self.getSelectedPbNode(), mode = mode)
			mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
			self.initializeSelectedPb()

	#transforms list
	def getSelectedTragetTransforms(self):
		selectedItems = self.targetTransforms_lst.selectedItems()
		if selectedItems:
			return [s.text() for s in selectedItems]

	def addSelectedTransformsToPB(self):
		sel = pm.ls(sl=True, type = "transform")
		if sel:
			mnsFacialMocapUtils.connectTargetTransformsToPbNode(self.getSelectedPbNode(), sel)
			mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
			self.initializeSelectedPb()

	def removeSelectedTransformsFromPB(self, **kwargs):
		mode = kwargs.get("mode", 0) #0 - remove, 1 - clear

		reply = QtWidgets.QMessageBox.question(None, 'Are you sure?', "This action will remove all stored pose data for the selected transforms.<br>Are you sure you want to continue?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.Yes:
			if mode == 0:
				currentSelectedTargetTransforms = self.getSelectedTragetTransforms()
				if currentSelectedTargetTransforms:
					mnsFacialMocapUtils.removeTargetTransformsFromPbNode(self.getSelectedPbNode(), currentSelectedTargetTransforms)
					mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
					self.initializeSelectedPb()
			elif mode == 1:
				mnsFacialMocapUtils.removeTargetTransformsFromPbNode(self.getSelectedPbNode(), mode = mode)
				mnsFacialMocapUtils.refreshPbNode(self.getSelectedPbNode())
				self.initializeSelectedPb()
		
	#create new
	def createNewDefinition(self):
		#name dialog
		text, ok = QtWidgets.QInputDialog.getText(self, 'New Definition', 'Definition Name:')
		if text:
			pbNode = mnsNodes.mnsPoseBlendNode(body = text)
			self.initializeView(restoreSelection = pbNode.name)
	
	def importFMData(self):
		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Information)
		msg.setText("<font size = 4><b>Before you continue, here are some things to be mindful of:</b>")
		msg.setInformativeText("<font size = 4><ul><li>Make sure that the source attributes node/s have the same name as they did when they where exported. If the name doesn't match, the system will not be able to find them.<br></li><li>In case you are using namespaces in your import scene, please make sure to input them into the next dialog in order for the system to be able to take them under consideration.</li></ul>")
		msg.setWindowTitle("Import Info")
		msg.exec_()

		status = mnsFacialMocapUtils.importFMDataFromFile()
		if status:
			loadFacialMocapTool()
			
	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsFacialMocapTool", svr = 0)
		self.show()

def loadFacialMocapTool(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("Facial Mocap Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsFacialMocapTool")

	mnsUtils.isPluginLoaded("mnsPoseBlend")
	MnsFacialMocapToolWin = MnsFacialMocapTool()
	MnsFacialMocapToolWin.loadWindow()
	if previousPosition: MnsFacialMocapToolWin.move(previousPosition)
	return MnsFacialMocapToolWin