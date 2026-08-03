# Changelog

All notable changes to this Windows Studio distribution are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases use [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Modernized the public repository presentation with a release-independent
  README, documentation index, support and governance policies, structured
  issue forms, a pull-request checklist, CODEOWNERS, and a social-preview asset.
- Strengthened repository administration with required CodeQL checks, enforced
  branch protection for administrators, Discussions, automatic merged-branch
  cleanup, and clearer security-reporting boundaries.
- Raised the declared tqdm floor to the already locked 4.70.0 release and held
  incomplete TensorFlow, DirectML, camera-enumeration, and generic Torch bot
  proposals until their full release and hardware gates can be satisfied.
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

[Unreleased]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.1.9...v2.2.0
[2.1.9]: https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.1.9
