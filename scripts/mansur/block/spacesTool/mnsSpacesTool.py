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
from ..core import blockUtility as blkUtils
from ...core.globals import *
from ...gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsSpacesTool.ui")
class MnsSpacesTool(form_class, base_class):
	"""Spaces Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsSpacesTool, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsSpacesTool") 
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		# locals
		self.mayaSelectCallBack = None
		self.mayaTimeChangedCallBack = None
		self.insertCallbacks()

		self.spacesDict = {"space": [], "translateSpace": [], "orientSpace": []}
		self.limbs = {}
		self.spaceCtrls = []
		self.spaceCBPairing = {"space": self.spaces_cb, "translateSpace": self.tSpaces_cb, "orientSpace": self.oSpaces_cb}

		#methods
		self.installEventFilter(self)
		self.connectSignals()
		self.initializeView()
		mnsGui.setGuiStyle(self, "Spaces Tool")

	##################	
	###### INIT ######
	##################

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.sequence_rb.toggled.connect(self.setSequenceMode)
		self.bake_btn.toggled.connect(self.setAutoKeyMode)
		self.autoKey_btn.toggled.connect(self.setAutoKeyMode)
		self.space_btn.released.connect(self.spaceSwitch)
		self.translateSpace_btn.released.connect(self.spaceSwitch)
		self.orientSpace_btn.released.connect(self.spaceSwitch)
		self.fromTimeSlider_cbx.toggled.connect(self.setSequenceRange)
		self.selectHost_btn.released.connect(self.selectIKFKHost)
		self.toFK_btn.released.connect(lambda: self.fkIKSwitch(0))
		self.toIK_btn.released.connect(lambda: self.fkIKSwitch(1))

	##################	
	###### View ######
	##################

	def initializeView(self):
		self.mainTabs_tw.setCurrentIndex(0)
		self.sceneSelectionChanged()
		self.setSequenceRange()

		###ICONS
		self.selectHost_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/IsolateSelected.png"))
		self.autoKey_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/autoKeyframe.png"))
		self.bake_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/bakeAnimation.png"))
		self.translateSpace_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/currentNamespaceParent.png"))
		self.orientSpace_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/currentNamespaceParent.png"))
		self.space_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/currentNamespaceParent.png"))
		self.toIK_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/out_ikHandle.png"))
		self.toFK_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/HIKCharacterToolFK.png"))

	def setSequenceRange(self):
		if self.fromTimeSlider_cbx.isChecked():
			startTime = pm.playbackOptions(q = True, min = True)
			endTime = pm.playbackOptions(q = True, max = True)
			self.startFrmae_sb.setValue(startTime)
			self.endFrame_sb.setValue(endTime)
			self.startFrmae_sb.setEnabled(True)
			self.endFrame_sb.setEnabled(True)
		else:
			self.startFrmae_sb.setEnabled(False)
			self.endFrame_sb.setEnabled(False)
	
	def setSpacesMode(self):
		if self.mainTabs_tw.currentIndex() == 0:
			self.bake_btn.setEnabled(False)
			self.currentFrame_rb.setChecked(True)
			self.sequence_rb.setEnabled(False)
		else:
			self.bake_btn.setEnabled(True)
			self.sequence_rb.setEnabled(True)

	def setSequenceMode(self, state):
		for childWidget in [self.sequence_gbx] + self.sequence_gbx.children():
			childWidget.setEnabled(state)
		if state: 
			self.sequence_gbx.setStyleSheet("")
			if self.fromTimeSlider_cbx.isChecked():
				self.setSequenceRange()
		else: self.sequence_gbx.setStyleSheet("background-color: rgb(75, 75, 75);")

	def setAutoKeyMode(self, state):
		self.bake_btn.blockSignals(True)
		self.autoKey_btn.blockSignals(True)
		if not self.autoKey_btn.isChecked() and self.sequence_rb.isChecked():
			self.currentFrame_rb.setChecked(True)
		self.bake_btn.blockSignals(False)
		self.autoKey_btn.blockSignals(False)

	def setIKFKView(self):
		btnState = False
		if self.limbs: btnState = True
		self.toIK_btn.setEnabled(btnState)
		self.toFK_btn.setEnabled(btnState)
		self.selectHost_btn.setEnabled(btnState)

	def setAvailbleLimbs(self):
		self.limbs = {}

		sel = cmds.ls(sl=True)
		if sel:
			for ctrl in sel:
				ctrl = mnsUtils.validateNameStd(ctrl)
				if ctrl:
					rootGuide = blkUtils.getRootGuideFromCtrl(ctrl)
					rootGuide = mnsUtils.validateNameStd(rootGuide)
					if rootGuide and not rootGuide.node in self.limbs.keys():
						status, modType = mnsUtils.validateAttrAndGet(rootGuide, "modType", None)
						if modType and "limb" in modType.lower():
							self.limbs.update({rootGuide.node: ctrl})
		self.setIKFKView()

	def setSpacesView(self):
		spaceVis = True
		splitSpaceVis = False

		if self.spacesDict["translateSpace"]:
			splitSpaceVis = True
			spaceVis = False

		self.space_lbl.setHidden(not spaceVis)
		self.spaces_cb.setHidden(not spaceVis)
		self.space_btn.setHidden(not spaceVis)
		self.tSpace_lbl.setHidden(not splitSpaceVis)
		self.tSpaces_cb.setHidden(not splitSpaceVis)
		self.translateSpace_btn.setHidden(not splitSpaceVis)
		self.oSpace_lbl.setHidden(not splitSpaceVis)
		self.oSpaces_cb.setHidden(not splitSpaceVis)
		self.orientSpace_btn.setHidden(not splitSpaceVis)

		if self.spacesDict["space"]:
			self.space_btn.setEnabled(True)
			self.translateSpace_btn.setEnabled(False)
			self.orientSpace_btn.setEnabled(False)
		elif self.spacesDict["translateSpace"] or self.spacesDict["orientSpace"]:
			self.space_btn.setEnabled(False)
			self.translateSpace_btn.setEnabled(True)
			self.orientSpace_btn.setEnabled(True)

		self.spaces_cb.clear()
		self.spaces_cb.addItems(self.spacesDict["space"])
		self.tSpaces_cb.clear()
		self.tSpaces_cb.addItems(self.spacesDict["translateSpace"])
		self.oSpaces_cb.clear()
		self.oSpaces_cb.addItems(self.spacesDict["orientSpace"])

		if spaceVis and self.spacesDict["space"]:
			status, currentIndex = mnsUtils.validateAttrAndGet(self.spaceCtrls[0].node, "space", 0)
			spaceValues = [mnsString.stringMultiReplaceBySingle(space, [" ", "[D]", "*"], "") for space in mnsUtils.splitEnumToStringList("space", self.spaceCtrls[0].node)]
			if spaceValues[currentIndex] in self.spacesDict["space"]:
				newIndex = self.spacesDict["space"].index(spaceValues[currentIndex])
				self.spaces_cb.setCurrentIndex(newIndex)
		if splitSpaceVis and self.spacesDict["translateSpace"]:
			status, currentIndex = mnsUtils.validateAttrAndGet(self.spaceCtrls[0].node, "translateSpace", 0)
			spaceValues = [mnsString.stringMultiReplaceBySingle(space, [" ", "[D]", "*"], "") for space in mnsUtils.splitEnumToStringList("translateSpace", self.spaceCtrls[0].node)]
			if spaceValues[currentIndex] in self.spacesDict["translateSpace"]:
				newIndex = self.spacesDict["translateSpace"].index(spaceValues[currentIndex])
				self.tSpaces_cb.setCurrentIndex(newIndex)
		if splitSpaceVis and self.spacesDict["orientSpace"]:
			status, currentIndex = mnsUtils.validateAttrAndGet(self.spaceCtrls[0].node, "orientSpace", 0)
			spaceValues = [mnsString.stringMultiReplaceBySingle(space, [" ", "[D]", "*"], "") for space in mnsUtils.splitEnumToStringList("orientSpace", self.spaceCtrls[0].node)]
			if spaceValues[currentIndex] in self.spacesDict["orientSpace"]:
				newIndex = self.spacesDict["orientSpace"].index(spaceValues[currentIndex])
				self.oSpaces_cb.setCurrentIndex(newIndex)

	def setAvailbleSpaces(self):
		self.spacesDict = {"space": [], "translateSpace": [], "orientSpace": []}
		self.spaceCtrls = []

		spaceCtrls = []
		splitSpaceCtrls = []

		sel = cmds.ls(sl=True)
		if sel:
			for ctrl in sel:
				ctrl = mnsUtils.validateNameStd(ctrl)
				if ctrl:
					for k, attrName in enumerate(["space", "translateSpace", "orientSpace"]):
						status, spaceAttr = mnsUtils.validateAttrAndGet(ctrl, attrName, [])
						if status:
							spaces = [mnsString.stringMultiReplaceBySingle(space, [" ", "[D]", "*"], "") for space in mnsUtils.splitEnumToStringList(attrName, ctrl.node)]
							if not self.spacesDict[attrName]: self.spacesDict[attrName] = spaces
							else: self.spacesDict[attrName] = list(set(self.spacesDict[attrName]).intersection(spaces))
							if k == 0 and not ctrl in spaceCtrls:
								spaceCtrls.append(ctrl)
							elif not ctrl in splitSpaceCtrls:
								splitSpaceCtrls.append(ctrl)

		if self.spacesDict["space"] and self.spacesDict["translateSpace"] and self.spacesDict["orientSpace"]:
			self.spacesDict = {"space": [], "translateSpace": [], "orientSpace": []}
			self.spaceCtrls = []

		if self.spacesDict["space"]:
			self.spaceCtrls = spaceCtrls
		elif self.spacesDict["translateSpace"]:
			self.spaceCtrls = splitSpaceCtrls

		self.setSpacesView()

	def sceneSelectionChanged(self, dummy = None):
		self.setAvailbleSpaces()
		self.setAvailbleLimbs()

	def insertCallbacks(self):
		self.mayaSelectCallBack = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.sceneSelectionChanged)
		self.mayaTimeChangedCallBack = OpenMaya.MEventMessage.addEventCallback("timeChanged", self.sceneSelectionChanged)

	def removeCallbacks(self):
		try: OpenMaya.MMessage.removeCallback(self.mayaSelectCallBack)
		except: pass
		try: OpenMaya.MMessage.removeCallback(self.mayaTimeChangedCallBack)
		except: pass

	def eventFilter(self, source, event):
		"""Override event filter to catch the close trigger to delete the callback
		"""

		if event.type() == QtCore.QEvent.Close:
			self.removeCallbacks()
			
		return super(QtWidgets.QWidget, self).eventFilter(source, event)

	##################	
	##### Action #####
	##################

	def getFramesListFromUIState(self, hostCtrl = None, attrName = ""):
		returnIndices = []
		if self.currentFrame_rb.isChecked():
			currentFrame = pm.currentTime( query=True )
			returnIndices.append(currentFrame)
		else:
			startFrame = self.startFrmae_sb.value()
			endFrame = self.endFrame_sb.value()
			if endFrame > startFrame:
				if not self.bake_btn.isChecked() and hostCtrl and attrName:
					returnIndices = list(dict.fromkeys(pm.keyframe(hostCtrl, at = attrName, time=(startFrame,endFrame), query=True)))
				else:
					returnIndices = [i for i in range(startFrame, endFrame + 1)]

		if not returnIndices: mnsLog.log("Couldn't find any keyed frames for controls. Skipping", svr = 2)
		return returnIndices

	def getSpaceEnumIndexByName(self, node, attr, targetSpaceName):
		index = -1
		for k, spaceName in enumerate(mnsUtils.splitEnumToStringList(attr.attrName(), node)):
			if targetSpaceName in spaceName:
				index = k
				break
		return index

	def spaceSwitch(self):
		self.removeCallbacks()

		if self.spaceCtrls:	
			#create a frame indecies and controls pairing assemebly
			frameIdicesCtrlsPairing = {}
			allFrameIndecies = []
			attrName = self.sender().objectName().split("_")[0]
			targetSpaceName = self.spaceCBPairing[attrName].currentText()

			#first loop to gather all data. 
			#this to avoid multiple sequence runs for multiple controls.
			#main target is to get all relevant frames for all limbs, and run once when matching.
			for ctrl in self.spaceCtrls:
				status, spaceAttr = mnsUtils.validateAttrAndGet(ctrl.node, attrName, returnAttrObject = True)
				if spaceAttr: 
					if not ctrl.node in frameIdicesCtrlsPairing.keys(): 
						#get current relevant frame indices
						seqRange = self.getFramesListFromUIState(ctrl.node, spaceAttr.attrName())
						#get all target xforms from all frames
						xFormPairing = {}
						for frameIdx in seqRange:
							pm.currentTime(frameIdx)
							xForm = pm.xform(ctrl.node, q=1, ws=1, matrix = True)
							xFormPairing.update({frameIdx: xForm})

						allFrameIndecies = sorted(list(dict.fromkeys(allFrameIndecies + seqRange)))
						frameIdicesCtrlsPairing.update({ctrl.node: {"frameIndices": seqRange, "attribute": spaceAttr, "xFormPairing": xFormPairing, "keyControl": ctrl.node}})

			#no act based on the gathed data
			for frameIdx in allFrameIndecies:
				pm.currentTime(frameIdx)
				for ctrlNode in frameIdicesCtrlsPairing:
					relevantFrameIndices = frameIdicesCtrlsPairing[ctrlNode]["frameIndices"]
					if frameIdx in relevantFrameIndices:
						attrObj = frameIdicesCtrlsPairing[ctrlNode]["attribute"]
						targetXFormMatrix = frameIdicesCtrlsPairing[ctrlNode]["xFormPairing"][frameIdx]
						targetEnumIndex = self.getSpaceEnumIndexByName(ctrlNode, attrObj, targetSpaceName)
						attrObj.set(targetEnumIndex)
						pm.xform(ctrlNode, ws=1, matrix = targetXFormMatrix)
						if self.autoKey_btn.isChecked():
							pm.setKeyframe(frameIdicesCtrlsPairing[ctrlNode]["keyControl"], time = frameIdx)

		self.insertCallbacks()

	def selectIKFKHost(self):
		newSelection = []

		for limbRoot in self.limbs.keys():
			refCtrl = self.limbs[limbRoot]
			attrHost = blkUtils.getLimbModuleControls(refCtrl, 3)[2]
			if attrHost: newSelection.append(attrHost)

		if newSelection:
			pm.select(newSelection, r = True)

	def fkIKSwitch(self, mode = 0):
		"""
		mode 0 - Match FK to IK
		mode 1 - Match IK to FK
		"""

		#collect new selection for end of method
		newSelection = []

		#create a frame indecies and controls pairing assemebly
		frameIdicesCtrlsPairing = {}
		allFrameIndecies = []

		#first loop to gather all data. 
		#this to avoid multiple sequence runs for multiple limbs.
		#main target is to get all relevant frames for all limbs, and run once when matching.
		for limbRoot in self.limbs.keys():
			ctrlsAssembly = {"fkControls": {}, "ikControls": {}, "hostCtrl": None}
			refCtrl = self.limbs[limbRoot]

			#first gather relevant controls, and set into the assembly
			fkControls, ikControls, hostCtrl = blkUtils.getLimbModuleControls(refCtrl, mode)
			if hostCtrl:
				newSelection.append(hostCtrl)
				ctrlsAssembly.update({"fkControls": fkControls})
				ctrlsAssembly.update({"ikControls": ikControls})
				ctrlsAssembly.update({"hostCtrl": hostCtrl})
				fkControlsList = [fkControls[key] for key in fkControls.keys() if fkControls[key] and fkControls[key].split("_")[-1] == mnsPS_ctrl]
				ikControlsList = [ikControls[key] for key in ikControls.keys() if ikControls[key] and  ikControls[key].split("_")[-1] == mnsPS_ctrl]
				
				#get current relevant frame indices
				seqRange = self.getFramesListFromUIState(hostCtrl, "ikFkBlend")
				ctrlPairing = fkControlsList
				if mode == 1: ctrlPairing = ikControlsList
				frameIdicesCtrlsPairing.update({hostCtrl: {"keyControls": ctrlPairing, "frameIndices": seqRange, "ctrlsAssembly": ctrlsAssembly}})
				allFrameIndecies = sorted(list(dict.fromkeys(allFrameIndecies + seqRange)))
		
		#no act based on the gathed data
		for frameIdx in allFrameIndecies:
			pm.currentTime(frameIdx)
			for hostCtrl in frameIdicesCtrlsPairing.keys():
				hostCtrl.ikFkBlend.set(1 - mode)
				relevantFrameIndices = frameIdicesCtrlsPairing[hostCtrl]["frameIndices"]
				if frameIdx in relevantFrameIndices:
					blkUtils.limbMatchFkIK(hostCtrl, mode, ctrlsAssembly = frameIdicesCtrlsPairing[hostCtrl]["ctrlsAssembly"])

					if self.autoKey_btn.isChecked():
						pm.setKeyframe(frameIdicesCtrlsPairing[hostCtrl]["keyControls"], time = frameIdx)
						pm.setKeyframe(hostCtrl, time = frameIdx, attribute = "ikFkBlend", v = 1 - mode)
	
		if newSelection: pm.select(newSelection, r = True)

	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsSpacesTool", svr = 0)
		self.show()

def loadSpacesTool(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("Spaces Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsSpacesTool")

	mnsSpacesToolWin = MnsSpacesTool()
	mnsSpacesToolWin.loadWindow()
	if previousPosition: mnsSpacesToolWin.move(previousPosition)
	return mnsSpacesToolWin