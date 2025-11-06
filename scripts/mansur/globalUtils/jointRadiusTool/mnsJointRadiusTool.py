"""=== Author: Assaf Ben Zur ===
A simple tool to control the rig's joint heirarchy joint radius easily.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
import maya.OpenMaya as OpenMaya

#mns dependencies
from ...core import log as mnsLog
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...block.core import blockUtility as blkUtils
from ...core.globals import *
from ...gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsJointRadiusTool.ui")
class MnsJointRadiusTool(form_class, base_class):
	"""Spaces Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsJointRadiusTool, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsJointRadiusTool") 
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		#callbacks
		self.mayaSelectCallBack = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.initializeWidgets)
		self.newSceneCallback = OpenMaya.MEventMessage.addEventCallback("NewSceneOpened", self.deleteCallBacks)
		self.sceneOpenedCallback = OpenMaya.MEventMessage.addEventCallback("SceneOpened", self.deleteCallBacks)
		self.installEventFilter(self)

		# locals
		self.allJnts = []

		#run
		self.initializeWidgets()
		self.connectSignals()
		self.initializeView()
		mnsGui.setGuiStyle(self, "Joint Radius")

	##################	
	###### INIT ######
	##################

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.radius_sld.valueChanged.connect(self.setValue)
		self.radius_sb.valueChanged.connect(self.setValue)

	##################	
	###### View ######
	##################

	def initializeWidgets(self, dummy = None):
		rigTop = blkUtils.getRigTopForSel()
		if not rigTop:
			self.radius_sld.setEnabled(False)
			self.radius_sb.setEnabled(False)
		else:
			self.radius_sld.setEnabled(True)
			self.radius_sb.setEnabled(True)

			currentRadius = self.getCurrentRadius()

			self.radius_sb.blockSignals(True)
			self.radius_sld.blockSignals(True)
			self.radius_sb.setValue(currentRadius)
			self.radius_sld.setValue(currentRadius * 10.0)
			self.radius_sb.blockSignals(False)
			self.radius_sld.blockSignals(False)

	def initializeView(self):
		pass

	##################	
	##### Action #####
	##################

	def eventFilter(self, source, event):
		"""Override event filter to catch the close trigger to delete the callback
		"""
		if event.type() == QtCore.QEvent.Close:
			self.deleteCallBacks()
		
		return super(QtWidgets.QWidget, self).eventFilter(source, event)
	
	def deleteCallBacks(self, dummy = None):
		#close event- delete all callbacks
		try: OpenMaya.MMessage.removeCallback(self.mayaSelectCallBack)
		except: pass

	def getCurrentRadius(self):
		radReturn = 0.0
		self.allJnts = []

		rigTop = blkUtils.getRigTopForSel()
		if rigTop:
			jntStructGrp = blkUtils.getJointStructGrpFromRigTop(rigTop)
			if jntStructGrp:
				rootJoint = jntStructGrp.node.listRelatives(c = True, type = "joint")
				if rootJoint:
					rootJoint = mnsUtils.validateNameStd(rootJoint[0])
					if rootJoint:
						self.allJnts = [rootJoint.node] + rootJoint.node.listRelatives(ad = True, type = "joint")
						radReturn = rootJoint.node.radius.get()

		return radReturn

	def setValue(self):
		sender = self.sender()
		trueVal = 1.0

		if sender == self.radius_sld:
			value = self.radius_sld.value() / 10.0
			self.radius_sb.blockSignals(True)
			self.radius_sb.setValue(value)
			self.radius_sb.blockSignals(False)
			trueVal = value
		elif sender == self.radius_sb:
			value = self.radius_sb.value() * 10.0
			self.radius_sld.blockSignals(True)
			self.radius_sld.setValue(value)
			self.radius_sld.blockSignals(False)
			trueVal = value

		if self.allJnts:
			for j in self.allJnts:
				j.radius.set(trueVal)

	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsJointRadiusTool", svr = 0)
		self.show()

def loadJointRadiusTool(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("Joint Radius Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsJointRadiusTool")

	MnsJointRadiusToolWin = MnsJointRadiusTool()
	MnsJointRadiusToolWin.loadWindow()
	if previousPosition: MnsJointRadiusToolWin.move(previousPosition)
	return MnsJointRadiusToolWin