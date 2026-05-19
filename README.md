# Deep Live Cam Studio 2.1.6

Deep Live Cam Studio is a Windows-focused build of Deep-Live-Cam with a packaged desktop installer, CUDA-enabled runtime support, explicit model download/verification, OBS virtual-camera workflow support, and release compliance tooling.

This repository is the working source for the Windows Studio build published by CRSD-Lau. It is based on the upstream [hacksider/Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) project, with the Windows packaging and release work documented below.

## What We Added

- Windows x64 per-user installer built with PyInstaller and Inno Setup.
- Versioned install path under `%LOCALAPPDATA%\Programs\DeepLiveCamStudio\<version>`.
- Desktop/Start Menu app launcher for `DeepLiveCamStudio.exe`.
- Separate CLI entry point, `DeepLiveCamStudioCLI.exe`, for diagnostics, model setup, and batch processing.
- Explicit model downloader with source URLs, license notes, and SHA-256 checks before download.
- User model storage under `%LOCALAPPDATA%\DeepLiveCamStudio\models`, preserved during uninstall.
- CUDA 12/cuDNN 9 runtime DLL bundling for `onnxruntime-gpu` in packaged Windows builds.
- Startup DLL registration for frozen PyInstaller installs so CUDA sessions load correctly.
- OBS Virtual Camera and direct virtual-camera workflow documentation.
- Packaged runtime, installer, clean-VM, OBS, and release-artifact verification scripts.
- Windows bundle manifest and third-party license evidence for release review.
- Optional Authenticode signing support and local self-signing support for test builds.

## Latest Release

Current release:

[Deep Live Cam Studio 2.1.6](https://github.com/CRSD-Lau/deep-live-cam/releases/tag/v2.1.6)

Installer:

```text
DeepLiveCamStudio-2.1.6-x64-setup.exe
```

The installer does not bundle model/checkpoint files. After installing, run:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

The downloader shows model sources, license notes, and checksums before installing model files.

## Install And Update

Install the latest release by downloading and running the Windows installer from the GitHub Release page.

Default install path:

```text
%LOCALAPPDATA%\Programs\DeepLiveCamStudio\2.1.6
```

Model storage:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

Updates install into a new versioned folder. You do not need to uninstall the previous version first. Once the new version is working, you can remove older versions from Windows Installed Apps.

## Windows Runtime Notes

- CUDA acceleration requires compatible NVIDIA drivers.
- The Windows installer bundles the CUDA 12/cuDNN 9 runtime DLLs needed by `onnxruntime-gpu`.
- If CUDA is unavailable, the app can fall back to CPU or DirectML where supported.
- `ffmpeg` and `ffprobe` are required for video processing and audio restore. They are not bundled by default.
- OBS Virtual Camera is optional and must be installed/configured through OBS.
- Desktop launch logs are written to `%LOCALAPPDATA%\DeepLiveCamStudio\logs`.
- UI switch state is written to `%LOCALAPPDATA%\DeepLiveCamStudio\switch_states.json`.

## Model Setup

From an installed build:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

From a source checkout:

```powershell
python run.py --download-models
```

Use `DLC_MODELS_DIR` to point the app at a different reviewed model folder.

Do not upload model binaries to GitHub Releases unless redistribution rights are confirmed for each model file.

## Usage

Launch the desktop app from the Start Menu or installed folder.

For CLI processing:

```powershell
DeepLiveCamStudioCLI.exe --source source.png --target target.png --output output.png --execution-provider cuda
```

For source checkout usage:

```powershell
python run.py --execution-provider cuda
```

Useful CLI flags:

```text
--download-models
--execution-provider cuda
--execution-provider cpu
--execution-provider directml
--virtual-cam
--camera-width 1280
--camera-height 720
--camera-fps 60
--virtual-cam-width 1920
--virtual-cam-height 1080
--virtual-cam-fps 60
```

## OBS And Virtual Camera

Deep Live Cam Studio can send processed live output directly to a virtual camera:

```powershell
python run.py --execution-provider cuda --virtual-cam
```

Example 720p60 processing with 1080p60 virtual-camera output:

```powershell
python run.py --execution-provider cuda --virtual-cam --camera-width 1280 --camera-height 720 --camera-fps 60 --virtual-cam-width 1920 --virtual-cam-height 1080 --virtual-cam-fps 60
```

OBS's built-in virtual camera is a single device. Use direct virtual-camera output for Discord, Zoom, or Teams, or use OBS Window Capture on the `Deep-Live-Cam Live Preview` window when OBS needs to rebroadcast the scene.

See [docs/OBS_VIRTUAL_CAMERA.md](docs/OBS_VIRTUAL_CAMERA.md) for setup and troubleshooting.

## Build From Source

Recommended Windows setup:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

For CUDA source runs:

```powershell
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu==1.23.2
python tools/check_cuda_provider.py --execution-provider cuda --strict
```

Run from source:

```powershell
python run.py --download-models
python run.py --execution-provider cuda
```

## Build The Windows Installer

Build the PyInstaller bundle:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1
```

Run local preflight checks:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\test_packaged_runtime.ps1
powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1
```

Package the installer:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_installer.ps1 -AppVersion 2.1.6
```

The installer output is:

```text
build\windows\installer\DeepLiveCamStudio-2.1.6-x64-setup.exe
```

## Signing

For a real public publisher name, sign with a trusted Authenticode code-signing certificate:

```powershell
$env:DLC_SIGN_CERT_PASSWORD = "<pfx-password>"
powershell -ExecutionPolicy Bypass -File build\windows\package_installer.ps1 -AppVersion 2.1.6 -SignCertPath "C:\path\to\certificate.pfx"
```

For local-only testing without a paid certificate, self-sign and trust the certificate for the current Windows user:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\self_sign_installer.ps1 -AppVersion 2.1.6 -TrustForCurrentUser
```

Self-signing does not create public SmartScreen reputation. Other users must import and trust the exported `.cer` file themselves.

## Release Process

Run the standard local release gate:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.6 -GitRef <release-tag-or-commit>
```

Package corresponding source for the exact release tag or commit:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.6 -GitRef <release-tag-or-commit>
```

Assemble upload assets:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\assemble_release_assets.ps1 -AppVersion 2.1.6 -RequireGitRefSource
```

The release asset set includes the installer, installer hash, source archive, source hash, source manifest, release notes, compliance evidence, `RELEASE_ASSETS.md`, and `SHA256SUMS.txt`.

## Safety And Responsible Use

Use this software responsibly and legally. If using a real person's face, obtain consent and clearly label generated output when sharing. Do not use the tool for impersonation, fraud, harassment, non-consensual sexual content, or other harmful activity.

The app includes content-safety checks, but users remain responsible for their own use.

## Upstream Attribution

This project is a modified Windows Studio build of [Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam), which is licensed under AGPL-3.0.

Important upstream and ecosystem credits include:

- [hacksider/Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam), the upstream application.
- [deepinsight/insightface](https://github.com/deepinsight/insightface), used for face analysis and model ecosystem support.
- [ffmpeg](https://ffmpeg.org/), used for video workflows.
- The upstream Deep-Live-Cam contributors listed in the original project history.

## License And Compliance

Deep-Live-Cam is AGPL-3.0. If you distribute a Windows installer or executable, publish the complete corresponding source for the exact binary release, including packaging scripts and modifications.

Release compliance files:

- [COMPLIANCE.md](COMPLIANCE.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [LICENSES/BUNDLED_BINARY_OBLIGATIONS.md](LICENSES/BUNDLED_BINARY_OBLIGATIONS.md)
- [LICENSES/MODEL_LICENSE_AUDIT.md](LICENSES/MODEL_LICENSE_AUDIT.md)
- [LICENSES/PYTHON_DEPENDENCIES.md](LICENSES/PYTHON_DEPENDENCIES.md)
- [LICENSES/WINDOWS_BUNDLE_MANIFEST.md](LICENSES/WINDOWS_BUNDLE_MANIFEST.md)

Model files have separate license and redistribution considerations. The installer excludes model/checkpoint files and requires explicit user download with visible source and license notes.
