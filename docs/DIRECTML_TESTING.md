# DirectML Portable Build

The DirectML release is the Windows GPU build for AMD and Intel DirectX 12
graphics. NVIDIA users should normally use the CUDA installer, although the
DirectML build can also run on DirectX 12-capable NVIDIA GPUs.

DirectML and CUDA require mutually exclusive ONNX Runtime packages. They are
therefore shipped as separate downloads and must not be copied over one
another.

## Install and run

1. Download `DeepLiveCamStudio-<version>-DirectML-x64-portable.zip` from the
   matching GitHub Release.
2. Extract the ZIP into a new folder.
3. Run `DeepLiveCamStudio.exe`.
4. Select **Set Up Models** if the required models are not already installed.

The portable build stores downloaded models, settings, and logs under
`%LOCALAPPDATA%\DeepLiveCamStudio`, just like the installed CUDA build.

## Verify GPU acceleration

Open PowerShell in the extracted folder and run:

```powershell
.\DeepLiveCamStudioCLI.exe --execution-provider directml --check-execution-provider
```

The check must report `DmlExecutionProvider` as active and finish with
`Execution provider check passed`. It fails instead of silently treating CPU
fallback as successful.

For Radeon stability, face detection and recognition run on CPU while the
heavier face-swap and enhancement models run on DirectML. Seeing
`CPUExecutionProvider` for face analysis is therefore expected; the face
swapper must still report `DmlExecutionProvider`.

## Multiple GPUs

Windows adapter 0 is used by default. When the intended GPU is not adapter 0,
test another adapter from the CLI:

```powershell
.\DeepLiveCamStudioCLI.exe --execution-provider directml --directml-device-id 1 --check-execution-provider
```

Windows Task Manager's **Performance** tab shows the adapter number assigned
to each GPU.

## Troubleshooting

- Always extract a new release into a new folder; do not overwrite an older
  CUDA or DirectML bundle.
- Install current GPU drivers and Windows updates.
- Run the provider check above before testing Preview, Render, or Live Output.
- Click Preview or Start Render once and allow the initial model load to
  finish.
- Desktop logs are written to
  `%LOCALAPPDATA%\DeepLiveCamStudio\logs\desktop-launch.log`.

When reporting a problem, include the GPU model, Windows version, provider
check output, and `desktop-launch.log`.

## Build from source

Create the isolated DirectML environment:

```powershell
powershell -ExecutionPolicy Bypass -File tools\setup_directml.ps1
```

Build, validate, and package the portable release:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1 -Accelerator DirectML
powershell -ExecutionPolicy Bypass -File build\windows\package_portable.ps1 -AppVersion 2.2.1 -Accelerator DirectML
```

The packaging step performs a strict provider probe, rejects bundled model
weights, verifies hidden runtime dependencies such as
`_internal/sklearn/.libs/vcomp140.dll`, and writes a SHA-256 sidecar next to the
release ZIP.
