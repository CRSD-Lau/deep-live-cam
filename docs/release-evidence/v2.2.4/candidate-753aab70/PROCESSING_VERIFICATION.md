---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Processing Verification

Status: PENDING

Release: `2.2.4`

Candidate source: `753aab70c34ae585d525a06b9f7de2d721b7f491`

The final CUDA runtime passed `--check-execution-provider` and real processing
without an external CUDA Toolkit or development Torch path. A compatible NVIDIA
driver remains required. The verified draft-hosted installer upgraded the stable
installation before these checks; the installed CLI reports 2.2.4.

## Completed official DirectML CLI checks

- [x] Verify official workflow provenance and ZIP sidecar, safely extract the
  artifact, and confirm the packaged CLI reports 2.2.4.
- [x] Run the real provider probe and inference with `--directml-device-id 1`,
  the AMD adapter identified by the release validation.
- [x] Render a real image with Unicode target/output filenames. The output was
  readable at 448x560 with 69,199 changed pixels.
- [x] Render silent and AAC-audio videos. Each output contained four H.264
  frames at 448x560 and 4 FPS; durations were 1.000 and 1.002 seconds.
- [x] Fully decode both output videos without errors and verify audio is
  present only in the audio test.
- [x] Exercise unsupported image output encoding after real inference: the CLI
  returned nonzero, the prior destination hash remained unchanged, and no
  unexpected sibling staging files remained.
- [x] Confirm the packaged CLI and existing local models were unchanged by testing.

The non-sensitive fixture was InsightFace's installed `t1.jpg`, with separate
source/target crops. Existing verified models were used. This is functional
inference evidence, not a visual-quality or performance assessment.

Evidence: `.tmp/release-2.2.4/official-directml/validation.json` and its
`amd1_smoke_report` result/log paths. ZIP SHA-256:
`3b0b1eec9467021215a1d2cff702062653305f131e70471800c755c2c8ca283a`.
The report's default-adapter preflight probe is separate from the explicit
AMD device-1 render; record the adapter inventory alongside these results.

## Completed installed CUDA and CPU checks

- [x] Run real inference using the final CUDA runtime on the identified RTX 4070.
- [x] Run the final CUDA provider probe without external CUDA Toolkit or
  PyTorch DLL paths.
- [x] Render an image using the packaged CPU fallback.
- [x] Repeat image, silent/audio-video, and failed-export retention checks on
  the final CUDA profile, with full output validation.

CUDA device 0 is the NVIDIA GeForce RTX 4070, driver 616.64. The CUDA image
changed 69,189 pixels; the CPU image changed 69,199 pixels and its model log
reported only `CPUExecutionProvider`. Both CUDA videos decoded completely,
with the expected frames, dimensions and audio behavior. CPU video testing was
explicitly skipped. All ten existing model files and both installed executables
retained their hashes.

The installed CLI SHA-256 is
`9f762064b9079721c9597610689f48e306a9a0ca8483856b09f2546b2c387748`.
It was measured after the verified official installer completed, rather than
supplied by an independent full-payload hash manifest. The local detailed report
is `official-cuda/installed-runtime-20260906T212857Z-1299d7af/validation.json`
under the release-validation staging directory.

## Outstanding GUI checks

- [ ] Check processed Preview start, seeking, and close against each final GUI.

The project review's source regression/integration suite separately exercises
cross-volume publication, workspace cleanup, decoder failure, and mapper
handoff. The official DirectML report establishes the packaged subset above;
the installed CUDA report establishes its additional subset. Source tests and
historical 2.2.3 reports do not establish the remaining current GUI checks.
