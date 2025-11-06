"""Author: Asaf Ben-Zur
Best used for: Eyes, Generic Orientation based components
This module was written to function as an eye IK (look at setup), but can be used for many other generic components.
This module will create a slave control (at root position) which is aim-constraint to custom look-at guide.
The slave control will be the control authority for the joint, as the look-at control will control its orientation.
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
	lookAtPos = None
	if customGuides: 
		for cGuide in customGuides:
			if "LookAtControlPos_" in cGuide.node.nodeName():
				lookAtPos = cGuide
				break

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
	slaveCtrlAttr = mnsUtils.addAttrToObj([ctrl.node], type = "message", name = "lookAtCtrl", value= "", replace = True)[0]

	if lookAtPos:
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
								matchTransform = lookAtPos.node,
								createSpaceSwitchGroup = True,
								createOffsetGrp = True,
								symmetryType = symmetryType,
								parentNode = animGrp,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial
								)
		ctrlsCollect.append(lookAtCtrl)
		lookAtCtrl.node.message >> slaveCtrlAttr
		mnsUtils.lockAndHideTransforms(lookAtCtrl.node, lock = True, tx = False, ty = False, tz = False, rx = False, ry = False, rz = False)
		attrHost = lookAtCtrl

		upNodeStd = mnsUtils.createNodeReturnNameStd(parentNode = animGrp.node, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "UpNode", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.makeIdentity(upNodeStd.node)
		
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

		#spring
		status, doLookAtSpring = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doLookAtSpring", False)
		if doLookAtSpring:
			status, defaultStiffness = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "defaultStiffness", 0.5)
			status, defaultDamping = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "defaultDamping", 0.5)

			lookAtOffsetGrp = blkUtils.getOffsetGrpForCtrl(lookAtCtrl)
			springLoc = mnsUtils.createNodeReturnNameStd(parentNode = lookAtOffsetGrp.node, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "Spring", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
			pm.makeIdentity(springLoc.node)
			springLoc.node.v.set(False)

			#create the target offset grp
			lookAtModGrp = mnsUtils.createOffsetGroup(lookAtCtrl, type = "modifyGrp")

			tsNode = mnsNodes.mnsTransformSpringNode(side =rootGuide.side, 
										body = rootGuide.body, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id,
										inputWorldMatrix = springLoc.node.worldMatrix[0],
										targetParentInverseMatrix = lookAtModGrp.node.parentInverseMatrix[0],
										outTranslate = lookAtModGrp.node.t,
										damaping = defaultStiffness,
										stiffness = defaultDamping)

			tsNode = tsNode.node

			#attributes
			host = MnsBuildModule.attrHostCtrl or lookAtCtrl
			mnsUtils.addAttrToObj([host.node], type = "enum", value = ["______"], name = "springSettings", replace = True, locked = True)
			strengthAttr = mnsUtils.addAttrToObj([host.node], type = "float", min = 0.0, max = 1.0, value = 1.0, name = "strength", replace = True)[0]
			strengthAttr >> tsNode.strength
			stiffnessAttr = mnsUtils.addAttrToObj([host.node], type = "float", min = 0.0, max = 1.0, value = defaultStiffness, name = "stiffness", replace = True)[0]
			stiffnessAttr >> tsNode.stiffness
			dampingAttr = mnsUtils.addAttrToObj([host.node], type = "float", min = 0.0, max = 1.0, value = defaultDamping, name = "damping", replace = True)[0]
			dampingAttr >> tsNode.damping

			startFrameAttr = mnsUtils.addAttrToObj([host.node], type = "int", value = 1, name = "startFrame", replace = True, keyable = False, cb = True, locked = False)[0]
			startFrameAttr >> tsNode.startFrame

			startFrameFromRangeAttr = mnsUtils.addAttrToObj([host.node], type = "bool", value = True, name = "startFrameFromRange", replace = True, keyable = False, cb = True, locked = False)[0]
			startFrameFromRangeAttr >> tsNode.startFrameFromRange										

	status, pupilDilateAttribute = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "pupilDilateAttribute", None)
	status, pupilContractAttribute = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "pupilContractAttribute", None)
	status, irisDilateAttribute = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "irisDilateAttribute", None)
	status, irisContractAttribute = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "irisContractAttribute", None)

	#eye shapes
	if pupilDilateAttribute or pupilContractAttribute or irisDilateAttribute or irisContractAttribute:
		mnsUtils.addAttrToObj([attrHost.node], type = "enum", value = ["______"], name = "eyeShapes", replace = True, locked = True)
		
		pupilContractMaster = mnsUtils.addAttrToObj([attrHost.node], type = "float", min = -1.0, max = 1.0, value = 0.0, name = "pupil", replace = True)[0]
		irisContractMaster = mnsUtils.addAttrToObj([attrHost.node], type = "float", min = -1.0, max = 1.0, value = 0.0, name = "iris", replace = True)[0]

		mdNode = mnsNodes.mdNode([pupilContractMaster, irisContractMaster, 0.0],
									[-1.0, -1.0, -1.0],
									None)

		clampNodeA = mnsNodes.clampNode([pupilContractMaster, mdNode.node.outputX, 0], 
									[1.0, 1.0, 1.0],
									[0.0, 0.0, 0.0],
									[pupilDilateAttribute, pupilContractAttribute, None])

		blkUtils.connectSlaveToDeleteMaster(clampNodeA, animGrp)

		clampNodeB = mnsNodes.clampNode([irisContractMaster, mdNode.node.outputY, 0], 
									[1.0, 1.0, 1.0],
									[0.0, 0.0, 0.0],
									[irisDilateAttribute, irisContractAttribute, None])

		blkUtils.connectSlaveToDeleteMaster(clampNodeB, animGrp)

		mnsNodes.connectAttrAttempt(clampNodeA.node.attr("outputR"), pupilDilateAttribute)
		mnsNodes.connectAttrAttempt(clampNodeA.node.attr("outputG"), pupilContractAttribute)
		mnsNodes.connectAttrAttempt(clampNodeB.node.attr("outputR"), irisDilateAttribute)
		mnsNodes.connectAttrAttempt(clampNodeB.node.attr("outputG"), irisContractAttribute)

		status, combinedAttributeHost = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "combinedAttributeHost", None)
		combinedAttributeHost = mnsUtils.validateNameStd(combinedAttributeHost)
		if combinedAttributeHost:
			combinedAttributeHost = blkUtils.getCtrlAuthFromRootGuide(combinedAttributeHost)
			if combinedAttributeHost:
				pupilContractMasterHost, irisContractMasterHost = None, None
				if not combinedAttributeHost.node.hasAttr("eyeShapes"):
					mnsUtils.addAttrToObj([combinedAttributeHost.node], type = "enum", value = ["______"], name = "eyeShapes", replace = True, locked = True)
					pupilContractMasterHost = mnsUtils.addAttrToObj([combinedAttributeHost.node], type = "float", min = -1.0, max = 1.0, value = 0.0, name = "pupil", replace = False)[0]
					irisContractMasterHost = mnsUtils.addAttrToObj([combinedAttributeHost.node], type = "float", min = -1.0, max = 1.0, value = 0.0, name = "iris", replace = False)[0]
				else:
					try:
						pupilContractMasterHost = combinedAttributeHost.node.pupil
						irisContractMasterHost = combinedAttributeHost.node.iris
					except: pass

				if pupilContractMasterHost: 
					pupilContractMasterHost >> pupilContractMaster
					pupilContractMaster.setKeyable(False)
				if irisContractMasterHost: 
					irisContractMasterHost >> irisContractMaster
					irisContractMaster.setKeyable(False)

	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(MnsBuildModule.rootGuide))
	blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)

	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, None, lookAtCtrl

def customGuides(mansur, builtGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils

	custGuides = []
	parentDict = {}

	if builtGuides:
		nameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "LookAtControlPos", alpha = builtGuides[0].alpha, id = builtGuides[0].id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(builtGuides[0].node, nameStd.node))
		custGuides.append(nameStd)
		parentDict.update({nameStd: builtGuides[0]})

	return custGuides, parentDict


def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	if MnsBuildModule.rootGuide:
		status, ctrlAuthority = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ctrlAuthority", None)
		if ctrlAuthority: 
			status, doInterpOrient = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doInterpOrient", False)
			if doInterpOrient:
				slaveCtrl = mnsUtils.validateNameStd(ctrlAuthority)
				if slaveCtrl:
					status, lookAtCtrl = mnsUtils.validateAttrAndGet(ctrlAuthority, "lookAtCtrl", None)
					lookAtCtrl = mnsUtils.validateNameStd(lookAtCtrl)

					if lookAtCtrl:
						spaceA = mnsUtils.checkIfObjExistsAndSet(mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "spaceA", None)[1])
						spaceB = mnsUtils.checkIfObjExistsAndSet(mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "spaceB", None)[1])
						spaceA = blkUtils.convertInputObjToSpace(spaceA)
						spaceB = blkUtils.convertInputObjToSpace(spaceB)

						if spaceA and spaceB and not spaceA is spaceB:
							status, spaceAWeight = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "spaceAWeight", 0.5)
							spaceBWeight = 1.0 - spaceAWeight;

							lookAtOffsetGrp = blkUtils.getOffsetGrpForCtrl(lookAtCtrl)
							interpOrientGrp = mnsUtils.createNodeReturnNameStd(parentNode = lookAtOffsetGrp.node.getParent(), 
															side =  lookAtCtrl.side, 
															body = lookAtCtrl.body, 
															alpha = lookAtCtrl.alpha, 
															id =  lookAtCtrl.id, 
															buildType = "modifyGrp", 
															incrementAlpha = False)

							pm.delete(pm.parentConstraint(slaveCtrl.node ,interpOrientGrp.node))
							pm.parent(lookAtOffsetGrp.node, interpOrientGrp.node)
							
							#create the sources to avoid offsets
							rigComponentsGrp = MnsBuildModule.rigComponentsGrp

							sourceALoc , sourceBLoc = None, None

							for space in [spaceA, spaceB]:
								spaceName = "A"
								if space == spaceB: spaceName = "B"

								sourceAGrp = mnsUtils.createNodeReturnNameStd(parentNode = rigComponentsGrp, 
																	side =  slaveCtrl.side, 
																	body = slaveCtrl.body + "IOSourceA", 
																	alpha = slaveCtrl.alpha, 
																	id =  slaveCtrl.id, 
																	buildType = "group", 
																	incrementAlpha = False)
								mnsNodes.mnsMatrixConstraintNode(sources = [space], 
																targets = [sourceAGrp.node], 
																connectRotate = True, 
																connectTranslate = True, 
																connectScale = True, 
																maintainOffset = False)
								sourceLoc = mnsUtils.createNodeReturnNameStd(parentNode = sourceAGrp, 
																	side =  slaveCtrl.side, 
																	body = slaveCtrl.body + "Source" + spaceName, 
																	alpha = slaveCtrl.alpha, 
																	id =  slaveCtrl.id, 
																	buildType = "locator", 
																	incrementAlpha = False)
								sourceLoc.node.v.set(False)
								pm.makeIdentity(sourceLoc.node)
								pm.delete(pm.orientConstraint(interpOrientGrp.node, sourceLoc.node))

								if space == spaceA: sourceALoc = sourceLoc
								else: sourceBLoc = sourceLoc
							
							orientCns = mnsNodes.mayaConstraint([sourceALoc, sourceBLoc], interpOrientGrp.node, type = "orient", maintainOffset = False)
							mnsUtils.addAttrToObj([lookAtCtrl.node], type = "enum", value = ["______"], name = "interpolatedOrientation", replace = True, locked = True)
							
							sourceAWeightAttr = mnsUtils.addAttrToObj([lookAtCtrl.node], type = "float", min = 0.0, max = 1.0, value = spaceAWeight, name = spaceA.nodeName(), replace = True)[0]
							mnsNodes.connectAttrAttempt(sourceAWeightAttr, orientCns.node.attr(sourceALoc.node.nodeName() + "W0"))


							sourceBWeightAttr = mnsUtils.addAttrToObj([lookAtCtrl.node], type = "float", min = 0.0, max = 1.0, value = spaceAWeight, name = spaceB.nodeName(), replace = True)[0]
							
							revNode = mnsNodes.reverseNode([sourceAWeightAttr,0,0], 
															[sourceBWeightAttr, 0, 0],
															side = lookAtCtrl.side, 
															body = lookAtCtrl.body + "IO", 
															alpha = lookAtCtrl.alpha, 
															id = lookAtCtrl.id)

							mnsNodes.connectAttrAttempt(sourceBWeightAttr, orientCns.node.attr(sourceBLoc.node.nodeName() + "W1"))

							status, doAngleBasedScale = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doAngleBasedScale", False)
							if doAngleBasedScale:
								status, maxScale = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "maxScale", 2.0)
								status, angleMaxRange = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "angleMaxRange", 180.0)
								status, scaleWhenAngle = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "scaleWhenAngle", 0.0)

								originalOffsetGrp = blkUtils.getOffsetGrpForCtrl(slaveCtrl, type = "modifyGrp")
								targetOffsetGrp = mnsUtils.createOffsetGroup(slaveCtrl)
								
								sourceAngleLocator = mnsUtils.createNodeReturnNameStd(parentNode = originalOffsetGrp, 
																	side =  slaveCtrl.side, 
																	body = slaveCtrl.body + "AngleSource", 
																	alpha = slaveCtrl.alpha, 
																	id =  slaveCtrl.id, 
																	buildType = "locator", 
																	incrementAlpha = False)
								sourceAngleLocator.node.v.set(False)
								pm.makeIdentity(sourceAngleLocator.node)

								sourceAVector = mnsNodes.pmaNode(None, None, [sourceAngleLocator.node.getShape().worldPosition[0], sourceALoc.node.getShape().worldPosition[0]],
															None, None, None,
															side = slaveCtrl.side, 
															body = slaveCtrl.body + "SourceA", 
															alpha = slaveCtrl.alpha, 
															id = slaveCtrl.id,
															operation = 2)

								sourceBVector = mnsNodes.pmaNode(None, None, [sourceAngleLocator.node.getShape().worldPosition[0], sourceBLoc.node.getShape().worldPosition[0]],
															None, None, None,
															side = slaveCtrl.side, 
															body = slaveCtrl.body + "SourceB", 
															alpha = slaveCtrl.alpha, 
															id = slaveCtrl.id,
															operation = 2)

								angleBetweenNode = mnsNodes.angleBetweenNode(
															vector1 = sourceAVector.node.output3D,
															vector2 = sourceBVector.node.output3D,
															side = slaveCtrl.side, 
															body = slaveCtrl.body + "ScaleAngle", 
															alpha = slaveCtrl.alpha, 
															id = slaveCtrl.id)

								mnsUtils.addAttrToObj([lookAtCtrl.node], type = "enum", value = ["______"], name = "angleBasedScale", replace = True, locked = True)
								restAngleAttr = mnsUtils.addAttrToObj([lookAtCtrl.node], type = "float", value = angleBetweenNode.node.axisAngle.angle.get(), name = "restAngle", replace = True, locked = True, keyable = False, cb = True)[0]
								currentAngleAttr = mnsUtils.addAttrToObj([lookAtCtrl.node], type = "float", value = angleBetweenNode.node.axisAngle.angle.get(), name = "currentAngle", replace = True, locked = False, keyable = False, cb = True)[0]
								mnsNodes.connectAttrAttempt(angleBetweenNode.node.axisAngle.angle, currentAngleAttr)
								maxScaleAttr = mnsUtils.addAttrToObj([lookAtCtrl.node], type = "float", value = maxScale, name = "maxScale", replace = True)[0]
								angleMaxRangeAttr = mnsUtils.addAttrToObj([lookAtCtrl.node], type = "float", min = 0.0, value = angleMaxRange, name = "angleMaxRange", replace = True)[0]

								setRangeNode = None
								if scaleWhenAngle == 1:
									setRangeNode = mnsNodes.setRangeNode([1.0, 1.0, 1.0],
																		[maxScaleAttr, 1.0, 1.0],
																		[angleBetweenNode.node.axisAngle.angle.get(), 1.0, 1.0],
																		[angleMaxRangeAttr, 1.0, 1.0],
																		[angleBetweenNode.node.axisAngle.angle, 1.0, 1.0],
																		[None, None, None])
								else:
									setRangeNode = mnsNodes.setRangeNode([maxScaleAttr, 1.0, 1.0],
																		[1.0, 1.0, 1.0],
																		[angleMaxRangeAttr, 1.0, 1.0],
																		[angleBetweenNode.node.axisAngle.angle.get(), 1.0, 1.0],
																		[angleBetweenNode.node.axisAngle.angle, 1.0, 1.0],
																		[None, None, None])

								status, connectToTargetAxis = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "connectToTargetAxis", 1)
							
								if connectToTargetAxis == 0: mnsNodes.connectAttrAttempt(setRangeNode.node.outValueX, targetOffsetGrp.node.sx)
								if connectToTargetAxis == 1: mnsNodes.connectAttrAttempt(setRangeNode.node.outValueX, targetOffsetGrp.node.sy)
								if connectToTargetAxis == 2: mnsNodes.connectAttrAttempt(setRangeNode.node.outValueX, targetOffsetGrp.node.sz)
