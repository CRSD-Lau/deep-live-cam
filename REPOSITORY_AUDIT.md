# Repository Engineering Audit

Audit date: 2026-08-02

## Scope

This review covered application code, tests, Windows packaging, GitHub Actions,
dependency and model supply chains, release/compliance evidence, contributor
documentation, and repository security settings.

## Evidence Collected

| Area | Result |
| --- | --- |
| Source tests | 456 passed on Python 3.11 and Windows after hardening |
| Coverage | 48.9% overall before this hardening change |
| Dependency audit | ONNX 1.21.0 and Pillow 12.2.0 findings remediated in 2.2.0; both runtime profiles then returned no known vulnerabilities |
| Dependency alert triage | GHSA-rrmf-rvhw-rf47 affects `torch.jit.script`; the app never imports or ships the PyTorch package and only copies its CUDA runtime DLLs. The official CUDA 12.8 index had no patched stable wheel on 2026-08-02, so the low alert was dismissed as not used and remains on the upgrade watchlist. |
| Static security | Three medium findings remediated; Bandit then reported zero medium/high findings |
| Secret history | Gitleaks 8.30.1 scanned 672 commits and found no leaks |
| Code quality | Ruff reported 413 existing findings, primarily annotations, broad exceptions, and import ordering |
| Complexity | Highest-risk functions are in face swapping, UI processing, pipe processing, and release verification |
| Documentation | Internal Markdown links passed; contributor and issue instructions were stale |
| GitHub security | Secret scanning, push protection, Dependabot alerts/security updates, private vulnerability reporting, and CodeQL default setup enabled; branch protection follows the first CI run |

## Remediated In The Hardening Pull Request

- Added continuous Windows tests, dependency auditing, Bandit, and critical
  Ruff checks for pull requests and the production branch.
- Added Dependabot configuration for Python and GitHub Actions.
- Upgraded GitHub-maintained actions away from deprecated Node 20 releases and
  pinned them to immutable full commit SHAs.
- Enforced verified HTTPS for model and utility downloads and removed the
  certificate-verification bypass.
- Made clean release environments the default and expanded cleanup to both
  CUDA and DirectML outputs.
- Made corresponding-source packaging peel annotated tags to their commit so
  manifests and archive names record the reproducible source commit.
- Added a security policy and replaced stale contribution and bug-report
  instructions.
- Enabled GitHub private vulnerability reporting, Dependabot security updates,
  and CodeQL default scanning; the APIs reported zero open Dependabot alerts at
  enablement.

## Deferred Work Requiring Isolated Regression Plans

### Core pipeline decomposition

`modules/processors/frame/face_swapper.py`, `modules/ui.py`, and
`modules/processors/frame/core.py` contain very high-complexity functions.
Refactor them behind characterization tests and hardware benchmarks; do not
combine that work with a release or dependency upgrade.

### Coverage of hardware and UI paths

Coverage is strong in diagnostics, tracking, compositing helpers, and release
validation, but weak in UI orchestration, startup, face analysis, video
capture, and frame-pipeline execution. Add seams for camera/provider/process
adapters before setting a global coverage gate.

### Major dependency upgrades and reproducible locks

Several dependencies have newer major releases. ONNX Runtime, OpenCV,
InsightFace, TensorFlow, psutil, and opennsfw2 changes need separate CUDA and
DirectML hardware testing. Introduce platform-specific lock or constraints
files after the supported matrix is agreed, rather than accepting unreviewed
major upgrades into release builds.

### Release verifier decomposition

The artifact validator and release-verification generator intentionally encode
many compliance rules, but their largest functions should be split into named
checks with structured results. Preserve the current negative tests while
doing so.
