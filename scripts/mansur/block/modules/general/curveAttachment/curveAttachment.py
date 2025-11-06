"""Author: Asaf Ben-Zur
Best used for: Sliding doors, curtains
This is a simple module that allows a control attachment to a given curve.
The attachment can also be created with an offset to current position, as well as some attachment modes and up modes.
Use this module in case you need to attach a control or joint to a curve 
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

	channelControlList = mnsUtils.splitEnumAttrToChannelControlList("channelControl", MnsBuildModule.rootGuide.node)
	status, controlShape = mnsUtils.validateAttrAndGet(rootGuide, "masterControlShape", "arrow")
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

	status, attachmentCurve = mnsUtils.validateAttrAndGet(rootGuide, "attachmentCurve", None)
	if attachmentCurve:
		attachmentCurve = mnsUtils.checkIfObjExistsAndSet(attachmentCurve)
		
		if attachmentCurve and attachmentCurve.getShape() and type(attachmentCurve.getShape()) == pm.nodetypes.NurbsCurve:
			upMode = 6

			upCurve = None
			status, attachmentUpCurve = mnsUtils.validateAttrAndGet(rootGuide, "attachmentUpCurve", None)
			attachmentUpCurve = mnsUtils.checkIfObjExistsAndSet(attachmentUpCurve)
			if attachmentUpCurve and attachmentUpCurve.getShape() and type(attachmentUpCurve.getShape()) == pm.nodetypes.NurbsCurve:
				upCurve = attachmentUpCurve
				upMode = 1
			status, attachmentMode = mnsUtils.validateAttrAndGet(rootGuide, "attachmentMode", 0)
			
			pocn = mnsNodes.mnsPointsOnCurveNode(
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body + "Attachment", 
												inputCurve = attachmentCurve,
												inputUpCurve = upCurve,
												buildOutputs = True,
												buildMode = attachmentMode,
												aimAxis = 1,
												upAxis = 0,
												numOutputs = 2,
												doScale = False,
												upMode = upMode
												)
			blkUtils.getGlobalScaleAttrFromTransform(animGrp) >> pocn["node"].node.globalScale

			if upMode == 6:
				animGrp.node.worldMatrix[0] >> pocn["node"].node.upObject
				status, objectOrientUpAxis = mnsUtils.validateAttrAndGet(rootGuide, "objectOrientUpAxis", 0)
				pocn["node"].node.objectOrientUpAxis.set(objectOrientUpAxis)

			samples = pocn["samples"]
			pm.delete(samples[1])
			primarySample = samples[0]
			pm.parent(primarySample, rigComponentsGrp.node)

			#contraint slave to sample
			slaveModGrp = mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp")
			status, maintainOffset = mnsUtils.validateAttrAndGet(rootGuide, "maintainOffset", True)
			mnsNodes.mnsMatrixConstraintNode(sources = [primarySample], targets = [slaveModGrp.node], connectRotate = True, connectTranslate = True, connectScale = False, maintainOffset = maintainOffset)

			#create extra channels
			host = ctrl
			mnsUtils.addAttrToObj([host], type = "enum", value = ["______"], name = "Attachment", replace = True)

			
			uOffset = mnsUtils.addAttrToObj([host], type = "float", value = 0.0, min = 0.0, max = 10.0, name = "uOffset", replace = True)[0]

			maxV = float(attachmentCurve.getShape().numSpans())

			
			if attachmentMode == 1:
				maxV = pocn["node"].node.fixedLength.get()
				globalScaleMult = mnsNodes.mdlNode(maxV, blkUtils.getGlobalScaleAttrFromTransform(animGrp))
				maxV = globalScaleMult.node.output

			setRangeNode = mnsNodes.setRangeNode(maxIn = [maxV,0.0,0.0], 
													minIn = [0.0,0.0,0.0], 
													oldMax = [10.0, 0.0, 0.0], 
													oldMin = [0.0, 0.0,0.0], 
													value = [uOffset, None,None], 
													outValue = [pocn["node"].node.uOffset,None,None],
													side = ctrl.side, 
													body = ctrl.body, 
													alpha = ctrl.alpha, 
													id = ctrl.id)

	########### Transfer Authority ###########
	if relatedJnt: 
		blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl, maintainOffset = False)

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, ctrl, ctrl