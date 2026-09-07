---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# OBS Virtual Camera Verification

Status: PASS

Publication status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Publication is authorized by Neil Mitchell and pending actual publication.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.


Release: `2.2.4`

Candidate source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Workflow: [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [x] Verify final CUDA and identified AMD DirectML providers and real processing.
- [x] Check packaged Preview and physical-camera Live Output start, stop, restart and failed startup. — PASS reported by Neil Mitchell.
- [x] Confirm file rendering and live processing cannot overlap through the final GUIs. — PASS reported by Neil Mitchell.
- [x] Confirm actual processed Live Output reaches an independent receiving application. — PASS reported by Neil Mitchell.
- [x] Confirm the final workflow matches docs/OBS_VIRTUAL_CAMERA.md. — PASS reported by Neil Mitchell.

The archived source-component test delivered 240 changing synthetic frames through
the actual OBS Virtual Camera driver across two start/stop cycles. No physical
webcam, GPU inference or packaged GUI was used in that test. Retain its useful
delivery/reacquisition evidence without calling it complete application approval.
