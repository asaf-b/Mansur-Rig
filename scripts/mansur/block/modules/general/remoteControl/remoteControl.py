"""Author: Asaf Ben-Zur
Best used for: Blend Shape Targets, Facial-Remotes, General Extra-Setups
This moudle, upon construction, will create a remote-control style control.
It will create a frame, with a control within, limited to that frame.
The frame range is dictated by the settings below.
Use the min-max values for both vertical and horizontal directions to create the remote that best fitting to your needs.
You can freely use both vertical and horizontal directions in combination.
This type of control is often seen when creating a blend-shape-based facial rig, with an adjacent remote control to easily and visually animate the targets instead of using the channel box directly.

Also, you can control the target value range for your control.
That means that the control and target ranges can differ.
For example, a blend shape target with values between 0 and 1 is needed to be controlled.
You can set the control range between 0 and 5, while keeping the target range between 0 and 1, which will result in a slower behaving control for more fidelity.

The target connection is handled post-construction so connecting to constructed objects is also possible.
Multiple targets can be input into the same target. Simply select multiple targets and input. Alternatively manually input the targets, separated by commas.

Module build assumptions/requisites:
- targetMin < targetMax
- rangeMin < rangeMax
- A target can be shared within a direction minimum and maximum
- Output ranges between 0.0 and TargetMax given 0.0 and range Max
- Output ranges between 0.0 and TargetMin given 0.0 and range Min
- AKA the module assumes 0.0 as a default value for both input range and target range
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
	attrHost = animGrp

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule) * 0.3

	########### Get settings ######################
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	status, controlScale = mnsUtils.validateAttrAndGet(rootGuide, "controlScale", 1.0)
	controlScale *= modScale
	status, textScale = mnsUtils.validateAttrAndGet(rootGuide, "textScale", 1.0)
	textScale *= controlScale

	status, verticalMinimum = mnsUtils.validateAttrAndGet(rootGuide, "verticalMinimum", 0.0)
	status, verticalMaximum = mnsUtils.validateAttrAndGet(rootGuide, "verticalMaximum", 1.0)
	status, verticalDefault = mnsUtils.validateAttrAndGet(rootGuide, "verticalDefault", 0.0)
	status, horizontalMinimum = mnsUtils.validateAttrAndGet(rootGuide, "horizontalMinimum", 0.0)
	status, horizontalMaximum = mnsUtils.validateAttrAndGet(rootGuide, "horizontalMaximum", 0.0)
	status, horizontalDefault = mnsUtils.validateAttrAndGet(rootGuide, "horizontalDefault", 0.0)

	status, verticalTargetMinimum = mnsUtils.validateAttrAndGet(rootGuide, "verticalTargetMinimum", 0.0)
	status, verticalTargetMaximum = mnsUtils.validateAttrAndGet(rootGuide, "verticalTargetMaximum", 1.0)
	status, horizontalTargetMinimum = mnsUtils.validateAttrAndGet(rootGuide, "horizontalTargetMinimum", 0.0)
	status, horizontalTargetMaximumm = mnsUtils.validateAttrAndGet(rootGuide, "horizontalTargetMaximumm", 0.0)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	ctrl, ctrlOffsetGrp, ctrlFrame = blkCtrlShps.createRemoteControlStyleCtrl(nameReference = rootGuide,
																					side = rootGuide.side,
																					verticalMin = verticalMinimum, 
																					verticalMax = verticalMaximum, 
																					horizontalMin = horizontalMinimum, 
																					horizontalMax = horizontalMaximum,
																					uiScale = controlScale,
																					isFacial = MnsBuildModule.isFacial)
	mnsUtils.setAttr(ctrl.node.tz, verticalDefault)
	mnsUtils.setAttr(ctrl.node.tx, horizontalDefault)

	pm.parent(ctrlOffsetGrp.node, animGrp.node)
	for axis in "xyz": ctrlOffsetGrp.node.setAttr("t" + axis, 0.0)
	ctrlsCollect.append(ctrl)

	lblCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
							color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
							matchPosition = ctrl,
							controlShape = "txtCtrlShp_" + MnsBuildModule.rootGuide.body,
							bodySuffix = "Label",
							scale = textScale, 
							parentNode = animGrp,
							symmetryType = symmetryType,
							doMirror = True,
							alongAxis = 2,
							creatgearMasterSwitchGroup = False,
							createOffsetGrp = False,
							chennelControl = {'t': [False, False, False], 'r': [False, False, False], 's': [False, False, False]},
							isFacial = MnsBuildModule.isFacial)
	ctrlsCollect.append(lblCtrl)

	#position label
	remoteCtrlWorldBB = pm.exactWorldBoundingBox(ctrlOffsetGrp.node)
	bottomCenterPos = [((remoteCtrlWorldBB[0] +  remoteCtrlWorldBB[3]) / 2), remoteCtrlWorldBB[1], remoteCtrlWorldBB[2]]

	lblWorldBB = pm.exactWorldBoundingBox(lblCtrl.node)
	topCenterPos = [((lblWorldBB[0] +  lblWorldBB[3]) / 2), lblWorldBB[4], lblWorldBB[5]]
	offsetY = bottomCenterPos[1] - topCenterPos[1]
	offsetX = bottomCenterPos[0] - topCenterPos[0]
	mnsUtils.setAttr(lblCtrl.node.ty, offsetY + lblCtrl.node.ty.get())
	mnsUtils.setAttr(lblCtrl.node.tx, offsetX + lblCtrl.node.tx.get())

	attr = mnsUtils.addAttrToObj([ctrl.node], type = "message", name = "guideAuthority", value= rootGuide.node, replace = True)[0]
	attr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "ctrlAuthority", value= ctrl.node, replace = True)[0]

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, attrHost, attrHost

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core.prefixSuffix import GLOB_mnsJntStructDefaultSuffix

	rootGuide = guides[0]
	relatedRootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(rootGuide))
	createJoint = False

	parentJnt = blkUtils.recGetParentJoint(rootGuide.node.getParent())
	if relatedRootJnt and not createJoint:
		jntChildren = relatedRootJnt.node.listRelatives(c = True, type = "joint")
		if jntChildren: pm.parent(jntChildren, relatedRootJnt.node.getParent())
		pm.delete(relatedRootJnt.node)
		relatedRootJnt = None



def postConstruct(mansur, MnsBuildModule, **kwargs):
	def validateTargetAttributes(targets):
		validatedTargtes = []
		for tString in targets:
			if "." in tString:
				targetNode = mnsUtils.checkIfObjExistsAndSet(tString.split(".")[0])
				if targetNode:
					status, targetAttr = mnsUtils.validateAttrAndGet(targetNode, tString.split(".")[1], None, returnAttrObject = True)
					if status:
						validatedTargtes.append(targetAttr)
		return validatedTargtes
	

	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core import string as mnsString

	if MnsBuildModule.rootGuide:
		rootGuide = MnsBuildModule.rootGuide
		status, ctrlAuthority = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
		if ctrlAuthority: 
			status, upTraget = mnsUtils.validateAttrAndGet(rootGuide, "upTraget", "")
			status, downTraget = mnsUtils.validateAttrAndGet(rootGuide, "downTraget", "")
			status, leftTraget = mnsUtils.validateAttrAndGet(rootGuide, "leftTraget", "")
			status, rightTraget = mnsUtils.validateAttrAndGet(rootGuide, "rightTraget", "")
			status, verticalMinimum = mnsUtils.validateAttrAndGet(rootGuide, "verticalMinimum", 0.0)
			status, verticalMaximum = mnsUtils.validateAttrAndGet(rootGuide, "verticalMaximum", 1.0)
			status, horizontalMinimum = mnsUtils.validateAttrAndGet(rootGuide, "horizontalMinimum", 0.0)
			status, horizontalMaximum = mnsUtils.validateAttrAndGet(rootGuide, "horizontalMaximum", 0.0)
			status, verticalTargetMinimum = mnsUtils.validateAttrAndGet(rootGuide, "verticalTargetMinimum", 0.0)
			status, verticalTargetMaximum = mnsUtils.validateAttrAndGet(rootGuide, "verticalTargetMaximum", 1.0)
			status, horizontalTargetMinimum = mnsUtils.validateAttrAndGet(rootGuide, "horizontalTargetMinimum", 0.0)
			status, horizontalTargetMaximumm = mnsUtils.validateAttrAndGet(rootGuide, "horizontalTargetMaximumm", 0.0)

			for direction in "vh":
				posTraget = upTraget
				negTraget = downTraget
				if direction == "h":
					posTraget = rightTraget
					negTraget = leftTraget

				posTargets, negTargets = [], []
				for target in [posTraget, negTraget]:
					if target:
						validatedTargets = validateTargetAttributes(mnsString.splitStringToArray(target))
						if validatedTargets:
							if target is posTraget:
								posTargets = validatedTargets
							else:
								negTargets = validatedTargets
				
				if posTargets or negTargets:
					#targets acquired, move to creating the driver
					targetMin = verticalTargetMinimum
					targetMax = verticalTargetMaximum
					inMin = verticalMinimum
					inMax = verticalMaximum
					ctrlAttr = ctrlAuthority.tz

					if direction == "h":
						targetMin = horizontalTargetMinimum
						targetMax = horizontalTargetMaximumm
						inMin = horizontalMinimum
						inMax = horizontalMaximum
						ctrlAttr = ctrlAuthority.tx

					posSetRange = mnsNodes.setRangeNode(maxIn = [targetMax,0.0,0.0], 
													minIn = [0.0,0.0,0.0], 
													oldMax = [inMax, 0.0, 0.0], 
													oldMin = [0.0, 0.0,0.0], 
													value = [ctrlAttr, None,None], 
													outValue = [None,None,None],
													side = rootGuide.side, 
													body = rootGuide.body, 
													alpha = rootGuide.alpha, 
													id = rootGuide.id)
					blkUtils.connectSlaveToDeleteMaster(posSetRange, ctrlAuthority)

					negSetRange = mnsNodes.setRangeNode(maxIn = [0.0,0.0,0.0], 
													minIn = [targetMin,0.0,0.0], 
													oldMax = [0.0, 0.0, 0.0], 
													oldMin = [inMin, 0.0,0.0], 
													value = [ctrlAttr, None,None], 
													outValue = [None,None,None],
													side = rootGuide.side, 
													body = rootGuide.body, 
													alpha = rootGuide.alpha, 
													id = rootGuide.id)
					blkUtils.connectSlaveToDeleteMaster(negSetRange, ctrlAuthority)

					
					conNode = mnsNodes.conditionNode(ctrlAttr, 0.0, [posSetRange.node.outValue.outValueX,0,0], [negSetRange.node.outValue.outValueX,0,0], operation = 2)
					blkUtils.connectSlaveToDeleteMaster(conNode, ctrlAuthority)

					sharedTargets = [t for t in posTargets if t in negTargets]
					
					posClampNode, negClampNode = None, None
					for target in (posTargets + negTargets):
						if target in sharedTargets:
							conNode.node.outColor.outColorR >> target
						else:
							if target in posTargets:
								if not posClampNode:
									posClampNode = mnsNodes.clampNode([conNode.node.outColor.outColorR, 0, 0], 
													[targetMax, 0, 0],
													[0.0, 0.0, 0.0],
													[None, None, None])
								posClampNode.node.outputR >> target
								blkUtils.connectSlaveToDeleteMaster(posClampNode, ctrlAuthority)
							else:
								if not negClampNode:
									negClampNode = mnsNodes.clampNode([conNode.node.outColor.outColorR, 0, 0], 
													[0.0, 0.0, 0.0],
													[targetMin, 0.0, 0.0],
													[None, None, None])
									blkUtils.connectSlaveToDeleteMaster(negClampNode, ctrlAuthority)
								negClampNode.node.outputR >> target
