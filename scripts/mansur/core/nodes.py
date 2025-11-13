"""=== Author: Assaf Ben Zur ===
Mns nodes utility module.
All node creation functions are covered by this module"""

#global dependencies


from maya import cmds
import pymel.core as pm
from pymel.core.general import Attribute as pmAttr

import maya.mel as mel

#mns dependencies
from . import utility as mnsUtils
from . import meshUtility as mnsMeshUtils
from . import log as mnsLog
from . prefixSuffix import *
from .globals import *

#python3 exceptions
import sys
if sys.version_info[0] >= 3:
	unicode = str

def connectAttrAttempt(attrA, nodeAttr):
	"""Attempt to connect the sourceAttr given to the target attribute passed in.
	"""

	success = False
	if attrA or attrA != None:
		try:
			if pm.isConnected(attrA, attrA): success = True
		except: pass
		
		if not success:
			if type(attrA) is pmAttr: 
				try: 
					attrA >> nodeAttr
					success = True
				except: pass
			elif type(attrA) is str or type(attrA) is unicode: 
				try: 
					pm.connectAttr(attrA, nodeAttr)
					success = True
				except: pass 

	#return;bool (sucess status)
	return success

def setAttrAttempt(nodeAttr, value, valType):
	"""Attempt to set the passed in value into the attribute passed in.
	"""

	success = False
	try: 
		nodeAttr.set(valType(value))
		success = True
	except: pass

	#return;bool (sucess status)
	return success
	
def connectSetAttempt(attrA, nodeAttr, valType):
	"""Attemp to connect the values passed in.
	If a failue status was return, attempt a 'setAttr' next.
	"""

	status = connectAttrAttempt(attrA, nodeAttr)
	if not status: status = setAttrAttempt(nodeAttr, attrA, valType)

	#return;bool (sucess status)
	return status

def addativeConnectionBridge(attrA, attrB):
	if attrA and attrB:
		if attrB.isConnected():
			originConnection = attrB.listConnections(d = False, s = True, p = True)[0]
			adlNode(originConnection, attrA, attrB)
		else:
			connectAttrAttempt(attrA, attrB)

def mnsPointsOnCurveNode(**kwargs):
	"""Creates an mnsPointOnCurve node based on specified parameters and outputs.
	A 'buildOutputs' parameter is defaulted to True to build output (of a choice of any mnsType)."""

	mnsUtils.isPluginLoaded("mnsPointsOnCurve")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "pointsOnCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsPointsOnCurve", incrementAlpha = incrementAlpha)

	inputCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputCurve", "")) #arg; comment = name of the curve object to connect as input curve into the node. Setting as nothing or an invalid name will result in nothing connected
	inputUpCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputUpCurve", "")) #arg; comment = name of the up-curve object to connect as input up-curve into the node. Setting as nothing or an invalid name will result in nothing connected

	transforms = kwargs.get("transforms", []) #arg; comment = array of object to output to;
	buildMode = kwargs.get("buildMode", 0) #arg; optionBox = parametric, uniform, fixedLength, parametricallyUnifom; comment = Node's build mode attribute
	numOutputs = kwargs.get("numOutputs", 10) #arg; min = 1; comment = set the number of outputs or samples to be outputed from the node
	doRotate = kwargs.get("doRotate", True) #arg; comment = Node's 'doRotate' attribute
	rotateMode = kwargs.get("rotateMode", 0) #arg; optionBox = curveTangent, objectAim, lookAtNext, curveAim, objectOrientAim; comment = Node's 'rotateMode' attribute
	upMode = kwargs.get("upMode", 1) #arg; optionBox = normal, curve, worldX, worldY, worldZ, objectUp, objectOrientUp; comment = Node's 'upMode' attribute
	aimAxis = kwargs.get("aimAxis", 0) #arg; optionBox = x, y, z, -x, -y, -z; comment = Node's 'aimAxis' attribute
	upAxis = kwargs.get("upAxis", 1) #arg; optionBox = x, y, z, -x, -y, -z; comment = Node's 'upAxis' attribute
	doScale = kwargs.get("doScale", True) #arg; comment = Node's 'doScale' attribute
	doSpring = kwargs.get("doSpring", False) #arg; comment = Node's 'doSpring' attribute
	connectTranslate = kwargs.get("connectTranslate", True) #arg; comment = Translate connect to the outputs if True
	connectRotate = kwargs.get("connectRotate", True) #arg; comment = Rotate connect to the outputs if True
	connectChildrenRotate = kwargs.get("connectChildrenRotate", False) #arg; comment = In case this attribute is set to True, along side connectRotate attribute, the indevidual rotation child attributes will be connected instead of the main compound rotate attribute
	connectScale = kwargs.get("connectScale", True) #arg; comment = Scale connect to the outputs if True
	buildOutputs = kwargs.get("buildOutputs", True) #arg; comment = in case output array is empty or invalid, build outpus as outputbuildType and outputBuildName
	outputBuildSuffix = kwargs.get("outputBuildSuffix", "OutSample") #arg; comment = suffix fom built outputs, if chosen to build
	outputBuildType = mnsBuildObjectTypes[kwargs.get("buildType", 0)] #arg; comment = if buildOutputs is executing, build based on this type.
	buildVisGeo = kwargs.get("buildVisGeo", False) #arg; comment = build axisVisGeo for the samples (debug mode) 
	buildVisCubes = kwargs.get("buildVisCubes", False) #arg; comment = build axisVisGeo for the samples (debug mode) 
	customPointsUpMode = kwargs.get("customPointsUpMode", 1) #arg; optionBox = normal, curve, worldX, worldY, worldZ, objectUp;
	isolatePolesTranlation = kwargs.get("isolatePolesTranlation", False) #arg; 
	isolatePolesRotation = kwargs.get("isolatePolesRotation", False) #arg; 
	isolatePolesScale = kwargs.get("isolatePolesScale", False) #arg; 
	baseAlternateWorldMatrix = kwargs.get("baseAlternateWorldMatrix", None) #arg; 
	tipAlternateWorldMatrix = kwargs.get("tipAlternateWorldMatrix", None) #arg; 


	#NODE
	pointsOnCurve_Node = nameStd.node
	connectAttrAttempt(baseAlternateWorldMatrix, pointsOnCurve_Node.baseAlternateWorldMatrix)
	connectAttrAttempt(tipAlternateWorldMatrix, pointsOnCurve_Node.tipAlternateWorldMatrix)

	pointsOnCurve_Node.setAttr("numOutputs", numOutputs)
	pointsOnCurve_Node.setAttr("doRotation", doRotate)
	pointsOnCurve_Node.setAttr("rotateMode", rotateMode)
	pointsOnCurve_Node.setAttr("aimAxis", aimAxis)
	pointsOnCurve_Node.setAttr("upAxis", upAxis)
	pointsOnCurve_Node.setAttr("upMode", upMode)
	pointsOnCurve_Node.setAttr("doScale", doScale)
	pointsOnCurve_Node.setAttr("doSpring", doSpring)
	pointsOnCurve_Node.setAttr("customPointsUpMode", customPointsUpMode)

	pointsOnCurve_Node.setAttr("excludePolesTranslation", isolatePolesTranlation)
	pointsOnCurve_Node.setAttr("excludePolesRotation", isolatePolesRotation)
	pointsOnCurve_Node.setAttr("excludePolesScale", isolatePolesScale)
	
	
	#connect inputCurves
	k = 0
	inputNames = ["curve", "upCurve"]
	for inputCrv in [inputCurve, inputUpCurve]:
		validS = 0
		if inputCrv:
			try:
				for shape in inputCrv.getShapes():
					if pm.objectType(shape, isType='nurbsCurve'): validS += 1
			except:
				pass
			if not validS: 
				suc = connectAttrAttempt(inputCrv, pointsOnCurve_Node + "." + inputNames[k])
				if k == 0:
					connectAttrAttempt(inputCrv, pointsOnCurve_Node + ".bindCurve")
					pointsOnCurve_Node.attr("bindCurve").disconnect()
					
				if not suc:
					mnsLog.log("\'" + inputCrv._name + "\' Doesn't have any valid nurbsCurve shape, this will be ignored and will not connect", svr = 1)
			else: 
				if validS > 1: mnsLog.log("\'" + inputCrv._name + "\' has more then one valid nurbsCurve shapes, connecting to the first direct child.", svr = 1)
				pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", pointsOnCurve_Node + "." + inputNames[k])
				if k == 0:
					pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", pointsOnCurve_Node + ".bindCurve")
					pointsOnCurve_Node.attr("bindCurve").disconnect()
		k+=1


	validArray = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = transforms)

	#check for build request
	builtArray = []
	builtArrayNodes = []
	if buildOutputs and not validArray:
		for i in range(0, numOutputs):
			transformA = ""
			transformA = mnsUtils.createNodeReturnNameStd(side = nameStd.side, body = nameStd.body, alpha = nameStd.alpha, id = 1, buildType = outputBuildType, incrementAlpha = False)

			if connectTranslate: pm.connectAttr(pointsOnCurve_Node.transforms[i].t, transformA.node.t)
			if connectRotate: 
				if not connectChildrenRotate:
					pm.connectAttr(pointsOnCurve_Node.transforms[i].r, transformA.node.r)
				else:
					addativeConnectionBridge(pointsOnCurve_Node.transforms[i].r.rx, transformA.node.rx)
					addativeConnectionBridge(pointsOnCurve_Node.transforms[i].r.ry, transformA.node.ry)
					addativeConnectionBridge(pointsOnCurve_Node.transforms[i].r.rz, transformA.node.rz)
			
			if connectScale: pm.connectAttr(pointsOnCurve_Node.transforms[i].s, transformA.node.s)
			builtArray.append(transformA)
			builtArrayNodes.append(transformA.node)
	elif validArray:
		builtArrayNodes = validArray
		i = 0
		for transformA in validArray:
			if connectTranslate: pointsOnCurve_Node.transforms[i].t >> transformA.t
			if connectRotate: 
				if not connectChildrenRotate:
					pointsOnCurve_Node.transforms[i].r >> transformA.r
				else:
					addativeConnectionBridge(pointsOnCurve_Node.transforms[i].r.rx, transformA.rx)
					addativeConnectionBridge(pointsOnCurve_Node.transforms[i].r.ry, transformA.ry)
					addativeConnectionBridge(pointsOnCurve_Node.transforms[i].r.rz, transformA.rz)

			if connectScale: pointsOnCurve_Node.transforms[i].s >> transformA.s
			i += 1
	if buildVisGeo:
		buildGeoAxisVisForParents(parentObjs = builtArray)
	if buildVisCubes:
		buildVisCubesForPSOCNode(nameStd.node)

	pm.dgdirty(nameStd.node)
	pm.refresh()
	
	pointsOnCurve_Node.setAttr("mode", buildMode)

	#return;dict ('node': MnsNameStd, 'samplesSTDs': output MnsNameStd list, 'samples': output node list)
	return {"node": nameStd, "samplesSTDs": builtArray, "samples": builtArrayNodes}

def mnsAnnotateNode(**kwargs):
	"""Creates an mnsAnnotateNode node based on specified parameters and outputs.
	Input as a node.channel list."""

	mnsUtils.isPluginLoaded("mnsAnnotate")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "annotate") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	attributes = kwargs.get("attributes", []) #arg; Input as a 'node.channel' string list.
	nameOnlyMode = kwargs.get("nameOnlyMode", False) #arg; 

	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsAnnotate", incrementAlpha = incrementAlpha)
	nameStd.node.attr("nameOnlyMode").set(nameOnlyMode)

	if attributes:
		k = 0
		for attr in attributes:
			try:
				pm.connectAttr (attr, (nameStd.node + ".attrs[" + str(k) + "]"))
				k+=1
			except:
				mnsLog.log("could not connect attr - " + attr + " - skipping.", svr = 1)
	#return; dict ('node': MnsNameStd)
	return nameStd

def buildVisCubesForPSOCNode(node = "", **kwargs):
	"""Single use function.
	From a given MnsPointsOnCurve node, create output 'visCubes'."""

	node = mnsUtils.checkIfObjExistsAndSet(obj = node)
	gapWidth = kwargs.get("gapWidth", 0.1) / 2 #arg;
	
	returnCubes = []
	returnNodes = []
	if node:
		if type(node).__name__ == "MnsPointsOnCurve":
			psocBuildState = node.getAttr("mode")
			if psocBuildState == 1:
				curveLength = node.getAttr("curveLength")
				numSamples = node.getAttr("numOutputs")
				interval = curveLength / (numSamples - 1)
				samples = list(set(pm.listConnections(node.transforms)))  
				axisShaders = ""
				if len(samples) > 0: axisShaders = mnsUtils.createAxisLamberts()
				for sam in samples:
					nameStdA = mnsUtils.splitNameStringToNameStd(sam.name())
					cubeNameStd = mnsUtils.returnNameStdChangeElement(nameStdA, suffix = mnsPS_geo)
					cube = pm.polyCube(w = interval - gapWidth ,h= interval - gapWidth, d= interval- gapWidth, sx=1, sy=1, sz=1, ax= (0,1,0), cuv =0, ch = 0, name = cubeNameStd.name)[0]
					cubeNameStd.node = cube
					pm.select ((cubeNameStd.name + ".f[1]"), (cubeNameStd.name + ".f[3]"))
					pm.hyperShade(assign= axisShaders["YAxisShader"])
					pm.select ((cubeNameStd.name + ".f[0]"), (cubeNameStd.name + ".f[2]"))
					pm.hyperShade(assign= axisShaders["ZAxisShader"])
					pm.select ((cubeNameStd.name + ".f[4]"), (cubeNameStd.name + ".f[5]"))
					pm.hyperShade(assign= axisShaders["XAxisShader"])
					pm.select(d=1)
					pm.parent(cubeNameStd.node, sam)
					for axis in "xyz":
						for channel in "trs":
							if channel is not "s":
								cubeNameStd.node.setAttr( (channel + axis), 0 )
							else:
								cubeNameStd.node.setAttr( (channel + axis), 1 )
					returnCubes.append(cubeNameStd)
					returnNodes.append(cubeNameStd.node)
			pm.select (node)

	#return;dict ('visCubesStds': output MnsNameStd list, 'nodes': output node list )
	return {"visCubesStds": returnCubes, "nodes": returnNodes}

def mnsBuildTransformsCurveNode(**kwargs):
	"""Creates an mnsBuildTransformsCurveNode node based on specified parameters and outputs.
	"""

	mnsUtils.isPluginLoaded("mnsBuildTransformsCurve")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "buildTransformsCurveCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsBuildTransformsCurve", incrementAlpha = incrementAlpha)
	transforms = kwargs.get("transforms", []) #arg; comment =  transforms to build the curve from
	buildOffsetCurve = kwargs.get("buildOffsetCurve", False) #arg; comment = Node's 'buildOffsetCurve' attribute 
	offsetCurveSuffix = kwargs.get("offsetCurveSuffix", "Up") #arg; comment = Up curve creation name body suffix
	buildMode = kwargs.get("buildMode", 0) #arg; optionBox = EPs, CVs, Hermite, TangentedCVs, Bezier; comment = Node's buildMode attribute
	tangentDirection = kwargs.get("tangentDirection", 1) #arg; optionBox = X, Y, Z; comment = Node's tangentDirection attribute
	tangentLength = kwargs.get("tangentLength", 1.0) #arg; comment = Node's tangentLength attribute
	hermiteSteps = kwargs.get("hermiteSteps", 5) #arg; min = 1; max = 10; comment = Node's hermiteSteps attribute
	degree = kwargs.get("degree", 3) #arg; min = 1; max = 5; comment = Node's degree attribute
	form = kwargs.get("form", 0) #arg; optionBox = open,periodic; comment = curve form attribute. Periodic will result in a closed shape.
	offsetType = kwargs.get("offsetType", 0) #arg; optionBox = local, world; comment = Node's offsetType attribute
	offsetX = kwargs.get("offsetX", 0.0) #arg; min = -20; max = 20; comment = Node's offsetX attribute
	offsetY = kwargs.get("offsetY", 0.0) #arg; min = -20; max = 20; comment = Node's offsetY attribute
	offsetZ = kwargs.get("offsetZ", 0.0) #arg; min = -20; max = 20; comment = Node's offsetZ attribute
	reverse = kwargs.get("reverse", False) #arg; comment = Node's reverse attribute
	deleteCurveObjects = kwargs.get("deleteCurveObjects", False)
	connectLocalMatrix = kwargs.get("connectLocalMatrix", False)
	localize = kwargs.get("localize", False)
	worldToLocalMatrix =  kwargs.get("worldToLocalMatrix", None)

	transforms = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = transforms)
	if transforms:
		k = 0
		for t in transforms:
			inputAttr = t.worldMatrix[0]
			if connectLocalMatrix: inputAttr = t.matrix
			
			pm.connectAttr(inputAttr, nameStd.node + ".transforms[" + str(k) + "].matrix")
			k += 1

	outUpCurve = ""
	outCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "curve", incrementAlpha = incrementAlpha)
	pm.connectAttr(nameStd.node + ".outCurve" , outCurve.node.getShape() + ".create")
	
	if buildOffsetCurve == True:
		outUpCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body + offsetCurveSuffix, alpha = alpha, id = id, buildType = "curve", incrementAlpha = incrementAlpha)
		pm.connectAttr(nameStd.node + ".outOffsetCurve" , outUpCurve.node.getShape() + ".create")
	

	nameStd.node.setAttr("buildMode", buildMode)
	nameStd.node.setAttr("buildOffsetCurve", buildOffsetCurve)
	nameStd.node.setAttr("tangentDirection", tangentDirection)
	nameStd.node.setAttr("tangentLength", tangentLength)
	nameStd.node.setAttr("HermiteSteps", hermiteSteps)
	nameStd.node.setAttr("degree", degree)
	nameStd.node.setAttr("form", form)
	nameStd.node.setAttr("OffsetType", offsetType)
	nameStd.node.setAttr("offsetX", offsetX)
	nameStd.node.setAttr("offsetY", offsetY)
	nameStd.node.setAttr("offsetZ", offsetZ)
	nameStd.node.setAttr("reverse", reverse)
	nameStd.node.setAttr("localize", localize)
	if worldToLocalMatrix: connectAttrAttempt(worldToLocalMatrix, nameStd.node.attr("worldToLocalMatrix"))

	if deleteCurveObjects:
		outCurve.node.attr("create").disconnect()
		pm.delete(outCurve.node)
		if outUpCurve: 
			outUpCurve.node.attr("create").disconnect()
			pm.delete(outUpCurve.node) 

	#return;dict ('transforms': input transforms list, 'outCurve': built output curve MnsNameStd, 'outOffsetCurve': built output up-curve MnsNameStd, 'node': Created node MnsNameStd)
	return {"transforms": transforms, "outCurve": outCurve, "outOffsetCurve": outUpCurve, "node": nameStd}

def mnsMatrixConstraintNode(**kwargs):
	"""Creates an mnsMatrixConstraintNode node based on specified parameters and outputs.
	"""

	mnsUtils.isPluginLoaded("mnsMatrixConstraint")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "matrixConstraint") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	targets = kwargs.get("targets", []) #arg; comment = Tragets to constrain
	sources = kwargs.get("sources", []) #arg; comment = Sources to constrain the targets to

	maintainOffset = kwargs.get("maintainOffset", False) #arg; comment = Node's maintainOffset attribute
	connectTranslate = kwargs.get("connectTranslate", True) #arg; comment = Connect Translate if True
	connectRoatete = kwargs.get("connectRotate", True) #arg; comment = Connect Rotate if True
	connectScale = kwargs.get("connectScale", True) #arg; comment = Connect Scale if True
	connectShear = kwargs.get("connectShear", connectScale) #arg; comment = Connect shear if True

	targets = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = targets)
	sources = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = sources)

	nameStdsReturn = []
	if targets and sources and (connectTranslate or connectRoatete or connectScale):
		for tar in targets:
			nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsMatrixConstraint", incrementAlpha = incrementAlpha)
			pm.connectAttr(tar.worldMatrix[0], nameStd.node.targetWorldMatrix) 
			pm.disconnectAttr(tar.worldMatrix[0], nameStd.node.targetWorldMatrix) 
			pm.connectAttr(tar.parentInverseMatrix[0], nameStd.node.targetParentInverseMatrix) 
			pm.connectAttr(tar.rotateOrder, nameStd.node.targetRotateOrder) 
			for k in range(0, len(sources)):
				pm.connectAttr(sources[k].worldMatrix[0], nameStd.node.sourceWorldMatrix[k]) 

			if connectTranslate: pm.connectAttr(nameStd.node.t, tar.t) 
			if connectRoatete: pm.connectAttr(nameStd.node.r, tar.r) 
			if connectScale: pm.connectAttr(nameStd.node.s, tar.s) 
			if connectShear: nameStd.node.shear >> tar.shear 

			nameStd.node.setAttr("maintainOffset", maintainOffset)
			nameStdsReturn.append(nameStd)
			
	#return;dict ('nameStds': Created MnsNameStd list)
	return {"nameStds": nameStdsReturn}

def mdNode(input1 = None, input2 = None, output = None, **kwargs):
	"""Create a new multiply devide node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "multDev") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	operation = kwargs.get("operation", 1) #arg; optionBox = noOperation, multiply, divide, power
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "multiplyDivide", incrementAlpha = incrementAlpha)
	nameStd.node.attr("operation").set(operation)

	asList = [input1, input2, output]
	attrList = ["input1", "input2", "output"]
	plugList = ["X", "Y", "Z"]

	for k in range(0, 3):
		if asList[k]:
			connect = False
			if not type(asList[k]) is list:
				if attrList[k] == "output": connect = connectSetAttempt(nameStd.node.attr(attrList[k]), asList[k], float)
				else: connect = connectSetAttempt(asList[k], nameStd.node.attr(attrList[k]), float)
			if not connect: 
				if not type(asList[k]) is list: asList[k] = [asList[k]]
				j = 0
				for plug in asList[k]:
					if plug or plug == 0 or plug == 0.0: 
						if attrList[k] == "output": connectSetAttempt(nameStd.node.attr(attrList[k] + plugList[j]), plug, float)
						else: connectSetAttempt(plug, nameStd.node.attr(attrList[k] + plugList[j]), float)
					j += 1
	#return;MnsNameStd (MultiplyDevide node)
	return nameStd

def adlNode(input1 = None, input2 = None, output = None, **kwargs):
	"""Create a new addDoubleLinear node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "addDoubleLinear") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	
	if GLOB_mayaVersion > 2025:
		nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "sumDL", incrementAlpha = incrementAlpha)
		
		if input1: connectSetAttempt(input1, nameStd.node.attr("input[0]"), float)
		if input2: connectSetAttempt(input2, nameStd.node.attr("input[1]"), float)
		if output: connectAttrAttempt(nameStd.node.attr("output"), output)

		#return;MnsNameStd (addDoubleLinear node)
		return nameStd
	else:
		nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "addDoubleLinear", incrementAlpha = incrementAlpha)

		if input1: connectSetAttempt(input1, nameStd.node.attr("input1"), float)
		if input2: connectSetAttempt(input2, nameStd.node.attr("input2"), float)
		if output: connectAttrAttempt(nameStd.node.attr("output"), output)

		#return;MnsNameStd (addDoubleLinear node)
		return nameStd

def mdlNode(input1 = None, input2 = None, output = None, **kwargs):
	"""Create a new multiplyDoubleLinear node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "multDoubleLinear") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True

	if GLOB_mayaVersion > 2025:
		nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "multiplyDL", incrementAlpha = incrementAlpha)

		if input1: connectSetAttempt(input1, nameStd.node.attr("input[0]"), float)
		if input2: connectSetAttempt(input2, nameStd.node.attr("input[1]"), float)
		if output: connectAttrAttempt(nameStd.node.attr("output"), output)

		#return;MnsNameStd (addDoubleLinear node)
		return nameStd
	else:
		nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "multDoubleLinear", incrementAlpha = incrementAlpha)

		if input1: connectSetAttempt(input1, nameStd.node.attr("input1"), float)
		if input2: connectSetAttempt(input2, nameStd.node.attr("input2"), float)
		if output: connectAttrAttempt(nameStd.node.attr("output"), output)

		#return;MnsNameStd (multiplyDoubleLinear node)
		return nameStd

def decomposeMatrixNode(inputMatrix = None, outputTranslate = None, outputRotate = None, outputScale = None, **kwargs):
	"""Create a new multiplyDoubleLinear node using the given inputs.
	"""

	if GLOB_mayaVersion == 2017:
		mnsUtils.isPluginLoaded("matrixNodes")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "decomposeMatrix") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "decomposeMatrix", incrementAlpha = incrementAlpha)

	if inputMatrix: connectAttrAttempt(inputMatrix, nameStd.node.attr("inputMatrix"))
	if outputTranslate: connectAttrAttempt(nameStd.node.attr("outputTranslate"), outputTranslate)
	if outputRotate: connectAttrAttempt(nameStd.node.attr("outputRotate"), outputRotate)
	if outputScale: connectAttrAttempt(nameStd.node.attr("outputScale"), outputScale)

	#return;MnsNameStd (multiplyDoubleLinear node)
	return nameStd

def mnsNodeRelationshipNode(**kwargs):
	"""Create a new mnsNodeRelationship node using the given inputs.
	"""

	mnsUtils.isPluginLoaded("mnsNodeRelationship")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "nodeRelationship") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	connectDeleteSlavesOnly = kwargs.get("connectDeleteSlavesOnly", False) #arg; 
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsNodeRelationship", incrementAlpha = incrementAlpha)

	master = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("master", None)) #arg;
	slaves = kwargs.get("slaves", []) #arg; 

	if master: 
		attr = mnsUtils.addAttrToObj([master], type = "message", name = "messageOut", value= "", replace = False)
		attr = master.attr("messageOut")
		connectAttrAttempt(master.attr("messageOut"), nameStd.node.attr("messageIn"))

	if slaves: 
		for slv in slaves:
			if not connectDeleteSlavesOnly:
				attr = mnsUtils.addAttrToObj([slv], type = "message", name = "masterIn", value= "", replace = True)[0]
				connectAttrAttempt(nameStd.node.messageOut, attr)
			else:
				attr = mnsUtils.addAttrToObj([slv], type = "message", name = "deleteMaster", value= "", replace = True)[0]
				connectAttrAttempt(nameStd.node.deleteSlaves, attr)

	#return;MnsNameStd (mnsNodeRelationship node)
	return nameStd

def buildGeoAxisVis(**kwargs):
	"""Utility aid function:
	Creates a Axis-Vis geometry object based on parameters"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "pointsOnCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = MnsNameStd(side = side, body = body, alpha = alpha, id = id, type = MnsTypeStd(name = "axisVis", suffix = mnsPS_axisVis, createName = "mesh"))
	nameStd.findNextIncrement()
	scaleA = kwargs.get("scale", 1) #arg; comment = Relative to parent
	axisSubdevision = kwargs.get("axisSubdevision", 16) #arg; comment = Geometry cylinder axis subdevision
	cylinderWidth = kwargs.get("cylinderWidth", 0.015) #arg; min = 0.001; max = 0.3;
	deleteAll = kwargs.get("deleteAll", False) #arg; comment = If true, do not attempt to create any objects- instead look for any existing objects and delete them

	if not deleteAll:
		lambertDict = mnsUtils.createAxisLamberts()
		axises = []
		rotations = [(0,0,-90), (0,0,0), (90,0,0)] 
		axisNames = "XYZ"
		for i in range (0,3):
			cyl = pm.polyCylinder(r = cylinderWidth, h=0.9, sx = axisSubdevision, sy = 1, sz=0, ax = (0,1,0), rcp = 0 , cuv = 3 , ch= 0)[0];
			pm.delete(cyl.f[axisSubdevision:axisSubdevision+1])
			cyl.setAttr("ty", 0.45)
			cone = pm.polyCone(r=cylinderWidth*2, h=0.1, sx=axisSubdevision, sy=1, sz=0, ax = (0,1,0), rcp=0, cuv=3, ch=0)[0];
			cone.setAttr("ty", 0.95)
			axis = pm.polyUnite([cyl, cone], ch= 0 ,mergeUVSets=1, centerPivot = 1, name= axisNames[i])[0];
			axis.setAttr("rotatePivot", (0,0,0));
			axis.setAttr("r", rotations[i])
			pm.hyperShade(axis, assign= lambertDict[axisNames[i] + "AxisShader"])
			axises.append(axis)
		visGeo = pm.polyUnite(axises, ch= 0 ,mergeUVSets=1, centerPivot = 0, name= ("axisVis" + "_" + mnsPS_geo))[0]
		visGeo.sx.set(scaleA)
		visGeo.sy.set(scaleA)
		visGeo.sz.set(scaleA)
		pm.makeIdentity(visGeo, apply = 1)
		pm.rename(visGeo, nameStd.name)
		nameStd.node = visGeo
	else:
		existing = pm.ls("*_" + mnsPS_axisVis)
		if len(existing) > 0:
			pm.delete(existing)
		nameStd = None

	#return;MnsNameStd (created vis-geo object)
	return nameStd

def buildGeoAxisVisForParents(**kwargs):
	"""Utility aid function.
	Created an Axis-Vis geometry object from each object within the list passed in."""

	parentObjs = kwargs.get("parentObjs", []) #arg; comment = If parent is empty, visGeo will not build
	parentMethod = kwargs.get("parentMethod", 0) #arg; optionBox = directParent, parentConstraint, directConnect, matrixConstraint
	scaleA = kwargs.get("scale", 1) #arg; comment = Relative to parent
	axisSubdevision = kwargs.get("axisSubdevision", 16) #arg; comment = Geometry cylinder axis subdevision
	cylinderWidth = kwargs.get("cylinderWidth", 0.015) #arg; min = 0.001; max = 0.3;
	createNodeRelationship = kwargs.get("createNodeRelationship", True) #arg;

	validArray = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = parentObjs)
	if validArray:
		visGeoArray = []
		visGeoArrayNodes = []

		visGeoA = buildGeoAxisVis(scale = scaleA, axisSubdevision= axisSubdevision, cylinderWidth= cylinderWidth)
		for obj in validArray:
			objNameStd = mnsUtils.splitNameStringToNameStd(obj)
			nameStd = mnsUtils.returnNameStdChangeElement(objNameStd, suffix = mnsPS_axisVis, autoRename = False)

			visGeoDup = pm.duplicate(visGeoA.node, name = nameStd.name)[0]
			nameStd.node = visGeoDup

			if parentMethod == 0: 
				pm.parent(nameStd.node, obj)
				mnsUtils.zeroTransforms(nameStd)
			elif parentMethod == 1:
				pm.parentConstraint(obj, nameStd.node)
			elif parentMethod == 2:
				obj.t >> nameStd.node.t
				obj.r >> nameStd.node.r
				obj.s >> nameStd.node.s
			else:
				mnsMatrixConstraintNode(side = nameStd.side, alpha = nameStd.alpha, id = nameStd.id, targets = [nameStd.node], sources = [obj])

			if createNodeRelationship: mnsNodeRelationshipNode(master = objNameStd, slaves = [nameStd])

			visGeoArray.append(nameStd)
			visGeoArrayNodes.append(nameStd.node)
		pm.delete(visGeoA.node)

	#return;dict ('visGeoObjs': visGeoMnsNameStdArray, 'visGeoObjsNodes': visGeoNodeArray)
	return {"visGeoObjs": visGeoArray, "visGeoObjsNodes": visGeoArrayNodes}

def mnsCameraGateRatioNode(**kwargs):
	"""Create a new mnsCameraGateRatio node using the given inputs.
	"""

	mnsUtils.isPluginLoaded("mnsCameraGateRatio")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "cameraGateRatio") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsCameraGateRatio", incrementAlpha = incrementAlpha)

	cam = kwargs.get("camera", "") #arg; 
	width = kwargs.get("widthInput", "") #arg; 
	height = kwargs.get("heightInput", "") #arg; 

	if cam: 
		cam = mnsUtils.checkIfObjExistsAndSet(obj = cam)
		if cam:
			shape = None
			try: cam = cam.getShape()
			except: pass
			if type(cam) != pm.nodetypes.Camera: cam = None

	if width: connectSetAttempt(width, nameStd.node.attr("gateWidth"), float)
	if height: connectSetAttempt(height, nameStd.node.attr("gateHeight"), float)
	if cam: connectAttrAttempt(cam.message ,nameStd.node.attr("cameraIn"))

	if width: pm.setAttr(width, pm.getAttr(width))
	if height: pm.setAttr(height, pm.getAttr(height))

	#return;MnsNameStd (mnsCameraGateRatio node)
	return nameStd

def conditionNode(firstTerm = None, secondTerm = None, colorIfTrue = None, colorIfFalse = None, outColor = None, **kwargs):
	"""Create a new condition node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "condition") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	operation = kwargs.get("operation", 0) #arg; optionBox = equal, notEqual, greaterThan, greaterOrEqual, lessThan, LessOrEqual
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "condition", incrementAlpha = incrementAlpha)
	nameStd.node.attr("operation").set(operation)

	asList = [colorIfTrue, colorIfFalse, outColor]
	attrList = ["colorIfTrue", "colorIfFalse", "outColor"]
	plugList = ["R", "G", "B"]
	for k in range(0, 3):
		if asList[k]:
			connect = False
			if not type(asList[k]) is list:
				if attrList[k] == "outColor": connect = connectSetAttempt(nameStd.node.attr(attrList[k]), asList[k], float)
				else: connect = connectSetAttempt(asList[k], nameStd.node.attr(attrList[k]), float)
			if not connect: 
				if not type(asList[k]) is list: asList[k] = [asList[k]]
				j = 0
				for plug in asList[k]:
					if plug or plug == 0 or plug == 0.0: 
						if attrList[k] == "outColor": connectSetAttempt(nameStd.node.attr(attrList[k] + plugList[j]), plug, float)
						else: connectSetAttempt(plug, nameStd.node.attr(attrList[k] + plugList[j]), float)
					j += 1

	if firstTerm: connectSetAttempt(firstTerm, nameStd.node.attr("firstTerm"), float)
	if secondTerm: connectSetAttempt(secondTerm, nameStd.node.attr("secondTerm"), float)

	#return;MnsNameStd (condition node)
	return nameStd

def reverseNode(inputA = None, output = None, **kwargs):
	"""Create a new reverse node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "reverse") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "reverse", incrementAlpha = incrementAlpha)

	asList = [inputA, output]
	attrList = ["input", "output"]
	plugList = ["X", "Y", "Z"]
	for k in range(0, 2):
		if asList[k]:
			connect = False
			if not type(asList[k]) is list:
				if attrList[k] == "output": connect = connectSetAttempt(nameStd.node.attr(attrList[k]), asList[k], float)
				else: connect = connectSetAttempt(asList[k], nameStd.node.attr(attrList[k]), float)
			if not connect: 
				if not type(asList[k]) is list: asList[k] = [asList[k]]
				j = 0
				for plug in asList[k]:
					if plug or plug == 0 or plug == 0.0: 
						if attrList[k] == "output": connectSetAttempt(nameStd.node.attr(attrList[k] + plugList[j]), plug, float)
						else: connectSetAttempt(plug, nameStd.node.attr(attrList[k] + plugList[j]), float)
					j += 1

	#return;MnsNameStd (reverse node)
	return nameStd

def mnsIKSolver(**kwargs):
	"""Create a new mnsIkSolver node using the given inputs.
	"""

	mnsUtils.isPluginLoaded("mnsIKSolver")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "ikSolver") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	ikSolveNameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsIKSolver", incrementAlpha = incrementAlpha)

	blend = kwargs.get("blend", 0.0) #arg; 
	ikSolveNameStd.node.blend.set(blend)
	roll = kwargs.get("roll", 0.0) #arg; 
	ikSolveNameStd.node.roll.set(roll)
	slide = kwargs.get("slide", 0.0) #arg; 
	ikSolveNameStd.node.slide.set(slide)
	softness = kwargs.get("softness", 0.0) #arg; 
	ikSolveNameStd.node.softness.set(softness)
	stretchLimit = kwargs.get("stretchLimit", 1.0) #arg; 
	ikSolveNameStd.node.stretchLimit.set(stretchLimit)
	aimAxis = kwargs.get("aimAxis", 1) #arg; optionBox = x, y, z, -x, -y, -z; comment = Node's 'aimAxis' attribute
	ikSolveNameStd.node.aimAxis.set(aimAxis)
	upAxis = kwargs.get("upAxis", 2) #arg; optionBox = x, y, z, -x, -y, -z; comment = Node's 'upAxis' attribute
	ikSolveNameStd.node.upAxis.set(upAxis)


	boneLengthA = kwargs.get("boneLengthA", 1.0) #arg; 
	boneLengthB = kwargs.get("boneLengthB", 1.0) #arg; 
	restHandleLength = kwargs.get("restHandleLength", 1.0) #arg; 

	rootPos =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("rootPos", "")) #arg; 
	midPos =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("midPos", "")) #arg; 
	endPos =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("endPos", "")) #arg; 

	if rootPos and midPos: boneLengthA = mnsUtils.distBetween(rootPos, midPos)
	if midPos and endPos: boneLengthB = mnsUtils.distBetween(midPos , endPos)
	if rootPos and endPos: restHandleLength = mnsUtils.distBetween(rootPos , endPos)

	limbRoot =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("limbRoot", "")) #arg; 
	if limbRoot: limbRoot.worldMatrix[0] >> ikSolveNameStd.node.rootWorldMatrix

	ikSolveNameStd.node.bla.set(boneLengthA)
	ikSolveNameStd.node.blb.set(boneLengthB)
	ikSolveNameStd.node.restHandleLength.set(restHandleLength)

	ikHandle =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("ikHandle", "")) #arg; 
	if ikHandle: ikHandle.worldMatrix[0] >> ikSolveNameStd.node.ikTarget

	poleVector =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("poleVector", "")) #arg; 
	if poleVector: poleVector.worldMatrix[0] >> ikSolveNameStd.node.poleVector

	fkRoot =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("fkRoot", "")) #arg; 
	if fkRoot: fkRoot.worldMatrix[0] >> ikSolveNameStd.node.rootFK

	fkMid =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("fkMid", "")) #arg; 
	if fkMid: fkMid.worldMatrix[0] >> ikSolveNameStd.node.midFK

	fkEnd =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("fkEnd", "")) #arg; 
	if fkEnd: fkEnd.worldMatrix[0] >> ikSolveNameStd.node.endFK


	outputRoot =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("outputRoot", "")) #arg; 
	if outputRoot: 
		ikSolveNameStd.node.rootTranslate >> outputRoot.t
		ikSolveNameStd.node.rootRotate >> outputRoot.r
		ikSolveNameStd.node.rootScale >> outputRoot.s

	outputMid =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("outputMid", "")) #arg; 
	if outputMid: 
		ikSolveNameStd.node.midTranslate >> outputMid.t
		ikSolveNameStd.node.midRotate >> outputMid.r
		ikSolveNameStd.node.midScale >> outputMid.s

	outputEnd =  mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("outputEnd", "")) #arg; 
	if outputEnd: 
		ikSolveNameStd.node.endTranslate >> outputEnd.t
		ikSolveNameStd.node.endRotate >> outputEnd.r
		ikSolveNameStd.node.endScale >> outputEnd.s

	#return;MnsNameStd (mnsIkSolver node)
	return ikSolveNameStd

def choiceNode(inputs = [], output = None, **kwargs):
	"""Create a new choice node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "choice") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "choice", incrementAlpha = incrementAlpha)

	if inputs: 
		for i in range(len(inputs)): connectAttrAttempt(inputs[i], nameStd.node.attr("input[" + str(i) + "]"))
	if output: connectAttrAttempt(nameStd.node.attr("output"), output)

	#return;MnsNameStd (choice node)
	return nameStd

def imagePlaneNode(camera = None, **kwargs):
	"""Create a new imagePlane node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "imagePlane") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "imagePlane", incrementAlpha = incrementAlpha)
	nameStd.node.getShape().lockedToCamera.set(False)

	#return;MnsNameStd (imagePlane node)
	return nameStd

def mnsCurveVariableNode(**kwargs):
	"""Creates an mnsCurveVariable node based on specified parameters and outputs.
	"""

	mnsUtils.isPluginLoaded("mnsCurveVariable")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "curveVariable") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	curveVar = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsCurveVariable", incrementAlpha = incrementAlpha)

	inputCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputCurve", "")) #arg; comment = name of the curve object to connect as input curve into the node. Setting as nothing or an invalid name will result in nothing connected
	inputUpCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputUpCurve", "")) #arg; comment = name of the up-curve object to connect as input up-curve into the node. Setting as nothing or an invalid name will result in nothing connected
	offsetCurveSuffix = kwargs.get("offsetCurveSuffix", "Up") #arg; comment = Up curve creation name body suffix
	deleteCurveObjects = kwargs.get("deleteCurveObjects", False)

	inTransforms = kwargs.get("inTransforms", []) #arg; comment = array of object to plug into the input array plug;
	outOffsetTransforms = kwargs.get("outOffsetTransforms", []) #arg; 
	upMode = kwargs.get("upMode", 1) #arg; optionBox = normal, curve, worldX, worldY, worldZ, objectUp; comment = Node's 'upMode' attribute
	aimAxis = kwargs.get("aimAxis", 0) #arg; optionBox = x, y, z, -x, -y, -z; comment = Node's 'aimAxis' attribute
	upAxis = kwargs.get("upAxis", 1) #arg; optionBox = x, y, z, -x, -y, -z; comment = Node's 'upAxis' attribute
	connectTranslate = kwargs.get("connectTranslate", True) #arg; comment = Translate connect to the outputs if True
	connectRotate = kwargs.get("connectRotate", True) #arg; comment = Rotate connect to the outputs if True
	offsetX = kwargs.get("offsetX", 10.0) #arg; min = -20; max = 20; comment = Node's offsetX attribute
	offsetY = kwargs.get("offsetY", 0.0) #arg; min = -20; max = 20; comment = Node's offsetY attribute
	offsetZ = kwargs.get("offsetZ", 0.0) #arg; min = -20; max = 20; comment = Node's offsetZ attribute
	substeps = kwargs.get("substeps", 20) #arg; 
	degree = kwargs.get("degree", 3) #arg; min = 1; max = 5;
	buildMode = kwargs.get("buildMode", 1) #arg; optionBox = EPs, CVs;
	translateMode = kwargs.get("translateMode", 0) #arg; optionBox = fk, ik;
	defaultFalloff = kwargs.get("defaultFalloff", 0.5) #arg; min = 0.01;
	defaultStregth= kwargs.get("defaultStregth", 1.0) #arg; min = 0.01;
	offsetType= kwargs.get("offsetType", 0) #arg; optionBox = local, world;

	#NODE
	curveVar_node = curveVar.node
	curveVar_node.setAttr("offsetX", offsetX)
	curveVar_node.setAttr("offsetY", offsetY)
	curveVar_node.setAttr("offsetZ", offsetZ)
	curveVar_node.setAttr("aimAxis", aimAxis)
	curveVar_node.setAttr("upAxis", upAxis)
	curveVar_node.setAttr("upMode", upMode)
	curveVar_node.setAttr("substeps", substeps)
	curveVar_node.setAttr("degree", degree)
	curveVar_node.setAttr("buildMode", buildMode)
	curveVar_node.setAttr("translateMode", translateMode)
	curveVar_node.setAttr("offsetType", offsetType)

	#connect inputCurves
	k = 0
	inputNames = ["curve", "upCurve"]
	for inputCrv in [inputCurve, inputUpCurve]:
		validS = 0
		if inputCrv:
			try:
				for shape in inputCrv.getShapes():
					if pm.objectType(shape, isType='nurbsCurve'): validS += 1
			except:
				pass
			if not validS: 
				suc = connectAttrAttempt(inputCrv, curveVar_node + "." + inputNames[k])
				if not suc:
					mnsLog.log("\'" + inputCrv._name + "\' Doesn't have any valid nurbsCurve shape, this will be ignored and will not connect", svr = 1)
			else: 
				if validS > 1: mnsLog.log("\'" + inputCrv._name + "\' has more then one valid nurbsCurve shapes, connecting to the first direct child.", svr = 1)
				pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", curveVar_node + "." + inputNames[k])
		k+=1


	validInputArray = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = inTransforms)
	if validInputArray:
		pairingDict = {"x": None, "y": None, "z": None}
		i = 0
		for transformA in validInputArray:
			transformA.matrix >> curveVar_node.inTransform[i].localMatrix
			
			mnsUtils.addAttrToObj([transformA], type = "enum", value = ["______"], name = "curveVariableCtrl", replace = True)
			maxValue = 1.0 - (1 / ((float(len(validInputArray)) - 1.0))* float(i))
			minValue = -(1.0 - maxValue)
			positionAttr = mnsUtils.addAttrToObj([transformA], type = "float", value = 0.0, name = "position", replace = True, min = minValue, max = maxValue)[0]
			falloffAttr = mnsUtils.addAttrToObj([transformA], type = "float", value = defaultFalloff, name = "falloff", replace = True, min = 0.01)[0]
			stregthAttr = mnsUtils.addAttrToObj([transformA], type = "float", value = defaultStregth, name = "strength", replace = True, min = 0.0)[0]
			transformA.ty >> curveVar_node.inTransform[i].aimTranslate
			transformA.tx >> curveVar_node.inTransform[i].upTranslate
			transformA.tz >> curveVar_node.inTransform[i].terTranslate

			transformA.ry >> curveVar_node.inTransform[i].aimRotation
			transformA.rx >> curveVar_node.inTransform[i].upRotation
			transformA.rz >> curveVar_node.inTransform[i].tertiaryRotation

			positionAttr >> curveVar_node.inTransform[i].uPosition
			falloffAttr >> curveVar_node.inTransform[i].falloff
			stregthAttr >> curveVar_node.inTransform[i].strength
			i += 1

	validOutputArray = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = outOffsetTransforms)
	if validOutputArray:
		i = 0
		for transformA in validOutputArray:
			if connectTranslate: 
				curveVar_node.outTransform[i].translate >> transformA.t

			if connectRotate: 
				curveVar_node.outTransform[i].rotate >> transformA.r
			i += 1

	if not deleteCurveObjects:
		outCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "curve", incrementAlpha = incrementAlpha)
		pm.connectAttr(curveVar_node + ".outCurve" , outCurve.node.getShape() + ".create")

		outUpCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body + offsetCurveSuffix, alpha = alpha, id = id, buildType = "curve", incrementAlpha = incrementAlpha)
		pm.connectAttr(curveVar_node + ".outOffsetCurve" , outUpCurve.node.getShape() + ".create")

	#return;dict ('node': MnsNameStd)
	return {"node": curveVar}

def mnsSpringCurveNode(**kwargs):
	"""Creates an mnsSpringCurve node based on specified parameters and outputs.
	"""

	mnsUtils.isPluginLoaded("mnsSpringCurve")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "springCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	springCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsSpringCurve", incrementAlpha = incrementAlpha)

	inputCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputCurve", "")) #arg; comment = name of the curve object to connect as input curve into the node. Setting as nothing or an invalid name will result in nothing connected
	inputUpCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputUpCurve", "")) #arg; comment = name of the up-curve object to connect as input up-curve into the node. Setting as nothing or an invalid name will result in nothing connected

	connectTime = kwargs.get("connectTime", True) #arg;
	startFrame = kwargs.get("startFrame", 1) #arg;
	startFrameFromRange = kwargs.get("startFrameFromRange", True) #arg;
	strength = kwargs.get("strength", 1.0) #arg;
	preventStretching = kwargs.get("preventStretching", True) #arg;
	deleteCurveObjects = kwargs.get("deleteCurveObjects", False) #arg;
	offsetCurveSuffix = kwargs.get("offsetCurveSuffix", "Up") #arg;
	attributeHost = mnsUtils.checkIfObjExistsAndSet(kwargs.get("attributeHost", None)) #arg;
	strengthDefault = kwargs.get("strengthDefault", 1.0) #arg; min = 0.01;

	#NODE
	springCurve_node = springCurve.node
	springCurve_node.startFrame.set(startFrame)
	springCurve_node.startFrameFromRange.set(startFrameFromRange)
	springCurve_node.strength.set(strength)
	springCurve_node.preventStretching.set(preventStretching)
	if connectTime: pm.connectAttr("time1.outTime", springCurve_node.time)

	#connect inputCurves
	k = 0
	inputNames = ["inputCurve", "inputOffsetCurve"]
	for inputCrv in [inputCurve, inputUpCurve]:
		validS = 0
		if inputCrv:
			try:
				for shape in inputCrv.getShapes():
					if pm.objectType(shape, isType='nurbsCurve'): validS += 1
			except:
				pass
			if not validS: 
				suc = connectAttrAttempt(inputCrv, springCurve_node + "." + inputNames[k])
				if not suc:
					mnsLog.log("\'" + inputCrv._name + "\' Doesn't have any valid nurbsCurve shape, this will be ignored and will not connect", svr = 1)
			else: 
				if validS > 1: mnsLog.log("\'" + inputCrv._name + "\' has more then one valid nurbsCurve shapes, connecting to the first direct child.", svr = 1)
				pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", springCurve_node + "." + inputNames[k])
		k+=1


	if not deleteCurveObjects:
		outCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "curve", incrementAlpha = incrementAlpha)
		pm.connectAttr(springCurve_node + ".outCurve" , outCurve.node.getShape() + ".create")

		outUpCurve = mnsUtils.createNodeReturnNameStd(side = side, body = body + offsetCurveSuffix, alpha = alpha, id = id, buildType = "curve", incrementAlpha = incrementAlpha)
		pm.connectAttr(springCurve_node + ".outOffsetCurve" , outUpCurve.node.getShape() + ".create")

	if attributeHost:
		mnsUtils.addAttrToObj([attributeHost], type = "enum", value = ["______"], name = "spring", replace = True)
		strengthAttr = mnsUtils.addAttrToObj([attributeHost], type = "float", value = strengthDefault, name = "strength", replace = True, min = 0.0, max = 1.0)[0]
		strengthAttr >> springCurve_node.strength
		startFrameAttr = mnsUtils.addAttrToObj([attributeHost], type = "int", value = 1, name = "startFrame", replace = True)[0]
		startFrameAttr >> springCurve_node.startFrame
		preventStretchAttr = mnsUtils.addAttrToObj([attributeHost], type = "bool", value = True, name = "preventStretching", replace = True)[0]
		preventStretchAttr >> springCurve_node.preventStretching
		startFrameFromRangeAttr = mnsUtils.addAttrToObj([attributeHost], type = "bool", value = True, name = "startFrameFromRange", replace = True)[0]
		startFrameFromRangeAttr >> springCurve_node.startFrameFromRange										

	#return;dict ('node': MnsNameStd)
	return {"node": springCurve}

def mnsResampleCurveNode(**kwargs):
	"""Creates an mnsReampleCurve node based on specified parameters and outputs.
	"""

	mnsUtils.isPluginLoaded("mnsResampleCurve")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "resampleCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsResampleCurve", incrementAlpha = incrementAlpha)
	resampleMode = kwargs.get("resampleMode", 0) #arg; optionBox = parametric, uniform; comment = Node's sample Mode
	degree = kwargs.get("degree", 3) #arg; min = 1; max = 5; comment = Output curve degree
	sections = kwargs.get("sections", 8) #arg; min = 4; comment = Output curve number of sections

	inputCrv = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputCurve", "")) #arg; comment = name of the curve object to connect as input curve into the node. Setting as nothing or an invalid name will result in nothing connected

	nameStd.node.setAttr("resampleMode", resampleMode)
	nameStd.node.setAttr("degree", degree)
	nameStd.node.setAttr("sections", sections)

	#connect inputCurves
	validS = 0
	if inputCrv:
		try:
			for shape in inputCrv.getShapes():
				if pm.objectType(shape, isType='nurbsCurve'): validS += 1
		except:
			pass
		if not validS: 
			suc = connectAttrAttempt(inputCrv, nameStd.node + ".inputCurve")
			if not suc:
				mnsLog.log("\'" + inputCrv._name + "\' Doesn't have any valid nurbsCurve shape, this will be ignored and will not connect", svr = 1)
		else: 
			if validS > 1: mnsLog.log("\'" + inputCrv._name + "\' has more then one valid nurbsCurve shapes, connecting to the first direct child.", svr = 1)
			pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", nameStd.node + ".inputCurve")

	#return;dict ('node': Created node MnsNameStd)
	return {"node": nameStd}

def mnsThreePointArcNode(**kwargs):
	"""Creates an mnsReampleCurve node based on specified parameters and outputs.
	"""

	mnsUtils.isPluginLoaded("mnsThreePointArc")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "threePointArc") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsThreePointArc", incrementAlpha = incrementAlpha)
	
	resampleMode = kwargs.get("resampleMode", 0) #arg; optionBox = parametric, uniform; comment = Node's sample Mode
	degree = kwargs.get("degree", 3) #arg; min = 1; max = 5; comment = Output curve degree
	sections = kwargs.get("sections", 8) #arg; min = 4; comment = Output curve number of sections
	conformMidPoint = kwargs.get("conformMidPoint", True) #arg; comment = conform to mid point flag
	collinearAction = kwargs.get("collinearAction", 0) #arg; optionBox = inputCurve, resample; 
	blend = kwargs.get("blend", 0.0) #arg;

	inputCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputCurve", "")) #arg; comment = name of the curve object to connect as input curve into the node. Setting as nothing or an invalid name will result in nothing connected
	inputUpCurve = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputUpCurve", "")) #arg; comment = name of the curve object to connect as input offset curve into the node. Setting as nothing or an invalid name will result in nothing connected

	nameStd.node.setAttr("resampleMode", resampleMode)
	nameStd.node.setAttr("degree", degree)
	nameStd.node.setAttr("sections", sections)
	nameStd.node.setAttr("conformMidPoint", conformMidPoint)
	nameStd.node.setAttr("collinearAction", collinearAction)
	nameStd.node.setAttr("blend", blend)

	#connect points
	pointA = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("pointA", ""))
	pointB = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("pointB", ""))
	pointC = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("pointC", ""))

	if pointA: pm.connectAttr(pointA.worldMatrix[0] , nameStd.node + ".point1")
	if pointB: pm.connectAttr(pointB.worldMatrix[0] , nameStd.node + ".point2")
	if pointC: pm.connectAttr(pointC.worldMatrix[0] , nameStd.node + ".point3")
	
	#connect inputCurves
	k = 0
	inputNames = ["inputCurve", "inputOffsetCurve"]
	for inputCrv in [inputCurve, inputUpCurve]:
		validS = 0
		if inputCrv:
			try:
				for shape in inputCrv.getShapes():
					if pm.objectType(shape, isType='nurbsCurve'): validS += 1
			except:
				pass
			if not validS: 
				suc = connectAttrAttempt(inputCrv, nameStd.node + "." + inputNames[k])
				if not suc:
					mnsLog.log("\'" + inputCrv._name + "\' Doesn't have any valid nurbsCurve shape, this will be ignored and will not connect", svr = 1)
			else: 
				if validS > 1: mnsLog.log("\'" + inputCrv._name + "\' has more then one valid nurbsCurve shapes, connecting to the first direct child.", svr = 1)
				pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", nameStd.node + "." + inputNames[k])
		k+=1

	#return;dict ('node': Created node MnsNameStd)
	return {"node": nameStd}

def inverseMatrixNode(inputMatrix = None, outputMatrix = None, **kwargs):
	"""Create a new inverseMatrix node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "choice") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "inverseMatrix", incrementAlpha = incrementAlpha)

	if inputMatrix: connectAttrAttempt(inputMatrix, nameStd.node.attr("inputMatrix"))
	if outputMatrix: connectAttrAttempt(nameStd.node.attr("outputMatrix"), outputMatrix)

	#return;MnsNameStd (inverseMatrix node)
	return nameStd

def multMatrixNode(inputMatricies = [], outputMatrix = None, **kwargs):
	"""Create a new inverseMatrix node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "multiplyMatrix") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "multMatrix", incrementAlpha = incrementAlpha)

	if inputMatricies:
		for k in range(len(inputMatricies)):
			connectAttrAttempt(inputMatricies[k], nameStd.node.attr("matrixIn[" + str(k) + "]"))
		
	if outputMatrix: connectAttrAttempt(nameStd.node.attr("outputMatrix"), outputMatrix)

	#return;MnsNameStd (multMatrix node)
	return nameStd

def mayaConstraint(sources = [], target = None, **kwargs):
	"""Create a new constraint node using the given inputs.
	"""

	if sources and not type(sources) is list: sources = [sources]
	if target and type(target) is list: target = target[0]
	sources = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = sources)
	target = mnsUtils.checkIfObjExistsAndSet(target)

	cnsType = kwargs.get("type", "parent") #arg; comment = side flag
	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", cnsType + "Constraint") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	maintainOffset = kwargs.get("maintainOffset", False) #arg; comment = Node's maintainOffset attribute
	skip = kwargs.get("skip", "none")
	skipRotate = kwargs.get("skipRotate", "none")

	nameStdA = MnsNameStd(side = side, body = body, alpha = alpha, id = id, type = mnsTypeDict[cnsType + "Constraint"])
	if not incrementAlpha : nameStdA.findNextIncrement()
	else : nameStdA.findNextAlphaIncrement()
	nodeName = nameStdA.name

	returnNode = None
	if sources and target:
		if cnsType == "parent": returnNode = pm.parentConstraint(sources, target, mo = maintainOffset, name = nodeName, skipRotate = skipRotate)
		if cnsType == "point": returnNode = pm.pointConstraint(sources, target, mo = maintainOffset, name = nodeName, sk = skip)
		if cnsType == "orient": returnNode = pm.orientConstraint(sources, target, mo = maintainOffset, name = nodeName, sk = skip)
		if cnsType == "scale": returnNode = pm.scaleConstraint(sources, target, mo = maintainOffset, name = nodeName, sk = skip)
		if cnsType == "aim": 
			aimVector = kwargs.get("aimVector", [0.0,1.0,0.0]) #arg;
			upVector = kwargs.get("upVector", [1.0,0.0,0.0]) #arg;
			worldUpType = kwargs.get("worldUpType", "object") #arg; optionBox = scene, object, objectrotation, vector, none
			worldUpObject = mnsUtils.checkIfObjExistsAndSet(kwargs.get("worldUpObject", None)) #arg;
			if worldUpObject:
				returnNode = pm.aimConstraint(sources, target, mo = maintainOffset, name = nodeName, aimVector = aimVector, upVector = upVector, worldUpType = worldUpType, worldUpObject = worldUpObject, sk = skip)
			else:
				returnNode = pm.aimConstraint(sources, target, mo = maintainOffset, name = nodeName, aimVector = aimVector, upVector = upVector, worldUpType = "scene", sk = skip)
		if cnsType == "poleVector":
			returnNode = pm.poleVectorConstraint(sources, target, name = nodeName)

	if returnNode: returnNode = mnsUtils.validateNameStd(returnNode)

	#return;MnsNameStd (constraint node)
	return returnNode

def clampNode(inputA = [], maxA = [], minA = [], output = [], **kwargs):
	"""Create a new clamp node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "clamp") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "clamp", incrementAlpha = incrementAlpha)

	asList = [inputA, maxA, minA, output]
	attrList = ["input", "max", "min", "output"]
	plugList = ["R", "G", "B"]
	for k in range(0, 3):
		if asList[k]:
			connect = False
			if not type(asList[k]) is list:
				if attrList[k] == "output": connect = connectSetAttempt(nameStd.node.attr(attrList[k]), asList[k], float)
				else: connect = connectSetAttempt(asList[k], nameStd.node.attr(attrList[k]), float)
			if not connect: 
				if not type(asList[k]) is list: asList[k] = [asList[k]]
				j = 0
				for plug in asList[k]:
					if plug or plug == 0 or plug == 0.0: 
						if attrList[k] == "output": connectSetAttempt(nameStd.node.attr(attrList[k] + plugList[j]), plug, float)
						else: connectSetAttempt(plug, nameStd.node.attr(attrList[k] + plugList[j]), float)
					j += 1

	#return;MnsNameStd (reverse node)
	return nameStd

def pmaNode(input1Ds = [], input2Ds = [], input3Ds = [], output1D = None, output2D = None, output3D = None, **kwargs):
	"""Create a new inverseMatrix node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "pma") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "plusMinusAverage", incrementAlpha = incrementAlpha)

	operation = kwargs.get("operation", 1) #arg; optionBox = noOperation, sum, subtract, avarage
	nameStd.node.operation.set(operation)

	if input1Ds: 
		for k in range(len(input1Ds)): connectAttrAttempt(input1Ds[k], nameStd.node.attr("input1D[" + str(k) + "]"))

	if input2Ds:
		k = 0
		for inputItem in input2Ds:
			connect = False
			if not type(inputItem) is list:
				connect = connectSetAttempt(inputItem, nameStd.node.attr("input2D[" + str(k) + "]"), float)
			if not connect: 
				if not type(inputItem) is list: inputItem = [inputItem]
				j = 0
				attrList = ["x","y"]
				for plug in inputItem:
					if plug or plug == 0 or plug == 0.0: 
						connectSetAttempt(plug, nameStd.node.attr("input2D[" + str(k) + "]" + attrList[j]), float)
					j += 1
			k += 1

	
	if input3Ds:
		k = 0
		for inputItem in input3Ds:
			connect = False
			if not type(inputItem) is list:
				connect = connectSetAttempt(inputItem, nameStd.node.attr("input3D[" + str(k) + "]"), float)
			if not connect: 
				if not type(inputItem) is list: inputItem = [inputItem]
				j = 0
				attrList = ["x","y","z"]
				for plug in inputItem:
					if plug or plug == 0 or plug == 0.0: 
						connectSetAttempt(plug, nameStd.node.attr("input3D[" + str(k) + "]" + attrList[j]), float)
					j += 1
			k += 1
	


	if output1D: connectAttrAttempt(nameStd.node.attr("output1D"), output1D)
	if output2D:
		connect = False
		if not type(inputItem) is list:
			connect = connectSetAttempt(nameStd.node.attr("output2D"), output2D, float)
		if not connect: 
			if not type(output2D) is list: output2D = [output2D]
			j = 0
			attrList = ["x","y"]
			for plug in output2D:
				if plug or plug == 0 or plug == 0.0: 
					connectSetAttempt(nameStd.node.attr("output2D" + attrList[j]), plug, float)
				j += 1

	if output3D:
		connect = False
		if not type(inputItem) is list:
			connect = connectSetAttempt(nameStd.node.attr("output3D"), output3D, float)
		if not connect: 
			if not type(output3D) is list: output2D = [output3D]
			j = 0
			attrList = ["x","y","z"]
			for plug in output3D:
				if plug or plug == 0 or plug == 0.0: 
					connectSetAttempt(nameStd.node.attr("output3D" + attrList[j]), plug, float)
				j += 1


	#return;MnsNameStd (plusMinusAverage node)
	return nameStd

def mnsDynamicPivotNode(**kwargs):
	mnsUtils.isPluginLoaded("mnsDynamicPivot")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "springCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	dynPivNode = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsDynamicPivot", incrementAlpha = incrementAlpha)
	
	distRateMultiplier = kwargs.get("distRateMultiplier", 1.0) #arg;
	dynPivNode.node.distRateMultiplier.set(distRateMultiplier)

	mapRotXTo = kwargs.get("mapRotXTo", 2) #arg; optionBox = X, Y, Z, -X, -Y, -Z, None; 
	mapRotYTo = kwargs.get("mapRotYTo", 6) #arg; optionBox = X, Y, Z, -X, -Y, -Z, None; 
	mapRotZTo = kwargs.get("mapRotZTo", 3) #arg; optionBox = X, Y, Z, -X, -Y, -Z, None; 
	dynPivNode.node.mapRotXTo.set(mapRotXTo)
	dynPivNode.node.mapRotYTo.set(mapRotYTo)
	dynPivNode.node.mapRotZTo.set(mapRotZTo)

	originWorldMatrix = kwargs.get("originWorldMatrix", None) #arg;
	if originWorldMatrix != None: connectAttrAttempt(originWorldMatrix, dynPivNode.node.attr("originWorldMatrix"))

	targetParentInverseMatrix = kwargs.get("targetParentInverseMatrix", None) #arg;
	if targetParentInverseMatrix != None: connectAttrAttempt(targetParentInverseMatrix, dynPivNode.node.attr("targetParentInverseMatrix"))

	#connect inputCurve
	inputCrv = mnsUtils.checkIfObjExistsAndSet(obj = kwargs.get("inputCurve", "")) #arg; comment = name of the curve object to connect as input curve into the node. Setting as nothing or an invalid name will result in nothing connected
	validS = 0
	if inputCrv:
		try:
			for shape in inputCrv.getShapes():
				if pm.objectType(shape, isType='nurbsCurve'): validS += 1
		except:
			pass
		if not validS: 
			suc = connectAttrAttempt(inputCrv, dynPivNode.node + ".inputCurve")
			if not suc:
				mnsLog.log("\'" + inputCrv._name + "\' Doesn't have any valid nurbsCurve shape, this will be ignored and will not connect", svr = 1)
		else: 
			if validS > 1: mnsLog.log("\'" + inputCrv._name + "\' has more then one valid nurbsCurve shapes, connecting to the first direct child.", svr = 1)
			pm.connectAttr(inputCrv.getShape() + ".worldSpace[0]", dynPivNode.node + ".inputCurve")

	rotate = kwargs.get("rotate", None) #arg; 

	if rotate:
		plugList = ["X", "Y", "Z"]
		connect = False
		if not type(rotate) is list:
			connect = connectSetAttempt(rotate, dynPivNode.node.attr("rotate"), float)
		if not connect: 
			if not type(rotate) is list: rotate = [rotate]
			j = 0
			for plug in rotate:
				if plug or plug == 0 or plug == 0.0: 
					connectSetAttempt(plug, dynPivNode.node.attr("rotate" + plugList[j]), float)
				j += 1

	rotatePivot = kwargs.get("rotatePivot", None) #arg;
	if rotatePivot != None: connectAttrAttempt(dynPivNode.node.attr("rotatePivot"), rotatePivot)


	#return;MnsNameStd (MnsDynamicPivot node)
	return dynPivNode

def blendColorsNode(color1 = None, color2 = None, blender = None, output = None, **kwargs):
	"""Create a new multiply devide node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "multDev") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	operation = kwargs.get("operation", 1) #arg; optionBox = noOperation, multiply, divide, power
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "blendColors", incrementAlpha = incrementAlpha)

	asList = [color1, color2, output]
	attrList = ["color1", "color2", "output"]
	plugList = ["R", "G", "B"]

	for k in range(0, 3):
		if asList[k]:
			connect = False
			if not type(asList[k]) is list:
				if attrList[k] == "output": connect = connectSetAttempt(nameStd.node.attr(attrList[k]), asList[k], float)
				else: connect = connectSetAttempt(asList[k], nameStd.node.attr(attrList[k]), float)
			if not connect: 
				if not type(asList[k]) is list: asList[k] = [asList[k]]
				j = 0
				for plug in asList[k]:
					if plug or plug == 0 or plug == 0.0: 
						if attrList[k] == "output": connectSetAttempt(nameStd.node.attr(attrList[k] + plugList[j]), plug, float)
						else: connectSetAttempt(plug, nameStd.node.attr(attrList[k] + plugList[j]), float)
					j += 1

	if blender:
		connectSetAttempt(blender, nameStd.node.blender, float)

	#return;MnsNameStd (MultiplyDevide node)
	return nameStd

def mnsSimpleSquashNode(**kwargs):
	mnsUtils.isPluginLoaded("mnsSimpleSquash")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "springCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	simpleSuqashNode = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsSimpleSquash", incrementAlpha = incrementAlpha)
	
	globalScale = kwargs.get("globalScale", 1.0) #arg;
	connectSetAttempt(globalScale, simpleSuqashNode.node.attr("globalScale"), float)

	squashFactor = kwargs.get("squashFactor", 1.0) #arg;
	connectSetAttempt(squashFactor, simpleSuqashNode.node.attr("squashFactor"), float)

	squashMin = kwargs.get("squashMin", 0.001) #arg;
	connectSetAttempt(squashMin, simpleSuqashNode.node.attr("squashMin"), float)

	squashMax = kwargs.get("squashMax", 10.0) #arg;
	connectSetAttempt(squashMax, simpleSuqashNode.node.attr("squashMax"), float)

	stretchFactor = kwargs.get("stretchFactor", 1.0) #arg;
	connectSetAttempt(stretchFactor, simpleSuqashNode.node.attr("stretchFactor"), float)

	stretchMin = kwargs.get("stretchMin", 0.001) #arg;
	connectSetAttempt(stretchMin, simpleSuqashNode.node.attr("stretchMin"), float)

	stretchMax = kwargs.get("stretchMax", 10.0) #arg;
	connectSetAttempt(stretchMax, simpleSuqashNode.node.attr("stretchMax"), float)

	squashRootWorldMatrix = kwargs.get("squashRootWorldMatrix", None) #arg;
	if squashRootWorldMatrix != None: connectAttrAttempt(squashRootWorldMatrix, simpleSuqashNode.node.attr("squashRootWorldMatrix"))

	handleWorldMatrix = kwargs.get("handleWorldMatrix", None) #arg;
	if handleWorldMatrix != None: connectAttrAttempt(handleWorldMatrix, simpleSuqashNode.node.attr("handleWorldMatrix"))

	scale = kwargs.get("scale", None) #arg;
	if scale:
		plugList = ["X", "Y", "Z"]
		connect = False
		if not type(scale) is list:
			connect = connectSetAttempt(simpleSuqashNode.node.attr("scale"), scale, float)
		if not connect: 
			if not type(scale) is list: scale = [scale]
			j = 0
			for plug in scale:
				if plug or plug == 0 or plug == 0.0: 
					connectSetAttempt(simpleSuqashNode.node.attr("scale" + plugList[j]), plug, float)
				j += 1

	#return;MnsNameStd (MnsDynamicPivot node)
	return simpleSuqashNode

def reverseCurveNode(inputCurve = None, outputCurve = None, **kwargs):
	if inputCurve:
		side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
		body = kwargs.get("body", "reverseCurve") #arg; comment = Node's name body.
		alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
		id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
		incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
		nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "reverseCurve", incrementAlpha = incrementAlpha)
		reverseCurveNode = nameStd.node

		connectAttrAttempt(inputCurve, reverseCurveNode.inputCurve)
		connectAttrAttempt(reverseCurveNode.outputCurve, outputCurve)

def mnsCurveZipNode(**kwargs):
	"""Creates an mnsPointOnCurve node based on specified parameters and outputs.
	A 'buildOutputs' parameter is defaulted to True to build output (of a choice of any mnsType)."""

	nodeType = kwargs.get("type", "mnsCurveZip") #arg; optionBox = mnsCurveZip, mnsCurveZipB

	mnsUtils.isPluginLoaded(nodeType)

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "pointsOnCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = nodeType, incrementAlpha = incrementAlpha)
	curveZipNode = nameStd.node

	inputCurveAtts = ["bindCurveA", "bindCurveB", "midCurve", "tweakCurveA", "tweakCurveABase", "tweakCurveB", "tweakCurveBBase"]
	for curveInput in inputCurveAtts:
		if curveZipNode.hasAttr(curveInput):
			curveAttr = kwargs.get(curveInput, None)
			connectAttrAttempt(curveAttr, curveZipNode.attr(curveInput))

	centerMatrix = kwargs.get("centerMatrix", None)
	connectAttrAttempt(centerMatrix, curveZipNode.centerMatrix)

	substeps = kwargs.get("substeps", 30) #arg; min=5;
	sampleMode = kwargs.get("sampleMode", 0) #arg; optionBox = parametric, uniform;
	buildMode = kwargs.get("buildMode", 0) #arg; optionBox = EPs, CVs;
	degree = kwargs.get("degree", 3) #arg; min=1; max = 5;
	upCurveOffset = kwargs.get("upCurveOffset", 1.0) #arg; min = -20; max = 20; comment = Node's offsetX attribute
	aroundCenter = kwargs.get("aroundCenter", True) #arg; 
	conformToMeetPoint = kwargs.get("conformToMeetPoint", True) #arg; 
	curveToConform = kwargs.get("curveToConform", 0) #arg; optionBox = curveA, curveB
	conformDistancethreshold = kwargs.get("conformDistancethreshold", 0.2) #arg; min = 0.001;
	midGenerateFrom = kwargs.get("midGenerateFrom", 0) #arg; optionBox = bindBases, tweakCurves, input

	curveZipNode.substeps.set(substeps)
	curveZipNode.offset.set(upCurveOffset)
	curveZipNode.degree.set(degree)
	curveZipNode.sampleMode.set(sampleMode)
	curveZipNode.buildMode.set(buildMode)
	curveZipNode.aroundCenter.set(aroundCenter)
	curveZipNode.conformToMeetPoint.set(conformToMeetPoint)
	curveZipNode.curveToConform.set(curveToConform)
	curveZipNode.conformDistancethreshold.set(conformDistancethreshold)
	try:
		curveZipNode.midGenerateFrom.set(midGenerateFrom)
	except: pass

	outCurveA = kwargs.get("outCurveA", None)
	connectAttrAttempt(curveZipNode.outCurveA, outCurveA)
	outCurveAOffset = kwargs.get("outCurveAOffset", None)
	connectAttrAttempt(curveZipNode.outCurveAOffset, outCurveAOffset)
	outCurveB = kwargs.get("outCurveB", None)
	connectAttrAttempt(curveZipNode.outCurveB, outCurveB)
	outCurveBOffset = kwargs.get("outCurveBOffset", None)
	connectAttrAttempt(curveZipNode.outCurveBOffset, outCurveBOffset)

	return nameStd

def setRangeNode(maxIn = [], minIn = [], oldMax = [], oldMin = [], value = [], outValue = [], **kwargs):
	"""Create a new setRange node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "setRange") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "setRange", incrementAlpha = incrementAlpha)


	attrNamesSeq = ["max", "min", "oldMax", "oldMin", "value", "outValue"]
	for k, inputArray in enumerate([maxIn, minIn, oldMax, oldMin, value]):
		attrName = attrNamesSeq[k]
		connect = False
		if not type(inputArray) is list:
			connect = connectSetAttempt(inputArray, nameStd.node.attr(attrName), float)
		if not connect: 
			if not type(inputArray) is list: inputArray = [inputArray]
			attrList = ["x","y","z"]
			for j, plug in enumerate(inputArray):
				if plug or plug == 0 or plug == 0.0: 
					connectSetAttempt(plug, nameStd.node.attr(attrName + attrList[j].upper()), float)

	if outValue:
		connect = False
		if not type(outValue) is list:
			connect = connectSetAttempt(nameStd.node.attr("outValue"), outValue, float)
		if not connect: 
			if not type(outValue) is list: outValue = [outValue]

			attrList = ["x","y","z"]
			for j, plug in enumerate(outValue):
				if plug or plug == 0 or plug == 0.0: 
					connectSetAttempt(nameStd.node.attr("outValue" + attrList[j].upper()), plug, float)

	#return;MnsNameStd (setRange node)
	return nameStd

def mnsClosestPointsOnMeshNode(**kwargs):
	"""Creates an mnsClosestPointsOnMesh node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsClosestPointsOnMesh")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "closestPointsOnMesh") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsClosestPointsOnMesh", incrementAlpha = incrementAlpha)
	
	inputMesh = mnsUtils.checkIfObjExistsAndSet(kwargs.get("inputMesh", None)) #arg;
	if inputMesh: 
		if not type(inputMesh) == pm.nodetypes.Mesh:
			if type(inputMesh) == pm.nodetypes.Transform:
				try: inputMesh = mnsMeshUtils.getShapeFromTransform(inputMesh)
				except: pass
	if inputMesh:
		if inputMesh.hasAttr("worldMesh"):
			connectAttrAttempt(inputMesh.attr("worldMesh[0]"), nameStd.node.attr("inMesh"))
		else:
			connectAttrAttempt(inputMesh.attr("worldSpace[0]"), nameStd.node.attr("inMesh"))

	inputTransforms = kwargs.get("inputTransforms", []) #arg;
	inputTransforms = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = inputTransforms)
	for k, transform in enumerate(inputTransforms):
		connectAttrAttempt(transform.attr("worldMatrix[0]"), nameStd.node.attr("inPosition[" + str(k) + "].matrix"))

	outputTransforms = kwargs.get("outputTransforms", []) #arg;
	outputTransforms = mnsUtils.objectArrayValidExistsCheckReturn(objectArray = outputTransforms)
	for k, transform in enumerate(outputTransforms):
		connectAttrAttempt(transform.attr("parentMatrix[0]"), nameStd.node.attr("inPosition[" + str(k) + "].targetParentMatrix"))
		connectAttrAttempt(nameStd.node.attr("outPosition[" + str(k) + "]"), transform.t)

	#return;dict ('node': Created node MnsNameStd)
	return {"node": nameStd}

def mnsSimpleRivetsNode(**kwargs):
	"""Creates an mnsClosestPointsOnMesh node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsSimpleRivets")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "simpleRivets") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsSimpleRivets", incrementAlpha = incrementAlpha)
	
	inputMesh = mnsUtils.checkIfObjExistsAndSet(kwargs.get("inputMesh", None)) #arg;
	inputMeshShape = inputMesh
	if inputMesh: 
		if not type(inputMesh) == pm.nodetypes.Mesh:
			if type(inputMesh) == pm.nodetypes.Transform:
				try: inputMeshShape = mnsMeshUtils.getShapeFromTransform(inputMesh)
				except: pass
	if inputMeshShape:
		connectAttrAttempt(inputMeshShape.attr("outMesh"), nameStd.node.attr("mesh"))
	if inputMesh:
		connectAttrAttempt(inputMesh.attr("worldMatrix[0]"), nameStd.node.attr("targetWorldMatrix"))

	mo = kwargs.get("mo", True)
	nameStd.node.maintainOffset.set(mo)

	#return;MnsNameStd
	return nameStd

def mnsLipZipNode(**kwargs):
	"""Creates an mnsLipZip node based on specified parameters and outputs.
	A 'buildOutputs' parameter is defaulted to True to build output (of a choice of any mnsType)."""
	mnsUtils.isPluginLoaded("mnsLipZip")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "pointsOnCurve") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsLipZip", incrementAlpha = incrementAlpha)
	curveZipNode = nameStd.node

	inputCurveAtts = ["bindCurveA", "bindCurveB", "midCurve", "tweakCurveA", "tweakCurveABase", "tweakCurveB", "tweakCurveBBase"]
	for curveInput in inputCurveAtts:
		if curveZipNode.hasAttr(curveInput):
			curveAttr = kwargs.get(curveInput, None)
			connectAttrAttempt(curveAttr, curveZipNode.attr(curveInput))

	centerMatrix = kwargs.get("centerMatrix", None)
	connectAttrAttempt(centerMatrix, curveZipNode.centerMatrix)

	substeps = kwargs.get("substeps", 30) #arg; min=5;
	sampleMode = kwargs.get("sampleMode", 0) #arg; optionBox = parametric, uniform;
	buildMode = kwargs.get("buildMode", 0) #arg; optionBox = EPs, CVs;
	degree = kwargs.get("degree", 3) #arg; min=1; max = 5;
	upCurveOffset = kwargs.get("upCurveOffset", 1.0) #arg; min = -20; max = 20; comment = Node's offsetX attribute
	aroundCenter = kwargs.get("aroundCenter", False) #arg; 
	conformToMeetPoint = kwargs.get("conformToMeetPoint", False) #arg; 
	curveToConform = kwargs.get("curveToConform", 0) #arg; optionBox = curveA, curveB
	conformDistancethreshold = kwargs.get("conformDistancethreshold", 0.2) #arg; min = 0.001;
	midGenerateFrom = kwargs.get("midGenerateFrom", 0) #arg; optionBox = bindBases, tweakCurves, input

	curveZipNode.substeps.set(substeps)
	curveZipNode.offset.set(upCurveOffset)
	curveZipNode.degree.set(degree)
	curveZipNode.sampleMode.set(sampleMode)
	curveZipNode.buildMode.set(buildMode)
	curveZipNode.aroundCenter.set(aroundCenter)
	curveZipNode.conformToMeetPoint.set(conformToMeetPoint)
	curveZipNode.curveToConform.set(curveToConform)
	curveZipNode.conformDistancethreshold.set(conformDistancethreshold)
	try:
		curveZipNode.midGenerateFrom.set(midGenerateFrom)
	except: pass

	outCurveA = kwargs.get("outCurveA", None)
	connectAttrAttempt(curveZipNode.outCurveA, outCurveA)
	outCurveAOffset = kwargs.get("outCurveAOffset", None)
	connectAttrAttempt(curveZipNode.outCurveAOffset, outCurveAOffset)
	outCurveB = kwargs.get("outCurveB", None)
	connectAttrAttempt(curveZipNode.outCurveB, outCurveB)
	outCurveBOffset = kwargs.get("outCurveBOffset", None)
	connectAttrAttempt(curveZipNode.outCurveBOffset, outCurveBOffset)

	return nameStd

def distBetweenNode(inMatrix1 = None, inMatrix2 = None, distance = None, **kwargs):
	"""Create a new distanceBetween node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "distBetween") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	operation = kwargs.get("operation", 0) #arg; optionBox = equal, notEqual, greaterThan, greaterOrEqual, lessThan, LessOrEqual
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "distanceBetween", incrementAlpha = incrementAlpha)

	connectAttrAttempt(inMatrix1, nameStd.node.attr("inMatrix1"))
	connectAttrAttempt(inMatrix2, nameStd.node.attr("inMatrix2"))
	connectAttrAttempt(nameStd.node.attr("distance"), distance)

	#return;MnsNameStd (distance between node)
	return nameStd

def mnsRemapFloatArrayNode(**kwargs):
	"""Create a new mnsRemapFlatArray node using the given inputs.
	"""

	mnsUtils.isPluginLoaded("mnsRemapFloatArray")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "remapFloatArray") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	operation = kwargs.get("operation", 0) #arg; optionBox = equal, notEqual, greaterThan, greaterOrEqual, lessThan, LessOrEqual
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsRemapFloatArray", incrementAlpha = incrementAlpha)

	value = kwargs.get("value", "") #arg;
	if value: connectSetAttempt(value, nameStd.node.attr("value"), float)
	outputCount = kwargs.get("outputCount", 1) #arg;
	if outputCount: connectSetAttempt(outputCount, nameStd.node.attr("outputCount"), float)
	angleOutputAsDegrees = kwargs.get("angleOutputAsDegrees", False) #arg;
	if angleOutputAsDegrees: connectSetAttempt(angleOutputAsDegrees, nameStd.node.attr("angleOutputAsDegrees"), bool)
	remapToRnage = kwargs.get("remapToRnage", False) #arg;
	if remapToRnage: connectSetAttempt(remapToRnage, nameStd.node.attr("remapToRnage"), bool)
	minimum = kwargs.get("min", 0.0) #arg;
	if minimum: connectSetAttempt(minimum, nameStd.node.attr("min"), float)
	maximum = kwargs.get("max", 1.0) #arg;
	if maximum: connectSetAttempt(maximum, nameStd.node.attr("max"), float)
	oldMin = kwargs.get("oldMin", 0.0) #arg;
	if oldMin: connectSetAttempt(oldMin, nameStd.node.attr("oldMin"), float)
	oldMax = kwargs.get("oldMax", 1.0) #arg;
	if oldMax: connectSetAttempt(oldMax, nameStd.node.attr("oldMax"), float)

	outValues = kwargs.get("outValues", []) #arg;
	if outValues: 
		for k, value in enumerate(outValues):
			connectAttrAttempt(nameStd.node.attr("outValue[" + str(k) + "]"), value)

	#return;MnsNameStd (mnsRemapFloatArray node)
	return nameStd

def mnsCurveTweakNode(**kwargs):
	"""Creates an mnsLipZip node based on specified parameters and outputs.
	A 'buildOutputs' parameter is defaulted to True to build output (of a choice of any mnsType)."""
	mnsUtils.isPluginLoaded("mnsCurveTweak")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "curveTweak") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsCurveTweak", incrementAlpha = incrementAlpha)

	inputCurveAtts = ["inputCurve", "inputBaseCurve", "inputTweakCurve"]
	for curveInput in inputCurveAtts:
		if nameStd.node.hasAttr(curveInput):
			curveAttr = kwargs.get(curveInput, None)
			connectAttrAttempt(curveAttr, nameStd.node.attr(curveInput))

	buildOffsetCurve = kwargs.get("buildOffsetCurve", False) #arg; 
	nameStd.node.buildOffsetCurve.set(buildOffsetCurve)
	tweakOffset = kwargs.get("tweakOffset", False) #arg;
	nameStd.node.tweakOffset.set(tweakOffset)
	offset = kwargs.get("offset", 0.0) #arg;
	nameStd.node.offset.set(offset)

	offsetBaseMatrix = kwargs.get("offsetBaseMatrix", None) #arg; 
	connectAttrAttempt(offsetBaseMatrix, nameStd.node.offsetBaseMatrix)

	outCurve = kwargs.get("outCurve", None)
	connectAttrAttempt(nameStd.node.outCurve, outCurve)

	return nameStd

def mnsAutoWheelDriveNode(**kwargs):
	"""Creates an mnsAutoWheelDrive node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsAutoWheelDrive")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "autoWheelDrive") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsAutoWheelDrive", incrementAlpha = incrementAlpha)

	driverWorldMatrix = kwargs.get("driverWorldMatrix", None)
	connectAttrAttempt(driverWorldMatrix, nameStd.node.driverWorldMatrix)

	startDirectionWorldMatrix = kwargs.get("startDirectionWorldMatrix", None)
	connectAttrAttempt(startDirectionWorldMatrix, nameStd.node.startDirectionWorldMatrix)

	wheelDiameter = kwargs.get("wheelDiameter", 10.0) #arg;
	nameStd.node.wheelDiameter.set(wheelDiameter)
	speedMultiplier = kwargs.get("speedMultiplier", 1.0) #arg;
	nameStd.node.speedMultiplier.set(speedMultiplier)
	outRotation = kwargs.get("outRotation", None) #arg;
	connectAttrAttempt(nameStd.node.outRotation, outRotation)

	connectTime = kwargs.get("connectTime", True) #arg;
	if connectTime: pm.connectAttr("time1.outTime", nameStd.node.time)

	return nameStd

def mnsTransformSpringNode(**kwargs):
	"""Creates an mnsAutoWheelDrive node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsTransformSpring")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "transformSpring") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsTransformSpring", incrementAlpha = incrementAlpha)

	inputWorldMatrix = kwargs.get("inputWorldMatrix", None)
	connectAttrAttempt(inputWorldMatrix, nameStd.node.inputWorldMatrix)

	targetParentInverseMatrix = kwargs.get("targetParentInverseMatrix", None)
	connectAttrAttempt(targetParentInverseMatrix, nameStd.node.targetParentInverseMatrix)

	strength = kwargs.get("strength", 1.0) #arg;
	nameStd.node.strength.set(strength)
	damping = kwargs.get("damping", 0.5) #arg;
	nameStd.node.damping.set(damping)
	stiffness = kwargs.get("stiffness", 0.5) #arg;
	nameStd.node.stiffness.set(stiffness)

	outTranslate = kwargs.get("outTranslate", None) #arg;
	connectAttrAttempt(nameStd.node.translate, outTranslate)

	connectTime = kwargs.get("connectTime", True) #arg;
	if connectTime: pm.connectAttr("time1.outTime", nameStd.node.time)

	return nameStd

def mnsSphereVectorPushNode(**kwargs):
	"""Creates an mnsSphereVectorPush node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsSphereVectorPush")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "sphereVectorPush") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	
	inputMesh = mnsUtils.checkIfObjExistsAndSet(kwargs.get("inputMesh", None)) #arg;
	if inputMesh: 
		if type(inputMesh) == pm.nodetypes.Mesh:
			inputMesh = inputMesh.getParent()

		if inputMesh.getShapes() and type(inputMesh.getShape()) == pm.nodetypes.Mesh:
			nameStd = MnsNameStd(side = side, body = body, alpha = alpha, id = id, type = mnsTypeDict["mnsSphereVectorPush"])
			if not incrementAlpha : nameStd.findNextIncrement()
			else : nameStd.findNextAlphaIncrement()

			deformerName = nameStd.name
			mnsSvpDeformer = pm.deformer(inputMesh, type = "mnsSphereVectorPush", name = deformerName)

			if mnsSvpDeformer:
				mnsSvpDeformer = mnsSvpDeformer[0]
				colliderTransform = mnsUtils.checkIfObjExistsAndSet(kwargs.get("colliderTransform", None)) #arg;
				if colliderTransform:
					colliderTransform.worldMatrix[0] >> mnsSvpDeformer.collider[0].collideMatrix

				collideRadius = kwargs.get("collideRadius", 1.0) #arg; min = 0.0;
				collideMethod = kwargs.get("collideMethod", 1) #arg; optionBox = matrix,position;
				thicknessCollide = kwargs.get("thicknessCollide", False) #arg;
				thicknessThreshold = kwargs.get("thicknessThreshold", 0.0) #arg; min = 0.0;
				
				attrHost = mnsUtils.checkIfObjExistsAndSet(kwargs.get("attrHost", None)) #arg;
				if attrHost:
					mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "sphereVectorPush", replace = True)

					collideRadiusAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = collideRadius, name = "collideRadius", replace = True, min = 0.0)[0]
					collideRadiusAttr >> mnsSvpDeformer.collider[0].radius

					collideMethodAttr = mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["matrix", "position"], name = "collideMethod", enumDefault = collideMethod, replace = True)[0]
					collideMethodAttr >> mnsSvpDeformer.collider[0].collideMethod

					thicknessCollideAttr = mnsUtils.addAttrToObj([attrHost], type = "bool", value = thicknessCollide, name = "thicknessCollide", replace = True)[0]
					thicknessCollideAttr >> mnsSvpDeformer.collider[0].thicknessCollide

					thicknessThresholdAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = thicknessThreshold, name = "thicknessThreshold", replace = True, min = 0.0)[0]
					thicknessThresholdAttr >> mnsSvpDeformer.collider[0].thicknessThreshold
				else:
					mnsSvpDeformer.collider[0].radius.set(collideRadius)
					mnsSvpDeformer.collider[0].collideMethod.set(collideMethod)
					mnsSvpDeformer.collider[0].thicknessCollide.set(thicknessCollide)
					mnsSvpDeformer.collider[0].thicknessThreshold.set(thicknessThreshold)

				#return;MnsNameStd
				return nameStd

def angleBetweenNode(**kwargs):
	"""Creates an angleBetween node based on specified parameters and outputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "angleBetween") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "angleBetween", incrementAlpha = incrementAlpha)

	vector1 = kwargs.get("vector1", None) #arg;
	vector2 = kwargs.get("vector2", None) #arg;

	asList = [vector1, vector2]
	attrList = ["vector1", "vector2"]
	plugList = ["X", "Y", "Z"]
	for k in range(0, 2):
		if asList[k]:
			connect = False
			if not type(asList[k]) is list:
				connect = connectSetAttempt(asList[k], nameStd.node.attr(attrList[k]), float)
			if not connect: 
				if not type(asList[k]) is list: asList[k] = [asList[k]]
				j = 0
				for plug in asList[k]:
					if plug or plug == 0 or plug == 0.0: 
						connectSetAttempt(plug, nameStd.node.attr(attrList[k] + plugList[j]), float)
					j += 1

	angle = kwargs.get("angle", None) #arg;
	connectAttrAttempt(nameStd.node.axisAngle.angle, angle)

	return nameStd

def mnsSphereRollNode(**kwargs):
	"""Creates an mnsSphereRoll node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsSphereRoll")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "sphereRoll") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsSphereRoll", incrementAlpha = incrementAlpha)

	driverWorldMatrix = kwargs.get("driverWorldMatrix", None)
	connectAttrAttempt(driverWorldMatrix, nameStd.node.driverWorldMatrix)

	upVectorWorldMatrix = kwargs.get("upVectorWorldMatrix", None)
	connectAttrAttempt(upVectorWorldMatrix, nameStd.node.upVectorWorldMatrix)

	sphereRadius = kwargs.get("sphereRadius", 10.0) #arg;
	nameStd.node.sphereRadius.set(sphereRadius)
	speedMultiplier = kwargs.get("speedMultiplier", 1.0) #arg;
	nameStd.node.speedMultiplier.set(speedMultiplier)

	outRotation = kwargs.get("outRotation", None) #arg;
	plugList = ["X", "Y", "Z"]

	connect = False
	if not type(outRotation) is list:
		connect = connectSetAttempt(nameStd.node.attr("outRotation"), outRotation, float)
	if not connect: 
		if not type(outRotation) is list: outRotation = [outRotation]
		j = 0
		for plug in outRotation:
			if plug or plug == 0 or plug == 0.0: 
				connectSetAttempt(nameStd.node.attr("outRotation" + plugList[j]), plug, float)
			j += 1

	connectTime = kwargs.get("connectTime", True) #arg;
	if connectTime: pm.connectAttr("time1.outTime", nameStd.node.time)

	return nameStd

def mnsVolumeJointNode(**kwargs):
	"""Creates an mnsClosestPointsOnMesh node based on specified parameters and outputs.
	"""
	mnsUtils.isPluginLoaded("mnsVolumeJoint")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "volumeJoint") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsVolumeJoint", incrementAlpha = incrementAlpha)
	
	parentJoint = mnsUtils.checkIfObjExistsAndSet(kwargs.get("parentJoint", None)) #arg;
	childJoint = mnsUtils.checkIfObjExistsAndSet(kwargs.get("childJoint", None)) #arg;

	for k, jointNode in enumerate([parentJoint, childJoint]):
		if jointNode: 
			if k == 0: 
				connectAttrAttempt(jointNode.attr("worldMatrix[0]"), nameStd.node.attr("parentJointWorldMatrix"))
			else:
				connectAttrAttempt(childJoint.attr("worldMatrix[0]"), nameStd.node.attr("childJointWorldMatrix"))
				try:
					connectAttrAttempt(childJoint.attr("worldMatrix[0]"), nameStd.node.attr("childJointRestWorldMatrix"))
					nameStd.node.attr("childJointRestWorldMatrix").disconnect()
				except:
					pass

	#return;MnsNameStd
	return nameStd

def quatSlerpNode(inputQuatA = None, inputQuatB = None, outputQuat = None, **kwargs):
	"""Create a new quatSlerp node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "quatSlerp") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "quatSlerp", incrementAlpha = incrementAlpha)

	if inputQuatA: connectAttrAttempt(inputQuatA, nameStd.node.attr("input1Quat"))
	if inputQuatB: connectAttrAttempt(inputQuatB, nameStd.node.attr("input2Quat"))
	if outputQuat: connectAttrAttempt(nameStd.node.attr("outputQuat"), outputQuat)

	#return;MnsNameStd (quatSlerp node)
	return nameStd

def quatToEulerNode(inputQuat = None, outputRotate = None, **kwargs):
	"""Create a new quatToEuler node using the given inputs.
	"""

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "quatToEuler") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg; comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "quatToEuler", incrementAlpha = incrementAlpha)

	if inputQuat: connectAttrAttempt(inputQuat, nameStd.node.attr("inputQuat"))
	if outputRotate: connectAttrAttempt(nameStd.node.attr("outputRotate"), outputRotate)

	#return;MnsNameStd (quatSlerp node)
	return nameStd

def mnsQuatBlendNode(**kwargs):
	mnsUtils.isPluginLoaded("mnsQuaternionBlend")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "quaternionBlend") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsQuaternionBlend", incrementAlpha = incrementAlpha)

	inMatrix1 = kwargs.get("inMatrix1", None)
	connectAttrAttempt(inMatrix1, nameStd.node.inMatrix1)

	inMatrix2 = kwargs.get("inMatrix2", None)
	connectAttrAttempt(inMatrix2, nameStd.node.inMatrix2)

	outRotate = kwargs.get("outRotate", None)
	connectAttrAttempt(nameStd.node.rotate, outRotate)

	#return;MnsNameStd (quatBlend node)
	return nameStd

def mnsPoseBlendNode(**kwargs):
	mnsUtils.isPluginLoaded("mnsPoseBlend")

	side = mnsSidesDict[kwargs.get("side", "center")] #arg; comment = side flag
	body = kwargs.get("body", "poseBlend") #arg; comment = Node's name body.
	alpha = kwargs.get("alpha", "A") #arg;  comment = Node's Alpha id
	id = kwargs.get("id", 1) #arg; min = 1; comment = Node's ID
	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = Search new node name incrementing Alpha instead of the id if True
	nameStd = mnsUtils.createNodeReturnNameStd(side = side, body = body, alpha = alpha, id = id, buildType = "mnsPoseBlend", incrementAlpha = incrementAlpha)
	
	#return;MnsNameStd (quatBlend node)
	return nameStd

def dlNodesConnect(sourceAttr, targetNode, targetAttrName):
	if sourceAttr and targetNode and targetAttrName:
		if targetNode.hasAttr(targetAttrName):
			sourceAttr >> targetNode.attr(targetAttrName)
		else:
			targetAttrIdx = targetAttrName.split("input")[-1]
			if targetAttrIdx == "1": targetAttrIdx = "0"
			elif targetAttrIdx == "2": targetAttrIdx = "1"
			
			targetAttrName = "input[" + targetAttrIdx + "]"
			if targetNode.hasAttr(targetAttrName):
				sourceAttr >> targetNode.attr(targetAttrName)