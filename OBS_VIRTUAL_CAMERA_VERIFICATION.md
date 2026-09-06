---
author: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# OBS Virtual Camera Verification

Status: PENDING

Release: `2.2.4`

Historical NVIDIA/AMD confirmations remain in
`docs/release-evidence/v2.2.3/OBS_VIRTUAL_CAMERA_VERIFICATION.md`.
This patch changes camera failure cleanup and file/live operation exclusion,
so historical live-output results alone cannot close this release gate.

## Current release checks

- [ ] Verify the final CUDA and DirectML runtimes on identified adapters.
- [ ] Check Preview and Live Output start, stop, restart and failed camera startup.
- [ ] Confirm file rendering and live processing cannot overlap.
- [ ] Confirm processed Live Output appears in a receiving application.
- [ ] Confirm the workflow still matches `docs/OBS_VIRTUAL_CAMERA.md`.

The synthetic sender in `verify_obs_virtualcam_gate.ps1` verifies an automated
subset. It does not by itself establish final-application processing or receiver
visibility. Record receiver evidence and the actual adapter used separately.
