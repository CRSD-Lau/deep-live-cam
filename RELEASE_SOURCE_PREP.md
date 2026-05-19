# Release Source Preparation

This repository currently has a locally verified Windows installer, but the
public GitHub Release gate is still blocked until the mixed-scope dirty
worktree is resolved and the manual gates are completed.

## Current Local Artifact State

- Installer: `build/windows/installer/DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: see `build/windows/installer/DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`
- Public-release source archive: see the latest `build/windows/installer/DeepLiveCamStudio-2.1.5-source-*.zip` whose manifest records `Archive mode: git-ref`
- Public-release source SHA-256: see the matching `.zip.sha256` sidecar
- Source ref: see the matching `.manifest.md`
- Current release verdict: local automation passed, public release not yet ready.

Do not hard-code installer or source archive hashes in this installed document.
The installer and source archive sidecars, plus `RELEASE_VERIFICATION.md`, are
the authoritative hash records for the current artifact set.

Older draft source archives may still exist in `build/windows/installer/` from
local testing. They are useful traceability evidence, but the public GitHub
Release should use the git-ref archive above or a later clean tag archive. To
remove stale local source archives while keeping the current upload packet, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\clean_build.ps1 -PruneStaleInstallerArtifacts -AppVersion 2.1.5
```

## Release-Relevant Files To Review Before Commit

Packaging and installer workflow:

- `.github/workflows/windows-release.yml`
- `.gitignore`
- `DeepLiveCamStudio.pyw`
- `build/windows/build_windows.ps1`
- `build/windows/clean_build.ps1`
- `build/windows/deep_live_cam_studio.spec`
- `build/windows/installer.iss`
- `build/windows/package_installer.ps1`
- `build/windows/package_source.ps1`
- `build/windows/prepare_release_staging.ps1`
- `build/windows/run_release_checks.ps1`
- `build/windows/test_environment.ps1`
- `build/windows/test_installer.ps1`
- `build/windows/test_packaged_runtime.ps1`
- `build/windows/verify_clean_vm_gate.ps1`
- `build/windows/verify_legal_review_gate.ps1`
- `build/windows/verify_obs_virtualcam_gate.ps1`
- `tools/check_cuda_provider.py`
- `tools/check_obs_virtualcam.py`
- `tools/check_windows_release_cutover.py`
- `tools/collect_third_party_license_files.py`
- `tools/generate_python_dependency_licenses.py`
- `tools/generate_windows_bundle_manifest.py`
- `tools/generate_windows_release_verification.py`
- `tools/install_windows_desktop_app.ps1`
- `tools/prune_windows_dist.py`
- `tools/validate_windows_release_artifacts.py`

Runtime path, model setup, and packaged-mode behavior:

- `modules/core.py`
- `modules/globals.py`
- `modules/paths.py`
- `modules/model_manager.py`
- `modules/ui.py`
- `modules/utilities.py`
- `run.py`
- `requirements.txt`
- `tests/test_image_upload_formats.py`
- `tests/test_model_manager.py`
- `tests/test_windows_release_scripts.py`
- `tests/test_windows_release_cutover.py`
- `tests/test_face_analyser_get_one_face.py`

Compliance and release documents:

- `COMPLIANCE.md`
- `THIRD_PARTY_NOTICES.md`
- `LICENSES/`
- `CLEAN_VM_VERIFICATION.md`
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md`
- `LEGAL_REVIEW.md`
- `README.md`
- `RELEASE_CHECKLIST.md`
- `RELEASE_COMPLETION_AUDIT.md`
- `RELEASE_CUTOVER_PLAN.md`
- `RELEASE_CUTOVER_STATUS.md`
- `CLEAN_RELEASE_WORKTREE_VERIFICATION.md`
- `RELEASE_REPORT.md`
- `RELEASE_NOTES_TEMPLATE.md`
- `RELEASE_VERIFICATION.md`
- `MODEL_DOWNLOAD_VERIFICATION.md`
- `PROCESSING_VERIFICATION.md`
- `docs/OBS_VIRTUAL_CAMERA.md`

## Mixed-Scope Files Requiring Human Review

The current worktree also contains untracked local planning/scratch files that
are not part of the Windows installer and licensing release packet:

- `.superpowers/`
- `docs/ITERATION_LOG.md`
- `docs/superpowers/`

These files are intentionally excluded from the current public release source
archive because the archive is created from the committed Git ref listed in
`RELEASE_ASSETS.md`, not from the dirty working tree. If any of those files are
intended to ship, review and commit them separately before creating the final
release tag. If they are not intended to ship, leave them out of the release
commit or move them aside before final publish signoff.

When the only dirty paths are reviewed mixed-scope scratch files and the source
archive was created from a committed Git ref, refresh the cutover report with:

```powershell
venv\Scripts\python.exe tools\check_windows_release_cutover.py --repo-root . --allow-mixed-scope-dirty --output RELEASE_CUTOVER_STATUS.md
```

## Clean Release Procedure

After the intended release files are reviewed and committed:

```powershell
git status --short
```

The output must be empty before final publish verification. A git-ref source
archive can be created from a specific commit while the developer worktree is
dirty, but public release signoff should still happen from a clean release tag
or clean release worktree.

`CLEAN_RELEASE_WORKTREE_VERIFICATION.md` records the clean-worktree proof
required for the release commit. Regenerate the source archive and strict
artifact validation if a later release commit or tag is used.

Create a release tag or use the exact release commit:

```powershell
git tag v2.1.5
```

Build and verify from that clean state:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -UseExistingVenv -GitRef v2.1.5 -RequireFfmpeg -RequireCuda
```

If the installer is already built and only the clean source archive needs to be
created:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef v2.1.5
venv\Scripts\python.exe tools\generate_windows_release_verification.py --repo-root . --dist dist\DeepLiveCamStudio --output-dir build\windows\installer --app-version 2.1.5 --output RELEASE_VERIFICATION.md
```

Do not pass `-FromWorkingTree` for a public GitHub Release.

## Manual Gates Still Required

- Clean Windows x64 VM install without admin rights. Record this in
  `CLEAN_VM_VERIFICATION.md` and change `Status` to `PASS` only after the VM
  test is complete.
- OBS Virtual Camera workflow with OBS installed and virtual camera enabled.
  Record this in `OBS_VIRTUAL_CAMERA_VERIFICATION.md` and change `Status` to
  `PASS` only after the OBS workflow is complete.
- Final legal review for model licenses, `pyvirtualcam` metadata,
  LGPL/GPL obligations, Qt/PySide6 notices, and the Inno Setup commercial-use
  position. Record this in `LEGAL_REVIEW.md` and change `Status` to `PASS`
  only after authorized review.
