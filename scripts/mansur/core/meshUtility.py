from maya.api import OpenMaya as om


from maya import cmds
import pymel.core as pm

from . import utility as mnsUtils

def getSymDictForMesh(meshName = "", tolerance = 0.02):
	if meshName:
		if pm.objExists(meshName):
			mSel=om.MSelectionList()
			mSel.add(meshName)
			mObj=mSel.getDagPath(0)
			mfnMesh=om.MFnMesh(mObj)
			baseShape = mfnMesh.getPoints()

			mtol = tolerance
			lVerts, rVerts, mVerts, corrVerts = [], [], [], {}

			for i in range(mfnMesh.numVertices):
				thisPoint = mfnMesh.getPoint(i) 
				if thisPoint.x > 0 + mtol: lVerts.append((i, thisPoint)) 
				elif thisPoint.x < 0 - mtol: rVerts.append((i, thisPoint))
				else:  mVerts.append((i, thisPoint))

			rVertspoints= [i for v , i in rVerts]

			for vert, mp in lVerts: #going through our left points, unpacking our vert index and mPoint position()
				nmp=om.MPoint(-mp.x, mp.y, mp.z) #storing the reversed mpoint of the left side vert
				rp = mfnMesh.getClosestPoint(nmp) #getting the closest point on the mesh
				if rp[0] in rVertspoints: #cheking if the point is in the right side
					corrVerts[vert] = rVerts[rVertspoints.index(rp[0])][0] #adding it if it is true
				else: #if it is not, calculate closest vert
					#iterating through rVertspoints and find smallest distance
					dList=[nmp.distanceTo(rVert) for rVert in rVertspoints] #distance list for each vert based on input point
					mindist = min(dList) #getting the closest distance
					corrVerts[vert] = rVerts[dList.index(mindist)][0] #adding the vert

			return corrVerts

def getShapeFromTransform(node, inter=False):
	returnState = None

	node = mnsUtils.checkIfObjExistsAndSet(node)
	if node and type(node) == pm.nodetypes.Transform:
		shapes = node.getShapes()

		for shape in shapes:
			isIntermediate = shape.intermediateObject.get()
			if inter and isIntermediate and pm.listConnections(shape, source=False): return shape
			elif not inter and not isIntermediate: return shape
		  
		if shapes: return shapes[0]
	elif type(node) == pm.nodetypes.Mesh or type(node) == pm.nodetypes.NurbsCurve or type(node) == pm.nodetypes.NurbsSurface:
	   return node

	return None

def extractBlendShapeTragets(mesh, bsDeformer):
	origBSConnection = bsDeformer.envelope.listConnections(s = True, d = False, p = True)
	origBSValue = bsDeformer.envelope.get()
	
	bsDeformer.envelope.disconnect()
	bsDeformer.envelope.set(1)
	
	targets = pm.listAttr(bsDeformer.w, m = True)
	if targets:
		originalConnections = {}
		
		#first disconnect attributes, and store the connection and values
		#then set all targets to 0
		for targetName in targets:
			originalConnections[targetName] = {"plug": None, "val": bsDeformer.attr(targetName).get()}
				
			origConnection = bsDeformer.attr(targetName).listConnections(s = True, d = False, p = True)
			if origConnection:
				originalConnections[targetName]["plug"] = origConnection[0]
			
			bsDeformer.attr(targetName).disconnect()
			bsDeformer.attr(targetName).set(0)
	   
		#now extract the targets 
		newTargets = []
		newTarGroup = pm.createNode("transform", name = "extractedTargets_grp")
		for targetName in targets:
			bsDeformer.attr(targetName).set(1)
			targetDup = pm.duplicate(mesh)[0]
			bsDeformer.attr(targetName).set(0)
			pm.parent(targetDup, newTarGroup)
			targetDup.v.set(0)
			targetDup.rename(targetName)
			newTargets.append(targetDup)

		#and restore original connection and value
		for targetName in originalConnections:
			bsDeformer.attr(targetName).set(originalConnections[targetName]["val"])
			
			if originalConnections[targetName]["plug"]:
				originalConnections[targetName]["plug"] >> bsDeformer.attr(targetName)
		
		bsDeformer.envelope.set(origBSValue)
		if origBSConnection:
			origBSConnection[0] >>  bsDeformer.envelope
			
		return newTarGroup, newTargets

def duplicateBlendShapeNodes(origMesh, meshTwin, **kwargs):
	connect = kwargs.get("connect", False)

	bshps = origMesh.listHistory(type = "blendShape")
	if bshps:
		for bsNode in bshps:
			newTarGroup, newTargets = extractBlendShapeTragets(origMesh, bsNode)

			#all dat collected, recreate the BS and connect
			newBS = pm.blendShape(newTargets, meshTwin, foc = True, name = bsNode.nodeName() + "_copy")[0]
			pm.delete(newTarGroup)

			if connect:
				for targetName in newTargets:
					targetName = targetName.split("|")[-1]
					bsNode.attr(targetName) >> newBS.attr(targetName)

			
			return newBS