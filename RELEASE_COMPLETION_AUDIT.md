# Release Completion Audit

This audit maps the original Windows packaging and compliance objective to
current evidence in the workspace. It is not a replacement for
`RELEASE_CHECKLIST.md`; it is the high-level proof map used to decide whether
the active release goal is actually complete.

## Verdict

Status: **NOT COMPLETE**

The repository now has a locally verified Windows installer workflow and
release-candidate artifacts. Commit
`66f90c00fe171fde65305a960caff0c8fbff4e9e` validates from a clean detached
worktree and has a strict git-ref source archive. The active goal is still not
complete because three required manual gates remain `PENDING`.

## Current Artifact Evidence

- Installer: `build/windows/installer/DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: see
  `build/windows/installer/DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`
- Git-ref source archive:
  `build/windows/installer/DeepLiveCamStudio-2.1.5-source-66f90c00fe17.zip`
- Git-ref source SHA-256:
  `83D90030A622520CB7735A56B3598340B5F2DA99E604A5D768068076B0CE0E62`
- Git-ref source commit:
  `66f90c00fe171fde65305a960caff0c8fbff4e9e`
- Generated release verdict: `RELEASE_VERIFICATION.md`
- Final cutover procedure: `RELEASE_CUTOVER_PLAN.md`
- Current cutover status report: `RELEASE_CUTOVER_STATUS.md`
- Clean release worktree proof: `CLEAN_RELEASE_WORKTREE_VERIFICATION.md`
- The source packaging script now requires `RELEASE_COMPLETION_AUDIT.md`,
  `RELEASE_CUTOVER_PLAN.md`, `RELEASE_CUTOVER_STATUS.md`, and
  `CLEAN_RELEASE_WORKTREE_VERIFICATION.md` so the final clean source archive
  carries the release status and cutover proof trail.

## Requirement Matrix

| Requirement | Current status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Create Windows x64 installer `.exe` | Locally satisfied | Installer exists and hash sidecar verifies; local installer smoke test passes. | Re-test final clean-tag artifact on clean VM. |
| Suitable for GitHub Releases | Partial | Installer, git-ref source archive, sidecars, release checklist, notes template, and workflow exist; strict artifact validation passes. | Complete manual gates, attach final artifacts, and publish/link exact source. |
| Preserve AGPL-3.0 and source obligations | Mostly satisfied / pending publication | `LICENSE`, `COMPLIANCE.md`, `RELEASE_REPORT.md`, `RELEASE_CHECKLIST.md`, clean-worktree source proof, and source packaging script exist. The source packager requires release docs, license evidence, build scripts, installer scripts, runtime path/model code, and focused release tests. | Publish/link corresponding source for the exact final binary release and have legal review confirm the source-offer posture. |
| Avoid redistributing restricted model files | Locally satisfied | Bundle/source scans report no `.onnx`, `.pth`, `.safetensors`, `models/`, or checkpoint entries. | Re-run scans on final clean-tag release artifact. |
| First-run or CLI model downloader | Locally satisfied | `modules/model_manager.py`, `--download-models`, checksum data, and model prompt are verified by tests and packaged runtime preflight. | Re-run on final clean VM/release candidate. |
| User-writable model/config/log paths | Locally satisfied | `modules/paths.py`, packaged runtime preflight, and release docs cover `%LOCALAPPDATA%\DeepLiveCamStudio`. | Confirm on clean VM and record in `CLEAN_VM_VERIFICATION.md`. |
| Build scripts under `build/windows/` | Locally satisfied | `build_windows.ps1`, `package_installer.ps1`, `clean_build.ps1`, test scripts, source packager, and wrapper exist. | Use these from the clean release branch/tag. |
| PyInstaller/Nuitka choice and config | Locally satisfied | PyInstaller onedir spec exists at `build/windows/deep_live_cam_studio.spec`; report explains the choice. | None unless final clean build reveals missing imports. |
| Inno Setup/NSIS installer config | Locally satisfied | Inno Setup script exists at `build/windows/installer.iss`; smoke install/uninstall passes. | Confirm publisher's Inno Setup commercial-use position in legal review. |
| Start menu shortcut | Automated/partial | Inno script defines shortcut; smoke install launches CLI. | Verify GUI shortcut on clean VM. |
| Optional desktop shortcut | Configured/partial | Inno script defines optional task. | Verify on clean VM. |
| Install/uninstall support | Locally satisfied | `test_installer.ps1` installs and uninstalls temp installation. | Verify interactive uninstall behavior on clean VM. |
| Preserve user models on uninstall unless user chooses | Automated/partial | Silent uninstall sentinel preservation is tested. | Verify interactive prompt on clean VM. |
| Include release docs in installer | Locally satisfied | `RELEASE_VERIFICATION.md` lists required installed files as present; installer wrapper packages docs. | Re-run on final clean-tag artifact. |
| Dependency license audit | Partial | `LICENSES/PYTHON_DEPENDENCIES.md`, `THIRD_PARTY_NOTICES.md`, `LICENSES/THIRD_PARTY_LICENSES/`, bundle manifest, and `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` exist. | Final legal review must approve unusual/unknown metadata and GPL/LGPL implications. |
| Model license audit | Partial | `LICENSES/MODEL_LICENSE_AUDIT.md` documents separate model licenses, current source URLs, refreshed 2026-05-19 review notes, and exclusion policy. | Final legal review must confirm downloader/license language for intended distribution. |
| CUDA / ONNX Runtime provider handling | Locally satisfied | Environment preflight detects CUDA provider locally; packaged preflight reports providers. | Test final artifact on CUDA and non-NVIDIA/CPU-only machines. |
| OBS/virtual camera workflow | Partial | `docs/OBS_VIRTUAL_CAMERA.md` and test hooks exist. | Run OBS machine test and mark `OBS_VIRTUAL_CAMERA_VERIFICATION.md` as `PASS` only if all checks pass. |
| GitHub Actions workflow | Locally satisfied as release-candidate CI | `.github/workflows/windows-release.yml` builds non-strict release candidates and includes a negative publish guard. | Run in GitHub and use strict local/manual gate before publishing. |
| WebP/AVIF image uploads | Locally satisfied | `tests/test_image_upload_formats.py` passes; packaged payload includes Pillow `_webp` and `_avif` modules. | Re-test if image-loading code changes before tag. |
| Final report required by user | Partial | `RELEASE_REPORT.md` exists and is included in installer; exact artifact hashes are recorded in sidecars/manifests and summarized in assistant status reports. | Final response after manual gates should include exact final artifact paths, hashes, obligations, risks, and checks completed. |

## Blocking Gates

These must be complete before the active goal can be marked done:

- The intended release commit has validated from a clean release worktree:
  `66f90c00fe171fde65305a960caff0c8fbff4e9e`.
- `package_source.ps1 -GitRef HEAD` produced a source manifest with
  `Archive mode: git-ref` from the clean detached worktree.
- `tools/validate_windows_release_artifacts.py --require-git-ref-source`
  passed against the current installer/source artifact set.
- `build/windows/assemble_release_assets.ps1 -RequireGitRefSource` produced
  the current upload folder and `RELEASE_ASSETS.md` manifest.
- `tools/validate_windows_release_artifacts.py --release-assets-dir
  build/windows/release-assets/2.1.5 --require-git-ref-source` passed before
  this audit refresh.
- `tools/check_windows_release_cutover.py --strict --allow-mixed-scope-dirty`
  fails only because the three manual evidence files are incomplete.
- `CLEAN_VM_VERIFICATION.md` must be `Status: PASS` with no unchecked items.
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md` must be `Status: PASS` with no unchecked
  items.
- `LEGAL_REVIEW.md` must be `Status: PASS` with no unchecked items.
- `run_release_checks.ps1 -RequirePublishReady` must pass on suitable
  release-test machines.

## Evidence Commands Last Used

```powershell
venv\Scripts\python.exe -m pytest tests\test_validate_windows_release_artifacts.py tests\test_windows_release_verification.py tests\test_image_upload_formats.py tests\test_model_manager.py
venv\Scripts\python.exe tools\check_windows_release_cutover.py --repo-root . --output RELEASE_CUTOVER_STATUS.md --allow-mixed-scope-dirty
venv\Scripts\python.exe tools\validate_windows_release_artifacts.py --repo-root . --output-dir build\windows\installer --app-version 2.1.5
venv\Scripts\python.exe tools\validate_windows_release_artifacts.py --repo-root . --output-dir build\windows\installer --app-version 2.1.5 --require-git-ref-source
git worktree add --detach C:\Projects\deep-live-cam-release-verify HEAD
C:\Projects\deep-live-cam\venv\Scripts\python.exe tools\check_windows_release_cutover.py --repo-root . --limit 50 --allow-mixed-scope-dirty
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef HEAD -OutputDir C:\Projects\deep-live-cam\build\windows\clean-worktree-source-check
C:\Projects\deep-live-cam\venv\Scripts\python.exe tools\validate_windows_release_artifacts.py --repo-root C:\Projects\deep-live-cam-release-verify --output-dir C:\Projects\deep-live-cam\build\windows\installer --release-assets-dir C:\Projects\deep-live-cam\build\windows\release-assets\2.1.5 --app-version 2.1.5 --require-git-ref-source
```

The strict artifact validator passes against the current installer/source
artifact set. The clean detached release worktree cutover check reports
`Dirty paths: 0` and is blocked only by the three manual gate files.
