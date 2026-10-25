---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-10-25
---

# Windows Release Report

Release: `2.2.5`

Status: PENDING

Publication status: NOT APPROVED

This is the 2.2.5 security release candidate. The [archived 2.2.4 receipt](docs/release-evidence/v2.2.4/final-attestations/RELEASE_REPORT.md) applies only to its original artifacts.

## Packaging Approach

PyInstaller onedir application bundle wrapped by Inno Setup. CUDA installer and DirectML portable archive use one immutable source commit.

## Files Changed For Packaging And Compliance

Pillow 12.3.0 to 13.0.0, setuptools 83.0.0 to 84.1.0, regenerated hash locks, aligned 2.2.5 defaults, and fresh release gates.

## Build Commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\update_dependency_locks.ps1 -Check
# Run Windows Release Candidate Build with app_version=2.2.5 and git_ref=<immutable SHA>.
```

## Installer Output

Expected `DeepLiveCamStudio-2.2.5-x64-setup.exe` and DirectML portable ZIP; build, SHA-256, exact source, and runtime verification pending.

## Dependencies Bundled

Separate hash-locked CUDA and DirectML profiles. Packaging generates fresh dependency inventories and third-party notices from each build environment. Verify Pillow 13.0.0 and setuptools 84.1.0 in the final payload inventories.

## Dependencies Not Bundled

Torch Python/JIT packages are excluded; only the reviewed CUDA/cuDNN DLL allowlist is copied from the isolated helper. External OBS camera transport and hardware drivers require their own verification.

## Model Files

Bundled model files: none. Download only after consent with `DeepLiveCamStudioCLI.exe --download-models`. User models belong under `%LOCALAPPDATA%\DeepLiveCamStudio\models`.

## License Obligations Found

Deep-Live-Cam is AGPL-3.0. Preserve corresponding source, attribution, Qt notices, dependency/vendor licences, and CUDA provenance. Do not bundle without legal review any restricted third-party model weights.

## Remaining Legal Risks

Fresh inventory review and exact final artifact/source inspection remain pending. Previous release approval does not apply to this candidate.

## Manual Checks Required Before Publishing

Complete the active clean-Windows, OBS, legal, model-download, and processing gate documents; set `Status: PASS` only after current artifact evidence establishes every item. No publication is approved by this report.
