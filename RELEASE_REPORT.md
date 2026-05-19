# Windows Installer Release Report

Report generated from the local Windows packaging workspace and refreshed on 2026-05-19.

## Packaging Approach

Chosen approach: PyInstaller onedir application bundle wrapped by Inno Setup.

Why:

- PyInstaller can package the Python runtime and native Python dependencies without requiring users to install Python manually.
- Onedir packaging keeps native DLLs visible for audit and LGPL/GPL notice review.
- Inno Setup provides a standard Windows x64 installer, per-user install path, Start menu entries, optional desktop shortcut, uninstall support, and post-install launch support.
- Model files are intentionally kept external because model/checkpoint redistribution rights are not fully confirmed.

Alternatives considered:

- Nuitka: viable later for performance and potentially smaller output, but higher compiler/toolchain friction for this dependency set.
- NSIS: viable installer wrapper, but Inno Setup is simpler for per-user install, license screen, shortcut, and uninstall logic here.
- Briefcase/cx_Freeze: possible but less aligned with this app's native ML dependency shape than PyInstaller.

## Current Release Candidate

Current assembled GitHub Release asset folder:

```text
C:\Projects\deep-live-cam\build\windows\release-assets\2.1.5
```

The exact uploadable artifact names, source ref, sizes, and SHA-256 hashes are
recorded in the generated `RELEASE_ASSETS.md` manifest in that folder. Keep
hashes in generated release assets rather than in files bundled into the
installer; changing a bundled document changes the installer hash.

Current automated status:

- Focused packaging/runtime/compliance tests passed locally: `302 passed`.
- Clean checkout PyInstaller build for `cc4451c150da09d634c4aac2f1a4c017cdead634` passed.
- Packaged runtime smoke test passed from the clean checkout.
- Inno Setup installer build passed.
- Installer smoke test passed: silent install, installed CLI `--version`, and uninstall.
- `tools/validate_windows_release_artifacts.py --require-git-ref-source` passed against the current installer/source pair and assembled release-assets folder.
- `tools/summarize_manual_release_gates.py --strict` correctly fails until clean VM, OBS workflow, and legal review gates are completed.

Current publish status: not publish-approved. The engineering release candidate exists, but the GitHub Release remains blocked on the manual gates listed in `MANUAL_RELEASE_GATES.md`, `CLEAN_VM_VERIFICATION.md`, `OBS_VIRTUAL_CAMERA_VERIFICATION.md`, and `LEGAL_REVIEW.md`.

## Build Commands

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\clean_build.ps1
python tools\generate_python_dependency_licenses.py --output LICENSES\PYTHON_DEPENDENCIES.md
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1
powershell -ExecutionPolicy Bypass -File build\windows\test_packaged_runtime.ps1
powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1
powershell -ExecutionPolicy Bypass -File build\windows\package_installer.ps1 -AppVersion 2.1.5
powershell -ExecutionPolicy Bypass -File build\windows\test_installer.ps1 -AppVersion 2.1.5
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>
```

For the local release-gate wrapper, run:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>
```

This wrapper builds and smoke-tests the installer, packages corresponding
source, validates the installer/source artifact set, assembles
`build/windows/release-assets/2.1.5/`, and validates that curated upload folder.

For the final publish gate, use strict mode on appropriate release-test
machines so the command fails unless the installer evidence, clean Git-ref
source archive, and manual gate evidence are all complete:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit> -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady
```

To validate the uploadable artifact directory directly, run:

```powershell
python tools\validate_windows_release_artifacts.py --app-version 2.1.5 --require-git-ref-source
```

To assemble the exact GitHub Release upload set into a dedicated folder, run:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\assemble_release_assets.ps1 -AppVersion 2.1.5 -RequireGitRefSource
```

The assembled files are written under `build/windows/release-assets/2.1.5/`
with a generated `RELEASE_ASSETS.md` manifest listing the installer, installer
hash, git-ref source archive, source hash, source manifest, release notes
template, manual gate summary, and verification documents to upload or quote.

Validate the curated upload folder with:

```powershell
python tools\validate_windows_release_artifacts.py --app-version 2.1.5 --require-git-ref-source --release-assets-dir build\windows\release-assets\2.1.5
```

If using the existing local development virtual environment, pass:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -UseExistingVenv
```

## Installer Output

Current local installer:

```text
C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe
```

Current local SHA-256 sidecar:

```text
build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe.sha256
```

The sidecar is generated by `build/windows/package_installer.ps1` and is the authoritative local hash record for the installer. `RELEASE_ASSETS.md` records the uploadable artifact set, hashes, and exact source ref after the source archive is assembled. Confirm the sidecar matches before publishing:

```powershell
Get-FileHash build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe -Algorithm SHA256
```

## Corresponding Source Archive

GitHub Releases should attach or link corresponding source for the exact commit/tag used to build the installer.

The current validated git-ref source archive is the `DeepLiveCamStudio-2.1.5-source-*.zip` file listed in `RELEASE_ASSETS.md`. The matching `.zip.sha256` sidecar and `.manifest.md` are the authoritative hash and resolved-ref records. Before publishing, run `tools\validate_windows_release_artifacts.py --require-git-ref-source` against the exact upload directory.

Use:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>
```

The source archive script refuses a dirty working tree by default. This is intentional: AGPL source availability should match the exact binary release. If `-AllowDirty` is used for CI or local diagnostics, the script still archives only the selected Git ref; uncommitted files are not included.

For a draft installer built from a dirty local workspace, use:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -FromWorkingTree
```

That mode creates a `draft-working-tree` source archive from current tracked, modified, and untracked workspace files while excluding build outputs, virtual environments, runtime data, and model/checkpoint files. It is useful for local traceability only. Do not publish a `draft-working-tree` source archive as the public AGPL corresponding source for a GitHub Release; commit or tag the release and rerun the clean `-GitRef` source archive command.

The source archive script also verifies that the selected Git ref and resulting archive contain required corresponding-source files, including license/compliance documents, generated dependency evidence, the OBS virtual-camera guide, Windows build and installer scripts, and model-download source, and that the archive does not contain model/checkpoint entries such as `.onnx`, `.pth`, `.safetensors`, `models/`, or `checkpoints/`. It writes a source archive `.manifest.md` with the resolved ref, hash, required-entry checks, and forbidden model/checkpoint scan result. The generated `LICENSES/WINDOWS_BUNDLE_MANIFEST.md` is release evidence from the built payload and is checked in the workspace before source packaging. Commit generated release evidence, including `LICENSES/PYTHON_DEPENDENCIES.md`, `LICENSES/THIRD_PARTY_LICENSES/`, and `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`, before creating the final release tag or source archive.

Use `RELEASE_SOURCE_PREP.md` to resolve the current dirty-worktree source gate before tagging. Use `RELEASE_NOTES_TEMPLATE.md` as the release-notes starting point and replace all placeholders with exact release values.

Manual release gates are tracked in `CLEAN_VM_VERIFICATION.md`,
`OBS_VIRTUAL_CAMERA_VERIFICATION.md`, and `LEGAL_REVIEW.md`. These files use a
simple `Status: PENDING/PASS/FAIL` line that `RELEASE_VERIFICATION.md` reads.
Do not change a status to `PASS` until the matching manual gate has actually
been completed. The verifier also requires that no unchecked `- [ ]` checklist
rows remain in a manual evidence file before it marks that gate complete.

`CLEAN_RELEASE_WORKTREE_VERIFICATION.md` records the separate automated proof
that the release commit can be checked out in a clean detached worktree, used
to create the git-ref source archive without `-AllowDirty`, and validated by
the strict artifact checker. That evidence keeps the dirty developer workspace
separate from the release commit, but it does not replace the manual gates.

Use `tools/summarize_manual_release_gates.py` to produce a concise current
status of the three manual gates, including unchecked items and the latest
local evidence packets. `--strict` exits non-zero until all three gate files are
`Status: PASS` and have no unchecked checklist rows. `assemble_release_assets.ps1`
also writes this summary into the upload folder as `MANUAL_RELEASE_GATES.md`.

Automated subsets have been run locally and summarized in the gate files:

- Clean install smoke helper passed on Windows 11 Pro build `26200`.
- OBS virtual-camera helper sent frames to `OBS Virtual Camera` and verified CUDA/ONNX Runtime provider detection.
- Legal review packet generation completed for the current installer/source pair.

These are useful release evidence, but they do not replace the clean VM,
visual OBS workflow, or authorized legal-review signoffs.

## Files Changed For Packaging And Compliance

- `DeepLiveCamStudio.pyw`
- `.github/workflows/windows-release.yml`
- `build/windows/build_windows.ps1`
- `build/windows/assemble_release_assets.ps1`
- `build/windows/package_installer.ps1`
- `build/windows/test_packaged_runtime.ps1`
- `build/windows/test_environment.ps1`
- `build/windows/test_installer.ps1`
- `build/windows/run_release_checks.ps1`
- `build/windows/package_source.ps1`
- `build/windows/clean_build.ps1`
- `build/windows/deep_live_cam_studio.spec`
- `build/windows/installer.iss`
- `COMPLIANCE.md`
- `THIRD_PARTY_NOTICES.md`
- `RELEASE_CHECKLIST.md`
- `RELEASE_COMPLETION_AUDIT.md`
- `RELEASE_CUTOVER_PLAN.md`
- `RELEASE_REPORT.md`
- `RELEASE_SOURCE_PREP.md`
- `CLEAN_VM_VERIFICATION.md`
- `OBS_VIRTUAL_CAMERA_VERIFICATION.md`
- `LEGAL_REVIEW.md`
- `MODEL_DOWNLOAD_VERIFICATION.md`
- `PROCESSING_VERIFICATION.md`
- `RELEASE_NOTES_TEMPLATE.md`
- `docs/OBS_VIRTUAL_CAMERA.md`
- `LICENSES/README.md`
- `LICENSES/MODEL_LICENSE_AUDIT.md`
- `LICENSES/PYTHON_DEPENDENCIES.md`
- `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`
- `tools/check_cuda_provider.py`
- `tools/check_obs_virtualcam.py`
- `tools/generate_python_dependency_licenses.py`
- `tools/generate_windows_bundle_manifest.py`
- `tools/generate_windows_release_verification.py`
- `tools/install_windows_desktop_app.ps1`
- `tools/prune_windows_dist.py`
- `tools/summarize_manual_release_gates.py`
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
- `tests/test_image_upload_formats.py`
- `tests/test_model_manager.py`
- `tests/test_release_report.py`
- `tests/test_summarize_manual_release_gates.py`
- `tests/test_validate_windows_release_artifacts.py`
- `tests/test_windows_release_verification.py`
- `modules/core.py`
- `modules/globals.py`
- `modules/execution_providers.py`
- `modules/desktop_launcher.py`
- `modules/ui.py`
- `modules/utilities.py`
- model-consuming frame processor modules updated to use the packaged/user model path and shared image loader
- focused image-format tests under `tests/`

The repository also contains other unrelated or broader local changes. Confirm the final staged set before tagging.

## Dependencies Bundled

The PyInstaller bundle includes the Python runtime, application code, GUI/runtime assets, and native libraries collected from the active Windows environment. High-level bundled dependency families include:

- PySide6 / Qt for Python
- OpenCV
- ONNX Runtime GPU
- TensorFlow and opennsfw2 dependency path
- insightface runtime code
- NumPy, SciPy, scikit-image, scikit-learn, Pillow, requests, tqdm, protobuf, pyvirtualcam, pygrabber, and transitive dependencies
- Pillow WebP and AVIF codec modules

See `LICENSES/PYTHON_DEPENDENCIES.md` for the current dependency metadata snapshot.
See `LICENSES/MODEL_LICENSE_AUDIT.md` for the dated model-source audit used to justify excluding model files from the installer.
See `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` for high-attention LGPL/GPL-family obligations around bundled native libraries and Python packages.
See `LICENSES/THIRD_PARTY_LICENSES/` for collected high-attention package license files and metadata from the release build environment.
See `LICENSES/WINDOWS_BUNDLE_MANIFEST.md` for a generated manifest from the actual PyInstaller payload, including package metadata directories, native/binary file summaries, required release-file presence, and forbidden model/checkpoint scan results.
See `RELEASE_VERIFICATION.md` for the generated local release-evidence summary with installer hash status, manifest status, source archive status, and manual gates that still require human confirmation.

## Dependencies Not Bundled

- Python source virtual environments
- `torch`, `torchvision`, and `torchaudio` package directories
- test suite and pytest runtime
- Jupyter/IPython tooling
- model/checkpoint files
- ffmpeg/ffprobe
- OBS Studio / OBS Virtual Camera
- NVIDIA driver, CUDA, cuDNN, and TensorRT system runtimes

PyInstaller warnings currently show missing TensorRT DLL dependencies (`nvinfer_10.dll`, `nvonnxparser_10.dll`) for the TensorRT provider. CUDA provider was detected locally; TensorRT provider should be treated as optional unless the target machine has matching NVIDIA TensorRT runtime installed.

## Model Files

Bundled model files: none.

Excluded model/checkpoint patterns:

- `*.onnx`
- `*.pth`
- `*.safetensors`

The current bundle scan found no model/checkpoint files under `dist\DeepLiveCamStudio`.

The downloader command is:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

The downloader presents source URLs, license notes, and SHA-256 checksums before downloading into:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

## License Obligations Found

- Deep-Live-Cam is AGPL-3.0. Binary distribution requires complete corresponding source for the exact release, including packaging scripts and local modifications.
- Release notes must preserve attribution to the original Deep-Live-Cam project and link to the exact source tag/commit.
- PySide6/shiboken6 use LGPL/GPL options. Preserve notices and keep a defensible LGPL compliance path.
- `cv2_enumerate_cameras` metadata includes GPL-3.0 text.
- `pyvirtualcam` metadata reports GPLv2 classifier; review compatibility before public binary release.
- TensorFlow, ONNX Runtime, OpenCV, NumPy/SciPy, Qt, and other native dependencies carry notice obligations.
- Model licenses are separate from application code and are not assumed redistributable.
- Inno Setup is used as the installer build tool. Current JR Software pages request commercial users purchase an Inno Setup commercial license; confirm the publisher's license position before production/commercial distribution.

## Remaining Legal Risks

- `inswapper` model files are mirrored in a Hugging Face repo labeled GPL-3.0, but InsightFace model-use history includes non-commercial/research restrictions. Do not bundle without legal review.
- GPEN upscaler model mirror states non-commercial, academic, and educational use only. Do not bundle in a general-purpose installer without permission.
- `gfpgan-1024.onnx` provenance should be verified before redistribution, even though upstream GFPGAN code is Apache-2.0.
- Dependency metadata is not a substitute for full legal review. `namex` currently reports `UNKNOWN` metadata in the local snapshot.
- LGPL/GPL obligations for native GUI/runtime libraries should be reviewed before public binary distribution. The release now includes `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` as an explicit checklist for PySide6/shiboken6, easydict, cv2_enumerate_cameras, pyvirtualcam, and native DLL notice handling.
- Inno Setup commercial-license expectations are a publisher-side release-tool consideration for commercial production use.

## Verification Completed Locally

- Focused WebP/AVIF image upload tests passed.
- Packaged CLI `--version` returned exit code `0`.
- Packaged CLI `--download-models` displays model source/license/checksum notes and cleanly cancels without consent in a non-interactive shell.
- Real model download verification passed on 2026-05-18 using `DLC_MODELS_DIR` pointed at a temporary folder outside the repository. All five configured model URLs downloaded successfully and matched their SHA-256 checksums. Evidence is recorded in `MODEL_DOWNLOAD_VERIFICATION.md`; the temporary model files were deleted afterward.
- Packaged CPU image processing, CPU short-video processing, and CUDA image processing with external CUDA/cuDNN runtime DLLs on `PATH` passed on 2026-05-18. Evidence is recorded in `PROCESSING_VERIFICATION.md`; the temporary model/media files were deleted afterward.
- The first packaged processing run exposed a missing PyInstaller dynamic import for `modules.processors.frame`; `build/windows/deep_live_cam_studio.spec` now collects that submodule tree so packaged frame processors such as `face_swapper` are included.
- `build/windows/test_packaged_runtime.ps1` verifies required release docs, no bundled model/checkpoint files, `_internal\torch` absence, WebP/AVIF codec files, `--version`, and `--download-models` cancellation behavior for the packaged `dist` bundle.
- Current packaged runtime preflight passed against a clean-checkout `dist\DeepLiveCamStudio` built from `cc4451c150da09d634c4aac2f1a4c017cdead634`.
- `build/windows/test_environment.ps1` consolidates ffmpeg/ffprobe, CUDA provider, and OBS/virtual-camera preflight checks. Strict target-machine gates are available with `-RequireFfmpeg`, `-RequireCuda`, and `-RequireObsVirtualCam`.
- Local environment preflight passed: ffmpeg and ffprobe were found on PATH, CUDAExecutionProvider loaded for an ONNX probe session on an NVIDIA GeForce RTX 4070, and OBS active-output testing was skipped because `-RequireObsVirtualCam` was not requested.
- `build/windows/package_source.ps1` now validates that the selected Git ref contains required AGPL release files before archive creation, then validates archive contents for forbidden model/checkpoint entries before writing the source hash sidecar and source archive manifest.
- `build/windows/package_source.ps1` also has a `-FromWorkingTree` draft mode for local dirty-worktree traceability; generated manifests label this as `draft-working-tree` so it is not mistaken for a clean public-release source archive.
- `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` is included in the packaged and installed payload and is required by packaged-runtime, installer-smoke, release-verification, and source-archive checks.
- `tools/collect_third_party_license_files.py` collects high-attention package license files into `LICENSES/THIRD_PARTY_LICENSES/`, including TensorFlow third-party notices, ONNX Runtime, OpenCV, ONNX, opennsfw2, Qt/PySide, and pyvirtualcam evidence, and release checks now require those files in the packaged and installed payload.
- `tools/prune_windows_dist.py` removes known dependency sample/test folders from the Windows PyInstaller payload, and packaged-runtime, installer-smoke, and bundle-manifest checks now verify those paths stay absent.
- `.github/workflows/windows-release.yml` now invokes the same non-strict `run_release_checks.ps1` wrapper as the local release-candidate path, so CI exercises the packaged runtime preflight, environment preflight, installer packaging, installer smoke test, hash verification, and source archive packaging through one gate. It also runs the strict verifier as a negative guard so hosted CI artifacts are not mistaken for publish-approved releases; final approval still requires the documented clean VM, OBS, legal, and strict local publish gates.
- `tools/generate_windows_release_verification.py` writes `RELEASE_VERIFICATION.md` at the end of the release gate so release evidence is available as a durable artifact instead of only console output.
- `tools/validate_windows_release_artifacts.py` verifies the uploadable release artifact set, including installer/source hash sidecars, source manifest, forbidden source model/checkpoint entries, and required release-verification sections.
- Latest local release-candidate pass rebuilt from a clean checkout, smoke-tested the packaged runtime, built the installer, smoke-tested the installer, created a git-ref source archive, and validated the uploadable artifact set.
- `RELEASE_ASSETS.md`, the generated `.sha256` sidecars, and the source archive manifest are the authoritative hash records for the latest local artifact set.
- Bundle scan found no `.onnx`, `.pth`, or `.safetensors` files.
- Bundle scan confirmed `_internal\torch` is absent.
- `LICENSE`, `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, `RELEASE_CHECKLIST.md`, and `LICENSES/PYTHON_DEPENDENCIES.md` are staged into the installer payload.
- `LICENSES/MODEL_LICENSE_AUDIT.md` is staged into the installer payload.
- `LICENSES/WINDOWS_BUNDLE_MANIFEST.md` is generated from the packaged payload and staged into the installer.
- `build/windows/test_installer.ps1` installs the generated `.exe` to a temporary directory, verifies required installed files, checks no bundled model/checkpoint files, runs `DeepLiveCamStudioCLI.exe --version`, verifies silent uninstall preserves a sentinel file in `%LOCALAPPDATA%\DeepLiveCamStudio\models`, and uninstalls with a timeout guard.
- Current installer smoke test passed against `DeepLiveCamStudio-2.1.5-x64-setup.exe` after the silent-uninstall model-preservation fix.
- The generated `.sha256` sidecar matches `Get-FileHash` for the installer.
- Latest local release verification summary was generated at `RELEASE_VERIFICATION.md` and reports local installer automation, real model download verification, and packaged CPU/CUDA processing verification as passing/recorded.
- Manual gate templates now exist for clean VM testing, OBS virtual-camera testing, and final legal/compliance review. They remain `PENDING` until the checks are performed and are reflected in `RELEASE_VERIFICATION.md`.

## Manual Checks Required Before Publishing

- Install on a clean Windows x64 VM without admin rights. The local smoke script is useful evidence, but it is not a substitute for a fresh VM test.
- Fill out `CLEAN_VM_VERIFICATION.md` and set `Status: PASS` only after the clean VM test passes.
- Confirm Start menu shortcut, optional desktop shortcut, launch, and uninstall behavior.
- Confirm uninstall asks before deleting downloaded models.
- Re-run model download with user consent and verify checksums on the final release candidate or release VM.
- Re-run CPU fallback processing on the final release candidate or release VM.
- Re-run CUDA processing on a supported NVIDIA release-test machine with external runtime libraries installed.
- Test non-NVIDIA Windows fallback behavior.
- Test OBS Virtual Camera workflow with OBS installed.
- Fill out `OBS_VIRTUAL_CAMERA_VERIFICATION.md` and set `Status: PASS` only after the OBS workflow passes.
- Confirm ffmpeg/ffprobe instructions match the final release policy.
- Run a final dependency license scan and legal review.
- Fill out `LEGAL_REVIEW.md` and set `Status: PASS` only after final authorized review.
- Confirm GitHub Release links to the exact source tag/commit and source archive.
