# Clean Release Worktree Verification

Status: AUTOMATED-PASS

This file records evidence that the Windows release artifact set can be
validated from a clean Git worktree for the release commit. It does not replace
the manual clean VM, OBS visual workflow, or legal review gates.

## Release Commit Under Test

- Commit: `ee44e48b3781ee6a2362ed431b18b46c7db44204`
- Worktree used: `C:\Projects\deep-live-cam-release-verify`
- Verification time UTC: `2026-05-19T07:25:46Z`
- Main developer worktree status at the time: dirty with mixed-scope runtime and quality work excluded from this release commit.

## Artifact Set

- Installer: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: see `DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`.
- Source archive: see `build/windows/release-assets/2.1.5/RELEASE_ASSETS.md`.
- Source SHA-256: see `build/windows/release-assets/2.1.5/RELEASE_ASSETS.md` and the matching `.sha256` sidecar.

## Automated Checks

- [x] Detached release worktree checked out at the release commit.
- [x] `git status --short --untracked-files=all` returned no paths in the detached release worktree.
- [x] `tools/check_windows_release_cutover.py` reported `Dirty paths: 0` in the detached release worktree.
- [x] `build/windows/package_source.ps1 -AppVersion 2.1.5 -GitRef HEAD -OutputDir C:\Projects\deep-live-cam\build\windows\clean-worktree-source-check` created the source archive from the clean detached release worktree without `-AllowDirty`.
- [x] Source archive manifest records `Archive mode: git-ref`.
- [x] Source archive manifest records the exact resolved release commit.
- [x] Source archive validation found no `.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, or model-cache entries.
- [x] `tools/validate_windows_release_artifacts.py --require-git-ref-source --release-assets-dir C:\Projects\deep-live-cam\build\windows\release-assets\2.1.5` passed against the installer and source archive.
- [x] Focused release tests passed from the detached release worktree using the main workspace Python: `25 passed`.

## Remaining Non-Automated Gates

The release is still not publish-ready until these separate files are completed:

- `CLEAN_VM_VERIFICATION.md`
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md`
- `LEGAL_REVIEW.md`
