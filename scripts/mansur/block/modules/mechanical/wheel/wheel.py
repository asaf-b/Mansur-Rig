"""Author: Asaf Ben-Zur
Best used for: Wheels
A simple module to create an auto-drive for wheels.
This module will calculate the rotation of a wheel based on the input settings, using the module's world position.
This will yield an auto-drive for wheels.
The behaviour will not be confined to a single control being moved, but rather to the modules world position.
This will apply to translation, as well as rotation, in all directions.
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
	if MnsBuildModule.cGuideControls: 
		for cGuide in customGuides:
			if "ForwardDirection_" in cGuide.node.nodeName():
				forwardDirCusGuide = cGuide
				break

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("channelControl", MnsBuildModule.rootGuide.node)
	status, controlShape = mnsUtils.validateAttrAndGet(rootGuide, "controlShape", "square")
	status, channelControl = mnsUtils.validateAttrAndGet(rootGuide, "channelControl", 0)
	if status: channelControl = mnsUtils.splitEnumAttrToChannelControlList("channelControl", rootGuide.node)

	ctrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = controlShape,
								scale = modScale, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial,
								alongAxis = 0)

	directionLoc = mnsUtils.createNodeReturnNameStd(parentNode = ctrl.node.getParent(), side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "Dir", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.delete(pm.parentConstraint(forwardDirCusGuide.node, directionLoc.node))
	directionLoc.node.v.set(False)

	status, wheelDiameter = mnsUtils.validateAttrAndGet(rootGuide, "wheelDiameter", 10.0)
	status, autoDriveDefault = mnsUtils.validateAttrAndGet(rootGuide, "autoDriveDefault", True)
	adwNode = mnsNodes.mnsAutoWheelDriveNode(side =rootGuide.side, 
											body = rootGuide.body, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id,
											wheelDiameter = wheelDiameter,
											driverWorldMatrix = ctrl.node.getParent().worldMatrix[0],
											startDirectionWorldMatrix = directionLoc.node.worldMatrix[0])
	wheelModGrp = mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp")
	blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> adwNode.node.globalScale

	#connect out rotation
	status, mapRoatationToAxis = mnsUtils.validateAttrAndGet(rootGuide, "mapRoatationToAxis", 0)
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
	host = MnsBuildModule.attrHostCtrl or ctrl
	mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "AutoDrive", replace = True, locked = True)
	speedMulAttr = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "speedMultiplier", replace = True)[0]
	speedMulAttr >> adwNode.node.speedMultiplier
	gearRatioAttr = mnsUtils.addAttrToObj([host], type = "float", value = gearRatio, name = "gearRatio", replace = True)[0]
	gearRatioAttr >> mdlNode.node.input2
	startFrameAttr = mnsUtils.addAttrToObj([host], type = "int", value = 1, name = "startFrame", replace = True, keyable = False, cb = True)[0]
	startFrameAttr >> adwNode.node.startFrame
	startFrameFromRangeAttr = mnsUtils.addAttrToObj([host], type = "bool", value = True, name = "startFrameFromRange", replace = True, keyable = False, cb = True)[0]
	startFrameFromRangeAttr >> adwNode.node.startFrameFromRange						

	ctrlsCollect.append(ctrl)
	blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, ctrl, host

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

		handlePos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "ForwardDirection", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		
		pm.parent(handlePos.node, builtGuides[0].node)
		pm.makeIdentity(handlePos.node)
		handlePos.node.ty.set(10)
		pm.parent(handlePos.node, w = True)

		parentDict.update({handlePos: builtGuides[0]})
		custGuides.append(handlePos)

	return custGuides, parentDict