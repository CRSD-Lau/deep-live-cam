# License Folder

The primary application license is the repository-root `LICENSE` file, which contains AGPL-3.0.

`PYTHON_DEPENDENCIES.md` records the current Windows packaging environment's dependency license metadata snapshot. Regenerate it before each public release candidate and reconcile any `UNKNOWN`, GPL/LGPL, or non-SPDX entries.

`BUNDLED_BINARY_OBLIGATIONS.md` records high-attention obligations for bundled native libraries and LGPL/GPL-family dependencies in the Windows PyInstaller payload.

`THIRD_PARTY_LICENSES/` is generated from the active build environment by `tools/collect_third_party_license_files.py` and contains high-attention package license/notice/metadata files that PyInstaller may not copy automatically.

For Windows binary releases, keep this folder for copied third-party license texts that are not already reproduced by package metadata or top-level notices. At minimum, final release candidates should preserve:

- AGPL-3.0 for Deep-Live-Cam.
- GPL-3.0 notices for GPL dependencies such as `cv2_enumerate_cameras`.
- LGPL-3.0 notices and Qt for Python notices for `PySide6`.
- GPLv2 notice and compatibility review notes for `pyvirtualcam`.
- Native library notices emitted by NumPy, ONNX Runtime, TensorFlow, OpenCV, and PySide6 wheels.

Do not place model binaries in this folder.
