---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
app_version: 2.2.4
source_commit: 617c733d42a10a2fcba036385e19d66fabcc2cc1
status: AUTOMATED_FINAL_CANDIDATE_SUBSETS_PASS
publication_approval: false
---

# Corrected 2.2.4 candidate validation

Source `617c733d42a10a2fcba036385e19d66fabcc2cc1`; official workflow `34063403042`. Companion JSON SHA-256: `03941c8992a971a1a5ea95daab1444f66e7d327a640c81c61f341df9c91487fe`.

The verified corrected installer replaced the earlier 2.2.4 candidate with corrected 2.2.4 bytes. Actual execution exited 0 and preserved user data, verified backups, and the historical 2.2.3 upgrade evidence. It is not a fresh 2.2.3-to-corrected-2.2.4 upgrade test.

Installer SHA-256: `d91080bef32a6bb731830599bfda90eeca4844d20af6d34e67957c0bda2b48bf`. Installed CLI: `a047d8e7060dd8704d838eebd1ee51650dee4cde19478fa020478a22c54f32eb`; GUI: `b7e5d120d4a00b51db8a87805f7f011fbbd74ccc3e45e39b24e9aab221951fad`. These are post-install measurements. Independent full-payload manifest verification: `NOT_PROVIDED`.

Local combined checks: 744 passed. Exact-source CI: 742 passed, 2 skipped. Official build/source attestation and fresh-hosted byte receipts passed.

CUDA real image and silent/audio video exports passed, including failed-export preservation. CPU fallback passed its image-only scope. DirectML rendering passed on AMD Radeon device 1, with changed image pixels, silent/audio videos, and failed-export preservation.

DirectML ZIP SHA-256: `f6b077f0364bb523e75ec7950b096d62763a5b4aa2de181d0eaffa47f9bf6f04`. Each profile matched all 77 upstream tool notice files and its dependency inventory. Both executable archives were inspected for support modules and excluded Torch/JIT code; Qt metadata and shared full license texts were checked.

The existing affected Torch DLL-source-wheel exception remains recorded. No new legal approval or vulnerability-free claim is made.

GUI/Preview/Live, physical webcam, packaged external receiver, clean Windows VM and publication gate remain PENDING. Historical source-only OBS synthetic receiver evidence does not complete them.

## Input evidence

| Descriptive identifier | SHA-256 |
| --- | --- |
| `upgrade-receipt` | `e3f871c756554a689a43e7e2a2315bc811ea0611328ef8c84eaff58bca75dfdf` |
| `installed-runtime-receipt` | `ef15b8e001a9ab3f7ed282c630638f9a94d2a1de9b028a2a7498240be0f03506` |
| `build-source-receipt` | `dba511cf92448e6322a7ae43279b16976fd6ef1e63ac9f40abaf347adcf53b87` |
| `cuda-compliance-receipt` | `9aa725dd5a37093a122428106f96736d99290cf77770407656e8431039e69f53` |
| `directml-compliance-receipt` | `84eee36536444f1a03a1236603bfe42665cf4ad3388dcf498af45532948900ff` |
| `directml-validation-receipt` | `f9fbd4d3cba228f740922dffb31fab82a4e0458db660f5b484466f9e555bebe1` |
| `source-ci-metadata-receipt` | `ecb7ded6f719704b5e98167000bdc6fc948a4532f40f3a3c65e3bb463c4ef636` |
| `official-bytes-receipt` | `0804b1043c9232db2228fb508d5c0cc1db027e7dddc36f70cf7284d776c8be77` |
| `cuda-render-receipt` | `4dfe1aad95bba6ae7c79321c7c1f527342d8f9cbc7b48565290d8543bba22312` |
| `cpu-render-receipt` | `ae71e6b72961a37f2d727f6cdd6156bcb44b2024b3e186a862fb5f2d179ffe49` |
| `directml-render-receipt` | `a0e36601cc6e2032ba6730a9b6b31bdd84aa579b45b52e8be3f63e344cb9d527` |
| `combined-local-tests-log` | `336cbfb802d93777e6c9529667d5a6ffbc71ec23f844eebbe303199a9aeb925c` |
| `exact-source-ci-log` | `909f45dd4901cfe0daa001d90b1c1aa3094c9e8c52027fe482eafaf10525faa6` |
| `fresh-hosted-byte-receipt-1` | `0694291a19fa8130012f7a3d0c2831e76643cf59aac75b46861edcea0b492ef0` |
| `fresh-hosted-byte-receipt-2` | `847cef11ef70e394eb8c6c7737f26ff7fc8343d36f9cce62e9fc5235ff1b991f` |

Installer preservation: 7 user files / 1,558,270,376 bytes before and 7 files / 1,558,270,376 bytes after. Required installed files verified: 30; installed payload file count: 2,418.
