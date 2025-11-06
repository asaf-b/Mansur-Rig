"""=== Author: Assaf Ben Zur ===
A Simple global UI class to handle global setting within the package.
All global changeable variables should be inserted into this UI.
Handeling is semi-procedural, drawing and retreiving all setting procedurally, although the implementation will look for specific widget names to handle the settings.
"restore factory defaults" is also contained within this UI, actual implementation is within mnsUtils.
"""

#global dependencies
import os, datetime, time, inspect, json


from maya import cmds
import pymel.core as pm
 
from functools import partial

#mns dependencies
from ..core.globals import *
from ..core import UIUtils as mnsUIUtils
from ..core import log as mnsLog
from ..core import utility as mnsUtils
from ..gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore, QtWidgets
	from PySide6.QtWidgets import QTreeWidgetItem
else:
	from PySide2 import QtGui, QtCore, QtWidgets
	from PySide2.QtWidgets import QTreeWidgetItem

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "preferences.ui")

class MnsPreferences(form_class, base_class):
	"""Main UI class
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsPreferences, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsPreferences") 
		
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		#init prefs
		self.currentPrefs = mnsUtils.getMansurPrefs()

		#run methods
		self.connectSignals()
		self.initView()
		mnsGui.setGuiStyle(self, "Preferences")

	def connectSignals(self): 
		"""Connect all the UI signals
		"""

		self.prefCat_trv.currentItemChanged.connect(self.loadCategoryPrefs)
		self.cancel_btn.released.connect(self.destroy)
		self.save_btn.released.connect(self.saveSetting)
		self.restoreDefault_btn.released.connect(self.restoreDefaults)
		self.pickerImagesPathLoad_btn.released.connect(lambda: self.loadPath(self.pickerImagesFallbackPath))
		
		for settingCat in self.currentPrefs:
			for setting in self.currentPrefs[settingCat]:
				setWid = self.findChild(QtWidgets.QWidget, setting)
				if setWid:
					if type(setWid) is QtWidgets.QSpinBox or type(setWid) is QtWidgets.QDoubleSpinBox:
						setWid.valueChanged.connect(partial(self.updateValue, settingCat, setting, setWid))
					elif type(setWid) is QtWidgets.QComboBox:
						setWid.currentIndexChanged.connect(partial(self.updateValue, settingCat, setting, setWid))
					elif type(setWid) is QtWidgets.QCheckBox or (type(setWid) is QtWidgets.QPushButton and not "color" in setWid.objectName()):
						setWid.toggled.connect(partial(self.updateValue, settingCat, setting, setWid))
					elif type(setWid) is QtWidgets.QPushButton and "color" in setWid.objectName():
						setWid.released.connect(partial(self.updateColorValue, setWid, settingCat, setting))
					elif type(setWid) is QtWidgets.QLineEdit:
						setWid.textChanged.connect(partial(self.updateLineEditValue, setWid, settingCat, setting))

	def loadPath(self, lineEditWidget):
		if lineEditWidget:
			selectedDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Picker Images Fallback Path", None)
			if selectedDir:
				selectedDir = mnsUIUtils.relativePathCheck(selectedDir)
				lineEditWidget.setText(selectedDir)

	def updateColorValue(self, colBtn, settingCat, setting):
		mnsUIUtils.getColor(colBtn)
		col = colBtn.palette().button().color()
		value = [float( float(col.red()) / 255), float(float(col.green()) / 255), float(float(col.blue()) / 255)]
		if settingCat and setting:
			self.currentPrefs[settingCat].update({setting: value})

	def updateLineEditValue(self, setWid, settingCat, setting, text):
		value = None
		if setWid:
			if type(setWid) is QtWidgets.QLineEdit:
				value = setWid.text()

		if settingCat and setting:
			self.currentPrefs[settingCat].update({setting: value})

	def updateValue(self, settingCat, setting, setWid, dummyA = None, dummyB = None, dummyC = None):
		value = None
		if setWid:
			if type(setWid) is QtWidgets.QSpinBox or type(setWid) is QtWidgets.QDoubleSpinBox: 
				value = setWid.value()
			elif type(setWid) is QtWidgets.QComboBox:
				value = setWid.currentIndex()
			elif type(setWid) is QtWidgets.QCheckBox or (type(setWid) is QtWidgets.QPushButton and not "color" in setWid.objectName()):
				if setWid.isChecked(): value = 1
				else: value = 0

		if settingCat and setting:
			self.currentPrefs[settingCat].update({setting: value})

	def initView(self):
		if self.currentPrefs:
			k = 0
			for prefCat in self.currentPrefs.keys():
				catItem = QTreeWidgetItem(self.prefCat_trv, [prefCat])
				if k == 0: catItem.setSelected(True)
				k += 1
		self.pickerImagesPathLoad_btn.setIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))

	def loadCategoryPrefs(self, currentItem, previousItem):
		if currentItem:
			targetTabName = currentItem.text(0).lower() + "_page"
			if self.mainStackedWid:
				for tabIndex in range(self.mainStackedWid.count()):
					pageWidget = self.mainStackedWid.widget(tabIndex)
					currentName = pageWidget.objectName().lower()
					if targetTabName == currentName:
						self.mainStackedWid.setCurrentIndex(tabIndex)
						self.title_lbl.setText(currentItem.text(0))
						pageSetting = self.currentPrefs[currentItem.text(0)]
						for setting in pageSetting:
							setWid = self.findChild(QtWidgets.QWidget, setting)
							if type(setWid) is QtWidgets.QSpinBox:
								setWid.setValue(pageSetting[setting])
							elif type(setWid) is QtWidgets.QDoubleSpinBox:
								setWid.setValue(float(pageSetting[setting]))
							elif type(setWid) is QtWidgets.QComboBox:
								setWid.setCurrentIndex(pageSetting[setting])
							elif type(setWid) is QtWidgets.QCheckBox or (type(setWid) is QtWidgets.QPushButton and not "color" in setWid.objectName()):
								setWid.setChecked(pageSetting[setting])
							elif type(setWid) is QtWidgets.QPushButton and "color" in setWid.objectName():
								setWid.setStyleSheet("QWidget { background-color: rgb(" + str(pageSetting[setting][0] * 255.0) + "," + str(pageSetting[setting][1]*255.0) + "," + str(pageSetting[setting][2] * 255.0) + ");}")
							elif type(setWid) is QtWidgets.QLineEdit:
								setWid.setText(pageSetting[setting])

	def saveSetting(self):
		if self.currentPrefs:
			settingsFile = mnsUtils.getMansurPrefsFromFile(returnFileDirectory = True)
			with open(settingsFile , 'w') as outfile:  
				json.dump(self.currentPrefs, outfile)
				mnsUtils.updateMansurPrefs()
				mnsUIUtils.readGuiStyle()
				pm.confirmDialog( title='Settings saved.', message="Settings saved successfully!", defaultButton='OK')

	def restoreDefaults(self):
		reply = QtWidgets.QMessageBox.question(self, 'Factory Defaults Restore', 'Are you sure you want to resote all defaults?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.Yes:
			mnsUtils.createMnsDefaultPrefs(restoreDefaults = True)
			mnsUtils.updateMansurPrefs()
			pm.confirmDialog( title='Defaults Restored.', message="Defaults Restored successfully.", defaultButton='OK')
			mnsUIUtils.readGuiStyle()
			loadPreferences()

	def loadWindow(self):
		""" Main window load.
		"""
		self.show()
		
def loadPreferences():
	"""Load the Preferences UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsPreferences")

	prefWin = MnsPreferences()
	prefWin.loadWindow()
	if previousPosition: prefWin.move(previousPosition)

