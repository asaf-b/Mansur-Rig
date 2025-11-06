"""=== Author: Assaf Ben Zur ===
Core mns logger.
This module contains the mns logger which will construct a log based on given parametrs.
All logs are written to the defined log file dectated by the project globals.
In case a log doesn't exists it will be automatically created."""

#global dependencies
import traceback, inspect, os, datetime

from maya import cmds
if int(cmds.about(version = True)) > 2024:
	import shiboken6 as shiboken2
else:
	import shiboken2

import maya.OpenMayaUI as apiUI

#mns dependencies
from .globals import *
from .prefixSuffix import *

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtCore, QtWidgets, QtGui
else:
	from PySide2 import QtCore, QtWidgets, QtGui

def getCurrentFunctionName():
	return inspect.stack()[1][3]

def getPreviousFunctionName():
	return inspect.stack()[2][3]

def logCurrentFrame():
	"""Log the current requested frame.
	The frame is collected procedurally from the dtack, without needing to pass any arguments into methed.
	"""

	func = getPreviousFunctionName()
	log(func, svr = 0, currentContextRequested = True)

def validateLogRootDirectory():
	"""Validate log directory existence within the current project folder.
	"""

	from . import utility as mnsUtils
	prefDir = mnsUtils.locatePreferencesDirectory()
	logDirectory = prefDir + "/mnsLog" 
	logFileDirectory = logDirectory + "/primary.mnsLog"

	if not os.path.isdir(logDirectory): os.makedirs(logDirectory)
	if not os.path.isfile(logFileDirectory): 
		with open(logFileDirectory, 'w'): pass

	#return;string (log directory path)
	return logDirectory

def log(msg = "", **kwargs):
	"""Core logger function.
	Given a message line and a severity parameter, log the line into the log file.
	In case the log file doesn't exist, create one.
	In case the directory doesn't exist, create one.
	An output message is printed into the consule based on the severity.
	severities(svr):
		0 = log
		1 = msg
		2 = warning
		3 = error
		4 = fatal
	"""

	from . import utility as mnsUtils

	svr = kwargs.get("svr", 0) #arg; min = 0; max = 4; comment = set the sevarity of the log message;
	currentContextRequested = kwargs.get("currentContextRequested", False) #arg; comment = in case a global context log was called
	supressMessages = kwargs.get("supressMessages", False)

	#get variables
	#logFile = validateLogRootDirectory() + "/primary.mnsLog"

	dbgMode = 1
	typ = type(svr).__name__
	if typ != 'int': 
		svr = 0
	elif svr < 0:
		svr = 0
	elif svr > 4:
		svr = 4
		
	typ = type(dbgMode).__name__
	if typ != 'int': 
		dbgMode = 0
	elif dbgMode < 0:
		dbgMode = 0
	elif dbgMode > 4:
		dbgMode = 4
	

	indtDepth = len(traceback.extract_stack()) - 2
	if currentContextRequested: indtDepth -= 1
	curframe = inspect.currentframe()
	calframe = inspect.getouterframes(curframe, 2)

	frameIndex = 1
	if currentContextRequested: frameIndex += 2
	callerFun = calframe[frameIndex][3]
	if callerFun == "<lambda>": callerFun = calframe[frameIndex - 1][3]
	if callerFun == "<module>": callerFun = calframe[frameIndex][1]

	timeStp = str(datetime.datetime.now())
	timeStp = timeStp.replace(" ", "-").split("-")
	timeStamp = timeStp[2] + "/" +  timeStp[1] + "/" + timeStp[0] +" "+ timeStp[3]

	severityPrint = "log"
	if svr ==  1:
		severityPrint = "msg"
	elif svr ==  2:
		severityPrint = "warning"
	elif svr == 3:
		severityPrint = "error"
	elif svr == 4:
		severityPrint = "fatal" 

	log = str(svr) + '][' + timeStamp +  '][' + GLOB_user + '][' + str(indtDepth) +'][' + msg + '][' + callerFun
	userMsg = '==' + "Mansur" + '==  [' + severityPrint + '] ' + msg + ' (' + callerFun + ')'
	
	dolog = 0
	doMsg = 0      

	if dbgMode != 0:
		if dbgMode < 3:
			dolog = 1
		if dbgMode == 3:
			if svr > 0:
				dolog = 1
		elif dbgMode == 4:
			if svr > 1:
				dolog = 1
			
	if svr != 0:
		if dbgMode != 2:
			doMsg = 1
	
	"""
	if dolog == 1:
		logfile = open(logFile, 'a')    
		logfile.write(log)
		logfile.write(os.linesep)  
		logfile.close() 

		fileSize = 0
		fileSize = int(str(os.stat(logfile.name).st_size).replace("L",""))

		allLine = tuple(open(logfile.name, 'r'))

		if fileSize > mnsUtils.getMansurPrefs()["Global"]["logFileSizeLimit"] * 1000:
			with open(logfile.name, 'w') as outFile: 
				toDelete = 200
				count = 0
				for line in allLine: 
					if count > toDelete: outFile.write(line)
					count += 1
	"""

	if doMsg == 1 and not supressMessages:
		print(userMsg)


	### log into BLOCK UI
	ptr = apiUI.MQtUtil.mainWindow()
	if pm.window("mnsBLOCK_UI", exists=True):
		blockUI = shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget).findChild(QtWidgets.QMainWindow, "mnsBLOCK_UI")
		if blockUI:
			try: 
				if svr != 0:
					blockUI.echoLog(msg, svr)
			except: pass