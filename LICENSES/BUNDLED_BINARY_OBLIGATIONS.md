# Bundled Binary License Obligations

This notice summarizes high-attention obligations for native libraries and copyleft dependencies bundled in the Windows PyInstaller payload. It is not legal advice. Re-check package metadata and upstream notices before each public release candidate.

## Why this file exists

The Windows installer ships a Python runtime, Python packages, native extension modules, and third-party DLLs. Some components are permissively licensed, while others carry LGPL/GPL-family obligations that need more care than a package-name table.

Keep this file installed beside `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, and `LICENSES/PYTHON_DEPENDENCIES.md`.

## High-attention bundled components

| Component | Local metadata observed | Release handling |
| --- | --- | --- |
| `PySide6`, `PySide6_Addons`, `PySide6_Essentials`, `shiboken6` | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | Preserve Qt for Python license files and notices. Keep the installed `_internal/PySide6`, `_internal/shiboken6`, and plugin DLL layout inspectable. Do not prohibit reverse engineering for debugging LGPL-covered components. Maintain a path for users to replace LGPL-covered libraries where legally required. |
| `easydict` | `LGPL-3.0` | Include LGPL notice and corresponding source availability. The AGPL corresponding-source release should include the exact dependency versions used to build the binary. |
| `cv2_enumerate_cameras` | GPL license text in package metadata | Include GPL notice and corresponding source availability. Treat this as part of the AGPL-compatible copyleft surface. |
| `pyvirtualcam` | GPLv2 classifier in package metadata | Review compatibility before public binary distribution. Keep source availability and license notice. Consider disabling/removing this optional feature if legal review does not approve the combined binary. |
| ONNX Runtime GPU, TensorFlow, OpenCV, NumPy/SciPy, Pillow, PySide6 | Native DLLs and `.pyd` extension modules | Preserve bundled notice/license files collected from wheels. Review native-library notices in the generated `WINDOWS_BUNDLE_MANIFEST.md` and installed `_internal` tree before publishing. |

## Release checklist

- Include `LICENSE`, `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, `LICENSES/PYTHON_DEPENDENCIES.md`, `LICENSES/THIRD_PARTY_LICENSES/`, `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`, and this file in the installer.
- Publish complete corresponding source for the exact binary release, including packaging scripts and modifications.
- Keep the PyInstaller `onedir` layout for release builds unless legal review approves a different layout. The directory layout makes DLLs and package metadata easier to inspect than a single-file executable.
- Do not strip third-party `.dist-info`, `licenses`, or native notice files merely to reduce package size.
- Confirm whether the release publisher will satisfy LGPL replaceability requirements by documented replacement instructions, relinkable object files, source offer, or another lawyer-approved method.
- Re-run `tools/generate_python_dependency_licenses.py` and `tools/generate_windows_bundle_manifest.py` for every release candidate.
- Re-run `tools/collect_third_party_license_files.py` for every release candidate so high-attention package license files from the build environment are copied into `LICENSES/THIRD_PARTY_LICENSES/`.

## Not bundled

The Windows installer intentionally does not bundle model/checkpoint files, ffmpeg/ffprobe, OBS, NVIDIA drivers, CUDA Toolkit, cuDNN, or TensorRT system runtime installers. If a future release bundles any of those items, add their exact license, source, build configuration, and redistribution permission evidence here before publishing.
