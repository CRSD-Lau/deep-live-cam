# Windows Release Checklist

Use this checklist for every public Windows release. The current release is
`2.2.0` and contains two mutually exclusive runtime profiles:

- NVIDIA/CUDA installer
- AMD/Intel DirectML portable ZIP

## Source and version

- [ ] Work from a clean release branch based on the production branch.
- [ ] `modules/metadata.py`, installer defaults, workflow defaults, README,
  changelog, and release notes use the intended version.
- [ ] `CHANGELOG.md` describes user-visible changes and links the comparison.
- [ ] The full automated test suite passes.
- [ ] The release commit is merged before tagging.
- [ ] The annotated tag resolves to the exact release commit.

## CUDA installer

- [ ] Build with `build\windows\build_windows.ps1 -Accelerator Cuda`.
- [ ] Run `build\windows\test_packaged_runtime.ps1 -Accelerator Cuda -RequireAccelerator`.
- [ ] Run `build\windows\test_environment.ps1 -RequireFfmpeg -RequireCuda`.
- [ ] Package with `build\windows\package_installer.ps1 -AppVersion 2.2.0`.
- [ ] Run `build\windows\test_installer.ps1 -AppVersion 2.2.0`.
- [ ] Confirm the installer and `.sha256` sidecar match.
- [ ] Confirm silent uninstall preserves `%LOCALAPPDATA%\DeepLiveCamStudio\models`.

## DirectML portable build

- [ ] Build with `build\windows\build_windows.ps1 -Accelerator DirectML`.
- [ ] Package with `build\windows\package_portable.ps1 -AppVersion 2.2.0 -Accelerator DirectML`.
- [ ] Confirm the strict provider probe reports `DmlExecutionProvider`.
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
- [ ] Package source from the exact tag:

  ```powershell
  powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.0 -GitRef v2.2.0
  ```

- [ ] Confirm the source manifest reports `Archive mode: git-ref` and records
  the forbidden-model scan.
- [ ] Attach the complete corresponding source ZIP, hash, and manifest.
- [ ] Keep AGPL-3.0 attribution and model-license limitations visible in the
  release notes.
- [ ] Do not bundle ffmpeg or model weights without a separate redistribution
  review.

## Manual release gates

- [ ] `CLEAN_VM_VERIFICATION.md` is `Status: PASS` with no unchecked items.
- [ ] `OBS_VIRTUAL_CAMERA_VERIFICATION.md` is `Status: PASS` with no unchecked
  items and covers the final runtime paths.
- [ ] `LEGAL_REVIEW.md` is `Status: PASS` for the intended release and records
  the DirectML dependency delta.
- [ ] `tools\summarize_manual_release_gates.py --strict` passes.

## Final release gate

Run the strict CUDA installer and source gate:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.2.0 -GitRef v2.2.0 -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady
```

Assemble the combined asset set after the DirectML ZIP is available:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\assemble_release_assets.ps1 -AppVersion 2.2.0 -PortableDir build\windows\portable -RequireGitRefSource
python tools\validate_windows_release_artifacts.py --app-version 2.2.0 --release-assets-dir build\windows\release-assets\2.2.0 --require-git-ref-source --require-directml-portable
```

## GitHub Release

- [ ] Create release `v2.2.0` from the annotated tag, initially as a draft.
- [ ] Upload every file listed in `RELEASE_ASSETS.md`.
- [ ] Verify live GitHub asset digests against `SHA256SUMS.txt`.
- [ ] Download the public CUDA installer and DirectML ZIP and re-run their
  smoke/provider checks.
- [ ] Publish only after the public-download checks pass.
- [ ] Update README links, close resolved issues, and thank external testers.
- [ ] Preserve a rollback path to `v2.1.9` and record any deferred risks.
