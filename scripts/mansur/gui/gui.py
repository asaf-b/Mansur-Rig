"""=== Author: Assaf Ben Zur ===
GUI Utility function assembly.
"""

#global dependencies


from maya import cmds
import pymel.core as pm

import os
from functools import partial

#mns dependencies
from ..core import string as mnsString
from ..core import utility as mnsUtils
from ..core import UIUtils as mnsUIUtils
from ..core.globals import *

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtWidgets, QtCore
	from PySide6.QtWidgets import QTreeWidgetItem
	from PySide6.QtWidgets import QFrame
	from PySide6.QtCore import Qt
	from PySide6.QtWidgets import QApplication
	from PySide6.QtCore import QEvent
else:
	from PySide2 import QtGui, QtWidgets, QtCore
	from PySide2.QtWidgets import QTreeWidgetItem
	from PySide2.QtWidgets import QFrame
	from PySide2.QtCore import Qt
	from PySide2.QtWidgets import QApplication
	from PySide2.QtCore import QEvent

#python3 exceptions
import sys
if sys.version_info[0] >= 3:
	unicode = str

def windowResizeEvent(window, QResizeEvent):
	if window.isMinimized():
		QResizeEvent.ignore()
		window.showNormal()
		
def windowCloseEvent(window, QCloseEvent):
	if window.isMinimized():
		window.showNormal()
		QCloseEvent.ignore()
	else:
		window.close()

class mnsTitleBar(QtWidgets.QWidget):
	def __init__(self, parent, title):
		super(mnsTitleBar, self).__init__()
		
		self.setAccessibleName("TitleBar")
		self.parent = parent
		self.title = title

		self.setFixedHeight(34)
		
		self.parent.header.setContentsMargins(0,0,0,0)
		self.parent.header.setAccessibleName("TitleBar")
		
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(14,6,14,6)
		
		self.titleIcon = QtWidgets.QLabel()
		self.titleIcon.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/titleBar/windowIcon.png"))
		self.titleIcon.setFixedWidth(25)

		self.title = QtWidgets.QLabel(self.title)
		self.title.setAccessibleName("TitleBar")
		
		
		btn_size = 23
		self.btn_min = QtWidgets.QPushButton()
		self.btn_min.setAccessibleName("TitleBar")
		self.btn_min.setFixedSize(btn_size, btn_size)
		self.btn_min.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/titleBar/minimizeWindow.png"))
		self.btn_min.setIconSize(QtCore.QSize(12, 12))
		self.btn_min.released.connect(self.parent.showMinimized)

		self.btn_close = QtWidgets.QPushButton()
		self.btn_close.setAccessibleName("TitleBar")
		self.btn_close.setFixedSize(btn_size,btn_size)
		self.btn_close.setIcon(QtGui.QIcon(GLOB_guiIconsDir + "/titleBar/closeWindow.png"))
		self.btn_close.setIconSize(QtCore.QSize(12, 12))
		self.btn_close.released.connect(self.parent.hide)

		self.layout.addWidget(self.titleIcon)
		self.layout.addWidget(self.title)
		self.layout.addWidget(self.btn_min)
		self.layout.addWidget(self.btn_close)

		self.setLayout(self.layout)

		self.start = QtCore.QPoint(0, 0)
		self.pressing = False

	def mousePressEvent(self, event):
		self.start = self.mapToGlobal(event.pos())
		self.pressing = True

	def mouseMoveEvent(self, event):
		if self.pressing:
			self.end = self.mapToGlobal(event.pos())
			self.movement = self.end-self.start
			self.parent.setGeometry(self.mapToGlobal(self.movement).x(),
								self.mapToGlobal(self.movement).y(),
								self.parent.width(),
								self.parent.height())
			self.start = self.end

	def mouseReleaseEvent(self, QMouseEvent):
		self.pressing = False

def setWindowHeader(window, title):
	if window:
		#set window attributes
		window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint)
		window.setAttribute(Qt.WA_TranslucentBackground, True)
		window.menubar.setHidden(True)
		window.centralwidget.layout().setContentsMargins(0, 0, 0, 0)
		
		window.headerLayout.addWidget(mnsTitleBar(window, title))

def setWindowStyleSheet(window, **kwargs):
	if window:
		guiStyle = kwargs.get("guiStyle", mnsUIUtils.getGuiStyle())
		if guiStyle:
			window.setStyleSheet(guiStyle)

def setGuiStyle(window, title):
	setWindowStyleSheet(window)
	setWindowHeader(window, title)
	