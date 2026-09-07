---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Compliance Delta Review

Status: PASS

Publication status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Published as the [latest stable v2.2.4](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.2.4) at 2026-09-07T01:55:44Z. [Public verification](docs/release-evidence/v2.2.4/candidate-617c733d/PUBLIC_RELEASE_VALIDATION.md) passed for all 47 fresh unauthenticated downloads and the annotated tag at the frozen source commit.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.

Release: `2.2.4`

Candidate source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Workflow: [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The corrected DirectML payload's
[technical audit](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_COMPLIANCE_TECHNICAL.md)
passed against its extraction receipt: all 77 newly collected notice/metadata
files match the pinned upstream packages, every inventory version matches its
lock, and both executable archives were inspected. This closes the earlier
DirectML notice finding. The final CUDA payload and exact-source checks also passed, as recorded in the combined validation.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [x] Verify exact matching source and runtime commits, hashes, attribution and AGPL source instructions.
- [x] Inspect both final runtime inventories, embedded modules and actual notice contents.
- [x] Verify collected pip/setuptools and vendor notices match the pinned main build environment.
- [x] Verify PyInstaller's licence/bootloader exception and the contributed hooks' licence texts.
- [x] Verify the CUDA helper uses the main pinned pip and fresh helpers omit bootstrap tools.
- [x] Verify CUDA DLL provenance, Qt notices and the documented build-only Torch exception's scope.
- [x] Scan both final payloads and corresponding source for excluded weights, Torch/JIT Python code and bundled FFmpeg.
- [x] Reconcile the actual packaging delta with the established distribution posture.

The previous owner-accepted distribution posture is recorded in
docs/release-evidence/v2.2.3/LEGAL_REVIEW.md. This technical delta review retains that posture. Neil Mitchell
has now separately confirmed the manual checks and authorized publication; this
does not constitute a new legal opinion. Runtime versions and model families remain unchanged;
packaging hooks move from 2026.6 to 2026.7 and development Ruff from 0.16.4 to
0.16.5. pip/setuptools package and vendor notices must accompany any embedded code.

The first candidate's deeper inspection found these notices missing. Its earlier
DirectML presence check did not establish complete embedded-module notice coverage.
The corrected payload audits resolve this finding; archived verdicts remain unchanged.
The affected build-only Torch 2.11.0 wheel retains the existing scoped exception
in docs/DEPENDENCY_LOCKS.md; do not claim the wheel is patched. CUDA seed DLLs may
have documented transitive binary dependencies, such as nvJitLink from cuSPARSE.
FFmpeg and model licences remain separate redistribution boundaries.

The eight technical delta checks above are complete within the established distribution posture. Both profiles match all 77 notice files and locked inventory rows; source membership and bytes match Git. Helper targeting is established by exact source plus successful pinned-pip/Torch log output, not an independently instrumented install-report. This PASS is technical evidence, not new legal advice. The separate owner confirmation closes the manual gates and authorizes publication; publication and public download verification are complete.
