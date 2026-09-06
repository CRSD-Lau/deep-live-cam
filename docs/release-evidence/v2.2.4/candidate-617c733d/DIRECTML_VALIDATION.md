# Rebuilt DirectML Validation

Author: Neil Mitchell
Creator: Neil Mitchell
Last Modified By: Neil Mitchell

Status: PASS for the bounded automated checks below. Publication approval: false.

Source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`; version: `2.2.4`; workflow: `34063403042`; artifact: `9998298095`.

Portable ZIP SHA-256: `f6b077f0364bb523e75ec7950b096d62763a5b4aa2de181d0eaffa47f9bf6f04`.
CLI SHA-256: `d7898571000e39d9925e3de7edc6f222ced40c8cf56f53cfd80328aeb732f61e`.
GUI SHA-256: `a1578d25460c681d9610dc878d1ef15f26ec32060a3cac5d129e2acba4281da2`.

- Official resolver and completed DirectML job provenance, ZIP/sidecar hash, safe extraction and packaged preflight: PASS.
- Fresh DXGI enumeration confirms AMD Radeon(TM) Graphics at device 1; both enumeration methods agree.
- Actual image and both video runs explicitly configured DirectML device 1 and reported DirectML as an active face-swap provider.
- Unicode image export: PASS, 69,199 changed pixels at 448 x 560.
- Silent and audio video exports: PASS, 4 frames each, expected dimensions/audio presence and complete FFmpeg decode.
- Unsupported image output: nonzero exit, previous output hash unchanged, no unexpected sibling files.
- Catalogue cancellation: exit 2, all five source/license/checksum notices present, no model files installed.
- Authorized --download-models --yes: exit 0, exactly five complete files matched the pinned source catalogue hashes; no partial download files remain.
- Real user data, real Buffalo/model cache, installed executables, official portable executables and frozen extraction receipt remained unchanged.
- Independent static/licence audit is separately recorded under the compliance staging directory.

## Downloaded catalogue hashes

- `GPEN-BFR-256.onnx`: `aa5bd3ab238640a378c59e4a560f7a7150627944cf2129e6311ae4720e833271` (75715262 bytes).
- `GPEN-BFR-512.onnx`: `0960f836488735444d508b588e44fb5dfd19c68fde9163ad7878aa24d1d5115e` (284250449 bytes).
- `gfpgan-1024.onnx`: `ee8dd6415e388b3a410689d5d9395a2bf50b5973b588421ebfa57bc266f19e24` (365875079 bytes).
- `inswapper_128.onnx`: `e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af` (554253681 bytes).
- `inswapper_128_fp16.onnx`: `6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b` (277680638 bytes).

Weights remain in the new local validation cache and must not be included in release assets or evidence uploads.

## Limits

- No GUI, camera, OBS/receiver, clean-VM, or interactive installation checks were performed.
- CUDA artifact and installed CUDA replacement verification are separate work.
- Face-swap inference used DirectML device 1; face analyser components used the existing designed CPU policy.
- Pixel-change and file-integrity checks do not establish subjective image quality or live-camera behavior.
- The extraction/preflight receipt is frozen; model weights remain only in the new local validation cache.

See `DIRECTML_VALIDATION.json` for portable relative evidence paths and hashes.
