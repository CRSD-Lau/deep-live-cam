---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Clean Release Worktree Verification

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.


Release: `2.2.4`

Status: PENDING FINAL SOURCE AND ATTESTATION RECONCILIATION

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

The [2.2.3 preparation snapshot](docs/release-evidence/v2.2.3/preparation/CLEAN_RELEASE_WORKTREE_VERIFICATION.md)
is retained unchanged, including its original base commit and completed items.
Those observations are historical and are not a new clean-worktree attestation.

For this candidate, record the clean build checkout, both runtime/source provenance
records, annotated tag target and final source manifest. A later documentation-only
PR may record the completed checks without retargeting the release to that PR's
commit. No uncommitted notes, local models or user data belong in corresponding
source. Current artifact and manual release gates remain pending until documented.
