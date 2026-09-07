---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Owner confirmation of 2.2.4 manual verification

Status: PASS — reported by Neil Mitchell

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

After receiving the outstanding manual checklist, Neil Mitchell confirmed:

> All tests pass release

This confirmation covers the seven outstanding checklist items below and
authorizes publication of the corrected, already tested 2.2.4 draft. The manual
results are owner-reported. Codex did not independently perform or observe these
manual tests; no device details, screenshots, timings or new automated execution
are implied by this attestation.

| Gate document | Owner-confirmed manual check | Result |
| --- | --- | --- |
| CLEAN_VM_VERIFICATION.md | Final installer on clean Windows: fresh install, 2.2.3 upgrade, no elevation and shortcut launch | PASS |
| CLEAN_VM_VERIFICATION.md | GUI model consent, missing-model behavior and interactive uninstall choices | PASS |
| OBS_VIRTUAL_CAMERA_VERIFICATION.md | Packaged Preview and physical-camera Live Output start, stop, restart and failed startup | PASS |
| OBS_VIRTUAL_CAMERA_VERIFICATION.md | File rendering and live processing cannot overlap through the final GUIs | PASS |
| OBS_VIRTUAL_CAMERA_VERIFICATION.md | Processed Live Output reaches an independent receiving application | PASS |
| OBS_VIRTUAL_CAMERA_VERIFICATION.md | Final workflow matches docs/OBS_VIRTUAL_CAMERA.md | PASS |
| PROCESSING_VERIFICATION.md | Processed Preview start, seek and close in both final CUDA and DirectML GUIs | PASS |

## Exact artifacts covered

| Artifact | SHA-256 |
| --- | --- |
| DeepLiveCamStudio-2.2.4-x64-setup.exe | `d91080bef32a6bb731830599bfda90eeca4844d20af6d34e67957c0bda2b48bf` |
| DeepLiveCamStudio-2.2.4-DirectML-x64-portable.zip | `f6b077f0364bb523e75ec7950b096d62763a5b4aa2de181d0eaffa47f9bf6f04` |
| DeepLiveCamStudio-2.2.4-source-617c733d42a1.zip | `ec59a3be3ffc4b4b58baafbc4fd4867ceeedea3fa66e3d86038dcb4dc4af7f8e` |

These remain the bytes from [official workflow 34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
This post-build attestation does not retarget or rebuild either runtime or the
corresponding source archive. Their original sidecars and source manifest remain
unchanged. The annotated release tag must resolve to the same binary/source commit.

## Evidence chronology

[RELEASE_VALIDATION.md](RELEASE_VALIDATION.md) and its companion JSON preserve the
earlier automated verification and its then-pending manual status. Those reports
remain unchanged. This later owner confirmation closes their manual gates; it
does not expand the measured scope of any earlier automated test.

Legal/model restrictions, the build-only PyTorch advisory exception, unsigned
Windows files and the documented runtime limitations remain applicable. Existing
model/settings preservation and rollback receipts remain available separately.

Publication is authorized. Hosted checks, exact asset validation and the frozen
tag must pass before publication; public download verification follows publication.
