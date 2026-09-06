---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Cutover Status

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.


Release: `2.2.4`

Status: PENDING CURRENT-RELEASE CUTOVER EVIDENCE

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

- BLOCKED: Final artifact and current-release manual verification remain pending.

The [previous generated snapshot](docs/release-evidence/v2.2.3/preparation/RELEASE_CUTOVER_STATUS.md)
is retained unchanged with the earlier preparation records. It had no explicit
release/source metadata; its old zero-dirty-path and PASS/READY verdicts must not
be treated as current measurements.

This is a pending placeholder, not freshly generated cutover evidence. Regenerate
the current report only after the documentation/evidence update is committed and
the applicable checks are complete. A clean worktree alone does not close the
five current-release gates or change the fixed binary/source commit.
