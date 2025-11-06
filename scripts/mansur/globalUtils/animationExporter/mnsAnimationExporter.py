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
import os, random, json
import maya.OpenMaya as OpenMaya
from maya import cmds
infoNodeName = "mnsAnimationExporterInfo"
infoNodeAttrName = "animExporterDefault"

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import nodes as mnsNodes
from ...core import skinUtility as mnsSkinUtils
from ...core import meshUtility as mnsMeshUtils
from ...block.core import blockUtility as blkUtils
from ...gui import gui as mnsGui
from ...core.globals import *

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

class ExtraAttributesListWidget(QtWidgets.QListWidget):
	"""A simple QPushButton re-implementation.
	This reimplementation is used to control the button's mouse events, used in 'Edit' mode.
	"""

	def __init__(self, parent = None, default_extraAttrs = [],  **kwargs):
		super(ExtraAttributesListWidget, self).__init__(parent)

		self.parent = parent
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.openExtraAttrsMenu)
		self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		if default_extraAttrs:
			self.addItems(default_extraAttrs)

		#locals
		self.acceptedAttributeTypes = ["float", "double", "doubleLinear", "doubleAngle", "bool", "long", "short", "byte", "enum", "time"]
	
	def getItems(self):
		returnList = []
		for rowIdx in range(self.count()):
			returnList.append(self.item(rowIdx).text())

		return returnList

	def copyList(self):
		if self.parent:
			self.parent.extraAttrsClipboard = self.getItems()
	
	def pasteList(self, **kwargs):
		replace = kwargs.get("replace", True)

		if self.parent and self.parent.extraAttrsClipboard:
			if replace:
				self.clear()
			self.addItems(self.parent.extraAttrsClipboard)
			self.sortItems()

	def validateAttribute(self, node, attributeName):
		if node and attributeName:
			attObj = node.attr(attributeName)
			if attObj.type() in self.acceptedAttributeTypes:
				return True
		return False	

	def addAttributesToList(self, **kwargs):
		replace = kwargs.get("replace", False)
		fromClipboard = kwargs.get("fromClipboard", False)
		
		cbSelection = []
		if fromClipboard and self.parent.extraAttrsClipboard:
			cbSelection = self.parent.extraAttrsClipboard
		else:
			cbSelection = pm.channelBox ('mainChannelBox', query=True, selectedMainAttributes=True)
		
		if cbSelection:
			if replace: self.clear()
			currentItems = self.getItems()

			if fromClipboard:
				for attrName in self.parent.extraAttrsClipboard:
					if attrName not in currentItems:
						self.addItem(attrName)
					else:
						mnsLog.log("Item: " + attrName + " already in list, skipping.", svr = 2)
			else:				
				for objectSel in pm.ls(sl = True):
					for attrName in cbSelection:
						attrFullName = objectSel.nodeName() + "." + attrName
						if attrFullName not in currentItems:
							if self.validateAttribute(objectSel, attrName):
								self.addItem(attrFullName)
						else:
							mnsLog.log("Item: " + attrName + " already in list, skipping.", svr = 2)
			self.sortItems() 

	def removeSelectedItems(self):
		selectedIndexes = self.selectedIndexes()
		if selectedIndexes:
			indexed = sorted([r.row() for r in selectedIndexes])
			for itemIdx in indexed[::-1]:
				self.takeItem(itemIdx)
			self.sortItems() 

	def openExtraAttrsMenu(self, position):
		menu = QtWidgets.QMenu()

		addSelectedAction = menu.addAction(self.tr("Add Channel-Box Selection"))
		addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
		addSelectedAction.triggered.connect(self.addAttributesToList)

		if self.selectedIndexes():
			removeSelectedAction = menu.addAction(self.tr("Remove Selected"))  
			removeSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
			removeSelectedAction.triggered.connect(self.removeSelectedItems)

		loadSelectedAction = menu.addAction(self.tr("Replace with Selected"))  
		loadSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/RS_refresh_layer.png")))
		loadSelectedAction.triggered.connect(lambda: self.addAttributesToList(replace = True))

		clearAction = menu.addAction(self.tr("Clear"))  
		clearAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/clip_mute.png")))
		clearAction.triggered.connect(self.clear)

		if self.getItems():
			copyAction = menu.addAction(self.tr("Copy List"))  
			copyAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/copyUV.png")))
			copyAction.triggered.connect(self.copyList)

		if self.parent.extraAttrsClipboard:
			pasteAction = menu.addAction(self.tr("Paste (Replace)"))  
			pasteAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/pasteUV.png")))
			pasteAction.triggered.connect(self.pasteList)
				
			pasteActionAdd = menu.addAction(self.tr("Paste (Add)"))  
			pasteActionAdd.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/pasteUV.png")))
			pasteActionAdd.triggered.connect(lambda: self.addAttributesToList(fromClipboard = True))

		menu.exec_(self.viewport().mapToGlobal(position))

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsAnimationExporter.ui")
class MnsAnimationExporter(form_class, base_class):
	"""Spaces Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsAnimationExporter, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsAnimationExporter") 
		iconDir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/icons/mansur_01.png"
		winIconDir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/icons/mansur_logo_noText.png"
		self.iconLbl.setPixmap(QtGui.QPixmap(iconDir))
		self.setWindowIcon(QtGui.QIcon(winIconDir))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		# locals
		self.rigTabsPairing = {}
		self.infoNode = None
		self.ranges_vs = None
		self.initializeView()
		self.validateUIInfoNode()
		loadMsg = self.loadUIInfo()
		
		self.extraAttrsClipboard = None

		#run
		self.initializeWidgets()
		self.connectSignals()
		mnsGui.setGuiStyle(self, "Game Exporter")
		
		if loadMsg:
			loadMsg.exec_()

	##################	
	###### INIT ######
	##################

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.addRig_btn.released.connect(self.addRig)
		self.addRange_btn.released.connect(self.addRange)
		self.resetUI_btn.released.connect(self.resetUI)
		self.export_btn.released.connect(self.export)
		self.saveData_btn.released.connect(self.storeData)
		self.delData_btn.released.connect(self.delData)
	
	##################	
	###### View ######
	##################

	def initializeWidgets(self):
		pass

	def initializeView(self):
		pass
		
	def resetUI(self):
		currentWidget = self.rigs_tw.currentWidget()
		if currentWidget in self.rigTabsPairing:
			contentLO = self.rigTabsPairing[currentWidget]["contentLO"]
			rigTopLE = self.rigTabsPairing[currentWidget]["rigTopLE"]
			rigTopLE.clear()
			mnsUIUtils.recDeleteAllLayoutItems(contentLO)

	def random_color(self):
		r = random.randrange(255)
		g = random.randrange(255)
		b = random.randrange(255)
		return '#%02x%02x%02x' % (int(r), int(g), int(b))

	def deleteRange(self):
		rangeGrpBox = self.sender().parentWidget()
		currentWidget = self.rigs_tw.currentWidget()

		#first delete tab
		if currentWidget in self.rigTabsPairing:
			contentLO = self.rigTabsPairing[currentWidget]["contentLO"]

			rangeGrpBoxIdx = contentLO.indexOf(rangeGrpBox)
			contentLO.takeAt(rangeGrpBoxIdx)
			rangeGrpBox.deleteLater()
			
			#renameRanges
			for rangeGrpBoxIdx in range(contentLO.count()):
				rangeGrpBox = contentLO.itemAt(rangeGrpBoxIdx)
				if type(rangeGrpBox) == QtWidgets.QWidgetItem:
					lo = rangeGrpBox.widget().layout()
					for childWidIdx in range(lo.count()):
						childWid = lo.itemAt(childWidIdx)
						if type(childWid) == QtWidgets.QHBoxLayout:
							for childWidIdxA in range(childWid.count()):
								childWidA = childWid.itemAt(childWidIdxA).widget()
								if type(childWidA) == QtWidgets.QLabel:
									childWidA.setText("range " + str(rangeGrpBoxIdx + 1))
									break

	def deleteRig(self):
		currentWidget = self.rigs_tw.currentWidget()
		currentWidgetIndex = self.rigs_tw.indexOf(currentWidget)

		#first delete tab
		if currentWidget in self.rigTabsPairing:
			contentLO = self.rigTabsPairing[currentWidget]["contentLO"]
			mnsUIUtils.recDeleteAllLayoutItems(contentLO)
			self.rigs_tw.removeTab(currentWidgetIndex)

		restoreIndex = self.rigs_tw.currentIndex()

		#now rename other tabs
		for idx in range(self.rigs_tw.count()):
			self.rigs_tw.setCurrentIndex(idx)
			self.rigs_tw.setTabText(idx, "Rig " + str(idx + 1))

		self.rigs_tw.setCurrentIndex(restoreIndex)

		if self.rigs_tw.count() == 0:
			self.addRig()

	def getRangePath(self, lineEditWidget):
		if lineEditWidget:
			filename = QtWidgets.QFileDialog.getSaveFileName(mnsUIUtils.get_maya_window(), "Range Export File Path", None, "FBX (*.fbx)")
			if filename[0]:
				lineEditWidget.setText(filename[0])

	def setRangeMode(self, widgets, isAsset):
		for wid in widgets:
			wid.setEnabled(not isAsset)

	def addRange(self, **kwargs):
		currentWidget = self.rigs_tw.currentWidget()
		if currentWidget in self.rigTabsPairing:
			contentLO = self.rigTabsPairing[currentWidget]["contentLO"]
			VSpacer = self.rigTabsPairing[currentWidget]["VSpacer"]

			default_path = kwargs.get("path", "")
			default_isAsset = kwargs.get("isAsset", False)
			default_min = kwargs.get("min", pm.playbackOptions(q=True, min=True))
			default_max = kwargs.get("max", pm.playbackOptions(q=True, max=True))
			default_extraAttrs = kwargs.get("extraAttributes", [])
			fromInit = kwargs.get("fromInit", False)

			numOfRanges = contentLO.count()

			if numOfRanges > 1 and not default_extraAttrs and not fromInit:
				#this means there is a previous range, with extra attributes set, and no default extra attributes were passed in 
				#get previous rnage extra attributes and set as default
				prevRangeGrpBox = contentLO.itemAt(numOfRanges - 2)
				if prevRangeGrpBox:
					lo = prevRangeGrpBox.widget().layout()
					for childWidIdx in range(lo.count()):
						childWid = lo.itemAt(childWidIdx)
						if type(childWid) == QtWidgets.QGridLayout:
							for childWidIdxA in range(childWid.count()):
								childWidA = childWid.itemAt(childWidIdxA).widget()
								if childWidA:
									if type(childWidA) == ExtraAttributesListWidget:
										default_extraAttrs = childWidA.getItems()
										break
							break

			if VSpacer:
				#remove spacer
				spacerIdx = contentLO.indexOf(VSpacer)
				contentLO.takeAt(spacerIdx)
			
			#main group box
			grpBox = QtWidgets.QGroupBox()
			grpBox.setMinimumHeight(220)
			grpBox.setMaximumHeight(220)
			grpBox_lo = QtWidgets.QVBoxLayout()
			grpBox_lo.setContentsMargins(6, 6, 6, 10)
			grpBox.setLayout(grpBox_lo)

			#title
			titleLayout = QtWidgets.QHBoxLayout()
			delButton = QtWidgets.QPushButton("")
			delButton.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png"))
			delButton.setStyleSheet("QPushButton{\nbackground-color:#404040;\nborder-style: sunken;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
			delButton.setMinimumSize(32, 26)
			delButton.setMaximumSize(32, 26)
			delButton.released.connect(self.deleteRange)
			titleLayout.addWidget(delButton)
			title = QtWidgets.QLabel("Range " + str(numOfRanges))
			title.setStyleSheet("QLabel{\nbackground-color:#1f4c58;\nborder-style: solid;\nborder-color: black;\nborder-width: 0px;\nborder-radius: 3px;}\n")
			title.setMaximumHeight(23)
			title.setMinimumHeight(23)
			title.setAlignment(QtCore.Qt.AlignCenter)
			titleLayout.addWidget(title)
			grpBox_lo.addLayout(titleLayout)

			grpBox_lo_vs = QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
			grpBox_lo.addItem(grpBox_lo_vs)

			#content layout
			contentLo = QtWidgets.QGridLayout()

			#path
			pathLabel = QtWidgets.QLabel("Export Path:")
			pathLabel.setMinimumWidth(100)
			pathLabel.setMinimumHeight(23)
			contentLo.addWidget(pathLabel, 0, 0)
			
			pathLineEdit = QtWidgets.QLineEdit(default_path)
			pathLineEdit.setMinimumHeight(23)
			contentLo.addWidget(pathLineEdit, 0, 1)
			pathSetBtn = QtWidgets.QPushButton("")
			pathSetBtn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/folder-open.png"))
			pathSetBtn.setStyleSheet("QPushButton{\nbackground-color:#404040;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
			pathSetBtn.setMinimumSize(26, 23)
			pathSetBtn.released.connect(partial(self.getRangePath, pathLineEdit))

			contentLo.addWidget(pathSetBtn, 0, 2)

			grpBox_lo.addLayout(contentLo)

			#range
			rangeAssetGrpBox = QtWidgets.QGroupBox()
			rangeAssetGrpBox.setAccessibleName("transparent")
			rangeAssetGrpBox.setMinimumHeight(21)
			rangeAssetGrpBox.setMaximumHeight(21)
			rangeAssetGrpBox_lo = QtWidgets.QHBoxLayout()
			rangeAssetGrpBox_lo.setSpacing(0)
			rangeAssetGrpBox_lo.setContentsMargins(0, 0, 0, 0)
			rangeAssetGrpBox.setLayout(rangeAssetGrpBox_lo)
			contentLo.addWidget(rangeAssetGrpBox, 1, 1)

			rangeRb = QtWidgets.QRadioButton("Range")
			assetRb = QtWidgets.QRadioButton("Asset")
			rangeAssetGrpBox_lo.addWidget(rangeRb)
			rangeAssetGrpBox_lo.addWidget(assetRb)
			pathLabel = QtWidgets.QLabel("Frame Range:")
			pathLabel.setMinimumWidth(100)
			contentLo.addWidget(pathLabel, 2, 0)

			rangeLO = QtWidgets.QHBoxLayout()
			rangeMinSB = QtWidgets.QSpinBox()
			rangeMinSB.setMaximum(10000)
			rangeMinSB.setMinimum(-10000)
			rangeMinSB.setValue(default_min)
			rangeMinSB.setMaximumWidth(70)
			rangeLO.addWidget(rangeMinSB)
			toLabel = QtWidgets.QLabel("To:")
			toLabel.setAlignment(QtCore.Qt.AlignCenter)
			rangeLO.addWidget(toLabel)
			rangeMaxSB = QtWidgets.QSpinBox()
			rangeMaxSB.setMaximum(10000)
			rangeMaxSB.setMinimum(-10000)
			rangeMaxSB.setValue(default_max)
			rangeMaxSB.setMaximumWidth(70)
			rangeLO.addWidget(rangeMaxSB)
			contentLo.addLayout(rangeLO, 2, 1)

			extraAttrsLabel = QtWidgets.QLabel("Extra Attributes:")
			extraAttrsLabel.setMinimumWidth(100)
			extraAttrsLabel.setMinimumHeight(23)
			contentLo.addWidget(extraAttrsLabel, 3, 0)
			extraAttrsLabel.setToolTip("Use Right Click Menu.<br>Extra channels to bake.<br>The attributes will be inserted and baked to the highest level joint in the extracted hierarchy.")

			extraAttrsTW = ExtraAttributesListWidget(self, default_extraAttrs)
			extraAttrsTW.setMinimumHeight(75)
			extraAttrsTW.setMaximumHeight(75)

			contentLo.addWidget(extraAttrsTW, 3, 1)

			"""
			extraAttrsEnlargeBtn = QtWidgets.QPushButton()
			extraAttrsEnlargeBtn.setStyleSheet("QPushButton{\nbackground-color:#404040;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
			extraAttrsEnlargeBtn.setMinimumHeight(68)
			extraAttrsEnlargeBtn.setMaximumHeight(68)
			extraAttrsEnlargeBtn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/zoom.png"))
			contentLo.addWidget(extraAttrsEnlargeBtn, 3, 2)
			"""

			assetRb.toggled.connect(partial(self.setRangeMode, [rangeMinSB, rangeMaxSB, toLabel, pathLabel]))
			rangeRb.setChecked(not default_isAsset)
			assetRb.setChecked(default_isAsset)

			grpBox_lo_vs = QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			grpBox_lo.addItem(grpBox_lo_vs)

			#add group box
			contentLO.addWidget(grpBox)
			
			#re-insert spacer
			if VSpacer:
				contentLO.addItem(VSpacer)

	def addRig(self, **kwargs):
		fromInit = kwargs.get("fromInit", False)

		tabIndex = self.rigs_tw.count()
		tabTitle = "Rig " + str(tabIndex + 1)
		
		newTab = QtWidgets.QWidget()
		tabContentLO =  QtWidgets.QVBoxLayout(newTab)
		
		#rigTop
		rigTopLO = QtWidgets.QGridLayout()

		delButton = QtWidgets.QPushButton("")
		delButton.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png"))
		delButton.setStyleSheet("QPushButton{\nbackground-color:#404040;\nborder-style: sunken;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
		delButton.setMinimumSize(32, 26)
		delButton.setMaximumSize(32, 26)
		delButton.released.connect(self.deleteRig)
		rigTopLO.addWidget(delButton, 0, 0)

		rogTopLbl = QtWidgets.QLabel("Rig-Top Node:")
		rogTopLbl.setMinimumWidth(100)
		rogTopLbl.setMinimumHeight(23)
		rigTopLO.addWidget(rogTopLbl, 0, 1)
	
		rigTopLineEdit = QtWidgets.QLineEdit()
		rigTopLineEdit.setMinimumHeight(23)
		rigTopLO.addWidget(rigTopLineEdit, 0, 2)
		rigTopSetBtn = QtWidgets.QPushButton("<")
		rigTopSetBtn.setStyleSheet("QPushButton{\nbackground-color:#404040;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
		rigTopSetBtn.setMinimumSize(26, 23)
		rigTopSetBtn.released.connect(lambda: mnsUIUtils.loadCmd(rigTopLineEdit))
		rigTopLO.addWidget(rigTopSetBtn, 0, 3)
		
		tabContentLO.addLayout(rigTopLO)

		#scroll
		newScroll = QtWidgets.QScrollArea(newTab)
		newScroll.setWidgetResizable(True)
		newScrollContent = QtWidgets.QWidget()
		scrollContentLOA = QtWidgets.QVBoxLayout(newScrollContent)
		newScroll.setWidget(newScrollContent)
		tabContentLO.addWidget(newScroll)
		self.rigs_tw.insertTab(-1, newTab, tabTitle)

		ranges_vs = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
		scrollContentLOA.addItem(ranges_vs)

		self.rigTabsPairing[newTab] = {"contentLO": scrollContentLOA, "VSpacer": ranges_vs, "rigTopLE": rigTopLineEdit}
		self.rigs_tw.setCurrentIndex(tabIndex)

	##################	
	##### Action #####
	##################
	
	def loadUIInfo(self):
		self.validateUIInfoNode()
		if self.infoNode:
			previousData = None
			try:
				previousData = json.loads(self.infoNode.attr(infoNodeAttrName).get())
			except:
				pass

			if previousData and type(previousData) is dict:
				globalSettings = previousData["globalSettings"]
				rangesData = previousData["rangesData"]

				for rigTopName in rangesData.keys():
					self.addRig()
					currentWidget = self.rigs_tw.currentWidget()
					if currentWidget in self.rigTabsPairing.keys():
						rigTopLineEdit = self.rigTabsPairing[currentWidget]["rigTopLE"]
						rigTopLineEdit.setText(rigTopName)

					for rng in rangesData[rigTopName]:
						extraAttributes = []
						if "extraAttributes" in rng.keys():
							extraAttributes = rng["extraAttributes"]
						
						self.addRange(path = rng["path"], isAsset = rng["isAsset"], min = rng["min"], max = rng["max"], extraAttributes = extraAttributes, fromInit = True)
				
				for settingCbxName in globalSettings.keys():
					if hasattr(self, settingCbxName):
						checkbox = self.findChild(QtWidgets.QCheckBox, settingCbxName)
						if checkbox:
							checkbox.setChecked(globalSettings[settingCbxName])
				
			elif previousData and type(previousData) is list:
				#backwards compatibility- < 2.5.0
				self.addRig()
				currentWidget = self.rigs_tw.currentWidget()
				
				for rng in previousData:
					extraAttributes = []
					if "extraAttributes" in rng.keys():
						extraAttributes = rng["extraAttributes"]
						
					self.addRange(path = rng["path"], isAsset = rng["isAsset"], min = rng["min"], max = rng["max"], extraAttributes = extraAttributes, fromInit = True)
				
				msg = QtWidgets.QMessageBox()
				
				msg.setIcon(QtWidgets.QMessageBox.Information)
				msg.setText("Mansur-Rig deprication warning")
				msg.setWindowTitle("Data load exception")

				infoMes = "This scene contains Game-Exporter data written prior to Mansur-Rig 2.5.0.\nThe data was loaded into the UI successfully, but please make sure to input the desired Rig-Top node into the new Rig-Top field."
				msg.setText(infoMes)
				msg.exec_()

				return msg

		if self.rigs_tw.count() == 0:
			self.addRig()

		self.rigs_tw.setCurrentIndex(0)

	def validateUIInfoNode(self):
		self.infoNode = mnsUtils.checkIfObjExistsAndSet(infoNodeName)
		if not self.infoNode:
			self.infoNode = pm.createNode("multDoubleLinear", name = infoNodeName)
			mnsUtils.addAttrToObj([self.infoNode], type = "string", value = "", name = infoNodeAttrName, locked = True)

	def gatherData(self):
		returnData = {}
		restoreIndex = self.rigs_tw.currentIndex()

		for tabIdx in range(self.rigs_tw.count()):
			self.rigs_tw.setCurrentIndex(tabIdx)
			currentWidget = self.rigs_tw.currentWidget()
			if currentWidget in self.rigTabsPairing:
				contentLO = self.rigTabsPairing[currentWidget]["contentLO"]
				rigTopLE = self.rigTabsPairing[currentWidget]["rigTopLE"]

				rigData = []
				for rangeGrpBoxIdx in range(contentLO.count()):
					rangeGrpBox = contentLO.itemAt(rangeGrpBoxIdx)
					if type(rangeGrpBox) == QtWidgets.QWidgetItem:
						lo = rangeGrpBox.widget().layout()
						for childWidIdx in range(lo.count()):
							rangeData = {}
							childWid = lo.itemAt(childWidIdx)
							if type(childWid) == QtWidgets.QGridLayout:
								for childWidIdxA in range(childWid.count()):
									childWidA = childWid.itemAt(childWidIdxA).widget()
									if childWidA:
										if type(childWidA) == QtWidgets.QLineEdit:
											path = childWidA.text()
											if path:
												rangeData.update({"path": path})
										elif type(childWidA) == ExtraAttributesListWidget:
											extraAttributes = childWidA.getItems()
											if extraAttributes:
												rangeData.update({"extraAttributes": extraAttributes})
									childLo = childWid.itemAt(childWidIdxA)
									if type(childLo) == QtWidgets.QHBoxLayout:
										gotMin = False
										for childWidBIdx in range(childLo.count()):
											childWidB = childLo.itemAt(childWidBIdx).widget()
											if type(childWidB) == QtWidgets.QSpinBox:
												value = childWidB.value()
												if not gotMin:
													rangeData.update({"min": value})
												else:
													rangeData.update({"max": value + 1})
												gotMin = True
												
												gotIsAsset = False
												if not gotIsAsset:
													isAsset = not childWidB.isEnabled()
													rangeData.update({"isAsset": isAsset})
													gotIsAsset = True

							if "path" in rangeData.keys():
								rigData.append(rangeData)			
				returnData[rigTopLE.text()] = rigData

		self.rigs_tw.setCurrentIndex(restoreIndex)
		return returnData

	def recIsMdlGrpParent(self, node):
		par = node.getParent()
		if par:
			if par.nodeName().endswith("_" + mnsPS_modelGrp):
				return True
			else:
				return self.recIsMdlGrpParent(par)
		else:
			return False

	def getSkinnedMeshesFromJntHeirarchy(self, origRootJnt):
		skinnedMeshes = []
		origRootJnt = mnsUtils.checkIfObjExistsAndSet(origRootJnt)
		geoFromMdlGrpOnly = self.geoFromMdlGrpOnly_cbx.isChecked()

		if origRootJnt:
			for j in [origRootJnt] + origRootJnt.listRelatives(ad = True, type = "joint"):
				for connectedAttr in j.worldMatrix.listConnections(d = True, s = False, p = True):
					if type(connectedAttr.node()) == pm.nodetypes.SkinCluster:
						origConnects = connectedAttr.node().listConnections(d = True, s = True, type = "mesh")
						for origConnect in origConnects:
							if origConnect not in skinnedMeshes:
								if geoFromMdlGrpOnly:
									if self.recIsMdlGrpParent(origConnect):
										skinnedMeshes.append(origConnect)
								else:
									skinnedMeshes.append(origConnect)
		return skinnedMeshes

	def getUnusedJoints(self, rootJnt, skinData):
		returnData = []
		if rootJnt and skinData:
			allUsedJnts = []
			for m in skinData:
				allUsedJnts += list(skinData[m]["weights"].keys())
			allUsedJnts = list(dict.fromkeys(allUsedJnts))
			
			for jnt in ([rootJnt] + rootJnt.listRelatives(ad = True, type = "joint")):
				pureName = mnsUtils.removeNamespaceFromString(jnt.nodeName().split("|")[-1])
				if not pureName in allUsedJnts and "_rigRoot_" not in pureName:
					if pureName not in returnData:
						returnData.append(pureName)
		return returnData

	def restructureJointHeirarchy(self, rootJnt, unusedInfluences):
		if rootJnt and unusedInfluences:
			#list relatives only, exclude root
			allJnts = rootJnt.listRelatives(ad = True, type = "joint")
			allJntsDict = {}
			for jnt in allJnts:
				allJntsDict[jnt.nodeName()] = jnt

			for unusedJntName in unusedInfluences:
				if unusedJntName in allJntsDict.keys():
					unusedJnt = allJntsDict[unusedJntName]
					children = unusedJnt.listRelatives(c = True, type = "joint")
					if children:
						pm.parent(children, unusedJnt.getParent())
					pm.delete(unusedJnt)
			return True

	def extractSkeletonFromRigTop(self, rigTop, extractMode, rotToJointOrient, includeMeshes, messageLog):
		#first, extract the sekeleton
		extractedRootJnt, origRootJnt = blkUtils.extractSkeleton2(rigTop, 
								mode = extractMode,
								rotToJointOrient = rotToJointOrient
								)

		twinDict = {}
		meshTwins = []
		skinnedMeshes = self.getSkinnedMeshesFromJntHeirarchy(origRootJnt)
		skinData = mnsSkinUtils.exportSkin(skinnedMeshes, returnData = True)
		unusedInfluences = self.getUnusedJoints(origRootJnt, skinData)

		if includeMeshes:
			if skinnedMeshes:
				for sm in skinnedMeshes:
					mt = pm.duplicate(sm)[0]
					meshTwins.append(mt)
					twinDict[sm] = mt
					mt.v.set(True)
					mnsUtils.lockAndHideAllTransforms(mt, lock = False, keyable = True, cb = True)
					pm.parent(mt, w = True)
					mt.rename(sm.nodeName().split(":")[-1] + "_mnsSkinImportTraget")
				
				#rename joints for import and store
				predefinedTargetJoints = {}
				for pdJnt in ([extractedRootJnt.node] + extractedRootJnt.node.listRelatives(ad = True, type = "joint")):
					pdJnt.rename(pdJnt.nodeName() + "_mnsSkinImportTraget")
					predefinedTargetJoints[pdJnt.nodeName()] = pdJnt
				
				#rename the output meshes in the skin data
				newSkinData = {}
				for meshKey in skinData:
					kD = skinData[meshKey]
					
					newWeights = {}
					for jntName in skinData[meshKey]["weights"].keys():
						newWeights[jntName + "_mnsSkinImportTraget"] = skinData[meshKey]["weights"][jntName]
					kD["weights"] = newWeights
					newKey = meshKey.split(":")[-1] + "_mnsSkinImportTraget"
					newSkinData[newKey] = kD

				mnsSkinUtils.importSkin(predefinedData = newSkinData, predefinedTargetJoints = predefinedTargetJoints) 
				
				for pdJnt in ([extractedRootJnt.node] + extractedRootJnt.node.listRelatives(ad = True, type = "joint")):
					pdJnt.rename(pdJnt.nodeName().replace("_mnsSkinImportTraget", ""))

				for mt in meshTwins:
					mt.rename(mt.nodeName().replace("_mnsSkinImportTraget", ""))
			else:
				status = 1
				messageLog.append("Include meshes or Asset modes were selected, but no meshes were found (nothing is bound to the Rig's joint-structure. The process continued exluding mesh export.")
		
		return extractedRootJnt, origRootJnt, meshTwins, skinnedMeshes, skinData, unusedInfluences, twinDict, messageLog
	
	def saveWSAnimData(self, joints, rangeMin, rangeMax):
		animData = {}
		if joints:
			for frame in range(rangeMin, rangeMax):
				animData[frame] = {}
				pm.currentTime(frame, e = True)
				for jnt in joints:
					animData[frame][jnt] = pm.xform(jnt, q = True, ws=True, a = True, m = True)
		return animData

	def loadWSAnimData(self, animData):
		if animData:
			reorderedjoints = {}
			for j in animData[list(animData.keys())[0]].keys():
				if mnsUtils.checkIfObjExistsAndSet(j):
					numParents = (len(j.longName().split("|")) - 2)
					if numParents in reorderedjoints:
						reorderedjoints[numParents].append(j)
					else:
						reorderedjoints[numParents] = [j]
			
			for frame in animData.keys():
				pm.currentTime(frame, e = True)
				
				for i in range(min(reorderedjoints.keys()), max(reorderedjoints.keys()) + 1):
					for jnt in reorderedjoints[i]:
						pm.xform(jnt, ws=True, a = True, m = animData[frame][jnt])
						pm.setKeyframe(jnt)
	
	def writeDefaultData(self, exportData = {}):
		if self.infoNode:
			#store global settings
			newExportData = {
							"globalSettings": 
											{"normRanges_cbx": self.normRanges_cbx.isChecked(),
											 "resetRootJnt_cbx": self.resetRootJnt_cbx.isChecked(),
											 "includeMeshes_cbx": self.includeMeshes_cbx.isChecked(),
											 "geoFromMdlGrpOnly_cbx": self.geoFromMdlGrpOnly_cbx.isChecked(),
											 "rotToJO_cbx": self.rotToJO_cbx.isChecked(),
											 "deleteUnusedJnts_cbx": self.deleteUnusedJnts_cbx.isChecked()
											},
							"rangesData": {}
							}

			for rigTopName in exportData:
				exportRangesAbs = []
				for rng in exportData[rigTopName]:
					absRange = rng
					absRange["max"] = absRange["max"] - 1
					exportRangesAbs.append(absRange)
				newExportData["rangesData"][rigTopName] = exportRangesAbs

			mnsUtils.setAttr(self.infoNode.attr(infoNodeAttrName), json.dumps(newExportData))

	def bakeExtraAttributes(self, rng, host):
		returnAttrs = []
		if "extraAttributes" in rng.keys() and host:
			if rng["extraAttributes"]:
				for extraAttrName in rng["extraAttributes"]:
					nodeName, attrName = extraAttrName.split(".")
					node = mnsUtils.checkIfObjExistsAndSet(nodeName)
					if node:
						status, attr = mnsUtils.validateAttrAndGet(node, attrName, None, returnAttrObject = True)
						if status and attr:
							#all tests passed, axecute
							fullAttrName = node.nodeName() + "_" + attr.attrName()
							status, newAttr = mnsUtils.validateAttrAndGet(host, fullAttrName, None, returnAttrObject = True)
							if not newAttr:
								newAttr = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = fullAttrName, locked = False, keyable = True, cb = True)
								if newAttr: newAttr = newAttr[0]

							if newAttr:
								returnAttrs.append(newAttr)
								try:
									attr >> newAttr
								except:
									pass

		return returnAttrs

	def storeData(self):
		exportData = self.gatherData()
		self.writeDefaultData(exportData)
		#mes
		pm.confirmDialog( title='Data Saved', message='Game-Exporter data was successfully saved in this scene.', defaultButton='OK')

	def delData(self):
		self.writeDefaultData({})
		#mes
		reply = QtWidgets.QMessageBox.question(None, 'Are you sure?', "Are you sure you want to delete Game-Exporter Data from this scene?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.Yes:
			#resetUI
			loadAnimationExporter()

	def resetRootJnt(self, extractedRootJnt):
		#delete all keys from root joint
		for chan in "trs":
			extractedRootJnt.node.attr(chan).disconnect()
			extractedRootJnt.node.attr(chan).setLocked(False)
			for axis in "xyz":
				extractedRootJnt.node.attr(chan + axis).disconnect()
			extractedRootJnt.node.attr(chan + axis).setLocked(False)
		#reset transforms
		for chan in "trs":
			extractedRootJnt.node.attr(chan).setLocked(False)
			for axis in "xyz":
				extractedRootJnt.node.attr(chan + axis).setLocked(False)
				extractedRootJnt.node.attr(chan + axis).set(0.0)
				if chan == "s":
					extractedRootJnt.node.attr(chan + axis).set(1.0)
			
	def export(self):
		self.process_pb.setValue(4)

		messageLog = []
		statusArray = []
		status = 0
		userStartTime = pm.currentTime()

		exportData = self.gatherData()
		self.writeDefaultData(exportData)
		self.process_pb.setValue(10)

		if exportData:
			for rigTopName in exportData.keys():
				messageLog.append(rigTopName + ":")
				rigTop = blkUtils.getRigTop(rigTopName)
				if rigTop:
					exportRanges = exportData[rigTopName]
					additiveProgValue = int(90 / len(exportData.keys()) / len(exportRanges))

					#################################
					############# PREP ##############
					#################################
					
					#if include meshes is on, or there is an asset export, create the meshe twins
					includeMeshes = self.includeMeshes_cbx.isChecked()
					if not includeMeshes:
						for r in exportRanges:
							if r["isAsset"]:
								includeMeshes = True
								break


					extractedRootJnt, origRootJnt, meshTwins, skinnedMeshes, skinData, unusedInfluences, twinDict, messageLog = self.extractSkeletonFromRigTop(rigTop, 
																																					self.skeletonExtractMode_cb.currentIndex(),
																																					self.rotToJO_cbx.isChecked(),
																																					includeMeshes,
																																					messageLog
																																					)
					

					restructureRequired = False
					if extractedRootJnt and unusedInfluences and self.deleteUnusedJnts_cbx.isChecked():
						restructureRequired = True

					#################################
					############ ASSETS #############
					#################################

					#start with asset export
					restructured = False
					if restructureRequired:
						 restructured = self.restructureJointHeirarchy(extractedRootJnt.node, unusedInfluences)

					bspsNodes = []

					## handle blend-shapes
					for r in exportRanges:
						if r["isAsset"]:
							newSelection = [extractedRootJnt.node]
							if meshTwins: newSelection += meshTwins
							self.bakeExtraAttributes(r, extractedRootJnt.node)
							
							#reset root joint
							if self.resetRootJnt_cbx.isChecked() and extractedRootJnt:
								self.resetRootJnt(extractedRootJnt)

							#Handle Blend-Shapes
							if meshTwins:
								for origMesh in twinDict.keys():
									newBS = mnsMeshUtils.duplicateBlendShapeNodes(origMesh, twinDict[origMesh], connect = True)	
									if newBS:
										newBS.rename(newBS.nodeName().split(":")[-1])
										bspsNodes.append(newBS)

							pm.select(newSelection)
							try:
								pm.mel.FBXExport(f=r["path"], s = True)
								messageLog.append("      " + r["path"] + ": Sucess")
							except:
								messageLog.append("      " + r["path"] + ": Failure")

							self.process_pb.setValue(self.process_pb.value() + additiveProgValue)
					
					#################################
					############# ANIM ##############
					#################################

					#for each range
					for r in exportRanges:
						if not r["isAsset"]:
							# if the structure changed due to Assets/previous runs, recreate
							if restructured:
								if meshTwins: pm.delete(meshTwins)
								pm.delete(extractedRootJnt.node)
								extractedRootJnt, origRootJnt, meshTwins, skinnedMeshes, skinData, unusedInfluences, twinDict, messageLog = self.extractSkeletonFromRigTop(rigTop, 
																																					self.skeletonExtractMode_cb.currentIndex(),
																																					self.rotToJO_cbx.isChecked(),
																																					includeMeshes,
																																					messageLog
																																					)


							
							#connect joints to drivers
							allJoints = [extractedRootJnt.node] + extractedRootJnt.node.listRelatives(ad = True, type = "joint")
							allOrigJointsDict = {}
							for j in [origRootJnt] + origRootJnt.listRelatives(ad = True, type = "joint"):
								allOrigJointsDict.update({j.nodeName().split(":")[-1]: j})
								
							cnsToDel = []
							for j in allJoints:
								mnsUtils.lockAndHideAllTransforms(j, lock = False, keyable = True, cb = True)
								pureName = j.nodeName().split(":")[-1]
								if pureName in allOrigJointsDict.keys():
									mnsUtils.lockAndHideAllTransforms(allOrigJointsDict[pureName], lock = False, keyable = True, cb = True)

									if self.bakeConMethod_cb.currentIndex() == 0: #constraints
										cnsToDel.append(pm.parentConstraint(allOrigJointsDict[pureName], j, mo = True))
										cnsToDel.append(pm.scaleConstraint(allOrigJointsDict[pureName], j, mo = True))
										j.jointOrient.set(allOrigJointsDict[pureName].jointOrient.get())
									else: #direct
										for chan in ["t", "r", "s", "jointOrient"]:
											allOrigJointsDict[pureName].attr(chan) >> j.attr(chan)
							
							#extra attributes
							self.bakeExtraAttributes(r, extractedRootJnt.node)

							if meshTwins and not bspsNodes:
								for origMesh in twinDict.keys():
									newBS = mnsMeshUtils.duplicateBlendShapeNodes(origMesh, twinDict[origMesh], connect = True)	
									if newBS:
										newBS.rename(newBS.nodeName().split(":")[-1])
										bspsNodes.append(newBS)

							#bake
							pm.bakeResults(allJoints + bspsNodes, t= (r["min"], r["max"]), sb = 1, simulation = True)

							#disconnect joints
							if cnsToDel: pm.delete(cnsToDel)
							for j in allJoints:
								for chan in ["t", "r", "s", "jointOrient"]:
									j.attr(chan).disconnect()

							jntsToKey = allJoints
							if restructureRequired:
								#save Animation Data (WS)
								animWSData = self.saveWSAnimData(allJoints, r["min"], r["max"])
								
								#delete keys
								pm.cutKey(allJoints, s=True)

								#restructureJoints
								restructured = self.restructureJointHeirarchy(extractedRootJnt.node, unusedInfluences)
								if restructured:
									jntsToKey = [extractedRootJnt.node] + extractedRootJnt.node.listRelatives(ad = True, type = "joint")
								
								#load anim data (WS)
								self.loadWSAnimData(animWSData)

							#move keys to start
							if self.normRanges_cbx.isChecked():
								if r["min"] != 0:
									tc = r["min"]
									if r["min"] > 0: tc = r["min"] * -1
									pm.keyframe(jntsToKey + bspsNodes, 
												e = True, 
												iub = False, 
												an = "objects", 
												t = str(r["min"] - 1) + ".9999:" + str(r["max"]) + ".9999", 
												r = True, 
												o = "over", 
												tc = tc)
									
							#export
							newSelection = [extractedRootJnt.node]
							if meshTwins and self.includeMeshes_cbx.isChecked(): newSelection += meshTwins
							
							#reset root joint
							if self.resetRootJnt_cbx.isChecked() and extractedRootJnt:
								self.resetRootJnt(extractedRootJnt)

							pm.select(newSelection)
							try:
								pm.mel.FBXExport(f=r["path"], s = True)
								messageLog.append("      " + r["path"] + ": Sucess")
							except:
								messageLog.append("      " + r["path"] + ": Failure")

							#delete all keys
							pm.cutKey(jntsToKey, s=True)
							
							self.process_pb.setValue(self.process_pb.value() + additiveProgValue)
					
					#delete everything
					if meshTwins: pm.delete(meshTwins)
					pm.delete(extractedRootJnt.node)

					#reset time slider
					pm.currentTime(userStartTime, edit=True)
					statusArray.append(True)
				else:
					statusArray.append(False)
					messageLog.append("      Couldn't find Rig-Top.")
		else:
			messageLog.append("Couldn't find valid ranges and paths to export.")
		
		if statusArray:
			if all(v is True for v in statusArray):
				status = 2
			elif all(v is False for v in statusArray):
				pass
			else:
				status = 1

		#messge
		msg = QtWidgets.QMessageBox()
		if status == 0:
			msg.setIcon(QtWidgets.QMessageBox.Critical)
			msg.setText("Export Process Failed" + (" " * 250))
			msg.setWindowTitle("Faliure")
		elif status == 1:
			msg.setIcon(QtWidgets.QMessageBox.Warning)
			msg.setText("Export Process Partially Failed" + (" " * 250))
			msg.setWindowTitle("Warning")
		elif status == 2:
			msg.setIcon(QtWidgets.QMessageBox.Information)
			msg.setText("Export Process Successfully Completed" + (" " * 250))
			msg.setWindowTitle("Sucess!")
		
		infoMes = ""
		for line in messageLog:
			infoMes += line + "\n"

		self.process_pb.setValue(100)
		msg.setInformativeText(infoMes)
		msg.exec_()
		self.process_pb.setValue(0)

	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsAnimationExporter", svr = 0)
		self.show()

def loadAnimationExporter(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("Animation Exporter Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsAnimationExporter")

	if mnsUtils.mnsLicStatusCheck():
		MnsAnimExporterWin = MnsAnimationExporter()
		MnsAnimExporterWin.loadWindow()
		if previousPosition: MnsAnimExporterWin.move(previousPosition)
		return MnsAnimExporterWin