---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Clean Windows Verification

Status: PENDING

Release: `2.2.4`

Candidate source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Workflow: [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

The corrected [DirectML artifact/runtime checks](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_VALIDATION.md)
passed on the configured host, including safe extraction, strict preflight,
AMD processing and consent cancellation. This portable-runtime evidence does
not establish installation or clean-Windows behavior.

- [x] Verify the replacement official installer and DirectML ZIP hashes and provenance.
- [x] Execute the verified replacement installer, preserving current user data and a verified backup.
- [x] Verify one stable registration, required installed files and the new executable identities.
- [x] Verify the rebuilt hosted test-GUID legacy migration, orphan cleanup and model-preserving uninstall fixture.
- [ ] Verify the final installer on clean Windows, including installation, a 2.2.3 upgrade, no elevation and shortcut launch.
- [ ] Check GUI model consent, missing-model behavior and interactive uninstall choices.
- [x] Inspect final CUDA/DirectML notice contents and weight exclusion.

The original official 2.2.3-to-2.2.4 upgrade passed on the configured workstation;
the archived receipt records its exact first-candidate installer and executable
hashes. The corrected local install passed as a same-version first-candidate-to-rebuilt-2.2.4
replacement. Both receipts and user-data backups are preserved separately. Neither
configured-host upgrade nor the isolated test-GUID fixture establishes clean-VM
or interactive GUI behavior. Do not uninstall the live application to manufacture
that evidence.
