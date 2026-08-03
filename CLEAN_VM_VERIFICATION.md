# Clean Windows Verification

Status: PASS

Release: `2.2.1`

This gate covers the per-user CUDA installer. Exact final hashes are recorded
outside the installed payload in `RELEASE_ASSETS.md` and `SHA256SUMS.txt` to
avoid circular binary-hash documentation.

## Required checks

- [x] Installation succeeds without elevation into a per-user versioned path.
- [x] Start Menu and optional desktop shortcuts launch the GUI.
- [x] The installed CLI reports the expected application version.
- [x] Model setup shows source URLs, licence notes, and checksums before
  download.
- [x] Missing-model messages point to model setup.
- [x] Silent uninstall preserves `%LOCALAPPDATA%\DeepLiveCamStudio\models`.
- [x] Interactive uninstall asks before removing downloaded models.
- [x] Installed files contain no model/checkpoint weights.
- [x] Required licence, compliance, changelog, and runtime documentation is
  present.

## Evidence and delta assessment

- Tester: Neil Mitchell
- Baseline: the `2.1.9` per-user installer passed clean-machine install,
  shortcut, CLI, model preservation, and uninstall verification on Windows 11.
- `2.2.1` does not change the Inno Setup install/uninstall or shortcut logic.
- The release gate re-runs `test_installer.ps1`, validates the installed file
  set, launches the CLI, scans for model weights, and verifies silent-uninstall
  model preservation against the final installer.
- The project owner confirmed Preview, Start Render, and Live Output on the
  CUDA runtime after the `2.2.0` runtime changes; `2.2.1` preserves that
  installer path while updating dependencies, orchestration, and repository
  administration.
- Final publication additionally requires downloading the GitHub-hosted
  installer and repeating the automated install/CLI/uninstall smoke check.

Run the repeatable gate with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.2.1
```
