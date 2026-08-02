# Final Legal and Compliance Review

Status: PASS

Release: `2.2.0`

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

Generate the final evidence packet with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_legal_review_gate.ps1 -AppVersion 2.2.0
```
