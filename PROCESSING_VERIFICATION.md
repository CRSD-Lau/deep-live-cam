---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Processing Verification

Status: PENDING

Release: `2.2.4`

Candidate source: PENDING — record the corrected immutable build SHA and asset hashes.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [ ] Verify final CUDA and DirectML runtime identities and strict provider probes.
- [ ] Render real Unicode image exports on NVIDIA CUDA and identified AMD DirectML hardware.
- [ ] Render and fully decode silent/audio videos with expected frame, dimension and audio metadata.
- [ ] Verify failed export preserves the prior destination and cleans owned staging files.
- [ ] Verify packaged CPU image fallback explicitly uses CPUExecutionProvider.
- [ ] Confirm existing models and tested executable hashes remain unchanged.
- [ ] Check packaged processed Preview start, seek and close in both final GUIs.

Record device identity/index, binary/source SHA, tested models, render outputs and
scope limits. CPU image evidence does not establish CPU video performance; CUDA
FP32 inference does not establish FP16 inference. The archived first candidate
passed the real CLI subsets on RTX 4070 and AMD device 1, but these results do not
substitute for validation of replacement binaries.
