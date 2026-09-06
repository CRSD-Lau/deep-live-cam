# Processing Verification

Generated: 2026-05-18

This records local packaged-runtime processing smoke tests against the rebuilt `dist\DeepLiveCamStudio` bundle. It is release evidence only and does not replace clean-VM validation.

## Packaging Fix Found During Test

The first packaged processing run failed with:

```text
Frame processor face_swapper not found
```

Root cause: frame processors are imported dynamically from `modules.processors.frame`, so PyInstaller did not include them from static analysis alone.

Fix: `build/windows/deep_live_cam_studio.spec` now includes:

```python
hiddenimports += collect_submodules("modules.processors.frame")
```

## Test Setup

- Packaged CLI: `dist\DeepLiveCamStudio\DeepLiveCamStudioCLI.exe`
- Temporary model directory: `C:\Users\neil_\AppData\Local\Temp\DeepLiveCamStudio-processing-smoke-aab9326d21bf450380929107dd2a1911\models`
- Test media directory: `C:\Users\neil_\AppData\Local\Temp\DeepLiveCamStudio-processing-smoke-aab9326d21bf450380929107dd2a1911\io`
- Source/target sample image: bundled InsightFace sample `t1.jpg`
- Short target video: generated locally from `t1.jpg` with ffmpeg

The temporary model/media directory was deleted after verification.

## Model Setup

Command:

```powershell
$env:DLC_MODELS_DIR = "<temp>\models"
dist\DeepLiveCamStudio\DeepLiveCamStudioCLI.exe --download-models --yes
```

Result: exit code `0`; all configured model files downloaded and verified by SHA-256.

## CPU Image Processing

Command:

```powershell
dist\DeepLiveCamStudio\DeepLiveCamStudioCLI.exe `
  -s "<temp>\io\source.png" `
  -t "<temp>\io\target.jpg" `
  -o "<temp>\io\cpu-output.jpg" `
  --execution-provider cpu `
  --execution-threads 1
```

Result: exit code `0`; output image was created and readable by OpenCV.

Provider evidence:

```text
[DLC.FACE-SWAPPER] Face swapper active providers: ['CPUExecutionProvider']
[DLC.FACE-ANALYSER] detection active providers: ['CPUExecutionProvider']
```

## CPU Video Processing

Command:

```powershell
dist\DeepLiveCamStudio\DeepLiveCamStudioCLI.exe `
  -s "<temp>\io\target.jpg" `
  -t "<temp>\io\target-video.mp4" `
  -o "<temp>\io\cpu-output-video.mp4" `
  --execution-provider cpu `
  --execution-threads 1 `
  --video-quality 35
```

Result: exit code `0`; output video existed and `ffprobe` read it successfully.

Provider evidence:

```text
[DLC.FACE-SWAPPER] Face swapper active providers: ['CPUExecutionProvider']
[DLC.CORE] Video processing succeeded!
```

Note: ffmpeg printed an audio-map warning because the synthetic test video had no audio stream. The output video was still produced and readable.

## CUDA Image Processing And Self-Contained Runtime

An early `2.2.0` release candidate exposed a packaging gap: the CUDA provider
was registered, but an actual ONNX Runtime session could not load
`cublasLt64_12.dll` unless compatible CUDA libraries were already on `PATH`.
That candidate was not published.

The corrected clean build copies an explicit, tested CUDA 12/cuDNN 9 DLL set
from the pinned build-only PyTorch wheel. The Python `torch` package is not
included in the application. A fresh packaged bundle then passed this command
on an NVIDIA RTX 4070 without an external CUDA Toolkit or PyTorch directory on
`PATH`:

```powershell
dist\DeepLiveCamStudio\DeepLiveCamStudioCLI.exe `
  --execution-provider cuda `
  --check-execution-provider
```

Result: exit code `0`; ONNX Runtime created a real CUDA session.

Provider evidence:

```text
[DLC.CORE] Requested execution provider(s): ['cuda']
[DLC.CORE] Resolved execution provider(s): ['CUDAExecutionProvider', 'CPUExecutionProvider']
[DLC.CORE] Execution provider probe active providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
[DLC.CORE] Execution provider check passed.
```

The earlier end-to-end CUDA image test also produced a valid output once this
same runtime set was available. The project owner subsequently confirmed the
Preview, file-rendering, and OBS/Live Output paths on the corrected CUDA build.

## Release Implication

- CPU packaged processing is verified locally for image and short-video paths.
- CUDA provider startup is verified from a self-contained packaged bundle, and
  the interactive Preview, rendering, and Live Output paths are owner-verified.
- The installer bundles the allow-listed CUDA 12/cuDNN 9 runtime DLLs. A
  compatible NVIDIA display driver remains required; the CUDA Toolkit,
  PyTorch, and TensorRT are not bundled application dependencies.
- This does not replace a clean Windows VM install test or OBS Virtual Camera test.
