"""Author: Asaf Ben-Zur
Best used for: chassis
This module will yield four corner controls, which will be avaraged determine the main control's translation and orientation. 
The aim of this module is creating an easy to use control for a chassis orientation on a vehicle.
Using the four corner controls, the main joint will be avaraged to detrmine the best orientation and translation for the module.
Best used alongside geometry constraints to follow a ground mesh for automatic orientation and translation of vehicles.  
"""



from maya import cmds
import pymel.core as pm

import math
import maya.OpenMaya as OpenMaya

def construct(mansur, MnsBuildModule, **kwargs):
	########### local library imports ###########
	from mansur.block.core import blockUtility as blkUtils
	from mansur.block.core import controlShapes as blkCtrlShps
	from mansur.core import utility as mnsUtils
	from mansur.core import nodes as mnsNodes
	from mansur.core import prefixSuffix

	########### global module objects collect ###########
	relatedJnt = mnsUtils.validateNameStd(blkUtils.getRelatedNodeFromObject(MnsBuildModule.rootGuide))
	rootGuide = MnsBuildModule.rootGuide
	allGuides = [MnsBuildModule.rootGuide] + MnsBuildModule.guideControls
	moduleTopGrp = MnsBuildModule.moduleTop
	animGrp = MnsBuildModule.animGrp
	animStaticGrp = MnsBuildModule.animStaticGrp
	animStaticGrp.node.v.set(False)
	rigComponentsGrp = MnsBuildModule.rigComponentsGrp
	attrHost = MnsBuildModule.attrHostCtrl or animGrp
	customGuides = MnsBuildModule.cGuideControls

	########### local root variables collect ###########
	status, symmetryType = mnsUtils.validateAttrAndGet(rootGuide, "symmetryType", 0)
	modScale = blkUtils.getModuleScale(MnsBuildModule)

	########### returns collect declare ###########
	ctrlsCollect = []
	internalSpacesDict = {}

	status, controlShape = mnsUtils.validateAttrAndGet(rootGuide, "slaveControlShape", "cube")
	ctrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = MnsBuildModule.rootGuide.node,
								controlShape = controlShape,
								scale = modScale, 
								parentNode = animGrp,
								symmetryType = symmetryType,
								doMirror = True,
								createSpaceSwitchGroup = True,
								createOffsetGrp = True,
								isFacial = MnsBuildModule.isFacial,
								alongAxis = 0)
	ctrlsCollect.append(ctrl)
	host = MnsBuildModule.attrHostCtrl or ctrl
	ctrlOffsetGrp = blkUtils.getOffsetGrpForCtrl(ctrl)

	if customGuides:
		status, groundControlShape = mnsUtils.validateAttrAndGet(rootGuide, "groundControlShape", "arrow")
		status, doGroundCtrls = mnsUtils.validateAttrAndGet(rootGuide, "doGroundCtrls", "False")
		
		#create plane
		planeNameStd = prefixSuffix.MnsNameStd(side = rootGuide.side, body = rootGuide.body + "ControlPlane", alpha = rootGuide.alpha, id = rootGuide.id, type = prefixSuffix.mnsTypeDict["geometry"])
		planeMaster = pm.polyPlane(sx = 1, sy = 1, ch = False, n = planeNameStd.name)[0]
		planeNameStd.node = planeMaster
		pm.parent(planeNameStd.node, rigComponentsGrp.node)
		status, pivotsControlShape = mnsUtils.validateAttrAndGet(rootGuide, "pivotsControlShape", "diamond")
		
		planeSkinningJoints = []
		for guide in customGuides: 
			if not "AttrHost" in guide.node.nodeName():
				
				vertexMatchIndex = 0
				if "FrontLeft" in guide.node.nodeName():
					vertexMatchIndex = 1
				elif "BackRight" in guide.node.nodeName():
					vertexMatchIndex = 2
				elif "BackLeft" in guide.node.nodeName():
					vertexMatchIndex = 3

				wsVertPos = pm.xform(guide.node, ws = True, q = True, t = True)
				pm.move(planeNameStd.node.vtx[vertexMatchIndex], wsVertPos, a = True)

				parentNode = animGrp
				createSpaceSwitchGroup = True
				if doGroundCtrls:
					matchLoc = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "MasterPos", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
					pm.matchTransform(matchLoc.node, guide.node)
					matchLoc.node.r.set((0,0,0))
					matchLoc.node.s.set((1,1,1))
					matchLoc.node.ty.set(0)

					groundCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
														color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
														matchTransform = matchLoc.node,
														controlShape = groundControlShape,
														scale = modScale * 0.5, 
														bodySuffix = "CornerPosition",
														parentNode = animGrp,
														symmetryType = 0,
														doMirror = False,
														createSpaceSwitchGroup = True,
														createOffsetGrp = True,
														isFacial = MnsBuildModule.isFacial,
														alongAxis = 4)
					pm.delete(matchLoc.node)
					ctrlsCollect.append(groundCtrl)
					parentNode = groundCtrl
					createSpaceSwitchGroup = False

				#create ctrl
				cornerCtrl = blkCtrlShps.ctrlCreate(nameReference = MnsBuildModule.rootGuide,
								color = blkUtils.getCtrlCol(MnsBuildModule.rootGuide, MnsBuildModule.rigTop),
								matchTransform = guide.node,
								controlShape = pivotsControlShape,
								scale = modScale * 0.5, 
								bodySuffix = "CornerPosition",
								parentNode = parentNode,
								symmetryType = 0,
								doMirror = False,
								createSpaceSwitchGroup = createSpaceSwitchGroup,
								createOffsetGrp = True,
								isFacial = MnsBuildModule.isFacial
								)
				ctrlsCollect.append(cornerCtrl)

				#create joint
				cornerJnt = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "Corner", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "helperJoint", createBlkClassID = False, incrementAlpha = False)
				pm.parent(cornerJnt.node, rigComponentsGrp.node)
				mnsNodes.mnsMatrixConstraintNode(side = rootGuide.side, id = rootGuide.id, body = rootGuide.body, alpha = rootGuide.alpha, targets = [cornerJnt.node], sources = [cornerCtrl.node])
				planeSkinningJoints.append(cornerJnt)

		#skin the plane
		pm.skinCluster(planeNameStd.node, [j.node for j in planeSkinningJoints], tsb = True)	
		#create a rivet at plane center
		simpleRivetNode = mnsNodes.mnsSimpleRivetsNode(side = rootGuide.side, 
									id = rootGuide.id, 
									body = rootGuide.body, 
									alpha = rootGuide.alpha,
									inputMesh = planeNameStd.node,
									mo = False)
		simpleRivetNode.node.targetWorldMatrix.disconnect()
		#find face center pos
		face = pm.MeshFace(planeNameStd.node.f[0])
		pt = face.__apimfn__().center(OpenMaya.MSpace.kWorld)
		centerPoint = pm.datatypes.Point(pt)
		transformMasterLoc = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "MasterPos", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.parent(transformMasterLoc.node, rigComponentsGrp.node)
		rivetInputLoc = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "RivetInput", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
		rivetInputLoc.node.v.set(False)
		pm.parent(rivetInputLoc.node, animGrp.node)
		pm.xform(transformMasterLoc.node, ws = True, t = centerPoint)
		rivetInputLoc.node.worldMatrix[0] >> simpleRivetNode.node.rivet[0].rivetStartPosition
		simpleRivetNode.node.transform[0].r >> transformMasterLoc.node.r
		simpleRivetNode.node.transform[0].t >> transformMasterLoc.node.t
		
		#create a normalized up vector to kill twists
		simpleRivetNodeUp = mnsNodes.mnsSimpleRivetsNode(side = rootGuide.side, 
									id = rootGuide.id, 
									body = rootGuide.body, 
									alpha = rootGuide.alpha,
									inputMesh = planeNameStd.node,
									mo = False)
		simpleRivetNodeUp.node.targetWorldMatrix.disconnect()
		rivetInputLoc.node.worldMatrix[0] >> simpleRivetNodeUp.node.rivet[0].rivetStartPosition

		status, forwardAxis = mnsUtils.validateAttrAndGet(rootGuide, "forwardAxis", 2)
		upLoc = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "UpLoc", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.parent(upLoc.node, animGrp.node)
		pm.makeIdentity(upLoc.node)
		upLoc.node.v.set(False)

		setValue = 10;
		attrToCon = upLoc.node.tx
		if forwardAxis == 1 or forwardAxis == 4: attrToCon = upLoc.node.ty
		elif forwardAxis == 2 or forwardAxis == 5: attrToCon = upLoc.node.tz
		if forwardAxis > 2: setValue *= -1
		attrToCon.set(setValue)
		upLoc.node.worldMatrix[0] >> simpleRivetNode.node.rivet[0].upMatrix
		simpleRivetNode.node.rivet[0].upMode.set(1)

		upDummy = mnsUtils.createNodeReturnNameStd(side = rootGuide.side, body = rootGuide.body + "UpDummy", alpha = rootGuide.alpha, id = rootGuide.id, buildType = "locator", incrementAlpha = False)
		pm.parent(upDummy.node, rigComponentsGrp.node)
		pm.delete(pm.pointConstraint(upLoc.node, upDummy.node))
		upDummy.node.v.set(False)
		simpleRivetNodeUp.node.transform[0].t >> upDummy.node.t
		
		mnsNodes.mayaConstraint([upDummy.node], upLoc.node, type = "point", maintainOffset = True)

		mnsNodes.mnsMatrixConstraintNode(side = rootGuide.side, id = rootGuide.id, body = rootGuide.body, alpha = rootGuide.alpha, targets = [ctrlOffsetGrp.node], sources = [transformMasterLoc.node], maintainOffset = True, connectScale = False)
		
	#tranfer auth
	blkUtils.transferAuthorityToCtrl(relatedJnt, ctrl)

	#return; list (controls), dict (internalSpaces)
	return ctrlsCollect, internalSpacesDict, host, host

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

		positionArray = [(3,0,3), (3,0,-3), (-3,0,-3), (-3,0,3)]
		nameArray = ["FrontLeft", "BackLeft", "BackRight", "FrontRight"]
		for index in range(4):
			pivotPos = mnsUtils.createNodeReturnNameStd(side = builtGuides[0].side, body = builtGuides[0].body + nameArray[index], alpha = builtGuides[0].alpha, id = 1, buildType = "locator", incrementAlpha = False)
			pm.parent(pivotPos.node, builtGuides[0].node)
			pm.makeIdentity(pivotPos.node)
			

			pivotPos.node.t.set(positionArray[index])
			pm.parent(pivotPos.node, w = True)

			parentDict.update({pivotPos: builtGuides[0]})
			custGuides.append(pivotPos)

	return custGuides, parentDict
