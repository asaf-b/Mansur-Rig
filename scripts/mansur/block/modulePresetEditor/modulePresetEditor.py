"""=== Author: Assaf Ben Zur ===
This tool was designed to manage module presets.
As Mansur-Rig modules comatin many attrbiutes, it is sometimes more convenient to use a predefined preset to speed up the wrokflow.
Mansur-Rig includes some module presets, although this was designed mainly to allow usesrs to create their own presets, essentially saving the module settings' state.
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
from ...core import arguments as mnsArgs
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

class ExportPresetDialog(QtWidgets.QDialog):
	def __init__(self, parent = None):
		super(ExportPresetDialog, self).__init__(parent)
		self.setWindowTitle ("Module Preset Export")
		self.setFixedSize(400,200)
		mnsUIUtils.fourKWindowAdjust(self)

		QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

		self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
		self.buttonBox.buttons()[0].setText("Export")
		self.buttonBox.buttons()[0].setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
		self.buttonBox.buttons()[1].setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
		self.buttonBox.buttons()[0].setFixedSize(150,22)
		self.buttonBox.buttons()[1].setFixedSize(100,22)

		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.accepted.connect(self.getInfo)
		self.buttonBox.rejected.connect(self.reject)

		self.layout = QtWidgets.QVBoxLayout()
		message = QtWidgets.QLabel("<html><head/><body><p align=\"center\"><span style=\" font-size:11pt; font-style:italic;\">Please input required information for this preset</span></p></body></html>")
		self.layout.addWidget(message)
		
		hLayout = QtWidgets.QHBoxLayout()
		lbl = QtWidgets.QLabel("Author")
		lbl.setFixedWidth(70)
		hLayout.addWidget(lbl)
		self.author_le = QtWidgets.QLineEdit()
		hLayout.addWidget(self.author_le)
		self.layout.addLayout(hLayout)

		hLayout = QtWidgets.QHBoxLayout()
		lbl = QtWidgets.QLabel("Description")
		lbl.setFixedWidth(70)
		hLayout.addWidget(lbl)
		self.description_te = QtWidgets.QTextEdit()
		self.description_te.setFixedHeight(80)
		hLayout.addWidget(self.description_te)
		self.layout.addLayout(hLayout)

		self.layout.addWidget(self.buttonBox)
		self.setLayout(self.layout)

	def getInfo(self):
		return self.author_le.text(), self.description_te.toPlainText()

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "modulePresetEditor.ui")
class MnsModulePresetEditor(form_class, base_class):
	"""Module preset Tool UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsModulePresetEditor, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsModulePresetEditor") 

		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		# locals
		self.rigTop = None
		self.mnsModulePresetsDir = os.path.dirname(__file__) + "/mnsModulePresets"
		self.settingsWindowDynUI = parent
		status, self.moduleType = mnsUtils.validateAttrAndGet(self.settingsWindowDynUI.rootGuide, "modType", "")
		if not self.moduleType:
			self.moduleType = self.settingsWindowDynUI.titleLbl.text().split(" ")[0]

		self.winTitle_lbl_2.setText("<b>" + self.moduleType + "</b>")
		self.presetsDict = {}
		self.currentPreset = {}

		#methods
		self.gatherAdditionalModulePresetsPaths()
		self.initlizeUI()
		self.connectSignals()
		self.initializeView()
		mnsGui.setGuiStyle(self, "Module Preset Editor")

	##################	
	###### INIT ######
	##################

	def initlizeUI(self):
		"""Initialize the UI display
		"""

		self.load_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/bake_Settings.png"))
		self.importPreset_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/save.png"))
		self.exportPreset_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
		self.close_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nodeGrapherClose.png"))

	def connectSignals(self):
		"""Connect all UI Signals.
		"""

		self.presets_lst.itemSelectionChanged.connect(self.readPreset)
		self.exportPreset_btn.released.connect(self.exportPreset)
		self.load_btn.released.connect(self.loadPreset)
		self.importPreset_btn.released.connect(self.importPreset)
		self.close_btn.released.connect(self.destroy)
		
	##################	
	###### View ######
	##################

	def initializeView(self, selection = None):
		"""initialize data into the UI
		"""

		#get all presets then filter by type.
		#draw only if type matches to current module type

		presets = []
		self.presetsDict = {}
		self.presets_lst.clear()
		self.author_le.clear()
		self.description_te.clear()

		for o in os.listdir(self.mnsModulePresetsDir):
			if os.path.isfile(self.mnsModulePresetsDir + "/" + o) and o.endswith(GLOB_modPresetSuffix):
				formatedPresetInfo = None
				
				try:
					formatedPresetInfo = mnsUtils.readJson(self.mnsModulePresetsDir + "/" + o)
				except:
					pass

				if formatedPresetInfo and formatedPresetInfo["info"]["module"] == self.moduleType:
					presets.append(o.split(".")[0])
					self.presetsDict.update({o: self.mnsModulePresetsDir + "/" + o})


		for customPath in self.customPresetsPaths:
			if os.path.isdir(customPath):
				for o in os.listdir(customPath):
					if os.path.isfile(customPath + "/" + o) and o.endswith(GLOB_modPresetSuffix):
						formatedPresetInfo = None
						try:
							formatedPresetInfo = mnsUtils.readJson(customPath + "/" + o)
						except:
							pass

						if formatedPresetInfo and formatedPresetInfo["info"]["module"] == self.moduleType:
							presets.append(o.split(".")[0])
							self.presetsDict.update({o: customPath + "/" + o})

		self.presets_lst.addItems(presets)

		#select
		if selection:
			for k in range(self.presets_lst.count()):
				item =self.presets_lst.item(k)
				if item.text() == selection:
					self.presets_lst.setCurrentItem(item)
					break

	def gatherAdditionalModulePresetsPaths(self, **kwargs):
		"""Initialize any custom module presets paths that already exist within the data collect json.
		"""

		self.customPresetsPaths = []

		additionalPathsFile = mnsUtils.locatePreferencesDirectory() + "/" + GLOB_additionalModulePresetsPathsJsonName + ".json"
		if os.path.isfile(additionalPathsFile):
			additional = mnsUtils.readJson(additionalPathsFile)
			for add in additional:
				self.customPresetsPaths.append(add)

	def readPresetFile(self, filePath = ""):
		"""Read a preset from the selected file input
		"""

		if filePath:
			return mnsUtils.readJson(filePath)

	def readPreset(self):
		"""Read the curretly selected preset
		"""

		self.description_te.clear()
		self.author_le.clear()
		self.currentPreset = {}

		selectedItem = self.presets_lst.currentItem()
		fullFileName = selectedItem.text() + "." + GLOB_modPresetSuffix
		if fullFileName in self.presetsDict.keys():
			formatedPresetInfo = mnsUtils.readJson(self.presetsDict[fullFileName])
				
			self.author_le.setText(formatedPresetInfo["info"]["author"])
			self.description_te.setText(formatedPresetInfo["info"]["description"])

			self.currentPreset = formatedPresetInfo

	##################	
	##### Action #####
	##################

	def readCurrentModuleValues(self):
		"""From the current preset, read the current UI state.
		This method will return a formatted data assembly of all values and fields within the module-settings tab
		"""

		sendVals = self.settingsWindowDynUI.assembleFeildValues()
		kwargsMapping = {}
		if self.settingsWindowDynUI.preDefinedArgs: kwargsMapping = self.settingsWindowDynUI.preDefinedArgs
		for k in range (0, len(sendVals)): kwargsMapping.update({self.settingsWindowDynUI.optArguments[k].name: sendVals[k]})
		
		modArgs = [a.name for a in self.settingsWindowDynUI.modArgs]
		
		exportAssembly = {}
		for argName in kwargsMapping.keys():
			if argName in modArgs:
				exportAssembly[argName] = kwargsMapping[argName]

		return exportAssembly

	def loadPreset(self, **kwargs):
		"""Apply the selected preset onto the settings window
		"""

		dataAssembly = kwargs.get("dataAssembly", self.currentPreset)

		if dataAssembly and "data" in dataAssembly:
			for attrKey in self.settingsWindowDynUI.attrComponentPairing.keys():
				UIComponent = self.settingsWindowDynUI.attrComponentPairing[attrKey]
				
				if UIComponent and attrKey in dataAssembly["data"]:
					newValue = dataAssembly["data"][attrKey]
					componentType = type(UIComponent)

					#set values based on data type
					if componentType == QtWidgets.QCheckBox: UIComponent.setChecked(newValue)
					elif componentType == QtWidgets.QComboBox:
						if type(newValue) == int:
							UIComponent.setCurrentIndex(newValue)
						else:
							UIComponent.setCurrentText(newValue)
					elif componentType == QtWidgets.QSpinBox or componentType == QtWidgets.QDoubleSpinBox: UIComponent.setValue(newValue)
					elif "channelcontrol" in attrKey.lower() and componentType == list:
						for cbx in UIComponent:
							subAttrName = cbx.objectName()
							if subAttrName.replace(" ", ""):
								if subAttrName in newValue: cbx.setChecked(True)
								else: cbx.setChecked(False)
					elif componentType == QtWidgets.QListWidget:
						UIComponent.clear()
						UIComponent.addItems(newValue)
					elif componentType == QtWidgets.QLineEdit:
						UIComponent.setText(newValue)

			#message
			mnsLog.log("Preset Loaded succesffully.", svr = 1)

	def importPreset(self):
		"""Import a preset from file
		"""

		file = QtWidgets.QFileDialog.getOpenFileName(self, "Select Module Preset File", filter = "Mns Module Preset (*.mnsBMPS)")
		if file:
			file = file[0]
			if file.endswith(".mnsBMPS"):
				formatedPresetInfo = self.readPresetFile(file)
				if "info" in formatedPresetInfo:
					if "module" in formatedPresetInfo["info"]:
						if formatedPresetInfo["info"]["module"] == self.moduleType:
							self.loadPreset(dataAssembly = formatedPresetInfo)
							pm.confirmDialog( title='Success', message= "Preset imported succesffully.", defaultButton='OK')
						else:
							mnsLog.log("The selected module preset (" + formatedPresetInfo["info"]["module"] + ") dosn't match the current module type (" + self.moduleType + "). Aborting.", svr = 3) 
					else:
						mnsLog.log("Couldn't read preset file.", svr = 3) 
				else:
					mnsLog.log("Couldn't read preset file.", svr = 3) 
			else:
				mnsLog.log("Couldn't read preset file.", svr = 3) 

	def exportPreset(self):
		"""Export current settings window state as a preset.
		"""

		#get author and description
		exportDialog = ExportPresetDialog()
		exportDialogReturn = exportDialog.exec_()
		if exportDialogReturn:
			presetInfo = exportDialog.getInfo()
			author = presetInfo[0]
			description = presetInfo[1]

			if author and description:
				#get dynUI module values
				exportValuesAssembly = self.readCurrentModuleValues()

				#finalizeData
				exportData = {"info": {"module": self.moduleType, "author": author, "description": description}, "data": exportValuesAssembly}
				
				#export
				filename = QtWidgets.QFileDialog.getSaveFileName(mnsUIUtils.get_maya_window(), "Export Module Preset", None, "Mns Module Preset (*.mnsBMPS)")
				if filename: 
					filename = filename[0]
					if filename.endswith(".mnsBMPS"):
						if not "_" + self.moduleType + ".mnsBMPS" in filename:
							filename = filename.replace(".mnsBMPS", "_" + self.moduleType + ".mnsBMPS")
						mnsUtils.writeJsonFullPath(filename, exportData)

						#message
						pm.confirmDialog( title='Success', message= "Preset exported succesffully.", defaultButton='OK')

						#re init
						self.initializeView(filename.replace("\\","/").split("/")[-1].split(".")[0])

			else:
				mnsLog.log("Preset information input is mandatory, please try again.", svr = 3)	
			
	##################	
	###### LOAD ######
	##################

	def loadWindow(self):
		"""Show window method.
		"""

		mnsLog.log("mnsModulePresetEditor", svr = 0)
		self.show()

def loadModulePresetEditor(parent=mnsUIUtils.get_maya_window()): 
	"""Load the module preset window, avoid UI duplication.
	"""

	mnsLog.log("mnsModulePresetEditor Tool Load Pressed.")
	previousPosition = mnsUIUtils.reloadWindow("mnsModulePresetEditor")

	mnsModulePresetEditorWin = MnsModulePresetEditor(parent = parent)
	mnsModulePresetEditorWin.loadWindow()
	if previousPosition: mnsModulePresetEditorWin.move(previousPosition)
	return mnsModulePresetEditorWin

