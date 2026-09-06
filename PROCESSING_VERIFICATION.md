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

The final CUDA runtime must pass `--check-execution-provider` and real processing
without an external CUDA Toolkit or development Torch path. A compatible NVIDIA
driver remains required. This check is pending for the final CUDA installer.

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

## Outstanding checks

- [ ] Run real inference using the final CUDA runtime on the identified RTX 4070.
- [ ] Run the final CUDA provider probe without external CUDA Toolkit or
  PyTorch DLL paths.
- [ ] Render an image using the packaged CPU fallback.
- [ ] Repeat image, silent/audio-video, and failed-export retention checks on
  the final CUDA profile, with full output validation.
- [ ] Check processed Preview start, seeking, and close against each final GUI.

The project review's source regression/integration suite separately exercises
cross-volume publication, workspace cleanup, decoder failure, and mapper
handoff. The official DirectML report establishes the packaged subset above;
neither source tests nor historical 2.2.3 reports establish the outstanding
final CUDA, CPU, or GUI checks.
