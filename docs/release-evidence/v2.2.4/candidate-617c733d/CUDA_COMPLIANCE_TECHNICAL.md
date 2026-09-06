---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
source_commit: 617c733d42a10a2fcba036385e19d66fabcc2cc1
app_version: 2.2.4
technical_status: PASS
publication_approval: false
---

# CUDA payload technical inspection

Offline final payload files and archives; no application launch, DLL load, GPU inference, GUI, physical camera, clean VM or legal approval.

Source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`; JSON SHA-256: `9aa725dd5a37093a122428106f96736d99290cf77770407656e8431039e69f53`.

Identity receipt: `upgrade-report.json` SHA-256 `e3f871c756554a689a43e7e2a2315bc811ea0611328ef8c84eaff58bca75dfdf`; basis `post-install-verified-installer`.

Expected CLI/GUI hashes were measured after a verified installer completed. They are not an independent pre-extracted installer payload manifest.

- CLI SHA-256: `a047d8e7060dd8704d838eebd1ee51650dee4cde19478fa020478a22c54f32eb`
- GUI SHA-256: `b7e5d120d4a00b51db8a87805f7f011fbbd74ccc3e45e39b24e9aab221951fad`

Files: 2,420; bytes: 5,160,219,624. Runtime inventory rows: 91. Four build-tool notice sets: 77 upstream reference files.

## Native identity

| Relative file | PE version | SHA-256 |
| --- | --- | --- |
| `_internal/cublas64_12.dll` | `6.14.11.1284` | `9513540e4ec4c51ee9e7304138c2cc255c29a8c181f9e80c38efa25738becd99` |
| `_internal/cublasLt64_12.dll` | `6.14.11.1284` | `b199d1ff892a81b7fd3d57ba1781549609b41500b36008fef326038393ad46c7` |
| `_internal/cudart64_12.dll` | `6.14.11.12080` | `c2c9a9c22a9bcba90e261825968836787b331038047a26770cffb7a583c28344` |
| `_internal/cudnn64_9.dll` | `9.19.0.56` | `c6de55089c4759a545ff63459c00a6223dacffa5e797109a6be2be0477fb6c5c` |
| `_internal/cudnn_adv64_9.dll` | `9.19.0.56` | `a8aed3390144ea20d96c0d618462a12cbc7897620380e60438489329b9722531` |
| `_internal/cudnn_cnn64_9.dll` | `9.19.0.56` | `acac8bf8f924ecd60928877310ba360d2ee5eb1e4ec80ff6475bf9d819d3a5c8` |
| `_internal/cudnn_engines_precompiled64_9.dll` | `9.19.0.56` | `3a97df241beb2b75eb5d6152996a9a90d2155c2d4da1aeac5bd66850ed2446c1` |
| `_internal/cudnn_engines_runtime_compiled64_9.dll` | `9.19.0.56` | `81c5e5475e386269825ae6da0652f4554fa1c58af6c90908a180314689e12350` |
| `_internal/cudnn_graph64_9.dll` | `No fixed resource` | `f5453cb541402218cb5459e669db1d578656ebef394c755ab5acc2bec1165657` |
| `_internal/cudnn_heuristic64_9.dll` | `No fixed resource` | `3b1cb10835204fb7a45bf03aeb353842185cb2ebb34f59db20d9cb6fe5c1c556` |
| `_internal/cudnn_ops64_9.dll` | `9.19.0.56` | `922897bd15a66acecde7c026ecc835b0fc5662c9ae08c120fd89f0f73affa7da` |
| `_internal/cufft64_11.dll` | `6.14.11.1133` | `f4fea9227b14843894ad5436725f9638b172171142c95291fc6ae7a493248221` |
| `_internal/cufftw64_11.dll` | `6.14.11.1133` | `84c86dcc4d4b770e75766964149ef688c901dc89e380278fe399dd3c03608541` |
| `_internal/curand64_10.dll` | `6.14.11.1039` | `3465fd1b46e551339b8f44c455756a0f2cba8bd846562eb659040d48edb7aaac` |
| `_internal/cusolver64_11.dll` | `6.14.11.1173` | `3d4f7a66b5f352db56d4bb5962bb453a42d5feb2d831779f4a0bebc9971c36fb` |
| `_internal/cusolverMg64_11.dll` | `6.14.11.1173` | `c3377f10606ff0606be2f08401d54aff6c37f137b78d6b6e21be356a5b4d6cc2` |
| `_internal/cusparse64_12.dll` | `6.14.11.1258` | `f4688daa6163c47a0b5293926ec7ae367de6b4af54ea201638b308831b322a0e` |
| `_internal/nvJitLink_120_0.dll` | `6.14.11.9000` | `959d3cb44527ec884db8dc20772520b584dbe7d622d11b0530e6326417078b3e` |
| `_internal/nvrtc-builtins64_128.dll` | `No fixed resource` | `a7afa2a40cbd3f922a33d8bf71c13cb26ca707c7016a9bc5fcde36759ba668f5` |
| `_internal/nvrtc64_120_0.dll` | `6.14.11.9000` | `02d2d7ef4690bf1a55dda1d3ac94c86ce8d16920071c87bcd3e70e94ef346e93` |
| `_internal/nvToolsExt64_1.dll` | `No fixed resource` | `0fe54f1b80ad3e44da2a3d9f0956e7c3903029d6319689ce1c4068f7a20932f3` |
| `_internal/onnxruntime/capi/onnxruntime_providers_cuda.dll` | `1.24.26.316` | `6a02338c8fcf9e913767c1eb57033959f69076567d5290cee59c541793d16354` |
| `_internal/onnxruntime/capi/onnxruntime_providers_shared.dll` | `1.24.26.316` | `93f33380e5819cb9befbfe0e5212394dcb0c9983970c73a01bf51100bb1f13ee` |
| `_internal/onnxruntime/capi/onnxruntime_pybind11_state.pyd` | `No fixed resource` | `98a1398a33f10174929f512e6c17238693a99ad92a676e97500ce752a2cad10b` |
| `_internal/PySide6/Qt6Core.dll` | `6.11.1.0` | `65fe6224b6c47a15b058738031d31dce9928c4d7a58e1b8db6434f6f5cddd702` |
| `_internal/PySide6/QtCore.pyd` | `No fixed resource` | `be52341a5df1f76ecca2fb1e94eb429dfa46f0b659ed6536f25119b565b21ea8` |
| `_internal/PySide6/QtGui.pyd` | `No fixed resource` | `f0549716b10a8b4fbd5c6c041f36af215223809f919f4c4722d44cc199d5c593` |
| `_internal/PySide6/QtWidgets.pyd` | `No fixed resource` | `85cb6c2181b4b09887a7d8507dd950844d1b8f74a9c4002c7b71169f75bf6fda` |
| `_internal/python311.dll` | `3.11.9150.1013` | `0817a2a657a24c0d5fbb60df56960f42fc66b3039d522ec952dab83e2d869364` |
| `_internal/shiboken6/Shiboken.pyd` | `No fixed resource` | `0e2c5318c5ac60a016a12230bbb1f6a9d990c45cbf4a7c4af24aefb5ab7dc40a` |
| `_internal/zlibwapi.dll` | `1.2.3.0` | `1f047faec08d9a35c304fb4a7cf13853589359a8f7cbfdd48c5d5807712dcf05` |

## Attribution and runtime boundaries

Only this profile's snapshot, native payload and executable archives establish runtime content. Shared alternate-profile notice files are attribution, not runtime evidence.

The JSON records pip, setuptools, pkg_resources and packaging-support module counts in both executable archives. Tool roles do not establish exclusions. It checks every referenced pip/setuptools/PyInstaller/hooks notice against upstream hashes and rejects code in the notices directory.

The upstream commercial pointer does not override the LGPL/GPL expression in distribution metadata. Existing full texts are cross-referenced here without a new legal approval.

- `LGPL-3.0-only` full-text copy: `LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE` SHA-256 `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`
- `GPL-3.0-only` full-text copy: `LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE` SHA-256 `230184f60bae2feaf244f10a8bac053c8ff33a183bcc365b4d8b876d2b7f4809`
- `GPL-2.0-only` full-text copy: `LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE` SHA-256 `189b1af95d661151e054cea10c91b3d754e4de4d3fecfb074c1fb29476f7167b`

The spec lists seed binaries. PyInstaller recursively collects imported DLL dependencies; the static cusparse import establishes nvJitLink's transitive relationship. This observation is not a new redistribution approval.

The existing affected Torch source-wheel exception remains recorded, with no patched-version or new-approval claim. See `docs/DEPENDENCY_LOCKS.md` and the JSON for the precise boundary.

## Findings

- No failed technical checks in this scope. Manual GUI, physical-camera, clean-VM and publication gates remain separate.
