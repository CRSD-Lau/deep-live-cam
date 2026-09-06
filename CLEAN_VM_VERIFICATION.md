---
author: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Clean Windows Verification

Status: PENDING

Release: `2.2.4`

The previous signed-off record is preserved in
`docs/release-evidence/v2.2.3/CLEAN_VM_VERIFICATION.md`. It is historical evidence,
not a test of the 2.2.4 installer. Installer identity, migration and user-data
paths remain unchanged. Packaging hooks and application code have changed.

## Current release checks

- [ ] Validate the final downloaded installer, its expected version and file set.
- [ ] Exercise legacy migration, stable-version upgrade and uninstall with model preservation.
- [ ] Verify installation without elevation and shortcut launch in a clean Windows environment.
- [ ] Check model-setup consent, missing-model messaging and interactive uninstall choices.
- [ ] Confirm both runtime payloads contain notices and no model/checkpoint files.

`test_installer.ps1` compiles an isolated test-GUID installer from the payload.
Its result validates installer logic; it does not prove execution of the
supplied official installer EXE. Record actual hosted-installer execution
separately. Automated evidence must identify the tested source and artifacts.
