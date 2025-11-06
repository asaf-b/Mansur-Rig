"""=== Author: Assaf Ben Zur ===
All global prefix and suffix declerations.
All global Mns pre-defined dictionaries creation (i.e.  mnsTypeDict/mnsSidesDict/mnsBuildObjectTypes)

This module also holds the MnsTypeStd class and the MnsNameStd class.
This module holds any global dict creation defenitions used in MNS."""

#global dependencies


from maya import cmds
import pymel.core as pm


#mns dependencies
from .globals import *

class MnsTypeStd(object):
	"""This class holds simple attributes to extend pythos's 'type' object in order to preserve additional information regarding a node's type.
	"""

	def __init__(self,**kwargs):
		self.name = kwargs.get("name",None)  #arg; 
		self.suffix = kwargs.get("suffix","")  #arg; 
		self.createName = kwargs.get("createName", self.name) #arg; 
		self.comment = kwargs.get("comment","Comment wasn't inserted") #arg; 

class MnsNameStd(object):
	"""This class holds simple attributes to extend pythos's 'node' object in order to preserve additional information regarding a node.
	Any name related methods are held by this class.
	"""

	def __init__(self,**kwargs):
		self.node = kwargs.get("node",None)  #arg; 
		self.side = kwargs.get("side","c")  #arg; 
		self.body = kwargs.get("body","")  #arg; 
		self.type = kwargs.get("type", MnsTypeStd())  #arg; 
		self.id = kwargs.get("id", 1)  #arg; 
		try:
			self.id = int(self.id)
		except:
			pass
		self.alpha = kwargs.get("alpha", "A")  #arg; 
		self.suffix = kwargs.get("suffix", self.type.suffix)  #arg; 
		self.name = None 
		self.namespace = ""
		self.comment = kwargs.get("comment","Comment wasn't inserted") #arg; 
		self.buildName()

	def findNextIncrement(self):
		"""Recursive.
		Find next available id increment"""

		if self.id > 700:
			userMsg = '==' + "Mansur" + '==  [warning] Mansur node index passed 900. That indicates node accumulation. Please report to us as soon as you can via Email to support@mansur-rig.com or via our Discord community.'
			
		if pm.objExists(self.name):
			if self.id > 999:
				self.findNextAlphaIncrement()
				self.id = 1
				self.buildName()
				self.findNextIncrement()
			else:
				self.id += 1
				self.buildName()
				self.findNextIncrement()

	def findNextAlphaIncrement(self):
		"""Recursive.
		Find next available Alpha id increment"""

		rigRootName = self.name.replace("_" + self.suffix, "_" + mnsPS_rigTop)
		if pm.objExists(self.name) or pm.objExists(rigRootName):
			newAlpha = ""
			icremented = False
			for c in self.alpha[::-1]:
				if not icremented: 
					charA = ord(c) - 65
					if charA < 25:
						charA += 1
						alphaInc = chr(charA + 65)
						newAlpha += alphaInc
						icremented = True
					else: newAlpha += "A"
				else:
					newAlpha += c
			newAlpha = newAlpha[::-1]
			if not icremented:
				newAlpha += "A" 
			self.alpha = newAlpha
			self.buildName()
			self.findNextAlphaIncrement()
	
	def buildName(self):
		"""Build the instance's name based on the current class members defenitions.
		"""

		from . import utility as mnsUtils
		numSuffixPadding = mnsUtils.getMansurPrefs()["Global"]["numberSuffixPadding"]

		padding = ""
		idLen = len(str(self.id))
		for k in range (0, numSuffixPadding - idLen + 1): padding += "0"
		self.name = self.side + "_" + self.body + "_" + self.alpha + padding + str(self.id) + "_" + self.suffix

	def splitName(self):
		"""This function splits a given node name as string into an MnsNameStd object
		"""

		if self.node:
			nameString =  self.node.nodeName()
			if ":" in nameString:
				nameString = nameString.split(":")[-1]
				self.namespace = self.node.name().replace(":" + nameString.split(":")[-1], "")
				
			if "_" in nameString and len(nameString.split("_")) == 4:
				side, body, alphaID, suffix = nameString.split("_")
				alpha = ""
				id = ""
				for char in alphaID:
					if char.isdigit():
						id += char
					else: alpha += char
				id = int(id) 
				typeStd = MnsTypeStd(name = self.node.type(), suffix = suffix)

				self.side = side
				self.body = body
				self.type = typeStd 
				self.id = id
				self.alpha = alpha
				self.suffix = suffix
				self.buildName()

	def splitDefinedName(self):
		"""This function splits a given object name as string into an MnsNameStd object
		"""

		if self.name:
			nameString =  self.name
			if ":" in nameString:
				nameString = nameString.split(":")[-1]
				self.namespace = nameString.split(":")[0]
				
			if "_" in nameString and len(nameString.split("_")) == 4:
				side, body, alphaID, suffix = nameString.split("_")
				alpha = ""
				id = ""
				for char in alphaID:
					if char.isdigit():
						id += char
					else: alpha += char
				id = int(id) 
				
				self.side = side
				self.body = body
				self.id = id
				self.alpha = alpha
				self.suffix = suffix

	def setNodeName(self):
		if self.node:
			pm.rename(self.node, self.name)

def buildTypeDict(namesArray = []):
	"""Build a dictionary for a given list, adding index (int) key and an index (string) key for each item
	"""

	dictRet = {}
	indexAdd = 0
	for k in namesArray:
		typeObj = MnsTypeStd(name = k[0], suffix = k[1])
		if len(k) > 2: typeObj.createName = k[2]
		dictRet.update({k[0]: typeObj})
		dictRet.update({indexAdd: typeObj})
		dictRet.update({str(indexAdd): typeObj})
		indexAdd += 1
	#return;dict
	return dictRet

def buildMultKeysDict(items = []):
	"""Build a multy key dict for the given item list
	"""

	dictRet = {}
	k = 0
	for item in items:
		keys = []
		if len(item[1]) > 0:
			keys = item[1]
		element = item[0]
		keys.append(element.lower())
		if element.upper() not in keys: keys.append(element.upper())
		if element.lower().title() not in keys: keys.append(element.lower().title())   
		if k not in keys: keys.append(k)
		if str(k) not in keys: keys.append(str(k))
		for key in keys: dictRet.update({key: element})
		k += 1

	#return;dict
	return dictRet

def buildOptionArrayFromDict(dict = {}, **kwargs):
	"""Construct an option list from the given dictionary
	"""

	returnArray = []
	tempArray = []
	index = 0
	uniqueCount = 0
	for v in dict.values():
		if v not in tempArray:
			tempArray.append(v)
			uniqueCount += 1
	for i in range (0, uniqueCount):
		returnArray.append(dict[i])

	#return; list
	return returnArray

######## globals ########
mnsPS_projectName = 'MANSUR'

######## sides ########
#left
mnsPS_left = 'l'

#right
mnsPS_right = 'r'

#center
mnsPS_cen = 'c'

######## types ########
#group
mnsPS_grp = 'grp'

mnsPS_rigTop = 'blkRig'

mnsPS_module = 'modu'

mnsPS_jntStruct = 'jntStrct'

mnsPS_guide = 'gud'

mnsPS_puppet = 'pup'

mnsPS_visHelpGrp = 'vHlp'

mnsPS_freeJntsGrp = "fjGrp"

mnsPS_pickerLayout = "ploGrp"

mnsPS_ctrlShpsGrp = "csGrp"

mnsPS_offsetSkelGrp = "oSkelGrp"

mnsPS_extraSetupGrp = "extSetupGrp"

mnsPS_modelGrp = "mdlGrp"

mnsPS_ctrlShape = "cs"

mnsPS_ctrlShapeExport = "cse"

#joint
mnsPS_jnt = 'jnt'

mnsPS_hJnt = 'jntH'

mnsPS_rJnt = "rootJnt"

mnsPS_rrJnt = "rigJnt"

mnsPS_iJnt = "interpJnt"

mnsPS_oJnt = "oJnt"

#locator
mnsPS_loc = 'loc'

#interpLoc
mnsPS_iLoc = 'interpLoc'

#curve
mnsPS_crv = 'crv'

#ctrl
mnsPS_ctrl = 'ctrl'

mnsPS_techCtrl = 'techCtl'

mnsPS_gCtrl = 'gCtrl'

mnsPS_cgCtrl = "cgCtrl"

mnsPS_plg = "plgCtrl"

mnsPS_gRootCtrl = 'rCtrl'

#pivot ctrl
mnsPS_pivCtrl = 'pivCtrl'

#gimbal ctrl
mnsPS_gimCtrl = 'gimbalCtrl'

#geometry
mnsPS_geo = 'geo'

#lambert
mnsPS_lambert = 'lam'

#constraint
mnsPS_const = 'cst'

#ik handle
mnsPS_ikHan = 'ikHan'

#cluster
mnsPS_clus = 'clus'

#camera
mnsPS_cam = 'cam'

#projCam
mnsPS_projCam = "prjCam"

#set
mnsPS_set = 'set'

#lattice
mnsPS_lat = 'ltc'

#connection group
mnsPS_conGrp = 'cnsGrp'

#offset group
mnsPS_offsetGrp = 'osGrp'

#spaceSwitch group
mnsPS_ssGrp = 'ssGrp'

#mirror sclae group
mnsPS_mirGrp = 'mirGrp'

#modify groupw
mnsPS_modGrp = 'modifyGrp'

#top group
mnsPS_topGrp = 'topGrp'

#offset constraint
mnsPS_osCns = "ocGrp"

#tmp obj
mnsPS_tmp = 'tmp'

#tmp obj
mnsPS_axisVis = "axv"

#deformer node
mnsPS_dfm = 'dfm'

#skin cluster node
mnsPS_skinCluster = 'sc'

#blendShape node
mnsPS_bsp = 'bsp'

#pointsOnCurvenode
mnsPS_psoc = 'psoc'

#resampleCurve
mnsPS_rsc = 'rsc'

#threePointArc
mnsPS_tpa = 'tpa'

#curveVariable
mnsPS_crvVar = "crvVar"

#cameraGateNode
mnsPS_cgr = 'cgr'

#ikSolver
mnsPS_ikSolver = "ikS"

#annotateNode
mnsPS_annotate = 'ann'

#buildTransformsCurve
mnsPS_buildTransCrv = 'btc'

#matrixConstraintNode
mnsPS_matConst = 'mat' + mnsPS_const

#mnsSpringCurve
mnsPS_springCurve = "spCrv"

#addDoubleLinear
mnsPS_adl = "adl"

#multDoubleLinear
mnsPS_mdl = "mdl"

#decomposeMatrix
mnsPS_dcMat = "dcMat"

#multiplyDivide
mnsPS_md = "md"

#node relationship
mnsPS_nodeRel = "ndr"

#condition
mnsPS_cond = "cond"

#reverse
mnsPS_reverse = "rev"

#animCurvesUU
mnsPS_acUU = "acUU"

#choice
mnsPS_choice = "cho"

#inverseMatrix
mnsPS_invMat = "invMat"

#imagePlane
imgP = "imgP"

#parentCns
mnsPS_parCns = "parCns"

#pointCns
mnsPS_pntCns = "pntCns"

#orientCns
mnsPS_oriCns = "oriCns"

#scaleCns
mnsPS_sclCns = "sclCns"

#aimCns
mnsPS_aimCns = "aimCns"

#pvCns
mnsPS_pvCns = "pvCns"

#clamp
mnsPS_clp = "clp"

#multMatrix
mnsPS_mulMat = "mulMat"

#plusMinusAvarage
mnsPS_pma = "pma"

#dynamic pivot
mnsPS_dynPiv = "dynPiv"

#blendColors 
mnsPS_bldCol = "bldCol"

#simpleSquash
mnsPS_simSqsh = "simSqsh"

#crvZip
mnsPS_crvZip = "crvZip"

#simpleRivets
mnsPS_simRiv = "simRiv"

#crvZip
mnsPS_crvZipB = "crvZipB"

#bs
mnsPS_bs = "bsp"

#revCrv
mnsPS_revCrv = "revCrv"

#setRnge
mnsPS_setRng = "setRng"

#setRnge
mnsPS_cpom = "cpom"

#setRnge
mnsPS_lipZip = "lipZip"

#dist between
mnsPS_distBet = "distBet"

#remapFloatArray
mnsPS_rfa = "rfa"

#curveTweak
mnsPS_crvTwk = "crvTwk"

#cns
mnsPS_cnsCtrl = "cnsCtrl"

#cnsGrp
mnsPS_cnsGrp = "cnsOffset"

#autowheeldrive
mnsPS_awd = "awd"

#transformSpring
mnsPS_ts = "ts"

#sphereVectorPush
mnsPS_svp = "svp"

#angleBetween
mnsPS_angleBet = "angBet"

#sphereRoll
mnsPS_spr = "spr"

#volume joint node
mnsPS_vjn = "vjn"

#volume joints
mnsPS_vJnt = "vJnt"

#ikEffector
mnsPS_ikEff = "ike"

#quat selrp
mnsPS_quatSlerp = "qSlp"

#quat to euler
mnsPS_quatToEuler = "qte"

#mnsQuatBlend
mnsPS_qb = "qb"

mnsPS_pb = "pb"

#moduleVis
mnsPS_modVis = "modVis"


mnsTypeDict = buildTypeDict([
						["locator", mnsPS_loc],
						["interpolationLoc", mnsPS_iLoc, "locator"],
						["group", mnsPS_grp, "transform"],
						["rigTop", mnsPS_rigTop, "transform"],
						["jointStructGrp", mnsPS_jntStruct, "transform"],
						["offsetSkeletonGrp", mnsPS_offsetSkelGrp, "transform"],
						["guideGrp", mnsPS_guide, "transform"],
						["puppetGrp", mnsPS_puppet, "transform"],
						["visHelpersGrp", mnsPS_visHelpGrp, "transform"],
						["modelGrp", mnsPS_modelGrp, "transform"],
						["extraSetupGrp", mnsPS_extraSetupGrp, "transform"],
						["freeJointsGrp", mnsPS_freeJntsGrp, "transform"],
						["pickerLayoutGrp", mnsPS_pickerLayout, "transform"],
						["controlShapesGrp", mnsPS_ctrlShpsGrp, "transform"],
						["moduleTop", mnsPS_module, "transform"],
						["offsetGrp", mnsPS_offsetGrp, "transform"],
						["cnsGrp", mnsPS_cnsGrp, "transform"],
						["modifyGrp", mnsPS_modGrp, "transform"],
						["offsetCnsGrp", mnsPS_osCns, "transform"],
						["spaceSwitchGrp", mnsPS_ssGrp, "transform"],
						["mirrorScaleGroup", mnsPS_mirGrp, "transform"],
						["controlShape", mnsPS_ctrlShape, "transform"],
						["controlShapeExport", mnsPS_ctrlShapeExport, "transform"],
						["joint", mnsPS_jnt],
						["interpolationJoint", mnsPS_iJnt, "joint"],
						["helperJoint", mnsPS_hJnt, "joint"],
						["rootJoint", mnsPS_rJnt, "joint"],
						["rigRootJoint", mnsPS_rrJnt, "joint"],
						["offsetJoint", mnsPS_oJnt, "joint"],
						["volumeJoint", mnsPS_vJnt, "joint"],
						["ctrl", mnsPS_ctrl, "transform"],
						["techCtrl", mnsPS_techCtrl, "transform"],
						["cns", mnsPS_cnsCtrl, "transform"],
						["guideCtrl", mnsPS_gCtrl, "transform"],
						["customGuide", mnsPS_cgCtrl, "transform"],
						["guideRootCtrl", mnsPS_gRootCtrl, "transform"],
						["pickerLayoutCtrl", mnsPS_plg, "transform"],
						["curve", mnsPS_crv, "nurbsCurve"],
						["axisVis", mnsPS_axisVis, "mesh"],
						["geometry", mnsPS_geo, "mesh"],
						["mesh", mnsPS_geo],
						["ikHandle", mnsPS_ikHan],
						["ikEffoctor", mnsPS_ikEff],
						["cluster", mnsPS_clus],
						["camera", mnsPS_cam],
						["projectionCamera", mnsPS_projCam, "camera"],
						["set", mnsPS_set, "objectSet"],
						["skinCluster", mnsPS_skinCluster],
						["blendShape", mnsPS_bsp],
						["mnsPointsOnCurve", mnsPS_psoc],
						["mnsCurveVariable", mnsPS_crvVar],
						["mnsIKSolver", mnsPS_ikSolver],
						["mnsNodeRelationship", mnsPS_nodeRel],
						["mnsAnnotate", mnsPS_annotate],
						["mnsBuildTransformsCurve", mnsPS_buildTransCrv],
						["mnsSpringCurve", mnsPS_springCurve],
						["mnsResampleCurve", mnsPS_rsc],
						["mnsThreePointArc", mnsPS_tpa],
						["mnsCameraGateRatio", mnsPS_cgr],
						["mnsSphereVectorPush", mnsPS_svp],
						["lambert", mnsPS_lambert],
						["mnsMatrixConstraint", mnsPS_matConst],
						["addDoubleLinear", mnsPS_adl],
						["decomposeMatrix", mnsPS_dcMat],
						["quatSlerp", mnsPS_quatSlerp],
						["quatToEuler", mnsPS_quatToEuler],
						["multDoubleLinear", mnsPS_mdl],
						["multiplyDivide", mnsPS_md],
						["condition", mnsPS_cond],
						["reverse", mnsPS_reverse],
						["animCurveUU", mnsPS_acUU],
						["choice", mnsPS_choice],
						["inverseMatrix", mnsPS_invMat],
						["imagePlane", imgP],
						["parentConstraint", mnsPS_parCns],
						["pointConstraint", mnsPS_pntCns],
						["orientConstraint", mnsPS_oriCns],
						["scaleConstraint", mnsPS_sclCns],
						["aimConstraint", mnsPS_aimCns],
						["poleVectorConstraint", mnsPS_pvCns],
						["clamp", mnsPS_clp],
						["multMatrix", mnsPS_mulMat],
						["plusMinusAverage", mnsPS_pma],
						["mnsDynamicPivot", mnsPS_dynPiv],
						["blendColors", mnsPS_bldCol],
						["mnsSimpleSquash", mnsPS_simSqsh],
						["blendShape", mnsPS_bs],
						["mnsCurveZip", mnsPS_crvZip],
						["mnsCurveZipB", mnsPS_crvZipB],
						["reverseCurve", mnsPS_revCrv],
						["setRange", mnsPS_setRng],
						["mnsClosestPointsOnMesh", mnsPS_cpom],
						["mnsSimpleRivets", mnsPS_simRiv],
						["mnsLipZip", mnsPS_lipZip],
						["distanceBetween", mnsPS_distBet],
						["mnsRemapFloatArray", mnsPS_rfa],
						["mnsCurveTweak", mnsPS_crvTwk],
						["mnsAutoWheelDrive", mnsPS_awd],
						["mnsTransformSpring", mnsPS_ts],
						["angleBetween", mnsPS_angleBet],
						["mnsSphereRoll", mnsPS_spr],
						["mnsVolumeJoint", mnsPS_vjn],
						["mnsQuaternionBlend", mnsPS_qb],
						["mnsPoseBlend", mnsPS_pb],
						["mnsModuleVis", mnsPS_modVis]
						])

mnsValidSuffixes = [mnsTypeDict[key].suffix for key in mnsTypeDict.keys()]

mnsBuildObjectTypes = buildMultKeysDict([["locator", ["loc", "Loc", "LOC"]],
									  ["group", ["grp", "Grp", "GRP"]],
									  ["joint", ["jnt", "Jnt", "JNT"]],
									  ["interpolationJoint", ["InterpolationJoint", "interpolationjoint", "INTERPOLATIONJOINT"]],
									  ["interpolationLoc", ["InterpolationLoc", "interpolationloc", "INTERPOLATIONLOC"]]
									  ])

mnsSidesDict = buildMultKeysDict([[mnsPS_right, ["right", "Right", "RIGHT"]],
									[mnsPS_cen, ["center", "Center", "CENTER"]],
									[mnsPS_left, ["left", "Left", "LEFT"]]
									])

mnsAlphaDict = buildMultKeysDict([
								["A", []],
								["B", []],
								["C", []],
								["D", []],
								["E", []],
								["F", []],
								["G", []],
								["H", []],
								["I", []],
								["J", []],
								["K", []],
								["L", []],
								["M", []],
								["N", []],
								["O", []],
								["P", []],
								["Q", []],
								["R", []],
								["S", []],
								["T", []],
								["U", []],
								["V", []],
								["W", []],
								["X", []],
								["Y", []],
								["Z", []]
							 ])

mnsControlShapesDict = buildMultKeysDict([
								["circle", []],
								["square", []],
								["squareRound", []],
								["dial", []],
								["dialRound", []],
								["dialSquare", []],
								["pinchedCircle", []],
								["bubblePin", []],
								["teardrop", []],
								["arrowSquare", []],
								["arrowDodecagon", []],
								["curvedFourArrow", []],
								["fourArrow", []],
								["dodecagon", []],
								["triangle", []],
								["flatDiamond", []],
								["hexagon", []],
								["octagon", []],
								["plus", []],
								["cross", []],
								["diamond", []],
								["pick", []],
								["cube", []],
								["lightSphere", []],
								["sphere", []],
								["pyramid", []],
								["arrow", []],
								["doubleArrow", []],
								["tripleArrow", []],
								["cone", []],
								["lightPin", []],
								["pin", []],
								["pointArrow", []],
								["cylinder", []],
								["directionCircle", []],
								["directionDiamond", []],
								["text", []]
							 ])
