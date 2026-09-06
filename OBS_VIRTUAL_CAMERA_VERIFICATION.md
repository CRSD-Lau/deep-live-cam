---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# OBS Virtual Camera Verification

Status: PENDING

Release: `2.2.4`

Candidate source: `753aab70c34ae585d525a06b9f7de2d721b7f491`

## Completed synthetic source-component subset

- [x] Start the source `runtime.virtual_cam.VirtualCameraSink` with the existing
  OBS backend at 1280x720 and 30 FPS.
- [x] Receive changing generated colors through an independent FFmpeg
  DirectShow process explicitly selecting `OBS Virtual Camera`.
- [x] Stop the first sink, reacquire with a fresh sink, and repeat the receiver check.
- [x] Confirm both owned receiver processes exited and OBS remained closed.

Each cycle received 120 frames. All 240 received frames matched the two
expected synthetic colors within the documented conversion tolerance; each
cycle observed eight color transitions. The first cycle's color counts were
62/58; the second cycle's were 60/60.

Evidence: `.tmp/release-2.2.4/obs-subset/EVIDENCE.md`, `evidence.json`, and
`cleanup.json`. These record exact source identity, receiver metrics, and raw
sample hashes. No physical webcam, GPU inference, GUI, or packaged application
was used. OBS absence was checked immediately before each start; no user app
was stopped or reconfigured.

## Outstanding final-application checks

- [ ] Verify the final CUDA runtime on the identified NVIDIA adapter; the
  official DirectML CLI has already passed on the recorded AMD device index 1.
- [ ] Check processed Preview and Live Output start, stop, restart, and failed
  physical-camera startup through each final packaged GUI.
- [ ] Confirm actual file rendering and live processing cannot overlap in the GUI.
- [ ] Confirm final packaged processed Live Output appears in a receiving application.
- [ ] Confirm the application workflow still matches `docs/OBS_VIRTUAL_CAMERA.md`.

The source sender-to-receiver subset proves native virtual-camera delivery and
reacquisition, not the complete packaged camera/face-processing/GUI workflow.
Historical NVIDIA/AMD signoff in
`docs/release-evidence/v2.2.3/OBS_VIRTUAL_CAMERA_VERIFICATION.md` remains historical.
