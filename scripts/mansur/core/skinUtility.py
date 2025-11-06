"""=== Author: Assaf Ben Zur ===
"""

#global dependencies


from maya import cmds
import pymel.core as pm

import os

try:
	from six import string_types #2018 and up
except ImportError:
	string_types = str
	from io import StringIO ## 2017, 2025

try:
	import cPickle as pickle
except ImportError:
	import pickle
from functools import partial

#maya dependencies
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaAnim as OpenMayaAnim
from maya import mel

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtWidgets, QtCore
else:
	from PySide2 import QtGui, QtWidgets, QtCore

#mns dependencies
from . import log as mnsLog
from .prefixSuffix import *
from . import utility as mnsUtils
from . import UIUtils as mnsUIUtils
from . import meshUtility as mnsMeshUtils
from ..block.core import blockUtility as blkUtils
from .globals import *

def getSkinningJointsFromSelection(mode = 1, **kwargs):
	mainJointsOnly = kwargs.get("mainJointsOnly", False)

	returnArray = []

	moduleRoots = blkUtils.collectModuleRootsBasedOnMode(mode)
	if moduleRoots:
		for rGuide in moduleRoots:
			sJnts = []

			rGuide = mnsUtils.validateNameStd(rGuide)
			searchPattern = rGuide.side + "_" + rGuide.body + "*_" + rGuide.alpha + "*_" + mnsPS_iJnt
			iJnts = [c for c in pm.ls(searchPattern)]

			#for both limb and hind limb modules
			#if a foot is a child module, 
			#remove the last interp joint from return
			status, modType = mnsUtils.validateAttrAndGet(rGuide, "modType", "")
			if modType == "limb" or modType == "hindLimb":
				for childModNode in rGuide.node.listRelatives(ad = True, type = "transform"):
					if mnsPS_gRootCtrl in childModNode.nodeName():
						childMod = mnsUtils.validateNameStd(childModNode)
						if childMod and childMod.suffix == mnsPS_gRootCtrl:
							status, childModType = mnsUtils.validateAttrAndGet(childMod, "modType", "")
							if childModType and childModType == "foot":
								status, interpolationJoints = mnsUtils.validateAttrAndGet(rGuide, "interpolationJoints", None)
								if interpolationJoints:
									rmIndex = interpolationJoints
									for iJnt in iJnts:
										iJntNStd = mnsUtils.validateNameStd(iJnt)
										if iJntNStd:
											if iJntNStd.id == rmIndex:
												iJnts.remove(iJnt)

			if not iJnts:
				searchPattern = rGuide.side + "_" + rGuide.body + "*_" + rGuide.alpha + "*_" + "*nt"
				sJnts = [c for c in pm.ls(searchPattern)]
			elif mainJointsOnly:
				searchPattern = rGuide.side + "_" + rGuide.body + "*_" + rGuide.alpha + "*_" + "*nt"
				sJnts = [c for c in pm.ls(searchPattern)]
			else: sJnts = iJnts

			returnArray += sJnts
			if mainJointsOnly:
				for j in returnArray:
					if "_" + mnsPS_iJnt in j.nodeName():
						returnArray.remove(j)
	#return; list
	return returnArray

def getGeometryComponentsFromTagExpression(skinCls, tag="*"):
	geo_types = ["mesh", "nurbsSurface", "nurbsCurve"]
	for t in geo_types:
		obj = skinCls.listConnections(et=True, t=t)
		if obj:
			geo = mnsMeshUtils.getShapeFromTransform(obj[0]).nodeName()

	# Get the geo out attribute for the shape
	out_attr = cmds.deformableShape(geo, localShapeOutAttr=True)[0]

	# Get the output geometry data as MObject
	sel = OpenMaya.MSelectionList()
	sel.add(geo)
	dep = OpenMaya.MObject()
	sel.getDependNode(0, dep)
	fn_dep = OpenMaya.MFnDependencyNode(dep)
	plug = fn_dep.findPlug(out_attr, True)
	obj = plug.asMObject()

	# Use the MFnGeometryData class to query the components for a tag
	# expression
	fn_geodata = OpenMaya.MFnGeometryData(obj)

	# Components MObject
	components = fn_geodata.resolveComponentTagExpression(tag)

	dagPath = OpenMaya.MDagPath.getAPathTo(dep)
	return dagPath, components

def getGeometryComponents(skinClusterFn = None, skinClusterNode = None):
	if skinClusterFn:
		try:
			fnSet = OpenMaya.MFnSet(skinClusterFn.deformerSet())
			members = OpenMaya.MSelectionList()
			fnSet.getMembers(members, False)
			dagPath = OpenMaya.MDagPath()
			components = OpenMaya.MObject()
			members.getDagPath(0, dagPath, components)
			return dagPath, components
		except:
			return getGeometryComponentsFromTagExpression(skinClusterNode)

def getSkinClusterFromMeshTransform(meshTransform = None):
	meshTransform = mnsUtils.checkIfObjExistsAndSet(meshTransform)

	if meshTransform:
		shapeNode = mnsMeshUtils.getShapeFromTransform(meshTransform)
		if shapeNode:
			skins = shapeNode.listHistory(type = "skinCluster", il = 2)
			if skins: return skins[0]
	return None

def getCurrentWeights(dagPath, components, skinClusterFn):
	weights = OpenMaya.MDoubleArray()
	util = OpenMaya.MScriptUtil()
	util.createFromInt(0)
	pUInt = util.asUintPtr()
	skinClusterFn.getWeights(dagPath, components, weights, pUInt);
	return weights

def gatherInfluenceWeights(dagPath, components, skinClusterFn):
	weights = getCurrentWeights(dagPath, components, skinClusterFn)

	influencePaths = OpenMaya.MDagPathArray()
	numInfluences = skinClusterFn.influenceObjects(influencePaths)
	numComponentsPerInfluence = int(weights.length() / numInfluences)

	influenceWeights = {}
	for i in range(influencePaths.length()):
		influenceName = influencePaths[i].partialPathName()
		influenceWithoutNamespace = mnsUtils.removeNamespaceFromString(influenceName.split("|")[-1])
		influenceWeights[influenceWithoutNamespace] = [weights[j*numInfluences+i] for j in range(numComponentsPerInfluence)]

	return influenceWeights

def gatherBlendWeights(dagPath, components, skinClusterFn):
	weights = OpenMaya.MDoubleArray()
	skinClusterFn.getBlendWeights(dagPath, components, weights)
	return [weights[i] for i in range(weights.length())]

def injectSkinClusterNodeToMfn(skinClusterNode = None):
	if skinClusterNode:
		selectionList = OpenMaya.MSelectionList()
		selectionList.add(skinClusterNode.nodeName())

		mObject = OpenMaya.MObject()
		selectionList.getDependNode(0, mObject)
		scFn = OpenMayaAnim.MFnSkinCluster(mObject)
		return scFn

def gatherDataFromSkinCluster(skinClusterNode = None):
	if skinClusterNode:
		scFn = injectSkinClusterNodeToMfn(skinClusterNode)
		if scFn:
			dagPath, components = getGeometryComponents(scFn, skinClusterNode)
			influenceWeights = gatherInfluenceWeights(dagPath, components, scFn)
			blendWeights = gatherBlendWeights(dagPath, components, scFn)
				
			data = {
					'weights' : influenceWeights,
					'blendWeights' : blendWeights,
					'skinningMethod': skinClusterNode.skinningMethod.get(),
					'normalizeWeights': skinClusterNode.normalizeWeights.get(),
					'skinClusterNodeName': skinClusterNode.nodeName()
					}
			return data

def gatherSkinData(nodes = []):
	skinsData = {}

	if nodes:
		if type(nodes) != list: nodes = [nodes]

		validObjTypes = [pm.nodetypes.Mesh, pm.nodetypes.NurbsCurve, pm.nodetypes.NurbsSurface]
		meshes = [meshTransform for meshTransform in nodes if type(meshTransform) == pm.nodetypes.Transform and meshTransform.getShape() and type(meshTransform.getShape()) in validObjTypes] 
		for meshTransform in meshes:
			skinClusterNode = getSkinClusterFromMeshTransform(meshTransform)
			if skinClusterNode:
				skinData = gatherDataFromSkinCluster(skinClusterNode)
				skinsData[meshTransform.nodeName()] = skinData
	return skinsData

def exportSkin(nodes = [], **kwargs):
	returnData = kwargs.get("returnData", False)
	
	if nodes:
		filename = [""]
		if not returnData:
			filename = QtWidgets.QFileDialog.getSaveFileName(mnsUIUtils.get_maya_window(), "Export Skin", None, "Mns Skin (*.mnsSkin)")
		
		if filename: 
			filename = filename[0]
			if returnData or filename.endswith(".mnsSkin"):
				skinsData = gatherSkinData(nodes)
				if skinsData:
					if returnData:
						return skinsData
					else:
						fh = open(filename, 'wb')
						pickle.dump(skinsData, fh, pickle.HIGHEST_PROTOCOL)
						fh.close()
						mnsLog.log("Exported skin succesfully to: \'" + filename + "\'.", svr = 1)
				else:
					mnsLog.log("Couldn't find meshes/skins to export.", svr = 1)
			else:
				mnsLog.log("Invalid file name. Aborting.", svr = 1)
	else:
		mnsLog.log("Couldn't find meshes/skins to export.", svr = 1)

def gatherSkinDataFromFile(filePath = None):
	returnData = None
	filePath = filePath or QtWidgets.QFileDialog.getOpenFileName(mnsUIUtils.get_maya_window(), "Import Skin", None, "Mns Skin (*.mnsSkin)")
	if filePath: 
		if not isinstance(filePath, string_types): filePath = filePath[0]
		if filePath.endswith(".mnsSkin"):
			if os.path.isfile(filePath):
				fh = open(filePath, 'rb')
				returnData = pickle.load(fh)
				fh.close()
			else:
				mnsLog.log("Couldn't find the specified skin file.", svr = 1)
		else:
			mnsLog.log("Invalid file name.", svr = 1)
	return returnData

def getMeshesFromData(skinsData = None):
	returnObjects = []
	if skinsData:
		for meshName in skinsData.keys():
			mesh = mnsUtils.checkIfObjExistsAndSet(meshName)
			if mesh: returnObjects.append(mesh)
	return returnObjects

def setInfluenceWeights(dagPath, components, scFn, skinData):
	weights = getCurrentWeights(dagPath, components, scFn)
	influencePaths = OpenMaya.MDagPathArray()
	numInfluences = scFn.influenceObjects(influencePaths)
	numComponentsPerInfluence = int(weights.length() / numInfluences)

	for importedInfluence, importedWeights in skinData['weights'].items():
		for ii in range(influencePaths.length()):
			influenceName = influencePaths[ii].partialPathName()
			influenceWithoutNamespace = mnsUtils.removeNamespaceFromString(influenceName)
			if influenceWithoutNamespace == importedInfluence:
				# Store the imported weights into the MDoubleArray
				for jj in range(numComponentsPerInfluence):
					weights.set(importedWeights[jj], jj*numInfluences+ii)
				break

	influenceIndices = OpenMaya.MIntArray(numInfluences)
	for ii in range(numInfluences):
		influenceIndices.set(ii, ii)
	scFn.setWeights(dagPath, components, influenceIndices, weights, False);

def setBlendWeights(dagPath, components, scFn, skinData):
	blendWeights = OpenMaya.MDoubleArray(len(skinData['blendWeights']))
	for i, w in enumerate(skinData['blendWeights']):
		blendWeights.set(w, i)
	scFn.setBlendWeights(dagPath, components, blendWeights)

def setSkinData(skinClusterNode = None, skinData = None):
	if skinClusterNode and skinData:
		scFn = injectSkinClusterNodeToMfn(skinClusterNode)
		if scFn:
			dagPath, components = getGeometryComponents(scFn, skinClusterNode)
			setInfluenceWeights(dagPath, components, scFn, skinData)
			setBlendWeights(dagPath, components, scFn, skinData)
			skinClusterNode.skinningMethod.set(skinData["skinningMethod"])
			skinClusterNode.normalizeWeights.set(skinData["normalizeWeights"])
			return True

def importSkin(filePath = None, **kwargs):
	skinsData = kwargs.get("predefinedData", None)
	targetJoints = kwargs.get("predefinedTargetJoints", None)

	if not skinsData: skinsData = gatherSkinDataFromFile(filePath)

	if skinsData:
		meshes =  getMeshesFromData(skinsData)
		if meshes:
			for mesh in meshes:
				# Make sure the vertex count is the same
				shape = mnsMeshUtils.getShapeFromTransform(mesh)
				if shape:
					meshVertices = pm.polyEvaluate(shape, vertex=True)
					
					#Nurbs exception- skip vertex count check
					if type(shape) != pm.nodetypes.Mesh:
						meshVertices = len(skinsData[mesh.nodeName()]['blendWeights'])

					importedVertices = len(skinsData[mesh.nodeName()]['blendWeights'])
					if meshVertices != importedVertices:
						mnsLog.log("Import Skin failed for mesh: " + mesh.nodeName() + ". Vertex count mismatch.", svr = 3)
					else:
						skinCluster = getSkinClusterFromMeshTransform(mesh)
						if not skinCluster:
							jointInfluencesNames = skinsData[mesh.nodeName()]['weights'].keys()         
							jointInfluences = []
							for jntName in jointInfluencesNames:
								jnt = None
								if targetJoints:
									if jntName in targetJoints:
										jnt = targetJoints[jntName]
								else:
									jnt = mnsUtils.checkIfObjExistsAndSet(jntName)
								
								if jnt: jointInfluences.append(jnt)
								else:
									mnsLog.log("Import Skin failed for mesh: " + mesh.nodeName() + ". Couldn't find \'" + jntName + "\'.", svr = 3)
									return False

							skinCluster = pm.skinCluster(jointInfluences, shape, tsb=True, nw=2, n=skinsData[mesh.nodeName()]['skinClusterNodeName'])

						importState = setSkinData(skinCluster, skinsData[mesh.nodeName()])
						if importState: mnsLog.log("Imported Skin successfully on mesh: " + mesh.nodeName() + ".", svr = 1)
		else:
			mnsLog.log("The meshes within the skin file were not found.", svr = 3)

def filterValidMeshesFromList(meshTransforms = [], skinnedOnly = False, notSkinnedOnly = False):
	returnMeshes = []

	if meshTransforms:
		if isinstance(meshTransforms, string_types): meshTransforms = [meshTransforms]
		for meshTransform in meshTransforms:
			validObjTypes = [pm.nodetypes.Mesh, pm.nodetypes.NurbsCurve, pm.nodetypes.NurbsSurface]
			if type(meshTransform) == pm.nodetypes.Transform and meshTransform.getShape() and type(meshTransform.getShape()) in validObjTypes:
				if not skinnedOnly and not notSkinnedOnly:
					returnMeshes.append(meshTransform)
				else:
					skinClusterNode = getSkinClusterFromMeshTransform(meshTransform)
					if skinClusterNode and skinnedOnly: 
						returnMeshes.append(meshTransform)
					elif not skinClusterNode and notSkinnedOnly:
						returnMeshes.append(meshTransform)
					else:
						mnsLog.log("Some meshes were found invalid for the requested operation. Please make sure all of your source meshes have a skin cluster to transfer from.", svr = 1)
	return returnMeshes

def gatherInfluenceJointsFromMesh(skinnedMesh = None):
	influenceJoints = []

	if skinnedMesh:
		skinCluster = getSkinClusterFromMeshTransform(skinnedMesh)
		if skinCluster:
			for jnt in pm.skinCluster(skinCluster, q = True, inf = True):
				if jnt not in influenceJoints: influenceJoints.append(jnt)
	return influenceJoints

def gatherInfluenceJointsFromMeshes(sourceMeshes = None):
	influenceJoints = []
	if sourceMeshes:
		for mesh in sourceMeshes: influenceJoints += gatherInfluenceJointsFromMesh(mesh)

	return influenceJoints

def createCombinedSkinProxyFromMeshes(sourceMeshes = []):
	sourceMeshes = filterValidMeshesFromList(sourceMeshes, True)

	if sourceMeshes:
		influenceJoints = gatherInfluenceJointsFromMeshes(sourceMeshes)
			
		if influenceJoints:
			dupMeshes = pm.duplicate(sourceMeshes)
			pm.parent(sourceMeshes, w = True)
			combinedMesh = pm.polyUnite(sourceMeshes, ch= False, name = "tempProxySkinnedMesh_mns")
			pm.delete(sourceMeshes)
			pm.skinCluster(combinedMesh, influenceJoints)
			pm.copySkinWeights(origMeshes, combinedMesh, noMirror = True, surfaceAssociation = "closestPoint", influenceAssociation= "oneToOne")
			return combinedMesh

def copySkin(sourceMeshes = [], targetMeshes = [], **kwargs):
	if sourceMeshes and targetMeshes:
		surfaceAssociation = kwargs.get("surfaceAssociation", "closestPoint")
		influenceAssociation = kwargs.get("influenceAssociation", "oneToOne")
		noMirror = kwargs.get("noMirror", True)

		sourceMeshes = filterValidMeshesFromList(sourceMeshes, True, False)
		targetMeshes = filterValidMeshesFromList(targetMeshes, False, True)

		if sourceMeshes and targetMeshes:
			allRequiredInfluences = gatherInfluenceJointsFromMeshes(sourceMeshes)

			for targetMesh in targetMeshes:
				pm.skinCluster(targetMesh, allRequiredInfluences, tsb=True, nw = True)
			
				pm.copySkinWeights(sourceMeshes, 
									targetMesh, 
									noMirror = noMirror, 
									sm=True,
									surfaceAssociation = surfaceAssociation, 
									influenceAssociation= influenceAssociation)
			
			mnsLog.log("Skin copied successfully.", svr = 1)

def unbind(sourceMeshes = []):
	if sourceMeshes:
		if not type(sourceMeshes) is list: sourceMeshes = [sourceMeshes]
		sourceMeshes = filterValidMeshesFromList(sourceMeshes, True, False)

		for mesh in sourceMeshes:
			skinCluster = getSkinClusterFromMeshTransform(mesh)
			if skinCluster:
				try:
					pm.skinCluster(mesh, e = True, ub = True, unbindKeepHistory = False)
				except: pass

def rebind(sourceMeshes = []):
	if sourceMeshes:
		if not type(sourceMeshes) is list: sourceMeshes = [sourceMeshes]
		sourceMeshes = filterValidMeshesFromList(sourceMeshes, True, False)

		if sourceMeshes:
			skinsData = gatherSkinData(sourceMeshes)
			unbind(sourceMeshes)
			importSkin(predefinedData = skinsData)
			mnsLog.log("Meshes were rebound.", svr = 1)
			pm.select(sourceMeshes, replace = True)
			
def getSkinClustersFromJoints(sourceJoints = []):
	skinClusters = []
	
	if sourceJoints:
		for j in sourceJoints:
			for connectedNode in j.worldMatrix.listConnections(d = True, s = False):
				if type(connectedNode) == pm.nodetypes.SkinCluster and connectedNode not in skinClusters:
					skinClusters.append(connectedNode)
	return skinClusters
					
def getAllSkinClustersFromJointStructure(rigTop = None):
	skinClusters = []
	
	#locate rig top
	rigTop = mnsUtils.validateNameStd(rigTop)
	if not rigTop or not rigTop.suffix == mnsPS_rigTop:
		rigTop = blkUtils.getRigTopForSel()
	
	if rigTop:
		jntStrcutGrp = blkUtils.getJointStructGrpFromRigTop(rigTop)
		if jntStrcutGrp:
			rootJnt = [c for c in jntStrcutGrp.node.listRelatives(c = True, type = "joint") if "rigRoot" in c.nodeName()]
			if rootJnt:
				jointHeirarchy = rootJnt + [c for c in rootJnt[0].listRelatives(ad = True, type = "joint")]
				skinClusters = getSkinClustersFromJoints(jointHeirarchy)
			else:
				mnsLog.log("Couldn't find Root-Joint. Aborting.", svr = 2)
		else:
			mnsLog.log("Couldn't find Joint-Structure-Group. Aborting.", svr = 2)
	else:
		mnsLog.log("Couldn't find Rig-Top for selection. Aborting.", svr = 2)
	
	return skinClusters
	

def mirrorSkinToDetachedComponent(source = None, target = None):
	if not source and not target:
		sel = pm.ls(sl=True)
		if len(sel) > 1:
			source = sel[0]
			target = sel[1]
	
	source = mnsUtils.checkIfObjExistsAndSet(source)
	target = mnsUtils.checkIfObjExistsAndSet(target)

	if source and target:
		deformers = pm.listHistory(source, pruneDagObjects = True, interestLevel = 1)
		skinClusterA = None
		if deformers:
			for d in deformers:
				if type(d) == pm.nodetypes.SkinCluster:
					skinClusterA = d
					break
					
		#if a skin deformer exists
		if skinClusterA:
			influenceJoints = pm.skinCluster(skinClusterA, query=True, inf=True)
			if influenceJoints:
				oppositeInfluenceArray = influenceJoints
				for jnt in influenceJoints:
					jnt = mnsUtils.validateNameStd(jnt)
					if jnt:
						side = jnt.side
						symSide = mnsPS_right
						if side == mnsPS_right: symSide = mnsPS_left	
													
						oppositeJnt = mnsUtils.returnNameStdChangeElement(jnt, side = symSide, autoRename = False)					#jntSide = getMGearSide(jnt)
						oppositeJnt = mnsUtils.validateNameStd(oppositeJnt.name)
						if oppositeJnt and oppositeJnt.node not in oppositeInfluenceArray: 
							oppositeInfluenceArray.append(oppositeJnt.node)
				
				if oppositeInfluenceArray:
					dupMesh = pm.duplicate(source)[0]
					pm.parent(dupMesh, w = True)
					dupMeshMir = pm.duplicate(source)[0]
					scaleMirGrp = pm.createNode("transform", name = "mirTranTemp")
					pm.parent(dupMeshMir, scaleMirGrp)
					scaleMirGrp.sx.set(-1)
					combinedMesh = pm.polyUnite(dupMesh, dupMeshMir, ch = False)[0]
					pm.delete(dupMesh, scaleMirGrp)
					skNode = pm.skinCluster(combinedMesh, oppositeInfluenceArray, tsb = True)
					pm.copySkinWeights(ss = skinClusterA, ds=skNode, noMirror=True, surfaceAssociation = "closestPoint", ia="oneToOne",sm=True, nr=True)
					pm.copySkinWeights(ss= skNode, ds= skNode, mirrorMode = "YZ", surfaceAssociation = "closestPoint", influenceAssociation = "oneToOne", sm = True, nr=True)
					
					#check for skin custers on target, and delete if exists
					deformersB = pm.listHistory(target, pruneDagObjects = True, interestLevel = 1)
					if deformersB:
						for d in deformersB:
							if type(d) == pm.nodetypes.SkinCluster:
								pm.delete(d)

					#copy skin
					copySkin([combinedMesh], [target])
					pm.delete(combinedMesh)
					pm.select(target, r = True)
					mel.eval("removeUnusedInfluences;")

					mnsLog.log("Skin mirrored succesfully.", svr = 1)
	else:
		mnsLog.log("Invalid input. Aborting", svr = 2)