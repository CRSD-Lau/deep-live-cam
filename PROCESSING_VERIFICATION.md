---
author: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Processing Verification

Status: PENDING

Release: `2.2.4`

Historical packaged processing results are preserved in
`docs/release-evidence/v2.2.3/PROCESSING_VERIFICATION.md`.

## Current release checks

- [ ] Run real inference using the final CUDA runtime on the identified NVIDIA GPU.
- [ ] Run `--check-execution-provider` without an external CUDA Toolkit or external PyTorch DLL paths.
- [ ] Run real inference using the final DirectML runtime on an explicitly identified AMD adapter.
- [ ] Render a real image with the packaged CPU fallback and GPU profiles.
- [ ] Render short videos with and without audio, then validate frames, dimensions, duration and complete decode.
- [ ] Confirm a failed export preserves an existing destination and cleans its owned workspaces.
- [ ] Check processed Preview start, seeking and close against the final application.

The project review passed 619 source tests, including real FFmpeg media and
cross-volume publication checks. These tests establish I/O and failure behavior;
they do not establish final packaged inference or visual quality. Use non-sensitive
fixtures and existing verified models. Record exact source, artifact hashes,
provider identity and output validation in the final candidate evidence.
