"""Author: Asaf Ben-Zur
Best used for: Hydraulic Piston, Mechanical Springs
A simple module to create a piston style control.
Combining aim and translation constraints, this module will create a piston like behaviour, keeping the main orientation of the module towards the aim control, while stretching an inner piston along its axis regadless of the module orientation, keeping the piston within its outer tube.
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

	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("channelControl", MnsBuildModule.rootGuide.node)
	modScale = MnsBuildModule.rigTop.node.assetScale.get() * MnsBuildModule.rootGuide.node.controlsMultiplier.get() * mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]
	status, slaveControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "slaveControlShape", "lightSphere")
	status, targetControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "targetControlShape", "circle")

	ctrl = blkCtrlShps.ctrlCreate(
								controlShape = slaveControlShape,
								createBlkClassID = True, 
								createBlkCtrlTypeID = True, 
								blkCtrlTypeID = 1, 
								scale = modScale * 0.7, 
								alongAxis = 1, 
								side = MnsBuildModule.rootGuide.side, 
								body = MnsBuildModule.rootGuide.body, 
								alpha = MnsBuildModule.rootGuide.alpha, 
								id = MnsBuildModule.rootGuide.id,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								parentNode = animGrp,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								symmetryType = symmetryType,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial
								)
	ctrlsCollect.append(ctrl)

	lookAtCtrl = blkCtrlShps.ctrlCreate(
							controlShape = targetControlShape,
							createBlkClassID = True, 
							createBlkCtrlTypeID = True, 
							blkCtrlTypeID = 0, 
							scale = modScale, 
							alongAxis = 2, 
							side = MnsBuildModule.rootGuide.side, 
							body = MnsBuildModule.rootGuide.body + "LookAt", 
							alpha = MnsBuildModule.rootGuide.alpha, 
							id = MnsBuildModule.rootGuide.id,
							color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
							matchTransform = allGuides[1].node,
							createSpaceSwitchGroup = True,
							createOffsetGrp = True,
							symmetryType = symmetryType,
							parentNode = animGrp,
							chennelControl = channelControlList,
							isFacial = MnsBuildModule.isFacial
							)
	ctrlsCollect.append(lookAtCtrl)
	mnsUtils.lockAndHideTransforms(lookAtCtrl.node, lock = True, tx = False, ty = False, tz = False, rx = False, ry = False, rz = False)
	attrHost = lookAtCtrl

	upNodeStd = mnsUtils.createNodeReturnNameStd(parentNode = animGrp.node, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "UpNode", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.makeIdentity(upNodeStd.node)
	
	pitonArmCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = "PistonArmArm",
											ctrlType = "techCtrl", 
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = allGuides[1].node,
											controlShape = slaveControlShape,
											scale = modScale, 
											parentNode = ctrl,
											symmetryType = symmetryType,
											doMirror = True,
											createSpaceSwitchGroup = False,
											createOffsetGrp = True,
											isFacial = MnsBuildModule.isFacial)
	pitonArmCtrl.node.v.set(False)
	pntCont = mnsNodes.mayaConstraint([lookAtCtrl.node], pitonArmCtrl.node, type = "point", maintainOffset = False, skip = ["x", "z"])

	status, upLocalDirection = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "upLocalDirection", 1)
	if upLocalDirection == 0: upNodeStd.node.tx.set(10)
	elif upLocalDirection == 1: upNodeStd.node.ty.set(10)
	elif upLocalDirection == 2: upNodeStd.node.tz.set(10)
	elif upLocalDirection == 3: upNodeStd.node.tx.set(-10)
	elif upLocalDirection == 4: upNodeStd.node.ty.set(-10)
	elif upLocalDirection == 5: upNodeStd.node.tz.set(-10)
	
	upNodeStd.node.v.set(False)
	upNodeStd.node.v.setLocked(True)
	aimCns = mnsNodes.mayaConstraint(lookAtCtrl.node, mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp").node, worldUpObject = upNodeStd.node,type = "aim")

	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(MnsBuildModule.rootGuide))
	blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)

	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(allGuides[1]))
	blkUtils.transferAuthorityToCtrl(relatedJnt, pitonArmCtrl)

	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, None, attrHost