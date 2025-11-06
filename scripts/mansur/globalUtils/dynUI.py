"""=== Author: Assaf Ben Zur ===
Supporting module for the 'defSearch' UI Class.
This module build the base UI for any function UI build called from the defSerach UI.
The build is based on a .ui base file, constructing an empty UI that will accomedate the dynamic UI elemnts requested.
This module also holds the RunCmd. The run command will filter and get any elemnt value based on it's type and recompile an argument string to pass into the function requested.
A template icon is created as well as an empty 'title' item to be changed after creation base on the function name requested."""

#global dependencies


from maya import cmds
import pymel.core as pm

import sys, os, inspect, json
from os.path import dirname, abspath     
from functools import partial

#mns dependencies
from ..core import arguments as mnsArgs
from ..core import string as mnsString
from ..core import log as mnsLog
from ..core import UIUtils as mnsUIUtils
from ..core import utility as mnsUtils
from ..block.core import blockUtility as blkUtils
from ..block.modulePresetEditor import modulePresetEditor as mnsModulePresetEditor
from ..core.UIUtils import CollapsibleFrameWidget
from ..core.prefixSuffix import *
from ..core.globals import *
from ..gui import gui as mnsGui
if GLOB_pyVer > 2: from importlib import reload

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore, QtWidgets
	from PySide6.QtWidgets import QTreeWidgetItem
else:
	from PySide2 import QtGui, QtCore, QtWidgets
	from PySide2.QtWidgets import QTreeWidgetItem

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "dynUI.ui")

class MnsDynamicDefUI(form_class, base_class):
	"""Main UI class
	"""

	def __init__(self, defenition, parent=mnsUIUtils.get_maya_window(), **kwargs):
		super(MnsDynamicDefUI, self).__init__(parent)
		self.setupUi( self )

		winTitle = kwargs.get("winTitle", "") #arg;
		if winTitle != "": self.setWindowTitle(winTitle)

		self.funObjectCreation = False
		if inspect.isfunction(defenition): self.funObjectCreation = True

		iconPath = kwargs.get("icon", GLOB_guiIconsDir + "/logo/dynUITitle.png")
		self.iconLbl.setPixmap(QtGui.QPixmap(iconPath))
		self.setWindowIcon(QtGui.QIcon(GLOB_guiIconsDir + "/logo/mansur_logo_noText.png"))
		self.factoryRest_btn.setHidden(True)
		self.presetEditor_btn.setHidden(True)

		self.closeOnApplyEnabled = kwargs.get("closeOnApplyEnabled", False) #arg;
		self.closeOnApply_cbx.setHidden(not self.closeOnApplyEnabled)
		mnsUtils.updateMansurPrefs()
		closeOnApplyDefault = mnsUtils.getMansurPrefs()["Global"]["closeSettingsWindowOnApply"]
		self.closeOnApply_cbx.setChecked(closeOnApplyDefault)

		self.readOnly = kwargs.get("readOnly", False) #arg;
		self.defenition = None 
		self.arguments = [] 
		self.optArguments = [] 
		self.txtFields = () 
		self.attrComponentPairing = {}
		self.defenitionName = ""
		self.title = ""
		self.preDefinedArgs = None
		self.sideCB = None
		self.colOverride = None
		self.rigTop = None
		self.split = None
		self.multiTypeEdit = kwargs.get("multiTypeEdit", False)
		self.batchEdit = kwargs.get("batchEdit", False)
		self.splitLayout = None
		self.dividerLayout = None
		self.allCollapsible = []
		self.widgetRelationships = {}
		self.rootGuide = ""
		self.modArgs = {}

		newModuleTab = QtWidgets.QWidget();
		horizontalLayout =  QtWidgets.QHBoxLayout(newModuleTab)
		horizontalLayout.setSpacing(2)
		horizontalLayout.setContentsMargins(0, 0, 0, 0)
		newScroll = QtWidgets.QScrollArea(newModuleTab)
		newScroll.setWidgetResizable(True)
		newScrollContent = QtWidgets.QWidget()
		horizontalLayout_2 = QtWidgets.QVBoxLayout(newScrollContent);
		horizontalLayout_2.setSpacing(2)
		horizontalLayout_2.setContentsMargins(2, 9, 2, 2)
		self.mainVLayout = QtWidgets.QVBoxLayout()
		self.mainVLayout.setSpacing(6)
		self.mainVLayout.setAlignment(QtCore.Qt.AlignLeft)
		self.mainVLayout.setAlignment(QtCore.Qt.AlignTop)
		horizontalLayout_2.addLayout(self.mainVLayout)
		newScroll.setWidget(newScrollContent)
		horizontalLayout.addWidget(newScroll)
		self.mainTabWidget.insertTab(0, newModuleTab, "Main")

		if self.funObjectCreation:
			module = sys.modules[defenition.__module__]
			reload(module)
			self.defenition = defenition 
			self.defenitionName = defenition.__name__
			self.title = '++MANSUR++defDynUI++ ' + self.defenitionName 
			self.arguments, self.optArguments = mnsArgs.extractArgsFromDef(defenition)
		else:
			self.rootGuide = kwargs.get("rootGuide", None)
			self.defenitionName = kwargs.get("title", "Settings") #arg;
			if pm.window(self.defenitionName, exists = True):
				try:
					pm.deleteUI(self.defenitionName)
				except:
					pass
			self.setObjectName(self.defenitionName)
			runButtonText = kwargs.get("btnText", "Create new rig top") #arg;
			self.runBtn.setText(runButtonText)

			self.optArguments = kwargs.get("customArgs", []) #arg;
			self.customRunCommand = kwargs.get("runCmd", None) #arg;
			self.preDefinedArgs = kwargs.get("preDefinedArgs", None) #arg;
			self.rigTop = kwargs.get("rigTop", None) #arg;
			self.split = kwargs.get("split", None) #arg;
			if not self.rigTop and self.preDefinedArgs: self.rigTop = self.preDefinedArgs.get("rigTop", None)
			if type(self.rigTop) is MnsNameStd: self.rigTop = self.rigTop.node

			if self.split: 
				firstTabTitle = kwargs.get("firstTabTitle", "Mandatory settings") #arg;
				secondTabTitle = kwargs.get("secondTabTitle", "module settings") #arg;
				
				if self.rootGuide and not self.batchEdit and not self.readOnly:
					self.factoryRest_btn.setHidden(False)
					self.factoryRest_btn.released.connect(self.resetToFactory)
					
				if not "Block Rig Top" in self.defenitionName and not self.multiTypeEdit and not self.readOnly:
					self.presetEditor_btn.setHidden(False)
					self.presetEditor_btn.released.connect(lambda: mnsModulePresetEditor.loadModulePresetEditor(self))
					
				self.mainTabWidget.setTabText(0, firstTabTitle)

				if not self.multiTypeEdit:
					self.splitLayout = mnsUIUtils.buildTabForModuleParentDir(secondTabTitle, 1, self.mainTabWidget, modSet = True)
					self.splitLayout.setAlignment(QtCore.Qt.AlignTop)


		self.fullList = self.arguments + self.optArguments
		if len(self.fullList) == 0:
			#self.scrollAreaA.takeWidget()
			self.resize(420,100)
		else:
			extraLines  = 0
			height = 200
			if self.split:
				allArgsHeight = 110
				modArgsHeight = 110

				allArgs = self.optArguments[0:self.split]
				modArgs = self.optArguments[self.split:]
				self.modArgs = modArgs

				for arg in allArgs:
					if "colorScheme".lower() in arg.name.lower(): extraLines += 7
					if "schemeOverride".lower() in arg.name.lower(): extraLines += 3
					if "channelControl".lower() in arg.name.lower(): extraLines += 4
				allArgsHeight = ((len(allArgs) + len(self.arguments) + extraLines)) * 30

				extraLines  = 0
				for arg in modArgs:
					if "colorScheme".lower() in arg.name.lower(): extraLines += 7
					if "schemeOverride".lower() in arg.name.lower(): extraLines += 3
					if "channelControl".lower() in arg.name.lower(): extraLines += 4
				modArgsHeight = (len(modArgs) + len(self.arguments) + extraLines) * 30
				height = max([allArgsHeight, modArgsHeight])
			else:
				for arg in self.optArguments:
					if "colorScheme".lower() in arg.name.lower(): extraLines += 7
					if "schemeOverride".lower() in arg.name.lower(): extraLines += 3
					if "channelControl".lower() in arg.name.lower(): extraLines += 4
				height = (len(self.optArguments) +  len(self.arguments) + extraLines) * 28

			height += 286
			if height > 820: height = 820
			self.resize(440,height)

		#self.mainVLayout.setAlignment(QtCore.Qt.AlignTop)
		self.drawUI()
		mnsUIUtils.fourKWindowAdjust(self)
		self.setCollapsibleWidgetsBehaviour()
		mnsGui.setGuiStyle(self, "Dynamic UI")

		if not self.readOnly:
			self.runBtn.released.connect(self.runCmd)
		else:
			self.runBtn.setEnabled(True)
			self.runBtn.setText("CLOSE WITHOUT CHANGES (READ-ONLY)")
			self.runBtn.setStyleSheet("color:#00ff00;font-weight:bold")
			self.runBtn.released.connect(partial(self.destroy, True, True))

	def keyPressEvent(self, event):
		if (event.modifiers() & QtCore.Qt.ShiftModifier):
			self.shift = True
			pass # make silent
				
	def closeEvent(self, event):
		if not self.funObjectCreation: self.destroy(True, True)

	def drawTitle(self):
		"""Title set method.
		"""

		title = self.defenitionName
		if self.readOnly: title += " (READ-ONLY)"

		self.titleLbl.setText(title)
		font = QtGui.QFont()
		font.setPointSize(9)
		font.setBold(True)
		self.titleLbl.setFont(font)
		
	def setCollapsibleWidgetsBehaviour(self):
		if not mnsUtils.getMansurPrefs()["Global"]["collapsibleWidgetBehavior"]:
			for colWid in self.allCollapsible:
				if colWid:
					QtCore.QObject.connect(colWid._title_frame, QtCore.SIGNAL('clicked()'), partial(self.toggleAllCollapsed, colWid))
		
	def toggleAllCollapsed(self, pressedColWid):
		if pressedColWid:
			for colWid in self.allCollapsible:
				if colWid:
					if not colWid is pressedColWid:
						if not colWid._is_collasped:
							colWid.toggleCollapsed()

	def resetToFactory(self):
		if self.rootGuide and self.rigTop:
			status, modPath = mnsUtils.validateAttrAndGet(self.rootGuide, "modPath", None)
			status, modType = mnsUtils.validateAttrAndGet(self.rootGuide, "modType", None)
			
			if modPath and os.path.isdir(modPath):
				allSettingsPath = (dirname(dirname(abspath(__file__))) + "/block/core/allModSettings.modSettings").replace("\\", "/")

				if os.path.isfile(allSettingsPath):
					globArgs = mnsUtils.readSetteingFromFile(allSettingsPath)
					globArgs = blkUtils.filterCreationOnlyFromArgs(globArgs)

					for arg in globArgs:
						if "schemeOverride".lower() in arg.name.lower():
							colScheme = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList("colorScheme", self.rigTop)
							arg.default = mnsUIUtils.getColorArrayFromColorScheme("c", colScheme)
						elif arg.name == "body":
							arg.default = self.rootGuide.body
						elif arg.name == "blkSide":
							side = "center"
							if self.rootGuide.side == "l": side = "left"
							elif self.rootGuide.side == "r": side = "right"
							arg.default = side
						elif arg.name == "alpha":
							arg.default = self.rootGuide.alpha

					settingsPath = os.path.join(modPath, modType + ".modSettings").replace("\\", "/")
					if os.path.isfile(settingsPath):
						split = len(globArgs)
						optArgs = mnsUtils.readSetteingFromFile(settingsPath)
						optArgs = blkUtils.filterCreationOnlyFromArgs(optArgs)

						toRemove = []
						for arg in optArgs:
							for argA in globArgs:
								if arg.name == argA.name:
									arg.comment = argA.comment
									globArgs[globArgs.index(argA)] = arg
									toRemove.append(arg)
						for arg in toRemove: optArgs.remove(arg)

						optArgs = globArgs + optArgs

						self.fullList = optArgs
						self.destroyUI()
						self.drawUI()
			else:
				mnsLog.log("Couldn't find module path, aborting.", svr = 2)
		else:
			mnsLog.log("Couldn't find root guide, aborting.", svr = 2)

	def destroyUI(self):
		mnsUIUtils.recDeleteAllLayoutItems(self.mainVLayout)
		mnsUIUtils.recDeleteAllLayoutItems(self.splitLayout)
		self.txtFields = ()

	def boolAutoExlusiveTrig(self, triggerOrigin, exclutionGroup, boolFeildsByName, state):
		for groupMemberName in exclutionGroup:
			cbxObj =  boolFeildsByName[groupMemberName]
			if cbxObj is not triggerOrigin:
				cbxObj.blockSignals(True)
				cbxObj.setChecked(False)
				cbxObj.blockSignals(False)

	def drawUI(self):
		"""Main UI draw method.
		"""

		boolExclusives = []
		boolFeildsByName = {}
		attributeListByName = {}
		for arg in self.fullList:
			attributeListByName[arg.name] = arg
		
		self.drawTitle()

		for i in range(0,len(self.fullList)):
			if "divider" in self.fullList[i].name.lower(): self.dividerLayout = None

			contentLayout = self.mainVLayout

			if self.split:
				if i >= self.split: contentLayout = self.splitLayout
			if self.dividerLayout: 
				contentLayout = self.dividerLayout
			if self.fullList[i].name.lower() == "extraChannels".lower():
				extraChannelsBox = mnsUIUtils.drawExtraChannelsBox(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (extraChannelsBox,)
			elif self.fullList[i].name.lower() == "spaces".lower():
				spacesBox = mnsUIUtils.drawSpacesBox(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (spacesBox,)
			elif "path".lower() in self.fullList[i].name.lower():
				txtField = mnsUIUtils.drawPathField(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (txtField,)
			elif "constructscripts".lower() in self.fullList[i].name.lower():
				txtField = mnsUIUtils.drawCustomScriptsSlot(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (txtField,)
			elif "divider" in self.fullList[i].name.lower():
				txtField, self.dividerLayout, dividerWidget = mnsUIUtils.drawHorizontalDevider(self.fullList[i], contentLayout)
				self.allCollapsible.append(dividerWidget)
				self.txtFields = self.txtFields + (txtField,)
			elif "channelControl".lower() in self.fullList[i].name.lower():
				chennelControl = mnsUIUtils.drawChannelControl(self.fullList[i], contentLayout, rootGuide = self.rootGuide)
				self.txtFields = self.txtFields + (chennelControl,)
			elif "schemeOverride".lower() in self.fullList[i].name.lower() :
				colorScheme = mnsUIUtils.drawColorSchemeOverride(self.fullList[i], contentLayout, sideCB = self.sideCB, colOverride = self.colOverride, rigTop = self.rigTop)
				self.txtFields = self.txtFields + (colorScheme,)	
			elif "colorScheme".lower() in self.fullList[i].name.lower() :
				colorScheme = mnsUIUtils.drawColorScheme(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (colorScheme,)
			elif "color" in self.fullList[i].name.lower() and self.fullList[i].type is tuple and len(self.fullList[i].default) == 3:
				colorBox = mnsUIUtils.drawColorBox(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (colorBox,)
			elif "alpha" == self.fullList[i].name:
				txtField = mnsUIUtils.drawButtonAndField(self.fullList[i], contentLayout, True)
				self.txtFields = self.txtFields + (txtField,)
			elif self.fullList[i].ob != [] and type(self.fullList[i].ob) is list and len(self.fullList[i].ob) > 0:
				optionBox, lineEdit = mnsUIUtils.drawOptionBox(self.fullList[i], contentLayout)
				if lineEdit:
					self.widgetRelationships.update({optionBox: lineEdit})
				self.txtFields = self.txtFields + (optionBox,)
				if "side".lower() in self.fullList[i].name.lower():
					self.sideCB = optionBox
			elif self.fullList[i].type == str or self.fullList[i].type == list or self.fullList[i].type == tuple:
				if self.fullList[i].type == list and self.fullList[i].multiRowList:
					multiRowBox = mnsUIUtils.drawSpacesBox(self.fullList[i], contentLayout, genericList = True)
					self.txtFields = self.txtFields + (multiRowBox,)
				else:
					txtField = mnsUIUtils.drawButtonAndField(self.fullList[i], contentLayout)
					self.txtFields = self.txtFields + (txtField,)
			elif self.fullList[i].type == int:
				intSlider = mnsUIUtils.drawIntSpinner(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (intSlider,)
			elif self.fullList[i].type == float:
				floatSlider = mnsUIUtils.drawFloatScroll(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (floatSlider,)
			elif self.fullList[i].type == bool:
				if self.fullList[i].boolExclusive:
					validatedList = []
					for boolPair in self.fullList[i].boolExclusive:
						if boolPair in attributeListByName and attributeListByName[boolPair].type == bool:
							validatedList.append(boolPair)
					
					if validatedList:
						groupToAdd = [self.fullList[i].name] + validatedList
						
						#make sure not to add the same group multiple times
						previosulyAdded = False
						for previousGroup in boolExclusives:
							inPreviousGroup = [x for x in groupToAdd if x in previousGroup]
							if inPreviousGroup:
								previosulyAdded = True
								break
						if not previosulyAdded:
							boolExclusives.append(groupToAdd)

				bolChk = mnsUIUtils.drawBooleanChk(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (bolChk,)
				boolFeildsByName[self.fullList[i].name] = bolChk
				if "colOverride".lower() in self.fullList[i].name.lower():
					self.colOverride = bolChk
			else:
				txtField = mnsUIUtils.drawButtonAndFieldUnknown(self.fullList[i], contentLayout)
				self.txtFields = self.txtFields + (txtField,)

			self.attrComponentPairing.update({self.fullList[i].name: self.txtFields[-1]})

		if boolExclusives:
			for exclutionGroup in boolExclusives:
				if set(exclutionGroup).issubset(boolFeildsByName.keys()):
					#group fully validated, execture boolExlusive behaviour
					#backwards compatibility- first, if any are on, make sure the others are off
					foundOnAttr = False
					for attrName in exclutionGroup:
						if not foundOnAttr and boolFeildsByName[attrName].isChecked():
							foundOnAttr = True
						elif foundOnAttr:
							boolFeildsByName[attrName].setChecked(False)

					#now set the trigger
					for attrName in exclutionGroup:
						boolFeildsByName[attrName].toggled.connect(partial(self.boolAutoExlusiveTrig, boolFeildsByName[attrName], exclutionGroup, boolFeildsByName))

		#read only mode
		if self.readOnly:
			roWidgets = self.txtFields
			for k in self.widgetRelationships.keys():
				roWidgets += (self.widgetRelationships[k],)

			for component in roWidgets:
				if component:
					if type(component) is list:
						for c in component:
							c.setEnabled(False)
					else:
						component.setEnabled(False)
			for button in self.findChildren(QtWidgets.QPushButton):
				button.setEnabled(False)

	def runCmd(self):
		"""Main method run command trigger.
		"""
		if self.funObjectCreation:
			if (self.arguments == []) and (self.optArguments == []):
				m = sys.modules[self.defenition.__module__]
				exec ('import ' + m.__name__) in globals()
				eval(m.__name__ + '.' + self.defenitionName +  '()')

			else:
				sendVals = self.assembleFeildValues()

				finalArgCallStrComp = mnsArgs.recompileArgumetsAsString(self.defenition, self.arguments, self.optArguments, sendVals)
				m = sys.modules[self.defenition.__module__]
				reload(m)
				exec ('import ' + m.__name__) in globals()
				m = sys.modules[self.defenition.__module__]
				reload(m)
				mnsLog.log('executing: ' +  (m.__name__ + '.' + self.defenitionName +  '(' + finalArgCallStrComp + ')'), svr = 1)
				eval(m.__name__ + '.' + self.defenitionName +  '(' + finalArgCallStrComp + ')')
		else:
			sendVals = self.assembleFeildValues()
			kwargsMapping = {}
			if self.preDefinedArgs: kwargsMapping = self.preDefinedArgs
			for k in range (0, len(sendVals)): kwargsMapping.update({self.optArguments[k].name: sendVals[k]})
			if self.customRunCommand: self.customRunCommand(**kwargsMapping)
			if self.closeOnApply_cbx.isEnabled() and not self.closeOnApply_cbx.isChecked():
				pass
			else:
				self.destroy(True, True)

	def assembleFeildValues(self):
		"""Assemble all UI values into a list
		"""

		sendVals = []
		for i in range(0,len(self.fullList)):
			if self.fullList[i].name.lower() == "spaces".lower():
				send = []
				currentItems =  [str(self.txtFields[i].item(k).text()) for k in range(self.txtFields[i].count())]
				if currentItems:
					sendVals.append(currentItems)
				else: sendVals.append(["None"])
			elif "divider".lower() in self.fullList[i].name.lower(): 
				value = self.fullList[i].default
				sendVals.append(value)
			elif "schemeOverride".lower() in self.fullList[i].name.lower():
				send = []
				for btn in self.txtFields[i]:
					col = btn.palette().button().color()
					value = ( float( float(col.red()) / 255), float(float(col.green()) / 255), float(float(col.blue()) / 255))
					send.append(value)
				sendVals.append(send)
			elif "channelControl".lower() in self.fullList[i].name.lower():
				send = [" "]
				for cbx in self.txtFields[i]:
					if cbx.isChecked(): send.append(cbx.objectName())
				sendVals.append(send)
			elif "colorScheme".lower() in self.fullList[i].name.lower() :
				send = []
				for btn in self.txtFields[i]:
					col = btn.palette().button().color()
					value = ( float( float(col.red()) / 255), float(float(col.green()) / 255), float(float(col.blue()) / 255))
					send.append(value)
				sendVals.append(send)
			elif "color" in self.fullList[i].name and self.fullList[i].type is tuple and len(self.fullList[i].default) == 3:
				col = self.txtFields[i].palette().button().color()
				value = ( float( float(col.red()) / 255), float(float(col.green()) / 255), float(float(col.blue()) / 255))
				sendVals.append(value)
			elif "constructscripts" in self.fullList[i].name.lower():
				listItems = [self.txtFields[i].item(j).toolTip() for j in range(self.txtFields[i].count())]
				send = ""
				if listItems: send = mnsString.flattenArray(listItems)
				sendVals.append(send)
			elif self.fullList[i].name.lower() == "extraChannels".lower():
				treeWG = self.txtFields[i]
				sendList = []
				for itemIdx in range(treeWG.topLevelItemCount()):
					item = treeWG.topLevelItem(itemIdx)
					sendList.append({"attrName": item.text(0), "attrTarget": item.text(1), "dir": item.text(2), "isDiv": item.text(3)})
				sendVals.append(json.dumps(sendList))
			elif self.fullList[i].ob != [] and type(self.fullList[i].ob) is list and len(self.fullList[i].ob) > 0:
				value = ""
				if(self.fullList[i].type == str):
					value = self.txtFields[i].currentText()
					if "controlshape" in self.fullList[i].name.lower():
						if value == "text" and self.txtFields[i] in self.widgetRelationships.keys():
							currentText = self.widgetRelationships[self.txtFields[i]].text()
							if not currentText: value = "circle"
							else:
								value = "txtCtrlShp_" + currentText
				else:
					value = self.txtFields[i].currentIndex()
				sendVals.append(value)
			elif self.fullList[i].type == str:
				value = self.txtFields[i].text()
				sendVals.append(value)
			elif self.fullList[i].type == list:
				if self.fullList[i].multiRowList:
					send = []
					currentItems =  [str(self.txtFields[i].item(k).text()) for k in range(self.txtFields[i].count())]
					if currentItems:
						sendVals.append(currentItems)
					else: sendVals.append(["None"])
				else:
					value = self.txtFields[i].text()
					sendVals.append(value)
			elif self.fullList[i].type == float:
				value = self.txtFields[i].value()
				sendVals.append(value)
			elif self.fullList[i].type == int:
				value = self.txtFields[i].value()
				sendVals.append(value)
			elif self.fullList[i].type == bool:
				value = self.txtFields[i].isChecked()
				sendVals.append(value)
			else:
				value = self.txtFields[i].text()
				sendVals.append(value)
		#return;list
		return sendVals

	def loadUI(self):
		"""Main UI load.
		"""

		self.show()
		state = QtCore.Qt.WindowMinimized
		if self.windowState() == QtCore.Qt.WindowMinimized:
			self.setWindowState(QtCore.Qt.WindowNoState)
