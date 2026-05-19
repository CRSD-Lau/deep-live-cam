# Deep Live Cam Studio {VERSION} Windows Release

This release packages a modified build of Deep-Live-Cam for Windows x64.

## Downloads

- Windows installer: `DeepLiveCamStudio-{VERSION}-x64-setup.exe`
- Installer SHA-256: see `DeepLiveCamStudio-{VERSION}-x64-setup.exe.sha256`
- Corresponding source archive: attach the source archive for the exact commit used to build this installer, or link the exact Git tag/commit.

## Source And License

Deep-Live-Cam is licensed under AGPL-3.0. This binary release is distributed with corresponding source availability requirements.

Before publishing, replace this paragraph with the exact source tag/commit URL and attach or link the source archive produced by:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion {VERSION} -GitRef <release-tag-or-commit>
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

- Clean Windows VM install without admin rights.
- Packaged runtime preflight.
- Installer smoke test.
- CPU fallback processing.
- CUDA processing.
- OBS Virtual Camera workflow.
- Final dependency and model-license review.
