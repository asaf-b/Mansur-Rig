"""Author: Asaf Ben-Zur
Best used for: Balls, BB-8-Style
A simple module to drive a sphere roll based on position.
Upon contruction, based on the given settings, the main joint orientation will be driven by the module's position.
This module will calculate the roll of the sphere needed to reach the target position, without slipping, in any direction.
This behaviour is not confined to a single control being moved, but rather calculated based on the module's world-position.
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

	forwardDirCusGuide = None
	groundPosCusGuide = None
	if MnsBuildModule.cGuideControls: 
		for cGuide in customGuides:
			if "UpDirection_" in cGuide.node.nodeName():
				forwardDirCusGuide = cGuide
			if "GroundPos_" in cGuide.node.nodeName():
				groundPosCusGuide = cGuide

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	status, controlShape = mnsUtils.validateAttrAndGet(rootGuide, "controlShape", "lightSphere")
	status, channelControl = mnsUtils.validateAttrAndGet(rootGuide, "channelControl", 0)
	if status: channelControlList = mnsUtils.splitEnumAttrToChannelControlList("channelControl", rootGuide.node)
	status, sphereRadius = mnsUtils.validateAttrAndGet(rootGuide, "sphereRadius", 10.0)

	slaveCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = controlShape,
								scale = sphereRadius * 1.1, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial,
								alongAxis = 0)
	ctrlsCollect.append(slaveCtrl)
	slaveOffsetGrp = blkUtils.getOffsetGrpForCtrl(slaveCtrl)

	directionLoc = mnsUtils.createNodeReturnNameStd(parentNode = slaveOffsetGrp.node.getParent(), side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "Dir", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(forwardDirCusGuide.node, directionLoc.node))
	directionLoc.node.v.set(False)

	status, autoRollDefault = mnsUtils.validateAttrAndGet(rootGuide, "autoRollDefault", True)


	sprNode = mnsNodes.mnsSphereRollNode(side =rootGuide.side, 
											body = rootGuide.body, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id,
											sphereRadius = sphereRadius,
											driverWorldMatrix = slaveOffsetGrp.node.worldMatrix[0],
											upVectorWorldMatrix = directionLoc.node.worldMatrix[0],
											outRotation = slaveOffsetGrp.node.r)
	
	blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> sprNode.node.globalScale


	#create drive attributes
	host = MnsBuildModule.attrHostCtrl or slaveCtrl
	mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "AutoRoll", replace = True, locked = True)
	speedMulAttr = mnsUtils.addAttrToObj([host], type = "float", value = autoRollDefault, name = "speedMultiplier", replace = True)[0]
	speedMulAttr >> sprNode.node.speedMultiplier
	startFrameAttr = mnsUtils.addAttrToObj([host], type = "int", value = 1, name = "startFrame", replace = True, keyable = False, cb = True)[0]
	startFrameAttr >> sprNode.node.startFrame
	startFrameFromRangeAttr = mnsUtils.addAttrToObj([host], type = "bool", value = True, name = "startFrameFromRange", replace = True, keyable = False, cb = True)[0]
	startFrameFromRangeAttr >> sprNode.node.startFrameFromRange						

	blkUtils.transferAuthorityToCtrl(relatedJnt, slaveCtrl)

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, slaveCtrl, host

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

		handlePos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "UpDirection", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		
		pm.parent(handlePos.node, builtGuides[0].node)
		pm.makeIdentity(handlePos.node)
		handlePos.node.ty.set(10)
		pm.parent(handlePos.node, w = True)

		parentDict.update({handlePos: builtGuides[0]})
		custGuides.append(handlePos)

	return custGuides, parentDict