# Windows Release Checklist

Use this checklist for every Windows installer release.

## Build

- [ ] Confirm working tree contains only intentional release changes.
- [ ] Confirm no model/checkpoint files are staged or included in `dist\DeepLiveCamStudio`.
- [ ] Commit generated release evidence before source packaging, including `LICENSES/PYTHON_DEPENDENCIES.md`, `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`, and `LICENSES/THIRD_PARTY_LICENSES/`.
- [ ] Review `RELEASE_SOURCE_PREP.md` and resolve mixed-scope dirty worktree changes before tagging.
- [ ] Confirm `CLEAN_RELEASE_WORKTREE_VERIFICATION.md` matches the final release commit/tag.
- [ ] For the standard local release gate, run `powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>`.
- [ ] For the final publish gate, run `powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit> -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady`.
- [ ] For CI release-candidate builds, confirm `.github/workflows/windows-release.yml` completed the same non-strict `run_release_checks.ps1` gate and uploaded `RELEASE_VERIFICATION.md`.
- [ ] Do not treat GitHub-hosted CI artifacts as publish-approved unless a separate strict publish gate has passed on appropriate release-test machines.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\clean_build.ps1`.
- [ ] Run `python tools\generate_python_dependency_licenses.py --output LICENSES\PYTHON_DEPENDENCIES.md` after installing release dependencies.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1`.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\test_packaged_runtime.ps1`.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1` on the target test machine.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\package_installer.ps1 -AppVersion 2.1.5`.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\test_installer.ps1 -AppVersion 2.1.5`.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>`.
- [ ] Verify installer exists at `build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe`.
- [ ] Verify SHA-256 sidecar exists at `build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256`.
- [ ] Confirm sidecar matches `Get-FileHash build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe -Algorithm SHA256`.
- [ ] Verify corresponding source archive and `.sha256` sidecar exist under `build\windows\installer`.
- [ ] Verify corresponding source archive `.manifest.md` exists under `build\windows\installer`.
- [ ] Confirm `package_source.ps1` reported source archive content verification passed.
- [ ] Run `python tools\validate_windows_release_artifacts.py --app-version 2.1.5 --require-git-ref-source` before publishing.
- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\assemble_release_assets.ps1 -AppVersion 2.1.5 -RequireGitRefSource`.
- [ ] Confirm the source archive manifest says `Archive mode: ` followed by `git-ref` for public GitHub Releases. `draft-working-tree` archives are for local traceability only.
- [ ] Review generated `RELEASE_VERIFICATION.md` and confirm no automated evidence item unexpectedly failed.
- [ ] Confirm manual gate evidence files remain `PENDING` until their gate is actually complete: `CLEAN_VM_VERIFICATION.md`, `OBS_VIRTUAL_CAMERA_VERIFICATION.md`, and `LEGAL_REVIEW.md`.

## Installer smoke test

- [ ] Local automated installer smoke test passes with `build\windows\test_installer.ps1`.
- [ ] Install on a clean Windows x64 VM without admin rights.
- [ ] Run `build\windows\verify_clean_vm_gate.ps1` on the clean Windows x64 VM and attach or summarize its generated evidence.
- [ ] Record clean VM results in `CLEAN_VM_VERIFICATION.md` and set `Status: PASS` only if every required check passes.
- [ ] Confirm Start menu shortcut launches.
- [ ] Confirm optional desktop shortcut works when selected.
- [ ] Confirm uninstall removes app files.
- [ ] Confirm local automated smoke test preserves a sentinel file in `%LOCALAPPDATA%\DeepLiveCamStudio\models` during silent uninstall.
- [ ] Confirm interactive uninstall asks before removing `%LOCALAPPDATA%\DeepLiveCamStudio\models`.

## Runtime test

- [ ] Local packaged runtime preflight passes with `build\windows\test_packaged_runtime.ps1`.
- [ ] Launch GUI on a fresh install.
- [ ] Run `DeepLiveCamStudioCLI.exe --download-models` and review the model license prompt.
- [ ] Verify downloaded model checksums pass.
- [ ] Review `MODEL_DOWNLOAD_VERIFICATION.md` from the release environment, if present, and confirm it was regenerated for the final release candidate.
- [ ] Confirm missing-model failures show a clear setup message.
- [ ] Confirm `switch_states.json` is written under `%LOCALAPPDATA%\DeepLiveCamStudio`.
- [ ] Confirm desktop logs are written under `%LOCALAPPDATA%\DeepLiveCamStudio\logs`.

## Processing test

- [ ] Run `powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1 -RequireFfmpeg` on the video-processing test machine.
- [ ] CPU fallback test with a small image and a short video.
- [ ] CUDA machine test with `powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1 -RequireCuda`.
- [ ] DirectML or CPU-only fallback test on a non-NVIDIA Windows machine.
- [ ] OBS Virtual Camera test with OBS installed and virtual camera enabled: `powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1 -RequireObsVirtualCam`.
- [ ] Run `build\windows\verify_obs_virtualcam_gate.ps1` on the OBS test machine and attach or summarize its generated evidence.
- [ ] Record OBS results in `OBS_VIRTUAL_CAMERA_VERIFICATION.md` and set `Status: PASS` only if every required check passes.
- [ ] Confirm live preview still opens and stops cleanly.

## Compliance

- [ ] Include `LICENSE`, `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, `RELEASE_CHECKLIST.md`, `RELEASE_REPORT.md`, and `RELEASE_SOURCE_PREP.md` in the installed app.
- [ ] Include `LICENSES/MODEL_LICENSE_AUDIT.md` in the installed app.
- [ ] Include `LICENSES/PYTHON_DEPENDENCIES.md` in the installed app.
- [ ] Include generated `LICENSES/WINDOWS_BUNDLE_MANIFEST.md` in the installed app.
- [ ] Include `MODEL_DOWNLOAD_VERIFICATION.md` and `PROCESSING_VERIFICATION.md` in the installed app.
- [ ] Include `docs/OBS_VIRTUAL_CAMERA.md` in the installed app.
- [ ] Link the GitHub Release to the exact source tag or commit.
- [ ] Confirm complete corresponding source includes build and installer scripts.
- [ ] Confirm corresponding source archive contains `LICENSE`, `COMPLIANCE.md`, `THIRD_PARTY_NOTICES.md`, `RELEASE_SOURCE_PREP.md`, `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md`, `LICENSES/THIRD_PARTY_LICENSES/`, `LICENSES/MODEL_LICENSE_AUDIT.md`, packaging scripts, and model-download source.
- [ ] Confirm `package_source.ps1` was run against the exact tag or commit used for the installer and not against a workspace-only dirty state.
- [ ] Confirm corresponding source archive contains no `.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, or model-cache entries.
- [ ] Re-run dependency license scan with `tools\generate_python_dependency_licenses.py` and update `THIRD_PARTY_NOTICES.md` if newly surfaced risks need summary treatment.
- [ ] Re-check Hugging Face model repository licenses and checksums.
- [ ] Review `namex` and any other `UNKNOWN` or non-SPDX dependency metadata before publishing.
- [ ] Confirm no `.onnx`, `.pth`, `.safetensors`, checkpoint, or model cache files are bundled.
- [ ] Confirm generated `LICENSES/WINDOWS_BUNDLE_MANIFEST.md` reports zero dev-only sample/test payload paths.
- [ ] Review `pyvirtualcam` GPLv2 metadata compatibility before publishing the binary.
- [ ] Review `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` and confirm the release path satisfies bundled LGPL/GPL-family obligations.
- [ ] Run `build\windows\verify_legal_review_gate.ps1` and attach or summarize its generated reviewer packet.
- [ ] Confirm `LICENSES/THIRD_PARTY_LICENSES/` was regenerated from the release build environment and includes high-attention TensorFlow, ONNX Runtime, OpenCV, Qt/PySide, pyvirtualcam, and model-safety dependency notices in the installed payload.
- [ ] Review any ffmpeg redistribution plan before bundling ffmpeg.
- [ ] Confirm the release publisher's Inno Setup commercial-license position before production/commercial distribution.
- [ ] Record final compliance/legal conclusions in `LEGAL_REVIEW.md` and set `Status: PASS` only after authorized review.

## GitHub Release

- [ ] Attach installer `.exe`.
- [ ] Attach installer `.sha256`.
- [ ] Attach or link source archive for the exact release.
- [ ] Attach source archive `.sha256`.
- [ ] Attach source archive `.manifest.md`.
- [ ] Attach or review `RELEASE_ASSETS.md` from `build\windows\release-assets\2.1.5`.
- [ ] Attach or quote `RELEASE_VERIFICATION.md`.
- [ ] Use `RELEASE_NOTES_TEMPLATE.md` and replace placeholders with exact version, commit, hashes, and source URL.
- [ ] Include AGPL-3.0 source availability notice in release notes.
- [ ] Include model exclusion notice and setup command in release notes.
- [ ] Include known legal risks for model redistribution.
