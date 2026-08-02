# Deep Live Cam Studio 2.2.0 Windows Release

This release adds a verified DirectML build for AMD and Intel GPUs and fixes a
file Preview/Render deadlock that could also affect CUDA systems.

## Downloads

- NVIDIA/CUDA installer: `DeepLiveCamStudio-2.2.0-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.2.0-x64-setup.exe.sha256`
- AMD/Intel DirectML portable ZIP: {{DIRECTML_PORTABLE_NAME}}
- DirectML portable SHA-256: {{DIRECTML_PORTABLE_SHA256}}
- Corresponding source archive: listed in the uploaded `RELEASE_ASSETS.md`
- Source archive SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and source `.zip.sha256` sidecar
- Source ref: listed in the uploaded `RELEASE_ASSETS.md` and source `.manifest.md`

Use the CUDA installer for NVIDIA GPUs. Use the DirectML ZIP for AMD or Intel
DirectX 12 GPUs: extract it into a new folder and run
`DeepLiveCamStudio.exe`. Do not copy one runtime over another.

## What Changed

### Added

- DirectML GPU acceleration for AMD and Intel GPUs, including strict provider
  verification and multi-GPU adapter selection.
- A versioned DirectML portable ZIP with a SHA-256 sidecar and release-time
  archive validation.

### Fixed

- Preview and Start Render can no longer re-enter while the first file
  operation is loading models, preventing the observed Not Responding
  deadlock.
- DirectML face analysis uses the CPU compatibility path while swap and
  enhancement inference remain on the GPU, avoiding Radeon multi-session
  hangs.
- GitHub packaging now preserves dot-prefixed runtime directories, including
  the scikit-learn `.libs` DLL required by the application.
- Clean NVIDIA installer builds now include the pinned CUDA 12/cuDNN 9 runtime
  DLL set required for an actual ONNX Runtime CUDA session.
- Provider diagnostics fail clearly when requested GPU acceleration is not
  active instead of silently treating CPU fallback as success.

The DirectML fix was validated by the issue reporter on a Radeon 6900 XT for
file rendering and Live Output. The packaged release runtimes were separately
checked for their expected GPU providers. CUDA rendering and Live Output were
also verified locally on an NVIDIA RTX 4070.

## Source and license

Deep-Live-Cam is licensed under AGPL-3.0. Complete corresponding source for the
exact binary release is attached and identified by the source ref above.

The source archive is produced with:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.0 -GitRef HEAD
```

This release preserves attribution to the original project:

- Original project: https://github.com/hacksider/Deep-Live-Cam
- License: AGPL-3.0

## Models are not bundled

The installer intentionally does not include model/checkpoint files. The
DirectML portable ZIP also excludes them because model licenses and
redistribution rights are separate from the application license.

After launching, select **Set Up Models**, or run:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

Downloaded models are stored under:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

## Requirements and known limitations

- `ffmpeg` and `ffprobe` must be installed separately for video workflows.
- OBS Studio must be installed separately for OBS Virtual Camera workflows.
- The public files are unsigned and may trigger Microsoft Defender
  SmartScreen.
- Face-swap and enhancer model families retain their documented
  non-commercial or research-use restrictions; no model weights are
  redistributed here.

## Release evidence

This release candidate is not publish-approved by release notes alone;
publish approval is recorded in `RELEASE_VERIFICATION.md`,
`MANUAL_RELEASE_GATES.md`, and the signed gate documents included with the
upload.

Completed local evidence is included in the uploaded release documents:

- Full automated test suite.
- Packaged CUDA and DirectML runtime/provider checks.
- Installer smoke install/uninstall checks.
- Model download/checksum and forbidden-model scans.
- CUDA and DirectML file-render checks.
- Radeon 6900 XT and NVIDIA RTX 4070 Live Output checks.

Remaining publish blockers:

- None when `RELEASE_VERIFICATION.md` says `Ready to publish without remaining manual gates: YES`.

Completed manual signoffs include:

- Clean Windows install without admin rights.
- OBS Virtual Camera and DirectML Live Output workflows.
- Authorized legal review for dependency, model-license, and redistribution obligations.
