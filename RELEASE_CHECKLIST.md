---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Checklist

Use this checklist for every public Windows release. The release candidate is
`2.2.4` and contains two mutually exclusive runtime profiles:

- NVIDIA/CUDA installer
- AMD/Intel DirectML portable ZIP

Binary and corresponding-source commit: `753aab70c34ae585d525a06b9f7de2d721b7f491`.
The existing release remains a draft while final artifact or manual checks are pending.
Later documentation/evidence commits do not move this artifact commit or release tag.
Rollback release: `v2.2.3`.

## Source and version

- [ ] Work from a clean release branch based on the production branch.
- [ ] `modules/metadata.py`, installer defaults, workflow defaults, README,
  changelog, and release notes use the intended version.
- [ ] `CHANGELOG.md` describes user-visible changes and links the comparison.
- [ ] The full automated test suite passes.
- [ ] Both runtime build jobs and source packaging use one resolved, immutable
  commit SHA; verify the recorded binary/source provenance matches.
- [ ] The release commit is merged before tagging.
- [ ] The annotated tag resolves to the exact release commit.

## CUDA installer

- [ ] Build with `build\windows\build_windows.ps1 -Accelerator Cuda`.
- [ ] Run `build\windows\test_packaged_runtime.ps1 -Accelerator Cuda -RequireAccelerator`.
- [ ] Run `build\windows\test_environment.ps1 -RequireFfmpeg -RequireCuda`.
- [ ] Package with `build\windows\package_installer.ps1 -AppVersion 2.2.4`.
- [ ] Run `build\windows\test_installer.ps1 -AppVersion 2.2.4`.
- [ ] Confirm an existing 2.2.3 stable-directory installation upgrades in
  place; keep the registered 2.2.1 legacy-migration fixture passing.
- [ ] Test the exact final installer bytes in an isolated Windows environment;
  the test-GUID installer rebuilt by the migration fixture is separate evidence.
- [ ] Confirm the installer and `.sha256` sidecar match.
- [ ] Confirm silent uninstall preserves `%LOCALAPPDATA%\DeepLiveCamStudio\models`.

## DirectML portable build

- [ ] Build with `build\windows\build_windows.ps1 -Accelerator DirectML`.
- [ ] Package with `build\windows\package_portable.ps1 -AppVersion 2.2.4 -Accelerator DirectML`.
- [ ] Confirm the strict provider probe reports `DmlExecutionProvider`.
- [ ] Record the tested physical AMD adapter and its DirectML device index;
  do not infer AMD coverage from the default adapter or provider name alone.
- [ ] Confirm the ZIP contains `_internal/sklearn/.libs/vcomp140.dll`.
- [ ] Confirm the ZIP and `.sha256` sidecar match.
- [ ] Confirm the ZIP contains no `.onnx`, `.pth`, `.safetensors`, `models/`,
  or `checkpoints/` payloads.
- [ ] Test file Preview, Start Render, and Live Output on AMD hardware.

## Corresponding source and compliance

- [ ] Generate dependency licences from the final CUDA and DirectML
  environments.
- [ ] Confirm `LICENSES/THIRD_PARTY_LICENSES/` contains the CUDA and DirectML
  ONNX Runtime licences plus Qt, OpenCV, TensorFlow, ONNX, pyvirtualcam,
  cv2_enumerate_cameras, and other shipped dependencies.
- [ ] Confirm no model/checkpoint files are committed or distributed.
- [ ] Package source from the exact merged release commit:

  ```powershell
  powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.4 -GitRef 753aab70c34ae585d525a06b9f7de2d721b7f491
  ```

- [ ] Confirm the source manifest reports `Archive mode: git-ref` and records
  the forbidden-model scan.
- [ ] Attach the complete corresponding source ZIP, hash, and manifest.
- [ ] Keep AGPL-3.0 attribution and model-license limitations visible in the
  release notes.
- [ ] Do not bundle ffmpeg or model weights without a separate redistribution
  review.

## Manual release gates

- [ ] `CLEAN_VM_VERIFICATION.md` is `Status: PASS` for `2.2.4` with no unchecked items.
- [ ] `OBS_VIRTUAL_CAMERA_VERIFICATION.md` is `Status: PASS` with no unchecked
  items and covers the final `2.2.4` runtime paths and receiving application.
- [ ] `LEGAL_REVIEW.md` is `Status: PASS` for the intended release and records
  the packaging dependency delta and scoped build-only PyTorch exception.
- [ ] Model-download and processing evidence identifies `2.2.4`; previous
  releases' files or automated-subset reports do not establish a new PASS.
- [ ] `tools\summarize_manual_release_gates.py --app-version 2.2.4 --strict` passes.

## Final release gate

Run the strict CUDA installer and source gate in the release worktree before
freezing the final asset bytes. This command copies documents/licences,
repackages the installer, and regenerates reports/source; it is not a read-only
check of downloaded official artifacts. Keep later attestation-only changes
separate from the verified payload:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.2.4 -GitRef 753aab70c34ae585d525a06b9f7de2d721b7f491 -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady
```

Assemble the combined asset set after the DirectML ZIP is available:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\assemble_release_assets.ps1 -AppVersion 2.2.4 -PortableDir build\windows\portable -RequireGitRefSource
python tools\validate_windows_release_artifacts.py --app-version 2.2.4 --output-dir build\windows\release-assets\2.2.4 --release-assets-dir build\windows\release-assets\2.2.4 --require-git-ref-source --require-directml-portable
```

## GitHub Release

- [ ] Keep the existing `v2.2.4` release as a draft and verify its annotated tag resolves to the fixed binary/source commit.
- [ ] Upload every file listed in `RELEASE_ASSETS.md`.
- [ ] Verify live GitHub asset digests against `SHA256SUMS.txt`.
- [ ] Download the draft-hosted CUDA installer and DirectML ZIP and re-run their
  smoke/provider checks.
- [ ] Publish only after the draft-hosted download checks and all required gates pass; then verify public download availability and hashes.
- [ ] Update README links, close resolved issues, and thank external testers.
- [ ] Confirm no unexpected release-blocking issues, pull requests, Dependabot
  alerts, code-scanning alerts, or secret-scanning alerts remain; record
  unrelated queue items.
- [ ] Preserve a rollback path to `v2.2.3` and record any deferred risks.
