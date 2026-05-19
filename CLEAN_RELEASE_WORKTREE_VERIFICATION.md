# Clean Release Worktree Verification

Status: AUTOMATED-PASS

This file records evidence that the Windows release artifact set can be
validated from a clean Git worktree for the release commit. It does not replace
the manual clean VM, OBS visual workflow, or legal review gates.

## Release Commit Under Test

- Commit: `930e6ea39546bf7e4d90b4feb5b7f24783190940`
- Worktree used: `C:\Projects\deep-live-cam-release-verify`
- Verification time UTC: `2026-05-19T02:34:00Z`
- Main developer worktree status at the time: dirty with mixed-scope runtime and quality work excluded from this release commit.

## Artifact Set

- Installer: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: `ECD1840E2C8761C38BAE4E05488CB716D00B0A95B3A32471F5306F19DF86ACF7`
- Source archive: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-source-930e6ea39546.zip`
- Source SHA-256: `AD5D3E93A0D204CE2D475A41FCA1A2100F8A3D66260CE0B66A55C08960836731`

## Automated Checks

- [x] Detached release worktree checked out at the release commit.
- [x] `git status --short --untracked-files=all` returned no paths in the detached release worktree.
- [x] `tools/check_windows_release_cutover.py` reported `Dirty paths: 0` in the detached release worktree.
- [x] `build/windows/package_source.ps1 -AppVersion 2.1.5 -GitRef HEAD` created the source archive from the clean detached release worktree without `-AllowDirty`.
- [x] Source archive manifest records `Archive mode: git-ref`.
- [x] Source archive manifest records the resolved commit `930e6ea39546bf7e4d90b4feb5b7f24783190940`.
- [x] Source archive validation found no `.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, or model-cache entries.
- [x] `tools/validate_windows_release_artifacts.py --require-git-ref-source` passed against the installer and source archive.
- [x] Focused release tests passed from the detached release worktree: `22 passed`.

## Remaining Non-Automated Gates

The release is still not publish-ready until these separate files are completed:

- `CLEAN_VM_VERIFICATION.md`
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md`
- `LEGAL_REVIEW.md`

