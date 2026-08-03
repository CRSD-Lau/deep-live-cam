# Build and Test on Windows

Deep Live Cam Studio supports Python 3.11 on 64-bit Windows. CUDA and DirectML use conflicting ONNX Runtime packages, so keep their environments separate.

## Prerequisites

- Windows 10 22H2, Windows 11 23H2, or newer
- CPython 3.11.9
- Git
- Current GPU drivers
- `ffmpeg` and `ffprobe` for video and audio workflows
- Inno Setup 6 only when packaging the installer

## CUDA Development Environment

```powershell
py -3.11 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
venv\Scripts\python.exe -m pip install --no-deps -r requirements-build-windows-cuda.txt
venv\Scripts\python.exe tools\check_cuda_provider.py --execution-provider cuda --strict
venv\Scripts\python.exe run.py --execution-provider cuda
```

The Torch wheel is a build-only source for reviewed CUDA runtime DLLs. The packaged application must not contain the Torch Python package.

## DirectML Development Environment

Create the isolated environment with the repository helper:

```powershell
powershell -ExecutionPolicy Bypass -File tools\setup_directml.ps1
.venv-directml\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv-directml\Scripts\python.exe run.py --execution-provider directml --directml-device-id 0 --check-execution-provider
.venv-directml\Scripts\python.exe run.py --execution-provider directml --directml-device-id 0
```

Strict verification succeeds only when an actual ONNX session activates `DmlExecutionProvider`. CPU fallback is not accepted as DirectML validation.

## Tests and Static Checks

Run these checks from the matching development environment:

```powershell
python -m pytest -q
python -m pip_audit -r requirements-locks\windows-cuda-py311.lock --progress-spinner off
python -m pip_audit -r requirements-locks\windows-directml-py311.lock --progress-spinner off
python -m bandit -r modules tools run.py DeepLiveCamStudio.pyw -ll
python -m ruff check modules tools tests run.py DeepLiveCamStudio.pyw --select E9,F63,F7,F82
powershell -ExecutionPolicy Bypass -File tools\update_dependency_locks.ps1 -Check
```

Provider, camera, render, or live-output changes also need the hardware evidence described in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Build Packaged Applications

CUDA installer bundle:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Accelerator Cuda
powershell -ExecutionPolicy Bypass -File build\windows\test_packaged_runtime.ps1 -Accelerator Cuda -RequireAccelerator
```

DirectML portable bundle:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Accelerator DirectML
powershell -ExecutionPolicy Bypass -File build\windows\test_packaged_runtime.ps1 -Accelerator DirectML -RequireAccelerator
```

Build release assets only through the scripts under `build/windows/`. Do not distribute an ad-hoc `dist/` directory as a public release.

## Release Validation

The complete release path is intentionally stricter than a developer build:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion <version> -GitRef <tag-or-commit>
```

Follow [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for physical hardware, clean-machine, legal, source-archive, checksum, and publication gates.
