---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# OBS Virtual Camera Verification

Status: PENDING

Release: `2.2.4`

Candidate source: PENDING — record the corrected immutable build SHA and asset hashes.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [ ] Verify final CUDA and identified AMD DirectML providers and real processing.
- [ ] Check packaged Preview and physical-camera Live Output start, stop, restart and failed startup.
- [ ] Confirm file rendering and live processing cannot overlap through the final GUIs.
- [ ] Confirm actual processed Live Output reaches an independent receiving application.
- [ ] Confirm the final workflow matches docs/OBS_VIRTUAL_CAMERA.md.

The archived source-component test delivered 240 changing synthetic frames through
the actual OBS Virtual Camera driver across two start/stop cycles. No physical
webcam, GPU inference or packaged GUI was used in that test. Retain its useful
delivery/reacquisition evidence without calling it complete application approval.
