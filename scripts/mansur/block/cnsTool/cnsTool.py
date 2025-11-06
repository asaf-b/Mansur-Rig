"""=== Author: Assaf Ben Zur ===
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from functools import partial

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import string as mnsString
from ...core import nodes as mnsNodes
from ...core.globals import *
from ...gui import gui as mnsGui
from ..core import blockUtility as blkUtils

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtCore, QtWidgets
else:
	from PySide2 import QtGui, QtCore, QtWidgets

form_class, base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "cnsTool.ui")

class MnsCnsTool(form_class, base_class):
	"""Main UI Class
	"""

	def __init__(self, parent=mnsUIUtils.get_maya_window()):
		#initialize UI
		super(MnsCnsTool, self).__init__(parent)
		self.setupUi( self )
		self.setObjectName("mnsCnsTool") 
		self.iconLbl.setPixmap(QtGui.QPixmap(GLOB_guiIconsDir + "/logo/mansur_01.png"))

		mnsUtils.updateMansurPrefs()
		mnsUIUtils.fourKWindowAdjust(self)
		
		self.cnsTree_trv.setColumnWidth(0, 200)
		self.cnsTree_trv.setColumnWidth(1, 200)

		#locals
		self.rigTops = {}
		self.existingCnsDict = {}

		#methods
		self.connectSignals()
		self.initializeUI()
		mnsGui.setGuiStyle(self, "CNS Tool")

	def connectSignals(self):
		"""Connect all UI signals
		"""

		self.createCns_btn.released.connect(self.createCnsForSelection)
		self.cnsTree_trv.itemClicked.connect(self.selectCnsFromTree)
		self.removeCns_btn.released.connect(self.removeCnsFromSelection)

	def selectCnsFromTree(self):
		currentItem = self.cnsTree_trv.currentItem()
		if currentItem:
			if currentItem in self.existingCnsDict:
				try:
					pm.select(self.existingCnsDict[currentItem].node, r = True)
				except:
					pass

	def initializeUI(self):
		self.cnsTree_trv.clear()
		self.existingCnsDict = {}
		self.rigTops = blkUtils.getRigTopAssemblies()
		
		for rigTop in self.rigTops:
			exsitingCnsCtrls = blkUtils.getExisingCnsCtrlsForRigTop(self.rigTops[rigTop])
			if exsitingCnsCtrls:
				for cnsCtrlKey in exsitingCnsCtrls.keys():
					item = QtWidgets.QTreeWidgetItem(self.cnsTree_trv, [cnsCtrlKey, self.rigTops[rigTop].name])
					self.existingCnsDict.update({item: exsitingCnsCtrls[cnsCtrlKey]})

	def createCnsForSelection(self):
		status = blkUtils.createCnsForCtrls()
		if status:
			self.initializeUI()

	def removeCnsFromSelection(self):
		status = blkUtils.removeCnsFromCtrls()
		if status:
			self.initializeUI()

	def loadWindow(self):	
		"""Main UI load
		"""
		self.show()
		
def loadCnsTool():
	"""Load the cns tool UI from globals, avoid UI duplication.
	"""
	
	previousPosition = mnsUIUtils.reloadWindow("mnsCnsTool")

	mnsCnsToolWin = MnsCnsTool()
	mnsCnsToolWin.loadWindow()
	if previousPosition: mnsCnsToolWin.move(previousPosition)