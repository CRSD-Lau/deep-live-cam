# Release Cutover Plan

This plan turns the current locally verified Windows release candidate into a
publishable GitHub Release. It is intentionally separate from the installed
release documents so installer hashes are not made stale by handoff notes.

## Current State

- The Windows installer build, package, smoke-test, and artifact-validation
  path passes locally.
- The installer and git-ref source archive hashes are recorded in their
  generated `.sha256` sidecars and in the assembled `RELEASE_ASSETS.md`.
- The current source archive uses `git-ref` mode for commit
  `66f90c00fe171fde65305a960caff0c8fbff4e9e`.
- The public-release gate remains blocked until the manual evidence files pass.

## Release Branch Strategy

Use a dedicated release branch or worktree before tagging:

```powershell
git switch -c codex/windows-installer-release
```

Do not tag directly from the current mixed dirty state. First divide changes
into these buckets.

## Required Packaging And Compliance Set

These files are required by `build/windows/package_source.ps1` for the public
corresponding-source archive:

- `LICENSE`
- `README.md`
- `COMPLIANCE.md`
- `THIRD_PARTY_NOTICES.md`
- `RELEASE_CHECKLIST.md`
- `RELEASE_REPORT.md`
- `RELEASE_SOURCE_PREP.md`
- `CLEAN_VM_VERIFICATION.md`
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md`
- `LEGAL_REVIEW.md`
- `MODEL_DOWNLOAD_VERIFICATION.md`
- `PROCESSING_VERIFICATION.md`
- `docs/OBS_VIRTUAL_CAMERA.md`
- `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md`
- `LICENSES/MODEL_LICENSE_AUDIT.md`
- `LICENSES/PYTHON_DEPENDENCIES.md`
- `LICENSES/README.md`
- `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`
- `LICENSES/THIRD_PARTY_LICENSES/`
- `.github/workflows/windows-release.yml`
- `DeepLiveCamStudio.pyw`
- `build/windows/`
- `tools/check_cuda_provider.py`
- `tools/check_obs_virtualcam.py`
- `tools/collect_third_party_license_files.py`
- `tools/generate_python_dependency_licenses.py`
- `tools/prune_windows_dist.py`
- `tools/generate_windows_bundle_manifest.py`
- `tools/generate_windows_release_verification.py`
- `tools/install_windows_desktop_app.ps1`
- `tools/validate_windows_release_artifacts.py`
- `requirements.txt`
- `run.py`
- `modules/core.py`
- `modules/globals.py`
- `modules/execution_providers.py`
- `modules/desktop_launcher.py`
- `modules/model_manager.py`
- `modules/paths.py`
- `modules/ui.py`
- `modules/utilities.py`
- focused release tests for model setup, image uploads, artifact validation, and release verification

Also include the runtime files needed for the installer and packaged behavior:

- `DeepLiveCamStudio.pyw`
- `modules/core.py`
- `modules/globals.py`
- `modules/execution_providers.py`
- `modules/desktop_launcher.py`
- `modules/ui.py`
- `modules/utilities.py`
- model-consuming frame processor modules changed for packaged/user model paths
- `run.py`
- `requirements.txt`
- focused tests for model setup, release verification, and WebP/AVIF uploads

Review `.gitignore` changes with the same care, because ignored build outputs,
model files, and installer artifacts affect source-archive hygiene.

## Mixed-Scope Changes To Resolve Before Tagging

The current workspace also contains broader runtime and quality changes. Before
creating a release tag, choose one of these paths for each item:

- commit it as an intentional runtime change with tests;
- move it to a separate branch/worktree for later;
- leave it uncommitted and do not include it in the release tag.

Mixed-scope areas visible in `git status` include:

- `modules/compositing/`
- `modules/tracking/`
- `modules/expression_*`
- `modules/visual_qa*`
- `modules/benchmark_report.py`
- `modules/pipeline_metrics.py`
- face-processing behavior changes beyond packaged path resolution
- matching tests for those broader runtime features

Do not use `-FromWorkingTree` to publish around this decision. A dirty-tree
archive is useful evidence only; it is not the AGPL corresponding source for a
binary GitHub Release.

## Cutover Procedure

1. Review and stage only the intended release files.

For a dry run of the release-owned staging set:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\prepare_release_staging.ps1
```

After reviewing `RELEASE_CUTOVER_STATUS.md`, stage only the release-owned set:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\prepare_release_staging.ps1 -Stage
```
2. Check the dirty-tree split:

```powershell
venv\Scripts\python.exe tools\check_windows_release_cutover.py --repo-root . --output RELEASE_CUTOVER_STATUS.md
```

This command reports release-owned dirty paths, mixed-scope paths that need an
explicit include/exclude decision, unknown dirty paths, and the remaining manual
evidence gates. It also writes `RELEASE_CUTOVER_STATUS.md` as persistent release
evidence. `build/windows/run_release_checks.ps1` also regenerates this report
before packaging source; strict publish runs add `--strict` and fail on any
remaining blocker.

3. Run focused tests:

```powershell
venv\Scripts\python.exe -m pytest tests\test_validate_windows_release_artifacts.py tests\test_windows_release_scripts.py tests\test_windows_release_cutover.py tests\test_windows_release_verification.py tests\test_image_upload_formats.py tests\test_model_manager.py
```

4. Rebuild and verify the release candidate:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -UseExistingVenv -DraftWorkingTreeSource
```

5. Complete and mark manual evidence files only after real checks pass:

- `CLEAN_VM_VERIFICATION.md`
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md`
- `LEGAL_REVIEW.md`

Use the evidence helpers for the repeatable subsets:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_clean_vm_gate.ps1 -AppVersion 2.1.5
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_obs_virtualcam_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_legal_review_gate.ps1 -AppVersion 2.1.5
```

6. Commit the release source and evidence.
7. Confirm the tree is clean:

```powershell
git status --short
```

8. Tag the exact release commit:

```powershell
git tag v2.1.5
```

9. Generate clean corresponding source from the tag:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef v2.1.5
```

10. Run the strict publish gate on suitable release-test machines:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -UseExistingVenv -GitRef v2.1.5 -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady
```

The strict publish gate intentionally rejects `-AllowDirtySource`,
`-DraftWorkingTreeSource`, and `-SkipSourceArchive`. Those flags are useful for
release-candidate diagnostics only, never for the final public AGPL release.

11. Attach the installer, installer `.sha256`, source archive, source archive
    `.sha256`, source manifest, and `RELEASE_VERIFICATION.md` to the GitHub
    Release.

## Publish Blockers

Do not publish until all of these are true:

- `RELEASE_VERIFICATION.md` says `Ready to publish without remaining manual gates: YES`.
- `tools/validate_windows_release_artifacts.py --require-git-ref-source` passes.
- The source archive manifest says `Archive mode: git-ref`.
- The GitHub Release links to the exact source tag or commit.
- The final legal reviewer has approved the documented model, dependency, AGPL,
  LGPL/GPL, pyvirtualcam, Qt/PySide6, and Inno Setup positions.
