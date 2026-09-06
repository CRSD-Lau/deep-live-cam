---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Report

Release: `2.2.4`

Status: DRAFT — FINAL ARTIFACT AND MANUAL VERIFICATION PENDING

Binary/source commit: `753aab70c34ae585d525a06b9f7de2d721b7f491`

The candidate contains export-integrity, Unicode-path, temporary-workspace,
settings, model-transfer and camera-lifecycle fixes. CUDA remains an Inno Setup
installer and DirectML a separate portable ZIP. The current scope and dependency
delta are described in [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md).

Use [RELEASE_PUBLISH_HANDOFF.md](RELEASE_PUBLISH_HANDOFF.md),
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) and
[RELEASE_SOURCE_PREP.md](RELEASE_SOURCE_PREP.md) for current commands and gates.
The [original 2.2.3 report](docs/release-evidence/v2.2.3/preparation/RELEASE_REPORT.md)
is retained unchanged; its old build commands and validation claims are historical.

Final artifact hashes, licence inventories, processing/installer evidence and
publication status belong in the reviewed asset attestations. This draft report
does not mark any pending check as passed. Keep `v2.2.3` available as rollback.

## Packaging Approach

The NVIDIA profile is a PyInstaller onedir application bundle wrapped by Inno Setup.
The DirectML profile packages a separate onedir bundle as a portable ZIP. Both
runtime jobs and the corresponding-source archive use the immutable commit above.

## Files Changed For Packaging And Compliance

The workflow now resolves source once and verifies the application version.
`run_release_checks.ps1` and `package_installer.ps1` prefer the actual build
environment when generating licence inventories. Release validators require
current-version manual evidence. Post-build documentation records what was tested
without altering frozen runtime or source bytes.

## Build Commands

The official workflow uses the following build-stage commands in its clean checkout:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Python python -Accelerator DirectML
powershell -ExecutionPolicy Bypass -File build\windows\package_portable.ps1 -AppVersion 2.2.4 -Accelerator DirectML -SkipAcceleratorProbe
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.2.4 -Python python -GitRef 753aab70c34ae585d525a06b9f7de2d721b7f491 -AllowDirtySource
```

The hosted runner has no display adapter; actual GPU validation uses the downloaded
artifacts on identified local adapters. The final command regenerates build outputs
and is not a smoke test of already downloaded official bytes.

## Installer Output

Expected output is `DeepLiveCamStudio-2.2.4-x64-setup.exe`, with a SHA-256 sidecar.
The matching DirectML ZIP, corresponding-source archive and complete checksum
manifest belong in the existing draft. Final CUDA and upgrade checks are pending.

## Dependencies Bundled

Python, Qt/PySide6, OpenCV, TensorFlow, ONNX Runtime and the reviewed runtime
dependencies are collected with licence metadata. CUDA additionally includes the
allow-listed CUDA/cuDNN DLLs from the build-only Torch wheel. DirectML contains its
own provider DLLs. Exact inventories accompany the final artifact set.

## Dependencies Not Bundled

FFmpeg/ffprobe remain external prerequisites. Torch/JIT Python code and the full
CUDA Toolkit are excluded from the runtime; the existing scoped Torch advisory
exception remains documented in `docs/DEPENDENCY_LOCKS.md`.

## Model Files

Bundled model files: none. The application catalogue is installed separately with
`DeepLiveCamStudioCLI.exe --download-models` or Set Up Models, after consent, into
`%LOCALAPPDATA%\DeepLiveCamStudio\models`. Dependency-managed InsightFace analysis
and optional OpenNSFW2 downloads remain outside that explicit catalogue.

## License Obligations Found

Deep-Live-Cam is AGPL-3.0; the exact corresponding source, original attribution,
dependency notices and model licence limitations accompany the release. The
[DirectML technical inspection](docs/release-evidence/v2.2.4/DIRECTML_COMPLIANCE_TECHNICAL.md)
records actual Qt metadata and the existing shared LGPL/GPL text locations.

## Remaining Legal Risks

Do not bundle without legal review: model/checkpoint weights or additional codec
binaries. Current technical checks do not create a new publisher signoff. The
existing distribution posture and unresolved source/model limitations are recorded
in `LEGAL_REVIEW.md`, `COMPLIANCE.md` and the licence audits.

## Manual Checks Required Before Publishing

For each current-version manual gate, set `Status: PASS` only after its required
checks are complete and supported by evidence. Clean-Windows installation,
interactive controls, packaged Preview, physical-camera and receiving-application
Live Output checks remain pending. Keep the release draft until the strict manual
summary and final artifact checks pass.
