# Contributing

Thanks for helping improve Deep Live Cam Studio. This fork is a Windows-focused
desktop application, so changes must preserve both CUDA and DirectML behavior
unless the pull request clearly documents a narrower platform scope.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Questions and setup help belong in [GitHub Discussions](https://github.com/CRSD-Lau/deep-live-cam/discussions); reproducible bugs and scoped features use the repository issue forms.

## Before You Start

- Use the current default branch, `windows-obs-virtualcam-runtime`, as your base.
- Open a focused branch and pull request; do not mix release, refactor, and
  unrelated feature work.
- Report security vulnerabilities privately through the process in
  [`SECURITY.md`](SECURITY.md), not in a public issue.
- Read the project scope and hardware-evidence policy in
  [`GOVERNANCE.md`](GOVERNANCE.md).
- Do not commit model/checkpoint files, generated videos, local environments,
  credentials, or release binaries.

## Development Setup

Use Python 3.11 on Windows.

For the standard CUDA profile:

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

For AMD or Intel DirectML development:

```powershell
powershell -ExecutionPolicy Bypass -File tools\setup_directml.ps1
.venv-directml\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Required Checks

Run the full source suite and the checks relevant to your change:

```powershell
venv\Scripts\python.exe -m pytest -q
venv\Scripts\python.exe -m pip_audit -r requirements.txt --progress-spinner off
venv\Scripts\python.exe -m pip_audit -r requirements-directml.txt --progress-spinner off
venv\Scripts\python.exe -m bandit -r modules tools run.py DeepLiveCamStudio.pyw -ll
venv\Scripts\python.exe -m ruff check modules tools tests run.py DeepLiveCamStudio.pyw --select E9,F63,F7,F82
```

Packaging changes must also run the appropriate Windows build and runtime
preflight documented in [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md).

Documentation-only changes should run the Markdown-link and repository-health checks documented in the pull request.

## Hardware Changes

For provider, render, camera, or live-output changes, record:

- Windows version, CPU, GPU, and driver version;
- CUDA or DirectML provider selection and provider-probe output;
- file Preview/Render behavior;
- Live Output or OBS Virtual Camera behavior when affected;
- whether face enhancement and multi-face options were enabled;
- the duration of any stability run.

Hardware-specific changes should not claim cross-vendor support without either
matching hardware evidence or a clearly described external test request.

## Pull Requests

Keep the summary user-facing and include:

- what changed and why;
- linked issue(s);
- tests and hardware validation performed;
- security, dependency, licence, and release-note impact;
- screenshots or logs when they materially help review.

Maintainers may split large refactors into staged pull requests when that makes
regression testing and rollback safer.

## Commit and Review Hygiene

- Use focused commits with descriptive messages.
- Keep generated binaries, environments, media, credentials, and local reports out of Git.
- Respond to review threads or explain why a suggestion is not being adopted.
- Do not rewrite another contributor's branch without their permission.
- Allow GitHub to delete merged topic branches unless the branch is intentionally long-lived.
