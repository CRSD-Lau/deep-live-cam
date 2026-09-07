---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Deep Live Cam Studio 2.2.4 Windows Release

Status: PUBLISHED — PUBLIC DOWNLOADS VERIFIED

Remaining manual gates: None.

Published as the [latest stable v2.2.4](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.2.4) at 2026-09-07T01:55:44Z. [Public verification](docs/release-evidence/v2.2.4/candidate-617c733d/PUBLIC_RELEASE_VALIDATION.md) passed for all 47 fresh unauthenticated downloads and the annotated tag at the frozen source commit.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.

Automated artifact checks passed. Neil Mitchell has reported all outstanding manual tests PASS and authorized publication; publication and public download verification are complete.
Binary and corresponding-source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`.
Later documentation/evidence commits do not change this artifact identity.

This patch release protects existing exports when rendering fails, isolates
temporary frames from user folders, and improves settings, model-transfer, and
camera lifecycle handling. It also tightens release source matching and rejects
stale verification evidence.

The first candidate was superseded for missing embedded-package notices. Its
tests and hashes are archived separately. Only the corrected assets and their
matching validation may be approved for publication.

## Downloads

- NVIDIA/CUDA installer: `DeepLiveCamStudio-2.2.4-x64-setup.exe`
- Installer SHA-256: listed in the uploaded `RELEASE_ASSETS.md` and `DeepLiveCamStudio-2.2.4-x64-setup.exe.sha256`
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

- Image exports, extracted frames and QA images use Unicode-safe file paths on
  Windows, preventing garbled filenames and unchanged exports reported as success.
- Image processors report write failures, and image/video publication replaces
  the destination only after staging succeeds. Failed processing or audio
  restoration preserves the previous export. Silent source videos remain valid.
- Video exports reject failed decoding and incomplete frames, handle short
  pipe reads, and prevent FFmpeg diagnostic output from blocking processing.
- Frame extraction uses private workspaces. Same-named inputs cannot share
  extracted frames, and cleanup never targets unrelated input-folder `temp`
  directories. Retained frame locations appear in the processing log.
- Invalid saved settings recover safely; interrupted settings writes preserve
  the previous file.
- Camera startup failures release their resources, and file rendering cannot
  overlap live output.
- Interrupted model downloads clean up partial files without replacing an
  existing model. Insecure redirects are rejected before they are followed.
- CLI resource validation rejects invalid values, requires both FFmpeg tools
  for video workflows, and returns failure status for unsuccessful renders.
- Packaging includes embedded pip/setuptools and vendor notices. The CUDA DLL-source
  helper uses the main locked pip, and only the isolated installer test fixture
  uses faster compression; public installer compression stays unchanged.
- Packaging also retains PyInstaller's licence and bootloader exception and the
  contributed hooks' licence; missing declared or recorded notices fail the build.
- Release builds pin both runtime profiles and corresponding source to one
  immutable commit. Verification rejects evidence for an earlier release.

The dependency changes since `v2.2.3` are PyInstaller hooks **2026.6 → 2026.7**
in both Windows package locks and Ruff **0.16.4 → 0.16.5** in development tools.
The ONNX Runtime versions and CUDA/DirectML inference dependencies remain at
their reviewed locks. The build-only PyTorch 2.11.0 advisory exception is
documented accurately: the wheel is affected, while the packaged application
excludes Torch/JIT Python code and uses only the reviewed CUDA/cuDNN DLLs.
See `docs/DEPENDENCY_LOCKS.md` for the exception's scope and limitations.

## Source and license

Deep-Live-Cam is licensed under AGPL-3.0. Complete corresponding source for the
exact binary release is attached and identified by the source ref above.

The asset assembler replaces HEAD below with the exact source-manifest SHA in
the generated release notes. Run this template command only from the frozen
clean release checkout:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.4 -GitRef HEAD
```

This release preserves attribution to the
[original project](https://github.com/hacksider/Deep-Live-Cam).

## Models are not bundled

The installer intentionally does not include model/checkpoint files. The
DirectML portable ZIP also excludes them because model licenses and
redistribution rights are separate from the application license.

After launching, select **Set Up Models**, or run:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

This consent flow downloads and verifies the model-manager inventory. Some
dependencies, including InsightFace's analysis models and optional NSFW
filtering, may download their own assets on first use; they are outside that
inventory and may use different cache locations.

The model-manager downloads are stored under:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

## Requirements and known limitations

- Install `ffmpeg` and `ffprobe` separately for video workflows.
- Install OBS Studio separately for OBS Virtual Camera workflows.
- The public files are unsigned and may trigger Microsoft Defender SmartScreen.
- Processed Preview FPS depends on the selected processors, models, content,
  and hardware; it may be lower than the source video's frame rate.
- Face-swap and enhancer model families retain their documented non-commercial
  or research-use restrictions; no model weights are redistributed here.

## Release evidence

This release candidate is not publish-approved by automated checks alone. Neil Mitchell has now confirmed all outstanding manual tests pass and authorized publication; the manual gate is closed.

Official workflow 34063403042 passed from the exact binary/source commit above. Local tests passed 744 cases; exact-source CI passed 742 with two platform skips. Both final runtime packages and corresponding source were freshly downloaded from the draft and matched the verified build bytes.

The corrected installer passed actual same-version replacement with unchanged models/settings and verified backups. CUDA and identified AMD DirectML image/video processing, CPU image fallback, Unicode output, failure preservation, catalogue downloads and both complete package-notice audits passed. The earlier first candidate is superseded and retained separately.

The isolated installer fixture compiled in 336.468 seconds versus 1,465.188 seconds for the public installer in this run; public ultra64 compression remains unchanged. Its prior-run fixture time was 1,542.828 seconds. This observed timing improvement is not a controlled cross-run benchmark.

Remaining publish blockers: None.

The seven manual items are PASS as reported by Neil Mitchell in the linked owner confirmation. The strict current-version summary, frozen tag, final manifest, publication and public download checks all passed. These publication actions are complete and verified.

`RELEASE_VALIDATION.md`, `RELEASE_VERIFICATION.md`, `MANUAL_RELEASE_GATES.md` and `LEGAL_REVIEW.md` contain current evidence and limits. Publication is complete and public downloads are verified; preserve `v2.2.3` as rollback.
