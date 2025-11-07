## Mansur-Rig 2.6.0
Released 01 Jan 2025

### General
Maya 2025 Support for Windows</b>- Due to increasing complications and hardware requirements, Mansur-Rig 2.6 now supports Maya 2025 for Windows platform only. Linux support IS NOT dropped, only delayed. I'm still working hard on implementing support for Maya 2025 for linux as well. Since it is taking longer, I didn't want to delay the release for windows.
PyMel library was moved to an internal Mansur-Rig dependency- Due to some distribution issues/delays with the open source library PyMel, I decided to move this dependency to an internal component within Mansur-Rig, so I can be in control of it. That also means that all previous PyMel installation requirements are no longer required.


### Features
Wing Module- bat wing upgrade

### Bug Fixes
- Export skin- this utility would sometimes fail to find the shape node and skinCluster for the requested meshes- Fixed.
- Limb- upper twist issues were reported again, and fixed again.

### mnsMayaPlugins v 2.6
- Maya 2025 build for windows

### Transition Log
- Please use the centralized "Update Rig" utility button in Block's utility tab to update rigs built with previous versions of Mansur-Rig. 