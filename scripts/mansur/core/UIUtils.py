"""=== Author: Assaf Ben Zur ===
UI Utility function assembly.
This module holds all UI utility functions as well s any QT dynamic draw functions.
All UI functions should be held in here for multi-usage of the same UI draw functions.

This module also holds the QT ui dynamic conversion to '.py' and the 'get_maya_window' function.
"""

#global dependencies
import maya.OpenMayaUI as apiUI
try:
	from cStringIO import StringIO ## for Python 2
except ImportError:
	from io import StringIO ## for Python 3
import xml.etree.ElementTree as xml


from maya import cmds
import pymel.core as pm

import os, math, subprocess, json

if int(cmds.about(version = True)) > 2024:
	import shiboken6 as shiboken2
else:
	import shiboken2

from tempfile import mkstemp
from os import fdopen, remove
from os.path import dirname
from functools import partial

#mns dependencies
from . import string as mnsString
from . import utility as mnsUtils
from .prefixSuffix import *

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtWidgets, QtCore
	from PySide6.QtWidgets import QTreeWidgetItem
	from PySide6.QtWidgets import QFrame
	from PySide6.QtCore import QRegularExpression as QRegExp
else:
	from PySide2 import QtGui, QtWidgets, QtCore
	from PySide2.QtWidgets import QTreeWidgetItem
	from PySide2.QtWidgets import QFrame
	from PySide2.QtCore import QRegExp

#python3 exceptions
import sys
if sys.version_info[0] >= 3:
	unicode = str

def get_maya_window():
	"""Main maya window get for a global UI parent
	"""

	version = int(cmds.about(v = True))

	if "mnsMayaWin" in globals():
		return globals()["mnsMayaWin"]

	ptr = apiUI.MQtUtil.mainWindow()
	if ptr is not None:
		retWin = shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
		globals().update({"mnsMayaWin": retWin})

		return retWin

	#return;qtWindow (main maya window as a qt window)

class CollapsibleFrameWidget(QFrame):
	"""Collapsible frame Widget class.
	This is a wrapper widget that allows for a collapisble frame to be built.
	The QFrame object will allow for Layouts to be inserted into the Collapsible frame, inserting any widgets within it, 
	collapsing and expanding it by a click trigger (from the user).
	"""

	def __init__(self, parent=None, title=None):
		QFrame.__init__(self, parent=parent)

		self._is_collasped = True
		self._title_frame = None
		self._content, self._content_layout = (None, None)

		self._main_v_layout = QtWidgets.QVBoxLayout(self)
		self._main_v_layout.setContentsMargins(0, 0, 0, 0)
		self._main_v_layout.addWidget(self.initTitleFrame(title, self._is_collasped))
		self._main_v_layout.addWidget(self.initContent(self._is_collasped))

		self.initCollapsable()

		self.clickedSignal = QtCore.Signal('clicked()')

	def initTitleFrame(self, title, collapsed):
		self._title_frame = self.TitleFrame(title=title, collapsed=collapsed)

		return self._title_frame

	def initContent(self, collapsed):
		self._content = QtWidgets.QWidget()
		
		self._content_layout = QtWidgets.QVBoxLayout()
		self._content_layout.setObjectName("CollapsibleFrameWidgetContent")
		self._content_layout.setContentsMargins(0, 0, 0, 0)

		self._content.setLayout(self._content_layout)
		self._content.setVisible(not collapsed)

		return self._content

	def addWidget(self, widget):
		self._content_layout.addWidget(widget)

	def initCollapsable(self):
		QtCore.QObject.connect(self._title_frame, QtCore.SIGNAL('clicked()'), self.toggleCollapsed)

	def toggleCollapsed(self):
		self._content.setVisible(self._is_collasped)
		self._is_collasped = not self._is_collasped
		self._title_frame._arrow.setArrow(int(self._is_collasped))

	class TitleFrame(QFrame):
		def __init__(self, parent=None, title="", collapsed=False):
			QFrame.__init__(self, parent=parent)

			self.setMinimumHeight(24)
			self.setMaximumHeight(24)
			self.setAccessibleName("dropDownTitle")
			#self.setStyleSheet("border:1px solid rgb(41, 41, 41); border-radius: 5px; background-color: #50686d")
			
			self._hlayout = QtWidgets.QHBoxLayout(self)
			self._hlayout.setContentsMargins(0, 0, 0, 0)
			self._hlayout.setSpacing(0)

			self._arrow = None
			self._title = None

			self._hlayout.addWidget(self.initArrow(collapsed))
			self._hlayout.addWidget(self.initTitle(title))

		def initArrow(self, collapsed):
			self._arrow = CollapsibleFrameWidget.Arrow(collapsed=collapsed)
			return self._arrow

		def initTitle(self, title=None):
			self._title = QtWidgets.QLabel(title)
			self._title.setMinimumHeight(22)
			self._title.move(QtCore.QPoint(22, 0))
			return self._title

		def mousePressEvent(self, event):
			try:
				self.emit(QtCore.SIGNAL('clicked()'))
				return super(CollapsibleFrameWidget.TitleFrame, self).mousePressEvent(event)
			except: pass
			
	class Arrow(QFrame):
		def __init__(self, parent=None, collapsed=False):
			QFrame.__init__(self, parent=parent)

			self.setMaximumSize(24, 24)

			# horizontal == 0
			self._arrow_horizontal = (QtCore.QPointF(7.0, 8.0), QtCore.QPointF(17.0, 8.0), QtCore.QPointF(12.0, 13.0))
			# vertical == 1
			self._arrow_vertical = (QtCore.QPointF(8.0, 7.0), QtCore.QPointF(13.0, 12.0), QtCore.QPointF(8.0, 17.0))
			# arrow
			self._arrow = None
			self.setArrow(int(collapsed))

		def setArrow(self, arrow_dir):
			if arrow_dir: self._arrow = self._arrow_vertical
			else: self._arrow = self._arrow_horizontal

		def paintEvent(self, event):
			painter = QtGui.QPainter()
			painter.begin(self)
			painter.setBrush(QtGui.QColor(192, 192, 192))
			painter.setPen(QtGui.QColor(64, 64, 64))
			painter.drawPolygon(self._arrow)
			painter.end()

class extraChannelsDelegate(QtWidgets.QItemDelegate):
	def __init__(self, parent=None, *args):
		QtWidgets.QItemDelegate.__init__(self, parent, *args)

	def createEditor(self, parent, option, index):
		lineEdit = QtWidgets.QLineEdit(parent)

		validator = None
		if int(cmds.about(version = True)) > 2024: 
			validator = QtGui.QRegularExpressionValidator("[A-Za-z0-9_]*")
		else:
			validator = QtGui.QRegExpValidator("[A-Za-z0-9_]*")

		if validator:
			lineEdit.setValidator(validator)
			return lineEdit

	def setModelData(self, editor, model, index):
		name = editor.text()
		if not name: return
		model.setData(index, name.lstrip('0123456789'))

class MnsAbout(QtWidgets.QDialog):
	"""Mansur - About dialog
	"""

	def __init__(self, parent=get_maya_window(), version = "dev"):
		super(MnsAbout, self).__init__(parent)
		self.setObjectName("mnsAbout") 
		self.setWindowTitle("About Mansur")

		self.setWindowIcon(QtGui.QIcon(GLOB_guiIconsDir + "/logo/mansur_logo_noText.png"))

		layout = QtWidgets.QVBoxLayout()

		vLine = QFrame()
		vLine.setFrameShape(QFrame.HLine)
		vLine.setFrameShadow(QFrame.Sunken)
		vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
		layout.addWidget(vLine)

		iconHLay = QtWidgets.QHBoxLayout()
		spacerA = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		iconHLay.addItem(spacerA)
		iconLbl = QtWidgets.QLabel()
		iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))
		iconHLay.addWidget(iconLbl)
		spacerB = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		iconHLay.addItem(spacerB)
		layout.addLayout(iconHLay)

		vLine = QFrame()
		vLine.setFrameShape(QFrame.HLine)
		vLine.setFrameShadow(QFrame.Sunken)
		vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
		layout.addWidget(vLine)

		verHLayout = QtWidgets.QHBoxLayout()
		self.version_le = QtWidgets.QLabel("Product Version:")
		self.version_le.setFixedWidth(120)
		verHLayout.addWidget(self.version_le)
		self.versionDisplay = QtWidgets.QLineEdit()
		self.versionDisplay.setReadOnly(True)
		self.versionDisplay.setText(version)
		verHLayout.addWidget(self.versionDisplay)
		spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		verHLayout.addItem(spacer)
		layout.addLayout(verHLayout)

		textContainer = QtWidgets.QTextEdit()
		textContainer.setFixedWidth(350)
		textContainer.setFixedHeight(400)
		eulaText = getEulaText()
		textContainer.setText(eulaText)
		textContainer.setReadOnly(True)
		layout.addWidget(textContainer)

		self.close_btn = QtWidgets.QPushButton("Close")
		layout.addWidget(self.close_btn)

		self.setLayout(layout)

		self.close_btn.clicked.connect(self.destroy)
		self.show()

def applyCollapsibleWidgetsForPairing(pairing = [], expandedTabs = []):
	if pairing:
		for collapsiblePair in pairing:
			lo = collapsiblePair["lo"]
			title = collapsiblePair["title"]
			widget = collapsiblePair["widget"]
			isExapanded = collapsiblePair["isExpanded"]
			
			colWidget = CollapsibleFrameWidget(title=title)
			colWidget.addWidget(widget)
			lo.addWidget(colWidget)
			if isExapanded: 
				colWidget.toggleCollapsed()

def load_ui_type(ui_file):
	"""This function converts a '.ui' file into a '.py' file live.
	This means that all UI's are derived from a QT designer ui files that are converted directly to form the UI.
	This keeps a live connection between the '.ui' file and the actul UI in maya. Meaning that any edit or a change to the UI base needs to be done only from the QT designer, without any further action by the user.
	It reruns a baseClass and a formClass to be used when creating any UI."""

	try:
		import pyside2uic

		parsed = xml.parse(ui_file)
		widget_class = parsed.find('widget').get('class')
		form_class = parsed.find('class').text

		with open(ui_file,'r') as f:
			o = StringIO()
			frame = {}
			pyside2uic.compileUi(f, o, indent = 0)
			pyc = compile(o.getvalue(), '<string>', 'exec')
			exec(pyc) in frame

			# Fetch the base_class and form class based on their type in the xml from design
			form_class = frame['Ui_{0}'.format(form_class)]
			base_class = eval('QtWidgets.{0}'.format(widget_class))

		#return;baseClass, formClass
		return form_class, base_class
	except:
		parsed = xml.parse(ui_file)
		widget_class = parsed.find('widget').get('class')
		form_class = parsed.find('class').text

		with open(ui_file,'r') as f:
			fd, abs_path = mkstemp(suffix = ".py")
			command = "uic -g python \"" + ui_file + "\" -o " + abs_path
			subprocess.call(command, shell=True)
			
			o = StringIO()
			fileLines = list(open(abs_path, 'r'))
			o.writelines(fileLines)
			o.seek(0)

			pyc = compile(o.getvalue(), '<string>', 'exec')
			frame = {}
			exec(pyc, frame)
			
			#Fetch the base_class and form class based on their type in the xml from design
			form_class = frame['Ui_{0}'.format(form_class)]
			base_class = eval('QtWidgets.{0}'.format(widget_class))
			
			os.close(fd)
			os.remove(abs_path)

		#return;baseClass, formClass
		return form_class, base_class

def buildFormBaseClassForUI(script_dir, rel_path):
	abs_file_path = os.path.join(script_dir, rel_path)
	form_class, base_class = load_ui_type(abs_file_path)

	#return;baseClass, formClass
	return form_class, base_class

def buildStackedTabForModuleParentDir(modDirName, insertIndex, tabWidget, **kwargs):
	"""Main BLOCK dynamiuc tab builder.
	Builds a tab for a given tab parent including all the neccesary layouts within, returning the main layout that can be inserted with new q items."""

	newModuleTab = QtWidgets.QWidget()
	horizontalLayout =  QtWidgets.QVBoxLayout(newModuleTab)
	horizontalLayout.setContentsMargins(0, 0, 0, 0)
	mainLay =QtWidgets.QVBoxLayout()
	newListWidget = QtWidgets.QListWidget()
	newListWidget.setIconSize(QtCore.QSize(22,22))
	horizontalLayout.addWidget(newListWidget)
	tabWidget.insertWidget(insertIndex, newModuleTab)
	iconPath = os.path.dirname(os.path.dirname(__file__)) + "/icons/module.png"

	return newListWidget

def buildTabForModuleParentDir(modDirName, insertIndex, tabWidget, **kwargs):
	"""Main BLOCK dynamiuc tab builder.
	Builds a tab for a given tab parent including all the neccesary layouts within, returning the main layout that can be inserted with new q items."""
 
	modSet = kwargs.get("modSet", False) #arg;

	newModuleTab = QtWidgets.QWidget();

	horizontalLayout =  QtWidgets.QHBoxLayout(newModuleTab)
	horizontalLayout.setSpacing(2)

	horizontalLayout.setContentsMargins(0, 0, 0, 0)
	newScroll = QtWidgets.QScrollArea(newModuleTab)
	newScroll.setWidgetResizable(True)
	newScrollContent = QtWidgets.QWidget()
	horizontalLayout_2 = QtWidgets.QVBoxLayout(newScrollContent);
	horizontalLayout_2.setSpacing(2)

	mainLay = None
	horizontalLayout_2.setContentsMargins(2, 9, 2, 2)
	if not modSet: 
		mainLay = QtWidgets.QVBoxLayout()
		#newScroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
	else: 
		mainLay = QtWidgets.QVBoxLayout()
		mainLay.setSpacing(8)
	mainLay.setAlignment(QtCore.Qt.AlignLeft)
	horizontalLayout_2.addLayout(mainLay)
	newScroll.setWidget(newScrollContent)
	horizontalLayout.addWidget(newScroll)
	name = modDirName
	if modSet: name = modDirName

	tabWidget.insertTab(insertIndex, newModuleTab, name)

	iconPath = os.path.dirname(os.path.dirname(__file__)) + "/icons/module.png"
	tabWidget.setTabIcon(insertIndex, QtGui.QPixmap(iconPath))

	return mainLay

def drawModuleButton(MnsBuildModuleObj, connectFunction):
	"""Main BLOCK dynamic build module buttom function draw.
	Builds a new QPushButoon for a given module, return the QPushButton created after connecting it to the given 'connectFunction'.
	The QPush buttom created will then to be inserted into a layout by the caller function."""

	VLayout = QtWidgets.QHBoxLayout()
	VLayout.setAlignment(QtCore.Qt.AlignLeft)
	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignCenter)
	spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
	HLayout.insertItem(0, spacer)
	btn = QtWidgets.QPushButton()
	btn.setObjectName(MnsBuildModuleObj.moduleName + "Btn")
	btn.setText(MnsBuildModuleObj.shortName)
	btn.setFixedSize(27, 27)

	currentIndex = MnsBuildModuleObj.layoutParent.count()
	if float(currentIndex / float(2)) == float(int(currentIndex / 2)):
		btn.setStyleSheet("QPushButton{background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #2198c0, stop: 1 #0d5ca6); \
						   color: #333333; font: bold; \
						   font-size: 13px; \
						   border-radius: 4px; \
						   border-width: 2px; \
						   border-color: #313131; \
						   border-style: solid;}  \
						   QPushButton:hover{background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #27e3ff, stop: 1 #1281e1)}")
	else:
		btn.setStyleSheet("QPushButton{background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #a6ffc4, stop: 1 #2bff72); \
				   color: #333333; font: bold; \
				   font-size: 13px; \
				   border-radius: 4px; \
				   border-width: 2px; \
				   border-color: #313131; \
				   border-style: solid;}  \
				   QPushButton:hover{background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #d0ffdb, stop: 1 #58ff87)}")

	HLayout.insertWidget(1, btn)
	spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
	HLayout.insertItem(2, spacer)
	HLayoutA = QtWidgets.QHBoxLayout()
	HLayoutA.setAlignment(QtCore.Qt.AlignCenter)
	spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
	HLayoutA.insertItem(0, spacer)
	label = QtWidgets.QLabel()
	label.setText(MnsBuildModuleObj.moduleName)
	HLayoutA.insertWidget(1,label)
	spacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
	HLayoutA.insertItem(2, spacer)
	VLayout.insertLayout(0,HLayout)
	VLayout.insertLayout(1,HLayoutA)
	MnsBuildModuleObj.layoutParent.addLayout(VLayout)

	btn.released.connect(lambda: connectFunction(MnsBuildModuleObj))

	#return; QPushButton
	return btn

def setSpaceDefault(listWG, **kwargs):
	displayOnly = kwargs.get("displayOnly", False)

	defaultSuffix = "*"
	if listWG:
		if not displayOnly:
			defaultItem = listWG.currentItem()
			for itemIdx in range(listWG.count()):
				item = listWG.item(itemIdx)
				if defaultItem and not item is defaultItem:
					if defaultSuffix in item.text():
						boldFont=QtGui.QFont()
						boldFont.setBold(False)
						boldFont.setWeight(50)
						item.setFont(boldFont)
						item.setForeground(QtGui.QColor('lightGray'))
						item.setText(item.text().replace(defaultSuffix, ""))
				else:
					if defaultSuffix in item.text():
						boldFont=QtGui.QFont()
						boldFont.setBold(False)
						boldFont.setWeight(50)
						item.setFont(boldFont)
						item.setForeground(QtGui.QColor('lightGray'))
						item.setText(item.text().replace("*", ""))
					else:
						boldFont=QtGui.QFont()
						boldFont.setBold(True)
						item.setFont(boldFont)
						item.setForeground(QtGui.QColor('green'))
						item.setText(item.text() + defaultSuffix)
		else:
			for itemIdx in range(listWG.count()):
				item = listWG.item(itemIdx)
				if defaultSuffix in item.text():
					boldFont=QtGui.QFont()
					boldFont.setBold(True)
					item.setFont(boldFont)
					item.setForeground(QtGui.QColor('green'))
					break

def drawSpacesBox(MnsArgumentObj, layoutParent, **kwargs):
	"""Main dynamic 'draw spaces box' creation function.
	"""

	genericList = kwargs.get("genericList", False)
	
	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)
	HLayout.addWidget(resetBtn)
	
	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(170,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	listWG = QtWidgets.QListWidget()
	listWG.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
	listWG.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
	listWG.setFixedSize(140,80)
	sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
	listWG.setSizePolicy(sizePolicy)
	HLayout.addWidget(listWG)
	
	VLayout = QtWidgets.QVBoxLayout()
	insertBtn = QtWidgets.QPushButton()
	insertBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	insertBtn.setFixedSize(20,20)
	insertBtn.setText("<")
	insertBtn.released.connect(lambda: listLoadCmd(listWG))
	VLayout.addWidget(insertBtn)

	removeBtn = QtWidgets.QPushButton()
	removeBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	removeBtn.setFixedSize(20,20)
	removeBtn.setText(">")
	removeBtn.released.connect(lambda: listRemoveCommand(listWG))
	VLayout.addWidget(removeBtn)

	HLayout.addLayout(VLayout)
	layoutParent.addLayout(HLayout)
	setListWidgetDefaultCommand(listWG, MnsArgumentObj.default)
	resetBtn.released.connect(lambda: setListWidgetDefaultCommand(listWG, MnsArgumentObj.default))
	
	if not genericList:
		listWG.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		listWG.customContextMenuRequested.connect(lambda: setSpaceDefault(listWG))

	#return;QListWidget
	return listWG

def extraChannelsRemoveSelected(treeWG):
	currentItems = treeWG.selectedItems()
	if currentItems:
		for item in currentItems:
			treeWG.takeTopLevelItem(treeWG.indexOfTopLevelItem(item))

def extraChannelsEdit(item, col):
	if (item.text(3) == "True" and col == 1) or col == 2: 
		pass
	else:
		item.treeWidget().editItem(item, col)

def extraChannelsAddRow(treeWG, **kwargs):
	attrName = kwargs.get("attrName", "Name")
	attr = kwargs.get("attr", "Attribute")
	direction = kwargs.get("direction", "Pos")
	skipDataValidation = kwargs.get("skipDataValidation", False)

	twItem = QtWidgets.QTreeWidgetItem(treeWG, [attrName, attr, direction])
	twItem.setFlags(twItem.flags() | QtCore.Qt.ItemIsEditable)

	if direction == "Pos":
		twItem.setIcon(2, QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTBAdd.png")))
	else:
		twItem.setIcon(2, QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTBRemove.png")))
	
	twItem.setSizeHint(0, QtCore.QSize(300, 21))

	if not skipDataValidation:
		extraChannelsValidateCurrentData(treeWG)

def extraChannelsAddDivider(treeWG, **kwargs):
	dividerName = kwargs.get("dividerName", "Divider")
	skipDataValidation = kwargs.get("skipDataValidation", False)

	twItem = QtWidgets.QTreeWidgetItem(treeWG, [dividerName, "------------", "-", "True"])
	twItem.setFlags(twItem.flags() | QtCore.Qt.ItemIsEditable)
	twItem.setSizeHint(0, QtCore.QSize(300, 21))

	if not skipDataValidation:		
		extraChannelsValidateCurrentData(treeWG)

def extraChannelsChangeDirection(treeWG, direction = 1):
	text = "Neg"
	icon = QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTBRemove.png"))

	if direction: 
		text = "Pos"
		icon = QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTBAdd.png"))

	if treeWG.selectedItems():
		for item in treeWG.selectedItems():
			if item.text(2) != "-":
				item.setText(2, text)
				item.setIcon(2, icon)

def extraChannelsLoadCBSel(treeWG):
	channelSelection = pm.channelBox ('mainChannelBox', query=True, selectedMainAttributes=True)
	sel = pm.ls(sl=1, ap=1)

	if sel and channelSelection:
		attrString = sel[0] + "." + channelSelection[0]
		for twi in treeWG.selectedItems():
			twi.setText(1, attrString)

def extraChannelsDuplicateRows(treeWG, **kwargs):
	skipDataValidation = kwargs.get("skipDataValidation", False)

	currentItems = treeWG.selectedItems()
	for item in currentItems:
		if item.text(3) != "True":
			extraChannelsAddRow(treeWG, attrName = item.text(0), attr = item.text(1), direction =item.text(2))
		else:
			extraChannelsAddDivider(treeWG, dividerName = item.text(0))

	if not skipDataValidation:		
		extraChannelsValidateCurrentData(treeWG)

def extraChannelsValidateCurrentData(treeWG):
	existingDividers = []
	for itemIdx in range(treeWG.topLevelItemCount()):
		item = treeWG.topLevelItem(itemIdx)

		if item.text(3) == "True":
			if item.text(0) in existingDividers:
				suffix = "1"

				try: 
					suffix = str(int(item.text(0)[-1]) + 1)
					item.setText(0, item.text(0)[:-1] + suffix)
				except: 
					item.setText(0, item.text(0) + suffix)

				extraChannelsValidateCurrentData(treeWG)
				break

			existingDividers.append(item.text(0))

def dynUIExtraChannelsMenu(treeWG, position):
	menu = QtWidgets.QMenu()
	
	col = treeWG.header().logicalIndexAt(position)

	if col != 2 or not treeWG.selectedItems():
		addSelectedAction = menu.addAction("Add Divider")
		addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/clip_divider.png")))
		addSelectedAction.triggered.connect(lambda: extraChannelsAddDivider(treeWG))

		addSelectedAction = menu.addAction("Add Row")
		addSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/addClip.png")))
		addSelectedAction.triggered.connect(lambda: extraChannelsAddRow(treeWG))

		currentItems = treeWG.selectedItems()
		if currentItems:
			dupRowAction = menu.addAction("Duplicate Selected Rows")
			dupRowAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/polyDuplicateUVSet.png")))
			dupRowAction.triggered.connect(lambda: extraChannelsDuplicateRows(treeWG))

			if col == 1:
				loadFromCBAction = menu.addAction("Load Channel-Box Selection")
				loadFromCBAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nodeGrapherAddNodes.png")))
				loadFromCBAction.triggered.connect(lambda: extraChannelsLoadCBSel(treeWG))
			
			removeSelectedAction = menu.addAction("Remove Selected Row/Divider")
			removeSelectedAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/deleteClip.png")))
			removeSelectedAction.triggered.connect(lambda: extraChannelsRemoveSelected(treeWG))

		clearAction = menu.addAction("Clear")
		clearAction.triggered.connect(treeWG.clear)
	else:
		positiveAction = menu.addAction("Positive")
		positiveAction.triggered.connect(lambda: extraChannelsChangeDirection(treeWG, 1))
		positiveAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTBAdd.png")))
		negativeAction = menu.addAction("Negative")
		negativeAction.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/UVTBRemove.png")))
		negativeAction.triggered.connect(lambda: extraChannelsChangeDirection(treeWG, 0))

	menu.exec_(treeWG.viewport().mapToGlobal(position))

def extraChannelsMoveItemsUp(treeWG):
	currentItems = treeWG.selectedItems()
	rootItem = treeWG.invisibleRootItem()

	movedItems = []

	for item in currentItems:
		row = treeWG.indexOfTopLevelItem(item)
		if row > 0:
			child = rootItem.takeChild(row)
			rootItem.insertChild(row-1, child);
			movedItems.append(child)

	for item in movedItems: item.setSelected(True)

def extraChannelsMoveItemsDown(treeWG):
	currentItems = treeWG.selectedItems()
	rootItem = treeWG.invisibleRootItem()

	movedItems = []

	for item in currentItems:
		row = treeWG.indexOfTopLevelItem(item)
		if row < treeWG.topLevelItemCount() - 1:
			child = rootItem.takeChild(row)
			rootItem.insertChild(row+1, child);
			movedItems.append(child)

	for item in movedItems: item.setSelected(True)

def drawExtraChannelsBox(MnsArgumentObj, layoutParent):
	"""Main dynamic 'draw blend shape targets box' creation function.
	"""

	HLayout = QtWidgets.QVBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignHCenter)

	lLayout = QtWidgets.QHBoxLayout()
	lLayout.setContentsMargins(0, 0, 0, 0)
	label = QtWidgets.QLabel()

	toolTip = "<html><table width = 700><tr><td><font face = SansSerif size = 4><b>Extra-Channels</b></font></td></tr>\
		<tr><td><font face = SansSerif size = 4>Use this UI to create custom attributes within your modules and automatically connect to an attribute.\
		<br>This was built mainly for blend shape connections.\
		<br>Any row within this list will create a custom attribute with the selected name on the main control (or attribute host control) of the relevant module, and connect to the given attribute, considering the target attribute range is 0-1.\
		<br><br>Use right-click menu to add/remove items, and double-click to edit values.\
		<br>Use the order buttons to reorder rows.\
		<br><br>Valid characters for attribute names are 0-1, a-z, A-Z, _\
		<br>Attribute names cannot start with numbers.\
		<br>Use dividers to group attributes in case you need to. All attributes will be created in the same order as they are listed.\
		<br>Divider names cannot be repeated.\
		<br>Attribute names may be repeated- only a single attribute will be created in this case, although it will be connected to all listed attributes.\
		<br>Use the direction column to choose the channel direction control. Negative direction will be revesed and normalized to the 0-1 range when connected.\
		<br>For example, in case you have 2 shapes, one for expantion and one for contraction, you can create 2 rows with the same attrbiute name, one in the positive direction- connected to the expantion shape, and one in the negative direction- connected to the contraction shape.\
		<br>This will result in a single attribute that ranges between -1 and +1, while 0 to -1 will control the contraction shape, and 0 to +1 will control the expantion shape.\
		<br><br>Symmetry: When symmetrizing modules, every extra channel row containing a \"l_\" or \"r_\" prefix, will be renamed to the opposite side.\
		</td></tr>\
		</table></html>"

	label.setToolTip(toolTip)
	label.setFixedSize(20,20)
	label.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/info.png"))
	lLayout.addWidget(label)
	label = QtWidgets.QLabel()
	
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(170,20)
	label.setText(MnsArgumentObj.name)
	lLayout.addWidget(label)

	moveUpBtn = QtWidgets.QPushButton()
	moveUpBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	moveUpBtn.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nodeGrapherArrowUp.png")))
	moveUpBtn.setFixedSize(20,20)
	moveUpBtn.released.connect(lambda: extraChannelsMoveItemsUp(treeWG))
	lLayout.addWidget(moveUpBtn)

	moveDownBtn = QtWidgets.QPushButton()
	moveDownBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	moveDownBtn.setIcon(QtGui.QIcon(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/nodeGrapherArrowDown.png")))
	moveDownBtn.setFixedSize(20,20)
	moveDownBtn.released.connect(lambda: extraChannelsMoveItemsDown(treeWG))
	lLayout.addWidget(moveDownBtn)

	HLayout.addLayout(lLayout)

	treeWG = QtWidgets.QTreeWidget()
	treeWG.setIndentation(1)
	treeWG.setFixedSize(390,200)
	treeWG.setColumnCount(4)
	treeWG.setColumnWidth(0, 160)
	treeWG.setColumnWidth(1, 160)
	treeWG.setColumnWidth(2, 60)
	treeWG.setColumnHidden(3, True)
	treeWG.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
	treeWG.itemDoubleClicked.connect(extraChannelsEdit)
	treeWG.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
	treeWG.setItemDelegate(extraChannelsDelegate())
	treeWG.setAlternatingRowColors(True)
	header = treeWG.headerItem()
	header.setText(0, "Channel-Name")
	header.setText(1, "Target-Attribute")
	header.setText(2, "Direction")
	header.setText(3, "isDiv")

	treeWG.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
	treeWG.customContextMenuRequested.connect(partial(dynUIExtraChannelsMenu, treeWG))
	treeWG.itemChanged.connect(lambda: extraChannelsValidateCurrentData(treeWG))

	currentChannelList = None
	try: currentChannelList = json.loads(MnsArgumentObj.default)
	except: pass

	if currentChannelList:
		treeWG.blockSignals(True)
		for extraChannelDef in currentChannelList:
			if extraChannelDef["isDiv"] == "True":
				extraChannelsAddDivider(treeWG, skipDataValidation = True, dividerName = extraChannelDef["attrName"])
			else:
				extraChannelsAddRow(treeWG, skipDataValidation = True, attrName = extraChannelDef["attrName"], attr = extraChannelDef["attrTarget"], direction = extraChannelDef["dir"])
		treeWG.blockSignals(False)

	HLayout.addWidget(treeWG)

	layoutParent.addLayout(HLayout)

	#return;QTreeWidget
	return treeWG

def setListWidgetDefaultCommand(QListWidget, default):
	"""'Default' command trigger for a 'list' type synamic row (dynUI)
	"""

	QListWidget.clear()
	if default == ["None"]: pass
	elif default and default != [' ']: 
		QListWidget.addItems(default)
		setSpaceDefault(QListWidget, displayOnly = True)

def listLoadCmd(QListWidget):
	"""Load to list command trigger (dynUI)
	"""

	sel = [s.nodeName() for s in pm.ls(sl=1, ap=1)]
	currentItems =  [str(QListWidget.item(i).text()) for i in range(QListWidget.count())]
	if sel:
		for item in sel:
			if not item in currentItems: 
				QListWidget.addItem(item)

def listRemoveCommand(QListWidget):
	"""Remove from list command trigger (dynUI)
	"""

	sel = QListWidget.selectedItems()
	for item in sel: 
		QListWidget.takeItem(QListWidget.indexFromItem(item).row())

def getColor(btn, **kwargs):
	"""Simple 'get color for a color PButton'.
	Creates a new QColorDialog asking the user for a color choice.
	When color selected sets the caller QPushButton color to the selected color"""

	colOverrideCbx = kwargs.get("colOverrideCbx", None) #arg;

	widget = QtWidgets.QColorDialog()
	current = btn.palette().button().color()
	col = widget.getColor(current)

	if col.isValid(): 
		btn.setStyleSheet("QWidget { background-color: " + col.name() + "}")
		if colOverrideCbx: colOverrideCbx.setChecked(True)
		
	#return;tuple[3] (color)
	return col

def setColorDefaultCmd(btn, colorDef):
	"""A 'set color back to default command.
	A command to be triggered by an outside 'default' button, or when initializing to set the specified QPushButton color back to it's default value."""

	btn.setStyleSheet("QWidget { background-color: rgb(" + str(colorDef[0] * 255) + "," + str(colorDef[1]*255) + "," + str(colorDef[2] * 255) + "); color: #333333; font: bold }")

def drawColorBox(MnsArgumentObj, layoutParent):
	"""Main dynamic 'draw color box' creation function.
	Will create a new QPushButton with its 'color picker' style display and inserts it into the given layoutParent.
	An automatic connection to the 'getColor' function is made, as well as a 'default' button creation and connection is made."""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())

	label.setFixedSize(170,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)


	colBtn = QtWidgets.QPushButton()
	colBtn.setFixedSize(140,20)
	colBtn.setText("color select")
	HLayout.addWidget(colBtn)
	col = colBtn.released.connect(lambda: getColor(colBtn))

	setColorDefaultCmd(colBtn, MnsArgumentObj.default)
	layoutParent.addLayout(HLayout)
	resetBtn.released.connect(lambda: setColorDefaultCmd(colBtn, MnsArgumentObj.default))

	#return;QPushButton
	return colBtn

def drawColorBtnAndConnect(default, **kwargs):
	btnSize = kwargs.get("buttonSize", 25) #arg;
	colOverrideCbx = kwargs.get("colOverrideCbx", None) #arg;

	colBtn = QtWidgets.QPushButton()
	colBtn.setFixedSize(btnSize,btnSize)
	setColorDefaultCmd(colBtn, default)
	colBtn.released.connect(lambda: getColor(colBtn, colOverrideCbx = colOverrideCbx))

	#return;QPushButton
	return colBtn

def getColorArrayFromColorScheme(side, colorScheme):
	"""Collect a normalized array of colors from a 'colorSceheme' enum attribute.
	"""

	sideV = mnsSidesDict[side]
	retList = [] 
	if sideV == mnsPS_cen: retList = [colorScheme[1], colorScheme[4], colorScheme[7],colorScheme[10],colorScheme[13]]
	elif sideV == mnsPS_right: retList = [colorScheme[0], colorScheme[3], colorScheme[6],colorScheme[9],colorScheme[12]]
	elif sideV == mnsPS_left: retList = [colorScheme[2], colorScheme[5], colorScheme[8],colorScheme[11],colorScheme[14]]
	
	#return;list (color sceheme)
	return retList

def sideCBChangedTriggerCommand(colorOverrideCbx, sideCB, ovverideBtnList, rigTop, ignoreOvverideCheckbox = False):
	"""DynUI side combo box changed command trigger.
	"""

	if rigTop and sideCB and colorOverrideCbx:
		if not colorOverrideCbx.isChecked() or ignoreOvverideCheckbox:
			if ignoreOvverideCheckbox: colorOverrideCbx.setChecked(False)
			colScheme = mnsUtils.splitEnumAttrToColorSchemeFloatTupleList("colorScheme", rigTop)
			side = sideCB.currentText()
			valueArray = getColorArrayFromColorScheme(side, colScheme)
			for k in range(0, len(valueArray)):
					setColorDefaultCmd(ovverideBtnList[k], valueArray[k])

def colOverrideBlockDefTriggerCommand(colorOverrideCbx, sideCB, ovverideBtnList):
	"""DynUI color-override default command trigger.
	"""

	if colorOverrideCbx and sideCB:
		side = sideCB.currentText()
		valueArray = getColorArrayFromColorScheme(side, GLOB_mnsBlockDefColorScheme)

		for k in range(0, len(valueArray)):
			setColorDefaultCmd(ovverideBtnList[k], valueArray[k])

def colOverrideStateChange(colorOverrideCbx, sideCB, ovverideBtnList):
	"""DynUI color-override changed command trigger.
	"""

	if colorOverrideCbx:
		if not colorOverrideCbx.isChecked():
			colOverrideBlockDefTriggerCommand(colorOverrideCbx, sideCB, ovverideBtnList)

def drawJntStructMemberCol(layout = None, argument = None):
	if layout and argument:
		label = QtWidgets.QLabel()
		label.setFixedSize(20,20)
		
		if argument.jntStructMember or argument.jntStructSoftMod:
			#setIcon
			if argument.jntStructSoftMod:
				label.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/moveSkinnedJoint.png"))
				label.setScaledContents(True) 
				label.setToolTip("jntStructSoftMod")

			elif argument.jntStructMember:
				label.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/mayaResource/smoothSkin.png"))
				label.setScaledContents(True) 
				label.setToolTip("jntStructMember")

		layout.addWidget(label)

def drawColorSchemeOverride(MnsArgumentObj, layoutParent, **kwargs):
	"""Draw the predefined 'color scheme' slot into a dynUI.
	"""

	sideCB = kwargs.get("sideCB", None) #arg;
	colOverrideCbx = kwargs.get("colOverride", False) #arg;
	rigTop =  kwargs.get("rigTop", None) #arg;

	grpBx = QtWidgets.QGroupBox("")
	grpBx.setAlignment(QtCore.Qt.AlignHCenter)
	grpBx.setFixedSize(370,80)

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)
	HLayout.addWidget(resetBtn)

	labelVLay = QtWidgets.QVBoxLayout()
	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(140,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	labelVLay.addWidget(label)

	blkResetBtn = QtWidgets.QPushButton()
	blkResetBtn.setText("Block Default")
	blkResetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	blkResetBtn.setFixedSize(90,20)
	labelVLay.addWidget(blkResetBtn)
	HLayout.addLayout(labelVLay)

	btnList = []
	for k in range(0, len(MnsArgumentObj.default)):
		colBtn = drawColorBtnAndConnect(MnsArgumentObj.default[k], buttonSize = 20, colOverrideCbx = colOverrideCbx)
		HLayout.addWidget(colBtn,)
		btnList.append(colBtn)

	grpBx.setLayout(HLayout)
	layoutParent.addWidget(grpBx)

	if sideCB: sideCB.currentTextChanged.connect(lambda: sideCBChangedTriggerCommand(colOverrideCbx, sideCB, btnList, rigTop))
	if colOverrideCbx: colOverrideCbx.stateChanged.connect(lambda: colOverrideStateChange(colOverrideCbx, sideCB, btnList))

	resetBtn.released.connect(lambda: sideCBChangedTriggerCommand(colOverrideCbx, sideCB, btnList, rigTop, ignoreOvverideCheckbox = True))
	blkResetBtn.released.connect(lambda: colOverrideBlockDefTriggerCommand(colOverrideCbx, sideCB, btnList))
	sideCBChangedTriggerCommand(colOverrideCbx, sideCB, btnList, rigTop, ignoreOvverideCheckbox = False)

	#return;list
	return btnList

def drawColorScheme(MnsArgumentObj, layoutParent):
	"""Main block 'draw color scheme box' creation function.
	Will create a new QPushButton series with 'color picker's style display and inserts it into the given layoutParent.
	An automatic connection to the 'getColor' function is made, as well as a 'default' button creation and connection is made."""

	grpBx = QtWidgets.QGroupBox()
	grpBx.setAlignment(QtCore.Qt.AlignHCenter)


	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)


	labelVLay = QtWidgets.QVBoxLayout()

	spacer = QtWidgets.QSpacerItem(2,20,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
	labelVLay.addItem(spacer)

	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(140,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	label.setAlignment(QtCore.Qt.AlignBottom)
	labelVLay.addWidget(label)

	blkResetBtn = QtWidgets.QPushButton()
	blkResetBtn.setText("Block Default")
	blkResetBtn.setFixedSize(90,20)
	labelVLay.addWidget(blkResetBtn)

	spacer = QtWidgets.QSpacerItem(2,20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding,)
	labelVLay.addItem(spacer)

	HLayout.addLayout(labelVLay)


	VSecLayout = QtWidgets.QVBoxLayout()
	HSecLayout = QtWidgets.QHBoxLayout()

	for col in ["", "R", "C", "L"]:
		label = QtWidgets.QLabel()
		label.setText(col)
		label.setAlignment(QtCore.Qt.AlignHCenter)
		label.setFixedSize(25,15)
		HSecLayout.addWidget(label)
	VSecLayout.addLayout(HSecLayout)

	btnList = []

	j = 0
	row = 0
	count = 0
	rowIndex = ["prim", "sec", "ter", "gimb", "piv"]
	HSecLayout = None
	for val in MnsArgumentObj.default:
		if j == 0: 
			HSecLayout = QtWidgets.QHBoxLayout()
			HSecLayout.setAlignment(QtCore.Qt.AlignVCenter)
			label = QtWidgets.QLabel()
			label.setFixedSize(40,20)
			label.setText(rowIndex[row])
			HSecLayout.addWidget(label)

		colBtn = drawColorBtnAndConnect(MnsArgumentObj.default[count])
		HSecLayout.addWidget(colBtn)
		btnList.append(colBtn)


		if j == 2: 
			VSecLayout.addLayout(HSecLayout)
			j = 0
			row += 1
		else: j += 1	
		count += 1


	HLayout.addLayout(VSecLayout)
	grpBx.setLayout(HLayout)
	layoutParent.addWidget(grpBx)
	#layoutParent.addLayout(HLayout)

	blkResetBtn.released.connect(lambda: setColorSchemeDefaultCmd(btnList, GLOB_mnsBlockDefColorScheme))
	resetBtn.released.connect(lambda: setColorSchemeDefaultCmd(btnList, MnsArgumentObj.default))

	#return;list
	return btnList

def checkChannelCommand(chanBtn,chanCbxs):
	"""DynUI 'channel control' checkBox changed command trigger.
	"""

	allCheck = False
	for cbx in chanCbxs: 
		if not cbx.isChecked(): 
			allCheck = True
			break
	for cbx in chanCbxs: 
		if cbx.isEnabled():
			cbx.setChecked(allCheck)

def drawChannelColumnAndConnect(MnsArgumentObj, channel, **kwargs):
	"""Draw channel column (part of channel control) into a DynUI.
	"""

	rootSettings = kwargs.get("rootSettings", None)

	VSecLayout = QtWidgets.QVBoxLayout()
	chanBtn = QtWidgets.QPushButton()
	chanBtn.setText(channel.upper())
	chanBtn.setFixedSize(45,20)
	chanBtn.setStyleSheet("QPushButton{ background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #434343, stop: 1 #515251);\
						   color: #d1d1d1; font: bold; \
						   font-size: 10px; \
						   border-radius: 2px; \
						   border-width: 1px; \
						   border-color: #000000; \
						   border-style: solid;}  \
						   QPushButton:hover{background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #9f9f9f, stop: 1 #b0b1b0)}")

	VSecLayout.addWidget(chanBtn)

	labelList = ["x", "y", "z"]
	k = 0
	chanCbxs = []
	for val in MnsArgumentObj.default[channel]:
		HLayoutA = QtWidgets.QHBoxLayout()
		label = QtWidgets.QLabel()
		label.setText(channel.lower() + labelList[k])
		label.setAlignment(QtCore.Qt.AlignRight)
		label.setFixedHeight(17)
		HLayoutA.addWidget(label)
		cbx = QtWidgets.QCheckBox()
		cbx.setObjectName(channel.lower() + labelList[k])
		chanCbxs.append(cbx)
		setBooleanDefaultCmd(cbx, val)
		
		if not val and MnsArgumentObj.lockOffAttributes and rootSettings: 
			if not rootSettings[channel][k]:
				cbx.setEnabled(False)

		HLayoutA.addWidget(cbx)
		VSecLayout.addLayout(HLayoutA)
		k += 1

	chanBtn.released.connect(lambda: checkChannelCommand(chanBtn, chanCbxs))

	#return;QVBoxLayout (layout), list (drawen boxes)
	return VSecLayout,chanCbxs

def setChennelControlDefaultCmd(cbxList, MnsArgumentObj):
	"""DynUI chennel control slot default command trigger.
	"""

	defaultList = MnsArgumentObj.default["t"] + MnsArgumentObj.default["r"] + MnsArgumentObj.default["s"]
	k = 0
	for cbx in cbxList:
		cbx.setChecked(defaultList[k])
		k += 1

def drawChannelControl(MnsArgumentObj, layoutParent, **kwargs):
	"""Draw the predefined channel-control slot into a DynUI.
	"""

	rootGuide = kwargs.get("rootGuide", None)
	grpBx = QtWidgets.QGroupBox("Channel Control")
	grpBx.setAlignment(QtCore.Qt.AlignHCenter)
	grpBx.setFixedSize(370,150)

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(140,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	rootSettings = []
	rootGuide = mnsUtils.validateNameStd(rootGuide)
	if rootGuide:
		status, modPath = mnsUtils.validateAttrAndGet(rootGuide, "modPath", None)
		status, modType = mnsUtils.validateAttrAndGet(rootGuide, "modType", None)
		if modPath and modType:
			modSetFile = os.path.join(modPath, modType + ".modSettings").replace("\\", "/")
			if modSetFile and os.path.isfile(modSetFile):
				modArgs = mnsUtils.readSetteingFromFile(modSetFile)
				for modArg in modArgs:
					if modArg.name == MnsArgumentObj.name:
						rootSettings = modArg.default
						break

	HSecLayout = QtWidgets.QHBoxLayout()
	allCbxs = []
	for channel in "trs":
		VSecLayout, cbxs = drawChannelColumnAndConnect(MnsArgumentObj,channel, rootSettings = rootSettings)
		allCbxs = allCbxs + cbxs
		HSecLayout.addLayout(VSecLayout)

	HLayout.addLayout(HSecLayout)
	grpBx.setLayout(HLayout)
	layoutParent.addWidget(grpBx)
	#layoutParent.addLayout(HLayout)
	resetBtn.released.connect(lambda: setChennelControlDefaultCmd(allCbxs,MnsArgumentObj))

	#return;list (all channel cbxs)
	return allCbxs

def drawHorizontalDevider(MnsArgumentObj, layoutParent):
	"""Draw a simple Horizontal devider into the dynUI.
	"""
	vLine = None
	loReturn = None
	dividerWidget = None

	if MnsArgumentObj.simpleDivider:
		if MnsArgumentObj.default:
			HLayout = QtWidgets.QHBoxLayout()

			vLine = QFrame()
			vLine.setAccessibleName("HLine")
			vLine.setFrameShape(QFrame.HLine)
			vLine.setFrameShadow(QFrame.Sunken)
			vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
			HLayout.addWidget(vLine)

			label = QtWidgets.QLabel()
			label.setMinimumHeight(25)
			label.setText(MnsArgumentObj.default)
			label.setAlignment(QtCore.Qt.AlignCenter)
			#label.setAlignment(QtCore.Qt.AlignVCenter)
			HLayout.addWidget(label)

			vLine = QFrame()
			vLine.setAccessibleName("HLine")
			vLine.setFrameShape(QFrame.HLine)
			vLine.setFrameShadow(QFrame.Sunken)
			vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
			HLayout.addWidget(vLine)

			layoutParent.addLayout(HLayout)
		else:
			vLine = QFrame()
			vLine.setFrameShape(QFrame.HLine)
			vLine.setFrameShadow(QFrame.Sunken)
			vLine.setStyleSheet("border: 1px;border-style: solid;border-color: #292929;")
			layoutParent.addWidget(vLine)
	else:
		dividerWidget = CollapsibleFrameWidget(title=MnsArgumentObj.default)
		dividerWidget.setObjectName(MnsArgumentObj.default)
		layoutParent.addWidget(dividerWidget)
		loReturn = dividerWidget._content_layout

	#return;QFrame (Horizontal line devider)
	return vLine, loReturn, dividerWidget

def convertRelativePathToAbs(filePath = ""):
	"""A method for replacing a projectRoot variable within a relative path to the absolute path
	Based on the current project directory"""

	if filePath and "$PROJECT_ROOT" in filePath:
		projectDir = pm.workspace(q = True,rootDirectory = True).replace("\\", "/")
		filePath = filePath.replace("$PROJECT_ROOT/", projectDir)

	#return;string
	return filePath

def relativePathCheck(filePath = ""):
	"""A method for checking if any file path can be converted to a relative path.
	If relative path is available, promt a message asking the user if he want to convert.
	if so, convert and return.
	"""
	if filePath:
		filePath = filePath.replace("\\", "/")
		projectDir = pm.workspace(q = True,rootDirectory = True)
		if projectDir in filePath: #the path can be relative
			reply = QtWidgets.QMessageBox.question(None, 'Convart path to relative?', "The path you selected is within the current project directory, and it can be converted to a relative path. Would you like to convert it?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
			if reply == QtWidgets.QMessageBox.Yes:
				filePath = os.path.relpath(filePath, projectDir).replace("\\", "/")
				filePath = "$PROJECT_ROOT/" + filePath

	#return;string
	return filePath

def customScriptsAddCommand(listWidget):
	"""Add button trigger command for "custom scripts" slot of synamic UI.
	"""

	if listWidget:
		currentItems = [listWidget.item(i).text() for i in range(listWidget.count())]

		selectionList = QtWidgets.QFileDialog.getOpenFileNames(get_maya_window(), "Select File", "", "(*.py)");
		if selectionList[0]: 
			for file in selectionList[0]:
				fileName = file.split("/")[-1]
				if not fileName in currentItems:
					file = relativePathCheck(file)

					listWidgetItem = QtWidgets.QListWidgetItem(fileName, listWidget)
					listWidgetItem.setToolTip(file)

def customScriptsRemoveCommand(listWidget):
	"""Remove button trigger command for "custom scripts" slot of synamic UI.
	"""

	if listWidget:
		currentSelection = listWidget.selectedItems()
		if currentSelection:
			for item in reversed(currentSelection):
				listWidget.takeItem(listWidget.row(item))

def customScriptsDefaultCommand(listWidget, MnsArgumentObj):
	"""Default trigger command for 'custom scripts' slot in dynUI.
	"""

	if MnsArgumentObj.default and listWidget:
		listWidget.clear()
		if not type(MnsArgumentObj.default) is list:
			files = MnsArgumentObj.default.split(",")
			for file in files:
				fileName = file.split("/")[-1]
				listWidgetItem = QtWidgets.QListWidgetItem(fileName, listWidget)
				listWidgetItem.setToolTip(file)

def drawCustomScriptsSlot(MnsArgumentObj, layoutParent):
	"""draw a "custom scripts" slot into dyn UI.
	"""

	HLayout = QtWidgets.QHBoxLayout()

	listVLayout = QtWidgets.QVBoxLayout()
	listWidget = QtWidgets.QListWidget()
	listWidget.setFixedSize(330,120)
	listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
	listWidget.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
	customScriptsDefaultCommand(listWidget, MnsArgumentObj)
	
	listVLayout.addWidget(listWidget)
	spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
	listVLayout.insertItem(1, spacer)
	HLayout.addLayout(listVLayout)

	btnVLayout = QtWidgets.QVBoxLayout()
	addBtn = QtWidgets.QPushButton()
	addBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	addBtn.setText("+")
	addBtn.setFixedSize(20,20)
	addBtn.released.connect(lambda: customScriptsAddCommand(listWidget))
	btnVLayout.addWidget(addBtn)
	removeBtn = QtWidgets.QPushButton()
	removeBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	removeBtn.setText("-")
	removeBtn.setFixedSize(20,20)
	removeBtn.released.connect(lambda: customScriptsRemoveCommand(listWidget))
	btnVLayout.addWidget(removeBtn)

	defaultBtn = QtWidgets.QPushButton()
	defaultBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	defaultBtn.setText("D")
	defaultBtn.setFixedSize(20,20)
	defaultBtn.released.connect(lambda: customScriptsDefaultCommand(listWidget, MnsArgumentObj))
	btnVLayout.addWidget(defaultBtn)

	spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
	btnVLayout.insertItem(3, spacer)
	HLayout.addLayout(btnVLayout)

	layoutParent.addLayout(HLayout)
	
	#return;QListWidget
	return listWidget

def setColorSchemeDefaultCmd(btnList, default):
	"""DynUI color-scheme default command trigger.
	"""

	if default is not None:
		k = 0
		for btn in btnList:
			setColorDefaultCmd(btn, default[k])
			k += 1

def optionBoxTextTrigger(comboBox = None, lineWditWidget = None, index = 0):
	if comboBox and lineWditWidget:
		if comboBox.currentText() == "text":
			lineWditWidget.setHidden(False)
			comboBox.setFixedWidth(100)
		else:
			lineWditWidget.setHidden(True)
			comboBox.setFixedWidth(170)

def drawOptionBox(MnsArgumentObj, layoutParent):
	"""Main dynamic 'option box' draw.
	Drawing a new ob based on parameters within the MnsArgument object passed in.
	The QComboBox is inserted into the parent layout passed in.
	A default button and connection is made."""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setFixedSize(170,20)
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)
	cbox = QtWidgets.QComboBox()
	cbox.setFixedSize(140,20)

	cbox.addItems(MnsArgumentObj.ob)
	HLayout.addWidget(cbox)

	le = None
	if "controlshape" in MnsArgumentObj.name.lower():
		cbox.setFixedSize(160,23)
		cbox.setAccessibleName("ctrlShapes")
		iconsPath = os.path.dirname(os.path.dirname(__file__)).replace("\\", "/") + "/icons/controlShapesIcons"
		
		for shapeIdx, shapeName in enumerate(MnsArgumentObj.ob):
			iconPath = GLOB_guiIconsDir + "/controlShapesIcons/" + shapeName + ".png"
			if os.path.isfile(iconPath):
				cbox.setItemIcon(shapeIdx, QtGui.QIcon(iconPath))
				cbox.setIconSize(QtCore.QSize(36, 24))

		le = QtWidgets.QLineEdit()
		le.setHidden(True)
		le.setPlaceholderText("text...")
		le.setFixedWidth(70)
		HLayout.addWidget(le)
		cbox.currentIndexChanged.connect(partial(optionBoxTextTrigger, cbox, le))
		if "txtCtrlShp_" in MnsArgumentObj.default:
			le.setText(MnsArgumentObj.default.split("txtCtrlShp_")[-1])
			MnsArgumentObj.default = "text"

	layoutParent.addLayout(HLayout)
	setOtionBoxDefaultCmd(cbox, MnsArgumentObj.default)
	resetBtn.released.connect(lambda: setOtionBoxDefaultCmd(cbox, MnsArgumentObj.default))
	drawJntStructMemberCol(HLayout, MnsArgumentObj)
	
	if MnsArgumentObj.disabled:
		resetBtn.setEnabled(False)
		le.setEnabled(False)
		cbox.setEnabled(False)

	if "controlshape" in MnsArgumentObj.name.lower():
		optionBoxTextTrigger(cbox, le)
		return cbox, le

	#return;QComboBox
	return cbox, None

def setOtionBoxDefaultCmd(cbox, default):
	"""A 'set default' command to be triggered for a combo box item.
	"""

	if default is not None:
		strM = False
		if type(default) == str or type(default) == unicode:
			strM = True
		if strM:
			try:
				cbox.setCurrentText(default)
			except:
				pass
		else:
			try:
				cbox.setCurrentIndex(default)
			except:
				pass

def drawButtonAndField(MnsArgumentObj, layoutParent, alphaLimit = False):
	"""Main dynamic 'button and field' draw. 
	Draws a deault button, text field and an 'Insert items from scene' button into the given parent layout.
	This function makes all relevant connections between the QItems created-
		- 'Load command' from the QPushButton (insert) to the text field
		- 'Clear' trigger for the text field.
		- 'Set default' from the QPushButton 'default' to the text field.

	These connections are made within in order the return the QLEdit only, with no need to worrie about the 'functionallity' buttons created, only the value within the text field."""

	if MnsArgumentObj.name == "body":
		MnsArgumentObj.alphabeticalOnly = True
		
	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setFixedSize(170,20)
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	LEdit = QtWidgets.QLineEdit()
	LEdit.setFixedSize(140,20)
	if alphaLimit: LEdit.setInputMask(">AAA") #limited to alpha chars only, max ZZZ = 17575
	if MnsArgumentObj.alphabeticalOnly:
		regex=QRegExp("[a-z-A-Z]+")
		if int(cmds.about(version = True)) > 2024: 
			validator = QtGui.QRegularExpressionValidator(regex)
		else:
			validator = QtGui.QRegExpValidator(regex)

		LEdit.setValidator(validator)
	
	setStringDefaultCmd(LEdit, MnsArgumentObj.default)
	HLayout.addWidget(LEdit)

	insertBtn = QtWidgets.QPushButton()
	insertBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	insertBtn.setFixedSize(20,20)
	insertBtn.setText("<")
	HLayout.addWidget(insertBtn)
	drawJntStructMemberCol(HLayout, MnsArgumentObj)

	layoutParent.addLayout(HLayout)
	
	resetBtn.released.connect(lambda: setStringDefaultCmd(LEdit, MnsArgumentObj.default))
	insertBtn.released.connect(lambda: loadCmd(LEdit))

	if MnsArgumentObj.disabled:
		resetBtn.setEnabled(False)
		insertBtn.setEnabled(False)
		LEdit.setEnabled(False)

	#return;QLEdit
	return LEdit

def getPathCommand(LEdit, mode = 0, fileTypes = []):
	"""Dyn UI path slot 'get path' command trigger.
	"""

	directory = None
	if mode == 1: 
		selection = QtWidgets.QFileDialog.getExistingDirectory(get_maya_window(), "Select Directory")
		if selection: directory = str(selection)
	else: 
		if fileTypes:
			fileTypeString = "" 
			for fType in fileTypes: 
				if not fileTypeString: fileTypeString = "Image Files (*." + fType
				else: fileTypeString += " *." + fType
			if fileTypeString: fileTypeString += ")"

			selection = QtWidgets.QFileDialog.getOpenFileName(get_maya_window(), "Select File", "", fileTypeString)
			if selection[0]: directory = str(selection[0])
		else:
			selection = QtWidgets.QFileDialog.getOpenFileName(get_maya_window(), "Select File")
			if selection[0]: directory = str(selection[0])
	if directory: 
		LEdit.setText(directory)

def drawPathField(MnsArgumentObj, layoutParent):
	"""Main Path row draw
	"""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setFixedSize(170,20)
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	LEdit = QtWidgets.QLineEdit()
	LEdit.setFixedSize(140,20)
	setStringDefaultCmd(LEdit, MnsArgumentObj.default)
	HLayout.addWidget(LEdit)

	insertBtn = QtWidgets.QPushButton()
	insertBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	insertBtn.setFixedSize(20,20)
	insertBtn.setText("...")
	HLayout.addWidget(insertBtn)

	layoutParent.addLayout(HLayout)

	resetBtn.released.connect(lambda: setStringDefaultCmd(LEdit, MnsArgumentObj.default))
	insertBtn.released.connect(lambda: getPathCommand(LEdit, MnsArgumentObj.pathMode, MnsArgumentObj.pathFileTypes))

	#return;QLEdit
	return LEdit

def loadCmd(LEdit):
	"""Main text field 'load from scene' trigger command.
	This command will update the given QLEdit with members of the maya scene when triggered.
	Three main cases:
		1. Nothing is selected - if the field is empty- do nothing, else clear the field.
		2. objects are selected, without any CB selection - load the object names in, seperated by commas.
		3. Objects are selected and there is a CB selection as well - load all objects and chnnels in a 'object.channel' format, seperated by commas."""

	channelSelection = pm.channelBox ('mainChannelBox', query=True, selectedMainAttributes=True)
	sel = pm.ls(sl=1, ap=1)

	if sel:
		if type(sel[0]) is pm.general.MeshVertex or type(sel[0]) is pm.general.MeshEdge or type(sel[0]) is pm.general.MeshFace:
			stringArray = []
			if type(sel[0]) is pm.general.MeshVertex:
				stringArray = pm.filterExpand(sm = 31)
			elif type(sel[0]) is pm.general.MeshEdge:
				stringArray = pm.filterExpand(sm = 32)
			elif type(sel[0]) is pm.general.MeshFace:
				stringArray = pm.filterExpand(sm = 34)

			flattened = mnsString.flattenArray(stringArray)
			LEdit.setText(flattened)
		elif len(sel) == 1:
			if channelSelection:
				channelsString = []
				for chan in channelSelection:
					channelsString.append(sel[0] + "." + chan)
				flattened = mnsString.flattenArray(channelsString)
				LEdit.setText(flattened)
			else:
				LEdit.setText(str(sel[0].nodeName()))
		elif len(sel) > 1:
			if channelSelection:
				channelsString = []
				for se in sel:
					for chan in channelSelection:
						channelsString.append(se + "." + chan)
				flattened = mnsString.flattenArray(channelsString)
				LEdit.setText(flattened)
			else:
				flattened = mnsString.flattenArray(sel)
				LEdit.setText(flattened)
		else: LEdit.setText("")

def setStringDefaultCmd(LEdit,default):
	"""'Set default' command trigger from a text field
	"""

	if default:
		try:
			LEdit.setText(default)
		except:
			pass
	else:
		LEdit.setText("")

def setIntIncrement(spinner, increment, start):
	value = spinner.value()
	pureVal = value - start 
	if pureVal != 0 and (pureVal % 4) != 0:
		newAddition = int(increment * round(float(float(pureVal) / float(increment))))
		newVal = start + newAddition
		spinner.blockSignals(True)
		spinner.setValue(newVal)
		spinner.blockSignals(False)

def drawIntSpinner(MnsArgumentObj, layoutParent):
	"""Main dynamic 'int field' field and spinner UI draw.
	Creates an int QSpinBox widget, and a default button connected to it."""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(170,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	spinner = QtWidgets.QSpinBox()
	if MnsArgumentObj.min:
		try:
			spinner.setMinimum(int(MnsArgumentObj.min))
		except:
			pass
	if MnsArgumentObj.max:
		try:
			spinner.setMaximum(int(MnsArgumentObj.max))
		except:
			pass
	setIntDefaultCmd(spinner, MnsArgumentObj.default)
	HLayout.addWidget(spinner)
	drawJntStructMemberCol(HLayout, MnsArgumentObj)

	layoutParent.addLayout(HLayout)
	resetBtn.released.connect(lambda: setIntDefaultCmd(spinner, MnsArgumentObj.default))

	if MnsArgumentObj.intIncrement:
		spinner.setSingleStep(MnsArgumentObj.intIncrement)
		spinner.editingFinished.connect(partial(setIntIncrement, spinner, MnsArgumentObj.intIncrement, MnsArgumentObj.default))
		MnsArgumentObj.intIncrement

	if MnsArgumentObj.disabled:
		resetBtn.setEnabled(False)
		spinner.setEnabled(False)

	#return;QSpinBox
	return spinner

def setIntDefaultCmd(spinner,default):
	"""'Set deafult' command trigget for an int QSpinBox.
	"""

	if default:
		try:
			spinner.setValue(int(default))
		except:
			pass

def drawFloatScroll(MnsArgumentObj, layoutParent):
	"""Main dynamic "Float spinner" UI draw
	Creates a Float QDoubleSpinBox widget, and a default button connected to it."""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setFixedSize(170,20)
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	spinner = QtWidgets.QDoubleSpinBox()
	spinner.setDecimals(3)
	if MnsArgumentObj.min:
		try:
			spinner.setMinimum(float(MnsArgumentObj.min))
		except:
			pass
	if MnsArgumentObj.max:
		try:
			spinner.setMaximum(float(MnsArgumentObj.max))
		except:
			pass
	setFloatDefaultCmd(spinner, MnsArgumentObj.default)
	HLayout.addWidget(spinner)
	drawJntStructMemberCol(HLayout, MnsArgumentObj)

	layoutParent.addLayout(HLayout)
	resetBtn.released.connect(lambda: setFloatDefaultCmd(spinner, MnsArgumentObj.default))

	if MnsArgumentObj.disabled:
		resetBtn.setEnabled(False)
		spinner.setEnabled(False)
		
	#return;QDoubleSpinBox
	return spinner

def setFloatDefaultCmd(spinner,default):
	"""'Set default' trigger for a QDoubleSpinBox item.
	"""

	if default is not None:
		try:
			spinner.setValue(float(default))
		except:
			pass

def drawBooleanChk(MnsArgumentObj, layoutParent):
	"""Main dynamic check-box UI draw.
	Creates a simple boolean check-box (QCheckBox) as well as a connected 'default' button."""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setFixedSize(170,20)
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	cbx = QtWidgets.QCheckBox()
	setBooleanDefaultCmd(cbx, MnsArgumentObj.default)
	HLayout.addWidget(cbx)
	drawJntStructMemberCol(HLayout, MnsArgumentObj)

	layoutParent.addLayout(HLayout)
	resetBtn.released.connect(lambda: setBooleanDefaultCmd(cbx, MnsArgumentObj.default))

	if MnsArgumentObj.disabled:
		resetBtn.setEnabled(False)
		cbx.setEnabled(False)

	#return;QCheckBox
	return cbx

def setBooleanDefaultCmd(cbx,default):
	"""'Set default' trigger for a QCheckBox item.
	"""

	if default is not None:
		try:
			cbx.setChecked(default)
		except:
			pass

def drawButtonAndFieldUnknown(MnsArgumentObj, layoutParent):
	"""Main 'unknown' button and field UI draw.
	In case the MnsArgument.type in question is an unknown type, draw a button and field style item for it."""

	HLayout = QtWidgets.QHBoxLayout()
	HLayout.setAlignment(QtCore.Qt.AlignLeft)
	resetBtn = QtWidgets.QPushButton()
	resetBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	resetBtn.setText("D")
	resetBtn.setFixedSize(20,20)

	HLayout.addWidget(resetBtn)
	label = QtWidgets.QLabel()
	label.setFixedSize(170,20)
	label.setToolTip(MnsArgumentObj.formatCommentToToolTip())
	label.setText(MnsArgumentObj.name + ' (' + MnsArgumentObj.type.__name__ + ')')
	HLayout.addWidget(label)

	LEdit = QtWidgets.QLineEdit()
	LEdit.setFixedSize(140,20)
	setStringDefaultCmd(LEdit, "")
	HLayout.addWidget(LEdit)

	insertBtn = QtWidgets.QPushButton()
	insertBtn.setStyleSheet("QPushButton{\nbackground-color:#535252;\nborder-style: solid;\nborder-color: black;\nborder-width: 1px;\nborder-radius: 5px;}\nQPushButton:hover{background-color:#707070;}\nQPushButton:pressed{background-color:#1d1d1d;}")
	insertBtn.setFixedSize(20,20)
	insertBtn.setText("<")
	HLayout.addWidget(insertBtn)

	layoutParent.addLayout(HLayout)

	resetBtn.released.connect(lambda: setStringDefaultCmd(LEdit, MnsArgumentObj.default))
	insertBtn.released.connect(lambda: loadCmd(LEdit))

	#return;QLEdit
	return LEdit
		
def tearOffWindow(name, title, width, height, cameraToView):
	"""Create a new maya 'tear-off' panel.
	"""

	if pm.window(name, exists = True): 
		try:
			pm.deleteUI(name)
		except:
			pass
	if not pm.window(name, exists = 1):
		win = pm.window(name, title = title, width = width, height = height)
		lay = pm.paneLayout()
		pm.modelPanel(camera = cameraToView)
		pm.showWindow(win)

		#return;pymel.core.window (tear-off window)
		return win

def getObjectScreenSpaceByFilmGate(objectProj, cam):
	"""This method is used to 'project' a plg into the projection camera's film gate.
	Get the relative position of the plg to the camera film-gate's top left corener.
	"""

	dumpPt = pm.PyNode(objectProj)
	cam = pm.PyNode(cam)
	
	ptPosWs = pm.xform(dumpPt, q = 1, ws = 1, t = 1)
	ptPosWs = pm.dt.VectorN(ptPosWs[0], ptPosWs[1], ptPosWs[2], 1)
	camMatrix = cam.worldInverseMatrix.get()
	ptVecCs =ptPosWs * camMatrix

	hfv = pm.camera(cam, q = 1, hfv = 1)
	ptx = ((ptVecCs[0] / (-ptVecCs[2]))/math.tan(math.radians(hfv/2)))/2.0 + 0.5
	vfv = pm.camera(cam, q = 1, vfv = 1)
	pty = ((ptVecCs[1] / (-ptVecCs[2]))/math.tan(math.radians(vfv/2)))/2.0 + 0.5

	#return;float, float (posX, posY)
	return ptx, pty

def acquireExternalWindow(UIName = None):
	"""A simple method to acquire an external QT window, into an actual PyQt MianWindow object.
	"""

	returnWindow = None
	if UIName:
		mayaMainWndow = apiUI.MQtUtil.mainWindow()
		if pm.window(UIName, exists=True):
			externalWin = shiboken2.wrapInstance(int(mayaMainWndow), QtWidgets.QWidget).findChild(QtWidgets.QMainWindow, UIName)
			if externalWin: returnWindow = externalWin

	#return;QMainWindow (UI Class)
	return returnWindow	

def createTextSeparator(label = "", QMenuItem = None, parent = get_maya_window()):
	label = "       " + label
	lbl = QtWidgets.QLabel(label, parent)
	lbl.setStyleSheet("background: #404040;")
	widAction = QtWidgets.QWidgetAction(parent)
	widAction.setDefaultWidget(lbl)
	if QMenuItem:
		QMenuItem.addAction(widAction)
		QMenuItem.addSeparator()

def setLinkToQLabel(labelObj = None, ahref = ""):
	if labelObj:
		labelObj.setText("<a href=\"https://" + ahref + "\" style=\"color: #3499c3;text-decoration:none;\">" + labelObj.text() + "</a>")
		labelObj.setTextFormat(QtCore.Qt.RichText);
		labelObj.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction);
		labelObj.setOpenExternalLinks(True);
		labelObj.setFocusPolicy(QtCore.Qt.NoFocus)

def extractAllMayaIcons():
	from maya import cmds
	if int(cmds.about(version = True)) > 2020:
		from mansur.internalDependencies import pymel as pm
	else:
		import pymel.core as pm


		for item in pm.resourceManager(nameFilter='*'):
			try:
				#Make sure the folder exists before attempting.
				pm.resourceManager(saveAs=(item, "D:/temp/icons/{0}".format(item)))    
			except:
				#For the cases in which some files do not work for windows, name formatting wise. I'm looking at you 'http:'!
				print (item)

def readGuiStyle(scheme = "dark", **kwargs):
	prefs = mnsUtils.getMansurPrefs()
	if "Global" in prefs.keys():
		if "UIColorScheme" in prefs["Global"].keys():
			schemeIdx = prefs["Global"]["UIColorScheme"]
			scheme = GLOB_schemes[schemeIdx]

	guiStylePath = dirname(dirname(__file__)) + "/gui/uiStyle.txt"
	scehemePath = dirname(dirname(__file__)) + "/gui/schemes/" + scheme + ".json"
	returnRawStyle = kwargs.get("returnRawStyle", False)
	schemeData = kwargs.get("schemeData", None)
	applyToGlobals = kwargs.get("applyToGlobals", True)

	if os.path.isfile(guiStylePath) and (os.path.isfile(scehemePath) or schemeData):
		scheme = {}
		if schemeData:
			scheme = schemeData
		elif os.path.isfile(scehemePath):
			scheme = mnsUtils.readJson(scehemePath)
		
		guiStyle = ""
		
		with open(guiStylePath) as f:
			for line in f:
				if not returnRawStyle:
					#apply scheme
					for key in scheme.keys():
						replaceString = "$" + key + "$"
						if replaceString in line:
							line = line.replace(replaceString, scheme[key])

				guiStyle += line.strip()
		
		if applyToGlobals:
			from . import globals as mnsGlobals
			mnsGlobals.GLOB_guiStyle = guiStyle
		
		return guiStyle

def getGuiStyle():
	from . import globals as mnsGlobals
	return mnsGlobals.GLOB_guiStyle

####### PICKER ###########

def getPlgPosition(plg, pickerBase):
	"""Get the relative position of the requested plg, based on the 'Picker Layout Base' Guide top left corner.
	Return the local bounding box size as well.
	"""

	pickerBB = pickerBase.node.boundingBox()
	pickerWS = pm.xform(pickerBase.node,q=1,ws=1,rp=1)
	plgWS = pm.xform(plg,q=1,ws=1,rp=1)[0:2]
	childs = plg.listRelatives(c = True, type = "transform")
	if childs: pm.parent(childs, w = True)
	plgBB = plg.boundingBox()
	if childs: pm.parent(childs, plg)
	width = (plgBB[1][0] - plgBB[0][0])
	height = (plgBB[1][1] - plgBB[0][1])

	posX = abs(pickerBB[0][0] - plgWS[0] + (width/2)) * 5
	posY = abs(pickerBB[1][1] - plgWS[1] - (height/2)) * 5 

	#return;float,float,float,float (posX,PosY,Width,Height)
	return posX,posY,width,height

def drawPrimaryButton(plg, tabWidget, pickerBase, picker):
	"""Picker method- draw a generic picker button.
	"""
	
	posX, posY, width, height = getPlgPosition(plg, pickerBase)
	picker.testBtn.setGeometry(posX, posY, 20,20)

def deleteAllLayoutItems(layout, **kwargs):
	"""A method to delete all widgets/object from a given layout
	"""

	for i in reversed(range(layout.count())): 
		if layout.itemAt(i).widget():
			layout.itemAt(i).widget().deleteLater()

def recDeleteAllLayoutItems(layout, **kwargs):
	"""A method to delete all widgets/object from a given layout
	"""

	for i in reversed(range(layout.count())): 
		if layout.itemAt(i).widget():
			layout.itemAt(i).widget().deleteLater()
		elif type(layout.itemAt(i)) == QtWidgets.QHBoxLayout or type(layout.itemAt(i)) == QtWidgets.QVBoxLayout:
			recDeleteAllLayoutItems(layout.itemAt(i))

####### ABOUT ###########

def getEulaText():
	"""get the most recent eula.
	"""
	
	eulaText = "MANSUR"

	mansurPath = __import__(__name__.split('.')[0]).__path__[0].replace("\\", "/")
	versiondir = os.path.dirname(os.path.dirname(mansurPath))

	for root, dirs, files in os.walk(versiondir):
		for file in files:
			if file == "LICENSE":
				fullEulaPath = os.path.join(root, file)
				lines = []
				if sys.version_info[0] >= 3:
					lines = list(open(fullEulaPath, 'r', encoding='utf-8'))
				else:
					lines = list(open(fullEulaPath, 'r'))
				eulaText = ""
				for line in lines: eulaText += line
				break
				
	return eulaText

def createAboutWindow():
	"""Load about dialog
	"""
	
	version = mnsUtils.getCurrentVersion()

	if pm.window("mnsAbout", exists=True):
		try:
			pm.deleteUI("mnsAbout")
		except:
			pass

	MnsAbout(get_maya_window(), version)

def toQtObject(mayaName, **kwargs):
	"""Convert a maya UI component into a QT object
	"""

	objectTypeTarget = kwargs.get("objectTypeTarget", QtWidgets.QMenu)

	if mayaName:
		ptr = apiUI.MQtUtil.findControl(mayaName)
		if not ptr:
			ptr = apiUI.MQtUtil.findLayout(mayaName)
		if not ptr:
			ptr = apiUI.MQtUtil.findMenuItem(mayaName)
		if ptr:
			return shiboken2.wrapInstance(int(ptr), objectTypeTarget)

def getWindow(windowName = ""):
	previousWindow = None
	if windowName:
		if pm.window(windowName, exists=True):
			previousWindow = toQtObject(windowName).window()
	return previousWindow

def reloadWindow(windowName = ""):
	if windowName:
		previousPosition = None
		if pm.window(windowName, exists=True):
			previousWindow = toQtObject(windowName)
			if previousWindow: previousPosition = previousWindow.pos()
			
			try: pm.deleteUI(windowName)
			except: pass
			
			return previousPosition

def fourKWindowAdjust(window):
	if window:
		prefs = mnsUtils.getMansurPrefs()
		if "Global" in prefs.keys() and prefs["Global"]["attempt4KmonitorFix"]:
			newWidth = window.width() * 2
			newHeight = window.height() * 2
			maxWidth = window.maximumWidth()
			maxHeight = window.maximumHeight()
			
			if maxWidth < newWidth:
				window.setMaximumWidth(maxWidth * 2)
			if maxHeight < newHeight:
				window.setMaximumHeight(maxHeight * 2)

			window.resize(newWidth,newHeight)

def fourKWindowRevert(window):
	if window:
		prefs = mnsUtils.getMansurPrefs()
		if "Global" in prefs.keys() and not prefs["Global"]["attempt4KmonitorFix"]:
			newWidth = window.width() / 2
			newHeight = window.height() / 2
			window.resize(newWidth,newHeight);