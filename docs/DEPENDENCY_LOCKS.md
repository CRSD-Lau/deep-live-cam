# Windows Dependency Locks

Release builds install reviewed lock files rather than resolving ranged dependencies during packaging.

## Supported release matrix

| Component | CUDA release | DirectML release |
| --- | --- | --- |
| Architecture | Windows x64 | Windows x64 |
| Operating system | Windows 10 22H2 or Windows 11 23H2 and newer | Windows 10 22H2 or Windows 11 23H2 and newer |
| Python | CPython 3.11.9 | CPython 3.11.9 |
| ONNX Runtime | `onnxruntime-gpu==1.24.4` | `onnxruntime-directml==1.23.0` |
| GPU runtime | CUDA 12.8, cuDNN 9 | DirectX 12 / DirectML |
| Driver floor | NVIDIA Windows driver 528.33 or newer; current production driver recommended | Current vendor driver with DirectX 12 support |
| Validated hardware | NVIDIA GPU with CUDA Execution Provider | AMD, Intel, or NVIDIA DirectX 12 adapter with DML Execution Provider |

The CUDA package is compatible with the CUDA 12.x family and cuDNN 9. NVIDIA documents 528.33 as the Windows driver floor for CUDA 12.x minor-version compatibility. DirectML requires Windows 10 version 1903 or newer and a DirectX 12-capable device; this project supports the narrower Windows versions listed above.

CUDA and DirectML environments are deliberately separate. Never install both `onnxruntime-gpu` and `onnxruntime-directml` into one environment.

## Maintained inputs and generated outputs

- `requirements.txt`: CUDA application inputs.
- `requirements-directml.txt`: DirectML application inputs.
- `requirements-build-windows.txt`: shared packaging tools.
- `requirements-build-windows-cuda.txt`: build-only CUDA runtime wheel.
- `requirements-locks/windows-cuda-py311.lock`: generated CUDA release set.
- `requirements-locks/windows-cuda-runtime-py311.lock`: generated hash lock for the build-only PyTorch CUDA wheel.
- `requirements-locks/windows-cuda-runtime-audit-py311.txt`: generated upstream PyTorch version used for advisory lookup without the custom CUDA build suffix.
- `requirements-locks/windows-directml-py311.lock`: generated DirectML release set.

The lock files are generated on Windows with CPython 3.11.9 and include hashes. The large build-only PyTorch wheel is kept in a separate no-dependencies lock and installed into an isolated helper environment used only to source CUDA/cuDNN DLLs. This keeps PyTorch's build-tool constraints out of the packaged application environment and avoids downloading the wheel during ordinary application resolution. Do not edit generated locks by hand.

## Updating a dependency

Change one high-impact dependency family in the maintained input manifests, then run:

```powershell
powershell -ExecutionPolicy Bypass -File tools\update_dependency_locks.ps1
```

Review both lock diffs. A lock-only transitive change still requires explanation in the pull request. Confirm regeneration is clean with:

```powershell
powershell -ExecutionPolicy Bypass -File tools\update_dependency_locks.ps1 -Check
```

For every lock update:

1. Install each profile with `--require-hashes` in a clean environment.
2. Run `pip-audit` against both lock files.
3. Regenerate `LICENSES/PYTHON_DEPENDENCIES.md` and third-party licence files from each packaged environment.
4. Run the full tests and Windows release validators.
5. Record Preview, Render, enhancement, provider-probe, and Live Output evidence on supported NVIDIA and AMD hardware before publication.

Dependabot monitors the maintained root manifests weekly. Major upgrades remain ignored and must be proposed deliberately; this repository does not auto-merge dependency updates.

## Build-only PyTorch advisory handling

The CUDA build installs PyTorch into an isolated helper environment and copies only an explicit allowlist of CUDA and cuDNN DLLs. PyTorch Python modules, including `torch.jit`, are excluded from the packaged application.

The generated audit companion removes the `+cu128` local build suffix so `pip-audit` can query the upstream `torch` version. As reviewed on 2026-09-06, [GHSA-rrmf-rvhw-rf47 / CVE-2025-3000](https://github.com/advisories/GHSA-rrmf-rvhw-rf47), also tracked as `PYSEC-2025-194`, lists versions through 2.12.1 as affected and 2.13.0 as patched. The locked 2.11.0 DLL-source wheel is therefore within the advisory's affected version range. The older OSV range ending at 2.6.0 does not establish that this wheel is patched.

The audit exception is limited to the build-only DLL source because the [reported failure is in `torch.jit.script`](https://github.com/pytorch/pytorch/issues/149623), which the application and build do not call. Its continued use depends on these boundaries:

- `build/windows/build_windows.ps1` installs the hash-locked wheel without dependencies in a separate helper environment.
- `build/windows/deep_live_cam_studio.spec` copies an explicit CUDA/cuDNN DLL allowlist and excludes the `torch`, `torchvision`, and `torchaudio` Python packages.
- `build/windows/test_packaged_runtime.ps1` and `build/windows/test_installer.ps1` reject a payload containing `_internal/torch`.

This is a reachability exception, not a claim that PyTorch 2.11.0 is unaffected. It does not cover a source installation that adds PyTorch, a different advisory, or a build that includes Torch/JIT code. Re-evaluate the exception whenever the PyTorch lock, copied DLLs, build isolation, packaging exclusions, or application use of PyTorch changes. Any upgrade to the DLL-source wheel still requires the CUDA provider and release validation described above.
