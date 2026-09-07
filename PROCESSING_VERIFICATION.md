---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Processing Verification

Status: PASS

Publication status: APPROVED FOR PUBLICATION

Remaining manual gates: None.

Publication is authorized by Neil Mitchell and pending actual publication.

Neil Mitchell reported "All tests pass release" after the explicit seven-item
manual checklist. The [owner confirmation](docs/release-evidence/v2.2.4/candidate-617c733d/OWNER_MANUAL_CONFIRMATION.md)
records those manual PASS results and publication authorization. These results
were reported by Neil Mitchell; the agent did not execute the manual checks.


Release: `2.2.4`

Candidate source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Workflow: [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
[Candidate validation](docs/release-evidence/v2.2.4/candidate-617c733d/RELEASE_VALIDATION.md) and [build/source evidence](docs/release-evidence/v2.2.4/candidate-617c733d/BUILD_SOURCE_VALIDATION.md) record the exact files, input hashes and limits.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

The rebuilt [DirectML automated checks](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_VALIDATION.md)
passed on the identified AMD Radeon(TM) Graphics device 1. Unicode image output
was readable at 448x560 with 69,199 changed pixels. Silent and audio exports each
contained four fully decoded frames with the expected dimensions/audio behavior.
An unsupported output format failed without changing the prior destination or
leaving sibling files. The provider logs identify DirectML device 1 for all three
successful renders. Existing models and tested executables remained unchanged.

Portable ZIP SHA-256:
`f6b077f0364bb523e75ec7950b096d62763a5b4aa2de181d0eaffa47f9bf6f04`.
The checklist combines recorded automated evidence with the owner-reported GUI result.

- [x] Verify final CUDA and DirectML runtime identities and strict
  `--check-execution-provider` probes.
- [x] Run CUDA checks without an external CUDA Toolkit or development PyTorch
  DLL paths; retain the required compatible NVIDIA graphics driver.
- [x] Render real Unicode image exports on NVIDIA CUDA and identified AMD DirectML hardware.
- [x] Render and fully decode silent/audio videos with expected frame, dimension and audio metadata.
- [x] Verify failed export preserves the prior destination and cleans owned staging files.
- [x] Verify packaged CPU image fallback explicitly uses CPUExecutionProvider.
- [x] Confirm existing models and tested executable hashes remain unchanged.
- [x] Check packaged processed Preview start, seek and close in both final GUIs. — PASS reported by Neil Mitchell.

Record device identity/index, binary/source SHA, tested models, render outputs and
scope limits. CPU image evidence does not establish CPU video performance; CUDA
FP32 inference does not establish FP16 inference. The archived first candidate
passed the real CLI subsets on RTX 4070 and AMD device 1, but these results do not
substitute for validation of replacement binaries.

The corrected installed CUDA runtime also passed strict preflight without an external CUDA Toolkit, Unicode image output, silent/audio videos and failed-export preservation. CPU fallback passed image-only processing with CPUExecutionProvider. The combined validation records new installer/CLI/GUI hashes and preserved model bytes. Neil Mitchell reports packaged Preview PASS in the owner confirmation; the agent did not execute that manual GUI check.
