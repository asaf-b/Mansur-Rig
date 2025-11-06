from maya import cmds

def pymelExistenceCheck():
	try:
		import pymel.core
	except:
		result = cmds.confirmDialog( title="Mansur-Rig failed to load", message="Mansur-Rig failed to load because a required component- PyMel, isn't installed.\nPlease press \'Help me fix it!' for more information on how to easily resolve this issue", button=["Help me fix it!", "Close"], defaultButton='Help me fix it!', dismissString="Close")
		if result == "Help me fix it!":
			cmds.showHelp("https://docs.mansur-rig.com/userGuides/System-Requirements/#maya-2022-and-above-requirements", absolute=True)

if not cmds.about(batch=True):
	if int(cmds.about(version = True)) > 2020:
		maya.utils.executeDeferred(pymelExistenceCheck)
	else:
		cmds.evalDeferred(pymelExistenceCheck)

from mansur import mnsMayaMenu
from mansur.core import utility as mnsUtils
from mansur.licensing import licensingUI as mnsLicensing

if not cmds.about(batch=True):
	if int(cmds.about(version = True)) > 2020:
		maya.utils.executeDeferred(mnsMayaMenu.createMansurMayaMenu)
		maya.utils.executeDeferred(mnsLicensing.autoLogin)
		maya.utils.executeDeferred(mnsUtils.autoLoadMnsPlugins)
	else:
		cmds.evalDeferred(mnsMayaMenu.createMansurMayaMenu)
		cmds.evalDeferred(mnsLicensing.autoLogin)
		cmds.evalDeferred(mnsUtils.autoLoadMnsPlugins)