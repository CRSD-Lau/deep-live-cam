---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Completion Audit

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.


Release: `2.2.4`

Status: PENDING FINAL ARTIFACT AND MANUAL VERIFICATION

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

The [2.2.3 preparation audit](docs/release-evidence/v2.2.3/preparation/RELEASE_COMPLETION_AUDIT.md)
is preserved unchanged as historical evidence. Its test counts, hardware reports
and readiness claims do not describe this candidate.

Record the exact final asset identities and completed 2.2.4 checks in a follow-up
attestation. Until every required gate in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
passes, the release remains a draft. This placeholder claims no new completed
manual, clean-Windows, upgrade, runtime or publication verification.
