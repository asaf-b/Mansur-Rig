"""Author: Asaf Ben-Zur
Best used for: Foot
This Module was created for a foot setup mainly.
Some of it's main features are FK controls, BK (backward kinematics) controls, Roll control, Bank Controls, Heel and Tip controls, Dynamic pivot control.
The best application for this module is placing it under a limb module, which will result in a connected (standard) behaviour.
"""



from maya import cmds
import pymel.core as pm


def createIKMuteForCtrl(mansur, ctrl, ikFkAttr, **kwargs):
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	reverseValues = kwargs.get("reverseValues", None)

	if ctrl and ikFkAttr:
		ctrlModGrp = mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp")

		invMatNode = mnsNodes.inverseMatrixNode(ctrl.node.matrix, 
												None,
												side = ctrl.side, 
												body = ctrl.body + "ikMute", 
												alpha = ctrl.alpha, 
												id = ctrl.id)

		decomposeMatNode = mnsNodes.decomposeMatrixNode(invMatNode.node.outputMatrix, 
												None,
												None,
												None,
												side = ctrl.side, 
												body = ctrl.body + "ikMute", 
												alpha = ctrl.alpha, 
												id = ctrl.id)
		
		mdNodeB = mnsNodes.mdNode(decomposeMatNode.node.outputRotate, 
									[ikFkAttr, ikFkAttr, ikFkAttr],
									ctrlModGrp.node.r,
									side = ctrl.side, 
									body = ctrl.body + "ikMute", 
									alpha = ctrl.alpha, 
									id = ctrl.id)

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
	fkIkBlendAttr = mnsUtils.addAttrToObj([attrHost.node], type = "float", value = 0.0, name = "ikFkBlend", replace = True, max = 1.0, min = 0.0)[0]
	blendAttrHolder = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "blendAttrHolder", value= "", replace = True)[0]
	attrHost.node.message >> blendAttrHolder

	revNode = mnsNodes.reverseNode([fkIkBlendAttr,0,0], 
								None,
								side = attrHost.side, 
								body = attrHost.body + "IkFk", 
								alpha = attrHost.alpha, 
								id = attrHost.id)
	fkVisAttr = fkIkBlendAttr
	ikVisAttr = revNode.node.outputX

	##collect costum guides
	customGuides = MnsBuildModule.cGuideControls
	heelPivGuide, toePivGuide, innerPivGuide, outerPivGuide = None, None, None, None		

	status, FKcontrolShape = mnsUtils.validateAttrAndGet(rootGuide, "FKControlShape", "cube")
	FKChannelControlList = mnsUtils.splitEnumAttrToChannelControlList("FKChannelControl", MnsBuildModule.rootGuide.node)
	
	status, BKcontrolShape = mnsUtils.validateAttrAndGet(rootGuide, "BKControlShape", "diamond")
	BKChannelControlList = mnsUtils.splitEnumAttrToChannelControlList("BKChannelControl", MnsBuildModule.rootGuide.node)

	#global declares
	secondaryCtrls = []
	pureTops = []
	FKControls = []
	BKControls = []
	FKTop = None
	ikTarAttr, bkTopAttr, FKRootCtrl = None, None, None

	##################################################################################
	############# FK control #########################################################

	for n, guide in enumerate(allGuides):
		parNode = animGrp
		if FKControls: parNode = FKControls[-1]

		relatedFKJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(guide))	
		offsetRigMaster = relatedFKJnt
		offsetRigSlaveIsParent = False
		if n == 0: offsetRigSlaveIsParent = True

		#for each position exept the first one, create both FK and BK controls
		FKCtrl = blkCtrlShps.ctrlCreate(
									controlShape = FKcontrolShape,
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 0.4, 
									alongAxis = 1, 
									side = guide.side, 
									body = guide.body + "ToesFK", 
									alpha = guide.alpha, 
									id = guide.id,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = guide.node,
									parentNode = parNode,
									createSpaceSwitchGroup = False,
									createOffsetGrp = True,
									symmetryType = symmetryType,
									doMirror = True,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = offsetRigMaster,
									offsetRigSlaveIsParent = offsetRigSlaveIsParent)
		#apply channel control
		mnsUtils.applyChennelControlAttributesToTransform(FKCtrl.node, FKChannelControlList)

		#if first position, collect and record
		if not FKControls: 
			FKTop = blkUtils.getOffsetGrpForCtrl(FKCtrl)
			#pureTops.append(FKTop)
			ikTarAttr = mnsUtils.addAttrToObj([FKCtrl.node], type = "message", name = "newIKTarget", value= "", replace = True)[0]
			bkTopAttr = mnsUtils.addAttrToObj([FKCtrl.node], type = "message", name = "bkTop", value= "", replace = True)[0]
			FKRootCtrl = mnsUtils.addAttrToObj([FKCtrl.node], type = "message", name = "fkRootCtrl", value= "", replace = True)[0]
			FKCtrl.node.message >> FKRootCtrl
			for shape in FKCtrl.node.getShapes(): fkVisAttr >> shape.v

			#create IK-FK mute
			createIKMuteForCtrl(mansur, FKCtrl, revNode.node.outputX)

		#transfer authority
		blkUtils.transferAuthorityToCtrl(relatedFKJnt, FKCtrl)

		#collect
		FKControls.append(FKCtrl)

	BKTop = None
	##################################################################################
	############# custom pivots ######################################################

	status, bankControlShape = mnsUtils.validateAttrAndGet(rootGuide, "bankControlShape", "lightSphere")
	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("bankChannelControl", MnsBuildModule.rootGuide.node)

	#create ankle tweak
	ankleTweak = blkCtrlShps.ctrlCreate(parentNode = animStaticGrp,
										controlShape = "flatDiamond", 
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "AnkleTweak", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchPosition = rootGuide.node, 
										createOffsetGrp = True, 
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial,
										offsetRigMaster = relatedJnt)
	BKTop = blkUtils.getOffsetGrpForCtrl(ankleTweak)
	for shape in ankleTweak.node.getShapes(): ikVisAttr >> shape.v
	
	cusPivCtrls = []
	tipCtrl, heelCtrl, innerCtrl, outerCtrl = None, None, None, None
	for name in ["Heel", "Toe", "Inner", "Outer"]:
		cusGuide = None
		for guide in customGuides: 
			if name in guide.name: cusGuide = guide
		if guide:
			parNode = ankleTweak
			if cusPivCtrls: parNode = cusPivCtrls[-1]

			ctrl = blkCtrlShps.ctrlCreate(
										controlShape = bankControlShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 0.2, 
										alongAxis = 1, 
										side = MnsBuildModule.rootGuide.side, 
										body = cusGuide.body, 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = 1,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = cusGuide.node,
										parentNode = parNode,
										createSpaceSwitchGroup = False,
										createOffsetGrp = True,
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial
										)
			for shape in ctrl.node.getShapes(): ikVisAttr >> shape.v

			if name == "Toe": tipCtrl = ctrl
			if name == "Heel": heelCtrl = ctrl
			if name == "Inner": innerCtrl = ctrl
			if name == "Outer": outerCtrl = ctrl

			mnsUtils.applyChennelControlAttributesToTransform(ctrl.node, channelControlList)
			cusPivCtrls.append(ctrl)

	##################################################################################
	############# BK control #########################################################

	k = 0
	for FKCtrl in reversed(FKControls):
		if k < len(FKControls) - 1:
			#create mod grp
			FKModGrp = mnsUtils.createOffsetGroup(FKCtrl, type = "modifyGrp")

			BKParNode = animGrp
			if cusPivCtrls: BKParNode = cusPivCtrls[-1]
			if BKControls: BKParNode = BKControls[-1]

			#BK control
			BKCtrl = blkCtrlShps.ctrlCreate(
										controlShape = BKcontrolShape,
										createBlkClassID = True, 
										createBlkCtrlTypeID = True, 
										blkCtrlTypeID = 0, 
										scale = modScale * 0.4, 
										alongAxis = 1, 
										side =FKCtrl.side, 
										body = FKCtrl.body + "ToesBK", 
										alpha = FKCtrl.alpha, 
										id = FKCtrl.id,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = FKCtrl.node,
										parentNode = BKParNode,
										createSpaceSwitchGroup = False,
										createOffsetGrp = True,
										symmetryType = symmetryType,
										doMirror = True,
										isFacial = MnsBuildModule.isFacial
										)
			BKControls.append(BKCtrl)
			for shape in BKCtrl.node.getShapes(): ikVisAttr >> shape.v

			#apply channel control
			mnsUtils.applyChennelControlAttributesToTransform(BKCtrl.node, BKChannelControlList)


			#connect bk control rotation to FK control modGrp
			
			#createIKMuteForCtrl(mansur, BKCtrl, fkIkBlendAttr)
			invMatNode = mnsNodes.inverseMatrixNode(BKCtrl.node.matrix, 
													None,
													side = MnsBuildModule.rootGuide.side, 
													body = MnsBuildModule.rootGuide.body + "bk", 
													alpha = MnsBuildModule.rootGuide.alpha, 
													id = MnsBuildModule.rootGuide.id)
			decomposeMatNode = mnsNodes.decomposeMatrixNode(invMatNode.node.outputMatrix, 
													None,
													None,
													None,
													side = MnsBuildModule.rootGuide.side, 
													body = MnsBuildModule.rootGuide.body + "bk", 
													alpha = MnsBuildModule.rootGuide.alpha, 
													id = MnsBuildModule.rootGuide.id)

			
			mdNodeB = mnsNodes.mdNode(decomposeMatNode.node.outputRotate, 
									[revNode.node.outputX, revNode.node.outputX, revNode.node.outputX],
									FKModGrp.node.r,
									side = MnsBuildModule.rootGuide.side, 
									body = MnsBuildModule.rootGuide.body + "ikMute", 
									alpha = MnsBuildModule.rootGuide.alpha, 
									id = MnsBuildModule.rootGuide.id)

			if MnsBuildModule.rootGuide.side == "r" and False:
				mdNodeC = mnsNodes.mdNode(mdNodeB.node.output, 
										[-1.0, -1.0, 1.0],
										FKModGrp.node.r,
										side = MnsBuildModule.rootGuide.side, 
										body = MnsBuildModule.rootGuide.body + "ikMuteB", 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id)
			


		else:
			#create ikEffector
			custIkEffector = mnsUtils.createNodeReturnNameStd(side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "AltIkEffector", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
			pm.delete(pm.parentConstraint(FKCtrl.node, custIkEffector.node))
			pm.parent(custIkEffector.node, BKControls[-1].node)
			custIkEffector.node.v.set(False)
			custIkEffector.node.v.setLocked(True)
			mnsUtils.lockAndHideAllTransforms(custIkEffector.node, lock = True)
			custIkEffector.node.message >> ikTarAttr

		k += 1

	#reparent topFK
	if FKTop: pm.parent(FKTop.node, BKControls[-1].node)
	if BKTop: BKTop.node.message >> bkTopAttr


	##################################################################################
	############# Roll ctrl ##########################################################
	rollCtrl = None
	status, doRollCtrl = mnsUtils.validateAttrAndGet(rootGuide, "doRollCtrl", True)
	if doRollCtrl:
		status, rollCtrlShape = mnsUtils.validateAttrAndGet(rootGuide, "rollControlShape", "cylinder")
		status, rollDefaultMaxAngle = mnsUtils.validateAttrAndGet(rootGuide, "rollDefaultMaxAngle", 60.0)
		status, straightenDefaultAngle = mnsUtils.validateAttrAndGet(rootGuide, "straightenDefaultAngle", 130.0)

		#BK control
		rollCtrl = blkCtrlShps.ctrlCreate(
									controlShape = rollCtrlShape,
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 0.8, 
									alongAxis = 0, 
									side =rootGuide.side, 
									body = rootGuide.body + "Roll", 
									alpha = rootGuide.alpha, 
									id = rootGuide.id,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = FKControls[0].node,
									createSpaceSwitchGroup = False,
									createOffsetGrp = True,
									parentNode = animGrp,
									symmetryType = symmetryType,
									doMirror = True,
									isFacial = MnsBuildModule.isFacial
									)
		for shape in rollCtrl.node.getShapes(): ikVisAttr >> shape.v
		mnsUtils.lockAndHideTransforms(rollCtrl.node, lock = True, rx = False, ry = False)
		mnsUtils.addAttrToObj([rollCtrl.node], type = "enum", value = ["______"], name = "RollAttrs", replace = True)

		for cusPivCtrl in cusPivCtrls: mnsUtils.createOffsetGroup(cusPivCtrl, type = "modifyGrp")

		k = 0
		lastUnitConNode = None, None
		anglesAttrs = []
		for bkCtrl in BKControls[::-1]:
			clampNode = mnsNodes.clampNode([rollCtrl.node.rx, 0, 0], 
									None,
									None,
									None,
									side = bkCtrl.side, 
									body = bkCtrl.body, 
									alpha = bkCtrl.alpha, 
									id = bkCtrl.id)

			#get unitConversionNode
			unitConNode = clampNode.node.inputR.listConnections(s = True, d = False)[0]
			lastUnitConNode = unitConNode
			unitConNode.output >> clampNode.node.inputG
			unitConNode.output >> clampNode.node.inputB

			if k == 0:
				clampNode.node.minB.set(-360)

				if rootGuide.side == "r" and False:
					mdlNode = mnsNodes.mdlNode(clampNode.node.outputB, 
												-1.0,
												None,
												side = bkCtrl.side, 
												body = bkCtrl.body, 
												alpha = bkCtrl.alpha, 
												id = bkCtrl.id)
					mdlNode.node.output >> blkUtils.getOffsetGrpForCtrl(heelCtrl, type = "modifyGrp").node.rx
				else:
					clampNode.node.outputB >> blkUtils.getOffsetGrpForCtrl(heelCtrl, type = "modifyGrp").node.rx

			bkModGrp = mnsUtils.createOffsetGroup(bkCtrl, type = "modifyGrp")
			attrName = "maxAngle" + mnsUtils.convertIntToAlpha(k)
			maxAngleAttr = mnsUtils.addAttrToObj([rollCtrl.node], type = "float", value = rollDefaultMaxAngle, min = 0.0, name = attrName, replace = True)[0]
			maxAngleAttr >> clampNode.node.maxR

			attrName = "strightenAngle" + mnsUtils.convertIntToAlpha(k)
			strightenAngleAttr = mnsUtils.addAttrToObj([rollCtrl.node], type = "float", value = straightenDefaultAngle, min = 0.0, name = attrName, replace = True)[0]

			if rootGuide.side == "r" and False:
				mdlNode = mnsNodes.mdlNode(clampNode.node.outputR, 
											-1.0,
											bkModGrp.node.rx,
											side = bkCtrl.side, 
											body = bkCtrl.body, 
											alpha = bkCtrl.alpha, 
											id = bkCtrl.id)
			else:
				setRangeNode = mnsNodes.setRangeNode(maxIn = [0.0,0.0,0.0], 
													minIn = [1.0,0.0,0.0], 
													oldMax = [strightenAngleAttr, 0.0, 0.0], 
													oldMin = [maxAngleAttr, 0.0,0.0], 
													value = [rollCtrl.node.rx, None,None], 
													outValue = [None,None,None],
													side = bkCtrl.side, 
													body = bkCtrl.body, 
													alpha = bkCtrl.alpha, 
													id = bkCtrl.id)
				mnsNodes.mdlNode(setRangeNode.node.outValueX, 
											clampNode.node.outputR,
											bkModGrp.node.rx,
											side = bkCtrl.side, 
											body = bkCtrl.body, 
											alpha = bkCtrl.alpha, 
											id = bkCtrl.id)
				#clampNode.node.outputR >> bkModGrp.node.rx

			#add the modGrp matrix into the bk inverse calc
			previousInvMat = bkCtrl.node.matrix.listConnections(s = False, d = True)[0]
			mulMatrixNode = mnsNodes.multMatrixNode([bkCtrl.node.matrix,  bkModGrp.node.matrix],
									None,
									side = bkCtrl.side, 
									body = bkCtrl.body, 
									alpha = bkCtrl.alpha, 
									id = bkCtrl.id)
			
			mulMatrixNode.node.matrixSum >> previousInvMat.inputMatrix

			#if it isn't the fist bk control, connect last clamp node instead of the rotation and subtract
			if k > 0: 
				pmaNode = mnsNodes.pmaNode(anglesAttrs, None, None,
							None, None, None,
							side = bkCtrl.side, 
							body = bkCtrl.body, 
							alpha = bkCtrl.alpha, 
							id = bkCtrl.id)

				mdlNode = mnsNodes.mdlNode(pmaNode.node.output1D, 
									-1.0,
									None,
									side = bkCtrl.side, 
									body = bkCtrl.body, 
									alpha = bkCtrl.alpha, 
									id = bkCtrl.id)

				adlNode = mnsNodes.adlNode(mdlNode.node.output, 
											lastUnitConNode.output,
											None,
											side = bkCtrl.side, 
											body = bkCtrl.body, 
											alpha = bkCtrl.alpha, 
											id = bkCtrl.id)

				adlNode.node.output >> clampNode.node.inputR

			anglesAttrs.append(maxAngleAttr)
			k += 1


		pmaNode = mnsNodes.pmaNode(anglesAttrs, None, None,
									None, None, None,
									side = tipCtrl.side, 
									body = tipCtrl.body, 
									alpha = tipCtrl.alpha, 
									id = tipCtrl.id)

		mdlNode = mnsNodes.mdlNode(pmaNode.node.output1D, 
									-1.0,
									None,
									side = tipCtrl.side, 
									body = tipCtrl.body, 
									alpha = tipCtrl.alpha, 
									id = tipCtrl.id)

		adlNode = mnsNodes.adlNode(mdlNode.node.output, 
									lastUnitConNode.output,
									None,
									side = tipCtrl.side, 
									body = tipCtrl.body, 
									alpha = tipCtrl.alpha, 
									id = tipCtrl.id)

		clampNode = mnsNodes.clampNode([adlNode.node.output, 0, 0], 
									[360.0, 0.0, 0.0],
									None,
									None,
									side = tipCtrl.side, 
									body = tipCtrl.body, 
									alpha = tipCtrl.alpha, 
									id = tipCtrl.id)

		if rootGuide.side == "r" and False:
			mdlNode = mnsNodes.mdlNode(clampNode.node.outputR, 
										-1.0,
										None,
										side = tipCtrl.side, 
										body = tipCtrl.body, 
										alpha = tipCtrl.alpha, 
										id = tipCtrl.id)
			mdlNode.node.output >> blkUtils.getOffsetGrpForCtrl(tipCtrl, type = "modifyGrp").node.rx
		else:
			clampNode.node.outputR >> blkUtils.getOffsetGrpForCtrl(tipCtrl, type = "modifyGrp").node.rx

		#connect banks
		clampNode = mnsNodes.clampNode([rollCtrl.node.ry, 0, 0], 
									None,
									None,
									None,
									side = bkCtrl.side, 
									body = bkCtrl.body + "Bank", 
									alpha = bkCtrl.alpha, 
									id = bkCtrl.id)

		#get unitConversionNode
		unitConNode = clampNode.node.inputR.listConnections(s = True, d = False)[0]
		lastUnitConNode = unitConNode
		unitConNode.output >> clampNode.node.inputG
		unitConNode.output >> clampNode.node.inputB

		innerModGrp = mnsUtils.createOffsetGroup(innerCtrl, type = "modifyGrp")
		clampNode.node.maxR.set(360)

		if rootGuide.side == "r" and False:
			mdlNode = mnsNodes.mdlNode(clampNode.node.outputR, 
								-1.0,
								None,
								side = bkCtrl.side, 
								body = bkCtrl.body, 
								alpha = bkCtrl.alpha, 
								id = bkCtrl.id)
			mdlNode.node.output >> innerModGrp.node.ry
		else:
			clampNode.node.outputR >> innerModGrp.node.ry

		outerModGrp = mnsUtils.createOffsetGroup(outerCtrl, type = "modifyGrp")
		clampNode.node.minG.set(-360)
		if rootGuide.side == "r" and False:
			mdlNode = mnsNodes.mdlNode(clampNode.node.outputG, 
								-1.0,
								None,
								side = bkCtrl.side, 
								body = bkCtrl.body, 
								alpha = bkCtrl.alpha, 
								id = bkCtrl.id)
			mdlNode.node.output >> outerModGrp.node.ry
		else:
			clampNode.node.outputG >> outerModGrp.node.ry

	
	##################################################################################
	############# dyn Piv ctrl #######################################################

	status, doDynamicPivCtrl = mnsUtils.validateAttrAndGet(rootGuide, "doDynamicPivCtrl", True)
	dynPivCtrl = None
	if doDynamicPivCtrl:
		status, dynPivCtrlShape = mnsUtils.validateAttrAndGet(rootGuide, "dynamicPivControlShape", "lightSphere")
		dynPivChannelControlList = mnsUtils.splitEnumAttrToChannelControlList("dynamicPivChannelControl", rootGuide.node)

		dynPivPosGuide, dynPivShape = None, None
		for guide in customGuides: 
			if "DynPivPos" in guide.name: dynPivPosGuide = guide
			if "DynPivShape" in guide.name: dynPivShape = guide

		if dynPivPosGuide and dynPivShape:
			#first, create the control driver
			dynPivCtrl = blkCtrlShps.ctrlCreate(
								controlShape = dynPivCtrlShape,
								createBlkClassID = True, 
								createBlkCtrlTypeID = True, 
								blkCtrlTypeID = 1, 
								scale = modScale * 0.5, 
								alongAxis = 0, 
								side =rootGuide.side, 
								body = rootGuide.body + "DynPiv", 
								alpha = rootGuide.alpha, 
								id = rootGuide.id,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = dynPivPosGuide.node,
								parentNode = animGrp,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								symmetryType = symmetryType,
								doMirror = True,
								isFacial = MnsBuildModule.isFacial
								)
			for shape in dynPivCtrl.node.getShapes(): ikVisAttr >> shape.v
			secondaryCtrls.append(dynPivCtrl)
			mnsUtils.applyChennelControlAttributesToTransform(dynPivCtrl.node, dynPivChannelControlList)

			#create a new control for shape reference, and copy the guide shape into it.
			newDynShape = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "DynPivotShapeRef", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "group", incrementAlpha = False)
			dupCusShape = pm.duplicate(dynPivShape.node)[0]
			pm.parent(dupCusShape, newDynShape.node.getParent())
			pm.makeIdentity(dupCusShape, a = True)
			pm.delete(dupCusShape, ch = True)

			for cShape in dupCusShape.listRelatives(c = True, type = "nurbsCurve"):
				pm.parent(cShape, newDynShape.node, r = True, s = True)
				pm.rename(cShape, newDynShape.name + "Shape")
			pm.delete(dupCusShape)
			pm.parent(newDynShape.node, BKControls[0].node)
			newDynShape.node.v.set(False)
			mnsUtils.lockAndHideAllTransforms(newDynShape.node, lock = True)

			#create the driving mech and dynPiv node
			originalOffset = blkUtils.getOffsetGrpForCtrl(heelCtrl)
			originalModGrp = blkUtils.getOffsetGrpForCtrl(heelCtrl, type = "modifyGrp")
			if not originalModGrp:
				originalModGrp = mnsUtils.createOffsetGroup(heelCtrl, type = "modifyGrp")
			newOffset =  mnsUtils.createOffsetGroup(originalModGrp)

			status, distRateMultiplier = mnsUtils.validateAttrAndGet(rootGuide, "distRateMultiplier", 1.0)
			status, mapRotXTo = mnsUtils.validateAttrAndGet(rootGuide, "mapRotXTo", 2)
			status, mapRotYTo = mnsUtils.validateAttrAndGet(rootGuide, "mapRotYTo", 6)
			status, mapRotZTo = mnsUtils.validateAttrAndGet(rootGuide, "mapRotZTo", 3)
			
			originMatrixLoc = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "DynOriginPiv", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
			pm.parent(originMatrixLoc.node, originalOffset.node)
			
			dupShapeTemp = pm.duplicate(dynPivShape.node)[0]
			pm.xform(dupShapeTemp, cp = True)
			pm.delete(pm.parentConstraint(dupShapeTemp, originMatrixLoc.node))
			pm.delete(dupShapeTemp)
			mnsUtils.lockAndHideAllTransforms(originMatrixLoc.node, lock = True)
			originMatrixLoc.node.v.set(False)
			originMatrixLoc.node.v.setLocked(True)

			dynPivNode = mnsNodes.mnsDynamicPivotNode(side =rootGuide.side, 
													body = rootGuide.body, 
													alpha = rootGuide.alpha, 
													id = rootGuide.id,
													distRateMultiplier = distRateMultiplier,
													mapRotXTo = mapRotXTo,
													mapRotYTo = mapRotYTo,
													mapRotZTo = mapRotZTo,
													inputCurve = newDynShape.node,
													originWorldMatrix = originMatrixLoc.node.attr("worldMatrix[0]"),
													rotate = dynPivCtrl.node.r,
													targetParentInverseMatrix = newOffset.node.attr("parentInverseMatrix[0]"),
													rotatePivot = newOffset.node.attr("rotatePivot")
													)

			dynPivCtrlOffset = blkUtils.getOffsetGrpForCtrl(dynPivCtrl)
			pm.delete(pm.orientConstraint(newOffset.node, dynPivCtrlOffset.node))

			inputNode = dynPivCtrl
			xAttrName = "rx"
			yAttrName = "ry"
			if rootGuide.side == "r":
				dynPivNode.node.inputMultipliersY.set(-1)
				"""
				inputNode = mnsNodes.mdNode(inputNode.node.r, 
									[-1, -1, -1],
									None,
									side = dynPivCtrl.side, 
									body = dynPivCtrl.body + "RightRev", 
									alpha = dynPivCtrl.alpha, 
									id = dynPivCtrl.id)

				xAttrName = "outputX"
				yAttrName = "outputY"
				"""

			inputNode.node.attr(xAttrName) >> newOffset.node.rx
			inputNode.node.attr(yAttrName) >> newOffset.node.ry

			#create custom Attrs
			host = dynPivCtrl.node

			#divider
			mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "dynamicPivot", replace = True, locked = True)
				
			#distRateMultiplier
			distRateMultiplierAttr = mnsUtils.addAttrToObj([host], type = "float", value = distRateMultiplier, name = "distRateMultiplier", replace = True)[0]
			distRateMultiplierAttr >> dynPivNode.node.distRateMultiplier
			
			dynShapeVisAttr = mnsUtils.addAttrToObj([host], type = "bool", value = False, name = "dynamicShapeVis", replace = True)[0]
			dynShapeVisAttr >> newDynShape.node.v
			
	ctrlsCollect = FKControls + BKControls + cusPivCtrls + [ankleTweak]
	if rollCtrl: ctrlsCollect.append(rollCtrl)
	if dynPivCtrl: ctrlsCollect.append(dynPivCtrl)

	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, None, attrHost

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

		valFlip = 1
		translateDict = {"heel": {"attrName": "ty", "value": -2}, "toe": {"attrName": "ty", "value": 2}, "inner": {"attrName": "tx", "value": -2 * valFlip}, "outer": {"attrName": "tx", "value": 2 * valFlip}}
		for cusPivot in translateDict.keys():
			cusPivNameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + cusPivot.capitalize() + "Pivot", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
			custGuides.append(cusPivNameStd)
			parentDict.update({cusPivNameStd: builtGuides[0]})

			cusPivNameStdOffGrp = mnsUtils.createOffsetGroup(cusPivNameStd)
			pm.delete(pm.parentConstraint(builtGuides[0].node, cusPivNameStdOffGrp.node))
			cusPivNameStd.node.attr(translateDict[cusPivot]["attrName"]).set(translateDict[cusPivot]["value"])
			pm.parent(cusPivNameStd.node, w = True)
			pm.delete(cusPivNameStdOffGrp.node)

		dynPivPos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "DynPivPos", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		dynPivPosOffset = mnsUtils.createOffsetGroup(dynPivPos)
		pm.delete(pm.parentConstraint(builtGuides[0].node, dynPivPosOffset.node))
		dynPivPos.node.tz.set(-2)
		pm.parent(dynPivPos.node, w = True)
		pm.delete(dynPivPosOffset.node)
		parentDict.update({dynPivPos: builtGuides[0]})
		custGuides.append(dynPivPos)

		status, shapeSections = mnsUtils.validateAttrAndGet(builtGuides[0], "dynamicPivShapeSections", 8)
		dynPivShape = blkCtrlShps.ctrlCreate(
									controlShape = "circle",
									createBlkClassID = True, 
									createBlkCtrlTypeID = False, 
									scale = modScale * 2, 
									sections = shapeSections,
									alongAxis = 2, 
									side =builtGuides[0].side, 
									body = builtGuides[0].body + "DynPivShape", 
									alpha = builtGuides[0].alpha, 
									id = builtGuides[0].id,
									color = blkUtils.getCtrlCol(builtGuides[0], rigTop),
									matchTransform = builtGuides[0].node,
									createSpaceSwitchGroup = False,
									createOffsetGrp = False
									)

		custGuides.append(dynPivShape)
		parentDict.update({dynPivShape: builtGuides[0]})
		
	return custGuides, parentDict

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	#find sleeve nodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core import utility as mnsUtils

	rootGuide = guides[0]
	status, doDynamicPivCtrl = mnsUtils.validateAttrAndGet(rootGuide, "doDynamicPivCtrl", True)

	customGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, customGuidesOnly = True)
	for cg in customGuides:
		if "dynpiv" in cg.name.lower():
			if doDynamicPivCtrl: cg.node.v.set(True)
			else: cg.node.v.set(False)

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	#connection to limb
	ikSolverNode, newIKTarget, bkTop, fkRootCtrl, footSpaceSource = None, None, None, None, None

	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		connectToLimb, parModuleRoot = False, None
		parNode = rootGuide.node.getParent()
		if parNode:
			parModuleRoot = blkUtils.getModuleRoot(parNode)
			if parModuleRoot:
				status, modType = mnsUtils.validateAttrAndGet(parModuleRoot, "modType", None)
				if modType and "limb" in modType.lower(): 
					connectToLimb = True

		status, ctrlAuthority = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
		if ctrlAuthority: 
			status, newIKTarget = mnsUtils.validateAttrAndGet(ctrlAuthority, "newIKTarget", None)
			status, bkTop = mnsUtils.validateAttrAndGet(ctrlAuthority, "bkTop", None)
			status, fkRootCtrl = mnsUtils.validateAttrAndGet(ctrlAuthority, "fkRootCtrl", None)

			if connectToLimb:
				status, ctrlAuthority = mnsUtils.validateAttrAndGet(parModuleRoot, "ctrlAuthority", None)
				if ctrlAuthority:
					status, ikSolverNode = mnsUtils.validateAttrAndGet(ctrlAuthority, "ikSolver", None)
					ikModuleAnimGrp = blkUtils.getModuleAnimGrp(ctrlAuthority)
					selfModuleAnimGrp = blkUtils.getModuleAnimGrp(MnsBuildModule.allControls[0])
					
					status, blendAttrHolder = mnsUtils.validateAttrAndGet(ikModuleAnimGrp, "blendAttrHolder", None)
					if blendAttrHolder:
						status, selfBlendAttrHolder = mnsUtils.validateAttrAndGet(selfModuleAnimGrp, "blendAttrHolder", None)
						if selfBlendAttrHolder:
							blendAttrHolder.ikFkBlend >> selfBlendAttrHolder.ikFkBlend
					
					status, footSpaceSource = mnsUtils.validateAttrAndGet(ctrlAuthority, "footSpaceSource", None)
					if ikSolverNode and newIKTarget: 
						status, ikTarget = mnsUtils.validateAttrAndGet(ikSolverNode, "ikTarget", None)
						originalIkTarget = None

						if status: # Limb case
							inConnections =ikSolverNode.ikTarget.listConnections(s = True, d = False)
							if inConnections: 
								originalIkTarget = inConnections[0]
								newIKTarget.worldMatrix[0] >> ikSolverNode.ikTarget
						if not status: # hind Limb case
							pm.delete(ikSolverNode.listRelatives(c = True, type = "parentConstraint"))
							parentConstraint = mnsNodes.mayaConstraint([newIKTarget], ikSolverNode, type = "parent", maintainOffset = True)
				
							status, originalIkTarget = mnsUtils.validateAttrAndGet(ctrlAuthority, "ikCtrl", None)
							if originalIkTarget:
								status, ik2BSolver = mnsUtils.validateAttrAndGet(ctrlAuthority, "ik2BSolver", None)
								ik2BSolverPar= ik2BSolver.getParent()
								pntCns = ik2BSolverPar.listRelatives(c = True, type = "pointConstraint")
								if pntCns:
									pntCns = pntCns[0]
									cnsInCons = pntCns.target[0].targetParentMatrix.listConnections(s = True, d = False)
									if cnsInCons:
										ik2BTargetLoc = cnsInCons[0]
										tarOsGrp = blkUtils.getOffsetGrpForCtrl(ik2BTargetLoc.getParent())
										if tarOsGrp:
											pm.delete(tarOsGrp.node.listRelatives(c = True, type = "pointConstraint"))
											pointCns = mnsNodes.mayaConstraint([newIKTarget], tarOsGrp, type = "point", maintainOffset = True)

											ik2BEndEffector = ik2BSolver.endEffector.listConnections(s = True, d = False)
											if ik2BEndEffector:
												ik2BEndEffector = ik2BEndEffector[0]
												aimCns = ik2BEndEffector.getParent().listRelatives(ad = True, type = "aimConstraint")
												if aimCns:
													aimCns = aimCns[0]
													#reconnect aim target
													newIKTarget.translate >> aimCns.target[0].targetTranslate
													newIKTarget.parentMatrix >> aimCns.target[0].targetParentMatrix
													newIKTarget.rotatePivot >> aimCns.target[0].targetRotatePivot
													newIKTarget.rotatePivotTranslate >> aimCns.target[0].targetRotateTranslate

						if originalIkTarget: #both cases
							status, endTweak = mnsUtils.validateAttrAndGet(ctrlAuthority, "endTweak", None)
							if endTweak: pm.delete(endTweak.getShapes())
							
							if bkTop:
								mnsNodes.mnsMatrixConstraintNode(side = rootGuide.side, alpha = rootGuide.alpha, id = rootGuide.id, targets = [bkTop], sources = [originalIkTarget], connectScale = True, maintainOffset = True)

							if fkRootCtrl:
								rootCtrlOffsetGrp = blkUtils.getOffsetGrpForCtrl(fkRootCtrl)
								if rootCtrlOffsetGrp and footSpaceSource:
									#create the orient connector
									orientConnector = mnsUtils.createNodeReturnNameStd(parentNode = footSpaceSource, side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "Connector", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
									pm.delete(pm.parentConstraint(footSpaceSource, orientConnector.node))
									pm.delete(pm.orientConstraint(newIKTarget, orientConnector.node))
									mnsUtils.createOffsetGroup(orientConnector)
									orientConnector.node.v.set(False)
									orientConnector.node.v.setLocked(True)

									#create FK orient vlend loc
									fkRotBlend = mnsUtils.createNodeReturnNameStd(parentNode = footSpaceSource, side = MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "FKRotBlend", alpha = MnsBuildModule.rootGuide.alpha, id = MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
									pm.delete(pm.parentConstraint(footSpaceSource, fkRotBlend.node))
									pm.delete(pm.orientConstraint(newIKTarget, fkRotBlend.node))
									mnsUtils.createOffsetGroup(fkRotBlend)
									fkRotBlend.node.v.set(False)
									fkRotBlend.node.v.setLocked(True)
									
									#create the new space for the foot FK offset group, and connect a switcher
									oriCns = mnsNodes.mayaConstraint([newIKTarget, fkRotBlend.node], orientConnector.node, type = "orient")
									#connect the switcher
									status, ctrlAuthority = mnsUtils.validateAttrAndGet(MnsBuildModule.rootGuide, "ctrlAuthority", None)
									if ctrlAuthority:
										animGrp = blkUtils.getModuleAnimGrp(ctrlAuthority)
										if animGrp:
											status, value = mnsUtils.validateAttrAndGet(animGrp, "ikFkBlend", None)
											if status:
												blendAttr = animGrp.node.ikFkBlend
												revNode = mnsNodes.reverseNode([blendAttr,0,0], 
																				None,
																				side = animGrp.side, 
																				body = animGrp.body + "IkFk", 
																				alpha = animGrp.alpha, 
																				id = animGrp.id)
												revNode.node.outputX >> oriCns.node.attr(newIKTarget.nodeName() + "W0")
												blendAttr >> oriCns.node.attr(fkRotBlend.node.nodeName() + "W1")

									#lock and hide trans for new utility transforms
									mnsUtils.lockAndHideAllTransforms(orientConnector.node, lock = True)
									mnsUtils.lockAndHideAllTransforms(fkRotBlend.node, lock = True)

									#constraint the FK group to the new space
									mnsNodes.mnsMatrixConstraintNode(side = rootCtrlOffsetGrp.side, alpha = rootCtrlOffsetGrp.alpha, id = rootCtrlOffsetGrp.id, targets = [rootCtrlOffsetGrp], sources = [orientConnector], connectScale = False, maintainOffset = True)
			else:
				#parent bkTop to module Root
				animGrp = blkUtils.getModuleAnimGrp(ctrlAuthority)
				pm.parent(bkTop, animGrp.node)