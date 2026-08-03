# Deep Live Cam Studio 2.2.1 Windows Release

This maintenance release modernizes the Windows dependency set, hardens the
release process, and safely refactors the UI/frame pipeline while preserving
the CUDA and DirectML workflows introduced in 2.2.0.

## Downloads

- NVIDIA/CUDA installer: `DeepLiveCamStudio-2.2.1-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.2.1-x64-setup.exe.sha256`
- AMD/Intel DirectML portable ZIP: {{DIRECTML_PORTABLE_NAME}}
- DirectML portable SHA-256: {{DIRECTML_PORTABLE_SHA256}}
- Corresponding source archive: listed in the uploaded `RELEASE_ASSETS.md`
- Source archive SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and source `.zip.sha256` sidecar
- Source ref: listed in the uploaded `RELEASE_ASSETS.md` and source `.manifest.md`

Use the CUDA installer for NVIDIA GPUs. Use the DirectML ZIP for AMD or Intel
DirectX 12 GPUs: extract it into a new folder and run
`DeepLiveCamStudio.exe`. Do not copy one runtime over another.

## What Changed

### Changed

- Refreshed the reviewed Windows dependency set and regenerated reproducible
  CUDA and DirectML locks plus licence snapshots.
- Refactored high-complexity UI and frame-pipeline orchestration behind
  characterization tests while preserving user-visible behavior.
- Modernized the repository README, documentation, issue forms, support and
  security policies, dependency policy, and public project presentation.

### Fixed

- Removed stale release triggers, obsolete duplicate tooling, unused imports,
  and retired scaffolding without changing supported workflows.
- Kept strict provider checks so CPU fallback cannot be mistaken for a
  successful CUDA or DirectML result.

An independent physical tester validated the release candidate on Windows 11
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
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.1 -GitRef HEAD
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
- Radeon RX 9060 XT DirectML and NVIDIA RTX 4070 CUDA Live Output checks.

Remaining publish blockers:

- None when `RELEASE_VERIFICATION.md` says `Ready to publish without remaining manual gates: YES`.

Completed manual signoffs include:

- Clean Windows install without admin rights.
- OBS Virtual Camera and DirectML Live Output workflows.
- Authorized legal review for dependency, model-license, and redistribution obligations.
