# Clean Windows VM Verification

Status: PENDING

This file records the clean-machine install gate for the Windows installer.
Change `Status` to `PASS` only after completing the checklist below on a fresh
Windows x64 VM without relying on local developer-machine state. The release
verifier only treats this file as passed when `Status: PASS` is present and no
unchecked `- [ ]` checklist rows remain.

## Artifact Under Test

- Installer: `DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: `34B74A43DCECE31DE52DEF948BC9DADAB99648E6C88334EF35ECDFA07B2197BA`
- Source commit/tag: see `build/windows/release-assets/2.1.5/RELEASE_ASSETS.md`
- Tester:
- Date:
- Windows edition/build:
- Admin rights used for install: no

## Required Checks

- [ ] Install succeeds without elevation into a per-user path.
- [ ] Start menu shortcut launches the GUI.
- [ ] Optional desktop shortcut works when selected.
- [ ] Installed CLI runs `DeepLiveCamStudioCLI.exe --version`.
- [ ] `DeepLiveCamStudioCLI.exe --download-models` shows model source URLs, license notes, and checksums before download.
- [ ] Missing-model startup/error messaging points to the model setup command.
- [ ] `%LOCALAPPDATA%\DeepLiveCamStudio\models` is preserved by silent uninstall.
- [ ] Interactive uninstall prompts before deleting user model data.
- [ ] Installed payload contains no `.onnx`, `.pth`, or `.safetensors` files.
- [ ] Installed payload includes `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, `RELEASE_CHECKLIST.md`, `RELEASE_PUBLISH_HANDOFF.md`, `RELEASE_REPORT.md`, `RELEASE_SOURCE_PREP.md`, `LICENSES/`, and `docs/OBS_VIRTUAL_CAMERA.md`.

## Evidence

Record command output, screenshots, VM snapshot name, or tester notes here.

### Automated Subset Evidence

- 2026-05-19T06:35:21Z on `DESKTOP-NEIL` / Windows 11 Pro build `26200`: `build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.1.5` completed with `Installer smoke test passed`.
- Installer under test: `build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe`.
- Installer SHA-256 observed by the helper: `34B74A43DCECE31DE52DEF948BC9DADAB99648E6C88334EF35ECDFA07B2197BA`.
- Generated local evidence packet: `build\windows\manual-evidence\clean-vm\clean-vm-2.1.5-20260519-033521.md`.
- Release upload copy: `CLEAN_VM_AUTOMATED_EVIDENCE.md`.
- Covered repeatable subset: silent per-user install, required installed files, forbidden model/checkpoint scan, CLI `--version`, silent uninstall, and user-model sentinel preservation.
- Still requires manual tester confirmation before `Status: PASS`: fresh Windows VM context, Start menu shortcut, optional desktop shortcut, model-download consent text, missing-model messaging, and interactive uninstall prompt.

Automated evidence helper for the repeatable subset:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.1.5
```

Attach or summarize the generated `build\windows\manual-evidence\clean-vm\*.md`
and `*.log` files, then complete the remaining interactive checks before
changing this file to `Status: PASS`.
