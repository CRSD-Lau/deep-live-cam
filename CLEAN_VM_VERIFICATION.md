---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Clean Windows Verification

Status: PENDING

Release: `2.2.4`

Candidate source: PENDING — record the corrected immutable build SHA and asset hashes.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

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
