"""=== Author: Assaf Ben Zur ===
Core MNS Utility UI
This UI will allow the user to search though all available function within a given library and build a dynamic UI for it, based on it's arguments and keyword arguments drawen as 'type' QObjects into a new UI window.
This UI class will search thorugh the default library (mns), although has functionallity to add any library into the search.
IMPORTANT: Any given custom library needs to follow the mns code structure convension in order to work and sraw properly. Please refer to some code examples.

The main process of this UI class is:
	- Load the UI
	- procedurally look through the given libraries and add any found python defenition into the UI list.
	- Uppon a 'UI creation' call (via the button or souble-click):
		- Deconstruct the selected defenition into mandatory arguments and keyword arguments
		- Build a new UI based on the parameters got.
	- Uppon a 'Run' call:
		- Re-construct the function's argument based on the UI fields and recompile into a string
		- Call the selected function using the complied arguent string

Features:
	- Prefs tab to control the UI's behavior.
	- Directory addition
	- Indepentent custom '.py' files add
	- Library reload
	- 'Default Prefs restore'
	- Settings export/import
	- Function 'pinning' (Global, session independent)
	- UI features - Search, Case-Sensative display, Pinned view only, clear all pinns
	- 'dev mode':
		- When set to False (default) the UI call will create a new UI only if it han't been created before- 
		meaning that the UI objects are kept within the UI class, and when closed will not lose their user-set values. 
		When called again, the UI will simply re-load- not re-create to keep previous set values. The function will not be read again to build.

		When set to True, instead of re-loading of a previously created UI- it will be deleted- and recreated, READING THE FUNCTION AGAIN.
		This allows the user to re-read a function every time the UI is called- that means that all previous value set will be lost- as the UI rebuilds it will set all items to default value.
		This gives a very fast way of developing a function- not needing to re-load maya after edit-
		The UI will rebuild based on any change made to the defenition code, adding any new items or running a different fuctionallity every run call.
		Use this feature when writing or developing a new fuction."""

#global dependencies


from maya import cmds
import pymel.core as pm

import importlib, pkgutil, sys, os, json, glob, imp, shutil, time, zipfile
import inspect as ins
from os import listdir
from os.path import isfile, join, dirname, abspath
from collections import OrderedDict
from inspect import getmembers, isfunction

#mns dependencies
from ...core.globals import *
if GLOB_pyVer > 2: from importlib import reload
import mansur as mns
from ...core import log as mnsLog
from .. import dynUI as mnsDynUI
reload(mnsDynUI)
from ...core import UIUtils as mnsUIUtils
from ...core import utility as mnsUtils
from ...gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore
else:
	from PySide2 import QtGui, QtCore


form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "defSearch.ui")

class MnsDefSearch(form_class, base_class):
	"""Main UI Class
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		#initialize UI
		super(MnsDefSearch, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsDefSearch") 
		iconDir = GLOB_guiIconsDir + "/logo/mansur_01.png"
		self.iconLbl.setPixmap(QtGui.QPixmap(iconDir))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)

		mnsLog.log("initializing MnsDefSearch", svr = 0)
		self.pinnedFilePath = None
		self.initializePinnedDir()
	
		self.loadedWindows = {}
		self.packages = [mns]
		self.rawLib = []
		self.library = []
		self.funList = []
		self.pinnedFunList = []
		self.pinnedFunDict = OrderedDict()
		self.loadList()
		#methods
		self.connectSignals()
		mnsGui.setGuiStyle(self, "Dynamic UI Creator")

	def initializePinnedDir(self):
		self.pinnedFilePath = mnsUtils.locatePreferencesDirectory() + "/defSearchPinned.json"
		if not os.path.isfile(self.pinnedFilePath): mnsUtils.writeJson(mnsUtils.locatePreferencesDirectory(), "defSearchPinned", [])

	def connectSignals(self):
		"""Connect all UI signals
		"""

		self.connect(self.txtFldSearch, QtCore.SIGNAL('editingFinished()'), self.updateResults)
		self.txtFldSearch.textChanged.connect(self.updateResults)
		self.connect(self.cbxCase, QtCore.SIGNAL('stateChanged(int)'), self.updateResults)
		self.connect(self.btnClear, QtCore.SIGNAL('released()'), self.clearResults)
		self.connect(self.btnCreateUI, QtCore.SIGNAL('released()'), self.createUI)
		self.lstvResults.doubleClicked.connect(self.createUI)
		self.lstvResults.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.lstvResults.customContextMenuRequested.connect(self.pin)
		self.connect(self.btn_clearPins, QtCore.SIGNAL('released()'), self.clearPins)
		self.connect(self.btn_pin, QtCore.SIGNAL('released()'), self.pin)
		self.connect(self.btnReload, QtCore.SIGNAL('released()'), self.reloadResults)
		self.pinnedOnlyCbx.stateChanged.connect(self.pinnedOnlyView)

	def pinnedOnlyView(self, state):
		"""Pinned only view trigger method.
		"""

		self.updateResults()

	def createUI(self):
		"""Main dynamic UI creation method trigger based on current selection.
		"""

		if self.lstvResults.currentItem() is not None:
			index = self.library.index(self.lstvResults.currentItem().text())
			module = sys.modules[self.rawLib[index][1].__module__]
			reload (module)

			winName = self.rawLib[index][1].__name__
			if self.devModeCbx.isChecked():
				if pm.window(winName, exists = True): 
					try:
						pm.deleteUI(winName)
					except:
						pass
				if winName in self.loadedWindows: del self.loadedWindows[winName]
				win = mnsDynUI.MnsDynamicDefUI(self.rawLib[index][1])
				win.loadUI()
				self.loadedWindows.update({winName: win})
			else:
				if winName in self.loadedWindows:
					self.loadedWindows[winName].loadUI()
				else:
					win = mnsDynUI.MnsDynamicDefUI(self.rawLib[index][1])
					win.loadUI()
					self.loadedWindows.update({winName: win})	

	def pin(self):
		"""Pin call method trigger based on current selection.
		"""

		pinnedFunList = json.load(open(self.pinnedFilePath))
		if self.lstvResults.currentItem() is not None:
			if (self.lstvResults.currentItem().text()) in (pinnedFunList):
				self.lstvResults.currentItem().setForeground(QtGui.QColor('lightgray'))
				boldFont=QtGui.QFont()
				boldFont.setBold(False)
				self.lstvResults.currentItem().setFont(boldFont)
				pinnedFunList.remove(self.lstvResults.currentItem().text())
			else:
				self.lstvResults.currentItem().setForeground(QtGui.QColor('white'))
				boldFont=QtGui.QFont()
				boldFont.setBold(True)
				self.lstvResults.currentItem().setFont(boldFont)
				pinnedFunList.append(self.lstvResults.currentItem().text())

			pinnedFunList = sorted(pinnedFunList)
			with open (self.pinnedFilePath, 'w') as p:
				pass
			with open (self.pinnedFilePath, 'w') as p:
				json.dump(pinnedFunList, p, indent =4)
		self.updateResults()

	def clearPins(self):
		"""Clear all pinns method trigger.
		"""

		with open (self.pinnedFilePath, 'w') as p:
			pass
		with open (self.pinnedFilePath, 'w') as p:
				json.dump([], p, indent =4)
		self.updateResults()

	def updateResults(self):
		"""Main UI view update method trigger.
		The UI list will be updated from this method based on the current UI state and prefs"""

		pinnedOnly = self.pinnedOnlyCbx.isChecked()
		#clear
		filterTxt = self.txtFldSearch.text()
		self.lstvResults.clear()
		newItemList = []

		#handle Pinned
		pinnedFunList = json.load(open(self.pinnedFilePath))
		newItemList.extend(pinnedFunList)
		self.lstvResults.addItems(newItemList)

		for i in range(0,self.lstvResults.count()):
			self.lstvResults.item(i).setForeground(QtGui.QColor('white'))
			boldFont=QtGui.QFont()
			boldFont.setBold(True)
			self.lstvResults.item(i).setFont(boldFont)

		#filter and add
		if not pinnedOnly:
			newItemList = []
			for item in self.funList:
				if self.cbxCase.isChecked():
					if filterTxt in item:
						if item not in pinnedFunList:
							newItemList.append(item) 
				else:
					if(filterTxt.lower() in item.lower()):
						if item not in pinnedFunList:
							newItemList.append(item) 
			self.lstvResults.addItems(newItemList)
		
	def clearResults(self):
		"""Clear Serach method trigger.
		"""

		self.txtFldSearch.clear()
		self.updateResults()

	def loadWindow(self):
		"""Main UI load
		"""
		self.show()
		
	def import_submodules(self, package, recursive=True):
		"""Recursive method to walk thorugh a given package and sub-packages to store all sub-directories within.
		"""

		if isinstance(package, str):
			try:
				package = importlib.import_module(package)
			except:
				pass

		results = {}
		for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
			skip = 0
			full_name = package.__name__ + '.' + name
			try:
				results[full_name] = importlib.import_module(full_name)
			except:
				skip = 1
				#error1 = str(sys.exc_info())
				#mnsLog.log(("Trying to import module errored" + error1), svr = 0)
				pass

			if recursive and is_pkg:
				if skip != 1:
					results.update(self.import_submodules(full_name))

		#return;dict
		return results

	def addPackageToResults(self, package):   
		"""Package addition method trigger.
		"""

		pkgMods = self.import_submodules(package.__name__)
		for mod in pkgMods:
			functions_list = [o for o in getmembers(pkgMods[mod]) if isfunction(o[1])]
			for fun in functions_list:
				self.library.append(fun[0])
				fun = fun + (mod,)
				self.rawLib.append(fun)

	def addModuleToResults(self, module): 
		"""Module add method trigger.
		"""

		functions_list = [o for o in getmembers(module) if isfunction(o[1])]
		for fun in functions_list:
			self.library.append(fun[0])
			fun = fun + (module,)
			self.rawLib.append(fun)

	def loadList(self):
		"""Main list load method.
		A wrapper to filter all functions based on prefs selected and update the UI."""

		mnsLog.log("loading library", svr = 1)
		listLoadTimer = pm.timerX()
		self.importModules()
		for r in self.library:
			if r != 'dirname' and r != 'abspath':
				if r not in self.funList:
					self.funList.append(r)
		self.funList = sorted(self.funList)
		timeF = pm.timerX(st = listLoadTimer)
		mnsLog.log(('Loaded search library in ' + timeF.__str__() + ' seconds.'), svr = 1)
		self.updateResults()

	def reloadResults(self):
		"""Wrapper re-load method.
		"""

		self.txtFldSearch.clear()
		self.lstvResults.clear()
		self.funList = []
		self.library = []
		self.loadList()

	def importModules(self):
		"""Import modules wrapper.
		"""

		for p in self.packages:
			self.addPackageToResults(p) 

def loadDefSearch():
	"""Load the Def Serach UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsDefSearch")

	mnsDefSearchWin = MnsDefSearch()
	mnsDefSearchWin.loadWindow()
	if previousPosition: mnsDefSearchWin.move(previousPosition)