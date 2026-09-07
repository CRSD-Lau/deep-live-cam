---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Model Download Verification

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
The scope below was verified against the official rebuilt DirectML executable.

The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded. Its evidence is retained
with original hashes and does not approve this rebuild.

- [x] The replacement CLI displayed all five catalogue sources, licence notes and checksums.
- [x] Cancellation without consent returned exit 2 and created no model files in an isolated empty cache.
- [x] Authorized `--download-models --yes` completed with exit 0; all five files matched their expected hashes and no partial files remained.
- [x] Current source CI passed the interrupted-transfer, checksum-failure, retained-destination and redirect regressions.

See [the rebuilt DirectML validation](docs/release-evidence/v2.2.4/candidate-617c733d/DIRECTML_VALIDATION.md)
and its JSON for all five hashes and linked raw evidence. The new download
validation completed at `2026-09-06T22:28:43.160611+00:00`, with 1,557,775,109 model bytes.
The tested CLI SHA-256 is
`d7898571000e39d9925e3de7edc6f222ced40c8cf56f53cfd80328aeb732f61e`;
the portable ZIP SHA-256 is
`f6b077f0364bb523e75ec7950b096d62763a5b4aa2de181d0eaffa47f9bf6f04`.

Models remain in the new owned test cache and are excluded from release assets.
Existing user data, model/Buffalo caches and installed executables stayed unchanged.
PASS covers packaged DirectML cancellation/success and source-level failure tests;
it does not claim a fresh interrupted-network test of the executable or CUDA-package
setup. GUI consent is separately PASS as reported by Neil Mitchell in the owner
confirmation; it was not executed by the agent. Dependency-managed InsightFace/OpenNSFW2 downloads remain
outside this explicit catalogue. The first candidate's separate download evidence
stays archived with its original CLI hash.
