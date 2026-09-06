---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Model Download Verification

Status: PASS

Release: `2.2.4`

Candidate source: `753aab70c34ae585d525a06b9f7de2d721b7f491`

## Verified current-release scope

- [x] The official DirectML CLI displayed catalogue sources, licence notes, and
  checksums, then cancelled setup with exit code 2 when consent was not given.
  The preflight used an isolated application-data directory.
- [x] The official DirectML CLI completed the authorized `--download-models --yes`
  setup with exit code 0 into an isolated cache.
- [x] All five installed catalogue files matched their expected SHA-256 values.
- [x] Source regression tests cover interrupted transfers, checksum failures,
  preservation of existing destinations, owned partial-file cleanup, and HTTPS
  redirect rejection.

The current download verified at `2026-09-06T20:23:28.224545+00:00` transferred
1,557,775,109 bytes. Executable SHA-256:
`51bc3516b1ffc17a6ae5fd48ba38f727f3787d28fb39a2783729fe569ad7edb2`.

| Catalogue file | Verified SHA-256 |
| --- | --- |
| inswapper_128.onnx | e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af |
| inswapper_128_fp16.onnx | 6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b |
| GPEN-BFR-256.onnx | aa5bd3ab238640a378c59e4a560f7a7150627944cf2129e6311ae4720e833271 |
| GPEN-BFR-512.onnx | 0960f836488735444d508b588e44fb5dfd19c68fde9163ad7878aa24d1d5115e |
| gfpgan-1024.onnx | ee8dd6415e388b3a410689d5d9395a2bf50b5973b588421ebfa57bc266f19e24 |

Evidence: `.tmp/release-2.2.4/model-download/verification.json` and
`.tmp/release-2.2.4/official-directml/validation.json` with the referenced
`packaged-runtime-preflight-attempt2.log`.

## Limits

PASS applies to the shared model-manager catalogue: current packaged DirectML
cancel/success checks plus source-level failure regressions. It does not claim
an interactive GUI click, a fresh interrupted-network test of the executable,
or a CUDA-package test. Final CUDA packaging receives its own consent preflight
under the runtime/installer gates. Dependency-managed InsightFace and optional
OpenNSFW2 assets remain outside this catalogue and may use separate caches.
No downloaded model is included in release artifacts.
