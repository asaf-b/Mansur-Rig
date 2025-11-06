from .core import globals as mnsGlobals
import os

if mnsGlobals.GLOB_pyVer > 2:
	from importlib import reload

reload(mnsGlobals)

from .core import prefixSuffix
reload(prefixSuffix)
from .core import string as mnsString
reload(mnsString)
from .core import arguments as mnsArgs
reload(mnsArgs)
from .core import meshUtility as mnsMeshUtils
reload(mnsMeshUtils)
from .core import log as mnsLog
reload(mnsLog)
from .core import utility as mnsUtils
reload(mnsUtils)
from .core import UIUtils as mnsUIUtils
reload(mnsUIUtils)
from .core import skinUtility as mnsSkinUtils
reload(mnsSkinUtils)
from .core import nodes as mnsNodes
reload(mnsNodes)
from .globalUtils import defSearch as mnsDefSearch
reload(mnsDefSearch)
from .globalUtils import dynUI as mnsDynUI
reload(mnsDynUI)
#from . import block as mnsBlock
#reload(mnsBlock)
from .block.core import buildModules as mnsBuildModules
reload(mnsBuildModules)
from .block import blockBuildUI as blkUI
reload(blkUI)
from .block.core import controlShapes as blkCtrlShps
reload(blkCtrlShps)
from .block.core import blockUtility as blkUtils
reload(blkUtils)
from .block.picker2 import picker2 as mnsPicker
reload(mnsPicker)
from .block.picker2 import plgSettings as mnsPlgSettings
reload(mnsPlgSettings)
from .preferences import preferences as mnsPreferences
reload(mnsPreferences)
from . import mnsMayaMenu as mnsMayaMenu
reload(mnsMayaMenu)
from .block.moduleVisUI import moduleVisUI as mnsModuleVisUI
reload(mnsModuleVisUI)
from .block.cnsTool import cnsTool as mnsCnsTool
reload(mnsCnsTool)
from .block.characterDefenition import characterDefenitionUI as mnsCharDef
reload(mnsCharDef)
from .block.springTool import mnsSpringTool
reload(mnsSpringTool)
from .block.spacesTool import mnsSpacesTool
reload(mnsSpacesTool)
from .block.LODsTool import LODsTool as mnsLODsTool
reload(mnsLODsTool)
from .block.modulePresetEditor import modulePresetEditor as mnsModulePresetEditor
reload(mnsModulePresetEditor)
from .globalUtils import facialMocap as mnsFacialMocap
reload(mnsFacialMocap)
from .globalUtils.facialMocap import facialMocapUtils as mnsFacialMocapUtils
reload(mnsFacialMocapUtils)
from .globalUtils.animationExporter import mnsAnimationExporter as mnsAnimExporter
reload(mnsAnimExporter)
from .globalUtils.jointRadiusTool import mnsJointRadiusTool
reload(mnsJointRadiusTool)
from .gui import gui as mnsGui
reload(mnsGui)

reload(mnsJointRadiusTool)

mnsUtils.updateMansurPrefs()
mnsUIUtils.readGuiStyle()

from maya import cmds
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui
else:
	from PySide2 import QtGui

fontsDir = os.path.dirname(__file__) + "/gui/fonts/"
for font in os.listdir(fontsDir):
	fontDir = fontsDir + font
	QtGui.QFontDatabase.addApplicationFont(fontDir)

from maya import mel
mel.eval("help -popupMode true;windowPref -saveMainWindowState startupMainWindowState;")