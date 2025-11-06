"""Author: Asaf Ben-Zur
Best used for: Head Squash, Nose, any general squash behaviour
This module will create a squash behaviour to it's slave joint.
Any child modules under this module will inherit the squash behaviour.
The squash behaviour can be set by the module's settings, and can also be adjusted and keyed post construction. 
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
	rigComponentsGrp = MnsBuildModule.rigComponentsGrp
	attrHost = MnsBuildModule.attrHostCtrl or animGrp
	customGuides = MnsBuildModule.cGuideControls

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	handlePosCGuide = None
	if MnsBuildModule.cGuideControls: 
		for cGuide in customGuides:
			if "HandlePos_" in cGuide.node.nodeName():
				handlePosCGuide = cGuide
				break

	#create root locs
	rootLoc = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RootPosition", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(animGrp.node, rootLoc.node))
	pm.parent(rootLoc.node, animGrp.node)
	rootLoc.node.v.set(False)
	rootLoc.node.v.setLocked(True)
	mnsUtils.lockAndHideAllTransforms(rootLoc.node, lock = True)


	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("channelControl", MnsBuildModule.rootGuide.node)
	modScale = MnsBuildModule.rigTop.node.assetScale.get() * MnsBuildModule.rootGuide.node.controlsMultiplier.get() * mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]
	handleControl = blkCtrlShps.ctrlCreate(
								controlShape = MnsBuildModule.rootGuide.node.controlShape.get(),
								createBlkClassID = True, 
								createBlkCtrlTypeID = True, 
								blkCtrlTypeID = 0, 
								scale = modScale, 
								alongAxis = 1, 
								side = MnsBuildModule.rootGuide.side, 
								body = MnsBuildModule.rootGuide.body + "Handle", 
								alpha = MnsBuildModule.rootGuide.alpha, 
								id = MnsBuildModule.rootGuide.id,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = handlePosCGuide.node,
								parentNode = animGrp,
								createSpaceSwitchGroup = True,
								createOffsetGrp = True,
								symmetryType = symmetryType,
								isFacial = MnsBuildModule.isFacial,
								doMirror = True
								)
	ctrlsCollect.append(handleControl)
	mnsUtils.applyChennelControlAttributesToTransform(handleControl.node, channelControlList)

	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("slaveChannelControl", MnsBuildModule.rootGuide.node)
	status, slaveControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "slaveControlShape", "lightSpehere")
	jntCtrl = blkCtrlShps.ctrlCreate(
								controlShape = slaveControlShape,
								createBlkClassID = True, 
								createBlkCtrlTypeID = True, 
								blkCtrlTypeID = 1, 
								scale = modScale * 0.8, 
								alongAxis = 1, 
								side = MnsBuildModule.rootGuide.side, 
								body = MnsBuildModule.rootGuide.body + "Slave", 
								alpha = MnsBuildModule.rootGuide.alpha, 
								id = MnsBuildModule.rootGuide.id,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								parentNode = animGrp,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								symmetryType = symmetryType,
								isFacial = MnsBuildModule.isFacial,
								doMirror = True
								)
	ctrlsCollect.append(jntCtrl)
	mnsUtils.applyChennelControlAttributesToTransform(jntCtrl.node, channelControlList)
	jntCtrlModGrp = mnsUtils.createOffsetGroup(jntCtrl, type = "modifyGrp")

	#get settings
	status, squashFactor = mnsUtils.validateAttrAndGet(rootGuide, "squashFactor", 1.0)
	status, squashMin = mnsUtils.validateAttrAndGet(rootGuide, "squashMin", 0.001)
	status, squashMax = mnsUtils.validateAttrAndGet(rootGuide, "squashMax", 10.0)

	status, stretchFactor = mnsUtils.validateAttrAndGet(rootGuide, "stretchFactor", 1.0)
	status, stretchMin = mnsUtils.validateAttrAndGet(rootGuide, "stretchMin", 0.001)
	status, stretchMax = mnsUtils.validateAttrAndGet(rootGuide, "stretchMax", 10.0)

	#create simpleSuqash node
	squashNode = mnsNodes.mnsSimpleSquashNode(side =rootGuide.side, 
								body = rootGuide.body, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id,
								squashFactor = squashFactor,
								squashMin = squashMin,
								squashMax = squashMax,
								stretchFactor = stretchFactor,
								stretchMin = stretchMin,
								stretchMax = stretchMax,
								squashRootWorldMatrix  = rootLoc.node.worldMatrix[0],
								handleWorldMatrix = handleControl.node.worldMatrix[0],
								scale = jntCtrlModGrp.node.s
								)
	#connect globScale
	blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> squashNode.node.globalScale

	###aimConstraint
	#create up node
	upLoc = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "UpVector", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(animGrp.node, upLoc.node))
	pm.parent(upLoc.node, animGrp.node)
	
	status, upLocalDirection = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "upLocalDirection", 0)
	if upLocalDirection == 0: upLoc.node.tx.set(10)
	elif upLocalDirection == 1: upLoc.node.ty.set(10)
	elif upLocalDirection == 2: upLoc.node.tz.set(10)
	elif upLocalDirection == 3: upLoc.node.tx.set(-10)
	elif upLocalDirection == 4: upLoc.node.ty.set(-10)
	elif upLocalDirection == 5: upLoc.node.tz.set(-10)

	upLoc.node.v.set(False)
	upLoc.node.v.setLocked(True)
	mnsUtils.lockAndHideAllTransforms(upLoc.node, lock = True)
	aimConst = mnsNodes.mayaConstraint([handleControl.node], [jntCtrlModGrp.node],
								side =rootGuide.side, 
								body = rootGuide.body, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id,
								type = "aim",
								worldUpObject = upLoc.node
								)

	#addAttrs
	host = handleControl.node
	mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "squashSettings", replace = True, locked = True)
	
	#squashFactor
	squashFactorAttr = mnsUtils.addAttrToObj([host], type = "float", value = squashFactor, name = "squashFactor", replace = True, min = 0.001)[0]
	squashFactorAttr >> squashNode.node.squashFactor

	#squashMin
	squashMinAttr = mnsUtils.addAttrToObj([host], type = "float", value = squashMin, name = "squashMin", replace = True, min = 0.001, max = 1.0)[0]
	squashMinAttr >> squashNode.node.squashMin

	#squashMin
	squashMaxAttr = mnsUtils.addAttrToObj([host], type = "float", value = squashMax, name = "squashMax", replace = True, min = 0.001)[0]
	squashMaxAttr >> squashNode.node.squashMax

	#stretchFactor
	stretchFactorAttr = mnsUtils.addAttrToObj([host], type = "float", value = squashFactor, name = "stretchFactor", replace = True, min = 0.001)[0]
	stretchFactorAttr >> squashNode.node.stretchFactor

	#stretchMin
	stretchMinAttr = mnsUtils.addAttrToObj([host], type = "float", value = squashMin, name = "stretchMin", replace = True, min = 0.001, max = 1.0)[0]
	stretchMinAttr >> squashNode.node.stretchMin

	#stretchMax
	stretchMaxAttr = mnsUtils.addAttrToObj([host], type = "float", value = squashMax, name = "stretchMax", replace = True, min = 0.001)[0]
	stretchMaxAttr >> squashNode.node.stretchMax


	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(MnsBuildModule.rootGuide))
	blkUtils.transferAuthorityToCtrl(relatedJnt, jntCtrl)

	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, None, handleControl

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

		handlePos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "HandlePos", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		
		pm.parent(handlePos.node, builtGuides[0].node)
		pm.makeIdentity(handlePos.node)
		handlePos.node.ty.set(10)
		pm.parent(handlePos.node, w = True)

		parentDict.update({handlePos: builtGuides[0]})
		custGuides.append(handlePos)

	return custGuides, parentDict