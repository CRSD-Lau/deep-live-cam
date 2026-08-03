# License Evidence

This folder keeps the license and redistribution evidence used for Windows release review.

> [!IMPORTANT]
> The primary application license is the repository-root [`LICENSE`](../LICENSE), which contains AGPL-3.0.

## What Lives Here

| File or folder | Purpose |
| --- | --- |
| [`PYTHON_DEPENDENCIES.md`](PYTHON_DEPENDENCIES.md) | CUDA dependency license metadata snapshot from the Windows packaging environment. |
| [`PYTHON_DEPENDENCIES_DIRECTML.md`](PYTHON_DEPENDENCIES_DIRECTML.md) | DirectML dependency license metadata snapshot from its isolated Windows packaging environment. |
| [`BUNDLED_BINARY_OBLIGATIONS.md`](BUNDLED_BINARY_OBLIGATIONS.md) | High-attention obligations for native libraries and GPL/LGPL-family dependencies in the PyInstaller payload. |
| [`MODEL_LICENSE_AUDIT.md`](MODEL_LICENSE_AUDIT.md) | Model-source review notes and redistribution posture. |
| [`WINDOWS_BUNDLE_MANIFEST.md`](WINDOWS_BUNDLE_MANIFEST.md) | Installed payload manifest summary for the Windows bundle. |
| [`THIRD_PARTY_LICENSES/`](THIRD_PARTY_LICENSES/) | Collected package license, notice, and metadata files that may not be copied automatically by PyInstaller. |

## Release Rules

- Regenerate dependency and third-party license evidence before every public release candidate.
- Reconcile any `UNKNOWN`, GPL/LGPL, unusual, or non-SPDX dependency metadata before publishing.
- Keep high-attention license texts available beside the installed app when required.
- Preserve model-license notes separately from application-license notes.
- Do not place model binaries in this folder.

## Minimum Release Evidence

Final Windows release candidates should preserve evidence for:

- AGPL-3.0 for Deep-Live-Cam.
- GPL-3.0 notices for GPL dependencies such as `cv2_enumerate_cameras`.
- LGPL-3.0 notices and Qt for Python notices for `PySide6`.
- GPLv2 notice and compatibility review notes for `pyvirtualcam`.
- Native library notices emitted by NumPy, ONNX Runtime, TensorFlow, OpenCV, and PySide6 wheels.

> [!CAUTION]
> Model binaries have separate redistribution risk. Keep them out of this folder and out of release assets unless each file has explicit redistribution approval.
