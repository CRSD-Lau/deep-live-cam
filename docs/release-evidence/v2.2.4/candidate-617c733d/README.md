---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Corrected 2.2.4 candidate evidence

Release: `2.2.4`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Status: AUTOMATED CANDIDATE CHECKS PASS; MANUAL PUBLICATION GATES PENDING

[RELEASE_VALIDATION.md](RELEASE_VALIDATION.md) summarizes exact-byte build, hosted download, installer, CUDA/CPU/AMD processing, catalogue and notice checks. Its companion JSON binds the input reports by hash. [BUILD_SOURCE_VALIDATION.md](BUILD_SOURCE_VALIDATION.md) is a path-redacted derivative of the original source/build receipt; all measurements and original receipt hashes are retained.

The CUDA and DirectML compliance reports inspect actual payload inventories and 77 upstream notice files. Existing DirectML validation files remain byte-identical to their first completed reports. The seven frozen binary/source files still originate from the official workflow; later attestations do not alter their source.

The actual corrected installation is a same-version replacement of the first 2.2.4 candidate. Its earlier 2.2.3 upgrade proof and both data backups are preserved separately. Post-install binary measurements do not claim an independent full payload manifest.

Packaged GUI Preview/Live Output, physical-camera/receiving-application behavior, and clean-Windows/interactive installation checks remain pending. Keep `v2.2.4` as a draft; `v2.2.3` remains public stable and rollback.
