---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-10-25
---

# Clean Windows Verification

Status: PENDING

Release: `2.2.5`

Publication status: NOT APPROVED

Candidate source: pending immutable candidate commit and build artifacts.

The archived [2.2.4 attestation](docs/release-evidence/v2.2.4/final-attestations/CLEAN_VM_VERIFICATION.md) applies only to its original binaries. Complete these checks against the new 2.2.5 artifacts and record exact hashes, source commit, hardware, and evidence before publication.

- [ ] Verify the exact candidate installer and portable artifact hashes.
- [ ] Install on clean Windows without elevation and launch through shortcuts.
- [ ] Upgrade from 2.2.4, preserve user data, and verify migration/uninstall behavior.
- [ ] Verify model consent, missing-model behavior, and interactive uninstall choices.
