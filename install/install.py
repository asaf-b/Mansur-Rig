from ctypes import *
import platform
from maya import cmds

def linux_mnsInstall(varValue = "", mode = "install", varName = "MAYA_MODULE_PATH"):
	import os
	
	mayaEnvFile = os.environ["MAYA_APP_DIR"] + "/" + cmds.about(version=True) + "/Maya.env"
	if os.path.isfile(mayaEnvFile):
		lines = tuple(open(mayaEnvFile, 'r'))
		lines = [x.strip() for x in lines] 
		
		newLines = []
		existingLine = ""
		continueInstall = True
		for value in lines:
			if varName in value:
				for keyVal in value.split(";"):
					if "mansurRig" in keyVal and mode == "install":
						currentVersion = keyVal.split("_")[-1]
						requestedVersion = varValue.split("/")[-1].split("_")[-1]
						if currentVersion != requestedVersion:
							reply = cmds.confirmDialog( title='Override existing version', message="Another version of Mansur-Rig is already installed: \'" + currentVersion + "\'.\nAre you sure you want to override it?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No', icon = "question")
							if(reply != 'Yes'): continueInstall = False
						else:
							continueInstall = False
							cmds.confirmDialog(title='Requested version exists', message='The requested version of Mansur-Rig is already installed.', defaultButton='OK')
					if continueInstall:
						existingLine = value.strip().split("=")[-1]
			else:
				newLines.append(value)
				
		if continueInstall:
			value = ';'.join([s for s in existingLine.split(';') if not r'mansurRig' in s])

			if mode == "install":
				if not value: value +=  varValue
				elif value.endswith(';'): value += varValue
				else: value += ";" + varValue
			
			if value:
				newLines.append(varName + "=" + value)       
			
			with open(mayaEnvFile, "w") as eFile:
				for line in newLines:
					eFile.write(line)
					eFile.write("\n")
			return True
		
def win_mnsInstall(varValue = "", mode = "install", varName = "MAYA_MODULE_PATH"):
	import sys
	if sys.version_info.major > 2:
		import winreg as reg
	else:
		import _winreg as reg

	key = reg.OpenKey(reg.HKEY_CURRENT_USER, 'Environment', 0, reg.KEY_ALL_ACCESS)
	
	try:
		value, _ = reg.QueryValueEx(key, varName)
	except WindowsError:
		value = ""


	continueInstall = True
	for keyVal in value.split(";"):
		if "mansurRig" in keyVal and mode == "install":
			currentVersion = keyVal.split("_")[-1]
			requestedVersion = varValue.split("/")[-1].split("_")[-1]
			if currentVersion != requestedVersion:
				reply = cmds.confirmDialog( title='Override existing version', message="Another version of Mansur-Rig is already installed: \'" + currentVersion + "\'.\nAre you sure you want to override it?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No', icon = "question")
				if(reply != 'Yes'): continueInstall = False
			else:
				continueInstall = False
				cmds.confirmDialog(title='Requested version exists', message='The requested version of Mansur-Rig is already installed.', defaultButton='OK')

	if continueInstall:
		value = ';'.join([s for s in value.split(';') if not r'mansurRig' in s])
		
		if mode == "install":
			if not value: value += varValue
			elif value.endswith(';'): value += varValue
			else: value += ";" + varValue
			
		reg.SetValueEx(key, varName, 0, reg.REG_EXPAND_SZ, value)
		reg.CloseKey(key)
		
		HWND_BROADCAST = 65535
		WM_SETTINGCHANGE = 26
		SMTO_ABORTIFHUNG = 2
		
		result = c_long()
		user32dll = windll.user32
		
		user32dll.SendMessageTimeoutA(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 100, byref(result))
		
		mayaVersion = int(cmds.about(version=True))
		if sys.version_info.major > 2 or mayaVersion > 2020:
			HWND_BROADCAST = 0xFFFF
			WM_SETTINGCHANGE = 0x1A
			SMTO_ABORTIFHUNG = 0x0002
			user32dll.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 5000, byref(result))

		return True

def mnsInstall(requestPath = "", **kwargs):
	mode = kwargs.get("mode", "install")

	requestedVersion = requestPath.split("/")[-1].split("_")[-1]
	if mode == "uninstall":
		reply = cmds.confirmDialog( title='UNINSTALL', message="Are you sure you want to uninstall Mansur-Rig?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No', icon = "question")
	else:
		reply = cmds.confirmDialog( title='Mansur-Rig Install', message='Are you sure you want to install Mansur-Rig version \'' + requestedVersion + "\'?", button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No', icon = "question")
	
	if(reply == 'Yes'):
		installed = False
		if platform.system().lower() == "windows":
			installed = win_mnsInstall(requestPath, mode)
		elif platform.system().lower() == "linux":
			installed = linux_mnsInstall(requestPath, mode)
		else:
			reply = cmds.confirmDialog( title='Mansur-Rig Install', message='Unsupported platform.\nPlease visit \'mansurRig.com\' website for details.', defaultButton='Ok', icon = "critical")

		if installed:
			if mode == "uninstall":
				cmds.confirmDialog( title='Uninstalled Mansur-Rig Successfully', message='Mansur-Rig uninstalled successfully! \nPlease resteart maya for the changes to take effect.', defaultButton='OK')
			else:
				cmds.confirmDialog( title='Installed Mansur-Rig Successfully', message='Mansur-Rig installed successfully! \nPlease resteart maya for the changes to take effect.', defaultButton='OK')