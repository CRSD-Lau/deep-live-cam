# OBS Virtual Camera on Windows

This guide covers the Windows-first live workflow for Deep-Live-Cam with OBS,
OBS Virtual Camera, and NVIDIA CUDA.

## Install

1. Install Python 3.11, Git, FFmpeg, Visual Studio 2022 Runtime, OBS Studio,
   and a current NVIDIA driver.
2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

3. Download models only after reviewing their source and license notes:

```bash
python run.py --download-models
```

Installed Windows builds provide the same flow through:

```bash
DeepLiveCamStudioCLI.exe --download-models
```

For source checkouts, models are stored in the repository `models` folder by
default. Installed Windows builds store models under
`%LOCALAPPDATA%\DeepLiveCamStudio\models` by default. Use `DLC_MODELS_DIR` to
point either mode at a different reviewed model folder. The Windows installer
intentionally does not bundle `.onnx`, `.pth`, or `.safetensors` files.

## CUDA Check

Deep-Live-Cam uses `onnxruntime-gpu` when `CUDAExecutionProvider` is available
and falls back to CPU when CUDA cannot load.

```bash
python tools/check_cuda_provider.py --execution-provider cuda --strict
```

The checker verifies both provider discovery and an actual ONNX session. If CUDA
is advertised but the probe falls back to CPU, install the CUDA-enabled PyTorch
wheel above so ONNX Runtime can find the CUDA 12/cuDNN 9 DLLs on Windows.

## Direct Virtual Camera Output

Run Deep-Live-Cam with virtual camera output enabled:

```bash
python run.py --execution-provider cuda --virtual-cam
```

Then:

1. Select a source face.
2. Select the physical camera.
3. Click `Live`.
4. In Discord, Zoom, Teams, or another app, choose the virtual camera device.

The default virtual camera output is `1280x720@30`.

Optional settings:

```bash
python run.py --execution-provider cuda --virtual-cam ^
  --virtual-cam-name "OBS Virtual Camera" ^
  --virtual-cam-width 1280 ^
  --virtual-cam-height 720 ^
  --virtual-cam-fps 30
```

For a practical high-FPS setup, separate the camera/model processing resolution
from the virtual camera output resolution:

```bash
python run.py --execution-provider cuda --virtual-cam ^
  --camera-width 1280 ^
  --camera-height 720 ^
  --camera-fps 60 ^
  --virtual-cam-width 1920 ^
  --virtual-cam-height 1080 ^
  --virtual-cam-fps 60
```

The on-screen `Show FPS` value is the number of unique frames produced by the
face swap pipeline. The virtual camera can still publish a `60fps` signal by
sending the latest processed frame on each virtual camera tick.

To test the virtual camera without loading models:

```bash
python tools/check_obs_virtualcam.py --width 1280 --height 720 --fps 30
```

## OBS Workflows

### Send Deep-Live-Cam Directly to Apps

Use `--virtual-cam`, then choose the virtual camera in the target app. This is
the simplest workflow when you do not need OBS scene composition.

### Rebroadcast Through OBS

OBS's built-in virtual camera is one camera instance. If Python sends frames to
`OBS Virtual Camera`, OBS cannot also capture that same device and rebroadcast it
through OBS Virtual Camera.

Use one of these workflows instead:

- Use OBS `Window Capture` and capture the `Deep-Live-Cam Live Preview` window,
  then click `Start Virtual Camera` in OBS.
- Use a separate pyvirtualcam-supported virtual camera device for Python output,
  such as Unity Capture, capture that device in OBS, then start OBS Virtual
  Camera.

## Troubleshooting

- `pyvirtualcam` is missing: run `pip install -r requirements.txt`.
- OBS Virtual Camera is missing: install OBS Studio, start OBS once, and confirm
  the `Start Virtual Camera` button is present.
- The virtual camera is busy: close Discord, Zoom, browser tabs, OBS, or other
  apps that may already be using the same camera device.
- CUDA falls back to CPU: run `python tools/check_cuda_provider.py --execution-provider cuda`
  and fix the missing CUDA/cuDNN/onnxruntime-gpu dependency it reports.
- OBS does not show Deep-Live-Cam: use `Window Capture` on `Deep-Live-Cam Live
  Preview`, or capture a separate virtual camera device instead of OBS's own
  output device.
- Performance is below 60fps: process at `720p60` with `--camera-width 1280
  --camera-height 720 --camera-fps 60`, disable face enhancers, keep `Many
  faces` off, and confirm `CUDAExecutionProvider` is active.
