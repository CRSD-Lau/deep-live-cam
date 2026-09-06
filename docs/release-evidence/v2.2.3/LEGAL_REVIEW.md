# Final Legal and Compliance Review

Status: PASS

Release: `2.2.3`

This is a release-management record, not legal advice. Publisher acceptance is
recorded by project owner Neil Mitchell; exact final hashes and source refs are
kept in the release asset manifest rather than embedded in installed files.

## Required review items

- [x] AGPL-3.0 corresponding source is attached for the exact release tag.
- [x] Original Deep-Live-Cam attribution is preserved.
- [x] Release notes describe source availability and AGPL obligations.
- [x] Runtime downloads include the required licence and compliance files.
- [x] No model/checkpoint files are included in either runtime download.
- [x] Model sources, licence limitations, and checksums remain visible before
  user-initiated download.
- [x] InsightFace/inswapper, GPEN, and GFPGAN redistribution remains excluded.
- [x] PySide6/shiboken6 and GPL-family dependency metadata retain the accepted
  `2.1.9` distribution posture and notices.
- [x] Inno Setup publisher/commercial-use posture remains accepted.
- [x] ffmpeg is not bundled.
- [x] DirectML dependency and binary redistribution delta is documented.
- [x] PyTorch CUDA-wheel licence, notice, and package metadata accompany the
  selected CUDA 12/cuDNN 9 runtime DLLs bundled in the NVIDIA installer.

## 2.2.0 delta review

- The new runtime dependency is `onnxruntime-directml==1.23.0`; its bundled
  metadata and package licence are included under
  `LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/`.
- ONNX Runtime DirectML uses the same MIT-licensed ONNX Runtime project and
  does not introduce model weights.
- The portable ZIP contains application/runtime binaries only and is scanned
  for `.onnx`, `.pth`, `.safetensors`, `models/`, and `checkpoints/` entries.
- DirectML and CUDA are shipped separately so mutually exclusive ONNX Runtime
  packages are not combined into one environment.
- The scikit-learn `vcomp140.dll` packaging fix restores a dependency that was
  already part of the built runtime; it does not add a new model or content
  source.
- The clean CUDA build installs pinned `torch==2.11.0+cu128` only as the source
  for the runtime DLL allow-list. The Python `torch` package is excluded from
  the installer, while its `LICENSE`, `NOTICE`, and metadata remain bundled.

## 2.2.1 delta review

- The reviewed runtime refresh updates ONNX Runtime GPU to 1.24.3 and other
  already-shipped Python dependencies; regenerated locks and licence snapshots
  remain part of both release profiles.
- The DirectML package, model-download policy, source-distribution scope, and
  external binary families are unchanged from 2.2.0.
- PyTorch remains a build-only CUDA DLL source at 2.11.0+cu128 and is not
  imported or shipped as a Python runtime. The two dismissed Torch advisories
  therefore remain documented as not used rather than open release alerts.
- UI/frame-pipeline refactoring and repository-administration changes add no
  model weights, codecs, or separately licensed binary payloads.

## 2.2.2 delta review

- ONNX Runtime GPU moves from the unavailable 1.24.3 wheel to its compatible
  1.24.4 patch; the existing MIT licence remains bundled and the regenerated
  dependency inventory records the exact shipped package.
- Build-only updates to pip, wheel, PyInstaller, pip-tools, and Ruff do not add
  a new runtime dependency family or model payload.
- Stable-directory migration, legacy-install cleanup, and isolated installer
  testing change Windows packaging behavior only. User models remain external
  and neither release profile gains model/checkpoint files.
- CUDA and DirectML remain separate downloads with exact corresponding source,
  hashes, notices, and the previously accepted runtime licence posture.

## 2.2.3 delta review

- The Preview autoplay and playback changes use the already-shipped Qt,
  OpenCV, NumPy, face-analysis, and frame-processor paths.
- No dependency version, licence family, codec, external binary, model source,
  model weight, or redistribution scope changes in this patch.
- CUDA and DirectML remain separate downloads with the same model-exclusion,
  notices, exact corresponding source, manifest, and hash requirements.
- The Radeon RX 6900 XT result is functional hardware evidence only; it does
  not add redistributed content or change the accepted runtime licence posture.

Generate the final evidence packet with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_legal_review_gate.ps1 -AppVersion 2.2.3
```
