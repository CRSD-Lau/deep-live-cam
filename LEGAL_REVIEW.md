---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Compliance Delta Review

Status: PENDING

Release: `2.2.4`

Candidate source: `753aab70c34ae585d525a06b9f7de2d721b7f491`

## Distribution posture and reviewed delta

The previous owner-accepted distribution posture is preserved in
`docs/release-evidence/v2.2.3/LEGAL_REVIEW.md`. It records Neil Mitchell's
historical publisher acceptance. This current technical evidence update does
not create or claim a new owner signoff or a legal opinion.

- [x] Review the dependency delta: PyInstaller hooks 2026.6 to 2026.7 in both
  package locks and development Ruff 0.16.4 to 0.16.5. Runtime dependency
  versions, codec families, and model families remain unchanged from 2.2.3.
- [x] Retain separate CUDA and DirectML distribution and model-weight exclusion.
- [x] Document that explicit catalogue downloads carry source, checksum, and
  licence notes, while InsightFace analysis and optional OpenNSFW2 models may
  download through dependency-managed paths outside that consent inventory.
- [x] Verify required runtime notice files and model exclusion through the
  official DirectML packaged-runtime preflight.

The build-only PyTorch 2.11.0 wheel remains affected by the documented advisory.
The existing exception depends on excluding Torch/JIT Python code and copying
only the selected CUDA/cuDNN DLLs. It is not an assertion that the wheel is
patched. Its scope and re-evaluation conditions remain in
`docs/DEPENDENCY_LOCKS.md`; the final CUDA payload must still be checked.

## Outstanding final artifact checks

- [ ] Attach corresponding source that matches both final runtime builds.
- [ ] Verify final source/binary refs, hashes, original attribution, and AGPL
  source instructions in the assembled asset set.
- [ ] Verify both final dependency inventories and notices, including actual
  Qt metadata and CUDA DLL licences; DirectML file-presence checks alone do
  not establish every licence document's content.
- [ ] Scan the final CUDA runtime and exact source archive for excluded weights;
  retain the already completed DirectML exclusion result with its hash.
- [ ] Verify external FFmpeg and model redistribution boundaries in the complete
  final artifact set, and assess any material obligation revealed by that inspection.

Evidence read for this update: `docs/DEPENDENCY_LOCKS.md`, the historical legal
record, and `.tmp/release-2.2.4/official-directml/validation.json`. Exact binary
hashes belong in the external asset manifest. Do not promote this gate to PASS
until the outstanding technical artifact checks are complete and the existing
owner-accepted posture still applies to the actual delta.
