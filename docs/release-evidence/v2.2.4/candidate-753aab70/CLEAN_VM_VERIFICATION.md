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

## Official installer upgrade

- [x] Validate the fresh draft-hosted CUDA installer against its sidecar, release
  API digest/size, and the workflow asset; verify the installed version and 30
  required files.
- [x] Upgrade the actual stable 2.2.3 installation to 2.2.4, retaining one
  registration and the same installation directory.
- [x] Back up and hash all seven application-data files before installation;
  confirm all seven files and their combined 1,558,270,376 bytes are unchanged
  by path, size and SHA-256 afterward.

The official installer exited 0. Its SHA-256 is
`797f15a50cef7522374c5bf4f1880b047e6fe0f1cd165c39a1639bc36189c31d`.
The installed CLI reports 2.2.4 and has SHA-256
`9f762064b9079721c9597610689f48e306a9a0ca8483856b09f2546b2c387748`.
The CLI digest was measured after executing the verified installer; an independent
full installed-payload hash manifest was not supplied. Required-file coverage
does not claim such a full-payload comparison. The verified backup and detailed
before/after reports remain local. No GUI launch or automatic rollback was used.

## Hosted installer fixture

- [x] Reconcile the successful hosted fixture: registered 2.2.1 migration,
  orphan cleanup, model-sentinel preservation and silent uninstall checks passed.

See [the build/source attestation](docs/release-evidence/v2.2.4/BUILD_SOURCE_VERIFICATION.md).
These checks used the separate test-GUID installer compiled by the fixture.

## Outstanding clean-environment checks

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
