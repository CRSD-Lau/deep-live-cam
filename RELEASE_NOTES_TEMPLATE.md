---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-10-25
---

# Deep Live Cam Studio 2.2.5 Windows Release Candidate

Status: PENDING

This release candidate is not publish-approved. Automated build and runtime
checks are evidence for the exact candidate; manual publication gates remain open.

## Downloads

- NVIDIA/CUDA installer: `DeepLiveCamStudio-2.2.5-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.2.5-x64-setup.exe.sha256`
- AMD/Intel DirectML portable ZIP: {{DIRECTML_PORTABLE_NAME}}
- DirectML portable SHA-256: {{DIRECTML_PORTABLE_SHA256}}
- Corresponding source archive: listed in the uploaded `RELEASE_ASSETS.md`
- Source archive SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and source `.zip.sha256` sidecar
- Source ref: listed in the uploaded `RELEASE_ASSETS.md` and source `.manifest.md`

Use the CUDA installer for NVIDIA GPUs. Extract DirectML into a new folder for
AMD/Intel DirectX 12 GPUs. Preserve current models, settings and logs before an
upgrade. Do not overlay one runtime profile onto another.

## Security changes

- Pillow 13.0.0 fixes the image-decoder advisories affecting 12.3.0.
- Setuptools 84.1.0 fixes its Windows namespace-installation path escape.
- Certifi 2026.10.23 updates the trust store; filelock 4.2.4 fixes locking issues.
- Pip and its vendored runtime code are excluded from both executable archives.
- Full dependency licence texts and current-profile inventories are included.

## Source and license

Deep-Live-Cam is licensed under AGPL-3.0. The exact corresponding source archive,
commit and hashes are listed above. Original project attribution is preserved.

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.5 -GitRef HEAD
```

The installer intentionally does not include model/checkpoint files. Models
require separate consent and retain their own redistribution/use restrictions.
Run `DeepLiveCamStudioCLI.exe --download-models` only after reviewing that consent.
The isolated CUDA DLL source retains the documented Torch JIT reachability
exception; Torch Python code is excluded from the application.

## Release evidence

Current evidence is recorded in `RELEASE_VERIFICATION.md`, `MANUAL_RELEASE_GATES.md`
and `LEGAL_REVIEW.md`. Prior 2.2.4 attestations do not approve these new artifacts.

Remaining publish blockers:

- Exact rebuilt CUDA/DirectML artifact hashes, source and notice verification.
- Supported-hardware processing, model download/consent and interactive Preview.
- Clean-Windows installation/upgrade and an independent OBS camera receiver.
- Current legal review, strict publish-readiness checks and owner authorization.

These gates remain pending until the exact candidate evidence closes them.
