---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Source Preparation

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Publication is authorized by Neil Mitchell and pending actual publication.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.


The official corresponding source was built from the immutable commit above, passed a per-file comparison to Git, and was downloaded again from the draft with matching hashes. It is attached as `DeepLiveCamStudio-2.2.4-source-617c733d42a1.zip`, with its SHA-256 sidecar and manifest.

[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

For independent reproduction, use a clean checkout and a separate output directory:

```powershell
$ReleaseCommit = '617c733d42a10a2fcba036385e19d66fabcc2cc1'
git show --no-patch $ReleaseCommit
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.4 -GitRef $ReleaseCommit -OutputDir build\windows\source-verification\2.2.4
```

Do not overwrite frozen release files to refresh documents. Later evidence is a separate attestation. Older instructions inside the exact source archive remain historical content of that commit; the current external handoff records completed checks and remaining publication work.
