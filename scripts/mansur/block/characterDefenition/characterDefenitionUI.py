"""=== Author: Assaf Ben Zur ===
This tool was created to assist users in creating humanIK character definitions.
Also, in conjunction with Block, create an animation puppet for predifined skeleton templates.

Use pre-existing prests, as well as create your own presets, to characterize any skeleton in seconds.
Many workflows and scenrios are covered within this tool, please refer to Mansur-Rig's You-Tube channel for a full video guide demonstratig all of them.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
import json
import maya.mel as mel

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import string as mnsString
from ...core import nodes as mnsNodes
from ...core.globals import *
from ..core import blockUtility as blkUtils
from ...gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore, QtWidgets
	from PySide6.QtWidgets import QTreeWidgetItem
else:
	from PySide2 import QtGui, QtCore, QtWidgets
	from PySide2.QtWidgets import QTreeWidgetItem

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "characterDefenitionUI.ui")

class MnsCharacterDefenitionUI(form_class, base_class):
	"""Main UI Class
	"""

	### INIT ###
	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		#initialize UI
		super(MnsCharacterDefenitionUI, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsCharacterDefenitionUI") 
		iconDir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/icons/mansur_01.png"
		winIconDir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/icons/mansur_logo_noText.png"
		self.iconLbl.setPixmap(QtGui.QPixmap(iconDir))
		self.setWindowIcon(QtGui.QIcon(winIconDir))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		#locals
		self.presetsDir = os.path.dirname(__file__).replace("\\", "/") + "/defenitionPresets"
		self.charDefPresets = {}
		self.charDefData = {}
		self.blockNameSpace = ""
		self.targetNameSpace = ""
		self.nameSpaceLEPairing = {self.loadSelectedBlockNS_btn: self.blockNameSpace_le, self.loadSelectedTargetNS_btn: self.targetNameSpace_le}
		#methods
		self.connectSignals()
		self.initView()
		self.initializeUI()

	def initView(self):
		"""Initialize UI default display state.
		"""

		self.importFromFile_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.charDef_trv.setColumnWidth(0, 160)
		self.charDef_trv.setColumnWidth(1, 160)
		self.charDef_trv.setColumnWidth(2, 160)
		self.charDef_trv.setColumnWidth(3, 160)
		self.resetView_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/menuIconReset.png"))
		self.disconnectTargetSkel_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/kinDisconnect.png"))
		self.connectTargetSkel_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/kinConnect.png"))
		self.matchGuidesToTarget_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nClothMatchingMesh.png"))
		self.filterIcon_lbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/search.png"))
		self.humanIKUI_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/HIKcreateControlRig.png"))
		self.humanIKCharacterize_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/HIKCharacterToolStancePose.png"))

	def initPresets(self):
		"""Initialize existing Mansur-Rig presets that are delivered with the product and update the UI list.
		"""

		self.charDefPresets = {}

		if self.presetsDir and os.path.isdir(self.presetsDir):
			presets = []
			defaultIndex = 0
			k = 0
			for presetFile in os.listdir(self.presetsDir):
				if presetFile.endswith(".json"):
					presetName = presetFile.split(".")[0]
					presets.append(presetName)
					self.charDefPresets.update({presetName: self.presetsDir + "/" + presetFile})
					if "mansur" in presetName.lower():
						defaultIndex = k
					k += 1

			if presets:
				self.charDefPresets_cb.addItems(presets)
				if defaultIndex != 0:
					self.charDefPresets_cb.setCurrentIndex(defaultIndex)
					
	def initializeUI(self):
		"""Initialize UI Data.
		"""

		self.initPresets()

	def connectSignals(self):
		"""Connect all UI signals
		"""

		self.charDef_trv.itemDoubleClicked.connect(self.valueEdit)
		self.importPreset_btn.released.connect(self.importPreset)
		self.resetView_btn.released.connect(self.resetUI)
		self.matchGuidesToTarget_btn.released.connect(lambda: blkUtils.matchGuidesToTargetSkeleton(self.gatherCharDefData(), self.blockNameSpace, self.targetNameSpace))
		self.connectTargetSkel_btn.released.connect(lambda: blkUtils.connectTargetSkeleton(self.gatherCharDefData(), self.blockNameSpace, self.targetNameSpace))
		self.disconnectTargetSkel_btn.released.connect(lambda: blkUtils.disconnectTargetSkeleton(self.gatherCharDefData(), self.blockNameSpace, self.targetNameSpace))
		self.charDef_trv.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.charDef_trv.customContextMenuRequested.connect(self.editMenu)
		self.charDef_trv.itemChanged.connect(self.gatherCharDefData)
		self.searchClear_btn.released.connect(self.search_le.clear)
		self.search_le.textChanged.connect(self.filterView)
		self.loadSelectedBlockNS_btn.released.connect(self.loadNameSpace)
		self.loadSelectedTargetNS_btn.released.connect(self.loadNameSpace)
		self.blockNameSpace_le.textChanged.connect(self.updateNameSpaceVars)
		self.targetNameSpace_le.textChanged.connect(self.updateNameSpaceVars)
		self.importFromFile_btn.released.connect(self.importFromFile)
		self.exportPreset_btn.released.connect(self.exportPreset)
		self.humanIKUI_btn.released.connect(lambda: mel.eval("HIKCharacterControlsTool"))
		self.humanIKCharacterize_btn.released.connect(lambda: blkUtils.characterizeHumanIK(self.gatherCharDefData(), mode = self.characterizeMode_cb.currentIndex(), charName = self.charName_le.text(), namespace = self.getNamespaceBasedOnMode(self.characterizeMode_cb.currentIndex())))
		self.characterizeMode_cb.currentIndexChanged.connect(self.setNameBoxStateBasedOnMode)
		self.charDef_trv.itemSelectionChanged.connect(self.updateSceneSelectionBasedOnUIState)

	### Triggers ###
	def setNameBoxStateBasedOnMode(self):
		"""set the character name line-edit state base on the current UI state.
		"""

		currnetIndex = self.characterizeMode_cb.currentIndex()
		if currnetIndex == 0:
			self.charName_le.setEnabled(False)
		else:
			self.charName_le.setEnabled(True)

	def getNamespaceBasedOnMode(self, mode = 0):
		"""Get relevant namespace inpit based on mode.
		mode 0 = Block name-space
		mode 1 = Target name-space.
		"""

		if mode == 0:
			return self.blockNameSpace
		else:
			return self.targetNameSpace

	def updateSceneSelectionBasedOnUIState(self):
		"""Update the current Maya scene selection based on the selected items in the UI.
		In case the "update selection" checkbox isn't checked, this will not execute and selection will not be updated.
		"""

		if self.updateSelection_cbx.isChecked():
			selectedItems = self.charDef_trv.selectedItems()
			newSelection = []
			for selItem in selectedItems:
				for colIdx in range(1, 3):
					sceneObj = mnsUtils.checkIfObjExistsAndSet(selItem.text(colIdx))
					if not sceneObj:
						if colIdx == 1 and self.blockNameSpace:
							sceneObj = mnsUtils.checkIfObjExistsAndSet(self.blockNameSpace + ":" + selItem.text(colIdx))
						elif colIdx == 2 and self.targetNameSpace:
							sceneObj = mnsUtils.checkIfObjExistsAndSet(self.targetNameSpace + ":" + selItem.text(colIdx))
					if sceneObj:
						newSelection.append(sceneObj)
			if newSelection:
				pm.select(newSelection, r = True)
			
	def valueEdit(self, item, column):
		"""TreeWidget Edit trigger
		"""

		tmp = item.flags()

		if column != 3:
			item.setFlags(tmp | QtCore.Qt.ItemIsEditable)
		elif tmp & QtCore.Qt.ItemIsEditable:
			item.setFlags(tmp ^ QtCore.Qt.ItemIsEditable)

	def resetUI(self):
		"""Reset the UI to default state.
		"""

		self.charDef_trv.clear()
		self.charDefData = {}
		self.blockNameSpace_le.clear()
		self.targetNameSpace_le.clear()
		self.search_le.clear()

	def updateNameSpaceVars(self):
		"""Update the class member variables for both namespaces.
		"""

		self.blockNameSpace = self.blockNameSpace_le.text()
		self.targetNameSpace = self.targetNameSpace_le.text()

	def loadNameSpace(self):
		"""Load selected namespace trigger.
		"""

		senderBtn = self.sender()
		sel = pm.ls(sl=True)
		if sel:
			sel = sel[0]
			if ":" in sel.nodeName():
				loadText = sel.nodeName().split(":")[0]
				self.nameSpaceLEPairing[senderBtn].setText(loadText)

	def filterView(self):
		"""Search trigger. Filter the main treeWidget list based on the input filter text.
		"""

		filterText = self.search_le.text()
		if filterText:
			for rowIdx in range(self.charDef_trv.topLevelItemCount()):
				componentRow = self.charDef_trv.invisibleRootItem().child(rowIdx)
				componentRow.setHidden(True)

				hidden = True
				for colIdx in range(3):
					currentText = componentRow.text(colIdx)
					if filterText.lower() in currentText.lower():
						componentRow.setHidden(False)
						break
		else:
			for rowIdx in range(self.charDef_trv.topLevelItemCount()):
				componentRow = self.charDef_trv.invisibleRootItem().child(rowIdx)
				componentRow.setHidden(False)

	def clearRow(self):
		"""Delete Row trigger.
		"""

		componentRow = self.charDef_trv.currentItem()
		componentRow.setText(1, "")
		componentRow.setText(2, "")
		componentRow.setText(3, "")

	def clearCell(self, position):
		"""Clear cell trigger.
		"""

		colIndex = self.charDef_trv.indexAt(position).column()
		componentRow = self.charDef_trv.currentItem()
		componentRow.setText(colIndex, "")

	def loadSelectedToCell(self, position):
		"""Load scene selection to cell trigger.
		"""

		sel = pm.ls(sl=True)
		if sel:
			colIndex = self.charDef_trv.indexAt(position).column()
			componentRow = self.charDef_trv.currentItem()
			if colIndex != 3:
				componentRow.setText(colIndex, sel[0].nodeName().split(":")[-1])

	def addRowToTable(self):
		"""Add a new empty row trigger.
		"""

		componentItem = QTreeWidgetItem(self.charDef_trv, ["componentName"])
		componentItem.setFlags(componentItem.flags() | QtCore.Qt.ItemIsEditable)
		componentItem.setSizeHint(0, QtCore.QSize(300, 22))
		self.charDef_trv.scrollTo(self.charDef_trv.indexFromItem(componentItem))
		self.charDef_trv.clearSelection()
		componentItem.setSelected(True)

	def removeRowFromTable(self):
		"""Remove Row trigger.
		"""

		selected = self.charDef_trv.currentItem() 
		if selected:
			self.charDef_trv.takeTopLevelItem(self.charDef_trv.indexOfTopLevelItem(selected))

	def loadHikSlotToSelectedCells(self, text, position):
		"""Load selected HIK slot into selected cell trigger.
		"""

		colIndex = self.charDef_trv.indexAt(position).column()
		componentRow = self.charDef_trv.currentItem()
		if colIndex == 3:
			componentRow.setText(colIndex, text)
	
	### Import/Export ###
	def importFromFile(self):
		"""Import preset from file trigger.
		"""

		file = QtWidgets.QFileDialog.getOpenFileName(self, "Select Preset File", filter = "Json Files (*.json)")
		if file:
			if file[0].endswith(".json"):
				self.importPreset(fromPath = file[0])

	def exportPreset(self):
		"""Export preset to file trigger.
		"""

		if self.targetSkel_cb.currentText() != "HIK Slot":
			self.gatherCharDefData()
			if self.charDefData:
				filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export Preset", filter = "Json Files (*.json)")
				if filename: 
					filePath = filename[0]
					if filePath.endswith(".json"):
						
							targetComponent = self.targetSkel_cb.currentText()
							targetKey = "blockSkelItem"
							if targetComponent == "Target Skeleton": targetKey = "targetSkelItem"
							
							exportData = {}
							for componentKey in self.charDefData:
								exportData.update({componentKey: {"joint": self.charDefData[componentKey][targetKey], "hikSlot": self.charDefData[componentKey]["hikSlot"]}})
							mnsUtils.writeJsonPath(filePath, exportData)
							pm.confirmDialog( title='Preset Exported.', message="Preset Exported successfully.", defaultButton='OK')
			else:
				pm.confirmDialog( title='Empty Column', message="No data found, nothing to export.", defaultButton='OK')
		else:
			mnsLog.log("Please select Block or Target columns to export.", svr = 2)

	def importPreset(self, **kwargs):
		"""Import preset trigger.
		"""

		fromPath = kwargs.get("fromPath", None)

		presetPath = None
		if not fromPath:
			presetPath = self.charDefPresets[self.charDefPresets_cb.currentText()]
		else:
			presetPath = fromPath

		if os.path.isfile(presetPath) and presetPath.endswith(".json"):
			presetDict = mnsUtils.readJson(presetPath)
			
			if presetDict:
				self.gatherCharDefData()

				#filter data
				targetComponent = self.targetSkel_cb.currentText()

				for componentKey in presetDict.keys():
					component = componentKey
					blockSkelItem = ""
					targetSkelItem = ""
					hikSlot = ""

					if componentKey in self.charDefData.keys():
						blockSkelItem = self.charDefData[componentKey]["blockSkelItem"]
						targetSkelItem = self.charDefData[componentKey]["targetSkelItem"]
						hikSlot = self.charDefData[componentKey]["hikSlot"]

					if targetComponent == "Block Skeleton":
						blockSkelItem = presetDict[component]["joint"]
					elif targetComponent == "Target Skeleton":
						targetSkelItem = presetDict[component]["joint"]
					elif targetComponent == "HIK Slot":
						hikSlot = presetDict[component]["hikSlot"]

					self.charDefData.update({component: {"blockSkelItem": blockSkelItem, "targetSkelItem": targetSkelItem, "hikSlot": hikSlot}})

				self.drawData()

	### Right click menu ###
	def linkHikMenuAction(self, menuItem, position):
		"""Procedural menu items action linking to action.
		"""

		for action in menuItem.actions():
			if action.isSeparator():
				pass
			elif action.menu():
				self.linkHikMenuAction(action.menu(), position)
			else:
				action.triggered.connect(partial(self.loadHikSlotToSelectedCells, action.text(), position))

	def createHIKSlotsMenu(self, rootMenuItem, position):
		"""Create the predifined HIK context menu structure.
		"""

		if rootMenuItem:
			menu = rootMenuItem
			Reference = menu.addAction(self.tr("Reference"))
			Hips = menu.addAction(self.tr("Hips"))
			HipsTranslation = menu.addAction(self.tr("HipsTranslation"))
			SpineMenu = menu.addMenu(self.tr("Spine"))
			Spine = SpineMenu.addAction(self.tr("Spine"))
			Spine1 = SpineMenu.addAction(self.tr("Spine1"))
			Spine2 = SpineMenu.addAction(self.tr("Spine2"))
			Spine3 = SpineMenu.addAction(self.tr("Spine3"))
			Spine4 = SpineMenu.addAction(self.tr("Spine4"))
			Spine5 = SpineMenu.addAction(self.tr("Spine5"))
			Spine6 = SpineMenu.addAction(self.tr("Spine6"))
			Spine7 = SpineMenu.addAction(self.tr("Spine7"))
			Spine8 = SpineMenu.addAction(self.tr("Spine8"))
			Spine9 = SpineMenu.addAction(self.tr("Spine9"))
			legsMenu = menu.addMenu(self.tr("Legs"))
			LeftLegMenu = legsMenu.addMenu(self.tr("LeftLeg")) 
			LeftUpLeg = LeftLegMenu.addAction(self.tr("LeftUpLeg"))
			LeftUpLegRollMenu = LeftLegMenu.addMenu(self.tr("LeftUpperLegRoll")) 
			LeafLeftUpLegRoll1 = LeftUpLegRollMenu.addAction(self.tr("LeafLeftUpLegRoll1"))
			LeafLeftUpLegRoll2 = LeftUpLegRollMenu.addAction(self.tr("LeafLeftUpLegRoll2"))
			LeafLeftUpLegRoll3 = LeftUpLegRollMenu.addAction(self.tr("LeafLeftUpLegRoll3"))
			LeafLeftUpLegRoll4 = LeftUpLegRollMenu.addAction(self.tr("LeafLeftUpLegRoll4"))
			LeafLeftUpLegRoll5 = LeftUpLegRollMenu.addAction(self.tr("LeafLeftUpLegRoll5"))
			LeftLeg = LeftLegMenu.addAction(self.tr("LeftLeg"))
			LeftLegRollMenu = LeftLegMenu.addMenu(self.tr("LeftLegRoll")) 
			LeafLeftLegRoll1 = LeftLegRollMenu.addAction(self.tr("LeafLeftLegRoll1"))
			LeafLeftLegRoll2 = LeftLegRollMenu.addAction(self.tr("LeafLeftLegRoll2"))
			LeafLeftLegRoll3 = LeftLegRollMenu.addAction(self.tr("LeafLeftLegRoll3"))
			LeafLeftLegRoll4 = LeftLegRollMenu.addAction(self.tr("LeafLeftLegRoll4"))
			LeafLeftLegRoll5 = LeftLegRollMenu.addAction(self.tr("LeafLeftLegRoll5"))
			LeftFoot = LeftLegMenu.addAction(self.tr("LeftFoot")) 
			LeftToeBase = LeftLegMenu.addAction(self.tr("LeftToeBase")) 
			LeftToesMenu = LeftLegMenu.addMenu(self.tr("LeftToes"))
			LeftBigToeMenu = LeftToesMenu.addMenu(self.tr("Big-Toe"))
			LeftInFootBigToe = LeftBigToeMenu.addAction(self.tr("LeftInFootBigToe")) 
			LeftFootBigToe1 = LeftBigToeMenu.addAction(self.tr("LeftFootBigToe1")) 
			LeftFootBigToe2 = LeftBigToeMenu.addAction(self.tr("LeftFootBigToe2")) 
			LeftFootBigToe3 = LeftBigToeMenu.addAction(self.tr("LeftFootBigToe3")) 
			LeftFootBigToe4 = LeftBigToeMenu.addAction(self.tr("LeftFootBigToe4")) 
			LeftIndexToeMenu = LeftToesMenu.addMenu(self.tr("Index"))
			LeftInFootIndex = LeftIndexToeMenu.addAction(self.tr("LeftInFootIndex")) 
			LeftFootIndex1 = LeftIndexToeMenu.addAction(self.tr("LeftFootIndex1")) 
			LeftFootIndex2 = LeftIndexToeMenu.addAction(self.tr("LeftFootIndex2")) 
			LeftFootIndex3 = LeftIndexToeMenu.addAction(self.tr("LeftFootIndex3")) 
			LeftFootIndex4 = LeftIndexToeMenu.addAction(self.tr("LeftFootIndex4")) 
			LeftMiddleToeMenu = LeftToesMenu.addMenu(self.tr("Middle"))
			LeftInFootMiddle = LeftMiddleToeMenu.addAction(self.tr("LeftInFootMiddle")) 
			LeftFootMiddle1 = LeftMiddleToeMenu.addAction(self.tr("LeftFootMiddle1")) 
			LeftFootMiddle2 = LeftMiddleToeMenu.addAction(self.tr("LeftFootMiddle2")) 
			LeftFootMiddle3 = LeftMiddleToeMenu.addAction(self.tr("LeftFootMiddle3")) 
			LeftFootMiddle4 = LeftMiddleToeMenu.addAction(self.tr("LeftFootMiddle4")) 
			LeftRingToeMenu = LeftToesMenu.addMenu(self.tr("Ring"))
			LeftInFootRing = LeftRingToeMenu.addAction(self.tr("LeftInFootRing")) 
			LeftFootRing1 = LeftRingToeMenu.addAction(self.tr("LeftFootRing1")) 
			LeftFootRing2 = LeftRingToeMenu.addAction(self.tr("LeftFootRing2")) 
			LeftFootRing3 = LeftRingToeMenu.addAction(self.tr("LeftFootRing3")) 
			LeftFootRing4 = LeftRingToeMenu.addAction(self.tr("LeftFootRing4")) 
			LeftPinkyToeMenu = LeftToesMenu.addMenu(self.tr("Pinky"))
			LeftInFootPinky = LeftPinkyToeMenu.addAction(self.tr("LeftInFootPinky")) 
			LeftFootPinky1 = LeftPinkyToeMenu.addAction(self.tr("LeftFootPinky1")) 
			LeftFootPinky2 = LeftPinkyToeMenu.addAction(self.tr("LeftFootPinky2")) 
			LeftFootPinky3 = LeftPinkyToeMenu.addAction(self.tr("LeftFootPinky3")) 
			LeftFootPinky4 = LeftPinkyToeMenu.addAction(self.tr("LeftFootPinky4")) 
			RightLegMenu = legsMenu.addMenu(self.tr("RightLeg")) 
			RightUpLeg = RightLegMenu.addAction(self.tr("RightUpLeg"))
			RightUpLegRollMenu = RightLegMenu.addMenu(self.tr("RightUpperLegRoll")) 
			LeafRightUpLegRoll1 = RightUpLegRollMenu.addAction(self.tr("LeafRightUpLegRoll1"))
			LeafRightUpLegRoll2 = RightUpLegRollMenu.addAction(self.tr("LeafRightUpLegRoll2"))
			LeafRightUpLegRoll3 = RightUpLegRollMenu.addAction(self.tr("LeafRightUpLegRoll3"))
			LeafRightUpLegRoll4 = RightUpLegRollMenu.addAction(self.tr("LeafRightUpLegRoll4"))
			LeafRightUpLegRoll5 = RightUpLegRollMenu.addAction(self.tr("LeafRightUpLegRoll5"))
			RightLeg = RightLegMenu.addAction(self.tr("RightLeg"))
			RightLegRollMenu = RightLegMenu.addMenu(self.tr("RightLegRoll")) 
			LeafRightLegRoll1 = RightLegRollMenu.addAction(self.tr("LeafRightLegRoll1"))
			LeafRightLegRoll2 = RightLegRollMenu.addAction(self.tr("LeafRightLegRoll2"))
			LeafRightLegRoll3 = RightLegRollMenu.addAction(self.tr("LeafRightLegRoll3"))
			LeafRightLegRoll4 = RightLegRollMenu.addAction(self.tr("LeafRightLegRoll4"))
			LeafRightLegRoll5 = RightLegRollMenu.addAction(self.tr("LeafRightLegRoll5"))
			RightFoot = RightLegMenu.addAction(self.tr("RightFoot")) 
			RightToeBase = RightLegMenu.addAction(self.tr("RightToeBase")) 
			RightToesMenu = RightLegMenu.addMenu(self.tr("RightToes"))
			RightBigToeMenu = RightToesMenu.addMenu(self.tr("Big-Toe"))
			RightInFootBigToe = RightBigToeMenu.addAction(self.tr("RightInFootBigToe")) 
			RightFootBigToe1 = RightBigToeMenu.addAction(self.tr("RightFootBigToe1")) 
			RightFootBigToe2 = RightBigToeMenu.addAction(self.tr("RightFootBigToe2")) 
			RightFootBigToe3 = RightBigToeMenu.addAction(self.tr("RightFootBigToe3")) 
			RightFootBigToe4 = RightBigToeMenu.addAction(self.tr("RightFootBigToe4")) 
			RightIndexToeMenu = RightToesMenu.addMenu(self.tr("Index"))
			RightInFootIndex = RightIndexToeMenu.addAction(self.tr("RightInFootIndex")) 
			RightFootIndex1 = RightIndexToeMenu.addAction(self.tr("RightFootIndex1")) 
			RightFootIndex2 = RightIndexToeMenu.addAction(self.tr("RightFootIndex2")) 
			RightFootIndex3 = RightIndexToeMenu.addAction(self.tr("RightFootIndex3")) 
			RightFootIndex4 = RightIndexToeMenu.addAction(self.tr("RightFootIndex4")) 
			RightMiddleToeMenu = RightToesMenu.addMenu(self.tr("Middle"))
			RightInFootMiddle = RightMiddleToeMenu.addAction(self.tr("RightInFootMiddle")) 
			RightFootMiddle1 = RightMiddleToeMenu.addAction(self.tr("RightFootMiddle1")) 
			RightFootMiddle2 = RightMiddleToeMenu.addAction(self.tr("RightFootMiddle2")) 
			RightFootMiddle3 = RightMiddleToeMenu.addAction(self.tr("RightFootMiddle3")) 
			RightFootMiddle4 = RightMiddleToeMenu.addAction(self.tr("RightFootMiddle4")) 
			RightRingToeMenu = RightToesMenu.addMenu(self.tr("Ring"))
			RightInFootRing = RightRingToeMenu.addAction(self.tr("RightInFootRing")) 
			RightFootRing1 = RightRingToeMenu.addAction(self.tr("RightFootRing1")) 
			RightFootRing2 = RightRingToeMenu.addAction(self.tr("RightFootRing2")) 
			RightFootRing3 = RightRingToeMenu.addAction(self.tr("RightFootRing3")) 
			RightFootRing4 = RightRingToeMenu.addAction(self.tr("RightFootRing4")) 
			RightPinkyToeMenu = RightToesMenu.addMenu(self.tr("Pinky"))
			RightInFootPinky = RightPinkyToeMenu.addAction(self.tr("RightInFootPinky")) 
			RightFootPinky1 = RightPinkyToeMenu.addAction(self.tr("RightFootPinky1")) 
			RightFootPinky2 = RightPinkyToeMenu.addAction(self.tr("RightFootPinky2")) 
			RightFootPinky3 = RightPinkyToeMenu.addAction(self.tr("RightFootPinky3")) 
			RightFootPinky4 = RightPinkyToeMenu.addAction(self.tr("RightFootPinky4")) 
			shouldersArmsMenu = menu.addMenu(self.tr("Shoudlers/arms"))
			leftShoulderMenu = shouldersArmsMenu.addMenu(self.tr("LeftShoulder")) 
			LeftShoulder = leftShoulderMenu.addAction(self.tr("LeftShoulder"))
			LeftShoulderExtra = leftShoulderMenu.addAction(self.tr("LeftShoulderExtra"))
			leftArmMenu = shouldersArmsMenu.addMenu(self.tr("LeftArm")) 
			LeftArm = leftArmMenu.addAction(self.tr("LeftArm"))
			LeftArmRollMenu = leftArmMenu.addMenu(self.tr("LeftArmRoll")) 
			LeafLeftArmRoll1 = LeftArmRollMenu.addAction(self.tr("LeafLeftArmRoll1"))
			LeafLeftArmRoll2 = LeftArmRollMenu.addAction(self.tr("LeafLeftArmRoll2"))
			LeafLeftArmRoll3 = LeftArmRollMenu.addAction(self.tr("LeafLeftArmRoll3"))
			LeafLeftArmRoll4 = LeftArmRollMenu.addAction(self.tr("LeafLeftArmRoll4"))
			LeafLeftArmRoll5 = LeftArmRollMenu.addAction(self.tr("LeafLeftArmRoll5"))
			LeftForeArm = leftArmMenu.addAction(self.tr("LeftForeArm"))
			LeftForeArmRollMenu = leftArmMenu.addMenu(self.tr("LeftForeArmRoll")) 
			LeafLeftForeArmRoll1 = LeftForeArmRollMenu.addAction(self.tr("LeafLeftForeArmRoll1"))
			LeafLeftForeArmRoll2 = LeftForeArmRollMenu.addAction(self.tr("LeafLeftForeArmRoll2"))
			LeafLeftForeArmRoll3 = LeftForeArmRollMenu.addAction(self.tr("LeafLeftForeArmRoll3"))
			LeafLeftForeArmRoll4 = LeftForeArmRollMenu.addAction(self.tr("LeafLeftForeArmRoll4"))
			LeafLeftForeArmRoll5 = LeftForeArmRollMenu.addAction(self.tr("LeafLeftForeArmRoll5"))
			LeftHand = leftArmMenu.addAction(self.tr("LeftHand"))
			LeftFingerBase = leftArmMenu.addAction(self.tr("LeftFingerBase"))
			leftFingersMenu = leftArmMenu.addMenu(self.tr("LeftFingers")) 
			leftThumbFingerMenu = leftFingersMenu.addMenu(self.tr("Thumb")) 
			LeftInHandThumb = leftThumbFingerMenu.addAction(self.tr("LeftInHandThumb"))
			LeftHandThumb1 = leftThumbFingerMenu.addAction(self.tr("LeftHandThumb1"))
			LeftHandThumb2 = leftThumbFingerMenu.addAction(self.tr("LeftHandThumb2"))
			LeftHandThumb3 = leftThumbFingerMenu.addAction(self.tr("LeftHandThumb3"))
			LeftHandThumb4 = leftThumbFingerMenu.addAction(self.tr("LeftHandThumb4"))
			leftIndexFingerMenu = leftFingersMenu.addMenu(self.tr("Index")) 
			LeftInHandIndex = leftIndexFingerMenu.addAction(self.tr("LeftInHandIndex"))
			LeftHandIndex1 = leftIndexFingerMenu.addAction(self.tr("LeftHandIndex1"))
			LeftHandIndex2 = leftIndexFingerMenu.addAction(self.tr("LeftHandIndex2"))
			LeftHandIndex3 = leftIndexFingerMenu.addAction(self.tr("LeftHandIndex3"))
			LeftHandIndex4 = leftIndexFingerMenu.addAction(self.tr("LeftHandIndex4"))
			leftMiddleFingerMenu = leftFingersMenu.addMenu(self.tr("Middle")) 
			LeftInHandMiddle = leftMiddleFingerMenu.addAction(self.tr("LeftInHandMiddle"))
			LeftHandMiddle1 = leftMiddleFingerMenu.addAction(self.tr("LeftHandMiddle1"))
			LeftHandMiddle2 = leftMiddleFingerMenu.addAction(self.tr("LeftHandMiddle2"))
			LeftHandMiddle3 = leftMiddleFingerMenu.addAction(self.tr("LeftHandMiddle3"))
			LeftHandMiddle4 = leftMiddleFingerMenu.addAction(self.tr("LeftHandMiddle4"))
			leftRingFingerMenu = leftFingersMenu.addMenu(self.tr("Ring")) 
			LeftInHandRing = leftRingFingerMenu.addAction(self.tr("LeftInHandRing"))
			LeftHandRing1 = leftRingFingerMenu.addAction(self.tr("LeftHandRing1"))
			LeftHandRing2 = leftRingFingerMenu.addAction(self.tr("LeftHandRing2"))
			LeftHandRing3 = leftRingFingerMenu.addAction(self.tr("LeftHandRing3"))
			LeftHandRing4 = leftRingFingerMenu.addAction(self.tr("LeftHandRing4"))
			leftPinkyFingerMenu = leftFingersMenu.addMenu(self.tr("Pinky")) 
			LeftInHandPinky = leftPinkyFingerMenu.addAction(self.tr("LeftInHandPinky"))
			LeftHandPinky1 = leftPinkyFingerMenu.addAction(self.tr("LeftHandPinky1"))
			LeftHandPinky2 = leftPinkyFingerMenu.addAction(self.tr("LeftHandPinky2"))
			LeftHandPinky3 = leftPinkyFingerMenu.addAction(self.tr("LeftHandPinky3"))
			LeftHandPinky4 = leftPinkyFingerMenu.addAction(self.tr("LeftHandPinky4"))	
			RightShoulderMenu = shouldersArmsMenu.addMenu(self.tr("RightShoulder")) 
			RightShoulder = RightShoulderMenu.addAction(self.tr("RightShoulder"))
			RightShoulderExtra = RightShoulderMenu.addAction(self.tr("RightShoulderExtra"))
			RightArmMenu = shouldersArmsMenu.addMenu(self.tr("RightArm")) 
			RightArm = RightArmMenu.addAction(self.tr("RightArm"))
			RightArmRollMenu = RightArmMenu.addMenu(self.tr("RightArmRoll")) 
			LeafRightArmRoll1 = RightArmRollMenu.addAction(self.tr("LeafRightArmRoll1"))
			LeafRightArmRoll2 = RightArmRollMenu.addAction(self.tr("LeafRightArmRoll2"))
			LeafRightArmRoll3 = RightArmRollMenu.addAction(self.tr("LeafRightArmRoll3"))
			LeafRightArmRoll4 = RightArmRollMenu.addAction(self.tr("LeafRightArmRoll4"))
			LeafRightArmRoll5 = RightArmRollMenu.addAction(self.tr("LeafRightArmRoll5"))
			RightForeArm = RightArmMenu.addAction(self.tr("RightForeArm"))
			RightForeArmRollMenu = RightArmMenu.addMenu(self.tr("RightForeArmRoll")) 
			LeafRightForeArmRoll1 = RightForeArmRollMenu.addAction(self.tr("LeafRightForeArmRoll1"))
			LeafRightForeArmRoll2 = RightForeArmRollMenu.addAction(self.tr("LeafRightForeArmRoll2"))
			LeafRightForeArmRoll3 = RightForeArmRollMenu.addAction(self.tr("LeafRightForeArmRoll3"))
			LeafRightForeArmRoll4 = RightForeArmRollMenu.addAction(self.tr("LeafRightForeArmRoll4"))
			LeafRightForeArmRoll5 = RightForeArmRollMenu.addAction(self.tr("LeafRightForeArmRoll5"))
			RightHand = RightArmMenu.addAction(self.tr("RightHand"))
			RightFingerBase = RightArmMenu.addAction(self.tr("RightFingerBase"))
			RightFingersMenu = RightArmMenu.addMenu(self.tr("RightFingers")) 
			RightThumbFingerMenu = RightFingersMenu.addMenu(self.tr("Thumb")) 
			RightInHandThumb = RightThumbFingerMenu.addAction(self.tr("RightInHandThumb"))
			RightHandThumb1 = RightThumbFingerMenu.addAction(self.tr("RightHandThumb1"))
			RightHandThumb2 = RightThumbFingerMenu.addAction(self.tr("RightHandThumb2"))
			RightHandThumb3 = RightThumbFingerMenu.addAction(self.tr("RightHandThumb3"))
			RightHandThumb4 = RightThumbFingerMenu.addAction(self.tr("RightHandThumb4"))
			RightIndexFingerMenu = RightFingersMenu.addMenu(self.tr("Index")) 
			RightInHandIndex = RightIndexFingerMenu.addAction(self.tr("RightInHandIndex"))
			RightHandIndex1 = RightIndexFingerMenu.addAction(self.tr("RightHandIndex1"))
			RightHandIndex2 = RightIndexFingerMenu.addAction(self.tr("RightHandIndex2"))
			RightHandIndex3 = RightIndexFingerMenu.addAction(self.tr("RightHandIndex3"))
			RightHandIndex4 = RightIndexFingerMenu.addAction(self.tr("RightHandIndex4"))
			RightMiddleFingerMenu = RightFingersMenu.addMenu(self.tr("Middle")) 
			RightInHandMiddle = RightMiddleFingerMenu.addAction(self.tr("RightInHandMiddle"))
			RightHandMiddle1 = RightMiddleFingerMenu.addAction(self.tr("RightHandMiddle1"))
			RightHandMiddle2 = RightMiddleFingerMenu.addAction(self.tr("RightHandMiddle2"))
			RightHandMiddle3 = RightMiddleFingerMenu.addAction(self.tr("RightHandMiddle3"))
			RightHandMiddle4 = RightMiddleFingerMenu.addAction(self.tr("RightHandMiddle4"))
			RightRingFingerMenu = RightFingersMenu.addMenu(self.tr("Ring")) 
			RightInHandRing = RightRingFingerMenu.addAction(self.tr("RightInHandRing"))
			RightHandRing1 = RightRingFingerMenu.addAction(self.tr("RightHandRing1"))
			RightHandRing2 = RightRingFingerMenu.addAction(self.tr("RightHandRing2"))
			RightHandRing3 = RightRingFingerMenu.addAction(self.tr("RightHandRing3"))
			RightHandRing4 = RightRingFingerMenu.addAction(self.tr("RightHandRing4"))
			RightPinkyFingerMenu = RightFingersMenu.addMenu(self.tr("Pinky")) 
			RightInHandPinky = RightPinkyFingerMenu.addAction(self.tr("RightInHandPinky"))
			RightHandPinky1 = RightPinkyFingerMenu.addAction(self.tr("RightHandPinky1"))
			RightHandPinky2 = RightPinkyFingerMenu.addAction(self.tr("RightHandPinky2"))
			RightHandPinky3 = RightPinkyFingerMenu.addAction(self.tr("RightHandPinky3"))
			RightHandPinky4 = RightPinkyFingerMenu.addAction(self.tr("RightHandPinky4"))
			neckMenu = menu.addMenu(self.tr("Neck"))
			Neck = neckMenu.addAction(self.tr("Neck"))
			Neck1 = neckMenu.addAction(self.tr("Neck1"))
			Neck2 = neckMenu.addAction(self.tr("Neck2"))
			Neck3 = neckMenu.addAction(self.tr("Neck3"))
			Neck4 = neckMenu.addAction(self.tr("Neck4"))
			Neck5 = neckMenu.addAction(self.tr("Neck5"))
			Neck6 = neckMenu.addAction(self.tr("Neck6"))
			Neck7 = neckMenu.addAction(self.tr("Neck7"))
			Neck8 = neckMenu.addAction(self.tr("Neck8"))
			Neck9 = neckMenu.addAction(self.tr("Neck9"))
			Head = menu.addAction(self.tr("Head"))

			self.linkHikMenuAction(menu, position)

			clearAction = menu.addAction(self.tr("Clear"))  
			clearAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
			clearAction.triggered.connect(lambda: self.clearCell(position))

			clearRowAction = menu.addAction(self.tr("Clear Row"))
			clearRowAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))  
			clearRowAction.triggered.connect(self.clearRow)

	def editMenu(self, position):
		"""Right-Click/Context Menu open trigger.
		Create a menu based on the right click position and column, and connect all actions to their related triggers.
		"""

		treeWidget = self.sender()
		menu = QtWidgets.QMenu()

		index = treeWidget.indexAt(position)
		if index.isValid() and index.column() == 3:
			if treeWidget.currentItem():
				self.createHIKSlotsMenu(menu, position)
		elif index.column() < 3:
			addRowAction = menu.addAction(self.tr("Add Row"))
			addRowAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
			addRowAction.triggered.connect(self.addRowToTable)

			if treeWidget.currentItem():
				removeRowAction = menu.addAction(self.tr("Remove Selected Rows"))  
				removeRowAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
				removeRowAction.triggered.connect(self.removeRowFromTable)

				loadSelectedAction = menu.addAction(self.tr("Load Selected"))  
				loadSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/selectObject.png")))
				loadSelectedAction.triggered.connect(lambda: self.loadSelectedToCell(position))

				clearCellAction = menu.addAction(self.tr("Clear Cell"))  
				clearCellAction.triggered.connect(lambda: self.clearCell(position))

				clearRowAction = menu.addAction(self.tr("Clear Row"))  
				clearRowAction.triggered.connect(self.clearRow)


		menu.exec_(treeWidget.viewport().mapToGlobal(position))

	### DRAW ###
	def gatherCharDefData(self):
		"""Gather character definition data from UI into a python dict.
		"""

		self.charDefData = {}

		for rowIdx in range(self.charDef_trv.topLevelItemCount()):
			componentRow = self.charDef_trv.invisibleRootItem().child(rowIdx)
			component = componentRow.text(0)
			blockSkelItem = componentRow.text(1)
			targetSkelItem = componentRow.text(2)
			hikSlot = componentRow.text(3)
			
			if any([component, blockSkelItem, targetSkelItem, hikSlot]):
				self.charDefData.update({component: {"blockSkelItem": blockSkelItem, "targetSkelItem": targetSkelItem, "hikSlot": hikSlot}})

		return self.charDefData

	def drawData(self):
		"""Draw gathered data into the UI.
		"""

		self.charDef_trv.blockSignals(True)
		self.charDef_trv.clear()

		for k, componentKey in enumerate(sorted(self.charDefData.keys())):
			componentItem = QTreeWidgetItem(self.charDef_trv, [componentKey, self.charDefData[componentKey]["blockSkelItem"], self.charDefData[componentKey]["targetSkelItem"], self.charDefData[componentKey]["hikSlot"]])
			componentItem.setFlags(componentItem.flags() | QtCore.Qt.ItemIsEditable)
			componentItem.setSizeHint(0, QtCore.QSize(300, 22))

		self.charDef_trv.blockSignals(False)

		self.blockNameSpace_le.blockSignals(True)
		self.targetNameSpace_le.blockSignals(True)
		self.blockNameSpace_le.setText(self.blockNameSpace)
		self.targetNameSpace_le.setText(self.targetNameSpace)
		self.blockNameSpace_le.blockSignals(False)
		self.targetNameSpace_le.blockSignals(False)

	def loadWindow(self):
		"""Main UI load
		"""
		self.show()
		
def loadCharacterDefenitionUI():
	"""Load the Charecter Definition UI from globals, avoid UI duplication.
	"""
	
	charDefData = {}
	blockNameSpace = ""
	targetNameSpace = ""

	if pm.window("mnsCharacterDefenitionUI", exists=True):
		if "mnsCharacterDefenitionUI" in globals(): 
			mnsCharacterDefenitionUI = globals()["mnsCharacterDefenitionUI"]
			charDefData = mnsCharacterDefenitionUI.gatherCharDefData()
			blockNameSpace = mnsCharacterDefenitionUI.blockNameSpace
			targetNameSpace = mnsCharacterDefenitionUI.targetNameSpace

	previousPosition = mnsUIUtils.reloadWindow("mnsCharacterDefenitionUI")
	
	if mnsUtils.mnsLicStatusCheck(1):
		charDefUI = MnsCharacterDefenitionUI()
		globals().update({"mnsCharacterDefenitionUI": charDefUI})
		charDefUI.loadWindow()
		if previousPosition: charDefUI.move(previousPosition)
		if charDefData:
			pass
			charDefUI.charDefData = charDefData
			charDefUI.blockNameSpace = blockNameSpace
			charDefUI.targetNameSpace = targetNameSpace
			charDefUI.drawData()