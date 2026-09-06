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
Artifact hashes and completed checks remain to be recorded; source identity alone
is not validation of built files.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

The corrected [DirectML artifact/runtime checks](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_VALIDATION.md)
passed on the configured host, including safe extraction, strict preflight,
AMD processing and consent cancellation. This portable-runtime evidence does
not establish installation or clean-Windows behavior.

- [ ] Verify the replacement official installer and DirectML ZIP hashes and provenance.
- [ ] Execute the verified replacement installer, preserving current user data and a verified backup.
- [ ] Verify one stable registration, required installed files and the new executable identities.
- [ ] Verify the rebuilt hosted test-GUID legacy migration, orphan cleanup and model-preserving uninstall fixture.
- [ ] Verify clean-Windows installation without elevation and shortcut launch.
- [ ] Check GUI model consent, missing-model behavior and interactive uninstall choices.
- [ ] Inspect final CUDA/DirectML notice contents and weight exclusion.

The original official 2.2.3-to-2.2.4 upgrade passed on the configured workstation;
the archived receipt records its exact first-candidate installer and executable
hashes. The next local install is a same-version first-candidate-to-rebuilt-2.2.4
replacement. Record that honestly and keep the two receipts separate. Neither
configured-host upgrade nor the isolated test-GUID fixture establishes clean-VM
or interactive GUI behavior. Do not uninstall the live application to manufacture
that evidence.
