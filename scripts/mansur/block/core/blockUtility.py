"""=== Author: Assaf Ben Zur ===
BLOCK Core Utility Library.
This library contains all utility methods used primarily by BLOCK.
The objective of this library is mainting most Block-Core abilities external and independent.
"""

#global dependencies
import os, fnmatch, imp, json, math
from os.path import dirname, abspath


from maya import cmds
import pymel.core as pm

from inspect import getmembers, isfunction
from maya import cmds
import maya.mel as mel

#mns dependencies
from ...core.prefixSuffix import *
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import log as mnsLog
from ...core import nodes as mnsNodes
from ...core import meshUtility as mnsMeshUtils
from . import controlShapes as blkCtrlShps
mansur = __import__(__name__.split('.')[0])

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtWidgets, QtCore, QtGui
else:
	from PySide2 import QtWidgets, QtCore, QtGui

class MnsRigInfo(QtWidgets.QDialog):
	"""Mansur - About dialog
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window(), rigInfoData = {}):
		super(MnsRigInfo, self).__init__(parent)
		self.setObjectName("mnsRigInfo") 
		self.setWindowTitle("Rig Info")

		self.setWindowIcon(QtGui.QIcon(GLOB_guiIconsDir + "/logo/mansur_logo_noText.png"))

		layout = QtWidgets.QVBoxLayout()

		vLine = QtWidgets.QFrame()
		vLine.setFrameShape(QtWidgets.QFrame.HLine)
		vLine.setFrameShadow(QtWidgets.QFrame.Sunken)
		vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
		layout.addWidget(vLine)

		iconHLay = QtWidgets.QHBoxLayout()
		spacerA = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		iconHLay.addItem(spacerA)
		iconLbl = QtWidgets.QLabel()
		iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/info.png"))
		iconHLay.addWidget(iconLbl)
		
		rigName_lbl = QtWidgets.QLabel()
		if "rigName" in rigInfoData.keys():
			rigName_lbl.setText("<b>" + rigInfoData["rigName"] + "</b>")

		iconHLay.addWidget(rigName_lbl)
		spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		iconHLay.addItem(spacer)

		layout.addLayout(iconHLay)

		vLine = QtWidgets.QFrame()
		vLine.setFrameShape(QtWidgets.QFrame.HLine)
		vLine.setFrameShadow(QtWidgets.QFrame.Sunken)
		vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
		layout.addWidget(vLine)

		#construction version
		constructVerHLay = QtWidgets.QHBoxLayout()
		constructVerLbl = QtWidgets.QLabel("Mansur-Rig Version:")
		constructVerLbl.setFixedWidth(200)
		constructVerHLay.addWidget(constructVerLbl)

		textContainer = QtWidgets.QLineEdit()
		textContainer.setFixedWidth(200)
		if "mnsVersion" in rigInfoData.keys():
			textContainer.setText(rigInfoData["mnsVersion"])
		textContainer.setReadOnly(True)
		constructVerHLay.addWidget(textContainer)
		layout.addLayout(constructVerHLay)

		#construction version
		mayaVerVerHLay = QtWidgets.QHBoxLayout()
		mayaVerVerLbl = QtWidgets.QLabel("Maya Version:")
		mayaVerVerLbl.setFixedWidth(200)
		mayaVerVerHLay.addWidget(mayaVerVerLbl)

		textContainer = QtWidgets.QLineEdit()
		textContainer.setFixedWidth(200)
		if "mayaVersion" in rigInfoData.keys():
			textContainer.setText(rigInfoData["mayaVersion"])
		textContainer.setReadOnly(True)
		mayaVerVerHLay.addWidget(textContainer)
		layout.addLayout(mayaVerVerHLay)

		#time stamp
		timeStampHLay = QtWidgets.QHBoxLayout()
		timeStampLbl = QtWidgets.QLabel("Constructed at:")
		timeStampHLay.addWidget(timeStampLbl)

		textContainer = QtWidgets.QLineEdit()
		textContainer.setFixedWidth(200)
		if "timeStamp" in rigInfoData.keys():
			textContainer.setText(rigInfoData["timeStamp"])
		textContainer.setReadOnly(True)
		timeStampHLay.addWidget(textContainer)
		layout.addLayout(timeStampHLay)

		#user
		userHLay = QtWidgets.QHBoxLayout()
		userLbl = QtWidgets.QLabel("Constructed by:")
		userHLay.addWidget(userLbl)

		textContainer = QtWidgets.QLineEdit()
		textContainer.setFixedWidth(200)
		if "user" in rigInfoData.keys():
			textContainer.setText(rigInfoData["user"])
		textContainer.setReadOnly(True)
		userHLay.addWidget(textContainer)
		layout.addLayout(userHLay)

		#num modules
		numModulesHLay = QtWidgets.QHBoxLayout()
		numModulesLbl = QtWidgets.QLabel("Modules Built Count:")
		numModulesHLay.addWidget(numModulesLbl)

		textContainer = QtWidgets.QLineEdit()
		textContainer.setFixedWidth(200)
		if "numBuiltModules" in rigInfoData.keys():
			textContainer.setText(str(rigInfoData["numBuiltModules"]))
		textContainer.setReadOnly(True)
		numModulesHLay.addWidget(textContainer)
		layout.addLayout(numModulesHLay)

		#buildTime
		buildTimeHLay = QtWidgets.QHBoxLayout()
		numModulesLbl = QtWidgets.QLabel("Build Time:")
		buildTimeHLay.addWidget(numModulesLbl)

		textContainer = QtWidgets.QLineEdit()
		textContainer.setFixedWidth(200)
		if "buildTime" in rigInfoData.keys():
			textContainer.setText(str(rigInfoData["buildTime"]))
		textContainer.setReadOnly(True)
		buildTimeHLay.addWidget(textContainer)
		layout.addLayout(buildTimeHLay)

		self.close_btn = QtWidgets.QPushButton("Close")
		layout.addWidget(self.close_btn)

		self.setLayout(layout)
		
		self.close_btn.clicked.connect(self.destroy)
		self.show()

###############################
###### globals ################
###############################

def getTabTitleAndIndex(name):
	tabTitle = "Home"
	tabIndex = 0
	
	if name == "pickerTab_btn":
		tabTitle = "Picker"
		tabIndex = 1
	elif name == "deformationTab_btn":
		tabTitle = "Deformation"
		tabIndex = 2
	elif name == "mocapTab_btn":
		tabTitle = "Mocap/Game-Engine"
		tabIndex = 3
	elif name == "utilityTab_btn":
		tabTitle = "Utility"
		tabIndex = 4
	
	return tabTitle, tabIndex
	
def attemptModulePathFixForRootGuide(guideRoot, existingBtns):
	fixed = False
	if guideRoot.hasAttr("modType"):
		if guideRoot.modType.get() in existingBtns:
			if guideRoot.modPath.get() != existingBtns[guideRoot.modType.get()].path:
				mnsLog.log("Fixing module path for '" + guideRoot.nodeName() + "'.", svr = 2)
				guideRoot.modPath.setLocked(False)
				guideRoot.modPath.set(existingBtns[guideRoot.modType.get()].path)
				guideRoot.modPath.setLocked(True)
				fixed = True
		else:
			mnsLog.log("Didn't find module '" + guideRoot.nodeName() + "'. Please check your block version, consult your admin or consult us at MANSUR.", svr = 3)
	return fixed

def attemptModulePathFixFroRigTop(rigTop, existingBtns, **kwargs):
	"""
	Run through all existing rig component (in rigTop) and validate the module directories against all existing module directories.
	If a module path was found invalid, attempt to re-find it in the existing modules."""

	progressBar = kwargs.get("progressBar", None)
	progBarStartValue = kwargs.get("progBarStartValue", 0.0)
	progBarChunk = kwargs.get("progBarChunk", 20.0)

	if rigTop:
		allGuides = getAllGuideRootsForRigTop(rigTop)
		fixedOne = False

		for k, guideRoot in enumerate(allGuides):
			status = attemptModulePathFixForRootGuide(guideRoot, existingBtns)
			if status and not fixedOne: fixedOne = True

			if progressBar: 
				progBarValue = progBarStartValue + (progBarChunk / len(allGuides) * float(k +1))
				progressBar.setValue(progBarValue)
		if not fixedOne:
			mnsLog.log("All existing modules within the selected rig are valid.", svr = 1)

def missingModuleActionTrigger(rigTop, missingModuleName, existingBtns):
	"""Action trigger for an invalid module path fix attempt
	"""

	mnsLog.log("The module '" + missingModuleName + "' is missing. Attempting a guide fix with current module directories", svr = 3)
	attemptModulePathFixFroRigTop(rigTop, existingBtns)

def preCheckNameForUI(arguments, suffix):
	"""A simple method to check for argument duplicates within an argument dict
	"""

	if arguments and suffix:
		kwargsDupTest = {}
		for arg in arguments: kwargsDupTest.update({arg.name: arg.default})
		if "characterName" in kwargsDupTest.keys(): kwargsDupTest["body"] = kwargsDupTest.pop("characterName")
		if "blkSide" in kwargsDupTest.keys(): 
			kwargsDupTest["side"] = kwargsDupTest.pop("blkSide")

		if "side" in kwargsDupTest.keys(): kwargsDupTest["side"] = mnsSidesDict[kwargsDupTest["side"]]

		kwargsDupTest.update({"suffix": suffix})
		testNameStd = MnsNameStd(**kwargsDupTest)
		defName = testNameStd.name
		testNameStd.findNextAlphaIncrement()

		if testNameStd.name != defName:
			for arg in arguments:
				if arg.name == "alpha": arg.default = testNameStd.alpha
				if arg.name == "id": arg.default = testNameStd.id

	#return;dict (recompiled arguments)
	return arguments

### settings ###
def filterCreationOnlyFromArgs(argsList):
	"""A simple method to filter out the "creationOnly" flag for an argument.
	   This method is called on a dynamicUI creation call if it NOT a "new creation" mode in BLOCK.
	   In case any arguments within the list passed in is flagged as "creationOnly", it is removed from the list"""

	if argsList:
		toRemove = []
		for a in argsList: 
			if a.blockCreationOnly: toRemove.append(a)
		
		for a in toRemove: 
			argsList.remove(a)

	#return;list (filtered arguments)
	return argsList

def getSettings(settingsPath, node, blkType):
	"""Get setting for the requested setting path.
	   The settings are being filtered and set according to a node passed in."""

	node = mnsUtils.validateNameStd(node).node
	optArgsFromFile = None
	sidePlaceHolder = "center"

	if node:
		if node.hasAttr("blkClassID"):
			if node.getAttr("blkClassID") ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, blkType): 
				pm.select(node, r = 1)	
				optArgsFromFile = mnsUtils.readSetteingFromFile(settingsPath)
				optArgsFromFile, sidePlaceHolder = filterSettings(optArgsFromFile, node)
			else: mnsLog.log("Top parent isn't a blkRigTop object. Aborting.", svr = 1)
		else: mnsLog.log("Top parent doesn't have a blkClassID. Aborting.", svr = 1)
	else:
		mnsLog.log("No selection. Aborting", svr = 1)

	#return;list (optionalArgumentsFromFile), string (current side place holder)
	return optArgsFromFile, sidePlaceHolder

def filterSettings(fileSettings, node):
	"""Filter all pre-defined settings to their corresponding gathering methods, and re-collect
	"""

	sidePlaceHolder = "center"
	customAttrs = pm.listAttr(node, ud = 1)
	for arg in fileSettings:
		if arg.name in customAttrs:
			if  "side".lower() in arg.name.lower(): sidePlaceHolder = arg.default
			if "colorScheme".lower() in arg.name.lower() or "schemeOverride".lower() in arg.name.lower():
				values = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList(arg.name, node)
				arg.default = values
			elif "channelControl".lower() in arg.name.lower():
				returnDict = mnsUtils.splitEnumAttrToChannelControlList(arg.name, node)
				arg.default = returnDict
			elif arg.name.lower() == "spaces" or arg.multiRowList:
				retList = mnsUtils.splitEnumToStringList(arg.name, node)
				arg.default = retList
			else:
				arg.default = node.attr(arg.name).get()

	#return;list (settings), string (current side place holder)
	return fileSettings, sidePlaceHolder

def getRigTopAssemblies():
	rigTops = {}
	assemblies = pm.ls(assemblies = True)
	for assembly in assemblies:
		try:
			assembly = mnsUtils.validateNameStd(assembly)
			if assembly: 
				status, blkClassID = mnsUtils.validateAttrAndGet(assembly, "blkClassID", None)
				if blkClassID and blkClassID == "rigTop":
					if assembly.namespace: rigTops[assembly.namespace + ":" + assembly.body] = assembly
					else: rigTops[assembly.body] = assembly
		except:	pass
	return rigTops

### scriped buildes ###
def gatherMnsRigObject():
	"""This method will gather an MnsRig class object based on the passed in input, in order to use all of it's methods.
	If you need to run any method from MnsRig class, use this method to gather the class object, the run any internal method within.
	"""

	blockWin = None
	windowName = "mnsBLOCK_UI"
	mnsUIUtils.reloadWindow(windowName)

	from .. import blockBuildUI as blockBuildUI
	blockWin = blockBuildUI.MnsBlockBuildUI()

	if blockWin:
		from . import buildModules as mnsBuildModules

		MnsRig = mnsBuildModules.MnsRig(execInit = False, buildModulesBtns = blockWin.buildModulesBtns)
		return MnsRig
	else:
		mnsLog.log("Something went wrong- couldn't find Block. Please contact support at support@mansur-rig.com")

def collectPartialModules(fromNodes = [], mode = 0):
	"""This method will collect module root objects based on the input data.
	If you need to run MnsRig class internal methods, which can operate on partial modules as well as the entire rig, use this method to collect the partial data to be passed into MnsRig class methods.
	In case fromNodes argument is Null, this method will return data based on the current scene selection.
	"""

	fromNodes = fromNodes or pm.ls(sl=True)
	if not type(fromNodes) is list: fromNodes = [fromNodes]

	if fromNodes:
		newSelection = []
		for nodeName in fromNodes:
			pyNode = mnsUtils.checkIfObjExistsAndSet(nodeName)
			if pyNode: newSelection.append(pyNode)

		if newSelection:
			pm.select(newSelection, r = True)

			partialModules = []
			if mode != 0:
				mnsLog.log("Collecting partial modules.", svr = 0)
				partialModules = collectPartialModulesRoots(mode)
				return partialModules
		else:
			mnsLog.log("Couldn't find items to build from. Aborting.", svr = 2)
	else:
		mnsLog.log("Couldn't find items/selection to build from.  Aborting.", svr = 2)

def constructRig(fromNodes = [], mode = 0):
	"""API style scripted construction method. 
	If you wish to construct a rig from an external command instead of Block's UI, use this method.
	You can pass in a fromNodes argument to specify the rig you wish to construct.
	In case the fromNodes argument isn't valid, the construction will be selection based.
	Also, use the mode argument to specify which mode you wish to construct in:
	mode 0 = ALL
	mode 1 = Branch
	mode 2 = Module

	fromNodes is a list argument. 
	In case any input is passed, this method will attempt to aquire the modules to construct based on the mode selected.
	You can pass in any Block-Node names into this method.
	"""

	MnsRig = gatherMnsRigObject()
	partialModules = collectPartialModules(fromNodes = fromNodes, mode = mode)
	MnsRig.constructRig(partialModules = partialModules)

def deconstructRig(fromNodes = [], mode = 0):
	"""API style scripted deconstruction method. 
	If you wish to construct a rig from an external command instead of Bloxk's UI, use this method.
	You can pass in a fromNodes argument to specify the rig you wish to construct.
	In case the fromNodes argument isn't valid, the deconstruction will be selection based.
	Also, use the mode argument to specify which mode you wish to construct in:
	mode 0 = ALL
	mode 1 = Branch
	mode 2 = Module

	fromNodes is a list argument. 
	In case any input is passed, this method will attempt to aquire the modules to construct based on the mode selected.
	You can pass in any Block-Node names into this method.
	"""

	MnsRig = gatherMnsRigObject()
	partialModules = collectPartialModules(fromNodes = fromNodes, mode = mode)
	MnsRig.deconstructRig(partialModules = partialModules)

###############################
###### rigTop #################
###############################

def getRigTop(objectA):
	"""Attempt to get a rigTop node from the passed in node to check.
	"""

	objectA = mnsUtils.checkIfObjExistsAndSet(objectA)
	if objectA:
		_rigTop = None
		firstLevelParent = mnsUtils.getFirstLevelParentForObject(objectA)
		status, blkClassID = mnsUtils.validateAttrAndGet(firstLevelParent, "blkClassID", None)
		if firstLevelParent.hasAttr("blkClassID"):
			if blkClassID and blkClassID == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop): 
				_rigTop = mnsUtils.validateNameStd(firstLevelParent)

		if not _rigTop: mnsLog.log("Couldn't find rig top for selection.", svr = 2)

		#return;MnsNameStd (rigTop)
		return _rigTop

def getRigTopForSel(**kwargs):
	"""Attempt to get a rigTop node from current selection
	"""

	mnsLog.log("Searching for rig-top from selection.")

	constructionState = kwargs.get("getConstructionState", False)

	_rigTop = None
	currentSelection = None
	try: currentSelection = pm.ls(sl = 1)[0]
	except: mnsLog.log("No Selection.")
	if currentSelection: _rigTop = getRigTop(currentSelection)

	if _rigTop: mnsLog.log("Found Rig-Top - \'" + _rigTop.name + "\'.")

	if constructionState:
		return _rigTop, getConstructionState(_rigTop)
	else:
		#return;MnsNameStd (rigTop)
		return _rigTop

def getConstructionState(rigTop = None):
	returnState = False

	rigTop = mnsUtils.validateNameStd(rigTop)
	if rigTop:
		puppetRoot = getPuppetRootFromRigTop(rigTop)
		if puppetRoot:
			returnState = True

	return returnState

def getAllGuideRootsForRigTop(rigTop):
	"""Gather all guide roots for the passed in rigTop node.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)

	ad = pm.listRelatives(rigTop.node, ad = 1, type = pm.nt.Transform)
	returnGuides = []
	for c in ad:
		if c.nodeName().endswith("_rCtrl"): returnGuides.append(c)

	#return;list (rootGuides)
	return returnGuides

def getRootGuideFromRigTop(rigTop = None):
	"""Attempt to collect the rig's root guide from the passed in rigTop node
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	if rigTop: 
		#return;MnsNameStd (rig root guide)
		return mnsUtils.validateNameStd(rigTop.node.rigRootGuide.get())

def getAllPlgsForRigTop(rigTop):
	"""Collect all 'picker layout guides' from the rig passed in (as rigTop)
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	pickerGuideGrp = getPickerGuidesGrpFromRigTop(rigTop)
	ad = pm.listRelatives(pickerGuideGrp.node, ad = 1, type = pm.nt.Transform)
	returnGuides = []
	for c in ad:
		if c.nodeName().endswith("_" + mnsPS_plg): returnGuides.append(c)

	#return;list (All PLGs)
	return returnGuides

def getAllcolCtrlforRigTop(rigTop):
	"""Collect all 'color associated' nodes within the passed in rigTop.
	   All returned nodes are considered 'color associated', meaning they are nodes that all of their shapes need to be directly colored."""

	rigTop = mnsUtils.validateNameStd(rigTop)

	ad = pm.listRelatives(rigTop.node, ad = 1, type = pm.nt.Transform)
	returnGuides = []
	for c in ad:
		if c.nodeName().endswith("_rCtrl") or c.nodeName().endswith("_gCtrl") or c.nodeName().endswith("_cgCtrl"):
			returnGuides.append(c)

	#return;list (colorControls)
	return returnGuides

def getPuppetBaseFromRigTop(rigTop = None):
	"""Attempt to collect the 'puppet group' from the passed in rigTop.
	"""

	objectSel = mnsUtils.validateNameStd(rigTop).node
	
	ret = None
	if objectSel:
		if objectSel.hasAttr("blkClassID"):
			if objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop):
				if objectSel.hasAttr("puppetGrp"):
					ret = objectSel.attr("puppetGrp").get()

	#return;MnsNameStd (puppet base)
	return mnsUtils.validateNameStd(ret)

def getCsGrpFromRigTop(rigTop = None):
	"""Attempt to collect the 'Control Shapes Group' from the passed in rigTop.
	"""

	objectSel = mnsUtils.validateNameStd(rigTop).node
	
	ret = None
	if objectSel:
		if objectSel.hasAttr("blkClassID"):
			if objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop):
				if objectSel.hasAttr("controlShapesGrp"):
					ret = objectSel.attr("controlShapesGrp").get()

	#return;MnsNameStd (ctrlShapes group)
	return mnsUtils.validateNameStd(ret)

def getPuppetRootFromRigTop(rigTop = None):
	"""Attempt to collect the 'Puppet World Control' from the passed in rigTop.
	"""

	objectSel = mnsUtils.validateNameStd(rigTop)

	if objectSel:
		objectSel = objectSel.node
		ret = None
		if objectSel:
			if objectSel.hasAttr("blkClassID"):
				if objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop):
					if objectSel.hasAttr("puppetRoot"):
						ret = objectSel.attr("puppetRoot").get()
		#return;MnsNameStd (Puppet world control)
		return mnsUtils.validateNameStd(ret)
	else: return None

def locatePLGBaseVisMdNodes(baseLayoutGuide = None):
	bodyMDNode, facialMDNode = None, None

	baseLayoutGuide = mnsUtils.validateNameStd(baseLayoutGuide)
	if baseLayoutGuide:
		baseLayout = baseLayoutGuide.node

		originAttr = baseLayout.attr("bodyPrimaries")
		outConnections = originAttr.listConnections(s = True)
		if outConnections:
			mdNode = None
			nextNode = outConnections[0]
			if type(nextNode) == pm.nodetypes.MultiplyDivide: bodyMDNode = mnsUtils.validateNameStd(nextNode)

		originAttr = baseLayout.attr("facialPrimaries")
		outConnections = originAttr.listConnections(s = True)
		if outConnections:
			mdNode = None
			nextNode = outConnections[0]
			if type(nextNode) == pm.nodetypes.MultiplyDivide: facialMDNode = mnsUtils.validateNameStd(nextNode)

		if not bodyMDNode:
			revNode = mnsNodes.reverseNode([baseLayout.pickerMode, baseLayout.pickerMode, baseLayout.pickerMode])
			bodyMDNode = mnsNodes.mdNode([baseLayout.bodyPrimaries, baseLayout.bodySecondaries, baseLayout.bodyTertiaries], revNode.node.output, body = "bodyPlgVis")
			connectSlaveToDeleteMaster(bodyMDNode, baseLayoutGuide)

		if not facialMDNode:
			facialMDNode = mnsNodes.mdNode([baseLayout.pickerMode, baseLayout.pickerMode, baseLayout.pickerMode], [baseLayout.facialPrimaries, baseLayout.facialSecondaries, baseLayout.facialTertiaries], body = "facialPlgVis")
			connectSlaveToDeleteMaster(facialMDNode, baseLayoutGuide)

	#return; MnsNameStd (bodyMdNode), MnsNameStd (facialMDNode)
	return bodyMDNode, facialMDNode

def createPlgBaseVisChannels(baseLayoutGuide = None):
	baseLayoutGuide = mnsUtils.validateNameStd(baseLayoutGuide)
	if baseLayoutGuide:
		for attrName in ["bodyPrimaries", "bodySecondaries", "bodyTertiaries", "facialPrimaries", "facialSecondaries", "facialTertiaries"]:
			mnsUtils.addAttrToObj([baseLayoutGuide.node], type = "bool", value = True, name = attrName, replace = False)
		mnsUtils.addAttrToObj([baseLayoutGuide.node], type = "enum", value = ["Body", "Facial"], name = "pickerMode", replace = False)

		#locate vis md nodes
		bodyMDNode, facialMDNode = locatePLGBaseVisMdNodes(baseLayoutGuide)
		
def getPickerLayoutBaseFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Layout Base guide' from the passed in rigTop.
	"""

	objectSel = mnsUtils.validateNameStd(rigTop).node
	
	ret = None
	if objectSel:
		if objectSel.hasAttr("blkClassID"):
			if objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop):
				if objectSel.hasAttr("pickerLayoutBase"):
					ret = objectSel.attr("pickerLayoutBase").get()

	#return;MnsNameStd (Picker Layout Base guide)
	return mnsUtils.validateNameStd(ret)

def getPickerLayoutCamFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Layout Camera' from the passed in rigTop.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	
	ret = None
	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop).node
		if rigTop.hasAttr("blkClassID"):
			if rigTop.hasAttr("pickerLayoutCam"):
				ret = rigTop.attr("pickerLayoutCam").get()

	#return;MnsNameStd (Picker Layout Base guide)
	return mnsUtils.validateNameStd(ret)

def getPickerProjectionCamFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Projection Camera' from the passed in rigTop.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	
	ret = None
	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop).node
		if rigTop.hasAttr("blkClassID"):
			if rigTop.hasAttr("pickerProjectionCam"):
				ret = rigTop.attr("pickerProjectionCam").get()

	#return;MnsNameStd (Picker Projection Camera)
	return mnsUtils.validateNameStd(ret)

def getPickerGuidesGrpFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Guide Group' from the passed in rigTop.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	ret = None
	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop).node
		if rigTop.hasAttr("blkClassID"):
			if rigTop.hasAttr("pickerGuidesGrp"):
				ret = rigTop.attr("pickerGuidesGrp").get()

	#return;MnsNameStd (Picker Guide Group)
	return mnsUtils.validateNameStd(ret)

def getPickerTitleGrpFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Title Group' from the passed in rigTop.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	ret = None
	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop).node
		if rigTop.hasAttr("blkClassID"):
			if rigTop.hasAttr("pickerTitleGrp"):
				ret = rigTop.attr("pickerTitleGrp").get()
	
	#return;MnsNameStd (Picker Title Group))				
	return mnsUtils.validateNameStd(ret)

def getOffsetSkeletonGrpFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Title Group' from the passed in rigTop.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	ret = None
	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop).node
		if rigTop.hasAttr("blkClassID"):
			if rigTop.hasAttr("offsetSkeletonGrp"):
				ret = rigTop.attr("offsetSkeletonGrp").get()
	
	#return;MnsNameStd (Offset Skeleton Grp)				
	return mnsUtils.validateNameStd(ret)

def getJointStructGrpFromRigTop(rigTop = None):
	"""Attempt to collect the 'Picker Title Group' from the passed in rigTop.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	ret = None
	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop).node
		if rigTop.hasAttr("blkClassID"):
			if rigTop.hasAttr("jointStructGrp"):
				ret = rigTop.attr("jointStructGrp").get()
	
	#return;MnsNameStd (Offset Skeleton Grp)				
	return mnsUtils.validateNameStd(ret)

def findNamingIssuesInHierarchy():
	faultyNodes = []
	validSuffixes = [mnsTypeDict[key].suffix for key in mnsTypeDict.keys()]

	sel = pm.ls(sl=True)
	if sel:
		for s in sel:
			for tran in s.listRelatives(ad = True, type = "transform"):
				nStd = mnsUtils.validateNameStd(tran)
				if not nStd or not nStd.suffix in validSuffixes:
					faultyNodes.append(tran)
	if faultyNodes: 
		pm.select(faultyNodes, r = True)
		mnsLog.log("Naming issues search complete. Invalid names found (selected).", svr = 2)
	else:
		mnsLog.log("Naming issues search complete. All names are valid.", svr = 1)

def collectPartialModulesRoots(mode):
	"""This method will be called in case a partial build was requested.
	Using methods within 'blockUtility', this method will collect the requested modules to build based on the UI state.
	"""

	partialRoots = []

	if len(pm.ls(sl=1)) > 0:
		for obj in pm.ls(sl=1):
			obj = mnsUtils.validateNameStd(obj)
			guideRoot = mnsUtils.validateNameStd(getModuleRoot(obj))

			if guideRoot:
				rigTop = getRigTop(guideRoot.node)
				baseGuide = getRootGuideFromRigTop(rigTop)

				if baseGuide.node != guideRoot.node:
					if not guideRoot.name in partialRoots: partialRoots.append(guideRoot.name)
					if mode == 1:
						partialRoots += [obj.nodeName() for obj in guideRoot.node.listRelatives(ad = True) if obj.hasAttr("blkClassID") and obj.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl) and obj != baseGuide.node and obj.nodeName() not in partialRoots]
	
	#return; list (root guides (modules) to build)
	return partialRoots

###############################
###### module Hierarchy #######
###############################

def updateRigStructure(softMod = False, **kwargs):
	"""Rig structure update required trigger.
	This method will be called in case any 'jntStructMember' attribute was altered, which means the internal joint structure of the module needs to be rebuilt.
	This method will locate and filter the existing module related joint structure, destroy it, and re-build it using the updated settings. 
	"""

	settingsHolder = kwargs.get("settingsHolder", None)
	if settingsHolder:
		rigTop = kwargs.get("rigTop", None)
		if not rigTop:
			rigTop = getRigTop(settingsHolder.node)

		mnsLog.logCurrentFrame()
		if not softMod:
			jntStructModule = getModuleFromGuide(settingsHolder)
				
			if jntStructModule: 
				builtGuides = getModuleGuideDecendents(settingsHolder)
				deleteFreeJntGrpForModule(builtGuides[0])
				interpLocs = jntStructModule.jointStructure(mansur, builtGuides, **kwargs)
				handleInterpLocsStructureReturn(rigTop, interpLocs, builtGuides)
		else:
			jntStructModule = getModuleFromGuide(settingsHolder, methodName = "jointStructureSoftMod")
			if jntStructModule: 
				builtGuides = getModuleGuideDecendents(settingsHolder)
				jntStructModule.jointStructureSoftMod(mansur, builtGuides, **kwargs)

def rebuildJointStructure(mode = 0):
	"""
	modes:
	0 = All
	1 = Branch
	2 = Module
	"""

	rigTop, constructed = getRigTopForSel(getConstructionState = True)
	if rigTop:
		if not constructed:
			rootGuide = getRootGuideFromRigTop(rigTop)
			if rootGuide:
				rootGuides = []
				if mode == 0:
					rootGuides = [mnsUtils.validateNameStd(obj) for obj in rootGuide.node.listRelatives(ad = True, type = "transform") if obj.hasAttr("blkClassID") and obj.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl) and obj != rootGuide.node]
				else:
					rootGuides = [mnsUtils.validateNameStd(r) for r in collectPartialModulesRoots(mode)]

				if rootGuides:
					buildModulesText = ""
					for bmName in [rootG.side + "_" + rootG.body + "_" + rootG.alpha for rootG in rootGuides]:
						if not buildModulesText:
							buildModulesText = bmName
						else:
							buildModulesText += ", " + bmName

					reply = QtWidgets.QMessageBox.question(mnsUIUtils.get_maya_window(), 'Joint-Structure rebuild', "<b>Are you sure you want to rebuild the joint structure for the following modules?<br>(this cannot be undone)</b><br>" + buildModulesText, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
					if reply == QtWidgets.QMessageBox.Yes:
						for rootG in rootGuides:
							status, isConstructed = mnsUtils.validateAttrAndGet(rootG, "constructed", False)
							if not isConstructed:
								updateRigStructure(False, settingsHolder = rootG, rigTop = rigTop)
							else:
								mnsLog.log(rootG.side + "_" + rootG.body + "_" + rootG.alpha + " - Cannot re-build joint-structure in constructed state.", svr = 2)
						mnsLog.log("Joint structures updated successfully.", svr = 1)
				else:
					mnsLog.log("Couldn't find guides to rebuild for. Aborting.", svr = 2)
			else:
				mnsLog.log("Couldn't find Root-Guide. Aborting.", svr = 2)
		else:
			mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
	else:
		mnsLog.log("Couldn't find Rig-Top. Aborting.", svr = 2)

def searchForRootGuideInRelatives(obj):
	"""Search for a 'guide authority' or 'rootGuide' in the given node's decendents
	"""

	obj = mnsUtils.validateNameStd(obj)
	if obj:
		for cNode in obj.node.listRelatives(ad = True, type ="transform"):
			if cNode.hasAttr("guideAuthority") and cNode.guideAuthority.get():
				guideAuth = mnsUtils.validateNameStd(cNode.guideAuthority.get())
				if guideAuth:
					rootGuide = getModuleRoot(guideAuth)
					if rootGuide: 

						#return;PyNode (rootGuide)
						return rootGuide
						break

def recSearchForGuideRootInParents(obj):
	"""Recusrsivly look for a 'rootGuide' from the given node's parent relatives.
	"""

	obj = mnsUtils.validateNameStd(obj)
	if obj:
		if obj.node.hasAttr("blkClassID") and obj.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl):
			return obj
		else: 
			return recSearchForGuideRootInParents(obj.node.getParent())
	#return; PyNode (rootGuide)

def getModuleRoot(objectA):
	"""Attempt to collect the root guide relative from the given node.
	"""

	moduleRoot = None
	if objectA:
		objectA = mnsUtils.validateNameStd(objectA)
		if objectA:
			if objectA.node.hasAttr("blkClassID"):
				if objectA.node.blkClassID.get() ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_cgCtrl):
					return recSearchForGuideRootInParents(objectA)
				elif objectA.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl):
					return objectA
				elif objectA.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_plg):
					guideParent = getDeleteMasterFromSlave(objectA)
					return getModuleRoot(guideParent)
				elif objectA.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_ctrl):
					return getRootGuideFromCtrl(objectA)
				elif objectA.node.getParent():
					return getModuleRoot(objectA.node.getParent())
				elif objectA.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop):
					if objectA.node.hasAttr("rigRootGuide"):
						guide = objectA.node.attr("rigRootGuide").get()
						if guide: return objectA.node.attr("rigRootGuide").get()
						else:
							mnsLog.log("Couldn't find a valid root guide for selection. Aborting.", svr = 2)
							return None
					else:
						mnsLog.log("Couldn't find a valid root guide for selection. Aborting.", svr = 2)
						return None
				else: 
					mnsLog.log("Something went wrong, couldn't find a parent root guide nor a rigTop. Please check your guide hirarchy.", svr = 3)
					return None
			else:
				mnsLog.log("Selection is not valid. Cannot load settings", svr = 0)
				return None
		else:
			mnsLog.log("Selection is not valid. Cannot load settings", svr = 0)
			return None

	#return;PyNode (rootGuide)

def getModuleRootForSel():
	"""Attempt to collect a 'root guide' relative from the current selection
	"""

	moduleRoot = None
	sel = pm.ls(sl = 1)
	if sel: moduleRoot = getModuleRoot(sel[0])
	else:
		mnsLog.log("No Selection. Aborting.", svr = 1)
		moduleRoot = None

	#return;PyNode (moduleRoot)
	return moduleRoot

def getChildModules(rootGuide):
	"""Recusrsivly collect all child modules from the given rootGuide's decendents.
	"""

	rootGuide = mnsUtils.validateNameStd(rootGuide)

	#return;list (module decendents)
	return [mnsUtils.validateNameStd(c) for c in pm.listRelatives(rootGuide.node, ad = True, type = "transform")  if mnsPS_gRootCtrl in c.nodeName()]

def getPyModuleFromGuide(guide):
	"""Attempt to collect a 'Python Module' (or package) related to the given guide node passed in.
	If a related module was found, this method will return it as a PyModule object not as a directory.
	This method will also return the module's methods in a dictionary in order to run directly from it."""

	if guide:
		mnsLog.logCurrentFrame()

		guideRoot = mnsUtils.validateNameStd(getModuleRoot(guide))
		if guideRoot:
			guideRoot = getModuleRoot(guideRoot)
			if guideRoot:
				modPath, modName = None, None
				if guideRoot.node.hasAttr("modPath"): modPath = guideRoot.node.attr("modPath").get()
				if guideRoot.node.hasAttr("modType"): modName = guideRoot.node.attr("modType").get()

				if modPath and modName:
					#get jntStrcut from module
					moduleFilePath = modPath + "/" + modName + ".py"
					if os.path.isfile(moduleFilePath):
						pyModule = None
						pyModule = imp.load_source(modName, moduleFilePath)

						methods = {}
						[methods.update({o[0]: o[1]}) for o in getmembers(pyModule) if isfunction(o[1])]
						
						return pyModule, methods
	#return;PyModule, dict (module methods as keys and method objects as entries)
	return None, []

def getModuleFromGuide(guideRoot, **kwargs):
	"""This method will attempt to collect a related PyModule from the given guideRoot passed in.
	This method will not return the module's methods, only the PyModule as an object.
	This method also contains override optional arguments to specify a direct path or module name."""

	mnsLog.logCurrentFrame()
	methodName = kwargs.get("methodName", "jointStructure") #arg;

	modPath =  kwargs.get("modPath", None) #arg;
	modName = kwargs.get("modName", None) #arg;

	moduleReturn = None

	guideRoot = mnsUtils.validateNameStd(guideRoot)
	if guideRoot:
		guideRoot = getModuleRoot(guideRoot)
		if guideRoot:
			if not modPath and guideRoot.node.hasAttr("modPath"): modPath = guideRoot.node.attr("modPath").get()
			if not modName and guideRoot.node.hasAttr("modType"): modName = guideRoot.node.attr("modType").get()

			if modPath and modName:
				#get jntStrcut from module
				moduleFilePath = modPath + "/" + modName + ".py"
				if os.path.isfile(moduleFilePath):
					pyModule = imp.load_source('module', moduleFilePath)
					methodListNames = [o[0] for o in getmembers(pyModule) if isfunction(o[1])]
					if methodName in methodListNames:
						moduleReturn = pyModule
	#return;PyModule (object)
	return moduleReturn

def collectSlavesFromNdr(ndrNode):
	"""Collect all slaves related to the passed in 'mnsNodeRelationship' node.
	"""

	returnSlaves = []
	ndrNode = mnsUtils.validateNameStd(ndrNode)
	if ndrNode:
		if ndrNode.node.nodeType() == "mnsNodeRelationship":
			returnSlaves = ndrNode.node.listConnections(s = True)

	#return;list (slave nodes)
	return returnSlaves

def connectSlaveToDeleteMaster(slave, master):
	"""Connect the passed in 'slave' node to the passed in 'master' node using 'mnsNodeRelationship'.
	This method will be successfull only if the master already has a related 'mnsNodeRelationship' node."""

	slave = mnsUtils.validateNameStd(slave)
	master = mnsUtils.validateNameStd(master)
	ndr = getNodeRelationshipNodeFromObject(master)
	if ndr:
		if not slave.node.hasAttr("deleteMaster"):
			attr = mnsUtils.addAttrToObj([slave.node], type = "message", name = "deleteMaster", value= "", replace = True)[0]
		ndr.deleteSlaves >> slave.node.attr("deleteMaster")

def getDeleteMasterFromSlave(slave):
	"""Collect the delete master from a slave's related 'mnsNodeRelationship' node, if there is one.
	   This method will collect the master connected to the 'deleteMaster' attribute of the node."""

	slave = mnsUtils.validateNameStd(slave)
	status, deleteMaster = mnsUtils.validateAttrAndGet(slave, "deleteMaster", None)
	if deleteMaster:
		if deleteMaster.nodeType() == "mnsNodeRelationship":
			#return;MnsNameStd (master)
			return mnsUtils.validateNameStd(slave.node.attr("deleteMaster").get().attr("messageIn").get())

def disconnectSlaveFromMaster(slave):
	"""Disconnect the slave passed in from it's master, if there is one.
	"""

	slave = mnsUtils.validateNameStd(slave)
	if slave:
		delMaster = getDeleteMasterFromSlave(slave)
		if delMaster: slave.node.deleteMaster.disconnect()

def getRelationMasterFromSlave(slave):
	"""Collect the delete master from a slave's related 'mnsNodeRelationship' node, if there is one.
	   This method will collect the master connected to the 'masterIn' attribute of the node."""

	slave = mnsUtils.validateNameStd(slave)
	if slave.node.hasAttr("masterIn"):
		if slave.node.attr("masterIn").get():
			if slave.node.attr("masterIn").get().nodeType() == "mnsNodeRelationship":
				#return;MnsNameStd (master)
				return mnsUtils.validateNameStd(slave.node.attr("masterIn").get().attr("messageIn").get())

def removeAlienMatchesFromList(guideRoot, currentMatches = []):
	if currentMatches and guideRoot and type(guideRoot) == MnsNameStd:
		#remove alien matches
		alienBodyPattern = guideRoot.side + "_" + guideRoot.body + "*_" + guideRoot.alpha + "*_" + mnsPS_gRootCtrl 
		alienBodyMatches = pm.ls(alienBodyPattern, transforms = True)
		for alienM in alienBodyMatches:
			if alienM != guideRoot.node:
				alienGuideRoot = mnsUtils.validateNameStd(alienM)
				if alienGuideRoot:
					dropMatchesPattern = guideRoot.side + "_" + alienGuideRoot.body + "*_" + guideRoot.alpha + "*"
					dropMatches = pm.ls(dropMatchesPattern, transforms = True)
					currentMatches = [x for x in currentMatches if x not in dropMatches]
	return currentMatches

def getModuleGuideDecendents(guideRoot):
	"""Collect all of the root guide module relatives for the passed in moduleRoot (or rootGuide).
	"""

	guideRoot = mnsUtils.validateNameStd(guideRoot)
	if guideRoot:
		moduleDecendents =[f.nodeName() for f in pm.listRelatives(guideRoot.node, ad = True)]
		pattern = guideRoot.side + "_" + guideRoot.body + "*_" + guideRoot.alpha + "*_" + mnsPS_gCtrl
		deced = fnmatch.filter(moduleDecendents, pattern)
		deced = removeAlienMatchesFromList(guideRoot, deced)

		decendetsCompile = [guideRoot] + [mnsUtils.validateNameStd(c) for c in deced]

		#return;list (sorted by ID module decendents)
		return mnsUtils.sortNameStdArrayByID(decendetsCompile)
	else: return None 

def getCtrlShapesForModueRoot(guideRoot):
	guideRoot = mnsUtils.validateNameStd(guideRoot)
	if guideRoot:
		cShapes = getModuleDecendentsWildcard(guideRoot, getJoints = False, getInterpLocs = False, getInterpJnts = False,
												getGuides = False, getRootGuide = False, getCustomGuides = False,
												getCtrls = False, getFreeJntGrp = False, getCs = True)
		return cShapes

def getCtrlsFromModuleRoot(guideRoot):
	if guideRoot:
		ctrls = getModuleDecendentsWildcard(guideRoot, getJoints = False, getInterpLocs = False, getInterpJnts = False,
											getGuides = False, getRootGuide = False, getCustomGuides = False, getFreeJntGrp = False)
		return ctrls

def getRootJointsFromModuleRoot(guideRoot):
	if guideRoot:
		joints = getModuleDecendentsWildcard(guideRoot, getInterpLocs = False, getInterpJnts = False, getExactMatch = True,
											getGuides = False, getCtrls = False, getRootGuide = False, getCustomGuides = False, getFreeJntGrp = False)
		return joints

def getModuleDecendentsWildcard(guideRoot, **kwargs):
	"""Collect all given module dendents using a 'wild-card' search method.
	   This will collect all relatives using a * search within the root decendents, and return all of the passed in node types."""

	getAll = kwargs.get("getAll", False) #arg
	getJoints = kwargs.get("getJoints", True) #arg
	getInterpLocs = kwargs.get("getInterpLocs", True) #arg
	getInterpJnts = kwargs.get("getInterpJnts", True) #arg
	getVJnts = kwargs.get("getVJnts", False) #arg
	getGuides = kwargs.get("getGuides", True) #arg
	getRootGuide = kwargs.get("getRootGuide", True) #arg
	getCustomGuides = kwargs.get("getCustomGuides", True) #arg
	getCtrls = kwargs.get("getCtrls", True) #arg
	getTechCtrls = kwargs.get("getTechCtrls", getCtrls) #arg
	getFreeJntGrp = kwargs.get("getFreeJntGrp", True) #arg
	getPLGs = kwargs.get("getPLGs", False) #arg
	getCs = kwargs.get("getCs", False) #arg
	plgsOnly = kwargs.get("plgsOnly", False) #arg
	customGuidesOnly = kwargs.get("customGuidesOnly", False) #arg
	getExactMatch = kwargs.get("getExactMatch", False) #arg
	guidesOnly = kwargs.get("guidesOnly", False) #arg
	interpJntsOnly = kwargs.get("interpJntsOnly", False) #arg

	if plgsOnly:
		getPLGs = True
		getJoints, getInterpLocs, getInterpJnts, getGuides, getRootGuide, getCustomGuides, getFreeJntGrp = False, False, False, False, False, False, False

	if customGuidesOnly:
		getCustomGuides = True
		getJoints, getInterpLocs, getInterpJnts, getGuides, getRootGuide, getCtrls, getFreeJntGrp, getTechCtrls = False, False, False, False, False, False, False, False

	if guidesOnly:
		getGuides = True
		getJoints, getInterpLocs, getInterpJnts, getCtrls, getTechCtrls, getFreeJntGrp = False, False, False, False, False, False

	if interpJntsOnly:
		getInterpJnts = True
		getJoints, getInterpLocs, getCtrls, getTechCtrls, getFreeJntGrp, getCustomGuides, getGuides, getRootGuide = False, False, False, False, False, False, False, False

	guideRoot = mnsUtils.validateNameStd(guideRoot)
	if guideRoot:
		searchPattern = guideRoot.side + "_" + guideRoot.body + "*_" + guideRoot.alpha + "*"
		if getExactMatch: searchPattern = guideRoot.side + "_" + guideRoot.body + "_" + guideRoot.alpha + "*"
		if guideRoot.namespace: searchPattern = guideRoot.namespace + ":" + searchPattern

		matches = []

		allMatches = pm.ls(searchPattern, transforms = True)
		allMatches = removeAlienMatchesFromList(guideRoot, allMatches)

		for m in allMatches:
			app = False
			suffix = m.nodeName().split("_")[-1]
			if getAll: app = True
			else:
				if getRootGuide:
					if suffix == mnsPS_gRootCtrl: app = True
				if getGuides:
					if suffix == mnsPS_gCtrl: app = True
				if getCustomGuides:
					if suffix == mnsPS_cgCtrl: app = True
				if getCtrls:
					if suffix == mnsPS_ctrl: app = True
				if getTechCtrls:
					if suffix == mnsPS_techCtrl: app = True
				if getPLGs:
					if suffix == mnsPS_plg: app = True
				if getInterpLocs:
					if suffix == mnsPS_iLoc: app = True
				if getFreeJntGrp:
					if suffix == mnsPS_freeJntsGrp: app = True
				if getCs:
					if suffix == mnsPS_ctrlShape: app = True
				if getJoints:
					if suffix == mnsPS_jnt or suffix  == mnsPS_rJnt: app = True
				if getInterpJnts:
					if suffix == mnsPS_iJnt: app = True
				if getVJnts:
					if suffix == mnsPS_vJnt: app = True
			if app:
				matches.append(m)

		matches = [mnsUtils.validateNameStd(c) for c in matches]

		#return;list (matching decendents)
		return matches

	else: return None 

def getModuleInterpJoints(guideRoot, **kwargs):
	"""Collect all the given moduleRoot's 'interpolationJoints' relatives.
	"""

	interpType = kwargs.get("interpType", mnsPS_iLoc)
	useSuffix = kwargs.get("useSuffix", GLOB_mnsJntStructDefaultSuffix)

	guideRoot = mnsUtils.validateNameStd(guideRoot)
	if guideRoot:
		searchPattern = guideRoot.side + "_" + guideRoot.body + useSuffix + "_" + guideRoot.alpha + "*_" + interpType
		matches = [mnsUtils.validateNameStd(c) for c in pm.ls(searchPattern)]

		#return;list (matching interJoints)
		return matches
	else: return None 

def getRelatedNodeFromObject(node):
	"""Collect a related node from the 'messageOut' attribute of the given node's 'mnsNodeRelationship' node.
	"""

	returnA = None
	node = mnsUtils.validateNameStd(node)

	if node:
		node = node.node
		if node.hasAttr("messageOut"):
			ndr = node.attr("messageOut").get()
			if ndr:
				ndr = mnsUtils.validateNameStd(ndr).node
				if ndr.hasAttr("messageOut"):
					returnA = ndr.attr("messageOut").get()

	#return;PyNode
	return returnA

def getNodeRelationshipNodeFromObject(node):
	"""Collect the related 'mnsNodeRelationship' node from the given input node.
	"""

	returnA = None
	node = mnsUtils.validateNameStd(node)

	if node:
		if node.node.hasAttr("messageOut"):
			ndr = node.node.attr("messageOut").get()
			if ndr:
				if ndr.nodeType() == "mnsNodeRelationship":
					returnA = ndr

		if not returnA:
			returnA = mnsNodes.mnsNodeRelationshipNode(side = node.side, alpha = node.alpha , id = node.id, body = node.body, master = node.node, slaves = [])
			if returnA: returnA = returnA.node

	#return;PyNode
	return returnA

def recGetParentJoint(rootObject = None):
	"""Recursivly attempt to get a parent joint starting with a given root object, scaling up the heirarchy.
	"""

	rootObject = mnsUtils.validateNameStd(rootObject)
	if rootObject:
		relatedRootJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(rootObject))
		if relatedRootJnt: return relatedRootJnt
		else:
			parentGuide = rootObject.node.getParent()
			if parentGuide:
				return recGetParentJoint(parentGuide)
			else:
				return None
	else:
		return None

	#return;mnsNameStd

def getGuideParent(objectSel = None):
	"""Collect a ctrl type object's 'Guide Authority', or related guide object.
	"""

	objectSel = mnsUtils.validateNameStd(objectSel)
	if objectSel:
		objectSel = objectSel.node
		if objectSel.hasAttr("blkClassID"):
			if objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl) or objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gCtrl):
				return objectSel
			else:
				if objectSel.getParent():
					return getGuideParent(objectSel.getParent())
				else:
					if objectSel.hasAttr("blkClassID"):
						if objectSel.attr("blkClassID").get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_rigTop):
							if objectSel.hasAttr("rigRootGuide"):
								if mnsUtils.checkIfObjExistsAndSet(obj = objectSel.attr("rigRootGuide").get()):
									return getRootGuideFromRigTop(objectSel)
								else: return None
							else: return None
						else: return None
					else: return None
		else: return None
	else: return None
	#return; PyNode

def collectGuides(roots = pm.ls(sl = 1), **kwargs):
	"""Based on the oprional arguments passed in, collect all matching related guides to the input root list.
	"""

	if roots:
		rigTop = kwargs.get("rigTop", None) #arg; 
		includeDecendents = kwargs.get("includeDecendents", False) #arg; 
		includeDecendentBranch = kwargs.get("includeDecendentBranch", False) #arg; 
		getGuides = kwargs.get("getGuides", True) #arg; 
		getCustomGuides = kwargs.get("getCustomGuides", True) #arg; 
		allAsSparse = kwargs.get("allAsSparse", False) #arg;

		rootsCollect = []
		guidesCollect = []
		customGuidesCollect = []

		if type(roots) is not list: roots = [roots]
		if len(roots) > 0:
			if not rigTop: rigTop = getRigTopForSel()
			if rigTop:
				if includeDecendentBranch:
					checkedChilds = []
					for obj in roots:
						obj = mnsUtils.validateNameStd(obj)
						if obj:
							children = obj.node.listRelatives(ad = True, type = "transform")[::-1]
							for child in children:
								if child not in checkedChilds:
									checkedChilds.append(child)
									child = mnsUtils.validateNameStd(child)
									if child and child.suffix == mnsPS_gRootCtrl and child.node not in roots: roots.append(child.node)					
				for obj in roots:
					obj = mnsUtils.validateNameStd(obj)
					if obj:
						if obj.node.hasAttr("blkClassID"):
							objClass = obj.node.blkClassID.get()
							if obj not in rootsCollect and objClass == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl): rootsCollect.append(obj)
							if obj not in guidesCollect and objClass == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gCtrl): guidesCollect.append(obj)
							if obj not in customGuidesCollect and objClass == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_cgCtrl): customGuidesCollect.append(obj)

		#collect to root dictionary
		parentedGuides = []
		sparseGuides = []
		arrangedDict = {}
		for root in rootsCollect:
			arrangedDict.update({root.name: [root, [], mnsUtils.validateNameStd(root.node.getParent()), []]})
			if allAsSparse: 
				if root.node not in [s.node for s in sparseGuides]: sparseGuides.append(root)
			if includeDecendents and (getGuides or getCustomGuides): 
				for c in getModuleDecendentsWildcard(root, guidesOnly = True, getGuides = getGuides, getCustomGuides = getCustomGuides): 
					arrangedDict[root.name][1].append(c)
					if allAsSparse: 
						if c.node not in [s.node for s in sparseGuides]: sparseGuides.append(c)
			else:
				decendents = [c.node for c in getModuleDecendentsWildcard(root, guidesOnly = True)]
				for guide in (guidesCollect + customGuidesCollect):
					if guide.node in decendents: 
						arrangedDict[root.name][1].append(guide)
						parentedGuides.append(guide)
					elif allAsSparse: 
						if guide.node not in [s.node for s in sparseGuides]:
							sparseGuides.append(guide)
		if not allAsSparse: sparseGuides = [g for g in (guidesCollect + customGuidesCollect) if g not in parentedGuides]
		if not rootsCollect and allAsSparse: sparseGuides = guidesCollect + customGuidesCollect

		#return;dict (Related guides), list (sparseGuides, guide without any relations)
		return arrangedDict, sparseGuides

def getSideModuleBranchRoot(guide = None):
	"""For a non "center" component passed in, recursively attempt to collect the 'side-branch' root guide.
	In essence look for the highest rootGuide in the selected 'side' heirarchy that has a 'center' component parent- meaning it's the top of the requested branch."""

	guide = mnsUtils.validateNameStd(guide)
	if guide:
		if guide.side != mnsPS_cen and guide.suffix == mnsPS_gRootCtrl and mnsUtils.validateNameStd(guide.node.getParent()).side == mnsPS_cen: return guide
		else: 
			#return;MnsNameStd (branch root)
			return getSideModuleBranchRoot(guide.node.getParent())

def orientGuides(guides = [], **kwargs):
	if guides:
		#gather inputs
		orientNativeOnly = kwargs.get("orientNativeOnly", True)
		skipEndGuides = kwargs.get("skipEndGuides", False)
		progressBar = kwargs.get("progressBar", None)

		aimAxis = kwargs.get("aimAxis", "x")
		flipAim = kwargs.get("flipAim", False)
		aimVector = [0,1,0]
		if aimAxis == "x": aimVector = [1,0,0]
		elif aimAxis == "z": aimVector = [0,0,1]
		if flipAim: aimVector = [aimVector[0] * -1, aimVector[1] * -1, aimVector[2] * -1]

		upAxis = kwargs.get("upAxis", "z")
		flipUp = kwargs.get("flipUp", False)
		if upAxis == aimAxis:
			#make sure sec axis isn't the same one
			if upAxis == "z": upAxis = "y"
			else: upAxis = "z"
		upVector = [0,0,1]
		if upAxis == "x": upVector = [1,0,0]
		elif upAxis == "y": upVector = [0,1,0]
		if flipUp: upVector = [upVector[0] * -1, upVector[1] * -1, upVector[2] * -1]

		#filter input / validate input
		guideList = []
		nodes = []
		
		if not type(guides) == list: guides = [guides]
		for g in guides:
			g = mnsUtils.validateNameStd(g)
			if g.suffix == mnsPS_gCtrl or g.suffix == mnsPS_gRootCtrl:
				if g and not g.node in nodes and not "blkRoot" in g.node.nodeName(): 
					guideList.append(g)
					nodes.append(g.node)
				
		if guideList:
			#reorder list
			newList = guideList

			if progressBar: progressBar.setValue(15)
			previousProgValue = 15.0
			addedPrgBarValue = 85.0 / float(len(guideList))

			pm.undoInfo(openChunk=True)

			#create a hold locator, that will act as a contrainer to maintain all positions.
			holdLoc = mnsUtils.createNodeReturnNameStd(body = "orientTempMasterHoldLoc", buildType = "locator", createBlkClassID = False, incrementAlpha = False)
			
			#Filetring complete
			for guide in guideList:
				upVectorToUse = upVector

				#gather Data
				toDelete = []
				aimTarget = None
				
				###find aim target within children
				guideChilds = [mnsUtils.validateNameStd(c) for c in guide.node.listRelatives(c = True, type = "transform")]
				foundNativeAimTarget = False
				for c in guideChilds:
					if c and c.node.getShape() and not type(c.node.getShape()) == pm.nodetypes.Locator:
						#if the current child isn't a locator (not the attrHost), assign it to the aim target
						if not foundNativeAimTarget and not orientNativeOnly:
							aimTarget = c

						if c.body == guide.body and c.id == (guide.id + 1):
							#if the current child is of the same module and the next id, it is surely the best aim to find, so break the find loop
							aimTarget = c
							foundNativeAimTarget = True

						if skipEndGuides and not foundNativeAimTarget:
							aimTarget = None

					#pin the node's position
					try:
						toDelete.append(pm.parentConstraint(holdLoc.node, c.node, mo = True))
					except:
						pass

				#data gathering finished, begin action
				if aimTarget:
					#create up loactor
					upLoc = mnsUtils.createNodeReturnNameStd(side = guide.side, body = guide.body + "orientTempUp", alpha = guide.alpha, id = guide.id, buildType = "locator", createBlkClassID = False, incrementAlpha = False)
					pm.matchTransform(upLoc.node, guide.node)
					pm.parent(upLoc.node, guide.node)
					upLoc.node.attr("t" + upAxis).set(5)
					
					#create comparison loc to determaine local direction
					compLoc = mnsUtils.createNodeReturnNameStd(side = guide.side, body = guide.body + "orientTempUpCompare", alpha = guide.alpha, id = guide.id, buildType = "locator", createBlkClassID = False, incrementAlpha = False)
					pm.matchTransform(compLoc.node, guide.node)
					compLoc.node.s.set((1,1,1))
					compOsGrp = mnsUtils.createOffsetGroup(compLoc)
					compLoc.node.attr("t" + upAxis).set(5)

					upLocPos = pm.xform(upLoc.node, q = True, ws=True, a = True, t = True)
					compLocPos = pm.xform(compLoc.node, q = True, ws=True, a = True, t = True)
					pm.delete(compOsGrp.node)

					if upLocPos != compLocPos:
						upLoc.node.attr("t" + upAxis).set(-5)
						if guide.node.sx.get() > 0.0 and guide.node.sy.get() > 0.0 and guide.node.sz.get() > 0.0:
							upVectorToUse = [upVector[0] * -1, upVector[1] * -1, upVector[2] * -1]

					pm.parent(upLoc.node, w = True)
					
					#create Aim Loc
					aimLoc = mnsUtils.createNodeReturnNameStd(side = guide.side, body = guide.body + "orientTempAim", alpha = guide.alpha, id = guide.id, buildType = "locator", createBlkClassID = False, incrementAlpha = False)
					pm.matchTransform(aimLoc.node, aimTarget.node)
					
					#orient guide
					toDelete.append(pm.aimConstraint(aimLoc.node, guide.node, mo = False, aimVector = aimVector, upVector = upVectorToUse, worldUpType = "object", worldUpObject = upLoc.node))
					
					#delete locs
					toDelete.append([upLoc.node, aimLoc.node])
				elif not skipEndGuides:
					#no aim target found, and skip is set to False
					parent = mnsUtils.validateNameStd(guide.node.getParent())
					if parent:
						if orientNativeOnly:
							if not parent.body == guide.body or not parent.id == (guide.id - 1):
								parent = None
						if parent:	
							#create Match Loc
							matchLoc = mnsUtils.createNodeReturnNameStd(side = guide.side, body = guide.body + "orientTempMatch", alpha = guide.alpha, id = guide.id, buildType = "locator", createBlkClassID = False, incrementAlpha = False)
							pm.matchTransform(matchLoc.node, parent.node)
							toDelete.append(pm.orientConstraint(matchLoc.node, guide.node))
							#delete match loc
							toDelete.append(matchLoc.node)

				#delete pin constraints
				if toDelete: pm.delete(toDelete)
				if progressBar:
					progressBar.setValue(previousProgValue + addedPrgBarValue)
					previousProgValue += addedPrgBarValue

			#delete pin loc
			pm.delete(holdLoc.node)
			pm.undoInfo(closeChunk=True)
			if progressBar: progressBar.setValue(100)

def copyShape(source = None, targets = [], reposition = True, **kwargs):
	"""copy shape utility.
	This method is operation on selection.
	Copy the control shape of the first selected component, to the rest of the selection.
	"""

	supressMessages = kwargs.get("supressMessages", False)

	if targets and not type(targets) == list: targets = [targets]
	if source and type(source) == list: source = source[0]

	if not source or not targets:
		sel = pm.ls(sl=True)
		if len(sel) > 1:
			source = sel[0]
			targets = sel[1:]

	if source and targets:
		targetShapes = source.getShapes()
		if targetShapes:
			pm.undoInfo(openChunk=True)
			for s in targets:
				drO = s.getShape().overrideEnabled.get()
				color = s.getShape().overrideColorRGB.get()

				try: pm.delete(s.getShapes())
				except: pass

				dupTransform = pm.duplicate(source)[0]
				pm.delete(dupTransform.listRelatives(c = True, type = "transform"))
				dupTransform.centerPivots()

				for chan in "trs":
					for axis in "xyz":
						dupTransform.attr(chan + axis).setLocked(False)

				if s.getParent(): pm.parent(dupTransform, s.getParent())

				if reposition: 
					pm.delete(pm.parentConstraint(s, dupTransform))
					
				pm.makeIdentity(dupTransform, a = True)
				pm.parent(dupTransform.getShapes(), s, r = 1, shape = 1)
				pm.delete(dupTransform)
				mnsUtils.fixShapesName([s])
				for shape in s.getShapes():
					shape.overrideEnabled.set(True)
					shape.overrideRGBColors.set(1)
					shape.overrideColorRGB.set(color)
			pm.select(targets)
			pm.undoInfo(closeChunk=True)
			if not supressMessages: mnsLog.log("Control shapes copied successfully.", svr = 1)
	else:
		if not supressMessages: mnsLog.log("Invalid selection. Aborting.", svr = 2)

def repositionShape(targets = []):
	"""Simple method to re-center a control shape to its natural pivot
	"""
	pm.undoInfo(openChunk=True)
	if targets and not type(targets) == list: targets = [targets]
	if not targets:
		targets = pm.ls(sl=True)

	if targets:
		
		for s in targets:
			dupTransform = pm.duplicate(s)[0]
			pm.delete(dupTransform.listRelatives(c = True, type = "transform"))

			for chan in "trs":
				for axis in "xyz":
					dupTransform.attr(chan + axis).setLocked(False)
			copyShape(dupTransform, s, True, supressMessages = True)
			pm.delete(dupTransform)
		mnsLog.log("Control shapes repositioned succesfully.", svr = 1)
	pm.undoInfo(closeChunk=True)

def exportCtrlShapes(mode = 0):
	"""
	mode = 0 - All
	mode = 1 - Branch
	mode = 2 - module

	Simple export method for control shapes.
	The relevant control shapes are collected, duplicated and exported to MA.
	"""

	#first get a directory
	rigTop = getRigTopForSel()
	if rigTop:
		filename = QtWidgets.QFileDialog.getSaveFileName(mnsUIUtils.get_maya_window(), "Export Control-Shapes", None, "Maya Ascii (*.ma)")
		if filename: 
			filename = filename[0]
			if filename.endswith(".ma"):
				#file validated, continue
				moduleRoots = collectModuleRootsBasedOnMode(mode)
				
				exportNodes = []
				for moduleRoot in moduleRoots:
					for cs in getCtrlShapesForModueRoot(moduleRoot):
						newName = mnsUtils.returnNameStdChangeElement(cs, suffix = mnsPS_ctrlShapeExport, autoRename = False)
						csDup = pm.duplicate(cs.node)[0]
						csDup.rename(newName.name)
						pm.parent(csDup, w = True)
						exportNodes.append(csDup)
				
				if exportNodes:
					#collection done, export to ma
					pm.select(exportNodes, r = True)
					exported = cmds.file(filename, type='mayaAscii',  pr = True, es=True, f = True, options = "v=0;" )
					pm.delete(exportNodes)
					pm.confirmDialog( title='Success', message= "Control Shapes exported succesffully.", defaultButton='OK')
					mnsLog.log("Control Shapes exported succesffully.", svr = 1)
			else:
				mnsLog.log("Invalid filename. Aborting", svr = 2)
		else:
			mnsLog.log("Invalid filename. Aborting", svr = 2)

def importCtrlShapes():
	"""
	Simple import method for control shapes.
	"""

	#first get a directory
	rigTop = getRigTopForSel()
	if rigTop:
		ctrlShpGrp = getCsGrpFromRigTop(rigTop)

		file = QtWidgets.QFileDialog.getOpenFileName(mnsUIUtils.get_maya_window(), "Select Control Shapes File", filter = "Maya Ascii (*.ma)")
		if file:
			file = file[0]
			if file.endswith(".ma"):
				#file validated, continue
					imported = cmds.file(file, type='mayaAscii', f = True, i = True, gr = True, gn = "mnsImportedCtrlShapes_grp", options = "v=0;" )
					importedGrp = mnsUtils.checkIfObjExistsAndSet("mnsImportedCtrlShapes_grp")
					if importedGrp:
						importedShapes = [s for s in importedGrp.listRelatives(c = True, type = "transform") if s.nodeName().split("_")[-1] == mnsPS_ctrlShapeExport]
						if importedShapes:
							#first run through once to seee if there are clashes
							#if there are, get user decision
							decision = 0 #0 = override, 1 = skip, 2 = abort
							for cs in importedShapes:
								originalName = cs.nodeName().split("_" + mnsPS_ctrlShapeExport)[0] + "_" + mnsPS_ctrlShape
								if mnsUtils.checkIfObjExistsAndSet(originalName):
									msg = QtWidgets.QMessageBox()
									msg.setIcon(QtWidgets.QMessageBox.Critical)
									msg.setText("Some Control-Shapes within the selected file clash with existing control shape of the selected Rig.")
									msg.setInformativeText("How would you like to continue?\n\nOverride - Override existing shapes with imported shapes\nSkip - Skip all clashes keeping oriinal shapes\nAbort - Cancel- do nothing.\n")
									msg.setWindowTitle("Control shapes import clash")

									overrideBtn = QtWidgets.QPushButton("Override")
									msg.addButton(overrideBtn, QtWidgets.QMessageBox.ButtonRole.AcceptRole)

									skipBtn = QtWidgets.QPushButton("Skip")
									msg.addButton(skipBtn, QtWidgets.QMessageBox.ButtonRole.ActionRole)

									AbortBtn = QtWidgets.QPushButton("Abort")
									msg.addButton(AbortBtn, QtWidgets.QMessageBox.ButtonRole.RejectRole)
									
									decision = msg.exec_()
									if decision == 2: #if decision is abort, do nothing
										return False
									break

							#run the second time and act
							importedCount = 0
							for cs in importedShapes:
								originalName = cs.nodeName().split("_" + mnsPS_ctrlShapeExport)[0] + "_" + mnsPS_ctrlShape
								if mnsUtils.checkIfObjExistsAndSet(originalName):
									if decision == 0: #override
										pm.delete(originalName)
									else: #skip
										continue
								
								##all validations finished, accept the control shape
								pm.parent(cs, ctrlShpGrp.node)
								importedCount += 1
								relatedCtrlName = cs.nodeName().split("_" + mnsPS_ctrlShapeExport)[0] + "_" + mnsPS_ctrl
								cs.rename(originalName)
								#find related root guide and connect
								relatedCtrl = mnsUtils.checkIfObjExistsAndSet(relatedCtrlName)
								if relatedCtrl:
									rGuide = getRootGuideFromCtrl(relatedCtrl)
									if rGuide:
										rGuide.node.message >> cs.rootGuide

							if not importedCount:
								pm.confirmDialog( title='Failure', message= "Could not find any shapes matching the selected criteria. No action taken.", defaultButton='OK')
							else:
								pm.confirmDialog( title='Success', message= str(importedCount) + " Control Shapes imported succesffully.", defaultButton='OK')
								mnsLog.log(str(importedCount) + " Control Shapes imported succesffully.", svr = 1)
						else:
							mnsLog.log("Couldn't find any valid control-shapes within the selected file. Aborting.", svr = 2)
						
						#lastly delete the imported grp
						pm.delete(importedGrp)
			else:
				mnsLog.log("Invalid filename. Aborting", svr = 2)
		else:
			mnsLog.log("Invalid filename. Aborting", svr = 2)

def recRenameLowerIndex(root = None, moduleGuides = [], moduleJoints = []):
	root = mnsUtils.validateNameStd(root)
	if root:
		if root.node in moduleGuides:
			relatedJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(root))
			if relatedJnt: 
				recRenameLowerIndex(relatedJnt, moduleGuides, moduleJoints)

			root = mnsUtils.returnNameStdChangeElement(root, id = root.id - 1, autoRename = True)
			if root.node.listRelatives(c = True, type = "transform"):
				for child in root.node.listRelatives(c = True, type = "transform"):
					recRenameLowerIndex(child, moduleGuides, moduleJoints)

		if root.node in moduleJoints:
			root = mnsUtils.returnNameStdChangeElement(root, id = root.id - 1, autoRename = True)
			if root.node.listRelatives(c = True, type = "joint"):
				for child in root.node.listRelatives(c = True, type = "joint"):
					recRenameLowerIndex(child, moduleGuides, moduleJoints)
	
def insertGuides(amount = 0, mode = "above", **kwargs):
	"""This method is used primarily through Block UI, to insert guides above/below any guide selection.
	This will handle all exceptions, as well as re-analyze and re-orgenize each module based on the action performed.
	"""
	
	if mode == "above" or mode == "below":
		modulesToAdd = {}

		sel = kwargs.get("fromObjs", pm.ls(sl=True))
		for s in sel:
			s = mnsUtils.validateNameStd(s)
			rootGuide = mnsUtils.validateNameStd(getModuleRoot(s))
			if s and rootGuide and rootGuide.node not in modulesToAdd.keys():
				if s.node.getAttr("blkClassID") ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gCtrl) or s.node.getAttr("blkClassID") ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl):
					rigTop = getRigTop(rootGuide)
					if rootGuide.node != getRootGuideFromRigTop(rigTop).node:
						modulesToAdd.update({rootGuide.node: s.node})

		if modulesToAdd:
			numGuidesToAdd = amount

			for moduleRoot in modulesToAdd.keys():
				moduleRoot = mnsUtils.validateNameStd(moduleRoot)
				settings, split = getModuleSettings(moduleRoot, includeCreationOnly = True)
				maxGuides, minGuides = -1, -1

				for arg in settings:
					if arg.name == "numOfGuides":
						maxGuides = int(arg.max)
						minGuides = int(arg.min)
						break

				currentGuides = getModuleDecendentsWildcard(moduleRoot, getFreeJntGrp = False, getCtrls = False, getCustomGuides = False, getInterpLocs = False, getJoints = False, getInterpJnts = False)
				currentGuidesCount = len(currentGuides)
				resultCount = numGuidesToAdd + currentGuidesCount

				if resultCount <= maxGuides:
					#all validations passed. Complete the request.
					guideBelow, guideAbove = None, None
					for j in range(currentGuidesCount):
						if currentGuides[j].node == modulesToAdd[moduleRoot.node]:
							if j > 0: guideBelow = currentGuides[j - 1]
							if j < currentGuidesCount - 1: guideAbove = currentGuides[j + 1]
							break

					if mode == "below" and not guideBelow:
						mnsLog.log("Cannot add guides below a root guide. Aborting.", svr = 2)
						return
					
					#rename existing guides and joints
					selectedGuide = mnsUtils.validateNameStd(modulesToAdd[moduleRoot.node])
					incrementIndex = selectedGuide.id
					if mode == "below": incrementIndex -= 1

					for k in range(currentGuidesCount -1 + numGuidesToAdd, -1, -1):
						if not k > currentGuidesCount - 1 and k >= incrementIndex:
							#rename guide and related joint
							mnsUtils.returnNameStdChangeElement(currentGuides[k], id = currentGuides[k].id + numGuidesToAdd, autoRename = True)
							relatedJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(currentGuides[k]))
							mnsUtils.returnNameStdChangeElement(relatedJnt, id = relatedJnt.id + numGuidesToAdd, autoRename = True)

					previousGuide, nextGuide = None, None
					try:
						previousGuide = currentGuides[incrementIndex - 1]
						nextGuide = currentGuides[incrementIndex]
					except: pass

					gScale = mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]
					spacing = gScale * 10

					createdIdx = 1
					for k in range(currentGuidesCount + numGuidesToAdd):
						if k >= incrementIndex and k < incrementIndex + numGuidesToAdd:
							#create new guide, with correct index
							gCtrl = blkCtrlShps.ctrlCreate(side = moduleRoot.side, body = moduleRoot.body, alpha = moduleRoot.alpha, id = k + 1, controlShape = "directionSphere", createBlkClassID = True, createBlkCtrlTypeID = True, blkCtrlTypeID = 0, ctrlType = "guideCtrl", scale = gScale / 2, alongAxis = 1)
							
							#reposition guide
							if incrementIndex == currentGuidesCount:
								pass
							else:
								const = pm.parentConstraint(previousGuide.node, nextGuide.node,  gCtrl.node)
								value = 1.0 / (numGuidesToAdd + 1) * createdIdx
								const.attr(previousGuide.node.nodeName() + "W0").set(1- value)
								const.attr(nextGuide.node.nodeName() + "W1").set(value)
								pm.delete(const)

							gJnt = mnsUtils.createNodeReturnNameStd(side = moduleRoot.side, body = moduleRoot.body, alpha = moduleRoot.alpha, id = k + 1, buildType = "joint", createBlkClassID = True, incrementAlpha = True)
							mnsUtils.lockAndHideAllTransforms(gJnt, lock = True, keyable = False, cb = False)
							gJnt.node.radius.set(gScale)

							mnsNodes.mnsMatrixConstraintNode(side = gCtrl.side, alpha = gCtrl.alpha , id = gCtrl.id, targets = [gJnt.node], sources = [gCtrl.node], connectScale = False)
							mnsNodes.mnsNodeRelationshipNode(side = gCtrl.side, alpha = gCtrl.alpha , id = gCtrl.id, master = gCtrl.node, slaves = [gJnt.node])
							mnsUtils.addAttrToObj(gCtrl, name = "jntSlave" , type = "message", value = gJnt.node, locked = True, cb = False, keyable = False)

							pm.parent(gCtrl.node, currentGuides[k - 1].node)

							if incrementIndex == currentGuidesCount:
								pm.delete(pm.parentConstraint(previousGuide.node, gCtrl.node))
								gCtrl.node.ty.set(spacing)

							currentGuides.insert(k, gCtrl)
							createdIdx += 1
						elif k > incrementIndex:
							pm.parent(currentGuides[k].node, currentGuides[k - 1].node)

					#update joint struct BTC if exists.
					relatedRootJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(moduleRoot))
					outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
					if outConnections:
						for con in outConnections: 
							if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
								con.transforms.disconnect()
								k = 0
								for guide in currentGuides:
									relatedJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(guide))
									relatedJnt.node.worldMatrix[0] >> con.attr("transforms[" + str(k) + "].matrix")
									k += 1

								interpJnts = getModuleInterpJoints(moduleRoot, interpType = mnsPS_iJnt)
								
								j = 0
								for interpJnt in interpJnts:
									parentGuideIdx = int(math.floor((float(len(currentGuides)) / float(len(interpJnts))) * j))
									pm.parent(interpJnt.node, currentGuides[parentGuideIdx].node.attr("jntSlave").get())
									j += 1
								break
					mnsLog.log("Guides added.", svr =1)
				else:
					mnsLog.log("The requested guides addition exceeds the maximum limit for the selected build module. Aborting.", svr = 2)

			setgCtrlColorForRigTop(rigTop)
		else:
			mnsLog.log("Couldn't find any valid items in selection to add to. Aborting.", svr = 2)
	else:
		mnsLog.log("Invalid Mode. Aborting.", svr = 2)

def removeGuides(**kwargs):
	modulesToAdd = {}

	sel = kwargs.get("fromObjs", pm.ls(sl=True))
	for s in sel:
		s = mnsUtils.validateNameStd(s)
		rootGuide = mnsUtils.validateNameStd(getModuleRoot(s))
		if s and rootGuide:
			if s.node.getAttr("blkClassID") ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gCtrl):
				rigTop = getRigTop(rootGuide)
				if rootGuide.node != getRootGuideFromRigTop(rigTop).node:
					if rootGuide.node not in modulesToAdd.keys(): modulesToAdd.update({rootGuide.node: []})
					modulesToAdd[rootGuide.node].append(s.node)

	if modulesToAdd:
		for moduleRoot in modulesToAdd.keys():
			currentGuides = getModuleDecendentsWildcard(moduleRoot, getFreeJntGrp = False, getCtrls = False, getCustomGuides = False, getInterpLocs = False, getJoints = False, getInterpJnts = False)
			resultCount = len(currentGuides) - len(modulesToAdd[moduleRoot])
			moduleRoot = mnsUtils.validateNameStd(moduleRoot)
			settings, split = getModuleSettings(moduleRoot, includeCreationOnly = True)
			maxGuides, minGuides = -1, -1

			for arg in settings:
				if arg.name == "numOfGuides":
					maxGuides = int(arg.max)
					minGuides = int(arg.min)
					break

			if resultCount >= minGuides:
				#all validations passed. Complete the request.

				for guide in modulesToAdd[moduleRoot.node]:
					guideBelow = guide.getParent()
					guidesAbove = guide.listRelatives(c = True, type = "transform")

					#reparent guideAbove
					if guidesAbove:
						for guideAbove in guidesAbove:
							pm.parent(guideAbove, guideBelow)
							
					#get interpJnts and reparent under root
					relatedRootJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(moduleRoot))
					interpJnts = getModuleInterpJoints(moduleRoot, interpType = mnsPS_iJnt)
					for ij in interpJnts: pm.parent(ij.node, relatedRootJnt.node)

					#remove guide
					pm.delete(guide)

					#rename guide from this point beyond
					if guidesAbove:
						currentJoints = getModuleDecendentsWildcard(moduleRoot, getInterpJnts = False, getRootGuide = False, getGuides = False, getFreeJntGrp = False, getCtrls = False, getCustomGuides = False, getInterpLocs = False, getJoints = True)

						for guideAbove in guidesAbove:
							recRenameLowerIndex(guideAbove, [n.node for n in currentGuides if n.node and pm.objExists(n.node)], [j.node for j in currentJoints if j.node and pm.objExists(j.node)])

					#update joint struct BTC if exists.
					currentGuides = getModuleDecendentsWildcard(moduleRoot, getFreeJntGrp = False, getCtrls = False, getCustomGuides = False, getInterpLocs = False, getJoints = False, getInterpJnts = False)
					outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
					if outConnections:
						for con in outConnections: 
							if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
								con.transforms.disconnect()
								
								k = 0
								for guide in currentGuides:
									relatedJnt = mnsUtils.validateNameStd(getRelatedNodeFromObject(guide))
									relatedJnt.node.worldMatrix[0] >> con.attr("transforms[" + str(k) + "].matrix")
									k += 1

								interpJnts = getModuleInterpJoints(moduleRoot, interpType = mnsPS_iJnt)

								j = 0
								for interpJnt in interpJnts:
									parentGuideIdx = int(math.floor((float(len(currentGuides)) / float(len(interpJnts))) * j))
									pm.parent(interpJnt.node, currentGuides[parentGuideIdx].node.attr("jntSlave").get())
									j += 1

								pm.removeMultiInstance(con.attr("transforms[" + str(len(currentGuides)) +"]"))
								break
				mnsLog.log("Guides Removed.", svr =1)
			else:
				mnsLog.log("The requested guides subtraction subceeds the minimum limit for the selected build module. Aborting.", svr = 2)
	else:
		mnsLog.log("Couldn't find any valid items in selection to add to. Aborting.", svr = 2)

###############################
###### color ##################
###############################

def getCtrlCol(ctrl, rigTop, **kwargs):
	"""Get the passed in node's color based on it's type, heirarchy and attributes.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	ctrl = mnsUtils.validateNameStd(ctrl)
	ctrlTypeID = 0
	if ctrl.node.hasAttr("blkCtrlTypeID"): ctrlTypeID = ctrl.node.blkCtrlTypeID.get()

	moduleRoot = kwargs.get("moduleRoot", None)
	if not moduleRoot:
		if ctrl.suffix == mnsPS_gCtrl or ctrl.suffix == mnsPS_cgCtrl or ctrl.suffix == mnsPS_plg: moduleRoot = getModuleRoot(ctrl)

	getRigTop = True
	if moduleRoot:
		if moduleRoot.node.hasAttr("colOverride") and moduleRoot.node.hasAttr("schemeOverride"):
			if moduleRoot.node.attr("colOverride").get(): getRigTop = False
	
	col = (1.0,1.0,1.0)

	colorSchemeList = None
	if getRigTop: 
		colorSchemeList = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList("colorScheme", rigTop)
		sideID = mnsUtils.returnIndexFromSideDict(mnsSidesDict, ctrl.side)
		colrSchemeIndex = (ctrlTypeID * 3) + sideID
		col = colorSchemeList[colrSchemeIndex]
	
	elif moduleRoot: 
		ctrl = moduleRoot
		if ctrl.node.hasAttr("colOverride"):
			if ctrl.node.colOverride.get(): 
				if ctrl.node.hasAttr("schemeOverride"):
					col = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList("schemeOverride", ctrl)[ctrlTypeID]
		
	#return;tuple[3] (color)
	return col

def setCtrlCol(ctrl, rigTop, **kwargs):
	"""Attempt to collect the passed in node's color (based on its type), and set it if seccessfull.
	"""

	ctrl = mnsUtils.validateNameStd(ctrl)

	try: mnsUtils.setCtrlColorRGB([ctrl.node], getCtrlCol(ctrl, rigTop, **kwargs))
	except: pass

	#return;MnsNameStd (ctrl)
	return ctrl

def setgCtrlColorForModule(rigTop, moduleRoot):
	"""For all relevant decendents of the passed in moduleRoot, get and set it's color.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)
	moduleRoot = mnsUtils.validateNameStd(moduleRoot)
	moduleDecendents = getModuleDecendentsWildcard(moduleRoot)

	for guide in moduleDecendents: 
		try: setCtrlCol(guide, rigTop, moduleRoot = moduleRoot)
		except: pass

def setgCtrlColorForRigTop(rigTop):
	"""Set ALL relevnt controls within a rigTop, to their color based on their type.
	"""

	rigTop = mnsUtils.validateNameStd(rigTop)

	gCtrls = getAllcolCtrlforRigTop(rigTop)
	for gCtrl in gCtrls: setCtrlCol(gCtrl, rigTop)

###############################
###### picker #################
###############################

def collectPlgsBasedOnMode(rigTop = None, mode = 0, **kwargs):
	"""
	mode 0 = All
	mode 1 = Brnach
	mode 2 = module
	mode 3 = selected
	"""

	returnCtrls = kwargs.get("returnCtrls", False)

	returnList = []
	if not rigTop: rigTop = getRigTopForSel()
	if rigTop:
		if mode == 0:
			returnList = getAllPlgsForRigTop(rigTop)
		else:
			moduleRoots = collectModuleRootsBasedOnMode(mode)
			ctrls = getCtrlAuthFromRootGuides(moduleRoots)

			if mode == 0:
				ctrls = collectCtrlRelatives(2, rootCtrls = ctrls)
			if mode == 3:
				sel = pm.ls(sl=1)
				for guide in sel:
					guide = mnsUtils.validateNameStd(guide)
					if guide and guide.suffix == mnsPS_plg and not guide.node.hasAttr("width"):
						returnList.append(guide.node)
			else:
				ctrls = collectCtrlRelatives(1, rootCtrls = ctrls)

			if mode != 3 and not returnCtrls:
				returnList = ctrlPickerGuideToggle(rootObjs = ctrls, returnToggle = True, skipUnmatched = True)
			elif mode != 3:
				returnList = ctrls

	return returnList

def collectPickerDataForRigTop(rigTop = None, mode = 0):
	"""
	mode 0 = All
	mode 1 = Brnach
	mode 2 = module
	mode 3 = selected
	"""

	returnData = {}
	if not rigTop: rigTop = getRigTopForSel()
	if rigTop:
		plgsList = collectPlgsBasedOnMode(rigTop, mode)
		if plgsList:
			skipList = ["blkClassID", "blkCtrlTypeID", "messageOut", "master", "ctrlType", "ctrlGrp", "deleteMaster"] 
			for plgNode in plgsList:
				plgKey = plgNode.nodeName()
				
				attrDataDict = {}
				for attr in plgNode.listAttr(ud = True) + [plgNode.tx, plgNode.ty, plgNode.sx, plgNode.sy]:
					if not attr.attrName() in skipList and not attr.attrName() == "selectControls":
						attrDataDict.update({attr.attrName(): attr.get()})
						
					if "freePlg" in plgNode.nodeName():
						#add plgColor
						currentColor = plgNode.getShape().overrideColorRGB.get()
						attrDataDict.update({"overrideColorRGB": currentColor})

						if attr.attrName() == "selectControls":
							controlsList = mnsUtils.splitEnumToStringList("selectControls", plgNode)
							attrDataDict.update({attr.attrName(): controlsList})

				returnData.update({plgKey: attrDataDict})

	#return; dict (plgs data)
	return returnData

def exportPickerData(rigTop = None, mode = 0):
	"""
	mode 0 = All
	mode 1 = Brnach
	mode 2 = module
	mode 3 = selected
	"""

	if not rigTop: rigTop = getRigTopForSel()
	if rigTop:
		filename = QtWidgets.QFileDialog.getSaveFileName(mnsUIUtils.get_maya_window(), "Export Picker Data", None, "Mns Picker Data (*.mnsPickerData)")
		if filename: 
			filename = filename[0]
			if filename.endswith(".mnsPickerData"):
				pickerData = collectPickerDataForRigTop(rigTop, mode)
				if pickerData:
					mnsUtils.writeJsonPath(filename, pickerData)
					pm.confirmDialog( title='Picker Data Exported.', message="Picker Data Exported successfully.", defaultButton='OK')
					mnsLog.log("Exported Picker Data succesfully to: \'" + filename + "\'.", svr = 1)
				else:
					mnsLog.log("Found nothing to export in current mode. Aborting.", svr = 1)
			else:
				mnsLog.log("Invalid file name. Aborting.", svr = 1)
	else:
		mnsLog.log("Couldn't find Rig-Top. Aborting.", svr = 1)

def injectPlgPropertiesFromData(plg = None, data = {}):
	plg = mnsUtils.validateNameStd(plg)
	if plg and data:
		for attrKey in data:
			if "freePlg" in plg.node.nodeName():
				mnsUtils.addAttrToObj([plg.node], type = "list", value = [" "], name = "selectControls", locked = True)

			status, value = mnsUtils.validateAttrAndGet(plg, attrKey, None)
			if status:
				value = data[attrKey]
				if attrKey == "overrideColorRGB":
					mnsUtils.setAttr(plg.node.getShape().attr(attrKey), value)
				elif attrKey == "selectControls":
					mnsUtils.addAttrToObj([plg], type = "list", value = value, name = "selectControls", locked = True, replace = True)
				elif attrKey == "isFacial" and "freePlg" in plg.node.nodeName():
					mnsUtils.setAttr(plg.node.attr(attrKey), value)
					plg.node.v.disconnect()
					connectPlgToVisChannel(plg.node)
				else:
					mnsUtils.setAttr(plg.node.attr(attrKey), value)

def importPickerData(**kwargs):
	fromPath = kwargs.get("fromPath", None)
	progressBar = kwargs.get("progressBar", None)

	filePath = None
	if not fromPath:
		file = QtWidgets.QFileDialog.getOpenFileName(mnsUIUtils.get_maya_window(), "Import Picker Data", filter = "Mns Picker Data (*.mnsPickerData)")
		if file: filePath = file[0]
	else:
		filePath = fromPath
			
	if filePath.endswith(".mnsPickerData"):
		if os.path.isfile(filePath) and filePath.endswith(".mnsPickerData"):
			pickerData = mnsUtils.readJson(filePath)
			rigTop = None

			if pickerData:
				firstPlg = list(pickerData.keys())[0]
				ctrlName = firstPlg.replace("_" + mnsPS_plg, "_" + mnsPS_ctrl)
				firstCtrl = mnsUtils.validateNameStd(ctrlName)
				if firstCtrl:
					rigTop = getRigTop(firstCtrl)

			if not rigTop:
				existingTops = getRigTopAssemblies()
				if len(existingTops) == 1:
					rigTop = existingTops[list(existingTops.keys())[0]]

			if rigTop:
				for plgName in pickerData.keys():
					override = False
					plg = mnsUtils.validateNameStd(plgName)
					freePlgIndex = 1
					side = "c"

					if "freePlg" in plgName:
						freePlgIndex = int(plgName.split("freePlg_A")[-1].split("_")[0])
						side = plgName.split("_")[0]
					if plg: override = True
					if plg and "freePlg" in plgName:
						override = False
						pm.delete(plg.node)

					ctrlName = plgName.replace("_" + mnsPS_plg, "_" + mnsPS_ctrl)
					ctrl = mnsUtils.validateNameStd(ctrlName)

					newPlg = None
					if ctrl or "freePlg" in plgName:
						isFacialInput = -1
						if "isFacial" in pickerData[plgName]:
							isFacialInput = pickerData[plgName]["isFacial"]
						newPlg = createPickerLayoutGuide(ctrl, override, rigTop = rigTop, dontProject = True, freePlgIndex = freePlgIndex, side = side, isFacialInput = isFacialInput)
	
					if newPlg:
						injectPlgPropertiesFromData(newPlg, pickerData[plgName])
			else:
				mnsLog.log("Can't find relevant Rig-Top. Aborting.", svr = 1)
		else:
			mnsLog.log("Invalid file path. Aborting.", svr = 1)
	else:
		mnsLog.log("Invalid file path. Aborting.", svr = 1)

def pickerTitleToggle():
	"""Toggle between PLG 'control' view, to 'title' view.
	"""

	rigTop = getRigTopForSel()
	if rigTop:
		base = getPickerLayoutBaseFromRigTop(rigTop)
		if base:
			if base.node.hasAttr("titleVis"):
				currentVal = base.node.titleVis.get()
				if currentVal is False: base.node.titleVis.set(True)
				else: base.node.titleVis.set(False)

def loadPickerProjectionCam():
	"""Set the main maya camera view to the 'picker projection camera', based on the scene selection (or the related rigTop to selection).
	"""

	rigTop = getRigTopForSel()
	if rigTop:
		projCam = getPickerProjectionCamFromRigTop(rigTop = rigTop)
		if projCam:
			pm.modelPanel("modelPanel4", e=1, cam = projCam.node)
			pm.camera(projCam.node, e= 1,  dfg = True, dgm = True, ff = 3, overscan = 1.1) 
			pm.camera(projCam.node, e= 1, ff = 1) 
			pm.camera(projCam.node, e= 1, ff = 3) 

def pickerLayoutAdjust():
	"""Load a new Maya panel, with the 'Picker Layout Camera' related to the scene selction.
	   This will also set the panel settings before loading it, based on the rigTop and 'layout base' attributes."""

	sel = pm.ls(sl=1)
	rigTop = getRigTopForSel()
	layoutCam = getPickerLayoutCamFromRigTop(rigTop)
	layoutBase = None
	try: layoutBase = rigTop.node.attr("pickerLayoutBase").get()
	except: pass

	if layoutBase and layoutCam:
		rigTop.node.pickerLayoutGrpVis.set(1)
		mnsUtils.lockAndHideAllTransforms(layoutCam.node, lock = False, cb = True, keyable = True)
		layoutCam.node.getShape().ow.setLocked(False)
		width = layoutBase.attr("width").get()
		height = layoutBase.attr("height").get()
		win = mnsUIUtils.tearOffWindow("layoutEditWin", "Edit Picker Layout", width, height, layoutCam.node)
		curPane = "modelPanel4";
		curCam = pm.modelPanel(curPane, q=1, cam = 1)
		pm.modelPanel(curPane, e=1, cam = layoutCam.node)
		pan = cmds.getPanel(withFocus = True)
		pm.modelEditor(pan, e=1, grid = False, headsUpDisplay = False)
		pm.select(layoutBase)
		pm.viewFit()
		pm.modelPanel(curPane, e=1, cam = curCam)
		mnsUtils.lockAndHideAllTransforms(layoutCam.node, lock = True, cb = True, keyable = True)
		layoutCam.node.getShape().ow.setLocked(True)

	pm.select(sel, r= 1)

def loadPerspCam():
	"""Set Maya's main camera panel, to the default 'persp' camera.
	"""

	pm.modelPanel("modelPanel4", e=1, cam = "persp")

def upParentAllPlgTrigger():
	"""OBSELETE. PLG parenting is no longer in use.
	"""

	sel = pm.ls(sl=1)
	rigTop = getRigTopForSel()

	if rigTop: 
		plgs = getAllPlgsForRigTop(rigTop)
		if plgs:
			pickerGuideGrp = getPickerGuidesGrpFromRigTop(rigTop) 
			if pickerGuideGrp:
				for plg in plgs: pm.parent(plg, pickerGuideGrp.node)
	pm.select(sel, r = 1)

def ctrlPickerGuideToggle(**kwargs):
	"""Atempt to toggle between a selection "control" and "PLG" if possible.
	"""

	sel = kwargs.get("rootObjs", pm.ls(sl=1))
	returnToggle = kwargs.get("returnToggle", False)
	skipUnmatched = kwargs.get("skipUnmatched", False)

	newSel = []
	if len(sel) > 0:
		for obj in sel:
			obj = mnsUtils.validateNameStd(obj)
			if obj:
				paralel = None
				if obj.suffix == mnsPS_ctrl:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_plg, autoRename = False).name)
				elif obj.suffix == mnsPS_plg:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_ctrl, autoRename = False).name)

				if paralel: newSel.append(paralel.node)
				elif not skipUnmatched: newSel.append(obj.node)
	
	if returnToggle: return newSel
	else: pm.select(newSel, r= 1)
	
def projectPickerLayoutPos(ctrl, cam, layoutBase):
	"""Get the passed in Ctrl PLG position, relative to the rig's 'layoutBase'.
	   This method 'projects' the ctrl position based on the rig's 'Projection Camera' into the layout base space, and returns it's processed position."""

	x, y = mnsUIUtils.getObjectScreenSpaceByFilmGate(ctrl.node, cam.node)
	x = min(max(x,0), 1)
	y = min(max(y,0), 1)

	basePos = pm.xform(layoutBase.node, q = 1, ws = 1, t = 1)
	width = layoutBase.node.width.get() / 10
	height = layoutBase.node.height.get() / 10
	xZeroWSCoord = basePos[0] - width 
	yZeroWSCoord = basePos[1] - height

	wsPosX = xZeroWSCoord + (x*width*2)
	wsPosY = yZeroWSCoord + (y*height*2)

	#return;tuple[3] (posX), tuple[3] (posY)
	return wsPosX, wsPosY

def addDefaultAttrsToPlg(plg, **kwargs):
	"""For a newly created plg, create all of it's default predefined attributes.
	"""

	plg = mnsUtils.validateNameStd(plg)

	if plg:
		rootGuide = mnsUtils.validateNameStd(kwargs.get("rootGuide", None))
		if rootGuide: 
			mnsUtils.addAttrToObj([plg.node], type = "bool", value = False, name = "isFacial", locked = False, replace = True)
			status, isFacial = mnsUtils.validateAttrAndGet(rootGuide, "isFacial", 0)
			if status:
				rootGuide.node.isFacial >> plg.node.isFacial
			rootGuide = rootGuide.name

		master = mnsUtils.validateNameStd(kwargs.get("master", None))
		if master: master = [master.name]
		else: master = None

		#get defaults from prefs
		prefs = mnsUtils.getMansurPrefs()
		side = plg.side

		defFontSize = 8
		if prefs and "Picker" in prefs and (side + "_PLGText_fontSize") in prefs["Picker"]: defFontSize = prefs["Picker"][(side + "_PLGText_fontSize")]
		defTextCol = [0.0, 0.0, 0.0]
		if prefs and "Picker" in prefs and (side + "_PLGText_color") in prefs["Picker"]: defTextCol = prefs["Picker"][(side + "_PLGText_color")]
		defBold = False
		if prefs and "Picker" in prefs and (side + "_PLGText_bold") in prefs["Picker"]: defBold = prefs["Picker"][(side + "_PLGText_bold")]
		defItalic = False
		if prefs and "Picker" in prefs and (side + "_PLGText_italic") in prefs["Picker"]: defItalic = prefs["Picker"][(side + "_PLGText_italic")]
		defUnderline = False
		if prefs and "Picker" in prefs and (side + "_PLGText_underline") in prefs["Picker"]: defUnderline = prefs["Picker"][(side + "_PLGText_underline")]

		#add all default attributes
		mnsUtils.addAttrToObj([plg.node], type = "string", value = rootGuide, name = "master", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "int", value = -1, name = "ctrlType", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "int", value = -1, name = "ctrlGrp", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "string", value = "", name = "buttonText", locked = True)

		mnsUtils.addAttrToObj([plg.node], type = "int", value = defFontSize, name = "fontSize", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "float", value = defTextCol[0] * 255, name = "textColorR", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "float", value = defTextCol[1] * 255, name = "textColorG", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "float", value = defTextCol[2] * 255, name = "textColorB", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "bool", value = defBold, name = "bold", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "bool", value = defItalic, name = "italic", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "bool", value = defUnderline, name = "underline", locked = True)
		if master: mnsUtils.addAttrToObj([plg.node], type = "list", value = master, name = "selectControls", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "string", value = "", name = "actionScript", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "bool", value = True, name = "isFree", locked = True)
		mnsUtils.addAttrToObj([plg.node], type = "bool", value = False, name = "pre", locked = True)

def connectPlgToVisChannel(plg):
	"""This method handles the vis channel connection of a plg to it's related layoutBase attributes based on it's type.
	"""

	plg = mnsUtils.validateNameStd(plg)
	if plg:
		rigTop = getRigTop(plg.node)
		if rigTop:
			if rigTop.node.hasAttr("pickerLayoutBase"):
				pickerLayoutBase = rigTop.node.pickerLayoutBase.get()
				if pickerLayoutBase:
					plgType = plg.node.blkCtrlTypeID.get()
					isFacial = plg.node.isFacial.get()
					attrSuffix = "Primaries"
					if plgType == 1: attrSuffix = "Secondaries"
					elif plgType == 2: attrSuffix = "Tertiaries"

					bodyMDNode, facialMDNode = locatePLGBaseVisMdNodes(pickerLayoutBase)
					attrSuffix = "X"
					if plgType == 1: attrSuffix = "Y"
					elif plgType == 2: attrSuffix = "Z"

					if isFacial and facialMDNode:
						facialMDNode.node.attr("output" + attrSuffix) >> plg.node.v
					elif not isFacial and bodyMDNode:
						bodyMDNode.node.attr("output" + attrSuffix) >> plg.node.v

def createPickerLayoutGuide(ctrl, override, rigTop = None, **kwargs):
	"""The main creation method for PLG creation.
	   This method will create a new 'Pikcer Layout Guide' based on the passed in parameters.
	   1. get picker layout base.
	   2. collect projection position if requested.
	   3. create and set all attributes"""

	dontProject = kwargs.get("dontProject", False) 
	side = kwargs.get("side", "c") 
	freePlgIndex = kwargs.get("freePlgIndex", 1) 
	isFacialInput = kwargs.get("isFacialInput", -1)

	if rigTop:
		cam = kwargs.get("camera", None) 

		if not cam: cam = getPickerProjectionCamFromRigTop(rigTop)
		pickerLayoutBase = kwargs.get("pickerLayoutBase", None) 
		if not pickerLayoutBase: pickerLayoutBase = getPickerLayoutBaseFromRigTop(rigTop)
		pickerGuidesGrp = kwargs.get("pickerGuidesGrp", None) 
		if not pickerGuidesGrp: pickerGuidesGrp = getPickerGuidesGrpFromRigTop(rigTop)
		rootGuide = None
		master = None

		wsPosX,wsPosY = 0, -3000
		if not dontProject:
			wsPosX, wsPosY = projectPickerLayoutPos(ctrl, cam, pickerLayoutBase)

		if ctrl and override:
			mnsUtils.lockAndHideTransforms(ctrl.node, lock = False)
			plg = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(ctrl, suffix = mnsPS_plg, autoRename = False).name)
			if plg:
				plg = plg.node
				oldParent = plg.getParent()
				pm.parent(plg, w=1)
				plg.tx.set(wsPosX)
				plg.ty.set(wsPosY)
				pm.parent(plg, oldParent)
				mnsUtils.lockAndHideTransforms(plg, tx = False, ty = False, sx = False, sy = False, lock = True)
				return plg
		else:
			color = getCtrlCol(getPuppetRootFromRigTop(rigTop), rigTop)
			body = "freePlg"
			alpha = "A"
			ctrlId = freePlgIndex
			blkClassID = -1
			if ctrl: 
				color = getCtrlCol(ctrl, rigTop)
				side = ctrl.side
				body = ctrl.body
				alpha = ctrl.alpha
				ctrlId = ctrl.id
				rootGuide = getRootGuideFromCtrl(ctrl)
				master = ctrl
				blkClassID = ctrl.node.blkCtrlTypeID.get()

			status, isFacial = mnsUtils.validateAttrAndGet(pickerLayoutBase, "pickerMode", 0)
			if isFacialInput != -1: isFacial = isFacialInput
			plg = blkCtrlShps.ctrlCreate(side = side, body = body, alpha = alpha, id = ctrlId, controlShape = "square", createBlkClassID = True, createBlkCtrlTypeID = True, blkCtrlTypeID = blkClassID, ctrlType = "pickerLayoutCtrl", scale = 1.5, color = color, alongAxis = 2, incrementAlpha = False, isFacial = isFacial)

			plg.node.tx.set(wsPosX)
			plg.node.ty.set(wsPosY)
			pm.parent(plg.node, pickerGuidesGrp.node)

			addDefaultAttrsToPlg(plg, rootGuide = rootGuide, master = master)
			connectPlgToVisChannel(plg)

			if rootGuide: connectSlaveToDeleteMaster(plg, rootGuide)
			mnsUtils.lockAndHideTransforms(plg.node, tx = False, ty = False, sx = False, sy = False, lock = True)
			if ctrl: mnsUtils.setAttr(plg.node.isFree, False)
			pm.select(plg.node, r = True)

			#return;MnsNameStd (plg)
			return plg

def createPickerLayoutGuides(ctrlsToProject, rigTop, msgPrompt = True, **kwargs):
	"""Warpper method that handles multiple PLGs creation.
	"""

	mesPrompted = False
	override = False

	plgs = []
	for ctrl in ctrlsToProject:
		exists = False
		exists = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(ctrl, suffix = mnsPS_plg, autoRename = False).name)

		if exists and msgPrompt and not mesPrompted:
			overrideMes = "One of the selected ctrls already exists within the picker layout guide. <br> Do you want to override existing position ? <br><br> YES = Override for this clash and all next clashes <br> NO = Skip all clashes"
			reply = pm.confirmDialog( title='Picker Layout Guide Override', message=overrideMes, button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
			if(reply == 'Yes'): override = True
			mesPrompted = True
		elif not msgPrompt: override = True

		overrideSend = False
		if exists and override: overrideSend = True

		create = True
		if exists and not override: pass
		else: 
			plg = createPickerLayoutGuide(ctrl, overrideSend, rigTop, **kwargs)
			plgs.append(plg.node)
	if plgs:
		pm.select(plgs, r = True)

def projectPickerLayout(mode = 0, msgPrompt = True):
	"""A wrapper method that handles plg projection from scene objects based on mode.
	mode 0 = selected
	mode 1 = module
	mode 2 = branch
	"""

	ctrlsToProject = []
	cam = None
	rigTop = None

	selection = pm.ls(sl = 1)
	if len(selection) > 0:
		rigTop = getRigTopForSel()
		if rigTop:
			cam = getPickerProjectionCamFromRigTop(rigTop)
			if cam:
				#selection case
				if mode == 0:
					for obj in selection:
						obj = mnsUtils.validateNameStd(obj)
						if obj:
							if obj.node.hasAttr("blkClassID"):
								if obj.node.blkClassID.get() ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_ctrl):
									if obj.node.hasAttr("blkCtrlTypeID") and obj.node.blkCtrlTypeID.get() < 3:
										ctrlsToProject.append(obj)
				#module/branch cases
				else:
					sendMode = 2
					if mode == 1: sendMode = 2
					elif mode == 2: sendMode = 1

					ctrlsToProject = collectPlgsBasedOnMode(rigTop, sendMode, returnCtrls = True)
					ctrlsToProject = [mnsUtils.validateNameStd(ctrl) for ctrl in ctrlsToProject]

	if len(ctrlsToProject) > 0:
		pm.undoInfo(openChunk=True)
		upParentAllPlgTrigger()
		createPickerLayoutGuides(ctrlsToProject, rigTop, msgPrompt, cam = cam)
		pm.undoInfo(closeChunk=True)

def projectSelectedPickerLayout(msgPrompt = True):
	"""A wrapper method that handles plg projection from selected scene objects.
	"""

	ctrlsToProject = []
	cam = None
	rigTop = None

	selection = pm.ls(sl = 1)
	if len(selection) > 0:
		rigTop = getRigTopForSel()
		if rigTop:
			cam = getPickerProjectionCamFromRigTop(rigTop)
			if cam:
				for obj in selection:
					obj = mnsUtils.validateNameStd(obj)
					if obj:
						if obj.node.hasAttr("blkClassID"):
							if obj.node.blkClassID.get() ==  mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_ctrl):
								if obj.node.hasAttr("blkCtrlTypeID") and obj.node.blkCtrlTypeID.get() < 3:
									ctrlsToProject.append(obj)

	if len(ctrlsToProject) > 0:
		upParentAllPlgTrigger()
		createPickerLayoutGuides(ctrlsToProject, rigTop, msgPrompt, cam = cam)

def symmetrizePlg(guide = None):
	"""Block 'plg symmetrize' button trigger.
	   This method will handle validation and creation of PLG related symmetrical plg."""

	guide = mnsUtils.validateNameStd(guide)
	if guide and guide.suffix == mnsPS_plg:
		rigTop = getRigTop(guide)
		if rigTop:	
			if guide.side == mnsPS_cen: mnsLog.log("Cannot symmetrize center component - \'" + guide.name + "\'.", svr = 1) 
			else:
				symSide = mnsPS_right
				if guide.side == mnsPS_right: symSide = mnsPS_left

				symPlg = getOppositeSideControl(guide)

				if not symPlg:
					if guide.node.isFree.get():
						symPlg = createPickerLayoutGuide(None, False, rigTop, side = symSide,dontProject = True)
						symPlg = mnsUtils.returnNameStdChangeElement(symPlg, side = symSide, autoRename = True)
					else:
						guideMaster = mnsUtils.splitEnumToStringList("selectControls", guide.node)

						if guideMaster:
							guideMaster = guideMaster[0]
							symMaster = getOppositeSideControl(guideMaster)
							if symMaster:
								symPlg = createPickerLayoutGuide(symMaster, False, rigTop, dontProject = True)

				if symPlg:
					#pos
					symPlg.node.tx.set(guide.node.tx.get() * -1)
					symPlg.node.ty.set(guide.node.ty.get())

					#copy attrs
					attrToCopy = ["buttonText","fontSize", "textColorR", "textColorG", "textColorB",
									"bold", "italic", "underline", "pre", "sx", "sy", "actionScript"]
					for attrName in attrToCopy: 
						mnsUtils.setAttr(symPlg.node.attr(attrName), guide.node.attr(attrName).get())

					if guide.node.isFree.get():
						mnsUtils.setAttr(symPlg.node.attr("isFacial"), guide.node.attr("isFacial").get())

						controlsList = mnsUtils.splitEnumToStringList("selectControls", guide.node)
						newCtrlsList = []
						for ctrl in controlsList:
							ctrl = mnsUtils.validateNameStd(ctrl)
							if ctrl:
								oppCtrl = getOppositeSideControl(ctrl)
								if oppCtrl: newCtrlsList.append(oppCtrl.name)
						if newCtrlsList:
							mnsUtils.addAttrToObj([symPlg], type = "list", value = newCtrlsList, name = "selectControls", locked = True, replace = True)

						## set complimantary color
						currentColor = guide.node.getShape().overrideColorRGB.get()
						mnsUtils.setAttr(symPlg.node.getShape().overrideColorRGB, (1.0 - currentColor[0], 1.0 - currentColor[1], 1.0 - currentColor[2]))

def duplicatePlg(guide = None):
	"""Block "PLG duplicate" trigger.
	   This method will handle PLG validation and duplication."""

	guide = mnsUtils.validateNameStd(guide)
	if guide and guide.suffix == mnsPS_plg:
		rigTop = getRigTop(guide)
		if rigTop:	
			if guide.node.isFree.get():
				dupPlg = createPickerLayoutGuide(None, False, rigTop, dontProject = True)
				
				if dupPlg:
					dupPlg.node.tx.set(guide.node.tx.get() + 2)
					dupPlg.node.ty.set(guide.node.ty.get() - 2)

					#copy attrs
					attrToCopy = ["buttonText","fontSize", "textColorR", "textColorG", "textColorB",
									"bold", "italic", "underline", "pre", "sx", "sy", "actionScript", "isFacial"]
					for attrName in attrToCopy: 
						mnsUtils.setAttr(dupPlg.node.attr(attrName), guide.node.attr(attrName).get())

					controlsList = mnsUtils.splitEnumToStringList("selectControls", guide.node)
					mnsUtils.addAttrToObj([dupPlg], type = "list", value = controlsList, name = "selectControls", locked = True, replace = True)
					mnsUtils.setAttr(dupPlg.node.getShape().overrideColorRGB, guide.node.getShape().overrideColorRGB.get())

def symmetrizePlgs():
	"""A simple wrapper method to symmetrize multiple PLG's (based on scene selection).
	"""

	sel = pm.ls(sl=1)
	if sel:
		pm.undoInfo(openChunk=True)
		for guide in sel:
			guide = mnsUtils.validateNameStd(guide)
			if guide and guide.suffix == mnsPS_plg:
				symmetrizePlg(guide)
		pm.undoInfo(closeChunk=True)

def duplicatePlgs():
	"""A simple wrapper mwthod to handle multiple PLG duplication (Based on scene selection).
	"""

	sel = pm.ls(sl=1)
	if sel:
		pm.undoInfo(openChunk=True)
		for guide in sel:
			guide = mnsUtils.validateNameStd(guide)
			if guide and guide.suffix == mnsPS_plg:
				duplicatePlg(guide)
		pm.undoInfo(closeChunk=True)
		
def collectPLGuidesToAlign(mode = 0):
	"""This is the main collect wrapper for all 'align plg' tools in BLOCK.
	   This methods will validate and collect all PLG to align from the current scene selection"""

	sel = pm.ls(sl=1)
	guidesToAlign = {}
	minLeft = None

	rigTop = None

	for guide in sel:
		guide = mnsUtils.validateNameStd(guide)

		if guide:
			if guide.suffix == mnsPS_plg and not guide.node.hasAttr("width"):
				data = None
				if mode != 1: data = pm.xform(guide.node, q = 1, ws = 1, t = 1)
				else: 
					dup = pm.duplicate(guide.node, name = "TEMPDUP")[0]
					pm.delete(dup.getChildren(type = "transform"))
					pm.parent(dup, w=1)
					data = dup.getBoundingBox()
					pm.delete(dup)
				gParent = guide.node.getParent()
				gather = [guide, data]
				guidesToAlign.update({guide.name: gather})

	#return;dict (PLGs to align)
	return guidesToAlign

def alignPLGuides(border = "left", mode = 0):
	"""This is the main 'align' trigger to all 'align tools' in BLOCK.
	   This method will calidate and collect the current scene slection, then align the collected PLG's based on the mode passed in."""

	selA = pm.ls(sl=1)
	guidesToAlign = collectPLGuidesToAlign(mode)

	newCollection = {}
	if guidesToAlign:
		alignRef = None
		for guide in guidesToAlign.keys():
			if not alignRef: alignRef = guidesToAlign[guide]
			else:
				if mode != 1:
					if border == "left":
						if guidesToAlign[guide][1][0] < alignRef[1][0]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][0] != alignRef[1][0]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					elif border == "right":
						if guidesToAlign[guide][1][0] > alignRef[1][0]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][0] != alignRef[1][0]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					elif border == "top":
						if guidesToAlign[guide][1][1] > alignRef[1][1]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][1] != alignRef[1][1]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					elif border == "bottom":
						if guidesToAlign[guide][1][1] < alignRef[1][1]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][1] != alignRef[1][1]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					elif border == "h" or border == "v" or border == "mir" or border == "sym":
						newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
				else:
					if border == "left": 
						if guidesToAlign[guide][1][0][0] < alignRef[1][0][0]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][0][0] != alignRef[1][0][0]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					if border == "right": 
						if guidesToAlign[guide][1][1][0] > alignRef[1][1][0]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][1][0] != alignRef[1][1][0]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					if border == "bottom": 
						if guidesToAlign[guide][1][0][1] < alignRef[1][0][1]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][0][1] != alignRef[1][0][1]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
					if border == "top": 
						if guidesToAlign[guide][1][1][1] > alignRef[1][1][1]: 
							newCollection.update({alignRef[0].name: alignRef})
							alignRef = guidesToAlign[guide]
						elif guidesToAlign[guide][1][1][1] != alignRef[1][1][1]: newCollection.update({guidesToAlign[guide][0].name: guidesToAlign[guide]})
		if (newCollection or border == "h" or border == "v" or border == "mir" or border == "sym") and alignRef[0].name not in newCollection: 
			newCollection.update({alignRef[0].name: alignRef})



		####### handle symmetry unparenting
		mirrorSideCollect = {}
		if mode == 3 and border == "sym":
			for guide in newCollection.keys():
				symSide = mnsPS_right
				if newCollection[guide][0].side == mnsPS_right: symSide = mnsPS_left
				symPlg = mnsUtils.returnNameStdChangeElement(newCollection[guide][0], side = symSide, autoRename = False)
				symPlg = mnsUtils.checkIfObjExistsAndSet(obj = symPlg.name)
				if symPlg:
					symPlg = mnsUtils.validateNameStd(symPlg)
					if symPlg:
						mirrorSideCollect.update({symPlg.name: [symPlg]})
		loopDict = dict(newCollection, **mirrorSideCollect)
		#######


		unparentCollect = {}
		for guide in loopDict.keys():
			if loopDict[guide][0].node.nodeName() not in unparentCollect:
				unparentCollect.update({loopDict[guide][0].node.nodeName(): [loopDict[guide][0].node, loopDict[guide][0].node.getParent()]})

			children = loopDict[guide][0].node.listRelatives(ad = True, type = "transform")
			for child in children: 
				if child.nodeName() not in unparentCollect:
					unparentCollect.update({child.nodeName(): [child, child.getParent()]})

		rigTop = getRigTop(alignRef[0].node)
		layoutBase = getPickerLayoutBaseFromRigTop(rigTop)

		pm.undoInfo(openChunk=True)
		for child in unparentCollect:
			pm.parent(unparentCollect[child][0], w = True)

		tempTransform = None
		if mode == 1: tempTransform = pm.group(empty = 1, name = "tempAlignroupBloxk")

		for guide in newCollection.keys():
			if newCollection[guide] is not alignRef or border == "h" or border == "v" or border == "mir" or border == "sym":
				if mode != 1:
					if border == "left" or border == "right": pm.delete(pm.pointConstraint(alignRef[0].node,  newCollection[guide][0].node, skip = ["z","y"]))
					elif border == "top" or border == "bottom": pm.delete(pm.pointConstraint(alignRef[0].node,  newCollection[guide][0].node, skip = ["z","x"]))
					elif border == "h" or border == "v": 
						pm.parent(newCollection[guide][0].node, layoutBase.node)
						if border == "h": newCollection[guide][0].node.tx.set(0)
						if border == "v": newCollection[guide][0].node.ty.set(0)
					elif border == "mir":
						newCollection[guide][0].node.tx.set(newCollection[guide][1][0] * -1)
					elif border == "sym":
						symSide = mnsPS_right
						if newCollection[guide][0].side == mnsPS_right: symSide = mnsPS_left
						symPlg = mnsUtils.returnNameStdChangeElement(newCollection[guide][0], side = symSide, autoRename = False)
						symPlg = mnsUtils.checkIfObjExistsAndSet(obj = symPlg.name)
						if symPlg:
							symPlg = mnsUtils.validateNameStd(symPlg)
							if symPlg:
								symPlg.node.tx.set(newCollection[guide][1][0] * -1)
								symPlg.node.ty.set(newCollection[guide][1][1])
								symPlg.node.sx.set(newCollection[guide][0].node.sx.get() * -1)
								symPlg.node.sy.set(newCollection[guide][0].node.sy.get())
				if mode == 1:
					if border == "left": 
						tempTransform.tx.set((newCollection[guide][1][0][0]))
						pm.parent(newCollection[guide][0].node, tempTransform)
						tempTransform.tx.set(alignRef[1][0][0])
						pm.parent(newCollection[guide][0].node, w=1)
					if border == "right": 
						tempTransform.tx.set((newCollection[guide][1][1][0]))
						pm.parent(newCollection[guide][0].node, tempTransform)
						tempTransform.tx.set(alignRef[1][1][0])
						pm.parent(newCollection[guide][0].node, w=1)
					if border == "bottom": 
						tempTransform.ty.set((newCollection[guide][1][0][1]))
						pm.parent(newCollection[guide][0].node, tempTransform)
						tempTransform.ty.set(alignRef[1][0][1])
						pm.parent(newCollection[guide][0].node, w=1)
					if border == "top": 
						tempTransform.ty.set((newCollection[guide][1][1][1]))
						pm.parent(newCollection[guide][0].node, tempTransform)
						tempTransform.ty.set(alignRef[1][1][1])
						pm.parent(newCollection[guide][0].node, w=1)


		for child in unparentCollect: pm.parent(unparentCollect[child][0], unparentCollect[child][1])
		if mode == 1: pm.delete(tempTransform)

		pm.select(selA, r = 1)
		pm.undoInfo(closeChunk=True)

def getKeyboardModifiersState():
	mode = "replace"
	modifiers = QtWidgets.QApplication.keyboardModifiers()
	if modifiers:
		if modifiers == QtCore.Qt.AltModifier: mode = "alt"
		elif modifiers == QtCore.Qt.ShiftModifier: mode = "toggle"
		elif modifiers == QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier: mode = "toggleAlt"
		elif modifiers == QtCore.Qt.ControlModifier: mode = "remove"
		elif modifiers == QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier: mode = "removeAlt"
		elif modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier): mode = "add"
		elif modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier): mode = "addAlt"
	return mode

def selectRelatedControls(controlsToSelect, mode = "replace"):
	if controlsToSelect:
		if "alt" in mode.lower():
			addedControls = []
			for ctrl in controlsToSelect:
				symCtrl = getOppositeSideControl(ctrl)
				if symCtrl: addedControls.append(symCtrl.node)

			controlsToSelect += addedControls
		
		if "replace" in mode or mode == "alt": pm.select(controlsToSelect, r = True)
		elif "add" in mode: pm.select(controlsToSelect, add = True)
		elif "toggle" in mode: pm.select(controlsToSelect, tgl = True)
		elif "remove" in mode: pm.select(controlsToSelect, d = True)
		
	else:
		pm.select(clear = True)

def executeActionScript(plgNode):
	if plgNode:
		if plgNode.actionScript.get():
			exec(plgNode.actionScript.get())
				
def pickerButtonClickAction(btn, **kwargs):
	"""The global action trigger for any picker UI button click trigger.
	   This method will trigger the "controls selection" and the "action script" for the passed in QPushButton passed in.
	"""

	plgNode = kwargs.get("plgNode", None)

	if btn or plgNode:
		mode = getKeyboardModifiersState()
		if not plgNode and btn: plgNode = mnsUtils.checkIfObjExistsAndSet(obj = btn.plgNode)
		
		if plgNode:
			plgStd = mnsUtils.validateNameStd(plgNode)
			controlsToSelect = []

			if plgNode.hasAttr("selectControls"):
				controlsList = mnsUtils.splitEnumToStringList("selectControls", plgNode)

				for ctrlName in controlsList:
					ctrl = mnsUtils.checkIfObjExistsAndSet(obj = ctrlName, namespace = plgStd.namespace)
					if ctrl: 
						status, cnsMaster = mnsUtils.validateAttrAndGet(ctrl, "cnsMaster", None)
						if cnsMaster:
							controlsToSelect.append(cnsMaster)
						else:
							controlsToSelect.append(ctrl)

			if not plgNode.pre.get():
				selectRelatedControls(controlsToSelect, mode)
				executeActionScript(plgNode)
			else:
				executeActionScript(plgNode)
				selectRelatedControls(controlsToSelect, mode)

def getAllCtrlsFromRigTop(rigTop = None):
	"""Get all controls for the given rig top.
	"""

	if rigTop:
		if rigTop.namespace:
			return pm.ls(rigTop.namespace + ":*_ctrl")
		else:
			return [ctrl for ctrl in rigTop.node.listRelatives(ad = True, type = "transform") if ctrl.nodeName().endswith("_ctrl")]

def selectAllCtrls(rigTop = None, **kwargs):
	"""Select all controls for the given rig top.
	"""

	predefinedCtrls = kwargs.get("predefinedCtrls", [])

	if rigTop:
		allCtrls = predefinedCtrls
		if not allCtrls:
			allCtrls = getAllCtrlsFromRigTop(rigTop)
			exsitingCnsCtrls = getExisingCnsCtrlsForRigTop(rigTop)
			if exsitingCnsCtrls:
				for cnsKey in exsitingCnsCtrls.keys():
					status, cnsSlave = mnsUtils.validateAttrAndGet(exsitingCnsCtrls[cnsKey], "cnsSlave", None)
					if cnsSlave and cnsSlave in allCtrls:
						allCtrls.remove(cnsSlave)
						allCtrls.append(exsitingCnsCtrls[cnsKey].node)

		pm.select(allCtrls, replace = True)
		return allCtrls

def resetAllControlForRigTop(rigTop = None, **kwargs):
	predefinedCtrls = kwargs.get("predefinedCtrls", [])
	skipModuleVis = kwargs.get("skipModuleVis", False)

	if not rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		predefinedCtrls = kwargs.get("predefinedCtrls", [])
		allCtrls = predefinedCtrls
		if not allCtrls: allCtrls = getAllCtrlsFromRigTop(rigTop)

		resetControls(allCtrls, skipModuleVis = skipModuleVis)

def togglePickerCtrlBodyFacial():
	sel = pm.ls(sl=1)
	if sel:
		rigTop = getRigTopForSel()
		if rigTop:
			pickerBase = getPickerLayoutBaseFromRigTop(rigTop)
			if pickerBase:
				pickerBase.node.pickerMode.set(not pickerBase.node.pickerMode.get())

def getExisingCnsCtrlsForRigTop(rigTop):
	exsitingCnsCtrls = {}

	if rigTop:
		status, rigTopCnsCtrls = mnsUtils.validateAttrAndGet(rigTop, "cnsCtrls", "")
		if rigTopCnsCtrls:
			for nodeName in rigTopCnsCtrls.replace(" ", "").split(","):
				cnsCtrl = mnsUtils.validateNameStd(nodeName)
				if cnsCtrl: 
					exsitingCnsCtrls.update({nodeName: cnsCtrl})
	return exsitingCnsCtrls

def toggleGuideJoint(**kwargs):
	"""Atempt to toggle between a selection guide and main joint if possible.
	"""

	sel = kwargs.get("rootObjs", pm.ls(sl=1))
	returnToggle = kwargs.get("returnToggle", False)

	newSel = []
	if len(sel) > 0:
		for obj in sel:
			obj = mnsUtils.validateNameStd(obj)
			if obj:
				paralel = None
				if obj.suffix == mnsPS_gRootCtrl:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_rJnt, autoRename = False).name)
				elif obj.suffix == mnsPS_gCtrl:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_jnt, autoRename = False).name)
				elif obj.suffix == mnsPS_rJnt:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_gRootCtrl, autoRename = False).name)
				elif obj.suffix == mnsPS_jnt:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_gCtrl, autoRename = False).name)

				if paralel: newSel.append(paralel.node)
				else: newSel.append(obj.node)
	
	if returnToggle: return newSel
	else: pm.select(newSel, r= 1)

def toggleGuideCtrl(**kwargs):
	"""Atempt to toggle between a selection guide and main joint if possible.
	"""

	sel = kwargs.get("rootObjs", pm.ls(sl=1))
	returnToggle = kwargs.get("returnToggle", False)

	newSel = []
	if len(sel) > 0:
		for obj in sel:
			obj = mnsUtils.validateNameStd(obj)
			if obj:
				paralel = None
				if obj.suffix == mnsPS_gRootCtrl:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_ctrl, autoRename = False).name)
				elif obj.suffix == mnsPS_gCtrl:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_ctrl, autoRename = False).name)
				elif obj.suffix == mnsPS_ctrl:
					paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_gRootCtrl, autoRename = False).name)
					if not paralel:
						paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(obj, suffix = mnsPS_gCtrl, autoRename = False).name)
					if not paralel:
						moduleAnimGrp = recGetModuleTopForCtrl(obj)
						if moduleAnimGrp:
							paralel = mnsUtils.validateNameStd(mnsUtils.returnNameStdChangeElement(moduleAnimGrp, suffix = mnsPS_gRootCtrl, autoRename = False).name)

				if paralel and not paralel.node in newSel: newSel.append(paralel.node)
				else: newSel.append(obj.node)
	
	if returnToggle: return newSel
	else: pm.select(newSel, r= 1)

###############################
###### pose ###################
###############################

def saveLoadPose(guides = [], **kwargs):
	"""This is the main wrapper for all pose 'save & load' triggers of BLOCK.
	"""

	progressBar = kwargs.get("progressBar", None)
	rigTop = kwargs.get("rigTop", None) #arg; 
	mode = kwargs.get("mode", 0) #arg; optionBox = all, tree, modules, selectedOnly 
	saveLoad = kwargs.get("saveLoad", 0) #arg; optionBox = save, load, delete
	msgPrompt = kwargs.get("msgPrompt", False) #arg;
	pose = kwargs.get("pose", "T") #arg; optionBox = bind, T, A, concept, custom
	relAbsMode = kwargs.get("relAbsMode", 3) #0 = relative, 1 = absolute, 3 = auto

	if guides:
		if type(guides) is not list: guides = [guides]
		if len(guides) > 0:
			if progressBar: progressBar.setValue(0)
			if not rigTop: rigTop = getRigTop(guides[0])
			if rigTop:
				guidesCollect = []
				if mode == 0:
					baseGuide= getRootGuideFromRigTop(rigTop)
					guidesCollect = collectGuides(baseGuide, getCustomGuides = True, getGuides = True, includeDecendents = True, includeDecendentBranch = True, allAsSparse = True)[1]
				elif mode == 1: guidesCollect = collectGuides(guides, getCustomGuides = True, getGuides = True, includeDecendents = True, includeDecendentBranch = True, allAsSparse = True)[1]
				elif mode == 2: guidesCollect = collectGuides(guides, getCustomGuides = True, getGuides = True, includeDecendents = True, includeDecendentBranch = False, allAsSparse = True)[1]
				elif mode == 3: guidesCollect = collectGuides(guides, getCustomGuides = True, getGuides = True, includeDecendents = False, includeDecendentBranch = False, allAsSparse = True)[1]
				if progressBar: progressBar.setValue(10)

				if saveLoad == 0 or saveLoad == 2:
					if saveLoad == 2:
						do = False
						if msgPrompt:
							deleteMes = "Are you sure you want to delete " + pose + "-pose from selected ?"
							reply = pm.confirmDialog( title='Pose Delete', message=deleteMes, button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
							if(reply == 'Yes'): do = True
						else: do = True
						if do: 	
							deletePoseForGuides(guidesCollect, pose, progressBar = progressBar)
							if progressBar: progressBar.setValue(100)
							mnsLog.log("Deleted " + pose + "-Pose for guides.", svr = 1)
							if progressBar: progressBar.setValue(0)
					else:
						savePoseForGuides(guidesCollect, pose, msgPrompt, progressBar = progressBar, mode = relAbsMode)
						if progressBar: progressBar.setValue(100)
						mnsLog.log("Saved " + pose + "-Pose for guides.", svr = 1)
						if progressBar: progressBar.setValue(0)
							
				elif saveLoad == 1:
					loadPoseForGuides(guidesCollect, pose, progressBar = progressBar, mode = relAbsMode)
					if progressBar: progressBar.setValue(100)
					mnsLog.log("Loaded " + pose + "-Pose for guides.", svr = 1)
					if progressBar: progressBar.setValue(0)

def savePoseForGuides(guides = [], poseSet = "T", msgPrompt = False, **kwargs):
	"""Block's save pose wrapper.
	"""

	mode = kwargs.get("mode", 1) #0 = relative, 1 = absolute
	progressBar = kwargs.get("progressBar", None)
	mesPrompted = False
	override = False
	exists = False

	if guides:
		if progressBar: progressBar.setValue(0)
		addedPrgBarValue = 90.0 / float(len(guides))
		previousProgValue = 10.0

		for guide in guides:
			guide =  mnsUtils.validateNameStd(guide)

			if guide:
				#add relative/abs attr
				mnsUtils.addAttrToObj([guide.node], type = "int", value = int(mode), name = (poseSet + "_Pose_mode"), cb = False, locked = True, keyable = False, replace = True)

				for chan in "TRS":
					attrName = poseSet + "_Pose" + chan
					if guide.node.hasAttr(attrName): exists = True
					else:
						pm.addAttr(guide.node, type = "float3", ln = attrName)
						data = [0,0,0]
						if mode == 1:
							if chan == "T":
								data = pm.xform(guide.node, q = True, ws=True, a = True, t = True)
							elif chan == "R":
								data = pm.xform(guide.node, q = True, ws=True, a = True, ro = True)
							elif chan == "S":
								data = pm.xform(guide.node, q = True, ws=True, a = True, s = True)
						else:
							data = guide.node.attr(chan.lower()).get()

						guide.node.attr(attrName).set(data)
						guide.node.attr(attrName).setLocked(True)
					
					if exists and msgPrompt and not mesPrompted:
						overrideMes = "One of the selected guides " + poseSet + "-pose is laready set. <br> Do you want to override it ? <br><br> YES = Override for this clash and all next clashes <br> NO = Skip all clashes"
						reply = pm.confirmDialog( title='Pose Override', message=overrideMes, button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
						if(reply == 'Yes'): override = True
						mesPrompted = True
					elif not msgPrompt: override = True

					if exists and override:
						guide.node.attr(attrName).setLocked(False)
						data = ""
						if chan == "T":
							data = pm.xform(guide.node, q = True, ws=True, a = True, t = True)
						elif chan == "R":
							data = pm.xform(guide.node, q = True, ws=True, a = True, ro = True)
						elif chan == "S":
							data = pm.xform(guide.node, q = True, ws=True, a = True, s = True)
						guide.node.attr(attrName).set(data)
						guide.node.attr(attrName).setLocked(True)

				#check whether it is a custom guide, and a nurbs curve shape
				#if so, store pose as a new nurbsCurve attr
				status, blkClassID = mnsUtils.validateAttrAndGet(guide, "blkClassID", False)
				if blkClassID and blkClassID == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_cgCtrl):
					guideShapeNode = guide.node.getShape()
					if guideShapeNode and type(guideShapeNode) == pm.nodetypes.NurbsCurve:
						attrName = poseSet + "_PoseShape"
						contin = True
						if guide.node.hasAttr(attrName):
							if override: 
								pm.deleteAttr(guide.node.attr(attrName))
							else:
								contin = False
						if contin:
							guide.node.addAttr(attrName, dt = "nurbsCurve", ci = True)
							poseAttr = guide.node.attr(attrName)
							guideShapeNode.worldSpace[0] >> poseAttr
							poseAttr.disconnect()

			if progressBar:
				progressBar.setValue(previousProgValue + addedPrgBarValue)
				previousProgValue += addedPrgBarValue

def orderGuidesToFamilyOrder(guides = []):
	returnOrdered = []

	orderedIndices = {}
	for guide in guides:
		guideNode = mnsUtils.checkIfObjExistsAndSet(guide.node)
		if guideNode:
			parents = guideNode.getAllParents()
			numParents = len(parents)
			if numParents in orderedIndices.keys():
				orderedIndices[numParents].append(guide)
			else:
				orderedIndices[numParents] = [guide]

	for parentIndex in sorted(orderedIndices.keys()):
		returnOrdered += orderedIndices[parentIndex]

	return returnOrdered

def loadPoseForGuides(guides = [], poseSet = "T", **kwargs):
	"""Block's load pose wrapper.
	"""

	mode = kwargs.get("mode", 3) #0 = relative, 1 = absolute, 3 = auto

	if guides:
		if mode != 0:
			guides = orderGuidesToFamilyOrder(guides)
		
		progressBar = kwargs.get("progressBar", None)
		if progressBar: progressBar.setValue(0)
		addedPrgBarValue = 90.0 / float(len(guides))
		previousProgValue = 10.0

		pm.undoInfo(openChunk=True)
		attrsToDisconnect = []

		for guide in guides:
			guide =  mnsUtils.validateNameStd(guide)
			if guide:
				setMode = mode
				if setMode == 3:
					#get mode, if doesn't exist, assume relative
					if guide.node.hasAttr(poseSet + "_Pose_mode"):
						setMode = guide.node.attr(poseSet + "_Pose_mode").get()
					else:
						#add relative/abs attr
						setMode = 0
						mnsUtils.addAttrToObj([guide.node], type = "int", value = int(setMode), name = (poseSet + "_Pose_mode"), locked = True, replace = True)

				for chan in "TR":
					attrName = poseSet + "_Pose" + chan
					if guide.node.hasAttr(attrName):
						if setMode == 1:
							try: 
								data = guide.node.attr(attrName).get()
								if chan == "T":
									pm.xform(guide.node, ws=True, a = True, t = data)
								elif chan == "R":
									data = pm.xform(guide.node, ws=True, a = True, ro = data)
								elif chan == "S":
									data = pm.xform(guide.node, ws=True, a = True, s = data)
							except: pass
						else:
							try: guide.node.attr(chan.lower()).set(guide.node.attr(attrName).get())
							except: pass


				#check whether it is a custom guide, and a nurbs curve shape
				#if so, set the pose as the relevant nurbsCurve attr
				status, blkClassID = mnsUtils.validateAttrAndGet(guide, "blkClassID", False)
				if blkClassID and blkClassID == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_cgCtrl):
					guideShapeNode = guide.node.getShape()
					if guideShapeNode and type(guideShapeNode) == pm.nodetypes.NurbsCurve:
						attrName = poseSet + "_PoseShape"
						if guide.node.hasAttr(attrName):
							guide.node.attr(attrName) >> guideShapeNode.create
							attrsToDisconnect.append(guideShapeNode.create)

			if progressBar:
				progressBar.setValue(previousProgValue + addedPrgBarValue)
				previousProgValue += addedPrgBarValue

		pm.refresh()
		pm.disconnectAttr(attrsToDisconnect)

		pm.undoInfo(closeChunk=True)

def deletePoseForGuides(guides = [], poseSet = "T", **kwargs):
	"""Block's delete pose wrapper.
	"""

	if guides:
		progressBar = kwargs.get("progressBar", None)
		if progressBar: progressBar.setValue(0)
		addedPrgBarValue = 90.0 / float(len(guides))
		previousProgValue = 10.0

		for guide in guides:
			guide =  mnsUtils.validateNameStd(guide)
			if guide:
				for chan in "TRS":
					attrName = poseSet + "_Pose" + chan
					if guide.node.hasAttr(attrName):
						guide.node.attr(attrName).setLocked(False)
						guide.node.attr(attrName).delete()
			if progressBar:
				progressBar.setValue(previousProgValue + addedPrgBarValue)
				previousProgValue += addedPrgBarValue

def symmetrizeCGShape(mode = 0, direction = 0, cGuides = []):
	"""
	A simple method to symmetrize custom guides nurbs shapes when aplicable

		Mode=
			0: All
			1: Modules
			2: Branches
			3: selection

		Direction=
			0: L -> R
			1: R -> L
	"""

	#first validate data based on input params
	sourceSide = mnsPS_left
	symSide = mnsPS_right
	if direction == 1: 
		sourceSide = mnsPS_right
		symSide = mnsPS_left

	validatedGuides = []
	if not cGuides:
		#get cguides from sel
		sel = pm.ls(sl=True)
		if sel:
			if mode == 3:
				cGuides = sel
			else:
				rigTop = getRigTopForSel()
				if rigTop:
					moduleRoots = collectModuleRootsBasedOnMode(mode)
					for mRoot in moduleRoots:
						mRoot = mnsUtils.validateNameStd(mRoot)
						if mRoot.side == sourceSide:
							cGuides += getModuleDecendentsWildcard(mRoot, customGuidesOnly = True)

	errored = False
	if cGuides:
		rigTop, constructed = getRigTopForSel(getConstructionState = True)
		if rigTop and constructed:
			mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
			errored =True
		else:
			for guide in cGuides:
				guide = mnsUtils.validateNameStd(guide)
				if guide:
					#check whether it is a custom guide, and a nurbs curve shape
					#if so, store pose as a new nurbsCurve attr
					status, blkClassID = mnsUtils.validateAttrAndGet(guide, "blkClassID", False)
					if blkClassID and blkClassID == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_cgCtrl):
						guideShapeNode = guide.node.getShape()
						if guideShapeNode and type(guideShapeNode) == pm.nodetypes.NurbsCurve:
							if guide.side == sourceSide:
								validatedGuides.append(guide)
	if not errored:
		if validatedGuides:
			#data validated, execute
			origSelection = pm.ls(sl=1)

			for guide in validatedGuides:	
				symCtrl = mnsUtils.returnNameStdChangeElement(guide, side = symSide, autoRename = False)
				symNode = mnsUtils.checkIfObjExistsAndSet(symCtrl.name)
				if symNode:
					symCtrl.node = symNode
					newShapeTransform = pm.duplicate(guide.node)[0]
					pm.parent(newShapeTransform, w = True)
					newShapeTransform.inheritsTransform.set(True)

					#	- symmetrize it
					mirrorGrp = pm.createNode("transform", name = "tmpMirror")
					pm.parent(newShapeTransform, mirrorGrp)
					mirrorGrp.sx.set(mirrorGrp.sx.get() * -1)
					
					if not newShapeTransform.attr("tx").isLocked():
						pm.parent(newShapeTransform, symCtrl.node.getParent())
						pm.matchTransform(symCtrl.node, newShapeTransform)
					else:
						mnsUtils.lockAndHideAllTransforms(newShapeTransform, locked = False, keyable = True, cb = True)
						pm.parent(newShapeTransform, w = True)
						pm.makeIdentity(newShapeTransform, apply = True)
					bsp = pm.blendShape(newShapeTransform, symCtrl.node)[0]
					bsp.attr(newShapeTransform.nodeName()).set(1.0)
					pm.delete(symCtrl.node, ch = True)
					pm.delete([newShapeTransform, mirrorGrp])


			pm.select(origSelection, r = True)
			mnsLog.log("Custom Guides Shapes Symmetrized succesfully.", svr = 1)
		else:
			mnsLog.log("Couldn't find any Custom Guides Shapes to symmetrize. Please adjust input parameters and try again.", svr = 2)

###############################
###### defaults ###############
###############################

def resetControls(controls=[], **kwargs):
	"""reset all keyable attributes to default value.
	"""
	skipModuleVis = kwargs.get("skipModuleVis", False)

	pm.undoInfo(openChunk=True)
	if controls:
		for ctrl in controls:
			loadDefaultsForCtrl(ctrl, skipModuleVis = skipModuleVis)
	pm.undoInfo(closeChunk=True)
	
def setCurrentStateAsDefaultForCtrl(ctrl, **kwargs):
	"""Set custom defaults for keyable attributes for the given control, based on it's current state.
	"""

	ctrl = mnsUtils.validateNameStd(ctrl)
	uiStyleOsGrp = kwargs.get("uiStyleOsGrp", False)

	if ctrl and (ctrl.suffix == mnsPS_ctrl or uiStyleOsGrp):
		ctrlNode = ctrl.node

		defaultsDict = {}
		status, currentDefaults = mnsUtils.validateAttrAndGet(ctrlNode, "mnsDefaults", "")
		if currentDefaults: defaultsDict = json.loads(currentDefaults)

		attrList = ctrlNode.listAttr(k = True, v = True, se = True, l = False, u = True, s = True)
		if ctrl.name == "c_world_A001_ctrl":
			attrList = ctrlNode.listAttr(r = True, s = True, ud = True, cb = True)

		for attr in attrList:
			currentValue = attr.get()

			try: currentValue = round(currentValue, 3)
			except: pass

			defaultValue = currentValue
			if attr.attrName() in defaultsDict.keys():
				defaultValue = defaultsDict[attr.attrName()]
			else:
				defaultValues = pm.attributeQuery(attr.attrName(), node=ctrlNode, listDefault=True)
				if defaultValues: defaultValue = defaultValues[0]
				
			if currentValue != defaultValue:
				defaultsDict.update({attr.attrName(): currentValue})

			try: pm.addAttr(attr, e=1, dv = attr.get())
			except: pass

		if defaultsDict:
			defaultsString = json.dumps(defaultsDict)
			mnsUtils.addAttrToObj([ctrl], type = "string", value = defaultsString, name = "mnsDefaults", locked = True, replace = True)
		else:
			deleteDefaultsForCtrl(ctrl)

		if not uiStyleOsGrp:
			status, isUiStyle = mnsUtils.validateAttrAndGet(ctrl, "isUiStyle", False)
			if isUiStyle:
				setCurrentStateAsDefaultForCtrl(ctrl.node.getParent(), uiStyleOsGrp = True)

def gatherCustomDefaultDictForCtrl(ctrl):
	customDefaultsDict = {}
	ctrl = mnsUtils.validateNameStd(ctrl)
	if ctrl:
		ctrlNode = ctrl.node
		if ctrlNode.hasAttr("mnsDefaults"): customDefaultsDict = json.loads(ctrlNode.mnsDefaults.get())

	#return;dict (Custom Defaults Dict)
	return customDefaultsDict

def loadDefaultsForCtrl(ctrl, **kwargs):
	"""Load all default attributes for the given control, taking mnsDefaults (custom) into acount
	"""

	ctrl = mnsUtils.validateNameStd(ctrl)
	uiStyleOsGrp = kwargs.get("uiStyleOsGrp", False)
	skipModuleVis = kwargs.get("skipModuleVis", False)

	if ctrl and (ctrl.suffix == mnsPS_ctrl or uiStyleOsGrp):
		ctrlNode = ctrl.node

		customDefaultsDict = gatherCustomDefaultDictForCtrl(ctrl)

		for attr in ctrlNode.listAttr(k = True, v = True, se = True, l = False):
			if attr.attrName() != "v":
				skip = False
				if "_world_" in ctrl.name:
					try: 
						enums = attr.getEnums()
						if enums and 'none' in enums: skip = True
					except: pass

				if not skip and not uiStyleOsGrp:
					defaultValues = pm.attributeQuery(attr.attrName(), node=ctrlNode, listDefault=True)
					if defaultValues:
						try: attr.set(defaultValues[0]) 
						except: pass

		if customDefaultsDict:
			if "_world_" in ctrl.name and skipModuleVis:
				pass
			else:
				for defAttrName in customDefaultsDict.keys():
					if ctrlNode.hasAttr(defAttrName):
						try: ctrlNode.attr(defAttrName).set(customDefaultsDict[defAttrName])
						except: pass

		if not uiStyleOsGrp:
			status, isUiStyle = mnsUtils.validateAttrAndGet(ctrl, "isUiStyle", False)
			if isUiStyle:
				loadDefaultsForCtrl(ctrl.node.getParent(), uiStyleOsGrp = True)

def deleteDefaultsForCtrl(ctrl, **kwargs):
	"""Delete all set custom attributes for the given ctrl.
	"""

	force = kwargs.get("force", False)

	ctrl = mnsUtils.validateNameStd(ctrl)
	if ctrl and (ctrl.suffix == mnsPS_ctrl or force):
		status, isUiStyle = mnsUtils.validateAttrAndGet(ctrl, "isUiStyle", False)
		if isUiStyle and "Frame_" not in ctrl.node.nodeName():
			osGrp = getOffsetGrpForCtrl(ctrl)
			if osGrp:
				deleteDefaultsForCtrl(osGrp, force = True)

		ctrlNode = ctrl.node
		if ctrlNode.hasAttr("mnsDefaults"):
			ctrlNode.mnsDefaults.setLocked(False)
			pm.deleteAttr(ctrlNode, attribute = "mnsDefaults")

def setRigDefaults(mode = 0, **kwargs):
	"""Set controls custom defaults based on given state:
		0: All
		1: Modules
		2: Branches"""

	sel = pm.ls(sl=True)
	if sel:
		rigTop = getRigTopForSel()
		if rigTop:
			progressBar = kwargs.get("progressBar", None)
			if progressBar: progressBar.setValue(0)

			moduleRoots = collectModuleRootsBasedOnMode(mode)
			ctrls = getCtrlAuthFromRootGuides(moduleRoots)
			ctrls = collectCtrlRelatives(1, rootCtrls = ctrls)
			puppetRoot = getPuppetRootFromRigTop(rigTop)
			if puppetRoot: ctrls.append(puppetRoot)

			if ctrls:
				if progressBar: progressBar.setValue(5)
				addedPrgBarValue = 95.0 / float(len(ctrls))
				previousProgValue = 5.0

				for ctrl in ctrls:
					setCurrentStateAsDefaultForCtrl(ctrl)
					if progressBar:
						progressBar.setValue(previousProgValue + addedPrgBarValue)
						previousProgValue += addedPrgBarValue

			if progressBar: progressBar.setValue(100)
			mnsLog.log("Custom Defaults saved.", svr = 1)
			if progressBar: progressBar.setValue(0)

		else:
			mnsLog.log("Couldn't find Rig-Top from selection. Aborting.", svr = 1)
	else:
		mnsLog.log("Please select a rig component.", svr = 1)

def loadRigDefaults(mode = 0, **kwargs):
	"""Load controls predefined and custom defaults:
		0: All
		1: Modules
		2: Selected"""

	sel = pm.ls(sl=True)
	if sel:
		rigTop = getRigTopForSel()
		if rigTop:
			progressBar = kwargs.get("progressBar", None)
			if progressBar: progressBar.setValue(0)

			moduleRoots = collectModuleRootsBasedOnMode(mode)
			ctrls = getCtrlAuthFromRootGuides(moduleRoots)
			ctrls = collectCtrlRelatives(1, rootCtrls = ctrls)
			puppetRoot = getPuppetRootFromRigTop(rigTop)
			if puppetRoot: ctrls.append(puppetRoot)

			if ctrls:
				if progressBar: progressBar.setValue(5)
				addedPrgBarValue = 95.0 / float(len(ctrls))
				previousProgValue = 5.0

				for ctrl in ctrls:
					loadDefaultsForCtrl(ctrl)
					if progressBar:
						progressBar.setValue(previousProgValue + addedPrgBarValue)
						previousProgValue += addedPrgBarValue

			if progressBar: progressBar.setValue(100)	
			mnsLog.log("Custom Defaults loaded.", svr = 1)
			if progressBar: progressBar.setValue(0)

		else:
			mnsLog.log("Couldn't find Rig-Top from selection. Aborting.", svr = 1)
	else:
		mnsLog.log("Please select a rig component.", svr = 1)
					
def deleteRigDefaults(mode = 0, **kwargs):
	"""Load controls predefined and custom defaults:
		0: All
		1: Modules
		2: Selected"""

	sel = pm.ls(sl=True)
	if sel:
		rigTop = getRigTopForSel()
		if rigTop:
			progressBar = kwargs.get("progressBar", None)
			if progressBar: progressBar.setValue(0)

			moduleRoots = collectModuleRootsBasedOnMode(mode)
			ctrls = getCtrlAuthFromRootGuides(moduleRoots)
			ctrls = collectCtrlRelatives(1, rootCtrls = ctrls)
			puppetRoot = getPuppetRootFromRigTop(rigTop)
			if puppetRoot: ctrls.append(puppetRoot)

			for rGuide in moduleRoots:
				status, moduleDefaults = mnsUtils.validateAttrAndGet(rGuide, "moduleDefaults", None)
				if moduleDefaults:
					pm.PyNode(rGuide).attr("moduleDefaults").setLocked(False)
					pm.deleteAttr(rGuide, attribute = "moduleDefaults")
				
			if ctrls:
				if progressBar: progressBar.setValue(10)
				addedPrgBarValue = 90.0 / float(len(ctrls))
				previousProgValue = 10.0
				
				for ctrl in ctrls:
					deleteDefaultsForCtrl(ctrl)
					if progressBar:
						progressBar.setValue(previousProgValue + addedPrgBarValue)
						previousProgValue += addedPrgBarValue

			if progressBar: progressBar.setValue(100)
			mnsLog.log("Custom Defaults deleted.", svr = 1)
			if progressBar: progressBar.setValue(0)

		else:
			mnsLog.log("Couldn't find Rig-Top from selection. Aborting.", svr = 1)
	else:
		mnsLog.log("Please select a rig component.", svr = 1)

def gatherAllControlsCustomDefaults(rigTop):
	"""Gather custom defaults for all ctrls within the given rig.
	This method is used on rig deconstruction, to store all set default values, in order to restore them on construction.
	"""

	customAttributes = {}
	rigTop = mnsUtils.validateNameStd(rigTop)
	if rigTop:
		allCtrls = collectCtrls(rigTop)
		if allCtrls:
			for ctrlNode in allCtrls:
				customAttrDict = gatherCustomDefaultDictForCtrl(ctrlNode)
				if customAttrDict: customAttributes.update({ctrlNode.nodeName(): customAttrDict})
	
	#return;dict (All rig custom defaults)
	return customAttributes

def gatherModuleCustomDefaults(moduleTop):
	"""Gather custom defaults for all ctrls within the given module.
	This method is used on rig deconstruction, to store all set default values, in order to restore them on construction.
	"""

	customAttributes = {}
	moduleTop = mnsUtils.validateNameStd(moduleTop)
	if moduleTop and moduleTop.suffix == mnsPS_module:
		allCtrls = collectModuleControls(moduleTop, getUiStyleOsGrp = True)
		for ctrlNode in allCtrls:
			customAttrDict = gatherCustomDefaultDictForCtrl(ctrlNode)
			if customAttrDict: customAttributes.update({ctrlNode.nodeName(): customAttrDict})
	
	#return;dict (module custom defaults)
	return customAttributes

###############################
###### CONSTRUCT ##############
###############################

def getCtrlAuthFromRootGuide(rootGuide = None):
	rootGuide = mnsUtils.validateNameStd(rootGuide)
	if rootGuide:
		status, ctrlAuth = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
		ctrlAuth = mnsUtils.validateNameStd(ctrlAuth)
		if ctrlAuth: 
			return ctrlAuth

def getCtrlAuthFromRootGuides(rGuides = []):
	returnArray = []

	if rGuides:
		for rootGuide in rGuides:
			ctrlAuth = getCtrlAuthFromRootGuide(rootGuide)
			if ctrlAuth:
				returnArray.append(ctrlAuth)

	return returnArray

def collectModuleRootsBasedOnMode(mode = 0):
	"""
	0: All
	1: Branch
	2: Module
	"""

	partialRoots = []

	if len(pm.ls(sl=1)) > 0:
		for obj in pm.ls(sl=1):
			obj = mnsUtils.validateNameStd(obj)
			guideRoot = mnsUtils.validateNameStd(getModuleRoot(obj))

			if guideRoot:
				rigTop = getRigTop(guideRoot.node)
				baseGuide = getRootGuideFromRigTop(rigTop)

				if mode != 0 and baseGuide.node != guideRoot.node:
					if not guideRoot.name in partialRoots: partialRoots.append(guideRoot.name)
					if mode == 1:
						partialRoots += [obj.nodeName() for obj in guideRoot.node.listRelatives(ad = True) if obj.hasAttr("blkClassID") and obj.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl) and obj != baseGuide.node and obj.nodeName() not in partialRoots]
				else:
					partialRoots += [obj.nodeName() for obj in baseGuide.node.listRelatives(ad = True) if obj.hasAttr("blkClassID") and obj.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl) and obj != baseGuide.node and obj.nodeName() not in partialRoots]

	#return; list (root guides (modules) to build)
	return partialRoots

def collectCtrls(rigTop = None):
	"""Collect ALL related controls for th given rigTop.
	"""

	if rigTop: 
		rigTop = mnsUtils.validateNameStd(rigTop)
		ctrls = [c for c in rigTop.node.listRelatives(ad = True, type="transform") if mnsUtils.validateNameStd(c).suffix == mnsPS_ctrl]

		#return;list (controls)
		return ctrls

def collectCtrlRelatives(mode = 0, **kwargs):
	"""Collect ctrls based on given state:
		0: All
		1: Modules
		2: Selected"""

	ctrls = []
	sel = kwargs.get("rootCtrls", pm.ls(sl=True))
	if sel:
		rigTop = getRigTopForSel()
		rigTop = mnsUtils.validateNameStd(rigTop)

		if rigTop: 
			if mode == 0:
				ctrls = [c for c in rigTop.node.listRelatives(ad = True, type="transform") if mnsUtils.validateNameStd(c).suffix == mnsPS_ctrl]
			elif mode == 1:
				moduleTops = []
				for selectedObject in sel:
					selectedObject = mnsUtils.validateNameStd(selectedObject)
					if selectedObject:
						moduleTop = recGetModuleTopForCtrl(selectedObject)
						if moduleTop and moduleTop.node not in moduleTops:
							ctrls += [c for c in moduleTop.node.listRelatives(ad = True, type="transform") if mnsUtils.validateNameStd(c).suffix == mnsPS_ctrl]
							moduleTops.append(moduleTop.node)
			elif mode == 2:
				for selectedObject in sel:
					selectedObjectNS = mnsUtils.validateNameStd(selectedObject)
					if selectedObjectNS and selectedObjectNS.suffix == mnsPS_ctrl: ctrls.append(selectedObject)

	#return;list (controls)
	return ctrls

def getGlobalScaleAttrFromTransform(transform = None):
	"""This method is used to retreive any output decompose matrix node to be used as global scale input connection.
	If this method fails to retreive such attribute, it creates one and returns it.
	"""

	transform = mnsUtils.validateNameStd(transform)
	if transform:
		outConnections = transform.node.worldMatrix[0].listConnections(d = True, s = False)
		if outConnections:
			for outCon in outConnections:
				if outCon.type() == "decomposeMatrix":
					return outCon.outputScaleX
					break

		decMat = mnsNodes.decomposeMatrixNode(transform.node.worldMatrix[0], None,None,None)
		connectIfNotConnected(transform.node.worldMatrix[0], decMat.node.attr("inputMatrix"))
		
		#return; Attribute
		return decMat.node.outputScaleX

def collectModuleControls(moduleTop, **kwargs):
	"""Collect all related controls for the given module.
	"""

	getUiStyleOsGrp = kwargs.get("getUiStyleOsGrp", False)

	moduleTop = mnsUtils.validateNameStd(moduleTop)
	if moduleTop:
		controls = [c for c in moduleTop.node.listRelatives(ad = True, type="transform") if mnsUtils.validateNameStd(c).suffix == mnsPS_ctrl]
		if getUiStyleOsGrp:
			[controls.append(c.getParent()) for c in controls if c.hasAttr("isUiStyle") and c.isUiStyle.get() == True and not c.getParent() in controls]

		#return;list (controls)
		return controls

def deleteFreeJntGrpForModule(guideRoot = None, **kwargs):
	keepCurrentFreeJntsGrp = kwargs.get("keepCurrentFreeJntsGrp", False)

	guideRoot = mnsUtils.validateNameStd(guideRoot)
	if guideRoot:
		if guideRoot.node.hasAttr("freeJointsGrp"):
			existingFreeJntsGrp = guideRoot.node.attr("freeJointsGrp").get()
			if existingFreeJntsGrp and not keepCurrentFreeJntsGrp: pm.delete(existingFreeJntsGrp)

def handleInterpLocsStructureReturn(rigTop = None, interpLocs = [], guides = [], **kwargs):
	addSuffix = kwargs.get("addSuffix", "Main")
	keepCurrentFreeJntsGrp = kwargs.get("keepCurrentFreeJntsGrp", False)

	if type(interpLocs) == dict:
		for addSuffixKey in interpLocs:
			handleInterpLocsStructureReturn(rigTop, interpLocs[addSuffixKey], guides, addSuffix = addSuffixKey, keepCurrentFreeJntsGrp = keepCurrentFreeJntsGrp)
			keepCurrentFreeJntsGrp = True
		return

	if guides:
		guideRoot = guides[0]
		deleteFreeJntGrpForModule(guideRoot, keepCurrentFreeJntsGrp = keepCurrentFreeJntsGrp)

		if interpLocs and rigTop:
			rigTopFreeJntsGrp = None
			if rigTop.node.hasAttr("freeJointsGrp"): rigTopFreeJntsGrp = rigTop.node.attr("freeJointsGrp").get()
			
			if rigTopFreeJntsGrp:
				freeJntsGrp = None
				if guideRoot.node.hasAttr("freeJointsGrp"):
					freeJntsGrp = mnsUtils.validateNameStd(guideRoot.node.attr("freeJointsGrp").get())
				if not freeJntsGrp:
					freeJntsGrp = mnsUtils.createNodeReturnNameStd(side = guideRoot.side, body = guideRoot.body, alpha = guideRoot.alpha, id = guideRoot.id, buildType = "freeJointsGrp", createBlkClassID = True)
					if freeJntsGrp: pm.parent(freeJntsGrp.node, rigTopFreeJntsGrp)
					freeJntsGrp.node.v.set(False)
					mnsUtils.addAttrToObj([guideRoot.node], type = "message", value = freeJntsGrp.node, name = "freeJointsGrp", replace = True)

				#constraintGrp
				#if not freeJntsGrp.node.t.isConnected():
				#	mnsNodes.mnsMatrixConstraintNode(side = guideRoot.side, body = guideRoot.body + "FJC", alpha = guideRoot.alpha, id = guideRoot.id, targets = [freeJntsGrp.node], sources = [guideRoot.node], maintainOffset = True)

				gScale = mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]
				prevJoint = getRelatedNodeFromObject(guideRoot.node.getParent())
				prevJointRadius = None
				if prevJoint:
					prevJointRadius = prevJoint.radius.get()

				builtJoints = []
				k = 0
				for node in interpLocs:
					connectSlaveToDeleteMaster(node, guideRoot)
					pm.parent(node, freeJntsGrp.node)

					interpJnt = mnsUtils.createNodeReturnNameStd(side = guideRoot.side, body = guideRoot.body + addSuffix, alpha = guideRoot.alpha, id = 1, buildType = "interpolationJoint", incrementAlpha = False)
					
					if prevJointRadius is None:
						interpJnt.node.radius.set(gScale)
					else:
						interpJnt.node.radius.set(prevJointRadius)
				
					mnsNodes.mnsMatrixConstraintNode(side = guideRoot.side, alpha = guideRoot.alpha, id = guideRoot.id, targets = [interpJnt.node], sources = [node])
					mnsNodes.mnsNodeRelationshipNode(master = node, slaves = [interpJnt])

					parentGuideIdx = int(math.floor((float(len(guides)) / float(len(interpLocs))) * k))
					pm.parent(interpJnt.node, guides[parentGuideIdx].node.attr("jntSlave").get())
					mnsUtils.zeroJointOrient(interpJnt.node)
					if rigTop.node.hasAttr("jntStructHandles"): rigTop.node.attr("jntStructHandles") >> interpJnt.node.attr("displayLocalAxis")
					k += 1

def getModuleScale(MnsBuildModule):
	return MnsBuildModule.rigTop.node.assetScale.get() * MnsBuildModule.rootGuide.node.controlsMultiplier.get() * mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]
	#

def getExistingCpomNodeFromSurface(surface):
	nodeReturn = None
	surface = mnsUtils.checkIfObjExistsAndSet(surface)
	if surface:
		surfaceShape = mnsMeshUtils.getShapeFromTransform(surface)
		if surfaceShape:
			outAttr = None
			if type(surfaceShape) == pm.nodetypes.Mesh:
				outAttr = surfaceShape.worldMesh
			elif type(surfaceShape) == pm.nodetypes.NurbsSurface:
				outAttr = surfaceShape.worldSpace[0]

			if outAttr:
				outCons = outAttr.listConnections(s = True)
				for outCon in outCons:
					if type(outCon) == pm.nodetypes.MnsClosestPointsOnMesh:
						nodeReturn = outCon
						break
	return nodeReturn

def constrainObjectsToSurface(MnsBuildModule = None, ctrlMasters = [], jointsToAttach = [], surface = None):
	returnCtrls = []
	if surface and len(ctrlMasters) == len(jointsToAttach):
		newCtrls = []
		newCtrlOffsets = []
		modScale = getModuleScale(MnsBuildModule)

		for ctrl in (ctrlMasters):
			ctrlOffsetGrp = getOffsetGrpForCtrl(ctrl)
			if ctrlOffsetGrp:
				newctrl = blkCtrlShps.ctrlCreate(nameReference = ctrl,
												blkCtrlTypeID = 2,
												body = ctrl.body + "AlongSrf",
												color = getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
												matchTransform = ctrl.node,
												controlShape = "diamond",
												scale = modScale * 0.3, 
												parentNode = ctrlOffsetGrp,
												createOffsetGrp = True)

				newCtrls.append(newctrl)
				newCtrlOffsets.append(getOffsetGrpForCtrl(newctrl))

		if len(newCtrls) == len(ctrlMasters):
			cpom = mnsNodes.mnsClosestPointsOnMeshNode(
												side = ctrl.side, 
												alpha = ctrl.alpha, 
												id = ctrl.id,  
												inputMesh = surface,
												inputTransforms = ctrlMasters,
												outputTransforms = newCtrlOffsets
												)

			for k, ctrl in enumerate(newCtrls):
				pm.delete(pm.parentConstraint(jointsToAttach[k], ctrl.node))
				modGrp = mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp")
				jointsToAttach[k].t.disconnect()
				mnsNodes.mnsMatrixConstraintNode(sources = [ctrl.node], targets = [jointsToAttach[k]], connectRotate = False, connectTranslate = True, connectScale = False, maintainOffset = True)
				mnsUtils.lockAndHideTransforms(ctrl.node, tx = False, ty = False, tz = False, lock = True)
				
			returnCtrls = newCtrls

	#return; list (new ctrls)
	return returnCtrls

def convertModuleAuthorityToSurface(MnsBuildModule):
	newCtrls = []

	if MnsBuildModule:
		rootGuide = MnsBuildModule.rootGuide
		status, alongSurface =  mnsUtils.validateAttrAndGet(rootGuide, "alongSurface", "")
		if alongSurface: alongSurface = mnsUtils.checkIfObjExistsAndSet(alongSurface)

		if alongSurface:
			jointsToAttach = []
			ctrlMasters = []

			for ctrl in MnsBuildModule.allControls:
				status, guideAuthority = mnsUtils.validateAttrAndGet(ctrl, "guideAuthority", None)
				if guideAuthority:
					status, jntSlave = mnsUtils.validateAttrAndGet(guideAuthority, "jntSlave", None)
					if jntSlave: 
						ctrlMasters.append(ctrl)
						jointsToAttach.append(jntSlave)
			
			if ctrlMasters:
				newCtrls = constrainObjectsToSurface(MnsBuildModule, ctrlMasters, jointsToAttach, alongSurface)

	#return; list (new ctrls)
	return newCtrls

def connectIfNotConnected(attrA, attrB):
	if not attrA.isConnectedTo(attrB):
		attrA >> attrB

def convertInputObjToSpace(obj = None):
	eSpace = mnsUtils.validateNameStd(obj)
	if eSpace:
		#handleJnts
		if eSpace.suffix == mnsPS_rJnt or eSpace.suffix == mnsPS_jnt or eSpace.suffix == mnsPS_iJnt:
			if eSpace.node:
				return eSpace.node

		#handleGuides
		elif eSpace.suffix == mnsPS_gRootCtrl or eSpace.suffix == mnsPS_gCtrl or  eSpace.suffix == mnsPS_cgCtrl:
			if eSpace.node.ctrlAuthority.get():
				return eSpace.node.ctrlAuthority.get()

	#return; PyNode (Space object if found)

###############################
###### PUPPET #################
###############################

def deletePuppetName(rigTop, **kwargs):
	"""This method will filter and delete the rigTops' puppet curves title.
	"""

	if rigTop:
		puppetRoot = getPuppetRootFromRigTop(rigTop)
		if puppetRoot:
			for s in puppetRoot.node.getShapes():
				if "titleShape" in s.nodeName(): pm.delete(s)

def namePuppet(rigTop, **kwargs):
	"""This method is used to create the rig's curves puppet title and connect it to to it's world control as additional shape nodes.
	"""

	if rigTop:
		zUpAxis = False
		currentUpAxis = pm.upAxis(q=True, axis=True)
		if currentUpAxis == "z": zUpAxis = True

		puppetRoot = getPuppetRootFromRigTop(rigTop)
		guideBase = getRootGuideFromRigTop(rigTop)
		if puppetRoot:
			if rigTop.node.hasAttr("characterName"):
				deletePuppetName(rigTop)
				
				name = rigTop.node.attr("characterName").get()
				transformTemp = pm.group(empty = True, name = "tempName")
				textRet = pm.PyNode(pm.textCurves(t=name)[0])
				pm.makeIdentity([textRet] + textRet.listRelatives(ad = True), apply=True)
				allShapes = textRet.listRelatives(ad = True, type = "nurbsCurve")
				for shape in allShapes: pm.parent(shape, transformTemp, r = 1, shape = 1)
				pm.delete(transformTemp, ch = True)
				pm.delete(textRet)

				if not zUpAxis: transformTemp.rx.set(-90)

				pm.makeIdentity(transformTemp, apply=True)
				pm.xform(transformTemp, cp= True)
				ttG = pm.group(empty = True)
				pm.delete(pm.pointConstraint(ttG, transformTemp))
				pm.delete(ttG)
				pm.makeIdentity(transformTemp, apply=True)
				textBb = transformTemp.getBoundingBox()
				titleDup = pm.duplicate(puppetRoot.node)[0]

				pm.delete(titleDup.getShapes()[0]) 
				titleDupABbb = pm.duplicate(titleDup)[0]
				titleDupABbb.t.set(0,0,0)
				titleDupABbb.r.set(0,0,0)
				origHeight = titleDupABbb.getBoundingBox().depth()
				origWidth = titleDupABbb.getBoundingBox().width()
				
				if zUpAxis:
					origHeight = titleDupABbb.getBoundingBox().height()
					origWidth = titleDupABbb.getBoundingBox().width()

				pm.delete(titleDupABbb)
				pm.xform(titleDup, cp=1)

				transformTempA = pm.group(empty = True, name = "tempNameA")
				pm.delete(pm.parentConstraint(titleDup, transformTempA))
				titleBoxBb = titleDup.getBoundingBox()
				allShapes = transformTemp.listRelatives(ad = True, type = "nurbsCurve")
				for shape in allShapes: pm.parent(shape, transformTempA, r = 1, shape = 1)
				pm.delete(transformTemp)
				
				scaleFactorA = 1.0
				scaleFactorB = 1.0

				if not zUpAxis:
					scaleFactorA = origHeight / textBb.depth() * 0.7    
					scaleFactorB = origWidth / textBb.width() * 0.8
				else:
					scaleFactorA = origHeight / textBb.height() * 0.7    
					scaleFactorB = origWidth / textBb.width() * 0.8

				scaleFactor = min(scaleFactorA, scaleFactorB)
				if scaleFactor != 0: transformTempA.s.set((scaleFactor,scaleFactor,scaleFactor))

				for shape in transformTempA.getShapes(): 
					pm.parent(shape, titleDup, shape = True, a = True)
					pm.makeIdentity(shape.getParent(), apply=True)
					pm.parent(shape, puppetRoot.node, shape = True, r = True)
					pm.rename(shape, "titleShape")
				pm.delete(titleDup, transformTempA)
				mnsUtils.connectShapeColorRGB(guideBase, puppetRoot)

				pm.select(puppetRoot.node)

def removeAllAuthority(slave = None, **kwargs):
	"""This method is used to delete all 'Authority' from the passsed in slave, if there are any.
	"""

	if slave:
		slave = mnsUtils.validateNameStd(slave)
		oldAuthority = getRelationMasterFromSlave(slave)

		if slave.node.hasAttr("masterIn"): slave.node.masterIn.disconnect()
		if slave.node.hasAttr("deleteMaster"): slave.node.deleteMaster.disconnect()
		
		inputs = list(dict.fromkeys(slave.node.listConnections(p = True)))
		collectAdjusted = []
		for i in inputs:
			if i.nodeType() == "mnsMatrixConstraint":
				if i.plugNode() not in collectAdjusted: collectAdjusted.append(i.plugNode())
				if "sourceWorldMatrix" not in str(i): 
					toCon = i.listConnections(p = True)
					for con in toCon:
						if con.plugNode() == slave.node:
							try: pm.disconnectAttr(i, con)
							except:
								try: pm.disconnectAttr(con, i)
								except: pass
		for n in collectAdjusted:
			if not n.listConnections(d = True, s = False): pm.delete(n)
		
		#return;MnsNameStd (oldAuthority)
		return oldAuthority

def transferAuthorityToCtrl(slave = None, ctrlMaster = None, **kwargs):	
	"""This is a very important method used in BLOCK cosntruction.
	This method will find the current 'guide control' from the given joint slave. and transfer it's authority to a newly created 'control authority'.
	This method will be called on every module build and it is the main trigger to flag a module construction.
	The 'authority' attribute for every guide or control is used to distiguish the module state, and jnt state.
	When transfering an authority to a ctrl, a 'old authority' attr (of sort) is created, in order for the procedural 'deconstruct' to look for and tranfer the jnt authority back to it's orignal guide, 
	before deleting the constructed module.
	See also parallel: 'transferAuthorityToGuide' Method."""

	connectScale = kwargs.get("connectScale", True) #arg
	maintainOffset = kwargs.get("maintainOffset", True) #arg

	slave = mnsUtils.validateNameStd(slave)
	ctrlMaster = mnsUtils.validateNameStd(ctrlMaster)

	if slave and ctrlMaster:
		oldAuthority = removeAllAuthority(slave)
		mnsNodes.mnsMatrixConstraintNode(maintainOffset = maintainOffset, side = slave.side, alpha = slave.alpha , id = slave.id, targets = [slave.node], sources = [ctrlMaster.node], connectScale = connectScale)
		attr = mnsUtils.addAttrToObj([ctrlMaster.node], type = "message", name = "guideAuthority", value= oldAuthority.node, replace = True)[0]
		attr = mnsUtils.addAttrToObj([oldAuthority.node], type = "message", name = "ctrlAuthority", value= ctrlMaster.node, replace = True)[0]

def transferAuthorityToGuide(ctrl = None, **kwargs):	
	"""This is a very important method used in BLOCK de-construction.
	This method will find the current 'control' from the given joint slave. and transfer it's authority to a it's original 'guide' authority.
	This method will be called procedurally on any module deconstruction, before deleting the constructed module.
	See also parallel: 'transferAuthorityToCtrl' Method.
	"""

	ctrl = mnsUtils.validateNameStd(ctrl)

	if ctrl:
		if ctrl.node.hasAttr("guideAuthority"):
			guideAuthority =  mnsUtils.validateNameStd(ctrl.node.guideAuthority.get())
			if guideAuthority.node.hasAttr("jntSlave"):
				jntSlave = mnsUtils.validateNameStd(guideAuthority.node.jntSlave.get())
				if jntSlave:
					removeAllAuthority(jntSlave)
					mnsNodes.mnsMatrixConstraintNode(side = guideAuthority.side, alpha = guideAuthority.alpha , id = guideAuthority.id, targets = [jntSlave.node], sources = [guideAuthority.node], connectScale = False)
					mnsUtils.setAttr(jntSlave.node.scale, (1.0,1.0,1.0))
					for axis in "xyz": mnsUtils.setAttr(jntSlave.node.attr("s" + axis), 1.0)

					ndr = getNodeRelationshipNodeFromObject(guideAuthority)
					if ndr: mnsNodes.connectAttrAttempt(ndr.attr("messageOut"), jntSlave.node.attr("masterIn"))
					else: mnsNodes.mnsNodeRelationshipNode(side = guideAuthority.side, alpha = guideAuthority.alpha , id = guideAuthority.id, master = guideAuthority.node, slaves = [jntSlave.node])

def getOffsetGrpForCtrl(ctrl, **kwargs):
	"""Collect the offsetGroup related to the passed in control, if it exists.
	"""

	grpType = kwargs.get("type", "offsetGrp") #arg; optionBox = offsetGrp, spaceSwitchGrp
	
	ctrl = mnsUtils.validateNameStd(ctrl)
	if ctrl:
		par = ctrl.node.getParent()
		par = mnsUtils.validateNameStd(par)
		if par:
			if par.body == ctrl.body:
				if grpType == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, par.suffix):
					return par
				else:
					return getOffsetGrpForCtrl(par, type = grpType)
			else: 
				return None
		else: 
			return None
	else: 
		return None
	#return;MnsNameStd (offset group)

def getModuleTopForCtrl(ctrl = None, nameMatch = None):
	"""Collect the 'Module Top Group' related to the passed in control.
	"""

	ctrl = mnsUtils.validateNameStd(ctrl)

	if ctrl:
		if not nameMatch: nameMatch = mnsUtils.returnNameStdChangeElement(ctrl, id = 1, suffix = mnsPS_module, autoRename = False)
		if nameMatch:
			par = mnsUtils.validateNameStd(ctrl.node.getParent())
			if par:
				if par.name == nameMatch.name:
					return par
				elif par.suffix != mnsPS_puppet:
					return getModuleTopForCtrl(par, nameMatch)
				else:
					return None
			else:
				return None
	#return;MnsNameStd (Module Top Group)

def recGetModuleTopForCtrl(ctrl = None):
	"""Recursively attempt to collect the 'Module Top Group' related to the ctrl passed in within it's related parents.
	"""

	ctrl = mnsUtils.validateNameStd(ctrl)
	if ctrl:
		if ctrl.node.hasAttr("blkClassID") and ctrl.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_module):
			return ctrl
		else: return recGetModuleTopForCtrl(ctrl.node.getParent())
	#return;MnsNameStd (Module Top Group)

def getModuleTopFromRootGuide(rootGuide = None):
	"""Attempt to collect 'Module Top Group' from a given root guide.
	"""

	rootGuide = mnsUtils.validateNameStd(rootGuide)

	if rootGuide:
		if rootGuide.node.hasAttr("ctrlAuthority"):
			ctrl = mnsUtils.validateNameStd(rootGuide.node.ctrlAuthority.get())
			nameMatch = mnsUtils.returnNameStdChangeElement(rootGuide, id = 1, suffix = mnsPS_module, autoRename = False)
			return getModuleTopForCtrl(ctrl, nameMatch)
		else: return None
	else: return None
	#return;MnsNameStd (Module Top Group)

def extractControlShapes(ctrls = [], rigTop = None, **kwargs):
	"""Trigger method for BLOCK - 'extract control shapes' method.
	   This method will extract and store the current state of control shapes within the given rig (rigTop).
	   The extracted shapes will be re-constructed once a rig-rebuild is initiated.
	   In case of any control shape already exists, it will be replaced by default."""

	tempExtract = kwargs.get("tempExtract", False)
	progressBar = kwargs.get("progressBar", None)

	if rigTop:
		rigTop = mnsUtils.validateNameStd(rigTop)
		if rigTop:
			csGrp = getCsGrpFromRigTop(rigTop)
			if csGrp:
				returnCtrls = []
				existingShapes = [c.nodeName() for c in csGrp.node.listRelatives(ad = True, type = "transform")]
				addedPrgBarValue = 90.0 / float(len(ctrls))
				previousProgValue = 10.0
				defaultSaveIgnore = []

				for k, ctrl in enumerate(ctrls):
					ctrl = mnsUtils.validateNameStd(ctrl)
					status, isUiStyle = mnsUtils.validateAttrAndGet(ctrl, "isUiStyle", False)

					if not isUiStyle:
						newSuffix = mnsPS_ctrlShape
						if tempExtract: newSuffix += "Temp"
						name = mnsUtils.returnNameStdChangeElement(ctrl, suffix = newSuffix, autoRename = False)
						if name.name in existingShapes:
							pm.delete(name.name)

						controlShape = mnsUtils.validateNameStd(pm.duplicate(ctrl.node, name = name.name)[0])
						for chan in "trs":
							for axis in "xyz":
								attr = controlShape.node.attr(chan + axis)
								attr.setLocked(False)

						pm.delete(controlShape.node.listRelatives(c = True, type = "transform"))

						if not controlShape.node.getShape():
							pm.delete(controlShape.node)
						else:
							controlShape.node.v.setLocked(False)
							controlShape.node.v.set(True)

							if not tempExtract:
								guideAuthority = None

								if controlShape.node.hasAttr("blkClassID"):
									controlShape.node.blkClassID.setLocked(False)
									controlShape.node.blkClassID.set(mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_ctrlShape))
									controlShape.node.blkClassID.setLocked(True)
								pm.parent(controlShape.node, csGrp.node)

								rGuide = getRootGuideFromCtrl(ctrl)
								if rGuide: 
									rGuideAttr = mnsUtils.addAttrToObj([controlShape.node], type = "message", name = "rootGuide", value= "", replace = True)[0]
									rGuide.node.message >> rGuideAttr 
							else:
								pm.parent(controlShape.node, w = True)

							returnCtrls.append(controlShape)
					elif "Frame_" not in ctrl.node.nodeName():
						#defult save
						setCurrentStateAsDefaultForCtrl(ctrl)

						#get parent Ctrl
						uiStyleOsGrp =getOffsetGrpForCtrl(ctrl)
						if uiStyleOsGrp:
							parentCtrl = mnsUtils.validateNameStd(uiStyleOsGrp.node.getParent())
							if parentCtrl and parentCtrl.suffix == mnsPS_ctrl and parentCtrl.node not in defaultSaveIgnore:
								setCurrentStateAsDefaultForCtrl(parentCtrl)
								defaultSaveIgnore.append(parentCtrl.node)

					if progressBar: 
						progressBar.setValue(previousProgValue + addedPrgBarValue)
						previousProgValue += addedPrgBarValue
						
				#return;list (controls)
				return returnCtrls

def buildShapes(ctrls = [], rigTop = None, **kwargs):
	"""This method will be called from a rig construction.
	   This method will look for any contol shapes stored within the given rig (rigTop), and replace the default shapes with any corresponding control shape.
	   Shape replacement method will be done according to the 'mode' flag (relative/absulote)."""

	shapesMode = kwargs.get("mode", 0) #arg; 
	tempExtract = kwargs.get("tempExtract", False)

	if ctrls and rigTop:
		csGrp = getCsGrpFromRigTop(rigTop)
		ctrlShapes = [mnsUtils.validateNameStd(c).name for c in csGrp.node.listRelatives(ad = True, type = "transform") if mnsUtils.validateNameStd(c).suffix == mnsPS_ctrlShape]

		if ctrlShapes or tempExtract:
			for ctrl in ctrls:
				if ctrl.suffix == mnsPS_ctrl:
					ctrl = mnsUtils.validateNameStd(ctrl)
					newSuffix = mnsPS_ctrlShape
					if tempExtract: newSuffix += "Temp"
					shapeName = mnsUtils.returnNameStdChangeElement(ctrl, suffix = newSuffix, autoRename = False).name
					if shapeName in ctrlShapes or tempExtract:
						controlShape = mnsUtils.validateNameStd(shapeName)
						if controlShape.node.getShape():
							vAttrConnectionRestore = None
							if ctrl.node.getShape(): 
								inputConnections = ctrl.node.getShape().v.listConnections(d = False, s = True, p = True)
								if inputConnections: vAttrConnectionRestore = inputConnections[0]

								pm.delete(ctrl.node.getShapes())
							tempShapeDup = pm.duplicate(controlShape.node)[0]
							if shapesMode == 1: 
								for chan in "trs":
									for axis in "xyz":
										attr = tempShapeDup.attr(chan + axis)
										attr.setLocked(False)

								pm.parent(tempShapeDup, ctrl.node.getParent())
								pm.makeIdentity(tempShapeDup, apply = True)

							#parent
							for s in tempShapeDup.getShapes():
								pm.parent(s, ctrl.node, r = True, s = True)
								if vAttrConnectionRestore: vAttrConnectionRestore >> s.v

							pm.delete(tempShapeDup)
							mnsUtils.fixShapesName([ctrl])

def getExistingSpaceConstraintForControl(ctrl = None):
	"""Collect existing 'spaces' constraints for a passed in (built) control, in order to re-build them in turn, after correct filtering and validation (in case of a partial build for example).
	"""

	if ctrl:
		matConstraints = []
		ctrl = mnsUtils.validateNameStd(ctrl)
		if ctrl:
			ssGrp = getOffsetGrpForCtrl(ctrl, type = "spaceSwitchGrp")
			if ssGrp:
				[matConstraints.append(input) for input in ssGrp.node.listConnections(d = True, s= True) if input not in matConstraints]
				#return;list (mnsMatrixConstraint nodes)
				return matConstraints
				
def getExistingSpaceConstraintForControls(controls = []):
	"""Wrapper mwthod to collect 'spaces' constraints for multiple controls.
	"""

	returnState = {} 
	if controls:
		if type(controls) != list: controls = [controls]
		for ctrl in controls:
			ctrl = mnsUtils.validateNameStd(ctrl)
			if ctrl:
				matConstraints = getExistingSpaceConstraintForControl(ctrl)
				if matConstraints:
					returnState.update({ctrl.node.nodeName(): [ctrl, matConstraints]})

	#return;dict (constraintSpaces dictionary)
	return returnState

def createVisibilityBridgeMdl(source = None, target = None):
	"""This method will check wether the 'target' has a visibility channel connection.
	   In the case the given 'target' has input visibility connection, a 'bridge' multiplyDoubleLinear node will be created.
	   The brigde node will accomidate both sources as an input, instead of replacing the original visibility by simple multiplication.
	   By creating the 'bridge', both old and new sources will be kept as drivers, setting the visibility to 'False' if ANY of the given sources is 'False'.
	   In case there is no connection input to the target's visibility channel, a simple connection will be made using the input source."""

	if source and target:
		if type(source) is pm.general.Attribute and type(target) is pm.general.Attribute:
			currentInputs = pm.listConnections(target, s = True, p =True)
			if currentInputs:
				currentInput = currentInputs[0]
				target.disconnect()
				mnsNodes.mdlNode(source, currentInput, target)
			else: 
				source >> target

def createAndConnectModuleVisChannelsToPuppetRootCtrl(moduleTopNode = None):
	"""
	This method will create and connect the pedefined visibility graph to a given 'Module Top Group'.
	The driver attribute will be created within the puppet's 'world control', and the connection graph (using animCurvesUU node) will input into the group's visibility channels.
	The channels are split (predefined) as follows:

	0. None
	1. primaries
	2. Secondaries
	3. Tertiaries
	4. Secondaries Only
	5. Tertiaries Only
	6. No Primaries
	"""

	moduleTopNode = mnsUtils.validateNameStd(moduleTopNode)
	if moduleTopNode:
		rigTop = getRigTop(moduleTopNode.node)
		if rigTop:
			puppetRoot = getPuppetRootFromRigTop(rigTop)
			if puppetRoot:
				if not puppetRoot.node.hasAttr("moduleVis"): devider = mnsUtils.addAttrToObj([puppetRoot.node], type = "enum", value = ["______"], name = "moduleVis", replace = True,  locked= True)
				moduleAttr = mnsUtils.addAttrToObj([puppetRoot.node], type = "enum", value = ["none", "primeries", "secondaries", "tertiaries", "secondariesOnly", "tertiariesOnly", "noPrimaries", "noSecondaries"], name = moduleTopNode.side + "_" + moduleTopNode.body + "_" + moduleTopNode.alpha, replace = True, keyable = False)[0]

				modVisNode = mnsUtils.createNodeReturnNameStd(side = moduleTopNode.side, body = moduleTopNode.body, alpha = moduleTopNode.alpha, id = moduleTopNode.id, buildType = "mnsModuleVis", incrementAlpha = False)
				moduleAttr >> modVisNode.node.inputVisibility
				modVisNode.node.primaryVis >> moduleTopNode.node.primaryVis
				modVisNode.node.secondaryVis >> moduleTopNode.node.secondaryVis
				modVisNode.node.tertiaryVis >> moduleTopNode.node.tertiaryVis

				moduleAttr.set(3)
				return None

def removeModuleVisAttrFromPuppetTop(moduleTopNode = None, puppetTop = None):
	"""This method will remove the corresponding "module vis" channel from the given puppet base control.
	   This method is used when a 'partial deconstruction' is initiated, keeping only relevant vis channels in place, removing the 'deconstructed' modules vis channels."""

	moduleTopNode =  mnsUtils.validateNameStd(moduleTopNode)
	puppetTop =  mnsUtils.validateNameStd(puppetTop)

	if moduleTopNode and puppetTop:
		attrName = moduleTopNode.side + "_" + moduleTopNode.body + "_" + moduleTopNode.alpha
		if puppetTop.node.hasAttr(attrName):
			pm.deleteAttr(puppetTop.node, attribute = attrName)

def getRootGuideFromCtrl(obj):
	"""Attempt to collect the related 'rootGuide' from the given control passed in.
	"""

	if obj:
		obj = mnsUtils.validateNameStd(obj)
		if obj:
			if obj.node.nodeName() == "c_world_A001_ctrl":
				if obj.node.hasAttr("guideAuthority"):
					rootGuide = mnsUtils.validateNameStd(obj.node.attr("guideAuthority").get())
					return rootGuide
			elif obj.node.hasAttr("blkClassID") and obj.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_ctrl):
				moduleTop = recGetModuleTopForCtrl(obj)
				if moduleTop:
					rootGuide = searchForRootGuideInRelatives(moduleTop)
					#return;MnsNameStd (rootGuide)
					return rootGuide

def locateCnsForCtrl(ctrl = None, **kwargs):
	masterOnly = kwargs.get("masterOnly", False)
	slaveOnly = kwargs.get("slaveOnly", False)

	ctrl = mnsUtils.validateNameStd(ctrl)
	
	returnCtrl = ctrl
	if ctrl:
		if not slaveOnly:
			status, cnsMaster = mnsUtils.validateAttrAndGet(ctrl, "cnsMaster", None)
			if cnsMaster: returnCtrl = cnsMaster

		if not masterOnly:
			status, cnsSlave = mnsUtils.validateAttrAndGet(ctrl, "cnsSlave", None)
			if cnsSlave: returnCtrl = cnsSlave

	return returnCtrl

def getOppositeSideControl(obj = None):
	"""Attempt to collect the opposite related mns object if it exists.
		Only non 'ceneter components' will be tested of course."""

	obj = locateCnsForCtrl(obj)
	obj = mnsUtils.validateNameStd(obj)

	if obj:
		if obj.side == mnsPS_cen: return False
		else:
			symSide = mnsPS_right
			if obj.side == mnsPS_right: symSide = mnsPS_left

			newStd = mnsUtils.returnNameStdChangeElement(obj, side = symSide, autoRename = False)
			existingNode = mnsUtils.checkIfObjExistsAndSet(obj = newStd.name, namespace = obj.namespace)
			if existingNode: 
				existingNode = locateCnsForCtrl(existingNode)
				#return;MnsNameStd (Opposite object)
				return mnsUtils.validateNameStd(existingNode)

def getModuleRootCtrl(obj = None):
	obj = mnsUtils.validateNameStd(obj)
	if obj:
		moduleTop = recGetModuleTopForCtrl(obj)
		if moduleTop:
			for child in moduleTop.node.listRelatives(ad = True, type = "transform"):
				if "ModuleRoot_" in child.nodeName(): return mnsUtils.validateNameStd(child)

def getModuleAnimGrp(obj = None):
	obj = mnsUtils.validateNameStd(obj)
	if obj:
		moduleTop = recGetModuleTopForCtrl(obj)
		if moduleTop:
			for child in moduleTop.node.listRelatives(ad = True, type = "transform"):
				if "Anim_" in child.nodeName() and child.nodeName().endswith("_techCtl"): 
					return mnsUtils.validateNameStd(child)
					break

def getSimpleRivetsNodeForMesh(mesh = None):
	mesh = mnsUtils.checkIfObjExistsAndSet(mesh)
	if mesh:
		outConnections = mesh.worldMatrix[0].listConnections(d = True, s = False)
		if outConnections:
			for outCon in outConnections:
				if outCon.type() == "mnsSimpleRivets":
					return outCon

		simpleRivetsNode = mnsNodes.mnsSimpleRivetsNode(inputMesh = mesh)

		#return; PyNode
		return simpleRivetsNode.node

def muteLocalTransformations(ctrl = None, **kwargs):
	ctrl = mnsUtils.validateNameStd(ctrl)
	if ctrl:
		modGrp = mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp")
		decMat = mnsNodes.decomposeMatrixNode(ctrl.node.inverseMatrix, None,None,None)

		translate = kwargs.get("t", True)
		rotate = kwargs.get("r", True)
		scale = kwargs.get("s", True)

		if translate: decMat.node.outputTranslate >> modGrp.node.t
		if rotate: decMat.node.outputRotate >> modGrp.node.r
		if scale: decMat.node.outputScale >> modGrp.node.s

def matchKeyableAttributes(source = None, target = None):
	if source and target:
		attrs = source.listAttr(k = True)
		for attr in attrs:
			try:
				target.attr(attr.attrName()).set(attr.get())
			except:
				pass 

def mirrorCtrls(ctrls = [], direction = 0, **kwargs):
	if ctrls:
		pm.undoInfo(openChunk=True)
		for ctrl in ctrls:
			ctrl = mnsUtils.validateNameStd(ctrl)
			if ctrl:
				symCtrl = None
				if ctrl.side == "l" and direction == 0: symCtrl = getOppositeSideControl(ctrl)
				elif ctrl.side == "r" and direction == 1: symCtrl = getOppositeSideControl(ctrl)
				if symCtrl:
					matchKeyableAttributes(ctrl.node, symCtrl.node)
		pm.undoInfo(closeChunk=True)

def loadRigInfo(puppetRoot = None):
	if pm.window("mnsRigInfo", exists=True):
		try:
			pm.deleteUI("mnsRigInfo")
		except:
			pass

	if not puppetRoot:
		rigTop = getRigTopForSel()
		if rigTop:
			puppetRoot = getPuppetRootFromRigTop(rigTop)
	if puppetRoot:
		status, rigInfo = mnsUtils.validateAttrAndGet(puppetRoot.node, "rigInfo", {})
		if status and rigInfo:
			MnsRigInfo(mnsUIUtils.get_maya_window(), json.loads(rigInfo))
		else:
			mnsLog.log("Rig-Info unavailable. This rig is most likely constructed pre version 1.5.1.", svr = 2)
	else:
		mnsLog.log("Rig-Info is available only post construction.", svr = 2)

###############################
######### MOCAP ###############
###############################

def setResetValuesForOffsetJoint(offsetJnt = None):
	offsetJnt = mnsUtils.validateNameStd(offsetJnt)
	if offsetJnt:
		resetValuesDict = {}
		for chan in "ts":
			for axis in "xyz":
				resetValuesDict.update({(chan + axis): offsetJnt.node.attr((chan + axis)).get()})
		
		resetValuesString = json.dumps(resetValuesDict)
		mnsUtils.addAttrToObj([offsetJnt.node], type = "string", value = resetValuesString, name = "resetValues", locked = True, replace = True)

def loadResetValuesForOffsetJoint(offsetJnt = None):
	offsetJnt = mnsUtils.validateNameStd(offsetJnt)
	if offsetJnt:
		status, resetValues = mnsUtils.validateAttrAndGet(offsetJnt, "resetValues", {})
		if status and resetValues:
			resetDict = json.loads(resetValues)
			if resetDict:
				for key in resetDict.keys():
					offsetJnt.node.attr(key).set(resetDict[key])
				for axis in "xyz":
					offsetJnt.node.attr("r" + axis).set(0.0)
					
def resetOffsetSkeleton(rigTop = None):
	pm.undoInfo(openChunk=True)

	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		offsetSkelGrp = getOffsetSkeletonGrpFromRigTop(rigTop)
		if offsetSkelGrp:
			offsetJoints = offsetSkelGrp.node.listRelatives(ad = True, type = "joint")
			if offsetJoints:
				for offsetJoint in offsetJoints:
					loadResetValuesForOffsetJoint(offsetJoint)
				mnsLog.log("Offset Skeleton was reset.", svr = 1)

	pm.undoInfo(closeChunk=True)

def transferAuthorityToPuppet(rigTop = None):
	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		offsetSkelGrp = getOffsetSkeletonGrpFromRigTop(rigTop)
		puppetGrp = getPuppetBaseFromRigTop(rigTop)
		if offsetSkelGrp and puppetGrp:
			isOffsetSkelExists = offsetSkelGrp.node.listRelatives(c = True, type = "transform")
			if isOffsetSkelExists:
				#gather all controls
				allCtrls = [c for c in puppetGrp.node.listRelatives(ad = True, type = "transform") if c.nodeName().split("_")[-1] == "ctrl"]
				if allCtrls:
					#loop through all controls and find offsetMaster attributes
					for ctrl in allCtrls:
						status, offsetRigSlaveIsParent = mnsUtils.validateAttrAndGet(ctrl, "offsetRigSlaveIsParent", False)
						
						ocGrp = ctrl.getParent()
						if offsetRigSlaveIsParent:
							pm.delete(ocGrp.listRelatives(c = True, type = "constraint"))
						else:
							pm.delete(ctrl.listRelatives(c = True, type = "constraint"))

						#tranfer keys if exist on parent master
						if offsetRigSlaveIsParent:
							if pm.keyframe(ocGrp, q=True):
								#there are keys, transfer them to the original control
								pm.cutKey(ocGrp, animation = "objects", option = "keys")
								pm.pasteKey(ctrl, animation = "objects", option = "replaceCompletely")
					rigTop.node.offsetSkeletonGrpVis.set(3)
					mnsLog.log("Authority transfered to the Puppet.", svr = 1)
			else:				
				mnsLog.log("There is no offset-skeleton. Please create the offset-skeleton before transfering the authority to it.", svr = 2)
		else:				
			#no offset-sekeleton/puppet group exception
			mnsLog.log("Couldn't find offset-skeleton-group or puppet-group for selection. Aborting.", svr = 2)

def transferAuthorityToOffsetSkeleton(rigTop = None):
	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		offsetSkelGrp = getOffsetSkeletonGrpFromRigTop(rigTop)
		puppetGrp = getPuppetBaseFromRigTop(rigTop)
		if offsetSkelGrp and puppetGrp:
			isOffsetSkelExists = offsetSkelGrp.node.listRelatives(c = True, type = "transform")
			if isOffsetSkelExists:
				#gather all controls
				allCtrls = [c for c in puppetGrp.node.listRelatives(ad = True, type = "transform") if c.nodeName().split("_")[-1] == "ctrl"]
				if allCtrls:
					#loop through all controls and find offsetMaster attributes
					for ctrl in allCtrls:
						status, offsetMaster = mnsUtils.validateAttrAndGet(ctrl, "offsetRigMaster", None)
						if offsetMaster:
							#offset master aquired
							offsetMaster = mnsUtils.validateNameStd(offsetMaster)
							offsetAuth = mnsUtils.returnNameStdChangeElement(offsetMaster, suffix = mnsPS_oJnt, autoRename = False)
							offsetAuthA = mnsUtils.validateNameStd(offsetAuth.name)
							if offsetAuthA: offsetAuth = offsetAuthA
							elif offsetMaster.namespace:
								offsetAuth = mnsUtils.validateNameStd(offsetMaster.namespace + ":" + offsetAuth.name)

							if offsetAuth:
								status, offsetRigSlaveIsParent = mnsUtils.validateAttrAndGet(ctrl, "offsetRigSlaveIsParent", False)
								if not offsetRigSlaveIsParent:
									pm.parentConstraint(offsetAuth.node, ctrl, mo = True)
								else:
									ocGrp = ctrl.getParent()
									pm.parentConstraint(offsetAuth.node, ocGrp, mo = True)
					
					rigTop.node.offsetSkeletonGrpVis.set(1)
					mnsLog.log("Authority transfered to the Offset-Skeleton.", svr = 1)
			else:				
				mnsLog.log("There is no offset-skeleton. Please create the offset-skeleton before transfering the authority to it.", svr = 2)
		else:				
			#no offset-sekeleton/puppet group exception
			mnsLog.log("Couldn't find offset-skeleton-group or puppet-group for selection. Aborting.", svr = 2)

def deleteOffsetSekeleton(rigTop = None):
	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		offsetSkelGrp = getOffsetSkeletonGrpFromRigTop(rigTop)
		if offsetSkelGrp:
			isOffsetSkelExists = offsetSkelGrp.node.listRelatives(c = True, type = "transform")
			if isOffsetSkelExists:
				reply = pm.confirmDialog(icon = "information", title='Delete Offset Skeleton', message="Are you sure you want to delete the offset skeleton?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No' )
				if(reply == 'Yes'): 
					pm.delete(isOffsetSkelExists)
					mnsLog.log("Offset-Skeleton Deleted successfully.", svr = 1)
				else: contin = False
			else:				
				#no offset-sekeleton/puppet group exception
				mnsLog.log("There is no offset-skeleton to delete. Aborting.", svr = 2)
		else:				
			#no offset-sekeleton/puppet group exception
			mnsLog.log("Couldn't find offset-skeleton-group for selection. Aborting.", svr = 2)

def createOffsetSkeleton(rigTop = None):
	from . import buildModules as mnsBuildModules

	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		MnsRig = mnsBuildModules.MnsRig(rigTop = rigTop, execInit = False)
		MnsRig.createSubGrpsForRigTop(MnsRig.rigTop)
		offsetSkelGrp = getOffsetSkeletonGrpFromRigTop(rigTop)
		jntStructGrp = getJointStructGrpFromRigTop(rigTop)

		if offsetSkelGrp and jntStructGrp:
			# existing offset skeleton exception
			contin = True
			isOffsetSkelExists = offsetSkelGrp.node.listRelatives(c = True, type = "transform")
			if isOffsetSkelExists:
				reply = pm.confirmDialog(icon = "warning", title='Replace Existing Offset Skeleton', message="An Offset-Skeleton already exists, do you want to replace it?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No' )
				if(reply == 'Yes'): pm.delete(isOffsetSkelExists)
				else: contin = False

			if contin:
				#All pre checks passed, create the offset sekeleton
				#duplictae existing structure, place it onder the relevant group
				rootJoint = jntStructGrp.node.listRelatives(c = True, type = "joint")
				if rootJoint:
					nameSpace = False
					if rigTop.namespace:
						pm.namespace(set = ":")
						if pm.namespace(exists=rigTop.namespace):
							pm.namespace(set = rigTop.namespace)
							nameSpace = True
				
					rootJoint = mnsUtils.validateNameStd(rootJoint[0])
					dupRootJointName = mnsUtils.returnNameStdChangeElement(rootJoint, suffix = mnsPS_oJnt, autoRename = False)
					dupRootJnt = mnsUtils.validateNameStd(pm.duplicate(rootJoint.node, name = dupRootJointName.name)[0])
					mnsUtils.lockAndHideAllTransforms(dupRootJnt, lock = False, keyable = True, cb = True)
					setResetValuesForOffsetJoint(dupRootJnt)

					pm.parent(dupRootJnt.node, offsetSkelGrp.node)
					for joint in dupRootJnt.node.listRelatives(ad = True, type = "joint"):
						joint = mnsUtils.validateNameStd(joint)
						if joint.suffix == mnsPS_iJnt: 
							pm.delete(joint.node)
						else:
							dupJoint = mnsUtils.returnNameStdChangeElement(joint, suffix = mnsPS_oJnt, autoRename = True)
							mnsUtils.lockAndHideAllTransforms(dupJoint, lock = False, keyable = True, cb = True)
							setResetValuesForOffsetJoint(dupJoint)

					mnsUtils.jointRotationToOrient(dupRootJnt.node)
					
					if nameSpace:
						pm.namespace(set = ":")

					mnsLog.log("Offset-Skeleton Created successfully.", svr = 1)
				else:
					#no root-Joint exception
					mnsLog.log("Couldn't find Root-Joint for selection. Aborting.", svr = 2)
		else:				
			#no offset-sekeleton/puppet group exception
			mnsLog.log("Couldn't find offset-skeleton-group or puppet-group for selection. Aborting.", svr = 2)

def selectSlaveControls(rigTop = None, **kwargs):
	returnOnly = kwargs.get("returnOnly", False)

	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		offsetSkelGrp = getOffsetSkeletonGrpFromRigTop(rigTop)
		puppetGrp = getPuppetBaseFromRigTop(rigTop)
		if offsetSkelGrp and puppetGrp:
			#gather all controls
			allCtrls = [c for c in puppetGrp.node.listRelatives(ad = True, type = "transform") if c.nodeName().split("_")[-1] == "ctrl"]
			if allCtrls:
				newSelection = []

				#loop through all controls and find offsetMaster attributes
				for ctrl in allCtrls:
					status, offsetMaster = mnsUtils.validateAttrAndGet(ctrl, "offsetRigMaster", None)
					if offsetMaster:
						status, offsetRigSlaveIsParent = mnsUtils.validateAttrAndGet(ctrl, "offsetRigSlaveIsParent", False)
						if offsetRigSlaveIsParent:
							ocGrp = ctrl.getParent()
							if not ocGrp.nodeName().split("_")[-1] is mnsPS_osCns:
								ctrl = ocGrp
						newSelection.append(ctrl)

				if newSelection:
					if not returnOnly:
						pm.select(newSelection, r = True)
					return newSelection

				mnsLog.log("Controls Selected.", svr = 1)
		else:				
			#no offset-sekeleton/puppet group exception
			mnsLog.log("Couldn't find offset-skeleton-group or puppet-group for selection. Aborting.", svr = 2)

def bakeSlaveControls(rigTop = None):
	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	slaveControls = selectSlaveControls(rigTop, returnOnly = True)
	if slaveControls:
		anim_startTime = pm.playbackOptions(minTime =True, q=True)
		anim_endTime = pm.playbackOptions(maxTime =True, q=True)
		pm.bakeResults(slaveControls, t= (anim_startTime, anim_endTime), sb = 1, simulation = True)

def importGuidePreset(presetName = None):
	if presetName:
		presetDirectory =  os.path.dirname(os.path.dirname(__file__)) + "/guidePresets"
		if os.path.isdir(presetDirectory):
			fileToImport = None
			for file in os.listdir(presetDirectory):
				if presetName in file:
					fileToImport = presetDirectory.replace("\\", "/") + "/" + file
					break

			if fileToImport:
				cmds.file(fileToImport, i=True, pmt = False, f = True)
				mnsLog.log("Preset Imported successfully.", svr = 1)

		currentUpAxis = pm.upAxis(q=True, axis=True)
		if currentUpAxis == "z":
			importedPresetRigTop = mnsUtils.validateNameStd("c_" + presetName + "_A001_blkRig")
			if importedPresetRigTop:
				rootGuide = getRootGuideFromRigTop(importedPresetRigTop)
				if rootGuide:
					mnsUtils.setAttr(rootGuide.node.rx, 90.0)

def matchGuidesToTargetSkeleton(defenitionDict = {}, blockNameSpace = "", targetNameSpace = ""):
	pm.undoInfo(openChunk=True)
	cnsToDel = []
	for key in defenitionDict.keys():
		blockSkelItem = defenitionDict[key]["blockSkelItem"]
		if blockNameSpace: blockSkelItem = blockNameSpace + ":" + blockSkelItem
		blockSkelItem = mnsUtils.checkIfObjExistsAndSet(blockSkelItem)

		targetSkelItem = defenitionDict[key]["targetSkelItem"]
		if targetNameSpace: targetSkelItem = targetNameSpace + ":" + targetSkelItem
		targetSkelItem = mnsUtils.checkIfObjExistsAndSet(targetSkelItem)
		
		if blockSkelItem and targetSkelItem:
			guideMaster = getRelationMasterFromSlave(blockSkelItem)
			if guideMaster.body != "blkRoot":
				cnsToDel.append(pm.pointConstraint(targetSkelItem, guideMaster.node))

	if cnsToDel: pm.delete(cnsToDel)
	pm.undoInfo(closeChunk=True)

def connectTargetSkeleton(defenitionDict = {}, blockNameSpace = "", targetNameSpace = ""):
	pm.undoInfo(openChunk=True)
	for key in defenitionDict.keys():
		blockSkelItem = defenitionDict[key]["blockSkelItem"]
		if blockNameSpace: blockSkelItem = blockNameSpace + ":" + blockSkelItem
		blockSkelItem = mnsUtils.checkIfObjExistsAndSet(blockSkelItem)

		targetSkelItem = defenitionDict[key]["targetSkelItem"]
		if targetNameSpace: targetSkelItem = targetNameSpace + ":" + targetSkelItem
		targetSkelItem = mnsUtils.checkIfObjExistsAndSet(targetSkelItem)
		
		if blockSkelItem and targetSkelItem:
			parCns = pm.parentConstraint(blockSkelItem, targetSkelItem, mo = True)
			sclCns = pm.scaleConstraint(blockSkelItem, targetSkelItem, mo = True)
			mnsUtils.addAttrToObj(targetSkelItem, name = "blockParentConnect" , type = "message", value = parCns, locked = True, cb = False, keyable = False)
			mnsUtils.addAttrToObj(targetSkelItem, name = "blockScaleConnect" , type = "message", value = sclCns, locked = True, cb = False, keyable = False)

	pm.undoInfo(closeChunk=True)

def disconnectTargetSkeleton(defenitionDict = {}, blockNameSpace = "", targetNameSpace = "", **kwargs):
	pm.undoInfo(openChunk=True)

	for key in defenitionDict.keys():
		targetSkelItem = defenitionDict[key]["targetSkelItem"]
		if targetNameSpace: targetSkelItem = targetNameSpace + ":" + targetSkelItem
		targetSkelItem = mnsUtils.checkIfObjExistsAndSet(targetSkelItem)
		
		status, parCns = mnsUtils.validateAttrAndGet(targetSkelItem, "blockParentConnect", None)
		if parCns: pm.delete(parCns)
		status, sclCns = mnsUtils.validateAttrAndGet(targetSkelItem, "blockScaleConnect", None)
		if sclCns: pm.delete(sclCns)

	pm.undoInfo(closeChunk=True)

def characterizeHumanIK(charDefData = {}, mode = 0, **kwargs):
	charName = kwargs.get("charName", "Character1")
	namespace = kwargs.get("namespace", "")

	if charDefData:
		hikDef = {}
		initializeCharName = False
		for componentName in charDefData.keys():
			hikSlot = charDefData[componentName]["hikSlot"]
			if hikSlot:
				if mode == 0:
					#get offset joint from base joint
					targetBlockJoint = mnsUtils.validateNameStd(charDefData[componentName]["blockSkelItem"])
					if not targetBlockJoint and namespace:
						targetBlockJoint = mnsUtils.validateNameStd(namespace + ":" + charDefData[componentName]["blockSkelItem"])

					if targetBlockJoint:
						osJoint = mnsUtils.returnNameStdChangeElement(nameStd = targetBlockJoint, suffix = mnsPS_oJnt, autoRename = False)
						osJointA = mnsUtils.checkIfObjExistsAndSet(osJoint.name)
						if osJointA:
							osJoint = osJointA
						elif namespace:
							osJoint = mnsUtils.checkIfObjExistsAndSet(namespace + ":" + osJoint.name)

						if osJoint:
							hikDef.update({hikSlot: osJoint})

						if not initializeCharName:
							rigTop = getRigTop(targetBlockJoint)
							status, characterName = mnsUtils.validateAttrAndGet(rigTop, "characterName", None)
							if characterName:
								charName = characterName
								initializeCharName = True
				else:
					targetSkeletonJoint = mnsUtils.checkIfObjExistsAndSet(charDefData[componentName]["targetSkelItem"])
					if not targetSkeletonJoint and namespace:
						targetSkeletonJoint = mnsUtils.checkIfObjExistsAndSet(namespace + ":" + charDefData[componentName]["targetSkelItem"])

					if targetSkeletonJoint:
						hikDef.update({hikSlot: targetSkeletonJoint})
		if hikDef:
			mel.eval("HIKCharacterControlsTool")
			mel.eval("hikCreateCharacter(\"" + charName + "\")")
			hikProportiesNode = pm.ls(sl=True)[0]
			hikCharNode = hikProportiesNode.listConnections()[0]
			mel.eval("hikUpdateCurrentCharacterFromUI(); hikUpdateContextualUI();")

			for hikSlotKey in hikDef.keys():
				jointNode = hikDef[hikSlotKey]
				mnsUtils.addAttrToObj(jointNode, name = "Character" , type = "message", value = None, locked = True, cb = False, keyable = False)
				jointNode.Character >> hikCharNode.attr(hikSlotKey)
			if charName: hikCharNode.rename(charName)
			mel.eval("hikUpdateCurrentCharacterFromUI(); hikUpdateContextualUI();")
			mel.eval("hikCharacterLock(\"" + charName + "\",1,1);")
			mel.eval("hikUpdateCurrentCharacterFromUI(); hikUpdateContextualUI();")
			mel.eval("hikSelectDefinitionTab();")

def extractSkeleton(rigTop = None, mode = 0, bakeAnim = False, **kwargs):
	deleteInterpJoints = kwargs.get("deleteInterpJoints", False)
	rotToJointOrient = kwargs.get("rotToJointOrient", True)
	preserveNameSpace = kwargs.get("preserveNameSpace", False)
	transferSkin = kwargs.get("transferSkin", False)
	bakeConnectionMethod = kwargs.get("bakeConnectionMethod", 0)

	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		skeletonGrp = None
		if mode == 0:
			skeletonGrp = getJointStructGrpFromRigTop(rigTop)
		elif mode == 1:
			skeletonGrp = getOffsetSkeletonGrpFromRigTop(rigTop)

		if skeletonGrp:
			nameSpace = False
			if rigTop.namespace and preserveNameSpace:
				pm.namespace(set = ":")
				if pm.namespace(exists=rigTop.namespace):
					pm.namespace(set = rigTop.namespace)
					nameSpace = True

			rootJoint = skeletonGrp.node.listRelatives(c = True, type = "joint")
			if rootJoint:
				rootJoint = rootJoint[0]
				dupRootJnt = mnsUtils.validateNameStd(pm.duplicate(rootJoint)[0])
				dupRootJnt.node.overrideDisplayType.set(0)
				dupRootJnt.node.overrideEnabled.set(0)
				pm.parent(dupRootJnt.node, w = True)
				dupRootJnt.node.rename(rootJoint.nodeName().split(":")[-1])
				mnsUtils.lockAndHideAllTransforms(dupRootJnt, lock = False, keyable = True, cb = True)

				dupJointDict = {dupRootJnt.name: dupRootJnt.node}
				for joint in dupRootJnt.node.listRelatives(ad = True, type = "joint"):
					joint.overrideDisplayType.set(0)
					joint.overrideEnabled.set(0)

					joint = mnsUtils.validateNameStd(joint)
					if joint.suffix == mnsPS_iJnt and deleteInterpJoints: 
						pm.delete(joint.node)
					else:
						mnsUtils.lockAndHideAllTransforms(joint, lock = False, keyable = True, cb = True)
						dupJointDict.update({joint.name: joint.node})
				
				if transferSkin and mode == 0:
					for j in [rootJoint] + rootJoint.listRelatives(ad = True, type = "joint"):
						pureName = j.nodeName().split(":")[-1]
						if pureName in dupJointDict.keys():
							for connectedAttr in j.worldMatrix.listConnections(d = True, s = False, p = True):
								if type(connectedAttr.node()) == pm.nodetypes.SkinCluster:
									dupJointDict[pureName].worldMatrix[0] >> connectedAttr
									dupJointDict[pureName].attr("objectColorRGB") >> connectedAttr.node().influenceColor[connectedAttr.index()]
									dupJointDict[pureName].attr("lockInfluenceWeights") >> connectedAttr.node().lockWeights[connectedAttr.index()]

				if rotToJointOrient:
					mnsUtils.jointRotationToOrient(dupRootJnt.node)
				
				if bakeAnim:
					allJoints = [dupRootJnt.node] + dupRootJnt.node.listRelatives(ad = True, type = "joint")
					anim_startTime = pm.playbackOptions(minTime =True, q=True)
					anim_endTime = pm.playbackOptions(maxTime =True, q=True)
					
					allOrigJointsDict = {}
					for j in [rootJoint] + rootJoint.listRelatives(ad = True, type = "joint"):
						allOrigJointsDict.update({j.nodeName().split(":")[-1]: j})
						
					cnsToDel = []
					for j in allJoints:
						pureName = j.nodeName().split(":")[-1]
						if pureName in allOrigJointsDict.keys():
							if bakeConnectionMethod == 0: #constraints
								cnsToDel.append(pm.parentConstraint(allOrigJointsDict[pureName], j, mo = True))
								cnsToDel.append(pm.scaleConstraint(allOrigJointsDict[pureName], j, mo = True))
							else: #direct
								for chan in ["t", "r", "s", "jointOrient"]:
									allOrigJointsDict[pureName].attr(chan) >> j.attr(chan)

					pm.bakeResults(allJoints, t= (anim_startTime, anim_endTime), sb = 1, simulation = True)
					#pm.delete(cnsToDel)
					pm.currentTime(anim_startTime, edit=True)

				pm.select(dupRootJnt.node, r = True)
				if nameSpace:
					pm.namespace(set = ":")

				mnsLog.log("Sekeleton extracted successfully.", svr = 1)

				return dupRootJnt
		
def extractSkeleton2(rigTop = None, mode = 0, **kwargs):
	rotToJointOrient = kwargs.get("rotToJointOrient", False)

	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = getRigTopForSel()

	if rigTop:
		skeletonGrp = None
		if mode == 0:
			skeletonGrp = getJointStructGrpFromRigTop(rigTop)
		elif mode == 1:
			skeletonGrp = getOffsetSkeletonGrpFromRigTop(rigTop)

		if skeletonGrp:

			rootJoint = skeletonGrp.node.listRelatives(c = True, type = "joint")
			if rootJoint:
				rootJoint = rootJoint[0]
				dupRootJnt = mnsUtils.validateNameStd(pm.duplicate(rootJoint)[0])
				dupRootJnt.node.overrideDisplayType.set(0)
				dupRootJnt.node.overrideEnabled.set(0)
				pm.parent(dupRootJnt.node, w = True)
				dupRootJnt.node.rename(rootJoint.nodeName().split(":")[-1])
				mnsUtils.lockAndHideAllTransforms(dupRootJnt, lock = False, keyable = True, cb = True)

				for joint in dupRootJnt.node.listRelatives(ad = True, type = "joint"):
					joint.overrideDisplayType.set(0)
					joint.overrideEnabled.set(0)
					mnsUtils.lockAndHideAllTransforms(joint, lock = False, keyable = True, cb = True)

				if rotToJointOrient:
					mnsUtils.jointRotationToOrient(dupRootJnt.node)
			
				pm.select(dupRootJnt.node, r = True)
				mnsLog.log("Sekeleton extracted successfully.", svr = 1)

				return dupRootJnt, rootJoint

def matchExtractedSkeletonToBaseSkeleton():
	sel = pm.ls(sl=True)
	if sel and type(sel[0]) == pm.nodetypes.Joint:
		rigTops = getRigTopAssemblies()
		if rigTops:
			extractedSkeletonRoot = mnsUtils.getFirstLevelParentForObject(sel[0])
			baseSkeletonRoot = getJointStructGrpFromRigTop(rigTops[list(rigTops.keys())[0]])
			if baseSkeletonRoot:
				baseSkeletonRoot = baseSkeletonRoot.node.listRelatives(c = True, type = "joint")
				if baseSkeletonRoot:
					baseSkeletonRoot = baseSkeletonRoot[0]
					
					extractedSkelDict = {}
					for j in [extractedSkeletonRoot] + extractedSkeletonRoot.listRelatives(ad = True, type = "joint"):
						extractedSkelDict.update({j.nodeName(): j})

					pm.undoInfo(openChunk=True)
					#validations finished, snap skeleton
					constraints = []
					for baseJoint in [baseSkeletonRoot] + baseSkeletonRoot.listRelatives(ad = True, type = "joint"):
						if baseJoint.nodeName() in extractedSkelDict.keys():
							constraints.append(pm.parentConstraint(baseJoint, extractedSkelDict[baseJoint.nodeName()]))
							constraints.append(pm.scaleConstraint(baseJoint, extractedSkelDict[baseJoint.nodeName()]))
					if constraints:
						pm.delete(constraints)
					pm.undoInfo(closeChunk=True)

					mnsLog.log("Extracted skeleton matched to base skeleton successfully.", svr = 1)
				else:
					mnsLog.log("Couldn't find base skeleton root joint. Aborting.", svr = 2)
			else:
				mnsLog.log("Couldn't find joint structure group. Aborting.", svr = 2)
		else:
			mnsLog.log("Couldn't find a Block Puppet within the scene.", svr = 2)

	else:
		mnsLog.log("Please select a joint from the extracted skeleton hierarchy.", svr = 2)

def jointRotateToOrientTrigger(rigTop = None):
	rootJoint = pm.ls(sl=True)
	if rootJoint:
		rootJoint = rootJoint[0]
		try:
			pm.undoInfo(openChunk=True)
			mnsUtils.jointRotationToOrient(rootJoint)
			pm.undoInfo(closeChunk=True)
			mnsLog.log("Joint Rotation To Joint Orient process complete.", svr = 1)
		except:
			mnsLog.log("Joint Rotation To Joint Orient failed. Please check the skeleton is valid, and that it's transforms are not locked.", svr = 2)
			pass

def saveLoadDagPose(rootJoint = None, mode = 1, poseName = "Bind"):
	"""
	mode 0 = Save
	mode 1 = Load
	mode 2 = Delete
	
	poses: Bind, T, A
	"""
	
	poseName = poseName.lower()
	if poseName == "bind" or poseName == "t" or poseName == "a":
		if not rootJoint:
			sel = pm.ls(sl=True)
			if sel: rootJoint = sel[0]
		
		if rootJoint:
			if type(rootJoint) == pm.nodetypes.Joint:
				pm.undoInfo(openChunk=True)
				pm.select(rootJoint, r = True)
				
				#first query if a pose exists
				currentPoses = [c for c in rootJoint.message.listConnections(d = True, s = False) if type(c) == pm.nodetypes.DagPose]
				existingPose = None
				for p in currentPoses:
					if (poseName + "Pose") in p.nodeName(): existingPose = p
				
				#### SAVE
				if mode == 0:
					if poseName == "bind":
						if existingPose:
							pm.dagPose(bp = True, addToPose = True, name = existingPose.nodeName())
						else:
							pm.dagPose(bp = True, save = True)
					else:
						if existingPose:
							cmds.dagPose(a = True, name = poseName + "Pose")
						else:
							cmds.dagPose(save = True, name = poseName + "Pose")

					mnsLog.log(poseName.capitalize() + " Pose Saved.", svr = 1)

				### LOAD
				elif mode == 1:
					if existingPose:
						if poseName == "bind":
							pm.dagPose(bp = True, r = True)
						else:
							pm.dagPose(name = poseName + "Pose", r = True)

						mnsLog.log(poseName.capitalize() + " Pose Loaded.", svr = 1)
					else:
						mnsLog.log(poseName.capitalize() + "Pose does not exist, nothing to load.", svr = 2)

				### DELETE  
				elif mode == 2:
					if existingPose: 
						pm.delete(existingPose)
						mnsLog.log(poseName.capitalize() + " Pose Deleted.", svr = 1)
					else:
						mnsLog.log(poseName.capitalize() + "Pose does not exist, nothing to delete.", svr = 2)

				pm.undoInfo(closeChunk=True)
			else:
				mnsLog.log("Please select a joint.", svr = 2)
		else:
			mnsLog.log("Please select a joint from the skeleton you want to perform actions on.", svr = 2)
	else:
		mnsLog.log("Invalid pose name flag. Valid inputs are: Bind, T, A", svr = 2)

###############################
###### Volume Joints ##########
###############################

def getExistingVolumeJointNodeForJoint(joint = None):
	joint = mnsUtils.checkIfObjExistsAndSet(joint)
	if joint:
		existingConnections = joint.listConnections(d = True, s = False, p = True)
		for c in existingConnections:
			if type(c.node()) == pm.nodetypes.MnsVolumeJoint:
				if c.attrName() == "childJointWorldMatrix":
					return c.node()

def getExistingVolumeJointNodeForVolumeJoint(joint = None):
	joint = mnsUtils.checkIfObjExistsAndSet(joint)
	if joint:
		outCons = joint.parentInverseMatrix[0].listConnections(d = True, s = False, p = True)
		if outCons:
			for o in outCons:
				if type(o.node()) == pm.nodetypes.MnsVolumeJoint:
					return o.node(), o.parent().index()

def createVolumeJoint(parentJoint = None, childJoint = None, **kwargs):
	appendToExistingNode = kwargs.get("appendToExistingNode", True)
	existingSymVJnt = mnsUtils.validateNameStd(kwargs.get("existingSymVJnt", None))

	if parentJoint and childJoint:
		#check if this is a volume joint itself
		existingConnections = childJoint.listConnections(d = False, s = True, p = True)
		for c in existingConnections:
			if type(c.node()) == pm.nodetypes.MnsVolumeJoint:
				mnsLog.log("Cannot create a volume joint from a volume joint. Aborting", svr = 2)
				return None

		mnsVJNode = None
		if appendToExistingNode:
			mnsVJNode = getExistingVolumeJointNodeForJoint(childJoint)

		if not mnsVJNode:
			mnsVJNode = mnsNodes.mnsVolumeJointNode(parentJoint = parentJoint, childJoint = childJoint)
			mnsVJNode = mnsVJNode.node

		if mnsVJNode:
			#get next available index
			nextAvailableIndex = 0
			for idx in range(mnsVJNode.volumeJoint.numElements()):
				if mnsVJNode.volumeJoint[idx].parentInverseMatrix.isConnected():
					nextAvailableIndex += 1
				else:
					break

			side = "c"
			body = "volumeJoint"
			alpha = "A"
			idA = 1
			childJointNameStd = mnsUtils.validateNameStd(childJoint)
			if childJointNameStd:
				side = childJointNameStd.side
				body = childJointNameStd.body
				alpha = childJointNameStd.alpha
				idA = childJointNameStd.id

			vj = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = idA, buildType = "volumeJoint")
			if vj:
				vj.node.parentInverseMatrix[0] >> mnsVJNode.volumeJoint[nextAvailableIndex].parentInverseMatrix
				mnsVJNode.result[nextAvailableIndex].translate >> vj.node.t
				mnsVJNode.result[nextAvailableIndex].rotate >> vj.node.r
				mnsVJNode.result[nextAvailableIndex].scale >> vj.node.s
				pm.parent(vj.node, childJoint)
				mnsUtils.zeroJointOrient(vj.node)

				if existingSymVJnt:
					mnsUtils.addAttrToObj(existingSymVJnt, name = "symVJ" , type = "message", value = vj.node, locked = True, cb = False, keyable = False, replace = True)
					mnsUtils.addAttrToObj(vj, name = "symVJ" , type = "message", value = existingSymVJnt.node, locked = True, cb = False, keyable = False, replace = True)

				#return; mnsNameStd (volumeJoint)
				return vj

def getRelatedVolJntSourcesForSelection():
	sTransform = None

	sel = pm.ls(sl=True)
	if sel:
		sTransform = sel[0]
		sTransformStd = mnsUtils.validateNameStd(sTransform)
		if sTransformStd:
			suffix = sTransformStd.suffix
			if suffix == mnsPS_vJnt: return sTransformStd
			elif suffix == mnsPS_rJnt or suffix == mnsPS_jnt:
				if "rigRoot" in sTransformStd.name:
					sTransform = None
			elif suffix == mnsPS_ctrl:
				status, guideAuthority = mnsUtils.validateAttrAndGet(sTransformStd, "guideAuthority", None)
				if guideAuthority:
					guideStd = mnsUtils.validateNameStd(guideAuthority)
					if guideStd:
						sTransformStd = guideStd
						suffix = sTransformStd.suffix
			elif suffix == mnsPS_gRootCtrl or suffix == mnsPS_gCtrl:
				if "blkRoot" in sTransformStd.name:
					sTransform = None
				else:
					status, jntSlave = mnsUtils.validateAttrAndGet(sTransformStd, "jntSlave", None)
					if jntSlave:
						sTransform = jntSlave
			else:
				sTransform = None

			if sTransform:
				vJointNode = getExistingVolumeJointNodeForJoint(sTransform)
				if vJointNode:
					inCons = vJointNode.listConnections(s = True, d = False)
					for inputCon in inCons:
						nn = inputCon.nodeName()
						if "_" in nn and nn.split("_")[-1] == mnsPS_vJnt: 
							return inputCon
							break

	return sTransform

def createVolumeJointForSelection():
	sel = pm.ls(sl=True)
	if sel:
		for sTransform in sel:
			sTransformStd = mnsUtils.validateNameStd(sTransform)
			if sTransformStd:
				suffix = sTransformStd.suffix
				if suffix == mnsPS_rJnt or suffix == mnsPS_jnt:
					if "rigRoot" in sTransformStd.name:
						sTransform = None
						mnsLog.log("Cannot create volume joint from Block-Rig Root.", svr = 2)
				elif suffix == mnsPS_ctrl:
					status, guideAuthority = mnsUtils.validateAttrAndGet(sTransformStd, "guideAuthority", None)
					if guideAuthority:
						guideStd = mnsUtils.validateNameStd(guideAuthority)
						if guideStd:
							sTransformStd = guideStd
							suffix = sTransformStd.suffix
						else:
							mnsLog.log("Couldn't find slave joint from ctrl " + sTransformStd.name + ".", svr = 2)
					else:
						mnsLog.log("Couldn't find slave joint from ctrl " + sTransformStd.name + ".", svr = 2)

				if suffix == mnsPS_gRootCtrl or suffix == mnsPS_gCtrl:
					if "blkRoot" in sTransformStd.name:
						sTransform = None
						mnsLog.log("Cannot create volume joint from Block-Rig Root.", svr = 2)
					else:
						status, jntSlave = mnsUtils.validateAttrAndGet(sTransformStd, "jntSlave", None)
						if jntSlave:
							sTransform = jntSlave
						else:
							mnsLog.log("Couldn't find slave joint from guide " + sTransformStd.name + ".", svr = 2)

			if sTransform and type(sTransform) == pm.nodetypes.Joint:
				childJoint = sTransform
				parentJoint = sTransform.getParent()
				if childJoint and parentJoint:
					vj = createVolumeJoint(parentJoint = parentJoint, childJoint = childJoint)
					
					#return; mnsNameStd (volumeJoint)
					return vj
			else:
				mnsLog.log("Couldn't find a joint to attach to from "  + sTransform.nodeName() + ". Please check your selection.", svr = 2)

def getVJntSources(vJnt = None):
	sourceA = None
	sourceB = None

	vJnt = mnsUtils.checkIfObjExistsAndSet(vJnt)
	if vJnt:
		outCons = vJnt.parentInverseMatrix[0].listConnections(d = True, s = False)
		if outCons:
			for o in outCons:
				if type(o) == pm.nodetypes.MnsVolumeJoint:
					pInCons = o.parentJointWorldMatrix.listConnections(d = False, s = True)
					if pInCons: sourceA = pInCons[0].nodeName()
					cInCons = o.childJointWorldMatrix.listConnections(d = False, s = True)
					if cInCons: sourceB = cInCons[0].nodeName()
					break
	return sourceA, sourceB

def volumeJointAngleSymmetryMapping(symmetryDelta = pm.datatypes.Vector(1.0, 1.0, 1.0)):
	mappedReturn = {"rest": "rest","posX": "posX", "negX": "negX", "posY": "posY", "negY": "negY", "posZ": "posZ", "negZ": "negZ"}
	
	if symmetryDelta == pm.datatypes.Vector(-1.0, 1.0, 1.0):
		mappedReturn.update({"posY": "negY"})
		mappedReturn.update({"negY": "posY"})
		mappedReturn.update({"posZ": "negZ"})
		mappedReturn.update({"negZ": "posZ"})
	elif symmetryDelta == pm.datatypes.Vector(-1.0, -1.0, 1.0):
		mappedReturn.update({"posX": "negX"})
		mappedReturn.update({"negX": "posX"})
		mappedReturn.update({"posY": "negY"})
		mappedReturn.update({"negY": "posY"})
	elif symmetryDelta == pm.datatypes.Vector(-1.0, 1.0, -1.0):
		mappedReturn.update({"posX": "negX"})
		mappedReturn.update({"negX": "posX"})
		mappedReturn.update({"posZ": "negZ"})
		mappedReturn.update({"negZ": "posZ"})
	elif symmetryDelta == pm.datatypes.Vector(1.0, -1.0, 1.0):
		mappedReturn.update({"posX": "negX"})
		mappedReturn.update({"negX": "posX"})
		mappedReturn.update({"posZ": "negZ"})
		mappedReturn.update({"negZ": "posZ"})
	elif symmetryDelta == pm.datatypes.Vector(1.0, -1.0, -1.0):
		mappedReturn.update({"posY": "negY"})
		mappedReturn.update({"negY": "posY"})
		mappedReturn.update({"posZ": "negZ"})
		mappedReturn.update({"negZ": "posZ"})
	elif symmetryDelta == pm.datatypes.Vector(1.0, 1.0, -1.0):
		mappedReturn.update({"posX": "negX"})
		mappedReturn.update({"negX": "posX"})
		mappedReturn.update({"posY": "negY"})
		mappedReturn.update({"negY": "posY"})

	return mappedReturn

def detrmineSymmetryDelta(sourceA = None, sourceB = None, **kwargs):
	sourceA = mnsUtils.checkIfObjExistsAndSet(sourceA)
	sourceB = mnsUtils.checkIfObjExistsAndSet(sourceB)
	if sourceA and sourceB:
		masterLoc = pm.spaceLocator()
		sourceALoc = pm.spaceLocator()
		pm.parent(sourceALoc, sourceA)
		sourceBLoc = pm.spaceLocator()
		pm.parent(sourceBLoc, sourceB)

		for sourceLoc in [sourceALoc, sourceBLoc]:
			parCns = pm.parentConstraint(masterLoc, sourceLoc)
			scaleCns = pm.scaleConstraint(masterLoc, sourceLoc)
			pm.delete([parCns, scaleCns])
			pm.parent(sourceLoc, w = True)

		rDelta = sourceALoc.r.get() - sourceBLoc.r.get()
		pm.delete([masterLoc, sourceALoc, sourceBLoc])

		negateTolerance = kwargs.get("negateTolerance", 0.05)
		delta = pm.datatypes.Vector(1.0, 1.0, 1.0)
		if abs(rDelta.x) > (180.0 - negateTolerance) and abs(rDelta.x) < (180.0 + negateTolerance): delta.x = -1.0
		if abs(rDelta.y) > (180.0 - negateTolerance) and abs(rDelta.y) < (180.0 + negateTolerance): delta.y = -1.0
		if abs(rDelta.z) > (180.0 - negateTolerance) and abs(rDelta.z) < (180.0 + negateTolerance): delta.z = -1.0
		return delta

def getSymAttrBasedOnSymMapping(attr = None, attrMapping = {}):
	if attr and attrMapping:
		targetMap = attr.attrName().split("Translate")[0]
		if "Scale" in attr.attrName():
			targetMap = attr.attrName().split("Scale")[0]
		targetAttrName = attr.name().replace(targetMap, attrMapping[targetMap])
		return pm.Attribute(targetAttrName)

def getSymmetricalVolumeJoint(vJnt = None, **kwargs):
	supressMessages = kwargs.get("supressMessages", False)
	createIfMissing = kwargs.get("createIfMissing", True)

	vJnt = mnsUtils.validateNameStd(vJnt)
	symVJnt = None
	if vJnt and vJnt.suffix == mnsPS_vJnt and vJnt.side != "c":
		status, symVJnt = mnsUtils.validateAttrAndGet(vJnt, "symVJ", None)
		symVJnt = mnsUtils.validateNameStd(symVJnt)

		#createSymVJ
		if not symVJnt and createIfMissing:
			sourceA, sourceB = getVJntSources(vJnt.node)
			sourceA = mnsUtils.validateNameStd(sourceA)
			sourceB = mnsUtils.validateNameStd(sourceB)

			if sourceA and sourceB:
				symSourceA = getOppositeSideControl(sourceA)
				symSourceB = getOppositeSideControl(sourceB)
				if sourceA.side == "c": 
					symSourceA = sourceA

				if symSourceA and symSourceB:
					symVJnt = createVolumeJoint(symSourceA.node, symSourceB.node, existingSymVJnt = vJnt)
				else:
					mnsLog.log("Couldn't find symmetrical targets. Aborting.", svr = 2, supressMessages = supressMessages)
					return None
			else:
				mnsLog.log("Couldn't find symmetrical sources. Aborting.", svr = 2, supressMessages = supressMessages)
				return None
		else:
			mnsLog.log("Couldn't find symmetrical volume-joint, attempting to create one.", svr = 0, supressMessages = supressMessages)
	else:	
		mnsLog.log("Couldn't find a valid volume joint to symmetrize. Aborting.", svr = 2, supressMessages = supressMessages)

	if symVJnt:
		#return; mnsNameStd (symmetrical volume-joint)
		return symVJnt
	else:
		mnsLog.log("Couldn't find symmetrical volume-joint, and failed to create one. Aborting.", svr = 2, supressMessages = supressMessages)

def getVJointData(vJnt):
	vJnt = mnsUtils.validateNameStd(vJnt)
	if vJnt:
		vJntParent, vJntChild = getVJntSources(vJnt.node)
		vJntMaster = getRelationMasterFromSlave(vJntChild)
		if not vJntMaster:
			vJntChildN = mnsUtils.checkIfObjExistsAndSet(vJntChild)
			if vJntChildN:
				outCons = vJntChildN.message.listConnections(d = True, s = False, p = True)
				for o in outCons:
					if o.attrName() == "jntSlave":
						vJntMaster = mnsUtils.validateNameStd(o.node())
						break

		return vJntParent, vJntChild, vJntMaster

def symmetrizeVJ(vJnt = None, **kwargs):
	supressMessages = kwargs.get("supressMessages", False)
	symmetryDelta = kwargs.get("symmetryDelta", None)
	attrMapping = kwargs.get("attrMapping", None)

	vJnt = mnsUtils.validateNameStd(vJnt)
	if vJnt:
		symVJnt = getSymmetricalVolumeJoint(vJnt, supressMessages = supressMessages)

		#if a sym joint exists/created, symmetrize attrs
		if symVJnt:
			sourceVJntNode, sourceIndex = getExistingVolumeJointNodeForVolumeJoint(vJnt.node)
			symVJntNode, symIndex = getExistingVolumeJointNodeForVolumeJoint(symVJnt.node)
			if sourceVJntNode and symVJntNode:
				if not symmetryDelta or not attrMapping:
					vJntParent, vJntChild, vJntMaster = getVJointData(vJnt)
					symVJntParent, symVJntchild, symVJntMaster = getVJointData(symVJnt)
					symmetryDelta = detrmineSymmetryDelta(vJntMaster.node, symVJntMaster.node)
					attrMapping = volumeJointAngleSymmetryMapping(symmetryDelta)

				sourceAttrs = sourceVJntNode.volumeJoint[sourceIndex].getChildren()
				symAttrs = symVJntNode.volumeJoint[symIndex].getChildren()
				for k, attr in enumerate(sourceAttrs):
					if not attr.type() == "matrix":
						if "translate" in attr.name().lower() and not "limit" in attr.name().lower():
							getSymAttrBasedOnSymMapping(symAttrs[k], attrMapping).set(attr.get() * symmetryDelta)
						else:
							symAttrs[k].set(attr.get())
		
###############################
###### FK IK Match ############
###############################

def getLimbModuleControls(limbCtrl, mode = 2):
	"""
	mode 0: fk controls and attrHost
	mode 1: ik controls and attrHost
	mode 2: both and attrHost
	mode 3: attrHost only
	"""

	fkControls = {}
	ikControls = {}
	blendAttrHolder = None

	if limbCtrl:
		rootGuide = getRootGuideFromCtrl(limbCtrl)
		if rootGuide:
			status, modType = mnsUtils.validateAttrAndGet(rootGuide, "modType", None)
			if modType and "limb" in modType.lower():
				#gather controls
				moduleCtrls = getCtrlsFromModuleRoot(rootGuide)
				moduleRoot = getModuleTopFromRootGuide(rootGuide)
				moduleRootJoints = getRootJointsFromModuleRoot(rootGuide)
				if moduleRootJoints: 
					moduleRootJoints = mnsUtils.sortNameStdArrayByID(moduleRootJoints)
				
				animGrp = None
				for ctrl in moduleCtrls:
					if "Anim_" in ctrl.node.nodeName(): 
						animGrp = ctrl
						break
						
				if animGrp and moduleRoot:
					status, blendAttrHolder = mnsUtils.validateAttrAndGet(animGrp, "blendAttrHolder", None)
					if mode < 3:
						status, currentBlendValue = mnsUtils.validateAttrAndGet(blendAttrHolder, "ikFkBlend", 0.0)
						if status and moduleRootJoints:
							status, fkMidB = mnsUtils.validateAttrAndGet(animGrp, "fkMidB", None)
							fkControls.update({"fkMidB": fkMidB})

							if mode == 0 or mode == 2:
								status, fkRoot = mnsUtils.validateAttrAndGet(animGrp, "fkRoot", None)
								status, fkRootRef = mnsUtils.validateAttrAndGet(animGrp, "fkRootRef", None)
								status, fkRootRefA = mnsUtils.validateAttrAndGet(animGrp, "fkRootRefA", None)
								status, fkMid = mnsUtils.validateAttrAndGet(animGrp, "fkMid", None)
								status, fkMidRef = mnsUtils.validateAttrAndGet(animGrp, "fkMidRef", None)
								status, fkMidRefA = mnsUtils.validateAttrAndGet(animGrp, "fkMidRefA", None)
								status, fkMidB = mnsUtils.validateAttrAndGet(animGrp, "fkMidB", None)
								status, fkMidBRef = mnsUtils.validateAttrAndGet(animGrp, "fkMidBRef", None)
								status, fkEnd = mnsUtils.validateAttrAndGet(animGrp, "fkEnd", None)
								status, fkEndRef = mnsUtils.validateAttrAndGet(animGrp, "fkEndRef", None)
								status, fkEndRefA = mnsUtils.validateAttrAndGet(animGrp, "fkEndRefA", None)
								fkControls = {
												"fkRoot": fkRoot, 
												"fkRootRef": fkRootRef,
												"fkRootRefA": fkRootRefA,
												"fkMid": fkMid,
												"fkMidRef": fkMidRef,
												"fkMidRefA": fkMidRefA,
												"fkMidBRef": fkMidBRef,
												"fkEnd": fkEnd,
												"fkEndRef": fkEndRef,
												"fkEndRefA": fkEndRefA
												}
							if mode == 1 or mode == 2:
								status, ikCtrl = mnsUtils.validateAttrAndGet(animGrp, "ikCtrl", None)
								status, ikCtrlRef = mnsUtils.validateAttrAndGet(animGrp, "ikCtrlRef", None)
								status, poleVector = mnsUtils.validateAttrAndGet(animGrp, "poleVector", None)
								status, poleVectorRef = mnsUtils.validateAttrAndGet(animGrp, "poleVectorRef", None)
								status, ankleBendCtrl = mnsUtils.validateAttrAndGet(animGrp, "ankleBendCtrl", None)
								status, angleBendRef = mnsUtils.validateAttrAndGet(animGrp, "angleBendRef", None)
								
								ikControls = {
												"ikCtrl": ikCtrl, 
												"ikCtrlRef": ikCtrlRef,
												"poleVector": poleVector,
												"poleVectorRef": poleVectorRef,
												"ankleBendCtrl": ankleBendCtrl,
												"angleBendRef": angleBendRef,
												}

	return fkControls, ikControls, blendAttrHolder

def limbMatchFkIK(limbCtrl, mode = 0, **kwargs):
	"""
	mode 0 - Match FK to IK
	mode 1 - Match IK to FK
	"""
	
	if limbCtrl:
		ctrlsAssembly = kwargs.get("ctrlsAssembly", {})
		fkControls = {}
		ikControls = {}
		blendAttrHolder = None
		
		if ctrlsAssembly:
			fkControls = ctrlsAssembly.get("fkControls", {})
			ikControls = ctrlsAssembly.get("ikControls", {})
			blendAttrHolder = ctrlsAssembly.get("hostCtrl", None)
		else:
			fkControls, ikControls, blendAttrHolder = getLimbModuleControls(limbCtrl, 2)
			
		if mode == 0:
			fkRoot = fkControls.get("fkRoot", None)
			fkRootRef = fkControls.get("fkRootRefA", None)
			if not fkRootRef: fkRootRef = fkControls.get("fkRootRef", None)
			fkMid = fkControls.get("fkMid", None)
			fkMidRef = fkControls.get("fkMidRefA", None)
			if not fkMidRef: fkMidRef = fkControls.get("fkMidRef", None)
			fkMidB = fkControls.get("fkMidB", None)
			fkMidBRef = fkControls.get("fkMidBRefA", None)
			fkEnd = fkControls.get("fkEnd", None)
			fkEndRef = fkControls.get("fkEndRefA", None)
			if not fkEndRef: fkEndRef = fkControls.get("fkEndRef", None)

			if fkRoot and fkMid and fkEnd:
				blendAttrHolder.ikFkBlend.set(0.0)

				pm.matchTransform(fkRoot, fkRootRef)
				pm.matchTransform(fkMid, fkMidRef)
				if fkMidB: pm.matchTransform(fkMidB, fkMidBRef) #hindLimb case
				pm.matchTransform(fkEnd, fkEndRef)

				blendAttrHolder.ikFkBlend.set(1.0)
		else:
			ikCtrl = ikControls.get("ikCtrl", None)
			ikCtrlRef = ikControls.get("ikCtrlRef", None)
			poleVector = ikControls.get("poleVector", None)
			poleVectorRef = ikControls.get("poleVectorRef", None)

			if ikCtrl and poleVector and poleVectorRef:
				blendAttrHolder.ikFkBlend.set(1.0)
				pm.matchTransform(ikCtrl, ikCtrlRef)
				pm.matchTransform(poleVector, poleVectorRef)    
				blendAttrHolder.ikFkBlend.set(0.0)

			fkMidB = fkControls.get("fkMidB", None)
			ankleBendCtrl = ikControls.get("ankleBendCtrl", None)
			angleBendRef = ikControls.get("angleBendRef", None)

			if fkMidB and ankleBendCtrl and angleBendRef: #hindLimb case
				tempAimLoc = mnsUtils.createNodeReturnNameStd(buildType = "locator")
				pm.matchTransform(tempAimLoc.node, angleBendRef)
				aimCns = mnsNodes.mayaConstraint([tempAimLoc.node], ankleBendCtrl, type = "aim", aimVector = [1.0,0.0,0.0], upVector = [0.0,0.0,1.0], maintainOffset = True, worldUpObject = poleVector.nodeName())
				pm.matchTransform(tempAimLoc.node, fkMidB)
				pm.delete(aimCns.node)
				pm.delete(tempAimLoc.node)

		#pm.dgdirty()
		#pm.refresh()

###############################
############ CNS ##############
###############################

def compileCnsCtrlsAttrString(exsitingCnsCtrlsDict = {}):
	return mnsString.flattenArray(exsitingCnsCtrlsDict.keys())

def createCnsForCtrls(ctrls = []):
	"""This method is used to create CNS controls/sub-controls for existing puppet controls.
	In case you need to add extra offset controls in order to constraint them to other components, you can use this method.
	Pass in a list of controls you want to add sub-controls to, and run.
	This method is also the one used by the CNS Tool.
	"""

	returnState = False

	if not type(ctrls) is list: ctrls = [ctrls]
	selection = ctrls or pm.ls(sl = True)
	ctrlSelection = []

	if selection:
		for node in selection:
			nameStd = mnsUtils.validateNameStd(node)
			if nameStd:
				status, blkClassID = mnsUtils.validateAttrAndGet(nameStd, "blkClassID", None)
				if blkClassID and blkClassID == mnsPS_ctrl and nameStd.suffix == mnsPS_ctrl: ctrlSelection.append(nameStd)

	if ctrlSelection:
		for ctrl in ctrlSelection:
			status, cnsCtrl = mnsUtils.validateAttrAndGet(ctrl, "cnsMaster", None)
			if cnsCtrl:
				mnsLog.log(cnsCtrl.nodeName() + " already has a CNS. Aborting.", svr = 2)
				#select row in QTreeWidget
			else:
				rigTop = getRigTop(ctrl)
				if rigTop:
					#create the cns duplicateCtrl
					cnsName = mnsUtils.returnNameStdChangeElement(ctrl, suffix = mnsPS_cnsCtrl, autoRename = False)
					cnsCtrlDup = pm.duplicate(ctrl.node, name = cnsName.name)[0]
					pm.delete(cnsCtrlDup.listRelatives(c = True, type = "transform"))
					cnsCtrl = mnsUtils.validateNameStd(cnsCtrlDup)
					
					cnsOffsetName = mnsUtils.returnNameStdChangeElement(cnsCtrl, suffix = mnsPS_cnsGrp, autoRename = False)
					cnsCtrlDup = pm.duplicate(cnsCtrl.node, name = cnsOffsetName.name)[0]
					cnsOffset = mnsUtils.validateNameStd(cnsCtrlDup)
					mnsUtils.lockAndHideTransforms(cnsOffset.node, lock = False, keyable = True, cb = True)
					pm.scale(cnsOffset.node, 1.2, 1.2, 1.2, r = True)
					pm.makeIdentity(cnsOffset.node, a = True, t = False, s = True)
					pm.parent(cnsCtrl.node, cnsOffset.node)
					pm.makeIdentity(cnsOffset.node)
					try:
						pm.cutKey(ctrl.node, animation = "objects")
						pm.pasteKey(cnsCtrl.node, animation = "objects", option = "replaceCompletely")
					except: pass

					status, rigTopCnsAttr = mnsUtils.validateAttrAndGet(rigTop, "cnsCtrls", None, returnAttrObject = True)
					if not status: rigTopCnsAttr = mnsUtils.addAttrToObj(rigTop, name = "cnsCtrls" , type = "string", value = "", locked = True, cb = False, keyable = False)[0]
					
					#reconstruct vis-connections
					visInCon = ctrl.node.v.listConnections(d = False, s = True, p = True)
					if visInCon:
						visInCon = visInCon[0]
						visInCon >> cnsCtrl.node.v
						ctrl.node.v.disconnect()

					for shape in ctrl.node.getShapes(): shape.v.set(False)
					cnsOffset.node.v.set(True)
					cnsCtrl.node.v >> ctrl.node.v
					cnsCtrl.node.v >> cnsOffset.node.v
					
					#restore all keyable connections
					for attr in ctrl.node.listAttr(k = True, ud = True):
						if not attr.isLocked():
							cnsCtrl.node.attr(attr.attrName()) >> attr 

					#offsetCtrlVisAttr
					mnsUtils.addAttrToObj(cnsCtrl, type = "enum", value = ["______"], name = "CNS", replace = True, locked = True)
					offsetCtrlVisAttr = mnsUtils.addAttrToObj(cnsCtrl, name = "offsetCtrlVis" , type = "bool", value = True, locked = False, cb = True, keyable = True)[0]
					for shape in cnsOffset.node.getShapes(): 
						offsetCtrlVisAttr >> shape.v

					exsitingCnsCtrls = getExisingCnsCtrlsForRigTop(rigTop)
					exsitingCnsCtrls.update({cnsCtrl.node.nodeName(): ctrl})
					newAttrValue = compileCnsCtrlsAttrString(exsitingCnsCtrls)
					mnsUtils.setAttr(rigTopCnsAttr, newAttrValue)
					
					#mnsNodes.mnsMatrixConstraintNode(sources = [cnsCtrl.node], targets = [ctrl.node], connectRotate = True, connectTranslate = True, connectScale = True, maintainOffset = False)
					parentConstraint = mnsNodes.mayaConstraint([cnsCtrl.node], ctrl.node, type = "parent", maintainOffset = False)
					scaleConstraint = mnsNodes.mayaConstraint([cnsCtrl.node], ctrl.node, type = "scale", maintainOffset = False)
					
					cnsMasterAttr = mnsUtils.addAttrToObj(ctrl, name = "cnsMaster" , type = "message", locked = False, cb = False, keyable = False, replace = True)[0]
					cnsCtrl.node.message >> cnsMasterAttr

					cnsSlaveAttr = mnsUtils.addAttrToObj(cnsCtrl, name = "cnsSlave" , type = "message", locked = False, cb = False, keyable = False, replace = True)[0]
					ctrl.node.message >> cnsSlaveAttr

					pm.select(cnsCtrl.node, r = True)
					returnState = True

	#return; bool (success state)
	return returnState

def removeCnsFromCtrls(ctrls = []):
	"""This method is used to remove existing CNS controls/sub-controls for existing puppet controls.
	If you have CNS controls you want to remove, use this method.
	Pass in a list of controls you want to remove sub-controls from, and run.
	This method is also the one used by the CNS Tool.
	"""

	returnState = False

	if not type(ctrls) is list: ctrls = [ctrls]
	selection = ctrls or pm.ls(sl = True)
	ctrlSelection = []

	if selection:
		for node in selection:
			nameStd = mnsUtils.validateNameStd(node)
			if nameStd:
				status, blkClassID = mnsUtils.validateAttrAndGet(nameStd, "blkClassID", None)
				if blkClassID and blkClassID == mnsPS_ctrl and nameStd.suffix == mnsPS_cnsCtrl: ctrlSelection.append(nameStd)

	if ctrlSelection:
		for cnsCtrl in ctrlSelection:
			originCtrl = None
			status, originCtrl = mnsUtils.validateAttrAndGet(cnsCtrl, "cnsSlave", None)
			originCtrl = mnsUtils.validateNameStd(originCtrl)

			if originCtrl:
				#reconstruct vis-connections
				visInCon = cnsCtrl.node.v.listConnections(d = False, s = True, p = True)
				if visInCon:
					visInCon = visInCon[0]
					visInCon >> originCtrl.node.v

				try: pm.cutKey(ctrl.node, animation = "objects")
				except: pass

				outCons = cnsCtrl.node.worldMatrix[0].listConnections(d = True, s = False)
				for outCon in outCons:
					if type(outCon) == pm.nodetypes.MnsMatrixConstraint:
						pm.delete(outCon)


				pm.delete(cnsCtrl.node.getParent())

				try: pm.pasteKey(originCtrl.node, animation = "objects", option = "replaceCompletely")
				except: pass

				pm.showHidden(originCtrl.node)
				pm.select(originCtrl.node, r = True)
				returnState = True

	#return; bool (success state)
	return returnState

def getCompundChildren(rootGuide = None):
	compoundChildren = []

	rootGuide = mnsUtils.validateNameStd(rootGuide)
	if rootGuide:
		compoundChildren = [mnsUtils.validateNameStd(c.node()) for c in pm.listConnections(rootGuide.node.message, d = True, s = False, p = True) if c.attrName() == "compoundMaster"]
	return compoundChildren

def getModuleSettings(rootGuide, firstAttempt = True, **kwargs):
	"""Get passed in module settings.
	First get the default settings and values from the build-module directory,
	then compare against the rootGuide attributes, and return the filtered and altered settings.
	"""

	includeCreationOnly = kwargs.get("includeCreationOnly", False)
	getDefaults = kwargs.get("getDefaults", False)

	split = 0
	if rootGuide:
		rigTop = getRigTopForSel()
		settingsPath = os.path.join(dirname(abspath(__file__)), "allModSettings.modSettings").replace("\\", "/")
		optArgsFromFile, sidePlaceHolder = getSettings(settingsPath, rootGuide, mnsPS_gRootCtrl)
		if not includeCreationOnly: optArgsFromFile = filterCreationOnlyFromArgs(optArgsFromFile)

		modSetFile = os.path.join(rootGuide.node.modPath.get(), rootGuide.node.modType.get() + ".modSettings").replace("\\", "/")
		if not os.path.isfile(modSetFile) and firstAttempt:
			missingModuleActionTrigger(rigTop, rootGuide.node.modType.get(), self.buildModulesBtns)
			return getModuleSettings(rootGuide, firstAttempt = False)

		if os.path.isfile(modSetFile):
			pm.select(rootGuide.node)
			modArgs = mnsUtils.readSetteingFromFile(modSetFile)

			if not includeCreationOnly: 
				optArgsFromFile = filterCreationOnlyFromArgs(optArgsFromFile)
				modArgs = filterCreationOnlyFromArgs(modArgs)

			split = len(optArgsFromFile)
			
			for oArg in modArgs:
				match = False
				for arg in optArgsFromFile:
					if oArg.name == arg.name:
						arg.default = oArg.default
						arg.min = oArg.min
						arg.max = oArg.max
						arg.disabled = oArg.disabled
						arg.multiRowList = oArg.multiRowList
						match = True
						break
				if not match:
					optArgsFromFile.append(oArg)

			#optArgsFromFile =  optArgsFromFile + modArgs
			optArgsFromFile, sidePlaceHolder = filterSettings(optArgsFromFile, rootGuide.node)
			
			#return; dict,int (optionalArguments, spilt index - for dynUI)
			return optArgsFromFile, split

		else: mnsLog.log("Can't find module path. Aborting.", svr = 3)

