"""Author: Asaf Ben-Zur
Best used for: General Chain, Spine, Neck, Tail, Elephant-Trunk, Tentacle 
This Module when used in it's basic state, will create a simple FK hierarchy control chain. 
Altough this module contains many layers with many features such as Variable FK, Spring, Embedded IK, Secondary IK chains (interpolation controls).
Use as many layers an in any combination to create any form of FK chain behaviour.
"""



from maya import cmds
import pymel.core as pm


def construct(mansur, MnsBuildModule, **kwargs):
	def createPrimaryCtrls():
		#attributes gather
		status, FKcontrolShape = mnsUtils.validateAttrAndGet(rootGuide, "FKcontrolShape", "circle")
		status, FKChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "FKChannelControl", {})
		if status: FKChannelControl = mnsUtils.splitEnumAttrToChannelControlList("FKChannelControl", rootGuide.node)

		#controls
		primaryFkControls = []
		for guide in allGuides:
			relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(guide))	

			parNode = animGrp
			if primaryFkControls: parNode = primaryFkControls[-1]

			createSS = False
			if doPrimariesSpaceSwitch: createSS = True

			ctrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
										controlShape = FKcontrolShape,
										scale = modScale, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = guide.node,
										createOffsetGrp = True,
										createSpaceSwitchGroup = createSS,
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial,
										offsetRigMaster = relatedJnt,
										freezeScale = True
										)

			if doPrimariesSpaceSwitch and primaryFkControls:
				internalSpacesDict.update({ctrl.name: [primaryFkControls[-1].node]})

			ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl, type = "offsetGrp")
			if doPrimariesSpaceSwitch:
				ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl, type = "spaceSwitchGrp")

			pm.parent(ctrlOffset.node, parNode.node)
			primaryFkControls.append(ctrl)
			
		status, doFKSeconderyIK = mnsUtils.validateAttrAndGet(rootGuide, "doFKSeconderyIK", False)
		secondaryIKs = []
		if doFKSeconderyIK:
			status, FKSecondaryIKControlShape = mnsUtils.validateAttrAndGet(rootGuide, "FKSecondaryIKControlShape", "diamond")

			for primFK in primaryFkControls:
				ctrlIK = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
										bodySuffix = "SecIk",
										blkCtrlTypeID = 1,
										controlShape = FKSecondaryIKControlShape,
										scale = modScale * 0.5, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = primFK.node,
										createOffsetGrp = False,
										createSpaceSwitchGroup = False,
										parentNode = primFK,
										symmetryType = symmetryType,
										doMirror = True,
										chennelControl = FKChannelControl,
										isFacial = MnsBuildModule.isFacial
										)
				secondaryIKs.append(ctrlIK)

		return primaryFkControls, secondaryIKs

	def createEmbeddedIK():
		builtCtrls = []

		#create component group
		componentGroup = mnsUtils.createNodeReturnNameStd(parentNode = rigComponentsGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EmbeddedIKComponents", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
		componentGroup.node.v.set(False)

		#create the curves and structure them
		status, embeddedIKCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "embIKCurveDegree", 3)
		status, embIKInterpolation = mnsUtils.validateAttrAndGet(rootGuide, "embIKInterpolation", 0)

		#create the control
		status, embeddedIKControlShape = mnsUtils.validateAttrAndGet(rootGuide, "embIKControlShape", "curvedFourArrow")
		status, embeddedIKChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "embIKChannelControl", {})
		if status: embeddedIKChannelControl = mnsUtils.splitEnumAttrToChannelControlList("embIKChannelControl", rootGuide.node)

		tipIkCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = "TipIK",
											controlShape = embeddedIKControlShape, 
											scale = modScale * 2, 
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = primaryFkControls[-1].node,
											createOffsetGrp = True,
											createSpaceSwitchGroup = True,
											parentNode = animGrp,
											symmetryType = symmetryType,
											doMirror = True,
											isFacial = MnsBuildModule.isFacial
											)
		builtCtrls.append(tipIkCtrl)
		mnsUtils.lockAndHideTransforms(tipIkCtrl.node, negateOperation = True, sx = False, sz = False, lock = True)

		midIKCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = "MidIK",
											controlShape = embeddedIKControlShape,
											scale = modScale * 2, 
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = primaryFkControls[0].node,
											createOffsetGrp = True,
											createSpaceSwitchGroup = True,
											parentNode = animGrp,
											symmetryType = symmetryType,
											doMirror = True,
											isFacial = MnsBuildModule.isFacial
											)
		builtCtrls.append(midIKCtrl)
		mnsUtils.lockAndHideTransforms(midIKCtrl.node, negateOperation = True, sx = False, sz = False, lock = True)

		baseIkCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = "BaseIk",
											controlShape = embeddedIKControlShape,
											scale = modScale * 2, 
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = primaryFkControls[0].node,
											createOffsetGrp = True,
											createSpaceSwitchGroup = True,
											parentNode = animGrp,
											symmetryType = symmetryType,
											doMirror = True,
											isFacial = MnsBuildModule.isFacial
											)
		builtCtrls.append(baseIkCtrl)
		mnsUtils.lockAndHideTransforms(baseIkCtrl.node, negateOperation = True, sx = False, sz = False, lock = True)

		status, embIKMode = mnsUtils.validateAttrAndGet(rootGuide, "embIKMode", 0)
		status, ikCurveInterpolation = mnsUtils.validateAttrAndGet(rootGuide, "ikCurveInterpolation", 0)
		"""
		modes:
		0- btcTranslation
		1- btcRotation
		2- skinnedWithMidCtrl
		3- skinnedPolesSingleTan
		4- skinnedPolesDoubleTan
		"""

		pocCurveInput, pocCurveOffsetInput = None, None 
		#create the curves and structure them
		embeddedIKBtc = mnsNodes.mnsBuildTransformsCurveNode(
												side = MnsBuildModule.rootGuide.side, 
												alpha = MnsBuildModule.rootGuide.alpha, 
												id = MnsBuildModule.rootGuide.id, 
												body = MnsBuildModule.rootGuide.body + "EmbIk", 
												transforms = [baseIkCtrl, midIKCtrl, tipIkCtrl], 
												deleteCurveObjects = True, 
												tangentDirection = 1, 
												buildOffsetCurve = True,
												buildMode = ikCurveInterpolation,
												degree = embeddedIKCurveDegree,
												offsetX = offsetX,
												offsetY = offsetY,
												offsetZ = offsetZ)


		pocCurveInput = embeddedIKBtc["node"].node.outCurve
		pocCurveOffsetInput = embeddedIKBtc["node"].node.outOffsetCurve
													
		#create locs
		topJnt = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EmbeddedIkTip", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(tipIkCtrl.node, topJnt.node))
		topJnt.node.v.set(False)
		pm.parent(topJnt.node, tipIkCtrl.node)

		midJnt = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EmbeddedIkMid", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(midIKCtrl.node, midJnt.node))
		midJnt.node.v.set(False)
		pm.parent(midJnt.node, midIKCtrl.node)

		bottomJoint = mnsUtils.createNodeReturnNameStd(side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EmbeddedIkBase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(primaryFkControls[0].node, bottomJoint.node))
		bottomJoint.node.v.set(False)
		pm.parent(bottomJoint.node, baseIkCtrl.node)
		
		#constrain mid Ctrl
		pm.delete(pm.parentConstraint([tipIkCtrl.node, baseIkCtrl.node], midIKCtrl.node))
		ikMidModGrp = mnsUtils.createOffsetGroup(midIKCtrl, type = "modifyGrp")
		
		constraintType = "point"
		if embIKMode == 1: constraintType = "parent"
		pointCns = mnsNodes.mayaConstraint([bottomJoint.node, topJnt.node], ikMidModGrp.node, type = constraintType, maintainOffset = True)
		if embIKMode == 1:
			for axis in "xyz": ikMidModGrp.node.attr("r" + axis).disconnect()

		#tangents
		status, doMidTangentCtrls = mnsUtils.validateAttrAndGet(rootGuide, "doMidTangentCtrls", True)
		if doMidTangentCtrls:
			tanACtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
												bodySuffix = "TangentA",
												controlShape = "lightSphere",
												scale = modScale * 0.3, 
												blkCtrlTypeID = 0,
												color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
												matchTransform = midIKCtrl.node,
												createOffsetGrp = True,
												createSpaceSwitchGroup = False,
												parentNode = midIKCtrl,
												symmetryType = symmetryType,
												doMirror = False,
												isFacial = MnsBuildModule.isFacial
												)
			builtCtrls.append(tanACtrl)
			mnsUtils.lockAndHideTransforms(tanACtrl.node, tx = False, ty = False, tz = False, lock = True)

			tanBCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
												bodySuffix = "TangentB",
												controlShape = "lightSphere",
												scale = modScale * 0.3, 
												blkCtrlTypeID = 0,
												color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
												matchTransform = midIKCtrl.node,
												createOffsetGrp = True,
												createSpaceSwitchGroup = False,
												parentNode = midIKCtrl,
												symmetryType = symmetryType,
												doMirror = False,
												isFacial = MnsBuildModule.isFacial
												)
			builtCtrls.append(tanBCtrl)
			mnsUtils.lockAndHideTransforms(tanBCtrl.node, tx = False, ty = False, tz = False, lock = True)

			#tanVis
			tanVisAttr = mnsUtils.addAttrToObj([midIKCtrl.node], type = "bool", value = False, name = "tangentVis", replace = True)[0]
			for tanCtrl in [tanACtrl, tanBCtrl]:
				for shape in tanCtrl.node.getShapes(): tanVisAttr >> shape.v

			#tan position
			tempPocn = mnsNodes.mnsPointsOnCurveNode(inputCurve = embeddedIKBtc["node"].node.outCurve,
													inputUpCurve = embeddedIKBtc["node"].node.outOffsetCurve,
													buildOutputs = False,
													buildMode = 0,
													aimAxis = 1,
													upAxis = 0,
													numOutputs = 5,
													doScale = False
													)
			tempLoc = pm.createNode("transform")
			tempPocn["node"].node.transforms[1].translate >> tempLoc.t
			tempPocn["node"].node.transforms[1].rotate >> tempLoc.r
			pm.delete(pm.parentConstraint(tempLoc, blkUtils.getOffsetGrpForCtrl(tanACtrl).node))
			tempPocn["node"].node.transforms[3].translate >> tempLoc.t
			tempPocn["node"].node.transforms[3].rotate >> tempLoc.r
			pm.delete(pm.parentConstraint(tempLoc, blkUtils.getOffsetGrpForCtrl(tanBCtrl).node))
			tempPocn["node"].node.curve.disconnect()
			tempPocn["node"].node.upCurve.disconnect()
			pm.delete(tempPocn["node"].node, tempLoc)

			#create base locs from mid tangents
			midBaseGrp = mnsUtils.createNodeReturnNameStd(parentNode = animGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "EmbeddedIKMidBase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
			pointCns = mnsNodes.mayaConstraint([bottomJoint.node, topJnt.node], midBaseGrp.node, type = "point", maintainOffset = False)
			midBaseGrp.node.v.set(False)

			tanABaseLoc = mnsUtils.createNodeReturnNameStd(parentNode = midBaseGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "tanABase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
			tanABaseLoc.node.v.set(False)
			pm.delete(pm.parentConstraint(tanACtrl.node, tanABaseLoc.node))
			pointCns = mnsNodes.mayaConstraint([midIKCtrl.node], tanABaseLoc.node, type = "point", maintainOffset = True)

			tanBBaseLoc = mnsUtils.createNodeReturnNameStd(parentNode = midBaseGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "tanBBase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
			tanBBaseLoc.node.v.set(False)
			pm.delete(pm.parentConstraint(tanBCtrl.node, tanBBaseLoc.node))
			pointCns = mnsNodes.mayaConstraint([midIKCtrl.node], tanBBaseLoc.node, type = "point", maintainOffset = True)


			embeddedIKTweakBaseBtc = mnsNodes.mnsBuildTransformsCurveNode(
												side = MnsBuildModule.rootGuide.side, 
												alpha = MnsBuildModule.rootGuide.alpha, 
												id = MnsBuildModule.rootGuide.id, 
												body = MnsBuildModule.rootGuide.body + "TweakBase", 
												transforms = [baseIkCtrl, tanABaseLoc, midIKCtrl, tanBBaseLoc, tipIkCtrl], 
												deleteCurveObjects = True, 
												tangentDirection = 1, 
												buildOffsetCurve = False,
												buildMode = 1,
												degree = embeddedIKCurveDegree,
												offsetX = 0.0,
												offsetY = 0.0,
												offsetZ = 0.0)

			embeddedIKTweakBtc = mnsNodes.mnsBuildTransformsCurveNode(
												side = MnsBuildModule.rootGuide.side, 
												alpha = MnsBuildModule.rootGuide.alpha, 
												id = MnsBuildModule.rootGuide.id, 
												body = MnsBuildModule.rootGuide.body + "Tweak", 
												transforms = [baseIkCtrl, tanACtrl, midIKCtrl, tanBCtrl, tipIkCtrl], 
												deleteCurveObjects = True, 
												tangentDirection = 1, 
												buildOffsetCurve = False,
												buildMode = 1,
												degree = embeddedIKCurveDegree,
												offsetX = 0.0,
												offsetY = 0.0,
												offsetZ = 0.0)

			if len(primaryFkControls) > 3:
				embeddedIKBtc["node"].node.resample.set(True)
				embeddedIKBtc["node"].node.substeps.set(5)
				embeddedIKTweakBaseBtc["node"].node.outCurve >> embeddedIKBtc["node"].node.tweakCurveBase
				embeddedIKTweakBtc["node"].node.outCurve >> embeddedIKBtc["node"].node.tweakCurve
			elif primBtcNode and len(primaryFkControls) < 4:
				primBtcNode.resample.set(True)
				primBtcNode.substeps.set(5)
				embeddedIKTweakBaseBtc["node"].node.outCurve >> primBtcNode.tweakCurveBase
				embeddedIKTweakBtc["node"].node.outCurve >> primBtcNode.tweakCurve

		if embeddedIKChannelControl:
			mnsUtils.applyChennelControlAttributesToTransform(tipIkCtrl.node, embeddedIKChannelControl)
			mnsUtils.applyChennelControlAttributesToTransform(midIKCtrl.node, embeddedIKChannelControl)
			mnsUtils.applyChennelControlAttributesToTransform(baseIkCtrl.node, embeddedIKChannelControl)

		#create vis switch
		ikVisState, fkVisState = True, True
		status, defaultVisibilityMode = mnsUtils.validateAttrAndGet(rootGuide, "defaultVisibilityMode", 1)
		if status:
			if defaultVisibilityMode == 0: fkVisState = False
			if defaultVisibilityMode == 1: ikVisState = False

		mnsUtils.addAttrToObj([attrHost.node], type = "enum", value = ["______"], name = "ctrlVis", replace = True, locked = True)
		ikVisAttr = mnsUtils.addAttrToObj([attrHost.node], type = "bool", value = ikVisState, name = "ikVis", replace = True)[0]
		fkVisAttr = mnsUtils.addAttrToObj([attrHost.node], type = "bool", value = fkVisState, name = "fkVis", replace = True)[0]


		for ctrl in [tipIkCtrl, midIKCtrl, baseIkCtrl]:
			ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl)
			ikVisAttr >> ctrlOffset.node.v

		for ctrl in primaryFkControls:
			ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl)
			fkVisAttr >> ctrlOffset.node.v

		FKModGrps = []
		for l, FKControl in enumerate(primaryFkControls):
			fkModGrp = mnsUtils.createOffsetGroup(FKControl, type = "modifyGrp")
			FKModGrps.append(fkModGrp)

		#poc primaries on the curve, and input local channels
		embeddedPocNode = mnsNodes.mnsPointsOnCurveNode(
														side = rootGuide.side, 
														alpha = rootGuide.alpha, 
														id = rootGuide.id, 
														body = rootGuide.body + "EmbeddedIK", 
														inputCurve = pocCurveInput,
														inputUpCurve = pocCurveOffsetInput,
														buildOutputs = True,
														buildMode = 0,
														aimAxis = 1,
														upAxis = 0,
														numOutputs = len(allGuides),
														doScale = False
														)
		blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> embeddedPocNode["node"].node.globalScale

		
		resultTransforms = embeddedPocNode["samples"]
		
		#connect FK controls to embeddded IK
		"""
		parentNode = rigComponentsGrp.node
		for j, sample in enumerate(resultTransforms): 
			sample = mnsUtils.validateNameStd(sample)
			sample.node.v.set(False)
			pm.parent(sample.node, componentGroup.node)
			intermediateSample = mnsUtils.createNodeReturnNameStd(side =  rootGuide.side, body = rootGuide.body + "Intermediate", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "locator", incrementAlpha = False)
			intermediateSample.node.v.set(False)
			dupHeirGrp = mnsUtils.createNodeReturnNameStd(side =  rootGuide.side, body = rootGuide.body + "InermediateDup", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)
			dupHeirGrp.node.v.set(False)
			pm.delete(pm.parentConstraint(FKModGrps[j].node.getParent(), dupHeirGrp.node))
			pm.parent(dupHeirGrp.node, parentNode)
			pm.parent(intermediateSample.node, dupHeirGrp.node)
			pm.makeIdentity(intermediateSample.node)

			if j == 0:
				mnsNodes.mnsMatrixConstraintNode(sources = [sample.node], targets = [intermediateSample.node], connectRotate = False, connectTranslate = True, connectScale = False, maintainOffset = True)
				mnsNodes.mnsMatrixConstraintNode(sources = [baseIkCtrl.node], targets = [intermediateSample.node], connectRotate = True, connectTranslate = False, connectScale = False, maintainOffset = True)
				#constraint Dup Hierarchy
				matConNode = mnsNodes.mnsMatrixConstraintNode(sources = [animGrp.node], targets = [dupHeirGrp.node], maintainOffset = True)
			elif j == (len(resultTransforms) - 1):
				mnsNodes.mnsMatrixConstraintNode(sources = [sample.node], targets = [intermediateSample.node], connectRotate = False, connectTranslate = True, connectScale = False, maintainOffset = True)
				mnsNodes.mnsMatrixConstraintNode(sources = [tipIkCtrl.node], targets = [intermediateSample.node], connectRotate = True, connectTranslate = False, connectScale = False, maintainOffset = True)
			else:
				mnsNodes.mnsMatrixConstraintNode(sources = [sample.node], targets = [intermediateSample.node], connectRotate = True, connectTranslate = True, connectScale = False, maintainOffset = True)
			
			intermediateSample.node.t >> FKModGrps[j].node.t
			intermediateSample.node.r >> FKModGrps[j].node.r

			parentNode = intermediateSample.node
		"""

		for j, sample in enumerate(resultTransforms): 
			#cleanup variables for readability
			targetTransformStd = FKModGrps[j]
			sourceTransformStd = mnsUtils.validateNameStd(sample)
			
			#handle the new poc sample
			pm.parent(sourceTransformStd.node, componentGroup.node)
			sourceTransformStd.node.v.set(False)

			if j == 0:
				mnsNodes.mnsMatrixConstraintNode(sources = [sourceTransformStd.node], targets = [targetTransformStd.node], connectRotate = False, connectTranslate = True, connectScale = False, maintainOffset = True)
				mnsNodes.mnsMatrixConstraintNode(sources = [baseIkCtrl.node], targets = [targetTransformStd.node], connectRotate = True, connectTranslate = False, connectScale = False, maintainOffset = True)
			elif j == (len(resultTransforms) - 1):
				mnsNodes.mnsMatrixConstraintNode(sources = [sourceTransformStd.node], targets = [targetTransformStd.node], connectRotate = False, connectTranslate = True, connectScale = False, maintainOffset = True)
				mnsNodes.mnsMatrixConstraintNode(sources = [tipIkCtrl.node], targets = [targetTransformStd.node], connectRotate = True, connectTranslate = False, connectScale = False, maintainOffset = True)
			else:
				mnsNodes.mnsMatrixConstraintNode(sources = [sourceTransformStd.node], targets = [targetTransformStd.node], connectRotate = True, connectTranslate = True, connectScale = False, maintainOffset = True)
			
			#restore FK #temp solution, until some other way is found
			if j != 0:
				#create the need heirarchy for the FK controls
				#This setup is created to maintain FK behaviour
				#while constraining to the IK result
				for n in range(j):
					#save ctrl pos
					posLoc = pm.spaceLocator()
					pm.matchTransform(posLoc, primaryFkControls[j].node, pos = True, rot = True, scl = True)
					
					
					targetModGrpA = mnsUtils.createOffsetGroup(primaryFkControls[j])
					targetModGrpB = mnsUtils.createOffsetGroup(primaryFkControls[j])
					
					pm.matchTransform(targetModGrpA.node, primaryFkControls[n].node, pos = True, rot = True, scl = False)
					pm.matchTransform(primaryFkControls[j].node, posLoc, pos = True, rot = True, scl = True)
					pm.delete(posLoc)
					primaryFkControls[n].node.t >> targetModGrpB.node.t
					primaryFkControls[n].node.r >> targetModGrpB.node.r
					primaryFkControls[n].node.s >> targetModGrpB.node.s
					targetModGrpC = mnsUtils.createOffsetGroup(primaryFkControls[j])
					
		#createPivotSwitchers
		dictEnum = {"base": baseIkCtrl, "tip": tipIkCtrl};
		for embedIKControlKey in dictEnum.keys():
			arrayToEnum = primaryFkControls
			if embedIKControlKey == "tip": arrayToEnum = primaryFkControls[::-1]
			
			choiceInputCollect = []
			for k, FKControl in enumerate(arrayToEnum):
				pivotPos = mnsUtils.createNodeReturnNameStd(side =  rootGuide.side, body = rootGuide.body + embedIKControlKey.capitalize() + "Pivot" + mnsUtils.convertIntToAlpha(k), alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)
				pm.parent(pivotPos.node, dictEnum[embedIKControlKey].node.getParent())
				pm.delete(pm.parentConstraint(FKControl.node, pivotPos.node))
				choiceInputCollect.append(pivotPos.node.t)
			
			pivotSelectorAttr = mnsUtils.addAttrToObj([dictEnum[embedIKControlKey].node], type = "int", value = 0, name = "pivotSelector", replace = True, min = 0, max = len(primaryFkControls) - 1)[0]
			choiceNode = mnsNodes.choiceNode(choiceInputCollect, dictEnum[embedIKControlKey].node.rotatePivot)
			pivotSelectorAttr >> choiceNode.node.selector


		midIKTweakCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = "IkTweaker",
											controlShape = "doubleArrow",
											scale = modScale * 1, 
											blkCtrlTypeID = 1,
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = midIKCtrl.node,
											createOffsetGrp = True,
											createSpaceSwitchGroup = False,
											parentNode = midIKCtrl,
											symmetryType = symmetryType,
											doMirror = False,
											isFacial = MnsBuildModule.isFacial
											)
		builtCtrls.append(midIKTweakCtrl)
		mnsUtils.lockAndHideTransforms(midIKTweakCtrl.node, ty = False, ry = False, sy = False, lock = True)

		#attrs
		embeddedPocNode = embeddedPocNode["node"].node
		
		mnsUtils.addAttrToObj([baseIkCtrl.node], type = "enum", value = ["______"], name = "chainTweaks", replace = True, locked = True)
		#uScale
		uScaleAttr = mnsUtils.addAttrToObj([baseIkCtrl.node], type = "float", value = 1.0, name = "pullDown", replace = True, min = 0.01, max = 1.0)[0]
		uScaleAttr >> embeddedPocNode.uScale
		#divider
		mnsUtils.addAttrToObj([tipIkCtrl.node], type = "enum", value = ["______"], name = "chainTweaks", replace = True, locked = True)
		#uScaleInvr
		uScaleInvAttr = mnsUtils.addAttrToObj([tipIkCtrl.node], type = "float", value = 1.0, name = "pullUp", replace = True, min = 0.01, max = 1.0)[0]
		uScaleInvAttr >> embeddedPocNode.uScaleInverse

		#uScaleMid
		midIKTweakCtrl.node.sy >> embeddedPocNode.uScaleMid

		#uScaleMidInverse
		mult = 1.0 / (embeddedPocNode.curveLength.get() / 2.0)
		mnsNodes.mdlNode(midIKTweakCtrl.node.ty, mult, embeddedPocNode.uScaleMidInverse, side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body, alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id)

		#squeezeAim
		mdlNode = mnsNodes.mdlNode(midIKTweakCtrl.node.ry, -1.0, embeddedPocNode.squeezeAim)

		#inputCurve = embeddedIKBtc["node"].node.attr("outCurve")
		#inputUpCurve = embeddedIKBtc["node"].node.attr("outOffsetCurve")

		return builtCtrls

	def getInterpJointsState():
		primBtcNode, inputCurve, inputUpCurve, interpJoints = None, None, None, False

		#Make sure interpolationJoints are requested, if so, continue
		status, value = mnsUtils.validateAttrAndGet(rootGuide, "doInterpolationJoints", False)
		if status and value: 
			status, value = mnsUtils.validateAttrAndGet(rootGuide, "interpolationJoints", 0)
			if status and value >= len(allGuides):
				relatedRootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(rootGuide))
				outConnections = [c for c in relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True) if rootGuide.body in c.nodeName()]
				if outConnections:
					outConnection = False
					for con in outConnections: 
						if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
							outConnection = con
							break

					if type(outConnection) == pm.nodetypes.MnsBuildTransformsCurve: 
						primBtcNode = outConnection
						inputCurve = primBtcNode.attr("outCurve")
						inputUpCurve = primBtcNode.attr("outOffsetCurve")
						interpJoints = True
		return primBtcNode, inputCurve, inputUpCurve, interpJoints

	def getPocn():
		psocn = None
		if interpJoints:
			interpLocsArray = blkUtils.getModuleInterpJoints(rootGuide)
			if interpLocsArray:
				iLoc = interpLocsArray[0]
				inConnections = iLoc.node.t.listConnections(s = True, d = False)
				if inConnections:
					inCon = inConnections[0]
					if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
						psocn = inCon
		return psocn

	def createIKSecondaries():
		#attributes gather
		status, IKControlShape = mnsUtils.validateAttrAndGet(rootGuide, "IKControlShape", "flatDiamond")
		status, secondaryCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "secondaryCurveDegree", 3)
		status, secondaryCurveMode = mnsUtils.validateAttrAndGet(rootGuide, "secondaryCurveMode", 0)
		status, secondaryInterpolaion = mnsUtils.validateAttrAndGet(rootGuide, "secondaryInterpolaion", 0)
		status, doIKSpring = mnsUtils.validateAttrAndGet(rootGuide, "doIKSpring", 0)
		status, IKChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "IKChannelControl", 0)
		if status: IKChannelControl = mnsUtils.splitEnumAttrToChannelControlList("IKChannelControl", rootGuide.node)

		##ik controls group
		ikControlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "IKControls", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)

		ikOffsetGrps = []
		ikControls = []
		for j in range(numIkControls):
			ctrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = "Ik",
											controlShape = IKControlShape, 
											blkCtrlTypeID = 1, 
											scale = modScale * 0.8, 
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											createOffsetGrp = True,
											createSpaceSwitchGroup = False,
											parentNode = ikControlsGrp,
											symmetryType = symmetryType,
											doMirror = True,
											chennelControl = IKChannelControl,
											isFacial = MnsBuildModule.isFacial
											)

			ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl)
			ikOffsetGrps.append(ctrlOffset)
			ikControls.append(ctrl)

			if psocn:
				positionAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = (1.0 / float(numIkControls - 1)) * j, name = "position", replace = True, min = 0.0, max = 1.0, locked = True, cb = False, kayable = False)[0]
				falloffAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = 1.0, name = "falloff", replace = True, min = 0.01)[0]
				
				positionAttr >> psocn.customPosition[j].uPosition
				falloffAttr >> psocn.customPosition[j].falloff
				ctrl.node.ry >> psocn.customPosition[j].twist
				ctrl.node.rz >> psocn.customPosition[j].tertiaryRotation
				ctrl.node.rx >> psocn.customPosition[j].aimRotation
				ctrl.node.sy >> psocn.customPosition[j].scaleAim
				ctrl.node.sz >> psocn.customPosition[j].scaleUp
				ctrl.node.sx >> psocn.customPosition[j].tertiaryScale

				psocn.customPositionOut[j].cusTranslate >> ctrlOffset.node.t
				psocn.customPositionOut[j].cusRotate >> ctrlOffset.node.r

		status, primaryCurveDegree = mnsUtils.validateAttrAndGet(rootGuide, "primaryCurveDegree", 3)
		status, primaryCurveMode = mnsUtils.validateAttrAndGet(rootGuide, "primaryCurveMode", 0)
		status, primaryInterpolaion = mnsUtils.validateAttrAndGet(rootGuide, "primaryInterpolaion", 0)
		status, isolateSecPolesRotation = mnsUtils.validateAttrAndGet(rootGuide, "isolateSecPolesRotation", False)
		status, isolatePolesRotation = mnsUtils.validateAttrAndGet(rootGuide, "isolatePolesRotation", False)

		#pocn with built ctrls
		secondariesPocn = mnsNodes.mnsPointsOnCurveNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body, 
								inputCurve = primBtcNode.outCurve,
								inputUpCurve = primBtcNode.outOffsetCurve,
								buildOutputs = False,
								buildMode = primaryCurveMode,
								aimAxis = 1,
								upAxis = 0,
								numOutputs = numIkControls,
								transforms = ikOffsetGrps,
								isolatePolesRotation = isolateSecPolesRotation,
								baseAlternateWorldMatrix = primaryFkControls[0].node.worldMatrix[0],
								tipAlternateWorldMatrix = primaryFkControls[-1].node.worldMatrix[0]
								)
		secondariesPocn = secondariesPocn["node"].node

		secBtcNode = mnsNodes.mnsBuildTransformsCurveNode(side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body, 
											transforms = ikControls, 
											deleteCurveObjects = True, 
											tangentDirection = 1, 
											buildOffsetCurve = True,
											buildMode = secondaryInterpolaion,
											degree = secondaryCurveDegree,
											offsetX = offsetX,
											offsetY = offsetY,
											offsetZ = offsetZ)
		
		inputCurve = secBtcNode["node"].node.attr("outCurve")
		inputUpCurve = secBtcNode["node"].node.attr("outOffsetCurve")

		if isolatePolesRotation:
			ikControls[0].node.worldMatrix[0] >> psocn.baseAlternateWorldMatrix
			ikControls[-1].node.worldMatrix[0] >> psocn.tipAlternateWorldMatrix

		if doIKSpring:
			springCurveNode = mnsNodes.mnsSpringCurveNode(side = rootGuide.side, 
																alpha = rootGuide.alpha, 
																id = rootGuide.id, 
																body = rootGuide.body, 
																deleteCurveObjects = True,
																inputCurve = primBtcNode["node"].node.outCurve,
																inputUpCurve = primBtcNode["node"].node.outOffsetCurve,
																attributeHost = ikControls[0].node)
			blkUtils.connectIfNotConnected(springCurveNode["node"].node.outCurve, secondariesPocn.curve)
			blkUtils.connectIfNotConnected(springCurveNode["node"].node.outOffsetCurve, secondariesPocn.upCurve)

		return ikControls, inputCurve, inputUpCurve, secondariesPocn

	def createVarFk(inputCurve, inputUpCurve):
		######################################
		############ varFK layer #############
		######################################

		status, numVarFKControls = mnsUtils.validateAttrAndGet(rootGuide, "numVarFKControls", 2)


		#attributes gather
		status, varFKControlShape = mnsUtils.validateAttrAndGet(rootGuide, "varFKControlShape", "lightSphere")
		status, varFKInterpolaion = mnsUtils.validateAttrAndGet(rootGuide, "varFKInterpolaion", 0)
		status, defaultFalloff = mnsUtils.validateAttrAndGet(rootGuide, "defaultFalloff", 0.1)
		status, varFKSubsteps = mnsUtils.validateAttrAndGet(rootGuide, "varFKSubsteps", 0)
		status, varFKDegree = mnsUtils.validateAttrAndGet(rootGuide, "varFKDegree", 3)
		status, doVarFKSpring = mnsUtils.validateAttrAndGet(rootGuide, "doVarFKSpring", 0)

		status, varFKChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "varFKChannelControl", 0)
		if status: varFKChannelControl = mnsUtils.splitEnumAttrToChannelControlList("varFKChannelControl", rootGuide.node)

		##var FK controls group
		varFkControlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "VarFkControls", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)

		curveVarCtrls = []
		curveVarOffsets = []

		#ctrl create loop
		for j in range(numVarFKControls):
			ctrl = blkCtrlShps.ctrlCreate(
						controlShape = varFKControlShape,
						createBlkClassID = True, 
						createBlkCtrlTypeID = True, 
						blkCtrlTypeID = 1, 
						scale = modScale * 0.8, 
						alongAxis = 1, 
						side = MnsBuildModule.rootGuide.side, 
						body = MnsBuildModule.rootGuide.body + "VarFk", 
						alpha = MnsBuildModule.rootGuide.alpha, 
						id = MnsBuildModule.rootGuide.id,
						color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
						createOffsetGrp = True,
						parentNode = varFkControlsGrp,
						symmetryType = 0,
						doMirror = False,
						chennelControl = varFKChannelControl,
						isFacial = MnsBuildModule.isFacial
						)
			ctrlsCollect.append(ctrl)
			curveVarCtrls.append(ctrl)

			curveVarMirGrp = blkUtils.getOffsetGrpForCtrl(ctrl, type = "mirrorScaleGroup")
			if curveVarMirGrp:curveVarMirGrp.node.sy.set(1)
			
			curveVarOffset = blkUtils.getOffsetGrpForCtrl(ctrl)
			curveVarOffsets.append(curveVarOffset)
			mnsNodes.mnsMatrixConstraintNode(sources = [primaryFkControls[0].node], targets = [curveVarOffset.node], connectRotate = False, connectTranslate = False, connectScale = True, maintainOffset = True)

		#varFKNode
		curveVariableNode = mnsNodes.mnsCurveVariableNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body, 
								inputCurve = inputCurve,
								inputUpCurve = inputUpCurve,
								buildMode = varFKInterpolaion,
								defaultFalloff = defaultFalloff,
								degree = varFKDegree,
								substeps = varFKSubsteps,
								aimAxis = 1,
								upAxis = 0,
								offsetX = offsetX,
								offsetY = offsetY,
								offsetZ = offsetZ,
								inTransforms = curveVarCtrls,
								outOffsetTransforms = curveVarOffsets,
								deleteCurveObjects = True
								)

		#varFK attributes
		host = curveVarCtrls[0]
		cvNode = curveVariableNode["node"].node
		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "curveVariableCahin", replace = True)
		
		substeps = mnsUtils.addAttrToObj([host], type = "int", value = cvNode.substeps.get(), name = "substeps", replace = True, min = 0.0)[0]
		substeps >> cvNode.substeps

		uScale = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "uScale", replace = True, min = 0.0)[0]
		uScale >> cvNode.uScale

		uOffset = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "uOffset", replace = True)[0]
		uOffset >> cvNode.uOffset

		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "sine", replace = True)
		startPos = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "startPos", replace = True, min = 0.0, max = 1.0)[0]
		startPos >> cvNode.startPos

		startAmp = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "startAmp", replace = True, min = 0.0, max = 1.0)[0]
		startAmp >> cvNode.startAmp

		endAmp = mnsUtils.addAttrToObj([host], type = "float", value = 1.0, name = "startAmp", replace = True, min = 0.0, max = 1.0)[0]
		endAmp >> cvNode.endAmp

		frequency = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "frequency", replace = True)[0]
		frequency >> cvNode.frequency

		phase = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = "phase", replace = True)[0]
		phase >> cvNode.phase

		for direction in ["Aim", "Up", "Tertiary"]:
			for action in ["amplitude", "frequency", "phase"]:
				attrName = action + direction
				addedAttr = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, name = attrName, replace = True)[0]
				addedAttr >> cvNode.attr(attrName)

		#varFK spring
		if doVarFKSpring:
			springCurveNode = mnsNodes.mnsSpringCurveNode(side = rootGuide.side, 
																alpha = rootGuide.alpha, 
																id = rootGuide.id, 
																body = rootGuide.body, 
																deleteCurveObjects = True,
																inputCurve = inputCurve,
																inputUpCurve = inputUpCurve,
																attributeHost = curveVarCtrls[0].node)
			springCurveNode["node"].node.outCurve >> curveVariableNode["node"].node.attr("curve")
			springCurveNode["node"].node.outOffsetCurve >> curveVariableNode["node"].node.attr("upCurve")

		inputCurve = curveVariableNode["node"].node.attr("outCurve")
		inputUpCurve = curveVariableNode["node"].node.attr("outOffsetCurve")
		return inputCurve, inputUpCurve

	def createTweakControls():
		######################################
		########### tweakers layer ###########
		######################################

		status, numTweakers = mnsUtils.validateAttrAndGet(rootGuide, "numTweakers", 1)
		status, tweakControlShape = mnsUtils.validateAttrAndGet(rootGuide, "tweakControlShape", "flatDiamond")
		status, tweakersChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "tweakersChannelControl", 0)
		if status: tweakersChannelControl = mnsUtils.splitEnumAttrToChannelControlList("tweakersChannelControl", rootGuide.node)

		if interpJoints and inputCurve and inputUpCurve:
			interpLocs = blkUtils.getModuleInterpJoints(rootGuide)
			if interpLocs:
				iLoc = interpLocs[0]
				inConnections = iLoc.node.t.listConnections(s = True, d = False)
				if inConnections:
					inCon = inConnections[0]
					if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
						psocn = inCon

						##tweakers
						tweakersControlGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "Tweakers", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)

						#ctrl create loop
						for j in range(numTweakers):
							ctrl = blkCtrlShps.ctrlCreate(
										controlShape = tweakControlShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 2, 
										scale = modScale * 0.7, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "Tweaker", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										createOffsetGrp = True,
										parentNode = tweakersControlGrp,
										symmetryType = symmetryType,
										doMirror = True,
										chennelControl = tweakersChannelControl,
										isFacial = MnsBuildModule.isFacial
										)
							ctrlsCollect.append(ctrl)
							ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl)

							mnsUtils.addAttrToObj([ctrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
							positionAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = (1.0 / float(numTweakers - 1)) * j, name = "position", replace = True, min = 0.0, max = 1.0)[0]
							falloffAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = 1.0, name = "falloff", replace = True, min = 0.01)[0]
							
							tweakerIndex = j
							if secondariesPocn: 
								status, numIkControlsA = mnsUtils.validateAttrAndGet(rootGuide, "numIKControls", 0)
								tweakerIndex += numIkControlsA - 1

							positionAttr >> psocn.customPosition[tweakerIndex].uPosition
							falloffAttr >> psocn.customPosition[tweakerIndex].falloff
							ctrl.node.ry >> psocn.customPosition[tweakerIndex].twist
							ctrl.node.rz >> psocn.customPosition[tweakerIndex].tertiaryRotation
							ctrl.node.rx >> psocn.customPosition[tweakerIndex].aimRotation
							ctrl.node.sy >> psocn.customPosition[tweakerIndex].scaleAim
							ctrl.node.sz >> psocn.customPosition[tweakerIndex].scaleUp
							ctrl.node.sx >> psocn.customPosition[tweakerIndex].tertiaryScale

							psocn.customPositionOut[tweakerIndex].cusTranslate >> ctrlOffset.node.t
							psocn.customPositionOut[tweakerIndex].cusRotate >> ctrlOffset.node.r

							decMat = mnsNodes.decomposeMatrixNode(primaryFkControls[0].node.worldMatrix[0], None,None,None)
							decMat.node.outputScaleX >> ctrlOffset.node.sx
							decMat.node.outputScaleX >> ctrlOffset.node.sy
							decMat.node.outputScaleX >> ctrlOffset.node.sz

	def springInterpJoints(inputCurve, inputUpCurve):
		######################################
		########## interpJnt Spring ##########
		######################################

		springCurveNode = mnsNodes.mnsSpringCurveNode(side = rootGuide.side, 
															alpha = rootGuide.alpha, 
															id = rootGuide.id, 
															body = rootGuide.body, 
															deleteCurveObjects = True,
															inputCurve = inputCurve,
															inputUpCurve = inputUpCurve,
															attributeHost = attrHost.node)
		inputCurve = springCurveNode["node"].node.attr("outCurve")
		inputUpCurve = springCurveNode["node"].node.attr("outOffsetCurve")
		return inputCurve, inputUpCurve

	########### local library imports ###########
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core.prefixSuffix import MnsNameStd, mnsTypeDict

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
	status, offsetX = mnsUtils.validateAttrAndGet(rootGuide, "offsetX", 0.0)
	status, offsetY = mnsUtils.validateAttrAndGet(rootGuide, "offsetY", 0.0)
	status, offsetZ = mnsUtils.validateAttrAndGet(rootGuide, "offsetZ", 20.0)
	status, doPrimariesSpaceSwitch = mnsUtils.validateAttrAndGet(rootGuide, "doPrimariesSpaceSwitch", False)
	status, doEmbeddedIK = mnsUtils.validateAttrAndGet(rootGuide, "doEmbeddedIK", False)
	if doEmbeddedIK:
		doPrimariesSpaceSwitch = False

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	### Primary FK

	primaryFkControls, secondaryIKs = createPrimaryCtrls()
	ctrlsCollect += primaryFkControls
	if secondaryIKs: ctrlsCollect += secondaryIKs

	primBtcNode, inputCurve, inputUpCurve, interpJoints = getInterpJointsState()

	### Embedded IK
	if doEmbeddedIK:
		builtControls = createEmbeddedIK()
		ctrlsCollect += builtControls

	#now apply FK channel control
	status, FKChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "FKChannelControl", {})
	if status: 
		FKChannelControl = mnsUtils.splitEnumAttrToChannelControlList("FKChannelControl", rootGuide.node)
		for primFKCtrl in primaryFkControls:
			mnsUtils.applyChennelControlAttributesToTransform(primFKCtrl.node, FKChannelControl)

	status, doFKSeconderyIK = mnsUtils.validateAttrAndGet(rootGuide, "doFKSeconderyIK", False)
	if doFKSeconderyIK: primaryFkControls = secondaryIKs

	secondariesPocn = None

	if inputCurve and inputUpCurve:
		psocn = getPocn()

		status, primaryCurveMode = mnsUtils.validateAttrAndGet(rootGuide, "primaryCurveMode", 0)
		psocn.mode.set(primaryCurveMode)

		#secondaries
		status, doSecondaryIKCtrls = mnsUtils.validateAttrAndGet(rootGuide, "doSecondaryIKCtrls", False)
		if doSecondaryIKCtrls: 
			status, numIkControls = mnsUtils.validateAttrAndGet(rootGuide, "numIKControls", 0)
			if status and numIkControls >= len(allGuides):
				ikControls, inputCurve, inputUpCurve, secondariesPocn = createIKSecondaries()
				ctrlsCollect += ikControls
		#varFK
		status, value = mnsUtils.validateAttrAndGet(rootGuide, "doVariableFK", False)
		if status and value: inputCurve, inputUpCurve = createVarFk(inputCurve, inputUpCurve)

		#tweakers layer
		status, value = mnsUtils.validateAttrAndGet(rootGuide, "doTweakControls", False)
		if status and value: createTweakControls()

		#inter joints spring
		status, doIntepJntsSpring = mnsUtils.validateAttrAndGet(rootGuide, "doIntepJntsSpring", 0)
		if doIntepJntsSpring: inputCurve, inputUpCurve = springInterpJoints(inputCurve, inputUpCurve)
			

		##########################
		#### poc connections #####
		##########################

		status, scaleMode = mnsUtils.validateAttrAndGet(rootGuide, "scaleMode", 2)
		status, squashMode = mnsUtils.validateAttrAndGet(rootGuide, "squashMode", 0)

		host = attrHost.node

		#divider
		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "SquashSettings", replace = True, locked = True)

		#squashMode
		squashMode = mnsUtils.addAttrToObj([host], type = "enum", value = ["squashStretch", "squash", "stretch", "unifom", "none"], enumDefault = squashMode, name = "squashMode", replace = True)[0]
		squashMode >> psocn.squashMode
		if secondariesPocn: squashMode >> secondariesPocn.squashMode

		#scaleMode
		scaleMode = mnsUtils.addAttrToObj([host], type = "enum", value = ["curveLengthIsDifferentThenCreation", "curveLengthChanges", "always"], enumDefault = scaleMode, name = "squashWhen", replace = True)[0]
		scaleMode >> psocn.scaleMode
		if secondariesPocn: scaleMode >> secondariesPocn.scaleMode

		#scaleMin
		scaleMin = mnsUtils.addAttrToObj([host], type = "float", value = 0.8, name = "scaleMin", replace = True, min = 0.001, max = 1.0)[0]
		scaleMin >> psocn.scaleMin
		if secondariesPocn: scaleMin >> secondariesPocn.scaleMin

		#scaleMax
		scaleMax = mnsUtils.addAttrToObj([host], type = "float", value = 1.2, name = "scaleMax", replace = True, min = 1.0)[0]
		scaleMax >> psocn.scaleMax
		if secondariesPocn: scaleMax >> secondariesPocn.scaleMax

		#squashFactor
		squashFactor = mnsUtils.addAttrToObj([host], type = "float", value = 1.1, name = "squashFactor", replace = True)[0]
		squashFactor >> psocn.squashFactor
		if secondariesPocn: squashFactor >> secondariesPocn.squashFactor

		#squashPos
		squashPos = mnsUtils.addAttrToObj([host], type = "float", value = 0.5, name = "squashPos", replace = True, min = 0.0, max = 1.0)[0]
		squashPos >> psocn.squashPos
		if secondariesPocn: squashPos >> secondariesPocn.squashPos


	######################################
	########## Tranfer Authority #########
	######################################

	k = 0
	primJnts = []
	for guide in allGuides:
		relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(guide))	
		if relatedJnt:
			blkUtils.transferAuthorityToCtrl(relatedJnt, primaryFkControls[k])
			primJnts.append(relatedJnt)
		k += 1

	#transfer pocn authority
	if interpJoints and inputCurve and inputUpCurve:
		interpLocs = blkUtils.getModuleInterpJoints(rootGuide)
		if interpLocs:
			iLoc = interpLocs[0]
			inConnections = iLoc.node.t.listConnections(s = True, d = False)
			if inConnections:
				inCon = inConnections[0]
				if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
					psocn = inCon
					blkUtils.connectIfNotConnected(inputCurve, psocn.curve)
					blkUtils.connectIfNotConnected(inputUpCurve, psocn.upCurve)
					
					blkUtils.getGlobalScaleAttrFromTransform(primaryFkControls[0]) >> psocn.globalScale

					psocn.doScale.set(1)
					psocn.resetScale.set(1)

					if primJnts:
						for jnt in primJnts:
							jnt.node.scale.disconnect()

					if secondariesPocn: blkUtils.getGlobalScaleAttrFromTransform(primaryFkControls[0]) >> secondariesPocn.globalScale

	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, ctrlsCollect[0], ctrlsCollect[0]

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
		if rootGuide.node.hasAttr("doInterpolationJoints"):
			if rootGuide.node.attr("doInterpolationJoints").get():
				if rootGuide.node.attr("interpolationJoints").get() >= len(guides):

					#attributes gather
					curveModeAttrName = "primaryCurveMode"
					curveDegreeAttrName = "primaryCurveDegree"
					curveInterpolationAttrName = "primaryInterpolaion"

					status, value = mnsUtils.validateAttrAndGet(rootGuide, "doSecondaryIKCtrls", False)
					if status and value:
						status, numIkControls = mnsUtils.validateAttrAndGet(rootGuide, "numIKControls", 0)
						if status and numIkControls >= len(guides):
							curveModeAttrName = "secondaryCurveMode"
							curveDegreeAttrName = "secondaryCurveDegree"
							curveInterpolationAttrName = "secondaryInterpolaion"

					status, doVariableFK = mnsUtils.validateAttrAndGet(rootGuide, "doVariableFK", False)
					if status and doVariableFK:
						#this means variable FK layer is selected, so the primary curve mode must be switched to uniform
						status, primaryCurveMode = mnsUtils.validateAttrAndGet(rootGuide, "primaryCurveMode", False)
						if status and primaryCurveMode == 0:
							mnsUtils.setAttr(rootGuide.node.primaryCurveMode, 1)

					status, offsetX = mnsUtils.validateAttrAndGet(rootGuide, "offsetX", 10.0)
					status, offsetY = mnsUtils.validateAttrAndGet(rootGuide, "offsetY", 0.0)
					status, offsetZ = mnsUtils.validateAttrAndGet(rootGuide, "offsetZ", 0.0)

					status, scaleMode = mnsUtils.validateAttrAndGet(rootGuide, "scaleMode", 2)
					status, squashMode = mnsUtils.validateAttrAndGet(rootGuide, "squashMode", 0)

					status, curveDegree = mnsUtils.validateAttrAndGet(rootGuide, curveDegreeAttrName, 3)
					status, curveMode = mnsUtils.validateAttrAndGet(rootGuide, curveModeAttrName, 0)
					curveMode = min(curveMode, 1)
					status, curveInterpolation = mnsUtils.validateAttrAndGet(rootGuide, curveInterpolationAttrName, 0)

					if not softMod:
						#build structure
						btcNode = mnsNodes.mnsBuildTransformsCurveNode(
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body, 
												transforms = transforms, 
												deleteCurveObjects = True, 
												tangentDirection = 1, 
												buildOffsetCurve = True,
												buildMode = curveInterpolation,
												degree = curveDegree,
												offsetX = offsetX,
												offsetY = offsetY,
												offsetZ = offsetZ)
						blkUtils.connectSlaveToDeleteMaster(btcNode["node"], rootGuide)

						pocn = mnsNodes.mnsPointsOnCurveNode(
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
												inputCurve = btcNode["node"].node.outCurve,
												inputUpCurve = btcNode["node"].node.outOffsetCurve,
												buildOutputs = True,
												buildType = 4, #interpJointsType
												buildMode = curveMode,
												doScale = False,
												aimAxis = 1,
												upAxis = 0,
												numOutputs = rootGuide.node.attr("interpolationJoints").get()
												)
						pocn["node"].node.scaleMode.set(scaleMode)
						pocn["node"].node.squashMode.set(squashMode)
						
						status, isolatePolesRotation = mnsUtils.validateAttrAndGet(rootGuide, "isolatePolesRotation", False)
						if isolatePolesRotation:
							pocn["node"].node.excludePolesRotation.set(True)
							transforms[0].worldMatrix[0] >> pocn["node"].node.baseAlternateWorldMatrix
							transforms[-1].worldMatrix[0] >> pocn["node"].node.tipAlternateWorldMatrix

						return pocn["samples"]
					else:
						#find btcNode and poc node
						primBtcNode, primPocNode = None, None
						relatedRootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(rootGuide))
						outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
						if outConnections:
							for con in outConnections: 
								if type(con) == pm.nodetypes.MnsBuildTransformsCurve:
									primBtcNode = con
									outConnections = primBtcNode.outCurve.listConnections(s = False, d = True)
									if outConnections:
										for con in outConnections: 
											if type(con) == pm.nodetypes.MnsPointsOnCurve:
												primPocNode = con
									break

						#adjust the nodes
						status, doVariableFK = mnsUtils.validateAttrAndGet(rootGuide, "doVariableFK", False)
						if doVariableFK and curveMode == 0: curveMode = 1

						if primBtcNode and primPocNode:
							primBtcNode.buildMode.set(curveInterpolation)
							primBtcNode.degree.set(curveDegree)
							primBtcNode.offsetX.set(offsetX)
							primBtcNode.offsetY.set(offsetY)
							primBtcNode.offsetZ.set(offsetZ)
							primPocNode.mode.set(curveMode)

							status, isolatePolesRotation = mnsUtils.validateAttrAndGet(rootGuide, "isolatePolesRotation", False)
							if isolatePolesRotation:
								primPocNode.excludePolesRotation.set(True)
								transforms[0].worldMatrix[0] >> primPocNode.baseAlternateWorldMatrix
								transforms[-1].worldMatrix[0] >> primPocNode.tipAlternateWorldMatrix
							else:
								primPocNode.excludePolesRotation.set(False)
								primPocNode.baseAlternateWorldMatrix.disconnect()
								primPocNode.tipAlternateWorldMatrix.disconnect()

def jointStructureSoftMod(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	kwargs.update({"softMod": True})
	jointStructure(mansur, guides, mnsBuildModule, **kwargs)

def deconstruct(mansur, MnsBuildModule, **kwargs):
	"""deconstruct method implementation for FKChain. 
	Transfer interJoints control back to the main joints.
	"""

	from mansur.block.core import blockUtility as blkUtils
	from mansur.core import utility as mnsUtils

	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		if rootGuide.node.hasAttr("jntSlave"):
			relatedRootJnt = mnsUtils.validateNameStd(rootGuide.node.jntSlave.get())
			if relatedRootJnt:
				outConnections = relatedRootJnt.node.worldMatrix[0].listConnections(s = False, d = True)
				if outConnections:
					for outConnection in outConnections:
						if type(outConnection) == pm.nodetypes.MnsBuildTransformsCurve: 
							btcNode = outConnection

							if relatedRootJnt.body in mnsUtils.validateNameStd(btcNode).body:
								interpLocs = blkUtils.getModuleInterpJoints(rootGuide)
								iLoc = interpLocs[0]
								inConnections = iLoc.node.t.listConnections(s = True, d = False)
								if inConnections:
									inCon = inConnections[0]
									if type(inCon) == pm.nodetypes.MnsPointsOnCurve:
										psocn = inCon
										blkUtils.connectIfNotConnected(btcNode.outCurve, psocn.curve)
										blkUtils.connectIfNotConnected(btcNode.outOffsetCurve, psocn.upCurve)

										outCons = btcNode.outCurve.listConnections(s = False, d = True)
										for outNode in outCons:
											if type(outNode) == pm.nodetypes.MnsSpringCurve:
												pm.delete(outNode)

										#attributes gather
										curveModeAttrName = "primaryCurveMode"

										status, value = mnsUtils.validateAttrAndGet(rootGuide, "doSecondaryIKCtrls", False)
										if status and value:
											status, numIkControls = mnsUtils.validateAttrAndGet(rootGuide, "numIKControls", 0)
											if status and numIkControls >= len(MnsBuildModule.guideControls):
												curveModeAttrName = "secondaryCurveMode"

										status, curveMode = mnsUtils.validateAttrAndGet(rootGuide, curveModeAttrName, 0)
										curveMode = min(curveMode, 1)
										psocn.mode.disconnect()
										psocn.mode.set(curveMode)

										psocn.resetScale.set(1)
										psocn.doScale.set(0)

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core import prefixSuffix as mnsPS

	rootGuide = MnsBuildModule.rootGuide
	status, doCurlAttrs = mnsUtils.validateAttrAndGet(rootGuide, "doCurlAttrs", True)

	if doCurlAttrs and MnsBuildModule.controls:
		primaryControls = mnsUtils.sortNameStdArrayByID(MnsBuildModule.controls["primaries"])

		#gather host
		attrHost = primaryControls[0]

		#divider
		mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "curls", replace = True, locked = True)

		#main curls
		curlXAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "curlX", replace = True)[0]
		curlYAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "curlY", replace = True)[0]
		curlZAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "curlZ", replace = True)[0]

		transformsToCurl = []
		primCtrlsCollect = []
		for ctrl in primaryControls:
			primCtrlsCollect.append(mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp", bodySuffix = "IsoCurl"))
		transformsToCurl = mnsUtils.sortNameStdArrayByID(primCtrlsCollect)

		for tranToCurl in transformsToCurl:
			curlXAttr >> tranToCurl.node.rx
			curlYAttr >> tranToCurl.node.ry
			curlZAttr >> tranToCurl.node.rz