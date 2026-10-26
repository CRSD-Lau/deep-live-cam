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

## Source maintenance after 2.2.5 (2026-10-26)

The maintained source now pins pip 26.2.2, setuptools 84.2.1, and
pyinstaller-hooks-contrib 2026.9 in both Windows application locks, with Ruff
0.17.2 in the development tools. The published 2.2.5 assets and their source
commit are unchanged. The checked-in `LICENSES/PYTHON_DEPENDENCIES*.md` files
are snapshots of earlier packaged environments; they do not attest to this
updated toolchain. Regenerate the inventories and third-party licence files
from each clean packaged environment before a future binary release.

This source-only tooling update does not validate new CUDA or DirectML binaries.
The full tests, release validators, licence review, and supported-hardware
Preview, Render, provider-probe, and Live Output gates above still apply before
binary publication.

## Security refresh for 2.2.5 (2026-10-25)

Both profiles lock Pillow 13.0.0, setuptools 84.1.0, certifi 2026.10.23,
and filelock 4.2.4. The two transitive security floors are maintained in
both root profiles so regeneration cannot retain an affected trust store
or filelock version. No unrelated dependency versions changed.

Pillow 13.0.0 supports the required CPython 3.11.9. Its removed APIs are not
used by the application: image arrays infer their mode, exports use RGB/RGBA,
and the UI uses supported resize/fit/exif APIs. Main UI code uses PySide6;
CustomTkinter is absent from the maintained release locks.

The official CUDA 12.8 index was rechecked on 2026-10-25: its newest Windows
CPython 3.11 wheel remains torch 2.11.0, so the existing build-only JIT advisory
exception below remains necessary. Both application profile audits pass
without exceptions; only the isolated DLL-source audit retains PYSEC-2025-194.

Fresh package inventory, licence, exact-artifact, hardware and manual gates
remain mandatory for this candidate. Prior 2.2.4 attestations are archived
under docs/release-evidence/v2.2.4/final-attestations and do not approve 2.2.5.

## Build-only PyTorch advisory handling

The CUDA build installs PyTorch into an isolated helper environment and copies only an explicit allowlist of CUDA and cuDNN DLLs. PyTorch Python modules, including `torch.jit`, are excluded from the packaged application.

The generated audit companion removes the `+cu128` local build suffix so `pip-audit` can query the upstream `torch` version. As reviewed on 2026-09-06, [GHSA-rrmf-rvhw-rf47 / CVE-2025-3000](https://github.com/advisories/GHSA-rrmf-rvhw-rf47), also tracked as `PYSEC-2025-194`, lists versions through 2.12.1 as affected and 2.13.0 as patched. The locked 2.11.0 DLL-source wheel is therefore within the advisory's affected version range. The older OSV range ending at 2.6.0 does not establish that this wheel is patched.

On the same date, the [official PyTorch CUDA 12.8 wheel index](https://download.pytorch.org/whl/cu128/torch/) listed 2.11.0 as its newest `cp311-cp311-win_amd64` wheel and had no patched 2.13.0-or-newer wheel for that profile. A version-only update cannot currently provide the fix within the supported release matrix. Recheck wheel availability when reviewing this exception; changing the CUDA runtime profile requires the provider and release validation above.

The audit exception is limited to the build-only DLL source because the [reported failure is in `torch.jit.script`](https://github.com/pytorch/pytorch/issues/149623), which the application and build do not call. Its continued use depends on these boundaries:

- `build/windows/build_windows.ps1` installs the hash-locked wheel without dependencies in a separate helper environment.
- `build/windows/deep_live_cam_studio.spec` copies an explicit CUDA/cuDNN DLL allowlist and excludes the `torch`, `torchvision`, and `torchaudio` Python packages.
- `build/windows/test_packaged_runtime.ps1` and `build/windows/test_installer.ps1` reject a payload containing `_internal/torch`.

This is a reachability exception, not a claim that PyTorch 2.11.0 is unaffected. It does not cover a source installation that adds PyTorch, a different advisory, or a build that includes Torch/JIT code. Re-evaluate the exception whenever the PyTorch lock, copied DLLs, build isolation, packaging exclusions, or application use of PyTorch changes. Any upgrade to the DLL-source wheel still requires the CUDA provider and release validation described above.

## Runtime notice staging

The collector preserves full Pillow, certifi, and filelock licence files as well
as their metadata. Each build stages only the directories listed by its freshly
generated collector manifest, replacing the earlier PyInstaller licence data
copy. The other accelerator inventory is an explicit non-applicable marker;
its historical table is not evidence for the current payload. Release assembly
uses the actual inventory inside the verified DirectML ZIP for the separate
DirectML release document. Exact payload checks remain required.

The frozen runtime excludes pip and its vendored modules. InsightFace's unused
`import_try_install` helper otherwise pulls pip into PyInstaller through a
missing-package installation fallback. Application/model-download paths do not
call that helper or pip. Both executable archives are checked for pip and Torch
modules by `tools/check_frozen_runtime_imports.py`; their build notices remain
available for attribution without claiming the code is shipped.
