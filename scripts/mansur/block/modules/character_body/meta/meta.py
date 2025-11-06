"""Author: Asaf Ben-Zur
Best used for: Metacarpal (Fingers), Metatarsal (Toes)
This module will create a control for every root guide position, as well as a few global splay controls for the collection of controls based on settings.
The play controls will behave as a global tweaker for the control collection, allowing easier animation.
In order to implement "splayB" feature, simply parent a FK chain modules under each of the main meta guides.
This module construction will try to detect a FK module under each guide, and if any exist, will create the second layer splay control for these FK chains.
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
	secondaryControls = []
	primaryCtrls = []

	########### module construction ###########
	status, tweakersControlShape = mnsUtils.validateAttrAndGet(rootGuide, "tweakersControlShape", "cone")
	status, tweakerChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "tweakerChannelControl", {})
	if status: tweakerChannelControl = mnsUtils.splitEnumAttrToChannelControlList("tweakerChannelControl", rootGuide.node)

	#build
	tweakerModGrps = []
	for guide in allGuides:
		relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(guide))	

		doMirror = True
		parNode = animGrp

		ctrl = blkCtrlShps.ctrlCreate(
									controlShape = tweakersControlShape,
									createBlkClassID = True, 
									createBlkCtrlTypeID = True, 
									blkCtrlTypeID = 0, 
									scale = modScale * 0.5, 
									alongAxis = 0, 
									side = guide.side, 
									body = guide.body, 
									alpha = guide.alpha, 
									id = guide.id,
									color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
									matchTransform = guide.node,
									createOffsetGrp = True,
									createSpaceSwitchGroup = False,
									parentNode = parNode,
									symmetryType = symmetryType,
									doMirror = doMirror,
									isFacial = MnsBuildModule.isFacial,
									offsetRigMaster = relatedJnt
									)

		#apply channel control
		mnsUtils.applyChennelControlAttributesToTransform(ctrl.node, tweakerChannelControl)

		#collect
		secondaryControls.append(ctrl)

		#transfer authority
		relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(guide))	
		if relatedJnt:blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)

	#splayControls
	status, doSplayA = mnsUtils.validateAttrAndGet(rootGuide, "doSplayA", True)
	status, doSplayAMid = mnsUtils.validateAttrAndGet(rootGuide, "doSplayAMid", True)
		
	if doSplayA:
		status, splayControlShape = mnsUtils.validateAttrAndGet(rootGuide, "splayControlShape", "diamond")
		status, splayChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "splayChannelControl", {})
		if status: splayChannelControl = mnsUtils.splitEnumAttrToChannelControlList("splayChannelControl", rootGuide.node)

		splayACtrl = blkCtrlShps.ctrlCreate(
						controlShape = splayControlShape,
						createBlkClassID = True, 
						createBlkCtrlTypeID = True, 
						blkCtrlTypeID = 0, 
						scale = modScale * 0.75, 
						alongAxis = 1, 
						side = rootGuide.side, 
						body = rootGuide.body + "SplayA", 
						alpha = rootGuide.alpha, 
						id = rootGuide.id,
						color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
						matchTransform = secondaryControls[-1].node,
						createOffsetGrp = True,
						createSpaceSwitchGroup = False,
						parentNode = animGrp,
						symmetryType = symmetryType,
						doMirror = doMirror,
						isFacial = MnsBuildModule.isFacial
						)
		splayAAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "splayACtrl", value= "", replace = True)[0]
		splayACtrl.node.message >> splayAAttr

		lastMetaTweakAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "lastMetaTweak", value= "", replace = True)[0]
		secondaryControls[-1].node.message >> lastMetaTweakAttr

		#apply channel control
		mnsUtils.applyChennelControlAttributesToTransform(splayACtrl.node, splayChannelControl)

		#collect
		primaryCtrls.append(splayACtrl)

		#create attrs and behaviour
		host = splayACtrl.node

		#divider
		mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "splayASettings", replace = True, locked = True)

		splayATranslateMDs = []
		splayARotateMDs = []
		splayAModGrps = []

		#mulpliers
		for k, secondaryControl in enumerate(secondaryControls):
			splayAModGrp = mnsUtils.createOffsetGroup(secondaryControl, type = "modifyGrp")
			splayAModGrps.append(splayAModGrp)

			attrName = "splayAMultiplier" + mnsUtils.convertIntToAlpha(k)
			attrValue = (1.0 / float(len(secondaryControls) - 1)) * float(k)
			multAttr = mnsUtils.addAttrToObj([host], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]

			for channel in "tr":
				mdNode = None
				if not doSplayAMid:
					mdNode = mnsNodes.mdNode(splayACtrl.node.attr(channel), 
								[multAttr, multAttr, multAttr],
								splayAModGrp.node.attr(channel),
								side = secondaryControl.side, 
								body = secondaryControl.body + "splayA" + channel, 
								alpha = secondaryControl.alpha, 
								id = secondaryControl.id)
				else:
					mdNode = mnsNodes.mdNode(splayACtrl.node.attr(channel), 
								[multAttr, multAttr, multAttr],
								None,
								side = secondaryControl.side, 
								body = secondaryControl.body + "splayA" + channel, 
								alpha = secondaryControl.alpha, 
								id = secondaryControl.id)

				if channel == "t": splayATranslateMDs.append(mdNode)
				else: splayARotateMDs.append(mdNode)

		if doSplayAMid:
			splayAMidCtrl = blkCtrlShps.ctrlCreate(
												controlShape = splayControlShape,
												createBlkClassID = True, 
												createBlkCtrlTypeID = True, 
												blkCtrlTypeID = 0, 
												scale = modScale * 0.75, 
												alongAxis = 1, 
												side = rootGuide.side, 
												body = rootGuide.body + "SplayAMid", 
												alpha = rootGuide.alpha, 
												id = rootGuide.id,
												color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
												matchTransform = secondaryControls[-1].node,
												createOffsetGrp = True,
												createSpaceSwitchGroup = False,
												parentNode = animGrp,
												symmetryType = symmetryType,
												doMirror = doMirror,
												isFacial = MnsBuildModule.isFacial
												)
			splayAMidAttr = mnsUtils.addAttrToObj([animGrp.node], type = "message", name = "splayAMidCtrl", value= "", replace = True)[0]
			splayAMidCtrl.node.message >> splayAMidAttr

			#position
			pConst = pm.delete(pm.pointConstraint([secondaryControls[0].node, secondaryControls[-1].node], splayAMidCtrl.node, w = 0.5))
			pm.makeIdentity(splayAMidCtrl.node, a = True)
			
			#apply channel control
			mnsUtils.applyChennelControlAttributesToTransform(splayAMidCtrl.node, splayChannelControl)

			#collect
			primaryCtrls.append(splayAMidCtrl)

			#create attrs and behaviour
			host = splayAMidCtrl.node

			#divider
			mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "splayAMidSettings", replace = True, locked = True)

			#mulpliers
			midParameter = 0.5

			rotEnum = 0
			tranEnum = 0

			for k, secondaryControl in enumerate(secondaryControls):
				fltK = float(k)
				attrName = "splayBMidMultiplier" + mnsUtils.convertIntToAlpha(k)
				attrValuePure = (1.0 / float(len(secondaryControls) - 1)) * fltK
				attrValue = abs(midParameter - attrValuePure)

				multAttr = mnsUtils.addAttrToObj([host], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]

				for j,channel in enumerate("tr"):
					mdNode = mnsNodes.mdNode(splayAMidCtrl.node.attr(channel), 
											[multAttr, multAttr, multAttr],
											None,
											side = secondaryControl.side, 
											body = secondaryControl.body + "splayAMid" + channel, 
											alpha = secondaryControl.alpha, 
											id = secondaryControl.id)


					if attrValuePure > midParameter:
						mdNode = mnsNodes.mdNode(mdNode.node.output, 
												[-1.0, -1.0, -1.0],
												None,
												side = secondaryControl.side, 
												body = secondaryControl.body + "splayAMid" + channel, 
												alpha = secondaryControl.alpha, 
												id = secondaryControl.id)

					sourceNode = None
					if channel == "t":
						sourceNode = splayATranslateMDs[tranEnum]
						tranEnum += 1
					else:
						sourceNode = splayARotateMDs[rotEnum]
						rotEnum += 1

					pmaNode = mnsNodes.pmaNode(None, None, [sourceNode.node.output, mdNode.node.output],
												None, None, splayAModGrps[k].node.attr(channel),
												side = secondaryControl.side, 
												body = secondaryControl.body, 
												alpha = secondaryControl.alpha, 
												id = secondaryControl.id)

	ctrlsCollect = primaryCtrls + secondaryControls
	#return; list (controls), dict (internalSpaces), MnsNameStd (moduleSpaceAttrHost)
	return ctrlsCollect, internalSpacesDict, None, attrHost

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core import prefixSuffix as mnsPS

	rootGuide = MnsBuildModule.rootGuide
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	selfModuleAnimGrp = MnsBuildModule.animGrp
	status, doSplayB = mnsUtils.validateAttrAndGet(rootGuide, "doSplayB", True)
	status, doSplayA = mnsUtils.validateAttrAndGet(rootGuide, "doSplayA", True)
	status, doSplayBMid = mnsUtils.validateAttrAndGet(rootGuide, "doSplayBMid", True)
	status, doCurls = mnsUtils.validateAttrAndGet(rootGuide, "doCurls", True)

	modScale = MnsBuildModule.rigTop.node.assetScale.get() * MnsBuildModule.rootGuide.node.controlsMultiplier.get() * mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]

	if selfModuleAnimGrp and (doSplayB or doCurls):
		allGuides = mnsUtils.sortNameStdArrayByID([MnsBuildModule.rootGuide] + MnsBuildModule.guideControls)
		allGuideNodes = [g.node for g in allGuides]

		moduleRootsToSplay = []
		for k, guideNode in enumerate(allGuideNodes):
			for childGuide in guideNode.listRelatives(c = True, type = "transform"):
				if not childGuide in allGuideNodes:
					status, ctrlAuthority = mnsUtils.validateAttrAndGet(childGuide, "ctrlAuthority", None)
					if ctrlAuthority:
						animGrp = blkUtils.getModuleAnimGrp(ctrlAuthority)
						if animGrp: moduleRootsToSplay.append(animGrp)

		splayBCtrl = None
		if doSplayB:
			ctrlsToShapeBuild = []
			if moduleRootsToSplay:
				status, splayControlShape = mnsUtils.validateAttrAndGet(rootGuide, "splayControlShape", "diamond")
				status, splayChannelControl = mnsUtils.validateAttrAndGet(rootGuide, "splayChannelControl", {})
				if status: splayChannelControl = mnsUtils.splitEnumAttrToChannelControlList("splayChannelControl", rootGuide.node)

				parNode = selfModuleAnimGrp
				status, splayACtrl =  mnsUtils.validateAttrAndGet(selfModuleAnimGrp, "splayACtrl", None)
				status, lastMetaTweak =  mnsUtils.validateAttrAndGet(selfModuleAnimGrp, "lastMetaTweak", None)
				if splayACtrl: parNode = splayACtrl

				splayBCtrl = blkCtrlShps.ctrlCreate(
													controlShape = splayControlShape,
													createBlkClassID = True, 
													createBlkCtrlTypeID = True, 
													blkCtrlTypeID = 0, 
													scale = modScale * 0.75, 
													alongAxis = 1, 
													side = rootGuide.side, 
													body = rootGuide.body + "SplayB", 
													alpha = rootGuide.alpha, 
													id = rootGuide.id,
													color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
													matchTransform = moduleRootsToSplay[-1].node,
													createOffsetGrp = True,
													createSpaceSwitchGroup = False,
													parentNode = parNode,
													symmetryType = symmetryType,
													doMirror = True,
													isFacial = MnsBuildModule.isFacial
													)
				ctrlsToShapeBuild.append(splayBCtrl)

				if lastMetaTweak:
					splayBMod = mnsUtils.createOffsetGroup(splayBCtrl, type = "modifyGrp")
					mc = mnsNodes.mnsMatrixConstraintNode(side = splayBCtrl.side, alpha = splayBCtrl.alpha, id = splayBCtrl.id, targets = [splayBMod.node], sources = [lastMetaTweak], connectScale = True, maintainOffset = True)

				#apply channel control
				mnsUtils.applyChennelControlAttributesToTransform(splayBCtrl.node, splayChannelControl)

				#create attrs and behaviour
				host = splayBCtrl.node

				#divider
				mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "splayBSettings", replace = True, locked = True)

				splayBTranslateMDs = []
				splayBRotateMDs = []
				splayBModGrps = []

				#mulpliers
				for k, moduleRootCtrl in enumerate(moduleRootsToSplay):
					splayBModGrp = mnsUtils.createOffsetGroup(moduleRootCtrl, type = "modifyGrp")
					splayBModGrps.append(splayBModGrp)

					attrName = "splayAMultiplier" + mnsUtils.convertIntToAlpha(k)
					
					attrValue = 0.0
					if len(moduleRootsToSplay) > 1:
						attrValue = (1.0 / float(len(moduleRootsToSplay) - 1)) * float(k)

					multAttr = mnsUtils.addAttrToObj([host], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]

					for channel in "tr":
						mdNode = None

						if not doSplayBMid:
							mdNode = mnsNodes.mdNode(splayBCtrl.node.attr(channel), 
										[multAttr, multAttr, multAttr],
										splayBModGrp.node.attr(channel),
										side = selfModuleAnimGrp.side, 
										body = selfModuleAnimGrp.body + "splayB" + channel, 
										alpha = selfModuleAnimGrp.alpha, 
										id = selfModuleAnimGrp.id)
						else:
							mdNode = mnsNodes.mdNode(splayBCtrl.node.attr(channel), 
										[multAttr, multAttr, multAttr],
										None,
										side = selfModuleAnimGrp.side, 
										body = selfModuleAnimGrp.body + "splayB" + channel, 
										alpha = selfModuleAnimGrp.alpha, 
										id = selfModuleAnimGrp.id)

						if channel == "t": splayBTranslateMDs.append(mdNode)
						else: splayBRotateMDs.append(mdNode)


				if doSplayBMid:
					status, splayAMidCtrl =  mnsUtils.validateAttrAndGet(selfModuleAnimGrp, "splayAMidCtrl", None)

					splayBMidCtrl = blkCtrlShps.ctrlCreate(
														controlShape = splayControlShape,
														createBlkClassID = True, 
														createBlkCtrlTypeID = True, 
														blkCtrlTypeID = 0, 
														scale = modScale * 0.75, 
														alongAxis = 1, 
														side = rootGuide.side, 
														body = rootGuide.body + "SplayBMid", 
														alpha = rootGuide.alpha, 
														id = rootGuide.id,
														color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
														matchTransform = moduleRootsToSplay[-1].node,
														createOffsetGrp = True,
														createSpaceSwitchGroup = False,
														parentNode = splayAMidCtrl,
														symmetryType = symmetryType,
														doMirror = True,
														isFacial = MnsBuildModule.isFacial
														)
					ctrlsToShapeBuild.append(splayBMidCtrl)

					splayBMidMod = mnsUtils.createOffsetGroup(splayBMidCtrl, type = "modifyGrp")
					mc = mnsNodes.mnsMatrixConstraintNode(side = splayBMidCtrl.side, alpha = splayBMidCtrl.alpha, id = splayBMidCtrl.id, targets = [splayBMidMod.node], sources = [selfModuleAnimGrp.node], connectScale = True, maintainOffset = True)

					#position	
					pConst = pm.delete(pm.pointConstraint([moduleRootsToSplay[0].node, moduleRootsToSplay[-1].node], splayBMidCtrl.node, w = 0.5))
					pm.makeIdentity(splayBMidCtrl.node, a = True)
					
					#apply channel control
					mnsUtils.applyChennelControlAttributesToTransform(splayBMidCtrl.node, splayChannelControl)

					#collect
					MnsBuildModule.controls["primaries"].append(splayBMidCtrl)

					#create attrs and behaviour
					host = splayBMidCtrl.node

					#divider
					mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "splayBMidSettings", replace = True, locked = True)

					#mulpliers
					midParameter = 0.5

					rotEnum = 0
					tranEnum = 0

					for k, moduleRoot in enumerate(moduleRootsToSplay):
						fltK = float(k)
						attrName = "splayBMidMultiplier" + mnsUtils.convertIntToAlpha(k)
						
						attrValuePure = 0.0
						if len(moduleRootsToSplay) > 1:
							attrValuePure = (1.0 / float(len(moduleRootsToSplay) - 1)) * fltK
						attrValue = abs(midParameter - attrValuePure)

						multAttr = mnsUtils.addAttrToObj([host], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]

						for j,channel in enumerate("tr"):
							mdNode = mnsNodes.mdNode(splayBMidCtrl.node.attr(channel), 
													[multAttr, multAttr, multAttr],
													None,
													side = moduleRoot.side, 
													body = moduleRoot.body + "splayBMid" + channel, 
													alpha = moduleRoot.alpha, 
													id = moduleRoot.id)


							if attrValuePure > midParameter:
								mdNode = mnsNodes.mdNode(mdNode.node.output, 
														[-1.0, -1.0, -1.0],
														None,
														side = moduleRoot.side, 
														body = moduleRoot.body + "splayBMid" + channel, 
														alpha = moduleRoot.alpha, 
														id = moduleRoot.id)

							sourceNode = None
							if channel == "t":
								sourceNode = splayBTranslateMDs[tranEnum]
								tranEnum += 1
							else:
								sourceNode = splayBRotateMDs[rotEnum]
								rotEnum += 1

							pmaNode = mnsNodes.pmaNode(None, None, [sourceNode.node.output, mdNode.node.output],
														None, None, splayBModGrps[k].node.attr(channel),
														side = moduleRoot.side, 
														body = moduleRoot.body, 
														alpha = moduleRoot.alpha, 
														id = moduleRoot.id)
				if ctrlsToShapeBuild:
					blkUtils.buildShapes(ctrlsToShapeBuild, MnsBuildModule.rigTop, mode = 1)
		if doCurls and moduleRootsToSplay:
			#gather host
			attrHost = MnsBuildModule.attrHostCtrl or selfModuleAnimGrp
			if attrHost == selfModuleAnimGrp and doSplayA:
				if splayBCtrl:
					attrHost = splayBCtrl
				else:
					for primCtrl in MnsBuildModule.controls["primaries"]:
						if "SplayA_" in primCtrl.node.nodeName() and not doSplayB:
							attrHost = mnsUtils.validateNameStd(primCtrl)
							break

			#divider
			mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "curls", replace = True, locked = True)

			#main curls
			curlXAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "curlX", replace = True)[0]
			curlYAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "curlY", replace = True)[0]
			curlZAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "curlZ", replace = True)[0]

			mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "gradualCurls", replace = True, locked = True)
			gradCurlXAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "gradCurlX", replace = True)[0]
			gradCurlYAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "gradCurlY", replace = True)[0]
			gradCurlZAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = 0.0, name = "gradCurlZ", replace = True)[0]

			mnsUtils.addAttrToObj([attrHost], type = "enum", value = ["______"], name = "gradualCurlSettings", replace = True, locked = True)

			for k, moduleRoot in enumerate(moduleRootsToSplay):
				allCtrlDecendents = [mnsUtils.validateNameStd(c) for c in moduleRoot.node.listRelatives(ad = True, type = "transform") if c.nodeName().split("_")[-1] == mnsPS.mnsPS_ctrl]
				primCtrlsCollect = []
				for ctrl in allCtrlDecendents:
					status, guideAuthority = mnsUtils.validateAttrAndGet(ctrl, "guideAuthority", None)
					if status and guideAuthority:
						primCtrlsCollect.append(mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp"))
				transformsToCurl = mnsUtils.sortNameStdArrayByID(primCtrlsCollect)

				attrName = "curlMultiplier" + mnsUtils.convertIntToAlpha(k)
				attrValue = 0.0
				if len(moduleRootsToSplay) > 1:
					attrValue = (1.0 / float(len(moduleRootsToSplay) - 1)) * float(k)

				multAttr = mnsUtils.addAttrToObj([attrHost], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]

				mdNode = mnsNodes.mdNode([gradCurlXAttr, gradCurlYAttr, gradCurlZAttr], 
										[multAttr, multAttr, multAttr],
										None,
										side = selfModuleAnimGrp.side, 
										body = selfModuleAnimGrp.body + "GradCurl", 
										alpha = selfModuleAnimGrp.alpha, 
										id = selfModuleAnimGrp.id)

				pmaNode = mnsNodes.pmaNode(None, None, [mdNode.node.output],
														None, None, None,
														side = moduleRoot.side, 
														body = moduleRoot.body, 
														alpha = moduleRoot.alpha, 
														id = moduleRoot.id)
				curlXAttr >> pmaNode.node.input3D[1].input3Dx
				curlYAttr >> pmaNode.node.input3D[1].input3Dy
				curlZAttr >> pmaNode.node.input3D[1].input3Dz

				for tranToCurl in transformsToCurl:
					pmaNode.node.output3Dx >> tranToCurl.node.rx
					pmaNode.node.output3Dy >> tranToCurl.node.ry
					pmaNode.node.output3Dz >> tranToCurl.node.rz