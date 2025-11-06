"""=== Author: Assaf Ben Zur ===
mnsPickerSettings UI Class
This is simple UI class built to handle user manipulation to PLG settings easily.
The settings window (at freest state) handles:
- Color
- Side
- Control goruping (body/facial)
- scaleX, scaleY
- Button text
- font size, color
- font bold, italic, underline
- controls select 
- Action script (pre/post)
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial
from os.path import dirname, abspath   
import os, json, ctypes

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ..core import blockUtility as blkUtils
from ...core.globals import *

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "mnsPLGSettings.ui")
class MnsPLGSettingsUI(form_class, base_class):
	"""mnsPickerSettings UI Class.
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsPLGSettingsUI, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName( 'MnsPLGSettingsUI' )
		mnsLog.log("MnsPLGSettingsUI Class Initialize.")
		
		##locals
		self.currentPlgNode = None

		self.initView()
		self.loadSelection()
		self.connectSignals()

	#### GLOBALS ###############
	def connectSignals(self):
		"""Connect all UI signals.
		"""

		self.loadSelection_btn.released.connect(self.loadSelection)
		self.createPLG_btn.released.connect(self.createAndLoadPlg)

		#edits
		self.color_btn.released.connect(self.updateButtonColor)
		self.scaleX_sb.valueChanged.connect(partial(self.updateScale, mode = "x"))
		self.scaleY_sb.valueChanged.connect(partial(self.updateScale, mode = "y"))
		self.buttonText_le.editingFinished.connect(self.updateButtonText)
		self.fontSize_sb.valueChanged.connect(self.updateButtonFontSize)
		self.textColor_btn.released.connect(self.updateButtonTextColor)
		self.bold_btn.toggled.connect(self.updateButtonFont)
		self.italic_btn.toggled.connect(self.updateButtonFont)
		self.underline_btn.toggled.connect(self.updateButtonFont)
		self.sides_cb.currentIndexChanged.connect(self.updateSide)
		self.facial_rb.toggled.connect(self.updateCtrlGroup)

		#controlsSelect
		self.controlsClear_btn.released.connect(self.clearControls)
		self.addSelected_btn.released.connect(self.addSceneSelectedControls)
		self.removeControls_btn.released.connect(self.removeSceneSelectedControls)
		self.replaceControls_btn.released.connect(self.replaceControls)
		self.controlsSelect_btn.released.connect(self.selectControls)

		#actionScript
		self.pre_cbx.toggled.connect(self.updatePre)
		self.scriptClear_btn.released.connect(self.clearScript)
		self.scriptRun_btn.released.connect(self.runScript)
		self.actionScript_te.textChanged.connect(self.updateActionScript)

		#click btn
		self.clickButton_btn.released.connect(lambda: blkUtils.pickerButtonClickAction(None, plgNode = self.currentPlgNode))

	####### init view #######
	def initView(self):
		"""Initialize view:
		- Set title
		- Set Icons
		- Initialize sides comboBox
		"""

		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/dynUITitle.png"))
		self.setWindowIcon(QtGui.QIcon(GLOB_guiIconsDir + "/logo/mansur_logo_noText_picker.png"))
		self.sides_cb.addItems([mnsPS_left, mnsPS_cen, mnsPS_right])

	def clearView(self):
		"""This method clears all setting from the UI, and restores 'empty' state.
		"""

		self.currentPlgNode = None
		self.name_le.clear()
		self.master_le.clear()
		self.color_btn.setStyleSheet("QWidget { background-color: rgb(" + str(1.0 * 255.0) + "," + str(1.0*255.0) + "," + str(1.0 * 255.0) + ");}")
		self.color_btn.setEnabled(True)
		self.primary_rb.setChecked(True)
		self.ctrlType_gb.setEnabled(True)
		self.body_rb.setChecked(True)
		self.ctrlGrp_gb.setEnabled(True)
		self.buttonText_le.clear()
		self.textColor_btn.setStyleSheet("QWidget { background-color: rgb(" + str(1.0 * 255.0) + "," + str(1.0*255.0) + "," + str(1.0 * 255.0) + ");}")
		self.fontSize_sb.setValue(8)
		self.bold_btn.setChecked(False)
		self.italic_btn.setChecked(False)
		self.underline_btn.setChecked(False)
		self.controls_lst.clear()
		self.controls_lst.setEnabled(True)
		self.actionScript_te.clear()
		self.actionScript_te.setEnabled(True)
		self.scriptSection_gb.setEnabled(True)
		self.scaleX_sb.setValue(1.0)
		self.scaleY_sb.setValue(1.0)
		self.sides_cb.setCurrentIndex(1)
		self.sides_cb.setEnabled(True)
		self.replaceControls_btn.setEnabled(True)
		self.addSelected_btn.setEnabled(True)
		self.removeControls_btn.setEnabled(True)
		self.controlsClear_btn.setEnabled(True)

	def loadSelection(self, **kwargs):
		"""Main UI method- load current selection into the UI.
		This method will handle reading, and acquiring all settings into the UI from the selected PLG (only it is a plg type).
		"""

		toggleAttempt = kwargs.get("toggleAttempt", False) #arg

		self.clearView()

		currentSel = pm.ls(sl=True)
		if currentSel:
			if len(currentSel) > 0:
				plg = mnsUtils.validateNameStd(currentSel[0])
				if plg:
					if plg.node.hasAttr("blkClassID"):
						if not toggleAttempt and plg.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_ctrl):
							blkUtils.ctrlPickerGuideToggle()
							self.loadSelection(toggleAttempt = True)

						elif plg.node.blkClassID.get() == mnsUtils.returnKeyFromElementTypeDict(mnsTypeDict, mnsPS_plg):							
							self.ctrlType_gb.setEnabled(False)

							#set current local
							self.currentPlgNode = plg.node


							#name		
							self.name_le.setText(plg.name)

							#color
							self.color_btn.setStyleSheet("QWidget { background-color: rgb(" + str(plg.node.getShape().overrideColorR.get() * 255.0) + "," + str(plg.node.getShape().overrideColorG.get()*255.0) + "," + str(plg.node.getShape().overrideColorB.get() * 255.0) + ");}")
							
							#ctrl type
							if plg.node.hasAttr("blkCtrlTypeID"):
								if plg.node.blkCtrlTypeID.get() == 0: self.primary_rb.setChecked(True)
								elif plg.node.blkCtrlTypeID.get() == 1: self.secondary_rb.setChecked(True)
								elif plg.node.blkCtrlTypeID.get() == 2: self.tertiary_rb.setChecked(True)

							#btnText
							if plg.node.hasAttr("buttonText"): self.buttonText_le.setText(plg.node.buttonText.get())

							#textColor
							if plg.node.hasAttr("textColorR") and plg.node.hasAttr("textColorG") and plg.node.hasAttr("textColorB"): 
								self.textColor_btn.setStyleSheet("QWidget { background-color: rgb(" + str(plg.node.textColorR.get()) + "," + str(plg.node.textColorG.get()) + "," + str(plg.node.textColorB.get()) + ");}")

							#fontSize
							if plg.node.hasAttr("fontSize"): self.fontSize_sb.setValue(plg.node.fontSize.get())


							#bold, italic, underline
							if plg.node.hasAttr("bold"): 
								self.bold_btn.blockSignals(True)
								self.bold_btn.setChecked(plg.node.bold.get())
								self.bold_btn.blockSignals(False)
							if plg.node.hasAttr("italic"): 
								self.italic_btn.blockSignals(True)
								self.italic_btn.setChecked(plg.node.italic.get())
								self.italic_btn.blockSignals(False)
							if plg.node.hasAttr("underline"): 
								self.underline_btn.blockSignals(True)
								self.underline_btn.setChecked(plg.node.underline.get())
								self.underline_btn.blockSignals(False)

							#scale
							self.scaleX_sb.setValue(plg.node.sx.get())
							self.scaleY_sb.setValue(plg.node.sy.get())

							if plg.node.hasAttr("isFree") and not plg.node.isFree.get():
								self.controls_lst.setEnabled(False)
								self.color_btn.setEnabled(False)
								self.sides_cb.setEnabled(False)
								self.replaceControls_btn.setEnabled(False)
								self.addSelected_btn.setEnabled(False)
								self.removeControls_btn.setEnabled(False)
								self.controlsClear_btn.setEnabled(False)

								#master
								if plg.node.hasAttr("master") and plg.node.master.get():
									#master
									self.master_le.setText(plg.node.master.get())

							#ctrl group
							if plg.node.hasAttr("isFacial"):
								if plg.node.isFacial.get(): 
									self.facial_rb.blockSignals(True)
									self.facial_rb.setChecked(True)
									self.facial_rb.blockSignals(False)
								else: self.body_rb.setChecked(True)
							
							#side
							if plg.side == "l": self.sides_cb.setCurrentIndex(0)
							if plg.side == "c": self.sides_cb.setCurrentIndex(1)
							if plg.side == "r": self.sides_cb.setCurrentIndex(2)

							#control select
							if plg.node.hasAttr("selectControls"):
								controlsList = mnsUtils.splitEnumToStringList("selectControls", plg.node)
								if controlsList:
									self.controls_lst.addItems(controlsList)

							#action script
							if plg.node.hasAttr("actionScript"):
								self.actionScript_te.setPlainText(plg.node.actionScript.get())

	## Utility ##
	def createAndLoadPlg(self):
		"""'Create PLG' button trigger.
		A simple wrapper to create a new free plg, then selecting it and loading it into the UI.
		"""

		blkUtils.createPickerLayoutGuide(None, False, blkUtils.getRigTopForSel(), dontProject = True)
		self.loadSelection()

	## Edit triggers ##
	def updateButtonColor(self):
		"""Button color update requested trigger.
		"""

		color = mnsUIUtils.getColor(self.color_btn)
		if self.currentPlgNode:
			plgShape = self.currentPlgNode.getShape()
			pm.setAttr(plgShape.overrideColorRGB, (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0))

	def updateScale(self, size, **kwargs):
		"""Button scale update requested trigger.
		"""
		
		mode = kwargs.get("mode", None) #arg

		if self.currentPlgNode:
			if mode:
				if mode == "x": mnsUtils.setAttr(self.currentPlgNode.sx, self.scaleX_sb.value())
				else: mnsUtils.setAttr(self.currentPlgNode.sy, self.scaleY_sb.value())
			else:
				mnsUtils.setAttr(self.currentPlgNode.sx, self.scaleX_sb.value())
				mnsUtils.setAttr(self.currentPlgNode.sy, self.scaleY_sb.value())

	def updateButtonText(self):
		"""Button text update requested trigger.
		"""

		if self.currentPlgNode:
			if self.currentPlgNode.hasAttr("buttonText"):
				mnsUtils.setAttr(self.currentPlgNode.buttonText, self.buttonText_le.text())

	def updateButtonTextColor(self):
		"""Button text-color update requested trigger.
		"""

		color = mnsUIUtils.getColor(self.textColor_btn)
		if self.currentPlgNode:
			if self.currentPlgNode.hasAttr("textColorR"): mnsUtils.setAttr(self.currentPlgNode.textColorR, color.red())
			if self.currentPlgNode.hasAttr("textColorG"): mnsUtils.setAttr(self.currentPlgNode.textColorG, color.green())
			if self.currentPlgNode.hasAttr("textColorB"): mnsUtils.setAttr(self.currentPlgNode.textColorB, color.blue())

	def updateButtonFontSize(self, size):
		"""Button text-size update requested trigger.
		"""

		if self.currentPlgNode:
			if self.currentPlgNode.hasAttr("fontSize"): mnsUtils.setAttr(self.currentPlgNode.fontSize, size)

	def updateButtonFont(self):
		"""Button text-font update requested trigger.
		"""

		if self.currentPlgNode:
			if self.currentPlgNode.hasAttr("bold"): mnsUtils.setAttr(self.currentPlgNode.bold, self.bold_btn.isChecked())
			if self.currentPlgNode.hasAttr("italic"): mnsUtils.setAttr(self.currentPlgNode.italic, self.italic_btn.isChecked())
			if self.currentPlgNode.hasAttr("underline"): mnsUtils.setAttr(self.currentPlgNode.underline, self.underline_btn.isChecked())

	def updateControlsSelect(self):
		"""Button 'controls select' update requested trigger.
		"""

		if self.currentPlgNode:
			currentControls = [self.controls_lst.item(itemIdx).text() for itemIdx in range(self.controls_lst.count())]
			if currentControls:
				mnsUtils.addAttrToObj([self.currentPlgNode], type = "list", value = currentControls, name = "selectControls", locked = True, replace = True)
			else:
				if self.currentPlgNode.hasAttr("selectControls"):
					self.currentPlgNode.selectControls.setLocked(False)
					pm.deleteAttr(self.currentPlgNode.selectControls)

	def updateSide(self):
		"""Button side update requested trigger.
		"""

		if self.sides_cb.isEnabled():
			if self.currentPlgNode:
				plgNameStd = mnsUtils.validateNameStd(self.currentPlgNode)
				if plgNameStd:
					if self.sides_cb.currentText() != plgNameStd.side:
						newStd = mnsUtils.returnNameStdChangeElement(plgNameStd, side = self.sides_cb.currentText(), autoRename = False)
						newStd.findNextIncrement()
						existingNode = mnsUtils.checkIfObjExistsAndSet(obj = newStd.name)
						if not existingNode: 
							newStd = mnsUtils.returnNameStdChangeElement(plgNameStd, id = newStd.id, side = self.sides_cb.currentText())
							
							prefs = mnsUtils.getMansurPrefs()
							side = newStd.side

							if prefs and "Picker" in prefs:
								if (side + "_PLGText_fontSize") in prefs["Picker"]: 
									mnsUtils.setAttr(newStd.node.attr("fontSize"), prefs["Picker"][(side + "_PLGText_fontSize")])
								if (side + "_PLGText_color") in prefs["Picker"]:
									mnsUtils.setAttr(newStd.node.attr("textColorR"), prefs["Picker"][(side + "_PLGText_color")][0] * 255)
									mnsUtils.setAttr(newStd.node.attr("textColorG"), prefs["Picker"][(side + "_PLGText_color")][1] * 255)
									mnsUtils.setAttr(newStd.node.attr("textColorB"), prefs["Picker"][(side + "_PLGText_color")][2] * 255)
								if (side + "_PLGText_bold") in prefs["Picker"]:
									mnsUtils.setAttr(newStd.node.attr("bold"), prefs["Picker"][(side + "_PLGText_bold")])
								if (side + "_PLGText_italic") in prefs["Picker"]:
									mnsUtils.setAttr(newStd.node.attr("italic"), prefs["Picker"][(side + "_PLGText_italic")])
								if (side + "_PLGText_underline") in prefs["Picker"]:
									mnsUtils.setAttr(newStd.node.attr("underline"), prefs["Picker"][(side + "_PLGText_underline")])

							pm.select(newStd.node)
							self.loadSelection()
						else:
							if plgNameStd.side == "l": self.sides_cb.setCurrentIndex(0)
							if plgNameStd.side == "c": self.sides_cb.setCurrentIndex(1)
							if plgNameStd.side == "r": self.sides_cb.setCurrentIndex(2)

	def updateCtrlGroup(self):
		"""Button group update requested trigger.
		"""

		if self.currentPlgNode and self.currentPlgNode.hasAttr("isFacial"):
			if not self.currentPlgNode.isFacial.isConnected():
				if self.facial_rb.isChecked(): mnsUtils.setAttr(self.currentPlgNode.isFacial, True)
				else: mnsUtils.setAttr(self.currentPlgNode.isFacial, False)
			else:
				inCons = self.currentPlgNode.isFacial.listConnections(d = True)
				if inCons:
					rootGuide = inCons[0]
					ctrlDecendents = blkUtils.getCtrlsFromModuleRoot(rootGuide)
					mnsUtils.setAttr(rootGuide.isFacial, self.facial_rb.isChecked())
					for ctrl in ctrlDecendents:
						mnsUtils.setAttr(ctrl.node.isFacial, self.facial_rb.isChecked())
						plg = blkUtils.ctrlPickerGuideToggle(rootObjs = [ctrl], returnToggle = True)
						if plg:
							plg = mnsUtils.validateNameStd(plg[0])
							if plg.suffix == mnsPS_plg:
								blkUtils.connectPlgToVisChannel(plg)

			self.currentPlgNode.v.disconnect()
			blkUtils.connectPlgToVisChannel(self.currentPlgNode)
			pm.select(self.currentPlgNode, r = True)

	def updatePre(self):
		"""Button pre checkbox update requested trigger.
		"""

		if self.currentPlgNode:
			if self.currentPlgNode.hasAttr("pre"): mnsUtils.setAttr(self.currentPlgNode.pre, self.pre_cbx.isChecked())

	def runScript(self):
		"""'Run Script' button trigger.
		"""

		exec(self.actionScript_te.toPlainText())

	def updateActionScript(self):
		"""Button Action-script update requested trigger.
		"""

		if self.currentPlgNode:
			if self.currentPlgNode.hasAttr("actionScript"): mnsUtils.setAttr(self.currentPlgNode.actionScript, self.actionScript_te.toPlainText())

	def clearScript(self):
		"""'Clear' (ActionScript) button trigger.
		"""

		self.actionScript_te.clear()
		self.updateActionScript()

	# controls select #
	def addSceneSelectedControls(self):
		"""Add current scene selection into the controls to select list.
		"""

		currentControls = [self.controls_lst.item(itemIdx).text() for itemIdx in range(self.controls_lst.count())]
		currentSel = pm.ls(sl = True)
		if currentSel:
			for control in currentSel:
				if control not in currentControls:
					self.controls_lst.addItem(control.nodeName())
		self.updateControlsSelect()

	def removeSceneSelectedControls(self):
		"""Remove current selection from the controls list.
		"""

		currentSelected = self.controls_lst.selectedItems()
		if currentSelected:
			toRemove = []
			for itemIdx in range(self.controls_lst.count()):
				if self.controls_lst.item(itemIdx).isSelected(): toRemove.append(itemIdx)
			if toRemove:
				for itemIdx in reversed(toRemove):
					self.controls_lst.takeItem(itemIdx)
		self.updateControlsSelect()

	def clearControls(self):
		"""'Clear' (Controls Select) button trigger.
		"""

		self.controls_lst.clear()
		self.updateControlsSelect()

	def replaceControls(self):
		"""Replace current 'controls list' with the current scene selection.
		"""

		self.controls_lst.clear()
		self.addSceneSelectedControls()

	def selectControls(self):
		"""Select current controls list btn trigger.
		"""

		pm.select(d = True)
		allControls = [self.controls_lst.item(itemIdx).text() for itemIdx in range(self.controls_lst.count())]
		if allControls:
			controlsToSelect = []

			for control in allControls:
				control = mnsUtils.checkIfObjExistsAndSet(obj = control)
				if control: controlsToSelect.append(control)
			if controlsToSelect: pm.select(controlsToSelect, r = True)

	####### load window #######
	def loadWindow(self):
		"""Show windoe method.
		"""

		mnsLog.log("mnsPickerSettings", svr = 0)
		self.show()

def loadPlgSettings():
	"""Load the PLG Settings UI from globals, avoid UI duplication.
	"""
	
	if pm.window("MnsPLGSettingsUI", exists=True):
		try:
			pm.deleteUI("MnsPLGSettingsUI")
		except:
			pass

	pickerSettingsWin = MnsPLGSettingsUI()
	pickerSettingsWin.loadWindow()
