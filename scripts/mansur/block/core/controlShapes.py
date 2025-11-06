"""=== Author: Assaf Ben Zur ===
Core control shapes creation function assembly.
A main CtrlCreate function calls a veriaty of pre-defined shape creation, then handles them"""

#global dependencies


from maya import cmds
import pymel.core as pm

import os

#mns dependencies
from ...core.prefixSuffix import *
from ...core import utility as mnsUtils

def ctrlCreate(**kwargs):
	"""Main creation function.
	This function takes user defined parameters and creates a ctrl transform node following the mns naming convention.
	Based on the choice passed in, a shape node will be created with the shape selected, and will be parented under the transform ceated.
	Then a color selected will be assigned to it.
	The ctrl can be set to be created along all axes and in every color.
	The default color is white when used as standalone, and based on the rig's global color coding defined- based on the side flag."""

	side, body, alpha, id = "center", "control", "A", 1
	nameReference = mnsUtils.validateNameStd(kwargs.get("nameReference", None)) #arg
	if nameReference: side, body, alpha, id = nameReference.side, nameReference.body, nameReference.alpha, nameReference.id 

	side = mnsSidesDict[kwargs.get("side", side)] #arg; comment = side flag;
	
	body = kwargs.get("body", body) #arg; comment = Node's name body
	alpha = kwargs.get("alpha", alpha) #arg; comment = Node's Alpha id 
	id = kwargs.get("id", id) #arg; min = 1; comment = Node's id
	isFacial = kwargs.get("isFacial", False) #arg;

	bodySuffix = kwargs.get("bodySuffix", "") #arg;
	body += bodySuffix

	incrementAlpha = kwargs.get("incrementAlpha", False) #arg; comment = In case of a 'free' creation, if True will name the node to the first possible name- searching for new Alpha instead of the ID
	ctrlType = kwargs.get("ctrlType", "ctrl") #arg; optionBox = ctrl, techCtrl, guideCtrl, guideRootCtrl, pickerLayoutCtrl
	createBlkClassID = kwargs.get("createBlkClassID", True) #arg;
	createBlkCtrlTypeID = kwargs.get("createBlkCtrlTypeID", True) #arg; 
	blkCtrlTypeID = kwargs.get("blkCtrlTypeID", 0) #arg; optionBox = primary, secondary, tertiary, gimble, pivot
	customParentTransform = kwargs.get("customParentTransform", "") #arg; 
	skipColor = kwargs.get("skipColor", False) #arg; 
	createOffsetGrp = kwargs.get("createOffsetGrp", False) #arg; 
	createSpaceSwitchGroup = kwargs.get("createSpaceSwitchGroup", False) #arg; 
	symmetryType = kwargs.get("symmetryType", 0) #arg; 
	doMirror = kwargs.get("doMirror", False) #arg; 
	forceMirrorGrp = kwargs.get("forceMirrorGrp", False) #arg; 
	parentNode = kwargs.get("parentNode", None) #arg;
	chennelControl = kwargs.get("chennelControl", None) #arg;

	nameStd = None
	if not customParentTransform: 
		nameStd = mnsUtils.createNodeReturnNameStd(parentNode = parentNode, side = side, body = body, alpha = alpha, id = id, buildType = ctrlType, incrementAlpha = incrementAlpha, createBlkClassID = createBlkClassID, createBlkCtrlTypeID= createBlkCtrlTypeID, blkCtrlTypeID = blkCtrlTypeID)
		nameStd.node.rotateOrder.setKeyable(True)
	
	ctrlShape = kwargs.get("controlShape", "circle") #arg; comment = Control's NURBS shape	
	scale = kwargs.get("scale", 1.0) #arg; comment = Ctrl scale. Relative to global settings.
	color = kwargs.get("color", (1.0,1.0,1.0)) #arg; comment = Shape's color
	alongAxis = kwargs.get("alongAxis", 1) #arg; optionBox = X, Y, Z, -X, -Y, -Z; comment = Along which axis to create the shape
	matchTransform = kwargs.get("matchTransform", "") #arg; comment = if not empty, look for a node within the scene matching the string specefied. If found, match it's transforms. 
	freezeScale = kwargs.get("freezeScale", False) #arg;
	matchScale = kwargs.get("matchScale", False) #arg;
	matchPos = kwargs.get("matchPosition", "") #arg; comment = if not empty, look for a node within the scene matching the string specefied. If found, match it's position. 
	matchOrient = kwargs.get("matchOrientation", "") #arg; comment = if not empty, look for a node within the scene matching the string specefied. If found, match it's Orientation. 
	sections = kwargs.get("sections", 1) #arg; comment = Aplicable only for circle creation

	shapeRet = None
	if ctrlShape == "circle": shapeRet = circleShapeCreate(sections = sections)
	elif ctrlShape == "dial": shapeRet = dialShapeCreate()
	elif ctrlShape == "dialRound": shapeRet = dialRoundShapeCreate()
	elif ctrlShape == "dialSquare": shapeRet = dialSquareShapeCreate()
	elif ctrlShape == "pinchedCircle": shapeRet = pinchedCircleShapeCreate()
	elif ctrlShape == "bubblePin": shapeRet = bubblePinShapeCreate()
	elif ctrlShape == "teardrop": shapeRet = teardropShapeCreate()
	elif ctrlShape == "square": shapeRet = squareShapeCreate()
	elif ctrlShape == "squareRound": shapeRet = squareRoundShapeCreate()
	elif ctrlShape == "arrowSquare": shapeRet = arrowSquareShapeCreate()
	elif ctrlShape == "arrowDodecagon": shapeRet = arrowDodecagonShapeCreate()
	elif ctrlShape == "curvedFourArrow": shapeRet = curvedFourArrowShapeCreate()
	elif ctrlShape == "fourArrow": shapeRet = fourArrowShapeCreate()
	elif ctrlShape == "dodecagon": shapeRet = dodecagonShapeCreate()
	elif ctrlShape == "triangle": shapeRet = triangleShapeCreate()
	elif ctrlShape == "flatDiamond": shapeRet = flatDiamondShapeCreate()
	elif ctrlShape == "flatDiamondRoot": shapeRet = flatDiamondRootShapeCreate()
	elif ctrlShape == "hexagon": shapeRet = hexagonShapeCreate()
	elif ctrlShape == "octagon": shapeRet = octagonShapeCreate()
	elif ctrlShape == "plus": shapeRet = plusShapeCreate()
	elif ctrlShape == "cross": shapeRet = crossShapeCreate()
	elif ctrlShape == "diamond": shapeRet = diamondShapeCreate()
	elif ctrlShape == "pick": shapeRet = pickShapeCreate()
	elif ctrlShape == "cube": shapeRet = cubeShapeCreate()
	elif ctrlShape == "lightSphere": shapeRet = lightSphereShapeCreate()
	elif ctrlShape == "sphere": shapeRet = sphereShapeCreate()
	elif ctrlShape == "pyramid": shapeRet = pyramidShapeCreate()
	elif ctrlShape == "arrow": shapeRet = arrowShapeCreate()
	elif ctrlShape == "doubleArrow": shapeRet = doubleArrowShapeCreate()
	elif ctrlShape == "tripleArrow": shapeRet = tripleArrowShapeCreate()
	elif ctrlShape == "cone": shapeRet = coneShapeCreate()
	elif ctrlShape == "lightPin": shapeRet = pinShapeCreate(light = True)
	elif ctrlShape == "pin": shapeRet = pinShapeCreate()
	elif ctrlShape == "pointArrow": shapeRet = pointArrowShapeCreate()
	elif ctrlShape == "cylinder": shapeRet = cylinderShapeCreate()
	elif ctrlShape == "directionCircle": shapeRet = directionCircle()
	elif ctrlShape == "directionDiamond": shapeRet = directionDiamond()
	elif ctrlShape == "directionCube": shapeRet = directionCubeShape()
	elif ctrlShape == "directionSphere": shapeRet = directionSphereShape()
	elif ctrlShape == "puppetRoot": shapeRet = puppetRootShapeCreate()
	elif ctrlShape == "guidesRoot": shapeRet = guidesRootShape()
	elif ctrlShape == "squareWithDividers": shapeRet = squareWithMidDividersShapeCreate()
	elif "txtCtrlShp_" in ctrlShape:
		textShapeValue = ctrlShape.split("txtCtrlShp_")[-1]
		shapeRet = textShapeCreate(textShapeValue)

	pm.xform(shapeRet, ws = 1, a = 1, rp = (0,0,0), sp = (0,0,0))

	#set the scale
	shapeRet.sx.set(scale)
	shapeRet.sy.set(scale)
	shapeRet.sz.set(scale)

	#set axis direction
	if alongAxis is 0: shapeRet.rz.set(-90)
	if alongAxis is 3: shapeRet.rz.set(90)
	if alongAxis is 2: shapeRet.rx.set(90)
	if alongAxis is 5: shapeRet.rx.set(-90)
	if alongAxis is 4: shapeRet.rx.set(180)

	pm.makeIdentity(shapeRet, apply = 1)

	#parent shape under control
	if customParentTransform:
		customParentTransform = mnsUtils.checkIfObjExistsAndSet(obj = customParentTransform)
		if customParentTransform:
			pm.parent(shapeRet.getShapes(), customParentTransform, r = 1, shape = 1)
			pm.delete(shapeRet)
			if not skipColor: mnsUtils.setCtrlColorRGB([customParentTransform], color)
			mnsUtils.fixShapesName([customParentTransform])
	else:
		pm.delete(nameStd.node.getShapes())
		pm.parent(shapeRet.getShapes(), nameStd.node, r = 1, shape = 1)
		pm.delete(shapeRet)
		if not skipColor: mnsUtils.setCtrlColorRGB([nameStd], color)
		mnsUtils.fixShapesName([nameStd])

		#match transforms
		matched = False
		if matchTransform:
			transfrom = mnsUtils.checkIfObjExistsAndSet(obj = matchTransform)
			if transfrom:
				if freezeScale:
					orientLoc = pm.spaceLocator()
					pm.parent(orientLoc, transfrom.getParent())
					pm.matchTransform(orientLoc, transfrom)
					pm.parent(orientLoc, w = True)
					pm.makeIdentity(orientLoc, a = True, t = False, r = False, s = True)
					pm.delete(pm.parentConstraint(orientLoc, nameStd.node))
					pm.delete(orientLoc)
				else:
					pm.delete(pm.parentConstraint(transfrom, nameStd.node))
					if matchScale:
						pm.delete(pm.scaleConstraint(transfrom, nameStd.node))

				matched = True
		if not matched and matchPos != "":
			transfrom = mnsUtils.checkIfObjExistsAndSet(obj = matchPos)
			if transfrom:
				pm.delete(pm.pointConstraint(transfrom, nameStd.node))
		if not matched and matchOrient != "":
			transfrom = mnsUtils.checkIfObjExistsAndSet(obj = matchOrient)
			if transfrom:
				pm.delete(pm.orientConstraint(transfrom, nameStd.node))

	pm.select(d=1)

	actionNameStd = nameStd

	if createOffsetGrp: actionNameStd = mnsUtils.createOffsetGroup(actionNameStd)
	if createSpaceSwitchGroup: 
		actionNameStd = mnsUtils.createOffsetGroup(actionNameStd, type = "spaceSwitchGrp")
		mnsUtils.addAttrToObj([nameStd.node], type = "bool", value = True, name = "spaceSwitchControl", locked = True, keyable = False, cb = False)

	if (side == "r" or forceMirrorGrp) and doMirror:
		createMirrorGroup(nameStd, symmetryType)

	if chennelControl: mnsUtils.applyChennelControlAttributesToTransform(nameStd.node, chennelControl)	
	mnsUtils.addAttrToObj([nameStd.node], type = "bool", value = isFacial, name = "isFacial", locked = True, keyable = False, cb = False)

	offsetRigMaster = mnsUtils.validateNameStd(kwargs.get("offsetRigMaster", None)) #arg; comment = If passed in, an attribute connecting the master joint to the control will be created.
	offsetRigSlaveIsParent = kwargs.get("offsetRigSlaveIsParent", False)

	createOffsetRigMasterAttrForTransform(nameStd, offsetRigMaster = offsetRigMaster, offsetRigSlaveIsParent = offsetRigSlaveIsParent)

	if "txtCtrlShp_" in ctrlShape:
		mnsUtils.addAttrToObj([nameStd.node], type = "bool", value = True, name = "isTextCtrl", locked = True, keyable = False, cb = False)
	
	#return;MnsNameStd (MnsNameStd class instance containing all info for the new node created)
	return nameStd

def createMirrorGroup(nameStd, symmetryType = 0):
	mirGrp = mnsUtils.createOffsetGroup(nameStd, type = "mirrorScaleGroup")

	if symmetryType == 0 or symmetryType == 8: pass
	if symmetryType == 1: mirGrp.node.rx.set(mirGrp.node.rx.get() + 180)
	elif symmetryType == 2: mirGrp.node.ry.set(mirGrp.node.ry.get() + 180)
	elif symmetryType == 3: mirGrp.node.rz.set(mirGrp.node.rz.get() + 180)
	elif symmetryType == 4: 
		mirGrp.node.rx.set(mirGrp.node.rx.get() + 180)
		mirGrp.node.ry.set(mirGrp.node.ry.get() + 180)
	elif symmetryType == 5: 
		mirGrp.node.rx.set(mirGrp.node.rx.get() + 180)
		mirGrp.node.rz.set(mirGrp.node.rz.get() + 180)
	elif symmetryType == 6: 
		mirGrp.node.ry.set(mirGrp.node.ry.get() + 180)
		mirGrp.node.rz.set(mirGrp.node.rz.get() + 180)
	elif symmetryType == 7: 
		mirGrp.node.ry.set(mirGrp.node.rx.get() + 180)
		mirGrp.node.ry.set(mirGrp.node.ry.get() + 180)
		mirGrp.node.rz.set(mirGrp.node.rz.get() + 180)

	if symmetryType != 8:
		mirGrp.node.sx.set(mirGrp.node.sx.get() * -1)
		mirGrp.node.sy.set(mirGrp.node.sy.get() * -1)
		mirGrp.node.sz.set(mirGrp.node.sz.get() * -1)
	return mirGrp

def createOffsetRigMasterAttrForTransform(ctrl = None, **kwargs):
	ctrl = mnsUtils.validateNameStd(ctrl)
	if ctrl:
		offsetRigMaster = mnsUtils.validateNameStd(kwargs.get("offsetRigMaster", None)) #arg; comment = If passed in, an attribute connecting the master joint to the control will be created.
		if offsetRigMaster:
			if offsetRigMaster.suffix == mnsPS_rJnt or offsetRigMaster.suffix == mnsPS_jnt:
				mnsUtils.addAttrToObj([ctrl.node], type = "message", value = offsetRigMaster.node, name = "offsetRigMaster", locked = True, keyable = False, cb = False)

				offsetRigSlaveIsParent = kwargs.get("offsetRigSlaveIsParent", False)
				if offsetRigSlaveIsParent:
					mnsUtils.addAttrToObj([ctrl.node], type = "bool", value = offsetRigSlaveIsParent, name = "offsetRigSlaveIsParent", locked = True, keyable = False, cb = False)

def createRemoteControlStyleCtrl(**kwargs):
	"""creates a frames ui remote-control style ctrl based on the input params.
	"""

	horizontalMin = kwargs.get("horizontalMin", -1.0) #arg; max = 0.0;
	horizontalMin = min(horizontalMin, 0.0)
	horizontalMax = kwargs.get("horizontalMax", 1.0) #arg; min = 0.0;
	horizontalMax = max(horizontalMax, 0.0)

	verticalMin = kwargs.get("verticalMin", -1.0) #arg; max = 0.0;	
	verticalMin = min(verticalMin, 0.0)
	verticalMax = kwargs.get("verticalMax", 1.0) #arg; min = 0.0;
	verticalMax = max(verticalMax, 0.0)

	bodySuffix = kwargs.get("bodySuffix", "") #arg;

	kwargs.update({"controlShape": "circle"})
	kwargs.update({"scale": 1.0})
	ctrl = ctrlCreate(**kwargs)

	#create frame
	kwargs.update({"controlShape": "square"})
	kwargs.update({"scale": 1.0})
	kwargs.update({"bodySuffix": bodySuffix + "Frame"})
	frameCtrl = ctrlCreate(**kwargs)

	frameCtrl.node.sx.set(1.0 + (abs(horizontalMax - horizontalMin) / 2.0))
	frameCtrl.node.sz.set(1.0 + (abs(verticalMax - verticalMin) / 2.0))
	pm.makeIdentity(frameCtrl.node, a = True)

	horDif = (horizontalMin + horizontalMax) / 2
	frameCtrl.node.tx.set(horDif)

	verDif = (verticalMin + verticalMax) / 2
	frameCtrl.node.tz.set(verDif)

	offsetGrp = mnsUtils.createOffsetGroup(ctrl)
	pm.parent(frameCtrl.node, offsetGrp.node)

	mnsUtils.lockAndHideTransforms(ctrl.node, tx = False, tz = False, lock = True)
	mnsUtils.lockAndHideAllTransforms(frameCtrl.node, lock = True)
	pm.transformLimits(ctrl.node, etx = (True, True), etz = (True, True), tx = (horizontalMin, horizontalMax), tz = (verticalMin, verticalMax))

	offsetGrp.node.rx.set(270)
	uiScale = kwargs.get("uiScale", 1.0) #arg;
	offsetGrp.node.s.set((uiScale, uiScale, uiScale))

	frameCtrl.node.overrideEnabled.set(True)
	frameCtrl.node.overrideDisplayType.set(2)

	flip = kwargs.get("flip", False) #arg
	if not flip:
		side = kwargs.get("side", "c") #arg
		if side == "r": flip = True
	
	upsideDown = kwargs.get("upsideDown", False) #arg	
	if upsideDown: offsetGrp.node.rz.set(180)

	if flip: offsetGrp.node.ry.set(180)

	mnsUtils.addAttrToObj([ctrl.node], type = "bool", value = True, name = "isUiStyle", locked = True, keyable = False, cb = False)
	mnsUtils.addAttrToObj([frameCtrl.node], type = "bool", value = True, name = "isUiStyle", locked = True, keyable = False, cb = False)

	#return; MnsNameStd (ctrl), MnsNameStd (uiOffsetGrp), MnsNameStd (Frame)
	return ctrl, offsetGrp, frameCtrl

def batchCreateAllControlShapes(**kwargs):
	side = kwargs.get("side", "c") #arg;
	color = kwargs.get("color", (0.0,1.0,0.0)) #arg;
	csList = buildOptionArrayFromDict(mnsControlShapesDict)
	
	collect = []
	for controlShape in csList:
		ctrl = ctrlCreate(side = side, controlShape = controlShape, color  = color)
		collect.append(ctrl)

	#return; list (MnsNameStd, created shapes)
	return collect

def batchCreateAllControlShapesIcons():
	iconsPath = os.path.dirname(os.path.dirname(os.path.dirname(__file__))).replace("\\", "/") + "/icons/controlShapesIcons"
	if not os.path.isdir(iconsPath): os.makedirs(iconsPath)

	for iconFile in os.listdir(iconsPath):
		iconPath = iconsPath + "/" + iconFile
		os.remove(iconPath)

	sel = pm.ls(sl=True)
	pm.select(clear = True)
	for ctrl in sel:
		ctrl = mnsUtils.validateNameStd(ctrl)
		ctrl.node.v.set(True)
		pm.refresh()
		iconName = ctrl.body
		iconPath = iconsPath + "/" + iconName
		pm.playblast(format = "image", 
					filename = iconPath,
					sequenceTime = False,
					startTime = 0,
					endTime = 1,
					clearCache = True,
					viewer = False,
					showOrnaments = False,
					fp = 1,
					percent = 100,
					compression = "png",
					quality = 100,
					widthHeight = (36,24))
		ctrl.node.v.set(False)

	for iconFile in os.listdir(iconsPath):
		index = iconFile.split(".")[1]
		iconPath = iconsPath + "/" + iconFile
		if index == "1":
			os.remove(iconPath)
		else:
			newPath = iconsPath + "/" + iconFile.split(".")[0] + ".png"
			os.rename(iconPath, newPath)

def textShapeCreate(text = ""):
	if not text: text = "nun"
	transformTemp = pm.group(empty = True, name = "tempName")
	textRet = pm.PyNode(pm.textCurves(t=text)[0])
	pm.makeIdentity([textRet] + textRet.listRelatives(ad = True), apply=True)
	allShapes = textRet.listRelatives(ad = True, type = "nurbsCurve")
	for shape in allShapes: pm.parent(shape, transformTemp, r = 1, shape = 1)
	pm.delete(transformTemp, ch = True)
	pm.delete(textRet)
	transformTemp.rx.set(-90)
	pm.makeIdentity(transformTemp, apply=True)
	pm.xform(transformTemp, cp= True)
	ttG = pm.group(empty = True)
	pm.delete(pm.pointConstraint(ttG, transformTemp))
	pm.delete(ttG)
	pm.makeIdentity(transformTemp, apply=True)
	return transformTemp
	
def circleShapeCreate(**kwargs):
	sections = kwargs.get("sections", 8) #arg;
	control = pm.circle( nr=[0,1,0], r = 1 ,  sections = sections, ch = 0)[0]
	return control

def dialShapeCreate(**kwargs):
	control = pm.circle(nr=[0,1,0], sections = 16, ch = 0, degree = 1)[0]
	pm.move(control + '.cv[12]', (0.5, 0, 0) ,r=True)
	pm.xform(control, ws = 1, a = 1, rp = (0,0,0))
	pm.makeIdentity(control, apply = 1)
	return control

def dialRoundShapeCreate(**kwargs):
	control = pm.circle(nr=[0,1,0], sections = 16, ch = 0, degree = 3)[0]
	pm.move(control + '.cv[13]', (0.5, 0, 0) ,r=True)
	pm.xform(control, ws = 1, a = 1, rp = (0,0,0))
	pm.makeIdentity(control, apply = 1)
	return control

def dialSquareShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1,0,-1),(1,0,-1), (1,0,-0.4), (1.5,0,0), (1,0,0.4), (1,0,1),(-1,0,1), (-1,0,-1)])
	return control

def pinchedCircleShapeCreate(**kwargs):
	control = pm.circle(nr=[0,1,0], sections = 16, ch = 0, degree = 3)[0]
	pm.move(control + '.cv[12]', (0, 0, -0.392646) ,r=True)
	pm.move(control + '.cv[14]', (0, 0, 0.392646) ,r=True)
	return control

def bubblePinShapeCreate(**kwargs):
	control = pm.circle(nr=[0,1,0], sections = 16, ch = 0, degree = 3)[0]
	pm.move(control + '.cv[12]', (0, 0, -0.392646) ,r=True)
	pm.move(control + '.cv[14]', (0, 0, 0.392646) ,r=True)
	pm.move(control + '.cv[11]', (0, 0, -0.725516) ,r=True)
	pm.move(control + '.cv[15]', (0, 0, 0.725516) ,r=True)
	return control

def teardropShapeCreate(**kwargs):
	control = pm.circle(nr=[0,1,0], sections = 8, ch = 0, degree = 3)[0]
	pm.move(control + '.cv[6]', (0, 0, -0.76) ,r=True)
	pm.move(control + '.cv[0]', (0, 0, 0.76) ,r=True)
	return control

def squareShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1,0,-1),(1,0,-1),(1,0,1),(-1,0,1), (-1,0,-1)], k=[0,1,2,3,4])
	return control

def squareRoundShapeCreate(**kwargs):
	control = pm.circle( nr=[0,1,0], r = 1 ,  sections = 16, ch = 0)[0]
	pm.move(control + '.cv[0]', (0.5, 0, -1) ,a=True)
	pm.move(control + '.cv[1]', (0, 0, -1) ,a=True)
	pm.move(control + '.cv[2]', (-0.5, 0, -1) ,a=True)
	pm.move(control + '.cv[3]', (-1, 0, -1) ,a=True)
	pm.move(control + '.cv[4]', (-1, 0, -0.5) ,a=True)
	pm.move(control + '.cv[5]', (-1, 0, 0) ,a=True)
	pm.move(control + '.cv[6]', (-1, 0, 0.5) ,a=True)
	pm.move(control + '.cv[7]', (-1, 0, 1) ,a=True)
	pm.move(control + '.cv[8]', (-0.5, 0, 1) ,a=True)
	pm.move(control + '.cv[9]', (0, 0, 1) ,a=True)
	pm.move(control + '.cv[10]', (0.5, 0, 1) ,a=True)
	pm.move(control + '.cv[11]', (1, 0, 1) ,a=True)
	pm.move(control + '.cv[12]', (1, 0, 0.5) ,a=True)
	pm.move(control + '.cv[13]', (1, 0, 0) ,a=True)
	pm.move(control + '.cv[14]', (1, 0, -0.5) ,a=True)
	pm.move(control + '.cv[15]', (1, 0, -1) ,a=True)
	return control

def squareWithMidDividersShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1,0,-1),(1,0,-1),(1,0,1),(-1,0,1), (-1,0,-1)], k=[0,1,2,3,4])
	shapeB = pm.curve(d=1, p =[(0,0,-1),(0,0,1)])
	shapeC = pm.curve(d=1, p =[(-1,0,0),(1,0,0)])
	pm.parent(shapeB.getShape(), control, r = 1, shape = 1)
	pm.parent(shapeC.getShape(), control, r = 1, shape = 1)
	pm.delete([shapeB, shapeC])

	return control

def puppetRootShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1,0,-1),(1,0,-1),(1,0,1),(-1,0,1), (-1,0,-1)], k=[0,1,2,3,4])
	shapeB = pm.curve(d=1, p =[(0.9,0,0.9),(-0.9,0,0.9),(-0.9,0,0.7),(0.9,0,0.7), (0.9,0,0.9)], k=[0,1,2,3,4])
	pm.parent(shapeB.getShape(), control, r = 1, shape = 1)
	pm.delete(shapeB) 
	return control

def guidesRootShape(**kwargs):
	control = pm.curve(d=1, p=[(-1,0,-1),(1,0,-1),(1,0,1),(-1,0,1), (-1,0,-1)], k=[0,1,2,3,4])
	shapeB = pm.curve(d=1, p=[(-0.93,0,-0.93),(0.93,0,-0.93),(0.93,0,0.93),(-0.93,0,0.93), (-0.93,0,-0.93)], k=[0,1,2,3,4])
	shapeC = pm.curve(d=1, p =[(-1,0,1), (0,0,1.5), (1,0,1)])
	
	pm.parent(shapeB.getShape(), control, r = 1, shape = 1)
	pm.delete(shapeB) 
	pm.parent(shapeC.getShape(), control, r = 1, shape = 1)
	pm.delete(shapeC) 
	
	return control
	
def arrowDodecagonShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-0.25, 0.0, -1.0),(-0.25, 0.0, -1.25),(-0.5, 0.0, -1.25),(0.0, 0.0, -2.0),(0.5, 0.0, -1.25),(0.25, 0.0, -1.25),(0.25, 0.0, -1.0),(0.75, 0.0, -0.75),(1.0, 0.0, -0.25),(1.25, 0.0, -0.25),(1.25, 0.0, -0.5),(2.0, 0.0, 0.0),(1.25, 0.0, 0.5),(1.25, 0.0, 0.25),(1.0, 0.0, 0.25),(0.75, 0.0, 0.75),(0.25, 0.0, 1.0),(0.25, 0.0, 1.25),(0.5, 0.0, 1.25),(0.0, 0.0, 2.0),(-0.5, 0.0, 1.25),(-0.25, 0.0, 1.25),(-0.25, 0.0, 1.0),(-0.75, 0.0, 0.75),(-1.0, 0.0, 0.25),(-1.25, 0.0, 0.25),(-1.25, 0.0, 0.5),(-2.0, 0.0, 0.0),(-1.25, 0.0, -0.5),(-1.25, 0.0, -0.25),(-1.0, 0.0, -0.25),(-0.75, 0.0, -0.75),(-0.25, 0.0, -1.0)])
	return control

def arrowSquareShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-0.25, 0.0, -1.0),(-0.25, 0.0, -1.25),(-0.5, 0.0, -1.25),(0.0, 0.0, -2.0),(0.5, 0.0, -1.25),(0.25, 0.0, -1.25),(0.25, 0.0, -1.0),(1.0, 0.0, -1.0),(1.0, 0.0, -0.25),(1.25, 0.0, -0.25),(1.25, 0.0, -0.5),(2.0, 0.0, 0.0),(1.25, 0.0, 0.5),(1.25, 0.0, 0.25),(1.0, 0.0, 0.25),(1.0, 0.0, 1.0),(0.25, 0.0, 1.0),(0.25, 0.0, 1.25),(0.5, 0.0, 1.25),(0.0, 0.0, 2.0),(-0.5, 0.0, 1.25),(-0.25, 0.0, 1.25),(-0.25, 0.0, 1.0),(-1.0, 0.0, 1.0),(-1.0, 0.0, 0.25),(-1.25, 0.0, 0.25),(-1.25, 0.0, 0.5),(-2.0, 0.0, 0.0),(-1.25, 0.0, -0.5),(-1.25, 0.0, -0.25),(-1.0, 0.0, -0.25),(-1.0, 0.0, -1.0),(-0.25, 0.0, -1.0)])
	return control

def curvedFourArrowShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-0.25, 0.0, -1.0),(-0.25, 0.0, -1.25),(-0.5, 0.0, -1.25),(0.0, 0.0, -2.0),(0.5, 0.0, -1.25),(0.25, 0.0, -1.25),(0.25, 0.0, -1.0),(0.5, 0.0, -0.5),(1.0, 0.0, -0.25),(1.25, 0.0, -0.25),(1.25, 0.0, -0.5),(2.0, 0.0, 0.0),(1.25, 0.0, 0.5),(1.25, 0.0, 0.25),(1.0, 0.0, 0.25),(0.5, 0.0, 0.5),(0.25, 0.0, 1.0),(0.25, 0.0, 1.25),(0.5, 0.0, 1.25),(0.0, 0.0, 2.0),(-0.5, 0.0, 1.25),(-0.25, 0.0, 1.25),(-0.25, 0.0, 1.0),(-0.5, 0.0, 0.5),(-1.0, 0.0, 0.25),(-1.25, 0.0, 0.25),(-1.25, 0.0, 0.5),(-2.0, 0.0, 0.0),(-1.25, 0.0, -0.5),(-1.25, 0.0, -0.25),(-1.0, 0.0, -0.25),(-0.5, 0.0, -0.5),(-0.25, 0.0, -1.0)])
	return control

def fourArrowShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-0.25, 0.0, -1.0),(-0.25, 0.0, -1.25),(-0.5, 0.0, -1.25),(0.0, 0.0, -2.0),(0.5, 0.0, -1.25),(0.25, 0.0, -1.25),(0.25, 0.0, -1.0),(0.25, 0.0, -0.25),(1.0, 0.0, -0.25),(1.25, 0.0, -0.25),(1.25, 0.0, -0.5),(2.0, 0.0, 0.0),(1.25, 0.0, 0.5),(1.25, 0.0, 0.25),(1.0, 0.0, 0.25),(0.25, 0.0, 0.25),(0.25, 0.0, 1.0),(0.25, 0.0, 1.25),(0.5, 0.0, 1.25),(0.0, 0.0, 2.0),(-0.5, 0.0, 1.25),(-0.25, 0.0, 1.25),(-0.25, 0.0, 1.0),(-0.25, 0.0, 0.25),(-1.0, 0.0, 0.25),(-1.25, 0.0, 0.25),(-1.25, 0.0, 0.5),(-2.0, 0.0, 0.0),(-1.25, 0.0, -0.5),(-1.25, 0.0, -0.25),(-1.0, 0.0, -0.25),(-0.25, 0.0, -0.25),(-0.25, 0.0, -1.0)])
	return control

def dodecagonShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(1.0, 0.0, -0.25),(1.0, 0.0, 0.25),(0.75, 0.0, 0.75),(0.25, 0.0, 1.0),(-0.25, 0.0, 1.0),(-0.75, 0.0, 0.75),(-1.0, 0.0, 0.25),(-1.0, 0.0, -0.25),(-0.75, 0.0, -0.75),(-0.25, 0.0, -1.0),(0.25, 0.0, -1.0),(0.75, 0.0, -0.75),(1.0, 0.0, -0.25)])
	return control

def triangleShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1.0, 0.0, -1.0),(1.0, 0.0, 0.0),(-1.0, 0.0, 1.0),(-1.0, 0.0, -1.0)])
	return control

def flatDiamondShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.0, 0.0, -1.0),(1.0, 0.0, 0.0),(0.0, 0.0, 1.0),(-1.0, 0.0, 0.0),(0.0, 0.0, -1.0)])
	return control

def flatDiamondRootShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.0, 0.0, -1.0),(1.0, 0.0, 0.0),(0.0, 0.0, 1.0),(-1.0, 0.0, 0.0),(0.0, 0.0, -1.0)])
	shapeB = pm.curve(d=1, p =[(0.5,0,0.375), (0,0,0.875), (-0.5,0,0.375)])
	pm.parent(shapeB.getShape(), control, r = 1, shape = 1)
	pm.delete(shapeB) 

	return control

def hexagonShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.5, 0.0, -0.875),(1.0, 0.0, 0.0),(0.5, 0.0, 0.875),(-0.5, 0.0, 0.875),(-1.0, 0.0, 0.0),(-0.5, 0.0, -0.875),(0.5, 0.0, -0.875)])
	return control

def octagonShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.0, 0.0, -1.0),(0.75, 0.0, -0.75),(1.0, 0.0, 0.0),(0.75, 0.0, 0.75),(0.0, 0.0, 1.0),(-0.75, 0.0, 0.75),(-1.0, 0.0, 0.0),(-0.75, 0.0, -0.75),(0.0, 0.0, -1.0),(0.75, 0.0, -0.75)])
	return control

def plusShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(1.0, 0.0, -0.25),(1.0, 0.0, 0.25),(0.25, 0.0, 0.25),(0.25, 0.0, 1.0),(-0.25, 0.0, 1.0),(-0.25, 0.0, 0.25),(-1.0, 0.0, 0.25),(-1.0, 0.0, -0.25),(-0.25, 0.0, -0.25),(-0.25, 0.0, -1.0),(0.25, 0.0, -1.0),(0.25, 0.0, -0.25),(1.0, 0.0, -0.25)])
	return control

def crossShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.375, 0.0, 0.0),(1.0, 0.0, 0.625),(0.625, 0.0, 1.0),(0.0, 0.0, 0.375),(-0.625, 0.0, 1.0),(-1.0, 0.0, 0.625),(-0.375, 0.0, 0.0),(-1.0, 0.0, -0.625),(-0.625, 0.0, -1.0),(0.0, 0.0, -0.375),(0.625, 0.0, -1.0),(1.0, 0.0, -0.625),(0.375, 0.0, 0.0)])
	return control

def diamondShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1.0, 0.0, 0.0),(0.0, 0.0, 1.0),(1.0, 0.0, 0.0),(0.0, 0.0, -1.0),(-1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(1.0, 0.0, 0.0),(0.0, -1.0, 0.0),(-1.0, 0.0, 0.0),(0.0, 0.0, 1.0),(0.0, 1.0, 0.0),(0.0, 0.0, -1.0),(0.0, -1.0, 0.0),(0.0, 0.0, 1.0)])
	return control

def pickShapeCreate(**kwargs):
	control = pm.circle(nr=[0,1,0], ch = 0)[0]
	pm.move(control + '.cv[5]', (0, 0, -1.108194) ,r=True)
	pm.move(control + '.cv[1]', (0, 0, 1.108194) ,r=True)
	pm.move(control + '.cv[6]', (-0.783612, 0, -0.783612) ,r=True)
	pm.move(control + '.cv[0]', (-0.783612, 0, 0.783612) ,r=True)
	pm.move(control + '.cv[7]', (-1.108194, 0, 0) ,r=True)
	pm.move(control + '.cv[2]', (0, 0, .2) ,r=True)
	pm.move(control + '.cv[4]', (0, 0, -.2) ,r=True)
	control.tx.set(0.5)
	pm.xform(control, ws = 1, a = 1, rp = (0,0,0))
	pm.makeIdentity(control, apply = 1)
	return control

def cubeShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1.0, -1.0, -1.0),(-1.0, 1.0, -1.0),(1.0, 1.0, -1.0),(1.0, 1.0, 1.0),(1.0, -1.0, 1.0),(1.0, -1.0, -1.0),(-1.0, -1.0, -1.0),(-1.0, -1.0, 1.0),(-1.0, 1.0, 1.0),(-1.0, 1.0, -1.0),(1.0, 1.0, -1.0),(1.0, -1.0, -1.0),(1.0, -1.0, 1.0),(-1.0, -1.0, 1.0),(-1.0, 1.0, 1.0),(1.0, 1.0, 1.0)])
	return control

def lightSphereShapeCreate(**kwargs):
	cicles = []
	cicrleA = circleShapeCreate()
	circleB = pm.duplicate(cicrleA)[0]
	circleB.rx.set(90)
	pm.makeIdentity(circleB, apply = 1)
	circleC = pm.duplicate(circleB)[0]
	circleC.ry.set(90)
	pm.makeIdentity(circleC, apply = 1)
	for c in [circleB, circleC]:
		pm.parent(c.getShape(), cicrleA, r = 1, shape = 1)
		pm.delete(c)
	return cicrleA

def sphereShapeCreate(**kwargs):
	circles = []
	cicrleA = circleShapeCreate()
	circleB = pm.duplicate(cicrleA)[0]
	circleB.rx.set(90)
	pm.makeIdentity(circleB, apply = 1)
	circles.append(circleB)
	circleC = pm.duplicate(circleB)[0]
	circleC.ry.set(90)
	pm.makeIdentity(circleC, apply = 1)
	circles.append(circleC)
	circleD = pm.duplicate(circleC)[0]
	circleD.ry.set(45)
	pm.makeIdentity(circleD, apply = 1)
	circles.append(circleD)
	circleE = pm.duplicate(circleC)[0]
	circleE.ry.set(-45)
	pm.makeIdentity(circleE, apply = 1)
	circles.append(circleE)
	for c in circles:
		pm.parent(c.getShape(), cicrleA, r = 1, shape = 1)
		pm.delete(c) 
	return cicrleA

def pyramidShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(1.0, 2.0, -1.0),(1.0, 2.0, 1.0),(-1.0, 2.0, 1.0),(-1.0, 2.0, -1.0),(1.0, 2.0, -1.0),(0.0, 0.0, 0.0),(-1.0, 2.0, 1.0),(1.0, 2.0, 1.0),(0.0, 0.0, 0.0),(-1.0, 2.0, -1.0)])
	return control

def arrowShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(-1.0, 0.0, -0.25),(-1.0, 0.0, 0.25),(0.0, 0.0, 0.25),(0.0, 0.0, 0.625),(1.0, 0.0, 0.0),(0.0, 0.0, -0.625),(0.0, 0.0, -0.25),(-1.0, 0.0, -0.25)])
	control.rz.set(-90)
	control.ty.set(1)
	pm.makeIdentity(control, apply = 1)
	pm.xform(control, ws = 1, a = 1, rp = (0,0,0))
	return control

def doubleArrowShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.5, 0.0, -0.375),(1.0, 0.0, 0.0),(0.5, 0.0, 0.375),(0.5, 0.0, 0.125),(-0.5, 0.0, 0.125),(-0.5, 0.0, 0.375),(-1.0, 0.0, 0.0),(-0.5, 0.0, -0.375),(-0.5, 0.0, -0.125),(0.5, 0.0, -0.125),(0.5, 0.0, -0.375)])
	control.rz.set(-90)
	pm.makeIdentity(control, apply = 1)
	return control

def tripleArrowShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.625, 0.0, -0.125),(0.625, 0.0, -0.375),(1.0, 0.0, 0.0),(0.625, 0.0, 0.375),(0.625, 0.0, 0.125),(-0.625, 0.0, 0.125),(-0.625, 0.0, 0.375),(-1.0, 0.0, 0.0),(-0.625, 0.0, -0.375),(-0.625, 0.0, -0.125),(-0.125, 0.0, -0.125),(-0.125, 0.0, -0.625),(-0.375, 0.0, -0.625),(0.0, 0.0, -1.0),(0.375, 0.0, -0.625),(0.125, 0.0, -0.625),(0.125, 0.0, -0.125),(0.625, 0.0, -0.125)])
	control.rz.set(-90)
	pm.makeIdentity(control, apply = 1)
	return control

def coneShapeCreate(**kwargs):
	control = pm.curve(d=1, p=[(0.5, 2.0, 0.875),(-0.5, 2.0, 0.875),(0.0, 0.0, 0.0),(0.5, 2.0, 0.875),(1.0, 2.0, 0.0),(0.0, 0.0, 0.0),(0.5, 2.0, -0.875),(1.0, 2.0, 0.0),(0.5, 2.0, -0.875),(-0.5, 2.0, -0.875),(0.0, 0.0, 0.0),(-1.0, 2.0, 0.0),(-0.5, 2.0, -0.875),(-1.0, 2.0, 0.0),(-0.5, 2.0, 0.875)])
	return control
	 
def pinShapeCreate(**kwargs):
	light = kwargs.get("light", True) #arg;
	sphereA = None
	if light: 
		sphereA = circleShapeCreate()
	else: sphereA = sphereShapeCreate()
	sphereA.tx.set(2)
	if not light: sphereA.rz.set(90)
	sphereA.s.set((0.25, 0.25,0.25))
	pm.makeIdentity(sphereA, apply = 1)
	line = pm.curve(d=1, p=[(1.75, 0.0, 0.0),(0.0, 0.0, 0.0)])
	pm.parent(sphereA.getShapes(), line, r = 1, shape = 1)
	pm.delete(sphereA)
	line.rz.set(90)
	pm.xform(line, ws = 1, a = 1, rp = (0,0,0))
	pm.makeIdentity(line, apply = 1)
	return line

def pointArrowShapeCreate(**kwargs):
	arrowA = arrowShapeCreate()
	for ep in pm.ls(arrowA.nodeName() + ".ep[0:]",fl=True):
		pm.move(ep, (1,0,0), r = 1)
	arrowB = pm.duplicate(arrowA)[0]
	arrowB.rx.set(90)
	pm.makeIdentity(arrowB, apply = 1)
	pm.parent(arrowB.getShapes(), arrowA, r = 1, shape = 1)
	pm.delete(arrowB)
	arrowA.rz.set(180)
	arrowA.tx.set(2)
	pm.xform(arrowA, ws = 1, a = 1, rp = (0,0,0))
	arrowA.rz.set(-90)
	pm.makeIdentity(arrowA, apply = 1)
	return arrowA

def cylinderShapeCreate(**kwargs):
	circleA = circleShapeCreate()
	circleA.rz.set(-90)
	pm.makeIdentity(circleA, apply = 1)
	for ep in pm.ls(circleA.nodeName() + ".cv[0:]",fl=True): pm.move(ep, (-1,0,0), r = 1)
	circleB = pm.duplicate(circleA)[0]
	circleB.tx.set(2)
	pm.makeIdentity(circleB, apply = 1)
	pm.parent(circleB.getShapes(), circleA, r = 1, shape = 1)
	pm.delete(circleB)
	lines = []
	lineA = pm.curve(d=1, p=[(1.0, 0.0, 0.0),(-1.0, 0.0, 0.0)])
	lineA.ty.set(1)
	pm.xform(lineA, ws = 1, a = 1, rp = (0,0,0))
	pm.makeIdentity(lineA, apply = 1)
	rot = 45
	for i in range(0, 7):
		line = pm.duplicate(lineA)[0]
		line.rx.set(rot)
		pm.makeIdentity(line, apply = 1)
		pm.parent(line.getShape(), circleA, r = 1, shape = 1)
		pm.delete(line)
		rot += 45
	pm.parent(lineA.getShape(), circleA, r = 1, shape = 1)
	pm.delete(lineA)
	circleA.rz.set(-90)
	pm.makeIdentity(circleA, apply = 1)
	return circleA

def directionCircle(**kwargs):
	circle = circleShapeCreate()
	lines = []
	lines.append(pm.curve(d=1, p=[(-1, 0.0, 0.0),(1, 0.0, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, -1),(0.0, 0.0, 1)]))
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(0.0, 1, 0.0)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, 0.0),(0.0, 1, 0.0), (0.1, 0.85, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.0, 0.85, -0.1),(0.0, 1, 0.0), (0.0, 0.85, 0.1)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, 0.0),(0.0, 0.85, -0.1), (0.1, 0.85, 0.0), (0.0, 0.85, 0.1), (-0.1, 0.85, 0.0)]))
	
	for line in lines:
		pm.parent(line.getShape(), circle, r = 1, shape = 1)
		pm.delete(line)

	return circle

def directionDiamond(**kwargs):
	circle = pm.curve(d=1, p=[(-1, 0.0, 0.0),(0.0, 0.0, -1), (1,0,0), (0,0,1), (-1,0,0)])
	lines = []
	lines.append(pm.curve(d=1, p=[(-1, 0.0, 0.0),(1, 0.0, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, -1),(0.0, 0.0, 1)]))
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(0.0, 1, 0.0)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, 0.0),(0.0, 1, 0.0), (0.1, 0.85, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.0, 0.85, -0.1),(0.0, 1, 0.0), (0.0, 0.85, 0.1)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, 0.0),(0.0, 0.85, -0.1), (0.1, 0.85, 0.0), (0.0, 0.85, 0.1), (-0.1, 0.85, 0.0)]))
	
	for line in lines:
		pm.parent(line.getShape(), circle, r = 1, shape = 1)
		pm.delete(line)

	return circle
	
def directionCubeShape(**kwargs):
	circle = cubeShapeCreate()
	lines = []
	
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(0.0, 1, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.1, 0.85, 0.1),(-0.1, 0.85, 0.1),(-0.1, 0.85, -0.1), (0.1, 0.85, -0.1), (0.1, 0.85, 0.1)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, 0.1),(0.0, 1, 0.0), (0.1, 0.85, 0.1)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, -0.1),(0.0, 1, 0.0), (0.1, 0.85, -0.1)]))
	
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(1, 0, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.85, 0.1, 0.1),(0.85, -0.1, 0.1),(0.85, -0.1, -0.1), (0.85, 0.1, -0.1), (0.85, 0.1, 0.1)]))
	lines.append(pm.curve(d=1, p=[(0.85, -0.1, 0.1),(1, 0, 0.0), (0.85, 0.1, 0.1)]))
	lines.append(pm.curve(d=1, p=[(0.85, -0.1, -0.1),(1, 0, 0.0), (0.85, 0.1, -0.1)]))
	
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(0, 0, 1)]))
	lines.append(pm.curve(d=1, p=[(0.1, 0.1, 0.85),(-0.1, 0.1,0.85),(-0.1, -0.1,0.85), (0.1, -0.1,0.85), (0.1, 0.1, 0.85)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.1, 0.85),(0, 0, 1), (0.1, 0.1, 0.85)]))
	lines.append(pm.curve(d=1, p=[(-0.1, -0.1, 0.85),(0, 0, 1), (0.1, -0.1, 0.85)]))
	
	for line in lines:
		pm.parent(line.getShape(), circle, r = 1, shape = 1)
		pm.delete(line)

	circle.sx.set(0.5)
	circle.sy.set(0.5)
	circle.sz.set(0.5)
	pm.makeIdentity(circle, a = True)

	return circle

def directionSphereShape(**kwargs):
	circle = lightSphereShapeCreate()
	lines = []
	
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(0.0, 1, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.1, 0.85, 0.1),(-0.1, 0.85, 0.1),(-0.1, 0.85, -0.1), (0.1, 0.85, -0.1), (0.1, 0.85, 0.1)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, 0.1),(0.0, 1, 0.0), (0.1, 0.85, 0.1)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.85, -0.1),(0.0, 1, 0.0), (0.1, 0.85, -0.1)]))
	
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(1, 0, 0.0)]))
	lines.append(pm.curve(d=1, p=[(0.85, 0.1, 0.1),(0.85, -0.1, 0.1),(0.85, -0.1, -0.1), (0.85, 0.1, -0.1), (0.85, 0.1, 0.1)]))
	lines.append(pm.curve(d=1, p=[(0.85, -0.1, 0.1),(1, 0, 0.0), (0.85, 0.1, 0.1)]))
	lines.append(pm.curve(d=1, p=[(0.85, -0.1, -0.1),(1, 0, 0.0), (0.85, 0.1, -0.1)]))
	
	lines.append(pm.curve(d=1, p=[(0.0, 0.0, 0.0),(0, 0, 1)]))
	lines.append(pm.curve(d=1, p=[(0.1, 0.1, 0.85),(-0.1, 0.1,0.85),(-0.1, -0.1,0.85), (0.1, -0.1,0.85), (0.1, 0.1, 0.85)]))
	lines.append(pm.curve(d=1, p=[(-0.1, 0.1, 0.85),(0, 0, 1), (0.1, 0.1, 0.85)]))
	lines.append(pm.curve(d=1, p=[(-0.1, -0.1, 0.85),(0, 0, 1), (0.1, -0.1, 0.85)]))
	
	for line in lines:
		pm.parent(line.getShape(), circle, r = 1, shape = 1)
		pm.delete(line)

	return circle