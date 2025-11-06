"""Author: Asaf Ben-Zur
Best used for: Arms, Legs
This module was designed to create a generic 3 joint limb control.
This module will create both the FK and IK controls, and the standard blend control.
On top of the standard behaviour, based on parameters, this module can also include bendy limb controls (as many as you want), Arc layer and Sleeve layer.
Note: When used as a leg, try using the foot module as a direct child of this module to automatically achive a connected behaviour.
"""



from maya import cmds
import pymel.core as pm


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
	sleeveGuide = [g for g in customGuides if "SleevePosition" in g.name]
	if sleeveGuide: sleeveGuide = sleeveGuide[0]

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

	#collections declare
	rscNodes = []

	#get poc node
	psocn = None
	interpLocs = blkUtils.getModuleInterpJoints(MnsBuildModule.rootGuide)
	if interpLocs:
		iLoc = interpLocs[0]
		inConnections = iLoc.node.t.listConnections(s = True, d = False)
		if inConnections:
			inCon = inConnections[0]
			if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
				psocn = inCon

	if psocn: blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> psocn.globalScale

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
	status, blendDefault = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ikFkBlendDefault", 0)
	fkIkBlendAttr = mnsUtils.addAttrToObj([attrHost.node], type = "int", value = int(blendDefault), name = "ikFkBlend", replace = True, max = 1, min = 0)[0]
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
			if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
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

			numTweakControls = (tweakersPerSection * 2) + 3
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
			# (tweakersPerSection * numOfSections * numberOfPositionsPerTweaker) + 3(base, mid, root)
			btcNode["node"].node.substeps.set((tweakersPerSection * 2 * 3) + 2)

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

	
	#add arc
	tpaNode, tpaNodeTweak = None, None
	status, doArc = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doArc", False)
	if doArc:
		if resampleCurve and resampleCurveOffset and psocn:
			status, arcDegree = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "arcDegree", 3)
			status, arcSections = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "arcSections", 8)
			status, resampleCurveSections = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "resampleCurveSections", 16)
			status, collinearAction = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "collinearAction", 1)
			status, conformToMidPoint = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "conformToMidPoint", True)

			#get pocn inputs
			curveInput, offsetCurveInput = None, None
			inConnections = psocn.curve.listConnections(s = True, d = False, p = True)
			if inConnections: curveInput = inConnections[0]
			inConnections = psocn.upCurve.listConnections(s = True, d = False, p = True)
			if inConnections: offsetCurveInput = inConnections[0]
			
			inputCurve, inputUpCurve = None, None
			for curveInputAttr in [curveInput, offsetCurveInput]:
				#create re-sampleCurve and reconnect
				rscNode = mnsNodes.mnsResampleCurveNode(side = MnsBuildModule.rootGuide.side, 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										body = MnsBuildModule.rootGuide.body, 
										inputCurve = curveInputAttr
										)
				if doTweakers:
					btcNode["node"].node.degree >> rscNode["node"].node.degree

				rscNode["node"].node.resampleMode.set(0)
				rscNode["node"].node.sections.set(resampleCurveSections)

				if curveInputAttr == curveInput: curveInput = rscNode["node"].node.outCurve
				else: offsetCurveInput = rscNode["node"].node.outCurve
				rscNodes.append(rscNode["node"].node)

			tpaNode = mnsNodes.mnsThreePointArcNode(side = MnsBuildModule.rootGuide.side, 
											alpha = MnsBuildModule.rootGuide.alpha, 
											id = MnsBuildModule.rootGuide.id, 
											body = MnsBuildModule.rootGuide.body, 
											inputCurve = curveInput,
											inputUpCurve = offsetCurveInput,
											degree = arcDegree, 
											sections = arcSections, 
											conformMidPoint = conformToMidPoint, 
											collinearAction = collinearAction,
											pointA = rootJnt.node,
											pointB = midJnt.node,
											pointC = endJnt.node
											)
			mnsNodes.mnsNodeRelationshipNode(connectDeleteSlavesOnly = True, side = animGrp.side, alpha = animGrp.alpha , id = animGrp.id, master = animGrp.node, slaves = [tpaNode["node"].node])
			tpaNode["node"].node.outCurve >> psocn.curve
			tpaNode["node"].node.outOffsetCurve >> psocn.upCurve

			if TweakPocn:
				tpaNodeTweak = mnsNodes.mnsThreePointArcNode(side = MnsBuildModule.rootGuide.side, 
								alpha = MnsBuildModule.rootGuide.alpha, 
								id = MnsBuildModule.rootGuide.id, 
								body = MnsBuildModule.rootGuide.body, 
								inputCurve = resampleCurve.outCurve,
								inputUpCurve = resampleCurveOffset.outCurve,
								degree = arcDegree, 
								sections = arcSections, 
								conformMidPoint = conformToMidPoint, 
								collinearAction = collinearAction,
								pointA = rootJnt.node,
								pointB = midJnt.node,
								pointC = endJnt.node
								)
				mnsNodes.mnsNodeRelationshipNode(connectDeleteSlavesOnly = True, side = animGrp.side, alpha = animGrp.alpha , id = animGrp.id, master = animGrp.node, slaves = [tpaNodeTweak["node"].node])
				tpaNodeTweak["node"].node.outCurve >> TweakPocn["node"].node.curve
				tpaNodeTweak["node"].node.outOffsetCurve >> TweakPocn["node"].node.upCurve

				resampleCurve.sections.set(resampleCurveSections)
				resampleCurveOffset.sections.set(resampleCurveSections)


			#create extra attributes
			host = attrHost.node
			targetNode = tpaNode["node"].node
			secondaryTargetNode = None
			if tpaNodeTweak: secondaryTargetNode = tpaNodeTweak["node"].node

			#divider
			mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "arc", replace = True, locked = True)
				
			#blend
			blend = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "blend", replace = True, min = 0.0, max = 1.0)[0]
			blend >> targetNode.blend
			if secondaryTargetNode: blend >> secondaryTargetNode.blend

			#blendSectionA
			blendSectionA = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "blendSectionA", replace = True, min = 0.0, max = 1.0)[0]
			blendSectionA >> targetNode.blendSectionA
			if secondaryTargetNode: blendSectionA >> secondaryTargetNode.blendSectionA

			#blendSectionB
			blendSectionB = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "blendSectionB", replace = True, min = 0.0, max = 1.0)[0]
			blendSectionB >> targetNode.blendSectionB
			if secondaryTargetNode: blendSectionB >> secondaryTargetNode.blendSectionB

			status, addSwipes = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "addSwipes", True)
			if addSwipes:
				#swipeStart
				swipeStart = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "swipeStart", replace = True, min = 0.0, max = 1.0)[0]
				swipeStart >> targetNode.swipeStart
				if secondaryTargetNode: swipeStart >> secondaryTargetNode.swipeStart

				#swipeStartFalloff
				swipeStartFalloff = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "swipeStartFalloff", replace = True, min = 0.0, max = 1.0)[0]
				swipeStartFalloff >> targetNode.swipeStartFalloff
				if secondaryTargetNode: swipeStartFalloff >> secondaryTargetNode.swipeStartFalloff

				#swipeMidToRoot
				swipeMidToRoot = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "swipeMidToRoot", replace = True, min = 0.0, max = 1.0)[0]
				swipeMidToRoot >> targetNode.swipeMidToRoot
				if secondaryTargetNode: swipeMidToRoot >> secondaryTargetNode.swipeMidToRoot

				#swipeMidToRootFalloff
				swipeMidToRootFalloff = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "swipeMidToRootFalloff", replace = True, min = 0.0, max = 1.0)[0]
				swipeMidToRootFalloff >> targetNode.swipeMidToRootFalloff
				if secondaryTargetNode: swipeMidToRootFalloff >> secondaryTargetNode.swipeMidToRootFalloff

				#swipeMidToEnd
				swipeMidToEnd = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "swipeMidToEnd", replace = True, min = 0.0, max = 1.0)[0]
				swipeMidToEnd >> targetNode.swipeMidToEnd
				if secondaryTargetNode: swipeMidToEnd >> secondaryTargetNode.swipeMidToEnd

				#swipeMidToEndFalloff
				swipeMidToEndFalloff = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "swipeMidToEndFalloff", replace = True, min = 0.0, max = 1.0)[0]
				swipeMidToEndFalloff >> targetNode.swipeMidToEndFalloff
				if secondaryTargetNode: swipeMidToEndFalloff >> secondaryTargetNode.swipeMidToEndFalloff

				#swipeEnd
				swipeEnd = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "swipeEnd", replace = True, min = 0.0, max = 1.0)[0]
				swipeEnd >> targetNode.swipeEnd
				if secondaryTargetNode: swipeEnd >> secondaryTargetNode.swipeEnd

				#swipeEndFalloff
				swipeEndFalloff = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "swipeEndFalloff", replace = True, min = 0.0, max = 1.0)[0]
				swipeEndFalloff >> targetNode.swipeEndFalloff
				if secondaryTargetNode: swipeEndFalloff >> secondaryTargetNode.swipeEndFalloff
		
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
	pinMidAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = 0.0, name = "pinMidToPoleVec", replace = True, min = 0.0, max = 1.0)[0]
	pointConMid = pm.pointConstraint(midTweakRef.node, poleVector.node, midTweakModGroup.node, name = midTweakModGroup.node.nodeName().replace("_modifyGrp", "_pntCns"))
	pinMidAttr >> pointConMid.attr(poleVector.node + "W1")
	mnsNodes.reverseNode([pinMidAttr, None, None], [pointConMid.attr(midTweakRef.node + "W0"), None, None])

	#sleeve
	status, doSleeve = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doSleeve", False)
	if doSleeve:
		status, sleeveControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "sleeveControlShape", "octagon")
		sleeveCtrl = blkCtrlShps.ctrlCreate(parentNode = animStaticGrp,
											controlShape = sleeveControlShape, 
											createBlkClassID = True, 
											createBlkCtrlTypeID = True, 
											blkCtrlTypeID = 0, 
											scale = modScale * 2, 
											alongAxis = 1, 
											side = MnsBuildModule.rootGuide.side, 
											body = MnsBuildModule.rootGuide.body + "Sleeve", 
											alpha = MnsBuildModule.rootGuide.alpha, 
											id = MnsBuildModule.rootGuide.id,
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											createOffsetGrp = True,
											symmetryType = symmetryType,
											doMirror = False,
											isFacial = MnsBuildModule.isFacial)

		offsetGrp = blkUtils.getOffsetGrpForCtrl(sleeveCtrl, type = "offsetGrp")
		primaryCtrls.append(sleeveCtrl)

		status, sleevePosition = mnsUtils.validateAttrAndGet(sleeveGuide, "sleevePosition", 1.0)
		sleevePosAttr = mnsUtils.addAttrToObj([sleeveCtrl.node], type = "float", value = 0.0, name = "sleevePosition", replace = True, min = 0.0 - sleevePosition, max = 1.0 - sleevePosition)[0]
		sleevePocn = [node for node in sleeveGuide.node.sleevePosition.listConnections(s = False, d = True) if type(node) == pm.nodetypes.MnsPointsOnCurve][0]
		
		blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> sleevePocn.globalScale

		destantionAttr = mnsUtils.addAttrToObj([sleeveGuide.node], type = "message", name = "destinationPocn", value= "", replace = True)[0]
		sleevePocn.message >> destantionAttr

		adlNode = mnsNodes.adlNode(sleevePosAttr, sleevePosition, sleevePocn.uScale)
		#blkUtils.connectSlaveToDeleteMaster(adlNode, sleeveCtrl)

		status, numSleeveJoints = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "numSleeveJoints", 3)
		sleevePocn.transforms[numSleeveJoints - 1].translate >> offsetGrp.node.t
		sleevePocn.transforms[numSleeveJoints - 1].rotate >> offsetGrp.node.r
		sleevePocn.transforms[numSleeveJoints - 1].scale >> offsetGrp.node.s

		#sleeve Attrs
		scaleModeAttr >> sleevePocn.scaleMode
		squashModeAttr >> sleevePocn.squashMode
		scaleMinAttr >> sleevePocn.scaleMin
		scaleMaxAttr >> sleevePocn.scaleMax
		squashFactorAttr >> sleevePocn.squashFactor
		squashPosAttr >> sleevePocn.squashPos

		sleeveCtrl.node.ry >> sleevePocn.twistAimEnd
		host = sleeveCtrl.node

		#divider
		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "rotationTweaks", replace = True, locked = True)
		
		#twistAimStart
		twistAimStartAttr = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "twistAimStart", replace = True)[0]
		twistAimStartAttr >> sleevePocn.twistAimStart

		#twistAimMid
		twistAimMid = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "twistAimMid", replace = True)[0]
		twistAimMid >> sleevePocn.twistAimMid

		#twistAimMidPos
		twistAimMidPos = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "twistAimMidPos", replace = True, min = 0.0, max = 1.0)[0]
		twistAimMidPos >> sleevePocn.twistAimMidPos

		#twistUpEnd
		twistUpEnd = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "twistUpEnd", replace = True)[0]
		twistUpEnd >> sleevePocn.twistUpEnd

		#divider
		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "squeezes", replace = True, locked = True)
		
		#squeezeAim
		squeezeAim = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "squeezeAim", replace = True)[0]
		squeezeAim >> sleevePocn.squeezeAim

		#divider
		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "waves", replace = True, locked = True)
		
		#waveAimAngle
		waveAimAngle = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "waveAimAngle", replace = True)[0]
		waveAimAngle >> sleevePocn.waveAimAngle

		#waveAimPhase
		waveAimPhase = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "waveAimPhase", replace = True)[0]
		waveAimPhase >> sleevePocn.twistAimWavePhase


		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "scaleTweaks", replace = True, locked = True)
		
		#scaleStart
		scaleStart = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "scaleStart", replace = True, min = 0.01)[0]
		scaleStart >> sleevePocn.scaleStart

		#scaleMid
		scaleMid = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "scaleMid", replace = True, min = 0.01)[0]
		scaleMid >> sleevePocn.scaleMid

		#scaleMidPos
		scaleMidPos = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "scaleMidPos", replace = True, min = 0.0, max = 1.0)[0]
		scaleMidPos >> sleevePocn.scaleMidPos

		#scaleWaveAmp
		scaleWaveAmp = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "scaleWaveAmp", replace = True)[0]
		scaleWaveAmp >> sleevePocn.scaleWaveAmp

		#scaleWavePhase
		scaleWavePhase = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "scaleWavePhase", replace = True)[0]
		scaleWavePhase >> sleevePocn.scaleWavePhase

		#scaleEnd
		scaleEnd = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "scaleEnd", replace = True, min = 0.01)[0]
		scaleEnd >> sleevePocn.scaleEnd

		sleevePocn.doScale.set(1)
		sleevePocn.resetScale.set(1)
		mnsUtils.lockAndHideTransforms(sleeveCtrl.node, lock = True, ry = False)



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
		pm.makeIdentity(fkRef.node)
		fkRefs.append(fkRef)
		pm.matchTransform(fkRef.node, fkCtrl.node)
		mnsNodes.mnsMatrixConstraintNode(side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id, targets = [fkRefGrp.node], sources = [mainJnts[k].node], connectScale = True)

		FKAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fk" + names[k] + "Ref", value= "", replace = True)[0]
		fkRef.node.message >> FKAttr 

	fkRefsA = []
	for k, fkCtrl in enumerate([fkRoot, fkMid, fkEnd]):
		fkRefGrp = mnsUtils.createNodeReturnNameStd(parentNode = rigComponentsGrp, side = fkCtrl.side, body = fkCtrl.body + "RefAOffset", alpha = fkCtrl.alpha, id = fkCtrl.id, buildType = "group", incrementAlpha = False)
		fkRefGrp.node.v.set(False)
		fkRef = mnsUtils.createNodeReturnNameStd(parentNode = fkRefGrp, side = fkCtrl.side, body = fkCtrl.body + "RefA", alpha = fkCtrl.alpha, id = fkCtrl.id, buildType = "locator", incrementAlpha = False)
		fkRefs.append(fkRef)
		mnsNodes.mnsMatrixConstraintNode(side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id, targets = [fkRefGrp.node], sources = [mainJnts[k].node], connectScale = True)
		pm.matchTransform(fkRef.node, fkCtrl.node)

		FKAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fk" + names[k] + "RefA", value= "", replace = True)[0]
		fkRef.node.message >> FKAttr 

	#transfer authority
	blkUtils.transferAuthorityToCtrl(rootJnt, rootTweak)
	rootJnt.node.scale.disconnect()
	blkUtils.transferAuthorityToCtrl(midJnt, midTweak)
	midJnt.node.scale.disconnect()
	blkUtils.transferAuthorityToCtrl(endJnt, endTweak)
	endJnt.node.scale.disconnect()

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
		startPositionLoc = mnsUtils.createNodeReturnNameStd(parentNode = animGrp,side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "StartPosition", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		startPositionLoc.node.v.set(False)
		
		parentConstraint = mnsNodes.mayaConstraint([fkRefs[0].node], startPositionLoc.node, type = "parent", maintainOffset = True, side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id)
		parentConstraint.node.interpType.set(0)
		scaleConstraint = mnsNodes.mayaConstraint([fkRefs[0].node], startPositionLoc.node, type = "scale", maintainOffset = False, side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id)
					
		#mnsNodes.mnsMatrixConstraintNode(side = fkCtrl.side, alpha = fkCtrl.alpha, id = fkCtrl.id, targets = [startPositionLoc.node], sources = [fkRefs[0].node], connectScale = True)
		
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
		nameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "SleevePosition", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(builtGuides[0].node, nameStd.node))
		custGuides.append(nameStd)
		parentDict.update({nameStd: builtGuides[0]})
		nameStd.node.inheritsTransform.set(False)
		nameStd.node.localScale.set((2,2,2))

		btcNode = mnsNodes.mnsBuildTransformsCurveNode(
									side = builtGuides[0].side, 
									alpha = builtGuides[0].alpha, 
									id = builtGuides[0].id, 
									body = builtGuides[0].body + "SleeveGuide", 
									transforms = builtGuides, 
									deleteCurveObjects = True, 
									tangentDirection = 2, 
									buildOffsetCurve = True,
									degree = 1,
									offsetX = builtGuides[0].node.offsetX.get(),
									offsetY = 0.0,
									offsetZ = builtGuides[0].node.offsetZ.get())
		blkUtils.connectSlaveToDeleteMaster(btcNode["node"], nameStd)

		pocn = mnsNodes.mnsPointsOnCurveNode(
									side = builtGuides[0].side, 
									alpha = builtGuides[0].alpha, 
									id = builtGuides[0].id, 
									body = builtGuides[0].body + "SleeveGuide", 
									inputCurve = btcNode["node"].node.outCurve,
									inputUpCurve = btcNode["node"].node.outOffsetCurve,
									buildOutputs = False,
									transforms = [nameStd.node],
									buildType = 3,
									doScale = False,
									aimAxis = 1,
									upAxis = 0,
									numOutputs = 2
									)
		sleevePosAttr = mnsUtils.addAttrToObj([nameStd.node], type = "float", value = 1.0, name = "sleevePosition", replace = True, min = 0.0, max = 1.0)
		mnsNodes.mdlNode(sleevePosAttr[0], 2.0, pocn["node"].node.uOffset )
		mnsUtils.lockAndHideTransforms(nameStd.node, lock = True)

		nameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "PoleVector", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		nameStd.node.localScale.set((2,2,2))
		pm.delete(pm.parentConstraint(builtGuides[1].node, nameStd.node))
		custGuides.append(nameStd)
		parentDict.update({nameStd: builtGuides[1]})

	return custGuides, parentDict

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
		if rootGuide.node.attr("interpolationJoints").get() >= len(guides):
			status, offsetX = mnsUtils.validateAttrAndGet(rootGuide, "offsetX", 10.0)
			status, offsetY = mnsUtils.validateAttrAndGet(rootGuide, "offsetY", 0.0)
			status, offsetZ = mnsUtils.validateAttrAndGet(rootGuide, "offsetZ", 0.0)

			status, scaleMode = mnsUtils.validateAttrAndGet(rootGuide, "scaleMode", 2)
			status, squashMode = mnsUtils.validateAttrAndGet(rootGuide, "squashMode", 0)

			if not softMod:
				#build structure
				btcNode = mnsNodes.mnsBuildTransformsCurveNode(
										side = rootGuide.side, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id, 
										body = rootGuide.body, 
										transforms = transforms, 
										deleteCurveObjects = True, 
										tangentDirection = 2, 
										buildOffsetCurve = True,
										degree = 1,
										offsetX = offsetX,
										offsetY = offsetY,
										offsetZ = offsetZ)
				blkUtils.connectSlaveToDeleteMaster(btcNode["node"], rootGuide)

				sections = 2
				status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
				if doTweakers:
					status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
					sections = (tweakersPerSection * 2) + 2


				inputCurve, inputUpCurve = None, None
				for curveType in ["curve", "upCurve"]:
					outCurveAttrName = "outCurve"
					if curveType == "upCurve": outCurveAttrName = "outOffsetCurve"

					#create re-sampleCurve and reconnect
					rscNode = mnsNodes.mnsResampleCurveNode(side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body, 
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


				returnData = pocn["samples"]

				customGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, customGuidesOnly = True)
				sleeveGuide = None
				for cg in customGuides:
					if "sleeveposition" in cg.name.lower():
						sleeveGuide = cg
						sleeveGuide.node.v.set(False)
						break

				status, doSleeve = mnsUtils.validateAttrAndGet(rootGuide, "doSleeve", False)
				if doSleeve and sleeveGuide:
					status, numSleeveJoints = mnsUtils.validateAttrAndGet(rootGuide, "numSleeveJoints", 3)
					status, sleeveCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "sleeveCurveDegree", 3)
					status, sleeveBuildMode = mnsUtils.validateAttrAndGet(rootGuide, "sleeveBuildMode", 0)

					#deleteCurrent pocn
					existingPocn = [n for n in sleeveGuide.node.sleevePosition.listConnections(d = True, s = False) if type(n) == pm.nodetypes.MnsPointsOnCurve]
					if existingPocn: pm.delete(existingPocn)

					if pocn:
						#build structure
						sleeveBtcNode = mnsNodes.mnsBuildTransformsCurveNode(
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body, 
												transforms = pocn["samples"], 
												deleteCurveObjects = True, 
												tangentDirection = 2, 
												buildOffsetCurve = True,
												buildMode = sleeveBuildMode,
												degree = sleeveCurveDegree,
												offsetX = offsetX,
												offsetY = offsetY,
												offsetZ = offsetZ)
						blkUtils.connectSlaveToDeleteMaster(sleeveBtcNode["node"], rootGuide)

						sleevePocn = mnsNodes.mnsPointsOnCurveNode(
														side = rootGuide.side, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id, 
														body = rootGuide.body + "SleeveInterp", 
														inputCurve = sleeveBtcNode["node"].node.outCurve,
														inputUpCurve = sleeveBtcNode["node"].node.outOffsetCurve,
														buildOutputs = True,
														buildType = 4, #interpLocsType
														buildMode = 0,
														doScale = False,
														aimAxis = 1,
														upAxis = 0,
														numOutputs = numSleeveJoints
														)
						returnData = {"Main": returnData, "Sleeve": sleevePocn["samples"]}
						
						if sleeveGuide: 
							sleeveGuide.node.sleevePosition >> sleevePocn["node"].node.uScale
							sleeveGuide.node.v.set(True)
						
				return returnData
			else:
				#find btcNode and poc node
				primBtcNode, primPocNode, resampleCurve, resampleCurveOffset = None, None, None, None
				relatedRootJnt = mnsUtils.validateNameStd(rootGuide.node.jntSlave.get())
				outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
				if outConnections:
					for con in outConnections: 
						if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
							primBtcNode = con
							outConnections = primBtcNode.outCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										resampleCurve = con

							outConnections = primBtcNode.outOffsetCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										resampleCurveOffset = con

							if resampleCurve:
								outConnections = resampleCurve.outCurve.listConnections(s = False, d = True)
								if outConnections:
									for con in outConnections: 
										if type(con) == pm.nodetypes.MnsPointsOnCurve:
											primPocNode = con
							break

				#find sleeve nodes
				sleeveBtcNode, sleevePocNode, sleeveGuide = None, None, None
				customGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, customGuidesOnly = True)
				for cg in customGuides:
					if "sleeveposition" in cg.name.lower():
						sleeveGuide = cg
						outConnections = sleeveGuide.node.sleevePosition.listConnections(s = False, d = True)
						for con in outConnections: 
							if type(con) == pm.nodetypes.MnsPointsOnCurve:
								sleevePocNode = con
								outConnections = sleevePocNode.curve.listConnections(s = True, d = False)
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
										sleeveBtcNode = con
										break
								break
						break

				#adjust the nodes
				if primBtcNode and primPocNode:
					primBtcNode.offsetX.set(offsetX)
					primBtcNode.offsetY.set(offsetY)
					primBtcNode.offsetZ.set(offsetZ)

				if resampleCurve:
					sections = 2
					status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
					if doTweakers:
						status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
						sections = (tweakersPerSection * 2) + 2
					
					resampleCurve.sections.set(sections)
					if resampleCurveOffset: resampleCurveOffset.sections.set(sections)

				if sleeveBtcNode:
					status, sleeveCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "sleeveCurveDegree", 3)
					status, sleeveBuildMode = mnsUtils.validateAttrAndGet(rootGuide, "sleeveBuildMode", 0)
					sleeveBtcNode.degree.set(sleeveCurveDegree)
					sleeveBtcNode.buildMode.set(sleeveBuildMode)

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
							if inConnections:
								for inCon in inConnections:
									if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
										psocn = inCon
										psocn.excludeBaseRotation.set(True)
										psocn.resetScale.set(1)
										psocn.doScale.set(0)
										break

							sections = 2
							status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
							if doTweakers:
								status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
								sections = (tweakersPerSection * 2) + 2
						
							outConnections = btcNode.outCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										resampleCurve = con
										blkUtils.connectIfNotConnected(resampleCurve.outCurve, psocn.curve)
										resampleCurve.sections.disconnect()
										resampleCurve.sections.set(sections)

							outConnections = btcNode.outOffsetCurve.listConnections(s = False, d = True)
							if outConnections:
								for con in outConnections: 
									if type(con) == pm.nodetypes.MnsResampleCurve:
										resampleCurveOffset = con
										blkUtils.connectIfNotConnected(resampleCurveOffset.outCurve, psocn.upCurve)
										resampleCurveOffset.sections.disconnect()
										resampleCurveOffset.sections.set(sections)	
							break

		status, doSleeve = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doSleeve", False)
		if doSleeve:
			##collect costum guides
			customGuides = MnsBuildModule.cGuideControls
			sleeveGuide = [g for g in customGuides if "SleevePosition" in g.name]
			if sleeveGuide: 
				sleeveGuide = sleeveGuide[0]
				destanationPocn = sleeveGuide.node.destinationPocn.get()
				if destanationPocn:
					sleeveGuide.node.sleevePosition >> destanationPocn.uScale
