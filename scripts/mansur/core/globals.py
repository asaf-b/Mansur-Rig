"""All top level global variable declaration.
	Used thoughout the python structure to easily manipulate global settings.
"""

#global dependencies
import os, sys


from maya import cmds
import pymel.core as pm


## globals
GLOB_mnsRootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))).replace("\\", "/")
GLOB_guiIconsDir = os.path.dirname(os.path.dirname(__file__)) + "/gui/icons"
GLOB_mayaVersion = int(cmds.about(version=True))
GLOB_compatibleMayaVersions = ["2020", "2022", "2023", "2024", "2025", "2026"]
GLOB_supportedPlatforms = ["win", "linux"]
GLOB_user = os.environ['USER']
mns_visualStudioMSBuildDir = "C:/Program Files (x86)/Microsoft Visual Studio/2017/Community/MSBuild/15.0/Bin/MSBuild.exe"

GLOB_mnsPrefsFolderName = "mansurPrefs"
GLOB_mnsPrefsFileName = "mnsPreferences.json"
GLOB_additionalModulePathsJsonName = "moduleParentPaths"
GLOB_additionalModulePresetsPathsJsonName = "modulePresetsPaths"
GLOB_modPresetSuffix = "mnsBMPS"
GLOB_moduleDirectoryFlag = "buildModulesDir.mns"
GLOB_mnsBlockDefColorScheme = [(1,0.15,0.15), (0,1,0), (0,0,1),(1,0.15,0.15), (0.15,1,0.15), (0.15,0.15,1), (1,0.3,0.3), (0.3,1,0.3), (0.3,0.3,1),(1,0.45,0.45), (0.45,1,0.45), (0.45,0.45,1),(1,0.6,0.6), (0.6,1,0.6), (0.6,0.6,1)]

GLOB_mnsJntStructDefaultSuffix = "Main"

GLOB_autoLoadPluginList = ["mnsAnnotate",
							"mnsBuildTransformsCurve",
							"mnsCameraGateRatio",
							"mnsCurveVariable",
							"mnsDynamicPivot",
							"mnsIKSolver",
							"mnsLicDigest",
							"mnsMatrixConstraint",
							"mnsNodeRelationship",
							"mnsPointsOnCurve",
							"mnsResampleCurve",
							"mnsSimpleSquash",
							"mnsSpringCurve",
							"mnsThreePointArc",
							"matrixNodes",
							"mnsVolumeJoint",
							"mnsCurveTweak",
							"mnsPoseBlend",
							"mnsModuleVis"]

GLOB_cnsToolNodeName = "c_mnsCns_A001_grp"
GLOB_pyVer = sys.version_info.major
GLOB_mnsPrefs = {}
GLOB_schemes = ["dark"]

GLOB_mnsPickerInstances = {}