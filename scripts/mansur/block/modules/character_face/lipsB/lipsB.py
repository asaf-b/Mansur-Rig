"""Author: Asaf Ben-Zur
Best used for: Lips
This module was designed around lips behaviour.
This module has a few layers that will allow general as well as extremely fiddle control (based on parameters) over the lips deformation.
Some of the main features in this module include: Macro corner controls, Along Surface feature, Around Center Feature, Jaw connections, Global "Full-Lips" control, Zip Controls, Curve meet controls, Tweak controls, Cheek Raise connection,  and much more.
The joint structure of this module will be dictated by input vertices on a given mesh.
"""



from maya import cmds
import pymel.core as pm

import json

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
					curve = pm.polyToCurve(form = 0, degree = 1, ch = False, conformToSmoothMeshPreview = False)
					if curve:
						curve = mnsUtils.checkIfObjExistsAndSet(curve[0]) 
						bindCurves[k] = curve

			#check curves direction. if invalid, flip
			if bindCurves[0] and bindCurves[1]:
				upperFirstCv = bindCurves[0].getShape().getCV(0)
				if upperFirstCv.x < 0.0: pm.reverseCurve(bindCurves[0], ch= False, rpo = True)

				lowerFirstCv = bindCurves[1].getShape().getCV(0)
				if lowerFirstCv.x < 0.0: pm.reverseCurve(bindCurves[1], ch= False, rpo = True)

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
	tweakerIndex = 0

	cusPivCtrls = []
	upperCurlPivGuide, lowerCurlPivGuide = None, None
	upperLeftMidGuide, upperRightMidGuide = None, None
	lowerLeftMidGuide, lowerRightMidGuide = None, None

	if customGuides:
		for guide in customGuides: 
			if "UpperCurl" in guide.name: upperCurlPivGuide = guide
			elif "LowerCurl" in guide.name: lowerCurlPivGuide = guide
			elif "UpperLeft" in guide.name: upperLeftMidGuide = guide
			elif "UpperRight" in guide.name: upperRightMidGuide = guide
			elif "LowerLeft" in guide.name: lowerLeftMidGuide = guide
			elif "LowerRight" in guide.name: lowerRightMidGuide = guide

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

	#first create the bind curves from the input edges
	curveGrp = mnsUtils.createNodeReturnNameStd(parentNode = mainCtrl, side =  rootGuide.side, body = rootGuide.body + "Curves", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)
	curveGrp.node.v.set(False)

	bindCurves, upperEdge, lowerEdge = createBindCurvesFromModuleSettings(mansur, rootGuide)
	if bindCurves[0] and bindCurves[1]:
		#rename the bind curves and orgenize them
		nameStdA = MnsNameStd(side = rootGuide.side, body = rootGuide.body + "UpperBind", alpha = rootGuide.alpha, id = rootGuide.id, type = mnsTypeDict["curve"])
		nameStdA.findNextIncrement()
		bindCurves[0].rename(nameStdA.name)
		upperBindCurve = bindCurves[0]
		nameStdB = MnsNameStd(side = rootGuide.side, body = rootGuide.body + "LowerBind", alpha = rootGuide.alpha, id = rootGuide.id, type = mnsTypeDict["curve"])
		nameStdB.findNextIncrement()
		bindCurves[1].rename(nameStdB.name)
		pm.parent(bindCurves, curveGrp.node)
		lowerBindCurve = bindCurves[1]

		#get corners positions
		upperCVs = upperBindCurve.getShape().getCVs()
		rightCornerPosition = pm.datatypes.Vector(upperCVs[0])
		leftCornerPosition = pm.datatypes.Vector(upperCVs[len(upperCVs) - 1])
		if rightCornerPosition.x > 0.0:
			leftCornerPosition = pm.datatypes.Vector(upperCVs[0])
			rightCornerPosition = pm.datatypes.Vector(upperCVs[len(upperCVs) - 1])

		upperLeftMidPosition = pm.datatypes.Vector(pm.xform(upperLeftMidGuide.node, ws = True, t = True, q = True))
		upperRightMidPosition = pm.datatypes.Vector(pm.xform(upperRightMidGuide.node, ws = True, t = True, q = True))
		lowerLeftMidPosition = pm.datatypes.Vector(pm.xform(lowerLeftMidGuide.node, ws = True, t = True, q = True))
		lowerRightMidPosition = pm.datatypes.Vector(pm.xform(lowerRightMidGuide.node, ws = True, t = True, q = True))
		status, midsPosition = mnsUtils.validateAttrAndGet(rootGuide, "midsPosition", 0)

		#get mid positions
		poci = pm.createNode("pointOnCurveInfo")
		poci.turnOnPercentage.set(True)
		upperBindCurve.worldSpace[0] >> poci.inputCurve
		poci.parameter.set(0.5)
		upperMidPosition = poci.result.position.get()
		upperMidPosition.x = 0.0
		if midsPosition == 0:
			poci.parameter.set(0.25)
			upperLeftMidPosition = poci.result.position.get()
			poci.parameter.set(0.75)
			upperRightMidPosition = poci.result.position.get()
		lowerBindCurve.worldSpace[0] >> poci.inputCurve
		poci.parameter.set(0.5)
		lowerMidPosition = poci.result.position.get()
		lowerMidPosition.x = 0.0
		if midsPosition == 0:
			poci.parameter.set(0.25)
			lowerLeftMidPosition = poci.result.position.get()
			poci.parameter.set(0.75)
			lowerRightMidPosition = poci.result.position.get()
		pm.delete(poci)

		#positions aquired, create the main controls
		status, cornerControlShape = mnsUtils.validateAttrAndGet(rootGuide, "cornerControlShape", "fourArrow")
		status, upperLowerControlShape = mnsUtils.validateAttrAndGet(rootGuide, "upperLowerControlShape", "squareRound")
		status, midsControlShape = mnsUtils.validateAttrAndGet(rootGuide, "midsControlShape", "circle")

		reorderedPositions =  {
								0: {"pos": leftCornerPosition, "isCorner":True, "isMid": False, "side": "l", "bodySuffix": "Corner"}, 
								1: {"pos": upperLeftMidPosition, "isCorner":False, "isMid": False, "side": "l", "bodySuffix": "UpperMid"}, 
								2: {"pos": upperMidPosition, "isCorner":False, "isMid": True, "side": "c", "bodySuffix": "UpperMid"}, 
								3: {"pos": upperRightMidPosition, "isCorner":False, "isMid": False, "side": "r", "bodySuffix": "UpperMid"}, 
								4: {"pos": rightCornerPosition, "isCorner":True, "isMid": False, "side": "r", "bodySuffix": "Corner"}, 
								5: {"pos": lowerRightMidPosition, "isCorner":False, "isMid": False, "side": "r", "bodySuffix": "lowerMid"}, 
								6: {"pos": lowerMidPosition, "isCorner":False, "isMid": True, "side": "c", "bodySuffix": "lowerMid"}, 
								7: {"pos": lowerLeftMidPosition, "isCorner":False, "isMid": False, "side": "l", "bodySuffix": "lowerMid"}
							}

		for positionIndex in sorted(reorderedPositions.keys()):
			controlShape = midsControlShape
			if reorderedPositions[positionIndex]["isCorner"]: 
				controlShape = cornerControlShape
			elif reorderedPositions[positionIndex]["isMid"]:
				controlShape = upperLowerControlShape
			
			#createNewPositionLoc
			newPosition = pm.spaceLocator()
			pm.xform(newPosition, ws = True, a = True, t = reorderedPositions[positionIndex]["pos"])
			
			#and orient it
			if reorderedPositions[positionIndex]["isCorner"]:
				aimPosition = (reorderedPositions[1]["pos"] + reorderedPositions[7]["pos"] ) / 2
				aimVector = (1,0,0)
				if reorderedPositions[positionIndex]["side"] == "r":
					aimPosition = (reorderedPositions[3]["pos"] + reorderedPositions[5]["pos"] ) / 2
					aimVector = (-1,0,0)

				aimTarget = pm.spaceLocator()
				pm.xform(aimTarget, ws = True, a = True, t = aimPosition)
				pm.delete(pm.pointConstraint(newPosition, aimTarget, sk = ["x", "z"]))
				pm.delete(pm.aimConstraint(aimTarget, newPosition, aimVector = aimVector, upVector = (0,1,0), worldUpType = "scene"))
				pm.delete(aimTarget)
			elif not reorderedPositions[positionIndex]["isMid"]:
				aimPosition = (reorderedPositions[2]["pos"] + reorderedPositions[6]["pos"] ) / 2
				aimVector = (1,0,0)
				if reorderedPositions[positionIndex]["side"] == "r":
					aimVector = (-1,0,0)
				aimTarget = pm.spaceLocator()
				pm.xform(aimTarget, ws = True, a = True, t = aimPosition)
				pm.delete(pm.pointConstraint(newPosition, aimTarget, sk = ["x", "z"]))
				pm.delete(pm.aimConstraint(aimTarget, newPosition, aimVector = aimVector, upVector = (0,1,0), worldUpType = "scene"))
				pm.delete(aimTarget)

				if "lower" in reorderedPositions[positionIndex]["bodySuffix"]:
					newPosition.sx.set(-1)
					newPosition.sy.set(-1)
					newPosition.sz.set(-1)
					newPosition.ry.set(newPosition.ry.get() + 180)
			elif positionIndex == 6: #lower mid main, flip Y
				newPosition.sx.set(-1)
				newPosition.sy.set(-1)
				newPosition.sz.set(-1)
				newPosition.ry.set(newPosition.ry.get() + 180)


			ctrl = blkCtrlShps.ctrlCreate(
							nameReference = rootGuide,
							bodySuffix = reorderedPositions[positionIndex]["bodySuffix"],
							side = reorderedPositions[positionIndex]["side"],
							color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
							controlShape = controlShape,
							matchTransform = newPosition,
							matchScale = True,
							alongAxis = 2,
							scale = modScale * 0.2, 
							parentNode = mainCtrl,
							symmetryType = symmetryType,
							doMirror = True,
							createSpaceSwitchGroup = False,
							createOffsetGrp = True,
							isFacial = MnsBuildModule.isFacial)
			pm.delete(newPosition)
			blkUtils.setCtrlCol(ctrl, MnsBuildModule.rigTop)
			ctrlsCollect.append(ctrl)
			reorderedPositions[positionIndex]["ctrl"] = ctrl
			reorderedPositions[positionIndex]["offsetGrp"] = blkUtils.getOffsetGrpForCtrl(ctrl)

			"""
			#set transformation locks and sShapes
			if reorderedPositions[positionIndex]["isCorner"]: #corners
				pass
			elif not reorderedPositions[positionIndex]["isMid"]: #mid left and right
				mnsUtils.lockAndHideTransforms(ctrl.node, t = False, lock = True)
			else: #upper lower
				pass
			"""

		attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "l_cheekRaise", value= "", replace = True)[0]
		reorderedPositions[0]["ctrl"].node.message >> attrStore
		attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "message", name = "r_cheekRaise", value= "", replace = True)[0]
		reorderedPositions[4]["ctrl"].node.message >> attrStore

		#main Ctrls Built
		#create the tweak curves
		upperTweakTransforms = [
								reorderedPositions[0]["ctrl"],
								reorderedPositions[0]["ctrl"], 
								reorderedPositions[1]["ctrl"], 
								reorderedPositions[2]["ctrl"], 
								reorderedPositions[3]["ctrl"], 
								reorderedPositions[4]["ctrl"],
								reorderedPositions[4]["ctrl"]
								]
		lowerTweakTransforms = [
								reorderedPositions[0]["ctrl"],
								reorderedPositions[0]["ctrl"], 
								reorderedPositions[7]["ctrl"], 
								reorderedPositions[6]["ctrl"],
								reorderedPositions[5]["ctrl"], 
								reorderedPositions[4]["ctrl"],
								reorderedPositions[4]["ctrl"]
								]

		upperTweakBtc = mnsNodes.mnsBuildTransformsCurveNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + "UpperTweak", 
											transforms = upperTweakTransforms, 
											deleteCurveObjects = False, 
											buildOffsetCurve = False,
											buildMode = 1,
											degree = 2)

		lowerTweakBtc = mnsNodes.mnsBuildTransformsCurveNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body + "LowerTweak", 
											transforms = lowerTweakTransforms, 
											deleteCurveObjects = False, 
											buildOffsetCurve = False,
											buildMode = 1,
											degree = 2)

		status, upCurveOffset = mnsUtils.validateAttrAndGet(rootGuide, "upCurveOffset", 1.0)
		status, curveResolution = mnsUtils.validateAttrAndGet(rootGuide, "curveResolution", 24)
		sampleMode = 0
		if midsPosition == 1: sampleMode = 2
		mnsCurveZipNode = mnsNodes.mnsLipZipNode(
											side = rootGuide.side, 
											alpha = rootGuide.alpha, 
											id = rootGuide.id, 
											body = rootGuide.body, 
											bindCurveA =upperBindCurve.getShape().worldSpace[0],
											bindCurveB = lowerBindCurve.getShape().worldSpace[0],
											centerMatrix = mainCtrl.node.worldMatrix[0],
											upCurveOffset = upCurveOffset,
											substeps = curveResolution,
											aroundCenter = False,
											buildMode = 0,
											sampleMode = sampleMode
											)
		mnsCurveZipNode.node.tweakMode.set(0)
		blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> mnsCurveZipNode.node.globalScale

		upperCurve = upperTweakBtc["outCurve"]
		upperCurve.node.create.disconnect()
		pm.parent(upperCurve.node, curveGrp.node)
		upperTweakBtc["node"].node.outCurve >> mnsCurveZipNode.node.tweakCurveA[0]
		upperCurve.node.worldSpace[0] >> mnsCurveZipNode.node.tweakCurveABase[0]

		lowerCurve = lowerTweakBtc["outCurve"]
		lowerCurve.node.create.disconnect()
		pm.parent(lowerCurve.node, curveGrp.node)
		lowerTweakBtc["node"].node.outCurve >> mnsCurveZipNode.node.tweakCurveB[0]
		lowerCurve.node.worldSpace[0] >> mnsCurveZipNode.node.tweakCurveBBase[0]


		#Curls
		upperMidIsolated, loweMidIsolated = None , None
		iLocs = blkUtils.getModuleInterpJoints(rootGuide)
		if upperCurlPivGuide and lowerCurlPivGuide: 
			nameArray = ["Upper", "Lower"]
			positionMatchArray = [upperCurlPivGuide, lowerCurlPivGuide]

			for k, positionIndex in enumerate([2, 6]):
				forceMirrorGrp = False
				if k == 1: forceMirrorGrp = True

				##create curl ctrl
				curlCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
					color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
					matchPosition = positionMatchArray[k],
					matchOrientation = reorderedPositions[positionIndex]["ctrl"],
					bodySuffix = nameArray[k] + "Curl",
					controlShape = upperLowerControlShape,
					scale = modScale * 0.075, 
					parentNode = reorderedPositions[positionIndex]["ctrl"],
					alongAxis = 2,
					side = "c",
					symmetryType = 3,
					doMirror = True,
					forceMirrorGrp = forceMirrorGrp,
					createSpaceSwitchGroup = False,
					createOffsetGrp = True,
					isFacial = MnsBuildModule.isFacial)
				ctrlsCollect.append(curlCtrl)

				curlOffset = mnsUtils.validateNameStd(curlCtrl.node.getParent())
				baseCurlLoc = mnsUtils.createNodeReturnNameStd(parentNode = curlOffset, side = curlCtrl.side, body = curlCtrl.body + "Base", alpha = curlCtrl.alpha, id = curlCtrl.id, buildType = "locator", incrementAlpha = False)
				baseCurlLoc.node.v.set(False)
				pm.makeIdentity(baseCurlLoc.node)

				mnsUtils.addAttrToObj([curlCtrl.node], type = "enum", value = ["______"], name = "curl", replace = True, locked = True)
				curlFalloffAttr = mnsUtils.addAttrToObj([curlCtrl.node], type = "float", value = 0.5, max = 1.0, min = 0.0, name = "curlFalloff", replace = True)[0]

				if k == 0:
					baseCurlLoc.node.worldMatrix[0] >> mnsCurveZipNode.node.upperCurlBaseMatrix
					curlCtrl.node.worldMatrix[0] >> mnsCurveZipNode.node.upperCurlMatrix
					curlFalloffAttr >> mnsCurveZipNode.node.upperCurlFalloff
				else:
					baseCurlLoc.node.worldMatrix[0] >> mnsCurveZipNode.node.lowerCurlBaseMatrix
					curlCtrl.node.worldMatrix[0] >> mnsCurveZipNode.node.lowerCurlMatrix
					curlFalloffAttr >> mnsCurveZipNode.node.lowerCurlFalloff

				#curl
				transformsArray = iLocs[0:len(upperEdge)]
				if k == 1: transformsArray = iLocs[len(upperEdge):]

				outputValuesArray = []
				for transform in transformsArray:
					outputValuesArray.append(transform.node.rx)

				if k == 1:
					mdlTranLoc = mnsUtils.createNodeReturnNameStd(parentNode = curlCtrl, side = curlCtrl.side, body = curlCtrl.body + "RFAAngleTransition", alpha = curlCtrl.alpha, id = curlCtrl.id, buildType = "locator", incrementAlpha = False)
					mdlTranLoc.node.v.set(False)
					pm.makeIdentity(mdlTranLoc.node)
					mdlNode = mnsNodes.mdlNode(curlCtrl.node.rx, -1.0, mdlTranLoc.node.rx)
					mnsRemapFloatArrayNode = mnsNodes.mnsRemapFloatArrayNode(value = mdlTranLoc.node.rx, angleOutputAsDegrees = False, outputCount = len(transformsArray), outValues = outputValuesArray)
				else:
					mnsRemapFloatArrayNode = mnsNodes.mnsRemapFloatArrayNode(value = curlCtrl.node.rx, angleOutputAsDegrees = False, outputCount = len(transformsArray), outValues = outputValuesArray)


				#create isolated mid ctrl
				bodySuffix = "UpperMidIsolated"
				if positionIndex == 6: bodySuffix = "LowerMidIsolated"

				ctrl = blkCtrlShps.ctrlCreate(
									nameReference = rootGuide,
									bodySuffix = bodySuffix,
									side = reorderedPositions[positionIndex]["side"],
									color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
									controlShape = upperLowerControlShape,
									matchTransform = reorderedPositions[positionIndex]["ctrl"],
									matchScale = True,
									alongAxis = 2,
									scale = modScale * 0.1, 
									parentNode = curlCtrl,
									symmetryType = symmetryType,
									doMirror = False,
									createSpaceSwitchGroup = False,
									createOffsetGrp = True,
									isFacial = MnsBuildModule.isFacial)
				ctrlsCollect.append(ctrl)
				#mnsUtils.lockAndHideTransforms(ctrl.node, t = False, lock = True)
				if positionIndex == 2:
					upperMidIsolated = ctrl
					#replace the original mid ctrl in the new isolated mid within the tweak btc nodes 
					upperMidIsolated.node.worldMatrix[0] >> upperTweakBtc["node"].node.transforms[3].matrix
				else:
					loweMidIsolated = ctrl
					#replace the original mid ctrl in the new isolated mid within the tweak btc nodes 
					loweMidIsolated.node.worldMatrix[0] >> lowerTweakBtc["node"].node.transforms[3].matrix



		#connect zips
		mnsUtils.addAttrToObj([reorderedPositions[0]["ctrl"].node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
		zipAttr = mnsUtils.addAttrToObj([reorderedPositions[0]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "zip", replace = True)[0]
		mnsNodes.setRangeNode([1, 1, 1],
								[0, 0, 0],
								[10, 10, 10],
								[0, 0, 0],
								[zipAttr, None, None],
								[mnsCurveZipNode.node.zipStart, None, None])
		falloffAttr = mnsUtils.addAttrToObj([reorderedPositions[0]["ctrl"].node], type = "float", value = 0.5, max = 1.0, min = 0.01, name = "zipFalloff", replace = True)[0]
		falloffAttr >> mnsCurveZipNode.node.zipStartFalloff

		mnsUtils.addAttrToObj([reorderedPositions[4]["ctrl"].node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
		zipAttr = mnsUtils.addAttrToObj([reorderedPositions[4]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "zip", replace = True)[0]
		mnsNodes.setRangeNode([1, 1, 1],
								[0, 0, 0],
								[10, 10, 10],
								[0, 0, 0],
								[zipAttr, None, None],
								[mnsCurveZipNode.node.zipEnd, None, None])
		falloffAttr = mnsUtils.addAttrToObj([reorderedPositions[4]["ctrl"].node], type = "float", value = 0.5, max = 1.0, min = 0.01, name = "zipFalloff", replace = True)[0]
		falloffAttr >> mnsCurveZipNode.node.zipEndFalloff

		#connect mids
		mnsUtils.addAttrToObj([reorderedPositions[2]["ctrl"].node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
		toMidAttr = mnsUtils.addAttrToObj([reorderedPositions[2]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toMid", replace = True)[0]
		toLowerAttr = mnsUtils.addAttrToObj([reorderedPositions[2]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toLower", replace = True)[0]
		mnsNodes.setRangeNode([1, 1, 1],
								[0, 0, 0],
								[10, 10, 10],
								[0, 0, 0],
								[toLowerAttr, toMidAttr, None],
								[mnsCurveZipNode.node.AToB, mnsCurveZipNode.node.AToMid, None]) 
		sShapeAttr = mnsUtils.addAttrToObj([reorderedPositions[2]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = -10.0, name = "sShape", replace = True)[0]
		sShapeAttr >> mnsCurveZipNode.node.sCurveA

		mnsUtils.addAttrToObj([reorderedPositions[6]["ctrl"].node], type = "enum", value = ["______"], name = "zipControls", replace = True, locked = True)
		toMidAttr = mnsUtils.addAttrToObj([reorderedPositions[6]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toMid", replace = True)[0]
		toLowerAttr = mnsUtils.addAttrToObj([reorderedPositions[6]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = 0.0, name = "toUpper", replace = True)[0]
		mnsNodes.setRangeNode([1, 1, 1],
								[0, 0, 0],
								[10, 10, 10],
								[0, 0, 0],
								[toLowerAttr, toMidAttr, None],
								[mnsCurveZipNode.node.BToA, mnsCurveZipNode.node.BToMid, None])
		sShapeAttr = mnsUtils.addAttrToObj([reorderedPositions[6]["ctrl"].node], type = "float", value = 0.0, max = 10.0, min = -10.0, name = "sShape", replace = True)[0]
		sShapeAttr >> mnsCurveZipNode.node.sCurveB

		### curve zip attrs #####
		mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["______"], name = "globalModuleSettings", replace = True, locked = True)

		status, midCurveHeight = mnsUtils.validateAttrAndGet(rootGuide, "midCurveHeight", 0.5)
		blinkHeightAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", min = 0.0, max = 1.0, value = midCurveHeight, name = "midCurveHeight", replace = True)[0]
		blinkHeightAttr >> mnsCurveZipNode.node.midBias

		status, aroundCenter = mnsUtils.validateAttrAndGet(rootGuide, "aroundCenter", False)
		aroundCenterAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = aroundCenter, name = "aroundCenter", replace = True)[0]
		aroundCenterAttr >> mnsCurveZipNode.node.aroundCenter

		conformToMeetAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "bool", value = False, name = "conformToMeetPoint", replace = True)[0]
		conformToMeetAttr >> mnsCurveZipNode.node.conformToMeetPoint

		curveToConformAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "enum", value = ["curveA", "curveB"], name = "alterCurveToMeetPoint", replace = True)[0]
		curveToConformAttr >> mnsCurveZipNode.node.curveToConform

		confDistAttr = mnsUtils.addAttrToObj([mainCtrl.node], type = "float", value = 0.2, name = "conformDistanceThreshold", replace = True)[0]
		confDistAttr >> mnsCurveZipNode.node.conformDistancethreshold

		# store jaw connections ctrls
		for ctrlIdx in reorderedPositions.keys():
			reorderedPositions[ctrlIdx]["ctrl"] = reorderedPositions[ctrlIdx]["ctrl"].node.nodeName()
			reorderedPositions[ctrlIdx]["offsetGrp"] = reorderedPositions[ctrlIdx]["offsetGrp"].node.nodeName()
			del reorderedPositions[ctrlIdx]["pos"]
		attrStore = mnsUtils.addAttrToObj([mainCtrl.node], type = "string", name = "jawConnect_data", value= json.dumps(reorderedPositions), replace = True)[0]
			
	########### Transfer Authority ###########
	blkUtils.transferAuthorityToCtrl(relatedJnt, mainCtrl)
	
	#create a world orient loc and parent it under the main control
	worldOrientLoc = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "WorldOrient", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
	pm.parent(worldOrientLoc.node, mainCtrl.node)	 

	#connect lipZip output curves to orig poc nodes, essentially transfer authority.
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
			status, layerBInterpolation = mnsUtils.validateAttrAndGet(rootGuide, "layerBInterpolation", 1)
			if doLayerBCtrls:
				layeBCtrlsGrp = mnsUtils.createNodeReturnNameStd(parentNode = animStaticGrp, side =  rootGuide.side, body = rootGuide.body + "LayBCtrls", alpha = rootGuide.alpha, id =  rootGuide.id, buildType = "group", incrementAlpha = False)

				status, numLayerBCtrlsPerSection = mnsUtils.validateAttrAndGet(rootGuide, "numLayerBCtrlsPerSection", 9)
				if (numLayerBCtrlsPerSection % 2) == 0: numLayerBCtrlsPerSection += 1

				status, layerBControlShape = mnsUtils.validateAttrAndGet(rootGuide, "layerBControlShape", "cube")

				layeBoffsets = []
				layerBCtrls = []
				for b in range(numLayerBCtrlsPerSection):
					contin = True

					ctrlType = "ctrl"
					if k == 1 and (b == 0 or b == numLayerBCtrlsPerSection - 1):
						ctrlType = "techCtrl"

					side = "c"
					if b > (numLayerBCtrlsPerSection  / 2): side = "r"
					if b < (numLayerBCtrlsPerSection  / 2): side = "l"

					bodySuffix = "LayBUpper"
					if k == 1: bodySuffix = "LayBLower"

					idx = rootGuide.id
					if side == "l" and k == 1:
						idx = b + 1
					elif side == "r":
						idx = ((numLayerBCtrlsPerSection  - 1)  / 2) - (b - ((numLayerBCtrlsPerSection  - 1)  / 2)) + 1

					layerBCtrl = blkCtrlShps.ctrlCreate(nameReference = rootGuide,
							color = blkUtils.getCtrlCol(rootGuide, MnsBuildModule.rigTop),
							side = side,
							id = idx,
							bodySuffix = bodySuffix,
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

					blkUtils.setCtrlCol(layerBCtrl, MnsBuildModule.rigTop)

					if ctrlType == "ctrl":
						if side == "c" and k == 1:
							mirGrp = blkCtrlShps.createMirrorGroup(layerBCtrl, 3)
						elif side == "r" and k == 0:
							mirGrp = blkCtrlShps.createMirrorGroup(layerBCtrl, 2)
						elif side == "l" and k == 1:
							mirGrp = blkCtrlShps.createMirrorGroup(layerBCtrl, 4)
						elif side == "r" and k == 1:
							mirGrp = blkCtrlShps.createMirrorGroup(layerBCtrl, 8)
							mirGrp.node.s.set((1.0,-1.0,-1.0))

					if layerBInterpolation < 1:
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

				status, layerBSamplingMode = mnsUtils.validateAttrAndGet(rootGuide, "layerBSamplingMode", 3)
				if layerBSamplingMode == 2: layerBSamplingMode = 3

				pocn = mnsNodes.mnsPointsOnCurveNode(
										transforms = layeBoffsets,
										side = rootGuide.side, 
										alpha = rootGuide.alpha, 
										id = rootGuide.id, 
										body = rootGuide.body + inputNames[k] + "LayerB", 
										inputCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k]),
										inputUpCurve = mnsCurveZipNode.node.attr("outCurve" + inputAttrSuffix[k] + "Offset"),
										buildOutputs = False,
										buildMode = layerBSamplingMode,
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
							buildMode = layerBInterpolation,
							degree = 3)

				btcNodeTweak = mnsNodes.mnsBuildTransformsCurveNode(
							side = rootGuide.side, 
							alpha = rootGuide.alpha, 
							id = rootGuide.id, 
							body = rootGuide.body + inputNames[k].capitalize() + "TweakB", 
							transforms = layerBCtrls, 
							deleteCurveObjects = True, 
							buildMode = layerBInterpolation,
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
											doScale = True,
											doRotate = True,
											rotateMode = 4,
											upMode = 6,
											connectRotate = True,
											connectChildrenRotate = True,
											aimAxis = 1,
											upAxis = 0,
											numOutputs = len(transformsArray),
											isolatePolesRotation = False
											)
			pocn["node"].node.squashMode.set(4)
			blkUtils.getGlobalScaleAttrFromTransform(mainCtrl) >> pocn["node"].node.globalScale
			worldOrientLoc.node.worldMatrix[0] >> pocn["node"].node.upObject
			worldOrientLoc.node.worldMatrix[0] >> pocn["node"].node.aimObject
			pocn["node"].node.objectOrientAimAxis.set(1)
			pocn["node"].node.objectOrientUpAxis.set(0)

			#connect all custom tweakers
			if k == 0:
				for b, ctrlIndex in enumerate([1,2,3]):
					ctrl = mnsUtils.validateNameStd(reorderedPositions[ctrlIndex]["ctrl"])
					if ctrlIndex == 2: 
						ctrl = upperMidIsolated

					if ctrl:
						mnsUtils.addAttrToObj([ctrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
						positionAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = (1.0 / float(4)) * ctrlIndex, name = "position", replace = True, min = 0.0, max = 1.0)[0]
						falloffAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = 0.5, name = "falloff", replace = True, min = 0.01)[0]
						
						positionAttr >> pocn["node"].node.customPosition[b].uPosition
						falloffAttr >> pocn["node"].node.customPosition[b].falloff

						if ctrlIndex == 1:
							mnsNodes.mdlNode(ctrl.node.rx, -1, pocn["node"].node.customPosition[b].aimRotation)
							ctrl.node.ry >> pocn["node"].node.customPosition[b].twist
							mnsNodes.mdlNode(ctrl.node.rz, -1, pocn["node"].node.customPosition[b].tertiaryRotation)
							ctrl.node.sx >> pocn["node"].node.customPosition[b].tertiaryScale
							ctrl.node.sy >> pocn["node"].node.customPosition[b].scaleAim
							ctrl.node.sz >> pocn["node"].node.customPosition[b].scaleUp
						elif ctrlIndex == 2:
							ctrl.node.rx >> pocn["node"].node.customPosition[b].aimRotation
							ctrl.node.ry >> pocn["node"].node.customPosition[b].twist
							ctrl.node.rz >> pocn["node"].node.customPosition[b].tertiaryRotation
							ctrl.node.sx >> pocn["node"].node.customPosition[b].tertiaryScale
							ctrl.node.sy >> pocn["node"].node.customPosition[b].scaleAim
							ctrl.node.sz >> pocn["node"].node.customPosition[b].scaleUp
						else:
							mnsNodes.mdlNode(ctrl.node.rx, -1, pocn["node"].node.customPosition[b].aimRotation)
							mnsNodes.mdlNode(ctrl.node.ry, -1, pocn["node"].node.customPosition[b].twist)
							ctrl.node.rz >> pocn["node"].node.customPosition[b].tertiaryRotation
							ctrl.node.sx >> pocn["node"].node.customPosition[b].tertiaryScale
							ctrl.node.sy >> pocn["node"].node.customPosition[b].scaleAim
							ctrl.node.sz >> pocn["node"].node.customPosition[b].scaleUp
							
			else:
				for b, ctrlIndex in enumerate([5,6,7]):
					ctrl = mnsUtils.validateNameStd(reorderedPositions[ctrlIndex]["ctrl"])
					if ctrlIndex == 6: 
						ctrl = loweMidIsolated

					if ctrl:
						mnsUtils.addAttrToObj([ctrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)

						positionAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = 1 - ((1.0 / float(4)) * (b + 1)), name = "position", replace = True, min = 0.0, max = 1.0)[0]
						falloffAttr = mnsUtils.addAttrToObj([ctrl.node], type = "float", value = 0.5, name = "falloff", replace = True, min = 0.01)[0]
						
						positionAttr >> pocn["node"].node.customPosition[b].uPosition
						falloffAttr >> pocn["node"].node.customPosition[b].falloff

						if ctrlIndex == 5:
							ctrl.node.rx >> pocn["node"].node.customPosition[b].aimRotation
							mnsNodes.mdlNode(ctrl.node.ry, -1, pocn["node"].node.customPosition[b].twist)
							mnsNodes.mdlNode(ctrl.node.rz, -1, pocn["node"].node.customPosition[b].tertiaryRotation)
							ctrl.node.sx >> pocn["node"].node.customPosition[b].tertiaryScale
							ctrl.node.sy >> pocn["node"].node.customPosition[b].scaleAim
							ctrl.node.sz >> pocn["node"].node.customPosition[b].scaleUp
						elif ctrlIndex == 6:
							mnsNodes.mdlNode(ctrl.node.rx, -1, pocn["node"].node.customPosition[b].aimRotation)
							ctrl.node.ry >> pocn["node"].node.customPosition[b].twist
							mnsNodes.mdlNode(ctrl.node.rz, -1, pocn["node"].node.customPosition[b].tertiaryRotation)
							ctrl.node.sx >> pocn["node"].node.customPosition[b].tertiaryScale
							ctrl.node.sy >> pocn["node"].node.customPosition[b].scaleAim
							ctrl.node.sz >> pocn["node"].node.customPosition[b].scaleUp
						else:
							ctrl.node.rx >> pocn["node"].node.customPosition[b].aimRotation
							ctrl.node.ry >> pocn["node"].node.customPosition[b].twist
							ctrl.node.rz >> pocn["node"].node.customPosition[b].tertiaryRotation
							ctrl.node.sx >> pocn["node"].node.customPosition[b].tertiaryScale
							ctrl.node.sy >> pocn["node"].node.customPosition[b].scaleAim
							ctrl.node.sz >> pocn["node"].node.customPosition[b].scaleUp
							
			# connect layer B ctrls as tweakers
			if doLayerBCtrls:
				for b, layerBCtrl in enumerate(layerBCtrls):
					tweakerIndexA = b + 3
					mnsUtils.addAttrToObj([layerBCtrl.node], type = "enum", value = ["______"], name = "pocTweaker", replace = True)
					positionAttr = mnsUtils.addAttrToObj([layerBCtrl.node], type = "float", value = (1.0 / float(numLayerBCtrlsPerSection - 1)) * b, name = "position", replace = True, min = 0.0, max = 1.0)[0]
					falloffAttr = mnsUtils.addAttrToObj([layerBCtrl.node], type = "float", value = 0.5, name = "falloff", replace = True, min = 0.01)[0]
					
					positionAttr >> pocn["node"].node.customPosition[tweakerIndexA].uPosition
					falloffAttr >> pocn["node"].node.customPosition[tweakerIndexA].falloff
					
					if k == 0:
						if not layerBCtrl.side == "r":
							layerBCtrl.node.rx >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryRotation
							mnsNodes.mdlNode(layerBCtrl.node.ry, -1, pocn["node"].node.customPosition[tweakerIndexA].aimRotation)
							mnsNodes.mdlNode(layerBCtrl.node.rz, -1, pocn["node"].node.customPosition[tweakerIndexA].twist)
							layerBCtrl.node.sy >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryScale
							layerBCtrl.node.sz >> pocn["node"].node.customPosition[tweakerIndexA].scaleAim
							layerBCtrl.node.sx >> pocn["node"].node.customPosition[tweakerIndexA].scaleUp
						else:
							mnsNodes.mdlNode(layerBCtrl.node.rx, -1, pocn["node"].node.customPosition[tweakerIndexA].tertiaryRotation)
							mnsNodes.mdlNode(layerBCtrl.node.ry, -1, pocn["node"].node.customPosition[tweakerIndexA].aimRotation)
							layerBCtrl.node.rz >> pocn["node"].node.customPosition[tweakerIndexA].twist
							layerBCtrl.node.sy >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryScale
							layerBCtrl.node.sz >> pocn["node"].node.customPosition[tweakerIndexA].scaleAim
							layerBCtrl.node.sx >> pocn["node"].node.customPosition[tweakerIndexA].scaleUp
					else:
						if not layerBCtrl.side == "r":
							mnsNodes.mdlNode(layerBCtrl.node.rx, -1, pocn["node"].node.customPosition[tweakerIndexA].tertiaryRotation)
							layerBCtrl.node.ry >> pocn["node"].node.customPosition[tweakerIndexA].aimRotation
							mnsNodes.mdlNode(layerBCtrl.node.rz, -1, pocn["node"].node.customPosition[tweakerIndexA].twist)
							layerBCtrl.node.sy >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryScale
							layerBCtrl.node.sz >> pocn["node"].node.customPosition[tweakerIndexA].scaleAim
							layerBCtrl.node.sx >> pocn["node"].node.customPosition[tweakerIndexA].scaleUp
						
						else:
							layerBCtrl.node.rx >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryRotation
							layerBCtrl.node.ry >> pocn["node"].node.customPosition[tweakerIndexA].aimRotation
							layerBCtrl.node.rz >> pocn["node"].node.customPosition[tweakerIndexA].twist
							layerBCtrl.node.sy >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryScale
							layerBCtrl.node.sz >> pocn["node"].node.customPosition[tweakerIndexA].scaleAim
							layerBCtrl.node.sx >> pocn["node"].node.customPosition[tweakerIndexA].scaleUp

						if b == 0: 
							layBCornA.node.position >> pocn["node"].node.customPosition[tweakerIndexA].uPosition
							layBCornA.node.falloff >> pocn["node"].node.customPosition[tweakerIndexA].falloff
					
							layBCornA.node.rx >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryRotation
							mnsNodes.mdlNode(layBCornA.node.ry, -1, pocn["node"].node.customPosition[tweakerIndexA].aimRotation)
							mnsNodes.mdlNode(layBCornA.node.rz, -1, pocn["node"].node.customPosition[tweakerIndexA].twist)
							layBCornA.node.sy >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryScale
							layBCornA.node.sz >> pocn["node"].node.customPosition[tweakerIndexA].scaleAim
							layBCornA.node.sx >> pocn["node"].node.customPosition[tweakerIndexA].scaleUp
						elif b == (numLayerBCtrlsPerSection - 1):
							layBCornB.node.position >> pocn["node"].node.customPosition[tweakerIndexA].uPosition
							layBCornB.node.falloff >> pocn["node"].node.customPosition[tweakerIndexA].falloff
					
							mnsNodes.mdlNode(layBCornB.node.rx, -1, pocn["node"].node.customPosition[tweakerIndexA].tertiaryRotation)
							mnsNodes.mdlNode(layBCornB.node.ry, -1, pocn["node"].node.customPosition[tweakerIndexA].aimRotation)
							layBCornB.node.rz >> pocn["node"].node.customPosition[tweakerIndexA].twist
							layBCornB.node.sy >> pocn["node"].node.customPosition[tweakerIndexA].tertiaryScale
							layBCornB.node.sz >> pocn["node"].node.customPosition[tweakerIndexA].scaleAim
							layBCornB.node.sx >> pocn["node"].node.customPosition[tweakerIndexA].scaleUp
							
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
		upperPivotPos.node.ty.set(3)
		pm.parent(upperPivotPos.node, w = True)
		custGuides.append(upperPivotPos)
		parentDict.update({upperPivotPos: builtGuides[0]})

		lowerPivotPos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + "LowerCurlPivot", alpha = builtGuides[0].alpha, id = builtGuides[0].id, buildType = "locator", incrementAlpha = False)
		pm.delete(pm.parentConstraint(builtGuides[0].node, lowerPivotPos.node))
		pm.parent(lowerPivotPos.node, builtGuides[0].node)
		pm.makeIdentity(lowerPivotPos.node)
		lowerPivotPos.node.ty.set(-3)
		pm.parent(lowerPivotPos.node, w = True)
		custGuides.append(lowerPivotPos)
		parentDict.update({lowerPivotPos: builtGuides[0]})

		status, midsPosition = mnsUtils.validateAttrAndGet(builtGuides[0], "midsPosition", 0)

		for side in ["left", "right"]:
			for section in ["upper", "lower"]:
				custGuide = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + section.capitalize() + side.capitalize() + "Mid", alpha = builtGuides[0].alpha, id = builtGuides[0].id, buildType = "locator", incrementAlpha = False)
				pm.delete(pm.parentConstraint(builtGuides[0].node, custGuide.node))
				pm.parent(custGuide.node, builtGuides[0].node)
				pm.makeIdentity(custGuide.node)

				additionalTx = 3.0
				additionalTy = 3.0
				if section == "lower": additionalTy *= -1 
				if side == "right": additionalTx *= -1
				
				custGuide.node.tx.set(additionalTx)
				custGuide.node.ty.set(additionalTy)

				pm.parent(custGuide.node, w = True)
				custGuides.append(custGuide)
				parentDict.update({custGuide: builtGuides[0]})
				if midsPosition == 0: custGuide.node.v.set(False)

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

	status, midsPosition = mnsUtils.validateAttrAndGet(rootGuide, "midsPosition", 0)
	for cg in customGuides:
		if "Midv" in cg.name.lower():
			if midsPosition == 1: cg.node.v.set(True)
			else: cg.node.v.set(False)

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
								conformToMeetPoint = False,
								buildMode = 0
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
											doScale = True,
											doRotate = True,
											rotateMode = 4,
											connectRotate = True,
											connectChildrenRotate = True,
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

def jointStructureSoftMod(mansur, guides, mnsBuildModule = None, **kwargs):
	#internal Imports
	from mansur.core import utility as mnsUtils
	from mansur.block.core import blockUtility as blkUtils

	rootGuide = guides[0]
	customGuides = blkUtils.getModuleDecendentsWildcard(guides[0], customGuidesOnly = True)

	status, midsPosition = mnsUtils.validateAttrAndGet(rootGuide, "midsPosition", 0)
	for cg in customGuides:
		if "Mid" in cg.name:
			if midsPosition == 1: cg.node.v.set(True)
			else: cg.node.v.set(False)

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
					pocns[k].rotateMode.set(5)

			if pocns[0] and pocns[1]:
				iLocs = blkUtils.getModuleInterpJoints(rootGuide)
				if iLocs:
					iLocs = mnsUtils.sortNameStdArrayByID(iLocs)
				
					for k, iLoc in enumerate(iLocs):
						if  k < len(upperEdge):
							enumToConnect = k
							pocnToConnect = pocns[0]
						else:
							enumToConnect = k - len(upperEdge)
							pocnToConnect = pocns[1]

						for axisName in "xyz":
							inputAdlCons = iLoc.node.attr("r" + axisName).listConnections(s = True, d = False)
							if inputAdlCons:
								if type(inputAdlCons[0]) == pm.nodetypes.UnitConversion:
									inputAdlCons = inputAdlCons[0].input.listConnections(s = True, d = False)
									if inputAdlCons:
										if type(inputAdlCons[0]) == pm.nodetypes.AddDoubleLinear:
											pm.delete(inputAdlCons[0])
											iLoc.node.attr("r" + axisName).set(0)

						pocnToConnect.transforms[enumToConnect].translate >> iLoc.node.t
						#pocnToConnect.transforms[enumToConnect].rotate >> iLoc.node.r
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

	if selfMainCtrl:
		status, jawConnectData = mnsUtils.validateAttrAndGet(selfMainCtrl, "jawConnect_data", None)
		if jawConnectData:
			jawConnectData = json.loads(jawConnectData)
			cornerA = mnsUtils.checkIfObjExistsAndSet(jawConnectData["0"]["ctrl"])
			upperLeftMid = mnsUtils.checkIfObjExistsAndSet(jawConnectData["1"]["ctrl"])
			upperMid = mnsUtils.checkIfObjExistsAndSet(jawConnectData["2"]["ctrl"])
			upperRightMid = mnsUtils.checkIfObjExistsAndSet(jawConnectData["3"]["ctrl"])
			cornerB = mnsUtils.checkIfObjExistsAndSet(jawConnectData["4"]["ctrl"])
			lowerRightMid = mnsUtils.checkIfObjExistsAndSet(jawConnectData["5"]["ctrl"])
			lowerMid = mnsUtils.checkIfObjExistsAndSet(jawConnectData["6"]["ctrl"])
			lowerLeftMid = mnsUtils.checkIfObjExistsAndSet(jawConnectData["7"]["ctrl"])

		status, connectJaw = mnsUtils.validateAttrAndGet(rootGuide, "connectJaw", False)
		if jawRootGuide and jawConnectData and connectJaw:
			jawCtrl = blkUtils.getCtrlAuthFromRootGuide(jawRootGuide)
			if jawCtrl:
				mnsUtils.addAttrToObj([selfMainCtrl.node], type = "enum", value = ["______"], name = "JawConnect", replace = True, locked = True)

				cornersFollowAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", min = 0.0, max = 1.0, value = 0.5, name = "cornersFollowJaw", replace = True)[0]
				for ctrl in [lowerMid, upperMid, cornerA, cornerB]:
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

						if ctrl.node == upperMid:
							status, connectUpMotionRot = mnsUtils.validateAttrAndGet(rootGuide, "connectUpMotionRot", True)
							if connectUpMotionRot:
								status, upMotionRotAxis = mnsUtils.validateAttrAndGet(rootGuide, "upMotionRotAxis", "-x")
								upRotationWeightAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", value = 1.0, name = "upRotationWeight", min = 0.0, max = 1.0, replace = True)[0]	
								weightMdlNode = mnsNodes.mdlNode(None, upRotationWeightAttr, None)

								if upMotionRotAxis == "x":
									clampNode = mnsNodes.clampNode([jawCtrl.node.rx, 0, 0], 
																	[180.0, 0.0, 0.0],
																	[0.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.rx
								elif upMotionRotAxis == "y":
									clampNode = mnsNodes.clampNode([jawCtrl.node.ry, 0, 0], 
																	[180.0, 0.0, 0.0],
																	[0.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.ry
								elif upMotionRotAxis == "z":
									clampNode = mnsNodes.clampNode([jawCtrl.node.rz, 0, 0], 
																	[180.0, 0.0, 0.0],
																	[0.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.rz
								elif upMotionRotAxis == "-x":
									clampNode = mnsNodes.clampNode([jawCtrl.node.rx, 0, 0], 
																	[0.0, 0.0, 0.0],
																	[-180.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.rx
								elif upMotionRotAxis == "-y":
									clampNode = mnsNodes.clampNode([jawCtrl.node.ry, 0, 0], 
																	[0.0, 0.0, 0.0],
																	[-180.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.ry
								elif upMotionRotAxis == "-z":
									clampNode = mnsNodes.clampNode([jawCtrl.node.rz, 0, 0], 
																	[0.0, 0.0, 0.0],
																	[-180.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.rz

							status, connectUpMotionTran = mnsUtils.validateAttrAndGet(rootGuide, "connectUpMotionTran", True)
							if connectUpMotionTran:
								status, upMotionTranAxis = mnsUtils.validateAttrAndGet(rootGuide, "upMotionTranAxis", "y")
								upTranlationWeightAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", value = 1.0, name = "upTranslationWeight", min = 0.0, max = 1.0, replace = True)[0]	
								weightMdlNode = mnsNodes.mdlNode(None, upTranlationWeightAttr, None)

								if upMotionTranAxis == "x":
									clampNode = mnsNodes.clampNode([jawCtrl.node.tx, 0, 0], 
																	[180.0, 0.0, 0.0],
																	[0.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.tx
								elif upMotionTranAxis == "y":
									clampNode = mnsNodes.clampNode([jawCtrl.node.ty, 0, 0], 
																	[180.0, 0.0, 0.0],
																	[0.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.ty
								elif upMotionTranAxis == "z":
									clampNode = mnsNodes.clampNode([jawCtrl.node.tz, 0, 0], 
																	[180.0, 0.0, 0.0],
																	[0.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.tz
								elif upMotionTranAxis == "-x":
									clampNode = mnsNodes.clampNode([jawCtrl.node.tx, 0, 0], 
																	[0.0, 0.0, 0.0],
																	[-180.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.tx
								elif upMotionTranAxis == "-y":
									clampNode = mnsNodes.clampNode([jawCtrl.node.ty, 0, 0], 
																	[0.0, 0.0, 0.0],
																	[-180.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.ty
								elif upMotionTranAxis == "-z":
									clampNode = mnsNodes.clampNode([jawCtrl.node.tz, 0, 0], 
																	[0.0, 0.0, 0.0],
																	[-180.0, 0.0, 0.0])
									mnsNodes.dlNodesConnect(clampNode.node.outputR, weightMdlNode.node, "input1")
									weightMdlNode.node.output >> offsetA.node.tz

							
						elif ctrl.node == lowerMid:
							mnsNodes.mdNode(jawCtrl.node.t, 
											[1.0, 1.0, -1.0],
											offsetA.node.t)			
							mnsNodes.mdNode(jawCtrl.node.r, 
											[-1.0, -1.0, 1.0],
											offsetA.node.r)		
							jawCtrl.node.s >> offsetA.node.s
						else:
							mnsNodes.mdNode(jawCtrl.node.t, 
											[cornersFollowAttr, cornersFollowAttr, cornersFollowAttr],
											offsetA.node.t)			
							mnsNodes.mdNode(jawCtrl.node.r, 
											[cornersFollowAttr, cornersFollowAttr, cornersFollowAttr],
											offsetA.node.r)		
							jawCtrl.node.s >> offsetA.node.s

				lipsPullAttr = mnsUtils.addAttrToObj([selfMainCtrl.node], type = "float", value = 0.6, name = "cornerPullAmount", replace = True)[0]	
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

		if cornerA and upperLeftMid and upperMid and upperRightMid and cornerB and lowerRightMid and lowerMid and lowerLeftMid:
			#temporarily parent slave controls under world, to avoid using maintain offset in the partial parent contraint
			#for ctrlIdx in ["1","3","5","7"]: pm.parent(jawConnectData[ctrlIdx]["ctrl"], w = True)
			parCns = mnsNodes.mayaConstraint([jawConnectData["0"]["ctrl"], jawConnectData["2"]["ctrl"]], jawConnectData["1"]["offsetGrp"], type = "parent", maintainOffset = True, skip = ["rx", "ry", "rz"])
			parCns.node.interpType.set(0)
			mnsUtils.addAttrToObj([jawConnectData["1"]["ctrl"]], type = "enum", value = ["______"], name = "corner", replace = True, locked = True)
			weightAttr = mnsUtils.addAttrToObj([jawConnectData["1"]["ctrl"]], type = "float", value = 0.5, min = 0.0, max = 1.0, name = "cornerWeight", replace = True)[0]	
			revWeightRev = mnsNodes.reverseNode([weightAttr, 1.0,1.0])
			weightAttr >> parCns.node.attr(jawConnectData["0"]["ctrl"] + "W0")
			revWeightRev.node.outputX >> parCns.node.attr(jawConnectData["2"]["ctrl"] + "W1")

			parCns = mnsNodes.mayaConstraint([jawConnectData["4"]["ctrl"], jawConnectData["2"]["ctrl"]], jawConnectData["3"]["offsetGrp"], type = "parent", maintainOffset = True, skip = ["rx", "ry", "rz"])
			parCns.node.interpType.set(0)
			mnsUtils.addAttrToObj([jawConnectData["3"]["ctrl"]], type = "enum", value = ["______"], name = "corner", replace = True, locked = True)
			weightAttr = mnsUtils.addAttrToObj([jawConnectData["3"]["ctrl"]], type = "float", value = 0.5, min = 0.0, max = 1.0, name = "cornerWeight", replace = True)[0]	
			revWeightRev = mnsNodes.reverseNode([weightAttr, 1.0,1.0])
			weightAttr >> parCns.node.attr(jawConnectData["4"]["ctrl"] + "W0")
			revWeightRev.node.outputX >> parCns.node.attr(jawConnectData["2"]["ctrl"] + "W1")

			parCns = mnsNodes.mayaConstraint([jawConnectData["4"]["ctrl"], jawConnectData["6"]["ctrl"]], jawConnectData["5"]["offsetGrp"], type = "parent", maintainOffset = True, skip = ["rx", "ry", "rz"])
			parCns.node.interpType.set(0)
			mnsUtils.addAttrToObj([jawConnectData["5"]["ctrl"]], type = "enum", value = ["______"], name = "corner", replace = True, locked = True)
			weightAttr = mnsUtils.addAttrToObj([jawConnectData["5"]["ctrl"]], type = "float", value = 0.5, min = 0.0, max = 1.0, name = "cornerWeight", replace = True)[0]	
			revWeightRev = mnsNodes.reverseNode([weightAttr, 1.0,1.0])
			weightAttr >> parCns.node.attr(jawConnectData["4"]["ctrl"] + "W0")
			revWeightRev.node.outputX >> parCns.node.attr(jawConnectData["6"]["ctrl"] + "W1")

			parCns = mnsNodes.mayaConstraint([jawConnectData["0"]["ctrl"], jawConnectData["6"]["ctrl"]], jawConnectData["7"]["offsetGrp"], type = "parent", maintainOffset = True, skip = ["rx", "ry", "rz"])
			parCns.node.interpType.set(0)
			mnsUtils.addAttrToObj([jawConnectData["7"]["ctrl"]], type = "enum", value = ["______"], name = "corner", replace = True, locked = True)
			weightAttr = mnsUtils.addAttrToObj([jawConnectData["7"]["ctrl"]], type = "float", value = 0.5, min = 0.0, max = 1.0, name = "cornerWeight", replace = True)[0]	
			revWeightRev = mnsNodes.reverseNode([weightAttr, 1.0,1.0])
			weightAttr >> parCns.node.attr(jawConnectData["0"]["ctrl"] + "W0")
			revWeightRev.node.outputX >> parCns.node.attr(jawConnectData["6"]["ctrl"] + "W1")

			#now reparent the controls back under their newly positioned offset groups
			#for ctrlIdx in ["1","3","5","7"]: 
			#	pm.parent(jawConnectData[ctrlIdx]["ctrl"], jawConnectData[ctrlIdx]["offsetGrp"])
			#	mnsUtils.createOffsetGroup(jawConnectData[ctrlIdx]["ctrl"])