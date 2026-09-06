---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
app_version: 2.2.4
review_date: 2026-09-06
source_commit: 753aab70c34ae585d525a06b9f7de2d721b7f491
technical_inspection: PASS
publication_approval: PENDING
---

# DirectML 2.2.4 candidate: technical license and payload inspection

The inspected DirectML candidate preserves the reviewed dependency versions and license metadata, includes the LGPL/GPL full texts identified below, and contains no model weights, FFmpeg executables, CUDA runtime binaries, or Torch Python modules. This is a technical artifact inspection. It supplies evidence for the release review; it does not grant publisher acceptance or complete the manual release gates.

## Artifact and method

- Source: clean checkout at `753aab70c34ae585d525a06b9f7de2d721b7f491`; application version `2.2.4`.
- Official workflow run: `34056909310`; DirectML artifact ID: `9996349043`.
- Portable ZIP: `DeepLiveCamStudio-2.2.4-DirectML-x64-portable.zip`, 641,461,085 bytes, SHA-256 `3b0b1eec9467021215a1d2cff702062653305f131e70471800c755c2c8ca283a`.
- Extracted payload: 2,327 files, 1,852,098,831 bytes. The archive digest and extraction counts agree with the existing official-artifact validation record.
- CLI executable SHA-256: `51bc3516b1ffc17a6ae5fd48ba38f727f3787d28fb39a2783729fe569ad7edb2`.
- GUI executable SHA-256: `b7cbd20ac677f8c7e0a3ef49161cbd8e9f97aefdb62f2778d79e64be387fd4df`.

The audit read actual license contents and metadata, compared version tables with the exact source lock, inspected native version resources, enumerated the extracted files, and parsed both executables' embedded PyInstaller archives without launching the application. It also downloaded the two small upstream hooks wheels for in-memory hash/content comparison; nothing was installed. Detailed relative paths and hashes are in `directml_compliance_inventory.json`. No inference, physical-camera capture, GUI interaction, user-data changes, or installed-app changes were performed.

All paths below are relative to the extracted portable bundle unless described as source or upstream-wheel paths.

## Qt for Python: actual files and license options

Each of these four directories contains `METADATA` and `licenses/LicenseRef-Qt-Commercial.txt`:

- `LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/`
- `LICENSES/THIRD_PARTY_LICENSES/PySide6_Addons-6.11.1/`
- `LICENSES/THIRD_PARTY_LICENSES/PySide6_Essentials-6.11.1/`
- `LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/`

The metadata for all four reports version `6.11.1`, the license expression `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`, and `License-File: LicenseRef-Qt-Commercial.txt`. The umbrella PySide6 metadata pins the other three packages to exactly `6.11.1`. In `PySide6-6.11.1/METADATA`, line 6 contains the license expression, line 40 identifies the commercial-reference file, and lines 135–140 contain the upstream licensing paragraph describing open-source and commercial options.

The four commercial-reference files are each 470 bytes and have the same SHA-256, `4f54763ac0fe2abd8f7f8d8fe370a94a08ebf84786aa0b91045bd6628deb08a3`. Their contents address holders of commercial Qt licenses, refer to their agreement or accepted terms, and point to Qt's terms and contact pages. They are commercial pointers rather than the GNU license bodies. Their filename does not override the open-source license expression carried in the same package metadata. All eight Qt metadata/reference files are byte-identical to the corresponding files in the clean source checkout.

The open-source license texts are present elsewhere in this same bundle. The following cross-reference makes their location explicit:

| Qt metadata option | Bundled full-text copy | Content verified | SHA-256 |
| --- | --- | --- | --- |
| `LGPL-3.0-only` | `LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE` | 7,651 bytes; LGPL version 3 title, sections 0–6, and complete final section. Its introduction incorporates GPL version 3, whose full text is present in the next row. | `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768` |
| `GPL-3.0-only` | `LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE` | 35,823 bytes; GPL version 3, terms through section 17, end-of-terms marker at line 621, and application appendix. | `230184f60bae2feaf244f10a8bac053c8ff33a183bcc365b4d8b876d2b7f4809` |
| `GPL-2.0-only` | `LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE` | 18,431 bytes; GPL version 2, terms through section 12, end-of-terms marker at line 280, and application appendix. | `189b1af95d661151e054cea10c91b3d754e4de4d3fecfb074c1fb29476f7167b` |

These are existing shared full-text copies; their directory names identify the dependencies from which they were collected. No separate LGPL/GPL full-text file was found inside the four Qt notice directories or the `_internal/PySide6` and `_internal/shiboken6` runtime trees. The bundle therefore must not be described as lacking the GNU license texts. This report clarifies their layout without rewriting upstream files or claiming that file presence alone proves every distribution obligation.

The installed layout retains separate `_internal/PySide6/Qt6Core.dll`, `QtCore.pyd`, `QtGui.pyd`, `QtWidgets.pyd`, Qt plugin DLLs, and `_internal/shiboken6/Shiboken.pyd`. `Qt6Core.dll` reports native file version `6.11.1.0`. The two inspected binding `.pyd` files have no fixed PE version resource; their package metadata remains the version evidence.

Qt's official guidance identifies copies of license terms, notices, source availability, and library replacement as inspection topics. Its current Qt for Python documentation distinguishes Community and Commercial distributions. These references explain the inspection basis and do not supply release-specific acceptance: [Qt LGPL/GPL obligations](https://www.qt.io/development/open-source-lgpl-obligations), [Qt for Python distribution guidance](https://doc.qt.io/qtforpython-6/commercial/index.html).

## ONNX Runtime DirectML and runtime inventory

`LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/METADATA` identifies `onnxruntime-directml` version `1.23.0` and the MIT license. Its `package/LICENSE` is 1,094 bytes and contains Microsoft's copyright, permission grant, reproduction condition, and warranty disclaimer; SHA-256 is `c250d6278f0b47a6439fb7592b08b58a55eb9f535aa49a1db63211c3f982b674`. Both files are byte-identical to their clean-source copies.

The actual `_internal/onnxruntime/capi` directory contains `DirectML.dll`, `onnxruntime.dll`, `onnxruntime_providers_shared.dll`, and `onnxruntime_pybind11_state.pyd`. Windows string version resources report ONNX Runtime `1.23.20250924.2.be835ef`, DirectML `1.15.4+241025-1615.1.dml-1.15.fac7597`, and the bundled `python311.dll` reports Python `3.11.9`. Fixed numeric PE versions are separately retained in the inventory JSON and need not match those display strings.

Every one of the 102 package/version rows in `LICENSES/PYTHON_DEPENDENCIES_DIRECTML.md`, including its separate build/excluded table, matches `requirements-locks/windows-directml-py311.lock` from the exact source commit. The runtime entries include Qt/shiboken `6.11.1`, ORT DirectML `1.23.0`, ONNX `1.22.0`, NumPy `1.26.4`, TensorFlow `2.19.1`, InsightFace `0.7.3`, Pillow `12.3.0`, OpenCV `4.10.0.84` and headless OpenCV `4.11.0.86`. This is an environment-metadata inventory, not a claim that every installed package is included as an executable component.

The source DirectML lock differs from `v2.2.3` in exactly one package version: the build hook package described below. Existing `namex` unknown metadata, pyvirtualcam compatibility review, native third-party notices, model-source restrictions, and publisher decisions retain their established status; this inspection invents no new approval for those items.

## PyInstaller hooks delta

The source build requirement and DirectML lock advance `pyinstaller-hooks-contrib` from `2026.6` to `2026.7`; PyInstaller stays `6.22.2`. Ruff changes from `0.16.4` to `0.16.5` in development tooling and is outside this runtime profile.

Upstream wheels were fetched read-only and checked against PyPI's SHA-256 values and the source lock history:

| Wheel | SHA-256 |
| --- | --- |
| `pyinstaller_hooks_contrib-2026.6-py3-none-any.whl` | `fd13b8ac126b35361175edacd41a0d97080b75dd5f4b594ecefefff969509dd3` |
| `pyinstaller_hooks_contrib-2026.7-py3-none-any.whl` | `24257a04c7a5a7a034cf28e39dcee20fbeeb9f043076729480f2e1b69904408a` |

The wheels' `*.dist-info/licenses/LICENSE` files are byte-identical: 27,666 bytes, SHA-256 `91d0baaff00773038e72c0a1fc9d5d2d38706b7a2b9c04f34296608f931b9cd0`. Both distinguish standard build hooks under GPL-2.0-or-later from runtime hooks under Apache-2.0. The `_pyinstaller_hooks_contrib/rthooks/pyi_rth_tensorflow.py` files are also byte-identical: 2,665 bytes, SHA-256 `e62136eb3413803723c6f9d22b2fc2097a4938b54df7ee9c404785a5bffc877e`, with an Apache-2.0 header. See the exact-version upstream records: [2026.6](https://pypi.org/project/pyinstaller-hooks-contrib/2026.6/), [2026.7](https://pypi.org/project/pyinstaller-hooks-contrib/2026.7/).

Both packaged executables contain the normal `pyi_rth_*` bootstrap entries, including `pyi_rth_tensorflow`. Neither embedded module archive contains `PyInstaller` or `_pyinstaller_hooks_contrib` as an importable package. Excluding the build-tool package does not mean no runtime hook code is present. This comparison verifies the changed package's license continuity and its relevant upstream runtime-hook continuity; it does not assert byte-for-byte identity of every generated bootstrap code object.

## Exclusion checks and remaining scope

Independent filesystem and executable-archive checks found:

- Zero files with conventional model/checkpoint extensions `.onnx`, `.pth`, `.pt`, `.ckpt`, `.safetensors`, `.h5`, `.hdf5`, `.pb`, or `.tflite`.
- Zero `ffmpeg` or `ffprobe` executable/file stems.
- Zero native CUDA/cuDNN/Torch binaries matching the reviewed runtime families.
- Zero Torch, torchvision, or torchaudio Python source/extension files in the extracted payload; zero such modules in either executable's 6,609-entry PYZ archive.

The retained `torch-2.11.0_cu128` and `onnxruntime-gpu-1.24.4` notice directories document the repository's alternate CUDA profile. Their presence is not evidence that those runtime packages or DLLs are installed in the DirectML payload. The scan above inspects executable components separately from historical/profile-shared notice files.

This report verifies the DirectML artifact only. The CUDA candidate, actual stable installer upgrade, fresh clean-VM execution, packaged GUI Preview/Live behavior, and physical-webcam receiver workflow require their own evidence. Existing synthetic OBS receiver and packaged DirectML inference tests remain useful scoped evidence; they do not complete those missing manual gates. The release controller must preserve pending states until the corresponding requirements are fulfilled. No binary rebuild is indicated solely by the existing GNU text-copy locations documented here.
