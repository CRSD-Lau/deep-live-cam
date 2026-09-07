---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Report

Release: `2.2.4`

Status: PUBLISHED — PUBLIC DOWNLOADS VERIFIED

Remaining manual gates: None.

Published as the [latest stable v2.2.4](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.2.4) at 2026-09-07T01:55:44Z. [Public verification](docs/release-evidence/v2.2.4/candidate-617c733d/PUBLIC_RELEASE_VALIDATION.md) passed for all 47 fresh unauthenticated downloads and the annotated tag at the frozen source commit.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

The candidate contains export-integrity, Unicode-path, temporary-workspace,
settings, model-transfer and camera-lifecycle fixes. CUDA remains an Inno Setup
installer and DirectML a separate portable ZIP. The current scope and dependency
delta are described in [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md).

Use [RELEASE_PUBLISH_HANDOFF.md](RELEASE_PUBLISH_HANDOFF.md),
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) and
[RELEASE_SOURCE_PREP.md](RELEASE_SOURCE_PREP.md) for current commands and gates.
The [original 2.2.3 report](docs/release-evidence/v2.2.3/preparation/RELEASE_REPORT.md)
is retained unchanged; its old build commands and validation claims are historical.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.
The exact artifacts passed their automated checks, and Neil Mitchell has confirmed the remaining manual checks PASS. Keep `v2.2.3` available as rollback during the authorized publication.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.

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
$ReleaseCommit = '617c733d42a10a2fcba036385e19d66fabcc2cc1' # Frozen binary/source commit
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Python python -Accelerator DirectML
powershell -ExecutionPolicy Bypass -File build\windows\package_portable.ps1 -AppVersion 2.2.4 -Accelerator DirectML -SkipAcceleratorProbe
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.2.4 -Python python -GitRef $ReleaseCommit -AllowDirtySource
```

The hosted runner has no display adapter; actual GPU validation uses the downloaded
artifacts on identified local adapters. The final command regenerates build outputs
and is not a smoke test of already downloaded official bytes.

## Installer Output

The verified `DeepLiveCamStudio-2.2.4-x64-setup.exe` and its sidecar are attached to the published release with DirectML and exact corresponding source. The corrected installer passed actual same-version replacement, preserving seven user-data files and both backups. CUDA/DirectML real processing and CPU image fallback passed. GUI and clean-Windows checks are PASS as reported by Neil Mitchell; publication is complete and public downloads are verified.

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
dependency notices and model licence limitations accompany the release. Both [CUDA](docs/release-evidence/v2.2.4/candidate-617c733d/CUDA_COMPLIANCE_TECHNICAL.md) and [DirectML](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_COMPLIANCE_TECHNICAL.md) final payload inspections passed. All 77 tool notices match pinned upstream bytes, runtime inventories match their locks, and the earlier embedded-package notice gap is closed. Original historical verdicts are preserved.

## Remaining Legal Risks

Do not bundle without legal review: model/checkpoint weights or additional codec
binaries. Technical checks alone do not create publisher signoff; Neil Mitchell has now separately authorized publication in the owner confirmation. The
existing distribution posture and unresolved source/model limitations are recorded
in `LEGAL_REVIEW.md`, `COMPLIANCE.md` and the licence audits.

## Manual Checks Required Before Publishing

For future evidence updates, set `Status: PASS` only after the required checks
are complete and the evidence identifies who executed or reported each result.

The seven current-version manual checks are complete as reported by Neil Mitchell
in the linked owner confirmation: clean-Windows installation, interactive controls,
packaged Preview, physical-camera Live Output and independent receiving-application
behavior. Their gate documents now record `Status: PASS`. These manual results were
reported by the owner, not executed by the agent. Regenerate the strict summary and
complete the authorized publication procedure against the unchanged final artifacts.

## Completed automated candidate checks

The official workflow 34063403042 passed for both runtime profiles and exact corresponding source. All 36 original assets passed their checksum and structure checks; fresh draft-hosted downloads matched the verified runtime/source files.

The corrected installer ran successfully over the superseded 2.2.4 candidate. Seven user-data files totaling 1,558,270,376 bytes remained identical, with a verified backup and the earlier 2.2.3 upgrade evidence preserved. One stable registration and 30 required installed files were verified. Installed executable hashes are post-install measurements; no independent full-payload manifest was supplied.

Real CUDA and AMD device-1 DirectML image and silent/audio video processing passed, including Unicode output and failed-export preservation. CPU fallback passed its image-only checks. Existing model and executable hashes remained unchanged. The fresh five-model catalogue download and cancellation checks passed.

Both payload audits matched all 77 upstream tool notice files and every locked inventory row. The affected build-only Torch exception remains documented; runtime audits, critical lint, security checks and CodeQL passed. Local integration passed 744 tests; exact-source CI passed 742 with two platform skips.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.
