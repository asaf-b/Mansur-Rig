"""Account UI Class.
	=== Author: Assaf Ben Zur ===
	Licensing utility.

	//RETRUN STATUS CODES
	//
	// 0 - Process failed
	// 1 - username/password are empty or not provided
	// 2 - Invalid Username
	// 3 - Invalid Password
	// 4 - Couldn't find related license for user.
	// 5 - Invalid License
	// 6 - All available seats are already taken.
	// 7 - Couldn't find node-lock for current HUID.
	//
	//
	// 15 - License validated.
	// 16 - Log-Out successful.

"""

#global dependencies
import os, json, platform, zipfile

from maya import cmds
if int(cmds.about(version = True)) > 2024:
	import shiboken6 as shiboken2
else:
	import shiboken2

try:
	import urllib2
except ImportError:
	import urllib as urllib2

import maya.OpenMayaUI as apiUI


from maya import cmds
import pymel.core as pm
 
from os.path import dirname, abspath
from maya import mel
from functools import partial

#mns dependencies
from ..core.globals import *
from ..core import utility as mnsUtils
from ..core import UIUtils as mnsUIUtils
from ..core import log as mnsLog
from ..gui import gui as mnsGui

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore, QtWidgets
else:
	from PySide2 import QtGui, QtCore, QtWidgets

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "versionManager.ui")
class MnsVersionManager(form_class, base_class):
	"""pluginRelease UI class
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		super(MnsVersionManager, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsVersionManager") 
		self.setWindowFlags(QtCore.Qt.Window) 

		#initalize icons
		iconSDir = GLOB_guiIconsDir + "/logo/mansur_01.png"
		self.iconLbl.setPixmap(QtGui.QPixmap(iconSDir))
		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)

		#locals
		self.currentRootDir = None
		self.currentVersion = "dev"

		#run methods
		self.initializeView()
		mnsGui.setGuiStyle(self, "Version Manager")
		self.connectSignals()
		self.initializeVersion()

	#initalize UI methods
	def resizeEvent(self, QResizeEvent):
		mnsGui.windowResizeEvent(self, QResizeEvent)
			
	def closeEvent(self, QCloseEvent):
		mnsGui.windowCloseEvent(self, QCloseEvent)

	def connectSignals(self):
		"""Connect all the UI signals
		"""

		self.versions_trv.itemClicked.connect(self.setButtonsState)
		self.download_btn.released.connect(self.downloadVersion)
		self.install_btn.released.connect(self.installVersion)
		self.openInstallDir_btn.released.connect(self.goToFolder)

	def downloadVersion(self):
		if self.versions_trv.currentItem():
			if not self.versions_trv.currentItem().text(2):
				if mnsUtils.isPluginLoaded("mnsLicDigest"):
					targetDirectory = self.currentRootDir + "/" + self.versions_trv.currentItem().text(0) + ".zip"
					filedata = None
					try:
						filedata = urllib2.urlopen(cmds.mnsDist(p = platform.system().lower(), dv = self.versions_trv.currentItem().text(0) + ".zip"))
					except:
						try:
							filedata = urllib2.request.urlopen(cmds.mnsDist(p = platform.system().lower(), dv = self.versions_trv.currentItem().text(0) + ".zip"))
						except:
							import urllib.request
							filedata = urllib.request.urlopen(cmds.mnsDist(p = platform.system().lower(), dv = self.versions_trv.currentItem().text(0) + ".zip"))

					datatowrite = filedata.read()
					with open(targetDirectory, 'wb') as f:
						f.write(datatowrite)

					if os.path.isfile(targetDirectory):
						with zipfile.ZipFile(targetDirectory, 'r') as zipObj:
							zipObj.extractall(self.currentRootDir)
					os.remove(targetDirectory)
					loadVersionManager()

	def installVersion(self):
		if self.versions_trv.currentItem():
			if self.versions_trv.currentItem().text(2) == "i":
				for root, dirs, files in os.walk(self.currentRootDir + "/" + self.versions_trv.currentItem().text(0)):
					for file in files:
						if file == "mansurRig_DragAndDrop_install.mel":
							filePath = (root + "/" + file).replace("\\", "/")
							mel.eval("source \"" + filePath + "\"")
							self.destroy()

	def setButtonsState(self, item, culomn):
		self.download_btn.setEnabled(False)
		self.install_btn.setEnabled(False)

		if item:
			if not item.text(2): 
				self.download_btn.setEnabled(True)
			elif item.text(2) == "i":
				self.install_btn.setEnabled(True)

	def initializeView(self):
		self.versions_trv.setColumnWidth(0, 150)
		self.versions_trv.setColumnHidden(2, True)
			
		self.lgndCurrent_lbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/general/licValid.png"))
		self.lgndCurrent_lbl.setScaledContents(True)
		self.lgndLocal_lbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/general/down_arrow.png"))
		self.lgndLocal_lbl.setScaledContents(True)
		self.lgndOnline_lbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/general/nonExistingVer.png"))
		self.lgndOnline_lbl.setScaledContents(True)
		self.openInstallDir_btn.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/mayaResource/openLoadGeneric_100.png"))
	
	def goToFolder(self):
		try: os.startfile(self.currentRoot_le.text())
		except: pass

	def getInstallledVersions(self):
		installedVersions = []
		if self.currentRootDir:
			for ver in os.listdir(self.currentRootDir):
				if "mansurRig" in ver:
					if "." in ver and "_" in ver:
						versionString = ver
						installedVersions.append(versionString)
		return installedVersions

	def initializeVersion(self):
		self.currentRootDir = dirname(dirname(dirname(__import__(__name__.split('.')[0]).__path__[0]))).replace("\\", "/")
		self.currentRoot_le.setText(self.currentRootDir)
		currentRelativePath = dirname(dirname(__import__(__name__.split('.')[0]).__path__[0])).replace("\\", "/")
		
		if "_" in currentRelativePath and "." in currentRelativePath:
			self.currentVersion = currentRelativePath.split("/")[-1]

		installedVersions = self.getInstallledVersions()

		versionsReturn = cmds.mnsDist(p = platform.system().lower(), lv = True)
		if versionsReturn:
			availableVersions = json.loads(versionsReturn)
			for ver in availableVersions:
				versionItem = QtWidgets.QTreeWidgetItem(self.versions_trv, [ver["key"].split(".zip")[0], '{:,}'.format(round(ver["filesize"] / 1000)) + " KB"])
				
				ver = ver["key"].split(".zip")[0]
				if ver == self.currentVersion:
					versionItem.setIcon(0, QtGui.QIcon(os.path.join(GLOB_guiIconsDir, "general/licValid.png")))
					versionItem.setForeground(0, QtGui.QColor('green'))
					versionItem.setForeground(1, QtGui.QColor('green'))
					versionItem.setText(2, "c")
				elif ver in installedVersions:
					versionItem.setIcon(0, QtGui.QIcon(os.path.join(GLOB_guiIconsDir, "general/down_arrow.png")))
					versionItem.setText(2, "i")
				else:
					versionItem.setIcon(0, QtGui.QIcon(os.path.join(GLOB_guiIconsDir, "general/nonExistingVer.png")))
					versionItem.setForeground(0, QtGui.QColor('grey'))
					versionItem.setForeground(1, QtGui.QColor('grey'))

	def loadWindow(self):
		""" Main window load.
		"""
		self.show()
		
def loadVersionManager():
	"""Load the Preferences UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsVersionManager")

	vmWin = MnsVersionManager()
	vmWin.loadWindow()
	if previousPosition: vmWin.move(previousPosition)
