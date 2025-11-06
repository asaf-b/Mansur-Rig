"""=== Author: Assaf Ben Zur ===
MANSUR - BLOCK
Main BLOCK UI.

This is the main UI for rig building (BLOCK). This is the essence of the entire library.
This tool gathers all user actions, and defines triggers for edditing rigs.
The main goal of this UI is to collect the available build-modules and draw creation buttons for them.
The core module library is defined as the block library, but additionals paths can be inserted into the collect loop.

Many UI triggers are available in this UI, but many are kept external to the UI class, to keep things as clean and independent as possible.
Most core functionalitites belong to the rig classes in 'buildModules'.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

import os, json, ctypes, math, inspect, imp
from os.path import dirname, abspath
from functools import partial
import maya.OpenMaya as OpenMaya

#mns dependencies
from ..core import log as mnsLog
from ..core.prefixSuffix import *
from ..globalUtils import dynUI as mnsDynUI
from ..core import arguments as mnsArgs
from ..core import nodes as mnsNodes
from ..core import utility as mnsUtils
from ..core import UIUtils as mnsUIUtils
from ..core import string as mnsString
from ..core import meshUtility as mnsMeshUtils
from ..core import skinUtility as mnsSkinUtils
from ..preferences import preferences as mnsPrefs
from ..gui import gui as mnsGui

from ..core.UIUtils import CollapsibleFrameWidget
from .picker2 import picker2 as mnsPicker
from .picker2 import plgSettings as mnsPlgSettings
from .characterDefenition import characterDefenitionUI as mnsCharDef
from .core import buildModules as mnsBuildModules
from .core import controlShapes as blkCtrlShps
from .core import blockUtility as blkUtils
from ..core.globals import *

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

mansur = __import__(__name__.split('.')[0])

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "blockBuildUI.ui")
class MnsBlockBuildUI(form_class, base_class):
	"""BLOCK UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsBlockBuildUI, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName( 'mnsBLOCK_UI' )
		mnsLog.log("mnsBLOCK_UI Class Initialize.")
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)

		#locals
		self.collapsibleWidgetPairing = []
		self.setCollapsibleWidgetPairing()

		self.tabIndex = 1
		self.buildModulesBtns = {}
		self.sidePlaceHolder = None
		self.bmLib = {}
		self.deformationTabLoadPairing = {self.loadMeshes_btn: self.skinMeshes_lst, self.loadMeshesSources_btn: self.sourceMshes_lst, self.loadMeshesTargets_btn: self.targetMeshes_lst}
		self.meshWidgetDict = {self.skinMeshes_lst: [], self.sourceMshes_lst: [], self.targetMeshes_lst: []}
		self.bmToolTips = {}
		self.tabButtons = []

		#run init methods
		self.installEventFilter(self)
		self.mayaSelectCallBack = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.refreshSelectionState)

		self.defineBuildParentModules()
		self.initView()
		mnsGui.setGuiStyle(self, "BLOCK Builder")
		
		self.initializePrefDirs()
		self.initializeAdditionalModulePaths()
		self.initializeAdditionalModulePresetsPaths()
		
		self.connectSignals()
		self.initializeGuidePresetCb()
		self.echoLog("UI initialized.", 1)

	def resizeEvent(self, QResizeEvent):
		mnsGui.windowResizeEvent(self, QResizeEvent)
			
	def closeEvent(self, QCloseEvent):
		mnsGui.windowCloseEvent(self, QCloseEvent)

	def setCollapsibleWidgetPairing(self):
		self.collapsibleWidgetPairing = [
			{
				"lo": self.blockMainHolder_lo,
				"title": "Edit Guides",
				"widget": self.editGuides_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockMainHolder_lo,
				"title": "Orient Guides",
				"widget": self.orientGuides_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockMainHolder_lo,
				"title": "Guide Posing",
				"widget": self.posing_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockMainHolder_lo,
				"title": "Control Shapes",
				"widget": self.controlShapes_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockMainHolder_lo,
				"title": "Controls Default Values",
				"widget": self.defaults_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockUtilsHolder_lo,
				"title": "Build Modules Paths",
				"widget": self.buildModulesPaths_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockUtilsHolder_lo,
				"title": "Module Presets Paths",
				"widget": self.modulePresetsPaths_gpx,
				"isExpanded": False
			},
			{
				"lo": self.blockPickerHolder_lo,
				"title": "Tools",
				"widget": self.pickerTools_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockPickerHolder_lo,
				"title": "Align",
				"widget": self.pickerAlign_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockPickerHolder_lo,
				"title": "Import / Export",
				"widget": self.pickerEI_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockDeformationHolder_lo,
				"title": "Skinning Joints",
				"widget": self.skinningJoints_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockDeformationHolder_lo,
				"title": "Skinning",
				"widget": self.skinning_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockDeformationHolder_lo,
				"title": "Mirror Skin To Detached Component",
				"widget": self.mirrorSkinToDetached_gbx,
				"isExpanded": False
			},
			{
				"lo": self.blockMocapHolder_lo,
				"title": "Import Preset",
				"widget": self.importPreset_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockMocapHolder_lo,
				"title": "Offset Rig",
				"widget": self.offsetRig_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockMocapHolder_lo,
				"title": "Utility",
				"widget": self.mocapUtils_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockMocapHolder_lo,
				"title": "Character Definition",
				"widget": self.charDef_gbx,
				"isExpanded": True
			},
			{
				"lo": self.blockMocapHolder_lo,
				"title": "Extract Skeleton",
				"widget": self.extractSkel_gbx,
				"isExpanded": False
			}
			]

	def initView(self):
		"""Initialize view:
		- Set icons
		- Set logger view
		- Set tab index to 1
		- Set-Up CollapsibleWidget view
		"""

		mnsUIUtils.applyCollapsibleWidgetsForPairing(self.collapsibleWidgetPairing)
		
		for layoutHolder in [self.blockMainHolder_lo,
							self.blockPickerHolder_lo,
							self.blockDeformationHolder_lo,
							self.blockMocapHolder_lo,
							self.blockUtilsHolder_lo]:
			spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			layoutHolder.addItem(spacer)

		self.tabWidget.setCurrentIndex(0)
		self.bakeConMethod_cb.setCurrentIndex(1)
		self.resize(700, 830)

		#icons
		self.logoHeader_lbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/block_t5.png"))

		#self.modSetBtn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/moduleSettings.png"))
		self.rigInfo_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/info.png"))
		self.updateRig_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/CN_refresh.png"))

		self.guideJointToggle_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/joint.svg"))
		self.ctrlGuideToggle_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/projectCurve_Poly.png"))
		self.dupModule.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/paste.png"))
		self.dupModuleOnly_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/duplicateReference.png"))
		self.symModule_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/symmetrize.png"))
		self.symmetrizeControlShapes_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/symmetrize.png"))
		self.reposition_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/alignCurve.png"))
		self.copyShape_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/out_alignCurve.png"))
		self.exportCS_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.importCS_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.addGuidesAbove_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addProxy.png"))
		self.addGuidesBelow_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addProxy.png"))
		self.removeSelectedGuides_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeReference.png"))
		self.extractShapes_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nurbsCurve.svg"))
		self.removeCustomShapes_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeRenderable.png"))
		self.defaultsDelete_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeRenderable.png"))
		self.setDefaults_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.loadDefaults_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		
		self.modulePromote_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/promote.png"))
		self.rebuildJointStruct_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/rebuild.png"))
		
		self.poseSave_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.poseLoad_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.poseDelete_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeRenderable.png"))
		self.symCgShape_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/polySymmetrizeUV.png"))

		self.editPlg_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/pickerSettings.png"))
		self.projectPlgs_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/projectCurve.png"))
		self.projCam_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/Camera.png"))
		self.createPLG_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addProxy.png"))
		self.ducplicatePLG_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/paste.png"))
		self.symPickerGuide_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/symmetrize.png"))
		self.mirrorPickerGuides_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/mirrorSkinWeight.png"))
		self.loadPickerBtn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/pickerIcon.png"))
		self.pickerLayBtn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/edit.png"))
		self.toggleGuides_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/square.png"))
		self.bodyFacialTgl_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/general/bodyFace.png"))

		self.matchScale_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/scale_M.png"))
		self.matchTranslate_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/move_M.png"))
		self.exportPickerData_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.importPickerData_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))

		#set align icons
		self.plgAlignHCenter.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignHCenter.png"))
		self.plgAlignHCenter.setIconSize(QtCore.QSize(26,26))
		self.plgAlignVCenter.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignVCenter.png"))
		self.plgAlignVCenter.setIconSize(QtCore.QSize(26,26))
		self.plgAlignLeftBb.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignBBLeft.png"))
		self.plgAlignLeftBb.setIconSize(QtCore.QSize(26,26))
		self.plgAlignRightBb.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignBBRight.png"))
		self.plgAlignRightBb.setIconSize(QtCore.QSize(26,26))
		self.plgAlignTopBb.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignBBTop.png"))
		self.plgAlignTopBb.setIconSize(QtCore.QSize(26,26))
		self.plgAlignBottomBb.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignBBBottom.png"))
		self.plgAlignBottomBb.setIconSize(QtCore.QSize(26,26))
		self.plgAlignLeftPos.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignPosLeft.png"))
		self.plgAlignLeftPos.setIconSize(QtCore.QSize(26,26))
		self.plgAlignRightPos.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignPosRight.png"))
		self.plgAlignRightPos.setIconSize(QtCore.QSize(26,26))
		self.plgAlignTopPos.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignPosTop.png"))
		self.plgAlignTopPos.setIconSize(QtCore.QSize(26,26))
		self.plgAlignBottomPos.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/alignment/alignPosBottom.png"))
		self.plgAlignBottomPos.setIconSize(QtCore.QSize(26,26))

		## Mocap Tab Icons ##
		self.createOffsetRig_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/HIKcreateControlRig.png"))
		self.deleteOffsetRig_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeRenderable.png"))
		self.transferAuthToOffsetSkel_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/HIKCharacterToolSkeleton.png"))
		self.transferAuthToPuppet_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/alignCurve.svg"))
		self.resetPuppet_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/menuIconReset.png"))
		self.resetOffsetRig_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/menuIconReset.png"))
		self.charDefUi_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/hotkeySetSettings.png"))
		self.bakeControls_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/bakeAnimation.png"))
		self.extractSkel_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/kinJoint.png"))
		self.selectSlaveControls_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/IsolateSelected.png"))
		self.jointRotateToOrient_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/orientJoint.png"))
		self.matchExtractedSkelToBase_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nClothMatchingMesh.png"))
		self.saveExtractedSkelPose_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.loadExtractedSkelPose_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.deleteExtractedSkelPose_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/removeRenderable.png"))

		#deformation tab icons
		self.importSkin_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.exportSkin_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.copySkin_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/skinWeightCopy.png"))
		self.unBindSkin_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/detachSkin.png"))
		self.rebindSkin_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/smoothSkin.png"))
		self.mirrorSkinToDetached_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/mirrorSkinWeight.png"))

	#####GLOBALS################
	def connectSignals(self):
		"""Connect all UI signals.
		"""

		## construct ##
		self.constructRig_btn.released.connect(self.constructRigInit)
		self.deconstructRig_btn.released.connect(self.deconstructRigInit)
		
		## Build modules paths ##
		self.resetModulePaths_btn.released.connect(self.initializeAdditionalModulePaths)
		self.addModulePath_btn.released.connect(self.addModulePath)
		self.removeModulePath_btn.released.connect(self.removeModelPath)
		self.applyModulePathChange_btn.released.connect(self.applyModulePathsChange)

		## module presets paths ##
		self.resetModulePresetPaths_btn.released.connect(self.initializeAdditionalModulePresetsPaths)
		self.addModulePresetPath_btn.released.connect(self.addModulePresetPath)
		self.removeModulePresetPath_btn.released.connect(self.removeModulePresetPath)
		self.applyModulePresetPathChange_btn.released.connect(self.applyModulePresetPathsChange)

		## build Tab ##
		self.modSetBtn.released.connect(self.loadModuleSettings)
		self.modulePromote_btn.released.connect(self.promoteModule)
		self.guideJointToggle_btn.released.connect(blkUtils.toggleGuideJoint)
		self.ctrlGuideToggle_btn.released.connect(blkUtils.toggleGuideCtrl)
		self.rebuildJointStruct_btn.released.connect(lambda: blkUtils.rebuildJointStructure(self.getConstructMode()))
		self.rigInfo_btn.released.connect(blkUtils.loadRigInfo)
		
		## orient guide ##
		self.orientGuide_btn.released.connect(self.orientGuides)

		## guides Tab ##
		self.dupModule.released.connect(self.duplicateModule)
		self.dupModuleOnly_btn.released.connect(lambda: self.duplicateModule(skipChildrenModules = True))
		self.extractShapes_btn.released.connect(self.extractControlShapes)
		self.symmetrizeControlShapes_btn.released.connect(self.symmetrizeControlShapes)
		self.copyShape_btn.released.connect(lambda: blkUtils.copyShape(reposition = self.reposition_cbx.isChecked()))
		self.reposition_btn.released.connect(blkUtils.repositionShape)
		self.exportCS_btn.released.connect(lambda: blkUtils.exportCtrlShapes(self.getConstructMode()))
		self.importCS_btn.released.connect(blkUtils.importCtrlShapes)
		
		self.symModule_btn.released.connect(self.symmetrizeModule)
		self.removeCustomShapes_btn.released.connect(self.removeCustomShapes)
		self.addGuidesAbove_btn.released.connect(lambda: blkUtils.insertGuides(self.addGuidesAbove_sb.value(), "above"))
		self.addGuidesBelow_btn.released.connect(lambda: blkUtils.insertGuides(self.addGuidesBelow_sb.value(), "below"))
		self.removeSelectedGuides_btn.released.connect(blkUtils.removeGuides)

		## poseing ##
		self.poseSave_btn.released.connect(lambda: self.poseSaveLoadTrigger(0))
		self.poseLoad_btn.released.connect(lambda: self.poseSaveLoadTrigger(1))
		self.poseDelete_btn.released.connect(lambda: self.poseSaveLoadTrigger(2))
		self.symCgShape_btn.released.connect(lambda: blkUtils.symmetrizeCGShape(self.getConstructMode(), int(self.symCgShapeRLDir_rb.isChecked())))

		## defaultsTab tab ##
		self.setDefaults_btn.released.connect(lambda: blkUtils.setRigDefaults(self.getConstructMode(), progressBar = self.constructProg_pb))
		self.loadDefaults_btn.released.connect(lambda: blkUtils.loadRigDefaults(self.getConstructMode(), progressBar = self.constructProg_pb))
		self.defaultsDelete_btn.released.connect(lambda: blkUtils.deleteRigDefaults(self.getConstructMode(), progressBar = self.constructProg_pb))
		
		## picker tab ##
		self.projectPlgs_btn.released.connect(lambda: blkUtils.projectPickerLayout(self.getPickerProjectionMode(), self.mesPrompt_cbx.isChecked()))
		self.pickerLayBtn.released.connect(blkUtils.pickerLayoutAdjust)
		self.projCam_btn.released.connect(self.toggleProjPerpCam)
		self.toggleGuides_btn.released.connect(blkUtils.ctrlPickerGuideToggle)
		self.plgAlignLeftPos.released.connect(lambda: blkUtils.alignPLGuides("left", 0))
		self.plgAlignRightPos.released.connect(lambda: blkUtils.alignPLGuides("right", 0))
		self.plgAlignTopPos.released.connect(lambda: blkUtils.alignPLGuides("top", 0))
		self.plgAlignBottomPos.released.connect(lambda: blkUtils.alignPLGuides("bottom", 0))
		self.plgAlignHCenter.released.connect(lambda: blkUtils.alignPLGuides("h", 0))
		self.plgAlignVCenter.released.connect(lambda: blkUtils.alignPLGuides("v", 0))
		self.plgAlignRightBb.released.connect(lambda: blkUtils.alignPLGuides("right", 1))
		self.plgAlignLeftBb.released.connect(lambda: blkUtils.alignPLGuides("left", 1))
		self.plgAlignTopBb.released.connect(lambda: blkUtils.alignPLGuides("top", 1))
		self.plgAlignBottomBb.released.connect(lambda: blkUtils.alignPLGuides("bottom", 1))
		self.mirrorPickerGuides_btn.released.connect(lambda: blkUtils.alignPLGuides("mir", 2))
		self.symPickerGuide_btn.released.connect(blkUtils.symmetrizePlgs)
		self.loadPickerBtn.released.connect(mnsPicker.loadPicker)
		self.editPlg_btn.released.connect(mnsPlgSettings.loadPlgSettings)
		self.createPLG_btn.released.connect(lambda: blkUtils.createPickerLayoutGuide(None, False, blkUtils.getRigTopForSel(), dontProject = True))
		self.ducplicatePLG_btn.released.connect(blkUtils.duplicatePlgs)
		self.bodyFacialTgl_btn.released.connect(blkUtils.togglePickerCtrlBodyFacial)
		self.matchTranslate_btn.released.connect(self.plgMatch)
		self.matchScale_btn.released.connect(self.plgMatch)
		self.exportPickerData_btn.released.connect(lambda: blkUtils.exportPickerData(mode = self.getPickerExportMode()))
		self.importPickerData_btn.released.connect(blkUtils.importPickerData)

		## Mocap Tab ##
		self.createOffsetRig_btn.released.connect(blkUtils.createOffsetSkeleton)
		self.deleteOffsetRig_btn.released.connect(blkUtils.deleteOffsetSekeleton)
		self.transferAuthToOffsetSkel_btn.released.connect(blkUtils.transferAuthorityToOffsetSkeleton)
		self.transferAuthToPuppet_btn.released.connect(blkUtils.transferAuthorityToPuppet)
		self.resetPuppet_btn.released.connect(blkUtils.resetAllControlForRigTop)
		self.resetOffsetRig_btn.released.connect(blkUtils.resetOffsetSkeleton)
		self.importPreset_btn.released.connect(lambda: blkUtils.importGuidePreset(self.guidePresets_cb.currentText()))
		self.charDefUi_btn.released.connect(mnsCharDef.loadCharacterDefenitionUI)
		self.selectSlaveControls_btn.released.connect(blkUtils.selectSlaveControls)
		self.bakeControls_btn.released.connect(blkUtils.bakeSlaveControls)
		self.extractSkel_btn.released.connect(lambda: blkUtils.extractSkeleton(None, mode = self.skeletonExtractMode_cb.currentIndex(), bakeAnim = self.bakeAnim_cbx.isChecked(), deleteInterpJoints = self.delInterpJoints_cbx.isChecked(), preserveNameSpace = self.preserveNameSpace_cbx.isChecked(), transferSkin = self.transferSkin_cbx.isChecked(), bakeConnectionMethod = self.bakeConMethod_cb.currentIndex()))
		self.jointRotateToOrient_btn.released.connect(blkUtils.jointRotateToOrientTrigger)
		self.matchExtractedSkelToBase_btn.released.connect(blkUtils.matchExtractedSkeletonToBaseSkeleton)
		self.saveExtractedSkelPose_btn.released.connect(lambda: blkUtils.saveLoadDagPose(mode = 0, poseName = self.extractedSkelPose_cb.currentText()))
		self.loadExtractedSkelPose_btn.released.connect(lambda: blkUtils.saveLoadDagPose(mode = 1, poseName = self.extractedSkelPose_cb.currentText()))
		self.deleteExtractedSkelPose_btn.released.connect(lambda: blkUtils.saveLoadDagPose(mode = 2, poseName = self.extractedSkelPose_cb.currentText()))
		
		## Utility Tab ##
		self.newRigTop.released.connect(self.newRigTopTrig)
		self.updateRig_btn.released.connect(lambda: mnsBuildModules.updateRig(self, self.buildModulesBtns, progressBar = self.constructProg_pb))
		self.findNamingIssues_btn.released.connect(blkUtils.findNamingIssuesInHierarchy)

		## log ##
		self.echoClear_btn.released.connect(self.clearEcho)

		## Deformation Tab ##
		self.selectSkinningJoints_btn.released.connect(lambda: pm.select(mnsSkinUtils.getSkinningJointsFromSelection(self.skinJntsModule_rb.isChecked() + 1), r = True))
		self.selectMainJoints_btn.released.connect(lambda: pm.select(mnsSkinUtils.getSkinningJointsFromSelection(self.skinJntsModule_rb.isChecked() + 1, mainJointsOnly = True), r = True))

		for loadBtn in self.deformationTabLoadPairing.keys(): 
			loadBtn.released.connect(self.loadMeshes)

			listWG = self.deformationTabLoadPairing[loadBtn]
			listWG.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			listWG.customContextMenuRequested.connect(self.meshListWidgetMenu)
			listWG.itemSelectionChanged.connect(self.sceneSelectFromWidgets)
		self.exportSkin_btn.released.connect(lambda: mnsSkinUtils.exportSkin(self.getCurrentMeshes(returnAsObjects = True) or pm.ls(sl=True)))
		self.importSkin_btn.released.connect(mnsSkinUtils.importSkin)
		self.copySkin_btn.released.connect(self.copySkin)
		self.unBindSkin_btn.released.connect(lambda: mnsSkinUtils.unbind(self.getCurrentMeshes(returnAsObjects = True) or pm.ls(sl=True)))
		self.rebindSkin_btn.released.connect(lambda: mnsSkinUtils.rebind(self.getCurrentMeshes(returnAsObjects = True) or pm.ls(sl=True)))
		self.mirrorToDetachedSourceLoad_btn.released.connect(lambda: self.loadSelectionToLineEdit(self.mirrorToDetachedSource_le))
		self.mirrorToDetachedTargetLoad_btn.released.connect(lambda: self.loadSelectionToLineEdit(self.mirrorToDetachedTarget_le))
		self.mirrorSkinToDetached_btn.released.connect(lambda: mnsSkinUtils.mirrorSkinToDetachedComponent(self.mirrorToDetachedSource_le.text(), self.mirrorToDetachedTarget_le.text()))

	def eventFilter(self, source, event):
		"""Override event filter to catch the tear off to override it's event.
		"""

		if event.type() == QtCore.QEvent.Close:
			try: OpenMaya.MMessage.removeCallback(self.mayaSelectCallBack)
			except: pass
		return super(QtWidgets.QWidget, self).eventFilter(source, event)

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("Loading BLOCK Window")
		self.show()

	def resizeWindowBasedOnLog(self):
		if self.logColWidget._is_collasped:
			self.resize(650, 860)
		else:
			self.resize(650, 950)

	def initializePrefDirs(self):
		prefsDir = mnsUtils.locatePreferencesDirectory()
		if prefsDir:
			additionalPathsFile = prefsDir + "/" + GLOB_additionalModulePathsJsonName + ".json"
			if not os.path.isfile(additionalPathsFile): mnsUtils.writeJson(mnsUtils.locatePreferencesDirectory(), GLOB_additionalModulePathsJsonName, {})

			additionalPresetPathsFile = prefsDir + "/" + GLOB_additionalModulePresetsPathsJsonName + ".json"
			if not os.path.isfile(additionalPresetPathsFile): mnsUtils.writeJson(mnsUtils.locatePreferencesDirectory(), GLOB_additionalModulePresetsPathsJsonName, {})

	def initializeAdditionalModulePaths(self, **kwargs):
		"""Initialize any custom build-modules paths that already exist within the data collect json.
		(Read any paths that were added before, on UI draw).
		query flag will return the paths only without drawing the items into the UI.
		"""

		existingPaths = []
		query = kwargs.get("query", False) #arg

		if not query:
			self.modulePaths_trv.clear()

		additionalPathsFile = mnsUtils.locatePreferencesDirectory() + "/" + GLOB_additionalModulePathsJsonName + ".json"
		if os.path.isfile(additionalPathsFile):
			additional = mnsUtils.readJson(additionalPathsFile)
			for add in additional:
				if not query: 
					QtWidgets.QTreeWidgetItem(self.modulePaths_trv, [add])
				existingPaths.append(add)

		#return;list (Existing Paths)
		return existingPaths
	
	def initializeAdditionalModulePresetsPaths(self, **kwargs):
		"""Initialize any custom build-modules paths that already exist within the data collect json.
		(Read any paths that were added before, on UI draw).
		query flag will return the paths only without drawing the items into the UI.
		"""

		existingPaths = []
		query = kwargs.get("query", False) #arg

		if not query:
			self.modulePresetPaths_trv.clear()

		additionalPathsFile = mnsUtils.locatePreferencesDirectory() + "/" + GLOB_additionalModulePresetsPathsJsonName + ".json"
		if os.path.isfile(additionalPathsFile):
			additional = mnsUtils.readJson(additionalPathsFile)
			for add in additional:
				if not query: 
					QtWidgets.QTreeWidgetItem(self.modulePresetPaths_trv, [add])
				existingPaths.append(add)

		#return;list (Existing Paths)
		return existingPaths

	def gatherAdditionalModulePaths(self):
		"""Gather all existing additional custom patns from the UI.
		"""
		#return;list (Paths)
		return [self.modulePaths_trv.topLevelItem(itemIdx).text(0) for itemIdx in range(self.modulePaths_trv.topLevelItemCount())]

	def gatherAdditionalModulePresetPaths(self):
		"""Gather all existing additional custom patns from the UI.
		"""
		#return;list (Paths)
		return [self.modulePresetPaths_trv.topLevelItem(itemIdx).text(0) for itemIdx in range(self.modulePresetPaths_trv.topLevelItemCount())]

	def bmCategoryChangedTrigger(self):
		curWid = self.moduleBtnsWidget.currentWidget()
		children = curWid.findChildren(QtWidgets.QListWidget)
		if children:
			listW = children[0]
			#listW.clearSelection()
		self.moduleBtnsWidget.setCurrentIndex(self.bmCategory_cb.currentIndex())

	def defineBuildParentModules(self):
		"""Define build module tabs, based on the collected valid build-modules directories.
		If the directory in question is a valid directory for build modules:
		for every folder containing modules within it, a new tab will be inserted and named based on it.
		"""
		mnsLog.log("BLOCK - initializing build modules UI", svr = 0)

		self.bmLib = {}
		moduleParentPaths = [dirname(__file__) + "/modules"] #+ self.gatherAdditionalModulePaths()

		for path in moduleParentPaths:
			if GLOB_moduleDirectoryFlag in os.listdir(path):
				for name in os.listdir(path):
					fullPath = path + "/" + name
					if os.path.isdir(fullPath):
						modDir = fullPath.replace("\\", "/")
						listWidget = mnsUIUtils.buildStackedTabForModuleParentDir(name, self.tabIndex, self.moduleBtnsWidget)
						self.bmCategory_cb.addItem(name)
						self.tabIndex += 1
						self.buildModulesDefine(modDir, listWidget)
						listWidget.itemDoubleClicked.connect(self.moduleBuildGuide)
				self.createAllModulesSection()
			else:
				mnsLog.log("The module path specefied - \'" + fullPath + "\' isn't an mns module directory. Skipping.", svr = 2)

		self.bmCategory_cb.currentIndexChanged.connect(self.bmCategoryChangedTrigger)

	def createAllModulesSection(self):
		listWidget = mnsUIUtils.buildStackedTabForModuleParentDir("All", 0, self.moduleBtnsWidget)
		listWidget.itemDoubleClicked.connect(self.moduleBuildGuide)
		
		currentCats = [self.bmCategory_cb.itemText(idx) for idx in range(self.bmCategory_cb.count())]
		self.bmCategory_cb.clear()
		self.bmCategory_cb.addItems(["All"] + currentCats)

		k = 0
		for mod in sorted(self.buildModulesBtns.keys()):
			if self.buildModulesBtns[mod].groupType != "legacy":
				addedItem = QtWidgets.QListWidgetItem(mod, listWidget)
				bm = self.buildModulesBtns[mod]

				boldFont=QtGui.QFont()
				boldFont.setPixelSize(11)
				addedItem.setFont(boldFont)

				iconPath = GLOB_guiIconsDir + "/general/module.png"
				icon = QtGui.QIcon(QtGui.QPixmap(iconPath))
				addedItem.setIcon(icon)
				addedItem.setSizeHint(QtCore.QSize(60,22))

				if mod in self.bmToolTips.keys(): addedItem.setToolTip(self.bmToolTips[mod])

				if (k % 2) != 0: addedItem.setBackground(QtGui.QColor("#393939"))
				if k == 0: addedItem.setSelected(True)
				k += 1
		self.bmCategoryChangedTrigger()

	def getToolTipForModule(self, buildModule):
		formattedTooltip = "Module description wasn't created."
		fullPath = buildModule.path + "/" + buildModule.moduleName + ".py"
		if os.path.isfile(fullPath):
			headerLines = mnsUtils.extractHeaderFromPath(fullPath)

			author = ""
			components = ""
			synopsis = []

			for line in headerLines:
				if "Author: " in line: author = line.split(": ")[-1]
				elif "Best used for: " in line: components = line.split(": ")[-1]
				else:
					synopsis.append(line)

			if author or components or synopsis:
				formattedTooltip = "<html><body><font size = 4><table width = 500>"
				formattedTooltip += "<tr><td><b>Author:</b><td></tr>"
				formattedTooltip += "<tr><td>" + author + "</td></tr>"
				formattedTooltip += "<tr></tr>"
				formattedTooltip += "<tr><td><b>Best For Components:</b><td></tr>"
				formattedTooltip += "<tr><td>" + components + "</tr></td>"
				formattedTooltip += "<tr></tr>"
				formattedTooltip += "<tr><td><b>Synopsis:</b><td></tr>"
				for line in synopsis: formattedTooltip += "<tr><td>" + line + "</tr></td>"
				formattedTooltip += "</table></font></body></html>"
		
		self.bmToolTips[buildModule.moduleName] = formattedTooltip
		return formattedTooltip

	def buildModulesDefine(self, modParentPath, listWidget):
		"""Define all existing build-modules within a built tab's directory.
		This mehthod will run for every valid build-module's directory folder, essentially building the actual build-module button in the UI.
		These will all be stored in the 'buildModulesBtns' attribute of this class.
		"""

		mnsLog.logCurrentFrame()
		modules = [os.path.join(modParentPath, name).replace("\\", "/") for name in os.listdir(modParentPath) if os.path.isdir(os.path.join(modParentPath, name))]
		
		k = 0
		for mod in modules:
			bm = mnsBuildModules.MnsBuildModuleBtn(mod)
			addedItem = QtWidgets.QListWidgetItem(bm.moduleName, listWidget)
			
			boldFont=QtGui.QFont()
			boldFont.setPixelSize(11)
			addedItem.setFont(boldFont)

			iconPath = GLOB_guiIconsDir + "/general/module.png"
			icon = QtGui.QIcon(QtGui.QPixmap(iconPath))
			addedItem.setIcon(icon)
			addedItem.setSizeHint(QtCore.QSize(60,22))
			addedItem.setToolTip(self.getToolTipForModule(bm))

			if (k % 2) != 0: addedItem.setBackground(QtGui.QColor("#393939"))
			self.bmLib.update({bm.moduleName: bm})
			self.buildModulesBtns.update({bm.moduleName: bm})
			if k == 0: addedItem.setSelected(True)
			k += 1
			
	def moduleBuildGuide(self, listWidgetItemName):
		"""Action trigger for any build-module button.
		This trigger action will be connected procedurally within the 'drawModuleButton' method in blockUtility.
		"""

		MnsBuildModuleButton = self.bmLib[listWidgetItemName.text()]
		mnsLog.log(MnsBuildModuleButton.moduleName + " clicked.", svr = 1)
		mnsBuildModules.MnsBuildModule(MnsBuildModuleButton, dynUIIcon = GLOB_guiIconsDir + "/logo/block_t5.png")

	def getCorrespondingModuleButtonForModule(self, rootGuide):
		"""For the given rootGuide object, try to locate its corresponding UI button.
		Look within this class's 'buildModulesBtns' attribute.
		"""
		mnsLog.logCurrentFrame()
		rootGuide = mnsUtils.validateNameStd(rootGuide)
		if rootGuide:
			if rootGuide.node.hasAttr("modType"):
				if rootGuide.node.modType.get() in self.buildModulesBtns:
					#return;MnsBuildModuleBtn
					return self.buildModulesBtns[rootGuide.node.modType.get()]

	def applyModulePathsChange(self):
		"""'Apply' (in build tab, module paths) trigger.
		Write the additional paths entered within the UI in the stor json.
		"""

		existingPaths = self.initializeAdditionalModulePaths(query = True)
		uiPaths = self.gatherAdditionalModulePaths()
		additionalPathsDir =  mnsUtils.locatePreferencesDirectory() + "/" + GLOB_additionalModulePathsJsonName + ".json"

		if existingPaths != uiPaths:
			mnsUtils.writeJson(mnsUtils.locatePreferencesDirectory(), GLOB_additionalModulePathsJsonName, uiPaths)
			pm.confirmDialog( title='Success', message="Module Directories changed successfully.", defaultButton='OK')
			exec ("from mansur.block import blockBuildUI as mnsBlockBuildUI\nfrom mansur.globalUtils import dynUI as mnsDynUI\nreload(mnsBlockBuildUI)\nreload(mnsDynUI)\nimport pymel.core as pm\n\nif pm.window(\"mnsBLOCK_UI\", exists=True):\n\tpm.deleteUI(\"mnsBLOCK_UI\")\n\nmnsBlock = mnsBlockBuildUI.MnsBlockBuildUI()\nmnsBlock.loadWindow()\n\n")

	def applyModulePresetPathsChange(self):
		"""'Apply' (in build tab, module paths) trigger.
		Write the additional paths entered within the UI in the stor json.
		"""

		existingPaths = self.initializeAdditionalModulePresetsPaths(query = True)
		uiPaths = self.gatherAdditionalModulePresetPaths()
		additionalPathsDir =  mnsUtils.locatePreferencesDirectory() + "/" + GLOB_additionalModulePresetsPathsJsonName + ".json"

		if existingPaths != uiPaths:
			mnsUtils.writeJson(mnsUtils.locatePreferencesDirectory(), GLOB_additionalModulePresetsPathsJsonName, uiPaths)
			pm.confirmDialog( title='Success', message="Module Presets Directories changed successfully.", defaultButton='OK')
			exec ("from mansur.block import blockBuildUI as mnsBlockBuildUI\nfrom mansur.globalUtils import dynUI as mnsDynUI\nreload(mnsBlockBuildUI)\nreload(mnsDynUI)\nimport pymel.core as pm\n\nif pm.window(\"mnsBLOCK_UI\", exists=True):\n\tpm.deleteUI(\"mnsBLOCK_UI\")\n\nmnsBlock = mnsBlockBuildUI.MnsBlockBuildUI()\nmnsBlock.loadWindow()\n\n")

	def removeModelPath(self):
		"""Remove a module path line from the 'module paths' tree trigger.
		"""

		if self.modulePaths_trv.currentItem():
			self.modulePaths_trv.currentItem().setSelected(False)
			self.modulePaths_trv.takeTopLevelItem(self.modulePaths_trv.indexOfTopLevelItem(self.modulePaths_trv.currentItem()))

	def removeModulePresetPath(self):
		"""Remove a module path line from the 'module paths' tree trigger.
		"""

		if self.modulePresetPaths_trv.currentItem():
			self.modulePresetPaths_trv.currentItem().setSelected(False)
			self.modulePresetPaths_trv.takeTopLevelItem(self.modulePresetPaths_trv.indexOfTopLevelItem(self.modulePresetPaths_trv.currentItem()))

	def addModulePath(self):
		"""Add a module path line to the 'module paths' tree trigger.
		"""

		directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
		if directory:
			QtWidgets.QTreeWidgetItem(self.modulePaths_trv, [directory])

	def addModulePresetPath(self):
		"""Add a module path line to the 'module paths' tree trigger.
		"""

		directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
		if directory:
			QtWidgets.QTreeWidgetItem(self.modulePresetPaths_trv, [directory])

	def clearEcho(self):
		self.echo_le.clear()
		self.constructProg_pb.setValue(0)
		self.echoIcon_lbl.setStyleSheet("background-color: #25b6d2;")

	def echoLog(self, msg, svr):
		if svr == 1:
			self.echoIcon_lbl.setStyleSheet("background-color: #25b6d2;")
		elif svr == 2:
			self.echoIcon_lbl.setStyleSheet("background-color: #e79e2d;")
		elif svr > 2:
			self.echoIcon_lbl.setStyleSheet("background-color: #e84849;")
		self.echo_le.setText(msg)

	#####GLOBAL TOOLS TAB################
	def newRigTopTrig(self):
		"""Utils->'New RigTop' trigger.
		deselect, then initialize a MnsRig class.
		"""

		pm.select(d=1)
		mnsBuildModules.MnsRig()

	def toggleProjPerpCam(self):
		rigTop = blkUtils.getRigTopForSel()
		if rigTop:
			projCam = blkUtils.getPickerProjectionCamFromRigTop(rigTop = rigTop)

			if pm.modelPanel("modelPanel4", q=1, cam = True) != projCam.node.nodeName():
				blkUtils.loadPickerProjectionCam()
			else:
				blkUtils.loadPerspCam()

	#####DEFORMATION TAB################
	def refreshSelectionState(self, dummy = None):
		try:
			selection = pm.ls(sl=True)
			meshes = [meshTransform for meshTransform in selection if type(meshTransform) == pm.nodetypes.Transform and meshTransform.getShape() and type(meshTransform.getShape()) == pm.nodetypes.Mesh] 

			if meshes:
				for listWidgetKey in self.meshWidgetDict.keys():
					listWidgetKey.blockSignals(True)
					listWidgetKey.clearSelection()
					for mesh in meshes:
						for meshItem in self.meshWidgetDict[listWidgetKey]:
							try:
								if meshItem.text() == mesh.nodeName(): 
									meshItem.setSelected(True)
							except: pass

				for listWidgetKey in self.meshWidgetDict.keys(): listWidgetKey.blockSignals(False)
				return True
		except: pass

	def sceneSelectFromWidgets(self):
		newSelection = []
		for listWidgetKey in self.meshWidgetDict.keys():
			listWidgetKey.blockSignals(True)

			for meshItem in self.meshWidgetDict[listWidgetKey]:
				try:
					if meshItem.isSelected():
						sceneMesh = mnsUtils.checkIfObjExistsAndSet(meshItem.text())
						if sceneMesh not in newSelection: newSelection.append(sceneMesh)
				except: pass

		pm.select(newSelection, replace = True)
		for listWidgetKey in self.meshWidgetDict.keys(): listWidgetKey.blockSignals(False)

	def getListWidgetFromSender(self):
		returnState = None
		senderBtn = self.sender()
		if senderBtn:
			if senderBtn in self.deformationTabLoadPairing.keys():
				lstWidget = self.deformationTabLoadPairing[senderBtn]
				if lstWidget: returnState = lstWidget
		return returnState

	def meshListWidgetMenu(self, position):
		currentLstWidget = self.sender()

		menu = QtWidgets.QMenu()
		addSelectedAction = menu.addAction(self.tr("Add Selected"))
		addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
		addSelectedAction.triggered.connect(lambda: self.addMeshes(currentLstWidget))

		removeSelectedAction = menu.addAction(self.tr("Remove Selected"))  
		removeSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
		removeSelectedAction.triggered.connect(lambda: self.removeMeshes(currentLstWidget))

		loadSelectedAction = menu.addAction(self.tr("Load Selected"))  
		loadSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/reference.png")))
		loadSelectedAction.triggered.connect(lambda: self.loadMeshes(listWidget = currentLstWidget))

		clearAction = menu.addAction(self.tr("Clear"))  
		clearAction.triggered.connect(currentLstWidget.clear)

		menu.exec_(currentLstWidget.viewport().mapToGlobal(position))

	def updateMeshWidgetsDict(self):
		self.meshWidgetDict = {self.skinMeshes_lst: [], self.sourceMshes_lst: [], self.targetMeshes_lst: []}

		for listWidget in self.meshWidgetDict.keys():
			self.meshWidgetDict[listWidget] = [listWidget.item(rowIdx) for rowIdx in range(listWidget.count())]

	def sortMeshLists(self):
		for listWidget in self.meshWidgetDict.keys():
			listWidget.sortItems()

	def loadMeshes(self, **kwargs):
		selection = pm.ls(sl=True)
		if selection:
			meshes = [meshTransform for meshTransform in selection if meshTransform.getShape() and type(meshTransform.getShape()) == pm.nodetypes.Mesh] 

			if meshes:
				lstWidget = kwargs.get("listWidget", self.getListWidgetFromSender())

				if lstWidget:
					lstWidget.clear()
					meshItems = [mesh.nodeName() for mesh in meshes]
					lstWidget.addItems(meshItems)
					self.sortMeshLists()
					self.updateMeshWidgetsDict()

		self.refreshSelectionState()

	def getCurrentMeshes(self, listWidget = None, **kwargs):
		returnAsObjects = kwargs.get("returnAsObjects", False)

		listWidget =  listWidget or self.skinMeshes_lst
		currentMeshes = [listWidget.item(rowIdx).text() for rowIdx in range(listWidget.count())]
		
		if currentMeshes and returnAsObjects:
			returnObjects = []
			for meshName in currentMeshes:
				mesh = mnsUtils.checkIfObjExistsAndSet(meshName)
				if mesh: returnObjects.append(mesh)
			return returnObjects

		return currentMeshes

	def addMeshes(self, listWidget):
		if listWidget:
			selection = pm.ls(sl=True)
			if selection:
				currentMeshes = self.getCurrentMeshes(listWidget)
				
				meshesToAdd = []
				for meshToAdd in selection:
					if not meshToAdd.nodeName() in currentMeshes: meshesToAdd.append(meshToAdd.nodeName())
				
				if meshesToAdd:
					listWidget.addItems(meshesToAdd)
					self.sortMeshLists()
					self.updateMeshWidgetsDict()
		self.refreshSelectionState()

	def removeMeshes(self, listWidget):
		if listWidget:
			newMeshes = [listWidget.item(rowIdx).text() for rowIdx in range(listWidget.count()) if not listWidget.item(rowIdx).isSelected()]
			listWidget.clear()
			listWidget.addItems(newMeshes)	
			self.sortMeshLists()
			self.updateMeshWidgetsDict()
			self.refreshSelectionState()

	def copySkin(self):
		sourceMeshes = self.getCurrentMeshes(self.sourceMshes_lst, returnAsObjects = True)
		targetMeshes = self.getCurrentMeshes(self.targetMeshes_lst, returnAsObjects = True)

		if sourceMeshes and targetMeshes:
			surfaceAssociation = self.surfaceAssociation_cb.currentText()
			influenceAssociation = self.influenceAssociation_cb.currentText()
			mnsSkinUtils.copySkin(sourceMeshes, targetMeshes, surfaceAssociation = surfaceAssociation, influenceAssociation = influenceAssociation)

	def loadSelectionToLineEdit(self, lEditWidget = None):
		sel = pm.ls(sl = True)
		if sel:
			lEditWidget.setText(sel[0].nodeName())
		else:
			lEditWidget.clear()
			
	#####MOCAP TAB################
	def initializeGuidePresetCb(self):
		presetDirectory = dirname(__file__) + "/guidePresets"
		if os.path.isdir(presetDirectory):
			presets = []
			for file in os.listdir(presetDirectory):
				if file.endswith(".ma"): presets.append(file.split(".")[0])
			if presets:
				self.guidePresets_cb.addItems(presets)

	#####SETTINGS TAB################
	def getModuleSettings(self, rootGuide, firstAttempt = True, **kwargs):
		"""Get passed in module settings.
		First get the default settings and values from the build-module directory,
		then compare against the rootGuide attributes, and return the filtered and altered settings.
		"""

		includeCreationOnly = kwargs.get("includeCreationOnly", False)
		getDefaults = kwargs.get("getDefaults", False)

		mnsLog.logCurrentFrame()
		split = 0
		if rootGuide:
			rigTop = blkUtils.getRigTopForSel()
			settingsPath = os.path.join(dirname(abspath(__file__)), "core/allModSettings.modSettings").replace("\\", "/")
			optArgsFromFile, self.sidePlaceHolder = blkUtils.getSettings(settingsPath, rootGuide, mnsPS_gRootCtrl)
			if not includeCreationOnly: optArgsFromFile = blkUtils.filterCreationOnlyFromArgs(optArgsFromFile)

			modSetFile = os.path.join(rootGuide.node.modPath.get(), rootGuide.node.modType.get() + ".modSettings").replace("\\", "/")
			if not os.path.isfile(modSetFile) and firstAttempt:
				blkUtils.missingModuleActionTrigger(rigTop, rootGuide.node.modType.get(), self.buildModulesBtns)
				return self.getModuleSettings(rootGuide, firstAttempt = False)

			if os.path.isfile(modSetFile):
				pm.select(rootGuide.node)
				modArgs = mnsUtils.readSetteingFromFile(modSetFile)

				if not includeCreationOnly: 
					optArgsFromFile = blkUtils.filterCreationOnlyFromArgs(optArgsFromFile)
					modArgs = blkUtils.filterCreationOnlyFromArgs(modArgs)

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


				optArgsFromFile, self.sidePlaceHolder = blkUtils.filterSettings(optArgsFromFile, rootGuide.node)
				

				#return; dict,int (optionalArguments, spilt index - for dynUI)
				return optArgsFromFile, split
			else: mnsLog.log("Can't find module path. Aborting.", svr = 3)

	def loadModuleSettings(self, firstAttempt = True):
		"""Load selected module setting trigger.
		"""

		mnsLog.log("Module Settings Load", svr = 1)
		sel = pm.ls(sl=1)
		if sel:
			rigSettings = True

			partialModules = blkUtils.collectPartialModulesRoots(2)
			if partialModules:
				rootGuide = None
				rigTop = blkUtils.getRigTopForSel()
				readOnly = False
				batchEdit = bool(len(partialModules) - 1)
				multiTypedModules = False
				title = ""

				#loop modules
				settingHolders = []
				newSelection = []
				previousModType = None
				for moduleRoot in partialModules:
					rootGuide = mnsUtils.validateNameStd(moduleRoot)
					settingHolders.append(rootGuide)
					newSelection.append(rootGuide.node)

					#check read only state
					if not readOnly:
						status, constructed = mnsUtils.validateAttrAndGet(rootGuide, "constructed", False)
						if constructed:
							readOnly = True
							mnsLog.log("Can't alter settings in constructed state. Loading setting in read-only mode.", svr = 2)

					#check type
					status, moduleType = mnsUtils.validateAttrAndGet(rootGuide, "modType", None)

					if not previousModType:
						previousModType = str(moduleType)
					elif not multiTypedModules and previousModType != moduleType:
						multiTypedModules = True

					#title compile
					if not title:
						title = rootGuide.side + "_" + rootGuide.body + "_" + rootGuide.alpha + " (" + moduleType + ")"
					else:
						title += "\n" + rootGuide.side + "_" + rootGuide.body + "_" + rootGuide.alpha + " (" + moduleType + ")"

				split = 0
				optArgsFromFile, split = self.getModuleSettings(rootGuide)
				if multiTypedModules:
					optArgsFromFile = optArgsFromFile[:split]
				if batchEdit:
					newArgs = []
					for arg in optArgsFromFile:
						if not arg.name == "body" and not arg.name == "alpha" and not arg.name == "blkSide" and not arg.name == "dividerMName":
							newArgs.append(arg)
						else:
							split -= 1
					optArgsFromFile = newArgs

				pm.select(newSelection, r = True)

				if optArgsFromFile:
					win = mnsDynUI.MnsDynamicDefUI(
									None,
									customArgs = optArgsFromFile, 
									winTitle = "Mansur - BLOCK  ||  " + rootGuide.node.modType.get(),
									title = title,
									rootGuide = rootGuide,
									btnText = "Update Settings", 
									runCmd = self.updateSettings, 
									preDefinedArgs = {"settingsHolders": settingHolders, "rigTop": rigTop, "origArgs": optArgsFromFile}, 
									icon = GLOB_guiIconsDir + "/logo/block_t5.png",
									split = split,
									readOnly = readOnly,
									multiTypeEdit = multiTypedModules,
									batchEdit = batchEdit,
									closeOnApplyEnabled = True)
					win.loadUI()	

			else:
				self.loadRigSettings()
		else:
			mnsLog.log("No selection.", svr =2)
				
	def loadRigSettings(self):
		"""Load selected rig settings trigger.
		"""

		mnsLog.log("Rig Settings Load", svr = 1)
		rigTop = blkUtils.getRigTopForSel()
		if rigTop:
			settingsPath = os.path.join(dirname(abspath(__file__)), "core/charInitSettings.charSet").replace("\\", "/")
			optArgsFromFile, self.sidePlaceHolder = blkUtils.getSettings(settingsPath, rigTop, mnsPS_rigTop)
			if optArgsFromFile:
				win = mnsDynUI.MnsDynamicDefUI(None, 
												customArgs = optArgsFromFile, 
												winTitle = "Mansur - BLOCK  ||  Rig Settings", 
												title = "Block Rig Top Edit Settings", 
												btnText = "Update Settings", 
												icon = GLOB_guiIconsDir + "/logo/block_t5.png",
												runCmd = self.updateSettings, 
												preDefinedArgs = {"settingsHolder": rigTop, "rigTop": rigTop}, 
												split = len(optArgsFromFile) - 12,
												firstTabTitle = "Main",
												secondTabTitle = "Custom Scripts",
												closeOnApplyEnabled = True)
				win.loadUI()

	def updateSettings(self, **kwargs):
		"""update setting trigger. This method will apply when a user altered any data within a setting window and chose to apply the changes.
		The current settings will be validated against the default settings, and in case any data changed,
		all neccessary actions will be called to apply and store the changes.
		"""

		mnsLog.logCurrentFrame()
		reBuildJntStruct = False
		jntStrcutSoftMod = False
		isRigSettings = False

		origArgsPairing = {}
		if "origArgs" in kwargs.keys():
			for attr in kwargs["origArgs"]:
				origArgsPairing.update({attr.name: attr})
		else:
			isRigSettings = True

		settingsHolders = None
		if "settingsHolder" in kwargs.keys():
			settingsHolders = [kwargs["settingsHolder"]]
		elif "settingsHolders" in kwargs.keys():
			settingsHolders = kwargs["settingsHolders"]

		convertedChannelControlAttrs = []
		for settingsHolder in settingsHolders:
			settingsHolder = mnsUtils.validateNameStd(settingsHolder).node
			
			for attr in sorted(kwargs.keys()):
				if settingsHolder.hasAttr(attr):
					if "channelControl".lower() in attr.lower() and not attr in convertedChannelControlAttrs:
						kwargs[attr] = mnsUtils.splitEnumAttrToChannelControlList(None, None, fromExistingList = kwargs[attr])
						convertedChannelControlAttrs.append(attr)

					if isRigSettings or origArgsPairing[attr].default != kwargs[attr]:
						if "colorScheme".lower() in attr.lower() or "schemeOverride".lower() in attr.lower():
							oldVals = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList(attr, settingsHolder)
							if oldVals != kwargs[attr]: 
								settingsHolder.attr(attr).setLocked(False)
								pm.deleteAttr( settingsHolder + "." + attr)
								mnsUtils.addAttrToObj(settingsHolder, name = attr , type = type(kwargs[attr]), value = kwargs[attr], locked = True, cb = False, keyable = False)
								if "colorScheme".lower() in attr.lower():
									blkUtils.setgCtrlColorForRigTop(kwargs["rigTop"])
								if "colOverride" in kwargs:
									blkUtils.setgCtrlColorForModule(kwargs["rigTop"], settingsHolder)
						elif "channelControl".lower() in attr.lower():
							oldVals = mnsUtils.splitEnumAttrToChannelControlList(attr, settingsHolder)
							if oldVals != kwargs[attr]:
								settingsHolder.attr(attr).setLocked(False)
								pm.deleteAttr( settingsHolder + "." + attr)
								attrValue = mnsArgs.convertChannelControlDictToAttr(kwargs[attr])
								mnsUtils.addAttrToObj(settingsHolder, name = attr , type = type(attrValue), value = attrValue, locked = True, cb = False, keyable = False)
						elif attr.lower() == "spaces" or (attr in origArgsPairing and origArgsPairing[attr].multiRowList) or (isRigSettings and attr == "preDefinedCnsCtrls"):
							oldVals = mnsUtils.splitEnumToStringList(attr, settingsHolder)
							if oldVals != kwargs[attr]:
								settingsHolder.attr(attr).setLocked(False)
								pm.deleteAttr( settingsHolder + "." + attr)
								mnsUtils.addAttrToObj(settingsHolder, name = attr , type = type(kwargs[attr]), value = kwargs[attr], locked = True, cb = False, keyable = False)
						else:
							locked = False
							if settingsHolder.attr(attr).isLocked(): locked = True
							if locked: settingsHolder.attr(attr).setLocked(False)
							settingsHolder.attr(attr).set(kwargs[attr])
							if locked: settingsHolder.attr(attr).setLocked(True)

			#attr Host
			status, doAttributeHostCtrl = mnsUtils.validateAttrAndGet(settingsHolder, "doAttributeHostCtrl", False)
			customGuides = blkUtils.getModuleDecendentsWildcard(settingsHolder, customGuidesOnly = True)
			for cg in customGuides:
				if "AttrHost_" in cg.name:
					if doAttributeHostCtrl: cg.node.v.set(True)
					else: cg.node.v.set(False)
					break
			#name
			prevNameStd = mnsUtils.validateNameStd(settingsHolder)

			nameStd = MnsNameStd(node = settingsHolder)
			nameStd.splitName()
			if "characterName" in kwargs.keys(): kwargs["body"] = kwargs.pop("characterName")
			kwargs.update({"autoRename": False})
			kwargs.update({"bodyPattern": nameStd.body})

			nameStd = mnsUtils.returnNameStdChangeElement(nameStd, **kwargs)

			if nameStd.name != prevNameStd.name:
				#change all spaces if the name has changed
				baseGuide = blkUtils.getRootGuideFromRigTop(kwargs["rigTop"])
				if baseGuide:
					guidesCollect = [o for o in baseGuide.node.listRelatives(ad = True, type = "transform") if "_" + mnsPS_gRootCtrl in o.nodeName()]
					for gRoot in guidesCollect:
						if gRoot.hasAttr("spaces"):
							spaces = mnsUtils.splitEnumToStringList("spaces", gRoot)
							
							newSpaces = []
							recreateAttr = False
							for s in spaces:
								if prevNameStd.body in s:
									recreateAttr = True
									oldSpaceStd = mnsUtils.validateNameStd(s)
									if oldSpaceStd:
										kwargs["autoRename"] = False
										newSpaceStd = mnsUtils.returnNameStdChangeElement(oldSpaceStd, **kwargs)
										newSpaces.append(newSpaceStd.name)
								else:
									newSpaces.append(s)

							if recreateAttr:
								gRoot.spaces.setLocked(False)
								pm.deleteAttr(gRoot + ".spaces")
								mnsUtils.addAttrToObj(gRoot, name = "spaces" , type = "enum", value = newSpaces , locked = True, cb = False, keyable = False)

				#change module name		
				kwargs["autoRename"] = True			
				moduleDecendents = blkUtils.getModuleDecendentsWildcard(prevNameStd, getAll = True)
				for c in moduleDecendents:
					node = mnsUtils.checkIfObjExistsAndSet(obj = c)
					if node:
						childNameStd = MnsNameStd(node = node)
						childNameStd.splitName()
						childNameStd = mnsUtils.returnNameStdChangeElement(childNameStd, **kwargs)
				blkUtils.setgCtrlColorForModule(kwargs["rigTop"], nameStd)
				

				#rename puppet
				if nameStd.node.hasAttr("blkClassID"):
					if nameStd.node.attr("blkClassID").get() == "rigTop":
						puppetBase = blkUtils.getPuppetRootFromRigTop(nameStd)
						if puppetBase: blkUtils.namePuppet(nameStd)


			#joint struct rebuild
			if "origArgs" in kwargs.keys():
				for k in kwargs["origArgs"]:
					if k.name in kwargs.keys():
						if k.jntStructMember:
							if k.default != kwargs[k.name]: 
								reBuildJntStruct = True
								break
						if k.jntStructSoftMod:
							if k.default != kwargs[k.name]: 
								jntStrcutSoftMod = True

			kwargs.update({"settingsHolder": settingsHolder})
			if reBuildJntStruct: blkUtils.updateRigStructure(False, **kwargs)
			elif jntStrcutSoftMod: blkUtils.updateRigStructure(True, **kwargs)

		mnsLog.log("Settings Updated.", svr = 1)

	#####GUIDES TAB################
	def pureDuplicate(self, modRoot, **kwargs):
		"""Module duplicate.
		Gather all of the requested module's settings, as well as compare against the module's default settings.
		Build a new module (same module) using the gathered data.
		"""

		if modRoot:
			parentGuide = mnsUtils.validateNameStd(modRoot.node.getParent())
			settings, split = self.getModuleSettings(modRoot)
			buildModuleBtn = self.getCorrespondingModuleButtonForModule(modRoot)
			newModule = mnsBuildModules.MnsBuildModule(buildModuleBtn, skipUI = True, parentGuide = parentGuide, settingsHolder = modRoot.node)

			mnsUtils.setAttr(newModule.builtGuides[0].node.alpha, newModule.builtGuides[0].alpha)

			origGuides = blkUtils.getModuleDecendentsWildcard(modRoot, getJoints = False, getInterpLocs = False, getInterpJnts = False, getCtrls = False, getFreeJntGrp = False, getPLGs = False)
			newGuides = blkUtils.getModuleDecendentsWildcard(newModule.rootGuide, getJoints = False, getInterpLocs = False, getInterpJnts = False, getCtrls = False, getFreeJntGrp = False, getPLGs = False)

			for k in range (0, len(newGuides)):
				keyableAttrs = newGuides[k].node.listAttr(k = True, u = True, s = True)
				for kAttr in keyableAttrs: 
					mnsUtils.setAttr(kAttr, origGuides[k].node.attr(kAttr.attrName()).get())

			#match shape if needed
			origCusGuides = [cGuide for cGuide in origGuides if cGuide.suffix == mnsPS_cgCtrl]
			symCusGuides = [cGuide for cGuide in newGuides if cGuide.suffix == mnsPS_cgCtrl]

			for k, cGuide in enumerate(origCusGuides):
				if type(cGuide.node.getShape()) == pm.nodetypes.NurbsCurve:
					blkUtils.copyShape(cGuide.node, [symCusGuides[k].node], reposition = False)
					#bsp = pm.blendShape(cGuide.node, symCusGuides[k].node)[0]
					#bsp.attr(cGuide.node.nodeName()).set(1.0)
					#pm.delete(symCusGuides[k].node, ch = True)

			#return;MnsBuildModule (New Module)
			return newModule

	def duplicateModule(self, **kwargs):
		"""Module duplicate.
		Gather all of the requested module's settings, as well as compare against the module's default settings.
		Build a new module (same module) using the gathered data, then match all guide positions for the new module guide.
		"""

		self.constructProg_pb.setValue(0)
		rigTop, constructed = blkUtils.getRigTopForSel(getConstructionState = True)
		if rigTop and constructed:
			mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
		else:
			rootGuide = mnsUtils.validateNameStd(blkUtils.getModuleRootForSel())
			skipChildrenModules = kwargs.get("skipChildrenModules", False)

			if rootGuide:
				self.constructProg_pb.setValue(5)

				if not rootGuide.body == "blkRoot":
					if not skipChildrenModules:
						childModules = [rootGuide] + blkUtils.getChildModules(rootGuide)
					else:
						childModules = [rootGuide]

					finalSelect = None
					newModules = {}
					for k, modRoot in enumerate(childModules):
						newModule = self.pureDuplicate(modRoot)
						if modRoot is rootGuide: finalSelect = newModule.builtGuides[0]
						newModules.update({modRoot.name: newModule})
						self.constructProg_pb.setValue(5 + (90 / len(childModules) * float(k +1)))

					for k, modRoot in enumerate(childModules):
						parentGuide = mnsUtils.validateNameStd(modRoot.node.getParent())
						parentRoot = blkUtils.getModuleRoot(parentGuide).name
						if parentRoot in [c.name for c in childModules]:
							newModule = newModules[modRoot.name]
							if parentRoot in newModules:
								newParent = mnsUtils.returnNameStdChangeElement(nameStd = parentGuide , alpha = newModules[parentRoot].builtGuides[0].alpha, autoRename = False)
								newParent = mnsUtils.checkIfObjExistsAndSet(obj = newParent.name)
								if newParent: pm.parent(newModule.builtGuides[0].node, newParent)
						self.constructProg_pb.setValue(90 + (20 / len(childModules) * float(k +1)))

					if finalSelect: pm.select(finalSelect.node, r = 1)
					self.constructProg_pb.setValue(100)
					mnsLog.log("Duplicated successfully.", svr =1)
					self.constructProg_pb.setValue(0)

				else:
					mnsLog.log("Can't duplicate the root guide. Aborting", svr =2)

	def symmetrizeModule(self):
		"""Symmetrize module trigger.
		Exclusive class member process.
		This method will attempt to symmetrize the requested module guides.
		"""

		rigTop, constructed = blkUtils.getRigTopForSel(getConstructionState = True)
		if rigTop and constructed:
			mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
		else:
			partialModules = blkUtils.collectPartialModulesRoots(2)

			symBranches = []
			for rg in partialModules:
				rootGuide = mnsUtils.validateNameStd(rg)

				if rootGuide:
					if not rootGuide.body == "blkRoot":
						if rootGuide.side != mnsPS_cen:
							symSide = mnsPS_right
							if rootGuide.side == mnsPS_right: symSide = mnsPS_left

							#get sym branch root
							branchRoot = blkUtils.getSideModuleBranchRoot(rootGuide)
							
							if branchRoot and not branchRoot.node in symBranches:
								symBranches.append(branchRoot.node)

								#first validate existence of all symmetry module roots.
								branchRoots = [branchRoot] + blkUtils.getChildModules(branchRoot)
								#rearrange roots, to make sure compound modules are first in line
								compounds = []
								nonCompounds = []
								for rootGuide in branchRoots: 
									pyModule, methods = blkUtils.getPyModuleFromGuide(rootGuide)
									if "moduleCompound" in methods:
										compounds.append(rootGuide)
									else:
										nonCompounds.append(rootGuide)
								branchRoots = compounds + nonCompounds


								#handle plgs
								plgsToRestore = {}
								for rootGuide in branchRoots: 
									symRoot = blkUtils.getOppositeSideControl(rootGuide)
									if symRoot: 
										#get plgs
										modulePLGs = blkUtils.getModuleDecendentsWildcard(symRoot, plgsOnly = True)
										for plg in modulePLGs:
											# store origMaster
											delMaster = blkUtils.getDeleteMasterFromSlave(plg)
											if delMaster: 
												plgsToRestore.update({plg: delMaster.name})
												# remove ndr master
												blkUtils.disconnectSlaveFromMaster(plg)
											
								# sym re-creation
								newModule = None
								for rootGuide in branchRoots: 
									symRoot = blkUtils.getOppositeSideControl(rootGuide)
									if not symRoot: 
										buildModuleBtn = self.getCorrespondingModuleButtonForModule(rootGuide)
										parentGuide = mnsUtils.validateNameStd(rootGuide.node.getParent())
										newModule = mnsBuildModules.MnsBuildModule(buildModuleBtn, skipUI = True, parentGuide = parentGuide, settingsHolder = rootGuide.node, symmetrize = True)
								
								
								#match hierarchy
								for rootGuide in branchRoots:
									symRoot = blkUtils.getOppositeSideControl(rootGuide)
									if symRoot:
										origParent =  mnsUtils.validateNameStd(rootGuide.node.getParent())
										symParent = blkUtils.getOppositeSideControl(origParent)
										if symParent: pm.parent(symRoot.node, symParent.node)

								#mirror attrs
								postSymJntStructRoots = []

								for rootGuide in branchRoots:
									symRoot = blkUtils.getOppositeSideControl(rootGuide)
									rigTop = blkUtils.getRigTop(symRoot.node)

									#get module settings
									settingsPath = symRoot.node.modPath.get() + "/" + symRoot.node.modType.get() + ".modSettings"
									optArgsFromFile, sidePlaceHolder = blkUtils.getSettings(settingsPath, rigTop, mnsPS_rigTop)
									jntStructMembers = []
									softModMembers = []
									meshComponentsMembers = []

									for arg in optArgsFromFile:
										if arg.jntStructMember: jntStructMembers.append(arg.name)
										if arg.jntStructSoftMod: softModMembers.append(arg.name)
										if arg.meshComponents: meshComponentsMembers.append(arg.name)

									if symRoot:
										#match all attributes
										origGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, getJoints = False, getInterpLocs = False, getFreeJntGrp = False, getInterpJnts = False)
										symGuides = blkUtils.getModuleDecendentsWildcard(symRoot, getJoints = False, getInterpLocs = False, getFreeJntGrp = False, getInterpJnts = False)

										rebuildJntStruct = False
										jntStructSoftMod = False

										for k in range (0, len(symGuides)):
											keyableAttrs = symGuides[k].node.listAttr(k = True, u = True, s = True)
											for kAttr in keyableAttrs:
												kAttr.set(origGuides[k].node.attr(kAttr.attrName()).get())

											customAttrs = symGuides[k].node.listAttr(ud = True)
											for cAttr in customAttrs: 
												if origGuides[k].node.hasAttr(cAttr.attrName()):
													if cAttr.type() != "message":
														if cAttr.attrName() == "spaces":
															newSpaces = []
															
															spaces = mnsUtils.splitEnumToStringList(cAttr.attrName(), origGuides[k].node)
															if spaces:
																for space in spaces:
																	isDefaultSapce = False
																	if "*" in space:
																		isDefaultSapce = True
																		space = space.replace("*", "")

																	spaceStd = mnsUtils.validateNameStd(space)
																	if spaceStd:
																		if spaceStd.side == mnsPS_left or spaceStd.side == mnsPS_right:
																			spaceSymSide = "r"
																			if spaceStd.side == mnsPS_right: spaceSymSide = "l"
																			symSpace = mnsUtils.returnNameStdChangeElement(spaceStd, side = spaceSymSide, autoRename = False)
																			if symSpace: 
																				spaceName = symSpace.name
																				if isDefaultSapce: spaceName += "*"
																				newSpaces.append(symSpace.name)
																		else:
																			spaceName = spaceStd.name
																			if isDefaultSapce: spaceName += "*"
																			newSpaces.append(spaceName)
															if not newSpaces: newSpaces.append("None")
															mnsUtils.addAttrToObj([symGuides[k]], type = "enum", value = newSpaces, name = cAttr.attrName(), replace = True, locked = True, cb = False, keyable = False)
														elif cAttr.type() == "enum": #multi row list attrs
															enumList = mnsUtils.splitEnumToStringList(cAttr.attrName(), origGuides[k].node)
															if enumList:
																enumList = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = enumList)
																if enumList:
																	if all(item for item in enumList if "_" in item and len(item.split("_")) == 4):
																		newValues = []
																		for item in enumList:
																			itemStd = MnsNameStd()
																			itemStd.name = item
																			itemStd.splitDefinedName()
																			if itemStd.side == mnsPS_left or itemStd.side == mnsPS_right:
																				itemSymSide = "r"
																				if itemStd.side == mnsPS_right: itemSymSide = "l"
																				symItem = mnsUtils.returnNameStdChangeElement(itemStd, side = itemSymSide, autoRename = False)
																				if symItem: 
																					symName = symItem.name
																					newValues.append(symItem.name)
																		if newValues:
																			mnsUtils.addAttrToObj([symGuides[k]], type = "enum", value = newValues, name = cAttr.attrName(), replace = True, locked = True, cb = False, keyable = False)
																			
														elif "blkSide" != cAttr.attrName() and not "_pose" in cAttr.attrName().lower():
															#symmetrize components
															if cAttr.attrName() in meshComponentsMembers:
																if cAttr.type() == "string":
																	stringValue = origGuides[k].node.attr(cAttr.attrName()).get()
																	if stringValue: 
																		stringValueArray = mnsString.splitStringToArray(stringValue)
																		if stringValueArray:
																			firstComponent = stringValueArray[0]
																			if "." in firstComponent:
																				mesh = mnsUtils.checkIfObjExistsAndSet(firstComponent.split(".")[0])
																				if mesh:
																					symTable = mnsMeshUtils.getSymDictForMesh(mesh.nodeName())
																					newArray = []
																					for meshComponent in stringValueArray:
																						vertIndex = int(meshComponent.split("[")[-1].replace("]", ""))
																						if vertIndex in symTable: 
																							symVertIndex = symTable[vertIndex]
																							symmetricalComponent = meshComponent.split("[")[0] + "[" + str(symVertIndex) + "]"
																							newArray.append(symmetricalComponent)
																					if newArray:
																						newArrayString = mnsString.flattenArray(newArray)
																						mnsUtils.setAttr(cAttr, newArrayString)
																						if cAttr.attrName() in jntStructMembers: rebuildJntStruct = True
																						if cAttr.attrName() in softModMembers: jntStructSoftMod = True
															elif cAttr.type() == "string": #mirror string values
																stringValue = origGuides[k].node.attr(cAttr.attrName()).get()
																if stringValue: 
																	stringValueArray = mnsString.splitStringToArray(stringValue)
																	if stringValueArray:
																		newArray = []
																		for componentValue in stringValueArray:
																			newValue = componentValue
																			componentValueStd = mnsUtils.validateNameStd(componentValue)
																			if componentValueStd:
																				symComponent = blkUtils.getOppositeSideControl(componentValueStd)
																				if symComponent:
																					newValue = symComponent.node.nodeName()
																				
																			newArray.append(newValue)

																		newArrayString = mnsString.flattenArray(newArray)
																		mnsUtils.setAttr(cAttr, newArrayString)

															elif cAttr.attrName() == "extraChannels":
																if origGuides[k].node.attr(cAttr.attrName()).get():
																	extraChannelsList = json.loads(origGuides[k].node.attr(cAttr.attrName()).get())
																	for row in extraChannelsList:
																		attrName = row["attrName"]
																		if attrName.startswith("l_") or attrName.startswith("r_"):
																			if attrName[0] == "l": attrName = "r" + attrName[1:]
																			else: attrName = "l" + attrName[1:]
																			row["attrName"] = attrName
																		attrTarget = row["attrTarget"]
																		if "l_" in attrTarget or "r_" in attrTarget:
																			splitName = attrTarget.split(".")
																			for k, stringComponent in enumerate(splitName):
																				if stringComponent.startswith("l_") or stringComponent.startswith("r_"):
																					if stringComponent[0] == "l": stringComponent = "r" + stringComponent[1:]
																					else: stringComponent = "l" + stringComponent[1:]
																					splitName[k] = stringComponent
																			row["attrTarget"] = mnsString.combineStringList(splitName, ".")
																	extraChannelsList = json.dumps(extraChannelsList)
																	mnsUtils.setAttr(cAttr, extraChannelsList)
															elif cAttr.get() != origGuides[k].node.attr(cAttr.attrName()).get():
																mnsUtils.setAttr(cAttr, origGuides[k].node.attr(cAttr.attrName()).get())
																if cAttr.attrName() in jntStructMembers: rebuildJntStruct = True
																if cAttr.attrName() in softModMembers: jntStructSoftMod = True

										#rebuild jnt struct	
										if rebuildJntStruct or jntStructSoftMod:
											status, postSymmetryJntStruct = mnsUtils.validateAttrAndGet(rootGuide, "postSymmetryJntStruct", False)
											if not postSymmetryJntStruct:
												symModule = blkUtils.getModuleFromGuide(symRoot)
												if symModule:
													builtGuides = blkUtils.getModuleGuideDecendents(symRoot)
													if rebuildJntStruct:
														blkUtils.deleteFreeJntGrpForModule(builtGuides[0])
														interpLocs = symModule.jointStructure(mansur, builtGuides)
														blkUtils.handleInterpLocsStructureReturn(rigTop, interpLocs, builtGuides)
													else:
														symModule.jointStructureSoftMod(mansur, builtGuides)
											else:
												postSymJntStructRoots.append(symRoot)

										#match shape if needed
										origCusGuides = [cGuide for cGuide in origGuides if cGuide.suffix == mnsPS_cgCtrl]
										symCusGuides = [cGuide for cGuide in symGuides if cGuide.suffix == mnsPS_cgCtrl]

										for k, cGuide in enumerate(origCusGuides):
											if type(cGuide.node.getShape()) == pm.nodetypes.NurbsCurve:
												blkUtils.copyShape(cGuide.node, [symCusGuides[k].node], reposition = False)
												pm.makeIdentity(symCusGuides[k].node)
												#bsp = pm.blendShape(cGuide.node, symCusGuides[k].node)[0]
												#bsp.attr(cGuide.node.nodeName()).set(1.0)
												#pm.delete(symCusGuides[k].node, ch = True)

								
								symBranchRoot = blkUtils.getOppositeSideControl(branchRoot)
							
								## symmetrize branch root
								parent =  mnsUtils.validateNameStd(symBranchRoot.node.getParent())
								if parent.side == mnsPS_cen:
									mirrorGrp = pm.createNode("transform", name = "tmpMirror")

									if self.relSym_rb.isChecked():
										pm.delete(pm.parentConstraint(parent.node, mirrorGrp))
										pm.delete(pm.scaleConstraint(parent.node, mirrorGrp))
									
									pm.parent(symBranchRoot.node, mirrorGrp)
									mirrorGrp.sx.set(mirrorGrp.sx.get() * -1)
									pm.parent(symBranchRoot.node, parent.node)
									pm.delete(mirrorGrp)

								if postSymJntStructRoots:
									for symRoot in postSymJntStructRoots:
										symModule = blkUtils.getModuleFromGuide(symRoot)
										if symModule:
											builtGuides = blkUtils.getModuleGuideDecendents(symRoot)
											blkUtils.deleteFreeJntGrpForModule(builtGuides[0])
											interpLocs = symModule.jointStructure(mansur, builtGuides)
											blkUtils.handleInterpLocsStructureReturn(rigTop, interpLocs, builtGuides)

								## restore plgs
								if plgsToRestore:
									for plgKey in plgsToRestore:
										originalMaster = mnsUtils.validateNameStd(plgsToRestore[plgKey])
										if originalMaster:
											blkUtils.connectSlaveToDeleteMaster(plgKey, originalMaster)

								##sym vJnts
								rootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(branchRoot))
								if rootJnt:
									vJnts = [j for j in rootJnt.node.listRelatives(ad = True, type = "joint") if "_" in j.nodeName() and j.nodeName().split("_")[-1] == mnsPS_vJnt]
									for vJnt in vJnts:
										blkUtils.symmetrizeVJ(vJnt)

								pm.select(symBranchRoot.node, r = True)
								mnsLog.log("Symmetrized branch successfully.", svr =1)

							else:
								mnsLog.log("Couldn't find a brach root for selection. Aborting symmetry.", svr =2)

						else:
							mnsLog.log("Can't symmetrize a center component. Aborting symmetry.", svr =2)

	def promoteModule(self):
		sel = pm.ls(sl=True)

		if sel:
			sel = sel[0]

		rigTop, constructed = blkUtils.getRigTopForSel(getConstructionState = True)
		if rigTop and constructed:
			mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
		else:
			if sel and sel.hasAttr("modType"):
				moduleRoot = blkUtils.getModuleRoot(sel)
				currentGuides = blkUtils.getModuleDecendentsWildcard(moduleRoot, getFreeJntGrp = False, getCtrls = False, getCustomGuides = False, getInterpLocs = False, getJoints = False)
				currentGuidesCount = len(currentGuides)
				currentModuleSettings, split = self.getModuleSettings(moduleRoot, includeCreationOnly = True)
				
				allSettingsPath = os.path.join(dirname(abspath(__file__)), "core/allModSettings.modSettings").replace("\\", "/")
				allSettings = mnsUtils.readSetteingFromFile(allSettingsPath)

				maxGuides, minGuides = -1, -1
				for arg in allSettings:
					if arg.name == "numOfGuides":
						maxGuides = int(arg.max)
						minGuides = int(arg.min)
						break

				promotableModules = []
				for moduleKey in self.bmLib:
					if moduleKey !=  moduleRoot.node.modType.get():
						modSettings = mnsUtils.readSetteingFromFile(self.bmLib[moduleKey].path + "/" + moduleKey + ".modSettings")
						maxGuidesMod = maxGuides
						minGuidesMod = minGuides
						for arg in modSettings:
							if arg.name == "numOfGuides":
								maxGuidesMod = int(arg.max)
								minGuidesMod = int(arg.min)
								break

						if currentGuidesCount <= maxGuidesMod and currentGuidesCount >= minGuidesMod:
							promotableModules.append(moduleKey)

				moduleKey, ok = QtWidgets.QInputDialog.getItem(self, 'Promote To', "Promote To:", promotableModules, 0, False) 
				if moduleKey and ok:
					buildModuleBtn = self.bmLib[moduleKey]

					#get parent 
					parentGuide = mnsUtils.validateNameStd(moduleRoot.node.getParent())

					#create new one
					pm.select(parentGuide.node)
					newModule = mnsBuildModules.MnsBuildModule(buildModuleBtn, skipUI = True, parentGuide = parentGuide, settingsHolder = moduleRoot.node)
					newGuides = blkUtils.getModuleDecendentsWildcard(newModule.rootGuide, getCustomGuides = False, getJoints = False, getInterpLocs = False, getInterpJnts = False, getCtrls = False, getFreeJntGrp = False, getPLGs = False)
					origGuides = blkUtils.getModuleDecendentsWildcard(moduleRoot, getCustomGuides = False, getJoints = False, getInterpLocs = False, getInterpJnts = False, getCtrls = False, getFreeJntGrp = False, getPLGs = False)

					for k in range (0, len(newGuides)):
						keyableAttrs = newGuides[k].node.listAttr(k = True, u = True, s = True)
						for kAttr in keyableAttrs: 
							mnsUtils.setAttr(kAttr, origGuides[k].node.attr(kAttr.attrName()).get())

					modSettings, sidePlaceHolder = blkUtils.filterSettings(currentModuleSettings, moduleRoot.node)

					pm.delete(moduleRoot.node)
					MnsRig = mnsBuildModules.MnsRig(execInit = False, buildModulesBtns = self.buildModulesBtns)
					MnsRig.createSubGrpsForRigTop(MnsRig.rigTop)

					kwargsMapping = {"settingsHolder": newGuides[0], "rigTop": newModule.rigTop}
					for k in range (0, len(modSettings)): kwargsMapping.update({modSettings[k].name: modSettings[k].default})
					self.updateSettings(**kwargsMapping)
					mnsLog.log("Module promoted.", svr =1)

	def orientGuides(self):
		"""orient guides trigger
		mode 0 = All
		mode 1 = Branch
		mode 2 = Module
		mode 3 = Selection
		"""

		mode = self.getConstructMode()
		if self.goSelectedOnly_cbx.isChecked():
			mode = 3

		rigTop, constructed = blkUtils.getRigTopForSel(getConstructionState = True)
		if rigTop:
			if not constructed:
				origSelection = pm.ls(sl=1)
				self.constructProg_pb.setValue(5)
				guides = pm.ls(sl=True)
				if guides:
					guidesCollect = None
					if mode == 0:
						baseGuide= blkUtils.getRootGuideFromRigTop(rigTop)
						guidesCollect = blkUtils.collectGuides(baseGuide, getCustomGuides = False, includeDecendents = True, includeDecendentBranch = True, allAsSparse = True)[1]
					elif mode == 1: guidesCollect = blkUtils.collectGuides(guides, getCustomGuides = False,includeDecendents = True, includeDecendentBranch = True, allAsSparse = True)[1]
					elif mode == 2: guidesCollect = blkUtils.collectGuides(guides, getCustomGuides = False, includeDecendents = True, includeDecendentBranch = False, allAsSparse = True)[1]
					elif mode == 3: guidesCollect = pm.ls(sl=True)

					if guidesCollect:
						self.constructProg_pb.setValue(10)

						aimAxis = "y"
						if self.goAimAxisX_rb.isChecked(): aimAxis = "x"
						elif self.goAimAxisZ_rb.isChecked(): aimAxis = "z"
						
						upAxis = "z"
						if self.goUpAxisX_rb.isChecked(): upAxis = "x"
						elif self.goUpAxisY_rb.isChecked(): upAxis = "y"

						blkUtils.orientGuides(guidesCollect, 
												aimAxis = aimAxis,
												flipAim = self.goFlipAim_cbx.isChecked(),
												upAxis = upAxis,
												flipUp = self.goFlipUp_cbx.isChecked(),
												orientNativeOnly = self.goOrientNativeOnly_cbx.isChecked(),
												skipEndGuides = self.goSkipEndGuide_cbx.isChecked(),
												progressBar = self.constructProg_pb)

						pm.select(origSelection, r = True)
						mnsLog.log("Guides oriented successfully.", svr = 1)
					else:
						mnsLog.log("Couldn't find guides from selection. Aborting.", svr = 2)
				else:
					mnsLog.log("Couldn't find guides from selection. Aborting.", svr = 2)
			else:
				mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
		else:
			mnsLog.log("Couldn't find Rig-Top from selection. Aborting.", svr = 2)
		
		#reset prog bar
		self.constructProg_pb.setValue(0)

	##### PICKER ##########
	def plgMatch(self):
		senderBtn = self.sender()
		targetAttr = "t"
		if senderBtn == self.matchScale_btn: targetAttr = "s"

		sel = pm.ls(sl=1)
		plgsCollect = []

		for guide in sel:
			guide = mnsUtils.validateNameStd(guide)
			if guide:
				if guide.suffix == mnsPS_plg and not guide.node.hasAttr("width"):
					plgsCollect.append(guide.node)

		if plgsCollect and len(plgsCollect) > 1:
			target = plgsCollect[-1]
			sources = plgsCollect[:-1]
			pm.undoInfo(openChunk=True)
			for plgToAlign in sources:
				if self.xMatch_cbx.isChecked():
					plgToAlign.attr(targetAttr + "x").set(target.attr(targetAttr + "x").get())
				if self.yMatch_cbx.isChecked():
					plgToAlign.attr(targetAttr + "y").set(target.attr(targetAttr + "y").get())
			pm.undoInfo(closeChunk=True)

	def getPickerExportMode(self):
		mode = 0
		if self.pickerExportBrnach_btn.isChecked():
			mode = 1
		elif self.pickerExportModule_btn.isChecked():
			mode = 2
		elif self.pickerExportSelected_btn.isChecked():
			mode = 3

		#return; int
		return mode

	def getPickerProjectionMode(self):
		mode = 0 
		if self.pickerProjectionModule_btn.isChecked():
			mode = 1
		elif self.pickerProjectionBranch_btn.isChecked():
			mode = 2

		return mode
		
	##### POSING ##########
	def getPoseMode(self):
		pose = "bind"
		if self.tPose_rb.isChecked(): pose = "T"
		elif self.aPose_rb.isChecked(): pose = "A"
		elif self.conceptPose_rb.isChecked(): pose = "concept"
		elif self.customPose_rb.isChecked(): pose = "custom"
		return pose

	def poseSaveLoadTrigger(self, saveLoadMode = 0):
		"""Save/Load pose trigger.
		Simple method to gather pose data and store it, or apply it.
		"""

		rigTop, constructed = blkUtils.getRigTopForSel(getConstructionState = True)
		if rigTop and constructed:
			mnsLog.log("Cannot perform the requested action when the rig is constructed. Please deconstruct and try again.", svr = 2)
		else:
			pose = self.getPoseMode()
			operationMode = self.getConstructMode()

			msgPrompt = False
			if saveLoadMode != 1: msgPrompt = self.posingMsgP_cbx.isChecked()

			blkUtils.saveLoadPose(pm.ls(sl=True), pose = pose, mode = operationMode, saveLoad = saveLoadMode, msgPrompt = msgPrompt, progressBar = self.constructProg_pb, relAbsMode = self.guidePoseAbs_cbx.isChecked())

	##### DEFAULTS ##########
	def getDefaultsMode(self):
		"""Simple method to get the current UI 'defaults' mode.
		"""

		returnState = 0
		#if self.defaultsModules_rb.isChecked(): returnState = 1
		#elif self.defaultsSelected_rb.isChecked(): returnState = 2

		#return;int (defaults mode)
		return returnState

	##### PUPPET ##########
	
	def extractControlShapes(self, **kwargs):
		"""Extract all control shapes from the current constructed rig, and store them for future re-construction.
		"""

		if len(pm.ls(sl=1)) > 0:
			origSelection = pm.ls(sl=1)
			self.constructProg_pb.setValue(0)

			rigTop = blkUtils.getRigTopForSel()
			if rigTop:
				self.constructProg_pb.setValue(5)
				moduleRoots = blkUtils.collectModuleRootsBasedOnMode(self.getConstructMode())
				ctrls = blkUtils.getCtrlAuthFromRootGuides(moduleRoots)
				ctrls = blkUtils.collectCtrlRelatives(1, rootCtrls = ctrls)
				self.constructProg_pb.setValue(10)
				if ctrls:
					ctrlShapes = blkUtils.extractControlShapes(ctrls, rigTop, progressBar = self.constructProg_pb)
				
				self.constructProg_pb.setValue(100)
				mnsLog.log("Shapes extracted successfully.", svr = 1)
				self.constructProg_pb.setValue(0)
				pm.select(origSelection, r = True)
		else:
			mnsLog.log("No selection. Aborting.", svr = 1)
	
	def symmetrizeControlShapes(self):
		"""
		For the selected state, symmetrize all found control shapes.
		sym Mode:
			0: Left to Right
			1: Right to Left
		"""

		mnsLog.log("Symmetrizing control shapes.", svr = 1)

		if len(pm.ls(sl=1)) > 0:
			origSelection = pm.ls(sl=1)
			self.constructProg_pb.setValue(0)

			rigTop = blkUtils.getRigTopForSel()
			if rigTop:
				status, csGrp = mnsUtils.validateAttrAndGet(rigTop, "controlShapesGrp", None)
				if csGrp:
					mode = self.getConstructMode()
					symMode = self.csSymRtoL_btn.isChecked()
					symSide = mnsPS_right
					if symMode == 1: symSide = mnsPS_left

					self.constructProg_pb.setValue(5)

					#collect all module roots
					moduleRoots = blkUtils.collectModuleRootsBasedOnMode(mode)
					addedPrgBarValue = 95.0 / float(len(moduleRoots))
					previousProgValue = 5.0

					for k, moduleRoot in enumerate(moduleRoots):
						moduleRoot = mnsUtils.validateNameStd(moduleRoot)
						#get the constructed state for each module
						status, isConstructed = mnsUtils.validateAttrAndGet(moduleRoot, "constructed", False)
						if status:
							if isConstructed:
								#if the module is constructed:
								#	- check if the module is the source side
								doSym = False
								if symMode == 0 and moduleRoot.side == mnsPS_left: doSym = True
								elif symMode == 1 and moduleRoot.side == mnsPS_right: doSym = True

								if doSym:
									#	- collect all controls for module
									ctrlAuth = blkUtils.getCtrlAuthFromRootGuide(moduleRoot)
									ctrls = blkUtils.collectCtrlRelatives(1, rootCtrls = [ctrlAuth])
									ignoreArray = []

									for ctrl in ctrls:
										#	- for each control, check if the symCtrl exists
										ctrl = mnsUtils.validateNameStd(ctrl)
										symCtrl = mnsUtils.returnNameStdChangeElement(ctrl, side = symSide, autoRename = False)
										symNode = mnsUtils.checkIfObjExistsAndSet(symCtrl.name)
										if symNode:
											symCtrl.node = symNode
											ctrlShapes = ctrl.node.getShapes()
											if ctrlShapes:
												#	- if so, extract the shape temporarily with a temp name, not to override any existing cs
												newShapeTransform = blkUtils.extractControlShapes([ctrl], rigTop, tempExtract = True)
												if newShapeTransform:
													newShapeTransform = newShapeTransform[0]
													#	- symmetrize it
													mirrorGrp = pm.createNode("transform", name = "tmpMirror")
													pm.parent(newShapeTransform.node, mirrorGrp)
													mirrorGrp.sx.set(mirrorGrp.sx.get() * -1)
													pm.parent(newShapeTransform.node, w = True)
													pm.delete(mirrorGrp)
													status, isTextCtrl  = mnsUtils.validateAttrAndGet(ctrl, "isTextCtrl", False)
													if isTextCtrl:
														newShapeTransform.node.r.set([0,0,0])
														newShapeTransform.node.s.set([1,1,1])
													pm.makeIdentity(newShapeTransform.node, apply = True, t = False, r = False, s = True)
													newName = mnsUtils.returnNameStdChangeElement(nameStd = newShapeTransform, side = symSide, autoRename = True)

													symRootGuide = blkUtils.getOppositeSideControl(moduleRoot)
													if symRootGuide:
														rGuideAttr = mnsUtils.addAttrToObj([newName.node], type = "message", name = "rootGuide", value= "", replace = True)[0]
														symRootGuide.node.message >> rGuideAttr 
														
														newColor = blkUtils.getCtrlCol(newName, rigTop, moduleRoot = symRootGuide)
														mnsUtils.setCtrlColorRGB([newName], newColor)

													#	- build the new shape for the symCtrl
													blkUtils.buildShapes([symCtrl], rigTop, mode = 1, tempExtract = True)
													#	- delete temp cs
													pm.delete(newShapeTransform.node)
												else:
													status, isUiStyle = mnsUtils.validateAttrAndGet(ctrl, "isUiStyle", False)
													if status and isUiStyle and not "Frame_" in ctrl.node.nodeName():
														uiStyleOsGrp =blkUtils.getOffsetGrpForCtrl(ctrl)
														if uiStyleOsGrp:
															#get parent Ctrl
															parentCtrl = mnsUtils.validateNameStd(uiStyleOsGrp.node.getParent())
															if parentCtrl and parentCtrl.suffix == mnsPS_ctrl:
																#first make sure to act on the parent ctrl first
																if parentCtrl.node not in ignoreArray:
																	symParentCtrl = blkUtils.getOppositeSideControl(parentCtrl)
																	if symParentCtrl:
																		###sym parent values
																		mnsUtils.mirrorPose2(parentCtrl.node, symParentCtrl.node)

																		## add to ignore array after process is complete
																		ignoreArray.append(parentCtrl.node)

																#only then, act on the child os groups
																symUiStyleOsGrp = blkUtils.getOppositeSideControl(uiStyleOsGrp)
																if symUiStyleOsGrp:
																	###sym values
																	mnsUtils.mirrorPose2(uiStyleOsGrp.node, symUiStyleOsGrp.node)

						self.constructProg_pb.setValue(previousProgValue + addedPrgBarValue)
						previousProgValue += addedPrgBarValue

					self.constructProg_pb.setValue(100)
					mnsLog.log("Control shapes symmetrized successfully.", svr = 1)
					self.constructProg_pb.setValue(0)
					pm.select(origSelection, r = True)
			else:
				mnsLog.log("Couldn't find rigTop for selection. Aborting.", svr = 1)
		else:	
			mnsLog.log("No selection. Aborting.", svr = 1)

	def removeCustomShapes(self):
		"""Remove all custom control shapes from the current rig.
		"""

		if len(pm.ls(sl=1)) > 0:
			rigTop = blkUtils.getRigTopForSel()
			if rigTop:
				status, csGrp = mnsUtils.validateAttrAndGet(rigTop, "controlShapesGrp", None)
				if csGrp:
					reply = pm.confirmDialog( title='Control Shapes Delete', message="Are you sure you want to delete all custom control shapes selected ?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No' )
					if(reply == 'Yes'):
						self.constructProg_pb.setValue(0)

						mode = self.getConstructMode()
						if mode == 0:
							pm.delete(csGrp.listRelatives(c = True, type = "transform"))
						else:
							self.constructProg_pb.setValue(5)
							moduleRoots = blkUtils.collectModuleRootsBasedOnMode(mode)
							ctrls = blkUtils.getCtrlAuthFromRootGuides(moduleRoots)
							ctrls = blkUtils.collectCtrlRelatives(1, rootCtrls = ctrls)
							self.constructProg_pb.setValue(35)

							addedPrgBarValue = 65.0 / float(len(moduleRoots))
							previousProgValue = 35.0

							shapesToDelete = []
							for ctrl in ctrls:
								ctrl = mnsUtils.validateNameStd(ctrl)
								csNode = mnsUtils.checkIfObjExistsAndSet(mnsUtils.returnNameStdChangeElement(nameStd = ctrl , suffix = mnsPS_ctrlShape, autoRename = False).name)
								if csNode: shapesToDelete.append(csNode)

								self.constructProg_pb.setValue(previousProgValue + addedPrgBarValue)
								previousProgValue += addedPrgBarValue
							if shapesToDelete: pm.delete(shapesToDelete)

						self.constructProg_pb.setValue(100)
						mnsLog.log("Control-Shapes Deleted.", svr = 1)
						self.constructProg_pb.setValue(0)
		else:			
			mnsLog.log("No selection. Aborting.", svr = 1)

	##### CONSTRUCT ##########

	def getConstructMode(self):
		"""Get current UI radio-buttons construction state (All/Branch/Module).
		"""

		mnsLog.log("Getting construction state state from UI.")

		mode = 0
		if self.constructActionRadio_all.isChecked(): mode = 0
		elif self.constructActionRadio_branch.isChecked(): mode = 1
		elif self.constructActionRadio_module.isChecked(): mode = 2 

		#return;int (construction mode)
		return mode

	def constructRigInit(self, **kwargs):
		"""Construct trigger.
		"""

		mnsLog.log("Construct button pressed.", svr = 1)
		self.constructProg_pb.setValue(0)
		

		if len(pm.ls(sl=1)) > 0:
			buildTimer = pm.timerX()

			partialModules = []
			mode = self.getConstructMode()
			if mode != 0:
				mnsLog.log("Collecting partial modules.", svr = 0)
				partialModules = blkUtils.collectPartialModulesRoots(mode)

			MnsRig = mnsBuildModules.MnsRig(execInit = False, buildModulesBtns = self.buildModulesBtns)
			MnsRig.constructRig(partialModules = partialModules, progressBar = self.constructProg_pb, buildTimer = buildTimer)
			self.constructProg_pb.setValue(0)

			buildTime = pm.timerX(startTime=buildTimer)
			mnsLog.log("Construction finished at " + str(buildTime) + " Seconds.", svr = 1)
		else:
			mnsLog.log("No selection. Aborting Construction.", svr = 1)

	def deconstructRigInit(self, **kwargs):
		"""Deconstruct trigger.
		"""
		
		mnsLog.log("Deconstruct button pressed.", svr = 1)
		self.constructProg_pb.setValue(0)

		if len(pm.ls(sl=1)) > 0:
			partialModules = []
			mode = self.getConstructMode()
			if mode != 0:
				mnsLog.log("Collecting partial modules.", svr = 0)
				partialModules = blkUtils.collectPartialModulesRoots(mode)

			MnsRig = mnsBuildModules.MnsRig(execInit = False, buildModulesBtns = self.buildModulesBtns)
			MnsRig.deconstructRig(partialModules = partialModules, progressBar = self.constructProg_pb)
			self.constructProg_pb.setValue(0)
		else:
			mnsLog.log("No selection. Aborting.", svr = 1)

def loadBlock():
	"""Load the BLOCK UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsBLOCK_UI")

	blockWin = MnsBlockBuildUI()
	blockWin.loadWindow()
	if previousPosition: blockWin.move(previousPosition)

def reloadBlock(previousBlockWindow):
	mnsUtils.reloadLib()
	blockWin = loadBlock()