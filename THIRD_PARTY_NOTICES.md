# Third Party Notices

This file summarizes third-party components expected to be bundled by the Windows PyInstaller build. It is based on `requirements.txt`, installed package metadata in this workspace, and model repository notices reviewed on 2026-05-18. Re-run a license scan before every public release. See `LICENSES/PYTHON_DEPENDENCIES.md` for the current installed-package license snapshot, `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` for LGPL/GPL-family binary distribution notes, and `LICENSES/MODEL_LICENSE_AUDIT.md` for the dated model-source audit.

## Application

- Deep-Live-Cam: AGPL-3.0. Original project: https://github.com/hacksider/Deep-Live-Cam
- This packaged build must provide complete corresponding source for the exact binary release.

## Python dependencies

The table below highlights the primary runtime dependencies from `requirements.txt`. The more complete transitive dependency metadata snapshot is in `LICENSES/PYTHON_DEPENDENCIES.md`.

| Package | Version observed | License observed | Notes |
| --- | ---: | --- | --- |
| `numpy` | 1.26.4 | BSD-3-Clause plus bundled notices | Wheel may include OpenBLAS, LAPACK, and GCC runtime exception notices. |
| `typing-extensions` | installed by resolver | Python Software Foundation / permissive metadata varies by version | Include metadata from built wheel. |
| `opencv-python` | 4.10.0.84 | Apache-2.0 | Includes OpenCV native binaries. |
| `cv2_enumerate_cameras` | 1.1.15 | GPL-3.0 metadata text | Include GPL notice/source availability. |
| `onnx` | 1.18.0 | Apache-2.0 | ONNX libraries and protobuf integration. |
| `insightface` | 0.7.3 | MIT | Upstream README warns models are non-commercial research unless otherwise stated. |
| `psutil` | 5.9.8 | BSD-3-Clause | Native extension. |
| `PySide6` | 6.11.1 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | Preserve Qt for Python notices and LGPL compliance path. |
| `Pillow` | 12.1.1 | HPND/Pillow license metadata varies | Include wheel metadata in final release audit. |
| `tqdm` | 4.67.3 | MPL-2.0 AND MIT | Progress display. |
| `onnxruntime-gpu` | 1.23.2 | MIT | Bundles ONNX Runtime native DLLs; CUDA provider needs compatible NVIDIA runtime DLLs. |
| `onnxruntime-silicon` | not installed on Windows | MIT/Apple Silicon package | macOS-only requirement marker. |
| `tensorflow` | 2.19.1 observed | Apache-2.0 | Large dependency tree; PyInstaller may collect many transitive notices. |
| `opennsfw2` | 0.10.2 | MIT classifier | May download/use Yahoo Open NSFW-derived assets; review separately if bundled. |
| `protobuf` | 4.25.1 | BSD-3-Clause | Google protobuf runtime. |
| `pygrabber` | 0.2 | MIT | Windows camera enumeration. |
| `pyvirtualcam` | 0.15.0 | GPLv2 classifier observed | Review AGPL-3.0 compatibility before public binary release. |

See `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` for the release checklist covering bundled native libraries, LGPL replaceability considerations, and pyvirtualcam/cv2_enumerate_cameras review items. High-attention package license files collected from the build environment are installed under `LICENSES/THIRD_PARTY_LICENSES/`.

## Model files

No model files are bundled by the Windows installer by default.

The model downloader presents source URLs, license notes, and SHA-256 checksums before download. Downloaded files are stored in the user's app data model folder, not in the installer.

Current public source evidence reviewed on 2026-05-18 is captured in `LICENSES/MODEL_LICENSE_AUDIT.md`. Summary:

- `hacksider/deep-live-cam` on Hugging Face is labeled `gpl-3.0`.
- `netrunner-exe/Face-Upscalers-onnx` on Hugging Face states that repository models are for non-commercial, academic, and educational purposes only.
- TencentARC/GFPGAN license text states GFPGAN is Apache-2.0 except for listed third-party components.

| Model | Source | License/status observed | SHA-256 |
| --- | --- | --- | --- |
| `inswapper_128.onnx` | https://huggingface.co/hacksider/deep-live-cam | Hugging Face repo declares GPL-3.0; InsightFace model-use restrictions remain a risk | `e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af` |
| `inswapper_128_fp16.onnx` | https://huggingface.co/hacksider/deep-live-cam | Hugging Face repo declares GPL-3.0; InsightFace model-use restrictions remain a risk | `6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b` |
| `GPEN-BFR-256.onnx` | https://huggingface.co/netrunner-exe/Face-Upscalers-onnx | No OSI license declared; model card states non-commercial, academic, educational use only | `aa5bd3ab238640a378c59e4a560f7a7150627944cf2129e6311ae4720e833271` |
| `GPEN-BFR-512.onnx` | https://huggingface.co/netrunner-exe/Face-Upscalers-onnx | No OSI license declared; model card states non-commercial, academic, educational use only | `0960f836488735444d508b588e44fb5dfd19c68fde9163ad7878aa24d1d5115e` |
| `gfpgan-1024.onnx` | https://huggingface.co/hacksider/deep-live-cam | Hugging Face mirror declares GPL-3.0; upstream TencentARC/GFPGAN is Apache-2.0, but converted-model provenance should be rechecked | `ee8dd6415e388b3a410689d5d9395a2bf50b5973b588421ebfa57bc266f19e24` |

## External tools

- Inno Setup: used to build the Windows installer, not bundled as a runtime dependency. The Inno Setup License permits broad use, including commercial applications, but current JR Software pages request commercial users purchase an Inno Setup commercial license. Confirm the release publisher's Inno Setup license position before production/commercial distribution.
- ffmpeg/ffprobe: required for video processing, not bundled by default. If bundled later, include the exact ffmpeg license and build configuration.
- OBS Virtual Camera: optional user-installed workflow dependency, not bundled.
- NVIDIA CUDA/cuDNN/TensorRT runtime libraries: not bundled by default. Users must install compatible drivers/runtimes or use CPU/DirectML where available.
