# Deep Live Cam Studio 2.1.5 Windows Release

This release packages a modified build of Deep-Live-Cam for Windows x64.

## Downloads

- Windows installer: `DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`
- Corresponding source archive: listed in the uploaded `RELEASE_ASSETS.md`
- Source archive SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and source `.zip.sha256` sidecar
- Source ref: listed in the uploaded `RELEASE_ASSETS.md` and source `.manifest.md`

## Source And License

Deep-Live-Cam is licensed under AGPL-3.0. This binary release is distributed with corresponding source availability requirements.

Attach the source archive listed above to the GitHub Release, or link the exact release tag/commit in the publishing repository. The public release must make the complete corresponding source available for the exact binary installer.

The source archive must be produced from the release Git ref with:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef HEAD
```

This release preserves attribution to the original project:

- Original project: https://github.com/hacksider/Deep-Live-Cam
- License: AGPL-3.0

## Models Are Not Bundled

The installer intentionally does not include model/checkpoint files (`.onnx`, `.pth`, `.safetensors`) because model licenses and redistribution rights are separate from the application license.

After installing, users can review model sources, license notes, and SHA-256 checksums before downloading:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

Downloaded models are stored under:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

## Notable Packaging Changes

- Windows x64 per-user installer using Inno Setup.
- PyInstaller onedir app bundle; Python does not need to be installed by users.
- Start menu shortcut and optional desktop shortcut.
- Clean uninstall of app files; user model data is preserved during silent uninstall and interactive uninstall asks before removing models.
- WebP and AVIF source-image upload support.
- Packaged runtime preflight and installer smoke tests are included under `build/windows`.

## Known Requirements

- ffmpeg/ffprobe must be installed separately for video workflows unless a future release explicitly bundles a reviewed ffmpeg build.
- NVIDIA GPU acceleration requires compatible NVIDIA drivers and runtime libraries. CPU fallback should be tested before publishing.
- OBS Virtual Camera workflows require OBS Studio installed separately.

## Compliance Notes

Review these files before publishing:

- `COMPLIANCE.md`
- `THIRD_PARTY_NOTICES.md`
- `LICENSES/PYTHON_DEPENDENCIES.md`
- `MODEL_DOWNLOAD_VERIFICATION.md`
- `PROCESSING_VERIFICATION.md`
- `RELEASE_CHECKLIST.md`
- `RELEASE_REPORT.md`

Known legal risks that must not be hidden from release notes:

- The `inswapper` model family has historical non-commercial/research-use restrictions from InsightFace even where mirrors are labeled GPL-3.0.
- GPEN upscaler model mirrors are marked non-commercial, academic, and educational use only.
- `pyvirtualcam` metadata reports GPLv2; review binary distribution compatibility.
- Dependency metadata can be incomplete and should be legally reviewed before public distribution.

## Pre-Publish Checks

This release candidate is not publish-approved by release notes alone; publish
approval is recorded in `RELEASE_VERIFICATION.md`, `MANUAL_RELEASE_GATES.md`,
and the signed gate documents included with the upload.

Completed local evidence is included in the uploaded release documents:

- Packaged runtime preflight.
- Installer smoke test.
- Model download/checksum verification.
- CPU fallback processing.
- CUDA processing on the local NVIDIA test machine.

Remaining publish blockers:

- None when `RELEASE_VERIFICATION.md` says `Ready to publish without remaining manual gates: YES`.

Completed manual signoffs include:

- Clean Windows VM install without admin rights.
- OBS Virtual Camera workflow.
- Authorized legal review for dependency, model-license, and redistribution obligations.
