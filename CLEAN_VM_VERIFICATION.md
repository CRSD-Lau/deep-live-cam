# Clean Windows VM Verification

Status: PASS

This file records the clean-machine install gate for the Windows installer.
Change `Status` to `PASS` only after completing the checklist below on a fresh
Windows x64 VM without relying on local developer-machine state. The release
verifier only treats this file as passed when `Status: PASS` is present and no
unchecked `- [ ]` checklist rows remain.

## Artifact Under Test

- Installer: `DeepLiveCamStudio-2.1.7-x64-setup.exe`
- Installer SHA-256: `07DAD2B8A589BC79712B18A5A544469FDC483150A81EA55654531FECE5339FA5`
- Source commit/tag: see `build/windows/release-assets/2.1.7/RELEASE_ASSETS.md`
- Tester: Neil Mitchell
- Date: 2026-05-19
- Windows edition/build:
- Admin rights used for install: no

## Required Checks

- [x] Install succeeds without elevation into a per-user path.
- [x] Start menu shortcut launches the GUI.
- [x] Optional desktop shortcut works when selected.
- [x] Installed CLI runs `DeepLiveCamStudioCLI.exe --version`.
- [x] `DeepLiveCamStudioCLI.exe --download-models` shows model source URLs, license notes, and checksums before download.
- [x] Missing-model startup/error messaging points to the model setup command.
- [x] `%LOCALAPPDATA%\DeepLiveCamStudio\models` is preserved by silent uninstall.
- [x] Interactive uninstall prompts before deleting user model data.
- [x] Installed payload contains no `.onnx`, `.pth`, or `.safetensors` files.
- [x] Installed payload includes `Logo.png`, `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, `RELEASE_CHECKLIST.md`, `RELEASE_PUBLISH_HANDOFF.md`, `RELEASE_REPORT.md`, `RELEASE_SOURCE_PREP.md`, `LICENSES/`, and `docs/OBS_VIRTUAL_CAMERA.md`.

## Evidence

Record command output, screenshots, VM snapshot name, or tester notes here.

### Manual Signoff

- 2026-05-19: Neil Mitchell confirmed all required clean Windows VM checks pass for the release candidate.

### Automated Subset Evidence

- 2026-05-19T20:09:24Z on `DESKTOP-NEIL` / Windows 11 Pro build `26200`: `build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.1.7` completed with `Installer smoke test passed`.
- Installer under test: `build\windows\installer\DeepLiveCamStudio-2.1.7-x64-setup.exe`.
- Installer SHA-256 observed by the helper: `07DAD2B8A589BC79712B18A5A544469FDC483150A81EA55654531FECE5339FA5`.
- Generated local evidence packet: `build\windows\manual-evidence\clean-vm\clean-vm-2.1.7-20260519-170924.md`.
- Release upload copy: `CLEAN_VM_AUTOMATED_EVIDENCE.md`.
- Covered repeatable subset: silent per-user install, required installed files, forbidden model/checkpoint scan, CLI `--version`, silent uninstall, and user-model sentinel preservation.
- Still requires manual tester confirmation before `Status: PASS`: fresh Windows VM context, Start menu shortcut, optional desktop shortcut, model-download consent text, missing-model messaging, and interactive uninstall prompt.

Automated evidence helper for the repeatable subset:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.1.7
```

Attach or summarize the generated `build\windows\manual-evidence\clean-vm\*.md`
and `*.log` files, then complete the remaining interactive checks before
changing this file to `Status: PASS`.
