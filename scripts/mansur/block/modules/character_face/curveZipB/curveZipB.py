"""Author: Asaf Ben-Zur
Best used for: Eyelids, Eyelashes
This facial module was created to allow adavnced control over eyelids and eyelashes.
Based on settings, this module will create a very flexible control over eyelids, and if choosen (Attachment Curves) to eyelashes on top of the eyelids as well.
The main features of this modules are: Joint positions based on a center matrix (Around the eye), Blink controls, Blink height control, Eyelid tweak controls (dynamic), Zip controls, and much more.
The joint structure of this module will be dictated by input vertices on a given mesh.
Note: Please select upper and lower vertices along a single closed loop
"""



from maya import cmds
import pymel.core as pm


def createTangentsForCtrl(mansur, MnsBuildModule, ctrl, btcNode, cornerACtrl, cornerBCtrl, nameID, doCornerTangents, mainCtrl):
	########### local library imports ###########
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes

	modScale = blkUtils.getModuleScale(MnsBuildModule)
	animGrp = MnsBuildModule.animGrp

	builtCtrls = []
	tanACtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
										bodySuffix = "TangentA",
										controlShape = "lightSphere",
										scale = modScale * 0.05, 
										blkCtrlTypeID = 0,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = ctrl.node,
										createOffsetGrp = True,
										createSpaceSwitchGroup = False,
										parentNode = ctrl,
										isFacial = MnsBuildModule.isFacial
										)
	builtCtrls.append(tanACtrl)
	mnsUtils.lockAndHideTransforms(tanACtrl.node, tx = False, ty = False, tz = False, lock = True)

	tanBCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
										bodySuffix = nameID + "Tangent",
										controlShape = "lightSphere",
										scale = modScale * 0.05, 
										blkCtrlTypeID = 0,
										color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
										matchTransform = ctrl.node,
										createOffsetGrp = True,
										createSpaceSwitchGroup = False,
										parentNode = ctrl,
										isFacial = MnsBuildModule.isFacial
										)
	builtCtrls.append(tanBCtrl)
	mnsUtils.lockAndHideTransforms(tanBCtrl.node, tx = False, ty = False, tz = False, lock = True)

	cornerTanA, cornerTanB = None, None

	if doCornerTangents:
		cornerTanA = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = nameID + "TangentA",
											controlShape = "lightSphere",
											scale = modScale * 0.05, 
											blkCtrlTypeID = 0,
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = cornerACtrl.node,
											createOffsetGrp = True,
											createSpaceSwitchGroup = False,
											parentNode = cornerACtrl,
											isFacial = MnsBuildModule.isFacial
											)
		builtCtrls.append(cornerTanA)
		mnsUtils.lockAndHideTransforms(cornerTanA.node, tx = False, ty = False, tz = False, lock = True)

		cornerTanB = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
											bodySuffix = nameID + "TangentB",
											controlShape = "lightSphere",
											scale = modScale * 0.05, 
											blkCtrlTypeID = 0,
											color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
											matchTransform = cornerBCtrl.node,
											createOffsetGrp = True,
											createSpaceSwitchGroup = False,
											parentNode = cornerBCtrl,
											isFacial = MnsBuildModule.isFacial
											)
		builtCtrls.append(cornerTanB)
		mnsUtils.lockAndHideTransforms(tanBCtrl.node, tx = False, ty = False, tz = False, lock = True)

	#tanVis
	tanVisAttr = mnsUtils.addAttrToObj([ctrl.node], type = "bool", value = False, name = "tangentVis", replace = True)[0]
	for tanCtrl in [tanACtrl, tanBCtrl]:
		for shape in tanCtrl.node.getShapes(): tanVisAttr >> shape.v

	if doCornerTangents:
		if not cornerACtrl.node.hasAttr("tangentVis"):
			mnsUtils.addAttrToObj([cornerACtrl.node], type = "bool", value = False, name = "tangentVis", replace = True)
			mnsUtils.addAttrToObj([cornerBCtrl.node], type = "bool", value = False, name = "tangentVis", replace = True)

		for shape in cornerTanA.node.getShapes(): cornerACtrl.node.attr("tangentVis") >> shape.v
		for shape in cornerTanB.node.getShapes(): cornerBCtrl.node.attr("tangentVis") >> shape.v

	#tan position
	numOutputs = 5
	if doCornerTangents: numOutputs = 7

	tempPocn = mnsNodes.mnsPointsOnCurveNode(inputCurve = btcNode["node"].node.outCurve,
											inputUpCurve = btcNode["node"].node.outOffsetCurve,
											buildOutputs = False,
											buildMode = 1,
											aimAxis = 1,
											upAxis = 0,
											doRotate = False,
											numOutputs = numOutputs,
											doScale = False
											)

	tempLoc = pm.createNode("transform")
	tempPocn["node"].node.transforms[((numOutputs - 1) / 2) - 1].translate >> tempLoc.t
	tempPocn["node"].node.transforms[1].rotate >> tempLoc.r
	pm.delete(pm.parentConstraint(tempLoc, blkUtils.getOffsetGrpForCtrl(tanACtrl).node))
	blkUtils.getOffsetGrpForCtrl(tanACtrl).node.r.set((0,0,0))

	tempPocn["node"].node.transforms[((numOutputs - 1) / 2) + 1].translate >> tempLoc.t
	tempPocn["node"].node.transforms[3].rotate >> tempLoc.r
	pm.delete(pm.parentConstraint(tempLoc, blkUtils.getOffsetGrpForCtrl(tanBCtrl).node))
	blkUtils.getOffsetGrpForCtrl(tanBCtrl).node.r.set((0,0,0))

	if doCornerTangents:
		tempPocn["node"].node.transforms[3].translate >> tempLoc.t
		#tempPocn["node"].node.transforms[3].rotate >> tempLoc.r
		pm.delete(pm.parentConstraint(tempLoc, blkUtils.getOffsetGrpForCtrl(cornerTanA).node))
		blkUtils.getOffsetGrpForCtrl(cornerTanA).node.tz.set(0)
		blkUtils.getOffsetGrpForCtrl(cornerTanA).node.tx.set(0)
		blkUtils.getOffsetGrpForCtrl(cornerTanA).node.r.set((0,0,0))

		tempPocn["node"].node.transforms[5].translate >> tempLoc.t
		#tempPocn["node"].node.transforms[3].rotate >> tempLoc.r
		pm.delete(pm.parentConstraint(tempLoc, blkUtils.getOffsetGrpForCtrl(cornerTanB).node))
		blkUtils.getOffsetGrpForCtrl(cornerTanB).node.tz.set(0)
		blkUtils.getOffsetGrpForCtrl(cornerTanB).node.tx.set(0)
		blkUtils.getOffsetGrpForCtrl(cornerTanB).node.r.set((0,0,0))

	tempPocn["node"].node.curve.disconnect()
	tempPocn["node"].node.upCurve.disconnect()
	pm.delete(tempPocn["node"].node, tempLoc)

	#create base locs from mid tangents
	midBaseGrp = mnsUtils.createNodeReturnNameStd(parentNode = mainCtrl, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "TweakBase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
	midBaseGrp.node.v.set(False)

	tanABaseLoc = mnsUtils.createNodeReturnNameStd(parentNode = midBaseGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "tanABase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	tanABaseLoc.node.v.set(False)
	pm.delete(pm.parentConstraint(tanACtrl.node, tanABaseLoc.node))
	pointCns = mnsNodes.mayaConstraint([ctrl.node], tanABaseLoc.node, type = "point", maintainOffset = True)

	tanBBaseLoc = mnsUtils.createNodeReturnNameStd(parentNode = midBaseGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "tanBBase", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
	tanBBaseLoc.node.v.set(False)
	pm.delete(pm.parentConstraint(tanBCtrl.node, tanBBaseLoc.node))
	pointCns = mnsNodes.mayaConstraint([ctrl.node], tanBBaseLoc.node, type = "point", maintainOffset = True)

	cornerTanABaseLoc, cornerTanBBaseLoc = None, None
	if doCornerTangents:
		cornerTanABaseLoc = mnsUtils.createNodeReturnNameStd(parentNode = midBaseGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + nameID + "TangentA", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		cornerTanABaseLoc.node.v.set(False)
		pm.delete(pm.parentConstraint(cornerTanA.node, cornerTanABaseLoc.node))
		pointCns = mnsNodes.mayaConstraint([cornerACtrl.node], cornerTanABaseLoc.node, type = "point", maintainOffset = True)

		cornerTanBBaseLoc = mnsUtils.createNodeReturnNameStd(parentNode = midBaseGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + nameID + "TangentB", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "locator", incrementAlpha = False)
		cornerTanBBaseLoc.node.v.set(False)
		pm.delete(pm.parentConstraint(cornerTanB.node, cornerTanBBaseLoc.node))
		pointCns = mnsNodes.mayaConstraint([cornerBCtrl.node], cornerTanBBaseLoc.node, type = "point", maintainOffset = True)


	baseTransforms = [cornerACtrl, tanABaseLoc, ctrl, tanBBaseLoc, cornerBCtrl]
	if doCornerTangents: baseTransforms = [cornerACtrl, cornerTanABaseLoc, tanABaseLoc, ctrl, tanBBaseLoc, cornerTanBBaseLoc, cornerBCtrl]

	tanTweakBaseBtc = mnsNodes.mnsBuildTransformsCurveNode(
										side = MnsBuildModule.rootGuide.side, 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										body = MnsBuildModule.rootGuide.body + "TanTweakBase", 
										transforms = baseTransforms, 
										deleteCurveObjects = True, 
										tangentDirection = 1, 
										buildOffsetCurve = False,
										buildMode = 0,
										degree = 3,
										offsetX = 0.0,
										offsetY = 0.0,
										offsetZ = 0.0)
	blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> tanTweakBaseBtc["node"].node.globalScale
	
	tweakTransforms = [cornerACtrl, tanACtrl, ctrl, tanBCtrl, cornerBCtrl]
	if doCornerTangents: tweakTransforms = [cornerACtrl, cornerTanA, tanACtrl, ctrl, tanBCtrl, cornerTanB, cornerBCtrl]

	tanTweakBtc = mnsNodes.mnsBuildTransformsCurveNode(
										side = MnsBuildModule.rootGuide.side, 
										alpha = MnsBuildModule.rootGuide.alpha, 
										id = MnsBuildModule.rootGuide.id, 
										body = MnsBuildModule.rootGuide.body + "TanTweak", 
										transforms = tweakTransforms, 
										deleteCurveObjects = True, 
										tangentDirection = 1, 
										buildOffsetCurve = False,
										buildMode = 0,
										degree = 3,
										offsetX = 0.0,
										offsetY = 0.0,
										offsetZ = 0.0)
	blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> tanTweakBtc["node"].node.globalScale

	btcNode["node"].node.resample.set(True)
	btcNode["node"].node.substeps.set(numOutputs)
	tanTweakBaseBtc["node"].node.outCurve >> btcNode["node"].node.tweakCurveBase
	tanTweakBtc["node"].node.outCurve >> btcNode["node"].node.tweakCurve

def getEdgesFromModuleSettings(mansur, rootGuide = None):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import string as mnsString

	upperEdge, lowerEdge = None, None

	if rootGuide:
		status, upperEdge = mnsUtils.validateAttrAndGet(rootGuide, "upperEdgeVerts", "")
		status, lowerEdge = mnsUtils.validateAttrAndGet(rootGuide, "lowerEdgeVerts", "")

		upperEdgeVerts, lowerEdgeVerts =  None, None

		if upperEdge: upperEdgeVerts = mnsString.splitStringToArray(upperEdge)
		if lowerEdge: lowerEdgeVerts = mnsString.splitStringToArray(lowerEdge)

		if upperEdgeVerts and lowerEdgeVerts:
			upperEdgeMesh = mnsUtils.checkIfObjExistsAndSet(upperEdgeVerts[0].split(".")[0])
			lowerEdgeMesh = mnsUtils.checkIfObjExistsAndSet(lowerEdgeVerts[0].split(".")[0])

			if upperEdgeMesh and lowerEdgeMesh:
				upperEdgeMeshVtxCount = pm.polyEvaluate(upperEdgeMesh, v = True)
				lowerEdgeMesVtxCount = pm.polyEvaluate(lowerEdgeMesh, v = True)

				upperEdge, lowerEdge = [], [] 
				for upperVert in upperEdgeVerts:
					vertIdx =  int(upperVert.split("[")[-1].split("]")[0])
					if vertIdx < upperEdgeMeshVtxCount: upperEdge.append(upperEdgeMesh.vtx[vertIdx])

				for lowerVert in lowerEdgeVerts:
					vertIdx =  int(lowerVert.split("[")[-1].split("]")[0])
					if vertIdx < lowerEdgeMesVtxCount: lowerEdge.append(lowerEdgeMesh.vtx[vertIdx])
	return upperEdge, lowerEdge

def createBindCurvesFromModuleSettings(mansur, rootGuide = None):
	#internal Imports
	from mansur.core import utility as mnsUtils

	bindCurves = [None, None]
	upperEdge, lowerEdge = None, None

	if rootGuide:
		upperEdge, lowerEdge = getEdgesFromModuleSettings(mansur, rootGuide)
		if upperEdge and lowerEdge:
			#create bindCurves
			for k, inputVertArray in enumerate([upperEdge, lowerEdge]):
				edges = pm.polyListComponentConversion(inputVertArray, fv=True, te=True, internal=True) 
				if not edges:
					shapeNode = pm.ls(inputVertArray[0], o=True)
					if shapeNode:
						transformNode = shapeNode[0].getParent()
						if transformNode:
							shapes = transformNode.getShapes()
							if len(shapes) > 1:
								for s in shapes:
									if not s == shapeNode[0]:
										newShapeNode = s
										inputVertArray = [v.replace(shapeNode[0].nodeName(), newShapeNode.nodeName()) for v in inputVertArray]
										edges = pm.polyListComponentConversion(inputVertArray, fv=True, te=True, internal=True)
										break
				if edges:
					pm.select(edges, replace = True)
					curve = pm.polyToCurve(form = 0, degree = 3, ch = False, conformToSmoothMeshPreview = False)
					if curve:
						curve = mnsUtils.checkIfObjExistsAndSet(curve[0]) 
						bindCurves[k] = curve

			#check curves direction. if invalid, flip
			if bindCurves[0] and bindCurves[1]:
				upperCvs = bindCurves[0].getShape().getCVs()
				lowerCvs = bindCurves[1].getShape().getCVs()
				
				if rootGuide.side == "r":
					if upperCvs[-1].x < upperCvs[0].x: pm.reverseCurve(bindCurves[0], ch= False, rpo = True)
					if lowerCvs[-1].x < lowerCvs[0].x: pm.reverseCurve(bindCurves[1], ch= False, rpo = True)
				else:
					if upperCvs[0].x < upperCvs[-1].x: pm.reverseCurve(bindCurves[0], ch= False, rpo = True)
					if lowerCvs[0].x < lowerCvs[-1].x: pm.reverseCurve(bindCurves[1], ch= False, rpo = True)

	return bindCurves, upperEdge, lowerEdge

def construct(mansur, MnsBuildModule, **kwargs):
	########### local library imports ###########
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core.prefixSuffix import MnsNameStd
	from mansur.core.prefixSuffix import mnsTypeDict

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
	#create main ctrl
	mainCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
							color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
							matchTransform = rootGuide.node,
							controlShape = "square",
							scale = modScale, 
							parentNode = animGrp,
							symmetryType = symmetryType,
							createSpaceSwitchGroup = True,
							createOffsetGrp = True,
							doMirror = True,
							isFacial = MnsBuildModule.isFacial)
	ctrlsCollect.append(mainCtrl)
	mnsUtils.lockAndHideTransforms(mainCtrl.node, rx = False, ry = False, rz = False, lock = True)

	# first recreare the curve.
	curveGrp = mnsUtils.createNodeReturnNameStd(parentNode = mainCtrl, side =  rootGuide.side, body = rootGuide.body + "Curves", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)
	curveGrp.node.v.set(False)

	bindCurves, upperEdge, lowerEdge = createBindCurvesFromModuleSettings(mansur, rootGuide)
	iLocs = []
	
	mnsCurveZipNode = None
	if bindCurves[0] and bindCurves[1]:
		nameStdA = MnsNameStd(side = rootGuide.side, body = rootGuide.body + "UpperBind", alpha = rootGuide.alpha, id = rootGuide.id, type = mnsTypeDict["curve"])
		nameStdA.findNextIncrement()
		bindCurves[0].rename(nameStdA.name)
		nameStdB = MnsNameStd(side = rootGuide.side, body = rootGuide.body + "LowerBind", alpha = rootGuide.alpha, id = rootGuide.id, type = mnsTypeDict["curve"])
		nameStdB.findNextIncrement()
		bindCurves[1].rename(nameStdB.name)
		pm.parent(bindCurves, curveGrp.node)

		status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 1.0)
		status, curveResolution = mnsUtils.validateAttrAndGet(rootGuide, "curveResolution", 24)
		mnsCurveZipNode = mnsNodes.mnsCurveZipNode(
								type = "mnsCurveZipB",
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body, 
								bindCurveA =bindCurves[0].getShape().worldSpace[0],
								bindCurveB = bindCurves[1].getShape().worldSpace[0],
								centerMatrix = mainCtrl.node.worldMatrix[0],
								upCurveOffset = upCurveOffset,
								substeps = curveResolution
								)

		blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> mnsCurveZipNode.node.globalScale

		#get existing iLocs and connect them, essentially transfer authority.
		iLocs = blkUtils.getModuleInterpJoints(rootGuide)
		if iLocs:
			iLocs = mnsUtils.sortNameStdArrayByID(iLocs)
			inputAttrSuffix = "AB"
			inputNames = ["Upper", "Lower"]
			for k, curve in enumerate(bindCurves):
				transformsArray = iLocs[0:len(upperEdge)] 
				if k  ==1 : transformsArray = iLocs[len(upperEdge):]

				pocn = mnsNodes.mnsPointsOnCurveNode(
												transforms = transformsArray,
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body + inputNames[k], 
												inputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k]),
												inputUpCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k] + "Offset"),
												buildOutputs = False,
												buildType = 4, #interpJointsType
												buildMode = 0,
												doScale = False,
												doRotate = False,
												aimAxis = 1,
												upAxis = 0,
												numOutputs = len(transformsArray),
												isolatePolesRotation = False
												)
				blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> pocn["node"].node.globalScale

		#create a temp pocns to find corner and mid positions.
		nodesToDelete = []
		cornerA, upperMid, cornerB, lowerMid = None, None, None, None

		for k, curve in enumerate(bindCurves):
			tempPocn = mnsNodes.mnsPointsOnCurveNode(side = rootGuide.side, 
													alpha = rootGuide.alpha, 
													id = rootGuide.id, 
													body = rootGuide.body + "Temp", 
													inputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k]),
													inputUpCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k] + "Offset"),
													buildOutputs = True,
													buildType = 0, #interpJointsType
													buildMode = 0,
													doScale = False,
													connectScale = False,
													doRotate = False,
													aimAxis = 1,
													upAxis = 0,
													numOutputs = 3)
			nodesToDelete.append(tempPocn["node"].node)
			for samp in tempPocn["samples"]:
				samp.t.disconnect()
				samp.r.disconnect()
				samp.s.disconnect()

			if k == 0:
				cornerA = tempPocn["samples"][0]
				cornerB = tempPocn["samples"][2]
				upperMid = tempPocn["samples"][1]
				nodesToDelete += tempPocn["samples"]
			else:
				pm.delete([tempPocn["samples"][0], tempPocn["samples"][2]])
				nodesToDelete.append(tempPocn["samples"][1])
				lowerMid = tempPocn["samples"][1]

		#create global controls
		status, rangeMinValue = mnsUtils.validateAttrAndGet(rootGuide, "raiseRange", 0.5)
		status, uiCtrlsScale = mnsUtils.validateAttrAndGet(rootGuide, "uiCtrlsScale", 0.15)

		#create remote ctrl style orient locator
		orientLoc = pm.spaceLocator()
		nodesToDelete.append(orientLoc)
		upperMidPos = pm.datatypes.Vector(pm.xform(upperMid, q = True, ws = True, t = True, a = True))
		lowerMidPos = pm.datatypes.Vector(pm.xform(lowerMid, q = True, ws = True, t = True, a = True))
		outerPos = pm.datatypes.Vector(pm.xform(cornerA, q = True, ws = True, t = True, a = True))
		innerPos = pm.datatypes.Vector(pm.xform(cornerB, q = True, ws = True, t = True, a = True))
		orientLocPos = (upperMidPos + lowerMidPos + outerPos + innerPos) / 4.0
		pm.xform(orientLoc, ws = True, a = True, t = orientLocPos)

		uiCtrlsCtrl = mnsUtils.createNodeReturnNameStd(parentNode = mainCtrl, side =  rootGuide.side, body = rootGuide.body + "UICtrls", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "ctrl", incrementAlpha = False)
		uiCtrlsGrp = mnsUtils.createOffsetGroup(uiCtrlsCtrl)
		pm.delete(pm.pointConstraint(orientLoc, uiCtrlsGrp.node))

		###Upper/Lower
		mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["______"], name = "VIS", replace = True, locked = True)
		upperLowerVisAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = True, name = "upperLower", replace = True)[0]

		alignOffsetGrps = []
		upperLidCtrl, upperLidOffsetGrp, frameCtrl = blkCtrlShps.createRemoteControlStyleCtrl(nameReference = rootGuide,
																					bodySuffix = "UpperLid",
																					side = rootGuide.side,
																					verticalMin = -1.0, 
																					verticalMax = 4.0, 
																					horizontalMin = 0.0, 
																					horizontalMax = 0.0,
																					uiScale = uiCtrlsScale * 0.9,
																					upsideDown = True,
																					isFacial = MnsBuildModule.isFacial)
		upperLowerVisAttr >> upperLidOffsetGrp.node.v
		ctrlsCollect.append(upperLidCtrl)
		ctrlsCollect.append(frameCtrl)
		alignOffsetGrps.append(upperLidOffsetGrp)
		pm.parent(upperLidOffsetGrp.node, uiCtrlsCtrl.node)
		pm.makeIdentity(upperLidOffsetGrp.node, r = False, s = False, t = True)
		pm.delete(pm.pointConstraint(upperMid, upperLidOffsetGrp.node))
		upperLidOffsetGrp.node.tx.set(0.0)
		upperLidOffsetGrp.node.tz.set(0.0)
		mnsUtils.lockAndHideTransforms(upperLidCtrl.node, tz = False, lock = True)
		mnsUtils.lockAndHideTransforms(upperLidCtrl.node, ry = False, negateOperation = True, lock = False, cb = True, keyable = True)
		upperSSetRange = mnsNodes.setRangeNode([1.0, 1.0, 1.0],
												[-1.0, -1.0, -1.0],
												[90, 90.0, 90.0],
												[-90.0, -90.0, -90.0],
												[upperLidCtrl.node.ry, None, None],
												[mnsCurveZipNode.node.sCurveA, None, None])
		pm.transformLimits(upperLidCtrl.node, ery = (True, True), ry = (-90, 90))

		toMidAttr = mnsUtils.addAttrToObj([upperLidCtrl.node], type = "float", min = 0.0, max = 1.0, value = 0.0, name = "toMid", replace = True)[0]
		toMidAttr >> mnsCurveZipNode.node.AToMid
		upperToLowerAttr = mnsUtils.addAttrToObj([upperLidCtrl.node], type = "float", min = 0.0, max = 1.0, value = 0.0, name = "upperToLower", replace = True)[0]
		upperToLowerAttr >> mnsCurveZipNode.node.AToB		

		lowerLidCtrl, lowerLidOffsetGrp, frameCtrl = blkCtrlShps.createRemoteControlStyleCtrl(nameReference = rootGuide,
																					bodySuffix = "LowerLid",
																					side = rootGuide.side,
																					verticalMin = -1.0, 
																					verticalMax = 4.0, 
																					horizontalMin = 0.0, 
																					horizontalMax = 0.0,
																					uiScale = uiCtrlsScale,
																					isFacial = MnsBuildModule.isFacial)
		upperLowerVisAttr >> lowerLidOffsetGrp.node.v
		ctrlsCollect.append(lowerLidCtrl)
		ctrlsCollect.append(frameCtrl)
		alignOffsetGrps.append(lowerLidOffsetGrp)
		pm.parent(lowerLidOffsetGrp.node, uiCtrlsCtrl.node)
		pm.makeIdentity(lowerLidOffsetGrp.node, r = False, s = False, t = True)
		pm.delete(pm.pointConstraint(lowerMid, lowerLidOffsetGrp.node))
		lowerLidOffsetGrp.node.tx.set(0.0)
		lowerLidOffsetGrp.node.tz.set(0.0)
		mnsUtils.lockAndHideTransforms(lowerLidCtrl.node, tz = False, lock = True)
		mnsUtils.lockAndHideTransforms(lowerLidCtrl.node, ry = False, negateOperation = True, lock = False, cb = True, keyable = True)
		lowerSSetRange = mnsNodes.setRangeNode([1.0, 1.0, 1.0],
												[-1.0, -1.0, -1.0],
												[90, 90.0, 90.0],
												[-90.0, -90.0, -90.0],
												[lowerLidCtrl.node.ry, None, None],
												[mnsCurveZipNode.node.sCurveB, None, None])
		pm.transformLimits(lowerLidCtrl.node, ery = (True, True), ry = (-90, 90))

		toMidAttr = mnsUtils.addAttrToObj([lowerLidCtrl.node], type = "float", min = 0.0, max = 1.0, value = 0.0, name = "toMid", replace = True)[0]
		toMidAttr >> mnsCurveZipNode.node.BToMid
		lowerToUpperAttr = mnsUtils.addAttrToObj([lowerLidCtrl.node], type = "float", min = 0.0, max = 1.0, value = 0.0, name = "lowerToUpper", replace = True)[0]
		lowerToUpperAttr >> mnsCurveZipNode.node.BToA

		setRangeNode = mnsNodes.setRangeNode([1.0, 1.0, 1.0],
												[0.0, 0.0, 0.0],
												[4.0, 4.0, 4.0],
												[0.0, 0.0, 0.0],
												[upperLidCtrl.node.tz, lowerLidCtrl.node.tz, None],
												[mnsCurveZipNode.node.AToBindB, mnsCurveZipNode.node.BToBindA])

		setRangeNodeBelowZero = mnsNodes.setRangeNode([0.0, 0.0, 0.0],
												[-rangeMinValue, -rangeMinValue, -rangeMinValue],
												[0.0, 0.0, 0.0],
												[-1.0, -1.0, -1.0],
												[upperLidCtrl.node.tz, lowerLidCtrl.node.tz, None],
												[mnsCurveZipNode.node.AToBindB, mnsCurveZipNode.node.BToBindA])


		conditionNodeA = mnsNodes.conditionNode(upperLidCtrl.node.tz, 0.0, [setRangeNodeBelowZero.node.outValueX, 0.0, 0.0], [setRangeNode.node.outValueX, 0.0, 0.0], [mnsCurveZipNode.node.AToBindB, None, None], operation = 4)
		conditionNodeB = mnsNodes.conditionNode(lowerLidCtrl.node.tz, 0.0, [setRangeNodeBelowZero.node.outValueY, 0.0, 0.0], [setRangeNode.node.outValueY, 0.0, 0.0], [mnsCurveZipNode.node.BToBindA, None, None], operation = 4)
		mnsNodes.mnsNodeRelationshipNode(connectDeleteSlavesOnly = True, side = animGrp.side, alpha = animGrp.alpha , id = animGrp.id, master = animGrp.node, slaves = [setRangeNode.node, conditionNodeA.node, conditionNodeB.node])

		###inner/outer
		status, doZipControls = mnsUtils.validateAttrAndGet(rootGuide, "doZipControls", True)
		if doZipControls:
			innerOuterVisAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = True, name = "innerOuter", replace = True)[0]

			flip = True
			if rootGuide.side == "r": flip = False

			innerLidCtrl, innerLidOffsetGrp, frameCtrl = blkCtrlShps.createRemoteControlStyleCtrl(nameReference = rootGuide,
																						bodySuffix = "Inner",
																						blkCtrlTypeID = 1,
																						verticalMin = 0.0, 
																						verticalMax = 0.0, 
																						horizontalMin = 0.0, 
																						horizontalMax = 5.0,
																						uiScale = uiCtrlsScale * 0.8,
																						flip = not(flip),
																						isFacial = MnsBuildModule.isFacial)
			innerOuterVisAttr >> innerLidOffsetGrp.node.v
			ctrlsCollect.append(innerLidCtrl)
			ctrlsCollect.append(frameCtrl)
			alignOffsetGrps.append(innerLidOffsetGrp)
			pm.parent(innerLidOffsetGrp.node, uiCtrlsCtrl.node)
			pm.makeIdentity(innerLidOffsetGrp.node, r = False, s = False, t = True)
			pm.delete(pm.pointConstraint(cornerB, innerLidOffsetGrp.node))
			innerLidOffsetGrp.node.ty.set(0.0)
			innerLidOffsetGrp.node.tz.set(0.0)
			mnsUtils.lockAndHideTransforms(innerLidCtrl.node, tx = False, lock = True)
			falloffAttr = mnsUtils.addAttrToObj([innerLidCtrl.node], type = "float", value = 0.6, min = 0.01, max = 1.0, name = "zipFalloff", replace = True)[0]
			falloffAttr >> mnsCurveZipNode.node.zipEndFalloff

			outerLidCtrl, outerLidOffsetGrp, frameCtrl = blkCtrlShps.createRemoteControlStyleCtrl(nameReference = rootGuide,
																						bodySuffix = "Outer",
																						blkCtrlTypeID = 1,
																						verticalMin = 0.0, 
																						verticalMax = 0.0, 
																						horizontalMin = 0.0, 
																						horizontalMax = 5.0,
																						uiScale = uiCtrlsScale * 0.8,
																						flip = flip,
																						isFacial = MnsBuildModule.isFacial)
			innerOuterVisAttr >> outerLidOffsetGrp.node.v
			ctrlsCollect.append(outerLidCtrl)
			ctrlsCollect.append(frameCtrl)
			pm.parent(outerLidOffsetGrp.node, uiCtrlsCtrl.node)
			pm.makeIdentity(outerLidOffsetGrp.node, r = False, s = False, t = True)
			pm.delete(pm.pointConstraint(cornerA, outerLidOffsetGrp.node))
			outerLidOffsetGrp.node.ty.set(0.0)
			outerLidOffsetGrp.node.tz.set(0.0)
			mnsUtils.lockAndHideTransforms(outerLidCtrl.node, tx = False, lock = True)
			falloffAttr = mnsUtils.addAttrToObj([outerLidCtrl.node], type = "float", value = 0.6, max = 1.0, min = 0.01, name = "zipFalloff", replace = True)[0]
			falloffAttr >> mnsCurveZipNode.node.zipStartFalloff
			pm.delete(pm.pointConstraint(outerLidOffsetGrp.node, innerLidOffsetGrp.node, sk = ["x", "z"]))

			outputArray = [mnsCurveZipNode.node.zipStart, mnsCurveZipNode.node.zipEnd]

			setRangeNode = mnsNodes.setRangeNode([1.0, 1.0, 1.0],
													[0.0, 0.0, 0.0],
													[5.0, 5.0, 5.0],
													[0.0, 0.0, 0.0],
													[outerLidCtrl.node.tx, innerLidCtrl.node.tx, None],
													outputArray
													)

			mnsNodes.mnsNodeRelationshipNode(connectDeleteSlavesOnly = True, side = animGrp.side, alpha = animGrp.alpha , id = animGrp.id, master = animGrp.node, slaves = [setRangeNode.node])

		#finalize UI pos
		aimVec = [0, 0, -1]
		if rootGuide.side == "r": aimVec = [0, 0, 1]
		pm.delete(mnsNodes.mayaConstraint([rootGuide.node], uiCtrlsGrp.node, type = "aim", aimVector = aimVec, upVector = [0.0,1.0,0.0], maintainOffset = False, worldUpObject = upperMid).node)
		status, uiCtrlsPositionOffset = mnsUtils.validateAttrAndGet(rootGuide, "uiCtrlsPositionOffset", 1.0)
		pm.move(uiCtrlsGrp.node, (0.0, 0.0, uiCtrlsPositionOffset), r = True, os = True, wd = True)

		try: pm.delete(nodesToDelete)
		except: pass

		#create tweak controls
		status, doTweakControls = mnsUtils.validateAttrAndGet(rootGuide, "doTweakControls", True)
		corners = []

		if doTweakControls:
			status, numTweakControlsPerSection = mnsUtils.validateAttrAndGet(rootGuide, "numTweakControlsPerSection", 3)
			status, cornersControlShape = mnsUtils.validateAttrAndGet(rootGuide, "cornersControlShape", "diamond")
			status, tweakersControlShape = mnsUtils.validateAttrAndGet(rootGuide, "tweakersControlShape", "lightSphere")
			status, doTweakTangents = mnsUtils.validateAttrAndGet(rootGuide, "doTweakTangents", False)
			status, tweakCurvesInterpolation = mnsUtils.validateAttrAndGet(rootGuide, "tweakCurvesInterpolation", 2)
			status, flipRightX = mnsUtils.validateAttrAndGet(rootGuide, "flipRightX", False)
			status, flipRightY = mnsUtils.validateAttrAndGet(rootGuide, "flipRightY", False)
			status, flipRightZ = mnsUtils.validateAttrAndGet(rootGuide, "flipRightZ", False)

			mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["______"], name = "TWEAKERS", replace = True, locked = True)
			tweakCurvesInterpolationAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["EPs", "CVs"], name = "tweakersMode", enumDefault = tweakCurvesInterpolation, replace = True)[0]
			tweakCurvesInterpolationAttr >> mnsCurveZipNode.node.tweakMode

			namesArray = ["upper", "lower"]

			midIndex = 0
			if (numTweakControlsPerSection % 2) != 0: midIndex = ((numTweakControlsPerSection + 1) / 2) - 1
			
			for k, curve in enumerate(bindCurves):
				#create a parentGrp at origin
				tweakCtrlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  rootGuide.side, body = rootGuide.body + namesArray[k].capitalize() + "TweakCtrls", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)
				mirGrpMat = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  rootGuide.side, body = rootGuide.body + namesArray[k].capitalize() + "MirrorMatrix", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)

				tweakControls = []
				for j in range(numTweakControlsPerSection):
					isCorner = False
					if j == 0 or j == numTweakControlsPerSection - 1: isCorner = True

					controlShape = tweakersControlShape
					bodySuffix = namesArray[k].capitalize() + "Tweak"
					if isCorner: 
						controlShape = cornersControlShape
						bodySuffix = "Corner"

					ctrlT = "ctrl"
					if k == 1 and isCorner: ctrlT = "techCtrl"

					#create control
					tweakCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
							color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
							bodySuffix = bodySuffix,
							ctrlType = ctrlT,
							controlShape = controlShape,
							scale = modScale * 0.1, 
							parentNode = tweakCtrlsGrp,
							symmetryType = symmetryType,
							doMirror = True,
							createSpaceSwitchGroup = False,
							createOffsetGrp = True,
							isFacial = MnsBuildModule.isFacial)

					tweakOffset = blkUtils.getOffsetGrpForCtrl(tweakCtrl)
					mirGrp = blkUtils.getOffsetGrpForCtrl(tweakCtrl, type = "mirrorScaleGroup")
					mnsNodes.mayaConstraint(mainCtrl.node, tweakOffset.node, type = "scale")

					tweakControls.append(tweakCtrl)

					mnsUtils.lockAndHideTransforms(tweakCtrl.node, tx = False, ty = False, tz = False, lock = True)

					if rootGuide.side == "r":
						if flipRightX or flipRightY or flipRightZ:
							modGrp = mnsUtils.createOffsetGroup(tweakCtrl, type = "modifyGrp")
							if flipRightX: modGrp.node.sx.set(-1)
							if flipRightY: modGrp.node.sy.set(-1)
							if flipRightZ: modGrp.node.sz.set(-1)

					if k ==0 and j == 0:
						if mirGrp:
							mirGrpMat.node.r.set(mirGrp.node.r.get())
							mirGrpMat.node.s.set(mirGrp.node.s.get())

						mirGrpMat.node.matrix >> mnsCurveZipNode.node.tweakMirrorMatrix

					if k == 0: 
						tweakCtrl.node.matrix >> mnsCurveZipNode.node.inTweakAPosition[j]
						mnsCurveZipNode.node.outTweakA[j].outTweakATranslate >> tweakOffset.node.t
						mnsCurveZipNode.node.outTweakA[j].outTweakARotate >> tweakOffset.node.r
					else: 
						tweakCtrl.node.matrix >> mnsCurveZipNode.node.inTweakBPosition[j]
						mnsCurveZipNode.node.outTweakB[j].outTweakBTranslate >> tweakOffset.node.t
						mnsCurveZipNode.node.outTweakB[j].outTweakBRotate >> tweakOffset.node.r

					if k == 0 and isCorner: corners.append(tweakCtrl)
					ctrlsCollect.append(tweakCtrl)

					if k == 1 and isCorner: 
						pm.delete(tweakCtrl.node.getShapes())

						masterCon = corners[0]
						if j != 0: masterCon = corners[1]
						masterCon.node.t >> tweakCtrl.node.t
						masterCon.node.r >> tweakCtrl.node.r
						masterCon.node.s >> tweakCtrl.node.s
					
	###attachmentCurves
	inputNames = ["Upper", "Lower"]
	for inputName in inputNames:
		status, origAttachPoc = mnsUtils.validateAttrAndGet(rootGuide, "orig" + inputName + "Attach", None)
		if origAttachPoc:
			blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> origAttachPoc.globalScale
				

			#store original cGuide
			cgCtrl = origAttachPoc.uScale.listConnections(d = True, s = True)
			if cgCtrl:
				attchCGuideAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = inputName + "AttachCGuide", value= "", replace = True)[0] 
				cgCtrl = cgCtrl[0]
				cgCtrl.message >> attchCGuideAttr

			#store previous values
			uScaleValue = origAttachPoc.uScale.get()
			uOffsetVale = origAttachPoc.uOffset.get()
			tugOffsetValue = origAttachPoc.uTugOffset.get()
			tugScaleValue = origAttachPoc.uTugScale.get()
			uScaleInvValue = origAttachPoc.uScaleMidInverse.get()

			numOutputs = origAttachPoc.numOutputs.get()
			baseIndex = 0
			midIndex = int(float(numOutputs) / 2.0)
			tipIndex = numOutputs - 1

			#create ctrls
			attachCtrlAll = None
			attachmentCtrlsDict = {inputName + "AttachmentBase": {"ctrl": None, "idx": baseIndex}, inputName + "AttachmentMid": {"ctrl": None, "idx": midIndex}, inputName + "AttachmentAll": {"ctrl": None, "idx": midIndex}, inputName + "AttachmentTip": {"ctrl": None, "idx": tipIndex}}
			for attachCtrlName in attachmentCtrlsDict.keys():
				ctrlScale = modScale * 0.15
				if attachCtrlName == inputName + "AttachmentAll": ctrlScale = modScale * 0.2

				attachCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
														bodySuffix = attachCtrlName,
														controlShape = "circle",
														scale = ctrlScale, 
														blkCtrlTypeID = 1,
														color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
														createOffsetGrp = True,
														createSpaceSwitchGroup = False,
														parentNode = animStaticGrp,
														isFacial = MnsBuildModule.isFacial
														)
				attachCtrlName

				ctrlsCollect.append(attachCtrl)
				attachmentCtrlsDict[attachCtrlName].update({"ctrl": attachCtrl})

				idx = attachmentCtrlsDict[attachCtrlName]["idx"]
				modGrp = mnsUtils.createOffsetGroup(attachCtrl, type = "modifyGrp")
				origAttachPoc.transforms[idx].t >> modGrp.node.t
				origAttachPoc.transforms[idx].r >> modGrp.node.r
				origAttachPoc.transforms[idx].s >> modGrp.node.s

				if attachCtrlName == (inputName + "AttachmentTip"):
					modGrpB = mnsUtils.createOffsetGroup(attachCtrl, type = "modifyGrp")
					modGrpB.node.sy.set(-1)

				if not attachCtrlName == inputName + "AttachmentAll":
					mnsUtils.lockAndHideTransforms(attachCtrl.node, ry = False, sy = False, lock = True)
				else:
					mnsUtils.lockAndHideTransforms(attachCtrl.node, ry = False, lock = True)


			attachmentCtrlsDict[inputName + "AttachmentBase"]["ctrl"].node.ry >> origAttachPoc.twistAimStart

			attachmentCtrlsDict[inputName + "AttachmentMid"]["ctrl"].node.ry >> origAttachPoc.twistAimMid

			attachmentCtrlsDict[inputName + "AttachmentTip"]["ctrl"].node.ry >> origAttachPoc.twistAimEnd

			attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node.ry >> origAttachPoc.twistAimAll

			attachmentCtrlsDict[inputName + "AttachmentMid"]["ctrl"].node.sy >> origAttachPoc.uScaleMid
			adlNode = mnsNodes.adlNode(attachmentCtrlsDict[inputName + "AttachmentBase"]["ctrl"].node.sy, 
									uScaleValue - 1.0,
									origAttachPoc.uScale,
									side = attachCtrl.side, 
									body = attachCtrl.body, 
									alpha = attachCtrl.alpha, 
									id = attachCtrl.id)

			attachmentCtrlsDict[inputName + "AttachmentTip"]["ctrl"].node.sy >> origAttachPoc.uScaleInverse

			#re-connect attrs
			mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "enum", value = ["______"], name = "attachmentControls", replace = True, locked = True)

			offsetAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = 0.0, name = "offsetPosition", replace = True)[0]
			adlNode = mnsNodes.adlNode(offsetAttr, 
									uOffsetVale,
									origAttachPoc.uOffset,
									side = attachCtrl.side, 
									body = attachCtrl.body, 
									alpha = attachCtrl.alpha, 
									id = attachCtrl.id)

			tugOffsetAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = tugOffsetValue, name = "tugOffset", cb = False, keyable = False, locked = True, replace = True)[0]
			tugOffsetAttr >> origAttachPoc.uTugOffset

			tugScaleAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = tugScaleValue, name = "tugScale", cb = False, keyable = False, locked = True, replace = True)[0]
			tugScaleAttr >> origAttachPoc.uTugScale

			uScaleInvAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = uScaleInvValue, name = "uShift", cb = False, keyable = False, locked = True, replace = True)[0]
			uScaleInvAttr >> origAttachPoc.uScaleMidInverse

			squeezeAimAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = 0.0, name = "squeezeTips", replace = True)[0]
			squeezeAimAttr >> origAttachPoc.squeezeAim

			waveAimAngleAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = 0.0, name = "curlWaveStrength", replace = True)[0]
			waveAimAngleAttr >> origAttachPoc.waveAimAngle

			waveAimPhaseAttr = mnsUtils.addAttrToObj([attachmentCtrlsDict[inputName + "AttachmentAll"]["ctrl"].node], type = "float", value = 0.5, name = "curlWavePhase", replace = True)[0]
			waveAimPhaseAttr >> origAttachPoc.twistAimWavePhase

	###follow
	status, doFollowRotation = mnsUtils.validateAttrAndGet(rootGuide, "doFollowRotation", False)
	status, jntToFollow = mnsUtils.validateAttrAndGet(rootGuide, "jntToFollow", "")
	if doFollowRotation and jntToFollow:
		jntToFollow = mnsUtils.checkIfObjExistsAndSet(jntToFollow)
		
		if jntToFollow and jntToFollow.nodeName().split("_")[-1] == "rCtrl":
			jntToFollow = blkUtils.toggleGuideJoint(rootObjs = [jntToFollow], returnToggle = True)
			if jntToFollow: jntToFollow = jntToFollow[0]

		if jntToFollow:
			status, horizontalFollow = mnsUtils.validateAttrAndGet(rootGuide, "horizontalFollow", 0.15)
			status, verticalFollow = mnsUtils.validateAttrAndGet(rootGuide, "verticalFollow", 0.15)
			
			origOfffsetGrp = blkUtils.getOffsetGrpForCtrl(mainCtrl)
			mainCtrlModGrp =  mnsUtils.createOffsetGroup(mainCtrl, type = "modifyGrp")
			pm.parent(mainCtrlModGrp.node, animGrp.node)
			pm.delete(pm.orientConstraint(jntToFollow, origOfffsetGrp.node))
			pm.parent(mainCtrlModGrp.node, origOfffsetGrp.node)
			orientOffsetGrp = mnsUtils.createNodeReturnNameStd(parentNode = animGrp, side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "FollowRotateOffset", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
			orientOffsetGrp.node.v.set(False)
			pm.delete(pm.parentConstraint(jntToFollow, orientOffsetGrp.node))
			
			horReceiveTranform = mnsUtils.createNodeReturnNameStd(parentNode = origOfffsetGrp.node.getParent(), side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RotFolHor", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
			horReceiveTranform.node.v.set(False)
			pm.delete(pm.parentConstraint(origOfffsetGrp.node, horReceiveTranform.node))
			
			verReceiveTranform = mnsUtils.createNodeReturnNameStd(parentNode = origOfffsetGrp.node.getParent(), side =  MnsBuildModule.rootGuide.side, body = MnsBuildModule.rootGuide.body + "RotFolVer", alpha = MnsBuildModule.rootGuide.alpha, id =  MnsBuildModule.rootGuide.id, buildType = "group", incrementAlpha = False)
			verReceiveTranform.node.v.set(False)
			pm.delete(pm.parentConstraint(origOfffsetGrp.node, verReceiveTranform.node))
			
			horReceiveTranform.node.ry >> origOfffsetGrp.node.ry
			verReceiveTranform.node.rx >> origOfffsetGrp.node.rx

			horOrient = mnsNodes.mayaConstraint([jntToFollow, orientOffsetGrp.node], horReceiveTranform.node, type = "orient")
			horOrient.node.interpType.set(0)
			verOrient = mnsNodes.mayaConstraint([jntToFollow, orientOffsetGrp.node], verReceiveTranform.node, type = "orient")
			verOrient.node.interpType.set(0)

			mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["______"], name = "rotationFollow", replace = True, locked = True)
			horFollowAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", min = 0.0, max = 1.0, value = horizontalFollow, name = "horizontalFollow", replace = True)[0]
			horFollowAttr >> horOrient.node.attr(jntToFollow.nodeName() + "W0")
			mnsNodes.reverseNode([horFollowAttr, 0.0, 0.0], [horOrient.node.attr(orientOffsetGrp.node.nodeName() + "W1"), 0.0, 0.0])

			verFollowAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", min = 0.0, max = 1.0, value = horizontalFollow, name = "verticalFollow", replace = True)[0]
			verFollowAttr >> verOrient.node.attr(jntToFollow.nodeName() + "W0")
			mnsNodes.reverseNode([verFollowAttr, 0.0, 0.0], [verOrient.node.attr(orientOffsetGrp.node.nodeName() + "W1"), 0.0, 0.0])

	#fix global rotation
	if iLocs:
		for iLoc in iLocs: 
			iLoc.node.r.disconnect()
			iLoc.node.rx.disconnect()
			iLoc.node.ry.disconnect()
			iLoc.node.rz.disconnect()
			orientCon = mnsNodes.mayaConstraint(mainCtrl, iLoc, type = "orient", maintainOffset = True)

	if mnsCurveZipNode:
		### curve zip attrs #####
		mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["______"], name = "globalModuleSettings", replace = True, locked = True)

		status, blinkHeight = mnsUtils.validateAttrAndGet(rootGuide, "blinkHeight", 0.5)
		blinkHeightAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", min = 0.0, max = 1.0, value = blinkHeight, name = "blinkHeight", replace = True)[0]
		blinkHeightAttr >> mnsCurveZipNode.node.midBias

		status, midCurveMode = mnsUtils.validateAttrAndGet(rootGuide, "midCurveMode", 1)
		midCurveModeAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["oneToOne", "regenerate"], enumDefault = midCurveMode, name = "midCurveMode", replace = True)[0]
		midCurveModeAttr >> mnsCurveZipNode.node.midCurveMode

		status, midCurveSubsteps = mnsUtils.validateAttrAndGet(rootGuide, "midCurveResolution", 5)
		midCurveSubstepsAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "int", value = midCurveSubsteps, name = "midCurveResolution", replace = True)[0]
		midCurveSubstepsAttr >> mnsCurveZipNode.node.midCurveSubsteps

		status, aroundCenter = mnsUtils.validateAttrAndGet(rootGuide, "aroundCenter", True)
		aroundCenterAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = aroundCenter, name = "aroundCenter", replace = True)[0]
		aroundCenterAttr >> mnsCurveZipNode.node.aroundCenter

		status, curveResolution = mnsUtils.validateAttrAndGet(rootGuide, "curveResolution", 24)
		curveResolutionAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "int", value = curveResolution, name = "curveResolution", replace = True)[0]
		curveResolutionAttr >> mnsCurveZipNode.node.substeps

		conformToMeetAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = False, name = "conformToMeetPoint", replace = True)[0]
		conformToMeetAttr >> mnsCurveZipNode.node.conformToMeetPoint

		curveToConformAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["curveA", "curveB"], name = "alterCurveToMeetPoint", replace = True)[0]
		curveToConformAttr >> mnsCurveZipNode.node.curveToConform

		confDistAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", value = 0.2, name = "conformDistanceThreshold", replace = True)[0]
		confDistAttr >> mnsCurveZipNode.node.conformDistancethreshold

	########### Transfer Authority ###########
	blkUtils.transferAuthorityToCtrl(relatedJnt, mainCtrl)

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, mainCtrl, mainCtrl

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core.prefixSuffix import GLOB_mnsJntStructDefaultSuffix
	from mansur.core import string as mnsString
	from mansur.block.core import controlShapes as blkCtrlShps

	rootGuide = guides[0]
	rigTop = blkUtils.getRigTop(rootGuide)
	relatedRootJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(rootGuide))
	customGuides = blkUtils.getModuleDecendentsWildcard(guides[0], customGuidesOnly = True)
	returnData = {}

	inputNames = ["Upper", "Lower"]
	for k, inputName in enumerate(inputNames):
		for attrName in [("orig" + inputNames[k]), ("orig" + inputNames[k] + "Attach"), ("orig" + inputNames[k] + "AttachGuides")]:
			if rootGuide.node.hasAttr(attrName):
				try:
					pm.delete(rootGuide.node.attr(attrName).get())
				except:
					pass		

	bindCurves, upperEdge, lowerEdge = createBindCurvesFromModuleSettings(mansur, rootGuide)

	if bindCurves[0] and bindCurves[1]:
		iLocsReturn = []
		nodesToDelete = []
		nodesToDelete += bindCurves

		status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 1.0)
		status, curveResolution = mnsUtils.validateAttrAndGet(rootGuide, "curveResolution", 24)
		mnsCurveZipNode = mnsNodes.mnsCurveZipNode(
								type = "mnsCurveZipB",
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
								bindCurveA =bindCurves[0].getShape().worldSpace[0],
								bindCurveB = bindCurves[1].getShape().worldSpace[0],
								centerMatrix = rootGuide.node.worldMatrix[0],
								aroundCenter = False,
								upCurveOffset = upCurveOffset,
								substeps = curveResolution
								)
		nodesToDelete.append(mnsCurveZipNode.node)

		samplesAmount = [len(upperEdge), len(lowerEdge)]
		inputAttrSuffix = "AB"

		samples = {"Upper": [], "Lower": []}
		curveInputAttrs = [mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[0]), mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[1])]
		upCurveInputAttrs = [mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[0] + "Offset"), mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[1] + "Offset")]
		
		#create intermediate curves if needed
		#first, locate old cgCurves and delete
		customGuides = blkUtils.getModuleDecendentsWildcard(rootGuide, customGuidesOnly = True)
		for cg in customGuides:
			if "BindTweak" in cg.body: pm.delete(cg.node)
		#now check if needed to create new ones
		status, doBindTweak = mnsUtils.validateAttrAndGet(rootGuide, "doBindTweak", False)
		if doBindTweak:
			for k, curve in enumerate(bindCurves):
				tweakCurve = blkCtrlShps.ctrlCreate(
										side =rootGuide.side, 
										body = rootGuide.body + inputAttrSuffix[k] + "BindTweak", 
										alpha = rootGuide.alpha, 
										id = rootGuide.id,
										color = blkUtils.getCtrlCol(rootGuide, rigTop),
										parentNode = rootGuide.node,
										ctrlType = "customGuide")
				curveInputAttrs[k] >> tweakCurve.node.getShape().create
				curveInputAttrs[k] = tweakCurve.node.getShape().worldSpace[0]
				pm.makeIdentity(tweakCurve.node)
				tweakCurve.node.inheritsTransform.set(False)
				mnsUtils.lockAndHideAllTransforms(tweakCurve, lock = True, keyable = False, cb = False)

		pocNodes = []
		for k, curve in enumerate(bindCurves):
			pocn = mnsNodes.mnsPointsOnCurveNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix,
											buildOutputs = True,
											buildType = 4, #interpJointsType
											buildMode = 0,
											doScale = False,
											aimAxis = 1,
											upAxis = 0,
											doRotate = False,
											numOutputs = samplesAmount[k],
											isolatePolesRotation = False
											)
			curveInputAttrs[k] >> pocn["node"].node.curve
			upCurveInputAttrs[k] >> pocn["node"].node.upCurve

			samples.update({inputNames[k]: pocn["samples"]})
			iLocsReturn += pocn["samples"]
			
			if not doBindTweak:			
				pocn["node"].node.curve.disconnect()
				pocn["node"].node.upCurve.disconnect()
			blkUtils.connectSlaveToDeleteMaster(pocn["node"], rootGuide)

			origCurveAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "orig" + inputNames[k], value= "", replace = True)[0]
			pocn["node"].node.message >> origCurveAttr
			pocNodes.append(pocn["node"].node)

		returnData = {"Main": iLocsReturn}

		#curve attachments
		connectCustomGuidesToPoc(mansur, guides, customGuides)
		for n in pocNodes: n.mode.set(0)

		lowerBase, upperBase = None, None
		for cGuide in customGuides:
			if "Lower" in cGuide.name:
				if "Base" in cGuide.name: lowerBase = cGuide
			if "Upper" in cGuide.name:
				if "Base" in cGuide.name: upperBase = cGuide

		inputNames = ["Upper", "Lower"]
		for inputName in inputNames:
			contin = False
			if inputName == "Upper":
				status, doUpperAttachment = mnsUtils.validateAttrAndGet(guides[0], "doUpperAttachment", False)
				if doUpperAttachment: contin = True
			else:
				status, doLowerAttachment = mnsUtils.validateAttrAndGet(guides[0], "doLowerAttachment", False)
				if doLowerAttachment: contin = True

			if contin:
				status, originPocn = mnsUtils.validateAttrAndGet(guides[0], "orig" + inputName, None)

				if originPocn:
					status, jntCount = mnsUtils.validateAttrAndGet(guides[0], "upperJntCount", 2)
					if inputName == "Lower": status, jntCount = mnsUtils.validateAttrAndGet(guides[0], "lowerJntCount", 2)

					typeSample = samples[inputName] 

					#btc from interJoints
					status, offsetX = mnsUtils.validateAttrAndGet(rootGuide, "offsetX", 3.0)
					status, offsetY = mnsUtils.validateAttrAndGet(rootGuide, "offsetY", 0.0)
					status, offsetZ = mnsUtils.validateAttrAndGet(rootGuide, "offsetZ", 0.0)

					attachmentBtc = mnsNodes.mnsBuildTransformsCurveNode(
																			side = rootGuide.side, 
																			alpha = rootGuide.alpha, 
																			id = rootGuide.id, 
																			body = rootGuide.body + inputName + "Attach", 
																			transforms = typeSample, 
																			deleteCurveObjects = True, 
																			tangentDirection = 2, 
																			buildOffsetCurve = True,
																			buildMode = 1,
																			degree = 3,
																			offsetX = offsetX,
																			offsetY = offsetY,
																			offsetZ = offsetZ)

					if relatedRootJnt:
						relatedRootJnt.node.worldMatrix[0] >> attachmentBtc["node"].node.offsetBaseMatrix

					blkUtils.connectSlaveToDeleteMaster(attachmentBtc["node"], rootGuide)

					status, curveResolution = mnsUtils.validateAttrAndGet(rootGuide, "curveResolution", 24)

					rscNode = mnsNodes.mnsResampleCurveNode(side = rootGuide.side, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id, 
										body = rootGuide.body, 
										sections = curveResolution,
										inputCurve = attachmentBtc["node"].node.outCurve
										)
					blkUtils.connectSlaveToDeleteMaster(rscNode["node"], rootGuide)

					rscNodeUp = mnsNodes.mnsResampleCurveNode(side = rootGuide.side, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id, 
										body = rootGuide.body, 
										sections = curveResolution,
										inputCurve = attachmentBtc["node"].node.outOffsetCurve
										)
					blkUtils.connectSlaveToDeleteMaster(rscNodeUp["node"], rootGuide)

					attachmentPoc = mnsNodes.mnsPointsOnCurveNode(
													side = rootGuide.side, 
													alpha = rootGuide.alpha, 
													id = rootGuide.id, 
													body = rootGuide.body + inputName + "Attach",
													inputCurve = rscNode["node"].node.outCurve,
													inputUpCurve = rscNodeUp["node"].node.outCurve,
													buildOutputs = True,
													buildType = 4, #interpLocsType
													buildMode = 0,
													doScale = False,
													aimAxis = 1,
													upAxis = 0,
													numOutputs = jntCount
													)	
					blkUtils.connectSlaveToDeleteMaster(attachmentPoc["node"], rootGuide)
					returnData.update({inputName + "Attach": attachmentPoc["samples"]})
					origCurveAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "orig" + inputName + "Attach", value= "", replace = True)[0]
					attachmentPoc["node"].node.message >> origCurveAttr

					attrHost = upperBase
					if inputName == "Lower": attrHost = lowerBase

					if attrHost: 
						attrHost.node.attachmentLength >> attachmentPoc["node"].node.uScale
						attrHost.node.attachmentOffset >> attachmentPoc["node"].node.uOffset
						attrHost.node.tugOffset >> attachmentPoc["node"].node.uTugOffset
						attrHost.node.tugScale >> attachmentPoc["node"].node.uTugScale
						attrHost.node.uShift >> attachmentPoc["node"].node.uScaleMidInverse

						#create param adjust
						attachmentPoc["node"].node.enableParamAdjust.set(True)
						mnsUtils.addAttrToObj([attrHost.node], type = "enum", value = ["______"], name = "IsolatedParamAdjust", replace = True, locked = True)
						for j in range(jntCount):
							attrName = "pos" + mnsUtils.convertIntToAlpha(j)
							mnsUtils.addAttrToObj([attrHost.node], type = "float", value = 0.0, name = attrName, replace = True)[0]
							attrHost.node.attr(attrName) >> attachmentPoc["node"].node.paramAdjustment[j]

		if nodesToDelete: pm.delete(nodesToDelete)
		
		return returnData

def connectCustomGuidesToPoc(mansur, guides, cGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils

	if guides and cGuides:
		lowerBase, lowerTip, upperBase, upperTip = None, None, None, None
		for cGuide in cGuides:
			
			if "Lower" in cGuide.name:
				if "Base" in cGuide.name: lowerBase = cGuide
				if "Tip" in cGuide.name: lowerTip = cGuide
				cGuide.node.v.set(False)
			if "Upper" in cGuide.name:
				if "Base" in cGuide.name: upperBase = cGuide
				if "Tip" in cGuide.name: upperTip = cGuide
				cGuide.node.v.set(False)

		inputNames = ["Upper", "Lower"]
		for inputName in inputNames:
			contin = False
			transformsInput = []
			if inputName == "Upper": 
				if upperBase and upperTip: 
					contin = True
					transformsInput = [upperBase, upperTip]
			else:
				if lowerBase and lowerTip: 
					transformsInput = [lowerBase, lowerTip]
					contin = True

			if contin:
				status, originPocn = mnsUtils.validateAttrAndGet(guides[0], "orig" + inputName, None)
				
				attachmentLengthValue = 1.0
				attachmentOffsetValue = 0.0
				uTugOffsetValue = 0.0
				uTugScaleValue = 0.0
				uScaleMidInverseValue = 0.0

				if transformsInput[0].node.hasAttr("attachmentLength"):
					attachmentLengthValue = transformsInput[0].node.attachmentLength.get()
				if transformsInput[0].node.hasAttr("attachmentOffset"):
					attachmentOffsetValue = transformsInput[0].node.attachmentOffset.get()
				if transformsInput[0].node.hasAttr("tugOffset"):
					uTugOffsetValue = transformsInput[0].node.tugOffset.get()
				if transformsInput[0].node.hasAttr("tugScale"):
					uTugScaleValue = transformsInput[0].node.tugScale.get()
				if transformsInput[0].node.hasAttr("uShift"):
					uScaleMidInverseValue = transformsInput[0].node.uShift.get()

				if originPocn:
					pocn = mnsNodes.mnsPointsOnCurveNode(
											side = guides[0].side, 
											alpha = guides[0].alpha, 
											id = guides[0].id, 
											body = guides[0].body + inputName + "AttachGuides", 
											inputCurve = originPocn.curve,
											inputUpCurve = originPocn.upCurve,
											buildOutputs = False,
											transforms = transformsInput,
											doScale = False,
											buildMode = 0,
											aimAxis = 1,
											upAxis = 0,
											numOutputs = 2
											)
					origCurveAttr = mnsUtils.addAttrToObj([guides[0].node], type = "message", name = "orig" + inputName + "AttachGuides", value= "", replace = True)[0]
					pocn["node"].node.message >> origCurveAttr

					if inputName == "Upper":
						status, doUpperAttachment = mnsUtils.validateAttrAndGet(guides[0], "doUpperAttachment", False)
						if doUpperAttachment: 
							for cGuide in transformsInput: cGuide.node.v.set(True)
					else:
						status, doLowerAttachment = mnsUtils.validateAttrAndGet(guides[0], "doLowerAttachment", False)
						if doLowerAttachment: 
							for cGuide in transformsInput: cGuide.node.v.set(True)
					
					pm.refresh()
					pocn["node"].node.mode.set(0)	
					attachmentLengthAttr = mnsUtils.addAttrToObj([transformsInput[0].node], type = "float", value = attachmentLengthValue, name = "attachmentLength", replace = True, min = 0.0, max = 1.0)[0]
					attachmentLengthAttr >> pocn["node"].node.uScale
					attachmentOffsetAttr = mnsUtils.addAttrToObj([transformsInput[0].node], type = "float", value = attachmentOffsetValue, name = "attachmentOffset", replace = True, min = 0.0)[0]
					attachmentOffsetAttr >> pocn["node"].node.uOffset
					uTugOffsetAttr = mnsUtils.addAttrToObj([transformsInput[0].node], type = "float", value = uTugOffsetValue, name = "tugOffset", replace = True)[0]
					uTugOffsetAttr >> pocn["node"].node.uTugOffset
					uTugScaleAttr = mnsUtils.addAttrToObj([transformsInput[0].node], type = "float", value = uTugScaleValue, name = "tugScale", replace = True)[0]
					uTugScaleAttr >> pocn["node"].node.uTugScale
					uScaleMidInvAttr = mnsUtils.addAttrToObj([transformsInput[0].node], type = "float", value = uScaleMidInverseValue, name = "uShift", replace = True)[0]
					uScaleMidInvAttr >> pocn["node"].node.uScaleMidInverse
					
def customGuides(mansur, builtGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils

	custGuides = []
	parentDict = {}

	if builtGuides:
		inputNames = ["Upper", "Lower"]
		locationNames = ["Base", "Tip"]

		for inputName in inputNames:
			for locationName in locationNames:
				nameStd = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + inputName + "Attach" + locationName, alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
				pm.delete(pm.parentConstraint(builtGuides[0].node, nameStd.node))
				custGuides.append(nameStd)
				parentDict.update({nameStd: builtGuides[0]})
				nameStd.node.inheritsTransform.set(False)
				
				status, doUpperAttachment = mnsUtils.validateAttrAndGet(builtGuides[0], "doUpperAttachment", False)
				status, doLowerAttachment = mnsUtils.validateAttrAndGet(builtGuides[0], "doLowerAttachment", False)
				if inputName == "Upper": 
					nameStd.node.ty.set(2)
					if not doUpperAttachment: nameStd.node.v.set(False)
				else: 
					nameStd.node.ty.set(-2)
					if not doLowerAttachment: nameStd.node.v.set(False)

				if locationName == "Base": nameStd.node.tx.set(2)
				else:  nameStd.node.tx.set(-2)

				mnsUtils.lockAndHideTransforms(nameStd.node, lock = True)
	
		connectCustomGuidesToPoc(mansur, builtGuides, custGuides)

	return custGuides, parentDict

def deconstruct(mansur, MnsBuildModule, **kwargs):
	#transfer authority back to original pocn
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core import utility as mnsUtils

	rootGuide = MnsBuildModule.rootGuide
	if rootGuide:
		#get existing iLocs and connect them, essentially transfer authority.

		inputAttrSuffix = "AB"
		inputNames = ["Upper", "Lower"]

		upperEdge, lowerEdge = getEdgesFromModuleSettings(mansur, rootGuide)

		if upperEdge and lowerEdge:
			#get origin pocns
			pocns = [None, None]
			for k, inputName in enumerate(inputNames):
				if rootGuide.node.hasAttr("orig" + inputNames[k]):
					pocns[k] = rootGuide.node.attr("orig" + inputNames[k]).get()
					pocns[k].globalScale.disconnect()
					pocns[k].globalScale.set(1.0)

			if pocns[0] and pocns[1]:
				iLocs = blkUtils.getModuleInterpJoints(rootGuide)
				if iLocs:
					iLocs = mnsUtils.sortNameStdArrayByID(iLocs)
				
					for k, iLoc in enumerate(iLocs):
						if k < len(upperEdge):
							enumToConnect = k
							pocnToConnect = pocns[0]
						else:
							enumToConnect = k - len(upperEdge)
							pocnToConnect = pocns[1]

						pocnToConnect.transforms[enumToConnect].translate >> iLoc.node.t
						pocnToConnect.transforms[enumToConnect].rotate >> iLoc.node.r
						pocnToConnect.transforms[enumToConnect].scale >> iLoc.node.s

		#attachments
		for inputName in inputNames:
			status, origAttachPoc = mnsUtils.validateAttrAndGet(rootGuide, "orig" + inputName + "Attach", None)
			status, attachCGuide = mnsUtils.validateAttrAndGet(rootGuide, inputName + "AttachCGuide", None)
			
			if origAttachPoc and attachCGuide:
				try:
					attachCGuide.attr("attachmentLength") >> origAttachPoc.uScale
					attachCGuide.attr("attachmentOffset") >> origAttachPoc.uOffset
					attachCGuide.attr("tugOffset") >> origAttachPoc.uTugOffset
					attachCGuide.attr("tugScale") >> origAttachPoc.uTugScale
					attachCGuide.attr("uShift") >> origAttachPoc.uScaleMidInverse
				except: pass

				origAttachPoc.globalScale.disconnect()
				origAttachPoc.globalScale.set(1.0)

				for attrName in ["twistUpStart", "twistAimStart", "twistTertiaryStart",
								 "twistUpMid", "twistAimMid", "twistTertiaryMid",
								 "twistUpEnd", "twistAimEnd", "tertiaryTwistEnd",
								 "uScaleMid", "squeezeAim", "waveAimAngle", "twistAimWavePhase"]:
					try:
						origAttachPoc.attr(attrName).set(pm.attributeQuery(attrName, node=transform, listDefault=True)[0])
					except:
						pass