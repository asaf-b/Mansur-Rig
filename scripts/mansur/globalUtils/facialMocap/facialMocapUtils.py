"""=== Author: Assaf Ben Zur ===
"""

#global dependencies


from maya import cmds
import pymel.core as pm

from pymel.core import datatypes as dt
from maya import OpenMaya

try:
	import cPickle as pickle
except ImportError:
	import pickle

try:
	from six import string_types #2018 and up
except ImportError:
	string_types = str
	from io import StringIO ## 2017

#Qt dependencies
if int(cmds.about(version = True)) > 2024:
	from PySide6 import QtGui, QtWidgets, QtCore
else:
	from PySide2 import QtGui, QtWidgets, QtCore

#mns dependencies
from ...core import log as mnsLog
from ...core.prefixSuffix import *
from ...core import string as mnsString
from ...core import utility as mnsUtils
from ...core import UIUtils as mnsUIUtils
from ...core import nodes as mnsNodes
from ...core.globals import *

dialog_form_class, dialog_base_class = mnsUIUtils.buildFormBaseClassForUI(os.path.dirname(__file__), "importPrefixesDialog.ui")
class ImportPrefixesDialog(QtWidgets.QDialog, dialog_form_class):
	def __init__(self):
		super(ImportPrefixesDialog, self).__init__()
		self.setupUi(self)
		# set initials values to widgets

	def getResults(self):
		if self.exec_() == QtWidgets.QDialog.Accepted:
			# get all values
			sourcePrefix = self.sourcePrefix_le.text()
			targetPrefix = self.targetPrefix_le.text()
			return sourcePrefix, targetPrefix
		else:
			return None

def refreshPbNode(pbNode):
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)

	if pbNode:
		pbNode.reinitialize.set(True)
		pm.dgdirty()
		pm.refresh()
		pbNode.reinitialize.set(False)

def connectSourceAttrsToPB(pbNode, sourceAttrs, **kwargs):
	mode = kwargs.get("mode", 0) #0 - add, 1 - replace

	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	
	originalConnections = {}
	if sourceAttrs and pbNode:
		for attrIdx in range(pbNode.data.numElements()):
			inputAttr = pbNode.data[attrIdx].poseValue.listConnections(s = True, d = False, p = True)
			if inputAttr:
				inputAttr = inputAttr[0]
				poseName = pbNode.data[attrIdx].poseName.get()
				poseWeight = pbNode.data[attrIdx].poseWeight.get()
				poseMinimum = pbNode.data[attrIdx].poseMinimum.get()
				poseMaximum = pbNode.data[attrIdx].poseMaximum.get()
				originalConnections.update({inputAttr: {"idx": attrIdx, 
														"poseName": poseName,
														"poseWeight": poseWeight,
														"poseMinimum": poseMinimum,
														"poseMaximum": poseMaximum}})
			if mode == 1:
				pm.removeMultiInstance(pbNode.data[attrIdx], b = True)

		nextAvailableIndex = max(0, pbNode.data.numElements() - 1)
		for i, attr in enumerate(sourceAttrs):
			if mode == 0 and not attr in originalConnections.keys():
				attr >> pbNode.data[nextAvailableIndex].poseValue
				poseName = attr.info().split(".")[-1]
				pbNode.data[nextAvailableIndex].poseName.set(poseName)
				nextAvailableIndex += 1
			elif mode == 1:
				attr >> pbNode.data[i].poseValue
				if attr in originalConnections.keys():
					pbNode.data[i].poseWeight.set(originalConnections[attr]["poseWeight"])
					pbNode.data[i].poseMinimum.set(originalConnections[attr]["poseMinimum"])
					pbNode.data[i].poseMaximum.set(originalConnections[attr]["poseMaximum"])

def removeSourceAttrsFromPbNode(pbNode, sourceAttrNames = [], **kwargs):
	mode = kwargs.get("mode", 0) #0 - remove, 1 - clear
	if not sourceAttrNames: sourceAttrNames = []

	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:
		for attrIdx in range(pbNode.data.numElements()):
			inputAttr = pbNode.data[attrIdx].poseValue.listConnections(s = True, d = False, p = True)
			if inputAttr:
				inputAttr = inputAttr[0]
				poseName = inputAttr.info().split(".")[-1]
				
				execute = True
				if mode == 0:
					if not poseName in sourceAttrNames:
						execute = False
				
				if execute:
					pm.removeMultiInstance(pbNode.data[attrIdx], b = True)

def getTransformCustomAttrs(targetNode):
	returnAttrs = []
	if targetNode:
		attrs = pm.PyNode(targetNode).listAttr(k = True, se = True, c = True, s = True, ud = True, v = True) 
		for attr in attrs:
			attrType = attr.type()
			if attrType == "double" or attrType == "float":
				if attr.getDefault() == 0.0:
					returnAttrs.append(attr)
	return returnAttrs
	
def connectOutTarget(sourceAttr, targetNode):
	sourceAttr.outTranslate >> targetNode.t
	sourceAttr.outRotate >> targetNode.r
	sourceAttr.outScale >> targetNode.s
	
	targetCustomAttrs = getTransformCustomAttrs(targetNode)
	for i, cAttr in enumerate(targetCustomAttrs):
		sourceAttr.outCustomAttribute[i] >> cAttr

def disconnectOutTarget(sourceAttr, targetNode):
	if targetNode:
		try: sourceAttr.outTranslate // targetNode.t
		except: pass
		try: sourceAttr.outRotate // targetNode.r
		except: pass
		try: sourceAttr.outScale // targetNode.s
		except: pass

		#targetNode.t.set((0.0,0.0,0.0))
		#targetNode.r.set((0.0,0.0,0.0))
		#targetNode.s.set((1.0,1.0,1.0))

		targetCustomAttrs = getTransformCustomAttrs(targetNode)
		for i, cAttr in enumerate(targetCustomAttrs):
			try: sourceAttr.outCustomAttribute[i] // cAttr
			except: pass

def connectTargetTransformsToPbNode(pbNode, targetTransforms):
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	
	existingTransforms = []
	if targetTransforms and pbNode:
		for attrIdx in range(pbNode.target.numElements()):
			inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False)
			if inputAttr:
				inputTransform = inputAttr[0]
				existingTransforms.append(inputTransform)
		
		nextAvailableIndex = max(0 , pbNode.target.numElements() - 1)
		for targetTransform in targetTransforms:
			if not targetTransform in existingTransforms:
				targetTransform.message >> pbNode.target[nextAvailableIndex].targetTransform
				connectOutTarget(pbNode.outTarget[nextAvailableIndex], targetTransform)
				nextAvailableIndex += 1

def removeTargetTransformsFromPbNode(pbNode, targetTransformsNames = [], **kwargs):
	mode = kwargs.get("mode", 0) #0 - remove, 1 - clear
	if not targetTransformsNames: targetTransformsNames = []

	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:
		for attrIdx in range(pbNode.target.numElements()):
			inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False)
			if inputAttr:
				inputAttr = inputAttr[0]
				execute = True
				if mode == 0:
					if not inputAttr in targetTransformsNames:
						execute = False
				
				if execute:
					pm.removeMultiInstance(pbNode.target[attrIdx], b = True)

def connectOutputs(pbNode, **kwargs):
	mode = kwargs.get("mode", 1)  # 0 = disconnect, 1 = connect
	
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:
		nodesToConnectStore = []
		for attrIdx in range(pbNode.target.numElements()):
			inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False)
			if inputAttr:
				inputTransform = inputAttr[0]
				nodesToConnectStore.append(inputTransform)

		for attrIdx in range(pbNode.outTarget.numElements()):
			if mode == 0:
				disconnectOutTarget(pbNode.outTarget[attrIdx], nodesToConnectStore[attrIdx])
			else:
				connectOutTarget(pbNode.outTarget[attrIdx], nodesToConnectStore[attrIdx])

def muteSourceAttrs(pbNode, **kwargs):
	mode = kwargs.get("mode", 1)  # 0 = disconnect, 1 = connect

	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:	
		for attrIdx in range(pbNode.data.numElements()):
			inputAttr = pbNode.data[attrIdx].poseValue.listConnections(s = True, d = False, p = True)
			if inputAttr:
				inputAttr = inputAttr[0]
				if mode == 0:
					inputAttr.mute()
					inputAttr.set(0.0)
				elif mode == 1:
					inputAttr.unmute()
			
def isTransformChanged(targetTransform):
	for channelName in "trs":
		for axisName in "xyz":
			attrToTest = targetTransform.attr(channelName + axisName)
			if not round(attrToTest.getDefault(), 2) == round(attrToTest.get(), 2):
				return True
				break

	targetCustomAttrs = getTransformCustomAttrs(targetTransform)
	for cAttr in targetCustomAttrs:
		if not round(cAttr.getDefault(), 2) == round(cAttr.get(), 2):
			return True
			break

	return False

def storePose(pbNode, poseName):
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode and poseName:
		for attrIdx in range(pbNode.target.numElements()):
			inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False, p = False)
			if inputAttr:
				targetTransform = inputAttr[0]
				#check if there is an existing storage for this pose name
				existingPoseAttr = None
				for poseAttrIdx in range(pbNode.target[attrIdx].targetPose.numElements()):
					targetPoseName = pbNode.target[attrIdx].targetPose[poseAttrIdx].targetPoseName.get()
					if targetPoseName == poseName:
						existingPoseAttr = pbNode.target[attrIdx].targetPose[poseAttrIdx]
						break

				if isTransformChanged(targetTransform) or existingPoseAttr:
					#store pose
					targetAttr = pbNode.target[attrIdx].targetPose
					targetCustomAttrs = getTransformCustomAttrs(targetTransform)
		
					if not existingPoseAttr: #new pose
						if targetAttr.numElements() == 1 and not targetAttr[0].targetPoseName.get():
							nextAvailableIndex = 0
						else:
							nextAvailableIndex = targetAttr.numElements()

						targetAttr[nextAvailableIndex].targetPoseName.set(poseName)
						targetAttr[nextAvailableIndex].poseTranslate.set(targetTransform.t.get())
						targetAttr[nextAvailableIndex].poseRotate.set(targetTransform.r.get())
						targetAttr[nextAvailableIndex].poseScale.set(targetTransform.s.get())

						for i, cAttr in enumerate(targetCustomAttrs):
							targetAttr[nextAvailableIndex].customAttribute[i].set(cAttr.get())

					else: #existing pose update
						existingPoseAttr.poseTranslate.set(targetTransform.t.get())
						existingPoseAttr.poseRotate.set(targetTransform.r.get())
						existingPoseAttr.poseScale.set(targetTransform.s.get())

						for i, cAttr in enumerate(targetCustomAttrs):
							existingPoseAttr.customAttribute[i].set(cAttr.get())
						
def resetPose(pbNode):
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:
		for attrIdx in range(pbNode.target.numElements()):
			inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False, p = False)
			if inputAttr:
				targetTransform = inputAttr[0]
				for channelName in "trs":
					for axisName in "xyz":
						attr = targetTransform.attr(channelName + axisName)
						try:
							attr.set(attr.getDefault())
						except:
							pass
				
				targetCustomAttrs = getTransformCustomAttrs(targetTransform)
				for cAttr in targetCustomAttrs:
					try:
						cAttr.set(cAttr.getDefault())
					except:
						pass

def loadPose(pbNode, poseStorage):
	if pbNode and poseStorage:
		resetPose(pbNode)

		toDel = []
		for nodeName in poseStorage.keys():
			targetTransform = mnsUtils.checkIfObjExistsAndSet(nodeName)
			if targetTransform:
				targetTransform.setMatrix(poseStorage[nodeName]["matrix"])

				for cAttrName in poseStorage[nodeName]["customAttribues"].keys():
					if targetTransform.hasAttr(cAttrName):
						targetTransform.attr(cAttrName).set(poseStorage[nodeName]["customAttribues"][cAttrName])
		pm.delete(toDel)

def getMirrorTransform(sourceTransformName, **kwargs):
	leftPrefix = kwargs.get("leftPrefix", "l_")
	rightPrefix = kwargs.get("rightPrefix", "r_")

	if sourceTransformName:
		if sourceTransformName.startswith(leftPrefix):
			mirrorTransformName = rightPrefix + sourceTransformName[len(leftPrefix):]
			return mirrorTransformName
		elif sourceTransformName.startswith(rightPrefix):
			mirrorTransformName = leftPrefix + sourceTransformName[len(rightPrefix):]
			return mirrorTransformName

def mirrorPose(targetTransform, mirrorTransform):
	if targetTransform and mirrorTransform:
		targetMatrix =  targetTransform.getMatrix(worldSpace=True)
		
		pm.makeIdentity(targetTransform)
		pm.makeIdentity(mirrorTransform)
		zeroTargetMatrix = targetTransform.getMatrix(worldSpace=True)
		zeroMirrorMatrix = mirrorTransform.getMatrix(worldSpace=True)
		reflectionMatrix_YZ = pm.datatypes.Matrix(-1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0)
		reflectionReferenceMat = (zeroTargetMatrix * reflectionMatrix_YZ)
		mirrorTransform.setMatrix(reflectionReferenceMat , worldSpace=True)
		reflectionReferenceRotation = mirrorTransform.r.get()
  
		targetMirror = (targetMatrix * reflectionMatrix_YZ)
		mirrorTransform.setMatrix(targetMirror , worldSpace=True)

		for i, chan in enumerate("xyz"):
			try:
				mirrorTransform.attr("r" + chan).set(mirrorTransform.attr("r" + chan).get() + (reflectionReferenceRotation[i] * -1))
			except:
				pass
				
def copyPose(pbNode, flip = False, **kwargs):
	leftPrefix = kwargs.get("leftPrefix", "l_")
	rightPrefix = kwargs.get("rightPrefix", "r_")

	storage = {}
	localPoseStore = {}
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:
		if flip:
			#first store pose for end of process recovery
			localPoseStore = copyPose(pbNode)

			#locally store changed matricies
			localStorage = {}
			for attrIdx in range(pbNode.target.numElements()):
				inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False, p = False)
				if inputAttr:
					targetTransform = inputAttr[0]
					if isTransformChanged(targetTransform):
						targetCustomAttrs = getTransformCustomAttrs(targetTransform)
						localStorage[targetTransform] = {"matrix": targetTransform.getMatrix(), "customAttribues": {}}
						
						for cAttr in targetCustomAttrs:
							localStorage[targetTransform]["customAttribues"][cAttr.attrName()] = cAttr.get()

			#zeroAll
			resetPose(pbNode)

			#get mirror data and collect
			for targetTransform in localStorage.keys():
				mirrorTransform = mnsUtils.checkIfObjExistsAndSet(getMirrorTransform(targetTransform, **kwargs))
				targetTransform = mnsUtils.checkIfObjExistsAndSet(targetTransform)
				if targetTransform and mirrorTransform:
					storage[mirrorTransform.nodeName()] = {"matrix": None, "customAttribues": {}}

					if targetTransform in localStorage.keys():
						targetMatrix = localStorage[targetTransform]["matrix"]
						targetTransform.setMatrix(targetMatrix)
						mirrorPose(targetTransform, mirrorTransform)
						storage[mirrorTransform.nodeName()]["matrix"] = mirrorTransform.getMatrix()

						targetCustomAttrs = localStorage[targetTransform]["customAttribues"]
						for cAttr in targetCustomAttrs:
							if mirrorTransform.hasAttr(cAttr):
								storage[mirrorTransform.nodeName()]["customAttribues"][cAttr] = localStorage[targetTransform]["customAttribues"][cAttr]

						pm.makeIdentity(targetTransform)
						pm.makeIdentity(mirrorTransform)
			
			#restore pose
			loadPose(pbNode, localPoseStore)
		else:
			for attrIdx in range(pbNode.target.numElements()):
				inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False, p = False)
				if inputAttr:
					targetTransform = inputAttr[0]
					if isTransformChanged(targetTransform):
						targetCustomAttrs = getTransformCustomAttrs(targetTransform)
						storage[targetTransform.nodeName()] = {"matrix": None, "customAttribues": {}}
						transformStore = targetTransform.getMatrix()
						storage[targetTransform.nodeName()]["matrix"] = transformStore

						for cAttr in targetCustomAttrs:
							storage[targetTransform.nodeName()]["customAttribues"][cAttr.attrName()] = cAttr.get()
	return storage

def collectInputDataFromPbNode(pbNode):
	sourceData = {}
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	if pbNode:
		for attrIdx in range(pbNode.data.numElements()):
			inputAttr = pbNode.data[attrIdx].poseValue.listConnections(s = True, d = False, p = True)
			
			poseName = pbNode.data[attrIdx].poseName.get()
			inputAttrPoseName = ""
			inputAttrName = ""
			if inputAttr:
				inputAttr = inputAttr[0]
				inputAttrName = mnsUtils.removeNamespaceFromString(inputAttr.name())
				inputAttrPoseName = inputAttr.info().split(".")[-1]
				
			poseWeight = pbNode.data[attrIdx].poseWeight.get()
			poseMinimum = pbNode.data[attrIdx].poseMinimum.get()
			poseMaximum = pbNode.data[attrIdx].poseMaximum.get()
			
			sourceData[poseName] = {"poseName": poseName,
									"inputAttrPoseName": inputAttrPoseName,
									"inputAttrName": inputAttrName,
									"poseWeight": poseWeight,
									"poseMinimum": poseMinimum,
									"poseMaximum": poseMaximum}
	return sourceData

def collectTargetDataFromPbNode(pbNode):
	pbNode = mnsUtils.checkIfObjExistsAndSet(pbNode)
	targetData = {}

	if pbNode:
		for attrIdx in range(pbNode.target.numElements()):
			inputAttr = pbNode.target[attrIdx].targetTransform.listConnections(s = True, d = False)
			if inputAttr:
				inputTransform = inputAttr[0]
				inputTransformName = mnsUtils.removeNamespaceFromString(inputTransform.nodeName())
				
				targetPoses = {}
				for poseAttrIdx in range(pbNode.target[attrIdx].targetPose.numElements()):
					targetPoseAttr = pbNode.target[attrIdx].targetPose[poseAttrIdx]
					targetPoseName = targetPoseAttr.targetPoseName.get()
				
					if targetPoseName:
						poseTranslate = targetPoseAttr.poseTranslate.get()
						poseRotate = targetPoseAttr.poseRotate.get()
						poseScale = targetPoseAttr.poseScale.get()
						
						poseCustomAttributes = []
						poseCustomAttributeAttr = targetPoseAttr.customAttribute
						for i in range(poseCustomAttributeAttr.numElements()):
							poseCustomAttributes.append(poseCustomAttributeAttr[i].get())

						targetPoseData = {"targetPoseName": targetPoseName,
											"poseTranslate": poseTranslate,
											"poseRotate": poseRotate,
											"poseScale": poseScale,
											"poseCustomAttributes": poseCustomAttributes}
						targetPoses[targetPoseName] = targetPoseData

				targetData[inputTransformName] = {"targetTransformName": inputTransformName,
												"targetPoses": targetPoses}
	return targetData										

def exportPBData(pbNode):
	sourceData = collectInputDataFromPbNode(pbNode)
	targetData = collectTargetDataFromPbNode(pbNode)
	
	if sourceData or targetData:
		exportData = {"sourceData": sourceData,
						"targetData": targetData,
						"definitionName": pbNode.nodeName()
						}

		filename = QtWidgets.QFileDialog.getSaveFileName(mnsUIUtils.get_maya_window(), "Export Facial Mocap Data", None, "Mns Facial Mocap Data (*.mnsFMD)")
		if filename: 
			filename = filename[0]
			if filename.endswith(".mnsFMD"):
					fh = open(filename, 'wb')
					pickle.dump(exportData, fh, pickle.HIGHEST_PROTOCOL)
					fh.close()
					mnsLog.log("Exported Facial Mocap Data Succesfully to: \'" + filename + "\'.", svr = 1)
					#dialog
					pm.confirmDialog( title='Success', message="Exported Facial Mocap Data Succesfully to: \'" + filename + "\'.", defaultButton='OK')
			else:
				mnsLog.log("Invalid file name. Aborting.", svr = 1)

def collectFMDataFromFile(filePath = None):
	filePath = filePath or QtWidgets.QFileDialog.getOpenFileName(mnsUIUtils.get_maya_window(), "Import Facial Mocap Data", None, "Mns Facial Mocap Data (*.mnsFMD)")
	if filePath: 
		if not isinstance(filePath, string_types): filePath = filePath[0]
		if filePath.endswith(".mnsFMD"):
			if os.path.isfile(filePath):
				fh = open(filePath, 'rb')
				returnData = pickle.load(fh)
				fh.close()
				return returnData
			else:
				mnsLog.log("Couldn't find the specified FMD file.", svr = 1)
		else:
			mnsLog.log("Invalid file name.", svr = 1)
	
def importFMDataFromFile():
	FMData = collectFMDataFromFile()
	if FMData and "definitionName" in FMData.keys():
		infoReturn = []

		targetNameSpace = ""
		sourceNameSpace = ""

		prefixDialog = ImportPrefixesDialog()
		prefixes = prefixDialog.getResults()
		if prefixes:
			sourceNameSpace, targetNameSpace =  prefixes

		definitionName = FMData["definitionName"].split("_")[1]
		#create new definition
		pbNode = mnsNodes.mnsPoseBlendNode(body = definitionName)

		sourceData = FMData["sourceData"]
		targetData = FMData["targetData"]

		sourceAttrs = []
		for sourceAttrName in sourceData.keys():
			inputAttrName = mnsUtils.removeNamespaceFromString(sourceData[sourceAttrName]["inputAttrName"])
			if "." in inputAttrName:
				hostNodeName = inputAttrName.split(".")[0]
				if hostNodeName:
					hostNodeName = sourceNameSpace + ":" + hostNodeName
				
				hostNode = mnsUtils.checkIfObjExistsAndSet(hostNodeName)
				if hostNode:
					inputAttrName = inputAttrName.replace((inputAttrName.split(".")[0] + "."), "")
					if hostNode.hasAttr(inputAttrName):
						sourceAttrs.append(hostNode.attr(inputAttrName))

		if sourceAttrs:
			#connect source attrs
			connectSourceAttrsToPB(pbNode, sourceAttrs)
			infoReturn.append(["Sucessfully found source attributes and connected them.", True])
		else:
			infoReturn.append(["[ERROR] Couldn't find source attributes.", False])

		targetTransforms = []
		for ctrlName in targetData.keys():
			ctrlName = mnsUtils.removeNamespaceFromString(ctrlName)
			if targetNameSpace:
				ctrlName = targetNameSpace + ":" + ctrlName

			ctrlNode = mnsUtils.checkIfObjExistsAndSet(ctrlName)
			if ctrlNode:
				targetTransforms.append(ctrlNode)

		#connect target transforms
		if targetTransforms:
			connectTargetTransformsToPbNode(pbNode, targetTransforms)
			infoReturn.append(["Successfully found target transforms and connected them.", True])

			for ctrl in targetTransforms:
				ctrlKey = mnsUtils.removeNamespaceFromString(ctrl.nodeName())
				if ctrlKey in targetData.keys(): 
					outCons = ctrl.message.listConnections(s = False, d = True, p = True, t= "mnsPoseBlend")
					if outCons:
						targetAttr = outCons[0].parent()
						if "targetPoses" in targetData[ctrlKey].keys():
							for k, targetPoseKey in enumerate(targetData[ctrlKey]["targetPoses"]):
								pT =  targetData[ctrlKey]["targetPoses"][targetPoseKey]["poseTranslate"]
								pR =  targetData[ctrlKey]["targetPoses"][targetPoseKey]["poseRotate"]
								pS =  targetData[ctrlKey]["targetPoses"][targetPoseKey]["poseScale"]

								targetAttr.targetPose[k].targetPoseName.set(targetPoseKey)
								targetAttr.targetPose[k].poseTranslate.set(pT)
								targetAttr.targetPose[k].poseRotate.set(pR)
								targetAttr.targetPose[k].poseScale.set(pS)

								customAttributesAttr = targetAttr.targetPose[k].customAttribute
								customAttributes =  targetData[ctrlKey]["targetPoses"][targetPoseKey]["poseCustomAttributes"]
								for i, attrValue in enumerate(customAttributes):
									customAttributesAttr[i].set(attrValue)
		else:
			infoReturn.append(["[ERROR] Couldn't find target transforms.", False])

		#dialog
		refreshPbNode(pbNode)
		
		dialogText = "<font size = 4><b>The process finished successfully, with the following results:</b><br><br>"
		for k, infoLine in enumerate(infoReturn):
			if infoLine[1]:
				dialogText += "<font color = grey>"
			else:
				dialogText += "<font color = red><b>"
			dialogText += str(k + 1) + ". "
			dialogText += infoLine[0] + "<br>"
			if not infoLine[1]:
				dialogText += "</b>"

		pm.confirmDialog( title='Success', message=dialogText, defaultButton='OK')
		
		#return status
		return True