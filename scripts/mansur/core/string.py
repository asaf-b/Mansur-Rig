"""=== Author: Assaf Ben Zur ===
This module covers all custom string operations used in MNS
"""

#global dependencies
from re import finditer
import os

# inputs an array and returns it as a flattened string
def flattenArraySpace(array = []):
	"""Flatten a given list into a single string, seperated by spaces
	"""

	flattenedArray = ""
	for o in array:
		if type(o).__name__ != 'str':
				o = o.__str__()
		if flattenedArray == "":
			flattenedArray = flattenedArray + o
		else:
			flattenedArray = flattenedArray + " " + o

	#return;string 
	return flattenedArray

def flattenArrayColon(array = []):
	"""Flatten a given list into a single string, seperated by colons
	"""

	flattenedArray = ""
	for o in array:
		if type(o).__name__ != 'str':
				o = o.__str__()
		if flattenedArray == "":
			flattenedArray += o
		else:
			flattenedArray += ":" + o

	#return;string 
	return flattenedArray

def flattenArray(array = []):
	"""Flatten a given list into a single string, seperated by commas
	"""

	flattenedArray = ""
	for o in array:
		if type(o).__name__ != 'str':
				o = o.__str__()
		if flattenedArray == "":
			flattenedArray = flattenedArray + o
		else:
			flattenedArray = flattenedArray + ", " + o

	#return;string 
	return flattenedArray

def flattenArrayKeepBracets(array = []):
	"""Flatten a given list into a single string, seperated by commas, adding the open and close square brackets as string.
	"""

	flattenedArray = ""
	i = 1
	for o in array:
		if type(o).__name__ != 'str':
				o = o.__str__()
		if flattenedArray == "":
			flattenedArray = "[" + flattenedArray + o
		elif i == len(array):
			flattenedArray = flattenedArray + ", " + o + "]"
		else:
			flattenedArray = flattenedArray + ", " + o
		i = i + 1 

	#return;string 
	return flattenedArray

def flattenArrayKeepBracetsAndStrings(array = []):
	"""Flatten a given list into a single string, seperated by commas, adding the open and close square brackets as string as well as add the " into the actual string elements.
	"""

	flattenedArray = ""
	i = 1
	for o in array:
		if type(o).__name__ != 'str':
				o = '\'' + o.__str__().strip() + '\''
		if flattenedArray == "":
			flattenedArray = "[" + flattenedArray + o
		elif i == len(array):
			flattenedArray = flattenedArray + ", " + o + "]"
		else:
			flattenedArray = flattenedArray + ", " + o
		i = i + 1

	#return;string 
	return flattenedArray

def stringConvertToString(var):
	"""convert the input provided to a string, regardless of its type.
	"""

	returnString = ""
	if type(var) is list:
		returnString = flattenArray(var)
	if type(var).__name__ != 'str':
		returnString = var.__str__()
	return var

def stringMultiReplaceBySingle(element = "", replaceStrings = [], replaceBy = ""):
	"""Replace all given string characters by the 'replaceBy' string given.
	"""

	for s in replaceStrings:
		element = element.replace(s, replaceBy)

	#return;string 
	return element

def camelCaseSplit(ccString):
	"""Split input string into array based on the 'camel-casing' rule.
	"""

	matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', ccString)

	#return;list (splitted string)
	return [m.group(0) for m in matches]
	
def combineStringList(stringList = [], separatorS = " "):
	"""Combine the given string array, into a single string, using the 'separatorS' string input as a seperator.
	"""

	returnString = ""
	if stringList:
		for s in stringList: 
			if returnString: returnString += separatorS
			returnString += s

	#return;string (combined string)
	return returnString

def splitStringToArray(stringSplit = ""):
	"""Split the given string into a formatted array, using a "," split.
	"""	

	returnState = stringSplit

	if stringSplit:
		stringSplit = stringSplit.replace(" ", "")

		returnState = [stringSplit]
		if "," in stringSplit: returnState = stringSplit.split(",")	
	
	#return;list (splitted string)
	return returnState

def extractHeaderFromPythonFile(filePath = None):
	"""For the given python file, extract the header comment.
	"""

	headerLines = []
	if filePath and os.path.isfile(filePath):
		fileLines = list(open(filePath, 'r'))	

		if "\"\"\"" in fileLines[0]: #header exists
			for lineIndex in range(0, len(fileLines)):
				line = fileLines[lineIndex]
				formatedLine = line.replace("\"\"\"", "")
				if formatedLine: headerLines.append(formatedLine)

				if lineIndex > 0 and "\"\"\"" in line: break

	#return;list (file header)
	return headerLines