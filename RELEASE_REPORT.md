# Windows Release Report

Release: `2.2.0`

## Packaging Approach

The NVIDIA distribution is a PyInstaller onedir application bundle wrapped by Inno Setup.
AMD and Intel systems use a separately built PyInstaller DirectML
bundle distributed as a versioned portable ZIP. Keeping CUDA and DirectML
separate prevents mutually exclusive ONNX Runtime packages from contaminating
one environment.

## Files Changed For Packaging And Compliance

- Added `requirements-directml.txt`, DirectML provider selection, adapter
  choice, and the CPU face-analysis compatibility path.
- Added `build/windows/package_portable.ps1` and combined release CI.
- Added strict portable ZIP, hidden-runtime, hash, and model-exclusion checks.
- Updated version metadata, README, DirectML guide, changelog, release notes,
  source preparation, checklist, handoff, and gate evidence.

## Build Commands

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Accelerator Cuda
powershell -ExecutionPolicy Bypass -File build\windows\package_installer.ps1 -AppVersion 2.2.0
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Accelerator DirectML
powershell -ExecutionPolicy Bypass -File build\windows\package_portable.ps1 -AppVersion 2.2.0 -Accelerator DirectML
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.0 -GitRef v2.2.0
```

## Installer Output

- `DeepLiveCamStudio-2.2.0-x64-setup.exe`
- `DeepLiveCamStudio-2.2.0-DirectML-x64-portable.zip`
- matching SHA-256 sidecars
- exact source ZIP, source SHA-256, and source manifest

Final hashes are recorded in `RELEASE_ASSETS.md` and `SHA256SUMS.txt` rather
than embedded in installed documents.

## Dependencies Bundled

Each runtime includes Python 3.11, PySide6, OpenCV, InsightFace support,
TensorFlow/opennsfw2, application dependencies, and one ONNX Runtime profile:
`onnxruntime-gpu` for CUDA or `onnxruntime-directml` for DirectML. Required
third-party licence files are copied into `LICENSES/THIRD_PARTY_LICENSES/`.

## Dependencies Not Bundled

- ffmpeg/ffprobe
- OBS Studio and OBS Virtual Camera
- GPU display drivers
- paid Authenticode trust/reputation
- model/checkpoint weights

Do not bundle without legal review any new external binary, media codec, model
weight, or dependency whose redistribution terms have not been captured.

## Model Files

Bundled model files: none.

Users review sources, licence notes, and checksums before running
`DeepLiveCamStudioCLI.exe --download-models`. Downloaded files are stored under
`%LOCALAPPDATA%\DeepLiveCamStudio\models`.

## License Obligations Found

Deep-Live-Cam is AGPL-3.0, so the exact complete corresponding source is
published beside the binary assets. Qt/PySide, ONNX Runtime, OpenCV,
TensorFlow, pyvirtualcam, cv2_enumerate_cameras, and other dependency notices
remain in the bundled licence inventory. Model licences remain separate from
the application licence.

## Remaining Legal Risks

- InsightFace/inswapper and GPEN-family model use has non-commercial or
  research-use limitations.
- GPL/LGPL-family dependency combinations and the publisher's Inno Setup use
  remain subject to the accepted project-owner review.
- The project does not provide legal advice; distributors must assess their
  own intended use.

## Manual Checks Required Before Publishing

The clean-install, OBS/Live Output, and legal/compliance gate files must each
set `Status: PASS` only after the documented checks and delta review are
complete. Final publication also requires public-download digest and runtime
verification for both CUDA and DirectML assets.
