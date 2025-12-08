## Mansur-Rig 3.0.0
Released 10 Dec 2025

### General
<B>Mansur-Rig is going open source!</b>
<br>All license restrictions have been removed, and activation is no longer required.

* <B>IMPORTANT NOTE</b>: Please update to this version before 1 March 2026. <b>On March 1st 2026, Mansur-Rig's licensing server will be shut-down</b>, rendering all previous versions UNUSABLE. Since all previous versions included license restrictions, once the licensing server will shut down, product activation will no longer be possible.

* <b>Linux:</b> Linux Support is temporarily dropped. Unfourtunatlly, due to increasing complications and hardware requirements, and lack of popularity amoung Linux users, Linux support is dropped until further notice. Keeping up with Autodesk's requirements is getting more and more challenging, and it got to a point where I can no longer justify complying with it. I apologize.

* <b>Distribution</b>: From this version on, Mansur-Rig distribution will be done from the <a href="https://github.com/asaf-b/Mansur-Rig">public Git-Hub Repository</a>. On March 1st 2026 Mansur-Rig's Web-App will be taken down alogside it's current distribution page.

### Features
* <b>OPEN SOURCE</b>: Mansur-Rig is updating to a partial open-source product. The new public repository can be found <a href="https://github.com/asaf-b/Mansur-Rig"><b>HERE</b></a>. C++ code remains private, although will be compiled and maintained for future versions, and the result mll files will be released publicly under the main repo. <b>All license restrictions have been removed, and activation is no longer required.</b> Only installation is required to use Mansur-Rig and rigs built with it.

* <b>Maya 2026 support for Windows</b>: Please note that <a href="https://help.autodesk.com/view/MAYAUL/2026/ENU/?guid=Maya_ReleaseNotes_2026_release_notes_known_limitations2026_html">Autodesk have introduced a breaking change in Maya 2026</a>. This change was handeled in version 3.0, and from Maya version 2026 onwards, the new DL format will be used within Mansur-Rig. Also, a centralized function to change all previous DL nodes format to the new one, was added into the main <u>Update-Rig</u> process. Since Autodesk kept the old DL format within 2026, suggesting it will be completely dropped in version 2027, this update will only be possible within Maya 2026 version. In case the old DL format will be dropped completely in the future, it will mean that rigs that were built in versions below 2026 will not be possible to open in version 2027 onwards. In case that happens, I suggest opening any Block Rig in Maya 2026, using the centralized <u>Update-Rig</u> process, updating the rig to be 2026 onwards compatible.This is NOT Mansur-Rig rig related- a general breaking change Maya have introduced that must be accommodated to.
> <i>"addDoubleLinear, multiplyDoubleLinear, and pointMatrixMult cause errors in custom scripts, while other DoubleLinear attributes result in Script Editor warnings"</i> 

* "FindNextIncrement" function upgraded to be able to increment Alpha as well, when the 999 ID limit is passed
* Added flip Right option to Splay module
* localClump flip attributes splitted to translate & rotate

### Bug Fixes
* Limb- Mute Root Twist featured was reviewed and stabalized.
* Lips B module- node accumulation bug- Fixed
* Maya 2025 DynUI is not working- Fixed
* freeControl- "position mode" is taken into account only in "sameMeshEffector" mode- Fixed

### mnsMayaPlugins v 3.0
* All license restrictions removed. mnsLicDigest removed.
* Maya 2026 build for windows

### Transition Log
- Please use the centralized "Update Rig" utility button in Block's utility tab to update rigs built with previous versions of Mansur-Rig. 