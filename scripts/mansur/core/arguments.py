"""=== Author: Assaf Ben Zur ===
MNS main arguments core functions and Classes.
This module holds the MnsArgument class as well as all argument handeling functions.
This module was designed to procedurally handle function arguments in order to manipulate them, generate dynamic UI's from them, and pass them along back to their creator function as an execute."""

#global dependencies
import inspect as ins
import sys

#mns dependencies
from . import string as mnsString
from .prefixSuffix import *
from .globals import *

class MnsArgument(object):
	"""MnsArgument Convieniency Class.
		A class instance holds all relevant information regarding an extracted single function argument.
		These class members will dectate any behavior derived from an actual function object or a method object."""

	def __init__(self,**kwargs):
		self.name = kwargs.get("name",None) #arg;
		self.type = kwargs.get("type",None) #arg;
		self.default = kwargs.get("default",None) #arg;
		self.min = kwargs.get("min",-100000000.0) #arg;
		self.max = kwargs.get("max",100000000.0) #arg;
		self.comment = kwargs.get("comment","Comment wasn't inserted")  #arg;   
		self.ob = kwargs.get("ob",[]) #arg;
		self.side = mnsSidesDict[kwargs.get("side", "center")] #arg;
		self.pathMode = kwargs.get("pathMode", 0) #arg;
		self.pathFileTypes = kwargs.get("pathFileTypes", []) #arg;
		self.intIncrement = kwargs.get("intIncrement", 0) #arg;
		self.boolExclusive = kwargs.get("boolExclusive", []) #arg;

		self.blockCreationOnly = kwargs.get("blockCreationOnly", False) #arg;
		self.jntStructMember = kwargs.get("jntStructMember", False) #arg;
		self.jntStructSoftMod = kwargs.get("jntStructSoftMod", False) #arg;
		self.lockOffAttributes = kwargs.get("lockOffAttributes", False) #arg;
		self.simpleDivider = kwargs.get("simpleDivider", False) #arg;
		self.meshComponents = kwargs.get("meshComponents", False) #arg;
		self.disabled = kwargs.get("disabled", False) #arg;
		self.multiRowList = kwargs.get("multiRowList", False) #arg;
		self.alphabeticalOnly = kwargs.get("alphabeticalOnly", False) #arg;

	def formatCommentToToolTip(self):
		return "<html><table width = 250><tr><td><font face = SansSerif size = 4>" + self.comment + "</b></font></td></tr></table></html>"

def returnValueAndTypeFromArgString(argString = ""):
	"""This function will return a value (as its actual type) and a type (as a type object) from a given extracted argument string
	"""

	stripped = argString.strip()   
	value = 0
	typeA = None
	if stripped == "True" or stripped =="true": 
		value = True
		typeA = bool
	elif stripped == "False" or stripped =="false": 
		value = False
		typeA = bool
	elif stripped == "\"\"":
		value = ""
		typeA = str
	else:
		found = False
		try: 
			value = int(argString) 
			typeA = int
			found = True
		except ValueError: pass
		if found == False:
			try:
				value = float(argString) 
				typeA = float
				found = True
			except ValueError: pass
		if found == False and "[" in argString:
			argString = mnsString.stringMultiReplaceBySingle(argString, ["\"", "\'"], "")
			value = argString.strip("[]").split(",")
			typeA = list
			found = True
		elif found == False and "," in argString:
			value = argString.strip("()").split(",")
			tupleA = ()
			for element in value:
				element = mnsString.stringMultiReplaceBySingle(element, ["\"", "\'", "(", ")", " "], "")
				found = False
				try: 
					element = int(element) 
					found = True
				except: pass
				if not found:
					try: 
						element = float(element) 
					except: pass
				tupleA = tupleA + (element,)
			value = tupleA
			typeA = tuple
			found = True
		if not found:
			value = mnsString.stringMultiReplaceBySingle(argString, ["\"", "\'", " "], "")
			typeA = str 

	#return;value (Dynamic type), type (type object)     
	return value,typeA
			
def splitStringToArg(argAsString):
	"""This function return a MnsArgument object from a given argument string.
		It will split the argument string into actual elemnts and values and directly ingest them into the class members.
	"""

	argumentReturn = MnsArgument()
	argsListString = argAsString.split(";")
	for sp in argsListString:
		if("=" in sp):
			arg,val = sp.split("=")
			arg = arg.strip()
			if arg == "name": argumentReturn.name = val.strip()
			elif arg == "type": 
				typeStr = val.strip()
				typeCases = {
							'int': int,
							'float': float,
							'string': str,
							'bool': bool,
							'list': list,
							'dict': dict,
							'tuple': tuple
							}
				argumentReturn.type = typeCases.get(typeStr, None)
			elif arg == "default":
				if ',' in val:
					valList = arg.split(",")
					for v in valList: v = v.strip()
					argumentReturn.default = valList
				else:
					argumentReturn.default = val.strip()

			elif arg == "min": argumentReturn.min = val.strip()
			elif arg == "max": argumentReturn.max = val.strip()
			elif arg == "comment": argumentReturn.comment = val.strip() 
			elif arg == "pathMode": 
				val = val.strip() 
				if val.isdigit(): argumentReturn.pathMode = int(val)
			elif arg == "pathFileTypes": 
				options = mnsString.stringMultiReplaceBySingle(val, ["\"", "\'", " "], "").split(",")
				if type(options) is list and len(options) > 0:
					argumentReturn.pathFileTypes = options 
			elif arg == "optionBox": 
				options = mnsString.stringMultiReplaceBySingle(val, ["\"", "\'", " "], "").split(",")
				if type(options) is list and len(options) > 0:
					argumentReturn.ob = options 
			elif arg == "blockCreationOnly": argumentReturn.blockCreationOnly = True
			elif arg == "jntStructMember": argumentReturn.jntStructMember = True
			elif arg == "jntStructSoftMod": argumentReturn.jntStructSoftMod = True
			elif arg == "lockOffAttributes": argumentReturn.lockOffAttributes = True
			elif arg == "simpleDivider": argumentReturn.simpleDivider = True
			elif arg == "meshComponents": argumentReturn.meshComponents = True
			elif arg == "disabled": argumentReturn.disabled = True
			elif arg == "multiRowList": argumentReturn.multiRowList = True
			elif arg == "alphabeticalOnly": argumentReturn.alphabeticalOnly = True
			elif arg == "intIncrement": 
				try:
					argumentReturn.intIncrement = int(val.strip())
				except:
					pass
			elif arg == "boolExclusive":
				options = mnsString.stringMultiReplaceBySingle(val, ["\"", "\'", " "], "").split(",")
				if type(options) is list and len(options) > 0:
					argumentReturn.boolExclusive = options
	
	#return;MnsArgument
	return argumentReturn
	
def extractArgsFromDef(defenition):
	"""This function will extract all arguments and optional arguments from a given function object.
	Returns two lists containing MnsArgument instances."""

	argsReturnList = []
	argsOptReturnList = []
	
	argsSpec = []
	if GLOB_pyVer > 2:
		argsSpec = ins.getfullargspec(defenition)
	else:
		argsSpec = ins.getargspec(defenition)

	defaults = argsSpec.defaults
	add = 0
	if argsSpec.args is not None:
		if argsSpec.defaults is None: 
			defaults = ()
			add = len(argsSpec.args)
		elif len(argsSpec.defaults) != len(argsSpec.args): 
			add = len(argsSpec.args) - len(argsSpec.defaults)
		for i in range (0, add): 
			defaults = (None,) + defaults

	k = 0
	if argsSpec.args is not None:
		for arg in argsSpec.args:
			appendArgument = MnsArgument(name = arg, type = type(defaults[k]), default = defaults[k])
			argsReturnList.append(appendArgument)
			k+=1

	
	fileA =  sys.modules[defenition.__module__].__file__
	if ".pyc" in fileA:
		fileA = fileA.replace(".pyc",".py")
	src = tuple(open(fileA, 'r'))

	compiledSrc = []
	add = False
	for l in src:
		stripped = l.strip()
		if stripped.startswith("def " + defenition.__name__ + "("): add = True
		elif add and stripped.startswith("def "): break
		elif add: compiledSrc.append(l)
	src = compiledSrc
	#src = ins.getsourcelines(defenition)[0] 
	
	emptyTemp, optArgumentList = extractArgsFromSource(src)

	#return;list (arguments MnsArgument list), list (optional arguments MnsArgument list)
	return argsReturnList, optArgumentList

def extractColorSchemeDefaultFromLine(line = "", argAame = ""):
	default = line.replace(" ", "").split("\"" + argAame + "\"" + ",")[1]
	default = default.split(")#")[0].replace("[", "").replace("]", "")
	defaultList = default.split("),(")
	returnList = []
	for valString in defaultList:
		val = []
		valString = valString.replace(")", ""). replace("(", "")
		valList = valString.split(",")
		for valS in valList: val.append(float(valS))
		returnList.append(tuple(val))
	return returnList

def extractChennelControlDefaultFromLine(line = "", argAame = ""):
	default = line.replace(" ", "").split("\"" + argAame + "\"" + ",")[1]
	default = default.split(")#")[0].replace("{", "").replace("}", "").replace("\"","").split("),")

	retDict = {}
	for k in default:
		tupList = []
		chennel, values = k.split(":(")
		values = values.split(",")
		for v in values:
			if v.replace(")","").lower() == "true": tupList.append(True)
			else: tupList.append(False)
		retDict.update({chennel: tuple(tupList)})
	 
	#return; dict
	return retDict

def convertChannelControlDictToAttr(channelControlDict = {}):
	returnList = [' ']

	for channel in "trs":
		for index, axis in enumerate("xyz"):
			if channelControlDict[channel][index]:
				returnList.append(channel + axis)

	#return; list
	return returnList

def extractArgsFromSource(src):
	"""This function will extract all arguments and optional arguments from a given function source.
	Returns two lists containing MnsArgument instances."""

	optArgumentList = []
	argumentList =[]

	if len(src) > 0:
		if src[0].split(" ")[0].replace("\t", "") == "def":
			argumentLine = src[0].replace("def " + src[0].split("def ")[1].split("(")[0] + "(", "").split("):")[0]
			arguments = argumentLine.split(",")
			for arg in arguments:
				arg = arg.replace("\t", "")
				arg = arg.replace(" ", "")

				argumentReturn = MnsArgument()
				if "=" in arg:
					if "pm.ls(sl=1)" in arg: arg = arg.replace("pm.ls(sl=1)", "selection")
					name, value = arg.split("=")
					typeStr = "string"
					isString = True
					if value == 'True' or value == 'False': 
							typeStr = "bool"
							isString = False
					if isString:
						try:
							int(value)
							typeStr = "int"
							isString = False
						except: pass
					if isString:	
						try:
							float(value)
							typeStr = "float"
							isString = False
						except: pass
					if isString:	
						if "[" in value: typeStr = "list"
						elif "{" in value: typeStr = "dict"

					typeCases = {
						'int': int,
						'float': float,
						'string': str,
						'bool': bool,
						'list': list,
						'dict': dict,
						'tuple': tuple
						}
					argumentReturn.type = typeCases.get(typeStr, None)
					argumentReturn.name = arg.split("=")[0]
					argumentReturn.default = value
				else:
					argumentReturn.name = arg
				argumentList.append(argumentReturn)
		for l in src:
			l = l.replace("\n", "").replace("\r", "")
			if "#arg;" in l and "selfAvoidFromTheCurrentDefRead" not in l:
				name = l.strip().split('kwargs.get(')[1].split(",")[0].strip("'").strip("\"")
				argsAsString = l.split('#arg;')[1] #selfAvoidFromTheCurrentDefRead

				argReturn = splitStringToArg(argsAsString)
				default = l.strip().split("\"" + name + "\"" + ",")[1].split(")")[0]

				argReturn.default, argReturn.type = returnValueAndTypeFromArgString(default)

				if "channelControl".lower() in l.lower():
					argReturn.default = extractChennelControlDefaultFromLine(l, name)
					argReturn.type = dict

				if "colorScheme".lower() in l.lower() or "schemeOverride".lower() in l.lower():
					argReturn.default = extractColorSchemeDefaultFromLine(l, name)
					argReturn.type = list

				argReturn.name = name
				if "side".lower() in argReturn.name.lower():
					argReturn.ob = ["right", "left", "center"]
				#if argReturn.name == "alpha":
				#	argReturn.ob = buildOptionArrayFromDict(mnsAlphaDict)
				if "controlshape" in argReturn.name.lower():
					argReturn.ob = sorted(buildOptionArrayFromDict(mnsControlShapesDict))
				if argReturn.name == "buildType":
					argReturn.ob = buildOptionArrayFromDict(mnsBuildObjectTypes)
				optArgumentList.append(argReturn)

	#return;list (arguments MnsArgument list), list (optional arguments MnsArgument list)
	return argumentList, optArgumentList

def recompileArgumetsAsString(defenition, arguments, optArgs, values):
	"""A reverse function to the 'extractArgsFromDef'.
	In order to pass any arguments back to it's creator, comes a need to re-compile an argument list into a single callable formatted string.
	This function covers this need."""

	compiledArgsString = ""
	k = 0
	if (len(arguments) + len(optArgs) == 0):
			return compiledArgsString
	else:
		if arguments:
			for i in range(0, len(arguments)):
				if arguments[i].type == int or arguments[i].type == bool or arguments[i].type == float:
					val = values[i].__str__().replace(' ','')
					if compiledArgsString == "":
						compiledArgsString += val
					else:
						compiledArgsString += ',' + val  
				elif arguments[i].type == str:
					val = values[i].__str__().replace(' ','')
					if compiledArgsString == "":
						compiledArgsString += '\'' + val + '\''
					else:
						compiledArgsString += ',\'' + val + '\''
				elif arguments[i].type == list:
					if ',' in values[i]:
						values[i] = values[i].replace(' ','')
						list1 = values[i].split(',')
						string ='['
						for l in range(0,len(list1)):
							if 'str' in arguments[i].type.lower():
								string = string + '\'' + list1[l] + '\'' 
							else:
								string = string + list1[l]
							if l != (len(list1) - 1):
								string = string + ","
						string = string +']'
						if compiledArgsString == "":
							compiledArgsString += string 
						else:
							compiledArgsString += ',' + string 
					else:
						val = values[i].__str__().replace(' ','')
						if compiledArgsString == "":
							compiledArgsString +=  '[\'' + val + '\']'
						else:
							compiledArgsString +=  ',[\'' + val + '\']'
				elif arguments[i].type == tuple:
					val = ""
					stringComponenets = "("
					for component in values[i]:
						if type(component) == str: 
							component = component.__str__().replace(' ','')
							component = "\'" + component + "\'"
						if stringComponenets == "(": stringComponenets += str(component)
						else: stringComponenets += "," + str(component)
					stringComponenets += ")"
					if compiledArgsString == "":
						compiledArgsString +=  val + stringComponenets
					else:
						compiledArgsString +=  ',' + val + stringComponenets

				else: #unknown
					if ',' in values[i]:
						values[i] = values[i].replace(' ','')
						list1 = values[i].split(',')
						string ='['
						for k in range(0,len(list1)):
							isString = 1
							#check if boolean
							if list1[k] == 'True' or list1[k] == 'False':
								isString =0
							#check if int
							try:
								int(list1[k])
								isString = 0
							except:
								pass
							#check if float
							try:
								float(list1[k])
								isString = 0
							except:
								pass
							if isString == 0:
								val = values[i].__str__().replace(' ','')
							else:
								val = '\'' + values[i].__str__().replace(' ','') + '\''
							string = string + val
							if i != (len(list1) - 1):
								string = string + ","
						string = string +']' 
						if compiledArgsString == "":
							compiledArgsString +=  string
						else:
							compiledArgsString +=  ','  + string        
					else:
						isString = 1
						#check if boolean
						if values[i] == 'True' or values[i] == 'False':
							isString =0
						#check if int
						try:
							int(values[i])
							isString = 0
						except:
							pass
						#check if float
						try:
							float(values[i])
							isString = 0
						except:
							pass
						val = ''
						if isString == 0:
							val = values[i].__str__().replace(' ','')
						else:
							val = '\'' + values[i].__str__().replace(' ','') + '\''
						if compiledArgsString == "":
							compiledArgsString += val
						else:
							compiledArgsString += ','  + val
				k += 1
		if optArgs:
			for j in range(0, len(optArgs)):
				val = str(values[k + j]).replace(' ','')
				if optArgs[j].type is str and "," in val: optArgs[j].type = list
				if (optArgs[j].type == int) or (optArgs[j].type == bool) or (optArgs[j].type == float):
					val = optArgs[j].name + '=' + values[k + j].__str__().replace(' ','')
					if compiledArgsString == "":
						compiledArgsString += val
					else:
						compiledArgsString += ',' + val  
				elif optArgs[j].type == str:
					val = optArgs[j].name + '=' + '\'' + values[k + j].__str__().replace(' ','') + '\''
					if compiledArgsString == "":
						compiledArgsString += val
					else:
						compiledArgsString += ',' + val
				elif optArgs[j].type == list:
					list1 = []
					if ',' in values[k + j]:
						values[k + j] = values[k + j].replace(' ','')
						list1 = values[k + j].split(',')
					else:
						list1 = [values[k + j].replace(' ','')]
					string = optArgs[j].name + '=' + '['
					for i in range(0,len(list1)):
						isString = True
						#check if boolean
						if list1[i] == 'True' or list1[i] == 'False':
							isString = False
						try:
							int(list1[i])
							isString = False
						except:
							pass
						try:
							float(list1[i])
							isString = False
						except:
							pass
						val = ''
						if isString and list1[i] != "":
							string += '\'' + list1[i].__str__().replace(' ','') + '\''
						else:
							string += list1[i].__str__().replace(' ','')
						if i != (len(list1) - 1):
							string += ","
					string += ']'
					if compiledArgsString == "":
						compiledArgsString += string 
					else:
						compiledArgsString += ',' + string 
				elif optArgs[j].type == tuple:
					val = optArgs[j].name + '='
					stringComponenets = "("
					for component in values[k + j]:
						if type(component) == str: 
							component = component.__str__().replace(' ','')
							component = "\'" + component + "\'"
						if stringComponenets == "(": stringComponenets += str(component)
						else: stringComponenets += "," + str(component)
					stringComponenets += ")"
					if compiledArgsString == "":
						compiledArgsString +=  val + stringComponenets
					else:
						compiledArgsString +=  ',' + val + stringComponenets

	#return;string (re-compiled arguments as string)
	return compiledArgsString

def formatArgumetsAsDict(mnsArgsList = []):
	"""Format given list of arguments into a predefined dictionary structure.
	"""

	retDict = {}
	for arg in mnsArgsList:
		if "channelControl".lower() in arg.name.lower():
			newDefault = []
			labelList = ["x", "y", "z"]
			for key in arg.default.keys():
				k = 0
				for val in arg.default[key]:
					if val: newDefault.append(key + labelList[k])
					k += 1
			if not newDefault: newDefault = [" "]
			arg.default = newDefault
			
		retDict.update({arg.name: arg.default})

	#return;dict (Formated arguments)
	return retDict