---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-10-25
---

# Release Compliance Delta Review

Status: PENDING

Release: `2.2.5`

Publication status: NOT APPROVED

Candidate source: pending immutable candidate commit and build artifacts.

The archived [2.2.4 attestation](docs/release-evidence/v2.2.4/final-attestations/LEGAL_REVIEW.md) applies only to its original binaries. Complete these checks against the new 2.2.5 artifacts and record exact hashes, source commit, hardware, and evidence before publication.

- [ ] Generate fresh CUDA and DirectML Python dependency inventories from their clean packaged environments.
- [ ] Verify Pillow 13.0.0 and setuptools 84.1.0 metadata and licence notices in both final artifacts.
- [ ] Inspect Qt texts, CUDA provenance, source attribution, model exclusions, and exact corresponding source.
