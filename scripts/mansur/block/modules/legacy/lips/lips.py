"""Author: Asaf Ben-Zur
Best used for: Lips
This module has been depreciated, please use LipsB module.
"""



from maya import cmds
import pymel.core as pm


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
		status, reverseUpper = mnsUtils.validateAttrAndGet(rootGuide, "reverseUpper", False)
		status, reverseLower = mnsUtils.validateAttrAndGet(rootGuide, "reverseLower", False)

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

			#check curves direction. if invalid, flip upper
			if bindCurves[0] and bindCurves[1]:
				upperFirstCv = bindCurves[0].getShape().getCV(0)
				lowerFirstCv = bindCurves[1].getShape().getCV(0)
				if upperFirstCv != lowerFirstCv: pm.reverseCurve(bindCurves[0], ch= False, rpo = True)

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

	cusPivCtrls = []
	upperCurlPivGuide, lowerCurlPivGuide = None, None
	if customGuides:
		for guide in customGuides: 
			if "Upper" in guide.name: upperCurlPivGuide = guide
			elif "Lower" in guide.name: lowerCurlPivGuide = guide

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	########### module construction ###########
	status, doCheekRaise = mnsUtils.validateAttrAndGet(rootGuide, "doCheekRaise", False)

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
							isFacial = MnsBuildModule.isFacial)
	ctrlsCollect.append(mainCtrl)


	#get offsets
	status, offsetX = mnsUtils.validateAttrAndGet(rootGuide, "offsetX", 10.0)
	status, offsetY = mnsUtils.validateAttrAndGet(rootGuide, "offsetY", 0.0)
	status, offsetZ = mnsUtils.validateAttrAndGet(rootGuide, "offsetZ", 0.0)

	# first recreare the curve.
	curveGrp = mnsUtils.createNodeReturnNameStd(parentNode = mainCtrl, side =  rootGuide.side, body = rootGuide.body + "Curves", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)
	curveGrp.node.v.set(False)

	bindCurves, upperEdge, lowerEdge = createBindCurvesFromModuleSettings(mansur, rootGuide)

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
		mnsCurveZipNode = mnsNodes.mnsLipZipNode(
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

		#input surface
		status, doAlongSurface = mnsUtils.validateAttrAndGet(rootGuide, "doAlongSurface", False)
		status, inputSurface = mnsUtils.validateAttrAndGet(rootGuide, "inputSurface", None)
		if doAlongSurface:
			inputSurface = mnsUtils.checkIfObjExistsAndSet(inputSurface)
			if inputSurface and inputSurface.getShape():
				shapeNode = inputSurface.getShape()
				if type(shapeNode) == pm.nodetypes.NurbsSurface:
					shapeNode.worldSpace[0] >> mnsCurveZipNode.node.inputSurface

					baseSyrfaceNameStd = mnsUtils.returnNameStdChangeElement(rootGuide, body = rootGuide.body + "BaseSurface", suffix = "sfc", autoRename = False)
					baseSurface = pm.duplicate(inputSurface, name = baseSyrfaceNameStd.name)[0]
					mnsUtils.deleteUnusedShapeNodes(baseSurface)
					pm.parent(baseSurface, animStaticGrp.node)
					baseSurface.v.set(False)
					baseSurface.getShape().worldSpace[0] >> mnsCurveZipNode.node.inputSurfaceBase

					status, baseSurfaceJointFollow = mnsUtils.validateAttrAndGet(rootGuide, "baseSurfaceJointFollow", None)
					if baseSurfaceJointFollow:
						baseSurfaceJointFollow = mnsUtils.checkIfObjExistsAndSet(baseSurfaceJointFollow)
						if baseSurfaceJointFollow and type(baseSurfaceJointFollow) == pm.nodetypes.Joint:
							#all required input are present to create a base surface, so create it.
							pm.skinCluster(baseSurface, baseSurfaceJointFollow, tsb = True)
							
		#get existing iLocs and connect them, essentially transfer authority.
		iLocs = blkUtils.getModuleInterpJoints(rootGuide)
		if iLocs:
			iLocs = mnsUtils.sortNameStdArrayByID(iLocs)
			inputAttrSuffix = "AB"
			inputNames = ["Upper", "Lower"]

			layBCornA, layBCornB = None, None
			for k, curve in enumerate(bindCurves):
				transformsArray = iLocs[0:len(upperEdge)] 
				if k  ==1 : transformsArray = iLocs[len(upperEdge):]

				zipInputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k])
				zipInputCurveOffset = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k] + "Offset")


				status, doLayerBCtrls = mnsUtils.validateAttrAndGet(rootGuide, "doLayerBCtrls", True)
				if doLayerBCtrls:
					layeBCtrlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  rootGuide.side, body = rootGuide.body + "LayBCtrls", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)

					status, numLayerBCtrlsPerSection = mnsUtils.validateAttrAndGet(rootGuide, "numLayerBCtrlsPerSection", 9)
					status, layerBControlShape = mnsUtils.validateAttrAndGet(rootGuide, "layerBControlShape", "cube")

					layeBoffsets = []
					layerBCtrls = []
					for b in range(numLayerBCtrlsPerSection):
						contin = True

						ctrlType = "ctrl"
						if k == 1 and (b == 0 or b == numLayerBCtrlsPerSection - 1):
							ctrlType = "techCtrl"

						layerBCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
								color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
								bodySuffix = "LayB",
								controlShape = layerBControlShape,
								scale = modScale * 0.05, 
								ctrlType = ctrlType,
								parentNode = layeBCtrlsGrp,
								alongAxis = 2,
								blkCtrlTypeID = 1,
								symmetryType = 1,
								doMirror = False,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								isFacial = MnsBuildModule.isFacial)
						mnsUtils.lockAndHideTransforms(layerBCtrl.node, tx = False, ty = False, tz = False, lock = True)
						layBOffset = blkUtils.getOffsetGrpForCtrl(layerBCtrl)
						ctrlsCollect.append(layerBCtrl)
						layeBoffsets.append(layBOffset)
						layerBCtrls.append(layerBCtrl)

						if k == 0: 
							if b == 0: layBCornA = layerBCtrl
							elif b == numLayerBCtrlsPerSection - 1: layBCornB = layerBCtrl

						elif k == 1 and (b == 0 or b == numLayerBCtrlsPerSection - 1):
							pm.delete(layerBCtrl.node.getShapes())
							layBOffset.node.t.disconnect()
							layBOffset.node.s.disconnect()
							layBOffset.node.r.disconnect()
							layerBCtrl.node.v.set(False)
							if b == 0: pm.parent(layerBCtrl.node, layBCornA.node)
							else: pm.parent(layerBCtrl.node, layBCornB.node)
							pm.makeIdentity(layerBCtrl.node)

					pocn = mnsNodes.mnsPointsOnCurveNode(
											transforms = layeBoffsets,
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + inputNames[k] + "LayerB", 
											inputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k]),
											inputUpCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k] + "Offset"),
											buildOutputs = False,
											buildMode = 1,
											doScale = False,
											aimAxis = 1,
											upAxis = 0,
											numOutputs = len(layeBoffsets),
											isolatePolesRotation = False
											)

					btcNodeBase = mnsNodes.mnsBuildTransformsCurveNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body + inputNames[k].capitalize() + "TweakBBase", 
								transforms = layeBoffsets, 
								deleteCurveObjects = True, 
								buildMode = 1,
								degree = 3)

					btcNodeTweak = mnsNodes.mnsBuildTransformsCurveNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body + inputNames[k].capitalize() + "TweakB", 
								transforms = layerBCtrls, 
								deleteCurveObjects = True, 
								buildMode = 1,
								degree = 3)

					crvTwkNode = mnsNodes.mnsCurveTweakNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body + inputNames[k].capitalize(), 
								inputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k]),
								inputBaseCurve = btcNodeBase["node"].node.outCurve,
								inputTweakCurve = btcNodeTweak["node"].node.outCurve,
								outCurve = None)

					zipInputCurve = crvTwkNode.node.outCurve

				
				pocn = mnsNodes.mnsPointsOnCurveNode(
												transforms = transformsArray,
												side = rootGuide.side, 
												alpha = rootGuide.alpha, 
												id = rootGuide.id, 
												body = rootGuide.body + inputNames[k], 
												inputCurve = zipInputCurve,
												inputUpCurve = zipInputCurveOffset,
												buildOutputs = False,
												buildType = 4, #interpJointsType
												buildMode = 0,
												doScale = False,
												doRotate = False,
												connectRotate = False,
												aimAxis = 1,
												upAxis = 0,
												numOutputs = len(transformsArray),
												isolatePolesRotation = False
												)
				blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> pocn["node"].node.globalScale


		#create a temp pocns to find corner and mid positions.
		nodesToDelete = []
		cornerA, upperMid, cornerB, lowerMid = None, None, None, None
		status, reverseCorners = mnsUtils.validateAttrAndGet(rootGuide, "reverseCorners", False)

		namesArray = ["upper", "lower"]
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
													aimAxis = 1,
													upAxis = 0,
													numOutputs = 3)
			nodesToDelete.append(tempPocn["node"].node)
			for samp in tempPocn["samples"]:
				samp.t.disconnect()
				samp.r.disconnect()
				samp.s.disconnect()

			if k == 0:
				if not reverseCorners:
					cornerA = tempPocn["samples"][0]
					cornerB = tempPocn["samples"][2]
				else:
					cornerB = tempPocn["samples"][0]
					cornerA = tempPocn["samples"][2]
				upperMid = tempPocn["samples"][1]
				nodesToDelete += tempPocn["samples"]
			else:
				pm.delete([tempPocn["samples"][0], tempPocn["samples"][2]])
				nodesToDelete.append(tempPocn["samples"][1])
				lowerMid = tempPocn["samples"][1]

		#reverse position if needed
		if reverseCorners:
			temp = cornerA
			cornerA = cornerB
			cornerB = temp

		#find out if the direction of tangent needs to be flipped
		upperLocsArray = iLocs[0:len(upperEdge)]
		bezierTangentLength = mnsUtils.distBetween(upperLocsArray[0].node, upperLocsArray[-1].node)
		absXA = pm.xform(upperLocsArray[0].node, q = True, ws = True, t = True)[0]
		absXB = pm.xform(upperLocsArray[-1].node, q = True, ws = True, t = True)[0]
		if absXB > absXA: bezierTangentLength *= -1

		#create first layer main controls
		cornerACtrl, cornerBCtrl = None, None
		for k, curve in enumerate(bindCurves):
			transformsArray = iLocs[0:len(upperEdge)] 
			if k == 1: transformsArray = iLocs[len(upperEdge):]

			positionArray = [cornerA, upperMid, cornerB]
			if k == 1: positionArray = [cornerA, lowerMid, cornerB]

			tweakControls = []
			curlCtrl = None
			for j, position in enumerate(positionArray):
				layerACtrl = None

				if k == 1 and j != 1:
				 	if j == 0: layerACtrl = cornerACtrl
				 	if j == 2: layerACtrl = cornerBCtrl
				else:
					forceMirrorGrp = False
					symmetryType = 1

					if j == 0:
						if positionArray[0].tx.get() < positionArray[2].tx.get(): forceMirrorGrp = True
					elif j == 2:
						if positionArray[2].tx.get() < positionArray[0].tx.get(): forceMirrorGrp = True

					if k == 1 and j == 1:
						forceMirrorGrp = True
						symmetryType = 5

					controlShape = "square"
					bodySuffix = namesArray[k].capitalize() + "Mid"
					if j != 1:
						controlShape = "triangle"
						bodySuffix = namesArray[k].capitalize() + "Corner"

					#create control
					layerACtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
							color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
							matchPosition = position,
							bodySuffix = bodySuffix,
							controlShape = controlShape,
							scale = modScale * 0.1, 
							parentNode = mainCtrl,
							alongAxis = 2,
							side = "c",
							symmetryType = symmetryType,
							doMirror = True,
							forceMirrorGrp = forceMirrorGrp,
							createSpaceSwitchGroup = False,
							createOffsetGrp = True,
							isFacial = MnsBuildModule.isFacial)
					ctrlsCollect.append(layerACtrl)	

					if j == 1:
						mnsUtils.lockAndHideTransforms(layerACtrl.node, negateOperation = True, ry = False, sy = False, sz = False, lock = True)

						curlPosition = None
						doCurl = False
						if k == 0 and upperCurlPivGuide: 
							doCurl = True
							curlPosition = upperCurlPivGuide
						elif lowerCurlPivGuide:
							doCurl = True
							curlPosition = lowerCurlPivGuide
							forceMirrorGrp = True

						if doCurl:
							##create curl ctrl
							curlCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
								color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
								matchPosition = curlPosition,
								ctrlType = "techCtrl",
								bodySuffix = namesArray[k].capitalize() + "Curl",
								controlShape = "circle",
								scale = modScale * 0.075, 
								parentNode = mainCtrl,
								alongAxis = 2,
								side = "c",
								symmetryType = 3,
								doMirror = True,
								forceMirrorGrp = forceMirrorGrp,
								createSpaceSwitchGroup = False,
								createOffsetGrp = True,
								isFacial = MnsBuildModule.isFacial)
							mnsUtils.lockAndHideTransforms(curlCtrl.node, rx = False, lock = True)
							curlCtrl.node.v.set(False)

							curlOffset = mnsUtils.validateNameStd(curlCtrl.node.getParent())
							baseCurlLoc = mnsUtils.createNodeReturnNameStd(parentNode = curlOffset, side = curlCtrl.side, body = curlCtrl.body + "Base", alpha = curlCtrl.alpha, id = curlCtrl.id, buildType = "locator", incrementAlpha = False)
							baseCurlLoc.node.v.set(False)
							pm.makeIdentity(baseCurlLoc.node)

							if k == 0:
								baseCurlLoc.node.worldMatrix[0] >> mnsCurveZipNode.node.upperCurlBaseMatrix
								curlCtrl.node.worldMatrix[0] >> mnsCurveZipNode.node.upperCurlMatrix
							else:
								baseCurlLoc.node.worldMatrix[0] >> mnsCurveZipNode.node.lowerCurlBaseMatrix
								curlCtrl.node.worldMatrix[0] >> mnsCurveZipNode.node.lowerCurlMatrix
							layerACtrl.node.rx >> curlCtrl.node.rx

						###connect psuh-out and curl
						if k == 0:
							layerACtrl.node.tz >> mnsCurveZipNode.node.pushOutA
						else:
							layerACtrl.node.tz >> mnsCurveZipNode.node.pushOutB

						#curl
						outputValuesArray = []
						for transform in transformsArray:
							outputValuesArray.append(transform.node.rx)

						if curlCtrl: 

							if k == 1:
								mdlTranLoc = mnsUtils.createNodeReturnNameStd(parentNode = curlCtrl, side = curlCtrl.side, body = curlCtrl.body + "RFAAngleTransition", alpha = curlCtrl.alpha, id = curlCtrl.id, buildType = "locator", incrementAlpha = False)
								mdlTranLoc.node.v.set(False)
								pm.makeIdentity(mdlTranLoc.node)
								mdlNode = mnsNodes.mdlNode(curlCtrl.node.rx, -1.0, mdlTranLoc.node.rx)
								mnsRemapFloatArrayNode = mnsNodes.mnsRemapFloatArrayNode(value = mdlTranLoc.node.rx, angleOutputAsDegrees = True, outputCount = len(transformsArray), outValues = outputValuesArray)
							else:
								mnsRemapFloatArrayNode = mnsNodes.mnsRemapFloatArrayNode(value = curlCtrl.node.rx, angleOutputAsDegrees = True, outputCount = len(transformsArray), outValues = outputValuesArray)

						###connect sShape
						if k == 0:
							"""
							inputRotationAttr = layerACtrl.node.rz
							if negateSShapes:
								mdlNode = mnsNodes.mdlNode(inputRotationAttr, -1.0, None)
								inputRotationAttr = mdlNode.node.output

							sShapeSetRange = mnsNodes.setRangeNode([6.0, 6.0, 6.0],
													[-6.0, -6.0, -6.0],
													[180.0, 180.0, 180.0],
													[-180.0, -180.0, -180.0],
													[inputRotationAttr, None, None],
													[mnsCurveZipNode.node.sCurveA, None, None])
							"""
							#create a reference locator to normalize S shapes movements
							sShapeRefLoc = mnsUtils.createNodeReturnNameStd(parentNode = layerACtrl.node.getParent(), side = layerACtrl.side, body = layerACtrl.body + "UpperSReference", alpha = layerACtrl.alpha, id = layerACtrl.id, buildType = "locator", incrementAlpha = False)
							sShapeRefLoc.node.v.set(False)
							pm.makeIdentity(sShapeRefLoc.node)
							txValue = bezierTangentLength / 4.0
							sShapeRefLoc.node.tx.set(txValue)
							parentConstraint = mnsNodes.mayaConstraint([layerACtrl.node], sShapeRefLoc.node, type = "parent", maintainOffset = True, skipRotate = ["x", "y", "z"])
							mdlNode = mnsNodes.mdlNode(layerACtrl.node.ty, -1.0, None)
							adlNode = mnsNodes.adlNode(sShapeRefLoc.node.ty, mdlNode.node.output, mnsCurveZipNode.node.sCurveA)

							#connect zips
							mnsUtils.addAttrToObj([layerACtrl.node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
							toMidAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toMid", replace = True)[0]
							toLowerAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toLower", replace = True)[0]
							mnsNodes.setRangeNode([1, 1, 1],
													[0, 0, 0],
													[10, 10, 10],
													[0, 0, 0],
													[toLowerAttr, toMidAttr, None],
													[mnsCurveZipNode.node.AToB, mnsCurveZipNode.node.AToMid, None]) 
						else:
							"""
							inputRotationAttr = layerACtrl.node.rz
							if negateSShapes:
								mdlNode = mnsNodes.mdlNode(inputRotationAttr, -1.0, None)
								inputRotationAttr = mdlNode.node.output

							sShapeSetRange = mnsNodes.setRangeNode([-6.0, -6.0, -6.0],
													[6.0, 6.0, 6.0],
													[180, 180.0, 180.0],
													[-180.0, -180.0, -180.0],
													[inputRotationAttr, None, None],
													[mnsCurveZipNode.node.sCurveB, None, None])
							"""
							#create a reference locator to normalize S shapes movements
							sShapeRefLoc = mnsUtils.createNodeReturnNameStd(parentNode = layerACtrl.node.getParent(), side = layerACtrl.side, body = layerACtrl.body + "LowerSReference", alpha = layerACtrl.alpha, id = layerACtrl.id, buildType = "locator", incrementAlpha = False)
							sShapeRefLoc.node.v.set(False)
							pm.makeIdentity(sShapeRefLoc.node)
							txValue = bezierTangentLength / -4.0
							sShapeRefLoc.node.tx.set(txValue)
							parentConstraint = mnsNodes.mayaConstraint([layerACtrl.node], sShapeRefLoc.node, type = "parent", maintainOffset = True, skipRotate = ["x", "y", "z"])
							mdlNode = mnsNodes.mdlNode(layerACtrl.node.ty, -1.0, None)
							adlNode = mnsNodes.adlNode(sShapeRefLoc.node.ty, mdlNode.node.output, mnsCurveZipNode.node.sCurveB)

							#connect zips
							mnsUtils.addAttrToObj([layerACtrl.node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
							toMidAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toMid", replace = True)[0]
							toLowerAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toUpper", replace = True)[0]
							mnsNodes.setRangeNode([1, 1, 1],
													[0, 0, 0],
													[10, 10, 10],
													[0, 0, 0],
													[toLowerAttr, toMidAttr, None],
													[mnsCurveZipNode.node.BToA, mnsCurveZipNode.node.BToMid, None])
					else:
						#store attributes for cheek raise
						if doCheekRaise:
							#if forceMirrorGrp side is right
							#else, side is left

							raiseRoot = None
							if not forceMirrorGrp: #side is left
								attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "l_cheekRaise", value= "", replace = True)[0]
								layerACtrl.node.message >> attrStore
							else: #side is right
								attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "r_cheekRaise", value= "", replace = True)[0]
								layerACtrl.node.message >> attrStore

					# store jaw connections ctrls
					if k == 0:
						if j == 0:
							attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "jawConnect_cornerA", value= "", replace = True)[0]
							layerACtrl.node.message >> attrStore

							#connect zips
							mnsUtils.addAttrToObj([layerACtrl.node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
							zipAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "zip", replace = True)[0]
							mnsNodes.setRangeNode([1, 1, 1],
													[0, 0, 0],
													[10, 10, 10],
													[0, 0, 0],
													[zipAttr, None, None],
													[mnsCurveZipNode.node.zipStart, None, None])
							falloffAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.5, max = 1.0, min = 0.01, name = "zipFalloff", replace = True)[0]
							falloffAttr >> mnsCurveZipNode.node.zipStartFalloff

						elif j == 1:
							attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "jawConnect_upperMid", value= "", replace = True)[0]
							layerACtrl.node.message >> attrStore
						else:
							attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "jawConnect_cornerB", value= "", replace = True)[0]
							layerACtrl.node.message >> attrStore

							#connect zips
							mnsUtils.addAttrToObj([layerACtrl.node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
							zipAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "zip", replace = True)[0]
							mnsNodes.setRangeNode([1, 1, 1],
													[0, 0, 0],
													[10, 10, 10],
													[0, 0, 0],
													[zipAttr, None, None],
													[mnsCurveZipNode.node.zipEnd, None, None])
							falloffAttr = mnsUtils.addAttrToObj([layerACtrl.node], type = "float", value = 0.5, max = 1.0, min = 0.01, name = "zipFalloff", replace = True)[0]
							falloffAttr >> mnsCurveZipNode.node.zipEndFalloff
				
					if k == 1 and j == 1:
						attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "jawConnect_lowerMid", value= "", replace = True)[0]
						layerACtrl.node.message >> attrStore

					if k == 0:
						if j == 0: cornerACtrl = layerACtrl
						if j == 2: cornerBCtrl = layerACtrl


				tweakControls.append(layerACtrl)


			#create an alignment locator to create the curves from
			alignmentLocs = []
			for j, layACtrl in enumerate(tweakControls):
				alignmentLoc = mnsUtils.createNodeReturnNameStd(parentNode = layACtrl, side = layerACtrl.side, body = layerACtrl.body + "Align", alpha = layerACtrl.alpha, id = layerACtrl.id, buildType = "locator", incrementAlpha = False)
				alignmentLoc.node.v.set(False)
				pm.delete(pm.pointConstraint(layACtrl.node, alignmentLoc.node))
				
				if j == 0:
					offsetGrp = mnsUtils.createOffsetGroup(alignmentLoc.node)
					aimCns = mnsNodes.mayaConstraint([tweakControls[1].node], offsetGrp.node, type = "aim", aimVector = [0.0,1.0,0.0], upVector = [0.0,0.0,1.0], maintainOffset = False)
					offsetGrpA = mnsUtils.createOffsetGroup(alignmentLoc.node)
					pm.parent(alignmentLoc.node, w = True)
					pm.delete(pm.orientConstraint(layACtrl.node, offsetGrpA.node))
					pm.parent(alignmentLoc.node, offsetGrpA.node)
					offsetGrpB = mnsUtils.createOffsetGroup(offsetGrpA.node)
					layACtrl.node.r >> offsetGrpA.node.r
					#pm.delete(pm.aimConstraint(tweakControls[1].node, alignmentLoc.node, mo = False, aimVector = (0.0,1.0,0.0), upVector = (0.0,0.0,1.0)))
				elif j == 2: 
					offsetGrp = mnsUtils.createOffsetGroup(alignmentLoc.node)
					aimCns = mnsNodes.mayaConstraint([tweakControls[1].node], offsetGrp.node, type = "aim", aimVector = [0.0,-1.0,0.0], upVector = [0.0,0.0,1.0], maintainOffset = False)
					offsetGrpA = mnsUtils.createOffsetGroup(alignmentLoc.node)
					pm.parent(alignmentLoc.node, w = True)
					pm.delete(pm.orientConstraint(layACtrl.node, offsetGrpA.node))
					pm.parent(alignmentLoc.node, offsetGrpA.node)
					offsetGrpB = mnsUtils.createOffsetGroup(offsetGrpA.node)
					layACtrl.node.r >> offsetGrpA.node.r
					#pm.delete(pm.aimConstraint(tweakControls[1].node, alignmentLoc.node, mo = False, aimVector = (0.0,-1.0,0.0), upVector = (0.0,0.0,1.0)))
				else:
					alignmentLoc.node.ry.set(90)
					alignmentLoc.node.rz.set(90)
					if k == 1: alignmentLoc.node.sy.set(-1)
					pointCns = mnsNodes.mayaConstraint([mainCtrl.node], alignmentLoc.node, type = "orient", maintainOffset = True)

				alignmentLocs.append(alignmentLoc)

			#buildTheCurves
			status, tweakCurvesInterpolation = mnsUtils.validateAttrAndGet(rootGuide, "tweakCurvesInterpolation", 2)

			btcNode = mnsNodes.mnsBuildTransformsCurveNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body + namesArray[k].capitalize() + "Tweak", 
								transforms = alignmentLocs, 
								deleteCurveObjects = False, 
								tangentDirection = 1, 
								tangentLength = bezierTangentLength / 10.0,
								buildOffsetCurve = True,
								buildMode = tweakCurvesInterpolation,
								degree = 3,
								hermiteSteps = 5,
								offsetX = offsetX,
								offsetY = offsetY,
								offsetZ = offsetZ)
			blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> btcNode["node"].node.globalScale

			curve = btcNode["outCurve"]
			curve.node.create.disconnect()
			pm.parent(curve.node, curveGrp.node)

			if k == 0:
				btcNode["node"].node.outCurve >> mnsCurveZipNode.node.tweakCurveA[0]
				curve.node.worldSpace[0] >> mnsCurveZipNode.node.tweakCurveABase[0]
			else:
				btcNode["node"].node.outCurve >> mnsCurveZipNode.node.tweakCurveB[0]
				curve.node.worldSpace[0] >> mnsCurveZipNode.node.tweakCurveBBase[0]

			pm.delete(btcNode["outOffsetCurve"].node)

	
	try: pm.delete(nodesToDelete)
	except: pass
	
	#create tweak controls
	status, doTweakControls = mnsUtils.validateAttrAndGet(rootGuide, "doTweakControls", True)
	corners = []

	if doTweakControls and mnsCurveZipNode:
		status, numTweakControlsPerSection = mnsUtils.validateAttrAndGet(rootGuide, "numTweakControlsPerSection", 3)
		status, cornersControlShape = mnsUtils.validateAttrAndGet(rootGuide, "cornersControlShape", "diamond")
		status, tweakersControlShape = mnsUtils.validateAttrAndGet(rootGuide, "tweakersControlShape", "lightSphere")
		status, doTweakTangents = mnsUtils.validateAttrAndGet(rootGuide, "doTweakTangents", False)

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

				#create control
				ctrlType = "ctrl"
				if k == 1 and isCorner:
					ctrlType = "techCtrl"

				tweakCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
						color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
						bodySuffix = bodySuffix,
						controlShape = controlShape,
						ctrlType = ctrlType,
						scale = modScale * 0.1, 
						parentNode = tweakCtrlsGrp,
						symmetryType = symmetryType,
						doMirror = True,
						createSpaceSwitchGroup = False,
						createOffsetGrp = True,
						isFacial = MnsBuildModule.isFacial)
				mnsUtils.lockAndHideTransforms(tweakCtrl.node, tx = False, ty = False, tz = False, lock = True)
				tweakOffset = blkUtils.getOffsetGrpForCtrl(tweakCtrl)
				mnsNodes.mayaConstraint(mainCtrl.node, tweakOffset.node, type = "scale")

				tweakControls.append(tweakCtrl)

				if k ==0 and j == 0:
					mirGrp = blkUtils.getOffsetGrpForCtrl(tweakCtrl, type = "mirrorScaleGroup")
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

		#fix global rotation
		if iLocs:
			for iLoc in iLocs: 
				#orig Curl Input
				origCurlOutConnection = iLoc.node.rx.listConnections(p = True)
				if origCurlOutConnection: origCurlOutConnection = origCurlOutConnection[0]

				iLoc.node.r.disconnect()
				iLoc.node.rx.disconnect()
				iLoc.node.ry.disconnect()
				iLoc.node.rz.disconnect()

				orientCon = mnsNodes.mayaConstraint(mainCtrl, iLoc, type = "orient", maintainOffset = True)

				adlNode = mnsNodes.adlNode(orientCon.node.constraintRotateX, 
											origCurlOutConnection,
											iLoc.node.rx)


	if mnsCurveZipNode:
		### curve zip attrs #####
		mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["______"], name = "globalModuleSettings", replace = True, locked = True)

		status, midCurveHeight = mnsUtils.validateAttrAndGet(rootGuide, "midCurveHeight", 0.5)
		blinkHeightAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", min = 0.0, max = 1.0, value = midCurveHeight, name = "midCurveHeight", replace = True)[0]
		blinkHeightAttr >> mnsCurveZipNode.node.midBias

		status, aroundCenter = mnsUtils.validateAttrAndGet(rootGuide, "aroundCenter", False)
		aroundCenterAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = aroundCenter, name = "aroundCenter", replace = True)[0]
		aroundCenterAttr >> mnsCurveZipNode.node.aroundCenter

		status, doAlongSurface = mnsUtils.validateAttrAndGet(rootGuide, "doAlongSurface", True)
		doAlongSurfaceAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = doAlongSurface, name = "alongSurface", replace = True)[0]
		doAlongSurfaceAttr >> mnsCurveZipNode.node.alongSurface

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

def customGuides(mansur, builtGuides):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils

	custGuides = []
	parentDict = {}

	if builtGuides:
		rigTop = blkUtils.getRigTop(builtGuides[0])
		modScale = rigTop.node.assetScale.get() * builtGuides[0].node.controlsMultiplier.get() * mnsUtils.getMansurPrefs()["Global"]["mnsProjectScale"]

		upperPivotPos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "UpperCurlPivot", alpha = builtGuides[0].alpha, id = builtGuides[0].id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(builtGuides[0].node, upperPivotPos.node))
		pm.parent(upperPivotPos.node, builtGuides[0].node)
		pm.makeIdentity(upperPivotPos.node)
		upperPivotPos.node.ty.set(2)
		pm.parent(upperPivotPos.node, w = True)
		custGuides.append(upperPivotPos)
		parentDict.update({upperPivotPos: builtGuides[0]})

		lowerPivotPos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "LowerCurlPivot", alpha = builtGuides[0].alpha, id = builtGuides[0].id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(builtGuides[0].node, lowerPivotPos.node))
		pm.parent(lowerPivotPos.node, builtGuides[0].node)
		pm.makeIdentity(lowerPivotPos.node)
		lowerPivotPos.node.ty.set(-2)
		pm.parent(lowerPivotPos.node, w = True)
		custGuides.append(lowerPivotPos)
		parentDict.update({lowerPivotPos: builtGuides[0]})

	return custGuides, parentDict

def jointStructure(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.block.core import blockUtility as blkUtils
	from mansur.core.prefixSuffix import GLOB_mnsJntStructDefaultSuffix
	from mansur.core import string as mnsString

	rootGuide = guides[0]
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
		mnsCurveZipNode = mnsNodes.mnsLipZipNode(
								side = rootGuide.side, 
								alpha = rootGuide.alpha, 
								id = rootGuide.id, 
								body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
								bindCurveA =bindCurves[0].getShape().worldSpace[0],
								bindCurveB = bindCurves[1].getShape().worldSpace[0],
								centerMatrix = rootGuide.node.worldMatrix[0],
								upCurveOffset = upCurveOffset,
								substeps = curveResolution,
								aroundCenter = False,
								conformToMeetPoint = False
								)
		nodesToDelete.append(mnsCurveZipNode.node)

		samplesAmount = [len(upperEdge), len(lowerEdge)]
		inputAttrSuffix = "AB"

		samples = {"Upper": [], "Lower": []}

		for k, curve in enumerate(bindCurves):
			zipInputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k])
			zipInputCurveOffset = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k] + "Offset")

			pocn = mnsNodes.mnsPointsOnCurveNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + GLOB_mnsJntStructDefaultSuffix, 
											inputCurve = zipInputCurve,
											inputUpCurve = zipInputCurveOffset,
											buildOutputs = True,
											buildType = 4, #interpJointsType
											buildMode = 0,
											doScale = False,
											doRotate = False,
											aimAxis = 1,
											upAxis = 0,
											numOutputs = samplesAmount[k],
											isolatePolesRotation = False
											)
			samples.update({inputNames[k]: pocn["samples"]})
			iLocsReturn += pocn["samples"]
			pocn["node"].node.curve.disconnect()
			pocn["node"].node.upCurve.disconnect()
			blkUtils.connectSlaveToDeleteMaster(pocn["node"], rootGuide)

			origCurveAttr = mnsUtils.addAttrToObj([rootGuide.node], type = "message", name = "orig" + inputNames[k], value= "", replace = True)[0]
			pocn["node"].node.message >> origCurveAttr

		returnData = {"Main": iLocsReturn}

		if nodesToDelete: pm.delete(nodesToDelete)
		return returnData

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

		status, ctrlAuthority = mnsUtils.validateAttrAndGet(rootGuide, "ctrlAuthority", None)
		if ctrlAuthority:
			if ctrlAuthority.hasAttr("aroundCenter"):
				inCons = ctrlAuthority.aroundCenter.listConnections(s = False, d = True)
				for inNode in inCons:
					if type(inNode) == pm.nodetypes.MnsLipZip:
						pm.delete(inNode)

def postConstruct(mansur, MnsBuildModule, **kwargs):
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	rootGuide = MnsBuildModule.rootGuide

	status, jawRootGuide = mnsUtils.validateAttrAndGet(rootGuide, "jawRootGuide", None)
	jawRootGuide = mnsUtils.validateNameStd(jawRootGuide)
	selfMainCtrl = blkUtils.getCtrlAuthFromRootGuide(rootGuide)

	if jawRootGuide:
		jawCtrl = blkUtils.getCtrlAuthFromRootGuide(jawRootGuide)
		if jawCtrl:
			if selfMainCtrl:
				cornersFollowAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", min = 0.0, max = 1.0, value = 0.5, name = "cornersFollowJaw", replace = True)[0]

				status, cornerA = mnsUtils.validateAttrAndGet(selfMainCtrl, "jawConnect_cornerA", None)
				status, upperMid = mnsUtils.validateAttrAndGet(selfMainCtrl, "jawConnect_upperMid", None)
				status, cornerB = mnsUtils.validateAttrAndGet(selfMainCtrl, "jawConnect_cornerB", None)
				status, lowerMid = mnsUtils.validateAttrAndGet(selfMainCtrl, "jawConnect_lowerMid", None)
				
				if cornerA and cornerB and upperMid and lowerMid:
					for ctrl in [lowerMid, cornerA, cornerB]:
						ctrl = mnsUtils.validateNameStd(ctrl)
						if ctrl:
							ctrlOffset = blkUtils.getOffsetGrpForCtrl(ctrl)

							origParent = ctrlOffset.node.getParent()
							offsetA = mnsUtils.createOffsetGroup(ctrlOffset, type = "modifyGrp")
							offsetB = mnsUtils.createOffsetGroup(offsetA, type = "modifyGrp")
							
							pm.parent(ctrlOffset.node, origParent)
							pm.delete(pm.parentConstraint(jawCtrl.node, offsetB.node))
							pm.makeIdentity(offsetA.node)
							pm.parent(ctrlOffset.node, offsetA.node)

							if ctrl.node == lowerMid:
								jawCtrl.node.t >> offsetA.node.t
								jawCtrl.node.r >> offsetA.node.r
								jawCtrl.node.s >> offsetA.node.s
							else:
								mnsNodes.mdNode(jawCtrl.node.t, 
												[cornersFollowAttr, cornersFollowAttr, cornersFollowAttr],
												offsetA.node.t)			
								mnsNodes.mdNode(jawCtrl.node.r, 
												[cornersFollowAttr, cornersFollowAttr, cornersFollowAttr],
												offsetA.node.r)		
								jawCtrl.node.s >> offsetA.node.s

							"""
							lowerMidCtrl = mnsUtils.validateNameStd(lowerMid)
							upperMidCtrl = mnsUtils.validateNameStd(upperMid)
							if lowerMidCtrl and upperMidCtrl:
								bindDistance = mnsUtils.distBetween(lowerMidCtrl.node, upperMidCtrl.node)
								distBetNode = mnsNodes.distBetweenNode(lowerMidCtrl.node.worldMatrix[0], upperMidCtrl.node.worldMatrix[0], None)
								lowerMidCtrl.node.worldMatrix[0] >> distBetNode.node.inMatrix1
								upperMidCtrl.node.worldMatrix[0] >> distBetNode.node.inMatrix2

								conditionNodeA = mnsNodes.conditionNode(distBetNode.node.distance, 
																		bindDistance, 
																		jawCtrl.node.r, 
																		[0.0, 0.0, 0.0], 
																		offsetA.node.r, 
																		operation = 4)
							"""

					lipsPullAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", value = -0.6, name = "cornerPullAmount", replace = True)[0]	
					lipsPullMaxDegreeAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", value = 30.0, name = "cornersPullDegreeRange", replace = True)[0]	
					lipsPullMapToJawRotAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "enum", value = ["x", "y", "z"], name = "lipsPullMapToJawRot", replace = True)[0]	

					choiceNode = mnsNodes.choiceNode([jawCtrl.node.rx, jawCtrl.node.ry, jawCtrl.node.rz], None)
					lipsPullMapToJawRotAttr >> choiceNode.node.selector

					unitConvertion = pm.createNode("unitConversion")
					unitConvertion.conversionFactor.set(57.296)
					choiceNode.node.output >> unitConvertion.input

					cornersPullRange = mnsNodes.setRangeNode([lipsPullAttr, 0.0, 0.0],
															[0, 0, 0],
															[lipsPullMaxDegreeAttr, lipsPullMaxDegreeAttr, lipsPullMaxDegreeAttr],
															[0, 0, 0],
															[unitConvertion.output, None, None],
															[None, None, None])

					for ctrl in [cornerA, cornerB]:
						offsetA = mnsUtils.createOffsetGroup(ctrl, type = "modifyGrp")
						cornersPullRange.node.outValueX >> offsetA.node.tx

	status, doCheekRaise = mnsUtils.validateAttrAndGet(rootGuide, "doCheekRaise", False)
	if doCheekRaise:
		status, pushValue = mnsUtils.validateAttrAndGet(rootGuide, "pushValue", 0.0)
		status, raiseValue = mnsUtils.validateAttrAndGet(rootGuide, "raiseValue", 0.0)
		
		status, connectRaiseToAxis = mnsUtils.validateAttrAndGet(rootGuide, "connectRaiseToAxis", "y")
		status, connectPushToAxis = mnsUtils.validateAttrAndGet(rootGuide, "connectPushToAxis", "z")

		for side in "rl":
			status, mouthCornerCtrl = mnsUtils.validateAttrAndGet(selfMainCtrl, side + "_cheekRaise", None)
			mouthCornerCtrl = mnsUtils.validateNameStd(mouthCornerCtrl)
			if mouthCornerCtrl:
				mouthCornerCtrl = mouthCornerCtrl.node
				status, cheekCtrl = mnsUtils.validateAttrAndGet(rootGuide, side + "_CheekRaiseRoot", None)
				cheekCtrl = mnsUtils.validateNameStd(cheekCtrl)
				if cheekCtrl:
					cheekCtrl = blkUtils.getCtrlAuthFromRootGuide(cheekCtrl)
					if cheekCtrl:
						cheekCtrl = cheekCtrl.node
						if cheekCtrl and mouthCornerCtrl:
							mnsUtils.addAttrToObj(mouthCornerCtrl, type = "enum", value = ["______"], name = "cheekRaise", replace = True, locked = True)
							raiseAmountAttr = mnsUtils.addAttrToObj(mouthCornerCtrl, name = "raiseAmount" , type = "float", value = raiseValue, locked = False, cb = True, keyable = True, min = 0.0, max = 100.0)[0]
							pushAmountAttr = mnsUtils.addAttrToObj(mouthCornerCtrl, name = "pushAmount" , type = "float", value = pushValue, locked = False, cb = True, keyable = True, min = 0.0, max = 100.0)[0]
							cheeckModify = mnsUtils.createOffsetGroup(cheekCtrl, type = "modifyGrp")


							mdNode = mnsNodes.mdNode([mouthCornerCtrl.ty, mouthCornerCtrl.ty, 0], [raiseAmountAttr, pushAmountAttr, 0], None)
							clampNode = mnsNodes.clampNode(mdNode.node.output, #in 
														[100,100,0], #max
														[0,0,0], #min
														[None, None, None]) #out

							raiseSourceAttribute = clampNode.node.outputR
							pushSourceAttribute = clampNode.node.outputG

							if connectRaiseToAxis == ("-x", "-y", "-z"):
								mdlNode = mnsNodes.mdlNode(raiseSourceAttribute, -1.0, None)
								raiseSourceAttribute = mdlNode.node.output
							if connectPushToAxis == ("-x", "-y", "-z"):
								mdlNode = mnsNodes.mdlNode(pushSourceAttribute, -1.0, None)
								pushSourceAttribute = mdlNode.node.output

							if connectRaiseToAxis == ("x" or "-x"): raiseSourceAttribute >> cheeckModify.node.tx
							elif connectRaiseToAxis == ("y" or "-y"): raiseSourceAttribute >> cheeckModify.node.ty
							elif connectRaiseToAxis == ("z" or "-z"): raiseSourceAttribute >> cheeckModify.node.tz

							if connectPushToAxis == ("x" or "-x"): pushSourceAttribute >> cheeckModify.node.tx
							elif connectPushToAxis == ("y" or "-y"): pushSourceAttribute >> cheeckModify.node.ty
							elif connectPushToAxis == ("z" or "-z"): pushSourceAttribute >> cheeckModify.node.tz