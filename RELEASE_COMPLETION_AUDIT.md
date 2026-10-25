---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-10-25
---

# Release Completion Audit

Release: `2.2.5`

Status: PENDING

Publication status: NOT APPROVED

This is the 2.2.5 security release candidate. The [archived 2.2.4 receipt](docs/release-evidence/v2.2.4/final-attestations/RELEASE_COMPLETION_AUDIT.md) applies only to its original artifacts.

- [ ] Complete source CI, CodeQL, dependency lock reproducibility, and security audits.
- [ ] Build both Windows profiles and corresponding source from the same immutable commit.
- [ ] Verify installer, portable archive, source hashes, dependency inventories, and licence notices.
- [ ] Validate exact candidate CUDA/DirectML provider and processing behavior on supported hardware.
- [ ] Complete fresh clean-Windows installation/upgrade and OBS receiver checks.
- [ ] Complete all active manual gate documents and strict publish-readiness verification.
- [ ] Obtain publication authorization for the verified candidate before tagging or publishing.

The installed application and latest public v2.2.4 remain unchanged during preparation. Preserve current user data and a verified backup before any separately authorized upgrade. Use the Windows Release Candidate Build workflow with `app_version=2.2.5` and `git_ref=<immutable source SHA>`.
