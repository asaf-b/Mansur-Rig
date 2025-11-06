"""Author: Asaf Ben-Zur
Best used for: Hind-Legs
This module was designed to create a generic 4 joint limb control.
This module will create both the FK and IK controls, and the standard blend control.
On top of the standard behaviour, based on parameters, this module can also include bendy limb controls (as many as you want).
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
	from mansur.core import prefixSuffix

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
	midJntB = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[2]))	
	endJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[3]))	

	#collect global attrs
	status, scaleMode = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "scaleMode", 2)
	status, squashMode = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "squashMode", 0)

	status, rootControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "rootControlShape", "lightSphere")
	status, ikHandleControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ikHandleControlShape", "square")
	status, poleVectorControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "poleVectorControlShape", "diamond")
	status, ankleBendControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ankleBendControlShape", "square")
	status, fkControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "fkControlShape", "hexagon")
	status, tertiariesControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "tertiariesControlShape", "flatDiamond")

	#collections declare
	rscNodes = []

	### root ctrl
	rootCtrl = blkCtrlShps.ctrlCreate(controlShape = rootControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale, 
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

	if psocn: blkUtils.getGlobalScaleAttrFromTransform(rootCtrl) >> psocn.globalScale

	#first create the source of the 3bSolve
	import maya.mel as mel
	mel.eval('ikSpringSolver')

	ikSolverGrp = mnsUtils.createNodeReturnNameStd(parentNode = rigComponentsGrp.node, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IkSolve", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	ikSolverGrp.node.v.set(False)
	pm.matchTransform(ikSolverGrp.node, rootJnt.node, pos = True, rot = False, scl = False)

	pm.select(d = True)
	solveSourceJntA = mnsUtils.createNodeReturnNameStd(parentNode = ikSolverGrp, side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveSource", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	solveSourceJntA.node.v.set(False)
	pm.matchTransform(solveSourceJntA.node, rootJnt.node, pos = True, rot = False, scl = False)
	solveSourceJntB = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveSource", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveSourceJntB.node, midJnt.node, pos = True, rot = False, scl = False)
	pm.parent(solveSourceJntB.node, solveSourceJntA.node)
	pm.joint(solveSourceJntA.node, e = True, sao = "yup", oj = "xyz", zso = True)
	solveSourceJntC = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveSource", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveSourceJntC.node, midJntB.node, pos = True, rot = False, scl = False)
	pm.parent(solveSourceJntC.node, solveSourceJntB.node)
	pm.joint(solveSourceJntB.node, e = True, sao = "yup", oj = "xyz", zso = True)
	solveSourceJntD = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveSource", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveSourceJntD.node, endJnt.node, pos = True, rot = False, scl = False)
	pm.parent(solveSourceJntD.node, solveSourceJntC.node)
	pm.joint(solveSourceJntC.node, e = True, sao = "yup", oj = "xyz", zso = True)
	solveSourceJntD.node.jointOrient.set([0.0,0.0,0.0])


	#create the solver
	ikSpringHandle = pm.ikHandle(sj = solveSourceJntA.node, ee = solveSourceJntD.node, solver = "ikSpringSolver")[0]
	
	if pm.xform(solveSourceJntB.node, q = True, ws = True, t = True) != pm.xform(midJnt.node, q = True, ws = True, t = True):
		ikSpringHandle.twist.set(180)

	pm.parent(ikSpringHandle, ikSolverGrp.node)
	status, ikSpringEffector = mnsUtils.validateAttrAndGet(ikSpringHandle, "endEffector", None)
	#rename the effector and handle
	ikSpringHandleStd = prefixSuffix.MnsNameStd(side = rootGuide.side, body = rootGuide.body + "SourceIkHandle", alpha = rootGuide.alpha, id = rootGuide.id, type = prefixSuffix.mnsTypeDict["ikHandle"])
	ikSpringHandle.rename(ikSpringHandleStd.name)
	ikSpringHandleStd.node = ikSpringHandle
	ikSpringEffectorStd = prefixSuffix.MnsNameStd(side = rootGuide.side, body = rootGuide.body + "SourceEffector", alpha = rootGuide.alpha, id = rootGuide.id, type = prefixSuffix.mnsTypeDict["ikEffoctor"])
	ikSpringEffector.rename(ikSpringEffectorStd.name)
	ikSpringEffectorStd.node = ikSpringEffector

	#create all needed ctrls for the ik setup
	##create ik controls group
	ikControlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IkControls", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)

	###ik handle control
	status, ikHandleMatchOrient = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "iKHandleMatchOrient", False)
	if ikHandleMatchOrient: ikHandleMatchOrient = mnsUtils.validateNameStd(ikHandleMatchOrient)

	ikCtrl = blkCtrlShps.ctrlCreate(parentNode = animStaticGrp, 
									controlShape = ikHandleControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 2, 
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
	ikHandleOffsetGrp = blkUtils.getOffsetGrpForCtrl(ikCtrl, type = "offsetGrp")

	##match orient feature
	if ikHandleMatchOrient:
		if ikHandleOffsetGrp:
			pm.delete(pm.orientConstraint(ikHandleMatchOrient.node, ikHandleOffsetGrp.node))

	### poleVector
	poleVector = blkCtrlShps.ctrlCreate(parentNode = ikControlsGrp, 
										controlShape = poleVectorControlShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 0.75, 
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

	poleVectorB = blkCtrlShps.ctrlCreate(parentNode = poleVector, 
										controlShape = poleVectorControlShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 0.4, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "PoleVectorB", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = poleVecGuide.node, 
										createSpaceSwitchGroup = False,
										symmetryType = symmetryType,
										doMirror = False,
										isFacial = MnsBuildModule.isFacial)

	primaryCtrls.append(poleVectorB)
	
	pvCns = mnsNodes.mayaConstraint([poleVector.node], ikSpringHandleStd.node, type = "poleVector")
	

	#create the ik solve
	parentConstraint = mnsNodes.mayaConstraint([ikCtrl.node], ikSpringHandleStd.node, type = "parent", maintainOffset = True)
	

	#create the secondary joint herirachy
	pm.select(d = True)
	solveTargetJntA = mnsUtils.createNodeReturnNameStd(parentNode = ikSolverGrp, side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveTarget", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveTargetJntA.node, rootJnt.node, pos = True, rot = False, scl = False)
	solveTargetJntB = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveTarget", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveTargetJntB.node, midJnt.node, pos = True, rot = False, scl = False)
	pm.parent(solveTargetJntB.node, solveTargetJntA.node)
	pm.joint(solveTargetJntA.node, e = True, sao = "yup", oj = "xyz", zso = True)
	solveTargetJntC = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveTarget", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveTargetJntC.node, midJntB.node, pos = True, rot = False, scl = False)
	pm.parent(solveTargetJntC.node, solveTargetJntB.node)
	pm.joint(solveTargetJntB.node, e = True, sao = "yup", oj = "xyz", zso = True)
	solveTargetJntD = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "SolveTarget", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "joint", createBlkClassID = True, incrementAlpha = False)
	pm.matchTransform(solveTargetJntD.node, endJnt.node, pos = True, rot = False, scl = False)
	pm.parent(solveTargetJntD.node, solveTargetJntC.node)
	pm.joint(solveTargetJntC.node, e = True, sao = "yup", oj = "xyz", zso = True)
	solveTargetJntD.node.jointOrient.set([0.0,0.0,0.0])

	ik2BHandle = pm.ikHandle(sj = solveTargetJntA.node, ee = solveTargetJntC.node)[0]
	pm.parent(ik2BHandle, ikSolverGrp.node)
	status, ik2BEffector = mnsUtils.validateAttrAndGet(ik2BHandle, "endEffector", None)
	#rename the effector and handle
	ik2BHandleStd = prefixSuffix.MnsNameStd(side = rootGuide.side, body = rootGuide.body + "TargetIkHandle", alpha = rootGuide.alpha, id = rootGuide.id, type = prefixSuffix.mnsTypeDict["ikHandle"])
	ik2BHandle.rename(ik2BHandleStd.name)
	ik2BHandleStd.node = ik2BHandle
	ik2BEffectorStd = prefixSuffix.MnsNameStd(side = rootGuide.side, body = rootGuide.body + "TargetEffector", alpha = rootGuide.alpha, id = rootGuide.id, type = prefixSuffix.mnsTypeDict["ikEffoctor"])
	ik2BEffector.rename(ik2BEffectorStd.name)
	ik2BEffectorStd.node = ik2BEffector
	pvCns = mnsNodes.mayaConstraint([poleVectorB.node], ik2BHandleStd.node, type = "poleVector")

	###ik Bend Control
	ankleBendCtrl = blkCtrlShps.ctrlCreate(parentNode = ikHandleOffsetGrp, 
									controlShape = ankleBendControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 0.75, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "AnkleBend", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = endJnt.node, 
									createOffsetGrp = True,
									createSpaceSwitchGroup = False,
									symmetryType = symmetryType,
									doMirror = False,
									isFacial = MnsBuildModule.isFacial)
	primaryCtrls.append(ankleBendCtrl)
	mnsUtils.lockAndHideTransforms(ankleBendCtrl.node, rx = False, rz = False, lock = True)

	secondaryIKCnsLoc = mnsUtils.createNodeReturnNameStd(parentNode = ankleBendCtrl, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "2BIKTarget", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	secondaryIKCnsLoc.node.v.set(False)
	secondaryIKCnsLoc.node.v.setLocked(True)
	pm.matchTransform(secondaryIKCnsLoc.node, midJntB.node, solveTargetJntC.node, pos = True, rot = False, scl = False)
	
	ik2BHandleOSGrp = mnsUtils.createOffsetGroup(ik2BHandleStd)
	pointCns = mnsNodes.mayaConstraint([secondaryIKCnsLoc.node], ik2BHandleOSGrp.node, type = "point", maintainOffset = True)
	
	ankleBendCtrlOffsetGrp = blkUtils.getOffsetGrpForCtrl(ankleBendCtrl, type = "offsetGrp")
	pointCns = mnsNodes.mayaConstraint([ikCtrl.node], ankleBendCtrlOffsetGrp.node, type = "point", maintainOffset = True)
	orientCns = mnsNodes.mayaConstraint([solveSourceJntC.node], ankleBendCtrlOffsetGrp.node, type = "orient", maintainOffset = True)
	aimCns = mnsNodes.mayaConstraint([ikCtrl.node], solveTargetJntC.node, type = "aim", aimVector = [1.0,0.0,0.0], upVector = [0.0,1.0,0.0], maintainOffset = False, worldUpObject = poleVector.node.nodeName())

	#connect pole vectors and bend bias
	devider = mnsUtils.addAttrToObj([ikCtrl.node], type = "enum", value = ["______"], name = "IkAttributes", replace = True)
	bendBiasAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = 0.5, name = "bendBias", replace = True, min = 0.0, max = 1.0)[0]
	bendBiasAttr >> ikSpringHandleStd.node.springAngleBias[0].springAngleBias_FloatValue
	revNode = mnsNodes.reverseNode([bendBiasAttr,0,0], 
								[ikSpringHandleStd.node.springAngleBias[1].springAngleBias_FloatValue, 0.0, 0.0],
								side = MnsBuildModule.rootGuide.side, 
								body = MnsBuildModule.rootGuide.body + "BendBias", 
								alpha = MnsBuildModule.rootGuide.alpha, 
								id = MnsBuildModule.rootGuide.id)

	#create the stretch solve
	stretchLimitAttr = mnsUtils.addAttrToObj([ikCtrl.node], type = "float", value = allGuides[0].node.stretchLimit.get(), name = "stretchLimit", replace = True, min = 1.0)[0]
	
	solveDistance2B = mnsNodes.distBetweenNode(rootCtrl.node.worldMatrix[0], ik2BHandleStd.node.worldMatrix[0], None)
	chainLength2B = mnsUtils.distBetween(solveTargetJntA.node, solveTargetJntB.node) + mnsUtils.distBetween(solveTargetJntB.node, solveTargetJntC.node)
	solveDistance3B = mnsNodes.distBetweenNode(rootCtrl.node.worldMatrix[0], ikSpringHandleStd.node.worldMatrix[0], None)
	chainLength3B = chainLength2B + mnsUtils.distBetween(solveTargetJntC.node, solveTargetJntD.node)
	
	globalScaleAttr = blkUtils.getGlobalScaleAttrFromTransform(rootCtrl)
	mdNodeGlobScale = mnsNodes.mdNode([globalScaleAttr, 1.0,1.0], 
								[chainLength2B, 1.0, 1.0], operation = 1)

	mdNodeA = mnsNodes.mdNode([solveDistance2B.node.distance, 1.0,1.0], 
								[mdNodeGlobScale.node.outputX, 1.0, 1.0], operation = 2)
	conditionNodeA = mnsNodes.conditionNode(solveDistance2B.node.distance, 
											mdNodeGlobScale.node.outputX, 
											mdNodeA.node.output, 
											[1.0,1.0,1.0], 
											None, 
											operation = 2)
	
	mdNodeGlobScaleA = mnsNodes.mdNode([globalScaleAttr, 1.0,1.0], 
								[chainLength3B, 1.0, 1.0], operation = 1)


	mdNodeB = mnsNodes.mdNode([solveDistance3B.node.distance, 1.0,1.0], 
								[mdNodeGlobScaleA.node.outputX, 1.0, 1.0], operation = 2)
	

	conditionNodeB = mnsNodes.conditionNode(solveDistance3B.node.distance, 
											mdNodeGlobScaleA.node.outputX, 
											[1.0,1.0,1.0], 
											conditionNodeA.node.outColor, 
											None, 
											operation = 2)

	conditionNodeC = mnsNodes.conditionNode(solveDistance3B.node.distance, 
											mdNodeGlobScaleA.node.outputX, 
											mdNodeB.node.output, 
											[1.0,1.0,1.0], 
											None, 
											operation = 2)
	mdNodeC = mnsNodes.mdNode(conditionNodeB.node.outColor, 
								conditionNodeC.node.outColor)

	clampNode = mnsNodes.clampNode(mdNodeC.node.output, 
									[stretchLimitAttr, stretchLimitAttr, stretchLimitAttr],
									[1.0, 1.0, 1.0],
									None)
	clampNode.node.output >> solveTargetJntA.node.s

	#create ik connectors
	ikConnectorsGroup = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IkLocs", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	ikConnectorsGroup.node.v.set(0)
	pm.parent(ikConnectorsGroup.node, rigComponentsGrp.node)
	rootLoc = mnsUtils.createNodeReturnNameStd(parentNode = ikConnectorsGroup, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RootConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)
	pm.matchTransform(rootLoc.node, rootJnt.node)
	midLoc = mnsUtils.createNodeReturnNameStd(parentNode = rootLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)
	pm.matchTransform(midLoc.node, midJnt.node)
	midLocB = mnsUtils.createNodeReturnNameStd(parentNode = midLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidBConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)
	pm.matchTransform(midLocB.node, midJntB.node)
	endLoc = mnsUtils.createNodeReturnNameStd(parentNode = midLocB, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EndConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False, segmentScaleCompensate = False)
	pm.matchTransform(endLoc.node, endJnt.node)

	###lowest level tweakers
	jntTweakersGrp = mnsUtils.createNodeReturnNameStd(parentNode = ikControlsGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "JntTweakers", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	rootTweak = blkCtrlShps.ctrlCreate(parentNode = jntTweakersGrp, 
										controlShape = tertiariesControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 2, 
										scale = modScale * 0.5, 
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
	ikSpringHandleStd.node.message >> ikSolverMesAttr
	ikCtrlAttrA = mnsUtils.addAttrToObj([rootTweak.node], type = "message", name = "ikCtrl", value= "", replace = True)[0]
	ikCtrl.node.message >> ikCtrlAttrA 
	ik2BSolverMesAttr = mnsUtils.addAttrToObj([rootTweak.node], type = "message", name = "ik2BSolver", value= "", replace = True)[0]
	ik2BHandleStd.node.message >> ik2BSolverMesAttr

	mnsNodes.mayaConstraint(rootCtrl.node, ikSolverGrp.node, type = "parent", maintainOffset = True)
	mnsNodes.mayaConstraint(rootCtrl.node, ikSolverGrp.node, type = "scale", maintainOffset = True)

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

	midTweakB = blkCtrlShps.ctrlCreate(parentNode = jntTweakersGrp, 
										controlShape = ikHandleControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 1, 
										scale = modScale * 0.7, 
										alongAxis = 1,  
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "MidTweakB", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = midJntB.node, 
										createOffsetGrp = True, 
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial)

	midBOffsetGrp =blkUtils.getOffsetGrpForCtrl(midTweakB)
	secondaryCtrls.append(midTweakB)

	endTweak = blkCtrlShps.ctrlCreate(parentNode = jntTweakersGrp,
										controlShape = tertiariesControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 2, 
										scale = modScale * 0.5, 
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
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [midBOffsetGrp.node], sources = [midLocB.node], connectScale = True)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [endOffsetGrp.node], sources = [endLoc.node], connectScale = False)
	
	##FK controls
	status, FKSymmetryType = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "FKSymmetryType", 0)
	fkRoot = blkCtrlShps.ctrlCreate(parentNode = rootCtrl, 
									controlShape = fkControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 1.5, 
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
									scale = modScale * 1.5, 
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

	fkMidB = blkCtrlShps.ctrlCreate(parentNode = fkMid, 
									controlShape = fkControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 1.5, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "FK", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id + 2,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = midJntB.node, 
									createOffsetGrp = True,
									symmetryType = FKSymmetryType,
									doMirror = True,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = midJnt)
	primaryCtrls.append(fkMidB)
	FKMidBAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "fkMidB", value= "", replace = True)[0]
	fkMidB.node.message >> FKMidBAttr

	fkEnd = blkCtrlShps.ctrlCreate(parentNode = fkMidB, 
									controlShape = fkControlShape, 
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 1.5, 
									alongAxis = 1, 
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "FK", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id + 3,
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

	#create bridge FK locs (solving mirroring issues)
	fkConnectorsGroup = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "FkLocs", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	fkConnectorsGroup.node.v.set(0)
	pm.parent(fkConnectorsGroup.node, rigComponentsGrp.node)

	fkRootLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkConnectorsGroup, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RootFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(fkRootLoc.node, rootLoc.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkRootLoc.node], sources = [fkRoot.node], connectScale = True, maintainOffset = True)

	fkMidLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkRootLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(fkMidLoc.node, midLoc.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkMidLoc.node], sources = [fkMid.node], connectScale = True, maintainOffset = True)

	fkMidLocB = mnsUtils.createNodeReturnNameStd(parentNode = fkMidLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidBFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(fkMidLocB.node, midLocB.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkMidLocB.node], sources = [fkMidB.node], connectScale = True, maintainOffset = True)

	fkEndLoc = mnsUtils.createNodeReturnNameStd(parentNode = fkMidLocB, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EndFkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(fkEndLoc.node, endLoc.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [fkEndLoc.node], sources = [fkEnd.node], connectScale = True, maintainOffset = True)
	mnsUtils.zeroJointOrient(fkRootLoc.node)

	#create bridge IK locs
	ikConnectorsGroup = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IkLocs", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	ikConnectorsGroup.node.v.set(0)
	pm.parent(ikConnectorsGroup.node, rigComponentsGrp.node)

	ikRootLoc = mnsUtils.createNodeReturnNameStd(parentNode = ikConnectorsGroup, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RootIkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(ikRootLoc.node, rootLoc.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [ikRootLoc.node], sources = [solveTargetJntA.node], connectScale = True, maintainOffset = True)

	ikMidLoc = mnsUtils.createNodeReturnNameStd(parentNode = ikRootLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidIkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(ikMidLoc.node, midLoc.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [ikMidLoc.node], sources = [solveTargetJntB.node], connectScale = True, maintainOffset = True)

	ikMidLocB = mnsUtils.createNodeReturnNameStd(parentNode = ikMidLoc, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "MidBIkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(ikMidLocB.node, midLocB.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [ikMidLocB.node], sources = [solveTargetJntC.node], connectScale = True, maintainOffset = True)

	ikEndLoc = mnsUtils.createNodeReturnNameStd(parentNode = ikMidLocB, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EndIkConnector", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "joint", incrementAlpha = False)
	pm.matchTransform(ikEndLoc.node, endLoc.node)
	mnsNodes.mnsMatrixConstraintNode(side = MnsBuildModule.rootGuide.side, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, targets = [ikEndLoc.node], sources = [solveTargetJntD.node], connectScale = True, maintainOffset = True)
	mnsUtils.zeroJointOrient(ikRootLoc.node)

	#create ikfk blend attr
	status, blendDefault = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ikFkBlendDefault", 0)
	fkIkBlendAttr = mnsUtils.addAttrToObj([attrHost.node], type = "int", value = int(blendDefault), name = "ikFkBlend", replace = True, max = 1, min = 0)[0]
	blendAttrHolder = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "blendAttrHolder", value= "", replace = True)[0]
	attrHost.node.message >> blendAttrHolder

	#create root twist mute attribute
	muteRootTwistAttr = mnsUtils.addAttrToObj([attrHost.node], type = "float", value = 1.0, name = "muteRootTwist", replace = True, max = 1.0, min = 0.0)[0]

	#fkIkBlendAttr >> ikSolverNode.node.blend
	blendDict = {
				"root": {"target": rootLoc, "sources": [ikRootLoc.node, fkRootLoc.node]},
				"midA": {"target": midLoc, "sources": [ikMidLoc.node, fkMidLoc.node]},
				"midB": {"target": midLocB, "sources": [ikMidLocB.node, fkMidLocB.node]},
				"end": {"target": endLoc, "sources": [ikEndLoc.node, fkEndLoc.node]}
				}

	blendRev = mnsNodes.reverseNode([fkIkBlendAttr,0,0], 
								None,
								side = animGrp.side, 
								body = animGrp.body + "IkFk", 
								alpha = animGrp.alpha, 
								id = animGrp.id)
	
	for targetKey in blendDict:
		target = blendDict[targetKey]["target"]
		sources = blendDict[targetKey]["sources"]

		blendParCns = mnsNodes.mayaConstraint(sources, target, type = "parent", maintainOffset = False)
		blendScaleCns = mnsNodes.mayaConstraint(sources, target, type = "scale", maintainOffset = False)
		
		blendRev.node.outputX >> blendParCns.node.attr(sources[0].nodeName() + "W0")
		blendRev.node.outputX >> blendScaleCns.node.attr(sources[0].nodeName() + "W0")
		fkIkBlendAttr >> blendParCns.node.attr(sources[1].nodeName() + "W1")
		fkIkBlendAttr >> blendScaleCns.node.attr(sources[1].nodeName() + "W1")
		
		#convert rot blend to quat slerp
		#for axis in "xyz": target.node.attr("r" + axis).disconnect()
		#sourceADecMat = mnsNodes.decomposeMatrixNode(sources[0].matrix, None,None,None)
		#sourceBDecMat = mnsNodes.decomposeMatrixNode(sources[1].matrix, None,None,None)

		#quatSlerpNode = mnsNodes.quatSlerpNode(sourceADecMat.node.outputQuat, sourceBDecMat.node.outputQuat, None)
		#quatToEulerNode = mnsNodes.quatToEulerNode(quatSlerpNode.node.outputQuat, target.node.r)
		
	#connect vis chennels
	for fkCtrl in [fkRoot, fkMid, fkMidB, fkEnd]:
		fkIkBlendAttr >> fkCtrl.node.v
	for ikC in [ikCtrl, poleVector, ankleBendCtrl]:
		blendRev.node.outputX >> ikC.node.v

	#connect twekers to pocn as tweakers
	tweakerIndex = 0
	tweakPos = 0.0
	for tweakCtrl in [rootTweak, midTweak, midTweakB, endTweak]:
		mnsUtils.addAttrToObj([tweakCtrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
		falloffAttr = mnsUtils.addAttrToObj([tweakCtrl.node], type = "float", value = 0.5, name = "scaleFalloff", replace = True, min = 0.01)[0]
		falloffAttr >> psocn.customPosition[tweakerIndex].falloff

		tweakCtrl.node.sy >> psocn.customPosition[tweakerIndex].scaleAim
		tweakCtrl.node.sz >> psocn.customPosition[tweakerIndex].scaleUp
		tweakCtrl.node.sx >> psocn.customPosition[tweakerIndex].tertiaryScale
		psocn.customPosition[tweakerIndex].uPosition.set(tweakPos)
		tweakPos += 0.333
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

		blendNode = mnsNodes.blendColorsNode(tweakCtrl.node.s, 
							[1.0, 1.0, 1.0],
							blendRev.node.outputX,
							[psocn.customPosition[tweakerIndex].scaleAim, psocn.customPosition[tweakerIndex].scaleUp, psocn.customPosition[tweakerIndex].tertiaryScale],
							side = animGrp.side, 
							body = animGrp.body + "HandleScalMute", 
							alpha = animGrp.alpha, 
							id = animGrp.id)

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

			numTweakControls = (tweakersPerSection * 3) + 4
			tweakerControls = []
			twekersOffsets = []
			
			for k in range(numTweakControls):
				tweakerCtrl = blkCtrlShps.ctrlCreate(parentNode = tweakerGrp, 
										controlShape = tweakControlShape, 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 1, 
										scale = modScale, 
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
				if k % (tweakersPerSection + 1) == 0:
					pm.delete(tweakerCtrl.node.getShapes())

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
			blkUtils.getGlobalScaleAttrFromTransform(rootCtrl) >> TweakPocn["node"].node.globalScale

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
			blkUtils.getGlobalScaleAttrFromTransform(rootCtrl) >> tweakCurveBaseBtc["node"].node.globalScale

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
			blkUtils.getGlobalScaleAttrFromTransform(rootCtrl) >> tweakCurveBtc["node"].node.globalScale

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
			#btcNode["node"].node.resample.set(True)
			# (tweakersPerSection * numOfSections * numberOfPositionsPerTweaker) + 3(base, mid, root)
			#btcNode["node"].node.substeps.set((tweakersPerSection * 3 * 3) + 3)

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

	angleBendRef = mnsUtils.createNodeReturnNameStd(side = source.side, body = source.body + "angleBendRef", alpha = source.alpha, id = source.id, buildType = "locator", incrementAlpha = False)
	pm.parent(angleBendRef.node, ankleBendCtrl.node)
	pm.delete(pm.parentConstraint(fkMidB.node, angleBendRef.node))
	pm.delete(pm.scaleConstraint(fkMidB.node, angleBendRef.node))
	angleBendRef.node.v.set(False)
	angleBendRefAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "angleBendRef", value= "", replace = True)[0]
	angleBendRef.node.message >> angleBendRefAttr 

	ankleBendCtrlAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "ankleBendCtrl", value= "", replace = True)[0]
	ankleBendCtrl.node.message >> ankleBendCtrlAttr 

	#fk refs
	mainJnts = [rootJnt, midJnt, midJntB, endJnt]
	names = ["Root", "Mid", "MidB", "End"]
	fkRefs = []
	for k, fkCtrl in enumerate([fkRoot, fkMid, fkMidB, fkEnd]):
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
	blkUtils.transferAuthorityToCtrl(midJntB, midTweakB)
	midJntB.node.scale.disconnect()
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
		endPositionLoc.node.worldMatrix[0] >> primBtcNode.transforms[3].matrix

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

				sections = 3
				status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
				if doTweakers:
					status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
					sections = (tweakersPerSection * 3) + 3


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

				#adjust the nodes
				if primBtcNode and primPocNode:
					primBtcNode.offsetX.set(offsetX)
					primBtcNode.offsetY.set(offsetY)
					primBtcNode.offsetZ.set(offsetZ)

				if resampleCurve:
					sections = 3
					status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
					if doTweakers:
						status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
						sections = (tweakersPerSection * 3) + 3
					
					resampleCurve.sections.set(sections)
					if resampleCurveOffset: resampleCurveOffset.sections.set(sections)

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
							endJnt = mnsUtils.validateNameStd(MnsBuildModule.guideControls[2].node.jntSlave.get())
							endJnt.node.worldMatrix[0] >> btcNode.transforms[3].matrix
							relatedRootJnt.node.worldMatrix[0] >> btcNode.transforms[0].matrix

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

							sections = 3
							status, doTweakers = mnsUtils.validateAttrAndGet(rootGuide, "doTweakers", False)
							if doTweakers:
								status, tweakersPerSection = mnsUtils.validateAttrAndGet(rootGuide, "tweakersPerSection", 1)
								sections = (tweakersPerSection * 3) + 3
						
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