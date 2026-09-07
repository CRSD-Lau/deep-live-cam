---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Cutover Status

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: PUBLISHED — PUBLIC DOWNLOADS VERIFIED

Remaining manual gates: None.

Published as the [latest stable v2.2.4](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.2.4) at 2026-09-07T01:55:44Z. [Public verification](docs/release-evidence/v2.2.4/candidate-617c733d/PUBLIC_RELEASE_VALIDATION.md) passed for all 47 fresh unauthenticated downloads and the annotated tag at the frozen source commit.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.

- PASS: immutable source, build, artifact hashes, hosted readback, real configured-host installer replacement, CLI processing and notice completeness.
- PASS: model catalogue and technical compliance delta checks.
- PASS reported by Neil Mitchell: the seven manual items in `CLEAN_VM_VERIFICATION.md`, `OBS_VIRTUAL_CAMERA_VERIFICATION.md` and `PROCESSING_VERIFICATION.md`.
- Publication: COMPLETE. The strict current-version summary passed; all 47 public assets were freshly downloaded and verified.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

This is an attestation of those decisions, not a claim that a changing documentation worktree has zero dirty paths. The frozen source checkout was verified separately. Post-build evidence can be merged without retargeting the binaries/source or publishing the draft.

All seven outstanding manual checks are PASS as reported by Neil Mitchell. Publication is complete and public downloads are verified; retain `v2.2.3` and the verified backups for rollback.
