# Model License Audit

Audit date: 2026-05-19

This audit covers model and checkpoint files referenced by the Windows model downloader. It is not legal advice. Model repositories can change after this date, so repeat this review immediately before publishing a GitHub Release.

## Release Policy

- Do not bundle `.onnx`, `.pth`, `.safetensors`, checkpoint, or model-cache files in the Windows installer by default.
- Store downloaded models under `%LOCALAPPDATA%\DeepLiveCamStudio\models`, not under the install directory.
- Show source URLs, license notes, and SHA-256 checksums before downloading.
- Verify every downloaded file by SHA-256 before moving it into the model directory.
- Do not upload model binaries to GitHub Releases unless redistribution rights are separately confirmed for each model file.

## Current Source Evidence

| Source | Evidence observed on 2026-05-19 | Release decision |
| --- | --- | --- |
| `hacksider/deep-live-cam` Hugging Face repository | The repository currently shows `License: gpl-3.0` and lists `inswapper_128.onnx`, `inswapper_128_fp16.onnx`, `gfpgan-1024.onnx`, and many additional model/checkpoint files. Source checked: https://huggingface.co/hacksider/deep-live-cam | Exclude from installer; allow explicit user download after source/license/checksum notice. |
| `netrunner-exe/Face-Upscalers-onnx` Hugging Face repository | The model card currently states that all models in the repository are intended for non-commercial use, academic research, and educational purposes only. Source checked: https://huggingface.co/netrunner-exe/Face-Upscalers-onnx | Exclude GPEN models from installer; do not redistribute without permission/legal review. |
| `TencentARC/GFPGANv1` license text | The upstream license text states GFPGAN is Apache-2.0 except for listed third-party components. Source checked: https://github.com/TencentARC/GFPGAN/blob/master/LICENSE | Do not assume a converted `gfpgan-1024.onnx` mirror is redistributable; verify exact conversion provenance before bundling. |

## Downloader Model Table

| File | Downloader source URL | SHA-256 | Observed status | Installer policy |
| --- | --- | --- | --- | --- |
| `inswapper_128.onnx` | `https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx` | `e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af` | Hugging Face mirror declares GPL-3.0; InsightFace model-use history remains a redistribution risk. | Excluded. |
| `inswapper_128_fp16.onnx` | `https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx` | `6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b` | Hugging Face mirror declares GPL-3.0; InsightFace model-use history remains a redistribution risk. | Excluded. |
| `GPEN-BFR-256.onnx` | `https://huggingface.co/netrunner-exe/Face-Upscalers-onnx/resolve/main/GPEN-BFR-256.onnx` | `aa5bd3ab238640a378c59e4a560f7a7150627944cf2129e6311ae4720e833271` | Source card says non-commercial, academic, educational use only. | Excluded. |
| `GPEN-BFR-512.onnx` | `https://huggingface.co/netrunner-exe/Face-Upscalers-onnx/resolve/main/GPEN-BFR-512.onnx` | `0960f836488735444d508b588e44fb5dfd19c68fde9163ad7878aa24d1d5115e` | Source card says non-commercial, academic, educational use only. | Excluded. |
| `gfpgan-1024.onnx` | `https://huggingface.co/hacksider/deep-live-cam/resolve/main/gfpgan-1024.onnx` | `ee8dd6415e388b3a410689d5d9395a2bf50b5973b588421ebfa57bc266f19e24` | Hugging Face mirror declares GPL-3.0; upstream GFPGAN license is Apache-2.0 with listed third-party exceptions, but ONNX conversion provenance is not fully established here. | Excluded. |

## Pre-Publish Checks

- Re-open the model source URLs and verify the license labels/card text have not changed.
- Recompute or re-download-and-verify the SHA-256 values before a public release.
- Confirm no model/checkpoint files appear in `dist\DeepLiveCamStudio`, the installer payload, source archive, or GitHub Release assets.
- Record any legal approval or redistribution permission in this file before changing the installer policy to bundle a model.

## Source URLs To Recheck

- `hacksider/deep-live-cam`: https://huggingface.co/hacksider/deep-live-cam
- `hacksider/deep-live-cam` file tree snapshot: https://huggingface.co/hacksider/deep-live-cam/tree/main
- `netrunner-exe/Face-Upscalers-onnx`: https://huggingface.co/netrunner-exe/Face-Upscalers-onnx
- TencentARC/GFPGAN license: https://github.com/TencentARC/GFPGAN/blob/master/LICENSE
