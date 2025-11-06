"""=== Author: Assaf Ben Zur ===
Global Core MNS utility module.
This module holds any 'global' function used within MNS.
A 'misc' style module."""

#global dependencies
import fnmatch, imp, os, types, json, math, importlib, pkgutil, re, shutil, socket, platform


from maya import cmds
import pymel.core as pm

from os.path import dirname, abspath
from inspect import getmembers, isfunction
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove
from maya import cmds
import maya.OpenMaya as OpenMaya

#mns dependencies
from . import log as mnsLog
from . import arguments as mnsArgs
from . import string as mnsString
from .prefixSuffix import *
from .globals import *

#python3 exceptions
if GLOB_pyVer > 2: from importlib import reload
import sys
if GLOB_pyVer > 2:
	unicode = str

def getNumLinesForDir(directory = "D:/mansurProject/mansurRig/scripts/mansur"):
	lines = 0
	for r, d, f in os.walk(directory):
		for fileA in f:
			if ".py" in fileA and ".pyc" not in fileA and ".pyd" not in fileA and "__init__" not in fileA:
				lines += len( tuple(open(os.path.join(r, fileA), 'r')))
	print(lines)

def checkFunctionRedundencyForPackage(package, printRedundentOnly = True):
	def import_submodules(package, recursive=True):
		if isinstance(package, str):
			try: package = importlib.import_module(package)
			except: pass

		results = {}
		for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
			skip = 0
			full_name = package.__name__ + '.' + name
			try:
				results[full_name] = importlib.import_module(full_name)
			except:
				skip = 1
				pass

			if recursive and is_pkg:
				if skip != 1:
					results.update(import_submodules(full_name))

		return results

	def listPackageFunctions(package):   
		library = []
		pkgMods = import_submodules(package.__name__)
		for mod in pkgMods:
			functions_list = [o for o in getmembers(pkgMods[mod]) if isfunction(o[1])]
			for fun in functions_list:
				library.append(fun[0])
	 
		return library


	allFunctions = listPackageFunctions(package)
	allPythonFiles = []  
	directory = os.path.dirname(package.__file__)
	for root, dirs, files in os.walk(directory):
		for file in files:
			if not "__init__" in file and file.endswith(".py"):
				 allPythonFiles.append(os.path.join(root, file))
	

	print("============== Function Redundency Check ==============\n")
	for funcName in allFunctions:    
		occurencesCount = 0     
		for pythonFile in allPythonFiles: 
			with open(pythonFile) as f:
				fileLines = f.readlines()
		
			for line in fileLines:
				if funcName in line and not ("def " + funcName) in line: occurencesCount += 1
				
		if occurencesCount > 0:
			if not printRedundentOnly:
				print(funcName + " (" + str(occurencesCount) + ")")
		else:
			print("************************** [redundent] " + funcName + " [redundent] **************************")
			
	print("\n=====================================================")

def reloadLib():
	mansur = __import__(__name__.split('.')[0])
	reload(mansur)

	if 'init_modules' in globals(  ):
		# second or subsequent run: remove all but initially loaded modules
		for m in sys.modules.keys(  ):
			if m not in init_modules:
				del(sys.modules[m])
		else:
			# first run: find out which modules were initially loaded
			init_modules = sys.modules.keys(  )

def checkIfObjExistsAndSet(objB = None, **kwargs):
	"""For the object passed in-
	three main cases:
		1. If it is a 'PyNode' object, set it as the object to check.
		2. If it is an MnsNameStd object,set it's .node property as the object to check.
		3. If it is a string, assign it into a 'PyNode' obhect and set it as the object to check.
	Check whether the object exists in the current scene and valid.
	If so, return it. Else return None."""

	objA = kwargs.get("obj", objB) #arg; comment = object to act on and return
	namesapce = kwargs.get("namespace", "") #arg;
	childOf = kwargs.get("childOf", None)

	returnObj = None

	if objA:
		objType = type(objA)
		if objType == MnsNameStd: objA = objA.node

		if objType is str or objType is unicode:
			if namesapce: objA = namesapce + ":" + objA

			if objA != "" and objA is not None:
				if childOf:
					allMatches = None
					try:
						allMatches = pm.ls(objA, long = True)
					except:
						pass

					if allMatches and len(allMatches) > 1:
						for o in  allMatches:
							if childOf in o.getAllParents():
								return pm.PyNode(o)
								break
					elif pm.objExists(objA):
						return pm.PyNode(objA)
				
				elif pm.objExists(objA):
						return pm.PyNode(objA)
		else:
			if pm.objExists(objA): 
				return objA

	#return;PyNode if valid, None if not. 
	return returnObj

def createNodeReturnNameStd(**kwargs):
	"""A core major MNS function.
	This function creates a new node, based on it's type passed in, and it's name parameters passed in, and returns it as a MnsNameStd object.

	This function also contains the 'search for next valid name' functionallity:
		In case the given parameter set returns an object name that already exists within the current scene a 'Handle' functionallity will be triggered:
			- In case the 'IncrementAlpha' argument is Flase, recursivly increment the ID value until a new name slot is available within the scene.
			- In case it's Flase, do the same while incrementing the Alpha value instead.

	Unlike Maya's core behavior- This function tests whether an object name exists whithin the entire scene- not only whether it exists whithin the current hirarchy level.
	In a sequence manner creation- the Alpha/ID should be incremented within the caller function loop- meaning while bulding an item sequence the 'search' functionallity should not be used.

	Another funtionallity of this function is the 'Fix Shape Name' functionallity:
	A simple shpe children name test of an object (after creation) and a renaming them."""


	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "pointsOnCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	buildType = mnsTypeDict[kwargs.get("buildType", 0)] #arg; 
	createBlkClassID = kwargs.get("createBlkClassID", False) #arg; 
	createBlkCtrlTypeID = kwargs.get("createBlkCtrlTypeID", False) #arg; 
	blkCtrlTypeID = kwargs.get("blkCtrlTypeID", 0) #arg; optionBox = primary, secondary, tertiary, gimble, pivot
	parentNode = kwargs.get("parentNode", None) #arg; 
	segmentScaleCompensate = kwargs.get("segmentScaleCompensate", False) #arg; 
	
	nameStdA = MnsNameStd(side = side, body = body, alpha = alpha, id = id, type = buildType)
	preSequel = nameStdA.name
	if not incrementAlpha : nameStdA.findNextIncrement()
	else : nameStdA.findNextAlphaIncrement()

	nodeA = pm.createNode(nameStdA.type.createName, name = nameStdA.name) 
	if type(nodeA) == pm.nodetypes.Joint: nodeA.segmentScaleCompensate.set(segmentScaleCompensate)
	
	if len(pm.listRelatives( nodeA, fullPath=1, parent=True)) > 0: 
		parentA = pm.listRelatives( nodeA, fullPath=1, parent=True )[0]
		if parentA:
			pm.rename(nodeA, (nameStdA.name + "Shape"))
			pm.rename(parentA, (nameStdA.name))
			nodeA = parentA

	
	nameStdA.node = nodeA
	if createBlkClassID: addBlockClasIDToObj(nameStdA)
	if createBlkCtrlTypeID: addAttrToObj([nameStdA.node], name = "blkCtrlTypeID", type = int, value = blkCtrlTypeID, locked = True, cb = False, keyable = False)

	parentNode = validateNameStd(parentNode)
	if parentNode: pm.parent(nameStdA.node, parentNode.node)

	#return;MnsNameStd
	return nameStdA

def objectArrayValidExistsCheckReturn(**kwargs):
	"""MNS core object array validity check.
	Two main Cases for the mode parameter:
		1. trueOnlyIfAllValid - Run through the objects and only if ALL of them are found existing and valid, return the array back to the caller. If a single item failed- Return None.
		2. trueIfSomeValid - Check all the objects and return any or all of them based on validity.
	"""

	objectArray = kwargs.get("objectArray", []) #arg; comment = Objects input list
	mode = kwargs.get("mode", 0) #arg; optionBox = trueOnlyIfAllValid, trueIfSomeValid ; comment = Validity return mode

	validArray = True
	returnArray = []
	if objectArray:
		for obj in objectArray:
			if type(obj) is MnsNameStd: obj = obj.node
			
			obj = checkIfObjExistsAndSet(obj = obj)
			if obj: returnArray.append(obj)

	if len(returnArray) != len(objectArray): validArray = False

	if not validArray : 
		if(mode == 0): 
			returnArray = None
			mnsLog.log("Input array was found as invalid. Return None", svr = 0)
		elif len(returnArray) > 0:
			mnsLog.log("Input array was found partially valid. Returning partial array.", svr = 0)

	#return;List (Valid object list), None (If found invalid)
	return returnArray

def createAxisLamberts(**kwargs):
	"""An axes colored lambert shaders creation function.
	"""

	doX = kwargs.get("doX", True) #arg; 
	doY = kwargs.get("doY", True) #arg; 
	doZ = kwargs.get("doZ", True) #arg; 
	deleteAll = kwargs.get("deleteAll", False) #arg; comment = If true, do not attempt to create any objects- instead look for any existing objects and delete them
	
	returnDict = {}
	axises = ["x", "y", "z"]
	axisColors = [(1,0,0), (0,1,0), (0,0,1)] 
	k = 0
	for axis in [doX, doY, doZ]:
		axisStd = ""
		if axis or deleteAll:
			axisStd = MnsNameStd(side = "c", alpha = "A", type = MnsTypeStd(name = "lambert", suffix = mnsPS_lambert), body = "axisShader" + axises[k].upper(), id = 1)
			if pm.objExists(axisStd.name): 
				axisStd.node = checkIfObjExistsAndSet(obj = axisStd.name)
				returnDict.update({(axises[k].upper() + "AxisShader"): axisStd.node})
				if deleteAll: 
					pm.delete(axisStd.node)
					returnDict.update({(axises[k].upper() + "AxisShader"): None})
			elif not deleteAll:
				axisStd.node = pm.shadingNode(axisStd.type.createName, asShader=1, name = axisStd.name) 
				axisStd.node.setAttr("color", axisColors[k],  type="double3");
				returnDict.update({(axises[k].upper() + "AxisShader"): axisStd.node})
			else:
				returnDict.update({(axises[k].upper() + "AxisShader"): None})
		else:
			returnDict.update({(axises[k].upper() + "AxisShader"): None})
		k += 1
	
	#return;dict ('X': xAxisLambert, 'Y': yAixsLambert, 'Z': zAxisLambert)			
	return returnDict

def zeroTransforms(transform = ""):
	"""Zero all available transforms for the given object passed in.
	"""

	returnBool = True
	if type(transform).__name__ == "MnsNameStd":
		transform = transform.node
	for axis in "xyz":
		for channel in "rts":
			try:
				if channel != "s":
					transform.setAttr(channel + axis, 0)
				else:
					transform.setAttr(channel + axis, 1)
			except:
				returnBool = False
				pass

	#return;bool
	return returnBool

def splitDateTimeStringToList(dateTime = ""):
	"""Split a 'dateTime' string to a major/minor/patch/timestemp list
	"""

	dateTimeList = []
	charIdx = 0
	mns_DateTimeFormat = [2,2,4,2,2] # day-day, month-month , year-year-year-year, hour-hour, minute-minute
	for zone in mns_DateTimeFormat:
		addString = ""
		for k in range(charIdx, charIdx + zone):
			addString += str(dateTime[k])
		charIdx += zone
		dateTimeList.append(addString)

	#return;list
	return dateTimeList

def convertIntToAlpha(intA = 0):
	"""Recursive. Convert an Int input into an Alpha ID. Infinite.
	"""

	intA += 1
	if intA <= 0:
		return ""
	elif intA <= 26:
		return chr(64+intA)
	else:
		return convertIntToAlpha(int((intA-1)/26))+chr(65+(intA-1)%26)

	#return;string

def convertAlphaToInt(alpha = "A"):
	"""Recursive. Convert an Alpha input into an Int ID. Infinite.
	"""

	alpha = alpha.upper()
	if alpha == " " or len(alpha) == 0:
		return None
	if len(alpha) == 1:
		return ord(alpha)-65
	else:
		return convertAlphaToInt(alpha[1:])+(26**(len(alpha)-1))*(ord(alpha[0])-65)
	
	#return;int

def splitNameStringToNameStd(nameString = ""):
	"""Split a given string object and return a MnsNameStd based on it's structure.
	"""

	side, body, alphaID, suffix = nameString.split("_")
	alpha = ""
	id = ""
	for char in alphaID:
		if char.isdigit():
			id += char
		else: alpha += char
	id = int(id)
	node = checkIfObjExistsAndSet(obj = nameString) 
	typeStd = MnsTypeStd(name = node.type(), suffix = suffix)
	nameStd = MnsNameStd(node= node, side= side, body = body, id = id, alpha = alpha, type = typeStd)

	#return;MnsNameStd
	return nameStd

def returnNameStdChangeElement(nameStd = None, **kwargs):
	"""global MnsNameStd utility-
	Use this function to change any elemnt within a given MnsNameStd object based on keyword args given"""

	if nameStd:
		autoRename = kwargs.get("autoRename",True) #arg;
		bodyPattern = kwargs.get("bodyPattern", None) #arg;

		if "blkSide" in kwargs.keys(): 
			kwargs["side"] = kwargs.pop("blkSide")
			kwargs["side"] = mnsSidesDict[kwargs["side"]]
		newNameStd = nameStd

		if type(nameStd) == MnsNameStd:
			node = kwargs.get("node",nameStd.node) #arg; comment = change node parameter
			side = kwargs.get("side",nameStd.side) #arg; comment = change side parameter
			
			if bodyPattern and "body" in kwargs:
				if bodyPattern != nameStd.body:
					if bodyPattern in nameStd.body:
						bodyArg = kwargs["body"] + nameStd.body.split(bodyPattern)[-1]
						kwargs.update({"body": bodyArg})

			body = kwargs.get("body",nameStd.body) #arg; comment = change body parameter
			typeA = kwargs.get("type", nameStd.type) #arg; comment = change type parameter
			id = kwargs.get("id", nameStd.id) #arg; comment = change id parameter
			alpha = kwargs.get("alpha", nameStd.alpha) #arg; comment = change alpha parameter
			suffix =  kwargs.get("suffix", nameStd.suffix) #arg; comment = change suffix
			comment = kwargs.get("comment",nameStd.comment) #arg; comment = change comment parameter
			newNameStd = MnsNameStd(node = node, side = side, body = body, type = typeA, id = id, alpha = alpha, suffix =suffix, comment = comment)

		if newNameStd.name != nameStd.name and autoRename: pm.rename(nameStd.node, newNameStd.name)

		#return;MnsNameStd
		return newNameStd

def duplicateNameStd(nameStd = None, **kwargs):
	"""Simple method to duplicate a node embedded within a NameStd object.
	This method will duuplicate the node, and rename it by the nameStd rules.
	"""

	parentOnly = kwargs.get("parentOnly", False)

	nameStd = validateNameStd(nameStd)
	if nameStd and nameStd.node:
		newStd = returnNameStdChangeElement(nameStd, autoRename = False)
		newStd.findNextIncrement()
		newNode = pm.duplicate(nameStd.node, parentOnly = parentOnly)[0]
		newStd.node = newNode
		newStd.setNodeName()
		return newStd

def setCtrlColorIdx(objects = [], colorIdx = 0):
	"""Global utility function:
	Change the shape color override to index type, and set to the input value index"""

	if colorIdx > 31: colorIdx = 31
	if colorIdx < 0: colorIdx = 0
	for o in objects:
		if type(o) is str: obj = pm.PyNode(o)
		elif type(o) is MnsNameStd: obj = o.node
		else: obj = o
		
		shapes = obj.getShapes()
		for s in shapes:
			try:
				pm.setAttr(ctrl + ".overrideRGBColors",0)
				pm.setAttr(s + ".overrideEnabled",1)
				pm.setAttr(s + ".overrideColor", colorIdx)
			except: pass

def setCtrlColorRGB(objects = [], color = (1,1,1)):
	"""Global utility function:
	Change the shape color override to RGB type, and set to the input value RGB"""

	for o in objects:
		o = validateNameStd(o)
		
		if o:
			shapes = None
			try: shapes = o.node.getShapes()
			except: pass
			if shapes:
				if o.suffix == "jnt" or o.suffix == "rootJnt" : shapes = [o.node]
				for s in shapes:
					pm.setAttr(s + ".overrideEnabled",1)
					pm.setAttr(s + ".overrideRGBColors",1)
					k = 0
					for channel in "RGB":
						pm.setAttr(s + ".overrideColor" + channel, color[k])
						k+=1
					if not o.node.attr("overrideDisplayType").isConnectedTo(s.attr("overrideDisplayType")):
						if o.node != s:
							try: o.node.attr("overrideDisplayType")>>s.attr("overrideDisplayType")			
							except: pass

def connectShapeColorRGB(source = None, target = None):
	if source: source = validateNameStd(source)
	if target: target = validateNameStd(target)

	if source and target:
		sourceShape = source.node.getShape()
		if target.node.getShape():
			for shape in target.node.getShapes():
				if shape.overrideEnabled.isConnected(): shape.overrideEnabled.disconnect()
				sourceShape.overrideEnabled >> shape.overrideEnabled
				if shape.overrideRGBColors.isConnected(): shape.overrideRGBColors.disconnect()
				shape.overrideRGBColors.set(1)
				if shape.overrideColorRGB.isConnected(): shape.overrideColorRGB.disconnect()
				sourceShape.overrideColorRGB >> shape.overrideColorRGB

def fixShapesName(objects = []):
	"""Simple shape name fix function based on parent's name.
	"""

	for o in objects:
		obj = None
		if type(o) is str: obj = pm.PyNode(o)
		elif type(o) is MnsNameStd: obj = o.node
		else: obj = o

		if obj.getShape():
			shapes = obj.getShapes()
			for shape in shapes:
				pm.rename(shape, obj.nodeName() + "Shape")	
						
def deleteFile(file):
	"""A delete file global function that includes a pre-defined log write.
	"""

	os.remove(file)
	mnsLog.log("Deleting file: " + file, svr = 1)

def getFirstLevelParentForObject(obj):
	"""Get the top level parent for a given object.
	"""
	parentObj = None
	try: parentObj = obj.getParent()
	except: pass
	if parentObj: return getFirstLevelParentForObject(parentObj)
	else: return obj
	#return;pyNode (top level parent)

def addAttrToObj(objects = [], **kwargs):
	"""A global conditioned wrapper for adding attributes to object/objects
	
	Exceptions:
		1. Object to add attr to was found non-existing or invalid. Abort.
		2. The 'replace' flag wasn't set, and the attribute already exists. Abort.
		3. Attr name wasn't passed in. Abort.
		4. The attribute type passed doesn't match the attribute value passed. Abort.
		5. min/max values were passed in, although the attr type is not an Int or a Float. Skip min/max values.
		6. min/max values were passed, and the attr type is Int or Float, although the min/max values passed arn't matching the data type. Skip min/max.
		7. The replace flag was set to True, but the attribute doesn't exist. Ignore replace flag.
		
	"""
	
	if type(objects) is not list: objects = [objects]
	returnObj = []
	
	for obj in objects:
		obj = checkIfObjExistsAndSet(obj = obj)

		if obj:
			attrName = kwargs.get("name", "") #arg; comment = Added attribute name
			replace = kwargs.get("replace", False) #arg; comment = If attr exists and this flag is set to True- delete the existing attribute then recreate according to parameters

			attrExists = False
			try: 
				pm.getAttr(obj.nodeName() + "." +  attrName)
				attrExists = True
			except: pass

			if attrExists and not replace:
				pass
			else:
				attrType = kwargs.get("type", "string") #arg; comment = Added attribute type; optionBox = string, int, float, bool, enum
				attrValue = kwargs.get("value", None) #arg; comment = Added attribute value
				attrMax = kwargs.get("max", None) #arg; comment = Added attribute max (only if float or int)
				attrMin = kwargs.get("min", None) #arg; comment = Added attribute min (only if float or int)
				locked = kwargs.get("locked", False) #arg; comment = Added attribute lock state
				channelBoxF = kwargs.get("cb", True) #arg; comment = Added attribute channelBox/Displayed state
				keyable = kwargs.get("keyable", True) #arg; comment = Added attribute keyable state
				enumDefault = kwargs.get("enumDefault", 0) #arg; comment = If added attr is enum, set its default to this value

				
				if attrType is unicode: attrType = str
				if type(attrValue) is unicode: attrValue = str(attrValue)
				if type(attrType) is str: 
					attrType = attrType.lower()
					if attrType == "string" or attrType == "str": attrType = str
					if attrType == "int" or attrType == "short": attrType = int
					if attrType == "float" or attrType == "double" or attrType == "long": attrType = float
					if attrType == "bool" or attrType == "boolean" or attrType == "binary": attrType = bool
					if attrType == "enum" or attrType == "list": attrType = list
					if attrType == "message" or attrType == "msg": attrType = "message"

				if attrType is bool and attrValue > 0: attrValue = True
				if attrType is bool and attrValue == "on": attrValue = True
				if attrType is bool and attrValue == "1": attrValue = True
				if attrType is bool and attrValue == 0: attrValue = False
				if attrType is bool and attrValue == "off": attrValue = False
				if attrType is bool and attrValue == "0": attrValue = False

				if attrName:
					if type(attrValue) is str and attrType is int:
						try: attrValue = int(attrValue)
						except: pass
					if type(attrValue) is str and attrType is float:
						try: attrValue = float(attrValue)
						except: pass

					if type(attrValue) is attrType or attrType == "message":
						attrTypeName = None
						if attrType is str: attrTypeName = "string"
						if attrType is int: attrTypeName = "short"
						if attrType is float: attrTypeName = "double"
						if attrType is bool: attrTypeName = "bool"
						if attrType is list: attrTypeName = "enum"
						if attrType == "message": attrTypeName = "message"

						if attrTypeName:
							attrExists = False
							try: 
								pm.getAttr(obj.nodeName() + "." +  attrName)
								attrExists = True
							except: pass
							if attrExists and replace:
								oldAttr = obj.attr(attrName)
								oldAttr.setLocked(False)
								pm.deleteAttr(oldAttr)
							
							if attrType is str: obj.addAttr(attrName, dt = attrTypeName)
							elif attrType == list: 
								stringValues = mnsString.flattenArrayColon(attrValue)
								pm.addAttr(obj, ln=attrName, at="enum", enumName=stringValues)
							else: 
								obj.addAttr(attrName, at = attrTypeName)

							newAttr = obj.attr(attrName)

							if attrType == "message": 
								connectNode = checkIfObjExistsAndSet(obj = attrValue)
								if connectNode: connectNode.message >> newAttr
							elif attrType is not list: 
								newAttr.set(attrValue)
								if not attrType is str and not attrType is unicode: 
									pm.addAttr(newAttr, e = True, dv = attrValue)
							else: 
								newAttr.set(enumDefault)
								pm.addAttr(newAttr, e = True, dv = enumDefault)
							
							if attrMax or attrMin:
								if type(attrMax) is str and attrType is int:
									try: attrMax = int(attrMax)
									except: pass
								if type(attrMax) is str and attrType is float:
									try: attrMax = float(attrMax)
									except: pass

								if type(attrMin) is str and attrType is int:
									try: attrMin = int(attrMin)
									except: pass
								if type(attrMin) is str and attrType is float:
									try: attrMin = float(attrMin)
									except: pass

								if attrType is int or attrType is float:
									try:
										if type(attrMax) is attrType:
											pm.addAttr(newAttr, e = True, maxValue = attrMax) 
									except: pass
									try:
										if type(attrMin) is attrType: 
											pm.addAttr(newAttr, e = True, minValue = attrMin) 
									except: pass
								else: mnsLog.log("min/Max flags ignored ('" + attrName + "'). The attr type is not an int or float type.", svr = 2)
							
							if locked: newAttr.setLocked(True)
							if channelBoxF: newAttr.showInChannelBox(True)
							if keyable: newAttr.setKeyable(True)
							returnObj.append(newAttr)
							
						else: mnsLog.log("Couldn't add attribute '" + attrName + "' - the attr type is invalid.", svr = 0)
					else: mnsLog.log("Couldn't add attribute '" + attrName + "' - the attribute value passed '" + str(attrValue) +"' does not match the attr type passed", svr = 0)
				else: mnsLog.log("Couldn't add attribute- attr name wasn't passed in.", svr = 0)
		else: mnsLog.log("Couldn't add attribute- the object passed is invalid", svr = 1)
		
	#return; list (added attributes 'attr' objects list)
	return returnObj

def readSetteingFromFile(settingsPath):
	"""Read mns setting from a given file and collect into a dict.
	"""

	if os.path.isfile(settingsPath):
		lines = tuple(open(settingsPath, 'r'))
		src = [x.strip() for x in lines] 
		args, optArgs = mnsArgs.extractArgsFromSource(src)

		#return;dict (arguments)
		return optArgs
	else:
		return None

def getTopParentForObj(obj):
	"""Recursively attempt to fet the top node of the maya heirarchy, from the given input upwards.
	"""

	obj = checkIfObjExistsAndSet(obj = obj)
	if obj:
		if obj.getParent(): return getTopParentForObj(obj.getParent())
		else: 
			#return;MnsNameStd (Top Parent)
			return validateNameStd(obj)
	
def getTopParentForSel():
	"""get the top node of the current selected object's maya heirarchy.
	"""

	topParent = None
	sel = None
	try: sel = pm.ls(sl=1)[0]
	except: 
		mnsLog.log("No Selection. Aborting.", svr = 1)
		pass
	if sel: topParent = getTopParentForObj(sel)

	#return;MnsNameStd (Top Parent)
	return topParent

def lockAndHideTransforms(node = None, **kwargs):
	"""Based on the given flags, lock/unlock, hide/unhide attributes for the given node.
	"""

	lock = kwargs.get("lock", False) #arg;
	keyable = kwargs.get("keyable", False) #arg;
	cb = kwargs.get("cb", False) #arg;
	negate = kwargs.get("negateOperation", False) #arg;

	t = kwargs.get("t", True) #arg;
	tx = kwargs.get("tx", t) #arg;
	ty = kwargs.get("ty", t) #arg;
	tz = kwargs.get("tz", t) #arg;

	r = kwargs.get("r", True) #arg;
	rx = kwargs.get("rx", r) #arg;
	ry = kwargs.get("ry", r) #arg;
	rz = kwargs.get("rz", r) #arg;

	s = kwargs.get("s", True) #arg;
	sx = kwargs.get("sx", s) #arg;
	sy = kwargs.get("sy", s) #arg;
	sz = kwargs.get("sz", s) #arg;

	if negate:
		tx = not tx
		ty = not ty
		tz = not tz
		rx = not rx
		ry = not ry
		rz = not rz
		sx = not sx
		sy = not sy
		sz = not sz

	channels = {
				"tx": tx,"ty": ty,"tz": tz,
				"rx": rx,"ry": ry,"rz": rz,
				"sx": sx,"sy": sy,"sz": sz
				}

	returnBool = True
	for chan in channels.keys():
		if channels[chan]:
			try:
				attr = node.attr(chan)
				attr.setLocked(lock)
				attr.showInChannelBox(cb)
				attr.setKeyable(keyable)
			except: 
				returnBool = False
				pass

	#return;bool
	return returnBool

def lockAndHideAllTransforms(node = None, **kwargs):
	"""Lock and hide all of the given node's attributes.
	Override flags can be inserted to skip requested channels.
	"""

	lock = kwargs.get("lock", False) #arg;
	keyable = kwargs.get("keyable", False) #arg;
	cb = kwargs.get("cb", False) #arg;

	t = kwargs.get("t", True) #arg;
	r = kwargs.get("r", True) #arg;
	s = kwargs.get("s", True) #arg;
	x = kwargs.get("x", True) #arg;
	y = kwargs.get("y", True) #arg;
	z = kwargs.get("z", True) #arg;

	chanString = ""
	channels = ["t","r","s"]
	k = 0
	for channel in [t,r,s]:
		if channel: chanString += channels[k]
		k += 1

	axesString = ""
	axes = ["x","y","z"]
	k = 0
	for axis in [x,y,z]:
		if axis: axesString += axes[k]
		k += 1

	returnBool = True
	if type(node).__name__ == "MnsNameStd":
		node = node.node
	for axis in axes:
		for channel in chanString:
			try:
				attr = node.attr(channel + axis)
				attr.setLocked(lock)
				attr.showInChannelBox(cb)
				attr.setKeyable(keyable)
			except: 
				returnBool = False
				pass

	#return;bool
	return returnBool

def convertNodeToNameStd(node):
	"""Attempt to convert a given node into a MnsNameStd object.
	"""

	node = checkIfObjExistsAndSet(obj = node)
	if node:
		nameSTD = MnsNameStd()
		nameSTD.node = node
		nameSTD.splitName()
		return nameSTD

def returnKeyFromElementTypeDict(dict, searchElement):
	for key, element in dict.items():
		if element.suffix == searchElement:
			try: int(key)
			except:
				return key
				break

def validateNameStd(objectA):
	"""For any input - string/PyNode/MnsNameStd - Validate it and attempt to convert it into a MnsNameStd Object.
	"""

	if objectA:
		if type(objectA) != MnsNameStd:
			obj = checkIfObjExistsAndSet(obj = objectA)
			if obj:
				if "_" in obj.nodeName() and len(obj.nodeName().split(":")[-1].split("_")) == 4:
					return convertNodeToNameStd(objectA)
			else:
				return None
		else: 
			#return;MnsNameStd
			return objectA

def splitEnumToStringList(enumAttrName, node):
	"""Split the given enum attribute is a formated python list.
	"""
	retList = []
	
	l = pm.attributeQuery(enumAttrName, node=node, listEnum=True)
	if l: 
		l = l[0]
		retList = l.split(":")

	#return;list (formated list)
	return retList

def returnIndexFromSideDict(dict, searchElement):
	"""Return the corresponding index from the pre-defined input dictionary, for the given input elenment.
	"""

	retIndex = 0
	fKey = None
	for key, element in dict.items():
		if key == searchElement:
			fKey = element
			break
	for key, element in dict.items():
		if element == fKey:
			try: 
				retIndex = int(key)
				break
			except:
				pass

	#return;int (index)
	return retIndex

def getSideFromNode(node):
	"""Attempt to collect the given input's side.
	"""

	nodeNameStd = MnsNameStd()
	nodeNameStd.node = node
	nodeNameStd.splitName()
	if nodeNameStd.side == mnsPS_cen: nodeNameStd.side = "center"
	elif nodeNameStd.side == mnsPS_left: nodeNameStd.side = "left"
	elif nodeNameStd.side == mnsPS_right: nodeNameStd.side = "right"

	#return;string (side)
	return nodeNameStd.side

def importModuleFromPath(path):
	"""Attempt to import the given path as a python package into the global scope.
	"""

	plugins = types.ModuleType("customModules")
	plugins.__path__ = ["customModules"]
	if os.path.isfile(path): return imp.load_source('customModules', path)
	else: return None

	#return;pythonPkg

def sortNameStdArrayByID(nameStdArray):
	"""Attempt to sort the given array based on it's content ID's.
	"""

	returnArray = []
	asDict = {}
	k = 0
	
	for nameStd in nameStdArray:
		nameStd = validateNameStd(nameStd)
		if nameStd: asDict.update({nameStd.id: nameStd})
	if asDict: 
		for key in sorted(asDict): returnArray.append(asDict[key]) 
		return returnArray
	else: return nameStdArray
	#return;list (sorted list)

def addBlockClasIDToObj(objectA, **kwargs):
	"""Add a 'blkClassId' Attribute to the given input.
	"""
	objectA = validateNameStd(objectA)

	idString = returnKeyFromElementTypeDict(mnsTypeDict, objectA.suffix)
	addAttrToObj(objectA.node, name = "blkClassID", type = str, value = idString, locked = True, cb = False, keyable = False, replace = 1)
	
	#return;PyAttribute ('blkClassID')
	return objectA.node.attr("blkClassID")

def splitEnumAttrToChannelControlList(enumAttrName, node, **kwargs):
	"""Split a pre-defined 'channel-control' enum attribute into a formatted python dict.
	"""

	defaultRet = {}

	l = None
	fromExistingList = kwargs.get("fromExistingList", False)
	if fromExistingList: l = fromExistingList
	else:
		l = pm.attributeQuery(enumAttrName, node=node, listEnum=True)[0]
		l = l.split(":")
	
	if l:
		t = [False,False,False]
		r = [False,False,False]
		s = [False,False,False]

		enumList = [t,r,s]
		k = 0
		for chan in "trs":
			j = 0
			for axis in "xyz":
				if (chan + axis) in l: enumList[k][j] = True
				j += 1
			k += 1

		retDict = {"t": t, "r": r, "s": s}

		#return;dict (formatted dictionary)
		return retDict

def splitEnumAttrToColorSchemeFloatTupleList(enumAttrName, node):
	node = validateNameStd(node)

	values = []
	l = pm.attributeQuery(enumAttrName, node=node.node, listEnum=True)[0]
	for v in l.split(":"):
		s = v.replace("(", "").replace(")", "").split(",")
		comp = []
		for val in s: comp.append(float(val))
		values.append(tuple(comp))

	#return;list (formatted list of tuples)
	return values

def setAttr(attr, value):
	"""mns set attr.
	Simple method to set attributes. 
	two cases:
	1. attribute isn't locked - set the value
	2. attribute is locked - unlock the attribute, set it's value, and re-lock the attribute.
	"""

	locked = False
	if attr.isLocked(): 
		attr.setLocked(False)
		locked = True
	try: attr.set(value)
	except: pass
	if locked: attr.setLocked(True)

def readJson(fullPath):
	"""Read the input json path into formatted python variables.
	"""

	returnDict = {}
	if os.path.isfile(fullPath):
		try:
			with open(fullPath, "r") as jsonFile:
				returnDict = json.load(jsonFile)
		except: pass

	#return;FormattedPythonJson
	return returnDict
	
def writeJsonPath(path = None, data = {}):
	"""Write the input data into the input json file path.
	"""

	with open(path , 'w') as outfile:  
		json.dump(data, outfile)

def writeJson(directory, fileName, data = {}, **kwargs):
	"""Write the input data into the input json file path.
	"""

	if os.path.isdir(directory):
		#write data
		with open(directory + "/" + fileName + ".json" , 'w') as outfile:  
			json.dump(data, outfile)

def writeJsonFullPath(fullPath, data):
	"""Write the input data into the input json file path.
	"""

	#write data
	with open(fullPath , 'w') as outfile:  
		json.dump(data, outfile)

def distBetween(transformA = None, transformB = None):
	"""Measure the distance between to maya transforms.
	"""

	transformA = checkIfObjExistsAndSet(obj = transformA)
	transformB = checkIfObjExistsAndSet(obj = transformB)

	if transformA and transformB:
		xformA = pm.xform(transformA, q = True, ws = True, t = True)
		xformB = pm.xform(transformB, q = True, ws = True, t = True)

		dx = xformA[0] - xformB[0]
		dy = xformA[1] - xformB[1]
		dz = xformA[2] - xformB[2]

		#return;float (distance)
		return math.sqrt( dx*dx + dy*dy + dz*dz )

def jointOrientToRotation(topNode = None):
	"""Transfer all jointOrient attributes for the jnt hirerchy to rotations.
	Essentially bake the joint orient attributes for the joints.
	"""

	if topNode:
		for o in ([topNode] + topNode.listRelatives(ad = True, type = "joint")):
			if o.hasAttr("jointOrient"):
				orientValues = []
				for axis in "xyz":
					orientValues.append(o.attr("jointOrient" + axis.upper()).get())
					o.attr("jointOrient" + axis.upper()).set(0.0)
				pm.rotate(o, orientValues, r = True)

def jointRotationToOrient(topNode = None):
	"""Transfer all jointOrient attributes for the jnt hirerchy to rotations.
	Essentially bake the joint orient attributes for the joints.
	"""

	if topNode:
		for o in ([topNode] + topNode.listRelatives(ad = True, type = "joint")):
			if o.hasAttr("jointOrient"):
				rotationValues = []
				for axis in "xyz":
					rotationValues.append(o.attr("r" + axis).get())
					o.attr("r" + axis).set(0.0)
				
				for k,axis in enumerate("xyz"):
					newValue = o.attr("jointOrient" + axis.upper()).get() + rotationValues[k]
					o.attr("jointOrient" + axis.upper()).set(newValue)

def zeroJointOrient(topNode = None):
	"""Zero all jointOrient attributes for the jnt hirerchy to rotations.
	"""

	if topNode:
		for o in ([topNode] + topNode.listRelatives(ad = True, type = "joint")):
			if o.hasAttr("jointOrient"):
				for axis in "xyz": o.attr("jointOrient" + axis.upper()).set(0.0)

def createOffsetGroup(transformObject, **kwargs):
	"""For the given transform, create a predefined offset group transform parent.
	"""

	grpType = kwargs.get("type", "offsetGrp") #arg; optionBox = offsetGrp, spaceSwitchGrp
	bodySuffix = kwargs.get("bodySuffix", "") #arg;

	transformObject = validateNameStd(transformObject)
	if transformObject:
		parentA = transformObject.node.getParent()
		offsetGrp = createNodeReturnNameStd(side = transformObject.side, body = transformObject.body + bodySuffix, alpha = transformObject.alpha, id =transformObject.id, buildType = grpType, createBlkClassID = True)
		pm.parent(offsetGrp.node, parentA)
		offsetGrp.node.setTransformation(transformObject.node.getMatrix())
		pm.parent(transformObject.node, offsetGrp.node)

		#return;MnsNameStd (offsetGrp)
		return offsetGrp

def createFreeOffsetGroup(transformObject):
	"""For the given transform, create a free offset group transform parent.
	"""

	transformObject = checkIfObjExistsAndSet(obj = transformObject)
	if transformObject:
		parentA = transformObject.getParent()
		offsetGrp = pm.createNode("transform", name = transformObject.nodeName() + "_Offset_grp")
		pm.parent(offsetGrp, parentA)
		offsetGrp.setTransformation(transformObject.getMatrix())
		pm.parent(transformObject, offsetGrp)

		#return;MnsNameStd (offsetGrp)
		return offsetGrp

def validateAttrAndGet(transform = None, attrName = "", default = None, **kwargs):
	"""For the given transform (or nameStd)- check whether the given attr exists.
	If the attr exist, get it and return it."""

	returnAttrObject = kwargs.get("returnAttrObject", False)

	returnStatus = False
	attrValue = default

	if transform and attrName:
		if type(transform) is MnsNameStd: transform = transform.node
		transform = checkIfObjExistsAndSet(obj = transform)
		if transform:
			if transform.hasAttr(attrName):
				if returnAttrObject: 
					attrValue = transform.attr(attrName)
				else:
					attrValue = transform.attr(attrName).get()
				returnStatus = True

	#return; bool (return status), unknownType (value)
	return returnStatus, attrValue
			 
def checkLocalAxisPairing(origin = None, target = None):
	"""This method will check and return local axis pairing.
	Main use is for pre-connection check for pocNode and curveVarNode tweakers (inputs),
	in order to link local axes correctly, avoiding the need to check aim and up axes, as well as the offset axes.
	"""

	origin = checkIfObjExistsAndSet(obj = origin)
	target = checkIfObjExistsAndSet(obj = target)
	
	chanPairingDict = {"x": None, "y": None, "z": None}
	if origin and target:
		checkLocOrigin = pm.createNode("locator", name = "paringLockOrigin").getParent()
		pm.delete(pm.parentConstraint(origin, checkLocOrigin))
		originOffsetGrp = createFreeOffsetGroup(checkLocOrigin)
		
		checkLocTarget = pm.createNode("locator", name = "paringLockTarget").getParent()
		pm.delete(pm.parentConstraint(target, checkLocTarget))
		targetOffsetGrp = createFreeOffsetGroup(checkLocTarget)
		
		for chan in "xyz":
			checkLocOrigin.attr("t" + chan).set(1.0)
			for chanPair in "xyz":
				checkLocTarget.attr("t" + chanPair).set(1.0)
				distBet = round(distBetween(checkLocOrigin,checkLocTarget),10)
				if distBet == 0.0:
					chanPairingDict.update({chan: chanPair})
					checkLocTarget.attr("t" + chanPair).set(0.0)
					break
				if distBet == 2.0:
					chanPairingDict.update({chan: chanPair + "Neg"})
					checkLocTarget.attr("t" + chanPair).set(0.0)
					break
					
				checkLocTarget.attr("t" + chanPair).set(0.0)
			checkLocOrigin.attr("t" + chan).set(0.0)
			
		pm.delete(originOffsetGrp, targetOffsetGrp)

		#return; dict (pairingDict - {"x", "y","z"})
		return chanPairingDict

def applyChennelControlAttributesToTransform(transform = None, ccDict = {}):
	"""This method applies a 'channelControl' dict attributes into the given transform.
	"""

	transform = checkIfObjExistsAndSet(transform)
	if transform:
		if ccDict:
			for chan in ccDict.keys():
				k = 0
				for axis in "xyz":
					attrName = chan + axis
					if transform.hasAttr(attrName):
						attribute = transform.attr(attrName)
						if attribute:
							if ccDict[chan][k]:
								attribute.setKeyable(True)
								attribute.setLocked(False)
							else:
								attribute.setKeyable(False)
								attribute.setLocked(True)
					k += 1 

def sorted_alphanumeric(data):
	"""returns an alphanumeric ordered data from input given
	"""

	convert = lambda text: int(text) if text.isdigit() else text.lower()
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 

	#return; list (sorted data)
	return sorted(data, key=alphanum_key)

def locatePreferencesDirectory():
	"""This method is used across to locate the prefs directory for the current user.
	"""

	prefsPath = None
	scriptPaths = os.environ['MAYA_APP_DIR'] + "/scripts"

	if os.path.isdir(scriptPaths):
		prefsPath = scriptPaths + "/" + GLOB_mnsPrefsFolderName

		if not GLOB_mnsPrefsFolderName in os.listdir(scriptPaths): 
			try: 
				os.makedirs(prefsPath)
			except: pass
		if not os.path.isdir(prefsPath): prefsPath = None 

	#return; string (preferences directory path)
	return prefsPath

def createMnsDefaultPrefs(**kwargs):
	"""This method is called whenever a pref read is being called.
	In case this method fails to locate local prefs for the current user, it creates it from the defualt prefs file.
	Also, this method contains the "restore" flag, which will create a new prefs local file from the default file regardless of any other choice.
	This is used as a "restore factory defaults" option.
	"""

	restore = kwargs.get("restoreDefaults", False)

	defPrefDir = dirname(dirname(__file__)) + "/preferences/preferencesDefaults.json"
	if os.path.isfile(defPrefDir):
		prefsDir = locatePreferencesDirectory()
		if prefsDir and os.path.isdir(prefsDir):
			if restore:
				if GLOB_mnsPrefsFileName in os.listdir(prefsDir): 
					try:
						deleteFile(prefsDir + "/" + GLOB_mnsPrefsFileName)
					except:
						pass
			if GLOB_mnsPrefsFileName not in os.listdir(prefsDir):
				try:
					shutil.copyfile(defPrefDir, prefsDir + "/" + GLOB_mnsPrefsFileName)
				except:
					pass

			prefsFile = prefsDir + "/" + GLOB_mnsPrefsFileName
			if os.path.isfile(prefsFile):
				defPrefDir = prefsFile 

	return defPrefDir
	#return; string (prefs file path)

def getMansurPrefsDefaults(**kwargs):
	defPrefDir = dirname(dirname(__file__)) + "/preferences/preferencesDefaults.json"
	if os.path.isfile(defPrefDir):
		return readJson(defPrefDir)

def updateMansurPrefs(prefs = None, **kwargs):
	if not prefs:
		prefs = getMansurPrefsFromFile()

	if prefs:
		defaultPrefs = getMansurPrefsDefaults()
		for prefCat in defaultPrefs.keys():
			if prefCat not in prefs.keys():
				prefs[prefCat] = defaultPrefs[prefCat]
			else:
				for pref in defaultPrefs[prefCat]:
					if pref not in prefs[prefCat].keys():
						prefs[prefCat][pref] = defaultPrefs[prefCat][pref]
		
		from . import globals as mnsGlobals
		mnsGlobals.GLOB_mnsPrefs = prefs
		
		settingsFile = getMansurPrefsFromFile(returnFileDirectory = True)
		with open(settingsFile , 'w') as outfile:  
			json.dump(prefs, outfile)

		return prefs

def getMansurPrefs():
	"""This method retrives the prefs static dict from globals
	"""
	from . import globals as mnsGlobals

	return mnsGlobals.GLOB_mnsPrefs
	#return; dict (prefrences)

def getMansurPrefsFromFile(**kwargs):
	"""This method retrives all of the current prefrences.
	In case the 'returnFileDirectory' flag is set to true, this will return the path of the prefs file, instead of the preferences as a dict.
	"""

	returnFileDirectory = kwargs.get("returnFileDirectory", False)

	prefsFile = None
	prefsDir = locatePreferencesDirectory()
	if prefsDir and GLOB_mnsPrefsFileName in os.listdir(prefsDir):
		prefsFile = prefsDir + "/" + GLOB_mnsPrefsFileName
		
	else:
		prefsFile = createMnsDefaultPrefs()

	if prefsFile:
		if returnFileDirectory: 
			return prefsFile
		else:
			returnPrefs = readJson(prefsFile) 
			return returnPrefs

	#return; dict (prefrences)

def findAndReplaceInFile(file_path, pattern, subst):
	"""This is a simple method to replace the pattern given with a substitute string within a file,
	Then overriting the original file with new lines.
	"""

	fh, abs_path = mkstemp()
	with fdopen(fh,'w') as new_file:
		with open(file_path) as old_file:
			for line in old_file:
				new_file.write(line.replace(pattern, subst))
	copymode(file_path, abs_path)
	remove(file_path)
	move(abs_path, file_path)

def checkForInternetConnection(host="8.8.8.8", port=53, timeout=3):
	"""check for a valid internet connection.
	"""

	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except: pass

	#return;bool

def checkForVersionUpdates():
	"""This method will compare the current mns version against the latest available.
	Return False if the current version is the latest version
	Return True if the current version isn't the latest version
	"""

	isNewVesrionAvailable = False
	try:
		versionsReturn = json.loads(cmds.mnsDist(p = platform.system().lower(), lv = True))
		currentVersion = getCurrentVersion()

		if versionsReturn and currentVersion:
			formatedLatestVersion = versionsReturn[0]["key"].split(".zip")[0].split("_")[-1]
			if currentVersion != formatedLatestVersion:
				isNewVesrionAvailable = True
	except:
		pass

	#return; bool (isNewVesrionAvailable)
	return isNewVesrionAvailable

def getCurrentVersion():
	"""Get the current mansur product version based on this file directory
	"""

	mansurPath = __import__(__name__.split('.')[0]).__path__[0].replace("\\", "/")
	versiondir = dirname(dirname(mansurPath))
	versionFullName = versiondir.split("/")[-1]

	if "." in versionFullName and "_" in versionFullName:
		return versionFullName.split("_")[-1]
	else:
		return "dev"

	#return;string (version)

def mnsLicStatusCheck(mode = 0):
	"""
	modes:
	0 = Available for all
	1 = Available for edit only
	"""
	res = 0
	from ..licensing import licensingUI as mnsLicensingUI

	returnState = False
	try:
		if isPluginLoaded("mnsLicDigest"):
			res = cmds.mnsLicStatus()
			if mode == 0 and res > 0:
				returnState = True
			elif mode == 1 and res == 1:
				returnState = True
	except: pass

	if not returnState:
		mnsLicensingUIWin = mnsLicensingUI.loadLicensingUI(silent = True)
		mnsLicensingUIWin.logIn()
		try:
			if isPluginLoaded("mnsLicDigest"):
				res = cmds.mnsLicStatus()
				if mode == 0 and res > 0:
					returnState = True
				elif mode == 1 and res == 1:
					returnState = True
		except: pass

	if not returnState:
		mnsLicensingUIWin = mnsLicensingUI.loadLicensingUI(silent = True)
		if mnsLicensingUIWin: mnsLicensingUIWin.showMinimized()
		
		if res == 0:
			pm.confirmDialog( title='MANSUR - Log-In', message='Mansur- You must be Logged-In to proceed', icon = "warning", defaultButton='OK')
		elif res == 2 and not returnState:
			pm.confirmDialog( title='MANSUR - Feature not available', message='Mansur- This feature is not included within your subscription plan.', icon = "warning", defaultButton='OK')

	return returnState

def isPluginLoaded(pluginName = None):
	if pluginName:
		loadedStat = pm.pluginInfo(pluginName, query=True, l=True)
		if not loadedStat:
			try:
				pm.loadPlugin(pluginName)
				loadedStat = pm.pluginInfo(pluginName + '.mll', query=True, l=True)
			except:
				pass

		return loadedStat

def autoLoadMnsPlugins():
	for pluginName in GLOB_autoLoadPluginList:
		try:
			pm.loadPlugin(pluginName)
			pm.pluginInfo(pluginName + '.mll', edit=True, autoload=True)
		except: pass

def removeNamespaceFromString(value):
	tokens = value.split('|')
	result = ''
	for i, token in enumerate(tokens):
		if i > 0:
			result += '|'
		result += token.split(':')[-1]
	return result

def extractHeaderFromPath(fullPath):
	headerLines = []

	if fullPath and os.path.isfile(fullPath):
		sourceLines = tuple(open(fullPath, 'r'))
		header = False
		inFirstHeader = False
		count = 0

		isDoubleHeader = False
		for lineIndex in range(5):
			line = sourceLines[lineIndex]
			if "Copyright" in line:
				isDoubleHeader = True
				break

		for line in sourceLines:
			line = line.replace("\n", "").replace("\r", "").replace("\t", "")

			if inFirstHeader:
				if "\"\"\"" in line: 
					isDoubleHeader = False
					inFirstHeader = False
					count = -2

			if header:
				if "\"\"\"" in line: 
					if line.replace("\"\"\"", "") != "":
						headerLines.append(line.replace("\"\"\"", "")) 
					break
				else: headerLines.append(line) 

			if count == 0:
				if "\"\"\"" in line and not isDoubleHeader: 
					header = True
					if line.replace("\"\"\"", "") != "":
						headerLines.append(line.replace("\"\"\"", "")) 
				elif isDoubleHeader:
					inFirstHeader = True
				else: break
			count += 1

	return headerLines

def deleteUnusedShapeNodes(obj = None):
	obj = checkIfObjExistsAndSet(obj)
	if obj:
		shapes = obj.getShapes()
		if len(shapes) > 1:
			for shape in shapes:
				if not shape.listConnections():
					pm.delete(shape)

def getMObjectFromObjName(name):
	if checkIfObjExistsAndSet(name):
		sel = OpenMaya.MSelectionList()
		sel.add(name)
		mObj = OpenMaya.MObject()
		sel.getDependNode(0,mObj)
		return mObj

def getMObjectFromNode(node):
	if checkIfObjExistsAndSet(node):
		sel = OpenMaya.MSelectionList()
		sel.add(node)
		mObj = OpenMaya.MObject()
		sel.getDependNode(0,mObj)
		return mObj

def mirrorPose(targetTransform, mirrorTransform):
	targetTransform = checkIfObjExistsAndSet(targetTransform)
	mirrorTransform = checkIfObjExistsAndSet(mirrorTransform)
	if targetTransform and mirrorTransform:
		targetMatrix =  targetTransform.getMatrix(worldSpace=True)
		
		pm.makeIdentity(targetTransform)
		pm.makeIdentity(mirrorTransform)
		zeroTargetMatrix = targetTransform.getMatrix(worldSpace=True)
		zeroMirrorMatrix = mirrorTransform.getMatrix(worldSpace=True)
		reflectionMatrix_YZ = pm.datatypes.Matrix(-1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0)
		reflectionReferenceMat = (zeroTargetMatrix * reflectionMatrix_YZ)
		mirrorTransform.setMatrix(reflectionReferenceMat , worldSpace=True)
		reflectionReferenceRotation = mirrorTransform.r.get()

		targetMirror = (targetMatrix * reflectionMatrix_YZ)
		mirrorTransform.setMatrix(targetMirror , worldSpace=True)

		for i, chan in enumerate("xyz"):
			mirrorTransform.attr("r" + chan).set(mirrorTransform.attr("r" + chan).get() + (reflectionReferenceRotation[i] * -1))
			
def mirrorPose2(targetTransform, mirrorTransform, **kwargs):
	targetTransform = checkIfObjExistsAndSet(targetTransform)
	mirrorTransform = checkIfObjExistsAndSet(mirrorTransform)

	if targetTransform and mirrorTransform:
		doScale = kwargs.get("doScale", False)
		keepTarget = kwargs.get("keepTarget", True)

		targetMatrix =  targetTransform.getMatrix(worldSpace=True)
		originRotationValues = targetTransform.r.get()

		pm.makeIdentity(targetTransform, s = doScale)
		pm.makeIdentity(mirrorTransform, s = doScale)
		zeroTargetMatrix = targetTransform.getMatrix(worldSpace=True)
		zeroMirrorMatrix = mirrorTransform.getMatrix(worldSpace=True)
		reflectionMatrix_YZ = pm.datatypes.Matrix(-1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0)
		reflectionReferenceMat = (zeroTargetMatrix * reflectionMatrix_YZ)
		mirrorTransform.setMatrix(reflectionReferenceMat , worldSpace=True)
		reflectionReferenceRotation = mirrorTransform.r.get()
  
		targetMirror = (targetMatrix * reflectionMatrix_YZ)
		mirrorTransform.setMatrix(targetMirror , worldSpace=True)
		
		if keepTarget:
			targetTransform.setMatrix(targetMatrix, worldSpace = True)

def resetMeshHistory(mesh, mode = 0):
	#mode 0 - reset
	#mode 1 - reactivate
	
	vMesh = checkIfObjExistsAndSet(mesh)
	if vMesh:
		allH = pm.listHistory(vMesh, pdo = True, il = 1)
		for hNode in allH:
			if hNode.hasAttr("envelope"):
				hNode.envelope.set(mode)
