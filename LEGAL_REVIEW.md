---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Compliance Delta Review

Status: PENDING

Release: `2.2.4`

Candidate source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Workflow: [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
Artifact hashes and completed checks remain to be recorded; source identity alone
is not validation of built files.

The corrected DirectML payload's
[technical audit](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_COMPLIANCE_TECHNICAL.md)
passed against its extraction receipt: all 77 newly collected notice/metadata
files match the pinned upstream packages, every inventory version matches its
lock, and both executable archives were inspected. This closes the earlier
DirectML notice finding; final CUDA and corresponding-source checks remain pending.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [ ] Verify exact matching source and runtime commits, hashes, attribution and AGPL source instructions.
- [ ] Inspect both final runtime inventories, embedded modules and actual notice contents.
- [ ] Verify collected pip/setuptools and vendor notices match the pinned main build environment.
- [ ] Verify PyInstaller's licence/bootloader exception and the contributed hooks' licence texts.
- [ ] Verify the CUDA helper uses the main pinned pip and fresh helpers omit bootstrap tools.
- [ ] Verify CUDA DLL provenance, Qt notices and the documented build-only Torch exception's scope.
- [ ] Scan both final payloads and corresponding source for excluded weights, Torch/JIT Python code and bundled FFmpeg.
- [ ] Reconcile the actual packaging delta with the established distribution posture.

The previous owner-accepted distribution posture is recorded in
docs/release-evidence/v2.2.3/LEGAL_REVIEW.md. This technical delta review does not
invent new owner signoff. Runtime versions and model families remain unchanged;
packaging hooks move from 2026.6 to 2026.7 and development Ruff from 0.16.4 to
0.16.5. pip/setuptools package and vendor notices must accompany any embedded code.

The first candidate's deeper inspection found these notices missing. Its earlier
DirectML presence check did not establish complete embedded-module notice coverage.
Resolve this finding against rebuilt payloads, not by changing archived verdicts.
The affected build-only Torch 2.11.0 wheel retains the existing scoped exception
in docs/DEPENDENCY_LOCKS.md; do not claim the wheel is patched. CUDA seed DLLs may
have documented transitive binary dependencies, such as nvJitLink from cuSPARSE.
FFmpeg and model licences remain separate redistribution boundaries.
