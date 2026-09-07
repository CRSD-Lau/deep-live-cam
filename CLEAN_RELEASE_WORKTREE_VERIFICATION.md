---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Clean Release Worktree Verification

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: PUBLISHED — PUBLIC DOWNLOADS VERIFIED

Remaining manual gates: None.

Published as the [latest stable v2.2.4](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.2.4) at 2026-09-07T01:55:44Z. [Public verification](docs/release-evidence/v2.2.4/candidate-617c733d/PUBLIC_RELEASE_VALIDATION.md) passed for all 47 fresh unauthenticated downloads and the annotated tag at the frozen source commit.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.

The separate rebuilt release checkout is clean at the full commit above. The successful source resolver and both runtime build jobs identify that same commit. The source archive contains 287 files / 6,691,483 unpacked bytes; all 119 required entries exist. Each member and its bytes match a fresh native Git archive of the immutable commit, with no model or local environment entries.

Source ZIP: `DeepLiveCamStudio-2.2.4-source-617c733d42a1.zip`

SHA-256: `ec59a3be3ffc4b4b58baafbc4fd4867ceeedea3fa66e3d86038dcb4dc4af7f8e`

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The published release targets the frozen build commit. All manual gates are now PASS as reported by Neil Mitchell. Create and verify the `v2.2.4` tag at the frozen commit during the authorized publication procedure; publication and public download verification are complete. Later documentation attestations preserve the seven frozen binary/source files and their original hashes; they do not become corresponding source for these binaries.
