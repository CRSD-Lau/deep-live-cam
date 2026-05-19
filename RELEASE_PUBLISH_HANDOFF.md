# Windows Release Publish Handoff

Status: NOT PUBLISH-APPROVED

This handoff is for the Windows `2.1.5` release candidate. It points release
testers and reviewers at the exact artifacts, commands, and gate files needed
before publishing a GitHub Release.

## Current Artifacts

- Upload folder: `build/windows/release-assets/2.1.5/`
- Upload manifest: `build/windows/release-assets/2.1.5/RELEASE_ASSETS.md`
- Installer: `DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: see `RELEASE_ASSETS.md` and
  `DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`
- Corresponding source archive: see `RELEASE_ASSETS.md`
- Source archive SHA-256: see `RELEASE_ASSETS.md` and the matching
  `DeepLiveCamStudio-2.1.5-source-*.zip.sha256`

Upload every file listed in `RELEASE_ASSETS.md`. Do not upload model or
checkpoint files unless a separate redistribution approval exists.

## Final Gate Commands

Run the automated gate summary first:

```powershell
venv\Scripts\python.exe tools\summarize_manual_release_gates.py --strict
```

It must pass before publication. If it fails, complete the gates below.

### Clean Windows VM

On a fresh Windows x64 VM:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.1.5
```

Then complete the interactive checks in `CLEAN_VM_VERIFICATION.md`. Change that
file to `Status: PASS` only after every checklist item is checked.

### OBS Virtual Camera

On the OBS test machine:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_obs_virtualcam_gate.ps1 -CameraName "OBS Virtual Camera"
```

Then complete the visual receiving-app or OBS rebroadcast checks in
`OBS_VIRTUAL_CAMERA_VERIFICATION.md`. Change that file to `Status: PASS` only
after every checklist item is checked.

### Legal Review

Generate the reviewer packet:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_legal_review_gate.ps1 -AppVersion 2.1.5
```

An authorized reviewer must complete `LEGAL_REVIEW.md`, including AGPL
corresponding-source handling, model-download license posture, PySide6/shiboken6
LGPL/GPL posture, `pyvirtualcam` and `cv2_enumerate_cameras` metadata, Inno
Setup commercial-use position, ffmpeg exclusion, and any unknown dependency
metadata. Change that file to `Status: PASS` only after every checklist item is
checked.

## Publish Gate

After the three manual files are `Status: PASS` with no unchecked items, run:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit> -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady
```

Then validate the upload folder:

```powershell
venv\Scripts\python.exe tools\validate_windows_release_artifacts.py --repo-root . --output-dir build\windows\installer --release-assets-dir build\windows\release-assets\2.1.5 --app-version 2.1.5 --require-git-ref-source
```

Only publish if both commands pass.

## Release Notes

Use `build/windows/release-assets/2.1.5/RELEASE_NOTES.md` as the GitHub Release
body. It includes the installer hash, source archive, source hash, AGPL source
availability notice, model exclusion notice, and remaining legal-risk notes.
