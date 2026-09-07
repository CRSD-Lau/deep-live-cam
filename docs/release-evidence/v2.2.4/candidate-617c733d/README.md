---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Corrected 2.2.4 candidate evidence

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Publication is authorized by Neil Mitchell and pending actual publication.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.


[RELEASE_VALIDATION.md](RELEASE_VALIDATION.md) summarizes exact-byte build, hosted download, installer, CUDA/CPU/AMD processing, catalogue and notice checks. Its companion JSON binds the input reports by hash. [BUILD_SOURCE_VALIDATION.md](BUILD_SOURCE_VALIDATION.md) is a path-redacted derivative of the original source/build receipt; all measurements and original receipt hashes are retained.

The CUDA and DirectML compliance reports inspect actual payload inventories and 77 upstream notice files. Existing DirectML validation files remain byte-identical to their first completed reports. The seven frozen binary/source files still originate from the official workflow; later attestations do not alter their source.

The actual corrected installation is a same-version replacement of the first 2.2.4 candidate. Its earlier 2.2.3 upgrade proof and both data backups are preserved separately. Post-install binary measurements do not claim an independent full payload manifest.

All seven outstanding manual checks are PASS as reported by Neil Mitchell. Publication is authorized and pending execution; retain `v2.2.3` and the verified backups for rollback.

The frozen automated reports retain their original pre-confirmation publication flags and scope limits. The owner confirmation and current active gate documents record the later manual PASS report and publication authorization without altering those historical measurements.
