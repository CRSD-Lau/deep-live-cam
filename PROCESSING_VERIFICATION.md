---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-10-25
---

# Processing Verification

Status: PENDING

Release: `2.2.5`

Publication status: NOT APPROVED

Candidate source: pending immutable candidate commit and build artifacts.

The archived [2.2.4 attestation](docs/release-evidence/v2.2.4/final-attestations/PROCESSING_VERIFICATION.md) applies only to its original binaries. Complete these checks against the new 2.2.5 artifacts and record exact hashes, source commit, hardware, and evidence before publication.

- [ ] Run strict CUDA and DirectML provider probes on supported NVIDIA and AMD hardware.
- [ ] Verify packaged Preview, Render, enhancement, CPU fallback, and Live Output.
- [ ] Verify Unicode image exports, silent/audio video integrity, and failed-export preservation.

Verify CUDA operation without an external CUDA Toolkit by running the packaged CLI with `--execution-provider cuda --check-execution-provider`, then run the strict packaged-runtime probe.
