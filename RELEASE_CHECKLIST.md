---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Checklist

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: PUBLISHED — PUBLIC DOWNLOADS VERIFIED

Remaining manual gates: None.

Published as the [latest stable v2.2.4](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.2.4) at 2026-09-07T01:55:44Z. [Public verification](docs/release-evidence/v2.2.4/candidate-617c733d/PUBLIC_RELEASE_VALIDATION.md) passed for all 47 fresh unauthenticated downloads and the annotated tag at the frozen source commit.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.

## Completed candidate checks

- [x] Version, changelog, dependency locks and release defaults reconciled.
- [x] Corrected source merged; local 744-test suite and exact-source CI/CodeQL passed.
- [x] Both runtime builds and corresponding source use the frozen commit above.
- [x] Official installer, DirectML ZIP, source archive and all original asset hashes verified.
- [x] Fresh draft-hosted runtime/source downloads match verified Actions bytes.
- [x] Corrected official EXE executed over the first 2.2.4 candidate; user data and both backups preserved.
- [x] Separate hosted legacy migration, orphan cleanup and model-preserving uninstall fixture passed.
- [x] Strict CUDA and identified AMD device-1 DirectML probes and real processing passed.
- [x] Unicode output, silent/audio video integrity, failed-export preservation and CPU image fallback passed.
- [x] Fresh model catalogue consent/cancellation/download verification passed.
- [x] Both payload inventories, 77 notice files, Qt texts, CUDA provenance and exclusions inspected.
- [x] Exact corresponding-source files match Git; AGPL attribution and model limitations retained.

## Completed owner-reported manual checks

- [x] `CLEAN_VM_VERIFICATION.md`: clean-Windows installation/upgrade and interactive behavior — PASS reported by Neil Mitchell.
- [x] `OBS_VIRTUAL_CAMERA_VERIFICATION.md`: physical-camera Live Output and an independent receiver — PASS reported by Neil Mitchell.
- [x] Packaged Preview in `PROCESSING_VERIFICATION.md` — PASS reported by Neil Mitchell.

## Completed publication actions

- [x] Regenerate the strict current-version manual summary from the completed gate documents.
- [x] Create and verify an annotated `v2.2.4` tag at the fixed build commit.
- [x] Recheck the final complete hosted asset manifest, repository queue and security alerts before publication.
- [x] Publish the authorized draft and verify public downloads; preserve `v2.2.3` rollback.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The original 2.2.3-to-first-2.2.4 upgrade and corrected same-version replacement are distinct tests. Neither supplies the separate clean-Windows result, which is now PASS as reported by Neil Mitchell. Commands and publication order are in [RELEASE_PUBLISH_HANDOFF.md](RELEASE_PUBLISH_HANDOFF.md).
