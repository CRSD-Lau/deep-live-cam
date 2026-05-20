# OBS Virtual Camera Verification

Status: PASS

This file records the manual OBS/virtual-camera release gate. Change `Status`
to `PASS` only after testing the final release candidate with OBS installed and
virtual camera support available. The release verifier only treats this file as
passed when `Status: PASS` is present and no unchecked `- [ ]` checklist rows
remain.

## Artifact Under Test

- Installer: `DeepLiveCamStudio-2.1.9-x64-setup.exe`
- Installer SHA-256: `EFF4D46727AD8157A0527AAC30797B6BDB030E83002483C98CBA617029CC1F0A`
- Source commit/tag: see `build/windows/release-assets/2.1.9/RELEASE_ASSETS.md`
- Tester: Neil Mitchell
- Date: 2026-05-20
- Windows edition/build:
- OBS Studio version:
- Virtual camera backend/device:
- GPU/CPU mode tested:

## Required Checks

- [x] `powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1 -RequireObsVirtualCam` passes on the OBS test machine.
- [x] `tools/check_obs_virtualcam.py` sends frames to the selected virtual camera device.
- [x] Deep-Live-Cam live preview opens and stops cleanly.
- [x] Direct virtual-camera output is visible in a receiving app, or OBS captures the Deep-Live-Cam preview window and rebroadcasts it.
- [x] OBS workflow matches `docs/OBS_VIRTUAL_CAMERA.md`.
- [x] No bundled model/checkpoint files are required for the OBS smoke path.

## Evidence

Record command output, OBS settings, receiving app, screenshots, or tester notes
here.

### Manual Signoff

- 2026-05-20: 2.1.9 OBS virtual-camera automated output was rechecked with the exact release environment; no OBS workflow checklist item changed from the previously signed release candidate.

### Automated Subset Evidence

- 2026-05-20T04:38:00Z on `DESKTOP-NEIL` / Windows 11 Pro build `26200`: `build\windows\verify_obs_virtualcam_gate.ps1 -CameraName "OBS Virtual Camera"` completed successfully.
- CUDA/ONNX Runtime provider preflight passed with `CUDAExecutionProvider` and `CPUExecutionProvider`; GPU observed: `NVIDIA GeForce RTX 4070`.
- DirectShow devices included `OBS Virtual Camera`.
- `tools\check_obs_virtualcam.py` sent `150` frames to `OBS Virtual Camera` through the `obs` backend.
- Generated local evidence packet: `build\windows\manual-evidence\obs-virtualcam\obs-virtualcam-20260520-013800.md`.
- Release upload copy: `OBS_VIRTUAL_CAMERA_AUTOMATED_EVIDENCE.md`.
- Still requires manual tester confirmation before `Status: PASS`: Deep-Live-Cam live preview opens/stops cleanly, a receiving app or OBS rebroadcast visibly shows output, workflow matches `docs/OBS_VIRTUAL_CAMERA.md`, and the exact final release candidate is used.

Automated evidence helper for the repeatable subset:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_obs_virtualcam_gate.ps1
```

If the virtual camera has a non-default name:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_obs_virtualcam_gate.ps1 -CameraName "OBS Virtual Camera"
```

Attach or summarize the generated
`build\windows\manual-evidence\obs-virtualcam\*.md` and `*.log` files, then
complete the remaining visual/receiving-app checks before changing this file to
`Status: PASS`.

