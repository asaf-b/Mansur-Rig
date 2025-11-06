"""Author: Asaf Ben-Zur
Best used for: Clumps of controls. i.e. the first layer of controls in a clump of 5 hair strands (FK chains).
This module was developed to allow a local control driver, over clumps of controls.
For example, a block rig contains 10 hair strands, controled by 10 FK-Shain modules, with 3 controls each.
In some cases it is easier to pose the hair treting it as a single unit instead of indevidual strands.
So, a clump-control can be created for each layer of controls (3, 1 for every unit in each chain).
The control will be created using local channels in order to not break the FK behaviour of the strands.
In case any other method was used (spaces, module parenting), each indevidual strand FK behaviour would have been broken.
The clump controls can also be parented under one another to create a layered-FK behaviour.
This will result in a main clump-fk chain, treating the hair as a single unit, and FK chains below to tread each strand indevidually.

In case you want to mimic a normal parenting behaviour, use the conformPivot attribute, which will conform all local driven controls to the pivot of this master clump control.
Leaving conformPivot OFF, will simply connect to the local channels of the slave, leaving its pivots intact. This will result in a slightly different behaviour.
You can also use connectToChannelControl attribute to decide which attributes you want to connect to, and the ones you want to leave out.
"""



from maya import cmds
import pymel.core as pm


def filterValidClumpSlaves(slavesList = [], mansur = None):
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

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	offsetRigMaster = relatedJnt
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
								createOffsetGrp = True,
								chennelControl = channelControlList,
								isFacial = MnsBuildModule.isFacial,
								offsetRigMaster = offsetRigMaster)
	ctrlsCollect.append(ctrl)

	########### Transfer Authority ###########
	status, createJoint = mnsUtils.validateAttrAndGet(rootGuide, "createJoint", True)

	if createJoint and relatedJnt: 
		blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)
	else:
		attr = mnsUtils.addAttrToObj([ctrl.node], type = "message", name = "guideAuthority", value= rootGuide.node, replace = True)[0]
		attr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "ctrlAuthority", value= ctrl.node, replace = True)[0]

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, ctrl, ctrl

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		status, ctrlAuthority = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
		if ctrlAuthority: 
			status, conformPivot = mnsUtils.validateAttrAndGet(rootGuide, "conformPivot", True)
			connectToChannelControl = mnsUtils.splitEnumAttrToChannelControlList("connectToChannelControl", MnsBuildModule.rootGuide.node)

			clumpSlaves = mnsUtils.splitEnumToStringList("clumpSlaves", rootGuide.node)
			clumpSlaves = filterValidClumpSlaves(clumpSlaves, mansur)
			if clumpSlaves:
				status, flipRightTX = mnsUtils.validateAttrAndGet(rootGuide, "flipRightTX", False)
				status, flipRightTY = mnsUtils.validateAttrAndGet(rootGuide, "flipRightTY", False)
				status, flipRightTZ = mnsUtils.validateAttrAndGet(rootGuide, "flipRightTZ", False)
				status, flipRightRX = mnsUtils.validateAttrAndGet(rootGuide, "flipRightRX", False)
				status, flipRightRY = mnsUtils.validateAttrAndGet(rootGuide, "flipRightRY", False)
				status, flipRightRZ = mnsUtils.validateAttrAndGet(rootGuide, "flipRightRZ", False)
				status, flipRightSX = mnsUtils.validateAttrAndGet(rootGuide, "flipRightSX", False)
				status, flipRightSY = mnsUtils.validateAttrAndGet(rootGuide, "flipRightSY", False)
				status, flipRightSZ = mnsUtils.validateAttrAndGet(rootGuide, "flipRightSZ", False)

				flipSettingsMap = {
								"tx": flipRightTX,
								"ty": flipRightTY,
								"tz": flipRightTZ,
								"rx": flipRightRX,
								"ry": flipRightRY,
								"rz": flipRightRZ,
								"sx": flipRightSX,
								"sy": flipRightSY,
								"sz": flipRightSZ
				}

				for clumpSlave in clumpSlaves:
					clumpSlave = mnsUtils.validateNameStd(clumpSlave)
					localModGrp = mnsUtils.createOffsetGroup(clumpSlave, type = "modifyGrp")
					
					if conformPivot:
						targetRP = pm.xform(ctrlAuthority, q = True, rotatePivot = True, ws = True)
						pm.xform(localModGrp.node, rotatePivot = targetRP, ws = True)
					
					for channel in "trs":
						axisList = "xyz"
						for axisId in range(3):
							axis = axisList[axisId]
							if connectToChannelControl[channel][axisId]: 
								isFlip = flipSettingsMap[channel + axis]

								if clumpSlave.side == "r" and isFlip:
									mnsNodes.mdlNode(ctrlAuthority.attr(channel + axis), -1.0, localModGrp.node.attr(channel + axis))
								else:
									ctrlAuthority.attr(channel + axis) >> localModGrp.node.attr(channel + axis)

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

		if rootGuide.node.hasAttr("messageOut"):
			ndr = rootGuide.node.attr("messageOut").get()
			if ndr: pm.delete(ndr)

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