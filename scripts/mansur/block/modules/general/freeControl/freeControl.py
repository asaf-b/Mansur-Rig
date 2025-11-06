"""Author: Asaf Ben-Zur
Best used for: Free objects, General Control, Mesh Tweaker, Mesh Local Tweaker
This Module is a general single control at it's base state.
It also contains a Mesh-Tweaker feature that will allow you to create a "Double Directional" tweaker- meaning that the control will follow the input Mesh's position (Rivet) and will also be able to affect it.
This effect is also commonly knowen as the "Dorito-Effect".
This feature also includes a "local" mode, to tunnel deformations from the control to a local skinCluster, then a blend-shape to the main Mesh, creating multi-layered skinned mesh.
All of these features will use the main joint as the effector.
Note: When using the "Mesh-Tweaker" feture, when needing to affect a mesh that will also be used as the rivet input- make sure "sameMeshAffector" is set to ON.
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

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	offsetRigMaster = None
	status, asMeshTweaker = mnsUtils.validateAttrAndGet(rootGuide, "asMeshTweaker", False)
	if not asMeshTweaker: offsetRigMaster = relatedJnt
	
	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("channelControl", MnsBuildModule.rootGuide.node)
	status, controlShape = mnsUtils.validateAttrAndGet(rootGuide, "controlShape", "square")
	ctrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = controlShape,
								scale = modScale, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								creatgearMasterSwitchGroup = False,
								createOffsetGrp = True,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial,
								offsetRigMaster = offsetRigMaster)
	ctrlsCollect.append(ctrl)

	status, createJoint = mnsUtils.validateAttrAndGet(rootGuide, "createJoint", True)

	######## mesh tweaker #########
	status, asMeshTweaker = mnsUtils.validateAttrAndGet(rootGuide, "asMeshTweaker", False)
	simpleRivetsNode = False
	createdLocalSetup = False
	originCtrl = None
	
	host = MnsBuildModule.attrHostCtrl or originCtrl or ctrl

	#mesh tweaker
	if asMeshTweaker and createJoint and relatedJnt:
		status, positionMode = mnsUtils.validateAttrAndGet(rootGuide, "positionMode", 0)
		status, doRotation = mnsUtils.validateAttrAndGet(rootGuide, "doRotation", False)
		status, sameMeshAffector = mnsUtils.validateAttrAndGet(rootGuide, "sameMeshAffector", True)
		status, rivetToMesh = mnsUtils.validateAttrAndGet(rootGuide, "rivetToMesh", "")
		status, isLocal = mnsUtils.validateAttrAndGet(rootGuide, "isLocal", False)

		rivetToMesh = mnsUtils.checkIfObjExistsAndSet(rivetToMesh)
		if rivetToMesh:
			simpleRivetsNode = blkUtils.getSimpleRivetsNodeForMesh(rivetToMesh)
			
			if simpleRivetsNode and sameMeshAffector:
				localCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								bodySuffix = "Local",
								ctrlType = "techCtrl", 
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = controlShape,
								scale = modScale, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								creatgearMasterSwitchGroup = False,
								createOffsetGrp = True,
								isFacial = MnsBuildModule.isFacial)
				localOffset = blkUtils.getOffsetGrpForCtrl(localCtrl)
				localOffset.node.v.set(False)
				localCtrl.node.v.set(False)

				offsetGrp = blkUtils.getOffsetGrpForCtrl(ctrl)
				nextElementIdx = simpleRivetsNode.rivet.numElements()
				simpleRivetsNode.rivet[nextElementIdx].positionMode.set(positionMode)
				ctrl.node.worldMatrix[0] >> simpleRivetsNode.rivet[nextElementIdx].rivetStartPosition
				simpleRivetsNode.rivet[nextElementIdx].rivetStartPosition.disconnect()
				offsetGrp.node.parentInverseMatrix[0] >> simpleRivetsNode.rivet[nextElementIdx].targetParentInverseMatrix
				simpleRivetsNode.transform[nextElementIdx].t >> offsetGrp.node.t
				if doRotation:
					simpleRivetsNode.transform[nextElementIdx].r >> offsetGrp.node.r
				ctrl.node.t >> localCtrl.node.t
				ctrl.node.r >> localCtrl.node.r
				ctrl.node.s >> localCtrl.node.s

				blkUtils.muteLocalTransformations(ctrl, s = False, r = False)
				originCtrl = ctrl
				ctrl = localCtrl

				if isLocal:
					pm.parent(localOffset.node, animStaticGrp.node)
					createdLocalSetup = True
			else:
				offsetGrp = blkUtils.getOffsetGrpForCtrl(ctrl)
				nextElementIdx = simpleRivetsNode.rivet.numElements()
				simpleRivetsNode.rivet[nextElementIdx].positionMode.set(positionMode)
				ctrl.node.worldMatrix[0] >> simpleRivetsNode.rivet[nextElementIdx].rivetStartPosition
				simpleRivetsNode.rivet[nextElementIdx].rivetStartPosition.disconnect()
				offsetGrp.node.parentInverseMatrix[0] >> simpleRivetsNode.rivet[nextElementIdx].targetParentInverseMatrix
				simpleRivetsNode.transform[nextElementIdx].t >> offsetGrp.node.t
				if doRotation:
					simpleRivetsNode.transform[nextElementIdx].r >> offsetGrp.node.r
	#spring
	status, doSpring = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doSpring", False)
	if doSpring and not createdLocalSetup:
		status, defaultStiffness = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "defaultStiffness", 0.5)
		status, defaultDamping = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "defaultDamping", 0.5)
		status, springSlaveControlShape = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "springSlaveControlShape", "lightSphere")

		offsetGrp = blkUtils.getOffsetGrpForCtrl(ctrl)
		springSlaveCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								bodySuffix = "Spring",
								blkCtrlTypeID = 1,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = springSlaveControlShape,
								scale = modScale * 0.5, 
								parentNode = offsetGrp,
								symmetryType = symmetryType,
								doMirror = False,
								creatgearMasterSwitchGroup = False,
								createOffsetGrp = True,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial)
		ctrlsCollect.append(springSlaveCtrl)
		springOffsetGrp = blkUtils.getOffsetGrpForCtrl(springSlaveCtrl)
		mnsNodes.mnsMatrixConstraintNode(side = ctrl.side, alpha = ctrl.alpha, id = ctrl.id, targets = [springOffsetGrp.node], sources = [ctrl.node], connectTranslate = False)


		tsNode = mnsNodes.mnsTransformSpringNode(side =rootGuide.side, 
									body = rootGuide.body, 
									alpha = rootGuide.alpha, 
									id = rootGuide.id,
									inputWorldMatrix = ctrl.node.worldMatrix[0],
									targetParentInverseMatrix = springOffsetGrp.node.parentInverseMatrix[0],
									outTranslate = springOffsetGrp.node.t,
									damaping = defaultStiffness,
									stiffness = defaultDamping)

		status, springX = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "springX", True)
		status, springY = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "springY", True)
		status, springZ = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "springZ", True)
		status, flipRightX = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "flipRightX", False)
		status, flipRightY = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "flipRightY", False)
		status, flipRightZ = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "flipRightZ", False)

		if not springX or not springY or not springZ:
			#create an intermediete receiver
			itermediateGrp = mnsUtils.createNodeReturnNameStd(parentNode = springOffsetGrp.node.getParent(), 
														side =  springOffsetGrp.side, 
														body = springOffsetGrp.body + "Rec", 
														alpha = springOffsetGrp.alpha, 
														id =  springOffsetGrp.id, 
														buildType = "offsetGrp", 
														incrementAlpha = False)
			tsNode.node.translate >> itermediateGrp.node.t
			springOffsetGrp.node.t.disconnect()
			if ctrl.side == "r" and flipRightX:
				mnsNodes.mdlNode(ctrl.node.tx, -1.0, springOffsetGrp.node.tx)
			else:
				ctrl.node.tx >> springOffsetGrp.node.tx
			if ctrl.side == "r" and flipRightY:
				mnsNodes.mdlNode(ctrl.node.ty, -1.0, springOffsetGrp.node.ty)
			else:
				ctrl.node.ty >> springOffsetGrp.node.ty
			if ctrl.side == "r" and flipRightZ:
				mnsNodes.mdlNode(ctrl.node.tz, -1.0, springOffsetGrp.node.tz)
			else:
				ctrl.node.tz >> springOffsetGrp.node.tz
			
			if springX: itermediateGrp.node.translate.translateX >> springOffsetGrp.node.tx
			if springY: itermediateGrp.node.translate.translateY >> springOffsetGrp.node.ty
			if springZ: itermediateGrp.node.translate.translateZ >> springOffsetGrp.node.tz

		#attributes
		mnsUtils.addAttrToObj([host.node], type = "enum", value = ["______"], name = "springSettings", replace = True, locked = True)
		strengthAttr = mnsUtils.addAttrToObj([host.node], type = "float", min = 0.0, max = 1.0, value = 1.0, name = "strength", replace = True)[0]
		strengthAttr >> tsNode.node.strength
		stiffnessAttr = mnsUtils.addAttrToObj([host.node], type = "float", min = 0.0, max = 1.0, value = defaultStiffness, name = "stiffness", replace = True)[0]
		stiffnessAttr >> tsNode.node.stiffness
		dampingAttr = mnsUtils.addAttrToObj([host.node], type = "float", min = 0.0, max = 1.0, value = defaultDamping, name = "damping", replace = True)[0]
		dampingAttr >> tsNode.node.damping

		startFrameAttr = mnsUtils.addAttrToObj([host.node], type = "int", value = 1, name = "startFrame", replace = True, keyable = False, cb = True, locked = False)[0]
		startFrameAttr >> tsNode.node.startFrame

		startFrameFromRangeAttr = mnsUtils.addAttrToObj([host.node], type = "bool", value = True, name = "startFrameFromRange", replace = True, keyable = False, cb = True, locked = False)[0]
		startFrameFromRangeAttr >> tsNode.node.startFrameFromRange
		
		#store main ctrl for intrpOrient
		mnsUtils.addAttrToObj([springSlaveCtrl.node], type = "message", name = "targetInterpOrient", value= ctrl.node, replace = True)[0]

		ctrl = springSlaveCtrl
	
	########### Transfer Authority ###########
	status, createJoint = mnsUtils.validateAttrAndGet(rootGuide, "createJoint", True)

	if createJoint and relatedJnt: 
		blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)
	else:
		attr = mnsUtils.addAttrToObj([ctrl.node], type = "message", name = "guideAuthority", value= rootGuide.node, replace = True)[0]
		attr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "ctrlAuthority", value= ctrl.node, replace = True)[0]

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, host, host

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core.prefixSuffix import GLOB_mnsJntStructDefaultSuffix

	rootGuide = guides[0]
	relatedRootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(rootGuide))
	status, createJoint = mnsUtils.validateAttrAndGet(rootGuide, "createJoint", True)

	parentJnt = blkUtils.recGetParentJoint(rootGuide.node.getParent())

	if relatedRootJnt and not createJoint:
		jntChildren = relatedRootJnt.node.listRelatives(c = True, type = "joint")
		if jntChildren: 
			pm.parent(jntChildren, relatedRootJnt.node.getParent())
			#zero joint orient
			for j in jntChildren:
				j.jointOrient.set((0.0,0.0,0.0))
		pm.delete(relatedRootJnt.node)
		relatedRootJnt = None

	if relatedRootJnt and relatedRootJnt.node.getParent() != parentJnt.node:
		pm.parent(relatedRootJnt.node, parentJnt.node)

	if createJoint and not relatedRootJnt:
		gScale = mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]

		gJnt = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body, alpha = rootGuide.alpha, id = rootGuide.id, buildType = "rootJoint", createBlkClassID = True, incrementAlpha = True)
		mnsUtils.lockAndHideAllTransforms(gJnt, lock = True, keyable = False, cb = False)
		gJnt.node.radius.set(gScale)
		rootGuide.node.jntSlave.setLocked(False)
		gJnt.node.message >> rootGuide.node.jntSlave
		rootGuide.node.jntSlave.setLocked(True)
		
		if parentJnt:
			pm.parent(gJnt.node, parentJnt.node)

		mnsNodes.mnsMatrixConstraintNode(side = rootGuide.side, alpha = rootGuide.alpha , id = rootGuide.id, targets = [gJnt.node], sources = [rootGuide.node], connectScale = False)
		mnsNodes.mnsNodeRelationshipNode(side = rootGuide.side, alpha = rootGuide.alpha , id = rootGuide.id, master = rootGuide.node, slaves = [gJnt.node])

		guideChildren = rootGuide.node.listRelatives(c = True, type = "transform")
		if guideChildren:
			for guideChild in guideChildren:
				relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(guideChild))
				if relatedJnt: 
					pm.parent(relatedJnt.node, gJnt.node)
					relatedJnt.node.jointOrient.set((0.0,0.0,0.0))

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
				status, doSpring = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "doSpring", False)
				if doSpring:
					status, slaveCtrl = mnsUtils.validateAttrAndGet(ctrlAuthority, "targetInterpOrient", None)
					slaveCtrl = mnsUtils.validateNameStd(slaveCtrl)

				if slaveCtrl:
					spaceA = mnsUtils.checkIfObjExistsAndSet(mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "spaceA", None)[1])
					spaceB = mnsUtils.checkIfObjExistsAndSet(mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "spaceB", None)[1])
					spaceA = blkUtils.convertInputObjToSpace(spaceA)
					spaceB = blkUtils.convertInputObjToSpace(spaceB)

					if spaceA and spaceB and not spaceA is spaceB:
						status, spaceAWeight = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "spaceAWeight", 0.5)
						spaceBWeight = 1.0 - spaceAWeight;

						ctrlOffsetGrp = blkUtils.getOffsetGrpForCtrl(slaveCtrl)
						interpOrientGrp = mnsUtils.createNodeReturnNameStd(parentNode = ctrlOffsetGrp.node.getParent(), 
														side =  slaveCtrl.side, 
														body = slaveCtrl.body, 
														alpha = slaveCtrl.alpha, 
														id =  slaveCtrl.id, 
														buildType = "modifyGrp", 
														incrementAlpha = False)

						pm.delete(pm.parentConstraint(slaveCtrl.node ,interpOrientGrp.node))
						pm.parent(ctrlOffsetGrp.node, interpOrientGrp.node)
						
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
						mnsUtils.addAttrToObj([slaveCtrl.node], type = "enum", value = ["______"], name = "interpolatedOrientation", replace = True, locked = True)
						
						sourceAWeightAttr = mnsUtils.addAttrToObj([slaveCtrl.node], type = "float", min = 0.0, max = 1.0, value = spaceAWeight, name = spaceA.nodeName(), replace = True)[0]
						mnsNodes.connectAttrAttempt(sourceAWeightAttr, orientCns.node.attr(sourceALoc.node.nodeName() + "W0"))


						sourceBWeightAttr = mnsUtils.addAttrToObj([slaveCtrl.node], type = "float", min = 0.0, max = 1.0, value = spaceAWeight, name = spaceB.nodeName(), replace = True)[0]
						
						revNode = mnsNodes.reverseNode([sourceAWeightAttr,0,0], 
														[sourceBWeightAttr, 0, 0],
														side = slaveCtrl.side, 
														body = slaveCtrl.body + "IO", 
														alpha = slaveCtrl.alpha, 
														id = slaveCtrl.id)

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

							mnsUtils.addAttrToObj([slaveCtrl.node], type = "enum", value = ["______"], name = "angleBasedScale", replace = True, locked = True)
							restAngleAttr = mnsUtils.addAttrToObj([slaveCtrl.node], type = "float", value = angleBetweenNode.node.axisAngle.angle.get(), name = "restAngle", replace = True, locked = True, keyable = False, cb = True)[0]
							currentAngleAttr = mnsUtils.addAttrToObj([slaveCtrl.node], type = "float", value = angleBetweenNode.node.axisAngle.angle.get(), name = "currentAngle", replace = True, locked = False, keyable = False, cb = True)[0]
							mnsNodes.connectAttrAttempt(angleBetweenNode.node.axisAngle.angle, currentAngleAttr)
							maxScaleAttr = mnsUtils.addAttrToObj([slaveCtrl.node], type = "float", value = maxScale, name = "maxScale", replace = True)[0]
							angleMaxRangeAttr = mnsUtils.addAttrToObj([slaveCtrl.node], type = "float", min = 0.0, value = angleMaxRange, name = "angleMaxRange", replace = True)[0]

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