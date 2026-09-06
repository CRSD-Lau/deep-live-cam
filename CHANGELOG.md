# Changelog

All notable changes to this Windows Studio distribution are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases use [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.2.4] - 2026-09-06

### Changed

- Updated PyInstaller hooks from 2026.6 to 2026.7 in both Windows package
  locks and Ruff from 0.16.4 to 0.16.5 in the development toolchain.

### Fixed

- Preserve existing image and video exports when processing, audio restoration,
  or final file replacement fails; report image processor failures accurately.
- Reject failed FFmpeg decoding and incomplete frames, handle short pipe reads,
  and prevent diagnostic output from blocking video exports.
- Use private temporary workspaces so frame extraction and cleanup cannot
  collide with unrelated folders or same-named videos. Retained-frame locations
  are printed in the processing log.
- Recover from malformed saved settings and preserve the previous settings file
  when a save is interrupted.
- Release camera and virtual-camera resources after startup failures, and
  prevent file rendering from overlapping live output.
- Clean up interrupted model downloads, preserve existing models when download
  publication fails, and reject insecure redirects before following them.
- Validate CLI resource values and check for both FFmpeg tools before video use.
- Bind CUDA binaries, DirectML binaries, and corresponding source to the same
  resolved release commit, and reject stale release-gate evidence.

### Documentation

- Clarified which model downloads use Set Up Models and which may be initiated
  by dependencies on first use.
- Corrected the build-only PyTorch security exception: the pinned 2.11.0 wheel
  is in the advisory's affected range; the exception relies on excluding
  Torch/JIT code from the application and copying only reviewed CUDA/cuDNN DLLs.

## [2.2.3] - 2026-08-28

### Changed

- Video Preview now starts processed target videos automatically and provides
  Play, Pause, and responsive timeline controls.
- Processed previews read frames sequentially through one persistent decoder
  and advance at the achievable face-processing rate instead of skipping
  source frames when processing is slower than the source video.

### Fixed

- Prevented the Preview window from growing as processed frames are displayed.
- Avoided reopening and seeking the video decoder for every preview frame,
  unnecessary temporal-state resets, and duplicate or unreachable edge frames.
- Hardened Preview shutdown, error retry, idle-timer restart, missing
  frame-count metadata, and file/live-preview mutual exclusion.
- Confirmed the autoplay, stable-window, sequential playback, controls, seek,
  and close behavior on Windows with a Radeon RX 6900 XT. The tester's separate
  low achieved-FPS observation remains dependent on face-processing throughput
  and is not interpreted as a 30 FPS cap.

## [2.2.2] - 2026-08-18

### Changed

- Updated the deterministic Windows packaging toolchain to pip 26.2.1, wheel
  0.48.0, PyInstaller 6.22.0, pip-tools 7.6.1, and Ruff 0.16.3.
- Standardized NVIDIA/CUDA installs on one stable per-user directory and
  documented the distinct installer and DirectML portable update paths.

### Fixed

- Replaced the unavailable ONNX Runtime GPU 1.24.3 package with the compatible
  1.24.4 patch release and refreshed its lock and licence evidence.
- Migrated registered version-named NVIDIA installations during upgrades,
  removed recognizable orphaned version folders, refreshed stale packaged
  runtime directories, and preserved models, settings, and logs.
- Isolated installer smoke tests from real Windows app registrations and added
  a functional legacy-layout upgrade fixture.

## [2.2.1] - 2026-08-03

### Added

- Added reproducible CUDA and DirectML dependency locks, strict provider
  verification, and expanded release evidence for both Windows runtimes.
- Added repository governance, security-reporting, support, contribution, and
  dependency-update policies, plus structured issue and pull-request forms.

### Changed

- Promoted the social-preview artwork to the README hero and moved the real
  application screenshot into the usage guide for a clearer front page.
- Modernized the public repository presentation with a release-independent
  README, documentation index, support and governance policies, structured
  issue forms, a pull-request checklist, CODEOWNERS, and a social-preview asset.
- Strengthened repository administration with required CodeQL checks, enforced
  branch protection for administrators, Discussions, automatic merged-branch
  cleanup, and clearer security-reporting boundaries.
- Raised the declared tqdm and typing-extensions floors to their already locked
  releases and limited automated pip update PRs to build/dev tools. Runtime
  dependencies remain on the manual lock, licence, package, and hardware path.
- Refreshed the reviewed Windows dependency set: ONNX Runtime GPU 1.24.3,
  OpenNSFW2 0.18.0, PyInstaller 6.21.0, PyInstaller hooks 2026.6,
  PySide6 6.11.1, and pytest 9.1.1, with regenerated CUDA and DirectML locks.
- Kept the lock generator on pip 26.1.2 and the CUDA DLL source on Torch
  2.11.0+cu128 until their proposed upgrades are compatible with the release
  pipeline and reviewed as complete runtime changes.
- Removed unused imports, locals, package exports, and an obsolete adaptive
  feathering argument without changing runtime behavior.
- Kept the DirectML test build manually dispatchable while removing its stale
  trigger for the retired AMD issue branch.
- Refactored high-complexity UI and frame-pipeline orchestration behind
  characterization tests while preserving Preview, Render, and Live Output
  behavior.

### Fixed

- Confirmed the DirectML release candidate on Windows 11 with a Radeon RX 9060
  XT: DirectML active, Preview passed, short-video Render passed, OBS Live
  Output passed, and no blocking regression was reported.

### Removed

- Removed repository-local agent/Spec Kit scaffolding, obsolete duplicate
  launch scripts, the undocumented CUDA batch wrapper, and the superseded
  standalone benchmark script.

## [2.2.0] - 2026-08-02

### Added

- Added a separately packaged DirectML runtime for AMD and Intel DirectX 12
  GPUs, with strict accelerator verification and adapter selection.
- Added release packaging and SHA-256 verification for the DirectML portable
  ZIP.

### Changed

- DirectML face analysis now uses the CPU compatibility path while face
  swapping and enhancement remain on the GPU for Radeon stability.
- Windows release CI now produces both the NVIDIA/CUDA installer asset set and
  the AMD/Intel DirectML portable asset.
- Installed support and update links now point to this maintained distribution
  while preserving upstream attribution.

### Fixed

- Prevented Preview and Start Render from re-entering while a file operation
  is already loading models, which could deadlock the UI.
- Preserved dot-prefixed runtime directories in GitHub artifacts so required
  scikit-learn DLLs are not omitted.
- Restored the pinned CUDA 12/cuDNN 9 runtime DLL set in clean NVIDIA installer
  builds and made packaging fail if any required DLL is absent.
- Improved provider diagnostics so an unavailable GPU provider cannot be
  mistaken for successful acceleration.

### Security

- Updated ONNX to 1.22.0 and Pillow to 12.3.0 to incorporate their current
  upstream security fixes before publishing the Windows binaries.
- Portable packaging rejects model/checkpoint files and validates the required
  runtime contents before publication.

## [2.1.9] - 2026-05-20

### Added

- Added extended subject masking and a subject-mask preview overlay.

### Fixed

- Fixed alpha-channel preview frames before face detection and swap inference.
- Fixed packaged desktop startup on clean Windows laptops.

[Unreleased]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.2.4...HEAD
[2.2.4]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.2.3...v2.2.4
[2.2.3]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.2.2...v2.2.3
[2.2.2]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.1.9...v2.2.0
[2.1.9]: https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.1.9
