"""=== Author: Assaf Ben Zur ===
This is the core BLOCK Build-Modules class library.
This package contains the three main classes for BLOCK:
	- MnsBuildModuleBtn
	- MnsRig
	- MnsBuildModule

Most core function are defined within the classes, although any external functionality is maintained in 'blockUtility' py module.
The objective of these classes are mainly effeciant data gathering, constructing and deconstructing modules within a rig group.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from pymel.internal.factories import virtualClasses
import os, json, sys, imp, math, traceback, maya.mel, time
from os.path import dirname, abspath  
import maya.mel as mel

#mns dependencies
from ...core.prefixSuffix import *
from ...core.globals import *
from ...core import log as mnsLog
from ...core import arguments as mnsArgs
from ...core import nodes as mnsNodes
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import string as mnsString
from ...globalUtils import dynUI as mnsDynUI
from . import controlShapes as blkCtrlShps
from . import blockUtility as blkUtils

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtWidgets, QtGui
else:
	from PySide2 import QtWidgets, QtGui

mansur = __import__(__name__.split('.')[0])

class MnsBuildModuleBtn(object):
	"""The procedural 'module' button class.
	This class is being called and constructed procedurally from the file system based on folder contents.
	The class itself isn't inhereting from QPushButton, as it only exists to contain build location information.
	The class contains a constuctor only, which initializes the following information:
		- The full-path to the buildModule 
		- The layout Parent of the button
		- The group of the button, based on the folder structure of which the bm is located in.
		- The 'settings' file-path.
		- Short-Name
		- The obselete - 'isMayaNative' attribute.

	This information will be accessed once the related QPushButton will be triggered.
	"""

	def __init__(self, path, **kwargs):
		self.path = path
		#get module name from path
		self.moduleName = os.path.basename(os.path.normpath(path))
		mnsLog.log("MnsBuildModuleBtn Class Initialize - " + self.moduleName + ".")

		#get groupType From Path
		parent = os.path.dirname(self.path)
		self.groupType = os.path.basename(os.path.normpath(parent))
		
class MnsRig(object):
	"""This is the main 'RIG' data class.
	This class's constructor will initialize and build all relevant information regarding the 'rig' top top group.
	As The rig topGrp has pre-defined structure, and many dependencies, all basic information will be checked every time this class is constructed.
	The essence of this class is first of all to build the predefined rigGroup,
	then, to store and parse all relevant data from the scene, as well as validating it and rebuilding any sub-components if necessary.
	The procedural settings UI build will be initiated if a rig top wasn't found in the current scene selection (or if there is no selection).
	In case a rigTop already exists, it will first be validated, then it's setting will be read and parsed, initiating the the same UI draw, in "edit" mode.
	""" 

	def __init__(self, callerSubClass = None, **kwargs):
		"""Class constructor.
		"""

		mnsLog.log("MnsRig Class Initialize.")

		mnsLog.log("Getting Rig-Top.")
		sourceObjects = kwargs.get("sourceObjects", pm.ls(sl=True)) #arg
		self.rigTop = kwargs.get("rigTop", None)
		if sourceObjects: 
			self.rigTop = blkUtils.getRigTop(sourceObjects[0])
			if self.rigTop: mnsLog.log("Found Rig Top: \'" + self.rigTop.node + "\'")
			else: mnsLog.log("Couldn't find Rig-Top.", svr = 1)

		self.rootGuide = None
		if self.rigTop: self.rootGuide = blkUtils.getRootGuideFromRigTop(self.rigTop)

		#locals
		self.callerSubClass = callerSubClass
		self.modules = {}
		self.buildModulesBtns= kwargs.get("buildModulesBtns", None) #arg
		self.puppetBase = blkUtils.getPuppetRootFromRigTop(self.rigTop)
		self.baseGuide = blkUtils.getRootGuideFromRigTop(self.rigTop)
		self.rootJnt = None
		self.buildTimer = None

		#Initialize.
		if not self.rigTop:
			mnsLog.log("Launching new Rig-Top creation UI.", svr = 1)
			settingsPath = os.path.join(dirname(abspath(__file__)), "charInitSettings.charSet").replace("\\", "/")
			optArgs = mnsUtils.readSetteingFromFile(settingsPath)
			optArgs = blkUtils.preCheckNameForUI(optArgs, mnsPS_rigTop)
			self.loadSettingsWindow(runCmd = self.createNewRigTop, 
									customArgs = optArgs, 
									winTitle = "Mansur - BLOCK- Create RigTop", 
									title = "Block Rig Top Creation Settings", 
									split = len(optArgs) - 12, 
									firstTabTitle = "Main", 
									secondTabTitle = "Custom Scripts",
									icon = GLOB_guiIconsDir + "/logo/block_t5.png")
		elif self.buildModulesBtns: #existing rig top, collect all buildModules
			self.collectBuildModules()

	def createSubGrpsForRigTop(self, rigTop = None):
		"""This wrapper creates all the sub-group components for a given main rigTop group.
		The sub-groups defenition is the following:
			- guideGrp - Guides group component
			- puppetGrp - The Puppet group.
			- jointStructGrp - Joint Structure group
			- pickerLayoutGrp - Picker Layout guiides group.
			- controlShapesGrp - Stored custom shapes group.
			- freeJointsGrp - "Free joints" group, containing interLocs as intermediate objects to the interJoints in the main joint structure.
		"""

		if rigTop:
			for subGrp in ["puppetGrp", "guideGrp", "jointStructGrp", "pickerLayoutGrp","controlShapesGrp", "freeJointsGrp", "offsetSkeletonGrp", "extraSetupGrp", "modelGrp"]:
				create = False
				if rigTop.node.hasAttr(subGrp):
					if not rigTop.node.attr(subGrp).get(): create = True
				else: create = True
				if create: self.createSubGroupForRigTop(rigTop, subGrpType = subGrp, default = 3)

			rigTop.node.controlShapesGrpVis.set(0)
			rigTop.node.pickerLayoutGrpVis.set(0)
			rigTop.node.extraSetupGrpVis.set(0)

			parentGuide = blkUtils.getGuideParent(rigTop.node)
			if not parentGuide:
				#createRoot guide
				jntStrctNode = rigTop.node.attr("jointStructGrp").get()
				jointStructure = mnsUtils.validateNameStd(jntStrctNode)
				kwargs = {"assetScale": rigTop.node.attr("assetScale").get()}
				rootJnt = self.createRootGuide(rigTop, **kwargs)
				pm.select(rootJnt.node, r = 1)
				pm.reorder(jointStructure.node, f = True)

			baseLay = blkUtils.getPickerLayoutBaseFromRigTop(rigTop)
			if not baseLay: baseLay = self.createPickerLayoutBase(rigTop)
			cam = blkUtils.getPickerLayoutCamFromRigTop(rigTop)
			if not cam: self.createPickerCam(rigTop, baseLay)
			projCam = blkUtils.getPickerProjectionCamFromRigTop(rigTop)
			if not projCam: self.createPickerProjectionCam(rigTop, baseLay)
			pickerLayoutGrp = blkUtils.getPickerGuidesGrpFromRigTop(rigTop)
			if not pickerLayoutGrp: self.createPickerGuideGrp(rigTop, baseLay)

	def createPickerTitleGrp(self, rigTop, pickerLayoutBase,**kwargs):
		"""Create the Picker Layout 'titles' sub-component.
		This group contains the mnsAnnotate locators to toggle PLG view between it's shape and it's title.
		"""

		rigTop = mnsUtils.validateNameStd(rigTop)
		titleGrp = None
		layoutGrp = None
		if rigTop.node.hasAttr("pickerLayoutGrp"):
			layoutGrp =  mnsUtils.validateNameStd(rigTop.node.attr("pickerLayoutGrp").get())
		if layoutGrp:
			titleGrp = mnsUtils.createNodeReturnNameStd(side = "center", body = "pickerGuidesTitles", alpha = rigTop.alpha, id = rigTop.id, buildType = "group", createBlkClassID = True)
			mnsUtils.addAttrToObj([rigTop.node], type = "message", value = titleGrp.node, name = "pickerTitleGrp", replace = True)
			pm.parent(titleGrp.node, layoutGrp.node)
			mnsUtils.lockAndHideAllTransforms(titleGrp.node, lock = True)

			#create annotate for base for grp safe keeping while deletion occured by the user
			titleNode = mnsNodes.mnsAnnotateNode(side = pickerLayoutBase.side, body = pickerLayoutBase.body, alpha = pickerLayoutBase.alpha, id = pickerLayoutBase.id, attributes = [(pickerLayoutBase.node.nodeName() + ".tx")], nameOnlyMode = True)
			mnsNodes.mnsMatrixConstraintNode(sources = [pickerLayoutBase.node], targets = [titleNode.node], connectRotate = False, connectScale = False)
			pm.parent(titleNode.node, titleGrp.node)
			titleNode.node.fontTransparency.set(0)
			blkUtils.connectSlaveToDeleteMaster(titleNode.node, pickerLayoutBase.node)

			#connectVisAttr
			if pickerLayoutBase:
				pickerLayoutBase.node.titleVis >> titleGrp.node.v
		#return;MnsNameStd (titleGrp)
		return titleGrp

	def createPickerGuideGrp(self, rigTop, pickerLayoutBase, **kwargs):
		"""Create the main Picker-Layout-Guides sub-component.
		"""

		rigTop = mnsUtils.validateNameStd(rigTop)
		guidesGrp = None
		layoutGrp = None
		if rigTop.node.hasAttr("pickerLayoutGrp"):
			layoutGrp =  mnsUtils.validateNameStd(rigTop.node.attr("pickerLayoutGrp").get())
		if layoutGrp:
			guidesGrp = mnsUtils.createNodeReturnNameStd(side = "center", body = "pickerGuides", alpha = rigTop.alpha, id = rigTop.id, buildType = "group", createBlkClassID = True)
			mnsUtils.addAttrToObj([rigTop.node], type = "message", value = guidesGrp.node, name = "pickerGuidesGrp", replace = True)
			pm.delete(pm.parentConstraint(pickerLayoutBase.node, guidesGrp.node))
			pm.parent(guidesGrp.node, layoutGrp.node)
			mnsUtils.lockAndHideAllTransforms(guidesGrp.node, lock = True)

			#connectVisAttr
			if pickerLayoutBase:
				adlNode = mnsNodes.adlNode((pickerLayoutBase.node.nodeName() + ".titleVis"), 0, None)
				mnsNodes.reverseNode([(adlNode.node.nodeName() + ".output")], [(guidesGrp.node.nodeName() + ".v")], side= guidesGrp.side, body = guidesGrp.body, alpha = guidesGrp.alpha, id = guidesGrp.id)

		#return;MnsNameStd (guidesGrp)
		return guidesGrp

	def createPickerLayoutBase(self, rigTop, **kwargs):
		"""Create Picker Layout Base control, and construct all of it's predefined attributes.
		The predefined attributes for the PLG base is the following:
			- width - Will define the width of the rig's picker window
			- height- Will define the height of the rig's picker window
			- titleVis - vis attr for the title-group
			- titleSize - a global scalar for all mnsAnnotate PLG titles.

		This group also contains a few vis control channels to allow easier edit for the PLGs:
			- bodyPrimaries
			- bodySecondaries
			- bodyTertiaries
			- facialPrimaries
			- facialSecondaries
			- facialTertiaries

		These sub-vis channels will be controled by a global toggle attribute:
			- pickerMode
		This will dictate the picker's scene vis mode, the toggle is between 'body' and 'facial' modes.
		As the picker inhabits to tabs - body and facial, these attributes will allow better manipulation of PLG, grouping them according to the actual picker window tab grouping.
		"""

		baseLayoutGuide = None
		rigTop = mnsUtils.validateNameStd(rigTop)
		layoutGrp = None
		if rigTop.node.hasAttr("pickerLayoutGrp"):
			layoutGrp =  mnsUtils.validateNameStd(rigTop.node.attr("pickerLayoutGrp").get())
		if layoutGrp:
			width = float(mnsUtils.getMansurPrefs()["Picker"]["pickerDefaultWidth"]) or 600.0
			height = float(mnsUtils.getMansurPrefs()["Picker"]["pickerDefaultHeight"]) or 800.0
			baseLayoutGuide = blkCtrlShps.ctrlCreate(
								controlShape = "square", 
								createBlkClassID = True, 
								createBlkCtrlTypeID = True, 
								blkCtrlTypeID = 0, 
								ctrlType = "pickerLayoutCtrl", 
								scale = 1, 
								alongAxis = 2, 
								side = "center", 
								body = rigTop.body, 
								alpha = rigTop.alpha, 
								id = 1)
			baseLayoutGuide.node.ty.set(-3000)
			pm.parent(baseLayoutGuide.node, layoutGrp.node)
			
			widthAttr = mnsUtils.addAttrToObj([baseLayoutGuide.node], type = "float", value = width, name = "width", replace = True)
			heightAttr = mnsUtils.addAttrToObj([baseLayoutGuide.node], type = "float", value = height, name = "height", replace = True)
			titleVis = mnsUtils.addAttrToObj([baseLayoutGuide.node], type = "bool", value = False, name = "titleVis", replace = True)
			titleSize = mnsUtils.addAttrToObj([baseLayoutGuide.node], type = "float", value = 11.0, name = "titleSize", replace = True)
			mnsNodes.mdNode([widthAttr[0], heightAttr[0], 1], [10, 10, 1], baseLayoutGuide.node.attr("scale"), operation = 2)
			mnsUtils.lockAndHideAllTransforms(baseLayoutGuide.node, lock = True)
			blkUtils.setCtrlCol(baseLayoutGuide, rigTop)
			mnsUtils.addAttrToObj([rigTop.node], type = "message", value = baseLayoutGuide.node, name = "pickerLayoutBase", replace = True)
			mnsNodes.mnsNodeRelationshipNode(side = baseLayoutGuide.side, alpha = baseLayoutGuide.alpha , id = baseLayoutGuide.id, master = baseLayoutGuide.node, slaves = [])

			#create the vis channels
			blkUtils.createPlgBaseVisChannels(baseLayoutGuide)
			
			self.createPickerCam(rigTop, baseLayoutGuide)

		#return;MnsNameStd (baseLayoutGuide)
		return baseLayoutGuide

	def createPickerCam(self, rigTop, pickerLayoutBase, **kwargs):
		"""Create the predefined "picker Layout View" camera within the rig.
		This camera will be used as the view camera when an "edit picker layout" trigger was initiated from BlockUI.
		The camera is orthographic, and will be used in a seperate display (Maya-Panel).
		This to allow easy view of the picker layout, and easy manipulation of PLG shapes and controls.
		"""

		sel = pm.ls(sl=1)
		layoutGrp = None
		cam = None
		if rigTop.node.hasAttr("pickerLayoutGrp"):
			layoutGrp =  mnsUtils.validateNameStd(rigTop.node.attr("pickerLayoutGrp").get())
		if pickerLayoutBase and layoutGrp:
			cam = mnsUtils.createNodeReturnNameStd(side = "center", body = pickerLayoutBase.body, alpha = pickerLayoutBase.alpha, id = pickerLayoutBase.id, buildType = "camera", createBlkClassID = True)
			pm.parent(cam.node, layoutGrp.node)
			cam.node.getShape().attr("orthographic").set(True)
			cam.node.attr("v").set(False)
			mnsUtils.lockAndHideAllTransforms(cam.node, lock = True, cb = True, keyable = True)
			cam.node.getShape().ow.setLocked(True)
			blkUtils.connectSlaveToDeleteMaster(cam, pickerLayoutBase)
			mnsUtils.addAttrToObj([rigTop.node], type = "message", value = cam.node, name = "pickerLayoutCam", replace = True)
			if rigTop.node.hasAttr("pickerLayoutGrpVis"): rigTop.node.attr("pickerLayoutGrpVis").set(1)
			
			imagePlaneNode = mnsNodes.imagePlaneNode(cam.node, body = pickerLayoutBase.body, side = pickerLayoutBase.side, alpha = pickerLayoutBase.alpha , id = pickerLayoutBase.id)
			imagePlaneNode.node.overrideDisplayType.set(2)
			imagePlaneNode.node.overrideEnabled.set(True)
			imagePlaneNode.node.ty.set(-3000)
			imagePlaneNode.node.tz.set(-1)
			pm.parent(imagePlaneNode.node, layoutGrp.node)
			mdNode = mnsNodes.mdNode([pickerLayoutBase.node.width, pickerLayoutBase.node.height, 0], [0.2,0.2,0], [imagePlaneNode.node.getShape().width, imagePlaneNode.node.getShape().height, ""])
			choice = mnsNodes.choiceNode([rigTop.node.bodyPickerImagePath, rigTop.node.facialPickerImagePath], imagePlaneNode.node.imageName)
			pickerLayoutBase.node.pickerMode >> choice.node.selector

			if len(sel) > 0: pm.select(sel, r = 1) 

		#return;MnsNameStd (Picker Layout Camera)
		return cam

	def createPickerProjectionCam(self, rigTop, pickerLayoutBase):
		"""Create the predefined "PLG Projection" camera within the rig.

		A dedicated mns node is used here - 'mnsCamreGateRatio':
		This dedicated node was written in order to control the camera shape 'gateRatio' attribute.
		Because this attribute isn't connectable (internal callback within the camera shape), 
		mnsCameraGateRatio inserts a custom maya-callback into itself, in-order to refresh the camera-gate in a "live" fashion,
		This will allow the user to edit the width and height of the projection camera, seeing a live feed of it's gate in the view.
		As the projection is based on the camera gate, it is very important for the user to see the actual gate used, while projecting PLG's.
		"""

		sel = pm.ls(sl=1)
		layoutGrp = None
		cam = None
		if rigTop.node.hasAttr("pickerLayoutGrp"):
			layoutGrp =  mnsUtils.validateNameStd(rigTop.node.attr("pickerLayoutGrp").get())
		if pickerLayoutBase and layoutGrp:
			cam = mnsUtils.createNodeReturnNameStd(side = "center", body = pickerLayoutBase.body, alpha = pickerLayoutBase.alpha, id = pickerLayoutBase.id, buildType = "projectionCamera", createBlkClassID = True)
			pm.parent(cam.node, layoutGrp.node)
			cam.node.attr("v").set(False)
			blkUtils.connectSlaveToDeleteMaster(cam, pickerLayoutBase)
			mnsUtils.addAttrToObj([rigTop.node], type = "message", value = cam.node, name = "pickerProjectionCam", replace = True)
			if rigTop.node.hasAttr("pickerLayoutGrpVis"): rigTop.node.attr("pickerLayoutGrpVis").set(1)

			mnsNodes.mnsCameraGateRatioNode(side = "center", body = pickerLayoutBase.body, alpha = pickerLayoutBase.alpha, id = pickerLayoutBase.id, camera = cam.node, widthInput = pickerLayoutBase.node.width, heightInput = pickerLayoutBase.node.height)
			pm.camera(cam.node, e= 1,  dfg = True, dgm = True, ff = 3, overscan = 1.1) 
			pm.delete(pm.parentConstraint("persp", cam.node))
			if len(sel) > 0: pm.select(sel, r = 1) 

		#return;MnsNameStd (Picker Projection Camera)
		return cam

	def createSubGroupForRigTop(self, rigTopNameStd, **kwargs):
		"""Create the predefined "guideGrp" or "freeJointsGrp" within the rig.

		Guides Group - Contains the module main guides.
		Free Joints Group - Contains the interpLocs intermediate matricies for the interJnts in the main jointStructure
		"""

		currentSelection = pm.ls(sl=True)

		subGrpType = kwargs.get("subGrpType", "") #arg; optionBox = jointStructGrp, guideGrp, puppetGrp
		default = kwargs.get("default", 1) #arg; 

		subGrp = mnsUtils.createNodeReturnNameStd(side = "center", body = rigTopNameStd.body, alpha = rigTopNameStd.alpha, id = rigTopNameStd.id, buildType = subGrpType, createBlkClassID = True)
		subGrp.node.inheritsTransform.set(False)
		self.createVisEnumAndConnect(rigTopNameStd, subGrp, default = default)

		mnsUtils.lockAndHideAllTransforms(subGrp.node, lock = True)
		pm.parent (subGrp.node, rigTopNameStd.node)
		mnsUtils.addAttrToObj([rigTopNameStd.node], type = "message", value = subGrp.node, name = subGrpType, replace = True)

		if subGrpType == "guideGrp": rigTopNameStd.node.attr(subGrpType + "Vis").set(1)
		if subGrpType == "freeJointsGrp": rigTopNameStd.node.attr(subGrpType + "Vis").set(0)
		if subGrpType == "pickerLayoutGrp": rigTopNameStd.node.attr(subGrpType + "Vis").set(0)

		pm.select(currentSelection, r = True)

		#return;MnsNameStd (guideGrp/freeJointsGrp)
		return subGrp

	def createNewRigTop(self, **kwargs):
		"""Create the main rig group, with all of its sub-Components within.
		"""

		rigTop = None
		rigTop = mnsUtils.createNodeReturnNameStd(side = "center", body = kwargs["characterName"], alpha = kwargs["alpha"], id = kwargs["id"], buildType = "rigTop", createBlkClassID = True)
		mnsLog.log("creating new rig top - \'" + rigTop.name + "\'.", svr = 1)

		for arg in kwargs.keys(): 
			locked, keyable, cb, minimum = True, False, False, None
			if arg == "assetScale": locked, keyable, cb, minimum= False, True, True, 0.01
			mnsUtils.addAttrToObj(rigTop, name = arg , type = type(kwargs[arg]), value = kwargs[arg], locked = locked, cb = cb, keyable = keyable, min = minimum)
		mnsUtils.addAttrToObj(rigTop, name = "jntStructHandles" , type = bool, value = False, locked = False, cb = True, keyable = True)
		mnsUtils.addAttrToObj(rigTop, name = "constructMode" , type = "enum", value = ["guides", "soft", "rig"], locked = True, cb = False, keyable = False)
		
		rigTop.node.assetScale >> rigTop.node.sx
		rigTop.node.assetScale >> rigTop.node.sy
		rigTop.node.assetScale >> rigTop.node.sz
		mnsUtils.lockAndHideAllTransforms(rigTop, lock = True)
		self.createSubGrpsForRigTop(rigTop)
		pm.select(rigTop.node.attr("rigRootGuide").get())

		if self.callerSubClass:
			self.callerSubClass.buildGuides(self.callerSubClass.MnsBuildModuleButton, rigTop = rigTop)
		
	def loadSettingsWindow(self, **kwargs):
		"""Load the dynamic "setting window" for the current rig.
		"""

		mnsLog.logCurrentFrame()
		win = mnsDynUI.MnsDynamicDefUI(None, **kwargs)
		win.loadUI()
		win.activateWindow()

	def createVisEnumAndConnect(self, masterStd, slaveStd, **kwargs):
		"""For any given slave MnsNameStd group passed in, create a generic vis channel and connect it.
		The Enums of the generic vis channels are the following:
		- hidden
		- normal
		- template
		- reference
		"""

		default = kwargs.get("default", 1) #arg; 

		slaveStd.node.attr("overrideEnabled").set(1)
		enumValues = ["hidden", "normal", "template", "reference"]
		if mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, slaveStd.suffix) == "puppetGrp":
			enumValues = ["hidden", "normal"]
			default = 0
		attr = mnsUtils.addAttrToObj(masterStd.node, name = mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, slaveStd.suffix) + "Vis", replace = True, type = list, value = enumValues)
		attr[0].set(default)
		attr[0] >> slaveStd.node.v
		mnsNodes.adlNode(attr[0], -1, slaveStd.node.attr("overrideDisplayType"))

		#return;PyAttribute (created attribute)
		return attr

	def createRootGuide(self, rigTopNameStd, **kwargs):
		"""Create the "world control guide", or "rigRootGuide".
		This rootGuide will be locked completely and will define the predefined "world" control for the puppet.
		This entity is mandatory.
		"""

		rootGuideScaleMultiplier = mnsUtils.getMansurPrefs()["Global"]["rootGuideScaleMultiplier"]
		gScale = mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]
		status, rootCtrlScale = mnsUtils.validateAttrAndGet(rigTopNameStd, "rootCtrlScale", 1.0)

		jntStructGrp = mnsUtils.validateNameStd(rigTopNameStd.node.attr("jointStructGrp").get())
		rootJnt = mnsUtils.createNodeReturnNameStd(side = "center", body = "rigRoot", alpha = "A", id = rigTopNameStd.id, buildType = "rootJoint", createBlkClassID = True)
		rootJnt.node.radius.set(gScale)
		rootJnt.node.attr("radius").showInChannelBox(False)
		pm.parent (rootJnt.node, jntStructGrp.node)
		mnsUtils.lockAndHideAllTransforms(rootJnt, lock = True, keyable = True, cb = True)

		guideGrp = mnsUtils.validateNameStd(rigTopNameStd.node.attr("guideGrp").get())
		gRootCtrl = blkCtrlShps.ctrlCreate(controlShape = "guidesRoot", createBlkClassID = True, createBlkCtrlTypeID = True, blkCtrlTypeID = 0, ctrlType = "guideRootCtrl", scale = gScale * rootGuideScaleMultiplier * rootCtrlScale, alongAxis = 1, side = "center", body = "blkRoot", alpha = "A", id = 1)
		mnsUtils.addAttrToObj([rigTopNameStd.node], type = "message", value = gRootCtrl.node, name = "rigRootGuide", replace = True, locked = False, cb = True, keyable = True)
		pm.parent(gRootCtrl.node, guideGrp.node)
		mnsUtils.lockAndHideAllTransforms(gRootCtrl, lock = True)
		guideGrp.node.attr("overrideDisplayType")>>gRootCtrl.node.attr("overrideDisplayType")
		blkUtils.setCtrlCol(gRootCtrl, rigTopNameStd)

		mnsNodes.mnsMatrixConstraintNode(side = gRootCtrl.side, alpha = gRootCtrl.alpha , id = gRootCtrl.id, targets = [rootJnt.node], sources = [gRootCtrl.node], connectScale = False)
		mnsNodes.mnsNodeRelationshipNode(side = gRootCtrl.side, alpha = gRootCtrl.alpha , id = gRootCtrl.id, master = gRootCtrl.node, slaves = [rootJnt.node])
		mnsUtils.addAttrToObj(gRootCtrl, name = "jntSlave" , type = "message", value = rootJnt.node, locked = True, cb = False, keyable = False)

		for attr in ["sx", "sy", "sz"]:
			gRootCtrl.node.attr(attr).setLocked(False)
			rigTopNameStd.node.assetScale>>gRootCtrl.node.attr(attr)
			gRootCtrl.node.attr(attr).setLocked(True)

		currentUpAxis = pm.upAxis(q=True, axis=True)
		if currentUpAxis == "z":
			mnsUtils.setAttr(gRootCtrl.node.rx, 90.0)
			
		#return;MnsNameStd (Root Guide)
		return rootJnt

	def collectBuildModules(self, **kwargs):
		"""Collect all build modules guide hierarchy into the 'modules' attribure of this class.
		This method will run through the rig, and attempt to collect it's guide heirarchy, validating the modules while collecting.
		"""

		mnsLog.log("Collecting rig module hireacrchy.", svr = 1)

		if self.rigTop and self.rootGuide:  
			rootGuides = [mnsUtils.validateNameStd(obj) for obj in self.rootGuide.node.listRelatives(ad = True, type = "transform") if obj.hasAttr("blkClassID") and obj.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gRootCtrl) and obj != self.rootGuide.node]

			for rootG in rootGuides:
				buildModule = MnsBuildModule(self.buildModulesBtns[rootG.node.modType.get()], rigTop = self.rigTop, newModule = False, rootGuide = rootG)
				buildModule.gatherRelatedGuides()
				buildModule.gatherRelatedCtrls()
				self.modules.update({buildModule.rootGuide.name: buildModule})

		else: mnsLog.log("Collect build modules failed. Couldn't find rigTop. Aborting.", svr = 3)

	def createPuppetRootCtrl(self, rigTop, **kwargs):
		"""Create the rig's predefined "puppetRoot" or "worldControl".
		This depends on the rootGuide of course, and transfer the rigs "Root-Joint" Authority from the rootGuide, to the new puppetRoot control.
		This method will return the new control, as well as store it in the 'puppetTopCtrl' attribute of this class.
		"""

		puppetRootCtrl = None
		if rigTop:
			self.rigTop = rigTop
			puppetBase = blkUtils.getPuppetBaseFromRigTop(rigTop)
			guideRoot = blkUtils.getRootGuideFromRigTop(rigTop)

			if puppetBase:
				rootGuideScaleMultiplier = mnsUtils.getMansurPrefs()["Global"]["rootGuideScaleMultiplier"]
				status, assetScale = mnsUtils.validateAttrAndGet(self.rigTop, "assetScale", 1.0)
				gScale = mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"] * assetScale
				status, rootCtrlScale = mnsUtils.validateAttrAndGet(self.rigTop, "rootCtrlScale", 1.0)

				alongAxis = 1
				currentUpAxis = pm.upAxis(q=True, axis=True)
				if currentUpAxis == "z": alongAxis = 2

				ctrl = blkCtrlShps.ctrlCreate(controlShape = "puppetRoot", createBlkClassID = True, createBlkCtrlTypeID = True, blkCtrlTypeID = 0, scale = gScale * rootGuideScaleMultiplier * rootCtrlScale, alongAxis = alongAxis, side = "center", body = "world", alpha = "A", id = 1, skipColor = True)
				
				mnsUtils.connectShapeColorRGB(guideRoot, ctrl)
				ctrl.node.sx>>ctrl.node.sy
				ctrl.node.sx>>ctrl.node.sz
				pm.parent(ctrl.node, puppetBase.node)
				mnsUtils.addAttrToObj([rigTop.node], type = "message", value = ctrl.node, name = "puppetRoot", replace = True, locked = False, cb = True, keyable = True)

				#ctrlPlayback vis
				mnsUtils.addAttrToObj(ctrl, type = "enum", value = ["______"], name = "ControlVisOnPlayback", replace = True, locked = True)
				ctrlVis = mnsUtils.addAttrToObj(ctrl, name = "hideControlsOnPlayback" , type = bool, value = False, locked = False, cb = True, keyable = False)[0]
				ctrlVis >> puppetBase.node.hideOnPlayback

				###transfer main joint authority to new control
				self.puppetTopCtrl = blkUtils.getPuppetRootFromRigTop(rigTop)
				self.baseGuide = blkUtils.getRootGuideFromRigTop(rigTop)
				self.rootJnt = blkUtils.getRelatedNodeFromObject(self.baseGuide)
				blkUtils.transferAuthorityToCtrl(self.rootJnt, self.puppetTopCtrl)

				## name puppet
				blkUtils.namePuppet(self.rigTop)

			#return;MnsNameStd (Root Guide)
			return ctrl

	def setVisChannelsBasedOnCunstructMode(self):
		"""A simple method to set the vis mode of the current rig based on it's construction state.
		The construction mode is read from the rigTop attribues.
		Construction modes:
		0: Guides - guideGrpVis = True, puppetGrpVis = False
		1: Intermediate (Partially built rig) - guideGrpVis = True, puppetGrpVis = True
		2: Puppet - guideGrpVis = False, puppetGrpVis = True
		"""

		if self.rigTop:
			mode = self.rigTop.node.constructMode.get()
			if mode == 0:
				self.rigTop.node.guideGrpVis.set(1)
				self.rigTop.node.puppetGrpVis.set(0)
			elif mode == 1:
				self.rigTop.node.guideGrpVis.set(1)
				self.rigTop.node.puppetGrpVis.set(1)
			elif mode == 2:
				self.rigTop.node.guideGrpVis.set(0)
				self.rigTop.node.puppetGrpVis.set(1)

	def getGlobalConstructionState(self):
		"""Gey the current rig construction state from rigTop attributes.
		"""

		mode = 0
		
		if self.rigTop:
			constructList = [self.modules[b].rootGuide.node.constructed.get() for b in self.modules.keys()]
			
			if True in constructList: 
				mode = 2
				if False in constructList: mode = 1

		#return;int (mode)
		return mode

	def destroyPuppetRootCtrl(self):
		"""This method will destroy the rig's puppetRoot control, and transfer the rig's root-joint authority back to it's rootGuide.
		"""

		puppetTopCtrl = blkUtils.getPuppetRootFromRigTop(self.rigTop)
		if mnsUtils.validateNameStd(puppetTopCtrl): 
			blkUtils.transferAuthorityToGuide(puppetTopCtrl)
			constructionState = self.getGlobalConstructionState()
			if constructionState == 0:
				pm.delete(puppetTopCtrl.node)

	def setConstructionMode(self):
		"""Set the construction state attribute of the current rig.
		"""

		if self.rigTop:
			mode = self.getGlobalConstructionState()

			mnsUtils.setAttr(self.rigTop.node.constructMode, mode)
			self.setVisChannelsBasedOnCunstructMode()

	def cunstructRigSpaces(self):
		"""Attempt to construct spaces for all 'modules' within the rig.
		"""

		for bm in self.modules: 
			self.modules[bm].constructSpaces()
			
			#postConstructActions
			moduleRootGuide = self.modules[bm].rootGuide
			if moduleRootGuide: 
				pyModule, methods = blkUtils.getPyModuleFromGuide(moduleRootGuide)
				if "postConstruct" in methods: 
					pyModule.postConstruct(mansur, self.modules[bm])

	def storePuppetBaseDefaults(self):
		"""This method is used to store the current 'Defaults' set for the puppet-root control on deconstruction.
		As deconstruction deletes all the controls, including the puppet-root, if any custom-defaults were set,
		its essential to store them, in order to re-create them on re-construction.
		This is a specific case for the root-control, as it isn't a 'build-module' hence, the generic defaults store for the build modules doesn't apply.
		related method: restorePuppetBaseDefaults
		"""

		puppetTopCtrl = blkUtils.getPuppetRootFromRigTop(self.rigTop)
		if mnsUtils.validateNameStd(puppetTopCtrl): 
			defaultAttrs = blkUtils.gatherCustomDefaultDictForCtrl(puppetTopCtrl)
			if defaultAttrs:
				defaultsString = json.dumps(defaultAttrs)
				mnsUtils.addAttrToObj([self.baseGuide.node], type = "string", value = defaultsString, name = "puppetBaseDefaults", locked = True, replace = True)
			elif self.baseGuide.node.hasAttr("puppetBaseDefaults"):
				self.baseGuide.node.puppetBaseDefaults.setLocked(False)
				pm.deleteAttr(self.baseGuide.node, attribute = "puppetBaseDefaults")

	def restorePuppetBaseDefaults(self):
		"""On reconstruction, attempt to restore the 'defaults' attribute for the puppet root, if there are any.
		related method: storePuppetBaseDefaults
		"""

		rootGuide = blkUtils.getRootGuideFromRigTop(self.rigTop)
		if rootGuide and self.puppetBase:
			if rootGuide.node.hasAttr("puppetBaseDefaults"):
				defaultAttrs = json.loads(rootGuide.node.puppetBaseDefaults.get())
				ctrlNode = self.puppetBase.node
				if ctrlNode:
					defaultsString = json.dumps(defaultAttrs)
					mnsUtils.addAttrToObj([ctrlNode], type = "string", value = defaultsString, name = "mnsDefaults", locked = True, replace = True)

	def failedConstructionCommand(self, fileName = ""):
		"""A global method to display and return a message dialog whenever a build fails.
		This method displays 3 options and returns a paraller state:
			- 0: 'Continue'
			- 1: 'Abort'
			- 2: 'Revert-Construction'
		"""

		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Critical)
		msg.setText("Custom Script Execution Failed: \n\'" + fileName + "\'\n\n" + traceback.format_exc())
		msg.setInformativeText('Please check the command editor for details.\nWhat do you want to do next ?')
		msg.setWindowTitle("Custom Script Execution Failed")
		msg.setWindowIcon(QtGui.QIcon(GLOB_guiIconsDir + "/logo/mansur_logo_noText.png"))

		spacer = QtWidgets.QSpacerItem(550, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
		msgLayout = msg.layout()
		msgLayout.addItem(spacer, msgLayout.rowCount(), 0, 1, msgLayout.columnCount())
		
		btn = QtWidgets.QPushButton()
		btn.setText("Continue")
		msg.addButton(btn, QtWidgets.QMessageBox.ButtonRole.AcceptRole)

		btn1 = QtWidgets.QPushButton()
		btn1.setText("Abort")
		msg.addButton(btn1, QtWidgets.QMessageBox.ButtonRole.RejectRole)
		
		"""
		btn2 = QtWidgets.QPushButton()
		btn2.setText("Revert-Construction")
		msg.addButton(btn2, QtWidgets.QMessageBox.ButtonRole.YesRole)
		"""

		reply = msg.exec_()

		#return;int (state/button clicked)
		return reply

	def executeCustomScripts(self, attrName = None):
		"""for the given 'customScripts' attribute: compile the run files, and execute (if set).
		"""

		returnState = True

		if attrName and self.rigTop:
			cbxPairing = {"preConstructScripts": "execPreConstruct",
							"postConstructScripts": "execPostConstruct",
							"preDeconstructScripts": "execPreDeconstruct",
							"postDeconstructScripts": "execPostDeconstruct"}

			if self.rigTop.node.hasAttr(cbxPairing[attrName]):
				if self.rigTop.node.hasAttr(attrName):
					customStepsString = self.rigTop.node.attr(cbxPairing[attrName]).get()
					if customStepsString:
						customStepsString = mnsString.splitStringToArray(self.rigTop.node.attr(attrName).get())
						for customScriptFile in customStepsString:
							customScriptFile = mnsUIUtils.convertRelativePathToAbs(customScriptFile)
							
							if os.path.isfile(customScriptFile):
								mnsLog.log("Executing custom-script: " + customScriptFile.split("/")[-1] + ".", svr = 0)

								try: pyModule = imp.load_source("cScript", customScriptFile)
								except Exception as e: 
									print(traceback.format_exc())

									returnState = False
									mnsLog.log("Custom-Script execution failed: " + customScriptFile.split("/")[-1] + ".", svr = 3)
									reply = self.failedConstructionCommand(customScriptFile.split("/")[-1])
									if reply == 0: 
										pass
										returnState = True
									elif reply == 1: 
										break
										returnState = False
									"""
									elif reply == 2: 
										returnState = True
										##@@TODO inititate revert for build
									"""

		#return; bool (Execution success)
		return returnState

	def connectLODs(self):
		#find the attr if exists
		status, lodVisAttr = mnsUtils.validateAttrAndGet(self.baseGuide.node, "LOD_Vis", None, returnAttrObject = True)
		if status:
			#get all of it's option
			attrValues = mnsUtils.splitEnumToStringList("LOD_Vis", self.baseGuide.node)
			
			#get the attribute host if set
			attributeHost = self.puppetBase.node
			status, lodsDict = mnsUtils.validateAttrAndGet(self.baseGuide.node, "lodsDef", {})
			if status:
				lodsDict = json.loads(lodsDict)
				if "attrHost" in lodsDict.keys():
					attrHost = mnsUtils.validateNameStd(lodsDict["attrHost"])
					if attrHost:
						#convert attrHost to related control
						status, ctrlAuthority = mnsUtils.validateAttrAndGet(attrHost, "ctrlAuthority", None)
						if ctrlAuthority:
							attributeHost = ctrlAuthority

			#create the attribute on the host
			newAttr = mnsUtils.addAttrToObj([attributeHost], name = "LOD_Vis", type = list, value = attrValues, locked = False, cb = True, keyable = True)[0]

			#connect to orig attribute
			status, lodVisAttrDef = mnsUtils.validateAttrAndGet(self.baseGuide.node, "LOD_Vis", None)
			newAttr.set(lodVisAttrDef)
			newAttr >> lodVisAttr

	def createPredefinedCnsControls(self):
		status, preDefinedCnsCtrls = mnsUtils.validateAttrAndGet(self.rigTop.node, "preDefinedCnsCtrls", None, returnAttrObject = True)
		if status:
			preDefinedCnsCtrls = mnsUtils.splitEnumToStringList("preDefinedCnsCtrls", self.rigTop.node)
			if preDefinedCnsCtrls:
				validatedCtrls = []
				for cnsSlave in preDefinedCnsCtrls:
					cnsSlave = mnsUtils.validateNameStd(cnsSlave)
					if cnsSlave: validatedCtrls.append(cnsSlave)
				
				if validatedCtrls:
					blkUtils.createCnsForCtrls(validatedCtrls)

	def createRigInfo(self):
		if self.puppetBase:
			rigName = self.rigTop.body
			mnsVersion = mnsUtils.getCurrentVersion()
			timeStamp = time.ctime()
			user = "Unknown"
			numBuiltModules = len(self.modules.keys())
			buildTime = "N/A"
			mayaVersion = GLOB_mayaVersion
			if self.buildTimer:
				buildTime = str(round(pm.timerX(startTime=self.buildTimer), 2)) + " Seconds"
			compiledRigInfo = {"rigName": rigName,
								"mnsVersion": mnsVersion,
								"timeStamp": timeStamp,
								"mayaVersion": str(mayaVersion),
								"user": user,
								"numBuiltModules": numBuiltModules,
								"buildTime": buildTime}
			formattedRigInfo = json.dumps(compiledRigInfo)
			mnsUtils.addAttrToObj([self.puppetBase], type = "string", value = formattedRigInfo, name = "rigInfo", locked = True, replace = True)

	def constructRig(self, **kwargs):
		"""This method is the main 'Construction' call for a mnsRig.
		Flow:
		- Log, and set Timer
		- Collect all relevant data from the rig
		- Collect modules to build
		- Loop through the 'modules' dict attribute of this class:
			- Initiate the 'Construct' method for every buildModule class within the collection.
		"""

		progBar = kwargs.get("progressBar", None)
		self.buildTimer = kwargs.get("buildTimer", None)
		mnsLog.log("Initiating rig construct.", svr = 2)
		processCanceled = False

		#execute pre custom scrips
		customScriptsSuccessState = self.executeCustomScripts("preConstructScripts")

		if self.modules:
			mnsLog.log("Constructing modules.", svr = 1)
			partialModules = kwargs.get("partialModules", []) #arg

			buildPose = self.rigTop.node.rigConstructAtPose.get()
			shapesBuildMode = self.rigTop.node.shapesLoadMode.get()
			rootGuide = blkUtils.getRootGuideFromRigTop(self.rigTop)

			blkUtils.saveLoadPose([rootGuide], rigTop = self.rigTop, mode = 0, saveLoad = 1, pose = buildPose)
			
			modulesToBuild = self.modules.keys()
			if partialModules:
				mnsLog.log("Constructing partial.", svr = 0)
				modulesToBuild = partialModules

			mayaMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')
			pm.progressBar( mayaMainProgressBar, edit=True, beginProgress=True, isInterruptable=True, status='Block Rig Construction', maxValue=100)

			if progBar: progBar.setValue(5.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=5)

			k = 0
			for buildModule in sorted(modulesToBuild):
				if buildModule in self.modules.keys():
					buildModuleRet = self.modules[buildModule].construct()
					if not buildModuleRet:
						mnsLog.log("Couldn't find build path for module, attempting a module fix", svr = 0)
						status = blkUtils.attemptModulePathFixForRootGuide(self.modules[buildModule].rootGuide.node, self.buildModulesBtns)
						if status: 
							buildModuleRet = self.modules[buildModule].construct()
						else:
							mnsLog.log("Couldn't find build path for module (" + buildModule + "), module construction skipped.", svr = 3)
					
					buildModule = buildModuleRet

					blkUtils.buildShapes(buildModule.allControls, self.rigTop, mode= shapesBuildMode)
				progBarValue = 5.0 + (80.0 / len(modulesToBuild) * float(k +1) )
				if progBar: progBar.setValue(progBarValue)
				pm.progressBar(mayaMainProgressBar, edit=True, pr=progBarValue)
				k += 1

				#Esc break
				if pm.progressBar(mayaMainProgressBar, query=True, isCancelled=True):
					mnsLog.log("Esc key pressed! Canceling construction.", svr = 3)
					processCanceled = True
					break

			#constructSpaces
			mnsLog.log("Constructing spaces.", svr = 1)
			self.cunstructRigSpaces()
			if progBar: progBar.setValue(90.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=90)

			#set construction mode
			self.setConstructionMode()

			#select
			self.puppetBase = blkUtils.getPuppetRootFromRigTop(self.rigTop)
			if self.puppetBase: pm.select(self.puppetBase.node)
			
			if progBar: progBar.setValue(90.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=95)

			#defaults
			self.restorePuppetBaseDefaults()
			blkUtils.loadRigDefaults(0)
			#blkUtils.setRigDefaults(0)

			if progBar: progBar.setValue(95.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=95)

			#create and connect LOD attribute
			self.connectLODs()

			if progBar: progBar.setValue(97.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=95)

			#create predefined CNSs
			self.createPredefinedCnsControls()

			pm.refresh()
			pm.dgdirty()
			
			if progBar: progBar.setValue(98.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=95)

			#create rigInfo attribute
			self.createRigInfo()

			if progBar: progBar.setValue(100.0)
			pm.progressBar(mayaMainProgressBar, edit=True, endProgress=True)

		else:
			mnsLog.log("Selected rigTop does not contain any modules to construct. Aborting", svr = 2)	

		#execute post custom scrips
		customScriptsSuccessState = self.executeCustomScripts("postConstructScripts")

	def deconstructRig(self, **kwargs):
		"""This is the main deconstruction method for the rig.
		Flow:
		- Log, and set Timer
		- Collect all relevant data from the rig
		- Collect modules to build
		- Loop through the 'modules' dict attribute of this class:
			- Initiate the 'Deconstruct' method for every buildModule class within the collection.
		"""

		progBar = kwargs.get("progressBar", None)
		mnsLog.log("Initiating rig deconstruct.", svr = 2)
		buildTimer = pm.timerX()

		#execute pre custom scrips
		customScriptsSuccessState = self.executeCustomScripts("preDeconstructScripts")

		if self.modules:
			mnsLog.log("Deconstructing modules.", svr = 1)
			partialModules = kwargs.get("partialModules", [])

			modulesToBuild = self.modules.keys()
			if partialModules:
				mnsLog.log("Deconstructing partial.", svr = 0)
				modulesToBuild = partialModules

			mayaMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')
			pm.progressBar( mayaMainProgressBar, edit=True, beginProgress=True, isInterruptable=True, status='Block Rig Construction', maxValue=100)

			if progBar: progBar.setValue(5.0)
			pm.progressBar(mayaMainProgressBar, edit=True, pr=5)

			k = 0
			for buildModule in modulesToBuild:
				if buildModule in self.modules.keys():
					buildModuleRet = self.modules[buildModule].deconstruct(self)
					if not buildModuleRet:
						mnsLog.log("Couldn't find build path for module, attempting a module fix", svr = 0)
						status = blkUtils.attemptModulePathFixForRootGuide(self.modules[buildModule].rootGuide.node, self.buildModulesBtns)
						if status: buildModuleRet = self.modules[buildModule].deconstruct(self)
						else:
							mnsLog.log("Couldn't find build path for module (" + buildModule + "), module deconstruction skipped.", svr = 3)

				progBarValue = 5.0 + (90.0 / len(modulesToBuild) * float(k +1) )
				if progBar: progBar.setValue(progBarValue)
				pm.progressBar(mayaMainProgressBar, edit=True, pr=progBarValue)
				k += 1

				#Esc break
				if pm.progressBar(mayaMainProgressBar, query=True, isCancelled=True):
					mnsLog.log("Esc key pressed! Canceling deconstruction.", svr = 3)
					processCanceled = True
					break

			self.setConstructionMode()
			self.storePuppetBaseDefaults()
			self.destroyPuppetRootCtrl()
			if self.baseGuide: pm.select(self.baseGuide.node)
			if progBar: progBar.setValue(100.0)
			pm.progressBar(mayaMainProgressBar, edit=True, endProgress=True)
		else:
			mnsLog.log("Selected rigTop does not contain any modules to deconstruct. Aborting.", svr = 2)

		#execute post custom scrips
		customScriptsSuccessState = self.executeCustomScripts("postDeconstructScripts")
	
		buildTime = pm.timerX(startTime=buildTimer)
		mnsLog.log("Deconstruction finished at " + str(buildTime) + " Seconds.", svr = 1)

class MnsBuildModule(MnsRig):
	"""This class is the data store class for any mns 'build-module'.
	This class contains the actual creation and deletion of the module, guides and controls.
	This class will be initialized through the MnsRig class, althogh process functions regarding the modules are store in this class only.
	This class is purely procedular, and so it should remain.
	As the main goal of the rig is maintaining dynamic abilities, and easy creation of modules,
	this class should remain completely independent of any specific build module.
	Guides creation is partlly procedural, as any "main-guides" creation is fully automatic, 
	although custom-guides creation isn't- as it is module specific, hence it is store within the buildModule directory.
	Interp Joint Structure creation is procedural, although its essence is also defined within each build-module directory, althogh it is not mandatory.
	As the build modules are very specific and have to be created manually, guide creation is kept independent.
	This for easily creating modules, not needing to worrie about the handeling of guides, consruction and deconstruction.
	The actual flow of the build is independent of the modules setup internals.
	"""

	def __init__(self, MnsBuildModuleButton, **kwargs):
		"""Class constructor.
		"""

		self.MnsBuildModuleButton = MnsBuildModuleButton
		self.sidePlaceHolder = "center"
		self.builtGuides = None
		self.rigTop = kwargs.get("rigTop", None) #arg
		if not self.rigTop: self.rigTop = self.getRigTop()

		##gather
		self.dynUIIcon = kwargs.get("dynUIIcon", None)
		self.rootGuide = kwargs.get("rootGuide", None) #arg
		self.isFacial = False
		if self.rootGuide: self.isFacial = self.rootGuide.node.isFacial.get()

		self.rootCtrl = None
		self.guideControls = []
		self.cGuideControls = []
		self.pureParent = None
		self.attrHostCtrl = None
		self.extraChannelsHost = None
		self.compundModules = []

		self.moduleTop = None
		self.animGrp = None
		self.animStaticGrp = None
		self.rigComponentsGrp = None
		self.moduleSpaceAttrHost = None

		self.extraSpaces = []
		self.defaultSpace = None
		self.pureTops = None
		self.spaceSwitchCtrls = None
		self.internalSpaces = {}
		self.controls = None
		self.allControls = None

		newModule = kwargs.get("newModule", True) #arg
		moduleRoot = kwargs.get("moduleRoot", None) #arg

		if self.rigTop and newModule: self.buildGuides(MnsBuildModuleButton, **kwargs)
		self.puppetTopCtrl = blkUtils.getPuppetRootFromRigTop(self.rigTop)

	def reCollectControlsFromLocals(self):
		"""Re-initialize the 'allControls' attribute of this class, based on the current rig state.
		"""

		try: self.allControls = self.controls["primaries"] + self.controls["secondaries"] + self.controls["tertiaries"]
		except: pass

	def splitControlsBasedOnType(self):
		if self.allControls:
			collectCompound = [[], [], []]
			self.spaceSwitchCtrls = []

			for ctrl in self.allControls:
				status, blkCtrlTypeID = mnsUtils.validateAttrAndGet(ctrl, "blkCtrlTypeID", 0)
				status, isSpaceSwitchCtrl = mnsUtils.validateAttrAndGet(ctrl, "spaceSwitchControl", False)
				collectCompound[blkCtrlTypeID].append(ctrl)
				if isSpaceSwitchCtrl: self.spaceSwitchCtrls.append(ctrl)

				status, offsetRigSlaveIsParent = mnsUtils.validateAttrAndGet(ctrl, "offsetRigSlaveIsParent", False)
				if offsetRigSlaveIsParent:
					ocGrp = mnsUtils.createOffsetGroup(ctrl, type = "offsetCnsGrp")

			self.controls = {"primaries": collectCompound[0], "secondaries": collectCompound[1], "tertiaries": collectCompound[2]}

	def createModuleTopNode(self):
		"""This method is used to create the genric 'module top group' on module construction.
		"""

		status, symmetryType = mnsUtils.validateAttrAndGet(self.rootGuide, "symmetryType", 0)

		puppetRoot = blkUtils.getPuppetRootFromRigTop(self.rigTop)

		self.moduleTop = mnsUtils.createNodeReturnNameStd(side = self.rootGuide.side, body = self.rootGuide.body, alpha = self.rootGuide.alpha, id = self.rootGuide.id, buildType = "moduleTop", createBlkClassID = True)
		mnsUtils.lockAndHideTransforms(self.moduleTop.node, lock = True)
		mnsUtils.addAttrToObj([self.moduleTop.node], type = "bool", value = True, name = "primaryVis")
		mnsUtils.addAttrToObj([self.moduleTop.node], type = "bool", value = True, name = "secondaryVis")
		mnsUtils.addAttrToObj([self.moduleTop.node], type = "bool", value = True, name = "tertiaryVis")


		self.animGrp = blkCtrlShps.ctrlCreate(
							controlShape = "circle",
							createBlkClassID = True, 
							createBlkCtrlTypeID = True, 
							blkCtrlTypeID = -1, 
							ctrlType = "techCtrl",
							alongAxis = 0, 
							side = self.rootGuide.side, 
							body = self.rootGuide.body + "Anim", 
							alpha = self.rootGuide.alpha, 
							id = self.rootGuide.id,
							color = blkUtils.getCtrlCol(self.rootGuide, self.rigTop),
							matchTransform = self.rootGuide.node,
							createOffsetGrp = True,
							createSpaceSwitchGroup = True,
							parentNode = self.moduleTop.node,
							symmetryType = symmetryType,
							doMirror = True
							)

		pm.delete(self.animGrp.node.getShapes())
		animOffsetGrp = blkUtils.getOffsetGrpForCtrl(self.animGrp)
		#if animOffsetGrp: animOffsetGrp.node.ry.set(180)
		#self.animGrp = mnsUtils.createNodeReturnNameStd(parentNode = self.moduleTop, side = self.rootGuide.side, body = self.rootGuide.body + "Anim", alpha = self.rootGuide.alpha, id = self.rootGuide.id, buildType = "group", createBlkClassID = True)
		#pm.delete(pm.parentConstraint(self.rootGuide.node, self.animGrp.node))
		#animOffsetGrp = mnsUtils.createOffsetGroup(self.animGrp, type = "spaceSwitchGrp")
		#animOffsetGrp = mnsUtils.createOffsetGroup(self.animGrp)

		self.animStaticGrp = mnsUtils.createNodeReturnNameStd(parentNode = self.moduleTop, side = self.rootGuide.side, body = self.rootGuide.body + "AnimStatic", alpha = self.rootGuide.alpha, id = self.rootGuide.id, buildType = "group", createBlkClassID = True)
		#pm.delete(pm.parentConstraint(self.animGrp.node, self.animStaticGrp.node))
		
		self.rigComponentsGrp = mnsUtils.createNodeReturnNameStd(parentNode = self.moduleTop, side = self.rootGuide.side, body = self.rootGuide.body + "Components", alpha = self.rootGuide.alpha, id = self.rootGuide.id, buildType = "group", createBlkClassID = True)
		#pm.delete(pm.parentConstraint(self.animGrp.node, self.rigComponentsGrp.node))
		self.rigComponentsGrp.node.v.set(False)

	def createAttrHostCustomGuide(self):
		attrHostCusGuide = mnsUtils.createNodeReturnNameStd(parentNode = self.rootGuide, side = self.rootGuide.side, body = self.rootGuide.body + "AttrHost", alpha = self.rootGuide.alpha, id = self.rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(self.rootGuide.node, attrHostCusGuide.node))
		status, doAttributeHostCtrl = mnsUtils.validateAttrAndGet(self.rootGuide, "doAttributeHostCtrl", False)
		if not doAttributeHostCtrl: attrHostCusGuide.node.v.set(False)
		self.cGuideControls.append(attrHostCusGuide)

	def createGuides(self, **kwargs):
		"""This is the main guide creation method.
		This method contains all the steps needed to gather a module data, and create the guides for it.
		This method will return the built guides, as well as store it in this class 'builtGuides' attribute.
		"""

		mnsLog.logCurrentFrame()

		rigTopSettingsPath = os.path.join(dirname(abspath(__file__)), "charInitSettings.charSet").replace("\\", "/")
		rigTopArgs, self.sidePlaceHolder = blkUtils.getSettings(rigTopSettingsPath, self.rigTop, mnsPS_rigTop)
		rigTopArgs =  mnsArgs.formatArgumetsAsDict(rigTopArgs)
		moduleArgs = kwargs
		parentGuide = moduleArgs["parentGuide"]
		buildCompound = kwargs.get("buildCompound", True) #arg; 

		status, assetScale = mnsUtils.validateAttrAndGet(self.rigTop, "assetScale", 1.0)
		gScale = mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"] * assetScale
		spacing = gScale * 10

		builtJntsNodes = []
		builtGuides = []
		builtGuidesNodes = []
		prevGuide = parentGuide
		prevJoint = blkUtils.getRelatedNodeFromObject(parentGuide)
		prevJointRadius = None
		if prevJoint:
			prevJointRadius = prevJoint.radius.get()
		newAlpha = None

		for k in range(0, kwargs["numOfGuides"]):
			side = mnsSidesDict[kwargs.get("blkSide", "center")] #arg; 
			body = kwargs.get("body", "guideCtrl") #arg; 
			alpha = kwargs.get("alpha", "A") #arg; 
			alongAxis = kwargs.get("alongAxis", 1) #arg; 
			moduleScale = kwargs.get("moduleScale", 1) #arg; 
			self.isFacial = kwargs.get("isFacial", False) #arg; 

			gRootCtrl = None
			gJnt = None
			if k == 0: 
				gRootCtrl = blkCtrlShps.ctrlCreate(side = side, 
													body = body, 
													alpha = alpha, 
													id = k + 1, 
													controlShape = "directionCube", 
													createBlkClassID = True, 
													createBlkCtrlTypeID = True, 
													blkCtrlTypeID = 0, 
													ctrlType = "guideRootCtrl", 
													scale = gScale, 
													alongAxis = 1, 
													incrementAlpha = True,
													isFacial = self.isFacial)
				self.rootGuide = gRootCtrl

				newAlpha = gRootCtrl.alpha
				pm.parent(gRootCtrl.node, prevGuide)
				
				gJnt = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = newAlpha, id = k + 1, buildType = "rootJoint", createBlkClassID = True, incrementAlpha = True)
				mnsUtils.lockAndHideAllTransforms(gJnt, lock = True, keyable = True, cb = True)
				if prevJointRadius is None:
					gJnt.node.radius.set(gScale)
				else:
					gJnt.node.radius.set(prevJointRadius)
				pm.parent(gJnt.node, prevJoint)

				mnsNodes.mnsMatrixConstraintNode(side = gRootCtrl.side, alpha = gRootCtrl.alpha , id = gRootCtrl.id, targets = [gJnt.node], sources = [gRootCtrl.node], connectScale = False)
				mnsNodes.mnsNodeRelationshipNode(side = gRootCtrl.side, alpha = gRootCtrl.alpha , id = gRootCtrl.id, master = gRootCtrl.node, slaves = [gJnt.node])

				if kwargs["matchParentOrient"]:
					pm.delete(pm.parentConstraint(prevGuide, gRootCtrl.node))
				else:
					pm.delete(pm.pointConstraint(prevGuide, gRootCtrl.node))
					#orient guide based on along axis var
					tempLoc = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = newAlpha, id = k + 1, buildType = "locator")
					if kwargs["alongAxis"] == 0: tempLoc.node.rz.set(-90)
					elif kwargs["alongAxis"] == 2: tempLoc.node.rx.set(90)
					elif kwargs["alongAxis"] == 3: tempLoc.node.rz.set(90)
					elif kwargs["alongAxis"] == 4: tempLoc.node.rz.set(180)
					elif kwargs["alongAxis"] == 5: tempLoc.node.rx.set(-90)
					pm.delete(pm.orientConstraint(tempLoc.node, gRootCtrl.node))
					pm.delete(tempLoc.node)

				for arg in moduleArgs.keys(): 
					locked, keyable, cb = True, False, False
					attrType = type(kwargs[arg])
					if attrType != pm.nodetypes.Transform:
						mnsUtils.addAttrToObj(gRootCtrl, name = arg , type = attrType, value = kwargs[arg], locked = locked, cb = cb, keyable = keyable)
				mnsUtils.addAttrToObj(gRootCtrl, name = "modType" , type = str, value = self.MnsBuildModuleButton.moduleName, locked = locked, cb = cb, keyable = keyable)
				mnsUtils.addAttrToObj(gRootCtrl, name = "modPath" , type = str, value = self.MnsBuildModuleButton.path, locked = locked, cb = cb, keyable = keyable)
				mnsUtils.addAttrToObj(gRootCtrl, name = "constructed" , type = bool, value = False, locked = True, cb = False, keyable = False)
			else:
				gRootCtrl = blkCtrlShps.ctrlCreate(side = side, body = body, alpha = newAlpha, id = k + 1, controlShape = "directionSphere", createBlkClassID = True, createBlkCtrlTypeID = True, blkCtrlTypeID = 0, ctrlType = "guideCtrl", scale = gScale / 2, alongAxis = 1)
				pm.parent(gRootCtrl.node, prevGuide)
				pm.delete(pm.parentConstraint(prevGuide, gRootCtrl.node))
				gRootCtrl.node.ty.set(spacing)

				gJnt = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = newAlpha, id = k + 1, buildType = "joint", createBlkClassID = True, incrementAlpha = True)
				mnsUtils.lockAndHideAllTransforms(gJnt, lock = True, keyable = True, cb = True)
				if prevJointRadius is None:
					gJnt.node.radius.set(gScale)
				else:
					gJnt.node.radius.set(prevJointRadius)
				
				pm.parent(gJnt.node, prevJoint)

				mnsNodes.mnsMatrixConstraintNode(side = gRootCtrl.side, alpha = gRootCtrl.alpha , id = gRootCtrl.id, targets = [gJnt.node], sources = [gRootCtrl.node], connectScale = False)
				mnsNodes.mnsNodeRelationshipNode(side = gRootCtrl.side, alpha = gRootCtrl.alpha , id = gRootCtrl.id, master = gRootCtrl.node, slaves = [gJnt.node])

			mnsUtils.zeroJointOrient(gJnt.node)
			mnsUtils.addAttrToObj(gRootCtrl, name = "jntSlave" , type = "message", value = gJnt.node, locked = True, cb = False, keyable = False)
			color = (1,1,1)
			if kwargs["colOverride"]: color = kwargs["schemeOverride"][0]
			else: color = blkUtils.getCtrlCol(gRootCtrl, self.rigTop)
			mnsUtils.setCtrlColorRGB([gRootCtrl], color)
			
			if self.rigTop.node.hasAttr("jntStructHandles"): self.rigTop.node.attr("jntStructHandles") >> gJnt.node.attr("displayLocalAxis")
			gJnt.node.attr("radius").showInChannelBox(False)

			builtJntsNodes.append(gJnt.node)
			prevJoint = gJnt.node
			prevGuide = gRootCtrl.node
			builtGuides.append(gRootCtrl)
			builtGuidesNodes.append(gRootCtrl.node)

		pyModule, methods = None, []
		pyModule, methods = blkUtils.getPyModuleFromGuide(builtGuides[0])

		#build custom guides
		self.createAttrHostCustomGuide()
		parentDict = None

		if "customGuides" in methods:
			cGuideControls, parentDict = pyModule.customGuides(mansur, builtGuides)
			self.cGuideControls += cGuideControls

			newParent = blkUtils.getRootGuideFromRigTop(rigTop = self.rigTop.node)
			
		if self.cGuideControls:
			for cGuide in self.cGuideControls: 
				newParent = None
				if parentDict and cGuide in parentDict: newParent = parentDict[cGuide]
				cGuide = mnsUtils.returnNameStdChangeElement(nameStd = cGuide, suffix = mnsPS_cgCtrl)
				
				if newParent: pm.parent(cGuide.node, newParent.node)
				blkUtils.connectSlaveToDeleteMaster(cGuide, builtGuides[0])
				mnsUtils.setCtrlColorRGB([cGuide], color)
				mnsUtils.addBlockClasIDToObj(cGuide)

		if "moduleCompound" in methods and buildCompound:
			blockWin = mnsUIUtils.getWindow("mnsBLOCK_UI")
			if blockWin:
				self.compundModules = pyModule.moduleCompound(mansur, blockWin.bmLib, builtGuides, self, **kwargs)
			else:
				mnsLog.log("Coundl't find Block window, module compound metohd skipped.", svr = 2)

		#build joint struct
		if "jointStructure" in methods:
			blkUtils.deleteFreeJntGrpForModule(builtGuides[0])
			interpLocs = pyModule.jointStructure(mansur, builtGuides, self, **kwargs)
			blkUtils.handleInterpLocsStructureReturn(self.rigTop, interpLocs, builtGuides)
					
		pm.select(builtGuidesNodes[0])
		self.builtGuides = builtGuides 

		#return;list (bbuiltGuides)
		return builtGuides

	def getRigTop(self):
		"""get the rigTop nameStd from current selection. 
		If it doesn't exist, initiate a new rig top creation.
		"""

		rigTop = blkUtils.getRigTopForSel()

		if not rigTop: MnsRig(self)
		else: self.createSubGrpsForRigTop(rigTop)

		#return;MnsNameStd (rigTop)
		return rigTop

	def updateCreationArgsToSymmetryMode(self, optArgs):
		"""This method will alter the current setting to their symmetry mode,
		In case the 'symmetrize' flag was passed into the buildGuides method.
		Altered attributes:
		- side (or blkSide)
		- spaces- if a side related space was found, symmetrize the space as well.
		"""

		if optArgs:
			symSide = "right"
			if optArgs["blkSide"] == "right": symSide = "left"

			#update side
			if "blkSide" in optArgs: optArgs.update({"blkSide": symSide})

			#update spaces
			if "spaces" in optArgs and optArgs["spaces"]: 
				newSpaces = []
				for space in optArgs["spaces"]:
					space = space.replace("*", "")
					if space and space != "None":
						spaceStd = mnsUtils.validateNameStd(space)
						if spaceStd:
							if spaceStd.side == mnsPS_left or spaceStd.side == mnsPS_right:
								spaceSymSide = "r"
								if spaceStd.side == mnsPS_right: spaceSymSide = "l"
								symSpace = mnsUtils.returnNameStdChangeElement(spaceStd, side = spaceSymSide, autoRename = False)
								if symSpace: newSpaces.append(symSpace.name)
						else: newSpaces.append(space)
				if newSpaces: optArgs.update({"spaces": newSpaces})
				else: optArgs.update({"spaces": ["None"]})

			#return;dict (optionalArguments)
			return optArgs

	def collecteModuleSettings(self, rootGuide = None):
		if not self.builtGuides:
			self.builtGuides = blkUtils.getModuleGuideDecendents(rootGuide)

		if self.builtGuides:
			settingsHolder = self.builtGuides[0]
			allSettingsPath = os.path.join(dirname(abspath(__file__)), "allModSettings.modSettings").replace("\\", "/")
			if os.path.isfile(allSettingsPath):
				globArgs = mnsUtils.readSetteingFromFile(allSettingsPath)
				for arg in globArgs:
					if "side".lower() in arg.name.lower(): arg.default = mnsUtils.getSideFromNode(settingsHolder.node)
					if arg.name == "body": arg.default = self.MnsBuildModuleButton.moduleName
					if "side".lower() in arg.name.lower(): self.sidePlaceHolder  = arg.default
					elif "schemeOverride".lower() in arg.name.lower():
						colScheme = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList("colorScheme", self.rigTop)
						arg.default = mnsUIUtils.getColorArrayFromColorScheme(self.sidePlaceHolder, colScheme)

				settingsPath = os.path.join(self.MnsBuildModuleButton.path, self.MnsBuildModuleButton.moduleName + ".modSettings").replace("\\", "/")
				if os.path.isfile(settingsPath):
					split = len(globArgs)
					optArgs = mnsUtils.readSetteingFromFile(settingsPath)
					toRemove = []
					for arg in optArgs:
						for argA in globArgs:
							if arg.name == argA.name:
								globArgs[globArgs.index(argA)] = arg
								toRemove = []
								toRemove.append(arg)
					for arg in toRemove: optArgs.remove(arg)

					optArgs = globArgs + optArgs
					optArgs = blkUtils.preCheckNameForUI(optArgs, mnsPS_rJnt)
					title = self.MnsBuildModuleButton.moduleName + " Creation Settings"

					#gather args to dict
					if settingsHolder: optArgs, temp = blkUtils.filterSettings(optArgs, settingsHolder.node)
					optArgs = mnsArgs.formatArgumetsAsDict(optArgs)

						
					if settingsHolder: 
						if "numOfGuides" in optArgs: optArgs.update({"numOfGuides": len(self.builtGuides)})
					optArgs.update({"rigTop": self.rigTop, "parentGuide": self.builtGuides[0]})

					return optArgs

	def buildGuides(self, MnsBuildModuleButton, **kwargs):
		"""This method is the initialize method for new guides creation.
		This method will be called first (before 'createGuides') and will also load the modules creation settings window if neccessary.
		"""

		if not MnsBuildModuleButton: MnsBuildModuleButton = self.MnsBuildModuleButton

		skipUI = kwargs.get("skipUI", False) #arg; 
		skipGuidesCreation = kwargs.get("skipGuidesCreation", False) #arg; 
		mnsLog.log("Building module guides, with skipUI flag set to - " + str(skipUI) + ".")
		buildCompound = kwargs.get("buildCompound", True) #arg; 

		settingsHolder = kwargs.get("settingsHolder", None) #arg; 
		preDefinedSettings = kwargs.get("preDefinedSettings", {}) #arg; 
		symmetrize = kwargs.get("symmetrize", False) #arg; 

		_newRigTop = self.getRigTop()
		
		split = 0

		if _newRigTop: self.rigTop = mnsUtils.validateNameStd(_newRigTop)
		parentGuide = None
		currentSel = pm.ls(sl = 1)

		if currentSel:
			nStd = mnsUtils.validateNameStd(currentSel[0])
			if nStd.suffix == mnsPS_gCtrl or nStd.suffix == mnsPS_cgCtrl or nStd.suffix == mnsPS_gRootCtrl:
				parentGuide = blkUtils.getGuideParent(currentSel[0])
				if "parentGuide" in kwargs.keys(): parentGuide = kwargs["parentGuide"].node
			else:
				mnsLog.log("Please select a guide ctrl to create.", svr = 2)

		if parentGuide:
			pm.select(parentGuide, r= 1)
			allSettingsPath = os.path.join(dirname(abspath(__file__)), "allModSettings.modSettings").replace("\\", "/")
			if os.path.isfile(allSettingsPath):
				globArgs = mnsUtils.readSetteingFromFile(allSettingsPath)
				for arg in globArgs:
					if "side".lower() in arg.name.lower(): arg.default = mnsUtils.getSideFromNode(parentGuide)
					if "isFacial".lower() in arg.name.lower(): 
						status, isFacial = mnsUtils.validateAttrAndGet(blkUtils.getModuleRoot(parentGuide), "isFacial", False)
						if status: arg.default = isFacial

					if arg.name == "body": arg.default = MnsBuildModuleButton.moduleName
					if "side".lower() in arg.name.lower(): self.sidePlaceHolder  = arg.default
					elif "schemeOverride".lower() in arg.name.lower():
						colScheme = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList("colorScheme", self.rigTop)
						arg.default = mnsUIUtils.getColorArrayFromColorScheme(self.sidePlaceHolder, colScheme)

				settingsPath = os.path.join(MnsBuildModuleButton.path, MnsBuildModuleButton.moduleName + ".modSettings").replace("\\", "/")
				if os.path.isfile(settingsPath):
					split = len(globArgs)
					optArgs = mnsUtils.readSetteingFromFile(settingsPath)
					toRemove = []
					for arg in optArgs:
						for argA in globArgs:
							if arg.name == argA.name:
								arg.comment = argA.comment
								globArgs[globArgs.index(argA)] = arg
								toRemove.append(arg)
					for arg in toRemove: optArgs.remove(arg)

					optArgs = globArgs + optArgs
					optArgs = blkUtils.preCheckNameForUI(optArgs, mnsPS_gRootCtrl)

					title = MnsBuildModuleButton.moduleName + " Creation Settings"

					if not skipUI:
						mnsLog.log("Launching guide creation UI.", svr = 1)
						self.loadSettingsWindow(
											runCmd = self.buildGuideObjects, 
											customArgs = optArgs, 
											winTitle = "Mansur - BLOCK  ||  " + MnsBuildModuleButton.moduleName,
											title = title, 
											btnText = "Build " + MnsBuildModuleButton.moduleName + " Guides", 
											preDefinedArgs = { "parentGuide": parentGuide}, 
											rigTop = self.rigTop,
											split = split,
											icon = self.dynUIIcon)
					else:
						#gather args to dict
						if settingsHolder: optArgs, temp = blkUtils.filterSettings(optArgs, settingsHolder)
						optArgs = mnsArgs.formatArgumetsAsDict(optArgs)

						if symmetrize: optArgs = self.updateCreationArgsToSymmetryMode(optArgs)

						if settingsHolder: 
							if "numOfGuides" in optArgs: optArgs.update({"numOfGuides": len(blkUtils.getModuleGuideDecendents(settingsHolder))})
						optArgs.update({"rigTop": self.rigTop, "parentGuide": parentGuide})
						
						if preDefinedSettings:
							for preDefinedKey in preDefinedSettings:
								if preDefinedKey in optArgs.keys():
									optArgs[preDefinedKey] = preDefinedSettings[preDefinedKey]

						if not skipGuidesCreation:
							optArgs.update({"buildCompound": buildCompound})
							self.buildGuideObjects(**optArgs)
						else:
							return optArgs

	def buildGuideObjects(self, **kwargs):
		"""A simple method to gather the amount of needed guides to create, and calling the creation accordingly.
		"""

		mnsLog.log("Building new guides.", svr = 0)
		buildCompound = kwargs.get("buildCompound", True) #arg; 

		builtGuides = []
		mnsLog.logCurrentFrame()
		if kwargs["numOfGuides"]: builtGuides = self.createGuides(**kwargs)
		pm.select(builtGuides[0].node)

	def gatherAllDependecies(self):
		"""Gather all scene object dependecies for the buildModule.
		A simple wrapper containing 'gatherRelatedGuides' method & gatherRelatedCtrls method.
		"""

		self.gatherRelatedGuides()
		self.gatherRelatedCtrls()

	def gatherRelatedGuides(self):
		"""This method will gather the buildModules related guides from the rig.
		collected objects:
		- rootGuide
		- guides
		- customGuides

		The data collected is stored in their related class attributes:
		- rootGuide - 'rootGuide'
		- guides - 'guideControls'
		- custom guides - 'cGuideControls'
		"""

		if self.rootGuide:
			self.rootGuide = mnsUtils.validateNameStd(self.rootGuide)
			if self.rootGuide:
				self.pureParent = mnsUtils.validateNameStd(self.rootGuide.node.getParent())
				unicodeSpaces = mnsUtils.splitEnumToStringList("spaces", self.rootGuide.node)
				if unicodeSpaces:
					defaultIndex = 0
					for j, s in enumerate(unicodeSpaces):
						if "*" in s:
							s = s.replace("*", "")
							self.defaultSpace = s

						#space = mnsUtils.validateNameStd(s)
						#if space: 
						self.extraSpaces.append(s)

				children = blkUtils.getModuleDecendentsWildcard(self.rootGuide, getJoints = False, getGuides = True, getCustomGuides = True)

				if children:
					for child in children:
						if child.node.hasAttr("blkClassID"):
							childClass = child.node.blkClassID.get()
							if childClass == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_gCtrl): self.guideControls.append(child)
							if childClass == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_cgCtrl): self.cGuideControls.append(child)

	def gatherRelatedCtrls(self):
		"""This method will collect and store the build-module related control objects from the rig.
		"""

		if self.rootGuide:
			self.rootGuide = mnsUtils.validateNameStd(self.rootGuide)
			if self.rootGuide:
				if self.rootGuide.node.hasAttr("ctrlAuthority"):
					self.rootCtrl = self.rootGuide.node.ctrlAuthority.get()
				self.moduleTop = blkUtils.getModuleTopFromRootGuide(self.rootGuide)
				
				if self.moduleTop:
					#get all pureTops &ctrls dict
					self.pureTops = [mnsUtils.validateNameStd(c) for c in self.moduleTop.node.listRelatives(c = True, type = "transform")]

					primaries = []
					secondaries = []
					tertiaries = []
					spaceSwitchCtrls = []

					for ctrl in self.moduleTop.node.listRelatives(ad = True, type = "transform"): 
						ctrl = mnsUtils.validateNameStd(ctrl)
						if ctrl:
							if ctrl.suffix == mnsPS_ctrl or ctrl.suffix == mnsPS_techCtrl:
								if ctrl.node.hasAttr("blkCtrlTypeID"):
									if ctrl.node.blkCtrlTypeID.get() == 0: primaries.append(ctrl)
									elif ctrl.node.blkCtrlTypeID.get() == 1: secondaries.append(ctrl)
									elif ctrl.node.blkCtrlTypeID.get() == 2: tertiaries.append(ctrl)

									if ctrl.node.hasAttr("spaceSwitchControl"):
										if ctrl.node.spaceSwitchControl.get(): spaceSwitchCtrls.append(ctrl)

					self.controls = {"primaries": primaries, "secondaries": secondaries, "tertiaries": tertiaries}
					self.spaceSwitchCtrls = spaceSwitchCtrls
					self.reCollectControlsFromLocals()

	def connectVisChannels(self):
		"""This method will connect this module into it's related vis channel in the puppet root control.
		"""

		controlTypes = ["primaries", "secondaries", "tertiaries"]
		attrNames = ["primaryVis", "secondaryVis", "tertiaryVis"]
		for j in range(3):
			for ctrl in self.controls[controlTypes[j]]: 
				try: 
					blkUtils.createVisibilityBridgeMdl(self.moduleTop.node.attr(attrNames[j]), ctrl.node.v)
				except: pass

	def restoreCustomDefaults(self):
		"""This method will attempt to restore any pre-stored 'defaults' set a newly created control.
		related method: storeCustomDefaults.
		"""

		if self.rootGuide.node.hasAttr("moduleDefaults"):
			defaultAttrs = json.loads(self.rootGuide.node.moduleDefaults.get())
			for nodeKey in defaultAttrs:
				ctrlNode = mnsUtils.checkIfObjExistsAndSet(obj= nodeKey)
				if ctrlNode:
					defaultsString = json.dumps(defaultAttrs[nodeKey])
					mnsUtils.addAttrToObj([ctrlNode], type = "string", value = defaultsString, name = "mnsDefaults", locked = True, replace = True)

	def constructAttrHostCtrl(self):
		#attr Host
		status, doAttributeHostCtrl = mnsUtils.validateAttrAndGet(self.rootGuide, "doAttributeHostCtrl", False)
		if doAttributeHostCtrl:
			for cg in self.cGuideControls:
				if "AttrHost_" in cg.name:
					modScale = blkUtils.getModuleScale(self)
					status, attributeHostControlShape = mnsUtils.validateAttrAndGet(self.rootGuide, "attributeHostControlShape", "plus")
					self.attrHostCtrl = blkCtrlShps.ctrlCreate(nameReference = self.rootGuide,
															bodySuffix = "AttrHost",
															parentNode = self.animGrp, 
															controlShape = attributeHostControlShape,
															scale = modScale * 0.5, 
															color = blkUtils.getCtrlCol(self.rootGuide, self.rigTop),
															matchPosition = cg.node, 
															createSpaceSwitchGroup = False,
															doMirror = False,
															createOffsetGrp = True,
															isFacial = self.isFacial)
					break

	def createExtraChannels(self):
		if self.extraChannelsHost:
			status, extraChannels = mnsUtils.validateAttrAndGet(self.rootGuide, "extraChannels", "")
			if extraChannels:
				extraChannels = json.loads(extraChannels)
				createdAttrNames = []
				
				minMaxDef = {}
				for channelDef in extraChannels:
					if not channelDef["isDiv"] == "True":
						minVal, maxVal = 0.0, 0.0
						if channelDef["attrName"] in minMaxDef.keys():
							minVal, maxVal = minMaxDef[channelDef["attrName"]][0], minMaxDef[channelDef["attrName"]][1]
						if channelDef["dir"] == "Pos": maxVal = 1.0
						else: minVal = -1.0
						minMaxDef.update({channelDef["attrName"]: [minVal, maxVal]})

				for channelDef in extraChannels:
					if channelDef["isDiv"] == "True":
						mnsUtils.addAttrToObj([self.extraChannelsHost.node], type = "enum", value = ["______"], name = channelDef["attrName"], replace = False, locked = True)
					else:
						status, attr = mnsUtils.validateAttrAndGet(self.extraChannelsHost, channelDef["attrName"], "", returnAttrObject = True)
						if not status:
							attr = mnsUtils.addAttrToObj([self.extraChannelsHost.node], type = "float", min = minMaxDef[channelDef["attrName"]][0], max = minMaxDef[channelDef["attrName"]][1], value = 0.0, name = channelDef["attrName"], replace = True)[0]
							mdlNode = mnsNodes.mdlNode(attr, -1.0, None)

							clampNode = mnsNodes.clampNode([attr, mdlNode.node.output, 0], 
														[1.0, 1.0, 1.0],
														[0.0, 0.0, 0.0],
														[None, None, None])
							blkUtils.connectSlaveToDeleteMaster(mdlNode, self.extraChannelsHost)
							blkUtils.connectSlaveToDeleteMaster(clampNode, self.extraChannelsHost)
						
						try:
							clampNode = None 

							outConnections = attr.listConnections(s = False, d = True)
							if outConnections:
								for oc in outConnections:
									if type(oc) == pm.nodetypes.Clamp:
										clampNode = oc
										break

							if clampNode:
								if channelDef["dir"] == "Pos":
									clampNode.outputR >> channelDef["attrTarget"]
								else:
									clampNode.outputG >> channelDef["attrTarget"]
						except: 
							mnsLog.log("Could not connect attribute \"" + channelDef["attrTarget"] + "\", please check your extra channels settings.", svr = 2)

	def createIsolatedInterpJointsControls(self):
		status, interpJointsIsoCtrls = mnsUtils.validateAttrAndGet(self.rootGuide, "interpJointsIsolatedCtrls", False)
		if interpJointsIsoCtrls:
			interpJoints = blkUtils.getModuleDecendentsWildcard(self.rootGuide, interpJntsOnly = True)
			
			if interpJoints:
				for iJoint in interpJoints:
					inCons = iJoint.node.t.listConnections(d = False, s = True)
					if inCons:
						matCns = inCons[0]
						inCons = matCns.sourceWorldMatrix[0].listConnections(d = False, s = True)
						if inCons:
							masterLoc = inCons[0]
							
							#create all attributes to store previous connections
							origMatCns = mnsUtils.addAttrToObj([iJoint.node], type = "message", value = matCns, name = "origMatCns", replace = True)[0]

							#get more needed data
							status, symmetryType = mnsUtils.validateAttrAndGet(self.rootGuide, "symmetryType", 0)
							status, isFacial = mnsUtils.validateAttrAndGet(self.rootGuide, "isFacial", False)
							status, ctrlShape = mnsUtils.validateAttrAndGet(self.rootGuide, "interpJointsIsolatedControlShape", "circle")
							modScale = blkUtils.getModuleScale(self)

							#all needed data gathered
							#create the in-between controls
							ctrl = blkCtrlShps.ctrlCreate(nameReference = iJoint,
									controlShape = ctrlShape,
									scale = modScale * 0.5, 
									blkCtrlTypeID = 2,
									color = blkUtils.getCtrlCol(self.rootGuide, self.rigTop),
									matchTransform = masterLoc,
									createOffsetGrp = True,
									symmetryType = symmetryType,
									doMirror = True,
									isFacial = isFacial,
									parentNode = self.animStaticGrp
									)
							ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl, type = "offsetGrp")
							self.allControls.append(ctrl)

							#delete connections before making new ones
							for channel in "trs":
								iJoint.node.attr(channel).disconnect()
								for axis in "xyz":
									iJoint.node.attr(channel + axis).disconnect()
								
							#constraint the offset grp to the loc master, then the jnt to the ctrl
							mnsNodes.mnsMatrixConstraintNode(sources = [masterLoc], targets = [ctrlOffset.node], maintainOffset = True)
							mnsNodes.mnsMatrixConstraintNode(sources = [ctrl.node], targets = [iJoint.node], maintainOffset = True)

	def removeIsolatedInterpJointsControls(self):
		status, interpJointsIsoCtrls = mnsUtils.validateAttrAndGet(self.rootGuide, "interpJointsIsolatedCtrls", False)
		if interpJointsIsoCtrls:
			interpJoints = blkUtils.getModuleDecendentsWildcard(self.rootGuide, interpJntsOnly = True)
			
			if interpJoints:
				for iJoint in interpJoints:
					inCons = iJoint.node.t.listConnections(d = False, s = True)
					if inCons:
						#remove current matCns
						matCns = inCons[0]
						iJoint.node.t.disconnect()
						iJoint.node.r.disconnect()
						iJoint.node.s.disconnect()
						iJoint.node.shear.disconnect()
						pm.delete(matCns)
						
						#find original matCns	
						status, origMatCns = mnsUtils.validateAttrAndGet(iJoint, "origMatCns", None)
						if origMatCns:
							#reconnect
							origMatCns.t >> iJoint.node.t
							origMatCns.r >> iJoint.node.r
							origMatCns.s >> iJoint.node.s 
							origMatCns.shear >> iJoint.node.shear 

							#delete attr
							oldAttr = iJoint.node.attr("origMatCns")
							oldAttr.setLocked(False)
							pm.deleteAttr(oldAttr)

	def construct(self):
		"""The main construct method.
		The actual 'Construct' method within the build module directory is being called here.
		Flow:
		- make sure the module isn't built
		- get the puppet root
		- try and find the related 'construct' method within the build module directory (or package).
		- construct the module, feeding the construct method with all of the requested module settings.
		  this will transfer the related joints to their new ctrl authority.
		- connect a vis channel to the new module group created.
		- re-collect relations for the module (post build).
		- Set colors for all built controls.
		- parent the new bm top group in the puppet group.
		- try restore defaults if there are any.
		"""

		if not self.rootGuide.node.constructed.get():
			self.puppetTopCtrl = blkUtils.getPuppetRootFromRigTop(self.rigTop)
			if not self.puppetTopCtrl: self.puppetTopCtrl = self.createPuppetRootCtrl(self.rigTop)
			
			pyModule, methods = blkUtils.getPyModuleFromGuide(self.rootGuide)
			if not pyModule: return None

			if "construct" in methods: 
				# craete module Top
				self.createModuleTopNode()
				self.constructAttrHostCtrl()

				#construct
				self.allControls, self.internalSpaces, self.moduleSpaceAttrHost, self.extraChannelsHost = pyModule.construct(mansur, self)
				if not self.moduleSpaceAttrHost and self.attrHostCtrl: self.moduleSpaceAttrHost = self.attrHostCtrl

				alongSfcCtrl = blkUtils.convertModuleAuthorityToSurface(self)
				if alongSfcCtrl: self.allControls += alongSfcCtrl

				if self.attrHostCtrl: self.allControls.append(self.attrHostCtrl)
				
				self.createIsolatedInterpJointsControls()
				self.splitControlsBasedOnType()
				self.spaceSwitchCtrls.append(self.animGrp)
				self.connectVisChannels()

				blkUtils.setgCtrlColorForModule(self.rigTop, self.rootGuide)
		mnsUtils.setAttr(self.rootGuide.node.constructed, True)
		pm.parent(self.moduleTop.node, blkUtils.getPuppetBaseFromRigTop(self.rigTop).node)

		blkUtils.createAndConnectModuleVisChannelsToPuppetRootCtrl(self.moduleTop)
		self.restoreCustomDefaults()
		self.createExtraChannels()

		pm.flushUndo()

		#return;MnsBuildModule (self, this buildModule class)
		return self

	def filterValidSpacs(self, sourceSpaces = [], **kwargs):
		gatherDefaultSpace = kwargs.get("gatherDefaultSpace", True)

		returnSpaces = []
		if sourceSpaces:
			for eSpace in sourceSpaces:
				if type(eSpace) != MnsNameStd:
					eSpace = mnsUtils.validateNameStd(eSpace)
				
				if eSpace:
					#handleJnts, Ctrls
					if eSpace.suffix == mnsPS_rJnt or eSpace.suffix == mnsPS_jnt or eSpace.suffix == mnsPS_iJnt or eSpace.suffix == mnsPS_ctrl:
						if eSpace.node:
							if eSpace.node not in returnSpaces: 
								spaceTransform =  eSpace.node

								if gatherDefaultSpace:
									if self.defaultSpace and self.defaultSpace == eSpace.node.nodeName(): 
										self.defaultSpace = spaceTransform.nodeName()
								returnSpaces.append(spaceTransform)

					#handleGuides
					if eSpace.suffix == mnsPS_gRootCtrl or eSpace.suffix == mnsPS_gCtrl or  eSpace.suffix == mnsPS_cgCtrl:
						status, ctrlAuthority = mnsUtils.validateAttrAndGet(eSpace, "ctrlAuthority", None)
						if ctrlAuthority:
							if ctrlAuthority not in returnSpaces: 
								spaceTransform =  ctrlAuthority
								if gatherDefaultSpace:
									if self.defaultSpace and self.defaultSpace == eSpace.node.nodeName(): 
										self.defaultSpace = spaceTransform.nodeName()
								returnSpaces.append(spaceTransform)
								
		return returnSpaces

	def constructAttrHostSpace(self):
		if self.attrHostCtrl:
			status, attrHostSpace = mnsUtils.validateAttrAndGet(self.rootGuide, "attrHostSpace", None)
			attrHostSpace = mnsUtils.validateNameStd(attrHostSpace)
			if attrHostSpace:
				attrHostSpace = self.filterValidSpacs([attrHostSpace], gatherDefaultSpace = False)
				if attrHostSpace:
					attrHostSpace = attrHostSpace[0]
					ssGrp = mnsUtils.createOffsetGroup(self.attrHostCtrl, type = "spaceSwitchGrp")
					
					#build cns
					matConNode = mnsNodes.mnsMatrixConstraintNode(sources = [attrHostSpace], targets = [ssGrp.node], maintainOffset = True)
					matConNode["nameStds"][0].node.spaceSet.set(0)

	def constructSpaces(self):
		"""This method is the spaces construction processing.
		This method is seperated from the main construct method in order to run it after an entire construction.
		Because the spaces within the module are dependent of other modules, a first loop is run to construct the modules,
		after, another loop is running through the built modules, calling this method, trying to construct all of it's spaces.
		"""

		def setDefaultSpaceForEnum(enumAttr = None, defaultIndex = 0):
			if enumAttr and defaultIndex > 0:
				pm.addAttr(enumAttr, e=1, dv = defaultIndex)
				enumAttr.set(defaultIndex)

		if self.rootGuide.node.constructed.get():
			#GatherSpaces
			spaces = []
			if self.pureParent.node.hasAttr("ctrlAuthority"):
				if mnsUtils.validateNameStd(self.pureParent.node.ctrlAuthority.get()):
					spaces += [self.pureParent.node.ctrlAuthority.get()]

			spaces += self.filterValidSpacs(self.extraSpaces)
			if self.puppetTopCtrl.node not in spaces: spaces.append(self.puppetTopCtrl.node)
			
			#build spaces
			if self.spaceSwitchCtrls:
				for k, trans in enumerate(self.spaceSwitchCtrls):
					#add internal spaces
					localSpaces = []
					if self.internalSpaces:
						if trans.name in self.internalSpaces:
							for iSpace in self.internalSpaces[trans.name]:
								node = mnsUtils.checkIfObjExistsAndSet(iSpace)
								if node:
									localSpaces.append(node)

					###deconstruct Existing Spaces
					pm.delete(blkUtils.getExistingSpaceConstraintForControl(trans))
					try: pm.deleteAttr(trans.node.attr("space"))
					except:
						try: 
							pm.deleteAttr(trans.node.attr("translateSpace"))
							pm.deleteAttr(trans.node.attr("orientSpace"))
						except: pass

					ssGrp = blkUtils.getOffsetGrpForCtrl(trans, type = "spaceSwitchGrp")
					spaceValues = []
					defaultSpaceIndex = 0
					for j, s in enumerate((localSpaces + spaces)):
						spaceName = s.nodeName()
						if j == 0: 
							spaceName = "*" + spaceName
							if not self.defaultSpace: spaceName = "[D] " + spaceName
						elif self.defaultSpace and self.defaultSpace == spaceName: 
							spaceName = "[D] " + spaceName
							defaultSpaceIndex = j
						spaceValues.append(spaceName)

					#ctrl vis on playback
					mnsUtils.addAttrToObj([trans.node], type = "enum", value = ["______"], name = "spaceSwitch", replace = True, locked = True)

					tranAttr, rotAttr, attr = None, None, None
					if self.rootGuide.node.splitOrientSpace.get():
						tranMatNode = mnsNodes.mnsMatrixConstraintNode(sources =  (localSpaces + spaces), targets = [ssGrp.node], maintainOffset = True, connectRotate = False)
						rotMatNode = mnsNodes.mnsMatrixConstraintNode(sources = (localSpaces + spaces), targets = [ssGrp.node], maintainOffset = True, connectTranslate = False, connectScale = False)
						tranAttr = mnsUtils.addAttrToObj([trans.node], type = "enum", value = spaceValues, name = "translateSpace", replace = True, locked = False, cb = True, keyable = True)[0]
						rotAttr = mnsUtils.addAttrToObj([trans.node], type = "enum", value = spaceValues, name = "orientSpace", replace = True, locked = False, cb = True, keyable = True)[0]
						if tranMatNode["nameStds"]: tranAttr >> tranMatNode["nameStds"][0].node.spaceSet
						if rotMatNode["nameStds"]: rotAttr >> rotMatNode["nameStds"][0].node.spaceSet
						setDefaultSpaceForEnum(tranAttr, defaultSpaceIndex)
						setDefaultSpaceForEnum(rotAttr, defaultSpaceIndex)
					else:
						matConNode = mnsNodes.mnsMatrixConstraintNode(sources = (localSpaces + spaces), targets = [ssGrp.node], maintainOffset = True)
						attr = mnsUtils.addAttrToObj([trans.node], type = "enum", value = spaceValues, name = "space", replace = True, locked = False, cb = True, keyable = True)[0]
						if matConNode["nameStds"]: attr >> matConNode["nameStds"][0].node.spaceSet
						setDefaultSpaceForEnum(attr, defaultSpaceIndex)
 
					#if index is -1, its the module space anim grp, create a driver if there is a host for it
					if k == (len(self.spaceSwitchCtrls) - 1) and self.moduleSpaceAttrHost and self.moduleSpaceAttrHost.node != trans.node:
						mnsUtils.addAttrToObj([self.moduleSpaceAttrHost.node], type = "enum", value = ["______"], name = "spaceSwitch", replace = True, locked = True)

						if self.rootGuide.node.splitOrientSpace.get() and tranAttr and rotAttr:
							moduleTranAttr = mnsUtils.addAttrToObj([self.moduleSpaceAttrHost.node], type = "enum", value = spaceValues, name = "translateSpace", replace = True, locked = False, cb = True, keyable = True)[0]
							moduleTranAttr >> tranAttr
							moduleRotAttr = mnsUtils.addAttrToObj([self.moduleSpaceAttrHost.node], type = "enum", value = spaceValues, name = "orientSpace", replace = True, locked = False, cb = True, keyable = True)[0]
							moduleRotAttr >> rotAttr
							setDefaultSpaceForEnum(moduleTranAttr, defaultSpaceIndex)
							setDefaultSpaceForEnum(moduleRotAttr, defaultSpaceIndex)
						elif attr:
							moduleAttr = mnsUtils.addAttrToObj([self.moduleSpaceAttrHost.node], type = "enum", value = spaceValues, name = "space", replace = True, locked = False, cb = True, keyable = True)[0]
							moduleAttr >> attr
							setDefaultSpaceForEnum(moduleAttr, defaultSpaceIndex)
			self.constructAttrHostSpace()

	def storeCustomDefaults(self):
		"""This method stores any custom 'defaults' set for the entire module.
		The collection is stored within the rootGuide node.
		This is important beacuse when the module is deconstructed, the ctrls containing the 'defaults' attribute are eventually deleted.
		So, in order to keep the information on deletion, this method runs thorugh the modules controls, 
		and storing the set 'defaults' attribute within the rootGuide, in order to restore them when a reconstruction is called.
		related method: restoreCustomDefaults
		""" 

		defaultAttrs = blkUtils.gatherModuleCustomDefaults(self.moduleTop)
		if defaultAttrs:
			defaultsString = json.dumps(defaultAttrs)
			mnsUtils.addAttrToObj([self.rootGuide.node], type = "string", value = defaultsString, name = "moduleDefaults", locked = True, replace = True)
		elif self.rootGuide.node.hasAttr("moduleDefaults"):
			self.rootGuide.node.moduleDefaults.setLocked(False)
			pm.deleteAttr(self.rootGuide.node, attribute = "moduleDefaults")

	def deconstruct(self, mnsRig):
		"""This is the main module deconstruction method.
		Flow:
			- Make sure the module is constructed
			- In case a deconstruvt method (non mandatory method) is found within the build-module's directory, run it.
			- Transfer all joint authoities back to the guides.
			- Remove the related vis channel from puppet root (Needed in case a partial deconstruction was called).
			- Delete the build module.
			- Set the construction state for the build module.
		"""

		if self.rootGuide.node.constructed.get():
			self.storeCustomDefaults()
			pyModule, methods = blkUtils.getPyModuleFromGuide(self.rootGuide)
			if not pyModule: return None

			self.removeIsolatedInterpJointsControls()
			
			if "deconstruct" in methods: pyModule.deconstruct(mansur, self)

			if self.allControls:
				blkUtils.resetControls(self.allControls)
				for ctrl in self.allControls:
					if ctrl.node.hasAttr("guideAuthority"):
						if ctrl.node.guideAuthority.get():
							blkUtils.transferAuthorityToGuide(ctrl)

				blkUtils.removeModuleVisAttrFromPuppetTop(self.moduleTop, self.puppetTopCtrl)
				pm.delete(self.moduleTop.node)

				mnsUtils.setAttr(self.rootGuide.node.constructed, False)

				pm.flushUndo()

				#return;MnsBuildModule (self, this buildModule class)
				return self

def updateRigTopStruct(rigTop = None, buildModulesBtns = []):
	if rigTop and buildModulesBtns:
		MnsRigO = MnsRig(execInit = False, buildModulesBtns = buildModulesBtns)
		if MnsRigO: MnsRigO.createSubGrpsForRigTop(MnsRigO.rigTop)

def updateModules(blkWin = None, rigTop = None, buildModulesBtns = [], **kwargs):
	if blkWin and rigTop and buildModulesBtns:
		progressBar = kwargs.get("progressBar", None)
		progBarStartValue = kwargs.get("progBarStartValue", 0.0)
		progBarChunk = kwargs.get("progBarChunk", 40.0)

		MnsRigO = MnsRig(rigTop = rigTop, execInit = False, buildModulesBtns = buildModulesBtns)

		updatedModules = []
		for k, buildModuleKey in enumerate(MnsRigO.modules.keys()):
			bm = MnsRigO.modules[buildModuleKey]
			rootGuide = bm.rootGuide

			optArgsFromFile, split = blkWin.getModuleSettings(rootGuide, includeCreationOnly = True)
			optArgs = mnsArgs.formatArgumetsAsDict(optArgsFromFile)

			for argKey in optArgs: 
				locked, keyable, cb = True, False, False
				attrType = type(optArgs[argKey])
				if attrType != pm.nodetypes.Transform:
					if not rootGuide.node.hasAttr(argKey):
						mnsUtils.addAttrToObj(rootGuide.node, name = argKey , type = attrType, value = optArgs[argKey], locked = locked, cb = cb, keyable = keyable)
						if not buildModuleKey in updatedModules: updatedModules.append(buildModuleKey)

			if progressBar: 
				progBarValue = progBarStartValue + (progBarChunk / len(MnsRigO.modules.keys()) * float(k + 1))
				progressBar.setValue(progBarValue)

		mnsLog.log("Finished updating guides. Total updated modules- " + str(len(updatedModules)), svr = 1)

def updateRigTopAttrs(rigTop = None):
	if rigTop:
		settingsPath = os.path.join(dirname(dirname(abspath(__file__))), "core/charInitSettings.charSet").replace("\\", "/")
		optArgsFromFile, sidePlaceHolder = blkUtils.getSettings(settingsPath, rigTop, mnsPS_rigTop)
		if optArgsFromFile:
			optArgs = mnsArgs.formatArgumetsAsDict(optArgsFromFile)
			locked, keyable, cb = True, False, False

			for argKey in optArgs:
				attrType = type(optArgs[argKey])
				if attrType != pm.nodetypes.Transform:
					mnsUtils.addAttrToObj(rigTop.node, name = argKey , type = attrType, value = optArgs[argKey], locked = locked, cb = cb, keyable = keyable)

def update2026DLNodes():
	if GLOB_mayaVersion > 2025:
		try:
			allMdlNodes = pm.ls("*", type = pm.nodetypes.multDL)
			allAdlNodes = pm.ls("*", type = pm.nodetypes.addDL)

			for oldDlNode in (allMdlNodes + allAdlNodes):
				#replace all nodes with new DL nodes
				input1Attr = oldDlNode.input1.listConnections(d = False, s = True, p = True)
				input2Attr = oldDlNode.input2.listConnections(d = False, s = True, p = True)
				outputAttr = oldDlNode.output.listConnections(s = False, d = True, p = True)
				if input1Attr: 
					input1Attr = input1Attr[0]
				else:
					input1Attr = oldDlNode.input1.get()

				if input2Attr: 
					input2Attr = input2Attr[0]
				else:
					input2Attr = oldDlNode.input2.get()

				if outputAttr: outputAttr = outputAttr[0]

				if type(oldDlNode) is pm.nodetypes.addDL:
					adlNode = mnsNodes.adlNode(input1Attr, input2Attr, outputAttr)
					nameDup = oldDlNode.nodeName()
					oldDlNode.rename(oldDlNode.nodeName() + "_tempRename")
					adlNode.node.rename(nameDup)
				else:
					mdlNode = mnsNodes.mdlNode(input1Attr, input2Attr, outputAttr)
					nameDup = oldDlNode.nodeName()
					oldDlNode.rename(oldDlNode.nodeName() + "_tempRename")
					mdlNode.node.rename(nameDup)

				oldDlNode.input1.disconnect()
				oldDlNode.input2.disconnect()
				oldDlNode.output.disconnect()

			pm.delete((allMdlNodes + allAdlNodes))
		except:
			pass

def updateRig(blkWin = None, buildModulesBtns = [], **kwargs):
	progressBar = kwargs.get("progressBar", None)
	if progressBar: progressBar.setValue(0)

	rigTop = blkUtils.getRigTopForSel()

	if blkWin and rigTop and buildModulesBtns:
		blkUtils.attemptModulePathFixFroRigTop(rigTop, buildModulesBtns, 
												progressBar = progressBar,
												progBarStartValue = 0.0,
												progBarChunk = 5.0)
		updateModules(blkWin, rigTop, buildModulesBtns, 
										progressBar = progressBar,
										progBarStartValue = 5.0,
										progBarChunk = 55.0)
		updateRigTopStruct(rigTop, buildModulesBtns)
		updateRigTopAttrs(rigTop)
		update2026DLNodes()

		if progressBar: progressBar.setValue(progressBar.value() + 10)

		progBarStartValue = 70.0
		progBarChunk = 30.0

		#temp- unlock all joints transforms
		rootGuide = blkUtils.getRootGuideFromRigTop(rigTop)
		status, rootJoint = mnsUtils.validateAttrAndGet(rootGuide, "jntSlave", None)
		if rootJoint:
			allJoints = [rootJoint] + rootJoint.listRelatives(ad = True, type = "joint")
			for idx,j in enumerate(allJoints):
				mnsUtils.lockAndHideAllTransforms(j, lock = True, cb = True, keyable = True)
				if progressBar: 
					progBarValue = progBarStartValue + (progBarChunk / len(allJoints) * float(idx + 1))
					progressBar.setValue(progBarValue)

		if progressBar: 
			progressBar.setValue(100)		
			progressBar.setValue(0)		
	mnsLog.log("Rig updated successfully.", svr = 1)

def createModuleCompound(compoundMaster, moduleName, bmButtonList, parent, settings):
	if bmButtonList and moduleName in bmButtonList.keys():
		MnsBuildModuleButton = bmButtonList[moduleName]
		newMod = MnsBuildModule(MnsBuildModuleButton, newModule = False)
		newMod.buildGuides(MnsBuildModuleButton, skipUI = True, parentGuide = parent, preDefinedSettings = settings)
		mnsUtils.addAttrToObj([newMod.rootGuide.node], type = "message", value = compoundMaster.node, name = "compoundMaster", replace = True)

		return newMod