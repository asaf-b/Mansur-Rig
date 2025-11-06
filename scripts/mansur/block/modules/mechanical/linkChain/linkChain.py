"""Author: Asaf Ben-Zur
Best used for: Tank-Treads, Bike-Chains, Ferris-Wheel, Tire, Conveyor-Belt
This is a comprehensive module, to create a link-chain style behaviour.
Originally created for tank-treads, but can be used for a range of components.
On creation, based on the number on the numberOfLinks setting, joints will be created on a circle Nurbs curve with shapeSections setting amount.
After creation, the shape can be tweaked to fit any need. 
IMPORTANT NOTE: This module requires a joint-struct-rebuild once the Nurbs shape has been tweaked.
Once the joint-struct is revuilt, the joints will be layed out uniformally along the given shape.
Upon construction, a main control will be created for controlling the entire position of the module.
Under, a chain-driver control will be created. Rotating it will drive the joint chain along the curve in both forwards and backwards directions.
Also, use the shape-tweak layer to create a tweak feature for the shape on construction. This will allow manipulation of the shape dynamically while the chain is driven.
Automatic drive based on position is also possible wihin this module using the AutoDrive layer.
"""



from maya import cmds
import pymel.core as pm

import math

def createUpCurveFromSamples(mansur, rootGuide, samples, upCurveOffset):
	from mansur.core import nodes as mnsNodes

	#now duplicate all iLocs and offset them to create the actual upCurve using btc
	duplictaeSmaples = pm.duplicate(samples)

	pm.parent(duplictaeSmaples, w = True)
	for dupSample in duplictaeSmaples:
		pm.move(dupSample, (upCurveOffset,0.0,0.0), r = True, os = True, wd = True)

	newUpCurveBtc = mnsNodes.mnsBuildTransformsCurveNode(
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body + "Temp", 
												transforms = duplictaeSmaples, 
												deleteCurveObjects = False, 
												buildOffsetCurve = False,
												degree = 3,
												buildMode = 1,
												form = 1)
	upCurve = newUpCurveBtc["outCurve"]
	upCurve.node.create.disconnect()
	pm.delete(duplictaeSmaples)
	return upCurve

def filterValidShapeTweakers(tweakersList = [], mansur = None):
	from mansur.core import prefixSuffix
	from mansur.core import utility as mnsUtils

	returnList = []
	if tweakersList:
		for k, tweaker in enumerate(tweakersList):
			tweaker = mnsUtils.validateNameStd(tweaker)
			if tweaker:
				#handleJnts
				if tweaker.suffix == prefixSuffix.mnsPS_rJnt or tweaker.suffix == prefixSuffix.mnsPS_jnt or tweaker.suffix == prefixSuffix.mnsPS_iJnt:
					if tweaker.node not in returnList:
						returnList.append(tweaker.node)
				
				#handleGuides
				elif tweaker.suffix == prefixSuffix.mnsPS_gRootCtrl or tweaker.suffix == prefixSuffix.mnsPS_gCtrl:
					status, jntSlave = mnsUtils.validateAttrAndGet(tweaker.node, "jntSlave", None)
					if jntSlave:
						jntSlave = mnsUtils.validateNameStd(jntSlave)
						if jntSlave and jntSlave.node not in returnList:
							returnList.append(jntSlave.node)
	return returnList

def construct(mansur, MnsBuildModule, **kwargs):
	########### local library imports ###########
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core import prefixSuffix

	########### global module objects collect ###########
	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(MnsBuildModule.rootGuide))
	rootGuide = MnsBuildModule.rootGuide
	allGuides = [MnsBuildModule.rootGuide] + MnsBuildModule.guideControls
	moduleTopGrp = MnsBuildModule.moduleTop
	animGrp = MnsBuildModule.animGrp
	animStaticGrp = MnsBuildModule.animStaticGrp
	animStaticGrp.node.v.set(False)
	rigComponentsGrp = MnsBuildModule.rigComponentsGrp
	attrHost = MnsBuildModule.attrHostCtrl or animGrp
	customGuides = MnsBuildModule.cGuideControls

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	status, controlShape = mnsUtils.validateAttrAndGet(rootGuide, "controlShape", "circle")
	ctrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = controlShape,
								scale = modScale, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								createSpaceSwitchGroup = True,
								createOffsetGrp = True,
								isFacial = MnsBuildModule.isFacial,
								alongAxis = 0)
	ctrlsCollect.append(ctrl)
	host = MnsBuildModule.attrHostCtrl or ctrl

	status, slaveControlShape = mnsUtils.validateAttrAndGet(rootGuide, "slaveControlShape", "dodecagon")
	status, slaveChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "slaveChannelControl", 0)
	if status: slaveChannelControl = mnsUtils.splitEnumAttrToChannelControlList("slaveChannelControl", rootGuide.node)

	slaveCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = slaveControlShape,
								scale = modScale * 0.7, 
								parentNode = ctrl,
								symmetryType = symmetryType,
								doMirror = True,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								blkCtrlTypeID = 0,
								chennelControl = slaveChannelControl,
								isFacial = MnsBuildModule.isFacial,
								alongAxis = 0)
	ctrlsCollect.append(slaveCtrl)
	status, mapRoatationToAxis = mnsUtils.validateAttrAndGet(rootGuide, "mapRoatationToAxis", 0)
	rxEn, ryEn, rzEn = False, False, False
	if mapRoatationToAxis == 0: rxEn = True
	elif mapRoatationToAxis == 1: ryEn = True
	elif mapRoatationToAxis == 2: rzEn = True
	mnsUtils.lockAndHideTransforms(slaveCtrl.node, lock = True, cb = False, keyable = False, t = False, s = False, rx = rxEn, ry = ryEn, rz = rzEn, negateOperation = True)

	chainShape = None
	forwardDirCusGuide = None
	for cg in customGuides:
		if "chainshape" in cg.name.lower():
			chainShape = cg
		if "ForwardDirection_" in cg.node.nodeName():
			forwardDirCusGuide = cg

	if chainShape:
		#first get the curve nodes
		status, pocNode = mnsUtils.validateAttrAndGet(rootGuide, "origPocn", None)
		if pocNode:
			#duplicate the chain shape, and connect to the node
			newChainShape = mnsUtils.duplicateNameStd(chainShape)
			pm.parent(newChainShape.node, ctrl.node)
			newChainShape = mnsUtils.returnNameStdChangeElement(newChainShape, suffix = prefixSuffix.mnsPS_techCtrl)
			mnsUtils.addBlockClasIDToObj(newChainShape)

			#connect new shape
			newChainShape.node.getShape().worldSpace[0] >> pocNode.curve
			newChainShape.node.getShape().worldSpace[0] >> pocNode.bindCurve
			pocNode.bindCurve.disconnect()
			pocNode.mode.set(3)

			#global scale
			blkUtils.getGlobalScaleAttrFromTransform(ctrl) >> pocNode.globalScale
			pocNode.doScale.set(1)
			pocNode.resetScale.set(1)

			#shapeVisAttr
			shapeVisAttr = mnsUtils.addAttrToObj([host], type = "bool", value = False, name = "shapeVis", replace = True)[0]
			shapeVisAttr >> newChainShape.node.v

			#create behaviour
			status, doAutoDrive = mnsUtils.validateAttrAndGet(rootGuide, "doAutoDrive", False)
			status, wheelDiameter = mnsUtils.validateAttrAndGet(rootGuide, "wheelDiameter", 20.0)
			wheelModGrp = None
			if doAutoDrive:
				directionLoc = mnsUtils.createNodeReturnNameStd(parentNode = ctrl, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "Dir", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
				pm.delete(pm.parentConstraint(forwardDirCusGuide.node, directionLoc.node))
				directionLoc.node.v.set(False)

				wheelModGrp = mnsUtils.createOffsetGroup(slaveCtrl, type = "modifyGrp")

				status, autoDriveDefault = mnsUtils.validateAttrAndGet(rootGuide, "autoDriveDefault", True)
				status, autoDriveWheelDiameter = mnsUtils.validateAttrAndGet(rootGuide, "autoDriveWheelDiameter", 20.0)
				adwNode = mnsNodes.mnsAutoWheelDriveNode(side =rootGuide.side, 
														body = rootGuide.body, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id,
														wheelDiameter = autoDriveWheelDiameter,
														driverWorldMatrix = ctrl.node.worldMatrix[0],
														startDirectionWorldMatrix = directionLoc.node.worldMatrix[0])
				#connect out rotation
				attrToCon = wheelModGrp.node.rx
				if mapRoatationToAxis == 1: attrToCon = wheelModGrp.node.ry
				elif mapRoatationToAxis == 2: attrToCon = wheelModGrp.node.rz
				
				#gearRatio
				status, gearRatio = mnsUtils.validateAttrAndGet(rootGuide, "gearRatio", 1.0)
				mdlNode = mnsNodes.mdlNode(adwNode.node.outRotation, gearRatio)

				status, reverseDirection = mnsUtils.validateAttrAndGet(rootGuide, "reverseDirection", False)
				if not reverseDirection:
					mdlNode.node.output >> attrToCon
				else:
					mnsNodes.mdlNode(mdlNode.node.output, -1.0, attrToCon)

				#create drive attributes
				mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "AutoDrive", replace = True, locked = True)
				speedMulAttr = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "speedMultiplier", replace = True)[0]
				speedMulAttr >> adwNode.node.speedMultiplier
				gearRatioAttr = mnsUtils.addAttrToObj([host], type = "float", value = gearRatio, name = "gearRatio", replace = True)[0]
				gearRatioAttr >> mdlNode.node.input2
				startFrameAttr = mnsUtils.addAttrToObj([host], type = "int", value = 1, name = "startFrame", replace = True, keyable = False, cb = True)[0]
				startFrameAttr >> adwNode.node.startFrame
				startFrameFromRangeAttr = mnsUtils.addAttrToObj([host], type = "bool", value = True, name = "startFrameFromRange", replace = True, keyable = False, cb = True)[0]
				startFrameFromRangeAttr >> adwNode.node.startFrameFromRange						

			#connect the driver sum to the pocn uOffset
			#slaveOffsetGrp = blkUtils.getOffsetGrpForCtrl(slaveCtrl)
			#mnsQuatBlendNode = mnsNodes.mnsQuatBlendNode(inMatrix1 = slaveCtrl.node.worldMatrix[0], inMatrix2 = ctrl.node.worldInverseMatrix[0])
			mdNode = mnsNodes.mdlNode(wheelDiameter, math.pi, None)
			mdlNode = mnsNodes.mdNode([slaveCtrl.node.rotateX, 0, 0], [360, 1, 1], None, operation = 2)
			if doAutoDrive and wheelModGrp:
				adlNode = mnsNodes.adlNode(slaveCtrl.node.rotateX, wheelModGrp.node.rotateX, mdlNode.node.input1X)

			mdNode = mnsNodes.mdlNode(mdlNode.node.outputX, mdNode.node.output, pocNode.uOffset)

			status, reverseOffsetDirection = mnsUtils.validateAttrAndGet(rootGuide.node, "reverseOffsetDirection", False)
			if reverseOffsetDirection:
				mdNode = mnsNodes.mdlNode(mdNode.node.output, -1.0, pocNode.uOffset)

			#add pre construct value
			outCons = rootGuide.node.uOffset.listConnections(d = True, s = False)
			for i in outCons:
				if type(i) == pm.nodetypes.MultDoubleLinear:
					adlNode = mnsNodes.adlNode(mdNode.node.output, i.output, pocNode.uOffset)
					blkUtils.connectSlaveToDeleteMaster(adlNode, ctrl)

			#create a phisical curve object from pocn upCurve
			upCurveStd = prefixSuffix.MnsNameStd(side =rootGuide.side, body = rootGuide.body + "UpCurve", alpha = rootGuide.alpha, id = rootGuide.id, suffix = prefixSuffix.mnsPS_crv)
			crvObj = pm.createNode("nurbsCurve").getParent()
			crvObj.rename(upCurveStd.name)
			upCurveStd.node = crvObj
			pocNode.upCurve >> crvObj.getShape().create
			crvObj.getShape().create.disconnect()
			crvObj.v.set(False)

			pm.parent(upCurveStd.node, ctrl.node)
			crvObj.getShape().worldSpace[0] >> pocNode.upCurve
		
			##########
			###shape tweakers feature
			##########
			status, doShapeTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doShapeTweakers", False)
			if doShapeTweakers:
				status, shapeTweakers = mnsUtils.validateAttrAndGet(rootGuide, "shapeTweakers", None)
				if status:
					shapeTweakers = mnsUtils.splitEnumToStringList("shapeTweakers", rootGuide.node)
					shapeTweakers = filterValidShapeTweakers(shapeTweakers, mansur)
					if shapeTweakers:
						status, tweakMethod = mnsUtils.validateAttrAndGet(rootGuide, "tweakMethod", 0)

						#create the dyn shape
						dynShape = mnsUtils.returnNameStdChangeElement(mnsUtils.duplicateNameStd(newChainShape), body = newChainShape.body + "Tweak")
						baseShape = mnsUtils.returnNameStdChangeElement(mnsUtils.duplicateNameStd(newChainShape), body = newChainShape.body + "TweakBase")
						#reparent the shapes correctly
						pm.parent(dynShape.node, animStaticGrp.node)
						pm.parent(baseShape.node, animStaticGrp.node)
						pm.parent(newChainShape.node, animStaticGrp.node)

						if tweakMethod == 0 or tweakMethod == 2: #rebuild then skin
							if tweakMethod == 0:
								status, tweakCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "tweakCurveDegree", 3)
								status, rebuildNumOfSpans = mnsUtils.validateAttrAndGet(rootGuide, "rebuildNumOfSpans", 8)

								pm.rebuildCurve(dynShape.node, ch = False, rpo = True, rt = False, end = True, kr = True, kcp = False, kep = True, kt = False, s = rebuildNumOfSpans, d = tweakCurveDegree, tol = 0.01)
								pm.rebuildCurve(baseShape.node, ch = False, rpo = True, rt = False, end = True, kr = True, kcp = False, kep = True, kt = False, s = rebuildNumOfSpans, d = tweakCurveDegree, tol = 0.01)
								
							#skin
							pm.skinCluster(dynShape.node, shapeTweakers, tsb = True, ps = 100)
						elif tweakMethod == 1: #btc Mode
							#create 2 shapes, base and dyn, using btc node, out of the input tweakers, in order
							status, tweakCurveInterpolaion = mnsUtils.validateAttrAndGet(rootGuide, "tweakCurveInterpolaion", 1)
							status, tweakCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "tweakCurveDegree", 3)
							dynShapeNode = mnsNodes.mnsBuildTransformsCurveNode(
														side = rootGuide.side, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id, 
														body = rootGuide.body + "ShapeTweakBase", 
														transforms = shapeTweakers, 
														deleteCurveObjects = False, 
														tangentDirection = 2, 
														buildOffsetCurve = False,
														degree = tweakCurveDegree,
														buildMode = tweakCurveInterpolaion,
														form = 1)
							
							dynShape = dynShapeNode["outCurve"]
							pm.parent(dynShape.node, animStaticGrp.node)
							pm.delete(baseShape.node)
							baseShape = mnsUtils.duplicateNameStd(dynShape)

						#skin the input and base curves
						tweakBindJnt = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "TweakBaseBind", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "helperJoint", createBlkClassID = False, incrementAlpha = False)
						pm.parent(tweakBindJnt.node, rigComponentsGrp.node)
						mnsNodes.mnsMatrixConstraintNode(side = rootGuide.side, id = rootGuide.id, body = rootGuide.body + "Bind", alpha = rootGuide.alpha, targets = [tweakBindJnt.node], sources = [animGrp.node])
						pm.skinCluster(baseShape.node, [tweakBindJnt.node], tsb = True)
						pm.skinCluster(newChainShape.node, [tweakBindJnt.node], tsb = True)

						#create a crvTweak node for the driver curve
						curveTweakNodeB = mnsNodes.mnsCurveTweakNode(
														side = rootGuide.side, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id, 
														body = rootGuide.body + "ShapeTweak", 
														inputCurve = newChainShape.node.worldSpace[0],
														inputBaseCurve = baseShape.node.worldSpace[0],
														inputTweakCurve = dynShape.node.worldSpace[0],
														buildOffsetCurve = False
														)
						blkUtils.connectSlaveToDeleteMaster(curveTweakNodeB, ctrl)
						curveTweakNodeB.node.outCurve >> pocNode.curve

						#create a crvTweak node for the up curve
						curveTweakNodeC = mnsNodes.mnsCurveTweakNode(
														side = rootGuide.side, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id, 
														body = rootGuide.body + "UpShapeTweak", 
														inputCurve = upCurveStd.node.worldSpace[0],
														inputBaseCurve = baseShape.node.worldSpace[0],
														inputTweakCurve = dynShape.node.worldSpace[0],
														buildOffsetCurve = False
														)
						blkUtils.connectSlaveToDeleteMaster(curveTweakNodeB, ctrl)
						curveTweakNodeC.node.outCurve >> pocNode.upCurve
						
	#tranfer auth
	blkUtils.transferAuthorityToCtrl(relatedJnt, slaveCtrl)

	
	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, host, host

def customGuides(mansur, builtGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps

	custGuides = []
	parentDict = {}

	if builtGuides:
		rigTop = blkUtils.getRigTop(builtGuides[0])
		modScale = rigTop.node.assetScale.get() * builtGuides[0].node.controlsMultiplier.get() * mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]

		status, shapeSections = mnsUtils.validateAttrAndGet(builtGuides[0], "shapeSections", 16)
		linkChainShape = blkCtrlShps.ctrlCreate(
									controlShape = "circle",
									createBlkClassID = True, 
									createBlkCtrlTypeID = False, 
									scale = modScale * 2, 
									sections = shapeSections,
									alongAxis = 0, 
									side =builtGuides[0].side, 
									body = builtGuides[0].body + "ChainShape", 
									alpha = builtGuides[0].alpha, 
									id = builtGuides[0].id,
									color = blkUtils.getCtrlCol(builtGuides[0], rigTop),
									matchTransform = builtGuides[0].node,
									createSpaceSwitchGroup = False,
									createOffsetGrp = False
									)

		custGuides.append(linkChainShape)
		parentDict.update({linkChainShape: builtGuides[0]})
		
		handlePos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "ForwardDirection", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		pm.parent(handlePos.node, builtGuides[0].node)
		pm.makeIdentity(handlePos.node)
		handlePos.node.ty.set(10)
		pm.parent(handlePos.node, w = True)

		parentDict.update({handlePos: builtGuides[0]})
		custGuides.append(handlePos)

	return custGuides, parentDict

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core.prefixSuffix import GLOB_mnsJntStructDefaultSuffix
	from mansur.core import string as mnsString

	rootGuide = guides[0]
	relatedRootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(rootGuide))
	customGuides = blkUtils.getModuleDecendentsWildcard(guides[0], customGuidesOnly = True)
	returnData = {}

	softMod = kwargs.get("softMod", False)

	status, autoDrive = mnsUtils.validateAttrAndGet(rootGuide, "doAutoDrive", False)
	chainShape = None
	forwardDirCusGuide = None
	for cg in customGuides:
		if "chainshape" in cg.name.lower():
			chainShape = cg
		if "ForwardDirection_" in cg.node.nodeName():
			forwardDirCusGuide = cg
			if autoDrive: forwardDirCusGuide.node.v.set(True)
			else: forwardDirCusGuide.node.v.set(False)
	
	if chainShape:
		#get rotate mode
		status, rotationMode = mnsUtils.validateAttrAndGet(rootGuide, "rotationMode", 0)
		pocRotateMode = 2
		if rotationMode == 1: pocRotateMode = 0

		#first look for existing poc node, and if existing, delete it
		if not softMod: 
			outCons = chainShape.node.getShape().worldSpace[0].listConnections(d = True, s = False)
			if outCons:
				for o in outCons:
					if type(o) == pm.nodetypes.MnsPointsOnCurve:
						pm.delete(o)

			iLocsReturn = []
			nodesToDelete = []

			status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 1.0)
			status, numberOfLinks = mnsUtils.validateAttrAndGet(rootGuide, "numberOfLinks", 16)
			
			pocn = mnsNodes.mnsPointsOnCurveNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
											inputCurve = chainShape.node,
											inputUpCurve = None,
											buildOutputs = True,
											buildType = 4, #interpJointsType
											buildMode = 1,
											doScale = False,
											aimAxis = 1,
											upAxis = 0,
											doRotate = True,
											numOutputs = numberOfLinks,
											rotateMode = pocRotateMode
											)
			pocn["node"].node.closedShape.set(1)
			pocn["node"].node.cycle.set(1)
			pocn["node"].node.squashMode.set(4)
			iLocsReturn += pocn["samples"]
			blkUtils.connectSlaveToDeleteMaster(pocn["node"], rootGuide)
			origCurveAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "origPocn", value= "", replace = True)[0]
			pocn["node"].node.message >> origCurveAttr
			returnData = {"Main": iLocsReturn}

			#create a curve tweak node to generate the intermediate up curve
			status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 5.0)
			curveTweakNode = mnsNodes.mnsCurveTweakNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
											inputCurve = chainShape.node.worldSpace[0],
											buildOffsetCurve = True,
											offset = upCurveOffset,
											offsetBaseMatrix = rootGuide.node.worldMatrix[0],
											)
			curveTweakNode.node.outOffsetCurve >> pocn["node"].node.upCurve
			pm.refresh()

			upCurve = createUpCurveFromSamples(mansur, rootGuide, iLocsReturn, upCurveOffset)
			upCurve.node.worldSpace[0] >> pocn["node"].node.upCurve
			pm.delete(upCurve.node, curveTweakNode.node)

			#create the uOffset attribute
			mnsUtils.addAttrToObj(rootGuide.node, type = "enum", value = ["______"], name = "jointSpreadTweak", replace = True, locked = True)
			uOffsetAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "float", value = 0.0, name = "uOffset", replace = True)[0]
			status, reverseOffsetDirection = mnsUtils.validateAttrAndGet(rootGuide.node, "reverseOffsetDirection", False)
			multValue = 1.0
			if reverseOffsetDirection: multValue = -1.0
			mdlNode = mnsNodes.mdlNode(uOffsetAttr, multValue, pocn["node"].node.uOffset)

			return returnData
		else:
			outCons = chainShape.node.getShape().worldSpace[0].listConnections(d = True, s = False)
			if outCons:
				for o in outCons:
					if type(o) == pm.nodetypes.MnsCurveTweak:
						status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 5.0)
						o.offset.set(upCurveOffset)
					elif type(o) == pm.nodetypes.MnsPointsOnCurve:
						status, reverseOffsetDirection = mnsUtils.validateAttrAndGet(rootGuide.node, "reverseOffsetDirection", False)
						multValue = 1.0
						if reverseOffsetDirection: multValue = -1.0
						#get the mdl node and set
						inCons = o.uOffset.listConnections(s = True, d = False)
						for i in inCons:
							if type(i) == pm.nodetypes.MultDoubleLinear:
								i.input2.set(multValue)
						#set rotate mode
						o.rotateMode.set(pocRotateMode)
						
def jointStructureSoftMod(mansur, guides, mnsBuildModule = None, **kwargs):
	kwargs.update({"softMod": True})
	jointStructure(mansur, guides, mnsBuildModule, **kwargs)

def deconstruct(mansur, MnsBuildModule, **kwargs):
	"""deconstruct method implementation for linkChain.
	"""

	from mansur.block.core import blockUtility as blkUtils
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	customGuides = MnsBuildModule.cGuideControls
	rootGuide = MnsBuildModule.rootGuide
	relatedRootJnt = mnsUtils.validateNameStd(rootGuide.node.jntSlave.get())
	iLocs = [i.node for i in blkUtils.getModuleInterpJoints(rootGuide)]

	chainShape = None
	for cg in customGuides:
		if "chainshape" in cg.name.lower():
			chainShape = cg

	if chainShape:
		status, pocNode = mnsUtils.validateAttrAndGet(rootGuide, "origPocn", None)
		if pocNode:
			chainShape.node.getShape().worldSpace[0] >> pocNode.curve
			pocNode.mode.set(1)
			pocNode.resetScale.set(1)
			pocNode.doScale.set(0)

			#create a curve tweak node to generate the intermediate up curve
			status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 5.0)
			curveTweakNode = mnsNodes.mnsCurveTweakNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body, 
											inputCurve = chainShape.node.worldSpace[0],
											buildOffsetCurve = True,
											offset = upCurveOffset,
											offsetBaseMatrix = rootGuide.node.worldMatrix[0],
											)
			curveTweakNode.node.outOffsetCurve >> pocNode.upCurve
			pm.dgdirty(pocNode)
			pm.refresh()

			upCurve = createUpCurveFromSamples(mansur, rootGuide, iLocs, upCurveOffset)
			
			upCurve.node.worldSpace[0] >> pocNode.upCurve
			pm.dgdirty(pocNode)
			pm.refresh()
			
			pm.delete(upCurve.node, curveTweakNode.node)

			

			outCons = rootGuide.node.uOffset.listConnections(d = True, s = False)
			for i in outCons:
				if type(i) == pm.nodetypes.MultDoubleLinear:
					i.output >> pocNode.uOffset

			