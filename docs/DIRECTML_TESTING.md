# DirectML Test Build

This portable build is for issue #3 hardware validation. It uses Microsoft's
ONNX Runtime DirectML package instead of the NVIDIA-only CUDA package in the
current public installer.

DirectML supports DirectX 12 GPUs from AMD, Intel, and NVIDIA. The reporter's
AMD GPU result is still required before this build can be promoted to a normal
release asset.

For AMD stability, face detection and recognition run on CPU while the heavier
face-swap and enhancement models run on DirectML. This avoids a known class of
multi-session DirectML hangs while retaining GPU acceleration where it matters
most.

## Run the portable build

1. Download and extract the `DeepLiveCamStudio-DirectML-...` Actions artifact.
2. Run `DeepLiveCamStudioCLI.exe --execution-provider directml --check-execution-provider`.
3. Confirm the output includes `DmlExecutionProvider` and says the provider
   check passed.
4. Run `DeepLiveCamStudio.exe`, set up the models when prompted, and test a
   short live or file-based swap.
5. Report the GPU model, Windows version, provider-check output, whether the
   app launched, and approximate FPS on issue #3.

On a computer with multiple GPUs, Windows adapter 0 is used by default. Try
`--directml-device-id 1` (then 2, if present) when the intended GPU is not the
primary adapter. Windows Task Manager's Performance tab shows the adapter
number assigned to each GPU.

The portable artifact is an unsigned test build, not a production release.
It expires from GitHub Actions after 14 days and should not replace the current
installed release until the AMD hardware test is confirmed.
