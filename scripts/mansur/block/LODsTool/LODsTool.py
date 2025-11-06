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
import os, json
import maya.OpenMaya as OpenMaya
from maya import cmds

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ..core import blockUtility as blkUtils
from ...core import nodes as mnsNodes
from ...core.globals import *
from ...gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "LODsTool.ui")
class MnsLodsTool(form_class, base_class):
	"""Spaces Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsLodsTool, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsLodsTool") 
		iconDir = GLOB_guiIconsDir + "/logo/mansur_01.png"
		self.iconLbl.setPixmap(QtGui.QPixmap(iconDir))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		# locals
		self.rigTops = {}
		self.rigTop = None
		self.puppetRoot = None
		self.namespace = ""
		self.rootGuide = None
		self.lodVisAttr = None
		self.lodsDict = {"lodsDef": {}, "attrHost": None}

		#methods
		self.initializeUI()
		self.connectSignals()
		self.initializeView()
		mnsGui.setGuiStyle(self, "LODs Tool")

	##################	
	###### INIT ######
	##################

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.rigName_cb.currentIndexChanged.connect(self.setRigTop)
		self.addLOD_btn.released.connect(self.addLod)
		self.alpha_rb.toggled.connect(self.setLodStyle)
		self.attrHostAdd_btn.released.connect(self.setAttrHost)
		self.apply_btn.released.connect(self.writeData)
		self.delLastLOD_btn.released.connect(lambda: self.deleteLOD(self.lods_tw.columnCount() - 1))
		self.currentLod_cb.currentIndexChanged.connect(self.updateLODAttrState)

	##################	
	###### View ######
	##################

	def initializeView(self):
		self.lods_tw.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.lods_tw.customContextMenuRequested.connect(self.openMenu)
		
	def initializeUI(self):
		#init rigTops
		self.rigTops = blkUtils.getRigTopAssemblies()
		if self.rigTops: self.rigName_cb.addItems(self.rigTops.keys())
		self.setRigTop()

		if self.lodsDict["lodsDef"]:
			indexName = self.lodsDict["lodsDef"][0]["name"].split("lod")[-1]
			if indexName == str(0):
				self.numeric_rb.setChecked(True)

	def setRigTop(self):
		self.rigTop = None
		self.currentLod_cb.clear()

		currentRig = self.rigName_cb.currentText()
		if currentRig:
			if currentRig in self.rigTops.keys():
				self.rigTop = self.rigTops[self.rigName_cb.currentText()]
		
		self.puppetRoot = None
		self.namespace = ""
		self.rootGuide = None
		self.lodsDict = {"lodsDef": {}, "attrHost": None}

		if self.rigTop: 
			self.puppetRoot = blkUtils.getPuppetRootFromRigTop(self.rigTop) 
			self.namespace = self.rigTop.namespace
			self.rootGuide = blkUtils.getRootGuideFromRigTop(self.rigTop)

			if self.rootGuide:
				status, self.lodsDict = mnsUtils.validateAttrAndGet(self.rootGuide.node, "lodsDef", {})
				if not status: 
					defaultsString = json.dumps({"lodsDef": {}, "attrHost": None})
					mnsUtils.addAttrToObj([self.rootGuide.node], name = "lodsDef", type = str, value = defaultsString, locked = True, cb = False, keyable = False)
					
				status, self.lodsDict = mnsUtils.validateAttrAndGet(self.rootGuide.node, "lodsDef", {})

				if status:
					self.lodsDict = json.loads(self.lodsDict)
					self.convertLodsDictKeysToInts()

				status, self.lodVisAttr = mnsUtils.validateAttrAndGet(self.rootGuide.node, "LOD_Vis", None, returnAttrObject = True)
				if not status:
					mnsUtils.addAttrToObj([self.rootGuide.node], name = "LOD_Vis", type = list, value = [" "], locked = False, cb = True, keyable = True)
				
				status, lodVisAttrDef = mnsUtils.validateAttrAndGet(self.rootGuide.node, "LOD_Vis", None)
				if status:
					lodOptions = [self.lodsDict["lodsDef"][o]["name"] for o in self.lodsDict["lodsDef"]]
					self.currentLod_cb.addItems(lodOptions)
					self.currentLod_cb.setCurrentIndex(lodVisAttrDef)

				self.attrHost_le.setText(self.lodsDict["attrHost"])

		self.drawLODsView()

	def drawLODsView(self):
		self.lods_tw.clear()
		self.lods_tw.setColumnCount(0)
		self.lods_tw.setRowCount(0)

		numOfRows = 0
		for lodKey in self.lodsDict["lodsDef"]:
			rowNum = len(self.lodsDict["lodsDef"][lodKey]["nodes"])
			if rowNum > numOfRows: numOfRows = rowNum
		self.lods_tw.setRowCount(numOfRows)

		for lodKey in sorted(self.lodsDict["lodsDef"]):
			self.lods_tw.insertColumn(lodKey)
			colItem = QtWidgets.QTableWidgetItem()
			colItem.setText(self.lodsDict["lodsDef"][lodKey]["name"]);
			self.lods_tw.setHorizontalHeaderItem(lodKey,colItem);
			self.lods_tw.setColumnWidth(lodKey, 200)

			for k, nodeName in enumerate(self.lodsDict["lodsDef"][lodKey]["nodes"]):
				item = QtWidgets.QTableWidgetItem(nodeName)
				self.lods_tw.setItem(k, lodKey, item)

	def convertLodsDictKeysToInts(self):
		updatedDict = {"lodsDef": {}}
		updatedDict.update({"attrHost": self.lodsDict["attrHost"]})
		for lodKey in sorted(self.lodsDict["lodsDef"]):
			indexName = self.lodsDict["lodsDef"][lodKey]["name"]
			lodKeyInt = int(lodKey)
			updatedDict["lodsDef"].update({lodKeyInt: {"name": indexName, "nodes": self.lodsDict["lodsDef"][lodKey]["nodes"]}})
		self.lodsDict = updatedDict

	def openMenu(self, position):
		if self.lodsDict["lodsDef"]:
			column = self.lods_tw.horizontalHeader().logicalIndexAt(position)
			menu = QtWidgets.QMenu()
			mnsUIUtils.createTextSeparator(self.lods_tw.horizontalHeaderItem(column).text(), menu, menu)

			setSelectedAction = menu.addAction(self.tr("Set Selected Items"))
			setSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTkPropSet_100.png")))
			setSelectedAction.triggered.connect(partial(self.setSelectedItems, column))

			addSelectedAction = menu.addAction(self.tr("Add Selected Items"))
			addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
			addSelectedAction.triggered.connect(partial(self.addSelectedItems, column))

			removeSelectedAction = menu.addAction(self.tr("Remove Selected Items"))
			removeSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
			removeSelectedAction.triggered.connect(partial(self.removeSlectedItems, column))

			clearALLAction = menu.addAction(self.tr("Clear All"))
			clearALLAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/clearAll.png")))
			clearALLAction.triggered.connect(self.clearALLLods)

			if column == self.lods_tw.columnCount() - 1:
				deleteLodAction = menu.addAction(self.tr("Delete " + self.lods_tw.horizontalHeaderItem(column).text()))
				deleteLodAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/hotkeyFieldClear.png")))
				deleteLodAction.triggered.connect(partial(self.deleteLOD, column))

			menu.exec_(self.lods_tw.viewport().mapToGlobal(position))

	##################	
	##### Action #####
	##################

	def setLodStyle(self):
		updatedDict = {"lodsDef": {}}
		updatedDict.update({"attrHost": self.lodsDict["attrHost"]})
		for lodKey in sorted(self.lodsDict["lodsDef"]):
			indexName = self.lodsDict["lodsDef"][lodKey]["name"].split("lod")[-1]
			if indexName == str(lodKey) and self.alpha_rb.isChecked():
				indexName = "lod" + chr(int(indexName) + 65)
			elif indexName != str(lodKey) and not self.alpha_rb.isChecked():
				indexName = "lod" + str(ord(indexName) - 65)
			updatedDict["lodsDef"].update({lodKey: {"name": indexName, "nodes": self.lodsDict["lodsDef"][lodKey]["nodes"]}})
		self.lodsDict = updatedDict
		self.drawLODsView()

	def setSelectedItems(self, index = 0):
		sel = [s.nodeName() for s in pm.ls(sl = True) if s != self.rigTop.node and s not in self.rigTop.node.listRelatives(c = True, type = "transform")]
		self.lodsDict["lodsDef"][index]["nodes"] = sel
		self.drawLODsView()

	def addSelectedItems(self, index = 0):
		sel = [s.nodeName() for s in pm.ls(sl = True) if s != self.rigTop.node and s not in self.rigTop.node.listRelatives(c = True, type = "transform")]
		self.lodsDict["lodsDef"][index]["nodes"] += sel
		self.drawLODsView()

	def removeSlectedItems(self, index = 0):
		for sItem in self.lods_tw.selectedItems():
			if sItem.column() == index:
				self.lods_tw.takeItem(sItem.row(), sItem.column())

	def addLod(self):
		currnetLodsDef = self.lodsDict["lodsDef"]
		newLODIndex = len(currnetLodsDef)
		newLODName = "lod" + str(newLODIndex)
		if self.alpha_rb.isChecked():
			newLODName = "lod" + chr(newLODIndex + 65)

		self.lodsDict["lodsDef"].update({newLODIndex: {"name": newLODName, "nodes": []}})
		self.drawLODsView()
	
	def deleteLOD(self, index = 0):
		self.lodsDict["lodsDef"].pop(index)
		self.drawLODsView()

	def clearALLLods(self):
		self.lodsDict["lodsDef"] = {}
		self.drawLODsView()

	def updateLODAttrState(self, index = 0):
		if self.rootGuide:
			try:
				self.rootGuide.node.LOD_Vis.set(index)
			except:
				pass

	def setAttrHost(self):
		sel = pm.ls(sl=True)
		if sel:
			sel = mnsUtils.validateNameStd(sel[0])
			if sel:
				if sel.suffix == mnsPS_gCtrl or sel.suffix == mnsPS_gRootCtrl:
					self.attrHost_le.setText(sel.node.nodeName())
				else:
					mnsLog.log("Only Block guide objects are allowed.", svr = 2)
			else:
				mnsLog.log("Only Block guide objects are allowed.", svr = 2)
	
	def readDataFromUI(self):
		newData = {"lodsDef": {}, "attrHost": self.attrHost_le.text()}

		for colIndex in range(self.lods_tw.columnCount()):
			lodName = self.lods_tw.horizontalHeaderItem(colIndex).text()
			newItem = {"name": lodName, "nodes": []}
			for rowIndex in range(self.lods_tw.rowCount()):
				item = self.lods_tw.item(rowIndex, colIndex)
				if item:
					itemText = item.text()
					if itemText:
						newItem["nodes"].append(itemText)
			newData["lodsDef"].update({colIndex: newItem})
		return newData

	def writeData(self):
		newData = self.readDataFromUI()

		#delete previous condition nodes
		outCons = self.rootGuide.node.LOD_Vis.listConnections(s = True, d = True)
		if outCons:
			for oc in outCons:
				if type(oc) == pm.nodetypes.Condition:
					pm.delete(oc)

		mnsUtils.addAttrToObj([self.rootGuide.node], name = "lodsDef", type = str, value = json.dumps(newData), locked = True, cb = False, keyable = False, replace = True)
		stringData = [" "]
		if self.lods_tw.columnCount() > 0:
			stringData = [newData["lodsDef"][k]["name"] for k in newData["lodsDef"].keys()]

		mnsUtils.addAttrToObj([self.rootGuide.node], name = "LOD_Vis", type = list, value = stringData, locked = False, cb = True, keyable = True, replace = True)
		
		#delete previous node
		outCons = self.rootGuide.node.LOD_Vis.listConnections(s = True, d = True)
		if outCons:
			for oc in outCons:
				if type(oc) == pm.nodetypes.Condition:
					pm.delete(oc)

		#connect the vis attributes
		if self.lods_tw.columnCount() > 0:
			for lodKey in newData["lodsDef"]:
				if newData["lodsDef"][lodKey]["nodes"]:
					conNode = mnsNodes.conditionNode(self.rootGuide.node.LOD_Vis, int(lodKey), [1,1,1], [0,0,0])
					for nodeName in newData["lodsDef"][lodKey]["nodes"]:
						node = mnsUtils.checkIfObjExistsAndSet(nodeName)
						if node:
							conNode.node.outColorR >> node.v

		#restart tool
		loadLodsTool()

	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsLodsTool", svr = 0)
		self.show()

def loadLodsTool(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("LODs Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsLodsTool")

	mnsLodsToolWin = MnsLodsTool()
	mnsLodsToolWin.loadWindow()
	if previousPosition: mnsLodsToolWin.move(previousPosition)
	return mnsLodsToolWin

