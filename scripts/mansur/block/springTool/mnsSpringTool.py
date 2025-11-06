"""=== Author: Assaf Ben Zur ===
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
from pymel.core import datatypes as pmDt
import os

if int(cmds.about(version = True)) > 2024:
	import shiboken6 as shiboken2
else:
	import shiboken2
	
import maya.OpenMayaUI as apiUI

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import arguments as mnsArgs
from ...core import nodes as mnsNodes
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ..core import buildModules as mnsBuildModules
from ..core import controlShapes as blkCtrlShps
from ..core import blockUtility as blkUtils
from ...core.globals import *
from ...gui import gui as mnsGui
from maya import cmds
import maya.OpenMaya as OpenMaya

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
	from PySide6.QtWidgets import QTreeWidgetItem
else:
	from PySide2 import QtCore, QtWidgets, QtGui
	from PySide2.QtWidgets import QTreeWidgetItem

class MnsGradientWidget(QtWidgets.QWidget):
	def __init__(self, parent = None):
		super(MnsGradientWidget, self).__init__(parent)
		self.installEventFilter(self)
		self.initialized = False
		self.currentSpringNodes = {}
		self.refSpringNode = None
		self.attrName = ""
		self.origValues = []

	def gatherCurrentValues(self):
		valuesRet = []
		for k in range(self.refSpringNode.attr(self.attrName).numElements()):
			attr = self.refSpringNode.attr(self.attrName +"[" + str(k) + "]")
			valuesRet.append(attr.get())
		return  valuesRet

	def paintEvent(self, event):
		if self.initialized:
			if not self.origValues:
				self.origValues = self.gatherCurrentValues()
				
			if self.gatherCurrentValues() != self.origValues:
				#update all current spring nodes
				numElements = self.refSpringNode.attr(self.attrName).numElements()

				if len(self.currentSpringNodes) > 1:
					for sn in self.currentSpringNodes:
						sn.attr(self.attrName).setNumElements(numElements)
						if sn != self.refSpringNode:
							rangeMax = max(sn.attr(self.attrName).numElements(), numElements)
							for k in range(rangeMax-1, -1, -1):
								if k >= numElements:
									fullAttrName = sn.nodeName() + "." + self.attrName +"[" + str(k) + "]"
									pm.removeMultiInstance(fullAttrName, b = True)
								else:
									for attrChildName in ["Position", "FloatValue", "Interp"]:
										fullAttrName = self.attrName +"[" + str(k) + "]." + self.attrName + "_" + attrChildName
										sn.attr(fullAttrName).set(self.refSpringNode.attr(fullAttrName).get())
		else:
			self.initialized = True

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsSpringTool.ui")
class MnsSpringTool(form_class, base_class):
	"""Spring Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsSpringTool, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsSpringTool") 
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		#init UI
		self.springNodes_trv.setColumnHidden(4, True)

		# locals
		self.rigTops = {}
		self.rigTop = None
		self.puppetRoot = None
		self.namespace = ""
		self.springNodes = {}
		self.springNodesByIndex = {}
		self.currentSpringNodes = {}
		self.drawType = ""
		self.stifGradCtrl = None
		self.dampingGradCtrl = None

		#UI layout
		self.springNodes_trv.setColumnWidth(0, 50)

		#methods
		mnsGui.setGuiStyle(self, "Spring Tool")
		self.initializeData()	
		self.setRigTop()
		self.connectSignals()
		self.filterView()


	##################	
	###### INIT ######
	##################

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.rigName_cb.currentIndexChanged.connect(self.setRigTop)
		self.springNodes_trv.itemSelectionChanged.connect(self.setSpringNode)
		self.autoSym_cbx.toggled.connect(self.setSpringNode)
		self.left_cb.toggled.connect(self.filterView)
		self.center_cb.toggled.connect(self.filterView)
		self.right_cb.toggled.connect(self.filterView)
		self.crvSpring_cbx.toggled.connect(self.filterView)
		self.tsSpring_cb.toggled.connect(self.filterView)

	def initializeData(self):
		#init rigTops
		self.rigTops = blkUtils.getRigTopAssemblies()
		if self.rigTops: self.rigName_cb.addItems(self.rigTops.keys())
		self.collectSpringNodes()

	def initializeSprings(self):
		if self.rigTop and self.puppetRoot:
			#get all spring curve nodes, and all transform spring nodes
			springCurveNodes = []
			allCrvSprings = pm.ls("*_" + mnsPS_springCurve)
			

			for springNode in allCrvSprings + allTransformSprings:
				strengthAttrInputs = springNode.strength.listConnections(d = False, s = True)
				for inp in strengthAttrInputs:
					rigTop = blkUtils.getRigTop(inp)
					if rigTop and rigTop.node == self.rigTop.node:
						springCurveNodes.append(springNode)
					break

	def collectSpringNodes(self):
		self.springNodes = {}
		self.springNodesByIndex = {}

		#reformat rigTopsCollection temporarily
		rigTopNodes = {}
		for rt in self.rigTops.keys():
			rigTopNodes.update({self.rigTops[rt].node: rt})
		
		#collect in a new formated dict
		allCrvSprings = pm.ls("*_" + mnsPS_springCurve, r = True)
		allTransformSprings = pm.ls("*_" + mnsPS_ts, r = True)

		if allCrvSprings or allTransformSprings:
			for i, springNode in enumerate((allCrvSprings + allTransformSprings)):
				strengthAttrInputs = springNode.strength.listConnections(d = False, s = True)
				for inp in strengthAttrInputs:
					rigTop = blkUtils.getRigTop(inp)
					if rigTop and rigTop.node in rigTopNodes:
						self.springNodes.update({springNode: 
														{
														"rigToAssemblyName": rigTopNodes[rigTop.node],
														"rigTopNode": rigTop.node,
														"type": mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, springNode.split("_")[-1]),
														"moduleRoot": blkUtils.getModuleRoot(inp),
														"id": i,
														"inputCtrl": inp,
														"widgetItem": None
														}})
						self.springNodesByIndex.update({i: springNode})
					break

	##################	
	###### View ######
	##################

	def filterView(self):
		for childIdx in range(self.springNodes_trv.invisibleRootItem().childCount()):
			childItem = self.springNodes_trv.invisibleRootItem().child(childIdx)
			side = childItem.text(0)
			nodeType = childItem.text(3)

			visible = True
			if side == "l" and not self.left_cb.isChecked(): visible = False 
			elif side == "c" and not self.center_cb.isChecked(): visible = False 
			elif side == "r" and not self.right_cb.isChecked(): visible = False 

			if visible:
				if nodeType == "Transform-Spring" and not self.tsSpring_cb.isChecked(): visible = False 
				elif nodeType == "Curve-Spring" and not self.crvSpring_cbx.isChecked(): visible = False 

			childItem.setHidden(not visible)

	##################	
	####### UI #######
	##################

	def setValueTrigger(self, attr, value):
		attr.set(value)
	
	def drawCommonAttrsToUi(self):
		if self.currentSpringNodes:
			#strength
			strengthLbl = QtWidgets.QLabel("Stregth")
			strengthLbl.setFixedWidth(150)

			self.dynamicDraw_lo.addWidget(strengthLbl, 0, 0)
			strengthSB = QtWidgets.QDoubleSpinBox()
			strengthSB.setSingleStep(0.05)
			strengthSB.setValue(list(self.currentSpringNodes.keys())[0].strength.get())
			strengthSB.setMinimum(0.0)
			strengthSB.setMaximum(1.0)
			strengthSB.setFixedWidth(50)
			self.dynamicDraw_lo.addWidget(strengthSB, 0, 1)

			spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
			self.dynamicDraw_lo.addItem(spacer, 0, 2)

			#stratFrame
			startFrameLbl = QtWidgets.QLabel("Start-Frame")
			self.dynamicDraw_lo.addWidget(startFrameLbl, 1, 0)
			startFrameSB = QtWidgets.QSpinBox()
			startFrameSB.setMinimum(-10000)
			startFrameSB.setMaximum(10000)
			startFrameSB.setFixedWidth(50)
			startFrameSB.setValue(list(self.currentSpringNodes.keys())[0].startFrame.get())
			self.dynamicDraw_lo.addWidget(startFrameSB, 1, 1)
			
			for csn in self.currentSpringNodes.keys():
				ctrl = self.currentSpringNodes[csn]["inputCtrl"]
				strengthSB.valueChanged.connect(partial(self.setValueTrigger, ctrl.strength))
				startFrameSB.valueChanged.connect(partial(self.setValueTrigger, ctrl.startFrame))

	def drawTransformSpringNodeToUI(self):
		if self.currentSpringNodes:
			stiffnessLbl = QtWidgets.QLabel("Stiffness")
			self.dynamicDraw_lo.addWidget(stiffnessLbl, 2, 0)
			stiffnessSB = QtWidgets.QDoubleSpinBox()
			stiffnessSB.setSingleStep(0.05)
			stiffnessSB.setValue(list(self.currentSpringNodes.keys())[0].stiffness.get())
			stiffnessSB.setMinimum(0.0)
			stiffnessSB.setMaximum(1.0)
			self.dynamicDraw_lo.addWidget(stiffnessSB, 2, 1)

			dampingLbl = QtWidgets.QLabel("Damping")
			self.dynamicDraw_lo.addWidget(dampingLbl, 3, 0)
			dampingSB = QtWidgets.QDoubleSpinBox()
			dampingSB.setSingleStep(0.05)
			dampingSB.setValue(list(self.currentSpringNodes.keys())[0].damping.get())
			dampingSB.setMinimum(0.0)
			dampingSB.setMaximum(1.0)
			self.dynamicDraw_lo.addWidget(dampingSB, 3, 1)
			
			for csn in self.currentSpringNodes.keys():
				ctrl = self.currentSpringNodes[csn]["inputCtrl"]
				stiffnessSB.valueChanged.connect(partial(self.setValueTrigger, ctrl.stiffness))
				dampingSB.valueChanged.connect(partial(self.setValueTrigger, ctrl.damping))

	def getGradientControl(self, attr = None):
		self.dynamicDraw_lo.setObjectName("mainLayout")
		
		#cmds layout pointer
		layout = apiUI.MQtUtil.fullName(int(shiboken2.getCppPointer(self.verticalLayout)[0]))
		pm.setParent(layout)

		# new pane layout and pointer
		paneLayoutName = pm.paneLayout()
		ptr = apiUI.MQtUtil.findControl(paneLayoutName)
		
		# Wrap the pointer into a python QObject
		paneLayout = shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)

		# create the gradient control and wrap it to QT widget
		gradientControl = pm.gradientControl(at = attr, w = 130)
		return paneLayout, gradientControl

	def drawCurveSpringNodeToUI(self):
		if self.currentSpringNodes:
			refSpringNode = list(self.currentSpringNodes.keys())[0]

			row = 0
			col = 0
			for k, attrName in enumerate(["Stiffness", "Damping"]):
				lbl = QtWidgets.QLabel("   " + attrName)
				lbl.setFixedHeight(19)
				lbl.setStyleSheet("background-color: rgb(90, 90, 90)")
				self.dynamicDraw_lo.addWidget(lbl, 2 + row + k, col, 1, 3)
				row += 1

				groupBox = QtWidgets.QGroupBox()
				groupBox.setStyleSheet("QGroupBox{\nborder: 1px ; \npadding: 0px 0px 0px 0px;\nborder-style: solid;\nborder-color: #292929;\nborder-radius: 4px;\n}\n\nQGroupBox::title {\n    subcontrol-origin:  margin;\n	subcontrol-position: top left; \n   padding: 0 12px 0 12px;\n}")
				contentLayout = QtWidgets.QGridLayout()
				contentLayout.setContentsMargins(6, 6, 6, 6)
				contentLayout.setSpacing(6)
				groupBox.setLayout(contentLayout)
				self.dynamicDraw_lo.addWidget(groupBox, 3 + row + k, 0, 1, 3)

				contentLayout.setObjectName("mainLayout" + attrName)
				layout = apiUI.MQtUtil.fullName(int(shiboken2.getCppPointer(contentLayout)[0]))
				pm.setParent(layout)
				

				selPosPtr = pm.attrFieldSliderGrp(attrName + "_pos", l = "Selected Position", precision = 2, cl2 = ("left", "left"), w = 50)
				selectedPosSB = mnsUIUtils.toQtObject(selPosPtr, objectTypeTarget = QtWidgets.QWidget)
				contentLayout.addWidget(selectedPosSB, row, col)
				row += 1

				pm.setParent(layout)
				selValPtr = pm.attrFieldSliderGrp(attrName + "_val", l = "Selected Value", precision = 2, cl2 = ("left", "left"))
				selectedValueSB = mnsUIUtils.toQtObject(selValPtr, objectTypeTarget = QtWidgets.QWidget)
				contentLayout.addWidget(selectedValueSB, row, col)
				row += 1

				pm.setParent(layout)
				interpPtr = pm.attrEnumOptionMenuGrp(attrName + "_interp", l = "Interpolation", cl2 = ("left", "left"), ei = [(0, "None"), (1, "Linear"), (2, "Smooth"), (3, "Spline")])
				interpCB = mnsUIUtils.toQtObject(interpPtr, objectTypeTarget = QtWidgets.QWidget)
				contentLayout.addWidget(interpCB, row, col)
				col += 1
				row -= 2

				gradCtrl, gradCtrlMayaObj = self.getGradientControl(attr = refSpringNode.nodeName() + "." + attrName.lower())
				pm.gradientControl(gradCtrlMayaObj, e = True, spc = selPosPtr, scc = selValPtr, sic = interpPtr)
				contentLayout.addWidget(gradCtrl, row, col, 4, 1)
				gradCtrlWG = mnsUIUtils.toQtObject(gradCtrlMayaObj, objectTypeTarget = QtWidgets.QWidget)
				gradCtrlWG = MnsGradientWidget(gradCtrlWG)
				gradCtrlWG.currentSpringNodes = self.currentSpringNodes
				gradCtrlWG.refSpringNode = refSpringNode
				gradCtrlWG.attrName = attrName.lower()

				row = 5
				col = 0

	def getCurrentSpringNodes(self):
		self.currentSpringNodes = {}
		self.drawType = ""

		for childIdx in range(self.springNodes_trv.invisibleRootItem().childCount()):
			childItem = self.springNodes_trv.invisibleRootItem().child(childIdx)
			for i in range(4):
				childItem.setForeground(i, QtGui.QColor('lightgray'))

		currentItems = self.springNodes_trv.selectedItems()
		if currentItems:
			for currentItem in currentItems:
				index = int(currentItem.text(4))
				if index in self.springNodesByIndex.keys():
					springNode = self.springNodesByIndex[index]
					springNodeData = self.springNodes[springNode]
					self.currentSpringNodes.update({springNode: springNodeData})
					if not self.drawType == "multi":
						if not self.drawType:
							self.drawType = springNodeData["type"]
						elif self.drawType != springNodeData["type"]:
							self.drawType = "multi"

					#auto symmetry
					if self.autoSym_cbx.isChecked():
						symSpringNode = blkUtils.getOppositeSideControl(springNode)
						if symSpringNode:
							symSpringNode = symSpringNode.node
							if not symSpringNode in self.currentSpringNodes and symSpringNode in self.springNodes.keys():
								symSpringNodeData = self.springNodes[symSpringNode]
								self.currentSpringNodes.update({symSpringNode: symSpringNodeData})
								
								symItem = symSpringNodeData["widgetItem"]
								for i in range(4):
									symItem.setForeground(i, QtGui.QColor('lightgreen'))
				
	def setSpringNode(self):
		#destrpoy UI
		mnsUIUtils.deleteAllLayoutItems(self.dynamicDraw_lo)
		self.stifGradCtrl = None
		self.dampingGradCtrl = None

		self.getCurrentSpringNodes()
		if self.currentSpringNodes and self.drawType:
			self.drawCommonAttrsToUi()
			if self.drawType == "mnsSpringCurve":
				self.drawCurveSpringNodeToUI()
			elif self.drawType == "mnsTransformSpring":
				self.drawTransformSpringNodeToUI()

		#determine selection
		newSelection = []
		if self.currentSpringNodes:
			for spNode in self.currentSpringNodes.keys():
				newSelection.append(self.currentSpringNodes[spNode]["inputCtrl"])
		if newSelection:
			pm.select(newSelection, r = True)

	def initializeView(self):
		#destroyUI
		self.springNodes_trv.clear()

		#rebuild
		currentRig = self.rigName_cb.currentText()
		for springNode in self.springNodes.keys():
			if self.springNodes[springNode]["rigToAssemblyName"] == currentRig:
				rigTopAssembly = self.springNodes[springNode]["rigToAssemblyName"] 
				rigTopNode = self.springNodes[springNode]["rigTopNode"] 
				nodeType = self.springNodes[springNode]["type"] 
				moduleRoot = self.springNodes[springNode]["moduleRoot"] 
				index = self.springNodes[springNode]["id"] 
				displayType = "Transform-Spring"
				if nodeType == "mnsSpringCurve": displayType = "Curve-Spring"

				widItm = QTreeWidgetItem(self.springNodes_trv, [moduleRoot.side, moduleRoot.body, moduleRoot.alpha, displayType, str(index)])
				self.springNodes[springNode]["widgetItem"] = widItm

	def setRigTop(self):
		self.rigTop = None
		self.puppetRoot = None
		self.namespace = ""

		#init rig top
		currentRig = self.rigName_cb.currentText()
		if currentRig:
			if currentRig in self.rigTops.keys():
				self.rigTop = self.rigTops[self.rigName_cb.currentText()]
		
		#init puppet root
		#init namespace
		if self.rigTop: 
			self.puppetRoot = blkUtils.getPuppetRootFromRigTop(self.rigTop)
			self.namespace = self.rigTop.namespace
		self.initializeView()

	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsSpringTool", svr = 0)
		self.show()

def loadSpringTool(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	mnsLog.log("Spring Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsSpringTool")

	mnsSpringToolWin = MnsSpringTool()
	mnsSpringToolWin.loadWindow()
	if previousPosition: mnsSpringToolWin.move(previousPosition)
	return mnsSpringToolWin