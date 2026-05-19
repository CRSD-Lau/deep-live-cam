# OBS Virtual Camera Verification

Status: PENDING

This file records the manual OBS/virtual-camera release gate. Change `Status`
to `PASS` only after testing the final release candidate with OBS installed and
virtual camera support available. The release verifier only treats this file as
passed when `Status: PASS` is present and no unchecked `- [ ]` checklist rows
remain.

## Artifact Under Test

- Installer: `DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: copy from `DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`
- Source commit/tag: fill before publishing
- Tester:
- Date:
- Windows edition/build:
- OBS Studio version:
- Virtual camera backend/device:
- GPU/CPU mode tested:

## Required Checks

- [ ] `powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1 -RequireObsVirtualCam` passes on the OBS test machine.
- [ ] `tools/check_obs_virtualcam.py` sends frames to the selected virtual camera device.
- [ ] Deep-Live-Cam live preview opens and stops cleanly.
- [ ] Direct virtual-camera output is visible in a receiving app, or OBS captures the Deep-Live-Cam preview window and rebroadcasts it.
- [ ] OBS workflow matches `docs/OBS_VIRTUAL_CAMERA.md`.
- [ ] No bundled model/checkpoint files are required for the OBS smoke path.

## Evidence

Record command output, OBS settings, receiving app, screenshots, or tester notes
here.

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
