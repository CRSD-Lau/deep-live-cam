# Release Source Preparation

This repository currently has a locally verified Windows installer, but the
public GitHub Release gate is still blocked until the mixed-scope dirty
worktree is resolved and the manual gates are completed.

## Current Local Artifact State

- Installer: `build/windows/installer/DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: see `build/windows/installer/DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`
- Public-release source archive: `build/windows/installer/DeepLiveCamStudio-2.1.5-source-c104da94c708.zip`
- Public-release source SHA-256: see `build/windows/installer/DeepLiveCamStudio-2.1.5-source-c104da94c708.zip.sha256`
- Source ref: `c104da94c70814abf19ad9b8de71ebdfa2a742cd`
- Current release verdict: local automation passed, public release not yet ready.

Do not hard-code installer or source archive hashes in this installed document.
The installer and source archive sidecars, plus `RELEASE_VERIFICATION.md`, are
the authoritative hash records for the current artifact set.

Older draft source archives may still exist in `build/windows/installer/` from
local testing. They are useful traceability evidence, but the public GitHub
Release should use the git-ref archive above or a later clean tag archive.

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
- `RELEASE_REPORT.md`
- `RELEASE_NOTES_TEMPLATE.md`
- `RELEASE_VERIFICATION.md`
- `MODEL_DOWNLOAD_VERIFICATION.md`
- `PROCESSING_VERIFICATION.md`
- `docs/OBS_VIRTUAL_CAMERA.md`

## Mixed-Scope Files Requiring Human Review

The current worktree also contains large modified or untracked application
modules that may be unrelated to the Windows installer and licensing goal. Do
not include them in a public release commit until their intent and test coverage
are confirmed.

Examples currently visible in `git status` include:

- `modules/processors/frame/face_masking.py`
- `modules/face_analyser.py`
- `modules/compositing/`
- `modules/tracking/`
- `modules/expression_*`
- `modules/visual_qa*`
- `modules/benchmark_report.py`
- `modules/pipeline_metrics.py`
- matching tests for those broader runtime features

If these changes are intended for the same release, review and commit them as a
separate feature/runtime commit before creating the release tag. If they are
not intended for this release, move them aside before the packaging commit so
the corresponding-source archive matches only the released installer.

## Clean Release Procedure

After the intended release files are reviewed and committed:

```powershell
git status --short
```

The output must be empty before final publish verification. A git-ref source
archive can be created from a specific commit while the developer worktree is
dirty, but public release signoff should still happen from a clean release tag
or clean release worktree.

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
