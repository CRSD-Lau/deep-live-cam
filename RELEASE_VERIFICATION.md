---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Verification

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.


App version: `2.2.4`

Status: DRAFT — FINAL ARTIFACT AND MANUAL VERIFICATION PENDING

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

- Local installer automation passed: PENDING CURRENT FINAL-ARTIFACT ATTESTATION
- Public-release source archive from clean Git ref: PENDING FINAL-ASSET VERIFICATION
- Ready to publish without remaining manual gates: NO

This is a pending source-document placeholder, not a generated final verification
report. The [2.2.3 preparation snapshot](docs/release-evidence/v2.2.3/preparation/RELEASE_VERIFICATION.md)
is preserved unchanged; its manual PASS claims do not apply to 2.2.4.

The final generated report must identify the actual installer, portable and source
assets, their hashes, and current-release evidence. Only completed checks may be
recorded as PASS. Keep the draft unpublished while any required gate is pending.
Later documentation attestations do not change the fixed binary/source commit.
