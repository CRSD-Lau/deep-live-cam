---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Publish Handoff

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Publication is authorized by Neil Mitchell and pending actual publication.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.


The existing draft targets the frozen commit above. Corrected runtime and source assets have replaced the superseded candidate. Preserve all seven frozen binary/source files, their hashes, and the existing `v2.2.3` rollback release. Tag verification, publication and public-download readback remain execution steps of the authorized publication.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The official workflow 34063403042 passed for both runtime profiles and exact corresponding source. All 36 original assets passed their checksum and structure checks; fresh draft-hosted downloads matched the verified runtime/source files.

The corrected installer ran successfully over the superseded 2.2.4 candidate. Seven user-data files totaling 1,558,270,376 bytes remained identical, with a verified backup and the earlier 2.2.3 upgrade evidence preserved. One stable registration and 30 required installed files were verified. Installed executable hashes are post-install measurements; no independent full-payload manifest was supplied.

Real CUDA and AMD device-1 DirectML image and silent/audio video processing passed, including Unicode output and failed-export preservation. CPU fallback passed its image-only checks. Existing model and executable hashes remained unchanged. The fresh five-model catalogue download and cancellation checks passed.

Both payload audits matched all 77 upstream tool notice files and every locked inventory row. The affected build-only Torch exception remains documented; runtime audits, critical lint, security checks and CodeQL passed. Local integration passed 744 tests; exact-source CI passed 742 with two platform skips.

## Manual validation confirmed by the owner

Neil Mitchell reports PASS for all seven outstanding items covering clean-Windows installation/2.2.3 upgrade, shortcut/model-consent/interactive-uninstall behavior, packaged Preview, physical-camera Live Output start/stop/restart, file/live exclusion, processed output in an independent receiver and the documented OBS workflow. The linked owner confirmation records the report against the final candidate. The agent did not execute these manual checks; source-only synthetic OBS and configured-host installer tests retain their separate recorded scopes.

`LEGAL_REVIEW.md` is a completed technical delta review under the established distribution posture. It is not a new legal opinion. The scoped affected Torch DLL-source-wheel exception and separate model/FFmpeg licences remain recorded.

Run the read-only checks against the complete downloaded/curated asset directory:

```powershell
python tools\summarize_manual_release_gates.py --app-version 2.2.4 --strict
python tools\validate_windows_release_artifacts.py --app-version 2.2.4 --output-dir build\windows\release-assets\2.2.4 --release-assets-dir build\windows\release-assets\2.2.4 --require-git-ref-source --require-directml-portable
```

Use the actual asset directory for both directory options. The artifact validator checks integrity and document structure; the strict summary is the separate manual gate. `Ready to publish without remaining manual gates: YES` now reflects the completed current-version checks and Neil Mitchell's explicit manual confirmation. Publication itself remains pending execution.

## Publication order

1. Create and verify the annotated `v2.2.4` tag at the fixed build commit; the owner-reported manual gates are complete.
2. Reconcile the existing draft with the final notes and every file listed in `RELEASE_ASSETS.md`. Keep binaries/source unchanged when updating attestations.
3. Compare all GitHub asset names, sizes and digests with `SHA256SUMS.txt`; fresh runtime/source downloads have passed, and must retain the same asset identities and bytes.
4. Recheck issues, PRs and security alerts. Record any unresolved or inaccessible check.
5. Publish the existing draft, then verify public availability and hashes.

`run_release_checks.ps1` is a build-stage command that repackages files and regenerates evidence. Use it for a new build before freezing bytes, not as a read-only test of this completed artifact set.

## Recovery

Keep `v2.2.3` and verified user-data backups available. A failed check leaves the draft unpublished. Do not silently replace a published binary, change its source identity, uninstall the working application, or run an automatic downgrade. Any new candidate needs its own matching bytes and evidence.
