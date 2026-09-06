---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
source_commit: 617c733d42a10a2fcba036385e19d66fabcc2cc1
app_version: 2.2.4
technical_status: PASS
publication_approval: false
---

# DIRECTML payload technical inspection

Offline final payload files and archives; no application launch, DLL load, GPU inference, GUI, physical camera, clean VM or legal approval.

Source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`; JSON SHA-256: `84eee36536444f1a03a1236603bfe42665cf4ad3388dcf498af45532948900ff`.

Identity receipt: `validation.json` SHA-256 `00d256d483ec16e4552c41e0f1e6540b19baeffe7f7e0cf09a24136f7a95fbd6`; basis `artifact-extraction-receipt`.

- CLI SHA-256: `d7898571000e39d9925e3de7edc6f222ced40c8cf56f53cfd80328aeb732f61e`
- GUI SHA-256: `a1578d25460c681d9610dc878d1ef15f26ec32060a3cac5d129e2acba4281da2`

Files: 2,404; bytes: 1,852,508,405. Runtime inventory rows: 94. Four build-tool notice sets: 77 upstream reference files.

## Native identity

| Relative file | PE version | SHA-256 |
| --- | --- | --- |
| `_internal/onnxruntime/capi/DirectML.dll` | `1.15.4.0` | `0489a854150b171c9eb6495c38c7e6363c9528151b9cdae066cfe770a18fd5b4` |
| `_internal/onnxruntime/capi/onnxruntime.dll` | `1.23.25.924` | `a358e2ec051a8948091fee74c6a836f61ea9e97f8ce1171b9261ebb2da237ec9` |
| `_internal/onnxruntime/capi/onnxruntime_pybind11_state.pyd` | `No fixed resource` | `627e0ec071c029bc7d69da33ebcfb6ed28174fd903ac0e196ce8671c62aeb2e4` |
| `_internal/PySide6/Qt6Core.dll` | `6.11.1.0` | `65fe6224b6c47a15b058738031d31dce9928c4d7a58e1b8db6434f6f5cddd702` |
| `_internal/PySide6/QtCore.pyd` | `No fixed resource` | `be52341a5df1f76ecca2fb1e94eb429dfa46f0b659ed6536f25119b565b21ea8` |
| `_internal/PySide6/QtGui.pyd` | `No fixed resource` | `f0549716b10a8b4fbd5c6c041f36af215223809f919f4c4722d44cc199d5c593` |
| `_internal/PySide6/QtWidgets.pyd` | `No fixed resource` | `85cb6c2181b4b09887a7d8507dd950844d1b8f74a9c4002c7b71169f75bf6fda` |
| `_internal/python311.dll` | `3.11.9150.1013` | `0817a2a657a24c0d5fbb60df56960f42fc66b3039d522ec952dab83e2d869364` |
| `_internal/shiboken6/Shiboken.pyd` | `No fixed resource` | `0e2c5318c5ac60a016a12230bbb1f6a9d990c45cbf4a7c4af24aefb5ab7dc40a` |

## Attribution and runtime boundaries

Only this profile's snapshot, native payload and executable archives establish runtime content. Shared alternate-profile notice files are attribution, not runtime evidence.

The JSON records pip, setuptools, pkg_resources and packaging-support module counts in both executable archives. Tool roles do not establish exclusions. It checks every referenced pip/setuptools/PyInstaller/hooks notice against upstream hashes and rejects code in the notices directory.

The upstream commercial pointer does not override the LGPL/GPL expression in distribution metadata. Existing full texts are cross-referenced here without a new legal approval.

- `LGPL-3.0-only` full-text copy: `LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE` SHA-256 `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`
- `GPL-3.0-only` full-text copy: `LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE` SHA-256 `230184f60bae2feaf244f10a8bac053c8ff33a183bcc365b4d8b876d2b7f4809`
- `GPL-2.0-only` full-text copy: `LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE` SHA-256 `189b1af95d661151e054cea10c91b3d754e4de4d3fecfb074c1fb29476f7167b`

## Findings

- No failed technical checks in this scope. Manual GUI, physical-camera, clean-VM and publication gates remain separate.
