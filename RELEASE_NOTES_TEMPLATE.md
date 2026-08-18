# Deep Live Cam Studio 2.2.2 Windows Release

This maintenance release makes NVIDIA updates behave like a conventional app
upgrade, clarifies the DirectML portable update path, and ships the reviewed
Windows dependency patches merged since 2.2.1.

## Downloads

- NVIDIA/CUDA installer: `DeepLiveCamStudio-2.2.2-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.2.2-x64-setup.exe.sha256`
- AMD/Intel DirectML portable ZIP: {{DIRECTML_PORTABLE_NAME}}
- DirectML portable SHA-256: {{DIRECTML_PORTABLE_SHA256}}
- Corresponding source archive: listed in the uploaded `RELEASE_ASSETS.md`
- Source archive SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and source `.zip.sha256` sidecar
- Source ref: listed in the uploaded `RELEASE_ASSETS.md` and source `.manifest.md`

Use the CUDA installer for NVIDIA GPUs. Use the DirectML ZIP for AMD or Intel
DirectX 12 GPUs: extract it into a new folder and run
`DeepLiveCamStudio.exe`. Do not copy one runtime over another.

To update an NVIDIA installation, close Deep Live Cam Studio and run the new
setup EXE. It migrates earlier version-named installations into one stable
per-user directory while preserving downloaded models, settings, and logs.
DirectML remains portable: extract each update into a new folder and delete the
old extracted folder after verifying the new copy.

## What Changed

### Changed

- Standardized NVIDIA installs on
  `%LOCALAPPDATA%\Programs\DeepLiveCamStudio` instead of a version-named
  directory.
- Updated pip, wheel, PyInstaller, pip-tools, and Ruff in the deterministic
  Windows build and test toolchain.
- Documented the separate NVIDIA installer and DirectML portable update paths.

### Fixed

- The NVIDIA installer now removes the registered legacy installation and
  recognizable orphaned version folders before completing the stable upgrade.
- Installer tests now use an isolated app identity and validate a complete
  2.2.1-layout to 2.2.2 migration without disturbing real installations.
- Replaced the unavailable ONNX Runtime GPU 1.24.3 wheel with 1.24.4 and
  refreshed locks and licence evidence.

The unchanged DirectML application path was previously validated on Windows 11
with a Radeon RX 9060 XT: the DirectML badge was active and Preview,
short-video Render, and OBS Live Output all passed with no blocking regression.
The packaged release runtimes are separately checked for their expected GPU
providers; CUDA rendering and Live Output were also verified locally on an
NVIDIA RTX 4070.

## Source and license

Deep-Live-Cam is licensed under AGPL-3.0. Complete corresponding source for the
exact binary release is attached and identified by the source ref above.

The source archive is produced with:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.2 -GitRef HEAD
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
- Clean-install, legacy-upgrade, registry, shortcut, and uninstall checks.
- Model download/checksum and forbidden-model scans.
- CUDA and DirectML file-render checks.
- Radeon RX 9060 XT DirectML and NVIDIA RTX 4070 CUDA Live Output checks.

Remaining publish blockers:

- None when `RELEASE_VERIFICATION.md` says `Ready to publish without remaining manual gates: YES`.

Completed manual signoffs include:

- Clean Windows install without admin rights.
- OBS Virtual Camera and DirectML Live Output workflows.
- Authorized legal review for dependency, model-license, and redistribution obligations.
