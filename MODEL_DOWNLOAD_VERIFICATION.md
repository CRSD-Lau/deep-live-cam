---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Model Download Verification

Status: PENDING

Release: `2.2.4`

Candidate source: PENDING — record the corrected immutable build SHA and asset hashes.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [ ] Verify the replacement CLI identifies the catalogue sources, licence notes and checksums.
- [ ] Verify cancellation without consent against an isolated empty model cache.
- [ ] Verify authorized catalogue setup and all five expected file hashes using the replacement CLI.
- [ ] Reconcile interrupted-transfer, checksum-failure, retained-destination and redirect source regressions.

Keep model downloads in an owned test cache; preserve live caches and exclude all
weights from release assets. Record exact executable/source hashes and distinguish
packaged checks from source failure tests. GUI consent and dependency-managed
InsightFace/OpenNSFW2 downloads remain distinct scopes. The first candidate's
successful 1,557,775,109-byte download is archived with its original CLI hash.
