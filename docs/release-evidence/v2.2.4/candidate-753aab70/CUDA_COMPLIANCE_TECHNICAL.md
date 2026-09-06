---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
app_version: 2.2.4
source_commit: 753aab70c34ae585d525a06b9f7de2d721b7f491
technical_status: REVIEW_REQUIRED
publication_approval: false
---

# Installed CUDA payload technical inspection

Offline installed CUDA payload inspection; no application launch, native DLL load, inference, GUI, physical-camera or legal approval.

Inspected: `2026-09-06T21:28:08.251253+00:00`. Companion JSON SHA-256: `83b96e02a1aa63eaa35390845040ff8b3d7aa9da981181c0231653748e9e1d82`.

CLI SHA-256: `9f762064b9079721c9597610689f48e306a9a0ca8483856b09f2546b2c387748`.
GUI SHA-256: `d81811c45534e97fa70b108834f06ec7402ddeeeb6a904fcefe8bb4a4c6866de`.

Payload files: 2,343; bytes: 5,159,115,772. Literal CUDA allowlist: 21 DLLs.

## Native file versions and identities

| Relative file | Version resources | SHA-256 |
| --- | --- | --- |
| `_internal/cublas64_12.dll` | `6,14,11,1284` | `9513540e4ec4c51ee9e7304138c2cc255c29a8c181f9e80c38efa25738becd99` |
| `_internal/cublasLt64_12.dll` | `6,14,11,1284` | `b199d1ff892a81b7fd3d57ba1781549609b41500b36008fef326038393ad46c7` |
| `_internal/cudart64_12.dll` | `6,14,11,12080` | `c2c9a9c22a9bcba90e261825968836787b331038047a26770cffb7a583c28344` |
| `_internal/cudnn64_9.dll` | `9.19.0.56` | `c6de55089c4759a545ff63459c00a6223dacffa5e797109a6be2be0477fb6c5c` |
| `_internal/cudnn_adv64_9.dll` | `9.19.0.56` | `a8aed3390144ea20d96c0d618462a12cbc7897620380e60438489329b9722531` |
| `_internal/cudnn_cnn64_9.dll` | `9.19.0.56` | `acac8bf8f924ecd60928877310ba360d2ee5eb1e4ec80ff6475bf9d819d3a5c8` |
| `_internal/cudnn_engines_precompiled64_9.dll` | `9.19.0.56` | `3a97df241beb2b75eb5d6152996a9a90d2155c2d4da1aeac5bd66850ed2446c1` |
| `_internal/cudnn_engines_runtime_compiled64_9.dll` | `9.19.0.56` | `81c5e5475e386269825ae6da0652f4554fa1c58af6c90908a180314689e12350` |
| `_internal/cudnn_graph64_9.dll` | `No PE version resource` | `f5453cb541402218cb5459e669db1d578656ebef394c755ab5acc2bec1165657` |
| `_internal/cudnn_heuristic64_9.dll` | `No PE version resource` | `3b1cb10835204fb7a45bf03aeb353842185cb2ebb34f59db20d9cb6fe5c1c556` |
| `_internal/cudnn_ops64_9.dll` | `9.19.0.56` | `922897bd15a66acecde7c026ecc835b0fc5662c9ae08c120fd89f0f73affa7da` |
| `_internal/cufft64_11.dll` | `6,14,11,1133` | `f4fea9227b14843894ad5436725f9638b172171142c95291fc6ae7a493248221` |
| `_internal/cufftw64_11.dll` | `6,14,11,1133` | `84c86dcc4d4b770e75766964149ef688c901dc89e380278fe399dd3c03608541` |
| `_internal/curand64_10.dll` | `6,14,11,1039` | `3465fd1b46e551339b8f44c455756a0f2cba8bd846562eb659040d48edb7aaac` |
| `_internal/cusolver64_11.dll` | `6,14,11,1173` | `3d4f7a66b5f352db56d4bb5962bb453a42d5feb2d831779f4a0bebc9971c36fb` |
| `_internal/cusolverMg64_11.dll` | `6,14,11,1173` | `c3377f10606ff0606be2f08401d54aff6c37f137b78d6b6e21be356a5b4d6cc2` |
| `_internal/cusparse64_12.dll` | `6,14,11,1258` | `f4688daa6163c47a0b5293926ec7ae367de6b4af54ea201638b308831b322a0e` |
| `_internal/nvrtc-builtins64_128.dll` | `No PE version resource` | `a7afa2a40cbd3f922a33d8bf71c13cb26ca707c7016a9bc5fcde36759ba668f5` |
| `_internal/nvrtc64_120_0.dll` | `6.14.11.9000` | `02d2d7ef4690bf1a55dda1d3ac94c86ce8d16920071c87bcd3e70e94ef346e93` |
| `_internal/nvToolsExt64_1.dll` | `No PE version resource` | `0fe54f1b80ad3e44da2a3d9f0956e7c3903029d6319689ce1c4068f7a20932f3` |
| `_internal/onnxruntime/capi/onnxruntime.dll` | `1.24.20260316.2.2d92497` | `844463e9d67973a002050179a5f19d4b9255d25c4d31fa520745222bc55f9e49` |
| `_internal/onnxruntime/capi/onnxruntime_providers_cuda.dll` | `1.24.20260316.2.2d92497` | `6a02338c8fcf9e913767c1eb57033959f69076567d5290cee59c541793d16354` |
| `_internal/onnxruntime/capi/onnxruntime_providers_shared.dll` | `1.24.20260316.2.2d92497` | `93f33380e5819cb9befbfe0e5212394dcb0c9983970c73a01bf51100bb1f13ee` |
| `_internal/onnxruntime/capi/onnxruntime_providers_tensorrt.dll` | `1.24.20260316.2.2d92497` | `befda48a12ceeee0033ba284ae1fa17a3f221fd5af245d22b71da81cd9a75a06` |
| `_internal/onnxruntime/capi/onnxruntime_pybind11_state.pyd` | `No PE version resource` | `98a1398a33f10174929f512e6c17238693a99ad92a676e97500ce752a2cad10b` |
| `_internal/PySide6/Qt6Core.dll` | `6.11.1.0` | `65fe6224b6c47a15b058738031d31dce9928c4d7a58e1b8db6434f6f5cddd702` |
| `_internal/PySide6/QtCore.pyd` | `No PE version resource` | `be52341a5df1f76ecca2fb1e94eb429dfa46f0b659ed6536f25119b565b21ea8` |
| `_internal/PySide6/QtGui.pyd` | `No PE version resource` | `f0549716b10a8b4fbd5c6c041f36af215223809f919f4c4722d44cc199d5c593` |
| `_internal/PySide6/QtWidgets.pyd` | `No PE version resource` | `85cb6c2181b4b09887a7d8507dd950844d1b8f74a9c4002c7b71169f75bf6fda` |
| `_internal/python311.dll` | `3.11.9` | `0817a2a657a24c0d5fbb60df56960f42fc66b3039d522ec952dab83e2d869364` |
| `_internal/shiboken6/Shiboken.pyd` | `No PE version resource` | `0e2c5318c5ac60a016a12230bbb1f6a9d990c45cbf4a7c4af24aefb5ab7dc40a` |
| `_internal/zlibwapi.dll` | `1.2.3.0` | `1f047faec08d9a35c304fb4a7cf13853589359a8f7cbfdd48c5d5807712dcf05` |

## Runtime and license boundaries

DirectML metadata/notice directories may be retained for the alternate profile. They are not classified as runtime packages; only the CUDA snapshot, actual native files and embedded archives establish this payload profile.

The JSON records the CUDA snapshot rows against the exact application lock; the isolated Torch wheel is checked against its separate lock. It records actual Qt, ORT GPU and Torch notice metadata, nonempty LICENSE/NOTICE files, hashes, source-text comparisons and content-marker line numbers. Read those content findings before interpreting technical coverage. File presence does not prove every legal obligation.

Qt metadata's LGPL/GPL options refer to existing shared full-text copies at:

- `LGPL-3.0-only`: `LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE`
- `GPL-3.0-only`: `LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE`
- `GPL-2.0-only`: `LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE`

The existing affected Torch DLL-source wheel exception is retained within `docs/DEPENDENCY_LOCKS.md`; this report does not claim a patched wheel, approve a new exception, or provide legal advice. It performs no GUI, GPU, physical-camera, source-archive, installer-upgrade or publication checks.

## Findings

- Historical unpinned Torch-helper bootstrap tools documented; expected main tool versions and runtime pins are present.
- OPEN: pip/setuptools PYZ code conflicts with excluded-table wording; dedicated package notices were not found by this bounded scan.

## Qualified outcome

CUDA runtime identity and exclusion checks: **PASS** within their stated scope.
Overall technical notice review: **REVIEW REQUIRED** for the separate bundled
build-tool finding. Exact original FAIL reports are retained with their original
hashes in the current JSON. The original comparison assumptions were too broad;
this qualification does not silently discard them or claim all build tools were locked.

All 91 runtime rows match the exact CUDA application lock. The excluded table
contains both pip 24.0 / 26.2.1 and setuptools 65.5.0 / 83.0.0. Independent build
tracing confirms the main pinned tools were installed before PyInstaller, while
separate Torch-helper metadata was added through PYTHONPATH. The old helper
bootstrap versions remain a documented build finding. The future helper fix is
separate from frozen source 753aab70; its PR reference is pending coordinator update.

## Transitive CUDA dependency

Static imports in `cusparse64_12.dll` name `nvJitLink_120_0.dll`, which the generated
installed manifest lists at 77,860,352 bytes. SHA-256:
`959d3cb44527ec884db8dc20772520b584dbe7d622d11b0530e6326417078b3e`.
Native resources identify NVIDIA CUDA 12.8.93 NVJITLINK. PyInstaller scans supplied
binaries for further binary dependencies, so the explicit seeds are not a complete
forbidden-file list. [PyInstaller binary collection documentation](https://pyinstaller.org/en/v6.22.0/spec-files.html#adding-binary-files).

The v2.2.3 manifest already names this DLL with the same size; historical DLL hash
identity was not tested. Installed Torch LICENSE/NOTICE/METADATA match the exact
source bytes and v2.2.3 text after newline normalization. The combined notices do
not explicitly name nvJitLink. No new component-specific permission or owner
approval is inferred from those observations.

## Bundled build-tool code finding

Each executable contains **353 pip modules** and **143 setuptools modules** in
PYZ; `pkg_resources` has zero. No loose executable/source files for those package
trees were found. pip statically identifies version 26.2.1. setuptools calculates
its version through metadata with an unknown fallback, so this scan does not
claim an independently observed embedded version 83.0.0.

The snapshot's blanket excluded-table wording is inaccurate for pip/setuptools
code. No dedicated pip/setuptools license directories or package-tree license
files were found in this bounded scan. That packaging/notice-classification finding
requires coordinator follow-up and is separate from helper metadata duplication.

## Installer provenance

Expected CLI/GUI hashes were measured after the successful official draft-hosted
installer upgrade. No independent pre-extracted full-payload hash manifest was
supplied. This report establishes static properties of the identified installed
bytes; it does not claim full-payload identity against such a manifest. Executable
hashes remained unchanged at final readback.

Official installer SHA-256: `797f15a50cef7522374c5bf4f1880b047e6fe0f1cd165c39a1639bc36189c31d`.
Upgrade receipt SHA-256: `aaa2b17e537fe8fa55e7ff5865117d6161f26ef31e2ed55a5903aed8b2542e7f`.
