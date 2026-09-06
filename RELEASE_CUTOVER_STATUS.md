---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Cutover Status

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: BLOCKED ON CURRENT-RELEASE MANUAL GATES

- PASS: immutable source, build, artifact hashes, hosted readback, real configured-host installer replacement, CLI processing and notice completeness.
- PASS: model catalogue and technical compliance delta checks.
- BLOCKED: `CLEAN_VM_VERIFICATION.md`, `OBS_VIRTUAL_CAMERA_VERIFICATION.md` and `PROCESSING_VERIFICATION.md` retain required manual items.
- Publication: NO. The strict manual summary must continue returning nonzero while those items remain open.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

This is an attestation of those decisions, not a claim that a changing documentation worktree has zero dirty paths. The frozen source checkout was verified separately. Post-build evidence can be merged without retargeting the binaries/source or publishing the draft.

Packaged GUI Preview/Live Output, physical-camera/receiving-application behavior, and clean-Windows/interactive installation checks remain pending. Keep `v2.2.4` as a draft; `v2.2.3` remains public stable and rollback.
