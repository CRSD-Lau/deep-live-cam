---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Clean Windows Verification

Status: PENDING

Release: `2.2.4`

Candidate source: `753aab70c34ae585d525a06b9f7de2d721b7f491`

## Completed automated subset

- [x] Verify the official DirectML portable ZIP's SHA-256 sidecar and safe extraction.
- [x] Verify the extracted DirectML CLI reports 2.2.4 and passes the packaged
  runtime preflight, including required files, model exclusion, provider probe,
  and isolated model-setup cancellation.
- [x] Confirm existing local models were unchanged by DirectML preflight and
  inference checks.

Evidence: `.tmp/release-2.2.4/official-directml/validation.json`, workflow run
`34056909310`, artifact `9996349043`. The DirectML ZIP SHA-256 is
`3b0b1eec9467021215a1d2cff702062653305f131e70471800c755c2c8ca283a`.
This is portable-runtime evidence on the existing host, not an installation test.

## Outstanding installer and clean-environment checks

- [ ] Validate the final downloaded CUDA installer, its expected version and file set.
- [ ] Exercise registered legacy migration and the 2.2.3 stable-version upgrade,
  recording one stable install path and registration and preserved user models.
- [ ] Verify silent uninstall preserves models and interactive uninstall choices
  match the documented behavior.
- [ ] Verify installation without elevation and shortcut launch in a clean
  Windows environment.
- [ ] Check actual GUI model-setup consent and missing-model messages.
- [ ] Confirm the final CUDA payload contains its required notices and excludes
  model/checkpoint weights.

`test_installer.ps1` compiles an isolated test-GUID installer from the payload;
that validates installer logic but is separate from executing the official
downloaded installer. An actual stable upgrade on this configured host also
does not establish clean-VM behavior. Preserve both scopes in the final report.

Historical signoff is retained in
`docs/release-evidence/v2.2.3/CLEAN_VM_VERIFICATION.md`. It does not close the
outstanding 2.2.4 checks.
