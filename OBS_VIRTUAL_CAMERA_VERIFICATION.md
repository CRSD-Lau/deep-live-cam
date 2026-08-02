# OBS Virtual Camera Verification

Status: PASS

Release: `2.2.0`

## Required checks

- [x] OBS Virtual Camera is detected by the Windows environment check.
- [x] Test frames can be sent to the selected virtual camera device.
- [x] Deep Live Cam Preview opens and stops cleanly.
- [x] Live Output is visible in a receiving application.
- [x] The workflow matches `docs/OBS_VIRTUAL_CAMERA.md`.
- [x] CUDA and DirectML paths do not require bundled model/checkpoint files.

## Evidence

- NVIDIA/CUDA: Neil Mitchell confirmed Preview, file rendering, and the normal
  OBS/Live Output workflow on an NVIDIA RTX 4070.
- AMD/DirectML: GitHub user `@d1stru3t0r` confirmed “It works now, tested live
  too” on a Radeon 6900 XT after testing the final DirectML runtime fix.
- Reporter evidence:
  https://github.com/CRSD-Lau/deep-live-cam/issues/3#issuecomment-5160009203
- The automated OBS gate previously sent 150 frames through the `obs` backend
  to `OBS Virtual Camera`; the virtual-camera implementation is unchanged in
  `2.2.0`.
- Final publication still verifies both downloadable runtime assets and their
  provider checks before the release is made public.

Repeat the local OBS gate with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_obs_virtualcam_gate.ps1 -CameraName "OBS Virtual Camera"
```
