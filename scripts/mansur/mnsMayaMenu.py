"""=== Author: Assaf Ben Zur ===
Mansur- Maya menu creator.
This contains the mansur menu class, as well as the entire UI build and connections."""

#dependencies
#Maya


from maya import cmds
import pymel.core as pm

import maya.OpenMayaUI as apiUI

#global
import os, webbrowser, platform

if int(cmds.about(version = True)) > 2024:
	import shiboken6 as shiboken2
else:
	import shiboken2

from .core import globals as mnsGlobals
if mnsGlobals.GLOB_pyVer > 2:
	from importlib import reload

#Qt
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtWidgets, QtCore, QtGui
	from PySide6.QtWidgets import QMenu
else:	
	from PySide2 import QtWidgets, QtCore, QtGui
	from PySide2.QtWidgets import QMenu
	
#internal
from .core import UIUtils as mnsUIUtils
from .core import utility as mnsUtils
from .globalUtils.defSearch import defSearch as mnsDefSearch
reload(mnsDefSearch)
from .globalUtils import dynUI as mnsDynUI
reload(mnsDynUI)
from .preferences import preferences as mnsPrefs
from .block.picker2 import picker2 as mnsPicker
from .block.picker2 import plgSettings as mnsPlgSettings
from .block import blockBuildUI as mnsBlkBuildUI
from .block.moduleVisUI import moduleVisUI as mnsModuleVisUI
reload(mnsModuleVisUI)
from .block.cnsTool import cnsTool as mnsCnsTool
reload(mnsCnsTool)
from .block.volumeJointsUI import volumeJointsUI as mnsVolJntUI
reload(mnsVolJntUI)
from .block.LODsTool import LODsTool as mnsLODsTool
reload(mnsLODsTool)
from .block.characterDefenition import characterDefenitionUI as mnsCharDef
reload(mnsCharDef)
from .block.springTool import mnsSpringTool
reload(mnsSpringTool)
from .block.spacesTool import mnsSpacesTool
reload(mnsSpacesTool)
from .globalUtils.facialMocap import mnsFacialMocapTool
reload(mnsFacialMocapTool)
from .globalUtils.animationExporter import mnsAnimationExporter as mnsAnimExporter
reload(mnsAnimExporter)
from .globalUtils.jointRadiusTool import mnsJointRadiusTool
reload(mnsJointRadiusTool)

#Qt
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtWidgets, QtCore, QtGui
	from PySide6.QtWidgets import QMenu
else:
	from PySide2 import QtWidgets, QtCore, QtGui
	from PySide2.QtWidgets import QMenu

def createLogoTitle(menuWidget = None, parent = mnsUIUtils.get_maya_window()):
	"""Create the logo title in the menu UI.
	"""

	if menuWidget and parent:
		horizontalLayout =  QtWidgets.QHBoxLayout()
		logoLbl = QtWidgets.QLabel(parent)
		logoLbl.setPixmap(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/mnsMenuIcon.png"))
		widAction = QtWidgets.QWidgetAction(parent)
		widAction.setDefaultWidget(logoLbl)
		menuWidget.addAction(widAction)

def createMenuItems(menuWidget = None, parentWid = mnsUIUtils.get_maya_window()):
	"""Create all menu items and sub-items.
	"""


	if menuWidget and parentWid:
		action = menuWidget.addAction(parentWid.tr("Block Builder"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/logo/block_t5_noText.png")))
		action.triggered.connect(mnsBlkBuildUI.loadBlock)

		######   block tools   #########
		menuWidget.addSeparator()
		blockMenu = menuWidget.addMenu(parentWid.tr("Block Tools"))
		blockMenu.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/blockTools.png")))
		blockMenu.setTearOffEnabled(True)

		action = blockMenu.addAction(parentWid.tr("Volume Joints UI"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/volJointsUI.png")))
		action.triggered.connect(mnsVolJntUI.loadVolumeJointsUI)

		action = blockMenu.addAction(parentWid.tr("LODs Tool"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/lodsToolIcon.png")))
		action.triggered.connect(mnsLODsTool.loadLodsTool)

		action = blockMenu.addAction(parentWid.tr("Dynamic UI Creator"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/defSearchIcon.png")))
		action.triggered.connect(mnsDefSearch.loadDefSearch)

		action = blockMenu.addAction(parentWid.tr("Joint Radius"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/jointRadiusIcon.png")))
		action.triggered.connect(mnsJointRadiusTool.loadJointRadiusTool)

		action = blockMenu.addAction(parentWid.tr("Preferences"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/preferences.png")))
		action.triggered.connect(mnsPrefs.loadPreferences)

		action = blockMenu.addAction(parentWid.tr("Reload Block"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/direction.png")))
		action.triggered.connect(mnsUtils.reloadLib)

		######   Anim tools   #########
		menuWidget.addSeparator()
		animMenu = menuWidget.addMenu(parentWid.tr("Animation Tools"))
		animMenu.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/bounce.png")))
		animMenu.setTearOffEnabled(True)

		action = animMenu.addAction(parentWid.tr("Picker"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/pickerIcon.png")))
		action.triggered.connect(mnsPicker.loadPicker)

		action = animMenu.addAction(parentWid.tr("Control Visibility UI"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/moduleVisUI.png")))
		action.triggered.connect(mnsModuleVisUI.loadModuleVisUI)

		action = animMenu.addAction(parentWid.tr("CNS Tool"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/cnsTool.png")))
		action.triggered.connect(mnsCnsTool.loadCnsTool)

		action = animMenu.addAction(parentWid.tr("Spring Tool"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/springToolIcon.png")))
		action.triggered.connect(mnsSpringTool.loadSpringTool)

		action = animMenu.addAction(parentWid.tr("Spaces/IK-FK Tool"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/spacesToolIcon.png")))
		action.triggered.connect(mnsSpacesTool.loadSpacesTool)

		action = animMenu.addAction(parentWid.tr("Facial Mocap Tool (Beta)"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/facial-recognition.png")))
		action.triggered.connect(mnsFacialMocapTool.loadFacialMocapTool)

		action = animMenu.addAction(parentWid.tr("Game Exporter"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/gameExporter.png")))
		action.triggered.connect(mnsAnimExporter.loadAnimationExporter)

		######   About   #########
		menuWidget.addSeparator()
		aboutMenu = menuWidget.addMenu(parentWid.tr("Help"))
		aboutMenu.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/logo/mansur_logo_noText.png")))
		aboutMenu.setTearOffEnabled(True)
				
		action = aboutMenu.addAction(parentWid.tr("About"))
		action.triggered.connect(mnsUIUtils.createAboutWindow)
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/question.png")))
		
		action = aboutMenu.addAction(parentWid.tr("Website"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/website.png")))
		action.triggered.connect(lambda: webbrowser.open("http://mansur-rig.com"))

		action = aboutMenu.addAction(parentWid.tr("User-Guides"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/information.png")))
		action.triggered.connect(lambda: webbrowser.open("https://docs.mansur-rig.com/userGuides/System-Requirements/"))
		
		action = aboutMenu.addAction(parentWid.tr("Code Documentation"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/paper.png")))
		action.triggered.connect(lambda: webbrowser.open("https://docs.mansur-rig.com/Maya-Plugins/"))
		
		action = aboutMenu.addAction(parentWid.tr("Tutorials"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/play.png")))
		action.triggered.connect(lambda: webbrowser.open("https://mansur-rig.com/tutorials/"))
		
		action = aboutMenu.addAction(parentWid.tr("FAQ"))
		action.setIcon(QtGui.QIcon(QtGui.QPixmap(mnsGlobals.GLOB_guiIconsDir + "/menu/faq.png")))
		action.triggered.connect(lambda: webbrowser.open("https://docs.mansur-rig.com/faq/FAQ/"))

class mnsMayaQtWindowTearoffCopy(QtWidgets.QMainWindow):
	"""an override tearoff copy menu, this class to override the default tearoff action
	"""

	def __init__(self, parent=None, cursorOffset = (0,0)):
		super(mnsMayaQtWindowTearoffCopy, self).__init__(parent)

		if pm.window("mnsMayaMenuTearoff", exists=True):
			try:
				pm.deleteUI("mnsMayaMenuTearoff")
			except:
				pass

		self.setObjectName("mnsMayaMenuTearoff")

		self.menuObj = QtWidgets.QMenu()
		createLogoTitle(self.menuObj, self)
		createMenuItems(self.menuObj, self)

		self.lastSignal = None

		self.setCentralWidget(self.menuObj)
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle("Mansur Rig")

		self.menuObj.installEventFilter(self)
		self.move(QtGui.QCursor().pos() - cursorOffset)

		self.show()

	def eventFilter(self, source, event):
		if event.type() is QtCore.QEvent.Type.MouseButtonRelease and self.lastSignal is QtCore.QEvent.Type.Leave:
			self.lastSignal = event.type()
			return True
		else:
			self.lastSignal = event.type()
			return super(QtWidgets.QWidget, self).eventFilter(source, event)

class mnsMayaQtWindow(QtWidgets.QMainWindow):
	"""Mansur Main maya menu item
	"""

	def __init__(self, name, label='Mansur Rig', parent=None):
		parent = parent or mnsUIUtils.get_maya_window()
		#QtWidgets.QWidget.__init__(self, parent)
		super(mnsMayaQtWindow, self).__init__(parent)

		#set name vars
		label = label or name
		self.name = name.replace(' ', '_')

		#convert to qMenu
		self.menuObj = self.toQtObject(self.name)
		self.menuObj.installEventFilter(self)
		self.menuObj.setTearOffEnabled(True)
		self.menuObj.setWindowTitle(label)

		#add title
		createLogoTitle(self.menuObj, self)
		createMenuItems(self.menuObj, self)
		mnsUtils.reloadLib()

	def eventFilter(self, source, event):
		"""Override event filter to catch the tear off to override it's event.
		"""
		
		mayaWin = mnsUIUtils.get_maya_window()

		tearOffRequested = False
		if event.type() == QtCore.QEvent.MouseButtonRelease:
			if self.menuObj.isTearOffEnabled():
				tearRect = QtCore.QRect(0,0,self.menuObj.width(),31)
				if tearRect.contains(event.pos()):
					tearOffRequested = True
		
		if tearOffRequested:
			self.menuObj.close()
			mnsMayaQtWindowTearoffCopy(mayaWin, event.pos())
			return True
		else:
			return super(QtWidgets.QWidget, self).eventFilter(source, event)
		
	def toQtObject(self, mayaName):
		"""Convert the created maya pm.menu object to a PyQt QMenu Object.
		"""

		ptr = apiUI.MQtUtil.findControl(mayaName)
		if not ptr:
			ptr = apiUI.MQtUtil.findLayout(mayaName)
		if not ptr:
			ptr = apiUI.MQtUtil.findMenuItem(mayaName)
		if ptr:
			return shiboken2.wrapInstance(int(ptr), QtWidgets.QMenu)

def createMansurMayaMenu(label = "Mansur Rig"):
	if pm.menu(label, exists=True): 
		try:
			pm.deleteUI(label)
		except:
			pass
	mayaWindow = pm.language.melGlobals['gMainWindow']
	pm.menu(label, l=label, parent=mayaWindow, tearOff=True, allowOptionBoxes=True)

	mnsMayaQtWindow(label)