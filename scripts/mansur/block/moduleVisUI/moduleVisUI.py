"""=== Author: Assaf Ben Zur ===
mnsModuleVisUI
A simple UI to control puppet's module animation controls visibility.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

import os, re
from os import listdir
from functools import partial
import maya.OpenMaya as OpenMaya

#mns dependencies
import mansur as mns
from ...core import log as mnsLog
from ...core import UIUtils as mnsUIUtils
from ...core import utility as mnsUtils
from ...core.globals import *
from ...gui import gui as mnsGui
from ..core import blockUtility as blkUtils

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
	from PySide6.QtWidgets import QFrame
else:
	from PySide2 import QtCore, QtWidgets, QtGui
	from PySide2.QtWidgets import QFrame

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "moduleVisUI.ui")
class MnsModuleVisUI(form_class, base_class):
	"""Main UI Class
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		#initialize UI
		super(MnsModuleVisUI, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsModuleVisUI") 
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		mnsLog.log("initializing MnsModuleVisUI", svr = 0)

		self.bodyLOHolder = self.bodyLayoutHolder_lo
		self.facialLOHolder = self.facialLayoutHolder_lo
		self.layoutHolders = [self.bodyLOHolder, self.facialLOHolder]
		
		#callbacks
		#self.puppetRootVisChaneCallbackID = None
		self.rigTopSubGrpVisCallbackID = None
		self.newSceneCallback = OpenMaya.MEventMessage.addEventCallback("NewSceneOpened", self.destroyAction)
		self.sceneOpenedCallback = OpenMaya.MEventMessage.addEventCallback("SceneOpened", self.destroyAction)

		self.puppetRoot = None
		self.rigTop = None
		self.rigTops = {}
		self.moduleAttrs = []
		self.btnDict = {}
		self.allBtnDict = {}
		self.layoutByAttrs = {}

		self.mainTab_twg.setCurrentIndex(0)

		self.initializeUI()
		self.connectSignals()
		self.installEventFilter(self)
		mnsGui.setGuiStyle(self, "Control Visibility UI")
		self.setRigTop()

	def connectSignals(self):
		"""Connect all UI signals
		"""

		self.globAll_btn.released.connect(self.setGlobAllTrigger)
		self.globPrimaries_btn.released.connect(self.setGlobPrimariesTrigger)
		self.globSecondaries_btn.released.connect(self.setGlobSecondariesTrigger)
		self.globTertiaries_btn.released.connect(self.setGlobTertiariesTrigger)
		self.rigName_cb.currentIndexChanged.connect(self.setRigTop)
		self.rSide_btn.toggled.connect(self.filterRows)
		self.cSide_btn.toggled.connect(self.filterRows)
		self.lSide_btn.toggled.connect(self.filterRows)
		self.filter_le.textChanged.connect(self.filterRows)
		self.filterClear_btn.released.connect(self.filter_le.clear)
		self.refresh_btn.released.connect(self.refresh)

	def initializeUI(self):
		self.clearLocalVars()
		self.rigTops = {}
		self.rigName_cb.clear()
		
		self.rigTops = blkUtils.getRigTopAssemblies()
		if self.rigTops: self.rigName_cb.addItems(self.rigTops.keys())

	def getAttrsFromPuppetRoot(self):
		if self.puppetRoot:
			preSortAttrs = {}
			moduleAttrs = [attr for attr in self.puppetRoot.node.listAttr(ud = True, u = True) if attr.type() == "enum" and "_" in attr.attrName()]
			
			for modAttr in moduleAttrs:
				side, name, alpha = modAttr.attrName().split("_")
				preSortAttrs[name + side + alpha] = modAttr
			self.moduleAttrs = [preSortAttrs[attr] for attr in sorted(preSortAttrs.keys())]

	def updateRigTopUIState(self):
		if self.rigTop:
			rigTopAttrs = [self.rigTop.node.visibility] + self.rigTop.node.listAttr(ud = True, v = True, se = True, k = True)
			for attr in rigTopAttrs:
				attrType = attr.type()
				if attr in self.rigTopGrpBoxes.keys():
					if self.rigTopGrpBoxes[attr]:
						grpBox = self.rigTopGrpBoxes[attr]
						btnChildren = grpBox.findChildren(QtWidgets.QPushButton)
						if attrType == "enum":
							visBtn, typeBtn = None, None
							for btn in btnChildren:
								if "_visBtn" in btn.objectName(): visBtn = btn
								elif "_typeBtn" in btn.objectName(): typeBtn = btn
							if visBtn and typeBtn:
								self.setRigTopBtnState(visBtn, typeBtn, attr, 0, True)
						elif attrType == "bool":
							if btnChildren:
								self.setRigTopBoolAttrState(btnChildren[0], attr, True)

	def setRigTopBtnState(self, visBtn, typeBtn, attr, btnType = 0, setCurrentState = False):
		if not setCurrentState:
			if btnType == 0:
				if visBtn.text() == "":visBtn.setText("V")
				else: visBtn.setText("")
			else:
				if typeBtn.text() == "": typeBtn.setText("T")
				elif typeBtn.text() == "T": typeBtn.setText("R")
				else: typeBtn.setText("")

			if visBtn.text() == "V":
				if typeBtn.text() == "": attr.set(1)
				elif typeBtn.text() == "T": attr.set(2)
				elif typeBtn.text() == "R": attr.set(3)
			else:
				attr.set(0)
		else:
			attrState = attr.get()
			if attrState == 0: 
				visBtn.setText("")
				typeBtn.setText("")
			elif attrState == 1:
				visBtn.setText("V")
				typeBtn.setText("")
			elif attrState == 2:
				visBtn.setText("V")
				typeBtn.setText("T")
			elif attrState == 3:
				visBtn.setText("V")
				typeBtn.setText("R")

	def setRigTopBoolAttrState(self, btn, attr, setCurrentState = False):
		if not setCurrentState:
			if btn.text() == "": btn.setText("V")
			else: btn.setText("")

			if btn.text() == "V": attr.set(1)
			else: attr.set(0)
		else:
			attrState = attr.get()
			if attrState == 0: btn.setText("")
			else: btn.setText("V")

	def drawRigTopBoolRow(self, attr):
		if attr:
			grpBox = QtWidgets.QGroupBox()
			HLayout = QtWidgets.QHBoxLayout()
			HLayout.setAlignment(QtCore.Qt.AlignLeft)
			HLayout.setContentsMargins(2, 2, 2, 2)
			grpBox.setLayout(HLayout)
			grpBox.setFixedHeight(35)

			attrState = attr.get()

			visBtn = QtWidgets.QPushButton()
			visBtn.setFixedSize(22,22)
			visBtn.setStyleSheet("QPushButton{\nbackground-color:#2a2a2a;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#1d1d1d;}\nQPushButton:pressed{background-color:#2a2a2a;}")
			HLayout.addWidget(visBtn)
			
			typeBtn = QtWidgets.QLabel()
			typeBtn.setFixedSize(22,22)
			HLayout.addWidget(typeBtn)

			visBtn.released.connect(partial(self.setRigTopBoolAttrState, visBtn, attr))
			self.setRigTopBoolAttrState(visBtn, attr, True)

			labelText = ""
			for capSplit in re.findall('[A-Z][^A-Z]*', re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), pm.attributeName(attr, l = True), 1)):
				labelText += " " + capSplit.capitalize()

			vLine = QFrame()
			vLine.setGeometry(QtCore.QRect(320, 150, 118, 3))
			vLine.setFrameShape(QFrame.VLine)
			vLine.setFrameShadow(QFrame.Sunken)
			HLayout.addWidget(vLine)

			label = QtWidgets.QLabel(labelText)
			label.setFixedSize(100,20)
			boldFont=QtGui.QFont()
			boldFont.setBold(True)
			label.setFont(boldFont)
			HLayout.addWidget(label)

			self.rigTopHolder_lo.addWidget(grpBox)
			self.rigTopGrpBoxes.update({attr: grpBox})

	def drawRigTopEnumRow(self, attr):
		if attr:
			grpBox = QtWidgets.QGroupBox()
			HLayout = QtWidgets.QHBoxLayout()
			HLayout.setAlignment(QtCore.Qt.AlignLeft)
			HLayout.setContentsMargins(2, 2, 2, 2)
			grpBox.setLayout(HLayout)
			grpBox.setFixedHeight(35)

			attrState = attr.get()

			visBtn = QtWidgets.QPushButton()
			visBtn.setObjectName(attr.attrName() + "_visBtn")
			visBtn.setFixedSize(22,22)
			visBtn.setStyleSheet("QPushButton{\nbackground-color:#2a2a2a;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#1d1d1d;}\nQPushButton:pressed{background-color:#2a2a2a;}")
			HLayout.addWidget(visBtn)
			
			typeBtn = QtWidgets.QPushButton()
			typeBtn.setObjectName(attr.attrName() + "_typeBtn")
			typeBtn.setFixedSize(22,22)
			typeBtn.setStyleSheet("QPushButton{\nbackground-color:#2a2a2a;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#1d1d1d;}\nQPushButton:pressed{background-color:#2a2a2a;}")
			HLayout.addWidget(typeBtn)
			if attr.attrName() == "puppetGrpVis":
				typeBtn.setEnabled(False)
				typeBtn.setStyleSheet("QPushButton{\nbackground-color:grey;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}")

			visBtn.released.connect(partial(self.setRigTopBtnState, visBtn, typeBtn, attr, 0))
			typeBtn.released.connect(partial(self.setRigTopBtnState, visBtn, typeBtn, attr, 1))
			self.setRigTopBtnState(visBtn, typeBtn, attr, 0, True)

			labelText = ""
			for capSplit in re.findall('[A-Z][^A-Z]*', re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), attr.attrName().split("Grp")[0], 1)):
				labelText += " " + capSplit.capitalize()

			vLine = QFrame()
			vLine.setGeometry(QtCore.QRect(320, 150, 118, 3))
			vLine.setFrameShape(QFrame.VLine)
			vLine.setFrameShadow(QFrame.Sunken)
			HLayout.addWidget(vLine)

			label = QtWidgets.QLabel(labelText)
			label.setFixedSize(100,20)
			boldFont=QtGui.QFont()
			boldFont.setBold(True)
			label.setFont(boldFont)
			HLayout.addWidget(label)

			self.rigTopHolder_lo.addWidget(grpBox)
			self.rigTopGrpBoxes.update({attr: grpBox})

	def destroyRigTopTab(self):
		#remove all
		for i in reversed(range(self.rigTopHolder_lo.count())):
			layout_proxy = self.rigTopHolder_lo.itemAt(i)
			layout_item = self.rigTopHolder_lo.itemAt(i).widget()
			if type(layout_item) == QtWidgets.QGroupBox:
				if layout_item.layout():
					mnsUIUtils.deleteAllLayoutItems(layout_item.layout())
			self.rigTopHolder_lo.removeItem(layout_proxy)
			if type(layout_item) == QtWidgets.QGroupBox:
				layout_item.deleteLater()

	def initializeRigTopTab(self):
		self.destroyRigTopTab()

		if self.rigTop:
			spacer = QtWidgets.QSpacerItem(5, 10, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
			self.rigTopHolder_lo.addItem(spacer)

			rigTopAttrs = [self.rigTop.node.visibility] + self.rigTop.node.listAttr(ud = True, v = True, se = True, k = True)
			for attr in rigTopAttrs:
				attrType = attr.type()
				if attrType == "enum":
					self.drawRigTopEnumRow(attr)
				elif attrType == "bool":
					self.drawRigTopBoolRow(attr)

			spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			self.rigTopHolder_lo.addItem(spacer)

	def eventFilter(self, source, event):
		"""Override event filter to catch the close trigger to delete the callback
		"""

		if event.type() == QtCore.QEvent.Close:
			self.deleteCallBacks()

		return super(QtWidgets.QWidget, self).eventFilter(source, event)

	### draw ##################################
	def refresh(self):
		currentCombo = self.rigName_cb.currentText()
		self.initializeUI()
		try:
			self.rigName_cb.setCurrentText(currentCombo)
		except:
			pass

	def detarmineAttrType(self, attr):
		isFacial = False

		if attr:
			for outCon in attr.listConnections(s = False, d = True):
				if type(outCon) is pm.nodetypes.AnimCurveUU:
					for secOutCon in outCon.output.listConnections(s = False, d = True):
						rootGuideName = secOutCon.nodeName()
						if "_modu" in rootGuideName:
							rootGuideName = rootGuideName.replace("_modu", "_rCtrl")
							rootGuide = mnsUtils.checkIfObjExistsAndSet(rootGuideName)
							if rootGuide:
								status, isFacial = mnsUtils.validateAttrAndGet(rootGuide, "isFacial", False)
		return isFacial

	def clearLocalVars(self):
		self.destroyUI()
		self.puppetRoot = None
		self.rigTop = None
		self.moduleAttrs = []
		self.btnDict = {}
		self.allBtnDict = {}
		self.layoutByAttrs = {}
		self.rigTopGrpBoxes = {}
		#try: OpenMaya.MMessage.removeCallback(self.puppetRootVisChaneCallbackID)
		#except: pass
		try: OpenMaya.MMessage.removeCallback(self.rigTopSubGrpVisCallbackID)
		except: pass

	def destroyUI(self):
		for layoutHolder in self.layoutHolders:
			for i in reversed(range(layoutHolder.count())):
				layout_item = layoutHolder.itemAt(i)
				if layout_item.layout():
					mnsUIUtils.deleteAllLayoutItems(layout_item.layout())
				layoutHolder.removeItem(layout_item)

	def setRigTop(self):
		self.clearLocalVars()

		puppetName = self.rigName_cb.currentText()
		if puppetName in self.rigTops:
			self.rigTop = self.rigTops[puppetName]
			self.puppetRoot = blkUtils.getPuppetRootFromRigTop(self.rigTop)

		self.drawUI()

	def drawUI(self):
		#top padding spacer
		for layoutParent in self.layoutHolders:
			spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
			layoutParent.addItem(spacer)

		if self.puppetRoot:
			self.getAttrsFromPuppetRoot()
			if self.moduleAttrs:
				for attr in self.moduleAttrs:
					isFacial = self.detarmineAttrType(attr)
					layoutParent = self.bodyLOHolder
					if isFacial: layoutParent = self.facialLOHolder

					btnDict = self.drawModuleRow(attr, layoutParent)
					btnDict.update({"isFacial": isFacial})
					btnDict.update({"vis": True})
					self.btnDict[attr] = btnDict

				for layoutParent in self.layoutHolders:
					spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
					layoutParent.addItem(spacer)
			
			self.rigTopSubGrpVisCallbackID = OpenMaya.MNodeMessage.addAttributeChangedCallback(mnsUtils.getMObjectFromObjName(self.rigTop.node.nodeName()), rigTopSubGrpEnumChangedCB, {"modVisUIObj": self})
			#self.puppetRootVisChaneCallbackID = OpenMaya.MNodeMessage.addAttributeChangedCallback(mnsUtils.getMObjectFromObjName(self.puppetRoot.node.nodeName()), puppetRootVisChangedCB, {"modVisUIObj": self})

		for layoutParent in self.layoutHolders:
			spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
			layoutParent.addItem(spacer)

		self.setRowsVisBasedOnState()
		self.filterRows()
		self.initializeRigTopTab()

	def drawModuleRow(self, attr = None, layoutParent = None):
		if attr and layoutParent:
			side, name, alpha = attr.attrName().split("_")

			HLayout = QtWidgets.QHBoxLayout()

			label = QtWidgets.QLabel(side.upper())
			label.setFixedSize(30,20)
			HLayout.addWidget(label)

			label = QtWidgets.QLabel(name)
			label.setFixedSize(110,20)
			HLayout.addWidget(label)

			label = QtWidgets.QLabel(alpha)
			label.setFixedSize(30,20)
			HLayout.addWidget(label)

			allBtn = QtWidgets.QPushButton("All")
			allBtn.setFixedSize(30,23)
			HLayout.addWidget(allBtn)
			allBtn.released.connect(partial(self.toggleAllStateForRow, attr))
			allBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}\nQPushButton:checked{background-color:#1d1d1d;}")

			returnDict = {"All": allBtn}
			for layer in ["Primaries", "Secondaries", "Tertiaries"]:
				btn = QtWidgets.QPushButton(layer[0].upper())
				btn.setCheckable(True)
				btn.setFixedSize(30,23)
				HLayout.addWidget(btn)
				returnDict[layer] = btn
				btn.toggled.connect(partial(self.changeModuleVisState, attr))
				btn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}\nQPushButton:checked{background-color:#1d1d1d;}")

			layoutParent.addLayout(HLayout)
			self.layoutByAttrs[attr] = HLayout

			return returnDict

	### triggers ##################################
		
	def setRowVisBasedOnState(self, attrKey):
		btnStates = [False, False, False]

		if attrKey in self.btnDict:
			btnDict = self.btnDict[attrKey]
			attrState = attrKey.get()

			if attrState == 1: btnStates = [True, False, False]
			elif attrState == 2: btnStates = [True, True, False]
			elif attrState == 3: btnStates = [True, True, True]
			elif attrState == 4: btnStates = [False, True, False]
			elif attrState == 5: btnStates = [False, False, True]
			elif attrState == 6: btnStates = [False, True, True]
			elif attrState == 7: btnStates = [True, False, True]

			for k,btnKey in enumerate(["Primaries", "Secondaries", "Tertiaries"]):
				btnDict[btnKey].blockSignals(True)
				btnDict[btnKey].setChecked(btnStates[k])
				btnDict[btnKey].blockSignals(False)

		from ...core.globals import GLOB_mnsPickerInstances
		for pickerInstanceName in GLOB_mnsPickerInstances.keys():
			pickerInstance = GLOB_mnsPickerInstances[pickerInstanceName]
			if pickerInstance:
				if pickerInstance.rigTop.node == self.rigTop.node:
					pickerInstance.setBtnVisStateBasedOnPupetRootAttr(attrKey)

		return btnStates

	def setRowsVisBasedOnState(self):
		if self.btnDict:
			for attrKey in self.btnDict:
				btnStates = self.setRowVisBasedOnState(attrKey)

	def changeModuleVisState(self, attr, dummy):
		if attr in self.btnDict:
			btnsState = [False, False, False]

			for key in self.btnDict[attr]:
				btn = self.btnDict[attr][key]
				if key == "Primaries":
					if btn.isChecked(): btnsState[0] = True
				elif key == "Secondaries":
					if btn.isChecked(): btnsState[1] = True
				elif key == "Tertiaries":
					if btn.isChecked(): btnsState[2] = True

			if btnsState == [False, False, False]: attr.set(0)		
			if btnsState == [True, False, False]: attr.set(1)
			elif btnsState == [True, True, False]: attr.set(2)
			elif btnsState == [True, True, True]: attr.set(3)
			elif btnsState == [False, True, False]: attr.set(4)
			elif btnsState == [False, False, True]: attr.set(5)
			elif btnsState == [False, True, True]: attr.set(6)
			elif btnsState == [True, False, True]: attr.set(7)

			self.setRowVisBasedOnState(attr)

	def toggleAllStateForRow(self, attr):
		if attr in self.btnDict:
			btnsState = [False, False, False]

			for key in self.btnDict[attr]:
				btn = self.btnDict[attr][key]
				if key == "Primaries":
					if btn.isChecked(): btnsState[0] = True
				elif key == "Secondaries":
					if btn.isChecked(): btnsState[1] = True
				elif key == "Tertiaries":
					if btn.isChecked(): btnsState[2] = True

			if all(btnsState): attr.set(0)
			elif any(btnsState) or not all(btnsState): attr.set(3)

			self.setRowVisBasedOnState(attr)

	def getUITabState(self):
		isFacial = False
		if self.mainTab_twg.currentIndex() == 1: isFacial = True
		return isFacial

	def setGlobAllTrigger(self):
		isFacial = self.getUITabState()

		attrSet = 0
		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:
					if not attr.get():
						attrSet = 3
						break

		for attr in self.moduleAttrs: 
			if self.btnDict[attr]["isFacial"] == isFacial: 
				if self.btnDict[attr]["vis"]:
					attr.set(attrSet)

		self.setRowsVisBasedOnState()

	def setGlobPrimariesTrigger(self):
		isFacial = self.getUITabState()

		attrSet = False
		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:
					if not (attr.get() == 1 or \
							attr.get() == 2 or \
							attr.get() == 3 or \
							attr.get() == 7):
						attrSet = True
						break

		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:

					btnStates = [False, False, False]

					attrState = attr.get()
					if attrState == 1: btnStates = [True, False, False]
					elif attrState == 2: btnStates = [True, True, False]
					elif attrState == 3: btnStates = [True, True, True]
					elif attrState == 4: btnStates = [False, True, False]
					elif attrState == 5: btnStates = [False, False, True]
					elif attrState == 6: btnStates = [False, True, True]
					elif attrState == 7: btnStates = [True, False, True]

					btnStates[0] = attrSet
					if btnStates == [False, False, False]: attr.set(0)		
					if btnStates == [True, False, False]: attr.set(1)
					elif btnStates == [True, True, False]: attr.set(2)
					elif btnStates == [True, True, True]: attr.set(3)
					elif btnStates == [False, True, False]: attr.set(4)
					elif btnStates == [False, False, True]: attr.set(5)
					elif btnStates == [False, True, True]: attr.set(6)
					elif btnStates == [True, False, True]: attr.set(7)

		self.setRowsVisBasedOnState()

	def setGlobSecondariesTrigger(self):
		isFacial = self.getUITabState()

		attrSet = False
		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:
					if not (attr.get() == 2 or \
							attr.get() == 3 or \
							attr.get() == 4 or \
							attr.get() == 6):
						attrSet = True
						break

		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:
					btnStates = [False, False, False]

					attrState = attr.get()
					if attrState == 1: btnStates = [True, False, False]
					elif attrState == 2: btnStates = [True, True, False]
					elif attrState == 3: btnStates = [True, True, True]
					elif attrState == 4: btnStates = [False, True, False]
					elif attrState == 5: btnStates = [False, False, True]
					elif attrState == 6: btnStates = [False, True, True]
					elif attrState == 7: btnStates = [True, False, True]

					btnStates[1] = attrSet
					if btnStates == [False, False, False]: attr.set(0)		
					if btnStates == [True, False, False]: attr.set(1)
					elif btnStates == [True, True, False]: attr.set(2)
					elif btnStates == [True, True, True]: attr.set(3)
					elif btnStates == [False, True, False]: attr.set(4)
					elif btnStates == [False, False, True]: attr.set(5)
					elif btnStates == [False, True, True]: attr.set(6)
					elif btnStates == [True, False, True]: attr.set(7)

		self.setRowsVisBasedOnState()

	def setGlobTertiariesTrigger(self):
		isFacial = self.getUITabState()

		attrSet = False
		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:
					if not (attr.get() == 3 or \
							attr.get() == 5 or \
							attr.get() == 6 or \
							attr.get() == 7):
						attrSet = True
						break

		for attr in self.moduleAttrs:
			if self.btnDict[attr]["isFacial"] == isFacial:
				if self.btnDict[attr]["vis"]:
					btnStates = [False, False, False]

					attrState = attr.get()
					if attrState == 1: btnStates = [True, False, False]
					elif attrState == 2: btnStates = [True, True, False]
					elif attrState == 3: btnStates = [True, True, True]
					elif attrState == 4: btnStates = [False, True, False]
					elif attrState == 5: btnStates = [False, False, True]
					elif attrState == 6: btnStates = [False, True, True]
					elif attrState == 7: btnStates = [True, False, True]

					btnStates[2] = attrSet
					if btnStates == [False, False, False]: attr.set(0)		
					if btnStates == [True, False, False]: attr.set(1)
					elif btnStates == [True, True, False]: attr.set(2)
					elif btnStates == [True, True, True]: attr.set(3)
					elif btnStates == [False, True, False]: attr.set(4)
					elif btnStates == [False, False, True]: attr.set(5)
					elif btnStates == [False, True, True]: attr.set(6)
					elif btnStates == [True, False, True]: attr.set(7)

		self.setRowsVisBasedOnState()

	def filterRows(self):
		sides = ""
		if self.rSide_btn.isChecked(): sides += "r"
		if self.cSide_btn.isChecked(): sides += "c"
		if self.lSide_btn.isChecked(): sides += "l"
		filterText = self.filter_le.text()

		for attr in self.layoutByAttrs.keys():
			visState = True
			side, name, alpha = attr.attrName().split("_")

			if not side in sides: visState = False
			if visState:
				if not filterText in name.lower():  
					visState = False

			layout = self.layoutByAttrs[attr]
			for i in reversed(range(layout.count())): 
				layout.itemAt(i).widget().setHidden(not visState)

			self.btnDict[attr]["vis"] = visState

	def deleteCallBacks(self):
		#try: OpenMaya.MMessage.removeCallback(self.puppetRootVisChaneCallbackID)
		#except: pass

		try: OpenMaya.MMessage.removeCallback(self.rigTopSubGrpVisCallbackID)
		except: pass

		try: OpenMaya.MMessage.removeCallback(self.newSceneCallback)
		except: pass

		try: OpenMaya.MMessage.removeCallback(self.sceneOpenedCallback)
		except: pass

	def destroyAction(self, dummy = None):
		self.deleteCallBacks()
		self.destroy()

	### load Win ##################################

	def loadWindow(self):
		"""Main UI load
		"""
		self.show()

def loadModuleVisUI(): 
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsModuleVisUI")

	mnsModuleVisWin = MnsModuleVisUI()
	mnsModuleVisWin.loadWindow()
	if previousPosition: mnsModuleVisWin.move(previousPosition)
	return mnsModuleVisWin

def rigTopSubGrpEnumChangedCB(msg, plug, otherPlug, clientData, **kwargs):
	modVisUIObj = clientData["modVisUIObj"]
	modVisUIObj.updateRigTopUIState()