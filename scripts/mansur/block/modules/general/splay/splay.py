"""Author: Asaf Ben-Zur
Best used for: fingers, bat wings
This is a general module used for splaying behaviour for any slave modules.
This module does not create any joints.
This module's behaviour is matched to the Meta module's splay behaviour, but can be implemented for any slave module.
A control will be created, and it's translation and rotation values will be connected to all input slave guides in the module settings, creating a gradual translation/rotation for all slaves- creating the splay behaviour.
Splay multipliers that can be manipulated will be created as well on the given control.
This module contains the choice of adding another Splay-Mid control, which will be added to the calculation, creating a gradual behaviour from the middle slave outwards in both directions, instead of the top-to-bottom splay that the main control offers.
Make sure to load slaves IN-ORDER to achive correct behaviour.
Valid-Slaves are root-guide and guides only. The slaves will be the direct related controls to these input guides.
Important: The behaviour is a result of a local channel connection. Since the slaves' orientation is unknowen, you need to make sure that this module's orientation matches the target slaves orientation.
"""



from maya import cmds
import pymel.core as pm


def filterValidSlaves(slavesList = [], mansur = None):
	from mansur.core import prefixSuffix
	from mansur.core import utility as mnsUtils

	returnList = []
	if slavesList:
		for k, slave in enumerate(slavesList):
			slave = mnsUtils.validateNameStd(slave)
			if slave:
				#handleGuides
				if slave.suffix == prefixSuffix.mnsPS_gRootCtrl or slave.suffix == prefixSuffix.mnsPS_gCtrl:
					status, ctrlAuthority = mnsUtils.validateAttrAndGet(slave, "ctrlAuthority", None)
					if ctrlAuthority:
						ctrlAuthority = mnsUtils.validateNameStd(ctrlAuthority)
						if ctrlAuthority:
							returnList.append(ctrlAuthority)	
	return returnList

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

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
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
								createMasterSwitchGroup = False,
								createOffsetGrp = True,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial,
								offsetRigMaster = None)
	ctrlsCollect.append(ctrl)

	status, doSplayMid = mnsUtils.validateAttrAndGet(rootGuide, "doSplayMid", False)
	if doSplayMid:
		customGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, customGuidesOnly = True)
		
		midPosRef = MnsBuildModule.rootGuide.node
		if customGuides:
			for cg in customGuides:
				if "midposition" in cg.name.lower():
					midPosRef = cg
					break

		status, midControlShape = mnsUtils.validateAttrAndGet(rootGuide, "midControlShape", "lightPin")
		midChannelControlList = mnsUtils.splitEnumAttrToChannelControlList("midChannelControl", MnsBuildModule.rootGuide.node)
	
		splayMidCtrl = blkCtrlShps.ctrlCreate(
								nameReference = MnsBuildModule.rootGuide,
								bodySuffix = "Mid",
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = midPosRef.node,
								controlShape = midControlShape,
								scale = modScale, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								chennelControl = midChannelControlList,
								isFacial = MnsBuildModule.isFacial,
								offsetRigMaster = None)
		ctrlsCollect.append(splayMidCtrl)

	#done contruction, finalize	
	host = MnsBuildModule.attrHostCtrl or ctrl
	mnsUtils.addAttrToObj([ctrl.node], type = "message", name = "guideAuthority", value= rootGuide.node, replace = True)[0]
	mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "ctrlAuthority", value= ctrl.node, replace = True)[0]

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, host, host

def customGuides(mansur, builtGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils

	custGuides = []
	parentDict = {}

	if builtGuides:
		nameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "MidPosition", alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(builtGuides[0].node, nameStd.node))
		custGuides.append(nameStd)
		parentDict.update({nameStd: builtGuides[0]})

	return custGuides, parentDict

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
		if jntChildren: 
			pm.parent(jntChildren, relatedRootJnt.node.getParent())
			#zero joint orient
			for j in jntChildren:
				j.jointOrient.set((0.0,0.0,0.0))
		pm.delete(relatedRootJnt.node)
		relatedRootJnt = None

	customGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, customGuidesOnly = True)
	if customGuides:
		for cg in customGuides:
			if "midposition" in cg.name.lower():
				status, doSplayMid = mnsUtils.validateAttrAndGet(rootGuide, "doSplayMid", False)
				if doSplayMid:
					cg.node.v.set(True)
				else:
					cg.node.v.set(False)
				break

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		status, ctrlAuthority = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
		if ctrlAuthority: 
			status, doSplayMid = mnsUtils.validateAttrAndGet(rootGuide, "doSplayMid", False)
			status, selfCtrl = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
			selfCtrl = mnsUtils.validateNameStd(selfCtrl)
			
			if selfCtrl:
				slaves = mnsUtils.splitEnumToStringList("slaveModules", rootGuide.node)
				slaves = filterValidSlaves(slaves, mansur)

				if slaves:
					status, flipRightX = mnsUtils.validateAttrAndGet(rootGuide, "flipRightX", False)
					status, flipRightY = mnsUtils.validateAttrAndGet(rootGuide, "flipRightY", False)
					status, flipRightZ = mnsUtils.validateAttrAndGet(rootGuide, "flipRightZ", False)

					#divider
					mnsUtils.addAttrToObj([selfCtrl], type = "enum", value = ["______"], name = "splayASettings", replace = True, locked = True)

					splayATranslateMDs = []
					splayARotateMDs = []
					splayAModGrps = []

					#mulpliers
					for k, ctrlAuthority in enumerate(slaves):
						splayAModGrp = mnsUtils.createOffsetGroup(ctrlAuthority, type = "modifyGrp")
						splayAModGrps.append(splayAModGrp)

						attrName = "splayMultiplier" + mnsUtils.convertIntToAlpha(k)
						attrValue = (1.0 / float(len(slaves) - 1)) * float(k)
						multAttr = mnsUtils.addAttrToObj([selfCtrl], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]

						for channel in "tr":
							mdNode = None
							if not doSplayMid:
								mdNode = mnsNodes.mdNode([selfCtrl.node.attr(channel + "x"), selfCtrl.node.attr(channel + "y"), selfCtrl.node.attr(channel + "z")], 
											[multAttr, multAttr, multAttr],
											splayAModGrp.node.attr(channel),
											side = ctrlAuthority.side, 
											body = ctrlAuthority.body + "splayA" + channel, 
											alpha = ctrlAuthority.alpha, 
											id = ctrlAuthority.id)
								
							else:
								mdNode = mnsNodes.mdNode([selfCtrl.node.attr(channel + "x"), selfCtrl.node.attr(channel + "y"), selfCtrl.node.attr(channel + "z")], 
											[multAttr, multAttr, multAttr],
											None,
											side = ctrlAuthority.side, 
											body = ctrlAuthority.body + "splay" + channel, 
											alpha = ctrlAuthority.alpha, 
											id = ctrlAuthority.id)

							if flipRightX:
								mnsNodes.mdlNode(selfCtrl.node.attr(channel + "x"), 
										-1.0,
										mdNode.node.input1X,
										side = ctrlAuthority.side, 
										body = ctrlAuthority.body + "splayA" + channel, 
										alpha = ctrlAuthority.alpha, 
										id = ctrlAuthority.id)

							if flipRightY:
								mnsNodes.mdlNode(selfCtrl.node.attr(channel + "y"), 
										-1.0,
										mdNode.node.input1Y,
										side = ctrlAuthority.side, 
										body = ctrlAuthority.body + "splayA" + channel, 
										alpha = ctrlAuthority.alpha, 
										id = ctrlAuthority.id)
							
							if flipRightZ:
								mnsNodes.mdlNode(selfCtrl.node.attr(channel + "z"), 
										-1.0,
										mdNode.node.input1Z,
										side = ctrlAuthority.side, 
										body = ctrlAuthority.body + "splayA" + channel, 
										alpha = ctrlAuthority.alpha, 
										id = ctrlAuthority.id)
									
							if channel == "t": splayATranslateMDs.append(mdNode)
							else: splayARotateMDs.append(mdNode)

					#mid splay
					if doSplayMid:
						host = None
						for ctrl in MnsBuildModule.controls["primaries"]:
							if rootGuide.body + "Mid" == ctrl.body:
								host = ctrl
								break

						if host:
							#divider
							mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "midSettings", replace = True, locked = True)

							#mulpliers
							midParameter = 0.5

							rotEnum = 0
							tranEnum = 0

							for k, ctrlAuthority in enumerate(slaves):
								fltK = float(k)
								attrName = "MidMultiplier" + mnsUtils.convertIntToAlpha(k)
								attrValuePure = (1.0 / float(len(slaves) - 1)) * fltK
								attrValue = abs(midParameter - attrValuePure)

								multAttr = mnsUtils.addAttrToObj([host], type = "float", value = attrValue, name = attrName, replace = True, min = 0.0, max = 1.0)[0]


								for j,channel in enumerate("tr"):
									mdNode = mnsNodes.mdNode(host.node.attr(channel), 
															[multAttr, multAttr, multAttr],
															None,
															side = ctrlAuthority.side, 
															body = ctrlAuthority.body + "splayAMid" + channel, 
															alpha = ctrlAuthority.alpha, 
															id = ctrlAuthority.id)


									if attrValuePure > midParameter:
										mdNode = mnsNodes.mdNode(mdNode.node.output, 
																[-1.0, -1.0, -1.0],
																None,
																side = ctrlAuthority.side, 
																body = ctrlAuthority.body + "splayMid" + channel, 
																alpha = ctrlAuthority.alpha, 
																id = ctrlAuthority.id)

									sourceNode = None
									if channel == "t":
										sourceNode = splayATranslateMDs[tranEnum]
										tranEnum += 1
									else:
										sourceNode = splayARotateMDs[rotEnum]
										rotEnum += 1

									pmaNode = mnsNodes.pmaNode(None, None, [sourceNode.node.output, mdNode.node.output],
																None, None, splayAModGrps[k].node.attr(channel),
																side = ctrlAuthority.side, 
																body = ctrlAuthority.body, 
																alpha = ctrlAuthority.alpha, 
																id = ctrlAuthority.id)