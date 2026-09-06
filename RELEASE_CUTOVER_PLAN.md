---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows 2.2.4 Release Cutover Plan

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: DRAFT — MANUAL VERIFICATION REMAINS

The fixes, builds, configured-host installation, CLI processing, source matching, model setup and notice correction have completed their automated checks. Preserve the exact tested binaries and source; later documentation does not change their identity.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

1. Complete the pending clean-Windows, packaged Preview, physical-camera Live Output and independent receiver checks.
2. Update only the relevant current-version evidence with observed results; run the strict manual gate summary.
3. After all gates pass, create/verify the annotated tag at the frozen commit and reconcile the final checksum manifest and hosted files.
4. Recheck repository/security status, publish the existing draft, then verify public download availability and hashes.
5. Keep `v2.2.3` and the verified data backups available for a deliberate recovery decision.

Do not substitute a source-only camera sender test, a test-GUID installer, historical 2.2.3 reports, or a version-string match for the pending final-package checks. The complete procedure is in [RELEASE_PUBLISH_HANDOFF.md](RELEASE_PUBLISH_HANDOFF.md).
