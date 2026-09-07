---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Completion Audit

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Publication is authorized by Neil Mitchell and pending actual publication.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.


The official workflow 34063403042 passed for both runtime profiles and exact corresponding source. All 36 original assets passed their checksum and structure checks; fresh draft-hosted downloads matched the verified runtime/source files.

The corrected installer ran successfully over the superseded 2.2.4 candidate. Seven user-data files totaling 1,558,270,376 bytes remained identical, with a verified backup and the earlier 2.2.3 upgrade evidence preserved. One stable registration and 30 required installed files were verified. Installed executable hashes are post-install measurements; no independent full-payload manifest was supplied.

Real CUDA and AMD device-1 DirectML image and silent/audio video processing passed, including Unicode output and failed-export preservation. CPU fallback passed its image-only checks. Existing model and executable hashes remained unchanged. The fresh five-model catalogue download and cancellation checks passed.

Both payload audits matched all 77 upstream tool notice files and every locked inventory row. The affected build-only Torch exception remains documented; runtime audits, critical lint, security checks and CodeQL passed. Local integration passed 744 tests; exact-source CI passed 742 with two platform skips.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The first candidate at `753aab70` is superseded for missing embedded-package notices. Its byte-exact evidence remains archived. Current reports identify corrected bytes; the shared 2.2.4 version does not transfer earlier test results.

All seven outstanding manual checks are PASS as reported by Neil Mitchell. Publication is authorized and pending execution; retain `v2.2.3` and the verified backups for rollback.
