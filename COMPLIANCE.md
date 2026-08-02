# Compliance Notes for Windows Binary Releases

This repository is a modified build of Deep-Live-Cam. Deep-Live-Cam is licensed under AGPL-3.0. Binary distribution through a Windows installer is allowed only if the distributor satisfies the AGPL-3.0 source, license, copyright, and modification-notice obligations.

This document is not legal advice. Treat it as an engineering compliance checklist before publishing a GitHub Release.

## Packaging decision

The Windows packaging flow uses PyInstaller to create a self-contained application directory and Inno Setup to create a per-user Windows x64 installer. This keeps the Python runtime out of the user's setup path while preserving a normal uninstall entry, Start menu shortcuts, and a model-download command.

The installer does not bundle model/checkpoint files by default. Users must run:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

or manually place reviewed model files in the configured model directory.

## AGPL-3.0 obligations

When publishing a binary installer, do all of the following:

- Include the original `LICENSE` file with the installer and installed files.
- Keep Deep-Live-Cam attribution and do not remove upstream notices.
- Publish the complete corresponding source for the exact binary release, including build scripts, installer scripts, PyInstaller spec, and local modifications.
- Link the GitHub Release installer to the exact source tag or commit used to build it.
- Mark modifications clearly. At minimum, the release notes should state that this build adds Windows packaging, user-data model storage, explicit model download/verification, and compliance documentation.
- Do not impose further restrictions that conflict with AGPL-3.0.
- If the program is offered as a network service, AGPL-3.0 section 13 source-offer obligations may apply to remote users.

## Models and checkpoints

Do not upload model binaries to GitHub Releases unless you have separately confirmed redistribution rights for each file.

Known model sources used by the app:

| File | Source | Observed license/status | Installer policy |
| --- | --- | --- | --- |
| `inswapper_128.onnx` | `hacksider/deep-live-cam` on Hugging Face | Hugging Face repo declares `gpl-3.0`; InsightFace model notices may restrict model use to non-commercial research | Excluded; explicit user download with URL, license note, and SHA-256 |
| `inswapper_128_fp16.onnx` | `hacksider/deep-live-cam` on Hugging Face | Hugging Face repo declares `gpl-3.0`; same InsightFace risk | Excluded; explicit user download with URL, license note, and SHA-256 |
| `GPEN-BFR-256.onnx` | `netrunner-exe/Face-Upscalers-onnx` on Hugging Face | No OSI license declared; model card states non-commercial, academic, educational use only | Excluded; explicit user download with URL, license note, and SHA-256 |
| `GPEN-BFR-512.onnx` | `netrunner-exe/Face-Upscalers-onnx` on Hugging Face | No OSI license declared; model card states non-commercial, academic, educational use only | Excluded; explicit user download with URL, license note, and SHA-256 |
| `gfpgan-1024.onnx` | `hacksider/deep-live-cam` on Hugging Face; derived from TencentARC/GFPGAN | Hugging Face mirror declares `gpl-3.0`; upstream GFPGAN is Apache-2.0, but converted-model provenance should be rechecked | Excluded; explicit user download with URL, license note, and SHA-256 |

Current SHA-256 values are encoded in `modules/model_manager.py` and should be rechecked before each release.

The model-source review was refreshed on 2026-05-19. The exact URLs and review notes are recorded in `LICENSES/MODEL_LICENSE_AUDIT.md`.

## Dependency redistribution notes

The installer bundles Python wheels and native libraries collected by PyInstaller. The most important license obligations and risks are summarized in `THIRD_PARTY_NOTICES.md`, the current transitive dependency metadata snapshot is in `LICENSES/PYTHON_DEPENDENCIES.md`, high-attention package license files are collected under `LICENSES/THIRD_PARTY_LICENSES/`, high-attention bundled binary obligations are in `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md`, and the dated model-source review is in `LICENSES/MODEL_LICENSE_AUDIT.md`.

High-attention dependencies:

- `PySide6`: LGPL-3.0-only OR GPL options. Preserve Qt notices and allow users to replace/inspect LGPL-covered libraries where applicable.
- `pyvirtualcam`: package metadata/classifiers indicate GPLv2. Review compatibility with the AGPL-3.0 application before public binary distribution.
- `cv2_enumerate_cameras`: package metadata includes GPL-3.0 text. GPL-3.0 can be compatible with AGPL-3.0, but include notices and source availability.
- The CUDA build uses `onnxruntime-gpu`; the DirectML test build uses the mutually exclusive `onnxruntime-directml` package. TensorFlow, OpenCV, NumPy, PySide6, and either ONNX Runtime profile may bundle native DLLs with their own notices.
- `ffmpeg` is required for video processing. This installer does not bundle ffmpeg. If a future build bundles ffmpeg, record the exact build source and whether it is LGPL or GPL configured.
- Inno Setup is used as a release build tool and is not bundled as an application runtime dependency. Current JR Software pages request commercial users purchase a commercial license even though the Inno Setup License text permits broad use, including commercial applications. Confirm the publisher's Inno Setup licensing position before production/commercial distribution.

Before publishing a binary release, review `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` and decide how the release will satisfy LGPL/GPL-family obligations for bundled native components, especially Qt for Python/PySide6, shiboken6, easydict, cv2_enumerate_cameras, and pyvirtualcam.

## Installer distribution

The installer is per-user by default and installs under:

```text
%LOCALAPPDATA%\Programs\DeepLiveCamStudio\<version>
```

Downloaded models are stored outside the install directory:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

Uninstall removes application files and asks before deleting downloaded model files.

## Remaining legal risks

- The `inswapper` model family has historical non-commercial/research-use notices from InsightFace. A GPL-3.0 label on a Hugging Face mirror may not be sufficient for commercial redistribution.
- GPEN model mirrors are marked non-commercial/academic/educational and should not be bundled in a general-purpose release without permission.
- A PyInstaller single application directory can make LGPL/GPL compliance harder to reason about. Keep third-party notices and preserve replaceability/source-offer paths for LGPL components.
- Dependency metadata can be incomplete. Run a fresh dependency license scan immediately before each release.
- The current snapshot has at least one `UNKNOWN` license metadata entry (`namex`) and several dependencies with long license text rather than normalized SPDX identifiers; inspect upstream notices before publishing.
- Inno Setup commercial-license expectations should be reviewed by the release publisher before commercial production use.
