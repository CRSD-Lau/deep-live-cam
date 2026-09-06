---
author: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Compliance Delta Review

Status: PENDING

Release: `2.2.4`

The previous owner-accepted distribution posture and its provenance are
preserved in `docs/release-evidence/v2.2.3/LEGAL_REVIEW.md`. This record assesses
the current delta and artifact evidence; it does not claim a new owner signoff.

## Delta from 2.2.3

Application reliability changes add no dependency, codec or model family.
Packaging hooks update from 2026.6 to 2026.7 and the development Ruff tool from
0.16.4 to 0.16.5. Runtime dependency versions remain unchanged. CUDA and DirectML
remain separate downloads. PyTorch remains only the isolated source of the
selected CUDA runtime DLLs; its Python package is excluded. The existing audit
exception and re-evaluation conditions are documented in `docs/DEPENDENCY_LOCKS.md`.

The explicit model catalogue retains source, checksum and licence information.
InsightFace analysis and optional OpenNSFW2 initialization can still download
missing dependency-managed models outside that catalogue, as README now states.
No blanket claim is made that every download passes the application's consent UI.

## Current artifact checks

- [ ] Attach exact corresponding source matching both runtime builds.
- [ ] Confirm original attribution and AGPL source instructions are present.
- [ ] Verify current dependency notices, Qt metadata and CUDA DLL licences in the final payloads.
- [ ] Scan both runtime assets and source for excluded model/checkpoint weights.
- [ ] Confirm external FFmpeg and model redistribution boundaries are unchanged.

Previously accepted licence and publisher/commercial-use decisions remain
historical owner decisions. Any new material distribution obligation requires
separate assessment. Exact source refs and hashes belong in the external asset
manifest to avoid circular binary-hash documentation.
