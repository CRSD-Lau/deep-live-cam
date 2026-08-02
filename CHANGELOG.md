# Changelog

All notable changes to this Windows Studio distribution are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases use [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Improved provider diagnostics so an unavailable GPU provider cannot be
  mistaken for successful acceleration.

### Security

- Portable packaging rejects model/checkpoint files and validates the required
  runtime contents before publication.

## [2.1.9] - 2026-05-20

### Added

- Added extended subject masking and a subject-mask preview overlay.

### Fixed

- Fixed alpha-channel preview frames before face detection and swap inference.
- Fixed packaged desktop startup on clean Windows laptops.

[2.2.0]: https://github.com/CRSD-Lau/deep-live-cam/compare/v2.1.9...v2.2.0
[2.1.9]: https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.1.9
