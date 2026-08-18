# Clean Windows Verification

Status: PASS

Release: `2.2.2`

This gate covers the per-user CUDA installer. Exact final hashes are recorded
outside the installed payload in `RELEASE_ASSETS.md` and `SHA256SUMS.txt` to
avoid circular binary-hash documentation.

## Required checks

- [x] Installation succeeds without elevation into one stable per-user path.
- [x] Upgrade removes the registered legacy version directory and recognizable
  orphaned version directories, then leaves one uninstall registration.
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
- Baseline: the published `2.2.1` per-user installer uses a version-named
  directory and can leave older version directories behind.
- The `2.2.2` installer uses one stable directory. An isolated functional test
  installed a registered `2.2.1` legacy-layout fixture, added an orphaned
  `2.1.9` installation directory, upgraded to `2.2.2`, and verified that both
  old directories were removed, one `2.2.2` uninstall entry remained, and the
  user-model sentinel survived.
- Installer automation uses a unique test-only GUID, validates the installed
  file set, launches the CLI, scans for model weights, and verifies
  silent-uninstall model preservation without changing a real installation.
- The project owner confirmed Preview, Start Render, and Live Output on the
  CUDA runtime after the `2.2.0` runtime changes; `2.2.2` changes packaging and
  dependency patches without changing face-processing behavior.
- Final publication additionally requires downloading the GitHub-hosted
  installer and repeating the automated install/CLI/uninstall smoke check.

Run the repeatable gate with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.2.2
```
