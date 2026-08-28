# Deep Live Cam Studio 2.2.3 Windows Release

This patch release fixes processed video Preview autoplay and playback. Preview
now starts without manual timeline scrubbing, keeps a stable window size, and
shows processed frames in order at the hardware's achievable processing rate.

## Downloads

- NVIDIA/CUDA installer: `DeepLiveCamStudio-2.2.3-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.2.3-x64-setup.exe.sha256`
- AMD/Intel DirectML portable ZIP: {{DIRECTML_PORTABLE_NAME}}
- DirectML portable SHA-256: {{DIRECTML_PORTABLE_SHA256}}
- Corresponding source archive: listed in the uploaded `RELEASE_ASSETS.md`
- Source archive SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and source `.zip.sha256` sidecar
- Source ref: listed in the uploaded `RELEASE_ASSETS.md` and source `.manifest.md`

Use the CUDA installer for NVIDIA GPUs. Use the DirectML ZIP for AMD or Intel
DirectX 12 GPUs: extract it into a new folder and run
`DeepLiveCamStudio.exe`. Do not copy one runtime over another.

To update an NVIDIA installation, close Deep Live Cam Studio and run the new
setup EXE. It migrates earlier version-named installations into one stable
per-user directory while preserving downloaded models, settings, and logs.
DirectML remains portable: extract each update into a new folder and delete the
old extracted folder after verifying the new copy.

## What Changed

### Changed

- Processed target-video Preview starts automatically and includes Play, Pause,
  and responsive timeline seeking.
- Preview reuses one decoder and requests the next frame only after the current
  processed frame is displayed. Slower hardware therefore shows every frame in
  order at its achievable processing rate instead of skipping ahead.

### Fixed

- Prevented the Preview window from growing on each displayed frame.
- Removed per-frame decoder reopen/seek overhead and unnecessary temporal-state
  resets during sequential playback.
- Hardened Preview shutdown, worker-error retry, idle-timer restart, missing
  frame-count metadata, and file/live-preview mutual exclusion.

The core Preview fix was physically tested on Windows with a Radeon RX 6900 XT:
autoplay, stable window size, smoother sequential playback without skipped
frames, Pause/Play, seeking, and responsive close all passed. The tester also
noted low achieved FPS; that is recorded as a separate processing-throughput
observation, not interpreted as a 30 FPS cap. This release does not promise
real-time source-rate Preview when face processing is expensive.

The CUDA/DirectML dependency sets, installer behavior, model policy, and OBS
Live Output implementation are unchanged from 2.2.2. Final release assets are
still checked separately for their expected GPU providers before publication.

## Source and license

Deep-Live-Cam is licensed under AGPL-3.0. Complete corresponding source for the
exact binary release is attached and identified by the source ref above.

The source archive is produced with:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.3 -GitRef HEAD
```

This release preserves attribution to the original project:

- Original project: https://github.com/hacksider/Deep-Live-Cam
- License: AGPL-3.0

## Models are not bundled

The installer intentionally does not include model/checkpoint files. The
DirectML portable ZIP also excludes them because model licenses and
redistribution rights are separate from the application license.

After launching, select **Set Up Models**, or run:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

Downloaded models are stored under:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

## Requirements and known limitations

- `ffmpeg` and `ffprobe` must be installed separately for video workflows.
- OBS Studio must be installed separately for OBS Virtual Camera workflows.
- The public files are unsigned and may trigger Microsoft Defender
  SmartScreen.
- Processed Preview FPS depends on the selected processors, models, source
  content, and hardware; it may be lower than the source video's frame rate.
- Face-swap and enhancer model families retain their documented
  non-commercial or research-use restrictions; no model weights are
  redistributed here.

## Release evidence

This release candidate is not publish-approved by release notes alone;
publish approval is recorded in `RELEASE_VERIFICATION.md`,
`MANUAL_RELEASE_GATES.md`, and the signed gate documents included with the
upload.

Completed local evidence is included in the uploaded release documents:

- Full automated test suite.
- Packaged CUDA and DirectML runtime/provider checks.
- Clean-install, legacy-upgrade, registry, shortcut, and uninstall checks.
- Model download/checksum and forbidden-model scans.
- CUDA and DirectML file-render checks.
- Radeon RX 6900 XT DirectML Preview autoplay and playback checks.
- Existing Radeon RX 9060 XT DirectML and NVIDIA RTX 4070 CUDA Live Output
  checks; the Live Output implementation is unchanged in this patch.

Remaining publish blockers:

- None when `RELEASE_VERIFICATION.md` says `Ready to publish without remaining manual gates: YES`.

Completed manual signoffs include:

- Clean Windows install without admin rights.
- OBS Virtual Camera and DirectML Live Output workflows.
- Authorized legal review for dependency, model-license, and redistribution obligations.
