"""Author: Asaf Ben-Zur
Best used for: Bird Wings
This module is designed for birds (feathered) wings.
This is a compound module.
The main module is based on the limb module, including most of it's features.
On top of the main limb module, there is a compound FK chain modules extending from each of the main modules main guides, to create a global feathers silhouette control.
Out of these compounds, a grid of interp-joints is created to control the shape's deformation, using mnsPointOnCuveNode as a driver.
As a bird wing is incredibly complex, controlling it precisely is incredibly difficult.
With that in mind, the grid of interp joints is designed to control the overall shape of the feathers as a group, mid-controls to curl them as a group, as well as control each feather row individually.
Use featherJoints attribute to define the number of feathers along the wings main skeleton.
Post joint-struct creation, use the custom position adjustment attribute on the root-guide to adjust the position of the joint grid to match your needs.
This module also contains multiple features to make animation even better:
Feathers spring, global wave control, individual feather control, bendy limbs, extension-to-look-at for easy wing fold control.
"""



from maya import cmds
import pymel.core as pm


def getNumSections(tweakersPerSection, doTweakers = False, asBatWing = False):
	sections = 4
	if doTweakers and not asBatWing:
		sections = (tweakersPerSection * 4) + 4
	return sections

def collectFeathParamAdjustValues(rootGuide):
	if rootGuide:
		dataCollect = {}
		attrs = rootGuide.node.listAttr(ud = True, s = True)
		for attr in attrs:
			if "featherPos" in attr.attrName() or "aimPos" in attr.attrName():
				dataCollect[attr.attrName()] = attr.get()
		return dataCollect
				   
def attempFeatherParamAdjustRemap(mansur, rootGuide = None, previousValues = {}):
	if rootGuide and previousValues:
		from mansur.core import utility as mnsUtils

		status, previousNumTweakers = mnsUtils.validateAttrAndGet(rootGuide, "previousNumTweakers", 0)
		if status:
			currentNumTweakers = 0
			status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
			if doTweakers:
				status, currentNumTweakers = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
			if currentNumTweakers != previousNumTweakers:
				for attrName in previousValues:
					status, attr = mnsUtils.validateAttrAndGet(rootGuide, attrName, 1, returnAttrObject = True)
					if status:
						oldValue = previousValues[attrName]
						newValue = (oldValue / (previousNumTweakers + 1)) * (currentNumTweakers + 1)
						attr.set(newValue)
			mnsUtils.setAttr(rootGuide.node.previousNumTweakers, currentNumTweakers)

def construct(mansur, MnsBuildModule, **kwargs):
	########### local library imports ###########
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	########### global module objects collect ###########
	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(MnsBuildModule.rootGuide))
	rootGuide = MnsBuildModule.rootGuide
	allGuides = [MnsBuildModule.rootGuide] + MnsBuildModule.guideControls
	moduleTopGrp = MnsBuildModule.moduleTop
	animGrp = MnsBuildModule.animGrp
	animStaticGrp = MnsBuildModule.animStaticGrp
	rigComponentsGrp = MnsBuildModule.rigComponentsGrp
	attrHost = MnsBuildModule.attrHostCtrl or animGrp
	customGuides = MnsBuildModule.cGuideControls

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)
	modScale /= 2

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########

	#return declares
	primaryCtrls = []
	secondaryCtrls = []
	tertiaryControls = []
	spaceSwitchCtrls = []
	internalSpacesDict = {}

	##collect costum guides
	customGuides = MnsBuildModule.cGuideControls
	poleVecGuide = None
	poleVecGuide = [g for g in customGuides if "PoleVector" in g.name]
	if poleVecGuide: poleVecGuide = poleVecGuide[0]

	##collect guide jnts
	rootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[0]))	
	if rootJnt: mnsUtils.jointOrientToRotation(rootJnt.node)
	midJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[1]))	
	endJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[2]))	

	#collect global attrs
	status, scaleMode = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "scaleMode", 2)
	status, squashMode = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "squashMode", 0)

	status, rootControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "rootControlShape", "lightSphere")
	status, ikHandleControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ikHandleControlShape", "square")
	status, poleVectorControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "poleVectorControlShape", "diamond")
	status, fkControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "fkControlShape", "hexagon")
	status, tertiariesControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "tertiariesControlShape", "flatDiamond")
	status, asBatWing = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "asBatWing", False)

	#collections declare
	rscNodes = []

	#get poc node
	globScaleAttr = blkUtils.getGlobalScaleAttrFromTransform(animGrp)
	
	psocn, feathMainPocn = None, None
	interpLocs = [f for f in blkUtils.getModuleInterpJoints(MnsBuildModule.rootGuide) if "Main" in f.name]
	if interpLocs:
		iLoc = interpLocs[0]
		inConnections = iLoc.node.t.listConnections(s = True, d = False)
		if inConnections:
			inCon = inConnections[0]
			if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
				psocn = inCon
	if psocn: globScaleAttr >> psocn.globalScale

	#get feathers row A poc node
	if psocn:
		inConnections = psocn.curve.listConnections(s = True, d = False)
		if inConnections:
			inCon = inConnections[0]
			if type(inCon) == pm.nodetypes.MnsResampleCurve:
				outConnections = inCon.outCurve.listConnections(s = False, d = True)
				if outConnections:
					for con in outConnections:
						if type(con) == pm.nodetypes.MnsPointsOnCurve and "Feather" in con.nodeName():
							feathMainPocn = con
							break

	#get feathers poc nodes and connect glob scale
	status, featherFKSections = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "featherFKSections", 3)
	for j in range(featherFKSections):
		rowAlpha = mnsUtils.convertIntToAlpha(j +1).upper()
		attrName = "feathers" + rowAlpha + "_pocn"
		status, pocNodeFeath = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, attrName, None) 
		if pocNodeFeath:
			globScaleAttr >> pocNodeFeath.globalScale

	#create ik connectors
	ikConnectorsGroup = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IkLocs", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	ikConnectorsGroup.node.v.set(0)
	pm.parent(ikConnectorsGroup.node, rigComponentsGrp.node)
	rootLoc = mnsUtils.createNodeReturnNameStd(parentNode = ikConnectorsGroup, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RootConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)
	midLoc = mnsUtils.createNodeReturnNameStd(parentNode = rootLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)
	endLoc = mnsUtils.createNodeReturnNameStd(parentNode = midLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EndConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)

	##create ik controls group
	ikControlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IkControls", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	
	###lowest level tweakers
	jntTweakersGrp = mnsUtils.createNodeReturnNameStd(parentNode = ikControlsGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "JntTweakers", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	rootTweak = blkCtrlShps.ctrlCreate(parentNode = jntTweakersGrp, 
										controlShape = tertiariesControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 2, 
										scale = modScale, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "RootTweak", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = rootJnt.node, 
										createOffsetGrp = True, 
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)
	ikSolverMesAttr = mnsUtils.addAttrToObj([rootTweak.node], type = "message", name = "ikSolver", value= "", replace = True)[0]
	
	tertiaryControls.append(rootTweak)
	rootOffsetGrp =blkUtils.getOffsetGrpForCtrl(rootTweak)

	midTweak = blkCtrlShps.ctrlCreate(parentNode = jntTweakersGrp, 
										controlShape = ikHandleControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 1, 
										scale = modScale * 0.7, 
										alongAxis = 1,  
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "MidTweak", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = midJnt.node, 
										createOffsetGrp = True, 
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)

	midOffsetGrp =blkUtils.getOffsetGrpForCtrl(midTweak)
	secondaryCtrls.append(midTweak)
	midTweakModGroup = mnsUtils.createOffsetGroup(midTweak, type = "modifyGrp")
	ikMidAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "ikMid", value= "", replace = True)[0]
	midTweak.node.message >> ikMidAttr

	endTweak = blkCtrlShps.ctrlCreate(parentNode = jntTweakersGrp,
										controlShape = tertiariesControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 2, 
										scale = modScale, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "EndTweak", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = endJnt.node, 
										createOffsetGrp = True, 
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)
	footSpaceSourceAttr = mnsUtils.addAttrToObj([rootTweak.node], type = "message", name = "footSpaceSource", value= "", replace = True)[0]
	secondaryCtrls.append(endTweak)
	endTweak.node.message >> footSpaceSourceAttr
	ikEndAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "ikEnd", value= "", replace = True)[0]
	endTweak.node.message >> ikEndAttr

	limbEndTweakAttr = mnsUtils.addAttrToObj([rootTweak.node], type = "message", name = "endTweak", value= "", replace = True)[0]
	endTweak.node.message >> limbEndTweakAttr 

	tertiaryControls.append(endTweak)
	endOffsetGrp = blkUtils.getOffsetGrpForCtrl(endTweak)
	endModGroup = mnsUtils.createOffsetGroup(endTweak, type = "modifyGrp")

	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [rootOffsetGrp.node], sources = [rootLoc.node], connectScale = True)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [midOffsetGrp.node], sources = [midLoc.node], connectScale = True)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [endOffsetGrp.node], sources = [endLoc.node], connectScale = False)

	### root ctrl
	rootCtrl = blkCtrlShps.ctrlCreate(controlShape = rootControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 1.5, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "Root", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = rootJnt.node, 
										createSpaceSwitchGroup = True, 
										parentNode = animGrp,
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)
	primaryCtrls.append(rootCtrl)

	###ik handle control
	status, ikHandleMatchOrient = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "iKHandleMatchOrient", False)
	if ikHandleMatchOrient: ikHandleMatchOrient = mnsUtils.validateNameStd(ikHandleMatchOrient)

	ikCtrl = blkCtrlShps.ctrlCreate(parentNode = animStaticGrp, 
									controlShape = ikHandleControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 1.5, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "IkTarget", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = endJnt.node, 
									createOffsetGrp = True,
									createSpaceSwitchGroup = True,
									symmetryType = symmetryType,
									doMirror = not ikHandleMatchOrient,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = endJnt)

	ikCtrl.node.sx >> ikCtrl.node.sy
	ikCtrl.node.sx >> ikCtrl.node.sz
	primaryCtrls.append(ikCtrl)
	spaceSwitchCtrls.append(ikCtrl)
	internalSpacesDict.update({ikCtrl.name: [rootCtrl.node]})
	ikCtrlAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "ikCtrl", value= "", replace = True)[0]
	ikCtrl.node.message >> ikCtrlAttr 

	##match orient feature
	if ikHandleMatchOrient:
		ikHandleOffsetGrp = blkUtils.getOffsetGrpForCtrl(ikCtrl, type = "offsetGrp")
		if ikHandleOffsetGrp:
			pm.delete(pm.orientConstraint(ikHandleMatchOrient.node, ikHandleOffsetGrp.node))

	### poleVector
	poleVector = blkCtrlShps.ctrlCreate(parentNode = ikControlsGrp, 
										controlShape = poleVectorControlShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 0.7, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "PoleVector", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = poleVecGuide.node, 
										createSpaceSwitchGroup = True,
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial,
										offsetRigMaster = rootJnt)

	primaryCtrls.append(poleVector)
	spaceSwitchCtrls.append(poleVector)
	internalSpacesDict.update({poleVector.name: [rootCtrl.node, ikCtrl.node]})
	poleVectorAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "poleVector", value= "", replace = True)[0]
	poleVector.node.message >> poleVectorAttr 

	### Extension lookAt
	status, extensionLookAtControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "extensionLookAtControlShape", "lightPin")
	extensionLookAt = blkCtrlShps.ctrlCreate(parentNode = rootCtrl, 
										controlShape = extensionLookAtControlShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 0.7, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "ExtensionLookAt", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = poleVecGuide.node, 
										createSpaceSwitchGroup = True,
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)

	primaryCtrls.append(extensionLookAt)
	spaceSwitchCtrls.append(extensionLookAt)
	internalSpacesDict.update({extensionLookAt.name: [rootCtrl.node, ikCtrl.node]})
	extensionLookAtAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "extensionLookAt", value= "", replace = True)[0]
	extensionLookAt.node.message >> extensionLookAtAttr 

	##FK controls
	status, FKSymmetryType = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "FKSymmetryType", 0)
	fkRoot = blkCtrlShps.ctrlCreate(parentNode = rootCtrl, 
									controlShape = fkControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 2, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "FK", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = rootJnt.node, 
									createOffsetGrp = True,
									symmetryType = FKSymmetryType,
									doMirror = True,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = rootJnt)
	primaryCtrls.append(fkRoot)
	FKRootAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fkRoot", value= "", replace = True)[0]
	fkRoot.node.message >> FKRootAttr 

	fkMid = blkCtrlShps.ctrlCreate(parentNode = fkRoot, 
									controlShape = fkControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 2, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "FK", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id + 1,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = midJnt.node, 
									createOffsetGrp = True,
									symmetryType = FKSymmetryType,
									doMirror = True,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = midJnt)
	primaryCtrls.append(fkMid)
	FKMidAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fkMid", value= "", replace = True)[0]
	fkMid.node.message >> FKMidAttr 

	fkEnd = blkCtrlShps.ctrlCreate(parentNode = fkMid, 
									controlShape = fkControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 2, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "FK", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id + 2,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = endJnt.node, 
									createOffsetGrp = True,
									symmetryType = FKSymmetryType,
									doMirror = True,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = endJnt)
	primaryCtrls.append(fkEnd)
	FKEndAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fkEnd", value= "", replace = True)[0]
	fkEnd.node.message >> FKEndAttr 

	fngs = []

	if len(allGuides) > 3:
		for fngIdx in range(4, (len(allGuides) + 1)): 
			fngJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[fngIdx - 1]))	

			#additional Fingers
			parentNode = rootCtrl
			if fngs: parentNode = fngs[-1]["ctrl"]

			fkFing = blkCtrlShps.ctrlCreate(parentNode = parentNode, 
											controlShape = fkControlShape, 
											createBlkClassID = True, 
											createBlkCtrlTypeID = True, 
											blkCtrlTypeID = 0, 
											scale = modScale * 2, 
											alongAxis = 1, 
											side = MnsBuildModule.rootGuide.side, 
											body = MnsBuildModule.rootGuide.body + "FK", 
											alpha = MnsBuildModule.rootGuide.alpha, 
											id = MnsBuildModule.rootGuide.id + (fngIdx - 1),
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = fngJnt.node, 
											createOffsetGrp = True,
											symmetryType = FKSymmetryType,
											doMirror = True,
											isFacial = MnsBuildModule.isFacial)
			primaryCtrls.append(fkFing)
			fngDict = {"idx": fngIdx, "jnt": fngJnt, "ctrl": fkFing}
			fngs.append(fngDict)

	#ikSolver Node
	ikSolverNode = mnsNodes.mnsIKSolver(outputRoot = rootLoc.node,
										outputMid = midLoc.node,
										outputEnd = endLoc.node,
										poleVector = poleVector.node,
										rootPos = allGuides[0].node, 
										midPos = allGuides[1].node, 
										endPos = allGuides[2].node,
										limbRoot = rootCtrl.node,
										ikHandle = ikCtrl.node,
										fkRoot = fkRoot,
										fkMid = fkMid,
										fkEnd = fkEnd,
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "IKSolver", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop))
	ikSolverNode.node.message >> ikSolverMesAttr

	#create bridge FK locs (solving mirroring issues)
	fkConnectorsGroup = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "FkLocs", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	fkConnectorsGroup.node.v.set(0)
	pm.parent(fkConnectorsGroup.node, rigComponentsGrp.node)

	fkRootLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkConnectorsGroup, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RootFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(rootLoc.node, fkRootLoc.node))
	pm.delete(pm.scaleConstraint(rootLoc.node, fkRootLoc.node))
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkRootLoc.node], sources = [fkRoot.node], connectScale = True, maintainOffset = True)
	fkRootLoc.node.worldMatrix[0] >> ikSolverNode.node.rootFK

	fkMidLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkRootLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(midLoc.node, fkMidLoc.node))
	pm.delete(pm.scaleConstraint(midLoc.node, fkMidLoc.node))
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkMidLoc.node], sources = [fkMid.node], connectScale = True, maintainOffset = True)
	fkMidLoc.node.worldMatrix[0] >> ikSolverNode.node.midFK

	fkEndLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkMidLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EndFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(endLoc.node, fkEndLoc.node))
	pm.delete(pm.scaleConstraint(endLoc.node, fkEndLoc.node))
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkEndLoc.node], sources = [fkEnd.node], connectScale = True, maintainOffset = False)
	fkEndLoc.node.worldMatrix[0] >> ikSolverNode.node.endFK

	mnsUtils.zeroJointOrient(fkRootLoc.node)

	#create ikfk blend attr
	status, blendDefault = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ikFkBlendDefault", 0.0)
	fkIkBlendAttr = mnsUtils.addAttrToObj([attrHost.node], type = "float", value = blendDefault, name = "ikFkBlend", replace = True, max = 1.0, min = 0.0)[0]
	fkIkBlendAttr >> ikSolverNode.node.blend
	blendAttrHolder = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "blendAttrHolder", value= "", replace = True)[0]
	attrHost.node.message >> blendAttrHolder

	#create root twist mute attribute
	muteRootTwistAttr = mnsUtils.addAttrToObj([attrHost.node], type = "float", value = 1.0, name = "muteRootTwist", replace = True, max = 1.0, min = 0.0)[0]

	#connect twekers to pocn as tweakers
	tweakerIndex = 0
	tweakPos = 0.0
	for tweakCtrl in [rootTweak, midTweak, endTweak]:
		mnsUtils.addAttrToObj([tweakCtrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
		falloffAttr = mnsUtils.addAttrToObj([tweakCtrl.node], type = "float", value = 0.5, name = "scaleFalloff", replace = True, min = 0.01)[0]
		falloffAttr >> psocn.customPosition[tweakerIndex].falloff

		tweakCtrl.node.sy >> psocn.customPosition[tweakerIndex].scaleAim
		tweakCtrl.node.sz >> psocn.customPosition[tweakerIndex].scaleUp
		tweakCtrl.node.sx >> psocn.customPosition[tweakerIndex].tertiaryScale
		psocn.customPosition[tweakerIndex].uPosition.set(tweakPos)

		tweakPos += 0.5
		tweakerIndex += 1


	#connect IKTarget as tweaker with mute
	tweakPos = 1.0
	for tweakCtrl in [ikCtrl]:
		mnsUtils.addAttrToObj([tweakCtrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
		falloffAttr = mnsUtils.addAttrToObj([tweakCtrl.node], type = "float", value = 0.5, name = "scaleFalloff", replace = True, min = 0.01)[0]
		falloffAttr >> psocn.customPosition[tweakerIndex].falloff

		tweakCtrl.node.sy >> psocn.customPosition[tweakerIndex].scaleAim
		tweakCtrl.node.sz >> psocn.customPosition[tweakerIndex].scaleUp
		tweakCtrl.node.sx >> psocn.customPosition[tweakerIndex].tertiaryScale
		psocn.customPosition[tweakerIndex].uPosition.set(tweakPos)

		revNode = mnsNodes.reverseNode([ikSolverNode.node.blend,0,0], 
							None,
							side = animGrp.side, 
							body = animGrp.body + "IkFk", 
							alpha = animGrp.alpha, 
							id = animGrp.id)

		blendNode = mnsNodes.blendColorsNode(tweakCtrl.node.s, 
							[1.0, 1.0, 1.0],
							revNode.node.outputX,
							[psocn.customPosition[tweakerIndex].scaleAim, psocn.customPosition[tweakerIndex].scaleUp, psocn.customPosition[tweakerIndex].tertiaryScale],
							side = animGrp.side, 
							body = animGrp.body + "HandleScalMute", 
							alpha = animGrp.alpha, 
							id = animGrp.id)
		blkUtils.connectSlaveToDeleteMaster(blendNode, animGrp)
		tweakerIndex += 1

	#get original btc node and crs nodes
	primBtcNode, resampleCurve, resampleCurveOffset = None, None, None
	relatedRootJnt = mnsUtils.validateNameStd(MnsBuildModule.guideControls[0].node.jntSlave.get())
	outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
	if outConnections:
		for con in outConnections: 
			if type(con) == pm.nodetypes.MnsBuildTransformsCurve and "Main" in con.nodeName():
				primBtcNode = con

				#get rasampleCurves
				outConnections = primBtcNode.outCurve.listConnections(s = False, d = True)
				if outConnections:
					for con in outConnections: 
						if type(con) == pm.nodetypes.MnsResampleCurve:
							resampleCurve = con
							rscNodes.append(resampleCurve)

				outConnections = primBtcNode.outOffsetCurve.listConnections(s = False, d = True)
				if outConnections:
					for con in outConnections: 
						if type(con) == pm.nodetypes.MnsResampleCurve:
							resampleCurveOffset = con		
							rscNodes.append(resampleCurveOffset)		
				break

	#create scale mode extra atributes
	host = attrHost.node
	mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "SETTINGS", replace = True, locked = True)
	
	#scaleMode
	scaleModeAttr = mnsUtils.addAttrToObj([host], type = "enum", value = ["curveLengthIsDifferentThenCreation", "curveLengthChanges", "always"], enumDefault = psocn.scaleMode.get(), name = "squashWhen", replace = True)[0]
	scaleModeAttr >> psocn.scaleMode

	#squashMode
	squashModeAttr = mnsUtils.addAttrToObj([host], type = "enum", value = ["squashStretch", "squash", "stretch", "unifom", "none"], enumDefault = psocn.squashMode.get(), name = "squashMode", replace = True)[0]
	squashModeAttr >> psocn.squashMode

	#scaleMin
	scaleMinAttr = mnsUtils.addAttrToObj([host], type = "float", value = 0.8, name = "scaleMin", replace = True, min = 0.001, max = 1.0)[0]
	scaleMinAttr >> psocn.scaleMin
	
	#scaleMax
	scaleMaxAttr = mnsUtils.addAttrToObj([host], type = "float", value = 1.2, name = "scaleMax", replace = True, min = 1.0)[0]
	scaleMaxAttr >> psocn.scaleMax
	
	#squashFactor
	squashFactorAttr = mnsUtils.addAttrToObj([host], type = "float", value = 1.1, name = "squashFactor", replace = True)[0]
	squashFactorAttr >> psocn.squashFactor
	
	#squashPos
	squashPosAttr = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "squashPos", replace = True, min = 0.0, max = 1.0)[0]
	squashPosAttr >> psocn.squashPos

	#bendy limbs
	TweakPocn = None
	status, doTweakers = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doTweakers", False)
	
	if doTweakers:
		if primBtcNode:
			status, tweakersPerSection = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "tweakersPerSection", 1)
			status, tweakControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "tweakControlShape", "dialSquare")
			status, tweakSymmetryType = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "tweakersSymmetryType", 0)
			status, tweakersChannelControl = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "tweakersChannelControl", {})
			if status: tweakersChannelControl = mnsUtils.splitEnumAttrToChannelControlList("tweakersChannelControl", MnsBuildModule.rootGuide.node)

			#create tweakers group
			tweakerGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "BendyTweakers", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
			numTweakControls = getNumSections(tweakersPerSection, doTweakers, asBatWing) + 1

			tweakerControls = []
			twekersOffsets = []
			
			for k in range(numTweakControls):
				tweakerCtrl = blkCtrlShps.ctrlCreate(parentNode = tweakerGrp, 
										controlShape = tweakControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 1, 
										scale = modScale * 1.5, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "BendyTweaker", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = k + 1,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										createOffsetGrp = True,
										symmetryType = tweakSymmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)
				tweakerControls.append(tweakerCtrl)
				secondaryCtrls.append(tweakerCtrl)
				twekersOffsets.append(blkUtils.getOffsetGrpForCtrl(tweakerCtrl))


				#tweakerCtrl.node.sx >> tweakerCtrl.node.sy
				tweakerCtrl.node.sx >> tweakerCtrl.node.sz

				mnsUtils.addAttrToObj([tweakerCtrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
				falloffAttr = mnsUtils.addAttrToObj([tweakerCtrl.node], type = "float", value = 0.5, name = "scaleFalloff", replace = True, min = 0.01)[0]

				falloffAttr >> psocn.customPosition[tweakerIndex].falloff
				#tweakerCtrl.node.sy >> psocn.customPosition[tweakerIndex].scaleAim
				tweakerCtrl.node.sz >> psocn.customPosition[tweakerIndex].scaleUp
				tweakerCtrl.node.sx >> psocn.customPosition[tweakerIndex].tertiaryScale
				tweakPos = (1.0 / float(numTweakControls - 1)) * float(k)
				positionAttr = mnsUtils.addAttrToObj([tweakerCtrl.node], type = "float", value = tweakPos, name = "scalePosition", replace = True, min = 0.01)[0]
				positionAttr >> psocn.customPosition[tweakerIndex].uPosition

				#if k == 0 or k == (numTweakControls - 1) or k == (numTweakControls - 1) / 2:
				#	pass

				tweakerIndex += 1


			#create new pocn
			TweakPocn = mnsNodes.mnsPointsOnCurveNode(
											side = MnsBuildModule.rootGuide.side, 
											alpha = MnsBuildModule.rootGuide.alpha, 
											id = MnsBuildModule.rootGuide.id, 
											body = MnsBuildModule.rootGuide.body + "TweakersPoc", 
											inputCurve = resampleCurve.outCurve,
											inputUpCurve = resampleCurveOffset.outCurve,
											buildOutputs = False,
											buildMode = 0,
											doScale = True,
											aimAxis = 1,
											upAxis = 0,
											numOutputs = numTweakControls,
											transforms = twekersOffsets
											)
			blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> TweakPocn["node"].node.globalScale

			scaleModeAttr >> TweakPocn["node"].node.scaleMode
			squashModeAttr >> TweakPocn["node"].node.squashMode
			scaleMinAttr >> TweakPocn["node"].node.scaleMin
			scaleMaxAttr >> TweakPocn["node"].node.scaleMax
			squashFactorAttr >> TweakPocn["node"].node.squashFactor
			squashPosAttr >> TweakPocn["node"].node.squashPos

			#create new btc
			status, offsetX = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "offsetX", 10.0)
			status, offsetY = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "offsetY", 0.0)
			status, offsetZ = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "offsetZ", 0.0)

			status, negateOffsetOnSymmetry = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "negateOffsetOnSymmetry", False)
			if negateOffsetOnSymmetry and MnsBuildModule.rootGuide.side == "r": 
				offsetX *= -1
				offsetY *= -1
				offsetZ *= -1

			btcNode = mnsNodes.mnsBuildTransformsCurveNode(
									side = MnsBuildModule.rootGuide.side, 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id, 
									body = MnsBuildModule.rootGuide.body + "TweakBtc", 
									transforms = tweakerControls, 
									deleteCurveObjects = True, 
									tangentDirection = 2, 
									buildOffsetCurve = True,
									degree = 1,
									offsetX = offsetX,
									offsetY = offsetY,
									offsetZ = offsetZ)

			btcNode["node"].node.outCurve >> psocn.curve
			btcNode["node"].node.outOffsetCurve >> psocn.upCurve

			#connect feathers main poc as well
			if feathMainPocn:
				btcNode["node"].node.outCurve >> feathMainPocn.curve
				btcNode["node"].node.outOffsetCurve >> feathMainPocn.upCurve

			tweakCurveBaseBtc = mnsNodes.mnsBuildTransformsCurveNode(
									side = MnsBuildModule.rootGuide.side, 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id, 
									body = MnsBuildModule.rootGuide.body + "TweakCurveBase", 
									transforms = twekersOffsets, 
									deleteCurveObjects = True, 
									tangentDirection = 1, 
									buildOffsetCurve = False,
									degree = 3,
									buildMode = 2)
			blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> tweakCurveBaseBtc["node"].node.globalScale

			tweakCurveBtc = mnsNodes.mnsBuildTransformsCurveNode(
									side = MnsBuildModule.rootGuide.side, 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id, 
									body = MnsBuildModule.rootGuide.body + "TweakCurveDyn", 
									transforms = twekersOffsets, 
									deleteCurveObjects = True, 
									tangentDirection = 1, 
									buildOffsetCurve = False,
									degree = 3,
									buildMode = 2)
			blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> tweakCurveBtc["node"].node.globalScale

			for l in range(numTweakControls):
				if l != 0 and l != (numTweakControls - 1) and l != (numTweakControls - 1) / 2:
					tweakRefGrp = mnsUtils.createNodeReturnNameStd(parentNode = animGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "tweakCurve", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
					pm.delete(pm.parentConstraint(tweakerControls[l].node, tweakRefGrp.node))
					pointCns = mnsNodes.mayaConstraint([twekersOffsets[l].node], tweakRefGrp.node, type = "point", maintainOffset = False)
					pointCns = mnsNodes.mayaConstraint([tweakerControls[l].node], tweakRefGrp.node, type = "orient", maintainOffset = False)
					pointCns = mnsNodes.mayaConstraint([tweakerControls[l].node], tweakRefGrp.node, type = "scale", maintainOffset = False)
					tweakRefGrp.node.v.set(False)
					tweakRefGrp.node.worldMatrix[0] >> tweakCurveBtc["node"].node.attr("transforms[" + str(l) + "].matrix")

			tweakCurveBaseBtc["node"].node.outCurve >> btcNode["node"].node.tweakCurveBase
			tweakCurveBtc["node"].node.outCurve >> btcNode["node"].node.tweakCurve
			btcNode["node"].node.resample.set(True)
			btcSubsteps = getNumSections(tweakersPerSection, doTweakers, asBatWing) + 1
			btcNode["node"].node.substeps.set(btcSubsteps)

			#add etxra attributes
			status, createExtraAttrs = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "createExtraAttributes", True)
			if createExtraAttrs:
				host = attrHost.node
				targetNode = TweakPocn["node"].node

				#divider
				mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "ExtraTweaks", replace = True, locked = True)
				
				#uScaleMidInv
				uScaleMidInvAttr = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "shiftFromMid", replace = True, min = -1.0, max = 1.0)[0]
				uScaleMidInvAttr >> targetNode.uScaleMidInverse

				#waveAimAngle
				waveAimAngle = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "twistWave", replace = True)[0]
				waveAimAngle >> targetNode.waveAimAngle

				#waveAimPhase
				waveAimPhase = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "twistWavePhase", replace = True)[0]
				waveAimPhase >> targetNode.twistAimWavePhase

	#connect vis chennels
	ikSolverNode.node.ikVis >> ikCtrl.node.v
	ikSolverNode.node.ikVis >> poleVector.node.v
	ikSolverNode.node.fkVis >> fkRoot.node.v
	ikSolverNode.node.fkVis >> fkMid.node.v
	ikSolverNode.node.fkVis >> fkEnd.node.v

	#connect ik target to end connector and FK end control
	sources = [ikCtrl, fkEnd]
	cnsSources = []
	for source in sources:
		refLoc = mnsUtils.createNodeReturnNameStd(side = source.side, body = source.body + "FkConRef", alpha = source.alpha, id = source.id, buildType = "locator", incrementAlpha = False)
		pm.parent(refLoc.node, source.node)
		pm.delete(pm.parentConstraint(endModGroup.node, refLoc.node))
		pm.delete(pm.scaleConstraint(endModGroup.node, refLoc.node))
		refLoc.node.v.set(False)
		refLoc.node.v.setLocked(True)
		mnsUtils.lockAndHideAllTransforms(refLoc.node, lock = True)
		cnsSources.append(refLoc.node)

	orientCns = mnsNodes.mayaConstraint(cnsSources, endModGroup.node, type = "orient")
	orientCns.node.interpType.set(0)
	scaleCns = mnsNodes.mayaConstraint(cnsSources, endModGroup.node, type = "scale")
	revNode = mnsNodes.reverseNode([fkIkBlendAttr,0,0], 
								None,
								side = animGrp.side, 
								body = animGrp.body + "IkFk", 
								alpha = animGrp.alpha, 
								id = animGrp.id)
	for cns in [orientCns, scaleCns]:
		revNode.node.outputX >> cns.node.attr(cnsSources[0].nodeName() + "W0")
		fkIkBlendAttr >> cns.node.attr(cnsSources[1].nodeName() + "W1")

	#pocn connections
	if psocn:	
		status, scaleMode = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "scaleMode", 2)
		status, squashMode = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "squashMode", 0)
		
		scaleModeAttr.set(scaleMode)
		squashModeAttr.set(squashMode)

		psocn.doScale.set(1)
		psocn.resetScale.set(1)

	#create ik extra attributes
	devider = mnsUtils.addAttrToObj([ikCtrl.node], type = "enum", value = ["______"], name = "IkAttributes", replace = True)
	stretchLimitAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = allGuides[0].node.stretchLimit.get(), name = "stretchLimit", replace = True, min = 1.0)[0]
	stretchLimitAttr >> ikSolverNode.node.stretchLimit
	rollAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = 0.0, name = "roll", replace = True)[0]
	rollAttr >> ikSolverNode.node.roll
	slideAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = 0.0, name = "slide", replace = True, min = -1.0, max = 1.0)[0]
	slideAttr >> ikSolverNode.node.slide
	softnessAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = allGuides[0].node.softness.get(), name = "softness", replace = True, min = 0.0, max = 1.0)[0]
	softnessAttr >> ikSolverNode.node.softness
	
	#pin mid
	midTweakRef = blkCtrlShps.ctrlCreate(parentNode = midOffsetGrp, 
										controlShape = "circle", 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 1, 
										ctrlType = "techCtrl",
										scale = modScale * 0.7, 
										alongAxis = 1,  
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "MidTweakRef", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = midTweak.node, 
										createOffsetGrp = False,
										isFacial = MnsBuildModule.isFacial)
	pm.delete(midTweakRef.node.getShapes())
	pinMidAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = allGuides[0].node.softness.get(), name = "pinMidToPoleVec", replace = True, min = 0.0, max = 1.0)[0]
	pointConMid = pm.pointConstraint(midTweakRef.node, poleVector.node, midTweakModGroup.node, name = midTweakModGroup.node.nodeName().replace("_modifyGrp", "_pntCns"))
	pinMidAttr >> pointConMid.attr(poleVector.node + "W1")
	mnsNodes.reverseNode([pinMidAttr, None, None], [pointConMid.attr(midTweakRef.node + "W0"), None, None])

	#create match refs
	#create pole vector reference
	pvRefLoc = mnsUtils.createNodeReturnNameStd(side = source.side, body = source.body + "PoleVecRef", alpha = source.alpha, id = source.id, buildType = "locator", incrementAlpha = False)
	pm.parent(pvRefLoc.node, fkMid.node)
	pm.delete(pm.parentConstraint(poleVector.node, pvRefLoc.node))
	pm.delete(pm.scaleConstraint(poleVector.node, pvRefLoc.node))
	pvRefLoc.node.v.set(False)
	poleVectorRefAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "poleVectorRef", value= "", replace = True)[0]
	pvRefLoc.node.message >> poleVectorRefAttr 

	ikCtrlRef = mnsUtils.createNodeReturnNameStd(side = source.side, body = source.body + "IkCtrlRef", alpha = source.alpha, id = source.id, buildType = "locator", incrementAlpha = False)
	pm.parent(ikCtrlRef.node, fkEnd.node)
	pm.delete(pm.parentConstraint(ikCtrl.node, ikCtrlRef.node))
	pm.delete(pm.scaleConstraint(ikCtrl.node, ikCtrlRef.node))
	ikCtrlRef.node.v.set(False)
	ikCtrlRefAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "ikCtrlRef", value= "", replace = True)[0]
	ikCtrlRef.node.message >> ikCtrlRefAttr 

	#fk refs
	mainJnts = [rootJnt, midJnt, endJnt]
	names = ["Root", "Mid", "End"]
	fkRefs = []
	for k, fkCtrl in enumerate([fkRoot, fkMid, fkEnd]):
		fkRefGrp = mnsUtils.createNodeReturnNameStd(parentNode = rigComponentsGrp, side = fkCtrl.side, body = fkCtrl.body + "RefOffset", alpha = fkCtrl.alpha, id = fkCtrl.id, buildType = "group", incrementAlpha = False)
		fkRefGrp.node.v.set(False)
		fkRef = mnsUtils.createNodeReturnNameStd(parentNode = fkRefGrp, side = fkCtrl.side, body = fkCtrl.body + "Ref", alpha = fkCtrl.alpha, id = fkCtrl.id, buildType = "locator", incrementAlpha = False)
		fkRefs.append(fkRef)
		mnsNodes.mnsMatrixConstraintNode(side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id, targets = [fkRefGrp.node], sources = [mainJnts[k].node], connectScale = True)
		pm.matchTransform(fkRef.node, fkCtrl.node)

		FKAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fk" + names[k] + "Ref", value= "", replace = True)[0]
		fkRef.node.message >> FKAttr 

	#transfer authority
	blkUtils.transferAuthorityToCtrl(rootJnt, rootTweak)
	rootJnt.node.scale.disconnect()
	blkUtils.transferAuthorityToCtrl(midJnt, midTweak)
	midJnt.node.scale.disconnect()
	blkUtils.transferAuthorityToCtrl(endJnt, endTweak)
	endJnt.node.scale.disconnect()
	
	for j,fngDict in enumerate(fngs):
		fkFing = fngDict["ctrl"]
		fngJnt = fngDict["jnt"]

		if j == 0:
			fngOffsetGrp = blkUtils.getOffsetGrpForCtrl(fkFing)
			mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fngOffsetGrp.node], sources = [endTweak.node], connectScale = True, maintainOffset = True)

		blkUtils.transferAuthorityToCtrl(fngJnt, fkFing)
		fngJnt.node.scale.disconnect()

	if psocn:
		# connect the root FK Y rotation revrese
		# to a new tweak slot 
		# muting Y rotation at the start position
		sourceValueMdl = mnsNodes.mdlNode(fkRoot.node.ry, muteRootTwistAttr)
		
		if rootGuide.side == "r":
			mdlNode = mnsNodes.mdlNode(sourceValueMdl.node.output, fkIkBlendAttr)
			mdlNode.node.output >> psocn.customPosition[tweakerIndex].twist
		else:
			mdlNode = mnsNodes.mdlNode(sourceValueMdl.node.output, -1.0)
			mdlNode1 = mnsNodes.mdlNode(mdlNode.node.output, fkIkBlendAttr)
			mdlNode1.node.output >> psocn.customPosition[tweakerIndex].twist
		
		psocn.customPosition[tweakerIndex].uPosition.set(0.0)
		tweakerIndex += 1

		#create another muting channel for the ik state
		startPositionLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkRoot,side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "StartPosition", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		startPositionLoc.node.v.set(False)
		mnsNodes.mnsMatrixConstraintNode(side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id, targets = [startPositionLoc.node], sources = [fkRefs[0].node], connectScale = True)
		sourceValueMdl = mnsNodes.mdlNode(startPositionLoc.node.ry, muteRootTwistAttr)
		revNode = mnsNodes.reverseNode([fkIkBlendAttr, 0.0, 0.0])
		mdlNode = mnsNodes.mdlNode(sourceValueMdl.node.output, -1.0)
		mdlNode1 = mnsNodes.mdlNode(mdlNode.node.output, revNode.node.outputX)
		mdlNode1.node.output >> psocn.customPosition[tweakerIndex].twist
		psocn.customPosition[tweakerIndex].uPosition.set(0.0)
		tweakerIndex += 1

		endPositionLoc = mnsUtils.createNodeReturnNameStd(parentNode = rigComponentsGrp,side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EndPosition", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		offGrp = mnsUtils.createOffsetGroup(endPositionLoc)
		parConst = mnsNodes.mayaConstraint([endJnt.node], offGrp.node, type = "parent", maintainOffset = False)
		endPositionAnimOffsetLoc = mnsUtils.createNodeReturnNameStd(parentNode = animGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "endPositionAnimOffset", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		endPositionAnimOffsetLoc.node.v.set(False)
		pm.delete(pm.parentConstraint(endJnt.node, endPositionAnimOffsetLoc.node))
		#orConst = mnsNodes.mayaConstraint([endPositionAnimOffsetLoc.node], endPositionLoc.node, type = "orient", maintainOffset = False, skip = ["x", "z"])
		endPositionLoc.node.worldMatrix[0] >> primBtcNode.transforms[2].matrix

		psocn.excludeBaseRotation.set(False)

		for extraTwistRotCtrl in [endTweak]:#, fkEnd, ikCtrl]:
			mnsUtils.addAttrToObj([extraTwistRotCtrl.node], type = "enum", value = ["______"], name = "TWIST", replace = True)
			falloffAttr = mnsUtils.addAttrToObj([extraTwistRotCtrl.node], type = "float", value = 1.0, name = "twistFalloff", replace = True, min = 0.01)[0]
			
			if rootGuide.side == "r":
				mdlNode = mnsNodes.mdlNode(extraTwistRotCtrl.node.ry, -1.0, psocn.customPosition[tweakerIndex].twist)
			else:
				extraTwistRotCtrl.node.ry >> psocn.customPosition[tweakerIndex].twist
			
			falloffAttr >> psocn.customPosition[tweakerIndex].falloff
			psocn.customPosition[tweakerIndex].uPosition.set(1.0)
			tweakerIndex += 1

		#create isolated feather controls bridge
		status, doFeatherIsolatedCtrls = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doFeatherIsolatedCtrls", True)
		if doFeatherIsolatedCtrls:
			status, featherIsolatedControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "featherIsolatedControlShape", "square")
			isolatedFeathersGrp = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IsolatedFeathers", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
			pm.parent(isolatedFeathersGrp.node, animGrp.node)

			interpJnts = [f for f in blkUtils.getModuleDecendentsWildcard(rootGuide, interpJntsOnly = True) if "Feathers" in f.name]
			iJntsByColumn =[]
			for iJnt in interpJnts:
				jId = iJnt.id - 1
				if len(iJntsByColumn) <= jId: iJntsByColumn.append([])
				iJntsByColumn[jId].append(iJnt)
			
			iJntBridgeControlByColumn = []
			for j, iJntCol in enumerate(iJntsByColumn):
				if len(iJntBridgeControlByColumn) <= j: iJntBridgeControlByColumn.append([])
				
				for k, iJnt in enumerate(iJntCol):
					parentNode = isolatedFeathersGrp
					if k != 0: parentNode = iJntBridgeControlByColumn[j][k-1]

					alphaIndex = iJnt.body.split("Feathers")[-1]

					bridgeCtrl = blkCtrlShps.ctrlCreate(parentNode = parentNode, 
										controlShape = featherIsolatedControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 1, 
										scale = modScale, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "IsoFeather" + alphaIndex, 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = iJnt.node, 
										createOffsetGrp = True,
										symmetryType = FKSymmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)
					
					bridgeCtrlOffsetGrp = blkUtils.getOffsetGrpForCtrl(bridgeCtrl)

					topOffsetGrp = None
					#create a local channels syle FK
					if k != 0:
						for prevCtrl in iJntBridgeControlByColumn[j]:
							newModGrp = mnsUtils.createOffsetGroup(bridgeCtrlOffsetGrp, type = "modifyGrp", bodySuffix = "PrevPiv")
							pm.parent(bridgeCtrlOffsetGrp.node, w = True)
							pm.matchTransform(newModGrp.node, prevCtrl.node)
							pm.parent(bridgeCtrlOffsetGrp.node, newModGrp.node)
							zeroOffset = mnsUtils.createOffsetGroup(newModGrp, type = "offsetGrp", bodySuffix = "Zero")
							for chan in "trs":
								prevCtrl.node.attr(chan) >> newModGrp.node.attr(chan)
							if not topOffsetGrp:
								topOffsetGrp = zeroOffset
					
					newPocSlave = bridgeCtrlOffsetGrp
					if topOffsetGrp:
						newModGrp = mnsUtils.createOffsetGroup(topOffsetGrp, type = "modifyGrp", bodySuffix = "NewSlave")
						pm.parent(topOffsetGrp.node, w = True)
						pm.matchTransform(newModGrp.node, bridgeCtrl.node)
						pm.parent(topOffsetGrp.node, newModGrp.node)
						newPocSlave = newModGrp

					#orient the ctrl - aim to next
					if k != (len(iJntCol) - 1):
						#this is commented because this behaviour was implemented in poc aimParamAdjust
						nextIjnt = iJntCol[k + 1]
						#createUpVector
						upLoc = pm.spaceLocator()
						pm.parent(upLoc, bridgeCtrl.node, relative = True)
						upLoc.tx.set(10)
						pm.parent(upLoc, world= True)

						aimCns = mnsNodes.mayaConstraint([nextIjnt.node], bridgeCtrl.node, type = "aim", aimVector = [0.0,1.0,0.0], upVector = [1.0,0.0,0.0], worldUpType = "object", worldUpObject = upLoc, maintainOffset = False)
						pm.delete(aimCns.node, upLoc)
					else:
						#last row, match previous ctrl orientation
						pm.delete(pm.orientConstraint(parentNode.node, bridgeCtrl.node))
					aimOffsetGrp = mnsUtils.createOffsetGroup(bridgeCtrl, type = "offsetGrp", bodySuffix = "Aim")


					masterLoc = blkUtils.getRelationMasterFromSlave(iJnt)
					origMatCns = iJnt.node.parentInverseMatrix.listConnections(s = False, d = True)
					if origMatCns and masterLoc: 
						pm.delete(origMatCns)
						mnsNodes.mnsMatrixConstraintNode(side = bridgeCtrl.side, alpha = bridgeCtrl.alpha, id = bridgeCtrl.id, targets = [newPocSlave.node], sources = [masterLoc.node], connectScale = True, maintainOffset = True)
						mnsNodes.mnsMatrixConstraintNode(side = bridgeCtrl.side, alpha = bridgeCtrl.alpha, id = bridgeCtrl.id, targets = [iJnt.node], sources = [bridgeCtrl.node], connectScale = True, maintainOffset = True)

					iJntBridgeControlByColumn[j].append(bridgeCtrl)
					secondaryCtrls.append(bridgeCtrl)



		#create extra poc node rotation attrs
		pocNodes = {}
		for j in range(featherFKSections):
			rowAlpha = mnsUtils.convertIntToAlpha(j +1).upper()
			attrName = "feathers" + rowAlpha + "_pocn"
			status, pocNodeFeath = mnsUtils.validateAttrAndGet(rootGuide, attrName, None) 
			if pocNodeFeath:
				pocNodes[rowAlpha] = pocNodeFeath

		if pocNodes:
			#first create "all" section
			#divider
			mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "Wave", replace = True, locked = True)
			
			#waveAimAngle
			waveAllAngleAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "all_waveAngle", replace = True)[0]
			
			#waveAimPhase
			waveAllPhaseAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "all_wavePhase", replace = True)[0]
			
			#now create the connection network
			for pocNodeAlpha in sorted(pocNodes.keys()):
				pocNode = pocNodes[pocNodeAlpha]
				
				#divider
				mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "row" + pocNodeAlpha, replace = True, locked = True)
			
				#waveAimAngle
				waveAngleAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "row" + pocNodeAlpha + "_waveAngle", replace = True)[0]
				mnsNodes.adlNode(waveAngleAttr, waveAllAngleAttr, pocNode.tertiaryWaveAngle)
				
				#waveAimPhase
				wavePhaseAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "row" + pocNodeAlpha + "_wavePhase", replace = True)[0]
				mnsNodes.adlNode(wavePhaseAttr, waveAllPhaseAttr, pocNode.tertiaryWavePhase)
		
		
		ctrlsCollect = primaryCtrls + secondaryCtrls + tertiaryControls

	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, None, attrHost

def customGuides(mansur, builtGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils

	custGuides = []
	parentDict = {}

	if builtGuides:
		nameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "PoleVector", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		nameStd.node.localScale.set((2,2,2))
		pm.delete(pm.parentConstraint(builtGuides[1].node, nameStd.node))
		custGuides.append(nameStd)
		parentDict.update({nameStd: builtGuides[1]})

	return custGuides, parentDict

def deleteUnusedMnsNodesFromRootGuide(rootNode = None):
	def recDelMnsNodes(rootNode = None, collect = []):
		if rootNode:
			for inCon in rootNode.listConnections(s = True, d = False):
				nodeType = type(inCon)
				if nodeType == pm.nodetypes.MnsBuildTransformsCurve or nodeType == pm.nodetypes.MnsPointsOnCurve or nodeType == pm.nodetypes.MnsResampleCurve:
					if not inCon in collect: 
						collect.append(inCon)
						recDelMnsNodes(inCon, collect)
						
	collectToDelete = []
	recDelMnsNodes(rootNode, collectToDelete)
	pm.delete(collectToDelete)

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core.prefixSuffix import GLOB_mnsJntStructDefaultSuffix

	rootGuide = guides[0]
	transforms = [blkUtils.getRelatedNodeFromObject(g.node) for g in guides]
	rigTop = blkUtils.getRigTop(rootGuide.node)

	softMod = kwargs.get("softMod", False)

	if rootGuide.node.hasAttr("interpolationJoints"): 
		if True:
			status, offsetX = mnsUtils.validateAttrAndGet(rootGuide, "offsetX", 10.0)
			status, offsetY = mnsUtils.validateAttrAndGet(rootGuide, "offsetY", 0.0)
			status, offsetZ = mnsUtils.validateAttrAndGet(rootGuide, "offsetZ", 0.0)
			
			status, asBatWing = mnsUtils.validateAttrAndGet(rootGuide, "asBatWing", False)
			if asBatWing: transforms = transforms[:3]

			status, scaleMode = mnsUtils.validateAttrAndGet(rootGuide, "scaleMode", 2)
			status, squashMode = mnsUtils.validateAttrAndGet(rootGuide, "squashMode", 0)

			if not softMod:
				#make sure all previous mns poc, btc, and rsc nodes are deleted
				deleteUnusedMnsNodesFromRootGuide(rootGuide.node)

				#build structure
				btcNode = mnsNodes.mnsBuildTransformsCurveNode(
										side = rootGuide.side, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id, 
										body = rootGuide.body + "Main", 
										transforms = transforms, 
										deleteCurveObjects = True, 
										tangentDirection = 2, 
										buildOffsetCurve = True,
										degree = 1,
										offsetX = offsetX,
										offsetY = offsetY,
										offsetZ = offsetZ)
				blkUtils.connectSlaveToDeleteMaster(btcNode["node"], rootGuide)

				status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
				status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
				mnsUtils.addAttrToObj([rootGuide.node], type = "int", value = tweakersPerSection, name = "previousNumTweakers", replace = True)[0]
				sections = getNumSections(tweakersPerSection, doTweakers, asBatWing)

				inputCurve, inputUpCurve = None, None
				for curveType in ["curve", "upCurve"]:
					outCurveAttrName = "outCurve"
					if curveType == "upCurve": outCurveAttrName = "outOffsetCurve"

					#create re-sampleCurve and reconnect
					rscNode = mnsNodes.mnsResampleCurveNode(side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + "Main", 
											inputCurve = btcNode["node"].node.attr(outCurveAttrName)
											)
					btcNode["node"].node.degree >> rscNode["node"].node.degree
					rscNode["node"].node.resampleMode.set(0)
					rscNode["node"].node.sections.set(sections)

					if curveType == "curve": inputCurve = rscNode["node"].node.outCurve
					else: inputUpCurve = rscNode["node"].node.outCurve

				pocn = mnsNodes.mnsPointsOnCurveNode(
										side = rootGuide.side, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id, 
										body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
										inputCurve = inputCurve,
										inputUpCurve = inputUpCurve,
										buildOutputs = True,
										buildType = 4, #interpJointsType
										buildMode = 0,
										doScale = False,
										aimAxis = 1,
										upAxis = 0,
										numOutputs = rootGuide.node.attr("interpolationJoints").get()
										)

				pocn["node"].node.scaleMode.set(scaleMode)
				pocn["node"].node.squashMode.set(squashMode)

				pocn["node"].node.excludePolesRotation.set(True)
				pocn["node"].node.excludeBaseRotation.set(True)
				transforms[0].worldMatrix[0] >> pocn["node"].node.baseAlternateWorldMatrix
				transforms[-1].worldMatrix[0] >> pocn["node"].node.tipAlternateWorldMatrix
				returnData = {"Main": pocn["samples"]}

				######################
				### Feathers bones ###
				######################
				
				status, featherFKSections = mnsUtils.validateAttrAndGet(rootGuide, "featherFKSections", 3)
				status, featherJoints = mnsUtils.validateAttrAndGet(rootGuide, "featherJoints", 0)
				status, doFeathersSpring = mnsUtils.validateAttrAndGet(rootGuide, "doFeathersSpring", False)
				status, featherFKControlShape = mnsUtils.validateAttrAndGet(rootGuide, "featherFKControlShape", "cube")
				status, doIndexFingerTweak = mnsUtils.validateAttrAndGet(rootGuide, "doIndexFingerTweak", False)

				if featherJoints: 
					if True:
						#create poc tweak attrs
						mnsUtils.addAttrToObj([rootGuide.node], type = "enum", value = ["______"], name = "FeathInterpTweaks", replace = True, locked = True)
						uTugScaleAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "float", value = 0.0, min = -1.0, max = 1.0, name = "tugScale", replace = True)[0]
						uTugScaleTensionAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "float", value = 0.0, min = -1.0, max = 1.0, name = "uTugScaleTension", replace = True)[0]
						uTugOffsetAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "float", value = 0.0, name = "uTugOffset", replace = True)[0]

						#get compuond FKChain modules
						compoundModules = blkUtils.getCompundChildren(guides[0])
						
						topRowGuidesDict = {}
						for childModule in compoundModules:
							mnsUtils.setAttr(childModule.node.FKcontrolShape, featherFKControlShape)

							parent = childModule.node.getParent()
							index = mnsUtils.validateNameStd(parent).id
							topRowGuidesDict[index] = childModule
							
							"""
							#validate number of sections, and divisions
							updateSettings = False
							doFeathersSpringCurrent = mnsUtils.validateAttrAndGet(childModule, "doIntepJntsSpring", False)
							if doFeathersSpringCurrent != doFeathersSpring:
								updateSettings = True

							fkGuides = blkUtils.getModuleDecendentsWildcard(childModule, guidesOnly = True, getCustomGuides = False)
							goalGuideAmount = featherFKSections + 1
							currentAmount = len(fkGuides)
							
							if goalGuideAmount > currentAmount:
								updateSettings = True
								differnece = goalGuideAmount - currentAmount
								#add missing difference
								blkUtils.insertGuides(differnece, "above", fromObjs = [fkGuides[-1]])
							elif goalGuideAmount < currentAmount:
								updateSettings = True
								differnece = currentAmount - goalGuideAmount
								#remove guides difference
								guidesToRemove = []
								for k in range(differnece):
									guidesToRemove.append(fkGuides[len(fkGuides) - k -1])
								blkUtils.removeGuides(fromObjs = guidesToRemove)


							if updateSettings:
								#update compound FK settings
								from mansur.block import blockBuildUI
								blockWin = blockBuildUI.MnsBlockBuildUI()

								#defining mandatory variables for the update settings command
								origArgs, split = blockWin.getModuleSettings(childModule)

								#creating the settings dictionary
								settings = {"settingsHolder": childModule, #mandatory
											"origArgs": origArgs, #mandatory
											"rigTop": rigTop, #mandatory
											"interpolationJoints": goalGuideAmount,
											"doIntepJntsSpring": doFeathersSpring,
											"doInterpolationJoints": doFeathersSpring
											}

								#running the update command
								blockWin.updateSettings(**settings)
							"""

						jntRowsList = []
						for i in range(1, len(topRowGuidesDict.keys()) + 1):
							interpJnts = []

							status, doInterpolationJoints =mnsUtils.validateAttrAndGet(topRowGuidesDict[i], "doInterpolationJoints", False)

							mainJnts = interpJnts = blkUtils.getRootJointsFromModuleRoot(topRowGuidesDict[i])
							if doInterpolationJoints:
								interpJnts = blkUtils.getModuleDecendentsWildcard(topRowGuidesDict[i], interpJntsOnly = True)
							else:
								interpJnts = mainJnts

							for j in range(featherFKSections + 1):
								targetJnt = interpJnts[j]
								
								if len(interpJnts) > len(mainJnts):
									targetJnt = interpJnts[j * 2]

								if len(jntRowsList) < j + 1:
									jntRowsList.append([targetJnt])
								else:
									jntRowsList[j].append(targetJnt)

						btcList = []
						inputCurveList = []
						inputUpCurveList = []
						
						for l, jntRow in enumerate(jntRowsList):
							buildOffsetCurve = True
							offsetXd, offsetYd, offsetZd = offsetX, offsetY, offsetZ
							rowAlpha = mnsUtils.convertIntToAlpha(l + 1).upper()

							if l == (len(jntRowsList) - 1):
								buildOffsetCurve = False
								offsetXd, offsetYd, offsetZd = 0.0, 0.0, 0.0

							btcFeathersA = mnsNodes.mnsBuildTransformsCurveNode(
													side = rootGuide.side, 
													alpha = rootGuide.alpha, 
													id = rootGuide.id, 
													body = rootGuide.body + "Feathers" + rowAlpha, 
													transforms = jntRow, 
													deleteCurveObjects = True, 
													tangentDirection = 2, 
													buildOffsetCurve = buildOffsetCurve,
													degree = 1,
													offsetX = offsetXd,
													offsetY = offsetYd,
													offsetZ = offsetZd)
							btcList.append(btcFeathersA)
							
							#store last btc node
							if l == (len(jntRowsList) - 1):
								attrName = "feathersLastRow_btc"
								mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = attrName, value= btcFeathersA["node"].node, replace = True)[0]

							if l== 0:
								inputCurveList.append(inputCurve)
								inputUpCurveList.append(inputUpCurve)
							else:
								for curveType in ["curve", "upCurve"]:
									outCurveAttrName = "outCurve"
									if curveType == "upCurve": outCurveAttrName = "outOffsetCurve"

									#create re-sampleCurve and reconnect
									rscNode = mnsNodes.mnsResampleCurveNode(side = rootGuide.side, 
															alpha = rootGuide.alpha, 
															id = rootGuide.id, 
															body = rootGuide.body + "Feathers" + rowAlpha, 
															inputCurve = btcList[l]["node"].node.attr(outCurveAttrName)
															)
									btcList[l]["node"].node.degree >> rscNode["node"].node.degree
									rscNode["node"].node.resampleMode.set(0)
									
									sections = len(jntRow) - 1
									rscNode["node"].node.sections.set(sections)

									if curveType == "curve": 
										inputCurveList.append(rscNode["node"].node.outCurve)
									else:
										inputUpCurveList.append(rscNode["node"].node.outCurve)

						#create isolated param adjust attrs
						mnsUtils.addAttrToObj([rootGuide.node], type = "enum", value = ["______"], name = "IsolatedParamAdjust", replace = True, locked = True)
						for j in range(featherJoints):
							mnsUtils.addAttrToObj([rootGuide.node], type = "enum", value = ["__"], name = "Pos_" + str(j), replace = True, locked = True)
							for l, jntRow in enumerate(jntRowsList):
								if l != (len(jntRowsList) - 1):
									attrName = "featherPos" + str(j) + "_" + mnsUtils.convertIntToAlpha(l)
									mnsUtils.addAttrToObj([rootGuide.node], type = "float", value = 0.0, name = attrName, replace = True)[0]
									if l == (len(jntRowsList) - 2):
										attrName = "aimPos" + str(j) + "_" + mnsUtils.convertIntToAlpha(l)
										mnsUtils.addAttrToObj([rootGuide.node], type = "float", value = 0.0, name = attrName, replace = True)[0]

						pocNodesCollect = []
						for l, jntRow in enumerate(jntRowsList):
							rowAlpha = mnsUtils.convertIntToAlpha(l + 1).upper()
							if l != (len(jntRowsList) - 1):
								inputCurveA = inputCurveList[l]
								inputUpCurveA = inputUpCurveList[l]
								pocnFeathersA = mnsNodes.mnsPointsOnCurveNode(
														side = rootGuide.side, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id, 
														body = rootGuide.body + "Feathers" + rowAlpha, 
														inputCurve = inputCurveA,
														inputUpCurve = inputUpCurveA,
														buildOutputs = True,
														buildType = 4, #interpJointsType
														buildMode = 0,
														doScale = False,
														aimAxis = 1,
														upAxis = 0,
														numOutputs = rootGuide.node.attr("featherJoints").get(),
														rotateMode = 3
														)
								#enable param adjust
								pocnFeathersA["node"].node.enableParamAdjust.set(True)
								for j in range(featherJoints):
									attrName = "featherPos" + str(j) + "_" + mnsUtils.convertIntToAlpha(l)
									rootGuide.node.attr(attrName) >> pocnFeathersA["node"].node.paramAdjustment[j]
									if l != 0:
										rootGuide.node.attr(attrName) >> pocNodesCollect[-1]["node"].node.aimParamAdjustment[j]
									if l == (len(jntRowsList) - 2):
										attrName = "aimPos" + str(j) + "_" + mnsUtils.convertIntToAlpha(l)
										rootGuide.node.attr(attrName) >> pocnFeathersA["node"].node.aimParamAdjustment[j]

								outConnections = btcList[l + 1]["node"].node.outCurve.listConnections(d = True, s = False)
								if outConnections:
									for con in outConnections:
										if type(con) == pm.nodetypes.MnsResampleCurve:
											con.outCurve >> pocnFeathersA["node"].node.aimCurve
								
								#store
								attrName = "feathers" + rowAlpha + "_pocn"
								bkTopAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = attrName, value= pocnFeathersA["node"].node, replace = True)[0]

								#connect tweak atrrs
								uTugScaleAttr >> pocnFeathersA["node"].node.uTugScale
								uTugScaleTensionAttr >> pocnFeathersA["node"].node.uTugScaleTension
								uTugOffsetAttr >> pocnFeathersA["node"].node.uTugOffset

								#collect nodes for next iteration
								pocNodesCollect.append(pocnFeathersA)

								#update return
								returnData.update({"Feathers" + rowAlpha: pocnFeathersA["samples"]})

				return returnData
			else:
				#find nodes
				btcNodes, pocNodes, rscNodes = [], [], []
				relatedRootJnt = mnsUtils.validateNameStd(rootGuide.node.jntSlave.get())
				outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
				if outConnections:
					for con in outConnections: 
						if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
							btcNode = con
							btcNodes.append(btcNode)
							outConnections = btcNode.outCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										if con not in rscNodes:
											rscNodes.append(con)

							outConnections = btcNode.outOffsetCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										if con not in rscNodes:
											rscNodes.append(con)

							if rscNodes:
								outConnections = rscNodes[0].outCurve.listConnections(s = False, d = True)
								if outConnections:
									for con in outConnections: 
										if type(con) == pm.nodetypes.MnsPointsOnCurve and "Main" in con.nodeName():
											if con not in pocNodes:
												pocNodes.append(con)
							break

				status, featherFKSections = mnsUtils.validateAttrAndGet(rootGuide, "featherFKSections", 3)
				for j in range(featherFKSections):
					rowAlpha = mnsUtils.convertIntToAlpha(j +1).upper()
					attrName = "feathers" + rowAlpha + "_pocn"
					status, pocNodeFeath = mnsUtils.validateAttrAndGet(rootGuide, attrName, None) 
					if pocNodeFeath:
						if pocNodeFeath not in pocNodes:
							pocNodes.append(pocNodeFeath)
							
							outConnections = pocNodeFeath.curve.listConnections(s = True, d = False)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										rscNodes.append(con)
										outConnections = con.inputCurve.listConnections(s = True, d = False)
										if outConnections:
											for con in outConnections: 
												if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
													if con not in btcNodes:
														btcNodes.append(con)
											
							outConnections = pocNodeFeath.upCurve.listConnections(s = True, d = False)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										if con not in rscNodes:
											rscNodes.append(con)
				
				status, feathersLastRow_btc = mnsUtils.validateAttrAndGet(rootGuide, "feathersLastRow_btc", None) 
				if feathersLastRow_btc:
					if feathersLastRow_btc not in btcNodes:
						btcNodes.append(feathersLastRow_btc)
						
						outConnections = feathersLastRow_btc.outCurve.listConnections(s = False, d = True)
						if outConnections:
							for con in outConnections: 
								if type(con) == pm.nodetypes.MnsResampleCurve:
									if con not in rscNodes:
										rscNodes.append(con)

				#adjust the nodes
				for btcNode in btcNodes:
					if btcNode.buildOffsetCurve.get():
						btcNode.offsetX.set(offsetX)
						btcNode.offsetY.set(offsetY)
						btcNode.offsetZ.set(offsetZ)

				status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
				status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
				sections = getNumSections(tweakersPerSection, doTweakers, asBatWing)
				for resampleCurve in rscNodes:
					resampleCurve.sections.set(sections)
					outConnections = resampleCurve.outCurve.listConnections(s = False, d = True, p = True)
					if outConnections:
						for plug in outConnections: 
							con = plug.node()
							if type(con) == pm.nodetypes.MnsPointsOnCurve and plug.attrName() != "aimCurve":
								resampleCurve.outCurve >> con.bindCurve
								con.bindCurve.disconnect()

				previousValues = collectFeathParamAdjustValues(rootGuide)
				attempFeatherParamAdjustRemap(mansur, rootGuide, previousValues)

				#compound attrs
				compoundModules = blkUtils.getCompundChildren(guides[0])
				status, featherFKControlShape = mnsUtils.validateAttrAndGet(rootGuide, "featherFKControlShape", "cube")

				for childModule in compoundModules:
					mnsUtils.setAttr(childModule.node.FKcontrolShape, featherFKControlShape)

def jointStructureSoftMod(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	kwargs.update({"softMod": True})
	jointStructure(mansur, guides, mnsBuildModule, **kwargs)

def deconstruct(mansur, MnsBuildModule, **kwargs):
	"""deconstruct method implementation. 
	Transfer interJoints control back to the main joints.
	"""

	from mansur.block.core import blockUtility as blkUtils
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	psocn = None
	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		if rootGuide.node.hasAttr("jntSlave"):
			relatedRootJnt = mnsUtils.validateNameStd(rootGuide.node.jntSlave.get())
			if relatedRootJnt:
				outConnections = MnsBuildModule.guideControls[0].node.jntSlave.get().worldMatrix[0].listConnections(s = False, d = True)
				if outConnections:
					for outConnection in outConnections:
						if type(outConnection) == pm.nodetypes.MnsBuildTransformsCurve: 
							btcNode = outConnection

							#reconnect the main end jnt to btc node
							endJnt = mnsUtils.validateNameStd(MnsBuildModule.guideControls[1].node.jntSlave.get())
							endJnt.node.worldMatrix[0] >> btcNode.transforms[2].matrix
							blkUtils.connectIfNotConnected(relatedRootJnt.node.worldMatrix[0], btcNode.transforms[0].matrix)

							interpLocs = blkUtils.getModuleInterpJoints(rootGuide)
							iLoc = interpLocs[0]
							inConnections = iLoc.node.t.listConnections(s = True, d = False)
							psocn, feathMainPocn = None, None
							if inConnections:
								for inCon in inConnections:
									if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
										psocn = inCon
										psocn.excludeBaseRotation.set(True)
										psocn.resetScale.set(1)
										psocn.doScale.set(0)
										break

							#get feathers row A poc node
							if psocn:
								inConnections = psocn.curve.listConnections(s = True, d = False)
								if inConnections:
									inCon = inConnections[0]
									if type(inCon) == pm.nodetypes.MnsBuildTransformsCurve:
										outConnections = inCon.outCurve.listConnections(s = False, d = True)
										if outConnections:
											for con in outConnections:
												if type(con) == pm.nodetypes.MnsPointsOnCurve and "Feather" in con.nodeName():
													feathMainPocn = con
													break

							status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
							status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
							status, asBatWing = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "asBatWing", False)

							sections = getNumSections(tweakersPerSection, doTweakers, asBatWing)
							
							outConnections = btcNode.outCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										resampleCurve = con
										blkUtils.connectIfNotConnected(resampleCurve.outCurve, psocn.curve)
										resampleCurve.sections.disconnect()
										resampleCurve.sections.set(sections)
										if feathMainPocn:
											blkUtils.connectIfNotConnected(resampleCurve.outCurve, feathMainPocn.curve)


							outConnections = btcNode.outOffsetCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										resampleCurveOffset = con
										blkUtils.connectIfNotConnected(resampleCurveOffset.outCurve, psocn.upCurve)
										resampleCurveOffset.sections.disconnect()
										resampleCurveOffset.sections.set(sections)	
										if feathMainPocn:
											blkUtils.connectIfNotConnected(resampleCurveOffset.outCurve, feathMainPocn.upCurve)

							#reconnect interpJoints away from bridge if needed
							status, doFeatherIsolatedCtrls = mnsUtils.validateAttrAndGet(rootGuide, "doFeatherIsolatedCtrls", True)
							if doFeatherIsolatedCtrls:
								interpJnts = [f for f in blkUtils.getModuleDecendentsWildcard(rootGuide, interpJntsOnly = True) if "Feathers" in f.name]
								for iJnt in interpJnts:
									masterLoc = blkUtils.getRelationMasterFromSlave(iJnt)
									origMatCns = iJnt.node.parentInverseMatrix.listConnections(s = False, d = True)
									if origMatCns and masterLoc: 
										pm.delete(origMatCns)
										mnsNodes.mnsMatrixConstraintNode(side = rootGuide.side, alpha = rootGuide.alpha, id = rootGuide.id, targets = [iJnt.node], sources = [masterLoc.node])
							break

		#make sure all extra poc nodes channels are reset
		status, featherFKSections = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "featherFKSections", 3)
		pocNodes = {}
		for j in range(featherFKSections):
			rowAlpha = mnsUtils.convertIntToAlpha(j +1).upper()
			attrName = "feathers" + rowAlpha + "_pocn"
			status, pocNodeFeath = mnsUtils.validateAttrAndGet(rootGuide, attrName, None) 
			if pocNodeFeath:
				#reset
				pocNodeFeath.tertiaryWaveAngle.disconnect()
				pocNodeFeath.tertiaryWaveAngle.set(0.0)
				pocNodeFeath.tertiaryWavePhase.disconnect()
				pocNodeFeath.tertiaryWavePhase.set(0.0)

def moduleCompound(mansur, bmButtonList, guides, mnsBuildModule = None, **kwargs):
	from mansur.block.core import buildModules as mnsBuildModules
	from mansur.core import utility as mnsUtils

	status, featherFKSections = mnsUtils.validateAttrAndGet(guides[0], "featherFKSections", 3)
	status, doFeathersSpring = mnsUtils.validateAttrAndGet(guides[0], "doFeathersSpring", False)
	status, featherFKControlShape = mnsUtils.validateAttrAndGet(guides[0], "featherFKControlShape", "cube")
	status, numOfGuides = mnsUtils.validateAttrAndGet(guides[0], "numOfGuides", 5)
	status, doIndexFingerTweak = mnsUtils.validateAttrAndGet(guides[0], "doIndexFingerTweak", False)

	modulesReturn = []
	doInterpolationJoints = False
	if doFeathersSpring:
		doInterpolationJoints = True

	settings = {
				"side": guides[0].side,
				"alpha": guides[0].alpha,
				"id": guides[0].id,
				"numOfGuides": featherFKSections + 1,
				#"matchParentOrient": False,
				#"alongAxis": 5,
				"splitOrientSpace": True,
				"doInterpolationJoints": doInterpolationJoints,
				"interpolationJoints": featherFKSections + 1,
				"doIntepJntsSpring": doFeathersSpring,
				"doAttributeHostCtrl": True,
				"primaryInterpolaion": 1,
				"primaryCurveDegree": 1,
				"FKcontrolShape": featherFKControlShape,
				"squashMode": 4,
				"spaces": ["None"]
				}
	
	#FKChains
	extNames = ["shoulder", "elbow", "wrist"]
	for k in range(0, numOfGuides - 3):
		extNames.append("fng" + mnsUtils.convertIntToAlpha(k).upper())

	for k, guide in enumerate(guides):
		settings["body"] = extNames[k] + "Ext"
		if doIndexFingerTweak and guide == guides[-1]:
			settings["doInterpolationJoints"] = True
			settings["interpolationJoints"] = (featherFKSections + 1) + featherFKSections
			settings["doSecondaryIKCtrls"] = True
			settings["numIKControls"] = (featherFKSections + 1) + featherFKSections

		compoundModule = mnsBuildModules.createModuleCompound(guides[0], "FKChain", bmButtonList, guide, settings)
		if compoundModule: 
			compoundModule.rootGuide.node.scale.set((0.7,0.7,0.7))
			compoundModule.gatherRelatedGuides()
			for guideA in compoundModule.guideControls:
				if guideA.node != compoundModule.rootGuide.node:
					guideA.node.t.set((0.0,0.0,-20.0))
			modulesReturn.append(compoundModule)
		if k == 0:
			settings["spaces"] = [guide.node.nodeName()]
		else:
			settings["spaces"].append(guide.node.nodeName())

	return modulesReturn

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core import prefixSuffix as mnsPrefixSufix
	from mansur.block.core import buildModules as mnsBuildModules

	#connection to limb
	ikSolverNode, newIKTarget, bkTop, fkRootCtrl, footSpaceSource = None, None, None, None, None
	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		MnsBuildModule.gatherRelatedCtrls()
		moduleAnimGrp = blkUtils.getModuleAnimGrp(MnsBuildModule.allControls[0])
		if moduleAnimGrp:
			status, lookAtMasterCtrl = mnsUtils.validateAttrAndGet(moduleAnimGrp, "extensionLookAt", None)
			if status and lookAtMasterCtrl:
				compoundModules = blkUtils.getCompundChildren(rootGuide)
				
				#get host
				lookAtAttr = mnsUtils.addAttrToObj([lookAtMasterCtrl], type = "float", value = 0.0, name = "toAimCtrl", replace = True, max = 1.0, min = 0.0)[0]

				for childModuleRoot in compoundModules:
					#create lookAt cluster feature
					mainCtrlNameStd = mnsUtils.returnNameStdChangeElement(nameStd = childModuleRoot, suffix = mnsPrefixSufix.mnsPS_ctrl, autoRename = False)
					mainCtrlNameStd = mnsUtils.validateNameStd(mainCtrlNameStd.name)
					mainCtrlOffsetGrp = blkUtils.getOffsetGrpForCtrl(mainCtrlNameStd)
					
					#creat native orient grp
					nativeOrientGrp = mnsUtils.duplicateNameStd(mainCtrlOffsetGrp, parentOnly = True)
					nativeOrientGrp = mnsUtils.returnNameStdChangeElement(nameStd = nativeOrientGrp, id = 1, body = nativeOrientGrp.body + "NativeOrient", autoRename = True)
					
					#create look at orient grp
					lookAtOrientGrp = mnsUtils.createNodeReturnNameStd(side =  nativeOrientGrp.side, body = mainCtrlOffsetGrp.body + "LookAt", alpha = nativeOrientGrp.alpha, id =  nativeOrientGrp.id, buildType = "group", incrementAlpha = False, parentNode = mainCtrlOffsetGrp.node.getParent())
					pm.matchTransform(lookAtOrientGrp.node, mainCtrlNameStd.node)
					
					#create up node
					moduleCompoundAnimGrp = blkUtils.getModuleAnimGrp(mainCtrlNameStd)
					upNodeGrp = mnsUtils.createNodeReturnNameStd(side =  moduleCompoundAnimGrp.side, body = moduleCompoundAnimGrp.body + "LookAtUp", alpha = moduleCompoundAnimGrp.alpha, id =  moduleCompoundAnimGrp.id, buildType = "group", incrementAlpha = False, parentNode = moduleCompoundAnimGrp.node)
					pm.matchTransform(upNodeGrp.node, mainCtrlNameStd.node)
					upNodeGrp.node.tx.set(10)
					
					#create the objective look-at cns
					aimCnsItermediate = None
					if rootGuide.side == "l":
						aimCnsItermediate = mnsNodes.mayaConstraint([lookAtMasterCtrl], lookAtOrientGrp, worldUpObject = upNodeGrp.node, type = "aim", aimVector = [0.0,0.0,1.0], upVector = [-1.0, 0.0, 0.0])
					else:
						aimCnsItermediate = mnsNodes.mayaConstraint([lookAtMasterCtrl], lookAtOrientGrp, worldUpObject = upNodeGrp.node, type = "aim", aimVector = [0.0,0.0,1.0], upVector = [1.0, 0.0, 0.0])

					#create and connect the transition attribue orient cns
					orientCns = mnsNodes.mayaConstraint([nativeOrientGrp.node, lookAtOrientGrp], mainCtrlOffsetGrp.node, type = "orient")
					orientCns.node.interpType.set(0)
					lookAtAttr >> orientCns.node.attr(lookAtOrientGrp.node.nodeName() + "W1")
					revNode = mnsNodes.reverseNode([lookAtAttr, None, None], [orientCns.node.attr(nativeOrientGrp.node.nodeName() + "W0"), None, None])